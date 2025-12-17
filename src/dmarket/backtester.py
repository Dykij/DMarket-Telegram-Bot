"""Backtesting system for DMarket trading strategies.

Provides historical simulation of trading strategies:
- Load historical price data
- Simulate trades based on strategy rules
- Calculate performance metrics (ROI, Sharpe ratio, max drawdown)
- Compare multiple strategies

Part of P1-22: Backtesting system for trading strategies.

Usage:
    ```python
    from src.dmarket.backtester import Backtester, SimpleArbitrageStrategy

    # Create backtester with historical data
    backtester = Backtester(initial_balance=1000.0)

    # Load historical data
    await backtester.load_historical_data(
        game="csgo",
        start_date=datetime(2025, 1, 1),
        end_date=datetime(2025, 6, 1)
    )

    # Run backtest with strategy
    strategy = SimpleArbitrageStrategy(min_profit_percent=10.0)
    results = await backtester.run(strategy)

    # Analyze results
    print(f"Total ROI: {results.total_roi:.2f}%")
    print(f"Sharpe Ratio: {results.sharpe_ratio:.2f}")
    print(f"Max Drawdown: {results.max_drawdown:.2f}%")
    ```
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
import logging
from typing import TYPE_CHECKING, Any

import numpy as np


if TYPE_CHECKING:
    from collections.abc import Sequence


logger = logging.getLogger(__name__)


class TradeAction(str, Enum):
    """Trade action type."""

    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


class TradeStatus(str, Enum):
    """Status of a simulated trade."""

    OPEN = "open"
    CLOSED = "closed"
    CANCELLED = "cancelled"


@dataclass
class PricePoint:
    """Historical price data point.

    Attributes:
        timestamp: Time of the price
        item_id: Unique item identifier
        item_name: Human-readable item name
        price: Price in USD
        volume: Number of items traded at this price
        min_price: Minimum price in period
        max_price: Maximum price in period
        avg_price: Average price in period
    """

    timestamp: datetime
    item_id: str
    item_name: str
    price: float
    volume: int = 0
    min_price: float | None = None
    max_price: float | None = None
    avg_price: float | None = None


@dataclass
class SimulatedTrade:
    """A simulated trade in backtesting.

    Attributes:
        trade_id: Unique trade identifier
        item_id: Item being traded
        item_name: Human-readable name
        action: Buy or sell
        price: Trade price
        quantity: Number of items
        timestamp: When trade occurred
        status: Trade status
        fees: Trading fees
        profit: Profit/loss (for closed trades)
        close_price: Price when trade was closed
        close_timestamp: When trade was closed
    """

    trade_id: str
    item_id: str
    item_name: str
    action: TradeAction
    price: float
    quantity: int
    timestamp: datetime
    status: TradeStatus = TradeStatus.OPEN
    fees: float = 0.0
    profit: float | None = None
    close_price: float | None = None
    close_timestamp: datetime | None = None

    @property
    def total_cost(self) -> float:
        """Total cost including fees."""
        return (self.price * self.quantity) + self.fees

    def close(self, close_price: float, timestamp: datetime) -> None:
        """Close the trade and calculate profit.

        Args:
            close_price: Price at which trade is closed
            timestamp: When trade is closed
        """
        self.status = TradeStatus.CLOSED
        self.close_price = close_price
        self.close_timestamp = timestamp

        if self.action == TradeAction.BUY:
            # Profit = sell price - buy price - fees
            sell_fees = close_price * self.quantity * 0.07  # 7% DMarket fee
            self.profit = (close_price * self.quantity) - self.total_cost - sell_fees
        else:
            # Short selling (buy back)
            buy_fees = close_price * self.quantity * 0.07
            self.profit = self.total_cost - (close_price * self.quantity) - buy_fees


@dataclass
class BacktestResults:
    """Results of a backtest run.

    Attributes:
        strategy_name: Name of the strategy tested
        start_date: Start of backtest period
        end_date: End of backtest period
        initial_balance: Starting balance
        final_balance: Ending balance
        total_trades: Number of trades executed
        winning_trades: Number of profitable trades
        losing_trades: Number of unprofitable trades
        total_roi: Total return on investment (%)
        avg_trade_roi: Average ROI per trade
        max_drawdown: Maximum drawdown (%)
        sharpe_ratio: Risk-adjusted return
        win_rate: Percentage of winning trades
        avg_profit: Average profit per trade
        avg_loss: Average loss per trade
        profit_factor: Gross profits / Gross losses
        trades: List of all trades
        equity_curve: Balance over time
    """

    strategy_name: str
    start_date: datetime
    end_date: datetime
    initial_balance: float
    final_balance: float
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    total_roi: float = 0.0
    avg_trade_roi: float = 0.0
    max_drawdown: float = 0.0
    sharpe_ratio: float = 0.0
    win_rate: float = 0.0
    avg_profit: float = 0.0
    avg_loss: float = 0.0
    profit_factor: float = 0.0
    trades: list[SimulatedTrade] = field(default_factory=list)
    equity_curve: list[tuple[datetime, float]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert results to dictionary."""
        return {
            "strategy_name": self.strategy_name,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "initial_balance": self.initial_balance,
            "final_balance": self.final_balance,
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "losing_trades": self.losing_trades,
            "total_roi": round(self.total_roi, 2),
            "avg_trade_roi": round(self.avg_trade_roi, 2),
            "max_drawdown": round(self.max_drawdown, 2),
            "sharpe_ratio": round(self.sharpe_ratio, 2),
            "win_rate": round(self.win_rate, 2),
            "avg_profit": round(self.avg_profit, 2),
            "avg_loss": round(self.avg_loss, 2),
            "profit_factor": round(self.profit_factor, 2),
        }


class TradingStrategy(ABC):
    """Abstract base class for trading strategies.

    Subclass this to implement custom trading strategies for backtesting.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Strategy name."""
        ...

    @abstractmethod
    def evaluate(
        self,
        current_price: PricePoint,
        historical_prices: Sequence[PricePoint],
        open_positions: list[SimulatedTrade],
        balance: float,
    ) -> tuple[TradeAction, float | None, str | None]:
        """Evaluate strategy and decide on action.

        Args:
            current_price: Current price data
            historical_prices: Recent price history
            open_positions: Currently open positions
            balance: Available balance

        Returns:
            Tuple of (action, price_to_use, reason)
            - action: TradeAction.BUY, SELL, or HOLD
            - price_to_use: Price for the trade (None for HOLD)
            - reason: Explanation for the decision
        """
        ...

    def should_close_position(
        self,
        position: SimulatedTrade,
        current_price: PricePoint,
    ) -> tuple[bool, str]:
        """Check if a position should be closed.

        Args:
            position: Open position to evaluate
            current_price: Current price data

        Returns:
            Tuple of (should_close, reason)
        """
        return False, ""


class SimpleArbitrageStrategy(TradingStrategy):
    """Simple arbitrage strategy based on price difference.

    Buys when current price is significantly below recent average,
    sells when price is above target profit margin.

    Attributes:
        min_profit_percent: Minimum profit target (default: 10%)
        max_loss_percent: Maximum loss before closing (default: 5%)
        lookback_periods: Number of periods for price average
        buy_threshold_percent: Buy when price is X% below average
    """

    def __init__(
        self,
        min_profit_percent: float = 10.0,
        max_loss_percent: float = 5.0,
        lookback_periods: int = 10,
        buy_threshold_percent: float = 5.0,
    ) -> None:
        """Initialize strategy.

        Args:
            min_profit_percent: Target profit percentage
            max_loss_percent: Stop-loss percentage
            lookback_periods: Periods to look back for average
            buy_threshold_percent: Buy threshold below average
        """
        self.min_profit_percent = min_profit_percent
        self.max_loss_percent = max_loss_percent
        self.lookback_periods = lookback_periods
        self.buy_threshold_percent = buy_threshold_percent

    @property
    def name(self) -> str:
        """Strategy name."""
        return f"SimpleArbitrage(profit={self.min_profit_percent}%)"

    def evaluate(
        self,
        current_price: PricePoint,
        historical_prices: Sequence[PricePoint],
        open_positions: list[SimulatedTrade],
        balance: float,
    ) -> tuple[TradeAction, float | None, str | None]:
        """Evaluate if we should buy at current price.

        Args:
            current_price: Current price data
            historical_prices: Recent price history
            open_positions: Currently open positions
            balance: Available balance

        Returns:
            Trade decision tuple
        """
        if len(historical_prices) < self.lookback_periods:
            return TradeAction.HOLD, None, "Insufficient history"

        # Calculate average of recent prices
        recent_prices = [p.price for p in historical_prices[-self.lookback_periods :]]
        avg_price = sum(recent_prices) / len(recent_prices)

        # Check if current price is below threshold
        price_diff_percent = ((avg_price - current_price.price) / avg_price) * 100

        if price_diff_percent >= self.buy_threshold_percent:
            # Check if we have enough balance
            cost = current_price.price * 1.07  # Include fees
            if balance >= cost:
                return (
                    TradeAction.BUY,
                    current_price.price,
                    f"Price {price_diff_percent:.1f}% below average",
                )
            return TradeAction.HOLD, None, "Insufficient balance"

        return TradeAction.HOLD, None, f"Price only {price_diff_percent:.1f}% below avg"

    def should_close_position(
        self,
        position: SimulatedTrade,
        current_price: PricePoint,
    ) -> tuple[bool, str]:
        """Check if position should be closed.

        Args:
            position: Open position
            current_price: Current price

        Returns:
            Tuple of (should_close, reason)
        """
        if position.action != TradeAction.BUY:
            return False, ""

        # Calculate potential profit/loss
        profit_percent = (
            (current_price.price - position.price) / position.price
        ) * 100

        # Close at profit target
        if profit_percent >= self.min_profit_percent:
            return True, f"Profit target reached: {profit_percent:.1f}%"

        # Close at stop-loss
        if profit_percent <= -self.max_loss_percent:
            return True, f"Stop-loss triggered: {profit_percent:.1f}%"

        return False, ""


class MomentumStrategy(TradingStrategy):
    """Momentum-based trading strategy.

    Buys when price is trending upward, sells when momentum reverses.

    Attributes:
        momentum_periods: Periods for momentum calculation
        momentum_threshold: Minimum momentum to trigger buy
        profit_target: Target profit percentage
        stop_loss: Stop-loss percentage
    """

    def __init__(
        self,
        momentum_periods: int = 5,
        momentum_threshold: float = 3.0,
        profit_target: float = 8.0,
        stop_loss: float = 4.0,
    ) -> None:
        """Initialize strategy.

        Args:
            momentum_periods: Periods for momentum calculation
            momentum_threshold: Minimum momentum percentage
            profit_target: Target profit percentage
            stop_loss: Stop-loss percentage
        """
        self.momentum_periods = momentum_periods
        self.momentum_threshold = momentum_threshold
        self.profit_target = profit_target
        self.stop_loss = stop_loss

    @property
    def name(self) -> str:
        """Strategy name."""
        return f"Momentum(threshold={self.momentum_threshold}%)"

    def evaluate(
        self,
        current_price: PricePoint,
        historical_prices: Sequence[PricePoint],
        open_positions: list[SimulatedTrade],
        balance: float,
    ) -> tuple[TradeAction, float | None, str | None]:
        """Evaluate momentum signal.

        Args:
            current_price: Current price data
            historical_prices: Recent price history
            open_positions: Currently open positions
            balance: Available balance

        Returns:
            Trade decision tuple
        """
        if len(historical_prices) < self.momentum_periods:
            return TradeAction.HOLD, None, "Insufficient history"

        # Calculate momentum as price change over period
        old_price = historical_prices[-self.momentum_periods].price
        momentum = ((current_price.price - old_price) / old_price) * 100

        if momentum >= self.momentum_threshold:
            cost = current_price.price * 1.07
            if balance >= cost:
                return (
                    TradeAction.BUY,
                    current_price.price,
                    f"Positive momentum: {momentum:.1f}%",
                )
            return TradeAction.HOLD, None, "Insufficient balance"

        return TradeAction.HOLD, None, f"Momentum {momentum:.1f}% below threshold"

    def should_close_position(
        self,
        position: SimulatedTrade,
        current_price: PricePoint,
    ) -> tuple[bool, str]:
        """Check if position should be closed."""
        if position.action != TradeAction.BUY:
            return False, ""

        profit_percent = (
            (current_price.price - position.price) / position.price
        ) * 100

        if profit_percent >= self.profit_target:
            return True, f"Profit target: {profit_percent:.1f}%"

        if profit_percent <= -self.stop_loss:
            return True, f"Stop-loss: {profit_percent:.1f}%"

        return False, ""


class MeanReversionStrategy(TradingStrategy):
    """Mean reversion trading strategy.

    Assumes prices will revert to mean over time.
    Buys when price is significantly below mean, sells when above.

    Attributes:
        lookback_periods: Periods for mean calculation
        std_threshold: Standard deviations from mean for entry
        profit_target: Target profit percentage
        stop_loss: Stop-loss percentage
    """

    def __init__(
        self,
        lookback_periods: int = 20,
        std_threshold: float = 2.0,
        profit_target: float = 10.0,
        stop_loss: float = 5.0,
    ) -> None:
        """Initialize strategy.

        Args:
            lookback_periods: Periods for mean calculation
            std_threshold: Standard deviations for entry signal
            profit_target: Target profit percentage
            stop_loss: Stop-loss percentage
        """
        self.lookback_periods = lookback_periods
        self.std_threshold = std_threshold
        self.profit_target = profit_target
        self.stop_loss = stop_loss

    @property
    def name(self) -> str:
        """Strategy name."""
        return f"MeanReversion(std={self.std_threshold}σ)"

    def evaluate(
        self,
        current_price: PricePoint,
        historical_prices: Sequence[PricePoint],
        open_positions: list[SimulatedTrade],
        balance: float,
    ) -> tuple[TradeAction, float | None, str | None]:
        """Evaluate mean reversion signal.

        Args:
            current_price: Current price data
            historical_prices: Recent price history
            open_positions: Currently open positions
            balance: Available balance

        Returns:
            Trade decision tuple
        """
        if len(historical_prices) < self.lookback_periods:
            return TradeAction.HOLD, None, "Insufficient history"

        # Calculate mean and standard deviation
        prices = [p.price for p in historical_prices[-self.lookback_periods :]]
        mean = sum(prices) / len(prices)
        std = (sum((p - mean) ** 2 for p in prices) / len(prices)) ** 0.5

        if std == 0:
            return TradeAction.HOLD, None, "No price variation"

        # Calculate z-score
        z_score = (current_price.price - mean) / std

        if z_score <= -self.std_threshold:
            cost = current_price.price * 1.07
            if balance >= cost:
                return (
                    TradeAction.BUY,
                    current_price.price,
                    f"Price {abs(z_score):.1f}σ below mean",
                )
            return TradeAction.HOLD, None, "Insufficient balance"

        return TradeAction.HOLD, None, f"Z-score: {z_score:.1f}σ"

    def should_close_position(
        self,
        position: SimulatedTrade,
        current_price: PricePoint,
    ) -> tuple[bool, str]:
        """Check if position should be closed."""
        if position.action != TradeAction.BUY:
            return False, ""

        profit_percent = (
            (current_price.price - position.price) / position.price
        ) * 100

        if profit_percent >= self.profit_target:
            return True, f"Profit target: {profit_percent:.1f}%"

        if profit_percent <= -self.stop_loss:
            return True, f"Stop-loss: {profit_percent:.1f}%"

        return False, ""


@dataclass
class HistoricalDataSet:
    """Container for historical price data.

    Attributes:
        item_id: Item identifier
        item_name: Item name
        game: Game code
        prices: List of price points
        start_date: Start of data range
        end_date: End of data range
    """

    item_id: str
    item_name: str
    game: str
    prices: list[PricePoint] = field(default_factory=list)
    start_date: datetime | None = None
    end_date: datetime | None = None

    def add_price(self, price_point: PricePoint) -> None:
        """Add a price point to the dataset."""
        self.prices.append(price_point)
        if self.start_date is None or price_point.timestamp < self.start_date:
            self.start_date = price_point.timestamp
        if self.end_date is None or price_point.timestamp > self.end_date:
            self.end_date = price_point.timestamp


class Backtester:
    """Backtesting engine for trading strategies.

    Simulates trading strategies on historical data to evaluate
    performance without risking real money.

    Attributes:
        initial_balance: Starting balance for simulation
        current_balance: Current simulation balance
        fee_percent: Trading fee percentage (default: 7% for DMarket)
        data: Historical price data
        trades: List of executed trades
        open_positions: Currently open positions
    """

    def __init__(
        self,
        initial_balance: float = 1000.0,
        fee_percent: float = 7.0,
    ) -> None:
        """Initialize backtester.

        Args:
            initial_balance: Starting balance in USD
            fee_percent: Trading fee percentage
        """
        self.initial_balance = initial_balance
        self.current_balance = initial_balance
        self.fee_percent = fee_percent
        self.data: dict[str, HistoricalDataSet] = {}
        self.trades: list[SimulatedTrade] = []
        self.open_positions: list[SimulatedTrade] = []
        self._trade_counter = 0

    def load_data_from_list(
        self,
        item_id: str,
        item_name: str,
        game: str,
        prices: list[dict[str, Any]],
    ) -> None:
        """Load historical data from a list of price dictionaries.

        Args:
            item_id: Item identifier
            item_name: Item name
            game: Game code
            prices: List of price dicts with timestamp, price, volume keys
        """
        dataset = HistoricalDataSet(item_id=item_id, item_name=item_name, game=game)

        for price_data in prices:
            timestamp = price_data.get("timestamp")
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp)
            elif isinstance(timestamp, int | float):
                timestamp = datetime.fromtimestamp(timestamp, tz=UTC)

            price_point = PricePoint(
                timestamp=timestamp,
                item_id=item_id,
                item_name=item_name,
                price=float(price_data.get("price", 0)),
                volume=int(price_data.get("volume", 0)),
                min_price=price_data.get("min_price"),
                max_price=price_data.get("max_price"),
                avg_price=price_data.get("avg_price"),
            )
            dataset.add_price(price_point)

        # Sort by timestamp
        dataset.prices.sort(key=lambda p: p.timestamp)
        self.data[item_id] = dataset

        logger.info(
            "loaded_historical_data",
            extra={
                "item_id": item_id,
                "item_name": item_name,
                "data_points": len(dataset.prices),
            },
        )

    def generate_sample_data(
        self,
        item_id: str,
        item_name: str,
        game: str = "csgo",
        base_price: float = 10.0,
        volatility: float = 0.1,
        num_days: int = 30,
        points_per_day: int = 24,
    ) -> None:
        """Generate synthetic historical data for testing.

        Args:
            item_id: Item identifier
            item_name: Item name
            game: Game code
            base_price: Starting price
            volatility: Price volatility (standard deviation)
            num_days: Number of days of data
            points_per_day: Data points per day
        """
        dataset = HistoricalDataSet(item_id=item_id, item_name=item_name, game=game)

        # Use modern numpy random Generator
        rng = np.random.default_rng()

        current_price = base_price
        start_time = datetime.now(UTC) - timedelta(days=num_days)

        for day in range(num_days):
            for hour in range(points_per_day):
                # Random walk with mean reversion
                change = rng.normal(0, volatility * current_price)
                mean_reversion = (base_price - current_price) * 0.1
                current_price = max(0.01, current_price + change + mean_reversion)

                timestamp = start_time + timedelta(days=day, hours=hour)
                price_point = PricePoint(
                    timestamp=timestamp,
                    item_id=item_id,
                    item_name=item_name,
                    price=round(current_price, 2),
                    volume=int(rng.poisson(5)),
                )
                dataset.add_price(price_point)

        self.data[item_id] = dataset
        logger.info(
            "generated_sample_data",
            extra={
                "item_id": item_id,
                "data_points": len(dataset.prices),
                "base_price": base_price,
            },
        )

    async def run(
        self,
        strategy: TradingStrategy,
        item_id: str | None = None,
        max_positions: int = 5,
    ) -> BacktestResults:
        """Run backtest with given strategy.

        Args:
            strategy: Trading strategy to test
            item_id: Specific item to trade (None = all items)
            max_positions: Maximum concurrent positions

        Returns:
            BacktestResults with performance metrics
        """
        self.current_balance = self.initial_balance
        self.trades = []
        self.open_positions = []
        self._trade_counter = 0

        equity_curve: list[tuple[datetime, float]] = []
        items_to_test = [item_id] if item_id else list(self.data.keys())

        if not items_to_test:
            raise ValueError("No historical data loaded")

        # Get time range from data
        all_timestamps: set[datetime] = set()
        for item in items_to_test:
            if item in self.data:
                for price in self.data[item].prices:
                    all_timestamps.add(price.timestamp)

        sorted_timestamps = sorted(all_timestamps)
        if not sorted_timestamps:
            raise ValueError("No price data available")

        # Simulate trading over time
        historical_prices: dict[str, list[PricePoint]] = {item: [] for item in items_to_test}

        for timestamp in sorted_timestamps:
            # Update historical prices
            for item in items_to_test:
                if item in self.data:
                    current_prices = [
                        p for p in self.data[item].prices if p.timestamp == timestamp
                    ]
                    for price in current_prices:
                        historical_prices[item].append(price)

                        # Check for position closes first
                        self._check_and_close_positions(strategy, price)

                        # Evaluate strategy for new positions
                        if len(self.open_positions) < max_positions:
                            action, price_val, reason = strategy.evaluate(
                                current_price=price,
                                historical_prices=historical_prices[item],
                                open_positions=self.open_positions,
                                balance=self.current_balance,
                            )

                            if action == TradeAction.BUY and price_val is not None:
                                self._execute_buy(price, reason or "")

            # Record equity
            total_equity = self.current_balance + sum(
                pos.price * pos.quantity for pos in self.open_positions
            )
            equity_curve.append((timestamp, total_equity))

        # Close any remaining open positions at last price
        self._close_all_positions(sorted_timestamps[-1])

        # Calculate results
        return self._calculate_results(
            strategy_name=strategy.name,
            start_date=sorted_timestamps[0],
            end_date=sorted_timestamps[-1],
            equity_curve=equity_curve,
        )

    def _execute_buy(self, price_point: PricePoint, reason: str) -> None:
        """Execute a buy trade.

        Args:
            price_point: Current price data
            reason: Reason for the trade
        """
        self._trade_counter += 1
        fees = price_point.price * (self.fee_percent / 100)

        trade = SimulatedTrade(
            trade_id=f"BT-{self._trade_counter:06d}",
            item_id=price_point.item_id,
            item_name=price_point.item_name,
            action=TradeAction.BUY,
            price=price_point.price,
            quantity=1,
            timestamp=price_point.timestamp,
            fees=fees,
        )

        self.current_balance -= trade.total_cost
        self.trades.append(trade)
        self.open_positions.append(trade)

        logger.debug(
            "executed_buy",
            extra={
                "trade_id": trade.trade_id,
                "item_name": trade.item_name,
                "price": trade.price,
                "reason": reason,
            },
        )

    def _check_and_close_positions(
        self,
        strategy: TradingStrategy,
        current_price: PricePoint,
    ) -> None:
        """Check open positions and close if needed.

        Args:
            strategy: Strategy to use for close decision
            current_price: Current price data
        """
        positions_to_close = []

        for position in self.open_positions:
            if position.item_id == current_price.item_id:
                should_close, reason = strategy.should_close_position(
                    position, current_price
                )
                if should_close:
                    positions_to_close.append((position, current_price, reason))

        for position, price, reason in positions_to_close:
            self._close_position(position, price, reason)

    def _close_position(
        self,
        position: SimulatedTrade,
        price_point: PricePoint,
        reason: str,
    ) -> None:
        """Close a position.

        Args:
            position: Position to close
            price_point: Current price
            reason: Reason for closing
        """
        position.close(price_point.price, price_point.timestamp)

        # Add proceeds to balance (minus sell fee)
        sell_fee = price_point.price * position.quantity * (self.fee_percent / 100)
        proceeds = (price_point.price * position.quantity) - sell_fee
        self.current_balance += proceeds

        self.open_positions.remove(position)

        logger.debug(
            "closed_position",
            extra={
                "trade_id": position.trade_id,
                "profit": position.profit,
                "reason": reason,
            },
        )

    def _close_all_positions(self, timestamp: datetime) -> None:
        """Close all open positions at end of backtest.

        Args:
            timestamp: Timestamp for closing
        """
        for position in list(self.open_positions):
            # Get last price for item
            if position.item_id in self.data:
                last_price = self.data[position.item_id].prices[-1]
                self._close_position(position, last_price, "End of backtest")

    def _calculate_results(
        self,
        strategy_name: str,
        start_date: datetime,
        end_date: datetime,
        equity_curve: list[tuple[datetime, float]],
    ) -> BacktestResults:
        """Calculate backtest performance metrics.

        Args:
            strategy_name: Name of strategy tested
            start_date: Start of test period
            end_date: End of test period
            equity_curve: Balance over time

        Returns:
            BacktestResults with all metrics
        """
        closed_trades = [t for t in self.trades if t.status == TradeStatus.CLOSED]

        winning_trades = [t for t in closed_trades if (t.profit or 0) > 0]
        losing_trades = [t for t in closed_trades if (t.profit or 0) < 0]

        sum(t.profit or 0 for t in closed_trades)
        total_roi = ((self.current_balance - self.initial_balance) / self.initial_balance) * 100

        # Calculate win rate
        win_rate = (
            (len(winning_trades) / len(closed_trades) * 100) if closed_trades else 0
        )

        # Calculate average profit/loss
        avg_profit = (
            sum(t.profit or 0 for t in winning_trades) / len(winning_trades)
            if winning_trades
            else 0
        )
        avg_loss = (
            sum(t.profit or 0 for t in losing_trades) / len(losing_trades)
            if losing_trades
            else 0
        )

        # Calculate profit factor
        gross_profit = sum(t.profit or 0 for t in winning_trades)
        gross_loss = abs(sum(t.profit or 0 for t in losing_trades))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("inf")

        # Calculate max drawdown
        max_drawdown = self._calculate_max_drawdown(equity_curve)

        # Calculate Sharpe ratio (simplified)
        sharpe_ratio = self._calculate_sharpe_ratio(equity_curve)

        # Average trade ROI
        avg_trade_roi = (
            sum(
                ((t.profit or 0) / (t.price * t.quantity)) * 100
                for t in closed_trades
            )
            / len(closed_trades)
            if closed_trades
            else 0
        )

        return BacktestResults(
            strategy_name=strategy_name,
            start_date=start_date,
            end_date=end_date,
            initial_balance=self.initial_balance,
            final_balance=self.current_balance,
            total_trades=len(closed_trades),
            winning_trades=len(winning_trades),
            losing_trades=len(losing_trades),
            total_roi=total_roi,
            avg_trade_roi=avg_trade_roi,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            win_rate=win_rate,
            avg_profit=avg_profit,
            avg_loss=avg_loss,
            profit_factor=profit_factor,
            trades=self.trades,
            equity_curve=equity_curve,
        )

    def _calculate_max_drawdown(
        self,
        equity_curve: list[tuple[datetime, float]],
    ) -> float:
        """Calculate maximum drawdown percentage.

        Args:
            equity_curve: Balance over time

        Returns:
            Maximum drawdown as percentage
        """
        if not equity_curve:
            return 0.0

        equities = [e[1] for e in equity_curve]
        peak = equities[0]
        max_drawdown = 0.0

        for equity in equities:
            peak = max(peak, equity)
            drawdown = ((peak - equity) / peak) * 100
            max_drawdown = max(max_drawdown, drawdown)

        return max_drawdown

    def _calculate_sharpe_ratio(
        self,
        equity_curve: list[tuple[datetime, float]],
        risk_free_rate: float = 0.02,
    ) -> float:
        """Calculate Sharpe ratio.

        Args:
            equity_curve: Balance over time
            risk_free_rate: Annual risk-free rate

        Returns:
            Sharpe ratio
        """
        if len(equity_curve) < 2:
            return 0.0

        equities = [e[1] for e in equity_curve]
        returns = []

        for i in range(1, len(equities)):
            if equities[i - 1] > 0:
                ret = (equities[i] - equities[i - 1]) / equities[i - 1]
                returns.append(ret)

        if not returns:
            return 0.0

        avg_return = sum(returns) / len(returns)
        std_return = (sum((r - avg_return) ** 2 for r in returns) / len(returns)) ** 0.5

        if std_return == 0:
            return 0.0

        # Annualize (assume hourly data, ~8760 hours/year)
        annualized_return = avg_return * 8760
        annualized_std = std_return * (8760**0.5)

        return (annualized_return - risk_free_rate) / annualized_std

    def compare_strategies(
        self,
        strategies: list[TradingStrategy],
        item_id: str | None = None,
    ) -> list[BacktestResults]:
        """Compare multiple strategies on same data.

        Args:
            strategies: List of strategies to compare
            item_id: Specific item to trade (None = all items)

        Returns:
            List of results for each strategy
        """
        import asyncio

        results = []
        for strategy in strategies:
            result = asyncio.get_event_loop().run_until_complete(
                self.run(strategy, item_id)
            )
            results.append(result)

        return results

    def get_summary_table(self, results: list[BacktestResults]) -> str:
        """Generate summary comparison table.

        Args:
            results: List of backtest results

        Returns:
            Formatted table string
        """
        header = (
            "| Strategy | ROI | Win Rate | Sharpe | Max DD | Trades |\n"
            "|----------|-----|----------|--------|--------|--------|\n"
        )
        rows = []
        for r in results:
            row = (
                f"| {r.strategy_name[:20]} | {r.total_roi:.1f}% | "
                f"{r.win_rate:.1f}% | {r.sharpe_ratio:.2f} | "
                f"{r.max_drawdown:.1f}% | {r.total_trades} |"
            )
            rows.append(row)

        return header + "\n".join(rows)
