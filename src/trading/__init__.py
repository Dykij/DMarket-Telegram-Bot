"""Trading module for automated trading.

This module provides:
- Trading automation (stop-loss, take-profit, DCA)
- Auto-rebalancing
- Scheduled tasks
"""

from src.trading.trading_automation import (
    TradingAutomation,
    AutoOrder,
    DCAConfig,
    RebalanceConfig,
    ScheduledTask,
    ExecutionResult,
    OrderType,
    OrderStatus,
    create_trading_automation,
)

__all__ = [
    "TradingAutomation",
    "AutoOrder",
    "DCAConfig",
    "RebalanceConfig",
    "ScheduledTask",
    "ExecutionResult",
    "OrderType",
    "OrderStatus",
    "create_trading_automation",
]
