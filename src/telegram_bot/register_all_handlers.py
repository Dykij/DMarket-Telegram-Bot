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
from src.telegram_bot.commands.test_sentry_command import test_sentry_command, test_sentry_info
from src.telegram_bot.handlers.callbacks import button_callback_handler
from src.telegram_bot.handlers.commands import (
    arbitrage_command,
    dashboard_command,
    dmarket_status_command,
    handle_text_buttons,
    help_command,
    markets_command,
    start_command,
    webapp_command,
)


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

    # Sentry тестирование (только для отладки и администраторов)
    application.add_handler(CommandHandler("test_sentry", test_sentry_command))
    application.add_handler(CommandHandler("sentry_info", test_sentry_info))

    # Backtesting команды
    application.add_handler(CommandHandler("backtest", backtest_command))
    application.add_handler(CommandHandler("backtest_help", backtest_help))

    logger.info("Базовые команды зарегистрированы")

    # Регистрация общего callback-обработчика
    application.add_handler(CallbackQueryHandler(button_callback_handler))

    logger.info("Callback-обработчики зарегистрированы")

    # Регистрация обработчиков текстовых сообщений (для постоянной клавиатуры)
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_text_buttons,
        ),
    )

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

    logger.info("Все обработчики успешно зарегистрированы")


__all__ = ["register_all_handlers"]
