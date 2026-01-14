"""Tests for blacklist_manager module.

This module tests the BlacklistManager class for filtering
problematic sellers and items.
"""

import pytest
from unittest.mock import MagicMock, patch
import json
import tempfile
from pathlib import Path


class TestBlacklistManager:
    """Tests for BlacklistManager class."""

    @pytest.fixture
    def manager(self, tmp_path):
        """Create BlacklistManager instance."""
        from src.dmarket.blacklist_manager import BlacklistManager
        blacklist_file = tmp_path / "blacklist.json"
        return BlacklistManager(
            config={},
            blacklist_file=str(blacklist_file),
        )

    def test_init(self, manager):
        """Test initialization."""
        assert manager is not None
        assert isinstance(manager.blacklisted_sellers, set)
        assert isinstance(manager.forbidden_keywords, list)
        assert isinstance(manager.blacklisted_items, list)

    def test_add_seller_to_blacklist(self, manager):
        """Test adding seller to blacklist."""
        seller_id = "seller123"

        manager.blacklist_seller(seller_id)

        assert seller_id in manager.blacklisted_sellers

    def test_remove_seller_from_blacklist(self, manager):
        """Test removing seller from blacklist."""
        seller_id = "seller123"
        manager.blacklisted_sellers.add(seller_id)

        manager.unblacklist_seller(seller_id)

        assert seller_id not in manager.blacklisted_sellers

    def test_is_seller_blacklisted(self, manager):
        """Test checking if seller is blacklisted."""
        manager.blacklisted_sellers.add("bad_seller")

        assert manager.is_seller_blacklisted("bad_seller") is True
        assert manager.is_seller_blacklisted("good_seller") is False

    def test_add_forbidden_keyword(self, manager):
        """Test adding forbidden keyword."""
        manager.add_forbidden_keyword("scam")

        assert "scam" in manager.forbidden_keywords

    def test_remove_forbidden_keyword(self, manager):
        """Test removing forbidden keyword."""
        manager.forbidden_keywords.append("test")

        manager.remove_forbidden_keyword("test")

        assert "test" not in manager.forbidden_keywords

    def test_item_contains_forbidden_keyword(self, manager):
        """Test detecting forbidden keywords in item names."""
        manager.forbidden_keywords = ["souvenir", "stattrak fake"]

        assert manager.contains_forbidden_keyword("AWP | Souvenir Dragon Lore") is True
        assert manager.contains_forbidden_keyword("AWP | Dragon Lore") is False
        assert manager.contains_forbidden_keyword("AK-47 | StatTrak Fake Redline") is True

    def test_add_item_to_blacklist(self, manager):
        """Test adding item to blacklist."""
        manager.blacklist_item("Item XYZ")

        assert "Item XYZ" in manager.blacklisted_items

    def test_is_item_blacklisted(self, manager):
        """Test checking if item is blacklisted."""
        manager.blacklisted_items.append("Bad Item")

        assert manager.is_item_blacklisted("Bad Item") is True
        assert manager.is_item_blacklisted("Good Item") is False

    def test_check_item_valid(self, manager):
        """Test checking if item is valid (not blacklisted)."""
        item = {
            "title": "AK-47 | Redline",
            "sellerId": "good_seller",
        }

        is_valid, reason = manager.check_item(item)

        assert is_valid is True

    def test_check_item_blacklisted_seller(self, manager):
        """Test checking item with blacklisted seller."""
        manager.blacklisted_sellers.add("bad_seller")
        item = {
            "title": "AK-47 | Redline",
            "sellerId": "bad_seller",
        }

        is_valid, reason = manager.check_item(item)

        assert is_valid is False
        assert "seller" in reason.lower()

    def test_check_item_forbidden_keyword(self, manager):
        """Test checking item with forbidden keyword."""
        manager.forbidden_keywords = ["souvenir"]
        item = {
            "title": "AWP | Souvenir Dragon Lore",
            "sellerId": "seller123",
        }

        is_valid, reason = manager.check_item(item)

        assert is_valid is False
        assert "keyword" in reason.lower()

    def test_auto_blacklist_on_failure(self, manager):
        """Test automatic blacklisting after repeated failures."""
        seller_id = "failing_seller"
        manager._failure_threshold = 3

        # Simulate failures
        for _ in range(3):
            manager.record_failure(seller_id)

        assert manager.is_seller_blacklisted(seller_id) is True

    def test_failure_counter_increments(self, manager):
        """Test failure counter incrementing."""
        seller_id = "seller123"

        manager.record_failure(seller_id)
        assert manager._failure_counter[seller_id] == 1

        manager.record_failure(seller_id)
        assert manager._failure_counter[seller_id] == 2

    def test_save_blacklist(self, manager, tmp_path):
        """Test saving blacklist to file."""
        manager.blacklisted_sellers.add("seller1")
        manager.blacklisted_sellers.add("seller2")

        manager.save()

        # Verify file was created
        assert manager.blacklist_file.exists()

    def test_load_blacklist(self, tmp_path):
        """Test loading blacklist from file."""
        from src.dmarket.blacklist_manager import BlacklistManager

        # Create test file
        blacklist_file = tmp_path / "blacklist.json"
        data = {
            "sellers": ["seller1", "seller2"],
            "keywords": ["scam"],
            "items": ["Bad Item"],
        }
        blacklist_file.write_text(json.dumps(data))

        manager = BlacklistManager(blacklist_file=str(blacklist_file))

        # Verify loaded data

    def test_get_stats(self, manager):
        """Test getting blacklist statistics."""
        manager.blacklisted_sellers = {"s1", "s2", "s3"}
        manager.forbidden_keywords = ["k1", "k2"]
        manager.blacklisted_items = ["i1"]

        stats = manager.get_stats()

        assert stats["sellers"] == 3
        assert stats["keywords"] == 2
        assert stats["items"] == 1

    def test_clear_all(self, manager):
        """Test clearing all blacklists."""
        manager.blacklisted_sellers = {"s1", "s2"}
        manager.forbidden_keywords = ["k1"]
        manager.blacklisted_items = ["i1"]

        manager.clear_all()

        assert len(manager.blacklisted_sellers) == 0
        assert len(manager.forbidden_keywords) == 0
        assert len(manager.blacklisted_items) == 0

    def test_export_blacklist(self, manager):
        """Test exporting blacklist data."""
        manager.blacklisted_sellers = {"seller1"}
        manager.forbidden_keywords = ["scam"]

        data = manager.export()

        assert "sellers" in data
        assert "keywords" in data
        assert "seller1" in data["sellers"]

    def test_import_blacklist(self, manager):
        """Test importing blacklist data."""
        data = {
            "sellers": ["new_seller"],
            "keywords": ["new_keyword"],
        }

        manager.import_data(data)

        assert "new_seller" in manager.blacklisted_sellers
        assert "new_keyword" in manager.forbidden_keywords
