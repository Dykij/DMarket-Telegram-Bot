"""Callback router initialization - Register all handlers.

Phase 2 Refactoring: Centralized registration using router pattern.
"""

import logging

from src.telegram_bot.handlers.callback_handlers import (
    handle_alerts,
    handle_arbitrage_menu,
    handle_auto_arbitrage,
    handle_back_to_main,
    handle_balance,
    handle_best_opportunities,
    handle_dmarket_arbitrage,
    handle_game_selection,
    handle_help,
    handle_main_menu,
    handle_market_analysis,
    handle_market_trends,
    handle_noop,
    handle_open_webapp,
    handle_search,
    handle_settings,
    handle_simple_menu,
    handle_temporary_unavailable,
)
from src.telegram_bot.handlers.callback_router import CallbackRouter
from src.telegram_bot.keyboards import CB_BACK, CB_CANCEL, CB_GAME_PREFIX, CB_HELP


logger = logging.getLogger(__name__)


def create_callback_router() -> CallbackRouter:
    """Create and configure callback router with all handlers.

    Returns:
        Configured CallbackRouter instance

    """
    router = CallbackRouter()

    # ========================================================================
    # EXACT MATCH HANDLERS
    # ========================================================================

    # Menu handlers
    router.register_exact("simple_menu", handle_simple_menu)
    router.register_exact("balance", handle_balance)
    router.register_exact("search", handle_search)
    router.register_exact("settings", handle_settings)
    router.register_exact("market_trends", handle_market_trends)
    router.register_exact("alerts", handle_alerts)
    router.register_exact("back_to_main", handle_back_to_main)
    router.register_exact("main_menu", handle_main_menu)
    router.register_exact("back_to_menu", handle_back_to_main)

    # Arbitrage handlers
    router.register_exact("arbitrage", handle_arbitrage_menu)
    router.register_exact("arbitrage_menu", handle_arbitrage_menu)
    router.register_exact("auto_arbitrage", handle_auto_arbitrage)
    router.register_exact("dmarket_arbitrage", handle_dmarket_arbitrage)
    router.register_exact("best_opportunities", handle_best_opportunities)
    router.register_exact("game_selection", handle_game_selection)
    router.register_exact("market_analysis", handle_market_analysis)
    router.register_exact("market_comparison", handle_market_analysis)
    router.register_exact("open_webapp", handle_open_webapp)

    # Help
    router.register_exact(CB_HELP, handle_help)
    router.register_exact("help", handle_help)

    # No-op handlers
    router.register_exact("noop", handle_noop)
    router.register_exact("page_info", handle_noop)
    router.register_exact("alerts_page_info", handle_noop)
    router.register_exact(CB_BACK, handle_noop)
    router.register_exact(CB_CANCEL, handle_noop)
    router.register_exact("back", handle_noop)
    router.register_exact("cancel", handle_noop)

    # Enhanced scanner menu
    router.register_exact("enhanced_scanner_menu", _handle_enhanced_scanner_menu)

    # Settings submenu
    router.register_exact("settings_api_keys", _handle_settings_api_keys)
    router.register_exact("settings_proxy", _handle_settings_proxy)
    router.register_exact("settings_currency", _handle_settings_currency)
    router.register_exact("settings_intervals", _handle_settings_intervals)
    router.register_exact("settings_filters", _handle_settings_filters)
    router.register_exact("settings_auto_refresh", _handle_settings_auto_refresh)
    router.register_exact("settings_language", _handle_settings_language)
    router.register_exact("settings_notify", _handle_settings_notify)
    router.register_exact("settings_api", _handle_settings_api)
    router.register_exact("settings_risk", _handle_settings_risk)
    router.register_exact("settings_limits", _handle_settings_limits)
    router.register_exact("settings_games", _handle_settings_games)

    # Alert submenu
    router.register_exact("alert_create", _handle_alert_create)
    router.register_exact("alert_list", _handle_alert_list)
    router.register_exact("alert_settings", _handle_alert_settings)
    router.register_exact("alert_active", _handle_alert_active)
    router.register_exact("alert_history", _handle_alert_history)
    router.register_exact("back_to_alerts", _handle_back_to_alerts)

    # Arbitrage submenu
    router.register_exact("arb_quick", _handle_arb_quick)
    router.register_exact("arb_deep", _handle_arb_deep)
    router.register_exact("arb_market_analysis", _handle_arb_market_analysis)
    router.register_exact("arb_target", _handle_arb_target)
    router.register_exact("arb_stats", _handle_arb_stats)
    router.register_exact("arb_compare", _handle_arb_compare)
    router.register_exact("arb_scan", _handle_arb_scan)
    router.register_exact("arb_game", _handle_arb_game)
    router.register_exact("arb_levels", _handle_arb_levels)
    router.register_exact("arb_settings", _handle_arb_settings)
    router.register_exact("arb_auto", _handle_arb_auto)
    router.register_exact("arb_analysis", _handle_arb_analysis)

    # Targets
    router.register_exact("targets", _handle_targets)
    router.register_exact("target_create", _handle_target_create)
    router.register_exact("target_list", _handle_target_list)
    router.register_exact("target_stats", _handle_target_stats)

    # Waxpeer P2P Integration
    router.register_exact("waxpeer_menu", _handle_waxpeer_menu)
    router.register_exact("waxpeer_balance", _handle_waxpeer_balance)
    router.register_exact("waxpeer_settings", _handle_waxpeer_settings)
    router.register_exact("waxpeer_list_items", _handle_waxpeer_scan)
    router.register_exact("waxpeer_valuable", _handle_waxpeer_scan)
    router.register_exact("waxpeer_reprice", _handle_waxpeer_settings)

    # Other features
    router.register_exact("inventory", _handle_inventory)
    router.register_exact("analytics", _handle_analytics)
    router.register_exact("scanner", _handle_scanner)

    # Auto arbitrage
    router.register_exact("auto_arb_start", _handle_auto_arb_start)
    router.register_exact("auto_arb_stop", _handle_auto_arb_stop)
    router.register_exact("auto_arb_settings", _handle_auto_arb_settings)
    router.register_exact("auto_arb_status", _handle_auto_arb_status)
    router.register_exact("auto_arb_history", _handle_auto_arb_history)

    # Smart Arbitrage (NEW - for $45.50 micro balance)
    router.register_exact("start_smart_arbitrage", _handle_start_smart_arbitrage)
    router.register_exact("stop_smart_arbitrage", _handle_stop_smart_arbitrage)
    router.register_exact("smart_arbitrage_status", _handle_smart_arbitrage_status)
    router.register_exact("smart", _handle_smart_arbitrage_menu)
    router.register_exact("smart_create_targets", _handle_smart_create_targets)

    # Comparison
    router.register_exact("cmp_steam", _handle_cmp_steam)
    router.register_exact("cmp_buff", _handle_cmp_buff)
    router.register_exact("cmp_refresh", _handle_cmp_refresh)

    # Analysis
    router.register_exact("analysis_trends", _handle_analysis_trends)
    router.register_exact("analysis_vol", _handle_analysis_vol)
    router.register_exact("analysis_top", _handle_analysis_top)
    router.register_exact("analysis_drop", _handle_analysis_drop)
    router.register_exact("analysis_rec", _handle_analysis_rec)

    # Backtesting
    router.register_exact("backtest_quick", _handle_backtest_quick)
    router.register_exact("backtest_standard", _handle_backtest_standard)
    router.register_exact("backtest_custom", _handle_backtest_custom)

    # ========================================================================
    # PREFIX HANDLERS
    # ========================================================================

    # Skip simplified menu callbacks (handled elsewhere)
    router.register_prefix("simple_", _handle_skip_simple)

    # Game selection
    router.register_prefix("game_selected:", _handle_game_selected)
    router.register_prefix(CB_GAME_PREFIX, _handle_game_prefix)

    # Pagination
    router.register_prefix("arb_next_page_", _handle_pagination)
    router.register_prefix("arb_prev_page_", _handle_pagination)

    # Scanner levels
    router.register_prefix("scan_level_", _handle_scan_level)
    router.register_prefix("scanner_level_scan_", _handle_scan_level)

    # Language
    router.register_prefix("lang_", _handle_lang)

    # Risk profile
    router.register_prefix("risk_", _handle_risk)

    # Alert types
    router.register_prefix("alert_type_", _handle_alert_type)

    # Notifications
    router.register_prefix("notify_", _handle_notify)

    # Arbitrage settings
    router.register_prefix("arb_set_", _handle_arb_set)

    # Filters
    router.register_prefix("filter:", _handle_filter)

    # Auto start
    router.register_prefix("auto_start:", _handle_auto_start)

    # Paginate
    router.register_prefix("paginate:", _handle_paginate)

    # Auto trade
    router.register_prefix("auto_trade:", _handle_auto_trade)

    # Compare
    router.register_prefix("compare:", _handle_compare)

    logger.info("Callback router initialized with %d exact handlers", len(router._exact_handlers))
    logger.info("Callback router initialized with %d prefix handlers", len(router._prefix_handlers))

    return router


# ============================================================================
# STUB HANDLERS (to be implemented)
# ============================================================================


async def _handle_enhanced_scanner_menu(update, context):
    """Stub: Enhanced scanner menu."""
    await handle_temporary_unavailable(update, context, "Расширенный сканер")


async def _handle_settings_api_keys(update, context):
    """Stub: API keys settings."""
    await handle_temporary_unavailable(update, context, "Настройка API ключей")


async def _handle_settings_proxy(update, context):
    """Stub: Proxy settings."""
    await handle_temporary_unavailable(update, context, "Настройка прокси")


async def _handle_settings_currency(update, context):
    """Stub: Currency settings."""
    await handle_temporary_unavailable(update, context, "Настройка валюты")


async def _handle_settings_intervals(update, context):
    """Stub: Intervals settings."""
    await handle_temporary_unavailable(update, context, "Настройка интервалов")


async def _handle_settings_filters(update, context):
    """Stub: Filters settings."""
    await handle_temporary_unavailable(update, context, "Настройка фильтров")


async def _handle_settings_auto_refresh(update, context):
    """Stub: Auto refresh settings."""
    await handle_temporary_unavailable(update, context, "Автообновление")


async def _handle_settings_language(update, context):
    """Stub: Language settings."""
    await handle_temporary_unavailable(update, context, "Настройка языка")


async def _handle_settings_notify(update, context):
    """Stub: Notification settings."""
    await handle_temporary_unavailable(update, context, "Настройка уведомлений")


async def _handle_settings_api(update, context):
    """Stub: API settings."""
    await handle_temporary_unavailable(update, context, "Настройка API")


async def _handle_settings_risk(update, context):
    """Stub: Risk settings."""
    await handle_temporary_unavailable(update, context, "Настройка рисков")


async def _handle_settings_limits(update, context):
    """Stub: Limits settings."""
    await handle_temporary_unavailable(update, context, "Настройка лимитов")


async def _handle_settings_games(update, context):
    """Stub: Games settings."""
    await handle_temporary_unavailable(update, context, "Выбор игр")


async def _handle_alert_create(update, context):
    """Stub: Create alert."""
    await handle_temporary_unavailable(update, context, "Создание оповещения")


async def _handle_alert_list(update, context):
    """Stub: Alert list."""
    await handle_temporary_unavailable(update, context, "Список оповещений")


async def _handle_alert_settings(update, context):
    """Stub: Alert settings."""
    await handle_temporary_unavailable(update, context, "Настройки оповещений")


async def _handle_alert_active(update, context):
    """Stub: Active alerts."""
    await handle_temporary_unavailable(update, context, "Активные оповещения")


async def _handle_alert_history(update, context):
    """Stub: Alert history."""
    await handle_temporary_unavailable(update, context, "История оповещений")


async def _handle_back_to_alerts(update, context):
    """Stub: Back to alerts."""
    await handle_alerts(update, context)


async def _handle_arb_quick(update, context):
    """Stub: Quick arbitrage."""
    await handle_temporary_unavailable(update, context, "Быстрый арбитраж")


async def _handle_arb_deep(update, context):
    """Stub: Deep arbitrage."""
    await handle_temporary_unavailable(update, context, "Глубокий арбитраж")


async def _handle_arb_market_analysis(update, context):
    """Stub: Market analysis."""
    await handle_market_analysis(update, context)


async def _handle_arb_target(update, context):
    """Stub: Arbitrage target."""
    await handle_temporary_unavailable(update, context, "Таргеты")


async def _handle_arb_stats(update, context):
    """Stub: Arbitrage stats."""
    await handle_temporary_unavailable(update, context, "Статистика")


async def _handle_arb_compare(update, context):
    """Stub: Arbitrage compare."""
    await handle_temporary_unavailable(update, context, "Сравнение площадок")


async def _handle_arb_scan(update, context):
    """Stub: Arbitrage scan."""
    await handle_temporary_unavailable(update, context, "Сканирование")


async def _handle_arb_game(update, context):
    """Stub: Arbitrage game selection."""
    await handle_game_selection(update, context)


async def _handle_arb_levels(update, context):
    """Stub: Arbitrage levels."""
    await handle_temporary_unavailable(update, context, "Уровни арбитража")


async def _handle_arb_settings(update, context):
    """Stub: Arbitrage settings."""
    await handle_temporary_unavailable(update, context, "Настройки арбитража")


async def _handle_arb_auto(update, context):
    """Stub: Auto arbitrage."""
    await handle_auto_arbitrage(update, context)


async def _handle_arb_analysis(update, context):
    """Stub: Arbitrage analysis."""
    await handle_market_analysis(update, context)


async def _handle_targets(update, context):
    """Stub: Targets."""
    await handle_temporary_unavailable(update, context, "Таргеты")


async def _handle_target_create(update, context):
    """Create target with game selection menu."""
    if not update.callback_query:
        return

    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

    keyboard = [
        [
            InlineKeyboardButton("CS:GO", callback_data="game_selected:csgo"),
            InlineKeyboardButton("Dota 2", callback_data="game_selected:dota2"),
        ],
        [
            InlineKeyboardButton("Rust", callback_data="game_selected:rust"),
            InlineKeyboardButton("TF2", callback_data="game_selected:tf2"),
        ],
        [InlineKeyboardButton("◀️ Назад", callback_data="targets")],
    ]

    await update.callback_query.edit_message_text(
        "🎯 <b>Создание таргета</b>\n\n"
        "Выберите игру для настройки параметров покупки.\n"
        "Бот будет выставлять запросы на покупку (Targets) "
        "на основе анализа ликвидности.",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def _handle_target_list(update, context):
    """Stub: Target list."""
    await handle_temporary_unavailable(update, context, "Список таргетов")


async def _handle_target_stats(update, context):
    """Stub: Target stats."""
    await handle_temporary_unavailable(update, context, "Статистика таргетов")


async def _handle_inventory(update, context):
    """Stub: Inventory."""
    await handle_temporary_unavailable(update, context, "Инвентарь")


async def _handle_analytics(update, context):
    """Stub: Analytics."""
    await handle_temporary_unavailable(update, context, "Аналитика")


async def _handle_scanner(update, context):
    """Stub: Scanner."""
    await handle_temporary_unavailable(update, context, "Сканер")


async def _handle_auto_arb_start(update, context):
    """Stub: Start auto arbitrage."""
    await handle_temporary_unavailable(update, context, "Запуск авто-арбитража")


async def _handle_auto_arb_stop(update, context):
    """Stub: Stop auto arbitrage."""
    await handle_temporary_unavailable(update, context, "Остановка авто-арбитража")


async def _handle_auto_arb_settings(update, context):
    """Stub: Auto arbitrage settings."""
    await handle_temporary_unavailable(update, context, "Настройки авто-арбитража")


async def _handle_auto_arb_status(update, context):
    """Stub: Auto arbitrage status."""
    await handle_temporary_unavailable(update, context, "Статус авто-арбитража")


async def _handle_auto_arb_history(update, context):
    """Stub: Auto arbitrage history."""
    await handle_temporary_unavailable(update, context, "История авто-арбитража")


async def _handle_cmp_steam(update, context):
    """Compare prices with Steam Market."""
    if not update.callback_query:
        return

    await update.callback_query.answer("Загрузка цен Steam...")

    try:
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        from src.utils.steam_async_parser import SteamAsyncParser

        # Configuration constants
        STEAM_CACHE_TTL = 300  # 5 minutes
        STEAM_MAX_CONCURRENT = 5
        ITEM_NAME_MAX_LEN = 30

        # Sample popular items to compare (can be expanded via config)
        SAMPLE_ITEMS = [
            "AK-47 | Redline (Field-Tested)",
            "AWP | Asiimov (Field-Tested)",
            "M4A4 | Asiimov (Field-Tested)",
        ]

        # Get API client and fetch some popular items
        api = context.bot_data.get("dmarket_api")

        if not api:
            await update.callback_query.edit_message_text(
                "❌ DMarket API не инициализирован. Используйте /start для настройки."
            )
            return

        parser = SteamAsyncParser(cache_ttl=STEAM_CACHE_TTL, max_concurrent=STEAM_MAX_CONCURRENT)

        results = await parser.get_batch_prices(SAMPLE_ITEMS, game="csgo")

        # Format results
        comparison_text = "📊 <b>Сравнение цен со Steam Market</b>\n\n"

        for result in results:
            item_name = result.get("item_name", "Unknown")
            truncated_name = item_name[:ITEM_NAME_MAX_LEN]

            if result.get("status") == "success":
                lowest = result.get("lowest_price", "N/A")
                median = result.get("median_price", "N/A")
                volume = result.get("volume", "0")

                comparison_text += f"<b>{truncated_name}...</b>\n"
                comparison_text += f"  └ Steam: ${lowest} (медиана ${median})\n"
                comparison_text += f"  └ Объем: {volume} шт/день\n\n"
            else:
                comparison_text += f"<b>{truncated_name}...</b>\n"
                comparison_text += f"  └ ⚠️ {result.get('status', 'error')}\n\n"

        comparison_text += "\n💡 <i>Цены обновляются каждые 5 минут</i>"

        keyboard = [
            [InlineKeyboardButton("🔄 Обновить", callback_data="cmp_steam")],
            [InlineKeyboardButton("◀️ Назад", callback_data="arb_compare")],
        ]

        await update.callback_query.edit_message_text(
            comparison_text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    except Exception as e:
        logger.exception("Error comparing Steam prices: %s", e)
        await update.callback_query.edit_message_text(
            f"❌ Ошибка получения цен Steam: {e}"
        )


async def _handle_cmp_buff(update, context):
    """Stub: Compare with Buff."""
    await handle_temporary_unavailable(update, context, "Сравнение с Buff")


async def _handle_cmp_refresh(update, context):
    """Stub: Refresh comparison."""
    await handle_temporary_unavailable(update, context, "Обновление сравнения")


async def _handle_analysis_trends(update, context):
    """Stub: Trends analysis."""
    await handle_temporary_unavailable(update, context, "Анализ трендов")


async def _handle_analysis_vol(update, context):
    """Stub: Volume analysis."""
    await handle_temporary_unavailable(update, context, "Анализ объемов")


async def _handle_analysis_top(update, context):
    """Stub: Top items analysis."""
    await handle_temporary_unavailable(update, context, "Топ предметов")


async def _handle_analysis_drop(update, context):
    """Stub: Price drops analysis."""
    await handle_temporary_unavailable(update, context, "Падение цен")


async def _handle_analysis_rec(update, context):
    """Stub: Recommendations."""
    await handle_temporary_unavailable(update, context, "Рекомендации")


async def _handle_backtest_quick(update, context):
    """Handle quick backtest."""
    from src.telegram_bot.commands.backtesting_commands import run_quick_backtest

    api = context.bot_data.get("dmarket_api")
    if api:
        await run_quick_backtest(update, context, api)
    else:
        await update.callback_query.edit_message_text("❌ DMarket API недоступен")


async def _handle_backtest_standard(update, context):
    """Handle standard backtest."""
    from src.telegram_bot.commands.backtesting_commands import run_standard_backtest

    api = context.bot_data.get("dmarket_api")
    if api:
        await run_standard_backtest(update, context, api)
    else:
        await update.callback_query.edit_message_text("❌ DMarket API недоступен")


async def _handle_backtest_custom(update, context):
    """Handle custom backtest."""
    if not update.callback_query:
        return

    await update.callback_query.edit_message_text(
        "⚙️ <b>Custom Backtest Settings</b>\n\n"
        "Custom backtesting coming soon!\n\n"
        "You'll be able to configure:\n"
        "• Date range\n"
        "• Initial balance\n"
        "• Strategy parameters\n"
        "• Item selection",
        parse_mode="HTML",
    )


# Prefix handlers
async def _handle_skip_simple(update, context):
    """Skip simple_ prefixed callbacks (handled elsewhere)."""


async def _handle_game_selected(update, context):
    """Handle game_selected: prefix."""
    from src.telegram_bot.handlers.callbacks import handle_game_selected_impl

    if not update.callback_query or not update.callback_query.data:
        return

    game = update.callback_query.data.split(":", 1)[1]
    await handle_game_selected_impl(update, context, game=game)


async def _handle_game_prefix(update, context):
    """Handle game_ prefix."""
    from src.telegram_bot.handlers.callbacks import handle_game_selected_impl

    if not update.callback_query or not update.callback_query.data:
        return

    if update.callback_query.data.startswith("game_selected"):
        return

    game = update.callback_query.data[len(CB_GAME_PREFIX) :]
    await handle_game_selected_impl(update, context, game=game)


async def _handle_pagination(update, context):
    """Handle arb_next_page_/arb_prev_page_ prefix."""
    from src.telegram_bot.handlers.callbacks import handle_arbitrage_pagination

    if not update.callback_query or not update.callback_query.data:
        return

    direction = (
        "next_page" if update.callback_query.data.startswith("arb_next_page_") else "prev_page"
    )
    await handle_arbitrage_pagination(update.callback_query, context, direction)


async def _handle_scan_level(update, context):
    """Handle scan_level_/scanner_level_scan_ prefix."""
    await handle_temporary_unavailable(update, context, "Уровень сканирования")


async def _handle_lang(update, context):
    """Handle lang_ prefix."""
    await handle_temporary_unavailable(update, context, "Смена языка")


async def _handle_risk(update, context):
    """Handle risk_ prefix."""
    await handle_temporary_unavailable(update, context, "Уровень риска")


async def _handle_alert_type(update, context):
    """Handle alert_type_ prefix."""
    await handle_temporary_unavailable(update, context, "Тип оповещения")


async def _handle_notify(update, context):
    """Handle notify_ prefix."""
    await handle_temporary_unavailable(update, context, "Уведомление")


async def _handle_arb_set(update, context):
    """Handle arb_set_ prefix."""
    await handle_temporary_unavailable(update, context, "Настройка арбитража")


async def _handle_filter(update, context):
    """Handle filter: prefix."""
    await handle_temporary_unavailable(update, context, "Фильтр")


async def _handle_auto_start(update, context):
    """Handle auto_start: prefix."""
    await handle_temporary_unavailable(update, context, "Автозапуск")


async def _handle_paginate(update, context):
    """Handle paginate: prefix."""
    await handle_temporary_unavailable(update, context, "Пагинация")


async def _handle_auto_trade(update, context):
    """Handle auto_trade: prefix."""
    await handle_temporary_unavailable(update, context, "Авто-торговля")


async def _handle_compare(update, context):
    """Handle compare: prefix."""
    await handle_temporary_unavailable(update, context, "Сравнение")


# ============================================================================
# SMART ARBITRAGE HANDLERS (NEW - For micro balance trading)
# ============================================================================


async def _handle_start_smart_arbitrage(update, context):
    """Start Smart Arbitrage mode with pagination and auto-buy."""
    if not update.callback_query:
        return

    try:
        # Get smart arbitrage engine from bot_data
        smart_engine = context.bot_data.get("smart_arbitrage_engine")
        api = context.bot_data.get("dmarket_api")

        if not smart_engine and api:
            # Initialize if not exists
            from src.dmarket.smart_arbitrage import SmartArbitrageEngine

            smart_engine = SmartArbitrageEngine(api)
            context.bot_data["smart_arbitrage_engine"] = smart_engine

        if smart_engine:
            if smart_engine.is_running:
                await update.callback_query.edit_message_text(
                    "⚠️ Smart Arbitrage уже запущен!\n\nИспользуйте /status для проверки состояния."
                )
                return

            # Get current balance and limits
            limits = await smart_engine.calculate_adaptive_limits()
            strategy = await smart_engine.get_strategy_description()

            await update.callback_query.edit_message_text(
                f"🚀 <b>Smart Arbitrage запускается!</b>\n\n"
                f"💰 Баланс: ${limits.usable_balance:.2f}\n"
                f"📊 Тир: {limits.tier.upper()}\n"
                f"🎯 ROI: {limits.min_roi:.0f}%+\n"
                f"💵 Max цена: ${limits.max_buy_price:.2f}\n\n"
                f"{strategy}\n\n"
                f"🔄 Сканирование: 500 предметов (5 страниц)\n"
                f"⏱ Интервал: {'30с' if limits.usable_balance < 50 else '60с'}\n\n"
                f"✅ Бот начал поиск арбитражных возможностей!",
                parse_mode="HTML",
            )

            # Start in background (don't await - let it run)
            import asyncio

            asyncio.create_task(smart_engine.start_smart_mode(auto_buy=True))

        else:
            await update.callback_query.edit_message_text(
                "❌ Smart Arbitrage Engine не инициализирован.\nПроверьте DMarket API подключение."
            )

    except Exception as e:
        logger.exception("Error starting smart arbitrage: %s", e)
        await update.callback_query.edit_message_text(f"❌ Ошибка: {e}")


async def _handle_stop_smart_arbitrage(update, context):
    """Stop Smart Arbitrage mode."""
    if not update.callback_query:
        return

    smart_engine = context.bot_data.get("smart_arbitrage_engine")

    if smart_engine and smart_engine.is_running:
        smart_engine.stop_smart_mode()
        await update.callback_query.edit_message_text(
            "🛑 <b>Smart Arbitrage остановлен</b>\n\n"
            "Бот прекратил поиск арбитражных возможностей.\n"
            "Используйте /smart для перезапуска.",
            parse_mode="HTML",
        )
    else:
        await update.callback_query.edit_message_text("ℹ️ Smart Arbitrage не был запущен.")


async def _handle_smart_arbitrage_status(update, context):
    """Show Smart Arbitrage status."""
    if not update.callback_query:
        return

    try:
        smart_engine = context.bot_data.get("smart_arbitrage_engine")
        api = context.bot_data.get("dmarket_api")

        if not smart_engine and api:
            from src.dmarket.smart_arbitrage import SmartArbitrageEngine

            smart_engine = SmartArbitrageEngine(api)
            context.bot_data["smart_arbitrage_engine"] = smart_engine

        if smart_engine:
            limits = await smart_engine.calculate_adaptive_limits()
            is_safe, warning = smart_engine.check_balance_safety()

            status_emoji = "🟢" if smart_engine.is_running else "🔴"
            safety_text = "✅ В норме" if is_safe else f"⚠️ {warning}"

            status_running = "Работает" if smart_engine.is_running else "Остановлен"
            await update.callback_query.edit_message_text(
                f"📊 <b>Smart Arbitrage Status</b>\n\n"
                f"Статус: {status_emoji} {status_running}\n\n"
                f"💰 <b>Баланс:</b> ${limits.total_balance:.2f}\n"
                f"💵 Доступно: ${limits.usable_balance:.2f}\n"
                f"🏦 Резерв: ${limits.reserve:.2f}\n\n"
                f"📈 <b>Лимиты:</b>\n"
                f"• Тир: {limits.tier.upper()}\n"
                f"• Max цена: ${limits.max_buy_price:.2f}\n"
                f"• Min ROI: {limits.min_roi:.0f}%\n"
                f"• Max предметов: {limits.max_inventory_items}\n\n"
                f"🛡 <b>Безопасность:</b> {safety_text}",
                parse_mode="HTML",
            )
        else:
            await update.callback_query.edit_message_text(
                "❌ Smart Arbitrage Engine не инициализирован."
            )

    except Exception as e:
        logger.exception("Error getting smart arbitrage status: %s", e)
        await update.callback_query.edit_message_text(f"❌ Ошибка: {e}")


async def _handle_smart_arbitrage_menu(update, context):
    """Show Smart Arbitrage menu."""
    if not update.callback_query:
        return

    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

    keyboard = [
        [
            InlineKeyboardButton("🚀 Запустить", callback_data="start_smart_arbitrage"),
            InlineKeyboardButton("🛑 Остановить", callback_data="stop_smart_arbitrage"),
        ],
        [
            InlineKeyboardButton("📊 Статус", callback_data="smart_arbitrage_status"),
        ],
        [
            InlineKeyboardButton("◀️ Назад", callback_data="back_to_main"),
        ],
    ]

    await update.callback_query.edit_message_text(
        "🎯 <b>Smart Arbitrage</b>\n\n"
        "Умный арбитраж с автоматической адаптацией под ваш баланс:\n\n"
        "• 📊 Пагинация: сканирует 500 предметов\n"
        "• 🎚 Динамический ROI: от 5% для микро-баланса\n"
        "• ⏱ Trade Lock фильтр: учитывает заморозку\n"
        "• 🔄 Auto-buy: мгновенная покупка выгодных лотов\n\n"
        "Выберите действие:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def _handle_smart_create_targets(update, context):
    """Create smart targets with game selection for micro-balance trading."""
    if not update.callback_query:
        return

    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

    keyboard = [
        [
            InlineKeyboardButton("CS:GO", callback_data="game_selected:csgo"),
            InlineKeyboardButton("Dota 2", callback_data="game_selected:dota2"),
        ],
        [
            InlineKeyboardButton("Rust", callback_data="game_selected:rust"),
            InlineKeyboardButton("TF2", callback_data="game_selected:tf2"),
        ],
        [InlineKeyboardButton("◀️ Назад", callback_data="smart")],
    ]

    await update.callback_query.edit_message_text(
        "🎯 <b>Создание авто-таргетов</b>\n\n"
        "Выберите игру для настройки параметров покупки.\n"
        "Бот будет автоматически выставлять запросы на покупку (Targets) "
        "на основе анализа ликвидности и вашего баланса.\n\n"
        "💡 <i>Таргеты помогают покупать предметы дешевле рыночной цены</i>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# ============================================================================
# WAXPEER HANDLERS
# ============================================================================


async def _handle_waxpeer_menu(update, context):
    """Handle Waxpeer menu callback."""
    try:
        from src.telegram_bot.handlers.waxpeer_handler import waxpeer_menu_handler

        await waxpeer_menu_handler(update, context)
    except ImportError:
        await handle_temporary_unavailable(update, context, "Waxpeer P2P")


async def _handle_waxpeer_balance(update, context):
    """Handle Waxpeer balance callback."""
    try:
        from src.telegram_bot.handlers.waxpeer_handler import waxpeer_balance_handler

        await waxpeer_balance_handler(update, context)
    except ImportError:
        await handle_temporary_unavailable(update, context, "Waxpeer баланс")


async def _handle_waxpeer_settings(update, context):
    """Handle Waxpeer settings callback."""
    try:
        from src.telegram_bot.handlers.waxpeer_handler import waxpeer_settings_handler

        await waxpeer_settings_handler(update, context)
    except ImportError:
        await handle_temporary_unavailable(update, context, "Waxpeer настройки")


async def _handle_waxpeer_scan(update, context):
    """Handle Waxpeer scan callback."""
    try:
        from src.telegram_bot.handlers.waxpeer_handler import waxpeer_scan_handler

        await waxpeer_scan_handler(update, context)
    except ImportError:
        await handle_temporary_unavailable(update, context, "Waxpeer сканирование")

