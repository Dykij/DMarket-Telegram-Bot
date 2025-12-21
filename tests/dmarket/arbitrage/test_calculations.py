"""Comprehensive tests for arbitrage calculations module.

Tests calculate_commission, calculate_profit, calculate_net_profit,
calculate_profit_percent, get_fee_for_liquidity, cents_to_usd, usd_to_cents,
is_profitable_opportunity functions.
"""

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


# =============================================================================
# calculate_commission tests
# =============================================================================


class TestCalculateCommission:
    """Tests for calculate_commission function."""

    def test_calculate_commission_base_case(self):
        """Test base commission calculation with average parameters."""
        # Average rarity, average type, average popularity, csgo
        commission = calculate_commission(
            rarity="mil-spec",
            item_type="rifle",
            popularity=0.5,
            game="csgo",
        )
        # Should be close to base commission (7%)
        assert 6.0 <= commission <= 8.0

    def test_calculate_commission_high_rarity(self):
        """Test commission increases for high rarity items."""
        high_rarity = calculate_commission(
            rarity="covert",
            item_type="rifle",
            popularity=0.5,
            game="csgo",
        )
        low_rarity = calculate_commission(
            rarity="consumer",
            item_type="rifle",
            popularity=0.5,
            game="csgo",
        )
        # High rarity should have higher commission
        assert high_rarity > low_rarity

    def test_calculate_commission_high_value_item_type(self):
        """Test commission increases for high value item types."""
        knife_commission = calculate_commission(
            rarity="mil-spec",
            item_type="knife",
            popularity=0.5,
            game="csgo",
        )
        rifle_commission = calculate_commission(
            rarity="mil-spec",
            item_type="rifle",
            popularity=0.5,
            game="csgo",
        )
        # Knife should have higher commission
        assert knife_commission > rifle_commission

    def test_calculate_commission_low_value_item_type(self):
        """Test commission decreases for low value item types."""
        sticker_commission = calculate_commission(
            rarity="mil-spec",
            item_type="sticker",
            popularity=0.5,
            game="csgo",
        )
        rifle_commission = calculate_commission(
            rarity="mil-spec",
            item_type="rifle",
            popularity=0.5,
            game="csgo",
        )
        # Sticker should have lower commission
        assert sticker_commission < rifle_commission

    def test_calculate_commission_high_popularity(self):
        """Test commission decreases for popular items."""
        popular = calculate_commission(
            rarity="mil-spec",
            item_type="rifle",
            popularity=0.9,
            game="csgo",
        )
        unpopular = calculate_commission(
            rarity="mil-spec",
            item_type="rifle",
            popularity=0.1,
            game="csgo",
        )
        # Popular items should have lower commission
        assert popular < unpopular

    def test_calculate_commission_rust_game(self):
        """Test Rust game has higher commission factor."""
        rust_commission = calculate_commission(
            rarity="mil-spec",
            item_type="rifle",
            popularity=0.5,
            game="rust",
        )
        csgo_commission = calculate_commission(
            rarity="mil-spec",
            item_type="rifle",
            popularity=0.5,
            game="csgo",
        )
        # Rust should have higher commission
        assert rust_commission > csgo_commission

    def test_calculate_commission_dota2_game(self):
        """Test Dota 2 game commission factor."""
        dota2_commission = calculate_commission(
            rarity="mythical",
            item_type="immortal",
            popularity=0.5,
            game="dota2",
        )
        # Should be within valid range
        assert 2.0 <= dota2_commission <= 15.0

    def test_calculate_commission_minimum_bound(self):
        """Test commission doesn't go below minimum."""
        # Low rarity, low value type, high popularity, csgo
        commission = calculate_commission(
            rarity="consumer",
            item_type="sticker",
            popularity=0.99,
            game="csgo",
        )
        # Should be at least MIN_COMMISSION_PERCENT (2.0)
        assert commission >= 2.0

    def test_calculate_commission_maximum_bound(self):
        """Test commission doesn't exceed maximum."""
        # High rarity, high value type, low popularity, rust
        commission = calculate_commission(
            rarity="covert",
            item_type="knife",
            popularity=0.01,
            game="rust",
        )
        # Should be at most MAX_COMMISSION_PERCENT (15.0)
        assert commission <= 15.0

    def test_calculate_commission_case_insensitive_rarity(self):
        """Test rarity is case-insensitive."""
        upper = calculate_commission(
            rarity="COVERT",
            item_type="rifle",
            popularity=0.5,
            game="csgo",
        )
        lower = calculate_commission(
            rarity="covert",
            item_type="rifle",
            popularity=0.5,
            game="csgo",
        )
        assert upper == lower

    def test_calculate_commission_case_insensitive_item_type(self):
        """Test item_type is case-insensitive."""
        upper = calculate_commission(
            rarity="mil-spec",
            item_type="KNIFE",
            popularity=0.5,
            game="csgo",
        )
        lower = calculate_commission(
            rarity="mil-spec",
            item_type="knife",
            popularity=0.5,
            game="csgo",
        )
        assert upper == lower

    def test_calculate_commission_unknown_game(self):
        """Test unknown game uses default factor."""
        unknown = calculate_commission(
            rarity="mil-spec",
            item_type="rifle",
            popularity=0.5,
            game="unknown_game",
        )
        # Should use default factor of 1.0
        csgo = calculate_commission(
            rarity="mil-spec",
            item_type="rifle",
            popularity=0.5,
            game="csgo",
        )
        assert unknown == csgo


class TestCalculateCommissionAlias:
    """Tests for _calculate_commission backward compatibility alias."""

    def test_alias_works_same_as_original(self):
        """Test _calculate_commission alias produces same results."""
        original = calculate_commission(
            rarity="covert",
            item_type="knife",
            popularity=0.9,
            game="csgo",
        )
        alias = _calculate_commission(
            rarity="covert",
            item_type="knife",
            popularity=0.9,
            game="csgo",
        )
        assert original == alias


# =============================================================================
# calculate_profit tests
# =============================================================================


class TestCalculateProfit:
    """Tests for calculate_profit function."""

    def test_calculate_profit_basic(self):
        """Test basic profit calculation."""
        net_profit, profit_percent = calculate_profit(
            buy_price=10.0,
            sell_price=12.0,
            commission_percent=7.0,
        )
        # Gross profit = 2.0
        # Commission = 12.0 * 0.07 = 0.84
        # Net profit = 2.0 - 0.84 = 1.16
        # Profit percent = (1.16 / 10.0) * 100 = 11.6%
        assert abs(net_profit - 1.16) < 0.01
        assert abs(profit_percent - 11.6) < 0.1

    def test_calculate_profit_zero_commission(self):
        """Test profit with zero commission."""
        net_profit, profit_percent = calculate_profit(
            buy_price=10.0,
            sell_price=15.0,
            commission_percent=0.0,
        )
        # No commission, full gross profit
        assert abs(net_profit - 5.0) < 0.01
        assert abs(profit_percent - 50.0) < 0.1

    def test_calculate_profit_high_commission(self):
        """Test profit with high commission."""
        net_profit, profit_percent = calculate_profit(
            buy_price=10.0,
            sell_price=12.0,
            commission_percent=15.0,
        )
        # Commission = 12.0 * 0.15 = 1.8
        # Net profit = 2.0 - 1.8 = 0.2
        assert abs(net_profit - 0.2) < 0.01

    def test_calculate_profit_negative_result(self):
        """Test profit calculation resulting in negative profit."""
        net_profit, profit_percent = calculate_profit(
            buy_price=10.0,
            sell_price=10.5,
            commission_percent=10.0,
        )
        # Gross profit = 0.5
        # Commission = 10.5 * 0.10 = 1.05
        # Net profit = 0.5 - 1.05 = -0.55
        assert net_profit < 0

    def test_calculate_profit_zero_buy_price(self):
        """Test profit with zero buy price."""
        net_profit, profit_percent = calculate_profit(
            buy_price=0.0,
            sell_price=10.0,
            commission_percent=7.0,
        )
        # Zero buy price should result in 0% profit (avoiding division by zero)
        assert profit_percent == 0.0

    def test_calculate_profit_large_values(self):
        """Test profit calculation with large values."""
        net_profit, profit_percent = calculate_profit(
            buy_price=1000.0,
            sell_price=1200.0,
            commission_percent=7.0,
        )
        # Should handle large values correctly
        assert net_profit > 0
        assert profit_percent > 0


# =============================================================================
# calculate_net_profit tests
# =============================================================================


class TestCalculateNetProfit:
    """Tests for calculate_net_profit function."""

    def test_calculate_net_profit_basic(self):
        """Test basic net profit calculation."""
        profit = calculate_net_profit(
            buy_price=10.0,
            sell_price=12.0,
            commission_percent=7.0,
        )
        # Net profit = 2.0 - (12.0 * 0.07) = 2.0 - 0.84 = 1.16
        assert abs(profit - 1.16) < 0.01

    def test_calculate_net_profit_default_commission(self):
        """Test net profit with default 7% commission."""
        profit = calculate_net_profit(
            buy_price=10.0,
            sell_price=12.0,
        )
        # Uses default 7% commission
        assert abs(profit - 1.16) < 0.01

    def test_calculate_net_profit_negative(self):
        """Test net profit can be negative."""
        profit = calculate_net_profit(
            buy_price=10.0,
            sell_price=10.1,
            commission_percent=7.0,
        )
        # Gross profit = 0.1
        # Commission = 10.1 * 0.07 = 0.707
        # Net profit = 0.1 - 0.707 = -0.607
        assert profit < 0

    def test_calculate_net_profit_break_even(self):
        """Test net profit at break-even point."""
        # At what sell price is profit exactly 0?
        # 0 = sell_price - buy_price - (sell_price * 0.07)
        # 0 = 0.93 * sell_price - buy_price
        # sell_price = buy_price / 0.93
        buy_price = 10.0
        sell_price = buy_price / 0.93  # ~10.75
        profit = calculate_net_profit(buy_price, sell_price, 7.0)
        assert abs(profit) < 0.01


# =============================================================================
# calculate_profit_percent tests
# =============================================================================


class TestCalculateProfitPercent:
    """Tests for calculate_profit_percent function."""

    def test_calculate_profit_percent_basic(self):
        """Test basic profit percent calculation."""
        percent = calculate_profit_percent(
            buy_price=10.0,
            sell_price=12.0,
            commission_percent=7.0,
        )
        # Profit percent = (1.16 / 10.0) * 100 = 11.6%
        assert abs(percent - 11.6) < 0.1

    def test_calculate_profit_percent_zero_buy_price(self):
        """Test profit percent with zero buy price returns 0."""
        percent = calculate_profit_percent(
            buy_price=0.0,
            sell_price=10.0,
            commission_percent=7.0,
        )
        assert percent == 0.0

    def test_calculate_profit_percent_negative_buy_price(self):
        """Test profit percent with negative buy price returns 0."""
        percent = calculate_profit_percent(
            buy_price=-10.0,
            sell_price=10.0,
            commission_percent=7.0,
        )
        assert percent == 0.0

    def test_calculate_profit_percent_default_commission(self):
        """Test profit percent with default commission."""
        percent = calculate_profit_percent(
            buy_price=10.0,
            sell_price=12.0,
        )
        # Uses default 7% commission
        assert percent > 0


# =============================================================================
# get_fee_for_liquidity tests
# =============================================================================


class TestGetFeeForLiquidity:
    """Tests for get_fee_for_liquidity function."""

    def test_fee_high_liquidity(self):
        """Test fee for high liquidity items (>= 0.8)."""
        fee = get_fee_for_liquidity(0.9)
        assert fee == 0.02  # LOW_FEE

    def test_fee_high_liquidity_threshold(self):
        """Test fee at exact high liquidity threshold."""
        fee = get_fee_for_liquidity(0.8)
        assert fee == 0.02  # LOW_FEE

    def test_fee_medium_liquidity(self):
        """Test fee for medium liquidity items (0.5 - 0.8)."""
        fee = get_fee_for_liquidity(0.6)
        assert fee == 0.07  # DEFAULT_FEE

    def test_fee_medium_liquidity_threshold(self):
        """Test fee at exact medium liquidity threshold."""
        fee = get_fee_for_liquidity(0.5)
        assert fee == 0.07  # DEFAULT_FEE

    def test_fee_low_liquidity(self):
        """Test fee for low liquidity items (< 0.5)."""
        fee = get_fee_for_liquidity(0.3)
        assert fee == 0.10  # HIGH_FEE

    def test_fee_zero_liquidity(self):
        """Test fee for zero liquidity."""
        fee = get_fee_for_liquidity(0.0)
        assert fee == 0.10  # HIGH_FEE

    def test_fee_perfect_liquidity(self):
        """Test fee for perfect liquidity."""
        fee = get_fee_for_liquidity(1.0)
        assert fee == 0.02  # LOW_FEE


# =============================================================================
# cents_to_usd tests
# =============================================================================


class TestCentsToUsd:
    """Tests for cents_to_usd function."""

    def test_cents_to_usd_basic(self):
        """Test basic cents to USD conversion."""
        assert cents_to_usd(1050) == 10.5

    def test_cents_to_usd_zero(self):
        """Test zero cents to USD."""
        assert cents_to_usd(0) == 0.0

    def test_cents_to_usd_one_cent(self):
        """Test one cent to USD."""
        assert cents_to_usd(1) == 0.01

    def test_cents_to_usd_large_value(self):
        """Test large cents value."""
        assert cents_to_usd(1000000) == 10000.0

    def test_cents_to_usd_negative(self):
        """Test negative cents value."""
        assert cents_to_usd(-500) == -5.0


# =============================================================================
# usd_to_cents tests
# =============================================================================


class TestUsdToCents:
    """Tests for usd_to_cents function."""

    def test_usd_to_cents_basic(self):
        """Test basic USD to cents conversion."""
        assert usd_to_cents(10.5) == 1050

    def test_usd_to_cents_zero(self):
        """Test zero USD to cents."""
        assert usd_to_cents(0.0) == 0

    def test_usd_to_cents_one_cent(self):
        """Test one cent value."""
        assert usd_to_cents(0.01) == 1

    def test_usd_to_cents_large_value(self):
        """Test large USD value."""
        assert usd_to_cents(10000.0) == 1000000

    def test_usd_to_cents_rounds_down(self):
        """Test USD to cents rounds down (int conversion)."""
        assert usd_to_cents(10.555) == 1055  # Rounds down from 1055.5


# =============================================================================
# is_profitable_opportunity tests
# =============================================================================


class TestIsProfitableOpportunity:
    """Tests for is_profitable_opportunity function."""

    def test_profitable_opportunity_true(self):
        """Test opportunity that is profitable."""
        result = is_profitable_opportunity(
            buy_price=10.0,
            sell_price=15.0,
            min_profit_percent=10.0,
            commission_percent=7.0,
        )
        assert result is True

    def test_profitable_opportunity_false(self):
        """Test opportunity that is not profitable enough."""
        result = is_profitable_opportunity(
            buy_price=10.0,
            sell_price=11.0,
            min_profit_percent=10.0,
            commission_percent=7.0,
        )
        assert result is False

    def test_profitable_opportunity_zero_buy_price(self):
        """Test opportunity with zero buy price returns False."""
        result = is_profitable_opportunity(
            buy_price=0.0,
            sell_price=10.0,
            min_profit_percent=5.0,
            commission_percent=7.0,
        )
        assert result is False

    def test_profitable_opportunity_negative_buy_price(self):
        """Test opportunity with negative buy price returns False."""
        result = is_profitable_opportunity(
            buy_price=-10.0,
            sell_price=10.0,
            min_profit_percent=5.0,
            commission_percent=7.0,
        )
        assert result is False

    def test_profitable_opportunity_sell_equals_buy(self):
        """Test opportunity where sell equals buy returns False."""
        result = is_profitable_opportunity(
            buy_price=10.0,
            sell_price=10.0,
            min_profit_percent=5.0,
            commission_percent=7.0,
        )
        assert result is False

    def test_profitable_opportunity_sell_less_than_buy(self):
        """Test opportunity where sell is less than buy returns False."""
        result = is_profitable_opportunity(
            buy_price=10.0,
            sell_price=8.0,
            min_profit_percent=5.0,
            commission_percent=7.0,
        )
        assert result is False

    def test_profitable_opportunity_default_commission(self):
        """Test opportunity with default commission."""
        result = is_profitable_opportunity(
            buy_price=10.0,
            sell_price=15.0,
            min_profit_percent=10.0,
        )
        # Uses default 7% commission
        assert result is True

    def test_profitable_opportunity_exact_threshold(self):
        """Test opportunity at exact profit threshold."""
        # Calculate what sell price gives exactly 10% profit with 7% commission
        # profit_percent = ((sell - buy - sell * 0.07) / buy) * 100 = 10
        # (sell - buy - sell * 0.07) = buy * 0.1
        # sell * 0.93 - buy = buy * 0.1
        # sell = buy * 1.1 / 0.93
        buy_price = 10.0
        sell_price = buy_price * 1.1 / 0.93  # ~11.83

        result = is_profitable_opportunity(
            buy_price=buy_price,
            sell_price=sell_price,
            min_profit_percent=10.0,
            commission_percent=7.0,
        )
        # Should be at or above threshold
        assert result is True


# =============================================================================
# Integration tests
# =============================================================================


class TestCalculationsIntegration:
    """Integration tests for calculations module."""

    def test_profit_consistency(self):
        """Test that different profit functions give consistent results."""
        buy_price = 10.0
        sell_price = 15.0
        commission = 7.0

        # Get results from different functions
        net_profit, profit_percent = calculate_profit(buy_price, sell_price, commission)
        net_profit_direct = calculate_net_profit(buy_price, sell_price, commission)
        profit_percent_direct = calculate_profit_percent(buy_price, sell_price, commission)

        # Results should match
        assert abs(net_profit - net_profit_direct) < 0.001
        assert abs(profit_percent - profit_percent_direct) < 0.001

    def test_cents_usd_roundtrip(self):
        """Test converting cents to USD and back."""
        original_cents = 1234
        usd = cents_to_usd(original_cents)
        back_to_cents = usd_to_cents(usd)
        assert original_cents == back_to_cents

    def test_commission_affects_profitability(self):
        """Test that commission affects profitability determination."""
        buy_price = 10.0
        sell_price = 12.0

        # With low commission, should be profitable
        low_comm_result = is_profitable_opportunity(
            buy_price=buy_price,
            sell_price=sell_price,
            min_profit_percent=10.0,
            commission_percent=2.0,
        )

        # With high commission, might not be profitable
        high_comm_result = is_profitable_opportunity(
            buy_price=buy_price,
            sell_price=sell_price,
            min_profit_percent=10.0,
            commission_percent=15.0,
        )

        assert low_comm_result is True
        assert high_comm_result is False


# =============================================================================
# Parametrized tests
# =============================================================================


class TestParametrizedCalculations:
    """Parametrized tests for calculations."""

    @pytest.mark.parametrize(
        "rarity,expected_factor",
        [
            ("covert", "high"),
            ("contraband", "high"),
            ("mythical", "high"),
            ("consumer", "low"),
            ("industrial", "low"),
            ("common", "low"),
            ("mil-spec", "normal"),
            ("restricted", "normal"),
        ],
    )
    def test_rarity_factors(self, rarity: str, expected_factor: str):
        """Test commission varies correctly by rarity."""
        commission = calculate_commission(
            rarity=rarity,
            item_type="rifle",
            popularity=0.5,
            game="csgo",
        )

        # All should be within valid range
        assert 2.0 <= commission <= 15.0

    @pytest.mark.parametrize(
        "buy,sell,commission,expected_positive",
        [
            (10.0, 15.0, 7.0, True),
            (10.0, 10.5, 7.0, False),
            (10.0, 12.0, 15.0, True),  # Net profit = 2 - 1.8 = 0.2 > 0
            (10.0, 20.0, 7.0, True),
            (100.0, 110.0, 5.0, True),
        ],
    )
    def test_profit_scenarios(
        self,
        buy: float,
        sell: float,
        commission: float,
        expected_positive: bool,
    ):
        """Test various profit scenarios."""
        net_profit, _ = calculate_profit(buy, sell, commission)
        is_positive = net_profit > 0
        assert is_positive == expected_positive

    @pytest.mark.parametrize(
        "liquidity,expected_fee",
        [
            (1.0, 0.02),
            (0.8, 0.02),
            (0.79, 0.07),
            (0.5, 0.07),
            (0.49, 0.10),
            (0.0, 0.10),
        ],
    )
    def test_liquidity_fees(self, liquidity: float, expected_fee: float):
        """Test liquidity fee calculation."""
        fee = get_fee_for_liquidity(liquidity)
        assert fee == expected_fee
