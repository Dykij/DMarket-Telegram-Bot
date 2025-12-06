# Test Generation Prompts

При генерации тестов:

1. **Использовать pytest** с async поддержкой (`pytest-asyncio`)
2. **Мокировать внешние API** (DMarket API, Telegram API)
3. **Тестировать граничные случаи**: пустые значения, None, неверные типы
4. **Тестировать ошибки**: проверять правильность обработки исключений
5. **Использовать фикстуры** для повторяющихся данных
6. **Структура теста**: Arrange-Act-Assert
7. **Имена тестов**: `test_<функция>_<условие>_<ожидаемый_результат>`
8. **Coverage**: Стремиться к 80%+ покрытию

Пример:
```python
@pytest.mark.asyncio
async def test_fetch_market_data_returns_valid_data_on_success(mock_api):
    # Arrange
    expected_data = {"item_id": "123", "price": 10.50}
    mock_api.get.return_value = expected_data

    # Act
    result = await fetch_market_data("123")

    # Assert
    assert result == expected_data
    assert result["price"] > 0
```
