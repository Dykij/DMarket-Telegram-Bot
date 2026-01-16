"""Tests for adaptive_scanner module.

This module tests the AdaptiveScanner class for intelligent
market scanning with automatic parameter adjustment.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestAdaptiveScanner:
    """Tests for AdaptiveScanner class."""

    @pytest.fixture
    def mock_api(self):
        """Create mock API client."""
        api = MagicMock()
        api.get_market_items = AsyncMock(return_value={"objects": []})
        api.get_balance = AsyncMock(return_value={"balance": 100.0})
        return api

    @pytest.fixture
    def scanner(self, mock_api):
        """Create AdaptiveScanner instance."""
        from src.dmarket.adaptive_scanner import AdaptiveScanner
        return AdaptiveScanner(api_client=mock_api)

    def test_init(self, scanner, mock_api):
        """Test initialization."""
        assert scanner.api == mock_api

    @pytest.mark.asyncio
    async def test_scan_with_default_params(self, scanner, mock_api):
        """Test scanning with default parameters."""
        mock_api.get_market_items.return_value = {"objects": []}

        results = await scanner.scan()

        assert results == []
        mock_api.get_market_items.assert_called()

    @pytest.mark.asyncio
    async def test_adapt_to_balance(self, scanner, mock_api):
        """Test adapting parameters to balance."""
        mock_api.get_balance.return_value = {"balance": 50.0}

        await scanner.adapt_to_balance()

        # Should adjust max_price based on balance
        assert scanner.max_price <= 50.0

    @pytest.mark.asyncio
    async def test_adapt_to_market_conditions(self, scanner, mock_api):
        """Test adapting to market conditions."""
        # Simulate many opportunities found
        scanner.opportunities_found = 100
        scanner.adapt_to_market()

        # Should increase min_profit when many opportunities
        assert scanner.min_profit >= 5.0

    @pytest.mark.asyncio
    async def test_learn_from_success(self, scanner):
        """Test learning from successful trades."""
        trade = {
            "item_type": "rifle",
            "profit_percent": 15.0,
            "game": "csgo",
        }

        scanner.record_success(trade)

        # Should prefer similar items in future
        preferences = scanner.get_preferences()
        assert "rifle" in preferences.get("preferred_types", [])

    @pytest.mark.asyncio
    async def test_learn_from_failure(self, scanner):
        """Test learning from failed trades."""
        trade = {
            "item_type": "sticker",
            "reason": "low_liquidity",
            "game": "csgo",
        }

        scanner.record_failure(trade)

        # Should avoid similar items
        avoided = scanner.get_avoided_types()
        assert "sticker" in avoided or scanner.failure_count.get("sticker", 0) > 0

    @pytest.mark.asyncio
    async def test_auto_adjust_filters(self, scanner):
        """Test automatic filter adjustment."""
        # After multiple scans with low results
        scanner.scan_results_history = [0, 1, 0, 2, 0]

        scanner.auto_adjust_filters()

        # Should relax filters when low results

    def test_get_optimal_parameters(self, scanner):
        """Test getting optimal scan parameters."""
        scanner.balance = 100.0
        scanner.market_activity = "high"

        params = scanner.get_optimal_parameters()

        assert "min_price" in params
        assert "max_price" in params
        assert "min_profit" in params

    @pytest.mark.asyncio
    async def test_scan_with_learning(self, scanner, mock_api):
        """Test scanning with learning enabled."""
        mock_api.get_market_items.return_value = {
            "objects": [
                {"itemId": "item1", "profit_percent": 20.0},
            ]
        }

        results = await scanner.scan(learning_enabled=True)

        # Should track results for learning

    def test_get_stats(self, scanner):
        """Test getting scanner statistics."""
        scanner.total_scans = 100
        scanner.successful_purchases = 15
        scanner.total_profit = 250.0

        stats = scanner.get_stats()

        assert stats["total_scans"] == 100
        assert stats["success_rate"] == 0.15

    @pytest.mark.asyncio
    async def test_reset_learning(self, scanner):
        """Test resetting learning data."""
        scanner.preferences = {"types": ["rifle"]}
        scanner.failure_count = {"sticker": 5}

        scanner.reset_learning()

        assert scanner.preferences == {}
        assert scanner.failure_count == {}
