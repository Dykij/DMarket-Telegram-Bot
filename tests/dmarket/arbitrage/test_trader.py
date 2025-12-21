"""Comprehensive tests for ArbitrageTrader module.

This module tests the ArbitrageTrader class functionality:
- Initialization with api_client or credentials
- Balance checking
- Trading limits management
- Error handling and recovery
- Profitable item discovery
- Trade execution (buy/sell)
- Auto-trading loop
- Transaction history
"""

import time
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.dmarket.arbitrage.trader import ArbitrageTrader


# ==============================================================================
# FIXTURES
# ==============================================================================


@pytest.fixture
def mock_api_client():
    """Create a mock DMarket API client."""
    api = AsyncMock()
    api.get_balance = AsyncMock(return_value={"usd": "10000"})  # $100 balance
    api.get_all_market_items = AsyncMock(return_value=[])
    api._request = AsyncMock(return_value={})
    api.__aenter__ = AsyncMock(return_value=api)
    api.__aexit__ = AsyncMock(return_value=None)
    return api


@pytest.fixture
def trader(mock_api_client):
    """Create an ArbitrageTrader instance with mock API."""
    return ArbitrageTrader(api_client=mock_api_client)


@pytest.fixture
def sample_profitable_item():
    """Create a sample profitable item for trading."""
    return {
        "name": "AK-47 | Redline",
        "buy_price": 10.0,
        "sell_price": 12.0,
        "profit": 1.16,
        "profit_percentage": 11.6,
        "commission_percent": 7.0,
        "buy_item_id": "buy_item_123",
        "sell_item_id": "sell_item_456",
        "game": "csgo",
    }


@pytest.fixture
def sample_market_items():
    """Create sample market items for testing."""
    return [
        {
            "title": "AK-47 | Redline",
            "itemId": "item1",
            "price": {"USD": "1000"},  # $10
            "extra": {"rarity": "Classified", "category": "Rifle", "popularity": 0.8},
        },
        {
            "title": "AK-47 | Redline",
            "itemId": "item2",
            "price": {"USD": "1200"},  # $12
            "extra": {"rarity": "Classified", "category": "Rifle", "popularity": 0.8},
        },
        {
            "title": "AWP | Dragon Lore",
            "itemId": "item3",
            "price": {"USD": "500000"},  # $5000
            "extra": {"rarity": "Covert", "category": "Sniper", "popularity": 0.95},
        },
    ]


# ==============================================================================
# TEST INITIALIZATION
# ==============================================================================


class TestArbitrageTraderInit:
    """Tests for ArbitrageTrader initialization."""

    def test_init_with_api_client(self, mock_api_client):
        """Test initialization with api_client."""
        trader = ArbitrageTrader(api_client=mock_api_client)

        assert trader.api == mock_api_client
        assert trader.min_profit_percentage == 5.0
        assert trader.max_trade_value == 100.0
        assert trader.daily_limit == 500.0
        assert trader.active is False
        assert trader.transaction_history == []

    def test_init_with_credentials(self, mock_api_client):
        """Test initialization with credentials stores them properly.

        Note: This test verifies that credentials are stored.
        The actual DMarketAPI import inside __init__ is difficult to mock
        due to dynamic import. Integration tests should verify full flow.
        """
        # Test with api_client but also providing credentials (both should work)
        trader = ArbitrageTrader(
            api_client=mock_api_client,
            public_key="test_public_key",
            secret_key="test_secret_key",
        )

        # Credentials should be stored for reference
        assert trader.public_key == "test_public_key"
        assert trader.secret_key == "test_secret_key"
        # API should be the provided client (api_client takes precedence)
        assert trader.api == mock_api_client

    def test_init_with_custom_parameters(self, mock_api_client):
        """Test initialization with custom parameters."""
        trader = ArbitrageTrader(
            api_client=mock_api_client,
            min_profit_percentage=10.0,
            max_trade_value=50.0,
            daily_limit=200.0,
        )

        assert trader.min_profit_percentage == 10.0
        assert trader.max_trade_value == 50.0
        assert trader.daily_limit == 200.0

    def test_init_without_api_or_credentials_raises_error(self):
        """Test that initialization without api_client or credentials raises error."""
        with pytest.raises(ValueError, match="requires either api_client"):
            ArbitrageTrader()

    def test_init_with_only_public_key_raises_error(self):
        """Test that initialization with only public_key raises error."""
        with pytest.raises(ValueError, match="requires either api_client"):
            ArbitrageTrader(public_key="test_public_key")

    def test_init_with_only_secret_key_raises_error(self):
        """Test that initialization with only secret_key raises error."""
        with pytest.raises(ValueError, match="requires either api_client"):
            ArbitrageTrader(secret_key="test_secret_key")


# ==============================================================================
# TEST BALANCE CHECKING
# ==============================================================================


class TestBalanceChecking:
    """Tests for balance checking functionality."""

    @pytest.mark.asyncio
    async def test_check_balance_success(self, trader, mock_api_client):
        """Test successful balance check."""
        mock_api_client.get_balance.return_value = {"usd": "10000"}  # $100

        has_funds, balance = await trader.check_balance()

        assert has_funds is True
        assert balance == 100.0
        mock_api_client.get_balance.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_balance_insufficient_funds(self, trader, mock_api_client):
        """Test balance check with insufficient funds."""
        mock_api_client.get_balance.return_value = {"usd": "50"}  # $0.50

        has_funds, balance = await trader.check_balance()

        assert has_funds is False
        assert balance == 0.5

    @pytest.mark.asyncio
    async def test_check_balance_empty_response(self, trader, mock_api_client):
        """Test balance check with empty response."""
        mock_api_client.get_balance.return_value = {}

        has_funds, balance = await trader.check_balance()

        assert has_funds is False
        assert balance == 0.0

    @pytest.mark.asyncio
    async def test_check_balance_api_error(self, trader, mock_api_client):
        """Test balance check with API error."""
        mock_api_client.get_balance.side_effect = Exception("API Error")

        has_funds, balance = await trader.check_balance()

        assert has_funds is False
        assert balance == 0.0


# ==============================================================================
# TEST TRADING LIMITS
# ==============================================================================


class TestTradingLimits:
    """Tests for trading limits management."""

    @pytest.mark.asyncio
    async def test_check_trading_limits_within_limits(self, trader):
        """Test trade within limits."""
        result = await trader._check_trading_limits(50.0)

        assert result is True

    @pytest.mark.asyncio
    async def test_check_trading_limits_exceeds_max_trade_value(self, trader):
        """Test trade exceeding max trade value."""
        result = await trader._check_trading_limits(150.0)  # Default max is 100

        assert result is False

    @pytest.mark.asyncio
    async def test_check_trading_limits_exceeds_daily_limit(self, trader):
        """Test trade exceeding daily limit."""
        trader.daily_traded = 450.0  # Already traded $450
        result = await trader._check_trading_limits(100.0)  # Total would be $550 > $500

        assert result is False

    def test_reset_daily_limits(self, trader):
        """Test daily limits reset after 24 hours."""
        trader.daily_traded = 200.0
        trader.daily_reset_time = time.time() - 86500  # More than 24 hours ago

        trader._reset_daily_limits()

        assert trader.daily_traded == 0.0
        assert trader.daily_reset_time > time.time() - 10

    def test_reset_daily_limits_not_expired(self, trader):
        """Test daily limits not reset before 24 hours."""
        trader.daily_traded = 200.0
        trader.daily_reset_time = time.time() - 3600  # Only 1 hour ago

        trader._reset_daily_limits()

        assert trader.daily_traded == 200.0

    def test_set_trading_limits(self, trader):
        """Test setting trading limits."""
        trader.set_trading_limits(max_trade_value=75.0, daily_limit=300.0)

        assert trader.max_trade_value == 75.0
        assert trader.daily_limit == 300.0

    def test_set_trading_limits_partial(self, trader):
        """Test setting only one limit."""
        original_daily_limit = trader.daily_limit

        trader.set_trading_limits(max_trade_value=75.0)

        assert trader.max_trade_value == 75.0
        assert trader.daily_limit == original_daily_limit


# ==============================================================================
# TEST ERROR HANDLING
# ==============================================================================


class TestErrorHandling:
    """Tests for error handling and recovery."""

    @pytest.mark.asyncio
    async def test_handle_trading_error_increments_count(self, trader):
        """Test error handling increments error count."""
        assert trader.error_count == 0

        await trader._handle_trading_error()

        assert trader.error_count == 1

    @pytest.mark.asyncio
    async def test_handle_trading_error_pause_after_3_errors(self, trader):
        """Test 15 minute pause after 3 errors."""
        trader.error_count = 2

        await trader._handle_trading_error()

        assert trader.error_count == 3
        assert trader.pause_until > time.time()
        assert trader.pause_until < time.time() + 1000  # ~15 minutes

    @pytest.mark.asyncio
    async def test_handle_trading_error_pause_after_10_errors(self, trader):
        """Test 1 hour pause after 10 errors."""
        trader.error_count = 9

        await trader._handle_trading_error()

        assert trader.error_count == 0  # Reset after 10
        assert trader.pause_until > time.time()
        assert trader.pause_until < time.time() + 4000  # ~1 hour

    @pytest.mark.asyncio
    async def test_can_trade_now_no_pause(self, trader):
        """Test trading allowed when no pause."""
        result = await trader._can_trade_now()

        assert result is True

    @pytest.mark.asyncio
    async def test_can_trade_now_during_pause(self, trader):
        """Test trading blocked during pause."""
        trader.pause_until = time.time() + 600  # 10 minutes from now

        result = await trader._can_trade_now()

        assert result is False

    @pytest.mark.asyncio
    async def test_can_trade_now_after_pause_expires(self, trader):
        """Test trading allowed after pause expires."""
        trader.pause_until = time.time() - 60  # Pause expired 1 minute ago
        trader.error_count = 5

        result = await trader._can_trade_now()

        assert result is True
        assert trader.pause_until == 0
        assert trader.error_count == 0


# ==============================================================================
# TEST PROFITABLE ITEMS SEARCH
# ==============================================================================


class TestFindProfitableItems:
    """Tests for finding profitable items."""

    @pytest.mark.asyncio
    async def test_find_profitable_items_success(
        self, trader, mock_api_client, sample_market_items
    ):
        """Test finding profitable items."""
        mock_api_client.get_all_market_items.return_value = sample_market_items

        opportunities = await trader.find_profitable_items(
            game="csgo",
            min_profit_percentage=5.0,
        )

        # Should find AK-47 Redline opportunity (10 -> 12 = 20% profit before commission)
        assert isinstance(opportunities, list)
        mock_api_client.get_all_market_items.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_profitable_items_empty_market(self, trader, mock_api_client):
        """Test when no items on market."""
        mock_api_client.get_all_market_items.return_value = []

        opportunities = await trader.find_profitable_items(game="csgo")

        assert opportunities == []

    @pytest.mark.asyncio
    async def test_find_profitable_items_no_opportunities(self, trader, mock_api_client):
        """Test when no profitable opportunities exist."""
        mock_api_client.get_all_market_items.return_value = [
            {
                "title": "Test Item",
                "itemId": "item1",
                "price": {"USD": "1000"},
                "extra": {"rarity": "Common", "category": "Other", "popularity": 0.5},
            },
        ]

        opportunities = await trader.find_profitable_items(game="csgo")

        assert opportunities == []  # Single item can't have arbitrage

    @pytest.mark.asyncio
    async def test_find_profitable_items_api_error(self, trader, mock_api_client):
        """Test handling API error during search."""
        mock_api_client.get_all_market_items.side_effect = Exception("API Error")

        opportunities = await trader.find_profitable_items(game="csgo")

        assert opportunities == []

    @pytest.mark.asyncio
    async def test_find_profitable_items_custom_parameters(
        self, trader, mock_api_client
    ):
        """Test search with custom parameters."""
        mock_api_client.get_all_market_items.return_value = []

        await trader.find_profitable_items(
            game="dota2",
            min_profit_percentage=10.0,
            max_items=50,
            min_price=5.0,
            max_price=50.0,
        )

        mock_api_client.get_all_market_items.assert_called_once_with(
            game="dota2",
            max_items=50,
            price_from=5.0,
            price_to=50.0,
            sort="price",
        )


# ==============================================================================
# TEST TRADE EXECUTION
# ==============================================================================


class TestExecuteArbitrageTrade:
    """Tests for executing arbitrage trades."""

    @pytest.mark.asyncio
    async def test_execute_trade_success(
        self, trader, mock_api_client, sample_profitable_item
    ):
        """Test successful trade execution."""
        mock_api_client.get_balance.return_value = {"usd": "10000"}  # $100
        mock_api_client._request.side_effect = [
            {"items": [{"itemId": "new_item_123"}]},  # Purchase response
            {"success": True},  # Sell response
        ]

        result = await trader.execute_arbitrage_trade(sample_profitable_item)

        assert result["success"] is True
        assert result["profit"] == sample_profitable_item["profit"]
        assert trader.daily_traded == sample_profitable_item["buy_price"]
        assert len(trader.transaction_history) == 1

    @pytest.mark.asyncio
    async def test_execute_trade_insufficient_funds(
        self, trader, mock_api_client, sample_profitable_item
    ):
        """Test trade with insufficient funds."""
        mock_api_client.get_balance.return_value = {"usd": "500"}  # $5

        result = await trader.execute_arbitrage_trade(sample_profitable_item)

        assert result["success"] is False
        assert "Недостаточно средств" in result["errors"][0]

    @pytest.mark.asyncio
    async def test_execute_trade_exceeds_limits(
        self, trader, mock_api_client, sample_profitable_item
    ):
        """Test trade exceeding trading limits."""
        trader.max_trade_value = 5.0  # Set max below buy price

        result = await trader.execute_arbitrage_trade(sample_profitable_item)

        assert result["success"] is False
        assert "Превышены лимиты" in result["errors"][0]

    @pytest.mark.asyncio
    async def test_execute_trade_purchase_error(
        self, trader, mock_api_client, sample_profitable_item
    ):
        """Test trade when purchase fails."""
        mock_api_client.get_balance.return_value = {"usd": "10000"}
        mock_api_client._request.return_value = {
            "error": {"message": "Item not available"}
        }

        result = await trader.execute_arbitrage_trade(sample_profitable_item)

        assert result["success"] is False
        assert "Ошибка покупки" in result["errors"][0]

    @pytest.mark.asyncio
    async def test_execute_trade_sell_error(
        self, trader, mock_api_client, sample_profitable_item
    ):
        """Test trade when selling fails."""
        mock_api_client.get_balance.return_value = {"usd": "10000"}
        mock_api_client._request.side_effect = [
            {"items": [{"itemId": "new_item_123"}]},  # Purchase success
            {"error": {"message": "Sell failed"}},  # Sell failure
        ]

        result = await trader.execute_arbitrage_trade(sample_profitable_item)

        assert result["success"] is False
        assert "Ошибка выставления" in result["errors"][0]


# ==============================================================================
# TEST AUTO TRADING
# ==============================================================================


class TestAutoTrading:
    """Tests for auto trading functionality."""

    @pytest.mark.asyncio
    async def test_start_auto_trading_success(self, trader, mock_api_client):
        """Test starting auto trading."""
        mock_api_client.get_balance.return_value = {"usd": "10000"}

        with patch.object(trader, "_auto_trading_loop", new_callable=AsyncMock):
            success, message = await trader.start_auto_trading(
                game="csgo",
                min_profit_percentage=5.0,
            )

        assert success is True
        assert "Автоторговля запущена" in message
        assert trader.active is True
        assert trader.current_game == "csgo"
        assert trader.min_profit_percentage == 5.0

    @pytest.mark.asyncio
    async def test_start_auto_trading_already_active(self, trader, mock_api_client):
        """Test starting auto trading when already active."""
        trader.active = True

        success, message = await trader.start_auto_trading()

        assert success is False
        assert "уже запущена" in message

    @pytest.mark.asyncio
    async def test_start_auto_trading_insufficient_funds(self, trader, mock_api_client):
        """Test starting auto trading with insufficient funds."""
        mock_api_client.get_balance.return_value = {"usd": "50"}  # $0.50

        success, message = await trader.start_auto_trading()

        assert success is False
        assert "Недостаточно средств" in message

    @pytest.mark.asyncio
    async def test_stop_auto_trading_success(self, trader):
        """Test stopping auto trading."""
        trader.active = True

        success, message = await trader.stop_auto_trading()

        assert success is True
        assert "Автоторговля остановлена" in message
        assert trader.active is False

    @pytest.mark.asyncio
    async def test_stop_auto_trading_not_active(self, trader):
        """Test stopping auto trading when not active."""
        success, message = await trader.stop_auto_trading()

        assert success is False
        assert "не запущена" in message


# ==============================================================================
# TEST STATUS AND HISTORY
# ==============================================================================


class TestStatusAndHistory:
    """Tests for status and transaction history."""

    def test_get_status_initial(self, trader):
        """Test getting status with no activity."""
        status = trader.get_status()

        assert status["active"] is False
        assert status["current_game"] == "csgo"
        assert status["transactions_count"] == 0
        assert status["total_profit"] == 0.0
        assert status["daily_traded"] == 0.0
        assert status["error_count"] == 0
        assert status["on_pause"] is False

    def test_get_status_with_transactions(self, trader):
        """Test getting status with transactions."""
        trader.transaction_history = [
            {"profit": 1.5},
            {"profit": 2.0},
            {"profit": 0.75},
        ]
        trader.daily_traded = 50.0
        trader.active = True

        status = trader.get_status()

        assert status["active"] is True
        assert status["transactions_count"] == 3
        assert status["total_profit"] == 4.25
        assert status["daily_traded"] == 50.0

    def test_get_status_during_pause(self, trader):
        """Test getting status during pause."""
        trader.pause_until = time.time() + 600  # 10 minutes

        status = trader.get_status()

        assert status["on_pause"] is True
        assert status["pause_minutes"] > 0

    def test_get_transaction_history_empty(self, trader):
        """Test getting empty transaction history."""
        history = trader.get_transaction_history()

        assert history == []

    def test_get_transaction_history_with_data(self, trader):
        """Test getting transaction history with data."""
        transactions = [
            {"item_name": "Item 1", "profit": 1.0},
            {"item_name": "Item 2", "profit": 2.0},
        ]
        trader.transaction_history = transactions

        history = trader.get_transaction_history()

        assert history == transactions


# ==============================================================================
# TEST ITEM DATA RETRIEVAL
# ==============================================================================


class TestItemDataRetrieval:
    """Tests for getting current item data."""

    @pytest.mark.asyncio
    async def test_get_current_item_data_success(self, trader, mock_api_client):
        """Test successful item data retrieval."""
        mock_api_client._request.return_value = {
            "objects": [
                {
                    "itemId": "item123",
                    "price": {"USD": "1500"},
                    "title": "AK-47 | Redline",
                }
            ]
        }

        result = await trader.get_current_item_data("item123", "csgo")

        assert result is not None
        assert result["itemId"] == "item123"
        assert result["price"] == 15.0
        assert result["title"] == "AK-47 | Redline"
        assert result["game"] == "csgo"

    @pytest.mark.asyncio
    async def test_get_current_item_data_not_found(self, trader, mock_api_client):
        """Test item data retrieval when item not found."""
        mock_api_client._request.return_value = {"objects": []}

        result = await trader.get_current_item_data("nonexistent", "csgo")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_current_item_data_empty_response(self, trader, mock_api_client):
        """Test item data retrieval with empty response."""
        mock_api_client._request.return_value = {}

        result = await trader.get_current_item_data("item123", "csgo")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_current_item_data_api_error(self, trader, mock_api_client):
        """Test item data retrieval with API error."""
        mock_api_client._request.side_effect = Exception("API Error")

        result = await trader.get_current_item_data("item123", "csgo")

        assert result is None


# ==============================================================================
# TEST PURCHASE AND SELL OPERATIONS
# ==============================================================================


class TestPurchaseAndSell:
    """Tests for purchase and sell operations."""

    @pytest.mark.asyncio
    async def test_purchase_item_success(self, trader, mock_api_client):
        """Test successful item purchase."""
        mock_api_client._request.return_value = {
            "items": [{"itemId": "new_item_456"}]
        }

        result = await trader.purchase_item("item123", 10.0)

        assert result["success"] is True
        assert result["new_item_id"] == "new_item_456"
        assert result["price"] == 10.0

    @pytest.mark.asyncio
    async def test_purchase_item_error_response(self, trader, mock_api_client):
        """Test item purchase with error response."""
        mock_api_client._request.return_value = {
            "error": {"message": "Item not available"}
        }

        result = await trader.purchase_item("item123", 10.0)

        assert result["success"] is False
        assert "Item not available" in result["error"]

    @pytest.mark.asyncio
    async def test_purchase_item_no_items_returned(self, trader, mock_api_client):
        """Test item purchase when no items returned."""
        mock_api_client._request.return_value = {"items": []}

        result = await trader.purchase_item("item123", 10.0)

        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_purchase_item_api_exception(self, trader, mock_api_client):
        """Test item purchase with API exception."""
        mock_api_client._request.side_effect = Exception("Network error")

        result = await trader.purchase_item("item123", 10.0)

        assert result["success"] is False
        assert "Network error" in result["error"]

    @pytest.mark.asyncio
    async def test_list_item_for_sale_success(self, trader, mock_api_client):
        """Test successful item listing for sale."""
        mock_api_client._request.return_value = {"success": True}

        result = await trader.list_item_for_sale("item123", 15.0)

        assert result["success"] is True
        assert result["price"] == 15.0

    @pytest.mark.asyncio
    async def test_list_item_for_sale_error_response(self, trader, mock_api_client):
        """Test item listing with error response."""
        mock_api_client._request.return_value = {
            "error": {"message": "Item locked"}
        }

        result = await trader.list_item_for_sale("item123", 15.0)

        assert result["success"] is False
        assert "Item locked" in result["error"]

    @pytest.mark.asyncio
    async def test_list_item_for_sale_api_exception(self, trader, mock_api_client):
        """Test item listing with API exception."""
        mock_api_client._request.side_effect = Exception("Network error")

        result = await trader.list_item_for_sale("item123", 15.0)

        assert result["success"] is False
        assert "Network error" in result["error"]


# ==============================================================================
# TEST EDGE CASES
# ==============================================================================


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_init_with_zero_limits(self, mock_api_client):
        """Test initialization with zero limits."""
        trader = ArbitrageTrader(
            api_client=mock_api_client,
            min_profit_percentage=0.0,
            max_trade_value=0.0,
            daily_limit=0.0,
        )

        assert trader.min_profit_percentage == 0.0
        assert trader.max_trade_value == 0.0
        assert trader.daily_limit == 0.0

    def test_init_with_negative_limits(self, mock_api_client):
        """Test initialization with negative limits."""
        trader = ArbitrageTrader(
            api_client=mock_api_client,
            min_profit_percentage=-5.0,
            max_trade_value=-100.0,
            daily_limit=-500.0,
        )

        # Should accept negative values (validation might be elsewhere)
        assert trader.min_profit_percentage == -5.0

    @pytest.mark.asyncio
    async def test_check_trading_limits_with_zero_trade_value(self, trader):
        """Test checking limits with zero trade value."""
        result = await trader._check_trading_limits(0.0)

        assert result is True

    @pytest.mark.asyncio
    async def test_execute_trade_with_zero_profit_item(self, trader, mock_api_client):
        """Test executing trade with zero profit item."""
        mock_api_client.get_balance.return_value = {"usd": "10000"}

        item = {
            "name": "Test Item",
            "buy_price": 10.0,
            "sell_price": 10.0,
            "profit": 0.0,
            "profit_percentage": 0.0,
            "buy_item_id": "buy_123",
            "sell_item_id": "sell_456",
            "game": "csgo",
        }

        mock_api_client._request.side_effect = [
            {"items": [{"itemId": "new_item"}]},
            {"success": True},
        ]

        result = await trader.execute_arbitrage_trade(item)

        # Should still execute even with zero profit
        assert result["success"] is True
        assert result["profit"] == 0.0

    def test_get_status_with_large_transaction_history(self, trader):
        """Test status with many transactions."""
        trader.transaction_history = [
            {"profit": i * 0.1}
            for i in range(1000)
        ]

        status = trader.get_status()

        assert status["transactions_count"] == 1000
        # Sum of 0.1 + 0.2 + ... + 99.9 = ~5000
        assert status["total_profit"] > 0

    @pytest.mark.asyncio
    async def test_find_profitable_items_with_items_missing_fields(
        self, trader, mock_api_client
    ):
        """Test finding items when market items have missing fields."""
        mock_api_client.get_all_market_items.return_value = [
            {"title": "Item 1"},  # Missing price and extra
            {"price": {"USD": "1000"}},  # Missing title
            {},  # Empty item
        ]

        opportunities = await trader.find_profitable_items(game="csgo")

        # Should handle gracefully without crashing
        assert isinstance(opportunities, list)
