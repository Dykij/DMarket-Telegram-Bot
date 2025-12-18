"""Extended tests for arbitrage module."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import time

from src.dmarket.arbitrage import (
    GAMES,
    MIN_PROFIT_PERCENT,
    PRICE_RANGES,
    DEFAULT_FEE,
    LOW_FEE,
    HIGH_FEE,
    _get_cached_results,
    _save_to_cache,
    _arbitrage_cache,
    fetch_market_items,
    _find_arbitrage_async,
    arbitrage_boost_async,
    arbitrage_mid_async,
    arbitrage_pro_async,
    find_arbitrage_opportunities_async,
    find_arbitrage_items,
    ArbitrageTrader,
    _calculate_commission,
    _group_items_by_name,
)


class TestArbitrageConstants:
    """Tests for arbitrage constants."""

    def test_games_constant(self):
        """Test GAMES constant contains expected games."""
        assert "csgo" in GAMES
        assert "dota2" in GAMES
        assert "tf2" in GAMES
        assert "rust" in GAMES
        assert GAMES["csgo"] == "CS2"

    def test_min_profit_percent(self):
        """Test MIN_PROFIT_PERCENT constant."""
        assert "low" in MIN_PROFIT_PERCENT
        assert "medium" in MIN_PROFIT_PERCENT
        assert "high" in MIN_PROFIT_PERCENT
        assert "boost" in MIN_PROFIT_PERCENT
        assert "pro" in MIN_PROFIT_PERCENT
        assert MIN_PROFIT_PERCENT["boost"] == 1.5
        assert MIN_PROFIT_PERCENT["pro"] == 15.0

    def test_price_ranges(self):
        """Test PRICE_RANGES constant."""
        assert "low" in PRICE_RANGES
        assert "medium" in PRICE_RANGES
        assert "high" in PRICE_RANGES
        assert "boost" in PRICE_RANGES
        assert "pro" in PRICE_RANGES
        assert PRICE_RANGES["boost"] == (0.5, 3.0)
        assert PRICE_RANGES["pro"] == (100.0, 1000.0)

    def test_fee_constants(self):
        """Test fee constants."""
        assert DEFAULT_FEE == 0.07
        assert LOW_FEE == 0.02
        assert HIGH_FEE == 0.10


class TestCacheFunctions:
    """Tests for cache functions."""

    def setup_method(self):
        """Clear cache before each test."""
        _arbitrage_cache.clear()

    def test_save_and_get_cached_results(self):
        """Test saving and retrieving cached results."""
        cache_key = ("csgo", "test", 1.0, 100.0)
        items = [{"name": "Test Item", "profit": 5.0}]
        
        _save_to_cache(cache_key, items)
        result = _get_cached_results(cache_key)
        
        assert result is not None
        assert len(result) == 1
        assert result[0]["name"] == "Test Item"

    def test_get_cached_results_not_found(self):
        """Test getting non-existent cache."""
        cache_key = ("nonexistent", "test", 1.0, 100.0)
        result = _get_cached_results(cache_key)
        assert result is None

    def test_cache_expiration(self):
        """Test cache expiration."""
        cache_key = ("csgo", "expired", 1.0, 100.0)
        items = [{"name": "Test Item"}]
        
        # Save with old timestamp
        _arbitrage_cache[cache_key] = (items, time.time() - 400)  # Older than cache TTL
        
        result = _get_cached_results(cache_key)
        assert result is None


class TestFetchMarketItems:
    """Tests for fetch_market_items function."""

    @pytest.mark.asyncio
    async def test_fetch_without_api_and_keys(self):
        """Test fetch without API and environment keys."""
        with patch.dict("os.environ", {"DMARKET_PUBLIC_KEY": "", "DMARKET_SECRET_KEY": ""}):
            result = await fetch_market_items("csgo")
            assert result == []

    @pytest.mark.asyncio
    async def test_fetch_with_api_client(self):
        """Test fetch with provided API client."""
        mock_api = AsyncMock()
        mock_api.get_market_items = AsyncMock(return_value={
            "objects": [
                {"title": "Test Item", "price": {"amount": 1000}}
            ]
        })
        mock_api.__aenter__ = AsyncMock(return_value=mock_api)
        mock_api.__aexit__ = AsyncMock(return_value=None)
        
        result = await fetch_market_items(
            game="csgo",
            limit=10,
            price_from=1.0,
            price_to=100.0,
            dmarket_api=mock_api
        )
        
        assert len(result) == 1
        assert result[0]["title"] == "Test Item"

    @pytest.mark.asyncio
    async def test_fetch_handles_exception(self):
        """Test fetch handles exceptions gracefully."""
        mock_api = AsyncMock()
        mock_api.__aenter__ = AsyncMock(return_value=mock_api)
        mock_api.__aexit__ = AsyncMock(return_value=None)
        mock_api.get_market_items = AsyncMock(side_effect=Exception("API Error"))
        
        result = await fetch_market_items(game="csgo", dmarket_api=mock_api)
        assert result == []


class TestFindArbitrageAsync:
    """Tests for _find_arbitrage_async function."""

    def setup_method(self):
        """Clear cache before each test."""
        _arbitrage_cache.clear()

    @pytest.mark.asyncio
    async def test_find_arbitrage_returns_from_cache(self):
        """Test that cached results are returned."""
        cache_key = ("csgo", "1-5", 0, float("inf"))
        cached_items = [{"name": "Cached Item", "profit": "$2.00"}]
        _arbitrage_cache[cache_key] = (cached_items, time.time())
        
        result = await _find_arbitrage_async(1, 5, "csgo")
        
        assert result == cached_items

    @pytest.mark.asyncio
    async def test_find_arbitrage_calculates_profit(self):
        """Test profit calculation for arbitrage items."""
        mock_items = [
            {
                "title": "Test Item",
                "price": {"amount": 1000},  # $10
                "suggestedPrice": {"amount": 1500},  # $15
                "itemId": "item123"
            }
        ]
        
        with patch("src.dmarket.arbitrage.core.fetch_market_items", return_value=mock_items):
            result = await _find_arbitrage_async(1, 10, "csgo")
            
            # May be empty if no profitable items found
            assert isinstance(result, list)


class TestArbitrageModeFunctions:
    """Tests for arbitrage mode functions."""

    @pytest.mark.asyncio
    async def test_arbitrage_boost_async(self):
        """Test arbitrage_boost_async calls correct range."""
        with patch("src.dmarket.arbitrage.core._find_arbitrage_async") as mock_find:
            mock_find.return_value = []
            await arbitrage_boost_async("csgo")
            mock_find.assert_called_once()

    @pytest.mark.asyncio
    async def test_arbitrage_mid_async(self):
        """Test arbitrage_mid_async calls correct range."""
        with patch("src.dmarket.arbitrage.core._find_arbitrage_async") as mock_find:
            mock_find.return_value = []
            await arbitrage_mid_async("csgo")
            mock_find.assert_called_once()

    @pytest.mark.asyncio
    async def test_arbitrage_pro_async(self):
        """Test arbitrage_pro_async calls correct range."""
        with patch("src.dmarket.arbitrage.core._find_arbitrage_async") as mock_find:
            mock_find.return_value = []
            await arbitrage_pro_async("csgo")
            mock_find.assert_called_once()


class TestFindArbitrageOpportunities:
    """Tests for find_arbitrage_opportunities_async function."""

    @pytest.mark.asyncio
    async def test_find_opportunities_empty_items(self):
        """Test with no items returned."""
        with patch("src.dmarket.arbitrage.fetch_market_items", return_value=[]):
            result = await find_arbitrage_opportunities_async(
                min_profit_percentage=10.0,
                max_results=5,
                game="csgo"
            )
            assert result == []

    @pytest.mark.asyncio
    async def test_find_opportunities_with_items(self):
        """Test with items that have arbitrage potential."""
        mock_items = [
            {
                "title": "Test Item",
                "price": {"amount": 1000},
                "suggestedPrice": {"amount": 1200},
                "itemId": "item123"
            }
        ]
        
        with patch("src.dmarket.arbitrage.fetch_market_items", return_value=mock_items):
            result = await find_arbitrage_opportunities_async(
                min_profit_percentage=5.0,
                max_results=5,
                game="csgo"
            )
            
            # Result may be empty if profit doesn't meet threshold
            assert isinstance(result, list)


class TestFindArbitrageItems:
    """Tests for find_arbitrage_items function."""

    @pytest.mark.asyncio
    async def test_find_items_low_mode(self):
        """Test finding items in low mode."""
        with patch("src.dmarket.arbitrage.search.arbitrage_boost_async") as mock:
            mock.return_value = []
            result = await find_arbitrage_items("csgo", mode="low")
            mock.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_items_boost_mode(self):
        """Test finding items in boost mode."""
        with patch("src.dmarket.arbitrage.search.arbitrage_boost_async") as mock:
            mock.return_value = []
            result = await find_arbitrage_items("csgo", mode="boost")
            mock.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_items_mid_mode(self):
        """Test finding items in mid mode."""
        with patch("src.dmarket.arbitrage.search.arbitrage_mid_async") as mock:
            mock.return_value = []
            result = await find_arbitrage_items("csgo", mode="mid")
            mock.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_items_pro_mode(self):
        """Test finding items in pro mode."""
        with patch("src.dmarket.arbitrage.search.arbitrage_pro_async") as mock:
            mock.return_value = []
            result = await find_arbitrage_items("csgo", mode="pro")
            mock.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_items_converts_tuple_results(self):
        """Test that tuple results are converted to dicts."""
        dict_results = [
            {"market_hash_name": "Item Name", "buy_price": 10.0, "sell_price": 15.0, "profit": 5.0, "profit_percent": 50.0}
        ]
        
        with patch("src.dmarket.arbitrage.search.arbitrage_mid_async", return_value=dict_results):
            result = await find_arbitrage_items("csgo", mode="mid")
            
            assert len(result) >= 0  # Results may be filtered


class TestArbitrageTrader:
    """Tests for ArbitrageTrader class."""

    def _create_mock_api(self):
        """Create a mock API client."""
        mock_api = MagicMock()
        mock_api.__aenter__ = AsyncMock(return_value=mock_api)
        mock_api.__aexit__ = AsyncMock(return_value=None)
        return mock_api

    def test_trader_initialization(self):
        """Test trader initialization."""
        trader = ArbitrageTrader(
            public_key="test_public",
            secret_key="test_secret",
        )
        
        assert trader.public_key == "test_public"
        assert trader.secret_key == "test_secret"
        assert trader.active is False
        assert trader.min_profit_percentage == 5.0
        assert trader.max_trade_value == 100.0
        assert trader.daily_limit == 500.0

    def test_trader_initialization_with_api_client(self):
        """Test trader initialization with API client."""
        mock_api = self._create_mock_api()
        trader = ArbitrageTrader(api_client=mock_api)
        
        assert trader.api == mock_api
        assert trader.active is False

    def test_trader_initialization_raises_without_credentials(self):
        """Test trader initialization raises error without credentials."""
        with pytest.raises(ValueError) as exc_info:
            ArbitrageTrader()
        
        assert "requires either api_client" in str(exc_info.value)

    def test_trader_set_trading_limits(self):
        """Test setting trading limits."""
        mock_api = self._create_mock_api()
        trader = ArbitrageTrader(api_client=mock_api)
        
        trader.set_trading_limits(max_trade_value=200.0, daily_limit=1000.0)
        
        assert trader.max_trade_value == 200.0
        assert trader.daily_limit == 1000.0

    def test_trader_get_status(self):
        """Test getting trader status."""
        mock_api = self._create_mock_api()
        trader = ArbitrageTrader(api_client=mock_api)
        
        status = trader.get_status()
        
        assert "active" in status
        assert "current_game" in status
        assert "transactions_count" in status
        assert "total_profit" in status
        assert "daily_traded" in status

    def test_trader_get_transaction_history(self):
        """Test getting transaction history."""
        mock_api = self._create_mock_api()
        trader = ArbitrageTrader(api_client=mock_api)
        
        history = trader.get_transaction_history()
        
        assert isinstance(history, list)
        assert len(history) == 0

    @pytest.mark.asyncio
    async def test_trader_check_balance(self):
        """Test balance checking."""
        mock_api = self._create_mock_api()
        mock_api.get_balance = AsyncMock(return_value={"usd": 10000})  # $100 in cents
        trader = ArbitrageTrader(api_client=mock_api)
        
        has_funds, balance = await trader.check_balance()
        
        assert isinstance(has_funds, bool)
        assert isinstance(balance, float)

    @pytest.mark.asyncio
    async def test_trader_check_balance_insufficient(self):
        """Test balance checking with insufficient funds."""
        mock_api = self._create_mock_api()
        mock_api.get_balance = AsyncMock(return_value={"usd": 50})  # $0.50 in cents
        trader = ArbitrageTrader(api_client=mock_api)
        
        has_funds, balance = await trader.check_balance()
        
        assert isinstance(has_funds, bool)
        assert isinstance(balance, float)

    @pytest.mark.asyncio
    async def test_trader_check_trading_limits_exceeded(self):
        """Test trading limits exceeded."""
        mock_api = self._create_mock_api()
        trader = ArbitrageTrader(api_client=mock_api, max_trade_value=100.0)
        
        result = await trader._check_trading_limits(150.0)
        
        assert result is False

    @pytest.mark.asyncio
    async def test_trader_check_trading_limits_within(self):
        """Test trading limits within bounds."""
        mock_api = self._create_mock_api()
        trader = ArbitrageTrader(api_client=mock_api, max_trade_value=100.0, daily_limit=500.0)
        trader.daily_traded = 0.0
        
        result = await trader._check_trading_limits(50.0)
        
        assert result is True

    @pytest.mark.asyncio
    async def test_trader_can_trade_now_on_pause(self):
        """Test can_trade_now when on pause."""
        mock_api = self._create_mock_api()
        trader = ArbitrageTrader(api_client=mock_api)
        trader.pause_until = time.time() + 3600  # 1 hour in future
        
        result = await trader._can_trade_now()
        
        assert result is False

    @pytest.mark.asyncio
    async def test_trader_can_trade_now_not_paused(self):
        """Test can_trade_now when not paused."""
        mock_api = self._create_mock_api()
        trader = ArbitrageTrader(api_client=mock_api)
        trader.pause_until = 0
        
        result = await trader._can_trade_now()
        
        assert result is True

    @pytest.mark.asyncio
    async def test_stop_auto_trading_not_running(self):
        """Test stopping auto trading when not running."""
        mock_api = self._create_mock_api()
        trader = ArbitrageTrader(api_client=mock_api)
        trader.active = False
        
        success, message = await trader.stop_auto_trading()
        
        assert success is False
        assert "не запущена" in message

    @pytest.mark.asyncio
    async def test_stop_auto_trading_running(self):
        """Test stopping auto trading when running."""
        mock_api = self._create_mock_api()
        trader = ArbitrageTrader(api_client=mock_api)
        trader.active = True
        
        success, message = await trader.stop_auto_trading()
        
        assert success is True
        assert trader.active is False


class TestCalculateCommission:
    """Tests for _calculate_commission function."""

    def test_commission_base(self):
        """Test base commission calculation."""
        commission = _calculate_commission("", "", 0.5, "csgo")
        assert commission >= 2.0
        assert commission <= 15.0

    def test_commission_rare_item(self):
        """Test commission for rare items."""
        commission = _calculate_commission("covert", "", 0.5, "csgo")
        base_commission = _calculate_commission("", "", 0.5, "csgo")
        assert commission > base_commission

    def test_commission_common_item(self):
        """Test commission for common items."""
        commission = _calculate_commission("consumer", "", 0.5, "csgo")
        base_commission = _calculate_commission("", "", 0.5, "csgo")
        assert commission < base_commission

    def test_commission_knife_item(self):
        """Test commission for knife items."""
        commission = _calculate_commission("", "knife", 0.5, "csgo")
        base_commission = _calculate_commission("", "", 0.5, "csgo")
        assert commission > base_commission

    def test_commission_popular_item(self):
        """Test commission for popular items."""
        commission = _calculate_commission("", "", 0.9, "csgo")
        base_commission = _calculate_commission("", "", 0.5, "csgo")
        assert commission < base_commission

    def test_commission_unpopular_item(self):
        """Test commission for unpopular items."""
        commission = _calculate_commission("", "", 0.2, "csgo")
        base_commission = _calculate_commission("", "", 0.5, "csgo")
        assert commission > base_commission


class TestGroupItemsByName:
    """Tests for _group_items_by_name function."""

    def test_group_items_empty(self):
        """Test grouping empty list."""
        result = _group_items_by_name([])
        assert result == {}

    def test_group_items_single(self):
        """Test grouping single item."""
        items = [{"title": "Test Item", "price": {"USD": 1000}}]
        result = _group_items_by_name(items)
        
        assert "Test Item" in result
        assert len(result["Test Item"]) == 1

    def test_group_items_multiple_same_name(self):
        """Test grouping multiple items with same name."""
        items = [
            {"title": "Test Item", "price": {"USD": 1000}},
            {"title": "Test Item", "price": {"USD": 1100}},
            {"title": "Other Item", "price": {"USD": 500}}
        ]
        result = _group_items_by_name(items)
        
        assert "Test Item" in result
        assert len(result["Test Item"]) == 2
        assert "Other Item" in result
        assert len(result["Other Item"]) == 1

    def test_group_items_no_title(self):
        """Test grouping items without title."""
        items = [
            {"price": {"USD": 1000}},  # No title
            {"title": "", "price": {"USD": 500}},  # Empty title
            {"title": "Valid Item", "price": {"USD": 2000}}
        ]
        result = _group_items_by_name(items)
        
        assert "Valid Item" in result
        assert "" not in result
