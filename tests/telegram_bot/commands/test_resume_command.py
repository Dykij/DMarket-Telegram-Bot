"""Unit tests for resume_command module.

Tests for the /resume command handler.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.telegram_bot.commands.resume_command import resume_command


class TestResumeCommandBasic:
    """Basic tests for resume_command function."""

    @pytest.mark.asyncio
    async def test_resume_returns_early_without_message(self):
        """Test that resume returns early if update has no message."""
        mock_update = MagicMock()
        mock_update.message = None
        mock_context = MagicMock()

        await resume_command(mock_update, mock_context)

        # Should not raise, just return

    @pytest.mark.asyncio
    async def test_resume_returns_early_without_user(self):
        """Test that resume returns early if no effective_user."""
        mock_update = MagicMock()
        mock_update.message = MagicMock()
        mock_update.effective_user = None
        mock_context = MagicMock()

        await resume_command(mock_update, mock_context)

        # Should not raise, just return


class TestResumeCommandNoStateManager:
    """Tests for resume_command when state_manager is not available."""

    @pytest.mark.asyncio
    async def test_resume_without_state_manager(self):
        """Test resume when state_manager is not in bot_data."""
        mock_update = MagicMock()
        mock_update.message = MagicMock()
        mock_update.message.reply_text = AsyncMock()
        mock_update.effective_user = MagicMock()
        mock_update.effective_user.id = 123456

        mock_context = MagicMock()
        mock_context.bot_data = {}

        await resume_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "недоступна" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_resume_with_none_state_manager(self):
        """Test resume when state_manager is explicitly None."""
        mock_update = MagicMock()
        mock_update.message = MagicMock()
        mock_update.message.reply_text = AsyncMock()
        mock_update.effective_user = MagicMock()
        mock_update.effective_user.id = 123456

        mock_context = MagicMock()
        mock_context.bot_data = {"state_manager": None}

        await resume_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()


class TestResumeCommandNotPaused:
    """Tests for resume_command when bot is not paused."""

    @pytest.mark.asyncio
    async def test_resume_when_not_paused(self):
        """Test resume when bot is not paused."""
        mock_update = MagicMock()
        mock_update.message = MagicMock()
        mock_update.message.reply_text = AsyncMock()
        mock_update.effective_user = MagicMock()
        mock_update.effective_user.id = 123456

        mock_state_manager = MagicMock()
        mock_state_manager.is_paused = False
        mock_state_manager.consecutive_errors = 0

        mock_context = MagicMock()
        mock_context.bot_data = {"state_manager": mock_state_manager}

        await resume_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "не находится на паузе" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_resume_when_not_paused_shows_errors(self):
        """Test that resume shows current error count when not paused."""
        mock_update = MagicMock()
        mock_update.message = MagicMock()
        mock_update.message.reply_text = AsyncMock()
        mock_update.effective_user = MagicMock()
        mock_update.effective_user.id = 123456

        mock_state_manager = MagicMock()
        mock_state_manager.is_paused = False
        mock_state_manager.consecutive_errors = 3

        mock_context = MagicMock()
        mock_context.bot_data = {"state_manager": mock_state_manager}

        await resume_command(mock_update, mock_context)

        call_args = mock_update.message.reply_text.call_args
        assert "3" in call_args[0][0]


class TestResumeCommandAdminCheck:
    """Tests for admin authorization in resume_command."""

    @pytest.mark.asyncio
    async def test_resume_denied_for_non_admin(self):
        """Test that resume is denied for non-admin users."""
        mock_update = MagicMock()
        mock_update.message = MagicMock()
        mock_update.message.reply_text = AsyncMock()
        mock_update.effective_user = MagicMock()
        mock_update.effective_user.id = 999999  # Non-admin user

        mock_state_manager = MagicMock()
        mock_state_manager.is_paused = True

        mock_config = MagicMock()
        mock_config.security.admin_users = [123456]  # Different user

        mock_context = MagicMock()
        mock_context.bot_data = {
            "state_manager": mock_state_manager,
            "config": mock_config,
        }

        await resume_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "администратор" in call_args[0][0].lower()

    @pytest.mark.asyncio
    async def test_resume_allowed_for_admin(self):
        """Test that resume is allowed for admin users."""
        mock_update = MagicMock()
        mock_update.message = MagicMock()
        mock_update.message.reply_text = AsyncMock()
        mock_update.effective_user = MagicMock()
        mock_update.effective_user.id = 123456  # Admin user

        mock_state_manager = MagicMock()
        mock_state_manager.is_paused = True
        mock_state_manager.consecutive_errors = 5

        mock_config = MagicMock()
        mock_config.security.admin_users = [123456]

        mock_context = MagicMock()
        mock_context.bot_data = {
            "state_manager": mock_state_manager,
            "config": mock_config,
        }

        await resume_command(mock_update, mock_context)

        mock_state_manager.resume_operations.assert_called_once()

    @pytest.mark.asyncio
    async def test_resume_allowed_when_no_admin_config(self):
        """Test that resume is allowed when no admin config."""
        mock_update = MagicMock()
        mock_update.message = MagicMock()
        mock_update.message.reply_text = AsyncMock()
        mock_update.effective_user = MagicMock()
        mock_update.effective_user.id = 123456

        mock_state_manager = MagicMock()
        mock_state_manager.is_paused = True
        mock_state_manager.consecutive_errors = 3

        mock_context = MagicMock()
        mock_context.bot_data = {"state_manager": mock_state_manager}

        await resume_command(mock_update, mock_context)

        mock_state_manager.resume_operations.assert_called_once()

    @pytest.mark.asyncio
    async def test_resume_allowed_when_empty_admin_list(self):
        """Test that resume is allowed when admin list is empty."""
        mock_update = MagicMock()
        mock_update.message = MagicMock()
        mock_update.message.reply_text = AsyncMock()
        mock_update.effective_user = MagicMock()
        mock_update.effective_user.id = 123456

        mock_state_manager = MagicMock()
        mock_state_manager.is_paused = True
        mock_state_manager.consecutive_errors = 2

        mock_config = MagicMock()
        mock_config.security.admin_users = []

        mock_context = MagicMock()
        mock_context.bot_data = {
            "state_manager": mock_state_manager,
            "config": mock_config,
        }

        await resume_command(mock_update, mock_context)

        mock_state_manager.resume_operations.assert_called_once()


class TestResumeCommandSuccess:
    """Tests for successful resume operation."""

    @pytest.mark.asyncio
    async def test_resume_calls_resume_operations(self):
        """Test that resume calls state_manager.resume_operations."""
        mock_update = MagicMock()
        mock_update.message = MagicMock()
        mock_update.message.reply_text = AsyncMock()
        mock_update.effective_user = MagicMock()
        mock_update.effective_user.id = 123456

        mock_state_manager = MagicMock()
        mock_state_manager.is_paused = True
        mock_state_manager.consecutive_errors = 5

        mock_context = MagicMock()
        mock_context.bot_data = {"state_manager": mock_state_manager}

        await resume_command(mock_update, mock_context)

        mock_state_manager.resume_operations.assert_called_once()

    @pytest.mark.asyncio
    async def test_resume_success_message(self):
        """Test that successful resume shows correct message."""
        mock_update = MagicMock()
        mock_update.message = MagicMock()
        mock_update.message.reply_text = AsyncMock()
        mock_update.effective_user = MagicMock()
        mock_update.effective_user.id = 123456

        mock_state_manager = MagicMock()
        mock_state_manager.is_paused = True
        mock_state_manager.consecutive_errors = 10

        mock_context = MagicMock()
        mock_context.bot_data = {"state_manager": mock_state_manager}

        await resume_command(mock_update, mock_context)

        call_args = mock_update.message.reply_text.call_args
        message = call_args[0][0]
        assert "возобновлена" in message
        assert "10" in message

    @pytest.mark.asyncio
    async def test_resume_resets_error_count_in_message(self):
        """Test that resume message shows reset error count."""
        mock_update = MagicMock()
        mock_update.message = MagicMock()
        mock_update.message.reply_text = AsyncMock()
        mock_update.effective_user = MagicMock()
        mock_update.effective_user.id = 123456

        mock_state_manager = MagicMock()
        mock_state_manager.is_paused = True
        mock_state_manager.consecutive_errors = 15

        mock_context = MagicMock()
        mock_context.bot_data = {"state_manager": mock_state_manager}

        await resume_command(mock_update, mock_context)

        call_args = mock_update.message.reply_text.call_args
        message = call_args[0][0]
        assert "15" in message  # Shows old error count


class TestResumeCommandLogging:
    """Tests for logging in resume_command."""

    @pytest.mark.asyncio
    @patch("src.telegram_bot.commands.resume_command.logger")
    async def test_resume_logs_error_when_no_state_manager(self, mock_logger):
        """Test that error is logged when state_manager not found."""
        mock_update = MagicMock()
        mock_update.message = MagicMock()
        mock_update.message.reply_text = AsyncMock()
        mock_update.effective_user = MagicMock()
        mock_update.effective_user.id = 123456

        mock_context = MagicMock()
        mock_context.bot_data = {}

        await resume_command(mock_update, mock_context)

        mock_logger.error.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.telegram_bot.commands.resume_command.logger")
    async def test_resume_logs_info_when_not_paused(self, mock_logger):
        """Test that info is logged when bot not paused."""
        mock_update = MagicMock()
        mock_update.message = MagicMock()
        mock_update.message.reply_text = AsyncMock()
        mock_update.effective_user = MagicMock()
        mock_update.effective_user.id = 123456

        mock_state_manager = MagicMock()
        mock_state_manager.is_paused = False
        mock_state_manager.consecutive_errors = 0

        mock_context = MagicMock()
        mock_context.bot_data = {"state_manager": mock_state_manager}

        await resume_command(mock_update, mock_context)

        mock_logger.info.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.telegram_bot.commands.resume_command.logger")
    async def test_resume_logs_warning_for_unauthorized(self, mock_logger):
        """Test that warning is logged for unauthorized attempts."""
        mock_update = MagicMock()
        mock_update.message = MagicMock()
        mock_update.message.reply_text = AsyncMock()
        mock_update.effective_user = MagicMock()
        mock_update.effective_user.id = 999999

        mock_state_manager = MagicMock()
        mock_state_manager.is_paused = True

        mock_config = MagicMock()
        mock_config.security.admin_users = [123456]

        mock_context = MagicMock()
        mock_context.bot_data = {
            "state_manager": mock_state_manager,
            "config": mock_config,
        }

        await resume_command(mock_update, mock_context)

        mock_logger.warning.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.telegram_bot.commands.resume_command.logger")
    async def test_resume_logs_info_on_success(self, mock_logger):
        """Test that info is logged on successful resume."""
        mock_update = MagicMock()
        mock_update.message = MagicMock()
        mock_update.message.reply_text = AsyncMock()
        mock_update.effective_user = MagicMock()
        mock_update.effective_user.id = 123456

        mock_state_manager = MagicMock()
        mock_state_manager.is_paused = True
        mock_state_manager.consecutive_errors = 5

        mock_context = MagicMock()
        mock_context.bot_data = {"state_manager": mock_state_manager}

        await resume_command(mock_update, mock_context)

        mock_logger.info.assert_called_once()


class TestResumeCommandEdgeCases:
    """Tests for edge cases in resume_command."""

    @pytest.mark.asyncio
    async def test_resume_with_zero_errors(self):
        """Test resume when consecutive_errors is zero."""
        mock_update = MagicMock()
        mock_update.message = MagicMock()
        mock_update.message.reply_text = AsyncMock()
        mock_update.effective_user = MagicMock()
        mock_update.effective_user.id = 123456

        mock_state_manager = MagicMock()
        mock_state_manager.is_paused = True
        mock_state_manager.consecutive_errors = 0

        mock_context = MagicMock()
        mock_context.bot_data = {"state_manager": mock_state_manager}

        await resume_command(mock_update, mock_context)

        mock_state_manager.resume_operations.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "0" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_resume_config_without_security_attribute(self):
        """Test resume when config exists but has no security attribute."""
        mock_update = MagicMock()
        mock_update.message = MagicMock()
        mock_update.message.reply_text = AsyncMock()
        mock_update.effective_user = MagicMock()
        mock_update.effective_user.id = 123456

        mock_state_manager = MagicMock()
        mock_state_manager.is_paused = True
        mock_state_manager.consecutive_errors = 3

        # Config that returns False for hasattr(config.security, "admin_users")
        mock_config = MagicMock()
        mock_security = MagicMock(spec=[])  # spec=[] means no attributes
        mock_config.security = mock_security

        mock_context = MagicMock()
        mock_context.bot_data = {
            "state_manager": mock_state_manager,
            "config": mock_config,
        }

        await resume_command(mock_update, mock_context)

        # hasattr(mock_security, "admin_users") returns False, so admin check is skipped
        mock_state_manager.resume_operations.assert_called_once()

    @pytest.mark.asyncio
    async def test_resume_security_without_admin_users(self):
        """Test resume when security exists but has no admin_users."""
        mock_update = MagicMock()
        mock_update.message = MagicMock()
        mock_update.message.reply_text = AsyncMock()
        mock_update.effective_user = MagicMock()
        mock_update.effective_user.id = 123456

        mock_state_manager = MagicMock()
        mock_state_manager.is_paused = True
        mock_state_manager.consecutive_errors = 3

        mock_config = MagicMock()
        mock_config.security = MagicMock(spec=[])  # No admin_users

        mock_context = MagicMock()
        mock_context.bot_data = {
            "state_manager": mock_state_manager,
            "config": mock_config,
        }

        await resume_command(mock_update, mock_context)

        # Should still work
        mock_state_manager.resume_operations.assert_called_once()
