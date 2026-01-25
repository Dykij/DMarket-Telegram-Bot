---
description: 'Generate async Python code following best practices for DMarket Telegram Bot'
mode: 'agent'
---

# Async Python Code Generator

Generate async Python code following these guidelines:

## Requirements

1. **Always use `async/await`** for I/O operations
2. **Use `httpx`** for HTTP requests (not `requests`)
3. **Use `asyncio.gather()`** for parallel operations
4. **Add proper type annotations** using Python 3.11+ syntax
5. **Handle exceptions** with specific types, not bare `except:`
6. **Use `structlog`** for logging with context

## Code Template

```python
import asyncio
from typing import Any

import httpx
import structlog

logger = structlog.get_logger(__name__)

async def example_function(item_id: str) -> dict[str, Any]:
    """Brief description.
    
    Args:
        item_id: Description of parameter
        
    Returns:
        Description of return value
        
    Raises:
        httpx.HTTPError: When request fails
    """
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(f"/api/items/{item_id}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error("request_failed", item_id=item_id, error=str(e))
            raise
```

## Apply this prompt when:
- Creating new async functions
- Refactoring sync code to async
- Working with DMarket/Waxpeer API clients
