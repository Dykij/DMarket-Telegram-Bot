"""Модуль обработки callback запросов арбитража.

Реализует:
- Обработку колбэков для различных режимов арбитража
- Пагинацию результатов
- Форматирование ответов с HTML разметкой
- Индикацию действий через ChatAction
"""

from telegram import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ChatAction, ParseMode
from telegram.ext import ContextTypes

from src.dmarket.arbitrage import GAMES
from src.telegram_bot.keyboards import (
    get_arbitrage_keyboard,
    get_game_selection_keyboard,
    get_marketplace_comparison_keyboard,
    get_modern_arbitrage_keyboard,
)
from src.telegram_bot.utils.formatters import format_best_opportunities, format_dmarket_results
from src.utils.exceptions import handle_exceptions
from src.utils.logging_utils import get_logger


# Removed: execute_api_request - использовать прямые вызовы API


logger = get_logger(__name__)

# Состояния для ConversationHandler
SELECTING_GAME, SELECTING_MODE, CONFIRMING_ACTION = range(3)


@handle_exceptions(
    logger_instance=logger, default_error_message="Ошибка в обработчике арбитража", reraise=False
)
async def arbitrage_callback_impl(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int | None:
    """Реализация обработки кнопки арбитража.

    Args:
        update: Объект обновления от Telegram
        context: Контекст обработчика

    Returns:
        int: Следующее состояние разговора или None

    """
    query = update.callback_query
    if not query:
        return None
    await query.answer()

    # Показываем индикатор, что бот печатает
    if update.effective_chat:
        await update.effective_chat.send_action(ChatAction.TYPING)

    # Проверяем, использует ли пользователь современный UI
    user_data = context.user_data or {}

    # Если у пользователя есть настройка современного UI, используем её
    use_modern_ui = user_data.get("use_modern_ui", False)

    if use_modern_ui:
        keyboard = get_modern_arbitrage_keyboard()
    else:
        keyboard = get_arbitrage_keyboard()

    await query.edit_message_text(
        text="🔍 <b>Выберите режим арбитража:</b>",
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML,
    )

    # Возвращаем состояние выбора режима
    return SELECTING_MODE


@handle_exceptions(
    logger_instance=logger, default_error_message="Ошибка при поиске арбитража", reraise=False
)
async def handle_dmarket_arbitrage_impl(
    query: CallbackQuery,
    context: ContextTypes.DEFAULT_TYPE,
    mode: str,
) -> None:
    """Обрабатывает запрос на поиск арбитражных возможностей на DMarket.

    Args:
        query: Объект callback-запроса
        context: Контекст бота
        mode: Режим арбитража ("boost", "mid", "pro")

    """
    # Получаем выбранную игру
    user_data = context.user_data or {}
    game = user_data.get("current_game", "csgo")

    # Сохраняем последний выбранный режим
    user_data["last_arbitrage_mode"] = mode

    # Словарь для отображения режимов на русском языке
    mode_display = {
        "boost": "Разгон баланса",
        "mid": "Средний трейдер",
        "pro": "Trade Pro",
    }

    # Показываем, что запрос обрабатывается
    if query.message is not None and query.message.chat is not None:
        await query.message.chat.send_action(ChatAction.TYPING)

    # Редактируем сообщение, показывая процесс поиска
    await query.edit_message_text(
        text=(
            f"🔍 <b>Поиск арбитражных возможностей</b>\n\n"
            f"Режим: <b>{mode_display.get(mode, mode)}</b>\n"
            f"Игра: <b>{GAMES.get(game, game)}</b>\n\n"
            f"<i>Пожалуйста, подождите...</i>"
        ),
        reply_markup=None,
        parse_mode=ParseMode.HTML,
    )

    # Показываем индикатор загрузки
    if query.message is not None and query.message.chat is not None:
        await query.message.chat.send_action(ChatAction.TYPING)

    # Определяем функцию для получения данных арбитража
    async def get_arbitrage_data():
        from src.dmarket.arbitrage import (
            arbitrage_boost_async,
            arbitrage_mid_async,
            arbitrage_pro_async,
        )

        if mode == "boost":
            return await arbitrage_boost_async(game)
        if mode == "pro":
            return await arbitrage_pro_async(game)
        return await arbitrage_mid_async(game)

    # Выполняем API запрос напрямую
    results = await get_arbitrage_data()

    # Если получены результаты
    if results:
        from src.telegram_bot.pagination import format_paginated_results, pagination_manager

        # Подготавливаем пагинацию результатов
        user_id = query.from_user.id
        pagination_manager.add_items_for_user(user_id, results, mode)
        page_data = pagination_manager.get_page(user_id)
        page_items, current_page, total_pages = page_data

        # Форматируем текст с результатами
        formatted_text = format_paginated_results(
            page_items,
            game,
            mode,
            current_page,
            total_pages,
        )

        # Создаем клавиатуру с кнопками пагинации
        keyboard = []

        # Добавляем кнопки пагинации, если страниц больше одной
        if total_pages > 1:
            pagination_row = []

            if current_page > 0:
                pagination_row.append(
                    InlineKeyboardButton(
                        "⬅️ Пред.",
                        callback_data=f"paginate:prev:{mode}",
                    ),
                )

            # Добавляем индикатор текущей страницы
            pagination_row.append(
                InlineKeyboardButton(
                    f"{current_page + 1}/{total_pages}",
                    callback_data="page_info",
                ),
            )

            if current_page < total_pages - 1:
                pagination_row.append(
                    InlineKeyboardButton(
                        "След. ➡️",
                        callback_data=f"paginate:next:{mode}",
                    ),
                )

            if pagination_row:
                keyboard.append(pagination_row)

        # Добавляем кнопки действий с результатами
        keyboard.append(
            [
                InlineKeyboardButton(
                    "📊 Подробный анализ",
                    callback_data=f"analyze:{mode}",
                ),
                InlineKeyboardButton(
                    "🔄 Обновить",
                    callback_data=f"refresh:{mode}",
                ),
            ],
        )

        # Добавляем кнопку открытия DMarket
        keyboard.append(
            [
                InlineKeyboardButton(
                    "🌐 Открыть DMarket",
                    web_app={"url": "https://dmarket.com"},
                ),
            ],
        )

        # Добавляем стандартные кнопки меню арбитража
        arbitrage_keyboard = get_arbitrage_keyboard().inline_keyboard
        keyboard.extend(arbitrage_keyboard[-1:])  # Только кнопка "Назад"

        # Отправляем сообщение с результатами
        await query.edit_message_text(
            text=formatted_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.HTML,
        )
    else:
        # Если результатов нет, показываем соответствующее сообщение
        # Передаем пустой словарь как валидный результат для форматирования
        formatted_text = format_dmarket_results(results or {}, mode)
        keyboard = get_arbitrage_keyboard()

        await query.edit_message_text(
            text=formatted_text,
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML,
        )


@handle_exceptions(
    logger_instance=logger,
    default_error_message="Ошибка при поиске лучших возможностей",
    reraise=False,
)
async def handle_best_opportunities_impl(
    query: CallbackQuery,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Обрабатывает запрос на поиск лучших арбитражных возможностей.

    Args:
        query: Объект callback-запроса
        context: Контекст бота

    """
    # Получаем выбранную игру
    user_data = context.user_data or {}
    game = user_data.get("current_game", "csgo")

    # Показываем, что запрос обрабатывается
    if query.message is not None and query.message.chat is not None:
        await query.message.chat.send_action(ChatAction.TYPING)

    # Редактируем сообщение, показывая процесс поиска
    await query.edit_message_text(
        text=(
            f"🔍 <b>Поиск лучших арбитражных возможностей</b>\n\n"
            f"Игра: <b>{GAMES.get(game, game)}</b>\n\n"
            f"<i>Идет анализ рынка, пожалуйста подождите...</i>"
        ),
        reply_markup=None,
        parse_mode=ParseMode.HTML,
    )

    # Показываем индикатор загрузки
    if query.message is not None and query.message.chat is not None:
        await query.message.chat.send_action(ChatAction.TYPING)

    # Получаем арбитражные возможности
    from src.dmarket.arbitrage_scanner import find_arbitrage_opportunities_async

    # Отображаем прогресс
    await query.edit_message_text(
        text=(
            f"🔍 <b>Поиск лучших арбитражных возможностей</b>\n\n"
            f"Игра: <b>{GAMES.get(game, game)}</b>\n\n"
            f"<i>Анализ цен... (1/3)</i>"
        ),
        parse_mode=ParseMode.HTML,
    )

    # Находим арбитражные возможности
    opportunities = await find_arbitrage_opportunities_async(
        game=game,
        max_items=10,
    )

    # Обновляем прогресс
    await query.edit_message_text(
        text=(
            f"🔍 <b>Поиск лучших арбитражных возможностей</b>\n\n"
            f"Игра: <b>{GAMES.get(game, game)}</b>\n\n"
            f"<i>Подготовка результатов... (3/3)</i>"
        ),
        parse_mode=ParseMode.HTML,
    )

    # Форматируем результаты
    formatted_text = format_best_opportunities(opportunities, game)

    # Создаем клавиатуру с кнопками действий
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🔄 Обновить",
                    callback_data="best_opportunities",
                ),
                InlineKeyboardButton(
                    "🌐 DMarket",
                    web_app={"url": "https://dmarket.com"},
                ),
            ],
            [InlineKeyboardButton("« Назад", callback_data="arbitrage")],
        ],
    )

    # Отправляем результаты
    await query.edit_message_text(
        text=formatted_text,
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML,
    )


@handle_exceptions(
    logger_instance=logger, default_error_message="Ошибка при выборе игры", reraise=False
)
async def handle_game_selection_impl(
    query: CallbackQuery,
    _: ContextTypes.DEFAULT_TYPE,
) -> int | None:
    """Обрабатывает выбор игры для арбитража.

    Args:
        query: Объект callback-запроса
        _: Контекст бота (не используется)

    Returns:
        int: Следующее состояние разговора или None

    """
    await query.answer()

    # Показываем индикатор, что бот печатает
    if query.message is not None and query.message.chat is not None:
        await query.message.chat.send_action(ChatAction.TYPING)

    # Получаем клавиатуру выбора игры
    keyboard = get_game_selection_keyboard()

    # Отправляем сообщение с выбором игры
    await query.edit_message_text(
        text=(
            "🎮 <b>Выберите игру для арбитража:</b>\n\n"
            "<i>Для каждой игры доступны свои рынки и возможности</i>"
        ),
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML,
    )

    # Возвращаем состояние выбора игры
    return SELECTING_GAME


@handle_exceptions(
    logger_instance=logger, default_error_message="Ошибка при обработке выбора игры", reraise=False
)
async def handle_game_selected_impl(
    query: CallbackQuery,
    context: ContextTypes.DEFAULT_TYPE,
    game: str,
) -> int | None:
    """Обрабатывает выбор конкретной игры.

    Args:
        query: Объект callback-запроса
        context: Контекст бота
        game: Выбранная игра

    Returns:
        int: Следующее состояние разговора или None

    """
    await query.answer()

    # Сохраняем выбранную игру
    if context.user_data is None:
        context.user_data = {}
    context.user_data["current_game"] = game

    # Показываем индикатор, что бот печатает
    if query.message is not None and query.message.chat is not None:
        await query.message.chat.send_action(ChatAction.TYPING)

    # Получаем клавиатуру арбитража
    keyboard = get_arbitrage_keyboard()

    # Отправляем сообщение с подтверждением выбора
    game_name = GAMES.get(game, game)
    await query.edit_message_text(
        text=(f"✅ <b>Выбрана игра:</b> {game_name}\n\nТеперь выберите режим арбитража:"),
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML,
    )

    # Возвращаем состояние выбора режима
    return SELECTING_MODE


@handle_exceptions(
    logger_instance=logger, default_error_message="Ошибка при сравнении площадок", reraise=False
)
async def handle_market_comparison_impl(
    query: CallbackQuery,
    _: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Показывает сравнение различных торговых площадок.

    Args:
        query: Объект callback-запроса
        _: Контекст бота (не используется)

    """
    await query.answer()

    # Показываем индикатор, что бот печатает
    if query.message is not None and query.message.chat is not None:
        await query.message.chat.send_action(ChatAction.TYPING)

    # Получаем клавиатуру сравнения маркетплейсов
    keyboard = get_marketplace_comparison_keyboard()

    # Отправляем сообщение с выбором маркетплейса
    await query.edit_message_text(
        text=(
            "🔄 <b>Сравнение торговых площадок</b>\n\n"
            "Выберите площадку для просмотра:\n\n"
            "<i>Вы можете открыть любую из этих площадок прямо в Telegram</i>"
        ),
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML,
    )
