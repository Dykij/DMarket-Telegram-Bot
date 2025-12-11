# 📋 План реализации: P2-17 - Dependency Injection и архитектурные улучшения

**Задача**: P2-17 из ROADMAP.md
**Приоритет**: 🟢 УЛУЧШЕНИЕ
**Оценка времени**: 15-20 часов
**Дата создания**: 11 декабря 2025 г.

---

## 📌 Обзор

Внедрение системы Dependency Injection (DI) с использованием библиотеки `dependency-injector` для улучшения тестируемости, модульности и поддерживаемости кодовой базы DMarket Telegram Bot.

### Текущее состояние

Сейчас зависимости передаются:
1. **Через `bot_data`** в `main.py`:
   ```python
   self.bot.bot_data["config"] = self.config
   self.bot.bot_data["dmarket_api"] = self.dmarket_api
   self.bot.bot_data["database"] = self.database
   ```

2. **Напрямую через конструкторы** в некоторых классах:
   ```python
   class ArbitrageScanner:
       def __init__(self, api_client: DMarketAPI | None = None):
           self.api_client = api_client
   ```

### Проблемы текущего подхода

- ❌ Сложно мокировать зависимости в тестах
- ❌ Неявные зависимости через `bot_data`
- ❌ Нет единого места для конфигурации зависимостей
- ❌ Сложно заменить реализации (например, для staging vs production)
- ❌ Циклические импорты возможны

### Ожидаемые улучшения

- ✅ Явная декларация зависимостей
- ✅ Простое мокирование в тестах
- ✅ Централизованная конфигурация
- ✅ Поддержка разных контекстов (prod/test/dev)
- ✅ Ленивая инициализация компонентов

---

## 📊 Анализ влияния

### Затронутые модули

| Файл | Изменения | Риск |
|------|-----------|------|
| `src/main.py` | Интеграция с DI container | Средний |
| `src/dmarket/dmarket_api.py` | Извлечение Protocol интерфейса | Низкий |
| `src/dmarket/arbitrage_scanner.py` | Использование DI | Низкий |
| `src/dmarket/targets.py` | Использование DI | Низкий |
| `src/utils/memory_cache.py` | Регистрация как singleton | Низкий |
| `src/utils/redis_cache.py` | Регистрация как singleton | Низкий |
| `src/telegram_bot/handlers/*` | Доступ к зависимостям через DI | Средний |
| `tests/conftest.py` | Тестовый контейнер | Низкий |

### Новые файлы для создания

| Файл | Назначение |
|------|------------|
| `src/containers.py` | Основной DI контейнер |
| `src/interfaces.py` | Protocol интерфейсы |
| `src/telegram_bot/dependencies.py` | Telegram-специфичные зависимости |
| `tests/conftest_di.py` | Тестовый DI контейнер |
| `docs/DEPENDENCY_INJECTION.md` | Документация по DI |

### Зависимости

```toml
# Добавить в requirements.in
dependency-injector>=4.41.0
```

### Риски

1. **Breaking changes** - обработчики Telegram могут сломаться при неправильной миграции
2. **Производительность** - DI container добавляет небольшой overhead
3. **Сложность** - команда должна понимать концепции DI

---

## 🎯 Требования

### Функциональные
- [ ] Создать централизованный DI container
- [ ] Извлечь Protocol интерфейсы для основных классов
- [ ] Обеспечить обратную совместимость с существующим кодом
- [ ] Поддержать lazy initialization
- [ ] Реализовать singleton scope для кэшей и API клиентов

### Нефункциональные
- [ ] Покрытие тестами новых компонентов >= 90%
- [ ] Документация с примерами использования
- [ ] Все существующие тесты должны проходить

---

## 🛠️ Шаги реализации

### Фаза 1: Базовый DI Container (⏱️ 3-4 часа)

#### Шаг 1.1: Добавить зависимость (15 мин)

**Файл**: `requirements.in`

```
# DI Framework
dependency-injector>=4.41.0
```

Выполнить:
```bash
pip-compile requirements.in -o requirements.txt
pip install -r requirements.txt
```

#### Шаг 1.2: Создать интерфейсы (1 час)

**Файл**: `src/interfaces.py`

```python
"""Protocol интерфейсы для Dependency Injection.

Этот модуль определяет абстрактные интерфейсы (Protocol) для основных
компонентов системы, что позволяет легко заменять реализации в тестах
и для разных окружений.
"""

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class IDMarketAPI(Protocol):
    """Protocol интерфейс для DMarket API клиента.

    Определяет минимальный набор методов, необходимых для работы
    с DMarket API. Позволяет создавать mock-реализации для тестов.
    """

    async def get_balance(self) -> dict[str, Any]:
        """Получить баланс аккаунта."""
        ...

    async def get_market_items(
        self,
        game: str,
        limit: int = 100,
        offset: int = 0,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Получить предметы с маркета."""
        ...

    async def buy_item(self, item_id: str, price: float) -> dict[str, Any]:
        """Купить предмет."""
        ...

    async def sell_item(
        self,
        asset_id: str,
        price: float,
    ) -> dict[str, Any]:
        """Выставить предмет на продажу."""
        ...

    async def create_targets(
        self,
        targets: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Создать таргеты (buy orders)."""
        ...

    async def get_user_targets(
        self,
        game_id: str | None = None,
    ) -> dict[str, Any]:
        """Получить активные таргеты пользователя."""
        ...


@runtime_checkable
class ICache(Protocol):
    """Protocol интерфейс для кэша.

    Абстрактный интерфейс для кэширования данных.
    Поддерживает как in-memory, так и распределенные кэши (Redis).
    """

    async def get(self, key: str) -> Any | None:
        """Получить значение из кэша."""
        ...

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
    ) -> None:
        """Сохранить значение в кэш."""
        ...

    async def delete(self, key: str) -> bool:
        """Удалить значение из кэша."""
        ...

    async def clear(self, pattern: str | None = None) -> int:
        """Очистить кэш (опционально по паттерну)."""
        ...


@runtime_checkable
class IArbitrageScanner(Protocol):
    """Protocol интерфейс для сканера арбитража."""

    async def scan_game(
        self,
        game: str,
        level: str,
        max_results: int = 10,
    ) -> list[dict[str, Any]]:
        """Сканировать игру на арбитражные возможности."""
        ...

    async def find_opportunities(
        self,
        games: list[str] | None = None,
        levels: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Найти арбитражные возможности."""
        ...


@runtime_checkable
class ITargetManager(Protocol):
    """Protocol интерфейс для менеджера таргетов."""

    async def create_target(
        self,
        game: str,
        title: str,
        price: float,
        amount: int = 1,
        attrs: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Создать таргет."""
        ...

    async def delete_targets(
        self,
        target_ids: list[str],
    ) -> dict[str, Any]:
        """Удалить таргеты."""
        ...

    async def get_active_targets(
        self,
        game: str | None = None,
    ) -> list[dict[str, Any]]:
        """Получить активные таргеты."""
        ...


@runtime_checkable
class IDatabase(Protocol):
    """Protocol интерфейс для базы данных."""

    async def init_database(self) -> None:
        """Инициализировать базу данных."""
        ...

    def get_async_session(self) -> Any:
        """Получить async session."""
        ...

    async def close(self) -> None:
        """Закрыть соединения с БД."""
        ...
```

#### Шаг 1.3: Создать DI Container (1.5 часа)

**Файл**: `src/containers.py`

```python
"""Dependency Injection контейнер для DMarket Telegram Bot.

Этот модуль предоставляет централизованную конфигурацию зависимостей
с использованием библиотеки dependency-injector.

Пример использования:

    # Инициализация контейнера
    container = Container()
    container.config.from_dict(settings_dict)

    # Получение зависимостей
    api = container.dmarket_api()
    scanner = container.arbitrage_scanner()

    # Переопределение для тестов
    container.dmarket_api.override(MockDMarketAPI())
"""

import logging
from typing import Any

from dependency_injector import containers, providers

from src.dmarket.arbitrage_scanner import ArbitrageScanner
from src.dmarket.dmarket_api import DMarketAPI
from src.dmarket.targets import TargetManager
from src.utils.config import Config
from src.utils.database import DatabaseManager
from src.utils.memory_cache import TTLCache
from src.utils.redis_cache import RedisCache


logger = logging.getLogger(__name__)


class CacheContainer(containers.DeclarativeContainer):
    """Контейнер для кэширования.

    Предоставляет in-memory и Redis кэши как singletons.
    """

    config = providers.Configuration()

    # In-memory TTL Cache (singleton)
    memory_cache = providers.Singleton(
        TTLCache,
        max_size=providers.Callable(
            lambda c: c.get("cache", {}).get("max_size", 1000),
            config,
        ),
        default_ttl=providers.Callable(
            lambda c: c.get("cache", {}).get("default_ttl", 300),
            config,
        ),
    )

    # Redis Cache (singleton, optional)
    redis_cache = providers.Singleton(
        RedisCache,
        redis_url=providers.Callable(
            lambda c: c.get("redis", {}).get("url"),
            config,
        ),
        default_ttl=providers.Callable(
            lambda c: c.get("redis", {}).get("default_ttl", 300),
            config,
        ),
        fallback_to_memory=True,
    )


class DatabaseContainer(containers.DeclarativeContainer):
    """Контейнер для базы данных."""

    config = providers.Configuration()

    # Database Manager (singleton)
    database = providers.Singleton(
        DatabaseManager,
        database_url=providers.Callable(
            lambda c: c.get("database", {}).get("url", "sqlite:///:memory:"),
            config,
        ),
        echo=providers.Callable(
            lambda c: c.get("debug", False),
            config,
        ),
    )


class DMarketContainer(containers.DeclarativeContainer):
    """Контейнер для DMarket API компонентов."""

    config = providers.Configuration()
    cache = providers.DependenciesContainer()

    # DMarket API Client (singleton)
    api = providers.Singleton(
        DMarketAPI,
        public_key=providers.Callable(
            lambda c: c.get("dmarket", {}).get("public_key", ""),
            config,
        ),
        secret_key=providers.Callable(
            lambda c: c.get("dmarket", {}).get("secret_key", ""),
            config,
        ),
        api_url=providers.Callable(
            lambda c: c.get("dmarket", {}).get("api_url", "https://api.dmarket.com"),
            config,
        ),
    )

    # Arbitrage Scanner (factory - new instance each call)
    arbitrage_scanner = providers.Factory(
        ArbitrageScanner,
        api_client=api,
        enable_liquidity_filter=True,
        enable_competition_filter=True,
    )

    # Target Manager (factory)
    target_manager = providers.Factory(
        TargetManager,
        api_client=api,
        enable_liquidity_filter=True,
    )


class Container(containers.DeclarativeContainer):
    """Главный DI контейнер приложения.

    Объединяет все подконтейнеры и предоставляет единую точку доступа
    к зависимостям приложения.

    Attributes:
        config: Конфигурация приложения
        caches: Подконтейнер для кэшей
        database: Подконтейнер для БД
        dmarket: Подконтейнер для DMarket компонентов

    Example:
        >>> container = Container()
        >>> container.config.from_dict({"dmarket": {"public_key": "xxx"}})
        >>> api = container.dmarket.api()
        >>> scanner = container.dmarket.arbitrage_scanner()
    """

    # Wiring configuration - modules that will use @inject
    wiring_config = containers.WiringConfiguration(
        modules=[
            "src.main",
            "src.telegram_bot.handlers.commands",
            "src.telegram_bot.handlers.callbacks",
            "src.telegram_bot.handlers.scanner_handler",
            "src.telegram_bot.handlers.target_handler",
        ],
    )

    # Configuration provider
    config = providers.Configuration()

    # Sub-containers
    caches = providers.Container(
        CacheContainer,
        config=config,
    )

    database = providers.Container(
        DatabaseContainer,
        config=config,
    )

    dmarket = providers.Container(
        DMarketContainer,
        config=config,
        cache=caches,
    )

    # Convenience aliases for common dependencies
    dmarket_api = providers.Callable(
        lambda dmarket: dmarket.api(),
        dmarket,
    )

    arbitrage_scanner = providers.Callable(
        lambda dmarket: dmarket.arbitrage_scanner(),
        dmarket,
    )

    target_manager = providers.Callable(
        lambda dmarket: dmarket.target_manager(),
        dmarket,
    )

    memory_cache = providers.Callable(
        lambda caches: caches.memory_cache(),
        caches,
    )


# Global container instance
_container: Container | None = None


def get_container() -> Container:
    """Получить глобальный экземпляр контейнера.

    Returns:
        Container: Настроенный DI контейнер

    Raises:
        RuntimeError: Если контейнер не инициализирован
    """
    global _container
    if _container is None:
        raise RuntimeError(
            "DI Container not initialized. Call init_container() first.",
        )
    return _container


def init_container(config: Config | dict[str, Any] | None = None) -> Container:
    """Инициализировать глобальный DI контейнер.

    Args:
        config: Конфигурация приложения (Config object или dict)

    Returns:
        Container: Инициализированный контейнер
    """
    global _container

    _container = Container()

    if config is not None:
        if isinstance(config, Config):
            # Convert Config to dict for dependency-injector
            config_dict = {
                "dmarket": {
                    "public_key": config.dmarket.public_key,
                    "secret_key": config.dmarket.secret_key,
                    "api_url": config.dmarket.api_url,
                },
                "database": {
                    "url": config.database.url,
                },
                "redis": {
                    "url": getattr(config, "redis_url", None),
                    "default_ttl": 300,
                },
                "cache": {
                    "max_size": 1000,
                    "default_ttl": 300,
                },
                "debug": config.debug,
                "testing": config.testing,
            }
            _container.config.from_dict(config_dict)
        else:
            _container.config.from_dict(config)

    logger.info("DI Container initialized successfully")
    return _container


def reset_container() -> None:
    """Сбросить глобальный контейнер (для тестов)."""
    global _container
    if _container is not None:
        _container.reset_singletons()
    _container = None
```

#### Шаг 1.4: Тесты для контейнера (1 час)

**Файл**: `tests/test_containers.py`

```python
"""Тесты для DI контейнера."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.containers import (
    Container,
    init_container,
    get_container,
    reset_container,
)
from src.interfaces import IDMarketAPI, ICache


@pytest.fixture(autouse=True)
def reset_di():
    """Сбросить контейнер перед каждым тестом."""
    reset_container()
    yield
    reset_container()


class TestContainerInitialization:
    """Тесты инициализации контейнера."""

    def test_init_container_creates_instance(self):
        """Тест создания контейнера."""
        config = {
            "dmarket": {
                "public_key": "test_key",
                "secret_key": "test_secret",
                "api_url": "https://api.dmarket.com",
            },
            "database": {"url": "sqlite:///:memory:"},
            "debug": True,
        }

        container = init_container(config)

        assert container is not None
        assert get_container() is container

    def test_get_container_raises_if_not_initialized(self):
        """Тест ошибки при получении неинициализированного контейнера."""
        with pytest.raises(RuntimeError, match="not initialized"):
            get_container()

    def test_reset_container_clears_state(self):
        """Тест сброса контейнера."""
        init_container({"dmarket": {"public_key": "test"}})
        reset_container()

        with pytest.raises(RuntimeError):
            get_container()


class TestDMarketProviders:
    """Тесты провайдеров DMarket."""

    @pytest.fixture
    def container(self):
        """Создать контейнер с тестовой конфигурацией."""
        return init_container({
            "dmarket": {
                "public_key": "test_public",
                "secret_key": "test_secret",
                "api_url": "https://api.dmarket.com",
            },
            "database": {"url": "sqlite:///:memory:"},
        })

    def test_dmarket_api_is_singleton(self, container):
        """Тест что DMarketAPI создается как singleton."""
        api1 = container.dmarket.api()
        api2 = container.dmarket.api()

        assert api1 is api2

    def test_arbitrage_scanner_is_factory(self, container):
        """Тест что ArbitrageScanner создается как factory."""
        scanner1 = container.dmarket.arbitrage_scanner()
        scanner2 = container.dmarket.arbitrage_scanner()

        # Factory создает новые экземпляры
        assert scanner1 is not scanner2

    def test_arbitrage_scanner_uses_same_api(self, container):
        """Тест что сканеры используют один API клиент."""
        scanner1 = container.dmarket.arbitrage_scanner()
        scanner2 = container.dmarket.arbitrage_scanner()

        assert scanner1.api_client is scanner2.api_client


class TestContainerOverrides:
    """Тесты переопределения зависимостей."""

    def test_override_dmarket_api(self):
        """Тест переопределения DMarket API для тестов."""
        container = init_container({
            "dmarket": {"public_key": "test"},
        })

        # Создать mock API
        mock_api = AsyncMock()
        mock_api.get_balance = AsyncMock(return_value={"balance": 100.0})

        # Переопределить
        container.dmarket.api.override(mock_api)

        # Проверить что используется mock
        api = container.dmarket.api()
        assert api is mock_api

        # Сбросить переопределение
        container.dmarket.api.reset_override()

    def test_override_propagates_to_dependents(self):
        """Тест что переопределение влияет на зависимые компоненты."""
        container = init_container({
            "dmarket": {"public_key": "test"},
        })

        mock_api = AsyncMock()
        container.dmarket.api.override(mock_api)

        # Сканер должен использовать mock API
        scanner = container.dmarket.arbitrage_scanner()
        assert scanner.api_client is mock_api
```

---

### Фаза 2: Рефакторинг DMarketAPI (⏱️ 4-6 часов)

#### Шаг 2.1: Обновить DMarketAPI для соответствия Protocol (1 час)

**Файл**: `src/dmarket/dmarket_api.py` - добавить в начало класса:

```python
from src.interfaces import IDMarketAPI

class DMarketAPI(IDMarketAPI):
    """Асинхронный клиент для работы с DMarket API.

    Реализует Protocol IDMarketAPI для поддержки Dependency Injection.
    """
    # ... существующий код без изменений ...
```

#### Шаг 2.2: Обновить ArbitrageScanner (2 часа)

**Файл**: `src/dmarket/arbitrage_scanner.py`

```python
from src.interfaces import IDMarketAPI

class ArbitrageScanner:
    """Класс для сканирования арбитражных возможностей."""

    def __init__(
        self,
        api_client: IDMarketAPI | None = None,  # Используем Protocol
        enable_liquidity_filter: bool = True,
        enable_competition_filter: bool = True,
        max_competition: int = 3,
    ) -> None:
        """Инициализирует сканер арбитража.

        Args:
            api_client: DMarket API клиент (Protocol IDMarketAPI)
            enable_liquidity_filter: Включить фильтрацию по ликвидности
            enable_competition_filter: Включить фильтрацию по конкуренции
            max_competition: Максимально допустимое количество конкурентов
        """
        self.api_client = api_client
        # ... остальной код без изменений ...
```

#### Шаг 2.3: Обновить TargetManager (1 час)

**Файл**: `src/dmarket/targets.py`

```python
from src.interfaces import IDMarketAPI

class TargetManager:
    """Менеджер для работы с таргетами."""

    def __init__(
        self,
        api_client: IDMarketAPI,  # Используем Protocol
        enable_liquidity_filter: bool = True,
    ) -> None:
        """Инициализация менеджера таргетов.

        Args:
            api_client: DMarket API клиент (Protocol IDMarketAPI)
            enable_liquidity_filter: Включить фильтрацию по ликвидности
        """
        self.api = api_client
        # ... остальной код без изменений ...
```

#### Шаг 2.4: Тесты с использованием Protocol (1 час)

**Файл**: `tests/test_di_integration.py`

```python
"""Интеграционные тесты DI с Protocol интерфейсами."""

import pytest
from unittest.mock import AsyncMock

from src.interfaces import IDMarketAPI
from src.dmarket.arbitrage_scanner import ArbitrageScanner
from src.dmarket.targets import TargetManager


class MockDMarketAPI:
    """Mock реализация IDMarketAPI для тестов."""

    def __init__(self):
        self.get_balance = AsyncMock(return_value={"balance": 100.0})
        self.get_market_items = AsyncMock(return_value={"objects": []})
        self.buy_item = AsyncMock(return_value={"success": True})
        self.sell_item = AsyncMock(return_value={"success": True})
        self.create_targets = AsyncMock(return_value={"success": True})
        self.get_user_targets = AsyncMock(return_value={"targets": []})


class TestProtocolCompliance:
    """Тесты соответствия Protocol интерфейсам."""

    def test_mock_api_implements_protocol(self):
        """Тест что mock реализует Protocol."""
        mock = MockDMarketAPI()
        assert isinstance(mock, IDMarketAPI)

    def test_arbitrage_scanner_accepts_protocol(self):
        """Тест что ArbitrageScanner принимает Protocol."""
        mock = MockDMarketAPI()
        scanner = ArbitrageScanner(api_client=mock)

        assert scanner.api_client is mock

    def test_target_manager_accepts_protocol(self):
        """Тест что TargetManager принимает Protocol."""
        mock = MockDMarketAPI()
        manager = TargetManager(api_client=mock)

        assert manager.api is mock


class TestMockedScanner:
    """Тесты сканера с мокированным API."""

    @pytest.fixture
    def mock_api(self):
        """Создать mock API."""
        mock = MockDMarketAPI()
        mock.get_market_items.return_value = {
            "objects": [
                {
                    "itemId": "item1",
                    "title": "Test Item",
                    "price": {"USD": "1000"},
                    "suggestedPrice": {"USD": "1200"},
                },
            ],
        }
        return mock

    @pytest.mark.asyncio
    async def test_scan_uses_mock_api(self, mock_api):
        """Тест что сканер использует mock API."""
        scanner = ArbitrageScanner(api_client=mock_api)

        # Вызов scan_game должен использовать mock
        # (реальная реализация зависит от текущего кода)
        mock_api.get_market_items.assert_not_called()  # Пока не вызывали

        # При вызове метода сканирования
        # await scanner.scan_game("csgo", "standard", 10)
        # mock_api.get_market_items.assert_called()
```

---

### Фаза 3: Рефакторинг Telegram Bot (⏱️ 4-6 часов)

#### Шаг 3.1: Создать telegram-специфичные зависимости (1.5 часа)

**Файл**: `src/telegram_bot/dependencies.py`

```python
"""Telegram Bot зависимости и интеграция с DI контейнером.

Этот модуль предоставляет удобные функции для доступа к зависимостям
из Telegram handlers через bot_data и DI контейнер.
"""

import logging
from typing import Any, TypeVar

from telegram.ext import ContextTypes

from src.containers import get_container, Container
from src.interfaces import IDMarketAPI, IArbitrageScanner, ITargetManager


logger = logging.getLogger(__name__)

T = TypeVar("T")


def get_from_context(
    context: ContextTypes.DEFAULT_TYPE,
    key: str,
    default: T | None = None,
) -> T | None:
    """Безопасно получить значение из bot_data.

    Args:
        context: Telegram контекст
        key: Ключ для поиска
        default: Значение по умолчанию

    Returns:
        Значение из bot_data или default
    """
    if context.bot_data is None:
        return default
    return context.bot_data.get(key, default)


def get_dmarket_api(context: ContextTypes.DEFAULT_TYPE) -> IDMarketAPI | None:
    """Получить DMarket API клиент.

    Пробует получить из bot_data (legacy) или из DI контейнера.

    Args:
        context: Telegram контекст

    Returns:
        DMarket API клиент или None
    """
    # Сначала проверяем legacy bot_data
    api = get_from_context(context, "dmarket_api")
    if api is not None:
        return api

    # Затем пробуем DI контейнер
    try:
        container = get_container()
        return container.dmarket_api()
    except RuntimeError:
        logger.warning("DI container not initialized, dmarket_api unavailable")
        return None


def get_arbitrage_scanner(
    context: ContextTypes.DEFAULT_TYPE,
) -> IArbitrageScanner | None:
    """Получить ArbitrageScanner.

    Args:
        context: Telegram контекст

    Returns:
        ArbitrageScanner или None
    """
    try:
        container = get_container()
        return container.arbitrage_scanner()
    except RuntimeError:
        # Fallback: создать scanner с API из bot_data
        api = get_dmarket_api(context)
        if api is not None:
            from src.dmarket.arbitrage_scanner import ArbitrageScanner
            return ArbitrageScanner(api_client=api)
        return None


def get_target_manager(
    context: ContextTypes.DEFAULT_TYPE,
) -> ITargetManager | None:
    """Получить TargetManager.

    Args:
        context: Telegram контекст

    Returns:
        TargetManager или None
    """
    try:
        container = get_container()
        return container.target_manager()
    except RuntimeError:
        # Fallback: создать manager с API из bot_data
        api = get_dmarket_api(context)
        if api is not None:
            from src.dmarket.targets import TargetManager
            return TargetManager(api_client=api)
        return None


def get_config(context: ContextTypes.DEFAULT_TYPE) -> Any | None:
    """Получить конфигурацию.

    Args:
        context: Telegram контекст

    Returns:
        Config или None
    """
    return get_from_context(context, "config")


def get_database(context: ContextTypes.DEFAULT_TYPE) -> Any | None:
    """Получить DatabaseManager.

    Args:
        context: Telegram контекст

    Returns:
        DatabaseManager или None
    """
    db = get_from_context(context, "database")
    if db is not None:
        return db

    try:
        container = get_container()
        return container.database.database()
    except RuntimeError:
        return None


# Декоратор для handlers с DI (опционально)
def inject_dependencies(handler_func):
    """Декоратор для автоматической инъекции зависимостей в handler.

    Пример использования:
        @inject_dependencies
        async def my_handler(update, context, *, dmarket_api=None, scanner=None):
            # dmarket_api и scanner будут автоматически инжектированы
            pass
    """
    import functools
    import inspect

    @functools.wraps(handler_func)
    async def wrapper(update, context, *args, **kwargs):
        # Получить параметры функции
        sig = inspect.signature(handler_func)

        for param_name, param in sig.parameters.items():
            if param_name in ("update", "context"):
                continue

            # Инжектировать зависимости по имени
            if param_name == "dmarket_api" and param_name not in kwargs:
                kwargs["dmarket_api"] = get_dmarket_api(context)
            elif param_name == "scanner" and param_name not in kwargs:
                kwargs["scanner"] = get_arbitrage_scanner(context)
            elif param_name == "target_manager" and param_name not in kwargs:
                kwargs["target_manager"] = get_target_manager(context)
            elif param_name == "config" and param_name not in kwargs:
                kwargs["config"] = get_config(context)
            elif param_name == "database" and param_name not in kwargs:
                kwargs["database"] = get_database(context)

        return await handler_func(update, context, *args, **kwargs)

    return wrapper
```

#### Шаг 3.2: Обновить main.py (2 часа)

**Файл**: `src/main.py` - добавить интеграцию с DI

```python
# Добавить импорты в начало файла
from src.containers import init_container, get_container, reset_container

# В методе Application.initialize(), после загрузки конфигурации:

async def initialize(self) -> None:
    """Initialize all application components."""
    try:
        # Load configuration
        logger.info("Loading configuration...")
        self.config = Config.load(self.config_path)
        self.config.validate()

        # Initialize DI Container
        logger.info("Initializing DI Container...")
        self.container = init_container(self.config)
        logger.info("DI Container initialized")

        # ... существующий код setup_logging, Sentry и т.д. ...

        # Initialize DMarket API через DI
        logger.info("Initializing DMarket API...")
        self.dmarket_api = self.container.dmarket_api()  # Через DI

        # ... остальной код без изменений ...

        # Store dependencies in bot_data (для обратной совместимости)
        self.bot.bot_data["config"] = self.config
        self.bot.bot_data["dmarket_api"] = self.dmarket_api
        self.bot.bot_data["database"] = self.database
        self.bot.bot_data["state_manager"] = self.state_manager
        self.bot.bot_data["container"] = self.container  # Добавить контейнер

# В методе shutdown():
async def shutdown(self) -> None:
    """Gracefully shutdown the application."""
    # ... существующий код ...

    # Reset DI container
    reset_container()
    logger.info("DI Container reset")
```

#### Шаг 3.3: Пример обновления handler (1 час)

**Файл**: Пример для `src/telegram_bot/handlers/scanner_handler.py`

```python
# Добавить импорт
from src.telegram_bot.dependencies import (
    get_arbitrage_scanner,
    get_dmarket_api,
    inject_dependencies,
)

# Вариант 1: Явное получение зависимостей
async def handle_scan_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Обработчик команды сканирования."""
    scanner = get_arbitrage_scanner(context)
    if scanner is None:
        await update.message.reply_text("❌ Scanner unavailable")
        return

    # Использовать scanner...
    results = await scanner.scan_game("csgo", "standard", 10)

# Вариант 2: Использование декоратора (опционально)
@inject_dependencies
async def handle_scan_with_di(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    *,
    scanner: IArbitrageScanner | None = None,
) -> None:
    """Обработчик с автоматической инъекцией."""
    if scanner is None:
        await update.message.reply_text("❌ Scanner unavailable")
        return

    results = await scanner.scan_game("csgo", "standard", 10)
```

#### Шаг 3.4: Тесты для Telegram зависимостей (1.5 часа)

**Файл**: `tests/telegram_bot/test_dependencies.py`

```python
"""Тесты для Telegram Bot зависимостей."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.telegram_bot.dependencies import (
    get_dmarket_api,
    get_arbitrage_scanner,
    get_target_manager,
    get_from_context,
    inject_dependencies,
)
from src.containers import init_container, reset_container


@pytest.fixture(autouse=True)
def reset_di():
    """Сбросить DI перед каждым тестом."""
    reset_container()
    yield
    reset_container()


@pytest.fixture
def mock_context():
    """Создать mock Telegram контекст."""
    context = MagicMock()
    context.bot_data = {}
    return context


class TestGetFromContext:
    """Тесты для get_from_context."""

    def test_returns_value_if_exists(self, mock_context):
        """Тест возврата значения из bot_data."""
        mock_context.bot_data["test_key"] = "test_value"
        result = get_from_context(mock_context, "test_key")
        assert result == "test_value"

    def test_returns_default_if_missing(self, mock_context):
        """Тест возврата default при отсутствии ключа."""
        result = get_from_context(mock_context, "missing", default="default")
        assert result == "default"

    def test_returns_none_if_bot_data_none(self):
        """Тест при bot_data = None."""
        context = MagicMock()
        context.bot_data = None
        result = get_from_context(context, "key")
        assert result is None


class TestGetDMarketApi:
    """Тесты для get_dmarket_api."""

    def test_returns_from_bot_data_if_exists(self, mock_context):
        """Тест получения API из bot_data (legacy)."""
        mock_api = MagicMock()
        mock_context.bot_data["dmarket_api"] = mock_api

        result = get_dmarket_api(mock_context)

        assert result is mock_api

    def test_returns_from_container_if_bot_data_empty(self, mock_context):
        """Тест получения API из DI контейнера."""
        init_container({
            "dmarket": {
                "public_key": "test",
                "secret_key": "test",
            },
        })

        result = get_dmarket_api(mock_context)

        assert result is not None

    def test_returns_none_if_not_available(self, mock_context):
        """Тест возврата None при недоступности API."""
        result = get_dmarket_api(mock_context)
        assert result is None


class TestInjectDependencies:
    """Тесты для декоратора inject_dependencies."""

    @pytest.mark.asyncio
    async def test_injects_dmarket_api(self, mock_context):
        """Тест инъекции dmarket_api."""
        mock_api = MagicMock()
        mock_context.bot_data["dmarket_api"] = mock_api

        @inject_dependencies
        async def handler(update, context, *, dmarket_api=None):
            return dmarket_api

        update = MagicMock()
        result = await handler(update, mock_context)

        assert result is mock_api
```

---

### Фаза 4: Обновление тестов (⏱️ 3-4 часа)

#### Шаг 4.1: Создать тестовый DI контейнер (1.5 часа)

**Файл**: `tests/conftest_di.py`

```python
"""Тестовый DI контейнер и фикстуры.

Этот модуль предоставляет специализированные фикстуры для тестирования
с использованием Dependency Injection.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.containers import Container, init_container, reset_container


@pytest.fixture
def di_config():
    """Конфигурация для тестового DI контейнера."""
    return {
        "dmarket": {
            "public_key": "test_public_key",
            "secret_key": "test_secret_key",
            "api_url": "https://api.dmarket.com",
        },
        "database": {
            "url": "sqlite:///:memory:",
        },
        "redis": {
            "url": None,  # Без Redis в тестах
            "default_ttl": 60,
        },
        "cache": {
            "max_size": 100,
            "default_ttl": 60,
        },
        "debug": True,
        "testing": True,
    }


@pytest.fixture
def test_container(di_config):
    """Создать тестовый DI контейнер.

    Автоматически сбрасывается после теста.
    """
    container = init_container(di_config)
    yield container
    reset_container()


@pytest.fixture
def mock_dmarket_api():
    """Mock DMarket API для тестов.

    Предоставляет полностью мокированный API клиент
    с предустановленными return values.
    """
    mock = AsyncMock()

    # Balance
    mock.get_balance.return_value = {
        "balance": 100.0,
        "usd": {"amount": 10000},
        "error": False,
    }

    # Market items
    mock.get_market_items.return_value = {
        "objects": [
            {
                "itemId": "test_item_1",
                "title": "AK-47 | Redline (Field-Tested)",
                "price": {"USD": "1250"},
                "suggestedPrice": {"USD": "1500"},
                "gameId": "csgo",
            },
        ],
        "cursor": None,
    }

    # Buy/Sell
    mock.buy_item.return_value = {"success": True, "orderId": "order_123"}
    mock.sell_item.return_value = {"success": True, "offerId": "offer_123"}

    # Targets
    mock.create_targets.return_value = {
        "success": True,
        "targets": [{"targetId": "target_1"}],
    }
    mock.get_user_targets.return_value = {
        "targets": [],
        "total": 0,
    }

    return mock


@pytest.fixture
def container_with_mock_api(test_container, mock_dmarket_api):
    """Тестовый контейнер с мокированным API.

    Использовать когда нужен полный контейнер, но с mock API.
    """
    test_container.dmarket.api.override(mock_dmarket_api)
    yield test_container
    test_container.dmarket.api.reset_override()


@pytest.fixture
def mock_scanner(mock_dmarket_api):
    """Mock ArbitrageScanner для тестов."""
    from src.dmarket.arbitrage_scanner import ArbitrageScanner

    scanner = ArbitrageScanner(api_client=mock_dmarket_api)
    return scanner


@pytest.fixture
def mock_target_manager(mock_dmarket_api):
    """Mock TargetManager для тестов."""
    from src.dmarket.targets import TargetManager

    manager = TargetManager(api_client=mock_dmarket_api)
    return manager
```

#### Шаг 4.2: Обновить conftest.py (1 час)

**Файл**: `tests/conftest.py` - добавить импорт DI фикстур

```python
# Добавить в начало файла
from tests.conftest_di import *  # noqa: F401, F403

# Или явно импортировать нужные фикстуры:
from tests.conftest_di import (
    di_config,
    test_container,
    mock_dmarket_api,
    container_with_mock_api,
    mock_scanner,
    mock_target_manager,
)
```

#### Шаг 4.3: Пример обновления существующего теста (1 час)

**Файл**: `tests/dmarket/test_arbitrage_scanner_di.py`

```python
"""Тесты ArbitrageScanner с использованием DI."""

import pytest

from src.dmarket.arbitrage_scanner import ArbitrageScanner


class TestArbitrageScannerWithDI:
    """Тесты сканера с DI мокированием."""

    @pytest.mark.asyncio
    async def test_scan_game_uses_api(self, mock_dmarket_api):
        """Тест что scan_game использует API."""
        scanner = ArbitrageScanner(api_client=mock_dmarket_api)

        # Настроить mock response
        mock_dmarket_api.get_market_items.return_value = {
            "objects": [
                {
                    "itemId": "item1",
                    "title": "Test Item",
                    "price": {"USD": "1000"},
                    "suggestedPrice": {"USD": "1200"},
                },
            ],
        }

        # Вызвать метод (если существует)
        # results = await scanner.scan_game("csgo", "standard", 10)

        # Проверить вызов API
        # mock_dmarket_api.get_market_items.assert_called()

    @pytest.mark.asyncio
    async def test_scanner_from_container(self, container_with_mock_api):
        """Тест получения сканера из контейнера."""
        scanner = container_with_mock_api.dmarket.arbitrage_scanner()

        assert scanner is not None
        assert scanner.api_client is not None
```

---

### Фаза 5: Документация (⏱️ 1-2 часа)

#### Шаг 5.1: Создать DEPENDENCY_INJECTION.md (1 час)

**Файл**: `docs/DEPENDENCY_INJECTION.md`

```markdown
# 🔧 Dependency Injection в DMarket Bot

## Обзор

DMarket Telegram Bot использует Dependency Injection (DI) для управления
зависимостями между компонентами. Это обеспечивает:

- **Тестируемость**: Легкое мокирование зависимостей
- **Модульность**: Слабое связывание компонентов
- **Гибкость**: Простая замена реализаций

## Архитектура

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

### Protocol интерфейсы

Все основные классы реализуют Protocol интерфейсы (`src/interfaces.py`):

- `IDMarketAPI` - API клиент
- `ICache` - Кэширование
- `IArbitrageScanner` - Сканер арбитража
- `ITargetManager` - Менеджер таргетов

## Использование

### Инициализация контейнера

```python
from src.containers import init_container, get_container

# При старте приложения
config = Config.load()
container = init_container(config)

# Получение зависимостей
api = container.dmarket_api()
scanner = container.arbitrage_scanner()
```

### В Telegram handlers

```python
from src.telegram_bot.dependencies import get_dmarket_api, get_arbitrage_scanner

async def handle_scan(update, context):
    scanner = get_arbitrage_scanner(context)
    if scanner is None:
        return

    results = await scanner.scan_game("csgo", "standard")
```

### В тестах

```python
@pytest.fixture
def mock_api():
    mock = AsyncMock()
    mock.get_balance.return_value = {"balance": 100.0}
    return mock

def test_scanner(mock_api):
    scanner = ArbitrageScanner(api_client=mock_api)
    # scanner использует mock API
```

### Переопределение для тестов

```python
def test_with_override(test_container):
    mock = AsyncMock()
    test_container.dmarket.api.override(mock)

    api = test_container.dmarket_api()
    assert api is mock

    test_container.dmarket.api.reset_override()
```

## Scopes

| Компонент | Scope | Описание |
|-----------|-------|----------|
| DMarketAPI | Singleton | Один экземпляр на приложение |
| TTLCache | Singleton | Общий кэш |
| RedisCache | Singleton | Распределенный кэш |
| ArbitrageScanner | Factory | Новый экземпляр при каждом запросе |
| TargetManager | Factory | Новый экземпляр при каждом запросе |

## Best Practices

1. **Используйте Protocol интерфейсы** для зависимостей
2. **Не обращайтесь к контейнеру напрямую** из бизнес-логики
3. **Переопределяйте зависимости** в тестах через `override()`
4. **Сбрасывайте контейнер** после тестов через `reset_container()`
```

#### Шаг 5.2: Обновить ARCHITECTURE.md (30 мин)

Добавить секцию о DI в `docs/ARCHITECTURE.md`:

```markdown
### 4. Dependency Injection

Проект использует библиотеку `dependency-injector` для управления зависимостями:

```python
from src.containers import get_container

container = get_container()
api = container.dmarket_api()
scanner = container.arbitrage_scanner()
```

Подробнее см. [DEPENDENCY_INJECTION.md](./DEPENDENCY_INJECTION.md).
```

---

## 🧪 Тестирование

### Новые тесты

| Файл | Количество тестов | Покрытие |
|------|-------------------|----------|
| `tests/test_containers.py` | ~10 | Container, providers |
| `tests/test_di_integration.py` | ~8 | Protocol compliance |
| `tests/telegram_bot/test_dependencies.py` | ~8 | Telegram DI helpers |
| `tests/conftest_di.py` | - | Фикстуры |

### Команды для запуска

```bash
# Запустить только DI тесты
pytest tests/test_containers.py tests/test_di_integration.py -v

# Запустить все тесты с coverage
pytest --cov=src --cov-report=html

# Проверить типы
mypy src/containers.py src/interfaces.py
```

---

## ✅ Критерии завершения

### Обязательные

- [ ] `dependency-injector` добавлен в requirements
- [ ] `src/containers.py` создан и работает
- [ ] `src/interfaces.py` содержит Protocol для основных классов
- [ ] `src/telegram_bot/dependencies.py` предоставляет helper функции
- [ ] `src/main.py` инициализирует DI контейнер
- [ ] Все существующие тесты проходят (2688+)
- [ ] Новые тесты для DI имеют покрытие >= 90%
- [ ] MyPy проверка проходит без новых ошибок
- [ ] Ruff проверка проходит

### Рекомендуемые

- [ ] `docs/DEPENDENCY_INJECTION.md` создан
- [ ] `docs/ARCHITECTURE.md` обновлен
- [ ] Минимум 2 handler'а обновлены для использования DI

---

## 📊 Метрики успеха

| Метрика | До | После |
|---------|-----|-------|
| Тесты | 2688 | 2700+ |
| Покрытие DI модулей | - | >= 90% |
| MyPy ошибки в DI | - | 0 |
| Время инициализации | baseline | +< 5% |

---

## 🔄 План миграции

### Этап 1: Добавить DI (не ломая существующий код)
- Создать контейнер и интерфейсы
- Добавить helper функции
- Сохранить обратную совместимость через `bot_data`

### Этап 2: Постепенная миграция handlers
- Обновлять по одному handler за раз
- Каждый PR содержит тесты

### Этап 3: Удаление legacy кода (после стабилизации)
- Убрать дублирование в `bot_data`
- Полностью перейти на DI

---

**Версия плана**: 1.0
**Автор**: GitHub Copilot
**Дата**: 11 декабря 2025 г.
