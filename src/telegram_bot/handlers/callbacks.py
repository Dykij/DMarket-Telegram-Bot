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
from src.telegram_bot.handlers.simplified_menu_handler import get_main_menu_keyboard
from src.telegram_bot.keyboards import (
    CB_BACK,
    CB_CANCEL,
    CB_GAME_PREFIX,
    CB_HELP,
    create_pagination_keyboard,
    get_alert_keyboard,
    get_auto_arbitrage_keyboard,
    get_back_to_arbitrage_keyboard,
    get_dmarket_webapp_keyboard,
    get_game_selection_keyboard,
    get_language_keyboard,
    get_marketplace_comparison_keyboard,
    get_modern_arbitrage_keyboard,
    get_risk_profile_keyboard,
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
        # Skip simplified menu callbacks - they are handled by simplified_menu_handler
        if callback_data.startswith("simple_"):
            # These callbacks are handled by the simplified_menu_handler registered in group 1
            return

        # Обработка для упрощенного меню (НОВОЕ)
        if callback_data == "simple_menu":
            from src.telegram_bot.handlers.simplified_menu_handler import start_simple_menu

            await start_simple_menu(update, context)

        # Обработка для баланса
        elif callback_data == "balance":
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
        elif callback_data in {"arbitrage", "arbitrage_menu"}:
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

        elif callback_data.startswith(CB_GAME_PREFIX) and not callback_data.startswith(
            "game_selected"
        ):
            # Обработка выбора игры с кнопок game_csgo, game_dota2 и т.д.
            game = callback_data[len(CB_GAME_PREFIX) :]  # Убираем префикс
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

        # Backtesting callbacks
        elif callback_data == "backtest_quick":
            from src.telegram_bot.commands.backtesting_commands import run_quick_backtest

            api = context.bot_data.get("dmarket_api")
            if api:
                await run_quick_backtest(update, context, api)
            else:
                await query.edit_message_text("❌ DMarket API недоступен")

        elif callback_data == "backtest_standard":
            from src.telegram_bot.commands.backtesting_commands import run_standard_backtest

            api = context.bot_data.get("dmarket_api")
            if api:
                await run_standard_backtest(update, context, api)
            else:
                await query.edit_message_text("❌ DMarket API недоступен")

        elif callback_data == "backtest_custom":
            await query.edit_message_text(
                "⚙️ <b>Custom Backtest Settings</b>\n\n"
                "Custom backtesting coming soon!\n\n"
                "You'll be able to configure:\n"
                "• Date range\n"
                "• Initial balance\n"
                "• Strategy parameters\n"
                "• Item selection",
                parse_mode=ParseMode.HTML,
            )

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

        # Обработчик для Enhanced Scanner Menu
        elif callback_data == "enhanced_scanner_menu":
            from src.telegram_bot.handlers.enhanced_scanner_handler import (
                show_enhanced_scanner_menu,
            )

            await show_enhanced_scanner_menu(update, context)

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

        # Обработчики для главного меню
        elif callback_data == "main_menu":
            await query.edit_message_text(
                "👋 <b>Главное меню</b>\n\nВыберите действие:",
                reply_markup=get_main_menu_keyboard(),
                parse_mode=ParseMode.HTML,
            )

        # Обработчики для быстрого и глубокого сканирования
        elif callback_data == "arb_quick":
            # Быстрый скан - быстрая проверка топ возможностей
            await query.edit_message_text(
                "🚀 <b>Быстрый скан арбитража</b>\n\nПоиск лучших возможностей арбитража...",
                parse_mode=ParseMode.HTML,
            )
            await handle_dmarket_arbitrage_impl(update, context, mode="quick")

        elif callback_data == "arb_deep":
            # Глубокий скан - полный анализ рынка
            await query.edit_message_text(
                "🔬 <b>Глубокий скан арбитража</b>\n\n"
                "Выполняется полный анализ рынка. Это может занять несколько минут...",
                parse_mode=ParseMode.HTML,
            )
            await handle_dmarket_arbitrage_impl(update, context, mode="deep")

        # Дополнительные функции арбитража
        elif callback_data == "enhanced_scanner_menu":
            # Enhanced Scanner Menu
            from src.telegram_bot.handlers.enhanced_scanner_handler import (
                show_enhanced_scanner_menu,
            )

            await show_enhanced_scanner_menu(update, context)

        elif callback_data == "arb_market_analysis":
            await query.edit_message_text(
                "📊 <b>Анализ рынка</b>\n\nВыберите игру для анализа рыночных трендов:",
                reply_markup=get_game_selection_keyboard(),
                parse_mode=ParseMode.HTML,
            )

        elif callback_data == "arb_target":
            await query.edit_message_text(
                "🎯 <b>Таргеты (Buy Orders)</b>\n\n"
                "Управление целевыми ордерами на покупку.\n\n"
                "Выберите действие:",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ Создать таргет", callback_data="target_create")],
                    [InlineKeyboardButton("📋 Мои таргеты", callback_data="target_list")],
                    [InlineKeyboardButton("◀️ Назад", callback_data="arbitrage")],
                ]),
                parse_mode=ParseMode.HTML,
            )

        elif callback_data == "arb_stats":
            await query.edit_message_text(
                "📈 <b>Статистика арбитража</b>\n\n"
                "⚠️ Функция находится в разработке.\n\n"
                "Скоро здесь будет отображаться:\n"
                "• Общая прибыль\n"
                "• Успешные сделки\n"
                "• Лучшие возможности\n"
                "• История операций",
                reply_markup=get_back_to_arbitrage_keyboard(),
                parse_mode=ParseMode.HTML,
            )

        elif callback_data == "arb_compare":
            await query.edit_message_text(
                "🔄 <b>Сравнение площадок</b>\n\nСравнение цен на разных торговых площадках:",
                reply_markup=get_marketplace_comparison_keyboard(),
                parse_mode=ParseMode.HTML,
            )

        # ============================================================================
        # Обработчики главного меню
        # ============================================================================

        elif callback_data == "targets":
            await query.edit_message_text(
                "🎯 <b>Таргеты (Buy Orders)</b>\n\n"
                "Управление целевыми ордерами на покупку:\n\n"
                "• Создайте таргет на нужный предмет\n"
                "• Система автоматически выставит buy order\n"
                "• Получайте уведомления о выполнении",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ Создать таргет", callback_data="target_create")],
                    [InlineKeyboardButton("📋 Мои таргеты", callback_data="target_list")],
                    [InlineKeyboardButton("📊 Статистика", callback_data="target_stats")],
                    [InlineKeyboardButton("◀️ Главное меню", callback_data="main_menu")],
                ]),
                parse_mode=ParseMode.HTML,
            )

        elif callback_data == "target_create":
            await query.edit_message_text(
                "➕ <b>Создание таргета</b>\n\nВыберите игру для создания таргета:",
                reply_markup=get_game_selection_keyboard(),
                parse_mode=ParseMode.HTML,
            )

        elif callback_data == "target_list":
            await query.edit_message_text(
                "📋 <b>Мои таргеты</b>\n\n"
                "У вас пока нет активных таргетов.\n"
                "Создайте первый таргет для автоматической покупки предметов!",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ Создать таргет", callback_data="target_create")],
                    [InlineKeyboardButton("◀️ Назад", callback_data="targets")],
                ]),
                parse_mode=ParseMode.HTML,
            )

        elif callback_data == "target_stats":
            await query.edit_message_text(
                "📊 <b>Статистика таргетов</b>\n\n⚠️ У вас пока нет выполненных таргетов.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("◀️ Назад", callback_data="targets")],
                ]),
                parse_mode=ParseMode.HTML,
            )

        elif callback_data == "inventory":
            await query.edit_message_text(
                "📦 <b>Ваш инвентарь</b>\n\n"
                "⚠️ Для просмотра инвентаря необходимо настроить API ключи DMarket.\n\n"
                "Перейдите в Настройки → API ключи для настройки.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔑 Настроить API", callback_data="settings_api")],
                    [InlineKeyboardButton("◀️ Главное меню", callback_data="main_menu")],
                ]),
                parse_mode=ParseMode.HTML,
            )

        elif callback_data == "analytics":
            await query.edit_message_text(
                "📈 <b>Аналитика рынка</b>\n\nВыберите раздел аналитики:",
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("📊 Тренды", callback_data="analysis_trends"),
                        InlineKeyboardButton("💹 Волатильность", callback_data="analysis_vol"),
                    ],
                    [
                        InlineKeyboardButton("🔥 Топ продаж", callback_data="analysis_top"),
                        InlineKeyboardButton("📉 Падающие", callback_data="analysis_drop"),
                    ],
                    [InlineKeyboardButton("🎯 Рекомендации", callback_data="analysis_rec")],
                    [InlineKeyboardButton("◀️ Главное меню", callback_data="main_menu")],
                ]),
                parse_mode=ParseMode.HTML,
            )

        elif callback_data in {CB_HELP, "help"}:
            await query.edit_message_text(
                "❓ <b>Справка по боту</b>\n\n"
                "<b>Основные команды:</b>\n"
                "/start - Запуск бота\n"
                "/help - Эта справка\n"
                "/arbitrage - Меню арбитража\n"
                "/status - Статус DMarket API\n\n"
                "<b>Функции бота:</b>\n"
                "• 📊 <b>Арбитраж</b> - поиск выгодных сделок\n"
                "• 🎯 <b>Таргеты</b> - автоматические buy orders\n"
                "• 💰 <b>Баланс</b> - проверка баланса DMarket\n"
                "• 📦 <b>Инвентарь</b> - ваши предметы\n"
                "• 🔔 <b>Оповещения</b> - уведомления о ценах\n\n"
                "По вопросам обращайтесь к администратору.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("◀️ Главное меню", callback_data="main_menu")],
                ]),
                parse_mode=ParseMode.HTML,
            )

        # ============================================================================
        # Обработчики арбитража
        # ============================================================================

        elif callback_data == "scanner":
            # Многоуровневый сканер - делегируем scanner_handler
            try:
                from src.telegram_bot.handlers.scanner_handler import start_scanner_menu

                await start_scanner_menu(update, context)
            except ImportError as e:
                logger.warning("Scanner handler not available: %s, using fallback menu", e)
                await query.edit_message_text(
                    "🔍 <b>Многоуровневый сканер</b>\n\nВыберите уровень сканирования:",
                    reply_markup=InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton("🟢 Boost", callback_data="scan_level_boost"),
                            InlineKeyboardButton(
                                "🔵 Standard", callback_data="scan_level_standard"
                            ),
                        ],
                        [
                            InlineKeyboardButton("🟡 Medium", callback_data="scan_level_medium"),
                            InlineKeyboardButton(
                                "🟠 Advanced", callback_data="scan_level_advanced"
                            ),
                        ],
                        [InlineKeyboardButton("🔴 Pro", callback_data="scan_level_pro")],
                        [InlineKeyboardButton("◀️ Назад", callback_data="arbitrage")],
                    ]),
                    parse_mode=ParseMode.HTML,
                )

        elif callback_data == "arb_scan":
            await handle_dmarket_arbitrage_impl(update, context, mode="normal")

        elif callback_data == "arb_game":
            await handle_game_selection_impl(update, context)

        elif callback_data == "arb_levels":
            await query.edit_message_text(
                "📊 <b>Уровни арбитража</b>\n\n"
                "🟢 <b>Boost</b> - $0.50-$3 (3-5% profit)\n"
                "🔵 <b>Standard</b> - $3-$10 (5-8% profit)\n"
                "🟡 <b>Medium</b> - $10-$30 (8-12% profit)\n"
                "🟠 <b>Advanced</b> - $30-$100 (12-20% profit)\n"
                "🔴 <b>Pro</b> - $100+ (20%+ profit)\n\n"
                "Выберите уровень для сканирования:",
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("🟢 Boost", callback_data="scan_level_boost"),
                        InlineKeyboardButton("🔵 Standard", callback_data="scan_level_standard"),
                    ],
                    [
                        InlineKeyboardButton("🟡 Medium", callback_data="scan_level_medium"),
                        InlineKeyboardButton("🟠 Advanced", callback_data="scan_level_advanced"),
                    ],
                    [InlineKeyboardButton("🔴 Pro", callback_data="scan_level_pro")],
                    [InlineKeyboardButton("◀️ Назад", callback_data="arbitrage")],
                ]),
                parse_mode=ParseMode.HTML,
            )

        elif callback_data.startswith(("scan_level_", "scanner_level_scan_")):
            # Обработка обоих форматов: scan_level_medium и scanner_level_scan_medium
            if callback_data.startswith("scanner_level_scan_"):
                level = callback_data.replace("scanner_level_scan_", "")
            else:
                level = callback_data.replace("scan_level_", "")

            await query.edit_message_text(
                f"🔍 <b>Сканирование уровня {level.upper()}</b>\n\n"
                "Поиск арбитражных возможностей...",
                parse_mode=ParseMode.HTML,
            )
            await handle_dmarket_arbitrage_impl(update, context, mode=level)

        elif callback_data == "arb_settings":
            await query.edit_message_text(
                "⚙️ <b>Настройки арбитража</b>\n\n"
                "Настройте параметры поиска арбитражных возможностей:",
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("💰 Мин. прибыль", callback_data="arb_set_min_profit"),
                        InlineKeyboardButton("💵 Макс. цена", callback_data="arb_set_max_price"),
                    ],
                    [
                        InlineKeyboardButton("🎮 Игры", callback_data="arb_set_games"),
                        InlineKeyboardButton("⚠️ Риск", callback_data="arb_set_risk"),
                    ],
                    [InlineKeyboardButton("◀️ Назад", callback_data="arbitrage")],
                ]),
                parse_mode=ParseMode.HTML,
            )

        elif callback_data == "arb_auto":
            await query.edit_message_text(
                "🤖 <b>Автоматический арбитраж</b>\n\nУправление автоматической торговлей:",
                reply_markup=get_auto_arbitrage_keyboard(),
                parse_mode=ParseMode.HTML,
            )

        elif callback_data == "arb_analysis":
            await query.edit_message_text(
                "📈 <b>Анализ рынка</b>\n\nВыберите игру для анализа:",
                reply_markup=get_game_selection_keyboard(),
                parse_mode=ParseMode.HTML,
            )

        # Auto-arbitrage handlers
        elif callback_data == "auto_arb_start":
            await query.answer("⚠️ Для запуска авто-арбитража настройте API ключи", show_alert=True)

        elif callback_data == "auto_arb_stop":
            await query.answer("ℹ️ Авто-арбитраж не запущен", show_alert=True)

        elif callback_data == "auto_arb_settings":
            await query.edit_message_text(
                "⚙️ <b>Настройки авто-арбитража</b>\n\n"
                "• Минимальная прибыль: 5%\n"
                "• Максимальная цена: $50\n"
                "• Максимум сделок: 10/день\n"
                "• Игры: CS2, Dota 2\n\n"
                "⚠️ Редактирование настроек в разработке",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("◀️ Назад", callback_data="arb_auto")],
                ]),
                parse_mode=ParseMode.HTML,
            )

        elif callback_data == "auto_arb_status":
            await query.edit_message_text(
                "📊 <b>Статус авто-арбитража</b>\n\n"
                "🔴 Статус: Остановлен\n"
                "📈 Сделок сегодня: 0\n"
                "💰 Прибыль сегодня: $0.00",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("▶️ Запустить", callback_data="auto_arb_start")],
                    [InlineKeyboardButton("◀️ Назад", callback_data="arb_auto")],
                ]),
                parse_mode=ParseMode.HTML,
            )

        elif callback_data == "auto_arb_history":
            await query.edit_message_text(
                "📜 <b>История авто-арбитража</b>\n\n"
                "У вас пока нет завершённых автоматических сделок.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("◀️ Назад", callback_data="arb_auto")],
                ]),
                parse_mode=ParseMode.HTML,
            )

        # Marketplace comparison handlers
        elif callback_data == "cmp_steam":
            await query.edit_message_text(
                "📊 <b>DMarket ↔️ Steam</b>\n\n"
                "Сравнение цен между DMarket и Steam Маркетом.\n\n"
                "⚠️ Функция находится в разработке.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Обновить", callback_data="cmp_steam")],
                    [InlineKeyboardButton("◀️ Назад", callback_data="arb_compare")],
                ]),
                parse_mode=ParseMode.HTML,
            )

        elif callback_data == "cmp_buff":
            await query.edit_message_text(
                "📊 <b>DMarket ↔️ Buff</b>\n\n"
                "Сравнение цен между DMarket и Buff163.\n\n"
                "⚠️ Функция находится в разработке.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Обновить", callback_data="cmp_buff")],
                    [InlineKeyboardButton("◀️ Назад", callback_data="arb_compare")],
                ]),
                parse_mode=ParseMode.HTML,
            )

        elif callback_data == "cmp_refresh":
            await query.answer("🔄 Обновление данных...", show_alert=False)

        # Analysis handlers
        elif callback_data == "analysis_trends":
            await query.edit_message_text(
                "📊 <b>Рыночные тренды</b>\n\n"
                "Анализ трендов цен на предметы.\n\n"
                "⚠️ Функция находится в разработке.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("◀️ Назад", callback_data="analytics")],
                ]),
                parse_mode=ParseMode.HTML,
            )

        elif callback_data == "analysis_vol":
            await query.edit_message_text(
                "💹 <b>Волатильность рынка</b>\n\n"
                "Анализ колебаний цен.\n\n"
                "⚠️ Функция находится в разработке.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("◀️ Назад", callback_data="analytics")],
                ]),
                parse_mode=ParseMode.HTML,
            )

        elif callback_data == "analysis_top":
            await query.edit_message_text(
                "🔥 <b>Топ продаж</b>\n\n"
                "Самые продаваемые предметы.\n\n"
                "⚠️ Функция находится в разработке.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("◀️ Назад", callback_data="analytics")],
                ]),
                parse_mode=ParseMode.HTML,
            )

        elif callback_data == "analysis_drop":
            await query.edit_message_text(
                "📉 <b>Падающие цены</b>\n\n"
                "Предметы с падающими ценами.\n\n"
                "⚠️ Функция находится в разработке.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("◀️ Назад", callback_data="analytics")],
                ]),
                parse_mode=ParseMode.HTML,
            )

        elif callback_data == "analysis_rec":
            await query.edit_message_text(
                "🎯 <b>Рекомендации</b>\n\n"
                "Рекомендации по покупке/продаже.\n\n"
                "⚠️ Функция находится в разработке.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("◀️ Назад", callback_data="analytics")],
                ]),
                parse_mode=ParseMode.HTML,
            )

        # ============================================================================
        # Обработчики настроек
        # ============================================================================

        elif callback_data == "settings_language":
            await query.edit_message_text(
                "🌐 <b>Выбор языка</b>\n\nВыберите язык интерфейса:",
                reply_markup=get_language_keyboard(),
                parse_mode=ParseMode.HTML,
            )

        elif callback_data.startswith("lang_"):
            lang = callback_data.replace("lang_", "")
            lang_names = {"ru": "Русский", "en": "English", "es": "Español", "de": "Deutsch"}
            await query.edit_message_text(
                f"🌐 <b>Язык изменён</b>\n\nВыбран язык: {lang_names.get(lang, lang)}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("◀️ Назад", callback_data="settings")],
                ]),
                parse_mode=ParseMode.HTML,
            )

        elif callback_data == "settings_notify":
            await query.edit_message_text(
                "🔔 <b>Настройки уведомлений</b>\n\nВыберите тип уведомлений для настройки:",
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("📊 Арбитраж", callback_data="notify_arb"),
                        InlineKeyboardButton("🎯 Таргеты", callback_data="notify_targets"),
                    ],
                    [
                        InlineKeyboardButton("💰 Цены", callback_data="notify_prices"),
                        InlineKeyboardButton("📈 Тренды", callback_data="notify_trends"),
                    ],
                    [InlineKeyboardButton("◀️ Назад", callback_data="settings")],
                ]),
                parse_mode=ParseMode.HTML,
            )

        elif callback_data == "settings_api":
            await query.edit_message_text(
                "🔑 <b>Настройка API ключей</b>\n\n"
                "Для работы бота необходимы API ключи от DMarket.\n\n"
                "<b>Инструкция:</b>\n"
                "1. Зайдите на https://dmarket.com\n"
                "2. Перейдите в Настройки → Trading API\n"
                "3. Активируйте Trading API\n"
                "4. Создайте новые API ключи\n"
                "5. Сохраните ключи в файле .env\n"
                "6. Перезапустите бота",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("◀️ Назад", callback_data="settings")],
                ]),
                parse_mode=ParseMode.HTML,
            )

        elif callback_data == "settings_risk":
            await query.edit_message_text(
                "⚠️ <b>Профиль риска</b>\n\nВыберите ваш профиль риска для торговли:",
                reply_markup=get_risk_profile_keyboard(),
                parse_mode=ParseMode.HTML,
            )

        elif callback_data.startswith("risk_"):
            risk = callback_data.replace("risk_", "")
            risk_names = {
                "low": "🟢 Низкий",
                "medium": "🟡 Средний",
                "high": "🔴 Высокий",
                "aggressive": "⚫ Агрессивный",
            }
            await query.edit_message_text(
                f"⚠️ <b>Профиль риска изменён</b>\n\nВыбран профиль: {risk_names.get(risk, risk)}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("◀️ Назад", callback_data="settings")],
                ]),
                parse_mode=ParseMode.HTML,
            )

        elif callback_data == "settings_limits":
            await query.edit_message_text(
                "💰 <b>Торговые лимиты</b>\n\n"
                "Текущие лимиты:\n"
                "• Максимальная цена сделки: $50\n"
                "• Максимум сделок в день: 10\n"
                "• Дневной лимит: $500\n\n"
                "⚠️ Редактирование в разработке",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("◀️ Назад", callback_data="settings")],
                ]),
                parse_mode=ParseMode.HTML,
            )

        elif callback_data == "settings_games":
            await query.edit_message_text(
                "🎮 <b>Настройка игр</b>\n\nВыберите игры для мониторинга:",
                reply_markup=get_game_selection_keyboard(),
                parse_mode=ParseMode.HTML,
            )

        # ============================================================================
        # Обработчики алертов
        # ============================================================================

        elif callback_data == "alert_active":
            await query.edit_message_text(
                "🔔 <b>Активные оповещения</b>\n\nУ вас пока нет активных оповещений.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ Создать", callback_data="alert_create")],
                    [InlineKeyboardButton("◀️ Назад", callback_data="alerts")],
                ]),
                parse_mode=ParseMode.HTML,
            )

        elif callback_data == "alert_history":
            await query.edit_message_text(
                "📊 <b>История оповещений</b>\n\nИстория сработавших оповещений пуста.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("◀️ Назад", callback_data="alerts")],
                ]),
                parse_mode=ParseMode.HTML,
            )

        elif callback_data.startswith("alert_type_"):
            alert_type = callback_data.replace("alert_type_", "")
            type_names = {
                "below": "Цена ниже",
                "above": "Цена выше",
                "target": "Целевая цена",
                "percent": "Изменение %",
                "new_item": "Новый предмет",
            }
            await query.edit_message_text(
                f"🔔 <b>Создание оповещения</b>\n\n"
                f"Тип: {type_names.get(alert_type, alert_type)}\n\n"
                "Выберите игру для оповещения:",
                reply_markup=get_game_selection_keyboard(),
                parse_mode=ParseMode.HTML,
            )

        # ============================================================================
        # Общие обработчики
        # ============================================================================

        elif callback_data in {CB_BACK, "back"}:
            await query.edit_message_text(
                "👋 <b>Главное меню</b>\n\nВыберите действие:",
                reply_markup=get_main_menu_keyboard(),
                parse_mode=ParseMode.HTML,
            )

        elif callback_data in {CB_CANCEL, "cancel"}:
            await query.edit_message_text(
                "❌ <b>Действие отменено</b>\n\nВыберите следующее действие:",
                reply_markup=get_main_menu_keyboard(),
                parse_mode=ParseMode.HTML,
            )

        elif callback_data in {"noop", "page_info", "alerts_page_info"}:
            # Игнорируем кнопки без действия
            await query.answer()

        elif callback_data.startswith("notify_"):
            # Уведомления
            notify_type = callback_data.replace("notify_", "")
            await query.edit_message_text(
                f"🔔 <b>Настройка уведомлений: {notify_type}</b>\n\n"
                "⚠️ Функция находится в разработке.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("◀️ Назад", callback_data="settings_notify")],
                ]),
                parse_mode=ParseMode.HTML,
            )

        elif callback_data.startswith("arb_set_"):
            # Настройки арбитража
            setting = callback_data.replace("arb_set_", "")
            await query.edit_message_text(
                f"⚙️ <b>Настройка: {setting}</b>\n\n⚠️ Функция находится в разработке.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("◀️ Назад", callback_data="arb_settings")],
                ]),
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
