"""
Market Sentiment Handler for Telegram Bot.

Handles commands and callbacks for:
- Market status display
- X5 hunting mode
- Smart arbitrage with adaptive limits
"""

import structlog
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes

logger = structlog.get_logger(__name__)


async def show_market_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show current market status and sentiment analysis."""
    query = update.callback_query
    if query:
        await query.answer()

    # Get market sentiment analyzer from context
    sentiment = context.application.bot_data.get("market_sentiment")
    # api_client available in bot_data for future API calls in sentiment analysis
    _api_client = context.application.bot_data.get("dmarket_api")  # noqa: F841

    if not sentiment:
        message = (
            "📊 *Анализатор рынка*\n\n"
            "⚠️ Модуль Market Sentiment не инициализирован.\n"
            "Добавьте `market_sentiment` в bot_data при запуске."
        )
    else:
        message = sentiment.get_status_message()

        # Add X5 opportunities if available
        if sentiment.x5_opportunities:
            message += f"\n\n🔥 *Найдено X5 возможностей:* {len(sentiment.x5_opportunities)}"

    # Keyboard
    keyboard = [
        [
            InlineKeyboardButton("🔄 Обновить", callback_data="refresh_market_status"),
            InlineKeyboardButton("🔥 X5 возможности", callback_data="show_x5_opportunities"),
        ],
        [
            InlineKeyboardButton("📊 Индикаторы", callback_data="show_market_indicators"),
            InlineKeyboardButton("⚙️ Настройки", callback_data="market_sentiment_settings"),
        ],
        [
            InlineKeyboardButton("◀️ Назад", callback_data="smart_menu"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if query:
        await query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )
    else:
        await update.effective_message.reply_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )


async def show_x5_opportunities(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show current X5 hunting opportunities."""
    query = update.callback_query
    if query:
        await query.answer()

    sentiment = context.application.bot_data.get("market_sentiment")

    if not sentiment:
        message = "⚠️ Market Sentiment не инициализирован."
    elif not sentiment.x5_opportunities:
        message = (
            "🔍 *X5 Возможности*\n\n"
            "Пока не найдено потенциальных X5 возможностей.\n\n"
            "Бот сканирует рынок каждые 15 минут в поисках:\n"
            "• Всплесков объема (10x+ обычного)\n"
            "• Значительных падений цен (20%+)\n"
            "• Лимитированных коллекций\n\n"
            "💡 *Совет:* Включите режим X5 Hunt для автоматического отслеживания."
        )
    else:
        message = sentiment.get_x5_opportunities_message()

    keyboard = [
        [
            InlineKeyboardButton("🔄 Сканировать снова", callback_data="scan_x5_now"),
            InlineKeyboardButton("⚙️ Настройки X5", callback_data="x5_hunt_settings"),
        ],
        [
            InlineKeyboardButton("◀️ К статусу рынка", callback_data="show_market_status"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if query:
        await query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )
    else:
        await update.effective_message.reply_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )


async def toggle_x5_hunt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Toggle X5 hunt mode on/off."""
    query = update.callback_query
    await query.answer()

    sentiment = context.application.bot_data.get("market_sentiment")

    if not sentiment:
        await query.answer("⚠️ Market Sentiment не инициализирован", show_alert=True)
        return

    # Toggle hunt mode
    sentiment.high_risk_hunt = not sentiment.high_risk_hunt
    status = "ВКЛ 🟢" if sentiment.high_risk_hunt else "ВЫКЛ 🔴"

    await query.answer(f"X5 Охота: {status}")

    # Refresh smart menu
    await show_smart_menu(update, context)


async def show_smart_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show smart trading menu with adaptive limits."""
    query = update.callback_query
    if query:
        await query.answer()

    # Get components
    api_client = context.application.bot_data.get("dmarket_api")
    sentiment = context.application.bot_data.get("market_sentiment")
    money_manager = context.application.bot_data.get("money_manager")

    # Get current balance
    balance = 0.0
    try:
        if api_client and hasattr(api_client, "get_balance"):
            balance_data = await api_client.get_balance()
            if isinstance(balance_data, dict):
                # DMarket API returns 'balance' field in dollars directly
                try:
                    balance = float(balance_data.get("balance", 0))
                except (ValueError, TypeError):
                    balance = 0.0
            else:
                balance = 0.0
    except Exception as e:
        logger.warning("balance_fetch_error", error=str(e))

    # Get market status
    market_status = "Загрузка..."
    hunt_mode = False
    if sentiment:
        if sentiment.current_health:
            state_text = {
                "stable": "✅ Стабилен",
                "volatile": "⚡ Волатилен",
                "crash": "🔴 ПАНИКА",
                "recovery": "📈 Восстановление",
                "bull_run": "🚀 Рост",
                "sale_period": "🎉 Распродажа!",
            }
            market_status = state_text.get(sentiment.current_health.state.value, "❓ Неизвестно")
        hunt_mode = sentiment.high_risk_hunt

    # Get adaptive limits
    limits_info = ""
    if money_manager and balance > 0:
        limits = money_manager.calculate_limits(balance)
        limits_info = f"\n📊 Макс. цена предмета: ${limits.get('max_price', 0):.2f}"
        limits_info += f"\n🎯 Мин. ROI: {limits.get('target_roi', 15):.0f}%"

    formatted_bal = f"${balance:,.2f}" if balance > 0 else "Загрузка..."
    hunt_status = "ВКЛ 🟢" if hunt_mode else "ВЫКЛ 🔴"

    message = (
        f"🚀 *Smart Arbitrage*\n\n"
        f"💰 *Баланс:* {formatted_bal}\n"
        f"📊 *Рынок:* {market_status}\n"
        f"🔥 *X5 Охота:* {hunt_status}"
        f"{limits_info}\n\n"
        f"Нажмите кнопку запуска для начала умного арбитража.\n"
        f"Бот автоматически адаптирует лимиты под ваш баланс."
    )

    keyboard = [
        [
            InlineKeyboardButton(
                text=f"🚀 ЗАПУСК ({formatted_bal})",
                callback_data="start_smart_arbitrage",
            ),
        ],
        [
            InlineKeyboardButton(text=f"📊 {market_status}", callback_data="show_market_status"),
            InlineKeyboardButton(text=f"🔥 X5: {hunt_status}", callback_data="toggle_x5_hunt"),
        ],
        [
            InlineKeyboardButton(text="📈 Стата по играм", callback_data="stats_by_games"),
            InlineKeyboardButton(text="🔄 Обновить", callback_data="refresh_smart_menu"),
        ],
        [
            InlineKeyboardButton(text="✅ WhiteList", callback_data="manage_whitelist"),
            InlineKeyboardButton(text="🚫 BlackList", callback_data="manage_blacklist"),
        ],
        [
            InlineKeyboardButton(text="♻️ Репрайсинг", callback_data="toggle_repricing"),
            InlineKeyboardButton(text="⚙️ Лимиты", callback_data="config_limits"),
        ],
        [
            InlineKeyboardButton(text="🛑 СТОП", callback_data="panic_stop"),
        ],
        [
            InlineKeyboardButton(text="◀️ Главное меню", callback_data="main_menu"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if query:
        await query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )
    else:
        await update.effective_message.reply_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )


async def start_smart_arbitrage(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start smart arbitrage with adaptive limits."""
    query = update.callback_query
    await query.answer("🚀 Запуск Smart Arbitrage...")

    api_client = context.application.bot_data.get("dmarket_api")
    sentiment = context.application.bot_data.get("market_sentiment")
    money_manager = context.application.bot_data.get("money_manager")
    scanner_manager = context.application.bot_data.get("scanner_manager")

    # Check components
    if not api_client or not scanner_manager:
        await query.edit_message_text(
            "⚠️ Необходимые компоненты не инициализированы.\nПроверьте логи запуска бота."
        )
        return

    try:
        # Get balance - DMarket API returns 'balance' field in dollars directly
        balance_data = await api_client.get_balance()
        if isinstance(balance_data, dict):
            try:
                balance = float(balance_data.get("balance", 0))
            except (ValueError, TypeError):
                balance = 0.0
        else:
            balance = 0.0

        if balance < 1.0:
            await query.edit_message_text(
                f"⚠️ Недостаточный баланс: ${balance:.2f}\n"
                "Минимальный баланс для Smart Arbitrage: $1.00"
            )
            return

        # Calculate adaptive limits
        base_limits = {}
        if money_manager:
            base_limits = money_manager.calculate_limits(balance)
        else:
            # Fallback limits
            base_limits = {
                "max_price": balance * 0.25,
                "min_price": max(0.10, balance * 0.005),
                "target_roi": 15.0 if balance < 100 else 10.0,
            }

        # Adjust for market conditions
        if sentiment and sentiment.current_health:
            adjusted = sentiment.get_adjusted_limits(base_limits, balance)
        else:
            adjusted = base_limits

        # Start scanner with adjusted limits
        message = (
            f"✅ *Smart Arbitrage запущен!*\n\n"
            f"💰 Баланс: ${balance:.2f}\n"
            f"📊 Макс. цена: ${adjusted.get('max_price', 0):.2f}\n"
            f"🎯 Мин. ROI: {adjusted.get('target_roi', 15):.0f}%\n"
        )

        if adjusted.get("pause_normal_buying"):
            message += "\n⚠️ *Режим защиты активен!* Обычные закупки приостановлены."

        if adjusted.get("speculative_budget", 0) > 0:
            message += f"\n🔥 X5 бюджет: ${adjusted['speculative_budget']:.2f}"

        message += (
            "\n\nБот начал сканирование рынка. Уведомления о сделках будут приходить автоматически."
        )

        keyboard = [
            [
                InlineKeyboardButton("📊 Статус", callback_data="smart_status"),
                InlineKeyboardButton("🛑 Остановить", callback_data="stop_smart_arbitrage"),
            ],
            [
                InlineKeyboardButton("◀️ Меню", callback_data="smart_menu"),
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )

        logger.info(
            "smart_arbitrage_started",
            balance=balance,
            max_price=adjusted.get("max_price"),
            target_roi=adjusted.get("target_roi"),
        )

    except Exception as e:
        logger.exception("smart_arbitrage_start_error", error=str(e))
        await query.edit_message_text(
            f"❌ Ошибка запуска: {e!s}\n\nПроверьте подключение к DMarket API."
        )


async def scan_x5_now(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manually trigger X5 opportunity scan."""
    query = update.callback_query
    await query.answer("🔍 Сканирование X5 возможностей...")

    sentiment = context.application.bot_data.get("market_sentiment")

    if not sentiment:
        await query.answer("⚠️ Market Sentiment не инициализирован", show_alert=True)
        return

    try:
        # Run scan
        opportunities = await sentiment.scan_for_x5_opportunities()

        if opportunities:
            message = sentiment.get_x5_opportunities_message()
        else:
            message = (
                "🔍 *Сканирование завершено*\n\n"
                "X5 возможностей не найдено.\n\n"
                "Критерии поиска:\n"
                "• Объем торгов 5x+ от нормы\n"
                "• Падение цены 20%+ от средней\n"
                "• Уверенность 60%+"
            )

        keyboard = [
            [
                InlineKeyboardButton("🔄 Сканировать снова", callback_data="scan_x5_now"),
            ],
            [
                InlineKeyboardButton("◀️ Назад", callback_data="show_market_status"),
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )

    except Exception as e:
        logger.exception("x5_scan_error", error=str(e))
        await query.answer(f"❌ Ошибка: {e!s}", show_alert=True)


def register_market_sentiment_handlers(application) -> None:
    """Register all market sentiment handlers."""
    # Commands
    application.add_handler(CommandHandler("market", show_market_status))
    application.add_handler(CommandHandler("smart", show_smart_menu))
    application.add_handler(CommandHandler("x5", show_x5_opportunities))

    # Callbacks
    application.add_handler(
        CallbackQueryHandler(
            show_market_status,
            pattern="^(show_market_status|refresh_market_status)$",
        )
    )
    application.add_handler(
        CallbackQueryHandler(
            show_x5_opportunities,
            pattern="^show_x5_opportunities$",
        )
    )
    application.add_handler(
        CallbackQueryHandler(
            toggle_x5_hunt,
            pattern="^toggle_x5_hunt$",
        )
    )
    application.add_handler(
        CallbackQueryHandler(
            show_smart_menu,
            pattern="^(smart_menu|refresh_smart_menu)$",
        )
    )
    application.add_handler(
        CallbackQueryHandler(
            start_smart_arbitrage,
            pattern="^start_smart_arbitrage$",
        )
    )
    application.add_handler(
        CallbackQueryHandler(
            scan_x5_now,
            pattern="^scan_x5_now$",
        )
    )

    logger.info("market_sentiment_handlers_registered")
