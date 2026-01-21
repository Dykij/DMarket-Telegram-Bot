"""
Telegram handler for Intelligent Hold recommendations.

Provides commands and callbacks for viewing hold/sell recommendations
based on upcoming market events.
"""

import logging
from typing import TYPE_CHECKING

from telegram import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes


if TYPE_CHECKING:
    from src.dmarket.intelligent_hold import IntelligentHoldManager


logger = logging.getLogger(__name__)


async def hold_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    /hold - Show intelligent hold recommendations for inventory.
    """
    if not update.effective_user:
        return

    try:
        # Import here to avoid circular imports
        from src.dmarket.intelligent_hold import get_hold_manager

        hold_manager = get_hold_manager()

        # Get upcoming events
        upcoming_events = hold_manager._get_upcoming_events(days_ahead=14)

        message = "🎯 **Intelligent Hold - Анализ рынка**\n\n"

        if upcoming_events:
            message += "📅 **Ближайшие события:**\n"
            for event in upcoming_events[:5]:
                impact_emoji = "📈" if event.expected_impact > 0 else "📉"
                impact_pct = event.expected_impact * 100
                message += (
                    f"\n{impact_emoji} **{event.name}**\n"
                    f"   ⏰ Через {event.days_until} дней\n"
                    f"   📊 Ожидаемое влияние: {impact_pct:+.0f}%\n"
                )
        else:
            message += "📅 Нет значимых событий в ближайшие 14 дней\n"

        message += "\n💡 Используйте кнопки ниже для анализа предметов:"

        keyboard = [
            [
                InlineKeyboardButton("📦 Анализ инвентаря", callback_data="hold_analyze_inventory"),
                InlineKeyboardButton("🔍 Проверить предмет", callback_data="hold_check_item"),
            ],
            [
                InlineKeyboardButton("📅 События CS2", callback_data="hold_events_csgo"),
                InlineKeyboardButton("📅 События Dota2", callback_data="hold_events_dota2"),
            ],
            [
                InlineKeyboardButton("⚙️ Настройки Hold", callback_data="hold_settings"),
                InlineKeyboardButton("🔙 Назад", callback_data="main_menu"),
            ],
        ]

        await update.message.reply_text(
            message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
        )

    except Exception as e:
        logger.exception(f"Hold command error: {e}")
        await update.message.reply_text("❌ Ошибка при получении данных. Попробуйте позже.")


async def _handle_analyze_inventory(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    query: CallbackQuery,
    hold_manager: "IntelligentHoldManager",
) -> None:
    """Handle inventory analysis callback.

    Fetches user inventory from DMarket API and provides hold/sell recommendations.
    """
    dmarket_api = context.application.bot_data.get("dmarket_api")

    if not dmarket_api:
        await query.edit_message_text("❌ API не инициализирован")
        return

    await query.edit_message_text("⏳ Анализирую ваш инвентарь...")

    try:
        inventory_data = await dmarket_api.get_user_inventory(game_id="csgo", limit=50)
        items = inventory_data.get("objects", [])

        if not items:
            await query.edit_message_text(
                "📦 Ваш инвентарь пуст или недоступен.\n\n"
                "Используйте /scan для поиска предметов для покупки."
            )
            return

        formatted_items = [
            {
                "name": item.get("title", "Unknown"),
                "current_price": float(item.get("price", {}).get("USD", 0)) / 100,
                "buy_price": float(item.get("price", {}).get("USD", 0)) / 100,
                "days_held": 0,
            }
            for item in items[:20]
        ]

        analysis = await hold_manager.analyze_inventory(formatted_items, game="csgo")
        message = _format_inventory_analysis(analysis)

    except Exception as e:
        logger.exception(f"Inventory analysis error: {e}")
        message = f"❌ Ошибка анализа: {str(e)[:100]}"

    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="hold_menu")]]
    await query.edit_message_text(
        message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
    )


def _format_inventory_analysis(analysis: dict) -> str:
    """Format inventory analysis results into a Telegram message."""
    message = "📊 **Анализ инвентаря**\n\n"
    message += f"📦 Всего предметов: {analysis['total_items']}\n"
    message += f"📈 Держать: {analysis['summary']['hold']}\n"
    message += f"💰 Продать: {analysis['summary']['sell']}\n"
    message += f"📊 Ср. ожидание: {analysis['summary']['avg_expected_change']:+.1f}%\n\n"

    message += "**Рекомендации:**\n"
    for rec in analysis["recommendations"][:10]:
        emoji = "📈" if rec["action"] == "hold" else "💰"
        action = "ДЕРЖАТЬ" if rec["action"] == "hold" else "ПРОДАТЬ"
        message += f"{emoji} {rec['item'][:25]}... - {action}\n"

    if analysis["upcoming_events"]:
        message += "\n**Учтенные события:**\n"
        for event in analysis["upcoming_events"][:3]:
            message += f"• {event['name']} ({event['days_until']}д)\n"

    return message


async def _handle_check_item(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    query: CallbackQuery,
    hold_manager: "IntelligentHoldManager",
) -> None:
    """Handle check item callback.

    Shows item selection interface for hold/sell analysis.
    """
    message = (
        "🔍 **Проверка предмета**\n\n"
        "Отправьте название предмета для анализа:\n"
        "Например: `AK-47 | Slate (Field-Tested)`\n\n"
        "Или выберите из популярных:"
    )

    keyboard = [
        [
            InlineKeyboardButton("Fracture Case", callback_data="hold_item_Fracture Case"),
            InlineKeyboardButton("Recoil Case", callback_data="hold_item_Recoil Case"),
        ],
        [
            InlineKeyboardButton(
                "AK-47 | Slate", callback_data="hold_item_AK-47 | Slate (Field-Tested)"
            ),
            InlineKeyboardButton(
                "Mann Co. Key", callback_data="hold_item_Mann Co. Supply Crate Key"
            ),
        ],
        [InlineKeyboardButton("🔙 Назад", callback_data="hold_menu")],
    ]

    await query.edit_message_text(
        message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def _handle_item_selection(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    query: CallbackQuery,
    hold_manager: "IntelligentHoldManager",
    item_name: str,
) -> None:
    """Handle specific item selection callback.

    Gets recommendation for the selected item.
    """
    rec = hold_manager.get_recommendation(
        item_name=item_name,
        current_price=10.0,  # Placeholder
        buy_price=9.0,  # Placeholder
        game="csgo",
        days_held=0,
    )

    message = hold_manager.format_telegram_message(rec)

    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="hold_check_item")]]
    await query.edit_message_text(
        message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def _handle_events_csgo(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    query: CallbackQuery,
    hold_manager: "IntelligentHoldManager",
) -> None:
    """Handle CS2/CSGO events callback.

    Shows upcoming CS2/CSGO market events.
    """
    events = hold_manager._get_upcoming_events(days_ahead=60, game="csgo")
    message = _format_events_message("CS2/CSGO", events)

    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="hold_menu")]]
    await query.edit_message_text(
        message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def _handle_events_dota2(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    query: CallbackQuery,
    hold_manager: "IntelligentHoldManager",
) -> None:
    """Handle Dota 2 events callback.

    Shows upcoming Dota 2 market events.
    """
    events = hold_manager._get_upcoming_events(days_ahead=60, game="dota2")
    message = _format_events_message("Dota 2", events)

    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="hold_menu")]]
    await query.edit_message_text(
        message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
    )


def _format_events_message(game_name: str, events: list) -> str:
    """Format events list into a Telegram message."""
    message = f"📅 **События {game_name} (60 дней)**\n\n"

    if not events:
        return message + "Нет запланированных событий"

    for event in events:
        impact_emoji = "📈" if event.expected_impact > 0 else "📉"
        status = "🔴 СЕЙЧАС" if event.is_active else f"⏰ {event.days_until}д"
        message += (
            f"{impact_emoji} **{event.name}**\n"
            f"   {status} | Влияние: {event.expected_impact * 100:+.0f}%\n\n"
        )

    return message


async def _handle_settings(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    query: CallbackQuery,
    hold_manager: "IntelligentHoldManager",
) -> None:
    """Handle settings callback.

    Shows current Intelligent Hold settings.
    """
    message = (
        "⚙️ **Настройки Intelligent Hold**\n\n"
        "📈 Мин. ожидаемый рост: 10%\n"
        "📉 Макс. срок удержания: 14 дней\n"
        "💰 Фиксация прибыли: при +20% ROI\n"
        "✂️ Стоп-лосс: 7 дней при <5% ROI\n\n"
        "Для изменения отредактируйте `config.yaml`"
    )

    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="hold_menu")]]
    await query.edit_message_text(
        message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def _handle_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    query: CallbackQuery,
    hold_manager: "IntelligentHoldManager",
) -> None:
    """Handle menu callback.

    Returns to the main hold menu.
    """
    upcoming_events = hold_manager._get_upcoming_events(days_ahead=14)

    message = "🎯 **Intelligent Hold - Анализ рынка**\n\n"

    if upcoming_events:
        message += "📅 **Ближайшие события:**\n"
        for event in upcoming_events[:3]:
            impact_emoji = "📈" if event.expected_impact > 0 else "📉"
            message += f"{impact_emoji} {event.name} (через {event.days_until}д)\n"

    keyboard = [
        [
            InlineKeyboardButton(
                "📦 Анализ инвентаря", callback_data="hold_analyze_inventory"
            ),
            InlineKeyboardButton("🔍 Проверить предмет", callback_data="hold_check_item"),
        ],
        [
            InlineKeyboardButton("📅 События CS2", callback_data="hold_events_csgo"),
            InlineKeyboardButton("📅 События Dota2", callback_data="hold_events_dota2"),
        ],
        [
            InlineKeyboardButton("⚙️ Настройки", callback_data="hold_settings"),
            InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu"),
        ],
    ]

    await query.edit_message_text(
        message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def hold_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle intelligent hold callbacks.

    Routes callback queries to appropriate handler functions.
    """
    query = update.callback_query
    if not query:
        return

    await query.answer()
    data = query.data

    try:
        from src.dmarket.intelligent_hold import get_hold_manager

        hold_manager = get_hold_manager()

        if data == "hold_analyze_inventory":
            await _handle_analyze_inventory(update, context, query, hold_manager)
        elif data == "hold_check_item":
            await _handle_check_item(update, context, query, hold_manager)
        elif data.startswith("hold_item_"):
            item_name = data.replace("hold_item_", "")
            await _handle_item_selection(update, context, query, hold_manager, item_name)
        elif data == "hold_events_csgo":
            await _handle_events_csgo(update, context, query, hold_manager)
        elif data == "hold_events_dota2":
            await _handle_events_dota2(update, context, query, hold_manager)
        elif data == "hold_settings":
            await _handle_settings(update, context, query, hold_manager)
        elif data == "hold_menu":
            await _handle_menu(update, context, query, hold_manager)

    except Exception as e:
        logger.exception(f"Hold callback error: {e}")
        await query.edit_message_text(f"❌ Ошибка: {str(e)[:100]}")


def register_intelligent_hold_handlers(application) -> None:
    """Register intelligent hold handlers with the application."""
    application.add_handler(CommandHandler("hold", hold_command))
    application.add_handler(CallbackQueryHandler(hold_callback_handler, pattern=r"^hold_"))
    logger.info("Intelligent Hold handlers registered")
