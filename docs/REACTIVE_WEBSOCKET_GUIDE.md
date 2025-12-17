# 🔄 Reactive WebSocket Guide

**Версия**: 1.0
**Дата**: 17 декабря 2025 г.

---

## 📋 Обзор

Reactive WebSocket клиент предоставляет event-driven архитектуру для получения real-time обновлений от DMarket API через WebSocket соединения. Использует паттерн Observer для реактивной обработки событий.

### Основные возможности

- ✅ **Event-driven архитектура** - реактивная обработка событий
- ✅ **Auto-reconnection** - автоматическое переподключение при обрыве
- ✅ **Observable pattern** - подписка на события через Observable
- ✅ **Typed events** - строгая типизация событий (EventType enum)
- ✅ **Subscription management** - управление активными подписками
- ✅ **Statistics tracking** - статистика по подпискам и событиям
- ✅ **Push notifications** - мгновенные уведомления без polling

---

## 🎯 Типы событий

### EventType

```python
class EventType(str, Enum):
    """WebSocket event types."""

    BALANCE_UPDATE = "balance:update"           # Обновление баланса
    ORDER_CREATED = "order:created"             # Создан ордер
    ORDER_UPDATED = "order:updated"             # Обновлен ордер
    ORDER_COMPLETED = "order:completed"         # Ордер исполнен
    ORDER_CANCELLED = "order:cancelled"         # Ордер отменен
    MARKET_PRICE_CHANGE = "market:price"        # Изменение цены
    MARKET_ITEM_ADDED = "market:item:added"     # Предмет добавлен
    MARKET_ITEM_REMOVED = "market:item:removed" # Предмет удален
    TARGET_MATCHED = "target:matched"           # Target исполнен
    TRADE_COMPLETED = "trade:completed"         # Сделка завершена
```

---

## 🚀 Быстрый старт

### 1. Инициализация клиента

```python
from src.utils.reactive_websocket import ReactiveDMarketWebSocket
from src.dmarket.dmarket_api import DMarketAPI

# Создать API клиент
api_client = DMarketAPI(public_key="...", secret_key="...")

# Создать WebSocket клиент
ws_client = ReactiveDMarketWebSocket(
    api_client=api_client,
    auto_reconnect=True,  # Автоматическое переподключение
    max_reconnect_attempts=10
)

# Подключиться
await ws_client.connect()
```

### 2. Подписка на события

#### Синхронный обработчик

```python
def on_balance_update(event: dict):
    """Обработчик обновления баланса."""
    print(f"New balance: {event['balance']}")

# Подписаться на обновления баланса
ws_client.observables[EventType.BALANCE_UPDATE].subscribe(on_balance_update)
```

#### Асинхронный обработчик

```python
async def on_order_completed(event: dict):
    """Обработчик завершения ордера."""
    order_id = event.get("orderId")
    print(f"Order {order_id} completed!")

    # Отправить уведомление в Telegram
    await send_telegram_notification(
        f"✅ Ордер #{order_id} исполнен!"
    )

# Подписаться на события ордеров
ws_client.observables[EventType.ORDER_COMPLETED].subscribe_async(
    on_order_completed
)
```

### 3. Подписка на топики DMarket

```python
# Подписаться на обновления баланса
await ws_client.subscribe_to_balance_updates()

# Подписаться на события ордеров
await ws_client.subscribe_to_order_events()

# Подписаться на изменения цен
await ws_client.subscribe_to_market_prices(
    game="csgo",
    items=["item_id_1", "item_id_2"]  # Опционально: конкретные предметы
)

# Подписаться на исполнение таргетов
await ws_client.subscribe_to_target_matches()
```

---

## 📊 Примеры использования

### Пример 1: Real-time мониторинг баланса

```python
async def setup_balance_monitoring():
    """Настроить мониторинг баланса."""

    # Обработчик обновлений баланса
    async def on_balance_change(event: dict):
        old_balance = event.get("old_balance", 0)
        new_balance = event.get("balance", 0)
        change = new_balance - old_balance

        logger.info(
            "Balance updated",
            old=old_balance,
            new=new_balance,
            change=change
        )

        # Уведомление в Telegram
        if abs(change) > 1.0:  # Изменение больше $1
            await notifier.send_notification(
                user_id=user.telegram_id,
                message=f"💰 Баланс изменился на ${change:.2f}\n"
                        f"Новый баланс: ${new_balance:.2f}",
                category="balance"
            )

    # Подписаться
    ws_client.observables[EventType.BALANCE_UPDATE].subscribe_async(
        on_balance_change
    )
    await ws_client.subscribe_to_balance_updates()
```

### Пример 2: Снайперский режим (мгновенная покупка)

```python
async def sniper_mode(target_items: list[str], max_price: float):
    """Снайперский режим - мгновенная покупка при появлении предмета.

    Args:
        target_items: Список названий предметов для покупки
        max_price: Максимальная цена для покупки
    """

    async def on_item_added(event: dict):
        """Обработчик добавления предмета на маркет."""
        item_title = event.get("title")
        item_price = event.get("price", {}).get("USD", 0) / 100  # Центы -> USD
        item_id = event.get("itemId")

        # Проверить, что это целевой предмет
        if item_title not in target_items:
            return

        # Проверить цену
        if item_price > max_price:
            logger.info(
                "Item too expensive",
                title=item_title,
                price=item_price,
                max_price=max_price
            )
            return

        # МГНОВЕННАЯ ПОКУПКА
        logger.info(
            "SNIPING ITEM!",
            title=item_title,
            price=item_price,
            item_id=item_id
        )

        try:
            result = await api_client.buy_item(item_id, item_price)

            if result.get("success"):
                await notifier.send_notification(
                    user_id=user.telegram_id,
                    message=f"🎯 КУПЛЕНО: {item_title}\n"
                            f"💰 Цена: ${item_price:.2f}\n"
                            f"⚡ Режим: Снайпер",
                    priority="HIGH"
                )
            else:
                logger.error("Snipe failed", result=result)

        except Exception as e:
            logger.exception("Error during snipe", error=str(e))

    # Подписаться на добавление предметов
    ws_client.observables[EventType.MARKET_ITEM_ADDED].subscribe_async(
        on_item_added
    )

    # Подписаться на маркет для конкретных предметов
    await ws_client.subscribe_to_market_prices(game="csgo")

    logger.info(
        "Sniper mode activated",
        targets=target_items,
        max_price=max_price
    )
```

### Пример 3: Автоматическая торговля на основе событий

```python
async def event_driven_trading():
    """Автоматическая торговля на основе событий."""

    # 1. Обработчик исполнения таргета
    async def on_target_matched(event: dict):
        """Таргет исполнен - автоматически выставить на продажу."""
        item_id = event.get("itemId")
        buy_price = event.get("price", 0) / 100
        item_title = event.get("title")

        # Рассчитать цену продажи (10% прибыли)
        sell_price = buy_price * 1.10

        logger.info(
            "Target matched - listing for sale",
            title=item_title,
            buy_price=buy_price,
            sell_price=sell_price
        )

        # Выставить на продажу
        await api_client.sell_item(item_id, sell_price)

        await notifier.send_notification(
            user_id=user.telegram_id,
            message=f"🎯 Target исполнен!\n"
                    f"📦 {item_title}\n"
                    f"💰 Куплено: ${buy_price:.2f}\n"
                    f"💵 Выставлено: ${sell_price:.2f}\n"
                    f"📈 Прибыль: ${sell_price - buy_price:.2f}",
            category="trading"
        )

    # 2. Обработчик завершения сделки
    async def on_trade_completed(event: dict):
        """Сделка завершена - записать статистику."""
        item_id = event.get("itemId")
        final_price = event.get("price", 0) / 100

        # Получить информацию о покупке
        # (предполагается, что храним в БД)
        trade_info = await db.get_trade_by_item_id(item_id)

        if trade_info:
            profit = final_price - trade_info["buy_price"]

            # Обновить статистику
            await db.update_trade_statistics(
                profit=profit,
                completed_at=datetime.now(UTC)
            )

            await notifier.send_notification(
                user_id=user.telegram_id,
                message=f"✅ Продано!\n"
                        f"💵 Цена: ${final_price:.2f}\n"
                        f"📈 Прибыль: ${profit:.2f}",
                category="trading"
            )

    # Подписаться на события
    ws_client.observables[EventType.TARGET_MATCHED].subscribe_async(
        on_target_matched
    )
    ws_client.observables[EventType.TRADE_COMPLETED].subscribe_async(
        on_trade_completed
    )

    # Активировать подписки
    await ws_client.subscribe_to_target_matches()
    await ws_client.subscribe_to_order_events()
```

---

## 🔧 Управление подписками

### Создание подписки

```python
# Создать подписку
subscription = await ws_client.subscribe_to(
    topic="custom:topic",
    params={"gameId": "csgo", "userId": "12345"}
)

# Проверить статус
print(f"State: {subscription.state}")
print(f"Events received: {subscription.event_count}")
```

### Отписка

```python
# Отписаться от топика
await ws_client.unsubscribe_from("custom:topic")
```

### Получение статистики

```python
# Статистика по всем подпискам
stats = ws_client.get_subscription_stats()

print(f"Total subscriptions: {stats['total_subscriptions']}")

for sub in stats['subscriptions']:
    print(f"Topic: {sub['topic']}")
    print(f"State: {sub['state']}")
    print(f"Events: {sub['events_received']}")
    print(f"Last event: {sub['last_event_at']}")
```

---

## 📡 Observable Pattern

### Подписка на все события

```python
async def log_all_events(event: dict):
    """Логировать все события."""
    logger.debug("Event received", event_type=event.get("type"), event=event)

# Подписаться на ВСЕ события
ws_client.all_events.subscribe_async(log_all_events)
```

### Множественные обработчики

```python
# Можно подписать несколько обработчиков на одно событие

async def handler1(event: dict):
    print("Handler 1:", event)

async def handler2(event: dict):
    print("Handler 2:", event)

observable = ws_client.observables[EventType.ORDER_COMPLETED]
observable.subscribe_async(handler1)
observable.subscribe_async(handler2)

# Оба обработчика получат событие
```

### Отписка от обработчика

```python
# Отписаться от конкретного обработчика
observable.unsubscribe_async(handler1)

# Очистить все обработчики
observable.clear()
```

---

## 🔌 Мониторинг соединения

### Подписка на состояние соединения

```python
async def on_connection_change(connected: bool):
    """Обработчик изменения состояния соединения."""
    if connected:
        logger.info("WebSocket connected!")
        await notifier.send_notification(
            user_id=admin_id,
            message="✅ WebSocket подключен",
            category="system"
        )
    else:
        logger.warning("WebSocket disconnected!")
        await notifier.send_notification(
            user_id=admin_id,
            message="⚠️ WebSocket отключен",
            priority="HIGH",
            category="system"
        )

# Подписаться на изменения состояния
ws_client.connection_state.subscribe_async(on_connection_change)
```

---

## ⚙️ Конфигурация

### Параметры клиента

```python
ws_client = ReactiveDMarketWebSocket(
    api_client=api_client,
    auto_reconnect=True,           # Автоматическое переподключение
    max_reconnect_attempts=10      # Максимум попыток
)
```

### Переменные окружения

Добавьте в `.env`:

```env
# WebSocket настройки
WEBSOCKET_AUTO_RECONNECT=true
WEBSOCKET_MAX_RECONNECT_ATTEMPTS=10
WEBSOCKET_HEARTBEAT_INTERVAL=30
```

---

## 🧪 Тестирование

### Unit тесты

```python
import pytest
from unittest.mock import AsyncMock, MagicMock

@pytest.mark.asyncio
async def test_websocket_subscription():
    """Тест подписки на событие."""

    # Arrange
    api_client = AsyncMock(spec=DMarketAPI)
    ws_client = ReactiveDMarketWebSocket(api_client)

    # Mock connection
    ws_client.is_connected = True
    ws_client.ws_connection = MagicMock()
    ws_client.ws_connection.send_json = AsyncMock()

    # Act
    subscription = await ws_client.subscribe_to("test:topic")

    # Assert
    assert subscription.topic == "test:topic"
    assert subscription.state == SubscriptionState.ACTIVE
    ws_client.ws_connection.send_json.assert_called_once()
```

---

## 🛡️ Best Practices

### 1. Обработка ошибок

```python
async def safe_handler(event: dict):
    """Безопасный обработчик с обработкой ошибок."""
    try:
        # Ваша логика
        await process_event(event)
    except Exception as e:
        logger.exception("Error in event handler", error=str(e))
        # НЕ перевыбрасывать исключение - это остановит обработку
```

### 2. Логирование событий

```python
async def logging_handler(event: dict):
    """Обработчик с логированием."""
    logger.info(
        "Event received",
        event_type=event.get("type"),
        timestamp=event.get("timestamp"),
        # НЕ логировать все событие - может быть большим
    )
```

### 3. Graceful Shutdown

```python
async def shutdown():
    """Корректное завершение работы."""
    logger.info("Shutting down WebSocket client...")

    # Отключиться (автоматически отпишется от всех топиков)
    await ws_client.disconnect()

    # Очистить все обработчики
    for observable in ws_client.observables.values():
        observable.clear()

    logger.info("WebSocket client shut down")
```

### 4. Мониторинг производительности

```python
import time

async def performance_monitoring():
    """Мониторинг производительности обработки событий."""

    event_count = 0
    start_time = time.time()

    async def count_events(event: dict):
        nonlocal event_count
        event_count += 1

        # Каждые 100 событий
        if event_count % 100 == 0:
            elapsed = time.time() - start_time
            rate = event_count / elapsed

            logger.info(
                "Event processing rate",
                events=event_count,
                elapsed=elapsed,
                rate=rate
            )

    ws_client.all_events.subscribe_async(count_events)
```

---

## 📚 Ссылки

- [DMarket WebSocket API](https://docs.dmarket.com/v1/websocket.html)
- [Observer Pattern](https://refactoring.guru/design-patterns/observer)
- [Reactive Programming](https://reactivex.io/)

---

**Версия**: 1.0
**Последнее обновление**: 17 декабря 2025 г.
