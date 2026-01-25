"""Обработчики callbacks для Telegram бота.

Этот модуль содержит функции обработки callback-запросов от inline-кнопок.
"""

import logging
import traceback

from telegram import CallbackQuery, Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from src.dmarket.arbitrage import GAMES, find_arbitrage_opportunities_advanced
from src.telegram_bot.handlers.dmarket_status import dmarket_status_impl
from src.telegram_bot.handlers.main_keyboard import (
    auto_trade_start,
    get_main_keyboard,
    main_menu_callback,
)
from src.telegram_bot.keyboards import (
    CB_GAME_PREFIX,
    create_pagination_keyboard,
    get_alert_keyboard,
    get_back_to_arbitrage_keyboard,
    get_game_selection_keyboard,
    get_marketplace_comparison_keyboard,
    get_settings_keyboard,
)
from src.telegram_bot.utils.api_client import setup_api_client
from src.telegram_bot.utils.formatters import format_opportunities
from src.utils.telegram_error_handlers import telegram_error_boundary


logger = logging.getLogger(__name__)


def _get_api_client(context: ContextTypes.DEFAULT_TYPE):
    """Get API client from context or create new one.

    Args:
        context: Bot context

    Returns:
        DMarketAPI instance or None if not available
    """
    # First try to get from bot_data (preferred)
    api = context.bot_data.get("dmarket_api") if context.bot_data else None

    # If not found, try to create new client from env
    if api is None:
        api = setup_api_client()
        if api and context.bot_data is not None:
            context.bot_data["dmarket_api"] = api

    return api


@telegram_error_boundary(user_friendly_message="❌ Ошибка меню арбитража")
async def arbitrage_callback_impl(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Обрабатывает callback 'arbitrage'.

    Args:
        update: Объект Update от Telegram
        context: Контекст взаимодействия с ботом

    """
    # Redirect to auto_trade in main_keyboard
    await auto_trade_start(update, context)


async def handle_dmarket_arbitrage_impl(
    update: Update, context: ContextTypes.DEFAULT_TYPE, mode: str = "normal"
) -> None:
    """Обрабатывает callback 'dmarket_arbitrage' - redirect to auto_trade.

    Args:
        update: Объект Update от Telegram
        context: Контекст взаимодействия с ботом
        mode: Режим арбитража (ignored, redirects to auto_trade)

    """
    await auto_trade_start(update, context)


async def search_arbitrage_for_game(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    game: str,
) -> list[dict]:
    """Search for arbitrage opportunities for a specific game.

    Uses find_arbitrage_opportunities_advanced for intelligent search.

    Args:
        update: Telegram update
        context: Bot context
        game: Game code (csgo, dota2, tf2, rust)

    Returns:
        List of arbitrage opportunities
    """
    api = _get_api_client(context)
    if not api:
        logger.warning("API client not available for arbitrage search")
        return []

    try:
        # Use advanced arbitrage search with smart filtering
        return await find_arbitrage_opportunities_advanced(
            api=api,
            game=game,
            min_profit_percent=5.0,  # 5% minimum profit
            max_items=50,  # Limit results
        )
    except Exception as e:
        logger.exception(f"Error searching arbitrage for {game}: {e}")
        return []


async def show_arbitrage_opportunities(
    query: CallbackQuery,
    context: ContextTypes.DEFAULT_TYPE,
    page: int | None = None,
) -> None:
    """Отображает результаты арбитража с пагинацией.

    Args:
        query: Объект callback_query
        context: Контекст взаимодействия с ботом
        page: Номер страницы (если None, берется из context.user_data)

    """
    # Получаем данные из контекста
    if context.user_data is None:
        return

    opportunities = context.user_data.get("arbitrage_opportunities", [])
    current_page = page if page is not None else context.user_data.get("arbitrage_page", 0)
    context.user_data.get("arbitrage_mode", "normal")

    # Пересчитываем текущую страницу при необходимости
    # по 3 возможности на странице
    total_pages = max(1, (len(opportunities) + 2) // 3)
    if current_page >= total_pages:
        current_page = 0

    # Сохраняем текущую страницу
    context.user_data["arbitrage_page"] = current_page

    # Форматируем результаты
    results_text = format_opportunities(opportunities, current_page, 3)

    # Создаем клавиатуру для пагинации
    keyboard = create_pagination_keyboard(
        current_page=current_page,
        total_pages=total_pages,
        prefix="arb_",
    )

    # Отправляем сообщение
    await query.edit_message_text(
        results_text,
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML,
    )


async def handle_arbitrage_pagination(
    query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, direction: str
) -> None:
    """Обрабатывает пагинацию результатов арбитража.

    Args:
        query: Объект callback_query
        context: Контекст взаимодействия с ботом
        direction: Направление (next_page или prev_page)

    """
    if context.user_data is None:
        return

    current_page = context.user_data.get("arbitrage_page", 0)
    opportunities = context.user_data.get("arbitrage_opportunities", [])
    total_pages = max(1, (len(opportunities) + 2) // 3)

    if direction == "next_page" and current_page < total_pages - 1:
        current_page += 1
    elif direction == "prev_page" and current_page > 0:
        current_page -= 1

    context.user_data["arbitrage_page"] = current_page
    await show_arbitrage_opportunities(query, context, current_page)


async def handle_best_opportunities_impl(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Обрабатывает callback 'best_opportunities'.

    Args:
        update: Объект Update от Telegram
        context: Контекст взаимодействия с ботом

    """
    # Перенаправляем на функцию поиска арбитражных возможностей
    # с режимом "best"
    await handle_dmarket_arbitrage_impl(update, context, mode="best")


async def handle_game_selection_impl(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает callback 'game_selection'.

    Args:
        update: Объект Update от Telegram
        context: Контекст взаимодействия с ботом

    """
    if not update.callback_query:
        return

    await update.callback_query.edit_message_text(
        "🎮 <b>Выберите игру для арбитража:</b>",
        reply_markup=get_game_selection_keyboard(),
        parse_mode=ParseMode.HTML,
    )


async def handle_game_selected_impl(
    update: Update, context: ContextTypes.DEFAULT_TYPE, game: str | None = None
) -> None:
    """Обрабатывает callback 'game_selected:...'.

    Args:
        update: Объект Update от Telegram
        context: Контекст взаимодействия с ботом
        game: Код выбранной игры

    """
    if not update.callback_query:
        return

    # Извлекаем код игры из callback_data
    if (
        game is None
        and update.callback_query.data
        and update.callback_query.data.startswith("game_selected:")
    ):
        game = update.callback_query.data.split(":", 1)[1]

    if game is None:
        return

    # Сохраняем выбранную игру в контексте пользователя
    if context.user_data is not None:
        context.user_data["selected_game"] = game

    game_name = GAMES.get(game, "Неизвестная игра")
    await update.callback_query.edit_message_text(
        f"🎮 <b>Выбрана игра: {game_name}</b>",
        parse_mode=ParseMode.HTML,
    )

    # Запускаем поиск арбитражных возможностей для выбранной игры
    await handle_dmarket_arbitrage_impl(update, context, mode=f"game_{game}")


async def handle_market_comparison_impl(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает callback 'market_comparison'.

    Args:
        update: Объект Update от Telegram
        context: Контекст взаимодействия с ботом

    """
    if not update.callback_query:
        return

    await update.callback_query.edit_message_text(
        "📊 <b>Сравнение рынков</b>\n\nВыберите рынки для сравнения:",
        reply_markup=get_marketplace_comparison_keyboard(),
        parse_mode=ParseMode.HTML,
    )


@telegram_error_boundary(user_friendly_message="❌ Ошибка обработки кнопки")
async def button_callback_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Общий обработчик колбэков от кнопок.

    Phase 2 Refactoring: Delegated to CallbackRouter for cleaner code.
    This legacy function is kept for backward compatibility.

    Args:
        update: Объект Update от Telegram
        context: Контекст взаимодействия с ботом

    """
    query = update.callback_query

    # Проверяем, что query не None
    if not query or not query.data:
        logger.warning("Получен update без callback_query или данных")
        return

    callback_data = query.data

    # Skip main keyboard callbacks - they are handled by main_keyboard registered in group 0
    if callback_data.startswith(("auto_trade_", "target")):
        return

    # Показываем индикатор загрузки
    await query.answer()

    # Try to use CallbackRouter first (Phase 2)
    router = context.bot_data.get("callback_router") if context.bot_data else None
    if router is not None:
        handled = await router.route(update, context)
        if handled:
            return

    # Fallback: handle callbacks not yet in router
    await _handle_legacy_callbacks(update, context, query, callback_data)


async def _handle_legacy_callbacks(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    query: CallbackQuery,
    callback_data: str,
) -> None:
    """Handle legacy callbacks not yet migrated to CallbackRouter.

    TODO(Phase 2): Migrate these callbacks to callback_registry.py
    This function contains callbacks that need to be migrated to callback_registry.py.

    Args:
        update: Telegram update object
        context: Bot context
        query: Callback query
        callback_data: Callback data string

    """
    try:
        # Main menu callback
        if callback_data == "main_menu":
            await main_menu_callback(update, context)
            return

        # Balance callback
        if callback_data == "balance":
            await dmarket_status_impl(update, context, status_message=query.message)
            return

        # Search callback
        if callback_data == "search":
            await query.edit_message_text(
                "🔍 <b>Поиск предметов на DMarket</b>\n\nВыберите игру для поиска предметов:",
                reply_markup=get_game_selection_keyboard(),
                parse_mode=ParseMode.HTML,
            )
            return

        # Settings callback
        if callback_data == "settings":
            await query.edit_message_text(
                "⚙️ <b>Настройки бота</b>\n\nВыберите раздел для настройки:",
                reply_markup=get_settings_keyboard(),
                parse_mode=ParseMode.HTML,
            )
            return

        # Market trends callback
        if callback_data == "market_trends":
            await query.edit_message_text(
                "📈 <b>Рыночные тренды</b>\n\n"
                "Анализ рыночных трендов и популярных предметов.\n"
                "Выберите игру для просмотра трендов:",
                reply_markup=get_game_selection_keyboard(),
                parse_mode=ParseMode.HTML,
            )
            return

        # Alerts callback
        if callback_data == "alerts":
            await query.edit_message_text(
                "🔔 <b>Управление оповещениями</b>\n\n"
                "Настройте оповещения о изменении цен и "
                "других рыночных событиях:",
                reply_markup=get_alert_keyboard(),
                parse_mode=ParseMode.HTML,
            )
            return

        # Back to main menu
        if callback_data == "back_to_main":
            await query.edit_message_text(
                "👋 <b>Главное меню</b>\n\nВыберите действие:",
                reply_markup=get_main_keyboard(),
                parse_mode=ParseMode.HTML,
            )
            return

        # Arbitrage callbacks - redirect to auto_trade
        if callback_data in {"arbitrage", "arbitrage_menu", "auto_arbitrage", "dmarket_arbitrage"}:
            await auto_trade_start(update, context)
            return

        # Best opportunities
        if callback_data == "best_opportunities":
            await handle_best_opportunities_impl(update, context)
            return

        # Game selection
        if callback_data == "game_selection":
            await handle_game_selection_impl(update, context)
            return

        # Game selected
        if callback_data.startswith("game_selected:"):
            game = callback_data.split(":", 1)[1]
            await handle_game_selected_impl(update, context, game=game)
            return

        # Game prefix
        if callback_data.startswith(CB_GAME_PREFIX) and not callback_data.startswith("game_selected"):
            game = callback_data[len(CB_GAME_PREFIX):]
            await handle_game_selected_impl(update, context, game=game)
            return

        # Market comparison
        if callback_data == "market_comparison":
            await handle_market_comparison_impl(update, context)
            return

        # Pagination
        if callback_data.startswith(("arb_next_page_", "arb_prev_page_")):
            direction = "next_page" if callback_data.startswith("arb_next_page_") else "prev_page"
            await handle_arbitrage_pagination(query, context, direction)
            return

        # Back to menu
        if callback_data == "back_to_menu":
            await main_menu_callback(update, context)
            return

        # Unknown callback - log and show error
        logger.warning("Неизвестный callback_data: %s", callback_data)
        await query.edit_message_text(
            "⚠️ <b>Неизвестная команда.</b>\n\nПожалуйста, вернитесь в главное меню:",
            reply_markup=get_back_to_arbitrage_keyboard(),
            parse_mode=ParseMode.HTML,
        )

    except Exception as e:
        logger.exception("Ошибка при обработке legacy callback %s: %s", callback_data, e)
        logger.exception(traceback.format_exc())

        try:
            await query.edit_message_text(
                f"❌ <b>Произошла ошибка при обработке команды</b>\n\n"
                f"Ошибка: {e!s}\n\n"
                f"Пожалуйста, попробуйте позже.",
                parse_mode=ParseMode.HTML,
                reply_markup=get_back_to_arbitrage_keyboard(),
            )
        except Exception as edit_error:
            logger.exception("Ошибка при отправке сообщения об ошибке: %s", edit_error)
            await query.answer("Произошла ошибка. Пожалуйста, попробуйте позже.")


# Экспортируем обработчики callbacks
__all__ = [
    "_handle_legacy_callbacks",
    "arbitrage_callback_impl",
    "button_callback_handler",
    "handle_best_opportunities_impl",
    "handle_dmarket_arbitrage_impl",
    "handle_game_selected_impl",
    "handle_game_selection_impl",
    "handle_market_comparison_impl",
]
