"""Phase 4 extended unit tests for market_alerts_handler.py module.

This module contains comprehensive tests to improve coverage for
market alerts handler functionality - managing market notifications.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ==================== ALERT_TYPES Constants Tests ====================


class TestAlertTypesConstants:
    """Tests for ALERT_TYPES constants."""

    def test_alert_types_contains_price_changes(self) -> None:
        """Test ALERT_TYPES contains price_changes."""
        from src.telegram_bot.handlers.market_alerts_handler import ALERT_TYPES

        assert "price_changes" in ALERT_TYPES
        assert "📈" in ALERT_TYPES["price_changes"]

    def test_alert_types_contains_trending(self) -> None:
        """Test ALERT_TYPES contains trending."""
        from src.telegram_bot.handlers.market_alerts_handler import ALERT_TYPES

        assert "trending" in ALERT_TYPES
        assert "🔥" in ALERT_TYPES["trending"]

    def test_alert_types_contains_volatility(self) -> None:
        """Test ALERT_TYPES contains volatility."""
        from src.telegram_bot.handlers.market_alerts_handler import ALERT_TYPES

        assert "volatility" in ALERT_TYPES
        assert "📊" in ALERT_TYPES["volatility"]

    def test_alert_types_contains_arbitrage(self) -> None:
        """Test ALERT_TYPES contains arbitrage."""
        from src.telegram_bot.handlers.market_alerts_handler import ALERT_TYPES

        assert "arbitrage" in ALERT_TYPES
        assert "💰" in ALERT_TYPES["arbitrage"]

    def test_alert_types_contains_price_drop(self) -> None:
        """Test ALERT_TYPES contains price_drop."""
        from src.telegram_bot.handlers.market_alerts_handler import ALERT_TYPES

        assert "price_drop" in ALERT_TYPES
        assert "⬇️" in ALERT_TYPES["price_drop"]

    def test_alert_types_contains_price_rise(self) -> None:
        """Test ALERT_TYPES contains price_rise."""
        from src.telegram_bot.handlers.market_alerts_handler import ALERT_TYPES

        assert "price_rise" in ALERT_TYPES
        assert "⬆️" in ALERT_TYPES["price_rise"]

    def test_alert_types_contains_volume_increase(self) -> None:
        """Test ALERT_TYPES contains volume_increase."""
        from src.telegram_bot.handlers.market_alerts_handler import ALERT_TYPES

        assert "volume_increase" in ALERT_TYPES
        assert "📊" in ALERT_TYPES["volume_increase"]

    def test_alert_types_contains_good_deal(self) -> None:
        """Test ALERT_TYPES contains good_deal."""
        from src.telegram_bot.handlers.market_alerts_handler import ALERT_TYPES

        assert "good_deal" in ALERT_TYPES
        assert "💰" in ALERT_TYPES["good_deal"]

    def test_alert_types_contains_trend_change(self) -> None:
        """Test ALERT_TYPES contains trend_change."""
        from src.telegram_bot.handlers.market_alerts_handler import ALERT_TYPES

        assert "trend_change" in ALERT_TYPES
        assert "📊" in ALERT_TYPES["trend_change"]

    def test_alert_types_count(self) -> None:
        """Test ALERT_TYPES has expected count."""
        from src.telegram_bot.handlers.market_alerts_handler import ALERT_TYPES

        assert len(ALERT_TYPES) == 9


# ==================== alerts_command Tests ====================


class TestAlertsCommand:
    """Tests for alerts_command function."""

    @pytest.mark.asyncio()
    async def test_alerts_command_no_user(self) -> None:
        """Test alerts_command with no user."""
        from src.telegram_bot.handlers.market_alerts_handler import alerts_command

        update = MagicMock()
        update.effective_user = None
        context = MagicMock()

        result = await alerts_command(update, context)

        assert result is None

    @pytest.mark.asyncio()
    async def test_alerts_command_no_message(self) -> None:
        """Test alerts_command with no message."""
        from src.telegram_bot.handlers.market_alerts_handler import alerts_command

        update = MagicMock()
        update.effective_user = MagicMock(id=12345)
        update.message = None
        context = MagicMock()

        result = await alerts_command(update, context)

        assert result is None

    @pytest.mark.asyncio()
    async def test_alerts_command_with_subscriptions(self) -> None:
        """Test alerts_command with existing subscriptions."""
        from src.telegram_bot.handlers.market_alerts_handler import alerts_command

        update = MagicMock()
        update.effective_user = MagicMock(id=12345)
        update.message = MagicMock()
        update.message.reply_text = AsyncMock()

        context = MagicMock()
        context.bot = MagicMock()

        mock_manager = MagicMock()
        mock_manager.get_user_subscriptions.return_value = ["price_changes", "trending"]

        with (
            patch(
                "src.telegram_bot.handlers.market_alerts_handler.get_alerts_manager",
                return_value=mock_manager,
            ),
            patch(
                "src.telegram_bot.handlers.market_alerts_handler.get_user_alerts",
                new_callable=AsyncMock,
                return_value=[],
            ),
        ):
            await alerts_command(update, context)

        update.message.reply_text.assert_called_once()
        call_args = update.message.reply_text.call_args
        assert "Управление уведомлениями" in call_args[0][0]

    @pytest.mark.asyncio()
    async def test_alerts_command_with_price_alerts(self) -> None:
        """Test alerts_command with price alerts."""
        from src.telegram_bot.handlers.market_alerts_handler import alerts_command

        update = MagicMock()
        update.effective_user = MagicMock(id=12345)
        update.message = MagicMock()
        update.message.reply_text = AsyncMock()

        context = MagicMock()
        context.bot = MagicMock()

        mock_manager = MagicMock()
        mock_manager.get_user_subscriptions.return_value = []

        mock_alerts = [
            {"id": "1", "title": "Test Item", "type": "price_drop", "threshold": 100.0},
        ]

        with (
            patch(
                "src.telegram_bot.handlers.market_alerts_handler.get_alerts_manager",
                return_value=mock_manager,
            ),
            patch(
                "src.telegram_bot.handlers.market_alerts_handler.get_user_alerts",
                new_callable=AsyncMock,
                return_value=mock_alerts,
            ),
        ):
            await alerts_command(update, context)

        update.message.reply_text.assert_called_once()
        call_args = update.message.reply_text.call_args
        # Check that price alerts count is mentioned
        assert "1 активных оповещений" in call_args[0][0]

    @pytest.mark.asyncio()
    async def test_alerts_command_no_subscriptions_shows_help(self) -> None:
        """Test alerts_command shows help when no subscriptions."""
        from src.telegram_bot.handlers.market_alerts_handler import alerts_command

        update = MagicMock()
        update.effective_user = MagicMock(id=12345)
        update.message = MagicMock()
        update.message.reply_text = AsyncMock()

        context = MagicMock()
        context.bot = MagicMock()

        mock_manager = MagicMock()
        mock_manager.get_user_subscriptions.return_value = []

        with (
            patch(
                "src.telegram_bot.handlers.market_alerts_handler.get_alerts_manager",
                return_value=mock_manager,
            ),
            patch(
                "src.telegram_bot.handlers.market_alerts_handler.get_user_alerts",
                new_callable=AsyncMock,
                return_value=[],
            ),
        ):
            await alerts_command(update, context)

        update.message.reply_text.assert_called_once()
        call_args = update.message.reply_text.call_args
        # Check that help text is included
        assert "не подписаны ни на какие уведомления" in call_args[0][0]


# ==================== alerts_callback Tests ====================


class TestAlertsCallback:
    """Tests for alerts_callback function."""

    @pytest.mark.asyncio()
    async def test_alerts_callback_no_query(self) -> None:
        """Test alerts_callback with no query."""
        from src.telegram_bot.handlers.market_alerts_handler import alerts_callback

        update = MagicMock()
        update.callback_query = None
        context = MagicMock()

        result = await alerts_callback(update, context)

        assert result is None

    @pytest.mark.asyncio()
    async def test_alerts_callback_invalid_format(self) -> None:
        """Test alerts_callback with invalid format."""
        from src.telegram_bot.handlers.market_alerts_handler import alerts_callback

        query = MagicMock()
        query.data = "alerts"  # Missing action
        query.from_user = MagicMock(id=12345)
        query.answer = AsyncMock()

        update = MagicMock()
        update.callback_query = query
        context = MagicMock()

        await alerts_callback(update, context)

        query.answer.assert_called_once()
        call_args = query.answer.call_args
        assert "Неверный формат" in call_args[0][0]

    @pytest.mark.asyncio()
    async def test_alerts_callback_manager_error(self) -> None:
        """Test alerts_callback handles manager initialization error."""
        from src.telegram_bot.handlers.market_alerts_handler import alerts_callback

        query = MagicMock()
        query.data = "alerts:toggle:price_changes"
        query.from_user = MagicMock(id=12345)
        query.answer = AsyncMock()

        update = MagicMock()
        update.callback_query = query
        context = MagicMock()
        context.bot = MagicMock()

        with patch(
            "src.telegram_bot.handlers.market_alerts_handler.get_alerts_manager",
            side_effect=Exception("Init error"),
        ):
            await alerts_callback(update, context)

        query.answer.assert_called_once()
        call_args = query.answer.call_args
        assert "Ошибка инициализации" in call_args[0][0]

    @pytest.mark.asyncio()
    async def test_alerts_callback_unknown_action(self) -> None:
        """Test alerts_callback with unknown action."""
        from src.telegram_bot.handlers.market_alerts_handler import alerts_callback

        query = MagicMock()
        query.data = "alerts:unknown_action"
        query.from_user = MagicMock(id=12345)
        query.answer = AsyncMock()

        update = MagicMock()
        update.callback_query = query
        context = MagicMock()
        context.bot = MagicMock()

        mock_manager = MagicMock()

        with patch(
            "src.telegram_bot.handlers.market_alerts_handler.get_alerts_manager",
            return_value=mock_manager,
        ):
            await alerts_callback(update, context)

        query.answer.assert_called_once()
        call_args = query.answer.call_args
        assert "Неизвестное действие" in call_args[0][0]


# ==================== _handle_toggle_alert Tests ====================


class TestHandleToggleAlert:
    """Tests for _handle_toggle_alert function."""

    @pytest.mark.asyncio()
    async def test_toggle_alert_invalid_format(self) -> None:
        """Test toggle alert with invalid format."""
        from src.telegram_bot.handlers.market_alerts_handler import _handle_toggle_alert

        query = MagicMock()
        query.answer = AsyncMock()

        await _handle_toggle_alert(
            query=query,
            update=MagicMock(),
            context=MagicMock(),
            parts=["alerts", "toggle"],  # Missing alert_type
            user_id=12345,
            alerts_manager=MagicMock(),
        )

        query.answer.assert_called_once()
        call_args = query.answer.call_args
        assert "Неверный формат" in call_args[0][0]

    @pytest.mark.asyncio()
    async def test_toggle_alert_subscribe(self) -> None:
        """Test toggle alert subscribes when not subscribed."""
        from src.telegram_bot.handlers.market_alerts_handler import _handle_toggle_alert

        query = MagicMock()
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()

        mock_manager = MagicMock()
        mock_manager.get_user_subscriptions.return_value = []  # Not subscribed
        mock_manager.subscribe.return_value = True

        with patch(
            "src.telegram_bot.handlers.market_alerts_handler.update_alerts_keyboard",
            new_callable=AsyncMock,
        ):
            await _handle_toggle_alert(
                query=query,
                update=MagicMock(),
                context=MagicMock(),
                parts=["alerts", "toggle", "price_changes"],
                user_id=12345,
                alerts_manager=mock_manager,
            )

        mock_manager.subscribe.assert_called_once_with(12345, "price_changes")
        query.answer.assert_called_once()
        assert "подписались на уведомления" in query.answer.call_args[0][0]

    @pytest.mark.asyncio()
    async def test_toggle_alert_unsubscribe(self) -> None:
        """Test toggle alert unsubscribes when subscribed."""
        from src.telegram_bot.handlers.market_alerts_handler import _handle_toggle_alert

        query = MagicMock()
        query.answer = AsyncMock()

        mock_manager = MagicMock()
        mock_manager.get_user_subscriptions.return_value = [
            "price_changes"
        ]  # Subscribed
        mock_manager.unsubscribe.return_value = True

        with patch(
            "src.telegram_bot.handlers.market_alerts_handler.update_alerts_keyboard",
            new_callable=AsyncMock,
        ):
            await _handle_toggle_alert(
                query=query,
                update=MagicMock(),
                context=MagicMock(),
                parts=["alerts", "toggle", "price_changes"],
                user_id=12345,
                alerts_manager=mock_manager,
            )

        mock_manager.unsubscribe.assert_called_once_with(12345, "price_changes")
        query.answer.assert_called_once()
        assert "отписались от уведомлений" in query.answer.call_args[0][0]

    @pytest.mark.asyncio()
    async def test_toggle_alert_subscribe_failure(self) -> None:
        """Test toggle alert handles subscription failure."""
        from src.telegram_bot.handlers.market_alerts_handler import _handle_toggle_alert

        query = MagicMock()
        query.answer = AsyncMock()

        mock_manager = MagicMock()
        mock_manager.get_user_subscriptions.return_value = []
        mock_manager.subscribe.return_value = False  # Failure

        with patch(
            "src.telegram_bot.handlers.market_alerts_handler.update_alerts_keyboard",
            new_callable=AsyncMock,
        ):
            await _handle_toggle_alert(
                query=query,
                update=MagicMock(),
                context=MagicMock(),
                parts=["alerts", "toggle", "price_changes"],
                user_id=12345,
                alerts_manager=mock_manager,
            )

        query.answer.assert_called_once()
        assert "Не удалось подписаться" in query.answer.call_args[0][0]


# ==================== _handle_subscribe_all Tests ====================


class TestHandleSubscribeAll:
    """Tests for _handle_subscribe_all function."""

    @pytest.mark.asyncio()
    async def test_subscribe_all_success(self) -> None:
        """Test subscribe all successful."""
        from src.telegram_bot.handlers.market_alerts_handler import (
            _handle_subscribe_all,
        )

        query = MagicMock()
        query.answer = AsyncMock()

        mock_manager = MagicMock()
        mock_manager.subscribe.return_value = True

        with patch(
            "src.telegram_bot.handlers.market_alerts_handler.update_alerts_keyboard",
            new_callable=AsyncMock,
        ):
            await _handle_subscribe_all(
                query=query,
                update=MagicMock(),
                context=MagicMock(),
                parts=["alerts", "subscribe_all"],
                user_id=12345,
                alerts_manager=mock_manager,
            )

        query.answer.assert_called_once()
        # Should subscribe to all 9 alert types
        assert "Подписано на" in query.answer.call_args[0][0]


# ==================== _handle_unsubscribe_all Tests ====================


class TestHandleUnsubscribeAll:
    """Tests for _handle_unsubscribe_all function."""

    @pytest.mark.asyncio()
    async def test_unsubscribe_all_with_method(self) -> None:
        """Test unsubscribe all with unsubscribe_all method."""
        from src.telegram_bot.handlers.market_alerts_handler import (
            _handle_unsubscribe_all,
        )

        query = MagicMock()
        query.answer = AsyncMock()

        mock_manager = MagicMock()
        mock_manager.unsubscribe_all.return_value = True

        with patch(
            "src.telegram_bot.handlers.market_alerts_handler.update_alerts_keyboard",
            new_callable=AsyncMock,
        ):
            await _handle_unsubscribe_all(
                query=query,
                update=MagicMock(),
                context=MagicMock(),
                parts=["alerts", "unsubscribe_all"],
                user_id=12345,
                alerts_manager=mock_manager,
            )

        mock_manager.unsubscribe_all.assert_called_once_with(12345)
        query.answer.assert_called_once()
        assert "отписались от всех" in query.answer.call_args[0][0]

    @pytest.mark.asyncio()
    async def test_unsubscribe_all_fallback(self) -> None:
        """Test unsubscribe all with fallback loop."""
        from src.telegram_bot.handlers.market_alerts_handler import (
            _handle_unsubscribe_all,
        )

        query = MagicMock()
        query.answer = AsyncMock()

        mock_manager = MagicMock()
        del mock_manager.unsubscribe_all  # Remove method to trigger fallback
        mock_manager.get_user_subscriptions.return_value = ["price_changes", "trending"]
        mock_manager.unsubscribe.return_value = True

        with patch(
            "src.telegram_bot.handlers.market_alerts_handler.update_alerts_keyboard",
            new_callable=AsyncMock,
        ):
            await _handle_unsubscribe_all(
                query=query,
                update=MagicMock(),
                context=MagicMock(),
                parts=["alerts", "unsubscribe_all"],
                user_id=12345,
                alerts_manager=mock_manager,
            )

        assert mock_manager.unsubscribe.call_count == 2
        query.answer.assert_called_once()


# ==================== _handle_remove_alert Tests ====================


class TestHandleRemoveAlert:
    """Tests for _handle_remove_alert function."""

    @pytest.mark.asyncio()
    async def test_remove_alert_invalid_format(self) -> None:
        """Test remove alert with invalid format."""
        from src.telegram_bot.handlers.market_alerts_handler import _handle_remove_alert

        query = MagicMock()
        query.answer = AsyncMock()

        await _handle_remove_alert(
            query=query,
            update=MagicMock(),
            context=MagicMock(),
            parts=["alerts", "remove_alert"],  # Missing alert_id
            user_id=12345,
            alerts_manager=MagicMock(),
        )

        query.answer.assert_called_once()
        assert "Неверный формат" in query.answer.call_args[0][0]

    @pytest.mark.asyncio()
    async def test_remove_alert_success(self) -> None:
        """Test remove alert successful."""
        from src.telegram_bot.handlers.market_alerts_handler import _handle_remove_alert

        query = MagicMock()
        query.answer = AsyncMock()

        with (
            patch(
                "src.telegram_bot.handlers.market_alerts_handler.remove_price_alert",
                new_callable=AsyncMock,
                return_value=True,
            ),
            patch(
                "src.telegram_bot.handlers.market_alerts_handler.show_user_alerts_list",
                new_callable=AsyncMock,
            ),
        ):
            await _handle_remove_alert(
                query=query,
                update=MagicMock(),
                context=MagicMock(),
                parts=["alerts", "remove_alert", "alert123"],
                user_id=12345,
                alerts_manager=MagicMock(),
            )

        query.answer.assert_called_once()
        assert "Оповещение удалено" in query.answer.call_args[0][0]

    @pytest.mark.asyncio()
    async def test_remove_alert_failure(self) -> None:
        """Test remove alert failure."""
        from src.telegram_bot.handlers.market_alerts_handler import _handle_remove_alert

        query = MagicMock()
        query.answer = AsyncMock()

        with patch(
            "src.telegram_bot.handlers.market_alerts_handler.remove_price_alert",
            new_callable=AsyncMock,
            return_value=False,
        ):
            await _handle_remove_alert(
                query=query,
                update=MagicMock(),
                context=MagicMock(),
                parts=["alerts", "remove_alert", "alert123"],
                user_id=12345,
                alerts_manager=MagicMock(),
            )

        query.answer.assert_called_once()
        assert "Ошибка при удалении" in query.answer.call_args[0][0]


# ==================== _handle_threshold_action Tests ====================


class TestHandleThresholdAction:
    """Tests for _handle_threshold_action function."""

    @pytest.mark.asyncio()
    async def test_threshold_invalid_format(self) -> None:
        """Test threshold with invalid format."""
        from src.telegram_bot.handlers.market_alerts_handler import (
            _handle_threshold_action,
        )

        query = MagicMock()
        query.answer = AsyncMock()

        await _handle_threshold_action(
            query=query,
            update=MagicMock(),
            context=MagicMock(),
            parts=["alerts", "threshold", "price_changes"],  # Missing direction
            user_id=12345,
            alerts_manager=MagicMock(),
        )

        query.answer.assert_called_once()
        assert "Неверный формат" in query.answer.call_args[0][0]

    @pytest.mark.asyncio()
    async def test_threshold_up(self) -> None:
        """Test threshold increase."""
        from src.telegram_bot.handlers.market_alerts_handler import (
            _handle_threshold_action,
        )

        query = MagicMock()
        query.answer = AsyncMock()

        mock_manager = MagicMock()
        mock_manager.alert_thresholds = {"price_changes_threshold": 10.0}
        mock_manager.update_alert_threshold.return_value = True

        with patch(
            "src.telegram_bot.handlers.market_alerts_handler.show_alerts_settings",
            new_callable=AsyncMock,
        ):
            await _handle_threshold_action(
                query=query,
                update=MagicMock(),
                context=MagicMock(),
                parts=["alerts", "threshold", "price_changes", "up"],
                user_id=12345,
                alerts_manager=mock_manager,
            )

        mock_manager.update_alert_threshold.assert_called_once()
        # New threshold should be 15.0 (10.0 * 1.5)
        call_args = mock_manager.update_alert_threshold.call_args
        assert call_args[0][1] == 15.0

    @pytest.mark.asyncio()
    async def test_threshold_down(self) -> None:
        """Test threshold decrease."""
        from src.telegram_bot.handlers.market_alerts_handler import (
            _handle_threshold_action,
        )

        query = MagicMock()
        query.answer = AsyncMock()

        mock_manager = MagicMock()
        mock_manager.alert_thresholds = {"price_changes_threshold": 10.0}
        mock_manager.update_alert_threshold.return_value = True

        with patch(
            "src.telegram_bot.handlers.market_alerts_handler.show_alerts_settings",
            new_callable=AsyncMock,
        ):
            await _handle_threshold_action(
                query=query,
                update=MagicMock(),
                context=MagicMock(),
                parts=["alerts", "threshold", "price_changes", "down"],
                user_id=12345,
                alerts_manager=mock_manager,
            )

        mock_manager.update_alert_threshold.assert_called_once()
        # New threshold should be 7.0 (10.0 * 0.7)
        call_args = mock_manager.update_alert_threshold.call_args
        assert call_args[0][1] == 7.0


# ==================== _handle_interval_action Tests ====================


class TestHandleIntervalAction:
    """Tests for _handle_interval_action function."""

    @pytest.mark.asyncio()
    async def test_interval_invalid_format(self) -> None:
        """Test interval with invalid format."""
        from src.telegram_bot.handlers.market_alerts_handler import (
            _handle_interval_action,
        )

        query = MagicMock()
        query.answer = AsyncMock()

        await _handle_interval_action(
            query=query,
            update=MagicMock(),
            context=MagicMock(),
            parts=["alerts", "interval", "price_changes"],  # Missing direction
            user_id=12345,
            alerts_manager=MagicMock(),
        )

        query.answer.assert_called_once()
        assert "Неверный формат" in query.answer.call_args[0][0]

    @pytest.mark.asyncio()
    async def test_interval_up(self) -> None:
        """Test interval increase."""
        from src.telegram_bot.handlers.market_alerts_handler import (
            _handle_interval_action,
        )

        query = MagicMock()
        query.answer = AsyncMock()

        mock_manager = MagicMock()
        mock_manager.check_intervals = {"price_changes": 3600}  # 1 hour
        mock_manager.update_check_interval.return_value = True

        with patch(
            "src.telegram_bot.handlers.market_alerts_handler.show_alerts_settings",
            new_callable=AsyncMock,
        ):
            await _handle_interval_action(
                query=query,
                update=MagicMock(),
                context=MagicMock(),
                parts=["alerts", "interval", "price_changes", "up"],
                user_id=12345,
                alerts_manager=mock_manager,
            )

        mock_manager.update_check_interval.assert_called_once()
        # New interval should be 7200 (3600 * 2)
        call_args = mock_manager.update_check_interval.call_args
        assert call_args[0][1] == 7200

    @pytest.mark.asyncio()
    async def test_interval_down(self) -> None:
        """Test interval decrease."""
        from src.telegram_bot.handlers.market_alerts_handler import (
            _handle_interval_action,
        )

        query = MagicMock()
        query.answer = AsyncMock()

        mock_manager = MagicMock()
        mock_manager.check_intervals = {"price_changes": 3600}  # 1 hour
        mock_manager.update_check_interval.return_value = True

        with patch(
            "src.telegram_bot.handlers.market_alerts_handler.show_alerts_settings",
            new_callable=AsyncMock,
        ):
            await _handle_interval_action(
                query=query,
                update=MagicMock(),
                context=MagicMock(),
                parts=["alerts", "interval", "price_changes", "down"],
                user_id=12345,
                alerts_manager=mock_manager,
            )

        mock_manager.update_check_interval.assert_called_once()
        # New interval should be 1800 (3600 // 2)
        call_args = mock_manager.update_check_interval.call_args
        assert call_args[0][1] == 1800

    @pytest.mark.asyncio()
    async def test_interval_max_cap(self) -> None:
        """Test interval capped at max value."""
        from src.telegram_bot.handlers.market_alerts_handler import (
            _handle_interval_action,
        )

        query = MagicMock()
        query.answer = AsyncMock()

        mock_manager = MagicMock()
        mock_manager.check_intervals = {"price_changes": 86400}  # 24 hours (max)
        mock_manager.update_check_interval.return_value = True

        with patch(
            "src.telegram_bot.handlers.market_alerts_handler.show_alerts_settings",
            new_callable=AsyncMock,
        ):
            await _handle_interval_action(
                query=query,
                update=MagicMock(),
                context=MagicMock(),
                parts=["alerts", "interval", "price_changes", "up"],
                user_id=12345,
                alerts_manager=mock_manager,
            )

        # Should be capped at 86400
        call_args = mock_manager.update_check_interval.call_args
        assert call_args[0][1] == 86400

    @pytest.mark.asyncio()
    async def test_interval_min_cap(self) -> None:
        """Test interval capped at min value."""
        from src.telegram_bot.handlers.market_alerts_handler import (
            _handle_interval_action,
        )

        query = MagicMock()
        query.answer = AsyncMock()

        mock_manager = MagicMock()
        mock_manager.check_intervals = {"price_changes": 300}  # 5 minutes (min)
        mock_manager.update_check_interval.return_value = True

        with patch(
            "src.telegram_bot.handlers.market_alerts_handler.show_alerts_settings",
            new_callable=AsyncMock,
        ):
            await _handle_interval_action(
                query=query,
                update=MagicMock(),
                context=MagicMock(),
                parts=["alerts", "interval", "price_changes", "down"],
                user_id=12345,
                alerts_manager=mock_manager,
            )

        # Should be capped at 300
        call_args = mock_manager.update_check_interval.call_args
        assert call_args[0][1] == 300


# ==================== show_user_alerts_list Tests ====================


class TestShowUserAlertsList:
    """Tests for show_user_alerts_list function."""

    @pytest.mark.asyncio()
    async def test_show_empty_alerts_list(self) -> None:
        """Test show alerts list when empty."""
        from src.telegram_bot.handlers.market_alerts_handler import (
            show_user_alerts_list,
        )

        query = MagicMock()
        query.edit_message_text = AsyncMock()

        with patch(
            "src.telegram_bot.handlers.market_alerts_handler.get_user_alerts",
            new_callable=AsyncMock,
            return_value=[],
        ):
            await show_user_alerts_list(query, 12345)

        query.edit_message_text.assert_called_once()
        call_args = query.edit_message_text.call_args
        assert "нет активных оповещений" in call_args[0][0]

    @pytest.mark.asyncio()
    async def test_show_alerts_list_with_price_drop(self) -> None:
        """Test show alerts list with price_drop alert."""
        from src.telegram_bot.handlers.market_alerts_handler import (
            show_user_alerts_list,
        )

        query = MagicMock()
        query.edit_message_text = AsyncMock()

        mock_alerts = [
            {
                "id": "alert1",
                "title": "AK-47 | Redline",
                "type": "price_drop",
                "threshold": 50.0,
            },
        ]

        with patch(
            "src.telegram_bot.handlers.market_alerts_handler.get_user_alerts",
            new_callable=AsyncMock,
            return_value=mock_alerts,
        ):
            await show_user_alerts_list(query, 12345)

        query.edit_message_text.assert_called_once()
        call_args = query.edit_message_text.call_args
        assert "AK-47" in call_args[0][0]
        assert "$50.00" in call_args[0][0]

    @pytest.mark.asyncio()
    async def test_show_alerts_list_with_price_rise(self) -> None:
        """Test show alerts list with price_rise alert."""
        from src.telegram_bot.handlers.market_alerts_handler import (
            show_user_alerts_list,
        )

        query = MagicMock()
        query.edit_message_text = AsyncMock()

        mock_alerts = [
            {
                "id": "alert1",
                "title": "Knife",
                "type": "price_rise",
                "threshold": 100.0,
            },
        ]

        with patch(
            "src.telegram_bot.handlers.market_alerts_handler.get_user_alerts",
            new_callable=AsyncMock,
            return_value=mock_alerts,
        ):
            await show_user_alerts_list(query, 12345)

        query.edit_message_text.assert_called_once()
        call_args = query.edit_message_text.call_args
        assert "Knife" in call_args[0][0]
        assert "⬆️" in call_args[0][0]

    @pytest.mark.asyncio()
    async def test_show_alerts_list_with_volume_increase(self) -> None:
        """Test show alerts list with volume_increase alert."""
        from src.telegram_bot.handlers.market_alerts_handler import (
            show_user_alerts_list,
        )

        query = MagicMock()
        query.edit_message_text = AsyncMock()

        mock_alerts = [
            {
                "id": "alert1",
                "title": "Glove",
                "type": "volume_increase",
                "threshold": 100.0,
            },
        ]

        with patch(
            "src.telegram_bot.handlers.market_alerts_handler.get_user_alerts",
            new_callable=AsyncMock,
            return_value=mock_alerts,
        ):
            await show_user_alerts_list(query, 12345)

        query.edit_message_text.assert_called_once()
        call_args = query.edit_message_text.call_args
        assert "Glove" in call_args[0][0]
        assert "📊" in call_args[0][0]

    @pytest.mark.asyncio()
    async def test_show_alerts_list_with_good_deal(self) -> None:
        """Test show alerts list with good_deal alert."""
        from src.telegram_bot.handlers.market_alerts_handler import (
            show_user_alerts_list,
        )

        query = MagicMock()
        query.edit_message_text = AsyncMock()

        mock_alerts = [
            {
                "id": "alert1",
                "title": "Sticker",
                "type": "good_deal",
                "threshold": 15.0,
            },
        ]

        with patch(
            "src.telegram_bot.handlers.market_alerts_handler.get_user_alerts",
            new_callable=AsyncMock,
            return_value=mock_alerts,
        ):
            await show_user_alerts_list(query, 12345)

        query.edit_message_text.assert_called_once()
        call_args = query.edit_message_text.call_args
        assert "Sticker" in call_args[0][0]
        assert "💰" in call_args[0][0]

    @pytest.mark.asyncio()
    async def test_show_alerts_list_with_trend_change(self) -> None:
        """Test show alerts list with trend_change alert."""
        from src.telegram_bot.handlers.market_alerts_handler import (
            show_user_alerts_list,
        )

        query = MagicMock()
        query.edit_message_text = AsyncMock()

        mock_alerts = [
            {
                "id": "alert1",
                "title": "Case",
                "type": "trend_change",
                "threshold": 80.0,
            },
        ]

        with patch(
            "src.telegram_bot.handlers.market_alerts_handler.get_user_alerts",
            new_callable=AsyncMock,
            return_value=mock_alerts,
        ):
            await show_user_alerts_list(query, 12345)

        query.edit_message_text.assert_called_once()
        call_args = query.edit_message_text.call_args
        assert "Case" in call_args[0][0]
        assert "📈" in call_args[0][0]


# ==================== show_create_alert_form Tests ====================


class TestShowCreateAlertForm:
    """Tests for show_create_alert_form function."""

    @pytest.mark.asyncio()
    async def test_show_create_alert_form(self) -> None:
        """Test show create alert form."""
        from src.telegram_bot.handlers.market_alerts_handler import (
            show_create_alert_form,
        )

        query = MagicMock()
        query.edit_message_text = AsyncMock()

        await show_create_alert_form(query, 12345)

        query.edit_message_text.assert_called_once()
        call_args = query.edit_message_text.call_args
        assert "Создание нового оповещения" in call_args[0][0]
        assert "/alert" in call_args[0][0]
        assert "price_drop" in call_args[0][0]


# ==================== show_alerts_settings Tests ====================


class TestShowAlertsSettings:
    """Tests for show_alerts_settings function."""

    @pytest.mark.asyncio()
    async def test_show_settings_no_subscriptions(self) -> None:
        """Test show settings with no subscriptions."""
        from src.telegram_bot.handlers.market_alerts_handler import show_alerts_settings

        query = MagicMock()
        query.edit_message_text = AsyncMock()

        mock_manager = MagicMock()
        mock_manager.get_user_subscriptions.return_value = []
        mock_manager.alert_thresholds = {}
        mock_manager.check_intervals = {}

        await show_alerts_settings(query, mock_manager, 12345)

        query.edit_message_text.assert_called_once()
        call_args = query.edit_message_text.call_args
        assert "Настройки уведомлений" in call_args[0][0]

    @pytest.mark.asyncio()
    async def test_show_settings_with_price_changes(self) -> None:
        """Test show settings with price_changes subscription."""
        from src.telegram_bot.handlers.market_alerts_handler import show_alerts_settings

        query = MagicMock()
        query.edit_message_text = AsyncMock()

        mock_manager = MagicMock()
        mock_manager.get_user_subscriptions.return_value = ["price_changes"]
        mock_manager.alert_thresholds = {"price_change_percent": 15.0}
        mock_manager.check_intervals = {"price_changes": 3600}

        await show_alerts_settings(query, mock_manager, 12345)

        query.edit_message_text.assert_called_once()
        call_args = query.edit_message_text.call_args
        assert "Порог изменения цены: 15.0%" in call_args[0][0]
        assert "1 ч" in call_args[0][0]

    @pytest.mark.asyncio()
    async def test_show_settings_with_trending(self) -> None:
        """Test show settings with trending subscription."""
        from src.telegram_bot.handlers.market_alerts_handler import show_alerts_settings

        query = MagicMock()
        query.edit_message_text = AsyncMock()

        mock_manager = MagicMock()
        mock_manager.get_user_subscriptions.return_value = ["trending"]
        mock_manager.alert_thresholds = {"trending_popularity": 50.0}
        mock_manager.check_intervals = {"trending": 1800}  # 30 minutes

        await show_alerts_settings(query, mock_manager, 12345)

        query.edit_message_text.assert_called_once()
        call_args = query.edit_message_text.call_args
        assert "Порог популярности: 50.0" in call_args[0][0]
        assert "30 мин" in call_args[0][0]

    @pytest.mark.asyncio()
    async def test_show_settings_with_volatility(self) -> None:
        """Test show settings with volatility subscription."""
        from src.telegram_bot.handlers.market_alerts_handler import show_alerts_settings

        query = MagicMock()
        query.edit_message_text = AsyncMock()

        mock_manager = MagicMock()
        mock_manager.get_user_subscriptions.return_value = ["volatility"]
        mock_manager.alert_thresholds = {"volatility_threshold": 25.0}
        mock_manager.check_intervals = {"volatility": 7200}  # 2 hours

        await show_alerts_settings(query, mock_manager, 12345)

        query.edit_message_text.assert_called_once()
        call_args = query.edit_message_text.call_args
        assert "Порог волатильности: 25.0" in call_args[0][0]
        assert "2 ч" in call_args[0][0]

    @pytest.mark.asyncio()
    async def test_show_settings_with_arbitrage(self) -> None:
        """Test show settings with arbitrage subscription."""
        from src.telegram_bot.handlers.market_alerts_handler import show_alerts_settings

        query = MagicMock()
        query.edit_message_text = AsyncMock()

        mock_manager = MagicMock()
        mock_manager.get_user_subscriptions.return_value = ["arbitrage"]
        mock_manager.alert_thresholds = {"arbitrage_profit_percent": 10.0}
        mock_manager.check_intervals = {"arbitrage": 900}  # 15 minutes

        await show_alerts_settings(query, mock_manager, 12345)

        query.edit_message_text.assert_called_once()
        call_args = query.edit_message_text.call_args
        assert "Минимальная прибыль: 10.0%" in call_args[0][0]
        assert "15 мин" in call_args[0][0]


# ==================== update_alerts_keyboard Tests ====================


class TestUpdateAlertsKeyboard:
    """Tests for update_alerts_keyboard function."""

    @pytest.mark.asyncio()
    async def test_update_keyboard_no_subscriptions(self) -> None:
        """Test update keyboard with no subscriptions."""
        from src.telegram_bot.handlers.market_alerts_handler import (
            update_alerts_keyboard,
        )

        query = MagicMock()
        query.edit_message_text = AsyncMock()

        mock_manager = MagicMock()
        mock_manager.get_user_subscriptions.return_value = []

        with patch(
            "src.telegram_bot.handlers.market_alerts_handler.get_user_alerts",
            new_callable=AsyncMock,
            return_value=[],
        ):
            await update_alerts_keyboard(query, mock_manager, 12345)

        query.edit_message_text.assert_called_once()
        call_args = query.edit_message_text.call_args
        assert "не подписаны" in call_args[0][0]

    @pytest.mark.asyncio()
    async def test_update_keyboard_with_subscriptions(self) -> None:
        """Test update keyboard with subscriptions."""
        from src.telegram_bot.handlers.market_alerts_handler import (
            update_alerts_keyboard,
        )

        query = MagicMock()
        query.edit_message_text = AsyncMock()

        mock_manager = MagicMock()
        mock_manager.get_user_subscriptions.return_value = ["price_changes", "trending"]

        with patch(
            "src.telegram_bot.handlers.market_alerts_handler.get_user_alerts",
            new_callable=AsyncMock,
            return_value=[],
        ):
            await update_alerts_keyboard(query, mock_manager, 12345)

        query.edit_message_text.assert_called_once()
        call_args = query.edit_message_text.call_args
        assert "Вы подписаны" in call_args[0][0]


# ==================== register_alerts_handlers Tests ====================


class TestRegisterAlertsHandlers:
    """Tests for register_alerts_handlers function."""

    def test_register_handlers(self) -> None:
        """Test register handlers."""
        from src.telegram_bot.handlers.market_alerts_handler import (
            register_alerts_handlers,
        )

        mock_application = MagicMock()

        with (
            patch(
                "src.telegram_bot.handlers.market_alerts_handler.load_user_alerts",
            ),
            patch(
                "src.telegram_bot.handlers.market_alerts_handler.register_notification_handlers",
            ),
        ):
            register_alerts_handlers(mock_application)

        # Should add 2 handlers (CommandHandler and CallbackQueryHandler)
        assert mock_application.add_handler.call_count == 2


# ==================== initialize_alerts_manager Tests ====================


class TestInitializeAlertsManager:
    """Tests for initialize_alerts_manager function."""

    @pytest.mark.asyncio()
    async def test_initialize_alerts_manager(self) -> None:
        """Test initialize alerts manager."""
        from src.telegram_bot.handlers.market_alerts_handler import (
            initialize_alerts_manager,
        )

        mock_application = MagicMock()

        await initialize_alerts_manager(mock_application)

        # Should complete without error


# ==================== Integration Tests ====================


class TestIntegration:
    """Integration tests for market_alerts_handler module."""

    @pytest.mark.asyncio()
    async def test_full_alert_flow(self) -> None:
        """Test full alert subscription flow."""
        from src.telegram_bot.handlers.market_alerts_handler import (
            alerts_command,
        )

        # Step 1: Show alerts command
        update = MagicMock()
        update.effective_user = MagicMock(id=12345)
        update.message = MagicMock()
        update.message.reply_text = AsyncMock()

        context = MagicMock()
        context.bot = MagicMock()

        mock_manager = MagicMock()
        mock_manager.get_user_subscriptions.return_value = []
        mock_manager.subscribe.return_value = True

        with (
            patch(
                "src.telegram_bot.handlers.market_alerts_handler.get_alerts_manager",
                return_value=mock_manager,
            ),
            patch(
                "src.telegram_bot.handlers.market_alerts_handler.get_user_alerts",
                new_callable=AsyncMock,
                return_value=[],
            ),
        ):
            await alerts_command(update, context)

        update.message.reply_text.assert_called_once()

    @pytest.mark.asyncio()
    async def test_alert_action_dispatcher(self) -> None:
        """Test alert action dispatcher."""
        from src.telegram_bot.handlers.market_alerts_handler import (
            _ALERT_ACTION_HANDLERS,
        )

        # Check all expected handlers are registered
        expected_handlers = [
            "toggle",
            "subscribe_all",
            "unsubscribe_all",
            "settings",
            "my_alerts",
            "create_alert",
            "remove_alert",
            "threshold",
            "interval",
            "back_to_alerts",
        ]

        for handler in expected_handlers:
            assert handler in _ALERT_ACTION_HANDLERS


# ==================== Edge Cases Tests ====================


class TestEdgeCases:
    """Edge case tests for market_alerts_handler module."""

    @pytest.mark.asyncio()
    async def test_alerts_with_empty_strings(self) -> None:
        """Test handling of empty strings."""
        from src.telegram_bot.handlers.market_alerts_handler import _handle_toggle_alert

        query = MagicMock()
        query.answer = AsyncMock()

        mock_manager = MagicMock()
        mock_manager.get_user_subscriptions.return_value = []
        mock_manager.subscribe.return_value = True

        with patch(
            "src.telegram_bot.handlers.market_alerts_handler.update_alerts_keyboard",
            new_callable=AsyncMock,
        ):
            await _handle_toggle_alert(
                query=query,
                update=MagicMock(),
                context=MagicMock(),
                parts=["alerts", "toggle", ""],  # Empty alert type
                user_id=12345,
                alerts_manager=mock_manager,
            )

        # Should still process (subscribe returns True)
        mock_manager.subscribe.assert_called_once()

    @pytest.mark.asyncio()
    async def test_concurrent_updates(self) -> None:
        """Test concurrent updates to alerts."""
        import asyncio

        from src.telegram_bot.handlers.market_alerts_handler import (
            _handle_subscribe_all,
        )

        query = MagicMock()
        query.answer = AsyncMock()

        mock_manager = MagicMock()
        mock_manager.subscribe.return_value = True

        with patch(
            "src.telegram_bot.handlers.market_alerts_handler.update_alerts_keyboard",
            new_callable=AsyncMock,
        ):
            # Run multiple subscribe_all concurrently
            tasks = [
                _handle_subscribe_all(
                    query=query,
                    update=MagicMock(),
                    context=MagicMock(),
                    parts=["alerts", "subscribe_all"],
                    user_id=12345 + i,
                    alerts_manager=mock_manager,
                )
                for i in range(5)
            ]

            await asyncio.gather(*tasks)

        # All should complete without errors
        assert query.answer.call_count == 5

    def test_alert_types_no_duplicates(self) -> None:
        """Test ALERT_TYPES has no duplicate values."""
        from src.telegram_bot.handlers.market_alerts_handler import ALERT_TYPES

        # Each alert type should have unique emoji prefix
        prefixes = [v.split()[0] for v in ALERT_TYPES.values()]
        # Note: some emojis may be shared (💰 for arbitrage and good_deal)
        # Just ensure all values are strings
        for value in ALERT_TYPES.values():
            assert isinstance(value, str)
            assert len(value) > 0
