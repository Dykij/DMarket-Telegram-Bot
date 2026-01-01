"""DMarket API wallet and balance operations.

This module provides wallet-related API operations including:
- Getting user balance
- Balance parsing from various response formats
- Direct balance requests
- Account details
"""

import base64
import hashlib
import hmac
import logging
import time
import traceback
from typing import Any

import nacl.signing

from src.utils.api_circuit_breaker import call_with_circuit_breaker


logger = logging.getLogger(__name__)


class WalletOperationsMixin:
    """Mixin class providing wallet-related API operations.

    This mixin is designed to be used with DMarketAPIClient or DMarketAPI
    which provides the _request method and endpoint constants.
    """

    # Type hints for mixin compatibility
    _request: Any
    _get_client: Any
    public_key: str
    secret_key: bytes
    _secret_key: str
    api_url: str
    ENDPOINT_BALANCE: str
    ENDPOINT_BALANCE_LEGACY: str
    ENDPOINT_ACCOUNT_DETAILS: str

    def _create_error_response(
        self,
        error_message: str,
        status_code: int = 500,
        error_code: str = "ERROR",
    ) -> dict[str, Any]:
        """Create standardized error response for balance requests.

        Args:
            error_message: Human-readable error message
            status_code: HTTP status code
            error_code: Machine-readable error code

        Returns:
            Standardized error response dict
        """
        return {
            "usd": {"amount": 0},
            "has_funds": False,
            "balance": 0.0,
            "available_balance": 0.0,
            "total_balance": 0.0,
            "error": True,
            "error_message": error_message,
            "status_code": status_code,
            "code": error_code,
        }

    def _create_balance_response(
        self,
        usd_amount: float,
        usd_available: float,
        usd_total: float,
        min_required: float = 100.0,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Create standardized success response for balance requests.

        Args:
            usd_amount: Total balance in cents
            usd_available: Available balance in cents
            usd_total: Total balance including locked funds in cents
            min_required: Minimum required balance in cents (default 100 = $1.00)
            **kwargs: Additional fields to include in response

        Returns:
            Standardized success response dict
        """
        has_funds = usd_amount >= min_required

        result = {
            "usd": {"amount": usd_amount},
            "has_funds": has_funds,
            "balance": usd_amount / 100,
            "available_balance": usd_available / 100,
            "total_balance": usd_total / 100,
            "error": False,
        }
        result.update(kwargs)
        return result

    def _parse_balance_from_response(
        self,
        response: dict[str, Any],
    ) -> tuple[float, float, float]:
        """Parse balance data from various DMarket API response formats.

        Args:
            response: API response dict

        Returns:
            Tuple of (usd_amount, usd_available, usd_total) in cents
        """
        usd_amount = 0.0
        usd_available = 0.0
        usd_total = 0.0

        try:
            # Format 0: Official DMarket API format (2024)
            if "usd" in response and "usdAvailableToWithdraw" in response:
                usd_str = response.get("usd", "0")
                usd_available_str = response.get("usdAvailableToWithdraw", usd_str)

                usd_amount = float(usd_str) if usd_str else 0
                usd_available = (
                    float(usd_available_str) if usd_available_str else usd_amount
                )
                usd_total = usd_amount
                logger.info(
                    f"Parsed balance from official format: ${usd_amount / 100:.2f} USD"
                )

            # Format 1: Alternative format with funds.usdWallet
            elif "funds" in response:
                funds = response["funds"]
                if isinstance(funds, dict) and "usdWallet" in funds:
                    wallet = funds["usdWallet"]
                    usd_amount = float(wallet.get("balance", 0)) * 100
                    usd_available = (
                        float(wallet.get("availableBalance", usd_amount / 100)) * 100
                    )
                    usd_total = (
                        float(wallet.get("totalBalance", usd_amount / 100)) * 100
                    )
                    logger.info(
                        f"Parsed balance from funds.usdWallet: ${usd_amount / 100:.2f} USD"
                    )

            # Format 2: Simple balance/available/total format
            elif "balance" in response and isinstance(
                response["balance"], (int, float, str)
            ):
                usd_amount = float(response["balance"]) * 100
                usd_available = float(response.get("available", usd_amount / 100)) * 100
                usd_total = float(response.get("total", usd_amount / 100)) * 100
                logger.info(
                    f"Parsed balance from simple format: ${usd_amount / 100:.2f} USD"
                )

            # Format 3: Legacy usdAvailableToWithdraw only
            elif "usdAvailableToWithdraw" in response:
                usd_value = response["usdAvailableToWithdraw"]
                if isinstance(usd_value, str):
                    usd_available = float(usd_value.replace("$", "").strip()) * 100
                else:
                    usd_available = float(usd_value) * 100
                usd_amount = usd_available
                usd_total = usd_available
                logger.info(
                    f"Parsed balance from legacy format: ${usd_amount / 100:.2f} USD"
                )

        except (ValueError, TypeError, KeyError) as e:
            logger.warning(f"Error parsing balance from response: {e}")
            logger.debug(f"Raw response: {response}")

        # Normalize values
        if usd_available == 0 and usd_amount > 0:
            usd_available = usd_amount
        if usd_total == 0:
            usd_total = max(usd_amount, usd_available)

        return usd_amount, usd_available, usd_total

    async def _try_endpoints_for_balance(
        self,
        endpoints: list[str],
    ) -> tuple[dict[str, Any] | None, str | None, Exception | None]:
        """Try multiple endpoints to get balance data.

        Args:
            endpoints: List of endpoint URLs to try

        Returns:
            Tuple of (response_dict, successful_endpoint, last_error)
        """
        response = None
        last_error = None
        successful_endpoint = None

        for endpoint in endpoints:
            try:
                logger.info(f"Trying to get balance from endpoint {endpoint}")
                resp = await self._request("GET", endpoint)

                if resp and not ("error" in resp or "code" in resp):
                    logger.info(f"Successfully got balance from {endpoint}")
                    response = resp
                    successful_endpoint = endpoint
                    break

            except Exception as e:
                last_error = e
                logger.warning(f"Error querying {endpoint}: {e!s}")
                continue

        return response, successful_endpoint, last_error

    async def get_balance(self) -> dict[str, Any]:
        """Get user balance with multiple fallback methods.

        Returns:
            Balance information in format:
            {
                "usd": {"amount": value_in_cents},
                "has_funds": True/False,
                "balance": value_in_dollars,
                "available_balance": value_in_dollars,
                "total_balance": value_in_dollars,
                "error": True/False,
                "error_message": "Error message (if any)"
            }
        """
        logger.debug("Requesting DMarket user balance via universal method")

        if not self.public_key or not self.secret_key:
            logger.error("Error: API keys not configured (empty values)")
            return self._create_error_response(
                "API keys not configured",
                status_code=401,
                error_code="MISSING_API_KEYS",
            )

        try:
            # Try direct REST API request first
            try:
                logger.debug("🔍 Trying to get balance via direct REST API request...")
                direct_response = await self.direct_balance_request()
                logger.debug(f"🔍 Direct API response: {direct_response}")

                if direct_response and direct_response.get("success", False):
                    logger.info(
                        "✅ Successfully got balance via direct REST API request"
                    )
                    balance_data = direct_response.get("data", {})
                    logger.debug(f"📊 Balance data: {balance_data}")

                    usd_amount = balance_data.get("balance", 0) * 100
                    usd_available = (
                        balance_data.get("available", balance_data.get("balance", 0))
                        * 100
                    )
                    usd_total = (
                        balance_data.get("total", balance_data.get("balance", 0)) * 100
                    )
                    usd_locked = balance_data.get("locked", 0) * 100
                    usd_trade_protected = balance_data.get("trade_protected", 0) * 100

                    result = self._create_balance_response(
                        usd_amount=usd_amount,
                        usd_available=usd_available,
                        usd_total=usd_total,
                        locked_balance=usd_locked / 100,
                        trade_protected_balance=usd_trade_protected / 100,
                        additional_info={
                            "method": "direct_request",
                            "raw_response": balance_data,
                        },
                    )

                    logger.info(
                        f"💰 Final balance (direct request): ${result['balance']:.2f} USD "
                        f"(available: ${result['available_balance']:.2f}, locked: ${result.get('locked_balance', 0):.2f})"
                    )
                    return result

                error_message = direct_response.get("error", "Unknown error")
                logger.warning(f"⚠️ Direct REST API request failed: {error_message}")
                logger.debug(f"🔍 Full error response: {direct_response}")
            except Exception as e:
                logger.warning(f"⚠️ Error during direct REST API request: {e!s}")
                logger.exception(f"📋 Exception details: {e}")

            # Try all known endpoints
            endpoints = [
                self.ENDPOINT_BALANCE,
                "/api/v1/account/wallet/balance",
                "/exchange/v1/user/balance",
                self.ENDPOINT_BALANCE_LEGACY,
            ]

            response, successful_endpoint, last_error = (
                await self._try_endpoints_for_balance(endpoints)
            )

            if not response:
                error_message = (
                    str(last_error)
                    if last_error
                    else "Failed to get balance from any endpoint"
                )
                logger.error(f"Critical error getting balance: {error_message}")

                status_code = 500
                error_code = "REQUEST_FAILED"
                error_lower = error_message.lower()
                if "404" in error_message or "not found" in error_lower:
                    status_code = 404
                    error_code = "NOT_FOUND"
                elif "401" in error_message or "unauthorized" in error_lower:
                    status_code = 401
                    error_code = "UNAUTHORIZED"

                return self._create_error_response(
                    error_message, status_code, error_code
                )

            if response and ("error" in response or "code" in response):
                error_code = response.get("code", "unknown")
                error_message = response.get(
                    "message", response.get("error", "Unknown error")
                )
                status_code = response.get("status", response.get("status_code", 500))

                logger.error(
                    f"DMarket API error getting balance: {error_code} - {error_message} (HTTP {status_code})"
                )

                if error_code == "Unauthorized" or status_code == 401:
                    logger.error(
                        "Problem with API keys. Please check correctness and validity of DMarket API keys"
                    )
                    return self._create_error_response(
                        "Authorization error: invalid API keys",
                        status_code=401,
                        error_code="UNAUTHORIZED",
                    )

                return self._create_error_response(
                    error_message, status_code, error_code
                )

            logger.info(f"🔍 RAW BALANCE API RESPONSE (get_balance): {response}")
            logger.info(
                f"Analyzing balance response from {successful_endpoint}: {response}"
            )

            usd_amount, usd_available, usd_total = self._parse_balance_from_response(
                response
            )

            if usd_amount == 0 and usd_available == 0 and usd_total == 0:
                logger.warning(
                    f"Could not parse balance data from known formats: {response}"
                )

            result = self._create_balance_response(
                usd_amount=usd_amount,
                usd_available=usd_available,
                usd_total=usd_total,
                additional_info={"endpoint": successful_endpoint},
            )

            logger.info(
                f"Final balance: ${result['balance']:.2f} USD "
                f"(available: ${result['available_balance']:.2f}, total: ${result['total_balance']:.2f})"
            )
            return result

        except Exception as e:
            logger.exception(f"Unexpected error getting balance: {e!s}")
            logger.exception(f"Stack trace: {traceback.format_exc()}")

            error_str = str(e)
            status_code = 500
            error_code = "EXCEPTION"
            error_lower = error_str.lower()
            if "404" in error_str or "not found" in error_lower:
                status_code = 404
                error_code = "NOT_FOUND"
            elif "401" in error_str or "unauthorized" in error_lower:
                status_code = 401
                error_code = "UNAUTHORIZED"

            return self._create_error_response(error_str, status_code, error_code)

    async def get_user_balance(self) -> dict[str, Any]:
        """Get user balance (deprecated method).

        This method is kept for backward compatibility.
        Use get_balance() instead.

        Returns:
            Balance information in the same format as get_balance()
        """
        logger.warning(
            "Method get_user_balance() is deprecated and may be removed in future versions. "
            "Please use get_balance() instead.",
        )
        return await self.get_balance()

    async def get_user_profile(self) -> dict[str, Any]:
        """Get user profile according to DMarket API.

        Returns:
            User profile information
        """
        return await self._request(
            "GET",
            "/account/v1/user",
        )

    async def get_account_details(self) -> dict[str, Any]:
        """Get account details.

        Returns:
            Account information
        """
        return await self._request(
            "GET",
            self.ENDPOINT_ACCOUNT_DETAILS,
        )

    async def direct_balance_request(self) -> dict[str, Any]:
        """Execute direct balance request via REST API using Ed25519.

        This method is used as an alternative way to get balance
        in case of issues with the main method.

        Returns:
            Balance request result or error dict
        """
        try:
            endpoint = self.ENDPOINT_BALANCE
            base_url = self.api_url
            full_url = f"{base_url}{endpoint}"

            timestamp = str(int(time.time()))
            string_to_sign = f"GET{endpoint}{timestamp}"

            logger.debug(f"Direct balance request - string to sign: {string_to_sign}")

            try:
                secret_key_str = self._secret_key

                try:
                    if len(secret_key_str) == 64:
                        secret_key_bytes = bytes.fromhex(secret_key_str)
                    elif len(secret_key_str) == 44 or "=" in secret_key_str:
                        secret_key_bytes = base64.b64decode(secret_key_str)
                    elif len(secret_key_str) >= 64:
                        secret_key_bytes = bytes.fromhex(secret_key_str[:64])
                    else:
                        secret_key_bytes = secret_key_str.encode("utf-8")[:32].ljust(
                            32, b"\0"
                        )
                except Exception as conv_error:
                    logger.exception(
                        f"Error converting secret key in direct request: {conv_error}"
                    )
                    raise

                signing_key = nacl.signing.SigningKey(secret_key_bytes)
                signed = signing_key.sign(string_to_sign.encode("utf-8"))
                signature = signed.signature.hex()

                logger.debug("Direct balance request - signature generated")

            except Exception as sig_error:
                logger.exception(f"Error generating Ed25519 signature: {sig_error}")
                secret_key = self.secret_key
                signature = hmac.new(
                    secret_key,
                    string_to_sign.encode(),
                    hashlib.sha256,
                ).hexdigest()

            headers = {
                "X-Api-Key": self.public_key,
                "X-Sign-Date": timestamp,
                "X-Request-Sign": f"dmar ed25519 {signature}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            }

            logger.debug(f"Executing direct request to {endpoint}")

            client = await self._get_client()

            response = await call_with_circuit_breaker(
                client.get, full_url, headers=headers, timeout=10
            )

            if response.status_code == 200:
                try:
                    response_data = response.json()

                    if response_data:
                        logger.info(f"Successful direct request to {endpoint}")
                        logger.info(f"🔍 RAW BALANCE API RESPONSE: {response_data}")

                        usd_amount, usd_available, usd_total = (
                            self._parse_balance_from_response(response_data)
                        )

                        return {
                            "success": True,
                            "data": {
                                "balance": usd_amount / 100,
                                "available": usd_available / 100,
                                "total": usd_total / 100,
                                "raw_response": response_data,
                            },
                        }
                except Exception as parse_error:
                    logger.exception(
                        f"Error parsing direct balance response: {parse_error}"
                    )

            logger.warning(
                f"Direct balance request failed with status {response.status_code}: {response.text}"
            )
            return {
                "success": False,
                "error": f"HTTP {response.status_code}: {response.text}",
            }

        except Exception as e:
            logger.exception(f"Error during direct balance request: {e}")
            return {
                "success": False,
                "error": str(e),
            }
