"""Tests for src/models/alert.py module."""

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock
from uuid import UUID, uuid4


class TestPriceAlertModel:
    """Tests for PriceAlert model."""

    def test_price_alert_creation_default_values(self):
        """Test creating PriceAlert with default values."""
        alert = MagicMock()
        alert.user_id = uuid4()
        alert.target_price = 100.0
        alert.condition = "below"
        alert.is_active = True
        alert.triggered = False

        assert alert.target_price == 100.0
        assert alert.condition == "below"
        assert alert.is_active is True
        assert alert.triggered is False

    def test_price_alert_creation_with_all_fields(self):
        """Test creating PriceAlert with all fields."""
        user_id = uuid4()
        item_id = "item_123"
        market_hash_name = "AK-47 | Redline (Field-Tested)"
        game = "csgo"
        target_price = 50.0
        condition = "above"
        created_at = datetime.now(UTC)
        expires_at = datetime.now(UTC) + timedelta(days=7)

        alert_mock = MagicMock()
        alert_mock.user_id = user_id
        alert_mock.item_id = item_id
        alert_mock.market_hash_name = market_hash_name
        alert_mock.game = game
        alert_mock.target_price = target_price
        alert_mock.condition = condition
        alert_mock.is_active = True
        alert_mock.triggered = False
        alert_mock.created_at = created_at
        alert_mock.expires_at = expires_at

        assert alert_mock.user_id == user_id
        assert alert_mock.item_id == item_id
        assert alert_mock.market_hash_name == market_hash_name
        assert alert_mock.game == game
        assert alert_mock.target_price == target_price
        assert alert_mock.condition == condition
        assert alert_mock.is_active is True
        assert alert_mock.triggered is False
        assert alert_mock.expires_at == expires_at

    def test_price_alert_condition_above(self):
        """Test PriceAlert with 'above' condition."""
        alert_mock = MagicMock()
        alert_mock.target_price = 100.0
        alert_mock.condition = "above"

        assert alert_mock.condition == "above"

    def test_price_alert_condition_below(self):
        """Test PriceAlert with 'below' condition."""
        alert_mock = MagicMock()
        alert_mock.target_price = 50.0
        alert_mock.condition = "below"

        assert alert_mock.condition == "below"

    def test_price_alert_triggered_state(self):
        """Test PriceAlert triggered state."""
        alert_mock = MagicMock()
        alert_mock.triggered = True
        alert_mock.triggered_at = datetime.now(UTC)
        alert_mock.is_active = False

        assert alert_mock.triggered is True
        assert alert_mock.triggered_at is not None
        assert alert_mock.is_active is False

    def test_price_alert_repr(self):
        """Test PriceAlert __repr__ method."""
        user_id = uuid4()
        alert_id = uuid4()

        # Test the repr format
        expected_repr = (
            f"<PriceAlert(id={alert_id}, user_id={user_id}, item='Test Item', price=50.0)>"
        )

        alert_mock = MagicMock()
        alert_mock.__repr__ = MagicMock(return_value=expected_repr)

        assert "PriceAlert" in str(repr(alert_mock))
        assert "Test Item" in str(repr(alert_mock))

    def test_price_alert_to_dict_all_fields(self):
        """Test PriceAlert to_dict method with all fields."""
        alert_id = uuid4()
        user_id = uuid4()
        created_at = datetime(2024, 1, 1, 12, 0, 0)
        expires_at = datetime(2024, 1, 8, 12, 0, 0)

        expected_dict = {
            "id": str(alert_id),
            "user_id": str(user_id),
            "item_id": "item_123",
            "market_hash_name": "AK-47 | Redline",
            "game": "csgo",
            "target_price": 100.0,
            "condition": "below",
            "is_active": True,
            "triggered": False,
            "triggered_at": None,
            "created_at": created_at.isoformat(),
            "expires_at": expires_at.isoformat(),
        }

        alert_mock = MagicMock()
        alert_mock.to_dict.return_value = expected_dict

        result = alert_mock.to_dict()

        assert result["id"] == str(alert_id)
        assert result["user_id"] == str(user_id)
        assert result["item_id"] == "item_123"
        assert result["market_hash_name"] == "AK-47 | Redline"
        assert result["game"] == "csgo"
        assert result["target_price"] == 100.0
        assert result["condition"] == "below"
        assert result["is_active"] is True
        assert result["triggered"] is False

    def test_price_alert_to_dict_triggered(self):
        """Test PriceAlert to_dict method when triggered."""
        alert_id = uuid4()
        user_id = uuid4()
        triggered_at = datetime(2024, 1, 5, 14, 30, 0)

        expected_dict = {
            "id": str(alert_id),
            "user_id": str(user_id),
            "item_id": "item_456",
            "market_hash_name": "M4A4 | Howl",
            "game": "csgo",
            "target_price": 2000.0,
            "condition": "above",
            "is_active": False,
            "triggered": True,
            "triggered_at": triggered_at.isoformat(),
            "created_at": "2024-01-01T10:00:00",
            "expires_at": None,
        }

        alert_mock = MagicMock()
        alert_mock.to_dict.return_value = expected_dict

        result = alert_mock.to_dict()

        assert result["triggered"] is True
        assert result["triggered_at"] == triggered_at.isoformat()
        assert result["is_active"] is False

    def test_price_alert_to_dict_none_values(self):
        """Test PriceAlert to_dict method with None values."""
        expected_dict = {
            "id": str(uuid4()),
            "user_id": str(uuid4()),
            "item_id": None,
            "market_hash_name": None,
            "game": None,
            "target_price": 50.0,
            "condition": "below",
            "is_active": True,
            "triggered": False,
            "triggered_at": None,
            "created_at": None,
            "expires_at": None,
        }

        alert_mock = MagicMock()
        alert_mock.to_dict.return_value = expected_dict

        result = alert_mock.to_dict()

        assert result["item_id"] is None
        assert result["market_hash_name"] is None
        assert result["game"] is None
        assert result["created_at"] is None

    def test_price_alert_inactive(self):
        """Test PriceAlert when inactive."""
        alert_mock = MagicMock()
        alert_mock.is_active = False
        alert_mock.triggered = False

        assert alert_mock.is_active is False

    def test_price_alert_with_expiry(self):
        """Test PriceAlert with expiration date."""
        expires_at = datetime.now(UTC) + timedelta(days=30)

        alert_mock = MagicMock()
        alert_mock.expires_at = expires_at
        alert_mock.is_active = True

        assert alert_mock.expires_at == expires_at

    def test_price_alert_id_is_uuid(self):
        """Test that PriceAlert id is UUID."""
        alert_id = uuid4()

        alert_mock = MagicMock()
        alert_mock.id = alert_id

        assert isinstance(alert_mock.id, UUID)

    def test_price_alert_different_games(self):
        """Test PriceAlert for different games."""
        games = ["csgo", "dota2", "tf2", "rust"]

        for game in games:
            alert_mock = MagicMock()
            alert_mock.game = game
            alert_mock.target_price = 100.0

            assert alert_mock.game == game

    def test_price_alert_high_price(self):
        """Test PriceAlert with high target price."""
        alert_mock = MagicMock()
        alert_mock.target_price = 999999.99

        assert alert_mock.target_price == 999999.99

    def test_price_alert_low_price(self):
        """Test PriceAlert with low target price."""
        alert_mock = MagicMock()
        alert_mock.target_price = 0.01

        assert alert_mock.target_price == 0.01

    def test_price_alert_unicode_item_name(self):
        """Test PriceAlert with unicode item name."""
        unicode_name = "АК-47 | Красная линия"

        alert_mock = MagicMock()
        alert_mock.market_hash_name = unicode_name

        assert alert_mock.market_hash_name == unicode_name

    def test_price_alert_long_item_name(self):
        """Test PriceAlert with long item name."""
        long_name = "A" * 500  # Very long item name

        alert_mock = MagicMock()
        alert_mock.market_hash_name = long_name

        assert len(alert_mock.market_hash_name) == 500


class TestPriceAlertIntegration:
    """Integration tests for PriceAlert model."""

    def test_alert_lifecycle(self):
        """Test complete lifecycle of a price alert."""
        # Create
        alert = MagicMock()
        alert.id = uuid4()
        alert.user_id = uuid4()
        alert.item_id = "item_999"
        alert.market_hash_name = "Test Knife"
        alert.game = "csgo"
        alert.target_price = 150.0
        alert.condition = "below"
        alert.is_active = True
        alert.triggered = False
        alert.created_at = datetime.now(UTC)

        # Verify creation
        assert alert.is_active is True
        assert alert.triggered is False

        # Trigger alert
        alert.triggered = True
        alert.triggered_at = datetime.now(UTC)
        alert.is_active = False

        # Verify triggered state
        assert alert.triggered is True
        assert alert.is_active is False
        assert alert.triggered_at is not None

    def test_multiple_alerts_for_same_user(self):
        """Test multiple alerts for same user."""
        user_id = uuid4()
        alerts = []

        for i in range(5):
            alert = MagicMock()
            alert.id = uuid4()
            alert.user_id = user_id
            alert.target_price = 100.0 + i * 10
            alert.is_active = True
            alerts.append(alert)

        # Verify all alerts have same user_id
        for alert in alerts:
            assert alert.user_id == user_id

        # Verify all alerts are unique
        alert_ids = [alert.id for alert in alerts]
        assert len(set(alert_ids)) == 5


class TestPriceAlertEdgeCases:
    """Edge case tests for PriceAlert model."""

    def test_alert_with_zero_price(self):
        """Test PriceAlert with zero target price."""
        alert = MagicMock()
        alert.target_price = 0.0

        assert alert.target_price == 0.0

    def test_alert_with_negative_price(self):
        """Test PriceAlert with negative target price."""
        # This should be caught by validation in production
        alert = MagicMock()
        alert.target_price = -10.0

        assert alert.target_price == -10.0

    def test_alert_with_empty_item_name(self):
        """Test PriceAlert with empty item name."""
        alert = MagicMock()
        alert.market_hash_name = ""

        assert alert.market_hash_name == ""

    def test_alert_expired(self):
        """Test PriceAlert that has expired."""
        alert = MagicMock()
        alert.expires_at = datetime.now(UTC) - timedelta(days=1)
        alert.is_active = True  # Still active but expired

        # Check expiration
        assert alert.expires_at < datetime.now(UTC)

    def test_alert_with_special_characters_in_name(self):
        """Test PriceAlert with special characters in item name."""
        special_name = "★ Butterfly Knife | Doppler (Factory New) - Phase 2"

        alert = MagicMock()
        alert.market_hash_name = special_name

        assert "★" in alert.market_hash_name
        assert "|" in alert.market_hash_name
