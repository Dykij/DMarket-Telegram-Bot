"""User model for DMarket Bot."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import JSON, BigInteger, Boolean, Column, DateTime, String, Text
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class User(Base):
    """User model.

    Stores information about bot users.

    Attributes:
        id: Unique user identifier (UUID)
        telegram_id: Telegram user ID
        username: Telegram username
        first_name: User's first name
        last_name: User's last name
        language_code: User's language (ru, en, etc.)
        is_active: Whether user is active
        is_admin: Whether user is admin
        is_banned: Whether user is banned
        dmarket_api_key_encrypted: Encrypted DMarket API public key
        dmarket_secret_key_encrypted: Encrypted DMarket API secret key
        created_at: When user first started the bot
        updated_at: Last profile update
        last_activity: Last bot interaction
        notes: Admin notes about the user

    """

    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    language_code = Column(String(10), default="ru")
    is_active = Column(Boolean, default=True, index=True)
    is_admin = Column(Boolean, default=False)
    is_banned = Column(Boolean, default=False, index=True)
    dmarket_api_key_encrypted = Column(Text, nullable=True)
    dmarket_secret_key_encrypted = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text, nullable=True)

    def __repr__(self) -> str:
        """String representation."""
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, username='{self.username}')>"

    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "telegram_id": self.telegram_id,
            "username": self.username,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "language_code": self.language_code,
            "is_active": self.is_active,
            "is_admin": self.is_admin,
            "is_banned": self.is_banned,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_activity": (self.last_activity.isoformat() if self.last_activity else None),
        }


class UserPreferences(Base):
    """User preferences model.

    Stores user's bot preferences and settings.

    Attributes:
        id: Unique identifier
        user_id: Reference to user
        default_game: Default game for searches
        notification_enabled: Enable/disable notifications
        price_alert_enabled: Enable/disable price alerts
        arbitrage_alert_enabled: Enable/disable arbitrage alerts
        min_profit_percent: Minimum profit percent for alerts
        preferred_currency: Preferred currency (USD, EUR)
        timezone: User's timezone
        created_at: When preferences created
        updated_at: Last update

    """

    __tablename__ = "user_preferences"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String(36), nullable=False, index=True)
    default_game = Column(String(50), default="csgo")
    notification_enabled = Column(Boolean, default=True)
    price_alert_enabled = Column(Boolean, default=True)
    arbitrage_alert_enabled = Column(Boolean, default=True)
    min_profit_percent = Column(String(10), default="5.0")
    preferred_currency = Column(String(10), default="USD")
    timezone = Column(String(50), default="UTC")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        """String representation."""
        return f"<UserPreferences(user_id={self.user_id}, game='{self.default_game}')>"

    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "default_game": self.default_game,
            "notification_enabled": self.notification_enabled,
            "price_alert_enabled": self.price_alert_enabled,
            "arbitrage_alert_enabled": self.arbitrage_alert_enabled,
            "min_profit_percent": float(self.min_profit_percent),
            "preferred_currency": self.preferred_currency,
            "timezone": self.timezone,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class PriceAlert(Base):
    """Price alert model.

    Stores user's price alerts for items.

    Attributes:
        id: Unique identifier
        user_id: Reference to user
        item_id: DMarket item ID
        market_hash_name: Item name
        game: Game code
        target_price: Target price for alert
        condition: Alert condition (above, below, equals)
        is_active: Whether alert is active
        triggered: Whether alert was triggered
        triggered_at: When alert was triggered
        created_at: When alert created
        expires_at: When alert expires

    """

    __tablename__ = "price_alerts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String(36), nullable=False, index=True)
    item_id = Column(String(255), nullable=True)
    market_hash_name = Column(String(500), nullable=False)
    game = Column(String(50), nullable=False)
    target_price = Column(String(20), nullable=False)
    condition = Column(String(20), default="below")
    is_active = Column(Boolean, default=True, index=True)
    triggered = Column(Boolean, default=False)
    triggered_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<PriceAlert(user_id={self.user_id}, "
            f"item='{self.market_hash_name}', "
            f"price=${self.target_price}, condition='{self.condition}')>"
        )

    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "item_id": self.item_id,
            "market_hash_name": self.market_hash_name,
            "game": self.game,
            "target_price": float(self.target_price),
            "condition": self.condition,
            "is_active": self.is_active,
            "triggered": self.triggered,
            "triggered_at": (self.triggered_at.isoformat() if self.triggered_at else None),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }


class MarketDataCache(Base):
    """Market data cache model.

    Stores cached market data to reduce API calls.

    Attributes:
        id: Unique identifier
        cache_key: Unique cache key (game, item, type)
        game: Game code
        item_hash_name: Item name
        data_type: Type of data (price, history, aggregated)
        data: JSON data
        created_at: When cached
        expires_at: When cache expires

    """

    __tablename__ = "market_data_cache"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    cache_key = Column(String(500), unique=True, nullable=False, index=True)
    game = Column(String(50), nullable=False, index=True)
    item_hash_name = Column(String(500), nullable=True)
    data_type = Column(String(50), nullable=False)
    data = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<MarketDataCache(key='{self.cache_key}', "
            f"type='{self.data_type}', expires={self.expires_at})>"
        )

    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "cache_key": self.cache_key,
            "game": self.game,
            "item_hash_name": self.item_hash_name,
            "data_type": self.data_type,
            "data": self.data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }
