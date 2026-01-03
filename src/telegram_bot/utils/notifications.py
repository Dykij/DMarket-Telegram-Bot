"""Модуль для отправки уведомлений о найденных арбитражных возможностях.

Поддерживает:
- Отправку уведомлений о профитных предметах
- Тихий режим (Silent Mode) для ночного времени
- Защиту от спама (анти-дубли)
- Красивое форматирование сообщений
"""

from datetime import datetime
import logging
import os

from telegram import Bot
from telegram.error import TelegramError


logger = logging.getLogger(__name__)


async def send_profit_alert(item_data: dict) -> bool:
    """Отправляет уведомление о найденной арбитражной возможности.

    Args:
        item_data: Словарь с информацией о предмете
            Обязательные ключи:
            - title: название предмета
            - game: код игры
            - profit: прибыль в USD
            - profit_percent: процент прибыли
            - price: словарь с ценой {'amount': цена_в_центах}

    Returns:
        True если сообщение отправлено успешно, False иначе
    """
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("ADMIN_CHAT_ID")

    if not token:
        logger.warning("TELEGRAM_BOT_TOKEN не установлен в .env")
        return False

    if not chat_id:
        logger.warning("ADMIN_CHAT_ID не установлен в .env - уведомления не будут отправляться")
        return False

    # --- ЛОГИКА ТИХОГО РЕЖИМА ---
    current_hour = datetime.now().hour
    # С 23 вечера до 8 утра - тихий режим (без звука)
    is_silent_night = current_hour >= 23 or current_hour < 8

    # Глобальный тихий режим (полностью отключает уведомления)
    global_silent_mode = os.getenv("SILENT_MODE", "False").lower() == "true"

    if global_silent_mode:
        logger.debug("Уведомление не отправлено: включен глобальный тихий режим")
        return False

    try:
        bot = Bot(token=token)

        # Извлекаем данные с проверками
        title = item_data.get("title", "Неизвестный предмет")
        game = item_data.get("game", "unknown").upper()
        profit = item_data.get("profit", 0)
        profit_percent = item_data.get("profit_percent", 0)

        # Цена может быть в разных форматах
        price_data = item_data.get("price", {})
        if isinstance(price_data, dict):
            price_cents = price_data.get("amount", 0)
        else:
            price_cents = price_data

        price_usd = float(price_cents) / 100 if price_cents else 0

        # Эмодзи для разных игр
        game_emoji = {
            "CSGO": "🔫",
            "DOTA2": "🎮",
            "TF2": "🎯",
            "RUST": "🔨",
        }.get(game, "🎲")

        # Статус иконка (ночь/день)
        status_icon = "🌙" if is_silent_night else "🎯"

        # Форматируем красивое сообщение
        text = (
            f"{status_icon} *Арбитражная возможность!*\n"
            f"{'━' * 25}\n"
            f"{game_emoji} *{title}*\n\n"
            f"🎮 Игра: `{game}`\n"
            f"💰 Профит: +*${profit:.2f}*\n"
            f"📈 Доходность: *{profit_percent:.1f}%*\n"
            f"💵 Цена входа: ${price_usd:.2f}\n"
            f"{'━' * 25}\n"
        )

        # Добавляем информацию о тихом режиме
        if is_silent_night:
            text += "\n🌙 _Тихий режим: уведомление без звука_"

        # Отправляем сообщение
        await bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode="Markdown",
            disable_notification=is_silent_night,  # Без звука ночью
        )

        logger.info(
            f"Уведомление отправлено: {title} ({game}), профит: ${profit:.2f}",
            extra={
                "item_title": title,
                "game": game,
                "profit": profit,
                "silent": is_silent_night,
            },
        )

        return True

    except TelegramError as e:
        logger.exception(f"Ошибка Telegram API при отправке уведомления: {e}")
        return False
    except Exception as e:
        logger.exception(f"Неожиданная ошибка при отправке уведомления: {e}")
        return False


async def send_batch_alert(items: list[dict], summary: str = "") -> bool:
    """Отправляет групповое уведомление о нескольких находках.

    Полезно для отправки дайджеста раз в N минут вместо спама.

    Args:
        items: Список предметов для уведомления
        summary: Дополнительная информация (опционально)

    Returns:
        True если успешно отправлено
    """
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("ADMIN_CHAT_ID")

    if not token or not chat_id:
        return False

    # Проверка тихого режима
    global_silent_mode = os.getenv("SILENT_MODE", "False").lower() == "true"
    if global_silent_mode:
        return False

    current_hour = datetime.now().hour
    is_silent_night = current_hour >= 23 or current_hour < 8

    try:
        bot = Bot(token=token)

        # Формируем сводку
        text = f"📊 *Найдено {len(items)} возможностей*\n\n"

        if summary:
            text += f"{summary}\n\n"

        # Показываем топ-5
        for i, item in enumerate(items[:5], 1):
            title = item.get("title", "Неизвестно")
            game = item.get("game", "?").upper()
            profit = item.get("profit", 0)
            profit_pct = item.get("profit_percent", 0)

            text += f"{i}. *{title}* ({game})\n"
            text += f"   💰 ${profit:.2f} ({profit_pct:.1f}%)\n\n"

        if len(items) > 5:
            text += f"_...и еще {len(items) - 5} предметов_\n"

        await bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode="Markdown",
            disable_notification=is_silent_night,
        )

        logger.info(f"Групповое уведомление отправлено: {len(items)} предметов")
        return True

    except Exception as e:
        logger.exception(f"Ошибка отправки группового уведомления: {e}")
        return False


async def send_scanner_status(status: str, details: dict | None = None) -> bool:
    """Отправляет уведомление о статусе сканера.

    Args:
        status: Статус сканера (started, stopped, error)
        details: Дополнительная информация

    Returns:
        True если успешно
    """
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("ADMIN_CHAT_ID")

    if not token or not chat_id:
        return False

    try:
        bot = Bot(token=token)

        status_emoji = {
            "started": "✅",
            "stopped": "⏸️",
            "error": "❌",
            "warning": "⚠️",
        }.get(status, "ℹ️")

        text = f"{status_emoji} *Статус сканера: {status}*\n\n"

        if details:
            text += "Детали:\n"
            for key, value in details.items():
                text += f"• {key}: `{value}`\n"

        await bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode="Markdown",
        )

        return True

    except Exception as e:
        logger.exception(f"Ошибка отправки статуса сканера: {e}")
        return False
