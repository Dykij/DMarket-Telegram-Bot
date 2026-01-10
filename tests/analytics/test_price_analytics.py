"""Tests for Price Analytics Module."""

from decimal import Decimal

import pytest

from src.analytics.price_analytics import (
    BollingerBands,
    LiquidityLevel,
    MACDResult,
    PriceAnalytics,
    RSIResult,
    Signal,
    Trend,
    create_price_analytics,
)


class TestRSICalculation:
    """Tests for RSI calculation."""

    @pytest.fixture
    def analytics(self):
        """Create analytics instance."""
        return PriceAnalytics(rsi_period=14)

    def test_rsi_overbought(self, analytics):
        """Test RSI detects overbought condition."""
        # Simulating upward price movement
        prices = [10 + i * 0.5 for i in range(20)]  # Consistent uptrend
        result = analytics.calculate_rsi(prices)

        assert result is not None
        assert result.value > 50  # Should be high in uptrend

    def test_rsi_oversold(self, analytics):
        """Test RSI detects oversold condition."""
        # Simulating downward price movement
        prices = [30 - i * 0.5 for i in range(20)]  # Consistent downtrend
        result = analytics.calculate_rsi(prices)

        assert result is not None
        assert result.value < 50  # Should be low in downtrend

    def test_rsi_insufficient_data(self, analytics):
        """Test RSI returns None with insufficient data."""
        prices = [10, 11, 12]  # Too few prices
        result = analytics.calculate_rsi(prices)
        assert result is None

    def test_rsi_signal_generation(self):
        """Test RSI generates correct signals."""
        # Overbought
        result = RSIResult.from_value(75)
        assert result.signal == Signal.SELL
        assert result.is_overbought is True

        # Oversold
        result = RSIResult.from_value(25)
        assert result.signal == Signal.BUY
        assert result.is_oversold is True

        # Neutral
        result = RSIResult.from_value(50)
        assert result.signal == Signal.HOLD


class TestMACDCalculation:
    """Tests for MACD calculation."""

    @pytest.fixture
    def analytics(self):
        """Create analytics instance."""
        return PriceAnalytics()

    def test_macd_calculation(self, analytics):
        """Test basic MACD calculation."""
        # Generate enough price data
        prices = [10 + i * 0.1 for i in range(50)]
        result = analytics.calculate_macd(prices)

        assert result is not None
        assert isinstance(result.macd_line, float)
        assert isinstance(result.signal_line, float)
        assert isinstance(result.histogram, float)

    def test_macd_insufficient_data(self, analytics):
        """Test MACD returns None with insufficient data."""
        prices = [10, 11, 12]
        result = analytics.calculate_macd(prices)
        assert result is None

    def test_macd_crossover_detection(self):
        """Test MACD crossover detection."""
        # Bullish crossover
        result = MACDResult.from_values(
            macd_line=0.5,
            signal_line=0.3,
            prev_macd=0.2,
            prev_signal=0.4,
        )
        assert result.is_bullish_crossover is True
        assert result.signal == Signal.BUY

        # Bearish crossover
        result = MACDResult.from_values(
            macd_line=0.2,
            signal_line=0.4,
            prev_macd=0.5,
            prev_signal=0.3,
        )
        assert result.is_bearish_crossover is True
        assert result.signal == Signal.SELL


class TestBollingerBands:
    """Tests for Bollinger Bands calculation."""

    @pytest.fixture
    def analytics(self):
        """Create analytics instance."""
        return PriceAnalytics(bollinger_period=20)

    def test_bollinger_calculation(self, analytics):
        """Test Bollinger Bands calculation."""
        prices = [10 + i * 0.1 for i in range(30)]
        result = analytics.calculate_bollinger_bands(prices)

        assert result is not None
        assert result.upper > result.middle
        assert result.middle > result.lower
        assert 0 <= result.position <= 1

    def test_bollinger_insufficient_data(self, analytics):
        """Test returns None with insufficient data."""
        prices = [10, 11, 12]
        result = analytics.calculate_bollinger_bands(prices)
        assert result is None

    def test_bollinger_signal(self):
        """Test Bollinger signal generation."""
        bands = BollingerBands(
            upper=15.0,
            middle=12.0,
            lower=9.0,
            bandwidth=0.5,
            position=0.05,  # Near lower band
        )
        assert bands.signal == Signal.BUY

        bands.position = 0.95  # Near upper band
        assert bands.signal == Signal.SELL


class TestMovingAverages:
    """Tests for moving average calculations."""

    @pytest.fixture
    def analytics(self):
        """Create analytics instance."""
        return PriceAnalytics()

    def test_sma_calculation(self, analytics):
        """Test SMA calculation."""
        prices = [10, 12, 14, 16, 18]
        sma = analytics.calculate_sma(prices, period=3)
        # Average of [10, 12, 14] = 12
        assert sma == pytest.approx(12.0, rel=0.01)

    def test_ema_calculation(self, analytics):
        """Test EMA calculation."""
        prices = [10, 12, 14, 16, 18]
        ema = analytics.calculate_ema(prices, period=3)
        assert ema is not None
        # EMA should be close to recent prices
        assert ema > 14  # Weighted toward recent

    def test_insufficient_data(self, analytics):
        """Test returns None with insufficient data."""
        prices = [10, 12]
        assert analytics.calculate_sma(prices, period=5) is None
        assert analytics.calculate_ema(prices, period=5) is None


class TestLiquidityCalculation:
    """Tests for liquidity scoring."""

    @pytest.fixture
    def analytics(self):
        """Create analytics instance."""
        return PriceAnalytics()

    def test_high_liquidity(self, analytics):
        """Test high liquidity detection."""
        result = analytics.calculate_liquidity(
            listings_count=100,
            min_price=Decimal("10.0"),
            max_price=Decimal("11.0"),
            avg_price=Decimal("10.5"),
        )

        assert result.level == LiquidityLevel.VERY_HIGH
        assert result.score >= 80
        assert result.is_tradable is True

    def test_low_liquidity(self, analytics):
        """Test low liquidity detection."""
        result = analytics.calculate_liquidity(
            listings_count=3,
            min_price=Decimal("10.0"),
            max_price=Decimal("20.0"),
            avg_price=Decimal("15.0"),
        )

        assert result.level == LiquidityLevel.VERY_LOW
        assert result.is_tradable is False

    def test_spread_penalty(self, analytics):
        """Test price spread affects score."""
        # Low spread
        result1 = analytics.calculate_liquidity(
            listings_count=50,
            min_price=Decimal("10.0"),
            max_price=Decimal("10.5"),
            avg_price=Decimal("10.25"),
        )

        # High spread
        result2 = analytics.calculate_liquidity(
            listings_count=50,
            min_price=Decimal("10.0"),
            max_price=Decimal("20.0"),
            avg_price=Decimal("15.0"),
        )

        assert result1.score > result2.score


class TestTrendAnalysis:
    """Tests for trend analysis."""

    @pytest.fixture
    def analytics(self):
        """Create analytics instance."""
        return PriceAnalytics()

    def test_uptrend_detection(self, analytics):
        """Test uptrend detection."""
        prices = [10 + i * 0.5 for i in range(30)]  # Clear uptrend
        result = analytics.analyze_trend(prices)

        assert result is not None
        assert result.trend in [Trend.UP, Trend.STRONG_UP]
        assert result.predicted_direction == "up"

    def test_downtrend_detection(self, analytics):
        """Test downtrend detection."""
        prices = [30 - i * 0.5 for i in range(30)]  # Clear downtrend
        result = analytics.analyze_trend(prices)

        assert result is not None
        assert result.trend in [Trend.DOWN, Trend.STRONG_DOWN]
        assert result.predicted_direction == "down"

    def test_support_resistance(self, analytics):
        """Test support/resistance calculation."""
        prices = [10 + i * 0.1 for i in range(30)]
        result = analytics.analyze_trend(prices)

        assert result is not None
        assert result.support_level < result.resistance_level


class TestCompleteAnalysis:
    """Tests for complete price analysis."""

    @pytest.fixture
    def analytics(self):
        """Create analytics instance."""
        return PriceAnalytics()

    def test_full_analysis(self, analytics):
        """Test complete analysis with all indicators."""
        price_history = [10 + i * 0.1 for i in range(50)]

        analysis = analytics.analyze_item(
            item_name="Test Item",
            price_history=price_history,
            current_price=Decimal("15.0"),
            listings_count=50,
            min_listing_price=Decimal("14.0"),
            max_listing_price=Decimal("16.0"),
        )

        assert analysis.item_name == "Test Item"
        assert analysis.current_price == Decimal("15.0")
        assert analysis.rsi is not None
        assert analysis.macd is not None
        assert analysis.bollinger is not None
        assert analysis.trend is not None
        assert analysis.liquidity is not None
        assert analysis.overall_signal in Signal

    def test_analysis_to_dict(self, analytics):
        """Test conversion to dictionary."""
        price_history = [10 + i * 0.1 for i in range(50)]

        analysis = analytics.analyze_item(
            item_name="Test Item",
            price_history=price_history,
            current_price=Decimal("15.0"),
        )

        data = analysis.to_dict()
        assert "item_name" in data
        assert "current_price" in data
        assert "overall_signal" in data


class TestFactoryFunction:
    """Tests for factory function."""

    def test_create_analytics(self):
        """Test factory function."""
        analytics = create_price_analytics(
            rsi_period=10,
            macd_fast=8,
            macd_slow=17,
        )

        assert analytics.rsi_period == 10
        assert analytics.macd_fast == 8
        assert analytics.macd_slow == 17
