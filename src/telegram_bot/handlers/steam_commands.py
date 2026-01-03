"""
Обработчики команд Steam статистики и настроек.

Этот модуль содержит команды для управления Steam интеграцией:
- /stats - статистика находок
- /top - топ предметов дня
- /steam_settings - настройки фильтров
"""

import logging

from telegram import Update
from telegram.ext import ContextTypes

from src.dmarket.steam_arbitrage_enhancer import get_steam_enhancer
from src.utils.steam_db_handler import get_steam_db


logger = logging.getLogger(__name__)


async def steam_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Команда /stats - показывает статистику арбитражных находок за день.

    Args:
        update: Telegram update object
        context: Telegram context object
    """
    if not update.message:
        return

    user_id = update.effective_user.id
    logger.info(f"Steam stats command from user {user_id}")

    try:
        enhancer = get_steam_enhancer()
        stats = enhancer.get_daily_stats()

        # Формируем сообщение
        message = (
            "📊 **Статистика Steam Арбитража за 24 часа**\n\n"
            f"🔍 Находок найдено: **{stats['count']}**\n"
        )

        if stats["count"] > 0:
            message += (
                f"💰 Средний профит: **{stats['avg_profit']:.1f}%**\n"
                f"🚀 Максимальный: **{stats['max_profit']:.1f}%**\n"
                f"📉 Минимальный: **{stats['min_profit']:.1f}%**\n"
            )
        else:
            message += "\n_Пока находок нет. Проверьте позже!_\n"

        # Получаем настройки
        db = get_steam_db()
        settings = db.get_settings()

        message += (
            f"\n⚙️ **Текущие фильтры:**\n"
            f"• Мин. профит: **{settings['min_profit']:.0f}%**\n"
            f"• Мин. объем: **{settings['min_volume']} продаж/день**\n"
            f"• Статус: {'🔴 Пауза' if settings['is_paused'] else '🟢 Работает'}\n"
        )

        # Кэш статистика
        cache_stats = db.get_cache_stats()
        message += (
            f"\n💾 **Кэш Steam:**\n"
            f"• Всего записей: **{cache_stats['total']}**\n"
            f"• Актуальных: **{cache_stats['actual']}**\n"
            f"• Устаревших: **{cache_stats['stale']}**\n"
        )

        await update.message.reply_text(message, parse_mode="Markdown")
        logger.info(f"Sent stats to user {user_id}")

    except Exception as e:
        logger.error(f"Error in steam_stats_command: {e}", exc_info=True)
        await update.message.reply_text("❌ Ошибка при получении статистики. Попробуйте позже.")


async def steam_top_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Команда /top - показывает топ-5 находок за день.

    Args:
        update: Telegram update object
        context: Telegram context object
    """
    if not update.message:
        return

    user_id = update.effective_user.id
    logger.info(f"Steam top command from user {user_id}")

    try:
        enhancer = get_steam_enhancer()
        top_items = enhancer.get_top_items_today(limit=5)

        if not top_items:
            await update.message.reply_text(
                "📊 Топ предметов за 24 часа\n\n_Пока находок нет. Проверьте позже!_",
                parse_mode="Markdown",
            )
            return

        # Формируем сообщение
        message = "🏆 **Топ-5 предметов за 24 часа**\n\n"

        for idx, item in enumerate(top_items, 1):
            item_name = item["item_name"]
            profit = item["profit_pct"]

            # Эмодзи для топ-3
            medal = ""
            if idx == 1:
                medal = "🥇"
            elif idx == 2:
                medal = "🥈"
            elif idx == 3:
                medal = "🥉"
            else:
                medal = f"{idx}."

            message += f"{medal} **{item_name}**\n"
            message += f"   💰 Профит: **{profit:.1f}%**\n\n"

        await update.message.reply_text(message, parse_mode="Markdown")
        logger.info(f"Sent top items to user {user_id}")

    except Exception as e:
        logger.error(f"Error in steam_top_command: {e}", exc_info=True)
        await update.message.reply_text("❌ Ошибка при получении топа. Попробуйте позже.")


async def steam_settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Команда /steam_settings - показывает и изменяет настройки.

    Примеры:
        /steam_settings - показать текущие настройки
        /steam_settings profit 15 - установить мин. профит 15%
        /steam_settings volume 100 - установить мин. объем 100 шт/день

    Args:
        update: Telegram update object
        context: Telegram context object
    """
    if not update.message:
        return

    user_id = update.effective_user.id
    logger.info(f"Steam settings command from user {user_id}")

    try:
        enhancer = get_steam_enhancer()
        db = get_steam_db()

        # Проверяем аргументы
        if not context.args or len(context.args) == 0:
            # Показываем текущие настройки
            settings = db.get_settings()

            message = (
                "⚙️ **Настройки Steam Арбитража**\n\n"
                f"💰 Минимальный профит: **{settings['min_profit']:.0f}%**\n"
                f"📊 Минимальный объем: **{settings['min_volume']} шт/день**\n"
                f"🔔 Статус: {'🔴 Пауза' if settings['is_paused'] else '🟢 Работает'}\n\n"
                "_Для изменения используйте:_\n"
                "`/steam_settings profit 15` - установить профит\n"
                "`/steam_settings volume 100` - установить объем\n"
            )

            await update.message.reply_text(message, parse_mode="Markdown")
            return

        # Обработка команд изменения
        command = context.args[0].lower()

        if command == "profit" and len(context.args) >= 2:
            try:
                new_profit = float(context.args[1])
                if 0 < new_profit <= 100:
                    enhancer.update_settings(min_profit=new_profit)
                    await update.message.reply_text(
                        f"✅ Минимальный профит установлен: **{new_profit:.0f}%**",
                        parse_mode="Markdown",
                    )
                    logger.info(f"User {user_id} updated min_profit to {new_profit}")
                else:
                    await update.message.reply_text("❌ Профит должен быть от 0% до 100%")
            except ValueError:
                await update.message.reply_text(
                    "❌ Некорректное значение профита. Используйте число."
                )

        elif command == "volume" and len(context.args) >= 2:
            try:
                new_volume = int(context.args[1])
                if new_volume >= 0:
                    enhancer.update_settings(min_volume=new_volume)
                    await update.message.reply_text(
                        f"✅ Минимальный объем установлен: **{new_volume} шт/день**",
                        parse_mode="Markdown",
                    )
                    logger.info(f"User {user_id} updated min_volume to {new_volume}")
                else:
                    await update.message.reply_text("❌ Объем должен быть положительным числом")
            except ValueError:
                await update.message.reply_text(
                    "❌ Некорректное значение объема. Используйте целое число."
                )

        else:
            await update.message.reply_text(
                "❌ Неизвестная команда.\n\n"
                "Используйте:\n"
                "`/steam_settings profit <число>`\n"
                "`/steam_settings volume <число>`",
                parse_mode="Markdown",
            )

    except Exception as e:
        logger.error(f"Error in steam_settings_command: {e}", exc_info=True)
        await update.message.reply_text("❌ Ошибка при изменении настроек. Попробуйте позже.")
