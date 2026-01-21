---
description: 'Generate pytest tests following AAA pattern for DMarket Telegram Bot'
mode: 'agent'
---

# Test Generator

Generate pytest tests following these guidelines:

## Requirements

1. **Use AAA pattern**: Arrange, Act, Assert
2. **Descriptive test names**: `test_<function>_<condition>_<expected>`
3. **Use `@pytest.mark.asyncio`** for async tests
4. **Mock external dependencies** with `AsyncMock`
5. **Use fixtures** for reusable setup
6. **Test edge cases** and error handling

## Test Template

```python
import pytest
from unittest.mock import AsyncMock, patch

@pytest.fixture
def mock_api_client():
    """Fixture for mocked API client."""
    client = AsyncMock()
    client.get_balance = AsyncMock(return_value={"balance": 100.0})
    return client

class TestFunctionName:
    """Tests for function_name."""

    @pytest.mark.asyncio
    async def test_function_name_with_valid_input_returns_expected(
        self, mock_api_client
    ):
        """Test that function returns expected result with valid input."""
        # Arrange
        expected = {"success": True}
        mock_api_client.some_method = AsyncMock(return_value=expected)

        # Act
        result = await function_name(mock_api_client, "test_param")

        # Assert
        assert result == expected
        mock_api_client.some_method.assert_called_once_with("test_param")

    @pytest.mark.asyncio
    async def test_function_name_with_invalid_input_raises_error(
        self, mock_api_client
    ):
        """Test that function raises error with invalid input."""
        # Arrange
        mock_api_client.some_method = AsyncMock(side_effect=ValueError("Invalid"))

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            await function_name(mock_api_client, "invalid")

        assert "Invalid" in str(exc_info.value)

    @pytest.mark.parametrize("input_val,expected", [
        ("valid1", True),
        ("valid2", True),
        ("", False),
    ])
    def test_function_name_parametrized(self, input_val, expected):
        """Test function with multiple inputs."""
        result = validate_input(input_val)
        assert result == expected
```

## Apply this prompt when:
- Writing new tests
- Adding test coverage
- Testing async functions
