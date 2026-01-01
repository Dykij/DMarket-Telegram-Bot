"""Extended unit tests for dmarket_status.py module.

Additional coverage for:
- Edge cases (no effective_user, no effective_chat, no message)
- Balance display edge cases (zero balance, large balance)
- Troubleshooting message generation
- Different error message formats
- HTML parse mode verification
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram import Chat, Message, Update, User
from telegram.constants import ChatAction, ParseMode
from telegram.ext import CallbackContext

from src.telegram_bot.handlers.dmarket_status import dmarket_status_impl
from src.utils.exceptions import APIError


@pytest.fixture()
def mock_user():
    """Create a mock User object."""
    user = MagicMock(spec=User)
    user.id = 123456789
    user.username = "testuser"
    user.first_name = "Test"
    return user


@pytest.fixture()
def mock_chat():
    """Create a mock Chat object."""
    chat = MagicMock(spec=Chat)
    chat.id = 123456789
    chat.type = "private"
    chat.send_action = AsyncMock()
    return chat


@pytest.fixture()
def mock_message(mock_user, mock_chat):
    """Create a mock Message object."""
    message = MagicMock(spec=Message)
    message.from_user = mock_user
    message.chat = mock_chat
    message.reply_text = AsyncMock()
    return message


@pytest.fixture()
def mock_update(mock_user, mock_chat, mock_message):
    """Create a mock Update object."""
    update = MagicMock(spec=Update)
    update.effective_user = mock_user
    update.effective_chat = mock_chat
    update.message = mock_message
    return update


@pytest.fixture()
def mock_context():
    """Create a mock CallbackContext."""
    context = MagicMock(spec=CallbackContext)
    context.user_data = {}
    context.chat_data = {}
    return context


@pytest.fixture()
def mock_status_message():
    """Create a mock status message."""
    msg = AsyncMock(spec=Message)
    msg.edit_text = AsyncMock()
    return msg


# ======================== Edge Cases Tests ========================


class TestDMarketStatusEdgeCases:
    """Edge case tests for dmarket_status_impl."""

    @pytest.mark.asyncio()
    async def test_no_effective_user(self, mock_update, mock_context):
        """Test with no effective_user."""
        mock_update.effective_user = None

        # Should return early without errors
        await dmarket_status_impl(mock_update, mock_context)

        mock_update.effective_chat.send_action.assert_not_called()

    @pytest.mark.asyncio()
    async def test_no_effective_chat(self, mock_update, mock_context):
        """Test with no effective_chat."""
        mock_update.effective_chat = None

        # Should return early without errors
        await dmarket_status_impl(mock_update, mock_context)

    @pytest.mark.asyncio()
    async def test_no_message_with_no_status_message(self, mock_update, mock_context):
        """Test with no message and no status_message provided."""
        mock_update.message = None

        with (
            patch(
                "src.telegram_bot.handlers.dmarket_status.get_user_profile"
            ) as mock_profile,
        ):
            mock_profile.return_value = {}

            # Should return early without errors
            await dmarket_status_impl(mock_update, mock_context)

    @pytest.mark.asyncio()
    async def test_with_provided_status_message(
        self, mock_update, mock_context, mock_status_message
    ):
        """Test with provided status_message skips creating new message."""
        with (
            patch(
                "src.telegram_bot.handlers.dmarket_status.get_user_profile"
            ) as mock_profile,
            patch("src.dmarket.dmarket_api.DMarketAPI") as mock_api,
            patch(
                "src.telegram_bot.handlers.dmarket_status.check_user_balance"
            ) as mock_balance,
        ):
            mock_profile.return_value = {"api_key": "key", "api_secret": "secret"}

            api_instance = MagicMock()
            api_instance._close_client = AsyncMock()
            mock_api.return_value = api_instance

            mock_balance.return_value = {
                "error": False,
                "balance": 100.0,
                "has_funds": True,
            }

            await dmarket_status_impl(
                mock_update, mock_context, status_message=mock_status_message
            )

            # Should not create a new message
            mock_update.message.reply_text.assert_not_called()
            # Should use provided status message
            mock_status_message.edit_text.assert_called_once()


# ======================== Balance Edge Cases Tests ========================


class TestDMarketStatusBalanceEdgeCases:
    """Tests for balance display edge cases."""

    @pytest.mark.asyncio()
    async def test_zero_balance(self, mock_update, mock_context):
        """Test display with zero balance."""
        with (
            patch(
                "src.telegram_bot.handlers.dmarket_status.get_user_profile"
            ) as mock_profile,
            patch(
                "src.telegram_bot.handlers.dmarket_status.get_localized_text"
            ) as mock_text,
            patch("src.dmarket.dmarket_api.DMarketAPI") as mock_api,
            patch(
                "src.telegram_bot.handlers.dmarket_status.check_user_balance"
            ) as mock_balance,
        ):
            mock_profile.return_value = {"api_key": "key", "api_secret": "secret"}
            mock_text.return_value = "Checking..."

            status_msg = AsyncMock(spec=Message)
            status_msg.edit_text = AsyncMock()
            mock_update.message.reply_text.return_value = status_msg

            api_instance = MagicMock()
            api_instance._close_client = AsyncMock()
            mock_api.return_value = api_instance

            mock_balance.return_value = {
                "error": False,
                "balance": 0.0,
                "has_funds": False,
            }

            await dmarket_status_impl(mock_update, mock_context)

            status_msg.edit_text.assert_called_once()
            call_text = status_msg.edit_text.call_args[0][0]
            # Should show warning emoji for zero balance
            assert "⚠️" in call_text or "$0.00" in call_text

    @pytest.mark.asyncio()
    async def test_large_balance(self, mock_update, mock_context):
        """Test display with large balance value."""
        with (
            patch(
                "src.telegram_bot.handlers.dmarket_status.get_user_profile"
            ) as mock_profile,
            patch(
                "src.telegram_bot.handlers.dmarket_status.get_localized_text"
            ) as mock_text,
            patch("src.dmarket.dmarket_api.DMarketAPI") as mock_api,
            patch(
                "src.telegram_bot.handlers.dmarket_status.check_user_balance"
            ) as mock_balance,
        ):
            mock_profile.return_value = {"api_key": "key", "api_secret": "secret"}
            mock_text.return_value = "Checking..."

            status_msg = AsyncMock(spec=Message)
            status_msg.edit_text = AsyncMock()
            mock_update.message.reply_text.return_value = status_msg

            api_instance = MagicMock()
            api_instance._close_client = AsyncMock()
            mock_api.return_value = api_instance

            mock_balance.return_value = {
                "error": False,
                "balance": 99999.99,
                "has_funds": True,
            }

            await dmarket_status_impl(mock_update, mock_context)

            status_msg.edit_text.assert_called_once()
            call_text = status_msg.edit_text.call_args[0][0]
            assert "$99999.99" in call_text

    @pytest.mark.asyncio()
    async def test_balance_without_keys(self, mock_update, mock_context):
        """Test balance display when keys are empty."""
        with (
            patch(
                "src.telegram_bot.handlers.dmarket_status.get_user_profile"
            ) as mock_profile,
            patch(
                "src.telegram_bot.handlers.dmarket_status.get_localized_text"
            ) as mock_text,
            patch("os.getenv") as mock_getenv,
            patch("src.dmarket.dmarket_api.DMarketAPI") as mock_api,
            patch(
                "src.telegram_bot.handlers.dmarket_status.check_user_balance"
            ) as mock_balance,
        ):
            mock_profile.return_value = {}
            mock_text.return_value = "Checking..."
            mock_getenv.return_value = ""

            status_msg = AsyncMock(spec=Message)
            status_msg.edit_text = AsyncMock()
            mock_update.message.reply_text.return_value = status_msg

            api_instance = MagicMock()
            api_instance._close_client = AsyncMock()
            mock_api.return_value = api_instance

            mock_balance.return_value = {
                "error": False,
                "balance": 0,
                "has_funds": False,
            }

            await dmarket_status_impl(mock_update, mock_context)

            call_text = status_msg.edit_text.call_args[0][0]
            assert "недоступен" in call_text.lower() or "❌" in call_text


# ======================== Error Message Tests ========================


class TestDMarketStatusErrorMessages:
    """Tests for error message handling."""

    @pytest.mark.asyncio()
    async def test_balance_error_with_unauthorized_message(
        self, mock_update, mock_context
    ):
        """Test error when balance returns unauthorized error."""
        with (
            patch(
                "src.telegram_bot.handlers.dmarket_status.get_user_profile"
            ) as mock_profile,
            patch(
                "src.telegram_bot.handlers.dmarket_status.get_localized_text"
            ) as mock_text,
            patch("src.dmarket.dmarket_api.DMarketAPI") as mock_api,
            patch(
                "src.telegram_bot.handlers.dmarket_status.check_user_balance"
            ) as mock_balance,
        ):
            mock_profile.return_value = {"api_key": "key", "api_secret": "secret"}
            mock_text.return_value = "Checking..."

            status_msg = AsyncMock(spec=Message)
            status_msg.edit_text = AsyncMock()
            mock_update.message.reply_text.return_value = status_msg

            api_instance = MagicMock()
            api_instance._close_client = AsyncMock()
            mock_api.return_value = api_instance

            mock_balance.return_value = {
                "error": True,
                "error_message": "Unauthorized access token",
            }

            await dmarket_status_impl(mock_update, mock_context)

            call_text = status_msg.edit_text.call_args[0][0]
            assert "ошибка авторизации" in call_text.lower()
            assert "❌" in call_text

    @pytest.mark.asyncio()
    async def test_balance_error_with_generic_error_message(
        self, mock_update, mock_context
    ):
        """Test error when balance returns generic error."""
        with (
            patch(
                "src.telegram_bot.handlers.dmarket_status.get_user_profile"
            ) as mock_profile,
            patch(
                "src.telegram_bot.handlers.dmarket_status.get_localized_text"
            ) as mock_text,
            patch("src.dmarket.dmarket_api.DMarketAPI") as mock_api,
            patch(
                "src.telegram_bot.handlers.dmarket_status.check_user_balance"
            ) as mock_balance,
        ):
            mock_profile.return_value = {"api_key": "key", "api_secret": "secret"}
            mock_text.return_value = "Checking..."

            status_msg = AsyncMock(spec=Message)
            status_msg.edit_text = AsyncMock()
            mock_update.message.reply_text.return_value = status_msg

            api_instance = MagicMock()
            api_instance._close_client = AsyncMock()
            mock_api.return_value = api_instance

            mock_balance.return_value = {
                "error": True,
                "error_message": "Connection timeout",
            }

            await dmarket_status_impl(mock_update, mock_context)

            call_text = status_msg.edit_text.call_args[0][0]
            assert "⚠️" in call_text
            assert "Connection timeout" in call_text

    @pytest.mark.asyncio()
    async def test_api_error_500(self, mock_update, mock_context):
        """Test handling of 500 server error."""
        with (
            patch(
                "src.telegram_bot.handlers.dmarket_status.get_user_profile"
            ) as mock_profile,
            patch(
                "src.telegram_bot.handlers.dmarket_status.get_localized_text"
            ) as mock_text,
            patch("src.dmarket.dmarket_api.DMarketAPI") as mock_api,
            patch(
                "src.telegram_bot.handlers.dmarket_status.check_user_balance"
            ) as mock_balance,
        ):
            mock_profile.return_value = {"api_key": "key", "api_secret": "secret"}
            mock_text.return_value = "Checking..."

            status_msg = AsyncMock(spec=Message)
            status_msg.edit_text = AsyncMock()
            mock_update.message.reply_text.return_value = status_msg

            api_instance = MagicMock()
            api_instance._close_client = AsyncMock()
            mock_api.return_value = api_instance

            mock_balance.side_effect = APIError(
                "Internal Server Error", status_code=500
            )

            await dmarket_status_impl(mock_update, mock_context)

            call_text = status_msg.edit_text.call_args[0][0]
            assert "⚠️" in call_text
            assert "Ошибка API" in call_text

    @pytest.mark.asyncio()
    async def test_api_error_429_rate_limit(self, mock_update, mock_context):
        """Test handling of 429 rate limit error."""
        with (
            patch(
                "src.telegram_bot.handlers.dmarket_status.get_user_profile"
            ) as mock_profile,
            patch(
                "src.telegram_bot.handlers.dmarket_status.get_localized_text"
            ) as mock_text,
            patch("src.dmarket.dmarket_api.DMarketAPI") as mock_api,
            patch(
                "src.telegram_bot.handlers.dmarket_status.check_user_balance"
            ) as mock_balance,
        ):
            mock_profile.return_value = {"api_key": "key", "api_secret": "secret"}
            mock_text.return_value = "Checking..."

            status_msg = AsyncMock(spec=Message)
            status_msg.edit_text = AsyncMock()
            mock_update.message.reply_text.return_value = status_msg

            api_instance = MagicMock()
            api_instance._close_client = AsyncMock()
            mock_api.return_value = api_instance

            mock_balance.side_effect = APIError("Too Many Requests", status_code=429)

            await dmarket_status_impl(mock_update, mock_context)

            call_text = status_msg.edit_text.call_args[0][0]
            assert "⚠️" in call_text


# ======================== Troubleshooting Message Tests ========================


class TestDMarketStatusTroubleshooting:
    """Tests for troubleshooting message generation."""

    @pytest.mark.asyncio()
    async def test_troubleshooting_shown_on_auth_error(self, mock_update, mock_context):
        """Test that troubleshooting is shown on auth error."""
        with (
            patch(
                "src.telegram_bot.handlers.dmarket_status.get_user_profile"
            ) as mock_profile,
            patch(
                "src.telegram_bot.handlers.dmarket_status.get_localized_text"
            ) as mock_text,
            patch("src.dmarket.dmarket_api.DMarketAPI") as mock_api,
            patch(
                "src.telegram_bot.handlers.dmarket_status.check_user_balance"
            ) as mock_balance,
        ):
            mock_profile.return_value = {
                "api_key": "bad_key",
                "api_secret": "bad_secret",
            }
            mock_text.return_value = "Checking..."

            status_msg = AsyncMock(spec=Message)
            status_msg.edit_text = AsyncMock()
            mock_update.message.reply_text.return_value = status_msg

            api_instance = MagicMock()
            api_instance._close_client = AsyncMock()
            mock_api.return_value = api_instance

            mock_balance.side_effect = APIError("Unauthorized", status_code=401)

            await dmarket_status_impl(mock_update, mock_context)

            call_text = status_msg.edit_text.call_args[0][0]
            assert "устранения проблемы" in call_text.lower() or "🔧" in call_text

    @pytest.mark.asyncio()
    async def test_no_troubleshooting_on_success(self, mock_update, mock_context):
        """Test that troubleshooting is not shown on success."""
        with (
            patch(
                "src.telegram_bot.handlers.dmarket_status.get_user_profile"
            ) as mock_profile,
            patch(
                "src.telegram_bot.handlers.dmarket_status.get_localized_text"
            ) as mock_text,
            patch("src.dmarket.dmarket_api.DMarketAPI") as mock_api,
            patch(
                "src.telegram_bot.handlers.dmarket_status.check_user_balance"
            ) as mock_balance,
        ):
            mock_profile.return_value = {"api_key": "key", "api_secret": "secret"}
            mock_text.return_value = "Checking..."

            status_msg = AsyncMock(spec=Message)
            status_msg.edit_text = AsyncMock()
            mock_update.message.reply_text.return_value = status_msg

            api_instance = MagicMock()
            api_instance._close_client = AsyncMock()
            mock_api.return_value = api_instance

            mock_balance.return_value = {
                "error": False,
                "balance": 100.0,
                "has_funds": True,
            }

            await dmarket_status_impl(mock_update, mock_context)

            call_text = status_msg.edit_text.call_args[0][0]
            # Troubleshooting should not appear
            assert "🔧" not in call_text


# ======================== HTML Parse Mode Tests ========================


class TestDMarketStatusParseMode:
    """Tests for HTML parse mode verification."""

    @pytest.mark.asyncio()
    async def test_html_parse_mode_used(self, mock_update, mock_context):
        """Test that HTML parse mode is used in final message."""
        with (
            patch(
                "src.telegram_bot.handlers.dmarket_status.get_user_profile"
            ) as mock_profile,
            patch(
                "src.telegram_bot.handlers.dmarket_status.get_localized_text"
            ) as mock_text,
            patch("src.dmarket.dmarket_api.DMarketAPI") as mock_api,
            patch(
                "src.telegram_bot.handlers.dmarket_status.check_user_balance"
            ) as mock_balance,
        ):
            mock_profile.return_value = {"api_key": "key", "api_secret": "secret"}
            mock_text.return_value = "Checking..."

            status_msg = AsyncMock(spec=Message)
            status_msg.edit_text = AsyncMock()
            mock_update.message.reply_text.return_value = status_msg

            api_instance = MagicMock()
            api_instance._close_client = AsyncMock()
            mock_api.return_value = api_instance

            mock_balance.return_value = {
                "error": False,
                "balance": 100.0,
                "has_funds": True,
            }

            await dmarket_status_impl(mock_update, mock_context)

            call_kwargs = status_msg.edit_text.call_args[1]
            assert call_kwargs.get("parse_mode") == ParseMode.HTML

    @pytest.mark.asyncio()
    async def test_html_tags_in_message(self, mock_update, mock_context):
        """Test that HTML tags are present in the message."""
        with (
            patch(
                "src.telegram_bot.handlers.dmarket_status.get_user_profile"
            ) as mock_profile,
            patch(
                "src.telegram_bot.handlers.dmarket_status.get_localized_text"
            ) as mock_text,
            patch("src.dmarket.dmarket_api.DMarketAPI") as mock_api,
            patch(
                "src.telegram_bot.handlers.dmarket_status.check_user_balance"
            ) as mock_balance,
        ):
            mock_profile.return_value = {"api_key": "key", "api_secret": "secret"}
            mock_text.return_value = "Checking..."

            status_msg = AsyncMock(spec=Message)
            status_msg.edit_text = AsyncMock()
            mock_update.message.reply_text.return_value = status_msg

            api_instance = MagicMock()
            api_instance._close_client = AsyncMock()
            mock_api.return_value = api_instance

            mock_balance.return_value = {
                "error": False,
                "balance": 100.0,
                "has_funds": True,
            }

            await dmarket_status_impl(mock_update, mock_context)

            call_text = status_msg.edit_text.call_args[0][0]
            # Should contain HTML bold tags
            assert "<b>" in call_text
            assert "</b>" in call_text
            # May contain code tags for balance
            assert "<code>" in call_text or "<i>" in call_text


# ======================== Chat Action Tests ========================


class TestDMarketStatusChatActions:
    """Tests for chat action indicators."""

    @pytest.mark.asyncio()
    async def test_typing_action_sent(self, mock_update, mock_context):
        """Test that TYPING action is sent initially."""
        with (
            patch(
                "src.telegram_bot.handlers.dmarket_status.get_user_profile"
            ) as mock_profile,
            patch(
                "src.telegram_bot.handlers.dmarket_status.get_localized_text"
            ) as mock_text,
            patch("src.dmarket.dmarket_api.DMarketAPI") as mock_api,
            patch(
                "src.telegram_bot.handlers.dmarket_status.check_user_balance"
            ) as mock_balance,
        ):
            mock_profile.return_value = {"api_key": "key", "api_secret": "secret"}
            mock_text.return_value = "Checking..."

            status_msg = AsyncMock(spec=Message)
            status_msg.edit_text = AsyncMock()
            mock_update.message.reply_text.return_value = status_msg

            api_instance = MagicMock()
            api_instance._close_client = AsyncMock()
            mock_api.return_value = api_instance

            mock_balance.return_value = {
                "error": False,
                "balance": 100.0,
                "has_funds": True,
            }

            await dmarket_status_impl(mock_update, mock_context)

            # Check that send_action was called with TYPING
            send_action_calls = mock_update.effective_chat.send_action.call_args_list
            actions = [call[0][0] for call in send_action_calls]
            assert ChatAction.TYPING in actions

    @pytest.mark.asyncio()
    async def test_upload_document_action_sent(self, mock_update, mock_context):
        """Test that UPLOAD_DOCUMENT action is sent."""
        with (
            patch(
                "src.telegram_bot.handlers.dmarket_status.get_user_profile"
            ) as mock_profile,
            patch(
                "src.telegram_bot.handlers.dmarket_status.get_localized_text"
            ) as mock_text,
            patch("src.dmarket.dmarket_api.DMarketAPI") as mock_api,
            patch(
                "src.telegram_bot.handlers.dmarket_status.check_user_balance"
            ) as mock_balance,
        ):
            mock_profile.return_value = {"api_key": "key", "api_secret": "secret"}
            mock_text.return_value = "Checking..."

            status_msg = AsyncMock(spec=Message)
            status_msg.edit_text = AsyncMock()
            mock_update.message.reply_text.return_value = status_msg

            api_instance = MagicMock()
            api_instance._close_client = AsyncMock()
            mock_api.return_value = api_instance

            mock_balance.return_value = {
                "error": False,
                "balance": 100.0,
                "has_funds": True,
            }

            await dmarket_status_impl(mock_update, mock_context)

            send_action_calls = mock_update.effective_chat.send_action.call_args_list
            actions = [call[0][0] for call in send_action_calls]
            assert ChatAction.UPLOAD_DOCUMENT in actions


# ======================== Auth Source Display Tests ========================


class TestDMarketStatusAuthSource:
    """Tests for auth source display in messages."""

    @pytest.mark.asyncio()
    async def test_env_source_shown_when_using_env_keys(
        self, mock_update, mock_context
    ):
        """Test that env source is indicated when using environment keys."""
        with (
            patch(
                "src.telegram_bot.handlers.dmarket_status.get_user_profile"
            ) as mock_profile,
            patch(
                "src.telegram_bot.handlers.dmarket_status.get_localized_text"
            ) as mock_text,
            patch("os.getenv") as mock_getenv,
            patch("src.dmarket.dmarket_api.DMarketAPI") as mock_api,
            patch(
                "src.telegram_bot.handlers.dmarket_status.check_user_balance"
            ) as mock_balance,
        ):
            mock_profile.return_value = {}
            mock_text.return_value = "Checking..."

            def getenv_mock(key, default=""):
                if "KEY" in key:
                    return "env_key_value"
                return default

            mock_getenv.side_effect = getenv_mock

            status_msg = AsyncMock(spec=Message)
            status_msg.edit_text = AsyncMock()
            mock_update.message.reply_text.return_value = status_msg

            api_instance = MagicMock()
            api_instance._close_client = AsyncMock()
            mock_api.return_value = api_instance

            mock_balance.return_value = {
                "error": False,
                "balance": 50.0,
                "has_funds": True,
            }

            await dmarket_status_impl(mock_update, mock_context)

            call_text = status_msg.edit_text.call_args[0][0]
            # Should show env source indication
            assert "переменных окружения" in call_text.lower()

    @pytest.mark.asyncio()
    async def test_no_env_source_when_using_profile_keys(
        self, mock_update, mock_context
    ):
        """Test that env source is NOT shown when using profile keys."""
        with (
            patch(
                "src.telegram_bot.handlers.dmarket_status.get_user_profile"
            ) as mock_profile,
            patch(
                "src.telegram_bot.handlers.dmarket_status.get_localized_text"
            ) as mock_text,
            patch("src.dmarket.dmarket_api.DMarketAPI") as mock_api,
            patch(
                "src.telegram_bot.handlers.dmarket_status.check_user_balance"
            ) as mock_balance,
        ):
            mock_profile.return_value = {
                "api_key": "profile_key",
                "api_secret": "profile_secret",
            }
            mock_text.return_value = "Checking..."

            status_msg = AsyncMock(spec=Message)
            status_msg.edit_text = AsyncMock()
            mock_update.message.reply_text.return_value = status_msg

            api_instance = MagicMock()
            api_instance._close_client = AsyncMock()
            mock_api.return_value = api_instance

            mock_balance.return_value = {
                "error": False,
                "balance": 100.0,
                "has_funds": True,
            }

            await dmarket_status_impl(mock_update, mock_context)

            call_text = status_msg.edit_text.call_args[0][0]
            # Should NOT show env source indication
            assert "переменных окружения" not in call_text.lower()
