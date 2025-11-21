"""Comprehensive test configuration and fixtures for DMarket Bot tests.

This module provides shared test configuration, fixtures, and utilities
for testing the DMarket Telegram Bot.
"""

import asyncio
import os
import tempfile
from collections.abc import AsyncGenerator, Generator
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from src.dmarket.dmarket_api import DMarketAPI
from src.utils.config import BotConfig, Config, DatabaseConfig, DMarketConfig
from src.utils.database import DatabaseManager

# Test configuration
TEST_CONFIG = {
    "bot": {
        "token": "123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZ123456789",
        "username": "test_dmarket_bot",
    },
    "dmarket": {
        "api_url": "https://api.dmarket.com",
        "public_key": "test_public_key",
        "secret_key": "test_secret_key",
        "rate_limit": 30,
    },
    "database": {
        "url": "sqlite:///:memory:",
        "echo": False,
    },
    "security": {
        "allowed_users": ["123456789"],
        "admin_users": ["123456789"],
    },
    "debug": True,
    "testing": True,
}

# Mock API responses
MOCK_BALANCE_RESPONSE = {
    "usd": {"amount": 10000},  # $100.00 in cents
    "has_funds": True,
    "balance": 100.0,
    "available_balance": 100.0,
    "total_balance": 100.0,
    "error": False,
}

MOCK_MARKET_ITEMS_RESPONSE = {
    "items": [
        {
            "itemId": "test_item_1",
            "title": "AK-47 | Redline (Field-Tested)",
            "price": {"USD": "1250"},  # $12.50 in cents
            "gameId": "csgo",
            "classId": "310776341",
            "inMarket": True,
        },
        {
            "itemId": "test_item_2",
            "title": "AWP | Asiimov (Field-Tested)",
            "price": {"USD": "4500"},  # $45.00 in cents
            "gameId": "csgo",
            "classId": "310776342",
            "inMarket": True,
        },
    ],
    "totalItems": 2,
}

MOCK_ARBITRAGE_OPPORTUNITIES = [
    {
        "item_title": "AK-47 | Redline (Field-Tested)",
        "market_from": "Steam Market",
        "market_to": "DMarket",
        "buy_price": 12.50,
        "sell_price": 15.75,
        "profit_amount": 3.25,
        "profit_percentage": 26.0,
    },
    {
        "item_title": "AWP | Asiimov (Field-Tested)",
        "market_from": "DMarket",
        "market_to": "Skinport",
        "buy_price": 45.00,
        "sell_price": 54.99,
        "profit_amount": 9.99,
        "profit_percentage": 22.2,
    },
]


@pytest_asyncio.fixture
async def test_config() -> Config:
    """Create test configuration."""
    config = Config()

    # Set test values
    config.bot = BotConfig(
        token=TEST_CONFIG["bot"]["token"],
        username=TEST_CONFIG["bot"]["username"],
    )
    config.dmarket = DMarketConfig(
        api_url=TEST_CONFIG["dmarket"]["api_url"],
        public_key=TEST_CONFIG["dmarket"]["public_key"],
        secret_key=TEST_CONFIG["dmarket"]["secret_key"],
        rate_limit=TEST_CONFIG["dmarket"]["rate_limit"],
    )
    config.database = DatabaseConfig(
        url=TEST_CONFIG["database"]["url"],
        echo=TEST_CONFIG["database"]["echo"],
    )
    config.debug = True
    config.testing = True

    return config


@pytest_asyncio.fixture
async def test_database() -> AsyncGenerator[DatabaseManager, None]:
    """Create test database manager."""
    db_manager = DatabaseManager("sqlite:///:memory:")
    await db_manager.init_database()
    yield db_manager
    await db_manager.close()


@pytest_asyncio.fixture
async def mock_dmarket_api() -> DMarketAPI:
    """Create mock DMarket API client."""
    api = DMarketAPI(public_key="test_public_key", secret_key="test_secret_key")

    # Mock the HTTP client
    with patch.object(api, "_request") as mock_request:
        # Configure mock responses
        async def side_effect(method: str, path: str, **kwargs):
            if "balance" in path:
                return MOCK_BALANCE_RESPONSE
            if "items" in path:
                return MOCK_MARKET_ITEMS_RESPONSE
            return {"success": True}

        mock_request.side_effect = side_effect
        yield api


@pytest_asyncio.fixture
async def test_bot(
    test_config: Config,
    mock_dmarket_api: DMarketAPI,
    test_database: DatabaseManager,
) -> AsyncGenerator[MagicMock, None]:
    """Create test bot instance."""
    bot = MagicMock()
    bot.config = test_config
    bot.dmarket_api = mock_dmarket_api
    bot.database = test_database
    bot.bot_data = {
        "config": test_config,
        "dmarket_api": mock_dmarket_api,
        "database": test_database,
    }

    # Mock initialize and stop methods
    bot.initialize = AsyncMock()
    bot.stop = AsyncMock()
    bot.start = AsyncMock()
    bot.shutdown = AsyncMock()

    yield bot


@pytest.fixture()
def temp_config_file() -> Generator[str, None, None]:
    """Create temporary config file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        import yaml

        yaml.dump(TEST_CONFIG, f)
        temp_path = f.name

    yield temp_path

    # Clean up
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture()
def mock_telegram_update():
    """Create mock Telegram update object."""
    update = MagicMock()
    update.effective_user.id = 123456789
    update.effective_user.username = "testuser"
    update.effective_user.first_name = "Test"
    update.effective_user.last_name = "User"
    update.effective_chat.id = 123456789
    update.effective_chat.type = "private"
    update.message.text = "/start"
    update.message.message_id = 1
    return update


@pytest.fixture()
def mock_telegram_context():
    """Create mock Telegram context object."""
    context = MagicMock()
    context.bot.username = "test_dmarket_bot"
    context.application.bot.username = "test_dmarket_bot"
    return context


class TestUtils:
    """Utility functions for tests."""

    @staticmethod
    def create_mock_market_item(
        item_id: str = "test_item",
        title: str = "Test Item",
        price_usd: float = 10.0,
        game_id: str = "csgo",
    ) -> dict[str, Any]:
        """Create mock market item data."""
        return {
            "itemId": item_id,
            "title": title,
            "price": {"USD": str(int(price_usd * 100))},
            "gameId": game_id,
            "classId": "123456",
            "inMarket": True,
        }

    @staticmethod
    def create_mock_price_history(
        days: int = 7,
        base_price: float = 10.0,
        volatility: float = 0.1,
    ) -> list[dict[str, Any]]:
        """Create mock price history data."""
        import random
        from datetime import datetime, timedelta

        history = []
        for i in range(days):
            date = datetime.now() - timedelta(days=days - i - 1)
            price = base_price * (1 + random.uniform(-volatility, volatility))
            history.append({"date": date.isoformat(), "price": round(price, 2)})

        return history

    @staticmethod
    async def wait_for_condition(
        condition_func,
        timeout: float = 5.0,
        interval: float = 0.1,
    ) -> bool:
        """Wait for a condition to become true."""
        start_time = asyncio.get_event_loop().time()

        while asyncio.get_event_loop().time() - start_time < timeout:
            if await condition_func():
                return True
            await asyncio.sleep(interval)

        return False


# Test data generators
def generate_test_user_data(user_id: int = 123456789) -> dict[str, Any]:
    """Generate test user data."""
    return {
        "telegram_id": user_id,
        "username": f"testuser{user_id}",
        "first_name": "Test",
        "last_name": "User",
        "language_code": "en",
    }


def generate_test_market_data(count: int = 10) -> list[dict[str, Any]]:
    """Generate test market data."""
    items = []
    for i in range(count):
        items.append(
            TestUtils.create_mock_market_item(
                item_id=f"test_item_{i}",
                title=f"Test Item {i}",
                price_usd=10.0 + i * 5.0,
            ),
        )
    return items


# Custom assertions
def assert_api_response_valid(response: dict[str, Any]) -> None:
    """Assert that API response is valid."""
    assert isinstance(response, dict)
    if "error" in response:
        assert response["error"] is False, f"API error: {response.get('error_message', 'Unknown')}"


def assert_balance_response_valid(balance: dict[str, Any]) -> None:
    """Assert that balance response is valid."""
    assert_api_response_valid(balance)
    assert "balance" in balance
    assert "has_funds" in balance
    assert isinstance(balance["balance"], int | float)
    assert isinstance(balance["has_funds"], bool)


# Pytest configuration
pytest_plugins = [
    "pytest_asyncio",
    "pytest_mock",
    "pytest_cov",
]
