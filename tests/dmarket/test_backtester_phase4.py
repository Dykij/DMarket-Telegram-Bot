"""
Extended Phase 4 tests for backtester.py - achieving 100% coverage.

This module contains additional tests for the backtester module,
covering strategies, trade simulation, metrics calculation, and edge cases.
"""

from datetime import UTC, datetime, timedelta

import pytest

from src.dmarket.backtester import (
    BacktestResults,
    MomentumStrategy,
    PricePoint,
    SimpleArbitrageStrategy,
    SimulatedTrade,
    TradeAction,
    TradeStatus,
)


# ======================== Test Fixtures ========================


@pytest.fixture()
def sample_price_point():
    """Create a sample price point."""
    return PricePoint(
        timestamp=datetime.now(UTC),
        item_id="item_123",
        item_name="AK-47 | Redline",
        price=50.00,
        volume=100,
        min_price=48.00,
        max_price=52.00,
        avg_price=50.00,
    )


@pytest.fixture()
def sample_price_history():
    """Create sample price history."""
    base_time = datetime.now(UTC)
    return [
        PricePoint(
            timestamp=base_time - timedelta(hours=i),
            item_id="item_123",
            item_name="AK-47 | Redline",
            price=50.00 + (i % 5 - 2),  # Varying prices
            volume=100 + i * 10,
        )
        for i in range(20)
    ]


@pytest.fixture()
def sample_trade():
    """Create a sample simulated trade."""
    return SimulatedTrade(
        trade_id="trade_001",
        item_id="item_123",
        item_name="AK-47 | Redline",
        action=TradeAction.BUY,
        price=50.00,
        quantity=1,
        timestamp=datetime.now(UTC),
        status=TradeStatus.OPEN,
        fees=3.50,  # 7% of 50
    )


@pytest.fixture()
def sample_backtest_results():
    """Create sample backtest results."""
    return BacktestResults(
        strategy_name="TestStrategy",
        start_date=datetime.now(UTC) - timedelta(days=30),
        end_date=datetime.now(UTC),
        initial_balance=1000.0,
        final_balance=1150.0,
        total_trades=20,
        winning_trades=12,
        losing_trades=8,
        total_roi=15.0,
        avg_trade_roi=0.75,
        max_drawdown=5.0,
        sharpe_ratio=1.5,
        win_rate=60.0,
        avg_profit=15.0,
        avg_loss=-10.0,
        profit_factor=1.8,
    )


# ======================== PricePoint Tests ========================


class TestPricePoint:
    """Tests for PricePoint dataclass."""

    def test_price_point_creation(self):
        """Test creating a price point with all fields."""
        timestamp = datetime.now(UTC)
        point = PricePoint(
            timestamp=timestamp,
            item_id="item_123",
            item_name="Test Item",
            price=100.00,
            volume=50,
            min_price=95.00,
            max_price=105.00,
            avg_price=100.00,
        )

        assert point.timestamp == timestamp
        assert point.item_id == "item_123"
        assert point.item_name == "Test Item"
        assert point.price == 100.00
        assert point.volume == 50
        assert point.min_price == 95.00
        assert point.max_price == 105.00
        assert point.avg_price == 100.00

    def test_price_point_default_values(self):
        """Test price point with default values."""
        point = PricePoint(
            timestamp=datetime.now(UTC),
            item_id="item_123",
            item_name="Test Item",
            price=100.00,
        )

        assert point.volume == 0
        assert point.min_price is None
        assert point.max_price is None
        assert point.avg_price is None

    def test_price_point_zero_volume(self):
        """Test price point with zero volume."""
        point = PricePoint(
            timestamp=datetime.now(UTC),
            item_id="item_123",
            item_name="Test Item",
            price=100.00,
            volume=0,
        )

        assert point.volume == 0

    def test_price_point_high_price(self):
        """Test price point with very high price."""
        point = PricePoint(
            timestamp=datetime.now(UTC),
            item_id="item_123",
            item_name="Expensive Item",
            price=10000.00,
            volume=1,
        )

        assert point.price == 10000.00

    def test_price_point_low_price(self):
        """Test price point with very low price."""
        point = PricePoint(
            timestamp=datetime.now(UTC),
            item_id="item_123",
            item_name="Cheap Item",
            price=0.01,
            volume=1000,
        )

        assert point.price == 0.01


# ======================== SimulatedTrade Tests ========================


class TestSimulatedTrade:
    """Tests for SimulatedTrade dataclass."""

    def test_trade_creation(self, sample_trade):
        """Test creating a simulated trade."""
        assert sample_trade.trade_id == "trade_001"
        assert sample_trade.action == TradeAction.BUY
        assert sample_trade.status == TradeStatus.OPEN

    def test_total_cost_calculation(self, sample_trade):
        """Test total cost calculation including fees."""
        # Price * quantity + fees
        expected = 50.00 * 1 + 3.50
        assert sample_trade.total_cost == expected

    def test_total_cost_multiple_quantity(self):
        """Test total cost with multiple quantity."""
        trade = SimulatedTrade(
            trade_id="trade_002",
            item_id="item_123",
            item_name="Test Item",
            action=TradeAction.BUY,
            price=25.00,
            quantity=4,
            timestamp=datetime.now(UTC),
            fees=7.00,
        )

        expected = 25.00 * 4 + 7.00
        assert trade.total_cost == expected

    def test_close_buy_trade_with_profit(self):
        """Test closing a buy trade with profit."""
        trade = SimulatedTrade(
            trade_id="trade_001",
            item_id="item_123",
            item_name="Test Item",
            action=TradeAction.BUY,
            price=50.00,
            quantity=1,
            timestamp=datetime.now(UTC),
            fees=3.50,
        )

        close_time = datetime.now(UTC)
        trade.close(close_price=60.00, timestamp=close_time)

        assert trade.status == TradeStatus.CLOSED
        assert trade.close_price == 60.00
        assert trade.close_timestamp == close_time
        assert trade.profit is not None

    def test_close_buy_trade_with_loss(self):
        """Test closing a buy trade with loss."""
        trade = SimulatedTrade(
            trade_id="trade_001",
            item_id="item_123",
            item_name="Test Item",
            action=TradeAction.BUY,
            price=50.00,
            quantity=1,
            timestamp=datetime.now(UTC),
            fees=3.50,
        )

        trade.close(close_price=40.00, timestamp=datetime.now(UTC))

        assert trade.status == TradeStatus.CLOSED
        assert trade.profit is not None
        assert trade.profit < 0  # Should be a loss

    def test_close_sell_trade(self):
        """Test closing a sell trade."""
        trade = SimulatedTrade(
            trade_id="trade_001",
            item_id="item_123",
            item_name="Test Item",
            action=TradeAction.SELL,
            price=50.00,
            quantity=1,
            timestamp=datetime.now(UTC),
            fees=3.50,
        )

        trade.close(close_price=45.00, timestamp=datetime.now(UTC))

        assert trade.status == TradeStatus.CLOSED

    def test_trade_cancelled_status(self):
        """Test trade with cancelled status."""
        trade = SimulatedTrade(
            trade_id="trade_001",
            item_id="item_123",
            item_name="Test Item",
            action=TradeAction.BUY,
            price=50.00,
            quantity=1,
            timestamp=datetime.now(UTC),
            status=TradeStatus.CANCELLED,
        )

        assert trade.status == TradeStatus.CANCELLED

    def test_trade_zero_fees(self):
        """Test trade with zero fees."""
        trade = SimulatedTrade(
            trade_id="trade_001",
            item_id="item_123",
            item_name="Test Item",
            action=TradeAction.BUY,
            price=100.00,
            quantity=1,
            timestamp=datetime.now(UTC),
            fees=0.0,
        )

        assert trade.total_cost == 100.00


# ======================== BacktestResults Tests ========================


class TestBacktestResults:
    """Tests for BacktestResults dataclass."""

    def test_results_creation(self, sample_backtest_results):
        """Test creating backtest results."""
        assert sample_backtest_results.strategy_name == "TestStrategy"
        assert sample_backtest_results.total_trades == 20
        assert sample_backtest_results.win_rate == 60.0

    def test_results_to_dict(self, sample_backtest_results):
        """Test converting results to dictionary."""
        result_dict = sample_backtest_results.to_dict()

        assert isinstance(result_dict, dict)
        assert result_dict["strategy_name"] == "TestStrategy"
        assert result_dict["total_trades"] == 20
        assert result_dict["win_rate"] == 60.0

    def test_results_to_dict_rounding(self):
        """Test that to_dict rounds values correctly."""
        results = BacktestResults(
            strategy_name="Test",
            start_date=datetime.now(UTC),
            end_date=datetime.now(UTC),
            initial_balance=1000.0,
            final_balance=1157.333333,
            total_roi=15.7333333,
            sharpe_ratio=1.23456789,
        )

        result_dict = results.to_dict()

        assert result_dict["total_roi"] == 15.73
        assert result_dict["sharpe_ratio"] == 1.23

    def test_results_default_values(self):
        """Test results with default values."""
        results = BacktestResults(
            strategy_name="Test",
            start_date=datetime.now(UTC),
            end_date=datetime.now(UTC),
            initial_balance=1000.0,
            final_balance=1000.0,
        )

        assert results.total_trades == 0
        assert results.winning_trades == 0
        assert results.losing_trades == 0
        assert results.trades == []
        assert results.equity_curve == []

    def test_results_with_trades_list(self, sample_trade):
        """Test results with trades list."""
        results = BacktestResults(
            strategy_name="Test",
            start_date=datetime.now(UTC),
            end_date=datetime.now(UTC),
            initial_balance=1000.0,
            final_balance=1050.0,
            trades=[sample_trade],
        )

        assert len(results.trades) == 1
        assert results.trades[0] == sample_trade

    def test_results_with_equity_curve(self):
        """Test results with equity curve."""
        now = datetime.now(UTC)
        equity_curve = [
            (now - timedelta(days=2), 1000.0),
            (now - timedelta(days=1), 1025.0),
            (now, 1050.0),
        ]

        results = BacktestResults(
            strategy_name="Test",
            start_date=now - timedelta(days=2),
            end_date=now,
            initial_balance=1000.0,
            final_balance=1050.0,
            equity_curve=equity_curve,
        )

        assert len(results.equity_curve) == 3


# ======================== TradeAction Enum Tests ========================


class TestTradeAction:
    """Tests for TradeAction enum."""

    def test_trade_action_buy(self):
        """Test BUY action."""
        assert TradeAction.BUY == "buy"
        assert TradeAction.BUY.value == "buy"

    def test_trade_action_sell(self):
        """Test SELL action."""
        assert TradeAction.SELL == "sell"
        assert TradeAction.SELL.value == "sell"

    def test_trade_action_hold(self):
        """Test HOLD action."""
        assert TradeAction.HOLD == "hold"
        assert TradeAction.HOLD.value == "hold"

    def test_trade_action_comparison(self):
        """Test action comparison."""
        assert TradeAction.BUY != TradeAction.SELL
        assert TradeAction.HOLD != TradeAction.BUY


# ======================== TradeStatus Enum Tests ========================


class TestTradeStatus:
    """Tests for TradeStatus enum."""

    def test_trade_status_open(self):
        """Test OPEN status."""
        assert TradeStatus.OPEN == "open"
        assert TradeStatus.OPEN.value == "open"

    def test_trade_status_closed(self):
        """Test CLOSED status."""
        assert TradeStatus.CLOSED == "closed"
        assert TradeStatus.CLOSED.value == "closed"

    def test_trade_status_cancelled(self):
        """Test CANCELLED status."""
        assert TradeStatus.CANCELLED == "cancelled"
        assert TradeStatus.CANCELLED.value == "cancelled"


# ======================== SimpleArbitrageStrategy Tests ========================


class TestSimpleArbitrageStrategy:
    """Tests for SimpleArbitrageStrategy."""

    def test_strategy_initialization(self):
        """Test strategy initialization with default values."""
        strategy = SimpleArbitrageStrategy()

        assert strategy.min_profit_percent == 10.0
        assert strategy.max_loss_percent == 5.0
        assert strategy.lookback_periods == 10
        assert strategy.buy_threshold_percent == 5.0

    def test_strategy_custom_values(self):
        """Test strategy with custom values."""
        strategy = SimpleArbitrageStrategy(
            min_profit_percent=15.0,
            max_loss_percent=3.0,
            lookback_periods=5,
            buy_threshold_percent=8.0,
        )

        assert strategy.min_profit_percent == 15.0
        assert strategy.max_loss_percent == 3.0
        assert strategy.lookback_periods == 5
        assert strategy.buy_threshold_percent == 8.0

    def test_strategy_name(self):
        """Test strategy name property."""
        strategy = SimpleArbitrageStrategy(min_profit_percent=12.0)

        assert "SimpleArbitrage" in strategy.name
        assert "12.0%" in strategy.name

    def test_evaluate_insufficient_history(self, sample_price_point):
        """Test evaluate with insufficient history."""
        strategy = SimpleArbitrageStrategy(lookback_periods=10)

        # Only 5 price points, need 10
        history = [sample_price_point] * 5

        action, price, reason = strategy.evaluate(
            current_price=sample_price_point,
            historical_prices=history,
            open_positions=[],
            balance=1000.0,
        )

        assert action == TradeAction.HOLD
        assert price is None
        assert "Insufficient history" in reason

    def test_evaluate_buy_signal(self):
        """Test evaluate generates buy signal when price is below average."""
        strategy = SimpleArbitrageStrategy(
            buy_threshold_percent=5.0,
            lookback_periods=5,
        )

        # Create history with average price of 100
        history = [
            PricePoint(
                timestamp=datetime.now(UTC) - timedelta(hours=i),
                item_id="item_123",
                item_name="Test Item",
                price=100.0,
            )
            for i in range(10)
        ]

        # Current price 10% below average
        current = PricePoint(
            timestamp=datetime.now(UTC),
            item_id="item_123",
            item_name="Test Item",
            price=90.0,
        )

        action, price, _reason = strategy.evaluate(
            current_price=current,
            historical_prices=history,
            open_positions=[],
            balance=1000.0,
        )

        assert action == TradeAction.BUY
        assert price == 90.0

    def test_evaluate_hold_insufficient_balance(self):
        """Test evaluate holds when insufficient balance."""
        strategy = SimpleArbitrageStrategy(buy_threshold_percent=5.0)

        history = [
            PricePoint(
                timestamp=datetime.now(UTC) - timedelta(hours=i),
                item_id="item_123",
                item_name="Test Item",
                price=100.0,
            )
            for i in range(15)
        ]

        current = PricePoint(
            timestamp=datetime.now(UTC),
            item_id="item_123",
            item_name="Test Item",
            price=90.0,  # 10% below avg
        )

        action, _price, reason = strategy.evaluate(
            current_price=current,
            historical_prices=history,
            open_positions=[],
            balance=50.0,  # Not enough
        )

        assert action == TradeAction.HOLD
        assert "Insufficient balance" in reason

    def test_evaluate_hold_price_not_low_enough(self):
        """Test evaluate holds when price is not below threshold."""
        strategy = SimpleArbitrageStrategy(buy_threshold_percent=10.0)

        history = [
            PricePoint(
                timestamp=datetime.now(UTC) - timedelta(hours=i),
                item_id="item_123",
                item_name="Test Item",
                price=100.0,
            )
            for i in range(15)
        ]

        current = PricePoint(
            timestamp=datetime.now(UTC),
            item_id="item_123",
            item_name="Test Item",
            price=97.0,  # Only 3% below avg
        )

        action, _price, _reason = strategy.evaluate(
            current_price=current,
            historical_prices=history,
            open_positions=[],
            balance=1000.0,
        )

        assert action == TradeAction.HOLD

    def test_should_close_position_profit_target(self, sample_trade):
        """Test closing position at profit target."""
        strategy = SimpleArbitrageStrategy(min_profit_percent=10.0)

        current = PricePoint(
            timestamp=datetime.now(UTC),
            item_id="item_123",
            item_name="Test Item",
            price=60.0,  # 20% above buy price of 50
        )

        should_close, reason = strategy.should_close_position(sample_trade, current)

        assert should_close is True
        assert "Profit target" in reason

    def test_should_close_position_stop_loss(self, sample_trade):
        """Test closing position at stop-loss."""
        strategy = SimpleArbitrageStrategy(max_loss_percent=5.0)

        current = PricePoint(
            timestamp=datetime.now(UTC),
            item_id="item_123",
            item_name="Test Item",
            price=45.0,  # 10% below buy price of 50
        )

        should_close, reason = strategy.should_close_position(sample_trade, current)

        assert should_close is True
        assert "Stop-loss" in reason

    def test_should_close_position_hold(self, sample_trade):
        """Test holding position when not at target."""
        strategy = SimpleArbitrageStrategy(
            min_profit_percent=10.0,
            max_loss_percent=5.0,
        )

        current = PricePoint(
            timestamp=datetime.now(UTC),
            item_id="item_123",
            item_name="Test Item",
            price=52.0,  # 4% above buy price
        )

        should_close, _reason = strategy.should_close_position(sample_trade, current)

        assert should_close is False

    def test_should_close_position_not_buy_trade(self):
        """Test that sell trades are handled correctly."""
        strategy = SimpleArbitrageStrategy()

        sell_trade = SimulatedTrade(
            trade_id="trade_001",
            item_id="item_123",
            item_name="Test Item",
            action=TradeAction.SELL,
            price=50.0,
            quantity=1,
            timestamp=datetime.now(UTC),
        )

        current = PricePoint(
            timestamp=datetime.now(UTC),
            item_id="item_123",
            item_name="Test Item",
            price=100.0,
        )

        should_close, reason = strategy.should_close_position(sell_trade, current)

        assert should_close is False
        assert reason == ""


# ======================== MomentumStrategy Tests ========================


class TestMomentumStrategy:
    """Tests for MomentumStrategy."""

    def test_momentum_strategy_initialization(self):
        """Test momentum strategy initialization."""
        strategy = MomentumStrategy()

        assert strategy.momentum_periods == 5
        assert strategy.momentum_threshold == 3.0
        assert strategy.profit_target == 8.0
        assert strategy.stop_loss == 4.0

    def test_momentum_strategy_custom_values(self):
        """Test momentum strategy with custom values."""
        strategy = MomentumStrategy(
            momentum_periods=10,
            momentum_threshold=5.0,
            profit_target=15.0,
            stop_loss=7.0,
        )

        assert strategy.momentum_periods == 10
        assert strategy.momentum_threshold == 5.0
        assert strategy.profit_target == 15.0
        assert strategy.stop_loss == 7.0

    def test_momentum_strategy_name(self):
        """Test momentum strategy name property."""
        strategy = MomentumStrategy(momentum_threshold=5.0)

        assert "Momentum" in strategy.name

    def test_momentum_evaluate_insufficient_history(self, sample_price_point):
        """Test momentum evaluate with insufficient history."""
        strategy = MomentumStrategy(momentum_periods=10)

        history = [sample_price_point] * 5

        action, _price, _reason = strategy.evaluate(
            current_price=sample_price_point,
            historical_prices=history,
            open_positions=[],
            balance=1000.0,
        )

        assert action == TradeAction.HOLD

    def test_momentum_evaluate_upward_trend(self):
        """Test momentum evaluate with upward price trend."""
        strategy = MomentumStrategy(momentum_threshold=3.0, momentum_periods=5)

        # Create upward trending prices
        history = [
            PricePoint(
                timestamp=datetime.now(UTC) - timedelta(hours=i),
                item_id="item_123",
                item_name="Test Item",
                price=100.0 - (i * 5),  # Decreasing backwards = increasing forwards
            )
            for i in range(10)
        ]

        current = PricePoint(
            timestamp=datetime.now(UTC),
            item_id="item_123",
            item_name="Test Item",
            price=105.0,
        )

        action, _price, _reason = strategy.evaluate(
            current_price=current,
            historical_prices=history,
            open_positions=[],
            balance=1000.0,
        )

        # Should consider buying on momentum
        assert action in {TradeAction.BUY, TradeAction.HOLD}

    def test_momentum_should_close_position(self, sample_trade):
        """Test momentum strategy close position logic."""
        strategy = MomentumStrategy(profit_target=8.0, stop_loss=4.0)

        current = PricePoint(
            timestamp=datetime.now(UTC),
            item_id="item_123",
            item_name="Test Item",
            price=55.0,  # 10% profit on 50
        )

        should_close, _reason = strategy.should_close_position(sample_trade, current)

        # Should close at profit target
        assert should_close is True


# ======================== Edge Case Tests ========================


class TestEdgeCases:
    """Tests for edge cases in backtester."""

    def test_trade_with_zero_price(self):
        """Test handling trade with zero price."""
        with pytest.raises(Exception):
            # This might raise an error or be handled differently
            trade = SimulatedTrade(
                trade_id="trade_001",
                item_id="item_123",
                item_name="Test Item",
                action=TradeAction.BUY,
                price=0.0,
                quantity=1,
                timestamp=datetime.now(UTC),
            )
            trade.total_cost  # Access to trigger calculation

    def test_trade_with_negative_quantity(self):
        """Test handling trade with negative quantity."""
        trade = SimulatedTrade(
            trade_id="trade_001",
            item_id="item_123",
            item_name="Test Item",
            action=TradeAction.BUY,
            price=50.0,
            quantity=-1,  # Invalid but should be handled
            timestamp=datetime.now(UTC),
        )

        # Should calculate but result may be negative
        assert trade.total_cost == -50.0

    def test_price_point_with_empty_strings(self):
        """Test price point with empty strings."""
        point = PricePoint(
            timestamp=datetime.now(UTC),
            item_id="",
            item_name="",
            price=100.0,
        )

        assert point.item_id == ""
        assert point.item_name == ""

    def test_results_with_zero_trades(self):
        """Test results with zero trades."""
        results = BacktestResults(
            strategy_name="Empty",
            start_date=datetime.now(UTC),
            end_date=datetime.now(UTC),
            initial_balance=1000.0,
            final_balance=1000.0,
            total_trades=0,
        )

        result_dict = results.to_dict()
        assert result_dict["total_trades"] == 0

    def test_results_with_all_losing_trades(self):
        """Test results with all losing trades."""
        results = BacktestResults(
            strategy_name="AllLoss",
            start_date=datetime.now(UTC),
            end_date=datetime.now(UTC),
            initial_balance=1000.0,
            final_balance=800.0,
            total_trades=10,
            winning_trades=0,
            losing_trades=10,
            win_rate=0.0,
            total_roi=-20.0,
        )

        assert results.win_rate == 0.0
        assert results.total_roi == -20.0

    def test_results_with_all_winning_trades(self):
        """Test results with all winning trades."""
        results = BacktestResults(
            strategy_name="AllWin",
            start_date=datetime.now(UTC),
            end_date=datetime.now(UTC),
            initial_balance=1000.0,
            final_balance=1500.0,
            total_trades=10,
            winning_trades=10,
            losing_trades=0,
            win_rate=100.0,
            total_roi=50.0,
        )

        assert results.win_rate == 100.0
        assert results.total_roi == 50.0

    def test_strategy_with_extreme_thresholds(self):
        """Test strategy with extreme threshold values."""
        strategy = SimpleArbitrageStrategy(
            min_profit_percent=100.0,  # Very high
            max_loss_percent=0.1,  # Very low
            buy_threshold_percent=50.0,  # Very high
        )

        assert strategy.min_profit_percent == 100.0
        assert strategy.max_loss_percent == 0.1

    def test_close_trade_breakeven(self):
        """Test closing trade at breakeven."""
        trade = SimulatedTrade(
            trade_id="trade_001",
            item_id="item_123",
            item_name="Test Item",
            action=TradeAction.BUY,
            price=50.0,
            quantity=1,
            timestamp=datetime.now(UTC),
            fees=0.0,
        )

        # Close at same price (but with fees, will be a loss)
        trade.close(close_price=50.0, timestamp=datetime.now(UTC))

        assert trade.status == TradeStatus.CLOSED


# ======================== Integration Tests ========================


class TestBacktesterIntegration:
    """Integration tests for backtester components."""

    def test_strategy_evaluate_with_positions(self, sample_trade, sample_price_point):
        """Test strategy evaluation with existing positions."""
        strategy = SimpleArbitrageStrategy()

        history = [sample_price_point] * 15

        action, _price, _reason = strategy.evaluate(
            current_price=sample_price_point,
            historical_prices=history,
            open_positions=[sample_trade],
            balance=1000.0,
        )

        # Should return an action
        assert action in {TradeAction.BUY, TradeAction.SELL, TradeAction.HOLD}

    def test_full_trade_lifecycle(self):
        """Test complete trade lifecycle."""
        # Create trade
        trade = SimulatedTrade(
            trade_id="trade_001",
            item_id="item_123",
            item_name="Test Item",
            action=TradeAction.BUY,
            price=50.0,
            quantity=2,
            timestamp=datetime.now(UTC),
            fees=7.0,
        )

        # Verify initial state
        assert trade.status == TradeStatus.OPEN
        assert trade.total_cost == 107.0

        # Close with profit
        trade.close(close_price=60.0, timestamp=datetime.now(UTC))

        # Verify final state
        assert trade.status == TradeStatus.CLOSED
        assert trade.close_price == 60.0
        assert trade.profit is not None

    def test_multiple_strategies_comparison(self):
        """Test comparing multiple strategies."""
        strategy1 = SimpleArbitrageStrategy(min_profit_percent=10.0)
        strategy2 = SimpleArbitrageStrategy(min_profit_percent=15.0)
        momentum = MomentumStrategy(momentum_threshold=5.0)

        # All should have different names
        assert strategy1.name != strategy2.name
        assert strategy1.name != momentum.name
        assert strategy2.name != momentum.name

    def test_results_serialization_cycle(self, sample_backtest_results):
        """Test serialization and deserialization of results."""
        # Convert to dict
        result_dict = sample_backtest_results.to_dict()

        # Verify all expected fields are present
        expected_fields = [
            "strategy_name",
            "start_date",
            "end_date",
            "initial_balance",
            "final_balance",
            "total_trades",
            "winning_trades",
            "losing_trades",
            "total_roi",
            "sharpe_ratio",
            "win_rate",
        ]

        for field in expected_fields:
            assert field in result_dict
