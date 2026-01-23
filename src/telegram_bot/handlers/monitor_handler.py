"""Telegram handler for Channel Monitoring.

Provides commands for managing Telethon channel monitoring:
- /monitor - Show monitoring status and controls
- /monitor_add <channel> - Add channel to monitor
- /monitor_signals - View detected signals

Usage:
    handler = MonitorHandler()
    app.add_handler(CommandHandler("monitor", handler.handle_monitor_command))
"""

from __future__ import annotations

from datetime import UTC, datetime
import logging
from typing import Any

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes

from src.monitoring import DetectedSignal, MockTelethonMonitor, SignalType, create_telethon_monitor


logger = logging.getLogger(__name__)


# Signal type emoji mapping
SIGNAL_EMOJI: dict[SignalType, str] = {
    SignalType.ARBITRAGE: "💰",
    SignalType.PRICE_DROP: "📉",
    SignalType.NEW_LISTING: "🆕",
    SignalType.TRADE_SIGNAL: "📊",
    SignalType.NEWS: "📰",
    SignalType.OTHER: "💬",
}

# Signal type Russian names
SIGNAL_NAMES_RU: dict[SignalType, str] = {
    SignalType.ARBITRAGE: "Арбитраж",
    SignalType.PRICE_DROP: "Снижение цены",
    SignalType.NEW_LISTING: "Новый лот",
    SignalType.TRADE_SIGNAL: "Торговый сигнал",
    SignalType.NEWS: "Новости",
    SignalType.OTHER: "Прочее",
}


class MonitorHandler:
    """Handler for channel monitoring commands.

    Manages Telethon-based channel monitoring for trade signals.
    """

    def __init__(
        self,
        api_id: int | None = None,
        api_hash: str | None = None,
        notify_callback: Any = None,
    ) -> None:
        """Initialize handler.

        Args:
            api_id: Telegram API ID
            api_hash: Telegram API Hash
            notify_callback: Callback for signal notifications
        """
        self._api_id = api_id
        self._api_hash = api_hash
        self._notify_callback = notify_callback

        # Initialize monitor (mock if no credentials)
        self._monitor = create_telethon_monitor(
            api_id=api_id,
            api_hash=api_hash,
            use_mock=not (api_id and api_hash),
        )

        # Default channels with keywords
        self._default_channels = {
            "@dmarket_deals": ["арбитраж", "скидка", "profit", "дешево"],
            "@csgo_trade": ["trade", "сделка", "обмен"],
        }

        # User notification settings
        self._user_settings: dict[int, dict[str, Any]] = {}

    async def handle_monitor_command(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:
        """Handle /monitor command."""
        if not update.message or not update.effective_user:
            return

        stats = self._monitor.get_stats()

        # Status indicator
        if stats.get("is_mock"):
            status_text = "🔶 Mock Mode (Telethon не настроен)"
        elif stats.get("is_running"):
            status_text = "🟢 Активен"
        else:
            status_text = "🔴 Остановлен"

        text = (
            f"📡 *Мониторинг каналов*\n\n"
            f"*Статус:* {status_text}\n"
            f"*Каналов:* {stats.get('channels_count', 0)}\n"
            f"*Сигналов обнаружено:* {stats.get('signals_detected', 0)}\n"
        )

        if stats.get("uptime"):
            text += f"*Uptime:* {stats['uptime']}\n"

        text += (
            "\n_Мониторинг каналов Telegram для обнаружения "
            "торговых сигналов и арбитражных возможностей._"
        )

        keyboard = self._create_monitor_keyboard()

        await update.message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )

    async def handle_callback(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:
        """Handle monitor callback queries."""
        query = update.callback_query
        if not query or not query.data:
            return

        await query.answer()

        data = query.data
        parts = data.split(":")

        action = parts[1] if len(parts) > 1 else ""

        if action == "status":
            await self._show_status(query)
        elif action == "channels":
            await self._show_channels(query)
        elif action == "signals":
            await self._show_signals(query)
        elif action == "settings":
            await self._show_settings(query)
        elif action == "start":
            await self._start_monitor(query)
        elif action == "stop":
            await self._stop_monitor(query)
        elif action == "add_default":
            await self._add_default_channels(query)
        elif action == "test_signal":
            await self._test_signal(query)
        elif action == "back":
            keyboard = self._create_monitor_keyboard()
            await query.edit_message_text(
                "📡 *Мониторинг каналов*\n\nВыберите действие:",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown",
            )

    async def _show_status(self, query: Any) -> None:
        """Show detailed monitoring status."""
        stats = self._monitor.get_stats()

        text = "📊 *Статус мониторинга*\n\n"

        if stats.get("is_mock"):
            text += (
                "⚠️ *Mock Mode*\n"
                "Telethon не настроен. Для реального мониторинга:\n"
                "1. Получите API credentials на my.telegram.org\n"
                "2. Установите TELETHON_API_ID и TELETHON_API_HASH\n\n"
            )

        text += f"*Активен:* {'Да' if stats.get('is_running') else 'Нет'}\n"

        if stats.get("uptime"):
            text += f"*Время работы:* {stats['uptime']}\n"

        text += "\n*Статистика:*\n"
        text += f"├ Каналов: {stats.get('channels_count', 0)}\n"
        text += f"└ Сигналов: {stats.get('signals_detected', 0)}\n"

        keyboard = [
            [
                InlineKeyboardButton(
                    "▶️ Запустить" if not stats.get("is_running") else "⏹️ Остановить",
                    callback_data="monitor:start"
                    if not stats.get("is_running")
                    else "monitor:stop",
                ),
            ],
            [
                InlineKeyboardButton("📋 Каналы", callback_data="monitor:channels"),
                InlineKeyboardButton("📊 Сигналы", callback_data="monitor:signals"),
            ],
            [InlineKeyboardButton("◀️ Назад", callback_data="monitor:back")],
        ]

        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )

    async def _show_channels(self, query: Any) -> None:
        """Show monitored channels."""
        stats = self._monitor.get_stats()
        channels = stats.get("channels", [])

        text = "📋 *Отслеживаемые каналы*\n\n"

        if not channels:
            text += "_Нет добавленных каналов._\n\n"
            text += "Добавьте каналы для мониторинга."
        else:
            for ch in channels:
                status_emoji = "🟢" if ch.get("is_active") else "🔴"
                text += (
                    f"{status_emoji} `{ch['id']}`\n"
                    f"   📝 Keywords: {', '.join(ch.get('keywords', [])[:3]) or 'все'}\n"
                    f"   📊 Обработано: {ch.get('messages_processed', 0)}\n\n"
                )

        keyboard = [
            [
                InlineKeyboardButton(
                    "➕ Добавить стандартные",
                    callback_data="monitor:add_default",
                ),
            ],
            [
                InlineKeyboardButton("🧪 Тест сигнала", callback_data="monitor:test_signal"),
            ],
            [InlineKeyboardButton("◀️ Назад", callback_data="monitor:back")],
        ]

        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )

    async def _show_signals(self, query: Any) -> None:
        """Show recent detected signals."""
        signals = self._monitor.get_recent_signals(limit=10)

        text = "📊 *Последние сигналы*\n\n"

        if not signals:
            text += "_Сигналов пока не обнаружено._\n\n"
            text += "Сигналы появятся здесь когда будут обнаружены сообщения с ключевыми словами."
        else:
            for signal in reversed(signals[-5:]):
                emoji = SIGNAL_EMOJI.get(signal.signal_type, "💬")
                name = SIGNAL_NAMES_RU.get(signal.signal_type, "Прочее")
                conf = int(signal.confidence * 100)

                text += f"{emoji} *{name}* ({conf}%)\n"
                text += f"   📍 {signal.source_channel}\n"

                if signal.item_name:
                    text += f"   🎯 {signal.item_name}\n"
                if signal.price:
                    text += f"   💰 ${signal.price:.2f}\n"
                if signal.discount_percent:
                    text += f"   📉 -{signal.discount_percent:.0f}%\n"

                # Time ago
                delta = datetime.now(UTC) - signal.timestamp
                if delta.seconds < 60:
                    time_str = f"{delta.seconds}с назад"
                elif delta.seconds < 3600:
                    time_str = f"{delta.seconds // 60}м назад"
                else:
                    time_str = f"{delta.seconds // 3600}ч назад"

                text += f"   ⏱️ {time_str}\n\n"

        keyboard = [
            [
                InlineKeyboardButton(
                    "💰 Только арбитраж",
                    callback_data="monitor:signals:arbitrage",
                ),
            ],
            [
                InlineKeyboardButton("🔄 Обновить", callback_data="monitor:signals"),
            ],
            [InlineKeyboardButton("◀️ Назад", callback_data="monitor:back")],
        ]

        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )

    async def _show_settings(self, query: Any) -> None:
        """Show monitor settings."""
        text = "⚙️ *Настройки мониторинга*\n\n*Типы сигналов:*\n"

        for sig_type in SignalType:
            emoji = SIGNAL_EMOJI.get(sig_type, "💬")
            name = SIGNAL_NAMES_RU.get(sig_type, sig_type.value)
            text += f"├ {emoji} {name}\n"

        text += "\n*Уведомления:*\n├ Мгновенные: ✅\n├ Мин. уверенность: 50%\n└ Тихие часы: выкл\n"

        keyboard = [
            [InlineKeyboardButton("◀️ Назад", callback_data="monitor:back")],
        ]

        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )

    async def _start_monitor(self, query: Any) -> None:
        """Start the monitor."""
        try:
            # For mock monitor, just set running flag
            if isinstance(self._monitor, MockTelethonMonitor):
                await self._monitor.start()
                await query.edit_message_text(
                    "✅ Мониторинг запущен (Mock Mode)\n\nИспользуйте 'Тест сигнала' для проверки.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("◀️ Назад", callback_data="monitor:back")]
                    ]),
                )
            else:
                # Real Telethon monitor runs in background
                await query.edit_message_text(
                    "⏳ Запуск мониторинга...\n\nЭто может занять несколько секунд.",
                )
                # Would need to run in background task
                # asyncio.create_task(self._monitor.start())

        except Exception as e:
            logger.exception(f"Monitor start error: {e}")
            await query.edit_message_text(f"❌ Ошибка запуска: {e}")

    async def _stop_monitor(self, query: Any) -> None:
        """Stop the monitor."""
        try:
            await self._monitor.stop()
            await query.edit_message_text(
                "⏹️ Мониторинг остановлен",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("◀️ Назад", callback_data="monitor:back")]
                ]),
            )
        except Exception as e:
            logger.exception(f"Monitor stop error: {e}")
            await query.edit_message_text(f"❌ Ошибка: {e}")

    async def _add_default_channels(self, query: Any) -> None:
        """Add default channels."""
        added = []

        for channel, keywords in self._default_channels.items():
            self._monitor.add_channel(channel, keywords=keywords)
            added.append(channel)

        text = (
            "✅ *Добавлены каналы:*\n\n"
            + "\n".join(f"• `{ch}`" for ch in added)
            + "\n\n_Это демонстрационные каналы. "
            "Добавьте свои через /monitor\\_add_"
        )

        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📋 Просмотреть", callback_data="monitor:channels")],
                [InlineKeyboardButton("◀️ Назад", callback_data="monitor:back")],
            ]),
            parse_mode="Markdown",
        )

    async def _test_signal(self, query: Any) -> None:
        """Test signal detection with sample message."""
        if not isinstance(self._monitor, MockTelethonMonitor):
            await query.edit_message_text(
                "❌ Тестовые сигналы доступны только в Mock Mode",
            )
            return

        # Sample messages for testing
        test_messages = [
            "🔥 Арбитраж! AK-47 | Redline за $15.50, профит 12%! https://dmarket.com/item/123",
            "📉 Скидка 25%! AWP Asiimov $45 ниже рынка!",
            "Новый лот: M4A1-S Hyper Beast только выставлен, дешево!",
        ]

        import random

        test_msg = random.choice(test_messages)  # noqa: S311

        signal = self._monitor.simulate_message(test_msg, "@test_channel")

        if signal:
            emoji = SIGNAL_EMOJI.get(signal.signal_type, "💬")
            name = SIGNAL_NAMES_RU.get(signal.signal_type, "Прочее")

            text = (
                f"🧪 *Тестовый сигнал обнаружен!*\n\n"
                f"*Сообщение:*\n_{test_msg}_\n\n"
                f"*Результат:*\n"
                f"├ Тип: {emoji} {name}\n"
                f"├ Уверенность: {signal.confidence:.0%}\n"
                f"├ Keywords: {', '.join(signal.keywords_matched)}\n"
            )

            if signal.item_name:
                text += f"├ Предмет: {signal.item_name}\n"
            if signal.price:
                text += f"├ Цена: ${signal.price:.2f}\n"
            if signal.discount_percent:
                text += f"└ Скидка: {signal.discount_percent:.0f}%\n"
        else:
            text = "❌ Сигнал не обнаружен в тестовом сообщении."

        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🧪 Ещё тест", callback_data="monitor:test_signal")],
                [InlineKeyboardButton("◀️ Назад", callback_data="monitor:back")],
            ]),
            parse_mode="Markdown",
        )

    def _create_monitor_keyboard(self) -> list[list[InlineKeyboardButton]]:
        """Create main monitor keyboard."""
        return [
            [
                InlineKeyboardButton("📊 Статус", callback_data="monitor:status"),
                InlineKeyboardButton("📋 Каналы", callback_data="monitor:channels"),
            ],
            [
                InlineKeyboardButton("📈 Сигналы", callback_data="monitor:signals"),
                InlineKeyboardButton("⚙️ Настройки", callback_data="monitor:settings"),
            ],
            [
                InlineKeyboardButton("◀️ Главное меню", callback_data="main_menu"),
            ],
        ]

    async def on_signal_detected(self, signal: DetectedSignal) -> None:
        """Handle detected signal - forward to users.

        This is called by TelethonMonitor when a signal is detected.
        """
        if self._notify_callback:
            emoji = SIGNAL_EMOJI.get(signal.signal_type, "💬")
            name = SIGNAL_NAMES_RU.get(signal.signal_type, "Прочее")

            text = f"{emoji} *Обнаружен сигнал: {name}*\n\n*Источник:* {signal.source_channel}\n"

            if signal.item_name:
                text += f"*Предмет:* {signal.item_name}\n"
            if signal.price:
                text += f"*Цена:* ${signal.price:.2f}\n"
            if signal.discount_percent:
                text += f"*Скидка:* {signal.discount_percent:.0f}%\n"
            if signal.url:
                text += f"*Ссылка:* {signal.url}\n"

            text += f"\n_Уверенность: {signal.confidence:.0%}_"

            try:
                await self._notify_callback(text)
            except Exception as e:
                logger.exception(f"Notification error: {e}")

    def get_handlers(self) -> list:
        """Get list of handlers for registration."""
        return [
            CommandHandler("monitor", self.handle_monitor_command),
            CallbackQueryHandler(
                self.handle_callback,
                pattern=r"^monitor:",
            ),
        ]


__all__ = ["MonitorHandler"]
