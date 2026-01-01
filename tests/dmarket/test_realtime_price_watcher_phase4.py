"""Phase 4 расширенные тесты для realtime_price_watcher.py.

Этот модуль содержит дополнительные тесты для достижения 100% покрытия
модуля realtime_price_watcher.py.
"""

import asyncio
from collections import defaultdict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# =========================================
# TestPriceAlert
# =========================================


class TestPriceAlertInit:
    """Тесты инициализации PriceAlert."""

    def test_price_alert_init_basic(self):
        """Тест базовой инициализации."""
        from src.dmarket.realtime_price_watcher import PriceAlert

        alert = PriceAlert(
            item_id="item123",
            market_hash_name="AK-47 | Redline",
            target_price=25.50,
        )
        assert alert.item_id == "item123"
        assert alert.market_hash_name == "AK-47 | Redline"
        assert alert.target_price == 25.50
        assert alert.condition == "below"
        assert alert.game == "csgo"
        assert alert.is_triggered is False
        assert alert.triggered_at is None
        assert alert.created_at > 0

    def test_price_alert_init_above_condition(self):
        """Тест инициализации с условием above."""
        from src.dmarket.realtime_price_watcher import PriceAlert

        alert = PriceAlert(
            item_id="item456",
            market_hash_name="AWP | Dragon Lore",
            target_price=1500.0,
            condition="above",
        )
        assert alert.condition == "above"
        assert alert.target_price == 1500.0

    def test_price_alert_init_different_game(self):
        """Тест инициализации с другой игрой."""
        from src.dmarket.realtime_price_watcher import PriceAlert

        alert = PriceAlert(
            item_id="item789",
            market_hash_name="Immortal Treasure",
            target_price=10.0,
            game="dota2",
        )
        assert alert.game == "dota2"

    def test_price_alert_init_all_params(self):
        """Тест инициализации со всеми параметрами."""
        from src.dmarket.realtime_price_watcher import PriceAlert

        alert = PriceAlert(
            item_id="item_full",
            market_hash_name="Full Test Item",
            target_price=100.0,
            condition="above",
            game="tf2",
        )
        assert alert.item_id == "item_full"
        assert alert.market_hash_name == "Full Test Item"
        assert alert.target_price == 100.0
        assert alert.condition == "above"
        assert alert.game == "tf2"


class TestPriceAlertCheckCondition:
    """Тесты метода check_condition."""

    def test_check_condition_below_triggered(self):
        """Тест срабатывания условия below."""
        from src.dmarket.realtime_price_watcher import PriceAlert

        alert = PriceAlert(
            item_id="item123",
            market_hash_name="Test Item",
            target_price=50.0,
            condition="below",
        )
        result = alert.check_condition(45.0)  # Цена ниже целевой
        assert result is True
        assert alert.triggered_at is not None

    def test_check_condition_below_not_triggered(self):
        """Тест не срабатывания условия below."""
        from src.dmarket.realtime_price_watcher import PriceAlert

        alert = PriceAlert(
            item_id="item123",
            market_hash_name="Test Item",
            target_price=50.0,
            condition="below",
        )
        result = alert.check_condition(55.0)  # Цена выше целевой
        assert result is False
        assert alert.triggered_at is None

    def test_check_condition_below_equal(self):
        """Тест условия below при равной цене."""
        from src.dmarket.realtime_price_watcher import PriceAlert

        alert = PriceAlert(
            item_id="item123",
            market_hash_name="Test Item",
            target_price=50.0,
            condition="below",
        )
        result = alert.check_condition(50.0)  # Цена равна целевой
        assert result is True

    def test_check_condition_above_triggered(self):
        """Тест срабатывания условия above."""
        from src.dmarket.realtime_price_watcher import PriceAlert

        alert = PriceAlert(
            item_id="item123",
            market_hash_name="Test Item",
            target_price=50.0,
            condition="above",
        )
        result = alert.check_condition(55.0)  # Цена выше целевой
        assert result is True

    def test_check_condition_above_not_triggered(self):
        """Тест не срабатывания условия above."""
        from src.dmarket.realtime_price_watcher import PriceAlert

        alert = PriceAlert(
            item_id="item123",
            market_hash_name="Test Item",
            target_price=50.0,
            condition="above",
        )
        result = alert.check_condition(45.0)  # Цена ниже целевой
        assert result is False

    def test_check_condition_above_equal(self):
        """Тест условия above при равной цене."""
        from src.dmarket.realtime_price_watcher import PriceAlert

        alert = PriceAlert(
            item_id="item123",
            market_hash_name="Test Item",
            target_price=50.0,
            condition="above",
        )
        result = alert.check_condition(50.0)  # Цена равна целевой
        assert result is True

    def test_check_condition_already_triggered(self):
        """Тест при уже сработавшем оповещении."""
        from src.dmarket.realtime_price_watcher import PriceAlert

        alert = PriceAlert(
            item_id="item123",
            market_hash_name="Test Item",
            target_price=50.0,
            condition="below",
        )
        # Первый раз срабатывает
        alert.check_condition(45.0)
        first_triggered_at = alert.triggered_at

        # Второй раз - triggered_at не должен измениться
        alert.check_condition(40.0)
        assert alert.triggered_at == first_triggered_at


class TestPriceAlertReset:
    """Тесты метода reset."""

    def test_reset_triggered_alert(self):
        """Тест сброса сработавшего оповещения."""
        from src.dmarket.realtime_price_watcher import PriceAlert

        alert = PriceAlert(
            item_id="item123",
            market_hash_name="Test Item",
            target_price=50.0,
            condition="below",
        )
        # Срабатываем оповещение
        alert.check_condition(45.0)
        alert.is_triggered = True

        # Сбрасываем
        alert.reset()
        assert alert.is_triggered is False
        assert alert.triggered_at is None

    def test_reset_not_triggered_alert(self):
        """Тест сброса не сработавшего оповещения."""
        from src.dmarket.realtime_price_watcher import PriceAlert

        alert = PriceAlert(
            item_id="item123",
            market_hash_name="Test Item",
            target_price=50.0,
            condition="below",
        )
        # Сбрасываем без срабатывания
        alert.reset()
        assert alert.is_triggered is False
        assert alert.triggered_at is None


# =========================================
# TestRealtimePriceWatcher
# =========================================


class TestRealtimePriceWatcherInit:
    """Тесты инициализации RealtimePriceWatcher."""

    def test_init_basic(self):
        """Тест базовой инициализации."""
        from src.dmarket.realtime_price_watcher import RealtimePriceWatcher

        mock_api = MagicMock()
        watcher = RealtimePriceWatcher(mock_api)

        assert watcher.api_client == mock_api
        assert watcher.websocket_client is not None
        assert watcher.price_cache == {}
        assert isinstance(watcher.price_history, defaultdict)
        assert watcher.max_history_points == 100
        assert isinstance(watcher.price_alerts, defaultdict)
        assert isinstance(watcher.price_change_handlers, defaultdict)
        assert watcher.alert_handlers == []
        assert watcher.watched_items == set()
        assert watcher.item_metadata == {}
        assert watcher.ws_task is None
        assert watcher.price_update_task is None
        assert watcher.is_running is False
        assert watcher.price_update_interval == 300


class TestRealtimePriceWatcherStart:
    """Тесты метода start."""

    @pytest.mark.asyncio()
    async def test_start_success(self):
        """Тест успешного запуска."""
        from src.dmarket.realtime_price_watcher import RealtimePriceWatcher

        mock_api = MagicMock()
        watcher = RealtimePriceWatcher(mock_api)

        # Мокаем WebSocket клиент
        watcher.websocket_client = MagicMock()
        watcher.websocket_client.connect = AsyncMock(return_value=True)
        watcher.websocket_client.listen = AsyncMock()
        watcher.websocket_client.register_handler = MagicMock()

        # Мокаем периодическое обновление
        with patch.object(
            watcher, "_periodic_price_updates", new_callable=AsyncMock
        ) as mock_updates:
            mock_updates.return_value = None
            result = await watcher.start()

        assert result is True
        assert watcher.is_running is True
        assert watcher.ws_task is not None

    @pytest.mark.asyncio()
    async def test_start_already_running(self):
        """Тест запуска при уже работающем наблюдателе."""
        from src.dmarket.realtime_price_watcher import RealtimePriceWatcher

        mock_api = MagicMock()
        watcher = RealtimePriceWatcher(mock_api)
        watcher.is_running = True

        result = await watcher.start()
        assert result is True

    @pytest.mark.asyncio()
    async def test_start_connection_failed(self):
        """Тест неудачного подключения."""
        from src.dmarket.realtime_price_watcher import RealtimePriceWatcher

        mock_api = MagicMock()
        watcher = RealtimePriceWatcher(mock_api)

        watcher.websocket_client = MagicMock()
        watcher.websocket_client.connect = AsyncMock(return_value=False)
        watcher.websocket_client.register_handler = MagicMock()

        result = await watcher.start()
        assert result is False
        assert watcher.is_running is False


class TestRealtimePriceWatcherStop:
    """Тесты метода stop."""

    @pytest.mark.asyncio()
    async def test_stop_running(self):
        """Тест остановки работающего наблюдателя."""
        from src.dmarket.realtime_price_watcher import RealtimePriceWatcher

        mock_api = MagicMock()
        watcher = RealtimePriceWatcher(mock_api)
        watcher.is_running = True

        # Создаём mock задачи
        watcher.ws_task = MagicMock()
        watcher.ws_task.done.return_value = False
        watcher.ws_task.cancel = MagicMock()

        watcher.price_update_task = MagicMock()
        watcher.price_update_task.done.return_value = False
        watcher.price_update_task.cancel = MagicMock()

        watcher.websocket_client = MagicMock()
        watcher.websocket_client.close = AsyncMock()

        # Мокаем await для отменённых задач
        async def mock_await():
            raise asyncio.CancelledError

        watcher.ws_task.__await__ = lambda self: mock_await().__await__()
        watcher.price_update_task.__await__ = lambda self: mock_await().__await__()

        await watcher.stop()
        assert watcher.is_running is False

    @pytest.mark.asyncio()
    async def test_stop_not_running(self):
        """Тест остановки не работающего наблюдателя."""
        from src.dmarket.realtime_price_watcher import RealtimePriceWatcher

        mock_api = MagicMock()
        watcher = RealtimePriceWatcher(mock_api)
        watcher.is_running = False

        await watcher.stop()
        assert watcher.is_running is False


class TestHandleMarketUpdate:
    """Тесты метода _handle_market_update."""

    @pytest.mark.asyncio()
    async def test_handle_market_update_valid(self):
        """Тест обработки валидного сообщения."""
        from src.dmarket.realtime_price_watcher import RealtimePriceWatcher

        mock_api = MagicMock()
        watcher = RealtimePriceWatcher(mock_api)
        watcher.watched_items.add("item123")

        message = {
            "data": {
                "items": [
                    {
                        "itemId": "item123",
                        "price": {"USD": 5000},
                    }
                ]
            }
        }

        await watcher._handle_market_update(message)
        assert watcher.price_cache.get("item123") == 50.0

    @pytest.mark.asyncio()
    async def test_handle_market_update_empty_data(self):
        """Тест обработки пустого сообщения."""
        from src.dmarket.realtime_price_watcher import RealtimePriceWatcher

        mock_api = MagicMock()
        watcher = RealtimePriceWatcher(mock_api)

        message = {"data": {}}
        await watcher._handle_market_update(message)
        assert watcher.price_cache == {}

    @pytest.mark.asyncio()
    async def test_handle_market_update_no_item_id(self):
        """Тест обработки сообщения без item_id."""
        from src.dmarket.realtime_price_watcher import RealtimePriceWatcher

        mock_api = MagicMock()
        watcher = RealtimePriceWatcher(mock_api)

        message = {
            "data": {
                "items": [
                    {
                        "price": {"USD": 5000},
                    }
                ]
            }
        }
        await watcher._handle_market_update(message)
        assert watcher.price_cache == {}

    @pytest.mark.asyncio()
    async def test_handle_market_update_no_price(self):
        """Тест обработки сообщения без цены."""
        from src.dmarket.realtime_price_watcher import RealtimePriceWatcher

        mock_api = MagicMock()
        watcher = RealtimePriceWatcher(mock_api)

        message = {
            "data": {
                "items": [
                    {
                        "itemId": "item123",
                    }
                ]
            }
        }
        await watcher._handle_market_update(message)
        assert watcher.price_cache == {}

    @pytest.mark.asyncio()
    async def test_handle_market_update_invalid_price(self):
        """Тест обработки сообщения с невалидной ценой."""
        from src.dmarket.realtime_price_watcher import RealtimePriceWatcher

        mock_api = MagicMock()
        watcher = RealtimePriceWatcher(mock_api)
        watcher.watched_items.add("item123")

        message = {
            "data": {
                "items": [
                    {
                        "itemId": "item123",
                        "price": {"USD": "invalid"},
                    }
                ]
            }
        }
        await watcher._handle_market_update(message)
        assert watcher.price_cache.get("item123") is None

    @pytest.mark.asyncio()
    async def test_handle_market_update_item_not_watched(self):
        """Тест обработки сообщения для не отслеживаемого предмета."""
        from src.dmarket.realtime_price_watcher import RealtimePriceWatcher

        mock_api = MagicMock()
        watcher = RealtimePriceWatcher(mock_api)

        message = {
            "data": {
                "items": [
                    {
                        "itemId": "item123",
                        "price": {"USD": 5000},
                    }
                ]
            }
        }
        await watcher._handle_market_update(message)
        assert watcher.price_cache == {}


class TestHandleItemsUpdate:
    """Тесты метода _handle_items_update."""

    @pytest.mark.asyncio()
    async def test_handle_items_update_valid(self):
        """Тест обработки валидного сообщения."""
        from src.dmarket.realtime_price_watcher import RealtimePriceWatcher

        mock_api = MagicMock()
        watcher = RealtimePriceWatcher(mock_api)
        watcher.watched_items.add("item123")

        message = {
            "data": {
                "items": [
                    {
                        "itemId": "item123",
                        "title": "Test Item",
                        "gameId": "csgo",
                        "price": {"USD": 5000},
                    }
                ]
            }
        }

        await watcher._handle_items_update(message)
        assert watcher.price_cache.get("item123") == 50.0
        assert watcher.item_metadata.get("item123") is not None
        assert watcher.item_metadata.get("item123")["title"] == "Test Item"

    @pytest.mark.asyncio()
    async def test_handle_items_update_with_metadata(self):
        """Тест сохранения метаданных."""
        from src.dmarket.realtime_price_watcher import RealtimePriceWatcher

        mock_api = MagicMock()
        watcher = RealtimePriceWatcher(mock_api)
        watcher.watched_items.add("item123")

        message = {
            "data": {
                "items": [
                    {
                        "itemId": "item123",
                        "title": "AWP | Dragon Lore",
                        "gameId": "csgo",
                        "price": {"USD": 150000},
                    }
                ]
            }
        }

        await watcher._handle_items_update(message)
        metadata = watcher.item_metadata.get("item123")
        assert metadata is not None
        assert metadata["title"] == "AWP | Dragon Lore"
        assert metadata["gameId"] == "csgo"
        assert "lastUpdated" in metadata


class TestAddToPriceHistory:
    """Тесты метода _add_to_price_history."""

    def test_add_to_price_history_basic(self):
        """Тест добавления в историю."""
        from src.dmarket.realtime_price_watcher import RealtimePriceWatcher

        mock_api = MagicMock()
        watcher = RealtimePriceWatcher(mock_api)

        watcher._add_to_price_history("item123", 50.0)
        history = watcher.price_history.get("item123", [])
        assert len(history) == 1
        assert history[0][1] == 50.0

    def test_add_to_price_history_limit(self):
        """Тест ограничения размера истории."""
        from src.dmarket.realtime_price_watcher import RealtimePriceWatcher

        mock_api = MagicMock()
        watcher = RealtimePriceWatcher(mock_api)
        watcher.max_history_points = 5

        for i in range(10):
            watcher._add_to_price_history("item123", float(i))

        history = watcher.price_history.get("item123", [])
        assert len(history) == 5
        assert history[0][1] == 5.0  # Первые 5 точек удалены


class TestPeriodicPriceUpdates:
    """Тесты метода _periodic_price_updates."""

    @pytest.mark.asyncio()
    async def test_periodic_updates_cancelled(self):
        """Тест отмены периодических обновлений."""
        from src.dmarket.realtime_price_watcher import RealtimePriceWatcher

        mock_api = MagicMock()
        watcher = RealtimePriceWatcher(mock_api)
        watcher.is_running = True
        watcher.price_update_interval = 0.01

        async def mock_update():
            raise asyncio.CancelledError

        with patch.object(
            watcher, "_update_watched_items_prices", side_effect=mock_update
        ):
            await watcher._periodic_price_updates()


class TestUpdateWatchedItemsPrices:
    """Тесты метода _update_watched_items_prices."""

    @pytest.mark.asyncio()
    async def test_update_prices_no_items(self):
        """Тест обновления без отслеживаемых предметов."""
        from src.dmarket.realtime_price_watcher import RealtimePriceWatcher

        mock_api = MagicMock()
        watcher = RealtimePriceWatcher(mock_api)

        await watcher._update_watched_items_prices()
        # Не должно быть ошибок

    @pytest.mark.asyncio()
    async def test_update_prices_with_items(self):
        """Тест обновления с предметами."""
        from src.dmarket.realtime_price_watcher import RealtimePriceWatcher

        mock_api = MagicMock()
        mock_api._request = AsyncMock(
            return_value={
                "items": [
                    {
                        "itemId": "item123",
                        "title": "Test Item",
                        "price": {"USD": 5000},
                    }
                ]
            }
        )

        watcher = RealtimePriceWatcher(mock_api)
        watcher.watched_items.add("item123")

        await watcher._update_watched_items_prices()
        assert watcher.price_cache.get("item123") == 50.0

    @pytest.mark.asyncio()
    async def test_update_prices_api_error(self):
        """Тест обновления при ошибке API."""
        from src.dmarket.realtime_price_watcher import RealtimePriceWatcher

        mock_api = MagicMock()
        mock_api._request = AsyncMock(side_effect=Exception("API Error"))

        watcher = RealtimePriceWatcher(mock_api)
        watcher.watched_items.add("item123")

        # Не должно выбросить исключение
        await watcher._update_watched_items_prices()


class TestProcessPriceChange:
    """Тесты метода _process_price_change."""

    @pytest.mark.asyncio()
    async def test_process_price_change_same_price(self):
        """Тест при одинаковых ценах."""
        from src.dmarket.realtime_price_watcher import RealtimePriceWatcher

        mock_api = MagicMock()
        watcher = RealtimePriceWatcher(mock_api)

        handler_called = False

        async def test_handler(item_id, old_price, new_price):
            nonlocal handler_called
            handler_called = True

        watcher.register_price_change_handler(test_handler, "item123")
        await watcher._process_price_change("item123", 50.0, 50.0)
        assert handler_called is False

    @pytest.mark.asyncio()
    async def test_process_price_change_with_handler(self):
        """Тест с обработчиком."""
        from src.dmarket.realtime_price_watcher import RealtimePriceWatcher

        mock_api = MagicMock()
        watcher = RealtimePriceWatcher(mock_api)

        results = []

        async def test_handler(item_id, old_price, new_price):
            results.append((item_id, old_price, new_price))

        watcher.register_price_change_handler(test_handler, "item123")
        await watcher._process_price_change("item123", 45.0, 50.0)
        assert len(results) == 1
        assert results[0] == ("item123", 45.0, 50.0)

    @pytest.mark.asyncio()
    async def test_process_price_change_global_handler(self):
        """Тест с глобальным обработчиком."""
        from src.dmarket.realtime_price_watcher import RealtimePriceWatcher

        mock_api = MagicMock()
        watcher = RealtimePriceWatcher(mock_api)

        results = []

        async def global_handler(item_id, old_price, new_price):
            results.append(("global", item_id))

        watcher.register_price_change_handler(global_handler, "*")
        await watcher._process_price_change("item123", 45.0, 50.0)
        assert len(results) == 1
        assert results[0][0] == "global"

    @pytest.mark.asyncio()
    async def test_process_price_change_handler_exception(self):
        """Тест при исключении в обработчике."""
        from src.dmarket.realtime_price_watcher import RealtimePriceWatcher

        mock_api = MagicMock()
        watcher = RealtimePriceWatcher(mock_api)

        async def bad_handler(item_id, old_price, new_price):
            raise ValueError("Handler error")

        watcher.register_price_change_handler(bad_handler, "item123")
        # Не должно выбросить исключение
        await watcher._process_price_change("item123", 45.0, 50.0)


class TestCheckAlerts:
    """Тесты метода _check_alerts."""

    @pytest.mark.asyncio()
    async def test_check_alerts_triggered(self):
        """Тест срабатывания оповещения."""
        from src.dmarket.realtime_price_watcher import PriceAlert, RealtimePriceWatcher

        mock_api = MagicMock()
        watcher = RealtimePriceWatcher(mock_api)

        alert = PriceAlert(
            item_id="item123",
            market_hash_name="Test Item",
            target_price=50.0,
            condition="below",
        )
        watcher.add_price_alert(alert)

        triggered_alerts = []

        async def alert_handler(alert, current_price):
            triggered_alerts.append((alert, current_price))

        watcher.register_alert_handler(alert_handler)
        await watcher._check_alerts("item123", 45.0)

        assert len(triggered_alerts) == 1
        assert alert.is_triggered is True

    @pytest.mark.asyncio()
    async def test_check_alerts_not_triggered(self):
        """Тест не срабатывания оповещения."""
        from src.dmarket.realtime_price_watcher import PriceAlert, RealtimePriceWatcher

        mock_api = MagicMock()
        watcher = RealtimePriceWatcher(mock_api)

        alert = PriceAlert(
            item_id="item123",
            market_hash_name="Test Item",
            target_price=50.0,
            condition="below",
        )
        watcher.add_price_alert(alert)

        await watcher._check_alerts("item123", 55.0)
        assert alert.is_triggered is False

    @pytest.mark.asyncio()
    async def test_check_alerts_already_triggered(self):
        """Тест уже сработавшего оповещения."""
        from src.dmarket.realtime_price_watcher import PriceAlert, RealtimePriceWatcher

        mock_api = MagicMock()
        watcher = RealtimePriceWatcher(mock_api)

        alert = PriceAlert(
            item_id="item123",
            market_hash_name="Test Item",
            target_price=50.0,
            condition="below",
        )
        alert.is_triggered = True
        watcher.add_price_alert(alert)

        triggered_alerts = []

        async def alert_handler(alert, current_price):
            triggered_alerts.append(alert)

        watcher.register_alert_handler(alert_handler)
        await watcher._check_alerts("item123", 45.0)

        # Не должно вызываться, т.к. уже сработало
        assert len(triggered_alerts) == 0


class TestSubscribeToItem:
    """Тесты метода subscribe_to_item."""

    @pytest.mark.asyncio()
    async def test_subscribe_not_running(self):
        """Тест подписки без запуска."""
        from src.dmarket.realtime_price_watcher import RealtimePriceWatcher

        mock_api = MagicMock()
        watcher = RealtimePriceWatcher(mock_api)
        watcher.is_running = False

        result = await watcher.subscribe_to_item("item123")
        assert result is False

    @pytest.mark.asyncio()
    async def test_subscribe_success(self):
        """Тест успешной подписки."""
        from src.dmarket.realtime_price_watcher import RealtimePriceWatcher

        mock_api = MagicMock()
        mock_api._request = AsyncMock(
            return_value={
                "items": [
                    {
                        "itemId": "item123",
                        "title": "Test Item",
                        "price": {"USD": 5000},
                    }
                ]
            }
        )

        watcher = RealtimePriceWatcher(mock_api)
        watcher.is_running = True
        watcher.websocket_client = MagicMock()
        watcher.websocket_client.subscribe_to_item_updates = AsyncMock(
            return_value=True
        )

        result = await watcher.subscribe_to_item("item123")
        assert result is True
        assert "item123" in watcher.watched_items


class TestSubscribeToMarketUpdates:
    """Тесты метода subscribe_to_market_updates."""

    @pytest.mark.asyncio()
    async def test_subscribe_market_not_running(self):
        """Тест подписки на рынок без запуска."""
        from src.dmarket.realtime_price_watcher import RealtimePriceWatcher

        mock_api = MagicMock()
        watcher = RealtimePriceWatcher(mock_api)
        watcher.is_running = False

        result = await watcher.subscribe_to_market_updates("csgo")
        assert result is False

    @pytest.mark.asyncio()
    async def test_subscribe_market_success(self):
        """Тест успешной подписки на рынок."""
        from src.dmarket.realtime_price_watcher import RealtimePriceWatcher

        mock_api = MagicMock()
        watcher = RealtimePriceWatcher(mock_api)
        watcher.is_running = True
        watcher.websocket_client = MagicMock()
        watcher.websocket_client.subscribe_to_market_updates = AsyncMock(
            return_value=True
        )

        result = await watcher.subscribe_to_market_updates("csgo")
        assert result is True


class TestFetchItemPrice:
    """Тесты метода _fetch_item_price."""

    @pytest.mark.asyncio()
    async def test_fetch_price_success(self):
        """Тест успешного получения цены."""
        from src.dmarket.realtime_price_watcher import RealtimePriceWatcher

        mock_api = MagicMock()
        mock_api._request = AsyncMock(
            return_value={
                "items": [
                    {
                        "itemId": "item123",
                        "title": "Test Item",
                        "price": {"USD": 5000},
                    }
                ]
            }
        )

        watcher = RealtimePriceWatcher(mock_api)
        price = await watcher._fetch_item_price("item123", "csgo")
        assert price == 50.0

    @pytest.mark.asyncio()
    async def test_fetch_price_no_items(self):
        """Тест при отсутствии предметов."""
        from src.dmarket.realtime_price_watcher import RealtimePriceWatcher

        mock_api = MagicMock()
        mock_api._request = AsyncMock(return_value={"items": []})

        watcher = RealtimePriceWatcher(mock_api)
        price = await watcher._fetch_item_price("item123", "csgo")
        assert price is None

    @pytest.mark.asyncio()
    async def test_fetch_price_error(self):
        """Тест при ошибке API."""
        from src.dmarket.realtime_price_watcher import RealtimePriceWatcher

        mock_api = MagicMock()
        mock_api._request = AsyncMock(side_effect=Exception("API Error"))

        watcher = RealtimePriceWatcher(mock_api)
        price = await watcher._fetch_item_price("item123", "csgo")
        assert price is None


class TestWatchItem:
    """Тесты метода watch_item."""

    def test_watch_item_basic(self):
        """Тест добавления предмета."""
        from src.dmarket.realtime_price_watcher import RealtimePriceWatcher

        mock_api = MagicMock()
        watcher = RealtimePriceWatcher(mock_api)

        watcher.watch_item("item123")
        assert "item123" in watcher.watched_items

    def test_watch_item_with_price(self):
        """Тест добавления предмета с начальной ценой."""
        from src.dmarket.realtime_price_watcher import RealtimePriceWatcher

        mock_api = MagicMock()
        watcher = RealtimePriceWatcher(mock_api)

        watcher.watch_item("item123", initial_price=50.0)
        assert "item123" in watcher.watched_items
        assert watcher.price_cache.get("item123") == 50.0
        assert len(watcher.price_history.get("item123", [])) == 1


class TestUnwatchItem:
    """Тесты метода unwatch_item."""

    def test_unwatch_item_basic(self):
        """Тест удаления предмета."""
        from src.dmarket.realtime_price_watcher import RealtimePriceWatcher

        mock_api = MagicMock()
        watcher = RealtimePriceWatcher(mock_api)

        watcher.watch_item("item123")
        watcher.unwatch_item("item123")
        assert "item123" not in watcher.watched_items

    def test_unwatch_item_with_cache(self):
        """Тест удаления предмета с кешем."""
        from src.dmarket.realtime_price_watcher import RealtimePriceWatcher

        mock_api = MagicMock()
        watcher = RealtimePriceWatcher(mock_api)

        watcher.watch_item("item123", initial_price=50.0)
        watcher.unwatch_item("item123")
        assert "item123" not in watcher.watched_items
        assert watcher.price_cache.get("item123") is None

    def test_unwatch_item_not_exists(self):
        """Тест удаления несуществующего предмета."""
        from src.dmarket.realtime_price_watcher import RealtimePriceWatcher

        mock_api = MagicMock()
        watcher = RealtimePriceWatcher(mock_api)

        # Не должно выбросить исключение
        watcher.unwatch_item("nonexistent")


class TestAddRemovePriceAlert:
    """Тесты методов add_price_alert и remove_price_alert."""

    def test_add_price_alert(self):
        """Тест добавления оповещения."""
        from src.dmarket.realtime_price_watcher import PriceAlert, RealtimePriceWatcher

        mock_api = MagicMock()
        watcher = RealtimePriceWatcher(mock_api)

        alert = PriceAlert(
            item_id="item123",
            market_hash_name="Test Item",
            target_price=50.0,
        )
        watcher.add_price_alert(alert)

        assert len(watcher.price_alerts.get("item123", [])) == 1
        assert "item123" in watcher.watched_items

    def test_remove_price_alert(self):
        """Тест удаления оповещения."""
        from src.dmarket.realtime_price_watcher import PriceAlert, RealtimePriceWatcher

        mock_api = MagicMock()
        watcher = RealtimePriceWatcher(mock_api)

        alert = PriceAlert(
            item_id="item123",
            market_hash_name="Test Item",
            target_price=50.0,
        )
        watcher.add_price_alert(alert)
        watcher.remove_price_alert(alert)

        assert "item123" not in watcher.price_alerts

    def test_remove_price_alert_not_exists(self):
        """Тест удаления несуществующего оповещения."""
        from src.dmarket.realtime_price_watcher import PriceAlert, RealtimePriceWatcher

        mock_api = MagicMock()
        watcher = RealtimePriceWatcher(mock_api)

        alert = PriceAlert(
            item_id="item123",
            market_hash_name="Test Item",
            target_price=50.0,
        )
        # Не должно выбросить исключение
        watcher.remove_price_alert(alert)


class TestRegisterHandlers:
    """Тесты регистрации обработчиков."""

    def test_register_price_change_handler(self):
        """Тест регистрации обработчика изменения цены."""
        from src.dmarket.realtime_price_watcher import RealtimePriceWatcher

        mock_api = MagicMock()
        watcher = RealtimePriceWatcher(mock_api)

        def handler(item_id, old_price, new_price):
            pass

        watcher.register_price_change_handler(handler, "item123")
        assert handler in watcher.price_change_handlers.get("item123", [])

    def test_register_global_price_change_handler(self):
        """Тест регистрации глобального обработчика."""
        from src.dmarket.realtime_price_watcher import RealtimePriceWatcher

        mock_api = MagicMock()
        watcher = RealtimePriceWatcher(mock_api)

        def handler(item_id, old_price, new_price):
            pass

        watcher.register_price_change_handler(handler)
        assert handler in watcher.price_change_handlers.get("*", [])

    def test_register_alert_handler(self):
        """Тест регистрации обработчика оповещений."""
        from src.dmarket.realtime_price_watcher import RealtimePriceWatcher

        mock_api = MagicMock()
        watcher = RealtimePriceWatcher(mock_api)

        def handler(alert, current_price):
            pass

        watcher.register_alert_handler(handler)
        assert handler in watcher.alert_handlers


class TestGetters:
    """Тесты геттеров."""

    def test_get_current_price(self):
        """Тест получения текущей цены."""
        from src.dmarket.realtime_price_watcher import RealtimePriceWatcher

        mock_api = MagicMock()
        watcher = RealtimePriceWatcher(mock_api)

        watcher.price_cache["item123"] = 50.0
        assert watcher.get_current_price("item123") == 50.0
        assert watcher.get_current_price("nonexistent") is None

    def test_get_price_history(self):
        """Тест получения истории цен."""
        from src.dmarket.realtime_price_watcher import RealtimePriceWatcher

        mock_api = MagicMock()
        watcher = RealtimePriceWatcher(mock_api)

        watcher._add_to_price_history("item123", 50.0)
        watcher._add_to_price_history("item123", 51.0)
        watcher._add_to_price_history("item123", 52.0)

        history = watcher.get_price_history("item123")
        assert len(history) == 3

        limited = watcher.get_price_history("item123", limit=2)
        assert len(limited) == 2

    def test_get_all_alerts(self):
        """Тест получения всех оповещений."""
        from src.dmarket.realtime_price_watcher import PriceAlert, RealtimePriceWatcher

        mock_api = MagicMock()
        watcher = RealtimePriceWatcher(mock_api)

        alert = PriceAlert(
            item_id="item123",
            market_hash_name="Test Item",
            target_price=50.0,
        )
        watcher.add_price_alert(alert)

        alerts = watcher.get_all_alerts()
        assert len(alerts) == 1
        assert "item123" in alerts

    def test_get_triggered_alerts(self):
        """Тест получения сработавших оповещений."""
        from src.dmarket.realtime_price_watcher import PriceAlert, RealtimePriceWatcher

        mock_api = MagicMock()
        watcher = RealtimePriceWatcher(mock_api)

        alert1 = PriceAlert(
            item_id="item123",
            market_hash_name="Test Item 1",
            target_price=50.0,
        )
        alert1.is_triggered = True

        alert2 = PriceAlert(
            item_id="item456",
            market_hash_name="Test Item 2",
            target_price=60.0,
        )

        watcher.add_price_alert(alert1)
        watcher.add_price_alert(alert2)

        triggered = watcher.get_triggered_alerts()
        assert len(triggered) == 1
        assert triggered[0] == alert1

    def test_reset_triggered_alerts(self):
        """Тест сброса сработавших оповещений."""
        from src.dmarket.realtime_price_watcher import PriceAlert, RealtimePriceWatcher

        mock_api = MagicMock()
        watcher = RealtimePriceWatcher(mock_api)

        alert1 = PriceAlert(
            item_id="item123",
            market_hash_name="Test Item 1",
            target_price=50.0,
        )
        alert1.is_triggered = True

        alert2 = PriceAlert(
            item_id="item456",
            market_hash_name="Test Item 2",
            target_price=60.0,
        )
        alert2.is_triggered = True

        watcher.add_price_alert(alert1)
        watcher.add_price_alert(alert2)

        count = watcher.reset_triggered_alerts()
        assert count == 2
        assert alert1.is_triggered is False
        assert alert2.is_triggered is False

    def test_get_item_metadata(self):
        """Тест получения метаданных."""
        from src.dmarket.realtime_price_watcher import RealtimePriceWatcher

        mock_api = MagicMock()
        watcher = RealtimePriceWatcher(mock_api)

        watcher.item_metadata["item123"] = {"title": "Test", "gameId": "csgo"}

        metadata = watcher.get_item_metadata("item123")
        assert metadata["title"] == "Test"

        empty_metadata = watcher.get_item_metadata("nonexistent")
        assert empty_metadata == {}


# =========================================
# TestEdgeCases
# =========================================


class TestEdgeCases:
    """Тесты граничных случаев."""

    def test_unicode_item_id(self):
        """Тест unicode в ID предмета."""
        from src.dmarket.realtime_price_watcher import RealtimePriceWatcher

        mock_api = MagicMock()
        watcher = RealtimePriceWatcher(mock_api)

        watcher.watch_item("предмет_123")
        assert "предмет_123" in watcher.watched_items

    def test_unicode_market_hash_name(self):
        """Тест unicode в названии предмета."""
        from src.dmarket.realtime_price_watcher import PriceAlert

        alert = PriceAlert(
            item_id="item123",
            market_hash_name="АК-47 | Кровавый спорт",
            target_price=50.0,
        )
        assert alert.market_hash_name == "АК-47 | Кровавый спорт"

    def test_zero_target_price(self):
        """Тест нулевой целевой цены."""
        from src.dmarket.realtime_price_watcher import PriceAlert

        alert = PriceAlert(
            item_id="item123",
            market_hash_name="Free Item",
            target_price=0.0,
            condition="below",
        )
        # Любая положительная цена будет выше нуля
        result = alert.check_condition(0.01)
        assert result is False  # 0.01 не <= 0.0

    def test_negative_price_check(self):
        """Тест проверки отрицательной цены."""
        from src.dmarket.realtime_price_watcher import PriceAlert

        alert = PriceAlert(
            item_id="item123",
            market_hash_name="Test Item",
            target_price=50.0,
            condition="below",
        )
        result = alert.check_condition(-10.0)
        assert result is True  # -10 <= 50

    def test_very_large_price(self):
        """Тест очень большой цены."""
        from src.dmarket.realtime_price_watcher import PriceAlert

        alert = PriceAlert(
            item_id="item123",
            market_hash_name="Expensive Item",
            target_price=1000000.0,
            condition="above",
        )
        result = alert.check_condition(999999.99)
        assert result is False

    def test_very_small_price(self):
        """Тест очень маленькой цены."""
        from src.dmarket.realtime_price_watcher import PriceAlert

        alert = PriceAlert(
            item_id="item123",
            market_hash_name="Cheap Item",
            target_price=0.01,
            condition="below",
        )
        result = alert.check_condition(0.001)
        assert result is True


# =========================================
# TestIntegration
# =========================================


class TestIntegration:
    """Интеграционные тесты."""

    @pytest.mark.asyncio()
    async def test_full_alert_workflow(self):
        """Тест полного рабочего процесса с оповещениями."""
        from src.dmarket.realtime_price_watcher import PriceAlert, RealtimePriceWatcher

        mock_api = MagicMock()
        watcher = RealtimePriceWatcher(mock_api)

        # Создаём оповещение
        alert = PriceAlert(
            item_id="item123",
            market_hash_name="Test Item",
            target_price=50.0,
            condition="below",
        )
        watcher.add_price_alert(alert)

        # Регистрируем обработчик
        triggered_alerts = []

        async def alert_handler(alert, current_price):
            triggered_alerts.append((alert.market_hash_name, current_price))

        watcher.register_alert_handler(alert_handler)

        # Проверяем оповещения
        await watcher._check_alerts("item123", 60.0)  # Не должно сработать
        assert len(triggered_alerts) == 0

        await watcher._check_alerts("item123", 45.0)  # Должно сработать
        assert len(triggered_alerts) == 1
        assert triggered_alerts[0][1] == 45.0

    @pytest.mark.asyncio()
    async def test_full_price_watch_workflow(self):
        """Тест полного рабочего процесса отслеживания цен."""
        from src.dmarket.realtime_price_watcher import RealtimePriceWatcher

        mock_api = MagicMock()
        watcher = RealtimePriceWatcher(mock_api)

        # Добавляем предмет
        watcher.watch_item("item123", initial_price=50.0)

        # Регистрируем обработчик
        price_changes = []

        async def price_handler(item_id, old_price, new_price):
            price_changes.append((item_id, old_price, new_price))

        watcher.register_price_change_handler(price_handler, "item123")

        # Симулируем изменение цены
        await watcher._process_price_change("item123", 50.0, 55.0)
        assert len(price_changes) == 1
        assert price_changes[0] == ("item123", 50.0, 55.0)

        # Проверяем историю
        history = watcher.get_price_history("item123")
        assert len(history) == 1  # Только начальная цена

    @pytest.mark.asyncio()
    async def test_multiple_items_and_alerts(self):
        """Тест с несколькими предметами и оповещениями."""
        from src.dmarket.realtime_price_watcher import PriceAlert, RealtimePriceWatcher

        mock_api = MagicMock()
        watcher = RealtimePriceWatcher(mock_api)

        # Добавляем несколько предметов
        for i in range(3):
            watcher.watch_item(f"item{i}", initial_price=float(i * 10 + 10))

            alert = PriceAlert(
                item_id=f"item{i}",
                market_hash_name=f"Test Item {i}",
                target_price=float(i * 10 + 5),
                condition="below",
            )
            watcher.add_price_alert(alert)

        # Проверяем что все добавлены
        assert len(watcher.watched_items) == 3
        assert len(watcher.get_all_alerts()) == 3

        # Удаляем один
        watcher.unwatch_item("item1")
        assert len(watcher.watched_items) == 2
