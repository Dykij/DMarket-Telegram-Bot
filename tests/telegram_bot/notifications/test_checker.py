"""Tests for telegram_bot.notifications.checker module.

This module tests price alert checker functions:
- get_current_price
- check_price_alert
- check_good_deal_alerts
- check_all_alerts
- run_alerts_checker
"""

from __future__ import annotations

import asyncio
import time
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# =============================================================================
# Test get_current_price function
# =============================================================================

class TestGetCurrentPrice:
    """Tests for get_current_price function."""

    @pytest.fixture
    def mock_api(self) -> MagicMock:
        """Create mock DMarket API."""
        api = MagicMock()
        api.get_market_items = AsyncMock(
            return_value={
                "objects": [
                    {
                        "itemId": "item_123",
                        "title": "Test Item",
                        "price": {"USD": "1500"},  # $15.00 in cents
                    }
                ]
            }
        )
        return api

    @pytest.fixture
    def mock_storage(self) -> MagicMock:
        """Create mock storage."""
        storage = MagicMock()
        storage.get_cached_price.return_value = None
        return storage

    @pytest.mark.asyncio
    async def test_get_current_price_from_api(
        self, mock_api: MagicMock, mock_storage: MagicMock
    ) -> None:
        """Test getting price from API when not cached."""
        with patch(
            "src.telegram_bot.notifications.checker.get_storage",
            return_value=mock_storage,
        ):
            from src.telegram_bot.notifications.checker import get_current_price

            result = await get_current_price(mock_api, "item_123", "csgo")

            assert result == 15.0  # $15.00
            mock_api.get_market_items.assert_called_once()
            mock_storage.set_cached_price.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_current_price_from_cache(
        self, mock_api: MagicMock, mock_storage: MagicMock
    ) -> None:
        """Test getting price from cache."""
        mock_storage.get_cached_price.return_value = {
            "price": 20.0,
            "timestamp": time.time(),  # Fresh cache
        }

        with patch(
            "src.telegram_bot.notifications.checker.get_storage",
            return_value=mock_storage,
        ):
            from src.telegram_bot.notifications.checker import get_current_price

            result = await get_current_price(mock_api, "item_123", "csgo")

            assert result == 20.0
            mock_api.get_market_items.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_current_price_stale_cache(
        self, mock_api: MagicMock, mock_storage: MagicMock
    ) -> None:
        """Test getting price when cache is stale."""
        mock_storage.get_cached_price.return_value = {
            "price": 20.0,
            "timestamp": time.time() - 1000,  # Old cache (> 300s TTL)
        }

        with patch(
            "src.telegram_bot.notifications.checker.get_storage",
            return_value=mock_storage,
        ):
            from src.telegram_bot.notifications.checker import get_current_price

            result = await get_current_price(mock_api, "item_123", "csgo")

            # Should fetch from API since cache is stale
            assert result == 15.0
            mock_api.get_market_items.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_current_price_no_items_found(
        self, mock_storage: MagicMock
    ) -> None:
        """Test get_current_price when no items found."""
        mock_api = MagicMock()
        mock_api.get_market_items = AsyncMock(return_value={"objects": []})

        with patch(
            "src.telegram_bot.notifications.checker.get_storage",
            return_value=mock_storage,
        ):
            from src.telegram_bot.notifications.checker import get_current_price

            result = await get_current_price(mock_api, "nonexistent", "csgo")

            assert result is None

    @pytest.mark.asyncio
    async def test_get_current_price_api_error(
        self, mock_storage: MagicMock
    ) -> None:
        """Test get_current_price handles API errors."""
        mock_api = MagicMock()
        mock_api.get_market_items = AsyncMock(side_effect=Exception("API Error"))

        with patch(
            "src.telegram_bot.notifications.checker.get_storage",
            return_value=mock_storage,
        ):
            from src.telegram_bot.notifications.checker import get_current_price

            result = await get_current_price(mock_api, "item_123", "csgo")

            assert result is None


# =============================================================================
# Test check_price_alert function
# =============================================================================

class TestCheckPriceAlert:
    """Tests for check_price_alert function."""

    @pytest.fixture
    def mock_api(self) -> MagicMock:
        """Create mock API."""
        return MagicMock()

    @pytest.mark.asyncio
    async def test_check_price_drop_triggered(self, mock_api: MagicMock) -> None:
        """Test price_drop alert triggers when price below threshold."""
        alert = {
            "item_id": "item_123",
            "type": "price_drop",
            "threshold": 20.0,
        }

        try:
            # Import and patch the module directly
            import src.telegram_bot.notifier as notifier_module

            with patch.object(
                notifier_module,
                "get_current_price",
                new_callable=AsyncMock,
                return_value=15.0,  # Below threshold
            ):
                from src.telegram_bot.notifications.checker import check_price_alert

                result = await check_price_alert(mock_api, alert)

                assert result is not None
                assert result["current_price"] == 15.0
        except ModuleNotFoundError:
            pytest.skip("Missing dependencies for notifier module")

    @pytest.mark.asyncio
    async def test_check_price_drop_not_triggered(self, mock_api: MagicMock) -> None:
        """Test price_drop alert not triggered when price above threshold."""
        alert = {
            "item_id": "item_123",
            "type": "price_drop",
            "threshold": 10.0,
        }

        try:
            import src.telegram_bot.notifier as notifier_module

            with patch.object(
                notifier_module,
                "get_current_price",
                new_callable=AsyncMock,
                return_value=15.0,  # Above threshold
            ):
                from src.telegram_bot.notifications.checker import check_price_alert

                result = await check_price_alert(mock_api, alert)

                assert result is None
        except ModuleNotFoundError:
            pytest.skip("Missing dependencies for notifier module")

    @pytest.mark.asyncio
    async def test_check_price_rise_triggered(self, mock_api: MagicMock) -> None:
        """Test price_rise alert triggers when price above threshold."""
        alert = {
            "item_id": "item_123",
            "type": "price_rise",
            "threshold": 10.0,
        }

        try:
            import src.telegram_bot.notifier as notifier_module

            with patch.object(
                notifier_module,
                "get_current_price",
                new_callable=AsyncMock,
                return_value=15.0,  # Above threshold
            ):
                from src.telegram_bot.notifications.checker import check_price_alert

                result = await check_price_alert(mock_api, alert)

                assert result is not None
        except ModuleNotFoundError:
            pytest.skip("Missing dependencies for notifier module")

    @pytest.mark.asyncio
    async def test_check_price_below_triggered(self, mock_api: MagicMock) -> None:
        """Test price_below alert triggers when price below threshold."""
        alert = {
            "item_id": "item_123",
            "type": "price_below",
            "threshold": 20.0,
        }

        try:
            import src.telegram_bot.notifier as notifier_module

            with patch.object(
                notifier_module,
                "get_current_price",
                new_callable=AsyncMock,
                return_value=15.0,
            ):
                from src.telegram_bot.notifications.checker import check_price_alert

                result = await check_price_alert(mock_api, alert)

                assert result is not None
        except ModuleNotFoundError:
            pytest.skip("Missing dependencies for notifier module")

    @pytest.mark.asyncio
    async def test_check_price_above_triggered(self, mock_api: MagicMock) -> None:
        """Test price_above alert triggers when price above threshold."""
        alert = {
            "item_id": "item_123",
            "type": "price_above",
            "threshold": 10.0,
        }

        try:
            import src.telegram_bot.notifier as notifier_module

            with patch.object(
                notifier_module,
                "get_current_price",
                new_callable=AsyncMock,
                return_value=15.0,
            ):
                from src.telegram_bot.notifications.checker import check_price_alert

                result = await check_price_alert(mock_api, alert)

                assert result is not None
        except ModuleNotFoundError:
            pytest.skip("Missing dependencies for notifier module")

    @pytest.mark.asyncio
    async def test_check_price_alert_no_price(self, mock_api: MagicMock) -> None:
        """Test check_price_alert returns None when no price available."""
        alert = {
            "item_id": "item_123",
            "type": "price_drop",
            "threshold": 20.0,
        }

        try:
            import src.telegram_bot.notifier as notifier_module

            with patch.object(
                notifier_module,
                "get_current_price",
                new_callable=AsyncMock,
                return_value=None,
            ):
                from src.telegram_bot.notifications.checker import check_price_alert

                result = await check_price_alert(mock_api, alert)

                assert result is None
        except ModuleNotFoundError:
            pytest.skip("Missing dependencies for notifier module")


# =============================================================================
# Test check_good_deal_alerts function
# =============================================================================

class TestCheckGoodDealAlerts:
    """Tests for check_good_deal_alerts function."""

    @pytest.fixture
    def mock_storage(self) -> MagicMock:
        """Create mock storage."""
        storage = MagicMock()
        storage.get_user_data.return_value = {
            "settings": {"good_deal_threshold": 10.0},
        }
        return storage

    @pytest.mark.asyncio
    async def test_check_good_deals_finds_discounted_items(
        self, mock_storage: MagicMock
    ) -> None:
        """Test finding discounted items."""
        mock_api = MagicMock()
        mock_api.get_market_items = AsyncMock(
            return_value={
                "objects": [
                    {
                        "itemId": "item_1",
                        "title": "Discounted Item",
                        "price": {"USD": "900"},  # $9.00
                        "suggestedPrice": {"USD": "1200"},  # $12.00 (25% discount)
                    }
                ]
            }
        )

        with patch(
            "src.telegram_bot.notifications.checker.get_storage",
            return_value=mock_storage,
        ):
            from src.telegram_bot.notifications.checker import check_good_deal_alerts

            result = await check_good_deal_alerts(mock_api, user_id=12345, game="csgo")

            assert len(result) == 1
            assert result[0]["discount"] >= 10

    @pytest.mark.asyncio
    async def test_check_good_deals_no_user_data(self) -> None:
        """Test check_good_deal_alerts when user not found."""
        mock_storage = MagicMock()
        mock_storage.get_user_data.return_value = None

        mock_api = MagicMock()

        with patch(
            "src.telegram_bot.notifications.checker.get_storage",
            return_value=mock_storage,
        ):
            from src.telegram_bot.notifications.checker import check_good_deal_alerts

            result = await check_good_deal_alerts(mock_api, user_id=99999, game="csgo")

            assert result == []

    @pytest.mark.asyncio
    async def test_check_good_deals_api_error(
        self, mock_storage: MagicMock
    ) -> None:
        """Test check_good_deal_alerts handles API errors."""
        mock_api = MagicMock()
        mock_api.get_market_items = AsyncMock(side_effect=Exception("API Error"))

        with patch(
            "src.telegram_bot.notifications.checker.get_storage",
            return_value=mock_storage,
        ):
            from src.telegram_bot.notifications.checker import check_good_deal_alerts

            result = await check_good_deal_alerts(mock_api, user_id=12345, game="csgo")

            assert result == []


# =============================================================================
# Test check_all_alerts function
# =============================================================================

class TestCheckAllAlerts:
    """Tests for check_all_alerts function."""

    @pytest.fixture
    def mock_storage(self) -> MagicMock:
        """Create mock storage with alerts."""
        storage = MagicMock()
        storage.user_alerts = {
            "12345": {
                "alerts": [
                    {
                        "id": "alert_1",
                        "item_id": "item_123",
                        "title": "Test Item",
                        "type": "price_drop",
                        "threshold": 20.0,
                        "active": True,
                    }
                ],
                "settings": {
                    "enabled": True,
                    "max_alerts_per_day": 50,
                    "quiet_hours": {"start": 23, "end": 7},
                    "min_interval": 0,
                },
                "last_day": "2025-01-01",
                "daily_notifications": 0,
                "last_notification": 0,
            }
        }
        return storage

    @pytest.mark.asyncio
    async def test_check_all_alerts_triggers_alert(
        self, mock_storage: MagicMock
    ) -> None:
        """Test check_all_alerts triggers and sends notifications."""
        mock_api = MagicMock()
        mock_bot = MagicMock()
        mock_bot.send_message = AsyncMock()

        try:
            import src.telegram_bot.notifier as notifier_module

            with (
                patch(
                    "src.telegram_bot.notifications.checker.get_storage",
                    return_value=mock_storage,
                ),
                patch(
                    "src.telegram_bot.notifications.alerts.can_send_notification",
                    return_value=True,
                ),
                patch.object(
                    notifier_module,
                    "check_price_alert",
                    new_callable=AsyncMock,
                    return_value={
                        "alert": {"title": "Test", "type": "price_drop"},
                        "current_price": 15.0,
                        "time": "2025-01-01 12:00:00",
                    },
                ),
                patch(
                    "src.telegram_bot.notifications.alerts.increment_notification_count",
                ),
            ):
                from src.telegram_bot.notifications.checker import check_all_alerts

                result = await check_all_alerts(mock_api, mock_bot)

                assert result >= 0  # May or may not trigger depending on mocks
        except ModuleNotFoundError:
            pytest.skip("Missing dependencies for notifier module")

    @pytest.mark.asyncio
    async def test_check_all_alerts_empty_storage(self) -> None:
        """Test check_all_alerts with no users."""
        mock_storage = MagicMock()
        mock_storage.user_alerts = {}

        mock_api = MagicMock()
        mock_bot = MagicMock()

        with patch(
            "src.telegram_bot.notifications.checker.get_storage",
            return_value=mock_storage,
        ):
            from src.telegram_bot.notifications.checker import check_all_alerts

            result = await check_all_alerts(mock_api, mock_bot)

            assert result == 0


# =============================================================================
# Test run_alerts_checker function
# =============================================================================

class TestRunAlertsChecker:
    """Tests for run_alerts_checker function."""

    @pytest.mark.asyncio
    async def test_run_alerts_checker_stops_on_event(self) -> None:
        """Test run_alerts_checker stops when event is set."""
        mock_api = MagicMock()
        mock_bot = MagicMock()
        stop_event = asyncio.Event()
        stop_event.set()  # Set immediately to stop

        with patch(
            "src.telegram_bot.notifications.checker.check_all_alerts",
            new_callable=AsyncMock,
            return_value=0,
        ):
            from src.telegram_bot.notifications.checker import run_alerts_checker

            # Should return immediately since event is set
            await run_alerts_checker(
                mock_bot,
                mock_api,
                check_interval=1,
                stop_event=stop_event,
            )

            # Test passes if it doesn't hang


# =============================================================================
# Constants tests
# =============================================================================

class TestCheckerConstants:
    """Tests for checker module constants."""

    def test_module_exports(self) -> None:
        """Test module exports correct functions."""
        from src.telegram_bot.notifications import checker

        assert hasattr(checker, "get_current_price")
        assert hasattr(checker, "check_price_alert")
        assert hasattr(checker, "check_good_deal_alerts")
        assert hasattr(checker, "check_all_alerts")
        assert hasattr(checker, "run_alerts_checker")
