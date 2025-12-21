"""Tests for chart_generator.py module.

This module provides comprehensive tests for:
- ChartGenerator class initialization
- generate_profit_chart tests
- generate_scan_history_chart tests
- generate_level_distribution_chart tests
- generate_profit_comparison_chart tests
- _generate_chart_url tests
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.telegram_bot.chart_generator import (
    QUICKCHART_API,
    ChartGenerator,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def chart_generator():
    """Create a ChartGenerator instance."""
    return ChartGenerator()


@pytest.fixture
def chart_generator_custom_size():
    """Create a ChartGenerator with custom dimensions."""
    return ChartGenerator(width=1200, height=600)


@pytest.fixture
def profit_data():
    """Sample profit data for testing."""
    return [
        {"date": "2024-01-01", "profit": 10.50},
        {"date": "2024-01-02", "profit": 15.25},
        {"date": "2024-01-03", "profit": -5.00},
        {"date": "2024-01-04", "profit": 20.00},
    ]


@pytest.fixture
def scan_history_data():
    """Sample scan history data for testing."""
    return [
        {"date": "2024-01-01", "count": 5},
        {"date": "2024-01-02", "count": 10},
        {"date": "2024-01-03", "count": 8},
    ]


@pytest.fixture
def level_distribution_data():
    """Sample level distribution data for testing."""
    return {
        "boost": 100,
        "standard": 250,
        "medium": 150,
        "advanced": 50,
        "pro": 20,
    }


@pytest.fixture
def mock_httpx_response():
    """Create a mock httpx response."""
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {"url": "https://quickchart.io/short/abc123"}
    return response


# ============================================================================
# ChartGenerator Initialization Tests
# ============================================================================


class TestChartGeneratorInitialization:
    """Test ChartGenerator initialization."""

    def test_init_default_dimensions(self):
        """Test initialization with default dimensions."""
        generator = ChartGenerator()
        assert generator.width == 800
        assert generator.height == 400

    def test_init_custom_dimensions(self):
        """Test initialization with custom dimensions."""
        generator = ChartGenerator(width=1000, height=500)
        assert generator.width == 1000
        assert generator.height == 500

    def test_init_only_width(self):
        """Test initialization with only width specified."""
        generator = ChartGenerator(width=1200)
        assert generator.width == 1200
        assert generator.height == 400

    def test_init_only_height(self):
        """Test initialization with only height specified."""
        generator = ChartGenerator(height=600)
        assert generator.width == 800
        assert generator.height == 600


# ============================================================================
# generate_profit_chart Tests
# ============================================================================


class TestGenerateProfitChart:
    """Test generate_profit_chart method."""

    @pytest.mark.asyncio
    async def test_generate_profit_chart_success(
        self, chart_generator, profit_data, mock_httpx_response
    ):
        """Test successful profit chart generation."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_httpx_response
            )
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_httpx_response
            )

            result = await chart_generator.generate_profit_chart(profit_data)

            assert result is not None
            assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_generate_profit_chart_empty_data(self, chart_generator):
        """Test profit chart with empty data returns None."""
        result = await chart_generator.generate_profit_chart([])
        assert result is None

    @pytest.mark.asyncio
    async def test_generate_profit_chart_none_data(self, chart_generator):
        """Test profit chart with None data."""
        result = await chart_generator.generate_profit_chart(None)
        assert result is None

    @pytest.mark.asyncio
    async def test_generate_profit_chart_missing_fields(self, chart_generator):
        """Test profit chart with missing fields uses defaults."""
        data = [{"date": "2024-01-01"}, {"profit": 10.0}]  # Missing profit  # Missing date

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await chart_generator.generate_profit_chart(data)
            # Should not raise, uses defaults


# ============================================================================
# generate_scan_history_chart Tests
# ============================================================================


class TestGenerateScanHistoryChart:
    """Test generate_scan_history_chart method."""

    @pytest.mark.asyncio
    async def test_generate_scan_history_success(
        self, chart_generator, scan_history_data, mock_httpx_response
    ):
        """Test successful scan history chart generation."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_httpx_response
            )
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_httpx_response
            )

            result = await chart_generator.generate_scan_history_chart(scan_history_data)

            assert result is not None

    @pytest.mark.asyncio
    async def test_generate_scan_history_empty_data(self, chart_generator):
        """Test scan history with empty data returns None."""
        result = await chart_generator.generate_scan_history_chart([])
        assert result is None

    @pytest.mark.asyncio
    async def test_generate_scan_history_single_item(self, chart_generator):
        """Test scan history with single item."""
        data = [{"date": "2024-01-01", "count": 5}]

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await chart_generator.generate_scan_history_chart(data)
            # Should succeed with single item


# ============================================================================
# generate_level_distribution_chart Tests
# ============================================================================


class TestGenerateLevelDistributionChart:
    """Test generate_level_distribution_chart method."""

    @pytest.mark.asyncio
    async def test_generate_level_distribution_success(
        self, chart_generator, level_distribution_data, mock_httpx_response
    ):
        """Test successful level distribution chart generation."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_httpx_response
            )
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_httpx_response
            )

            result = await chart_generator.generate_level_distribution_chart(
                level_distribution_data
            )

            assert result is not None

    @pytest.mark.asyncio
    async def test_generate_level_distribution_empty_data(self, chart_generator):
        """Test level distribution with empty data returns None."""
        result = await chart_generator.generate_level_distribution_chart({})
        assert result is None

    @pytest.mark.asyncio
    async def test_generate_level_distribution_single_level(self, chart_generator):
        """Test level distribution with single level."""
        data = {"boost": 100}

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await chart_generator.generate_level_distribution_chart(data)

    @pytest.mark.asyncio
    async def test_generate_level_distribution_many_levels(self, chart_generator):
        """Test level distribution with more than 5 levels."""
        data = {
            "level1": 10,
            "level2": 20,
            "level3": 30,
            "level4": 40,
            "level5": 50,
            "level6": 60,  # More than 5 levels
            "level7": 70,
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await chart_generator.generate_level_distribution_chart(data)


# ============================================================================
# generate_profit_comparison_chart Tests
# ============================================================================


class TestGenerateProfitComparisonChart:
    """Test generate_profit_comparison_chart method."""

    @pytest.mark.asyncio
    async def test_generate_profit_comparison_success(
        self, chart_generator, mock_httpx_response
    ):
        """Test successful profit comparison chart generation."""
        levels = ["boost", "standard", "medium"]
        avg_profits = [1.50, 3.25, 5.00]
        max_profits = [5.00, 10.00, 15.00]

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_httpx_response
            )
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_httpx_response
            )

            result = await chart_generator.generate_profit_comparison_chart(
                levels, avg_profits, max_profits
            )

            assert result is not None

    @pytest.mark.asyncio
    async def test_generate_profit_comparison_empty_levels(self, chart_generator):
        """Test profit comparison with empty levels returns None."""
        result = await chart_generator.generate_profit_comparison_chart(
            [], [1.0], [2.0]
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_generate_profit_comparison_empty_profits(self, chart_generator):
        """Test profit comparison with empty profits returns None."""
        result = await chart_generator.generate_profit_comparison_chart(
            ["boost"], [], [2.0]
        )
        assert result is None


# ============================================================================
# _generate_chart_url Tests
# ============================================================================


class TestGenerateChartUrl:
    """Test _generate_chart_url method."""

    @pytest.mark.asyncio
    async def test_generate_chart_url_short_config(self, chart_generator):
        """Test chart URL generation with short config (GET request)."""
        chart_config = {
            "type": "line",
            "data": {
                "labels": ["a", "b"],
                "datasets": [{"data": [1, 2]}],
            },
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await chart_generator._generate_chart_url(chart_config)

            assert result is not None

    @pytest.mark.asyncio
    async def test_generate_chart_url_long_config(self, chart_generator):
        """Test chart URL generation with long config (POST request)."""
        # Create a very long config that exceeds 2000 chars
        chart_config = {
            "type": "line",
            "data": {
                "labels": [f"label_{i}" for i in range(100)],  # Many labels
                "datasets": [
                    {
                        "data": list(range(100)),
                        "label": "A" * 500,  # Long label
                    }
                ],
            },
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "url": "https://quickchart.io/short/abc123"
            }
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await chart_generator._generate_chart_url(chart_config)

            assert result is not None

    @pytest.mark.asyncio
    async def test_generate_chart_url_api_error(self, chart_generator):
        """Test chart URL generation handles API errors."""
        chart_config = {"type": "line", "data": {"labels": [], "datasets": []}}

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 500  # Server error
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            # For long configs that trigger POST
            chart_config_long = {
                "type": "line",
                "data": {
                    "labels": [f"label_{i}" for i in range(100)],
                    "datasets": [{"data": list(range(100)), "label": "A" * 500}],
                },
            }

            result = await chart_generator._generate_chart_url(chart_config_long)

            assert result is None

    @pytest.mark.asyncio
    async def test_generate_chart_url_exception_handling(self, chart_generator):
        """Test chart URL generation handles exceptions for long configs."""
        # Use a long config that will trigger POST request
        chart_config = {
            "type": "line",
            "data": {
                "labels": [f"label_{i}" for i in range(100)],
                "datasets": [{"data": list(range(100)), "label": "A" * 500}],
            },
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                side_effect=Exception("Network error")
            )

            result = await chart_generator._generate_chart_url(chart_config)

            assert result is None


# ============================================================================
# Constants Tests
# ============================================================================


class TestConstants:
    """Test module constants."""

    def test_quickchart_api_endpoint(self):
        """Test QuickChart API endpoint is correct."""
        assert QUICKCHART_API == "https://quickchart.io/chart"


# ============================================================================
# Integration Tests
# ============================================================================


class TestChartGeneratorIntegration:
    """Integration tests for ChartGenerator."""

    @pytest.mark.asyncio
    async def test_generate_multiple_charts(
        self, chart_generator, profit_data, scan_history_data, level_distribution_data
    ):
        """Test generating multiple charts in sequence."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"url": "https://test.url"}
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            # Generate all chart types
            profit_chart = await chart_generator.generate_profit_chart(profit_data)
            scan_chart = await chart_generator.generate_scan_history_chart(
                scan_history_data
            )
            level_chart = await chart_generator.generate_level_distribution_chart(
                level_distribution_data
            )
            comparison_chart = await chart_generator.generate_profit_comparison_chart(
                ["boost", "standard"],
                [1.0, 2.0],
                [3.0, 4.0],
            )

            # All should succeed
            assert profit_chart is not None
            assert scan_chart is not None
            assert level_chart is not None
            assert comparison_chart is not None

    @pytest.mark.asyncio
    async def test_custom_size_affects_url(self, chart_generator_custom_size):
        """Test that custom dimensions affect generated URL."""
        chart_config = {"type": "line", "data": {"labels": ["a"], "datasets": []}}

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await chart_generator_custom_size._generate_chart_url(chart_config)

            assert result is not None
            assert "width=1200" in result
            assert "height=600" in result


# ============================================================================
# Edge Cases Tests
# ============================================================================


class TestEdgeCases:
    """Test edge cases for ChartGenerator."""

    @pytest.mark.asyncio
    async def test_profit_chart_with_negative_values(self, chart_generator):
        """Test profit chart handles negative values."""
        data = [
            {"date": "2024-01-01", "profit": -10.50},
            {"date": "2024-01-02", "profit": -5.25},
        ]

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await chart_generator.generate_profit_chart(data)
            # Should succeed even with negative values

    @pytest.mark.asyncio
    async def test_profit_chart_with_zero_values(self, chart_generator):
        """Test profit chart handles zero values."""
        data = [
            {"date": "2024-01-01", "profit": 0},
            {"date": "2024-01-02", "profit": 0},
        ]

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await chart_generator.generate_profit_chart(data)

    @pytest.mark.asyncio
    async def test_level_distribution_with_zero_counts(self, chart_generator):
        """Test level distribution handles zero counts."""
        data = {"boost": 0, "standard": 0}

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await chart_generator.generate_level_distribution_chart(data)

    @pytest.mark.asyncio
    async def test_special_characters_in_labels(self, chart_generator):
        """Test handling of special characters in labels."""
        data = [
            {"date": "2024/01/01", "profit": 10.0},
            {"date": "01-01-2024 & test", "profit": 20.0},
        ]

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await chart_generator.generate_profit_chart(data)
