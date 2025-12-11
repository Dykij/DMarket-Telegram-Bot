"""Обработчики для гибких фильтров уведомлений.

Этот модуль предоставляет интерфейс для настройки детальных
фильтров уведомлений по играм, уровням прибыли и типам алертов.
"""

from typing import Any

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

from src.utils.exceptions import handle_exceptions
from src.utils.logging_utils import get_logger


logger = get_logger(__name__)

# Константы для callback data
NOTIFY_FILTER = "notify_filter"
NOTIFY_FILTER_GAMES = "games"
NOTIFY_FILTER_PROFIT = "profit"
NOTIFY_FILTER_LEVELS = "levels"
NOTIFY_FILTER_TYPES = "types"
NOTIFY_FILTER_SAVE = "save"
NOTIFY_FILTER_RESET = "reset"

# Поддерживаемые игры
SUPPORTED_GAMES = {
    "csgo": "🎮 CS2/CS:GO",
    "dota2": "⚔️ Dota 2",
    "tf2": "🔫 Team Fortress 2",
    "rust": "🏗️ Rust",
}

# Уровни арбитража
ARBITRAGE_LEVELS = {
    "boost": "🚀 Разгон баланса",
    "standard": "⭐ Стандарт",
    "medium": "💰 Средний",
    "advanced": "💎 Продвинутый",
    "pro": "🏆 Профессионал",
}

# Типы уведомлений
NOTIFICATION_TYPES = {
    "arbitrage": "💰 Арбитраж",
    "price_drop": "⬇️ Падение цены",
    "price_rise": "⬆️ Рост цены",
    "trending": "🔥 Трендовые",
    "good_deal": "✨ Выгодное предложение",
}


class NotificationFilters:
    """Менеджер фильтров уведомлений для пользователей."""

    def __init__(self) -> None:
        """Инициализация менеджера фильтров."""
        self._filters: dict[int, dict[str, Any]] = {}

    def get_user_filters(self, user_id: int) -> dict[str, Any]:
        """Получить фильтры пользователя.

        Args:
            user_id: ID пользователя Telegram

        Returns:
            Словарь с настройками фильтров

        """
        if user_id not in self._filters:
            self._filters[user_id] = self._get_default_filters()
        return self._filters[user_id].copy()

    def update_user_filters(self, user_id: int, filters: dict[str, Any]) -> None:
        """Обновить фильтры пользователя.

        Args:
            user_id: ID пользователя Telegram
            filters: Новые настройки фильтров

        """
        if user_id not in self._filters:
            self._filters[user_id] = self._get_default_filters()
        self._filters[user_id].update(filters)

    def reset_user_filters(self, user_id: int) -> None:
        """Сбросить фильтры пользователя к значениям по умолчанию.

        Args:
            user_id: ID пользователя Telegram

        """
        self._filters[user_id] = self._get_default_filters()

    @staticmethod
    def _get_default_filters() -> dict[str, Any]:
        """Получить фильтры по умолчанию.

        Returns:
            Словарь с настройками по умолчанию

        """
        return {
            "games": list(SUPPORTED_GAMES.keys()),  # Все игры
            "min_profit_percent": 5.0,  # Минимальная прибыль 5%
            "levels": list(ARBITRAGE_LEVELS.keys()),  # Все уровни
            "notification_types": list(NOTIFICATION_TYPES.keys()),  # Все типы
            "enabled": True,
        }

    def should_notify(
        self,
        user_id: int,
        game: str,
        profit_percent: float,
        level: str,
        notification_type: str,
    ) -> bool:
        """Проверить, нужно ли отправлять уведомление.

        Args:
            user_id: ID пользователя
            game: Код игры
            profit_percent: Процент прибыли
            level: Уровень арбитража
            notification_type: Тип уведомления

        Returns:
            True если уведомление нужно отправить

        """
        filters = self.get_user_filters(user_id)

        if not filters.get("enabled", True):
            return False

        # Проверка игры
        games = filters.get("games", [])
        if not isinstance(games, list) or game not in games:
            return False

        # Проверка прибыли
        min_profit = filters.get("min_profit_percent", 0)
        if isinstance(min_profit, (int, float)) and profit_percent < min_profit:
            return False

        # Проверка уровня
        levels = filters.get("levels", [])
        if not isinstance(levels, list) or level not in levels:
            return False

        # Проверка типа уведомления
        notification_types = filters.get("notification_types", [])
        return isinstance(notification_types, list) and notification_type in notification_types


# Глобальный экземпляр менеджера
_filters_manager = NotificationFilters()


def get_filters_manager() -> NotificationFilters:
    """Получить глобальный экземпляр менеджера фильтров.

    Returns:
        Экземпляр NotificationFilters

    """
    return _filters_manager


@handle_exceptions(
    logger_instance=logger, default_error_message="Ошибка при отображении фильтров", reraise=False
)
async def show_notification_filters(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Показать главное меню фильтров уведомлений.

    Args:
        update: Объект Update
        context: Контекст бота

    """
    if not update.effective_user:
        return

    user_id = update.effective_user.id
    filters_manager = get_filters_manager()
    user_filters = filters_manager.get_user_filters(user_id)

    # Формируем сообщение
    enabled_status = "✅ Включены" if user_filters.get("enabled") else "❌ Выключены"
    games_list = user_filters.get("games", [])
    games_count = len(games_list) if isinstance(games_list, list) else 0
    min_profit = user_filters.get("min_profit_percent", 5.0)
    levels_list = user_filters.get("levels", [])
    levels_count = len(levels_list) if isinstance(levels_list, list) else 0
    types_list = user_filters.get("notification_types", [])
    types_count = len(types_list) if isinstance(types_list, list) else 0

    message = (
        "🔔 *Фильтры уведомлений*\n\n"
        f"Статус: {enabled_status}\n"
        f"🎮 Игры: {games_count}/{len(SUPPORTED_GAMES)}\n"
        f"💰 Мин. прибыль: {min_profit}%\n"
        f"📊 Уровни: {levels_count}/{len(ARBITRAGE_LEVELS)}\n"
        f"📢 Типы: {types_count}/{len(NOTIFICATION_TYPES)}\n\n"
        "Настройте фильтры для персонализации уведомлений:"
    )

    # Клавиатура
    keyboard = [
        [
            InlineKeyboardButton(
                "🎮 Игры",
                callback_data=f"{NOTIFY_FILTER}_{NOTIFY_FILTER_GAMES}",
            ),
            InlineKeyboardButton(
                "💰 Прибыль",
                callback_data=f"{NOTIFY_FILTER}_{NOTIFY_FILTER_PROFIT}",
            ),
        ],
        [
            InlineKeyboardButton(
                "📊 Уровни",
                callback_data=f"{NOTIFY_FILTER}_{NOTIFY_FILTER_LEVELS}",
            ),
            InlineKeyboardButton(
                "📢 Типы",
                callback_data=f"{NOTIFY_FILTER}_{NOTIFY_FILTER_TYPES}",
            ),
        ],
        [
            InlineKeyboardButton(
                "🔄 Сбросить",
                callback_data=f"{NOTIFY_FILTER}_{NOTIFY_FILTER_RESET}",
            ),
        ],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    # Отправляем или редактируем сообщение
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN,
        )
    elif update.message:
        await update.message.reply_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN,
        )


@handle_exceptions(
    logger_instance=logger, default_error_message="Ошибка при настройке игр", reraise=False
)
async def show_games_filter(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Показать фильтр игр.

    Args:
        update: Объект Update
        context: Контекст бота

    """
    query = update.callback_query
    if not query or not update.effective_user:
        return

    await query.answer()
    user_id = update.effective_user.id
    filters_manager = get_filters_manager()
    user_filters = filters_manager.get_user_filters(user_id)
    enabled_games_raw = user_filters.get("games", [])
    enabled_games: list[str] = enabled_games_raw if isinstance(enabled_games_raw, list) else []

    message = "🎮 *Фильтр по играм*\n\nВыберите игры для уведомлений:"

    # Клавиатура с играми
    keyboard = []
    for game_code, game_name in SUPPORTED_GAMES.items():
        if game_code in enabled_games:
            button_text = f"✅ {game_name}"
        else:
            button_text = f"⬜ {game_name}"

        keyboard.append(
            [
                InlineKeyboardButton(
                    button_text,
                    callback_data=f"{NOTIFY_FILTER}_game_{game_code}",
                ),
            ],
        )

    keyboard.append(
        [
            InlineKeyboardButton(
                "⬅️ Назад",
                callback_data=NOTIFY_FILTER,
            ),
        ],
    )

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN,
    )


@handle_exceptions(
    logger_instance=logger, default_error_message="Ошибка при переключении игры", reraise=False
)
async def toggle_game_filter(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Переключить фильтр игры.

    Args:
        update: Объект Update
        context: Контекст бота

    """
    query = update.callback_query
    if not query or not update.effective_user or not query.data:
        return

    await query.answer()
    user_id = update.effective_user.id

    # Получаем код игры из callback_data
    game_code = query.data.split("_")[-1]

    filters_manager = get_filters_manager()
    user_filters = filters_manager.get_user_filters(user_id)
    enabled_games_raw = user_filters.get("games", [])
    enabled_games: list[str] = enabled_games_raw if isinstance(enabled_games_raw, list) else []

    # Переключаем игру
    if game_code in enabled_games:
        enabled_games.remove(game_code)
    else:
        enabled_games.append(game_code)

    user_filters["games"] = enabled_games
    filters_manager.update_user_filters(user_id, user_filters)

    # Обновляем отображение
    await show_games_filter(update, context)


@handle_exceptions(
    logger_instance=logger, default_error_message="Ошибка при настройке прибыли", reraise=False
)
async def show_profit_filter(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Показать фильтр минимальной прибыли.

    Args:
        update: Объект Update
        context: Контекст бота

    """
    query = update.callback_query
    if not query or not update.effective_user:
        return

    await query.answer()
    user_id = update.effective_user.id
    filters_manager = get_filters_manager()
    user_filters = filters_manager.get_user_filters(user_id)
    current_profit = user_filters.get("min_profit_percent", 5.0)

    message = (
        "💰 *Фильтр минимальной прибыли*\n\n"
        f"Текущее значение: *{current_profit}%*\n\n"
        "Выберите порог прибыли для уведомлений:"
    )

    # Предустановленные значения
    profit_values = [3.0, 5.0, 7.0, 10.0, 15.0, 20.0]

    keyboard = []
    for profit in profit_values:
        if profit == current_profit:
            button_text = f"✅ {profit}%"
        else:
            button_text = f"{profit}%"

        keyboard.append(
            [
                InlineKeyboardButton(
                    button_text,
                    callback_data=f"{NOTIFY_FILTER}_profit_{profit}",
                ),
            ],
        )

    keyboard.append(
        [
            InlineKeyboardButton(
                "⬅️ Назад",
                callback_data=NOTIFY_FILTER,
            ),
        ],
    )

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN,
    )


@handle_exceptions(
    logger_instance=logger, default_error_message="Ошибка при установке прибыли", reraise=False
)
async def set_profit_filter(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Установить минимальную прибыль.

    Args:
        update: Объект Update
        context: Контекст бота

    """
    query = update.callback_query
    if not query or not update.effective_user or not query.data:
        return

    await query.answer()
    user_id = update.effective_user.id

    # Получаем значение прибыли из callback_data
    profit_value = float(query.data.split("_")[-1])

    filters_manager = get_filters_manager()
    user_filters = filters_manager.get_user_filters(user_id)
    user_filters["min_profit_percent"] = profit_value
    filters_manager.update_user_filters(user_id, user_filters)

    # Обновляем отображение
    await show_profit_filter(update, context)


@handle_exceptions(
    logger_instance=logger, default_error_message="Ошибка при настройке уровней", reraise=False
)
async def show_levels_filter(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Показать фильтр уровней арбитража.

    Args:
        update: Объект Update
        context: Контекст бота

    """
    query = update.callback_query
    if not query or not update.effective_user:
        return

    await query.answer()
    user_id = update.effective_user.id
    filters_manager = get_filters_manager()
    user_filters = filters_manager.get_user_filters(user_id)
    enabled_levels_raw = user_filters.get("levels", [])
    enabled_levels: list[str] = enabled_levels_raw if isinstance(enabled_levels_raw, list) else []

    message = "📊 *Фильтр по уровням*\n\nВыберите уровни для уведомлений:"

    keyboard = []
    for level_code, level_name in ARBITRAGE_LEVELS.items():
        if level_code in enabled_levels:
            button_text = f"✅ {level_name}"
        else:
            button_text = f"⬜ {level_name}"

        keyboard.append(
            [
                InlineKeyboardButton(
                    button_text,
                    callback_data=f"{NOTIFY_FILTER}_level_{level_code}",
                ),
            ],
        )

    keyboard.append(
        [
            InlineKeyboardButton(
                "⬅️ Назад",
                callback_data=NOTIFY_FILTER,
            ),
        ],
    )

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN,
    )


@handle_exceptions(
    logger_instance=logger, default_error_message="Ошибка при переключении уровня", reraise=False
)
async def toggle_level_filter(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Переключить фильтр уровня.

    Args:
        update: Объект Update
        context: Контекст бота

    """
    query = update.callback_query
    if not query or not update.effective_user or not query.data:
        return

    await query.answer()
    user_id = update.effective_user.id

    # Получаем код уровня из callback_data
    level_code = query.data.split("_")[-1]

    filters_manager = get_filters_manager()
    user_filters = filters_manager.get_user_filters(user_id)
    enabled_levels_raw = user_filters.get("levels", [])
    enabled_levels: list[str] = enabled_levels_raw if isinstance(enabled_levels_raw, list) else []

    # Переключаем уровень
    if level_code in enabled_levels:
        enabled_levels.remove(level_code)
    else:
        enabled_levels.append(level_code)

    user_filters["levels"] = enabled_levels
    filters_manager.update_user_filters(user_id, user_filters)

    # Обновляем отображение
    await show_levels_filter(update, context)


@handle_exceptions(
    logger_instance=logger, default_error_message="Ошибка при настройке типов", reraise=False
)
async def show_types_filter(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Показать фильтр типов уведомлений.

    Args:
        update: Объект Update
        context: Контекст бота

    """
    query = update.callback_query
    if not query or not update.effective_user:
        return

    await query.answer()
    user_id = update.effective_user.id
    filters_manager = get_filters_manager()
    user_filters = filters_manager.get_user_filters(user_id)
    enabled_types_raw = user_filters.get("notification_types", [])
    enabled_types: list[str] = enabled_types_raw if isinstance(enabled_types_raw, list) else []

    message = "📢 *Фильтр по типам*\n\nВыберите типы уведомлений:"

    keyboard = []
    for type_code, type_name in NOTIFICATION_TYPES.items():
        if type_code in enabled_types:
            button_text = f"✅ {type_name}"
        else:
            button_text = f"⬜ {type_name}"

        keyboard.append(
            [
                InlineKeyboardButton(
                    button_text,
                    callback_data=f"{NOTIFY_FILTER}_type_{type_code}",
                ),
            ],
        )

    keyboard.append(
        [
            InlineKeyboardButton(
                "⬅️ Назад",
                callback_data=NOTIFY_FILTER,
            ),
        ],
    )

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN,
    )


@handle_exceptions(
    logger_instance=logger, default_error_message="Ошибка при переключении типа", reraise=False
)
async def toggle_type_filter(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Переключить фильтр типа уведомлений.

    Args:
        update: Объект Update
        context: Контекст бота

    """
    query = update.callback_query
    if not query or not update.effective_user or not query.data:
        return

    await query.answer()
    user_id = update.effective_user.id

    # Получаем код типа из callback_data
    type_code = query.data.split("_")[-1]

    filters_manager = get_filters_manager()
    user_filters = filters_manager.get_user_filters(user_id)
    enabled_types_raw = user_filters.get("notification_types", [])
    enabled_types: list[str] = enabled_types_raw if isinstance(enabled_types_raw, list) else []

    # Переключаем тип
    if type_code in enabled_types:
        enabled_types.remove(type_code)
    else:
        enabled_types.append(type_code)

    user_filters["notification_types"] = enabled_types
    filters_manager.update_user_filters(user_id, user_filters)

    # Обновляем отображение
    await show_types_filter(update, context)


@handle_exceptions(
    logger_instance=logger, default_error_message="Ошибка при сбросе фильтров", reraise=False
)
async def reset_filters(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Сбросить все фильтры к значениям по умолчанию.

    Args:
        update: Объект Update
        context: Контекст бота

    """
    query = update.callback_query
    if not query or not update.effective_user:
        return

    await query.answer("Фильтры сброшены к значениям по умолчанию")
    user_id = update.effective_user.id

    filters_manager = get_filters_manager()
    filters_manager.reset_user_filters(user_id)

    # Обновляем отображение
    await show_notification_filters(update, context)


def register_notification_filter_handlers(application: Application[Any, Any, Any, Any, Any, Any]) -> None:  # type: ignore[type-arg]
    """Зарегистрировать обработчики фильтров уведомлений.

    Args:
        application: Экземпляр Application

    """
    # Команда для открытия фильтров
    application.add_handler(
        CommandHandler("filters", show_notification_filters),
    )

    # Главное меню фильтров
    application.add_handler(
        CallbackQueryHandler(
            show_notification_filters,
            pattern=f"^{NOTIFY_FILTER}$",
        ),
    )

    # Фильтр игр
    application.add_handler(
        CallbackQueryHandler(
            show_games_filter,
            pattern=f"^{NOTIFY_FILTER}_{NOTIFY_FILTER_GAMES}$",
        ),
    )
    application.add_handler(
        CallbackQueryHandler(
            toggle_game_filter,
            pattern=f"^{NOTIFY_FILTER}_game_",
        ),
    )

    # Фильтр прибыли
    application.add_handler(
        CallbackQueryHandler(
            show_profit_filter,
            pattern=f"^{NOTIFY_FILTER}_{NOTIFY_FILTER_PROFIT}$",
        ),
    )
    application.add_handler(
        CallbackQueryHandler(
            set_profit_filter,
            pattern=f"^{NOTIFY_FILTER}_profit_",
        ),
    )

    # Фильтр уровней
    application.add_handler(
        CallbackQueryHandler(
            show_levels_filter,
            pattern=f"^{NOTIFY_FILTER}_{NOTIFY_FILTER_LEVELS}$",
        ),
    )
    application.add_handler(
        CallbackQueryHandler(
            toggle_level_filter,
            pattern=f"^{NOTIFY_FILTER}_level_",
        ),
    )

    # Фильтр типов
    application.add_handler(
        CallbackQueryHandler(
            show_types_filter,
            pattern=f"^{NOTIFY_FILTER}_{NOTIFY_FILTER_TYPES}$",
        ),
    )
    application.add_handler(
        CallbackQueryHandler(
            toggle_type_filter,
            pattern=f"^{NOTIFY_FILTER}_type_",
        ),
    )

    # Сброс фильтров
    application.add_handler(
        CallbackQueryHandler(
            reset_filters,
            pattern=f"^{NOTIFY_FILTER}_{NOTIFY_FILTER_RESET}$",
        ),
    )

    logger.info("Notification filter handlers registered")
