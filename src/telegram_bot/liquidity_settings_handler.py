"""Обработчики команд для управления фильтрами ликвидности в Telegram боте."""

import logging
from typing import Any

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from src.telegram_bot.user_profiles import profile_manager


logger = logging.getLogger(__name__)

# Настройки по умолчанию для фильтров ликвидности
DEFAULT_LIQUIDITY_SETTINGS = {
    "enabled": True,
    "min_liquidity_score": 60,
    "min_sales_per_week": 5,
    "max_time_to_sell_days": 7,
}


def get_liquidity_settings(user_id: int) -> dict[str, Any]:
    """Получает настройки фильтров ликвидности для пользователя.

    Args:
        user_id: ID пользователя Telegram

    Returns:
        Словарь с настройками ликвидности

    """
    profile = profile_manager.get_profile(user_id)

    if "liquidity_settings" not in profile:
        profile["liquidity_settings"] = DEFAULT_LIQUIDITY_SETTINGS.copy()
        profile_manager.update_profile(
            user_id, {"liquidity_settings": profile["liquidity_settings"]}
        )

    return profile["liquidity_settings"]


def update_liquidity_settings(user_id: int, settings: dict[str, Any]) -> None:
    """Обновляет настройки фильтров ликвидности для пользователя.

    Args:
        user_id: ID пользователя Telegram
        settings: Словарь с настройками для обновления

    """
    profile = profile_manager.get_profile(user_id)

    if "liquidity_settings" not in profile:
        profile["liquidity_settings"] = DEFAULT_LIQUIDITY_SETTINGS.copy()

    # Обновляем настройки
    for key, value in settings.items():
        profile["liquidity_settings"][key] = value

    profile_manager.update_profile(user_id, {"liquidity_settings": profile["liquidity_settings"]})
    logger.info(f"Обновлены настройки ликвидности для пользователя {user_id}: {settings}")


def get_liquidity_settings_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру для управления настройками ликвидности.

    Returns:
        InlineKeyboardMarkup с кнопками настроек

    """
    keyboard = [
        [
            InlineKeyboardButton(
                "📊 Минимальный балл ликвидности",
                callback_data="liquidity_set_min_score",
            )
        ],
        [
            InlineKeyboardButton(
                "📈 Минимум продаж в неделю",
                callback_data="liquidity_set_min_sales",
            )
        ],
        [
            InlineKeyboardButton(
                "⏱️ Максимальное время продажи",
                callback_data="liquidity_set_max_time",
            )
        ],
        [
            InlineKeyboardButton(
                "🔄 Вкл/Выкл фильтр",
                callback_data="liquidity_toggle",
            )
        ],
        [
            InlineKeyboardButton(
                "🔄 Сбросить на умолчания",
                callback_data="liquidity_reset",
            )
        ],
        [
            InlineKeyboardButton(
                "🔙 Назад",
                callback_data="back_to_settings",
            )
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


async def liquidity_settings_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Команда /liquidity_settings - показать текущие настройки.

    Args:
        update: Объект Update от Telegram
        context: Контекст обработчика

    """
    if not update.effective_user or not update.message:
        return

    user_id = update.effective_user.id
    settings = get_liquidity_settings(user_id)

    # Формируем сообщение с текущими настройками
    status_emoji = "✅" if settings["enabled"] else "❌"
    status_text = "Включен" if settings["enabled"] else "Выключен"

    min_score = settings["min_liquidity_score"]
    min_sales = settings["min_sales_per_week"]
    max_days = settings["max_time_to_sell_days"]

    message = (
        "🔍 <b>Настройки фильтров ликвидности</b>\n\n"
        f"Статус: {status_emoji} <b>{status_text}</b>\n\n"
        f"📊 <b>Минимальный балл ликвидности:</b> {min_score}\n"
        f"   <i>Предметы с баллом ниже {min_score} "
        "будут отфильтрованы</i>\n\n"
        f"📈 <b>Минимум продаж в неделю:</b> {min_sales}\n"
        f"   <i>Показывать только предметы с {min_sales}+ "
        "продаж/неделю</i>\n\n"
        f"⏱️ <b>Максимальное время продажи:</b> {max_days} дней\n"
        f"   <i>Скрывать предметы, которые продаются дольше "
        f"{max_days} дней</i>\n\n"
        "Выберите параметр для изменения:"
    )

    await update.message.reply_text(
        message,
        reply_markup=get_liquidity_settings_keyboard(),
        parse_mode="HTML",
    )


async def toggle_liquidity_filter(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Включает/выключает фильтр ликвидности.

    Args:
        update: Объект Update от Telegram
        context: Контекст обработчика

    """
    if not update.effective_user or not update.callback_query:
        return

    user_id = update.effective_user.id
    settings = get_liquidity_settings(user_id)

    # Переключаем статус
    settings["enabled"] = not settings["enabled"]
    update_liquidity_settings(user_id, {"enabled": settings["enabled"]})

    status_emoji = "✅" if settings["enabled"] else "❌"
    status_text = "включен" if settings["enabled"] else "выключен"

    await update.callback_query.answer(f"Фильтр ликвидности {status_text}")

    # Обновляем сообщение
    message = (
        "🔍 <b>Настройки фильтров ликвидности</b>\n\n"
        f"Статус: {status_emoji} <b>{status_text.capitalize()}</b>\n\n"
        f"📊 <b>Минимальный балл ликвидности:</b> {settings['min_liquidity_score']}\n"
        f"   <i>Предметы с баллом ниже {settings['min_liquidity_score']} будут отфильтрованы</i>\n\n"
        f"📈 <b>Минимум продаж в неделю:</b> {settings['min_sales_per_week']}\n"
        f"   <i>Показывать только предметы с {settings['min_sales_per_week']}+ продаж/неделю</i>\n\n"
        f"⏱️ <b>Максимальное время продажи:</b> {settings['max_time_to_sell_days']} дней\n"
        f"   <i>Скрывать предметы, которые продаются дольше {settings['max_time_to_sell_days']} дней</i>\n\n"
        "Выберите параметр для изменения:"
    )

    if update.callback_query.message:
        await update.callback_query.edit_message_text(
            message,
            reply_markup=get_liquidity_settings_keyboard(),
            parse_mode="HTML",
        )


async def reset_liquidity_settings(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Сбрасывает настройки фильтров ликвидности на значения по умолчанию.

    Args:
        update: Объект Update от Telegram
        context: Контекст обработчика

    """
    if not update.effective_user or not update.callback_query:
        return

    user_id = update.effective_user.id

    # Сбрасываем на значения по умолчанию
    update_liquidity_settings(user_id, DEFAULT_LIQUIDITY_SETTINGS.copy())

    await update.callback_query.answer("Настройки сброшены на значения по умолчанию")

    # Обновляем сообщение
    settings = DEFAULT_LIQUIDITY_SETTINGS
    status_emoji = "✅" if settings["enabled"] else "❌"
    status_text = "Включен" if settings["enabled"] else "Выключен"

    message = (
        "🔍 <b>Настройки фильтров ликвидности</b>\n\n"
        f"Статус: {status_emoji} <b>{status_text}</b>\n\n"
        f"📊 <b>Минимальный балл ликвидности:</b> {settings['min_liquidity_score']}\n"
        f"   <i>Предметы с баллом ниже {settings['min_liquidity_score']} будут отфильтрованы</i>\n\n"
        f"📈 <b>Минимум продаж в неделю:</b> {settings['min_sales_per_week']}\n"
        f"   <i>Показывать только предметы с {settings['min_sales_per_week']}+ продаж/неделю</i>\n\n"
        f"⏱️ <b>Максимальное время продажи:</b> {settings['max_time_to_sell_days']} дней\n"
        f"   <i>Скрывать предметы, которые продаются дольше {settings['max_time_to_sell_days']} дней</i>\n\n"
        "Выберите параметр для изменения:"
    )

    if update.callback_query.message:
        await update.callback_query.edit_message_text(
            message,
            reply_markup=get_liquidity_settings_keyboard(),
            parse_mode="HTML",
        )


async def set_min_liquidity_score_prompt(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Запрашивает у пользователя значение минимального балла ликвидности.

    Args:
        update: Объект Update от Telegram
        context: Контекст обработчика

    """
    if not update.callback_query:
        return

    # Сохраняем в контексте, что ожидаем ввод балла ликвидности
    if context.user_data is not None:
        context.user_data["awaiting_liquidity_score"] = True

    await update.callback_query.answer()

    message = (
        "📊 <b>Установка минимального балла ликвидности</b>\n\n"
        "Введите минимальный балл ликвидности (0-100):\n\n"
        "<i>Балл ликвидности показывает, насколько легко продать предмет:\n"
        "• 0-30 - низкая ликвидность (сложно продать)\n"
        "• 31-60 - средняя ликвидность\n"
        "• 61-80 - высокая ликвидность\n"
        "• 81-100 - очень высокая ликвидность (быстро продается)</i>\n\n"
        "Отправьте /cancel для отмены"
    )

    if update.callback_query.message:
        await update.callback_query.edit_message_text(message, parse_mode="HTML")


async def set_min_sales_per_week_prompt(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Запрашивает у пользователя значение минимальных продаж в неделю.

    Args:
        update: Объект Update от Telegram
        context: Контекст обработчика

    """
    if not update.callback_query:
        return

    # Сохраняем в контексте, что ожидаем ввод продаж
    if context.user_data is not None:
        context.user_data["awaiting_sales_per_week"] = True

    await update.callback_query.answer()

    message = (
        "📈 <b>Установка минимума продаж в неделю</b>\n\n"
        "Введите минимальное количество продаж в неделю:\n\n"
        "<i>Это среднее количество продаж предмета за неделю.\n"
        "Чем больше продаж, тем выше ликвидность.\n\n"
        "Рекомендуемые значения:\n"
        "• 1-3 - для редких дорогих предметов\n"
        "• 5-10 - стандартное значение\n"
        "• 15+ - только очень популярные предметы</i>\n\n"
        "Отправьте /cancel для отмены"
    )

    if update.callback_query.message:
        await update.callback_query.edit_message_text(message, parse_mode="HTML")


async def set_max_time_to_sell_prompt(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Запрашивает у пользователя максимальное время продажи.

    Args:
        update: Объект Update от Telegram
        context: Контекст обработчика

    """
    if not update.callback_query:
        return

    # Сохраняем в контексте, что ожидаем ввод времени
    if context.user_data is not None:
        context.user_data["awaiting_time_to_sell"] = True

    await update.callback_query.answer()

    message = (
        "⏱️ <b>Установка максимального времени продажи</b>\n\n"
        "Введите максимальное время продажи (в днях):\n\n"
        "<i>Это среднее время, за которое продается предмет.\n\n"
        "Рекомендуемые значения:\n"
        "• 1-3 дня - только быстро продаваемые предметы\n"
        "• 5-7 дней - стандартное значение\n"
        "• 10-14 дней - включая медленно продаваемые</i>\n\n"
        "Отправьте /cancel для отмены"
    )

    if update.callback_query.message:
        await update.callback_query.edit_message_text(message, parse_mode="HTML")


async def process_liquidity_value_input(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Обрабатывает ввод пользователем значения для настройки ликвидности.

    Args:
        update: Объект Update от Telegram
        context: Контекст обработчика

    """
    if not update.effective_user or not update.message or not update.message.text:
        return

    user_id = update.effective_user.id

    # Проверяем, что ожидаем ввод
    if context.user_data is None:
        return

    try:
        value = int(update.message.text)
    except ValueError:
        await update.message.reply_text(
            "❌ Ошибка: введите целое число.\nОтправьте /cancel для отмены."
        )
        return

    # Обрабатываем в зависимости от того, что ожидаем
    if context.user_data.get("awaiting_liquidity_score"):
        # Валидация балла ликвидности
        if not 0 <= value <= 100:
            await update.message.reply_text(
                "❌ Ошибка: балл ликвидности должен быть от 0 до 100.\n"
                "Попробуйте еще раз или отправьте /cancel для отмены."
            )
            return

        update_liquidity_settings(user_id, {"min_liquidity_score": value})
        context.user_data["awaiting_liquidity_score"] = False

        await update.message.reply_text(
            f"✅ Минимальный балл ликвидности установлен: {value}\n\n"
            "Используйте /liquidity_settings для просмотра всех настроек."
        )

    elif context.user_data.get("awaiting_sales_per_week"):
        # Валидация продаж в неделю
        if value < 0:
            await update.message.reply_text(
                "❌ Ошибка: количество продаж не может быть отрицательным.\n"
                "Попробуйте еще раз или отправьте /cancel для отмены."
            )
            return

        update_liquidity_settings(user_id, {"min_sales_per_week": value})
        context.user_data["awaiting_sales_per_week"] = False

        await update.message.reply_text(
            f"✅ Минимум продаж в неделю установлен: {value}\n\n"
            "Используйте /liquidity_settings для просмотра всех настроек."
        )

    elif context.user_data.get("awaiting_time_to_sell"):
        # Валидация времени продажи
        if value <= 0:
            await update.message.reply_text(
                "❌ Ошибка: время продажи должно быть больше 0.\n"
                "Попробуйте еще раз или отправьте /cancel для отмены."
            )
            return

        update_liquidity_settings(user_id, {"max_time_to_sell_days": value})
        context.user_data["awaiting_time_to_sell"] = False

        await update.message.reply_text(
            f"✅ Максимальное время продажи установлено: {value} дней\n\n"
            "Используйте /liquidity_settings для просмотра всех настроек."
        )


async def cancel_liquidity_input(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Отменяет ввод значения настройки ликвидности.

    Args:
        update: Объект Update от Telegram
        context: Контекст обработчика

    """
    if not update.message or context.user_data is None:
        return

    # Сбрасываем все флаги ожидания ввода
    context.user_data["awaiting_liquidity_score"] = False
    context.user_data["awaiting_sales_per_week"] = False
    context.user_data["awaiting_time_to_sell"] = False

    await update.message.reply_text(
        "❌ Ввод отменен.\n\nИспользуйте /liquidity_settings для настройки фильтров."
    )
