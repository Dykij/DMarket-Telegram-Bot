"""Tests for auto_trader module.

This module tests the AutoTrader class and related components
for automatic trading functionality.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.dmarket.auto_trader import (
    AutoTrader,
    RiskConfig,
    TradeResult,
)


class TestRiskConfig:
    """Tests for RiskConfig class."""

    def test_init(self):
        """Test RiskConfig initialization."""
        config = RiskConfig(
            level="medium",
            max_trades=5,
            max_price=50.0,
            min_profit=0.5,
            balance=100.0,
        )

        assert config.level == "medium"
        assert config.max_trades == 5
        assert config.max_price == 50.0
        assert config.min_profit == 0.5
        assert config.balance == 100.0

    def test_from_level_low(self):
        """Test low risk configuration."""
        config = RiskConfig.from_level(
            level="low",
            max_trades=10,
            max_price=100.0,
            min_profit=0.5,
            balance=100.0,
        )

        assert config.level == "low"
        assert config.max_trades <= 2  # Low risk limits trades
        assert config.max_price <= 20.0  # Low risk limits price
        assert config.min_profit >= 1.0  # Low risk requires higher profit

    def test_from_level_medium(self):
        """Test medium risk configuration."""
        config = RiskConfig.from_level(
            level="medium",
            max_trades=10,
            max_price=100.0,
            min_profit=0.3,
            balance=100.0,
        )

        assert config.level == "medium"
        assert config.max_trades <= 5
        assert config.max_price <= 50.0
        assert config.min_profit >= 0.5

    def test_from_level_high(self):
        """Test high risk configuration."""
        config = RiskConfig.from_level(
            level="high",
            max_trades=10,
            max_price=100.0,
            min_profit=0.3,
            balance=100.0,
        )

        assert config.level == "high"
        # High risk keeps original values or slightly reduced


class TestTradeResult:
    """Tests for TradeResult class."""

    def test_success_result(self):
        """Test successful trade result."""
        result = TradeResult(
            success=True,
            item_name="AK-47 | Redline",
            buy_price=10.0,
            sell_price=12.0,
            profit=1.76,
            error=None,
        )

        assert result.success is True
        assert result.item_name == "AK-47 | Redline"
        assert result.profit == 1.76
        assert result.error is None

    def test_failed_result(self):
        """Test failed trade result."""
        result = TradeResult(
            success=False,
            item_name="M4A4 | Howl",
            buy_price=0,
            sell_price=0,
            profit=0,
            error="Insufficient balance",
        )

        assert result.success is False
        assert result.error == "Insufficient balance"


class TestAutoTrader:
    """Tests for AutoTrader class."""

    @pytest.fixture
    def mock_trader(self):
        """Create mock ArbitrageTrader."""
        trader = MagicMock()
        trader.check_balance = AsyncMock(return_value=(True, 100.0))
        trader.scan_market = AsyncMock(return_value=[])
        trader.execute_trade = AsyncMock(return_value={"success": True})
        return trader

    @pytest.fixture
    def auto_trader(self, mock_trader):
        """Create AutoTrader with mocked dependencies."""
        with patch("src.dmarket.auto_trader.ArbitrageTrader", return_value=mock_trader):
            return AutoTrader(public_key="test", secret_key="test")

    def test_init(self, auto_trader):
        """Test AutoTrader initialization."""
        assert auto_trader is not None
        assert hasattr(auto_trader, "is_running")

    def test_default_state(self, auto_trader):
        """Test default state is not running."""
        assert auto_trader.is_running is False

    @pytest.mark.asyncio
    async def test_start(self, auto_trader):
        """Test starting auto trader."""
        # Start should set is_running to True
        await auto_trader.start()
        assert auto_trader.is_running is True

    @pytest.mark.asyncio
    async def test_stop(self, auto_trader):
        """Test stopping auto trader."""
        auto_trader.is_running = True
        await auto_trader.stop()
        assert auto_trader.is_running is False

    @pytest.mark.asyncio
    async def test_get_status(self, auto_trader):
        """Test getting status."""
        status = await auto_trader.get_status()
        assert isinstance(status, dict)
        assert "is_running" in status

    @pytest.mark.asyncio
    async def test_validate_config(self, auto_trader):
        """Test config validation."""
        config = RiskConfig(
            level="medium",
            max_trades=5,
            max_price=50.0,
            min_profit=0.5,
            balance=100.0,
        )

        is_valid = auto_trader._validate_config(config)
        assert isinstance(is_valid, bool)

    @pytest.mark.asyncio
    async def test_run_iteration(self, auto_trader, mock_trader):
        """Test single trading iteration."""
        mock_trader.scan_market = AsyncMock(return_value=[
            {
                "name": "Test Item",
                "buy_price": 10.0,
                "sell_price": 12.0,
                "profit": 1.76,
            }
        ])

        result = await auto_trader._run_iteration()
        assert result is not None

    @pytest.mark.asyncio
    async def test_handle_error(self, auto_trader):
        """Test error handling."""
        error = Exception("Test error")
        # Should not raise
        await auto_trader._handle_error(error)
