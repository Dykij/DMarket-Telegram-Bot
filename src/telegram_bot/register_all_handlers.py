"""Модуль для регистрации всех обработчиков Telegram бота.

Этот модуль объединяет регистрацию всех обработчиков команд, callback-запросов,
и других обработчиков для упрощения инициализации бота.
"""

import logging
from typing import TYPE_CHECKING

from telegram.ext import CallbackQueryHandler, CommandHandler, MessageHandler, filters

from src.telegram_bot.commands.backtesting_commands import backtest_command, backtest_help
from src.telegram_bot.commands.daily_report_command import daily_report_command
from src.telegram_bot.commands.logs_command import logs_command
from src.telegram_bot.commands.start_minimal import start_minimal_command
from src.telegram_bot.commands.test_sentry_command import test_sentry_command, test_sentry_info
from src.telegram_bot.handlers.api_check_handler import handle_api_check_callback
from src.telegram_bot.handlers.automatic_arbitrage_handler import handle_mode_selection_callback
from src.telegram_bot.handlers.callback_registry import create_callback_router
from src.telegram_bot.handlers.callback_router import button_callback_handler_v2
from src.telegram_bot.handlers.callbacks import button_callback_handler
from src.telegram_bot.handlers.commands import (
    arbitrage_command,
    dashboard_command,
    dmarket_status_command,
    help_command,
    markets_command,
    start_command,
    webapp_command,
)
from src.telegram_bot.handlers.minimal_menu_router import minimal_menu_router
from src.telegram_bot.handlers.view_items_handler import handle_view_items_callback


if TYPE_CHECKING:
    from telegram.ext import Application


logger = logging.getLogger(__name__)


def register_all_handlers(application: "Application") -> None:
    """Регистрирует все обработчики команд и callback-запросов для бота.

    Args:
        application: Экземпляр приложения Telegram бота

    """
    logger.info("Начало регистрации обработчиков бота...")

    # Регистрация базовых команд
    # New minimal UI: /start_minimal for minimalistic interface
    application.add_handler(CommandHandler("start_minimal", start_minimal_command))
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("dashboard", dashboard_command))
    application.add_handler(CommandHandler("arbitrage", arbitrage_command))
    application.add_handler(CommandHandler("dmarket", dmarket_status_command))
    application.add_handler(CommandHandler("status", dmarket_status_command))
    application.add_handler(CommandHandler("markets", markets_command))
    application.add_handler(CommandHandler("webapp", webapp_command))
    application.add_handler(CommandHandler("logs", logs_command))
    application.add_handler(CommandHandler("dailyreport", daily_report_command))

    # ═══════════════════════════════════════════════════════════════════════════
    # ГЛАВНАЯ КЛАВИАТУРА (новая упрощённая версия)
    # ═══════════════════════════════════════════════════════════════════════════
    try:
        from src.telegram_bot.handlers.main_keyboard import register_main_keyboard_handlers

        register_main_keyboard_handlers(application)
        logger.info("✅ Main Keyboard Handler зарегистрирован")
    except ImportError as e:
        logger.warning("Не удалось импортировать main_keyboard: %s", e)

    # Sentry тестирование (только для отладки и администраторов)
    application.add_handler(CommandHandler("test_sentry", test_sentry_command))
    application.add_handler(CommandHandler("sentry_info", test_sentry_info))

    # Backtesting команды
    application.add_handler(CommandHandler("backtest", backtest_command))
    application.add_handler(CommandHandler("backtest_help", backtest_help))

    # Auto-buy команды
    try:
        from src.telegram_bot.handlers.auto_buy_handler import autobuy_command

        application.add_handler(CommandHandler("autobuy", autobuy_command))
        logger.info("Auto-buy команда зарегистрирована")
    except ImportError as e:
        logger.warning("Не удалось импортировать auto-buy handler: %s", e)

    # Smart Arbitrage команда (NEW - for micro balance trading)
    try:
        from src.telegram_bot.handlers.smart_arbitrage_handler import smart_arbitrage_command

        application.add_handler(CommandHandler("smart", smart_arbitrage_command))
        logger.info("Smart Arbitrage команда зарегистрирована")
    except ImportError as e:
        logger.warning("Не удалось импортировать smart arbitrage handler: %s", e)

    # Autopilot команды
    try:
        from src.telegram_bot.handlers.autopilot_handler import (
            autopilot_command,
            autopilot_stats_command,
            autopilot_status_command,
            autopilot_stop_command,
        )

        application.add_handler(CommandHandler("autopilot", autopilot_command))
        application.add_handler(CommandHandler("autopilot_stop", autopilot_stop_command))
        application.add_handler(CommandHandler("autopilot_status", autopilot_status_command))
        application.add_handler(CommandHandler("autopilot_stats", autopilot_stats_command))
        logger.info("Autopilot команды зарегистрированы")
    except ImportError as e:
        logger.warning("Не удалось импортировать autopilot handler: %s", e)

    # Panic Button команды
    try:
        from src.telegram_bot.handlers.panic_handler import (
            panic_button_command,
            panic_status_command,
        )

        application.add_handler(CommandHandler("panic", panic_button_command))
        application.add_handler(CommandHandler("panic_status", panic_status_command))
        logger.info("Panic Button команды зарегистрированы")
    except ImportError as e:
        logger.warning("Не удалось импортировать panic handler: %s", e)

    # WebSocket команды
    try:
        from src.telegram_bot.handlers.websocket_handler import (
            websocket_restart_command,
            websocket_stats_command,
            websocket_status_command,
        )

        application.add_handler(CommandHandler("websocket_status", websocket_status_command))
        application.add_handler(CommandHandler("websocket_stats", websocket_stats_command))
        application.add_handler(CommandHandler("websocket_restart", websocket_restart_command))
        logger.info("WebSocket команды зарегистрированы")
    except ImportError as e:
        logger.warning("Не удалось импортировать websocket handler: %s", e)

    # Health Check команды
    try:
        from src.telegram_bot.handlers.health_handler import (
            health_ping_command,
            health_status_command,
            health_summary_command,
        )

        application.add_handler(CommandHandler("health_status", health_status_command))
        application.add_handler(CommandHandler("health_summary", health_summary_command))
        application.add_handler(CommandHandler("health_ping", health_ping_command))
        logger.info("Health Check команды зарегистрированы")
    except ImportError as e:
        logger.warning("Не удалось импортировать health handler: %s", e)

    logger.info("Базовые команды зарегистрированы")

    # Minimal UI callback handlers (registered before general callback handler)
    application.add_handler(CallbackQueryHandler(handle_mode_selection_callback, pattern="^mode_"))
    application.add_handler(CallbackQueryHandler(handle_api_check_callback, pattern="^api_check"))
    application.add_handler(CallbackQueryHandler(handle_view_items_callback, pattern="^view_items"))

    # Auto-buy callback handlers
    try:
        from src.telegram_bot.handlers.auto_buy_handler import buy_now_callback, skip_item_callback

        application.add_handler(CallbackQueryHandler(buy_now_callback, pattern="^buy_now_"))
        application.add_handler(CallbackQueryHandler(skip_item_callback, pattern="^skip_item$"))
        logger.info("Auto-buy callback handlers зарегистрированы")
    except ImportError as e:
        logger.warning("Не удалось импортировать auto-buy callbacks: %s", e)

    # Autopilot callback handlers
    try:
        from src.telegram_bot.handlers.autopilot_handler import autopilot_start_confirmed_callback

        application.add_handler(
            CallbackQueryHandler(
                autopilot_start_confirmed_callback, pattern="^autopilot_start_confirmed$"
            )
        )
        logger.info("Autopilot callback handlers зарегистрированы")
    except ImportError as e:
        logger.warning("Не удалось импортировать autopilot callbacks: %s", e)

    # Enhanced Scanner handlers (MUST be before general callback handler)
    try:
        # Register enhanced scanner without bot_instance parameter
        # API client will be retrieved from bot_data when needed
        from src.telegram_bot.handlers.enhanced_scanner_handler import (
            handle_enhanced_scan,
            handle_enhanced_scan_help,
            handle_enhanced_scan_settings,
            show_enhanced_scanner_menu,
        )

        application.add_handler(
            CallbackQueryHandler(
                show_enhanced_scanner_menu,
                pattern="^enhanced_scanner_menu$",
            )
        )

        application.add_handler(
            CallbackQueryHandler(
                handle_enhanced_scan,
                pattern="^enhanced_scan_(csgo|dota2|rust|tf2)$",
            )
        )

        application.add_handler(
            CallbackQueryHandler(
                handle_enhanced_scan_settings,
                pattern="^enhanced_scan_settings$",
            )
        )

        application.add_handler(
            CallbackQueryHandler(
                handle_enhanced_scan_help,
                pattern="^enhanced_scan_help$",
            )
        )

        logger.info("✅ Enhanced Scanner handlers registered")
    except Exception as e:
        logger.warning("Не удалось зарегистрировать Enhanced Scanner handlers: %s", e)

    # ========================================================================
    # PHASE 2 REFACTORING: Modern Callback Router
    # ========================================================================
    # Initialize callback router and store in bot_data
    logger.info("Initializing Phase 2 callback router...")
    try:
        callback_router = create_callback_router()
        application.bot_data["callback_router"] = callback_router
        logger.info(
            "✅ Callback router initialized with %d handlers", len(callback_router._exact_handlers)
        )

        # Register new router-based callback handler
        application.add_handler(CallbackQueryHandler(button_callback_handler_v2))
        logger.info("✅ Router-based callback handler registered")
    except Exception as e:
        logger.error("Failed to initialize callback router, falling back to old handler: %s", e)
        # Fallback to old handler if new one fails
        application.add_handler(CallbackQueryHandler(button_callback_handler))
        logger.warning("⚠️ Using legacy callback handler (973 lines)")

    logger.info("Callback-обработчики зарегистрированы")

    # Minimal UI message router (higher priority for minimal menu buttons)
    application.add_handler(
        MessageHandler(
            filters.Regex(
                "^(🤖 Automatic Arbitrage|📦 View Items|⚙️ Detailed Settings|🔌 API Check)$"
            ),
            minimal_menu_router,
        ),
    )

    logger.info("Minimal UI message router registered")

    # ИСПРАВЛЕНО: Обработчик handle_text_buttons закомментирован
    # чтобы не конфликтовать с main_keyboard
    # Удален широкий фильтр filters.TEXT & ~filters.COMMAND
    # который перехватывал все текстовые сообщения включая "🎯 Таргеты"
    # application.add_handler(
    #     MessageHandler(
    #         filters.TEXT & ~filters.COMMAND,
    #         handle_text_buttons,
    #     ),
    # )

    logger.info("Обработчики текстовых сообщений зарегистрированы")

    # Регистрация дополнительных обработчиков
    try:
        from src.telegram_bot.handlers.scanner_handler import register_scanner_handlers

        register_scanner_handlers(application)
        logger.info("Scanner обработчики зарегистрированы")
    except ImportError as e:
        logger.warning("Не удалось импортировать scanner обработчики: %s", e)

    try:
        from src.telegram_bot.handlers.market_alerts_handler import register_alerts_handlers

        register_alerts_handlers(application)
        logger.info("Market alerts обработчики зарегистрированы")
    except ImportError as e:
        logger.warning("Не удалось импортировать market_alerts обработчики: %s", e)

    try:
        from src.telegram_bot.handlers.market_analysis_handler import (
            register_market_analysis_handlers,
        )

        register_market_analysis_handlers(application)
        logger.info("Market analysis обработчики зарегистрированы")
    except ImportError as e:
        logger.warning("Не удалось импортировать market_analysis обработчики: %s", e)

    try:
        from src.telegram_bot.handlers.intramarket_arbitrage_handler import (
            register_intramarket_handlers,
        )

        register_intramarket_handlers(application)
        logger.info("Intramarket arbitrage обработчики зарегистрированы")
    except ImportError as e:
        logger.warning("Не удалось импортировать intramarket_arbitrage обработчики: %s", e)

    # NOTE: Временно отключено - функции register_* не реализованы в этих модулях
    # TODO: Добавить функции регистрации в будущих обновлениях
    # try:
    #     from src.telegram_bot.handlers.game_filter_handlers import (
    #         register_game_filter_handlers,
    #     )
    #
    #     register_game_filter_handlers(application)
    #     logger.info("Game filter обработчики зарегистрированы")
    # except ImportError as e:
    #     logger.warning(
    #         "Не удалось импортировать game_filter обработчики: %s",
    #         e,
    #     )
    #
    # try:
    #     from src.telegram_bot.handlers.liquidity_settings_handler import (
    #         register_liquidity_handlers,
    #     )
    #
    #     register_liquidity_handlers(application)
    #     logger.info("Liquidity settings обработчики зарегистрированы")
    # except ImportError as e:
    #     logger.warning(
    #         "Не удалось импортировать liquidity_settings обработчики: %s",
    #         e,
    #     )
    #
    # try:
    #     from src.telegram_bot.handlers.settings_handlers import (
    #         register_localization_handlers,
    #     )
    #
    #     register_localization_handlers(application)
    #     logger.info("Localization обработчики зарегистрированы")
    # except ImportError as e:
    #     logger.warning(
    #         "Не удалось импортировать localization обработчики: %s",
    #         e,
    #     )

    try:
        from src.telegram_bot.handlers.target_handler import register_target_handlers

        register_target_handlers(application)
        logger.info("Target обработчики зарегистрированы")
    except ImportError as e:
        logger.warning("Не удалось импортировать target обработчики: %s", e)

    # Регистрация Dashboard handlers
    try:
        from src.telegram_bot.handlers.dashboard_handler import register_dashboard_handlers

        register_dashboard_handlers(application)
        logger.info("Dashboard обработчики зарегистрированы")
    except ImportError as e:
        logger.warning("Не удалось импортировать dashboard обработчики: %s", e)

    # Регистрация Notification Filters handlers
    # NOTE: Временно отключено - функция register_* не реализована
    # TODO: Добавить функцию регистрации в будущих обновлениях
    # try:
    #     from src.telegram_bot.handlers.notification_filters_handler import (
    #         register_notification_filter_handlers,
    #     )
    #
    #     register_notification_filter_handlers(application)
    #     logger.info("Notification filter обработчики зарегистрированы")
    # except ImportError as e:
    #     logger.warning(
    #         "Не удалось импортировать notification filter обработчики: %s", e
    #     )

    # Регистрация Notification Digest handlers
    try:
        from src.telegram_bot.handlers.notification_digest_handler import (
            register_notification_digest_handlers,
        )

        register_notification_digest_handlers(application)
        logger.info("Notification digest обработчики зарегистрированы")
    except ImportError as e:
        logger.warning(
            "Не удалось импортировать notification digest обработчики: %s",
            e,
        )

    # Регистрация DMarket handlers, если доступны API ключи
    try:
        dmarket_api = application.bot_data.get("dmarket_api")
        if dmarket_api:
            from src.telegram_bot.handlers.dmarket_handlers import register_dmarket_handlers

            register_dmarket_handlers(
                application,
                public_key=dmarket_api.public_key,
                secret_key=dmarket_api.secret_key,
                api_url=dmarket_api.api_url,
            )
            logger.info("DMarket обработчики зарегистрированы")
    except (ImportError, AttributeError) as e:
        logger.warning(
            "Не удалось зарегистрировать DMarket обработчики: %s",
            e,
        )

    # Регистрация Steam Arbitrage handlers (NEW - FIX)
    try:
        from src.telegram_bot.commands.steam_arbitrage_commands import (
            steam_arbitrage_start,
            steam_arbitrage_status,
            steam_arbitrage_stop,
        )

        application.add_handler(CommandHandler("steam_arbitrage_start", steam_arbitrage_start))
        application.add_handler(CommandHandler("steam_arbitrage_stop", steam_arbitrage_stop))
        application.add_handler(CommandHandler("steam_arbitrage_status", steam_arbitrage_status))
        logger.info("Steam Arbitrage команды зарегистрированы")
    except ImportError as e:
        logger.warning("Не удалось импортировать Steam Arbitrage команды: %s", e)

    # Extended Statistics handlers (/stats_full, /portfolio)
    try:
        from src.telegram_bot.handlers.extended_stats_handler import get_extended_stats_handlers

        for handler in get_extended_stats_handlers():
            application.add_handler(handler)
        logger.info("Extended Stats команды зарегистрированы (/stats_full, /portfolio)")
    except ImportError as e:
        logger.warning("Не удалось импортировать Extended Stats команды: %s", e)

    # Market Sentiment handlers (/market, /smart, /x5)
    try:
        from src.telegram_bot.handlers.market_sentiment_handler import (
            register_market_sentiment_handlers,
        )

        register_market_sentiment_handlers(application)
        logger.info("Market Sentiment команды зарегистрированы (/market, /smart, /x5)")
    except ImportError as e:
        logger.warning("Не удалось импортировать Market Sentiment команды: %s", e)

    # Intelligent Hold handlers (/hold)
    try:
        from src.telegram_bot.handlers.intelligent_hold_handler import (
            register_intelligent_hold_handlers,
        )

        register_intelligent_hold_handlers(application)
        logger.info("Intelligent Hold команды зарегистрированы (/hold)")
    except ImportError as e:
        logger.warning("Не удалось импортировать Intelligent Hold команды: %s", e)

    # AI Price Predictor handlers (/ai_train, /ai_status, /ai_scan, /ai_analyze)
    try:
        from src.telegram_bot.handlers.ai_handler import register_ai_handlers

        register_ai_handlers(application)
        logger.info("AI Price Predictor команды зарегистрированы (/ai_train, /ai_status, /ai_scan)")
    except ImportError as e:
        logger.warning("Не удалось импортировать AI handler команды: %s", e)

    logger.info("Все обработчики успешно зарегистрированы")


__all__ = ["register_all_handlers"]
