"""
Pydantic схемы для валидации ответов DMarket API.

Этот модуль содержит все модели данных для валидации ответов от DMarket API v1.1.0.
Использует Pydantic v2 для строгой типизации и автоматической валидации.
"""

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ============================================================================
# Базовые модели
# ============================================================================


class PriceModel(BaseModel):
    """Модель цены в различных валютах."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    usd: str | None = Field(None, alias="USD", description="Цена в центах USD")
    eur: str | None = Field(None, alias="EUR", description="Цена в центах EUR")
    dmc: str | None = Field(None, alias="DMC", description="Цена в DMC")

    @field_validator("usd", "eur", "dmc", mode="before")
    @classmethod
    def validate_price_string(cls, v: Any) -> str | None:
        """Валидация что цена - строка или число."""
        if v is None:
            return None
        return str(v)

    def to_usd_decimal(self) -> Decimal:
        """Конвертировать USD из центов в доллары."""
        if self.usd:
            return Decimal(self.usd) / 100
        return Decimal(0)

    def to_eur_decimal(self) -> Decimal:
        """Конвертировать EUR из центов в евро."""
        if self.eur:
            return Decimal(self.eur) / 100
        return Decimal(0)


class AttributesModel(BaseModel):
    """Модель дополнительных атрибутов предмета."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    category: str | None = Field(None, description="Категория предмета")
    exterior: str | None = Field(None, description="Состояние (для CS:GO)")
    rarity: str | None = Field(None, description="Редкость")
    float_value: str | None = Field(
        None, alias="floatValue", description="Float значение"
    )
    phase: str | None = Field(None, description="Фаза (для Doppler)")
    paint_seed: int | None = Field(None, alias="paintSeed", description="Paint seed")


# ============================================================================
# Модели для маркетплейса
# ============================================================================


class MarketItemModel(BaseModel):
    """Модель предмета на маркете."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    item_id: str = Field(..., alias="itemId", description="ID предмета")
    title: str = Field(..., description="Название предмета")
    price: PriceModel = Field(..., description="Цена предмета")
    suggested_price: PriceModel | None = Field(
        None, alias="suggestedPrice", description="Рекомендуемая цена"
    )
    image_url: str | None = Field(None, alias="imageUrl", description="URL изображения")
    game_id: str | None = Field(None, alias="gameId", description="ID игры")
    extra: dict[str, Any] | None = Field(None, description="Дополнительная информация")
    attributes: AttributesModel | None = Field(None, description="Атрибуты предмета")


class MarketItemsResponse(BaseModel):
    """Модель ответа для списка предметов маркета."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    objects: list[MarketItemModel] = Field(
        default_factory=list, description="Список предметов"
    )
    total: int | str = Field(0, description="Общее количество предметов")
    cursor: str | None = Field(None, description="Курсор для пагинации")

    @field_validator("total", mode="before")
    @classmethod
    def validate_total(cls, v: Any) -> int:
        """Валидация total - может быть строкой, числом или dict {'items': N, 'offers': M}."""
        if isinstance(v, dict):
            # DMarket API может вернуть {'items': 0, 'offers': 0}
            return int(v.get("items", 0)) + int(v.get("offers", 0))
        if isinstance(v, str):
            return int(v) if v.isdigit() else 0
        return int(v) if v is not None else 0


# ============================================================================
# Модели для таргетов (Buy Orders)
# ============================================================================


class TargetPriceModel(BaseModel):
    """Модель цены для таргета."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    amount: int | str = Field(..., description="Сумма в центах")
    currency: str = Field("USD", description="Валюта")

    @field_validator("amount", mode="before")
    @classmethod
    def validate_amount(cls, v: Any) -> int:
        """Валидация amount."""
        if isinstance(v, str):
            return int(v) if v.isdigit() else 0
        return int(v) if v is not None else 0


class CreateTargetRequest(BaseModel):
    """Модель запроса для создания таргета."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    title: str = Field(..., alias="Title", description="Название предмета")
    amount: int = Field(..., alias="Amount", description="Количество", ge=1, le=100)
    price: TargetPriceModel = Field(..., alias="Price", description="Цена")
    attrs: dict[str, Any] | None = Field(
        None, alias="Attrs", description="Дополнительные атрибуты"
    )


class TargetResultModel(BaseModel):
    """Модель результата создания/удаления таргета."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    target_id: str = Field(..., alias="TargetID", description="ID таргета")
    title: str | None = Field(None, alias="Title", description="Название")
    status: str = Field(..., alias="Status", description="Статус операции")


class CreateTargetsResponse(BaseModel):
    """Модель ответа для создания таргетов."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    result: list[TargetResultModel] = Field(
        default_factory=list, alias="Result", description="Результаты"
    )


class UserTargetModel(BaseModel):
    """Модель пользовательского таргета."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    target_id: str = Field(..., alias="TargetID", description="ID таргета")
    title: str = Field(..., alias="Title", description="Название")
    amount: int = Field(..., alias="Amount", description="Количество")
    price: TargetPriceModel = Field(..., alias="Price", description="Цена")
    status: str = Field(..., alias="Status", description="Статус")
    created_at: int = Field(..., alias="CreatedAt", description="Timestamp создания")


class UserTargetsResponse(BaseModel):
    """Модель ответа для списка таргетов пользователя."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    items: list[UserTargetModel] = Field(
        default_factory=list, alias="Items", description="Список таргетов"
    )
    total: str | int = Field("0", alias="Total", description="Общее количество")
    cursor: str | None = Field(None, alias="Cursor", description="Курсор пагинации")

    @field_validator("total", mode="before")
    @classmethod
    def validate_total(cls, v: Any) -> int:
        """Валидация total."""
        if isinstance(v, str):
            return int(v) if v.isdigit() else 0
        return int(v) if v is not None else 0


# ============================================================================
# Модели для предложений (Offers)
# ============================================================================


class DMarketOffer(BaseModel):
    """Модель предложения на продажу."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    offer_id: str = Field(..., alias="offerId", description="ID предложения")
    price_usd: str = Field(..., alias="price", description="Цена в центах USD")
    item_name: str = Field(..., alias="title", description="Название предмета")
    asset_id: str | None = Field(None, alias="assetId", description="ID актива")
    status: str | None = Field(None, description="Статус предложения")

    def get_price_decimal(self) -> Decimal:
        """Получить цену в долларах."""
        return Decimal(self.price_usd) / 100


class CreateOfferRequest(BaseModel):
    """Модель запроса для создания предложения."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    asset_id: str = Field(..., alias="AssetID", description="ID актива из инвентаря")
    price: TargetPriceModel = Field(..., alias="Price", description="Цена продажи")


class CreateOffersResponse(BaseModel):
    """Модель ответа для создания предложений."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    result: list[dict[str, Any]] = Field(
        default_factory=list, alias="Result", description="Результаты"
    )


# ============================================================================
# Модели для баланса
# ============================================================================


class BalanceResponse(BaseModel):
    """Модель ответа для баланса пользователя."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    usd: str = Field("0", description="Баланс USD в центах")
    usd_available_to_withdraw: str = Field(
        "0", alias="usdAvailableToWithdraw", description="Доступно для вывода USD"
    )
    dmc: str = Field("0", description="Баланс DMC")
    dmc_available_to_withdraw: str = Field(
        "0", alias="dmcAvailableToWithdraw", description="Доступно для вывода DMC"
    )

    def get_usd_decimal(self) -> Decimal:
        """Получить баланс USD в долларах."""
        return Decimal(self.usd) / 100

    def get_available_usd_decimal(self) -> Decimal:
        """Получить доступный баланс USD в долларах."""
        return Decimal(self.usd_available_to_withdraw) / 100


# ============================================================================
# Модели для агрегированных цен
# ============================================================================


class AggregatedPriceModel(BaseModel):
    """Модель агрегированных цен для предмета."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    title: str = Field(..., description="Название предмета")
    order_best_price: str | None = Field(
        None, alias="orderBestPrice", description="Лучшая цена покупки (buy order)"
    )
    order_count: int = Field(
        0, alias="orderCount", description="Количество активных заявок на покупку"
    )
    offer_best_price: str | None = Field(
        None, alias="offerBestPrice", description="Лучшая цена продажи"
    )
    offer_count: int = Field(
        0, alias="offerCount", description="Количество активных предложений"
    )

    def get_order_price_decimal(self) -> Decimal | None:
        """Получить цену buy order в долларах."""
        if self.order_best_price:
            return Decimal(self.order_best_price) / 100
        return None

    def get_offer_price_decimal(self) -> Decimal | None:
        """Получить цену offer в долларах."""
        if self.offer_best_price:
            return Decimal(self.offer_best_price) / 100
        return None


class AggregatedPricesResponse(BaseModel):
    """Модель ответа для агрегированных цен."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    aggregated_prices: list[AggregatedPriceModel] = Field(
        default_factory=list,
        alias="aggregatedPrices",
        description="Агрегированные цены",
    )
    next_cursor: str | None = Field(
        None, alias="nextCursor", description="Курсор для следующей страницы"
    )


# ============================================================================
# Модели для истории продаж
# ============================================================================


class SaleModel(BaseModel):
    """Модель продажи предмета."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    price: str = Field(..., description="Цена в центах")
    date: int = Field(..., description="Timestamp продажи")
    tx_operation_type: str | None = Field(
        None, alias="txOperationType", description="Тип операции (Target/Offer)"
    )

    def get_price_decimal(self) -> Decimal:
        """Получить цену в долларах."""
        return Decimal(self.price) / 100

    def get_datetime(self) -> datetime:
        """Получить дату-время продажи."""
        return datetime.fromtimestamp(self.date)


class SalesHistoryResponse(BaseModel):
    """Модель ответа для истории продаж."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    sales: list[SaleModel] = Field(default_factory=list, description="История продаж")


# ============================================================================
# Модели для покупки
# ============================================================================


class BuyOfferRequest(BaseModel):
    """Модель запроса для покупки предложения."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    offer_id: str = Field(..., alias="offerId", description="ID предложения")
    price: dict[str, Any] = Field(..., description="Цена покупки")


class BuyOffersResponse(BaseModel):
    """Модель ответа для покупки предложений."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    order_id: str | None = Field(None, alias="orderId", description="ID заказа")
    status: str = Field(..., description="Статус транзакции")
    tx_id: str | None = Field(None, alias="txId", description="ID транзакции")
    dm_offers_status: dict[str, Any] | None = Field(
        None, alias="dmOffersStatus", description="Статусы предложений"
    )


# ============================================================================
# Модели для ошибок API
# ============================================================================


class DMarketAPIError(BaseModel):
    """Модель ошибки DMarket API."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    error: dict[str, Any] | str = Field(..., description="Информация об ошибке")
    code: str | None = Field(None, description="Код ошибки")
    message: str | None = Field(None, description="Сообщение об ошибке")
    status_code: int | None = Field(None, description="HTTP статус код")

    @field_validator("error", mode="before")
    @classmethod
    def validate_error(cls, v: Any) -> dict[str, Any] | str:
        """Валидация поля error."""
        if isinstance(v, dict):
            return v
        return {"message": str(v)}
