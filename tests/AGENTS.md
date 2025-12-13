# AGENTS.md — Testing Module

> Специфичные инструкции для написания и запуска тестов.
> Общие правила: см. корневой `/AGENTS.md`

## 🧪 Типы тестов

| Тип         | Директория              | Количество | Назначение                  |
| ----------- | ----------------------- | ---------- | --------------------------- |
| Unit        | `tests/unit/`           | ~2500      | Изолированные тесты функций |
| Integration | `tests/integration/`    | ~40        | Взаимодействие модулей      |
| Contract    | `tests/contracts/`      | 43         | Pact Consumer-Driven        |
| Property    | `tests/property_based/` | ~20        | Hypothesis генеративные     |

## ✅ AAA Паттерн (Arrange-Act-Assert)

```python
@pytest.mark.asyncio
async def test_get_balance_returns_valid_data():
    """Тест: get_balance возвращает корректные данные."""

    # Arrange - подготовка
    api_client = DMarketAPI(public_key="test", secret_key="test")
    mock_response = {"usd": "10000", "dmc": "5000"}

    # Act - действие
    with patch.object(api_client, '_request', return_value=mock_response):
        balance = await api_client.get_balance()

    # Assert - проверка
    assert balance["usd"] == "10000"
    assert balance["dmc"] == "5000"
```

## 📋 Именование тестов

```python
# Формат: test_<функция>_<условие>_<результат>

# ✅ Хорошие имена
def test_calculate_profit_with_zero_price_returns_zero(): ...
def test_create_target_with_invalid_price_raises_validation_error(): ...
def test_scan_arbitrage_when_no_items_returns_empty_list(): ...

# ❌ Плохие имена
def test_profit(): ...
def test_target(): ...
def test_1(): ...
```

## 🔧 Полезные фикстуры

```python
# conftest.py
import pytest
from unittest.mock import AsyncMock

@pytest.fixture
def mock_dmarket_api():
    """Мок DMarket API клиента."""
    api = AsyncMock(spec=DMarketAPI)
    api.get_balance = AsyncMock(return_value={"usd": "10000", "dmc": "5000"})
    api.get_market_items = AsyncMock(return_value={"objects": []})
    return api

@pytest.fixture
async def test_database():
    """Тестовая БД в памяти."""
    db = DatabaseManager("sqlite:///:memory:")
    await db.init_database()
    yield db
    await db.close()
```

## 📼 VCR.py — HTTP записи

```python
import pytest

@pytest.mark.vcr()
@pytest.mark.asyncio
async def test_get_market_items():
    """Тест с записью HTTP (cassette: test_get_market_items.yaml)."""
    api = DMarketAPI(public_key="test", secret_key="test")
    items = await api.get_market_items(game="csgo", limit=10)

    assert "objects" in items
    assert len(items["objects"]) <= 10
```

### Режимы записи
```bash
# Первый запуск - запись
pytest tests/dmarket/test_api.py

# Перезаписать все кассеты
pytest --vcr-record=all tests/

# Только воспроизведение (CI)
pytest --vcr-record=none tests/
```

## 🤝 Pact — Contract тесты

```python
# tests/contracts/test_account_contracts.py
import pytest
from pact import Consumer, Provider

@pytest.fixture
def pact():
    return Consumer('DMarketBot').has_pact_with(Provider('DMarketAPI'))

def test_get_balance_contract(pact):
    """Контракт: GET /account/v1/balance."""
    pact.given("user has balance").upon_receiving(
        "a request for balance"
    ).with_request(
        method="GET",
        path="/account/v1/balance"
    ).will_respond_with(
        status=200,
        body={"usd": "10000", "dmc": "5000"}
    )

    with pact:
        result = api.get_balance()
        assert result["usd"] == "10000"
```

## 🎲 Hypothesis — Property-based

```python
from hypothesis import given, strategies as st

@given(
    buy_price=st.floats(min_value=0.01, max_value=10000),
    sell_price=st.floats(min_value=0.01, max_value=10000),
    commission=st.floats(min_value=0, max_value=100)
)
def test_profit_never_exceeds_price_difference(buy_price, sell_price, commission):
    """Прибыль не может превышать разницу цен."""
    profit = calculate_profit(buy_price, sell_price, commission)

    max_possible = sell_price - buy_price
    assert profit <= max_possible
```

## 🏃 Команды запуска

```bash
# Все тесты
pytest tests/ -v

# С покрытием
pytest --cov=src --cov-report=html --cov-report=term

# Конкретный модуль
pytest tests/dmarket/test_arbitrage_scanner.py -v

# По маркеру
pytest -m "asyncio" tests/
pytest -m "not slow" tests/

# Параллельно
pytest -n auto tests/

# Остановка на первой ошибке
pytest -x tests/
```

## 📊 Покрытие

```bash
# Генерация отчета
pytest --cov=src --cov-report=html

# Открыть отчет
start htmlcov/index.html  # Windows
open htmlcov/index.html   # macOS
```

### Цели покрытия
| Модуль              | Цель | Приоритет |
| ------------------- | ---- | --------- |
| `src/dmarket/`      | 85%+ | Высокий   |
| `src/telegram_bot/` | 80%+ | Средний   |
| `src/utils/`        | 90%+ | Высокий   |

## ⚠️ Типичные ошибки

1. **Забыл `@pytest.mark.asyncio`** — тест не выполняется как async
2. **Моки не сбрасываются** — использовать `with patch()` или фикстуры
3. **Тесты зависят друг от друга** — каждый тест должен быть независим
4. **Тестирование реального API** — использовать VCR.py или моки

## 🔍 Отладка тестов

```bash
# Подробный вывод
pytest -v -s tests/test_file.py

# Остановка в отладчике
pytest --pdb tests/test_file.py

# Показать локальные переменные при ошибке
pytest -l tests/test_file.py
```

---

*См. также: `docs/testing_guide.md`, `docs/CONTRACT_TESTING.md`*
