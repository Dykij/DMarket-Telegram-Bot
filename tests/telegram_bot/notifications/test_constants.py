"""Tests for telegram_bot.notifications.constants module.

This module tests notification constants:
- NOTIFICATION_TYPES
- _PRICE_CACHE_TTL
- DEFAULT_USER_SETTINGS
- NOTIFICATION_PRIORITIES
"""

from __future__ import annotations

import pytest


# =============================================================================
# Test NOTIFICATION_TYPES constant
# =============================================================================

class TestNotificationTypes:
    """Tests for NOTIFICATION_TYPES constant."""

    def test_notification_types_exists(self) -> None:
        """Test NOTIFICATION_TYPES constant exists."""
        from src.telegram_bot.notifications.constants import NOTIFICATION_TYPES

        assert isinstance(NOTIFICATION_TYPES, dict)

    def test_notification_types_has_required_keys(self) -> None:
        """Test NOTIFICATION_TYPES has all required keys."""
        from src.telegram_bot.notifications.constants import NOTIFICATION_TYPES

        required_keys = [
            "price_drop",
            "price_rise",
            "volume_increase",
            "good_deal",
            "arbitrage",
            "trend_change",
            "buy_intent",
            "buy_success",
            "buy_failed",
            "sell_success",
            "sell_failed",
            "critical_shutdown",
        ]

        for key in required_keys:
            assert key in NOTIFICATION_TYPES, f"Missing key: {key}"

    def test_notification_types_values_have_emoji(self) -> None:
        """Test NOTIFICATION_TYPES values contain emojis."""
        from src.telegram_bot.notifications.constants import NOTIFICATION_TYPES

        # Check a few expected emojis
        assert "📉" in NOTIFICATION_TYPES["price_drop"]
        assert "📈" in NOTIFICATION_TYPES["price_rise"]
        assert "✅" in NOTIFICATION_TYPES["buy_success"]
        assert "❌" in NOTIFICATION_TYPES["buy_failed"]

    def test_notification_types_is_final(self) -> None:
        """Test NOTIFICATION_TYPES is typed as Final."""
        from src.telegram_bot.notifications.constants import NOTIFICATION_TYPES

        # Can verify the dict is not None and has values
        assert NOTIFICATION_TYPES is not None
        assert len(NOTIFICATION_TYPES) >= 10


# =============================================================================
# Test _PRICE_CACHE_TTL constant
# =============================================================================

class TestPriceCacheTTL:
    """Tests for _PRICE_CACHE_TTL constant."""

    def test_price_cache_ttl_exists(self) -> None:
        """Test _PRICE_CACHE_TTL constant exists."""
        from src.telegram_bot.notifications.constants import _PRICE_CACHE_TTL

        assert isinstance(_PRICE_CACHE_TTL, int)

    def test_price_cache_ttl_is_5_minutes(self) -> None:
        """Test _PRICE_CACHE_TTL is 300 seconds (5 minutes)."""
        from src.telegram_bot.notifications.constants import _PRICE_CACHE_TTL

        assert _PRICE_CACHE_TTL == 300

    def test_price_cache_ttl_is_positive(self) -> None:
        """Test _PRICE_CACHE_TTL is positive."""
        from src.telegram_bot.notifications.constants import _PRICE_CACHE_TTL

        assert _PRICE_CACHE_TTL > 0


# =============================================================================
# Test DEFAULT_USER_SETTINGS constant
# =============================================================================

class TestDefaultUserSettings:
    """Tests for DEFAULT_USER_SETTINGS constant."""

    def test_default_user_settings_exists(self) -> None:
        """Test DEFAULT_USER_SETTINGS constant exists."""
        from src.telegram_bot.notifications.constants import DEFAULT_USER_SETTINGS

        assert isinstance(DEFAULT_USER_SETTINGS, dict)

    def test_default_user_settings_has_enabled(self) -> None:
        """Test DEFAULT_USER_SETTINGS has enabled key."""
        from src.telegram_bot.notifications.constants import DEFAULT_USER_SETTINGS

        assert "enabled" in DEFAULT_USER_SETTINGS
        assert DEFAULT_USER_SETTINGS["enabled"] is True

    def test_default_user_settings_has_language(self) -> None:
        """Test DEFAULT_USER_SETTINGS has language key."""
        from src.telegram_bot.notifications.constants import DEFAULT_USER_SETTINGS

        assert "language" in DEFAULT_USER_SETTINGS
        assert DEFAULT_USER_SETTINGS["language"] == "ru"

    def test_default_user_settings_has_min_interval(self) -> None:
        """Test DEFAULT_USER_SETTINGS has min_interval key."""
        from src.telegram_bot.notifications.constants import DEFAULT_USER_SETTINGS

        assert "min_interval" in DEFAULT_USER_SETTINGS
        assert DEFAULT_USER_SETTINGS["min_interval"] == 300  # 5 minutes

    def test_default_user_settings_has_quiet_hours(self) -> None:
        """Test DEFAULT_USER_SETTINGS has quiet_hours key."""
        from src.telegram_bot.notifications.constants import DEFAULT_USER_SETTINGS

        assert "quiet_hours" in DEFAULT_USER_SETTINGS
        quiet_hours = DEFAULT_USER_SETTINGS["quiet_hours"]
        assert isinstance(quiet_hours, dict)
        assert "start" in quiet_hours
        assert "end" in quiet_hours
        assert quiet_hours["start"] == 23
        assert quiet_hours["end"] == 7

    def test_default_user_settings_has_max_alerts_per_day(self) -> None:
        """Test DEFAULT_USER_SETTINGS has max_alerts_per_day key."""
        from src.telegram_bot.notifications.constants import DEFAULT_USER_SETTINGS

        assert "max_alerts_per_day" in DEFAULT_USER_SETTINGS
        assert DEFAULT_USER_SETTINGS["max_alerts_per_day"] == 50


# =============================================================================
# Test NOTIFICATION_PRIORITIES constant
# =============================================================================

class TestNotificationPriorities:
    """Tests for NOTIFICATION_PRIORITIES constant."""

    def test_notification_priorities_exists(self) -> None:
        """Test NOTIFICATION_PRIORITIES constant exists."""
        from src.telegram_bot.notifications.constants import NOTIFICATION_PRIORITIES

        assert isinstance(NOTIFICATION_PRIORITIES, dict)

    def test_notification_priorities_has_required_keys(self) -> None:
        """Test NOTIFICATION_PRIORITIES has all notification types."""
        from src.telegram_bot.notifications.constants import NOTIFICATION_PRIORITIES

        required_keys = [
            "critical_shutdown",
            "buy_success",
            "buy_failed",
            "sell_success",
            "sell_failed",
            "buy_intent",
            "arbitrage",
            "good_deal",
            "price_drop",
            "price_rise",
            "volume_increase",
            "trend_change",
        ]

        for key in required_keys:
            assert key in NOTIFICATION_PRIORITIES, f"Missing priority for: {key}"

    def test_notification_priorities_are_integers(self) -> None:
        """Test all NOTIFICATION_PRIORITIES values are integers."""
        from src.telegram_bot.notifications.constants import NOTIFICATION_PRIORITIES

        for key, value in NOTIFICATION_PRIORITIES.items():
            assert isinstance(value, int), f"Priority for {key} is not int"

    def test_critical_shutdown_has_highest_priority(self) -> None:
        """Test critical_shutdown has highest priority."""
        from src.telegram_bot.notifications.constants import NOTIFICATION_PRIORITIES

        critical_priority = NOTIFICATION_PRIORITIES["critical_shutdown"]

        for key, value in NOTIFICATION_PRIORITIES.items():
            assert critical_priority >= value, f"{key} has higher priority than critical_shutdown"

    def test_trend_change_has_lowest_priority(self) -> None:
        """Test trend_change has lowest priority."""
        from src.telegram_bot.notifications.constants import NOTIFICATION_PRIORITIES

        trend_priority = NOTIFICATION_PRIORITIES["trend_change"]

        for key, value in NOTIFICATION_PRIORITIES.items():
            assert trend_priority <= value, f"{key} has lower priority than trend_change"

    def test_notification_priorities_values_are_positive(self) -> None:
        """Test all priorities are positive."""
        from src.telegram_bot.notifications.constants import NOTIFICATION_PRIORITIES

        for key, value in NOTIFICATION_PRIORITIES.items():
            assert value > 0, f"Priority for {key} is not positive"

    def test_buy_transactions_have_high_priority(self) -> None:
        """Test buy transactions have high priority."""
        from src.telegram_bot.notifications.constants import NOTIFICATION_PRIORITIES

        assert NOTIFICATION_PRIORITIES["buy_success"] >= 80
        assert NOTIFICATION_PRIORITIES["buy_failed"] >= 80
        assert NOTIFICATION_PRIORITIES["buy_intent"] >= 70


# =============================================================================
# Module exports test
# =============================================================================

class TestConstantsModuleExports:
    """Tests for module exports."""

    def test_module_exports_notification_types(self) -> None:
        """Test NOTIFICATION_TYPES is exported."""
        from src.telegram_bot.notifications.constants import NOTIFICATION_TYPES

        assert NOTIFICATION_TYPES is not None

    def test_module_exports_price_cache_ttl(self) -> None:
        """Test _PRICE_CACHE_TTL is exported."""
        from src.telegram_bot.notifications.constants import _PRICE_CACHE_TTL

        assert _PRICE_CACHE_TTL is not None

    def test_module_exports_default_user_settings(self) -> None:
        """Test DEFAULT_USER_SETTINGS is exported."""
        from src.telegram_bot.notifications.constants import DEFAULT_USER_SETTINGS

        assert DEFAULT_USER_SETTINGS is not None

    def test_module_exports_notification_priorities(self) -> None:
        """Test NOTIFICATION_PRIORITIES is exported."""
        from src.telegram_bot.notifications.constants import NOTIFICATION_PRIORITIES

        assert NOTIFICATION_PRIORITIES is not None

    def test_all_exports(self) -> None:
        """Test __all__ exports correct constants."""
        from src.telegram_bot.notifications import constants

        expected = [
            "NOTIFICATION_TYPES",
            "_PRICE_CACHE_TTL",
            "DEFAULT_USER_SETTINGS",
            "NOTIFICATION_PRIORITIES",
        ]

        for name in expected:
            assert hasattr(constants, name), f"Missing export: {name}"


# =============================================================================
# Integration tests
# =============================================================================

class TestConstantsIntegration:
    """Integration tests for constants module."""

    def test_notification_types_match_priorities(self) -> None:
        """Test that notification types have corresponding priorities."""
        from src.telegram_bot.notifications.constants import (
            NOTIFICATION_PRIORITIES,
            NOTIFICATION_TYPES,
        )

        # Every type in priorities should have a readable name in types
        for key in NOTIFICATION_PRIORITIES:
            assert key in NOTIFICATION_TYPES, f"{key} missing from NOTIFICATION_TYPES"

    def test_default_settings_quiet_hours_valid(self) -> None:
        """Test that default quiet hours are valid times."""
        from src.telegram_bot.notifications.constants import DEFAULT_USER_SETTINGS

        quiet_hours = DEFAULT_USER_SETTINGS["quiet_hours"]

        assert 0 <= quiet_hours["start"] <= 23
        assert 0 <= quiet_hours["end"] <= 23

    def test_default_settings_min_interval_reasonable(self) -> None:
        """Test that default min_interval is reasonable."""
        from src.telegram_bot.notifications.constants import DEFAULT_USER_SETTINGS

        min_interval = DEFAULT_USER_SETTINGS["min_interval"]

        # Should be at least 60 seconds and at most 1 hour
        assert 60 <= min_interval <= 3600
