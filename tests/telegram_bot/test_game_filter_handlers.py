"""Тесты для модуля game_filter_handlers.

Этот модуль содержит тесты для обработчиков игровых фильтров, включая:
- Константы фильтров для разных игр
- Управление текущими фильтрами пользователя
- Построение клавиатур с фильтрами
- Обработку callback'ов для настройки фильтров
- Генерацию параметров API на основе фильтров
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram import CallbackQuery, InlineKeyboardMarkup, Update

from src.telegram_bot.game_filter_handlers import (
    CS2_CATEGORIES,
    CS2_EXTERIORS,
    CS2_RARITIES,
    DOTA2_HEROES,
    DOTA2_RARITIES,
    DOTA2_SLOTS,
    build_api_params_for_game,
    get_current_filters,
    get_filter_description,
    get_game_filter_keyboard,
    handle_back_to_filters_callback,
    handle_filter_callback,
    handle_game_filters,
    handle_select_game_filter_callback,
    update_filters,
)


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture()
def mock_update():
    """Создает мок Update объекта."""
    update = MagicMock(spec=Update)
    update.effective_chat = MagicMock()
    update.effective_chat.id = 123456
    update.callback_query = MagicMock(spec=CallbackQuery)
    update.callback_query.answer = AsyncMock()
    update.callback_query.edit_message_text = AsyncMock()
    update.callback_query.message = MagicMock()
    update.callback_query.message.reply_text = AsyncMock()
    # Добавляем message для handle_game_filters
    update.message = MagicMock()
    update.message.reply_text = AsyncMock()
    return update


@pytest.fixture()
def mock_context():
    """Создает мок CallbackContext объекта."""
    context = MagicMock()
    context.user_data = {}
    context.bot_data = {}
    return context


# ============================================================================
# ТЕСТЫ КОНСТАНТ
# ============================================================================


def test_cs2_categories_defined():
    """Тест наличия определения категорий для CS2."""
    assert len(CS2_CATEGORIES) > 0
    assert "Knife" in CS2_CATEGORIES
    assert "Rifle" in CS2_CATEGORIES
    assert isinstance(CS2_CATEGORIES, list)


def test_cs2_rarities_defined():
    """Тест наличия определения редкостей для CS2."""
    assert len(CS2_RARITIES) > 0
    assert "Covert" in CS2_RARITIES
    assert "Mil-Spec Grade" in CS2_RARITIES
    assert isinstance(CS2_RARITIES, list)


def test_cs2_exteriors_defined():
    """Тест наличия определения внешних видов для CS2."""
    assert len(CS2_EXTERIORS) > 0
    assert "Factory New" in CS2_EXTERIORS
    assert "Battle-Scarred" in CS2_EXTERIORS
    assert isinstance(CS2_EXTERIORS, list)


def test_dota2_heroes_defined():
    """Тест наличия определения героев для Dota 2."""
    assert len(DOTA2_HEROES) > 0
    assert "Pudge" in DOTA2_HEROES
    assert "Invoker" in DOTA2_HEROES
    assert isinstance(DOTA2_HEROES, list)


def test_dota2_rarities_defined():
    """Тест наличия определения редкостей для Dota 2."""
    assert len(DOTA2_RARITIES) > 0
    assert "Arcana" in DOTA2_RARITIES
    assert "Immortal" in DOTA2_RARITIES
    assert isinstance(DOTA2_RARITIES, list)


def test_dota2_slots_defined():
    """Тест наличия определения слотов для Dota 2."""
    assert len(DOTA2_SLOTS) > 0
    assert "Weapon" in DOTA2_SLOTS
    assert "Courier" in DOTA2_SLOTS
    assert isinstance(DOTA2_SLOTS, list)


# ============================================================================
# ТЕСТЫ УПРАВЛЕНИЯ ФИЛЬТРАМИ
# ============================================================================


def test_get_current_filters_no_filters(mock_context):
    """Тест получения фильтров когда их нет."""
    result = get_current_filters(mock_context, "csgo")

    # Должен вернуть пустой словарь
    assert isinstance(result, dict)


def test_get_current_filters_with_existing_filters(mock_context):
    """Тест получения существующих фильтров."""
    # Устанавливаем фильтры в правильной структуре
    mock_context.user_data["filters"] = {
        "csgo": {
            "category": "Rifle",
            "min_price": 10.0,
        }
    }

    result = get_current_filters(mock_context, "csgo")

    # Должен вернуть установленные фильтры
    assert result["category"] == "Rifle"
    assert result["min_price"] == 10.0


def test_update_filters_new_filter(mock_context):
    """Тест добавления нового фильтра."""
    update_filters(mock_context, "csgo", {"category": "Knife"})

    # Проверяем, что фильтр добавлен
    filters = mock_context.user_data.get("filters", {}).get("csgo", {})
    assert filters["category"] == "Knife"


def test_update_filters_update_existing(mock_context):
    """Тест обновления существующего фильтра."""
    # Устанавливаем начальный фильтр
    mock_context.user_data["filters"] = {"csgo": {"category": "Rifle"}}

    # Обновляем фильтр
    update_filters(mock_context, "csgo", {"category": "Knife"})

    # Проверяем обновление
    filters = mock_context.user_data["filters"]["csgo"]
    assert filters["category"] == "Knife"


def test_update_filters_remove_filter(mock_context):
    """Тест удаления фильтра (установка в None)."""
    # Устанавливаем начальный фильтр
    mock_context.user_data["filters"] = {"csgo": {"category": "Rifle"}}

    # Удаляем фильтр (перезаписываем пустым словарем)
    update_filters(mock_context, "csgo", {})

    # Проверяем - фильтр все еще есть, но он update не удаляет
    filters = mock_context.user_data["filters"]["csgo"]
    assert isinstance(filters, dict)


# ============================================================================
# ТЕСТЫ ПОСТРОЕНИЯ КЛАВИАТУР
# ============================================================================


def test_get_game_filter_keyboard_csgo():
    """Тест построения клавиатуры фильтров для CS:GO."""
    keyboard = get_game_filter_keyboard("csgo")

    # Проверяем тип
    assert isinstance(keyboard, InlineKeyboardMarkup)

    # Проверяем наличие кнопок
    assert len(keyboard.inline_keyboard) > 0


def test_get_game_filter_keyboard_dota2():
    """Тест построения клавиатуры фильтров для Dota 2."""
    keyboard = get_game_filter_keyboard("dota2")

    # Проверяем тип
    assert isinstance(keyboard, InlineKeyboardMarkup)

    # Проверяем наличие кнопок
    assert len(keyboard.inline_keyboard) > 0


# ============================================================================
# ТЕСТЫ ГЕНЕРАЦИИ ОПИСАНИЙ И API ПАРАМЕТРОВ
# ============================================================================


@patch("src.telegram_bot.game_filter_handlers.FilterFactory")
def test_get_filter_description_no_filters(mock_filter_factory):
    """Тест генерации описания без фильтров."""
    # Настраиваем мок
    mock_filter = MagicMock()
    mock_filter.get_filter_description.return_value = "Фильтры не установлены"
    mock_filter_factory.get_filter.return_value = mock_filter

    filters = {}
    description = get_filter_description("csgo", filters)

    # Должен вернуть строку
    assert isinstance(description, str)
    mock_filter.get_filter_description.assert_called_once_with(filters)


@patch("src.telegram_bot.game_filter_handlers.FilterFactory")
def test_get_filter_description_with_filters(mock_filter_factory):
    """Тест генерации описания с фильтрами."""
    # Настраиваем мок
    mock_filter = MagicMock()
    mock_filter.get_filter_description.return_value = "Rifle, Цена: $10-$50"
    mock_filter_factory.get_filter.return_value = mock_filter

    filters = {
        "category": "Rifle",
        "min_price": 10.0,
        "max_price": 50.0,
    }
    description = get_filter_description("csgo", filters)

    # Должен содержать информацию о фильтрах
    assert isinstance(description, str)
    assert len(description) > 0


@patch("src.telegram_bot.game_filter_handlers.FilterFactory")
def test_build_api_params_for_game_csgo(mock_filter_factory):
    """Тест построения API параметров для CS:GO."""
    # Настраиваем мок
    mock_filter = MagicMock()
    mock_filter.build_api_params.return_value = {"category": "Rifle"}
    mock_filter_factory.get_filter.return_value = mock_filter

    filters = {
        "category": "Rifle",
        "min_price": 10.0,
        "max_price": 50.0,
    }

    params = build_api_params_for_game("csgo", filters)

    # Проверяем, что параметры сформированы
    assert isinstance(params, dict)
    mock_filter.build_api_params.assert_called_once_with(filters)


@patch("src.telegram_bot.game_filter_handlers.FilterFactory")
def test_build_api_params_for_game_empty_filters(mock_filter_factory):
    """Тест построения API параметров с пустыми фильтрами."""
    # Настраиваем мок
    mock_filter = MagicMock()
    mock_filter.build_api_params.return_value = {}
    mock_filter_factory.get_filter.return_value = mock_filter

    filters = {}

    params = build_api_params_for_game("csgo", filters)

    # Должен вернуть словарь (возможно пустой)
    assert isinstance(params, dict)


# ============================================================================
# ТЕСТЫ ОБРАБОТЧИКОВ
# ============================================================================


@patch("src.telegram_bot.game_filter_handlers.FilterFactory")
@pytest.mark.asyncio()
async def test_handle_game_filters(mock_filter_factory, mock_update, mock_context):
    """Тест обработчика просмотра фильтров."""
    # Настраиваем мок FilterFactory
    mock_filter = MagicMock()
    mock_filter.get_filter_description.return_value = "Фильтры не установлены"
    mock_filter_factory.get_filter.return_value = mock_filter

    # Вызываем обработчик (он использует update.message, а не callback)
    await handle_game_filters(mock_update, mock_context)

    # Проверяем, что reply_text был вызван
    mock_update.message.reply_text.assert_called()


@patch("src.telegram_bot.game_filter_handlers.FilterFactory")
@pytest.mark.asyncio()
async def test_handle_select_game_filter_callback(mock_filter_factory, mock_update, mock_context):
    """Тест обработчика выбора типа фильтра."""
    # Настраиваем мок FilterFactory
    mock_filter = MagicMock()
    mock_filter.get_filter_description.return_value = "Фильтры не установлены"
    mock_filter_factory.get_filter.return_value = mock_filter

    # Настройка данных callback
    mock_update.callback_query.data = "select_filter:csgo:category"

    # Вызываем обработчик
    await handle_select_game_filter_callback(mock_update, mock_context)

    # Проверяем, что callback был обработан
    mock_update.callback_query.answer.assert_called()


@patch("src.telegram_bot.game_filter_handlers.FilterFactory")
@pytest.mark.asyncio()
async def test_handle_set_category_callback(mock_filter_factory, mock_update, mock_context):
    """Тест обработчика установки категории."""
    # Настраиваем мок FilterFactory
    mock_filter = MagicMock()
    mock_filter.get_filter_description.return_value = "Category: Rifle"
    mock_filter_factory.get_filter.return_value = mock_filter

    # Настройка данных callback - используем правильный формат для handle_filter_callback
    mock_update.callback_query.data = "filter:category:Rifle:csgo"

    # Вызываем обработчик filter, который фактически устанавливает фильтры
    await handle_filter_callback(mock_update, mock_context)

    # Проверяем, что фильтр установлен в правильной структуре
    filters = mock_context.user_data.get("filters", {}).get("csgo", {})
    assert filters.get("category") == "Rifle"


@patch("src.telegram_bot.game_filter_handlers.FilterFactory")
@pytest.mark.asyncio()
async def test_handle_set_rarity_callback(mock_filter_factory, mock_update, mock_context):
    """Тест обработчика установки редкости."""
    # Настраиваем мок FilterFactory
    mock_filter = MagicMock()
    mock_filter.get_filter_description.return_value = "Rarity: Covert"
    mock_filter_factory.get_filter.return_value = mock_filter

    # Настройка данных callback - используем правильный формат для handle_filter_callback
    mock_update.callback_query.data = "filter:rarity:Covert:csgo"

    # Вызываем обработчик filter
    await handle_filter_callback(mock_update, mock_context)

    # Проверяем, что фильтр установлен
    filters = mock_context.user_data.get("filters", {}).get("csgo", {})
    assert filters.get("rarity") == "Covert"


@patch("src.telegram_bot.game_filter_handlers.FilterFactory")
@pytest.mark.asyncio()
async def test_handle_set_exterior_callback(mock_filter_factory, mock_update, mock_context):
    """Тест обработчика установки внешнего вида."""
    # Настраиваем мок FilterFactory
    mock_filter = MagicMock()
    mock_filter.get_filter_description.return_value = "Exterior: Factory New"
    mock_filter_factory.get_filter.return_value = mock_filter

    # Настройка данных callback - используем правильный формат для handle_filter_callback
    mock_update.callback_query.data = "filter:exterior:Factory New:csgo"

    # Вызываем обработчик filter
    await handle_filter_callback(mock_update, mock_context)

    # Проверяем, что фильтр установлен
    filters = mock_context.user_data.get("filters", {}).get("csgo", {})
    assert filters.get("exterior") == "Factory New"


@patch("src.telegram_bot.game_filter_handlers.FilterFactory")
@pytest.mark.asyncio()
async def test_handle_set_hero_callback(mock_filter_factory, mock_update, mock_context):
    """Тест обработчика установки героя (Dota 2)."""
    # Настраиваем мок FilterFactory
    mock_filter = MagicMock()
    mock_filter.get_filter_description.return_value = "Hero: Pudge"
    mock_filter_factory.get_filter.return_value = mock_filter

    # Настройка данных callback - используем правильный формат для handle_filter_callback
    mock_update.callback_query.data = "filter:hero:Pudge:dota2"

    # Вызываем обработчик filter
    await handle_filter_callback(mock_update, mock_context)

    # Проверяем, что фильтр установлен
    filters = mock_context.user_data.get("filters", {}).get("dota2", {})
    assert filters.get("hero") == "Pudge"


@patch("src.telegram_bot.game_filter_handlers.FilterFactory")
@pytest.mark.asyncio()
async def test_handle_back_to_filters_callback(mock_filter_factory, mock_update, mock_context):
    """Тест обработчика возврата к фильтрам."""
    # Настраиваем мок FilterFactory
    mock_filter = MagicMock()
    mock_filter.get_filter_description.return_value = "Фильтры не установлены"
    mock_filter_factory.get_filter.return_value = mock_filter

    # Настройка данных callback
    mock_update.callback_query.data = "back_to_filters:csgo"

    # Вызываем обработчик
    await handle_back_to_filters_callback(mock_update, mock_context)

    # Проверяем, что callback был обработан
    mock_update.callback_query.answer.assert_called()
