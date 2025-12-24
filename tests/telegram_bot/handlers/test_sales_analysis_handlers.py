"""Unit tests for src/telegram_bot/handlers/sales_analysis_handlers.py.

Tests for sales analysis handlers including:
- GAMES constant
- get_liquidity_emoji function
- handle_sales_analysis handler
- handle_arbitrage_with_sales handler
- handle_liquidity_analysis handler
- handle_sales_volume_stats handler
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestGamesConstant:
    """Tests for GAMES constant."""

    def test_games_contains_expected_keys(self):
        """Test GAMES contains expected game keys."""
        from src.telegram_bot.handlers.sales_analysis_handlers import GAMES

        expected_keys = ["csgo", "dota2", "tf2", "rust"]
        for key in expected_keys:
            assert key in GAMES

    def test_games_has_readable_names(self):
        """Test GAMES has readable game names."""
        from src.telegram_bot.handlers.sales_analysis_handlers import GAMES

        assert GAMES["csgo"] == "CS2"
        assert GAMES["dota2"] == "Dota 2"
        assert GAMES["tf2"] == "Team Fortress 2"
        assert GAMES["rust"] == "Rust"


class TestGetLiquidityEmoji:
    """Tests for get_liquidity_emoji function."""

    def test_very_high_liquidity_emoji(self):
        """Test emoji for very high liquidity (>= 80)."""
        from src.telegram_bot.handlers.sales_analysis_handlers import get_liquidity_emoji

        assert get_liquidity_emoji(80) == "💎"
        assert get_liquidity_emoji(90) == "💎"
        assert get_liquidity_emoji(100) == "💎"

    def test_high_liquidity_emoji(self):
        """Test emoji for high liquidity (60-79)."""
        from src.telegram_bot.handlers.sales_analysis_handlers import get_liquidity_emoji

        assert get_liquidity_emoji(60) == "💧"
        assert get_liquidity_emoji(70) == "💧"
        assert get_liquidity_emoji(79) == "💧"

    def test_medium_liquidity_emoji(self):
        """Test emoji for medium liquidity (40-59)."""
        from src.telegram_bot.handlers.sales_analysis_handlers import get_liquidity_emoji

        assert get_liquidity_emoji(40) == "💦"
        assert get_liquidity_emoji(50) == "💦"
        assert get_liquidity_emoji(59) == "💦"

    def test_low_liquidity_emoji(self):
        """Test emoji for low liquidity (20-39)."""
        from src.telegram_bot.handlers.sales_analysis_handlers import get_liquidity_emoji

        assert get_liquidity_emoji(20) == "🌊"
        assert get_liquidity_emoji(30) == "🌊"
        assert get_liquidity_emoji(39) == "🌊"

    def test_very_low_liquidity_emoji(self):
        """Test emoji for very low liquidity (< 20)."""
        from src.telegram_bot.handlers.sales_analysis_handlers import get_liquidity_emoji

        assert get_liquidity_emoji(0) == "❄️"
        assert get_liquidity_emoji(10) == "❄️"
        assert get_liquidity_emoji(19) == "❄️"


class TestHandleSalesAnalysis:
    """Tests for handle_sales_analysis handler."""

    @pytest.mark.asyncio
    async def test_returns_when_no_message(self):
        """Test returns early when no message."""
        from src.telegram_bot.handlers.sales_analysis_handlers import handle_sales_analysis

        update = MagicMock()
        update.message = None

        context = MagicMock()

        # Should not raise
        await handle_sales_analysis(update, context)

    @pytest.mark.asyncio
    async def test_returns_when_no_text(self):
        """Test returns early when no text."""
        from src.telegram_bot.handlers.sales_analysis_handlers import handle_sales_analysis

        update = MagicMock()
        update.message = MagicMock()
        update.message.text = None

        context = MagicMock()

        # Should not raise
        await handle_sales_analysis(update, context)

    @pytest.mark.asyncio
    async def test_shows_error_when_no_item_name(self):
        """Test shows error when no item name provided."""
        from src.telegram_bot.handlers.sales_analysis_handlers import handle_sales_analysis

        update = MagicMock()
        update.message = AsyncMock()
        update.message.text = "/sales_analysis"
        update.message.reply_text = AsyncMock()

        context = MagicMock()

        await handle_sales_analysis(update, context)

        update.message.reply_text.assert_called_once()
        call_args = update.message.reply_text.call_args
        assert "Необходимо указать название предмета" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_analyzes_item_successfully(self):
        """Test successful item analysis."""
        from src.telegram_bot.handlers.sales_analysis_handlers import handle_sales_analysis

        update = MagicMock()
        update.message = AsyncMock()
        update.message.text = "/sales_analysis AWP | Asiimov"
        reply_message = AsyncMock()
        reply_message.edit_text = AsyncMock()
        update.message.reply_text = AsyncMock(return_value=reply_message)

        context = MagicMock()

        with patch(
            "src.telegram_bot.handlers.sales_analysis_handlers.analyze_sales_history",
            new_callable=AsyncMock,
            return_value={"avg_price": 50.0, "trend": "up"},
        ):
            with patch(
                "src.telegram_bot.handlers.sales_analysis_handlers.format_sales_analysis",
                return_value="Formatted analysis",
            ):
                await handle_sales_analysis(update, context)

        reply_message.edit_text.assert_called_once()
        call_args = reply_message.edit_text.call_args
        assert call_args[1]["text"] == "Formatted analysis"

    @pytest.mark.asyncio
    async def test_handles_api_error(self):
        """Test handles API error gracefully."""
        from src.telegram_bot.handlers.sales_analysis_handlers import handle_sales_analysis
        from src.utils.exceptions import APIError

        update = MagicMock()
        update.message = AsyncMock()
        update.message.text = "/sales_analysis AWP | Asiimov"
        reply_message = AsyncMock()
        reply_message.edit_text = AsyncMock()
        update.message.reply_text = AsyncMock(return_value=reply_message)

        context = MagicMock()

        with patch(
            "src.telegram_bot.handlers.sales_analysis_handlers.analyze_sales_history",
            new_callable=AsyncMock,
            side_effect=APIError("API Error"),
        ):
            await handle_sales_analysis(update, context)

        reply_message.edit_text.assert_called_once()
        call_args = reply_message.edit_text.call_args
        assert "Ошибка" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_handles_general_exception(self):
        """Test handles general exception gracefully."""
        from src.telegram_bot.handlers.sales_analysis_handlers import handle_sales_analysis

        update = MagicMock()
        update.message = AsyncMock()
        update.message.text = "/sales_analysis AWP | Asiimov"
        reply_message = AsyncMock()
        reply_message.edit_text = AsyncMock()
        update.message.reply_text = AsyncMock(return_value=reply_message)

        context = MagicMock()

        with patch(
            "src.telegram_bot.handlers.sales_analysis_handlers.analyze_sales_history",
            new_callable=AsyncMock,
            side_effect=Exception("Unexpected error"),
        ):
            await handle_sales_analysis(update, context)

        reply_message.edit_text.assert_called_once()
        call_args = reply_message.edit_text.call_args
        assert "Произошла ошибка" in call_args[0][0]


class TestHandleArbitrageWithSales:
    """Tests for handle_arbitrage_with_sales handler."""

    @pytest.mark.asyncio
    async def test_returns_when_no_message(self):
        """Test returns early when no message."""
        from src.telegram_bot.handlers.sales_analysis_handlers import handle_arbitrage_with_sales

        update = MagicMock()
        update.message = None

        context = MagicMock()

        # Should not raise
        await handle_arbitrage_with_sales(update, context)

    @pytest.mark.asyncio
    async def test_uses_default_game(self):
        """Test uses CSGO as default game."""
        from src.telegram_bot.handlers.sales_analysis_handlers import handle_arbitrage_with_sales

        update = MagicMock()
        update.message = AsyncMock()
        reply_message = AsyncMock()
        reply_message.edit_text = AsyncMock()
        update.message.reply_text = AsyncMock(return_value=reply_message)

        context = MagicMock()
        context.user_data = {}

        with patch(
            "src.telegram_bot.handlers.sales_analysis_handlers.enhanced_arbitrage_search",
            new_callable=AsyncMock,
            return_value=[],
        ):
            with patch(
                "src.telegram_bot.handlers.sales_analysis_handlers.format_arbitrage_with_sales",
                return_value="Results",
            ) as mock_format:
                await handle_arbitrage_with_sales(update, context)

                # Should have used "csgo" as default - check positional args
                mock_format.assert_called_once()
                call_args = mock_format.call_args
                # format_arbitrage_with_sales(results_dict, game) - game is 2nd positional arg
                assert call_args[0][1] == "csgo"

    @pytest.mark.asyncio
    async def test_uses_user_selected_game(self):
        """Test uses user-selected game from context."""
        from src.telegram_bot.handlers.sales_analysis_handlers import handle_arbitrage_with_sales

        update = MagicMock()
        update.message = AsyncMock()
        reply_message = AsyncMock()
        reply_message.edit_text = AsyncMock()
        update.message.reply_text = AsyncMock(return_value=reply_message)

        context = MagicMock()
        context.user_data = {"current_game": "dota2"}

        with patch(
            "src.telegram_bot.handlers.sales_analysis_handlers.enhanced_arbitrage_search",
            new_callable=AsyncMock,
            return_value=[],
        ):
            with patch(
                "src.telegram_bot.handlers.sales_analysis_handlers.format_arbitrage_with_sales",
                return_value="Results",
            ) as mock_format:
                await handle_arbitrage_with_sales(update, context)

                # Should have used "dota2" from user_data
                mock_format.assert_called_once()

    @pytest.mark.asyncio
    async def test_handles_api_error(self):
        """Test handles API error gracefully."""
        from src.telegram_bot.handlers.sales_analysis_handlers import handle_arbitrage_with_sales
        from src.utils.exceptions import APIError

        update = MagicMock()
        update.message = AsyncMock()
        reply_message = AsyncMock()
        reply_message.edit_text = AsyncMock()
        update.message.reply_text = AsyncMock(return_value=reply_message)

        context = MagicMock()
        context.user_data = {}

        with patch(
            "src.telegram_bot.handlers.sales_analysis_handlers.enhanced_arbitrage_search",
            new_callable=AsyncMock,
            side_effect=APIError("API Error"),
        ):
            await handle_arbitrage_with_sales(update, context)

        reply_message.edit_text.assert_called_once()
        call_args = reply_message.edit_text.call_args
        assert "Ошибка" in call_args[0][0]


class TestHandleLiquidityAnalysis:
    """Tests for handle_liquidity_analysis handler."""

    @pytest.mark.asyncio
    async def test_returns_when_no_message(self):
        """Test returns early when no message."""
        from src.telegram_bot.handlers.sales_analysis_handlers import handle_liquidity_analysis

        update = MagicMock()
        update.message = None

        context = MagicMock()

        # Should not raise
        await handle_liquidity_analysis(update, context)

    @pytest.mark.asyncio
    async def test_returns_when_no_text(self):
        """Test returns early when no text."""
        from src.telegram_bot.handlers.sales_analysis_handlers import handle_liquidity_analysis

        update = MagicMock()
        update.message = MagicMock()
        update.message.text = None

        context = MagicMock()

        # Should not raise
        await handle_liquidity_analysis(update, context)

    @pytest.mark.asyncio
    async def test_shows_error_when_no_item_name(self):
        """Test shows error when no item name provided."""
        from src.telegram_bot.handlers.sales_analysis_handlers import handle_liquidity_analysis

        update = MagicMock()
        update.message = AsyncMock()
        update.message.text = "/liquidity"
        update.message.reply_text = AsyncMock()

        context = MagicMock()

        await handle_liquidity_analysis(update, context)

        update.message.reply_text.assert_called_once()
        call_args = update.message.reply_text.call_args
        assert "Необходимо указать название предмета" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_analyzes_liquidity_successfully(self):
        """Test successful liquidity analysis."""
        from src.telegram_bot.handlers.sales_analysis_handlers import handle_liquidity_analysis

        update = MagicMock()
        update.message = AsyncMock()
        update.message.text = "/liquidity AWP | Asiimov"
        reply_message = AsyncMock()
        reply_message.edit_text = AsyncMock()
        update.message.reply_text = AsyncMock(return_value=reply_message)

        context = MagicMock()

        with patch(
            "src.telegram_bot.handlers.sales_analysis_handlers.analyze_item_liquidity",
            new_callable=AsyncMock,
            return_value={"liquidity_score": 75, "avg_time_to_sell": 2.5},
        ):
            with patch(
                "src.telegram_bot.handlers.sales_analysis_handlers.format_liquidity_analysis",
                return_value="Formatted liquidity",
            ):
                await handle_liquidity_analysis(update, context)

        reply_message.edit_text.assert_called_once()
        call_args = reply_message.edit_text.call_args
        assert call_args[1]["text"] == "Formatted liquidity"

    @pytest.mark.asyncio
    async def test_handles_api_error(self):
        """Test handles API error gracefully."""
        from src.telegram_bot.handlers.sales_analysis_handlers import handle_liquidity_analysis
        from src.utils.exceptions import APIError

        update = MagicMock()
        update.message = AsyncMock()
        update.message.text = "/liquidity AWP | Asiimov"
        reply_message = AsyncMock()
        reply_message.edit_text = AsyncMock()
        update.message.reply_text = AsyncMock(return_value=reply_message)

        context = MagicMock()

        with patch(
            "src.telegram_bot.handlers.sales_analysis_handlers.analyze_item_liquidity",
            new_callable=AsyncMock,
            side_effect=APIError("API Error"),
        ):
            await handle_liquidity_analysis(update, context)

        reply_message.edit_text.assert_called_once()
        call_args = reply_message.edit_text.call_args
        assert "Ошибка" in call_args[0][0]


class TestHandleSalesVolumeStats:
    """Tests for handle_sales_volume_stats handler."""

    @pytest.mark.asyncio
    async def test_returns_when_no_message(self):
        """Test returns early when no message."""
        from src.telegram_bot.handlers.sales_analysis_handlers import handle_sales_volume_stats

        update = MagicMock()
        update.message = None

        context = MagicMock()

        # Should not raise
        await handle_sales_volume_stats(update, context)

    @pytest.mark.asyncio
    async def test_uses_default_game(self):
        """Test uses CSGO as default game."""
        from src.telegram_bot.handlers.sales_analysis_handlers import handle_sales_volume_stats

        update = MagicMock()
        update.message = AsyncMock()
        reply_message = AsyncMock()
        reply_message.edit_text = AsyncMock()
        update.message.reply_text = AsyncMock(return_value=reply_message)

        context = MagicMock()
        context.user_data = {}

        with patch(
            "src.telegram_bot.handlers.sales_analysis_handlers.get_sales_volume_stats",
            new_callable=AsyncMock,
            return_value={"total_volume": 1000},
        ):
            with patch(
                "src.telegram_bot.handlers.sales_analysis_handlers.format_sales_volume_stats",
                return_value="Stats",
            ) as mock_format:
                await handle_sales_volume_stats(update, context)

                mock_format.assert_called_once()

    @pytest.mark.asyncio
    async def test_uses_user_selected_game(self):
        """Test uses user-selected game from context."""
        from src.telegram_bot.handlers.sales_analysis_handlers import handle_sales_volume_stats

        update = MagicMock()
        update.message = AsyncMock()
        reply_message = AsyncMock()
        reply_message.edit_text = AsyncMock()
        update.message.reply_text = AsyncMock(return_value=reply_message)

        context = MagicMock()
        context.user_data = {"current_game": "rust"}

        with patch(
            "src.telegram_bot.handlers.sales_analysis_handlers.get_sales_volume_stats",
            new_callable=AsyncMock,
            return_value={"total_volume": 500},
        ) as mock_stats:
            with patch(
                "src.telegram_bot.handlers.sales_analysis_handlers.format_sales_volume_stats",
                return_value="Stats",
            ):
                await handle_sales_volume_stats(update, context)

                # Should have called with "rust"
                mock_stats.assert_called_once_with(game="rust")

    @pytest.mark.asyncio
    async def test_handles_api_error(self):
        """Test handles API error gracefully."""
        from src.telegram_bot.handlers.sales_analysis_handlers import handle_sales_volume_stats
        from src.utils.exceptions import APIError

        update = MagicMock()
        update.message = AsyncMock()
        reply_message = AsyncMock()
        reply_message.edit_text = AsyncMock()
        update.message.reply_text = AsyncMock(return_value=reply_message)

        context = MagicMock()
        context.user_data = {}

        with patch(
            "src.telegram_bot.handlers.sales_analysis_handlers.get_sales_volume_stats",
            new_callable=AsyncMock,
            side_effect=APIError("API Error"),
        ):
            await handle_sales_volume_stats(update, context)

        reply_message.edit_text.assert_called_once()
        call_args = reply_message.edit_text.call_args
        assert "Ошибка" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_handles_general_exception(self):
        """Test handles general exception gracefully."""
        from src.telegram_bot.handlers.sales_analysis_handlers import handle_sales_volume_stats

        update = MagicMock()
        update.message = AsyncMock()
        reply_message = AsyncMock()
        reply_message.edit_text = AsyncMock()
        update.message.reply_text = AsyncMock(return_value=reply_message)

        context = MagicMock()
        context.user_data = {}

        with patch(
            "src.telegram_bot.handlers.sales_analysis_handlers.get_sales_volume_stats",
            new_callable=AsyncMock,
            side_effect=Exception("Unexpected error"),
        ):
            await handle_sales_volume_stats(update, context)

        reply_message.edit_text.assert_called_once()
        call_args = reply_message.edit_text.call_args
        assert "Произошла ошибка" in call_args[0][0]


class TestModuleExports:
    """Tests for module exports."""

    def test_all_exports_defined(self):
        """Test __all__ exports are defined."""
        from src.telegram_bot.handlers.sales_analysis_handlers import __all__

        expected_exports = [
            "GAMES",
            "get_liquidity_emoji",
            "get_trend_emoji",
            "handle_arbitrage_with_sales",
            "handle_liquidity_analysis",
            "handle_sales_analysis",
            "handle_sales_volume_stats",
        ]

        for export in expected_exports:
            assert export in __all__

    def test_get_trend_emoji_reexported(self):
        """Test get_trend_emoji is re-exported from formatters."""
        from src.telegram_bot.handlers.sales_analysis_handlers import get_trend_emoji

        # Should be callable
        assert callable(get_trend_emoji)


class TestIntegration:
    """Integration tests for sales analysis handlers."""

    @pytest.mark.asyncio
    async def test_full_sales_analysis_flow(self):
        """Test full sales analysis flow."""
        from src.telegram_bot.handlers.sales_analysis_handlers import handle_sales_analysis

        update = MagicMock()
        update.message = AsyncMock()
        update.message.text = "/sales_analysis AK-47 | Redline (Field-Tested)"
        reply_message = AsyncMock()
        reply_message.edit_text = AsyncMock()
        update.message.reply_text = AsyncMock(return_value=reply_message)

        context = MagicMock()

        mock_analysis = {
            "item_name": "AK-47 | Redline",
            "avg_price": 25.50,
            "min_price": 20.00,
            "max_price": 35.00,
            "sales_count": 150,
            "trend": "stable",
        }

        with patch(
            "src.telegram_bot.handlers.sales_analysis_handlers.analyze_sales_history",
            new_callable=AsyncMock,
            return_value=mock_analysis,
        ):
            with patch(
                "src.telegram_bot.handlers.sales_analysis_handlers.format_sales_analysis",
                return_value="📊 Analysis Results",
            ):
                await handle_sales_analysis(update, context)

        # Verify progress message was sent
        update.message.reply_text.assert_called_once()
        assert "Анализ" in update.message.reply_text.call_args[0][0]

        # Verify final result was shown
        reply_message.edit_text.assert_called_once()
        assert reply_message.edit_text.call_args[1]["text"] == "📊 Analysis Results"
