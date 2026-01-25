---
description: 'Add error handling with tenacity retry logic'
mode: 'agent'
---

# Error Handling Prompt - Retry Logic

Add robust error handling with tenacity retry logic:

## Retry Pattern

```python
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)
import httpx
import structlog

logger = structlog.get_logger(__name__)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
    before_sleep=before_sleep_log(logger, log_level=logging.WARNING),
)
async def fetch_with_retry(url: str) -> dict[str, Any]:
    """Fetch URL with automatic retry on failure.
    
    Args:
        url: The URL to fetch.
        
    Returns:
        JSON response data.
        
    Raises:
        httpx.HTTPError: After all retry attempts exhausted.
    """
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()
```

## Rate Limit Handling

```python
from tenacity import retry_if_result

def is_rate_limited(response):
    return response.status_code == 429

@retry(
    retry=retry_if_result(is_rate_limited),
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=2, min=4, max=60),
)
async def api_call_with_rate_limit():
    ...
```

## Rules

- Always set stop condition (attempts or time)
- Use exponential backoff for API calls
- Log retry attempts with context
- Re-raise final exception with context
