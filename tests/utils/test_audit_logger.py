"""Тесты для audit_logger.py"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from src.utils.audit_logger import (
    AuditEventType,
    AuditLogger,
    AuditLog,
    AuditSeverity,
)


class TestAuditLogger:
    """Тесты для AuditLogger."""

    @pytest.fixture
    def mock_session(self):
        """Create mock async session."""
        session = AsyncMock()
        session.add = MagicMock()
        session.commit = AsyncMock()
        session.execute = AsyncMock()
        return session

    @pytest.fixture
    def audit_logger(self, mock_session):
        """Create audit logger."""
        return AuditLogger(mock_session)

    @pytest.mark.asyncio
    async def test_log_basic(self, audit_logger, mock_session):
        """Тест базового логирования."""
        result = await audit_logger.log(
            event_type=AuditEventType.USER_LOGIN,
            action="User logged in",
            user_id=12345,
            username="test_user",
        )

        assert isinstance(result, AuditLog)
        assert result.event_type == "user_login"
        assert result.user_id == 12345
        assert result.username == "test_user"
        assert result.success == "true"
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_log_user_action(self, audit_logger, mock_session):
        """Тест логирования действия пользователя."""
        result = await audit_logger.log_user_action(
            user_id=12345,
            action="Created target",
            event_type=AuditEventType.TARGET_CREATE,
            details={"item_name": "AK-47", "price": 10.50},
        )

        assert result.event_type == "target_create"
        assert result.details == {"item_name": "AK-47", "price": 10.50}
        assert result.severity == AuditSeverity.INFO.value

    @pytest.mark.asyncio
    async def test_log_security_event(self, audit_logger, mock_session):
        """Тест логирования события безопасности."""
        result = await audit_logger.log_security_event(
            event_type=AuditEventType.RATE_LIMIT_EXCEEDED,
            action="Rate limit exceeded",
            user_id=12345,
            details={"requests": 100, "limit": 30},
            severity=AuditSeverity.WARNING,
        )

        assert result.event_type == "rate_limit_exceeded"
        assert result.severity == AuditSeverity.WARNING.value
        assert result.success == "false"

    @pytest.mark.asyncio
    async def test_log_system_event(self, audit_logger, mock_session):
        """Тест логирования системного события."""
        result = await audit_logger.log_system_event(
            action="Database connection failed",
            event_type=AuditEventType.SYSTEM_ERROR,
            details={"database": "postgresql"},
            severity=AuditSeverity.CRITICAL,
            error_message="Connection timeout",
        )

        assert result.event_type == "system_error"
        assert result.severity == AuditSeverity.CRITICAL.value
        assert result.error_message == "Connection timeout"

    @pytest.mark.asyncio
    async def test_get_user_history(self, audit_logger, mock_session):
        """Тест получения истории пользователя."""
        # Mock результатов запроса
        mock_logs = [
            AuditLog(
                id=1,
                event_type="user_login",
                action="Login",
                user_id=12345,
            ),
            AuditLog(
                id=2,
                event_type="target_create",
                action="Create target",
                user_id=12345,
            ),
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_logs
        mock_session.execute.return_value = mock_result

        history = await audit_logger.get_user_history(user_id=12345, limit=10)

        assert len(history) == 2
        assert all(log.user_id == 12345 for log in history)
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_security_events(self, audit_logger, mock_session):
        """Тест получения событий безопасности."""
        mock_logs = [
            AuditLog(
                id=1,
                event_type="security_violation",
                action="Unauthorized access attempt",
                severity="warning",
            ),
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_logs
        mock_session.execute.return_value = mock_result

        events = await audit_logger.get_security_events(limit=10)

        assert len(events) == 1
        assert events[0].event_type == "security_violation"

    @pytest.mark.asyncio
    async def test_search_logs(self, audit_logger, mock_session):
        """Тест поиска логов."""
        mock_logs = [
            AuditLog(
                id=1,
                event_type="target_create",
                action="Create",
                user_id=12345,
                resource_id="target_123",
            ),
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_logs
        mock_session.execute.return_value = mock_result

        results = await audit_logger.search_logs(
            user_id=12345,
            event_type=AuditEventType.TARGET_CREATE,
            resource_id="target_123",
        )

        assert len(results) == 1
        assert results[0].resource_id == "target_123"

    def test_audit_log_repr(self):
        """Тест __repr__ метода."""
        log = AuditLog(
            id=1,
            event_type="user_login",
            action="Login",
            user_id=12345,
        )

        repr_str = repr(log)
        assert "AuditLog" in repr_str
        assert "user_login" in repr_str
        assert "12345" in repr_str

    def test_audit_event_type_enum(self):
        """Тест AuditEventType enum."""
        assert AuditEventType.USER_LOGIN.value == "user_login"
        assert AuditEventType.TARGET_CREATE.value == "target_create"
        assert AuditEventType.SYSTEM_ERROR.value == "system_error"

    def test_audit_severity_enum(self):
        """Тест AuditSeverity enum."""
        assert AuditSeverity.DEBUG.value == "debug"
        assert AuditSeverity.INFO.value == "info"
        assert AuditSeverity.WARNING.value == "warning"
        assert AuditSeverity.ERROR.value == "error"
        assert AuditSeverity.CRITICAL.value == "critical"
