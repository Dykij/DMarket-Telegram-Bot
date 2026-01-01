"""Тесты для обработчика уведомлений о ценах."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram import CallbackQuery, Update, User
from telegram.ext import ConversationHandler

from src.telegram_bot.handlers.price_alerts_handler import (
    ALERT_CONDITION,
    ALERT_PRICE,
    CALLBACK_ADD_ALERT,
    CALLBACK_ALERT_LIST,
    CALLBACK_CANCEL,
    CALLBACK_CONDITION_ABOVE,
    CALLBACK_CONDITION_BELOW,
    CALLBACK_REMOVE_ALERT,
    ITEM_NAME,
    PriceAlertsHandler,
)


# ======================== Fixtures ========================


@pytest.fixture()
def mock_user():
    """Создать мок объекта User."""
    user = MagicMock(spec=User)
    user.id = 123456789
    user.username = "testuser"
    user.first_name = "Test"
    return user


@pytest.fixture()
def mock_message(mock_user):
    """Создать мок объекта Message."""
    message = MagicMock()
    message.reply_text = AsyncMock()
    message.from_user = mock_user
    message.text = "Test item name"
    return message


@pytest.fixture()
def mock_callback_query(mock_user):
    """Создать мок объекта CallbackQuery."""
    query = MagicMock(spec=CallbackQuery)
    query.answer = AsyncMock()
    query.edit_message_text = AsyncMock()
    query.data = CALLBACK_ALERT_LIST
    query.from_user = mock_user
    return query


@pytest.fixture()
def mock_update(mock_user, mock_callback_query, mock_message):
    """Создать мок объекта Update."""
    update = MagicMock(spec=Update)
    update.callback_query = mock_callback_query
    update.effective_user = mock_user
    update.message = mock_message
    update.effective_chat = MagicMock()
    update.effective_chat.id = 123456789
    return update


@pytest.fixture()
def mock_context():
    """Создать мок объекта CallbackContext."""
    context = MagicMock()
    context.bot = MagicMock()
    context.bot.send_message = AsyncMock()
    context.user_data = {}
    context.chat_data = {}
    return context


@pytest.fixture()
def mock_api_client():
    """Создать мок объекта DMarketAPI."""
    client = MagicMock()
    client.get_market_items = AsyncMock(return_value={"objects": []})
    return client


@pytest.fixture()
def price_alerts_handler(mock_api_client):
    """Создать экземпляр PriceAlertsHandler."""
    with patch("src.telegram_bot.handlers.price_alerts_handler.RealtimePriceWatcher"):
        handler = PriceAlertsHandler(mock_api_client)
        handler.price_watcher = MagicMock()
        handler.price_watcher.start = AsyncMock(return_value=True)
        handler.price_watcher.register_alert_handler = MagicMock()
        return handler


# ======================== Constants Tests ========================


class TestConstants:
    """Тесты для констант модуля."""

    def test_states_are_sequential(self):
        """Состояния ConversationHandler должны быть последовательными."""
        assert ITEM_NAME == 0
        assert ALERT_PRICE == 1
        assert ALERT_CONDITION == 2

    def test_callback_data_defined(self):
        """Все callback данные должны быть определены."""
        assert CALLBACK_ALERT_LIST == "alert_list"
        assert CALLBACK_ADD_ALERT == "add_alert"
        assert CALLBACK_REMOVE_ALERT == "rem_alert:"
        assert CALLBACK_CANCEL == "alert_cancel"
        assert CALLBACK_CONDITION_BELOW == "cond_below"
        assert CALLBACK_CONDITION_ABOVE == "cond_above"


# ======================== PriceAlertsHandler Initialization Tests ========================


class TestPriceAlertsHandlerInit:
    """Тесты для инициализации PriceAlertsHandler."""

    def test_init_stores_api_client(self, mock_api_client):
        """Должен сохранять API клиент."""
        with patch(
            "src.telegram_bot.handlers.price_alerts_handler.RealtimePriceWatcher"
        ):
            handler = PriceAlertsHandler(mock_api_client)
            assert handler.api_client == mock_api_client

    def test_init_creates_price_watcher(self, mock_api_client):
        """Должен создавать price_watcher."""
        with patch(
            "src.telegram_bot.handlers.price_alerts_handler.RealtimePriceWatcher"
        ) as mock_watcher:
            handler = PriceAlertsHandler(mock_api_client)
            mock_watcher.assert_called_once_with(mock_api_client)

    def test_init_watcher_not_started(self, price_alerts_handler):
        """Watcher не должен быть запущен при инициализации."""
        assert price_alerts_handler._is_watcher_started is False

    def test_init_empty_temp_data(self, price_alerts_handler):
        """Временные данные должны быть пустыми при инициализации."""
        assert price_alerts_handler._user_temp_data == {}


# ======================== ensure_watcher_started Tests ========================


class TestEnsureWatcherStarted:
    """Тесты для метода ensure_watcher_started."""

    @pytest.mark.asyncio()
    async def test_starts_watcher_if_not_started(self, price_alerts_handler):
        """Должен запускать watcher если он не запущен."""
        price_alerts_handler._is_watcher_started = False
        await price_alerts_handler.ensure_watcher_started()
        price_alerts_handler.price_watcher.start.assert_called_once()

    @pytest.mark.asyncio()
    async def test_does_not_start_if_already_started(self, price_alerts_handler):
        """Не должен запускать watcher если он уже запущен."""
        price_alerts_handler._is_watcher_started = True
        await price_alerts_handler.ensure_watcher_started()
        price_alerts_handler.price_watcher.start.assert_not_called()

    @pytest.mark.asyncio()
    async def test_sets_flag_on_successful_start(self, price_alerts_handler):
        """Должен устанавливать флаг при успешном запуске."""
        price_alerts_handler._is_watcher_started = False
        price_alerts_handler.price_watcher.start = AsyncMock(return_value=True)
        await price_alerts_handler.ensure_watcher_started()
        assert price_alerts_handler._is_watcher_started is True

    @pytest.mark.asyncio()
    async def test_does_not_set_flag_on_failed_start(self, price_alerts_handler):
        """Не должен устанавливать флаг при неудачном запуске."""
        price_alerts_handler._is_watcher_started = False
        price_alerts_handler.price_watcher.start = AsyncMock(return_value=False)
        await price_alerts_handler.ensure_watcher_started()
        assert price_alerts_handler._is_watcher_started is False


# ======================== handle_price_alerts_command Tests ========================


class TestHandlePriceAlertsCommand:
    """Тесты для метода handle_price_alerts_command."""

    @pytest.mark.asyncio()
    async def test_returns_none_if_no_message(
        self, price_alerts_handler, mock_update, mock_context
    ):
        """Должен возвращать None если нет сообщения."""
        mock_update.message = None
        result = await price_alerts_handler.handle_price_alerts_command(
            mock_update, mock_context
        )
        assert result is None

    @pytest.mark.asyncio()
    async def test_ensures_watcher_started(
        self, price_alerts_handler, mock_update, mock_context
    ):
        """Должен запускать watcher."""
        await price_alerts_handler.handle_price_alerts_command(
            mock_update, mock_context
        )
        price_alerts_handler.price_watcher.start.assert_called_once()

    @pytest.mark.asyncio()
    async def test_sends_keyboard_with_list_and_add_buttons(
        self, price_alerts_handler, mock_update, mock_context
    ):
        """Должен отправлять клавиатуру со списком и добавлением."""
        await price_alerts_handler.handle_price_alerts_command(
            mock_update, mock_context
        )

        call_args = mock_update.message.reply_text.call_args
        reply_markup = call_args.kwargs.get("reply_markup") or call_args[1].get(
            "reply_markup"
        )

        button_texts = [btn.text for row in reply_markup.inline_keyboard for btn in row]
        assert "📋 Список оповещений" in button_texts
        assert "➕ Добавить оповещение" in button_texts

    @pytest.mark.asyncio()
    async def test_uses_markdown_parse_mode(
        self, price_alerts_handler, mock_update, mock_context
    ):
        """Должен использовать Markdown parse mode."""
        await price_alerts_handler.handle_price_alerts_command(
            mock_update, mock_context
        )

        call_args = mock_update.message.reply_text.call_args
        assert call_args.kwargs.get("parse_mode") == "Markdown"


# ======================== handle_alert_list_callback Tests ========================


class TestHandleAlertListCallback:
    """Тесты для метода handle_alert_list_callback."""

    @pytest.mark.asyncio()
    async def test_returns_none_if_no_query(
        self, price_alerts_handler, mock_update, mock_context
    ):
        """Должен возвращать None если нет callback_query."""
        mock_update.callback_query = None
        result = await price_alerts_handler.handle_alert_list_callback(
            mock_update, mock_context
        )
        assert result is None

    @pytest.mark.asyncio()
    async def test_answers_callback_query(
        self, price_alerts_handler, mock_update, mock_context
    ):
        """Должен отвечать на callback_query."""
        await price_alerts_handler.handle_alert_list_callback(mock_update, mock_context)
        mock_update.callback_query.answer.assert_called_once()

    @pytest.mark.asyncio()
    async def test_returns_none_if_no_effective_user(
        self, price_alerts_handler, mock_update, mock_context
    ):
        """Должен возвращать None если нет effective_user."""
        mock_update.effective_user = None
        await price_alerts_handler.handle_alert_list_callback(mock_update, mock_context)
        # Не должен вызывать edit_message_text после answer
        assert mock_update.callback_query.edit_message_text.call_count == 0

    @pytest.mark.asyncio()
    async def test_returns_none_if_no_user_data(
        self, price_alerts_handler, mock_update, mock_context
    ):
        """Должен возвращать None если нет user_data."""
        mock_context.user_data = None
        await price_alerts_handler.handle_alert_list_callback(mock_update, mock_context)
        # После answer должен вернуться
        mock_update.callback_query.edit_message_text.assert_not_called()

    @pytest.mark.asyncio()
    async def test_shows_empty_message_if_no_alerts(
        self, price_alerts_handler, mock_update, mock_context
    ):
        """Должен показывать сообщение если нет оповещений."""
        mock_context.user_data = {}
        await price_alerts_handler.handle_alert_list_callback(mock_update, mock_context)

        call_args = mock_update.callback_query.edit_message_text.call_args
        message = call_args[0][0] if call_args[0] else call_args.kwargs.get("text", "")
        assert "У вас пока нет активных оповещений" in message

    @pytest.mark.asyncio()
    async def test_shows_alerts_list(
        self, price_alerts_handler, mock_update, mock_context
    ):
        """Должен показывать список оповещений."""
        mock_context.user_data = {
            "price_alerts": {
                "alert_1": {
                    "market_hash_name": "AK-47 | Redline",
                    "target_price": 25.0,
                    "condition": "below",
                }
            }
        }
        await price_alerts_handler.handle_alert_list_callback(mock_update, mock_context)

        call_args = mock_update.callback_query.edit_message_text.call_args
        message = call_args[0][0] if call_args[0] else call_args.kwargs.get("text", "")
        assert "AK-47 | Redline" in message
        assert "25.00" in message

    @pytest.mark.asyncio()
    async def test_shows_delete_buttons_for_alerts(
        self, price_alerts_handler, mock_update, mock_context
    ):
        """Должен показывать кнопки удаления для оповещений."""
        mock_context.user_data = {
            "price_alerts": {
                "alert_1": {
                    "market_hash_name": "AWP | Asiimov",
                    "target_price": 50.0,
                    "condition": "above",
                }
            }
        }
        await price_alerts_handler.handle_alert_list_callback(mock_update, mock_context)

        call_args = mock_update.callback_query.edit_message_text.call_args
        reply_markup = call_args.kwargs.get("reply_markup")
        button_texts = [btn.text for row in reply_markup.inline_keyboard for btn in row]
        assert any("Удалить" in text for text in button_texts)


# ======================== handle_add_alert_callback Tests ========================


class TestHandleAddAlertCallback:
    """Тесты для метода handle_add_alert_callback."""

    @pytest.mark.asyncio()
    async def test_returns_end_if_no_query(
        self, price_alerts_handler, mock_update, mock_context
    ):
        """Должен возвращать END если нет callback_query."""
        mock_update.callback_query = None
        result = await price_alerts_handler.handle_add_alert_callback(
            mock_update, mock_context
        )
        assert result == ConversationHandler.END

    @pytest.mark.asyncio()
    async def test_returns_end_if_no_effective_user(
        self, price_alerts_handler, mock_update, mock_context
    ):
        """Должен возвращать END если нет effective_user."""
        mock_update.effective_user = None
        result = await price_alerts_handler.handle_add_alert_callback(
            mock_update, mock_context
        )
        assert result == ConversationHandler.END

    @pytest.mark.asyncio()
    async def test_answers_callback_query(
        self, price_alerts_handler, mock_update, mock_context
    ):
        """Должен отвечать на callback_query."""
        await price_alerts_handler.handle_add_alert_callback(mock_update, mock_context)
        mock_update.callback_query.answer.assert_called_once()

    @pytest.mark.asyncio()
    async def test_initializes_temp_data_for_user(
        self, price_alerts_handler, mock_update, mock_context
    ):
        """Должен инициализировать временные данные для пользователя."""
        await price_alerts_handler.handle_add_alert_callback(mock_update, mock_context)
        user_id = str(mock_update.effective_user.id)
        assert user_id in price_alerts_handler._user_temp_data
        assert price_alerts_handler._user_temp_data[user_id] == {}

    @pytest.mark.asyncio()
    async def test_returns_item_name_state(
        self, price_alerts_handler, mock_update, mock_context
    ):
        """Должен возвращать состояние ITEM_NAME."""
        result = await price_alerts_handler.handle_add_alert_callback(
            mock_update, mock_context
        )
        assert result == ITEM_NAME

    @pytest.mark.asyncio()
    async def test_edits_message_with_instructions(
        self, price_alerts_handler, mock_update, mock_context
    ):
        """Должен редактировать сообщение с инструкциями."""
        await price_alerts_handler.handle_add_alert_callback(mock_update, mock_context)

        call_args = mock_update.callback_query.edit_message_text.call_args
        message = call_args[0][0] if call_args[0] else call_args.kwargs.get("text", "")
        assert "Введите полное название предмета" in message


# ======================== handle_item_name_input Tests ========================


class TestHandleItemNameInput:
    """Тесты для метода handle_item_name_input."""

    @pytest.mark.asyncio()
    async def test_returns_end_if_no_effective_user(
        self, price_alerts_handler, mock_update, mock_context
    ):
        """Должен возвращать END если нет effective_user."""
        mock_update.effective_user = None
        result = await price_alerts_handler.handle_item_name_input(
            mock_update, mock_context
        )
        assert result == ConversationHandler.END

    @pytest.mark.asyncio()
    async def test_returns_end_if_no_message(
        self, price_alerts_handler, mock_update, mock_context
    ):
        """Должен возвращать END если нет message."""
        mock_update.message = None
        result = await price_alerts_handler.handle_item_name_input(
            mock_update, mock_context
        )
        assert result == ConversationHandler.END

    @pytest.mark.asyncio()
    async def test_returns_end_if_no_message_text(
        self, price_alerts_handler, mock_update, mock_context
    ):
        """Должен возвращать END если нет text."""
        mock_update.message.text = None
        result = await price_alerts_handler.handle_item_name_input(
            mock_update, mock_context
        )
        assert result == ConversationHandler.END

    @pytest.mark.asyncio()
    async def test_saves_item_name_to_temp_data(
        self, price_alerts_handler, mock_update, mock_context
    ):
        """Должен сохранять название предмета во временные данные."""
        user_id = str(mock_update.effective_user.id)
        price_alerts_handler._user_temp_data[user_id] = {}
        mock_update.message.text = "AWP | Asiimov (Field-Tested)"

        await price_alerts_handler.handle_item_name_input(mock_update, mock_context)

        assert (
            price_alerts_handler._user_temp_data[user_id]["item_name"]
            == "AWP | Asiimov (Field-Tested)"
        )

    @pytest.mark.asyncio()
    async def test_strips_whitespace_from_item_name(
        self, price_alerts_handler, mock_update, mock_context
    ):
        """Должен убирать пробелы из названия предмета."""
        user_id = str(mock_update.effective_user.id)
        price_alerts_handler._user_temp_data[user_id] = {}
        mock_update.message.text = "  AWP | Asiimov  "

        await price_alerts_handler.handle_item_name_input(mock_update, mock_context)

        assert (
            price_alerts_handler._user_temp_data[user_id]["item_name"]
            == "AWP | Asiimov"
        )

    @pytest.mark.asyncio()
    async def test_returns_alert_price_state(
        self, price_alerts_handler, mock_update, mock_context
    ):
        """Должен возвращать состояние ALERT_PRICE."""
        user_id = str(mock_update.effective_user.id)
        price_alerts_handler._user_temp_data[user_id] = {}

        result = await price_alerts_handler.handle_item_name_input(
            mock_update, mock_context
        )

        assert result == ALERT_PRICE

    @pytest.mark.asyncio()
    async def test_sends_reply_with_item_name(
        self, price_alerts_handler, mock_update, mock_context
    ):
        """Должен отправлять ответ с названием предмета."""
        user_id = str(mock_update.effective_user.id)
        price_alerts_handler._user_temp_data[user_id] = {}
        mock_update.message.text = "AK-47 | Redline"

        await price_alerts_handler.handle_item_name_input(mock_update, mock_context)

        call_args = mock_update.message.reply_text.call_args
        message = call_args[0][0] if call_args[0] else call_args.kwargs.get("text", "")
        assert "AK-47 | Redline" in message


# ======================== handle_alert_price_input Tests ========================


class TestHandleAlertPriceInput:
    """Тесты для метода handle_alert_price_input."""

    @pytest.mark.asyncio()
    async def test_returns_end_if_no_effective_user(
        self, price_alerts_handler, mock_update, mock_context
    ):
        """Должен возвращать END если нет effective_user."""
        mock_update.effective_user = None
        result = await price_alerts_handler.handle_alert_price_input(
            mock_update, mock_context
        )
        assert result == ConversationHandler.END

    @pytest.mark.asyncio()
    async def test_returns_end_if_no_message(
        self, price_alerts_handler, mock_update, mock_context
    ):
        """Должен возвращать END если нет message."""
        mock_update.message = None
        result = await price_alerts_handler.handle_alert_price_input(
            mock_update, mock_context
        )
        assert result == ConversationHandler.END

    @pytest.mark.asyncio()
    async def test_returns_end_if_no_message_text(
        self, price_alerts_handler, mock_update, mock_context
    ):
        """Должен возвращать END если нет text."""
        mock_update.message.text = None
        result = await price_alerts_handler.handle_alert_price_input(
            mock_update, mock_context
        )
        assert result == ConversationHandler.END


# ======================== Edge Cases Tests ========================


class TestEdgeCases:
    """Тесты для граничных случаев."""

    def test_callback_remove_alert_prefix(self):
        """CALLBACK_REMOVE_ALERT должен быть префиксом."""
        assert CALLBACK_REMOVE_ALERT.endswith(":")

    @pytest.mark.asyncio()
    async def test_multiple_alerts_displayed(
        self, price_alerts_handler, mock_update, mock_context
    ):
        """Должен отображать несколько оповещений."""
        mock_context.user_data = {
            "price_alerts": {
                "alert_1": {
                    "market_hash_name": "Item 1",
                    "target_price": 10.0,
                    "condition": "below",
                },
                "alert_2": {
                    "market_hash_name": "Item 2",
                    "target_price": 20.0,
                    "condition": "above",
                },
            }
        }
        await price_alerts_handler.handle_alert_list_callback(mock_update, mock_context)

        call_args = mock_update.callback_query.edit_message_text.call_args
        message = call_args[0][0] if call_args[0] else call_args.kwargs.get("text", "")
        assert "Item 1" in message
        assert "Item 2" in message

    @pytest.mark.asyncio()
    async def test_condition_below_displays_correctly(
        self, price_alerts_handler, mock_update, mock_context
    ):
        """Условие 'below' должно отображаться как ≤."""
        mock_context.user_data = {
            "price_alerts": {
                "alert_1": {
                    "market_hash_name": "Test Item",
                    "target_price": 15.0,
                    "condition": "below",
                }
            }
        }
        await price_alerts_handler.handle_alert_list_callback(mock_update, mock_context)

        call_args = mock_update.callback_query.edit_message_text.call_args
        message = call_args[0][0] if call_args[0] else call_args.kwargs.get("text", "")
        assert "≤" in message

    @pytest.mark.asyncio()
    async def test_condition_above_displays_correctly(
        self, price_alerts_handler, mock_update, mock_context
    ):
        """Условие 'above' должно отображаться как ≥."""
        mock_context.user_data = {
            "price_alerts": {
                "alert_1": {
                    "market_hash_name": "Test Item",
                    "target_price": 15.0,
                    "condition": "above",
                }
            }
        }
        await price_alerts_handler.handle_alert_list_callback(mock_update, mock_context)

        call_args = mock_update.callback_query.edit_message_text.call_args
        message = call_args[0][0] if call_args[0] else call_args.kwargs.get("text", "")
        assert "≥" in message

    @pytest.mark.asyncio()
    async def test_price_formatted_with_two_decimals(
        self, price_alerts_handler, mock_update, mock_context
    ):
        """Цена должна форматироваться с двумя знаками после запятой."""
        mock_context.user_data = {
            "price_alerts": {
                "alert_1": {
                    "market_hash_name": "Test Item",
                    "target_price": 15.5,
                    "condition": "below",
                }
            }
        }
        await price_alerts_handler.handle_alert_list_callback(mock_update, mock_context)

        call_args = mock_update.callback_query.edit_message_text.call_args
        message = call_args[0][0] if call_args[0] else call_args.kwargs.get("text", "")
        assert "$15.50" in message


# ======================== Integration Tests ========================


class TestIntegration:
    """Интеграционные тесты."""

    @pytest.mark.asyncio()
    async def test_full_add_alert_flow_step_1(
        self, price_alerts_handler, mock_update, mock_context
    ):
        """Полный flow добавления оповещения - шаг 1."""
        mock_update.callback_query.data = CALLBACK_ADD_ALERT

        result = await price_alerts_handler.handle_add_alert_callback(
            mock_update, mock_context
        )

        assert result == ITEM_NAME
        user_id = str(mock_update.effective_user.id)
        assert user_id in price_alerts_handler._user_temp_data

    @pytest.mark.asyncio()
    async def test_full_add_alert_flow_step_2(
        self, price_alerts_handler, mock_update, mock_context
    ):
        """Полный flow добавления оповещения - шаг 2."""
        user_id = str(mock_update.effective_user.id)
        price_alerts_handler._user_temp_data[user_id] = {}
        mock_update.message.text = "AWP | Dragon Lore"

        result = await price_alerts_handler.handle_item_name_input(
            mock_update, mock_context
        )

        assert result == ALERT_PRICE
        assert (
            price_alerts_handler._user_temp_data[user_id]["item_name"]
            == "AWP | Dragon Lore"
        )
