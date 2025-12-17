# Telegram Bot API - Справочник

**Версия Bot API**: 9.2 (обновление от 15 августа 2025 г.)
**Базовый URL**: `https://api.telegram.org/bot<token>/METHOD_NAME`
**Дата документа**: 17 декабря 2025 г.
**Официальная документация**: [https://core.telegram.org/bots/api](https://core.telegram.org/bots/api)

> **Ключевые возможности Bot API 9.2:**
> - **Checklists** - ответы на конкретные пункты чек-листов
> - **Gifts** - отслеживание подарков с `publisher_chat`
> - **Direct Messages** - `is_direct_messages` и `parent_chat` для суперграпп
> - **Suggested Posts** - создание/одобрение предложенных постов для каналов
> - **Enhanced Admin** - `can_manage_direct_messages` для управления личными сообщениями

---

## 📋 Оглавление

1. [Введение](#введение)
2. [Аутентификация](#аутентификация)
3. [Получение обновлений](#получение-обновлений)
4. [Отправка сообщений](#отправка-сообщений)
5. [Редактирование сообщений](#редактирование-сообщений)
6. [Клавиатуры](#клавиатуры)
7. [Медиа и файлы](#медиа-и-файлы)
8. [Платежи (Telegram Stars)](#платежи-telegram-stars)
9. [Inline режим](#inline-режим)
10. [Форматирование текста](#форматирование-текста)
11. [Обработка ошибок](#обработка-ошибок)

---

## 📖 Введение

Telegram Bot API позволяет создавать ботов для Telegram с использованием HTTP-запросов. API предоставляет доступ к функциям отправки сообщений, обработки команд, работы с платежами и многому другому.

### Основные возможности

- ✅ Отправка текстовых сообщений, фото, видео, документов
- ✅ Inline и Reply клавиатуры для взаимодействия
- ✅ Обработка команд и callback-запросов
- ✅ Платежи через Telegram Stars
- ✅ Inline режим для быстрого поиска
- ✅ Чек-листы и подарки (новое в 9.2)
- ✅ Бизнес-аккаунты и прямые сообщения в каналах
- ✅ Stories и предложенные посты

---

## 🔐 Аутентификация

### Получение токена бота

1. Найдите [@BotFather](https://t.me/BotFather) в Telegram
2. Отправьте команду `/newbot`
3. Следуйте инструкциям для создания бота
4. Получите токен вида: `123456789:ABCDefGHIjklMNOpqrsTUVwxyz`

### Формат запросов

Все методы вызываются через URL:

```
https://api.telegram.org/bot<TOKEN>/METHOD_NAME
```

**Пример**:

```python
import httpx

BOT_TOKEN = "123456789:ABCDefGHIjklMNOpqrsTUVwxyz"
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

async def send_message(chat_id: int, text: str):
    url = f"{BASE_URL}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": text
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data)
        return response.json()
```

---

## 📥 Получение обновлений

### Метод 1: Long Polling (getUpdates)

**Рекомендуется для разработки и небольших ботов**

```http
GET /botTOKEN/getUpdates
```

**Параметры**:

| Параметр          | Тип     | Описание                                   |
| ----------------- | ------- | ------------------------------------------ |
| `offset`          | integer | Идентификатор первого возвращаемого update |
| `limit`           | integer | Лимит обновлений (1-100, по умолчанию 100) |
| `timeout`         | integer | Таймаут long polling в секундах (0-50)     |
| `allowed_updates` | array   | Список типов обновлений для получения      |

**Пример**:

```python
async def get_updates(offset: int | None = None):
    url = f"{BASE_URL}/getUpdates"
    params = {
        "offset": offset,
        "timeout": 30,
        "allowed_updates": ["message", "callback_query"]
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        return response.json()

# Основной цикл обработки
offset = None
while True:
    updates = await get_updates(offset)
    for update in updates.get("result", []):
        # Обработать update
        process_update(update)
        offset = update["update_id"] + 1
```

### Метод 2: Webhooks (setWebhook)

**Рекомендуется для production**

```http
POST /botTOKEN/setWebhook
```

**Параметры**:

| Параметр          | Тип     | Описание                                  |
| ----------------- | ------- | ----------------------------------------- |
| `url`             | string  | HTTPS URL для получения обновлений        |
| `certificate`     | file    | SSL сертификат (опционально)              |
| `max_connections` | integer | Максимум одновременных соединений (1-100) |
| `allowed_updates` | array   | Типы обновлений для получения             |
| `secret_token`    | string  | Секретный токен для валидации (1-256)     |

**Пример настройки**:

```python
async def set_webhook(webhook_url: str, secret_token: str):
    url = f"{BASE_URL}/setWebhook"
    data = {
        "url": webhook_url,
        "max_connections": 40,
        "allowed_updates": ["message", "callback_query"],
        "secret_token": secret_token
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data)
        return response.json()

# Пример endpoint для webhook (FastAPI)
from fastapi import FastAPI, Request, Header, HTTPException

app = FastAPI()
SECRET_TOKEN = "your_secret_token_here"

@app.post("/webhook")
async def webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str = Header(None)
):
    # Проверка токена
    if x_telegram_bot_api_secret_token != SECRET_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid token")

    update = await request.json()
    await process_update(update)
    return {"ok": True}
```

### Update объект

```json
{
  "update_id": 123456789,
  "message": {
    "message_id": 1,
    "from": {
      "id": 123456789,
      "is_bot": false,
      "first_name": "John",
      "username": "john_doe"
    },
    "chat": {
      "id": 123456789,
      "type": "private",
      "username": "john_doe"
    },
    "date": 1699876543,
    "text": "/start"
  }
}
```

**Типы обновлений**:

- `message` - новое сообщение
- `edited_message` - отредактированное сообщение
- `callback_query` - нажатие на inline кнопку
- `inline_query` - inline запрос
- `poll` - опрос
- `business_connection` - подключение к бизнес-аккаунту (новое в 9.0)
- `suggested_post_parameters` - параметры предложенного поста (новое в 9.2)

---

## 💬 Отправка сообщений

### sendMessage - Отправка текстового сообщения

```http
POST /botTOKEN/sendMessage
```

**Основные параметры**:

| Параметр                   | Тип     | Описание                                         |
| -------------------------- | ------- | ------------------------------------------------ |
| `chat_id`                  | integer | Идентификатор чата                               |
| `text`                     | string  | Текст сообщения (1-4096 символов)                |
| `parse_mode`               | string  | Режим парсинга: `MarkdownV2`, `HTML`, `Markdown` |
| `disable_notification`     | boolean | Отправить без уведомления                        |
| `protect_content`          | boolean | Запретить пересылку и сохранение                 |
| `reply_parameters`         | object  | Параметры ответа на сообщение                    |
| `reply_markup`             | object  | Inline клавиатура или Reply клавиатура           |
| `direct_messages_topic_id` | integer | ID топика для прямых сообщений в канале (9.2)    |

**Пример**:

```python
async def send_message(
    chat_id: int,
    text: str,
    parse_mode: str = "HTML",
    reply_markup: dict | None = None
):
    url = f"{BASE_URL}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode
    }
    if reply_markup:
        data["reply_markup"] = reply_markup

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data)
        return response.json()

# Использование
await send_message(
    chat_id=123456789,
    text="<b>Привет!</b> Это <i>форматированное</i> сообщение.",
    parse_mode="HTML"
)
```

### sendPhoto - Отправка фото

```http
POST /botTOKEN/sendPhoto
```

**Параметры**:

| Параметр       | Тип     | Описание                        |
| -------------- | ------- | ------------------------------- |
| `chat_id`      | integer | Идентификатор чата              |
| `photo`        | string  | File ID, URL или file_attach    |
| `caption`      | string  | Подпись к фото (0-1024 символа) |
| `parse_mode`   | string  | Режим парсинга для caption      |
| `reply_markup` | object  | Клавиатура                      |

**Пример**:

```python
async def send_photo(
    chat_id: int,
    photo: str | bytes,
    caption: str | None = None
):
    url = f"{BASE_URL}/sendPhoto"

    # Если фото - URL или file_id
    if isinstance(photo, str):
        data = {
            "chat_id": chat_id,
            "photo": photo,
            "caption": caption
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=data)

    # Если фото - файл
    else:
        files = {"photo": photo}
        data = {
            "chat_id": chat_id,
            "caption": caption
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(url, data=data, files=files)

    return response.json()

# Использование с URL
await send_photo(
    chat_id=123456789,
    photo="https://example.com/image.jpg",
    caption="Описание изображения"
)
```

### sendDocument - Отправка документа

```http
POST /botTOKEN/sendDocument
```

**Пример**:

```python
async def send_document(chat_id: int, document_path: str, caption: str | None = None):
    url = f"{BASE_URL}/sendDocument"

    with open(document_path, "rb") as doc:
        files = {"document": doc}
        data = {
            "chat_id": chat_id,
            "caption": caption
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(url, data=data, files=files)

    return response.json()
```

### sendChecklist - Отправка чек-листа (новое в 9.2)

```http
POST /botTOKEN/sendChecklist
```

**Параметры**:

| Параметр       | Тип     | Описание               |
| -------------- | ------- | ---------------------- |
| `chat_id`      | integer | Идентификатор чата     |
| `tasks`        | array   | Список задач чек-листа |
| `reply_markup` | object  | Клавиатура             |

**Пример**:

```python
async def send_checklist(chat_id: int, tasks: list[str]):
    url = f"{BASE_URL}/sendChecklist"
    data = {
        "chat_id": chat_id,
        "tasks": [{"text": task} for task in tasks]
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data)
        return response.json()

# Использование
await send_checklist(
    chat_id=123456789,
    tasks=[
        "Проверить баланс DMarket",
        "Запустить сканирование арбитража",
        "Создать таргеты на топ скины"
    ]
)
```

---

## ✏️ Редактирование сообщений

### editMessageText - Редактировать текст

```http
POST /botTOKEN/editMessageText
```

**Параметры**:

| Параметр       | Тип     | Описание                      |
| -------------- | ------- | ----------------------------- |
| `chat_id`      | integer | Идентификатор чата            |
| `message_id`   | integer | Идентификатор сообщения       |
| `text`         | string  | Новый текст (1-4096 символов) |
| `parse_mode`   | string  | Режим парсинга                |
| `reply_markup` | object  | Новая inline клавиатура       |

**Пример**:

```python
async def edit_message(
    chat_id: int,
    message_id: int,
    new_text: str,
    reply_markup: dict | None = None
):
    url = f"{BASE_URL}/editMessageText"
    data = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": new_text,
        "parse_mode": "HTML"
    }
    if reply_markup:
        data["reply_markup"] = reply_markup

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data)
        return response.json()

# Использование - обновление статуса арбитража
await edit_message(
    chat_id=123456789,
    message_id=42,
    new_text="<b>Арбитраж завершен!</b>\n\n✅ Найдено возможностей: 15\n💰 Потенциальная прибыль: $125.50"
)
```

### deleteMessage - Удалить сообщение

```http
POST /botTOKEN/deleteMessage
```

**Пример**:

```python
async def delete_message(chat_id: int, message_id: int):
    url = f"{BASE_URL}/deleteMessage"
    data = {
        "chat_id": chat_id,
        "message_id": message_id
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data)
        return response.json()
```

---

## ⌨️ Клавиатуры

### Inline клавиатура (InlineKeyboardMarkup)

Кнопки, прикрепленные к сообщению с callback данными.

**Структура**:

```python
{
    "inline_keyboard": [
        [  # Первый ряд
            {"text": "Кнопка 1", "callback_data": "button_1"},
            {"text": "Кнопка 2", "callback_data": "button_2"}
        ],
        [  # Второй ряд
            {"text": "URL кнопка", "url": "https://example.com"}
        ]
    ]
}
```

**Пример для DMarket бота**:

```python
def create_arbitrage_keyboard():
    """Создать клавиатуру для управления арбитражем."""
    return {
        "inline_keyboard": [
            [
                {"text": "🎯 Разгон баланса", "callback_data": "arb_boost"},
                {"text": "⭐ Стандарт", "callback_data": "arb_standard"}
            ],
            [
                {"text": "💰 Средний", "callback_data": "arb_medium"},
                {"text": "💎 Продвинутый", "callback_data": "arb_advanced"}
            ],
            [
                {"text": "🏆 Профессионал", "callback_data": "arb_pro"}
            ],
            [
                {"text": "❌ Отмена", "callback_data": "cancel"}
            ]
        ]
    }

# Использование
await send_message(
    chat_id=123456789,
    text="Выберите уровень арбитража:",
    reply_markup=create_arbitrage_keyboard()
)
```

**Обработка callback query**:

```python
async def handle_callback_query(callback_query: dict):
    """Обработать нажатие на inline кнопку."""
    query_id = callback_query["id"]
    chat_id = callback_query["message"]["chat"]["id"]
    message_id = callback_query["message"]["message_id"]
    data = callback_query["data"]

    # Подтвердить нажатие
    await answer_callback_query(query_id)

    # Обработать данные
    if data.startswith("arb_"):
        level = data.replace("arb_", "")
        await edit_message(
            chat_id=chat_id,
            message_id=message_id,
            new_text=f"Запускаю арбитраж уровня: {level}..."
        )
        # Запустить сканирование
        await start_arbitrage_scan(chat_id, level)

async def answer_callback_query(callback_query_id: str, text: str | None = None):
    """Подтвердить callback query."""
    url = f"{BASE_URL}/answerCallbackQuery"
    data = {"callback_query_id": callback_query_id}
    if text:
        data["text"] = text

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data)
        return response.json()
```

### Reply клавиатура (ReplyKeyboardMarkup)

Кнопки, заменяющие стандартную клавиатуру.

**Структура**:

```python
{
    "keyboard": [
        [{"text": "💰 Баланс"}, {"text": "🎯 Арбитраж"}],
        [{"text": "📊 Статистика"}, {"text": "⚙️ Настройки"}]
    ],
    "resize_keyboard": True,
    "one_time_keyboard": False
}
```

**Пример**:

```python
def create_main_menu_keyboard():
    """Создать главное меню бота."""
    return {
        "keyboard": [
            [{"text": "💰 Баланс DMarket"}, {"text": "🎯 Арбитраж"}],
            [{"text": "📦 Таргеты"}, {"text": "📊 История"}],
            [{"text": "⚙️ Настройки"}, {"text": "❓ Помощь"}]
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False
    }

# Отправить с Reply клавиатурой
await send_message(
    chat_id=123456789,
    text="Главное меню:",
    reply_markup=create_main_menu_keyboard()
)
```

**Удалить Reply клавиатуру**:

```python
await send_message(
    chat_id=123456789,
    text="Клавиатура удалена",
    reply_markup={"remove_keyboard": True}
)
```

---

## 📁 Медиа и файлы

### Отправка нескольких файлов (sendMediaGroup)

```http
POST /botTOKEN/sendMediaGroup
```

**Пример**:

```python
async def send_media_group(chat_id: int, media: list[dict]):
    """Отправить группу медиа (фото/видео)."""
    url = f"{BASE_URL}/sendMediaGroup"
    data = {
        "chat_id": chat_id,
        "media": media
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data)
        return response.json()

# Пример: отправка графиков арбитража
media_group = [
    {
        "type": "photo",
        "media": "https://example.com/chart1.png",
        "caption": "График цен за неделю"
    },
    {
        "type": "photo",
        "media": "https://example.com/chart2.png",
        "caption": "Прибыль по дням"
    }
]

await send_media_group(chat_id=123456789, media=media_group)
```

### Получение информации о файле

```python
async def get_file(file_id: str):
    """Получить информацию о файле."""
    url = f"{BASE_URL}/getFile"
    params = {"file_id": file_id}

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        result = response.json()

    if result.get("ok"):
        file_path = result["result"]["file_path"]
        file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
        return file_url
```

---

## 💳 Платежи (Telegram Stars)

### Обзор

Telegram Stars - встроенная валюта для платежей в боте. Пользователи могут покупать Stars и тратить их на подписки, услуги или контент.

### sendInvoice - Отправка счета

```http
POST /botTOKEN/sendInvoice
```

**Основные параметры**:

| Параметр      | Тип     | Описание                        |
| ------------- | ------- | ------------------------------- |
| `chat_id`     | integer | Идентификатор чата              |
| `title`       | string  | Название товара                 |
| `description` | string  | Описание товара                 |
| `payload`     | string  | Внутренние данные (до 128 байт) |
| `currency`    | string  | Валюта: `XTR` (Telegram Stars)  |
| `prices`      | array   | Список цен                      |

**Пример**:

```python
async def send_invoice(chat_id: int, title: str, description: str, amount: int):
    """Отправить счет на оплату."""
    url = f"{BASE_URL}/sendInvoice"
    data = {
        "chat_id": chat_id,
        "title": title,
        "description": description,
        "payload": f"premium_subscription_{chat_id}",
        "currency": "XTR",
        "prices": [{"label": title, "amount": amount}]
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data)
        return response.json()

# Пример: подписка на автоматический арбитраж
await send_invoice(
    chat_id=123456789,
    title="Premium подписка - 1 месяц",
    description="Автоматический арбитраж 24/7, приоритетная поддержка",
    amount=100  # 100 Stars
)
```

### Обработка успешного платежа

```python
async def handle_successful_payment(message: dict):
    """Обработать успешный платеж."""
    payment = message.get("successful_payment")
    if not payment:
        return

    user_id = message["from"]["id"]
    currency = payment["currency"]
    total_amount = payment["total_amount"]
    payload = payment["invoice_payload"]

    # Активировать подписку
    await activate_premium_subscription(user_id, payload)

    # Отправить подтверждение
    await send_message(
        chat_id=user_id,
        text=f"✅ Платеж на {total_amount} {currency} успешно обработан!\n\n"
             f"Premium подписка активирована."
    )
```

### getStarTransactions - История транзакций (новое в 9.0)

```http
GET /botTOKEN/getStarTransactions
```

**Пример**:

```python
async def get_star_transactions(offset: int = 0, limit: int = 100):
    """Получить историю транзакций Telegram Stars."""
    url = f"{BASE_URL}/getStarTransactions"
    params = {"offset": offset, "limit": limit}

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        return response.json()
```

---

## 🔍 Inline режим

### Активация inline режима

1. Отправьте [@BotFather](https://t.me/BotFather) команду `/setinline`
2. Выберите бота
3. Введите placeholder текст (например: "Поиск предметов DMarket...")

### answerInlineQuery - Ответить на inline запрос

```http
POST /botTOKEN/answerInlineQuery
```

**Пример для поиска предметов**:

```python
async def answer_inline_query(inline_query_id: str, results: list[dict]):
    """Ответить на inline запрос."""
    url = f"{BASE_URL}/answerInlineQuery"
    data = {
        "inline_query_id": inline_query_id,
        "results": results,
        "cache_time": 30
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data)
        return response.json()

async def handle_inline_query(inline_query: dict):
    """Обработать inline запрос."""
    query_id = inline_query["id"]
    query_text = inline_query["query"]

    # Поиск предметов на DMarket
    items = await search_dmarket_items(query_text)

    # Сформировать результаты
    results = []
    for idx, item in enumerate(items[:50]):
        results.append({
            "type": "article",
            "id": str(idx),
            "title": item["title"],
            "description": f"Цена: ${item['price']} | Прибыль: {item['profit_percent']:.1f}%",
            "input_message_content": {
                "message_text": f"<b>{item['title']}</b>\n\n"
                                f"💰 Цена покупки: ${item['buy_price']}\n"
                                f"💵 Цена продажи: ${item['sell_price']}\n"
                                f"📈 Прибыль: ${item['profit']} ({item['profit_percent']:.1f}%)",
                "parse_mode": "HTML"
            },
            "reply_markup": {
                "inline_keyboard": [[
                    {"text": "🛒 Купить", "callback_data": f"buy_{item['id']}"}
                ]]
            }
        })

    await answer_inline_query(query_id, results)
```

---

## 🎨 Форматирование текста

### HTML разметка (рекомендуется)

```python
text = """
<b>Жирный текст</b>
<i>Курсив</i>
<u>Подчеркнутый</u>
<s>Зачеркнутый</s>
<code>Моноширинный код</code>
<pre language="python">
# Блок кода
def hello():
    print("Hello!")
</pre>
<a href="https://example.com">Ссылка</a>
<tg-emoji emoji-id="12345">🔥</tg-emoji>
"""

await send_message(chat_id=123456789, text=text, parse_mode="HTML")
```

### MarkdownV2 разметка

```python
text = r"""
*Жирный текст*
_Курсив_
__Подчеркнутый__
~Зачеркнутый~
`Моноширинный код`
```python
# Блок кода
def hello():
    print("Hello!")
```

[Ссылка](https://example\.com)
"""

await send_message(chat_id=123456789, text=text, parse_mode="MarkdownV2")

```

**Важно для MarkdownV2**: Экранируйте специальные символы: `_`, `*`, `[`, `]`, `(`, `)`, `~`, `` ` ``, `>`, `#`, `+`, `-`, `=`, `|`, `{`, `}`, `.`, `!`

---

## 🆕 Новые функции Bot API 9.2 (15 августа 2025)

### 1. Чек-листы

Создание и управление задачами в чате:

```python
# Отправка чек-листа
await send_checklist(
    chat_id=123456789,
    tasks=[
        "Проверить баланс DMarket",
        "Запустить сканирование",
        "Создать таргеты"
    ]
)

# Редактирование чек-листа
async def edit_checklist(chat_id: int, message_id: int, tasks: list[dict]):
    url = f"{BASE_URL}/editMessageChecklist"
    data = {
        "chat_id": chat_id,
        "message_id": message_id,
        "tasks": tasks
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data)
        return response.json()
```

### 2. Прямые сообщения в каналах

Отправка сообщений в определенный топик канала:

```python
await send_message(
    chat_id=-1001234567890,  # ID канала
    text="Уведомление о новых арбитражных возможностях",
    direct_messages_topic_id=123  # ID топика
)
```

### 3. Предложенные посты

Работа с предложенными постами в каналах:

```python
async def approve_suggested_post(chat_id: int, post_id: int):
    """Одобрить предложенный пост."""
    url = f"{BASE_URL}/approveSuggestedPost"
    data = {
        "chat_id": chat_id,
        "post_id": post_id
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data)
        return response.json()

async def decline_suggested_post(chat_id: int, post_id: int):
    """Отклонить предложенный пост."""
    url = f"{BASE_URL}/declineSuggestedPost"
    data = {
        "chat_id": chat_id,
        "post_id": post_id
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data)
        return response.json()
```

### 4. Подарки

Отправка и управление подарками:

```python
async def send_gift(user_id: int, gift_id: str):
    """Отправить подарок пользователю."""
    url = f"{BASE_URL}/sendGift"
    data = {
        "user_id": user_id,
        "gift_id": gift_id
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data)
        return response.json()
```

---

## 🆕 Функции Bot API 9.0 (11 апреля 2025)

### Бизнес-аккаунты

Управление бизнес-аккаунтом через бота:

```python
async def set_business_account_name(name: str):
    """Установить название бизнес-аккаунта."""
    url = f"{BASE_URL}/setBusinessAccountName"
    data = {"name": name}
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data)
        return response.json()

async def get_business_account_star_balance():
    """Получить баланс Stars бизнес-аккаунта."""
    url = f"{BASE_URL}/getBusinessAccountStarBalance"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()

async def transfer_business_account_stars(user_id: int, amount: int):
    """Перевести Stars пользователю."""
    url = f"{BASE_URL}/transferBusinessAccountStars"
    data = {
        "user_id": user_id,
        "amount": amount
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data)
        return response.json()
```

### Stories

Публикация историй от имени бота:

```python
async def post_story(media: dict):
    """Опубликовать историю."""
    url = f"{BASE_URL}/postStory"
    data = {"media": media}
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data)
        return response.json()

# Пример публикации фото-истории
await post_story(
    media={
        "type": "photo",
        "media": "https://example.com/arbitrage_results.png"
    }
)
```

---

## ⚠️ Обработка ошибок

### Формат ошибки

```json
{
  "ok": false,
  "error_code": 400,
  "description": "Bad Request: message text is empty"
}
```

### Основные коды ошибок

| Код | Описание              | Решение                          |
| --- | --------------------- | -------------------------------- |
| 400 | Bad Request           | Проверить параметры запроса      |
| 401 | Unauthorized          | Проверить токен бота             |
| 403 | Forbidden             | Бот заблокирован пользователем   |
| 404 | Not Found             | Неверный метод или чат не найден |
| 429 | Too Many Requests     | Снизить частоту запросов         |
| 500 | Internal Server Error | Повторить запрос позже           |

### Обработка ошибок в коде

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def send_message_with_retry(chat_id: int, text: str):
    """Отправить сообщение с повторными попытками."""
    try:
        result = await send_message(chat_id, text)
        if not result.get("ok"):
            error_code = result.get("error_code")
            description = result.get("description")

            if error_code == 403:
                # Пользователь заблокировал бота
                logger.warning(f"Bot blocked by user {chat_id}")
                return None
            elif error_code == 429:
                # Rate limit
                retry_after = result.get("parameters", {}).get("retry_after", 60)
                await asyncio.sleep(retry_after)
                raise Exception("Rate limit exceeded")
            else:
                logger.error(f"Telegram API error: {error_code} - {description}")
                raise Exception(description)

        return result

    except httpx.HTTPError as e:
        logger.error(f"HTTP error: {e}")
        raise
```

---

## 🔄 Лучшие практики

### 1. Используйте асинхронность

```python
import asyncio
from telegram.ext import Application

# Инициализация
application = Application.builder().token(BOT_TOKEN).build()

# Асинхронные обработчики
async def start_command(update, context):
    await update.message.reply_text("Привет!")

# Регистрация
application.add_handler(CommandHandler("start", start_command))

# Запуск
application.run_polling()
```

### 2. Обрабатывайте все типы обновлений

```python
async def process_update(update: dict):
    """Централизованная обработка обновлений."""
    if "message" in update:
        await handle_message(update["message"])
    elif "callback_query" in update:
        await handle_callback_query(update["callback_query"])
    elif "inline_query" in update:
        await handle_inline_query(update["inline_query"])
    elif "business_connection" in update:
        await handle_business_connection(update["business_connection"])
```

### 3. Используйте контекст для хранения состояния

```python
from collections import defaultdict

user_states = defaultdict(dict)

async def handle_message(message: dict):
    user_id = message["from"]["id"]
    text = message.get("text", "")

    # Получить текущее состояние
    state = user_states[user_id].get("state")

    if state == "waiting_for_price":
        # Обработать ввод цены
        price = float(text)
        await process_price(user_id, price)
        user_states[user_id]["state"] = None
    elif text.startswith("/create_target"):
        # Начать процесс создания таргета
        user_states[user_id]["state"] = "waiting_for_price"
        await send_message(user_id, "Введите цену таргета:")
```

### 4. Валидируйте данные пользователя

```python
async def handle_price_input(user_id: int, text: str):
    """Обработать ввод цены с валидацией."""
    try:
        price = float(text)
        if not 0.01 <= price <= 10000:
            await send_message(
                user_id,
                "❌ Цена должна быть от $0.01 до $10,000"
            )
            return

        # Продолжить обработку
        await create_target_with_price(user_id, price)

    except ValueError:
        await send_message(
            user_id,
            "❌ Неверный формат цены. Используйте: 10.50"
        )
```

### 5. Логируйте активность

```python
import structlog

logger = structlog.get_logger(__name__)

async def handle_command(update: dict):
    """Обработать команду с логированием."""
    message = update.get("message", {})
    user_id = message.get("from", {}).get("id")
    text = message.get("text", "")

    logger.info(
        "command_received",
        user_id=user_id,
        command=text,
        chat_type=message.get("chat", {}).get("type")
    )

    # Обработка команды
    # ...
```

---

## 📚 Дополнительные ресурсы

- **Официальная документация**: <https://core.telegram.org/bots/api>
- **Telegram Bot API Updates**: <https://core.telegram.org/bots/api-changelog>
- **FAQ**: <https://core.telegram.org/bots/faq>
- **python-telegram-bot библиотека**: <https://python-telegram-bot.org/>
- **Примеры ботов**: <https://github.com/python-telegram-bot/python-telegram-bot/tree/master/examples>

---

## 📝 Примеры интеграции с DMarket ботом

### Пример 1: Уведомление о новых арбитражных возможностях

```python
async def notify_arbitrage_opportunity(user_id: int, opportunity: dict):
    """Уведомить пользователя о новой возможности."""

    text = f"""
🎯 <b>Новая арбитражная возможность!</b>

📦 Предмет: {opportunity['title']}
💰 Купить за: ${opportunity['buy_price']:.2f}
💵 Продать за: ${opportunity['sell_price']:.2f}
📈 Прибыль: ${opportunity['profit']:.2f} ({opportunity['profit_percent']:.1f}%)
⚡ Ликвидность: {opportunity['liquidity']}
    """

    keyboard = {
        "inline_keyboard": [
            [
                {"text": "🛒 Купить сейчас", "callback_data": f"buy_{opportunity['id']}"},
                {"text": "📊 Подробнее", "callback_data": f"details_{opportunity['id']}"}
            ],
            [
                {"text": "🎯 Создать таргет", "callback_data": f"target_{opportunity['id']}"}
            ]
        ]
    }

    await send_message(
        chat_id=user_id,
        text=text,
        parse_mode="HTML",
        reply_markup=keyboard
    )
```

### Пример 2: Отчет о результатах арбитража

```python
async def send_arbitrage_report(user_id: int, results: dict):
    """Отправить отчет о результатах арбитража."""

    # Создать график
    chart_url = await generate_profit_chart(results)

    # Отправить фото с графиком
    caption = f"""
📊 <b>Отчет о результатах арбитража</b>

📅 Период: {results['period']}
💰 Всего сделок: {results['total_deals']}
✅ Успешных: {results['successful']} ({results['success_rate']:.1f}%)
📈 Общая прибыль: ${results['total_profit']:.2f}
💵 Средняя прибыль: ${results['avg_profit']:.2f}
    """

    await send_photo(
        chat_id=user_id,
        photo=chart_url,
        caption=caption
    )
```

### Пример 3: Интерактивное создание таргета

```python
async def start_target_creation(user_id: int, item_title: str):
    """Начать процесс создания таргета."""

    # Получить текущие цены
    prices = await get_aggregated_prices(item_title)
    best_offer = prices['offerBestPrice'] / 100

    text = f"""
🎯 <b>Создание таргета</b>

📦 Предмет: {item_title}
💵 Текущая лучшая цена: ${best_offer:.2f}

Введите желаемую цену покупки:
    """

    # Сохранить состояние
    user_states[user_id] = {
        "state": "waiting_for_target_price",
        "item_title": item_title,
        "best_offer": best_offer
    }

    keyboard = {
        "inline_keyboard": [
            [
                {"text": f"-5% (${best_offer * 0.95:.2f})", "callback_data": f"target_price_{best_offer * 0.95}"},
                {"text": f"-10% (${best_offer * 0.90:.2f})", "callback_data": f"target_price_{best_offer * 0.90}"}
            ],
            [
                {"text": "❌ Отмена", "callback_data": "cancel_target"}
            ]
        ]
    }

    await send_message(
        chat_id=user_id,
        text=text,
        parse_mode="HTML",
        reply_markup=keyboard
    )
```

---

**Документация актуальна на 17 декабря 2025 г. Всегда проверяйте официальную документацию Telegram для получения последних обновлений Bot API.**
