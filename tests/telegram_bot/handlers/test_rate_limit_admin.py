"""
Comprehensive tests for rate_limit_admin.py module.

Tests cover:
- is_admin function
- rate_limit_stats_command handler
- rate_limit_reset_command handler
- rate_limit_whitelist_command handler
- rate_limit_config_command handler
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


if TYPE_CHECKING:
    pass


# ==============================================================================
# Fixtures
# ==============================================================================


@pytest.fixture
def mock_update():
    """Create a mock Telegram Update object."""
    update = MagicMock()
    update.effective_user = MagicMock()
    update.effective_user.id = 123456789  # Admin ID
    update.message = MagicMock()
    update.message.reply_text = AsyncMock()
    return update


@pytest.fixture
def mock_context():
    """Create a mock context object."""
    context = MagicMock()
    context.args = []
    context.bot_data = MagicMock()
    return context


@pytest.fixture
def mock_rate_limiter():
    """Create a mock UserRateLimiter."""
    limiter = MagicMock()
    limiter.get_user_stats = AsyncMock(return_value={
        "scan": {"remaining": 5, "limit": 10},
        "buy": {"remaining": 8, "limit": 20},
    })
    limiter.reset_user_limits = AsyncMock()
    limiter.add_whitelist = AsyncMock()
    limiter.remove_whitelist = AsyncMock()
    limiter.is_whitelisted = AsyncMock(return_value=True)
    limiter.limits = {
        "scan": MagicMock(requests=10, window=60, burst=None),
        "buy": MagicMock(requests=20, window=60, burst=5),
    }
    limiter.update_limit = MagicMock()
    return limiter


# ==============================================================================
# is_admin Tests
# ==============================================================================


class TestIsAdmin:
    """Tests for is_admin function."""

    def test_is_admin_returns_true_for_admin_id(self):
        """Test that is_admin returns True for admin users."""
        from src.telegram_bot.handlers.rate_limit_admin import ADMIN_IDS, is_admin
        
        # Add test admin ID to ADMIN_IDS temporarily
        original_ids = ADMIN_IDS.copy()
        ADMIN_IDS.clear()
        ADMIN_IDS.extend([123456789])
        
        try:
            result = is_admin(123456789)
            assert result is True
        finally:
            ADMIN_IDS.clear()
            ADMIN_IDS.extend(original_ids)

    def test_is_admin_returns_false_for_non_admin(self):
        """Test that is_admin returns False for non-admin users."""
        from src.telegram_bot.handlers.rate_limit_admin import is_admin
        
        result = is_admin(999999999)
        assert result is False

    def test_is_admin_with_zero_id(self):
        """Test is_admin with zero ID."""
        from src.telegram_bot.handlers.rate_limit_admin import is_admin
        
        result = is_admin(0)
        assert result is False


# ==============================================================================
# rate_limit_stats_command Tests
# ==============================================================================


class TestRateLimitStatsCommand:
    """Tests for rate_limit_stats_command handler."""

    @pytest.mark.asyncio
    async def test_stats_command_returns_early_when_no_user(self, mock_context):
        """Test handler returns early when no effective_user."""
        from src.telegram_bot.handlers.rate_limit_admin import rate_limit_stats_command
        
        update = MagicMock()
        update.effective_user = None
        update.message = None
        
        await rate_limit_stats_command(update, mock_context)
        # Should return early without error

    @pytest.mark.asyncio
    async def test_stats_command_returns_early_when_no_message(self, mock_context):
        """Test handler returns early when no message."""
        from src.telegram_bot.handlers.rate_limit_admin import rate_limit_stats_command
        
        update = MagicMock()
        update.effective_user = MagicMock()
        update.message = None
        
        await rate_limit_stats_command(update, mock_context)
        # Should return early without error

    @pytest.mark.asyncio
    async def test_stats_command_rejects_non_admin(self, mock_update, mock_context):
        """Test handler rejects non-admin users."""
        from src.telegram_bot.handlers.rate_limit_admin import rate_limit_stats_command
        
        # Set non-admin user ID
        mock_update.effective_user.id = 999999999
        
        await rate_limit_stats_command(mock_update, mock_context)
        
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args[0][0]
        assert "только администраторам" in call_args

    @pytest.mark.asyncio
    async def test_stats_command_handles_missing_rate_limiter(
        self, mock_update, mock_context
    ):
        """Test handler when rate limiter is not configured."""
        from src.telegram_bot.handlers.rate_limit_admin import (
            ADMIN_IDS,
            rate_limit_stats_command,
        )
        
        original_ids = ADMIN_IDS.copy()
        ADMIN_IDS.clear()
        ADMIN_IDS.extend([mock_update.effective_user.id])
        
        # No rate_limiter in bot_data
        mock_context.bot_data = MagicMock()
        delattr(mock_context.bot_data, "user_rate_limiter")
        
        try:
            await rate_limit_stats_command(mock_update, mock_context)
            mock_update.message.reply_text.assert_called()
            call_args = mock_update.message.reply_text.call_args[0][0]
            assert "не настроен" in call_args
        finally:
            ADMIN_IDS.clear()
            ADMIN_IDS.extend(original_ids)

    @pytest.mark.asyncio
    async def test_stats_command_shows_stats_for_current_user(
        self, mock_update, mock_context, mock_rate_limiter
    ):
        """Test showing stats for current user when no args provided."""
        from src.telegram_bot.handlers.rate_limit_admin import (
            ADMIN_IDS,
            rate_limit_stats_command,
        )
        
        original_ids = ADMIN_IDS.copy()
        ADMIN_IDS.clear()
        ADMIN_IDS.extend([mock_update.effective_user.id])
        mock_context.bot_data.user_rate_limiter = mock_rate_limiter
        mock_context.args = []
        
        try:
            await rate_limit_stats_command(mock_update, mock_context)
            mock_rate_limiter.get_user_stats.assert_called_once_with(
                mock_update.effective_user.id
            )
        finally:
            ADMIN_IDS.clear()
            ADMIN_IDS.extend(original_ids)

    @pytest.mark.asyncio
    async def test_stats_command_shows_stats_for_specified_user(
        self, mock_update, mock_context, mock_rate_limiter
    ):
        """Test showing stats for specified user ID."""
        from src.telegram_bot.handlers.rate_limit_admin import (
            ADMIN_IDS,
            rate_limit_stats_command,
        )
        
        original_ids = ADMIN_IDS.copy()
        ADMIN_IDS.clear()
        ADMIN_IDS.extend([mock_update.effective_user.id])
        mock_context.bot_data.user_rate_limiter = mock_rate_limiter
        mock_context.args = ["987654321"]
        
        try:
            await rate_limit_stats_command(mock_update, mock_context)
            mock_rate_limiter.get_user_stats.assert_called_once_with(987654321)
        finally:
            ADMIN_IDS.clear()
            ADMIN_IDS.extend(original_ids)

    @pytest.mark.asyncio
    async def test_stats_command_handles_exception(
        self, mock_update, mock_context, mock_rate_limiter
    ):
        """Test error handling when getting stats fails."""
        from src.telegram_bot.handlers.rate_limit_admin import (
            ADMIN_IDS,
            rate_limit_stats_command,
        )
        
        original_ids = ADMIN_IDS.copy()
        ADMIN_IDS.clear()
        ADMIN_IDS.extend([mock_update.effective_user.id])
        mock_rate_limiter.get_user_stats.side_effect = Exception("Test error")
        mock_context.bot_data.user_rate_limiter = mock_rate_limiter
        
        try:
            await rate_limit_stats_command(mock_update, mock_context)
            mock_update.message.reply_text.assert_called()
            call_args = mock_update.message.reply_text.call_args[0][0]
            assert "Ошибка" in call_args
        finally:
            ADMIN_IDS.clear()
            ADMIN_IDS.extend(original_ids)


# ==============================================================================
# rate_limit_reset_command Tests
# ==============================================================================


class TestRateLimitResetCommand:
    """Tests for rate_limit_reset_command handler."""

    @pytest.mark.asyncio
    async def test_reset_command_returns_early_when_no_user(self, mock_context):
        """Test handler returns early when no effective_user."""
        from src.telegram_bot.handlers.rate_limit_admin import rate_limit_reset_command
        
        update = MagicMock()
        update.effective_user = None
        update.message = None
        
        await rate_limit_reset_command(update, mock_context)

    @pytest.mark.asyncio
    async def test_reset_command_rejects_non_admin(self, mock_update, mock_context):
        """Test handler rejects non-admin users."""
        from src.telegram_bot.handlers.rate_limit_admin import rate_limit_reset_command
        
        mock_update.effective_user.id = 999999999
        
        await rate_limit_reset_command(mock_update, mock_context)
        
        call_args = mock_update.message.reply_text.call_args[0][0]
        assert "только администраторам" in call_args

    @pytest.mark.asyncio
    async def test_reset_command_requires_user_id_arg(
        self, mock_update, mock_context, mock_rate_limiter
    ):
        """Test handler requires user_id argument."""
        from src.telegram_bot.handlers.rate_limit_admin import (
            ADMIN_IDS,
            rate_limit_reset_command,
        )
        
        original_ids = ADMIN_IDS.copy()
        ADMIN_IDS.clear()
        ADMIN_IDS.extend([mock_update.effective_user.id])
        mock_context.bot_data.user_rate_limiter = mock_rate_limiter
        mock_context.args = []
        
        try:
            await rate_limit_reset_command(mock_update, mock_context)
            call_args = mock_update.message.reply_text.call_args[0][0]
            assert "Использование" in call_args
        finally:
            ADMIN_IDS.clear()
            ADMIN_IDS.extend(original_ids)

    @pytest.mark.asyncio
    async def test_reset_command_resets_all_limits(
        self, mock_update, mock_context, mock_rate_limiter
    ):
        """Test resetting all limits for a user."""
        from src.telegram_bot.handlers.rate_limit_admin import (
            ADMIN_IDS,
            rate_limit_reset_command,
        )
        
        original_ids = ADMIN_IDS.copy()
        ADMIN_IDS.clear()
        ADMIN_IDS.extend([mock_update.effective_user.id])
        mock_context.bot_data.user_rate_limiter = mock_rate_limiter
        mock_context.args = ["987654321"]
        
        try:
            await rate_limit_reset_command(mock_update, mock_context)
            mock_rate_limiter.reset_user_limits.assert_called_once_with(987654321, None)
            call_args = mock_update.message.reply_text.call_args[0][0]
            assert "сброшены" in call_args
        finally:
            ADMIN_IDS.clear()
            ADMIN_IDS.extend(original_ids)

    @pytest.mark.asyncio
    async def test_reset_command_resets_specific_action(
        self, mock_update, mock_context, mock_rate_limiter
    ):
        """Test resetting specific action limits for a user."""
        from src.telegram_bot.handlers.rate_limit_admin import (
            ADMIN_IDS,
            rate_limit_reset_command,
        )
        
        original_ids = ADMIN_IDS.copy()
        ADMIN_IDS.clear()
        ADMIN_IDS.extend([mock_update.effective_user.id])
        mock_context.bot_data.user_rate_limiter = mock_rate_limiter
        mock_context.args = ["987654321", "scan"]
        
        try:
            await rate_limit_reset_command(mock_update, mock_context)
            mock_rate_limiter.reset_user_limits.assert_called_once_with(
                987654321, "scan"
            )
        finally:
            ADMIN_IDS.clear()
            ADMIN_IDS.extend(original_ids)


# ==============================================================================
# rate_limit_whitelist_command Tests
# ==============================================================================


class TestRateLimitWhitelistCommand:
    """Tests for rate_limit_whitelist_command handler."""

    @pytest.mark.asyncio
    async def test_whitelist_command_rejects_non_admin(
        self, mock_update, mock_context
    ):
        """Test handler rejects non-admin users."""
        from src.telegram_bot.handlers.rate_limit_admin import (
            rate_limit_whitelist_command,
        )
        
        mock_update.effective_user.id = 999999999
        
        await rate_limit_whitelist_command(mock_update, mock_context)
        
        call_args = mock_update.message.reply_text.call_args[0][0]
        assert "только администраторам" in call_args

    @pytest.mark.asyncio
    async def test_whitelist_command_shows_usage_without_args(
        self, mock_update, mock_context, mock_rate_limiter
    ):
        """Test handler shows usage when no args provided."""
        from src.telegram_bot.handlers.rate_limit_admin import (
            ADMIN_IDS,
            rate_limit_whitelist_command,
        )
        
        original_ids = ADMIN_IDS.copy()
        ADMIN_IDS.clear()
        ADMIN_IDS.extend([mock_update.effective_user.id])
        mock_context.bot_data.user_rate_limiter = mock_rate_limiter
        mock_context.args = []
        
        try:
            await rate_limit_whitelist_command(mock_update, mock_context)
            call_args = mock_update.message.reply_text.call_args[0][0]
            assert "Использование" in call_args
        finally:
            ADMIN_IDS.clear()
            ADMIN_IDS.extend(original_ids)

    @pytest.mark.asyncio
    async def test_whitelist_command_adds_user(
        self, mock_update, mock_context, mock_rate_limiter
    ):
        """Test adding user to whitelist."""
        from src.telegram_bot.handlers.rate_limit_admin import (
            ADMIN_IDS,
            rate_limit_whitelist_command,
        )
        
        original_ids = ADMIN_IDS.copy()
        ADMIN_IDS.clear()
        ADMIN_IDS.extend([mock_update.effective_user.id])
        mock_context.bot_data.user_rate_limiter = mock_rate_limiter
        mock_context.args = ["add", "987654321"]
        
        try:
            await rate_limit_whitelist_command(mock_update, mock_context)
            mock_rate_limiter.add_whitelist.assert_called_once_with(987654321)
            call_args = mock_update.message.reply_text.call_args[0][0]
            assert "добавлен" in call_args
        finally:
            ADMIN_IDS.clear()
            ADMIN_IDS.extend(original_ids)

    @pytest.mark.asyncio
    async def test_whitelist_command_removes_user(
        self, mock_update, mock_context, mock_rate_limiter
    ):
        """Test removing user from whitelist."""
        from src.telegram_bot.handlers.rate_limit_admin import (
            ADMIN_IDS,
            rate_limit_whitelist_command,
        )
        
        original_ids = ADMIN_IDS.copy()
        ADMIN_IDS.clear()
        ADMIN_IDS.extend([mock_update.effective_user.id])
        mock_context.bot_data.user_rate_limiter = mock_rate_limiter
        mock_context.args = ["remove", "987654321"]
        
        try:
            await rate_limit_whitelist_command(mock_update, mock_context)
            mock_rate_limiter.remove_whitelist.assert_called_once_with(987654321)
            call_args = mock_update.message.reply_text.call_args[0][0]
            assert "удален" in call_args
        finally:
            ADMIN_IDS.clear()
            ADMIN_IDS.extend(original_ids)

    @pytest.mark.asyncio
    async def test_whitelist_command_checks_user(
        self, mock_update, mock_context, mock_rate_limiter
    ):
        """Test checking if user is in whitelist."""
        from src.telegram_bot.handlers.rate_limit_admin import (
            ADMIN_IDS,
            rate_limit_whitelist_command,
        )
        
        original_ids = ADMIN_IDS.copy()
        ADMIN_IDS.clear()
        ADMIN_IDS.extend([mock_update.effective_user.id])
        mock_context.bot_data.user_rate_limiter = mock_rate_limiter
        mock_context.args = ["check", "987654321"]
        
        try:
            await rate_limit_whitelist_command(mock_update, mock_context)
            mock_rate_limiter.is_whitelisted.assert_called_once_with(987654321)
            call_args = mock_update.message.reply_text.call_args[0][0]
            assert "whitelist" in call_args
        finally:
            ADMIN_IDS.clear()
            ADMIN_IDS.extend(original_ids)

    @pytest.mark.asyncio
    async def test_whitelist_command_handles_unknown_action(
        self, mock_update, mock_context, mock_rate_limiter
    ):
        """Test handling unknown action."""
        from src.telegram_bot.handlers.rate_limit_admin import (
            ADMIN_IDS,
            rate_limit_whitelist_command,
        )
        
        original_ids = ADMIN_IDS.copy()
        ADMIN_IDS.clear()
        ADMIN_IDS.extend([mock_update.effective_user.id])
        mock_context.bot_data.user_rate_limiter = mock_rate_limiter
        mock_context.args = ["invalid", "987654321"]
        
        try:
            await rate_limit_whitelist_command(mock_update, mock_context)
            call_args = mock_update.message.reply_text.call_args[0][0]
            assert "Неизвестное действие" in call_args
        finally:
            ADMIN_IDS.clear()
            ADMIN_IDS.extend(original_ids)


# ==============================================================================
# rate_limit_config_command Tests
# ==============================================================================


class TestRateLimitConfigCommand:
    """Tests for rate_limit_config_command handler."""

    @pytest.mark.asyncio
    async def test_config_command_rejects_non_admin(
        self, mock_update, mock_context
    ):
        """Test handler rejects non-admin users."""
        from src.telegram_bot.handlers.rate_limit_admin import rate_limit_config_command
        
        mock_update.effective_user.id = 999999999
        
        await rate_limit_config_command(mock_update, mock_context)
        
        call_args = mock_update.message.reply_text.call_args[0][0]
        assert "только администраторам" in call_args

    @pytest.mark.asyncio
    async def test_config_command_shows_current_limits(
        self, mock_update, mock_context, mock_rate_limiter
    ):
        """Test showing current limits when no args provided."""
        from src.telegram_bot.handlers.rate_limit_admin import (
            ADMIN_IDS,
            rate_limit_config_command,
        )
        
        original_ids = ADMIN_IDS.copy()
        ADMIN_IDS.clear()
        ADMIN_IDS.extend([mock_update.effective_user.id])
        mock_context.bot_data.user_rate_limiter = mock_rate_limiter
        mock_context.args = []
        
        try:
            await rate_limit_config_command(mock_update, mock_context)
            call_args = mock_update.message.reply_text.call_args[0][0]
            assert "Текущие лимиты" in call_args
        finally:
            ADMIN_IDS.clear()
            ADMIN_IDS.extend(original_ids)

    @pytest.mark.asyncio
    async def test_config_command_updates_limit(
        self, mock_update, mock_context, mock_rate_limiter
    ):
        """Test updating a limit configuration."""
        from src.telegram_bot.handlers.rate_limit_admin import (
            ADMIN_IDS,
            rate_limit_config_command,
        )
        
        original_ids = ADMIN_IDS.copy()
        ADMIN_IDS.clear()
        ADMIN_IDS.extend([mock_update.effective_user.id])
        mock_context.bot_data.user_rate_limiter = mock_rate_limiter
        mock_context.args = ["scan", "5", "60"]
        
        try:
            await rate_limit_config_command(mock_update, mock_context)
            mock_rate_limiter.update_limit.assert_called_once()
            call_args = mock_update.message.reply_text.call_args[0][0]
            assert "обновлен" in call_args
        finally:
            ADMIN_IDS.clear()
            ADMIN_IDS.extend(original_ids)

    @pytest.mark.asyncio
    async def test_config_command_updates_limit_with_burst(
        self, mock_update, mock_context, mock_rate_limiter
    ):
        """Test updating limit with burst parameter."""
        from src.telegram_bot.handlers.rate_limit_admin import (
            ADMIN_IDS,
            rate_limit_config_command,
        )
        
        original_ids = ADMIN_IDS.copy()
        ADMIN_IDS.clear()
        ADMIN_IDS.extend([mock_update.effective_user.id])
        mock_context.bot_data.user_rate_limiter = mock_rate_limiter
        mock_context.args = ["scan", "5", "60", "10"]
        
        try:
            await rate_limit_config_command(mock_update, mock_context)
            mock_rate_limiter.update_limit.assert_called_once()
            call_args = mock_update.message.reply_text.call_args[0][0]
            assert "Burst" in call_args
        finally:
            ADMIN_IDS.clear()
            ADMIN_IDS.extend(original_ids)

    @pytest.mark.asyncio
    async def test_config_command_shows_usage_with_invalid_args(
        self, mock_update, mock_context, mock_rate_limiter
    ):
        """Test showing usage when args are invalid."""
        from src.telegram_bot.handlers.rate_limit_admin import (
            ADMIN_IDS,
            rate_limit_config_command,
        )
        
        original_ids = ADMIN_IDS.copy()
        ADMIN_IDS.clear()
        ADMIN_IDS.extend([mock_update.effective_user.id])
        mock_context.bot_data.user_rate_limiter = mock_rate_limiter
        mock_context.args = ["scan"]  # Missing required args
        
        try:
            await rate_limit_config_command(mock_update, mock_context)
            call_args = mock_update.message.reply_text.call_args[0][0]
            assert "Использование" in call_args
        finally:
            ADMIN_IDS.clear()
            ADMIN_IDS.extend(original_ids)
