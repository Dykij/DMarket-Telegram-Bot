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
    """Stub: Create target."""
    await handle_temporary_unavailable(update, context, "Создание таргета")


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
    """Stub: Compare with Steam."""
    await handle_temporary_unavailable(update, context, "Сравнение с Steam")


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
        "next_page"
        if update.callback_query.data.startswith("arb_next_page_")
        else "prev_page"
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
