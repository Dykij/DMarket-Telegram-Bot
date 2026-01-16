"""Alert Throttling - предотвращение спама уведомлениями.

Этот модуль обеспечивает:
1. Throttling уведомлений по типу и приоритету
2. Группировка похожих алертов
3. Настраиваемые cooldown периоды
4. Дайджесты сгруппированных алертов
5. Метрики для мониторинга

Использование:
    >>> throttler = AlertThrottler()
    >>> if throttler.should_send("api_error", AlertPriority.HIGH):
    ...     await send_notification("API Error occurred")
    ...     throttler.record_sent("api_error", AlertPriority.HIGH)

Created: January 2026
"""

from __future__ import annotations

import asyncio
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import IntEnum, StrEnum
from typing import TYPE_CHECKING, Any

import structlog


if TYPE_CHECKING:
    from collections.abc import Callable


logger = structlog.get_logger(__name__)


class AlertPriority(IntEnum):
    """Приоритет алертов (чем выше число, тем выше приоритет)."""

    LOW = 1  # Информационные сообщения
    MEDIUM = 2  # Предупреждения
    HIGH = 3  # Важные ошибки
    CRITICAL = 4  # Критические ошибки (всегда отправляются)


class AlertCategory(StrEnum):
    """Категории алертов для группировки."""

    API_ERROR = "api_error"
    RATE_LIMIT = "rate_limit"
    TRADE_ERROR = "trade_error"
    TRADE_SUCCESS = "trade_success"
    BALANCE_LOW = "balance_low"
    HEALTH_CHECK = "health_check"
    SYSTEM = "system"
    ARBITRAGE = "arbitrage"
    TARGET = "target"
    OTHER = "other"


@dataclass
class AlertRecord:
    """Запись об отправленном алерте.

    Attributes:
        category: Категория алерта
        priority: Приоритет
        sent_at: Время отправки
        message: Сообщение (опционально)
        count: Количество похожих алертов
    """

    category: str
    priority: AlertPriority
    sent_at: datetime
    message: str = ""
    count: int = 1


@dataclass
class PendingAlert:
    """Ожидающий алерт для группировки.

    Attributes:
        category: Категория алерта
        priority: Приоритет
        messages: Список сообщений
        first_at: Время первого алерта
        last_at: Время последнего алерта
    """

    category: str
    priority: AlertPriority
    messages: list[str] = field(default_factory=list)
    first_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    last_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def add_message(self, message: str) -> None:
        """Добавить сообщение в группу."""
        self.messages.append(message)
        self.last_at = datetime.now(UTC)

    @property
    def count(self) -> int:
        """Количество сообщений в группе."""
        return len(self.messages)


class AlertThrottler:
    """Throttler для предотвращения спама уведомлениями.

    Особенности:
    - Разные cooldown периоды для разных приоритетов
    - Критические алерты всегда отправляются
    - Группировка похожих алертов
    - Дайджесты для низкоприоритетных уведомлений

    Пример:
        throttler = AlertThrottler()

        # Проверить, можно ли отправить
        if throttler.should_send("api_error", AlertPriority.HIGH):
            await send_telegram("API Error!")
            throttler.record_sent("api_error", AlertPriority.HIGH)

        # Или использовать декоратор
        @throttler.throttled(category="api_error", priority=AlertPriority.HIGH)
        async def send_api_error_alert(message: str):
            await telegram.send(message)
    """

    # Cooldown периоды по умолчанию (в секундах)
    DEFAULT_COOLDOWNS = {
        AlertPriority.LOW: 3600,  # 1 час
        AlertPriority.MEDIUM: 900,  # 15 минут
        AlertPriority.HIGH: 300,  # 5 минут
        AlertPriority.CRITICAL: 0,  # Всегда отправлять
    }

    def __init__(
        self,
        cooldowns: dict[AlertPriority, int] | None = None,
        max_history_size: int = 1000,
        digest_interval: int = 1800,  # 30 минут
    ) -> None:
        """Инициализация throttler.

        Args:
            cooldowns: Кастомные cooldown периоды по приоритетам
            max_history_size: Максимальный размер истории алертов
            digest_interval: Интервал отправки дайджестов (секунды)
        """
        self._cooldowns = cooldowns or self.DEFAULT_COOLDOWNS.copy()
        self._max_history = max_history_size
        self._digest_interval = timedelta(seconds=digest_interval)

        # История отправленных алертов: {category: [AlertRecord, ...]}
        self._sent_alerts: dict[str, list[AlertRecord]] = defaultdict(list)

        # Подавленные алерты для дайджестов: {category: PendingAlert}
        self._suppressed: dict[str, PendingAlert] = {}

        # Статистика
        self._total_sent = 0
        self._total_suppressed = 0
        self._total_critical = 0

        # Lock для thread safety
        self._lock = asyncio.Lock()

        logger.info(
            "alert_throttler_initialized",
            cooldowns=self._cooldowns,
            digest_interval=digest_interval,
        )

    def should_send(
        self,
        category: str,
        priority: AlertPriority = AlertPriority.MEDIUM,
        custom_cooldown: int | None = None,
    ) -> bool:
        """Проверить, можно ли отправить алерт.

        Args:
            category: Категория алерта
            priority: Приоритет алерта
            custom_cooldown: Кастомный cooldown (опционально)

        Returns:
            True если алерт можно отправить
        """
        # Критические алерты всегда отправляются
        if priority == AlertPriority.CRITICAL:
            return True

        # Получить cooldown для приоритета
        cooldown_seconds = custom_cooldown or self._cooldowns.get(
            priority,
            self.DEFAULT_COOLDOWNS[AlertPriority.MEDIUM],
        )

        # Проверить последний алерт этой категории
        last_alert = self._get_last_alert(category)
        if last_alert is None:
            return True

        # Проверить, прошёл ли cooldown
        elapsed = (datetime.now(UTC) - last_alert.sent_at).total_seconds()
        return elapsed >= cooldown_seconds

    def record_sent(
        self,
        category: str,
        priority: AlertPriority = AlertPriority.MEDIUM,
        message: str = "",
    ) -> None:
        """Записать отправленный алерт.

        Args:
            category: Категория алерта
            priority: Приоритет
            message: Сообщение (опционально)
        """
        record = AlertRecord(
            category=category,
            priority=priority,
            sent_at=datetime.now(UTC),
            message=message,
        )

        self._sent_alerts[category].append(record)
        self._total_sent += 1

        if priority == AlertPriority.CRITICAL:
            self._total_critical += 1

        # Очистить старые записи
        self._cleanup_history(category)

        # Очистить подавленные алерты для этой категории
        if category in self._suppressed:
            del self._suppressed[category]

        self._track_metrics("sent", category, priority)

        logger.debug(
            "alert_sent_recorded",
            category=category,
            priority=priority.name,
        )

    def record_suppressed(
        self,
        category: str,
        priority: AlertPriority = AlertPriority.MEDIUM,
        message: str = "",
    ) -> None:
        """Записать подавленный алерт.

        Args:
            category: Категория алерта
            priority: Приоритет
            message: Сообщение для группировки
        """
        self._total_suppressed += 1

        if category not in self._suppressed:
            self._suppressed[category] = PendingAlert(
                category=category,
                priority=priority,
            )

        self._suppressed[category].add_message(message)
        self._track_metrics("suppressed", category, priority)

        logger.debug(
            "alert_suppressed",
            category=category,
            priority=priority.name,
            suppressed_count=self._suppressed[category].count,
        )

    async def process_with_throttle(
        self,
        category: str,
        priority: AlertPriority,
        message: str,
        send_func: Callable[[str], Any],
    ) -> bool:
        """Обработать алерт с throttling.

        Args:
            category: Категория алерта
            priority: Приоритет
            message: Сообщение
            send_func: Функция отправки

        Returns:
            True если алерт был отправлен
        """
        async with self._lock:
            if self.should_send(category, priority):
                await send_func(message)
                self.record_sent(category, priority, message)
                return True

            self.record_suppressed(category, priority, message)
            return False

    def get_pending_digest(
        self,
        category: str | None = None,
    ) -> list[PendingAlert]:
        """Получить ожидающие дайджесты.

        Args:
            category: Фильтр по категории (опционально)

        Returns:
            Список ожидающих алертов для дайджеста
        """
        now = datetime.now(UTC)
        pending = []

        for cat, alert in self._suppressed.items():
            if category and cat != category:
                continue

            # Проверить, прошёл ли интервал дайджеста
            if now - alert.first_at >= self._digest_interval:
                pending.append(alert)

        return pending

    def format_digest(self, alerts: list[PendingAlert]) -> str:
        """Форматировать дайджест алертов.

        Args:
            alerts: Список ожидающих алертов

        Returns:
            Форматированная строка дайджеста
        """
        if not alerts:
            return ""

        lines = ["📋 <b>Alert Digest</b>\n"]

        for alert in alerts:
            emoji = self._get_priority_emoji(alert.priority)
            lines.append(
                f"{emoji} <b>{alert.category}</b>: "
                f"{alert.count} событий за "
                f"{self._format_duration(alert.last_at - alert.first_at)}"
            )

            # Показать примеры сообщений (первые 3)
            if alert.messages:
                for msg in alert.messages[:3]:
                    lines.append(f"  • {msg[:100]}...")
                if len(alert.messages) > 3:
                    lines.append(f"  ... и ещё {len(alert.messages) - 3}")

        return "\n".join(lines)

    def clear_pending(self, category: str | None = None) -> int:
        """Очистить ожидающие алерты.

        Args:
            category: Категория для очистки (None = все)

        Returns:
            Количество очищенных алертов
        """
        if category:
            if category in self._suppressed:
                count = self._suppressed[category].count
                del self._suppressed[category]
                return count
            return 0

        count = sum(a.count for a in self._suppressed.values())
        self._suppressed.clear()
        return count

    def get_stats(self) -> dict[str, Any]:
        """Получить статистику throttler.

        Returns:
            Словарь со статистикой
        """
        category_stats = {}
        for cat, records in self._sent_alerts.items():
            category_stats[cat] = {
                "sent_count": len(records),
                "last_sent": records[-1].sent_at.isoformat() if records else None,
            }

        suppressed_stats = {
            cat: alert.count for cat, alert in self._suppressed.items()
        }

        return {
            "total_sent": self._total_sent,
            "total_suppressed": self._total_suppressed,
            "total_critical": self._total_critical,
            "suppression_rate": (
                self._total_suppressed / (self._total_sent + self._total_suppressed) * 100
                if (self._total_sent + self._total_suppressed) > 0
                else 0
            ),
            "pending_digests": len(self._suppressed),
            "pending_messages": sum(a.count for a in self._suppressed.values()),
            "categories": category_stats,
            "suppressed_by_category": suppressed_stats,
        }

    def set_cooldown(
        self,
        priority: AlertPriority,
        cooldown_seconds: int,
    ) -> None:
        """Установить cooldown для приоритета.

        Args:
            priority: Приоритет
            cooldown_seconds: Cooldown в секундах
        """
        self._cooldowns[priority] = cooldown_seconds
        logger.info(
            "cooldown_updated",
            priority=priority.name,
            cooldown_seconds=cooldown_seconds,
        )

    def _get_last_alert(self, category: str) -> AlertRecord | None:
        """Получить последний алерт категории."""
        records = self._sent_alerts.get(category, [])
        return records[-1] if records else None

    def _cleanup_history(self, category: str) -> None:
        """Очистить старые записи истории."""
        if category not in self._sent_alerts:
            return

        records = self._sent_alerts[category]

        # Удалить записи старше 24 часов
        cutoff = datetime.now(UTC) - timedelta(hours=24)
        self._sent_alerts[category] = [
            r for r in records if r.sent_at > cutoff
        ]

        # Ограничить размер
        if len(self._sent_alerts[category]) > self._max_history:
            self._sent_alerts[category] = self._sent_alerts[category][
                -self._max_history :
            ]

    @staticmethod
    def _get_priority_emoji(priority: AlertPriority) -> str:
        """Получить emoji для приоритета."""
        return {
            AlertPriority.LOW: "ℹ️",
            AlertPriority.MEDIUM: "⚠️",
            AlertPriority.HIGH: "🔴",
            AlertPriority.CRITICAL: "🚨",
        }.get(priority, "📢")

    @staticmethod
    def _format_duration(delta: timedelta) -> str:
        """Форматировать продолжительность."""
        total_seconds = int(delta.total_seconds())

        if total_seconds < 60:
            return f"{total_seconds}с"
        if total_seconds < 3600:
            return f"{total_seconds // 60}м"
        return f"{total_seconds // 3600}ч {(total_seconds % 3600) // 60}м"

    def _track_metrics(
        self,
        action: str,
        category: str,
        priority: AlertPriority,
    ) -> None:
        """Обновить Prometheus метрики."""
        try:
            from src.utils.prometheus_metrics import (
                ALERT_OPERATIONS,
            )

            ALERT_OPERATIONS.labels(
                action=action,
                category=category,
                priority=priority.name.lower(),
            ).inc()
        except ImportError:
            pass


class AlertDigestScheduler:
    """Планировщик для автоматической отправки дайджестов.

    Периодически проверяет накопленные алерты и отправляет дайджесты.
    """

    def __init__(
        self,
        throttler: AlertThrottler,
        send_func: Callable[[str], Any],
        check_interval: int = 300,  # 5 минут
    ) -> None:
        """Инициализация планировщика.

        Args:
            throttler: AlertThrottler для получения дайджестов
            send_func: Функция отправки дайджеста
            check_interval: Интервал проверки (секунды)
        """
        self._throttler = throttler
        self._send_func = send_func
        self._interval = check_interval
        self._running = False
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        """Запустить планировщик."""
        if self._running:
            return

        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("alert_digest_scheduler_started", interval=self._interval)

    async def stop(self) -> None:
        """Остановить планировщик."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("alert_digest_scheduler_stopped")

    async def _run_loop(self) -> None:
        """Основной цикл."""
        while self._running:
            try:
                await self._check_and_send_digests()
                await asyncio.sleep(self._interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception("digest_scheduler_error", error=str(e))
                await asyncio.sleep(60)

    async def _check_and_send_digests(self) -> None:
        """Проверить и отправить дайджесты."""
        pending = self._throttler.get_pending_digest()
        if not pending:
            return

        digest = self._throttler.format_digest(pending)
        if digest:
            await self._send_func(digest)

            # Очистить отправленные
            for alert in pending:
                self._throttler.clear_pending(alert.category)

            logger.info(
                "digest_sent",
                categories=[a.category for a in pending],
                total_messages=sum(a.count for a in pending),
            )


# Глобальный экземпляр
_throttler_instance: AlertThrottler | None = None


def get_alert_throttler() -> AlertThrottler:
    """Получить глобальный экземпляр AlertThrottler.

    Returns:
        AlertThrottler
    """
    global _throttler_instance
    if _throttler_instance is None:
        _throttler_instance = AlertThrottler()
    return _throttler_instance


def set_alert_throttler(throttler: AlertThrottler) -> None:
    """Установить глобальный экземпляр AlertThrottler.

    Args:
        throttler: Экземпляр AlertThrottler
    """
    global _throttler_instance
    _throttler_instance = throttler


__all__ = [
    "AlertCategory",
    "AlertDigestScheduler",
    "AlertPriority",
    "AlertRecord",
    "AlertThrottler",
    "PendingAlert",
    "get_alert_throttler",
    "set_alert_throttler",
]
