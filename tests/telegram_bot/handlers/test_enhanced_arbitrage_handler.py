"""Tests for enhanced_arbitrage_handler.py module.

This module tests the enhanced arbitrage scanning functionality with comprehensive
market analysis, game selection, risk modes, and pagination.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram import CallbackQuery, InlineKeyboardMarkup, Message, Update, User
from telegram.ext import CallbackContext

from src.telegram_bot.handlers.enhanced_arbitrage_handler import (
    active_scans,
    handle_enhanced_arbitrage_callback,
    handle_enhanced_arbitrage_command,
    register_enhanced_arbitrage_handlers,
    update_enhanced_arbitrage_keyboard,
)


class TestHandleEnhancedArbitrageCommand:
    """Tests for handle_enhanced_arbitrage_command function."""

    @pytest.mark.asyncio()
    async def test_command_creates_initial_keyboard(self):
        """Test that command creates initial keyboard with game and mode selection."""
        # Arrange
        update = MagicMock(spec=Update)
        update.effective_user.id = 123456
        update.message = AsyncMock(spec=Message)
        update.message.reply_text = AsyncMock()

        context = MagicMock(spec=CallbackContext)
        context.user_data = {}

        # Act
        await handle_enhanced_arbitrage_command(update, context)

        # Assert
        update.message.reply_text.assert_called_once()
        call_kwargs = update.message.reply_text.call_args[1]

        # Check message text
        assert "Enhanced Auto-Arbitrage" in call_kwargs["text"]
        assert "Select the games" in call_kwargs["text"]

        # Check keyboard structure
        assert "reply_markup" in call_kwargs
        assert isinstance(call_kwargs["reply_markup"], InlineKeyboardMarkup)

        # Check parse mode
        assert call_kwargs["parse_mode"] == "Markdown"

        # Check context initialization
        assert "enhanced_arbitrage" in context.user_data
        assert context.user_data["enhanced_arbitrage"]["games"] == ["csgo"]
        assert context.user_data["enhanced_arbitrage"]["mode"] == "medium"
        assert context.user_data["enhanced_arbitrage"]["status"] == "configuring"

    @pytest.mark.asyncio()
    async def test_command_prevents_duplicate_scans(self):
        """Test that command prevents duplicate scans for same user."""
        # Arrange
        user_id = 123456
        active_scans[user_id] = True  # Mark as already scanning

        update = MagicMock(spec=Update)
        update.effective_user.id = user_id
        update.message = AsyncMock(spec=Message)
        update.message.reply_text = AsyncMock()

        context = MagicMock(spec=CallbackContext)
        context.user_data = {}

        try:
            # Act
            await handle_enhanced_arbitrage_command(update, context)

            # Assert
            update.message.reply_text.assert_called_once()
            call_text = update.message.reply_text.call_args[0][0]
            assert "already running" in call_text.lower()
        finally:
            # Cleanup
            active_scans.pop(user_id, None)

    @pytest.mark.asyncio()
    async def test_command_initializes_user_data(self):
        """Test that command properly initializes user_data structure."""
        # Arrange
        update = MagicMock(spec=Update)
        update.effective_user.id = 123456
        update.message = AsyncMock(spec=Message)
        update.message.reply_text = AsyncMock()

        context = MagicMock(spec=CallbackContext)
        context.user_data = {}

        # Act
        await handle_enhanced_arbitrage_command(update, context)

        # Assert
        assert "enhanced_arbitrage" in context.user_data
        enhanced_data = context.user_data["enhanced_arbitrage"]

        assert "games" in enhanced_data
        assert "mode" in enhanced_data
        assert "status" in enhanced_data
        assert isinstance(enhanced_data["games"], list)
        assert len(enhanced_data["games"]) > 0

    @pytest.mark.asyncio()
    async def test_command_keyboard_contains_all_games(self):
        """Test that keyboard contains buttons for all supported games."""
        # Arrange
        update = MagicMock(spec=Update)
        update.effective_user.id = 123456
        update.message = AsyncMock(spec=Message)
        update.message.reply_text = AsyncMock()

        context = MagicMock(spec=CallbackContext)
        context.user_data = {}

        # Act
        await handle_enhanced_arbitrage_command(update, context)

        # Assert
        call_kwargs = update.message.reply_text.call_args[1]
        keyboard = call_kwargs["reply_markup"]

        # Get all callback_data from keyboard
        all_callbacks = []
        for row in keyboard.inline_keyboard:
            for button in row:
                all_callbacks.append(button.callback_data)

        # Check for game scan callbacks
        assert any("enhanced_scan:" in cb for cb in all_callbacks)

        # Check for mode selection callbacks
        assert "enhanced_mode:low" in all_callbacks
        assert "enhanced_mode:medium" in all_callbacks
        assert "enhanced_mode:high" in all_callbacks

        # Check for start scan button
        assert "enhanced_start" in all_callbacks


class TestHandleEnhancedArbitrageCallback:
    """Tests for handle_enhanced_arbitrage_callback function."""

    @pytest.mark.asyncio()
    async def test_callback_game_selection_toggle(self):
        """Test that game selection can be toggled on/off."""
        # Arrange
        user_id = 123456
        update = MagicMock(spec=Update)
        update.callback_query = AsyncMock(spec=CallbackQuery)
        update.callback_query.from_user = MagicMock(spec=User)
        update.callback_query.from_user.id = user_id
        update.callback_query.data = "enhanced_scan:dota2"
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()

        context = MagicMock(spec=CallbackContext)
        context.user_data = {
            "enhanced_arbitrage": {"games": ["csgo"], "mode": "medium", "status": "configuring"}
        }

        # Act - Add dota2
        with patch(
            "src.telegram_bot.handlers.enhanced_arbitrage_handler.update_enhanced_arbitrage_keyboard",
            new=AsyncMock(),
        ):
            await handle_enhanced_arbitrage_callback(update, context)

        # Assert - dota2 added
        assert "dota2" in context.user_data["enhanced_arbitrage"]["games"]
        assert "csgo" in context.user_data["enhanced_arbitrage"]["games"]

        # Act - Remove dota2
        update.callback_query.data = "enhanced_scan:dota2"
        with patch(
            "src.telegram_bot.handlers.enhanced_arbitrage_handler.update_enhanced_arbitrage_keyboard",
            new=AsyncMock(),
        ):
            await handle_enhanced_arbitrage_callback(update, context)

        # Assert - dota2 removed
        assert "dota2" not in context.user_data["enhanced_arbitrage"]["games"]

    @pytest.mark.asyncio()
    async def test_callback_mode_selection(self):
        """Test that risk mode can be selected."""
        # Arrange
        user_id = 123456
        update = MagicMock(spec=Update)
        update.callback_query = AsyncMock(spec=CallbackQuery)
        update.callback_query.from_user = MagicMock(spec=User)
        update.callback_query.from_user.id = user_id
        update.callback_query.data = "enhanced_mode:high"
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()

        context = MagicMock(spec=CallbackContext)
        context.user_data = {
            "enhanced_arbitrage": {"games": ["csgo"], "mode": "medium", "status": "configuring"}
        }

        # Act
        with patch(
            "src.telegram_bot.handlers.enhanced_arbitrage_handler.update_enhanced_arbitrage_keyboard",
            new=AsyncMock(),
        ):
            await handle_enhanced_arbitrage_callback(update, context)

        # Assert
        assert context.user_data["enhanced_arbitrage"]["mode"] == "high"

    @pytest.mark.asyncio()
    async def test_callback_start_scan_success(self):
        """Test successful scan start with results."""
        # Arrange
        user_id = 123456
        update = MagicMock(spec=Update)
        update.callback_query = AsyncMock(spec=CallbackQuery)
        update.callback_query.from_user = MagicMock(spec=User)
        update.callback_query.from_user.id = user_id
        update.callback_query.data = "enhanced_start"
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()

        context = MagicMock(spec=CallbackContext)
        context.user_data = {
            "enhanced_arbitrage": {"games": ["csgo"], "mode": "medium", "status": "configuring"}
        }

        # Mock scan results
        mock_results = [
            {
                "item_name": "Test Item 1",
                "buy_price": 10.0,
                "sell_price": 12.0,
                "profit": 2.0,
                "profit_percent": 20.0,
            },
            {
                "item_name": "Test Item 2",
                "buy_price": 5.0,
                "sell_price": 6.0,
                "profit": 1.0,
                "profit_percent": 20.0,
            },
        ]

        try:
            # Act
            with patch(
                "src.telegram_bot.handlers.enhanced_arbitrage_handler.start_auto_arbitrage_enhanced",
                new=AsyncMock(return_value=mock_results),
            ):
                with patch(
                    "src.telegram_bot.handlers.enhanced_arbitrage_handler.pagination_manager"
                ) as mock_pagination:
                    mock_pagination.add_items_for_user = MagicMock()
                    mock_pagination.get_page = MagicMock(return_value=(mock_results, 1, 1))
                    mock_pagination.get_items_per_page = MagicMock(return_value=10)

                    with patch(
                        "src.telegram_bot.handlers.enhanced_arbitrage_handler.format_opportunities",
                        return_value="Formatted results",
                    ):
                        with patch(
                            "src.telegram_bot.handlers.enhanced_arbitrage_handler.create_pagination_keyboard",
                            return_value=InlineKeyboardMarkup([]),
                        ):
                            await handle_enhanced_arbitrage_callback(update, context)

            # Assert
            assert context.user_data["enhanced_arbitrage"]["status"] == "completed"
            assert (
                update.callback_query.edit_message_text.call_count >= 2
            )  # At least scanning + results

            # Check that results message was sent
            final_call = update.callback_query.edit_message_text.call_args
            assert "Enhanced Arbitrage Results" in final_call[1]["text"]
        finally:
            # Cleanup
            active_scans.pop(user_id, None)

    @pytest.mark.asyncio()
    async def test_callback_start_scan_no_games(self):
        """Test scan start fails when no games selected."""
        # Arrange
        user_id = 123456
        update = MagicMock(spec=Update)
        update.callback_query = AsyncMock(spec=CallbackQuery)
        update.callback_query.from_user = MagicMock(spec=User)
        update.callback_query.from_user.id = user_id
        update.callback_query.data = "enhanced_start"
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()

        context = MagicMock(spec=CallbackContext)
        context.user_data = {
            "enhanced_arbitrage": {
                "games": [],  # No games selected
                "mode": "medium",
                "status": "configuring",
            }
        }

        try:
            # Act
            await handle_enhanced_arbitrage_callback(update, context)

            # Assert
            update.callback_query.edit_message_text.assert_called_once()
            call_text = update.callback_query.edit_message_text.call_args[0][0]
            assert "at least one game" in call_text.lower()
        finally:
            # Cleanup
            active_scans.pop(user_id, None)

    @pytest.mark.asyncio()
    async def test_callback_start_scan_already_running(self):
        """Test scan start fails when scan already running."""
        # Arrange
        user_id = 123456
        active_scans[user_id] = True  # Mark as already scanning

        update = MagicMock(spec=Update)
        update.callback_query = AsyncMock(spec=CallbackQuery)
        update.callback_query.from_user = MagicMock(spec=User)
        update.callback_query.from_user.id = user_id
        update.callback_query.data = "enhanced_start"
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()

        context = MagicMock(spec=CallbackContext)
        context.user_data = {
            "enhanced_arbitrage": {"games": ["csgo"], "mode": "medium", "status": "configuring"}
        }

        try:
            # Act
            await handle_enhanced_arbitrage_callback(update, context)

            # Assert
            update.callback_query.edit_message_text.assert_called_once()
            call_text = update.callback_query.edit_message_text.call_args[0][0]
            assert "already running" in call_text.lower()
        finally:
            # Cleanup
            active_scans.pop(user_id, None)

    @pytest.mark.asyncio()
    async def test_callback_start_scan_no_results(self):
        """Test scan start with no results found."""
        # Arrange
        user_id = 123456
        update = MagicMock(spec=Update)
        update.callback_query = AsyncMock(spec=CallbackQuery)
        update.callback_query.from_user = MagicMock(spec=User)
        update.callback_query.from_user.id = user_id
        update.callback_query.data = "enhanced_start"
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()

        context = MagicMock(spec=CallbackContext)
        context.user_data = {
            "enhanced_arbitrage": {"games": ["csgo"], "mode": "medium", "status": "configuring"}
        }

        try:
            # Act
            with patch(
                "src.telegram_bot.handlers.enhanced_arbitrage_handler.start_auto_arbitrage_enhanced",
                new=AsyncMock(return_value=[]),
            ):
                await handle_enhanced_arbitrage_callback(update, context)

            # Assert
            # Should have at least 2 calls: scanning + no results
            assert update.callback_query.edit_message_text.call_count >= 2

            # Check final message
            final_call = update.callback_query.edit_message_text.call_args
            assert "No arbitrage opportunities" in final_call[0][0]
        finally:
            # Cleanup
            active_scans.pop(user_id, None)

    @pytest.mark.asyncio()
    async def test_callback_start_scan_timeout(self):
        """Test scan start with timeout error."""
        # Arrange
        user_id = 123456
        update = MagicMock(spec=Update)
        update.callback_query = AsyncMock(spec=CallbackQuery)
        update.callback_query.from_user = MagicMock(spec=User)
        update.callback_query.from_user.id = user_id
        update.callback_query.data = "enhanced_start"
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()

        context = MagicMock(spec=CallbackContext)
        context.user_data = {
            "enhanced_arbitrage": {"games": ["csgo"], "mode": "medium", "status": "configuring"}
        }

        try:
            # Act
            with patch(
                "src.telegram_bot.handlers.enhanced_arbitrage_handler.start_auto_arbitrage_enhanced",
                new=AsyncMock(side_effect=TimeoutError()),
            ):
                await handle_enhanced_arbitrage_callback(update, context)

            # Assert
            # При timeout execute_scan() возвращает [],
            # сообщение "No arbitrage opportunities found"
            assert any(
                "no arbitrage" in str(call[0][0]).lower()
                for call in update.callback_query.edit_message_text.call_args_list
            )

            # Check status is completed
            assert context.user_data["enhanced_arbitrage"]["status"] == "completed"
        finally:
            # Cleanup
            active_scans.pop(user_id, None)

    @pytest.mark.asyncio()
    async def test_callback_start_scan_error(self):
        """Test scan start with general error."""
        # Arrange
        user_id = 123456
        update = MagicMock(spec=Update)
        update.callback_query = AsyncMock(spec=CallbackQuery)
        update.callback_query.from_user = MagicMock(spec=User)
        update.callback_query.from_user.id = user_id
        update.callback_query.data = "enhanced_start"
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()

        context = MagicMock(spec=CallbackContext)
        context.user_data = {
            "enhanced_arbitrage": {"games": ["csgo"], "mode": "medium", "status": "configuring"}
        }

        try:
            # Act
            with patch(
                "src.telegram_bot.handlers.enhanced_arbitrage_handler.start_auto_arbitrage_enhanced",
                new=AsyncMock(side_effect=Exception("Test error")),
            ):
                await handle_enhanced_arbitrage_callback(update, context)

            # Assert
            # При exception execute_scan() возвращает [],
            # сообщение "No arbitrage opportunities found"
            assert any(
                "no arbitrage" in str(call[0][0]).lower()
                for call in update.callback_query.edit_message_text.call_args_list
            )

            # Check status is completed
            assert context.user_data["enhanced_arbitrage"]["status"] == "completed"
        finally:
            # Cleanup
            active_scans.pop(user_id, None)

    @pytest.mark.asyncio()
    async def test_callback_pagination_next(self):
        """Test pagination next page."""
        # Arrange
        user_id = 123456
        update = MagicMock(spec=Update)
        update.callback_query = AsyncMock(spec=CallbackQuery)
        update.callback_query.from_user = MagicMock(spec=User)
        update.callback_query.from_user.id = user_id
        update.callback_query.data = "paginate:next:enhanced"
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()

        context = MagicMock(spec=CallbackContext)
        context.user_data = {
            "enhanced_arbitrage": {"games": ["csgo"], "mode": "medium", "status": "completed"}
        }

        mock_items = [{"item_name": "Test", "profit": 1.0}]

        # Act
        with patch(
            "src.telegram_bot.handlers.enhanced_arbitrage_handler.pagination_manager"
        ) as mock_pagination:
            mock_pagination.next_page = MagicMock()
            mock_pagination.get_page = MagicMock(return_value=(mock_items, 2, 3))
            mock_pagination.get_items_per_page = MagicMock(return_value=10)

            with patch(
                "src.telegram_bot.handlers.enhanced_arbitrage_handler.format_opportunities",
                return_value="Page 2",
            ):
                with patch(
                    "src.telegram_bot.handlers.enhanced_arbitrage_handler.create_pagination_keyboard",
                    return_value=InlineKeyboardMarkup([]),
                ):
                    await handle_enhanced_arbitrage_callback(update, context)

        # Assert
        mock_pagination.next_page.assert_called_once_with(user_id)
        update.callback_query.edit_message_text.assert_called_once()

    @pytest.mark.asyncio()
    async def test_callback_pagination_prev(self):
        """Test pagination previous page."""
        # Arrange
        user_id = 123456
        update = MagicMock(spec=Update)
        update.callback_query = AsyncMock(spec=CallbackQuery)
        update.callback_query.from_user = MagicMock(spec=User)
        update.callback_query.from_user.id = user_id
        update.callback_query.data = "paginate:prev:enhanced"
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()

        context = MagicMock(spec=CallbackContext)
        context.user_data = {
            "enhanced_arbitrage": {"games": ["csgo"], "mode": "medium", "status": "completed"}
        }

        mock_items = [{"item_name": "Test", "profit": 1.0}]

        # Act
        with patch(
            "src.telegram_bot.handlers.enhanced_arbitrage_handler.pagination_manager"
        ) as mock_pagination:
            mock_pagination.prev_page = MagicMock()
            mock_pagination.get_page = MagicMock(return_value=(mock_items, 1, 3))
            mock_pagination.get_items_per_page = MagicMock(return_value=10)

            with patch(
                "src.telegram_bot.handlers.enhanced_arbitrage_handler.format_opportunities",
                return_value="Page 1",
            ):
                with patch(
                    "src.telegram_bot.handlers.enhanced_arbitrage_handler.create_pagination_keyboard",
                    return_value=InlineKeyboardMarkup([]),
                ):
                    await handle_enhanced_arbitrage_callback(update, context)

        # Assert
        mock_pagination.prev_page.assert_called_once_with(user_id)
        update.callback_query.edit_message_text.assert_called_once()

    @pytest.mark.asyncio()
    async def test_callback_initializes_user_data_if_missing(self):
        """Test that callback initializes user_data if not present."""
        # Arrange
        user_id = 123456
        update = MagicMock(spec=Update)
        update.callback_query = AsyncMock(spec=CallbackQuery)
        update.callback_query.from_user = MagicMock(spec=User)
        update.callback_query.from_user.id = user_id
        update.callback_query.data = "enhanced_mode:low"
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()

        context = MagicMock(spec=CallbackContext)
        context.user_data = {}  # No enhanced_arbitrage data

        # Act
        with patch(
            "src.telegram_bot.handlers.enhanced_arbitrage_handler.update_enhanced_arbitrage_keyboard",
            new=AsyncMock(),
        ):
            await handle_enhanced_arbitrage_callback(update, context)

        # Assert
        assert "enhanced_arbitrage" in context.user_data
        assert context.user_data["enhanced_arbitrage"]["mode"] == "low"


class TestUpdateEnhancedArbitrageKeyboard:
    """Tests for update_enhanced_arbitrage_keyboard function."""

    @pytest.mark.asyncio()
    async def test_keyboard_update_shows_selected_games(self):
        """Test that keyboard shows selected games with checkmarks."""
        # Arrange
        query = AsyncMock(spec=CallbackQuery)
        query.edit_message_text = AsyncMock()

        context = MagicMock(spec=CallbackContext)
        context.user_data = {
            "enhanced_arbitrage": {
                "games": ["csgo", "dota2"],
                "mode": "medium",
                "status": "configuring",
            }
        }

        # Act
        await update_enhanced_arbitrage_keyboard(query, context)

        # Assert
        query.edit_message_text.assert_called_once()
        call_kwargs = query.edit_message_text.call_args[1]

        # Check message shows selected games
        assert "Selected games:" in call_kwargs["text"]
        assert "CS2" in call_kwargs["text"] or "csgo" in call_kwargs["text"].lower()

        # Check keyboard markup
        assert isinstance(call_kwargs["reply_markup"], InlineKeyboardMarkup)

        # Check parse mode
        assert call_kwargs["parse_mode"] == "Markdown"

    @pytest.mark.asyncio()
    async def test_keyboard_update_shows_selected_mode(self):
        """Test that keyboard shows selected risk mode."""
        # Arrange
        query = AsyncMock(spec=CallbackQuery)
        query.edit_message_text = AsyncMock()

        context = MagicMock(spec=CallbackContext)
        context.user_data = {
            "enhanced_arbitrage": {"games": ["csgo"], "mode": "high", "status": "configuring"}
        }

        # Act
        await update_enhanced_arbitrage_keyboard(query, context)

        # Assert
        call_kwargs = query.edit_message_text.call_args[1]

        # Check message shows selected mode
        assert "Risk level: High" in call_kwargs["text"] or "high" in call_kwargs["text"].lower()

    @pytest.mark.asyncio()
    async def test_keyboard_update_handles_missing_user_data(self):
        """Test that keyboard update uses defaults when user_data missing."""
        # Arrange
        query = AsyncMock(spec=CallbackQuery)
        query.edit_message_text = AsyncMock()

        context = MagicMock(spec=CallbackContext)
        context.user_data = {}  # No enhanced_arbitrage data

        # Act
        await update_enhanced_arbitrage_keyboard(query, context)

        # Assert
        query.edit_message_text.assert_called_once()
        call_kwargs = query.edit_message_text.call_args[1]

        # Should use defaults
        assert "Selected games:" in call_kwargs["text"]
        assert "Risk level:" in call_kwargs["text"]


class TestRegisterEnhancedArbitrageHandlers:
    """Tests for register_enhanced_arbitrage_handlers function."""

    def test_register_handlers_adds_command_handler(self):
        """Test that registration adds CommandHandler for /enhanced_arbitrage."""
        # Arrange
        dispatcher = MagicMock()
        dispatcher.add_handler = MagicMock()

        # Act
        register_enhanced_arbitrage_handlers(dispatcher)

        # Assert
        assert dispatcher.add_handler.call_count == 2

        # Check first handler (CommandHandler)
        first_handler = dispatcher.add_handler.call_args_list[0][0][0]
        assert hasattr(first_handler, "commands")
        assert "enhanced_arbitrage" in first_handler.commands

    def test_register_handlers_adds_callback_handler(self):
        """Test that registration adds CallbackQueryHandler for enhanced_ pattern."""
        # Arrange
        dispatcher = MagicMock()
        dispatcher.add_handler = MagicMock()

        # Act
        register_enhanced_arbitrage_handlers(dispatcher)

        # Assert
        # Check second handler (CallbackQueryHandler)
        second_handler = dispatcher.add_handler.call_args_list[1][0][0]
        assert hasattr(second_handler, "pattern")


class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    @pytest.mark.asyncio()
    async def test_multiple_rapid_game_selections(self):
        """Test rapid game selection/deselection works correctly."""
        # Arrange
        user_id = 123456
        update = MagicMock(spec=Update)
        update.callback_query = AsyncMock(spec=CallbackQuery)
        update.callback_query.from_user = MagicMock(spec=User)
        update.callback_query.from_user.id = user_id
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()

        context = MagicMock(spec=CallbackContext)
        context.user_data = {
            "enhanced_arbitrage": {
                "games": ["csgo"],
                "mode": "medium",
                "status": "configuring",
            }
        }

        # Act - Toggle dota2 twice (add, then remove)
        update.callback_query.data = "enhanced_scan:dota2"
        with patch(
            "src.telegram_bot.handlers.enhanced_arbitrage_handler.update_enhanced_arbitrage_keyboard",
            new=AsyncMock(),
        ):
            # First toggle - add
            await handle_enhanced_arbitrage_callback(update, context)
            assert "dota2" in context.user_data["enhanced_arbitrage"]["games"]

            # Second toggle - remove
            await handle_enhanced_arbitrage_callback(update, context)
            assert "dota2" not in context.user_data["enhanced_arbitrage"]["games"]

    @pytest.mark.asyncio()
    async def test_callback_with_invalid_data_format(self):
        """Test callback with malformed callback_data doesn't crash."""
        # Arrange
        user_id = 123456
        update = MagicMock(spec=Update)
        update.callback_query = AsyncMock(spec=CallbackQuery)
        update.callback_query.from_user = MagicMock(spec=User)
        update.callback_query.from_user.id = user_id
        update.callback_query.data = "invalid_format"  # No colon separator
        update.callback_query.answer = AsyncMock()

        context = MagicMock(spec=CallbackContext)
        context.user_data = {
            "enhanced_arbitrage": {"games": ["csgo"], "mode": "medium", "status": "configuring"}
        }

        # Act & Assert - Should not crash
        try:
            await handle_enhanced_arbitrage_callback(update, context)
            # If no exception, test passes
        except Exception as e:
            pytest.fail(f"Callback crashed with invalid data: {e}")
