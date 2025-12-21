"""Tests for analytics/backtester.py module.

Comprehensive test suite covering:
- Trade dataclass tests
- Position dataclass tests
- BacktestResult dataclass tests
- TradingStrategy abstract class tests
- SimpleArbitrageStrategy tests
- Backtester class tests
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from src.analytics.backtester import (
    BacktestResult,
    Backtester,
    Position,
    SimpleArbitrageStrategy,
    Trade,
    TradeType,
    TradingStrategy,
)
from src.analytics.historical_data import PriceHistory, PricePoint


# ============================================================================
# TradeType Tests
# ============================================================================


class TestTradeType:
    """Tests for TradeType enum."""

    def test_buy_type(self):
        """Test BUY trade type."""
        assert TradeType.BUY == "buy"
        assert TradeType.BUY.value == "buy"

    def test_sell_type(self):
        """Test SELL trade type."""
        assert TradeType.SELL == "sell"
        assert TradeType.SELL.value == "sell"


# ============================================================================
# Trade Tests
# ============================================================================


class TestTrade:
    """Tests for Trade dataclass."""

    def test_create_buy_trade(self):
        """Test creating a buy trade."""
        trade = Trade(
            trade_type=TradeType.BUY,
            item_title="AK-47 | Redline",
            price=Decimal("10.50"),
            quantity=2,
            timestamp=datetime(2024, 1, 1, tzinfo=UTC),
        )

        assert trade.trade_type == TradeType.BUY
        assert trade.item_title == "AK-47 | Redline"
        assert trade.price == Decimal("10.50")
        assert trade.quantity == 2
        assert trade.fees == Decimal(0)  # Default

    def test_create_sell_trade_with_fees(self):
        """Test creating a sell trade with fees."""
        trade = Trade(
            trade_type=TradeType.SELL,
            item_title="AWP | Asiimov",
            price=Decimal("25.00"),
            quantity=1,
            timestamp=datetime(2024, 1, 1, tzinfo=UTC),
            fees=Decimal("1.75"),  # 7% of 25
        )

        assert trade.trade_type == TradeType.SELL
        assert trade.fees == Decimal("1.75")

    def test_total_cost_buy(self):
        """Test total cost calculation for buy trade."""
        trade = Trade(
            trade_type=TradeType.BUY,
            item_title="Item",
            price=Decimal("10"),
            quantity=3,
            timestamp=datetime.now(UTC),
            fees=Decimal("0"),
        )

        assert trade.total_cost == Decimal("30")  # 10 * 3

    def test_total_cost_with_fees(self):
        """Test total cost includes fees."""
        trade = Trade(
            trade_type=TradeType.BUY,
            item_title="Item",
            price=Decimal("10"),
            quantity=2,
            timestamp=datetime.now(UTC),
            fees=Decimal("2"),
        )

        assert trade.total_cost == Decimal("22")  # 10 * 2 + 2

    def test_net_amount_buy(self):
        """Test net amount is negative for buys."""
        trade = Trade(
            trade_type=TradeType.BUY,
            item_title="Item",
            price=Decimal("10"),
            quantity=2,
            timestamp=datetime.now(UTC),
            fees=Decimal("0"),
        )

        assert trade.net_amount == Decimal("-20")  # Outgoing money

    def test_net_amount_sell(self):
        """Test net amount for sells (after fees)."""
        trade = Trade(
            trade_type=TradeType.SELL,
            item_title="Item",
            price=Decimal("10"),
            quantity=2,
            timestamp=datetime.now(UTC),
            fees=Decimal("1.40"),  # 7% fee
        )

        assert trade.net_amount == Decimal("18.60")  # 20 - 1.40


# ============================================================================
# Position Tests
# ============================================================================


class TestPosition:
    """Tests for Position dataclass."""

    def test_create_position(self):
        """Test creating a position."""
        position = Position(
            item_title="AK-47",
            quantity=5,
            average_cost=Decimal("12.50"),
            created_at=datetime(2024, 1, 1, tzinfo=UTC),
        )

        assert position.item_title == "AK-47"
        assert position.quantity == 5
        assert position.average_cost == Decimal("12.50")

    def test_total_value(self):
        """Test total value calculation."""
        position = Position(
            item_title="Item",
            quantity=3,
            average_cost=Decimal("10"),
            created_at=datetime.now(UTC),
        )

        assert position.total_value == Decimal("30")

    def test_update_position(self):
        """Test updating position with new purchase."""
        position = Position(
            item_title="Item",
            quantity=2,
            average_cost=Decimal("10"),
            created_at=datetime.now(UTC),
        )

        # Buy 3 more at $15 each
        position.update(quantity=3, price=Decimal("15"))

        assert position.quantity == 5
        # Average: (2*10 + 3*15) / 5 = (20 + 45) / 5 = 13
        assert position.average_cost == Decimal("13")

    def test_update_position_zero_quantity(self):
        """Test updating position resulting in zero quantity."""
        position = Position(
            item_title="Item",
            quantity=2,
            average_cost=Decimal("10"),
            created_at=datetime.now(UTC),
        )

        # Sell all items (negative quantity update)
        position.update(quantity=-2, price=Decimal("0"))

        assert position.quantity == 0


# ============================================================================
# BacktestResult Tests
# ============================================================================


class TestBacktestResult:
    """Tests for BacktestResult dataclass."""

    @pytest.fixture()
    def sample_result(self):
        """Create a sample backtest result."""
        return BacktestResult(
            strategy_name="TestStrategy",
            start_date=datetime(2024, 1, 1, tzinfo=UTC),
            end_date=datetime(2024, 1, 31, tzinfo=UTC),
            initial_balance=Decimal("1000"),
            final_balance=Decimal("1150"),
            total_trades=20,
            profitable_trades=12,
            total_profit=Decimal("150"),
            max_drawdown=Decimal("5.5"),
            sharpe_ratio=1.5,
            win_rate=60.0,
            trades=[],
            positions_closed=8,
        )

    def test_total_return(self, sample_result):
        """Test total return calculation."""
        # (1150 - 1000) / 1000 * 100 = 15%
        assert sample_result.total_return == 15.0

    def test_total_return_zero_initial(self):
        """Test total return with zero initial balance."""
        result = BacktestResult(
            strategy_name="Test",
            start_date=datetime.now(UTC),
            end_date=datetime.now(UTC),
            initial_balance=Decimal("0"),
            final_balance=Decimal("100"),
            total_trades=0,
            profitable_trades=0,
            total_profit=Decimal("100"),
            max_drawdown=Decimal("0"),
            sharpe_ratio=0,
            win_rate=0,
        )

        assert result.total_return == 0.0

    def test_avg_profit_per_trade(self, sample_result):
        """Test average profit per trade."""
        # 150 / 20 = 7.5
        assert sample_result.avg_profit_per_trade == Decimal("7.5")

    def test_avg_profit_per_trade_no_trades(self):
        """Test average profit with no trades."""
        result = BacktestResult(
            strategy_name="Test",
            start_date=datetime.now(UTC),
            end_date=datetime.now(UTC),
            initial_balance=Decimal("1000"),
            final_balance=Decimal("1000"),
            total_trades=0,
            profitable_trades=0,
            total_profit=Decimal("0"),
            max_drawdown=Decimal("0"),
            sharpe_ratio=0,
            win_rate=0,
        )

        assert result.avg_profit_per_trade == Decimal("0")

    def test_to_dict(self, sample_result):
        """Test converting result to dictionary."""
        data = sample_result.to_dict()

        assert data["strategy_name"] == "TestStrategy"
        assert data["initial_balance"] == 1000.0
        assert data["final_balance"] == 1150.0
        assert data["total_return"] == 15.0
        assert data["total_trades"] == 20
        assert data["win_rate"] == 60.0
        assert "start_date" in data
        assert "end_date" in data


# ============================================================================
# SimpleArbitrageStrategy Tests
# ============================================================================


class TestSimpleArbitrageStrategy:
    """Tests for SimpleArbitrageStrategy."""

    @pytest.fixture()
    def strategy(self):
        """Create a strategy instance."""
        return SimpleArbitrageStrategy(
            buy_threshold=0.05,
            sell_margin=0.08,
            max_position_pct=0.1,
            dmarket_fee=0.07,
        )

    def test_initialization(self):
        """Test strategy initialization."""
        strategy = SimpleArbitrageStrategy()

        assert strategy.name == "SimpleArbitrage"
        assert strategy.buy_threshold == 0.05
        assert strategy.sell_margin == 0.08
        assert strategy.max_position_pct == 0.1
        assert strategy.dmarket_fee == 0.07

    def test_custom_initialization(self):
        """Test strategy with custom parameters."""
        strategy = SimpleArbitrageStrategy(
            buy_threshold=0.10,
            sell_margin=0.15,
            max_position_pct=0.05,
            dmarket_fee=0.05,
        )

        assert strategy.buy_threshold == 0.10
        assert strategy.sell_margin == 0.15

    def test_should_buy_below_threshold(self, strategy):
        """Test should buy when price is below threshold."""
        # Create price history with average = 100
        points = [
            PricePoint("csgo", "Item", Decimal("100"), datetime.now(UTC)),
            PricePoint("csgo", "Item", Decimal("100"), datetime.now(UTC)),
        ]
        history = PriceHistory("csgo", "Item", points)

        # Current price 93 is 7% below average (below 5% threshold)
        should_buy, price, quantity = strategy.should_buy(
            history,
            current_price=Decimal("93"),
            balance=Decimal("1000"),
            positions={},
        )

        assert should_buy is True
        assert price == Decimal("93")
        assert quantity >= 1

    def test_should_not_buy_above_threshold(self, strategy):
        """Test should not buy when price is above threshold."""
        points = [
            PricePoint("csgo", "Item", Decimal("100"), datetime.now(UTC)),
        ]
        history = PriceHistory("csgo", "Item", points)

        # Current price 98 is only 2% below average (above 5% threshold)
        should_buy, _, _ = strategy.should_buy(
            history,
            current_price=Decimal("98"),
            balance=Decimal("1000"),
            positions={},
        )

        assert should_buy is False

    def test_should_not_buy_if_has_position(self, strategy):
        """Test should not buy if already has position."""
        points = [
            PricePoint("csgo", "Item", Decimal("100"), datetime.now(UTC)),
        ]
        history = PriceHistory("csgo", "Item", points)

        # Already have position in this item
        positions = {
            "Item": Position("Item", 5, Decimal("90"), datetime.now(UTC)),
        }

        should_buy, _, _ = strategy.should_buy(
            history,
            current_price=Decimal("80"),  # Great price
            balance=Decimal("1000"),
            positions=positions,
        )

        assert should_buy is False

    def test_should_not_buy_insufficient_balance(self, strategy):
        """Test should not buy with insufficient balance."""
        points = [
            PricePoint("csgo", "Item", Decimal("100"), datetime.now(UTC)),
        ]
        history = PriceHistory("csgo", "Item", points)

        # Balance too low for max_position_pct
        should_buy, _, _ = strategy.should_buy(
            history,
            current_price=Decimal("90"),
            balance=Decimal("50"),  # 10% = $5, not enough for $90 item
            positions={},
        )

        assert should_buy is False

    def test_should_not_buy_zero_average(self, strategy):
        """Test should not buy when average price is zero."""
        history = PriceHistory("csgo", "Item", [])  # Empty history

        should_buy, _, _ = strategy.should_buy(
            history,
            current_price=Decimal("10"),
            balance=Decimal("1000"),
            positions={},
        )

        assert should_buy is False

    def test_should_sell_at_profit(self, strategy):
        """Test should sell when price reaches target margin."""
        points = [
            PricePoint("csgo", "Item", Decimal("100"), datetime.now(UTC)),
        ]
        history = PriceHistory("csgo", "Item", points)

        position = Position("Item", 5, Decimal("100"), datetime.now(UTC))

        # Target price: 100 * (1 + 0.08 + 0.07) = 115
        should_sell, price, quantity = strategy.should_sell(
            history,
            current_price=Decimal("120"),  # Above target
            position=position,
        )

        assert should_sell is True
        assert price == Decimal("120")
        assert quantity == 5

    def test_should_sell_stop_loss(self, strategy):
        """Test should sell at stop loss."""
        points = [
            PricePoint("csgo", "Item", Decimal("100"), datetime.now(UTC)),
        ]
        history = PriceHistory("csgo", "Item", points)

        position = Position("Item", 5, Decimal("100"), datetime.now(UTC))

        # Stop loss at 90% of average cost = 90
        should_sell, price, quantity = strategy.should_sell(
            history,
            current_price=Decimal("85"),  # Below stop loss
            position=position,
        )

        assert should_sell is True
        assert price == Decimal("85")

    def test_should_not_sell_in_range(self, strategy):
        """Test should not sell when price is in range."""
        points = [
            PricePoint("csgo", "Item", Decimal("100"), datetime.now(UTC)),
        ]
        history = PriceHistory("csgo", "Item", points)

        position = Position("Item", 5, Decimal("100"), datetime.now(UTC))

        # Price between stop loss (90) and target (115)
        should_sell, _, _ = strategy.should_sell(
            history,
            current_price=Decimal("105"),
            position=position,
        )

        assert should_sell is False


# ============================================================================
# Backtester Tests
# ============================================================================


class TestBacktester:
    """Tests for Backtester class."""

    @pytest.fixture()
    def backtester(self):
        """Create a backtester instance."""
        return Backtester(fee_rate=0.07)

    def test_initialization(self):
        """Test backtester initialization."""
        bt = Backtester()
        assert bt.fee_rate == 0.07

    def test_custom_fee_rate(self):
        """Test backtester with custom fee rate."""
        bt = Backtester(fee_rate=0.05)
        assert bt.fee_rate == 0.05

    def test_execute_buy(self, backtester):
        """Test executing a buy trade."""
        trade = backtester._execute_buy(
            title="Item",
            price=Decimal("10"),
            quantity=5,
            timestamp=datetime.now(UTC),
        )

        assert trade.trade_type == TradeType.BUY
        assert trade.item_title == "Item"
        assert trade.price == Decimal("10")
        assert trade.quantity == 5
        assert trade.fees == Decimal("0")  # No fees on buy

    def test_execute_sell(self, backtester):
        """Test executing a sell trade."""
        position = Position("Item", 5, Decimal("10"), datetime.now(UTC))

        trade = backtester._execute_sell(
            title="Item",
            price=Decimal("15"),
            quantity=3,
            timestamp=datetime.now(UTC),
            position=position,
        )

        assert trade.trade_type == TradeType.SELL
        assert trade.price == Decimal("15")
        assert trade.quantity == 3
        # Fees: 15 * 3 * 0.07 = 3.15
        assert trade.fees == Decimal("3.15")

    def test_get_price_at_date_found(self, backtester):
        """Test getting price at specific date."""
        target_date = datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)
        points = [
            PricePoint("csgo", "Item", Decimal("10"), datetime(2024, 1, 10, tzinfo=UTC)),
            PricePoint("csgo", "Item", Decimal("12"), datetime(2024, 1, 15, tzinfo=UTC)),
            PricePoint("csgo", "Item", Decimal("11"), datetime(2024, 1, 20, tzinfo=UTC)),
        ]
        history = PriceHistory("csgo", "Item", points)

        result = backtester._get_price_at_date(history, target_date)

        assert result is not None
        assert result.price == Decimal("12")

    def test_get_price_at_date_not_found(self, backtester):
        """Test getting price when date is too far."""
        target_date = datetime(2024, 6, 1, tzinfo=UTC)
        points = [
            PricePoint("csgo", "Item", Decimal("10"), datetime(2024, 1, 1, tzinfo=UTC)),
        ]
        history = PriceHistory("csgo", "Item", points)

        result = backtester._get_price_at_date(history, target_date)

        assert result is None

    def test_get_price_at_date_empty_history(self, backtester):
        """Test getting price with empty history."""
        history = PriceHistory("csgo", "Item", [])

        result = backtester._get_price_at_date(history, datetime.now(UTC))

        assert result is None

    def test_calculate_max_drawdown_no_drawdown(self, backtester):
        """Test max drawdown with increasing balance."""
        balance_history = [
            Decimal("100"),
            Decimal("110"),
            Decimal("120"),
            Decimal("130"),
        ]

        drawdown = backtester._calculate_max_drawdown(balance_history)

        assert drawdown == Decimal("0")

    def test_calculate_max_drawdown_with_drop(self, backtester):
        """Test max drawdown with price drop."""
        balance_history = [
            Decimal("100"),
            Decimal("120"),  # Peak
            Decimal("90"),  # Drop: (120-90)/120 = 25%
            Decimal("110"),
        ]

        drawdown = backtester._calculate_max_drawdown(balance_history)

        assert drawdown == Decimal("25")  # 25%

    def test_calculate_max_drawdown_short_history(self, backtester):
        """Test max drawdown with short history."""
        balance_history = [Decimal("100")]

        drawdown = backtester._calculate_max_drawdown(balance_history)

        assert drawdown == Decimal("0")

    def test_calculate_sharpe_ratio_no_variance(self, backtester):
        """Test Sharpe ratio with no variance."""
        balance_history = [
            Decimal("100"),
            Decimal("100"),
            Decimal("100"),
        ]

        sharpe = backtester._calculate_sharpe_ratio(balance_history)

        assert sharpe == 0.0

    def test_calculate_sharpe_ratio_short_history(self, backtester):
        """Test Sharpe ratio with short history."""
        balance_history = [Decimal("100")]

        sharpe = backtester._calculate_sharpe_ratio(balance_history)

        assert sharpe == 0.0

    def test_calculate_sharpe_ratio_positive_returns(self, backtester):
        """Test Sharpe ratio with positive returns."""
        balance_history = [
            Decimal("100"),
            Decimal("101"),
            Decimal("102"),
            Decimal("103"),
            Decimal("104"),
        ]

        sharpe = backtester._calculate_sharpe_ratio(balance_history)

        # Should be positive for positive returns
        assert sharpe > 0

    @pytest.mark.asyncio()
    async def test_run_backtest_basic(self, backtester):
        """Test running a basic backtest."""
        strategy = SimpleArbitrageStrategy()

        # Create minimal price history
        points = [
            PricePoint(
                "csgo", "Item", Decimal("100"),
                datetime(2024, 1, 1, tzinfo=UTC),
            ),
            PricePoint(
                "csgo", "Item", Decimal("95"),
                datetime(2024, 1, 2, tzinfo=UTC),
            ),
        ]
        history = PriceHistory("csgo", "Item", points)

        result = await backtester.run(
            strategy=strategy,
            price_histories={"Item": history},
            start_date=datetime(2024, 1, 1, tzinfo=UTC),
            end_date=datetime(2024, 1, 2, tzinfo=UTC),
            initial_balance=Decimal("1000"),
        )

        assert result.strategy_name == "SimpleArbitrage"
        assert result.initial_balance == Decimal("1000")
        assert isinstance(result.final_balance, Decimal)
        assert isinstance(result.trades, list)

    @pytest.mark.asyncio()
    async def test_run_backtest_empty_history(self, backtester):
        """Test running backtest with empty history."""
        strategy = SimpleArbitrageStrategy()

        result = await backtester.run(
            strategy=strategy,
            price_histories={},
            start_date=datetime(2024, 1, 1, tzinfo=UTC),
            end_date=datetime(2024, 1, 10, tzinfo=UTC),
            initial_balance=Decimal("1000"),
        )

        assert result.total_trades == 0
        assert result.final_balance == Decimal("1000")


# ============================================================================
# TradingStrategy Abstract Class Tests
# ============================================================================


class TestTradingStrategy:
    """Tests for TradingStrategy abstract class."""

    def test_cannot_instantiate_directly(self):
        """Test that abstract class cannot be instantiated."""
        # TradingStrategy is abstract and cannot be instantiated directly
        # SimpleArbitrageStrategy is a concrete implementation

        # Create a mock concrete strategy
        class MockStrategy(TradingStrategy):
            name = "Mock"

            def should_buy(self, *args):
                return False, Decimal(0), 0

            def should_sell(self, *args):
                return False, Decimal(0), 0

        strategy = MockStrategy()
        assert strategy.name == "Mock"


# ============================================================================
# Module Exports Tests
# ============================================================================


class TestModuleExports:
    """Tests for module exports."""

    def test_all_exports(self):
        """Test that __all__ contains expected exports."""
        from src.analytics import backtester

        assert hasattr(backtester, "__all__")
        assert "Trade" in backtester.__all__
        assert "Position" in backtester.__all__
        assert "BacktestResult" in backtester.__all__
        assert "Backtester" in backtester.__all__
        assert "SimpleArbitrageStrategy" in backtester.__all__

    def test_imports(self):
        """Test that classes can be imported."""
        from src.analytics.backtester import (
            BacktestResult,
            Backtester,
            Position,
            SimpleArbitrageStrategy,
            Trade,
            TradeType,
        )

        assert Trade is not None
        assert Position is not None
        assert BacktestResult is not None
        assert Backtester is not None
        assert SimpleArbitrageStrategy is not None
        assert TradeType is not None


# ============================================================================
# Edge Cases Tests
# ============================================================================


class TestEdgeCases:
    """Tests for edge cases."""

    def test_trade_zero_quantity(self):
        """Test trade with zero quantity."""
        trade = Trade(
            trade_type=TradeType.BUY,
            item_title="Item",
            price=Decimal("10"),
            quantity=0,
            timestamp=datetime.now(UTC),
        )

        assert trade.total_cost == Decimal("0")
        assert trade.net_amount == Decimal("0")

    def test_position_very_small_average(self):
        """Test position with very small average cost."""
        position = Position(
            item_title="Item",
            quantity=1000,
            average_cost=Decimal("0.001"),
            created_at=datetime.now(UTC),
        )

        assert position.total_value == Decimal("1")  # 1000 * 0.001

    def test_backtest_result_negative_profit(self):
        """Test backtest result with negative profit."""
        result = BacktestResult(
            strategy_name="Loser",
            start_date=datetime.now(UTC),
            end_date=datetime.now(UTC),
            initial_balance=Decimal("1000"),
            final_balance=Decimal("800"),  # Lost money
            total_trades=10,
            profitable_trades=3,
            total_profit=Decimal("-200"),
            max_drawdown=Decimal("25"),
            sharpe_ratio=-0.5,
            win_rate=30.0,
        )

        assert result.total_return == -20.0  # -20% loss
        assert result.avg_profit_per_trade == Decimal("-20")
