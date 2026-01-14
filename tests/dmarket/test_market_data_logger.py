"""Tests for market_data_logger module.

This module tests the MarketDataLogger class for logging
market data for analysis and ML training.
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import tempfile
from pathlib import Path
from datetime import datetime


class TestMarketDataLogger:
    """Tests for MarketDataLogger class."""

    @pytest.fixture
    def logger(self, tmp_path):
        """Create MarketDataLogger instance."""
        from src.dmarket.market_data_logger import MarketDataLogger
        return MarketDataLogger(
            data_dir=str(tmp_path),
            max_file_size_mb=10,
        )

    def test_init(self, logger, tmp_path):
        """Test initialization."""
        assert logger.data_dir == Path(tmp_path)

    def test_log_price(self, logger):
        """Test logging price data."""
        logger.log_price(
            item_id="item123",
            item_title="AK-47 | Redline",
            price=25.50,
            game="csgo",
        )

        assert logger.entries_logged > 0

    def test_log_trade(self, logger):
        """Test logging trade data."""
        logger.log_trade(
            item_id="item123",
            item_title="AK-47 | Redline",
            buy_price=25.0,
            sell_price=30.0,
            profit=4.65,  # After fees
            game="csgo",
        )

        assert logger.trades_logged > 0

    def test_log_opportunity(self, logger):
        """Test logging arbitrage opportunity."""
        logger.log_opportunity(
            item_id="item123",
            item_title="AK-47 | Redline",
            dmarket_price=25.0,
            suggested_price=32.0,
            profit_percent=20.0,
            game="csgo",
        )

        assert logger.opportunities_logged > 0

    def test_batch_logging(self, logger):
        """Test batch logging multiple items."""
        items = [
            {"item_id": "item1", "price": 10.0, "title": "Item 1"},
            {"item_id": "item2", "price": 20.0, "title": "Item 2"},
            {"item_id": "item3", "price": 30.0, "title": "Item 3"},
        ]

        logger.log_batch(items, data_type="prices")

        assert logger.entries_logged >= 3

    def test_file_rotation(self, logger):
        """Test log file rotation."""
        # Fill up a file
        for i in range(1000):
            logger.log_price(
                item_id=f"item{i}",
                item_title=f"Item {i}",
                price=float(i),
                game="csgo",
            )

        # Should have rotated to new file if limit exceeded

    def test_export_to_csv(self, logger, tmp_path):
        """Test exporting to CSV."""
        logger.log_price("item1", "Item 1", 10.0, "csgo")
        logger.log_price("item2", "Item 2", 20.0, "csgo")

        csv_path = tmp_path / "export.csv"
        logger.export_to_csv(str(csv_path), data_type="prices")

        assert csv_path.exists()

    def test_export_to_json(self, logger, tmp_path):
        """Test exporting to JSON."""
        logger.log_price("item1", "Item 1", 10.0, "csgo")

        json_path = tmp_path / "export.json"
        logger.export_to_json(str(json_path), data_type="prices")

        assert json_path.exists()

    def test_get_price_history(self, logger):
        """Test getting price history for item."""
        logger.log_price("item1", "Item 1", 10.0, "csgo")
        logger.log_price("item1", "Item 1", 11.0, "csgo")
        logger.log_price("item1", "Item 1", 12.0, "csgo")

        history = logger.get_price_history("item1")

        assert len(history) == 3

    def test_get_stats(self, logger):
        """Test getting logger statistics."""
        logger.log_price("item1", "Item 1", 10.0, "csgo")
        logger.log_trade("item1", "Item 1", 10.0, 12.0, 1.5, "csgo")

        stats = logger.get_stats()

        assert "prices_logged" in stats
        assert "trades_logged" in stats

    def test_cleanup_old_data(self, logger):
        """Test cleaning up old data."""
        # Log some old data
        logger.log_price("old_item", "Old Item", 10.0, "csgo")

        # Cleanup data older than X days
        logger.cleanup(days=30)

        # Old data should be removed/archived

    def test_search_logs(self, logger):
        """Test searching logs."""
        logger.log_price("item1", "AK-47 | Redline", 25.0, "csgo")
        logger.log_price("item2", "M4A4 | Howl", 1000.0, "csgo")

        results = logger.search(keyword="AK-47")

        assert len(results) >= 1

    def test_aggregate_stats(self, logger):
        """Test aggregating statistics."""
        logger.log_price("item1", "Item 1", 10.0, "csgo")
        logger.log_price("item1", "Item 1", 12.0, "csgo")
        logger.log_price("item1", "Item 1", 11.0, "csgo")

        agg = logger.aggregate("item1")

        assert "avg_price" in agg
        assert "min_price" in agg
        assert "max_price" in agg

    @pytest.mark.asyncio
    async def test_async_logging(self, logger):
        """Test asynchronous logging."""
        await logger.log_price_async(
            item_id="item1",
            item_title="Item 1",
            price=10.0,
            game="csgo",
        )

        assert logger.entries_logged > 0
