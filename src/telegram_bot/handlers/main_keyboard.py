"""Главная клавиатура бота - упрощённая версия.

Содержит только необходимые кнопки:
- 🤖 Авто-торговля (поиск арбитража, покупка, продажа)
- 🎯 Таргеты (создание и управление buy orders)
- Управление (WhiteList, BlackList, Репрайсинг, Настройки)
- 🛑 Экстренная остановка

Автор: DMarket Bot Team
Дата: 2026-01-04
"""

import os
from typing import Any

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes

from src.utils.logging_utils import get_logger


logger = get_logger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# ГЛАВНАЯ КЛАВИАТУРА
# ═══════════════════════════════════════════════════════════════════════════


def get_main_keyboard(balance: float | None = None) -> InlineKeyboardMarkup:
    """Создать главное меню бота.

    Args:
        balance: Текущий баланс для отображения

    Returns:
        InlineKeyboardMarkup с главным меню
    """
    balance_text = f"💰 ${balance:.2f}" if balance else "💰 Баланс"

    keyboard = [
        # ═══════════ ГЛАВНЫЕ ФУНКЦИИ ═══════════
        [InlineKeyboardButton("🤖 АВТО-ТОРГОВЛЯ", callback_data="auto_trade_start")],
        [InlineKeyboardButton("🎯 ТАРГЕТЫ", callback_data="targets_menu")],
        # ═══════════ ИНФОРМАЦИЯ ═══════════
        [
            InlineKeyboardButton(balance_text, callback_data="show_balance"),
            InlineKeyboardButton("📦 Инвентарь", callback_data="show_inventory"),
        ],
        # ═══════════ УПРАВЛЕНИЕ ═══════════
        [
            InlineKeyboardButton("✅ WhiteList", callback_data="whitelist_menu"),
            InlineKeyboardButton("🚫 BlackList", callback_data="blacklist_menu"),
        ],
        [
            InlineKeyboardButton("♻️ Репрайсинг", callback_data="repricing_toggle"),
            InlineKeyboardButton("⚙️ Настройки", callback_data="settings_menu"),
        ],
        # ═══════════ ЭКСТРЕННАЯ ОСТАНОВКА ═══════════
        [InlineKeyboardButton("🛑 ЭКСТРЕННАЯ ОСТАНОВКА", callback_data="emergency_stop")],
    ]
    return InlineKeyboardMarkup(keyboard)


# ═══════════════════════════════════════════════════════════════════════════
# КОМАНДА /start И ГЛАВНОЕ МЕНЮ
# ═══════════════════════════════════════════════════════════════════════════


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start - показать главное меню."""
    user = update.effective_user
    logger.info(f"User {user.id} started bot")

    # Получаем баланс если есть API
    balance = None
    try:
        dmarket_api = _get_dmarket_api(context)
        if dmarket_api:
            balance_data = await dmarket_api.get_balance()
            # API может вернуть dict или уже число
            if isinstance(balance_data, dict):
                raw_usd = balance_data.get("usd", "0")
                balance = float(raw_usd) / 100
            else:
                balance = float(balance_data) / 100
    except (ValueError, TypeError, AttributeError) as e:
        logger.warning(f"Failed to parse balance: {e}")
    except Exception as e:
        logger.warning(f"Failed to get balance: {e}")

    welcome_text = (
        f"👋 <b>Привет, {user.first_name}!</b>\n\n"
        f"🤖 <b>DMarket Trading Bot</b>\n\n"
        f"Выберите действие:\n\n"
        f"• <b>Авто-торговля</b> — автоматический поиск арбитража,\n"
        f"  покупка выгодных предметов и продажа с прибылью\n\n"
        f"• <b>Таргеты</b> — создание заявок на покупку (Buy Orders)\n"
        f"  по указанной цене\n"
    )

    await update.message.reply_text(
        welcome_text,
        parse_mode=ParseMode.HTML,
        reply_markup=get_main_keyboard(balance),
    )


async def main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Вернуться в главное меню."""
    query = update.callback_query
    await query.answer()

    # Получаем баланс
    balance = None
    try:
        dmarket_api = _get_dmarket_api(context)
        if dmarket_api:
            balance_data = await dmarket_api.get_balance()
            if isinstance(balance_data, dict):
                balance = float(balance_data.get("usd", "0")) / 100
            else:
                balance = float(balance_data) / 100 if balance_data else 0.0
    except Exception:
        pass

    await query.edit_message_text(
        "👋 <b>Главное меню</b>\n\nВыберите действие:",
        parse_mode=ParseMode.HTML,
        reply_markup=get_main_keyboard(balance),
    )


# ═══════════════════════════════════════════════════════════════════════════
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ═══════════════════════════════════════════════════════════════════════════


def _get_dmarket_api(context: ContextTypes.DEFAULT_TYPE):
    """Получить DMarket API клиент из context."""
    return getattr(context.application, "dmarket_api", None)


def _get_auto_buyer(context: ContextTypes.DEFAULT_TYPE):
    """Получить AutoBuyer из context."""
    return getattr(context.application, "auto_buyer", None)


def _get_orchestrator(context: ContextTypes.DEFAULT_TYPE):
    """Получить Orchestrator из context."""
    return getattr(context.application, "orchestrator", None)


# ═══════════════════════════════════════════════════════════════════════════
# АВТО-ТОРГОВЛЯ
# ═══════════════════════════════════════════════════════════════════════════


async def auto_trade_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Запустить/остановить авто-торговлю.

    Авто-торговля включает:
    - Сканирование рынка DMarket
    - Поиск арбитражных возможностей
    - Автоматическая покупка выгодных предметов
    - Автоматическая продажа с наценкой
    - Редкие предметы остаются в инвентаре
    """
    query = update.callback_query
    await query.answer()

    # Проверяем статус авто-торговли
    is_running = context.bot_data.get("auto_trade_running", False)
    _auto_buyer = _get_auto_buyer(context)  # Reserved for future status display
    _orchestrator = _get_orchestrator(context)  # Reserved for future status display

    if is_running:
        # Показать меню управления
        keyboard = [
            [InlineKeyboardButton("🛑 Остановить торговлю", callback_data="auto_trade_stop")],
            [InlineKeyboardButton("📊 Статус", callback_data="auto_trade_status")],
            [InlineKeyboardButton("⚙️ Настройки", callback_data="auto_trade_settings")],
            [InlineKeyboardButton("◀️ Главное меню", callback_data="main_menu")],
        ]

        await query.edit_message_text(
            "🤖 <b>АВТО-ТОРГОВЛЯ</b>\n\n"
            "🟢 <b>Статус: РАБОТАЕТ</b>\n\n"
            "Бот автоматически:\n"
            "• 🔍 Сканирует рынок DMarket\n"
            "• 🛒 Покупает выгодные предметы\n"
            "• 💸 Продаёт с наценкой\n"
            "• 💎 Редкие предметы сохраняет\n",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
    else:
        # Показать меню запуска
        dry_run = os.getenv("DRY_RUN", "true").lower() == "true"
        mode = "🔒 ТЕСТОВЫЙ РЕЖИМ" if dry_run else "⚠️ РЕАЛЬНЫЕ СДЕЛКИ"

        keyboard = [
            [InlineKeyboardButton("🚀 ЗАПУСТИТЬ", callback_data="auto_trade_run")],
            [InlineKeyboardButton("⚙️ Настройки", callback_data="auto_trade_settings")],
            [InlineKeyboardButton("◀️ Главное меню", callback_data="main_menu")],
        ]

        await query.edit_message_text(
            f"🤖 <b>АВТО-ТОРГОВЛЯ</b>\n\n"
            f"🔴 <b>Статус: ОСТАНОВЛЕНА</b>\n\n"
            f"Режим: {mode}\n\n"
            f"<b>Что делает авто-торговля:</b>\n"
            f"• 🔍 Сканирует все игры (CS2, Dota 2, TF2, Rust)\n"
            f"• 📊 Ищет предметы с высоким ROI (>10%)\n"
            f"• 🛒 Автоматически покупает выгодные\n"
            f"• 💸 Выставляет на продажу с наценкой\n"
            f"• 💎 Редкие предметы оставляет в инвентаре\n\n"
            f"<i>Нажмите ЗАПУСТИТЬ для старта</i>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )


async def auto_trade_run(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Запустить авто-торговлю."""
    query = update.callback_query
    await query.answer("Запускаю авто-торговлю...")

    await query.edit_message_text(
        "🤖 <b>АВТО-ТОРГОВЛЯ</b>\n\n⏳ <b>Запуск...</b>\n\nИнициализация сканера рынка...",
        parse_mode=ParseMode.HTML,
    )

    try:
        # Получаем компоненты
        dmarket_api = _get_dmarket_api(context)
        auto_buyer = _get_auto_buyer(context)
        orchestrator = _get_orchestrator(context)

        if not dmarket_api:
            await query.edit_message_text(
                "❌ <b>Ошибка</b>\n\nAPI клиент не инициализирован.\nПерезапустите бота.",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("◀️ Назад", callback_data="auto_trade_start")]
                ]),
            )
            return

        # Включаем auto_buyer
        if auto_buyer:
            auto_buyer.config.enabled = True
            logger.info("Auto-buyer enabled")

        # Запускаем orchestrator если есть
        if orchestrator:
            await orchestrator.start()
            logger.info("Orchestrator started")

        # Отмечаем что торговля запущена
        context.bot_data["auto_trade_running"] = True

        # Получаем баланс (безопасно)
        balance_data = await dmarket_api.get_balance()
        if isinstance(balance_data, dict):
            raw_usd = balance_data.get("usd", "0")
            balance = float(raw_usd) / 100
        else:
            balance = float(balance_data) / 100 if balance_data else 0.0

        keyboard = [
            [InlineKeyboardButton("🛑 Остановить", callback_data="auto_trade_stop")],
            [InlineKeyboardButton("📊 Статус", callback_data="auto_trade_status")],
            [InlineKeyboardButton("◀️ Главное меню", callback_data="main_menu")],
        ]

        await query.edit_message_text(
            f"🤖 <b>АВТО-ТОРГОВЛЯ ЗАПУЩЕНА!</b>\n\n"
            f"🟢 <b>Статус: РАБОТАЕТ</b>\n\n"
            f"💰 Баланс: <b>${balance:.2f}</b>\n\n"
            f"💎 Режим: Арбитраж + Rare Hold\n"
            f"(редкие предметы остаются в инвентаре)\n\n"
            f"Бот сканирует рынок и ищет выгодные сделки.\n\n"
            f"<i>Для остановки нажмите кнопку ниже</i>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

        logger.info(f"Auto-trade started, balance: ${balance:.2f}")

    except Exception as e:
        logger.exception(f"Failed to start auto-trade: {e}")
        await query.edit_message_text(
            f"❌ <b>Ошибка запуска</b>\n\n{str(e)[:200]}",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Повторить", callback_data="auto_trade_run")],
                [InlineKeyboardButton("◀️ Назад", callback_data="auto_trade_start")],
            ]),
        )


async def auto_trade_stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Остановить авто-торговлю."""
    query = update.callback_query
    await query.answer("Останавливаю...")

    try:
        # Выключаем компоненты
        auto_buyer = _get_auto_buyer(context)
        orchestrator = _get_orchestrator(context)

        if auto_buyer:
            auto_buyer.config.enabled = False

        if orchestrator:
            await orchestrator.stop()

        context.bot_data["auto_trade_running"] = False

        keyboard = [
            [InlineKeyboardButton("🚀 Запустить снова", callback_data="auto_trade_run")],
            [InlineKeyboardButton("◀️ Главное меню", callback_data="main_menu")],
        ]

        await query.edit_message_text(
            "🤖 <b>АВТО-ТОРГОВЛЯ</b>\n\n"
            "🔴 <b>Статус: ОСТАНОВЛЕНА</b>\n\n"
            "Все процессы остановлены.\n"
            "Предметы в инвентаре сохранены.",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

        logger.info("Auto-trade stopped")

    except Exception as e:
        logger.exception(f"Failed to stop auto-trade: {e}")


async def auto_trade_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать статус авто-торговли."""
    query = update.callback_query
    await query.answer()

    try:
        dmarket_api = _get_dmarket_api(context)
        auto_buyer = _get_auto_buyer(context)

        # Баланс (безопасная распаковка)
        balance = 0.0
        if dmarket_api:
            balance_data = await dmarket_api.get_balance()
            if isinstance(balance_data, dict):
                balance = float(balance_data.get("usd", "0")) / 100
            else:
                balance = float(balance_data) / 100 if balance_data else 0.0

        # Статистика покупок
        stats = {"total_purchases": 0, "successful": 0, "total_spent_usd": 0}
        if auto_buyer:
            stats = auto_buyer.get_purchase_stats()

        is_running = context.bot_data.get("auto_trade_running", False)
        status = "🟢 РАБОТАЕТ" if is_running else "🔴 ОСТАНОВЛЕНА"

        keyboard = [
            [InlineKeyboardButton("🔄 Обновить", callback_data="auto_trade_status")],
            [InlineKeyboardButton("◀️ Назад", callback_data="auto_trade_start")],
        ]

        await query.edit_message_text(
            f"📊 <b>СТАТУС АВТО-ТОРГОВЛИ</b>\n\n"
            f"Статус: {status}\n\n"
            f"<b>Баланс:</b>\n"
            f"💰 ${balance:.2f}\n\n"
            f"<b>Статистика сессии:</b>\n"
            f"• Покупок: {stats['total_purchases']}\n"
            f"• Успешных: {stats['successful']}\n"
            f"• Потрачено: ${stats['total_spent_usd']:.2f}",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    except Exception as e:
        logger.exception(f"Status error: {e}")


async def auto_trade_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать настройки авто-торговли."""
    query = update.callback_query
    await query.answer()

    auto_buyer = _get_auto_buyer(context)

    min_discount = 10.0
    max_price = 50.0
    dry_run = True

    if auto_buyer:
        min_discount = auto_buyer.config.min_discount_percent
        max_price = auto_buyer.config.max_price_usd
        dry_run = auto_buyer.config.dry_run

    mode = "🔒 ТЕСТ" if dry_run else "⚠️ РЕАЛ"

    keyboard = [
        [
            InlineKeyboardButton(
                f"Мин. скидка: {min_discount}%", callback_data="setting_min_discount"
            )
        ],
        [InlineKeyboardButton(f"Макс. цена: ${max_price}", callback_data="setting_max_price")],
        [InlineKeyboardButton(f"Режим: {mode}", callback_data="setting_dry_run")],
        [InlineKeyboardButton("◀️ Назад", callback_data="auto_trade_start")],
    ]

    await query.edit_message_text(
        "⚙️ <b>НАСТРОЙКИ АВТО-ТОРГОВЛИ</b>\n\n"
        f"• Мин. скидка: <b>{min_discount}%</b>\n"
        f"• Макс. цена предмета: <b>${max_price}</b>\n"
        f"• Режим: <b>{mode}</b>\n\n"
        "<i>Нажмите на параметр для изменения</i>",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# ═══════════════════════════════════════════════════════════════════════════
# ТАРГЕТЫ
# ═══════════════════════════════════════════════════════════════════════════


async def targets_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать меню таргетов."""
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("➕ Создать таргет", callback_data="target_create")],
        [InlineKeyboardButton("🤖 Авто-таргеты", callback_data="target_auto")],
        [InlineKeyboardButton("📋 Мои таргеты", callback_data="target_list")],
        [InlineKeyboardButton("◀️ Главное меню", callback_data="main_menu")],
    ]

    await query.edit_message_text(
        "🎯 <b>ТАРГЕТЫ (Buy Orders)</b>\n\n"
        "<b>Что такое таргеты?</b>\n"
        "Таргет — это заявка на покупку предмета по указанной цене.\n"
        "Когда кто-то выставит предмет по вашей цене — он будет куплен автоматически.\n\n"
        "<b>Режимы:</b>\n"
        "• <b>Ручной</b> — вы указываете предмет и цену\n"
        "• <b>Авто</b> — бот сам находит выгодные таргеты\n\n"
        "Выберите действие:",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def target_create(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Начать создание таргета."""
    query = update.callback_query
    await query.answer()

    keyboard = [
        [
            InlineKeyboardButton("🔫 CS2", callback_data="target_game_csgo"),
            InlineKeyboardButton("🏠 Rust", callback_data="target_game_rust"),
        ],
        [
            InlineKeyboardButton("⚔️ Dota 2", callback_data="target_game_dota2"),
            InlineKeyboardButton("🎩 TF2", callback_data="target_game_tf2"),
        ],
        [InlineKeyboardButton("◀️ Назад", callback_data="targets_menu")],
    ]

    await query.edit_message_text(
        "➕ <b>СОЗДАНИЕ ТАРГЕТА</b>\n\nШаг 1: Выберите игру:",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def target_auto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Создать авто-таргеты на основе анализа рынка."""
    query = update.callback_query
    await query.answer("Анализирую рынок...")

    await query.edit_message_text(
        "🤖 <b>АВТО-ТАРГЕТЫ</b>\n\n⏳ Анализирую рынок и подбираю выгодные позиции...",
        parse_mode=ParseMode.HTML,
    )

    try:
        dmarket_api = _get_dmarket_api(context)
        if not dmarket_api:
            raise ValueError("API не инициализирован")

        from src.dmarket.targets import TargetManager

        target_manager = TargetManager(api_client=dmarket_api)

        # Получаем рыночные предметы
        market_items = await dmarket_api.get_market_items(
            game="csgo",
            limit=20,
            order_by="best_deals",
        )

        items = market_items.get("objects", [])
        if not items:
            raise ValueError("Не найдено предметов для таргетов")

        # Создаём умные таргеты
        result = await target_manager.create_smart_targets(
            game="csgo",
            items=items[:5],
            profit_margin=0.15,
            max_targets=5,
        )

        created = result.get("created", [])

        keyboard = [
            [InlineKeyboardButton("📋 Посмотреть таргеты", callback_data="target_list")],
            [InlineKeyboardButton("🔄 Создать ещё", callback_data="target_auto")],
            [InlineKeyboardButton("◀️ Назад", callback_data="targets_menu")],
        ]

        if created:
            await query.edit_message_text(
                f"✅ <b>АВТО-ТАРГЕТЫ СОЗДАНЫ!</b>\n\n"
                f"Создано таргетов: <b>{len(created)}</b>\n\n"
                f"Бот будет отслеживать эти предметы и купит\n"
                f"автоматически когда цена достигнет указанной.",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        else:
            await query.edit_message_text(
                "😔 <b>Не удалось создать таргеты</b>\n\n"
                "Подходящих предметов не найдено.\nПопробуйте позже.",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(keyboard),
            )

    except Exception as e:
        logger.exception(f"Auto-target error: {e}")
        await query.edit_message_text(
            f"❌ <b>Ошибка</b>\n\n{str(e)[:150]}",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Назад", callback_data="targets_menu")]
            ]),
        )


async def target_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать список активных таргетов."""
    query = update.callback_query
    await query.answer()

    try:
        dmarket_api = _get_dmarket_api(context)
        if not dmarket_api:
            raise ValueError("API не инициализирован")

        from src.dmarket.targets import TargetManager

        target_manager = TargetManager(api_client=dmarket_api)

        # Получаем таргеты для всех игр
        all_targets = []
        for game in ["csgo", "dota2", "tf2", "rust"]:
            try:
                response = await target_manager.get_user_targets(game=game)
                targets = response.get("Items", [])
                for t in targets:
                    t["game"] = game
                all_targets.extend(targets)
            except Exception as e:
                logger.debug(f"Failed to get targets for {game}: {e}")
                continue

        keyboard = [
            [InlineKeyboardButton("➕ Создать", callback_data="target_create")],
            [InlineKeyboardButton("🤖 Авто-таргеты", callback_data="target_auto")],
            [InlineKeyboardButton("◀️ Назад", callback_data="targets_menu")],
        ]

        if not all_targets:
            await query.edit_message_text(
                "📋 <b>МОИ ТАРГЕТЫ</b>\n\n"
                "У вас пока нет активных таргетов.\n\n"
                "Создайте первый таргет!",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        else:
            game_emoji = {"csgo": "🔫", "dota2": "⚔️", "tf2": "🎩", "rust": "🏠"}
            message = f"📋 <b>МОИ ТАРГЕТЫ ({len(all_targets)})</b>\n\n"

            for i, target in enumerate(all_targets[:10], 1):
                title = target.get("title", "?")[:25]
                price = target.get("price", 0) / 100
                game = target.get("game", "csgo")
                emoji = game_emoji.get(game, "🎮")
                message += f"{i}. {emoji} <b>{title}</b> — ${price:.2f}\n"

            if len(all_targets) > 10:
                message += f"\n<i>...и ещё {len(all_targets) - 10}</i>"

            await query.edit_message_text(
                message,
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(keyboard),
            )

    except Exception as e:
        logger.exception(f"Target list error: {e}")
        await query.edit_message_text(
            f"❌ Ошибка: {str(e)[:100]}",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Назад", callback_data="targets_menu")]
            ]),
        )


# ═══════════════════════════════════════════════════════════════════════════
# УПРАВЛЕНИЕ (WhiteList, BlackList, Репрайсинг, Настройки)
# ═══════════════════════════════════════════════════════════════════════════


async def whitelist_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать WhiteList."""
    query = update.callback_query
    await query.answer()

    try:
        from src.dmarket.whitelist_config import WhitelistConfig

        config = WhitelistConfig()
        items = config.whitelist[:15]

        message = f"✅ <b>WHITE LIST ({len(config.whitelist)} предметов)</b>\n\n"
        for i, item in enumerate(items, 1):
            message += f"{i}. {item}\n"

        if len(config.whitelist) > 15:
            message += f"\n<i>...и ещё {len(config.whitelist) - 15}</i>"

        message += "\n\n<i>Редактировать: data/whitelist.json</i>"

    except Exception as e:
        message = f"❌ Ошибка загрузки: {e}"

    keyboard = [
        [InlineKeyboardButton("🔄 Обновить", callback_data="whitelist_menu")],
        [InlineKeyboardButton("◀️ Главное меню", callback_data="main_menu")],
    ]

    await query.edit_message_text(
        message,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def blacklist_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать BlackList."""
    query = update.callback_query
    await query.answer()

    try:
        from src.dmarket.blacklist_manager import BlacklistManager

        manager = BlacklistManager()
        items = manager.blacklisted_items[:15]

        message = f"🚫 <b>BLACK LIST ({len(manager.blacklisted_items)} слов)</b>\n\n"
        for i, item in enumerate(items, 1):
            message += f"{i}. {item}\n"

        if len(manager.blacklisted_items) > 15:
            message += f"\n<i>...и ещё {len(manager.blacklisted_items) - 15}</i>"

        message += f"\n\n🔒 Продавцов в бане: {len(manager.blacklisted_sellers)}"
        message += "\n\n<i>Редактировать: data/blacklist.json</i>"

    except Exception as e:
        message = f"❌ Ошибка загрузки: {e}"

    keyboard = [
        [InlineKeyboardButton("🔄 Обновить", callback_data="blacklist_menu")],
        [InlineKeyboardButton("◀️ Главное меню", callback_data="main_menu")],
    ]

    await query.edit_message_text(
        message,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def repricing_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Включить/выключить репрайсинг."""
    query = update.callback_query
    await query.answer()

    current = context.bot_data.get("repricing_enabled", True)
    new_state = not current
    context.bot_data["repricing_enabled"] = new_state

    status = "✅ ВКЛЮЧЕН" if new_state else "❌ ВЫКЛЮЧЕН"

    keyboard = [
        [
            InlineKeyboardButton(
                f"{'🔴 Выключить' if new_state else '🟢 Включить'}",
                callback_data="repricing_toggle",
            )
        ],
        [InlineKeyboardButton("◀️ Главное меню", callback_data="main_menu")],
    ]

    await query.edit_message_text(
        f"♻️ <b>АВТО-РЕПРАЙСИНГ</b>\n\n"
        f"Статус: {status}\n\n"
        f"<b>Как работает:</b>\n"
        f"• После 24ч — снижение до 5% прибыли\n"
        f"• После 48ч — продажа по себестоимости\n"
        f"• После 72ч — ликвидация",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать настройки бота."""
    query = update.callback_query
    await query.answer()

    dry_run = os.getenv("DRY_RUN", "true").lower() == "true"
    mode = "🔒 ТЕСТОВЫЙ" if dry_run else "⚠️ РЕАЛЬНЫЙ"

    keyboard = [
        [InlineKeyboardButton("⚙️ Авто-торговля", callback_data="auto_trade_settings")],
        [InlineKeyboardButton("📊 Статус системы", callback_data="system_status")],
        [InlineKeyboardButton("◀️ Главное меню", callback_data="main_menu")],
    ]

    await query.edit_message_text(
        f"⚙️ <b>НАСТРОЙКИ</b>\n\n"
        f"Режим работы: <b>{mode}</b>\n\n"
        f"<i>Основные настройки находятся в файле .env</i>",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# ═══════════════════════════════════════════════════════════════════════════
# ИНФОРМАЦИЯ (Баланс, Инвентарь)
# ═══════════════════════════════════════════════════════════════════════════


async def show_balance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать баланс."""
    query = update.callback_query
    await query.answer()

    try:
        dmarket_api = _get_dmarket_api(context)
        if not dmarket_api:
            raise ValueError("API не инициализирован")

        balance_data = await dmarket_api.get_balance()

        # Безопасная распаковка баланса
        if isinstance(balance_data, dict):
            usd = float(balance_data.get("usd", "0")) / 100
            dmc = float(balance_data.get("dmc", "0")) / 100
        else:
            usd = 0.0
            dmc = 0.0

        message = f"💰 <b>ВАШ БАЛАНС</b>\n\n💵 USD: <b>${usd:.2f}</b>\n💎 DMC: <b>{dmc:.2f}</b>"

    except Exception as e:
        message = f"❌ Ошибка: {e}"

    keyboard = [
        [InlineKeyboardButton("🔄 Обновить", callback_data="show_balance")],
        [InlineKeyboardButton("◀️ Главное меню", callback_data="main_menu")],
    ]

    await query.edit_message_text(
        message,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def show_inventory(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать инвентарь."""
    query = update.callback_query
    await query.answer()

    try:
        dmarket_api = _get_dmarket_api(context)
        if not dmarket_api:
            raise ValueError("API не инициализирован")

        # Получаем инвентарь
        inventory = await dmarket_api.get_user_inventory(game="csgo", limit=20)
        items = inventory.get("objects", [])

        if not items:
            message = "📦 <b>ИНВЕНТАРЬ</b>\n\nВаш инвентарь пуст."
        else:
            total_value = sum(float(i.get("price", {}).get("USD", 0)) / 100 for i in items)
            message = f"📦 <b>ИНВЕНТАРЬ ({len(items)} предметов)</b>\n\n"
            message += f"💰 Общая стоимость: <b>${total_value:.2f}</b>\n\n"

            for i, item in enumerate(items[:10], 1):
                title = item.get("title", "?")[:25]
                price = float(item.get("price", {}).get("USD", 0)) / 100
                message += f"{i}. {title} — ${price:.2f}\n"

            if len(items) > 10:
                message += f"\n<i>...и ещё {len(items) - 10}</i>"

    except Exception as e:
        message = f"❌ Ошибка: {e}"

    keyboard = [
        [InlineKeyboardButton("🔄 Обновить", callback_data="show_inventory")],
        [InlineKeyboardButton("◀️ Главное меню", callback_data="main_menu")],
    ]

    await query.edit_message_text(
        message,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# ═══════════════════════════════════════════════════════════════════════════
# ЭКСТРЕННАЯ ОСТАНОВКА
# ═══════════════════════════════════════════════════════════════════════════


async def _delete_all_targets(dmarket_api: Any) -> int:
    """Delete all active targets across all games.

    Returns:
        Number of deleted targets.
    """
    deleted_count = 0
    for game in ["csgo", "dota2", "tf2", "rust"]:
        try:
            targets_response = await dmarket_api.get_user_targets(game=game)
            targets = targets_response.get("Items", [])
            target_ids = [
                target.get("TargetID") or target.get("targetId")
                for target in targets
                if target.get("TargetID") or target.get("targetId")
            ]
            if target_ids:
                await dmarket_api.delete_targets(target_ids=target_ids)
                deleted_count += len(target_ids)
        except Exception as e:
            logger.debug(f"Failed to delete targets for {game}: {e}")
            continue
    return deleted_count


async def emergency_stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Экстренная остановка всех процессов.

    Останавливает:
    - Авто-торговлю (auto_buyer, orchestrator)
    - Сканирование рынка
    - Репрайсинг
    - Опционально удаляет все активные таргеты
    """
    query = update.callback_query
    await query.answer("⚠️ ЭКСТРЕННАЯ ОСТАНОВКА!")

    results = []

    try:
        # 1. Останавливаем авто-покупку
        auto_buyer = _get_auto_buyer(context)
        if auto_buyer:
            auto_buyer.config.enabled = False
            results.append("✅ Авто-покупка: ВЫКЛ")

        # 2. Останавливаем оркестратор
        orchestrator = _get_orchestrator(context)
        if orchestrator:
            if hasattr(orchestrator, "stop"):
                await orchestrator.stop()
            results.append("✅ Оркестратор: ВЫКЛ")

        # 3. Останавливаем сканер (если есть)
        scanner = context.bot_data.get("scanner_manager")
        if scanner and hasattr(scanner, "stop"):
            await scanner.stop()
            results.append("✅ Сканер: ВЫКЛ")

        # 4. Выключаем флаги
        context.bot_data["auto_trade_running"] = False
        context.bot_data["repricing_enabled"] = False

        # 5. Опционально: удаляем все активные таргеты (refactored to reduce nesting)
        dmarket_api = _get_dmarket_api(context)
        if dmarket_api:
            try:
                deleted_count = await _delete_all_targets(dmarket_api)
                if deleted_count > 0:
                    results.append(f"✅ Удалено таргетов: {deleted_count}")
            except Exception as e:
                logger.warning(f"Failed to delete targets: {e}")

        logger.warning("EMERGENCY STOP triggered by user")

        keyboard = [
            [InlineKeyboardButton("◀️ Главное меню", callback_data="main_menu")],
        ]

        status_text = "🛑 <b>ЭКСТРЕННАЯ ОСТАНОВКА</b>\n\n" + "\n".join(results)
        status_text += "\n\n💾 Предметы в инвентаре сохранены."

        await query.edit_message_text(
            status_text,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    except Exception as e:
        logger.exception(f"Emergency stop error: {e}")
        await query.edit_message_text(
            f"⚠️ Остановка выполнена частично: {e}",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Главное меню", callback_data="main_menu")]
            ]),
        )


# ═══════════════════════════════════════════════════════════════════════════
# РЕГИСТРАЦИЯ ОБРАБОТЧИКОВ
# ═══════════════════════════════════════════════════════════════════════════


def register_main_keyboard_handlers(application) -> None:
    """Зарегистрировать все обработчики главной клавиатуры.

    Args:
        application: Telegram Application instance
    """
    # Команда /start
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("menu", start_command))

    # Главное меню
    application.add_handler(CallbackQueryHandler(main_menu_callback, pattern="^main_menu$"))

    # Авто-торговля
    application.add_handler(CallbackQueryHandler(auto_trade_start, pattern="^auto_trade_start$"))
    application.add_handler(CallbackQueryHandler(auto_trade_run, pattern="^auto_trade_run$"))
    application.add_handler(CallbackQueryHandler(auto_trade_stop, pattern="^auto_trade_stop$"))
    application.add_handler(CallbackQueryHandler(auto_trade_status, pattern="^auto_trade_status$"))
    application.add_handler(
        CallbackQueryHandler(auto_trade_settings, pattern="^auto_trade_settings$")
    )

    # Таргеты
    application.add_handler(CallbackQueryHandler(targets_menu, pattern="^targets_menu$"))
    application.add_handler(CallbackQueryHandler(target_create, pattern="^target_create$"))
    application.add_handler(CallbackQueryHandler(target_auto, pattern="^target_auto$"))
    application.add_handler(CallbackQueryHandler(target_list, pattern="^target_list$"))

    # Управление
    application.add_handler(CallbackQueryHandler(whitelist_menu, pattern="^whitelist_menu$"))
    application.add_handler(CallbackQueryHandler(blacklist_menu, pattern="^blacklist_menu$"))
    application.add_handler(CallbackQueryHandler(repricing_toggle, pattern="^repricing_toggle$"))
    application.add_handler(CallbackQueryHandler(settings_menu, pattern="^settings_menu$"))

    # Информация
    application.add_handler(CallbackQueryHandler(show_balance, pattern="^show_balance$"))
    application.add_handler(CallbackQueryHandler(show_inventory, pattern="^show_inventory$"))

    # Экстренная остановка
    application.add_handler(CallbackQueryHandler(emergency_stop, pattern="^emergency_stop$"))

    logger.info("✅ Main keyboard handlers registered")
