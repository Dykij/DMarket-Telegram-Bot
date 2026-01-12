"""Pytest configuration for performance tests.

All tests in this directory are automatically marked as:
- slow: excluded from quick test runs
- performance: for filtering
"""

import pytest


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Mark all tests in this directory as slow and performance."""
    for item in items:
        item.add_marker(pytest.mark.slow)
        item.add_marker(pytest.mark.performance)
        # Увеличенный таймаут для performance тестов
        if not any(mark.name == "timeout" for mark in item.iter_markers()):
            item.add_marker(pytest.mark.timeout(120))


@pytest.fixture(scope="session")
def event_loop_policy():
    """Use default event loop policy."""
    import asyncio

    return asyncio.DefaultEventLoopPolicy()
