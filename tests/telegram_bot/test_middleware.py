"""Tests for middleware module.

This module tests the Telegram bot middleware components.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from telegram import Update, User

from src.telegram_bot.middleware import (
    UserAuthMiddleware,
    RateLimitMiddleware,
    LoggingMiddleware,
)


class TestUserAuthMiddleware:
    """Tests for UserAuthMiddleware."""

    @pytest.fixture
    def middleware(self):
        """Create UserAuthMiddleware instance."""
        return UserAuthMiddleware()

    @pytest.fixture
    def mock_update(self):
        """Create mock Update."""
        update = MagicMock(spec=Update)
        update.effective_user = MagicMock(spec=User)
        update.effective_user.id = 123456
        update.effective_user.username = "testuser"
        return update

    @pytest.fixture
    def mock_context(self):
        """Create mock Context."""
        context = MagicMock()
        context.user_data = {}
        return context

    @pytest.mark.asyncio
    async def test_init(self, middleware):
        """Test middleware initialization."""
        assert middleware is not None

    @pytest.mark.asyncio
    async def test_process_update(self, middleware, mock_update, mock_context):
        """Test processing update."""
        next_handler = AsyncMock()

        await middleware.process_update(mock_update, mock_context, next_handler)

        # Next handler should be called
        next_handler.assert_called_once()

    @pytest.mark.asyncio
    async def test_authorize_user(self, middleware, mock_update):
        """Test user authorization."""
        is_authorized = await middleware.authorize_user(mock_update)
        assert isinstance(is_authorized, bool)

    @pytest.mark.asyncio
    async def test_get_user_permissions(self, middleware, mock_update):
        """Test getting user permissions."""
        permissions = await middleware.get_user_permissions(mock_update.effective_user.id)
        assert isinstance(permissions, (dict, list, set))


class TestRateLimitMiddleware:
    """Tests for RateLimitMiddleware."""

    @pytest.fixture
    def middleware(self):
        """Create RateLimitMiddleware instance."""
        return RateLimitMiddleware(max_requests=10, time_window=60)

    @pytest.fixture
    def mock_update(self):
        """Create mock Update."""
        update = MagicMock(spec=Update)
        update.effective_user = MagicMock(spec=User)
        update.effective_user.id = 123456
        return update

    @pytest.fixture
    def mock_context(self):
        """Create mock Context."""
        return MagicMock()

    @pytest.mark.asyncio
    async def test_init(self, middleware):
        """Test middleware initialization."""
        assert middleware.max_requests == 10
        assert middleware.time_window == 60

    @pytest.mark.asyncio
    async def test_check_rate_limit(self, middleware, mock_update):
        """Test rate limit checking."""
        is_allowed = await middleware.check_rate_limit(mock_update.effective_user.id)
        assert is_allowed is True  # First request should be allowed

    @pytest.mark.asyncio
    async def test_rate_limit_exceeded(self, middleware, mock_update):
        """Test rate limit exceeded."""
        user_id = mock_update.effective_user.id

        # Make many requests
        for _ in range(15):
            await middleware.check_rate_limit(user_id)

        # After exceeding limit, should be blocked
        is_allowed = await middleware.check_rate_limit(user_id)
        assert is_allowed is False

    @pytest.mark.asyncio
    async def test_process_update_allowed(self, middleware, mock_update, mock_context):
        """Test processing allowed update."""
        next_handler = AsyncMock()

        await middleware.process_update(mock_update, mock_context, next_handler)

        next_handler.assert_called_once()

    @pytest.mark.asyncio
    async def test_reset_rate_limit(self, middleware, mock_update):
        """Test resetting rate limit."""
        user_id = mock_update.effective_user.id

        await middleware.reset_rate_limit(user_id)

        # Should be allowed after reset
        is_allowed = await middleware.check_rate_limit(user_id)
        assert is_allowed is True


class TestLoggingMiddleware:
    """Tests for LoggingMiddleware."""

    @pytest.fixture
    def middleware(self):
        """Create LoggingMiddleware instance."""
        return LoggingMiddleware()

    @pytest.fixture
    def mock_update(self):
        """Create mock Update."""
        update = MagicMock(spec=Update)
        update.effective_user = MagicMock(spec=User)
        update.effective_user.id = 123456
        update.effective_user.username = "testuser"
        update.update_id = 12345
        return update

    @pytest.fixture
    def mock_context(self):
        """Create mock Context."""
        return MagicMock()

    @pytest.mark.asyncio
    async def test_init(self, middleware):
        """Test middleware initialization."""
        assert middleware is not None

    @pytest.mark.asyncio
    async def test_log_request(self, middleware, mock_update):
        """Test logging request."""
        with patch("src.telegram_bot.middleware.logger") as mock_logger:
            await middleware.log_request(mock_update)
            # Logger should be called
            assert mock_logger.info.called or mock_logger.debug.called

    @pytest.mark.asyncio
    async def test_process_update(self, middleware, mock_update, mock_context):
        """Test processing update with logging."""
        next_handler = AsyncMock()

        with patch("src.telegram_bot.middleware.logger"):
            await middleware.process_update(mock_update, mock_context, next_handler)

        next_handler.assert_called_once()

    @pytest.mark.asyncio
    async def test_log_error(self, middleware):
        """Test logging errors."""
        error = Exception("Test error")

        with patch("src.telegram_bot.middleware.logger") as mock_logger:
            await middleware.log_error(error)
            mock_logger.error.assert_called()
