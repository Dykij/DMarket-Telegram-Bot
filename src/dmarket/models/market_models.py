"""Модели данных для работы с DMarket API согласно официальной документации.

Этот модуль содержит pydantic модели для работы с данными DMarket API v1.1.0,
включая модели для предметов, цен, продаж, баланса и других сущностей.

Documentation: https://docs.dmarket.com/v1/swagger.html
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ==================== ENUMS ====================


class OfferStatus(str, Enum):
    """Статусы предложений согласно DMarket API."""

    DEFAULT = "OfferStatusDefault"
    ACTIVE = "OfferStatusActive"
    SOLD = "OfferStatusSold"
    INACTIVE = "OfferStatusInactive"
    IN_TRANSFER = "OfferStatusIn_transfer"


class TargetStatus(str, Enum):
    """Статусы таргетов (buy orders) согласно DMarket API."""

    ACTIVE = "TargetStatusActive"
    INACTIVE = "TargetStatusInactive"


class TransferStatus(str, Enum):
    """Статусы трансфера согласно DMarket API."""

    PENDING = "TransferStatusPending"
    COMPLETED = "TransferStatusCompleted"
    FAILED = "TransferStatusFailed"


class TradeStatus(str, Enum):
    """Статусы сделок согласно DMarket API."""

    SUCCESSFUL = "successful"
    REVERTED = "reverted"
    TRADE_PROTECTED = "trade_protected"


# ==================== PRICE MODELS ====================


class Price(BaseModel):
    """Модель цены согласно DMarket API."""

    Currency: str = Field(default="USD", description="Валюта (USD, EUR, etc)")
    Amount: int = Field(description="Сумма в центах (для USD) или эквиваленте")

    @property
    def dollars(self) -> float:
        """Конвертирует цену из центов в доллары."""
        return self.Amount / 100.0

    @classmethod
    def from_dollars(cls, amount: float, currency: str = "USD") -> Price:
        """Создает объект Price из суммы в долларах.

        Args:
            amount: Сумма в долларах
            currency: Валюта

        Returns:
            Объект Price

        """
        return cls(Currency=currency, Amount=int(amount * 100))


class MarketPrice(BaseModel):
    """Модель цены предмета на маркете (упрощенная версия)."""

    USD: str = Field(description="Цена в USD")
    EUR: str | None = Field(None, description="Цена в EUR")


# ==================== ACCOUNT MODELS ====================


class Balance(BaseModel):
    """Модель баланса пользователя согласно DMarket API.

    Response format: /account/v1/balance
    {
        "usd": "string",
        "dmcAvailableToWithdraw": "string",
        "dmc": "string",
        "usdAvailableToWithdraw": "string"
    }
    """

    usd: str = Field(description="USD баланс в центах (строка)")
    usdAvailableToWithdraw: str = Field(description="Доступный для вывода USD в центах")
    dmc: str | None = Field(None, description="DMC баланс")
    dmcAvailableToWithdraw: str | None = Field(None, description="Доступный для вывода DMC")

    @property
    def usd_dollars(self) -> float:
        """Конвертирует USD баланс из центов в доллары."""
        try:
            # Может быть строкой или числом
            amount = int(self.usd) if isinstance(self.usd, str) else self.usd
            return amount / 100.0
        except (ValueError, TypeError):
            return 0.0

    @property
    def available_usd_dollars(self) -> float:
        """Конвертирует доступный USD из центов в доллары."""
        try:
            amount = (
                int(self.usdAvailableToWithdraw)
                if isinstance(self.usdAvailableToWithdraw, str)
                else self.usdAvailableToWithdraw
            )
            return amount / 100.0
        except (ValueError, TypeError):
            return 0.0


class UserProfile(BaseModel):
    """Модель профиля пользователя согласно DMarket API.

    Response format: /account/v1/user
    """

    id: str = Field(description="ID пользователя")
    username: str = Field(description="Имя пользователя")
    email: str = Field(description="Email пользователя")
    isEmailVerified: bool = Field(description="Email подтвержден")
    countryCode: str | None = Field(None, description="Код страны")
    publicKey: str | None = Field(None, description="Публичный ключ API")


# ==================== MARKET ITEM MODELS ====================


class MarketItem(BaseModel):
    """Модель предмета на маркете согласно DMarket API.

    Response format: /exchange/v1/market/items
    """

    itemId: str = Field(description="ID предмета")
    title: str = Field(description="Название предмета")
    price: dict[str, Any] = Field(description="Цена предмета")
    gameId: str = Field(description="ID игры")
    image: str | None = Field(None, description="URL изображения")
    categoryPath: str | None = Field(None, description="Путь категории")
    tradable: bool | None = Field(None, description="Можно торговать")
    type: str | None = Field(None, description="Тип предмета")
    tags: list[str] | None = Field(None, description="Теги предмета")
    extra: dict[str, Any] | None = Field(None, description="Дополнительные данные")

    @property
    def price_usd(self) -> float:
        """Получает цену в USD как float."""
        try:
            price_data = self.price.get("USD", "0")
            if isinstance(price_data, dict):
                # Формат: {"USD": {"amount": 1234}}
                return float(price_data.get("amount", 0)) / 100.0
            # Формат: {"USD": "12.34"}
            return float(price_data)
        except (ValueError, TypeError):
            return 0.0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MarketItem:
        """Создает объект MarketItem из словаря.

        Args:
            data: Словарь с данными предмета

        Returns:
            Объект MarketItem

        """
        return cls(**data)


# ==================== OFFER MODELS ====================


class Offer(BaseModel):
    """Модель предложения пользователя согласно DMarket API.

    Response format: /marketplace-api/v1/user-offers
    """

    OfferID: str = Field(description="ID предложения")
    AssetID: str = Field(description="ID актива")
    Title: str = Field(description="Название предмета")
    GameID: str = Field(description="ID игры")
    GameType: str | None = Field(None, description="Тип игры")
    price: dict[str, Any] = Field(description="Цена предложения")
    status: str = Field(description="Статус предложения")
    CreatedAt: str | None = Field(None, description="Дата создания")
    UpdatedAt: str | None = Field(None, description="Дата обновления")


# ==================== TARGET MODELS ====================


class TargetAttrs(BaseModel):
    """Дополнительные атрибуты для таргета."""

    paintSeed: int | None = Field(None, description="Paint seed (CS:GO)")
    phase: str | None = Field(None, description="Phase (Doppler, etc)")
    floatPartValue: str | None = Field(None, description="Float value")


class Target(BaseModel):
    """Модель таргета (buy order) согласно DMarket API.

    Request/Response format: /marketplace-api/v1/user-targets
    """

    TargetID: str | None = Field(None, description="ID таргета")
    Title: str = Field(description="Название предмета")
    Amount: str = Field(description="Количество")
    price: dict[str, Any] = Field(description="Цена покупки")
    Attrs: TargetAttrs | None = Field(None, description="Дополнительные атрибуты")
    status: str | None = Field(None, description="Статус таргета")


class CreateTargetRequest(BaseModel):
    """Запрос на создание таргетов."""

    GameID: str = Field(description="ID игры (a8db для CS:GO, 9a92 для Dota 2)")
    Targets: list[Target] = Field(description="Список таргетов для создания")


# ==================== AGGREGATED PRICES MODELS (API v1.1.0) ====================


class AggregatedPrice(BaseModel):
    """Модель агрегированной цены для предмета (API v1.1.0).

    Response format: /marketplace-api/v1/aggregated-prices
    """

    title: str = Field(description="Название предмета")
    orderBestPrice: str = Field(description="Лучшая цена покупки (buy order) в центах")
    orderCount: int = Field(description="Количество активных заявок на покупку")
    offerBestPrice: str = Field(description="Лучшая цена продажи (offer) в центах")
    offerCount: int = Field(description="Количество активных предложений")

    @property
    def order_price_usd(self) -> float:
        """Конвертирует лучшую цену покупки из центов в доллары."""
        try:
            return float(self.orderBestPrice) / 100.0
        except (ValueError, TypeError):
            return 0.0

    @property
    def offer_price_usd(self) -> float:
        """Конвертирует лучшую цену продажи из центов в доллары."""
        try:
            return float(self.offerBestPrice) / 100.0
        except (ValueError, TypeError):
            return 0.0

    @property
    def spread_usd(self) -> float:
        """Вычисляет спред между лучшей ценой продажи и покупки в USD."""
        return self.offer_price_usd - self.order_price_usd

    @property
    def spread_percent(self) -> float:
        """Вычисляет спред в процентах."""
        if self.order_price_usd == 0:
            return 0.0
        return (self.spread_usd / self.order_price_usd) * 100.0


class AggregatedPricesResponse(BaseModel):
    """Ответ от эндпоинта aggregated-prices (API v1.1.0)."""

    aggregatedPrices: list[AggregatedPrice] = Field(description="Список агрегированных цен")
    nextCursor: str | None = Field(None, description="Курсор для следующей страницы")


# ==================== TARGETS BY TITLE MODELS (API v1.1.0) ====================


class TargetOrder(BaseModel):
    """Модель заявки на покупку из targets-by-title (API v1.1.0)."""

    amount: int = Field(description="Количество запрашиваемых предметов")
    price: str = Field(description="Цена в центах")
    title: str = Field(description="Название предмета")
    attributes: dict[str, Any] | None = Field(None, description="Атрибуты (exterior, phase, etc)")

    @property
    def price_usd(self) -> float:
        """Конвертирует цену из центов в доллары."""
        try:
            return float(self.price) / 100.0
        except (ValueError, TypeError):
            return 0.0


class TargetsByTitleResponse(BaseModel):
    """Ответ от эндпоинта targets-by-title (API v1.1.0)."""

    orders: list[TargetOrder] = Field(description="Список заявок на покупку")


# ==================== SALES HISTORY MODELS ====================


class SalesHistory(BaseModel):
    """Модель истории продаж предмета согласно DMarket API.

    Response format: /trade-aggregator/v1/last-sales
    """

    price: str = Field(description="Цена продажи")
    date: str = Field(description="Дата продажи (ISO format)")
    txOperationType: str | None = Field(None, description="Тип операции")
    offerAttributes: dict[str, Any] | None = Field(None, description="Атрибуты оффера")
    orderAttributes: dict[str, Any] | None = Field(None, description="Атрибуты ордера")

    @property
    def price_float(self) -> float:
        """Конвертирует цену в float."""
        try:
            return float(self.price) / 100.0  # Предполагаем цена в центах
        except (ValueError, TypeError):
            return 0.0

    @property
    def date_datetime(self) -> datetime | None:
        """Конвертирует дату в datetime."""
        try:
            return datetime.fromisoformat(self.date)
        except (ValueError, AttributeError):
            return None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SalesHistory:
        """Создает объект SalesHistory из словаря.

        Args:
            data: Словарь с данными истории продаж

        Returns:
            Объект SalesHistory

        """
        return cls(**data)


# ==================== DEPOSIT/WITHDRAW MODELS ====================


class DepositAsset(BaseModel):
    """Модель актива в депозите."""

    InGameAssetID: str = Field(description="ID актива в игре")
    DmarketAssetID: str = Field(description="ID актива на DMarket")


class DepositStatus(BaseModel):
    """Статус депозита согласно DMarket API.

    Response format: /marketplace-api/v1/deposit-status/{DepositID}
    """

    DepositID: str = Field(description="ID депозита")
    AssetID: list[str] = Field(description="Список ID активов")
    status: TransferStatus = Field(description="Статус трансфера")
    Error: str | None = Field(None, description="Сообщение об ошибке")
    Assets: list[DepositAsset] | None = Field(None, description="Список активов")
    SteamDepositInfo: dict[str, Any] | None = Field(None, description="Информация о Steam депозите")


# ==================== LEGACY MODELS (для обратной совместимости) ====================


@dataclass
class BalanceLegacy:
    """Устаревшая модель баланса (для обратной совместимости)."""

    totalBalance: float
    blockedBalance: float

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BalanceLegacy:
        """Создает объект Balance из словаря.

        Args:
            data: Словарь с данными баланса

        Returns:
            Объект Balance

        """
        return cls(
            totalBalance=float(data.get("totalBalance", 0.0)),
            blockedBalance=float(data.get("blockedBalance", 0.0)),
        )


# Экспортируем все модели
__all__ = [
    # Account models
    "Balance",
    # Legacy models
    "BalanceLegacy",
    "CreateTargetRequest",
    # Deposit/Withdraw models
    "DepositAsset",
    "DepositStatus",
    # Market item models
    "MarketItem",
    "MarketPrice",
    # Offer models
    "Offer",
    # Enums
    "OfferStatus",
    # Price models
    "Price",
    # Sales history models
    "SalesHistory",
    # Target models
    "Target",
    "TargetAttrs",
    "TargetStatus",
    "TradeStatus",
    "TransferStatus",
    "UserProfile",
    # API v1.1.0 models
    "AggregatedPrice",
    "AggregatedPricesResponse",
    "TargetOrder",
    "TargetsByTitleResponse",
]
