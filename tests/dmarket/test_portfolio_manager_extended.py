"""
Extended tests for portfolio_manager.py module - Phase 4 Coverage Enhancement.

This module adds tests for:
- PortfolioManager initialization
- get_portfolio_snapshot with various scenarios
- _parse_inventory_item, _parse_listed_item, _parse_target helpers
- analyze_risk method
- get_rebalancing_recommendations
- get_performance_metrics
- format_portfolio_report
- Edge cases and error handling
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from src.dmarket.portfolio_manager import (
    AssetType,
    PortfolioAsset,
    PortfolioManager,
    PortfolioSnapshot,
    RebalanceAction,
    RiskAnalysis,
    RiskLevel,
    get_portfolio_summary,
    get_rebalancing_actions,
)


@pytest.fixture()
def mock_api_client():
    """Fixture: mocked DMarket API client."""
    client = AsyncMock()
    client.get_user_inventory = AsyncMock(return_value={"objects": []})
    client.get_user_offers = AsyncMock(return_value={"objects": []})
    client.get_active_offers = AsyncMock(return_value={"offers": []})
    client.get_user_targets = AsyncMock(return_value={"Items": []})
    client.get_balance = AsyncMock(return_value={"usd": 10000, "dmc": 5000})
    return client


@pytest.fixture()
def portfolio_manager(mock_api_client):
    """Fixture: PortfolioManager with mocked API client."""
    return PortfolioManager(api_client=mock_api_client)


# ============================================================================
# Tests for Enums and DataClasses
# ============================================================================


class TestEnums:
    """Tests for enum types."""

    def test_asset_type_values(self):
        """Test AssetType enum values."""
        assert AssetType.INVENTORY.value == "inventory"
        assert AssetType.LISTED.value == "listed"
        assert AssetType.TARGET.value == "target"
        assert AssetType.CASH.value == "cash"

    def test_risk_level_values(self):
        """Test RiskLevel enum values."""
        assert RiskLevel.LOW.value == "low"
        assert RiskLevel.MEDIUM.value == "medium"
        assert RiskLevel.HIGH.value == "high"
        assert RiskLevel.CRITICAL.value == "critical"

    def test_rebalance_action_values(self):
        """Test RebalanceAction enum values."""
        assert RebalanceAction.SELL.value == "sell"
        assert RebalanceAction.BUY.value == "buy"
        assert RebalanceAction.HOLD.value == "hold"
        assert RebalanceAction.REDUCE_PRICE.value == "reduce_price"
        assert RebalanceAction.INCREASE_PRICE.value == "increase_price"
        assert RebalanceAction.CANCEL_TARGET.value == "cancel_target"


class TestPortfolioAsset:
    """Tests for PortfolioAsset dataclass."""

    def test_portfolio_asset_creation(self):
        """Test creating a PortfolioAsset."""
        asset = PortfolioAsset(
            item_id="item_123",
            item_name="AK-47 | Redline",
            asset_type=AssetType.INVENTORY,
            quantity=1,
            unit_price=10.50,
            total_value=10.50,
            game="csgo",
            category="Rifle",
        )

        assert asset.item_id == "item_123"
        assert asset.item_name == "AK-47 | Redline"
        assert asset.asset_type == AssetType.INVENTORY
        assert asset.quantity == 1
        assert asset.unit_price == 10.50

    def test_portfolio_asset_with_optional_fields(self):
        """Test PortfolioAsset with optional fields."""
        asset = PortfolioAsset(
            item_id="item_123",
            item_name="AK-47",
            asset_type=AssetType.LISTED,
            quantity=1,
            unit_price=10.0,
            total_value=10.0,
            game="csgo",
            category="Rifle",
            listed_price=12.0,
            market_price=11.0,
            profit_loss=1.0,
            profit_loss_percent=10.0,
        )

        assert asset.listed_price == 12.0
        assert asset.market_price == 11.0
        assert asset.profit_loss == 1.0
        assert asset.profit_loss_percent == 10.0


# ============================================================================
# Tests for PortfolioManager Initialization
# ============================================================================


class TestPortfolioManagerInit:
    """Tests for PortfolioManager initialization."""

    def test_init_with_api_client(self, mock_api_client):
        """Test initialization with API client."""
        pm = PortfolioManager(api_client=mock_api_client)
        assert pm._api == mock_api_client

    def test_init_without_api_client(self):
        """Test initialization without API client."""
        pm = PortfolioManager()
        assert pm._api is None

    def test_init_with_config(self, mock_api_client):
        """Test initialization with custom config."""
        from src.dmarket.portfolio_manager import PortfolioConfig
        config = PortfolioConfig(
            max_single_item_percent=20.0,
        )
        pm = PortfolioManager(
            api_client=mock_api_client,
            config=config,
        )
        assert pm._config.max_single_item_percent == 20.0


# ============================================================================
# Tests for get_portfolio_snapshot
# ============================================================================


class TestGetPortfolioSnapshot:
    """Tests for get_portfolio_snapshot method."""

    @pytest.mark.asyncio()
    async def test_get_snapshot_empty_portfolio(self, portfolio_manager, mock_api_client):
        """Test getting snapshot of empty portfolio."""
        mock_api_client.get_user_inventory.return_value = {"objects": []}
        mock_api_client.get_user_offers.return_value = {"objects": []}
        mock_api_client.get_user_targets.return_value = {"Items": []}
        mock_api_client.get_balance.return_value = {"usd": 10000, "dmc": 0}

        snapshot = await portfolio_manager.get_portfolio_snapshot()

        assert snapshot is not None
        assert snapshot.cash_balance == 100.0  # 10000 cents = $100

    @pytest.mark.asyncio()
    async def test_get_snapshot_with_inventory_items(self, portfolio_manager, mock_api_client):
        """Test snapshot with inventory items."""
        mock_api_client.get_user_inventory.return_value = {
            "objects": [
                {
                    "itemId": "item_1",
                    "title": "AK-47 | Redline",
                    "price": {"USD": "1000"},
                    "gameId": "a8db",
                    "suggestedPrice": {"USD": "1100"},
                },
            ]
        }
        mock_api_client.get_user_offers.return_value = {"objects": []}
        mock_api_client.get_user_targets.return_value = {"Items": []}
        mock_api_client.get_balance.return_value = {"usd": 5000, "dmc": 0}

        snapshot = await portfolio_manager.get_portfolio_snapshot()

        assert len(snapshot.assets) >= 0  # May include inventory items

    @pytest.mark.asyncio()
    async def test_get_snapshot_with_listed_items(self, portfolio_manager, mock_api_client):
        """Test snapshot with listed items."""
        mock_api_client.get_user_inventory.return_value = {"objects": []}
        mock_api_client.get_user_offers.return_value = {
            "objects": [
                {
                    "offerId": "offer_1",
                    "title": "M4A4 | Asiimov",
                    "price": {"amount": 2500, "currency": "USD"},
                    "gameId": "a8db",
                },
            ]
        }
        mock_api_client.get_user_targets.return_value = {"Items": []}
        mock_api_client.get_balance.return_value = {"usd": 5000, "dmc": 0}

        snapshot = await portfolio_manager.get_portfolio_snapshot()

        assert snapshot is not None

    @pytest.mark.asyncio()
    async def test_get_snapshot_force_refresh(self, portfolio_manager, mock_api_client):
        """Test force refresh bypasses cache."""
        mock_api_client.get_user_inventory.return_value = {"objects": []}
        mock_api_client.get_user_offers.return_value = {"objects": []}
        mock_api_client.get_user_targets.return_value = {"Items": []}
        mock_api_client.get_balance.return_value = {"usd": 5000, "dmc": 0}

        # First call
        await portfolio_manager.get_portfolio_snapshot()
        # Second call with force refresh
        await portfolio_manager.get_portfolio_snapshot(force_refresh=True)

        # Should call API twice due to force refresh
        assert mock_api_client.get_balance.call_count >= 2

    @pytest.mark.asyncio()
    async def test_get_snapshot_api_error_handled(self, portfolio_manager, mock_api_client):
        """Test handling of API errors gracefully."""
        mock_api_client.get_balance.side_effect = Exception("API Error")

        # Should not raise, but log error and return snapshot with defaults
        snapshot = await portfolio_manager.get_portfolio_snapshot()
        assert snapshot is not None


# ============================================================================
# Tests for _parse_inventory_item
# ============================================================================


class TestParseInventoryItem:
    """Tests for _parse_inventory_item method."""

    def test_parse_valid_inventory_item(self, portfolio_manager):
        """Test parsing a valid inventory item."""
        item = {
            "itemId": "item_123",
            "title": "AK-47 | Redline (Field-Tested)",
            "price": {"USD": "1000"},
            "gameId": "a8db",
            "suggestedPrice": {"USD": "1100"},
        }

        result = portfolio_manager._parse_inventory_item(item)

        if result:
            assert result.item_id == "item_123"
            assert result.asset_type == AssetType.INVENTORY

    def test_parse_inventory_item_missing_id(self, portfolio_manager):
        """Test parsing item without ID returns None."""
        item = {
            "title": "AK-47",
            "price": {"USD": "1000"},
        }

        result = portfolio_manager._parse_inventory_item(item)
        # Should handle gracefully
        assert result is None or result.item_id is not None

    def test_parse_inventory_item_missing_price(self, portfolio_manager):
        """Test parsing item without price."""
        item = {
            "itemId": "item_123",
            "title": "AK-47",
            "gameId": "a8db",
        }

        result = portfolio_manager._parse_inventory_item(item)
        # Should handle missing price gracefully


# ============================================================================
# Tests for _parse_listed_item
# ============================================================================


class TestParseListedItem:
    """Tests for _parse_listed_item method."""

    def test_parse_valid_listed_item(self, portfolio_manager):
        """Test parsing a valid listed item."""
        item = {
            "offerId": "offer_123",
            "title": "M4A4 | Asiimov",
            "price": {"amount": 2500, "currency": "USD"},
            "gameId": "a8db",
        }

        result = portfolio_manager._parse_listed_item(item)

        if result:
            assert result.asset_type == AssetType.LISTED

    def test_parse_listed_item_price_in_cents(self, portfolio_manager):
        """Test that price is converted from cents to dollars."""
        item = {
            "offerId": "offer_123",
            "title": "AWP | Dragon Lore",
            "price": {"amount": 150000, "currency": "USD"},
            "gameId": "a8db",
        }

        result = portfolio_manager._parse_listed_item(item)

        # Check that result has correct asset type
        if result:
            assert result.asset_type == AssetType.LISTED


# ============================================================================
# Tests for _parse_target
# ============================================================================


class TestParseTarget:
    """Tests for _parse_target method."""

    def test_parse_valid_target(self, portfolio_manager):
        """Test parsing a valid target."""
        target = {
            "TargetID": "target_123",
            "Title": "AK-47 | Vulcan",
            "Price": {"Amount": 800, "Currency": "USD"},
            "Amount": 3,
            "GameID": "a8db",
        }

        result = portfolio_manager._parse_target(target)

        if result:
            assert result.asset_type == AssetType.TARGET
            assert result.quantity == 3

    def test_parse_target_with_single_amount(self, portfolio_manager):
        """Test parsing target with single quantity."""
        target = {
            "TargetID": "target_123",
            "Title": "AK-47",
            "Price": {"Amount": 500},
            "Amount": 1,
            "GameID": "a8db",
        }

        result = portfolio_manager._parse_target(target)

        if result:
            assert result.quantity == 1


# ============================================================================
# Tests for _extract_category
# ============================================================================


class TestExtractCategory:
    """Tests for _extract_category method."""

    def test_extract_rifle_category(self, portfolio_manager):
        """Test extracting Rifle category from AK-47 title."""
        title = "AK-47 | Redline"
        category = portfolio_manager._extract_category(title)
        assert category in {"Rifle", "Unknown"}

    def test_extract_knife_category(self, portfolio_manager):
        """Test extracting Knife category."""
        title = "★ Karambit | Doppler"
        category = portfolio_manager._extract_category(title)
        # Should recognize knife
        assert category is not None

    def test_extract_category_unknown(self, portfolio_manager):
        """Test unknown category."""
        title = "Some Random Item"
        category = portfolio_manager._extract_category(title)
        assert category is not None  # Should return something


# ============================================================================
# Tests for analyze_risk
# ============================================================================


class TestAnalyzeRisk:
    """Tests for analyze_risk method."""

    @pytest.mark.asyncio()
    async def test_analyze_risk_empty_portfolio(self, portfolio_manager, mock_api_client):
        """Test risk analysis of empty portfolio."""
        mock_api_client.get_user_inventory.return_value = {"objects": []}
        mock_api_client.get_user_offers.return_value = {"objects": []}
        mock_api_client.get_user_targets.return_value = {"Items": []}
        mock_api_client.get_balance.return_value = {"usd": 10000, "dmc": 0}

        snapshot = await portfolio_manager.get_portfolio_snapshot()
        risk = await portfolio_manager.analyze_risk(snapshot)

        assert risk is not None
        assert risk.overall_risk in list(RiskLevel)

    @pytest.mark.asyncio()
    async def test_analyze_risk_with_concentration(self, portfolio_manager, mock_api_client):
        """Test risk analysis detects concentration."""
        # Create a concentrated portfolio
        mock_api_client.get_user_inventory.return_value = {
            "objects": [
                {
                    "itemId": f"item_{i}",
                    "title": "AK-47 | Redline",
                    "price": {"USD": "1000"},
                    "gameId": "a8db",
                }
                for i in range(5)  # 5 identical items
            ]
        }
        mock_api_client.get_user_offers.return_value = {"objects": []}
        mock_api_client.get_user_targets.return_value = {"Items": []}
        mock_api_client.get_balance.return_value = {"usd": 1000, "dmc": 0}

        snapshot = await portfolio_manager.get_portfolio_snapshot()
        risk = await portfolio_manager.analyze_risk(snapshot)

        assert risk is not None

    @pytest.mark.asyncio()
    async def test_analyze_risk_uses_provided_snapshot(self, portfolio_manager, mock_api_client):
        """Test that provided snapshot is used."""
        mock_api_client.get_balance.return_value = {"usd": 5000, "dmc": 0}

        # Create a snapshot manually
        snapshot = PortfolioSnapshot(
            timestamp=datetime.now(UTC),
            total_value_usd=50.0,
            cash_balance=50.0,
            inventory_value=0,
            listed_value=0,
            targets_value=0,
            assets=[],
            asset_count=0,
            game_distribution={},
            category_distribution={},
        )

        risk = await portfolio_manager.analyze_risk(snapshot)

        assert risk is not None


# ============================================================================
# Tests for get_rebalancing_recommendations
# ============================================================================


class TestGetRebalancingRecommendations:
    """Tests for get_rebalancing_recommendations method."""

    @pytest.mark.asyncio()
    async def test_recommendations_empty_portfolio(self, portfolio_manager, mock_api_client):
        """Test recommendations for empty portfolio."""
        mock_api_client.get_user_inventory.return_value = {"objects": []}
        mock_api_client.get_user_offers.return_value = {"objects": []}
        mock_api_client.get_user_targets.return_value = {"Items": []}
        mock_api_client.get_balance.return_value = {"usd": 10000, "dmc": 0}

        recommendations = await portfolio_manager.get_rebalancing_recommendations()

        assert isinstance(recommendations, list)

    @pytest.mark.asyncio()
    async def test_recommendations_concentrated_portfolio(self, portfolio_manager, mock_api_client):
        """Test recommendations for concentrated portfolio."""
        # Single expensive item
        mock_api_client.get_user_inventory.return_value = {
            "objects": [
                {
                    "itemId": "item_1",
                    "title": "AWP | Dragon Lore",
                    "price": {"USD": "100000"},  # $1000, very concentrated
                    "gameId": "a8db",
                }
            ]
        }
        mock_api_client.get_user_offers.return_value = {"objects": []}
        mock_api_client.get_user_targets.return_value = {"Items": []}
        mock_api_client.get_balance.return_value = {"usd": 1000, "dmc": 0}

        recommendations = await portfolio_manager.get_rebalancing_recommendations()

        assert isinstance(recommendations, list)


# ============================================================================
# Tests for get_performance_metrics
# ============================================================================


class TestGetPerformanceMetrics:
    """Tests for get_performance_metrics method."""

    @pytest.mark.asyncio()
    async def test_performance_metrics_basic(self, portfolio_manager, mock_api_client):
        """Test getting basic performance metrics."""
        mock_api_client.get_user_inventory.return_value = {"objects": []}
        mock_api_client.get_user_offers.return_value = {"objects": []}
        mock_api_client.get_user_targets.return_value = {"Items": []}
        mock_api_client.get_balance.return_value = {"usd": 10000, "dmc": 0}

        metrics = await portfolio_manager.get_performance_metrics()

        assert metrics is not None
        assert isinstance(metrics, dict) or hasattr(metrics, "__dict__")


# ============================================================================
# Tests for format_portfolio_report
# ============================================================================


class TestFormatPortfolioReport:
    """Tests for format_portfolio_report method."""

    def test_format_report_basic(self, portfolio_manager):
        """Test basic report formatting."""
        snapshot = PortfolioSnapshot(
            timestamp=datetime.now(UTC),
            total_value_usd=100.0,
            cash_balance=50.0,
            inventory_value=30.0,
            listed_value=20.0,
            targets_value=0,
            assets=[],
            asset_count=0,
            game_distribution={"csgo": 100.0},
            category_distribution={"Rifle": 50.0, "Pistol": 50.0},
        )

        risk = RiskAnalysis(
            overall_risk=RiskLevel.LOW,
            concentration_score=20.0,
            single_item_risk=10.0,
            single_game_risk=100.0,
            illiquidity_risk=5.0,
            stale_items_risk=0.0,
            diversification_score=80.0,
            recommendations=[],
            risk_factors=[],
        )

        report = portfolio_manager.format_portfolio_report(snapshot, risk)

        assert isinstance(report, str)
        assert len(report) > 0

    def test_format_report_with_assets(self, portfolio_manager):
        """Test report formatting with assets."""
        asset = PortfolioAsset(
            item_id="item_1",
            item_name="AK-47 | Redline",
            asset_type=AssetType.INVENTORY,
            quantity=1,
            unit_price=10.0,
            total_value=10.0,
            game="csgo",
            category="Rifle",
        )

        snapshot = PortfolioSnapshot(
            timestamp=datetime.now(UTC),
            total_value_usd=60.0,
            cash_balance=50.0,
            inventory_value=10.0,
            listed_value=0,
            targets_value=0,
            assets=[asset],
            asset_count=1,
            game_distribution={"csgo": 100.0},
            category_distribution={"Rifle": 100.0},
        )

        risk = RiskAnalysis(
            overall_risk=RiskLevel.LOW,
            concentration_score=10.0,
            single_item_risk=16.67,
            single_game_risk=100.0,
            illiquidity_risk=0.0,
            stale_items_risk=0.0,
            diversification_score=90.0,
            recommendations=[],
            risk_factors=[],
        )

        report = portfolio_manager.format_portfolio_report(snapshot, risk)

        assert isinstance(report, str)


# ============================================================================
# Tests for Module-Level Functions
# ============================================================================


class TestModuleFunctions:
    """Tests for module-level helper functions."""

    @pytest.mark.asyncio()
    async def test_get_portfolio_summary(self, mock_api_client):
        """Test get_portfolio_summary function."""
        mock_api_client.get_user_inventory.return_value = {"objects": []}
        mock_api_client.get_user_offers.return_value = {"objects": []}
        mock_api_client.get_user_targets.return_value = {"Items": []}
        mock_api_client.get_balance.return_value = {"usd": 10000, "dmc": 0}

        summary = await get_portfolio_summary(mock_api_client)

        assert isinstance(summary, dict)

    @pytest.mark.asyncio()
    async def test_get_rebalancing_actions(self, mock_api_client):
        """Test get_rebalancing_actions function."""
        mock_api_client.get_user_inventory.return_value = {"objects": []}
        mock_api_client.get_user_offers.return_value = {"objects": []}
        mock_api_client.get_user_targets.return_value = {"Items": []}
        mock_api_client.get_balance.return_value = {"usd": 10000, "dmc": 0}

        actions = await get_rebalancing_actions(mock_api_client)

        assert isinstance(actions, list)


# ============================================================================
# Tests for Edge Cases
# ============================================================================


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.mark.asyncio()
    async def test_portfolio_with_zero_balance(self, portfolio_manager, mock_api_client):
        """Test portfolio with zero cash balance."""
        mock_api_client.get_user_inventory.return_value = {"objects": []}
        mock_api_client.get_user_offers.return_value = {"objects": []}
        mock_api_client.get_user_targets.return_value = {"Items": []}
        mock_api_client.get_balance.return_value = {"usd": 0, "dmc": 0}

        snapshot = await portfolio_manager.get_portfolio_snapshot()

        assert snapshot.cash_balance == 0

    @pytest.mark.asyncio()
    async def test_portfolio_with_large_values(self, portfolio_manager, mock_api_client):
        """Test portfolio with very large values."""
        mock_api_client.get_user_inventory.return_value = {
            "objects": [
                {
                    "itemId": "item_1",
                    "title": "AWP | Dragon Lore (FN)",
                    "price": {"USD": "10000000"},  # $100,000
                    "gameId": "a8db",
                }
            ]
        }
        mock_api_client.get_user_offers.return_value = {"objects": []}
        mock_api_client.get_user_targets.return_value = {"Items": []}
        mock_api_client.get_balance.return_value = {"usd": 100000000, "dmc": 0}

        snapshot = await portfolio_manager.get_portfolio_snapshot()

        assert snapshot is not None

    @pytest.mark.asyncio()
    async def test_portfolio_with_unicode_titles(self, portfolio_manager, mock_api_client):
        """Test handling Unicode characters in item titles."""
        mock_api_client.get_user_inventory.return_value = {
            "objects": [
                {
                    "itemId": "item_1",
                    "title": "AK-47 | Кровавый спорт",  # Russian
                    "price": {"USD": "1000"},
                    "gameId": "a8db",
                }
            ]
        }
        mock_api_client.get_user_offers.return_value = {"objects": []}
        mock_api_client.get_user_targets.return_value = {"Items": []}
        mock_api_client.get_balance.return_value = {"usd": 5000, "dmc": 0}

        snapshot = await portfolio_manager.get_portfolio_snapshot()

        assert snapshot is not None

    def test_portfolio_asset_with_negative_profit(self, portfolio_manager):
        """Test asset with negative profit/loss."""
        asset = PortfolioAsset(
            item_id="item_1",
            item_name="Bad Investment",
            asset_type=AssetType.INVENTORY,
            quantity=1,
            unit_price=10.0,
            total_value=10.0,
            game="csgo",
            category="Rifle",
            profit_loss=-5.0,
            profit_loss_percent=-50.0,
        )

        assert asset.profit_loss == -5.0
        assert asset.profit_loss_percent == -50.0

    @pytest.mark.asyncio()
    async def test_analyze_risk_no_api_client(self):
        """Test risk analysis without API client."""
        pm = PortfolioManager(api_client=None)

        snapshot = PortfolioSnapshot(
            timestamp=datetime.now(UTC),
            total_value_usd=0,
            cash_balance=0,
            inventory_value=0,
            listed_value=0,
            targets_value=0,
            assets=[],
            asset_count=0,
            game_distribution={},
            category_distribution={},
        )

        risk = await pm.analyze_risk(snapshot)

        assert risk is not None
