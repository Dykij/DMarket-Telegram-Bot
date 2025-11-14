"""Модуль для регистрации всех обработчиков Telegram бота.

Этот модуль объединяет регистрацию всех обработчиков команд, callback-запросов,
и других обработчиков для упрощения инициализации бота.
"""

import logging
from typing import TYPE_CHECKING

from telegram.ext import CallbackQueryHandler, CommandHandler, MessageHandler, filters

from src.telegram_bot.handlers.callbacks import button_callback_handler
from src.telegram_bot.handlers.commands import (
    arbitrage_command,
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
    application.add_handler(CommandHandler("arbitrage", arbitrage_command))
    application.add_handler(CommandHandler("dmarket", dmarket_status_command))
    application.add_handler(CommandHandler("status", dmarket_status_command))
    application.add_handler(CommandHandler("markets", markets_command))
    application.add_handler(CommandHandler("webapp", webapp_command))

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
        from src.telegram_bot.handlers.enhanced_arbitrage_handler import (
            register_enhanced_arbitrage_handlers,
        )

        register_enhanced_arbitrage_handlers(application)
        logger.info("Enhanced arbitrage обработчики зарегистрированы")
    except ImportError as e:
        logger.warning(f"Не удалось импортировать enhanced_arbitrage обработчики: {e}")

    try:
        from src.telegram_bot.handlers.scanner_handler import register_scanner_handlers

        register_scanner_handlers(application)
        logger.info("Scanner обработчики зарегистрированы")
    except ImportError as e:
        logger.warning(f"Не удалось импортировать scanner обработчики: {e}")

    try:
        from src.telegram_bot.handlers.market_alerts_handler import (
            register_alerts_handlers,
        )

        register_alerts_handlers(application)
        logger.info("Market alerts обработчики зарегистрированы")
    except ImportError as e:
        logger.warning(f"Не удалось импортировать market_alerts обработчики: {e}")

    try:
        from src.telegram_bot.handlers.market_analysis_handler import (
            register_market_analysis_handlers,
        )

        register_market_analysis_handlers(application)
        logger.info("Market analysis обработчики зарегистрированы")
    except ImportError as e:
        logger.warning(f"Не удалось импортировать market_analysis обработчики: {e}")

    try:
        from src.telegram_bot.handlers.intramarket_arbitrage_handler import (
            register_intramarket_handlers,
        )

        register_intramarket_handlers(application)
        logger.info("Intramarket arbitrage обработчики зарегистрированы")
    except ImportError as e:
        logger.warning(f"Не удалось импортировать intramarket_arbitrage обработчики: {e}")

    try:
        from src.telegram_bot.settings_handlers import register_localization_handlers

        register_localization_handlers(application)
        logger.info("Localization обработчики зарегистрированы")
    except ImportError as e:
        logger.warning(f"Не удалось импортировать localization обработчики: {e}")

    try:
        from src.telegram_bot.handlers.target_handler import register_target_handlers

        register_target_handlers(application)
        logger.info("Target обработчики зарегистрированы")
    except ImportError as e:
        logger.warning(f"Не удалось импортировать target обработчики: {e}")

    # Регистрация DMarket handlers, если доступны API ключи
    try:
        dmarket_api = application.bot_data.get("dmarket_api")
        if dmarket_api:
            from src.telegram_bot.handlers.dmarket_handlers import (
                register_dmarket_handlers,
            )

            register_dmarket_handlers(
                application,
                public_key=dmarket_api.public_key,
                secret_key=dmarket_api.secret_key,
                api_url=dmarket_api.api_url,
            )
            logger.info("DMarket обработчики зарегистрированы")
    except Exception as e:
        logger.warning(f"Не удалось зарегистрировать DMarket обработчики: {e}")

    logger.info("Все обработчики успешно зарегистрированы")


__all__ = ["register_all_handlers"]

