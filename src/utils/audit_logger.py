"""
Система аудит-логов для отслеживания действий пользователей и системных событий.

Записывает все важные операции для безопасности, комплаенса и отладки.
"""

import enum
from datetime import datetime
from typing import Any

import structlog
from sqlalchemy import BigInteger, Column, DateTime, Integer, String, Text, JSON
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.base import Base

logger = structlog.get_logger(__name__)


class AuditEventType(str, enum.Enum):
    """Типы аудит событий."""

    # User actions
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_REGISTER = "user_register"
    USER_UPDATE = "user_update"
    USER_DELETE = "user_delete"

    # API key management
    API_KEY_ADD = "api_key_add"
    API_KEY_UPDATE = "api_key_update"
    API_KEY_DELETE = "api_key_delete"
    API_KEY_VIEW = "api_key_view"

    # Trading actions
    TARGET_CREATE = "target_create"
    TARGET_DELETE = "target_delete"
    TARGET_UPDATE = "target_update"
    ITEM_BUY = "item_buy"
    ITEM_SELL = "item_sell"

    # Arbitrage
    ARBITRAGE_SCAN = "arbitrage_scan"
    ARBITRAGE_OPPORTUNITY = "arbitrage_opportunity"

    # Settings
    SETTINGS_UPDATE = "settings_update"
    LANGUAGE_CHANGE = "language_change"

    # Admin actions
    ADMIN_USER_BAN = "admin_user_ban"
    ADMIN_USER_UNBAN = "admin_user_unban"
    ADMIN_RATE_LIMIT_CHANGE = "admin_rate_limit_change"
    ADMIN_FEATURE_FLAG_CHANGE = "admin_feature_flag_change"

    # System events
    SYSTEM_ERROR = "system_error"
    SYSTEM_WARNING = "system_warning"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SECURITY_VIOLATION = "security_violation"


class AuditSeverity(str, enum.Enum):
    """Уровень важности события."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuditLog(Base):
    """Модель аудит лога."""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    # Event info
    event_type = Column(String(50), nullable=False, index=True)
    severity = Column(String(20), nullable=False, default=AuditSeverity.INFO.value)

    # User info
    user_id = Column(BigInteger, nullable=True, index=True)
    username = Column(String(255), nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible

    # Action details
    action = Column(String(255), nullable=False)
    resource_type = Column(String(50), nullable=True)
    resource_id = Column(String(255), nullable=True, index=True)

    # Additional data
    details = Column(JSON, nullable=True)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)

    # Result
    success = Column(String(10), nullable=False, default="true")
    error_message = Column(Text, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<AuditLog(id={self.id}, event={self.event_type}, "
            f"user={self.user_id}, action={self.action})>"
        )


class AuditLogger:
    """
    Менеджер аудит-логирования.

    Записывает все важные действия пользователей и системные события.
    """

    def __init__(self, session: AsyncSession):
        """
        Инициализация.

        Args:
            session: SQLAlchemy async session
        """
        self.session = session

    async def log(
        self,
        event_type: AuditEventType | str,
        action: str,
        user_id: int | None = None,
        username: str | None = None,
        ip_address: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        details: dict[str, Any] | None = None,
        old_value: str | None = None,
        new_value: str | None = None,
        success: bool = True,
        error_message: str | None = None,
        severity: AuditSeverity = AuditSeverity.INFO,
    ) -> AuditLog:
        """
        Записать аудит событие.

        Args:
            event_type: Тип события
            action: Описание действия
            user_id: ID пользователя
            username: Имя пользователя
            ip_address: IP адрес
            resource_type: Тип ресурса
            resource_id: ID ресурса
            details: Дополнительные детали
            old_value: Старое значение (для updates)
            new_value: Новое значение (для updates)
            success: Успешно ли выполнено
            error_message: Сообщение об ошибке
            severity: Уровень важности

        Returns:
            Созданная запись аудит лога
        """
        event_type_str = (
            event_type.value if isinstance(event_type, AuditEventType) else event_type
        )

        audit_log = AuditLog(
            timestamp=datetime.utcnow(),
            event_type=event_type_str,
            severity=severity.value,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            old_value=old_value,
            new_value=new_value,
            success="true" if success else "false",
            error_message=error_message,
        )

        self.session.add(audit_log)
        await self.session.commit()

        # Также логировать в structlog
        logger.info(
            "audit_event",
            event_type=event_type_str,
            action=action,
            user_id=user_id,
            success=success,
            severity=severity.value,
        )

        return audit_log

    async def log_user_action(
        self,
        user_id: int,
        action: str,
        event_type: AuditEventType,
        details: dict[str, Any] | None = None,
        username: str | None = None,
        ip_address: str | None = None,
        success: bool = True,
    ) -> AuditLog:
        """
        Записать действие пользователя.

        Args:
            user_id: ID пользователя
            action: Описание действия
            event_type: Тип события
            details: Дополнительные детали
            username: Имя пользователя
            ip_address: IP адрес
            success: Успешно ли выполнено

        Returns:
            Созданная запись
        """
        return await self.log(
            event_type=event_type,
            action=action,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            details=details,
            success=success,
            severity=AuditSeverity.INFO,
        )

    async def log_security_event(
        self,
        event_type: AuditEventType,
        action: str,
        user_id: int | None = None,
        details: dict[str, Any] | None = None,
        severity: AuditSeverity = AuditSeverity.WARNING,
    ) -> AuditLog:
        """
        Записать событие безопасности.

        Args:
            event_type: Тип события
            action: Описание
            user_id: ID пользователя (если известен)
            details: Дополнительные детали
            severity: Уровень важности

        Returns:
            Созданная запись
        """
        return await self.log(
            event_type=event_type,
            action=action,
            user_id=user_id,
            details=details,
            success=False,
            severity=severity,
        )

    async def log_system_event(
        self,
        action: str,
        event_type: AuditEventType = AuditEventType.SYSTEM_ERROR,
        details: dict[str, Any] | None = None,
        severity: AuditSeverity = AuditSeverity.ERROR,
        error_message: str | None = None,
    ) -> AuditLog:
        """
        Записать системное событие.

        Args:
            action: Описание
            event_type: Тип события
            details: Дополнительные детали
            severity: Уровень важности
            error_message: Сообщение об ошибке

        Returns:
            Созданная запись
        """
        return await self.log(
            event_type=event_type,
            action=action,
            details=details,
            severity=severity,
            error_message=error_message,
            success=False,
        )

    async def get_user_history(
        self,
        user_id: int,
        limit: int = 100,
        event_type: AuditEventType | None = None,
    ) -> list[AuditLog]:
        """
        Получить историю действий пользователя.

        Args:
            user_id: ID пользователя
            limit: Максимальное количество записей
            event_type: Фильтр по типу события

        Returns:
            Список аудит логов
        """
        from sqlalchemy import select

        query = select(AuditLog).where(AuditLog.user_id == user_id)

        if event_type:
            event_type_str = (
                event_type.value if isinstance(event_type, AuditEventType) else event_type
            )
            query = query.where(AuditLog.event_type == event_type_str)

        query = query.order_by(AuditLog.timestamp.desc()).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_security_events(
        self,
        limit: int = 100,
        severity: AuditSeverity | None = None,
    ) -> list[AuditLog]:
        """
        Получить события безопасности.

        Args:
            limit: Максимальное количество записей
            severity: Фильтр по уровню важности

        Returns:
            Список событий безопасности
        """
        from sqlalchemy import select

        security_events = [
            AuditEventType.SECURITY_VIOLATION.value,
            AuditEventType.RATE_LIMIT_EXCEEDED.value,
            AuditEventType.ADMIN_USER_BAN.value,
        ]

        query = select(AuditLog).where(AuditLog.event_type.in_(security_events))

        if severity:
            query = query.where(AuditLog.severity == severity.value)

        query = query.order_by(AuditLog.timestamp.desc()).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def search_logs(
        self,
        user_id: int | None = None,
        event_type: AuditEventType | str | None = None,
        resource_id: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 100,
    ) -> list[AuditLog]:
        """
        Поиск по аудит логам.

        Args:
            user_id: Фильтр по пользователю
            event_type: Фильтр по типу события
            resource_id: Фильтр по ресурсу
            start_date: Начальная дата
            end_date: Конечная дата
            limit: Максимальное количество

        Returns:
            Список найденных логов
        """
        from sqlalchemy import select

        query = select(AuditLog)

        if user_id:
            query = query.where(AuditLog.user_id == user_id)

        if event_type:
            event_type_str = (
                event_type.value if isinstance(event_type, AuditEventType) else event_type
            )
            query = query.where(AuditLog.event_type == event_type_str)

        if resource_id:
            query = query.where(AuditLog.resource_id == resource_id)

        if start_date:
            query = query.where(AuditLog.timestamp >= start_date)

        if end_date:
            query = query.where(AuditLog.timestamp <= end_date)

        query = query.order_by(AuditLog.timestamp.desc()).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())


def audit_decorator(event_type: AuditEventType, action: str):
    """
    Декоратор для автоматического аудит-логирования.

    Args:
        event_type: Тип события
        action: Описание действия

    Example:
        @audit_decorator(AuditEventType.TARGET_CREATE, "Create target")
        async def create_target(user_id: int, ...):
            ...
    """

    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Попытаться извлечь user_id из аргументов
            user_id = kwargs.get("user_id") or (args[0] if args else None)

            try:
                result = await func(*args, **kwargs)

                # Логировать успех (требует session в context)
                # В реальном использовании session должен быть доступен

                return result

            except Exception as e:
                # Логировать ошибку
                logger.error(
                    "audit_decorator_error",
                    event_type=event_type.value,
                    action=action,
                    user_id=user_id,
                    error=str(e),
                )
                raise

        return wrapper

    return decorator
