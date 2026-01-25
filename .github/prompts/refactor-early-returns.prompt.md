---
description: 'Refactor Python code to use early returns and reduce nesting'
mode: 'agent'
---

# Refactoring Prompt - Early Returns

Refactor the selected code to use early returns and reduce nesting:

## Goals

1. **Reduce nesting** to maximum 3 levels
2. **Use early returns** for validation and error cases
3. **Improve readability** with guard clauses

## Before Pattern (Nested)

```python
async def process_item(item):
    if item.price > 0:
        if item.suggested_price > 0:
            if item.profit_margin > 3:
                if await check_liquidity(item):
                    return await execute_trade(item)
    return None
```

## After Pattern (Early Returns)

```python
async def process_item(item):
    """Process item with validation."""
    if item.price <= 0:
        return None

    if item.suggested_price <= 0:
        return None

    if item.profit_margin <= 3:
        return None

    if not await check_liquidity(item):
        return None

    return await execute_trade(item)
```

## Rules

- Invert conditions and return early
- Keep the happy path at the end
- Add brief comments for complex conditions
- Maintain original functionality
