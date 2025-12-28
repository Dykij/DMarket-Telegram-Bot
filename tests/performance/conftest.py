"""Pytest configuration for performance tests."""

import pytest

# Configure pytest-asyncio mode for this directory
pytest_plugins = ["pytest_asyncio"]


@pytest.fixture(scope="session")
def event_loop_policy():
    """Use default event loop policy."""
    import asyncio
    return asyncio.DefaultEventLoopPolicy()
