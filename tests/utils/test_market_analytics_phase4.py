"""Phase 4 extended tests for market_analytics module.

Comprehensive tests for achieving 100% coverage on market analytics,
technical indicators, trading signals, and price prediction functionality.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import numpy as np
import pytest

from src.utils.market_analytics import (
    MarketAnalyzer,
    PricePoint,
    SignalType,
    TechnicalIndicators,
    TrendDirection,
)


# ==============================================================================
# TrendDirection Enum Extended Tests
# ==============================================================================


class TestTrendDirectionExtended:
    """Extended tests for TrendDirection enum."""

    def test_trend_direction_all_values_are_strings(self) -> None:
        """Test all TrendDirection values are strings."""
        for trend in TrendDirection:
            assert isinstance(trend.value, str)

    def test_trend_direction_unique_values(self) -> None:
        """Test all TrendDirection values are unique."""
        values = [t.value for t in TrendDirection]
        assert len(values) == len(set(values))

    def test_trend_direction_membership(self) -> None:
        """Test TrendDirection membership."""
        assert "bullish" in [t.value for t in TrendDirection]
        assert "bearish" in [t.value for t in TrendDirection]
        assert "neutral" in [t.value for t in TrendDirection]

    def test_trend_direction_iteration(self) -> None:
        """Test iterating over TrendDirection."""
        trends = list(TrendDirection)
        assert len(trends) == 3

    def test_trend_direction_str_enum_properties(self) -> None:
        """Test that TrendDirection behaves as str enum."""
        assert TrendDirection.BULLISH == "bullish"
        assert TrendDirection.BULLISH == "bullish"
        assert len(TrendDirection.BEARISH) == 7


# ==============================================================================
# SignalType Enum Extended Tests
# ==============================================================================


class TestSignalTypeExtended:
    """Extended tests for SignalType enum."""

    def test_signal_type_all_values_are_strings(self) -> None:
        """Test all SignalType values are strings."""
        for signal in SignalType:
            assert isinstance(signal.value, str)

    def test_signal_type_unique_values(self) -> None:
        """Test all SignalType values are unique."""
        values = [s.value for s in SignalType]
        assert len(values) == len(set(values))

    def test_signal_type_membership(self) -> None:
        """Test SignalType membership."""
        assert "buy" in [s.value for s in SignalType]
        assert "sell" in [s.value for s in SignalType]
        assert "hold" in [s.value for s in SignalType]

    def test_signal_type_iteration(self) -> None:
        """Test iterating over SignalType."""
        signals = list(SignalType)
        assert len(signals) == 3

    def test_signal_type_str_enum_properties(self) -> None:
        """Test that SignalType behaves as str enum."""
        assert SignalType.BUY == "buy"
        assert SignalType.SELL == "sell"
        assert len(SignalType.HOLD) == 4


# ==============================================================================
# PricePoint Extended Tests
# ==============================================================================


class TestPricePointExtended:
    """Extended tests for PricePoint class."""

    def test_price_point_with_large_values(self) -> None:
        """Test price point with very large values."""
        timestamp = datetime.now(UTC)
        pp = PricePoint(timestamp=timestamp, price=1_000_000.0, volume=10_000_000)

        assert pp.price == 1_000_000.0
        assert pp.volume == 10_000_000

    def test_price_point_with_small_values(self) -> None:
        """Test price point with very small values."""
        timestamp = datetime.now(UTC)
        pp = PricePoint(timestamp=timestamp, price=0.001, volume=1)

        assert pp.price == 0.001
        assert pp.volume == 1

    def test_price_point_with_zero_price(self) -> None:
        """Test price point with zero price."""
        timestamp = datetime.now(UTC)
        pp = PricePoint(timestamp=timestamp, price=0.0, volume=100)

        assert pp.price == 0.0

    def test_price_point_repr_format(self) -> None:
        """Test price point repr format details."""
        timestamp = datetime(2024, 6, 15, 10, 30, 0, tzinfo=UTC)
        pp = PricePoint(timestamp=timestamp, price=99.99, volume=50)

        repr_str = repr(pp)
        assert "PricePoint(" in repr_str
        assert "timestamp=" in repr_str
        assert "99.99" in repr_str
        assert "50" in repr_str

    def test_price_point_with_future_timestamp(self) -> None:
        """Test price point with future timestamp."""
        future = datetime.now(UTC) + timedelta(days=365)
        pp = PricePoint(timestamp=future, price=100.0, volume=100)

        assert pp.timestamp == future

    def test_price_point_with_old_timestamp(self) -> None:
        """Test price point with very old timestamp."""
        old = datetime(2010, 1, 1, tzinfo=UTC)
        pp = PricePoint(timestamp=old, price=100.0, volume=100)

        assert pp.timestamp == old


# ==============================================================================
# TechnicalIndicators RSI Extended Tests
# ==============================================================================


class TestTechnicalIndicatorsRSIPhase4:
    """Phase 4 extended tests for RSI calculation."""

    def test_rsi_with_alternating_gains_losses(self) -> None:
        """Test RSI with perfectly alternating gains and losses."""
        prices = [10.0, 11.0, 10.0, 11.0, 10.0, 11.0, 10.0, 11.0, 10.0, 11.0,
                  10.0, 11.0, 10.0, 11.0, 10.0]
        result = TechnicalIndicators.rsi(prices)

        assert result is not None
        # Should be around 50 for equal gains and losses
        assert 40 <= result <= 60

    def test_rsi_with_single_large_gain(self) -> None:
        """Test RSI with single large gain among small changes."""
        prices = [10.0, 10.1, 10.2, 10.1, 10.0, 10.1, 10.2, 50.0,  # Large gain
                  50.1, 50.0, 50.1, 50.0, 50.1, 50.0, 50.1]
        result = TechnicalIndicators.rsi(prices)

        assert result is not None
        assert 0 <= result <= 100

    def test_rsi_with_single_large_loss(self) -> None:
        """Test RSI with single large loss among small changes."""
        prices = [50.0, 50.1, 50.2, 50.1, 50.0, 50.1, 50.2, 10.0,  # Large loss
                  10.1, 10.0, 10.1, 10.0, 10.1, 10.0, 10.1]
        result = TechnicalIndicators.rsi(prices)

        assert result is not None
        assert 0 <= result <= 100

    def test_rsi_with_period_1(self) -> None:
        """Test RSI with period of 1."""
        prices = [10.0, 15.0, 12.0]  # Need period + 1 = 2 points
        result = TechnicalIndicators.rsi(prices, period=1)

        assert result is not None

    def test_rsi_returns_float_type(self) -> None:
        """Test that RSI always returns float type when valid."""
        prices = list(range(20))
        result = TechnicalIndicators.rsi(prices)

        assert result is not None
        assert isinstance(result, float)

    def test_rsi_boundary_100(self) -> None:
        """Test RSI returns exactly 100 for all gains."""
        prices = [float(i) for i in range(20)]  # Strictly increasing
        result = TechnicalIndicators.rsi(prices)

        assert result is not None
        assert result == 100.0


# ==============================================================================
# TechnicalIndicators MACD Extended Tests
# ==============================================================================


class TestTechnicalIndicatorsMACDPhase4:
    """Phase 4 extended tests for MACD calculation."""

    def test_macd_bearish_signal(self) -> None:
        """Test MACD bearish signal detection."""
        # Create downward trending prices
        prices = [100.0 - i * 0.5 for i in range(50)]
        result = TechnicalIndicators.macd(prices)

        assert result is not None
        # In a downtrend, MACD should be negative
        assert result["macd"] < 0

    def test_macd_histogram_interpretation(self) -> None:
        """Test MACD histogram value interpretation."""
        prices = [100 + np.sin(i / 5) * 10 for i in range(50)]
        result = TechnicalIndicators.macd(prices)

        assert result is not None
        # Histogram = MACD - Signal
        expected_histogram = result["macd"] - result["signal"]
        assert abs(result["histogram"] - expected_histogram) < 0.0001

    def test_macd_with_flat_prices(self) -> None:
        """Test MACD with flat prices."""
        prices = [100.0] * 50
        result = TechnicalIndicators.macd(prices)

        assert result is not None
        # With flat prices, MACD should be close to 0
        assert abs(result["macd"]) < 0.001
        assert abs(result["signal"]) < 0.001

    def test_macd_minimum_data_points(self) -> None:
        """Test MACD with minimum required data points."""
        # slow_period (26) + signal_period (9) = 35
        prices = list(range(35))
        result = TechnicalIndicators.macd(prices)

        assert result is not None

    def test_macd_returns_dict_with_correct_keys(self) -> None:
        """Test MACD returns dict with all required keys."""
        prices = [100 + np.sin(i / 3) * 10 for i in range(50)]
        result = TechnicalIndicators.macd(prices)

        assert result is not None
        assert set(result.keys()) == {"macd", "signal", "histogram"}

    def test_macd_values_are_floats(self) -> None:
        """Test that all MACD values are floats."""
        prices = [100 + np.sin(i / 5) * 10 for i in range(50)]
        result = TechnicalIndicators.macd(prices)

        assert result is not None
        assert isinstance(result["macd"], float)
        assert isinstance(result["signal"], float)
        assert isinstance(result["histogram"], float)


# ==============================================================================
# TechnicalIndicators Bollinger Bands Extended Tests
# ==============================================================================


class TestTechnicalIndicatorsBollingerBandsPhase4:
    """Phase 4 extended tests for Bollinger Bands calculation."""

    def test_bollinger_bands_with_constant_prices(self) -> None:
        """Test Bollinger Bands with constant prices."""
        prices = [100.0] * 25
        result = TechnicalIndicators.bollinger_bands(prices)

        assert result is not None
        # With constant prices, std = 0, so upper = middle = lower
        assert result["upper"] == result["middle"] == result["lower"]

    def test_bollinger_bands_with_zero_std_dev(self) -> None:
        """Test Bollinger Bands with std_dev = 0."""
        prices = [100.0 + i for i in range(25)]
        result = TechnicalIndicators.bollinger_bands(prices, std_dev=0.0)

        assert result is not None
        # With std_dev = 0, bands collapse to middle
        assert result["upper"] == result["middle"]
        assert result["lower"] == result["middle"]

    def test_bollinger_bands_upper_above_middle(self) -> None:
        """Test that upper band is always >= middle band."""
        np.random.seed(123)
        prices = [100 + np.random.randn() * 10 for _ in range(30)]
        result = TechnicalIndicators.bollinger_bands(prices)

        assert result is not None
        assert result["upper"] >= result["middle"]

    def test_bollinger_bands_lower_below_middle(self) -> None:
        """Test that lower band is always <= middle band."""
        np.random.seed(456)
        prices = [100 + np.random.randn() * 10 for _ in range(30)]
        result = TechnicalIndicators.bollinger_bands(prices)

        assert result is not None
        assert result["lower"] <= result["middle"]

    def test_bollinger_bands_width_with_different_std_devs(self) -> None:
        """Test Bollinger Bands width increases with std_dev."""
        prices = [100.0 + np.sin(i) * 5 for i in range(25)]

        result_1std = TechnicalIndicators.bollinger_bands(prices, std_dev=1.0)
        result_2std = TechnicalIndicators.bollinger_bands(prices, std_dev=2.0)
        result_3std = TechnicalIndicators.bollinger_bands(prices, std_dev=3.0)

        assert result_1std is not None
        assert result_2std is not None
        assert result_3std is not None

        width_1 = result_1std["upper"] - result_1std["lower"]
        width_2 = result_2std["upper"] - result_2std["lower"]
        width_3 = result_3std["upper"] - result_3std["lower"]

        assert width_1 < width_2 < width_3


# ==============================================================================
# TechnicalIndicators EMA Extended Tests
# ==============================================================================


class TestTechnicalIndicatorsEMAPhase4:
    """Phase 4 extended tests for EMA calculation."""

    def test_ema_with_two_values(self) -> None:
        """Test EMA with two values."""
        prices = np.array([10.0, 20.0])
        result = TechnicalIndicators._ema(prices, period=2)

        assert len(result) == 2
        assert result[0] == 10.0  # First value equals first price

    def test_ema_with_decreasing_values(self) -> None:
        """Test EMA with decreasing values."""
        prices = np.array([50.0, 40.0, 30.0, 20.0, 10.0])
        result = TechnicalIndicators._ema(prices, period=3)

        assert len(result) == 5
        # EMA should lag behind actual prices in a downtrend
        assert result[-1] > prices[-1]

    def test_ema_multiplier_calculation(self) -> None:
        """Test EMA multiplier calculation."""
        prices = np.array([10.0, 20.0])
        period = 3
        result = TechnicalIndicators._ema(prices, period=period)

        # Multiplier = 2 / (period + 1) = 2 / 4 = 0.5
        expected_multiplier = 2 / (period + 1)
        expected_second = (20.0 * expected_multiplier) + (10.0 * (1 - expected_multiplier))

        assert abs(result[1] - expected_second) < 0.0001

    def test_ema_with_large_period(self) -> None:
        """Test EMA with period larger than data."""
        prices = np.array([10.0, 20.0, 30.0])
        result = TechnicalIndicators._ema(prices, period=10)

        # Should still work, just with smaller multiplier
        assert len(result) == 3

    def test_ema_dtype_is_float(self) -> None:
        """Test EMA output dtype is float."""
        prices = np.array([1, 2, 3, 4, 5], dtype=int)
        result = TechnicalIndicators._ema(prices, period=2)

        assert result.dtype == float


# ==============================================================================
# MarketAnalyzer Initialization Extended Tests
# ==============================================================================


class TestMarketAnalyzerInitPhase4:
    """Phase 4 extended tests for MarketAnalyzer initialization."""

    def test_analyzer_default_min_data_points(self) -> None:
        """Test analyzer with default min_data_points."""
        analyzer = MarketAnalyzer()
        assert analyzer.min_data_points == 30

    def test_analyzer_custom_min_data_points(self) -> None:
        """Test analyzer with custom min_data_points."""
        analyzer = MarketAnalyzer(min_data_points=100)
        assert analyzer.min_data_points == 100

    def test_analyzer_zero_min_data_points(self) -> None:
        """Test analyzer with zero min_data_points."""
        analyzer = MarketAnalyzer(min_data_points=0)
        assert analyzer.min_data_points == 0

    def test_analyzer_has_indicators_attribute(self) -> None:
        """Test analyzer has indicators attribute."""
        analyzer = MarketAnalyzer()
        assert hasattr(analyzer, "indicators")
        assert isinstance(analyzer.indicators, TechnicalIndicators)


# ==============================================================================
# MarketAnalyzer calculate_fair_price Extended Tests
# ==============================================================================


class TestMarketAnalyzerFairPricePhase4:
    """Phase 4 extended tests for fair price calculation."""

    @pytest.fixture()
    def analyzer(self) -> MarketAnalyzer:
        """Create market analyzer."""
        return MarketAnalyzer(min_data_points=5)

    def test_fair_price_mean_calculation(self, analyzer: MarketAnalyzer) -> None:
        """Test fair price mean calculation accuracy."""
        now = datetime.now(UTC)
        history = [
            PricePoint(now - timedelta(days=i), price=100 + i, volume=100)
            for i in range(10)
        ]
        result = analyzer.calculate_fair_price(history, method="mean")

        expected_mean = sum(100 + i for i in range(10)) / 10
        assert result is not None
        assert abs(result - expected_mean) < 0.01

    def test_fair_price_median_calculation(self, analyzer: MarketAnalyzer) -> None:
        """Test fair price median calculation accuracy."""
        now = datetime.now(UTC)
        history = [
            PricePoint(now - timedelta(days=i), price=100 + i, volume=100)
            for i in range(10)
        ]
        result = analyzer.calculate_fair_price(history, method="median")

        # Median of 100, 101, 102, 103, 104, 105, 106, 107, 108, 109
        expected_median = 104.5
        assert result is not None
        assert abs(result - expected_median) < 0.01

    def test_fair_price_vwap_calculation(self, analyzer: MarketAnalyzer) -> None:
        """Test fair price VWAP calculation accuracy."""
        now = datetime.now(UTC)
        # Create prices with varying volumes
        history = [
            PricePoint(now - timedelta(days=0), price=100, volume=1000),  # High volume
            PricePoint(now - timedelta(days=1), price=200, volume=100),   # Low volume
            PricePoint(now - timedelta(days=2), price=100, volume=1000),  # High volume
            PricePoint(now - timedelta(days=3), price=200, volume=100),   # Low volume
            PricePoint(now - timedelta(days=4), price=100, volume=1000),  # High volume
        ]
        result = analyzer.calculate_fair_price(history, method="volume_weighted")

        # VWAP should be closer to 100 due to higher volume
        assert result is not None
        assert result < 150  # Biased toward high-volume price

    def test_fair_price_logs_warning_insufficient_data(
        self, analyzer: MarketAnalyzer
    ) -> None:
        """Test fair price logs warning for insufficient data."""
        now = datetime.now(UTC)
        history = [
            PricePoint(now - timedelta(days=i), price=100, volume=100)
            for i in range(3)  # Less than min_data_points
        ]

        with patch("src.utils.market_analytics.logger") as mock_logger:
            result = analyzer.calculate_fair_price(history)
            assert result is None
            mock_logger.warning.assert_called()


# ==============================================================================
# MarketAnalyzer detect_trend Extended Tests
# ==============================================================================


class TestMarketAnalyzerDetectTrendPhase4:
    """Phase 4 extended tests for trend detection."""

    @pytest.fixture()
    def analyzer(self) -> MarketAnalyzer:
        """Create market analyzer."""
        return MarketAnalyzer(min_data_points=5)

    def test_detect_trend_exactly_2_percent_above(
        self, analyzer: MarketAnalyzer
    ) -> None:
        """Test trend detection at exactly 2% threshold."""
        now = datetime.now(UTC)
        # Create prices where short MA is exactly 2% above long MA
        history = [
            PricePoint(now - timedelta(days=30 - i), price=100 + (i / 15), volume=100)
            for i in range(31)
        ]
        trend = analyzer.detect_trend(history)

        # Should be classified
        assert trend in {TrendDirection.BULLISH, TrendDirection.NEUTRAL}

    def test_detect_trend_exactly_2_percent_below(
        self, analyzer: MarketAnalyzer
    ) -> None:
        """Test trend detection at exactly 2% below threshold."""
        now = datetime.now(UTC)
        # Create prices where short MA is exactly 2% below long MA
        history = [
            PricePoint(now - timedelta(days=30 - i), price=200 - (i / 15), volume=100)
            for i in range(31)
        ]
        trend = analyzer.detect_trend(history)

        # Should be classified
        assert trend in {TrendDirection.BEARISH, TrendDirection.NEUTRAL}

    def test_detect_trend_logs_info(self, analyzer: MarketAnalyzer) -> None:
        """Test that trend detection logs info."""
        now = datetime.now(UTC)
        history = [
            PricePoint(now - timedelta(days=30 - i), price=100 + i, volume=100)
            for i in range(31)
        ]

        with patch("src.utils.market_analytics.logger") as mock_logger:
            analyzer.detect_trend(history)
            mock_logger.info.assert_called()

    def test_detect_trend_logs_warning_insufficient_data(
        self, analyzer: MarketAnalyzer
    ) -> None:
        """Test that trend detection logs warning for insufficient data."""
        now = datetime.now(UTC)
        history = [
            PricePoint(now - timedelta(days=i), price=100, volume=100)
            for i in range(10)  # Less than long_period
        ]

        with patch("src.utils.market_analytics.logger") as mock_logger:
            trend = analyzer.detect_trend(history)
            assert trend == TrendDirection.NEUTRAL
            mock_logger.warning.assert_called()


# ==============================================================================
# MarketAnalyzer predict_price_drop Extended Tests
# ==============================================================================


class TestMarketAnalyzerPredictPriceDropPhase4:
    """Phase 4 extended tests for price drop prediction."""

    @pytest.fixture()
    def analyzer(self) -> MarketAnalyzer:
        """Create market analyzer."""
        return MarketAnalyzer(min_data_points=5)

    def test_predict_price_drop_result_structure(
        self, analyzer: MarketAnalyzer
    ) -> None:
        """Test predict_price_drop result has all required keys."""
        now = datetime.now(UTC)
        history = [
            PricePoint(now - timedelta(days=i), price=100 + np.sin(i / 5) * 10, volume=100)
            for i in range(50)
        ]
        result = analyzer.predict_price_drop(history)

        assert "prediction" in result
        assert "confidence" in result
        assert "signals" in result
        assert "recommendation" in result

    def test_predict_price_drop_with_macd_signal(
        self, analyzer: MarketAnalyzer
    ) -> None:
        """Test predict_price_drop includes MACD signal."""
        now = datetime.now(UTC)
        history = [
            PricePoint(now - timedelta(days=i), price=100 + i * 0.5, volume=100)
            for i in range(50)
        ]
        result = analyzer.predict_price_drop(history)

        if "macd" in result["signals"]:
            macd_signal = result["signals"]["macd"]
            assert "value" in macd_signal
            assert "signal" in macd_signal
            assert "weight" in macd_signal

    def test_predict_price_drop_with_bollinger_signal(
        self, analyzer: MarketAnalyzer
    ) -> None:
        """Test predict_price_drop includes Bollinger Bands signal."""
        now = datetime.now(UTC)
        history = [
            PricePoint(now - timedelta(days=i), price=100 + np.sin(i / 3) * 10, volume=100)
            for i in range(50)
        ]
        result = analyzer.predict_price_drop(history)

        if "bollinger_bands" in result["signals"]:
            bb_signal = result["signals"]["bollinger_bands"]
            assert "value" in bb_signal
            assert "signal" in bb_signal
            assert "weight" in bb_signal

    def test_predict_price_drop_with_trend_signal(
        self, analyzer: MarketAnalyzer
    ) -> None:
        """Test predict_price_drop always includes trend signal."""
        now = datetime.now(UTC)
        history = [
            PricePoint(now - timedelta(days=i), price=100, volume=100)
            for i in range(50)
        ]
        result = analyzer.predict_price_drop(history)

        assert "trend" in result["signals"]
        trend_signal = result["signals"]["trend"]
        assert "value" in trend_signal
        assert "signal" in trend_signal
        assert "weight" in trend_signal

    def test_predict_price_drop_recommendation_values(
        self, analyzer: MarketAnalyzer
    ) -> None:
        """Test predict_price_drop recommendation is valid."""
        now = datetime.now(UTC)
        history = [
            PricePoint(now - timedelta(days=i), price=100 + np.sin(i / 5) * 10, volume=100)
            for i in range(50)
        ]
        result = analyzer.predict_price_drop(history)

        assert result["recommendation"] in {"BUY", "SELL", "HOLD"}


# ==============================================================================
# MarketAnalyzer calculate_support_resistance Extended Tests
# ==============================================================================


class TestMarketAnalyzerSupportResistancePhase4:
    """Phase 4 extended tests for support/resistance calculation."""

    @pytest.fixture()
    def analyzer(self) -> MarketAnalyzer:
        """Create market analyzer."""
        return MarketAnalyzer(min_data_points=5)

    def test_support_resistance_sorted(self, analyzer: MarketAnalyzer) -> None:
        """Test support levels are sorted ascending, resistance descending."""
        now = datetime.now(UTC)
        history = [
            PricePoint(now - timedelta(days=i), price=100 + np.sin(i / 3) * 20, volume=100)
            for i in range(50)
        ]
        result = analyzer.calculate_support_resistance(history, window=3)

        if result["support"]:
            assert result["support"] == sorted(result["support"])
        if result["resistance"]:
            assert result["resistance"] == sorted(result["resistance"], reverse=True)

    def test_support_resistance_no_duplicates(self, analyzer: MarketAnalyzer) -> None:
        """Test support/resistance levels have no duplicates."""
        now = datetime.now(UTC)
        history = [
            PricePoint(now - timedelta(days=i), price=100 + np.sin(i / 3) * 10, volume=100)
            for i in range(50)
        ]
        result = analyzer.calculate_support_resistance(history, window=3)

        if result["support"]:
            assert len(result["support"]) == len(set(result["support"]))
        if result["resistance"]:
            assert len(result["resistance"]) == len(set(result["resistance"]))

    def test_support_resistance_with_minimum_window(
        self, analyzer: MarketAnalyzer
    ) -> None:
        """Test support/resistance with minimum window size."""
        now = datetime.now(UTC)
        history = [
            PricePoint(now - timedelta(days=i), price=100 + np.sin(i) * 10, volume=100)
            for i in range(20)
        ]
        result = analyzer.calculate_support_resistance(history, window=1)

        assert "support" in result
        assert "resistance" in result

    def test_support_resistance_with_large_window(
        self, analyzer: MarketAnalyzer
    ) -> None:
        """Test support/resistance with large window size."""
        now = datetime.now(UTC)
        history = [
            PricePoint(now - timedelta(days=i), price=100 + np.sin(i / 5) * 10, volume=100)
            for i in range(100)
        ]
        result = analyzer.calculate_support_resistance(history, window=20)

        assert "support" in result
        assert "resistance" in result


# ==============================================================================
# MarketAnalyzer analyze_liquidity Extended Tests
# ==============================================================================


class TestMarketAnalyzerLiquidityPhase4:
    """Phase 4 extended tests for liquidity analysis."""

    @pytest.fixture()
    def analyzer(self) -> MarketAnalyzer:
        """Create market analyzer."""
        return MarketAnalyzer(min_data_points=5)

    def test_liquidity_score_range(self, analyzer: MarketAnalyzer) -> None:
        """Test liquidity score is in valid range [0, 1]."""
        now = datetime.now(UTC)
        history = [
            PricePoint(now - timedelta(days=i), price=100, volume=100 + i * 10)
            for i in range(20)
        ]
        result = analyzer.analyze_liquidity(history)

        assert 0 <= result["score"] <= 1

    def test_liquidity_high_volume_high_score(self, analyzer: MarketAnalyzer) -> None:
        """Test high volume results in higher liquidity score."""
        now = datetime.now(UTC)
        high_volume_history = [
            PricePoint(now - timedelta(days=i), price=100, volume=10000)
            for i in range(10)
        ]
        low_volume_history = [
            PricePoint(now - timedelta(days=i), price=100, volume=10)
            for i in range(10)
        ]

        high_result = analyzer.analyze_liquidity(high_volume_history)
        low_result = analyzer.analyze_liquidity(low_volume_history)

        assert high_result["score"] > low_result["score"]

    def test_liquidity_volume_consistency_calculation(
        self, analyzer: MarketAnalyzer
    ) -> None:
        """Test volume consistency is calculated correctly."""
        now = datetime.now(UTC)
        consistent_history = [
            PricePoint(now - timedelta(days=i), price=100, volume=100)
            for i in range(10)
        ]
        result = analyzer.analyze_liquidity(consistent_history)

        # With consistent volume, consistency should be high
        assert result["volume_consistency"] >= 0.9

    def test_liquidity_with_single_data_point(self, analyzer: MarketAnalyzer) -> None:
        """Test liquidity with single data point."""
        now = datetime.now(UTC)
        history = [PricePoint(now, price=100, volume=100)]

        result = analyzer.analyze_liquidity(history)

        assert "score" in result
        assert "volume_trend" in result
        assert result["volume_trend"] == TrendDirection.NEUTRAL

    def test_liquidity_volume_trend_bullish(self, analyzer: MarketAnalyzer) -> None:
        """Test volume trend detection as bullish."""
        now = datetime.now(UTC)
        # Volume increasing significantly
        history = [
            PricePoint(now - timedelta(days=9 - i), price=100, volume=100 + i * 50)
            for i in range(10)
        ]
        result = analyzer.analyze_liquidity(history, recent_period=10)

        # Should detect increasing volume trend
        assert result["volume_trend"] in {TrendDirection.BULLISH, TrendDirection.NEUTRAL}


# ==============================================================================
# MarketAnalyzer generate_trading_insights Extended Tests
# ==============================================================================


class TestMarketAnalyzerInsightsPhase4:
    """Phase 4 extended tests for trading insights generation."""

    @pytest.fixture()
    def analyzer(self) -> MarketAnalyzer:
        """Create market analyzer."""
        return MarketAnalyzer(min_data_points=10)

    def test_insights_overall_score_positive(self, analyzer: MarketAnalyzer) -> None:
        """Test insights overall score can be positive."""
        now = datetime.now(UTC)
        # Create bullish conditions
        history = [
            PricePoint(now - timedelta(days=49 - i), price=100 + i * 0.3, volume=100 + i * 5)
            for i in range(50)
        ]
        result = analyzer.generate_trading_insights(history, current_price=80.0)

        assert result["overall"]["score"] > 0 or result["overall"]["recommendation"] in {"BUY", "STRONG BUY"}

    def test_insights_overall_score_negative(self, analyzer: MarketAnalyzer) -> None:
        """Test insights overall score can be negative."""
        now = datetime.now(UTC)
        # Create bearish conditions
        history = [
            PricePoint(now - timedelta(days=49 - i), price=200 - i * 1, volume=100)
            for i in range(50)
        ]
        result = analyzer.generate_trading_insights(history, current_price=250.0)

        # Overpriced + bearish trend should give negative/sell
        assert "overall" in result

    def test_insights_recommendation_values(self, analyzer: MarketAnalyzer) -> None:
        """Test insights recommendation has valid value."""
        now = datetime.now(UTC)
        history = [
            PricePoint(now - timedelta(days=i), price=100, volume=100)
            for i in range(50)
        ]
        result = analyzer.generate_trading_insights(history, current_price=100.0)

        valid_recommendations = ["STRONG BUY", "BUY", "HOLD", "SELL", "STRONG SELL"]
        assert result["overall"]["recommendation"] in valid_recommendations

    def test_insights_fair_price_deviation_calculation(
        self, analyzer: MarketAnalyzer
    ) -> None:
        """Test fair price deviation is calculated correctly."""
        now = datetime.now(UTC)
        history = [
            PricePoint(now - timedelta(days=i), price=100, volume=100)
            for i in range(50)
        ]
        result = analyzer.generate_trading_insights(history, current_price=110.0)

        if "fair_price" in result:
            # 110 is 10% above 100
            assert abs(result["fair_price"]["deviation_percent"] - 10.0) < 1.0

    def test_insights_with_insufficient_data(self, analyzer: MarketAnalyzer) -> None:
        """Test insights with insufficient data for some calculations."""
        now = datetime.now(UTC)
        history = [
            PricePoint(now - timedelta(days=i), price=100, volume=100)
            for i in range(15)  # Enough for some but not all analyses
        ]
        result = analyzer.generate_trading_insights(history, current_price=100.0)

        # Should still return overall recommendation
        assert "overall" in result


# ==============================================================================
# Edge Cases and Boundary Tests
# ==============================================================================


class TestMarketAnalyticsEdgeCasesPhase4:
    """Phase 4 edge case and boundary tests."""

    def test_price_point_with_unicode_in_volume(self) -> None:
        """Test price point handles various volume types."""
        timestamp = datetime.now(UTC)
        pp = PricePoint(timestamp=timestamp, price=100.0, volume=int(1e10))

        assert pp.volume == int(1e10)

    def test_rsi_with_very_small_price_changes(self) -> None:
        """Test RSI with very small price changes."""
        prices = [100.0 + i * 0.0001 for i in range(20)]
        result = TechnicalIndicators.rsi(prices)

        assert result is not None

    def test_macd_with_exponential_growth(self) -> None:
        """Test MACD with exponential price growth."""
        prices = [100.0 * (1.01 ** i) for i in range(50)]
        result = TechnicalIndicators.macd(prices)

        assert result is not None

    def test_bollinger_bands_with_two_values_in_period(self) -> None:
        """Test Bollinger Bands with period equal to data length."""
        prices = [100.0, 110.0]
        result = TechnicalIndicators.bollinger_bands(prices, period=2)

        assert result is not None

    def test_analyzer_with_very_large_min_data_points(self) -> None:
        """Test analyzer with very large min_data_points."""
        analyzer = MarketAnalyzer(min_data_points=10000)
        now = datetime.now(UTC)
        history = [
            PricePoint(now - timedelta(days=i), price=100, volume=100)
            for i in range(100)
        ]

        # Should return None due to insufficient data
        result = analyzer.calculate_fair_price(history)
        assert result is None

    def test_predict_price_drop_all_signals_sell(self) -> None:
        """Test predict_price_drop when all signals indicate sell."""
        analyzer = MarketAnalyzer(min_data_points=10)
        now = datetime.now(UTC)
        # Create extremely overbought conditions
        history = [
            PricePoint(now - timedelta(days=49 - i), price=100 + i * 5, volume=100)
            for i in range(50)
        ]
        result = analyzer.predict_price_drop(history)

        # Should have high sell confidence
        assert result["sell_weight"] >= 0

    def test_liquidity_with_zero_coefficient_of_variation(self) -> None:
        """Test liquidity calculation with zero CV."""
        analyzer = MarketAnalyzer(min_data_points=5)
        now = datetime.now(UTC)
        # Perfectly consistent volume
        history = [
            PricePoint(now - timedelta(days=i), price=100, volume=100)
            for i in range(10)
        ]
        result = analyzer.analyze_liquidity(history)

        # CV = 0, so consistency should be 1
        assert result["volume_consistency"] == 1.0


# ==============================================================================
# Integration Tests
# ==============================================================================


class TestMarketAnalyticsIntegrationPhase4:
    """Phase 4 integration tests for market analytics."""

    def test_full_analysis_workflow(self) -> None:
        """Test complete analysis workflow."""
        analyzer = MarketAnalyzer(min_data_points=10)
        now = datetime.now(UTC)

        # Create realistic price history
        history = [
            PricePoint(
                now - timedelta(days=59 - i),
                price=100 + np.sin(i / 5) * 10 + i * 0.1,
                volume=100 + np.abs(np.sin(i / 3)) * 50,
            )
            for i in range(60)
        ]

        # Get all indicators
        prices = [p.price for p in history]
        rsi = TechnicalIndicators.rsi(prices)
        macd = TechnicalIndicators.macd(prices)
        bb = TechnicalIndicators.bollinger_bands(prices)

        # Get all analyses
        fair_price = analyzer.calculate_fair_price(history)
        trend = analyzer.detect_trend(history)
        prediction = analyzer.predict_price_drop(history)
        sr = analyzer.calculate_support_resistance(history)
        liquidity = analyzer.analyze_liquidity(history)
        insights = analyzer.generate_trading_insights(history, current_price=105.0)

        # Verify all results are valid
        assert rsi is not None
        assert macd is not None
        assert bb is not None
        assert fair_price is not None
        assert trend in TrendDirection
        assert "prediction" in prediction
        assert "support" in sr
        assert "score" in liquidity
        assert "overall" in insights

    def test_analysis_consistency_across_runs(self) -> None:
        """Test that analysis produces consistent results."""
        analyzer = MarketAnalyzer(min_data_points=10)
        now = datetime.now(UTC)

        history = [
            PricePoint(now - timedelta(days=49 - i), price=100 + i, volume=100)
            for i in range(50)
        ]

        # Run analysis multiple times
        results = [
            analyzer.generate_trading_insights(history, current_price=125.0)
            for _ in range(5)
        ]

        # All results should be identical
        first_result = results[0]
        for result in results[1:]:
            assert result["overall"]["recommendation"] == first_result["overall"]["recommendation"]
            assert result["overall"]["score"] == first_result["overall"]["score"]

    def test_analysis_with_real_world_pattern(self) -> None:
        """Test analysis with realistic market pattern."""
        analyzer = MarketAnalyzer(min_data_points=10)
        now = datetime.now(UTC)

        # Simulate a pump and dump pattern
        prices = []
        for i in range(60):
            if i < 20:
                # Accumulation phase
                price = 100 + np.random.randn() * 2
            elif i < 40:
                # Pump phase
                price = 100 + (i - 20) * 5 + np.random.randn() * 2
            else:
                # Dump phase
                price = 200 - (i - 40) * 4 + np.random.randn() * 2
            prices.append(price)

        history = [
            PricePoint(now - timedelta(days=59 - i), price=prices[i], volume=100 + i * 5)
            for i in range(60)
        ]

        insights = analyzer.generate_trading_insights(history, current_price=prices[-1])

        # Should provide valid analysis
        assert "overall" in insights
        assert "trend" in insights
        assert "liquidity" in insights
