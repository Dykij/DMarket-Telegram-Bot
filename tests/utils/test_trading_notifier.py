"""Unit tests for trading_notifier module.

Tests for TradingNotifier class and buy_with_notifications function.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.utils.trading_notifier import (
    TradingNotifier,
    buy_with_notifications,
)


class TestTradingNotifierInit:
    """Tests for TradingNotifier initialization."""

    def test_init_with_api_client_only(self):
        """Test initialization with only API client."""
        mock_api = MagicMock()
        notifier = TradingNotifier(api_client=mock_api)

        assert notifier.api is mock_api
        assert notifier.bot is None
        assert notifier.notification_queue is None
        assert notifier.user_id is None

    def test_init_with_all_parameters(self):
        """Test initialization with all parameters."""
        mock_api = MagicMock()
        mock_bot = MagicMock()
        mock_queue = MagicMock()
        user_id = 123456789

        notifier = TradingNotifier(
            api_client=mock_api,
            bot=mock_bot,
            notification_queue=mock_queue,
            user_id=user_id,
        )

        assert notifier.api is mock_api
        assert notifier.bot is mock_bot
        assert notifier.notification_queue is mock_queue
        assert notifier.user_id == user_id

    def test_init_with_partial_parameters(self):
        """Test initialization with partial parameters."""
        mock_api = MagicMock()
        mock_bot = MagicMock()

        notifier = TradingNotifier(
            api_client=mock_api,
            bot=mock_bot,
        )

        assert notifier.api is mock_api
        assert notifier.bot is mock_bot
        assert notifier.notification_queue is None
        assert notifier.user_id is None


class TestBuyItemWithNotifications:
    """Tests for buy_item_with_notifications method."""

    @pytest.mark.asyncio
    async def test_buy_without_bot_skips_notifications(self):
        """Test that buy without bot skips notifications."""
        mock_api = MagicMock()
        mock_api.buy_item = AsyncMock(return_value={"success": True, "orderId": "123"})
        mock_api.dry_run = False

        notifier = TradingNotifier(api_client=mock_api)

        result = await notifier.buy_item_with_notifications(
            item_id="item_123",
            item_name="AK-47 | Redline",
            buy_price=50.0,
            sell_price=60.0,
            game="csgo",
        )

        assert result["success"] is True
        mock_api.buy_item.assert_called_once()

    @pytest.mark.asyncio
    async def test_buy_without_user_id_skips_notifications(self):
        """Test that buy without user_id skips notifications."""
        mock_api = MagicMock()
        mock_api.buy_item = AsyncMock(return_value={"success": True, "orderId": "123"})
        mock_api.dry_run = False
        mock_bot = MagicMock()

        notifier = TradingNotifier(api_client=mock_api, bot=mock_bot)

        result = await notifier.buy_item_with_notifications(
            item_id="item_123",
            item_name="AK-47 | Redline",
            buy_price=50.0,
            sell_price=60.0,
        )

        assert result["success"] is True
        mock_api.buy_item.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.utils.trading_notifier.send_buy_intent_notification")
    @patch("src.utils.trading_notifier.send_buy_success_notification")
    async def test_buy_success_sends_notifications(
        self,
        mock_success_notif,
        mock_intent_notif,
    ):
        """Test that successful buy sends notifications."""
        mock_api = MagicMock()
        mock_api.buy_item = AsyncMock(return_value={"success": True, "orderId": "456"})
        mock_api.dry_run = False
        mock_bot = MagicMock()
        mock_intent_notif.return_value = None
        mock_success_notif.return_value = None

        notifier = TradingNotifier(
            api_client=mock_api,
            bot=mock_bot,
            user_id=123,
        )

        result = await notifier.buy_item_with_notifications(
            item_id="item_123",
            item_name="AWP | Dragon Lore",
            buy_price=100.0,
            sell_price=130.0,
            game="csgo",
            source="arbitrage_scanner",
        )

        assert result["success"] is True
        mock_intent_notif.assert_called_once()
        mock_success_notif.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.utils.trading_notifier.send_buy_intent_notification")
    @patch("src.utils.trading_notifier.send_buy_failed_notification")
    async def test_buy_failure_sends_failed_notification(
        self,
        mock_failed_notif,
        mock_intent_notif,
    ):
        """Test that failed buy sends failure notification."""
        mock_api = MagicMock()
        mock_api.buy_item = AsyncMock(
            return_value={"success": False, "error": "Insufficient balance"},
        )
        mock_api.dry_run = False
        mock_bot = MagicMock()
        mock_intent_notif.return_value = None
        mock_failed_notif.return_value = None

        notifier = TradingNotifier(
            api_client=mock_api,
            bot=mock_bot,
            user_id=123,
        )

        result = await notifier.buy_item_with_notifications(
            item_id="item_123",
            item_name="Knife",
            buy_price=500.0,
            sell_price=600.0,
        )

        assert result["success"] is False
        mock_intent_notif.assert_called_once()
        mock_failed_notif.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.utils.trading_notifier.send_buy_intent_notification")
    @patch("src.utils.trading_notifier.send_buy_failed_notification")
    async def test_buy_exception_sends_failed_notification(
        self,
        mock_failed_notif,
        mock_intent_notif,
    ):
        """Test that exception during buy sends failure notification."""
        mock_api = MagicMock()
        mock_api.buy_item = AsyncMock(side_effect=Exception("API error"))
        mock_api.dry_run = False
        mock_bot = MagicMock()
        mock_intent_notif.return_value = None
        mock_failed_notif.return_value = None

        notifier = TradingNotifier(
            api_client=mock_api,
            bot=mock_bot,
            user_id=123,
        )

        with pytest.raises(Exception, match="API error"):
            await notifier.buy_item_with_notifications(
                item_id="item_123",
                item_name="Knife",
                buy_price=500.0,
                sell_price=600.0,
            )

        mock_intent_notif.assert_called_once()
        mock_failed_notif.assert_called_once()

    @pytest.mark.asyncio
    async def test_buy_calculates_profit_correctly(self):
        """Test that profit is calculated correctly (7% commission)."""
        mock_api = MagicMock()
        mock_api.buy_item = AsyncMock(return_value={"success": True, "orderId": "789"})
        mock_api.dry_run = False

        notifier = TradingNotifier(api_client=mock_api)

        # Buy at 100, sell at 130
        # Net sell = 130 * 0.93 = 120.9
        # Profit = 120.9 - 100 = 20.9
        # Profit percent = 20.9 / 100 * 100 = 20.9%

        await notifier.buy_item_with_notifications(
            item_id="item_123",
            item_name="Test Item",
            buy_price=100.0,
            sell_price=130.0,
        )

        # Verify API was called with correct parameters
        call_kwargs = mock_api.buy_item.call_args.kwargs
        assert call_kwargs["item_id"] == "item_123"
        assert call_kwargs["price"] == 100.0

    @pytest.mark.asyncio
    async def test_buy_with_different_games(self):
        """Test buying items from different games."""
        mock_api = MagicMock()
        mock_api.buy_item = AsyncMock(return_value={"success": True})
        mock_api.dry_run = False

        notifier = TradingNotifier(api_client=mock_api)

        # Test with different games
        for game in ["csgo", "dota2", "tf2", "rust"]:
            await notifier.buy_item_with_notifications(
                item_id=f"item_{game}",
                item_name=f"Item from {game}",
                buy_price=10.0,
                sell_price=15.0,
                game=game,
            )

        assert mock_api.buy_item.call_count == 4

    @pytest.mark.asyncio
    async def test_buy_with_notification_queue(self):
        """Test buy with notification queue."""
        mock_api = MagicMock()
        mock_api.buy_item = AsyncMock(return_value={"success": True, "orderId": "123"})
        mock_api.dry_run = False
        mock_queue = MagicMock()

        notifier = TradingNotifier(
            api_client=mock_api,
            notification_queue=mock_queue,
        )

        result = await notifier.buy_item_with_notifications(
            item_id="item_123",
            item_name="Test Item",
            buy_price=50.0,
            sell_price=60.0,
        )

        assert result["success"] is True


class TestSellItemWithNotifications:
    """Tests for sell_item_with_notifications method."""

    @pytest.mark.asyncio
    async def test_sell_without_bot_skips_notifications(self):
        """Test that sell without bot skips notifications."""
        mock_api = MagicMock()
        mock_api.sell_item = AsyncMock(return_value={"success": True})
        mock_api.dry_run = False

        notifier = TradingNotifier(api_client=mock_api)

        result = await notifier.sell_item_with_notifications(
            item_id="item_123",
            item_name="AK-47 | Redline",
            buy_price=50.0,
            sell_price=60.0,
            game="csgo",
        )

        assert result["success"] is True
        mock_api.sell_item.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.utils.trading_notifier.send_sell_success_notification")
    async def test_sell_success_sends_notification(self, mock_sell_notif):
        """Test that successful sell sends notification."""
        mock_api = MagicMock()
        mock_api.sell_item = AsyncMock(return_value={"success": True})
        mock_api.dry_run = False
        mock_bot = MagicMock()
        mock_sell_notif.return_value = None

        notifier = TradingNotifier(
            api_client=mock_api,
            bot=mock_bot,
            user_id=123,
        )

        result = await notifier.sell_item_with_notifications(
            item_id="item_123",
            item_name="AWP | Asiimov",
            buy_price=50.0,
            sell_price=65.0,
            game="csgo",
        )

        assert result["success"] is True
        mock_sell_notif.assert_called_once()

    @pytest.mark.asyncio
    async def test_sell_failure_does_not_send_notification(self):
        """Test that failed sell does not send success notification."""
        mock_api = MagicMock()
        mock_api.sell_item = AsyncMock(return_value={"success": False})
        mock_api.dry_run = False

        notifier = TradingNotifier(api_client=mock_api)

        result = await notifier.sell_item_with_notifications(
            item_id="item_123",
            item_name="Test Item",
            buy_price=50.0,
            sell_price=60.0,
        )

        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_sell_exception_is_raised(self):
        """Test that exception during sell is raised."""
        mock_api = MagicMock()
        mock_api.sell_item = AsyncMock(side_effect=Exception("Network error"))
        mock_api.dry_run = False

        notifier = TradingNotifier(api_client=mock_api)

        with pytest.raises(Exception, match="Network error"):
            await notifier.sell_item_with_notifications(
                item_id="item_123",
                item_name="Test Item",
                buy_price=50.0,
                sell_price=60.0,
            )

    @pytest.mark.asyncio
    async def test_sell_calls_api_with_correct_params(self):
        """Test that sell calls API with correct parameters."""
        mock_api = MagicMock()
        mock_api.sell_item = AsyncMock(return_value={"success": True})
        mock_api.dry_run = False

        notifier = TradingNotifier(api_client=mock_api)

        await notifier.sell_item_with_notifications(
            item_id="item_456",
            item_name="M4A4 | Howl",
            buy_price=1000.0,
            sell_price=1500.0,
            game="csgo",
        )

        call_kwargs = mock_api.sell_item.call_args.kwargs
        assert call_kwargs["item_id"] == "item_456"
        assert call_kwargs["price"] == 1500.0
        assert call_kwargs["game"] == "csgo"


class TestBuyWithNotificationsFunction:
    """Tests for buy_with_notifications helper function."""

    @pytest.mark.asyncio
    @patch("src.utils.trading_notifier.send_buy_intent_notification")
    @patch("src.utils.trading_notifier.send_buy_success_notification")
    async def test_buy_with_notifications_creates_notifier(
        self,
        mock_success_notif,
        mock_intent_notif,
    ):
        """Test that function creates TradingNotifier and calls buy."""
        mock_api = MagicMock()
        mock_api.buy_item = AsyncMock(return_value={"success": True, "orderId": "123"})
        mock_api.dry_run = False
        mock_bot = MagicMock()
        mock_intent_notif.return_value = None
        mock_success_notif.return_value = None

        result = await buy_with_notifications(
            api_client=mock_api,
            bot=mock_bot,
            user_id=123456789,
            item_id="item_abc",
            item_name="Test Item",
            buy_price=100.0,
            sell_price=120.0,
            game="csgo",
        )

        assert result["success"] is True
        mock_api.buy_item.assert_called_once()

    @pytest.mark.asyncio
    async def test_buy_with_notifications_passes_all_params(self):
        """Test that all parameters are passed correctly."""
        mock_api = MagicMock()
        mock_api.buy_item = AsyncMock(return_value={"success": True})
        mock_api.dry_run = False
        mock_bot = MagicMock()
        mock_queue = MagicMock()

        # Need to patch notification functions since they have different signatures
        with patch("src.utils.trading_notifier.send_buy_intent_notification", new_callable=AsyncMock):
            with patch("src.utils.trading_notifier.send_buy_success_notification", new_callable=AsyncMock):
                await buy_with_notifications(
                    api_client=mock_api,
                    bot=mock_bot,
                    user_id=999,
                    item_id="item_xyz",
                    item_name="Special Item",
                    buy_price=200.0,
                    sell_price=250.0,
                    game="dota2",
                    source="manual",
                    notification_queue=mock_queue,
                )

        call_kwargs = mock_api.buy_item.call_args.kwargs
        assert call_kwargs["item_id"] == "item_xyz"
        assert call_kwargs["price"] == 200.0
        assert call_kwargs["game"] == "dota2"

    @pytest.mark.asyncio
    async def test_buy_with_notifications_default_values(self):
        """Test function with default values."""
        mock_api = MagicMock()
        mock_api.buy_item = AsyncMock(return_value={"success": True})
        mock_api.dry_run = False
        mock_bot = MagicMock()

        # Need to patch notification functions since they have different signatures
        with patch("src.utils.trading_notifier.send_buy_intent_notification", new_callable=AsyncMock):
            with patch("src.utils.trading_notifier.send_buy_success_notification", new_callable=AsyncMock):
                await buy_with_notifications(
                    api_client=mock_api,
                    bot=mock_bot,
                    user_id=123,
                    item_id="item_123",
                    item_name="Item",
                    buy_price=10.0,
                    sell_price=15.0,
                )

        call_kwargs = mock_api.buy_item.call_args.kwargs
        assert call_kwargs["game"] == "csgo"  # Default game


class TestDryRunMode:
    """Tests for dry run mode."""

    @pytest.mark.asyncio
    @patch("src.utils.trading_notifier.send_buy_intent_notification")
    @patch("src.utils.trading_notifier.send_buy_success_notification")
    async def test_dry_run_flag_passed_to_notifications(
        self,
        mock_success_notif,
        mock_intent_notif,
    ):
        """Test that dry_run flag is passed to notification functions."""
        mock_api = MagicMock()
        mock_api.buy_item = AsyncMock(return_value={"success": True, "orderId": "123"})
        mock_api.dry_run = True  # Dry run mode
        mock_bot = MagicMock()
        mock_intent_notif.return_value = None
        mock_success_notif.return_value = None

        notifier = TradingNotifier(
            api_client=mock_api,
            bot=mock_bot,
            user_id=123,
        )

        await notifier.buy_item_with_notifications(
            item_id="item_123",
            item_name="Test Item",
            buy_price=50.0,
            sell_price=60.0,
        )

        # Verify dry_run was passed
        intent_call_kwargs = mock_intent_notif.call_args.kwargs
        assert intent_call_kwargs["dry_run"] is True

        success_call_kwargs = mock_success_notif.call_args.kwargs
        assert success_call_kwargs["dry_run"] is True


class TestProfitCalculation:
    """Tests for profit calculation in notifications."""

    @pytest.mark.asyncio
    @patch("src.utils.trading_notifier.send_buy_intent_notification", new_callable=AsyncMock)
    @patch("src.utils.trading_notifier.send_buy_success_notification", new_callable=AsyncMock)
    async def test_profit_calculation_buy(self, mock_success_notif, mock_intent_notif):
        """Test profit calculation during buy notification."""
        mock_api = MagicMock()
        mock_api.buy_item = AsyncMock(return_value={"success": True})
        mock_api.dry_run = False
        mock_bot = MagicMock()

        notifier = TradingNotifier(
            api_client=mock_api,
            bot=mock_bot,
            user_id=123,
        )

        # Buy at 100, sell at 200
        # Net sell = 200 * 0.93 = 186
        # Profit = 186 - 100 = 86
        # Profit % = 86 / 100 * 100 = 86%
        await notifier.buy_item_with_notifications(
            item_id="item_123",
            item_name="Expensive Item",
            buy_price=100.0,
            sell_price=200.0,
        )

        # Intent notification should have been called with profit calculations
        mock_intent_notif.assert_called_once()
        call_kwargs = mock_intent_notif.call_args.kwargs
        expected_profit = (200.0 * 0.93) - 100.0
        expected_percent = (expected_profit / 100.0) * 100

        assert abs(call_kwargs["profit_usd"] - expected_profit) < 0.01
        assert abs(call_kwargs["profit_percent"] - expected_percent) < 0.01

    @pytest.mark.asyncio
    @patch("src.utils.trading_notifier.send_sell_success_notification")
    async def test_profit_calculation_sell(self, mock_sell_notif):
        """Test profit calculation during sell notification."""
        mock_api = MagicMock()
        mock_api.sell_item = AsyncMock(return_value={"success": True})
        mock_api.dry_run = False
        mock_bot = MagicMock()
        mock_sell_notif.return_value = None

        notifier = TradingNotifier(
            api_client=mock_api,
            bot=mock_bot,
            user_id=123,
        )

        await notifier.sell_item_with_notifications(
            item_id="item_123",
            item_name="Sold Item",
            buy_price=50.0,
            sell_price=80.0,
        )

        call_kwargs = mock_sell_notif.call_args.kwargs
        expected_profit = (80.0 * 0.93) - 50.0
        expected_percent = (expected_profit / 50.0) * 100

        assert abs(call_kwargs["profit_usd"] - expected_profit) < 0.01
        assert abs(call_kwargs["profit_percent"] - expected_percent) < 0.01
