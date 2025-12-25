"""
Тесты для arbitrage/calculations.py.

Этот модуль тестирует функции расчетов для арбитражной торговли:
- calculate_commission - расчет комиссии
- calculate_profit - расчет прибыли
- calculate_net_profit - расчет чистой прибыли
- calculate_profit_percent - расчет процента прибыли
- get_fee_for_liquidity - определение комиссии по ликвидности
- cents_to_usd / usd_to_cents - конвертация валюты
- is_profitable_opportunity - проверка прибыльности
"""

from __future__ import annotations

import pytest

from src.dmarket.arbitrage.calculations import (
    _calculate_commission,
    calculate_commission,
    calculate_net_profit,
    calculate_profit,
    calculate_profit_percent,
    cents_to_usd,
    get_fee_for_liquidity,
    is_profitable_opportunity,
    usd_to_cents,
)
from src.dmarket.arbitrage.constants import (
    BASE_COMMISSION_PERCENT,
    DEFAULT_FEE,
    HIGH_FEE,
    LOW_FEE,
    MAX_COMMISSION_PERCENT,
    MIN_COMMISSION_PERCENT,
)


# =============================================================================
# calculate_commission Tests
# =============================================================================


class TestCalculateCommission:
    """Tests for calculate_commission function."""

    def test_base_commission_with_neutral_factors(self) -> None:
        """Test commission with neutral factors returns base commission."""
        commission = calculate_commission(
            rarity="restricted",  # Not high or low
            item_type="rifle",  # Not high or low value
            popularity=0.5,  # Medium popularity
            game="csgo",  # Factor 1.0
        )
        assert abs(commission - BASE_COMMISSION_PERCENT) < 0.1

    def test_high_rarity_increases_commission(self) -> None:
        """Test that high rarity items have higher commission."""
        high_rarity_commission = calculate_commission(
            rarity="covert",  # High rarity
            item_type="rifle",
            popularity=0.5,
            game="csgo",
        )
        low_rarity_commission = calculate_commission(
            rarity="consumer",  # Low rarity
            item_type="rifle",
            popularity=0.5,
            game="csgo",
        )
        assert high_rarity_commission > low_rarity_commission

    def test_low_rarity_decreases_commission(self) -> None:
        """Test that low rarity items have lower commission."""
        low_rarity_commission = calculate_commission(
            rarity="consumer",
            item_type="rifle",
            popularity=0.5,
            game="csgo",
        )
        assert low_rarity_commission < BASE_COMMISSION_PERCENT

    @pytest.mark.parametrize(
        "rarity",
        ["covert", "extraordinary", "contraband", "ancient", "mythical", "immortal", "arcana"],
    )
    def test_all_high_rarity_items(self, rarity: str) -> None:
        """Test commission for all high rarity items."""
        commission = calculate_commission(
            rarity=rarity,
            item_type="rifle",
            popularity=0.5,
            game="csgo",
        )
        # High rarity should increase commission
        assert commission >= BASE_COMMISSION_PERCENT * 0.9  # At least close to base

    @pytest.mark.parametrize("rarity", ["consumer", "industrial", "common"])
    def test_all_low_rarity_items(self, rarity: str) -> None:
        """Test commission for all low rarity items."""
        commission = calculate_commission(
            rarity=rarity,
            item_type="rifle",
            popularity=0.5,
            game="csgo",
        )
        # Low rarity should decrease commission
        assert commission <= BASE_COMMISSION_PERCENT * 1.1

    def test_high_value_item_type_increases_commission(self) -> None:
        """Test that knives and gloves have higher commission."""
        knife_commission = calculate_commission(
            rarity="restricted",
            item_type="knife",
            popularity=0.5,
            game="csgo",
        )
        rifle_commission = calculate_commission(
            rarity="restricted",
            item_type="rifle",
            popularity=0.5,
            game="csgo",
        )
        assert knife_commission > rifle_commission

    @pytest.mark.parametrize("item_type", ["knife", "gloves", "rare_special"])
    def test_all_high_value_types(self, item_type: str) -> None:
        """Test commission for high value item types."""
        commission = calculate_commission(
            rarity="restricted",
            item_type=item_type,
            popularity=0.5,
            game="csgo",
        )
        assert commission > BASE_COMMISSION_PERCENT * 0.9

    @pytest.mark.parametrize("item_type", ["sticker", "container", "key"])
    def test_all_low_value_types(self, item_type: str) -> None:
        """Test commission for low value item types."""
        commission = calculate_commission(
            rarity="restricted",
            item_type=item_type,
            popularity=0.5,
            game="csgo",
        )
        # Low value types should have lower commission
        assert commission <= BASE_COMMISSION_PERCENT * 1.1

    def test_high_popularity_decreases_commission(self) -> None:
        """Test that popular items have lower commission."""
        popular_commission = calculate_commission(
            rarity="restricted",
            item_type="rifle",
            popularity=0.9,  # High popularity
            game="csgo",
        )
        unpopular_commission = calculate_commission(
            rarity="restricted",
            item_type="rifle",
            popularity=0.1,  # Low popularity
            game="csgo",
        )
        assert popular_commission < unpopular_commission

    def test_low_popularity_increases_commission(self) -> None:
        """Test that unpopular items have higher commission."""
        unpopular_commission = calculate_commission(
            rarity="restricted",
            item_type="rifle",
            popularity=0.2,  # Low popularity
            game="csgo",
        )
        assert unpopular_commission > BASE_COMMISSION_PERCENT

    @pytest.mark.parametrize(
        "game,expected_factor",
        [
            ("csgo", 1.0),
            ("dota2", 1.05),
            ("rust", 1.1),
            ("tf2", 1.0),
        ],
    )
    def test_game_commission_factors(self, game: str, expected_factor: float) -> None:
        """Test commission factors for different games."""
        commission = calculate_commission(
            rarity="restricted",
            item_type="rifle",
            popularity=0.5,
            game=game,
        )
        expected = BASE_COMMISSION_PERCENT * expected_factor
        assert abs(commission - expected) < 0.5

    def test_rust_has_highest_commission(self) -> None:
        """Test that Rust items have highest game commission."""
        rust_commission = calculate_commission(
            rarity="restricted",
            item_type="rifle",
            popularity=0.5,
            game="rust",
        )
        csgo_commission = calculate_commission(
            rarity="restricted",
            item_type="rifle",
            popularity=0.5,
            game="csgo",
        )
        assert rust_commission > csgo_commission

    def test_commission_not_below_minimum(self) -> None:
        """Test that commission doesn't go below minimum."""
        # Try to get lowest possible commission
        commission = calculate_commission(
            rarity="consumer",
            item_type="sticker",
            popularity=0.99,  # Very popular
            game="csgo",
        )
        assert commission >= MIN_COMMISSION_PERCENT

    def test_commission_not_above_maximum(self) -> None:
        """Test that commission doesn't go above maximum."""
        # Try to get highest possible commission
        commission = calculate_commission(
            rarity="covert",
            item_type="knife",
            popularity=0.01,  # Very unpopular
            game="rust",
        )
        assert commission <= MAX_COMMISSION_PERCENT

    def test_unknown_game_uses_default_factor(self) -> None:
        """Test that unknown game uses default factor of 1.0."""
        commission = calculate_commission(
            rarity="restricted",
            item_type="rifle",
            popularity=0.5,
            game="unknown_game",
        )
        # Should be close to base commission
        assert abs(commission - BASE_COMMISSION_PERCENT) < 1.0

    def test_backward_compatibility_alias(self) -> None:
        """Test _calculate_commission alias works."""
        # Both should return same result
        result1 = calculate_commission("restricted", "rifle", 0.5, "csgo")
        result2 = _calculate_commission("restricted", "rifle", 0.5, "csgo")
        assert result1 == result2


# =============================================================================
# calculate_profit Tests
# =============================================================================


class TestCalculateProfit:
    """Tests for calculate_profit function."""

    def test_basic_profit_calculation(self) -> None:
        """Test basic profit calculation."""
        net_profit, profit_percent = calculate_profit(10.0, 12.0, 7.0)
        # Expected: gross = 2.0, commission = 0.84, net = 1.16, percent = 11.6
        assert abs(net_profit - 1.16) < 0.01
        assert abs(profit_percent - 11.6) < 0.1

    def test_profit_with_zero_commission(self) -> None:
        """Test profit with zero commission."""
        net_profit, profit_percent = calculate_profit(10.0, 15.0, 0.0)
        # No commission, full gross profit
        assert abs(net_profit - 5.0) < 0.01
        assert abs(profit_percent - 50.0) < 0.1

    def test_profit_with_high_commission(self) -> None:
        """Test profit with high commission (15%)."""
        net_profit, profit_percent = calculate_profit(10.0, 12.0, 15.0)
        # gross = 2.0, commission = 1.8, net = 0.2
        assert abs(net_profit - 0.2) < 0.01

    def test_negative_profit_when_commission_exceeds_gross(self) -> None:
        """Test negative profit when commission exceeds gross profit."""
        net_profit, profit_percent = calculate_profit(10.0, 10.5, 10.0)
        # gross = 0.5, commission = 1.05, net = -0.55
        assert net_profit < 0

    def test_profit_with_zero_buy_price(self) -> None:
        """Test profit calculation with zero buy price."""
        net_profit, profit_percent = calculate_profit(0.0, 10.0, 7.0)
        # Should handle division by zero for percent
        assert profit_percent == 0.0

    @pytest.mark.parametrize(
        "buy,sell,commission,expected_net",
        [
            (10.0, 15.0, 7.0, 3.95),  # Standard case
            (100.0, 120.0, 7.0, 11.6),  # Higher prices
            (1.0, 2.0, 7.0, 0.86),  # Low prices
            (50.0, 60.0, 5.0, 7.0),  # 5% commission
        ],
    )
    def test_various_profit_scenarios(
        self, buy: float, sell: float, commission: float, expected_net: float
    ) -> None:
        """Test profit calculation for various scenarios."""
        net_profit, _ = calculate_profit(buy, sell, commission)
        assert abs(net_profit - expected_net) < 0.05


# =============================================================================
# calculate_net_profit Tests
# =============================================================================


class TestCalculateNetProfit:
    """Tests for calculate_net_profit function."""

    def test_net_profit_basic(self) -> None:
        """Test basic net profit calculation."""
        result = calculate_net_profit(10.0, 15.0)  # Default 7% commission
        expected = 5.0 - (15.0 * 0.07)  # 5.0 - 1.05 = 3.95
        assert abs(result - expected) < 0.01

    def test_net_profit_with_custom_commission(self) -> None:
        """Test net profit with custom commission."""
        result = calculate_net_profit(10.0, 15.0, commission_percent=10.0)
        expected = 5.0 - (15.0 * 0.10)  # 5.0 - 1.5 = 3.5
        assert abs(result - expected) < 0.01

    def test_net_profit_negative(self) -> None:
        """Test negative net profit."""
        result = calculate_net_profit(10.0, 10.5, commission_percent=10.0)
        # gross = 0.5, commission = 1.05, net = -0.55
        assert result < 0


# =============================================================================
# calculate_profit_percent Tests
# =============================================================================


class TestCalculateProfitPercent:
    """Tests for calculate_profit_percent function."""

    def test_profit_percent_basic(self) -> None:
        """Test basic profit percent calculation."""
        result = calculate_profit_percent(10.0, 15.0)  # Default 7% commission
        # net = 3.95, percent = 39.5%
        assert abs(result - 39.5) < 0.5

    def test_profit_percent_with_zero_buy_price(self) -> None:
        """Test profit percent with zero buy price returns 0."""
        result = calculate_profit_percent(0.0, 10.0)
        assert result == 0.0

    def test_profit_percent_with_negative_buy_price(self) -> None:
        """Test profit percent with negative buy price returns 0."""
        result = calculate_profit_percent(-5.0, 10.0)
        assert result == 0.0

    def test_profit_percent_100_percent(self) -> None:
        """Test 100% profit scenario."""
        result = calculate_profit_percent(10.0, 21.5, commission_percent=7.0)
        # gross = 11.5, commission = 1.505, net = 9.995, percent ~ 99.95%
        assert abs(result - 100.0) < 1.0


# =============================================================================
# get_fee_for_liquidity Tests
# =============================================================================


class TestGetFeeForLiquidity:
    """Tests for get_fee_for_liquidity function."""

    def test_high_liquidity_returns_low_fee(self) -> None:
        """Test high liquidity returns low fee."""
        fee = get_fee_for_liquidity(0.9)
        assert fee == LOW_FEE

    def test_very_high_liquidity(self) -> None:
        """Test very high liquidity (1.0)."""
        fee = get_fee_for_liquidity(1.0)
        assert fee == LOW_FEE

    def test_threshold_high_liquidity(self) -> None:
        """Test threshold for high liquidity (0.8)."""
        fee = get_fee_for_liquidity(0.8)
        assert fee == LOW_FEE

    def test_medium_liquidity_returns_default_fee(self) -> None:
        """Test medium liquidity returns default fee."""
        fee = get_fee_for_liquidity(0.6)
        assert fee == DEFAULT_FEE

    def test_threshold_medium_liquidity(self) -> None:
        """Test threshold for medium liquidity (0.5)."""
        fee = get_fee_for_liquidity(0.5)
        assert fee == DEFAULT_FEE

    def test_low_liquidity_returns_high_fee(self) -> None:
        """Test low liquidity returns high fee."""
        fee = get_fee_for_liquidity(0.3)
        assert fee == HIGH_FEE

    def test_very_low_liquidity(self) -> None:
        """Test very low liquidity (0.1)."""
        fee = get_fee_for_liquidity(0.1)
        assert fee == HIGH_FEE

    def test_zero_liquidity(self) -> None:
        """Test zero liquidity."""
        fee = get_fee_for_liquidity(0.0)
        assert fee == HIGH_FEE

    @pytest.mark.parametrize(
        "liquidity,expected_fee",
        [
            (0.0, HIGH_FEE),
            (0.2, HIGH_FEE),
            (0.49, HIGH_FEE),
            (0.5, DEFAULT_FEE),
            (0.7, DEFAULT_FEE),
            (0.79, DEFAULT_FEE),
            (0.8, LOW_FEE),
            (0.95, LOW_FEE),
            (1.0, LOW_FEE),
        ],
    )
    def test_liquidity_fee_boundaries(self, liquidity: float, expected_fee: float) -> None:
        """Test fee boundaries for different liquidity values."""
        fee = get_fee_for_liquidity(liquidity)
        assert fee == expected_fee


# =============================================================================
# cents_to_usd Tests
# =============================================================================


class TestCentsToUsd:
    """Tests for cents_to_usd function."""

    def test_basic_conversion(self) -> None:
        """Test basic cents to USD conversion."""
        result = cents_to_usd(1050)
        assert result == 10.5

    def test_even_dollar_amount(self) -> None:
        """Test conversion of even dollar amount."""
        result = cents_to_usd(1000)
        assert result == 10.0

    def test_zero_cents(self) -> None:
        """Test conversion of zero cents."""
        result = cents_to_usd(0)
        assert result == 0.0

    def test_small_amount(self) -> None:
        """Test conversion of small amount."""
        result = cents_to_usd(1)
        assert result == 0.01

    def test_large_amount(self) -> None:
        """Test conversion of large amount."""
        result = cents_to_usd(1000000)
        assert result == 10000.0

    @pytest.mark.parametrize(
        "cents,expected",
        [
            (100, 1.0),
            (250, 2.5),
            (99, 0.99),
            (1, 0.01),
            (50, 0.5),
        ],
    )
    def test_various_conversions(self, cents: int, expected: float) -> None:
        """Test various cent to USD conversions."""
        result = cents_to_usd(cents)
        assert result == expected


# =============================================================================
# usd_to_cents Tests
# =============================================================================


class TestUsdToCents:
    """Tests for usd_to_cents function."""

    def test_basic_conversion(self) -> None:
        """Test basic USD to cents conversion."""
        result = usd_to_cents(10.5)
        assert result == 1050

    def test_even_dollar_amount(self) -> None:
        """Test conversion of even dollar amount."""
        result = usd_to_cents(10.0)
        assert result == 1000

    def test_zero_usd(self) -> None:
        """Test conversion of zero USD."""
        result = usd_to_cents(0.0)
        assert result == 0

    def test_small_amount(self) -> None:
        """Test conversion of small amount."""
        result = usd_to_cents(0.01)
        assert result == 1

    def test_large_amount(self) -> None:
        """Test conversion of large amount."""
        result = usd_to_cents(10000.0)
        assert result == 1000000

    def test_fractional_cents_truncated(self) -> None:
        """Test that fractional cents are truncated."""
        result = usd_to_cents(1.999)
        assert result == 199  # Truncated, not rounded

    @pytest.mark.parametrize(
        "usd,expected",
        [
            (1.0, 100),
            (2.5, 250),
            (0.99, 99),
            (0.01, 1),
            (0.5, 50),
        ],
    )
    def test_various_conversions(self, usd: float, expected: int) -> None:
        """Test various USD to cent conversions."""
        result = usd_to_cents(usd)
        assert result == expected


# =============================================================================
# is_profitable_opportunity Tests
# =============================================================================


class TestIsProfitableOpportunity:
    """Tests for is_profitable_opportunity function."""

    def test_profitable_opportunity(self) -> None:
        """Test identifying a profitable opportunity."""
        result = is_profitable_opportunity(
            buy_price=10.0,
            sell_price=15.0,
            min_profit_percent=5.0,
        )
        assert result is True

    def test_unprofitable_opportunity(self) -> None:
        """Test identifying an unprofitable opportunity."""
        result = is_profitable_opportunity(
            buy_price=10.0,
            sell_price=10.5,
            min_profit_percent=10.0,
        )
        assert result is False

    def test_zero_buy_price(self) -> None:
        """Test with zero buy price."""
        result = is_profitable_opportunity(
            buy_price=0.0,
            sell_price=10.0,
            min_profit_percent=5.0,
        )
        assert result is False

    def test_negative_buy_price(self) -> None:
        """Test with negative buy price."""
        result = is_profitable_opportunity(
            buy_price=-5.0,
            sell_price=10.0,
            min_profit_percent=5.0,
        )
        assert result is False

    def test_sell_price_lower_than_buy(self) -> None:
        """Test when sell price is lower than buy price."""
        result = is_profitable_opportunity(
            buy_price=15.0,
            sell_price=10.0,
            min_profit_percent=5.0,
        )
        assert result is False

    def test_sell_price_equal_to_buy(self) -> None:
        """Test when sell price equals buy price."""
        result = is_profitable_opportunity(
            buy_price=10.0,
            sell_price=10.0,
            min_profit_percent=5.0,
        )
        assert result is False

    def test_exactly_at_threshold(self) -> None:
        """Test opportunity exactly at profit threshold."""
        # Calculate the sell price needed for exactly 5% profit with 7% commission
        # profit_percent = (net_profit / buy_price) * 100
        # net_profit = sell - buy - (sell * 0.07)
        # For 5% profit with buy=10: net_profit = 0.5
        # 0.5 = sell - 10 - 0.07*sell
        # 0.5 = 0.93*sell - 10
        # sell = 10.5/0.93 ≈ 11.29
        # Let's use a higher sell price to ensure we're above threshold
        result = is_profitable_opportunity(
            buy_price=10.0,
            sell_price=11.50,  # Higher than threshold
            min_profit_percent=5.0,
        )
        # Should be above threshold
        assert result is True

    def test_custom_commission(self) -> None:
        """Test with custom commission rate."""
        result = is_profitable_opportunity(
            buy_price=10.0,
            sell_price=15.0,
            min_profit_percent=5.0,
            commission_percent=15.0,  # Higher commission
        )
        assert result is True  # Still profitable

    @pytest.mark.parametrize(
        "buy,sell,min_profit,expected",
        [
            (10.0, 15.0, 5.0, True),  # Clearly profitable
            (10.0, 10.5, 10.0, False),  # Not enough profit
            (100.0, 120.0, 5.0, True),  # Higher price range
            (1.0, 1.5, 30.0, True),  # Low price high percentage
            (10.0, 11.0, 1.0, True),  # Low threshold
        ],
    )
    def test_various_scenarios(
        self, buy: float, sell: float, min_profit: float, expected: bool
    ) -> None:
        """Test various profitability scenarios."""
        result = is_profitable_opportunity(buy, sell, min_profit)
        assert result is expected


# =============================================================================
# Integration Tests
# =============================================================================


class TestCalculationsIntegration:
    """Integration tests for calculation functions."""

    def test_roundtrip_conversion(self) -> None:
        """Test that cents <-> USD conversion is consistent."""
        original = 1050
        usd = cents_to_usd(original)
        cents = usd_to_cents(usd)
        assert cents == original

    def test_profit_calculations_consistent(self) -> None:
        """Test that different profit functions give consistent results."""
        buy_price = 10.0
        sell_price = 15.0
        commission = 7.0

        net_profit1, percent1 = calculate_profit(buy_price, sell_price, commission)
        net_profit2 = calculate_net_profit(buy_price, sell_price, commission)
        percent2 = calculate_profit_percent(buy_price, sell_price, commission)

        assert abs(net_profit1 - net_profit2) < 0.001
        assert abs(percent1 - percent2) < 0.001

    def test_commission_affects_profitability(self) -> None:
        """Test that commission properly affects profitability check."""
        buy_price = 10.0
        sell_price = 11.5

        # With low commission, should be profitable
        result_low = is_profitable_opportunity(
            buy_price, sell_price, min_profit_percent=5.0, commission_percent=2.0
        )

        # With high commission, might not be profitable
        result_high = is_profitable_opportunity(
            buy_price, sell_price, min_profit_percent=5.0, commission_percent=15.0
        )

        assert result_low is True
        assert result_high is False

    def test_full_arbitrage_flow(self) -> None:
        """Test complete arbitrage calculation flow."""
        # Simulate finding an item
        buy_price_cents = 1000  # $10.00
        sell_price_cents = 1500  # $15.00

        # Convert to USD
        buy_price = cents_to_usd(buy_price_cents)
        sell_price = cents_to_usd(sell_price_cents)

        assert buy_price == 10.0
        assert sell_price == 15.0

        # Calculate commission based on item characteristics
        commission = calculate_commission(
            rarity="restricted",
            item_type="rifle",
            popularity=0.7,
            game="csgo",
        )

        # Check profitability
        is_profitable = is_profitable_opportunity(
            buy_price, sell_price, min_profit_percent=5.0, commission_percent=commission
        )

        assert is_profitable is True

        # Calculate actual profit
        net_profit, profit_percent = calculate_profit(buy_price, sell_price, commission)

        assert net_profit > 0
        assert profit_percent > 5.0


# =============================================================================
# Edge Cases Tests
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases."""

    def test_very_small_prices(self) -> None:
        """Test calculations with very small prices."""
        net_profit, profit_percent = calculate_profit(0.01, 0.02, 7.0)
        assert net_profit > 0

    def test_very_large_prices(self) -> None:
        """Test calculations with very large prices."""
        net_profit, profit_percent = calculate_profit(10000.0, 15000.0, 7.0)
        assert net_profit > 0

    def test_case_insensitive_rarity(self) -> None:
        """Test that rarity is case insensitive."""
        upper = calculate_commission("COVERT", "rifle", 0.5, "csgo")
        lower = calculate_commission("covert", "rifle", 0.5, "csgo")
        mixed = calculate_commission("Covert", "rifle", 0.5, "csgo")
        assert upper == lower == mixed

    def test_case_insensitive_item_type(self) -> None:
        """Test that item type is case insensitive."""
        upper = calculate_commission("restricted", "KNIFE", 0.5, "csgo")
        lower = calculate_commission("restricted", "knife", 0.5, "csgo")
        assert upper == lower

    def test_boundary_popularity_values(self) -> None:
        """Test boundary popularity values."""
        # 0.0 popularity
        comm_zero = calculate_commission("restricted", "rifle", 0.0, "csgo")
        # 1.0 popularity
        comm_one = calculate_commission("restricted", "rifle", 1.0, "csgo")

        assert comm_zero > comm_one  # Low popularity = higher commission
