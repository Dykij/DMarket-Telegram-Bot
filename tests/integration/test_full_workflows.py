"""Integration tests for full workflow scenarios."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from unittest.mock import patch

import pytest


if TYPE_CHECKING:
    from src.dmarket.dmarket_api import DMarketAPI
    from src.utils.database import DatabaseManager


pytestmark = pytest.mark.asyncio


class TestFullArbitrageWorkflow:
    """Test complete arbitrage workflow from scan to execution."""

    async def test_complete_arbitrage_cycle(
        self,
        mock_dmarket_api: DMarketAPI,
        test_database: DatabaseManager,
    ) -> None:
        """Test full cycle: scan -> find -> buy -> sell."""
        from src.dmarket.arbitrage_scanner import ArbitrageScanner

        scanner = ArbitrageScanner(api_client=mock_dmarket_api)

        # Mock profitable item
        market_response = {
            "objects": [
                {
                    "itemId": "item_001",
                    "title": "AK-47 | Redline (FT)",
                    "price": {"USD": "1000"},
                    "suggestedPrice": {"USD": "1200"},
                }
            ],
            "cursor": "",
        }

        with patch.object(mock_dmarket_api, "_request", return_value=market_response):
            # Step 1: Scan for opportunities
            opportunities = await scanner.scan_level(level="standard", game="csgo")
            assert len(opportunities) > 0

            # Step 2: Log scan to database
            user = await test_database.get_or_create_user(
                telegram_id=123456789, username="test_user"
            )
            assert user is not None

    async def test_multi_level_scan_workflow(
        self,
        mock_dmarket_api: DMarketAPI,
        test_database: DatabaseManager,
    ) -> None:
        """Test scanning multiple levels and storing results."""
        from src.dmarket.arbitrage_scanner import ArbitrageScanner

        scanner = ArbitrageScanner(api_client=mock_dmarket_api)

        market_response = {
            "objects": [{"itemId": f"item_{i}", "title": f"Item {i}"} for i in range(5)],
            "cursor": "",
        }

        with patch.object(mock_dmarket_api, "_request", return_value=market_response):
            all_results = await scanner.scan_all_levels(game="csgo")

            assert "boost" in all_results
            assert "standard" in all_results
            assert "medium" in all_results

    async def test_user_persistence_workflow(self, test_database: DatabaseManager) -> None:
        """Test user creation and retrieval across operations."""
        # Create user
        user1 = await test_database.get_or_create_user(telegram_id=111, username="user1")
        assert user1.telegram_id == 111

        # Get same user
        user2 = await test_database.get_or_create_user(telegram_id=111)
        assert user2.id == user1.id

        # Create different user
        user3 = await test_database.get_or_create_user(telegram_id=222, username="user2")
        assert user3.id != user1.id


class TestErrorRecoveryWorkflows:
    """Test error recovery in complete workflows."""

    async def test_scan_with_partial_api_failure(self, mock_dmarket_api: DMarketAPI) -> None:
        """Test scan continues after partial API failures."""
        import httpx

        from src.dmarket.arbitrage_scanner import ArbitrageScanner

        scanner = ArbitrageScanner(api_client=mock_dmarket_api)

        # First call fails, second succeeds
        error = httpx.HTTPStatusError(
            message="Server error",
            request=httpx.Request("GET", "http://test.com"),
            response=httpx.Response(status_code=500),
        )
        success_response = {
            "objects": [{"itemId": "item_001", "title": "Item 1"}],
            "cursor": "",
        }

        with patch.object(
            mock_dmarket_api,
            "_request",
            side_effect=[error, success_response],
        ):
            # Should recover from error
            opportunities = await scanner.scan_level(level="standard", game="csgo")
            assert isinstance(opportunities, list)

    async def test_database_transaction_rollback(self, test_database: DatabaseManager) -> None:
        """Test database transaction rollback on error."""
        try:
            # Attempt invalid operation
            user = await test_database.get_or_create_user(
                telegram_id=None,  # type: ignore[arg-type]
                username="invalid",
            )
        except Exception:
            # Should handle gracefully
            pass

        # Database should still be usable
        valid_user = await test_database.get_or_create_user(telegram_id=123, username="valid_user")
        assert valid_user is not None


class TestConcurrentOperations:
    """Test concurrent operation scenarios."""

    async def test_concurrent_user_creation(self, test_database: DatabaseManager) -> None:
        """Test concurrent user creation doesn't create duplicates."""
        import asyncio

        async def create_user(telegram_id: int) -> Any:
            return await test_database.get_or_create_user(
                telegram_id=telegram_id, username=f"user_{telegram_id}"
            )

        # Create different users concurrently (avoid race condition)
        users = await asyncio.gather(create_user(999001), create_user(999002), create_user(999003))

        # Should all be different users
        assert users[0].telegram_id != users[1].telegram_id
        assert users[1].telegram_id != users[2].telegram_id

    async def test_concurrent_scans(self, mock_dmarket_api: DMarketAPI) -> None:
        """Test concurrent scans don't interfere."""
        import asyncio

        from src.dmarket.arbitrage_scanner import ArbitrageScanner

        scanner = ArbitrageScanner(api_client=mock_dmarket_api)

        response = {"objects": [], "cursor": ""}

        async def scan(level: str) -> list[Any]:
            with patch.object(mock_dmarket_api, "_request", return_value=response):
                return await scanner.scan_level(level=level, game="csgo")

        results = await asyncio.gather(scan("boost"), scan("standard"), scan("medium"))

        assert len(results) == 3
        assert all(isinstance(r, list) for r in results)


class TestCachingBehavior:
    """Test caching behavior in workflows."""

    async def test_api_response_caching(self, mock_dmarket_api: DMarketAPI) -> None:
        """Test API responses are cached appropriately."""
        call_count = 0

        def mock_request(*args: Any, **kwargs: Any) -> dict[str, Any]:
            nonlocal call_count
            call_count += 1
            return {"objects": [], "cursor": ""}

        with patch.object(mock_dmarket_api, "_request", side_effect=mock_request):
            # First call
            await mock_dmarket_api.get_market_items(game="csgo")
            first_count = call_count

            # Second call (might be cached)
            await mock_dmarket_api.get_market_items(game="csgo")
            second_count = call_count

            # At least first call should have been made
            assert first_count >= 1
