"""Integration tests for DMarket API with httpx-mock.

Эти тесты используют pytest-httpx для мокирования HTTP запросов
и проверяют поведение API клиента в различных сценариях.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import httpx
import pytest
import pytest_asyncio
from pytest_httpx import HTTPXMock

if TYPE_CHECKING:
    from src.dmarket.dmarket_api import DMarketAPI


pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture
async def mock_dmarket_api():
    """Create DMarketAPI instance for integration tests WITHOUT mocking _request.

    Эта фикстура создает реальный экземпляр API без патча _request,
    чтобы pytest-httpx мог перехватывать HTTP запросы.
    """
    from src.dmarket.dmarket_api import DMarketAPI

    api = DMarketAPI(
        public_key="test_public_key",
        secret_key="test_secret_key",
        enable_cache=False,  # ВАЖНО: отключаем кэш для тестов
    )

    yield api
    # DMarketAPI doesn't have close() method - no cleanup needed


class TestDMarketAPIWithHTTPXMock:
    """Integration тесты с полным мокированием HTTP."""

    async def test_get_balance_success(
        self,
        mock_dmarket_api: DMarketAPI,
        httpx_mock: HTTPXMock,
    ) -> None:
        """Тест успешного получения баланса."""
        # Подготовка мока
        expected_response = {
            "usd": "10050",  # $100.50 в центах
            "usdAvailableToWithdraw": "10000",
            "dmc": "5000",
            "dmcAvailableToWithdraw": "4500",
        }

        httpx_mock.add_response(
            url="https://api.dmarket.com/account/v1/balance",
            method="GET",
            json=expected_response,
            status_code=200,
        )

        # Выполнение
        balance = await mock_dmarket_api.get_balance()

        # Проверка
        assert balance is not None
        assert isinstance(balance, dict)
        assert "usd" in balance or "amount" in balance

    async def test_get_balance_rate_limit(
        self,
        mock_dmarket_api: DMarketAPI,
        httpx_mock: HTTPXMock,
    ) -> None:
        """Тест обработки rate limit (429)."""
        # Первый запрос - rate limit
        httpx_mock.add_response(
            url="https://api.dmarket.com/account/v1/balance",
            method="GET",
            status_code=429,
            headers={"Retry-After": "1"},
            json={"error": "Rate limit exceeded"},
        )

        # Второй запрос - успех
        httpx_mock.add_response(
            url="https://api.dmarket.com/account/v1/balance",
            method="GET",
            status_code=200,
            json={"usd": "10000", "dmc": "5000"},
        )

        # Выполнение - должен повторить запрос
        balance = await mock_dmarket_api.get_balance()

        # Проверка что повторный запрос прошел успешно
        assert balance is not None

    async def test_get_balance_unauthorized(
        self,
        mock_dmarket_api: DMarketAPI,
        httpx_mock: HTTPXMock,
    ) -> None:
        """Тест обработки ошибки аутентификации (401)."""
        # API делает 5 попыток при 401:
        # 1. Direct Balance Request: /account/v1/balance
        # 2. Fallback #1: /account/v1/balance (повторный вызов того же URL)
        # 3-5. Fallback #2-4: другие эндпоинты

        # Регистрируем /account/v1/balance ДВАЖДЫ (pytest-httpx 0.35.0 не поддерживает can_reuse)
        # Первый мок - для Direct Balance Request
        httpx_mock.add_response(
            url="https://api.dmarket.com/account/v1/balance",
            method="GET",
            status_code=401,
            json={"error": "Unauthorized", "message": "Invalid API credentials"},
        )
        # Второй мок - для Fallback #1 (тот же URL)
        httpx_mock.add_response(
            url="https://api.dmarket.com/account/v1/balance",
            method="GET",
            status_code=401,
            json={"error": "Unauthorized"},
        )
        # Fallback #2
        httpx_mock.add_response(
            url="https://api.dmarket.com/api/v1/account/wallet/balance",
            method="GET",
            status_code=401,
            json={"error": "Unauthorized"},
        )
        httpx_mock.add_response(
            url="https://api.dmarket.com/exchange/v1/user/balance",
            method="GET",
            status_code=401,
            json={"error": "Unauthorized"},
        )
        httpx_mock.add_response(
            url="https://api.dmarket.com/api/v1/account/balance",
            method="GET",
            status_code=401,
            json={"error": "Unauthorized"},
        )

        # Выполнение
        balance = await mock_dmarket_api.get_balance()

        # API должен вернуть fallback или пустой результат
        assert balance is not None

    async def test_get_market_items_success(
        self,
        mock_dmarket_api: DMarketAPI,
        httpx_mock: HTTPXMock,
    ) -> None:
        """Тест успешного получения предметов рынка."""
        expected_response = {
            "cursor": "next_page_cursor",
            "objects": [
                {
                    "itemId": "item_123",
                    "title": "AK-47 | Redline (Field-Tested)",
                    "price": {"USD": "1250"},  # $12.50 в центах
                    "suggestedPrice": {"USD": "1300"},
                    "category": "Rifle",
                    "exterior": "Field-Tested",
                },
                {
                    "itemId": "item_456",
                    "title": "AWP | Asiimov (Field-Tested)",
                    "price": {"USD": "5000"},
                    "suggestedPrice": {"USD": "5200"},
                    "category": "Sniper Rifle",
                    "exterior": "Field-Tested",
                },
            ],
            "total": 1500,
        }

        # Mock с учетом query параметров
        httpx_mock.add_response(
            url="https://api.dmarket.com/exchange/v1/market/items?gameId=csgo&limit=100&offset=0&currency=USD&orderBy=price",  # noqa: E501
            method="GET",
            json=expected_response,
            status_code=200,
        )

        # Выполнение
        items = await mock_dmarket_api.get_market_items(game="csgo", limit=100)

        # Проверка
        assert items is not None
        assert "objects" in items
        assert len(items["objects"]) == 2
        assert items["objects"][0]["title"] == "AK-47 | Redline (Field-Tested)"

    async def test_get_market_items_pagination(
        self,
        mock_dmarket_api: DMarketAPI,
        httpx_mock: HTTPXMock,
    ) -> None:
        """Тест пагинации предметов рынка."""
        # Первая страница
        page1 = {
            "cursor": "cursor_1",
            "objects": [
                {"itemId": f"item_{i}", "title": f"Item {i}", "price": {"USD": "100"}}
                for i in range(100)
            ],
        }

        # Вторая страница
        page2 = {
            "cursor": "",
            "objects": [
                {"itemId": f"item_{i}", "title": f"Item {i}", "price": {"USD": "100"}}
                for i in range(100, 150)
            ],
        }

        # Добавляем моки для обеих страниц с query параметрами
        httpx_mock.add_response(
            url="https://api.dmarket.com/exchange/v1/market/items?gameId=csgo&limit=100&offset=0&currency=USD&orderBy=price",  # noqa: E501
            method="GET",
            json=page1,
            status_code=200,
        )
        httpx_mock.add_response(
            url="https://api.dmarket.com/exchange/v1/market/items?gameId=csgo&limit=100&offset=100&currency=USD&orderBy=price",  # noqa: E501
            method="GET",
            json=page2,
            status_code=200,
        )

        # Выполнение - получаем все предметы
        all_items = await mock_dmarket_api.get_all_market_items(
            game="csgo",
            max_items=200,
        )

        # Проверка
        assert isinstance(all_items, list)
        assert len(all_items) >= 100  # Минимум первая страница

    async def test_get_market_items_empty_result(
        self,
        mock_dmarket_api: DMarketAPI,
        httpx_mock: HTTPXMock,
    ) -> None:
        """Тест пустого результата рынка."""
        httpx_mock.add_response(
            url="https://api.dmarket.com/exchange/v1/market/items?gameId=csgo&limit=100&offset=0&currency=USD&orderBy=price",  # noqa: E501
            method="GET",
            json={"cursor": "", "objects": [], "total": 0},
            status_code=200,
        )

        items = await mock_dmarket_api.get_market_items(game="csgo")

        assert items["objects"] == []
        assert items["total"] == 0

    async def test_create_targets_success(
        self,
        mock_dmarket_api: DMarketAPI,
        httpx_mock: HTTPXMock,
    ) -> None:
        """Тест успешного создания таргетов."""
        expected_response = {
            "Result": [
                {
                    "TargetID": "target_12345",
                    "Title": "AK-47 | Redline (Field-Tested)",
                    "Status": "Created",
                }
            ]
        }

        httpx_mock.add_response(
            url="https://api.dmarket.com/marketplace-api/v1/user-targets/create",
            method="POST",
            json=expected_response,
            status_code=200,
        )

        targets_data = [
            {
                "Title": "AK-47 | Redline (Field-Tested)",
                "Amount": 1,
                "Price": {"Amount": 1200, "Currency": "USD"},
            }
        ]

        result = await mock_dmarket_api.create_targets(game_id="csgo", targets=targets_data)

        assert result is not None
        assert "Result" in result
        assert result["Result"][0]["Status"] == "Created"

    async def test_create_targets_validation_error(
        self,
        mock_dmarket_api: DMarketAPI,
        httpx_mock: HTTPXMock,
    ) -> None:
        """Тест ошибки валидации при создании таргетов."""
        httpx_mock.add_response(
            url="https://api.dmarket.com/marketplace-api/v1/user-targets/create",
            method="POST",
            status_code=400,
            json={
                "error": "ValidationError",
                "message": "Price must be greater than 0",
            },
        )

        targets_data = [
            {
                "Title": "Invalid Item",
                "Amount": 1,
                "Price": {"Amount": 0, "Currency": "USD"},
            }
        ]

        result = await mock_dmarket_api.create_targets(game_id="csgo", targets=targets_data)

        # API должен обработать ошибку и вернуть результат
        assert result is not None

    async def test_network_timeout(
        self,
        mock_dmarket_api: DMarketAPI,
        httpx_mock: HTTPXMock,
    ) -> None:
        """Тест обработки таймаута сети."""
        httpx_mock.add_exception(
            exception=httpx.TimeoutException("Request timeout"),
            url="https://api.dmarket.com/account/v1/balance",
        )

        # Добавляем успешный ответ для повторной попытки
        httpx_mock.add_response(
            url="https://api.dmarket.com/account/v1/balance",
            method="GET",
            json={"usd": "10000"},
            status_code=200,
        )

        # API должен повторить запрос
        balance = await mock_dmarket_api.get_balance()
        assert balance is not None

    async def test_network_connection_error(
        self,
        mock_dmarket_api: DMarketAPI,
        httpx_mock: HTTPXMock,
    ) -> None:
        """Тест обработки ошибки подключения."""
        httpx_mock.add_exception(
            exception=httpx.ConnectError("Connection refused"),
            url="https://api.dmarket.com/account/v1/balance",
        )

        # Добавляем успешный ответ для повторной попытки
        httpx_mock.add_response(
            url="https://api.dmarket.com/account/v1/balance",
            method="GET",
            json={"usd": "10000"},
            status_code=200,
        )

        balance = await mock_dmarket_api.get_balance()
        assert balance is not None

    async def test_server_error_retry(
        self,
        mock_dmarket_api: DMarketAPI,
        httpx_mock: HTTPXMock,
    ) -> None:
        """Тест повторной попытки при ошибке сервера (500)."""
        # Первый запрос - ошибка сервера
        httpx_mock.add_response(
            url="https://api.dmarket.com/account/v1/balance",
            method="GET",
            status_code=500,
            json={"error": "Internal Server Error"},
        )

        # Второй запрос - успех
        httpx_mock.add_response(
            url="https://api.dmarket.com/account/v1/balance",
            method="GET",
            status_code=200,
            json={"usd": "10000"},
        )

        balance = await mock_dmarket_api.get_balance()
        assert balance is not None

    async def test_malformed_json_response(
        self,
        mock_dmarket_api: DMarketAPI,
        httpx_mock: HTTPXMock,
    ) -> None:
        """Тест обработки некорректного JSON."""
        # Первый запрос вернет невалидный JSON (direct_balance_request)
        httpx_mock.add_response(
            url="https://api.dmarket.com/account/v1/balance",
            method="GET",
            status_code=200,
            content=b"Invalid JSON{{{",
        )

        # Fallback #1: /account/v1/balance (повторный запрос того же URL)
        # Также возвращает невалидный JSON
        httpx_mock.add_response(
            url="https://api.dmarket.com/account/v1/balance",
            method="GET",
            status_code=200,
            content=b"Invalid JSON{{{",
        )

        # Fallback #2: /api/v1/account/wallet/balance
        httpx_mock.add_response(
            url="https://api.dmarket.com/api/v1/account/wallet/balance",
            method="GET",
            status_code=200,
            content=b"Invalid JSON{{{",
        )

        # Fallback #3: /exchange/v1/user/balance
        httpx_mock.add_response(
            url="https://api.dmarket.com/exchange/v1/user/balance",
            method="GET",
            status_code=200,
            content=b"Invalid JSON{{{",
        )

        # Fallback #4: /api/v1/account/balance
        httpx_mock.add_response(
            url="https://api.dmarket.com/api/v1/account/balance",
            method="GET",
            status_code=200,
            content=b"Invalid JSON{{{",
        )

        # После всех fallback попыток get_balance() возвращает fallback результат с $0

        # API должен обработать ошибку парсинга
        # и вернуть fallback с нулевым балансом
        balance = await mock_dmarket_api.get_balance()
        assert balance is not None
        assert balance.get("error") is False or balance.get("balance", 0) >= 0

    async def test_concurrent_requests(
        self,
        mock_dmarket_api: DMarketAPI,
        httpx_mock: HTTPXMock,
    ) -> None:
        """Тест одновременных запросов к API."""
        import asyncio

        # Моки для разных эндпоинтов
        httpx_mock.add_response(
            url="https://api.dmarket.com/account/v1/balance",
            method="GET",
            json={"usd": "10000"},
            status_code=200,
        )
        # Используем matcher для поддержки query параметров
        market_url = (
            "https://api.dmarket.com/exchange/v1/market/items"
            "?gameId=csgo&limit=100&offset=0&currency=USD"
            "&orderBy=price"
        )
        httpx_mock.add_response(
            url=market_url,
            method="GET",
            json={"objects": [], "cursor": "", "total": 0},
            status_code=200,
        )

        # Выполнение одновременных запросов
        results = await asyncio.gather(
            mock_dmarket_api.get_balance(),
            mock_dmarket_api.get_market_items(game="csgo"),
        )

        assert len(results) == 2
        assert results[0] is not None
        assert results[1] is not None


class TestDMarketAPIEdgeCasesHTTPX:
    """Edge cases с httpx-mock."""

    async def test_very_large_response(
        self,
        mock_dmarket_api: DMarketAPI,
        httpx_mock: HTTPXMock,
    ) -> None:
        """Тест обработки очень большого ответа."""
        # Создаем большой ответ (1000 предметов)
        large_response = {
            "cursor": "",
            "objects": [
                {
                    "itemId": f"item_{i}",
                    "title": f"Item {i}",
                    "price": {"USD": str(100 + i)},
                }
                for i in range(1000)
            ],
            "total": 1000,
        }

        # Используем matcher для поддержки query параметров
        large_url = (
            "https://api.dmarket.com/exchange/v1/market/items"
            "?gameId=csgo&limit=1000&offset=0&currency=USD"
            "&orderBy=price"
        )
        httpx_mock.add_response(
            url=large_url,
            method="GET",
            json=large_response,
            status_code=200,
        )

        items = await mock_dmarket_api.get_market_items(game="csgo", limit=1000)

        assert len(items["objects"]) == 1000

    async def test_unicode_characters_in_response(
        self,
        mock_dmarket_api: DMarketAPI,
        httpx_mock: HTTPXMock,
    ) -> None:
        """Тест обработки Unicode символов."""
        response = {
            "objects": [
                {
                    "itemId": "item_1",
                    "title": "AK-47 | 红线 (久经沙场)",  # Китайские символы
                    "price": {"USD": "1250"},
                },
                {
                    "itemId": "item_2",
                    "title": "AWP | Азимов 🔥",  # Эмодзи
                    "price": {"USD": "5000"},
                },
            ],
            "cursor": "",
        }

        httpx_mock.add_response(
            url=(
                "https://api.dmarket.com/exchange/v1/market/items?"
                "gameId=csgo&limit=100&offset=0&currency=USD&"
                "orderBy=price"
            ),
            method="GET",
            json=response,
            status_code=200,
        )

        items = await mock_dmarket_api.get_market_items(game="csgo")

        assert len(items["objects"]) == 2
        assert "红线" in items["objects"][0]["title"]
        assert "🔥" in items["objects"][1]["title"]

    async def test_missing_optional_fields(
        self,
        mock_dmarket_api: DMarketAPI,
        httpx_mock: HTTPXMock,
    ) -> None:
        """Тест обработки отсутствующих опциональных полей."""
        response = {
            "objects": [
                {
                    "itemId": "item_1",
                    "title": "Minimal Item",
                    "price": {"USD": "100"},
                    # Отсутствуют suggestedPrice, category, exterior
                }
            ],
            "cursor": "",
        }

        httpx_mock.add_response(
            url=(
                "https://api.dmarket.com/exchange/v1/market/items?"
                "gameId=csgo&limit=100&offset=0&currency=USD&"
                "orderBy=price"
            ),
            method="GET",
            json=response,
            status_code=200,
        )

        items = await mock_dmarket_api.get_market_items(game="csgo")

        assert len(items["objects"]) == 1
        assert items["objects"][0]["title"] == "Minimal Item"

    async def test_price_edge_cases(
        self,
        mock_dmarket_api: DMarketAPI,
        httpx_mock: HTTPXMock,
    ) -> None:
        """Тест граничных значений цен."""
        response = {
            "objects": [
                {
                    "itemId": "item_1",
                    "title": "Very Cheap Item",
                    "price": {"USD": "1"},  # $0.01
                },
                {
                    "itemId": "item_2",
                    "title": "Very Expensive Item",
                    "price": {"USD": "10000000"},  # $100,000
                },
                {
                    "itemId": "item_3",
                    "title": "Zero Price Item",
                    "price": {"USD": "0"},  # Некорректная цена
                },
            ],
            "cursor": "",
        }

        httpx_mock.add_response(
            url=(
                "https://api.dmarket.com/exchange/v1/market/items?"
                "gameId=csgo&limit=100&offset=0&currency=USD&"
                "orderBy=price"
            ),
            method="GET",
            json=response,
            status_code=200,
        )

        items = await mock_dmarket_api.get_market_items(game="csgo")

        assert len(items["objects"]) == 3

    async def test_rate_limit_with_multiple_retries(
        self,
        mock_dmarket_api: DMarketAPI,
        httpx_mock: HTTPXMock,
    ) -> None:
        """Тест множественных повторных попыток при rate limit."""
        # Добавляем 3 ответа с rate limit
        for _ in range(3):
            httpx_mock.add_response(
                url="https://api.dmarket.com/account/v1/balance",
                method="GET",
                status_code=429,
                headers={"Retry-After": "1"},
            )

        # Последний запрос успешен
        httpx_mock.add_response(
            url="https://api.dmarket.com/account/v1/balance",
            method="GET",
            status_code=200,
            json={"usd": "10000"},
        )

        balance = await mock_dmarket_api.get_balance()
        assert balance is not None

    async def test_api_version_compatibility(
        self,
        mock_dmarket_api: DMarketAPI,
        httpx_mock: HTTPXMock,
    ) -> None:
        """Тест совместимости с разными версиями API."""
        # Старый формат ответа
        old_format = {
            "balance": 10000,  # Вместо "usd"
            "available": 9500,
        }

        httpx_mock.add_response(
            url="https://api.dmarket.com/account/v1/balance",
            method="GET",
            json=old_format,
            status_code=200,
        )

        balance = await mock_dmarket_api.get_balance()
        assert balance is not None

    async def test_partial_response_handling(
        self,
        mock_dmarket_api: DMarketAPI,
        httpx_mock: HTTPXMock,
    ) -> None:
        """Тест обработки частичного ответа."""
        partial_response = {
            "objects": [
                {"itemId": "item_1", "title": "Item 1"}
                # Отсутствует price
            ]
        }
        # Отсутствует cursor

        httpx_mock.add_response(
            url=(
                "https://api.dmarket.com/exchange/v1/market/items?"
                "gameId=csgo&limit=100&offset=0&currency=USD&"
                "orderBy=price"
            ),
            method="GET",
            json=partial_response,
            status_code=200,
        )

        items = await mock_dmarket_api.get_market_items(game="csgo")

        # API должен обработать частичный ответ
        assert items is not None
