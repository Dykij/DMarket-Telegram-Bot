"""Tests for analytics and visualization functionality.

This module contains tests for chart generation, market analysis,
and data visualization utilities.
"""

import io
from unittest.mock import patch

import pytest

from src.utils.analytics import ChartGenerator, MarketAnalyzer, generate_market_report
from tests.conftest import TestUtils


class TestChartGenerator:
    """Test cases for chart generation."""

    @pytest.fixture
    def chart_generator(self) -> ChartGenerator:
        """Create chart generator for testing."""
        return ChartGenerator()

    def test_chart_generator_initialization(self, chart_generator: ChartGenerator):
        """Test chart generator initialization."""
        assert chart_generator.style == "seaborn"
        assert chart_generator.figsize == (12, 8)

    def test_create_price_history_chart(self, chart_generator: ChartGenerator):
        """Test price history chart creation."""
        price_data = TestUtils.create_mock_price_history(days=7, base_price=10.0)

        chart_buffer = chart_generator.create_price_history_chart(
            price_data=price_data,
            title="Test Price History",
            currency="USD",
        )

        assert isinstance(chart_buffer, io.BytesIO)
        assert chart_buffer.tell() > 0  # Buffer should contain data

        # Reset buffer position for reading
        chart_buffer.seek(0)
        assert len(chart_buffer.read()) > 1000  # Should be a reasonable size PNG

    def test_create_price_history_chart_empty_data(
        self,
        chart_generator: ChartGenerator,
    ):
        """Test price history chart with empty data."""
        chart_buffer = chart_generator.create_price_history_chart(
            price_data=[],
            title="Empty Data Test",
        )

        assert isinstance(chart_buffer, io.BytesIO)
        # Should return error chart, not fail

    def test_create_market_overview_chart(self, chart_generator: ChartGenerator):
        """Test market overview chart creation."""
        items_data = [
            {"name": "Item 1", "price": 25.50},
            {"name": "Item 2", "price": 15.75},
            {"name": "Item 3", "price": 45.25},
            {
                "name": "Item 4 with very long name that should be truncated",
                "price": 8.99,
            },
        ]

        chart_buffer = chart_generator.create_market_overview_chart(
            items_data=items_data,
            title="Test Market Overview",
        )

        assert isinstance(chart_buffer, io.BytesIO)
        chart_buffer.seek(0)
        assert len(chart_buffer.read()) > 1000

    def test_create_arbitrage_opportunities_chart(
        self,
        chart_generator: ChartGenerator,
    ):
        """Test arbitrage opportunities chart creation."""
        opportunities = [
            {
                "item_title": "Test Item 1",
                "profit_amount": 5.25,
                "profit_percentage": 15.5,
            },
            {
                "item_title": "Test Item 2",
                "profit_amount": 3.75,
                "profit_percentage": 12.3,
            },
            {
                "item_title": "Test Item 3",
                "profit_amount": 8.50,
                "profit_percentage": 22.1,
            },
        ]

        chart_buffer = chart_generator.create_arbitrage_opportunities_chart(
            opportunities=opportunities,
            title="Test Arbitrage",
        )

        assert isinstance(chart_buffer, io.BytesIO)
        chart_buffer.seek(0)
        assert len(chart_buffer.read()) > 1000

    def test_create_volume_analysis_chart(self, chart_generator: ChartGenerator):
        """Test volume analysis chart creation."""
        from datetime import datetime, timedelta

        volume_data = []
        for i in range(10):
            volume_data.append(
                {
                    "date": (datetime.now() - timedelta(days=10 - i)).isoformat(),
                    "volume": 100 + i * 10,
                },
            )

        chart_buffer = chart_generator.create_volume_analysis_chart(
            volume_data=volume_data,
            title="Test Volume Analysis",
        )

        assert isinstance(chart_buffer, io.BytesIO)
        chart_buffer.seek(0)
        assert len(chart_buffer.read()) > 1000

    def test_create_error_chart(self, chart_generator: ChartGenerator):
        """Test error chart creation."""
        error_chart = chart_generator._create_error_chart("Test error message")

        assert isinstance(error_chart, io.BytesIO)
        error_chart.seek(0)
        assert len(error_chart.read()) > 0

    @patch("matplotlib.pyplot.savefig")
    def test_chart_creation_error_handling(
        self,
        mock_savefig,
        chart_generator: ChartGenerator,
    ):
        """Test chart creation error handling."""
        # Mock matplotlib to raise an exception
        mock_savefig.side_effect = Exception("Matplotlib error")

        # Should not raise exception, should return error chart
        chart_buffer = chart_generator.create_price_history_chart(
            price_data=[{"date": "2023-01-01", "price": 10.0}],
        )

        assert isinstance(chart_buffer, io.BytesIO)


class TestMarketAnalyzer:
    """Test cases for market analysis utilities."""

    def test_calculate_price_statistics(self):
        """Test price statistics calculation."""
        price_data = [10.0, 12.5, 8.75, 15.25, 11.50, 9.25, 13.75]

        stats = MarketAnalyzer.calculate_price_statistics(price_data)

        assert "mean" in stats
        assert "median" in stats
        assert "std" in stats
        assert "min" in stats
        assert "max" in stats
        assert "q25" in stats
        assert "q75" in stats
        assert "range" in stats
        assert "cv" in stats

        # Check some basic properties
        assert stats["min"] == min(price_data)
        assert stats["max"] == max(price_data)
        assert stats["range"] == max(price_data) - min(price_data)
        assert 0 <= stats["cv"] <= 1  # Coefficient of variation should be reasonable

    def test_calculate_price_statistics_empty(self):
        """Test price statistics with empty data."""
        stats = MarketAnalyzer.calculate_price_statistics([])
        assert stats == {}

    def test_detect_price_trends(self):
        """Test price trend detection."""
        # Create upward trend
        upward_data = []
        for i in range(10):
            upward_data.append(
                {
                    "date": f"2023-01-{i+1:02d}",
                    "price": 10.0 + i * 0.5,  # Increasing price
                },
            )

        trend = MarketAnalyzer.detect_price_trends(upward_data, window=5)

        assert "trend" in trend
        assert "confidence" in trend
        assert "price_change_percent" in trend
        assert "latest_price" in trend

        # Should detect upward trend
        assert trend["trend"] == "upward"
        assert trend["confidence"] > 0
        assert trend["price_change_percent"] > 0

    def test_detect_price_trends_insufficient_data(self):
        """Test trend detection with insufficient data."""
        short_data = [
            {"date": "2023-01-01", "price": 10.0},
            {"date": "2023-01-02", "price": 11.0},
        ]

        trend = MarketAnalyzer.detect_price_trends(short_data, window=5)

        assert trend["trend"] == "insufficient_data"
        assert trend["confidence"] == 0.0

    def test_find_support_resistance_levels(self):
        """Test support and resistance level detection."""
        # Create price data with obvious support/resistance
        price_data = [
            10,
            11,
            12,
            11,
            10,  # Support at 10
            15,
            16,
            15,
            14,
            15,  # Resistance at 15-16
            12,
            13,
            12,
            11,
            12,  # Mixed levels
            20,
            19,
            20,
            21,
            20,  # Resistance at 20
        ]

        levels = MarketAnalyzer.find_support_resistance_levels(
            price_data=price_data,
            window=2,
            min_touches=1,
        )

        assert "support" in levels
        assert "resistance" in levels
        assert isinstance(levels["support"], list)
        assert isinstance(levels["resistance"], list)

        # Should find some levels
        assert len(levels["support"]) <= 5
        assert len(levels["resistance"]) <= 5

    def test_find_support_resistance_insufficient_data(self):
        """Test support/resistance detection with insufficient data."""
        short_data = [10, 11, 12]

        levels = MarketAnalyzer.find_support_resistance_levels(
            price_data=short_data,
            window=5,
        )

        assert levels["support"] == []
        assert levels["resistance"] == []


class TestMarketReport:
    """Test cases for market report generation."""

    @pytest.fixture
    def chart_generator(self) -> ChartGenerator:
        """Create chart generator for testing."""
        return ChartGenerator()

    @pytest.mark.asyncio
    async def test_generate_market_report_complete(
        self,
        chart_generator: ChartGenerator,
    ):
        """Test complete market report generation."""
        market_data = {
            "price_history": TestUtils.create_mock_price_history(days=7),
            "top_items": [
                {"name": "Item 1", "price": 25.0},
                {"name": "Item 2", "price": 15.0},
            ],
            "arbitrage_opportunities": [
                {
                    "item_title": "Arb Item 1",
                    "profit_amount": 5.0,
                    "profit_percentage": 15.0,
                },
            ],
            "volume_data": [
                {"date": "2023-01-01", "volume": 100},
                {"date": "2023-01-02", "volume": 150},
            ],
        }

        charts = await generate_market_report(
            chart_generator=chart_generator,
            market_data=market_data,
            title="Test Market Report",
        )

        # Should generate 4 charts (one for each data type)
        assert len(charts) == 4
        assert all(isinstance(chart, io.BytesIO) for chart in charts)

        # Each chart should contain data
        for chart in charts:
            chart.seek(0)
            assert len(chart.read()) > 0

    @pytest.mark.asyncio
    async def test_generate_market_report_partial(
        self,
        chart_generator: ChartGenerator,
    ):
        """Test market report generation with partial data."""
        market_data = {
            "price_history": TestUtils.create_mock_price_history(days=5),
            # Missing other data types
        }

        charts = await generate_market_report(
            chart_generator=chart_generator,
            market_data=market_data,
            title="Partial Report",
        )

        # Should generate only 1 chart (price history)
        assert len(charts) == 1
        assert isinstance(charts[0], io.BytesIO)

    @pytest.mark.asyncio
    async def test_generate_market_report_empty(self, chart_generator: ChartGenerator):
        """Test market report generation with no data."""
        charts = await generate_market_report(
            chart_generator=chart_generator,
            market_data={},
            title="Empty Report",
        )

        # Should return empty list
        assert charts == []

    @pytest.mark.asyncio
    async def test_generate_market_report_error_handling(
        self,
        chart_generator: ChartGenerator,
    ):
        """Test market report generation with errors."""
        # Mock chart generator to raise exception
        with patch.object(chart_generator, "create_price_history_chart") as mock_create:
            mock_create.side_effect = Exception("Chart creation failed")

            market_data = {"price_history": TestUtils.create_mock_price_history(days=3)}

            charts = await generate_market_report(
                chart_generator=chart_generator,
                market_data=market_data,
                title="Error Test",
            )

            # Should handle error gracefully and return empty list
            assert charts == []
