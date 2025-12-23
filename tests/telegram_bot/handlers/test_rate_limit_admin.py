"""Tests for rate_limit_admin module.

Tests:
- Admin permission checking
- Rate limit statistics command
- Rate limit reset command
- Rate limit whitelist management
- Rate limit configuration command
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram import Update
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


@pytest.fixture
def mock_update():
    """Create a mocked Update object."""
    update = MagicMock(spec=Update)
    update.effective_user = MagicMock()
    update.effective_user.id = 123456789  # Default admin ID
    update.message = MagicMock()
    update.message.reply_text = AsyncMock()
    return update


@pytest.fixture
def mock_context():
    """Create a mocked context object."""
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.args = []
    context.bot_data = MagicMock()
    return context


@pytest.fixture
def mock_rate_limiter():
    """Create a mocked rate limiter."""
    rate_limiter = MagicMock()
    rate_limiter.get_user_stats = AsyncMock()
    rate_limiter.reset_user_limits = AsyncMock()
    rate_limiter.add_whitelist = AsyncMock()
    rate_limiter.remove_whitelist = AsyncMock()
    rate_limiter.is_whitelisted = AsyncMock()
    rate_limiter.limits = {}
    rate_limiter.update_limit = MagicMock()
    return rate_limiter


# ============================================================================
# TEST: is_admin function
# ============================================================================


class TestIsAdmin:
    """Tests for is_admin function."""

    def test_admin_user(self):
        """Test that admin user returns True."""
        # Use the first admin ID from ADMIN_IDS
        admin_id = ADMIN_IDS[0] if ADMIN_IDS else 123456789
        result = is_admin(admin_id)
        assert result is True

    def test_non_admin_user(self):
        """Test that non-admin user returns False."""
        result = is_admin(999999999)
        assert result is False

    def test_zero_id(self):
        """Test with zero ID."""
        result = is_admin(0)
        assert result is False

    def test_negative_id(self):
        """Test with negative ID."""
        result = is_admin(-1)
        assert result is False


# ============================================================================
# TEST: rate_limit_stats_command
# ============================================================================


class TestRateLimitStatsCommand:
    """Tests for rate_limit_stats_command."""

    @pytest.mark.asyncio
    async def test_no_effective_user(self, mock_context):
        """Test command with no effective user."""
        update = MagicMock(spec=Update)
        update.effective_user = None
        update.message = MagicMock()
        
        await rate_limit_stats_command(update, mock_context)
        
        # Should return early without error

    @pytest.mark.asyncio
    async def test_no_message(self, mock_context):
        """Test command with no message."""
        update = MagicMock(spec=Update)
        update.effective_user = MagicMock()
        update.effective_user.id = 123456789
        update.message = None
        
        await rate_limit_stats_command(update, mock_context)
        
        # Should return early without error

    @pytest.mark.asyncio
    async def test_non_admin_access(self, mock_update, mock_context):
        """Test command access by non-admin."""
        mock_update.effective_user.id = 999999999
        
        await rate_limit_stats_command(mock_update, mock_context)
        
        mock_update.message.reply_text.assert_called_once()
        call_text = mock_update.message.reply_text.call_args[0][0]
        assert "администратор" in call_text.lower()

    @pytest.mark.asyncio
    async def test_no_rate_limiter(self, mock_update, mock_context):
        """Test command when rate limiter not configured."""
        mock_context.bot_data = MagicMock()
        # No rate limiter attribute
        delattr(mock_context.bot_data, "user_rate_limiter") if hasattr(
            mock_context.bot_data, "user_rate_limiter"
        ) else None
        
        # Patch is_admin to return True
        with patch(
            "src.telegram_bot.handlers.rate_limit_admin.is_admin", return_value=True
        ):
            await rate_limit_stats_command(mock_update, mock_context)
        
            mock_update.message.reply_text.assert_called_once()
            call_text = mock_update.message.reply_text.call_args[0][0]
            assert "не настроен" in call_text.lower()

    @pytest.mark.asyncio
    async def test_stats_own_user(self, mock_update, mock_context, mock_rate_limiter):
        """Test getting stats for own user."""
        mock_context.bot_data.user_rate_limiter = mock_rate_limiter
        mock_context.args = []
        mock_rate_limiter.get_user_stats.return_value = {
            "scan": {"remaining": 3, "limit": 5},
            "arbitrage": {"remaining": 10, "limit": 10},
        }
        
        with patch(
            "src.telegram_bot.handlers.rate_limit_admin.is_admin", return_value=True
        ):
            await rate_limit_stats_command(mock_update, mock_context)
        
            mock_rate_limiter.get_user_stats.assert_called_once()
            mock_update.message.reply_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_stats_other_user(self, mock_update, mock_context, mock_rate_limiter):
        """Test getting stats for another user."""
        mock_context.bot_data.user_rate_limiter = mock_rate_limiter
        mock_context.args = ["555555"]
        mock_rate_limiter.get_user_stats.return_value = {
            "scan": {"remaining": 2, "limit": 5},
        }
        
        with patch(
            "src.telegram_bot.handlers.rate_limit_admin.is_admin", return_value=True
        ):
            await rate_limit_stats_command(mock_update, mock_context)
        
            mock_rate_limiter.get_user_stats.assert_called_once_with(555555)

    @pytest.mark.asyncio
    async def test_stats_error_handling(self, mock_update, mock_context, mock_rate_limiter):
        """Test error handling in stats command."""
        mock_context.bot_data.user_rate_limiter = mock_rate_limiter
        mock_rate_limiter.get_user_stats.side_effect = Exception("Database error")
        
        with patch(
            "src.telegram_bot.handlers.rate_limit_admin.is_admin", return_value=True
        ):
            await rate_limit_stats_command(mock_update, mock_context)
        
            call_text = mock_update.message.reply_text.call_args[0][0]
            assert "ошибка" in call_text.lower()


# ============================================================================
# TEST: rate_limit_reset_command
# ============================================================================


class TestRateLimitResetCommand:
    """Tests for rate_limit_reset_command."""

    @pytest.mark.asyncio
    async def test_no_effective_user(self, mock_context):
        """Test command with no effective user."""
        update = MagicMock(spec=Update)
        update.effective_user = None
        update.message = MagicMock()
        
        await rate_limit_reset_command(update, mock_context)

    @pytest.mark.asyncio
    async def test_non_admin_access(self, mock_update, mock_context):
        """Test command access by non-admin."""
        mock_update.effective_user.id = 999999999
        
        await rate_limit_reset_command(mock_update, mock_context)
        
        call_text = mock_update.message.reply_text.call_args[0][0]
        assert "администратор" in call_text.lower()

    @pytest.mark.asyncio
    async def test_no_rate_limiter(self, mock_update, mock_context, mock_rate_limiter):
        """Test command when rate limiter not configured correctly returns error."""
        mock_context.bot_data = MagicMock()
        mock_context.bot_data.user_rate_limiter = None  # Explicitly set to None
        mock_context.args = ["555555"]
        
        with patch(
            "src.telegram_bot.handlers.rate_limit_admin.is_admin", return_value=True
        ):
            await rate_limit_reset_command(mock_update, mock_context)
        
            call_text = mock_update.message.reply_text.call_args[0][0]
            # When rate limiter is None, should show error
            assert "не настроен" in call_text.lower() or "❌" in call_text

    @pytest.mark.asyncio
    async def test_missing_user_id(self, mock_update, mock_context, mock_rate_limiter):
        """Test command without user ID argument."""
        mock_context.bot_data.user_rate_limiter = mock_rate_limiter
        mock_context.args = []
        
        with patch(
            "src.telegram_bot.handlers.rate_limit_admin.is_admin", return_value=True
        ):
            await rate_limit_reset_command(mock_update, mock_context)
        
            call_text = mock_update.message.reply_text.call_args[0][0]
            assert "использование" in call_text.lower()

    @pytest.mark.asyncio
    async def test_invalid_user_id(self, mock_update, mock_context, mock_rate_limiter):
        """Test command with invalid user ID."""
        mock_context.bot_data.user_rate_limiter = mock_rate_limiter
        mock_context.args = ["invalid"]
        
        with patch(
            "src.telegram_bot.handlers.rate_limit_admin.is_admin", return_value=True
        ):
            await rate_limit_reset_command(mock_update, mock_context)
        
            call_text = mock_update.message.reply_text.call_args[0][0]
            assert "использование" in call_text.lower()

    @pytest.mark.asyncio
    async def test_reset_all_limits(self, mock_update, mock_context, mock_rate_limiter):
        """Test resetting all limits for a user."""
        mock_context.bot_data.user_rate_limiter = mock_rate_limiter
        mock_context.args = ["555555"]
        
        with patch(
            "src.telegram_bot.handlers.rate_limit_admin.is_admin", return_value=True
        ):
            await rate_limit_reset_command(mock_update, mock_context)
        
            mock_rate_limiter.reset_user_limits.assert_called_once_with(555555, None)
            call_text = mock_update.message.reply_text.call_args[0][0]
            assert "сброшены" in call_text.lower()

    @pytest.mark.asyncio
    async def test_reset_specific_action(self, mock_update, mock_context, mock_rate_limiter):
        """Test resetting specific action limit."""
        mock_context.bot_data.user_rate_limiter = mock_rate_limiter
        mock_context.args = ["555555", "scan"]
        
        with patch(
            "src.telegram_bot.handlers.rate_limit_admin.is_admin", return_value=True
        ):
            await rate_limit_reset_command(mock_update, mock_context)
        
            mock_rate_limiter.reset_user_limits.assert_called_once_with(555555, "scan")

    @pytest.mark.asyncio
    async def test_reset_error_handling(self, mock_update, mock_context, mock_rate_limiter):
        """Test error handling in reset command."""
        mock_context.bot_data.user_rate_limiter = mock_rate_limiter
        mock_context.args = ["555555"]
        mock_rate_limiter.reset_user_limits.side_effect = Exception("Reset error")
        
        with patch(
            "src.telegram_bot.handlers.rate_limit_admin.is_admin", return_value=True
        ):
            await rate_limit_reset_command(mock_update, mock_context)
        
            call_text = mock_update.message.reply_text.call_args[0][0]
            assert "ошибка" in call_text.lower()


# ============================================================================
# TEST: rate_limit_whitelist_command
# ============================================================================


class TestRateLimitWhitelistCommand:
    """Tests for rate_limit_whitelist_command."""

    @pytest.mark.asyncio
    async def test_no_effective_user(self, mock_context):
        """Test command with no effective user."""
        update = MagicMock(spec=Update)
        update.effective_user = None
        update.message = MagicMock()
        
        await rate_limit_whitelist_command(update, mock_context)

    @pytest.mark.asyncio
    async def test_non_admin_access(self, mock_update, mock_context):
        """Test command access by non-admin."""
        mock_update.effective_user.id = 999999999
        
        await rate_limit_whitelist_command(mock_update, mock_context)
        
        call_text = mock_update.message.reply_text.call_args[0][0]
        assert "администратор" in call_text.lower()

    @pytest.mark.asyncio
    async def test_no_rate_limiter(self, mock_update, mock_context, mock_rate_limiter):
        """Test command when rate limiter not configured correctly returns error."""
        mock_context.bot_data = MagicMock()
        mock_context.bot_data.user_rate_limiter = None  # Explicitly set to None
        mock_context.args = ["add", "555555"]
        
        with patch(
            "src.telegram_bot.handlers.rate_limit_admin.is_admin", return_value=True
        ):
            await rate_limit_whitelist_command(mock_update, mock_context)
        
            call_text = mock_update.message.reply_text.call_args[0][0]
            # When rate limiter is None, should show error
            assert "не настроен" in call_text.lower() or "❌" in call_text

    @pytest.mark.asyncio
    async def test_missing_args(self, mock_update, mock_context, mock_rate_limiter):
        """Test command without arguments."""
        mock_context.bot_data.user_rate_limiter = mock_rate_limiter
        mock_context.args = []
        
        with patch(
            "src.telegram_bot.handlers.rate_limit_admin.is_admin", return_value=True
        ):
            await rate_limit_whitelist_command(mock_update, mock_context)
        
            call_text = mock_update.message.reply_text.call_args[0][0]
            assert "использование" in call_text.lower()

    @pytest.mark.asyncio
    async def test_invalid_user_id(self, mock_update, mock_context, mock_rate_limiter):
        """Test command with invalid user ID."""
        mock_context.bot_data.user_rate_limiter = mock_rate_limiter
        mock_context.args = ["add", "invalid"]
        
        with patch(
            "src.telegram_bot.handlers.rate_limit_admin.is_admin", return_value=True
        ):
            await rate_limit_whitelist_command(mock_update, mock_context)
        
            call_text = mock_update.message.reply_text.call_args[0][0]
            assert "использование" in call_text.lower()

    @pytest.mark.asyncio
    async def test_add_to_whitelist(self, mock_update, mock_context, mock_rate_limiter):
        """Test adding user to whitelist."""
        mock_context.bot_data.user_rate_limiter = mock_rate_limiter
        mock_context.args = ["add", "555555"]
        
        with patch(
            "src.telegram_bot.handlers.rate_limit_admin.is_admin", return_value=True
        ):
            await rate_limit_whitelist_command(mock_update, mock_context)
        
            mock_rate_limiter.add_whitelist.assert_called_once_with(555555)
            call_text = mock_update.message.reply_text.call_args[0][0]
            assert "добавлен" in call_text.lower()

    @pytest.mark.asyncio
    async def test_remove_from_whitelist(self, mock_update, mock_context, mock_rate_limiter):
        """Test removing user from whitelist."""
        mock_context.bot_data.user_rate_limiter = mock_rate_limiter
        mock_context.args = ["remove", "555555"]
        
        with patch(
            "src.telegram_bot.handlers.rate_limit_admin.is_admin", return_value=True
        ):
            await rate_limit_whitelist_command(mock_update, mock_context)
        
            mock_rate_limiter.remove_whitelist.assert_called_once_with(555555)
            call_text = mock_update.message.reply_text.call_args[0][0]
            assert "удален" in call_text.lower()

    @pytest.mark.asyncio
    async def test_check_whitelist_is_whitelisted(self, mock_update, mock_context, mock_rate_limiter):
        """Test checking user whitelist status - whitelisted."""
        mock_context.bot_data.user_rate_limiter = mock_rate_limiter
        mock_context.args = ["check", "555555"]
        mock_rate_limiter.is_whitelisted.return_value = True
        
        with patch(
            "src.telegram_bot.handlers.rate_limit_admin.is_admin", return_value=True
        ):
            await rate_limit_whitelist_command(mock_update, mock_context)
        
            mock_rate_limiter.is_whitelisted.assert_called_once_with(555555)
            call_text = mock_update.message.reply_text.call_args[0][0]
            assert "в whitelist" in call_text.lower()

    @pytest.mark.asyncio
    async def test_check_whitelist_not_whitelisted(self, mock_update, mock_context, mock_rate_limiter):
        """Test checking user whitelist status - not whitelisted."""
        mock_context.bot_data.user_rate_limiter = mock_rate_limiter
        mock_context.args = ["check", "555555"]
        mock_rate_limiter.is_whitelisted.return_value = False
        
        with patch(
            "src.telegram_bot.handlers.rate_limit_admin.is_admin", return_value=True
        ):
            await rate_limit_whitelist_command(mock_update, mock_context)
        
            call_text = mock_update.message.reply_text.call_args[0][0]
            assert "не в whitelist" in call_text.lower()

    @pytest.mark.asyncio
    async def test_unknown_action(self, mock_update, mock_context, mock_rate_limiter):
        """Test unknown whitelist action."""
        mock_context.bot_data.user_rate_limiter = mock_rate_limiter
        mock_context.args = ["unknown", "555555"]
        
        with patch(
            "src.telegram_bot.handlers.rate_limit_admin.is_admin", return_value=True
        ):
            await rate_limit_whitelist_command(mock_update, mock_context)
        
            call_text = mock_update.message.reply_text.call_args[0][0]
            assert "неизвестное" in call_text.lower()

    @pytest.mark.asyncio
    async def test_whitelist_error_handling(self, mock_update, mock_context, mock_rate_limiter):
        """Test error handling in whitelist command."""
        mock_context.bot_data.user_rate_limiter = mock_rate_limiter
        mock_context.args = ["add", "555555"]
        mock_rate_limiter.add_whitelist.side_effect = Exception("Whitelist error")
        
        with patch(
            "src.telegram_bot.handlers.rate_limit_admin.is_admin", return_value=True
        ):
            await rate_limit_whitelist_command(mock_update, mock_context)
        
            call_text = mock_update.message.reply_text.call_args[0][0]
            assert "ошибка" in call_text.lower()


# ============================================================================
# TEST: rate_limit_config_command
# ============================================================================


class TestRateLimitConfigCommand:
    """Tests for rate_limit_config_command."""

    @pytest.mark.asyncio
    async def test_no_effective_user(self, mock_context):
        """Test command with no effective user."""
        update = MagicMock(spec=Update)
        update.effective_user = None
        update.message = MagicMock()
        
        await rate_limit_config_command(update, mock_context)

    @pytest.mark.asyncio
    async def test_non_admin_access(self, mock_update, mock_context):
        """Test command access by non-admin."""
        mock_update.effective_user.id = 999999999
        
        await rate_limit_config_command(mock_update, mock_context)
        
        call_text = mock_update.message.reply_text.call_args[0][0]
        assert "администратор" in call_text.lower()

    @pytest.mark.asyncio
    async def test_no_rate_limiter(self, mock_update, mock_context, mock_rate_limiter):
        """Test command when rate limiter not configured correctly returns error."""
        mock_context.bot_data = MagicMock()
        mock_context.bot_data.user_rate_limiter = None  # Explicitly set to None
        mock_context.args = ["scan", "5", "60"]
        
        with patch(
            "src.telegram_bot.handlers.rate_limit_admin.is_admin", return_value=True
        ):
            await rate_limit_config_command(mock_update, mock_context)
        
            call_text = mock_update.message.reply_text.call_args[0][0]
            # When rate limiter is None, should show error
            assert "не настроен" in call_text.lower() or "❌" in call_text

    @pytest.mark.asyncio
    async def test_show_current_limits(self, mock_update, mock_context, mock_rate_limiter):
        """Test showing current limits."""
        mock_context.bot_data.user_rate_limiter = mock_rate_limiter
        mock_context.args = []
        
        config1 = MagicMock()
        config1.requests = 5
        config1.window = 60
        config1.burst = None
        
        config2 = MagicMock()
        config2.requests = 10
        config2.window = 120
        config2.burst = 2
        
        mock_rate_limiter.limits = {
            "scan": config1,
            "arbitrage": config2,
        }
        
        with patch(
            "src.telegram_bot.handlers.rate_limit_admin.is_admin", return_value=True
        ):
            await rate_limit_config_command(mock_update, mock_context)
        
            call_text = mock_update.message.reply_text.call_args[0][0]
            assert "лимит" in call_text.lower()

    @pytest.mark.asyncio
    async def test_missing_args_for_update(self, mock_update, mock_context, mock_rate_limiter):
        """Test command with insufficient arguments for update."""
        mock_context.bot_data.user_rate_limiter = mock_rate_limiter
        mock_context.args = ["scan"]  # Missing requests and window
        
        with patch(
            "src.telegram_bot.handlers.rate_limit_admin.is_admin", return_value=True
        ):
            await rate_limit_config_command(mock_update, mock_context)
        
            call_text = mock_update.message.reply_text.call_args[0][0]
            assert "использование" in call_text.lower()

    @pytest.mark.asyncio
    async def test_invalid_numeric_args(self, mock_update, mock_context, mock_rate_limiter):
        """Test command with invalid numeric arguments."""
        mock_context.bot_data.user_rate_limiter = mock_rate_limiter
        mock_context.args = ["scan", "invalid", "60"]
        
        with patch(
            "src.telegram_bot.handlers.rate_limit_admin.is_admin", return_value=True
        ):
            await rate_limit_config_command(mock_update, mock_context)
        
            call_text = mock_update.message.reply_text.call_args[0][0]
            assert "использование" in call_text.lower()

    @pytest.mark.asyncio
    async def test_update_limit(self, mock_update, mock_context, mock_rate_limiter):
        """Test updating a limit."""
        mock_context.bot_data.user_rate_limiter = mock_rate_limiter
        mock_context.args = ["scan", "10", "120"]
        
        with patch(
            "src.telegram_bot.handlers.rate_limit_admin.is_admin", return_value=True
        ), patch(
            "src.telegram_bot.handlers.rate_limit_admin.RateLimitConfig"
        ) as mock_config:
            await rate_limit_config_command(mock_update, mock_context)
        
            mock_config.assert_called_once_with(requests=10, window=120, burst=None)
            mock_rate_limiter.update_limit.assert_called_once()
            call_text = mock_update.message.reply_text.call_args[0][0]
            assert "обновлен" in call_text.lower()

    @pytest.mark.asyncio
    async def test_update_limit_with_burst(self, mock_update, mock_context, mock_rate_limiter):
        """Test updating a limit with burst."""
        mock_context.bot_data.user_rate_limiter = mock_rate_limiter
        mock_context.args = ["scan", "10", "120", "3"]
        
        with patch(
            "src.telegram_bot.handlers.rate_limit_admin.is_admin", return_value=True
        ), patch(
            "src.telegram_bot.handlers.rate_limit_admin.RateLimitConfig"
        ) as mock_config:
            await rate_limit_config_command(mock_update, mock_context)
        
            mock_config.assert_called_once_with(requests=10, window=120, burst=3)

    @pytest.mark.asyncio
    async def test_config_error_handling(self, mock_update, mock_context, mock_rate_limiter):
        """Test error handling in config command."""
        mock_context.bot_data.user_rate_limiter = mock_rate_limiter
        mock_context.args = ["scan", "10", "120"]
        
        with patch(
            "src.telegram_bot.handlers.rate_limit_admin.is_admin", return_value=True
        ), patch(
            "src.telegram_bot.handlers.rate_limit_admin.RateLimitConfig",
            side_effect=Exception("Config error"),
        ):
            await rate_limit_config_command(mock_update, mock_context)
        
            call_text = mock_update.message.reply_text.call_args[0][0]
            assert "ошибка" in call_text.lower()


# ============================================================================
# TEST: Edge Cases
# ============================================================================


class TestEdgeCases:
    """Edge case tests."""

    @pytest.mark.asyncio
    async def test_stats_empty_stats(self, mock_update, mock_context, mock_rate_limiter):
        """Test stats with empty response."""
        mock_context.bot_data.user_rate_limiter = mock_rate_limiter
        mock_rate_limiter.get_user_stats.return_value = {}
        
        with patch(
            "src.telegram_bot.handlers.rate_limit_admin.is_admin", return_value=True
        ):
            await rate_limit_stats_command(mock_update, mock_context)
        
            # Should not error
            mock_update.message.reply_text.assert_called()

    @pytest.mark.asyncio
    async def test_stats_with_zero_limit(self, mock_update, mock_context, mock_rate_limiter):
        """Test stats with zero limit (edge case)."""
        mock_context.bot_data.user_rate_limiter = mock_rate_limiter
        mock_rate_limiter.get_user_stats.return_value = {
            "scan": {"remaining": 0, "limit": 0},
        }
        
        with patch(
            "src.telegram_bot.handlers.rate_limit_admin.is_admin", return_value=True
        ):
            await rate_limit_stats_command(mock_update, mock_context)
        
            # Should not error (division by zero handled)
            mock_update.message.reply_text.assert_called()

    @pytest.mark.asyncio
    async def test_whitelist_case_insensitive(self, mock_update, mock_context, mock_rate_limiter):
        """Test whitelist action case insensitivity."""
        mock_context.bot_data.user_rate_limiter = mock_rate_limiter
        mock_context.args = ["ADD", "555555"]
        
        with patch(
            "src.telegram_bot.handlers.rate_limit_admin.is_admin", return_value=True
        ):
            await rate_limit_whitelist_command(mock_update, mock_context)
        
            mock_rate_limiter.add_whitelist.assert_called_once_with(555555)
