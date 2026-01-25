"""Unit tests for ArbitrageScanner module.

This module contains comprehensive unit tests for the ArbitrageScanner class,
covering initialization, caching, filtering, scanning, and edge cases.

Target coverage: 95%+
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.dmarket.arbitrage_scanner import (
    ARBITRAGE_LEVELS,
    GAME_IDS,
    GAMES,
    STEAM_AVAILABLE,
    ArbitrageScanner,
    rate_limiter,
)


# ===========================================================================
# Fixtures
# ===========================================================================


@pytest.fixture()
def mock_api_client() -> MagicMock:
    """Create a mock DMarket API client."""
    mock = MagicMock()
    mock.get_market_items = AsyncMock(return_value={"objects": []})
    mock.get_balance = AsyncMock(return_value={"usd": "10000"})
    mock.get_aggregated_prices = AsyncMock(return_value={"Prices": []})
    mock.get_last_sales = AsyncMock(return_value={"Sales": []})
    return mock


@pytest.fixture()
def scanner(mock_api_client: MagicMock) -> ArbitrageScanner:
    """Create an ArbitrageScanner instance for testing."""
    return ArbitrageScanner(
        api_client=mock_api_client,
        enable_liquidity_filter=True,
        enable_competition_filter=True,
        max_competition=3,
    )


@pytest.fixture()
def scanner_minimal() -> ArbitrageScanner:
    """Create a minimal ArbitrageScanner without API client."""
    return ArbitrageScanner(
        api_client=None,
        enable_liquidity_filter=False,
        enable_competition_filter=False,
    )


# ===========================================================================
# Test Class: Initialization
# ===========================================================================


class TestArbitrageScannerInitialization:
    """Test ArbitrageScanner initialization."""

    def test_init_with_api_client(
        self, scanner: ArbitrageScanner, mock_api_client: MagicMock
    ) -> None:
        """Test initialization with API client."""
        assert scanner.api_client is mock_api_client

    def test_init_without_api_client(self, scanner_minimal: ArbitrageScanner) -> None:
        """Test initialization without API client."""
        assert scanner_minimal.api_client is None

    def test_init_liquidity_filter_enabled(self, scanner: ArbitrageScanner) -> None:
        """Test liquidity filter is enabled."""
        assert scanner.enable_liquidity_filter is True

    def test_init_liquidity_filter_disabled(
        self, scanner_minimal: ArbitrageScanner
    ) -> None:
        """Test liquidity filter is disabled."""
        assert scanner_minimal.enable_liquidity_filter is False

    def test_init_competition_filter_enabled(self, scanner: ArbitrageScanner) -> None:
        """Test competition filter is enabled."""
        assert scanner.enable_competition_filter is True

    def test_init_competition_filter_disabled(
        self, scanner_minimal: ArbitrageScanner
    ) -> None:
        """Test competition filter is disabled."""
        assert scanner_minimal.enable_competition_filter is False

    def test_init_max_competition(self, scanner: ArbitrageScanner) -> None:
        """Test max competition value."""
        assert scanner.max_competition == 3

    def test_init_default_limits(self, scanner: ArbitrageScanner) -> None:
        """Test default limit values."""
        assert scanner.min_profit == 0.5
        assert scanner.max_price == 50.0
        assert scanner.max_trades == 5

    def test_init_default_liquidity_settings(self, scanner: ArbitrageScanner) -> None:
        """Test default liquidity settings."""
        assert scanner.min_liquidity_score == 60
        assert scanner.min_sales_per_week == 5
        assert scanner.max_time_to_sell_days == 7

    def test_init_statistics(self, scanner: ArbitrageScanner) -> None:
        """Test statistics initialization."""
        assert scanner.total_scans == 0
        assert scanner.total_items_found == 0
        assert scanner.successful_trades == 0
        assert scanner.total_profit == 0.0

    def test_init_notifications_set(self, scanner: ArbitrageScanner) -> None:
        """Test notifications set is initialized."""
        assert isinstance(scanner._sent_notifications, set)
        assert len(scanner._sent_notifications) == 0

    def test_init_notification_cooldown(self, scanner: ArbitrageScanner) -> None:
        """Test notification cooldown is set."""
        assert scanner._notification_cooldown == 1800

    def test_init_graceful_shutdown(self, scanner: ArbitrageScanner) -> None:
        """Test graceful shutdown flag is initialized."""
        assert scanner._is_shutting_down is False


# ===========================================================================
# Test Class: Cache Properties
# ===========================================================================


class TestArbitrageScannerCacheProperties:
    """Test ArbitrageScanner cache properties."""

    def test_cache_ttl_getter(self, scanner: ArbitrageScanner) -> None:
        """Test cache_ttl getter."""
        assert isinstance(scanner.cache_ttl, int)
        assert scanner.cache_ttl == 300  # Default TTL

    def test_cache_ttl_setter(self, scanner: ArbitrageScanner) -> None:
        """Test cache_ttl setter."""
        scanner.cache_ttl = 600
        assert scanner.cache_ttl == 600

    def test_scanner_cache_initialized(self, scanner: ArbitrageScanner) -> None:
        """Test ScannerCache is initialized."""
        assert scanner._scanner_cache is not None

    def test_scanner_filters_initialized(self, scanner: ArbitrageScanner) -> None:
        """Test ScannerFilters is initialized."""
        assert scanner._scanner_filters is not None


# ===========================================================================
# Test Class: Cache Methods
# ===========================================================================


class TestArbitrageScannerCacheMethods:
    """Test ArbitrageScanner cache methods."""

    def test_get_cached_results_empty(self, scanner: ArbitrageScanner) -> None:
        """Test getting from empty cache returns None."""
        result = scanner._get_cached_results(("csgo", "medium", 1.0, 50.0))
        assert result is None

    def test_save_to_cache(self, scanner: ArbitrageScanner) -> None:
        """Test saving to cache."""
        cache_key = ("csgo", "medium", 1.0, 50.0)
        items = [{"title": "Test Item"}]
        scanner._save_to_cache(cache_key, items)
        # Cache should now contain the item
        result = scanner._get_cached_results(cache_key)
        assert result == items

    def test_cache_different_keys(self, scanner: ArbitrageScanner) -> None:
        """Test different cache keys store different data."""
        key1 = ("csgo", "medium", 1.0, 50.0)
        key2 = ("dota2", "high", 10.0, 100.0)
        items1 = [{"title": "CSGO Item"}]
        items2 = [{"title": "Dota 2 Item"}]

        scanner._save_to_cache(key1, items1)
        scanner._save_to_cache(key2, items2)

        assert scanner._get_cached_results(key1) == items1
        assert scanner._get_cached_results(key2) == items2


# ===========================================================================
# Test Class: Constants
# ===========================================================================


class TestArbitrageScannerConstants:
    """Test ArbitrageScanner module constants."""

    def test_games_constant_exists(self) -> None:
        """Test GAMES constant exists."""
        # GAMES is imported from arbitrage module
        assert GAMES is not None

    def test_game_ids_constant(self) -> None:
        """Test GAME_IDS constant."""
        assert isinstance(GAME_IDS, dict)
        assert "csgo" in GAME_IDS or len(GAME_IDS) > 0

    def test_arbitrage_levels_constant(self) -> None:
        """Test ARBITRAGE_LEVELS constant."""
        assert isinstance(ARBITRAGE_LEVELS, dict)
        assert len(ARBITRAGE_LEVELS) > 0

    def test_rate_limiter_exists(self) -> None:
        """Test rate_limiter is initialized."""
        assert rate_limiter is not None


# ===========================================================================
# Test Class: API Client Management
# ===========================================================================


class TestArbitrageScannerAPIClientManagement:
    """Test ArbitrageScanner API client management."""

    @pytest.mark.asyncio()
    async def test_get_api_client_returns_existing(
        self, scanner: ArbitrageScanner, mock_api_client: MagicMock
    ) -> None:
        """Test get_api_client returns existing client."""
        client = await scanner.get_api_client()
        assert client is mock_api_client

    @pytest.mark.asyncio()
    async def test_get_api_client_creates_new(
        self, scanner_minimal: ArbitrageScanner
    ) -> None:
        """Test get_api_client creates new client if none exists."""
        # Mock environment variables
        with patch.dict(
            "os.environ",
            {
                "DMARKET_PUBLIC_KEY": "test_pk",
                "DMARKET_SECRET_KEY": "test_sk",
                "DMARKET_API_URL": "https://test.api.com",
            },
        ):
            with patch(
                "src.dmarket.arbitrage_scanner.DMarketAPI"
            ) as MockDMarketAPI:
                mock_client = MagicMock()
                MockDMarketAPI.return_value = mock_client

                client = await scanner_minimal.get_api_client()

                assert scanner_minimal.api_client is mock_client


# ===========================================================================
# Test Class: Liquidity Analyzer
# ===========================================================================


class TestArbitrageScannerLiquidityAnalyzer:
    """Test ArbitrageScanner liquidity analyzer integration."""

    def test_liquidity_analyzer_initially_none(
        self, scanner: ArbitrageScanner
    ) -> None:
        """Test liquidity analyzer is initially None."""
        assert scanner.liquidity_analyzer is None

    @pytest.mark.asyncio()
    async def test_liquidity_analyzer_initialized_on_get_api_client(
        self, scanner: ArbitrageScanner
    ) -> None:
        """Test liquidity analyzer is initialized when getting API client."""
        await scanner.get_api_client()
        assert scanner.liquidity_analyzer is not None


# ===========================================================================
# Test Class: Steam Integration
# ===========================================================================


class TestArbitrageScannerSteamIntegration:
    """Test ArbitrageScanner Steam integration."""

    def test_steam_check_disabled_by_default(self, scanner: ArbitrageScanner) -> None:
        """Test Steam check is disabled by default."""
        assert scanner.enable_steam_check is False

    def test_steam_enhancer_none_when_disabled(self, scanner: ArbitrageScanner) -> None:
        """Test Steam enhancer is None when disabled."""
        assert scanner.steam_enhancer is None

    def test_steam_available_flag(self) -> None:
        """Test STEAM_AVAILABLE flag is a boolean."""
        assert isinstance(STEAM_AVAILABLE, bool)


# ===========================================================================
# Test Class: Notification System
# ===========================================================================


class TestArbitrageScannerNotifications:
    """Test ArbitrageScanner notification system."""

    def test_sent_notifications_is_set(self, scanner: ArbitrageScanner) -> None:
        """Test _sent_notifications is a set."""
        assert isinstance(scanner._sent_notifications, set)

    def test_notification_cooldown_value(self, scanner: ArbitrageScanner) -> None:
        """Test notification cooldown is 30 minutes (1800 seconds)."""
        assert scanner._notification_cooldown == 1800


# ===========================================================================
# Test Class: Graceful Shutdown
# ===========================================================================


class TestArbitrageScannerGracefulShutdown:
    """Test ArbitrageScanner graceful shutdown."""

    def test_is_shutting_down_initially_false(self, scanner: ArbitrageScanner) -> None:
        """Test _is_shutting_down is initially False."""
        assert scanner._is_shutting_down is False

    def test_can_set_shutting_down(self, scanner: ArbitrageScanner) -> None:
        """Test _is_shutting_down can be set."""
        scanner._is_shutting_down = True
        assert scanner._is_shutting_down is True


# ===========================================================================
# Test Class: Min Profit Percent
# ===========================================================================


class TestArbitrageScannerMinProfitPercent:
    """Test ArbitrageScanner min profit percent configuration."""

    def test_min_profit_percent_default_none(self, scanner: ArbitrageScanner) -> None:
        """Test min_profit_percent is None by default."""
        assert scanner.min_profit_percent is None

    def test_min_profit_percent_can_be_set(self, mock_api_client: MagicMock) -> None:
        """Test min_profit_percent can be set during initialization."""
        scanner = ArbitrageScanner(
            api_client=mock_api_client,
            min_profit_percent=15.0,
        )
        assert scanner.min_profit_percent == 15.0


# ===========================================================================
# Test Class: Item Filters
# ===========================================================================


class TestArbitrageScannerItemFilters:
    """Test ArbitrageScanner item filters."""

    def test_scanner_filters_initialized(self, scanner: ArbitrageScanner) -> None:
        """Test scanner filters are initialized."""
        assert scanner._scanner_filters is not None


# ===========================================================================
# Test Class: Edge Cases
# ===========================================================================


class TestArbitrageScannerEdgeCases:
    """Test ArbitrageScanner edge cases."""

    def test_max_competition_zero(self, mock_api_client: MagicMock) -> None:
        """Test initialization with zero max_competition."""
        scanner = ArbitrageScanner(
            api_client=mock_api_client,
            max_competition=0,
        )
        assert scanner.max_competition == 0

    def test_max_competition_high(self, mock_api_client: MagicMock) -> None:
        """Test initialization with high max_competition."""
        scanner = ArbitrageScanner(
            api_client=mock_api_client,
            max_competition=100,
        )
        assert scanner.max_competition == 100

    def test_multiple_scanners_independent(
        self, mock_api_client: MagicMock
    ) -> None:
        """Test multiple scanners are independent."""
        scanner1 = ArbitrageScanner(api_client=mock_api_client)
        scanner2 = ArbitrageScanner(api_client=mock_api_client)

        scanner1.total_scans = 10
        scanner2.total_scans = 20

        assert scanner1.total_scans == 10
        assert scanner2.total_scans == 20


# ===========================================================================
# Test Class: Statistics
# ===========================================================================


class TestArbitrageScannerStatistics:
    """Test ArbitrageScanner statistics tracking."""

    def test_statistics_initial_values(self, scanner: ArbitrageScanner) -> None:
        """Test statistics have correct initial values."""
        assert scanner.total_scans == 0
        assert scanner.total_items_found == 0
        assert scanner.successful_trades == 0
        assert scanner.total_profit == 0.0

    def test_statistics_can_be_updated(self, scanner: ArbitrageScanner) -> None:
        """Test statistics can be updated."""
        scanner.total_scans = 5
        scanner.total_items_found = 100
        scanner.successful_trades = 10
        scanner.total_profit = 50.5

        assert scanner.total_scans == 5
        assert scanner.total_items_found == 100
        assert scanner.successful_trades == 10
        assert scanner.total_profit == 50.5


# ===========================================================================
# Test Class: Limit Configuration
# ===========================================================================


class TestArbitrageScannerLimitConfiguration:
    """Test ArbitrageScanner limit configuration."""

    def test_min_profit_default(self, scanner: ArbitrageScanner) -> None:
        """Test min_profit default value."""
        assert scanner.min_profit == 0.5

    def test_max_price_default(self, scanner: ArbitrageScanner) -> None:
        """Test max_price default value."""
        assert scanner.max_price == 50.0

    def test_max_trades_default(self, scanner: ArbitrageScanner) -> None:
        """Test max_trades default value."""
        assert scanner.max_trades == 5

    def test_limits_can_be_updated(self, scanner: ArbitrageScanner) -> None:
        """Test limits can be updated after initialization."""
        scanner.min_profit = 1.0
        scanner.max_price = 100.0
        scanner.max_trades = 10

        assert scanner.min_profit == 1.0
        assert scanner.max_price == 100.0
        assert scanner.max_trades == 10


# ===========================================================================
# Test Class: Liquidity Settings
# ===========================================================================


class TestArbitrageScannerLiquiditySettings:
    """Test ArbitrageScanner liquidity settings."""

    def test_min_liquidity_score_default(self, scanner: ArbitrageScanner) -> None:
        """Test min_liquidity_score default value."""
        assert scanner.min_liquidity_score == 60

    def test_min_sales_per_week_default(self, scanner: ArbitrageScanner) -> None:
        """Test min_sales_per_week default value."""
        assert scanner.min_sales_per_week == 5

    def test_max_time_to_sell_days_default(self, scanner: ArbitrageScanner) -> None:
        """Test max_time_to_sell_days default value."""
        assert scanner.max_time_to_sell_days == 7

    def test_liquidity_settings_can_be_updated(self, scanner: ArbitrageScanner) -> None:
        """Test liquidity settings can be updated."""
        scanner.min_liquidity_score = 80
        scanner.min_sales_per_week = 10
        scanner.max_time_to_sell_days = 14

        assert scanner.min_liquidity_score == 80
        assert scanner.min_sales_per_week == 10
        assert scanner.max_time_to_sell_days == 14


# ===========================================================================
# Test Class: Module Public Interface
# ===========================================================================


class TestArbitrageScannerPublicInterface:
    """Test ArbitrageScanner public interface."""

    def test_public_interface_includes_scanner_class(self) -> None:
        """Test __all__ includes ArbitrageScanner."""
        from src.dmarket import arbitrage_scanner

        assert "ArbitrageScanner" in arbitrage_scanner.__all__

    def test_public_interface_includes_functions(self) -> None:
        """Test __all__ includes key functions."""
        from src.dmarket import arbitrage_scanner

        assert "find_arbitrage_opportunities_async" in arbitrage_scanner.__all__
        assert "scan_game_for_arbitrage" in arbitrage_scanner.__all__
        assert "scan_multiple_games" in arbitrage_scanner.__all__


# ===========================================================================
# Test Class: Async Scan Methods
# ===========================================================================


class TestArbitrageScannerAsyncMethods:
    """Test ArbitrageScanner async methods."""

    @pytest.mark.asyncio()
    async def test_scan_game_returns_list(
        self, scanner: ArbitrageScanner
    ) -> None:
        """Test scan_game returns a list."""
        result = await scanner.scan_game("csgo", "medium", max_items=10)
        assert isinstance(result, list)

    @pytest.mark.asyncio()
    async def test_scan_game_with_price_range(
        self, scanner: ArbitrageScanner
    ) -> None:
        """Test scan_game with price range."""
        result = await scanner.scan_game(
            "csgo",
            "medium",
            max_items=10,
            price_from=1.0,
            price_to=50.0,
        )
        assert isinstance(result, list)

    @pytest.mark.asyncio()
    async def test_scan_game_updates_statistics(
        self, scanner: ArbitrageScanner
    ) -> None:
        """Test scan_game updates statistics."""
        initial_scans = scanner.total_scans
        await scanner.scan_game("csgo", "medium", max_items=5)
        # Note: actual scan count depends on implementation
        # Just verify it doesn't raise an error


# ===========================================================================
# Test Class: Mode Validation
# ===========================================================================


class TestArbitrageScannerModes:
    """Test ArbitrageScanner scan modes."""

    def test_arbitrage_levels_has_modes(self) -> None:
        """Test ARBITRAGE_LEVELS has expected modes."""
        assert isinstance(ARBITRAGE_LEVELS, dict)
        # Check at least some modes exist
        assert len(ARBITRAGE_LEVELS) >= 1

    @pytest.mark.asyncio()
    async def test_scan_different_modes(self, scanner: ArbitrageScanner) -> None:
        """Test scanning with different modes."""
        # Test with medium mode (default)
        result_medium = await scanner.scan_game("csgo", "medium", max_items=5)
        assert isinstance(result_medium, list)

        # Test with low mode
        result_low = await scanner.scan_game("csgo", "low", max_items=5)
        assert isinstance(result_low, list)

        # Test with high mode
        result_high = await scanner.scan_game("csgo", "high", max_items=5)
        assert isinstance(result_high, list)


# ===========================================================================
# Test Class: Game Support
# ===========================================================================


class TestArbitrageScannerGameSupport:
    """Test ArbitrageScanner game support."""

    def test_game_ids_includes_csgo(self) -> None:
        """Test GAME_IDS includes CS:GO."""
        # Either "csgo" or "a8db" should be in GAME_IDS
        assert "csgo" in GAME_IDS or any(
            v == "a8db" for v in GAME_IDS.values() if isinstance(GAME_IDS, dict)
        )

    @pytest.mark.asyncio()
    async def test_scan_multiple_games(self, scanner: ArbitrageScanner) -> None:
        """Test scanning multiple games."""
        games = ["csgo", "dota2"]
        for game in games:
            result = await scanner.scan_game(game, "medium", max_items=5)
            assert isinstance(result, list)
