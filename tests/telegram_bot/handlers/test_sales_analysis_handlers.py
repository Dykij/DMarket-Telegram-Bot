"""Tests for sales_analysis_handlers module.

Tests cover:
- GAMES constant
- get_liquidity_emoji function
- handle_sales_analysis command
- handle_arbitrage_with_sales command
- handle_liquidity_analysis command
- handle_sales_volume_stats command
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestGamesConstant:
    """Tests for GAMES constant."""

    def test_games_structure(self):
        """Test GAMES has expected structure."""
        from src.telegram_bot.handlers.sales_analysis_handlers import GAMES

        assert isinstance(GAMES, dict)
        assert len(GAMES) == 4

    def test_games_contains_expected_games(self):
        """Test GAMES contains all expected games."""
        from src.telegram_bot.handlers.sales_analysis_handlers import GAMES

        assert "csgo" in GAMES
        assert "dota2" in GAMES
        assert "tf2" in GAMES
        assert "rust" in GAMES

    def test_games_values(self):
        """Test GAMES has correct display names."""
        from src.telegram_bot.handlers.sales_analysis_handlers import GAMES

        assert GAMES["csgo"] == "CS2"
        assert GAMES["dota2"] == "Dota 2"
        assert GAMES["tf2"] == "Team Fortress 2"
        assert GAMES["rust"] == "Rust"


class TestGetLiquidityEmoji:
    """Tests for get_liquidity_emoji function."""

    def test_very_high_liquidity(self):
        """Test emoji for very high liquidity (>=80)."""
        from src.telegram_bot.handlers.sales_analysis_handlers import (
            get_liquidity_emoji,
        )

        assert get_liquidity_emoji(100) == "💎"
        assert get_liquidity_emoji(80) == "💎"
        assert get_liquidity_emoji(85) == "💎"

    def test_high_liquidity(self):
        """Test emoji for high liquidity (>=60, <80)."""
        from src.telegram_bot.handlers.sales_analysis_handlers import (
            get_liquidity_emoji,
        )

        assert get_liquidity_emoji(79) == "💧"
        assert get_liquidity_emoji(60) == "💧"
        assert get_liquidity_emoji(70) == "💧"

    def test_medium_liquidity(self):
        """Test emoji for medium liquidity (>=40, <60)."""
        from src.telegram_bot.handlers.sales_analysis_handlers import (
            get_liquidity_emoji,
        )

        assert get_liquidity_emoji(59) == "💦"
        assert get_liquidity_emoji(40) == "💦"
        assert get_liquidity_emoji(50) == "💦"

    def test_low_liquidity(self):
        """Test emoji for low liquidity (>=20, <40)."""
        from src.telegram_bot.handlers.sales_analysis_handlers import (
            get_liquidity_emoji,
        )

        assert get_liquidity_emoji(39) == "🌊"
        assert get_liquidity_emoji(20) == "🌊"
        assert get_liquidity_emoji(30) == "🌊"

    def test_very_low_liquidity(self):
        """Test emoji for very low liquidity (<20)."""
        from src.telegram_bot.handlers.sales_analysis_handlers import (
            get_liquidity_emoji,
        )

        assert get_liquidity_emoji(19) == "❄️"
        assert get_liquidity_emoji(0) == "❄️"
        assert get_liquidity_emoji(10) == "❄️"

    def test_edge_case_exact_thresholds(self):
        """Test edge cases at exact threshold values."""
        from src.telegram_bot.handlers.sales_analysis_handlers import (
            get_liquidity_emoji,
        )

        assert get_liquidity_emoji(80) == "💎"
        assert get_liquidity_emoji(60) == "💧"
        assert get_liquidity_emoji(40) == "💦"
        assert get_liquidity_emoji(20) == "🌊"


class TestHandleSalesAnalysis:
    """Tests for handle_sales_analysis function."""

    @pytest.mark.asyncio
    async def test_handle_no_message(self):
        """Test handle_sales_analysis with no message."""
        from src.telegram_bot.handlers.sales_analysis_handlers import (
            handle_sales_analysis,
        )

        update = MagicMock()
        update.message = None
        context = MagicMock()

        # Should return early without error
        await handle_sales_analysis(update, context)

    @pytest.mark.asyncio
    async def test_handle_no_text(self):
        """Test handle_sales_analysis with no text."""
        from src.telegram_bot.handlers.sales_analysis_handlers import (
            handle_sales_analysis,
        )

        update = MagicMock()
        update.message = MagicMock()
        update.message.text = None
        context = MagicMock()

        await handle_sales_analysis(update, context)

    @pytest.mark.asyncio
    async def test_handle_no_item_name(self):
        """Test handle_sales_analysis without item name."""
        from src.telegram_bot.handlers.sales_analysis_handlers import (
            handle_sales_analysis,
        )

        update = MagicMock()
        update.message = AsyncMock()
        update.message.text = "/sales_analysis"
        context = MagicMock()

        await handle_sales_analysis(update, context)

        update.message.reply_text.assert_called_once()
        call_args = update.message.reply_text.call_args
        text = call_args[1].get("text", call_args[0][0])
        assert "Необходимо указать название предмета" in text

    @pytest.mark.asyncio
    @patch("src.telegram_bot.handlers.sales_analysis_handlers.analyze_sales_history")
    @patch("src.telegram_bot.handlers.sales_analysis_handlers.format_sales_analysis")
    async def test_handle_successful_analysis(self, mock_format, mock_analyze):
        """Test successful sales analysis."""
        from src.telegram_bot.handlers.sales_analysis_handlers import (
            handle_sales_analysis,
        )

        mock_analyze.return_value = {"some": "analysis"}
        mock_format.return_value = "Formatted analysis"

        update = MagicMock()
        update.message = AsyncMock()
        reply_msg = AsyncMock()
        update.message.reply_text.return_value = reply_msg
        update.message.text = "/sales_analysis AWP | Asiimov"
        context = MagicMock()

        await handle_sales_analysis(update, context)

        mock_analyze.assert_called_once()
        call_args = mock_analyze.call_args
        assert call_args[1]["item_name"] == "AWP | Asiimov"

    @pytest.mark.asyncio
    @patch("src.telegram_bot.handlers.sales_analysis_handlers.analyze_sales_history")
    async def test_handle_api_error(self, mock_analyze):
        """Test handle_sales_analysis with API error."""
        from src.telegram_bot.handlers.sales_analysis_handlers import (
            handle_sales_analysis,
        )
        from src.utils.exceptions import APIError

        mock_analyze.side_effect = APIError(message="API failed")

        update = MagicMock()
        update.message = AsyncMock()
        reply_msg = AsyncMock()
        update.message.reply_text.return_value = reply_msg
        update.message.text = "/sales_analysis AWP | Asiimov"
        context = MagicMock()

        await handle_sales_analysis(update, context)

        reply_msg.edit_text.assert_called_once()
        call_args = reply_msg.edit_text.call_args
        text = call_args[1].get("text", call_args[0][0])
        assert "Ошибка" in text

    @pytest.mark.asyncio
    @patch("src.telegram_bot.handlers.sales_analysis_handlers.analyze_sales_history")
    async def test_handle_general_exception(self, mock_analyze):
        """Test handle_sales_analysis with general exception."""
        from src.telegram_bot.handlers.sales_analysis_handlers import (
            handle_sales_analysis,
        )

        mock_analyze.side_effect = ValueError("Some error")

        update = MagicMock()
        update.message = AsyncMock()
        reply_msg = AsyncMock()
        update.message.reply_text.return_value = reply_msg
        update.message.text = "/sales_analysis AWP | Asiimov"
        context = MagicMock()

        await handle_sales_analysis(update, context)

        reply_msg.edit_text.assert_called_once()


class TestHandleArbitrageWithSales:
    """Tests for handle_arbitrage_with_sales function."""

    @pytest.mark.asyncio
    async def test_handle_no_message(self):
        """Test handle_arbitrage_with_sales with no message."""
        from src.telegram_bot.handlers.sales_analysis_handlers import (
            handle_arbitrage_with_sales,
        )

        update = MagicMock()
        update.message = None
        context = MagicMock()

        # Should return early without error
        await handle_arbitrage_with_sales(update, context)

    @pytest.mark.asyncio
    @patch("src.telegram_bot.handlers.sales_analysis_handlers.enhanced_arbitrage_search")
    @patch("src.telegram_bot.handlers.sales_analysis_handlers.format_arbitrage_with_sales")
    async def test_handle_default_game(self, mock_format, mock_search):
        """Test handle_arbitrage_with_sales with default game."""
        from src.telegram_bot.handlers.sales_analysis_handlers import (
            handle_arbitrage_with_sales,
        )

        mock_search.return_value = []
        mock_format.return_value = "No results"

        update = MagicMock()
        update.message = AsyncMock()
        reply_msg = AsyncMock()
        update.message.reply_text.return_value = reply_msg
        context = MagicMock()
        context.user_data = {}

        await handle_arbitrage_with_sales(update, context)

        mock_search.assert_called_once()
        call_args = mock_search.call_args
        assert call_args[1]["game"] == "csgo"

    @pytest.mark.asyncio
    @patch("src.telegram_bot.handlers.sales_analysis_handlers.enhanced_arbitrage_search")
    @patch("src.telegram_bot.handlers.sales_analysis_handlers.format_arbitrage_with_sales")
    async def test_handle_custom_game(self, mock_format, mock_search):
        """Test handle_arbitrage_with_sales with custom game from context."""
        from src.telegram_bot.handlers.sales_analysis_handlers import (
            handle_arbitrage_with_sales,
        )

        mock_search.return_value = []
        mock_format.return_value = "No results"

        update = MagicMock()
        update.message = AsyncMock()
        reply_msg = AsyncMock()
        update.message.reply_text.return_value = reply_msg
        context = MagicMock()
        context.user_data = {"current_game": "dota2"}

        await handle_arbitrage_with_sales(update, context)

        mock_search.assert_called_once()
        call_args = mock_search.call_args
        assert call_args[1]["game"] == "dota2"

    @pytest.mark.asyncio
    @patch("src.telegram_bot.handlers.sales_analysis_handlers.enhanced_arbitrage_search")
    async def test_handle_search_api_error(self, mock_search):
        """Test handle_arbitrage_with_sales with API error."""
        from src.telegram_bot.handlers.sales_analysis_handlers import (
            handle_arbitrage_with_sales,
        )
        from src.utils.exceptions import APIError

        mock_search.side_effect = APIError(message="Search failed")

        update = MagicMock()
        update.message = AsyncMock()
        reply_msg = AsyncMock()
        update.message.reply_text.return_value = reply_msg
        context = MagicMock()
        context.user_data = {}

        await handle_arbitrage_with_sales(update, context)

        reply_msg.edit_text.assert_called_once()


class TestHandleLiquidityAnalysis:
    """Tests for handle_liquidity_analysis function."""

    @pytest.mark.asyncio
    async def test_handle_no_message(self):
        """Test handle_liquidity_analysis with no message."""
        from src.telegram_bot.handlers.sales_analysis_handlers import (
            handle_liquidity_analysis,
        )

        update = MagicMock()
        update.message = None
        context = MagicMock()

        await handle_liquidity_analysis(update, context)

    @pytest.mark.asyncio
    async def test_handle_no_item_name(self):
        """Test handle_liquidity_analysis without item name."""
        from src.telegram_bot.handlers.sales_analysis_handlers import (
            handle_liquidity_analysis,
        )

        update = MagicMock()
        update.message = AsyncMock()
        update.message.text = "/liquidity"
        context = MagicMock()

        await handle_liquidity_analysis(update, context)

        update.message.reply_text.assert_called_once()
        call_args = update.message.reply_text.call_args
        text = call_args[1].get("text", call_args[0][0])
        assert "Необходимо указать" in text

    @pytest.mark.asyncio
    @patch("src.telegram_bot.handlers.sales_analysis_handlers.analyze_item_liquidity")
    @patch("src.telegram_bot.handlers.sales_analysis_handlers.format_liquidity_analysis")
    async def test_handle_successful_analysis(self, mock_format, mock_analyze):
        """Test successful liquidity analysis."""
        from src.telegram_bot.handlers.sales_analysis_handlers import (
            handle_liquidity_analysis,
        )

        mock_analyze.return_value = {"liquidity_score": 75}
        mock_format.return_value = "Formatted liquidity"

        update = MagicMock()
        update.message = AsyncMock()
        reply_msg = AsyncMock()
        update.message.reply_text.return_value = reply_msg
        update.message.text = "/liquidity AWP | Asiimov"
        context = MagicMock()

        await handle_liquidity_analysis(update, context)

        mock_analyze.assert_called_once()
        call_args = mock_analyze.call_args
        assert call_args[1]["item_name"] == "AWP | Asiimov"


class TestHandleSalesVolumeStats:
    """Tests for handle_sales_volume_stats function."""

    @pytest.mark.asyncio
    async def test_handle_no_message(self):
        """Test handle_sales_volume_stats with no message."""
        from src.telegram_bot.handlers.sales_analysis_handlers import (
            handle_sales_volume_stats,
        )

        update = MagicMock()
        update.message = None
        context = MagicMock()

        await handle_sales_volume_stats(update, context)

    @pytest.mark.asyncio
    @patch("src.telegram_bot.handlers.sales_analysis_handlers.get_sales_volume_stats")
    @patch("src.telegram_bot.handlers.sales_analysis_handlers.format_sales_volume_stats")
    async def test_handle_default_game(self, mock_format, mock_get_stats):
        """Test handle_sales_volume_stats with default game."""
        from src.telegram_bot.handlers.sales_analysis_handlers import (
            handle_sales_volume_stats,
        )

        mock_get_stats.return_value = {"total_sales": 100}
        mock_format.return_value = "Formatted stats"

        update = MagicMock()
        update.message = AsyncMock()
        reply_msg = AsyncMock()
        update.message.reply_text.return_value = reply_msg
        context = MagicMock()
        context.user_data = {}

        await handle_sales_volume_stats(update, context)

        mock_get_stats.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.telegram_bot.handlers.sales_analysis_handlers.get_sales_volume_stats")
    async def test_handle_api_error(self, mock_get_stats):
        """Test handle_sales_volume_stats with API error."""
        from src.telegram_bot.handlers.sales_analysis_handlers import (
            handle_sales_volume_stats,
        )
        from src.utils.exceptions import APIError

        mock_get_stats.side_effect = APIError(message="Stats failed")

        update = MagicMock()
        update.message = AsyncMock()
        reply_msg = AsyncMock()
        update.message.reply_text.return_value = reply_msg
        context = MagicMock()
        context.user_data = {}

        await handle_sales_volume_stats(update, context)


class TestModuleExports:
    """Tests for module exports."""

    def test_all_exports_exist(self):
        """Test all __all__ exports exist."""
        from src.telegram_bot.handlers.sales_analysis_handlers import __all__

        assert "GAMES" in __all__
        assert "get_liquidity_emoji" in __all__
        assert "handle_sales_analysis" in __all__
        assert "handle_arbitrage_with_sales" in __all__
        assert "handle_liquidity_analysis" in __all__
        assert "handle_sales_volume_stats" in __all__

    def test_get_trend_emoji_reexported(self):
        """Test get_trend_emoji is reexported."""
        from src.telegram_bot.handlers.sales_analysis_handlers import __all__

        assert "get_trend_emoji" in __all__

    def test_imports_work(self):
        """Test all exports can be imported."""
        from src.telegram_bot.handlers.sales_analysis_handlers import (
            GAMES,
            get_liquidity_emoji,
            handle_sales_analysis,
            handle_arbitrage_with_sales,
            handle_liquidity_analysis,
            handle_sales_volume_stats,
        )

        assert GAMES is not None
        assert callable(get_liquidity_emoji)
        assert callable(handle_sales_analysis)
        assert callable(handle_arbitrage_with_sales)
        assert callable(handle_liquidity_analysis)
        assert callable(handle_sales_volume_stats)


class TestEdgeCases:
    """Tests for edge cases."""

    def test_liquidity_emoji_negative_value(self):
        """Test get_liquidity_emoji with negative value."""
        from src.telegram_bot.handlers.sales_analysis_handlers import (
            get_liquidity_emoji,
        )

        # Negative should return very low emoji
        assert get_liquidity_emoji(-10) == "❄️"

    def test_liquidity_emoji_high_value(self):
        """Test get_liquidity_emoji with value above 100."""
        from src.telegram_bot.handlers.sales_analysis_handlers import (
            get_liquidity_emoji,
        )

        # Above 100 should still return very high emoji
        assert get_liquidity_emoji(150) == "💎"

    @pytest.mark.asyncio
    async def test_handle_sales_with_special_characters(self):
        """Test handle_sales_analysis with special characters in item name."""
        from src.telegram_bot.handlers.sales_analysis_handlers import (
            handle_sales_analysis,
        )

        update = MagicMock()
        update.message = AsyncMock()
        reply_msg = AsyncMock()
        update.message.reply_text.return_value = reply_msg
        update.message.text = "/sales_analysis AWP | Asiimov <script>alert('xss')</script>"
        context = MagicMock()

        with patch("src.telegram_bot.handlers.sales_analysis_handlers.analyze_sales_history") as mock_analyze:
            mock_analyze.return_value = {}
            with patch("src.telegram_bot.handlers.sales_analysis_handlers.format_sales_analysis") as mock_format:
                mock_format.return_value = "Result"
                await handle_sales_analysis(update, context)

                # Should still process the item name
                mock_analyze.assert_called_once()
