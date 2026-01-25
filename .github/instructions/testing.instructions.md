---
description: 'Testing conventions for test files'
applyTo: 'tests/**/*.py'
---

# Test File Instructions

Apply these standards to all test files:

## Test Structure
- Use AAA pattern: Arrange, Act, Assert
- One assertion focus per test
- Use descriptive test names: `test_<function>_<condition>_<result>`

## Async Tests
- Use `@pytest.mark.asyncio` decorator
- Use `AsyncMock` for mocking async functions
- Mock external dependencies (API, DB, Redis)

## Fixtures
- Define reusable fixtures in `conftest.py`
- Use scope appropriately (function, module, session)
- Clean up resources in fixture teardown

## Mocking
- Mock at the boundary (API client, not internal functions)
- Verify mock calls with `assert_called_once_with`
- Use `side_effect` for simulating errors

## Test Data
- Use factories for complex objects
- Keep test data minimal and focused
- Use `@pytest.mark.parametrize` for multiple inputs

## Markers
- Use `@pytest.mark.slow` for long-running tests
- Use `@pytest.mark.integration` for integration tests
- Use `@pytest.mark.e2e` for end-to-end tests

## Balance API Format
- Use `{"balance": 100.0}` (dollars) not `{"usd": 10000}` (cents)
- This is the current API format as of January 2026
