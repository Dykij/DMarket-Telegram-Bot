"""Unit tests for rate_limit_admin module.

Tests for admin commands for rate limiting management.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram import Message, Update, User
from telegram.ext import ContextTypes

from src.telegram_bot.handlers.rate_limit_admin import (
    ADMIN_IDS,
    is_admin,
    rate_limit_config_command,
    rate_limit_reset_command,
    rate_limit_stats_command,
    rate_limit_whitelist_command,
)


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture()
def mock_admin_user():
    """Create a mock admin user."""
    user = MagicMock(spec=User)
    user.id = ADMIN_IDS[0] if ADMIN_IDS else 123456789
    user.first_name = "Admin"
    user.username = "admin"
    return user


@pytest.fixture()
def mock_regular_user():
    """Create a mock regular (non-admin) user."""
    user = MagicMock(spec=User)
    user.id = 999999999  # Not in ADMIN_IDS
    user.first_name = "Regular"
    user.username = "regular"
    return user


@pytest.fixture()
def mock_message():
    """Create a mock Telegram message."""
    message = MagicMock(spec=Message)
    message.reply_text = AsyncMock()
    return message


@pytest.fixture()
def mock_update_admin(mock_admin_user, mock_message):
    """Create a mock update with admin user."""
    update = MagicMock(spec=Update)
    update.effective_user = mock_admin_user
    update.message = mock_message
    return update


@pytest.fixture()
def mock_update_regular(mock_regular_user, mock_message):
    """Create a mock update with regular user."""
    update = MagicMock(spec=Update)
    update.effective_user = mock_regular_user
    update.message = mock_message
    return update


@pytest.fixture()
def mock_context():
    """Create a mock bot context."""
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.args = []
    context.bot_data = MagicMock()
    return context


@pytest.fixture()
def mock_rate_limiter():
    """Create a mock rate limiter."""
    rate_limiter = MagicMock()
    rate_limiter.get_user_stats = AsyncMock(return_value={
        "scan": {"remaining": 5, "limit": 10},
        "trade": {"remaining": 8, "limit": 20},
    })
    rate_limiter.reset_user_limits = AsyncMock()
    rate_limiter.add_whitelist = AsyncMock()
    rate_limiter.remove_whitelist = AsyncMock()
    rate_limiter.is_whitelisted = AsyncMock(return_value=False)
    rate_limiter.limits = {
        "scan": MagicMock(requests=10, window=60, burst=None),
        "trade": MagicMock(requests=20, window=120, burst=5),
    }
    rate_limiter.update_limit = MagicMock()
    return rate_limiter


# ============================================================================
# TESTS FOR is_admin
# ============================================================================


class TestIsAdmin:
    """Tests for is_admin function."""

    def test_admin_user_returns_true(self):
        """Test that admin user returns True."""
        if ADMIN_IDS:
            assert is_admin(ADMIN_IDS[0]) is True

    def test_non_admin_user_returns_false(self):
        """Test that non-admin user returns False."""
        assert is_admin(999999999) is False

    def test_zero_id_returns_false(self):
        """Test that zero ID returns False."""
        assert is_admin(0) is False


# ============================================================================
# TESTS FOR rate_limit_stats_command
# ============================================================================


class TestRateLimitStatsCommand:
    """Tests for rate_limit_stats_command."""

    @pytest.mark.asyncio()
    async def test_no_user_returns_early(self, mock_update_admin, mock_context):
        """Test early return when no user."""
        mock_update_admin.effective_user = None

        await rate_limit_stats_command(mock_update_admin, mock_context)

        # Should return early without errors

    @pytest.mark.asyncio()
    async def test_no_message_returns_early(self, mock_update_admin, mock_context):
        """Test early return when no message."""
        mock_update_admin.message = None

        await rate_limit_stats_command(mock_update_admin, mock_context)

        # Should return early without errors

    @pytest.mark.asyncio()
    async def test_non_admin_denied(self, mock_update_regular, mock_context, mock_message):
        """Test non-admin users are denied."""
        await rate_limit_stats_command(mock_update_regular, mock_context)

        mock_message.reply_text.assert_called_once()
        call_args = mock_message.reply_text.call_args
        assert "администратор" in call_args[0][0].lower() or "admin" in call_args[0][0].lower()

    @pytest.mark.asyncio()
    async def test_no_rate_limiter_error(
        self, mock_update_admin, mock_context, mock_message
    ):
        """Test error when rate limiter not configured."""
        mock_context.bot_data.user_rate_limiter = None
        setattr(mock_context.bot_data, "user_rate_limiter", None)

        with patch(
            "src.telegram_bot.handlers.rate_limit_admin.is_admin",
            return_value=True
        ):
            await rate_limit_stats_command(mock_update_admin, mock_context)

        mock_message.reply_text.assert_called()
        call_args = mock_message.reply_text.call_args
        assert "не настроен" in call_args[0][0].lower() or "Rate limiter" in call_args[0][0]

    @pytest.mark.asyncio()
    async def test_stats_with_user_id_argument(
        self, mock_update_admin, mock_context, mock_message, mock_rate_limiter
    ):
        """Test stats command with user_id argument."""
        mock_context.args = ["12345"]
        setattr(mock_context.bot_data, "user_rate_limiter", mock_rate_limiter)

        with patch(
            "src.telegram_bot.handlers.rate_limit_admin.is_admin",
            return_value=True
        ):
            await rate_limit_stats_command(mock_update_admin, mock_context)

        mock_rate_limiter.get_user_stats.assert_called_once_with(12345)

    @pytest.mark.asyncio()
    async def test_stats_uses_own_user_id_when_no_args(
        self, mock_update_admin, mock_context, mock_message, mock_rate_limiter, mock_admin_user
    ):
        """Test stats command uses own user ID when no arguments."""
        mock_context.args = []
        setattr(mock_context.bot_data, "user_rate_limiter", mock_rate_limiter)

        with patch(
            "src.telegram_bot.handlers.rate_limit_admin.is_admin",
            return_value=True
        ):
            await rate_limit_stats_command(mock_update_admin, mock_context)

        mock_rate_limiter.get_user_stats.assert_called_once_with(mock_admin_user.id)

    @pytest.mark.asyncio()
    async def test_stats_exception_handling(
        self, mock_update_admin, mock_context, mock_message, mock_rate_limiter
    ):
        """Test exception handling in stats command."""
        mock_rate_limiter.get_user_stats = AsyncMock(side_effect=Exception("API Error"))
        setattr(mock_context.bot_data, "user_rate_limiter", mock_rate_limiter)

        with patch(
            "src.telegram_bot.handlers.rate_limit_admin.is_admin",
            return_value=True
        ):
            await rate_limit_stats_command(mock_update_admin, mock_context)

        mock_message.reply_text.assert_called()
        call_args = mock_message.reply_text.call_args
        assert "Ошибка" in call_args[0][0] or "Error" in call_args[0][0]


# ============================================================================
# TESTS FOR rate_limit_reset_command
# ============================================================================


class TestRateLimitResetCommand:
    """Tests for rate_limit_reset_command."""

    @pytest.mark.asyncio()
    async def test_no_user_returns_early(self, mock_update_admin, mock_context):
        """Test early return when no user."""
        mock_update_admin.effective_user = None

        await rate_limit_reset_command(mock_update_admin, mock_context)

    @pytest.mark.asyncio()
    async def test_non_admin_denied(self, mock_update_regular, mock_context, mock_message):
        """Test non-admin users are denied."""
        await rate_limit_reset_command(mock_update_regular, mock_context)

        mock_message.reply_text.assert_called_once()

    @pytest.mark.asyncio()
    async def test_no_args_shows_usage(
        self, mock_update_admin, mock_context, mock_message, mock_rate_limiter
    ):
        """Test usage message when no arguments."""
        mock_context.args = []
        setattr(mock_context.bot_data, "user_rate_limiter", mock_rate_limiter)

        with patch(
            "src.telegram_bot.handlers.rate_limit_admin.is_admin",
            return_value=True
        ):
            await rate_limit_reset_command(mock_update_admin, mock_context)

        mock_message.reply_text.assert_called()
        call_args = mock_message.reply_text.call_args
        assert "Использование" in call_args[0][0] or "usage" in call_args[0][0].lower()

    @pytest.mark.asyncio()
    async def test_invalid_user_id_shows_usage(
        self, mock_update_admin, mock_context, mock_message, mock_rate_limiter
    ):
        """Test usage message when invalid user ID."""
        mock_context.args = ["not_a_number"]
        setattr(mock_context.bot_data, "user_rate_limiter", mock_rate_limiter)

        with patch(
            "src.telegram_bot.handlers.rate_limit_admin.is_admin",
            return_value=True
        ):
            await rate_limit_reset_command(mock_update_admin, mock_context)

        mock_message.reply_text.assert_called()

    @pytest.mark.asyncio()
    async def test_reset_all_actions(
        self, mock_update_admin, mock_context, mock_message, mock_rate_limiter
    ):
        """Test resetting all actions for a user."""
        mock_context.args = ["12345"]
        setattr(mock_context.bot_data, "user_rate_limiter", mock_rate_limiter)

        with patch(
            "src.telegram_bot.handlers.rate_limit_admin.is_admin",
            return_value=True
        ):
            await rate_limit_reset_command(mock_update_admin, mock_context)

        mock_rate_limiter.reset_user_limits.assert_called_once_with(12345, None)

    @pytest.mark.asyncio()
    async def test_reset_specific_action(
        self, mock_update_admin, mock_context, mock_message, mock_rate_limiter
    ):
        """Test resetting specific action for a user."""
        mock_context.args = ["12345", "scan"]
        setattr(mock_context.bot_data, "user_rate_limiter", mock_rate_limiter)

        with patch(
            "src.telegram_bot.handlers.rate_limit_admin.is_admin",
            return_value=True
        ):
            await rate_limit_reset_command(mock_update_admin, mock_context)

        mock_rate_limiter.reset_user_limits.assert_called_once_with(12345, "scan")


# ============================================================================
# TESTS FOR rate_limit_whitelist_command
# ============================================================================


class TestRateLimitWhitelistCommand:
    """Tests for rate_limit_whitelist_command."""

    @pytest.mark.asyncio()
    async def test_no_user_returns_early(self, mock_update_admin, mock_context):
        """Test early return when no user."""
        mock_update_admin.effective_user = None

        await rate_limit_whitelist_command(mock_update_admin, mock_context)

    @pytest.mark.asyncio()
    async def test_non_admin_denied(self, mock_update_regular, mock_context, mock_message):
        """Test non-admin users are denied."""
        await rate_limit_whitelist_command(mock_update_regular, mock_context)

        mock_message.reply_text.assert_called_once()

    @pytest.mark.asyncio()
    async def test_insufficient_args_shows_usage(
        self, mock_update_admin, mock_context, mock_message, mock_rate_limiter
    ):
        """Test usage message when insufficient arguments."""
        mock_context.args = ["add"]  # Missing user_id
        setattr(mock_context.bot_data, "user_rate_limiter", mock_rate_limiter)

        with patch(
            "src.telegram_bot.handlers.rate_limit_admin.is_admin",
            return_value=True
        ):
            await rate_limit_whitelist_command(mock_update_admin, mock_context)

        mock_message.reply_text.assert_called()

    @pytest.mark.asyncio()
    async def test_add_to_whitelist(
        self, mock_update_admin, mock_context, mock_message, mock_rate_limiter
    ):
        """Test adding user to whitelist."""
        mock_context.args = ["add", "12345"]
        setattr(mock_context.bot_data, "user_rate_limiter", mock_rate_limiter)

        with patch(
            "src.telegram_bot.handlers.rate_limit_admin.is_admin",
            return_value=True
        ):
            await rate_limit_whitelist_command(mock_update_admin, mock_context)

        mock_rate_limiter.add_whitelist.assert_called_once_with(12345)

    @pytest.mark.asyncio()
    async def test_remove_from_whitelist(
        self, mock_update_admin, mock_context, mock_message, mock_rate_limiter
    ):
        """Test removing user from whitelist."""
        mock_context.args = ["remove", "12345"]
        setattr(mock_context.bot_data, "user_rate_limiter", mock_rate_limiter)

        with patch(
            "src.telegram_bot.handlers.rate_limit_admin.is_admin",
            return_value=True
        ):
            await rate_limit_whitelist_command(mock_update_admin, mock_context)

        mock_rate_limiter.remove_whitelist.assert_called_once_with(12345)

    @pytest.mark.asyncio()
    async def test_check_whitelist_status(
        self, mock_update_admin, mock_context, mock_message, mock_rate_limiter
    ):
        """Test checking whitelist status."""
        mock_context.args = ["check", "12345"]
        setattr(mock_context.bot_data, "user_rate_limiter", mock_rate_limiter)

        with patch(
            "src.telegram_bot.handlers.rate_limit_admin.is_admin",
            return_value=True
        ):
            await rate_limit_whitelist_command(mock_update_admin, mock_context)

        mock_rate_limiter.is_whitelisted.assert_called_once_with(12345)

    @pytest.mark.asyncio()
    async def test_unknown_action_error(
        self, mock_update_admin, mock_context, mock_message, mock_rate_limiter
    ):
        """Test error for unknown action."""
        mock_context.args = ["unknown", "12345"]
        setattr(mock_context.bot_data, "user_rate_limiter", mock_rate_limiter)

        with patch(
            "src.telegram_bot.handlers.rate_limit_admin.is_admin",
            return_value=True
        ):
            await rate_limit_whitelist_command(mock_update_admin, mock_context)

        mock_message.reply_text.assert_called()
        call_args = mock_message.reply_text.call_args
        assert "Неизвестное" in call_args[0][0] or "unknown" in call_args[0][0].lower()


# ============================================================================
# TESTS FOR rate_limit_config_command
# ============================================================================


class TestRateLimitConfigCommand:
    """Tests for rate_limit_config_command."""

    @pytest.mark.asyncio()
    async def test_no_user_returns_early(self, mock_update_admin, mock_context):
        """Test early return when no user."""
        mock_update_admin.effective_user = None

        await rate_limit_config_command(mock_update_admin, mock_context)

    @pytest.mark.asyncio()
    async def test_non_admin_denied(self, mock_update_regular, mock_context, mock_message):
        """Test non-admin users are denied."""
        await rate_limit_config_command(mock_update_regular, mock_context)

        mock_message.reply_text.assert_called_once()

    @pytest.mark.asyncio()
    async def test_no_args_shows_current_config(
        self, mock_update_admin, mock_context, mock_message, mock_rate_limiter
    ):
        """Test showing current config when no arguments."""
        mock_context.args = []
        setattr(mock_context.bot_data, "user_rate_limiter", mock_rate_limiter)

        with patch(
            "src.telegram_bot.handlers.rate_limit_admin.is_admin",
            return_value=True
        ):
            await rate_limit_config_command(mock_update_admin, mock_context)

        mock_message.reply_text.assert_called()
        call_args = mock_message.reply_text.call_args
        assert "лимит" in call_args[0][0].lower() or "config" in call_args[0][0].lower()

    @pytest.mark.asyncio()
    async def test_invalid_args_shows_usage(
        self, mock_update_admin, mock_context, mock_message, mock_rate_limiter
    ):
        """Test usage message for invalid arguments."""
        mock_context.args = ["scan"]  # Missing requests and window
        setattr(mock_context.bot_data, "user_rate_limiter", mock_rate_limiter)

        with patch(
            "src.telegram_bot.handlers.rate_limit_admin.is_admin",
            return_value=True
        ):
            await rate_limit_config_command(mock_update_admin, mock_context)

        mock_message.reply_text.assert_called()

    @pytest.mark.asyncio()
    async def test_update_limit_without_burst(
        self, mock_update_admin, mock_context, mock_message, mock_rate_limiter
    ):
        """Test updating limit without burst."""
        mock_context.args = ["scan", "5", "60"]
        setattr(mock_context.bot_data, "user_rate_limiter", mock_rate_limiter)

        with patch(
            "src.telegram_bot.handlers.rate_limit_admin.is_admin",
            return_value=True
        ):
            await rate_limit_config_command(mock_update_admin, mock_context)

        mock_rate_limiter.update_limit.assert_called_once()

    @pytest.mark.asyncio()
    async def test_update_limit_with_burst(
        self, mock_update_admin, mock_context, mock_message, mock_rate_limiter
    ):
        """Test updating limit with burst."""
        mock_context.args = ["scan", "5", "60", "3"]
        setattr(mock_context.bot_data, "user_rate_limiter", mock_rate_limiter)

        with patch(
            "src.telegram_bot.handlers.rate_limit_admin.is_admin",
            return_value=True
        ):
            await rate_limit_config_command(mock_update_admin, mock_context)

        mock_rate_limiter.update_limit.assert_called_once()

    @pytest.mark.asyncio()
    async def test_config_exception_handling(
        self, mock_update_admin, mock_context, mock_message, mock_rate_limiter
    ):
        """Test exception handling in config command."""
        mock_context.args = ["scan", "5", "60"]
        mock_rate_limiter.update_limit = MagicMock(side_effect=Exception("Config Error"))
        setattr(mock_context.bot_data, "user_rate_limiter", mock_rate_limiter)

        with patch(
            "src.telegram_bot.handlers.rate_limit_admin.is_admin",
            return_value=True
        ):
            await rate_limit_config_command(mock_update_admin, mock_context)

        mock_message.reply_text.assert_called()
        call_args = mock_message.reply_text.call_args
        assert "Ошибка" in call_args[0][0] or "Error" in call_args[0][0]
