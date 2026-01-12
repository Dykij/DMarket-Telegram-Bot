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
import pathlib
from pathlib import Path
from typing import Any

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes

from src.ai.price_predictor import PricePredictor
from src.dmarket.market_data_logger import MarketDataLogger
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
        [InlineKeyboardButton("🧠 ML/AI ОБУЧЕНИЕ", callback_data="ml_ai_menu")],
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
            # API returns balance in dollars directly in 'balance' field
            if isinstance(balance_data, dict):
                balance = float(balance_data.get("balance", 0))
            else:
                balance = float(balance_data) if balance_data else 0.0
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
                # DMarket API returns 'balance' field in dollars directly
                balance = float(balance_data.get("balance", 0))
            else:
                balance = float(balance_data) if balance_data else 0.0
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
            [
                InlineKeyboardButton(
                    "🔎 СКАНИРОВАТЬ ВСЕ СТРАТЕГИИ", callback_data="auto_trade_scan_all"
                )
            ],
            [InlineKeyboardButton("⚙️ Настройки", callback_data="auto_trade_settings")],
            [InlineKeyboardButton("◀️ Главное меню", callback_data="main_menu")],
        ]

        await query.edit_message_text(
            f"🤖 <b>АВТО-АРБИТРАЖ</b>\n\n"
            f"🔴 <b>Статус: ОСТАНОВЛЕНА</b>\n\n"
            f"Режим: {mode}\n\n"
            f"<b>Доступные стратегии поиска:</b>\n"
            f"• 🔄 <b>Cross-Platform</b> — DMarket ↔ Waxpeer\n"
            f"• 📊 <b>Intramarket</b> — ценовые аномалии внутри DMarket\n"
            f"• 🎯 <b>Float Value</b> — премиальные флоаты\n"
            f"• 💎 <b>Pattern/Phase</b> — Blue Gem, Doppler\n"
            f"• 🧠 <b>Smart Finder</b> — AI-анализ рынка\n\n"
            f"<b>ЗАПУСТИТЬ</b> — включить авто-покупку\n"
            f"<b>СКАНИРОВАТЬ</b> — найти возможности без покупки\n\n"
            f"<i>Выберите действие:</i>",
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
            # API returns balance in dollars directly in 'balance' field
            balance = float(balance_data.get("balance", 0))
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


async def auto_trade_scan_all(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Сканировать всеми стратегиями ВСЕ 4 ИГРЫ на арбитражные возможности.

    Игры: CS:GO/CS2, Dota 2, TF2, Rust

    Применяет ВСЕ доступные стратегии:
    - Cross-Platform Arbitrage (DMarket → Waxpeer)
    - Intramarket Arbitrage (ценовые аномалии)
    - Float Value Arbitrage (премиальные флоаты) - для CS:GO
    - Smart Market Finder (AI-анализ)
    """
    query = update.callback_query
    await query.answer("Запускаю сканирование ВСЕХ ИГР...")

    await query.edit_message_text(
        "🔎 <b>СКАНИРОВАНИЕ ВСЕХ ИГР</b>\n\n"
        "⏳ <b>Инициализация...</b>\n\n"
        "<b>Игры:</b>\n"
        "• 🔫 CS:GO / CS2\n"
        "• ⚔️ Dota 2\n"
        "• 🎩 Team Fortress 2\n"
        "• 🏚️ Rust\n\n"
        "<b>Стратегии:</b>\n"
        "• 🔄 Cross-Platform Arbitrage\n"
        "• 📊 Intramarket Arbitrage\n"
        "• 🎯 Float Value Arbitrage\n"
        "• 🧠 Smart Market Finder\n\n"
        "<i>Это может занять 60-120 секунд...</i>",
        parse_mode=ParseMode.HTML,
    )

    try:
        dmarket_api = _get_dmarket_api(context)
        if not dmarket_api:
            await query.edit_message_text(
                "❌ <b>Ошибка</b>\n\nAPI клиент не инициализирован.\nПерезапустите бота.",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("◀️ Назад", callback_data="auto_trade_start")]
                ]),
            )
            return

        # Проверяем API
        balance_data = await dmarket_api.get_balance()
        if isinstance(balance_data, dict) and balance_data.get("error"):
            await query.edit_message_text(
                f"❌ <b>API Error</b>\n\n{balance_data.get('error_message', 'Unknown')}",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("◀️ Назад", callback_data="auto_trade_start")]
                ]),
            )
            return

        # Получаем баланс для отображения
        if isinstance(balance_data, dict):
            balance = float(balance_data.get("balance", 0))
        else:
            balance = float(balance_data) if balance_data else 0.0

        # Импортируем Unified Strategy System с поддержкой мульти-игр
        from src.dmarket.unified_strategy_system import (
            GAME_EMOJIS,
            GAME_NAMES,
            SUPPORTED_GAMES,
            create_strategy_manager,
            scan_all_games,
        )

        # Создаём менеджер стратегий
        waxpeer_api = getattr(context.application, "waxpeer_api", None)
        strategy_manager = create_strategy_manager(
            dmarket_api=dmarket_api,
            waxpeer_api=waxpeer_api,
        )

        await query.edit_message_text(
            "🔎 <b>СКАНИРОВАНИЕ ВСЕХ ИГР</b>\n\n"
            "⏳ <b>Сканирование рынков...</b>\n\n"
            f"💰 Баланс: <b>${balance:.2f}</b>\n"
            f"🎮 Игры: <b>4</b>\n"
            f"📊 Мин. прибыль: <b>5-8%</b>\n\n"
            "📡 Прогресс:\n"
            "• 🔫 CS:GO... ⏳\n"
            "• ⚔️ Dota 2... ⏳\n"
            "• 🎩 TF2... ⏳\n"
            "• 🏚️ Rust... ⏳\n\n"
            "<i>Анализирую данные...</i>",
            parse_mode=ParseMode.HTML,
        )

        # Сканируем ВСЕ 4 ИГРЫ
        game_results = await scan_all_games(
            strategy_manager=strategy_manager,
            base_preset="standard",
            games=SUPPORTED_GAMES,
            top_n_per_game=10,
        )

        # Подсчитываем общее количество
        total_opportunities = sum(len(opps) for opps in game_results.values())

        if total_opportunities == 0:
            await query.edit_message_text(
                "🔎 <b>РЕЗУЛЬТАТЫ СКАНИРОВАНИЯ</b>\n\n"
                "ℹ️ <b>Возможности не найдены</b>\n\n"
                f"💰 Баланс: ${balance:.2f}\n"
                f"🎮 Просканировано игр: {len(SUPPORTED_GAMES)}\n\n"
                "Причины:\n"
                "• Рынки сейчас стабильны\n"
                "• Нет достаточного спреда\n"
                "• Попробуйте позже\n\n"
                "<i>Рекомендация: повторите через 5-10 минут</i>",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Повторить", callback_data="auto_trade_scan_all")],
                    [InlineKeyboardButton("◀️ Назад", callback_data="auto_trade_start")],
                ]),
            )
            return

        # Формируем результат
        result_text = (
            f"🎯 <b>НАЙДЕНО {total_opportunities} ВОЗМОЖНОСТЕЙ!</b>\n\n"
            f"💰 Баланс: <b>${balance:.2f}</b>\n\n"
        )

        # Статистика по играм
        result_text += "<b>🎮 По играм:</b>\n"
        for game in SUPPORTED_GAMES:
            emoji = GAME_EMOJIS.get(game, "🎮")
            name = GAME_NAMES.get(game, game.upper())
            count = len(game_results.get(game, []))
            result_text += f"{emoji} {name}: <b>{count}</b> шт.\n"

        # Объединяем и сортируем все возможности
        all_opportunities = []
        for game, opps in game_results.items():
            all_opportunities.extend(opps)
        all_opportunities.sort(key=lambda x: x.score.total_score, reverse=True)

        result_text += "\n<b>🔥 ТОП-6 возможностей (все игры):</b>\n\n"

        # Показываем топ-6
        for i, opp in enumerate(all_opportunities[:6], 1):
            game_emoji = GAME_EMOJIS.get(opp.game, "🎮")
            profit_emoji = "🔥" if float(opp.profit_percent) >= 15 else "💰"
            risk_emoji = {
                "very_low": "🟢",
                "low": "🟡",
                "medium": "🟠",
                "high": "🔴",
                "very_high": "⚫",
            }.get(opp.risk_level.value, "⚪")

            title_short = opp.title[:25] + "..." if len(opp.title) > 25 else opp.title
            result_text += (
                f"<b>{i}.</b> {game_emoji} {title_short}\n"
                f"   💵 ${float(opp.buy_price):.2f} → ${float(opp.sell_price):.2f}\n"
                f"   {profit_emoji} <b>+{float(opp.profit_percent):.1f}%</b> | "
                f"{risk_emoji} Score: {opp.score.total_score:.0f}\n\n"
            )

        if len(all_opportunities) > 6:
            result_text += f"<i>...и ещё {len(all_opportunities) - 6} возможностей</i>\n\n"

        result_text += (
            "💡 <b>Рекомендация:</b>\nПредметы с Score > 70 и 🟢/🟡 риском — лучший выбор!"
        )

        keyboard = [
            [InlineKeyboardButton("🔄 Сканировать снова", callback_data="auto_trade_scan_all")],
            [
                InlineKeyboardButton("🔫 CS:GO", callback_data="scan_game_csgo"),
                InlineKeyboardButton("⚔️ Dota 2", callback_data="scan_game_dota2"),
            ],
            [
                InlineKeyboardButton("🎩 TF2", callback_data="scan_game_tf2"),
                InlineKeyboardButton("🏚️ Rust", callback_data="scan_game_rust"),
            ],
            [InlineKeyboardButton("🚀 Запустить авто-покупку", callback_data="auto_trade_run")],
            [InlineKeyboardButton("◀️ Назад", callback_data="auto_trade_start")],
        ]

        await query.edit_message_text(
            result_text,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

        logger.info(
            "all_games_scan_complete",
            total_opportunities=total_opportunities,
            by_game={k: len(v) for k, v in game_results.items()},
        )

    except ImportError as e:
        logger.warning(f"Strategy module not available: {e}")
        await query.edit_message_text(
            "⚠️ <b>Модуль стратегий недоступен</b>\n\n"
            f"Ошибка: {str(e)[:100]}\n\n"
            "Попробуйте использовать базовый сканер.",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Назад", callback_data="auto_trade_start")]
            ]),
        )

    except Exception as e:
        logger.exception(f"All games scan failed: {e}")
        await query.edit_message_text(
            f"❌ <b>Ошибка сканирования</b>\n\n{str(e)[:200]}\n\nПопробуйте повторить позже.",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Повторить", callback_data="auto_trade_scan_all")],
                [InlineKeyboardButton("◀️ Назад", callback_data="auto_trade_start")],
            ]),
        )


async def scan_single_game(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Сканировать конкретную игру на арбитражные возможности.

    Обрабатывает callback: scan_game_csgo, scan_game_dota2, scan_game_tf2, scan_game_rust
    """
    query = update.callback_query
    callback_data = query.data

    # Извлекаем игру из callback_data (scan_game_csgo -> csgo)
    game = callback_data.replace("scan_game_", "")

    # Импортируем здесь чтобы избежать циклических импортов
    from src.dmarket.unified_strategy_system import (
        GAME_EMOJIS,
        GAME_NAMES,
        create_strategy_manager,
        get_game_specific_config,
    )

    game_emoji = GAME_EMOJIS.get(game, "🎮")
    game_name = GAME_NAMES.get(game, game.upper())

    await query.answer(f"Сканирую {game_name}...")

    await query.edit_message_text(
        f"{game_emoji} <b>СКАНИРОВАНИЕ {game_name.upper()}</b>\n\n"
        "⏳ <b>Инициализация...</b>\n\n"
        "<b>Стратегии:</b>\n"
        "• 🔄 Cross-Platform Arbitrage\n"
        "• 📊 Intramarket Arbitrage\n"
        f"{'• 🎯 Float Value Arbitrage' if game == 'csgo' else ''}\n"
        "• 🧠 Smart Market Finder\n\n"
        "<i>Это может занять 20-40 секунд...</i>",
        parse_mode=ParseMode.HTML,
    )

    try:
        dmarket_api = _get_dmarket_api(context)
        if not dmarket_api:
            await query.edit_message_text(
                "❌ <b>Ошибка</b>\n\nAPI клиент не инициализирован.",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("◀️ Назад", callback_data="auto_trade_scan_all")]
                ]),
            )
            return

        # Получаем баланс
        balance_data = await dmarket_api.get_balance()
        # API returns balance in dollars directly in 'balance' field
        if isinstance(balance_data, dict):
            balance = float(balance_data.get("balance", 0))
        else:
            balance = float(balance_data) if balance_data else 0.0

        # Создаём менеджер стратегий
        waxpeer_api = getattr(context.application, "waxpeer_api", None)
        strategy_manager = create_strategy_manager(
            dmarket_api=dmarket_api,
            waxpeer_api=waxpeer_api,
        )

        # Получаем конфиг для конкретной игры
        config = get_game_specific_config(game, "standard")

        # Сканируем
        opportunities = await strategy_manager.find_best_opportunities_combined(
            config=config,
            top_n=15,
        )

        if not opportunities:
            await query.edit_message_text(
                f"{game_emoji} <b>РЕЗУЛЬТАТЫ - {game_name.upper()}</b>\n\n"
                "ℹ️ <b>Возможности не найдены</b>\n\n"
                f"💰 Баланс: ${balance:.2f}\n\n"
                "Причины:\n"
                f"• Рынок {game_name} сейчас стабилен\n"
                "• Нет достаточного спреда\n"
                "• Попробуйте позже\n",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Повторить", callback_data=f"scan_game_{game}")],
                    [InlineKeyboardButton("🔎 Все игры", callback_data="auto_trade_scan_all")],
                    [InlineKeyboardButton("◀️ Назад", callback_data="auto_trade_start")],
                ]),
            )
            return

        # Формируем результат
        result_text = (
            f"{game_emoji} <b>НАЙДЕНО {len(opportunities)} ВОЗМОЖНОСТЕЙ</b>\n"
            f"<i>{game_name}</i>\n\n"
            f"💰 Баланс: <b>${balance:.2f}</b>\n\n"
        )

        # Группируем по стратегиям
        by_strategy: dict[str, list] = {}
        for opp in opportunities:
            strategy_name = opp.strategy_type.value
            if strategy_name not in by_strategy:
                by_strategy[strategy_name] = []
            by_strategy[strategy_name].append(opp)

        result_text += "<b>📊 По стратегиям:</b>\n"
        strategy_emojis = {
            "cross_platform": "🔄",
            "intramarket": "📈",
            "float_value": "🎯",
            "smart_market": "🧠",
            "pattern_phase": "💎",
        }
        for strategy, opps in by_strategy.items():
            emoji = strategy_emojis.get(strategy, "📌")
            result_text += f"{emoji} {strategy}: <b>{len(opps)}</b>\n"

        result_text += "\n<b>🔥 ТОП-5 возможностей:</b>\n\n"

        for i, opp in enumerate(opportunities[:5], 1):
            profit_emoji = "🔥" if float(opp.profit_percent) >= 15 else "💰"
            risk_emoji = {
                "very_low": "🟢",
                "low": "🟡",
                "medium": "🟠",
                "high": "🔴",
                "very_high": "⚫",
            }.get(opp.risk_level.value, "⚪")

            title_short = opp.title[:25] + "..." if len(opp.title) > 25 else opp.title
            result_text += (
                f"<b>{i}.</b> {title_short}\n"
                f"   💵 ${float(opp.buy_price):.2f} → ${float(opp.sell_price):.2f}\n"
                f"   {profit_emoji} <b>+{float(opp.profit_percent):.1f}%</b> | "
                f"{risk_emoji} Score: {opp.score.total_score:.0f}\n\n"
            )

        if len(opportunities) > 5:
            result_text += f"<i>...и ещё {len(opportunities) - 5} возможностей</i>\n"

        keyboard = [
            [InlineKeyboardButton("🔄 Повторить", callback_data=f"scan_game_{game}")],
            [InlineKeyboardButton("🔎 Все игры", callback_data="auto_trade_scan_all")],
            [InlineKeyboardButton("🚀 Авто-покупка", callback_data="auto_trade_run")],
            [InlineKeyboardButton("◀️ Назад", callback_data="auto_trade_start")],
        ]

        await query.edit_message_text(
            result_text,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

        logger.info(
            "single_game_scan_complete",
            game=game,
            opportunities_found=len(opportunities),
        )

    except Exception as e:
        logger.exception(f"Single game scan failed: {e}")
        await query.edit_message_text(
            f"❌ <b>Ошибка сканирования {game_name}</b>\n\n{str(e)[:200]}",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Повторить", callback_data=f"scan_game_{game}")],
                [InlineKeyboardButton("◀️ Назад", callback_data="auto_trade_scan_all")],
            ]),
        )


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
            # API returns balance in dollars directly in 'balance' field
            if isinstance(balance_data, dict):
                balance = float(balance_data.get("balance", 0))
            else:
                balance = float(balance_data) if balance_data else 0.0

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
            usd = float(balance_data.get("balance", 0))
            dmc = float(balance_data.get("dmc_balance", 0))
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

        # Получаем инвентарь (CS:GO game_id по умолчанию)
        inventory = await dmarket_api.get_user_inventory(limit=20)
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


# ═══════════════════════════════════════════════════════════════════════════
# ML/AI ОБУЧЕНИЕ - Callback handlers
# ═══════════════════════════════════════════════════════════════════════════


async def ml_ai_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """ML/AI меню - выбор действий для обучения модели."""
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("🎓 Обучить модель", callback_data="ml_ai_train")],
        [InlineKeyboardButton("📊 Статус AI", callback_data="ml_ai_status")],
        [InlineKeyboardButton("◀️ Главное меню", callback_data="main_menu")],
    ]

    text = (
        "🧠 <b>ML/AI ОБУЧЕНИЕ</b>\n\n"
        "Используйте машинное обучение для предсказания цен.\n\n"
        "• <b>Обучить модель</b> - запуск тренировки на истории цен\n"
        "• <b>Статус AI</b> - текущее состояние модели\n"
    )

    await query.edit_message_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def ml_ai_train_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Запуск обучения ML модели предсказания цен."""
    query = update.callback_query
    await query.answer("🎓 Запуск обучения...")

    # Показать статус "обучается"
    await query.edit_message_text(
        "🔄 <b>Обучение модели...</b>\n\n"
        "⏳ Это может занять несколько минут.\n"
        "Пожалуйста, подождите...",
        parse_mode=ParseMode.HTML,
    )

    try:
        # Создаем PricePredictor
        predictor = PricePredictor()

        # Проверяем наличие файла истории рынка (абсолютный путь)
        from pathlib import Path

        project_root = Path(__file__).resolve().parents[3]  # project root
        history_path = project_root / "data" / "market_history.csv"

        if history_path.exists():
            # Обучаем модель на реальных данных
            result = predictor.train_model(str(history_path), force_retrain=True)

            model_info = predictor.get_model_info()

            keyboard = [
                [InlineKeyboardButton("📊 Статус AI", callback_data="ml_ai_status")],
                [InlineKeyboardButton("◀️ Назад", callback_data="ml_ai_menu")],
            ]

            await query.edit_message_text(
                "✅ <b>Модель успешно обучена!</b>\n\n"
                f"📁 Модель: <code>data/price_model.pkl</code>\n"
                f"📊 Статус: {result}\n"
                f"🎯 Алгоритм: RandomForest\n"
                f"📈 Модель готова: {'Да' if model_info.get('model_loaded') else 'Нет'}\n\n"
                "Теперь AI может предсказывать цены!",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        else:
            # Нет данных для обучения - предложить собрать
            keyboard = [
                [InlineKeyboardButton("📈 Собрать данные", callback_data="ml_ai_collect_data")],
                [InlineKeyboardButton("📝 Создать демо данные", callback_data="ml_ai_create_demo")],
                [InlineKeyboardButton("◀️ Назад", callback_data="ml_ai_menu")],
            ]

            await query.edit_message_text(
                "⚠️ <b>Нет данных для обучения</b>\n\n"
                f"📁 Ожидаемый файл: <code>{history_path}</code>\n\n"
                "Для обучения модели нужны исторические данные о ценах.\n"
                "Выберите способ получения данных:",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(keyboard),
            )

    except Exception as e:
        logger.exception(f"ML training error: {e}")
        keyboard = [
            [InlineKeyboardButton("🔄 Попробовать снова", callback_data="ml_ai_train")],
            [InlineKeyboardButton("◀️ Назад", callback_data="ml_ai_menu")],
        ]
        await query.edit_message_text(
            f"❌ <b>Ошибка обучения</b>\n\n<code>{str(e)[:200]}</code>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )


async def ml_ai_status_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать статус ML/AI модели."""
    query = update.callback_query
    await query.answer()

    # Абсолютные пути к файлам
    from pathlib import Path

    project_root = Path(__file__).resolve().parents[3]
    model_path = project_root / "data" / "price_model.pkl"
    history_path = project_root / "data" / "market_history.csv"
    model_exists = model_path.exists()
    history_exists = history_path.exists()

    if model_exists:
        file_size = pathlib.Path(model_path).stat().st_size
        file_size_kb = file_size / 1024

        # Проверим историю
        history_info = ""
        if history_exists:
            try:
                import pandas as pd

                df = pd.read_csv(history_path)
                history_info = f"📊 Данные: {len(df)} записей\n"
            except Exception:
                history_info = "📊 Данные: файл есть\n"

        status_text = (
            "🧠 <b>Статус ML/AI модели</b>\n\n"
            "✅ <b>Модель обучена</b>\n\n"
            f"📁 Путь: <code>{model_path}</code>\n"
            f"💾 Размер: {file_size_kb:.1f} KB\n"
            f"{history_info}"
            f"🎯 Алгоритм: RandomForest\n"
            f"📈 Готова к предсказаниям: Да\n"
        )
    else:
        status_text = "🧠 <b>Статус ML/AI модели</b>\n\n❌ <b>Модель не обучена</b>\n\n"
        if history_exists:
            status_text += "✅ Файл истории найден - можно обучить\n"
        else:
            status_text += "⚠️ Нет данных для обучения\n"
            status_text += "Создайте демо данные или соберите реальные.\n"

    keyboard = [
        [InlineKeyboardButton("🎓 Обучить модель", callback_data="ml_ai_train")],
        [InlineKeyboardButton("📝 Создать демо данные", callback_data="ml_ai_create_demo")],
        [InlineKeyboardButton("◀️ Назад", callback_data="ml_ai_menu")],
    ]

    await query.edit_message_text(
        status_text,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def ml_ai_create_demo_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Создать демо данные для обучения модели."""
    query = update.callback_query
    await query.answer("Создаю демо данные...")

    try:
        from datetime import datetime, timedelta
        from pathlib import Path

        import numpy as np
        import pandas as pd

        # Абсолютный путь к директории data
        project_root = Path(__file__).resolve().parents[3]
        data_dir = project_root / "data"
        data_dir.mkdir(exist_ok=True)

        # Генерируем реалистичные демо данные
        n_samples = 500
        items = [
            "AK-47 | Redline (Field-Tested)",
            "AWP | Asiimov (Field-Tested)",
            "M4A4 | Desolate Space (Field-Tested)",
            "USP-S | Kill Confirmed (Field-Tested)",
            "Glock-18 | Water Elemental (Factory New)",
        ]

        data = []
        base_date = datetime.now() - timedelta(days=30)
        rng = np.random.default_rng()  # Modern numpy Generator

        for i in range(n_samples):
            item = rng.choice(items)
            base_price = 10 + rng.random() * 90  # $10-100
            suggested = base_price * (1.05 + rng.random() * 0.15)
            profit = suggested * 0.93 - base_price
            # Generate realistic float values for CS:GO skins
            float_value = round(rng.uniform(0.0, 1.0), 4)
            is_stat_trak = int(rng.random() < 0.15)  # 15% chance of StatTrak

            data.append({
                "date": (base_date + timedelta(hours=i)).isoformat(),
                "item_name": item,
                "price": round(base_price, 2),
                "suggested_price": round(suggested, 2),
                "profit": round(profit, 2),
                "profit_percent": round((profit / base_price) * 100, 2),
                "game": "csgo",
                "float_value": float_value,
                "is_stat_trak": is_stat_trak,
            })

        df = pd.DataFrame(data)
        history_path = data_dir / "market_history.csv"
        df.to_csv(history_path, index=False)

        keyboard = [
            [InlineKeyboardButton("🎓 Обучить модель", callback_data="ml_ai_train")],
            [InlineKeyboardButton("◀️ Назад", callback_data="ml_ai_menu")],
        ]

        await query.edit_message_text(
            "✅ <b>Демо данные созданы!</b>\n\n"
            f"📊 Записей: {n_samples}\n"
            f"📁 Файл: <code>{history_path}</code>\n"
            f"🎮 Предметов: {len(items)} типов\n\n"
            "Теперь можно обучить модель.",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    except Exception as e:
        keyboard = [
            [InlineKeyboardButton("◀️ Назад", callback_data="ml_ai_menu")],
        ]
        await query.edit_message_text(
            f"❌ <b>Ошибка создания данных</b>\n\n<code>{str(e)[:200]}</code>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )


async def ml_ai_collect_data_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Собрать реальные данные с DMarket для обучения ML модели.

    Использует MarketDataLogger для сбора текущих рыночных данных
    и сохранения в data/market_history.csv для последующего обучения.
    """
    query = update.callback_query
    await query.answer()

    try:
        # Получаем API из контекста бота
        dmarket_api = context.bot_data.get("dmarket_api")
        if not dmarket_api:
            await query.edit_message_text(
                "❌ <b>Ошибка:</b> DMarket API не настроен.\n\n"
                "Проверьте настройки API ключей в конфигурации бота.",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("◀️ Назад", callback_data="ml_ai_menu")]
                ]),
            )
            return

        # Показываем статус сбора
        await query.edit_message_text(
            "⏳ <b>Сбор данных с DMarket...</b>\n\nЭто может занять некоторое время.",
            parse_mode=ParseMode.HTML,
        )

        # Создаём логгер и собираем данные
        data_logger = MarketDataLogger(dmarket_api)
        items_logged = await data_logger.log_market_data()

        # Проверяем файл данных
        data_path = Path("data/market_history.csv")
        file_size = data_path.stat().st_size if data_path.exists() else 0
        file_size_kb = file_size / 1024

        # Показываем результат
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎓 Обучить модель", callback_data="ml_ai_train")],
            [InlineKeyboardButton("📈 Собрать ещё", callback_data="ml_ai_collect_data")],
            [InlineKeyboardButton("◀️ Назад", callback_data="ml_ai_menu")],
        ])
        await query.edit_message_text(
            f"✅ <b>Данные собраны!</b>\n\n"
            f"📊 Записано предметов: <code>{items_logged}</code>\n"
            f"📁 Файл: <code>data/market_history.csv</code>\n"
            f"💾 Размер: <code>{file_size_kb:.1f} KB</code>\n\n"
            "Теперь можно обучить модель на реальных данных рынка.",
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard,
        )

    except Exception as e:
        logger.exception(f"Ошибка сбора данных: {e}")
        await query.edit_message_text(
            f"❌ <b>Ошибка сбора данных:</b>\n\n<code>{str(e)[:300]}</code>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Назад", callback_data="ml_ai_menu")]
            ]),
        )


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
    application.add_handler(
        CallbackQueryHandler(auto_trade_scan_all, pattern="^auto_trade_scan_all$")
    )
    application.add_handler(CallbackQueryHandler(auto_trade_status, pattern="^auto_trade_status$"))
    application.add_handler(
        CallbackQueryHandler(auto_trade_settings, pattern="^auto_trade_settings$")
    )

    # Сканирование отдельных игр
    application.add_handler(CallbackQueryHandler(scan_single_game, pattern="^scan_game_csgo$"))
    application.add_handler(CallbackQueryHandler(scan_single_game, pattern="^scan_game_dota2$"))
    application.add_handler(CallbackQueryHandler(scan_single_game, pattern="^scan_game_tf2$"))
    application.add_handler(CallbackQueryHandler(scan_single_game, pattern="^scan_game_rust$"))

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

    # ML/AI обучение
    application.add_handler(CallbackQueryHandler(ml_ai_menu_callback, pattern="^ml_ai_menu$"))
    application.add_handler(CallbackQueryHandler(ml_ai_train_callback, pattern="^ml_ai_train$"))
    application.add_handler(CallbackQueryHandler(ml_ai_status_callback, pattern="^ml_ai_status$"))
    application.add_handler(
        CallbackQueryHandler(ml_ai_create_demo_callback, pattern="^ml_ai_create_demo$")
    )
    application.add_handler(
        CallbackQueryHandler(ml_ai_collect_data_callback, pattern="^ml_ai_collect_data$")
    )

    logger.info("✅ Main keyboard handlers registered (incl. multi-game scan, ML/AI)")
