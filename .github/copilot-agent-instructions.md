# Инструкции для GitHub Copilot Coding Agent

> **Специфичные правила для DMarket-Telegram-Bot проекта**
>
> Эти инструкции дополняют основные `.github/copilot-instructions.md`

---

## 🎯 Приоритеты проекта

1. **Асинхронность** - весь код должен быть async/await
2. **Типизация** - MyPy strict mode, 100% аннотаций
3. **Тестирование** - покрытие 80%+, FIRST принципы
4. **Качество** - Ruff 0.14+, Black 25.0+
5. **Безопасность** - DRY_RUN режим, шифрование ключей

---

## 📋 Перед началом работы

### ОБЯЗАТЕЛЬНО проверить:
```bash
# 1. Запустить линтеры
ruff check src/ tests/
mypy src/

# 2. Запустить тесты
pytest tests/ -v --maxfail=5

# 3. Проверить покрытие
pytest --cov=src --cov-report=term-missing
```

### Если тесты падают:
- ❌ **НЕ игнорировать** падающие тесты
- ✅ **Исправить** только если связано с текущей задачей
- ✅ **Отметить** в PR description если есть несвязанные ошибки

---

## 🏗️ Архитектурные правила

### Структура модулей
```
src/
├── dmarket/          # DMarket API - КРИТИЧЕСКИЙ модуль
│   ├── dmarket_api.py         # Только HTTP запросы + HMAC auth
│   ├── arbitrage_scanner.py   # Логика арбитража, 5 уровней
│   └── targets.py             # Buy Orders управление
├── telegram_bot/     # Telegram handlers
│   ├── commands/              # Команды /start, /balance и т.д.
│   └── handlers/              # Callback handlers
└── utils/            # Вспомогательные утилиты
    ├── rate_limiter.py        # API rate limiting (30 req/min)
    └── redis_cache.py         # Кэширование (TTL 5-15 min)
```

### Dependency Flow (ВАЖНО!)
```
telegram_bot → dmarket → utils
     ↓            ↓         ↓
   models ←──────┴─────────┘
```

**Запрещено:**
- ❌ Импорты `telegram_bot` в `dmarket`
- ❌ Импорты `dmarket` в `utils` (кроме типов)
- ❌ Циклические зависимости

---

## 💻 Стиль кода

### Async/await паттерны

```python
# ✅ ПРАВИЛЬНО - асинхронный код
async def get_market_data(item_id: str) -> dict[str, Any]:
    async with httpx.AsyncClient() as client:
        response = await client.get(f"/items/{item_id}")
        return response.json()

# ❌ НЕПРАВИЛЬНО - синхронный код
def get_market_data(item_id: str) -> dict[str, Any]:
    response = requests.get(f"/items/{item_id}")
    return response.json()
```

### Типизация (MyPy Strict)

```python
# ✅ ПРАВИЛЬНО - полная типизация
from typing import TypeAlias

PriceData: TypeAlias = dict[str, float | int]

async def calculate_profit(
    buy_price: float,
    sell_price: float,
    commission: float = 7.0
) -> float:
    """Рассчитать прибыль с учетом комиссии."""
    return (sell_price - buy_price) * (1 - commission / 100)

# ❌ НЕПРАВИЛЬНО - без типов
async def calculate_profit(buy_price, sell_price, commission=7.0):
    return (sell_price - buy_price) * (1 - commission / 100)
```

### Логирование (structlog)

```python
import structlog

logger = structlog.get_logger(__name__)

# ✅ ПРАВИЛЬНО - структурированное логирование
async def process_order(order_id: str, user_id: int) -> None:
    logger.info(
        "processing_order",
        order_id=order_id,
        user_id=user_id,
        event="start"
    )
    try:
        # обработка
        logger.info("order_completed", order_id=order_id)
    except Exception as e:
        logger.error(
            "order_failed",
            order_id=order_id,
            error=str(e),
            exc_info=True
        )

# ❌ НЕПРАВИЛЬНО - простые print или обычный logging
print(f"Processing order {order_id}")  # Запрещено!
```

### Обработка ошибок

```python
from tenacity import retry, stop_after_attempt, wait_exponential

# ✅ ПРАВИЛЬНО - retry с tenacity
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def fetch_with_retry(url: str) -> dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        logger.error("http_error", url=url, status=e.response.status_code)
        raise
    except httpx.RequestError as e:
        logger.error("request_error", url=url, error=str(e))
        raise

# ❌ НЕПРАВИЛЬНО - голый except
async def fetch_data(url):
    try:
        return await client.get(url)
    except:  # Запрещено!
        pass
```

---

## 🧪 Тестирование

### AAA Паттерн (ОБЯЗАТЕЛЬНО)

```python
@pytest.mark.asyncio
async def test_get_balance_returns_correct_value():
    """Тест: get_balance возвращает корректные данные."""
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

```
test_<функция>_<условие>_<ожидаемый_результат>
```

**Примеры:**
- ✅ `test_calculate_profit_with_zero_price_returns_zero`
- ✅ `test_create_target_with_invalid_price_raises_validation_error`
- ✅ `test_scan_arbitrage_when_no_items_returns_empty_list`

**Анти-паттерны:**
- ❌ `test_profit`
- ❌ `test_1`
- ❌ `test_function`

### Покрытие

**Минимальные требования:**
- `src/dmarket/` - **85%+**
- `src/telegram_bot/` - **80%+**
- `src/utils/` - **90%+**

**Проверка покрытия:**
```bash
pytest --cov=src --cov-report=term-missing --cov-fail-under=80
```

---

## 🔒 Безопасность

### Секреты (КРИТИЧНО!)

```python
# ✅ ПРАВИЛЬНО - из переменных окружения
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    telegram_bot_token: str
    dmarket_public_key: str
    dmarket_secret_key: str

    class Config:
        env_file = ".env"

settings = Settings()

# ❌ НЕПРАВИЛЬНО - хардкод
API_KEY = "sk-1234567890"  # Запрещено!
```

### DRY_RUN режим

```python
# Всегда проверять DRY_RUN перед изменениями
if not settings.dry_run:
    await api.buy_item(item_id, price)
else:
    logger.info("dry_run_mode", action="buy_item", item_id=item_id)
```

---

## 🚀 Специфичные задачи

### Добавление нового уровня арбитража

1. Отредактировать `src/dmarket/arbitrage_scanner.py`:
   ```python
   LEVELS = {
       "new_level": {
           "min_price": 5000,  # $50 в центах
           "max_price": 15000, # $150 в центах
           "min_profit": 10.0  # 10% минимум
       }
   }
   ```

2. Обновить handler в `src/telegram_bot/handlers/scanner_handler.py`
3. Добавить тесты в `tests/unit/dmarket/test_arbitrage_scanner.py`
4. Обновить документацию в `docs/ARBITRAGE.md`

### Добавление новой Telegram команды

1. Создать handler в `src/telegram_bot/handlers/`
2. Зарегистрировать в `src/main.py`
3. Добавить перевод в `src/telegram_bot/localization.py` (RU, EN)
4. Создать клавиатуру в `src/telegram_bot/keyboards.py` (если нужно)
5. Добавить тесты с мокированным `Update` объектом

### Добавление нового game filter

1. Добавить игру в `SupportedGame` enum (`src/dmarket/game_filters.py`)
2. Создать класс фильтра (наследовать от `BaseGameFilter`)
3. Добавить в `FilterFactory._filters`
4. Тесты с параметризацией `@pytest.mark.parametrize`
5. Документация в `docs/game_filters_guide.md`

---

## 📊 Метрики производительности

### Критические пороги

| Операция                   | Максимум | Оптимально |
| -------------------------- | -------- | ---------- |
| API запрос к DMarket       | 3s       | <1s        |
| Сканирование одного уровня | 10s      | <5s        |
| Создание таргета           | 2s       | <1s        |
| Запрос баланса             | 1s       | <500ms     |
| Загрузка истории           | 5s       | <2s        |

**Если превышены пороги:**
1. Проверить rate limiting
2. Использовать `asyncio.gather()` для параллелизма
3. Добавить кэширование через `@cached`
4. Профилировать через `cProfile`

---

## 🐛 Отладка

### Логи

```bash
# Включить DEBUG логи
export LOG_LEVEL=DEBUG
python -m src.main

# Structlog контекст
logger.bind(request_id="123").info("event", key="value")
```

### Sentry

```python
import sentry_sdk

# Добавить контекст
with sentry_sdk.configure_scope() as scope:
    scope.set_tag("user_id", user_id)
    scope.set_context("arbitrage", {"level": "standard"})
```

---

## 📚 Полезные ссылки

- **Основные инструкции**: `.github/copilot-instructions.md`
- **Архитектура**: `docs/ARCHITECTURE.md`
- **Арбитраж**: `docs/ARBITRAGE.md`
- **API Reference**: `docs/api_reference.md`
- **Тестирование**: `docs/testing_guide.md`
- **CI/CD**: `docs/CI_CD_GUIDE.md`

---

## ⚠️ Типичные ошибки Copilot

1. ❌ **Использование `requests` вместо `httpx`**
   - Исправление: Всегда `async with httpx.AsyncClient()`

2. ❌ **Забыл `@pytest.mark.asyncio` в тестах**
   - Исправление: Добавить декоратор для async функций

3. ❌ **Импорт `telegram_bot` в `dmarket`**
   - Исправление: Пересмотреть архитектуру

4. ❌ **Кириллица в комментариях без RUF001 игнорирования**
   - Исправление: Ruff автоматически игнорирует (см. pyproject.toml)

5. ❌ **Тесты зависят друг от друга**
   - Исправление: Использовать фикстуры, изолировать состояние

---

## 🎯 Checklist для PR

**Перед открытием Pull Request:**

- [ ] `ruff check src/ tests/` - 0 ошибок
- [ ] `mypy src/` - 0 ошибок
- [ ] `pytest tests/` - все тесты проходят
- [ ] `pytest --cov=src --cov-fail-under=80` - покрытие ≥80%
- [ ] Все функции имеют Google-style docstrings
- [ ] Нет захардкоженных секретов (`bandit -r src/`)
- [ ] Обновлены соответствующие `docs/` (если нужно)
- [ ] Коммиты следуют Conventional Commits (`feat:`, `fix:`, `docs:`)

---

**Версия**: 1.0
**Дата**: 14 декабря 2025
**Для вопросов**: см. `docs/README.md` или создай issue
