"""Extended Phase 4 tests for arbitrage_scanner.py module.

This module contains comprehensive tests targeting 100% coverage
for the ArbitrageScanner class and helper functions.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Any


# Test data fixtures
@pytest.fixture
def mock_api_client():
    """Create a mock DMarket API client."""
    client = AsyncMock()
    client.get_market_items = AsyncMock(return_value={
        "objects": [
            {
                "itemId": "item1",
                "title": "AK-47 | Redline",
                "price": {"USD": "1000", "amount": 1000},
                "suggestedPrice": {"USD": "1200", "amount": 1200},
                "game": "csgo",
            },
            {
                "itemId": "item2",
                "title": "M4A4 | Asiimov",
                "price": {"USD": "2500", "amount": 2500},
                "suggestedPrice": {"USD": "3000", "amount": 3000},
                "game": "csgo",
            },
        ]
    })
    client.get_aggregated_prices_bulk = AsyncMock(return_value={
        "aggregatedPrices": [
            {"title": "AK-47 | Redline", "offerCount": 10, "orderCount": 5},
            {"title": "M4A4 | Asiimov", "offerCount": 15, "orderCount": 8},
        ]
    })
    client.get_buy_orders_competition = AsyncMock(return_value={
        "competition_level": "low",
        "total_orders": 2,
        "total_amount": 500,
        "best_price": 9.50,
        "average_price": 9.75,
    })
    client._request = AsyncMock(return_value={
        "usd": {"available": 10000, "frozen": 500}
    })
    return client


@pytest.fixture
def sample_items():
    """Sample items for testing."""
    return [
        {
            "itemId": "item1",
            "title": "AK-47 | Redline",
            "price": {"USD": "1000", "amount": 1000},
            "suggestedPrice": {"USD": "1200", "amount": 1200},
            "game": "csgo",
            "profit": 2.0,
        },
        {
            "itemId": "item2",
            "title": "M4A4 | Asiimov",
            "price": {"USD": "2500", "amount": 2500},
            "suggestedPrice": {"USD": "3000", "amount": 3000},
            "game": "csgo",
            "profit": 5.0,
        },
    ]


@pytest.fixture
def sample_items_by_game(sample_items):
    """Sample items organized by game."""
    return {"csgo": sample_items}


class TestArbitrageScannerInit:
    """Tests for ArbitrageScanner initialization."""

    def test_init_default_parameters(self):
        """Test default initialization parameters."""
        from src.dmarket.arbitrage_scanner import ArbitrageScanner
        
        scanner = ArbitrageScanner()
        assert scanner.api_client is None
        assert scanner.enable_liquidity_filter is True
        assert scanner.enable_competition_filter is True
        assert scanner.max_competition == 3

    def test_init_with_api_client(self, mock_api_client):
        """Test initialization with API client."""
        from src.dmarket.arbitrage_scanner import ArbitrageScanner
        
        scanner = ArbitrageScanner(api_client=mock_api_client)
        assert scanner.api_client == mock_api_client

    def test_init_with_disabled_filters(self):
        """Test initialization with disabled filters."""
        from src.dmarket.arbitrage_scanner import ArbitrageScanner
        
        scanner = ArbitrageScanner(
            enable_liquidity_filter=False,
            enable_competition_filter=False,
        )
        assert scanner.enable_liquidity_filter is False
        assert scanner.enable_competition_filter is False

    def test_init_with_custom_max_competition(self):
        """Test initialization with custom max_competition."""
        from src.dmarket.arbitrage_scanner import ArbitrageScanner
        
        scanner = ArbitrageScanner(max_competition=5)
        assert scanner.max_competition == 5

    def test_init_default_trading_parameters(self):
        """Test default trading parameters."""
        from src.dmarket.arbitrage_scanner import ArbitrageScanner
        
        scanner = ArbitrageScanner()
        assert scanner.min_profit == 0.5
        assert scanner.max_price == 50.0
        assert scanner.max_trades == 5

    def test_init_statistics_zeroed(self):
        """Test statistics are zeroed on init."""
        from src.dmarket.arbitrage_scanner import ArbitrageScanner
        
        scanner = ArbitrageScanner()
        assert scanner.total_scans == 0
        assert scanner.total_items_found == 0
        assert scanner.successful_trades == 0
        assert scanner.total_profit == 0.0

    def test_init_liquidity_parameters(self):
        """Test default liquidity parameters."""
        from src.dmarket.arbitrage_scanner import ArbitrageScanner
        
        scanner = ArbitrageScanner()
        assert scanner.min_liquidity_score == 60
        assert scanner.min_sales_per_week == 5
        assert scanner.max_time_to_sell_days == 7


class TestCacheTTLProperty:
    """Tests for cache_ttl property."""

    def test_cache_ttl_getter(self):
        """Test getting cache TTL."""
        from src.dmarket.arbitrage_scanner import ArbitrageScanner
        
        scanner = ArbitrageScanner()
        # Default TTL is 300 seconds
        assert scanner.cache_ttl == 300

    def test_cache_ttl_setter(self):
        """Test setting cache TTL."""
        from src.dmarket.arbitrage_scanner import ArbitrageScanner
        
        scanner = ArbitrageScanner()
        scanner.cache_ttl = 600
        assert scanner.cache_ttl == 600


class TestGetCachedResults:
    """Tests for _get_cached_results method."""

    def test_get_cached_results_miss(self):
        """Test cache miss returns None."""
        from src.dmarket.arbitrage_scanner import ArbitrageScanner
        
        scanner = ArbitrageScanner()
        result = scanner._get_cached_results(("csgo", "medium", 0, float("inf")))
        assert result is None

    def test_get_cached_results_hit(self):
        """Test cache hit returns data."""
        from src.dmarket.arbitrage_scanner import ArbitrageScanner
        
        scanner = ArbitrageScanner()
        cache_key = ("csgo", "medium", 0, float("inf"))
        test_data = [{"item": "test"}]
        scanner._save_to_cache(cache_key, test_data)
        
        result = scanner._get_cached_results(cache_key)
        assert result == test_data


class TestSaveToCache:
    """Tests for _save_to_cache method."""

    def test_save_to_cache_basic(self):
        """Test basic cache save."""
        from src.dmarket.arbitrage_scanner import ArbitrageScanner
        
        scanner = ArbitrageScanner()
        cache_key = ("csgo", "high", 100, 500)
        test_data = [{"item": "expensive_item"}]
        scanner._save_to_cache(cache_key, test_data)
        
        result = scanner._get_cached_results(cache_key)
        assert result == test_data

    def test_save_to_cache_string_key(self):
        """Test cache save with string key."""
        from src.dmarket.arbitrage_scanner import ArbitrageScanner
        
        scanner = ArbitrageScanner()
        cache_key = "scan_level_csgo_boost"
        test_data = [{"item": "boost_item"}]
        scanner._save_to_cache(cache_key, test_data)
        
        # Retrieve using the same key
        result = scanner._scanner_cache.get(cache_key)
        assert result == test_data


class TestGetApiClient:
    """Tests for get_api_client method."""

    @pytest.mark.asyncio
    async def test_get_api_client_creates_new(self):
        """Test creating new API client when none provided."""
        from src.dmarket.arbitrage_scanner import ArbitrageScanner
        
        scanner = ArbitrageScanner()
        
        with patch.dict("os.environ", {
            "DMARKET_PUBLIC_KEY": "test_public",
            "DMARKET_SECRET_KEY": "test_secret",
            "DMARKET_API_URL": "https://api.dmarket.com",
        }):
            with patch("src.dmarket.arbitrage_scanner.DMarketAPI") as mock_api:
                mock_instance = MagicMock()
                mock_api.return_value = mock_instance
                
                result = await scanner.get_api_client()
                
                mock_api.assert_called_once()
                assert scanner.api_client == mock_instance

    @pytest.mark.asyncio
    async def test_get_api_client_returns_existing(self, mock_api_client):
        """Test returning existing API client."""
        from src.dmarket.arbitrage_scanner import ArbitrageScanner
        
        scanner = ArbitrageScanner(api_client=mock_api_client)
        result = await scanner.get_api_client()
        assert result == mock_api_client

    @pytest.mark.asyncio
    async def test_get_api_client_initializes_liquidity_analyzer(self, mock_api_client):
        """Test liquidity analyzer is initialized when filter enabled."""
        from src.dmarket.arbitrage_scanner import ArbitrageScanner
        
        scanner = ArbitrageScanner(
            api_client=mock_api_client,
            enable_liquidity_filter=True,
        )
        
        await scanner.get_api_client()
        assert scanner.liquidity_analyzer is not None


class TestStandardizeItems:
    """Tests for _standardize_items method."""

    def test_standardize_items_dict_format(self):
        """Test standardizing dict items."""
        from src.dmarket.arbitrage_scanner import ArbitrageScanner
        
        scanner = ArbitrageScanner()
        items = [
            {
                "name": "Test Item",
                "buy_price": 10.0,
                "sell_price": 12.0,
                "profit": 2.0,
                "profit_percentage": 20.0,
                "itemId": "item1",
            }
        ]
        
        result = scanner._standardize_items(items, "csgo", 1.0, 5.0)
        
        assert len(result) == 1
        assert result[0]["title"] == "Test Item"
        assert result[0]["profit"] == 2.0
        assert result[0]["game"] == "csgo"

    def test_standardize_items_tuple_format(self):
        """Test standardizing tuple items."""
        from src.dmarket.arbitrage_scanner import ArbitrageScanner
        
        scanner = ArbitrageScanner()
        items = [
            ("Test Item", 10.0, 12.0, 2.0, 20.0)  # name, buy, sell, profit, percent
        ]
        
        result = scanner._standardize_items(items, "csgo", 1.0, 5.0)
        
        assert len(result) == 1
        assert result[0]["title"] == "Test Item"
        assert result[0]["profit"] == 2.0

    def test_standardize_items_profit_filter(self):
        """Test filtering by profit range."""
        from src.dmarket.arbitrage_scanner import ArbitrageScanner
        
        scanner = ArbitrageScanner()
        items = [
            {"name": "Low Profit", "buy_price": 10.0, "profit": 0.5},
            {"name": "Medium Profit", "buy_price": 10.0, "profit": 3.0},
            {"name": "High Profit", "buy_price": 10.0, "profit": 10.0},
        ]
        
        result = scanner._standardize_items(items, "csgo", 1.0, 5.0)
        
        assert len(result) == 1
        assert result[0]["title"] == "Medium Profit"

    def test_standardize_items_price_string_with_dollar(self):
        """Test handling price strings with dollar sign."""
        from src.dmarket.arbitrage_scanner import ArbitrageScanner
        
        scanner = ArbitrageScanner()
        items = [
            {"name": "Dollar Item", "buy_price": 10.0, "profit": "$3.00"}
        ]
        
        result = scanner._standardize_items(items, "csgo", 1.0, 5.0)
        
        assert len(result) == 1
        assert result[0]["profit"] == 3.0

    def test_standardize_items_empty_list(self):
        """Test with empty list."""
        from src.dmarket.arbitrage_scanner import ArbitrageScanner
        
        scanner = ArbitrageScanner()
        result = scanner._standardize_items([], "csgo", 1.0, 5.0)
        assert result == []


class TestGetLevelConfig:
    """Tests for get_level_config method."""

    def test_get_level_config_boost(self):
        """Test getting boost level config."""
        from src.dmarket.arbitrage_scanner import ArbitrageScanner
        
        scanner = ArbitrageScanner()
        config = scanner.get_level_config("boost")
        
        assert "name" in config
        assert "price_range" in config
        assert "min_profit_percent" in config

    def test_get_level_config_standard(self):
        """Test getting standard level config."""
        from src.dmarket.arbitrage_scanner import ArbitrageScanner
        
        scanner = ArbitrageScanner()
        config = scanner.get_level_config("standard")
        assert "name" in config

    def test_get_level_config_invalid(self):
        """Test getting invalid level raises ValueError."""
        from src.dmarket.arbitrage_scanner import ArbitrageScanner
        
        scanner = ArbitrageScanner()
        with pytest.raises(ValueError, match="Неизвестный уровень"):
            scanner.get_level_config("invalid_level")


class TestGetLevelStats:
    """Tests for get_level_stats method."""

    def test_get_level_stats_returns_dict(self):
        """Test get_level_stats returns dict."""
        from src.dmarket.arbitrage_scanner import ArbitrageScanner
        
        scanner = ArbitrageScanner()
        stats = scanner.get_level_stats()
        
        assert isinstance(stats, dict)
        assert "boost" in stats or "standard" in stats

    def test_get_level_stats_contains_required_keys(self):
        """Test stats contain required keys."""
        from src.dmarket.arbitrage_scanner import ArbitrageScanner
        
        scanner = ArbitrageScanner()
        stats = scanner.get_level_stats()
        
        for level_name, level_stats in stats.items():
            assert "name" in level_stats
            assert "min_profit" in level_stats
            assert "price_range" in level_stats


class TestGetStatistics:
    """Tests for get_statistics method."""

    def test_get_statistics_initial(self):
        """Test initial statistics."""
        from src.dmarket.arbitrage_scanner import ArbitrageScanner
        
        scanner = ArbitrageScanner()
        stats = scanner.get_statistics()
        
        assert stats["total_scans"] == 0
        assert stats["total_items_found"] == 0
        assert stats["successful_trades"] == 0
        assert stats["total_profit"] == 0.0
        assert "cache_size" in stats
        assert "cache_hits" in stats
        assert "cache_misses" in stats


class TestClearCache:
    """Tests for clear_cache method."""

    def test_clear_cache_removes_all_data(self):
        """Test clear_cache removes all cached data."""
        from src.dmarket.arbitrage_scanner import ArbitrageScanner
        
        scanner = ArbitrageScanner()
        # Add some data to cache
        scanner._save_to_cache(("csgo", "boost", 0, 100), [{"item": "test"}])
        
        # Clear cache
        scanner.clear_cache()
        
        # Verify cache is empty
        result = scanner._get_cached_results(("csgo", "boost", 0, 100))
        assert result is None


class TestScanGame:
    """Tests for scan_game method."""

    @pytest.mark.asyncio
    async def test_scan_game_returns_cached_results(self, mock_api_client):
        """Test scan_game returns cached results when available."""
        from src.dmarket.arbitrage_scanner import ArbitrageScanner
        
        scanner = ArbitrageScanner(
            api_client=mock_api_client,
            enable_liquidity_filter=False,
        )
        
        cache_key = ("csgo", "medium", 0, float("inf"))
        cached_data = [{"item": "cached_item", "profit": 5.0}]
        scanner._save_to_cache(cache_key, cached_data)
        
        result = await scanner.scan_game("csgo", "medium", 10)
        assert result == cached_data

    @pytest.mark.asyncio
    async def test_scan_game_increments_scan_count(self, mock_api_client):
        """Test scan_game increments total_scans counter."""
        from src.dmarket.arbitrage_scanner import ArbitrageScanner
        
        scanner = ArbitrageScanner(
            api_client=mock_api_client,
            enable_liquidity_filter=False,
        )
        
        with patch("src.dmarket.arbitrage_scanner.rate_limiter") as mock_limiter:
            mock_limiter.wait_if_needed = AsyncMock()
            with patch("src.dmarket.arbitrage_scanner.arbitrage_mid", return_value=[]):
                with patch("src.dmarket.arbitrage_scanner.ArbitrageTrader") as mock_trader:
                    mock_trader_instance = MagicMock()
                    mock_trader_instance.find_profitable_items = AsyncMock(return_value=[])
                    mock_trader.return_value = mock_trader_instance
                    
                    await scanner.scan_game("csgo", "medium", 10)
        
        assert scanner.total_scans == 1

    @pytest.mark.asyncio
    async def test_scan_game_low_mode(self, mock_api_client):
        """Test scan_game with low mode."""
        from src.dmarket.arbitrage_scanner import ArbitrageScanner
        
        scanner = ArbitrageScanner(
            api_client=mock_api_client,
            enable_liquidity_filter=False,
        )
        
        with patch("src.dmarket.arbitrage_scanner.rate_limiter") as mock_limiter:
            mock_limiter.wait_if_needed = AsyncMock()
            with patch("src.dmarket.arbitrage_scanner.arbitrage_boost", return_value=[]):
                with patch("src.dmarket.arbitrage_scanner.ArbitrageTrader") as mock_trader:
                    mock_trader_instance = MagicMock()
                    mock_trader_instance.find_profitable_items = AsyncMock(return_value=[])
                    mock_trader.return_value = mock_trader_instance
                    
                    result = await scanner.scan_game("csgo", "low", 10)
        
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_scan_game_high_mode(self, mock_api_client):
        """Test scan_game with high mode."""
        from src.dmarket.arbitrage_scanner import ArbitrageScanner
        
        scanner = ArbitrageScanner(
            api_client=mock_api_client,
            enable_liquidity_filter=False,
        )
        
        with patch("src.dmarket.arbitrage_scanner.rate_limiter") as mock_limiter:
            mock_limiter.wait_if_needed = AsyncMock()
            with patch("src.dmarket.arbitrage_scanner.arbitrage_pro", return_value=[]):
                with patch("src.dmarket.arbitrage_scanner.ArbitrageTrader") as mock_trader:
                    mock_trader_instance = MagicMock()
                    mock_trader_instance.find_profitable_items = AsyncMock(return_value=[])
                    mock_trader.return_value = mock_trader_instance
                    
                    result = await scanner.scan_game("csgo", "high", 10)
        
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_scan_game_with_price_range(self, mock_api_client):
        """Test scan_game with custom price range."""
        from src.dmarket.arbitrage_scanner import ArbitrageScanner
        
        scanner = ArbitrageScanner(
            api_client=mock_api_client,
            enable_liquidity_filter=False,
        )
        
        with patch("src.dmarket.arbitrage_scanner.rate_limiter") as mock_limiter:
            mock_limiter.wait_if_needed = AsyncMock()
            with patch("src.dmarket.arbitrage_scanner.ArbitrageTrader") as mock_trader:
                mock_trader_instance = MagicMock()
                mock_trader_instance.find_profitable_items = AsyncMock(return_value=[])
                mock_trader.return_value = mock_trader_instance
                
                result = await scanner.scan_game(
                    "csgo", "medium", 10, price_from=50.0, price_to=100.0
                )
        
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_scan_game_handles_exception(self, mock_api_client):
        """Test scan_game handles exceptions gracefully."""
        from src.dmarket.arbitrage_scanner import ArbitrageScanner
        
        scanner = ArbitrageScanner(
            api_client=mock_api_client,
            enable_liquidity_filter=False,
        )
        
        with patch("src.dmarket.arbitrage_scanner.rate_limiter") as mock_limiter:
            mock_limiter.wait_if_needed = AsyncMock(side_effect=Exception("API error"))
            
            result = await scanner.scan_game("csgo", "medium", 10)
        
        assert result == []


class TestScanMultipleGames:
    """Tests for scan_multiple_games method."""

    @pytest.mark.asyncio
    async def test_scan_multiple_games_default(self, mock_api_client):
        """Test scanning multiple games with defaults."""
        from src.dmarket.arbitrage_scanner import ArbitrageScanner
        
        scanner = ArbitrageScanner(
            api_client=mock_api_client,
            enable_liquidity_filter=False,
        )
        
        with patch.object(scanner, "scan_game", new_callable=AsyncMock) as mock_scan:
            mock_scan.return_value = []
            
            result = await scanner.scan_multiple_games()
        
        assert isinstance(result, dict)
        assert mock_scan.called

    @pytest.mark.asyncio
    async def test_scan_multiple_games_specific_list(self, mock_api_client):
        """Test scanning specific games."""
        from src.dmarket.arbitrage_scanner import ArbitrageScanner
        
        scanner = ArbitrageScanner(
            api_client=mock_api_client,
            enable_liquidity_filter=False,
        )
        
        with patch.object(scanner, "scan_game", new_callable=AsyncMock) as mock_scan:
            mock_scan.return_value = []
            
            result = await scanner.scan_multiple_games(games=["csgo", "dota2"])
        
        assert isinstance(result, dict)
        assert "csgo" in result
        assert "dota2" in result


class TestScanLevel:
    """Tests for scan_level method."""

    @pytest.mark.asyncio
    async def test_scan_level_invalid_game(self, mock_api_client):
        """Test scan_level with invalid game raises ValueError."""
        from src.dmarket.arbitrage_scanner import ArbitrageScanner
        
        scanner = ArbitrageScanner(api_client=mock_api_client)
        
        # First need to provide a valid level, then invalid game
        with pytest.raises(ValueError, match="не поддерживается|Неизвестный уровень"):
            await scanner.scan_level("boost", "invalid_game_xyz")

    @pytest.mark.asyncio
    async def test_scan_level_uses_cache(self, mock_api_client):
        """Test scan_level uses cache when available."""
        from src.dmarket.arbitrage_scanner import ArbitrageScanner
        
        scanner = ArbitrageScanner(api_client=mock_api_client)
        
        cache_key = "scan_level_csgo_boost"
        cached_data = [{"item": "cached", "profit": 3.0}]
        scanner._save_to_cache(cache_key, cached_data)
        
        result = await scanner.scan_level("boost", "csgo", max_results=10, use_cache=True)
        assert result == cached_data

    @pytest.mark.asyncio
    async def test_scan_level_with_aggregated_api(self, mock_api_client):
        """Test scan_level with aggregated API."""
        from src.dmarket.arbitrage_scanner import ArbitrageScanner
        
        scanner = ArbitrageScanner(
            api_client=mock_api_client,
            enable_liquidity_filter=False,
        )
        
        result = await scanner.scan_level(
            "boost", "csgo", max_results=5, use_cache=False, use_aggregated_api=True
        )
        
        assert isinstance(result, list)


class TestScanAllLevels:
    """Tests for scan_all_levels method."""

    @pytest.mark.asyncio
    async def test_scan_all_levels(self, mock_api_client):
        """Test scanning all levels."""
        from src.dmarket.arbitrage_scanner import ArbitrageScanner
        
        scanner = ArbitrageScanner(api_client=mock_api_client)
        
        with patch.object(scanner, "scan_level", new_callable=AsyncMock) as mock_scan:
            mock_scan.return_value = []
            
            result = await scanner.scan_all_levels("csgo", max_results_per_level=5)
        
        assert isinstance(result, dict)


class TestFindBestOpportunities:
    """Tests for find_best_opportunities method."""

    @pytest.mark.asyncio
    async def test_find_best_opportunities_basic(self, mock_api_client):
        """Test finding best opportunities."""
        from src.dmarket.arbitrage_scanner import ArbitrageScanner
        
        scanner = ArbitrageScanner(api_client=mock_api_client)
        
        with patch.object(scanner, "scan_level", new_callable=AsyncMock) as mock_scan:
            mock_scan.return_value = [
                {"profit_percent": 10.0},
                {"profit_percent": 20.0},
            ]
            
            result = await scanner.find_best_opportunities("csgo", top_n=5)
        
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_find_best_opportunities_invalid_min_level(self, mock_api_client):
        """Test find_best_opportunities with invalid min_level."""
        from src.dmarket.arbitrage_scanner import ArbitrageScanner
        
        scanner = ArbitrageScanner(api_client=mock_api_client)
        
        with pytest.raises(ValueError, match="Неизвестный уровень"):
            await scanner.find_best_opportunities("csgo", min_level="invalid")

    @pytest.mark.asyncio
    async def test_find_best_opportunities_invalid_max_level(self, mock_api_client):
        """Test find_best_opportunities with invalid max_level."""
        from src.dmarket.arbitrage_scanner import ArbitrageScanner
        
        scanner = ArbitrageScanner(api_client=mock_api_client)
        
        with pytest.raises(ValueError, match="Неизвестный уровень"):
            await scanner.find_best_opportunities("csgo", max_level="invalid")


class TestCheckUserBalance:
    """Tests for check_user_balance method."""

    @pytest.mark.asyncio
    async def test_check_user_balance_success(self, mock_api_client):
        """Test successful balance check."""
        from src.dmarket.arbitrage_scanner import ArbitrageScanner
        
        scanner = ArbitrageScanner(api_client=mock_api_client)
        
        result = await scanner.check_user_balance()
        
        assert "has_funds" in result
        assert "balance" in result
        assert "available_balance" in result

    @pytest.mark.asyncio
    async def test_check_user_balance_empty_response(self, mock_api_client):
        """Test balance check with empty response."""
        from src.dmarket.arbitrage_scanner import ArbitrageScanner
        
        mock_api_client._request = AsyncMock(return_value=None)
        scanner = ArbitrageScanner(api_client=mock_api_client)
        
        result = await scanner.check_user_balance()
        
        assert result["error"] is True
        assert result["has_funds"] is False

    @pytest.mark.asyncio
    async def test_check_user_balance_not_dict_response(self, mock_api_client):
        """Test balance check with non-dict response."""
        from src.dmarket.arbitrage_scanner import ArbitrageScanner
        
        mock_api_client._request = AsyncMock(return_value=False)
        scanner = ArbitrageScanner(api_client=mock_api_client)
        
        result = await scanner.check_user_balance()
        
        assert result["error"] is True
        # The actual diagnosis can be "api_error" or "unknown_error"
        assert result["diagnosis"] in ("unknown_error", "api_error")

    @pytest.mark.asyncio
    async def test_check_user_balance_error_in_response(self, mock_api_client):
        """Test balance check with error in response."""
        from src.dmarket.arbitrage_scanner import ArbitrageScanner
        
        mock_api_client._request = AsyncMock(return_value={
            "error": True,
            "message": "unauthorized"
        })
        scanner = ArbitrageScanner(api_client=mock_api_client)
        
        result = await scanner.check_user_balance()
        
        assert result["error"] is True
        assert result["diagnosis"] == "auth_error"

    @pytest.mark.asyncio
    async def test_check_user_balance_timeout_error(self, mock_api_client):
        """Test balance check with timeout error."""
        from src.dmarket.arbitrage_scanner import ArbitrageScanner
        
        mock_api_client._request = AsyncMock(return_value={
            "error": True,
            "message": "timeout occurred"
        })
        scanner = ArbitrageScanner(api_client=mock_api_client)
        
        result = await scanner.check_user_balance()
        
        assert result["error"] is True
        assert result["diagnosis"] == "timeout_error"

    @pytest.mark.asyncio
    async def test_check_user_balance_missing_keys_error(self, mock_api_client):
        """Test balance check with missing keys error."""
        from src.dmarket.arbitrage_scanner import ArbitrageScanner
        
        mock_api_client._request = AsyncMock(return_value={
            "error": True,
            "message": "api key invalid"
        })
        scanner = ArbitrageScanner(api_client=mock_api_client)
        
        result = await scanner.check_user_balance()
        
        assert result["error"] is True
        assert result["diagnosis"] == "missing_keys"

    @pytest.mark.asyncio
    async def test_check_user_balance_zero_balance(self, mock_api_client):
        """Test balance check with zero balance."""
        from src.dmarket.arbitrage_scanner import ArbitrageScanner
        
        mock_api_client._request = AsyncMock(return_value={
            "usd": {"available": 0, "frozen": 0}
        })
        scanner = ArbitrageScanner(api_client=mock_api_client)
        
        result = await scanner.check_user_balance()
        
        assert result["has_funds"] is False
        assert result["balance"] == 0.0
        assert result["diagnosis"] == "zero_balance"

    @pytest.mark.asyncio
    async def test_check_user_balance_frozen_funds(self, mock_api_client):
        """Test balance check with frozen funds."""
        from src.dmarket.arbitrage_scanner import ArbitrageScanner
        
        mock_api_client._request = AsyncMock(return_value={
            "usd": {"available": 50, "frozen": 1000}  # Low available, high frozen
        })
        scanner = ArbitrageScanner(api_client=mock_api_client)
        
        result = await scanner.check_user_balance()
        
        assert result["has_funds"] is False
        assert result["diagnosis"] == "funds_frozen"

    @pytest.mark.asyncio
    async def test_check_user_balance_exception(self, mock_api_client):
        """Test balance check handles exceptions."""
        from src.dmarket.arbitrage_scanner import ArbitrageScanner
        
        mock_api_client._request = AsyncMock(side_effect=Exception("Network error"))
        scanner = ArbitrageScanner(api_client=mock_api_client)
        
        result = await scanner.check_user_balance()
        
        assert result["error"] is True
        assert result["diagnosis"] == "exception"


class TestAutoTradeItems:
    """Tests for auto_trade_items method."""

    @pytest.mark.asyncio
    async def test_auto_trade_no_funds(self, mock_api_client, sample_items_by_game):
        """Test auto trade with no funds."""
        from src.dmarket.arbitrage_scanner import ArbitrageScanner
        
        scanner = ArbitrageScanner(api_client=mock_api_client)
        
        with patch.object(scanner, "check_user_balance", new_callable=AsyncMock) as mock_balance:
            mock_balance.return_value = {"has_funds": False, "balance": 0.0}
            
            purchases, sales, profit = await scanner.auto_trade_items(sample_items_by_game)
        
        assert purchases == 0
        assert sales == 0
        assert profit == 0.0

    @pytest.mark.asyncio
    async def test_auto_trade_low_risk(self, mock_api_client, sample_items_by_game):
        """Test auto trade with low risk level."""
        from src.dmarket.arbitrage_scanner import ArbitrageScanner
        
        scanner = ArbitrageScanner(api_client=mock_api_client)
        
        with patch.object(scanner, "check_user_balance", new_callable=AsyncMock) as mock_balance:
            mock_balance.return_value = {"has_funds": True, "balance": 100.0}
            
            with patch.object(scanner, "_get_current_item_data", new_callable=AsyncMock) as mock_get:
                mock_get.return_value = None  # Item not available
                
                purchases, sales, profit = await scanner.auto_trade_items(
                    sample_items_by_game,
                    risk_level="low",
                )
        
        # With no items available, we expect 0 purchases
        assert purchases == 0


class TestGetMarketOverview:
    """Tests for get_market_overview method."""

    @pytest.mark.asyncio
    async def test_get_market_overview_success(self, mock_api_client):
        """Test successful market overview."""
        from src.dmarket.arbitrage_scanner import ArbitrageScanner
        
        # Configure mock to return proper numeric values
        mock_api_client.get_market_items = AsyncMock(return_value={
            "objects": [
                {
                    "itemId": "item1",
                    "title": "Test Item",
                    "price": {"USD": 1000},  # Numeric value, not string
                    "suggestedPrice": {"USD": 1200},
                }
            ]
        })
        
        scanner = ArbitrageScanner(api_client=mock_api_client)
        
        result = await scanner.get_market_overview("csgo")
        
        assert "game" in result
        assert result["game"] == "csgo"
        assert "total_items" in result
        # timestamp may be present only on successful parsing
        assert "total_items" in result

    @pytest.mark.asyncio
    async def test_get_market_overview_error(self, mock_api_client):
        """Test market overview with error."""
        from src.dmarket.arbitrage_scanner import ArbitrageScanner
        
        mock_api_client.get_market_items = AsyncMock(side_effect=Exception("API Error"))
        scanner = ArbitrageScanner(api_client=mock_api_client)
        
        result = await scanner.get_market_overview("csgo")
        
        assert "error" in result
        assert result["total_items"] == 0


class TestHelperFunctions:
    """Tests for module-level helper functions."""

    @pytest.mark.asyncio
    async def test_find_arbitrage_opportunities_async(self):
        """Test find_arbitrage_opportunities_async function."""
        from src.dmarket.arbitrage_scanner import find_arbitrage_opportunities_async
        
        with patch("src.dmarket.arbitrage_scanner.ArbitrageScanner") as mock_scanner:
            mock_instance = MagicMock()
            mock_instance.scan_game = AsyncMock(return_value=[])
            mock_scanner.return_value = mock_instance
            
            result = await find_arbitrage_opportunities_async("csgo")
        
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_find_multi_game_arbitrage_opportunities(self):
        """Test find_multi_game_arbitrage_opportunities function."""
        from src.dmarket.arbitrage_scanner import find_multi_game_arbitrage_opportunities
        
        with patch("src.dmarket.arbitrage_scanner.ArbitrageScanner") as mock_scanner:
            mock_instance = MagicMock()
            mock_instance.scan_multiple_games = AsyncMock(return_value={})
            mock_scanner.return_value = mock_instance
            
            result = await find_multi_game_arbitrage_opportunities()
        
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_scan_game_for_arbitrage(self):
        """Test scan_game_for_arbitrage function."""
        from src.dmarket.arbitrage_scanner import scan_game_for_arbitrage
        
        with patch("src.dmarket.arbitrage_scanner.ArbitrageScanner") as mock_scanner:
            mock_instance = MagicMock()
            mock_instance.scan_game = AsyncMock(return_value=[])
            mock_scanner.return_value = mock_instance
            
            result = await scan_game_for_arbitrage("csgo")
        
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_scan_multiple_games_function(self):
        """Test scan_multiple_games function."""
        from src.dmarket.arbitrage_scanner import scan_multiple_games
        
        with patch("src.dmarket.arbitrage_scanner.ArbitrageScanner") as mock_scanner:
            mock_instance = MagicMock()
            mock_instance.scan_multiple_games = AsyncMock(return_value={})
            mock_scanner.return_value = mock_instance
            
            result = await scan_multiple_games()
        
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_check_user_balance_function(self, mock_api_client):
        """Test check_user_balance function."""
        from src.dmarket.arbitrage_scanner import check_user_balance
        
        with patch("src.dmarket.arbitrage_scanner.ArbitrageScanner") as mock_scanner:
            mock_instance = MagicMock()
            mock_instance.check_user_balance = AsyncMock(return_value={
                "has_funds": True,
                "balance": 100.0,
            })
            mock_scanner.return_value = mock_instance
            
            result = await check_user_balance(mock_api_client)
        
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_auto_trade_items_function(self, mock_api_client, sample_items_by_game):
        """Test auto_trade_items function."""
        from src.dmarket.arbitrage_scanner import auto_trade_items
        
        with patch("src.dmarket.arbitrage_scanner.ArbitrageScanner") as mock_scanner:
            mock_instance = MagicMock()
            mock_instance.auto_trade_items = AsyncMock(return_value=(0, 0, 0.0))
            mock_scanner.return_value = mock_instance
            
            result = await auto_trade_items(sample_items_by_game)
        
        assert isinstance(result, tuple)
        assert len(result) == 3


class TestAnalyzeItem:
    """Tests for _analyze_item method."""

    @pytest.mark.asyncio
    async def test_analyze_item_valid_profit(self, mock_api_client):
        """Test analyzing item with valid profit."""
        from src.dmarket.arbitrage_scanner import ArbitrageScanner
        
        scanner = ArbitrageScanner(
            api_client=mock_api_client,
            enable_liquidity_filter=False,
            enable_competition_filter=False,
        )
        
        item = {
            "title": "Test Item",
            "price": {"USD": 1000},  # $10
            "suggestedPrice": {"USD": 1200},  # $12 (20% profit)
        }
        config = {
            "price_range": (5.0, 50.0),
            "min_profit_percent": 10.0,
        }
        
        result = await scanner._analyze_item(item, config, "csgo")
        
        assert result is not None
        assert result["buy_price"] == 10.0
        assert result["suggested_price"] == 12.0
        assert result["profit"] == 2.0

    @pytest.mark.asyncio
    async def test_analyze_item_price_out_of_range(self, mock_api_client):
        """Test analyzing item with price out of range."""
        from src.dmarket.arbitrage_scanner import ArbitrageScanner
        
        scanner = ArbitrageScanner(
            api_client=mock_api_client,
            enable_liquidity_filter=False,
            enable_competition_filter=False,
        )
        
        item = {
            "title": "Expensive Item",
            "price": {"USD": 10000},  # $100
            "suggestedPrice": {"USD": 12000},
        }
        config = {
            "price_range": (5.0, 50.0),  # Max $50
            "min_profit_percent": 10.0,
        }
        
        result = await scanner._analyze_item(item, config, "csgo")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_analyze_item_low_profit(self, mock_api_client):
        """Test analyzing item with low profit percent."""
        from src.dmarket.arbitrage_scanner import ArbitrageScanner
        
        scanner = ArbitrageScanner(
            api_client=mock_api_client,
            enable_liquidity_filter=False,
            enable_competition_filter=False,
        )
        
        item = {
            "title": "Low Profit Item",
            "price": {"USD": 1000},  # $10
            "suggestedPrice": {"USD": 1050},  # Only 5% profit
        }
        config = {
            "price_range": (5.0, 50.0),
            "min_profit_percent": 10.0,  # Min 10%
        }
        
        result = await scanner._analyze_item(item, config, "csgo")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_analyze_item_with_liquidity_data(self, mock_api_client):
        """Test analyzing item with pre-existing liquidity data."""
        from src.dmarket.arbitrage_scanner import ArbitrageScanner
        
        scanner = ArbitrageScanner(
            api_client=mock_api_client,
            enable_liquidity_filter=True,
            enable_competition_filter=False,
        )
        
        item = {
            "title": "Liquid Item",
            "price": {"USD": 1000},
            "suggestedPrice": {"USD": 1200},
            "_liquidity": {
                "offer_count": 20,
                "order_count": 10,
                "liquidity_score": 80,
                "is_liquid": True,
            }
        }
        config = {
            "price_range": (5.0, 50.0),
            "min_profit_percent": 10.0,
        }
        
        result = await scanner._analyze_item(item, config, "csgo")
        
        assert result is not None
        assert "liquidity_score" in result

    @pytest.mark.asyncio
    async def test_analyze_item_illiquid_filtered(self, mock_api_client):
        """Test illiquid item is filtered out."""
        from src.dmarket.arbitrage_scanner import ArbitrageScanner
        
        scanner = ArbitrageScanner(
            api_client=mock_api_client,
            enable_liquidity_filter=True,
            enable_competition_filter=False,
        )
        
        item = {
            "title": "Illiquid Item",
            "price": {"USD": 1000},
            "suggestedPrice": {"USD": 1200},
            "_liquidity": {
                "offer_count": 2,
                "order_count": 1,
                "liquidity_score": 10,
                "is_liquid": False,
            }
        }
        config = {
            "price_range": (5.0, 50.0),
            "min_profit_percent": 10.0,
        }
        
        result = await scanner._analyze_item(item, config, "csgo")
        
        assert result is None


class TestGetCurrentItemData:
    """Tests for _get_current_item_data method."""

    @pytest.mark.asyncio
    async def test_get_current_item_data_success(self, mock_api_client):
        """Test successful item data retrieval."""
        from src.dmarket.arbitrage_scanner import ArbitrageScanner
        
        mock_api_client._request = AsyncMock(return_value={
            "objects": [{
                "itemId": "item1",
                "title": "Test Item",
                "price": {"USD": 1000},
            }]
        })
        
        scanner = ArbitrageScanner(api_client=mock_api_client)
        
        result = await scanner._get_current_item_data("item1", "csgo", mock_api_client)
        
        assert result is not None
        assert result["itemId"] == "item1"

    @pytest.mark.asyncio
    async def test_get_current_item_data_not_found(self, mock_api_client):
        """Test item data retrieval when item not found."""
        from src.dmarket.arbitrage_scanner import ArbitrageScanner
        
        mock_api_client._request = AsyncMock(return_value={"objects": []})
        
        scanner = ArbitrageScanner(api_client=mock_api_client)
        
        result = await scanner._get_current_item_data("nonexistent", "csgo", mock_api_client)
        
        assert result is None

    @pytest.mark.asyncio
    async def test_get_current_item_data_exception(self, mock_api_client):
        """Test item data retrieval handles exception."""
        from src.dmarket.arbitrage_scanner import ArbitrageScanner
        
        mock_api_client._request = AsyncMock(side_effect=Exception("API Error"))
        
        scanner = ArbitrageScanner(api_client=mock_api_client)
        
        result = await scanner._get_current_item_data("item1", "csgo", mock_api_client)
        
        assert result is None


class TestPurchaseItem:
    """Tests for _purchase_item method."""

    @pytest.mark.asyncio
    async def test_purchase_item_success(self, mock_api_client):
        """Test successful item purchase."""
        from src.dmarket.arbitrage_scanner import ArbitrageScanner
        
        mock_api_client._request = AsyncMock(return_value={
            "items": [{"itemId": "new_item_id"}]
        })
        
        scanner = ArbitrageScanner(api_client=mock_api_client)
        
        result = await scanner._purchase_item("item1", 10.0, mock_api_client)
        
        assert result["success"] is True
        assert result["new_item_id"] == "new_item_id"

    @pytest.mark.asyncio
    async def test_purchase_item_error_response(self, mock_api_client):
        """Test purchase with error response."""
        from src.dmarket.arbitrage_scanner import ArbitrageScanner
        
        mock_api_client._request = AsyncMock(return_value={
            "error": {"message": "Item not available"}
        })
        
        scanner = ArbitrageScanner(api_client=mock_api_client)
        
        result = await scanner._purchase_item("item1", 10.0, mock_api_client)
        
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_purchase_item_exception(self, mock_api_client):
        """Test purchase handles exception."""
        from src.dmarket.arbitrage_scanner import ArbitrageScanner
        
        mock_api_client._request = AsyncMock(side_effect=Exception("Network error"))
        
        scanner = ArbitrageScanner(api_client=mock_api_client)
        
        result = await scanner._purchase_item("item1", 10.0, mock_api_client)
        
        assert result["success"] is False


class TestListItemForSale:
    """Tests for _list_item_for_sale method."""

    @pytest.mark.asyncio
    async def test_list_item_for_sale_success(self, mock_api_client):
        """Test successful item listing."""
        from src.dmarket.arbitrage_scanner import ArbitrageScanner
        
        mock_api_client._request = AsyncMock(return_value={"success": True})
        
        scanner = ArbitrageScanner(api_client=mock_api_client)
        
        result = await scanner._list_item_for_sale("item1", 15.0, mock_api_client)
        
        assert result["success"] is True
        assert result["price"] == 15.0

    @pytest.mark.asyncio
    async def test_list_item_for_sale_error_response(self, mock_api_client):
        """Test listing with error response."""
        from src.dmarket.arbitrage_scanner import ArbitrageScanner
        
        mock_api_client._request = AsyncMock(return_value={
            "error": {"message": "Price too low"}
        })
        
        scanner = ArbitrageScanner(api_client=mock_api_client)
        
        result = await scanner._list_item_for_sale("item1", 5.0, mock_api_client)
        
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_list_item_for_sale_exception(self, mock_api_client):
        """Test listing handles exception."""
        from src.dmarket.arbitrage_scanner import ArbitrageScanner
        
        mock_api_client._request = AsyncMock(side_effect=Exception("API Error"))
        
        scanner = ArbitrageScanner(api_client=mock_api_client)
        
        result = await scanner._list_item_for_sale("item1", 15.0, mock_api_client)
        
        assert result["success"] is False
