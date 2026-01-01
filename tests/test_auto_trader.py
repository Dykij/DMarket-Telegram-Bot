"""Tests for refactored auto trader module.

Phase 2 Refactoring Tests (January 1, 2026)
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.dmarket.auto_trader_refactored import AutoTrader, RiskConfig, TradeResult


class TestRiskConfig:
    """Tests for RiskConfig class."""

    def test_risk_config_low_level(self):
        """Test low risk configuration."""
        # Arrange & Act
        config = RiskConfig.from_level(
            level="low",
            max_trades=10,
            max_price=100.0,
            min_profit=0.5,
            balance=1000.0,
        )

        # Assert
        assert config.level == "low"
        assert config.max_trades == 2  # Limited to 2
        assert config.max_price == 20.0  # Limited to $20
        assert config.min_profit == 1.0  # Increased to $1
        assert config.balance == 1000.0

    def test_risk_config_medium_level(self):
        """Test medium risk configuration."""
        # Arrange & Act
        config = RiskConfig.from_level(
            level="medium",
            max_trades=10,
            max_price=100.0,
            min_profit=0.5,
            balance=1000.0,
        )

        # Assert
        assert config.level == "medium"
        assert config.max_trades == 5  # Limited to 5
        assert config.max_price == 50.0  # Limited to $50
        assert config.min_profit == 0.5  # Unchanged
        assert config.balance == 1000.0

    def test_risk_config_high_level(self):
        """Test high risk configuration."""
        # Arrange & Act
        config = RiskConfig.from_level(
            level="high",
            max_trades=10,
            max_price=1000.0,
            min_profit=0.5,
            balance=100.0,
        )

        # Assert
        assert config.level == "high"
        assert config.max_trades == 10  # Unchanged
        assert config.max_price == 80.0  # 80% of balance
        assert config.min_profit == 0.5  # Unchanged
        assert config.balance == 100.0


class TestTradeResult:
    """Tests for TradeResult class."""

    def test_trade_result_initialization(self):
        """Test trade result initializes with zeros."""
        # Arrange & Act
        result = TradeResult()

        # Assert
        assert result.purchases == 0
        assert result.sales == 0
        assert result.total_profit == 0.0
        assert result.trades_count == 0
        assert result.remaining_balance == 0.0

    def test_add_purchase(self):
        """Test adding purchase."""
        # Arrange
        result = TradeResult()
        result.remaining_balance = 100.0

        # Act
        result.add_purchase(25.0)

        # Assert
        assert result.purchases == 1
        assert result.remaining_balance == 75.0

    def test_add_sale(self):
        """Test adding sale."""
        # Arrange
        result = TradeResult()

        # Act
        result.add_sale(5.0)

        # Assert
        assert result.sales == 1
        assert result.total_profit == 5.0

    def test_increment_trades(self):
        """Test incrementing trades counter."""
        # Arrange
        result = TradeResult()

        # Act
        result.increment_trades()
        result.increment_trades()

        # Assert
        assert result.trades_count == 2

    def test_to_tuple(self):
        """Test converting to tuple."""
        # Arrange
        result = TradeResult()
        result.purchases = 5
        result.sales = 3
        result.total_profit = 15.5

        # Act
        tuple_result = result.to_tuple()

        # Assert
        assert tuple_result == (5, 3, 15.5)


class TestAutoTrader:
    """Tests for AutoTrader class."""

    @pytest.fixture()
    def mock_scanner(self):
        """Create mock scanner."""
        scanner = MagicMock()
        scanner.min_profit = 0.5
        scanner.max_price = 50.0
        scanner.max_trades = 5
        scanner.api_client = MagicMock()
        scanner.successful_trades = 0
        scanner.total_profit = 0.0
        scanner.check_user_balance = AsyncMock(return_value={"balance": 100.0, "has_funds": True})
        scanner.get_api_client = AsyncMock(return_value=MagicMock())
        scanner._get_current_item_data = AsyncMock()
        scanner._purchase_item = AsyncMock()
        scanner._list_item_for_sale = AsyncMock()
        return scanner

    @pytest.fixture()
    def auto_trader(self, mock_scanner):
        """Create auto trader instance."""
        return AutoTrader(scanner=mock_scanner)

    def test_has_sufficient_balance_true(self, auto_trader):
        """Test sufficient balance check returns true."""
        # Arrange
        balance_data = {"balance": 100.0, "has_funds": True}

        # Act
        result = auto_trader._has_sufficient_balance(balance_data)

        # Assert
        assert result is True

    def test_has_sufficient_balance_false_no_funds(self, auto_trader):
        """Test insufficient balance with no funds."""
        # Arrange
        balance_data = {"balance": 100.0, "has_funds": False}

        # Act
        result = auto_trader._has_sufficient_balance(balance_data)

        # Assert
        assert result is False

    def test_has_sufficient_balance_false_low_balance(self, auto_trader):
        """Test insufficient balance with low amount."""
        # Arrange
        balance_data = {"balance": 0.5, "has_funds": True}

        # Act
        result = auto_trader._has_sufficient_balance(balance_data)

        # Assert
        assert result is False

    def test_prepare_items_for_trading(self, auto_trader):
        """Test items preparation and sorting."""
        # Arrange
        items_by_game = {
            "csgo": [
                {"title": "Item A", "profit": 5.0},
                {"title": "Item B", "profit": 10.0},
            ],
            "dota2": [
                {"title": "Item C", "profit": 3.0},
            ],
        }

        # Act
        sorted_items = auto_trader._prepare_items_for_trading(items_by_game)

        # Assert
        assert len(sorted_items) == 3
        assert sorted_items[0]["profit"] == 10.0  # Highest first
        assert sorted_items[0]["game"] == "csgo"
        assert sorted_items[1]["profit"] == 5.0
        assert sorted_items[2]["profit"] == 3.0
        assert sorted_items[2]["game"] == "dota2"

    def test_should_continue_trading_true(self, auto_trader):
        """Test should continue trading returns true."""
        # Arrange
        result = TradeResult()
        result.trades_count = 2
        result.remaining_balance = 50.0
        config = RiskConfig("medium", 5, 50.0, 0.5, 100.0)

        # Act
        should_continue = auto_trader._should_continue_trading(result, config)

        # Assert
        assert should_continue is True

    def test_should_continue_trading_false_limit_reached(self, auto_trader):
        """Test should stop when trade limit reached."""
        # Arrange
        result = TradeResult()
        result.trades_count = 5
        result.remaining_balance = 50.0
        config = RiskConfig("medium", 5, 50.0, 0.5, 100.0)

        # Act
        should_continue = auto_trader._should_continue_trading(result, config)

        # Assert
        assert should_continue is False

    def test_should_continue_trading_false_no_balance(self, auto_trader):
        """Test should stop when balance is low."""
        # Arrange
        result = TradeResult()
        result.trades_count = 2
        result.remaining_balance = 0.5
        config = RiskConfig("medium", 5, 50.0, 0.5, 100.0)

        # Act
        should_continue = auto_trader._should_continue_trading(result, config)

        # Assert
        assert should_continue is False

    def test_is_item_suitable_true(self, auto_trader):
        """Test item suitability check returns true."""
        # Arrange
        item = {
            "title": "Test Item",
            "price": {"amount": 2000},  # $20.00
            "profit": 5.0,
        }
        result = TradeResult()
        result.remaining_balance = 50.0
        config = RiskConfig("medium", 5, 50.0, 1.0, 100.0)

        # Act
        is_suitable = auto_trader._is_item_suitable(item, config, result)

        # Assert
        assert is_suitable is True

    def test_is_item_suitable_false_price_too_high(self, auto_trader):
        """Test item rejected when price exceeds limit."""
        # Arrange
        item = {
            "title": "Test Item",
            "price": {"amount": 6000},  # $60.00
            "profit": 5.0,
        }
        result = TradeResult()
        result.remaining_balance = 100.0
        config = RiskConfig("medium", 5, 50.0, 1.0, 100.0)

        # Act
        is_suitable = auto_trader._is_item_suitable(item, config, result)

        # Assert
        assert is_suitable is False

    def test_is_item_suitable_false_profit_too_low(self, auto_trader):
        """Test item rejected when profit is too low."""
        # Arrange
        item = {
            "title": "Test Item",
            "price": {"amount": 2000},  # $20.00
            "profit": 0.5,  # Below min_profit
        }
        result = TradeResult()
        result.remaining_balance = 100.0
        config = RiskConfig("medium", 5, 50.0, 1.0, 100.0)

        # Act
        is_suitable = auto_trader._is_item_suitable(item, config, result)

        # Assert
        assert is_suitable is False

    def test_is_item_suitable_false_exceeds_balance(self, auto_trader):
        """Test item rejected when price exceeds balance."""
        # Arrange
        item = {
            "title": "Test Item",
            "price": {"amount": 3000},  # $30.00
            "profit": 5.0,
        }
        result = TradeResult()
        result.remaining_balance = 20.0  # Less than item price
        config = RiskConfig("medium", 5, 50.0, 1.0, 100.0)

        # Act
        is_suitable = auto_trader._is_item_suitable(item, config, result)

        # Assert
        assert is_suitable is False

    def test_is_price_acceptable_true(self, auto_trader):
        """Test price acceptability check returns true."""
        # Arrange
        updated_item = {"price": 20.0}
        original_price = 20.0
        title = "Test Item"

        # Act
        is_acceptable = auto_trader._is_price_acceptable(updated_item, original_price, title)

        # Assert
        assert is_acceptable is True

    def test_is_price_acceptable_false_none(self, auto_trader):
        """Test price check fails when item not found."""
        # Arrange
        updated_item = None
        original_price = 20.0
        title = "Test Item"

        # Act
        is_acceptable = auto_trader._is_price_acceptable(updated_item, original_price, title)

        # Assert
        assert is_acceptable is False

    def test_is_price_acceptable_false_increased(self, auto_trader):
        """Test price check fails when price increased."""
        # Arrange
        updated_item = {"price": 25.0}  # Increased > 5%
        original_price = 20.0
        title = "Test Item"

        # Act
        is_acceptable = auto_trader._is_price_acceptable(updated_item, original_price, title)

        # Assert
        assert is_acceptable is False

    @pytest.mark.asyncio()
    async def test_auto_trade_items_insufficient_balance(self, auto_trader, mock_scanner):
        """Test auto trade returns zeros with insufficient balance."""
        # Arrange
        mock_scanner.check_user_balance.return_value = {
            "balance": 0.5,
            "has_funds": False,
        }
        items_by_game = {"csgo": [{"title": "Item", "profit": 5.0}]}

        # Act
        result = await auto_trader.auto_trade_items(
            items_by_game=items_by_game,
            risk_level="medium",
        )

        # Assert
        assert result == (0, 0, 0.0)

    @pytest.mark.asyncio()
    async def test_purchase_item_safe_success(self, auto_trader, mock_scanner):
        """Test successful item purchase."""
        # Arrange
        mock_scanner._purchase_item.return_value = {
            "success": True,
            "new_item_id": "item_123",
        }

        # Act
        result = await auto_trader._purchase_item_safe(
            item_id="item_123",
            buy_price=20.0,
            title="Test Item",
            api_client=mock_scanner.api_client,
        )

        # Assert
        assert result is not None
        assert result["success"] is True
        assert result["new_item_id"] == "item_123"

    @pytest.mark.asyncio()
    async def test_purchase_item_safe_failure(self, auto_trader, mock_scanner):
        """Test failed item purchase."""
        # Arrange
        mock_scanner._purchase_item.return_value = {
            "success": False,
            "error": "Item unavailable",
        }

        # Act
        result = await auto_trader._purchase_item_safe(
            item_id="item_123",
            buy_price=20.0,
            title="Test Item",
            api_client=mock_scanner.api_client,
        )

        # Assert
        assert result is None

    @pytest.mark.asyncio()
    async def test_sell_item_success(self, auto_trader, mock_scanner):
        """Test successful item sale."""
        # Arrange
        mock_scanner._list_item_for_sale.return_value = {"success": True}
        result = TradeResult()

        # Act
        await auto_trader._sell_item(
            item_id="item_123",
            buy_price=20.0,
            profit=5.0,
            title="Test Item",
            result=result,
            api_client=mock_scanner.api_client,
        )

        # Assert
        assert result.sales == 1
        assert result.total_profit == 5.0

    @pytest.mark.asyncio()
    async def test_sell_item_failure(self, auto_trader, mock_scanner):
        """Test failed item sale."""
        # Arrange
        mock_scanner._list_item_for_sale.return_value = {
            "success": False,
            "error": "Listing failed",
        }
        result = TradeResult()

        # Act
        await auto_trader._sell_item(
            item_id="item_123",
            buy_price=20.0,
            profit=5.0,
            title="Test Item",
            result=result,
            api_client=mock_scanner.api_client,
        )

        # Assert
        assert result.sales == 0
        assert result.total_profit == 0.0

    def test_update_statistics(self, auto_trader, mock_scanner):
        """Test statistics update."""
        # Arrange
        result = TradeResult()
        result.sales = 5
        result.total_profit = 25.0

        # Act
        auto_trader._update_statistics(result)

        # Assert
        assert mock_scanner.successful_trades == 5
        assert mock_scanner.total_profit == 25.0
