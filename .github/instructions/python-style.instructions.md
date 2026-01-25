---
description: 'Code style and conventions for Python files in src/ directory'
applyTo: 'src/**/*.py'
---

# Python Code Style Instructions

Apply these standards to all Python files in `src/`:

## Type Annotations
- Use Python 3.11+ syntax: `list[str]` not `List[str]`
- Use `|` for union types: `str | None` not `Optional[str]`
- Always annotate function parameters and return types

## Async Code
- Use `async def` for all I/O operations
- Use `await` for all async calls
- Use `asyncio.gather()` for parallel execution
- Use `httpx.AsyncClient` for HTTP requests

## Error Handling
- Never use bare `except:`
- Catch specific exceptions
- Log errors with context using structlog
- Re-raise or return meaningful error messages

## Imports
- Use absolute imports
- Group: stdlib, third-party, local
- Sort alphabetically within groups

## Docstrings
- Use Google style docstrings
- Document Args, Returns, Raises
- Include usage examples for complex functions

## Logging
- Use `structlog.get_logger(__name__)`
- Include context: user_id, item_id, etc.
- Never log sensitive data (tokens, keys)

## Naming
- snake_case for functions and variables
- PascalCase for classes
- UPPER_CASE for constants
- Prefix private methods with underscore
