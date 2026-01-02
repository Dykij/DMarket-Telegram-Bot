"""Tests for ScannerManager integration module."""

import asyncio
from unittest.mock import AsyncMock

import pytest

from src.dmarket.scanner_manager import ScannerManager


@pytest.fixture()
def mock_api_client():
    """Mock DMarket API client."""
    client = AsyncMock()
    client.get_market_items = AsyncMock(return_value={"objects": []})
    return client


@pytest.fixture()
def scanner_manager(mock_api_client):
    """Create ScannerManager instance."""
    return ScannerManager(
        api_client=mock_api_client,
        enable_adaptive=True,
        enable_parallel=True,
        enable_cleanup=True,
    )


class TestScannerManager:
    """Tests for ScannerManager."""

    def test_initialization_all_features(self, mock_api_client):
        """Test initialization with all features enabled."""
        manager = ScannerManager(
            api_client=mock_api_client,
            enable_adaptive=True,
            enable_parallel=True,
            enable_cleanup=True,
        )

        assert manager.adaptive is not None
        assert manager.parallel is not None
        assert manager.cleaner is not None
        assert manager.cleaner.dry_run is True  # Starts in dry-run

    def test_initialization_disabled_features(self, mock_api_client):
        """Test initialization with features disabled."""
        manager = ScannerManager(
            api_client=mock_api_client,
            enable_adaptive=False,
            enable_parallel=False,
            enable_cleanup=False,
        )

        assert manager.adaptive is None
        assert manager.parallel is None
        assert manager.cleaner is None

    @pytest.mark.asyncio()
    async def test_scan_single_game(self, scanner_manager, mocker):
        """Test scanning single game."""
        mock_scan = mocker.patch.object(
            scanner_manager.scanner,
            "scan_level",
            return_value=[
                {"item_name": "Item 1", "price": 10.0},
                {"item_name": "Item 2", "price": 20.0},
            ],
        )

        results = await scanner_manager.scan_single_game(game="csgo", level="high", max_items=10)

        assert len(results) == 2
        mock_scan.assert_called_once_with(level="high", game="csgo", max_results=10)

    @pytest.mark.asyncio()
    async def test_scan_single_game_updates_adaptive(self, scanner_manager, mocker):
        """Test that adaptive scanner receives snapshots."""
        mock_scan = mocker.patch.object(
            scanner_manager.scanner,
            "scan_level",
            return_value=[{"item_name": "Item 1", "price": 10.0}],
        )

        mock_add_snapshot = mocker.patch.object(scanner_manager.adaptive, "add_snapshot")

        await scanner_manager.scan_single_game("csgo", "high")

        # Verify snapshot was added
        mock_add_snapshot.assert_called_once()
        snapshot_items = mock_add_snapshot.call_args[0][0]
        assert len(snapshot_items) == 1
        assert snapshot_items[0]["title"] == "Item 1"

    @pytest.mark.asyncio()
    async def test_scan_multiple_games_parallel(self, scanner_manager, mocker):
        """Test parallel scanning of multiple games."""
        mock_parallel_scan = mocker.patch.object(
            scanner_manager.parallel,
            "scan_multiple_games",
            return_value={
                "csgo": [{"item": 1}],
                "dota2": [{"item": 2}],
            },
        )

        results = await scanner_manager.scan_multiple_games(games=["csgo", "dota2"], level="medium")

        assert "csgo" in results
        assert "dota2" in results
        mock_parallel_scan.assert_called_once()

    @pytest.mark.asyncio()
    async def test_scan_multiple_games_fallback(self, mock_api_client):
        """Test fallback to sequential when parallel disabled."""
        manager = ScannerManager(
            api_client=mock_api_client,
            enable_parallel=False,
        )

        # Mock sequential scanning
        manager.scan_single_game = AsyncMock(
            side_effect=[
                [{"item": "csgo"}],
                [{"item": "dota2"}],
            ]
        )

        results = await manager.scan_multiple_games(games=["csgo", "dota2"], level="medium")

        assert len(results) == 2
        assert manager.scan_single_game.call_count == 2

    @pytest.mark.asyncio()
    async def test_cleanup_targets(self, scanner_manager, mocker):
        """Test target cleanup."""
        mock_clean = mocker.patch.object(
            scanner_manager.cleaner,
            "clean_targets",
            return_value={
                "game": "csgo",
                "total_targets": 10,
                "cancelled": 3,
                "kept": 7,
            },
        )

        results = await scanner_manager.cleanup_targets(["csgo", "dota2"])

        assert results["total_cancelled"] == 6  # 3 * 2 games
        assert results["total_kept"] == 14  # 7 * 2 games
        assert mock_clean.call_count == 2

    @pytest.mark.asyncio()
    async def test_cleanup_targets_disabled(self, mock_api_client):
        """Test cleanup when cleaner is disabled."""
        manager = ScannerManager(api_client=mock_api_client, enable_cleanup=False)

        results = await manager.cleanup_targets(["csgo"])

        assert results["status"] == "disabled"

    def test_set_cleaner_dry_run(self, scanner_manager):
        """Test changing dry-run mode."""
        assert scanner_manager.cleaner.dry_run is True

        scanner_manager.set_cleaner_dry_run(False)
        assert scanner_manager.cleaner.dry_run is False

        scanner_manager.set_cleaner_dry_run(True)
        assert scanner_manager.cleaner.dry_run is True

    @pytest.mark.asyncio()
    async def test_stop(self, scanner_manager):
        """Test stopping scanner manager."""
        scanner_manager._running = True

        await scanner_manager.stop()

        assert scanner_manager._running is False

    @pytest.mark.asyncio()
    async def test_run_continuous_cycle(self, scanner_manager, mocker):
        """Test continuous scanning cycle (limited runs)."""
        # Mock scanning to return results
        mock_scan = mocker.patch.object(
            scanner_manager,
            "scan_multiple_games",
            return_value={"csgo": [{"item": 1}]},
        )

        # Mock adaptive scanner to allow scanning
        mocker.patch.object(scanner_manager.adaptive, "should_scan_now", return_value=True)
        mock_wait = mocker.patch.object(scanner_manager.adaptive, "wait_next_scan")

        # Limit to 2 cycles
        cycle_count = 0

        async def limited_wait():
            nonlocal cycle_count
            cycle_count += 1
            if cycle_count >= 2:
                await scanner_manager.stop()
            await asyncio.sleep(0.1)

        mock_wait.side_effect = limited_wait

        # Run continuous (should stop after 2 cycles)
        await scanner_manager.run_continuous(
            games=["csgo"],
            level="medium",
            enable_cleanup=False,
        )

        assert mock_scan.call_count == 2

    @pytest.mark.asyncio()
    async def test_scan_error_handling(self, scanner_manager, mocker):
        """Test error handling in scan_single_game."""
        mocker.patch.object(
            scanner_manager.scanner,
            "scan_level",
            side_effect=Exception("API Error"),
        )

        results = await scanner_manager.scan_single_game("csgo", "high")

        # Should return empty list on error
        assert results == []

    @pytest.mark.asyncio()
    async def test_cleanup_error_handling(self, scanner_manager, mocker):
        """Test error handling in cleanup_targets."""
        mocker.patch.object(
            scanner_manager.cleaner,
            "clean_targets",
            side_effect=Exception("Cleanup Error"),
        )

        results = await scanner_manager.cleanup_targets(["csgo"])

        # Should include error in results
        assert "csgo" in results["games"]
        assert "error" in results["games"]["csgo"]
