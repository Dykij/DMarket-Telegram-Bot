"""Обработчик команд для таргетов (buy orders)."""

from typing import Any

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes

from src.dmarket.targets import TargetManager
from src.telegram_bot.utils.api_client import create_api_client_from_env
from src.telegram_bot.utils.formatters import format_target_competition_analysis
from src.utils.exceptions import handle_exceptions
from src.utils.logging_utils import get_logger


logger = get_logger(__name__)

# Константы для callback данных
TARGET_ACTION = "target"
TARGET_CREATE_ACTION = "target_create"
TARGET_LIST_ACTION = "target_list"
TARGET_DELETE_ACTION = "target_delete"
TARGET_SMART_ACTION = "target_smart"
TARGET_STATS_ACTION = "target_stats"
TARGET_COMPETITION_ACTION = "target_competition"


@handle_exceptions(logger_instance=logger, default_error_message="Ошибка в меню таргетов")
async def start_targets_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Показать главное меню таргетов.

    Args:
        update: Объект Update от Telegram
        context: Контекст выполнения

    """
    query = update.callback_query
    if query:
        await query.answer()

    if update.effective_user:
        user_id = update.effective_user.id
    else:
        return

    keyboard = [
        [
            InlineKeyboardButton(
                "📝 Создать таргет",
                callback_data=f"{TARGET_ACTION}_{TARGET_CREATE_ACTION}",
            ),
        ],
        [
            InlineKeyboardButton(
                "📋 Мои таргеты",
                callback_data=f"{TARGET_ACTION}_{TARGET_LIST_ACTION}",
            ),
        ],
        [
            InlineKeyboardButton(
                "🤖 Умные таргеты",
                callback_data=f"{TARGET_ACTION}_{TARGET_SMART_ACTION}",
            ),
        ],
        [
            InlineKeyboardButton(
                "🎯 Анализ конкуренции",
                callback_data=f"{TARGET_ACTION}_{TARGET_COMPETITION_ACTION}",
            ),
        ],
        [
            InlineKeyboardButton(
                "📊 Статистика",
                callback_data=f"{TARGET_ACTION}_{TARGET_STATS_ACTION}",
            ),
        ],
        [
            InlineKeyboardButton(
                "⬅️ Назад",
                callback_data="main_menu",
            ),
        ],
    ]

    text = (
        "🎯 *Таргеты (Buy Orders)*\n\n"
        "Создавайте заявки на покупку предметов по желаемой цене. "
        "Когда кто-то выставит предмет по вашей цене или ниже, "
        "он будет автоматически куплен.\n\n"
        "✨ *Новые возможности API v1.1.0:*\n"
        "🤖 Умные таргеты - автоматический расчет оптимальных цен\n"
        "🎯 Анализ конкуренции - оценка существующих buy orders\n\n"
        "Выберите действие:"
    )

    if query:
        await query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
    else:
        await context.bot.send_message(
            chat_id=user_id,
            text=text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )


@handle_exceptions(
    logger_instance=logger,
    default_error_message="Ошибка при создании умных таргетов",
)
async def handle_smart_targets(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    game: str = "csgo",
) -> None:
    """Обработать создание умных таргетов.

    Args:
        update: Объект Update от Telegram
        context: Контекст выполнения
        game: Код игры

    """
    query = update.callback_query
    if not query:
        return

    await query.answer()

    await query.edit_message_text(
        "🤖 *Умные таргеты*\n\n"
        "Анализируем рынок и создаем оптимальные таргеты...\n"
        "Пожалуйста, подождите...",
        parse_mode="Markdown",
    )

    try:
        # Получаем API клиент
        api_client = create_api_client_from_env()
        if api_client is None:
            await query.edit_message_text(
                "❌ Не удалось создать API клиент. Проверьте настройки.",
                parse_mode="Markdown",
            )
            return

        # Создаем менеджер таргетов
        target_manager = TargetManager(api_client=api_client)

        # Список популярных предметов для умных таргетов
        popular_items = [
            {"title": "AK-47 | Redline (Field-Tested)"},
            {"title": "AWP | Asiimov (Field-Tested)"},
            {"title": "M4A4 | Asiimov (Field-Tested)"},
        ]

        # Создаем умные таргеты
        results = await target_manager.create_smart_targets(
            game=game,
            items=popular_items,
            price_reduction_percent=5.0,
        )

        if results:
            text = f"✅ *Умные таргеты созданы успешно!*\n\nСоздано таргетов: {len(results)}\n\n"
            for i, result in enumerate(results[:5], 1):
                title = result.get("Title", "Неизвестный предмет")
                price = result.get("Price", {}).get("Amount", 0) / 100
                text += f"{i}. {title}\n💰 Цена: ${price:.2f}\n\n"
        else:
            text = "⚠️ Не удалось создать умные таргеты. Попробуйте позже."

        await query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("⬅️ Назад", callback_data=TARGET_ACTION)]],
            ),
        )

    except Exception as e:
        # Логирование выполняется декоратором handle_exceptions при re-raise
        await query.edit_message_text(
            f"⚠️ Произошла ошибка: {e!s}",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("⬅️ Назад", callback_data=TARGET_ACTION)]],
            ),
        )
        raise  # Пробрасываем исключение для логирования


@handle_exceptions(
    logger_instance=logger,
    default_error_message="Ошибка при анализе конкуренции",
)
async def handle_competition_analysis(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    game: str = "csgo",
) -> None:
    """Обработать анализ конкуренции buy orders.

    Args:
        update: Объект Update от Telegram
        context: Контекст выполнения
        game: Код игры

    """
    query = update.callback_query
    if not query:
        return

    await query.answer()

    await query.edit_message_text(
        "🎯 *Анализ конкуренции*\n\n"
        "Анализируем существующие buy orders...\n"
        "Пожалуйста, подождите...",
        parse_mode="Markdown",
    )

    try:
        # Получаем API клиент
        api_client = create_api_client_from_env()
        if api_client is None:
            await query.edit_message_text(
                "❌ Не удалось создать API клиент.",
                parse_mode="Markdown",
            )
            return

        # Создаем менеджер таргетов
        target_manager = TargetManager(api_client=api_client)

        # Анализируем конкуренцию для популярного предмета
        item_title = "AK-47 | Redline (Field-Tested)"
        analysis = await target_manager.analyze_target_competition(
            game=game,
            title=item_title,
        )

        if analysis:
            text = format_target_competition_analysis(analysis, item_title)
        else:
            text = "⚠️ Не удалось получить данные о конкуренции."

        await query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("⬅️ Назад", callback_data=TARGET_ACTION)]],
            ),
        )

    except Exception as e:
        # Логирование выполняется декоратором handle_exceptions при re-raise
        await query.edit_message_text(
            f"⚠️ Произошла ошибка: {e!s}",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("⬅️ Назад", callback_data=TARGET_ACTION)]],
            ),
        )
        raise  # Пробрасываем исключение для логирования


@handle_exceptions(
    logger_instance=logger,
    default_error_message="Ошибка в обработчике таргетов",
)
async def handle_target_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Обработать callback-запросы для таргетов.

    Args:
        update: Объект Update от Telegram
        context: Контекст выполнения

    """
    query = update.callback_query
    if not query or not query.data:
        return

    callback_data = query.data

    if callback_data == TARGET_ACTION:
        await start_targets_menu(update, context)
    elif callback_data == f"{TARGET_ACTION}_{TARGET_SMART_ACTION}":
        await handle_smart_targets(update, context)
    elif callback_data == f"{TARGET_ACTION}_{TARGET_COMPETITION_ACTION}":
        await handle_competition_analysis(update, context)
    elif callback_data.startswith(f"{TARGET_ACTION}_"):
        # Заглушки для остальных функций
        await query.answer("Эта функция будет реализована в следующей версии")


def register_target_handlers(dispatcher: Any) -> None:
    """Зарегистрировать обработчики команд таргетов.

    Args:
        dispatcher: Диспетчер бота

    """
    # Команда /targets
    dispatcher.add_handler(CommandHandler("targets", start_targets_menu))

    # Callback handlers
    dispatcher.add_handler(
        CallbackQueryHandler(handle_target_callback, pattern=f"^{TARGET_ACTION}"),
    )
