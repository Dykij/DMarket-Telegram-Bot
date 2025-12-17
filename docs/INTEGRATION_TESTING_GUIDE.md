# 🧪 Руководство по интеграционному тестированию

**Версия**: 1.0
**Дата создания**: 24 декабря 2025 г.
**Последнее обновление**: 24 декабря 2025 г.

---

## 📋 Оглавление

1. [Введение](#введение)
2. [Настройка окружения](#настройка-окружения)
3. [Создание моков с pytest-httpx](#создание-моков-с-pytest-httpx)
4. [Примеры integration тестов](#примеры-integration-тестов)
5. [Тестирование edge cases](#тестирование-edge-cases)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)

---

## 🎯 Введение

### Что такое интеграционные тесты?

**Интеграционные тесты** проверяют взаимодействие между различными компонентами системы:

- Взаимодействие с внешними API (DMarket API)
- Работа с базой данных
- Обработка HTTP запросов и ответов
- Корректность обработки ошибок сети

### Отличие от юнит-тестов

| Характеристика  | Юнит-тесты          | Интеграционные тесты               |
| --------------- | ------------------- | ---------------------------------- |
| **Область**     | Одна функция/класс  | Несколько компонентов              |
| **Зависимости** | Все замокированы    | Реальные или частично замокированы |
| **Скорость**    | Очень быстро (мс)   | Медленнее (секунды)                |
| **Сложность**   | Простые             | Сложные сценарии                   |
| **Цель**        | Корректность логики | Корректность интеграции            |

### Структура тестов в проекте

```
tests/
├── unit/                          # Юнит-тесты
│   ├── dmarket/
│   │   ├── test_arbitrage.py
│   │   └── test_targets.py
│   └── utils/
│       └── test_rate_limiter.py
│
├── integration/                   # Интеграционные тесты
│   ├── test_api_with_httpx_mock.py   # DMarket API моки
│   ├── test_database_integration.py   # БД интеграция
│   └── test_telegram_bot_integration.py
│
├── fixtures/                      # Тестовые данные
│   ├── dmarket_responses.json
│   └── sample_items.json
│
└── conftest.py                   # Фикстуры pytest
```

---

## ⚙️ Настройка окружения

### Установка зависимостей

```bash
# Основные зависимости для тестирования
pip install pytest pytest-asyncio pytest-cov pytest-httpx

# Дополнительные инструменты
pip install freezegun faker
```

### Конфигурация pytest

**pyproject.toml**:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]

# Маркеры для категоризации тестов
markers = [
    "unit: Unit tests",
    "integration: Integration tests",
    "slow: Slow tests",
    "requires_api: Tests requiring API access",
]

# Покрытие кода
addopts = """
    -v
    --tb=short
    --strict-markers
    --cov=src
    --cov-report=term-missing
    --cov-report=html
"""
```

### Переменные окружения для тестов

**tests/.env.test**:

```env
# Тестовое окружение
ENVIRONMENT=test

# Отключить реальные API вызовы
DRY_RUN=true

# Тестовая база данных
DATABASE_URL=sqlite:///:memory:

# Моковые API ключи (не настоящие!)
DMARKET_PUBLIC_KEY=test_public_key
DMARKET_SECRET_KEY=test_secret_key
TELEGRAM_BOT_TOKEN=123456:ABC-DEF-test-token
```

---

## 🎭 Создание моков с pytest-httpx

### Базовые концепции

**pytest-httpx** позволяет мокировать HTTP запросы библиотеки `httpx`:

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_api_call(httpx_mock):
    """Базовый пример мока HTTP запроса."""

    # Настроить mock ответ
    httpx_mock.add_response(
        url="https://api.dmarket.com/account/v1/balance",
        json={"usd": "10000", "dmc": "5000"},
        status_code=200
    )

    # Выполнить запрос
    async with AsyncClient() as client:
        response = await client.get("https://api.dmarket.com/account/v1/balance")
        data = response.json()

    # Проверить результат
    assert data["usd"] == "10000"
    assert data["dmc"] == "5000"
```

### Мокирование DMarket API

#### Пример 1: Получение баланса

```python
import pytest
from src.dmarket.dmarket_api import DMarketAPI

@pytest.mark.asyncio
async def test_get_balance_success(httpx_mock):
    """Тест успешного получения баланса."""

    # Arrange: Настроить mock
    httpx_mock.add_response(
        method="GET",
        url="https://api.dmarket.com/account/v1/balance",
        json={
            "usd": "10000",
            "usdAvailableToWithdraw": "9500",
            "dmc": "5000",
            "dmcAvailableToWithdraw": "4500"
        },
        status_code=200
    )

    # Arrange: Создать API клиент
    api = DMarketAPI(
        public_key="test_public",
        secret_key="test_secret"
    )

    # Act: Выполнить запрос
    balance = await api.get_balance()

    # Assert: Проверить результат
    assert balance["usd"] == "10000"
    assert balance["dmc"] == "5000"
    assert balance["usdAvailableToWithdraw"] == "9500"
```

#### Пример 2: Получение предметов с рынка

```python
@pytest.mark.asyncio
async def test_get_market_items_success(httpx_mock):
    """Тест получения предметов с маркетплейса."""

    # Mock ответ от DMarket API
    httpx_mock.add_response(
        method="GET",
        url="https://api.dmarket.com/exchange/v1/market/items",
        json={
            "cursor": "next_page_cursor",
            "objects": [
                {
                    "itemId": "item_001",
                    "title": "AK-47 | Redline (Field-Tested)",
                    "price": {"USD": "1250"},
                    "suggestedPrice": {"USD": "1300"},
                    "extra": {
                        "category": "Rifle",
                        "exterior": "Field-Tested"
                    }
                },
                {
                    "itemId": "item_002",
                    "title": "AWP | Asiimov (Field-Tested)",
                    "price": {"USD": "4500"},
                    "suggestedPrice": {"USD": "4700"},
                    "extra": {
                        "category": "Sniper Rifle",
                        "exterior": "Field-Tested"
                    }
                }
            ],
            "total": 2
        },
        status_code=200
    )

    # Создать API клиент
    api = DMarketAPI("test_public", "test_secret")

    # Выполнить запрос
    result = await api.get_market_items(
        game_id="a8db",
        limit=100
    )

    # Проверки
    assert "objects" in result
    assert len(result["objects"]) == 2
    assert result["objects"][0]["title"] == "AK-47 | Redline (Field-Tested)"
    assert result["total"] == 2
```

### Мокирование множественных вызовов

**Важно**: pytest-httpx 0.35.0+ не поддерживает `can_reuse=True`.
Необходимо добавлять отдельный mock для каждого вызова:

```python
@pytest.mark.asyncio
async def test_multiple_api_calls(httpx_mock):
    """Тест множественных вызовов одного эндпоинта."""

    # Первый вызов
    httpx_mock.add_response(
        url="https://api.dmarket.com/account/v1/balance",
        json={"usd": "10000", "dmc": "5000"},
        status_code=200
    )

    # Второй вызов (тот же URL, но новый mock)
    httpx_mock.add_response(
        url="https://api.dmarket.com/account/v1/balance",
        json={"usd": "9500", "dmc": "5500"},  # Изменённый баланс
        status_code=200
    )

    api = DMarketAPI("test_public", "test_secret")

    # Первый запрос
    balance1 = await api.get_balance()
    assert balance1["usd"] == "10000"

    # Второй запрос (получит второй mock)
    balance2 = await api.get_balance()
    assert balance2["usd"] == "9500"
```

### Мокирование ошибок

#### Пример 1: Rate Limit (429)

```python
@pytest.mark.asyncio
async def test_rate_limit_handling(httpx_mock):
    """Тест обработки rate limit ошибки."""

    httpx_mock.add_response(
        url="https://api.dmarket.com/exchange/v1/market/items",
        status_code=429,
        headers={"Retry-After": "60"},
        json={
            "error": {
                "code": "RATE_LIMIT_EXCEEDED",
                "message": "Too many requests"
            }
        }
    )

    api = DMarketAPI("test_public", "test_secret")

    # Проверить что выбрасывается исключение
    with pytest.raises(Exception) as exc_info:
        await api.get_market_items(game_id="a8db")

    assert "rate limit" in str(exc_info.value).lower()
```

#### Пример 2: Сетевая ошибка

```python
import httpx

@pytest.mark.asyncio
async def test_network_error_handling(httpx_mock):
    """Тест обработки сетевой ошибки."""

    # Симулировать connection error
    httpx_mock.add_exception(
        httpx.ConnectError("Connection refused"),
        url="https://api.dmarket.com/account/v1/balance"
    )

    api = DMarketAPI("test_public", "test_secret")

    with pytest.raises(httpx.ConnectError):
        await api.get_balance()
```

#### Пример 3: Timeout

```python
@pytest.mark.asyncio
async def test_timeout_handling(httpx_mock):
    """Тест обработки таймаута."""

    httpx_mock.add_exception(
        httpx.TimeoutException("Request timeout"),
        url="https://api.dmarket.com/exchange/v1/market/items"
    )

    api = DMarketAPI("test_public", "test_secret")

    with pytest.raises(httpx.TimeoutException):
        await api.get_market_items(game_id="a8db")
```

---

## 📦 Примеры integration тестов

### Тест 1: Создание таргетов

```python
@pytest.mark.asyncio
async def test_create_targets_integration(httpx_mock):
    """Полный integration тест создания таргетов."""

    # Mock 1: Получение агрегированных цен
    httpx_mock.add_response(
        method="POST",
        url="https://api.dmarket.com/marketplace-api/v1/aggregated-prices",
        json={
            "aggregatedPrices": [
                {
                    "title": "AK-47 | Redline (Field-Tested)",
                    "orderBestPrice": "1200",
                    "offerBestPrice": "1250"
                }
            ]
        },
        status_code=200
    )

    # Mock 2: Создание таргета
    httpx_mock.add_response(
        method="POST",
        url="https://api.dmarket.com/marketplace-api/v1/user-targets/create",
        json={
            "Result": [
                {
                    "TargetID": "target_12345",
                    "Title": "AK-47 | Redline (Field-Tested)",
                    "Status": "Created"
                }
            ]
        },
        status_code=200
    )

    # Инициализация
    api = DMarketAPI("test_public", "test_secret")
    from src.dmarket.targets import TargetManager
    target_manager = TargetManager(api)

    # Создать таргет
    result = await target_manager.create_target(
        game="csgo",
        title="AK-47 | Redline (Field-Tested)",
        price=12.00,
        amount=1
    )

    # Проверки
    assert result["success"] is True
    assert "target_12345" in result["target_id"]
```

### Тест 2: Арбитражное сканирование

```python
@pytest.mark.asyncio
async def test_arbitrage_scan_integration(httpx_mock):
    """Integration тест полного цикла арбитражного сканирования."""

    # Mock: Получение предметов с маркета
    httpx_mock.add_response(
        url="https://api.dmarket.com/exchange/v1/market/items",
        json={
            "objects": [
                {
                    "itemId": "item_001",
                    "title": "AK-47 | Redline (FT)",
                    "price": {"USD": "1000"},
                    "suggestedPrice": {"USD": "1200"}
                },
                {
                    "itemId": "item_002",
                    "title": "AWP | Asiimov (FT)",
                    "price": {"USD": "4000"},
                    "suggestedPrice": {"USD": "4500"}
                }
            ],
            "total": 2
        },
        status_code=200
    )

    # Инициализация
    api = DMarketAPI("test_public", "test_secret")
    from src.dmarket.arbitrage_scanner import ArbitrageScanner
    scanner = ArbitrageScanner(api)

    # Выполнить сканирование
    opportunities = await scanner.scan_level(
        level="standard",
        game="csgo"
    )

    # Проверки
    assert len(opportunities) > 0
    for opp in opportunities:
        assert "item_name" in opp
        assert "buy_price" in opp
        assert "sell_price" in opp
        assert "profit_percent" in opp
        assert opp["profit_percent"] >= 3.0  # Минимум для standard
```

### Тест 3: Работа с базой данных

```python
import pytest
from src.models.user import User
from src.utils.database import DatabaseManager

@pytest.mark.asyncio
async def test_user_creation_integration():
    """Integration тест создания пользователя в БД."""

    # Использовать in-memory БД для тестов
    db = DatabaseManager("sqlite:///:memory:")
    await db.init_database()

    try:
        # Создать пользователя
        async with db.get_async_session() as session:
            user = User(
                telegram_id=123456789,
                username="test_user",
                first_name="Test",
                last_name="User"
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)

            user_id = user.id

        # Проверить что пользователь сохранён
        async with db.get_async_session() as session:
            from sqlalchemy import select
            stmt = select(User).where(User.telegram_id == 123456789)
            result = await session.execute(stmt)
            saved_user = result.scalar_one_or_none()

            assert saved_user is not None
            assert saved_user.username == "test_user"
            assert saved_user.telegram_id == 123456789

    finally:
        await db.close()
```

---

## 🔥 Тестирование edge cases

### Edge Case 1: Пустой ответ от API

```python
@pytest.mark.asyncio
async def test_empty_market_items_response(httpx_mock):
    """Тест корректной обработки пустого ответа."""

    httpx_mock.add_response(
        url="https://api.dmarket.com/exchange/v1/market/items",
        json={
            "objects": [],
            "total": 0,
            "cursor": None
        },
        status_code=200
    )

    api = DMarketAPI("test_public", "test_secret")
    result = await api.get_market_items(game_id="a8db")

    assert result["objects"] == []
    assert result["total"] == 0
```

### Edge Case 2: Некорректный JSON

```python
@pytest.mark.asyncio
async def test_malformed_json_response(httpx_mock):
    """Тест обработки некорректного JSON."""

    httpx_mock.add_response(
        url="https://api.dmarket.com/account/v1/balance",
        content=b"{invalid json",
        status_code=200
    )

    api = DMarketAPI("test_public", "test_secret")

    with pytest.raises(Exception):  # JSONDecodeError или custom exception
        await api.get_balance()
```

### Edge Case 3: Очень большие числа

```python
@pytest.mark.asyncio
async def test_large_numbers_handling(httpx_mock):
    """Тест обработки очень больших чисел."""

    httpx_mock.add_response(
        url="https://api.dmarket.com/account/v1/balance",
        json={
            "usd": "999999999999",  # Очень большой баланс
            "dmc": "999999999999"
        },
        status_code=200
    )

    api = DMarketAPI("test_public", "test_secret")
    balance = await api.get_balance()

    assert int(balance["usd"]) > 0
    assert len(balance["usd"]) == 12  # Проверка длины строки
```

### Edge Case 4: Concurrent requests

```python
import asyncio

@pytest.mark.asyncio
async def test_concurrent_requests(httpx_mock):
    """Тест параллельных запросов."""

    # Добавить 10 моков для параллельных запросов
    for i in range(10):
        httpx_mock.add_response(
            url="https://api.dmarket.com/account/v1/balance",
            json={"usd": f"{10000 + i}", "dmc": "5000"},
            status_code=200
        )

    api = DMarketAPI("test_public", "test_secret")

    # Запустить 10 параллельных запросов
    tasks = [api.get_balance() for _ in range(10)]
    results = await asyncio.gather(*tasks)

    # Проверить что все запросы выполнились
    assert len(results) == 10
    for result in results:
        assert "usd" in result
```

### Edge Case 5: Retry логика

```python
@pytest.mark.asyncio
async def test_retry_on_server_error(httpx_mock):
    """Тест retry логики при ошибке сервера."""

    # Первые 2 запроса - ошибка 500
    httpx_mock.add_response(
        url="https://api.dmarket.com/account/v1/balance",
        status_code=500,
        json={"error": "Internal Server Error"}
    )
    httpx_mock.add_response(
        url="https://api.dmarket.com/account/v1/balance",
        status_code=500,
        json={"error": "Internal Server Error"}
    )

    # Третий запрос - успех
    httpx_mock.add_response(
        url="https://api.dmarket.com/account/v1/balance",
        json={"usd": "10000", "dmc": "5000"},
        status_code=200
    )

    api = DMarketAPI("test_public", "test_secret", max_retries=3)

    # API должен повторить запрос и в итоге получить успех
    balance = await api.get_balance()
    assert balance["usd"] == "10000"
```

---

## ✅ Best Practices

### 1. Организация тестов

**✅ Правильно**: AAA паттерн (Arrange-Act-Assert)

```python
@pytest.mark.asyncio
async def test_example():
    # Arrange: Подготовка
    httpx_mock.add_response(...)
    api = DMarketAPI(...)

    # Act: Действие
    result = await api.some_method()

    # Assert: Проверка
    assert result["key"] == "value"
```

**❌ Неправильно**: Смешивание фаз

```python
async def test_example():
    api = DMarketAPI(...)
    assert api is not None  # Преждевременная проверка
    httpx_mock.add_response(...)  # Подготовка после создания
    result = await api.some_method()
```

### 2. Именование тестов

**✅ Правильно**: Описательные имена

```python
def test_get_balance_returns_correct_format_when_api_responds_successfully()
def test_create_target_raises_validation_error_when_price_is_negative()
def test_scan_arbitrage_returns_empty_list_when_no_opportunities_found()
```

**❌ Неправильно**: Неинформативные имена

```python
def test_balance()
def test_target()
def test_scan()
```

### 3. Фикстуры для переиспользования

```python
# conftest.py
import pytest
from src.dmarket.dmarket_api import DMarketAPI

@pytest.fixture
def dmarket_api():
    """Фикстура DMarket API клиента."""
    return DMarketAPI(
        public_key="test_public",
        secret_key="test_secret"
    )

@pytest.fixture
def sample_market_items():
    """Фикстура тестовых данных маркета."""
    return {
        "objects": [
            {
                "itemId": "item_001",
                "title": "AK-47 | Redline (FT)",
                "price": {"USD": "1250"}
            }
        ],
        "total": 1
    }

# Использование
@pytest.mark.asyncio
async def test_with_fixtures(httpx_mock, dmarket_api, sample_market_items):
    httpx_mock.add_response(
        url="https://api.dmarket.com/exchange/v1/market/items",
        json=sample_market_items,
        status_code=200
    )

    result = await dmarket_api.get_market_items(game_id="a8db")
    assert len(result["objects"]) == 1
```

### 4. Параметризация для множественных сценариев

```python
@pytest.mark.parametrize("status_code,expected_error", [
    (400, "Bad Request"),
    (401, "Unauthorized"),
    (403, "Forbidden"),
    (404, "Not Found"),
    (429, "Rate Limit"),
    (500, "Server Error"),
])
@pytest.mark.asyncio
async def test_api_error_handling(httpx_mock, status_code, expected_error):
    """Тест обработки различных HTTP ошибок."""

    httpx_mock.add_response(
        url="https://api.dmarket.com/account/v1/balance",
        status_code=status_code,
        json={"error": expected_error}
    )

    api = DMarketAPI("test_public", "test_secret")

    with pytest.raises(Exception) as exc_info:
        await api.get_balance()

    assert str(status_code) in str(exc_info.value)
```

### 5. Изоляция тестов

**✅ Правильно**: Каждый тест независим

```python
@pytest.mark.asyncio
async def test_one(httpx_mock):
    httpx_mock.add_response(...)
    # Тест 1

@pytest.mark.asyncio
async def test_two(httpx_mock):
    httpx_mock.add_response(...)
    # Тест 2 (не зависит от test_one)
```

**❌ Неправильно**: Тесты зависят друг от друга

```python
shared_state = {}

async def test_one():
    shared_state["key"] = "value"  # Изменяет глобальное состояние

async def test_two():
    assert shared_state["key"] == "value"  # Зависит от test_one
```

### 6. Использование реальных тестовых данных

Храните тестовые данные в отдельных файлах:

```python
# tests/fixtures/dmarket_responses.json
{
  "balance": {
    "usd": "10000",
    "dmc": "5000"
  },
  "market_items": {
    "objects": [...]
  }
}

# Загрузка в тестах
import json

@pytest.fixture
def dmarket_responses():
    with open("tests/fixtures/dmarket_responses.json") as f:
        return json.load(f)

@pytest.mark.asyncio
async def test_with_fixture_data(httpx_mock, dmarket_responses):
    httpx_mock.add_response(
        url="https://api.dmarket.com/account/v1/balance",
        json=dmarket_responses["balance"],
        status_code=200
    )
    # ...
```

---

## 🔧 Troubleshooting

### Проблема 1: Mock не срабатывает

**Симптомы**: Тест падает с ошибкой "No mock found"

**Решение**:

```python
# Проверьте точное совпадение URL
httpx_mock.add_response(
    url="https://api.dmarket.com/account/v1/balance",  # Точный URL
    # НЕ: url="https://api.dmarket.com/account/balance"  # Неправильно
    json={"usd": "10000"},
    status_code=200
)

# Проверьте метод HTTP
httpx_mock.add_response(
    method="GET",  # Явно указать метод
    url="...",
    json=...
)
```

### Проблема 2: Mock используется дважды

**Симптомы**: `RuntimeError: Mock already used`

**Решение**: Добавить отдельный mock для каждого вызова

```python
# ✅ Правильно (pytest-httpx 0.35.0+)
httpx_mock.add_response(url="...", json={"first": "call"})
httpx_mock.add_response(url="...", json={"second": "call"})

# ❌ Неправильно (старая версия)
httpx_mock.add_response(url="...", json=..., can_reuse=True)  # Не поддерживается
```

### Проблема 3: Асинхронные тесты не запускаются

**Симптомы**: `RuntimeWarning: coroutine was never awaited`

**Решение**: Добавить `@pytest.mark.asyncio`

```python
# ✅ Правильно
@pytest.mark.asyncio
async def test_async_function():
    result = await some_async_function()
    assert result is not None

# ❌ Неправильно
async def test_async_function():  # Отсутствует декоратор
    result = await some_async_function()
```

### Проблема 4: Тесты проходят локально, но падают в CI

**Причины**:

- Различия в версиях зависимостей
- Таймауты в CI среде
- Проблемы с временными зонами

**Решение**:

```python
# Использовать freezegun для контроля времени
from freezegun import freeze_time

@freeze_time("2025-11-24 12:00:00")
@pytest.mark.asyncio
async def test_with_fixed_time():
    # Время всегда одинаковое
    result = await time_sensitive_function()
    assert result is not None

# Увеличить таймауты для CI
import os

TIMEOUT = 30 if os.getenv("CI") else 10

async def test_with_timeout():
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        # ...
```

### Проблема 5: Слишком медленные тесты

**Решение**: Использовать pytest-xdist для параллельного выполнения

```bash
# Установка
pip install pytest-xdist

# Запуск в 4 процессах
pytest -n 4

# Автоматический выбор количества
pytest -n auto
```

---

## 📚 Дополнительные ресурсы

### Официальная документация

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [pytest-httpx](https://colin-b.github.io/pytest_httpx/)
- [pytest-cov](https://pytest-cov.readthedocs.io/)

### Примеры в проекте

- `tests/integration/test_api_with_httpx_mock.py` - Примеры DMarket API моков
- `tests/test_targets.py` - Примеры тестирования таргетов
- `tests/test_arbitrage_scanner.py` - Примеры арбитражного сканирования

### Полезные команды

```bash
# Запустить только integration тесты
pytest tests/integration/ -v

# Запустить с покрытием
pytest --cov=src --cov-report=html

# Запустить конкретный тест
pytest tests/integration/test_api_with_httpx_mock.py::test_get_balance_success -v

# Показать медленные тесты
pytest --durations=10

# Запустить в параллель
pytest -n auto

# Остановиться на первой ошибке
pytest -x

# Показать локальные переменные при ошибках
pytest -l
```

---

## ✅ Чеклист для integration тестов

Перед созданием нового integration теста проверьте:

- [ ] Тест использует `@pytest.mark.asyncio` для async функций
- [ ] Все HTTP запросы замокированы через `httpx_mock`
- [ ] URL моков точно совпадают с реальными
- [ ] Тест не зависит от других тестов
- [ ] Тест проверяет как success, так и error cases
- [ ] Используется AAA паттерн (Arrange-Act-Assert)
- [ ] Имя теста описательное и понятное
- [ ] Добавлен docstring с описанием теста
- [ ] Тест работает в изоляции (`pytest test_file.py::test_name`)
- [ ] Тест покрывает edge cases (пустые ответы, большие числа и т.д.)

---

**Версия руководства**: 1.0
**Последнее обновление**: 24 декабря 2025 г.
**Автор**: DMarket Bot Development Team

**Feedback**: Если у вас есть вопросы или предложения по улучшению этого руководства, создайте Issue на GitHub.
