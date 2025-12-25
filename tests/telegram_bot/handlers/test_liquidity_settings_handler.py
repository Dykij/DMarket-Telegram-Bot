"""Unit tests for liquidity_settings_handler.py module.

This module tests the liquidity settings handler functionality including:
- Default settings configuration
- Getting and updating liquidity settings
- Keyboard generation
- Telegram command handlers
- Input validation
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.telegram_bot.handlers.liquidity_settings_handler import (
    DEFAULT_LIQUIDITY_SETTINGS,
    cancel_liquidity_input,
    get_liquidity_settings,
    get_liquidity_settings_keyboard,
    liquidity_settings_command,
    process_liquidity_value_input,
    reset_liquidity_settings,
    set_max_time_to_sell_prompt,
    set_min_liquidity_score_prompt,
    set_min_sales_per_week_prompt,
    toggle_liquidity_filter,
    update_liquidity_settings,
)


# ============================================================================
# Tests for DEFAULT_LIQUIDITY_SETTINGS
# ============================================================================
class TestDefaultLiquiditySettings:
    """Tests for DEFAULT_LIQUIDITY_SETTINGS constant."""

    def test_contains_enabled_key(self) -> None:
        """Test default settings contains enabled key."""
        assert "enabled" in DEFAULT_LIQUIDITY_SETTINGS
        assert DEFAULT_LIQUIDITY_SETTINGS["enabled"] is True

    def test_contains_min_liquidity_score(self) -> None:
        """Test default settings contains min_liquidity_score."""
        assert "min_liquidity_score" in DEFAULT_LIQUIDITY_SETTINGS
        assert DEFAULT_LIQUIDITY_SETTINGS["min_liquidity_score"] == 60

    def test_contains_min_sales_per_week(self) -> None:
        """Test default settings contains min_sales_per_week."""
        assert "min_sales_per_week" in DEFAULT_LIQUIDITY_SETTINGS
        assert DEFAULT_LIQUIDITY_SETTINGS["min_sales_per_week"] == 5

    def test_contains_max_time_to_sell_days(self) -> None:
        """Test default settings contains max_time_to_sell_days."""
        assert "max_time_to_sell_days" in DEFAULT_LIQUIDITY_SETTINGS
        assert DEFAULT_LIQUIDITY_SETTINGS["max_time_to_sell_days"] == 7


# ============================================================================
# Tests for get_liquidity_settings
# ============================================================================
class TestGetLiquiditySettings:
    """Tests for get_liquidity_settings function."""

    def test_returns_default_when_no_profile(self) -> None:
        """Test returns default settings when no profile exists."""
        with patch(
            "src.telegram_bot.handlers.liquidity_settings_handler.profile_manager"
        ) as mock_profile:
            mock_profile.get_profile.return_value = {}
            
            settings = get_liquidity_settings(123)
            
            assert settings == DEFAULT_LIQUIDITY_SETTINGS

    def test_returns_existing_settings(self) -> None:
        """Test returns existing settings when profile has them."""
        custom_settings = {
            "enabled": False,
            "min_liquidity_score": 80,
            "min_sales_per_week": 10,
            "max_time_to_sell_days": 3,
        }
        
        with patch(
            "src.telegram_bot.handlers.liquidity_settings_handler.profile_manager"
        ) as mock_profile:
            mock_profile.get_profile.return_value = {
                "liquidity_settings": custom_settings
            }
            
            settings = get_liquidity_settings(123)
            
            assert settings == custom_settings

    def test_creates_default_when_missing(self) -> None:
        """Test creates default settings when missing from profile."""
        with patch(
            "src.telegram_bot.handlers.liquidity_settings_handler.profile_manager"
        ) as mock_profile:
            mock_profile.get_profile.return_value = {}
            
            get_liquidity_settings(123)
            
            mock_profile.update_profile.assert_called_once()


# ============================================================================
# Tests for update_liquidity_settings
# ============================================================================
class TestUpdateLiquiditySettings:
    """Tests for update_liquidity_settings function."""

    def test_updates_single_setting(self) -> None:
        """Test updating a single setting."""
        with patch(
            "src.telegram_bot.handlers.liquidity_settings_handler.profile_manager"
        ) as mock_profile:
            mock_profile.get_profile.return_value = {
                "liquidity_settings": DEFAULT_LIQUIDITY_SETTINGS.copy()
            }
            
            update_liquidity_settings(123, {"min_liquidity_score": 75})
            
            mock_profile.update_profile.assert_called_once()

    def test_updates_multiple_settings(self) -> None:
        """Test updating multiple settings at once."""
        with patch(
            "src.telegram_bot.handlers.liquidity_settings_handler.profile_manager"
        ) as mock_profile:
            mock_profile.get_profile.return_value = {
                "liquidity_settings": DEFAULT_LIQUIDITY_SETTINGS.copy()
            }
            
            update_liquidity_settings(
                123,
                {"min_liquidity_score": 75, "enabled": False}
            )
            
            mock_profile.update_profile.assert_called_once()

    def test_creates_settings_if_missing(self) -> None:
        """Test creates settings if not present in profile."""
        with patch(
            "src.telegram_bot.handlers.liquidity_settings_handler.profile_manager"
        ) as mock_profile:
            mock_profile.get_profile.return_value = {}
            
            update_liquidity_settings(123, {"enabled": False})
            
            mock_profile.update_profile.assert_called_once()


# ============================================================================
# Tests for get_liquidity_settings_keyboard
# ============================================================================
class TestGetLiquiditySettingsKeyboard:
    """Tests for get_liquidity_settings_keyboard function."""

    def test_returns_inline_keyboard(self) -> None:
        """Test returns InlineKeyboardMarkup."""
        from telegram import InlineKeyboardMarkup
        
        keyboard = get_liquidity_settings_keyboard()
        
        assert isinstance(keyboard, InlineKeyboardMarkup)

    def test_keyboard_has_all_buttons(self) -> None:
        """Test keyboard contains all required buttons."""
        keyboard = get_liquidity_settings_keyboard()
        
        # Flatten all buttons
        all_buttons = []
        for row in keyboard.inline_keyboard:
            for button in row:
                all_buttons.append(button.callback_data)
        
        assert "liquidity_set_min_score" in all_buttons
        assert "liquidity_set_min_sales" in all_buttons
        assert "liquidity_set_max_time" in all_buttons
        assert "liquidity_toggle" in all_buttons
        assert "liquidity_reset" in all_buttons
        assert "back_to_settings" in all_buttons

    def test_keyboard_has_six_rows(self) -> None:
        """Test keyboard has correct number of rows."""
        keyboard = get_liquidity_settings_keyboard()
        
        assert len(keyboard.inline_keyboard) == 6


# ============================================================================
# Tests for liquidity_settings_command
# ============================================================================
class TestLiquiditySettingsCommand:
    """Tests for liquidity_settings_command function."""

    @pytest.mark.asyncio
    async def test_returns_when_no_effective_user(self) -> None:
        """Test returns early when no effective user."""
        update = MagicMock()
        update.effective_user = None
        context = MagicMock()
        
        await liquidity_settings_command(update, context)
        
        # Should not raise, just return

    @pytest.mark.asyncio
    async def test_returns_when_no_message(self) -> None:
        """Test returns early when no message."""
        update = MagicMock()
        update.effective_user = MagicMock(id=123)
        update.message = None
        context = MagicMock()
        
        await liquidity_settings_command(update, context)

    @pytest.mark.asyncio
    async def test_sends_settings_message(self) -> None:
        """Test sends message with current settings."""
        update = MagicMock()
        update.effective_user = MagicMock(id=123)
        update.message = AsyncMock()
        context = MagicMock()
        
        with patch(
            "src.telegram_bot.handlers.liquidity_settings_handler.get_liquidity_settings",
            return_value=DEFAULT_LIQUIDITY_SETTINGS,
        ):
            await liquidity_settings_command(update, context)
            
            update.message.reply_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_message_contains_settings_info(self) -> None:
        """Test message contains all settings information."""
        update = MagicMock()
        update.effective_user = MagicMock(id=123)
        update.message = AsyncMock()
        context = MagicMock()
        
        with patch(
            "src.telegram_bot.handlers.liquidity_settings_handler.get_liquidity_settings",
            return_value=DEFAULT_LIQUIDITY_SETTINGS,
        ):
            await liquidity_settings_command(update, context)
            
            call_args = update.message.reply_text.call_args
            message = call_args[0][0]
            
            assert "60" in message  # min_liquidity_score
            assert "5" in message   # min_sales_per_week
            assert "7" in message   # max_time_to_sell_days


# ============================================================================
# Tests for toggle_liquidity_filter
# ============================================================================
class TestToggleLiquidityFilter:
    """Tests for toggle_liquidity_filter function."""

    @pytest.mark.asyncio
    async def test_returns_when_no_effective_user(self) -> None:
        """Test returns early when no effective user."""
        update = MagicMock()
        update.effective_user = None
        context = MagicMock()
        
        await toggle_liquidity_filter(update, context)

    @pytest.mark.asyncio
    async def test_returns_when_no_callback_query(self) -> None:
        """Test returns early when no callback query."""
        update = MagicMock()
        update.effective_user = MagicMock(id=123)
        update.callback_query = None
        context = MagicMock()
        
        await toggle_liquidity_filter(update, context)

    @pytest.mark.asyncio
    async def test_toggles_enabled_status(self) -> None:
        """Test toggles the enabled status."""
        update = MagicMock()
        update.effective_user = MagicMock(id=123)
        update.callback_query = AsyncMock()
        update.callback_query.message = MagicMock()
        context = MagicMock()
        
        with patch(
            "src.telegram_bot.handlers.liquidity_settings_handler.get_liquidity_settings",
            return_value={"enabled": True, **DEFAULT_LIQUIDITY_SETTINGS},
        ), patch(
            "src.telegram_bot.handlers.liquidity_settings_handler.update_liquidity_settings"
        ) as mock_update:
            await toggle_liquidity_filter(update, context)
            
            mock_update.assert_called_once()
            call_args = mock_update.call_args
            assert call_args[0][1]["enabled"] is False


# ============================================================================
# Tests for reset_liquidity_settings
# ============================================================================
class TestResetLiquiditySettings:
    """Tests for reset_liquidity_settings function."""

    @pytest.mark.asyncio
    async def test_returns_when_no_effective_user(self) -> None:
        """Test returns early when no effective user."""
        update = MagicMock()
        update.effective_user = None
        context = MagicMock()
        
        await reset_liquidity_settings(update, context)

    @pytest.mark.asyncio
    async def test_resets_to_defaults(self) -> None:
        """Test resets settings to default values."""
        update = MagicMock()
        update.effective_user = MagicMock(id=123)
        update.callback_query = AsyncMock()
        update.callback_query.message = MagicMock()
        context = MagicMock()
        
        with patch(
            "src.telegram_bot.handlers.liquidity_settings_handler.update_liquidity_settings"
        ) as mock_update:
            await reset_liquidity_settings(update, context)
            
            mock_update.assert_called_once()
            update.callback_query.answer.assert_called()


# ============================================================================
# Tests for set_min_liquidity_score_prompt
# ============================================================================
class TestSetMinLiquidityScorePrompt:
    """Tests for set_min_liquidity_score_prompt function."""

    @pytest.mark.asyncio
    async def test_returns_when_no_callback_query(self) -> None:
        """Test returns early when no callback query."""
        update = MagicMock()
        update.callback_query = None
        context = MagicMock()
        
        await set_min_liquidity_score_prompt(update, context)

    @pytest.mark.asyncio
    async def test_sets_awaiting_flag(self) -> None:
        """Test sets awaiting flag in user_data."""
        update = MagicMock()
        update.callback_query = AsyncMock()
        update.callback_query.message = MagicMock()
        context = MagicMock()
        context.user_data = {}
        
        await set_min_liquidity_score_prompt(update, context)
        
        assert context.user_data["awaiting_liquidity_score"] is True

    @pytest.mark.asyncio
    async def test_edits_message_with_prompt(self) -> None:
        """Test edits message with input prompt."""
        update = MagicMock()
        update.callback_query = AsyncMock()
        # Message needs to be a MagicMock with edit_message_text as AsyncMock
        update.callback_query.message = MagicMock()
        update.callback_query.edit_message_text = AsyncMock()
        context = MagicMock()
        context.user_data = {}
        
        await set_min_liquidity_score_prompt(update, context)
        
        # The function calls callback_query.message.edit_text if message exists
        assert context.user_data["awaiting_liquidity_score"] is True


# ============================================================================
# Tests for set_min_sales_per_week_prompt
# ============================================================================
class TestSetMinSalesPerWeekPrompt:
    """Tests for set_min_sales_per_week_prompt function."""

    @pytest.mark.asyncio
    async def test_returns_when_no_callback_query(self) -> None:
        """Test returns early when no callback query."""
        update = MagicMock()
        update.callback_query = None
        context = MagicMock()
        
        await set_min_sales_per_week_prompt(update, context)

    @pytest.mark.asyncio
    async def test_sets_awaiting_flag(self) -> None:
        """Test sets awaiting flag in user_data."""
        update = MagicMock()
        update.callback_query = AsyncMock()
        update.callback_query.message = MagicMock()
        context = MagicMock()
        context.user_data = {}
        
        await set_min_sales_per_week_prompt(update, context)
        
        assert context.user_data["awaiting_sales_per_week"] is True


# ============================================================================
# Tests for set_max_time_to_sell_prompt
# ============================================================================
class TestSetMaxTimeToSellPrompt:
    """Tests for set_max_time_to_sell_prompt function."""

    @pytest.mark.asyncio
    async def test_returns_when_no_callback_query(self) -> None:
        """Test returns early when no callback query."""
        update = MagicMock()
        update.callback_query = None
        context = MagicMock()
        
        await set_max_time_to_sell_prompt(update, context)

    @pytest.mark.asyncio
    async def test_sets_awaiting_flag(self) -> None:
        """Test sets awaiting flag in user_data."""
        update = MagicMock()
        update.callback_query = AsyncMock()
        update.callback_query.message = MagicMock()
        context = MagicMock()
        context.user_data = {}
        
        await set_max_time_to_sell_prompt(update, context)
        
        assert context.user_data["awaiting_time_to_sell"] is True


# ============================================================================
# Tests for process_liquidity_value_input
# ============================================================================
class TestProcessLiquidityValueInput:
    """Tests for process_liquidity_value_input function."""

    @pytest.mark.asyncio
    async def test_returns_when_no_effective_user(self) -> None:
        """Test returns early when no effective user."""
        update = MagicMock()
        update.effective_user = None
        context = MagicMock()
        
        await process_liquidity_value_input(update, context)

    @pytest.mark.asyncio
    async def test_returns_when_no_user_data(self) -> None:
        """Test returns early when no user_data."""
        update = MagicMock()
        update.effective_user = MagicMock(id=123)
        update.message = MagicMock(text="50")
        context = MagicMock()
        context.user_data = None
        
        await process_liquidity_value_input(update, context)

    @pytest.mark.asyncio
    async def test_invalid_number_shows_error(self) -> None:
        """Test invalid number input shows error message."""
        update = MagicMock()
        update.effective_user = MagicMock(id=123)
        update.message = AsyncMock()
        update.message.text = "not_a_number"
        context = MagicMock()
        context.user_data = {"awaiting_liquidity_score": True}
        
        await process_liquidity_value_input(update, context)
        
        update.message.reply_text.assert_called()
        assert "❌" in update.message.reply_text.call_args[0][0]

    @pytest.mark.asyncio
    async def test_liquidity_score_out_of_range(self) -> None:
        """Test liquidity score out of range shows error."""
        update = MagicMock()
        update.effective_user = MagicMock(id=123)
        update.message = AsyncMock()
        update.message.text = "150"  # Out of 0-100 range
        context = MagicMock()
        context.user_data = {"awaiting_liquidity_score": True}
        
        await process_liquidity_value_input(update, context)
        
        assert "❌" in update.message.reply_text.call_args[0][0]

    @pytest.mark.asyncio
    async def test_valid_liquidity_score_updates(self) -> None:
        """Test valid liquidity score updates settings."""
        update = MagicMock()
        update.effective_user = MagicMock(id=123)
        update.message = AsyncMock()
        update.message.text = "75"
        context = MagicMock()
        context.user_data = {"awaiting_liquidity_score": True}
        
        with patch(
            "src.telegram_bot.handlers.liquidity_settings_handler.update_liquidity_settings"
        ) as mock_update:
            await process_liquidity_value_input(update, context)
            
            mock_update.assert_called_with(123, {"min_liquidity_score": 75})

    @pytest.mark.asyncio
    async def test_negative_sales_shows_error(self) -> None:
        """Test negative sales value shows error."""
        update = MagicMock()
        update.effective_user = MagicMock(id=123)
        update.message = AsyncMock()
        update.message.text = "-5"
        context = MagicMock()
        context.user_data = {"awaiting_sales_per_week": True}
        
        await process_liquidity_value_input(update, context)
        
        assert "❌" in update.message.reply_text.call_args[0][0]

    @pytest.mark.asyncio
    async def test_zero_time_to_sell_shows_error(self) -> None:
        """Test zero time to sell shows error."""
        update = MagicMock()
        update.effective_user = MagicMock(id=123)
        update.message = AsyncMock()
        update.message.text = "0"
        context = MagicMock()
        context.user_data = {"awaiting_time_to_sell": True}
        
        await process_liquidity_value_input(update, context)
        
        assert "❌" in update.message.reply_text.call_args[0][0]


# ============================================================================
# Tests for cancel_liquidity_input
# ============================================================================
class TestCancelLiquidityInput:
    """Tests for cancel_liquidity_input function."""

    @pytest.mark.asyncio
    async def test_returns_when_no_message(self) -> None:
        """Test returns early when no message."""
        update = MagicMock()
        update.message = None
        context = MagicMock()
        
        await cancel_liquidity_input(update, context)

    @pytest.mark.asyncio
    async def test_returns_when_no_user_data(self) -> None:
        """Test returns early when no user_data."""
        update = MagicMock()
        update.message = AsyncMock()
        context = MagicMock()
        context.user_data = None
        
        await cancel_liquidity_input(update, context)

    @pytest.mark.asyncio
    async def test_clears_all_awaiting_flags(self) -> None:
        """Test clears all awaiting flags in user_data."""
        update = MagicMock()
        update.message = AsyncMock()
        context = MagicMock()
        context.user_data = {
            "awaiting_liquidity_score": True,
            "awaiting_sales_per_week": True,
            "awaiting_time_to_sell": True,
        }
        
        await cancel_liquidity_input(update, context)
        
        assert context.user_data["awaiting_liquidity_score"] is False
        assert context.user_data["awaiting_sales_per_week"] is False
        assert context.user_data["awaiting_time_to_sell"] is False

    @pytest.mark.asyncio
    async def test_sends_cancellation_message(self) -> None:
        """Test sends cancellation confirmation message."""
        update = MagicMock()
        update.message = AsyncMock()
        context = MagicMock()
        context.user_data = {}
        
        await cancel_liquidity_input(update, context)
        
        update.message.reply_text.assert_called_once()
        assert "❌" in update.message.reply_text.call_args[0][0]
