# 🧪 Testing Complete Guide

> **Объединённое руководство** - стратегия тестирования + практическое руководство

---

## 📖 Содержание

1. [Testing Strategy](#testing-strategy)
2. [Practical Testing Guide](#practical-testing-guide)
3. [Running Tests](#running-tests)
4. [Writing Tests](#writing-tests)
5. [Advanced Topics](#advanced-topics)

---

# Testing Strategy

# Testing Strategy

## Overview

This document outlines the comprehensive testing strategy for the DMarket Telegram Bot project.

---

## Test Pyramid

```
        /\
       /  \
      / E2E \ (10-15%)
     /______\
    /        \
   / Integration \ (20-25%)
  /______________\
 /                \
/   Unit Tests     \ (60-70%)
\__________________/
```

---

## 1. Unit Tests (60-70% coverage)

### Purpose

Test individual functions and methods in isolation.

### Location

- `tests/unit/`

### Framework

- `pytest`
- `pytest-asyncio`
- `pytest-mock`

### Guidelines

- Test one thing per test
- Use AAA pattern (Arrange-Act-Assert)
- Mock external dependencies
- Test edge cases and error handling

### Example

```python
@pytest.mark.asyncio
async def test_calculate_profit_returns_correct_value():
    """Test profit calculation with standard inputs."""
    # Arrange
    buy_price = 10.00
    sell_price = 15.00
    commission = 7.0

    # Act
    profit = calculate_profit(buy_price, sell_price, commission)

    # Assert
    assert profit == 3.95
```

---

## 2. Integration Tests (20-25% coverage)

### Purpose

Test interactions between multiple components.

### Location

- `tests/integration/`

### What to Test

- API client with mocked HTTP responses
- Database operations
- Cache interactions
- Message queue processing

### Example

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_arbitrage_scanner_with_api():
    """Test scanner integrates correctly with API client."""
    # Arrange
    api_client = DMarketAPI(public_key="test", secret_key="test")
    scanner = ArbitrageScanner(api_client=api_client)

    # Mock API response
    with patch.object(api_client, 'get_market_items'):
        # Act
        results = await scanner.scan_level("standard", "csgo")

        # Assert
        assert len(results) > 0
```

---

## 3. E2E Tests (10-15% coverage)

### Purpose

Test complete user workflows from start to finish.

### Location

- `tests/e2e/`

### What to Test

- Complete arbitrage flow (scan → analyze → notify)
- Target management flow (create → monitor → execute)
- Notification delivery flow (trigger → queue → deliver)
- User settings flow (update → apply → verify)

### Example

```python
@pytest.mark.e2e
@pytest.mark.asyncio
async def test_complete_arbitrage_workflow():
    """Test full arbitrage workflow."""
    # 1. Scan market
    opportunities = await scanner.scan_level("standard", "csgo")

    # 2. Select best opportunity
    best = max(opportunities, key=lambda x: x.profit_margin)

    # 3. Create target
    target = await target_manager.create_target(
        game="csgo",
        item_title=best.title,
        price=best.buy_price
    )

    # 4. Verify notification sent
    assert notification_queue.size() > 0
```

---

## 4. Contract Testing (Pact)

### Purpose

Verify API contracts between consumer and provider.

### Location

- `tests/contracts/`

### What to Test

- DMarket API responses match expected schema
- Telegram Bot API requests are correct
- WebSocket message formats

### Example

```python
@pytest.mark.contract
def test_dmarket_api_balance_contract():
    """Test DMarket balance endpoint contract."""
    pact.given("User has balance") \
        .upon_receiving("A balance request") \
        .with_request("GET", "/account/v1/balance") \
        .will_respond_with(200, body={
            "usd": Matcher("10000"),
            "dmc": Matcher("5000")
        })
```

---

## 5. Property-Based Testing (Hypothesis)

### Purpose

Test properties that should hold for all inputs.

### Location

- Mixed with unit tests

### Example

```python
from hypothesis import given, strategies as st

@given(
    buy_price=st.floats(min_value=0.01, max_value=10000),
    sell_price=st.floats(min_value=0.01, max_value=10000)
)
def test_profit_is_always_less_than_sell_price(buy_price, sell_price):
    """Property: profit should never exceed sell price."""
    if sell_price > buy_price:
        profit = calculate_profit(buy_price, sell_price, 7.0)
        assert profit < sell_price
```

---

## Test Execution

### Run All Tests

```bash
pytest tests/
```

### Run by Type

```bash
# Unit tests only
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -m integration

# E2E tests
pytest tests/e2e/ -m e2e

# Exclude slow tests
pytest -m "not e2e"
```

### With Coverage

```bash
pytest --cov=src --cov-report=html --cov-report=term-missing
```

---

## CI/CD Integration

### GitHub Actions Workflow

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt

      - name: Run unit tests
        run: pytest tests/unit/ -v

      - name: Run integration tests
        run: pytest tests/integration/ -m integration

      - name: Run E2E tests
        run: pytest tests/e2e/ -m e2e

      - name: Generate coverage
        run: pytest --cov=src --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

---

## Test Data Management

### Fixtures

- Use `conftest.py` for shared fixtures
- Create realistic test data
- Use factories for complex objects

### VCR.py

- Record HTTP interactions
- Replay in tests
- Located in `tests/cassettes/`

### Example

```python
@pytest.mark.vcr()
async def test_api_with_recorded_response():
    """Test using VCR recorded response."""
    api = DMarketAPI(public_key="test", secret_key="test")
    balance = await api.get_balance()
    assert balance is not None
```

---

## Performance Testing

### Load Testing

- Use `locust` for load testing
- Test API rate limits
- Verify scalability

### Profiling

- Use `py-spy` for profiling
- Monitor memory usage
- Identify bottlenecks

---

## Test Quality Metrics

### Target Coverage

- **Unit Tests**: 80-85%
- **Integration Tests**: 60-70%
- **E2E Tests**: 40-50%
- **Overall**: 85%+

### Test Quality Checks

- ✅ No flaky tests
- ✅ Fast execution (<5 minutes)
- ✅ Clear test names
- ✅ Independent tests
- ✅ Proper mocking

---

## Best Practices

### DO ✅

- Write tests before fixing bugs
- Keep tests simple and focused
- Use descriptive test names
- Test edge cases
- Mock external dependencies
- Clean up resources

### DON'T ❌

- Test implementation details
- Write interdependent tests
- Use magic numbers
- Skip error cases
- Leave commented code
- Ignore flaky tests

---

## Debugging Failed Tests

### Steps

1. **Read error message** - understand what failed
2. **Check recent changes** - what code changed?
3. **Reproduce locally** - run test in isolation
4. **Add logging** - use `logger.debug()` liberally
5. **Use debugger** - `pytest --pdb`
6. **Check fixtures** - verify test data is correct

### Example

```bash
# Run single test with verbose output
pytest tests/unit/test_arbitrage_scanner.py::test_scan_level -vv

# Run with debugger on failure
pytest tests/unit/ --pdb

# Run with print statements visible
pytest tests/unit/ -s
```

---

## Maintenance

### Regular Tasks

- **Weekly**: Review test coverage reports
- **Monthly**: Update test data
- **Quarterly**: Refactor slow tests
- **Annually**: Review testing strategy

### Test Cleanup

- Remove obsolete tests
- Update deprecated patterns
- Improve test performance
- Reduce duplication

---

## Resources

### Documentation

- [pytest docs](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [Hypothesis](https://hypothesis.readthedocs.io/)
- [Pact Python](https://github.com/pact-foundation/pact-python)

### Internal Docs

- `docs/TESTING_GUIDE.md` - detailed testing guide
- `docs/CONTRACT_TESTING.md` - contract testing guide
- `tests/README.md` - test suite overview

---

**Last Updated**: January 1, 2026
**Version**: 1.0.0


---

# Practical Testing Guide

# Руководство по запуску тестов

**Версия**: 1.0.0
**Последнее обновление**: 28 декабря 2025 г.

---

В этом руководстве объясняется, как правильно запустить тесты в проекте DMarket Tools с корректной настройкой PYTHONPATH.

## Настройка PYTHONPATH

Тесты в проекте DMarket Tools используют относительные импорты из корневой директории проекта. Для корректной работы этих импортов необходимо добавить корневую директорию проекта в PYTHONPATH.

### Windows (PowerShell)

```powershell
# Временная настройка в текущей сессии
$env:PYTHONPATH = "$(Get-Location)"

# Запуск всех тестов
python -m pytest tests

# Запуск конкретного теста
python -m pytest tests/test_bot_v2.py
```

### Linux/macOS (Bash)

```bash
# Временная настройка в текущей сессии
export PYTHONPATH=$(pwd)

# Запуск всех тестов
python -m pytest tests

# Запуск конкретного теста
python -m pytest tests/test_bot_v2.py
```

## Использование VS Code

### Настройка VS Code для тестирования

1. Откройте VS Code settings.json (Ctrl+Shift+P -> Preferences: Open Settings (JSON))
2. Добавьте следующие настройки:

```json
{
    "python.testing.pytestEnabled": true,
    "python.envFile": "${workspaceFolder}/.env",
    "python.analysis.extraPaths": ["${workspaceFolder}"]
}
```

3. Теперь вы можете использовать встроенную в VS Code панель тестирования для запуска тестов.

## Запуск конкретных тестов

### Запуск по имени модуля

```
python -m pytest tests/test_bot_v2.py
```

### Запуск по имени теста

```
python -m pytest tests/test_bot_v2.py::test_start_command
```

### Запуск с повышенной детализацией

```
python -m pytest tests/test_bot_v2.py -v
```

## Отладка тестов

### Отладка в VS Code

1. Установите точки останова в коде теста
2. Выберите тест в панели тестирования VS Code
3. Щелкните правой кнопкой мыши и выберите "Debug Test"

### Отладка с помощью pdb

```
python -m pytest tests/test_bot_v2.py --pdb
```

## Дополнительные опции pytest

- `--pdb`: Вход в отладчик при ошибке
- `-v`: Подробный вывод
- `-xvs`: Отключает захват вывода, полезно для отладки
- `--no-header --no-summary -q`: Минимальный вывод
- `-k "expression"`: Запускает тесты, соответствующие выражению

## Примечания

- Тесты используют асинхронные функции, требующие поддержки pytest-asyncio
- Файл конфигурации pytest находится в `pyproject.toml`
- При запуске тестов через VS Code убедитесь, что выбран правильный интерпретатор Python

---

## VCR.py - Запись и воспроизведение HTTP-взаимодействий

VCR.py позволяет записывать HTTP-взаимодействия с внешними API и воспроизводить
их в тестах. Это обеспечивает:

- **Детерминированность** - одинаковые ответы при каждом запуске
- **Скорость** - нет сетевых задержек
- **Офлайн-тестирование** - тесты работают без доступа к API
- **CI/CD** - не нужны реальные API ключи

### Конфигурация

Конфигурация VCR находится в `tests/conftest_vcr.py`. Кассеты (записи HTTP)
хранятся в `tests/cassettes/`.

### Использование в тестах

```python
import pytest

@pytest.mark.vcr()
@pytest.mark.asyncio()
async def test_get_balance(vcr_cassette_async):
    """Тест получения баланса с записью HTTP."""
    api = DMarketAPI(public_key="test", secret_key="test")
    balance = await api.get_balance()
    assert "balance" in balance
```

### Основные фикстуры

| Фикстура              | Описание                          |
| --------------------- | --------------------------------- |
| `vcr_cassette`        | Автоматическое имя кассеты        |
| `vcr_cassette_async`  | Для async тестов (httpx, aiohttp) |
| `vcr_cassette_custom` | Кастомное имя кассеты             |
| `vcr_cassette_dir`    | Путь к директории кассет модуля   |

### Режимы записи

```bash
# Первый запуск - запись кассет
pytest tests/dmarket/test_api.py

# Записать только новые кассеты
pytest --vcr-record=new_episodes tests/

# Перезаписать все кассеты
pytest --vcr-record=all tests/dmarket/test_api.py

# Не записывать, только воспроизведение
pytest --vcr-record=none tests/
```

### Структура кассет

```text
tests/cassettes/
├── dmarket/
│   ├── test_dmarket_api/
│   │   ├── test_get_balance.yaml
│   │   └── test_get_market_items.yaml
│   └── test_arbitrage_scanner/
│       └── test_scan_level.yaml
└── telegram/
    └── test_bot_commands/
        └── test_start.yaml
```

### Фильтрация чувствительных данных

VCR автоматически фильтрует:

- `X-Api-Key` - API ключ DMarket
- `X-Sign-Date` - timestamp подписи
- `X-Request-Sign` - HMAC подпись
- `Authorization` - токены авторизации
- `Cookie` - куки сессии

### Пример: Миграция теста с httpx-mock на VCR

**До (httpx-mock):**

```python
async def test_get_balance(httpx_mock):
    httpx_mock.add_response(
        url="https://api.dmarket.com/account/v1/balance",
        json={"balance": 100.50}
    )
    api = DMarketAPI(...)
    balance = await api.get_balance()
    assert balance["balance"] == 100.50
```

**После (VCR.py):**

```python
@pytest.mark.vcr()
async def test_get_balance(vcr_cassette_async):
    # Первый запуск: реальный API вызов, запись в кассету
    # Последующие запуски: воспроизведение из кассеты
    api = DMarketAPI(...)
    balance = await api.get_balance()
    assert balance["balance"] >= 0
```

### Полезные советы

1. **Коммитьте кассеты в git** - они содержат ожидаемые ответы API
2. **Перезаписывайте при изменении API** - `--vcr-record=all`
3. **Используйте `@pytest.mark.vcr()`** для маркировки тестов
4. **Проверяйте фильтрацию** - убедитесь, что секреты не попадают в кассеты

---

## Управление логами в тестах

При запуске большого количества тестов логи могут стать трудночитаемыми.
Проект предоставляет несколько способов управления verbosity логов.

### Переменные окружения

```bash
# Установить уровень логирования для тестов
export TEST_LOG_LEVEL=DEBUG   # DEBUG, INFO, WARNING, ERROR

# Включить structlog форматирование
export TEST_LOG_STRUCTLOG=1

# Использовать JSON формат
export TEST_LOG_JSON=1

# Запустить тесты
python -m pytest tests/
```

### Опции командной строки pytest

```bash
# Показать логи в консоли с определенным уровнем
pytest --log-cli-level=INFO tests/

# Подавить все логи (только вывод тестов)
pytest --log-cli-level=CRITICAL tests/

# Сохранить подробные логи в файл
pytest --log-file=tests.log --log-file-level=DEBUG tests/

# Показать WARNING и выше в консоли, DEBUG в файл
pytest --log-cli-level=WARNING --log-file=debug.log --log-file-level=DEBUG tests/
```

### Маркеры pytest

```python
import pytest

@pytest.mark.quiet_logs
def test_something_noisy():
    """Логи будут полностью подавлены."""
    noisy_function()

@pytest.mark.verbose_logs
def test_need_debugging():
    """Будут показаны все DEBUG логи."""
    complex_function()

@pytest.mark.log_level("ERROR")
def test_only_errors():
    """Показать только ERROR и выше."""
    function_with_warnings()
```

### Фикстуры для тестов

```python
def test_with_suppressed_logs(suppress_logs):
    """Фикстура suppress_logs подавляет все логи."""
    noisy_function()

def test_with_debug_logs(enable_debug_logs):
    """Фикстура enable_debug_logs показывает DEBUG."""
    function_with_detailed_logging()

def test_log_assertions(log_capture):
    """Фикстура log_capture позволяет проверять содержимое логов."""
    my_function()
    assert "expected" in log_capture.text
```

### Класс LogAssertions

```python
from tests.conftest import LogAssertions

def test_error_logging(caplog):
    """Проверка что ошибки логируются корректно."""
    function_that_logs_error()

    # Проверить наличие сообщения
    LogAssertions.assert_logged(caplog, "error occurred", level="ERROR")

    # Проверить отсутствие чувствительных данных
    LogAssertions.assert_not_logged(caplog, "password")
    LogAssertions.assert_not_logged(caplog, "api_key")

    # Shortcut для ошибок
    LogAssertions.assert_error_logged(caplog, "connection failed")
```

### Рекомендации по читаемости логов

1. **Для CI/CD**: Используйте `--log-cli-level=WARNING` чтобы видеть только важные сообщения
2. **Для отладки**: Используйте `--log-cli-level=DEBUG` или `--log-file`
3. **Для быстрого прогона**: Используйте `--no-header --no-summary -q` плюс подавление логов
4. **Для анализа**: Сохраняйте в JSON формат с `TEST_LOG_JSON=1` и анализируйте с `jq`

### Пример фильтрации логов с jq

```bash
# Запустить тесты с JSON логами
TEST_LOG_JSON=1 pytest --log-file=tests.json tests/

# Показать только ERROR логи
cat tests.json | jq 'select(.level == "ERROR")'

# Показать логи определенного модуля
cat tests.json | jq 'select(.logger | contains("dmarket"))'

# Статистика по уровням
cat tests.json | jq -s 'group_by(.level) | map({level: .[0].level, count: length})'
```

