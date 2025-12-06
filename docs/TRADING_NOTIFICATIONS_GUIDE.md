# Руководство по торговым уведомлениям

**Дата**: 19 ноября 2025 г.
**Версия**: 1.0

---

## 📋 Обзор

Система торговых уведомлений предоставляет пользователям полную информацию о каждой торговой операции через Telegram бота с возможностью ручного контроля.

### Основные возможности

- ✅ **Уведомления о намерении покупки** - перед каждой покупкой с деталями о цене и прибыли
- ✅ **Уведомления об успешной покупке** - подтверждение с номером заказа
- ✅ **Уведомления об ошибках покупки** - информация о причине неудачи
- ✅ **Уведомления об успешной продаже** - подтверждение с расчетом прибыли
- ✅ **Кнопка отмены** - возможность отменить покупку до её выполнения
- ✅ **Индикатор DRY-RUN** - четкое отображение тестового режима

---

## 🎯 Типы уведомлений

### 1. Buy Intent Notification (Намерение купить)

Отправляется **перед** покупкой предмета для информирования пользователя и предоставления возможности отмены.

**Пример сообщения:**
```
🛒 НАМЕРЕНИЕ КУПИТЬ [DRY-RUN]

📦 Предмет: AK-47 | Redline (Field-Tested)
💵 Цена покупки: $8.50
💰 Цена продажи: $9.20
📈 Прибыль: $0.52 (6.1%)
🔍 Источник: arbitrage_scanner

[Отменить покупку] <- inline кнопка
```

**Параметры:**
```python
await send_buy_intent_notification(
    bot=bot,
    user_id=123456789,
    item_name="AK-47 | Redline (Field-Tested)",
    buy_price=8.50,
    sell_price=9.20,
    profit_usd=0.52,
    profit_percent=6.1,
    source="arbitrage_scanner",
    dry_run=True,
    notification_queue=queue,
    item_id="item_12345"
)
```

### 2. Buy Success Notification (Успешная покупка)

Отправляется **после** успешной покупки предмета.

**Пример сообщения:**
```
✅ ПОКУПКА ВЫПОЛНЕНА [DRY-RUN]

📦 Предмет: AK-47 | Redline (Field-Tested)
💵 Цена покупки: $8.50
💰 Выставлено на продажу: $9.20
📋 Order ID: order_67890

[Просмотреть на DMarket] <- inline кнопка
```

**Параметры:**
```python
await send_buy_success_notification(
    bot=bot,
    user_id=123456789,
    item_name="AK-47 | Redline (Field-Tested)",
    buy_price=8.50,
    sell_price=9.20,
    order_id="order_67890",
    dry_run=True,
    notification_queue=queue
)
```

### 3. Buy Failed Notification (Ошибка покупки)

Отправляется при неудачной попытке покупки.

**Пример сообщения:**
```
❌ ОШИБКА ПОКУПКИ [LIVE]

📦 Предмет: AK-47 | Redline (Field-Tested)
💵 Цена: $8.50
⚠️ Причина: Insufficient balance
```

**Параметры:**
```python
await send_buy_failed_notification(
    bot=bot,
    user_id=123456789,
    item_name="AK-47 | Redline (Field-Tested)",
    buy_price=8.50,
    error_reason="Insufficient balance",
    dry_run=False,
    notification_queue=queue
)
```

### 4. Sell Success Notification (Успешная продажа)

Отправляется после успешной продажи предмета.

**Пример сообщения:**
```
💰 ПРОДАЖА ВЫПОЛНЕНА [DRY-RUN]

📦 Предмет: AK-47 | Redline (Field-Tested)
💵 Цена покупки: $8.50
💰 Цена продажи: $9.20
📈 Прибыль: $0.52 (6.1%)
```

**Параметры:**
```python
await send_sell_success_notification(
    bot=bot,
    user_id=123456789,
    item_name="AK-47 | Redline (Field-Tested)",
    buy_price=8.50,
    sell_price=9.20,
    profit_usd=0.52,
    profit_percent=6.1,
    dry_run=True,
    notification_queue=queue
)
```

---

## 🔧 Использование TradingNotifier

### Базовое использование

```python
from src.utils.trading_notifier import TradingNotifier
from src.dmarket.dmarket_api import DMarketAPI
from telegram import Bot

# Инициализация компонентов
api = DMarketAPI(public_key, secret_key)
bot = Bot(token=bot_token)
notification_queue = NotificationQueue()

# Создание TradingNotifier
trading_notifier = TradingNotifier(
    api_client=api,
    bot=bot,
    notification_queue=notification_queue,
    user_id=123456789
)

# Покупка с уведомлениями
result = await trading_notifier.buy_item_with_notifications(
    item_id="item_12345",
    item_name="AK-47 | Redline (Field-Tested)",
    buy_price=8.50,
    sell_price=9.20,
    profit_usd=0.52,
    profit_percent=6.1,
    source="arbitrage_scanner"
)

# Проверка результата
if result.get("success"):
    print(f"Покупка успешна! Order ID: {result.get('order_id')}")
else:
    print(f"Ошибка: {result.get('error')}")
```

### Интеграция с ArbitrageScanner

```python
from src.dmarket.arbitrage_scanner import ArbitrageScanner
from src.utils.trading_notifier import TradingNotifier

async def scan_and_trade(user_id: int):
    """Сканировать арбитраж и автоматически покупать с уведомлениями."""

    # Инициализация
    scanner = ArbitrageScanner(api_client=api)
    trading_notifier = TradingNotifier(
        api_client=api,
        bot=bot,
        notification_queue=notification_queue,
        user_id=user_id
    )

    # Найти возможности
    opportunities = await scanner.scan_level(
        level="standard",
        game="csgo"
    )

    # Купить лучшие возможности
    for opp in opportunities[:3]:  # Топ-3
        result = await trading_notifier.buy_item_with_notifications(
            item_id=opp["item_id"],
            item_name=opp["title"],
            buy_price=opp["buy_price"],
            sell_price=opp["sell_price"],
            profit_usd=opp["profit"],
            profit_percent=opp["profit_percent"],
            source="arbitrage_scanner"
        )

        # Задержка между покупками
        await asyncio.sleep(2)
```

### Использование helper-функции

```python
from src.utils.trading_notifier import buy_with_notifications

# Упрощенная покупка через helper
result = await buy_with_notifications(
    api_client=api,
    bot=bot,
    notification_queue=notification_queue,
    user_id=123456789,
    item_id="item_12345",
    item_name="AK-47 | Redline (Field-Tested)",
    buy_price=8.50,
    sell_price=9.20,
    profit_usd=0.52,
    profit_percent=6.1,
    source="manual_purchase"
)
```

---

## 🎮 Callback-обработчики

### Отмена покупки

Когда пользователь нажимает кнопку "Отменить покупку", вызывается `handle_buy_cancel_callback`:

```python
async def handle_buy_cancel_callback(update, context):
    """Обработать отмену покупки."""
    query = update.callback_query
    callback_data = query.data

    if callback_data.startswith("cancel_buy:"):
        item_id = callback_data.split(":", 1)[1]

        # Логирование отмены
        logger.info(f"Пользователь отменил покупку предмета {item_id}")

        # Уведомление пользователя
        await query.answer("Покупка отменена")
        await query.edit_message_text(
            text=query.message.text + "\n\n❌ *ОТМЕНЕНО ПОЛЬЗОВАТЕЛЕМ*",
            parse_mode="Markdown"
        )
```

### Регистрация обработчиков

Обработчики автоматически регистрируются при вызове `register_notification_handlers`:

```python
from src.telegram_bot.notifier import register_notification_handlers

# В main.py
application = Application.builder().token(token).build()
await register_notification_handlers(application)
```

---

## ⚙️ Конфигурация

### DRY-RUN режим

По умолчанию бот работает в **DRY-RUN** режиме для безопасности:

```python
# В .env
DRY_RUN=true  # Безопасный режим (по умолчанию)
# DRY_RUN=false  # Реальная торговля (ОПАСНО!)
```

**Важно:** Индикатор `[DRY-RUN]` или `[LIVE]` всегда отображается в уведомлениях.

### Настройка NotificationQueue

```python
from src.telegram_bot.notifier import NotificationQueue, Priority

queue = NotificationQueue()

# Торговые уведомления имеют высокий приоритет
await queue.put(
    notification_func,
    priority=Priority.HIGH  # Отправляются первыми
)
```

---

## 📊 Примеры использования

### Пример 1: Простая покупка

```python
from src.utils.trading_notifier import TradingNotifier

async def simple_purchase():
    notifier = TradingNotifier(api, bot, queue, user_id=123)

    result = await notifier.buy_item_with_notifications(
        item_id="abc123",
        item_name="AWP | Asiimov (Field-Tested)",
        buy_price=50.00,
        sell_price=55.00,
        profit_usd=3.65,  # После комиссии 7%
        profit_percent=7.3,
        source="manual"
    )

    return result
```

### Пример 2: Batch-покупка

```python
async def batch_purchase(items_list):
    """Купить несколько предметов с уведомлениями."""
    notifier = TradingNotifier(api, bot, queue, user_id=123)
    results = []

    for item in items_list:
        result = await notifier.buy_item_with_notifications(
            item_id=item["id"],
            item_name=item["name"],
            buy_price=item["buy_price"],
            sell_price=item["sell_price"],
            profit_usd=item["profit"],
            profit_percent=item["profit_percent"],
            source="batch_scanner"
        )
        results.append(result)

        # Задержка для избежания rate limit
        await asyncio.sleep(3)

    return results
```

### Пример 3: Продажа с уведомлением

```python
async def sell_with_notification(item_id, item_name, buy_price, sell_price):
    """Продать предмет с уведомлением."""
    notifier = TradingNotifier(api, bot, queue, user_id=123)

    result = await notifier.sell_item_with_notifications(
        item_id=item_id,
        item_name=item_name,
        buy_price=buy_price,
        sell_price=sell_price
    )

    return result
```

---

## 🔒 Безопасность

### Рекомендации

1. **Всегда начинайте с DRY-RUN=true**
2. **Тестируйте 48-72 часа** перед переключением на реальную торговлю
3. **Проверяйте логи** на наличие ошибок
4. **Устанавливайте лимиты** на количество покупок в день
5. **Используйте кнопку отмены** для контроля

### Мониторинг

```python
import structlog

logger = structlog.get_logger(__name__)

# Все операции логируются
logger.info(
    "buy_intent_notification_sent",
    user_id=user_id,
    item_id=item_id,
    buy_price=buy_price,
    dry_run=dry_run
)
```

---

## 🐛 Отладка

### Проверка уведомлений

```python
# Включить DEBUG логирование
import logging
logging.basicConfig(level=logging.DEBUG)

# Проверить отправку уведомления
await send_buy_intent_notification(
    bot=bot,
    user_id=YOUR_USER_ID,
    item_name="Test Item",
    buy_price=10.0,
    sell_price=11.0,
    profit_usd=0.30,
    profit_percent=3.0,
    source="test",
    dry_run=True,
    notification_queue=queue,
    item_id="test_123"
)
```

### Частые проблемы

**Проблема**: Уведомления не приходят
- **Решение**: Проверьте `user_id`, убедитесь что бот запущен

**Проблема**: Кнопка отмены не работает
- **Решение**: Убедитесь что `register_notification_handlers` вызван

**Проблема**: DRY-RUN не отображается
- **Решение**: Проверьте параметр `dry_run` в функции

---

## 📚 API Reference

### send_buy_intent_notification

```python
async def send_buy_intent_notification(
    bot: Bot,
    user_id: int,
    item_name: str,
    buy_price: float,
    sell_price: float,
    profit_usd: float,
    profit_percent: float,
    source: str,
    dry_run: bool,
    notification_queue: NotificationQueue,
    item_id: str,
) -> None:
    """Отправить уведомление о намерении купить предмет.

    Args:
        bot: Telegram Bot instance
        user_id: ID пользователя Telegram
        item_name: Название предмета
        buy_price: Цена покупки (USD)
        sell_price: Цена продажи (USD)
        profit_usd: Прибыль в USD
        profit_percent: Прибыль в процентах
        source: Источник (arbitrage_scanner, manual, etc.)
        dry_run: Тестовый режим (True) или реальная торговля (False)
        notification_queue: Очередь уведомлений
        item_id: ID предмета для отмены покупки
    """
```

### TradingNotifier.buy_item_with_notifications

```python
async def buy_item_with_notifications(
    self,
    item_id: str,
    item_name: str,
    buy_price: float,
    sell_price: float,
    profit_usd: float,
    profit_percent: float,
    source: str = "arbitrage_scanner",
) -> dict[str, Any]:
    """Купить предмет с отправкой уведомлений.

    Args:
        item_id: ID предмета
        item_name: Название предмета
        buy_price: Цена покупки
        sell_price: Цена продажи
        profit_usd: Прибыль в USD
        profit_percent: Прибыль в процентах
        source: Источник операции

    Returns:
        Результат покупки от DMarketAPI
    """
```

---

## 📝 Changelog

### v1.0 (19 ноября 2025)
- ✅ Добавлены 4 типа уведомлений
- ✅ Реализован TradingNotifier wrapper
- ✅ Добавлена кнопка отмены покупки
- ✅ Добавлен индикатор DRY-RUN/LIVE
- ✅ Реализованы callback-обработчики
- ✅ Создана документация

---

**Версия документа**: 1.0
**Последнее обновление**: 19 ноября 2025 г.
