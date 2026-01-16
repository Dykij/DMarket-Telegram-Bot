"""Base DMarket API client with HTTP handling and authentication.

This module provides the core HTTP client functionality including:
- Request signing (Ed25519/HMAC)
- Rate limiting
- Retry logic
- Circuit breaker support
- Response caching
"""

import asyncio
import logging
import time
import traceback
from typing import TYPE_CHECKING, Any

from circuitbreaker import CircuitBreakerError  # type: ignore[import-untyped]
import httpx

from src.dmarket.api.auth import generate_signature_ed25519
from src.dmarket.api.cache import (
    clear_cache,
    clear_cache_for_endpoint,
    get_cache_key,
    get_from_cache,
    is_cacheable,
    save_to_cache,
)
from src.dmarket.api.endpoints import Endpoints
from src.utils import json_utils as json
from src.utils.api_circuit_breaker import call_with_circuit_breaker
from src.utils.rate_limiter import RateLimiter
from src.utils.sentry_breadcrumbs import add_api_breadcrumb


if TYPE_CHECKING:
    from src.telegram_bot.notifier import Notifier


logger = logging.getLogger(__name__)


class DMarketAPIClient:
    """Base DMarket API client with HTTP handling and authentication.

    This class provides:
    - Ed25519/HMAC request signing
    - Rate limiting and retry logic
    - Response caching
    - Circuit breaker support
    - Async context manager support

    Example:
        async with DMarketAPIClient(public_key, secret_key) as api:
            response = await api._request("GET", "/account/v1/balance")
    """

    def __init__(
        self,
        public_key: str,
        secret_key: str | bytes,
        api_url: str = "https://api.dmarket.com",
        max_retries: int = 3,
        connection_timeout: float = 30.0,
        pool_limits: httpx.Limits | None = None,
        retry_codes: list[int] | None = None,
        enable_cache: bool = True,
        dry_run: bool = True,
        notifier: "Notifier | None" = None,
    ) -> None:
        """Initialize DMarket API client.

        Args:
            public_key: DMarket API public key
            secret_key: DMarket API secret key
            api_url: API URL (default is https://api.dmarket.com)
            max_retries: Maximum number of retries for failed requests
            connection_timeout: Connection timeout in seconds
            pool_limits: Connection pool limits
            retry_codes: HTTP status codes to retry on
            enable_cache: Enable caching of frequent requests
            dry_run: If True, simulates trading operations without real API calls
            notifier: Notifier instance for sending alerts on API changes
        """
        self.public_key = public_key
        self._public_key = public_key

        if isinstance(secret_key, str):
            self._secret_key = secret_key
            self.secret_key = secret_key.encode("utf-8")
        else:
            self._secret_key = secret_key.decode("utf-8")
            self.secret_key = secret_key

        self.api_url = api_url
        self.max_retries = max_retries
        self.connection_timeout = connection_timeout
        self.enable_cache = enable_cache
        self.dry_run = dry_run
        self.notifier = notifier

        # Default retry codes: server errors and rate limiting
        self.retry_codes = retry_codes or [429, 500, 502, 503, 504]

        # Connection pool settings
        self.pool_limits = pool_limits or httpx.Limits(
            max_connections=100,
            max_keepalive_connections=20,
        )

        # HTTP client
        self._client: httpx.AsyncClient | None = None

        # Initialize RateLimiter
        self.rate_limiter = RateLimiter(
            is_authorized=bool(public_key and secret_key),
        )

        # Log initialization
        mode = "[DRY-RUN]" if dry_run else "[LIVE]"
        logger.info(
            f"Initialized DMarketAPIClient {mode} "
            f"(authorized: {'yes' if public_key and secret_key else 'no'}, "
            f"cache: {'enabled' if enable_cache else 'disabled'})",
        )

        if not dry_run:
            logger.warning(
                "⚠️  DRY_RUN=false - API client will make REAL TRADES! "
                "Ensure you understand the risks."
            )

    async def __aenter__(self) -> "DMarketAPIClient":
        """Context manager entry."""
        await self._get_client()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object | None,
    ) -> None:
        """Context manager exit."""
        _ = (exc_type, exc_val, exc_tb)  # Unused but required by protocol
        await self._close_client()

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=self.connection_timeout,
                limits=self.pool_limits,
            )
        return self._client

    async def _close_client(self) -> None:
        """Close HTTP client if it exists."""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    def _generate_signature(
        self,
        method: str,
        path: str,
        body: str = "",
    ) -> dict[str, str]:
        """Generate signature for API request.

        Args:
            method: HTTP method
            path: Request path
            body: Request body

        Returns:
            dict: Headers with signature
        """
        return generate_signature_ed25519(
            self.public_key,
            self._secret_key,
            method,
            path,
            body,
        )

    def _generate_headers(
        self,
        method: str,
        target: str,
        body: str = "",
    ) -> dict[str, str]:
        """Alias for _generate_signature for test compatibility."""
        return self._generate_signature(method, target, body)

    async def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        force_refresh: bool = False,
    ) -> dict[str, Any]:
        """Execute request to DMarket API with error handling, retries and caching.

        Args:
            method: HTTP method (GET, POST, etc.)
            path: API path without base URL
            params: Query parameters (for GET)
            data: Request data (for POST/PUT)
            force_refresh: Force cache refresh

        Returns:
            API response as dictionary

        Raises:
            Exception: On request error after all retries
        """
        client = await self._get_client()

        params = params or {}
        data = data or {}

        url = f"{self.api_url}{path}"

        # Check cacheability
        cacheable, ttl_type = is_cacheable(method, path)
        cache_key = ""

        # Check cache for GET requests
        body_json = ""
        if method.upper() == "GET" and self.enable_cache and not force_refresh and cacheable:
            cache_key = get_cache_key(method, path, params, data)
            cached_data = get_from_cache(cache_key)
            if cached_data is not None:
                logger.debug(f"Using cached data for {path}")
                return cached_data

        # Build request body for POST/PUT/PATCH
        if data and method.upper() in {"POST", "PUT", "PATCH"}:
            body_json = json.dumps(data)

        # Generate headers with signature
        headers = self._generate_signature(method.upper(), path, body_json)

        # Rate limiting
        await self.rate_limiter.wait_if_needed(
            "market" if "market" in path else "account",
        )

        # Retry loop
        retries = 0
        last_error: Exception | None = None
        retry_delay = 1.0

        while retries <= self.max_retries:
            start_time = time.time()
            try:
                add_api_breadcrumb(
                    endpoint=path,
                    method=method.upper(),
                    retry_attempt=retries,
                    has_cache=cache_key and get_from_cache(cache_key) is not None,
                )

                # Execute request
                if method.upper() == "GET":
                    response = await call_with_circuit_breaker(
                        client.get, url, params=params, headers=headers
                    )
                elif method.upper() == "POST":
                    response = await call_with_circuit_breaker(
                        client.post, url, json=data, headers=headers
                    )
                elif method.upper() == "PUT":
                    response = await call_with_circuit_breaker(
                        client.put, url, json=data, headers=headers
                    )
                elif method.upper() == "DELETE":
                    response = await call_with_circuit_breaker(client.delete, url, headers=headers)
                else:
                    msg = f"Unsupported HTTP method: {method}"
                    raise ValueError(msg)

                response.raise_for_status()

                response_time_ms = (time.time() - start_time) * 1000

                add_api_breadcrumb(
                    endpoint=path,
                    method=method.upper(),
                    status_code=response.status_code,
                    response_time_ms=response_time_ms,
                )

                # Parse JSON response
                try:
                    result = response.json()
                except (json.JSONDecodeError, TypeError, Exception):
                    result = {
                        "text": response.text,
                        "status_code": response.status_code,
                    }

                # Save to cache if applicable
                if method.upper() == "GET" and self.enable_cache and cacheable:
                    save_to_cache(cache_key, result, ttl_type)

                return result  # type: ignore[no-any-return]

            except CircuitBreakerError as e:
                logger.warning(f"Circuit breaker open for {method} {path}: {e}")
                add_api_breadcrumb(
                    endpoint=path,
                    method=method.upper(),
                    error="circuit_breaker_open",
                    error_message=str(e),
                )
                last_error = e
                break

            except httpx.HTTPStatusError as e:
                status_code = e.response.status_code
                response_text = e.response.text
                response_time_ms = (time.time() - start_time) * 1000

                logger.warning(
                    f"HTTP error {status_code} for {method} {path}: {response_text}",
                )

                add_api_breadcrumb(
                    endpoint=path,
                    method=method.upper(),
                    status_code=status_code,
                    response_time_ms=response_time_ms,
                    error="http_error",
                    retry_attempt=retries,
                )

                error_description = Endpoints.ERROR_CODES.get(
                    status_code,
                    "Unknown error",
                )
                logger.warning(f"Error description: {error_description}")

                # Check if should retry
                if status_code in self.retry_codes:
                    retries += 1

                    if status_code == 429:
                        retry_after = None
                        try:
                            retry_after = int(
                                e.response.headers.get("Retry-After", "0"),
                            )
                        except (ValueError, TypeError):
                            retry_after = None

                        if not retry_after or retry_after <= 0:
                            retry_delay = min(retry_delay * 2, 30)
                        else:
                            retry_delay = retry_after

                        logger.info(
                            f"Rate limit exceeded. Retry in {retry_delay} sec.",
                        )
                    else:
                        retry_delay = 1.0 + retries * 0.5

                    if retries <= self.max_retries:
                        logger.info(
                            f"Retry {retries}/{self.max_retries} in {retry_delay} sec...",
                        )
                        await asyncio.sleep(retry_delay)
                        continue

                # Non-retryable error or retries exhausted
                try:
                    error_json = e.response.json()
                    error_message = error_json.get("message", str(e))
                    error_code = error_json.get("code", status_code)
                except (json.JSONDecodeError, TypeError, AttributeError):
                    error_message = response_text
                    error_code = status_code

                error_data = {
                    "error": True,
                    "code": error_code,
                    "message": error_message,
                    "status": status_code,
                    "description": error_description,
                }

                if status_code in {400, 404}:
                    return error_data

                last_error = Exception(
                    f"DMarket API error: {error_message} "
                    f"(code: {error_code}, description: {error_description})",
                )
                break

            except (httpx.ConnectError, httpx.ReadError, httpx.WriteError) as e:
                logger.warning(f"Network error for {method} {path}: {e!s}")

                add_api_breadcrumb(
                    endpoint=path,
                    method=method.upper(),
                    error="network_error",
                    error_message=str(e),
                    retry_attempt=retries,
                )

                retries += 1
                retry_delay = min(retry_delay * 1.5, 10)

                if retries <= self.max_retries:
                    logger.info(
                        f"Retry {retries}/{self.max_retries} in {retry_delay} sec...",
                    )
                    await asyncio.sleep(retry_delay)
                    continue

                last_error = e
                break

            except Exception as e:
                logger.exception(
                    f"Unexpected error for {method} {path}: {e!s}",
                )
                logger.exception(traceback.format_exc())

                add_api_breadcrumb(
                    endpoint=path,
                    method=method.upper(),
                    error="unexpected_error",
                    error_message=str(e),
                    retry_attempt=retries,
                )

                last_error = e
                break

        # All retries exhausted
        if last_error:
            error_message = str(last_error)
            return {
                "error": True,
                "message": error_message,
                "code": "REQUEST_FAILED",
            }

        return {
            "error": True,
            "message": "Unknown error occurred during API request",
            "code": "UNKNOWN_ERROR",
        }

    async def clear_cache(self) -> None:
        """Clear all API cache."""
        clear_cache()
        logger.info("API cache cleared")

    async def clear_cache_for_endpoint(self, endpoint_path: str) -> None:
        """Clear cache for specific endpoint.

        Args:
            endpoint_path: Endpoint path to clear cache for
        """
        clear_cache_for_endpoint(endpoint_path)
        logger.info(f"Cache cleared for endpoint: {endpoint_path}")
