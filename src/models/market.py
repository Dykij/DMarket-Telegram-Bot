"""Market data models."""

from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import JSON, Column, DateTime, Float, Integer, String, Text

from src.models.base import Base, UUIDType


class MarketData(Base):
    """Market data model."""

    __tablename__ = "market_data"

    id = Column(UUIDType, primary_key=True, default=uuid4)
    item_id = Column(String(255), nullable=False, index=True)
    game = Column(String(100), nullable=False, index=True)
    item_name = Column(Text, nullable=False)
    price_usd = Column(Float, nullable=False)
    price_change_24h = Column(Float)
    volume_24h = Column(Integer)
    market_cap = Column(Float)
    data_source = Column(String(50), default="dmarket")
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, index=True)


class MarketDataCache(Base):
    """Market data cache model.

    Stores cached market data to reduce API calls.
    """

    __tablename__ = "market_data_cache"

    id = Column(UUIDType, primary_key=True, default=uuid4)
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
            f"game='{self.game}', type='{self.data_type}')>"
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "id": str(self.id),
            "cache_key": self.cache_key,
            "game": self.game,
            "item_hash_name": self.item_hash_name,
            "data_type": self.data_type,
            "data": self.data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }
