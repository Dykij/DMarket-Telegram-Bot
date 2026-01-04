"""Интерактивный дашборд для управления сканером и статистикой.

Этот модуль предоставляет расширенный UI для управления сканером арбитража,
отображения статистики и мониторинга работы бота.
"""

from datetime import datetime, timedelta
from typing import Any

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Message, Update
from telegram.constants import ParseMode
from telegram.ext import Application, CallbackQueryHandler, ContextTypes

from src.dmarket.arbitrage_scanner import ARBITRAGE_LEVELS
from src.telegram_bot.chart_generator import (
    generate_level_distribution_chart,
    generate_profit_comparison_chart,
    generate_scan_history_chart,
)
from src.utils.exceptions import handle_exceptions
from src.utils.logging_utils import get_logger


logger = get_logger(__name__)

# Константы для callback данных
DASHBOARD_ACTION = "dashboard"
DASHBOARD_STATS = "dashboard_stats"
DASHBOARD_SCANNER = "dashboard_scanner"
DASHBOARD_ACTIVE_SCANS = "dashboard_active"
DASHBOARD_HISTORY = "dashboard_history"
DASHBOARD_REFRESH = "dashboard_refresh"
DASHBOARD_CHARTS = "dashboard_charts"
DASHBOARD_CHARTS = "dashboard_charts"


class ScannerDashboard:
    """Менеджер дашборда для интерактивного управления."""

    def __init__(self) -> None:
        """Инициализация дашборда."""
        self.active_scans: dict[int, dict[str, Any]] = {}
        self.scan_history: list[dict[str, Any]] = []
        self.max_history = 50

    def add_scan_result(
        self,
        user_id: int,
        scan_data: dict[str, Any],
    ) -> None:
        """Добавить результат сканирования в историю.

        Args:
            user_id: ID пользователя
            scan_data: Данные сканирования

        """
        scan_entry = {
            "user_id": user_id,
            "timestamp": datetime.now(),
            "data": scan_data,
        }

        self.scan_history.insert(0, scan_entry)
        if len(self.scan_history) > self.max_history:
            self.scan_history = self.scan_history[: self.max_history]

    def get_user_stats(self, user_id: int) -> dict[str, Any]:
        """Получить статистику пользователя.

        Args:
            user_id: ID пользователя

        Returns:
            Словарь со статистикой

        """
        user_scans = [s for s in self.scan_history if s["user_id"] == user_id]

        total_scans = len(user_scans)
        total_opportunities = sum(len(s["data"].get("opportunities", [])) for s in user_scans)

        # Считаем среднюю прибыль
        all_opportunities = []
        for scan in user_scans:
            all_opportunities.extend(scan["data"].get("opportunities", []))

        avg_profit = 0.0
        max_profit = 0.0
        if all_opportunities:
            profits = [opp.get("profit", 0.0) for opp in all_opportunities]
            avg_profit = sum(profits) / len(profits)
            max_profit = max(profits)

        # Последнее сканирование
        last_scan_time = None
        if user_scans:
            last_scan_time = user_scans[0]["timestamp"]

        return {
            "total_scans": total_scans,
            "total_opportunities": total_opportunities,
            "avg_profit": avg_profit,
            "max_profit": max_profit,
            "last_scan_time": last_scan_time,
        }

    def mark_scan_active(
        self,
        user_id: int,
        scan_id: str,
        level: str,
        game: str,
    ) -> None:
        """Отметить сканирование как активное.

        Args:
            user_id: ID пользователя
            scan_id: ID сканирования
            level: Уровень арбитража
            game: Игра

        """
        self.active_scans[user_id] = {
            "scan_id": scan_id,
            "level": level,
            "game": game,
            "started_at": datetime.now(),
            "status": "running",
        }

    def mark_scan_complete(self, user_id: int) -> None:
        """Отметить сканирование как завершенное.

        Args:
            user_id: ID пользователя

        """
        if user_id in self.active_scans:
            self.active_scans[user_id]["status"] = "completed"
            self.active_scans[user_id]["completed_at"] = datetime.now()

    def get_active_scan(self, user_id: int) -> dict[str, Any] | None:
        """Получить активное сканирование пользователя.

        Args:
            user_id: ID пользователя

        Returns:
            Данные активного сканирования или None

        """
        return self.active_scans.get(user_id)


# Глобальный экземпляр дашборда
dashboard = ScannerDashboard()


def get_dashboard_keyboard() -> InlineKeyboardMarkup:
    """Создать клавиатуру главного дашборда.

    Returns:
        InlineKeyboardMarkup с кнопками дашборда

    """
    keyboard = [
        [
            InlineKeyboardButton(
                "📊 Статистика",
                callback_data=f"{DASHBOARD_ACTION}_{DASHBOARD_STATS}",
            ),
            InlineKeyboardButton(
                "🔍 Сканер",
                callback_data=f"{DASHBOARD_ACTION}_{DASHBOARD_SCANNER}",
            ),
        ],
        [
            InlineKeyboardButton(
                "⚡ Активные сканы",
                callback_data=f"{DASHBOARD_ACTION}_{DASHBOARD_ACTIVE_SCANS}",
            ),
            InlineKeyboardButton(
                "📜 История",
                callback_data=f"{DASHBOARD_ACTION}_{DASHBOARD_HISTORY}",
            ),
        ],
        [
            InlineKeyboardButton(
                "� Графики",
                callback_data=f"{DASHBOARD_ACTION}_{DASHBOARD_CHARTS}",
            ),
            InlineKeyboardButton(
                "�🔄 Обновить",
                callback_data=f"{DASHBOARD_ACTION}_{DASHBOARD_REFRESH}",
            ),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def format_stats_message(stats: dict[str, Any]) -> str:
    """Форматировать сообщение со статистикой.

    Args:
        stats: Статистика пользователя

    Returns:
        Отформатированное сообщение

    """
    total_scans = stats.get("total_scans", 0)
    total_opportunities = stats.get("total_opportunities", 0)
    avg_profit = stats.get("avg_profit", 0.0)
    max_profit = stats.get("max_profit", 0.0)
    last_scan = stats.get("last_scan_time")

    last_scan_str = "Никогда"
    if last_scan:
        now = datetime.now()
        delta = now - last_scan
        if delta < timedelta(minutes=1):
            last_scan_str = "Только что"
        elif delta < timedelta(hours=1):
            minutes = int(delta.total_seconds() / 60)
            last_scan_str = f"{minutes} мин. назад"
        elif delta < timedelta(days=1):
            hours = int(delta.total_seconds() / 3600)
            last_scan_str = f"{hours} ч. назад"
        else:
            days = delta.days
            last_scan_str = f"{days} дн. назад"

    return (
        "📊 *Ваша статистика*\n\n"
        f"🔍 Всего сканирований: *{total_scans}*\n"
        f"💰 Найдено возможностей: *{total_opportunities}*\n"
        f"📈 Средняя прибыль: *${avg_profit:.2f}*\n"
        f"🎯 Максимальная прибыль: *${max_profit:.2f}*\n"
        f"⏰ Последнее сканирование: _{last_scan_str}_\n"
    )


def get_scanner_control_keyboard(level: str | None = None) -> InlineKeyboardMarkup:
    """Создать клавиатуру управления сканером.

    Args:
        level: Выбранный уровень арбитража (если есть)

    Returns:
        InlineKeyboardMarkup с кнопками управления

    """
    if not level:
        # Показать выбор уровня
        keyboard = []
        for level_id, level_data in ARBITRAGE_LEVELS.items():
            emoji = level_data.get("emoji", "📊")
            name = level_data.get("name", level_id)
            keyboard.append(
                [
                    InlineKeyboardButton(
                        f"{emoji} {name}",
                        callback_data=f"{DASHBOARD_ACTION}_scanner_level_{level_id}",
                    ),
                ],
            )
        keyboard.append(
            [
                InlineKeyboardButton(
                    "« Назад к дашборду",
                    callback_data=DASHBOARD_ACTION,
                ),
            ],
        )
    else:
        # Показать управление для выбранного уровня
        keyboard = [
            [
                InlineKeyboardButton(
                    "▶️ Запустить сканирование",
                    callback_data=f"{DASHBOARD_ACTION}_scan_start_{level}",
                ),
            ],
            [
                InlineKeyboardButton(
                    "⚙️ Настройки уровня",
                    callback_data=f"{DASHBOARD_ACTION}_scan_settings_{level}",
                ),
            ],
            [
                InlineKeyboardButton(
                    "« Назад к уровням",
                    callback_data=f"{DASHBOARD_ACTION}_{DASHBOARD_SCANNER}",
                ),
            ],
        ]

    return InlineKeyboardMarkup(keyboard)


@handle_exceptions(logger_instance=logger, default_error_message="Ошибка дашборда", reraise=False)
async def show_dashboard(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Показать главный дашборд.

    Args:
        update: Объект Update от Telegram
        context: Контекст выполнения

    """
    query = update.callback_query
    if query:
        await query.answer()

    if not update.effective_user:
        return
    user_id = update.effective_user.id
    stats = dashboard.get_user_stats(user_id)
    active_scan = dashboard.get_active_scan(user_id)

    # Формируем сообщение
    message = "🎛️ *Дашборд DMarket Bot*\n\n"
    message += format_stats_message(stats)

    if active_scan and active_scan.get("status") == "running":
        level = active_scan.get("level", "unknown")
        game = active_scan.get("game", "unknown")
        started = active_scan.get("started_at")
        elapsed = ""
        if started:
            delta = datetime.now() - started
            elapsed = f" ({int(delta.total_seconds())}с)"
        message += f"\n⚡ *Активное сканирование:* {level} ({game}){elapsed}\n"

    keyboard = get_dashboard_keyboard()

    if query:
        await query.edit_message_text(
            message,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN,
        )
    elif update.message:
        await update.message.reply_text(
            message,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN,
        )


@handle_exceptions(logger_instance=logger, default_error_message="Ошибка статистики", reraise=False)
async def show_stats(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Показать расширенную статистику.

    Args:
        update: Объект Update от Telegram
        context: Контекст выполнения

    """
    query = update.callback_query
    if not query:
        return
    await query.answer()

    if not update.effective_user:
        return
    user_id = update.effective_user.id
    stats = dashboard.get_user_stats(user_id)

    message = format_stats_message(stats)
    message += "\n_Для возврата в дашборд нажмите кнопку ниже_"

    keyboard = [
        [
            InlineKeyboardButton(
                "« Назад к дашборду",
                callback_data=DASHBOARD_ACTION,
            ),
        ],
    ]

    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN,
    )


@handle_exceptions(
    logger_instance=logger, default_error_message="Ошибка меню сканера", reraise=False
)
async def show_scanner_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Показать меню управления сканером.

    Args:
        update: Объект Update от Telegram
        context: Контекст выполнения

    """
    query = update.callback_query
    if not query:
        return
    await query.answer()

    message = "🔍 *Управление сканером*\n\nВыберите уровень арбитража для сканирования:\n\n"

    for level_id, level_data in ARBITRAGE_LEVELS.items():
        emoji = level_data.get("emoji", "📊")
        name = level_data.get("name", level_id)
        price_range = level_data.get("price_range", "")
        min_profit = level_data.get("min_profit_percent", 0.0)
        message += f"{emoji} *{name}*: {price_range}, мин. {min_profit}%\n"

    keyboard = get_scanner_control_keyboard()

    await query.edit_message_text(
        message,
        reply_markup=keyboard,
        parse_mode=ParseMode.MARKDOWN,
    )


@handle_exceptions(
    logger_instance=logger,
    default_error_message="Ошибка активных сканов",
    reraise=False,
)
async def show_active_scans(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Показать активные сканирования.

    Args:
        update: Объект Update от Telegram
        context: Контекст выполнения

    """
    query = update.callback_query
    if not query:
        return
    await query.answer()

    if not update.effective_user:
        return
    user_id = update.effective_user.id
    active_scan = dashboard.get_active_scan(user_id)

    if not active_scan:
        message = "⚡ *Активные сканирования*\n\n_Нет активных сканирований_"
    else:
        level = active_scan.get("level", "unknown")
        game = active_scan.get("game", "unknown")
        status = active_scan.get("status", "unknown")
        started = active_scan.get("started_at")

        elapsed = "N/A"
        if started:
            delta = datetime.now() - started
            minutes = int(delta.total_seconds() / 60)
            seconds = int(delta.total_seconds() % 60)
            elapsed = f"{minutes}м {seconds}с"

        status_emoji = "⏳" if status == "running" else "✅"

        message = (
            f"⚡ *Активные сканирования*\n\n"
            f"{status_emoji} Уровень: *{level}*\n"
            f"🎮 Игра: *{game}*\n"
            f"⏱️ Время выполнения: _{elapsed}_\n"
            f"📊 Статус: _{status}_"
        )

    keyboard = [
        [
            InlineKeyboardButton(
                "« Назад к дашборду",
                callback_data=DASHBOARD_ACTION,
            ),
        ],
    ]

    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN,
    )


@handle_exceptions(logger_instance=logger, default_error_message="Ошибка истории", reraise=False)
async def show_history(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Показать историю сканирований.

    Args:
        update: Объект Update от Telegram
        context: Контекст выполнения

    """
    query = update.callback_query
    if not query:
        return
    await query.answer()

    if not update.effective_user:
        return
    user_id = update.effective_user.id
    user_scans = [s for s in dashboard.scan_history if s["user_id"] == user_id]

    if not user_scans:
        message = "📜 *История сканирований*\n\n_История пуста_"
    else:
        message = f"📜 *История сканирований* (последние {min(10, len(user_scans))})\n\n"

        for i, scan in enumerate(user_scans[:10], 1):
            timestamp = scan["timestamp"]
            data = scan["data"]
            level = data.get("level", "unknown")
            opportunities = len(data.get("opportunities", []))

            time_str = timestamp.strftime("%d.%m %H:%M")
            message += f"{i}. {time_str} - {level}: {opportunities} возм.\n"

    keyboard = [
        [
            InlineKeyboardButton(
                "« Назад к дашборду",
                callback_data=DASHBOARD_ACTION,
            ),
        ],
    ]

    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN,
    )


@handle_exceptions(logger_instance=logger, default_error_message="Ошибка графиков", reraise=False)
async def show_charts(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Показать графики статистики.

    Args:
        update: Объект Update от Telegram
        context: Контекст выполнения

    """
    query = update.callback_query
    if not query:
        return
    await query.answer("Генерирую графики...")

    if not update.effective_user:
        return
    user_id = update.effective_user.id

    if not query.message or not isinstance(query.message, Message):
        return
    message = query.message
    # Отправляем сообщение о загрузке
    loading_msg = await message.reply_text(
        "⏳ Генерирую графики, пожалуйста подождите...",
    )

    try:
        # Собираем данные для графиков
        user_scans = [s for s in dashboard.scan_history if s["user_id"] == user_id]

        if not user_scans:
            await loading_msg.edit_text(
                "📊 *Графики*\n\n_Недостаточно данных для генерации графиков_\n\n"
                "Выполните несколько сканирований для накопления статистики.",
                parse_mode=ParseMode.MARKDOWN,
            )
            return

        # График истории сканирований (последние 10)
        history_data = []
        for scan in user_scans[:10]:
            history_data.append(
                {
                    "date": scan["timestamp"].strftime("%d.%m"),
                    "count": len(scan["data"].get("opportunities", [])),
                },
            )

        history_chart_url = await generate_scan_history_chart(history_data)

        # Распределение по уровням
        level_counts: dict[str, int] = {}
        for scan in user_scans:
            level = scan["data"].get("level", "unknown")
            level_counts[level] = level_counts.get(level, 0) + 1

        distribution_chart_url = await generate_level_distribution_chart(
            level_counts,
        )

        # Сравнение прибыли по уровням
        level_profits: dict[str, list[float]] = {}
        for scan in user_scans:
            level = scan["data"].get("level", "unknown")
            opps = scan["data"].get("opportunities", [])
            if level not in level_profits:
                level_profits[level] = []
            for opp in opps:
                level_profits[level].append(opp.get("profit", 0.0))

        levels = list(level_profits.keys())
        avg_profits = [
            (sum(level_profits[level]) / len(level_profits[level]) if level_profits[level] else 0)
            for level in levels
        ]
        max_profits = [max(level_profits[level]) if level_profits[level] else 0 for level in levels]

        comparison_chart_url = await generate_profit_comparison_chart(
            levels,
            avg_profits,
            max_profits,
        )

        # Удаляем сообщение о загрузке
        await loading_msg.delete()

        # Отправляем графики
        caption = "📊 *Графики статистики*\n\n"

        if history_chart_url:
            await message.reply_photo(
                photo=history_chart_url,
                caption=caption + "История сканирований за последние дни",
                parse_mode=ParseMode.MARKDOWN,
            )

        if distribution_chart_url:
            await message.reply_photo(
                photo=distribution_chart_url,
                caption="Распределение сканирований по уровням",
            )

        if comparison_chart_url:
            await message.reply_photo(
                photo=comparison_chart_url,
                caption="Сравнение прибыли по уровням",
            )

        # Кнопка возврата
        keyboard = [
            [
                InlineKeyboardButton(
                    "« Назад к дашборду",
                    callback_data=DASHBOARD_ACTION,
                ),
            ],
        ]
        await message.reply_text(
            "Графики сгенерированы ✅",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    except Exception as e:
        logger.exception(f"Ошибка при генерации графиков: {e}")
        await loading_msg.edit_text(
            "❌ Произошла ошибка при генерации графиков.\n\nПопробуйте позже.",
        )


def register_dashboard_handlers(application: Application) -> None:  # type: ignore[type-arg]
    """Зарегистрировать обработчики дашборда.

    Args:
        application: Экземпляр Telegram Application

    """
    application.add_handler(
        CallbackQueryHandler(
            show_dashboard,
            pattern=f"^{DASHBOARD_ACTION}$",
        ),
    )

    application.add_handler(
        CallbackQueryHandler(
            show_stats,
            pattern=f"^{DASHBOARD_ACTION}_{DASHBOARD_STATS}$",
        ),
    )

    application.add_handler(
        CallbackQueryHandler(
            show_scanner_menu,
            pattern=f"^{DASHBOARD_ACTION}_{DASHBOARD_SCANNER}$",
        ),
    )

    application.add_handler(
        CallbackQueryHandler(
            show_active_scans,
            pattern=f"^{DASHBOARD_ACTION}_{DASHBOARD_ACTIVE_SCANS}$",
        ),
    )

    application.add_handler(
        CallbackQueryHandler(
            show_history,
            pattern=f"^{DASHBOARD_ACTION}_{DASHBOARD_HISTORY}$",
        ),
    )

    application.add_handler(
        CallbackQueryHandler(
            show_charts,
            pattern=f"^{DASHBOARD_ACTION}_{DASHBOARD_CHARTS}$",
        ),
    )

    application.add_handler(
        CallbackQueryHandler(
            show_dashboard,
            pattern=f"^{DASHBOARD_ACTION}_{DASHBOARD_REFRESH}$",
        ),
    )

    logger.info("Dashboard handlers registered")
