"""
Команды управления автоматическим Steam-арбитраж сканером.
"""

import logging

from telegram import Update
from telegram.ext import ContextTypes


logger = logging.getLogger(__name__)


async def steam_arbitrage_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Запустить автоматический Steam-арбитраж сканер.

    Использование: /steam_arbitrage_start [game] [min_roi]

    Примеры:
        /steam_arbitrage_start
        /steam_arbitrage_start csgo 5
        /steam_arbitrage_start dota2 10
    """
    if not update.message or not update.effective_user:
        return

    user_id = update.effective_user.id
    config = context.bot_data.get("config")

    # Проверка прав администратора
    admin_users = getattr(config.security, "admin_users", [])
    if user_id not in [int(uid) for uid in admin_users]:
        await update.message.reply_text("❌ У вас нет прав для управления сканером")
        return

    scanner = context.bot_data.get("steam_arbitrage_scanner")
    if not scanner:
        await update.message.reply_text("❌ Steam-арбитраж сканер не инициализирован")
        return

    # Парсинг параметров
    args = context.args or []
    game = args[0] if len(args) > 0 else "csgo"
    min_roi = float(args[1]) if len(args) > 1 else 5.0

    # Обновление настроек
    scanner.game = game
    scanner.min_roi = min_roi

    # Запуск
    await scanner.start()

    await update.message.reply_text(
        f"✅ <b>Steam-арбитраж сканер запущен!</b>\n\n"
        f"🎮 Игра: <code>{game}</code>\n"
        f"📊 Минимальный ROI: <code>{min_roi}%</code>\n"
        f"⏱ Интервал: <code>{scanner.scan_interval // 60} минут</code>\n\n"
        f"Используйте /steam_arbitrage_stop для остановки",
        parse_mode="HTML",
    )

    logger.info(f"Steam arbitrage scanner started by user {user_id}")


async def steam_arbitrage_stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Остановить автоматический Steam-арбитраж сканер.

    Использование: /steam_arbitrage_stop
    """
    if not update.message or not update.effective_user:
        return

    user_id = update.effective_user.id
    config = context.bot_data.get("config")

    # Проверка прав администратора
    admin_users = getattr(config.security, "admin_users", [])
    if user_id not in [int(uid) for uid in admin_users]:
        await update.message.reply_text("❌ У вас нет прав для управления сканером")
        return

    scanner = context.bot_data.get("steam_arbitrage_scanner")
    if not scanner:
        await update.message.reply_text("❌ Steam-арбитраж сканер не инициализирован")
        return

    await scanner.stop()

    await update.message.reply_text("🛑 Steam-арбитраж сканер остановлен")
    logger.info(f"Steam arbitrage scanner stopped by user {user_id}")


async def steam_arbitrage_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Показать статус автоматического Steam-арбитраж сканера.

    Использование: /steam_arbitrage_status
    """
    if not update.message or not update.effective_user:
        return

    user_id = update.effective_user.id
    config = context.bot_data.get("config")

    # Проверка прав администратора
    admin_users = getattr(config.security, "admin_users", [])
    if user_id not in [int(uid) for uid in admin_users]:
        await update.message.reply_text("❌ У вас нет прав для просмотра статуса сканера")
        return

    scanner = context.bot_data.get("steam_arbitrage_scanner")
    if not scanner:
        await update.message.reply_text("❌ Steam-арбитраж сканер не инициализирован")
        return

    status = scanner.get_status()

    status_emoji = "✅ Работает" if status["running"] else "🛑 Остановлен"
    last_scan = status["last_scan_time"] or "Еще не сканировал"

    message = (
        f"<b>Статус Steam-арбитраж сканера</b>\n\n"
        f"Состояние: {status_emoji}\n\n"
        f"📊 <b>Статистика:</b>\n"
        f"• Сканирований выполнено: {status['scans_completed']}\n"
        f"• Возможностей найдено: {status['opportunities_found']}\n"
        f"• Последнее сканирование: {last_scan}\n\n"
        f"⚙️ <b>Настройки:</b>\n"
        f"• Игра: {status['config']['game']}\n"
        f"• Интервал: {status['config']['scan_interval_minutes']} минут\n"
        f"• Минимальный ROI: {status['config']['min_roi_percent']}%\n"
        f"• Макс. предметов: {status['config']['max_items_per_scan']}"
    )

    await update.message.reply_text(message, parse_mode="HTML")
    logger.info(f"Steam arbitrage scanner status checked by user {user_id}")
