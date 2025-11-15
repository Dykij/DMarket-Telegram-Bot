"""Trading models for DMarket Bot."""

from datetime import datetime

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    String,
)

from src.models.user import Base


class TradingSettings(Base):
    """Trading settings model.

    Stores user's trading preferences and limits.

    Attributes:
        id: Unique identifier
        user_id: Reference to user (telegram_id)
        max_trade_value: Maximum value per single trade
        daily_limit: Maximum daily trading volume
        min_profit_percent: Minimum profit percentage to execute trade
        strategy: Trading strategy (conservative, balanced, aggressive)
        auto_trading_enabled: Whether automatic trading is enabled
        games_enabled: JSON list of enabled games for trading
        notifications_enabled: Whether to send trading notifications
        created_at: When settings created
        updated_at: Last settings update
    """

    __tablename__ = "trading_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, unique=True, index=True)
    max_trade_value = Column(Float, default=50.0, nullable=False)
    daily_limit = Column(Float, default=500.0, nullable=False)
    min_profit_percent = Column(Float, default=5.0, nullable=False)
    strategy = Column(String(50), default="balanced", nullable=False)
    auto_trading_enabled = Column(Boolean, default=False, nullable=False)
    games_enabled = Column(JSON, default=lambda: ["csgo"])
    notifications_enabled = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<TradingSettings(user_id={self.user_id}, "
            f"strategy='{self.strategy}', "
            f"auto_enabled={self.auto_trading_enabled})>"
        )

    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "max_trade_value": self.max_trade_value,
            "daily_limit": self.daily_limit,
            "min_profit_percent": self.min_profit_percent,
            "strategy": self.strategy,
            "auto_trading_enabled": self.auto_trading_enabled,
            "games_enabled": self.games_enabled,
            "notifications_enabled": self.notifications_enabled,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class TradeHistory(Base):
    """Trade history model.

    Stores history of all trades executed by users.

    Attributes:
        id: Unique identifier
        user_id: Reference to user (telegram_id)
        trade_type: Type of trade (buy, sell, arbitrage)
        item_title: Title of the item
        price: Price at which trade was executed
        profit: Profit/loss from the trade
        game: Game code
        status: Trade status (pending, completed, failed, cancelled)
        created_at: When trade was initiated
        completed_at: When trade was completed
        metadata: Additional trade metadata (JSON)
    """

    __tablename__ = "trade_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    trade_type = Column(String(50), nullable=False)
    item_title = Column(String(500), nullable=False)
    price = Column(Float, nullable=False)
    profit = Column(Float, default=0.0)
    game = Column(String(50), nullable=False)
    status = Column(String(50), default="pending", nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    metadata = Column(JSON, nullable=True)

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<TradeHistory(user_id={self.user_id}, "
            f"type='{self.trade_type}', "
            f"item='{self.item_title}', "
            f"profit=${self.profit:.2f}, "
            f"status='{self.status}')>"
        )

    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "trade_type": self.trade_type,
            "item_title": self.item_title,
            "price": self.price,
            "profit": self.profit,
            "game": self.game,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "metadata": self.metadata,
        }
