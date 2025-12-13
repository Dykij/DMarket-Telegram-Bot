# AGENTS.md — Telegram Bot Module

> Специфичные инструкции для работы с Telegram Bot модулем.
> Общие правила: см. корневой `/AGENTS.md`

## 🤖 Структура модуля

```
telegram_bot/
├── handlers/           # 21 обработчик команд
│   ├── commands.py           # /start, /help, /balance
│   ├── scanner_handler.py    # Арбитраж UI
│   ├── target_handler.py     # Таргеты
│   ├── dashboard_handler.py  # Главное меню
│   └── callbacks.py          # Callback queries
├── keyboards.py        # Inline клавиатуры
├── localization.py     # i18n (RU, EN, ES, DE)
├── notifier.py         # Push-уведомления
└── pagination.py       # Пагинация результатов
```

## 📋 Конвенции

### Callback Data Format
```python
# Формат: action:param1:param2
# Максимум: 64 байта!

callback_data = "scan:standard:csgo"
callback_data = "target:create:a8db"
callback_data = "page:3:results"

# ❌ Слишком длинный (>64 bytes)
callback_data = "very_long_action_name:with:many:parameters:that:exceed:limit"
```

### Handler Structure
```python
from telegram import Update
from telegram.ext import ContextTypes

async def my_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Описание команды."""
    user_id = update.effective_user.id

    # Проверка доступа (если нужно)
    if not await is_allowed(user_id):
        await update.message.reply_text("❌ Нет доступа")
        return

    # Логика команды
    result = await process_something()

    # Ответ пользователю
    await update.message.reply_text(
        format_result(result),
        reply_markup=get_keyboard()
    )
```

### Inline Keyboards
```python
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def get_main_keyboard() -> InlineKeyboardMarkup:
    """Главная клавиатура."""
    keyboard = [
        [
            InlineKeyboardButton("🔍 Сканер", callback_data="scanner:menu"),
            InlineKeyboardButton("🎯 Таргеты", callback_data="targets:menu"),
        ],
        [
            InlineKeyboardButton("💰 Баланс", callback_data="balance:show"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)
```

## 🌐 Локализация

### Добавление нового ключа
```python
# localization.py
TRANSLATIONS = {
    "new_feature_title": {
        "ru": "Новая функция",
        "en": "New Feature",
        "es": "Nueva función",
        "de": "Neue Funktion",
    },
    # ... другие ключи
}
```

### Использование
```python
from .localization import get_text

async def my_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_lang = get_user_language(update.effective_user.id)  # 'ru', 'en', etc.

    text = get_text("new_feature_title", user_lang)
    await update.message.reply_text(text)
```

### ⚠️ Всегда добавляй ВСЕ 4 языка!
```python
# ❌ Неправильно - только русский
"key": {"ru": "Текст"}

# ✅ Правильно - все языки
"key": {
    "ru": "Текст",
    "en": "Text",
    "es": "Texto",
    "de": "Text",
}
```

## ⚡ Rate Limiting для команд

```python
from collections import defaultdict
from datetime import datetime, timedelta

class CommandRateLimiter:
    def __init__(self, max_calls: int = 5, period: int = 60):
        self.max_calls = max_calls
        self.period = period
        self.calls = defaultdict(list)

    async def is_allowed(self, user_id: int) -> bool:
        now = datetime.now()
        cutoff = now - timedelta(seconds=self.period)

        self.calls[user_id] = [t for t in self.calls[user_id] if t > cutoff]

        if len(self.calls[user_id]) >= self.max_calls:
            return False

        self.calls[user_id].append(now)
        return True
```

## 📱 Типичные паттерны

### Пагинация результатов
```python
from .pagination import Paginator

async def show_results(update: Update, items: list, page: int = 1):
    paginator = Paginator(items, page_size=10)
    page_items = paginator.get_page(page)

    text = format_items(page_items)
    keyboard = paginator.get_keyboard(page, callback_prefix="results")

    await update.message.reply_text(text, reply_markup=keyboard)
```

### Callback Query обработка
```python
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # Обязательно! Убирает "часики"

    action, *params = query.data.split(":")

    match action:
        case "scan":
            await handle_scan(query, params)
        case "target":
            await handle_target(query, params)
        case _:
            await query.edit_message_text("❌ Неизвестное действие")
```

## 🧪 Тестирование

```python
import pytest
from unittest.mock import AsyncMock, MagicMock

@pytest.mark.asyncio
async def test_start_command():
    # Arrange
    update = MagicMock()
    update.effective_user.id = 123456
    update.message.reply_text = AsyncMock()
    context = MagicMock()

    # Act
    await start_command(update, context)

    # Assert
    update.message.reply_text.assert_called_once()
    call_args = update.message.reply_text.call_args
    assert "Добро пожаловать" in call_args[0][0] or "Welcome" in call_args[0][0]
```

## ⚠️ Типичные ошибки

1. **Забыл `await query.answer()`** — "часики" крутятся вечно
2. **Callback data > 64 bytes** — Telegram отклонит
3. **Не все языки в локализации** — KeyError в production
4. **Синхронный код в handlers** — блокировка бота

---

*См. также: `docs/TELEGRAM_BOT_API.md` для полной документации*
