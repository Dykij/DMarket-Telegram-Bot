"""Comprehensive tests for dmarket/models/market_models.py module.

This module tests Pydantic models for DMarket API v1.1.0,
including enums, price models, account models, market items,
offers, targets, and other entities.
"""


# ==================== ENUM TESTS ====================


class TestOfferStatusEnum:
    """Tests for OfferStatus enum."""

    def test_offer_status_default_value(self):
        """Test DEFAULT status value."""
        from src.dmarket.models.market_models import OfferStatus

        assert OfferStatus.DEFAULT.value == "OfferStatusDefault"

    def test_offer_status_active_value(self):
        """Test ACTIVE status value."""
        from src.dmarket.models.market_models import OfferStatus

        assert OfferStatus.ACTIVE.value == "OfferStatusActive"

    def test_offer_status_sold_value(self):
        """Test SOLD status value."""
        from src.dmarket.models.market_models import OfferStatus

        assert OfferStatus.SOLD.value == "OfferStatusSold"

    def test_offer_status_inactive_value(self):
        """Test INACTIVE status value."""
        from src.dmarket.models.market_models import OfferStatus

        assert OfferStatus.INACTIVE.value == "OfferStatusInactive"

    def test_offer_status_in_transfer_value(self):
        """Test IN_TRANSFER status value."""
        from src.dmarket.models.market_models import OfferStatus

        assert OfferStatus.IN_TRANSFER.value == "OfferStatusIn_transfer"

    def test_offer_status_is_string_enum(self):
        """Test that OfferStatus inherits from str."""
        from src.dmarket.models.market_models import OfferStatus

        assert isinstance(OfferStatus.ACTIVE, str)
        assert OfferStatus.ACTIVE == "OfferStatusActive"


class TestTargetStatusEnum:
    """Tests for TargetStatus enum."""

    def test_target_status_active_value(self):
        """Test ACTIVE status value."""
        from src.dmarket.models.market_models import TargetStatus

        assert TargetStatus.ACTIVE.value == "TargetStatusActive"

    def test_target_status_inactive_value(self):
        """Test INACTIVE status value."""
        from src.dmarket.models.market_models import TargetStatus

        assert TargetStatus.INACTIVE.value == "TargetStatusInactive"


class TestTransferStatusEnum:
    """Tests for TransferStatus enum."""

    def test_transfer_status_pending_value(self):
        """Test PENDING status value."""
        from src.dmarket.models.market_models import TransferStatus

        assert TransferStatus.PENDING.value == "TransferStatusPending"

    def test_transfer_status_completed_value(self):
        """Test COMPLETED status value."""
        from src.dmarket.models.market_models import TransferStatus

        assert TransferStatus.COMPLETED.value == "TransferStatusCompleted"

    def test_transfer_status_failed_value(self):
        """Test FAILED status value."""
        from src.dmarket.models.market_models import TransferStatus

        assert TransferStatus.FAILED.value == "TransferStatusFailed"


class TestTradeStatusEnum:
    """Tests for TradeStatus enum."""

    def test_trade_status_successful_value(self):
        """Test SUCCESSFUL status value."""
        from src.dmarket.models.market_models import TradeStatus

        assert TradeStatus.SUCCESSFUL.value == "successful"

    def test_trade_status_reverted_value(self):
        """Test REVERTED status value."""
        from src.dmarket.models.market_models import TradeStatus

        assert TradeStatus.REVERTED.value == "reverted"

    def test_trade_status_trade_protected_value(self):
        """Test TRADE_PROTECTED status value."""
        from src.dmarket.models.market_models import TradeStatus

        assert TradeStatus.TRADE_PROTECTED.value == "trade_protected"


# ==================== PRICE MODELS TESTS ====================


class TestPriceModel:
    """Tests for Price model."""

    def test_price_creation_with_defaults(self):
        """Test creating Price with default currency."""
        from src.dmarket.models.market_models import Price

        price = Price(Amount=1000)

        assert price.Amount == 1000
        assert price.Currency == "USD"

    def test_price_creation_with_custom_currency(self):
        """Test creating Price with custom currency."""
        from src.dmarket.models.market_models import Price

        price = Price(Currency="EUR", Amount=2000)

        assert price.Amount == 2000
        assert price.Currency == "EUR"

    def test_price_dollars_property(self):
        """Test dollars property conversion."""
        from src.dmarket.models.market_models import Price

        price = Price(Amount=1234)

        assert price.dollars == 12.34

    def test_price_dollars_property_zero(self):
        """Test dollars property with zero amount."""
        from src.dmarket.models.market_models import Price

        price = Price(Amount=0)

        assert price.dollars == 0.0

    def test_price_from_dollars_classmethod(self):
        """Test from_dollars classmethod."""
        from src.dmarket.models.market_models import Price

        price = Price.from_dollars(12.34)

        assert price.Amount == 1234
        assert price.Currency == "USD"

    def test_price_from_dollars_with_custom_currency(self):
        """Test from_dollars with custom currency."""
        from src.dmarket.models.market_models import Price

        price = Price.from_dollars(50.00, currency="EUR")

        assert price.Amount == 5000
        assert price.Currency == "EUR"

    def test_price_from_dollars_rounding(self):
        """Test from_dollars handles floating point rounding."""
        from src.dmarket.models.market_models import Price

        price = Price.from_dollars(10.99)

        assert price.Amount == 1099


class TestMarketPriceModel:
    """Tests for MarketPrice model."""

    def test_market_price_creation(self):
        """Test creating MarketPrice."""
        from src.dmarket.models.market_models import MarketPrice

        price = MarketPrice(USD="1234")

        assert price.USD == "1234"
        assert price.EUR is None

    def test_market_price_with_eur(self):
        """Test MarketPrice with EUR."""
        from src.dmarket.models.market_models import MarketPrice

        price = MarketPrice(USD="1234", EUR="1100")

        assert price.USD == "1234"
        assert price.EUR == "1100"


# ==================== ACCOUNT MODELS TESTS ====================


class TestBalanceModel:
    """Tests for Balance model."""

    def test_balance_creation(self):
        """Test creating Balance with string values."""
        from src.dmarket.models.market_models import Balance

        balance = Balance(usd="10000", usdAvailableToWithdraw="8000")

        assert balance.usd == "10000"
        assert balance.usdAvailableToWithdraw == "8000"

    def test_balance_creation_with_int_values(self):
        """Test creating Balance with int values."""
        from src.dmarket.models.market_models import Balance

        balance = Balance(usd=10000, usdAvailableToWithdraw=8000)

        assert balance.usd == 10000
        assert balance.usdAvailableToWithdraw == 8000

    def test_balance_usd_dollars_property_string(self):
        """Test usd_dollars property with string value."""
        from src.dmarket.models.market_models import Balance

        balance = Balance(usd="10000", usdAvailableToWithdraw="8000")

        assert balance.usd_dollars == 100.0

    def test_balance_usd_dollars_property_int(self):
        """Test usd_dollars property with int value."""
        from src.dmarket.models.market_models import Balance

        balance = Balance(usd=10000, usdAvailableToWithdraw=8000)

        assert balance.usd_dollars == 100.0

    def test_balance_available_usd_dollars_property(self):
        """Test available_usd_dollars property."""
        from src.dmarket.models.market_models import Balance

        balance = Balance(usd="10000", usdAvailableToWithdraw="8000")

        assert balance.available_usd_dollars == 80.0

    def test_balance_usd_dollars_invalid_value(self):
        """Test usd_dollars with invalid value returns 0."""
        from src.dmarket.models.market_models import Balance

        balance = Balance(usd="invalid", usdAvailableToWithdraw="8000")

        assert balance.usd_dollars == 0.0

    def test_balance_with_dmc(self):
        """Test Balance with DMC values."""
        from src.dmarket.models.market_models import Balance

        balance = Balance(
            usd="10000",
            usdAvailableToWithdraw="8000",
            dmc="500",
            dmcAvailableToWithdraw="400"
        )

        assert balance.dmc == "500"
        assert balance.dmcAvailableToWithdraw == "400"


class TestUserProfileModel:
    """Tests for UserProfile model."""

    def test_user_profile_creation(self):
        """Test creating UserProfile."""
        from src.dmarket.models.market_models import UserProfile

        profile = UserProfile(
            id="user123",
            username="testuser",
            email="test@example.com",
            isEmailVerified=True
        )

        assert profile.id == "user123"
        assert profile.username == "testuser"
        assert profile.email == "test@example.com"
        assert profile.isEmailVerified is True

    def test_user_profile_with_optional_fields(self):
        """Test UserProfile with optional fields."""
        from src.dmarket.models.market_models import UserProfile

        profile = UserProfile(
            id="user123",
            username="testuser",
            email="test@example.com",
            isEmailVerified=False,
            countryCode="US",
            publicKey="pubkey123"
        )

        assert profile.countryCode == "US"
        assert profile.publicKey == "pubkey123"


# ==================== MARKET ITEM MODELS TESTS ====================


class TestMarketItemModel:
    """Tests for MarketItem model."""

    def test_market_item_creation(self):
        """Test creating MarketItem."""
        from src.dmarket.models.market_models import MarketItem

        item = MarketItem(
            itemId="item123",
            title="AK-47 | Redline",
            price={"USD": "1234"},
            gameId="a8db"
        )

        assert item.itemId == "item123"
        assert item.title == "AK-47 | Redline"
        assert item.gameId == "a8db"

    def test_market_item_price_usd_property_simple(self):
        """Test price_usd property with simple format."""
        from src.dmarket.models.market_models import MarketItem

        item = MarketItem(
            itemId="item123",
            title="Test Item",
            price={"USD": "12.34"},
            gameId="a8db"
        )

        assert item.price_usd == 12.34

    def test_market_item_price_usd_property_dict_format(self):
        """Test price_usd property with dict format."""
        from src.dmarket.models.market_models import MarketItem

        item = MarketItem(
            itemId="item123",
            title="Test Item",
            price={"USD": {"amount": 1234}},
            gameId="a8db"
        )

        assert item.price_usd == 12.34

    def test_market_item_price_usd_invalid(self):
        """Test price_usd with invalid value returns 0."""
        from src.dmarket.models.market_models import MarketItem

        item = MarketItem(
            itemId="item123",
            title="Test Item",
            price={"USD": "invalid"},
            gameId="a8db"
        )

        assert item.price_usd == 0.0

    def test_market_item_suggested_price_usd(self):
        """Test suggested_price_usd property."""
        from src.dmarket.models.market_models import MarketItem

        item = MarketItem(
            itemId="item123",
            title="Test Item",
            price={"USD": "1234"},
            gameId="a8db",
            suggestedPrice={"USD": "1500"}
        )

        assert item.suggested_price_usd == 15.0

    def test_market_item_suggested_price_usd_none(self):
        """Test suggested_price_usd when suggestedPrice is None."""
        from src.dmarket.models.market_models import MarketItem

        item = MarketItem(
            itemId="item123",
            title="Test Item",
            price={"USD": "1234"},
            gameId="a8db"
        )

        assert item.suggested_price_usd == 0.0

    def test_market_item_from_dict(self):
        """Test from_dict classmethod."""
        from src.dmarket.models.market_models import MarketItem

        data = {
            "itemId": "item456",
            "title": "AWP | Dragon Lore",
            "price": {"USD": "100000"},
            "gameId": "a8db"
        }

        item = MarketItem.from_dict(data)

        assert item.itemId == "item456"
        assert item.title == "AWP | Dragon Lore"

    def test_market_item_with_all_fields(self):
        """Test MarketItem with all optional fields."""
        from src.dmarket.models.market_models import MarketItem

        item = MarketItem(
            itemId="item123",
            title="Test Item",
            price={"USD": "1000"},
            gameId="a8db",
            image="https://example.com/image.png",
            categoryPath="Rifles/AK-47",
            tradable=True,
            type="weapon",
            tags=["rare", "special"],
            extra={"exterior": "Factory New"}
        )

        assert item.image == "https://example.com/image.png"
        assert item.categoryPath == "Rifles/AK-47"
        assert item.tradable is True
        assert item.type == "weapon"
        assert item.tags == ["rare", "special"]
        assert item.extra == {"exterior": "Factory New"}


class TestMarketItemsResponseModel:
    """Tests for MarketItemsResponse model."""

    def test_market_items_response_creation(self):
        """Test creating MarketItemsResponse."""
        from src.dmarket.models.market_models import MarketItem, MarketItemsResponse

        items = [
            MarketItem(itemId="1", title="Item 1", price={"USD": "100"}, gameId="a8db"),
            MarketItem(itemId="2", title="Item 2", price={"USD": "200"}, gameId="a8db")
        ]

        response = MarketItemsResponse(objects=items, total=2)

        assert len(response.objects) == 2
        assert response.total == 2
        assert response.cursor is None

    def test_market_items_response_with_cursor(self):
        """Test MarketItemsResponse with pagination cursor."""
        from src.dmarket.models.market_models import MarketItemsResponse

        response = MarketItemsResponse(objects=[], total=100, cursor="next_page_cursor")

        assert response.cursor == "next_page_cursor"


# ==================== OFFER MODELS TESTS ====================


class TestOfferModel:
    """Tests for Offer model."""

    def test_offer_creation(self):
        """Test creating Offer."""
        from src.dmarket.models.market_models import Offer

        offer = Offer(
            OfferID="offer123",
            AssetID="asset456",
            Title="Test Offer",
            GameID="a8db",
            price={"USD": "1000"},
            status="OfferStatusActive"
        )

        assert offer.OfferID == "offer123"
        assert offer.AssetID == "asset456"
        assert offer.Title == "Test Offer"
        assert offer.status == "OfferStatusActive"


# ==================== TARGET MODELS TESTS ====================


class TestTargetAttrsModel:
    """Tests for TargetAttrs model."""

    def test_target_attrs_creation(self):
        """Test creating TargetAttrs."""
        from src.dmarket.models.market_models import TargetAttrs

        attrs = TargetAttrs(
            paintSeed=123,
            phase="Phase 2",
            floatPartValue="0.01"
        )

        assert attrs.paintSeed == 123
        assert attrs.phase == "Phase 2"
        assert attrs.floatPartValue == "0.01"

    def test_target_attrs_empty(self):
        """Test TargetAttrs with no values."""
        from src.dmarket.models.market_models import TargetAttrs

        attrs = TargetAttrs()

        assert attrs.paintSeed is None
        assert attrs.phase is None
        assert attrs.floatPartValue is None


class TestTargetModel:
    """Tests for Target model."""

    def test_target_creation(self):
        """Test creating Target."""
        from src.dmarket.models.market_models import Target

        target = Target(
            Title="AK-47 | Redline",
            Amount="5",
            price={"USD": "1000"}
        )

        assert target.Title == "AK-47 | Redline"
        assert target.Amount == "5"
        assert target.TargetID is None

    def test_target_with_attrs(self):
        """Test Target with attributes."""
        from src.dmarket.models.market_models import Target, TargetAttrs

        attrs = TargetAttrs(floatPartValue="0.15")
        target = Target(
            TargetID="target123",
            Title="M4A4 | Howl",
            Amount="1",
            price={"USD": "5000000"},
            Attrs=attrs,
            status="TargetStatusActive"
        )

        assert target.TargetID == "target123"
        assert target.Attrs.floatPartValue == "0.15"
        assert target.status == "TargetStatusActive"


class TestCreateTargetRequestModel:
    """Tests for CreateTargetRequest model."""

    def test_create_target_request(self):
        """Test creating CreateTargetRequest."""
        from src.dmarket.models.market_models import CreateTargetRequest, Target

        targets = [
            Target(Title="Item 1", Amount="1", price={"USD": "100"}),
            Target(Title="Item 2", Amount="2", price={"USD": "200"})
        ]

        request = CreateTargetRequest(GameID="a8db", Targets=targets)

        assert request.GameID == "a8db"
        assert len(request.Targets) == 2


# ==================== AGGREGATED PRICES MODELS TESTS ====================


class TestAggregatedPriceModel:
    """Tests for AggregatedPrice model."""

    def test_aggregated_price_creation(self):
        """Test creating AggregatedPrice."""
        from src.dmarket.models.market_models import AggregatedPrice

        agg = AggregatedPrice(
            title="Test Item",
            orderBestPrice="900",
            orderCount=10,
            offerBestPrice="1000",
            offerCount=5
        )

        assert agg.title == "Test Item"
        assert agg.orderBestPrice == "900"
        assert agg.offerBestPrice == "1000"

    def test_aggregated_price_order_price_usd(self):
        """Test order_price_usd property."""
        from src.dmarket.models.market_models import AggregatedPrice

        agg = AggregatedPrice(
            title="Test",
            orderBestPrice="900",
            orderCount=10,
            offerBestPrice="1000",
            offerCount=5
        )

        assert agg.order_price_usd == 9.0

    def test_aggregated_price_offer_price_usd(self):
        """Test offer_price_usd property."""
        from src.dmarket.models.market_models import AggregatedPrice

        agg = AggregatedPrice(
            title="Test",
            orderBestPrice="900",
            orderCount=10,
            offerBestPrice="1000",
            offerCount=5
        )

        assert agg.offer_price_usd == 10.0

    def test_aggregated_price_spread_usd(self):
        """Test spread_usd property."""
        from src.dmarket.models.market_models import AggregatedPrice

        agg = AggregatedPrice(
            title="Test",
            orderBestPrice="900",
            orderCount=10,
            offerBestPrice="1000",
            offerCount=5
        )

        assert agg.spread_usd == 1.0

    def test_aggregated_price_spread_percent(self):
        """Test spread_percent property."""
        from src.dmarket.models.market_models import AggregatedPrice

        agg = AggregatedPrice(
            title="Test",
            orderBestPrice="900",
            orderCount=10,
            offerBestPrice="1000",
            offerCount=5
        )

        assert abs(agg.spread_percent - 11.11) < 0.1

    def test_aggregated_price_spread_percent_zero_order(self):
        """Test spread_percent when order price is zero."""
        from src.dmarket.models.market_models import AggregatedPrice

        agg = AggregatedPrice(
            title="Test",
            orderBestPrice="0",
            orderCount=0,
            offerBestPrice="1000",
            offerCount=5
        )

        assert agg.spread_percent == 0.0


class TestAggregatedPricesResponseModel:
    """Tests for AggregatedPricesResponse model."""

    def test_aggregated_prices_response(self):
        """Test creating AggregatedPricesResponse."""
        from src.dmarket.models.market_models import AggregatedPrice, AggregatedPricesResponse

        prices = [
            AggregatedPrice(
                title="Item 1",
                orderBestPrice="100",
                orderCount=5,
                offerBestPrice="120",
                offerCount=3
            )
        ]

        response = AggregatedPricesResponse(aggregatedPrices=prices)

        assert len(response.aggregatedPrices) == 1
        assert response.nextCursor is None


# ==================== TARGET ORDER MODELS TESTS ====================


class TestTargetOrderModel:
    """Tests for TargetOrder model."""

    def test_target_order_creation(self):
        """Test creating TargetOrder."""
        from src.dmarket.models.market_models import TargetOrder

        order = TargetOrder(
            amount=5,
            price="1000",
            title="Test Item"
        )

        assert order.amount == 5
        assert order.price == "1000"
        assert order.title == "Test Item"

    def test_target_order_price_usd(self):
        """Test price_usd property."""
        from src.dmarket.models.market_models import TargetOrder

        order = TargetOrder(amount=5, price="1234", title="Test")

        assert order.price_usd == 12.34

    def test_target_order_price_usd_invalid(self):
        """Test price_usd with invalid value."""
        from src.dmarket.models.market_models import TargetOrder

        order = TargetOrder(amount=5, price="invalid", title="Test")

        assert order.price_usd == 0.0

    def test_target_order_with_attributes(self):
        """Test TargetOrder with attributes."""
        from src.dmarket.models.market_models import TargetOrder

        order = TargetOrder(
            amount=1,
            price="50000",
            title="Karambit",
            attributes={"phase": "Ruby", "exterior": "Factory New"}
        )

        assert order.attributes["phase"] == "Ruby"


# ==================== OFFER BY TITLE MODELS TESTS ====================


class TestOfferByTitleModel:
    """Tests for OfferByTitle model."""

    def test_offer_by_title_creation(self):
        """Test creating OfferByTitle."""
        from src.dmarket.models.market_models import MarketPrice, OfferByTitle

        offer = OfferByTitle(
            offerId="offer123",
            price=MarketPrice(USD="1234"),
            title="Test Item"
        )

        assert offer.offerId == "offer123"
        assert offer.title == "Test Item"

    def test_offer_by_title_price_usd_float(self):
        """Test price_usd_float property."""
        from src.dmarket.models.market_models import MarketPrice, OfferByTitle

        offer = OfferByTitle(
            offerId="offer123",
            price=MarketPrice(USD="1234"),
            title="Test Item"
        )

        assert offer.price_usd_float == 12.34

    def test_offer_by_title_price_usd_float_invalid(self):
        """Test price_usd_float with invalid value."""
        from src.dmarket.models.market_models import MarketPrice, OfferByTitle

        offer = OfferByTitle(
            offerId="offer123",
            price=MarketPrice(USD="invalid"),
            title="Test Item"
        )

        assert offer.price_usd_float == 0.0


# ==================== INVENTORY MODELS TESTS ====================


class TestInventoryItemModel:
    """Tests for InventoryItem model."""

    def test_inventory_item_creation(self):
        """Test creating InventoryItem."""
        from src.dmarket.models.market_models import InventoryItem

        item = InventoryItem(
            ItemID="item123",
            AssetID="asset456",
            Title="Test Item",
            GameID="a8db"
        )

        assert item.ItemID == "item123"
        assert item.AssetID == "asset456"
        assert item.InMarket is False
        assert item.Withdrawable is True
        assert item.Tradable is True

    def test_inventory_item_with_price(self):
        """Test InventoryItem with price."""
        from src.dmarket.models.market_models import InventoryItem, Price

        item = InventoryItem(
            ItemID="item123",
            AssetID="asset456",
            Title="Test Item",
            GameID="a8db",
            Price=Price(Amount=1000),
            InMarket=True
        )

        assert item.Price.Amount == 1000
        assert item.InMarket is True


class TestUserInventoryResponseModel:
    """Tests for UserInventoryResponse model."""

    def test_user_inventory_response(self):
        """Test creating UserInventoryResponse."""
        from src.dmarket.models.market_models import InventoryItem, UserInventoryResponse

        items = [
            InventoryItem(ItemID="1", AssetID="a1", Title="Item 1", GameID="a8db")
        ]

        response = UserInventoryResponse(Items=items, Total="1")

        assert len(response.Items) == 1
        assert response.Total == "1"


# ==================== TRANSACTION MODELS TESTS ====================


class TestBuyItemResponseModel:
    """Tests for BuyItemResponse model."""

    def test_buy_item_response(self):
        """Test creating BuyItemResponse."""
        from src.dmarket.models.market_models import BuyItemResponse

        response = BuyItemResponse(
            orderId="order123",
            status="success",
            txId="tx456"
        )

        assert response.orderId == "order123"
        assert response.status == "success"
        assert response.txId == "tx456"


class TestCreateOfferResponseModel:
    """Tests for CreateOfferResponse model."""

    def test_create_offer_response(self):
        """Test creating CreateOfferResponse."""
        from src.dmarket.models.market_models import CreateOfferResponse

        response = CreateOfferResponse(
            Result=[{"OfferId": "offer1", "Status": "Created"}]
        )

        assert len(response.Result) == 1


# ==================== SALES HISTORY MODELS TESTS ====================


class TestSalesHistoryModel:
    """Tests for SalesHistory model."""

    def test_sales_history_creation(self):
        """Test creating SalesHistory."""
        from src.dmarket.models.market_models import SalesHistory

        sale = SalesHistory(
            price="1234",
            date="2024-01-15T12:00:00Z"
        )

        assert sale.price == "1234"
        assert sale.date == "2024-01-15T12:00:00Z"

    def test_sales_history_price_float(self):
        """Test price_float property."""
        from src.dmarket.models.market_models import SalesHistory

        sale = SalesHistory(price="1234", date="2024-01-15T12:00:00")

        assert sale.price_float == 12.34

    def test_sales_history_price_float_invalid(self):
        """Test price_float with invalid value."""
        from src.dmarket.models.market_models import SalesHistory

        sale = SalesHistory(price="invalid", date="2024-01-15T12:00:00")

        assert sale.price_float == 0.0

    def test_sales_history_date_datetime(self):
        """Test date_datetime property."""
        from src.dmarket.models.market_models import SalesHistory

        sale = SalesHistory(price="1000", date="2024-01-15T12:00:00")

        dt = sale.date_datetime
        assert dt is not None
        assert dt.year == 2024
        assert dt.month == 1
        assert dt.day == 15

    def test_sales_history_date_datetime_invalid(self):
        """Test date_datetime with invalid date."""
        from src.dmarket.models.market_models import SalesHistory

        sale = SalesHistory(price="1000", date="invalid")

        assert sale.date_datetime is None

    def test_sales_history_from_dict(self):
        """Test from_dict classmethod."""
        from src.dmarket.models.market_models import SalesHistory

        data = {
            "price": "5000",
            "date": "2024-02-01T10:30:00",
            "txOperationType": "BUY"
        }

        sale = SalesHistory.from_dict(data)

        assert sale.price == "5000"
        assert sale.txOperationType == "BUY"


# ==================== DEPOSIT MODELS TESTS ====================


class TestDepositAssetModel:
    """Tests for DepositAsset model."""

    def test_deposit_asset_creation(self):
        """Test creating DepositAsset."""
        from src.dmarket.models.market_models import DepositAsset

        asset = DepositAsset(
            InGameAssetID="ingame123",
            DmarketAssetID="dmarket456"
        )

        assert asset.InGameAssetID == "ingame123"
        assert asset.DmarketAssetID == "dmarket456"


class TestDepositStatusModel:
    """Tests for DepositStatus model."""

    def test_deposit_status_creation(self):
        """Test creating DepositStatus."""
        from src.dmarket.models.market_models import DepositStatus, TransferStatus

        status = DepositStatus(
            DepositID="deposit123",
            AssetID=["asset1", "asset2"],
            status=TransferStatus.PENDING
        )

        assert status.DepositID == "deposit123"
        assert len(status.AssetID) == 2
        assert status.status == TransferStatus.PENDING


# ==================== LEGACY MODELS TESTS ====================


class TestBalanceLegacyModel:
    """Tests for BalanceLegacy dataclass."""

    def test_balance_legacy_creation(self):
        """Test creating BalanceLegacy."""
        from src.dmarket.models.market_models import BalanceLegacy

        balance = BalanceLegacy(totalBalance=100.0, blockedBalance=20.0)

        assert balance.totalBalance == 100.0
        assert balance.blockedBalance == 20.0

    def test_balance_legacy_from_dict(self):
        """Test from_dict classmethod."""
        from src.dmarket.models.market_models import BalanceLegacy

        data = {"totalBalance": 50.0, "blockedBalance": 10.0}

        balance = BalanceLegacy.from_dict(data)

        assert balance.totalBalance == 50.0
        assert balance.blockedBalance == 10.0

    def test_balance_legacy_from_dict_missing_keys(self):
        """Test from_dict with missing keys uses defaults."""
        from src.dmarket.models.market_models import BalanceLegacy

        data = {}

        balance = BalanceLegacy.from_dict(data)

        assert balance.totalBalance == 0.0
        assert balance.blockedBalance == 0.0


# ==================== MODULE EXPORTS TESTS ====================


class TestModuleExports:
    """Tests for module __all__ exports."""

    def test_all_exports_are_importable(self):
        """Test that all exports in __all__ are importable."""
        from src.dmarket.models import market_models

        for name in market_models.__all__:
            assert hasattr(market_models, name), f"{name} not found in module"

    def test_price_model_alias(self):
        """Test PriceModel is alias for Price."""
        from src.dmarket.models.market_models import Price, PriceModel

        # PriceModel should be the same class as Price
        assert Price is PriceModel


# ==================== EDGE CASES TESTS ====================


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_price_with_large_amount(self):
        """Test Price with very large amount."""
        from src.dmarket.models.market_models import Price

        price = Price(Amount=999999999)

        assert price.dollars == 9999999.99

    def test_price_with_negative_amount(self):
        """Test Price handles negative amount."""
        from src.dmarket.models.market_models import Price

        price = Price(Amount=-1000)

        assert price.dollars == -10.0

    def test_market_item_empty_price_dict(self):
        """Test MarketItem with empty price dict."""
        from src.dmarket.models.market_models import MarketItem

        item = MarketItem(
            itemId="item123",
            title="Test",
            price={},
            gameId="a8db"
        )

        assert item.price_usd == 0.0

    def test_unicode_in_title(self):
        """Test models handle unicode in titles."""
        from src.dmarket.models.market_models import MarketItem

        item = MarketItem(
            itemId="item123",
            title="АК-47 | Рулон",  # Russian text
            price={"USD": "1000"},
            gameId="a8db"
        )

        assert "АК-47" in item.title
