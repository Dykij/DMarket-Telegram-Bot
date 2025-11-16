"""Simple tests for model structure and methods."""

import pytest
from datetime import datetime, timedelta

# Test imports work
from src.models.user import User, UserPreferences, PriceAlert, MarketDataCache
from src.models.target import Target, TradeHistory, TradingSettings
from src.models.trading import TradingSettings as TradingSettings2, TradeHistory as TradeHistory2


class TestModelStructure:
    """Test that models are properly defined."""

    def test_user_model_exists(self):
        """Test User model can be imported and instantiated."""
        user = User(telegram_id=123456, is_active=True, language_code="en")
        assert user.telegram_id == 123456
        assert hasattr(user, 'to_dict')
        assert hasattr(user, '__repr__')

    def test_user_preferences_model_exists(self):
        """Test UserPreferences model can be imported and instantiated."""
        prefs = UserPreferences(user_id="user-123", default_game="csgo", min_profit_percent="5.0")
        assert prefs.user_id == "user-123"
        assert hasattr(prefs, 'to_dict')

    def test_price_alert_model_exists(self):
        """Test PriceAlert model can be imported and instantiated."""
        alert = PriceAlert(
            user_id="user-123",
            market_hash_name="Test Item",
            game="csgo",
            target_price="10.0",
            condition="below",
            is_active=True
        )
        assert alert.user_id == "user-123"
        assert hasattr(alert, 'to_dict')

    def test_market_data_cache_model_exists(self):
        """Test MarketDataCache model can be imported and instantiated."""
        cache = MarketDataCache(
            cache_key="test:key",
            game="csgo",
            data_type="price",
            data={},
            expires_at=datetime.utcnow()
        )
        assert cache.cache_key == "test:key"
        assert hasattr(cache, 'to_dict')

    def test_target_model_exists(self):
        """Test Target model can be imported and instantiated."""
        target = Target(
            user_id=123,
            target_id="target-123",
            game="csgo",
            title="Test Item",
            price=10.0,
            amount=1,
            status="active"
        )
        assert target.user_id == 123
        assert hasattr(target, 'to_dict')

    def test_trade_history_model_exists(self):
        """Test TradeHistory model can be imported and instantiated."""
        trade = TradeHistory(
            user_id=123,
            trade_type="buy",
            item_title="Test Item",
            price=10.0,
            game="csgo",
            status="pending",
            profit=0.0
        )
        assert trade.user_id == 123
        assert hasattr(trade, 'to_dict')

    def test_trading_settings_model_exists(self):
        """Test TradingSettings model can be imported and instantiated."""
        settings = TradingSettings(
            user_id=123,
            max_trade_value=50.0,
            daily_limit=500.0,
            min_profit_percent=5.0,
            strategy="balanced"
        )
        assert settings.user_id == 123
        assert hasattr(settings, 'to_dict')


class TestModelMethods:
    """Test model methods."""

    def test_user_to_dict(self):
        """Test User.to_dict() method."""
        now = datetime.utcnow()
        user = User(telegram_id=123, username="test", is_active=True, language_code="en")
        user.id = "user-id"
        user.created_at = now
        user.updated_at = now
        user.last_activity = now
        
        data = user.to_dict()
        
        assert data["telegram_id"] == 123
        assert data["username"] == "test"
        assert data["created_at"] == now.isoformat()

    def test_user_preferences_to_dict(self):
        """Test UserPreferences.to_dict() method."""
        now = datetime.utcnow()
        prefs = UserPreferences(user_id="user-123", min_profit_percent="7.5")
        prefs.id = "pref-id"
        prefs.created_at = now
        
        data = prefs.to_dict()
        
        assert data["user_id"] == "user-123"
        assert data["min_profit_percent"] == 7.5  # Should convert to float

    def test_price_alert_to_dict(self):
        """Test PriceAlert.to_dict() method."""
        now = datetime.utcnow()
        alert = PriceAlert(
            user_id="user-123",
            market_hash_name="Test",
            game="csgo",
            target_price="25.50",
            condition="below",
            is_active=True,
            triggered=False
        )
        alert.id = "alert-id"
        alert.created_at = now
        
        data = alert.to_dict()
        
        assert data["user_id"] == "user-123"
        assert data["target_price"] == 25.50  # Should convert to float

    def test_target_to_dict(self):
        """Test Target.to_dict() method."""
        now = datetime.utcnow()
        target = Target(
            user_id=123,
            target_id="target-123",
            game="csgo",
            title="Test",
            price=10.0,
            amount=1,
            status="active"
        )
        target.id = 1
        target.created_at = now
        
        data = target.to_dict()
        
        assert data["user_id"] == 123
        assert data["title"] == "Test"
        assert data["price"] == 10.0

    def test_trade_history_to_dict(self):
        """Test TradeHistory.to_dict() method."""
        now = datetime.utcnow()
        trade = TradeHistory(
            user_id=123,
            trade_type="buy",
            item_title="Test",
            price=10.0,
            profit=2.0,
            game="csgo",
            status="completed"
        )
        trade.id = 1
        trade.created_at = now
        
        data = trade.to_dict()
        
        assert data["user_id"] == 123
        assert data["trade_type"] == "buy"
        assert data["profit"] == 2.0

    def test_trading_settings_to_dict(self):
        """Test TradingSettings.to_dict() method."""
        now = datetime.utcnow()
        settings = TradingSettings(
            user_id=123,
            max_trade_value=100.0,
            strategy="aggressive",
            auto_trading_enabled=1,
            games_enabled=["csgo"]
        )
        settings.id = 1
        settings.created_at = now
        
        data = settings.to_dict()
        
        assert data["user_id"] == 123
        assert data["max_trade_value"] == 100.0
        assert data["auto_trading_enabled"] is True  # Should convert to bool


class TestModelRepr:
    """Test model __repr__ methods."""

    def test_user_repr(self):
        """Test User.__repr__() method."""
        user = User(telegram_id=123, username="test", is_active=True)
        user.id = "user-id"
        
        repr_str = repr(user)
        
        assert "User" in repr_str
        assert "123" in repr_str

    def test_target_repr(self):
        """Test Target.__repr__() method."""
        target = Target(
            user_id=123,
            target_id="t-123",
            game="csgo",
            title="Test",
            price=10.0,
            status="active",
            amount=1
        )
        target.id = 1
        
        repr_str = repr(target)
        
        assert "Target" in repr_str
        assert "Test" in repr_str

    def test_trade_history_repr(self):
        """Test TradeHistory.__repr__() method."""
        trade = TradeHistory(
            user_id=123,
            trade_type="buy",
            item_title="Test",
            price=10.0,
            game="csgo",
            status="pending",
            profit=0.0
        )
        trade.id = 1
        
        repr_str = repr(trade)
        
        assert "TradeHistory" in repr_str
        assert "buy" in repr_str


class TestModelTableNames:
    """Test model table names are correct."""

    def test_user_table_name(self):
        """Test User model table name."""
        assert User.__tablename__ == "users"

    def test_user_preferences_table_name(self):
        """Test UserPreferences model table name."""
        assert UserPreferences.__tablename__ == "user_preferences"

    def test_price_alert_table_name(self):
        """Test PriceAlert model table name."""
        assert PriceAlert.__tablename__ == "price_alerts"

    def test_target_table_name(self):
        """Test Target model table name."""
        assert Target.__tablename__ == "targets"

    def test_trade_history_table_name(self):
        """Test TradeHistory model table name."""
        assert TradeHistory.__tablename__ == "trade_history"

    def test_trading_settings_table_name(self):
        """Test TradingSettings model table name."""
        assert TradingSettings.__tablename__ == "trading_settings"
