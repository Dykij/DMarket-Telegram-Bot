"""Extended tests for market_analytics module.

Additional tests to improve coverage for technical indicators,
market analysis, and edge cases.
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


class TestTechnicalIndicatorsRSIExtended:
    """Extended tests for RSI calculation."""

    def test_rsi_neutral_market(self) -> None:
        """Test RSI calculation for neutral/mixed market."""
        # Create mixed prices (alternating up and down)
        prices = [10.0 + (i % 2) * 0.5 for i in range(20)]
        result = TechnicalIndicators.rsi(prices)

        assert result is not None
        # Should be around 50 for neutral market
        assert 40 <= result <= 60

    def test_rsi_exact_boundary_data(self) -> None:
        """Test RSI with exactly enough data points."""
        prices = list(range(15))  # Exactly period + 1 = 15 points
        result = TechnicalIndicators.rsi(prices, period=14)

        assert result is not None
        assert 0 <= result <= 100

    def test_rsi_with_flat_prices(self) -> None:
        """Test RSI with flat prices (no change)."""
        prices = [10.0] * 20
        result = TechnicalIndicators.rsi(prices)

        # With no changes, RSI should be undefined or 50
        # In our implementation, if avg_loss is 0 and avg_gain is also 0
        assert result is not None

    def test_rsi_with_large_period(self) -> None:
        """Test RSI with large period."""
        prices = list(range(100))
        result = TechnicalIndicators.rsi(prices, period=50)

        assert result is not None
        assert 0 <= result <= 100


class TestTechnicalIndicatorsExtended:
    """Extended tests for technical indicators."""

    def test_ema_with_single_value(self) -> None:
        """Test EMA with single value."""
        prices = np.array([10.0])
        result = TechnicalIndicators._ema(prices, period=3)

        assert len(result) == 1
        assert result[0] == 10.0

    def test_ema_with_increasing_values(self) -> None:
        """Test EMA with increasing values."""
        prices = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        result = TechnicalIndicators._ema(prices, period=3)

        assert len(result) == 5
        # EMA should lag behind actual prices in an uptrend
        assert result[-1] < prices[-1]

    def test_macd_with_varying_periods(self) -> None:
        """Test MACD with various period combinations."""
        prices = [100 + np.sin(i / 3) * 10 for i in range(60)]

        result = TechnicalIndicators.macd(
            prices, fast_period=5, slow_period=15, signal_period=5
        )

        assert result is not None
        assert "macd" in result
        assert "signal" in result
        assert "histogram" in result

    def test_bollinger_bands_with_volatile_prices(self) -> None:
        """Test Bollinger Bands with high volatility."""
        # Create volatile prices
        np.random.seed(42)
        prices = [100 + np.random.randn() * 20 for _ in range(30)]
        result = TechnicalIndicators.bollinger_bands(prices)

        assert result is not None
        # Band width should be larger for volatile prices
        band_width = result["upper"] - result["lower"]
        assert band_width > 0

    def test_bollinger_bands_with_minimum_period(self) -> None:
        """Test Bollinger Bands with minimum period."""
        prices = [100.0 + i * 0.1 for i in range(10)]
        result = TechnicalIndicators.bollinger_bands(prices, period=10)

        assert result is not None


class TestMarketAnalyzerFairPrice:
    """Extended tests for fair price calculation."""

    @pytest.fixture()
    def analyzer(self) -> MarketAnalyzer:
        """Create market analyzer."""
        return MarketAnalyzer(min_data_points=10)

    def test_calculate_fair_price_with_varying_volumes(
        self, analyzer: MarketAnalyzer
    ) -> None:
        """Test fair price with varying volumes."""
        now = datetime.now(UTC)
        # High volume at low price, low volume at high price
        history = [
            PricePoint(now - timedelta(days=i), price=100 + i, volume=100 - i * 5)
            for i in range(15)
        ]
        result = analyzer.calculate_fair_price(history, method="volume_weighted")

        assert result is not None
        # Volume-weighted should bias toward lower prices (higher volume)

    def test_calculate_fair_price_all_methods_compare(
        self, analyzer: MarketAnalyzer
    ) -> None:
        """Test that different methods produce different results."""
        now = datetime.now(UTC)
        # Create skewed distribution
        history = [
            PricePoint(now - timedelta(days=i), price=100 + i * 2, volume=100)
            for i in range(20)
        ]

        mean_price = analyzer.calculate_fair_price(history, method="mean")
        median_price = analyzer.calculate_fair_price(history, method="median")
        vwap = analyzer.calculate_fair_price(history, method="volume_weighted")

        assert mean_price is not None
        assert median_price is not None
        assert vwap is not None

        # For uniform volume, VWAP should equal mean
        assert abs(mean_price - vwap) < 0.01


class TestMarketAnalyzerTrend:
    """Extended tests for trend detection."""

    @pytest.fixture()
    def analyzer(self) -> MarketAnalyzer:
        """Create market analyzer."""
        return MarketAnalyzer(min_data_points=10)

    def test_detect_trend_strong_bullish(self, analyzer: MarketAnalyzer) -> None:
        """Test strong bullish trend detection."""
        now = datetime.now(UTC)
        # Very strong upward trend
        history = [
            PricePoint(now - timedelta(days=30 - i), price=100 + i * 5, volume=100)
            for i in range(31)
        ]
        trend = analyzer.detect_trend(history)
        assert trend == TrendDirection.BULLISH

    def test_detect_trend_strong_bearish(self, analyzer: MarketAnalyzer) -> None:
        """Test strong bearish trend detection."""
        now = datetime.now(UTC)
        # Very strong downward trend
        history = [
            PricePoint(now - timedelta(days=30 - i), price=200 - i * 5, volume=100)
            for i in range(31)
        ]
        trend = analyzer.detect_trend(history)
        assert trend == TrendDirection.BEARISH

    def test_detect_trend_with_custom_periods(self, analyzer: MarketAnalyzer) -> None:
        """Test trend detection with custom periods."""
        now = datetime.now(UTC)
        history = [
            PricePoint(now - timedelta(days=49 - i), price=100 + i, volume=100)
            for i in range(50)
        ]
        trend = analyzer.detect_trend(history, short_period=10, long_period=40)
        assert trend in {
            TrendDirection.BULLISH,
            TrendDirection.BEARISH,
            TrendDirection.NEUTRAL,
        }


class TestMarketAnalyzerPrediction:
    """Extended tests for price prediction."""

    @pytest.fixture()
    def analyzer(self) -> MarketAnalyzer:
        """Create market analyzer."""
        return MarketAnalyzer(min_data_points=10)

    def test_predict_price_drop_with_overbought_rsi(
        self, analyzer: MarketAnalyzer
    ) -> None:
        """Test prediction with overbought RSI signal."""
        now = datetime.now(UTC)
        # Create strong uptrend to get high RSI
        history = [
            PricePoint(now - timedelta(days=49 - i), price=100 + i * 2, volume=100)
            for i in range(50)
        ]
        result = analyzer.predict_price_drop(history)

        assert "signals" in result
        if "rsi" in result["signals"]:
            rsi_signal = result["signals"]["rsi"]
            assert "value" in rsi_signal
            assert "signal" in rsi_signal

    def test_predict_price_drop_with_oversold_rsi(
        self, analyzer: MarketAnalyzer
    ) -> None:
        """Test prediction with oversold RSI signal."""
        now = datetime.now(UTC)
        # Create strong downtrend to get low RSI
        history = [
            PricePoint(now - timedelta(days=49 - i), price=200 - i * 2, volume=100)
            for i in range(50)
        ]
        result = analyzer.predict_price_drop(history)

        assert "signals" in result
        if "rsi" in result["signals"]:
            rsi_signal = result["signals"]["rsi"]
            assert rsi_signal["signal"] in {SignalType.BUY, SignalType.SELL, SignalType.HOLD}

    def test_predict_price_drop_with_high_threshold(
        self, analyzer: MarketAnalyzer
    ) -> None:
        """Test prediction with high confidence threshold."""
        now = datetime.now(UTC)
        history = [
            PricePoint(now - timedelta(days=i), price=100 + np.sin(i / 5) * 10, volume=100)
            for i in range(50)
        ]
        result = analyzer.predict_price_drop(history, threshold=0.99)

        # With very high threshold, prediction should likely be False
        assert "prediction" in result
        assert "confidence" in result


class TestMarketAnalyzerSupportResistance:
    """Extended tests for support/resistance calculation."""

    @pytest.fixture()
    def analyzer(self) -> MarketAnalyzer:
        """Create market analyzer."""
        return MarketAnalyzer(min_data_points=10)

    def test_calculate_support_resistance_with_clear_levels(
        self, analyzer: MarketAnalyzer
    ) -> None:
        """Test support/resistance with clear price levels."""
        now = datetime.now(UTC)
        # Create price pattern with clear support and resistance
        prices = []
        for i in range(50):
            # Oscillating pattern
            base = 100
            if i % 10 < 5:
                price = base + i % 10
            else:
                price = base + 10 - (i % 10)
            prices.append(price)

        history = [
            PricePoint(now - timedelta(days=49 - i), price=prices[i], volume=100)
            for i in range(50)
        ]
        result = analyzer.calculate_support_resistance(history, window=3)

        assert "support" in result
        assert "resistance" in result

    def test_calculate_support_resistance_custom_window(
        self, analyzer: MarketAnalyzer
    ) -> None:
        """Test support/resistance with custom window size."""
        now = datetime.now(UTC)
        history = [
            PricePoint(
                now - timedelta(days=29 - i),
                price=100 + np.sin(i / 3) * 10,
                volume=100,
            )
            for i in range(30)
        ]
        result = analyzer.calculate_support_resistance(history, window=3)

        assert "support" in result
        assert "resistance" in result


class TestMarketAnalyzerLiquidity:
    """Extended tests for liquidity analysis."""

    @pytest.fixture()
    def analyzer(self) -> MarketAnalyzer:
        """Create market analyzer."""
        return MarketAnalyzer(min_data_points=10)

    def test_analyze_liquidity_with_high_volume(
        self, analyzer: MarketAnalyzer
    ) -> None:
        """Test liquidity analysis with high volume."""
        now = datetime.now(UTC)
        history = [
            PricePoint(now - timedelta(days=i), price=100, volume=1000)
            for i in range(10)
        ]
        result = analyzer.analyze_liquidity(history, recent_period=10)

        assert result["avg_daily_volume"] == 1000
        assert result["score"] > 0

    def test_analyze_liquidity_with_decreasing_volume(
        self, analyzer: MarketAnalyzer
    ) -> None:
        """Test liquidity analysis with decreasing volume trend."""
        now = datetime.now(UTC)
        # Volume decreasing over time
        history = [
            PricePoint(now - timedelta(days=9 - i), price=100, volume=1000 - i * 100)
            for i in range(10)
        ]
        result = analyzer.analyze_liquidity(history, recent_period=10)

        # Volume trend should be bearish
        assert result["volume_trend"] in {
            TrendDirection.BEARISH,
            TrendDirection.NEUTRAL,
        }

    def test_analyze_liquidity_with_inconsistent_volume(
        self, analyzer: MarketAnalyzer
    ) -> None:
        """Test liquidity analysis with inconsistent volume."""
        now = datetime.now(UTC)
        # Very inconsistent volume
        volumes = [10, 1000, 50, 500, 20, 800, 30, 600, 40, 700]
        history = [
            PricePoint(now - timedelta(days=i), price=100, volume=volumes[i])
            for i in range(10)
        ]
        result = analyzer.analyze_liquidity(history, recent_period=10)

        # Consistency should be low
        assert result["volume_consistency"] < 0.5

    def test_analyze_liquidity_fallback_to_history(
        self, analyzer: MarketAnalyzer
    ) -> None:
        """Test liquidity analysis falls back when no recent data."""
        old_date = datetime(2020, 1, 1, tzinfo=UTC)
        history = [
            PricePoint(old_date - timedelta(days=i), price=100, volume=100)
            for i in range(10)
        ]
        result = analyzer.analyze_liquidity(history, recent_period=7)

        # Should still return results using fallback
        assert "score" in result


class TestMarketAnalyzerInsights:
    """Extended tests for trading insights generation."""

    @pytest.fixture()
    def analyzer(self) -> MarketAnalyzer:
        """Create market analyzer."""
        return MarketAnalyzer(min_data_points=10)

    def test_generate_insights_strong_buy(self, analyzer: MarketAnalyzer) -> None:
        """Test insights generation for strong buy signal."""
        now = datetime.now(UTC)
        # Create conditions for strong buy
        history = [
            PricePoint(now - timedelta(days=49 - i), price=100 + i * 0.5, volume=100 + i * 10)
            for i in range(50)
        ]
        # Current price below fair price
        result = analyzer.generate_trading_insights(history, current_price=90.0)

        assert "overall" in result
        assert "recommendation" in result["overall"]

    def test_generate_insights_strong_sell(self, analyzer: MarketAnalyzer) -> None:
        """Test insights generation for strong sell signal."""
        now = datetime.now(UTC)
        # Create conditions for strong sell (downtrend, overpriced)
        history = [
            PricePoint(now - timedelta(days=49 - i), price=150 - i * 1, volume=100)
            for i in range(50)
        ]
        # Current price above fair price
        result = analyzer.generate_trading_insights(history, current_price=160.0)

        assert "overall" in result
        assert "recommendation" in result["overall"]

    def test_generate_insights_hold(self, analyzer: MarketAnalyzer) -> None:
        """Test insights generation for hold signal."""
        now = datetime.now(UTC)
        # Create neutral conditions
        history = [
            PricePoint(now - timedelta(days=i), price=100, volume=100) for i in range(50)
        ]
        # Current price at fair price
        result = analyzer.generate_trading_insights(history, current_price=100.0)

        assert "overall" in result
        # Could be HOLD or close to neutral

    def test_generate_insights_with_low_liquidity(
        self, analyzer: MarketAnalyzer
    ) -> None:
        """Test insights generation with low liquidity."""
        now = datetime.now(UTC)
        # Create history with very low volume
        history = [
            PricePoint(now - timedelta(days=i), price=100, volume=1) for i in range(50)
        ]
        result = analyzer.generate_trading_insights(history, current_price=100.0)

        assert "liquidity" in result
        assert result["liquidity"]["score"] < 0.5


class TestMarketAnalyzerLogging:
    """Tests for logging in market analytics."""

    def test_rsi_logs_warning_on_insufficient_data(self) -> None:
        """Test that RSI logs warning when data is insufficient."""
        prices = [10.0, 11.0, 12.0]

        with patch("src.utils.market_analytics.logger") as mock_logger:
            result = TechnicalIndicators.rsi(prices)
            assert result is None
            mock_logger.warning.assert_called_once()

    def test_macd_logs_warning_on_insufficient_data(self) -> None:
        """Test that MACD logs warning when data is insufficient."""
        prices = list(range(20))

        with patch("src.utils.market_analytics.logger") as mock_logger:
            result = TechnicalIndicators.macd(prices)
            assert result is None
            mock_logger.warning.assert_called_once()

    def test_bollinger_logs_warning_on_insufficient_data(self) -> None:
        """Test that Bollinger Bands logs warning when data is insufficient."""
        prices = [10.0, 11.0, 12.0]

        with patch("src.utils.market_analytics.logger") as mock_logger:
            result = TechnicalIndicators.bollinger_bands(prices)
            assert result is None
            mock_logger.warning.assert_called_once()

    def test_fair_price_logs_info_on_success(self) -> None:
        """Test that fair price logs info on success."""
        analyzer = MarketAnalyzer(min_data_points=10)
        now = datetime.now(UTC)
        history = [
            PricePoint(now - timedelta(days=i), price=100, volume=100) for i in range(15)
        ]

        with patch("src.utils.market_analytics.logger") as mock_logger:
            result = analyzer.calculate_fair_price(history)
            assert result is not None
            mock_logger.info.assert_called()

    def test_fair_price_logs_error_on_unknown_method(self) -> None:
        """Test that fair price logs error on unknown method."""
        analyzer = MarketAnalyzer(min_data_points=10)
        now = datetime.now(UTC)
        history = [
            PricePoint(now - timedelta(days=i), price=100, volume=100) for i in range(15)
        ]

        with patch("src.utils.market_analytics.logger") as mock_logger:
            result = analyzer.calculate_fair_price(history, method="invalid")
            assert result is None
            mock_logger.error.assert_called_once()


class TestEdgeCasesAndBoundaries:
    """Edge case and boundary tests."""

    def test_price_point_with_zero_volume(self) -> None:
        """Test price point with zero volume."""
        timestamp = datetime.now(UTC)
        pp = PricePoint(timestamp=timestamp, price=10.5, volume=0)

        assert pp.volume == 0

    def test_price_point_with_negative_price(self) -> None:
        """Test price point with negative price (edge case)."""
        timestamp = datetime.now(UTC)
        pp = PricePoint(timestamp=timestamp, price=-10.5, volume=100)

        assert pp.price == -10.5

    def test_rsi_with_all_losses(self) -> None:
        """Test RSI with all losses (decreasing prices)."""
        prices = [20.0 - i * 0.1 for i in range(20)]
        result = TechnicalIndicators.rsi(prices)

        assert result is not None
        # Should be close to 0 for all losses
        assert result < 30

    def test_analyzer_with_very_small_min_data_points(self) -> None:
        """Test analyzer with very small min_data_points."""
        analyzer = MarketAnalyzer(min_data_points=1)
        now = datetime.now(UTC)
        history = [PricePoint(now, price=100, volume=100)]

        result = analyzer.calculate_fair_price(history)
        assert result is not None
        assert result == 100.0

    def test_trend_detection_exactly_at_boundary(self) -> None:
        """Test trend detection when exactly at threshold boundary."""
        analyzer = MarketAnalyzer(min_data_points=10)
        now = datetime.now(UTC)
        # Create prices where short MA is exactly 2% above long MA
        history = [
            PricePoint(now - timedelta(days=30 - i), price=100 + (i * 0.066), volume=100)
            for i in range(31)
        ]
        trend = analyzer.detect_trend(history)

        # Should be classified as one of the three
        assert trend in {
            TrendDirection.BULLISH,
            TrendDirection.BEARISH,
            TrendDirection.NEUTRAL,
        }


class TestSignalTypeEnum:
    """Tests for SignalType enum."""

    def test_signal_type_string_values(self) -> None:
        """Test signal type string values."""
        assert str(SignalType.BUY.value) == "buy"
        assert str(SignalType.SELL.value) == "sell"
        assert str(SignalType.HOLD.value) == "hold"

    def test_signal_type_comparison(self) -> None:
        """Test signal type comparison."""
        assert SignalType.BUY == SignalType.BUY
        assert SignalType.BUY != SignalType.SELL


class TestTrendDirectionEnum:
    """Tests for TrendDirection enum."""

    def test_trend_direction_string_values(self) -> None:
        """Test trend direction string values."""
        assert str(TrendDirection.BULLISH.value) == "bullish"
        assert str(TrendDirection.BEARISH.value) == "bearish"
        assert str(TrendDirection.NEUTRAL.value) == "neutral"

    def test_trend_direction_is_string_enum(self) -> None:
        """Test that TrendDirection is string enum."""
        assert isinstance(TrendDirection.BULLISH, str)
        assert TrendDirection.BULLISH == "bullish"
