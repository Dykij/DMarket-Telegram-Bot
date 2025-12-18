"""Extended unit tests for Pydantic schemas module.

This module contains comprehensive tests for src/dmarket/schemas.py covering:
- PriceModel validation and conversion
- AttributesModel validation
- MarketItemModel validation
- MarketItemsResponse validation
- Target-related models
- Edge cases and error handling

Target: 30+ tests to achieve 80%+ coverage
"""

from decimal import Decimal

import pytest

from src.dmarket.schemas import (
    AttributesModel,
    CreateTargetRequest,
    CreateTargetsResponse,
    MarketItemModel,
    MarketItemsResponse,
    PriceModel,
    TargetPriceModel,
    TargetResultModel,
    UserTargetModel,
    UserTargetsResponse,
)


# TestPriceModel


class TestPriceModel:
    """Tests for PriceModel."""

    def test_price_model_with_usd(self):
        """Test PriceModel with USD price."""
        # Arrange & Act
        price = PriceModel(usd="1000")

        # Assert
        assert price.usd == "1000"

    def test_price_model_with_eur(self):
        """Test PriceModel with EUR price."""
        # Act
        price = PriceModel(eur="900")

        # Assert
        assert price.eur == "900"

    def test_price_model_with_alias(self):
        """Test PriceModel with alias (USD instead of usd)."""
        # Act
        price = PriceModel.model_validate({"USD": "1500", "EUR": "1300"})

        # Assert
        assert price.usd == "1500"
        assert price.eur == "1300"

    def test_price_model_to_usd_decimal(self):
        """Test conversion to USD decimal (dollars from cents)."""
        # Arrange
        price = PriceModel(usd="1000")

        # Act
        decimal_price = price.to_usd_decimal()

        # Assert
        assert decimal_price == Decimal("10.00")

    def test_price_model_to_eur_decimal(self):
        """Test conversion to EUR decimal (euros from cents)."""
        # Arrange
        price = PriceModel(eur="500")

        # Act
        decimal_price = price.to_eur_decimal()

        # Assert
        assert decimal_price == Decimal("5.00")

    def test_price_model_none_values(self):
        """Test PriceModel with None values."""
        # Act
        price = PriceModel()

        # Assert
        assert price.usd is None
        assert price.eur is None
        assert price.to_usd_decimal() == Decimal(0)

    def test_price_model_numeric_input(self):
        """Test PriceModel with numeric input (should convert to string)."""
        # Act
        price = PriceModel.model_validate({"USD": 1500})

        # Assert
        assert price.usd == "1500"


# TestAttributesModel


class TestAttributesModel:
    """Tests for AttributesModel."""

    def test_attributes_model_basic(self):
        """Test AttributesModel with basic attributes."""
        # Act
        attrs = AttributesModel(category="Rifle", exterior="Field-Tested", rarity="Covert")

        # Assert
        assert attrs.category == "Rifle"
        assert attrs.exterior == "Field-Tested"
        assert attrs.rarity == "Covert"

    def test_attributes_model_with_alias(self):
        """Test AttributesModel with alias fields."""
        # Act
        attrs = AttributesModel.model_validate({
            "category": "Knife",
            "floatValue": "0.15",
            "paintSeed": 123,
        })

        # Assert
        assert attrs.float_value == "0.15"
        assert attrs.paint_seed == 123

    def test_attributes_model_extra_fields(self):
        """Test AttributesModel allows extra fields."""
        # Act
        attrs = AttributesModel.model_validate({
            "category": "Rifle",
            "customField": "custom_value",
        })

        # Assert
        assert attrs.category == "Rifle"


# TestMarketItemModel


class TestMarketItemModel:
    """Tests for MarketItemModel."""

    def test_market_item_model_basic(self):
        """Test MarketItemModel with basic data."""
        # Arrange
        data = {
            "itemId": "item_123",
            "title": "AK-47 | Redline (Field-Tested)",
            "price": {"USD": "1500"},
        }

        # Act
        item = MarketItemModel.model_validate(data)

        # Assert
        assert item.item_id == "item_123"
        assert item.title == "AK-47 | Redline (Field-Tested)"
        assert item.price.usd == "1500"

    def test_market_item_model_with_suggested_price(self):
        """Test MarketItemModel with suggested price."""
        # Arrange
        data = {
            "itemId": "item_456",
            "title": "AWP | Dragon Lore",
            "price": {"USD": "100000"},
            "suggestedPrice": {"USD": "95000"},
        }

        # Act
        item = MarketItemModel.model_validate(data)

        # Assert
        assert item.suggested_price is not None
        assert item.suggested_price.usd == "95000"

    def test_market_item_model_with_attributes(self):
        """Test MarketItemModel with attributes."""
        # Arrange
        data = {
            "itemId": "item_789",
            "title": "★ Butterfly Knife | Fade",
            "price": {"USD": "50000"},
            "attributes": {"exterior": "Factory New", "phase": "Phase 2"},
        }

        # Act
        item = MarketItemModel.model_validate(data)

        # Assert
        assert item.attributes is not None
        assert item.attributes.exterior == "Factory New"


# TestMarketItemsResponse


class TestMarketItemsResponse:
    """Tests for MarketItemsResponse."""

    def test_market_items_response_basic(self):
        """Test MarketItemsResponse with basic data."""
        # Arrange
        data = {
            "objects": [
                {"itemId": "1", "title": "Item 1", "price": {"USD": "100"}},
                {"itemId": "2", "title": "Item 2", "price": {"USD": "200"}},
            ],
            "total": 2,
        }

        # Act
        response = MarketItemsResponse.model_validate(data)

        # Assert
        assert len(response.objects) == 2
        assert response.total == 2

    def test_market_items_response_total_as_string(self):
        """Test MarketItemsResponse with total as string."""
        # Arrange
        data = {
            "objects": [],
            "total": "100",
        }

        # Act
        response = MarketItemsResponse.model_validate(data)

        # Assert
        assert response.total == 100

    def test_market_items_response_total_as_dict(self):
        """Test MarketItemsResponse with total as dict."""
        # Arrange
        data = {
            "objects": [],
            "total": {"items": 50, "offers": 30},
        }

        # Act
        response = MarketItemsResponse.model_validate(data)

        # Assert
        assert response.total == 80  # 50 + 30

    def test_market_items_response_with_cursor(self):
        """Test MarketItemsResponse with pagination cursor."""
        # Arrange
        data = {
            "objects": [],
            "total": 0,
            "cursor": "abc123xyz",
        }

        # Act
        response = MarketItemsResponse.model_validate(data)

        # Assert
        assert response.cursor == "abc123xyz"

    def test_market_items_response_empty(self):
        """Test MarketItemsResponse with empty data."""
        # Act
        response = MarketItemsResponse.model_validate({"objects": []})

        # Assert
        assert response.objects == []
        assert response.total == 0


# TestTargetPriceModel


class TestTargetPriceModel:
    """Tests for TargetPriceModel."""

    def test_target_price_model_basic(self):
        """Test TargetPriceModel with basic data."""
        # Act
        price = TargetPriceModel(amount=1500, currency="USD")

        # Assert
        assert price.amount == 1500
        assert price.currency == "USD"

    def test_target_price_model_amount_as_string(self):
        """Test TargetPriceModel with amount as string."""
        # Act
        price = TargetPriceModel.model_validate({"amount": "2500", "currency": "USD"})

        # Assert
        assert price.amount == 2500

    def test_target_price_model_default_currency(self):
        """Test TargetPriceModel with default currency."""
        # Act
        price = TargetPriceModel(amount=1000)

        # Assert
        assert price.currency == "USD"


# TestCreateTargetRequest


class TestCreateTargetRequest:
    """Tests for CreateTargetRequest."""

    def test_create_target_request_basic(self):
        """Test CreateTargetRequest with basic data."""
        # Arrange
        data = {
            "Title": "AK-47 | Redline",
            "Amount": 5,
            "Price": {"amount": 1000, "currency": "USD"},
        }

        # Act
        request = CreateTargetRequest.model_validate(data)

        # Assert
        assert request.title == "AK-47 | Redline"
        assert request.amount == 5
        assert request.price.amount == 1000

    def test_create_target_request_with_attrs(self):
        """Test CreateTargetRequest with attributes."""
        # Arrange
        data = {
            "Title": "Test Item",
            "Amount": 1,
            "Price": {"amount": 500, "currency": "USD"},
            "Attrs": {"exterior": "Field-Tested"},
        }

        # Act
        request = CreateTargetRequest.model_validate(data)

        # Assert
        assert request.attrs is not None
        assert request.attrs["exterior"] == "Field-Tested"


# TestTargetResultModel


class TestTargetResultModel:
    """Tests for TargetResultModel."""

    def test_target_result_model_success(self):
        """Test TargetResultModel for successful operation."""
        # Arrange
        data = {
            "TargetID": "target_123",
            "Title": "AK-47",
            "Status": "success",
        }

        # Act
        result = TargetResultModel.model_validate(data)

        # Assert
        assert result.target_id == "target_123"
        assert result.status == "success"


# TestUserTargetModel


class TestUserTargetModel:
    """Tests for UserTargetModel."""

    def test_user_target_model_basic(self):
        """Test UserTargetModel with basic data."""
        # Arrange
        data = {
            "TargetID": "target_456",
            "Title": "AWP | Asiimov",
            "Amount": 3,
            "Price": {"amount": 5000, "currency": "USD"},
            "Status": "active",
            "CreatedAt": 1699999999,
        }

        # Act
        target = UserTargetModel.model_validate(data)

        # Assert
        assert target.target_id == "target_456"
        assert target.title == "AWP | Asiimov"
        assert target.amount == 3
        assert target.status == "active"


# TestUserTargetsResponse


class TestUserTargetsResponse:
    """Tests for UserTargetsResponse."""

    def test_user_targets_response_basic(self):
        """Test UserTargetsResponse with basic data."""
        # Arrange
        data = {
            "Items": [
                {
                    "TargetID": "1",
                    "Title": "Item 1",
                    "Amount": 1,
                    "Price": {"amount": 100, "currency": "USD"},
                    "Status": "active",
                    "CreatedAt": 1699999999,
                }
            ],
            "Total": "1",
        }

        # Act
        response = UserTargetsResponse.model_validate(data)

        # Assert
        assert len(response.items) == 1

    def test_user_targets_response_empty(self):
        """Test UserTargetsResponse with no items."""
        # Act
        response = UserTargetsResponse.model_validate({"Items": [], "Total": "0"})

        # Assert
        assert response.items == []


# TestEdgeCases


class TestSchemaEdgeCases:
    """Tests for edge cases in schemas."""

    def test_price_model_with_dmc(self):
        """Test PriceModel with DMC currency."""
        # Act
        price = PriceModel.model_validate({"DMC": "5000"})

        # Assert
        assert price.dmc == "5000"

    def test_market_item_response_total_non_digit_string(self):
        """Test total field with non-digit string."""
        # Arrange
        data = {
            "objects": [],
            "total": "invalid",
        }

        # Act
        response = MarketItemsResponse.model_validate(data)

        # Assert
        assert response.total == 0

    def test_market_item_response_total_none(self):
        """Test total field with None value."""
        # Arrange
        data = {
            "objects": [],
            "total": None,
        }

        # Act
        response = MarketItemsResponse.model_validate(data)

        # Assert
        assert response.total == 0

    def test_create_targets_response(self):
        """Test CreateTargetsResponse model."""
        # Arrange
        data = {
            "Result": [
                {"TargetID": "1", "Title": "Test", "Status": "success"},
            ]
        }

        # Act
        response = CreateTargetsResponse.model_validate(data)

        # Assert
        assert len(response.result) == 1
