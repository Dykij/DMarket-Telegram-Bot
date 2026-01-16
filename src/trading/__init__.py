"""Trading module for automated trading.

This module provides:
- Trading automation (stop-loss, take-profit, DCA)
- Auto-rebalancing
- Scheduled tasks
"""

from src.trading.trading_automation import (
    AutoOrder,
    DCAConfig,
    ExecutionResult,
    OrderStatus,
    OrderType,
    RebalanceConfig,
    ScheduledTask,
    TradingAutomation,
    create_trading_automation,
)


__all__ = [
    "AutoOrder",
    "DCAConfig",
    "ExecutionResult",
    "OrderStatus",
    "OrderType",
    "RebalanceConfig",
    "ScheduledTask",
    "TradingAutomation",
    "create_trading_automation",
]
