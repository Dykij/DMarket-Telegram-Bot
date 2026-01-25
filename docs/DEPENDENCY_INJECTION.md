# 🔧 Dependency Injection в DMarket Bot

**Версия**: 1.0.0
**Дата**: 28 декабря 2025 г.

---

## 📋 Обзор

DMarket Telegram Bot использует Dependency Injection (DI) для управления
зависимостями между компонентами. Это обеспечивает:

- **Тестируемость**: Легкое мокирование зависимостей
- **Модульность**: Слабое связывание компонентов
- **Гибкость**: Простая замена реализаций
- **Прозрачность**: Явная декларация зависимостей

## 🏗️ Архитектура

### Основные компоненты

```
┌─────────────────────────────────────────────────────────┐
│                     Container                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │   Caches    │  │  Database   │  │   DMarket   │     │
│  │ - memory    │  │ - manager   │  │ - api       │     │
│  │ - redis     │  │             │  │ - scanner   │     │
│  │             │  │             │  │ - targets   │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
└─────────────────────────────────────────────────────────┘
```

### Файловая структура

```
src/
├── containers.py          # Главный DI контейнер
├── interfaces.py          # Protocol интерфейсы
└── telegram_bot/
    └── dependencies.py    # Helper функции для handlers

tests/
├── conftest_di.py        # DI фикстуры для тестов
├── test_containers.py    # Тесты контейнера
└── telegram_bot/
    └── test_dependencies.py  # Тесты helper функций
```

### Protocol интерфейсы

Все основные классы реализуют Protocol интерфейсы (`src/interfaces.py`):

| Protocol | Описание |
|----------|----------|
| `IDMarketAPI` | API клиент DMarket |
| `ICache` | Кэширование (memory/Redis) |
| `IArbitrageScanner` | Сканер арбитража |
| `ITargetManager` | Менеджер таргетов |
| `IDatabase` | Менеджер базы данных |

## 🚀 Использование

### Инициализация контейнера

```python
from src.containers import init_container, get_container

# При старте приложения
config = Config.load()
container = init_container(config)

# Или с dict конфигурацией
container = init_container({
    "dmarket": {
        "public_key": "your_key",
        "secret_key": "your_secret",
    },
    "database": {"url": "postgresql://..."},
})
```

### Получение зависимостей из контейнера

```python
from src.containers import get_container

container = get_container()

# DMarket API (singleton)
api = container.dmarket_api()

# ArbitrageScanner (factory - новый экземпляр)
scanner = container.arbitrage_scanner()

# TargetManager (factory)
target_manager = container.target_manager()

# Memory cache (singleton)
cache = container.memory_cache()

# Database (singleton)
database = container.database()
```

### В Telegram handlers

```python
from src.telegram_bot.dependencies import (
    get_dmarket_api,
    get_arbitrage_scanner,
    get_target_manager,
)

async def handle_scan(update, context):
    scanner = get_arbitrage_scanner(context)
    if scanner is None:
        await update.message.reply_text("❌ Scanner unavailable")
        return

    results = await scanner.scan_game("csgo", "standard")
```

### Использование декоратора @inject_dependencies

```python
from src.telegram_bot.dependencies import inject_dependencies

@inject_dependencies
async def handle_balance(
    update,
    context,
    *,
    dmarket_api=None,  # Автоматически инжектируется
):
    if dmarket_api is None:
        return

    balance = await dmarket_api.get_balance()
    await update.message.reply_text(f"Balance: ${balance['balance']:.2f}")
```

## 🧪 Тестирование

### Базовое мокирование

```python
import pytest
from unittest.mock import AsyncMock

@pytest.fixture
def mock_api():
    mock = AsyncMock()
    mock.get_balance.return_value = {"balance": 100.0}
    return mock

def test_scanner(mock_api):
    from src.dmarket.arbitrage_scanner import ArbitrageScanner
    
    scanner = ArbitrageScanner(api_client=mock_api)
    # scanner использует mock API
```

### Переопределение в контейнере

```python
from src.containers import init_container, reset_container

@pytest.fixture
def test_container():
    container = init_container({"dmarket": {"public_key": "test"}})
    yield container
    reset_container()

def test_with_mock(test_container, mock_api):
    # Переопределить API
    test_container.dmarket_api.override(mock_api)
    
    # Получить сканер - он будет использовать mock
    scanner = test_container.arbitrage_scanner()
    assert scanner.api_client is mock_api
    
    # Сбросить после теста
    test_container.dmarket_api.reset_override()
```

### Использование готовых фикстур

```python
# tests/conftest_di.py предоставляет готовые фикстуры:

def test_with_fixtures(
    test_container,           # Контейнер с тестовой конфигурацией
    mock_dmarket_api,         # Полностью настроенный mock API
    container_with_mock_api,  # Контейнер с mock API
    mock_scanner,             # Scanner с mock API
    mock_target_manager,      # TargetManager с mock API
):
    # Все зависимости готовы к использованию
    pass
```

## ⚙️ Scopes

| Компонент | Scope | Описание |
|-----------|-------|----------|
| `DMarketAPI` | Singleton | Один экземпляр на всё приложение |
| `TTLCache` | Singleton | Общий in-memory кэш |
| `RedisCache` | Singleton | Распределенный кэш |
| `DatabaseManager` | Singleton | Менеджер БД |
| `ArbitrageScanner` | Factory | Новый экземпляр при каждом запросе |
| `TargetManager` | Factory | Новый экземпляр при каждом запросе |

### Почему такие scope?

- **Singleton для API**: Один HTTP клиент с connection pool
- **Singleton для кэшей**: Shared state между запросами
- **Factory для Scanner/TargetManager**: Изолированное состояние для каждой операции

## 🔄 Обратная совместимость

DI система сохраняет обратную совместимость с legacy кодом:

1. **bot_data проверяется первым**:
   ```python
   def get_dmarket_api(context):
       # Сначала legacy bot_data
       api = context.bot_data.get("dmarket_api")
       if api is not None:
           return api
       
       # Затем DI контейнер
       return get_container().dmarket.api()
   ```

2. **Fallback создание компонентов**:
   ```python
   def get_arbitrage_scanner(context):
       try:
           return get_container().dmarket.arbitrage_scanner()
       except RuntimeError:
           # Создать с API из bot_data
           api = get_dmarket_api(context)
           return ArbitrageScanner(api_client=api)
   ```

## 📚 Best Practices

### ✅ DO

1. **Используйте Protocol интерфейсы** для зависимостей:
   ```python
   def process(api: IDMarketAPI) -> None:
       ...
   ```

2. **Получайте зависимости через helpers** в handlers:
   ```python
   api = get_dmarket_api(context)
   ```

3. **Переопределяйте в тестах** через `override()`:
   ```python
   container.dmarket.api.override(mock)
   ```

4. **Сбрасывайте после тестов**:
   ```python
   reset_container()
   ```

### ❌ DON'T

1. **Не импортируйте контейнер напрямую** в бизнес-логике:
   ```python
   # ❌ Плохо
   from src.containers import get_container
   api = get_container().dmarket.api()
   
   # ✅ Хорошо - передать как аргумент
   def process(api: IDMarketAPI):
       ...
   ```

2. **Не создавайте экземпляры вручную** когда есть DI:
   ```python
   # ❌ Плохо
   api = DMarketAPI(public_key, secret_key)
   
   # ✅ Хорошо
   api = get_dmarket_api(context)
   ```

3. **Не забывайте reset_override()** после тестов

## 🔧 Конфигурация

### Структура конфигурации

```python
config = {
    "dmarket": {
        "public_key": "xxx",
        "secret_key": "yyy",
        "api_url": "https://api.dmarket.com",
    },
    "database": {
        "url": "postgresql://...",
    },
    "redis": {
        "url": "redis://localhost:6379/0",
        "default_ttl": 300,
    },
    "cache": {
        "max_size": 1000,
        "default_ttl": 300,
    },
    "debug": False,
    "testing": False,
}
```

### Переменные окружения

```bash
# .env
DMARKET_PUBLIC_KEY=xxx
DMARKET_SECRET_KEY=yyy
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
```

## 📖 Ссылки

- [dependency-injector docs](https://python-dependency-injector.ets-labs.org/)
- [Python typing.Protocol](https://docs.python.org/3/library/typing.html#typing.Protocol)
- [План реализации](./DEPENDENCY_INJECTION_PLAN.md)
