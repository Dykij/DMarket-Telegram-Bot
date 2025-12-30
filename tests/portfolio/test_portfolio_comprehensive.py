"""Comprehensive tests for portfolio manager and analyzer.

Coverage improvement tests for:
- PortfolioManager async methods (sync_with_inventory, update_prices)
- PortfolioManager detection methods (_detect_category)
- PortfolioManager persistence (_load_portfolios, _save_portfolios)
- PortfolioAnalyzer edge cases and private methods
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.portfolio.analyzer import (
    ConcentrationRisk,
    DiversificationReport,
    PortfolioAnalyzer,
    RiskReport,
)
from src.portfolio.manager import PortfolioManager
from src.portfolio.models import (
    ItemCategory,
    ItemRarity,
    Portfolio,
    PortfolioItem,
)


if TYPE_CHECKING:
    from pathlib import Path


class TestPortfolioManagerSetAPI:
    """Tests for PortfolioManager.set_api method."""

    def test_set_api(self, tmp_path: Path) -> None:
        """Test setting API client."""
        storage_path = tmp_path / "portfolios.json"
        manager = PortfolioManager(api=None, storage_path=storage_path)

        mock_api = MagicMock()
        manager.set_api(mock_api)

        assert manager.api is mock_api


class TestPortfolioManagerGetItems:
    """Tests for PortfolioManager.get_items method."""

    @pytest.fixture()
    def manager_with_items(self, tmp_path: Path) -> PortfolioManager:
        """Create manager with test items."""
        storage_path = tmp_path / "portfolios.json"
        manager = PortfolioManager(api=None, storage_path=storage_path)

        # Add items from different games and categories
        manager.add_item(
            user_id=123,
            item_id="csgo_ak",
            title="AK-47 | Redline",
            game="csgo",
            buy_price=25.00,
            category="weapon",
        )
        manager.add_item(
            user_id=123,
            item_id="csgo_knife",
            title="Karambit | Fade",
            game="csgo",
            buy_price=500.00,
            category="knife",
        )
        manager.add_item(
            user_id=123,
            item_id="dota_item",
            title="Dragon Claw Hook",
            game="dota2",
            buy_price=200.00,
            category="other",
        )

        return manager

    def test_get_items_all(self, manager_with_items: PortfolioManager) -> None:
        """Test getting all items."""
        items = manager_with_items.get_items(user_id=123)
        assert len(items) == 3

    def test_get_items_by_game(self, manager_with_items: PortfolioManager) -> None:
        """Test filtering by game."""
        items = manager_with_items.get_items(user_id=123, game="csgo")
        assert len(items) == 2
        assert all(item.game == "csgo" for item in items)

    def test_get_items_by_category(self, manager_with_items: PortfolioManager) -> None:
        """Test filtering by category."""
        items = manager_with_items.get_items(user_id=123, category="weapon")
        assert len(items) == 1
        assert items[0].category == ItemCategory.WEAPON

    def test_get_items_by_game_and_category(self, manager_with_items: PortfolioManager) -> None:
        """Test filtering by both game and category."""
        items = manager_with_items.get_items(user_id=123, game="csgo", category="knife")
        assert len(items) == 1
        assert items[0].title == "Karambit | Fade"


class TestPortfolioManagerTakeSnapshot:
    """Tests for PortfolioManager.take_snapshot method."""

    def test_take_snapshot(self, tmp_path: Path) -> None:
        """Test taking a portfolio snapshot."""
        storage_path = tmp_path / "portfolios.json"
        manager = PortfolioManager(api=None, storage_path=storage_path)

        manager.add_item(
            user_id=123,
            item_id="test",
            title="Test Item",
            game="csgo",
            buy_price=10.00,
        )

        manager.take_snapshot(user_id=123)

        portfolio = manager.get_portfolio(123)
        assert len(portfolio.snapshots) == 1


class TestPortfolioManagerDetectCategory:
    """Tests for PortfolioManager._detect_category method."""

    @pytest.fixture()
    def manager(self, tmp_path: Path) -> PortfolioManager:
        """Create manager instance."""
        storage_path = tmp_path / "portfolios.json"
        return PortfolioManager(api=None, storage_path=storage_path)

    def test_detect_knife_by_star(self, manager: PortfolioManager) -> None:
        """Test detecting knife by star symbol."""
        category = manager._detect_category("★ Bayonet | Doppler")
        assert category == ItemCategory.KNIFE

    def test_detect_knife_by_word(self, manager: PortfolioManager) -> None:
        """Test detecting knife by word."""
        category = manager._detect_category("Survival Knife | Safari Mesh")
        assert category == ItemCategory.KNIFE

    def test_detect_gloves(self, manager: PortfolioManager) -> None:
        """Test detecting gloves."""
        # Gloves without star symbol - detected as gloves
        category = manager._detect_category("Sport Gloves | Pandora's Box")
        assert category == ItemCategory.GLOVES

    def test_detect_wraps(self, manager: PortfolioManager) -> None:
        """Test detecting hand wraps."""
        # Wraps without star symbol - detected as gloves
        category = manager._detect_category("Hand Wraps | Cobalt Skulls")
        assert category == ItemCategory.GLOVES

    def test_detect_case(self, manager: PortfolioManager) -> None:
        """Test detecting case."""
        category = manager._detect_category("CS20 Case")
        assert category == ItemCategory.CASE

    def test_detect_key(self, manager: PortfolioManager) -> None:
        """Test detecting key."""
        # "key" must come before "case" check in the title
        category = manager._detect_category("Operation Breakout Key")
        assert category == ItemCategory.KEY

    def test_detect_agent(self, manager: PortfolioManager) -> None:
        """Test detecting agent."""
        category = manager._detect_category("Special Agent Ava | FBI")
        assert category == ItemCategory.AGENT

    def test_detect_music_kit(self, manager: PortfolioManager) -> None:
        """Test detecting music kit."""
        category = manager._detect_category("Music Kit | AWOLNATION")
        assert category == ItemCategory.MUSIC_KIT

    def test_detect_graffiti(self, manager: PortfolioManager) -> None:
        """Test detecting graffiti."""
        category = manager._detect_category("Sealed Graffiti | NaVi")
        assert category == ItemCategory.GRAFFITI

    def test_detect_patch(self, manager: PortfolioManager) -> None:
        """Test detecting patch."""
        category = manager._detect_category("Patch | Ninjas in Pyjamas")
        assert category == ItemCategory.PATCH

    def test_detect_weapon_usp(self, manager: PortfolioManager) -> None:
        """Test detecting USP weapon."""
        category = manager._detect_category("USP-S | Cortex")
        assert category == ItemCategory.WEAPON

    def test_detect_weapon_glock(self, manager: PortfolioManager) -> None:
        """Test detecting Glock weapon."""
        category = manager._detect_category("Glock-18 | Fade")
        assert category == ItemCategory.WEAPON

    def test_detect_weapon_deagle(self, manager: PortfolioManager) -> None:
        """Test detecting Desert Eagle weapon."""
        # Must use exact match for "deagle" not "Desert Eagle"
        category = manager._detect_category("Deagle | Blaze")
        assert category == ItemCategory.WEAPON

    def test_detect_weapon_m4a1(self, manager: PortfolioManager) -> None:
        """Test detecting M4A1-S weapon."""
        category = manager._detect_category("M4A1-S | Hyper Beast")
        assert category == ItemCategory.WEAPON

    def test_detect_other(self, manager: PortfolioManager) -> None:
        """Test detecting other category."""
        category = manager._detect_category("Some Random Item")
        assert category == ItemCategory.OTHER


class TestPortfolioManagerPersistence:
    """Tests for PortfolioManager persistence methods."""

    def test_save_and_load_portfolios(self, tmp_path: Path) -> None:
        """Test saving and loading portfolios."""
        storage_path = tmp_path / "portfolios.json"

        # Create manager and add items
        manager1 = PortfolioManager(api=None, storage_path=storage_path)
        manager1.add_item(
            user_id=123,
            item_id="test",
            title="Test Item",
            game="csgo",
            buy_price=10.00,
        )

        # Create new manager that loads from file
        manager2 = PortfolioManager(api=None, storage_path=storage_path)

        portfolio = manager2.get_portfolio(123)
        assert len(portfolio.items) == 1
        assert portfolio.items[0].title == "Test Item"

    def test_load_nonexistent_file(self, tmp_path: Path) -> None:
        """Test loading when file doesn't exist."""
        storage_path = tmp_path / "nonexistent.json"
        manager = PortfolioManager(api=None, storage_path=storage_path)

        # Should not raise, just have empty portfolios
        assert manager.get_portfolio(123).items == []

    def test_load_corrupted_file(self, tmp_path: Path) -> None:
        """Test loading corrupted JSON file."""
        storage_path = tmp_path / "corrupted.json"
        storage_path.write_text("not valid json{")

        # Should not raise, just log warning
        manager = PortfolioManager(api=None, storage_path=storage_path)
        assert manager.get_portfolio(123).items == []

    def test_save_creates_directory(self, tmp_path: Path) -> None:
        """Test that save creates parent directories."""
        storage_path = tmp_path / "nested" / "dir" / "portfolios.json"

        manager = PortfolioManager(api=None, storage_path=storage_path)
        manager.add_item(
            user_id=123,
            item_id="test",
            title="Test",
            game="csgo",
            buy_price=10.00,
        )

        assert storage_path.exists()


class TestPortfolioManagerSyncWithInventory:
    """Tests for PortfolioManager.sync_with_inventory method."""

    @pytest.fixture()
    def manager_with_api(self, tmp_path: Path) -> PortfolioManager:
        """Create manager with mock API."""
        storage_path = tmp_path / "portfolios.json"
        mock_api = AsyncMock()
        return PortfolioManager(api=mock_api, storage_path=storage_path)

    @pytest.mark.asyncio()
    async def test_sync_without_api(self, tmp_path: Path) -> None:
        """Test sync returns 0 when no API."""
        storage_path = tmp_path / "portfolios.json"
        manager = PortfolioManager(api=None, storage_path=storage_path)

        result = await manager.sync_with_inventory(user_id=123)

        assert result == 0

    @pytest.mark.asyncio()
    async def test_sync_empty_inventory(self, manager_with_api: PortfolioManager) -> None:
        """Test syncing empty inventory."""
        manager_with_api.api.get_user_inventory.return_value = {"objects": []}

        result = await manager_with_api.sync_with_inventory(user_id=123)

        assert result == 0

    @pytest.mark.asyncio()
    async def test_sync_with_items(self, manager_with_api: PortfolioManager) -> None:
        """Test syncing inventory with items."""
        manager_with_api.api.get_user_inventory.return_value = {
            "objects": [
                {
                    "itemId": "item1",
                    "title": "AK-47 | Redline",
                    "gameId": "csgo",
                    "price": {"USD": 2500},
                },
                {
                    "itemId": "item2",
                    "title": "AWP | Asiimov",
                    "gameId": "csgo",
                    "price": {"amount": 5000},
                },
            ]
        }

        result = await manager_with_api.sync_with_inventory(user_id=123)

        assert result == 2
        portfolio = manager_with_api.get_portfolio(123)
        assert len(portfolio.items) == 2

    @pytest.mark.asyncio()
    async def test_sync_skips_existing_items(self, manager_with_api: PortfolioManager) -> None:
        """Test that sync skips items already in portfolio."""
        # Add existing item
        manager_with_api.add_item(
            user_id=123,
            item_id="item1",
            title="AK-47 | Redline",
            game="csgo",
            buy_price=25.00,
        )

        manager_with_api.api.get_user_inventory.return_value = {
            "objects": [
                {
                    "itemId": "item1",
                    "title": "AK-47 | Redline",
                    "gameId": "csgo",
                    "price": {"USD": 2500},
                },
            ]
        }

        result = await manager_with_api.sync_with_inventory(user_id=123)

        assert result == 0

    @pytest.mark.asyncio()
    async def test_sync_handles_api_error(self, manager_with_api: PortfolioManager) -> None:
        """Test that sync handles API errors gracefully."""
        manager_with_api.api.get_user_inventory.side_effect = Exception("API Error")

        result = await manager_with_api.sync_with_inventory(user_id=123)

        assert result == 0

    @pytest.mark.asyncio()
    async def test_sync_with_offer_id(self, manager_with_api: PortfolioManager) -> None:
        """Test sync extracts item ID from extra.offerId."""
        manager_with_api.api.get_user_inventory.return_value = {
            "objects": [
                {
                    "extra": {"offerId": "offer123"},
                    "title": "Test Item",
                    "gameId": "csgo",
                    "price": {"USD": 1000},
                },
            ]
        }

        result = await manager_with_api.sync_with_inventory(user_id=123)

        assert result == 1
        portfolio = manager_with_api.get_portfolio(123)
        assert portfolio.items[0].item_id == "offer123"


class TestPortfolioManagerUpdatePrices:
    """Tests for PortfolioManager.update_prices method."""

    @pytest.fixture()
    def manager_with_items_and_api(self, tmp_path: Path) -> PortfolioManager:
        """Create manager with items and mock API."""
        storage_path = tmp_path / "portfolios.json"
        mock_api = AsyncMock()
        manager = PortfolioManager(api=mock_api, storage_path=storage_path)

        manager.add_item(
            user_id=123,
            item_id="ak",
            title="AK-47 | Redline",
            game="csgo",
            buy_price=25.00,
        )
        manager.add_item(
            user_id=123,
            item_id="awp",
            title="AWP | Asiimov",
            game="csgo",
            buy_price=50.00,
        )

        return manager

    @pytest.mark.asyncio()
    async def test_update_without_api(self, tmp_path: Path) -> None:
        """Test update returns 0 when no API."""
        storage_path = tmp_path / "portfolios.json"
        manager = PortfolioManager(api=None, storage_path=storage_path)
        manager.add_item(
            user_id=123,
            item_id="test",
            title="Test",
            game="csgo",
            buy_price=10.00,
        )

        result = await manager.update_prices(user_id=123)

        assert result == 0

    @pytest.mark.asyncio()
    async def test_update_empty_portfolio(self, tmp_path: Path) -> None:
        """Test updating empty portfolio."""
        storage_path = tmp_path / "portfolios.json"
        mock_api = AsyncMock()
        manager = PortfolioManager(api=mock_api, storage_path=storage_path)

        result = await manager.update_prices(user_id=123)

        assert result == 0
        mock_api.get_aggregated_prices_bulk.assert_not_called()

    @pytest.mark.asyncio()
    async def test_update_prices_success(self, manager_with_items_and_api: PortfolioManager) -> None:
        """Test successful price update."""
        manager_with_items_and_api.api.get_aggregated_prices_bulk.return_value = {
            "aggregatedPrices": [
                {"title": "AK-47 | Redline", "offerBestPrice": 3000},
                {"title": "AWP | Asiimov", "offerBestPrice": 6000},
            ]
        }

        result = await manager_with_items_and_api.update_prices(user_id=123)

        assert result == 2
        portfolio = manager_with_items_and_api.get_portfolio(123)
        ak = portfolio.get_item("ak")
        awp = portfolio.get_item("awp")
        assert ak.current_price == Decimal("30.00")
        assert awp.current_price == Decimal("60.00")

    @pytest.mark.asyncio()
    async def test_update_prices_handles_api_error(
        self, manager_with_items_and_api: PortfolioManager
    ) -> None:
        """Test that update handles API errors gracefully."""
        manager_with_items_and_api.api.get_aggregated_prices_bulk.side_effect = Exception("API Error")

        result = await manager_with_items_and_api.update_prices(user_id=123)

        assert result == 0

    @pytest.mark.asyncio()
    async def test_update_prices_skips_zero_price(
        self, manager_with_items_and_api: PortfolioManager
    ) -> None:
        """Test that update skips items with zero price."""
        manager_with_items_and_api.api.get_aggregated_prices_bulk.return_value = {
            "aggregatedPrices": [
                {"title": "AK-47 | Redline", "offerBestPrice": 0},
            ]
        }

        result = await manager_with_items_and_api.update_prices(user_id=123)

        # AK has 0 price, should not be updated
        assert result == 0

    @pytest.mark.asyncio()
    async def test_update_prices_multiple_games(self, tmp_path: Path) -> None:
        """Test updating prices for multiple games."""
        storage_path = tmp_path / "portfolios.json"
        mock_api = AsyncMock()
        manager = PortfolioManager(api=mock_api, storage_path=storage_path)

        # Add items from different games
        manager.add_item(
            user_id=123,
            item_id="csgo_item",
            title="AK-47",
            game="csgo",
            buy_price=25.00,
        )
        manager.add_item(
            user_id=123,
            item_id="dota_item",
            title="Dragon Claw",
            game="dota2",
            buy_price=200.00,
        )

        mock_api.get_aggregated_prices_bulk.side_effect = [
            {"aggregatedPrices": [{"title": "AK-47", "offerBestPrice": 3000}]},
            {"aggregatedPrices": [{"title": "Dragon Claw", "offerBestPrice": 25000}]},
        ]

        result = await manager.update_prices(user_id=123)

        assert result == 2


class TestPortfolioAnalyzerEdgeCases:
    """Tests for PortfolioAnalyzer edge cases."""

    @pytest.fixture()
    def analyzer(self) -> PortfolioAnalyzer:
        """Create analyzer instance."""
        return PortfolioAnalyzer()

    def test_analyze_diversification_zero_value(self, analyzer: PortfolioAnalyzer) -> None:
        """Test diversification with zero total value."""
        portfolio = Portfolio(user_id=123)
        portfolio.add_item(
            PortfolioItem(
                item_id="test",
                title="Test",
                game="csgo",
                buy_price=Decimal(0),
                current_price=Decimal(0),
            )
        )

        report = analyzer.analyze_diversification(portfolio)

        assert report.diversification_score == 0

    def test_analyze_risk_zero_value(self, analyzer: PortfolioAnalyzer) -> None:
        """Test risk analysis with zero total value."""
        portfolio = Portfolio(user_id=123)
        portfolio.add_item(
            PortfolioItem(
                item_id="test",
                title="Test",
                game="csgo",
                buy_price=Decimal(0),
                current_price=Decimal(0),
            )
        )

        report = analyzer.analyze_risk(portfolio)

        assert report.overall_risk_score == 0

    def test_analyze_risk_critical_level(self, analyzer: PortfolioAnalyzer) -> None:
        """Test risk analysis with critical risk level."""
        portfolio = Portfolio(user_id=123)
        # Single high-value item = high concentration
        portfolio.add_item(
            PortfolioItem(
                item_id="expensive",
                title="Expensive Item",
                game="csgo",
                buy_price=Decimal(1000),
                current_price=Decimal(500),  # -50% loss
                category=ItemCategory.KNIFE,
                rarity=ItemRarity.CONTRABAND,
            )
        )

        report = analyzer.analyze_risk(portfolio)

        # Single expensive item should have high risk
        assert report.risk_level in {"high", "critical"}

    def test_calculate_volatility_single_item(self, analyzer: PortfolioAnalyzer) -> None:
        """Test volatility calculation with single item."""
        portfolio = Portfolio(user_id=123)
        portfolio.add_item(
            PortfolioItem(
                item_id="test",
                title="Test",
                game="csgo",
                buy_price=Decimal(10),
                current_price=Decimal(15),  # +50% P&L
            )
        )

        volatility = analyzer._calculate_volatility_score(portfolio)

        assert volatility == 50.0  # abs(50%)

    def test_calculate_liquidity_high_value_items(self, analyzer: PortfolioAnalyzer) -> None:
        """Test liquidity with high value items."""
        portfolio = Portfolio(user_id=123)
        portfolio.add_item(
            PortfolioItem(
                item_id="expensive",
                title="Expensive Knife",
                game="csgo",
                buy_price=Decimal(200),
                current_price=Decimal(200),
            )
        )

        liquidity = analyzer._calculate_liquidity_score(portfolio)

        # High value item should reduce liquidity
        assert liquidity < 100

    def test_calculate_liquidity_rare_items(self, analyzer: PortfolioAnalyzer) -> None:
        """Test liquidity with rare items."""
        portfolio = Portfolio(user_id=123)
        portfolio.add_item(
            PortfolioItem(
                item_id="rare",
                title="Rare Item",
                game="csgo",
                buy_price=Decimal(50),
                current_price=Decimal(50),
                rarity=ItemRarity.CONTRABAND,
            )
        )

        liquidity = analyzer._calculate_liquidity_score(portfolio)

        # Rare items should reduce liquidity
        assert liquidity < 100

    def test_find_high_risk_items_large_loss(self, analyzer: PortfolioAnalyzer) -> None:
        """Test finding items with large losses."""
        portfolio = Portfolio(user_id=123)
        item = PortfolioItem(
            item_id="loser",
            title="Losing Item",
            game="csgo",
            buy_price=Decimal(100),
            current_price=Decimal(50),  # -50% loss
        )
        portfolio.add_item(item)

        high_risk = analyzer._find_high_risk_items(
            portfolio.items,
            Decimal(50),  # total value
        )

        assert any("Losing Item" in risk for risk in high_risk)

    def test_find_high_risk_items_expensive(self, analyzer: PortfolioAnalyzer) -> None:
        """Test finding expensive items."""
        portfolio = Portfolio(user_id=123)
        item = PortfolioItem(
            item_id="expensive",
            title="Very Expensive",
            game="csgo",
            buy_price=Decimal(600),
            current_price=Decimal(600),
        )
        portfolio.add_item(item)

        high_risk = analyzer._find_high_risk_items(
            portfolio.items,
            Decimal(1000),  # total value
        )

        assert any("Very Expensive" in risk for risk in high_risk)

    def test_concentration_risk_to_dict(self) -> None:
        """Test ConcentrationRisk.to_dict method."""
        risk = ConcentrationRisk(
            item_title="Test Item",
            value=Decimal(100),
            percentage=50.0,
            risk_level="high",
        )

        data = risk.to_dict()

        assert data["item_title"] == "Test Item"
        assert data["value"] == 100.0
        assert data["percentage"] == 50.0
        assert data["risk_level"] == "high"

    def test_diversification_report_to_dict(self) -> None:
        """Test DiversificationReport.to_dict method."""
        report = DiversificationReport(
            by_game={"csgo": 100.0},
            by_category={"weapon": 50.0, "knife": 50.0},
            by_rarity={"mil_spec": 100.0},
            concentration_risks=[],
            diversification_score=75.0,
            recommendations=["Test recommendation"],
        )

        data = report.to_dict()

        assert data["by_game"] == {"csgo": 100.0}
        assert data["diversification_score"] == 75.0
        assert "Test recommendation" in data["recommendations"]

    def test_risk_report_to_dict(self) -> None:
        """Test RiskReport.to_dict method."""
        report = RiskReport(
            volatility_score=30.0,
            liquidity_score=80.0,
            concentration_score=40.0,
            overall_risk_score=35.0,
            risk_level="medium",
            high_risk_items=["Item1"],
            recommendations=["Reduce concentration"],
        )

        data = report.to_dict()

        assert data["volatility_score"] == 30.0
        assert data["risk_level"] == "medium"
        assert "Item1" in data["high_risk_items"]


class TestPortfolioAnalyzerRecommendations:
    """Tests for recommendation generation."""

    @pytest.fixture()
    def analyzer(self) -> PortfolioAnalyzer:
        """Create analyzer instance."""
        return PortfolioAnalyzer()

    def test_diversification_recommendations_low_score(self, analyzer: PortfolioAnalyzer) -> None:
        """Test recommendations for low diversification score."""
        recommendations = analyzer._generate_diversification_recommendations(
            by_game={"csgo": 100.0},
            by_category={"weapon": 100.0},
            concentration_risks=[],
            score=20.0,
        )

        assert any("concentrated" in r.lower() for r in recommendations)

    def test_diversification_recommendations_single_game(self, analyzer: PortfolioAnalyzer) -> None:
        """Test recommendations for single game."""
        recommendations = analyzer._generate_diversification_recommendations(
            by_game={"csgo": 100.0},
            by_category={"weapon": 50.0, "knife": 50.0},
            concentration_risks=[],
            score=60.0,
        )

        assert any("multiple games" in r.lower() for r in recommendations)

    def test_diversification_recommendations_few_categories(self, analyzer: PortfolioAnalyzer) -> None:
        """Test recommendations for few categories."""
        recommendations = analyzer._generate_diversification_recommendations(
            by_game={"csgo": 50.0, "dota2": 50.0},
            by_category={"weapon": 100.0},
            concentration_risks=[],
            score=60.0,
        )

        assert any("categories" in r.lower() for r in recommendations)

    def test_diversification_recommendations_critical_concentration(
        self, analyzer: PortfolioAnalyzer
    ) -> None:
        """Test recommendations for critical concentration."""
        recommendations = analyzer._generate_diversification_recommendations(
            by_game={"csgo": 100.0},
            by_category={"weapon": 100.0},
            concentration_risks=[
                ConcentrationRisk(
                    item_title="Critical Item",
                    value=Decimal(1000),
                    percentage=80.0,
                    risk_level="critical",
                )
            ],
            score=40.0,
        )

        assert any("Critical" in r for r in recommendations)

    def test_diversification_recommendations_well_diversified(
        self, analyzer: PortfolioAnalyzer
    ) -> None:
        """Test recommendations for well diversified portfolio."""
        recommendations = analyzer._generate_diversification_recommendations(
            by_game={"csgo": 50.0, "dota2": 50.0},
            by_category={"weapon": 33.0, "knife": 33.0, "sticker": 34.0},
            concentration_risks=[],
            score=85.0,
        )

        assert any("well diversified" in r.lower() for r in recommendations)

    def test_risk_recommendations_high_volatility(self, analyzer: PortfolioAnalyzer) -> None:
        """Test recommendations for high volatility."""
        recommendations = analyzer._generate_risk_recommendations(
            volatility=60.0,
            liquidity=80.0,
            concentration=30.0,
            high_risk_items=[],
        )

        assert any("volatile" in r.lower() for r in recommendations)

    def test_risk_recommendations_low_liquidity(self, analyzer: PortfolioAnalyzer) -> None:
        """Test recommendations for low liquidity."""
        recommendations = analyzer._generate_risk_recommendations(
            volatility=20.0,
            liquidity=30.0,
            concentration=30.0,
            high_risk_items=[],
        )

        assert any("illiquid" in r.lower() for r in recommendations)

    def test_risk_recommendations_high_concentration(self, analyzer: PortfolioAnalyzer) -> None:
        """Test recommendations for high concentration."""
        recommendations = analyzer._generate_risk_recommendations(
            volatility=20.0,
            liquidity=80.0,
            concentration=60.0,
            high_risk_items=[],
        )

        assert any("concentration" in r.lower() for r in recommendations)

    def test_risk_recommendations_manageable(self, analyzer: PortfolioAnalyzer) -> None:
        """Test recommendations for manageable risk."""
        recommendations = analyzer._generate_risk_recommendations(
            volatility=20.0,
            liquidity=80.0,
            concentration=30.0,
            high_risk_items=[],
        )

        assert any("manageable" in r.lower() for r in recommendations)
