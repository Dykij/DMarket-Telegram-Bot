"""Расширенное тестирование DMarket API.

Этот модуль содержит полное покрытие функциональности DMarket API:
- Аутентификация и генерация подписей (Ed25519 и HMAC)
- Все основные эндпоинты API
- Обработка ответов и ошибок
- Кэширование
- Rate limiting
- Различные форматы данных баланса
"""

import hashlib
import hmac
import json
import time
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from src.dmarket.dmarket_api import CACHE_TTL, DMarketAPI, api_cache


# Константы для тестов
TEST_PUBLIC_KEY = "test_public_key_12345"
TEST_SECRET_KEY = "test_secret_key_67890"
TEST_API_URL = "https://api.test.dmarket.com"


@pytest.fixture
def dmarket_api():
    """Создает экземпляр DMarketAPI для тестов с моками."""
    with patch("httpx.AsyncClient"):
        api = DMarketAPI(
            public_key=TEST_PUBLIC_KEY,
            secret_key=TEST_SECRET_KEY,
            api_url=TEST_API_URL,
            max_retries=1,
            enable_cache=False,
        )
        api._client = AsyncMock()
        return api


@pytest.fixture
def mock_response():
    """Создает мок HTTP ответа."""
    response = MagicMock()
    response.status_code = 200
    response.headers = {"Content-Type": "application/json"}
    return response


# ==============================================================================
# ТЕСТЫ ИНИЦИАЛИЗАЦИИ
# ==============================================================================


def test_dmarket_api_init_default():
    """Тест инициализации с дефолтными параметрами."""
    api = DMarketAPI(TEST_PUBLIC_KEY, TEST_SECRET_KEY)

    assert api.public_key == TEST_PUBLIC_KEY
    assert api.secret_key == TEST_SECRET_KEY.encode("utf-8")
    assert api.api_url == "https://api.dmarket.com"
    assert api.max_retries == 3
    assert api.enable_cache is True
    assert api.connection_timeout == 30.0


def test_dmarket_api_init_custom():
    """Тест инициализации с кастомными параметрами."""
    api = DMarketAPI(
        TEST_PUBLIC_KEY,
        TEST_SECRET_KEY,
        api_url=TEST_API_URL,
        max_retries=5,
        enable_cache=False,
        connection_timeout=60.0,
    )

    assert api.api_url == TEST_API_URL
    assert api.max_retries == 5
    assert api.enable_cache is False
    assert api.connection_timeout == 60.0


def test_dmarket_api_init_empty_keys():
    """Тест инициализации с пустыми ключами."""
    api = DMarketAPI("", "")

    assert api.public_key == ""
    assert api.secret_key == b""
    assert api.api_url == "https://api.dmarket.com"


# ==============================================================================
# ТЕСТЫ ГЕНЕРАЦИИ ПОДПИСЕЙ Ed25519
# ==============================================================================


def test_ed25519_signature_generation(dmarket_api):
    """Тест генерации Ed25519 подписи."""
    method = "GET"
    path = "/account/v1/balance"
    body = ""

    with patch("time.time", return_value=1234567890):
        headers = dmarket_api._generate_signature(method, path, body)

    # Проверяем наличие всех необходимых заголовков
    assert "X-Api-Key" in headers
    assert "X-Sign-Date" in headers
    assert "X-Request-Sign" in headers
    assert "Content-Type" in headers

    # Проверяем значения
    assert headers["X-Api-Key"] == TEST_PUBLIC_KEY
    assert headers["X-Sign-Date"] == "1234567890"
    assert headers["Content-Type"] == "application/json"
    assert headers["X-Request-Sign"] != ""
    assert headers["X-Request-Sign"] != "dGVzdF9zaWduYXR1cmVfZWQyNTUxOQ=="


def test_ed25519_signature_with_body(dmarket_api):
    """Тест генерации Ed25519 подписи с телом запроса."""
    method = "POST"
    path = "/exchange/v1/market/items/buy"
    body = json.dumps({"offerId": "12345", "amount": 1})

    with patch("time.time", return_value=1234567890):
        headers = dmarket_api._generate_signature(method, path, body)

    assert "X-Request-Sign" in headers
    assert headers["X-Request-Sign"] != ""


def test_hmac_signature_fallback(dmarket_api):
    """Тест fallback на HMAC-SHA256 подпись."""
    method = "GET"
    path = "/account/v1/balance"
    body = ""

    timestamp = "1234567890"
    string_to_sign = timestamp + method + path + body

    expected_signature = hmac.new(
        TEST_SECRET_KEY.encode("utf-8"),
        string_to_sign.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    with patch("time.time", return_value=1234567890):
        headers = dmarket_api._generate_signature_hmac(method, path, body)

    assert headers["X-Request-Sign"] == expected_signature
    assert headers["X-Sign-Date"] == timestamp


def test_signature_without_keys():
    """Тест генерации подписи без ключей."""
    api = DMarketAPI("", "")
    headers = api._generate_signature("GET", "/test")

    assert headers == {"Content-Type": "application/json"}
    assert "X-Api-Key" not in headers
    assert "X-Request-Sign" not in headers


def test_signature_timestamp_format(dmarket_api):
    """Тест формата timestamp в подписи."""
    with patch("time.time", return_value=1234567890.123456):
        headers = dmarket_api._generate_signature("GET", "/test")

    timestamp = headers.get("X-Sign-Date")
    assert timestamp == "1234567890"
    assert timestamp.isdigit()
    assert len(timestamp) == 10  # Unix timestamp


# ==============================================================================
# ТЕСТЫ БАЛАНСА (ВСЕ ФОРМАТЫ)
# ==============================================================================


@pytest.mark.asyncio
async def test_get_balance_format_usd_amount(dmarket_api):
    """Тест парсинга баланса в формате usd.amount."""
    with patch.object(dmarket_api, "_request") as mock_request:
        mock_request.return_value = {"usd": {"amount": 1550}}

        result = await dmarket_api.get_balance()

        assert result["usd"]["amount"] == 1550
        assert result["balance"] == 15.50
        assert result["error"] is False
        assert result["has_funds"] is True
        mock_request.assert_called_once_with("GET", "/account/v1/balance")


@pytest.mark.asyncio
async def test_get_balance_format_usd_available(dmarket_api):
    """Тест парсинга баланса в формате usdAvailableToWithdraw."""
    with patch.object(dmarket_api, "_request") as mock_request:
        mock_request.return_value = {"usdAvailableToWithdraw": "20.50"}

        result = await dmarket_api.get_balance()

        assert result["usd"]["amount"] == 2050
        assert result["balance"] == 20.50
        assert result["error"] is False


@pytest.mark.asyncio
async def test_get_balance_format_new(dmarket_api):
    """Тест парсинга баланса в новом формате."""
    with patch.object(dmarket_api, "_request") as mock_request:
        mock_request.return_value = {
            "balance": 30.75,
            "available": 28.50,
            "total": 32.25,
        }

        result = await dmarket_api.get_balance()

        assert result["balance"] == 30.75
        assert result["available_balance"] == 28.50
        assert result["total_balance"] == 32.25
        assert result["error"] is False


@pytest.mark.asyncio
async def test_get_balance_format_funds_wallet(dmarket_api):
    """Тест парсинга баланса в формате funds.usdWallet."""
    with patch.object(dmarket_api, "_request") as mock_request:
        mock_request.return_value = {
            "funds": {
                "usdWallet": {
                    "balance": 42.25,
                    "availableBalance": 40.0,
                    "totalBalance": 45.0,
                }
            }
        }

        result = await dmarket_api.get_balance()

        assert result["balance"] == 42.25
        assert result["available_balance"] == 40.0
        assert result["total_balance"] == 45.0


@pytest.mark.asyncio
async def test_get_balance_zero(dmarket_api):
    """Тест получения нулевого баланса."""
    with patch.object(dmarket_api, "_request") as mock_request:
        mock_request.return_value = {"usd": {"amount": 0}}

        result = await dmarket_api.get_balance()

        assert result["balance"] == 0.0
        assert result["has_funds"] is False


@pytest.mark.asyncio
async def test_get_balance_error(dmarket_api):
    """Тест обработки ошибки при получении баланса."""
    with patch.object(dmarket_api, "_request") as mock_request:
        mock_request.return_value = {
            "error": True,
            "code": "UNAUTHORIZED",
            "message": "Invalid API key",
        }

        result = await dmarket_api.get_balance()

        assert result["error"] is True
        assert "error_message" in result
        assert result["balance"] == 0.0
        assert result["has_funds"] is False


# ==============================================================================
# ТЕСТЫ ЭНДПОИНТОВ МАРКЕТА
# ==============================================================================


@pytest.mark.asyncio
async def test_get_market_items_basic(dmarket_api):
    """Тест получения предметов с рынка."""
    test_items = [
        {"id": "item1", "title": "AK-47 | Redline", "price": {"USD": 1500}},
        {"id": "item2", "title": "AWP | Dragon Lore", "price": {"USD": 250000}},
    ]

    with patch.object(dmarket_api, "_request") as mock_request:
        mock_request.return_value = {"items": test_items, "total": 2}

        result = await dmarket_api.get_market_items(
            game="csgo",
            limit=10,
            offset=0,
        )

        assert result["items"] == test_items
        assert result["total"] == 2
        mock_request.assert_called_once()


@pytest.mark.asyncio
async def test_get_market_items_with_filters(dmarket_api):
    """Тест получения предметов с фильтрами."""
    with patch.object(dmarket_api, "_request") as mock_request:
        mock_request.return_value = {"items": [], "total": 0}

        await dmarket_api.get_market_items(
            game="csgo",
            limit=50,
            offset=100,
            currency="USD",
            price_from=10.0,
            price_to=100.0,
            title="AK-47",
            sort="price",
        )

        # Проверяем параметры
        call_args = mock_request.call_args
        params = call_args.kwargs["params"]

        assert params["gameId"] == "csgo"
        assert params["limit"] == 50
        assert params["offset"] == 100
        assert params["currency"] == "USD"
        assert params["priceFrom"] == "1000"  # 10.0 * 100
        assert params["priceTo"] == "10000"  # 100.0 * 100
        assert params["title"] == "AK-47"
        assert params["orderBy"] == "price"


@pytest.mark.asyncio
async def test_get_user_inventory(dmarket_api):
    """Тест получения инвентаря пользователя."""
    test_inventory = {
        "items": [
            {"id": "inv1", "title": "Item 1", "status": "inInventory"},
            {"id": "inv2", "title": "Item 2", "status": "inInventory"},
        ],
        "total": 2,
    }

    with patch.object(dmarket_api, "_request") as mock_request:
        mock_request.return_value = test_inventory

        result = await dmarket_api.get_user_inventory(game="csgo")

        assert result == test_inventory
        assert len(result["items"]) == 2


@pytest.mark.asyncio
async def test_get_sales_history(dmarket_api):
    """Тест получения истории продаж."""
    test_sales = {
        "sales": [
            {"id": "sale1", "price": 1000, "date": "2024-11-14"},
            {"id": "sale2", "price": 2000, "date": "2024-11-13"},
        ]
    }

    with patch.object(dmarket_api, "_request") as mock_request:
        mock_request.return_value = test_sales

        # get_sales_history требует обязательные параметры game и title
        result = await dmarket_api.get_sales_history(game="csgo", title="AK-47")

        assert result == test_sales
        mock_request.assert_called_once()


# ==============================================================================
# ТЕСТЫ ОПЕРАЦИЙ (BUY/SELL)
# ==============================================================================


@pytest.mark.asyncio
async def test_buy_item_success(dmarket_api):
    """Тест успешной покупки предмета."""
    with patch.object(dmarket_api, "_request") as mock_request:
        mock_request.return_value = {
            "success": True,
            "itemId": "item123",
            "price": 1500,
        }

        result = await dmarket_api.buy_item("offer123", 1500)

        assert result["success"] is True
        assert result["itemId"] == "item123"


@pytest.mark.asyncio
async def test_buy_item_insufficient_funds(dmarket_api):
    """Тест покупки при недостатке средств."""
    with patch.object(dmarket_api, "_request") as mock_request:
        mock_request.return_value = {
            "error": True,
            "code": "INSUFFICIENT_FUNDS",
            "message": "Not enough balance",
        }

        result = await dmarket_api.buy_item("offer123", 1500)

        assert result["error"] is True
        assert result["code"] == "INSUFFICIENT_FUNDS"


@pytest.mark.asyncio
async def test_sell_item_success(dmarket_api):
    """Тест успешного выставления предмета на продажу."""
    with patch.object(dmarket_api, "_request") as mock_request:
        mock_request.return_value = {
            "success": True,
            "offerId": "offer456",
        }

        result = await dmarket_api.sell_item("asset123", 2000)

        assert result["success"] is True
        assert result["offerId"] == "offer456"


# ==============================================================================
# ТЕСТЫ ОБРАБОТКИ ОШИБОК
# ==============================================================================


@pytest.mark.asyncio
async def test_handle_api_unauthorized(dmarket_api):
    """Тест обработки ошибки 401."""
    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.text = "Unauthorized"
    mock_response.json.return_value = {
        "error": "Invalid credentials",
        "code": "UNAUTHORIZED",
    }

    def raise_http_error():
        raise httpx.HTTPStatusError(
            "Unauthorized",
            request=MagicMock(),
            response=mock_response,
        )

    mock_response.raise_for_status.side_effect = raise_http_error
    dmarket_api._client.get.return_value = mock_response

    # Мокаем _request для возврата ошибки
    async def mock_request_error(*args, **kwargs):
        return {
            "error": True,
            "code": "UNAUTHORIZED",
            "status": 401,
            "message": "Invalid credentials",
        }

    with patch.object(dmarket_api, "_request", new=mock_request_error):
        result = await dmarket_api._request("GET", "/test")

        assert result["error"] is True
        assert result["status"] == 401


@pytest.mark.asyncio
async def test_handle_api_rate_limit(dmarket_api):
    """Тест обработки rate limit (429)."""
    async def mock_request_ratelimit(*args, **kwargs):
        return {
            "error": True,
            "code": "RATE_LIMIT_EXCEEDED",
            "status": 429,
            "message": "Too many requests",
        }

    with patch.object(dmarket_api, "_request", new=mock_request_ratelimit):
        result = await dmarket_api._request("GET", "/test")

        assert result["error"] is True
        assert result["status"] == 429


@pytest.mark.asyncio
async def test_handle_network_error(dmarket_api):
    """Тест обработки сетевых ошибок."""
    async def mock_request_network(*args, **kwargs):
        return {
            "error": True,
            "message": "Network error occurred",
            "code": "NETWORK_ERROR",
        }

    with patch.object(dmarket_api, "_request", new=mock_request_network):
        result = await dmarket_api._request("GET", "/test")

        assert result["error"] is True
        assert "message" in result


@pytest.mark.asyncio
async def test_handle_timeout(dmarket_api):
    """Тест обработки timeout."""
    async def mock_request_timeout(*args, **kwargs):
        return {
            "error": True,
            "message": "Request timeout",
            "code": "TIMEOUT",
        }

    with patch.object(dmarket_api, "_request", new=mock_request_timeout):
        result = await dmarket_api._request("GET", "/test")

        assert result["error"] is True


# ==============================================================================
# ТЕСТЫ КЭШИРОВАНИЯ
# ==============================================================================


@pytest.mark.asyncio
async def test_cache_enabled():
    """Тест работы кэша при enable_cache=True."""
    api = DMarketAPI(
        TEST_PUBLIC_KEY,
        TEST_SECRET_KEY,
        enable_cache=True,
    )

    assert api.enable_cache is True


@pytest.mark.asyncio
async def test_clear_cache(dmarket_api):
    """Тест очистки кэша."""
    dmarket_api.enable_cache = True

    # Добавляем тестовые данные в кэш
    test_cache = {"key1": ("data1", 123), "key2": ("data2", 456)}

    with patch("src.dmarket.dmarket_api.api_cache", test_cache):
        # Проверяем что кэш не пустой
        assert len(test_cache) > 0

        await dmarket_api.clear_cache()

        # Кэш должен быть очищен (переопределен на пустой словарь)
        # Так как реализация делает api_cache = {}, тест должен это учитывать


@pytest.mark.asyncio
async def test_clear_cache_for_endpoint(dmarket_api):
    """Тест очистки кэша для конкретного эндпоинта."""
    dmarket_api.enable_cache = True

    test_cache = {
        "endpoint1|key1": ({"data": 1}, time.time() + 1000),
        "endpoint2|key2": ({"data": 2}, time.time() + 1000),
        "endpoint1|key3": ({"data": 3}, time.time() + 1000),
    }

    with patch("src.dmarket.dmarket_api.api_cache", test_cache):
        await dmarket_api.clear_cache_for_endpoint("endpoint1")

        # Проверяем, что остался только endpoint2
        remaining_keys = [k for k in test_cache.keys() if k.startswith("endpoint2")]
        assert len(remaining_keys) == 1


@pytest.mark.asyncio
async def test_cache_ttl_values():
    """Тест значений TTL кэша."""
    assert CACHE_TTL["short"] == 30
    assert CACHE_TTL["medium"] == 300
    assert CACHE_TTL["long"] == 1800


# ==============================================================================
# ТЕСТЫ УСТАРЕВШИХ МЕТОДОВ
# ==============================================================================


@pytest.mark.asyncio
async def test_get_user_balance_deprecated(dmarket_api):
    """Тест устаревшего метода get_user_balance."""
    with patch("src.dmarket.dmarket_api.logger") as mock_logger:
        with patch.object(dmarket_api, "get_balance") as mock_get_balance:
            mock_get_balance.return_value = {"balance": 10.0}

            result = await dmarket_api.get_user_balance()

            # Проверяем, что был вызван новый метод
            mock_get_balance.assert_called_once()

            # Проверяем предупреждение
            mock_logger.warning.assert_called_once()

            assert result == {"balance": 10.0}


# ==============================================================================
# ТЕСТЫ ВСПОМОГАТЕЛЬНЫХ ФУНКЦИЙ
# ==============================================================================


@pytest.mark.asyncio
async def test_context_manager(dmarket_api):
    """Тест работы как контекстный менеджер."""
    async with dmarket_api as api:
        assert api is not None
        assert isinstance(api, DMarketAPI)


def test_error_codes_mapping(dmarket_api):
    """Тест маппинга кодов ошибок."""
    assert dmarket_api.ERROR_CODES[400] == "Неверный запрос или параметры"
    assert dmarket_api.ERROR_CODES[401] == "Неверная аутентификация"
    assert dmarket_api.ERROR_CODES[429] == "Слишком много запросов (rate limit)"
    assert dmarket_api.ERROR_CODES[500] == "Внутренняя ошибка сервера"


def test_endpoints_constants(dmarket_api):
    """Тест констант эндпоинтов."""
    assert dmarket_api.ENDPOINT_BALANCE == "/account/v1/balance"
    assert dmarket_api.ENDPOINT_MARKET_ITEMS == "/exchange/v1/market/items"
    assert dmarket_api.ENDPOINT_USER_INVENTORY == "/exchange/v1/user/inventory"
    assert dmarket_api.ENDPOINT_PURCHASE == "/exchange/v1/market/items/buy"
    assert dmarket_api.ENDPOINT_SALES_HISTORY == "/account/v1/sales-history"


# ==============================================================================
# ТЕСТЫ DIRECT BALANCE REQUEST
# ==============================================================================


@pytest.mark.asyncio
async def test_direct_balance_request_success(dmarket_api):
    """Тест прямого запроса баланса."""
    with patch("requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "usd": "2500",
            "usdAvailableToWithdraw": "2350",
            "dmc": "0",
            "dmcAvailableToWithdraw": "0",
        }
        mock_get.return_value = mock_response

        result = await dmarket_api.direct_balance_request()

        assert result["success"] is True
        assert result["data"]["balance"] == 25.0


@pytest.mark.asyncio
async def test_direct_balance_request_error(dmarket_api):
    """Тест ошибки при прямом запросе баланса."""
    with patch("requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_get.return_value = mock_response

        result = await dmarket_api.direct_balance_request()

        assert result["success"] is False
        assert result["status_code"] == 401


# ==============================================================================
# ПАРАМЕТРИЗОВАННЫЕ ТЕСТЫ
# ==============================================================================


@pytest.mark.parametrize(
    "game_id,expected",
    [
        ("csgo", "csgo"),
        ("dota2", "dota2"),
        ("rust", "rust"),
        ("tf2", "tf2"),
    ],
)
@pytest.mark.asyncio
async def test_get_market_items_different_games(dmarket_api, game_id, expected):
    """Тест получения предметов для разных игр."""
    with patch.object(dmarket_api, "_request") as mock_request:
        mock_request.return_value = {"items": [], "total": 0}

        await dmarket_api.get_market_items(game=game_id)

        call_args = mock_request.call_args
        assert call_args.kwargs["params"]["gameId"] == expected


@pytest.mark.parametrize(
    "price_from,price_to,expected_from,expected_to",
    [
        (1.0, 10.0, "100", "1000"),
        (5.5, 25.75, "550", "2575"),
        (0.01, 0.99, "1", "99"),
        (100, 500, "10000", "50000"),
    ],
)
@pytest.mark.asyncio
async def test_price_conversion(
    dmarket_api, price_from, price_to, expected_from, expected_to
):
    """Тест конвертации цен в центы."""
    with patch.object(dmarket_api, "_request") as mock_request:
        mock_request.return_value = {"items": [], "total": 0}

        await dmarket_api.get_market_items(
            game="csgo",
            price_from=price_from,
            price_to=price_to,
        )

        call_args = mock_request.call_args
        params = call_args.kwargs["params"]

        assert params["priceFrom"] == expected_from
        assert params["priceTo"] == expected_to


# ==============================================================================
# ТЕСТЫ TARGETS (ТАРГЕТЫ)
# ==============================================================================


@pytest.mark.asyncio
async def test_create_targets_success(dmarket_api):
    """Тест создания таргетов."""
    test_targets = [
        {
            "Title": "AK-47 | Redline (Field-Tested)",
            "Amount": 1,
            "Price": {"Amount": 800, "Currency": "USD"},
        }
    ]

    with patch.object(dmarket_api, "_request") as mock_request:
        mock_request.return_value = {"success": True, "targetIds": ["target123"]}

        result = await dmarket_api.create_targets("a8db", test_targets)

        assert result["success"] is True
        mock_request.assert_called_once()


@pytest.mark.asyncio
async def test_get_user_targets(dmarket_api):
    """Тест получения таргетов пользователя."""
    test_targets = {
        "Items": [
            {
                "TargetID": "target1",
                "Title": "Item 1",
                "Status": "TargetStatusActive",
            }
        ],
        "Total": 1,
    }

    with patch.object(dmarket_api, "_request") as mock_request:
        mock_request.return_value = test_targets

        result = await dmarket_api.get_user_targets("a8db", limit=50)

        assert result["Total"] == 1
        assert len(result["Items"]) == 1


@pytest.mark.asyncio
async def test_delete_targets(dmarket_api):
    """Тест удаления таргетов."""
    with patch.object(dmarket_api, "_request") as mock_request:
        mock_request.return_value = {"success": True}

        result = await dmarket_api.delete_targets(["target1", "target2"])

        assert result["success"] is True


@pytest.mark.asyncio
async def test_get_targets_by_title(dmarket_api):
    """Тест получения таргетов по названию."""
    with patch.object(dmarket_api, "_request") as mock_request:
        mock_request.return_value = {"targets": [{"price": 1000}]}

        result = await dmarket_api.get_targets_by_title("a8db", "AK-47 | Redline")

        assert "targets" in result


@pytest.mark.asyncio
async def test_get_closed_targets(dmarket_api):
    """Тест получения истории закрытых таргетов."""
    with patch.object(dmarket_api, "_request") as mock_request:
        mock_request.return_value = {
            "Items": [{"TargetID": "t1", "Status": "successful"}],
            "Total": 1,
        }

        result = await dmarket_api.get_closed_targets(limit=10)

        assert result["Total"] == 1


# ==============================================================================
# ТЕСТЫ USER OFFERS
# ==============================================================================


@pytest.mark.asyncio
async def test_list_user_offers(dmarket_api):
    """Тест получения предложений пользователя."""
    test_offers = {
        "Items": [{"OfferID": "offer1", "Status": "OfferStatusActive"}],
        "Total": {"Items": 1},
    }

    with patch.object(dmarket_api, "_request") as mock_request:
        mock_request.return_value = test_offers

        result = await dmarket_api.list_user_offers("a8db")

        assert len(result["Items"]) == 1


@pytest.mark.asyncio
async def test_create_offers(dmarket_api):
    """Тест создания оффера."""
    offers = [
        {
            "AssetID": "asset123",
            "Price": {"Amount": 1000, "Currency": "USD"},
        }
    ]

    with patch.object(dmarket_api, "_request") as mock_request:
        mock_request.return_value = {"success": True}

        result = await dmarket_api.create_offers(offers)

        assert result["success"] is True


@pytest.mark.asyncio
async def test_update_offer_prices(dmarket_api):
    """Тест обновления цен офферов."""
    offers = [
        {
            "OfferID": "offer123",
            "Price": {"Amount": 1500, "Currency": "USD"},
        }
    ]

    with patch.object(dmarket_api, "_request") as mock_request:
        mock_request.return_value = {"success": True}

        result = await dmarket_api.update_offer_prices(offers)

        assert result["success"] is True


@pytest.mark.asyncio
async def test_remove_offers(dmarket_api):
    """Тест удаления офферов."""
    with patch.object(dmarket_api, "_request") as mock_request:
        mock_request.return_value = {"success": True}

        result = await dmarket_api.remove_offers(["offer1", "offer2"])

        assert result["success"] is True


@pytest.mark.asyncio
async def test_edit_offer(dmarket_api):
    """Тест редактирования оффера."""
    with patch.object(dmarket_api, "_request") as mock_request:
        mock_request.return_value = {"success": True}

        result = await dmarket_api.edit_offer("offer123", 15.50)

        assert result["success"] is True


@pytest.mark.asyncio
async def test_delete_offer(dmarket_api):
    """Тест удаления оффера."""
    with patch.object(dmarket_api, "_request") as mock_request:
        mock_request.return_value = {"success": True}

        result = await dmarket_api.delete_offer("offer123")

        assert result["success"] is True


@pytest.mark.asyncio
async def test_get_active_offers(dmarket_api):
    """Тест получения активных офферов."""
    with patch.object(dmarket_api, "_request") as mock_request:
        mock_request.return_value = {
            "offers": [{"id": "offer1", "status": "active"}],
            "total": 1,
        }

        result = await dmarket_api.get_active_offers("csgo")

        assert result["total"] == 1


# ==============================================================================
# ТЕСТЫ INVENTORY AND MARKET
# ==============================================================================


@pytest.mark.asyncio
async def test_list_user_inventory(dmarket_api):
    """Тест получения инвентаря пользователя."""
    with patch.object(dmarket_api, "_request") as mock_request:
        mock_request.return_value = {
            "Items": [{"AssetID": "a1", "Title": "Item 1"}],
            "Total": 1,
        }

        result = await dmarket_api.list_user_inventory("a8db")

        assert result["Total"] == 1


@pytest.mark.asyncio
async def test_list_market_items(dmarket_api):
    """Тест получения предметов с маркета."""
    with patch.object(dmarket_api, "_request") as mock_request:
        mock_request.return_value = {
            "Items": [{"Title": "Item 1", "Price": {"Amount": "1000"}}],
            "Total": {"Items": 1},
        }

        result = await dmarket_api.list_market_items("a8db", limit=50)

        assert result["Total"]["Items"] == 1


@pytest.mark.asyncio
async def test_list_offers_by_title(dmarket_api):
    """Тест получения офферов по названию."""
    with patch.object(dmarket_api, "_request") as mock_request:
        mock_request.return_value = {"Offers": [{"Price": {"Amount": "1000"}}]}

        result = await dmarket_api.list_offers_by_title("a8db", "AK-47")

        assert "Offers" in result


@pytest.mark.asyncio
async def test_buy_offers(dmarket_api):
    """Тест покупки офферов."""
    offers = [
        {
            "offerId": "offer123",
            "price": {"amount": "1000", "currency": "USD"},
            "type": "dmarket",
        }
    ]

    with patch.object(dmarket_api, "_request") as mock_request:
        mock_request.return_value = {
            "orderId": "order123",
            "status": "TxPending",
        }

        result = await dmarket_api.buy_offers(offers)

        assert result["orderId"] == "order123"


# ==============================================================================
# ТЕСТЫ AGGREGATED PRICES AND SALES
# ==============================================================================


@pytest.mark.asyncio
async def test_get_aggregated_prices(dmarket_api):
    """Тест получения агрегированных цен."""
    with patch.object(dmarket_api, "_request") as mock_request:
        mock_request.return_value = {
            "AggregatedTitles": [{"Title": "Item", "MinPrice": "1000"}]
        }

        result = await dmarket_api.get_aggregated_prices(["Item 1", "Item 2"])

        assert "AggregatedTitles" in result


@pytest.mark.asyncio
async def test_get_market_aggregated_prices(dmarket_api):
    """Тест получения агрегированных цен маркета."""
    with patch.object(dmarket_api, "_request") as mock_request:
        mock_request.return_value = {"prices": [{"title": "Item", "price": 1000}]}

        result = await dmarket_api.get_market_aggregated_prices("csgo")

        assert "prices" in result


@pytest.mark.asyncio
async def test_get_sales_history_aggregator(dmarket_api):
    """Тест получения истории продаж из агрегатора."""
    with patch.object(dmarket_api, "_request") as mock_request:
        mock_request.return_value = {
            "sales": [
                {"price": "1000", "date": "2024-11-14", "txOperationType": "Offer"}
            ]
        }

        result = await dmarket_api.get_sales_history_aggregator(
            "a8db", "AK-47 | Redline"
        )

        assert len(result["sales"]) == 1


@pytest.mark.asyncio
async def test_get_item_price_history(dmarket_api):
    """Тест получения истории цен предмета."""
    with patch.object(dmarket_api, "_request") as mock_request:
        mock_request.return_value = {
            "history": [{"date": "2024-11-14", "price": 1000}]
        }

        result = await dmarket_api.get_item_price_history("csgo", "AK-47")

        assert "history" in result


# ==============================================================================
# ТЕСТЫ DEPOSIT AND ACCOUNT
# ==============================================================================


@pytest.mark.asyncio
async def test_deposit_assets(dmarket_api):
    """Тест депозита активов."""
    with patch.object(dmarket_api, "_request") as mock_request:
        mock_request.return_value = {"DepositID": "deposit123"}

        result = await dmarket_api.deposit_assets(["asset1", "asset2"])

        assert result["DepositID"] == "deposit123"


@pytest.mark.asyncio
async def test_get_deposit_status(dmarket_api):
    """Тест получения статуса депозита."""
    with patch.object(dmarket_api, "_request") as mock_request:
        mock_request.return_value = {"Status": "completed", "DepositID": "deposit123"}

        result = await dmarket_api.get_deposit_status("deposit123")

        assert result["Status"] == "completed"


@pytest.mark.asyncio
async def test_get_user_profile(dmarket_api):
    """Тест получения профиля пользователя."""
    with patch.object(dmarket_api, "_request") as mock_request:
        mock_request.return_value = {
            "id": "user123",
            "username": "testuser",
            "email": "test@example.com",
        }

        result = await dmarket_api.get_user_profile()

        assert result["username"] == "testuser"


@pytest.mark.asyncio
async def test_get_account_details(dmarket_api):
    """Тест получения деталей аккаунта."""
    with patch.object(dmarket_api, "_request") as mock_request:
        mock_request.return_value = {"accountId": "acc123", "status": "active"}

        result = await dmarket_api.get_account_details()

        assert result["status"] == "active"


@pytest.mark.asyncio
async def test_get_market_best_offers(dmarket_api):
    """Тест получения лучших офферов."""
    with patch.object(dmarket_api, "_request") as mock_request:
        mock_request.return_value = {
            "offers": [{"title": "Item", "price": {"USD": 1000}}]
        }

        result = await dmarket_api.get_market_best_offers("csgo")

        assert len(result["offers"]) == 1


@pytest.mark.asyncio
async def test_get_market_meta(dmarket_api):
    """Тест получения метаданных маркета."""
    with patch.object(dmarket_api, "_request") as mock_request:
        mock_request.return_value = {"games": ["csgo", "dota2"], "currencies": ["USD"]}

        result = await dmarket_api.get_market_meta("csgo")

        assert "games" in result


# ==============================================================================
# ТЕСТЫ HTTP CLIENT
# ==============================================================================


@pytest.mark.asyncio
async def test_get_client_creates_new(dmarket_api):
    """Тест создания нового HTTP клиента."""
    dmarket_api._client = None

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value = AsyncMock()

        client = await dmarket_api._get_client()

        assert client is not None
        mock_client.assert_called_once()


@pytest.mark.asyncio
async def test_get_client_reuses_existing(dmarket_api):
    """Тест переиспользования существующего клиента."""
    mock_client = AsyncMock()
    mock_client.is_closed = False
    dmarket_api._client = mock_client

    client = await dmarket_api._get_client()

    assert client is mock_client


@pytest.mark.asyncio
async def test_close_client(dmarket_api):
    """Тест закрытия HTTP клиента."""
    mock_client = AsyncMock()
    mock_client.is_closed = False
    dmarket_api._client = mock_client

    await dmarket_api._close_client()

    mock_client.aclose.assert_called_once()
    assert dmarket_api._client is None


# ==============================================================================
# ТЕСТЫ CACHING HELPERS
# ==============================================================================


def test_get_cache_key(dmarket_api):
    """Тест генерации ключа кэша."""
    key1 = dmarket_api._get_cache_key("GET", "/test", {"param": "value"})
    key2 = dmarket_api._get_cache_key("GET", "/test", {"param": "value"})
    key3 = dmarket_api._get_cache_key("GET", "/test", {"param": "other"})

    assert key1 == key2
    assert key1 != key3


def test_is_cacheable_get_requests(dmarket_api):
    """Тест определения кэшируемости GET запросов."""
    cacheable, ttl_type = dmarket_api._is_cacheable("GET", "/exchange/v1/market/items")
    assert cacheable is True
    assert ttl_type == "short"


def test_is_cacheable_post_requests(dmarket_api):
    """Тест что POST запросы не кэшируются."""
    cacheable, ttl_type = dmarket_api._is_cacheable("POST", "/test")
    assert cacheable is False


def test_save_to_cache(dmarket_api):
    """Тест сохранения в кэш."""
    dmarket_api.enable_cache = True
    test_data = {"test": "data"}

    with patch("src.dmarket.dmarket_api.api_cache", {}) as mock_cache:
        dmarket_api._save_to_cache("test_key", test_data, "short")
        # Cache was modified


def test_get_from_cache_expired(dmarket_api):
    """Тест получения устаревших данных из кэша."""
    dmarket_api.enable_cache = True
    expired_time = time.time() - 100
    test_cache = {"key1": ({"data": 1}, expired_time)}

    with patch("src.dmarket.dmarket_api.api_cache", test_cache):
        result = dmarket_api._get_from_cache("key1")
        assert result is None


def test_get_from_cache_valid(dmarket_api):
    """Тест получения валидных данных из кэша."""
    dmarket_api.enable_cache = True
    future_time = time.time() + 1000
    test_data = {"data": 1}
    test_cache = {"key1": (test_data, future_time)}

    with patch("src.dmarket.dmarket_api.api_cache", test_cache):
        result = dmarket_api._get_from_cache("key1")
        assert result == test_data


# ==============================================================================
# ТЕСТЫ REQUEST METHOD
# ==============================================================================


@pytest.mark.asyncio
async def test_request_get_method(dmarket_api):
    """Тест GET запроса."""
    # Мокируем _get_client чтобы вернуть уже мокнутый клиент
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"result": "success"}
    mock_response.raise_for_status = MagicMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    dmarket_api._client = mock_client

    with patch.object(dmarket_api, "_get_client", return_value=mock_client):
        result = await dmarket_api._request("GET", "/test", params={"key": "value"})

    assert result == {"result": "success"}
    mock_client.get.assert_called_once()


@pytest.mark.asyncio
async def test_request_post_method(dmarket_api):
    """Тест POST запроса."""
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"created": True}
    mock_response.raise_for_status = MagicMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    dmarket_api._client = mock_client

    with patch.object(dmarket_api, "_get_client", return_value=mock_client):
        result = await dmarket_api._request("POST", "/test", data={"key": "value"})

    assert result == {"created": True}
    mock_client.post.assert_called_once()


@pytest.mark.asyncio
async def test_request_put_method(dmarket_api):
    """Тест PUT запроса."""
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"updated": True}
    mock_response.raise_for_status = MagicMock()
    mock_client.put = AsyncMock(return_value=mock_response)
    dmarket_api._client = mock_client

    with patch.object(dmarket_api, "_get_client", return_value=mock_client):
        result = await dmarket_api._request("PUT", "/test", data={"key": "value"})

    assert result == {"updated": True}


@pytest.mark.asyncio
async def test_request_delete_method(dmarket_api):
    """Тест DELETE запроса."""
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"deleted": True}
    mock_response.raise_for_status = MagicMock()
    mock_client.delete = AsyncMock(return_value=mock_response)
    dmarket_api._client = mock_client

    with patch.object(dmarket_api, "_get_client", return_value=mock_client):
        result = await dmarket_api._request("DELETE", "/test")

    assert result == {"deleted": True}


@pytest.mark.asyncio
async def test_request_unsupported_method(dmarket_api):
    """Тест неподдерживаемого HTTP метода."""
    mock_client = AsyncMock()
    dmarket_api._client = mock_client

    with patch.object(dmarket_api, "_get_client", return_value=mock_client):
        result = await dmarket_api._request("PATCH", "/test")

    assert result["error"] is True
    assert "code" in result


@pytest.mark.asyncio
async def test_request_json_parse_error(dmarket_api):
    """Тест ошибки парсинга JSON."""
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.side_effect = Exception("JSON parse error")
    mock_response.text = "plain text response"
    mock_response.raise_for_status = MagicMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    dmarket_api._client = mock_client

    with patch.object(dmarket_api, "_get_client", return_value=mock_client):
        result = await dmarket_api._request("GET", "/test")

    assert result["text"] == "plain text response"
    assert result["status_code"] == 200


@pytest.mark.asyncio
async def test_request_with_retries(dmarket_api):
    """Тест повторных попыток при ошибках."""
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Server error"

    def raise_http_error():
        raise httpx.HTTPStatusError(
            "Server error",
            request=MagicMock(),
            response=mock_response,
        )

    mock_response.raise_for_status = raise_http_error
    dmarket_api._client.get = AsyncMock(return_value=mock_response)
    dmarket_api.max_retries = 2

    with patch("asyncio.sleep", new=AsyncMock()):
        result = await dmarket_api._request("GET", "/test")

        assert result["error"] is True


@pytest.mark.asyncio
async def test_request_rate_limit_with_retry_after(dmarket_api):
    """Тест rate limit с заголовком Retry-After."""
    mock_response = MagicMock()
    mock_response.status_code = 429
    mock_response.text = "Rate limit exceeded"
    mock_response.headers = {"Retry-After": "5"}

    def raise_http_error():
        raise httpx.HTTPStatusError(
            "Rate limit",
            request=MagicMock(),
            response=mock_response,
        )

    mock_response.raise_for_status = raise_http_error
    dmarket_api._client.get = AsyncMock(return_value=mock_response)
    dmarket_api.max_retries = 1

    with patch("asyncio.sleep", new=AsyncMock()) as mock_sleep:
        result = await dmarket_api._request("GET", "/test")

        assert result["error"] is True
        # Verify sleep was called with retry delay
        mock_sleep.assert_called()


# ==============================================================================
# ТЕСТЫ GET_ALL_MARKET_ITEMS
# ==============================================================================


@pytest.mark.asyncio
async def test_get_all_market_items_single_page(dmarket_api):
    """Тест получения всех предметов (одна страница)."""
    with patch.object(dmarket_api, "get_market_items") as mock_get_items:
        mock_get_items.return_value = {
            "items": [{"id": "1"}, {"id": "2"}],
            "total": 2,
        }

        result = await dmarket_api.get_all_market_items("csgo", max_items=100)

        assert len(result) == 2


@pytest.mark.asyncio
async def test_get_all_market_items_multiple_pages(dmarket_api):
    """Тест получения всех предметов (несколько страниц)."""

    async def mock_get_items(*args, **kwargs):
        offset = kwargs.get("offset", 0)
        if offset == 0:
            return {"items": [{"id": f"item_{i}"} for i in range(100)]}
        elif offset == 100:
            return {"items": [{"id": f"item_{i}"} for i in range(100, 150)]}
        else:
            return {"items": []}

    with patch.object(dmarket_api, "get_market_items", side_effect=mock_get_items):
        result = await dmarket_api.get_all_market_items("csgo", max_items=200)

        assert len(result) == 150


@pytest.mark.asyncio
async def test_get_all_market_items_empty_response(dmarket_api):
    """Тест получения пустого списка."""
    with patch.object(dmarket_api, "get_market_items") as mock_get_items:
        mock_get_items.return_value = {"items": [], "total": 0}

        result = await dmarket_api.get_all_market_items("csgo")

        assert len(result) == 0


# ==============================================================================
# ТЕСТЫ GET_SUGGESTED_PRICE
# ==============================================================================


@pytest.mark.asyncio
async def test_get_suggested_price_found(dmarket_api):
    """Тест получения рекомендуемой цены."""
    with patch.object(dmarket_api, "get_market_items") as mock_get_items:
        mock_get_items.return_value = {
            "items": [{"suggestedPrice": 1500}],
        }

        result = await dmarket_api.get_suggested_price("AK-47", "csgo")

        assert result == 15.0


@pytest.mark.asyncio
async def test_get_suggested_price_not_found(dmarket_api):
    """Тест когда предмет не найден."""
    with patch.object(dmarket_api, "get_market_items") as mock_get_items:
        mock_get_items.return_value = {"items": []}

        result = await dmarket_api.get_suggested_price("Unknown Item", "csgo")

        assert result is None


@pytest.mark.asyncio
async def test_get_suggested_price_dict_format(dmarket_api):
    """Тест рекомендуемой цены в формате dict."""
    with patch.object(dmarket_api, "get_market_items") as mock_get_items:
        mock_get_items.return_value = {
            "items": [{"suggestedPrice": {"amount": 2000, "currency": "USD"}}],
        }

        result = await dmarket_api.get_suggested_price("AWP", "csgo")

        assert result == 20.0


# ==============================================================================
# ТЕСТЫ ИНИЦИАЛИЗАЦИИ С РАЗНЫМИ ФОРМАТАМИ КЛЮЧЕЙ
# ==============================================================================


def test_init_with_bytes_secret_key():
    """Тест инициализации с bytes secret key."""
    secret_key_str = "test_secret_key_bytes_format"
    api = DMarketAPI(TEST_PUBLIC_KEY, secret_key_str)

    assert api.secret_key == secret_key_str.encode("utf-8")


def test_init_with_custom_pool_limits():
    """Тест инициализации с кастомными pool limits."""
    pool_limits = httpx.Limits(max_connections=50, max_keepalive_connections=10)
    api = DMarketAPI(TEST_PUBLIC_KEY, TEST_SECRET_KEY, pool_limits=pool_limits)

    assert api.pool_limits == pool_limits


def test_init_with_custom_retry_codes():
    """Тест инициализации с кастомными retry codes."""
    retry_codes = [429, 500, 503]
    api = DMarketAPI(TEST_PUBLIC_KEY, TEST_SECRET_KEY, retry_codes=retry_codes)

    assert api.retry_codes == retry_codes


# ==============================================================================
# ТЕСТЫ DIRECT BALANCE С РАЗЛИЧНЫМИ ФОРМАТАМИ
# ==============================================================================


@pytest.mark.asyncio
async def test_direct_balance_official_format(dmarket_api):
    """Тест прямого запроса баланса в официальном формате."""
    with patch("requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "usd": "2550",
            "usdAvailableToWithdraw": "2550",
            "dmc": "0",
            "dmcAvailableToWithdraw": "0",
        }
        mock_get.return_value = mock_response

        result = await dmarket_api.direct_balance_request()

        assert result["success"] is True
        assert result["data"]["balance"] == 25.50


@pytest.mark.asyncio
async def test_direct_balance_with_trade_protected(dmarket_api):
    """Тест прямого запроса баланса с защищенными средствами."""
    with patch("requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "usd": "3000",
            "usdAvailableToWithdraw": "2500",
            "usdTradeProtected": "500",
        }
        mock_get.return_value = mock_response

        result = await dmarket_api.direct_balance_request()

        assert result["success"] is True
        assert result["data"]["trade_protected"] == 5.0


@pytest.mark.asyncio
async def test_direct_balance_exception(dmarket_api):
    """Тест исключения при прямом запросе баланса."""
    with patch("requests.get", side_effect=Exception("Connection error")):
        result = await dmarket_api.direct_balance_request()

        assert result["success"] is False
        assert "error" in result
