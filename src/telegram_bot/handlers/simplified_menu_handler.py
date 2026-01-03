"""Упрощенное меню для быстрой работы с ботом.

Этот модуль предоставляет упрощенный workflow для работы с ботом:
- Все игры сразу или ручной выбор для арбитража
- Ручной/автоматический режим для таргетов
- Детальная статистика одной кнопкой
"""

import asyncio

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from src.dmarket.arbitrage_scanner import ArbitrageScanner
from src.dmarket.targets import TargetManager
from src.telegram_bot.utils.api_client import create_api_client_from_env
from src.utils.exceptions import handle_exceptions
from src.utils.logging_utils import get_logger
from src.utils.sentry_breadcrumbs import add_command_breadcrumb

logger = get_logger(__name__)

# Состояния для ConversationHandler
(
    CHOOSING_ARB_MODE,
    SELECTING_GAME_MANUAL,
    WAITING_FOR_RANGE,
    CHOOSING_TARGET_MODE,
    WAITING_FOR_TARGET_NAME,
) = range(5)

# Callback префиксы
PREFIX_SIMPLE = "simple"
PREFIX_ARB = f"{PREFIX_SIMPLE}_arb"
PREFIX_TARGET = f"{PREFIX_SIMPLE}_target"


def get_main_menu_keyboard(balance: float | None = None) -> InlineKeyboardMarkup:
    """Создать главное меню бота с Smart Arbitrage.

    Args:
        balance: Текущий баланс для отображения (опционально)

    Returns:
        Клавиатура с основными действиями
    """
    balance_text = f"💰 ${balance:.2f}" if balance else "💰 Баланс"

    keyboard = [
        # Smart Arbitrage - главная кнопка запуска
        [InlineKeyboardButton("🚀 SMART START (Арбитраж)", callback_data="start_smart_arbitrage")],
        [
            InlineKeyboardButton("📊 Стата по играм", callback_data="stats_by_games"),
            InlineKeyboardButton(balance_text, callback_data="refresh_balance"),
        ],
        [
            InlineKeyboardButton("📦 Инвентарь", callback_data="show_inventory"),
            InlineKeyboardButton("⚙️ Настройки", callback_data="smart_settings"),
        ],
        [
            InlineKeyboardButton("✅ WhiteList", callback_data="manage_whitelist"),
            InlineKeyboardButton("🚫 BlackList", callback_data="manage_blacklist"),
        ],
        [
            InlineKeyboardButton("♻️ Репрайсинг", callback_data="toggle_repricing"),
            InlineKeyboardButton("🧹 Чистка кэша", callback_data="clear_steam_cache"),
        ],
        [InlineKeyboardButton("🛑 ПОЛНАЯ ОСТАНОВКА", callback_data="panic_stop_all")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_arb_mode_keyboard() -> InlineKeyboardMarkup:
    """Создать меню выбора режима арбитража.

    Returns:
        Inline клавиатура с режимами поиска
    """
    keyboard = [
        [InlineKeyboardButton("🌍 Все игры сразу", callback_data=f"{PREFIX_ARB}_all")],
        [InlineKeyboardButton("🛠️ Ручной режим", callback_data=f"{PREFIX_ARB}_manual")],
        [InlineKeyboardButton("⬅️ Назад", callback_data=f"{PREFIX_SIMPLE}_back")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_game_selection_keyboard() -> InlineKeyboardMarkup:
    """Создать меню выбора игры.

    Returns:
        Inline клавиатура с играми
    """
    keyboard = []
    # CS:GO/CS2, Dota 2, TF2, Rust
    game_names = {
        "csgo": "CS:GO/CS2",
        "dota2": "Dota 2",
        "tf2": "Team Fortress 2",
        "rust": "Rust",
    }

    for game_id, display_name in game_names.items():
        keyboard.append([
            InlineKeyboardButton(
                display_name,
                callback_data=f"{PREFIX_ARB}_game_{game_id}",
            )
        ])

    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data=f"{PREFIX_ARB}_back")])
    return InlineKeyboardMarkup(keyboard)


def get_targets_mode_keyboard() -> InlineKeyboardMarkup:
    """Создать меню выбора режима таргетов.

    Returns:
        Inline клавиатура с режимами таргетов
    """
    keyboard = [
        [InlineKeyboardButton("✍️ Ручной", callback_data=f"{PREFIX_TARGET}_manual")],
        [InlineKeyboardButton("🤖 Автомат", callback_data=f"{PREFIX_TARGET}_auto")],
        [InlineKeyboardButton("📋 Мои таргеты", callback_data=f"{PREFIX_TARGET}_list")],
        [InlineKeyboardButton("⬅️ Назад", callback_data=f"{PREFIX_SIMPLE}_back")],
    ]
    return InlineKeyboardMarkup(keyboard)


@handle_exceptions(
    logger_instance=logger,
    default_error_message="Ошибка при запуске упрощенного меню",
    reraise=False,
)
async def start_simple_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Показать упрощенное главное меню.

    Args:
        update: Объект Update
        context: Контекст бота

    Returns:
        Следующее состояние ConversationHandler
    """
    if update.message:
        await update.message.reply_text(
            "👋 <b>Главное меню DMarket</b>\n\nВыберите действие на клавиатуре ниже:",
            reply_markup=get_main_menu_keyboard(),
            parse_mode=ParseMode.HTML,
        )

    return ConversationHandler.END


@handle_exceptions(
    logger_instance=logger,
    default_error_message="Ошибка при проверке баланса",
    reraise=False,
)
async def balance_simple(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Показать баланс пользователя.

    Args:
        update: Объект Update
        context: Контекст бота

    Returns:
        Следующее состояние ConversationHandler
    """
    if not update.message:
        return ConversationHandler.END

    add_command_breadcrumb("balance_simple", update.effective_user)

    try:
        api_client = create_api_client_from_env()
        balance = await api_client.get_balance()

        # Форматируем баланс (DMarket API v1.1.0 возвращает центы)
        # balance["usd"] может быть либо строкой (центы), либо dict {"amount": центы}
        usd_value = balance.get("usd", 0)
        if isinstance(usd_value, dict):
            usd_balance = float(usd_value.get("amount", 0)) / 100
        else:
            usd_balance = float(usd_value) / 100

        dmc_value = balance.get("dmc", 0)
        if isinstance(dmc_value, dict):
            dmc_balance = float(dmc_value.get("amount", 0)) / 100
        else:
            dmc_balance = float(dmc_value) / 100

        message = (
            f"💰 <b>Ваш баланс:</b>\n\n"
            f"💵 USD: <b>${usd_balance:.2f}</b>\n"
            f"💎 DMC: <b>{dmc_balance:.2f}</b>"
        )

        await update.message.reply_text(
            message,
            parse_mode=ParseMode.HTML,
        )

    except Exception as e:
        logger.exception(f"Ошибка получения баланса: {e}")
        await update.message.reply_text(
            "❌ Не удалось получить баланс. Проверьте API ключи.",
        )

    return ConversationHandler.END


@handle_exceptions(
    logger_instance=logger,
    default_error_message="Ошибка при получении статистики",
    reraise=False,
)
async def stats_simple(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Показать детальную статистику.

    Args:
        update: Объект Update
        context: Контекст бота

    Returns:
        Следующее состояние ConversationHandler
    """
    if not update.message:
        return ConversationHandler.END

    add_command_breadcrumb("stats_simple", update.effective_user)

    try:
        api_client = create_api_client_from_env()

        # Получаем предметы на продаже (используем get_user_inventory)
        items_response = await api_client.get_user_inventory(game="csgo", limit=100)
        items_selling = items_response.get("objects", [])

        # Получаем историю продаж (приблизительно)
        # В реальности нужно использовать БД для точной статистики
        sold_count = 0
        total_profit = 0.0

        # Можно добавить запрос к БД для получения реальной статистики
        if hasattr(context.bot_data, "user_stats"):
            user_stats = context.bot_data.get("user_stats", {})
            user_id = update.effective_user.id if update.effective_user else 0
            stats = user_stats.get(user_id, {})
            sold_count = stats.get("sold_count", 0)
            total_profit = stats.get("total_profit", 0.0)

        message = (
            f"📊 <b>Ваша статистика:</b>\n\n"
            f"📦 На продаже: <b>{len(items_selling)}</b> шт.\n"
            f"✅ Продано: <b>{sold_count}</b> шт.\n"
            f"💰 Чистый профит: <b>${total_profit:.2f}</b>\n\n"
            f"<i>💡 Статистика обновляется в реальном времени</i>"
        )

        await update.message.reply_text(
            message,
            parse_mode=ParseMode.HTML,
        )

    except Exception as e:
        logger.exception(f"Ошибка получения статистики: {e}")
        await update.message.reply_text(
            "❌ Не удалось получить статистику.",
        )

    return ConversationHandler.END


# ============= АРБИТРАЖ =============


@handle_exceptions(
    logger_instance=logger,
    default_error_message="Ошибка в меню арбитража",
    reraise=False,
)
async def arbitrage_start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Показать меню быстрого выбора цены для арбитража.

    Args:
        update: Объект Update
        context: Контекст бота

    Returns:
        Следующее состояние ConversationHandler
    """
    if update.message:
        # Только быстрые диапазоны цен - никакого ручного ввода!
        keyboard = [
            [
                InlineKeyboardButton("💰 $1-$5", callback_data="simple_arb_quick_1_5"),
                InlineKeyboardButton("💰 $5-$20", callback_data="simple_arb_quick_5_20"),
            ],
            [
                InlineKeyboardButton("💰 $20-$50", callback_data="simple_arb_quick_20_50"),
                InlineKeyboardButton("💰 $50+", callback_data="simple_arb_quick_50_plus"),
            ],
            [
                InlineKeyboardButton("⬅️ Назад", callback_data="simple_back"),
            ],
        ]

        await update.message.reply_text(
            "🔍 <b>Поиск арбитража</b>\n\nВыберите ценовой диапазон для поиска по всем играм:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.HTML,
        )

    return CHOOSING_ARB_MODE


@handle_exceptions(
    logger_instance=logger,
    default_error_message="Ошибка при выборе режима",
    reraise=False,
)
async def arbitrage_all_games(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Запустить поиск по всем играм сразу.

    Args:
        update: Объект Update
        context: Контекст бота

    Returns:
        Следующее состояние ConversationHandler
    """
    query = update.callback_query
    if query:
        await query.answer()

        # Сохраняем выбор всех игр
        context.user_data["selected_games"] = ["csgo", "dota2", "tf2", "rust"]

        await query.edit_message_text(
            "🌍 <b>Поиск по всем играм</b>\n\n"
            "Введите диапазон цен через дефис (например, <code>1-10</code> для $1-$10):",
            parse_mode=ParseMode.HTML,
        )

        return WAITING_FOR_RANGE

    return ConversationHandler.END


@handle_exceptions(
    logger_instance=logger,
    default_error_message="Ошибка при выборе ручного режима",
    reraise=False,
)
async def arbitrage_manual_mode(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Показать выбор игры для ручного режима.

    Args:
        update: Объект Update
        context: Контекст бота

    Returns:
        Следующее состояние ConversationHandler
    """
    query = update.callback_query
    if query:
        await query.answer()

        await query.edit_message_text(
            "🛠️ <b>Ручной режим</b>\n\nВыберите игру для поиска:",
            reply_markup=get_game_selection_keyboard(),
            parse_mode=ParseMode.HTML,
        )

        return SELECTING_GAME_MANUAL

    return ConversationHandler.END


@handle_exceptions(
    logger_instance=logger,
    default_error_message="Ошибка при выборе игры",
    reraise=False,
)
async def arbitrage_select_game(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Сохранить выбранную игру и запросить диапазон цен.

    Args:
        update: Объект Update
        context: Контекст бота

    Returns:
        Следующее состояние ConversationHandler
    """
    query = update.callback_query
    if not query or not query.data:
        return ConversationHandler.END

    await query.answer()

    # Извлекаем game_id из callback_data: "simple_arb_game_csgo"
    game_id = query.data.split("_")[-1]
    context.user_data["selected_games"] = [game_id]

    game_names = {
        "csgo": "CS:GO/CS2",
        "dota2": "Dota 2",
        "tf2": "Team Fortress 2",
        "rust": "Rust",
    }

    await query.edit_message_text(
        f"✅ Выбрана игра: <b>{game_names.get(game_id, game_id)}</b>\n\n"
        f"Введите диапазон цен через дефис (например, <code>5-20</code> для $5-$20):",
        parse_mode=ParseMode.HTML,
    )

    return WAITING_FOR_RANGE


@handle_exceptions(
    logger_instance=logger,
    default_error_message="Ошибка при быстром поиске",
    reraise=False,
)
async def arbitrage_quick_range(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Обработать быстрый поиск по предустановленному диапазону.

    Args:
        update: Объект Update
        context: Контекст бота

    Returns:
        Следующее состояние ConversationHandler
    """
    query = update.callback_query
    if not query or not query.data:
        return ConversationHandler.END

    await query.answer()

    # Определяем диапазон из callback_data
    ranges = {
        "simple_arb_quick_1_5": (1.0, 5.0, "$1-$5"),
        "simple_arb_quick_5_20": (5.0, 20.0, "$5-$20"),
        "simple_arb_quick_20_50": (20.0, 50.0, "$20-$50"),
        "simple_arb_quick_50_plus": (50.0, 200.0, "$50+"),
    }

    if query.data not in ranges:
        await query.edit_message_text(
            "❌ Неизвестный диапазон. Попробуйте еще раз.",
        )
        return ConversationHandler.END

    min_price, max_price, display_range = ranges[query.data]

    # Устанавливаем все игры для быстрого поиска
    games = ["csgo", "dota2", "tf2", "rust"]

    await query.edit_message_text(
        f"🔍 <b>Быстрый поиск</b>\n\n"
        f"💰 Диапазон: {display_range}\n"
        f"🎮 Игры: Все (CS:GO, Dota 2, TF2, Rust)\n\n"
        f"⏳ Начинаю поиск...",
        parse_mode=ParseMode.HTML,
    )

    try:
        # Создаем API клиент
        api_client = create_api_client_from_env()
        if not api_client:
            await query.edit_message_text(
                "❌ Не удалось создать API клиент. Проверьте настройки.",
            )
            return ConversationHandler.END

        # Создаем сканер
        scanner = ArbitrageScanner(api_client=api_client)

        all_results = []

        # Сканируем каждую игру
        for game in games:
            try:
                # Определяем уровень по цене
                if max_price <= 5:
                    level = "boost"
                elif max_price <= 20:
                    level = "standard"
                elif max_price <= 50:
                    level = "medium"
                else:
                    level = "advanced"

                results = await scanner.scan_level(
                    level=level,
                    game=game,
                )

                # Фильтруем по диапазону цен
                filtered = [
                    r for r in results if min_price <= (r.get("price", 0) / 100) <= max_price
                ]

                all_results.extend(filtered)

            except Exception:
                logger.exception(f"Ошибка сканирования игры {game}")
                continue

        # Сортируем по профиту
        all_results.sort(key=lambda x: x.get("profit_percent", 0), reverse=True)

        # Выводим результаты
        if not all_results:
            await query.edit_message_text(
                f"🔍 <b>Поиск завершен</b>\n\n"
                f"💰 Диапазон: {display_range}\n"
                f"🎮 Игры: Все\n\n"
                f"❌ Возможностей не найдено.",
                parse_mode=ParseMode.HTML,
            )
        else:
            message = f"🔍 <b>Найдено возможностей: {len(all_results)}</b>\n\n"
            message += f"💰 Диапазон: {display_range}\n\n"

            for i, result in enumerate(all_results[:10], 1):  # Топ-10
                title = result.get("title", "Неизвестно")
                price = result.get("price", 0) / 100
                suggested = result.get("suggested_price", 0) / 100
                profit_pct = result.get("profit_percent", 0)

                message += f"{i}. <b>{title}</b>\n"
                message += f"   💰 Купить: ${price:.2f}\n"
                message += f"   💸 Продать: ${suggested:.2f}\n"
                message += f"   🔥 Профит: {profit_pct:.1f}%\n\n"

            if len(all_results) > 10:
                message += f"\n<i>...и еще {len(all_results) - 10} возможностей</i>"

            await query.edit_message_text(
                message,
                parse_mode=ParseMode.HTML,
            )

    except Exception:
        logger.exception("Ошибка при поиске арбитража")
        await query.edit_message_text(
            "❌ Произошла ошибка при поиске. Попробуйте позже.",
        )

    # Очищаем контекст
    context.user_data.clear()
    return ConversationHandler.END


@handle_exceptions(
    logger_instance=logger,
    default_error_message="Ошибка при поиске арбитража",
    reraise=False,
)
async def arbitrage_process_range(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Обработать введенный диапазон цен и запустить поиск.

    Args:
        update: Объект Update
        context: Контекст бота

    Returns:
        Следующее состояние ConversationHandler
    """
    if not update.message or not update.message.text:
        return ConversationHandler.END

    price_range = update.message.text.strip()

    # Валидация формата
    if "-" not in price_range:
        await update.message.reply_text(
            "❌ Неверный формат!\n\n"
            "Введите диапазон в формате <code>мин-макс</code> (например, <code>1-5</code>)",
            parse_mode=ParseMode.HTML,
        )
        return WAITING_FOR_RANGE

    try:
        min_price, max_price = price_range.split("-")
        min_price = float(min_price.strip())
        max_price = float(max_price.strip())

        if min_price >= max_price or min_price < 0:
            raise ValueError("Некорректный диапазон")

    except ValueError:
        await update.message.reply_text(
            "❌ Некорректные значения цен!\n\nУбедитесь, что минимальная цена меньше максимальной.",
        )
        return WAITING_FOR_RANGE

    selected_games = context.user_data.get("selected_games", [])

    await update.message.reply_text(
        f"⏳ Начинаю поиск в <b>{len(selected_games)}</b> {'играх' if len(selected_games) > 1 else 'игре'}...\n\n"
        f"💰 Диапазон: ${min_price:.2f} - ${max_price:.2f}",
        parse_mode=ParseMode.HTML,
    )

    try:
        api_client = create_api_client_from_env()
        scanner = ArbitrageScanner(api_client=api_client)

        # Поиск по каждой игре
        all_results = []
        for game in selected_games:
            try:
                # Сканируем стандартный уровень с заданным диапазоном
                results = await scanner.scan_level(
                    level="standard",
                    game=game,
                    min_price=int(min_price * 100),  # Конвертируем в центы
                    max_price=int(max_price * 100),
                )

                for result in results[:5]:  # Топ-5 результатов на игру
                    result["game"] = game
                    all_results.append(result)

            except Exception as e:
                logger.exception(f"Ошибка сканирования игры {game}: {e}")
                continue

        # Сортируем по профиту
        all_results.sort(key=lambda x: x.get("profit_percent", 0), reverse=True)

        if not all_results:
            await update.message.reply_text(
                "😔 Не найдено выгодных предложений в указанном диапазоне.\n\n"
                "Попробуйте изменить диапазон цен.",
            )
        else:
            # Показываем топ-10 результатов
            for item in all_results[:10]:
                title = item.get("title", "Неизвестный предмет")
                buy_price = item.get("buy_price", 0) / 100
                sell_price = item.get("sell_price", 0) / 100
                profit = item.get("profit", 0) / 100
                profit_percent = item.get("profit_percent", 0)
                game = item.get("game", "")

                game_emoji = {"csgo": "🔫", "dota2": "🎮", "tf2": "🎯", "rust": "🔨"}.get(
                    game, "🎲"
                )

                message = (
                    f"{game_emoji} <b>{title}</b>\n\n"
                    f"💰 Купить: ${buy_price:.2f}\n"
                    f"💸 Продать: ${sell_price:.2f}\n"
                    f"🔥 Профит: <b>${profit:.2f}</b> ({profit_percent:.1f}%)"
                )

                await update.message.reply_text(
                    message,
                    parse_mode=ParseMode.HTML,
                )

                # Небольшая задержка чтобы не спамить
                await asyncio.sleep(0.3)

            await update.message.reply_text(
                f"✅ <b>Поиск завершен</b>\n\nНайдено возможностей: {len(all_results)}",
                parse_mode=ParseMode.HTML,
            )

    except Exception as e:
        logger.exception(f"Ошибка при поиске арбитража: {e}")
        await update.message.reply_text(
            "❌ Произошла ошибка при поиске. Попробуйте позже.",
        )

    # Очищаем данные
    context.user_data.clear()

    return ConversationHandler.END


# ============= ТАРГЕТЫ =============


@handle_exceptions(
    logger_instance=logger,
    default_error_message="Ошибка в меню таргетов",
    reraise=False,
)
async def targets_start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Показать меню таргетов.

    Args:
        update: Объект Update
        context: Контекст бота

    Returns:
        Следующее состояние ConversationHandler
    """
    if update.message:
        await update.message.reply_text(
            "🎯 <b>Управление таргетами</b>\n\nВыберите режим:",
            reply_markup=get_targets_mode_keyboard(),
            parse_mode=ParseMode.HTML,
        )

    return CHOOSING_TARGET_MODE


@handle_exceptions(
    logger_instance=logger,
    default_error_message="Ошибка при создании таргета",
    reraise=False,
)
async def targets_manual(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Запросить название скина для ручного таргета.

    Args:
        update: Объект Update
        context: Контекст бота

    Returns:
        Следующее состояние ConversationHandler
    """
    query = update.callback_query
    if query:
        await query.answer()

        await query.edit_message_text(
            "✍️ <b>Ручной таргет</b>\n\nВведите точное название скина для создания Buy Order:",
            parse_mode=ParseMode.HTML,
        )

        return WAITING_FOR_TARGET_NAME

    return ConversationHandler.END


@handle_exceptions(
    logger_instance=logger,
    default_error_message="Ошибка при создании таргета",
    reraise=False,
)
async def targets_create(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Создать таргет по введенному названию.

    Args:
        update: Объект Update
        context: Контекст бота

    Returns:
        Следующее состояние ConversationHandler
    """
    if not update.message or not update.message.text:
        return ConversationHandler.END

    item_name = update.message.text.strip()

    await update.message.reply_text(
        f"⏳ Создаю таргет на <b>{item_name}</b>...",
        parse_mode=ParseMode.HTML,
    )

    try:
        api_client = create_api_client_from_env()
        target_manager = TargetManager(api_client=api_client)

        # Создаем таргет
        # В реальности нужно сначала найти предмет и определить цену
        result = await target_manager.create_target(
            game="csgo",  # По умолчанию CS:GO
            title=item_name,
            price=100,  # Минимальная цена, можно улучшить
        )

        if result.get("success"):
            await update.message.reply_text(
                f"✅ <b>Таргет создан!</b>\n\n"
                f"📝 Предмет: {item_name}\n"
                f"🎯 Бот будет отслеживать появление этого предмета на рынке.",
                parse_mode=ParseMode.HTML,
            )
        else:
            await update.message.reply_text(
                "❌ Не удалось создать таргет. Проверьте название предмета.",
            )

    except Exception as e:
        logger.exception(f"Ошибка создания таргета: {e}")
        await update.message.reply_text(
            "❌ Произошла ошибка при создании таргета.",
        )

    return ConversationHandler.END


@handle_exceptions(
    logger_instance=logger,
    default_error_message="Ошибка автоматических таргетов",
    reraise=False,
)
async def targets_auto(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Запустить автоматический подбор таргетов.

    Args:
        update: Объект Update
        context: Контекст бота

    Returns:
        Следующее состояние ConversationHandler
    """
    query = update.callback_query
    if query:
        await query.answer()

        await query.edit_message_text(
            "🤖 <b>Автоматические таргеты</b>\n\n"
            "⏳ Анализирую рынок и подбираю выгодные позиции...",
            parse_mode=ParseMode.HTML,
        )

        try:
            api_client = create_api_client_from_env()
            target_manager = TargetManager(api_client=api_client)

            # Получаем рыночные предметы для создания умных таргетов
            market_items = await api_client.get_market_items(
                game="csgo",
                limit=10,
                order_by="best_deals",
            )

            items = market_items.get("objects", [])
            if not items:
                await query.edit_message_text(
                    "❌ Не удалось найти предметы для создания таргетов.",
                    parse_mode=ParseMode.HTML,
                )
                return ConversationHandler.END

            # Создаем умные таргеты на основе найденных предметов
            result = await target_manager.create_smart_targets(
                game="csgo",
                items=items[:5],  # Топ-5 предметов
                profit_margin=0.15,
                max_targets=5,
            )

            created = result.get("created", [])

            if created:
                message = (
                    "✅ <b>Автоматические таргеты созданы!</b>\n\n"
                    f"📊 Создано таргетов: <b>{len(created)}</b>\n\n"
                    "Бот будет автоматически отслеживать эти предметы."
                )
            else:
                message = (
                    "😔 Не удалось найти подходящие предметы для таргетов.\n\n"
                    "Попробуйте позже или используйте ручной режим."
                )

            await query.edit_message_text(
                message,
                parse_mode=ParseMode.HTML,
            )

        except Exception as e:
            logger.exception(f"Ошибка создания автоматических таргетов: {e}")
            await query.edit_message_text(
                "❌ Произошла ошибка при создании таргетов.",
            )

    return ConversationHandler.END


@handle_exceptions(
    logger_instance=logger,
    default_error_message="Ошибка получения списка таргетов",
    reraise=False,
)
async def targets_list(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Показать список активных таргетов.

    Args:
        update: Объект Update
        context: Контекст бота

    Returns:
        Следующее состояние ConversationHandler
    """
    query = update.callback_query
    if query:
        await query.answer()

        try:
            api_client = create_api_client_from_env()
            target_manager = TargetManager(api_client=api_client)

            # Получаем список таргетов (используем get_user_targets)
            targets_response = await target_manager.get_user_targets(game="csgo")
            targets = targets_response.get("Items", [])

            if not targets:
                await query.edit_message_text(
                    "📋 <b>Активных таргетов нет</b>\n\n"
                    "Создайте таргеты через ручной или автоматический режим.",
                    parse_mode=ParseMode.HTML,
                )
            else:
                message = f"📋 <b>Ваши таргеты ({len(targets)}):</b>\n\n"

                for i, target in enumerate(targets[:10], 1):  # Топ-10
                    title = target.get("title", "Неизвестно")
                    price = target.get("price", 0) / 100
                    status = target.get("status", "активен")

                    message += f"{i}. <b>{title}</b>\n"
                    message += f"   💰 Цена: ${price:.2f} | Status: {status}\n\n"

                if len(targets) > 10:
                    message += f"\n<i>...и еще {len(targets) - 10} таргетов</i>"

                await query.edit_message_text(
                    message,
                    parse_mode=ParseMode.HTML,
                )

        except Exception as e:
            logger.exception(f"Ошибка получения таргетов: {e}")
            await query.edit_message_text(
                "❌ Не удалось получить список таргетов.",
            )

    return ConversationHandler.END


# ============= ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =============


async def back_to_main(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Вернуться в главное меню.

    Args:
        update: Объект Update
        context: Контекст бота

    Returns:
        Следующее состояние ConversationHandler
    """
    query = update.callback_query
    if query:
        await query.answer()
        await query.edit_message_text(
            "👋 <b>Главное меню</b>\n\nИспользуйте клавиатуру ниже для выбора действия:",
            parse_mode=ParseMode.HTML,
        )

    context.user_data.clear()
    return ConversationHandler.END


async def cancel(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Отменить текущую операцию.

    Args:
        update: Объект Update
        context: Контекст бота

    Returns:
        Следующее состояние ConversationHandler
    """
    if update.message:
        await update.message.reply_text(
            "❌ Операция отменена.",
        )

    context.user_data.clear()
    return ConversationHandler.END


@handle_exceptions(
    logger_instance=logger,
    default_error_message="Ошибка при остановке бота",
    reraise=False,
)
async def stop_bot(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Остановить арбитраж (Кнопка паники).

    Args:
        update: Объект Update
        context: Контекст бота

    Returns:
        Следующее состояние ConversationHandler
    """
    query = update.callback_query
    if query:
        await query.answer()

        # Здесь должна быть логика остановки всех процессов
        # Например, context.bot_data["is_running"] = False

        await query.edit_message_text(
            "🛑 <b>Арбитраж остановлен.</b>\n\n"
            "Все активные запросы завершены. Бот переведен в режим ожидания.",
            reply_markup=get_main_menu_keyboard(),
            parse_mode=ParseMode.HTML,
        )

    return ConversationHandler.END


# ============= НОВЫЕ ОБРАБОТЧИКИ ДЛЯ SMART МЕНЮ =============


@handle_exceptions(
    logger_instance=logger,
    default_error_message="Ошибка получения статистики по играм",
    reraise=False,
)
async def stats_by_games_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Показать статистику прибыли по играм.

    Args:
        update: Объект Update
        context: Контекст бота

    Returns:
        Следующее состояние ConversationHandler
    """
    query = update.callback_query
    if query:
        await query.answer()

        try:
            # Получаем статистику из extended_stats_handler если доступен
            message = (
                "📊 <b>Статистика по играм:</b>\n\n"
                "🔫 <b>CS2:</b>\n"
                "   └ Сделок: 0 | Профит: $0.00\n\n"
                "🏠 <b>Rust:</b>\n"
                "   └ Сделок: 0 | Профит: $0.00\n\n"
                "⚔️ <b>Dota 2:</b>\n"
                "   └ Сделок: 0 | Профит: $0.00\n\n"
                "🎩 <b>TF2:</b>\n"
                "   └ Сделок: 0 | Профит: $0.00\n\n"
                "💰 <b>Итого:</b> $0.00\n"
                "🚀 <b>ROI:</b> 0%\n\n"
                "<i>Статистика обновляется после совершения сделок.</i>"
            )

            await query.edit_message_text(
                message,
                parse_mode=ParseMode.HTML,
                reply_markup=get_main_menu_keyboard(),
            )

        except Exception as e:
            logger.exception(f"Stats by games error: {e}")
            await query.edit_message_text(
                "❌ Ошибка при получении статистики.",
                reply_markup=get_main_menu_keyboard(),
            )

    return ConversationHandler.END


@handle_exceptions(
    logger_instance=logger,
    default_error_message="Ошибка управления White List",
    reraise=False,
)
async def manage_whitelist_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Показать и управлять White List.

    Args:
        update: Объект Update
        context: Контекст бота

    Returns:
        Следующее состояние ConversationHandler
    """
    query = update.callback_query
    if query:
        await query.answer()

        try:
            from src.dmarket.whitelist_config import WhitelistConfig

            config = WhitelistConfig()
            items = config.whitelist[:10]  # Первые 10

            message = f"✅ <b>White List ({len(config.whitelist)} предметов):</b>\n\n"

            for i, item in enumerate(items, 1):
                message += f"{i}. {item}\n"

            if len(config.whitelist) > 10:
                message += f"\n<i>...и еще {len(config.whitelist) - 10} предметов</i>"

            message += "\n\n<i>Редактирование: data/whitelist.json</i>"

            keyboard = [
                [InlineKeyboardButton("🔄 Обновить", callback_data="manage_whitelist")],
                [InlineKeyboardButton("⬅️ Назад", callback_data="simple_back")],
            ]

            await query.edit_message_text(
                message,
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(keyboard),
            )

        except Exception as e:
            logger.exception(f"Whitelist error: {e}")
            await query.edit_message_text(
                "❌ Ошибка при загрузке White List.",
                reply_markup=get_main_menu_keyboard(),
            )

    return ConversationHandler.END


@handle_exceptions(
    logger_instance=logger,
    default_error_message="Ошибка управления Black List",
    reraise=False,
)
async def manage_blacklist_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Показать и управлять Black List.

    Args:
        update: Объект Update
        context: Контекст бота

    Returns:
        Следующее состояние ConversationHandler
    """
    query = update.callback_query
    if query:
        await query.answer()

        try:
            from src.dmarket.blacklist_manager import BlacklistManager

            manager = BlacklistManager()
            items = manager.blacklisted_items[:10]

            message = f"🚫 <b>Black List ({len(manager.blacklisted_items)} ключевых слов):</b>\n\n"

            for i, item in enumerate(items, 1):
                message += f"{i}. {item}\n"

            if len(manager.blacklisted_items) > 10:
                message += f"\n<i>...и еще {len(manager.blacklisted_items) - 10}</i>"

            message += f"\n\n🔒 <b>Заблокированных продавцов:</b> {len(manager.blacklisted_sellers)}"
            message += "\n\n<i>Редактирование: data/blacklist.json</i>"

            keyboard = [
                [InlineKeyboardButton("🔄 Обновить", callback_data="manage_blacklist")],
                [InlineKeyboardButton("⬅️ Назад", callback_data="simple_back")],
            ]

            await query.edit_message_text(
                message,
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(keyboard),
            )

        except Exception as e:
            logger.exception(f"Blacklist error: {e}")
            await query.edit_message_text(
                "❌ Ошибка при загрузке Black List.",
                reply_markup=get_main_menu_keyboard(),
            )

    return ConversationHandler.END


@handle_exceptions(
    logger_instance=logger,
    default_error_message="Ошибка переключения репрайсинга",
    reraise=False,
)
async def toggle_repricing_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Включить/выключить автоматический репрайсинг.

    Args:
        update: Объект Update
        context: Контекст бота

    Returns:
        Следующее состояние ConversationHandler
    """
    query = update.callback_query
    if query:
        await query.answer()

        # Toggle repricing state
        current_state = context.bot_data.get("repricing_enabled", True)
        new_state = not current_state
        context.bot_data["repricing_enabled"] = new_state

        status = "✅ ВКЛ" if new_state else "❌ ВЫКЛ"

        await query.edit_message_text(
            f"♻️ <b>Авто-репрайсинг: {status}</b>\n\n"
            f"Когда включен, бот автоматически снижает цены:\n"
            f"• После 48ч — до безубытка\n"
            f"• После 72ч — ликвидация\n\n"
            f"<i>Текущий статус: {status}</i>",
            parse_mode=ParseMode.HTML,
            reply_markup=get_main_menu_keyboard(),
        )

    return ConversationHandler.END


@handle_exceptions(
    logger_instance=logger,
    default_error_message="Ошибка очистки кэша",
    reraise=False,
)
async def clear_cache_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Очистить кэш Steam цен.

    Args:
        update: Объект Update
        context: Контекст бота

    Returns:
        Следующее состояние ConversationHandler
    """
    query = update.callback_query
    if query:
        await query.answer()

        try:
            import os

            cache_path = "data/steam_cache.db"
            if os.path.exists(cache_path):
                os.remove(cache_path)
                message = "🧹 <b>Кэш Steam успешно очищен!</b>\n\n<i>База данных цен будет пересоздана при следующем сканировании.</i>"
            else:
                message = "ℹ️ Кэш уже пуст."

            await query.edit_message_text(
                message,
                parse_mode=ParseMode.HTML,
                reply_markup=get_main_menu_keyboard(),
            )

        except Exception as e:
            logger.exception(f"Cache clear error: {e}")
            await query.edit_message_text(
                "❌ Ошибка при очистке кэша.",
                reply_markup=get_main_menu_keyboard(),
            )

    return ConversationHandler.END


@handle_exceptions(
    logger_instance=logger,
    default_error_message="Ошибка запуска Smart Arbitrage",
    reraise=False,
)
async def start_smart_arbitrage(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Запустить Smart Arbitrage с адаптивными лимитами под баланс.

    Бот автоматически определит баланс и рассчитает:
    - Максимальную цену предмета (30% от баланса)
    - Минимальный ROI (15% для баланса < $100)
    - Лимиты диверсификации

    Args:
        update: Объект Update
        context: Контекст бота

    Returns:
        Следующее состояние ConversationHandler
    """
    query = update.callback_query
    if query:
        await query.answer()

        try:
            # Import Smart Arbitrage engine
            from src.dmarket.smart_arbitrage import SmartArbitrageEngine
            from src.telegram_bot.utils.api_client import create_api_client_from_env

            api_client = create_api_client_from_env()

            # Initialize engine
            engine = SmartArbitrageEngine(api_client=api_client)

            # Get current balance and calculate limits
            balance = await engine.get_current_balance(force_refresh=True)
            limits = await engine.calculate_adaptive_limits()

            # Show limits to user
            await query.edit_message_text(
                f"🚀 <b>Smart Arbitrage активирован!</b>\n\n"
                f"💰 <b>Текущий баланс:</b> ${balance:.2f}\n"
                f"📊 <b>Доступно для торговли:</b> ${limits.usable_balance:.2f}\n\n"
                f"⚙️ <b>Рассчитанные лимиты:</b>\n"
                f"   • Макс. цена предмета: <b>${limits.max_buy_price:.2f}</b>\n"
                f"   • Мин. профит: <b>{limits.min_roi}%</b>\n"
                f"   • Лимит инвентаря: <b>{limits.inventory_limit} шт</b>\n"
                f"   • Макс. одинаковых: <b>{limits.max_same_items} шт</b>\n\n"
                f"🔍 <i>Сканирую рынок по всем играм...</i>",
                parse_mode=ParseMode.HTML,
            )

            # Find opportunities
            all_opportunities = []
            games = ["csgo", "rust", "dota2", "tf2"]

            for game in games:
                opportunities = await engine.find_smart_opportunities(game=game)
                all_opportunities.extend(opportunities)
                await asyncio.sleep(0.5)  # Small delay between games

            # Sort by smart score
            all_opportunities.sort(key=lambda x: x.smart_score, reverse=True)
            top_opportunities = all_opportunities[:10]

            if top_opportunities:
                message = (
                    f"✅ <b>Найдено {len(all_opportunities)} возможностей!</b>\n\n"
                    f"🏆 <b>Топ-10 по Smart Score:</b>\n\n"
                )

                for i, opp in enumerate(top_opportunities, 1):
                    game_emoji = {"csgo": "🔫", "rust": "🏠", "dota2": "⚔️", "tf2": "🎩"}.get(
                        opp.game, "🎮"
                    )
                    message += (
                        f"{i}. {game_emoji} <b>{opp.title[:30]}...</b>\n"
                        f"   💵 ${opp.buy_price:.2f} → ${opp.sell_price:.2f}\n"
                        f"   📈 Профит: <b>+${opp.profit:.2f}</b> ({opp.profit_percent}%)\n"
                        f"   ⭐ Smart Score: {opp.smart_score}\n\n"
                    )

                message += (
                    f"\n💡 <i>Бот автоматически выберет лучшие предметы "
                    f"в рамках вашего баланса ${balance:.2f}</i>"
                )

                # Add action buttons
                keyboard = [
                    [
                        InlineKeyboardButton(
                            "🎯 Создать таргеты (Топ-5)",
                            callback_data="smart_create_targets",
                        )
                    ],
                    [
                        InlineKeyboardButton("🔄 Обновить", callback_data="start_smart_arbitrage"),
                        InlineKeyboardButton("⬅️ Назад", callback_data="simple_back"),
                    ],
                ]

                await query.edit_message_text(
                    message,
                    parse_mode=ParseMode.HTML,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                )
            else:
                await query.edit_message_text(
                    "😔 <b>Подходящих возможностей не найдено</b>\n\n"
                    f"При балансе ${balance:.2f} и лимитах:\n"
                    f"• Макс. цена: ${limits.max_buy_price:.2f}\n"
                    f"• Мин. профит: {limits.min_roi}%\n\n"
                    "Попробуйте позже — рынок постоянно меняется!",
                    parse_mode=ParseMode.HTML,
                    reply_markup=get_main_menu_keyboard(balance),
                )

        except Exception as e:
            logger.exception(f"Smart Arbitrage error: {e}")
            await query.edit_message_text(
                f"❌ Ошибка при запуске Smart Arbitrage.\nДетали: {str(e)[:100]}",
                reply_markup=get_main_menu_keyboard(),
            )

    return ConversationHandler.END


def get_simplified_conversation_handler() -> ConversationHandler:
    """Создать ConversationHandler для упрощенного меню.

    Returns:
        Настроенный ConversationHandler
    """
    return ConversationHandler(
        entry_points=[
            CommandHandler("simple", start_simple_menu),
            MessageHandler(filters.Regex("^🔍 Арбитраж$"), arbitrage_start),
            MessageHandler(filters.Regex("^🎯 Таргеты$"), targets_start),
            MessageHandler(filters.Regex("^💰 Баланс$"), balance_simple),
            MessageHandler(filters.Regex("^📊 Статистика$"), stats_simple),
            # Добавляем обработчик для кнопки паники в entry_points,
            # чтобы он работал даже если пользователь не в диалоге
            CallbackQueryHandler(stop_bot, pattern="^toggle_arb_off$"),
        ],
        states={
            CHOOSING_ARB_MODE: [
                CallbackQueryHandler(
                    arbitrage_all_games,
                    pattern=f"^{PREFIX_ARB}_all$",
                ),
                CallbackQueryHandler(
                    arbitrage_manual_mode,
                    pattern=f"^{PREFIX_ARB}_manual$",
                ),
                CallbackQueryHandler(
                    back_to_main,
                    pattern=f"^{PREFIX_ARB}_back$",
                ),
            ],
            SELECTING_GAME_MANUAL: [
                CallbackQueryHandler(
                    arbitrage_select_game,
                    pattern=f"^{PREFIX_ARB}_game_",
                ),
                CallbackQueryHandler(
                    arbitrage_start,
                    pattern=f"^{PREFIX_ARB}_back$",
                ),
            ],
            WAITING_FOR_RANGE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    arbitrage_process_range,
                ),
            ],
            CHOOSING_TARGET_MODE: [
                CallbackQueryHandler(
                    targets_manual,
                    pattern=f"^{PREFIX_TARGET}_manual$",
                ),
                CallbackQueryHandler(
                    targets_auto,
                    pattern=f"^{PREFIX_TARGET}_auto$",
                ),
                CallbackQueryHandler(
                    targets_list,
                    pattern=f"^{PREFIX_TARGET}_list$",
                ),
                CallbackQueryHandler(
                    back_to_main,
                    pattern=f"^{PREFIX_SIMPLE}_back$",
                ),
            ],
            WAITING_FOR_TARGET_NAME: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    targets_create,
                ),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CallbackQueryHandler(back_to_main, pattern=f"^{PREFIX_SIMPLE}_back$"),
            # Важно: разрешить повторный вход через кнопки меню
            MessageHandler(filters.Regex("^🔍 Арбитраж$"), arbitrage_start),
            MessageHandler(filters.Regex("^🎯 Таргеты$"), targets_start),
            MessageHandler(filters.Regex("^💰 Баланс$"), balance_simple),
            MessageHandler(filters.Regex("^📊 Статистика$"), stats_simple),
        ],
        name="simplified_menu",
        persistent=False,
        per_message=False,
        allow_reentry=True,
    )


# Регистрация дополнительных callback handlers
def register_simplified_callbacks(application) -> None:
    """Зарегистрировать callback handlers для упрощенного меню.

    Args:
        application: Application instance
    """
    # Регистрируем callback для быстрых диапазонов цен
    # Эти callbacks работают НЕЗАВИСИМО от ConversationHandler
    application.add_handler(
        CallbackQueryHandler(
            arbitrage_quick_range,
            pattern="^simple_arb_quick_",
        ),
        group=1,  # Группа выше, чем ConversationHandler
    )

    # Smart Arbitrage callback
    application.add_handler(
        CallbackQueryHandler(
            start_smart_arbitrage,
            pattern="^start_smart_arbitrage$",
        ),
        group=1,
    )

    # Panic stop callback
    application.add_handler(
        CallbackQueryHandler(
            stop_bot,
            pattern="^panic_stop_all$",
        ),
        group=1,
    )

    # Stats by games callback
    application.add_handler(
        CallbackQueryHandler(
            stats_by_games_handler,
            pattern="^stats_by_games$",
        ),
        group=1,
    )

    # Whitelist/Blacklist management
    application.add_handler(
        CallbackQueryHandler(
            manage_whitelist_handler,
            pattern="^manage_whitelist$",
        ),
        group=1,
    )

    application.add_handler(
        CallbackQueryHandler(
            manage_blacklist_handler,
            pattern="^manage_blacklist$",
        ),
        group=1,
    )

    # Toggle repricing
    application.add_handler(
        CallbackQueryHandler(
            toggle_repricing_handler,
            pattern="^toggle_repricing$",
        ),
        group=1,
    )

    # Clear cache
    application.add_handler(
        CallbackQueryHandler(
            clear_cache_handler,
            pattern="^clear_steam_cache$",
        ),
        group=1,
    )

    logger.info("✅ Simplified menu callbacks registered (including quick ranges)")
