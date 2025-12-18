"""Unit tests for pagination module.

This module contains tests for src/telegram_bot/pagination.py covering:
- PaginationManager initialization
- Adding items for users
- Page navigation
- Items per page settings

Target: 25+ tests to achieve 70%+ coverage
"""

from unittest.mock import MagicMock

import pytest

from src.telegram_bot.pagination import PaginationManager


# TestPaginationManagerInit


class TestPaginationManagerInit:
    """Tests for PaginationManager initialization."""

    def test_init_with_default_items_per_page(self):
        """Test initialization with default items per page."""
        # Act
        manager = PaginationManager()

        # Assert
        assert manager.default_items_per_page == 5

    def test_init_with_custom_items_per_page(self):
        """Test initialization with custom items per page."""
        # Act
        manager = PaginationManager(default_items_per_page=10)

        # Assert
        assert manager.default_items_per_page == 10

    def test_init_empty_state(self):
        """Test that initial state is empty."""
        # Act
        manager = PaginationManager()

        # Assert
        assert manager.items_by_user == {}
        assert manager.current_page_by_user == {}
        assert manager.mode_by_user == {}


# TestAddItems


class TestAddItems:
    """Tests for adding items to pagination."""

    def test_add_items_for_user(self):
        """Test adding items for a user."""
        # Arrange
        manager = PaginationManager()
        user_id = 12345
        items = [{"id": 1}, {"id": 2}, {"id": 3}]

        # Act
        manager.add_items_for_user(user_id, items)

        # Assert
        assert manager.items_by_user[user_id] == items
        assert manager.current_page_by_user[user_id] == 0

    def test_add_items_with_mode(self):
        """Test adding items with custom mode."""
        # Arrange
        manager = PaginationManager()
        user_id = 12345
        items = [{"id": 1}]

        # Act
        manager.add_items_for_user(user_id, items, mode="arbitrage")

        # Assert
        assert manager.mode_by_user[user_id] == "arbitrage"

    def test_add_items_alias(self):
        """Test add_items alias method."""
        # Arrange
        manager = PaginationManager()
        user_id = 12345
        items = [{"id": 1}]

        # Act
        manager.add_items(user_id, items)

        # Assert
        assert user_id in manager.items_by_user

    def test_set_items_alias(self):
        """Test set_items alias method."""
        # Arrange
        manager = PaginationManager()
        user_id = 12345
        items = [{"id": 1}]

        # Act
        manager.set_items(user_id, items)

        # Assert
        assert user_id in manager.items_by_user

    def test_add_items_clears_cache(self):
        """Test that adding items clears page cache."""
        # Arrange
        manager = PaginationManager()
        user_id = 12345
        manager.page_cache[user_id] = {0: ([], 0, 0)}

        # Act
        manager.add_items_for_user(user_id, [{"id": 1}])

        # Assert
        assert user_id not in manager.page_cache


# TestGetItemsPerPage


class TestGetItemsPerPage:
    """Tests for getting items per page."""

    def test_get_items_per_page_default(self):
        """Test getting default items per page."""
        # Arrange
        manager = PaginationManager(default_items_per_page=5)

        # Act
        items_per_page = manager.get_items_per_page(12345)

        # Assert
        assert items_per_page == 5

    def test_get_items_per_page_custom_setting(self):
        """Test getting custom items per page from user settings."""
        # Arrange
        manager = PaginationManager(default_items_per_page=5)
        user_id = 12345
        manager.user_settings[user_id] = {"items_per_page": 10}

        # Act
        items_per_page = manager.get_items_per_page(user_id)

        # Assert
        assert items_per_page == 10


# TestSetItemsPerPage


class TestSetItemsPerPage:
    """Tests for setting items per page."""

    def test_set_items_per_page(self):
        """Test setting items per page."""
        # Arrange
        manager = PaginationManager()
        user_id = 12345

        # Act
        manager.set_items_per_page(user_id, 10)

        # Assert
        assert manager.user_settings[user_id]["items_per_page"] == 10

    def test_set_items_per_page_limits_max(self):
        """Test that items per page is limited to max 20."""
        # Arrange
        manager = PaginationManager()
        user_id = 12345

        # Act
        manager.set_items_per_page(user_id, 50)

        # Assert
        assert manager.user_settings[user_id]["items_per_page"] == 20

    def test_set_items_per_page_limits_min(self):
        """Test that items per page is limited to min 1."""
        # Arrange
        manager = PaginationManager()
        user_id = 12345

        # Act
        manager.set_items_per_page(user_id, 0)

        # Assert
        assert manager.user_settings[user_id]["items_per_page"] == 1


# TestGetPage


class TestGetPage:
    """Tests for getting page."""

    def test_get_page_first_page(self):
        """Test getting first page."""
        # Arrange
        manager = PaginationManager(default_items_per_page=3)
        user_id = 12345
        items = [{"id": i} for i in range(10)]
        manager.add_items_for_user(user_id, items)

        # Act
        page_items, current_page, total_pages = manager.get_page(user_id)

        # Assert
        assert len(page_items) == 3
        assert current_page == 0
        assert total_pages == 4

    def test_get_page_no_items(self):
        """Test getting page when no items exist."""
        # Arrange
        manager = PaginationManager()
        user_id = 12345

        # Act
        page_items, current_page, total_pages = manager.get_page(user_id)

        # Assert
        assert page_items == []
        assert current_page == 0
        assert total_pages == 0

    def test_get_page_caching(self):
        """Test that get_page caches results."""
        # Arrange
        manager = PaginationManager(default_items_per_page=3)
        user_id = 12345
        items = [{"id": i} for i in range(10)]
        manager.add_items_for_user(user_id, items)

        # Act
        manager.get_page(user_id)

        # Assert - should be cached
        assert user_id in manager.page_cache


# TestPageNavigation


class TestPageNavigation:
    """Tests for page navigation."""

    def test_next_page(self):
        """Test navigating to next page."""
        # Arrange
        manager = PaginationManager(default_items_per_page=3)
        user_id = 12345
        items = list(range(20))
        manager.items_by_user[user_id] = items
        manager.current_page_by_user[user_id] = 0

        # Act
        page_items, current_page, total_pages = manager.next_page(user_id)

        # Assert
        assert current_page == 1

    def test_prev_page(self):
        """Test navigating to previous page."""
        # Arrange
        manager = PaginationManager(default_items_per_page=3)
        user_id = 12345
        items = list(range(20))
        manager.items_by_user[user_id] = items
        manager.current_page_by_user[user_id] = 2

        # Act
        page_items, current_page, total_pages = manager.prev_page(user_id)

        # Assert
        assert current_page == 1

    def test_prev_page_at_first_page(self):
        """Test prev_page at first page stays at first page."""
        # Arrange
        manager = PaginationManager()
        user_id = 12345
        manager.items_by_user[user_id] = list(range(20))
        manager.current_page_by_user[user_id] = 0

        # Act
        page_items, current_page, total_pages = manager.prev_page(user_id)

        # Assert
        assert current_page == 0

    def test_next_page_at_last_page(self):
        """Test next_page at last page stays at last page."""
        # Arrange
        manager = PaginationManager(default_items_per_page=5)
        user_id = 12345
        manager.items_by_user[user_id] = list(range(10))
        manager.current_page_by_user[user_id] = 1  # Last page

        # Act
        page_items, current_page, total_pages = manager.next_page(user_id)

        # Assert
        assert current_page == 1


# TestEdgeCases


class TestPaginationEdgeCases:
    """Tests for edge cases."""

    def test_next_page_no_items(self):
        """Test next_page when no items exist."""
        # Arrange
        manager = PaginationManager()
        user_id = 12345

        # Act
        result = manager.next_page(user_id)

        # Assert
        assert result == ([], 0, 0)

    def test_prev_page_no_items(self):
        """Test prev_page when no items exist."""
        # Arrange
        manager = PaginationManager()
        user_id = 12345

        # Act
        result = manager.prev_page(user_id)

        # Assert
        assert result == ([], 0, 0)

    def test_get_page_returns_correct_items(self):
        """Test get_page returns correct items for current page."""
        # Arrange
        manager = PaginationManager(default_items_per_page=3)
        user_id = 12345
        items = [{"id": i} for i in range(10)]
        manager.add_items_for_user(user_id, items)
        manager.current_page_by_user[user_id] = 1

        # Act
        page_items, current_page, total_pages = manager.get_page(user_id)

        # Assert
        assert len(page_items) == 3
        assert page_items[0]["id"] == 3  # First item on page 2 (index 1)

    def test_empty_items_list(self):
        """Test with empty items list."""
        # Arrange
        manager = PaginationManager()
        user_id = 12345
        manager.add_items_for_user(user_id, [])

        # Act
        result = manager.get_page(user_id)

        # Assert
        assert result == ([], 0, 0)
