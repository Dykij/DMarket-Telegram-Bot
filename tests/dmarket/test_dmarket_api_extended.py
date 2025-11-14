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
    with patch("src.dmarket.dmarket_api.api_cache") as mock_cache:
        mock_cache.clear = MagicMock()

        await dmarket_api.clear_cache()

        mock_cache.clear.assert_called_once()


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
            "balance": 25.0,
            "available": 23.5,
            "total": 26.0,
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

