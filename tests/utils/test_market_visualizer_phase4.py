"""
Extended unit tests for market_visualizer.py module (Phase 4).

This module provides comprehensive tests for the MarketVisualizer class
to achieve 100% coverage as part of Phase 4 testing roadmap.

Tests cover:
- Initialization and theme setup
- Price chart creation (all scenarios)
- Market comparison charts
- Pattern visualization
- Market summary images
- Data processing functions
- Trend coloring and support/resistance detection
- Edge cases and error handling
"""

from datetime import UTC, datetime, timedelta
import io
from unittest.mock import MagicMock

import pandas as pd
from PIL import Image
import pytest

from src.utils.market_visualizer import MarketVisualizer


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture()
def visualizer_dark():
    """Create a dark theme visualizer."""
    return MarketVisualizer(theme="dark")


@pytest.fixture()
def visualizer_light():
    """Create a light theme visualizer."""
    return MarketVisualizer(theme="light")


@pytest.fixture()
def basic_price_history():
    """Basic price history with minimal data."""
    now = datetime.now(UTC)
    return [
        {"price": 10.0, "timestamp": (now - timedelta(days=2)).timestamp()},
        {"price": 11.0, "timestamp": (now - timedelta(days=1)).timestamp()},
        {"price": 12.0, "timestamp": now.timestamp()},
    ]


@pytest.fixture()
def extended_price_history():
    """Extended price history for support/resistance testing."""
    now = datetime.now(UTC)
    return [
        {"price": 10.0, "timestamp": (now - timedelta(days=14)).timestamp()},
        {"price": 11.0, "timestamp": (now - timedelta(days=13)).timestamp()},
        {"price": 10.5, "timestamp": (now - timedelta(days=12)).timestamp()},
        {"price": 10.0, "timestamp": (now - timedelta(days=11)).timestamp()},
        {"price": 11.5, "timestamp": (now - timedelta(days=10)).timestamp()},
        {"price": 12.0, "timestamp": (now - timedelta(days=9)).timestamp()},
        {"price": 11.8, "timestamp": (now - timedelta(days=8)).timestamp()},
        {"price": 11.0, "timestamp": (now - timedelta(days=7)).timestamp()},
        {"price": 10.5, "timestamp": (now - timedelta(days=6)).timestamp()},
        {"price": 11.0, "timestamp": (now - timedelta(days=5)).timestamp()},
        {"price": 12.5, "timestamp": (now - timedelta(days=4)).timestamp()},
        {"price": 13.0, "timestamp": (now - timedelta(days=3)).timestamp()},
        {"price": 12.8, "timestamp": (now - timedelta(days=2)).timestamp()},
        {"price": 13.5, "timestamp": (now - timedelta(days=1)).timestamp()},
        {"price": 14.0, "timestamp": now.timestamp()},
    ]


@pytest.fixture()
def price_history_with_volume():
    """Price history with volume data."""
    now = datetime.now(UTC)
    return [
        {"price": 10.0, "timestamp": (now - timedelta(days=6)).timestamp(), "volume": 100},
        {"price": 10.5, "timestamp": (now - timedelta(days=5)).timestamp(), "volume": 120},
        {"price": 11.0, "timestamp": (now - timedelta(days=4)).timestamp(), "volume": 150},
        {"price": 10.8, "timestamp": (now - timedelta(days=3)).timestamp(), "volume": 130},
        {"price": 11.5, "timestamp": (now - timedelta(days=2)).timestamp(), "volume": 180},
        {"price": 12.0, "timestamp": (now - timedelta(days=1)).timestamp(), "volume": 200},
        {"price": 12.5, "timestamp": now.timestamp(), "volume": 220},
    ]


@pytest.fixture()
def price_history_dict_format():
    """Price history with dict format prices."""
    now = datetime.now(UTC)
    return [
        {"price": {"amount": 1000}, "timestamp": (now - timedelta(days=2)).timestamp()},
        {"price": {"amount": 1100}, "timestamp": (now - timedelta(days=1)).timestamp()},
        {"price": {"amount": 1200}, "timestamp": now.timestamp()},
    ]


@pytest.fixture()
def price_history_string_format():
    """Price history with string format prices and timestamps."""
    now = datetime.now(UTC)
    return [
        {"price": "10.0", "timestamp": now.isoformat()},
        {"price": "11.0", "timestamp": (now + timedelta(days=1)).isoformat()},
    ]


@pytest.fixture()
def mixed_patterns():
    """Various pattern types for testing."""
    return [
        {"type": "breakout", "confidence": 0.9, "direction": "upward"},
        {"type": "reversal", "confidence": 0.8, "direction": "upward"},
        {"type": "reversal", "confidence": 0.75, "direction": "downward"},
        {"type": "fomo", "confidence": 0.85},
        {"type": "panic", "confidence": 0.7},
        {"type": "consolidation", "confidence": 0.4},  # Below threshold
    ]


@pytest.fixture()
def sample_item_data():
    """Sample item data."""
    return {
        "itemId": "test_item_1",
        "title": "AK-47 | Redline",
        "price": {"amount": 1500},
        "gameId": "csgo",
    }


@pytest.fixture()
def sample_analysis():
    """Sample analysis data."""
    return {
        "trend": "up",
        "volatility": "medium",
        "price_change_24h": 5.5,
        "price_change_7d": 12.3,
        "support_level": 12.0,
        "resistance_level": 15.0,
        "patterns": [
            {"type": "breakout", "confidence": 0.85},
            {"type": "fomo", "confidence": 0.75},
            {"type": "trend_continuation", "confidence": 0.65},
        ],
    }


# ============================================================================
# Test MarketVisualizer Initialization
# ============================================================================


class TestMarketVisualizerInit:
    """Tests for MarketVisualizer initialization."""

    def test_init_default_theme(self):
        """Test default theme is dark."""
        visualizer = MarketVisualizer()
        assert visualizer.theme == "dark"

    def test_init_dark_theme(self):
        """Test dark theme initialization."""
        visualizer = MarketVisualizer(theme="dark")
        assert visualizer.theme == "dark"
        assert visualizer.text_color == "white"
        assert visualizer.grid_color == "#333333"
        assert visualizer.up_color == "#00ff9f"
        assert visualizer.down_color == "#ff5757"
        assert visualizer.neutral_color == "#aaaaaa"
        assert visualizer.volume_color == "#3498db"
        assert visualizer.highlight_color == "#ffcc00"

    def test_init_light_theme(self):
        """Test light theme initialization."""
        visualizer = MarketVisualizer(theme="light")
        assert visualizer.theme == "light"
        assert visualizer.text_color == "black"
        assert visualizer.grid_color == "#dddddd"
        assert visualizer.up_color == "#00aa5e"
        assert visualizer.down_color == "#d63031"
        assert visualizer.neutral_color == "#636e72"
        assert visualizer.volume_color == "#0984e3"
        assert visualizer.highlight_color == "#e67e22"

    def test_setup_plot_style_dark(self):
        """Test plot style setup for dark theme."""
        visualizer = MarketVisualizer(theme="dark")
        visualizer.setup_plot_style()
        assert visualizer.text_color == "white"

    def test_setup_plot_style_light(self):
        """Test plot style setup for light theme."""
        visualizer = MarketVisualizer(theme="light")
        visualizer.setup_plot_style()
        assert visualizer.text_color == "black"


# ============================================================================
# Test create_price_chart
# ============================================================================


@pytest.mark.asyncio()
class TestCreatePriceChart:
    """Tests for create_price_chart method."""

    async def test_empty_price_history(self, visualizer_dark):
        """Test with empty price history."""
        result = await visualizer_dark.create_price_chart(
            price_history=[],
            item_name="Test Item",
            game="csgo",
        )
        assert isinstance(result, io.BytesIO)
        # Verify it's a valid image
        img = Image.open(result)
        assert img.width > 0
        assert img.height > 0

    async def test_basic_price_chart(self, visualizer_dark, basic_price_history):
        """Test basic price chart creation."""
        result = await visualizer_dark.create_price_chart(
            price_history=basic_price_history,
            item_name="Test Item",
            game="csgo",
            include_volume=False,
        )
        assert isinstance(result, io.BytesIO)
        result.seek(0)
        # Check it's valid PNG data
        assert result.read(8) == b"\x89PNG\r\n\x1a\n"

    async def test_price_chart_with_volume(self, visualizer_dark, price_history_with_volume):
        """Test price chart with volume data."""
        result = await visualizer_dark.create_price_chart(
            price_history=price_history_with_volume,
            item_name="Test Item",
            game="csgo",
            include_volume=True,
        )
        assert isinstance(result, io.BytesIO)

    async def test_price_chart_without_volume_flag(self, visualizer_dark, price_history_with_volume):
        """Test price chart with volume data but flag disabled."""
        result = await visualizer_dark.create_price_chart(
            price_history=price_history_with_volume,
            item_name="Test Item",
            game="csgo",
            include_volume=False,
        )
        assert isinstance(result, io.BytesIO)

    async def test_price_chart_extended_data(self, visualizer_dark, extended_price_history):
        """Test price chart with extended data for support/resistance."""
        result = await visualizer_dark.create_price_chart(
            price_history=extended_price_history,
            item_name="Test Item",
            game="csgo",
        )
        assert isinstance(result, io.BytesIO)

    async def test_price_chart_different_games(self, visualizer_dark, basic_price_history):
        """Test price chart with different game codes."""
        games = ["csgo", "dota2", "tf2", "rust", "unknown_game"]
        for game in games:
            result = await visualizer_dark.create_price_chart(
                price_history=basic_price_history,
                item_name="Test Item",
                game=game,
            )
            assert isinstance(result, io.BytesIO)

    async def test_price_chart_custom_dimensions(self, visualizer_dark, basic_price_history):
        """Test price chart with custom dimensions."""
        result = await visualizer_dark.create_price_chart(
            price_history=basic_price_history,
            item_name="Test Item",
            game="csgo",
            width=1200,
            height=800,
        )
        assert isinstance(result, io.BytesIO)

    async def test_price_chart_light_theme(self, visualizer_light, basic_price_history):
        """Test price chart with light theme."""
        result = await visualizer_light.create_price_chart(
            price_history=basic_price_history,
            item_name="Test Item",
            game="csgo",
        )
        assert isinstance(result, io.BytesIO)


# ============================================================================
# Test create_market_comparison_chart
# ============================================================================


@pytest.mark.asyncio()
class TestCreateMarketComparisonChart:
    """Tests for create_market_comparison_chart method."""

    async def test_empty_items_data(self, visualizer_dark):
        """Test with empty items data."""
        result = await visualizer_dark.create_market_comparison_chart(
            items_data=[],
            price_histories={},
        )
        assert isinstance(result, io.BytesIO)

    async def test_empty_price_histories(self, visualizer_dark):
        """Test with empty price histories."""
        items_data = [{"itemId": "item1", "title": "Item 1"}]
        result = await visualizer_dark.create_market_comparison_chart(
            items_data=items_data,
            price_histories={},
        )
        assert isinstance(result, io.BytesIO)

    async def test_valid_comparison_chart(self, visualizer_dark, basic_price_history):
        """Test valid comparison chart creation."""
        items_data = [
            {"itemId": "item1", "title": "Item 1"},
            {"itemId": "item2", "title": "Item 2"},
        ]
        price_histories = {
            "item1": basic_price_history,
            "item2": basic_price_history,
        }
        result = await visualizer_dark.create_market_comparison_chart(
            items_data=items_data,
            price_histories=price_histories,
        )
        assert isinstance(result, io.BytesIO)

    async def test_comparison_chart_missing_item(self, visualizer_dark, basic_price_history):
        """Test comparison chart with missing item in histories."""
        items_data = [
            {"itemId": "item1", "title": "Item 1"},
            {"itemId": "item2", "title": "Item 2"},
            {"itemId": "item3", "title": "Item 3"},  # No history
        ]
        price_histories = {
            "item1": basic_price_history,
            "item2": basic_price_history,
        }
        result = await visualizer_dark.create_market_comparison_chart(
            items_data=items_data,
            price_histories=price_histories,
        )
        assert isinstance(result, io.BytesIO)

    async def test_comparison_chart_empty_history(self, visualizer_dark, basic_price_history):
        """Test comparison chart with empty history for one item."""
        items_data = [
            {"itemId": "item1", "title": "Item 1"},
            {"itemId": "item2", "title": "Item 2"},
        ]
        price_histories = {
            "item1": basic_price_history,
            "item2": [],  # Empty history
        }
        result = await visualizer_dark.create_market_comparison_chart(
            items_data=items_data,
            price_histories=price_histories,
        )
        assert isinstance(result, io.BytesIO)

    async def test_comparison_chart_zero_first_price(self, visualizer_dark):
        """Test comparison chart with zero first price."""
        items_data = [{"itemId": "item1", "title": "Item 1"}]
        now = datetime.now(UTC)
        price_histories = {
            "item1": [
                {"price": 0.0, "timestamp": (now - timedelta(days=1)).timestamp()},
                {"price": 10.0, "timestamp": now.timestamp()},
            ],
        }
        result = await visualizer_dark.create_market_comparison_chart(
            items_data=items_data,
            price_histories=price_histories,
        )
        assert isinstance(result, io.BytesIO)

    async def test_comparison_chart_custom_dimensions(self, visualizer_dark, basic_price_history):
        """Test comparison chart with custom dimensions."""
        items_data = [{"itemId": "item1", "title": "Item 1"}]
        price_histories = {"item1": basic_price_history}
        result = await visualizer_dark.create_market_comparison_chart(
            items_data=items_data,
            price_histories=price_histories,
            width=1000,
            height=700,
        )
        assert isinstance(result, io.BytesIO)


# ============================================================================
# Test create_pattern_visualization
# ============================================================================


@pytest.mark.asyncio()
class TestCreatePatternVisualization:
    """Tests for create_pattern_visualization method."""

    async def test_empty_price_history(self, visualizer_dark, mixed_patterns):
        """Test with empty price history."""
        result = await visualizer_dark.create_pattern_visualization(
            price_history=[],
            patterns=mixed_patterns,
            item_name="Test Item",
        )
        assert isinstance(result, io.BytesIO)

    async def test_empty_patterns(self, visualizer_dark, extended_price_history):
        """Test with empty patterns."""
        result = await visualizer_dark.create_pattern_visualization(
            price_history=extended_price_history,
            patterns=[],
            item_name="Test Item",
        )
        assert isinstance(result, io.BytesIO)

    async def test_valid_pattern_visualization(
        self, visualizer_dark, extended_price_history, mixed_patterns
    ):
        """Test valid pattern visualization."""
        result = await visualizer_dark.create_pattern_visualization(
            price_history=extended_price_history,
            patterns=mixed_patterns,
            item_name="Test Item",
        )
        assert isinstance(result, io.BytesIO)

    async def test_pattern_visualization_reversal_upward(
        self, visualizer_dark, extended_price_history
    ):
        """Test pattern visualization with upward reversal."""
        patterns = [{"type": "reversal", "confidence": 0.9, "direction": "upward"}]
        result = await visualizer_dark.create_pattern_visualization(
            price_history=extended_price_history,
            patterns=patterns,
            item_name="Test Item",
        )
        assert isinstance(result, io.BytesIO)

    async def test_pattern_visualization_reversal_downward(
        self, visualizer_dark, extended_price_history
    ):
        """Test pattern visualization with downward reversal."""
        patterns = [{"type": "reversal", "confidence": 0.9, "direction": "downward"}]
        result = await visualizer_dark.create_pattern_visualization(
            price_history=extended_price_history,
            patterns=patterns,
            item_name="Test Item",
        )
        assert isinstance(result, io.BytesIO)

    async def test_pattern_visualization_fomo(self, visualizer_dark, extended_price_history):
        """Test pattern visualization with FOMO pattern."""
        patterns = [{"type": "fomo", "confidence": 0.85}]
        result = await visualizer_dark.create_pattern_visualization(
            price_history=extended_price_history,
            patterns=patterns,
            item_name="Test Item",
        )
        assert isinstance(result, io.BytesIO)

    async def test_pattern_visualization_panic(self, visualizer_dark, extended_price_history):
        """Test pattern visualization with panic pattern."""
        patterns = [{"type": "panic", "confidence": 0.8}]
        result = await visualizer_dark.create_pattern_visualization(
            price_history=extended_price_history,
            patterns=patterns,
            item_name="Test Item",
        )
        assert isinstance(result, io.BytesIO)

    async def test_pattern_visualization_low_confidence(
        self, visualizer_dark, extended_price_history
    ):
        """Test pattern visualization with low confidence patterns (filtered out)."""
        patterns = [
            {"type": "breakout", "confidence": 0.3},  # Below 0.5 threshold
            {"type": "consolidation", "confidence": 0.2},
        ]
        result = await visualizer_dark.create_pattern_visualization(
            price_history=extended_price_history,
            patterns=patterns,
            item_name="Test Item",
        )
        assert isinstance(result, io.BytesIO)

    async def test_pattern_visualization_custom_dimensions(
        self, visualizer_dark, extended_price_history, mixed_patterns
    ):
        """Test pattern visualization with custom dimensions."""
        result = await visualizer_dark.create_pattern_visualization(
            price_history=extended_price_history,
            patterns=mixed_patterns,
            item_name="Test Item",
            width=1000,
            height=600,
        )
        assert isinstance(result, io.BytesIO)


# ============================================================================
# Test create_market_summary_image
# ============================================================================


@pytest.mark.asyncio()
class TestCreateMarketSummaryImage:
    """Tests for create_market_summary_image method."""

    async def test_basic_summary_image(self, visualizer_dark, sample_item_data, sample_analysis):
        """Test basic market summary image creation."""
        result = await visualizer_dark.create_market_summary_image(
            item_data=sample_item_data,
            analysis=sample_analysis,
        )
        assert isinstance(result, io.BytesIO)

    async def test_summary_image_light_theme(
        self, visualizer_light, sample_item_data, sample_analysis
    ):
        """Test summary image with light theme."""
        result = await visualizer_light.create_market_summary_image(
            item_data=sample_item_data,
            analysis=sample_analysis,
        )
        assert isinstance(result, io.BytesIO)

    async def test_summary_image_numeric_price(self, visualizer_dark, sample_analysis):
        """Test summary image with numeric price format."""
        item_data = {
            "title": "Test Item",
            "price": 15.50,
        }
        result = await visualizer_dark.create_market_summary_image(
            item_data=item_data,
            analysis=sample_analysis,
        )
        assert isinstance(result, io.BytesIO)

    async def test_summary_image_no_price(self, visualizer_dark, sample_analysis):
        """Test summary image without price."""
        item_data = {
            "title": "Test Item",
        }
        result = await visualizer_dark.create_market_summary_image(
            item_data=item_data,
            analysis=sample_analysis,
        )
        assert isinstance(result, io.BytesIO)

    async def test_summary_image_down_trend(self, visualizer_dark, sample_item_data):
        """Test summary image with down trend."""
        analysis = {
            "trend": "down",
            "volatility": "high",
            "price_change_24h": -5.5,
            "price_change_7d": -12.3,
        }
        result = await visualizer_dark.create_market_summary_image(
            item_data=sample_item_data,
            analysis=analysis,
        )
        assert isinstance(result, io.BytesIO)

    async def test_summary_image_stable_trend(self, visualizer_dark, sample_item_data):
        """Test summary image with stable trend."""
        analysis = {
            "trend": "stable",
            "volatility": "low",
            "price_change_24h": 0.0,
            "price_change_7d": 0.5,
        }
        result = await visualizer_dark.create_market_summary_image(
            item_data=sample_item_data,
            analysis=analysis,
        )
        assert isinstance(result, io.BytesIO)

    async def test_summary_image_with_support_resistance(self, visualizer_dark, sample_item_data):
        """Test summary image with support and resistance levels."""
        analysis = {
            "trend": "up",
            "volatility": "medium",
            "support_level": 12.0,
            "resistance_level": 18.0,
        }
        result = await visualizer_dark.create_market_summary_image(
            item_data=sample_item_data,
            analysis=analysis,
        )
        assert isinstance(result, io.BytesIO)

    async def test_summary_image_without_support_resistance(self, visualizer_dark, sample_item_data):
        """Test summary image without support and resistance levels."""
        analysis = {
            "trend": "up",
            "volatility": "low",
        }
        result = await visualizer_dark.create_market_summary_image(
            item_data=sample_item_data,
            analysis=analysis,
        )
        assert isinstance(result, io.BytesIO)

    async def test_summary_image_with_patterns(self, visualizer_dark, sample_item_data):
        """Test summary image with detected patterns."""
        analysis = {
            "trend": "up",
            "volatility": "medium",
            "patterns": [
                {"type": "breakout", "confidence": 0.9},
                {"type": "fomo_detected", "confidence": 0.8},
                {"type": "trend_continuation", "confidence": 0.7},
                {"type": "extra_pattern", "confidence": 0.6},  # More than 3
            ],
        }
        result = await visualizer_dark.create_market_summary_image(
            item_data=sample_item_data,
            analysis=analysis,
        )
        assert isinstance(result, io.BytesIO)

    async def test_summary_image_empty_patterns(self, visualizer_dark, sample_item_data):
        """Test summary image with empty patterns list."""
        analysis = {
            "trend": "up",
            "volatility": "low",
            "patterns": [],
        }
        result = await visualizer_dark.create_market_summary_image(
            item_data=sample_item_data,
            analysis=analysis,
        )
        assert isinstance(result, io.BytesIO)

    async def test_summary_image_custom_dimensions(
        self, visualizer_dark, sample_item_data, sample_analysis
    ):
        """Test summary image with custom dimensions."""
        result = await visualizer_dark.create_market_summary_image(
            item_data=sample_item_data,
            analysis=sample_analysis,
            width=1000,
            height=500,
        )
        assert isinstance(result, io.BytesIO)

    async def test_summary_image_volatility_levels(self, visualizer_dark, sample_item_data):
        """Test summary image with different volatility levels."""
        for volatility in ["low", "medium", "high"]:
            analysis = {"trend": "up", "volatility": volatility}
            result = await visualizer_dark.create_market_summary_image(
                item_data=sample_item_data,
                analysis=analysis,
            )
            assert isinstance(result, io.BytesIO)


# ============================================================================
# Test process_price_data
# ============================================================================


class TestProcessPriceData:
    """Tests for process_price_data method."""

    def test_basic_processing(self, visualizer_dark, basic_price_history):
        """Test basic price data processing."""
        df = visualizer_dark.process_price_data(basic_price_history)
        assert len(df) == 3
        assert "price" in df.columns
        assert df["price"].iloc[0] == 10.0

    def test_processing_with_volume(self, visualizer_dark, price_history_with_volume):
        """Test price data processing with volume."""
        df = visualizer_dark.process_price_data(price_history_with_volume)
        assert len(df) == 7
        assert "price" in df.columns
        assert "volume" in df.columns

    def test_processing_dict_price_format(self, visualizer_dark, price_history_dict_format):
        """Test price data processing with dict price format."""
        df = visualizer_dark.process_price_data(price_history_dict_format)
        assert len(df) == 3
        assert df["price"].iloc[0] == 10.0  # 1000 cents / 100

    def test_processing_string_price_format(self, visualizer_dark):
        """Test price data processing with string price format."""
        now = datetime.now(UTC)
        history = [
            {"price": "10.50", "timestamp": (now - timedelta(days=1)).timestamp()},
            {"price": "11.00", "timestamp": now.timestamp()},
        ]
        df = visualizer_dark.process_price_data(history)
        assert len(df) == 2
        assert df["price"].iloc[0] == 10.50

    def test_processing_iso_timestamp(self, visualizer_dark):
        """Test price data processing with ISO format timestamp."""
        now = datetime.now(UTC)
        history = [
            {"price": 10.0, "timestamp": now.isoformat()},
        ]
        df = visualizer_dark.process_price_data(history)
        assert len(df) == 1

    def test_processing_string_timestamp(self, visualizer_dark):
        """Test price data processing with string timestamp (epoch)."""
        now = datetime.now(UTC)
        history = [
            {"price": 10.0, "timestamp": str(now.timestamp())},
        ]
        df = visualizer_dark.process_price_data(history)
        assert len(df) == 1

    def test_processing_empty_history(self, visualizer_dark):
        """Test price data processing with empty history."""
        df = visualizer_dark.process_price_data([])
        assert len(df) == 0

    def test_processing_missing_timestamp(self, visualizer_dark):
        """Test price data processing with missing timestamp."""
        history = [
            {"price": 10.0},  # No timestamp
        ]
        df = visualizer_dark.process_price_data(history)
        assert len(df) == 0

    def test_processing_missing_price(self, visualizer_dark):
        """Test price data processing with missing price."""
        now = datetime.now(UTC)
        history = [
            {"timestamp": now.timestamp()},  # No price
        ]
        df = visualizer_dark.process_price_data(history)
        assert len(df) == 0

    def test_processing_invalid_timestamp_format(self, visualizer_dark):
        """Test price data processing with invalid timestamp format."""
        history = [
            {"price": 10.0, "timestamp": "invalid-timestamp"},
        ]
        df = visualizer_dark.process_price_data(history)
        assert len(df) == 0

    def test_processing_invalid_price_format(self, visualizer_dark):
        """Test price data processing with invalid price format."""
        now = datetime.now(UTC)
        history = [
            {"price": "invalid", "timestamp": now.timestamp()},
        ]
        df = visualizer_dark.process_price_data(history)
        assert len(df) == 0

    def test_processing_partial_volume(self, visualizer_dark):
        """Test price data processing with partial volume data."""
        now = datetime.now(UTC)
        history = [
            {"price": 10.0, "timestamp": (now - timedelta(days=2)).timestamp(), "volume": 100},
            {"price": 11.0, "timestamp": (now - timedelta(days=1)).timestamp()},  # No volume
            {"price": 12.0, "timestamp": now.timestamp(), "volume": 120},
        ]
        df = visualizer_dark.process_price_data(history)
        assert len(df) == 3
        # Volume column should not be present if not all entries have it
        assert "volume" not in df.columns or df["volume"].isna().any()

    def test_processing_sorts_by_date(self, visualizer_dark):
        """Test price data is sorted by date."""
        now = datetime.now(UTC)
        # Provide data in reverse order
        history = [
            {"price": 12.0, "timestamp": now.timestamp()},
            {"price": 10.0, "timestamp": (now - timedelta(days=2)).timestamp()},
            {"price": 11.0, "timestamp": (now - timedelta(days=1)).timestamp()},
        ]
        df = visualizer_dark.process_price_data(history)
        assert df["price"].iloc[0] == 10.0  # Oldest first
        assert df["price"].iloc[-1] == 12.0  # Newest last


# ============================================================================
# Test color_trend_regions
# ============================================================================


class TestColorTrendRegions:
    """Tests for color_trend_regions method."""

    def test_insufficient_data(self, visualizer_dark):
        """Test with insufficient data (less than 3 points)."""
        dates = [datetime.now(UTC) - timedelta(days=x) for x in range(2, 0, -1)]
        df = pd.DataFrame({"price": [10.0, 11.0]}, index=dates)

        ax = MagicMock()
        visualizer_dark.color_trend_regions(ax, df)
        # Should not add any patches
        ax.add_patch.assert_not_called()

    def test_uptrend_coloring(self, visualizer_dark):
        """Test uptrend region coloring."""
        dates = [datetime.now(UTC) - timedelta(days=x) for x in range(5, 0, -1)]
        df = pd.DataFrame({"price": [10.0, 11.0, 12.0, 13.0, 14.0]}, index=dates)

        ax = MagicMock()
        visualizer_dark.color_trend_regions(ax, df)
        # Should add patches for trend regions
        assert ax.add_patch.called

    def test_downtrend_coloring(self, visualizer_dark):
        """Test downtrend region coloring."""
        dates = [datetime.now(UTC) - timedelta(days=x) for x in range(5, 0, -1)]
        df = pd.DataFrame({"price": [14.0, 13.0, 12.0, 11.0, 10.0]}, index=dates)

        ax = MagicMock()
        visualizer_dark.color_trend_regions(ax, df)
        assert ax.add_patch.called

    def test_mixed_trend_coloring(self, visualizer_dark):
        """Test mixed trend region coloring."""
        dates = [datetime.now(UTC) - timedelta(days=x) for x in range(7, 0, -1)]
        df = pd.DataFrame(
            {"price": [10.0, 11.0, 12.0, 11.5, 11.0, 11.5, 12.0]}, index=dates
        )

        ax = MagicMock()
        visualizer_dark.color_trend_regions(ax, df)
        assert ax.add_patch.called


# ============================================================================
# Test add_support_resistance
# ============================================================================


class TestAddSupportResistance:
    """Tests for add_support_resistance method."""

    def test_insufficient_data(self, visualizer_dark):
        """Test with insufficient data (less than 10 points)."""
        dates = [datetime.now(UTC) - timedelta(days=x) for x in range(5, 0, -1)]
        df = pd.DataFrame({"price": [10.0, 11.0, 10.5, 11.5, 10.0]}, index=dates)

        ax = MagicMock()
        visualizer_dark.add_support_resistance(ax, df)
        # Should not add any lines
        ax.axhline.assert_not_called()

    def test_valid_support_resistance(self, visualizer_dark):
        """Test with valid data for support/resistance detection."""
        dates = [datetime.now(UTC) - timedelta(days=x) for x in range(15, 0, -1)]
        # Create data with clear support/resistance levels
        prices = [
            10.0, 11.0, 10.5, 10.0, 11.5, 12.0, 11.8, 11.0, 10.5, 11.0,
            12.5, 13.0, 12.8, 13.5, 14.0
        ]
        df = pd.DataFrame({"price": prices}, index=dates)

        ax = MagicMock()
        visualizer_dark.add_support_resistance(ax, df)
        # Should add horizontal lines
        assert ax.axhline.called

    def test_flat_price_data(self, visualizer_dark):
        """Test with flat price data (no local min/max)."""
        dates = [datetime.now(UTC) - timedelta(days=x) for x in range(15, 0, -1)]
        prices = [10.0] * 15  # All same price
        df = pd.DataFrame({"price": prices}, index=dates)

        ax = MagicMock()
        visualizer_dark.add_support_resistance(ax, df)
        # May or may not add lines depending on implementation


# ============================================================================
# Test Edge Cases
# ============================================================================


@pytest.mark.asyncio()
class TestEdgeCases:
    """Tests for edge cases and error handling."""

    async def test_very_large_dataset(self, visualizer_dark):
        """Test with very large dataset."""
        now = datetime.now(UTC)
        history = [
            {"price": 10.0 + i * 0.01, "timestamp": (now - timedelta(hours=i)).timestamp()}
            for i in range(500)
        ]
        result = await visualizer_dark.create_price_chart(
            price_history=history,
            item_name="Test Item",
            game="csgo",
        )
        assert isinstance(result, io.BytesIO)

    async def test_single_data_point(self, visualizer_dark):
        """Test with single data point."""
        now = datetime.now(UTC)
        history = [{"price": 10.0, "timestamp": now.timestamp()}]
        result = await visualizer_dark.create_price_chart(
            price_history=history,
            item_name="Test Item",
            game="csgo",
        )
        assert isinstance(result, io.BytesIO)

    async def test_unicode_item_name(self, visualizer_dark, basic_price_history):
        """Test with unicode characters in item name."""
        result = await visualizer_dark.create_price_chart(
            price_history=basic_price_history,
            item_name="AK-47 | Огненный змей (Field-Tested)",
            game="csgo",
        )
        assert isinstance(result, io.BytesIO)

    async def test_special_characters_in_name(self, visualizer_dark, basic_price_history):
        """Test with special characters in item name."""
        result = await visualizer_dark.create_price_chart(
            price_history=basic_price_history,
            item_name="★ M9 Bayonet | Doppler (Factory New)",
            game="csgo",
        )
        assert isinstance(result, io.BytesIO)

    async def test_very_small_dimensions(self, visualizer_dark, basic_price_history):
        """Test with very small dimensions."""
        result = await visualizer_dark.create_price_chart(
            price_history=basic_price_history,
            item_name="Test Item",
            game="csgo",
            width=100,
            height=50,
        )
        assert isinstance(result, io.BytesIO)

    async def test_very_large_dimensions(self, visualizer_dark, basic_price_history):
        """Test with very large dimensions."""
        result = await visualizer_dark.create_price_chart(
            price_history=basic_price_history,
            item_name="Test Item",
            game="csgo",
            width=3000,
            height=2000,
        )
        assert isinstance(result, io.BytesIO)

    async def test_extreme_price_values(self, visualizer_dark):
        """Test with extreme price values."""
        now = datetime.now(UTC)
        history = [
            {"price": 0.01, "timestamp": (now - timedelta(days=2)).timestamp()},
            {"price": 100000.0, "timestamp": (now - timedelta(days=1)).timestamp()},
            {"price": 50000.0, "timestamp": now.timestamp()},
        ]
        result = await visualizer_dark.create_price_chart(
            price_history=history,
            item_name="Test Item",
            game="csgo",
        )
        assert isinstance(result, io.BytesIO)

    async def test_negative_price_values(self, visualizer_dark):
        """Test with negative price values (should be handled gracefully)."""
        now = datetime.now(UTC)
        history = [
            {"price": -10.0, "timestamp": (now - timedelta(days=2)).timestamp()},
            {"price": 10.0, "timestamp": (now - timedelta(days=1)).timestamp()},
            {"price": 20.0, "timestamp": now.timestamp()},
        ]
        result = await visualizer_dark.create_price_chart(
            price_history=history,
            item_name="Test Item",
            game="csgo",
        )
        assert isinstance(result, io.BytesIO)

    async def test_duplicate_timestamps(self, visualizer_dark):
        """Test with duplicate timestamps."""
        now = datetime.now(UTC)
        history = [
            {"price": 10.0, "timestamp": now.timestamp()},
            {"price": 11.0, "timestamp": now.timestamp()},  # Same timestamp
            {"price": 12.0, "timestamp": (now + timedelta(days=1)).timestamp()},
        ]
        result = await visualizer_dark.create_price_chart(
            price_history=history,
            item_name="Test Item",
            game="csgo",
        )
        assert isinstance(result, io.BytesIO)


# ============================================================================
# Test Integration Scenarios
# ============================================================================


@pytest.mark.asyncio()
class TestIntegration:
    """Integration tests for MarketVisualizer."""

    async def test_full_workflow_price_chart(self, visualizer_dark, extended_price_history):
        """Test full workflow for creating a price chart."""
        # Create chart
        result = await visualizer_dark.create_price_chart(
            price_history=extended_price_history,
            item_name="AK-47 | Redline",
            game="csgo",
            include_volume=False,
        )

        # Verify result
        assert isinstance(result, io.BytesIO)
        result.seek(0)

        # Open as image and verify
        img = Image.open(result)
        assert img.format == "PNG"
        assert img.width > 0
        assert img.height > 0

    async def test_full_workflow_comparison(self, visualizer_dark, extended_price_history):
        """Test full workflow for creating a comparison chart."""
        items = [
            {"itemId": "item1", "title": "AK-47 | Redline"},
            {"itemId": "item2", "title": "M4A4 | Asiimov"},
        ]
        histories = {
            "item1": extended_price_history,
            "item2": extended_price_history,
        }

        result = await visualizer_dark.create_market_comparison_chart(
            items_data=items,
            price_histories=histories,
        )

        assert isinstance(result, io.BytesIO)
        result.seek(0)
        img = Image.open(result)
        assert img.format == "PNG"

    async def test_full_workflow_pattern(
        self, visualizer_dark, extended_price_history, mixed_patterns
    ):
        """Test full workflow for creating a pattern visualization."""
        result = await visualizer_dark.create_pattern_visualization(
            price_history=extended_price_history,
            patterns=mixed_patterns,
            item_name="AK-47 | Redline",
        )

        assert isinstance(result, io.BytesIO)
        result.seek(0)
        img = Image.open(result)
        assert img.format == "PNG"

    async def test_full_workflow_summary(
        self, visualizer_dark, sample_item_data, sample_analysis
    ):
        """Test full workflow for creating a market summary image."""
        result = await visualizer_dark.create_market_summary_image(
            item_data=sample_item_data,
            analysis=sample_analysis,
        )

        assert isinstance(result, io.BytesIO)
        result.seek(0)
        img = Image.open(result)
        assert img.format == "PNG"

    async def test_theme_switching(self, basic_price_history):
        """Test switching between themes."""
        dark_viz = MarketVisualizer(theme="dark")
        light_viz = MarketVisualizer(theme="light")

        dark_result = await dark_viz.create_price_chart(
            price_history=basic_price_history,
            item_name="Test Item",
            game="csgo",
        )

        light_result = await light_viz.create_price_chart(
            price_history=basic_price_history,
            item_name="Test Item",
            game="csgo",
        )

        # Both should produce valid images
        assert isinstance(dark_result, io.BytesIO)
        assert isinstance(light_result, io.BytesIO)

        # Images should be different (different themes)
        dark_result.seek(0)
        light_result.seek(0)
        assert dark_result.read() != light_result.read()
