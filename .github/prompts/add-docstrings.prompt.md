---
description: 'Add comprehensive docstrings to Python functions'
mode: 'agent'
---

# Documentation Prompt - Add Docstrings

Add Google-style docstrings to the selected functions:

## Docstring Template

```python
async def function_name(
    param1: str,
    param2: int,
    optional: bool = False
) -> dict[str, Any]:
    """Brief one-line description.

    Longer description if needed, explaining the purpose,
    algorithm, or important notes about the function.

    Args:
        param1: Description of first parameter.
        param2: Description of second parameter.
        optional: Description with default value noted.

    Returns:
        Description of return value with structure example:
        {"key": "value", "count": 42}

    Raises:
        ValueError: When param1 is empty.
        httpx.HTTPError: When API request fails.

    Example:
        >>> result = await function_name("test", 10)
        >>> print(result["key"])
        'test_processed'
    """
```

## Rules

- First line: imperative mood, ends with period
- Args: describe each parameter, note defaults
- Returns: describe structure with example
- Raises: list all possible exceptions
- Example: include for complex functions
