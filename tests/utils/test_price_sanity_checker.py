"""Unit tests for price_sanity_checker module.

Tests for PriceSanityChecker class and PriceSanityCheckFailed exception.
"""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.utils.price_sanity_checker import (
    PriceSanityCheckFailed,
    PriceSanityChecker,
)


class TestPriceSanityCheckFailedException:
    """Tests for PriceSanityCheckFailed exception."""

    def test_exception_basic_initialization(self):
        """Test exception with basic parameters."""
        exc = PriceSanityCheckFailed(
            message="Test error",
            item_name="AK-47 | Redline",
            current_price=Decimal("10.00"),
        )

        assert exc.message == "Test error"
        assert exc.item_name == "AK-47 | Redline"
        assert exc.current_price == Decimal("10.00")
        assert exc.average_price is None
        assert exc.max_allowed_price is None
        assert str(exc) == "Test error"

    def test_exception_full_initialization(self):
        """Test exception with all parameters."""
        exc = PriceSanityCheckFailed(
            message="Price too high",
            item_name="AWP | Dragon Lore",
            current_price=Decimal("15000.00"),
            average_price=Decimal("10000.00"),
            max_allowed_price=Decimal("12500.00"),
        )

        assert exc.message == "Price too high"
        assert exc.item_name == "AWP | Dragon Lore"
        assert exc.current_price == Decimal("15000.00")
        assert exc.average_price == Decimal("10000.00")
        assert exc.max_allowed_price == Decimal("12500.00")

    def test_exception_inherits_from_exception(self):
        """Test that exception inherits from Exception."""
        exc = PriceSanityCheckFailed(
            message="Test",
            item_name="Item",
            current_price=Decimal("1.00"),
        )
        assert isinstance(exc, Exception)

    def test_exception_can_be_raised_and_caught(self):
        """Test that exception can be raised and caught."""
        with pytest.raises(PriceSanityCheckFailed) as exc_info:
            raise PriceSanityCheckFailed(
                message="Test error",
                item_name="Test Item",
                current_price=Decimal("50.00"),
            )

        assert exc_info.value.item_name == "Test Item"


class TestPriceSanityCheckerInit:
    """Tests for PriceSanityChecker initialization."""

    def test_init_without_dependencies(self):
        """Test initialization without dependencies."""
        checker = PriceSanityChecker()

        assert checker.db is None
        assert checker.notifier is None
        assert checker._enabled is True
        assert checker.is_enabled is True

    def test_init_with_database_manager(self):
        """Test initialization with database manager."""
        mock_db = MagicMock()
        checker = PriceSanityChecker(database_manager=mock_db)

        assert checker.db is mock_db
        assert checker.notifier is None

    def test_init_with_notifier(self):
        """Test initialization with notifier."""
        mock_notifier = MagicMock()
        checker = PriceSanityChecker(notifier=mock_notifier)

        assert checker.db is None
        assert checker.notifier is mock_notifier

    def test_init_with_all_dependencies(self):
        """Test initialization with all dependencies."""
        mock_db = MagicMock()
        mock_notifier = MagicMock()
        checker = PriceSanityChecker(
            database_manager=mock_db,
            notifier=mock_notifier,
        )

        assert checker.db is mock_db
        assert checker.notifier is mock_notifier

    def test_constants_values(self):
        """Test that constants have expected values."""
        assert PriceSanityChecker.MAX_PRICE_MULTIPLIER == 1.5
        assert PriceSanityChecker.HISTORY_DAYS == 7
        assert PriceSanityChecker.MIN_HISTORY_SAMPLES == 3


class TestPriceSanityCheckerEnableDisable:
    """Tests for enable/disable functionality."""

    def test_disable_checker(self):
        """Test disabling the checker."""
        checker = PriceSanityChecker()
        assert checker.is_enabled is True

        checker.disable()

        assert checker.is_enabled is False
        assert checker._enabled is False

    def test_enable_checker(self):
        """Test enabling the checker after disable."""
        checker = PriceSanityChecker()
        checker.disable()
        assert checker.is_enabled is False

        checker.enable()

        assert checker.is_enabled is True

    def test_is_enabled_property(self):
        """Test is_enabled property returns correct value."""
        checker = PriceSanityChecker()

        assert checker.is_enabled is True
        checker._enabled = False
        assert checker.is_enabled is False


class TestCheckPriceSanityDisabled:
    """Tests for check_price_sanity when disabled."""

    @pytest.mark.asyncio
    async def test_check_returns_passed_when_disabled(self):
        """Test that check returns passed when checker is disabled."""
        checker = PriceSanityChecker()
        checker.disable()

        result = await checker.check_price_sanity(
            item_name="Test Item",
            current_price=Decimal("1000.00"),
            game="csgo",
        )

        assert result["passed"] is True
        assert result["reason"] == "Disabled"


class TestCheckPriceSanityInsufficientHistory:
    """Tests for check_price_sanity with insufficient history."""

    @pytest.mark.asyncio
    async def test_check_with_empty_history(self):
        """Test check with no price history."""
        mock_db = MagicMock()
        mock_db.get_price_history = AsyncMock(return_value=[])

        checker = PriceSanityChecker(database_manager=mock_db)

        result = await checker.check_price_sanity(
            item_name="New Item",
            current_price=Decimal("50.00"),
            game="csgo",
        )

        assert result["passed"] is True
        assert "Insufficient history" in result["reason"]
        assert result.get("warning") is True

    @pytest.mark.asyncio
    async def test_check_with_one_sample(self):
        """Test check with only one history sample."""
        mock_db = MagicMock()
        mock_db.get_price_history = AsyncMock(
            return_value=[{"price_usd": 50.0}],
        )

        checker = PriceSanityChecker(database_manager=mock_db)

        result = await checker.check_price_sanity(
            item_name="Test Item",
            current_price=Decimal("55.00"),
            game="csgo",
        )

        assert result["passed"] is True
        assert "Insufficient history" in result["reason"]

    @pytest.mark.asyncio
    async def test_check_with_two_samples(self):
        """Test check with two history samples (still insufficient)."""
        mock_db = MagicMock()
        mock_db.get_price_history = AsyncMock(
            return_value=[
                {"price_usd": 50.0},
                {"price_usd": 52.0},
            ],
        )

        checker = PriceSanityChecker(database_manager=mock_db)

        result = await checker.check_price_sanity(
            item_name="Test Item",
            current_price=Decimal("55.00"),
            game="csgo",
        )

        assert result["passed"] is True
        assert result.get("warning") is True


class TestCheckPriceSanityPassed:
    """Tests for check_price_sanity when check passes."""

    @pytest.mark.asyncio
    async def test_check_passes_when_price_within_limit(self):
        """Test check passes when price is within allowed limit."""
        mock_db = MagicMock()
        # Average price = 100, max allowed = 150 (1.5x)
        mock_db.get_price_history = AsyncMock(
            return_value=[
                {"price_usd": 95.0},
                {"price_usd": 100.0},
                {"price_usd": 105.0},
            ],
        )

        checker = PriceSanityChecker(database_manager=mock_db)

        result = await checker.check_price_sanity(
            item_name="AK-47 | Redline",
            current_price=Decimal("120.00"),
            game="csgo",
        )

        assert result["passed"] is True
        assert "average_price" in result
        assert "max_allowed_price" in result
        assert "price_deviation_percent" in result
        assert "history_samples" in result
        assert result["history_samples"] == 3

    @pytest.mark.asyncio
    async def test_check_passes_at_exact_limit(self):
        """Test check passes when price is exactly at limit."""
        mock_db = MagicMock()
        mock_db.get_price_history = AsyncMock(
            return_value=[
                {"price_usd": 100.0},
                {"price_usd": 100.0},
                {"price_usd": 100.0},
            ],
        )

        checker = PriceSanityChecker(database_manager=mock_db)

        # Max allowed = 100 * 1.5 = 150
        result = await checker.check_price_sanity(
            item_name="Test Item",
            current_price=Decimal("150.00"),
            game="csgo",
        )

        assert result["passed"] is True

    @pytest.mark.asyncio
    async def test_check_calculates_correct_deviation(self):
        """Test that deviation percentage is calculated correctly."""
        mock_db = MagicMock()
        mock_db.get_price_history = AsyncMock(
            return_value=[
                {"price_usd": 100.0},
                {"price_usd": 100.0},
                {"price_usd": 100.0},
            ],
        )

        checker = PriceSanityChecker(database_manager=mock_db)

        result = await checker.check_price_sanity(
            item_name="Test Item",
            current_price=Decimal("120.00"),
            game="csgo",
        )

        # 20% above average
        assert result["passed"] is True
        assert abs(result["price_deviation_percent"] - 20.0) < 0.01


class TestCheckPriceSanityFailed:
    """Tests for check_price_sanity when check fails."""

    @pytest.mark.asyncio
    async def test_check_fails_when_price_exceeds_limit(self):
        """Test check fails when price exceeds maximum allowed."""
        mock_db = MagicMock()
        mock_db.get_price_history = AsyncMock(
            return_value=[
                {"price_usd": 100.0},
                {"price_usd": 100.0},
                {"price_usd": 100.0},
            ],
        )

        checker = PriceSanityChecker(database_manager=mock_db)

        # Max allowed = 100 * 1.5 = 150, current = 200
        with pytest.raises(PriceSanityCheckFailed) as exc_info:
            await checker.check_price_sanity(
                item_name="Test Item",
                current_price=Decimal("200.00"),
                game="csgo",
            )

        assert exc_info.value.item_name == "Test Item"
        assert exc_info.value.current_price == Decimal("200.00")
        assert exc_info.value.average_price == Decimal("100.0")
        assert exc_info.value.max_allowed_price == Decimal("150.0")

    @pytest.mark.asyncio
    async def test_check_fails_sends_notification(self):
        """Test that failed check sends notification if notifier is set."""
        mock_db = MagicMock()
        mock_db.get_price_history = AsyncMock(
            return_value=[
                {"price_usd": 100.0},
                {"price_usd": 100.0},
                {"price_usd": 100.0},
            ],
        )

        mock_notifier = MagicMock()
        mock_notifier.send_message = AsyncMock()

        checker = PriceSanityChecker(
            database_manager=mock_db,
            notifier=mock_notifier,
        )

        with pytest.raises(PriceSanityCheckFailed):
            await checker.check_price_sanity(
                item_name="Expensive Item",
                current_price=Decimal("200.00"),
                game="csgo",
            )

        mock_notifier.send_message.assert_called_once()
        call_args = mock_notifier.send_message.call_args
        assert "Expensive Item" in call_args.kwargs["message"]
        assert call_args.kwargs["parse_mode"] == "HTML"

    @pytest.mark.asyncio
    async def test_check_fails_without_notifier(self):
        """Test that failed check works without notifier."""
        mock_db = MagicMock()
        mock_db.get_price_history = AsyncMock(
            return_value=[
                {"price_usd": 100.0},
                {"price_usd": 100.0},
                {"price_usd": 100.0},
            ],
        )

        checker = PriceSanityChecker(database_manager=mock_db)

        with pytest.raises(PriceSanityCheckFailed):
            await checker.check_price_sanity(
                item_name="Test Item",
                current_price=Decimal("200.00"),
                game="csgo",
            )


class TestGetPriceHistory:
    """Tests for _get_price_history method."""

    @pytest.mark.asyncio
    async def test_get_history_without_db(self):
        """Test getting history without database returns empty list."""
        checker = PriceSanityChecker()

        result = await checker._get_price_history(
            item_name="Test Item",
            game="csgo",
            days=7,
        )

        assert result == []

    @pytest.mark.asyncio
    async def test_get_history_calls_db_correctly(self):
        """Test that _get_price_history calls database correctly."""
        mock_db = MagicMock()
        mock_db.get_price_history = AsyncMock(
            return_value=[{"price_usd": 50.0}],
        )

        checker = PriceSanityChecker(database_manager=mock_db)

        result = await checker._get_price_history(
            item_name="Test Item",
            game="csgo",
            days=7,
        )

        assert result == [{"price_usd": 50.0}]
        mock_db.get_price_history.assert_called_once()
        call_kwargs = mock_db.get_price_history.call_args.kwargs
        assert call_kwargs["item_name"] == "Test Item"
        assert call_kwargs["game"] == "csgo"

    @pytest.mark.asyncio
    async def test_get_history_handles_attribute_error(self):
        """Test handling when get_price_history method doesn't exist."""
        mock_db = MagicMock(spec=[])  # Empty spec = no methods

        checker = PriceSanityChecker(database_manager=mock_db)

        result = await checker._get_price_history(
            item_name="Test Item",
            game="csgo",
            days=7,
        )

        assert result == []

    @pytest.mark.asyncio
    async def test_get_history_handles_general_exception(self):
        """Test handling general exceptions from database."""
        mock_db = MagicMock()
        mock_db.get_price_history = AsyncMock(
            side_effect=Exception("Database error"),
        )

        checker = PriceSanityChecker(database_manager=mock_db)

        result = await checker._get_price_history(
            item_name="Test Item",
            game="csgo",
            days=7,
        )

        assert result == []


class TestSendCriticalAlert:
    """Tests for _send_critical_alert method."""

    @pytest.mark.asyncio
    async def test_send_alert_without_notifier(self):
        """Test that send_alert does nothing without notifier."""
        checker = PriceSanityChecker()

        # Should not raise
        await checker._send_critical_alert(
            item_name="Test Item",
            current_price=Decimal("200.00"),
            average_price=Decimal("100.00"),
            max_allowed=Decimal("150.00"),
            deviation_percent=100.0,
        )

    @pytest.mark.asyncio
    async def test_send_alert_with_notifier(self):
        """Test that send_alert sends message with notifier."""
        mock_notifier = MagicMock()
        mock_notifier.send_message = AsyncMock()

        checker = PriceSanityChecker(notifier=mock_notifier)

        await checker._send_critical_alert(
            item_name="AWP | Dragon Lore",
            current_price=Decimal("15000.00"),
            average_price=Decimal("10000.00"),
            max_allowed=Decimal("12500.00"),
            deviation_percent=50.0,
        )

        mock_notifier.send_message.assert_called_once()
        call_kwargs = mock_notifier.send_message.call_args.kwargs
        assert "AWP | Dragon Lore" in call_kwargs["message"]
        assert "$15000.00" in call_kwargs["message"]
        assert "КРИТИЧЕСКИЙ" in call_kwargs["message"]

    @pytest.mark.asyncio
    async def test_send_alert_handles_notifier_error(self):
        """Test that send_alert handles notifier errors gracefully."""
        mock_notifier = MagicMock()
        mock_notifier.send_message = AsyncMock(
            side_effect=Exception("Network error"),
        )

        checker = PriceSanityChecker(notifier=mock_notifier)

        # Should not raise
        await checker._send_critical_alert(
            item_name="Test Item",
            current_price=Decimal("200.00"),
            average_price=Decimal("100.00"),
            max_allowed=Decimal("150.00"),
            deviation_percent=100.0,
        )


class TestCheckPriceSanityErrors:
    """Tests for error handling in check_price_sanity."""

    @pytest.mark.asyncio
    async def test_check_returns_passed_with_insufficient_history_on_error(self):
        """Test that check returns passed with insufficient history on general errors."""
        mock_db = MagicMock()
        mock_db.get_price_history = AsyncMock(
            side_effect=RuntimeError("Unexpected error"),
        )

        checker = PriceSanityChecker(database_manager=mock_db)

        # When _get_price_history returns empty list (due to error handling),
        # check_price_sanity returns passed with insufficient history warning
        result = await checker.check_price_sanity(
            item_name="Test Item",
            current_price=Decimal("100.00"),
            game="csgo",
        )

        # The error is handled in _get_price_history which returns empty list,
        # then check_price_sanity treats it as insufficient history
        assert result["passed"] is True
        assert "Insufficient history" in result.get("reason", "")

    @pytest.mark.asyncio
    async def test_check_propagates_sanity_check_failed(self):
        """Test that PriceSanityCheckFailed is propagated."""
        mock_db = MagicMock()
        mock_db.get_price_history = AsyncMock(
            return_value=[
                {"price_usd": 10.0},
                {"price_usd": 10.0},
                {"price_usd": 10.0},
            ],
        )

        checker = PriceSanityChecker(database_manager=mock_db)

        with pytest.raises(PriceSanityCheckFailed) as exc_info:
            await checker.check_price_sanity(
                item_name="Item",
                current_price=Decimal("100.00"),  # 10x average
                game="csgo",
            )

        # Original exception should be raised, not wrapped
        assert exc_info.value.item_name == "Item"


class TestCheckPriceSanityGames:
    """Tests for check_price_sanity with different games."""

    @pytest.mark.asyncio
    async def test_check_with_dota2_game(self):
        """Test check with Dota 2 game."""
        mock_db = MagicMock()
        mock_db.get_price_history = AsyncMock(
            return_value=[
                {"price_usd": 50.0},
                {"price_usd": 50.0},
                {"price_usd": 50.0},
            ],
        )

        checker = PriceSanityChecker(database_manager=mock_db)

        result = await checker.check_price_sanity(
            item_name="Arcana",
            current_price=Decimal("60.00"),
            game="dota2",
        )

        assert result["passed"] is True
        call_kwargs = mock_db.get_price_history.call_args.kwargs
        assert call_kwargs["game"] == "dota2"

    @pytest.mark.asyncio
    async def test_check_with_rust_game(self):
        """Test check with Rust game."""
        mock_db = MagicMock()
        mock_db.get_price_history = AsyncMock(
            return_value=[
                {"price_usd": 20.0},
                {"price_usd": 22.0},
                {"price_usd": 21.0},
            ],
        )

        checker = PriceSanityChecker(database_manager=mock_db)

        result = await checker.check_price_sanity(
            item_name="Metal Door",
            current_price=Decimal("25.00"),
            game="rust",
        )

        assert result["passed"] is True

    @pytest.mark.asyncio
    async def test_check_with_tf2_game(self):
        """Test check with TF2 game."""
        mock_db = MagicMock()
        mock_db.get_price_history = AsyncMock(
            return_value=[
                {"price_usd": 5.0},
                {"price_usd": 5.5},
                {"price_usd": 4.5},
            ],
        )

        checker = PriceSanityChecker(database_manager=mock_db)

        result = await checker.check_price_sanity(
            item_name="Unusual Hat",
            current_price=Decimal("6.00"),
            game="tf2",
        )

        assert result["passed"] is True
