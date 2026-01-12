"""Pytest configuration for comprehensive tests.

All tests in this directory are automatically marked as:
- slow: excluded from quick test runs
- comprehensive: for filtering

These tests are heavy and should not run during regular development.
Use `pytest -m comprehensive` to run only these tests.
"""

import pytest


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Mark all tests in this directory as slow and comprehensive."""
    for item in items:
        item.add_marker(pytest.mark.slow)
        item.add_marker(pytest.mark.comprehensive)
        # Увеличенный таймаут для comprehensive тестов
        if not any(mark.name == "timeout" for mark in item.iter_markers()):
            item.add_marker(pytest.mark.timeout(120))
