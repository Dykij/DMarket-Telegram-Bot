"""Тесты для обработчика уведомлений о ценах (PriceAlertsHandler).

Покрывает все функции модуля price_alerts_handler.py с целью достижения 70%+ покрытия.
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from telegram import CallbackQuery, Message, Update, User
from telegram.ext import CallbackContext, ConversationHandler

from src.telegram_bot.constants import PRICE_ALERT_STORAGE_KEY
from src.telegram_bot.price_alerts_handler import (
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
def mock_api_client():
    """Создать мок DMarketAPI клиента."""
    return MagicMock()


@pytest.fixture()
def price_alerts_handler(mock_api_client):
    """Создать экземпляр PriceAlertsHandler."""
    with patch("src.telegram_bot.price_alerts_handler.RealtimePriceWatcher"):
        handler = PriceAlertsHandler(mock_api_client)
        handler._is_watcher_started = False
        return handler


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
    message = MagicMock(spec=Message)
    message.reply_text = AsyncMock()
    message.from_user = mock_user
    message.text = "Test message"
    return message


@pytest.fixture()
def mock_callback_query(mock_user, mock_message):
    """Создать мок объекта CallbackQuery."""
    query = MagicMock(spec=CallbackQuery)
    query.answer = AsyncMock()
    query.edit_message_text = AsyncMock()
    query.data = CALLBACK_ALERT_LIST
    query.from_user = mock_user
    query.message = mock_message
    return query


@pytest.fixture()
def mock_update(mock_user, mock_message, mock_callback_query):
    """Создать мок объекта Update."""
    update = MagicMock(spec=Update)
    update.message = mock_message
    update.callback_query = mock_callback_query
    update.effective_user = mock_user
    return update


@pytest.fixture()
def mock_context():
    """Создать мок CallbackContext."""
    context = MagicMock(spec=CallbackContext)
    context.user_data = {}
    context.bot = MagicMock()
    context.bot.send_message = AsyncMock()
    return context


# ======================== Test: Initialization ========================


class TestPriceAlertsHandlerInitialization:
    """Тесты инициализации PriceAlertsHandler."""

    @pytest.mark.asyncio()
    async def test_initialization_success(self, mock_api_client):
        """Тест успешной инициализации обработчика."""
        with patch("src.telegram_bot.price_alerts_handler.RealtimePriceWatcher") as MockWatcher:
            handler = PriceAlertsHandler(mock_api_client)

            assert handler.api_client is mock_api_client
            assert handler._user_temp_data == {}
            assert handler._is_watcher_started is False
            MockWatcher.assert_called_once_with(mock_api_client)

    @pytest.mark.asyncio()
    async def test_alert_handler_registered(self, mock_api_client):
        """Тест регистрации обработчика оповещений."""
        with patch("src.telegram_bot.price_alerts_handler.RealtimePriceWatcher") as MockWatcher:
            mock_watcher_instance = MockWatcher.return_value
            mock_watcher_instance.register_alert_handler = MagicMock()

            handler = PriceAlertsHandler(mock_api_client)

            mock_watcher_instance.register_alert_handler.assert_called_once()
            # Проверяем, что передан метод _handle_alert_triggered
            call_args = mock_watcher_instance.register_alert_handler.call_args
            assert call_args[0][0] == handler._handle_alert_triggered


# ======================== Test: ensure_watcher_started ========================


class TestEnsureWatcherStarted:
    """Тесты для ensure_watcher_started."""

    @pytest.mark.asyncio()
    async def test_starts_watcher_when_not_started(self, price_alerts_handler):
        """Тест запуска наблюдателя, когда он не запущен."""
        price_alerts_handler.price_watcher.start = AsyncMock(return_value=True)
        price_alerts_handler._is_watcher_started = False

        await price_alerts_handler.ensure_watcher_started()

        assert price_alerts_handler._is_watcher_started is True
        price_alerts_handler.price_watcher.start.assert_called_once()

    @pytest.mark.asyncio()
    async def test_does_not_start_when_already_started(self, price_alerts_handler):
        """Тест, что наблюдатель не запускается повторно."""
        price_alerts_handler.price_watcher.start = AsyncMock(return_value=True)
        price_alerts_handler._is_watcher_started = True

        await price_alerts_handler.ensure_watcher_started()

        price_alerts_handler.price_watcher.start.assert_not_called()

    @pytest.mark.asyncio()
    async def test_handles_start_failure(self, price_alerts_handler):
        """Тест обработки ошибки запуска наблюдателя."""
        price_alerts_handler.price_watcher.start = AsyncMock(return_value=False)
        price_alerts_handler._is_watcher_started = False

        await price_alerts_handler.ensure_watcher_started()

        assert price_alerts_handler._is_watcher_started is False


# ======================== Test: handle_price_alerts_command ========================


class TestHandlePriceAlertsCommand:
    """Тесты для handle_price_alerts_command."""

    @pytest.mark.asyncio()
    async def test_command_sends_menu(self, price_alerts_handler, mock_update, mock_context):
        """Тест отправки меню при вызове команды."""
        price_alerts_handler.ensure_watcher_started = AsyncMock()

        await price_alerts_handler.handle_price_alerts_command(mock_update, mock_context)

        price_alerts_handler.ensure_watcher_started.assert_called_once()
        mock_update.message.reply_text.assert_called_once()

        # Проверка содержимого сообщения (первый позиционный аргумент)
        call_args = mock_update.message.reply_text.call_args
        assert "Оповещения о ценах" in call_args[0][0]

        # Проверка клавиатуры (keyword argument)
        assert "reply_markup" in call_args.kwargs
        assert call_args.kwargs["reply_markup"] is not None

    @pytest.mark.asyncio()
    async def test_command_creates_keyboard_with_buttons(
        self, price_alerts_handler, mock_update, mock_context
    ):
        """Тест создания клавиатуры с нужными кнопками."""
        price_alerts_handler.ensure_watcher_started = AsyncMock()

        await price_alerts_handler.handle_price_alerts_command(mock_update, mock_context)

        call_kwargs = mock_update.message.reply_text.call_args.kwargs
        keyboard = call_kwargs["reply_markup"].inline_keyboard

        # Проверяем наличие обеих кнопок
        assert len(keyboard) == 2
        assert keyboard[0][0].text == "📋 Список оповещений"
        assert keyboard[0][0].callback_data == CALLBACK_ALERT_LIST
        assert keyboard[1][0].text == "➕ Добавить оповещение"
        assert keyboard[1][0].callback_data == CALLBACK_ADD_ALERT


# ======================== Test: handle_alert_list_callback ========================


class TestHandleAlertListCallback:
    """Тесты для handle_alert_list_callback."""

    @pytest.mark.asyncio()
    async def test_shows_empty_list_message(self, price_alerts_handler, mock_update, mock_context):
        """Тест отображения сообщения о пустом списке оповещений."""
        mock_context.user_data = {}

        await price_alerts_handler.handle_alert_list_callback(mock_update, mock_context)

        mock_update.callback_query.answer.assert_called_once()
        mock_update.callback_query.edit_message_text.assert_called_once()

        # Используем позиционный аргумент
        call_args = mock_update.callback_query.edit_message_text.call_args
        text_arg = call_args[0][0] if call_args[0] else ""
        assert "нет активных оповещений" in text_arg

    @pytest.mark.asyncio()
    async def test_displays_alerts_list(self, price_alerts_handler, mock_update, mock_context):
        """Тест отображения списка оповещений."""
        alert_id = str(uuid4())
        mock_context.user_data = {
            PRICE_ALERT_STORAGE_KEY: {
                alert_id: {
                    "market_hash_name": "AK-47 | Redline (FT)",
                    "target_price": 10.50,
                    "condition": "below",
                }
            }
        }

        await price_alerts_handler.handle_alert_list_callback(mock_update, mock_context)

        # Используем позиционный аргумент
        call_args = mock_update.callback_query.edit_message_text.call_args
        text_arg = call_args[0][0] if call_args[0] else ""
        assert "AK-47 | Redline (FT)" in text_arg
        assert "$10.50" in text_arg
        assert "≤" in text_arg  # Condition "below"

    @pytest.mark.asyncio()
    async def test_creates_remove_buttons_for_each_alert(
        self, price_alerts_handler, mock_update, mock_context
    ):
        """Тест создания кнопок удаления для каждого оповещения."""
        alert_id_1 = str(uuid4())
        alert_id_2 = str(uuid4())
        mock_context.user_data = {
            PRICE_ALERT_STORAGE_KEY: {
                alert_id_1: {
                    "market_hash_name": "AK-47 | Redline (FT)",
                    "target_price": 10.50,
                    "condition": "below",
                },
                alert_id_2: {
                    "market_hash_name": "AWP | Asiimov (FT)",
                    "target_price": 50.00,
                    "condition": "above",
                },
            }
        }

        await price_alerts_handler.handle_alert_list_callback(mock_update, mock_context)

        call_kwargs = mock_update.callback_query.edit_message_text.call_args.kwargs
        keyboard = call_kwargs["reply_markup"].inline_keyboard

        # Должно быть 3 строки: 2 для удаления + 1 для добавления
        assert len(keyboard) == 3
        assert "Удалить AK-47" in keyboard[0][0].text
        assert "Удалить AWP" in keyboard[1][0].text
        assert CALLBACK_REMOVE_ALERT in keyboard[0][0].callback_data


# ======================== Test: handle_add_alert_callback ========================


class TestHandleAddAlertCallback:
    """Тесты для handle_add_alert_callback."""

    @pytest.mark.asyncio()
    async def test_starts_conversation(self, price_alerts_handler, mock_update, mock_context):
        """Тест начала разговора для добавления оповещения."""
        result = await price_alerts_handler.handle_add_alert_callback(mock_update, mock_context)

        assert result == ITEM_NAME
        mock_update.callback_query.answer.assert_called_once()

    @pytest.mark.asyncio()
    async def test_initializes_temp_data(self, price_alerts_handler, mock_update, mock_context):
        """Тест инициализации временных данных пользователя."""
        user_id = str(mock_update.effective_user.id)

        await price_alerts_handler.handle_add_alert_callback(mock_update, mock_context)

        assert user_id in price_alerts_handler._user_temp_data
        assert price_alerts_handler._user_temp_data[user_id] == {}

    @pytest.mark.asyncio()
    async def test_sends_item_name_prompt(self, price_alerts_handler, mock_update, mock_context):
        """Тест отправки запроса на ввод названия предмета."""
        await price_alerts_handler.handle_add_alert_callback(mock_update, mock_context)

        # Проверка сообщения (первый позиционный аргумент)
        call_args = mock_update.callback_query.edit_message_text.call_args
        assert "Введите полное название предмета" in call_args[0][0]
        assert call_args.kwargs.get("parse_mode") == "Markdown"


# ======================== Test: handle_item_name_input ========================


class TestHandleItemNameInput:
    """Тесты для handle_item_name_input."""

    @pytest.mark.asyncio()
    async def test_saves_item_name_to_temp_data(
        self, price_alerts_handler, mock_update, mock_context
    ):
        """Тест сохранения названия предмета во временные данные."""
        user_id = str(mock_update.effective_user.id)
        price_alerts_handler._user_temp_data[user_id] = {}
        mock_update.message.text = "AK-47 | Redline (FT)"

        result = await price_alerts_handler.handle_item_name_input(mock_update, mock_context)

        assert result == ALERT_PRICE
        assert price_alerts_handler._user_temp_data[user_id]["item_name"] == "AK-47 | Redline (FT)"

    @pytest.mark.asyncio()
    async def test_handles_whitespace_in_item_name(
        self, price_alerts_handler, mock_update, mock_context
    ):
        """Тест обработки пробелов в названии предмета."""
        user_id = str(mock_update.effective_user.id)
        price_alerts_handler._user_temp_data[user_id] = {}
        mock_update.message.text = "  AWP | Asiimov (FT)  "

        await price_alerts_handler.handle_item_name_input(mock_update, mock_context)

        assert price_alerts_handler._user_temp_data[user_id]["item_name"] == "AWP | Asiimov (FT)"

    @pytest.mark.asyncio()
    async def test_sends_price_prompt(self, price_alerts_handler, mock_update, mock_context):
        """Тест отправки запроса на ввод цены."""
        user_id = str(mock_update.effective_user.id)
        price_alerts_handler._user_temp_data[user_id] = {}
        mock_update.message.text = "AK-47 | Redline (FT)"

        await price_alerts_handler.handle_item_name_input(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        # Проверка сообщения (первый позиционный аргумент)
        call_args = mock_update.message.reply_text.call_args
        assert "введите целевую цену" in call_args[0][0].lower()


# ======================== Test: handle_alert_price_input ========================


class TestHandleAlertPriceInput:
    """Тесты для handle_alert_price_input."""

    @pytest.mark.asyncio()
    async def test_saves_valid_price(self, price_alerts_handler, mock_update, mock_context):
        """Тест сохранения валидной цены."""
        user_id = str(mock_update.effective_user.id)
        price_alerts_handler._user_temp_data[user_id] = {"item_name": "AK-47 | Redline (FT)"}
        mock_update.message.text = "50.5"

        result = await price_alerts_handler.handle_alert_price_input(mock_update, mock_context)

        assert result == ALERT_CONDITION
        assert price_alerts_handler._user_temp_data[user_id]["target_price"] == 50.5

    @pytest.mark.asyncio()
    async def test_rejects_negative_price(self, price_alerts_handler, mock_update, mock_context):
        """Тест отклонения отрицательной цены."""
        user_id = str(mock_update.effective_user.id)
        price_alerts_handler._user_temp_data[user_id] = {}
        mock_update.message.text = "-10"

        result = await price_alerts_handler.handle_alert_price_input(mock_update, mock_context)

        assert result == ALERT_PRICE
        mock_update.message.reply_text.assert_called_once()
        # Проверка сообщения (первый позиционный аргумент)
        call_args = mock_update.message.reply_text.call_args
        assert "корректное число" in call_args[0][0].lower()

    @pytest.mark.asyncio()
    async def test_rejects_zero_price(self, price_alerts_handler, mock_update, mock_context):
        """Тест отклонения нулевой цены."""
        user_id = str(mock_update.effective_user.id)
        price_alerts_handler._user_temp_data[user_id] = {}
        mock_update.message.text = "0"

        result = await price_alerts_handler.handle_alert_price_input(mock_update, mock_context)

        assert result == ALERT_PRICE

    @pytest.mark.asyncio()
    async def test_rejects_non_numeric_input(self, price_alerts_handler, mock_update, mock_context):
        """Тест отклонения нечислового ввода."""
        user_id = str(mock_update.effective_user.id)
        price_alerts_handler._user_temp_data[user_id] = {}
        mock_update.message.text = "not_a_number"

        result = await price_alerts_handler.handle_alert_price_input(mock_update, mock_context)

        assert result == ALERT_PRICE

    @pytest.mark.asyncio()
    async def test_creates_condition_keyboard(
        self, price_alerts_handler, mock_update, mock_context
    ):
        """Тест создания клавиатуры выбора условия."""
        user_id = str(mock_update.effective_user.id)
        price_alerts_handler._user_temp_data[user_id] = {}
        mock_update.message.text = "25.75"

        await price_alerts_handler.handle_alert_price_input(mock_update, mock_context)

        call_kwargs = mock_update.message.reply_text.call_args.kwargs
        keyboard = call_kwargs["reply_markup"].inline_keyboard

        assert len(keyboard) == 3  # 2 условия + отмена
        assert CALLBACK_CONDITION_BELOW in keyboard[0][0].callback_data
        assert CALLBACK_CONDITION_ABOVE in keyboard[1][0].callback_data


# ======================== Test: handle_alert_condition_callback ========================


class TestHandleAlertConditionCallback:
    """Тесты для handle_alert_condition_callback."""

    @pytest.mark.asyncio()
    async def test_creates_alert_with_below_condition(
        self, price_alerts_handler, mock_update, mock_context
    ):
        """Тест создания оповещения с условием 'ниже'."""
        user_id = str(mock_update.effective_user.id)
        price_alerts_handler._user_temp_data[user_id] = {
            "item_name": "AK-47 | Redline (FT)",
            "target_price": 10.50,
        }
        mock_update.callback_query.data = CALLBACK_CONDITION_BELOW

        result = await price_alerts_handler.handle_alert_condition_callback(
            mock_update, mock_context
        )

        assert result == ConversationHandler.END
        assert PRICE_ALERT_STORAGE_KEY in mock_context.user_data
        alerts = mock_context.user_data[PRICE_ALERT_STORAGE_KEY]
        assert len(alerts) == 1

        # Проверяем данные созданного оповещения
        alert = next(iter(alerts.values()))
        assert alert["market_hash_name"] == "AK-47 | Redline (FT)"
        assert alert["target_price"] == 10.50
        assert alert["condition"] == "below"

    @pytest.mark.asyncio()
    async def test_creates_alert_with_above_condition(
        self, price_alerts_handler, mock_update, mock_context
    ):
        """Тест создания оповещения с условием 'выше'."""
        user_id = str(mock_update.effective_user.id)
        price_alerts_handler._user_temp_data[user_id] = {
            "item_name": "AWP | Asiimov (FT)",
            "target_price": 50.00,
        }
        mock_update.callback_query.data = CALLBACK_CONDITION_ABOVE

        result = await price_alerts_handler.handle_alert_condition_callback(
            mock_update, mock_context
        )

        assert result == ConversationHandler.END
        alert = next(iter(mock_context.user_data[PRICE_ALERT_STORAGE_KEY].values()))
        assert alert["condition"] == "above"

    @pytest.mark.asyncio()
    async def test_cancels_on_cancel_button(self, price_alerts_handler, mock_update, mock_context):
        """Тест отмены при нажатии кнопки отмены."""
        user_id = str(mock_update.effective_user.id)
        price_alerts_handler._user_temp_data[user_id] = {"item_name": "Item", "target_price": 10.0}
        mock_update.callback_query.data = CALLBACK_CANCEL

        result = await price_alerts_handler.handle_alert_condition_callback(
            mock_update, mock_context
        )

        assert result == ConversationHandler.END
        assert PRICE_ALERT_STORAGE_KEY not in mock_context.user_data

    @pytest.mark.asyncio()
    async def test_clears_temp_data_after_creation(
        self, price_alerts_handler, mock_update, mock_context
    ):
        """Тест очистки временных данных после создания."""
        user_id = str(mock_update.effective_user.id)
        price_alerts_handler._user_temp_data[user_id] = {
            "item_name": "Item",
            "target_price": 10.0,
        }
        mock_update.callback_query.data = CALLBACK_CONDITION_BELOW

        await price_alerts_handler.handle_alert_condition_callback(mock_update, mock_context)

        assert user_id not in price_alerts_handler._user_temp_data


# ======================== Test: handle_remove_alert_callback ========================


class TestHandleRemoveAlertCallback:
    """Тесты для handle_remove_alert_callback."""

    @pytest.mark.asyncio()
    async def test_removes_existing_alert(self, price_alerts_handler, mock_update, mock_context):
        """Тест удаления существующего оповещения."""
        alert_id = str(uuid4())
        mock_context.user_data = {
            PRICE_ALERT_STORAGE_KEY: {
                alert_id: {
                    "market_hash_name": "AK-47 | Redline (FT)",
                    "target_price": 10.50,
                    "condition": "below",
                }
            }
        }
        mock_update.callback_query.data = f"{CALLBACK_REMOVE_ALERT}{alert_id}"
        price_alerts_handler.handle_alert_list_callback = AsyncMock()

        await price_alerts_handler.handle_remove_alert_callback(mock_update, mock_context)

        assert alert_id not in mock_context.user_data[PRICE_ALERT_STORAGE_KEY]
        price_alerts_handler.handle_alert_list_callback.assert_called_once()

    @pytest.mark.asyncio()
    async def test_handles_non_existent_alert(
        self, price_alerts_handler, mock_update, mock_context
    ):
        """Тест обработки попытки удаления несуществующего оповещения."""
        mock_context.user_data = {PRICE_ALERT_STORAGE_KEY: {}}
        mock_update.callback_query.data = f"{CALLBACK_REMOVE_ALERT}nonexistent_id"

        await price_alerts_handler.handle_remove_alert_callback(mock_update, mock_context)

        # Проверка сообщения (первый позиционный аргумент)
        call_args = mock_update.callback_query.edit_message_text.call_args
        assert "не найдено" in call_args[0][0].lower()


# ======================== Test: handle_cancel ========================


class TestHandleCancel:
    """Тесты для handle_cancel."""

    @pytest.mark.asyncio()
    async def test_cancels_conversation(self, price_alerts_handler, mock_update, mock_context):
        """Тест отмены разговора."""
        result = await price_alerts_handler.handle_cancel(mock_update, mock_context)

        assert result == ConversationHandler.END
        mock_update.message.reply_text.assert_called_once()

    @pytest.mark.asyncio()
    async def test_clears_temp_data(self, price_alerts_handler, mock_update, mock_context):
        """Тест очистки временных данных при отмене."""
        user_id = str(mock_update.effective_user.id)
        price_alerts_handler._user_temp_data[user_id] = {"some": "data"}

        await price_alerts_handler.handle_cancel(mock_update, mock_context)

        assert user_id not in price_alerts_handler._user_temp_data


# ======================== Test: get_handlers ========================


class TestGetHandlers:
    """Тесты для get_handlers."""

    def test_returns_all_handlers(self, price_alerts_handler):
        """Тест возврата всех обработчиков."""
        handlers = price_alerts_handler.get_handlers()

        assert len(handlers) == 4  # command + 2 callbacks + conversation

    def test_includes_conversation_handler(self, price_alerts_handler):
        """Тест включения ConversationHandler."""
        handlers = price_alerts_handler.get_handlers()

        conversation_handlers = [h for h in handlers if isinstance(h, ConversationHandler)]
        assert len(conversation_handlers) == 1

    def test_conversation_has_correct_states(self, price_alerts_handler):
        """Тест правильных состояний в ConversationHandler."""
        handlers = price_alerts_handler.get_handlers()
        conversation = next(h for h in handlers if isinstance(h, ConversationHandler))

        assert ITEM_NAME in conversation.states
        assert ALERT_PRICE in conversation.states
        assert ALERT_CONDITION in conversation.states


# ======================== Test: Integration Scenarios ========================


class TestIntegrationScenarios:
    """Интеграционные тесты полных сценариев."""

    @pytest.mark.asyncio()
    async def test_full_alert_creation_flow(self, price_alerts_handler, mock_update, mock_context):
        """Тест полного процесса создания оповещения."""
        user_id = str(mock_update.effective_user.id)

        # Шаг 1: Начало создания
        result1 = await price_alerts_handler.handle_add_alert_callback(mock_update, mock_context)
        assert result1 == ITEM_NAME

        # Шаг 2: Ввод названия
        mock_update.message.text = "AK-47 | Redline (FT)"
        result2 = await price_alerts_handler.handle_item_name_input(mock_update, mock_context)
        assert result2 == ALERT_PRICE

        # Шаг 3: Ввод цены
        mock_update.message.text = "10.50"
        result3 = await price_alerts_handler.handle_alert_price_input(mock_update, mock_context)
        assert result3 == ALERT_CONDITION

        # Шаг 4: Выбор условия
        mock_update.callback_query.data = CALLBACK_CONDITION_BELOW
        result4 = await price_alerts_handler.handle_alert_condition_callback(
            mock_update, mock_context
        )
        assert result4 == ConversationHandler.END

        # Проверка созданного оповещения
        assert PRICE_ALERT_STORAGE_KEY in mock_context.user_data
        alert = next(iter(mock_context.user_data[PRICE_ALERT_STORAGE_KEY].values()))
        assert alert["market_hash_name"] == "AK-47 | Redline (FT)"
        assert alert["target_price"] == 10.50
        assert alert["condition"] == "below"

    @pytest.mark.asyncio()
    async def test_alert_removal_flow(self, price_alerts_handler, mock_update, mock_context):
        """Тест полного процесса удаления оповещения."""
        # Создаем оповещение
        alert_id = str(uuid4())
        mock_context.user_data = {
            PRICE_ALERT_STORAGE_KEY: {
                alert_id: {
                    "market_hash_name": "AK-47 | Redline (FT)",
                    "target_price": 10.50,
                    "condition": "below",
                }
            }
        }

        # Удаляем оповещение
        mock_update.callback_query.data = f"{CALLBACK_REMOVE_ALERT}{alert_id}"
        price_alerts_handler.handle_alert_list_callback = AsyncMock()

        await price_alerts_handler.handle_remove_alert_callback(mock_update, mock_context)

        assert len(mock_context.user_data[PRICE_ALERT_STORAGE_KEY]) == 0
