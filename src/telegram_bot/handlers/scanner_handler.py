"""Обработчик команд для многоуровневого сканирования арбитража."""

import logging
from typing import Any

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, ContextTypes

from src.dmarket.arbitrage import GAMES
from src.dmarket.arbitrage_scanner import ARBITRAGE_LEVELS, ArbitrageScanner
from src.telegram_bot.keyboards import create_pagination_keyboard
from src.telegram_bot.pagination import pagination_manager
from src.telegram_bot.utils.api_client import create_api_client_from_env


logger = logging.getLogger(__name__)

# Константы для callback данных
SCANNER_ACTION = "scanner"
LEVEL_SCAN_ACTION = "level_scan"
ALL_LEVELS_ACTION = "all_levels"
BEST_OPPS_ACTION = "best_opps"
MARKET_OVERVIEW_ACTION = "market_overview"


def format_scanner_results(
    items: list[dict[str, Any]],
    current_page: int,
    items_per_page: int,
) -> str:
    """Форматирует результаты сканирования для отображения.

    Args:
        items: Список результатов арбитража
        current_page: Текущая страница
        items_per_page: Количество элементов на странице

    Returns:
        Отформатированный текст

    """
    if not items:
        return "Нет результатов для отображения."

    header = f"📄 Страница {current_page + 1}\n\n"

    formatted_items = []
    for item in items:
        formatted_items.append(format_scanner_item(item))

    return header + "\n\n".join(formatted_items)


def format_scanner_item(result: dict[str, Any]) -> str:
    """Форматирует один результат сканирования.

    Args:
        result: Результат арбитража

    Returns:
        Отформатированный текст

    """
    title = result.get("title", "Неизвестный предмет")
    buy_price = result.get("buy_price", 0.0)
    sell_price = result.get("sell_price", 0.0)
    profit = result.get("profit", 0.0)
    profit_percent = result.get("profit_percent", 0.0)
    level = result.get("level", "")
    risk = result.get("risk_level", "")
    item_id = result.get("item_id", "")

    # Информация о ликвидности (если есть) - обновлено для API v1.1.0
    liquidity_data = result.get("liquidity_data", {})
    liquidity_text = ""
    if liquidity_data:
        score = liquidity_data.get("liquidity_score", 0.0)

        # Эмодзи по уровню ликвидности
        if score >= 80:
            emoji = "🟢"
        elif score >= 60:
            emoji = "🟡"
        elif score >= 40:
            emoji = "🟠"
        else:
            emoji = "🔴"

        # Показываем offer_count и order_count если доступны
        offer_count = liquidity_data.get("offer_count", 0)
        order_count = liquidity_data.get("order_count", 0)

        if offer_count > 0 or order_count > 0:
            liquidity_text = (
                f"\n💧 Ликвидность: {emoji} {score:.0f}/100\n"
                f"   🔴 Offers: {offer_count} | 🟢 Orders: {order_count}"
            )
        else:
            # Фоллбэк на старый формат
            time_days = liquidity_data.get("time_to_sell_days", 0.0)
            liquidity_text = f"\n💧 Ликвидность: {emoji} {score:.0f}/100 (~{time_days:.1f} дней)"

    return (
        f"🎯 *{title}*\n"
        f"💰 Купить: ${buy_price:.2f} → Продать: ${sell_price:.2f}\n"
        f"📈 Прибыль: ${profit:.2f} ({profit_percent:.1f}%)\n"
        f"📊 {level} | ⚠️ Риск: {risk}"
        f"{liquidity_text}\n"
        f"🏷️ ID: `{item_id}`"
    )


async def start_scanner_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Показать главное меню многоуровневого сканера.

    Args:
        update: Объект Update от Telegram
        context: Контекст выполнения

    """
    query = update.callback_query
    if query:
        await query.answer()

    keyboard = [
        [
            InlineKeyboardButton(
                "🚀 Разгон баланса",
                callback_data=f"{SCANNER_ACTION}_{LEVEL_SCAN_ACTION}_boost",
            ),
        ],
        [
            InlineKeyboardButton(
                "⭐ Стандарт",
                callback_data=f"{SCANNER_ACTION}_{LEVEL_SCAN_ACTION}_standard",
            ),
        ],
        [
            InlineKeyboardButton(
                "💰 Средний",
                callback_data=f"{SCANNER_ACTION}_{LEVEL_SCAN_ACTION}_medium",
            ),
        ],
        [
            InlineKeyboardButton(
                "💎 Продвинутый",
                callback_data=f"{SCANNER_ACTION}_{LEVEL_SCAN_ACTION}_advanced",
            ),
        ],
        [
            InlineKeyboardButton(
                "🏆 Профессиональный",
                callback_data=f"{SCANNER_ACTION}_{LEVEL_SCAN_ACTION}_pro",
            ),
        ],
        [
            InlineKeyboardButton(
                "🔍 Все уровни",
                callback_data=f"{SCANNER_ACTION}_{ALL_LEVELS_ACTION}",
            ),
        ],
        [
            InlineKeyboardButton(
                "⭐ Лучшие возможности",
                callback_data=f"{SCANNER_ACTION}_{BEST_OPPS_ACTION}",
            ),
        ],
        [
            InlineKeyboardButton(
                "📊 Обзор рынка",
                callback_data=f"{SCANNER_ACTION}_{MARKET_OVERVIEW_ACTION}",
            ),
        ],
        [
            InlineKeyboardButton(
                "⬅️ Назад",
                callback_data="arbitrage_menu",
            ),
        ],
    ]

    text = (
        "🔍 *Многоуровневое сканирование*\n\n"
        "Выберите уровень арбитража для поиска выгодных предметов:\n\n"
        "🚀 *Разгон* - $0.5-$3, прибыль 1.5%+\n"
        "⭐ *Стандарт* - $3-$10, прибыль 3%+\n"
        "💰 *Средний* - $10-$30, прибыль 5%+\n"
        "💎 *Продвинутый* - $30-$100, прибыль 7%+\n"
        "🏆 *Профессиональный* - $100-$1000, прибыль 10%+"
    )

    if query:
        await query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
    elif update.effective_user:
        await context.bot.send_message(
            chat_id=update.effective_user.id,
            text=text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )


async def handle_level_scan(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    level: str,
    game: str = "csgo",
) -> None:
    """Обработать сканирование конкретного уровня.

    Args:
        update: Объект Update от Telegram
        context: Контекст выполнения
        level: Уровень арбитража (boost, standard, medium, advanced, pro)
        game: Код игры

    """
    query = update.callback_query
    if not query:
        return

    await query.answer()

    if not update.effective_user:
        return

    user_id = update.effective_user.id

    # Получаем конфигурацию уровня
    if level not in ARBITRAGE_LEVELS:
        await query.edit_message_text(
            "⚠️ Неизвестный уровень арбитража.",
            parse_mode="Markdown",
        )
        return

    config = ARBITRAGE_LEVELS[level]
    level_name = config["name"]

    await query.edit_message_text(
        f"🔍 *Сканирование уровня {level_name}*\n\n"
        f"Ищем выгодные предметы. Пожалуйста, подождите...",
        parse_mode="Markdown",
    )

    try:
        # Получаем API клиент
        api_client = create_api_client_from_env()
        if api_client is None:
            await query.edit_message_text(
                "❌ Не удалось создать API клиент. Проверьте настройки.",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("⬅️ Назад", callback_data=SCANNER_ACTION)]],
                ),
            )
            return

        # Создаем сканер
        scanner = ArbitrageScanner(api=api_client, cache_ttl=300)

        # Сканируем уровень
        results = await scanner.scan_level(level=level, game=game, max_results=50)

        if not results:
            await query.edit_message_text(
                f"ℹ️ *{level_name}*\n\n"
                f"Возможности не найдены на текущий момент.\n\n"
                f"💡 Попробуйте:\n"
                f"• Другой уровень арбитража\n"
                f"• Другую игру\n"
                f"• Подождать обновления рынка",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("⬅️ Назад", callback_data=SCANNER_ACTION)]],
                ),
            )
            return

        # Сохраняем в пагинацию
        pagination_manager.add_items_for_user(user_id, results, f"scanner_{level}")

        # Получаем первую страницу
        items, current_page, total_pages = pagination_manager.get_page(user_id)

        # Форматируем текст
        formatted_text = format_scanner_results(
            items,
            current_page,
            pagination_manager.get_items_per_page(user_id),
        )

        # Создаем клавиатуру с пагинацией
        keyboard = create_pagination_keyboard(
            current_page=current_page,
            total_pages=total_pages,
            prefix=f"scanner_paginate:{level}_{game}_",
            with_nums=True,
            back_button=True,
            back_text="⬅️ Назад к сканеру",
            back_callback=SCANNER_ACTION,
        )

        # Отправляем результаты
        header = (
            f"*{level_name}*\n"
            f"🎮 {GAMES.get(game, game)}\n"
            f"📊 Найдено: {len(results)} возможностей\n\n"
        )

        await query.edit_message_text(
            header + formatted_text,
            parse_mode="Markdown",
            reply_markup=keyboard,
        )

    except Exception as e:
        logger.error(f"Ошибка при сканировании уровня {level}: {e}", exc_info=True)
        await query.edit_message_text(
            f"⚠️ Произошла ошибка при сканировании: {e!s}",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("⬅️ Назад", callback_data=SCANNER_ACTION)]],
            ),
        )


async def handle_market_overview(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    game: str = "csgo",
) -> None:
    """Показать обзор рынка по всем уровням.

    Args:
        update: Объект Update от Telegram
        context: Контекст выполнения
        game: Код игры

    """
    query = update.callback_query
    if not query:
        return

    await query.answer()

    await query.edit_message_text(
        "📊 Анализ рынка...\n\nСканируем все уровни, пожалуйста, подождите...",
        parse_mode="Markdown",
    )

    try:
        # Получаем API клиент
        api_client = create_api_client_from_env()
        if api_client is None:
            await query.edit_message_text(
                "❌ Не удалось создать API клиент.",
                parse_mode="Markdown",
            )
            return

        # Создаем сканер
        scanner = ArbitrageScanner(api=api_client, cache_ttl=300)

        # Получаем обзор рынка
        overview = await scanner.get_market_overview(game=game)

        # Форматируем результаты
        best_level = overview["best_level"]
        best_level_name = ARBITRAGE_LEVELS[best_level]["name"] if best_level else "N/A"

        text_lines = [
            f"📊 *Обзор рынка {GAMES.get(game, game)}*\n",
            f"🎯 Всего возможностей: {overview['total_opportunities']}",
            f"💰 Лучшая прибыль: {overview['best_profit_percent']:.1f}%",
            f"🏆 Лучший уровень: {best_level_name}\n",
            "📈 *По уровням:*",
        ]

        for level_key, count in overview["results_by_level"].items():
            level_name = ARBITRAGE_LEVELS[level_key]["name"]
            text_lines.append(f"  {level_name}: {count} шт.")

        text = "\n".join(text_lines)

        # Добавляем информацию о глубине рынка (API v1.1.0)
        try:
            from src.dmarket.market_analysis import analyze_market_depth

            # Получаем данные о глубине рынка
            depth_data = await analyze_market_depth(api_client, game=game)
            if depth_data and depth_data.get("summary"):
                summary = depth_data["summary"]
                health = summary.get("market_health", "unknown")
                avg_liquidity = summary.get("average_liquidity_score", 0)

                text += f"\n\n🏥 *Здоровье рынка*: {health}\n"
                text += f"💧 Средняя ликвидность: {avg_liquidity:.1f}/100"
        except Exception as depth_error:
            logger.debug(
                "Не удалось получить данные о глубине рынка: %s",
                depth_error,
            )

        await query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("⬅️ Назад", callback_data=SCANNER_ACTION)]],
            ),
        )

    except Exception as e:
        logger.error(f"Ошибка при получении обзора рынка: {e}", exc_info=True)
        await query.edit_message_text(
            f"⚠️ Ошибка: {e!s}",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("⬅️ Назад", callback_data=SCANNER_ACTION)]],
            ),
        )


async def handle_scanner_pagination(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Обработать навигацию по страницам результатов сканера.

    Args:
        update: Объект Update от Telegram
        context: Контекст выполнения

    """
    query = update.callback_query
    if not query:
        return

    await query.answer()

    if not update.effective_user:
        return

    user_id = update.effective_user.id
    callback_data = query.data

    # Парсим данные callback: scanner_paginate:direction:level_game_
    parts = callback_data.split(":")
    if len(parts) < 3:
        return

    direction = parts[1]
    level_game = parts[2].rstrip("_")

    # Обновляем страницу
    if direction == "next":
        pagination_manager.next_page(user_id)
    elif direction == "prev":
        pagination_manager.prev_page(user_id)

    # Получаем текущую страницу
    items, current_page, total_pages = pagination_manager.get_page(user_id)

    # Форматируем результаты
    formatted_text = format_scanner_results(
        items,
        current_page,
        pagination_manager.get_items_per_page(user_id),
    )

    # Создаем клавиатуру
    keyboard = create_pagination_keyboard(
        current_page=current_page,
        total_pages=total_pages,
        prefix=f"scanner_paginate:{level_game}_",
        with_nums=True,
        back_button=True,
        back_text="⬅️ Назад к сканеру",
        back_callback=SCANNER_ACTION,
    )

    await query.edit_message_text(
        formatted_text,
        parse_mode="Markdown",
        reply_markup=keyboard,
    )


async def handle_scanner_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Обработать callback-запросы для сканера.

    Args:
        update: Объект Update от Telegram
        context: Контекст выполнения

    """
    query = update.callback_query
    if not query:
        return

    callback_data = query.data

    # Главное меню
    if callback_data == SCANNER_ACTION:
        await start_scanner_menu(update, context)

    # Сканирование уровня
    elif callback_data.startswith(f"{SCANNER_ACTION}_{LEVEL_SCAN_ACTION}_"):
        level = callback_data.split("_")[-1]
        await handle_level_scan(update, context, level)

    # Обзор рынка
    elif callback_data == f"{SCANNER_ACTION}_{MARKET_OVERVIEW_ACTION}":
        await handle_market_overview(update, context)

    # Остальные функции - заглушки
    else:
        await query.answer("Эта функция будет реализована в следующей версии")


def register_scanner_handlers(dispatcher: Any) -> None:
    """Зарегистрировать обработчики команд сканера.

    Args:
        dispatcher: Диспетчер бота

    """
    # Основные обработчики
    dispatcher.add_handler(
        CallbackQueryHandler(handle_scanner_callback, pattern=f"^{SCANNER_ACTION}"),
    )

    # Обработчик пагинации
    dispatcher.add_handler(
        CallbackQueryHandler(handle_scanner_pagination, pattern="^scanner_paginate:"),
    )
