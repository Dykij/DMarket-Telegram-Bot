"""Обработчики callbacks для Telegram бота.

Этот модуль содержит функции обработки callback-запросов от inline-кнопок.
"""

import logging
import traceback

from telegram import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from src.dmarket.arbitrage import GAMES, find_arbitrage_opportunities_advanced
from src.telegram_bot.handlers.dmarket_status import dmarket_status_impl
from src.telegram_bot.keyboards import (
    create_pagination_keyboard,
    get_alert_keyboard,
    get_auto_arbitrage_keyboard,
    get_back_to_arbitrage_keyboard,
    get_dmarket_webapp_keyboard,
    get_game_selection_keyboard,
    get_main_menu_keyboard,
    get_marketplace_comparison_keyboard,
    get_modern_arbitrage_keyboard,
    get_settings_keyboard,
)
from src.telegram_bot.utils.api_client import setup_api_client
from src.telegram_bot.utils.formatters import format_opportunities
from src.utils.telegram_error_handlers import telegram_error_boundary


logger = logging.getLogger(__name__)


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
    if not update.callback_query:
        return

    await update.callback_query.edit_message_text(
        "🔍 <b>Меню арбитража:</b>",
        reply_markup=get_modern_arbitrage_keyboard(),
        parse_mode=ParseMode.HTML,
    )


async def handle_dmarket_arbitrage_impl(
    update: Update, context: ContextTypes.DEFAULT_TYPE, mode: str = "normal"
) -> None:
    """Обрабатывает callback 'dmarket_arbitrage'.

    Args:
        update: Объект Update от Telegram
        context: Контекст взаимодействия с ботом
        mode: Режим арбитража

    """
    if not update.callback_query:
        return

    query = update.callback_query
    # Сообщаем пользователю, что начался поиск возможностей
    await query.edit_message_text(
        "🔍 <b>Поиск арбитражных возможностей...</b>\n\n"
        "Это может занять некоторое время, пожалуйста, подождите.",
        parse_mode=ParseMode.HTML,
    )

    # Получаем API клиент
    api_client = setup_api_client()
    if not api_client:
        await query.edit_message_text(
            "❌ <b>Ошибка</b>\n\n"
            "Не удалось инициализировать API клиент DMarket. "
            "Проверьте настройки API ключей.",
            reply_markup=get_back_to_arbitrage_keyboard(),
            parse_mode=ParseMode.HTML,
        )
        return

    try:
        # Поиск арбитражных возможностей
        async with api_client:
            opportunities = await find_arbitrage_opportunities_advanced(
                api_client=api_client, mode=mode
            )

        if not opportunities:
            await query.edit_message_text(
                "🔍 <b>Арбитражные возможности не найдены</b>\n\n"
                "Попробуйте изменить параметры поиска или повторить позже.",
                reply_markup=get_back_to_arbitrage_keyboard(),
                parse_mode=ParseMode.HTML,
            )
            return

        # Сохраняем результаты в контексте для пагинации
        if context.user_data is not None:
            context.user_data["arbitrage_opportunities"] = opportunities
            context.user_data["arbitrage_page"] = 0
            context.user_data["arbitrage_mode"] = mode

        # Форматируем и отображаем результаты
        await show_arbitrage_opportunities(query, context)

    except Exception as e:
        logger.exception("Ошибка при поиске арбитражных возможностей: %s", e)

        await query.edit_message_text(
            f"❌ <b>Ошибка при поиске возможностей</b>\n\nПроизошла ошибка: {e!s}",
            reply_markup=get_back_to_arbitrage_keyboard(),
            parse_mode=ParseMode.HTML,
        )


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
        with_nums=True,
        back_button=True,
        back_text="« Назад к меню",
        back_callback="back_to_menu",
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

    # Показываем индикатор загрузки
    await query.answer()

    try:
        # Обработка для баланса
        if callback_data == "balance":
            await dmarket_status_impl(update, context, status_message=query.message)

        # Обработка для поиска
        elif callback_data == "search":
            await query.edit_message_text(
                "🔍 <b>Поиск предметов на DMarket</b>\n\nВыберите игру для поиска предметов:",
                reply_markup=get_game_selection_keyboard(),
                parse_mode=ParseMode.HTML,
            )

        # Обработка для настроек
        elif callback_data == "settings":
            await query.edit_message_text(
                "⚙️ <b>Настройки бота</b>\n\nВыберите раздел для настройки:",
                reply_markup=get_settings_keyboard(),
                parse_mode=ParseMode.HTML,
            )

        # Обработка для рыночных трендов
        elif callback_data == "market_trends":
            await query.edit_message_text(
                "📈 <b>Рыночные тренды</b>\n\n"
                "Анализ рыночных трендов и популярных предметов.\n"
                "Выберите игру для просмотра трендов:",
                reply_markup=get_game_selection_keyboard(),
                parse_mode=ParseMode.HTML,
            )

        # Обработка для оповещений
        elif callback_data == "alerts":
            await query.edit_message_text(
                "🔔 <b>Управление оповещениями</b>\n\n"
                "Настройте оповещения о изменении цен и "
                "других рыночных событиях:",
                reply_markup=get_alert_keyboard(),
                parse_mode=ParseMode.HTML,
            )

        # Обработка для возврата в главное меню
        elif callback_data == "back_to_main":
            await query.edit_message_text(
                "👋 <b>Главное меню</b>\n\nВыберите действие:",
                reply_markup=get_main_menu_keyboard(),
                parse_mode=ParseMode.HTML,
            )

        # Обработка для арбитража
        elif callback_data == "arbitrage":
            await arbitrage_callback_impl(update, context)

        elif callback_data == "auto_arbitrage":
            # Показываем меню автоарбитража
            keyboard = get_auto_arbitrage_keyboard()
            await query.edit_message_text(
                "🤖 <b>Выберите режим автоматического арбитража:</b>",
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML,
            )

        elif callback_data == "dmarket_arbitrage":
            # Делегируем обработку специализированному обработчику
            await handle_dmarket_arbitrage_impl(update, context, mode="normal")

        elif callback_data == "best_opportunities":
            # Делегируем обработку специализированному обработчику
            await handle_best_opportunities_impl(update, context)

        elif callback_data == "game_selection":
            # Делегируем обработку специализированному обработчику
            await handle_game_selection_impl(update, context)

        elif callback_data.startswith("game_selected:"):
            # Извлекаем код игры из callback_data
            game = callback_data.split(":", 1)[1]
            # Делегируем обработку специализированному обработчику
            await handle_game_selected_impl(update, context, game=game)

        elif callback_data == "market_comparison":
            # Делегируем обработку специализированному обработчику
            await handle_market_comparison_impl(update, context)

        # Обработка пагинации для арбитража
        elif callback_data.startswith(("arb_next_page_", "arb_prev_page_")):
            direction = "next_page" if callback_data.startswith("arb_next_page_") else "prev_page"
            await handle_arbitrage_pagination(query, context, direction)

        elif callback_data == "market_analysis":
            # Обработка для анализа рынка
            await query.edit_message_text(
                "📊 <b>Анализ рынка</b>\n\nВыберите игру для анализа рыночных тенденций и цен:",
                reply_markup=get_game_selection_keyboard(),
                parse_mode=ParseMode.HTML,
            )

        elif callback_data == "filter:" or callback_data.startswith("filter:"):
            # Обработка фильтров
            await query.edit_message_text(
                "⚙️ <b>Настройка фильтров</b>\n\nВыберите игру для настройки фильтров:",
                reply_markup=get_game_selection_keyboard(),
                parse_mode=ParseMode.HTML,
            )

        elif callback_data == "open_webapp":
            # Открытие WebApp с DMarket
            await query.edit_message_text(
                "🌐 <b>DMarket WebApp</b>\n\n"
                "Нажмите кнопку ниже, чтобы открыть DMarket прямо в Telegram:",
                parse_mode=ParseMode.HTML,
                reply_markup=get_dmarket_webapp_keyboard(),
            )

        elif callback_data.startswith("auto_start:"):
            # Извлекаем режим автоарбитража и запускаем его
            await query.answer("⚠️ Функция авто-торговли временно недоступна.")

        elif callback_data.startswith("paginate:"):
            # Обработка пагинации для результатов автоарбитража
            await query.answer("⚠️ Функция пагинации временно недоступна.")

        elif callback_data == "auto_stats":
            # Показываем статистику автоарбитража
            await query.answer("⚠️ Статистика временно недоступна.")

        elif callback_data.startswith("auto_trade:"):
            # Запускаем автоматическую торговлю для выбранного режима
            await query.answer("⚠️ Функция авто-торговли временно недоступна.")

        elif callback_data.startswith("compare:"):
            # Обработка сравнения рынков
            parts = callback_data.split(":")
            if len(parts) >= 3:
                game = parts[1]  # csgo, dota2, tf2, rust
                markets = parts[2]  # steam_dmarket, skinport_dmarket и т.д.

                game_name = GAMES.get(game, "Неизвестная игра")
                market_names = {
                    "steam_dmarket": "Steam ↔ DMarket",
                    "skinport_dmarket": "Skinport ↔ DMarket",
                    "csgoempire_dmarket": "CSGOEmpire ↔ DMarket",
                }
                market_display = market_names.get(markets, markets)

                await query.edit_message_text(
                    f"📊 <b>Сравнение рынков</b>\n\n"
                    f"🎮 Игра: {game_name}\n"
                    f"🔄 Рынки: {market_display}\n\n"
                    f"⚠️ Функция находится в разработке.\n\n"
                    f"Скоро вы сможете сравнивать цены на разных площадках!",
                    parse_mode=ParseMode.HTML,
                    reply_markup=get_back_to_arbitrage_keyboard(),
                )
            else:
                await query.edit_message_text(
                    "⚠️ <b>Некорректный формат данных сравнения.</b>\n\nПопробуйте снова.",
                    reply_markup=get_back_to_arbitrage_keyboard(),
                    parse_mode=ParseMode.HTML,
                )

        elif callback_data == "back_to_menu":
            # Возврат в главное меню
            await query.edit_message_text(
                "👋 <b>Главное меню</b>\n\nВыберите действие:",
                parse_mode=ParseMode.HTML,
                reply_markup=get_modern_arbitrage_keyboard(),
            )

        # Обработчики для настроек
        elif callback_data == "settings_api_keys":
            await query.edit_message_text(
                "🔑 <b>Настройка API ключей</b>\n\n"
                "Для работы бота необходимы API ключи от DMarket.\n\n"
                "<b>Инструкция:</b>\n"
                "1. Зайдите на https://dmarket.com\n"
                "2. Перейдите в Настройки → Trading API\n"
                "3. Активируйте Trading API (если не активирован)\n"
                "4. Создайте новые API ключи с полными правами\n"
                "5. Сохраните ключи в файле .env\n"
                "6. Перезапустите бота\n\n"
                "📖 Подробная инструкция: НАСТРОЙКА_API_КЛЮЧЕЙ.md",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("« Назад", callback_data="settings")]
                ]),
            )

        elif callback_data == "settings_proxy":
            await query.edit_message_text(
                "🌐 <b>Настройка Proxy</b>\n\nФункция находится в разработке.",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("« Назад", callback_data="settings")]
                ]),
            )

        elif callback_data == "settings_currency":
            await query.edit_message_text(
                "💵 <b>Настройка валюты</b>\n\n"
                "Текущая валюта: USD\n\n"
                "Функция смены валюты находится в разработке.",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("« Назад", callback_data="settings")]
                ]),
            )

        elif callback_data == "settings_intervals":
            await query.edit_message_text(
                "⏰ <b>Настройка интервалов обновления</b>\n\nФункция находится в разработке.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("« Назад", callback_data="settings")]
                ]),
                parse_mode=ParseMode.HTML,
            )

        elif callback_data == "settings_filters":
            await query.edit_message_text(
                "⚙️ <b>Настройка фильтров</b>\n\nВыберите игру для настройки фильтров:",
                reply_markup=get_game_selection_keyboard(),
                parse_mode=ParseMode.HTML,
            )

        elif callback_data == "settings_auto_refresh":
            await query.edit_message_text(
                "🔄 <b>Автоматическое обновление</b>\n\nФункция находится в разработке.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("« Назад", callback_data="settings")]
                ]),
                parse_mode=ParseMode.HTML,
            )

        # Обработчики для оповещений
        elif callback_data == "alert_create":
            await query.edit_message_text(
                "➕ <b>Создание оповещения</b>\n\n"
                "Выберите игру для создания оповещения о цене предмета:",
                parse_mode=ParseMode.HTML,
                reply_markup=get_game_selection_keyboard(),
            )

        elif callback_data == "alert_list":
            await query.edit_message_text(
                "👁️ <b>Мои оповещения</b>\n\nУ вас пока нет активных оповещений.",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("« Назад", callback_data="alerts")]
                ]),
            )

        elif callback_data == "alert_settings":
            await query.edit_message_text(
                "⚙️ <b>Настройки оповещений</b>\n\nФункция находится в разработке.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("« Назад", callback_data="alerts")]
                ]),
                parse_mode=ParseMode.HTML,
            )

        elif callback_data == "back_to_alerts":
            await query.edit_message_text(
                "🔔 <b>Управление оповещениями</b>\n\n"
                "Настройте оповещения о изменении цен и "
                "других рыночных событиях:",
                reply_markup=get_alert_keyboard(),
                parse_mode=ParseMode.HTML,
            )

        else:
            # Неизвестный callback
            logger.warning("Неизвестный callback_data: %s", callback_data)
            await query.edit_message_text(
                "⚠️ <b>Неизвестная команда.</b>\n\nПожалуйста, вернитесь в главное меню:",
                reply_markup=get_back_to_arbitrage_keyboard(),
                parse_mode=ParseMode.HTML,
            )

    except Exception as e:
        logger.exception("Ошибка при обработке callback %s: %s", callback_data, e)
        logger.exception(traceback.format_exc())

        # Оповещение пользователя об ошибке
        try:
            await query.edit_message_text(
                f"❌ <b>Произошла ошибка при обработке команды</b>\n\n"
                f"Ошибка: {e!s}\n\n"
                f"Пожалуйста, попробуйте позже или обратитесь к "
                f"администратору.",
                parse_mode=ParseMode.HTML,
                reply_markup=get_back_to_arbitrage_keyboard(),
            )
        except Exception as edit_error:
            logger.exception("Ошибка при отправке сообщения об ошибке: %s", edit_error)
            await query.answer("Произошла ошибка. Пожалуйста, попробуйте позже.")


# Экспортируем обработчики callbacks
__all__ = [
    "arbitrage_callback_impl",
    "button_callback_handler",
    "handle_best_opportunities_impl",
    "handle_dmarket_arbitrage_impl",
    "handle_game_selected_impl",
    "handle_game_selection_impl",
    "handle_market_comparison_impl",
]
