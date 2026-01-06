"""AI Training Handler for Telegram Bot.

This module provides Telegram commands for:
- /ai_train - Train the AI price prediction model
- /ai_status - Check AI model status and data collection progress
- /ai_scan - Run AI-powered smart scan

Usage:
    Register handlers in your bot initialization:
    ```python
    from src.telegram_bot.handlers.ai_handler import register_ai_handlers
    register_ai_handlers(application)
    ```
"""

import logging
from typing import TYPE_CHECKING

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes


if TYPE_CHECKING:
    from telegram.ext import Application

logger = logging.getLogger(__name__)


async def ai_train_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /ai_train command - Train the AI price prediction model.

    This command triggers training of the RandomForest model on collected
    market data. Requires at least 100 data points in market_history.csv.

    Usage: /ai_train
    """
    if not update.message:
        return

    user_id = update.effective_user.id if update.effective_user else 0
    logger.info("ai_train_command", user_id=user_id)

    await update.message.reply_text(
        "🤖 <b>Запуск обучения AI модели...</b>\n\n"
        "Это может занять несколько минут.",
        parse_mode="HTML",
    )

    try:
        from src.ai.price_predictor import PricePredictor

        predictor = PricePredictor()
        result = predictor.train_model()

        await update.message.reply_text(
            f"🤖 <b>Результат обучения AI:</b>\n\n{result}",
            parse_mode="HTML",
        )

        # Log training result
        logger.info(
            "ai_model_trained",
            user_id=user_id,
            result=result,
        )

    except ImportError as e:
        error_msg = (
            "❌ <b>Ошибка:</b> Отсутствуют зависимости для AI.\n\n"
            f"Установите: <code>pip install scikit-learn pandas numpy scipy joblib</code>\n\n"
            f"Детали: {e}"
        )
        await update.message.reply_text(error_msg, parse_mode="HTML")

    except Exception as e:
        error_msg = f"❌ <b>Ошибка обучения:</b>\n\n{e}"
        await update.message.reply_text(error_msg, parse_mode="HTML")
        logger.exception("ai_train_failed", error=str(e))


async def ai_status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /ai_status command - Check AI model and data status.

    Shows:
    - Model training status
    - Number of known items
    - Data collection progress
    - Recommendation on next steps

    Usage: /ai_status
    """
    if not update.message:
        return

    user_id = update.effective_user.id if update.effective_user else 0
    logger.info("ai_status_command", user_id=user_id)

    try:
        from src.ai.price_predictor import PricePredictor
        from src.dmarket.market_data_logger import MarketDataLogger

        predictor = PricePredictor()
        model_info = predictor.get_model_info()

        # Get data status
        data_logger = MarketDataLogger(api=None)  # type: ignore
        data_status = data_logger.get_data_status()

        # Build status message
        status_parts = ["🤖 <b>AI Status</b>\n"]

        # Model status
        if model_info["is_trained"]:
            status_parts.append(
                f"✅ Модель обучена\n"
                f"📦 Известных предметов: {model_info.get('known_items_count', 'N/A')}\n"
            )
        else:
            status_parts.append("❌ Модель не обучена\n")

        status_parts.extend([
            "",  # Empty line
            "<b>📊 Данные для обучения:</b>\n",
        ])

        if data_status["exists"]:
            status_parts.append(
                f"📄 Файл: {data_status['path']}\n"
                f"📈 Записей: {data_status['rows']}\n"
            )

            if data_status["ready_for_training"]:
                status_parts.append("✅ Достаточно данных для обучения\n")
            else:
                remaining = 100 - data_status["rows"]
                status_parts.append(
                    f"⏳ Нужно еще {remaining} записей\n"
                )
        else:
            status_parts.append(
                "❌ Файл данных не найден\n"
                "💡 Запустите бота в режиме логгера на 48 часов\n"
            )

        status_parts.extend([
            "",
            "<b>💡 Рекомендации:</b>\n",
        ])

        if not data_status["exists"] or data_status["rows"] < 100:
            status_parts.append(
                "1. Подождите 48 часов для сбора данных\n"
                "2. Затем выполните /ai_train\n"
            )
        elif not model_info["is_trained"]:
            status_parts.append(
                "1. Выполните /ai_train для обучения\n"
                "2. После обучения используйте /ai_scan\n"
            )
        else:
            status_parts.append(
                "✅ Система готова к работе\n"
                "Используйте /ai_scan для поиска\n"
            )

        await update.message.reply_text(
            "".join(status_parts),
            parse_mode="HTML",
        )

    except Exception as e:
        await update.message.reply_text(
            f"❌ <b>Ошибка получения статуса:</b>\n\n{e}",
            parse_mode="HTML",
        )
        logger.exception("ai_status_failed", error=str(e))


async def ai_scan_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /ai_scan command - Run AI-powered smart scan.

    Performs a single scan using the Smart Scanner with AI validation.
    Finds and reports items with potential profit opportunities.

    Usage: /ai_scan [include_locked]
        include_locked - Include items with trade ban (default: no)
    """
    if not update.message:
        return

    user_id = update.effective_user.id if update.effective_user else 0
    logger.info("ai_scan_command", user_id=user_id)

    # Parse arguments
    args = context.args or []
    include_locked = "locked" in " ".join(args).lower()

    await update.message.reply_text(
        "🔍 <b>Запуск AI-сканирования...</b>\n\n"
        f"📦 Включить предметы с локом: {'Да' if include_locked else 'Нет'}",
        parse_mode="HTML",
    )

    try:
        from src.ai.price_predictor import PricePredictor
        from src.dmarket.dmarket_api import DMarketAPI
        from src.dmarket.smart_scanner import SmartScanner, SmartScannerConfig

        # Get API client from context
        api = getattr(context.application, "dmarket_api", None)
        if not api:
            # Create new API client
            import os

            api = DMarketAPI(
                public_key=os.getenv("DMARKET_PUBLIC_KEY", ""),
                secret_key=os.getenv("DMARKET_SECRET_KEY", ""),
            )

        # Initialize predictor
        predictor = PricePredictor()

        if not predictor.is_trained:
            await update.message.reply_text(
                "⚠️ AI модель не обучена.\n\n"
                "Выполните /ai_train сначала.",
                parse_mode="HTML",
            )
            return

        # Configure scanner
        config = SmartScannerConfig(
            allow_trade_ban=include_locked,
            max_lock_days=8 if include_locked else 0,
            min_profit_percent=15.0 if include_locked else 5.0,
            enable_ai=True,
            dry_run=True,  # Always dry run from Telegram
        )

        # Create scanner
        scanner = SmartScanner(api=api, predictor=predictor, config=config)

        # Run single scan
        results = await scanner.scan_once()

        # Filter profitable results
        opportunities = [r for r in results if r.should_buy]

        if not opportunities:
            await update.message.reply_text(
                "📭 <b>Результат сканирования:</b>\n\n"
                "Арбитражных возможностей не найдено.\n\n"
                f"Проанализировано предметов: {len(results)}",
                parse_mode="HTML",
            )
            return

        # Format results
        message_parts = [
            f"🎯 <b>Найдено {len(opportunities)} возможностей!</b>\n\n"
        ]

        for i, opp in enumerate(opportunities[:5], 1):  # Show top 5
            lock_info = f"⏳ Лок: {opp.lock_days}д" if opp.lock_days > 0 else "✅ Без лока"

            message_parts.append(
                f"<b>{i}. {opp.title[:50]}...</b>\n"
                f"💰 Цена: ${float(opp.market_price):.2f}\n"
                f"📈 Профит: +{opp.profit_percent:.1f}% (${float(opp.profit_usd):.2f})\n"
                f"{lock_info}\n"
                f"💡 {opp.reason}\n\n"
            )

        if len(opportunities) > 5:
            message_parts.append(
                f"<i>...и еще {len(opportunities) - 5} возможностей</i>\n"
            )

        await update.message.reply_text(
            "".join(message_parts),
            parse_mode="HTML",
        )

        logger.info(
            "ai_scan_completed",
            user_id=user_id,
            opportunities=len(opportunities),
            include_locked=include_locked,
        )

    except ImportError as e:
        await update.message.reply_text(
            f"❌ <b>Ошибка:</b> Отсутствуют зависимости.\n\n{e}",
            parse_mode="HTML",
        )

    except Exception as e:
        await update.message.reply_text(
            f"❌ <b>Ошибка сканирования:</b>\n\n{e}",
            parse_mode="HTML",
        )
        logger.exception("ai_scan_failed", error=str(e))


async def ai_analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /ai_analyze command - Analyze specific item with trade ban.

    Provides detailed analysis of an item to determine if it's worth
    buying even with a trade lock.

    Usage: /ai_analyze <item_name>
    """
    if not update.message:
        return

    user_id = update.effective_user.id if update.effective_user else 0

    # Get item name from arguments
    args = context.args or []
    if not args:
        await update.message.reply_text(
            "📝 <b>Использование:</b>\n\n"
            "/ai_analyze &lt;название предмета&gt;\n\n"
            "<b>Пример:</b>\n"
            "/ai_analyze AK-47 | Redline (Field-Tested)",
            parse_mode="HTML",
        )
        return

    item_name = " ".join(args)
    logger.info("ai_analyze_command", user_id=user_id, item=item_name)

    await update.message.reply_text(
        f"🔍 <b>Анализирую предмет:</b>\n\n"
        f"<code>{item_name}</code>",
        parse_mode="HTML",
    )

    try:
        from src.ai.price_predictor import PricePredictor

        predictor = PricePredictor()

        if not predictor.is_trained:
            await update.message.reply_text(
                "⚠️ AI модель не обучена.\n\n"
                "Выполните /ai_train сначала.",
                parse_mode="HTML",
            )
            return

        # Get raw prediction
        raw_price = predictor.get_raw_prediction(item_name)

        if raw_price is None:
            await update.message.reply_text(
                "❌ <b>Предмет не найден в базе AI</b>\n\n"
                "Этот предмет не встречался в данных обучения.\n"
                "Подождите пока бот соберет больше данных.",
                parse_mode="HTML",
            )
            return

        # Build analysis message
        message = (
            f"🤖 <b>AI Анализ предмета</b>\n\n"
            f"📦 <b>Предмет:</b>\n<code>{item_name}</code>\n\n"
            f"💵 <b>AI Справедливая цена:</b> ${raw_price:.2f}\n\n"
            f"<b>💡 Рекомендации:</b>\n"
            f"• Если рыночная цена ниже ${raw_price * 0.95:.2f} - покупка выгодна\n"
            f"• Если выше ${raw_price * 1.05:.2f} - переплата\n\n"
            f"⚠️ <i>AI предсказание не гарантирует прибыль</i>"
        )

        await update.message.reply_text(message, parse_mode="HTML")

    except Exception as e:
        await update.message.reply_text(
            f"❌ <b>Ошибка анализа:</b>\n\n{e}",
            parse_mode="HTML",
        )
        logger.exception("ai_analyze_failed", error=str(e))


def register_ai_handlers(application: "Application") -> None:
    """Register AI-related command handlers.

    Args:
        application: Telegram Application instance
    """
    application.add_handler(CommandHandler("ai_train", ai_train_command))
    application.add_handler(CommandHandler("ai_status", ai_status_command))
    application.add_handler(CommandHandler("ai_scan", ai_scan_command))
    application.add_handler(CommandHandler("ai_analyze", ai_analyze_command))

    logger.info("AI handlers registered")
