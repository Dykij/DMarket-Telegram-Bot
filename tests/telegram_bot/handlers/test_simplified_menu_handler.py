"""Тесты для упрощенного меню бота."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram import CallbackQuery, Chat, Message, Update, User
from telegram.ext import ContextTypes

from src.telegram_bot.handlers.simplified_menu_handler import (
    CHOOSING_ARB_MODE,
    CHOOSING_TARGET_MODE,
    SELECTING_GAME_MANUAL,
    WAITING_FOR_RANGE,
    WAITING_FOR_TARGET_NAME,
    arbitrage_all_games,
    arbitrage_manual_mode,
    arbitrage_process_range,
    arbitrage_select_game,
    arbitrage_start,
    balance_simple,
    get_arb_mode_keyboard,
    get_game_selection_keyboard,
    get_main_menu_keyboard,
    get_targets_mode_keyboard,
    start_simple_menu,
    stats_simple,
    targets_auto,
    targets_create,
    targets_list,
    targets_manual,
    targets_start,
)


@pytest.fixture()
def mock_update():
    """Создать mock Update с message."""
    update = MagicMock(spec=Update)
    message = MagicMock(spec=Message)
    user = MagicMock(spec=User)
    chat = MagicMock(spec=Chat)

    user.id = 123456789
    user.username = "test_user"

    message.reply_text = AsyncMock()
    message.text = None

    update.message = message
    update.effective_user = user
    update.callback_query = None

    return update


@pytest.fixture()
def mock_callback_update():
    """Создать mock Update с callback query."""
    update = MagicMock(spec=Update)
    query = MagicMock(spec=CallbackQuery)
    user = MagicMock(spec=User)

    user.id = 123456789
    user.username = "test_user"

    query.answer = AsyncMock()
    query.edit_message_text = AsyncMock()
    query.data = None

    update.callback_query = query
    update.effective_user = user
    update.message = None

    return update


@pytest.fixture()
def mock_context():
    """Создать mock ContextTypes.DEFAULT_TYPE."""
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.user_data = {}
    context.bot_data = {}
    return context


class TestKeyboards:
    """Тесты для функций создания клавиатур."""

    def test_get_main_menu_keyboard(self):
        """Тест создания главного меню."""
        keyboard = get_main_menu_keyboard()

        assert keyboard is not None
        assert keyboard.resize_keyboard is True
        assert len(keyboard.keyboard) == 2  # 2 ряда
        assert len(keyboard.keyboard[0]) == 2  # 2 кнопки в первом ряду

    def test_get_arb_mode_keyboard(self):
        """Тест создания меню арбитража."""
        keyboard = get_arb_mode_keyboard()

        assert keyboard is not None
        assert len(keyboard.inline_keyboard) == 3  # 3 кнопки
        assert "Все игры сразу" in keyboard.inline_keyboard[0][0].text
        assert "Ручной режим" in keyboard.inline_keyboard[1][0].text

    def test_get_game_selection_keyboard(self):
        """Тест создания меню выбора игры."""
        keyboard = get_game_selection_keyboard()

        assert keyboard is not None
        assert len(keyboard.inline_keyboard) >= 4  # 4 игры + кнопка назад

        # Проверяем наличие игр
        game_texts = [btn[0].text for btn in keyboard.inline_keyboard[:-1]]
        assert any("CS:GO" in text for text in game_texts)
        assert any("Dota" in text for text in game_texts)

    def test_get_targets_mode_keyboard(self):
        """Тест создания меню таргетов."""
        keyboard = get_targets_mode_keyboard()

        assert keyboard is not None
        assert len(keyboard.inline_keyboard) == 4  # 3 режима + назад
        assert "Ручной" in keyboard.inline_keyboard[0][0].text
        assert "Автомат" in keyboard.inline_keyboard[1][0].text


class TestStartMenu:
    """Тесты для стартового меню."""

    @pytest.mark.asyncio()
    async def test_start_simple_menu_success(self, mock_update, mock_context):
        """Тест успешного запуска упрощенного меню."""
        result = await start_simple_menu(mock_update, mock_context)

        # Проверяем что сообщение было отправлено
        mock_update.message.reply_text.assert_called_once()

        # Проверяем содержимое сообщения
        call_args = mock_update.message.reply_text.call_args
        assert "Главное меню DMarket" in call_args[0][0]

        # Проверяем что вернули ConversationHandler.END
        assert result == -1  # ConversationHandler.END

    @pytest.mark.asyncio()
    async def test_start_simple_menu_no_message(self, mock_context):
        """Тест когда нет message в update."""
        update = MagicMock(spec=Update)
        update.message = None

        result = await start_simple_menu(update, mock_context)

        assert result == -1


class TestBalance:
    """Тесты для проверки баланса."""

    @pytest.mark.asyncio()
    async def test_balance_simple_success(self, mock_update, mock_context):
        """Тест успешного получения баланса."""
        with patch(
            "src.telegram_bot.handlers.simplified_menu_handler.create_api_client_from_env"
        ) as mock_api:
            # Мокируем API клиент
            api_instance = AsyncMock()
            api_instance.get_balance = AsyncMock(
                return_value={
                    "usd": 12575,  # $125.75 в центах
                    "dmc": 0,
                }
            )
            mock_api.return_value = api_instance

            result = await balance_simple(mock_update, mock_context)

            # Проверяем что баланс был запрошен
            api_instance.get_balance.assert_called_once()

            # Проверяем что сообщение было отправлено
            mock_update.message.reply_text.assert_called_once()
            call_args = mock_update.message.reply_text.call_args[0][0]
            assert "$125.75" in call_args

            assert result == -1

    @pytest.mark.asyncio()
    async def test_balance_simple_api_error(self, mock_update, mock_context):
        """Тест обработки ошибки API."""
        with patch(
            "src.telegram_bot.handlers.simplified_menu_handler.create_api_client_from_env"
        ) as mock_api:
            # Мокируем ошибку API
            api_instance = AsyncMock()
            api_instance.get_balance = AsyncMock(side_effect=Exception("API Error"))
            mock_api.return_value = api_instance

            result = await balance_simple(mock_update, mock_context)

            # Проверяем что было отправлено сообщение об ошибке (только одно)
            assert mock_update.message.reply_text.call_count >= 1

            assert result == -1


class TestStats:
    """Тесты для статистики."""

    @pytest.mark.asyncio()
    async def test_stats_simple_success(self, mock_update, mock_context):
        """Тест успешного получения статистики."""
        with patch(
            "src.telegram_bot.handlers.simplified_menu_handler.create_api_client_from_env"
        ) as mock_api:
            # Мокируем API клиент
            api_instance = AsyncMock()
            api_instance.get_user_inventory = AsyncMock(
                return_value={
                    "objects": [
                        {"title": "Item 1"},
                        {"title": "Item 2"},
                    ],
                }
            )
            mock_api.return_value = api_instance

            result = await stats_simple(mock_update, mock_context)

            # Проверяем что был запрос к API
            api_instance.get_user_inventory.assert_called_once()

            # Проверяем что сообщение было отправлено
            mock_update.message.reply_text.assert_called_once()
            call_args = mock_update.message.reply_text.call_args[0][0]
            assert "Ваша статистика" in call_args
            assert "На продаже" in call_args

            assert result == -1


class TestArbitrage:
    """Тесты для арбитража."""

    @pytest.mark.asyncio()
    async def test_arbitrage_start(self, mock_update, mock_context):
        """Тест запуска меню арбитража."""
        result = await arbitrage_start(mock_update, mock_context)

        # Проверяем что сообщение было отправлено
        mock_update.message.reply_text.assert_called_once()

        # Проверяем что вернули правильное состояние
        assert result == CHOOSING_ARB_MODE

    @pytest.mark.asyncio()
    async def test_arbitrage_all_games(self, mock_callback_update, mock_context):
        """Тест выбора всех игр."""
        result = await arbitrage_all_games(mock_callback_update, mock_context)

        # Проверяем что query был отвечен
        mock_callback_update.callback_query.answer.assert_called_once()

        # Проверяем что сообщение было изменено
        mock_callback_update.callback_query.edit_message_text.assert_called_once()

        # Проверяем что игры были сохранены
        assert "selected_games" in mock_context.user_data
        assert len(mock_context.user_data["selected_games"]) == 4

        # Проверяем следующее состояние
        assert result == WAITING_FOR_RANGE

    @pytest.mark.asyncio()
    async def test_arbitrage_manual_mode(self, mock_callback_update, mock_context):
        """Тест ручного режима."""
        result = await arbitrage_manual_mode(mock_callback_update, mock_context)

        mock_callback_update.callback_query.answer.assert_called_once()
        mock_callback_update.callback_query.edit_message_text.assert_called_once()

        assert result == SELECTING_GAME_MANUAL

    @pytest.mark.asyncio()
    async def test_arbitrage_select_game(self, mock_callback_update, mock_context):
        """Тест выбора игры."""
        mock_callback_update.callback_query.data = "simple_arb_game_csgo"

        result = await arbitrage_select_game(mock_callback_update, mock_context)

        # Проверяем что игра была сохранена
        assert "selected_games" in mock_context.user_data
        assert mock_context.user_data["selected_games"] == ["csgo"]

        assert result == WAITING_FOR_RANGE

    @pytest.mark.asyncio()
    async def test_arbitrage_process_range_invalid_format(self, mock_update, mock_context):
        """Тест невалидного формата диапазона."""
        mock_update.message.text = "invalid"

        result = await arbitrage_process_range(mock_update, mock_context)

        # Проверяем что было сообщение об ошибке
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args[0][0]
        assert "Неверный формат" in call_args

        # Остаемся в том же состоянии
        assert result == WAITING_FOR_RANGE

    @pytest.mark.asyncio()
    async def test_arbitrage_process_range_invalid_values(self, mock_update, mock_context):
        """Тест невалидных значений цен."""
        mock_update.message.text = "10-5"  # min > max

        result = await arbitrage_process_range(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args[0][0]
        assert "Некорректные" in call_args

        assert result == WAITING_FOR_RANGE

    @pytest.mark.asyncio()
    async def test_arbitrage_process_range_success(self, mock_update, mock_context):
        """Тест успешной обработки диапазона."""
        mock_update.message.text = "1-10"
        mock_context.user_data["selected_games"] = ["csgo"]

        with patch(
            "src.telegram_bot.handlers.simplified_menu_handler.create_api_client_from_env"
        ) as mock_api:
            with patch(
                "src.telegram_bot.handlers.simplified_menu_handler.ArbitrageScanner"
            ) as mock_scanner:
                # Мокируем сканер
                scanner_instance = AsyncMock()
                scanner_instance.scan_level = AsyncMock(return_value=[])
                mock_scanner.return_value = scanner_instance

                result = await arbitrage_process_range(mock_update, mock_context)

                # Проверяем что сканирование было запущено
                scanner_instance.scan_level.assert_called_once()

                # Проверяем что контекст был очищен
                assert len(mock_context.user_data) == 0

                assert result == -1


class TestTargets:
    """Тесты для таргетов."""

    @pytest.mark.asyncio()
    async def test_targets_start(self, mock_update, mock_context):
        """Тест запуска меню таргетов."""
        result = await targets_start(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()

        assert result == CHOOSING_TARGET_MODE  # Should show mode selection menu

    @pytest.mark.asyncio()
    async def test_targets_manual(self, mock_callback_update, mock_context):
        """Тест ручного режима таргетов."""
        result = await targets_manual(mock_callback_update, mock_context)

        mock_callback_update.callback_query.answer.assert_called_once()
        mock_callback_update.callback_query.edit_message_text.assert_called_once()

        assert result == WAITING_FOR_TARGET_NAME

    @pytest.mark.asyncio()
    async def test_targets_create_success(self, mock_update, mock_context):
        """Тест создания таргета."""
        mock_update.message.text = "AK-47 | Redline (FT)"

        with patch(
            "src.telegram_bot.handlers.simplified_menu_handler.create_api_client_from_env"
        ) as mock_api:
            with patch(
                "src.telegram_bot.handlers.simplified_menu_handler.TargetManager"
            ) as mock_manager:
                # Мокируем менеджер таргетов
                manager_instance = AsyncMock()
                manager_instance.create_target = AsyncMock(return_value={"success": True})
                mock_manager.return_value = manager_instance

                result = await targets_create(mock_update, mock_context)

                # Проверяем что таргет был создан
                manager_instance.create_target.assert_called_once()

                # Проверяем сообщение об успехе
                assert mock_update.message.reply_text.call_count >= 2  # Прогресс + успех

                assert result == -1

    @pytest.mark.asyncio()
    async def test_targets_auto(self, mock_callback_update, mock_context):
        """Тест автоматических таргетов."""
        with patch(
            "src.telegram_bot.handlers.simplified_menu_handler.create_api_client_from_env"
        ) as mock_api_factory:
            with patch(
                "src.telegram_bot.handlers.simplified_menu_handler.TargetManager"
            ) as mock_manager:
                # Мокируем API клиент
                api_instance = AsyncMock()
                api_instance.get_market_items = AsyncMock(
                    return_value={
                        "objects": [
                            {"title": "Item 1", "price": {"USD": "1000"}},
                            {"title": "Item 2", "price": {"USD": "2000"}},
                        ]
                    }
                )
                mock_api_factory.return_value = api_instance

                # Мокируем менеджер
                manager_instance = AsyncMock()
                manager_instance.create_smart_targets = AsyncMock(
                    return_value={
                        "created": [{"title": "Item 1"}],
                    }
                )
                mock_manager.return_value = manager_instance

                result = await targets_auto(mock_callback_update, mock_context)

                # Проверяем что get_market_items был вызван
                api_instance.get_market_items.assert_called_once()

                # Проверяем что умные таргеты были созданы
                manager_instance.create_smart_targets.assert_called_once()

                assert result == -1

    @pytest.mark.asyncio()
    async def test_targets_list_empty(self, mock_callback_update, mock_context):
        """Тест пустого списка таргетов."""
        with patch(
            "src.telegram_bot.handlers.simplified_menu_handler.create_api_client_from_env"
        ) as mock_api:
            with patch(
                "src.telegram_bot.handlers.simplified_menu_handler.TargetManager"
            ) as mock_manager:
                # Мокируем пустой список (правильный формат ответа DMarket API)
                manager_instance = AsyncMock()
                manager_instance.get_user_targets = AsyncMock(return_value={"Items": []})
                mock_manager.return_value = manager_instance

                result = await targets_list(mock_callback_update, mock_context)

                # Проверяем сообщение
                call_args = mock_callback_update.callback_query.edit_message_text.call_args[0][0]
                assert "Активных таргетов нет" in call_args

                assert result == -1

    @pytest.mark.asyncio()
    async def test_targets_list_with_items(self, mock_callback_update, mock_context):
        """Тест списка таргетов с предметами."""
        with patch(
            "src.telegram_bot.handlers.simplified_menu_handler.create_api_client_from_env"
        ) as mock_api:
            with patch(
                "src.telegram_bot.handlers.simplified_menu_handler.TargetManager"
            ) as mock_manager:
                # Мокируем список таргетов (правильный формат ответа DMarket API)
                manager_instance = AsyncMock()
                manager_instance.get_user_targets = AsyncMock(
                    return_value={
                        "Items": [
                            {"title": "Item 1", "price": 100000, "status": "активен"},
                            {"title": "Item 2", "price": 200000, "status": "активен"},
                        ]
                    }
                )
                mock_manager.return_value = manager_instance

                result = await targets_list(mock_callback_update, mock_context)

                # Проверяем сообщение
                call_args = mock_callback_update.callback_query.edit_message_text.call_args[0][0]
                assert "Ваши таргеты (2)" in call_args
                assert "Item 1" in call_args

                assert result == -1


class TestIntegration:
    """Интеграционные тесты для workflow."""

    @pytest.mark.asyncio()
    async def test_full_arbitrage_workflow_all_games(
        self, mock_update, mock_callback_update, mock_context
    ):
        """Тест полного workflow арбитража (все игры)."""
        # 1. Старт меню
        result = await arbitrage_start(mock_update, mock_context)
        assert result == CHOOSING_ARB_MODE

        # 2. Выбор всех игр
        result = await arbitrage_all_games(mock_callback_update, mock_context)
        assert result == WAITING_FOR_RANGE
        assert len(mock_context.user_data["selected_games"]) == 4

        # 3. Ввод диапазона
        mock_update.message.text = "5-20"

        with patch("src.telegram_bot.handlers.simplified_menu_handler.create_api_client_from_env"):
            with patch(
                "src.telegram_bot.handlers.simplified_menu_handler.ArbitrageScanner"
            ) as mock_scanner:
                scanner_instance = AsyncMock()
                scanner_instance.scan_level = AsyncMock(return_value=[])
                mock_scanner.return_value = scanner_instance

                result = await arbitrage_process_range(mock_update, mock_context)
                assert result == -1
                assert len(mock_context.user_data) == 0  # Очищен

    @pytest.mark.asyncio()
    async def test_full_target_manual_workflow(
        self, mock_update, mock_callback_update, mock_context
    ):
        """Тест полного workflow ручного таргета."""
        # 1. Старт меню таргетов
        result = await targets_start(mock_update, mock_context)
        assert result == CHOOSING_TARGET_MODE  # Should show mode selection menu

        # 2. Выбор ручного режима
        result = await targets_manual(mock_callback_update, mock_context)
        assert result == WAITING_FOR_TARGET_NAME

        # 3. Ввод названия
        mock_update.message.text = "Test Item"

        with patch("src.telegram_bot.handlers.simplified_menu_handler.create_api_client_from_env"):
            with patch(
                "src.telegram_bot.handlers.simplified_menu_handler.TargetManager"
            ) as mock_manager:
                manager_instance = AsyncMock()
                manager_instance.create_target = AsyncMock(return_value={"success": True})
                mock_manager.return_value = manager_instance

                result = await targets_create(mock_update, mock_context)
                assert result == -1
