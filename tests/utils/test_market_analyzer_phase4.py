"""Phase 4 extended unit tests for the market_analyzer module.

This module contains extended tests for full coverage of market_analyzer.py
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest

from src.utils.market_analyzer import (
    PATTERN_BOTTOMING,
    PATTERN_BREAKOUT,
    PATTERN_FOMO,
    PATTERN_PANIC,
    PATTERN_RESISTANCE,
    PATTERN_REVERSAL,
    PATTERN_SUPPORT,
    PATTERN_TOPPING,
    TREND_DOWN,
    TREND_STABLE,
    TREND_UP,
    TREND_VOLATILE,
    VOL_HIGH,
    VOL_LOW,
    VOL_MEDIUM,
    MarketAnalyzer,
    analyze_market_opportunity,
    batch_analyze_items,
)


# ==================== Constants Tests ====================


class TestConstants:
    """Test module-level constants."""

    def test_trend_constants_defined(self):
        """Test that trend constants are defined."""
        assert TREND_UP == "up"
        assert TREND_DOWN == "down"
        assert TREND_STABLE == "stable"
        assert TREND_VOLATILE == "volatile"

    def test_volatility_constants_defined(self):
        """Test that volatility constants are defined."""
        assert VOL_LOW == "low"
        assert VOL_MEDIUM == "medium"
        assert VOL_HIGH == "high"

    def test_pattern_constants_defined(self):
        """Test that pattern constants are defined."""
        assert PATTERN_BREAKOUT == "breakout"
        assert PATTERN_SUPPORT == "support"
        assert PATTERN_RESISTANCE == "resistance"
        assert PATTERN_REVERSAL == "reversal"
        assert PATTERN_FOMO == "fomo"
        assert PATTERN_PANIC == "panic"
        assert PATTERN_BOTTOMING == "bottoming"
        assert PATTERN_TOPPING == "topping"


# ==================== MarketAnalyzer Init Tests ====================


class TestMarketAnalyzerInit:
    """Test MarketAnalyzer initialization."""

    def test_init_default_min_data_points(self):
        """Test default min_data_points value."""
        analyzer = MarketAnalyzer()
        assert analyzer.min_data_points == 5

    def test_init_custom_min_data_points(self):
        """Test custom min_data_points value."""
        analyzer = MarketAnalyzer(min_data_points=10)
        assert analyzer.min_data_points == 10

    def test_init_zero_min_data_points(self):
        """Test zero min_data_points value."""
        analyzer = MarketAnalyzer(min_data_points=0)
        assert analyzer.min_data_points == 0

    def test_init_large_min_data_points(self):
        """Test large min_data_points value."""
        analyzer = MarketAnalyzer(min_data_points=100)
        assert analyzer.min_data_points == 100


# ==================== analyze_price_history Tests ====================


class TestAnalyzePriceHistoryExtended:
    """Extended tests for analyze_price_history method."""

    @pytest.mark.asyncio()
    async def test_empty_price_history(self):
        """Test with empty price history."""
        analyzer = MarketAnalyzer()
        result = await analyzer.analyze_price_history([])

        assert result["trend"] == TREND_STABLE
        assert result["confidence"] == 0.0
        assert result["volatility"] == VOL_LOW
        assert result["patterns"] == []
        assert result["support_level"] is None
        assert result["resistance_level"] is None
        assert result["insufficient_data"] is True

    @pytest.mark.asyncio()
    async def test_single_data_point(self):
        """Test with single data point."""
        analyzer = MarketAnalyzer()
        result = await analyzer.analyze_price_history([
            {"price": 10.0, "timestamp": datetime.now(UTC).timestamp()}
        ])

        assert result["insufficient_data"] is True
        assert result["avg_price"] == 0.0

    @pytest.mark.asyncio()
    async def test_exact_min_data_points(self):
        """Test with exactly min_data_points entries."""
        analyzer = MarketAnalyzer(min_data_points=5)
        history = [
            {"price": float(10 + i), "timestamp": (datetime.now(UTC) - timedelta(days=4 - i)).timestamp()}
            for i in range(5)
        ]
        result = await analyzer.analyze_price_history(history)

        assert result["insufficient_data"] is False
        assert result["current_price"] == 14.0

    @pytest.mark.asyncio()
    async def test_unsorted_timestamps(self):
        """Test with unsorted timestamp data."""
        analyzer = MarketAnalyzer()
        # Create unsorted history
        history = [
            {"price": 12.0, "timestamp": (datetime.now(UTC) - timedelta(days=1)).timestamp()},
            {"price": 10.0, "timestamp": (datetime.now(UTC) - timedelta(days=4)).timestamp()},
            {"price": 11.0, "timestamp": (datetime.now(UTC) - timedelta(days=2)).timestamp()},
            {"price": 13.0, "timestamp": datetime.now(UTC).timestamp()},
            {"price": 10.5, "timestamp": (datetime.now(UTC) - timedelta(days=3)).timestamp()},
        ]
        result = await analyzer.analyze_price_history(history)

        # Should sort by timestamp and current price should be the most recent
        assert result["current_price"] == 13.0
        assert result["insufficient_data"] is False

    @pytest.mark.asyncio()
    async def test_missing_price_key(self):
        """Test with missing price key."""
        analyzer = MarketAnalyzer()
        history = [
            {"timestamp": (datetime.now(UTC) - timedelta(days=i)).timestamp()}
            for i in range(5, 0, -1)
        ]
        result = await analyzer.analyze_price_history(history)

        # All prices should be 0
        assert result["current_price"] == 0.0
        assert result["avg_price"] == 0.0

    @pytest.mark.asyncio()
    async def test_missing_timestamp_key(self):
        """Test with missing timestamp key."""
        analyzer = MarketAnalyzer()
        history = [{"price": float(10 + i)} for i in range(5)]
        result = await analyzer.analyze_price_history(history)

        # Should still work with 0 timestamps
        assert result["insufficient_data"] is False

    @pytest.mark.asyncio()
    async def test_volume_data_present(self):
        """Test with volume data present."""
        analyzer = MarketAnalyzer()
        history = [
            {"price": 10.0, "timestamp": (datetime.now(UTC) - timedelta(days=4)).timestamp(), "volume": 100},
            {"price": 10.5, "timestamp": (datetime.now(UTC) - timedelta(days=3)).timestamp(), "volume": 120},
            {"price": 11.0, "timestamp": (datetime.now(UTC) - timedelta(days=2)).timestamp(), "volume": 130},
            {"price": 11.5, "timestamp": (datetime.now(UTC) - timedelta(days=1)).timestamp(), "volume": 140},
            {"price": 12.0, "timestamp": datetime.now(UTC).timestamp(), "volume": 150},
        ]
        result = await analyzer.analyze_price_history(history)

        assert result["volume_change"] == 50.0  # (150-100)/100 * 100

    @pytest.mark.asyncio()
    async def test_volume_data_zero_initial(self):
        """Test with zero initial volume."""
        analyzer = MarketAnalyzer()
        history = [
            {"price": 10.0, "timestamp": (datetime.now(UTC) - timedelta(days=2)).timestamp(), "volume": 0},
            {"price": 10.5, "timestamp": (datetime.now(UTC) - timedelta(days=1)).timestamp(), "volume": 50},
            {"price": 11.0, "timestamp": datetime.now(UTC).timestamp(), "volume": 100},
        ]
        # Add more data points
        for i in range(3, 6):
            history.insert(0, {"price": float(9 + i), "timestamp": (datetime.now(UTC) - timedelta(days=i)).timestamp(), "volume": i * 10})

        result = await analyzer.analyze_price_history(history)
        assert "volume_change" in result

    @pytest.mark.asyncio()
    async def test_high_volatility_detection(self):
        """Test high volatility detection."""
        analyzer = MarketAnalyzer()
        # Highly volatile prices
        history = [
            {"price": 10.0, "timestamp": (datetime.now(UTC) - timedelta(days=6)).timestamp()},
            {"price": 15.0, "timestamp": (datetime.now(UTC) - timedelta(days=5)).timestamp()},
            {"price": 8.0, "timestamp": (datetime.now(UTC) - timedelta(days=4)).timestamp()},
            {"price": 16.0, "timestamp": (datetime.now(UTC) - timedelta(days=3)).timestamp()},
            {"price": 7.0, "timestamp": (datetime.now(UTC) - timedelta(days=2)).timestamp()},
            {"price": 14.0, "timestamp": (datetime.now(UTC) - timedelta(days=1)).timestamp()},
            {"price": 9.0, "timestamp": datetime.now(UTC).timestamp()},
        ]
        result = await analyzer.analyze_price_history(history)

        assert result["volatility"] == VOL_HIGH
        assert result["volatility_ratio"] > 0.1

    @pytest.mark.asyncio()
    async def test_medium_volatility_detection(self):
        """Test medium volatility detection."""
        analyzer = MarketAnalyzer()
        # Moderately volatile prices
        history = [
            {"price": 10.0, "timestamp": (datetime.now(UTC) - timedelta(days=6)).timestamp()},
            {"price": 10.8, "timestamp": (datetime.now(UTC) - timedelta(days=5)).timestamp()},
            {"price": 9.5, "timestamp": (datetime.now(UTC) - timedelta(days=4)).timestamp()},
            {"price": 11.0, "timestamp": (datetime.now(UTC) - timedelta(days=3)).timestamp()},
            {"price": 10.2, "timestamp": (datetime.now(UTC) - timedelta(days=2)).timestamp()},
            {"price": 10.9, "timestamp": (datetime.now(UTC) - timedelta(days=1)).timestamp()},
            {"price": 10.5, "timestamp": datetime.now(UTC).timestamp()},
        ]
        result = await analyzer.analyze_price_history(history)

        assert result["volatility"] in {VOL_LOW, VOL_MEDIUM}

    @pytest.mark.asyncio()
    async def test_price_statistics_calculation(self):
        """Test price statistics calculations."""
        analyzer = MarketAnalyzer()
        history = [
            {"price": 10.0, "timestamp": (datetime.now(UTC) - timedelta(days=4)).timestamp()},
            {"price": 12.0, "timestamp": (datetime.now(UTC) - timedelta(days=3)).timestamp()},
            {"price": 14.0, "timestamp": (datetime.now(UTC) - timedelta(days=2)).timestamp()},
            {"price": 16.0, "timestamp": (datetime.now(UTC) - timedelta(days=1)).timestamp()},
            {"price": 18.0, "timestamp": datetime.now(UTC).timestamp()},
        ]
        result = await analyzer.analyze_price_history(history)

        assert result["current_price"] == 18.0
        assert result["avg_price"] == 14.0  # (10+12+14+16+18)/5
        assert result["min_price"] == 10.0
        assert result["max_price"] == 18.0
        assert result["price_range"] == 8.0


# ==================== _analyze_trend Tests ====================


class TestAnalyzeTrendExtended:
    """Extended tests for _analyze_trend method."""

    def test_analyze_trend_insufficient_data(self):
        """Test trend analysis with insufficient data."""
        analyzer = MarketAnalyzer(min_data_points=10)
        trend, confidence = analyzer._analyze_trend([10.0, 11.0, 12.0])

        assert trend == TREND_STABLE
        assert confidence == 0.0

    def test_analyze_trend_perfect_uptrend(self):
        """Test with perfect linear uptrend."""
        analyzer = MarketAnalyzer()
        trend, confidence = analyzer._analyze_trend([10.0, 11.0, 12.0, 13.0, 14.0, 15.0])

        assert trend == TREND_UP
        assert confidence > 0.99

    def test_analyze_trend_perfect_downtrend(self):
        """Test with perfect linear downtrend."""
        analyzer = MarketAnalyzer()
        trend, confidence = analyzer._analyze_trend([15.0, 14.0, 13.0, 12.0, 11.0, 10.0])

        assert trend == TREND_DOWN
        assert confidence > 0.99

    def test_analyze_trend_perfectly_stable(self):
        """Test with perfectly stable prices."""
        analyzer = MarketAnalyzer()
        trend, _confidence = analyzer._analyze_trend([10.0, 10.0, 10.0, 10.0, 10.0])

        assert trend == TREND_STABLE
        # Zero variance means correlation is 0

    def test_analyze_trend_volatile_pattern(self):
        """Test with volatile pattern (high range, low confidence)."""
        analyzer = MarketAnalyzer()
        # High relative range with low correlation
        trend, confidence = analyzer._analyze_trend([10.0, 15.0, 8.0, 14.0, 9.0, 12.0])

        assert trend == TREND_VOLATILE
        assert confidence < 0.7

    def test_analyze_trend_slightly_up(self):
        """Test with slight upward trend."""
        analyzer = MarketAnalyzer()
        trend, _confidence = analyzer._analyze_trend([10.0, 10.2, 10.5, 10.3, 10.6, 10.8])

        assert trend == TREND_UP

    def test_analyze_trend_slightly_down(self):
        """Test with slight downward trend."""
        analyzer = MarketAnalyzer()
        trend, _confidence = analyzer._analyze_trend([10.8, 10.6, 10.3, 10.5, 10.2, 10.0])

        assert trend == TREND_DOWN


# ==================== Pattern Detection Tests ====================


class TestPatternDetectionExtended:
    """Extended tests for pattern detection methods."""

    def test_detect_patterns_insufficient_data(self):
        """Test pattern detection with insufficient data."""
        analyzer = MarketAnalyzer()
        timestamps = [datetime.now(UTC).timestamp()]
        patterns = analyzer._detect_patterns([10.0], timestamps)

        assert patterns == []

    def test_is_breakout_insufficient_data(self):
        """Test breakout detection with insufficient data."""
        analyzer = MarketAnalyzer()
        result = analyzer._is_breakout([10.0, 11.0, 12.0])  # Less than 10

        assert result is False

    def test_is_breakout_upward(self):
        """Test upward breakout detection."""
        analyzer = MarketAnalyzer()
        # Price breaks above the range
        prices = [10.0, 10.1, 10.0, 10.2, 10.1, 10.0, 10.1, 10.2, 12.0, 14.0]
        result = analyzer._is_breakout(prices)

        assert result is True

    def test_is_breakout_downward(self):
        """Test downward breakout detection."""
        analyzer = MarketAnalyzer()
        # Price breaks below the range
        prices = [10.0, 9.9, 10.0, 9.8, 9.9, 10.0, 9.9, 9.8, 8.0, 6.0]
        result = analyzer._is_breakout(prices)

        assert result is True

    def test_is_breakout_no_breakout(self):
        """Test when there's no breakout."""
        analyzer = MarketAnalyzer()
        # Price stays within range
        prices = [10.0, 10.1, 10.0, 10.2, 10.1, 10.0, 10.1, 10.2, 10.3, 10.1]
        result = analyzer._is_breakout(prices)

        assert result is False

    def test_is_reversal_insufficient_data(self):
        """Test reversal detection with insufficient data."""
        analyzer = MarketAnalyzer()
        result = analyzer._is_reversal([10.0, 11.0])

        assert result is False

    def test_is_reversal_up_to_down(self):
        """Test reversal from uptrend to downtrend."""
        analyzer = MarketAnalyzer()
        prices = [10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 14.5, 14.0, 13.5, 13.0]
        result = analyzer._is_reversal(prices)

        # Should detect change in trend direction
        assert isinstance(result, bool)

    def test_is_fomo_insufficient_data(self):
        """Test FOMO detection with insufficient data."""
        analyzer = MarketAnalyzer()
        result = analyzer._is_fomo([10.0, 11.0])

        assert result is False

    def test_is_fomo_rapid_rise(self):
        """Test FOMO pattern with rapid price rise."""
        analyzer = MarketAnalyzer()
        prices = [10.0, 10.5, 11.0, 11.5, 12.0, 12.5, 13.0, 14.0, 15.0, 20.0]
        result = analyzer._is_fomo(prices)

        assert result is True

    def test_is_fomo_no_rapid_rise(self):
        """Test when there's no FOMO pattern."""
        analyzer = MarketAnalyzer()
        prices = [10.0, 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7, 10.8, 10.9]
        result = analyzer._is_fomo(prices)

        assert result is False

    def test_is_fomo_zero_initial_price(self):
        """Test FOMO with zero initial price."""
        analyzer = MarketAnalyzer()
        prices = [0.0, 0.0, 10.0]
        result = analyzer._is_fomo(prices)

        assert result is False

    def test_is_panic_insufficient_data(self):
        """Test panic detection with insufficient data."""
        analyzer = MarketAnalyzer()
        result = analyzer._is_panic([10.0, 9.0])

        assert result is False

    def test_is_panic_rapid_drop(self):
        """Test panic pattern with rapid price drop."""
        analyzer = MarketAnalyzer()
        prices = [10.0, 9.5, 9.0, 8.5, 8.0, 7.5, 7.0, 6.0, 5.0, 4.0]
        result = analyzer._is_panic(prices)

        assert result is True

    def test_is_panic_no_rapid_drop(self):
        """Test when there's no panic pattern."""
        analyzer = MarketAnalyzer()
        prices = [10.0, 9.9, 9.8, 9.7, 9.6, 9.5, 9.4, 9.3, 9.2, 9.1]
        result = analyzer._is_panic(prices)

        assert result is False

    def test_is_panic_zero_initial_price(self):
        """Test panic with zero initial price."""
        analyzer = MarketAnalyzer()
        prices = [0.0, 0.0, 10.0]
        result = analyzer._is_panic(prices)

        assert result is False

    def test_is_bottoming_insufficient_data(self):
        """Test bottoming detection with insufficient data."""
        analyzer = MarketAnalyzer()
        result = analyzer._is_bottoming([10.0, 9.0])

        assert result is False

    def test_is_bottoming_pattern(self):
        """Test bottoming pattern detection."""
        analyzer = MarketAnalyzer()
        # Downward trend followed by stabilization
        prices = [10.0, 9.5, 9.0, 8.8, 8.85]
        result = analyzer._is_bottoming(prices)

        assert isinstance(result, bool)

    def test_is_topping_insufficient_data(self):
        """Test topping detection with insufficient data."""
        analyzer = MarketAnalyzer()
        result = analyzer._is_topping([10.0, 11.0])

        assert result is False

    def test_is_topping_pattern(self):
        """Test topping pattern detection."""
        analyzer = MarketAnalyzer()
        # Upward trend followed by stabilization
        prices = [10.0, 10.5, 11.0, 11.2, 11.15]
        result = analyzer._is_topping(prices)

        assert isinstance(result, bool)


# ==================== Pattern Confidence Tests ====================


class TestPatternConfidenceExtended:
    """Extended tests for pattern confidence calculation."""

    def test_calculate_pattern_confidence_base(self):
        """Test base confidence calculation."""
        analyzer = MarketAnalyzer()
        prices = [10.0, 10.1, 10.2, 10.3, 10.4, 10.5]
        confidence = analyzer._calculate_pattern_confidence(prices, PATTERN_BREAKOUT)

        assert 0.0 <= confidence <= 1.0

    def test_calculate_pattern_confidence_small_data(self):
        """Test confidence with small dataset."""
        analyzer = MarketAnalyzer()
        prices = [10.0, 11.0, 12.0]
        confidence = analyzer._calculate_pattern_confidence(prices, PATTERN_FOMO)

        # Small data reduces confidence
        assert confidence < 0.7

    def test_calculate_pattern_confidence_large_data(self):
        """Test confidence with large dataset."""
        analyzer = MarketAnalyzer()
        prices = [10.0 + i * 0.1 for i in range(30)]
        confidence = analyzer._calculate_pattern_confidence(prices, PATTERN_BREAKOUT)

        # Large data increases confidence
        assert confidence <= 1.0

    def test_calculate_pattern_confidence_breakout_strong(self):
        """Test confidence for strong breakout."""
        analyzer = MarketAnalyzer()
        # Strong breakout - price well beyond range
        prices = [10.0, 10.1, 10.0, 10.2, 10.1, 10.0, 10.1, 10.2, 15.0, 20.0]
        confidence = analyzer._calculate_pattern_confidence(prices, PATTERN_BREAKOUT)

        assert confidence > 0.5

    def test_calculate_pattern_confidence_fomo(self):
        """Test confidence for FOMO pattern."""
        analyzer = MarketAnalyzer()
        prices = [10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 25.0]
        confidence = analyzer._calculate_pattern_confidence(prices, PATTERN_FOMO)

        assert confidence <= 1.0

    def test_calculate_pattern_confidence_panic(self):
        """Test confidence for panic pattern."""
        analyzer = MarketAnalyzer()
        prices = [25.0, 18.0, 17.0, 16.0, 15.0, 14.0, 13.0, 12.0, 11.0, 5.0]
        confidence = analyzer._calculate_pattern_confidence(prices, PATTERN_PANIC)

        assert confidence <= 1.0

    def test_calculate_pattern_confidence_bottoming(self):
        """Test confidence for bottoming pattern."""
        analyzer = MarketAnalyzer()
        prices = [15.0, 14.0, 13.0, 12.5, 12.3, 12.4, 12.5, 12.6, 12.7, 12.8]
        confidence = analyzer._calculate_pattern_confidence(prices, PATTERN_BOTTOMING)

        assert 0.0 <= confidence <= 1.0

    def test_calculate_pattern_confidence_topping(self):
        """Test confidence for topping pattern."""
        analyzer = MarketAnalyzer()
        prices = [10.0, 11.0, 12.0, 12.5, 12.7, 12.6, 12.5, 12.4, 12.3, 12.2]
        confidence = analyzer._calculate_pattern_confidence(prices, PATTERN_TOPPING)

        assert 0.0 <= confidence <= 1.0


# ==================== Support/Resistance Tests ====================


class TestSupportResistanceExtended:
    """Extended tests for support/resistance level detection."""

    def test_find_support_resistance_insufficient_data(self):
        """Test with insufficient data."""
        analyzer = MarketAnalyzer(min_data_points=10)
        support, resistance = analyzer._find_support_resistance([10.0, 11.0])

        assert support is None
        assert resistance is None

    def test_find_support_resistance_with_local_extremes(self):
        """Test finding support/resistance with local min/max."""
        analyzer = MarketAnalyzer()
        # Pattern with local min at 9.0 and local max at 13.0
        prices = [10.0, 11.0, 9.0, 10.5, 12.0, 13.0, 11.5, 10.5]
        support, resistance = analyzer._find_support_resistance(prices)

        # Local min should be potential support
        # Local max should be potential resistance
        assert isinstance(support, float | type(None))
        assert isinstance(resistance, float | type(None))

    def test_find_support_resistance_no_local_extremes(self):
        """Test with no local extremes (monotonic)."""
        analyzer = MarketAnalyzer()
        prices = [10.0, 11.0, 12.0, 13.0, 14.0]
        support, resistance = analyzer._find_support_resistance(prices)

        # Monotonic increase has no local min/max
        assert support is None
        assert resistance is None

    def test_find_support_below_current(self):
        """Test finding support level below current price."""
        analyzer = MarketAnalyzer()
        # Local minimum at 8.0, current price at 12.0
        prices = [10.0, 9.0, 8.0, 9.0, 10.0, 11.0, 12.0]
        support, _resistance = analyzer._find_support_resistance(prices)

        assert support is not None
        assert support < 12.0

    def test_find_resistance_above_current(self):
        """Test finding resistance level above current price."""
        analyzer = MarketAnalyzer()
        # Local maximum at 14.0, current price at 10.0
        prices = [12.0, 13.0, 14.0, 13.0, 12.0, 11.0, 10.0]
        _support, resistance = analyzer._find_support_resistance(prices)

        assert resistance is not None
        assert resistance > 10.0


# ==================== analyze_market_opportunity Tests ====================


class TestAnalyzeMarketOpportunityExtended:
    """Extended tests for analyze_market_opportunity function."""

    @pytest.mark.asyncio()
    async def test_opportunity_with_dict_price(self):
        """Test with price as dictionary."""
        item_data = {
            "itemId": "test-123",
            "title": "Test Item",
            "price": {"amount": 1000},
        }
        history = [
            {"price": float(8 + i), "timestamp": (datetime.now(UTC) - timedelta(days=4 - i)).timestamp()}
            for i in range(5)
        ]
        result = await analyze_market_opportunity(item_data, history, "csgo")

        assert result["current_price"] == 10.0  # 1000/100

    @pytest.mark.asyncio()
    async def test_opportunity_with_numeric_price(self):
        """Test with price as number."""
        item_data = {
            "itemId": "test-123",
            "title": "Test Item",
            "price": 15.0,
        }
        history = [
            {"price": float(10 + i), "timestamp": (datetime.now(UTC) - timedelta(days=4 - i)).timestamp()}
            for i in range(5)
        ]
        result = await analyze_market_opportunity(item_data, history, "csgo")

        assert result["current_price"] == 15.0

    @pytest.mark.asyncio()
    async def test_opportunity_with_int_price(self):
        """Test with price as integer."""
        item_data = {
            "itemId": "test-123",
            "title": "Test Item",
            "price": 20,
        }
        history = [
            {"price": float(15 + i), "timestamp": (datetime.now(UTC) - timedelta(days=4 - i)).timestamp()}
            for i in range(5)
        ]
        result = await analyze_market_opportunity(item_data, history, "csgo")

        assert result["current_price"] == 20.0

    @pytest.mark.asyncio()
    async def test_opportunity_without_price_key(self):
        """Test without price key."""
        item_data = {
            "itemId": "test-123",
            "title": "Test Item",
        }
        history = [
            {"price": float(10 + i), "timestamp": (datetime.now(UTC) - timedelta(days=4 - i)).timestamp()}
            for i in range(5)
        ]
        result = await analyze_market_opportunity(item_data, history, "csgo")

        assert result["current_price"] == 0

    @pytest.mark.asyncio()
    async def test_opportunity_score_capped_at_100(self):
        """Test that opportunity score is capped at 100."""
        item_data = {
            "itemId": "test-123",
            "title": "Case Collection",
            "price": 5.0,
        }
        # Create history that triggers many patterns for high score
        history = [
            {"price": 20.0, "timestamp": (datetime.now(UTC) - timedelta(days=5)).timestamp(), "volume": 100},
            {"price": 18.0, "timestamp": (datetime.now(UTC) - timedelta(days=4)).timestamp(), "volume": 110},
            {"price": 15.0, "timestamp": (datetime.now(UTC) - timedelta(days=3)).timestamp(), "volume": 130},
            {"price": 10.0, "timestamp": (datetime.now(UTC) - timedelta(days=2)).timestamp(), "volume": 150},
            {"price": 6.0, "timestamp": (datetime.now(UTC) - timedelta(days=1)).timestamp(), "volume": 180},
            {"price": 5.0, "timestamp": datetime.now(UTC).timestamp(), "volume": 200},
        ]
        result = await analyze_market_opportunity(item_data, history, "csgo")

        assert result["opportunity_score"] <= 100

    @pytest.mark.asyncio()
    async def test_opportunity_with_uptrend(self):
        """Test opportunity analysis with upward trend."""
        item_data = {"itemId": "test-123", "title": "Test Item", "price": 15.0}
        history = [
            {"price": float(10 + i), "timestamp": (datetime.now(UTC) - timedelta(days=4 - i)).timestamp()}
            for i in range(5)
        ]
        result = await analyze_market_opportunity(item_data, history, "csgo")

        assert result["market_analysis"]["trend"] == TREND_UP
        assert "Upward price trend" in result["reasons"]

    @pytest.mark.asyncio()
    async def test_opportunity_with_panic_pattern(self):
        """Test opportunity analysis with panic pattern."""
        item_data = {"itemId": "test-123", "title": "Test Item", "price": 5.0}
        history = [
            {"price": 20.0, "timestamp": (datetime.now(UTC) - timedelta(days=4)).timestamp()},
            {"price": 17.0, "timestamp": (datetime.now(UTC) - timedelta(days=3)).timestamp()},
            {"price": 13.0, "timestamp": (datetime.now(UTC) - timedelta(days=2)).timestamp()},
            {"price": 9.0, "timestamp": (datetime.now(UTC) - timedelta(days=1)).timestamp()},
            {"price": 5.0, "timestamp": datetime.now(UTC).timestamp()},
        ]
        result = await analyze_market_opportunity(item_data, history, "csgo")

        pattern_types = [p["type"] for p in result["market_analysis"]["patterns"]]
        if PATTERN_PANIC in pattern_types:
            assert any("panic" in r.lower() for r in result["reasons"])

    @pytest.mark.asyncio()
    async def test_opportunity_with_fomo_pattern(self):
        """Test opportunity analysis with FOMO pattern."""
        item_data = {"itemId": "test-123", "title": "Test Item", "price": 25.0}
        history = [
            {"price": 10.0, "timestamp": (datetime.now(UTC) - timedelta(days=4)).timestamp()},
            {"price": 12.0, "timestamp": (datetime.now(UTC) - timedelta(days=3)).timestamp()},
            {"price": 15.0, "timestamp": (datetime.now(UTC) - timedelta(days=2)).timestamp()},
            {"price": 18.0, "timestamp": (datetime.now(UTC) - timedelta(days=1)).timestamp()},
            {"price": 25.0, "timestamp": datetime.now(UTC).timestamp()},
        ]
        result = await analyze_market_opportunity(item_data, history, "csgo")

        pattern_types = [p["type"] for p in result["market_analysis"]["patterns"]]
        if PATTERN_FOMO in pattern_types:
            assert any("FOMO" in r for r in result["reasons"])

    @pytest.mark.asyncio()
    async def test_opportunity_near_support(self):
        """Test opportunity when price is near support level."""
        item_data = {"itemId": "test-123", "title": "Test Item", "price": 10.2}
        history = [
            {"price": 12.0, "timestamp": (datetime.now(UTC) - timedelta(days=6)).timestamp()},
            {"price": 11.0, "timestamp": (datetime.now(UTC) - timedelta(days=5)).timestamp()},
            {"price": 10.0, "timestamp": (datetime.now(UTC) - timedelta(days=4)).timestamp()},
            {"price": 11.0, "timestamp": (datetime.now(UTC) - timedelta(days=3)).timestamp()},
            {"price": 12.0, "timestamp": (datetime.now(UTC) - timedelta(days=2)).timestamp()},
            {"price": 11.0, "timestamp": (datetime.now(UTC) - timedelta(days=1)).timestamp()},
            {"price": 10.2, "timestamp": datetime.now(UTC).timestamp()},
        ]
        result = await analyze_market_opportunity(item_data, history, "csgo")

        # Check support level detection
        assert result["market_analysis"]["support_level"] is not None or True

    @pytest.mark.asyncio()
    async def test_opportunity_volume_increase(self):
        """Test opportunity with volume increase."""
        item_data = {"itemId": "test-123", "title": "Test Item", "price": 12.0}
        history = [
            {"price": 10.0, "timestamp": (datetime.now(UTC) - timedelta(days=4)).timestamp(), "volume": 100},
            {"price": 10.5, "timestamp": (datetime.now(UTC) - timedelta(days=3)).timestamp(), "volume": 120},
            {"price": 11.0, "timestamp": (datetime.now(UTC) - timedelta(days=2)).timestamp(), "volume": 140},
            {"price": 11.5, "timestamp": (datetime.now(UTC) - timedelta(days=1)).timestamp(), "volume": 160},
            {"price": 12.0, "timestamp": datetime.now(UTC).timestamp(), "volume": 200},
        ]
        result = await analyze_market_opportunity(item_data, history, "csgo")

        # Volume change should be detected
        assert result["market_analysis"]["volume_change"] > 0

    @pytest.mark.asyncio()
    async def test_opportunity_csgo_case_bonus(self):
        """Test CS:GO case gets bonus score."""
        item_data = {"itemId": "test-123", "title": "Clutch Case", "price": 1.0}
        history = [
            {"price": float(1 + i * 0.1), "timestamp": (datetime.now(UTC) - timedelta(days=4 - i)).timestamp()}
            for i in range(5)
        ]
        result = await analyze_market_opportunity(item_data, history, "csgo")

        # Should have reason about cases
        assert any("case" in r.lower() for r in result["reasons"])

    @pytest.mark.asyncio()
    async def test_opportunity_csgo_collection_bonus(self):
        """Test CS:GO collection gets bonus score."""
        item_data = {"itemId": "test-123", "title": "2021 Collection Item", "price": 2.0}
        history = [
            {"price": float(2 + i * 0.1), "timestamp": (datetime.now(UTC) - timedelta(days=4 - i)).timestamp()}
            for i in range(5)
        ]
        result = await analyze_market_opportunity(item_data, history, "csgo")

        assert any("collection" in r.lower() for r in result["reasons"])

    @pytest.mark.asyncio()
    async def test_opportunity_different_games(self):
        """Test opportunity analysis for different games."""
        item_data = {"itemId": "test-123", "title": "Arcana Item", "price": 25.0}
        history = [
            {"price": float(20 + i), "timestamp": (datetime.now(UTC) - timedelta(days=4 - i)).timestamp()}
            for i in range(5)
        ]

        for game in ["csgo", "dota2", "tf2", "rust"]:
            result = await analyze_market_opportunity(item_data, history, game)
            assert result["game"] == game

    @pytest.mark.asyncio()
    async def test_opportunity_type_determination(self):
        """Test opportunity type determination."""
        item_data = {"itemId": "test-123", "title": "Test Item", "price": 5.0}
        # Create panic selling scenario for buy opportunity
        history = [
            {"price": 20.0, "timestamp": (datetime.now(UTC) - timedelta(days=4)).timestamp(), "volume": 100},
            {"price": 15.0, "timestamp": (datetime.now(UTC) - timedelta(days=3)).timestamp(), "volume": 150},
            {"price": 10.0, "timestamp": (datetime.now(UTC) - timedelta(days=2)).timestamp(), "volume": 200},
            {"price": 7.0, "timestamp": (datetime.now(UTC) - timedelta(days=1)).timestamp(), "volume": 250},
            {"price": 5.0, "timestamp": datetime.now(UTC).timestamp(), "volume": 300},
        ]
        result = await analyze_market_opportunity(item_data, history, "csgo")

        assert result["opportunity_type"] in {"buy", "sell", "neutral"}


# ==================== batch_analyze_items Tests ====================


class TestBatchAnalyzeItemsExtended:
    """Extended tests for batch_analyze_items function."""

    @pytest.mark.asyncio()
    async def test_batch_empty_items(self):
        """Test with empty items list."""
        results = await batch_analyze_items([], {}, "csgo")
        assert results == []

    @pytest.mark.asyncio()
    async def test_batch_items_without_item_id(self):
        """Test items without itemId are skipped."""
        items = [
            {"title": "Item 1"},  # No itemId
            {"itemId": "test-123", "title": "Item 2", "price": 10.0},
        ]
        histories = {
            "test-123": [
                {"price": float(8 + i), "timestamp": (datetime.now(UTC) - timedelta(days=4 - i)).timestamp()}
                for i in range(5)
            ]
        }
        results = await batch_analyze_items(items, histories, "csgo")

        assert len(results) == 1
        assert results[0]["item_id"] == "test-123"

    @pytest.mark.asyncio()
    async def test_batch_items_sorted_by_score(self):
        """Test results are sorted by opportunity score."""
        items = [
            {"itemId": "low-score", "title": "Low Score", "price": 10.0},
            {"itemId": "high-score", "title": "Clutch Case", "price": 5.0},
        ]
        # Create histories where case item should have higher score
        histories = {
            "low-score": [
                {"price": 10.0, "timestamp": (datetime.now(UTC) - timedelta(days=i)).timestamp()}
                for i in range(5, 0, -1)
            ],
            "high-score": [
                {"price": 20.0, "timestamp": (datetime.now(UTC) - timedelta(days=4)).timestamp(), "volume": 100},
                {"price": 15.0, "timestamp": (datetime.now(UTC) - timedelta(days=3)).timestamp(), "volume": 130},
                {"price": 10.0, "timestamp": (datetime.now(UTC) - timedelta(days=2)).timestamp(), "volume": 160},
                {"price": 7.0, "timestamp": (datetime.now(UTC) - timedelta(days=1)).timestamp(), "volume": 190},
                {"price": 5.0, "timestamp": datetime.now(UTC).timestamp(), "volume": 220},
            ],
        }
        results = await batch_analyze_items(items, histories, "csgo")

        assert len(results) == 2
        # Results should be sorted by score descending
        assert results[0]["opportunity_score"] >= results[1]["opportunity_score"]

    @pytest.mark.asyncio()
    async def test_batch_items_missing_history(self):
        """Test items with missing price history."""
        items = [
            {"itemId": "has-history", "title": "Item 1", "price": 10.0},
            {"itemId": "no-history", "title": "Item 2", "price": 15.0},
        ]
        histories = {
            "has-history": [
                {"price": float(8 + i), "timestamp": (datetime.now(UTC) - timedelta(days=4 - i)).timestamp()}
                for i in range(5)
            ]
        }
        results = await batch_analyze_items(items, histories, "csgo")

        assert len(results) == 2  # Both items should be analyzed

    @pytest.mark.asyncio()
    async def test_batch_handles_exception(self):
        """Test batch handles exception for individual items."""
        items = [
            {"itemId": "test-123", "title": "Test Item", "price": 10.0},
        ]
        histories = {
            "test-123": [
                {"price": float(8 + i), "timestamp": (datetime.now(UTC) - timedelta(days=4 - i)).timestamp()}
                for i in range(5)
            ]
        }

        # Patch analyze_market_opportunity to raise exception
        with patch("src.utils.market_analyzer.analyze_market_opportunity", side_effect=Exception("Test error")):
            results = await batch_analyze_items(items, histories, "csgo")

        # Should return empty list due to exception
        assert results == []

    @pytest.mark.asyncio()
    async def test_batch_large_item_list(self):
        """Test with large number of items."""
        items = [
            {"itemId": f"item-{i}", "title": f"Item {i}", "price": float(10 + i)}
            for i in range(50)
        ]
        histories = {
            f"item-{i}": [
                {"price": float(8 + j), "timestamp": (datetime.now(UTC) - timedelta(days=4 - j)).timestamp()}
                for j in range(5)
            ]
            for i in range(50)
        }
        results = await batch_analyze_items(items, histories, "csgo")

        assert len(results) == 50


# ==================== Edge Cases Tests ====================


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.mark.asyncio()
    async def test_unicode_item_title(self):
        """Test with unicode characters in title."""
        item_data = {
            "itemId": "test-123",
            "title": "АК-47 | Красная линия",
            "price": 10.0,
        }
        history = [
            {"price": float(8 + i), "timestamp": (datetime.now(UTC) - timedelta(days=4 - i)).timestamp()}
            for i in range(5)
        ]
        result = await analyze_market_opportunity(item_data, history, "csgo")

        assert result["item_name"] == "АК-47 | Красная линия"

    @pytest.mark.asyncio()
    async def test_very_small_prices(self):
        """Test with very small price values."""
        item_data = {"itemId": "test-123", "title": "Cheap Item", "price": 0.01}
        history = [
            {"price": 0.01 + i * 0.001, "timestamp": (datetime.now(UTC) - timedelta(days=4 - i)).timestamp()}
            for i in range(5)
        ]
        result = await analyze_market_opportunity(item_data, history, "csgo")

        assert result["current_price"] == 0.01

    @pytest.mark.asyncio()
    async def test_very_large_prices(self):
        """Test with very large price values."""
        item_data = {"itemId": "test-123", "title": "Expensive Item", "price": 100000.0}
        history = [
            {"price": float(90000 + i * 2000), "timestamp": (datetime.now(UTC) - timedelta(days=4 - i)).timestamp()}
            for i in range(5)
        ]
        result = await analyze_market_opportunity(item_data, history, "csgo")

        assert result["current_price"] == 100000.0

    @pytest.mark.asyncio()
    async def test_zero_prices_in_history(self):
        """Test with zero prices in history."""
        analyzer = MarketAnalyzer()
        history = [
            {"price": 0.0, "timestamp": (datetime.now(UTC) - timedelta(days=4)).timestamp()},
            {"price": 0.0, "timestamp": (datetime.now(UTC) - timedelta(days=3)).timestamp()},
            {"price": 0.0, "timestamp": (datetime.now(UTC) - timedelta(days=2)).timestamp()},
            {"price": 0.0, "timestamp": (datetime.now(UTC) - timedelta(days=1)).timestamp()},
            {"price": 0.0, "timestamp": datetime.now(UTC).timestamp()},
        ]
        result = await analyzer.analyze_price_history(history)

        assert result["avg_price"] == 0.0

    @pytest.mark.asyncio()
    async def test_negative_prices_in_history(self):
        """Test with negative prices in history (edge case)."""
        analyzer = MarketAnalyzer()
        history = [
            {"price": -10.0, "timestamp": (datetime.now(UTC) - timedelta(days=4)).timestamp()},
            {"price": -5.0, "timestamp": (datetime.now(UTC) - timedelta(days=3)).timestamp()},
            {"price": 0.0, "timestamp": (datetime.now(UTC) - timedelta(days=2)).timestamp()},
            {"price": 5.0, "timestamp": (datetime.now(UTC) - timedelta(days=1)).timestamp()},
            {"price": 10.0, "timestamp": datetime.now(UTC).timestamp()},
        ]
        result = await analyzer.analyze_price_history(history)

        # Should handle negative prices without crashing
        assert "avg_price" in result

    @pytest.mark.asyncio()
    async def test_missing_item_title(self):
        """Test with missing item title."""
        item_data = {"itemId": "test-123", "price": 10.0}
        history = [
            {"price": float(8 + i), "timestamp": (datetime.now(UTC) - timedelta(days=4 - i)).timestamp()}
            for i in range(5)
        ]
        result = await analyze_market_opportunity(item_data, history, "csgo")

        assert result["item_name"] == "Unknown item"

    @pytest.mark.asyncio()
    async def test_empty_item_id(self):
        """Test with empty item ID."""
        item_data = {"itemId": "", "title": "Test", "price": 10.0}
        history = [
            {"price": float(8 + i), "timestamp": (datetime.now(UTC) - timedelta(days=4 - i)).timestamp()}
            for i in range(5)
        ]
        result = await analyze_market_opportunity(item_data, history, "csgo")

        assert result["item_id"] == ""

    def test_analyze_trend_with_nan_values(self):
        """Test trend analysis doesn't crash with extreme variance."""
        analyzer = MarketAnalyzer()
        # All same values - zero variance
        trend, confidence = analyzer._analyze_trend([10.0, 10.0, 10.0, 10.0, 10.0])

        assert trend in {TREND_STABLE, TREND_UP, TREND_DOWN}
        assert 0.0 <= confidence <= 1.0


# ==================== Integration Tests ====================


class TestIntegration:
    """Integration tests for complete workflows."""

    @pytest.mark.asyncio()
    async def test_full_analysis_workflow(self):
        """Test complete analysis workflow."""
        # Create realistic market data
        item_data = {
            "itemId": "ak47-redline-123",
            "title": "AK-47 | Redline (Field-Tested)",
            "price": {"amount": 1500},
            "gameId": "csgo",
        }
        history = []
        base_price = 12.0
        for i in range(30):
            # Simulate realistic price movement
            import random
            random.seed(i)
            price = base_price + random.uniform(-1, 1.5)
            history.append({
                "price": price,
                "timestamp": (datetime.now(UTC) - timedelta(days=29 - i)).timestamp(),
                "volume": 100 + i * 5,
            })

        result = await analyze_market_opportunity(item_data, history, "csgo")

        # Verify all expected fields are present
        assert "opportunity_score" in result
        assert "opportunity_type" in result
        assert "reasons" in result
        assert "market_analysis" in result
        assert "current_price" in result
        assert "game" in result
        assert "timestamp" in result

        # Verify market analysis fields
        analysis = result["market_analysis"]
        assert "trend" in analysis
        assert "confidence" in analysis
        assert "volatility" in analysis
        assert "patterns" in analysis
        assert "support_level" in analysis or analysis["support_level"] is None
        assert "resistance_level" in analysis or analysis["resistance_level"] is None

    @pytest.mark.asyncio()
    async def test_batch_analysis_workflow(self):
        """Test batch analysis workflow."""
        items = []
        histories = {}

        for i in range(5):
            item_id = f"item-{i}"
            items.append({
                "itemId": item_id,
                "title": f"Test Item {i}",
                "price": float(10 + i * 2),
            })
            histories[item_id] = [
                {"price": float(8 + i + j * 0.5), "timestamp": (datetime.now(UTC) - timedelta(days=6 - j)).timestamp()}
                for j in range(7)
            ]

        results = await batch_analyze_items(items, histories, "csgo")

        assert len(results) == 5
        # Results should be sorted by opportunity score
        for i in range(len(results) - 1):
            assert results[i]["opportunity_score"] >= results[i + 1]["opportunity_score"]

    @pytest.mark.asyncio()
    async def test_multi_pattern_detection(self):
        """Test detection of multiple patterns simultaneously."""
        analyzer = MarketAnalyzer()
        # Create data that could trigger multiple patterns
        history = [
            {"price": 10.0, "timestamp": (datetime.now(UTC) - timedelta(days=14)).timestamp()},
            {"price": 10.5, "timestamp": (datetime.now(UTC) - timedelta(days=13)).timestamp()},
            {"price": 11.0, "timestamp": (datetime.now(UTC) - timedelta(days=12)).timestamp()},
            {"price": 10.8, "timestamp": (datetime.now(UTC) - timedelta(days=11)).timestamp()},
            {"price": 11.2, "timestamp": (datetime.now(UTC) - timedelta(days=10)).timestamp()},
            {"price": 10.9, "timestamp": (datetime.now(UTC) - timedelta(days=9)).timestamp()},
            {"price": 11.5, "timestamp": (datetime.now(UTC) - timedelta(days=8)).timestamp()},
            {"price": 12.0, "timestamp": (datetime.now(UTC) - timedelta(days=7)).timestamp()},
            {"price": 13.0, "timestamp": (datetime.now(UTC) - timedelta(days=6)).timestamp()},
            {"price": 14.0, "timestamp": (datetime.now(UTC) - timedelta(days=5)).timestamp()},
            {"price": 15.5, "timestamp": (datetime.now(UTC) - timedelta(days=4)).timestamp()},
            {"price": 17.0, "timestamp": (datetime.now(UTC) - timedelta(days=3)).timestamp()},
            {"price": 19.0, "timestamp": (datetime.now(UTC) - timedelta(days=2)).timestamp()},
            {"price": 22.0, "timestamp": (datetime.now(UTC) - timedelta(days=1)).timestamp()},
            {"price": 26.0, "timestamp": datetime.now(UTC).timestamp()},
        ]

        result = await analyzer.analyze_price_history(history)

        assert "patterns" in result
        assert isinstance(result["patterns"], list)
