"""Tests for refactored ArbitrageScanner (Phase 2)."""

from unittest.mock import AsyncMock, patch

import pytest

from src.dmarket.arbitrage_scanner_refactored import ArbitrageScannerRefactored


@pytest.fixture()
def mock_api_client():
    """Mock API client."""
    client = AsyncMock()
    client.get_market_items = AsyncMock(return_value={"objects": []})
    return client


@pytest.fixture()
def scanner(mock_api_client):
    """Create scanner instance."""
    return ArbitrageScannerRefactored(api_client=mock_api_client)


class TestArbitrageScannerRefactored:
    """Tests for refactored scanner."""

    @pytest.mark.asyncio()
    async def test_scan_game_returns_cached_results(self, scanner):
        """Test that cached results are returned when available."""
        # Arrange
        cached_data = [{"name": "Item1", "profit": 10.0}]
        cache_key = ("csgo", "medium", 0, float("inf"))
        scanner._save_to_cache(cache_key, cached_data)

        # Act
        results = await scanner.scan_game("csgo", "medium", 5)

        # Assert
        assert results == cached_data[:5]

    @pytest.mark.asyncio()
    async def test_scan_game_handles_errors_gracefully(self, scanner):
        """Test error handling in scan_game."""
        # Arrange
        with patch.object(
            scanner, "_find_arbitrage_items", side_effect=Exception("API Error")
        ):
            # Act
            results = await scanner.scan_game("csgo", "medium")

            # Assert
            assert results == []

    def test_get_profit_range_returns_correct_values(self, scanner):
        """Test profit range calculation for different modes."""
        # Test medium mode
        min_profit, max_profit = scanner._get_profit_range("medium")
        assert min_profit == 5.0
        assert max_profit == 20.0

        # Test high mode
        min_profit, max_profit = scanner._get_profit_range("high")
        assert min_profit == 20.0
        assert max_profit == 100.0

        # Test low mode
        min_profit, max_profit = scanner._get_profit_range("low")
        assert min_profit == 1.0
        assert max_profit == 5.0

    def test_get_price_range_uses_provided_values(self, scanner):
        """Test that provided price range is used."""
        price_from, price_to = scanner._get_price_range("medium", 10.0, 50.0)
        assert price_from == 10.0
        assert price_to == 50.0

    def test_get_price_range_calculates_for_medium_mode(self, scanner):
        """Test price range calculation for medium mode."""
        price_from, price_to = scanner._get_price_range("medium", None, None)
        assert price_from == 20.0
        assert price_to == 100.0

    def test_standardize_single_item_converts_tuple(self, scanner):
        """Test tuple item standardization."""
        # Arrange
        item_tuple = ("AK-47", 10.0, 15.0, 5.0, 50.0)

        # Act
        result = scanner._standardize_single_item(item_tuple, "csgo")

        # Assert
        assert result["name"] == "AK-47"
        assert result["buy_price"] == 10.0
        assert result["sell_price"] == 15.0
        assert result["profit"] == 5.0
        assert result["game"] == "csgo"

    def test_standardize_single_item_keeps_dict(self, scanner):
        """Test that dict items are kept as-is."""
        # Arrange
        item_dict = {"name": "AK-47", "profit": 10.0}

        # Act
        result = scanner._standardize_single_item(item_dict, "csgo")

        # Assert
        assert result == item_dict

    def test_is_valid_profit_with_numeric_profit(self, scanner):
        """Test profit validation with numeric values."""
        # Valid profit
        item = {"profit": 10.0}
        assert scanner._is_valid_profit(item, 5.0, 20.0) is True

        # Below minimum
        assert scanner._is_valid_profit(item, 15.0, 25.0) is False

        # Above maximum
        assert scanner._is_valid_profit(item, 1.0, 5.0) is False

    def test_is_valid_profit_with_string_profit(self, scanner):
        """Test profit validation with string values."""
        # Valid string profit
        item = {"profit": "$10.00"}
        assert scanner._is_valid_profit(item, 5.0, 20.0) is True

        # Invalid string
        item_invalid = {"profit": "invalid"}
        assert scanner._is_valid_profit(item_invalid, 5.0, 20.0) is False

    @pytest.mark.asyncio()
    async def test_apply_filters_without_liquidity_filter(self, scanner):
        """Test filtering without liquidity analyzer."""
        # Arrange
        scanner.enable_liquidity_filter = False
        items = [{"name": f"Item{i}", "profit": i} for i in range(10)]

        # Act
        results = await scanner._apply_filters(items, "csgo", 5)

        # Assert
        assert len(results) == 5

    @pytest.mark.asyncio()
    async def test_apply_filters_with_liquidity_filter(self, scanner):
        """Test filtering with liquidity analyzer."""
        # Arrange
        scanner.enable_liquidity_filter = True
        scanner.liquidity_analyzer = AsyncMock()
        scanner.liquidity_analyzer.filter_liquid_items = AsyncMock(
            return_value=[{"name": "Item1", "profit": 10.0}]
        )
        items = [{"name": f"Item{i}", "profit": i} for i in range(10)]

        # Act
        results = await scanner._apply_filters(items, "csgo", 5)

        # Assert
        assert len(results) == 1
        scanner.liquidity_analyzer.filter_liquid_items.assert_called_once()

    def test_find_items_builtin_calls_correct_function(self, scanner):
        """Test that built-in functions are called correctly."""
        with patch(
            "src.dmarket.arbitrage_scanner_refactored.arbitrage_mid"
        ) as mock_mid:
            mock_mid.return_value = [{"name": "Item1"}]

            results = scanner._find_items_builtin("csgo", "medium")

            mock_mid.assert_called_once_with("csgo")
            assert results == [{"name": "Item1"}]

    def test_cache_ttl_property(self, scanner):
        """Test cache TTL property getter and setter."""
        # Default value
        assert scanner.cache_ttl == 300

        # Set new value
        scanner.cache_ttl = 600
        assert scanner.cache_ttl == 600
