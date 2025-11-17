"""Тесты для модуля auto_arbitrage."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram import CallbackQuery

from src.telegram_bot.auto_arbitrage import (
    ARBITRAGE_MODES,
    check_balance_command,
    create_dmarket_api_client,
    format_auto_arbitrage_results,
    handle_auto_trade,
    safe_edit_message_text,
    start_auto_trading,
)


class TestArbitrageModes:
    """Тесты для конфигурации режимов арбитража."""

    def test_all_modes_exist(self):
        """Проверка наличия всех режимов."""
        expected_modes = ["boost_low", "mid_medium", "pro_high"]
        assert all(mode in ARBITRAGE_MODES for mode in expected_modes)

    def test_mode_structure(self):
        """Проверка структуры каждого режима."""
        required_fields = {
            "name",
            "min_price",
            "max_price",
            "min_profit_percent",
            "min_profit_amount",
            "trade_strategy",
        }

        for mode, config in ARBITRAGE_MODES.items():
            assert set(config.keys()) == required_fields, f"Mode {mode} missing fields"

    def test_price_ranges_ascending(self):
        """Проверка что диапазоны цен идут по возрастанию."""
        boost_max = ARBITRAGE_MODES["boost_low"]["max_price"]
        mid_max = ARBITRAGE_MODES["mid_medium"]["max_price"]
        pro_max = ARBITRAGE_MODES["pro_high"]["max_price"]

        assert boost_max < mid_max < pro_max

    def test_profit_requirements_ascending(self):
        """Проверка что требования к прибыли растут."""
        boost_profit = ARBITRAGE_MODES["boost_low"]["min_profit_percent"]
        mid_profit = ARBITRAGE_MODES["mid_medium"]["min_profit_percent"]
        pro_profit = ARBITRAGE_MODES["pro_high"]["min_profit_percent"]

        assert boost_profit < mid_profit < pro_profit


class TestSafeEditMessageText:
    """Тесты для функции safe_edit_message_text."""

    @pytest.mark.asyncio()
    async def test_successful_edit(self):
        """Тест успешного редактирования сообщения."""
        query = MagicMock()
        query.edit_message_text = AsyncMock()

        result = await safe_edit_message_text(
            query,
            "Test message",
            reply_markup=None,
        )

        assert result is True
        query.edit_message_text.assert_called_once()

    @pytest.mark.asyncio()
    async def test_message_not_modified(self):
        """Тест обработки ошибки 'message is not modified'."""
        from telegram.error import BadRequest

        query = MagicMock()
        query.edit_message_text = AsyncMock(
            side_effect=BadRequest("Message is not modified"),
        )

        result = await safe_edit_message_text(query, "Test message")

        assert result is False

    @pytest.mark.asyncio()
    async def test_other_bad_request(self):
        """Тест обработки других BadRequest ошибок."""
        from telegram.error import BadRequest

        query = MagicMock()
        query.edit_message_text = AsyncMock(
            side_effect=BadRequest("Some other error"),
        )

        with pytest.raises(BadRequest):
            await safe_edit_message_text(query, "Test message")


class TestFormatAutoArbitrageResults:
    """Тесты для функции format_auto_arbitrage_results."""

    @pytest.mark.asyncio()
    async def test_empty_items(self):
        """Тест форматирования пустого списка предметов."""
        result = await format_auto_arbitrage_results(
            items=[],
            current_page=0,
            total_pages=1,
            mode="boost_low",
        )

        assert "Нет данных" in result

    @pytest.mark.asyncio()
    async def test_format_single_item(self):
        """Тест форматирования одного предмета."""
        items = [
            {
                "title": "AK-47 | Redline (Field-Tested)",
                "price": {"amount": 1250},  # $12.50 в центах
                "profit": 250,  # $2.50 в центах
                "profit_percent": 20.0,
                "game": "csgo",
                "liquidity": "high",
            },
        ]

        result = await format_auto_arbitrage_results(
            items=items,
            current_page=0,
            total_pages=1,
            mode="boost_low",
        )

        assert "AK-47 | Redline" in result
        assert "$12.50" in result
        assert "20.0%" in result

    @pytest.mark.asyncio()
    async def test_multiple_pages(self):
        """Тест форматирования с пагинацией."""
        items = [
            {"title": f"Item {i}", "price": 1000, "profit": 100, "profit_percent": 10}
            for i in range(5)
        ]

        result = await format_auto_arbitrage_results(
            items=items,
            current_page=1,
            total_pages=3,
        )

        assert "Страница 2 из 3" in result

    @pytest.mark.asyncio()
    async def test_price_format_dict(self):
        """Тест форматирования цены из dict."""
        items = [
            {
                "title": "Test Item",
                "price": {"amount": 5000},  # $50.00
                "profit": 500,
                "profit_percent": 10.0,
            },
        ]

        result = await format_auto_arbitrage_results(items, 0, 1)
        assert "$50.00" in result

    @pytest.mark.asyncio()
    async def test_price_format_string(self):
        """Тест форматирования цены из строки."""
        items = [
            {
                "title": "Test Item",
                "price": "$25.00",
                "profit": "$5.00",
                "profit_percent": 20.0,
            },
        ]

        result = await format_auto_arbitrage_results(items, 0, 1)
        assert "$25.00" in result


class TestCreateDMarketAPIClient:
    """Тесты для функции create_dmarket_api_client."""

    @pytest.mark.asyncio()
    async def test_create_from_context(self):
        """Тест создания API клиента из контекста."""
        context = MagicMock()
        context.bot_data = {
            "dmarket_public_key": "test_public",
            "dmarket_secret_key": "test_secret",
        }

        with patch("src.telegram_bot.auto_arbitrage.DMarketAPI") as mock_api:
            await create_dmarket_api_client(context)
            mock_api.assert_called_once()

    @pytest.mark.asyncio()
    async def test_create_from_env(self):
        """Тест создания API клиента из переменных окружения."""
        context = MagicMock()
        context.bot_data = {}

        with (
            patch.dict(
                "os.environ",
                {
                    "DMARKET_PUBLIC_KEY": "env_public",
                    "DMARKET_SECRET_KEY": "env_secret",
                },
            ),
            patch("src.telegram_bot.auto_arbitrage.DMarketAPI") as mock_api,
        ):
            await create_dmarket_api_client(context)
            mock_api.assert_called_once()

    @pytest.mark.asyncio()
    async def test_missing_keys(self):
        """Тест обработки отсутствующих ключей."""
        context = MagicMock()
        context.bot_data = {}

        with patch.dict("os.environ", {}, clear=True):
            result = await create_dmarket_api_client(context)
            assert result is None


class TestCheckBalanceCommand:
    """Тесты для функции check_balance_command."""

    @pytest.mark.asyncio()
    async def test_successful_balance_check(self):
        """Тест успешной проверки баланса."""
        query = MagicMock(spec=CallbackQuery)
        query.edit_message_text = AsyncMock()

        context = MagicMock()

        mock_api = MagicMock()
        mock_api.get_user_balance = AsyncMock(
            return_value={
                "available_balance": 100.0,
                "total_balance": 100.0,
                "has_funds": True,
                "error": False,
            },
        )
        mock_api.get_account_details = AsyncMock(
            return_value={"username": "test_user"},
        )
        mock_api.get_active_offers = AsyncMock(
            return_value={"total": 5},
        )

        with patch(
            "src.telegram_bot.auto_arbitrage.create_dmarket_api_client", return_value=mock_api
        ):
            await check_balance_command(query, context)

            # Проверяем что был вызван метод редактирования сообщения
            assert query.edit_message_text.call_count >= 1

    @pytest.mark.asyncio()
    async def test_api_error_handling(self):
        """Тест обработки ошибки API."""
        query = MagicMock(spec=CallbackQuery)
        query.edit_message_text = AsyncMock()

        context = MagicMock()

        with patch(
            "src.telegram_bot.auto_arbitrage.create_dmarket_api_client",
            return_value=None,
        ):
            await check_balance_command(query, context)

            # Проверяем что было отправлено сообщение об ошибке
            assert query.edit_message_text.called


class TestHandleAutoTrade:
    """Тесты для функции handle_auto_trade."""

    @pytest.mark.asyncio()
    async def test_auto_trade_initialization(self):
        """Тест инициализации автоматической торговли."""
        query = MagicMock()
        query.from_user.id = 123456789
        query.edit_message_text = AsyncMock()

        context = MagicMock()
        context.user_data = {"current_game": "csgo"}

        mock_api = MagicMock()
        mock_api.get_user_balance = AsyncMock(
            return_value={"has_funds": True, "available_balance": 100.0},
        )

        with (
            patch(
                "src.telegram_bot.auto_arbitrage.create_dmarket_api_client", return_value=mock_api
            ),
            patch(
                "src.telegram_bot.auto_arbitrage.check_user_balance",
                return_value={"has_funds": True},
            ),
            patch("src.telegram_bot.auto_arbitrage.scan_multiple_games", return_value={}),
            patch("src.telegram_bot.auto_arbitrage.pagination_manager"),
        ):
            await handle_auto_trade(query, context, "medium")

            assert query.edit_message_text.called


class TestStartAutoTrading:
    """Тесты для функции start_auto_trading."""

    @pytest.mark.asyncio()
    async def test_start_trading_with_valid_mode(self):
        """Тест запуска торговли с валидным режимом."""
        query = MagicMock()
        query.from_user.id = 123456789
        query.edit_message_text = AsyncMock()

        context = MagicMock()

        mock_api = MagicMock()
        mock_balance = {"balance": 100.0, "has_funds": True, "available_balance": 100.0}

        with (
            patch(
                "src.telegram_bot.auto_arbitrage.create_dmarket_api_client", return_value=mock_api
            ),
            patch("src.telegram_bot.auto_arbitrage.check_user_balance", return_value=mock_balance),
            patch("src.telegram_bot.auto_arbitrage.scan_multiple_games", return_value=[]),
        ):
            await start_auto_trading(query, context, "boost_low")

            assert query.edit_message_text.called

    @pytest.mark.asyncio()
    async def test_insufficient_balance(self):
        """Тест обработки недостаточного баланса."""
        query = MagicMock()
        query.from_user.id = 123456789
        query.edit_message_text = AsyncMock()

        context = MagicMock()

        mock_api = MagicMock()
        mock_balance = {"balance": 0.5, "has_funds": False, "available_balance": 0.5}

        with (
            patch(
                "src.telegram_bot.auto_arbitrage.create_dmarket_api_client", return_value=mock_api
            ),
            patch("src.telegram_bot.auto_arbitrage.check_user_balance", return_value=mock_balance),
        ):
            await start_auto_trading(query, context, "boost_low")

            # Должно быть сообщение о недостаточном балансе
            call_args = query.edit_message_text.call_args_list
            assert any("Недостаточно средств" in str(call) for call in call_args)


class TestIntegration:
    """Интеграционные тесты."""

    @pytest.mark.asyncio()
    async def test_full_arbitrage_workflow(self):
        """Тест полного рабочего процесса арбитража."""
        query = MagicMock()
        query.from_user.id = 123456789
        query.edit_message_text = AsyncMock()

        context = MagicMock()
        context.user_data = {}

        mock_items = [
            {
                "title": "Test Item",
                "price": {"amount": 1000},
                "profit": 200,
                "profit_percent": 20.0,
                "game": "csgo",
                "liquidity": "high",
            },
        ]

        with (
            patch("src.telegram_bot.auto_arbitrage.create_dmarket_api_client"),
            patch(
                "src.telegram_bot.auto_arbitrage.check_user_balance",
                return_value={"has_funds": True, "available_balance": 100.0},
            ),
            patch("src.telegram_bot.auto_arbitrage.scan_multiple_games", return_value=mock_items),
            patch("src.telegram_bot.auto_arbitrage.pagination_manager"),
            patch("src.telegram_bot.auto_arbitrage.show_auto_stats_with_pagination"),
        ):
            await start_auto_trading(query, context, "boost_low")

            # Проверяем что функция завершилась без ошибок
            assert True
