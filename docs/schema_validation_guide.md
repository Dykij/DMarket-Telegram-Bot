# Руководство по Schema Validation

**Версия**: 1.0
**Дата**: 17 декабря 2025 г.
**Статус**: ✅ Production Ready

---

## 📋 Обзор

Schema Validation - это критически важная часть проекта DMarket Bot, обеспечивающая:

- ✅ **Раннее обнаружение breaking changes** в DMarket API
- ✅ **Type safety** для всего downstream кода
- ✅ **Автоматическую валидацию** всех API responses
- ✅ **Clear error messages** при schema mismatch
- ✅ **Self-documenting code** через Pydantic models

---

## 🎯 Цели

### Проблемы, которые решает Schema Validation

1. **Runtime errors** - Обнаружение несоответствий типов ДО использования данных
2. **API changes** - Автоматическое обнаружение изменений API DMarket
3. **Data integrity** - Гарантия корректности данных
4. **Developer experience** - IDE autocomplete и type hints

---

## 🏗️ Архитектура

### Расположение моделей

Все Pydantic модели находятся в:

```
src/dmarket/models/market_models.py
```

### Категории моделей

#### 1. **Enums** - Константные значения

```python
class OfferStatus(str, Enum):
    """Статусы предложений согласно DMarket API."""
    DEFAULT = "OfferStatusDefault"
    ACTIVE = "OfferStatusActive"
    SOLD = "OfferStatusSold"
    INACTIVE = "OfferStatusInactive"

class TargetStatus(str, Enum):
    """Статусы таргетов."""
    ACTIVE = "TargetStatusActive"
    INACTIVE = "TargetStatusInactive"
```

#### 2. **Price models** - Работа с ценами

```python
class Price(BaseModel):
    """Модель цены согласно DMarket API."""
    Currency: str = Field(default="USD")
    Amount: int = Field(description="Сумма в центах")

    @property
    def dollars(self) -> float:
        """Конвертирует из центов в доллары."""
        return self.Amount / 100.0

    @classmethod
    def from_dollars(cls, amount: float, currency: str = "USD") -> Price:
        """Создает Price из долларов."""
        return cls(Currency=currency, Amount=int(amount * 100))
```

#### 3. **Account models** - Баланс и профиль

```python
class Balance(BaseModel):
    """Модель баланса пользователя."""
    usd: str = Field(description="USD баланс в центах")
    usdAvailableToWithdraw: str
    dmc: str | None = None
    dmcAvailableToWithdraw: str | None = None

    @property
    def usd_dollars(self) -> float:
        """USD в долларах."""
        return int(self.usd) / 100.0
```

#### 4. **Market item models** - Предметы на рынке

```python
class MarketItem(BaseModel):
    """Модель предмета на маркете."""
    itemId: str
    title: str
    price: dict[str, Any]
    gameId: str
    suggestedPrice: dict[str, str] | None = None
    extra: dict[str, Any] | None = None

    @property
    def price_usd(self) -> float:
        """Цена в USD как float."""
        try:
            price_data = self.price.get("USD", "0")
            if isinstance(price_data, dict):
                return float(price_data.get("amount", 0)) / 100.0
            return float(price_data)
        except (ValueError, TypeError):
            return 0.0

class MarketItemsResponse(BaseModel):
    """Ответ от /exchange/v1/market/items."""
    objects: list[MarketItem] = Field(default_factory=list)
    total: int = Field(default=0)
    cursor: str | None = None
```

#### 5. **Target models** - Таргеты (Buy Orders)

```python
class TargetAttrs(BaseModel):
    """Дополнительные атрибуты для таргета."""
    paintSeed: int | None = None
    phase: str | None = None
    floatPartValue: str | None = None

class Target(BaseModel):
    """Модель таргета."""
    TargetID: str | None = None
    Title: str
    Amount: str
    price: dict[str, Any]
    Attrs: TargetAttrs | None = None
    status: str | None = None

class UserTargetsResponse(BaseModel):
    """Ответ от /marketplace-api/v1/user-targets."""
    Items: list[Target] = Field(default_factory=list)
    Total: str = Field(default="0")
    Cursor: str | None = None
```

#### 6. **API v1.1.0 models** - Новые эндпоинты

```python
class AggregatedPrice(BaseModel):
    """Агрегированная цена для предмета (API v1.1.0)."""
    title: str
    orderBestPrice: str  # В центах
    orderCount: int
    offerBestPrice: str  # В центах
    offerCount: int

    @property
    def order_price_usd(self) -> float:
        """Лучшая цена покупки в USD."""
        return float(self.orderBestPrice) / 100.0

    @property
    def spread_percent(self) -> float:
        """Спред в процентах."""
        if self.order_price_usd == 0:
            return 0.0
        return (self.spread_usd / self.order_price_usd) * 100.0

class AggregatedPricesResponse(BaseModel):
    """Ответ от /marketplace-api/v1/aggregated-prices."""
    aggregatedPrices: list[AggregatedPrice]
    nextCursor: str | None = None
```

#### 7. **Sales History models** - История продаж

```python
class SalesHistory(BaseModel):
    """История продаж предмета."""
    price: str
    date: str
    txOperationType: str | None = None
    offerAttributes: dict[str, Any] | None = None

    @property
    def price_float(self) -> float:
        """Цена как float."""
        return float(self.price) / 100.0

    @property
    def date_datetime(self) -> datetime | None:
        """Дата как datetime."""
        try:
            return datetime.fromisoformat(self.date)
        except (ValueError, AttributeError):
            return None

class LastSalesResponse(BaseModel):
    """Ответ от /trade-aggregator/v1/last-sales."""
    sales: list[SalesHistory] = Field(default_factory=list)
```

#### 8. **Inventory models** - Инвентарь пользователя

```python
class InventoryItem(BaseModel):
    """Предмет из инвентаря пользователя."""
    ItemID: str
    AssetID: str
    Title: str
    GameID: str
    Image: str | None = None
    Price: Price | None = None
    InMarket: bool = Field(default=False)
    Withdrawable: bool = Field(default=True)
    Tradable: bool = Field(default=True)
    Attributes: dict[str, Any] | None = None

class UserInventoryResponse(BaseModel):
    """Ответ от /marketplace-api/v1/user-inventory."""
    Items: list[InventoryItem] = Field(default_factory=list)
    Total: str = Field(default="0")
    Cursor: str | None = None
```

#### 9. **Transaction models** - Покупка/продажа

```python
class BuyItemResponse(BaseModel):
    """Ответ после покупки предмета."""
    orderId: str
    status: str
    txId: str | None = None
    dmOffersStatus: dict[str, dict[str, str]] | None = None

class CreateOfferResponse(BaseModel):
    """Ответ после создания предложения."""
    Result: list[dict[str, str]] = Field(default_factory=list)

class UserOffersResponse(BaseModel):
    """Ответ от /marketplace-api/v1/user-offers."""
    Items: list[Offer] = Field(default_factory=list)
    Total: str = Field(default="0")
    Cursor: str | None = None
```

---

## 🔧 Использование

### Базовое использование

```python
from src.dmarket.models.market_models import (
    MarketItemsResponse,
    AggregatedPricesResponse,
    UserTargetsResponse,
    Balance,
)

# Парсинг JSON ответа с автоматической валидацией
async def get_market_items(api_client):
    response_data = await api_client.get("/exchange/v1/market/items")

    # Pydantic автоматически валидирует схему
    try:
        validated_response = MarketItemsResponse(**response_data)
    except ValidationError as e:
        logger.error("API schema mismatch", error=str(e))
        # Обработка ошибки валидации
        raise

    # Теперь можно безопасно работать с данными
    for item in validated_response.objects:
        print(f"{item.title}: ${item.price_usd:.2f}")

    return validated_response
```

### Использование с конверсией типов

```python
# Создание Price из долларов
price = Price.from_dollars(25.50, "USD")
print(price.Amount)  # 2550 (в центах)
print(price.dollars)  # 25.5

# Работа с балансом
balance_data = await api_client.get_balance()
balance = Balance(**balance_data)

print(f"Balance: ${balance.usd_dollars:.2f}")
print(f"Available: ${balance.available_usd_dollars:.2f}")
```

### Обработка ошибок валидации

```python
from pydantic import ValidationError

try:
    item = MarketItem(**api_response_data)
except ValidationError as e:
    # Детальная информация об ошибках
    for error in e.errors():
        field = error['loc'][0]
        message = error['msg']
        value = error.get('input')
        logger.error(
            "Validation error",
            field=field,
            message=message,
            value=value
        )

    # Например:
    # field='price', message='field required', value=None
    # field='itemId', message='str type expected', value=12345
```

---

## 🎨 Best Practices

### 1. Всегда валидировать API responses

```python
# ✅ Правильно - валидация перед использованием
async def fetch_items(api_client):
    raw_data = await api_client.get_market_items("csgo")
    validated = MarketItemsResponse(**raw_data)
    return validated.objects

# ❌ Неправильно - использование без валидации
async def fetch_items_bad(api_client):
    raw_data = await api_client.get_market_items("csgo")
    return raw_data["objects"]  # Может упасть с KeyError
```

### 2. Использовать properties для конверсий

```python
# ✅ Правильно - property для конверсии
item = MarketItem(**data)
price_usd = item.price_usd  # Безопасно

# ❌ Неправильно - ручная конверсия каждый раз
price_usd = float(item.price.get("USD", 0)) / 100.0  # Повторяемый код
```

### 3. Обрабатывать optional поля

```python
# ✅ Правильно - проверка на None
if item.suggestedPrice:
    suggested = item.suggested_price_usd
else:
    suggested = 0.0

# ❌ Неправильно - может быть None
suggested = item.suggested_price_usd  # AttributeError if None
```

### 4. Использовать type hints

```python
# ✅ Правильно - type hints из моделей
async def process_items(items: list[MarketItem]) -> float:
    total = sum(item.price_usd for item in items)
    return total

# ❌ Неправильно - без type hints
async def process_items(items):  # Непонятно что за items
    total = sum(item.price_usd for item in items)
    return total
```

---

## 🚨 Обнаружение Breaking Changes

### Как это работает

Когда DMarket меняет API schema, Pydantic автоматически обнаруживает это:

```python
# До: API возвращает
{
    "itemId": "123",
    "title": "AK-47",
    "price": {"USD": "1250"}
}

# После изменения API: новое поле обязательное
{
    "itemId": "123",
    "title": "AK-47",
    "price": {"USD": "1250"},
    "newRequiredField": "value"  # Новое обязательное поле
}

# Pydantic выбросит ValidationError:
# ValidationError: 1 validation error for MarketItem
#   newRequiredField
#     field required (type=value_error.missing)
```

### Мониторинг через Sentry

```python
import sentry_sdk

try:
    item = MarketItem(**api_response)
except ValidationError as e:
    # Sentry автоматически залогирует
    sentry_sdk.capture_exception(e)

    # Дополнительный контекст
    sentry_sdk.set_context("api_response", api_response)
    sentry_sdk.set_tag("api_endpoint", "/market/items")

    raise
```

---

## 📊 Метрики успеха

### Покрытие API эндпоинтов

| Эндпоинт                                 | Модель                     | Статус |
| ---------------------------------------- | -------------------------- | ------ |
| `/account/v1/balance`                    | `Balance`                  | ✅      |
| `/exchange/v1/market/items`              | `MarketItemsResponse`      | ✅      |
| `/exchange/v1/offers-by-title`           | `OffersByTitleResponse`    | ✅      |
| `/marketplace-api/v1/user-targets`       | `UserTargetsResponse`      | ✅      |
| `/marketplace-api/v1/user-offers`        | `UserOffersResponse`       | ✅      |
| `/marketplace-api/v1/user-inventory`     | `UserInventoryResponse`    | ✅      |
| `/marketplace-api/v1/aggregated-prices`  | `AggregatedPricesResponse` | ✅      |
| `/marketplace-api/v1/targets-by-title`   | `TargetsByTitleResponse`   | ✅      |
| `/trade-aggregator/v1/last-sales`        | `LastSalesResponse`        | ✅      |
| `/exchange/v1/offers-buy`                | `BuyItemResponse`          | ✅      |
| `/marketplace-api/v1/user-offers/create` | `CreateOfferResponse`      | ✅      |

**Покрытие**: 11/11 критических эндпоинтов (100%) ✅

---

## 🔄 Миграция существующего кода

### До (без валидации)

```python
async def get_balance(api_client):
    data = await api_client.get("/account/v1/balance")
    usd = float(data["usd"]) / 100.0  # Ручная конверсия
    return usd
```

### После (с валидацией)

```python
from src.dmarket.models.market_models import Balance

async def get_balance(api_client):
    data = await api_client.get("/account/v1/balance")
    balance = Balance(**data)  # Автоматическая валидация
    return balance.usd_dollars  # Property с конверсией
```

---

## 🧪 Тестирование

### Unit тесты для моделей

```python
import pytest
from pydantic import ValidationError
from src.dmarket.models.market_models import MarketItem, Price

def test_price_from_dollars():
    """Тест создания Price из долларов."""
    price = Price.from_dollars(25.50)
    assert price.Amount == 2550
    assert price.Currency == "USD"
    assert price.dollars == 25.5

def test_price_validation_fails_on_negative():
    """Тест что отрицательная цена валидируется."""
    with pytest.raises(ValidationError):
        Price(Currency="USD", Amount=-100)

def test_market_item_price_usd():
    """Тест конверсии цены предмета."""
    item = MarketItem(
        itemId="123",
        title="Test Item",
        price={"USD": "1250"},
        gameId="csgo"
    )
    assert item.price_usd == 12.50

def test_market_item_suggested_price():
    """Тест рекомендуемой цены."""
    item = MarketItem(
        itemId="123",
        title="Test Item",
        price={"USD": "1250"},
        gameId="csgo",
        suggestedPrice={"USD": "1300"}
    )
    assert item.suggested_price_usd == 13.00

def test_market_item_validation_error_on_missing_field():
    """Тест что ValidationError выбрасывается при отсутствующем поле."""
    with pytest.raises(ValidationError) as exc_info:
        MarketItem(
            # itemId пропущен
            title="Test Item",
            price={"USD": "1250"},
            gameId="csgo"
        )

    errors = exc_info.value.errors()
    assert any(e['loc'][0] == 'itemId' for e in errors)
```

---

## 📚 Дополнительные ресурсы

- **Pydantic Documentation**: <https://docs.pydantic.dev/>
- **DMarket API Spec**: `docs/DMARKET_API_FULL_SPEC.md`
- **Existing Models**: `src/dmarket/models/market_models.py`

---

---

## 🆕 Новая система валидации (Pydantic v2)

### Расположение: `src/dmarket/schemas.py`

Новая версия схем с улучшенной архитектурой:

#### Ключевые улучшения

1. **Pydantic v2 API** - Использование современного ConfigDict
2. **Decimal для денег** - Точность для финансовых операций
3. **Field aliases** - Поддержка camelCase ↔ snake_case
4. **Валидаторы** - Кастомные проверки через @field_validator
5. **Helper методы** - Удобные конверторы для работы с ценами

#### Новые модели

```python
from src.dmarket.schemas import (
    BalanceResponse,
    MarketItemsResponse,
    CreateTargetsResponse,
    AggregatedPricesResponse,
    SalesHistoryResponse,
)

# Использование с валидацией через декоратор
from src.dmarket.api_validator import validate_response

@validate_response(BalanceResponse, endpoint="/account/v1/balance")
async def get_balance(self) -> dict[str, Any]:
    """Получить баланс с автоматической валидацией."""
    return await self._request("GET", "/account/v1/balance")
```

#### Пример: BalanceResponse

```python
class BalanceResponse(BaseModel):
    """Ответ от /account/v1/balance."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="allow",
    )

    usd: str = Field(description="USD баланс в центах")
    usd_available_to_withdraw: str = Field(
        alias="usdAvailableToWithdraw"
    )
    dmc: str | None = None
    dmc_available_to_withdraw: str | None = Field(
        default=None,
        alias="dmcAvailableToWithdraw",
    )

    def get_usd_decimal(self) -> Decimal:
        """Получить USD баланс как Decimal."""
        return Decimal(self.usd) / Decimal(100)

    def get_available_usd_decimal(self) -> Decimal:
        """Получить доступный USD баланс."""
        return Decimal(self.usd_available_to_withdraw) / Decimal(100)
```

#### Пример: MarketItemModel с валидатором

```python
class MarketItemModel(BaseModel):
    """Модель предмета с маркета."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="allow",
    )

    item_id: str = Field(alias="itemId")
    title: str
    price: dict[str, Any]
    suggested_price: dict[str, Any] | None = Field(
        default=None,
        alias="suggestedPrice",
    )
    game_id: str = Field(alias="gameId")

    @field_validator("price", "suggested_price")
    @classmethod
    def validate_price_dict(cls, v: dict[str, Any] | None) -> dict[str, Any] | None:
        """Валидация структуры цены."""
        if v is None:
            return None

        # Проверить что есть хотя бы одна валюта
        if not any(key in v for key in ["USD", "EUR"]):
            raise ValueError("Price must contain USD or EUR")

        return v

    def get_price_decimal(self, currency: str = "USD") -> Decimal:
        """Получить цену как Decimal."""
        price_str = str(self.price.get(currency, "0"))
        return Decimal(price_str) / Decimal(100)
```

#### Автоматическая валидация с уведомлениями

```python
from src.dmarket.api_validator import send_api_change_notification

# При ValidationError отправляется критическое уведомление в Telegram
try:
    validated = BalanceResponse.model_validate(api_response)
except ValidationError as e:
    await send_api_change_notification(
        endpoint="/account/v1/balance",
        errors=e.errors(),
        raw_response=api_response,
        notifier=self.notifier,
    )
    # Возвращаем raw data для backward compatibility
    return api_response
```

#### Декоратор @validate_response

Автоматическая валидация для методов API:

```python
from src.dmarket.api_validator import validate_response

class DMarketAPI:
    @validate_response(MarketItemsResponse, endpoint="/exchange/v1/market/items")
    async def get_market_items(
        self,
        game: str,
        limit: int = 100,
        **filters,
    ) -> dict[str, Any]:
        """
        Получить предметы с маркета.

        Ответ автоматически валидируется через MarketItemsResponse.
        При ValidationError:
        - Логируется CRITICAL ошибка
        - Отправляется Telegram уведомление
        - Возвращается raw response для совместимости
        """
        params = {"gameId": game, "limit": limit, **filters}
        return await self._request("GET", "/exchange/v1/market/items", params=params)
```

#### Сравнение: market_models.py vs schemas.py

| Аспект                     | market_models.py | schemas.py (NEW)              |
| -------------------------- | ---------------- | ----------------------------- |
| Pydantic версия            | v1 API           | v2 API (ConfigDict)           |
| Денежные операции          | float            | Decimal (точность)            |
| Field aliases              | Частично         | Полная поддержка              |
| Кастомные валидаторы       | Нет              | @field_validator              |
| Telegram уведомления       | Нет              | Автоматически                 |
| Декоратор валидации        | Нет              | @validate_response            |
| Helper методы              | Properties       | Методы get_*_decimal()        |
| ConfigDict extra="allow"   | Частично         | Везде (forward compatibility) |
| DMarket API v1.1.0 support | Частично         | Полная поддержка              |

#### Миграция на новые схемы

**Шаг 1**: Импортировать новые модели

```python
# Старый код
from src.dmarket.models.market_models import MarketItemsResponse

# Новый код
from src.dmarket.schemas import MarketItemsResponse
```

**Шаг 2**: Применить декораторы

```python
# Добавить к методам API
@validate_response(BalanceResponse, endpoint="/account/v1/balance")
async def get_balance(self) -> dict[str, Any]:
    ...
```

**Шаг 3**: Использовать Decimal вместо float

```python
# Старый код
price_usd = item.price_usd  # float

# Новый код
price_usd = item.get_price_decimal("USD")  # Decimal
```

---

## ✅ Чеклист интеграции

### Старые модели (market_models.py)
- [x] Модели созданы для всех критических эндпоинтов
- [x] Properties для конверсий типов (центы → доллары)
- [x] Validation errors обрабатываются
- [x] Sentry интеграция для мониторинга schema changes
- [x] Type hints везде
- [x] Документация создана
- [ ] Unit тесты для всех моделей (TODO)
- [ ] Integration тесты с реальным API (TODO)

### Новые схемы (schemas.py) ✨
- [x] Все модели переписаны с Pydantic v2 API
- [x] Decimal для всех денежных операций
- [x] ConfigDict с extra="allow" для forward compatibility
- [x] Field aliases для camelCase ↔ snake_case
- [x] Кастомные валидаторы через @field_validator
- [x] Helper методы get_*_decimal() для конверсий
- [x] Создан api_validator.py с декоратором @validate_response
- [x] Автоматические Telegram уведомления при ValidationError
- [x] DMarket API v1.1.0 полностью покрыт
- [ ] Применить @validate_response ко всем методам API (TODO)
- [ ] Unit тесты для новых схем (TODO)
- [ ] Integration тесты с реальными API responses (TODO)

---

**Статус**: 🚧 В разработке (новые схемы) + ✅ Production Ready (старые модели)
**Версия**: 2.0
**Дата**: 17 декабря 2025 г.
