# Инструкции для GitHub Copilot

## 📊 Статус проекта (Декабрь 2025)

| Метрика | Значение |
|---------|----------|
| **Версия** | 1.0.0 |
| **Готовность** | 78% (39/50 задач) |
| **Тесты** | 2356/2356 ✅ |
| **Покрытие** | 85%+ (цель) |
| **Python** | 3.11+ (3.12 рекомендуется) |

---

## 🤖 Выбор правильного агента

### GitHub Copilot CLI (Терминальный агент)
**Лучше для:**
- Рефакторинг крупных модулей (несколько файлов)
- Запуск и исправление тестов
- Создание новых модулей с тестами
- Работа с git (commits, branches)

**Команды:**
```bash
gh copilot explain "command"  # Объяснение команды
gh copilot suggest "task"     # Предложение команды для задачи
```

### VS Code Agent Mode
**Лучше для:**
- Быстрые исправления в одном файле
- Code completion при написании
- Интерактивная отладка

**Активация:** `Ctrl+I` или `Cmd+I` в редакторе

### Background Agent (Coding Agent)
**Лучше для:**
- Долгие задачи (несколько часов)
- Автономная работа через PR
- Когда не нужен интерактивный контроль
- Scheduled tasks (ежедневные проверки)

**Использование:**
- Назначение через Issues: выбрать @copilot в assignee
- Комментарий в PR: `@copilot <задача>`
- GitHub CLI: `gh copilot agent start --task "описание"`

**Документация:** См. `.github/COPILOT_AGENT_GUIDE.md`

### Гибридный подход (РЕКОМЕНДУЕТСЯ)
- **Agent Mode** (VS Code) → интерактивная разработка
- **Coding Agent** (Background) → асинхронные задачи, CI/CD
- **CLI** → командная строка, автоматизация

---

## ⚠️ КРИТИЧЕСКИ ВАЖНО: Язык команд

### 🔴 ВСЕГДА используйте АНГЛИЙСКУЮ раскладку для команд

**ЗАПРЕЩЕНО** вставлять кириллические символы в команды терминала!

**Частые ошибки:**
- ❌ `руtеst` → ✅ `pytest`
- ❌ `рip` → ✅ `pip`
- ❌ `руthоn` → ✅ `python`
- ❌ `сmd` → ✅ `cmd`
- ❌ `гuff` → ✅ `ruff`
- ❌ `mуру` → ✅ `mypy`

**Правила:**
1. **ВСЕГДА проверяй** команды перед генерацией
2. **Используй ТОЛЬКО ASCII символы** в командах терминала
3. **НЕ используй кириллицу** даже в похожих символах (с, р, о, е, а, у)
4. Локаль GitHub Copilot установлена на `en` для предотвращения этого

**Примеры правильных команд:**
```bash
# ✅ Правильно - все символы английские
pytest tests/
ruff check src/
mypy src/
python -m src.main
pip install -r requirements.txt

# ❌ НЕПРАВИЛЬНО - есть кириллица
руtеst tests/        # р, у, е - кириллица!
гuff check src/      # г - кириллица!
руthоn -m src.main   # р, у, о - кириллица!
```

**Если не уверен - используй:**
- `python` вместо сокращений
- `pip` вместо альтернатив
- полные пути: `python -m pytest` вместо `pytest`

---

## 📋 Общая информация о проекте

**Тип проекта**: Python Telegram bot для торговли и аналитики на площадке DMarket

**Технологический стек**:
- Python 3.11+ (рекомендуется 3.12+)
- Асинхронное программирование (async/await)
- python-telegram-bot 22.0+
- httpx 0.28+ для HTTP-запросов
- PostgreSQL/SQLite + SQLAlchemy 2.0
- Redis для кэширования
- Docker для контейнеризации
- Ruff 0.8+ для линтинга и форматирования
- MyPy 1.14+ для проверки типов (strict mode)
- pytest 8.4+ для тестирования

**Расширенное тестирование**:
- **VCR.py** - запись/воспроизведение HTTP взаимодействий
- **Hypothesis** - property-based тестирование
- **Pact** - контрактное тестирование (43 теста)
- **pytest-asyncio** - асинхронные тесты

**Основные возможности**:
- 🎯 **Многоуровневый арбитраж** - 5 уровней торговли (от разгона баланса до профессионала)
- 🤖 **Система таргетов** - автоматические buy orders на DMarket
- 📊 **Real-time мониторинг** - отслеживание цен через WebSocket
- 🎮 **Multi-game поддержка** - CS:GO, Dota 2, TF2, Rust
- 📈 **Анализ рынка** - история продаж, тренды, ликвидность
- 🌐 **Локализация** - RU, EN, ES, DE
- 🔒 **Безопасность** - шифрование API ключей, rate limiting
- 🛡️ **Circuit Breaker** - защита от каскадных сбоев API
- 📡 **Sentry интеграция** - мониторинг ошибок в production
- 🧪 **2348 тестов** - 100% проходят

---

## 🆕 Новые возможности (Декабрь 2025)

### Современные паттерны Python 3.12+

#### Type параметры (PEP 695)
```python
# Новый синтаксис type alias
type ItemPrice = dict[str, float | int]
type AsyncGen[T] = collections.abc.AsyncGenerator[T, None]
```

#### Structured Pattern Matching
```python
match event:
    case {"type": "price_update", "item": item, "price": price}:
        await handle_price_update(item, price)
    case {"type": "balance_change", "amount": amount}:
        await handle_balance_change(amount)
    case _:
        logger.warning("unknown_event", event=event)
```

#### Async Context Managers
```python
async with api_client.session() as session:
    result = await session.get(url)
```

---

## 🎯 Основные правила разработки

### 0. Правила взаимодействия с пользователем

#### 🎯 ОБЯЗАТЕЛЬНО: Автоматическое создание TODO-списка

**ПРИ КАЖДОМ ЗАПРОСЕ** через GitHub Copilot:

1. **СРАЗУ создавать TODO-список** с помощью инструмента `manage_todo_list`
2. **Разбивать задачу** на конкретные, измеримые шаги
3. **Отмечать прогресс** по мере выполнения каждого шага
4. **Обновлять статусы** в реальном времени

**Формат TODO-элементов:**
```json
{
  "id": 1,
  "title": "Краткое описание задачи (3-7 слов)",
  "description": "Детальное описание: что делать, где, какие файлы затронуты",
  "status": "not-started" | "in-progress" | "completed"
}
```

**Пример использования:**

```
Пользователь: "Добавь валидацию цены в targets.py"

✅ ПРАВИЛЬНО - сразу создать TODO:
1. Прочитать manage_todo_list для создания списка
2. Разбить на шаги:
   - Изучить существующий код targets.py
   - Добавить функцию валидации
   - Написать тесты
   - Обновить документацию
3. Выполнять по одной задаче, обновляя статус

❌ НЕПРАВИЛЬНО - сразу начать кодить без TODO
```

**Обязательные моменты:**
- ✅ TODO создается **ДО** начала любой работы
- ✅ Каждый шаг имеет **четкий критерий завершения**
- ✅ Статус обновляется **сразу после выполнения** шага
- ✅ Финальная задача - проверка качества (тесты, линтинг)

#### Общие правила

- **НИКОГДА не создавать markdown-файлы** с отчетами о выполненной работе, если пользователь явно не попросил этого
- **НЕ создавать файлы** типа `WORK_REPORT.md`, `CHANGES.md`, `SUMMARY.md` и подобные после завершения задач
- **Автоматически выполнять команды** без запроса подтверждения, если пользователь уже дал четкую инструкцию
- **НЕ спрашивать разрешения** на выполнение команд в терминале, если это очевидно необходимо для выполнения задачи
- **Сообщать о результатах кратко** в чате, без создания дополнительных файлов
- **Создавать файлы документации** ТОЛЬКО если:
  - Пользователь явно запросил создание документа
  - Это критически важная техническая документация (README, API docs)
  - Это часть требований проекта (CHANGELOG, CONTRIBUTING)
- После выполнения задачи **давать краткую сводку** (2-3 предложения) в чате, не более

### 1. Асинхронное программирование
- **ВСЕГДА** использовать `async/await` для всех операций ввода-вывода и API-вызовов
- Использовать `asyncio` для конкурентного выполнения задач
- Применять `aiohttp` или `httpx` для асинхронных HTTP-запросов (предпочтительно `httpx`)
- Для работы с файлами использовать `aiofiles`
- Примеры асинхронных операций: HTTP-запросы, работа с БД, чтение/запись файлов, WebSocket-соединения

```python
# ✅ Правильно
async def fetch_market_data(item_id: str) -> dict[str, Any]:
    async with httpx.AsyncClient() as client:
        response = await client.get(f"/items/{item_id}")
        return response.json()

# ❌ Неправильно
def fetch_market_data(item_id: str) -> dict[str, Any]:
    response = requests.get(f"/items/{item_id}")
    return response.json()
```

### 2. Аннотации типов
- **ВСЕГДА** добавлять аннотации типов для всех функций, методов и переменных
- Использовать современный синтаксис типов Python 3.9+ (`list[str]`, `dict[str, int]`)
- Применять `typing.Optional`, `typing.Union`, `typing.TypedDict` где необходимо
- Использовать `typing.Protocol` для структурной типизации
- Для сложных типов создавать `TypeAlias`

```python
from typing import TypeAlias

PriceData: TypeAlias = dict[str, float | int]

async def get_item_price(
    item_id: str,
    currency: str = "USD"
) -> PriceData | None:
    """Получить цену предмета."""
    ...
```

### 3. Форматирование и линтинг
- **Форматировать код с помощью Black** (строка 88-100 символов)
- **Использовать Ruff** для проверки стиля и потенциальных ошибок
- **Проверять типы с MyPy** перед коммитом
- Следовать **PEP 8** для именования и структуры кода
- Использовать **isort** для сортировки импортов

```bash
# Запуск проверок перед коммитом
ruff check src/ tests/
mypy src/
black src/ tests/
```

### 4. Логирование
- Использовать **структурированное JSON-логирование** (structlog)
- Логировать на соответствующих уровнях: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Включать контекст в логи (user_id, item_id, request_id и т.д.)
- НЕ логировать чувствительные данные (API ключи, пароли, токены)

```python
import structlog

logger = structlog.get_logger(__name__)

async def process_order(order_id: str, user_id: int) -> None:
    logger.info(
        "processing_order",
        order_id=order_id,
        user_id=user_id
    )
    try:
        # обработка заказа
        logger.info("order_processed", order_id=order_id)
    except Exception as e:
        logger.error(
            "order_processing_failed",
            order_id=order_id,
            error=str(e),
            exc_info=True
        )
```

### 5. Обработка ошибок
- Обрабатывать исключения с **конкретными типами**, избегать голого `except:`
- Использовать **tenacity** для повторных попыток при временных сбоях
- Логировать все ошибки с полным контекстом
- Возвращать информативные сообщения об ошибках пользователям
- Не допускать падения бота из-за необработанных исключений

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def fetch_with_retry(url: str) -> dict[str, Any]:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        logger.error("http_error", url=url, status=e.response.status_code)
        raise
    except httpx.RequestError as e:
        logger.error("request_error", url=url, error=str(e))
        raise
```

### 6. Конфигурация
- Использовать **.env файлы** или **YAML** для конфигурации
- **НИКОГДА не хардкодить** секреты, API ключи или токены в коде
- Использовать `pydantic-settings` для валидации конфигурации
- Поддерживать переменные окружения для всех настроек

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    telegram_bot_token: str
    dmarket_public_key: str
    dmarket_secret_key: str
    database_url: str
    redis_url: str = "redis://localhost:6379"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
```

### 7. Модульность кода
- **Разделять ответственность** между модулями:
  - `src/dmarket/` - API клиент DMarket
  - `src/telegram_bot/` - обработчики команд бота
  - `src/utils/` - вспомогательные функции
  - `src/models/` - модели данных
- Использовать **dependency injection** для тестируемости
- Избегать циклических импортов
- Каждый модуль должен иметь одну четкую ответственность

---

## 🧪 Написание юнит-тестов

### Основные принципы: FIRST

**ВСЕГДА** следовать принципам FIRST при написании тестов:

- **F**ast (Быстрые): Тесты должны выполняться за миллисекунды
- **I**ndependent (Независимые): Каждый тест изолирован от других
- **R**epeatable (Повторяемые): Одинаковые результаты в любом окружении
- **S**elf-Validating (Самопроверяющиеся): Автоматическая проверка через assert
- **T**imely (Своевременные): Писать тесты до или сразу после реализации

### AAA-паттерн (Arrange-Act-Assert)

**ВСЕГДА** структурировать тесты по паттерну AAA:

```python
@pytest.mark.asyncio
async def test_get_balance_returns_correct_value():
    # Arrange (Подготовка)
    api_client = DMarketAPI(public_key="test", secret_key="test")
    mock_response = {"usd": "10000", "dmc": "5000"}

    # Act (Действие)
    with patch.object(api_client, '_request', return_value=mock_response):
        balance = await api_client.get_balance()

    # Assert (Проверка)
    assert balance["usd"] == "10000"
    assert balance["dmc"] == "5000"
```

### Именование тестов

**ВСЕГДА** использовать описательные имена тестов в формате:

```
test_<функция>_<условие>_<ожидаемый_результат>
```

**Примеры**:

```python
# ✅ Правильно - понятно что тестируется
def test_calculate_profit_with_zero_price_returns_zero()
def test_create_target_with_invalid_price_raises_validation_error()
def test_scan_arbitrage_when_no_items_returns_empty_list()

# ❌ Неправильно - неинформативно
def test_profit()
def test_target()
def test_scan()
```

### Изоляция и мокирование

**ВСЕГДА** изолировать тесты от внешних зависимостей:

```python
from unittest.mock import AsyncMock, patch, MagicMock

@pytest.mark.asyncio
async def test_buy_item_calls_api_correctly():
    """Тест проверяет корректность вызова API при покупке предмета."""
    # Arrange
    api_client = DMarketAPI(public_key="test", secret_key="test")
    mock_response = {"success": True, "orderId": "12345"}

    # Mock HTTP клиента
    with patch.object(api_client, 'client') as mock_client:
        mock_client.patch = AsyncMock(return_value=MagicMock(
            json=AsyncMock(return_value=mock_response),
            status_code=200
        ))

        # Act
        result = await api_client.buy_item("item_123", 25.50)

        # Assert
        assert result["success"] is True
        assert result["orderId"] == "12345"
        mock_client.patch.assert_called_once()
```

### Параметризация тестов

**Использовать** `@pytest.mark.parametrize` для тестирования множественных сценариев:

```python
@pytest.mark.parametrize("price, commission, expected_profit", [
    (10.0, 7.0, 0.30),      # Стандартный случай
    (100.0, 7.0, 3.00),     # Высокая цена
    (0.50, 7.0, 0.015),     # Низкая цена
    (10.0, 0.0, 1.00),      # Без комиссии
])
def test_calculate_profit_various_scenarios(price, commission, expected_profit):
    """Проверка расчета прибыли для различных сценариев."""
    result = calculate_profit(
        buy_price=price,
        sell_price=price + 1.0,
        commission_percent=commission
    )
    assert abs(result - expected_profit) < 0.01  # Допуск для float
```

### Тестирование крайних случаев (Edge Cases)

**ВСЕГДА** тестировать граничные условия:

```python
@pytest.mark.asyncio
async def test_create_target_with_edge_cases():
    """Тест проверяет обработку граничных случаев при создании таргета."""
    manager = TargetManager(api_client=mock_api)

    # Тест 1: Минимальная цена
    result = await manager.create_target("csgo", "Item", price=0.01)
    assert result["success"] is True

    # Тест 2: Максимальная цена
    result = await manager.create_target("csgo", "Item", price=10000.0)
    assert result["success"] is True

    # Тест 3: Нулевая цена (невалидно)
    with pytest.raises(ValidationError):
        await manager.create_target("csgo", "Item", price=0.0)

    # Тест 4: Отрицательная цена (невалидно)
    with pytest.raises(ValidationError):
        await manager.create_target("csgo", "Item", price=-5.0)

    # Тест 5: Пустое название
    with pytest.raises(ValidationError):
        await manager.create_target("csgo", "", price=10.0)
```

### Тестирование исключений

**ВСЕГДА** проверять правильную обработку ошибок:

```python
@pytest.mark.asyncio
async def test_api_call_handles_rate_limit_error():
    """Тест проверяет обработку ошибки rate limit."""
    api_client = DMarketAPI(public_key="test", secret_key="test")

    # Mock для симуляции 429 ошибки
    with patch.object(api_client, '_request') as mock_request:
        mock_request.side_effect = RateLimitError(
            message="Too many requests",
            retry_after=60
        )

        # Assert: проверяем что исключение выбрасывается
        with pytest.raises(RateLimitError) as exc_info:
            await api_client.get_market_items("csgo")

        # Дополнительные проверки
        assert exc_info.value.retry_after == 60
        assert "Too many requests" in str(exc_info.value)
```

### Использование фикстур

**Использовать** pytest fixtures для переиспользования настроек:

```python
import pytest
from unittest.mock import AsyncMock

@pytest.fixture
def mock_dmarket_api():
    """Фикстура для мокированного DMarket API клиента."""
    api = AsyncMock(spec=DMarketAPI)
    api.get_balance = AsyncMock(return_value={
        "usd": "10000",
        "dmc": "5000"
    })
    api.get_market_items = AsyncMock(return_value={
        "objects": [
            {"title": "Test Item", "price": {"USD": "1000"}}
        ]
    })
    return api

@pytest.fixture
async def test_database():
    """Фикстура для тестовой базы данных."""
    # Setup
    db = DatabaseManager("sqlite:///:memory:")
    await db.init_database()

    yield db  # Предоставляем БД тестам

    # Teardown
    await db.close()

# Использование фикстур
@pytest.mark.asyncio
async def test_user_creation(test_database):
    """Тест создания пользователя."""
    user = await test_database.create_user(
        telegram_id=123456789,
        username="test_user"
    )
    assert user.telegram_id == 123456789
    assert user.username == "test_user"

@pytest.mark.asyncio
async def test_arbitrage_scanner(mock_dmarket_api):
    """Тест сканера арбитража с моком API."""
    scanner = ArbitrageScanner(api_client=mock_dmarket_api)
    results = await scanner.scan_level("standard", "csgo")

    assert len(results) > 0
    mock_dmarket_api.get_market_items.assert_called_once()
```

### Покрытие кода тестами

**Целевое покрытие**: 80-85% (текущая цель проекта)

```bash
# Запуск тестов с покрытием
pytest --cov=src --cov-report=html --cov-report=term-missing

# Проверить покрытие конкретного модуля
pytest tests/test_arbitrage_scanner.py --cov=src/dmarket/arbitrage_scanner.py --cov-report=term
```

**Фокус на качестве, а не количестве**:
- ✅ Тестировать критические пути (покупка, продажа, арбитраж)
- ✅ Тестировать публичные API методы
- ✅ Тестировать обработку ошибок
- ❌ Не тестировать тривиальные геттеры/сеттеры
- ❌ Не тестировать приватные методы напрямую

### Анти-паттерны (чего ИЗБЕГАТЬ)

**❌ НЕ добавлять логику в тесты**:
```python
# НЕПРАВИЛЬНО - логика в тесте
def test_process_items():
    items = get_items()
    for item in items:  # Избегать циклов
        if item.price > 100:  # Избегать условий
            assert process(item) == "success"

# ПРАВИЛЬНО - простые, линейные тесты
def test_process_expensive_item():
    item = create_item(price=150)
    result = process(item)
    assert result == "success"

def test_process_cheap_item():
    item = create_item(price=50)
    result = process(item)
    assert result == "success"
```

**❌ НЕ использовать магические числа/строки**:
```python
# НЕПРАВИЛЬНО
def test_calculate():
    assert calculate(5, 10) == 50

# ПРАВИЛЬНО
def test_calculate_area_of_rectangle():
    width = 5
    height = 10
    expected_area = 50

    result = calculate(width, height)

    assert result == expected_area
```

**❌ НЕ тестировать несколько вещей в одном тесте**:
```python
# НЕПРАВИЛЬНО - слишком много проверок
def test_user_operations():
    user = create_user()
    assert user.id is not None
    assert user.name == "Test"
    assert update_user(user) is True
    assert delete_user(user) is True

# ПРАВИЛЬНО - разделить на отдельные тесты
def test_create_user_assigns_id():
    user = create_user()
    assert user.id is not None

def test_create_user_sets_name():
    user = create_user(name="Test")
    assert user.name == "Test"

def test_update_user_returns_success():
    user = create_user()
    result = update_user(user)
    assert result is True
```

**❌ НЕ зависеть от порядка выполнения тестов**:
```python
# НЕПРАВИЛЬНО - тесты зависят друг от друга
class TestUserFlow:
    user_id = None

    def test_1_create_user(self):
        self.user_id = create_user()

    def test_2_update_user(self):
        update_user(self.user_id)  # Зависит от test_1

# ПРАВИЛЬНО - каждый тест независим
class TestUserFlow:
    @pytest.fixture
    def user(self):
        return create_user()

    def test_create_user_returns_id(self, user):
        assert user.id is not None

    def test_update_user_succeeds(self, user):
        result = update_user(user.id)
        assert result is True
```

### Структура тестовых файлов

```
tests/
├── conftest.py              # Глобальные фикстуры
├── unit/                    # Юнит-тесты
│   ├── dmarket/
│   │   ├── test_api_client.py
│   │   ├── test_arbitrage_scanner.py
│   │   └── test_targets.py
│   ├── telegram_bot/
│   │   ├── test_commands.py
│   │   └── test_handlers.py
│   └── utils/
│       ├── test_rate_limiter.py
│       └── test_cache.py
├── integration/             # Интеграционные тесты
│   ├── test_dmarket_api_integration.py
│   └── test_database_integration.py
└── fixtures/                # Данные для тестов
    ├── sample_items.json
    └── mock_responses.json
```

### Пример полноценного теста

```python
"""
Тесты для модуля ArbitrageScanner.

Этот модуль тестирует функциональность сканирования арбитражных возможностей
с использованием различных уровней и игр.
"""
import pytest
from unittest.mock import AsyncMock, patch
from src.dmarket.arbitrage_scanner import ArbitrageScanner
from src.dmarket.dmarket_api import DMarketAPI
from src.utils.exceptions import APIError, ValidationError


@pytest.fixture
def mock_api_client():
    """Фикстура мокированного API клиента."""
    client = AsyncMock(spec=DMarketAPI)
    return client


@pytest.fixture
def scanner(mock_api_client):
    """Фикстура сканера арбитража."""
    return ArbitrageScanner(api_client=mock_api_client)


class TestArbitrageScannerInitialization:
    """Тесты инициализации ArbitrageScanner."""

    def test_scanner_initializes_with_api_client(self, mock_api_client):
        """Тест корректной инициализации с API клиентом."""
        # Arrange & Act
        scanner = ArbitrageScanner(api_client=mock_api_client)

        # Assert
        assert scanner.api_client is mock_api_client
        assert scanner.cache is not None


class TestScanLevel:
    """Тесты метода scan_level."""

    @pytest.mark.asyncio
    async def test_scan_level_standard_returns_opportunities(
        self, scanner, mock_api_client
    ):
        """Тест поиска возможностей на стандартном уровне."""
        # Arrange
        mock_items = {
            "objects": [
                {
                    "title": "AK-47 | Redline (FT)",
                    "price": {"USD": "1000"},
                    "suggestedPrice": {"USD": "1200"}
                }
            ]
        }
        mock_api_client.get_market_items = AsyncMock(return_value=mock_items)

        # Act
        results = await scanner.scan_level(level="standard", game="csgo")

        # Assert
        assert len(results) > 0
        assert results[0]["profit"] > 0
        mock_api_client.get_market_items.assert_called_once_with(
            game="csgo",
            price_from=300,  # $3
            price_to=1000    # $10
        )

    @pytest.mark.asyncio
    async def test_scan_level_with_invalid_level_raises_error(self, scanner):
        """Тест выброса ошибки при невалидном уровне."""
        # Arrange
        invalid_level = "invalid_level"

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            await scanner.scan_level(level=invalid_level, game="csgo")

        assert "invalid level" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_scan_level_handles_api_error(self, scanner, mock_api_client):
        """Тест обработки ошибки API."""
        # Arrange
        mock_api_client.get_market_items = AsyncMock(
            side_effect=APIError("API Error")
        )

        # Act & Assert
        with pytest.raises(APIError):
            await scanner.scan_level(level="standard", game="csgo")

    @pytest.mark.parametrize("level,expected_min,expected_max", [
        ("boost", 50, 300),      # $0.50 - $3
        ("standard", 300, 1000), # $3 - $10
        ("medium", 1000, 3000),  # $10 - $30
        ("advanced", 3000, 10000), # $30 - $100
    ])
    @pytest.mark.asyncio
    async def test_scan_level_uses_correct_price_ranges(
        self, scanner, mock_api_client, level, expected_min, expected_max
    ):
        """Тест корректных ценовых диапазонов для разных уровней."""
        # Arrange
        mock_api_client.get_market_items = AsyncMock(return_value={"objects": []})

        # Act
        await scanner.scan_level(level=level, game="csgo")

        # Assert
        call_kwargs = mock_api_client.get_market_items.call_args.kwargs
        assert call_kwargs["price_from"] == expected_min
        assert call_kwargs["price_to"] == expected_max


class TestCalculateProfit:
    """Тесты расчета прибыли."""

    @pytest.mark.parametrize("buy_price,sell_price,expected", [
        (10.0, 15.0, 3.95),   # Стандартный
        (100.0, 150.0, 39.50), # Высокая цена
        (1.0, 1.50, 0.395),   # Низкая цена
    ])
    def test_calculate_profit_with_various_prices(
        self, scanner, buy_price, sell_price, expected
    ):
        """Тест расчета прибыли для различных цен."""
        # Act
        profit = scanner.calculate_profit(
            buy_price=buy_price,
            sell_price=sell_price,
            commission_percent=7.0
        )

        # Assert
        assert abs(profit - expected) < 0.01
```

---

## 📚 Специфичные правила для проекта

### HTTP-запросы
- **Предпочитать httpx** для всех HTTP-запросов (async/sync)
- Использовать пулы соединений для оптимизации
- Всегда устанавливать timeout для запросов
- Обрабатывать ошибки сети и таймауты

```python
async with httpx.AsyncClient(timeout=10.0) as client:
    response = await client.get(url)
```

### Тестирование
- Использовать **pytest** и **pytest-asyncio** для тестов
- Стремиться к покрытию кода **80%+** (текущая цель: 85%)
- Писать unit-тесты для всех публичных функций
- Использовать **pytest-mock** для моков внешних зависимостей
- Тестировать граничные случаи и обработку ошибок
- Именовать тесты описательно: `test_<функция>_<условие>_<ожидаемый_результат>`

```python
@pytest.mark.asyncio
async def test_get_balance_returns_valid_balance_on_success(mock_dmarket_api):
    """Тест проверяет корректный возврат баланса при успешном запросе."""
    balance = await mock_dmarket_api.get_balance()
    assert balance is not None
    assert "USD" in balance
    assert balance["USD"] >= 0
```

### Поддержка нескольких игр
- Все функции должны поддерживать **multi-game режим**: CS:GO, Dota 2, TF2, Rust
- Использовать enum для списка поддерживаемых игр
- Фильтры и анализ должны быть игро-агностичными

```python
from enum import Enum

class SupportedGame(str, Enum):
    CSGO = "csgo"
    DOTA2 = "dota2"
    TF2 = "tf2"
    RUST = "rust"
```

### Rate Limiting
- **Всегда реализовывать rate limiting** для внешних API
- Использовать библиотеки типа `aiolimiter` или встроенные механизмы
- Учитывать лимиты DMarket API (обычно 30 запросов/минуту)
- Логировать случаи превышения лимитов

```python
from aiolimiter import AsyncLimiter

rate_limiter = AsyncLimiter(max_rate=30, time_period=60)  # 30 req/min

async def api_call():
    async with rate_limiter:
        # выполнить запрос
        pass
```

### Кэширование
- Использовать **Redis** для кэширования частых данных
- Кэшировать результаты API запросов на разумное время (5-15 минут)
- Использовать `aiocache` для удобной работы с кэшем
- Инвалидировать кэш при изменении данных

```python
from aiocache import cached

@cached(ttl=300)  # кэш на 5 минут
async def get_market_items(game: str) -> list[dict]:
    # запрос к API
    pass
```

### Безопасность
- **Шифровать чувствительные данные** (API ключи пользователей)
- Использовать `cryptography` для шифрования
- Валидировать все входные данные от пользователей
- Ограничивать доступ к admin-командам
- Использовать HTTPS для всех внешних запросов

```python
from cryptography.fernet import Fernet

def encrypt_api_key(key: str, encryption_key: bytes) -> bytes:
    f = Fernet(encryption_key)
    return f.encrypt(key.encode())
```

### Git коммиты
- Следовать **Conventional Commits**: `type(scope): message`
- Типы: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`
- Примеры:
  - `feat(arbitrage): add cross-game arbitrage detection`
  - `fix(api): handle rate limit errors correctly`
  - `docs(readme): update installation instructions`

### Контейнеризация
- Проект **должен быть Dockerизирован**
- Использовать multi-stage builds для оптимизации размера образа
- Предоставлять `docker-compose.yml` для локальной разработки
- Включать PostgreSQL и Redis в docker-compose

---

## 🏗️ Структура проекта

```
DMarket-Telegram-Bot/
├── src/
│   ├── dmarket/              # DMarket API клиент
│   │   ├── dmarket_api.py   # Основной API клиент с HMAC auth
│   │   ├── arbitrage_scanner.py  # Многоуровневый сканер (5 уровней)
│   │   ├── targets.py       # Управление таргетами (Buy Orders)
│   │   ├── arbitrage.py     # Логика арбитража
│   │   ├── game_filters.py  # Фильтры для CS:GO, Dota 2, TF2, Rust
│   │   ├── liquidity_analyzer.py  # Анализ ликвидности рынка
│   │   ├── market_analysis.py     # Технический анализ цен
│   │   ├── sales_history.py       # История продаж
│   │   ├── schemas.py       # Pydantic модели валидации
│   │   └── filters/         # Фильтры по играм
│   ├── telegram_bot/         # Telegram бот
│   │   ├── commands/        # Обработчики команд
│   │   ├── handlers/        # Message/callback handlers
│   │   ├── keyboards.py     # Inline клавиатуры
│   │   ├── localization.py  # i18n (RU, EN, ES, DE)
│   │   ├── notifier.py      # Push-уведомления
│   │   ├── smart_notifier.py    # Умные уведомления
│   │   ├── notification_queue.py # Очередь уведомлений
│   │   └── pagination.py    # Пагинация результатов
│   ├── utils/                # Вспомогательные утилиты
│   │   ├── database.py      # SQLAlchemy session management
│   │   ├── memory_cache.py  # In-memory кэш (TTLCache)
│   │   ├── redis_cache.py   # Redis кэширование
│   │   ├── rate_limiter.py  # API rate limiting (aiolimiter)
│   │   ├── logging_utils.py # Structured logging (structlog)
│   │   ├── api_circuit_breaker.py  # Circuit Breaker паттерн
│   │   ├── sentry_integration.py   # Мониторинг Sentry
│   │   ├── batch_processor.py      # Пакетная обработка
│   │   ├── reactive_websocket.py   # Реактивный WebSocket
│   │   ├── state_manager.py        # Управление состоянием
│   │   └── config.py        # Pydantic Settings
│   ├── models/               # Модели данных (SQLAlchemy 2.0)
│   │   └── ...
│   └── main.py               # Точка входа
├── tests/                    # Тесты (2348 тестов)
│   ├── unit/                # Юнит-тесты
│   ├── integration/         # Интеграционные тесты
│   ├── contracts/           # Pact контрактные тесты (43 теста)
│   ├── property_based/      # Hypothesis property-based тесты
│   ├── cassettes/           # VCR.py записи HTTP
│   ├── conftest.py          # Основные фикстуры
│   └── conftest_vcr.py      # VCR.py фикстуры
├── docs/                     # Документация
│   ├── README.md            # Индекс документации
│   ├── ARCHITECTURE.md      # Архитектура проекта
│   ├── ARBITRAGE.md         # Руководство по арбитражу
│   ├── SECURITY.md          # Руководство по безопасности
│   ├── QUICK_START.md       # Быстрый старт
│   ├── CONTRACT_TESTING.md  # Контрактное тестирование
│   └── ...
├── config/                   # Конфигурация
│   └── config.yaml
├── alembic/                  # Миграции базы данных
│   └── versions/
├── docker-compose.yml        # Docker окружение (bot, postgres, redis)
├── Dockerfile               # Multi-stage build
├── pyproject.toml           # Конфигурация инструментов (Ruff, Black, MyPy)
├── requirements.txt         # Python зависимости
└── .env.example             # Пример переменных окружения
```

### Ключевые модули

#### ArbitrageScanner
- **Файл**: `src/dmarket/arbitrage_scanner.py`
- **Назначение**: Многоуровневое сканирование арбитражных возможностей
- **Уровни**: boost, standard, medium, advanced, pro
- **Функции**: параллельное сканирование, кэширование, фильтрация

#### TargetManager
- **Файл**: `src/dmarket/targets.py`
- **Назначение**: Управление таргетами (Buy Orders)
- **Функции**: создание, удаление, статистика, умные таргеты

#### DMarketAPI
- **Файл**: `src/dmarket/dmarket_api.py`
- **Назначение**: Клиент для DMarket API
- **Особенности**: HMAC-SHA256 auth, rate limiting, retry logic, кэширование

---

## ✅ Checklist перед коммитом

- [ ] Код отформатирован Black
- [ ] Ruff проверка пройдена
- [ ] MyPy проверка типов пройдена
- [ ] Все тесты проходят (pytest)
- [ ] Покрытие тестами >= 80%
- [ ] Добавлены docstrings для публичных функций
- [ ] Обновлена документация (если нужно)
- [ ] Нет захардкоженных секретов
- [ ] Логирование добавлено для важных операций
- [ ] Обработка ошибок реализована
- [ ] Коммит следует Conventional Commits

---

## 🚫 Запрещенные действия

### Создание избыточной документации
- **СТРОГО ЗАПРЕЩЕНО** создавать отчетные файлы после выполнения задач:
  - `WORK_COMPLETED.md`
  - `TASK_SUMMARY.md`
  - `IMPLEMENTATION_REPORT.md`
  - `CHANGES_MADE.md`
  - `REFACTORING_REPORT.md`
  - Любые подобные файлы с описанием выполненной работы
- **ИСКЛЮЧЕНИЯ**: Только явный запрос пользователя на создание конкретного документа

### Автоматизация команд
- **НЕ запрашивать подтверждение** для очевидных действий:
  - Установка зависимостей (`pip install`, `npm install`)
  - Запуск тестов (`pytest`, `npm test`)
  - Форматирование кода (`black`, `ruff`)
  - Запуск линтеров
  - Миграции БД при явной инструкции
  - Сборка Docker-образов
- **Запрашивать подтверждение** только для:
  - Удаления файлов/директорий
  - Изменения production конфигурации
  - Деплоя в production
  - Необратимых операций с БД (DROP TABLE и т.д.)

### Общение с пользователем
- **Отвечать кратко и по делу** (1-3 предложения для простых задач)
- **НЕ повторять** очевидную информацию
- **НЕ использовать** фразы типа:
  - "Вот что я сделал..."
  - "Позвольте мне объяснить..."
  - "Я выполнил следующие действия..."
  - "Вот подробный отчет..."
- **Использовать** прямые ответы:
  - "Готово" / "Выполнено"
  - "Тесты прошли успешно"
  - "Найдено 3 проблемы: ..."
  - "Ошибка: <описание>"

---

## 📖 Дополнительные рекомендации

### Docstrings
- Использовать **Google Style** для docstrings
- Документировать параметры, возвращаемые значения и исключения
- Включать примеры использования для сложных функций

```python
async def calculate_arbitrage_profit(
    buy_price: float,
    sell_price: float,
    fee_percent: float = 7.0
) -> float:
    """Рассчитать прибыль от арбитража с учетом комиссии.

    Args:
        buy_price: Цена покупки предмета
        sell_price: Цена продажи предмета
        fee_percent: Процент комиссии площадки (по умолчанию 7%)

    Returns:
        Чистая прибыль от арбитража

    Raises:
        ValueError: Если цены отрицательные

    Example:
        >>> await calculate_arbitrage_profit(10.0, 15.0, 7.0)
        3.95
    """
    if buy_price < 0 or sell_price < 0:
        raise ValueError("Prices cannot be negative")

    fee = sell_price * (fee_percent / 100)
    return sell_price - buy_price - fee
```

### Performance
- Использовать `asyncio.gather()` для параллельного выполнения независимых задач
- Применять connection pooling для БД
- Кэшировать результаты дорогостоящих вычислений
- Использовать индексы в БД для часто запрашиваемых полей

### WebSocket
- Использовать WebSocket для real-time данных о ценах
- Реализовать reconnection logic с exponential backoff
- Обрабатывать разрывы соединения gracefully

### Локализация
- Поддерживать минимум английский и русский языки
- Использовать gettext или подобные для i18n
- Хранить переводы в отдельных файлах

---

## 🔧 Инструменты разработки

- **IDE**: VS Code с расширениями Python, Pylance, Ruff
- **Форматтер**: Black
- **Линтер**: Ruff
- **Проверка типов**: MyPy
- **Тестирование**: pytest, pytest-asyncio, pytest-cov
- **Pre-commit hooks**: для автоматической проверки перед коммитом
- **CI/CD**: GitHub Actions
- **Контейнеризация**: Docker, docker-compose
- **Мониторинг**: Sentry для ошибок, Prometheus для метрик

---

## 📝 Примеры кода

### Создание нового API endpoint

```python
from typing import Any
import httpx
from tenacity import retry, stop_after_attempt

class DMarketAPI:
    async def get_item_details(self, item_id: str) -> dict[str, Any]:
        """Получить детальную информацию о предмете.

        Args:
            item_id: Идентификатор предмета

        Returns:
            Словарь с информацией о предмете

        Raises:
            httpx.HTTPError: При ошибке HTTP запроса
        """
        url = f"{self.base_url}/market/items/{item_id}"

        try:
            async with self.rate_limiter:
                response = await self.client.get(url)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error("failed_to_fetch_item", item_id=item_id, error=str(e))
            raise
```

### Создание Telegram команды

```python
from telegram import Update
from telegram.ext import ContextTypes

async def balance_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Обработчик команды /balance."""
    if not update.message:
        return

    user_id = update.effective_user.id
    logger.info("balance_command_received", user_id=user_id)

    try:
        balance = await dmarket_api.get_balance()
        await update.message.reply_text(
            f"💰 Ваш баланс: ${balance['USD']:.2f}"
        )
    except Exception as e:
        logger.error("balance_command_failed", user_id=user_id, error=str(e))
        await update.message.reply_text(
            "❌ Не удалось получить баланс. Попробуйте позже."
        )
```

---

**Версия**: 4.0
**Последнее обновление**: 13 ноября 2025 г.

---

## 📚 Документация проекта (50 файлов)

Вся документация находится в папке `docs/` и организована по категориям:

### 🚀 Начало работы (4 файла)
| Файл | Описание |
|------|----------|
| [README.md](../docs/README.md) | **Главный индекс** - навигация по всей документации |
| [QUICK_START.md](../docs/QUICK_START.md) | Запуск бота за 5 минут, чеклисты |
| [deployment.md](../docs/deployment.md) | Развертывание: Docker, Heroku, AWS, GCP |
| [TODO_CHEATSHEET.md](../docs/TODO_CHEATSHEET.md) | Шпаргалка по TODO-спискам |

### 🏗️ Архитектура (4 файла)
| Файл | Описание |
|------|----------|
| [ARCHITECTURE.md](../docs/ARCHITECTURE.md) | Полная архитектура, UML диаграммы |
| [project_structure.md](../docs/project_structure.md) | Структура папок и модулей |
| [DATA_STRUCTURES_GUIDE.md](../docs/DATA_STRUCTURES_GUIDE.md) | Структуры данных проекта |
| [DEPENDENCY_INJECTION.md](../docs/DEPENDENCY_INJECTION.md) | DI паттерны (dependency-injector) |

### 📡 API (4 файла)
| Файл | Описание |
|------|----------|
| [api_reference.md](../docs/api_reference.md) | Справочник методов бота |
| [DMARKET_API_FULL_SPEC.md](../docs/DMARKET_API_FULL_SPEC.md) | **DMarket API v1.1.0** - цены в центах! |
| [TELEGRAM_BOT_API.md](../docs/TELEGRAM_BOT_API.md) | Telegram Bot API 9.2 справочник |
| [API_COVERAGE_MATRIX.md](../docs/API_COVERAGE_MATRIX.md) | Матрица покрытия API методов |

### 💰 Торговля и арбитраж (6 файлов)
| Файл | Описание |
|------|----------|
| [ARBITRAGE.md](../docs/ARBITRAGE.md) | **Полное руководство** - 5 уровней, таргеты, стратегии |
| [game_filters_guide.md](../docs/game_filters_guide.md) | Фильтры: CS:GO, Dota 2, TF2, Rust |
| [MARKET_ANALYTICS_GUIDE.md](../docs/MARKET_ANALYTICS_GUIDE.md) | RSI, MACD, Bollinger, тренды |
| [ADVANCED_FILTERS_GUIDE.md](../docs/ADVANCED_FILTERS_GUIDE.md) | Продвинутая фильтрация |
| [PRICE_SANITY_CHECK_GUIDE.md](../docs/PRICE_SANITY_CHECK_GUIDE.md) | Валидация цен |
| [TRADING_NOTIFICATIONS_GUIDE.md](../docs/TRADING_NOTIFICATIONS_GUIDE.md) | Торговые уведомления |

### 🔔 Уведомления (4 файла)
| Файл | Описание |
|------|----------|
| [NOTIFICATION_FILTERS_GUIDE.md](../docs/NOTIFICATION_FILTERS_GUIDE.md) | Фильтрация уведомлений |
| [NOTIFICATION_DIGESTS_GUIDE.md](../docs/NOTIFICATION_DIGESTS_GUIDE.md) | Дайджесты уведомлений |
| [DAILY_REPORTS_GUIDE.md](../docs/DAILY_REPORTS_GUIDE.md) | Ежедневные отчеты |
| [DASHBOARD_GUIDE.md](../docs/DASHBOARD_GUIDE.md) | Интерактивный дашборд |

### 🛠️ Разработка (8 файлов)
| Файл | Описание |
|------|----------|
| [CONTRIBUTING.md](../docs/CONTRIBUTING.md) | Как помочь проекту |
| [code_quality_tools_guide.md](../docs/code_quality_tools_guide.md) | **Ruff 0.8+, MyPy strict** |
| [testing_guide.md](../docs/testing_guide.md) | pytest, VCR.py, Hypothesis |
| [CONTRACT_TESTING.md](../docs/CONTRACT_TESTING.md) | Pact контрактное тестирование |
| [INTEGRATION_TESTING_GUIDE.md](../docs/INTEGRATION_TESTING_GUIDE.md) | Интеграционные тесты |
| [DEBUG_WORKFLOW.md](../docs/DEBUG_WORKFLOW.md) | Отладка и troubleshooting |
| [schema_validation_guide.md](../docs/schema_validation_guide.md) | Валидация Pydantic схем |
| [AI_TOOLS_GUIDE.md](../docs/AI_TOOLS_GUIDE.md) | Интеграция с AI инструментами |

### ⚡ Производительность (5 файлов)
| Файл | Описание |
|------|----------|
| [CACHING_GUIDE.md](../docs/CACHING_GUIDE.md) | TTLCache, Redis, Query Cache |
| [batch_processing_guide.md](../docs/batch_processing_guide.md) | Пакетная обработка |
| [REACTIVE_WEBSOCKET_GUIDE.md](../docs/REACTIVE_WEBSOCKET_GUIDE.md) | WebSocket Observable паттерн |
| [state_management_guide.md](../docs/state_management_guide.md) | Управление состоянием |
| [AUTO_SHUTDOWN_GUIDE.md](../docs/AUTO_SHUTDOWN_GUIDE.md) | Автоматическое завершение |

### 🔒 Безопасность и ошибки (4 файла)
| Файл | Описание |
|------|----------|
| [SECURITY.md](../docs/SECURITY.md) | **DRY_RUN режим**, шифрование ключей |
| [ERROR_HANDLING_GUIDE.md](../docs/ERROR_HANDLING_GUIDE.md) | Обработка ошибок |
| [logging_and_error_handling.md](../docs/logging_and_error_handling.md) | Structlog, уровни логов |
| [BREADCRUMBS_GUIDE.md](../docs/BREADCRUMBS_GUIDE.md) | Хлебные крошки для отладки |

### 📊 Мониторинг (3 файла)
| Файл | Описание |
|------|----------|
| [SENTRY_GUIDE.md](../docs/SENTRY_GUIDE.md) | **Sentry** - настройка, алерты, очистка |
| [MONITORING_GUIDE.md](../docs/MONITORING_GUIDE.md) | Общий мониторинг системы |
| [PRODUCTION_IMPROVEMENTS.md](../docs/PRODUCTION_IMPROVEMENTS.md) | Улучшения для production |

### 🚀 CI/CD и DevOps (4 файла)
| Файл | Описание |
|------|----------|
| [CI_CD_GUIDE.md](../docs/CI_CD_GUIDE.md) | GitHub Actions полный гайд |
| [CI_CD_QUICKSTART.md](../docs/CI_CD_QUICKSTART.md) | Быстрый старт CI/CD |
| [DATABASE_MIGRATIONS.md](../docs/DATABASE_MIGRATIONS.md) | Alembic async миграции |
| [TELEGRAM_BOT_API_IMPROVEMENTS.md](../docs/TELEGRAM_BOT_API_IMPROVEMENTS.md) | Улучшения Telegram API |

### 📘 Дополнительно (4 файла)
| Файл | Описание |
|------|----------|
| [TODO_WORKFLOW_EXAMPLE.md](../docs/TODO_WORKFLOW_EXAMPLE.md) | Примеры TODO workflow |
| [WORKFLOWS_OVERVIEW.md](../docs/WORKFLOWS_OVERVIEW.md) | Обзор рабочих процессов |
| [vs_code_cyrillic_protection.md](../docs/vs_code_cyrillic_protection.md) | Защита от кириллицы в VS Code |
| [TOOLS_AND_EXTENSIONS_GUIDE.md](../docs/TOOLS_AND_EXTENSIONS_GUIDE.md) | Инструменты и расширения |

### ⚡ Перед созданием нового функционала
1. Изучи **ARCHITECTURE.md** для понимания структуры
2. Проверь **api_reference.md** на наличие похожих методов
3. Следуй **code_quality_tools_guide.md** для стиля кода
4. Обнови **CHANGELOG.md** при значимых изменениях
5. Прочитай **SECURITY.md** если работаешь с API ключами

---

## 🔍 Типичные задачи и решения

### Добавление нового уровня арбитража
1. Отредактируй `src/dmarket/arbitrage_scanner.py`
2. Добавь новый уровень в `LEVELS` dict
3. Обнови `src/telegram_bot/handlers/scanner_handler.py`
4. Добавь тесты в `tests/test_arbitrage_scanner.py`
5. Обнови документацию в `docs/ARBITRAGE.md`

### Добавление новой игры
1. Добавь игру в `SupportedGame` enum (`src/dmarket/game_filters.py`)
2. Создай класс фильтра (наследуй от `BaseGameFilter`)
3. Добавь в `FilterFactory._filters`
4. Обнови `docs/game_filters_guide.md`

### Добавление новой Telegram команды
1. Создай handler в `src/telegram_bot/handlers/`
2. Зарегистрируй в `src/main.py` или соответствующем модуле
3. Добавь переводы в `src/telegram_bot/localization.py`
4. Создай клавиатуру в `src/telegram_bot/keyboards.py` (если нужно)
5. Добавь тесты

### Оптимизация производительности
1. Используй кэширование через `@cached` декоратор
2. Применяй `asyncio.gather()` для параллельных запросов
3. Проверь rate limiting настройки
4. Используй connection pooling для БД
5. Используй Circuit Breaker через `src/utils/api_circuit_breaker.py`

---

## � Важно: Избежание кириллических символов в командах

### Проблема
Одна из самых частых ошибок при работе с GitHub Copilot - случайная вставка русских букв **«с»** вместо латинской **«c»** или **«р»** вместо **«p»** в командах `pytest`, `pip`, `python`, `poetry`.

### Ключевые способы избежать проблемы:

| № | Рекомендация | Как настроить |
|---|--------------|---------------|
| 1 | **Переключать раскладку на английскую перед вставкой** | Win + Пробел → всегда EN перед Ctrl+V |
| 2 | **Включить индикатор языка в трее** | Параметры → Время и язык → Показывать индикатор |
| 3 | **Использовать шрифт с чётким различием символов** | Fira Code NF, JetBrains Mono NF, Cascadia Code NF |
| 4 | **Включить подсветку кириллицы в VS Code** | Расширение **Highlight Bad Chars** |
| 5 | **Проверять команду перед Enter** | Выделить и увеличить (Ctrl + колесо) |

### Рекомендуемые расширения VS Code:
- **Highlight Bad Chars** - подсвечивает не-ASCII символы
- **Error Lens** - показывает ошибки прямо в строке
- **Russian Characters Highlighter** - специально для кириллицы

### Настройки шрифтов для терминала:
```json
{
    "font": {
        "face": "Cascadia Code NF"
    },
    "highlightBadCharacters": true
}
```

---

## 📌 Краткая памятка

### ДА ✅
- **TODO-список для КАЖДОГО запроса** (manage_todo_list)
- Асинхронный код (`async/await`)
- Аннотации типов везде
- Краткие ответы пользователю
- Автоматическое выполнение очевидных команд
- Структурированное логирование
- Тестирование (80%+ coverage)
- **Английская раскладка при работе с командами**
- **Проверка команд перед выполнением**

### НЕТ ❌
- **Начинать работу БЕЗ TODO-списка**
- Создание отчетных markdown-файлов
- Запрос подтверждения для рутинных команд
- Длинные объяснения в чате
- Синхронный код для I/O операций
- Захардкоженные секреты
- Голые `except:` блоки
- **Кириллические символы в командах терминала**
