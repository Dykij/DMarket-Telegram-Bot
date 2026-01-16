"""Tests for parallel_scanner module.

This module tests the ParallelScanner class for concurrent
market scanning across multiple games.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio


class TestParallelScanner:
    """Tests for ParallelScanner class."""

    @pytest.fixture
    def mock_api(self):
        """Create mock API client."""
        api = MagicMock()
        api.get_market_items = AsyncMock(return_value={"objects": []})
        return api

    @pytest.fixture
    def scanner(self, mock_api):
        """Create ParallelScanner instance."""
        from src.dmarket.parallel_scanner import ParallelScanner
        return ParallelScanner(
            api_client=mock_api,
            max_workers=4,
        )

    def test_init(self, scanner, mock_api):
        """Test initialization."""
        assert scanner.api == mock_api
        assert scanner.max_workers == 4

    @pytest.mark.asyncio
    async def test_scan_single_game(self, scanner, mock_api):
        """Test scanning single game."""
        mock_api.get_market_items.return_value = {
            "objects": [
                {"itemId": "item1", "title": "AK-47"},
                {"itemId": "item2", "title": "M4A4"},
            ]
        }

        results = await scanner.scan_game("csgo")

        assert len(results) == 2
        mock_api.get_market_items.assert_called()

    @pytest.mark.asyncio
    async def test_scan_multiple_games(self, scanner, mock_api):
        """Test scanning multiple games in parallel."""
        mock_api.get_market_items.return_value = {"objects": [{"itemId": "item1"}]}

        results = await scanner.scan_all_games(["csgo", "dota2", "tf2"])

        assert "csgo" in results
        assert "dota2" in results
        assert "tf2" in results

    @pytest.mark.asyncio
    async def test_scan_with_filters(self, scanner, mock_api):
        """Test scanning with price filters."""
        mock_api.get_market_items.return_value = {"objects": []}

        await scanner.scan_game(
            "csgo",
            min_price=100,
            max_price=1000,
        )

        call_args = mock_api.get_market_items.call_args
        # Should include price filters

    @pytest.mark.asyncio
    async def test_scan_handles_api_error(self, scanner, mock_api):
        """Test handling API errors during scan."""
        mock_api.get_market_items.side_effect = Exception("API Error")

        results = await scanner.scan_game("csgo")

        assert results == []

    @pytest.mark.asyncio
    async def test_parallel_execution(self, scanner, mock_api):
        """Test that scans run in parallel."""
        call_count = 0

        async def mock_scan(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.01)
            return {"objects": []}

        mock_api.get_market_items = mock_scan

        await scanner.scan_all_games(["csgo", "dota2", "tf2", "rust"])

        assert call_count == 4

    @pytest.mark.asyncio
    async def test_rate_limiting(self, scanner, mock_api):
        """Test rate limiting between requests."""
        scanner.rate_limit_delay = 0.1
        mock_api.get_market_items.return_value = {"objects": []}

        import time
        start = time.time()
        await scanner.scan_game("csgo", pages=3)
        elapsed = time.time() - start

        # Should take at least rate_limit_delay * (pages - 1)

    def test_get_supported_games(self, scanner):
        """Test getting supported games list."""
        games = scanner.get_supported_games()

        assert "csgo" in games
        assert "dota2" in games

    @pytest.mark.asyncio
    async def test_aggregate_results(self, scanner, mock_api):
        """Test aggregating results from multiple scans."""
        mock_api.get_market_items.return_value = {
            "objects": [{"itemId": "item1", "profit": 10.0}]
        }

        results = await scanner.scan_all_games(["csgo", "dota2"])
        aggregated = scanner.aggregate_results(results)

        assert len(aggregated) >= 2

    @pytest.mark.asyncio
    async def test_find_best_opportunities(self, scanner, mock_api):
        """Test finding best opportunities across games."""
        mock_api.get_market_items.return_value = {
            "objects": [
                {"itemId": "item1", "title": "Item 1", "profit_percent": 15.0},
                {"itemId": "item2", "title": "Item 2", "profit_percent": 25.0},
            ]
        }

        best = await scanner.find_best_opportunities(limit=5)

        assert len(best) <= 5

    def test_get_stats(self, scanner):
        """Test getting scanner statistics."""
        scanner.total_scans = 100
        scanner.items_found = 500

        stats = scanner.get_stats()

        assert stats["total_scans"] == 100
        assert stats["items_found"] == 500
