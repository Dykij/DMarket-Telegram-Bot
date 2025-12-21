"""
Comprehensive tests for resume_command.py module.

Tests cover:
- resume_command handler
- State manager interactions
- Admin authorization
- Error handling
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest


# ==============================================================================
# Fixtures
# ==============================================================================


@pytest.fixture
def mock_update():
    """Create a mock Telegram Update object."""
    update = MagicMock()
    update.effective_user = MagicMock()
    update.effective_user.id = 123456789
    update.message = MagicMock()
    update.message.reply_text = AsyncMock()
    return update


@pytest.fixture
def mock_context():
    """Create a mock context object."""
    context = MagicMock()
    context.bot_data = {}
    return context


@pytest.fixture
def mock_state_manager():
    """Create a mock state manager."""
    manager = MagicMock()
    manager.is_paused = True
    manager.consecutive_errors = 5
    manager.resume_operations = MagicMock()
    return manager


# ==============================================================================
# resume_command Tests
# ==============================================================================


class TestResumeCommand:
    """Tests for resume_command handler."""

    @pytest.mark.asyncio
    async def test_resume_returns_early_when_no_message(self, mock_context):
        """Test handler returns early when no message."""
        from src.telegram_bot.commands.resume_command import resume_command
        
        update = MagicMock()
        update.message = None
        update.effective_user = MagicMock()
        
        await resume_command(update, mock_context)
        # Should return early without error

    @pytest.mark.asyncio
    async def test_resume_returns_early_when_no_user(self, mock_context):
        """Test handler returns early when no effective_user."""
        from src.telegram_bot.commands.resume_command import resume_command
        
        update = MagicMock()
        update.message = MagicMock()
        update.effective_user = None
        
        await resume_command(update, mock_context)
        # Should return early without error

    @pytest.mark.asyncio
    async def test_resume_handles_missing_state_manager(
        self, mock_update, mock_context
    ):
        """Test handler when state_manager is not configured."""
        from src.telegram_bot.commands.resume_command import resume_command
        
        mock_context.bot_data = {}  # No state_manager
        
        await resume_command(mock_update, mock_context)
        
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args[0][0]
        assert "недоступна" in call_args

    @pytest.mark.asyncio
    async def test_resume_when_bot_not_paused(
        self, mock_update, mock_context, mock_state_manager
    ):
        """Test handler when bot is not paused."""
        from src.telegram_bot.commands.resume_command import resume_command
        
        mock_state_manager.is_paused = False
        mock_context.bot_data = {"state_manager": mock_state_manager}
        
        await resume_command(mock_update, mock_context)
        
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args[0][0]
        assert "не находится на паузе" in call_args

    @pytest.mark.asyncio
    async def test_resume_resumes_operations(
        self, mock_update, mock_context, mock_state_manager
    ):
        """Test successful resume of operations."""
        from src.telegram_bot.commands.resume_command import resume_command
        
        mock_context.bot_data = {"state_manager": mock_state_manager}
        
        await resume_command(mock_update, mock_context)
        
        mock_state_manager.resume_operations.assert_called_once()
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args[0][0]
        assert "возобновлена" in call_args

    @pytest.mark.asyncio
    async def test_resume_shows_reset_error_count(
        self, mock_update, mock_context, mock_state_manager
    ):
        """Test that resume message shows reset error count."""
        from src.telegram_bot.commands.resume_command import resume_command
        
        mock_state_manager.consecutive_errors = 10
        mock_context.bot_data = {"state_manager": mock_state_manager}
        
        await resume_command(mock_update, mock_context)
        
        call_args = mock_update.message.reply_text.call_args[0][0]
        assert "10" in call_args

    @pytest.mark.asyncio
    async def test_resume_rejects_non_admin_when_config_exists(
        self, mock_update, mock_context, mock_state_manager
    ):
        """Test handler rejects non-admin when admin_users configured."""
        from src.telegram_bot.commands.resume_command import resume_command
        
        # Setup config with admin_users
        config = MagicMock()
        config.security = MagicMock()
        config.security.admin_users = [999999999]  # Different from mock_update user ID
        
        mock_context.bot_data = {
            "state_manager": mock_state_manager,
            "config": config,
        }
        
        await resume_command(mock_update, mock_context)
        
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args[0][0]
        assert "администраторы" in call_args

    @pytest.mark.asyncio
    async def test_resume_allows_admin_user(
        self, mock_update, mock_context, mock_state_manager
    ):
        """Test handler allows admin user when admin_users configured."""
        from src.telegram_bot.commands.resume_command import resume_command
        
        # Setup config with admin_users including mock user
        config = MagicMock()
        config.security = MagicMock()
        config.security.admin_users = [mock_update.effective_user.id]
        
        mock_context.bot_data = {
            "state_manager": mock_state_manager,
            "config": config,
        }
        
        await resume_command(mock_update, mock_context)
        
        # Should resume operations
        mock_state_manager.resume_operations.assert_called_once()

    @pytest.mark.asyncio
    async def test_resume_allows_when_no_admin_users_config(
        self, mock_update, mock_context, mock_state_manager
    ):
        """Test handler allows when no admin_users configured."""
        from src.telegram_bot.commands.resume_command import resume_command
        
        # Setup config without admin_users
        config = MagicMock()
        config.security = MagicMock()
        config.security.admin_users = None
        
        mock_context.bot_data = {
            "state_manager": mock_state_manager,
            "config": config,
        }
        
        await resume_command(mock_update, mock_context)
        
        # Should resume operations
        mock_state_manager.resume_operations.assert_called_once()

    @pytest.mark.asyncio
    async def test_resume_allows_when_empty_admin_users(
        self, mock_update, mock_context, mock_state_manager
    ):
        """Test handler allows when admin_users is empty."""
        from src.telegram_bot.commands.resume_command import resume_command
        
        # Setup config with empty admin_users
        config = MagicMock()
        config.security = MagicMock()
        config.security.admin_users = []
        
        mock_context.bot_data = {
            "state_manager": mock_state_manager,
            "config": config,
        }
        
        await resume_command(mock_update, mock_context)
        
        # Should resume operations
        mock_state_manager.resume_operations.assert_called_once()

    @pytest.mark.asyncio
    async def test_resume_handles_config_without_security(
        self, mock_update, mock_context, mock_state_manager
    ):
        """Test handler when config has no security attribute."""
        from src.telegram_bot.commands.resume_command import resume_command
        
        # Setup config without security
        config = MagicMock(spec=[])
        
        mock_context.bot_data = {
            "state_manager": mock_state_manager,
            "config": config,
        }
        
        await resume_command(mock_update, mock_context)
        
        # Should resume operations (no admin check)
        mock_state_manager.resume_operations.assert_called_once()

    @pytest.mark.asyncio
    async def test_resume_works_without_config(
        self, mock_update, mock_context, mock_state_manager
    ):
        """Test handler works without config in bot_data."""
        from src.telegram_bot.commands.resume_command import resume_command
        
        mock_context.bot_data = {"state_manager": mock_state_manager}
        
        await resume_command(mock_update, mock_context)
        
        # Should resume operations
        mock_state_manager.resume_operations.assert_called_once()
