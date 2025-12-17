# 🍞 Руководство по Sentry Breadcrumbs

**Дата**: 17 декабря 2025 г.
**Версия**: 3.0

---

## 📋 Оглавление

- [Введение](#введение)
- [Что такое Breadcrumbs](#что-такое-breadcrumbs)
- [Архитектура](#архитектура)
- [Использование](#использование)
- [Примеры](#примеры)
- [Лучшие практики](#лучшие-практики)
- [Отладка с помощью breadcrumbs](#отладка-с-помощью-breadcrumbs)

---

## 🎯 Введение

Breadcrumbs (хлебные крошки) — это механизм логирования событий в Sentry, который помогает понять **контекст** возникновения ошибки. Каждый breadcrumb — это запись о действии пользователя, API вызове, изменении состояния или другом событии, которое произошло перед ошибкой.

### Зачем нужны breadcrumbs?

❌ **Без breadcrumbs**:

```
Error: HTTPStatusError 429 Too Many Requests
  at dmarket_api.py:705
```

Непонятно, что привело к ошибке.

✅ **С breadcrumbs**:

```
Error: HTTPStatusError 429 Too Many Requests
  at dmarket_api.py:705

Breadcrumbs:
1. [12:00:01] Command: /arbitrage (user_id: 123456789)
2. [12:00:02] Trading: arbitrage_scan_started (game: csgo, mode: standard)
3. [12:00:03] API: GET /market/items (status: 200, 450ms)
4. [12:00:04] API: GET /market/items (status: 200, 520ms)
5. [12:00:05] API: GET /market/items (status: 429, error: rate_limit)
```

Теперь видно полную цепочку событий!

---

## 🧠 Что такое Breadcrumbs

### Типы breadcrumbs

Sentry поддерживает несколько категорий breadcrumbs:

| Категория    | Описание               | Примеры                           |
| ------------ | ---------------------- | --------------------------------- |
| `default`    | Общие события          | Логи, изменения состояния         |
| `http`       | HTTP запросы           | API вызовы, webhook'и             |
| `navigation` | Навигация пользователя | Команды бота, переходы между меню |
| `user`       | Действия пользователя  | Клики, ввод данных                |
| `error`      | Ошибки                 | Исключения, неудачные операции    |
| `query`      | Запросы к БД           | SELECT, INSERT, UPDATE            |

### Структура breadcrumb

```python
{
    "type": "http",              # Тип события
    "category": "api",           # Категория
    "message": "GET /market/items",  # Описание
    "level": "info",             # Уровень (debug, info, warning, error, critical)
    "timestamp": 1700000000.123, # Unix timestamp
    "data": {                    # Дополнительные данные
        "status_code": 200,
        "response_time_ms": 450,
        "endpoint": "/market/items",
        "method": "GET"
    }
}
```

---

## 🏗️ Архитектура

### Модуль sentry_breadcrumbs.py

Централизованный модуль с утилитами для работы с breadcrumbs находится в:

```
src/utils/sentry_breadcrumbs.py
```

### Основные функции

#### 1. add_trading_breadcrumb

Для отслеживания торговых операций.

```python
from src.utils.sentry_breadcrumbs import add_trading_breadcrumb

add_trading_breadcrumb(
    action="arbitrage_scan_started",
    game="csgo",
    level="standard",
    user_id=123456789,
    balance=100.50,
    max_items=100,
    price_from=5.0,
    price_to=100.0
)
```

**Параметры**:

- `action` (обязательный): Тип действия (scan_started, buy_intent, sell_completed)
- `game` (обязательный): Игра (csgo, dota2, tf2, rust)
- `level`: Уровень арбитража (boost, standard, medium, advanced, pro)
- `user_id`: ID пользователя Telegram
- `balance`: Текущий баланс
- `**extra`: Дополнительные данные (любые ключи-значения)

#### 2. add_api_breadcrumb

Для отслеживания API запросов.

```python
from src.utils.sentry_breadcrumbs import add_api_breadcrumb

add_api_breadcrumb(
    endpoint="/market/items",
    method="GET",
    status_code=200,
    response_time_ms=450.5,
    retry_attempt=0
)
```

**Параметры**:

- `endpoint` (обязательный): Путь API (без домена)
- `method` (обязательный): HTTP метод (GET, POST, PUT, DELETE)
- `status_code`: HTTP статус код
- `response_time_ms`: Время ответа в миллисекундах
- `**extra`: Дополнительные данные (error, retry_attempt, has_cache)

#### 3. add_command_breadcrumb

Для отслеживания команд Telegram бота.

```python
from src.utils.sentry_breadcrumbs import add_command_breadcrumb

add_command_breadcrumb(
    command="/arbitrage",
    user_id=123456789,
    username="john_doe",
    chat_id=987654321
)
```

**Параметры**:

- `command` (обязательный): Название команды (с /)
- `user_id` (обязательный): ID пользователя
- `username`: Username пользователя
- `chat_id`: ID чата
- `**extra`: Дополнительные данные

#### 4. add_database_breadcrumb

Для отслеживания операций с базой данных.

```python
from src.utils.sentry_breadcrumbs import add_database_breadcrumb

add_database_breadcrumb(
    operation="INSERT",
    table="users",
    record_id=123,
    affected_rows=1
)
```

**Параметры**:

- `operation` (обязательный): Тип операции (SELECT, INSERT, UPDATE, DELETE)
- `table` (обязательный): Название таблицы
- `record_id`: ID записи
- `affected_rows`: Количество затронутых строк
- `**extra`: Дополнительные данные

#### 5. add_error_breadcrumb

Для отслеживания ошибок и исключений.

```python
from src.utils.sentry_breadcrumbs import add_error_breadcrumb

add_error_breadcrumb(
    error_type="HTTPStatusError",
    error_message="429 Too Many Requests",
    severity="warning"
)
```

**Параметры**:

- `error_type` (обязательный): Тип ошибки (название класса исключения)
- `error_message` (обязательный): Сообщение об ошибке
- `severity`: Уровень серьезности (debug, info, warning, error, critical)
- `**extra`: Дополнительные данные

#### 6. set_user_context

Установить контекст пользователя для всей сессии.

```python
from src.utils.sentry_breadcrumbs import set_user_context

set_user_context(
    user_id=123456789,
    username="john_doe",
    email="john@example.com"
)
```

#### 7. set_context_tag

Установить тег для контекста.

```python
from src.utils.sentry_breadcrumbs import set_context_tag

set_context_tag("environment", "production")
set_context_tag("game", "csgo")
set_context_tag("arbitrage_level", "standard")
```

---

## 💡 Использование

### В DMarket API клиенте

```python
# src/dmarket/dmarket_api.py

from src.utils.sentry_breadcrumbs import add_api_breadcrumb

async def _request(self, method: str, path: str, **kwargs):
    """Выполнить HTTP запрос к DMarket API."""
    start_time = time.time()

    # Breadcrumb перед запросом
    add_api_breadcrumb(
        endpoint=path,
        method=method.upper(),
        retry_attempt=retries,
        has_cache=self._has_cache(cache_key),
    )

    try:
        # Выполнить запрос
        response = await client.get(url, **kwargs)
        response_time_ms = (time.time() - start_time) * 1000

        # Breadcrumb после успешного ответа
        add_api_breadcrumb(
            endpoint=path,
            method=method.upper(),
            status_code=response.status_code,
            response_time_ms=response_time_ms,
        )

        return response.json()

    except httpx.HTTPStatusError as e:
        # Breadcrumb при HTTP ошибке
        add_api_breadcrumb(
            endpoint=path,
            method=method.upper(),
            status_code=e.response.status_code,
            error="http_error",
            retry_attempt=retries,
        )
        raise
```

### В ArbitrageScanner

```python
# src/dmarket/arbitrage_scanner.py

from src.utils.sentry_breadcrumbs import add_trading_breadcrumb

async def scan_game(self, game: str, mode: str, **kwargs):
    """Сканировать игру на арбитражные возможности."""

    # Breadcrumb о начале сканирования
    add_trading_breadcrumb(
        action="arbitrage_scan_started",
        game=game,
        level=mode,
        max_items=kwargs.get("max_items", 100),
        price_from=kwargs.get("price_from"),
        price_to=kwargs.get("price_to"),
    )

    try:
        # Выполнить сканирование
        items = await self._fetch_items(game, **kwargs)

        # Breadcrumb об успешном завершении
        add_trading_breadcrumb(
            action="arbitrage_scan_completed",
            game=game,
            level=mode,
            items_found=len(items),
        )

        return items

    except Exception as e:
        # Breadcrumb об ошибке
        add_trading_breadcrumb(
            action="arbitrage_scan_error",
            game=game,
            level=mode,
            error=str(e),
        )
        raise
```

### В командах Telegram бота

```python
# src/telegram_bot/commands/basic_commands.py

from src.utils.sentry_breadcrumbs import add_command_breadcrumb

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start."""
    user = update.effective_user

    # Breadcrumb о команде
    add_command_breadcrumb(
        command="/start",
        user_id=user.id,
        username=user.username or "",
        chat_id=update.effective_chat.id if update.effective_chat else 0,
    )

    await update.message.reply_text("Привет! Я бот для DMarket.")
```

---

## 🎯 Примеры

### Пример 1: Отслеживание покупки предмета

```python
# В методе buy_item

# 1. Breadcrumb о намерении купить
add_trading_breadcrumb(
    action="buy_item_intent",
    game="csgo",
    item_id="item_123",
    price=25.50,
    item_name="AK-47 | Redline",
    user_id=123456789,
)

# 2. API breadcrumb перед запросом
add_api_breadcrumb(
    endpoint="/market/items/buy",
    method="POST",
)

try:
    # Выполнить покупку
    result = await api_client.post("/market/items/buy", data=...)

    # 3. API breadcrumb после ответа
    add_api_breadcrumb(
        endpoint="/market/items/buy",
        method="POST",
        status_code=200,
        response_time_ms=450,
    )

    # 4. Breadcrumb об успешной покупке
    add_trading_breadcrumb(
        action="buy_item_success",
        game="csgo",
        item_id="item_123",
        price=25.50,
    )

except HTTPStatusError as e:
    # 5. Breadcrumb об ошибке
    add_error_breadcrumb(
        error_type="HTTPStatusError",
        error_message=f"{e.response.status_code} {e.response.text}",
        severity="error",
    )
    raise
```

### Пример 2: Отслеживание цепочки команд

```python
# Пользователь: /arbitrage
add_command_breadcrumb(
    command="/arbitrage",
    user_id=123456789,
    username="john_doe",
)

# Пользователь выбирает "Стандарт"
add_trading_breadcrumb(
    action="arbitrage_level_selected",
    level="standard",
    user_id=123456789,
)

# Начинается сканирование
add_trading_breadcrumb(
    action="arbitrage_scan_started",
    game="csgo",
    level="standard",
)

# API вызовы
add_api_breadcrumb(endpoint="/market/items", method="GET", status_code=200)
add_api_breadcrumb(endpoint="/market/items", method="GET", status_code=200)

# Завершение
add_trading_breadcrumb(
    action="arbitrage_scan_completed",
    items_found=15,
)
```

---

## ✅ Лучшие практики

### 1. Добавляйте breadcrumbs в ключевых точках

**✅ Хорошо**: Breadcrumbs в начале, успехе и ошибке

```python
# Начало операции
add_trading_breadcrumb(action="scan_started", game="csgo")

try:
    result = await scan()

    # Успех
    add_trading_breadcrumb(action="scan_completed", items=len(result))

except Exception as e:
    # Ошибка
    add_error_breadcrumb(error_type=type(e).__name__, error_message=str(e))
    raise
```

**❌ Плохо**: Breadcrumbs только при ошибке

```python
try:
    result = await scan()
except Exception as e:
    add_error_breadcrumb(...)  # Недостаточно контекста!
```

### 2. Используйте осмысленные названия действий

**✅ Хорошо**: Конкретные действия

```python
add_trading_breadcrumb(action="arbitrage_scan_started")
add_trading_breadcrumb(action="buy_item_intent")
add_trading_breadcrumb(action="sell_item_completed")
```

**❌ Плохо**: Неинформативные названия

```python
add_trading_breadcrumb(action="start")
add_trading_breadcrumb(action="action1")
add_trading_breadcrumb(action="process")
```

### 3. Включайте важный контекст

**✅ Хорошо**: Релевантные данные

```python
add_trading_breadcrumb(
    action="buy_item_intent",
    game="csgo",
    item_id="item_123",
    price=25.50,
    user_id=123456789,
    balance_before=100.0,
)
```

**❌ Плохо**: Избыточные данные

```python
add_trading_breadcrumb(
    action="buy_item_intent",
    entire_response=huge_dict,  # Слишком много данных!
    raw_html=page_content,      # Не релевантно!
)
```

### 4. Не дублируйте логирование

Breadcrumbs **дополняют** логи, но не заменяют их:

```python
# ✅ Хорошо: И логи, и breadcrumbs
logger.info("Starting arbitrage scan", extra={"game": "csgo"})
add_trading_breadcrumb(action="scan_started", game="csgo")

# ❌ Плохо: Только breadcrumbs
add_trading_breadcrumb(action="scan_started", game="csgo")
# Нет логов!
```

### 5. Устанавливайте контекст пользователя

В начале сессии:

```python
# При авторизации/старте бота
set_user_context(
    user_id=update.effective_user.id,
    username=update.effective_user.username,
)

set_context_tag("environment", "production")
set_context_tag("bot_version", "1.0.0")
```

---

## 🔍 Отладка с помощью breadcrumbs

### Сценарий: Rate limit ошибка

**Проблема**: Пользователи жалуются на ошибку "429 Too Many Requests"

**Breadcrumbs в Sentry**:

```
1. [12:00:00] Command: /arbitrage (user_id: 123)
2. [12:00:01] Trading: arbitrage_scan_started (game: csgo, level: standard)
3. [12:00:02] API: GET /market/items (status: 200, 450ms)
4. [12:00:03] API: GET /market/items (status: 200, 520ms)
5. [12:00:04] API: GET /market/items (status: 200, 490ms)
6. [12:00:05] API: GET /market/items (status: 200, 510ms)
7. [12:00:06] API: GET /market/items (status: 429, error: rate_limit)

Error: HTTPStatusError 429 Too Many Requests
```

**Анализ**:

- Видно, что было 5 запросов за 6 секунд
- Все запросы к одному эндпоинту `/market/items`
- Проблема: недостаточная задержка между запросами

**Решение**:

- Увеличить задержку между запросами
- Добавить rate limiter
- Использовать кэширование

### Сценарий: Неожиданная ошибка при покупке

**Проблема**: Ошибка "Insufficient balance" при покупке

**Breadcrumbs в Sentry**:

```
1. [12:00:00] Command: /balance (user_id: 456)
2. [12:00:01] API: GET /balance (status: 200, balance: 50.00)
3. [12:00:05] Command: /arbitrage (user_id: 456)
4. [12:00:06] Trading: arbitrage_scan_started (game: csgo)
5. [12:00:07] Trading: buy_item_intent (price: 25.50, item: AK-47)
6. [12:00:08] Trading: buy_item_intent (price: 30.00, item: AWP)
7. [12:00:09] API: POST /buy (status: 200, item: AK-47)
8. [12:00:10] API: POST /buy (status: 400, error: insufficient_balance)

Error: Insufficient balance
```

**Анализ**:

- Баланс был 50.00
- Попытка купить 2 предмета (25.50 + 30.00 = 55.50)
- Первая покупка успешна (25.50), баланс стал 24.50
- Вторая покупка неудачна (не хватает 5.50)

**Решение**:

- Проверять баланс перед каждой покупкой
- Учитывать планируемые покупки при расчете доступного баланса

---

## 📊 Просмотр breadcrumbs в Sentry

### 1. Открыть Sentry Dashboard

Перейдите по ссылке: <https://sentry.io/>

### 2. Выбрать проект

Выберите проект "dmarket-telegram-bot"

### 3. Открыть ошибку

Кликните на любую ошибку из списка

### 4. Вкладка "Breadcrumbs"

Внизу страницы ошибки будет раздел "Breadcrumbs" с полной цепочкой событий

### 5. Фильтрация

Можно фильтровать breadcrumbs по:

- Категории (http, navigation, error)
- Уровню (info, warning, error)
- Времени

---

## 🚀 Развертывание в production

### Настройка Sentry

```python
# src/utils/logging_utils.py

import sentry_sdk
from sentry_sdk.integrations.asyncio import AsyncioIntegration
from sentry_sdk.integrations.httpx import HttpxIntegration

sentry_sdk.init(
    dsn="your-sentry-dsn",
    traces_sample_rate=0.1,  # 10% транзакций
    profiles_sample_rate=0.1,  # 10% профилирования
    max_breadcrumbs=100,  # Максимум breadcrumbs на событие
    attach_stacktrace=True,
    send_default_pii=False,  # Не отправлять PII
    integrations=[
        AsyncioIntegration(),
        HttpxIntegration(),
    ],
)
```

### Лимиты breadcrumbs

- **max_breadcrumbs**: Максимум breadcrumbs на одно событие (по умолчанию 100)
- Старые breadcrumbs автоматически удаляются при превышении лимита
- Рекомендуется: 50-100 для production

---

## 📚 Дополнительные ресурсы

- [Официальная документация Sentry Breadcrumbs](https://docs.sentry.io/platforms/python/enriching-events/breadcrumbs/)
- [Sentry Python SDK](https://docs.sentry.io/platforms/python/)
- [Best Practices for Error Tracking](https://blog.sentry.io/error-monitoring-best-practices/)

---

**Версия документа**: 1.0
**Последнее обновление**: 17 декабря 2025 г.
