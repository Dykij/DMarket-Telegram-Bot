---
id: api-integration
name: API Integration
description: Generate API client integration with DMarket/Waxpeer patterns
category: api
variables: [api_name, base_url, auth_type]
---

Generate an API client integration for {{api_name}}.

## API Details
- **Name**: {{api_name}}
- **Base URL**: {{base_url|https://api.example.com}}
- **Auth Type**: {{auth_type|api_key}}

## Requirements

1. Async client with httpx
2. Rate limiting support
3. Retry logic with tenacity
4. Proper error handling
5. Response validation with Pydantic
6. Structured logging

## DMarket API Notes
- Prices in **CENTS**: 1000 = $10.00
- Commission: 7%
- Rate limit: 30 req/min

## Waxpeer API Notes
- Prices in **MILS**: 1000 mils = $1.00
- Commission: 6%
- Rate limit: 60 req/min

## Template

```python
from typing import Any

import httpx
import structlog
from aiolimiter import AsyncLimiter
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential

logger = structlog.get_logger(__name__)


class {{api_name}}Response(BaseModel):
    """Response model for {{api_name}} API."""

    success: bool
    data: dict[str, Any] | None = None
    error: str | None = None


class {{api_name}}Client:
    """Client for {{api_name}} API.

    Example:
        ```python
        client = {{api_name}}Client(api_key="your-key")
        result = await client.get_items("csgo")
        ```
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "{{base_url|https://api.example.com}}",
        rate_limit: int = 30,
    ) -> None:
        """Initialize the client.

        Args:
            api_key: API key for authentication
            base_url: Base URL of the API
            rate_limit: Requests per minute limit
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self._limiter = AsyncLimiter(rate_limit, 60)
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=30.0,
                headers=self._get_headers(),
            )
        return self._client

    def _get_headers(self) -> dict[str, str]:
        """Get authentication headers."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Make an API request with rate limiting and retry.

        Args:
            method: HTTP method
            endpoint: API endpoint
            **kwargs: Additional request arguments

        Returns:
            API response data

        Raises:
            httpx.HTTPError: If request fails
        """
        async with self._limiter:
            client = await self._get_client()

            logger.debug(
                "api_request",
                method=method,
                endpoint=endpoint,
            )

            response = await client.request(method, endpoint, **kwargs)
            response.raise_for_status()

            return response.json()

    async def get_items(self, game: str) -> list[dict[str, Any]]:
        """Get market items for a game.

        Args:
            game: Game identifier (csgo, dota2, tf2, rust)

        Returns:
            List of market items
        """
        data = await self._request("GET", f"/items/{game}")
        return data.get("items", [])

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
```

Generate the {{api_name}} client now.
