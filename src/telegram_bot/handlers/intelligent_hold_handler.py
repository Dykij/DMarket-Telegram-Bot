"""
Telegram handler for Intelligent Hold recommendations.

Provides commands and callbacks for viewing hold/sell recommendations
based on upcoming market events.
"""

import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes


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
        logger.error(f"Hold command error: {e}")
        await update.message.reply_text("❌ Ошибка при получении данных. Попробуйте позже.")


async def hold_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle intelligent hold callbacks."""
    query = update.callback_query
    if not query:
        return

    await query.answer()
    data = query.data

    try:
        from src.dmarket.intelligent_hold import get_hold_manager

        hold_manager = get_hold_manager()

        if data == "hold_analyze_inventory":
            # Get inventory from DMarket API
            dmarket_api = context.application.bot_data.get("dmarket_api")

            if not dmarket_api:
                await query.edit_message_text("❌ API не инициализирован")
                return

            await query.edit_message_text("⏳ Анализирую ваш инвентарь...")

            try:
                # Fetch user inventory
                inventory_data = await dmarket_api.get_user_inventory(game_id="csgo", limit=50)
                items = inventory_data.get("objects", [])

                if not items:
                    await query.edit_message_text(
                        "📦 Ваш инвентарь пуст или недоступен.\n\n"
                        "Используйте /scan для поиска предметов для покупки."
                    )
                    return

                # Format for analysis
                formatted_items = []
                for item in items[:20]:  # Analyze top 20 items
                    formatted_items.append({
                        "name": item.get("title", "Unknown"),
                        "current_price": float(item.get("price", {}).get("USD", 0)) / 100,
                        "buy_price": float(item.get("price", {}).get("USD", 0))
                        / 100,  # Approximate
                        "days_held": 0,  # Would need to track purchase date
                    })

                # Analyze
                analysis = await hold_manager.analyze_inventory(formatted_items, game="csgo")

                # Format response
                message = "📊 **Анализ инвентаря**\n\n"
                message += f"📦 Всего предметов: {analysis['total_items']}\n"
                message += f"📈 Держать: {analysis['summary']['hold']}\n"
                message += f"💰 Продать: {analysis['summary']['sell']}\n"
                message += (
                    f"📊 Ср. ожидание: {analysis['summary']['avg_expected_change']:+.1f}%\n\n"
                )

                message += "**Рекомендации:**\n"
                for rec in analysis["recommendations"][:10]:
                    emoji = "📈" if rec["action"] == "hold" else "💰"
                    action = "ДЕРЖАТЬ" if rec["action"] == "hold" else "ПРОДАТЬ"
                    message += f"{emoji} {rec['item'][:25]}... - {action}\n"

                if analysis["upcoming_events"]:
                    message += "\n**Учтенные события:**\n"
                    for event in analysis["upcoming_events"][:3]:
                        message += f"• {event['name']} ({event['days_until']}д)\n"

            except Exception as e:
                logger.error(f"Inventory analysis error: {e}")
                message = f"❌ Ошибка анализа: {str(e)[:100]}"

            keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="hold_menu")]]
            await query.edit_message_text(
                message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
            )

        elif data == "hold_check_item":
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

        elif data.startswith("hold_item_"):
            item_name = data.replace("hold_item_", "")

            # Get recommendation
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

        elif data == "hold_events_csgo":
            events = hold_manager._get_upcoming_events(days_ahead=60, game="csgo")

            message = "📅 **События CS2/CSGO (60 дней)**\n\n"

            if events:
                for event in events:
                    impact_emoji = "📈" if event.expected_impact > 0 else "📉"
                    status = "🔴 СЕЙЧАС" if event.is_active else f"⏰ {event.days_until}д"
                    message += (
                        f"{impact_emoji} **{event.name}**\n"
                        f"   {status} | Влияние: {event.expected_impact * 100:+.0f}%\n\n"
                    )
            else:
                message += "Нет запланированных событий"

            keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="hold_menu")]]
            await query.edit_message_text(
                message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
            )

        elif data == "hold_events_dota2":
            events = hold_manager._get_upcoming_events(days_ahead=60, game="dota2")

            message = "📅 **События Dota 2 (60 дней)**\n\n"

            if events:
                for event in events:
                    impact_emoji = "📈" if event.expected_impact > 0 else "📉"
                    status = "🔴 СЕЙЧАС" if event.is_active else f"⏰ {event.days_until}д"
                    message += (
                        f"{impact_emoji} **{event.name}**\n"
                        f"   {status} | Влияние: {event.expected_impact * 100:+.0f}%\n\n"
                    )
            else:
                message += "Нет запланированных событий"

            keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="hold_menu")]]
            await query.edit_message_text(
                message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
            )

        elif data == "hold_settings":
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

        elif data == "hold_menu":
            # Return to hold main menu
            await hold_command.__wrapped__(update, context) if hasattr(
                hold_command, "__wrapped__"
            ) else None
            # Re-show the menu
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

    except Exception as e:
        logger.error(f"Hold callback error: {e}")
        await query.edit_message_text(f"❌ Ошибка: {str(e)[:100]}")


def register_intelligent_hold_handlers(application) -> None:
    """Register intelligent hold handlers with the application."""
    application.add_handler(CommandHandler("hold", hold_command))
    application.add_handler(CallbackQueryHandler(hold_callback_handler, pattern=r"^hold_"))
    logger.info("Intelligent Hold handlers registered")
