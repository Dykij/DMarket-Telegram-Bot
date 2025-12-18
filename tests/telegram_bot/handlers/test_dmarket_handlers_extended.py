"""Extended tests for dmarket_handlers module."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.telegram_bot.handlers.dmarket_handlers import (
    DMarketHandler,
    register_dmarket_handlers,
)


class TestDMarketHandler:
    """Tests for DMarketHandler class."""

    def test_handler_initialization_with_keys(self):
        """Test handler initialization with API keys."""
        handler = DMarketHandler(
            public_key="test_public",
            secret_key="test_secret",
            api_url="https://api.dmarket.com"
        )
        
        assert handler.public_key == "test_public"
        assert handler.secret_key == "test_secret"
        assert handler.api_url == "https://api.dmarket.com"

    def test_handler_initialization_without_keys(self):
        """Test handler initialization without API keys."""
        handler = DMarketHandler(
            public_key="",
            secret_key="",
            api_url="https://api.dmarket.com"
        )
        
        assert handler.api is None

    def test_initialize_api_success(self):
        """Test successful API initialization."""
        with patch("src.telegram_bot.handlers.dmarket_handlers.DMarketAPI"):
            handler = DMarketHandler(
                public_key="test_public",
                secret_key="test_secret",
                api_url="https://api.dmarket.com"
            )
            
            assert handler.api is not None

    @pytest.mark.asyncio
    async def test_status_command_with_keys(self):
        """Test status command when keys are configured."""
        handler = DMarketHandler(
            public_key="test_public",
            secret_key="test_secret",
            api_url="https://api.dmarket.com"
        )
        
        update = MagicMock()
        update.effective_user = MagicMock()
        update.effective_user.id = 12345
        update.message = AsyncMock()
        update.message.reply_text = AsyncMock()
        
        context = MagicMock()
        
        await handler.status_command(update, context)
        
        update.message.reply_text.assert_called_once()
        call_text = update.message.reply_text.call_args[0][0]
        assert "API ключи DMarket настроены" in call_text

    @pytest.mark.asyncio
    async def test_status_command_without_keys(self):
        """Test status command when keys are not configured."""
        handler = DMarketHandler(
            public_key="",
            secret_key="",
            api_url="https://api.dmarket.com"
        )
        
        update = MagicMock()
        update.effective_user = MagicMock()
        update.effective_user.id = 12345
        update.message = AsyncMock()
        update.message.reply_text = AsyncMock()
        
        context = MagicMock()
        
        await handler.status_command(update, context)
        
        update.message.reply_text.assert_called_once()
        call_text = update.message.reply_text.call_args[0][0]
        assert "не настроены" in call_text

    @pytest.mark.asyncio
    async def test_status_command_no_user(self):
        """Test status command with no effective user."""
        handler = DMarketHandler(
            public_key="test_public",
            secret_key="test_secret",
            api_url="https://api.dmarket.com"
        )
        
        update = MagicMock()
        update.effective_user = None
        
        context = MagicMock()
        
        # Should return early without error
        await handler.status_command(update, context)

    @pytest.mark.asyncio
    async def test_balance_command_no_api(self):
        """Test balance command when API is not initialized."""
        handler = DMarketHandler(
            public_key="",
            secret_key="",
            api_url="https://api.dmarket.com"
        )
        
        update = MagicMock()
        update.effective_user = MagicMock()
        update.effective_user.id = 12345
        update.message = AsyncMock()
        update.message.reply_text = AsyncMock()
        
        context = MagicMock()
        
        await handler.balance_command(update, context)
        
        update.message.reply_text.assert_called_once()
        call_text = update.message.reply_text.call_args[0][0]
        assert "не инициализирован" in call_text

    @pytest.mark.asyncio
    async def test_balance_command_success(self):
        """Test balance command with successful API response."""
        handler = DMarketHandler(
            public_key="test_public",
            secret_key="test_secret",
            api_url="https://api.dmarket.com"
        )
        
        # Mock the API
        handler.api = AsyncMock()
        handler.api.get_balance = AsyncMock(return_value={
            "usd": 10000,  # $100 in cents
            "usdAvailableToWithdraw": 8000  # $80 available
        })
        
        update = MagicMock()
        update.effective_user = MagicMock()
        update.effective_user.id = 12345
        update.message = AsyncMock()
        update.message.reply_text = AsyncMock()
        
        context = MagicMock()
        
        await handler.balance_command(update, context)
        
        update.message.reply_text.assert_called_once()
        call_text = update.message.reply_text.call_args[0][0]
        assert "Баланс на DMarket" in call_text
        assert "$100.00" in call_text

    @pytest.mark.asyncio
    async def test_balance_command_no_data(self):
        """Test balance command with no balance data returned."""
        handler = DMarketHandler(
            public_key="test_public",
            secret_key="test_secret",
            api_url="https://api.dmarket.com"
        )
        
        handler.api = AsyncMock()
        handler.api.get_balance = AsyncMock(return_value=None)
        
        update = MagicMock()
        update.effective_user = MagicMock()
        update.effective_user.id = 12345
        update.message = AsyncMock()
        update.message.reply_text = AsyncMock()
        
        context = MagicMock()
        
        await handler.balance_command(update, context)
        
        update.message.reply_text.assert_called_once()
        call_text = update.message.reply_text.call_args[0][0]
        assert "Не удалось получить информацию" in call_text

    @pytest.mark.asyncio
    async def test_balance_command_api_error(self):
        """Test balance command with API error."""
        handler = DMarketHandler(
            public_key="test_public",
            secret_key="test_secret",
            api_url="https://api.dmarket.com"
        )
        
        handler.api = AsyncMock()
        handler.api.get_balance = AsyncMock(return_value={
            "error": True,
            "error_message": "Authentication failed"
        })
        
        update = MagicMock()
        update.effective_user = MagicMock()
        update.effective_user.id = 12345
        update.message = AsyncMock()
        update.message.reply_text = AsyncMock()
        
        context = MagicMock()
        
        await handler.balance_command(update, context)
        
        update.message.reply_text.assert_called_once()
        call_text = update.message.reply_text.call_args[0][0]
        assert "Ошибка при получении баланса" in call_text

    @pytest.mark.asyncio
    async def test_balance_command_no_user(self):
        """Test balance command with no effective user."""
        handler = DMarketHandler(
            public_key="test_public",
            secret_key="test_secret",
            api_url="https://api.dmarket.com"
        )
        
        update = MagicMock()
        update.effective_user = None
        
        context = MagicMock()
        
        # Should return early without error
        await handler.balance_command(update, context)


class TestRegisterDMarketHandlers:
    """Tests for register_dmarket_handlers function."""

    def test_register_handlers(self):
        """Test registering handlers on application."""
        mock_app = MagicMock()
        mock_app.add_handler = MagicMock()
        
        register_dmarket_handlers(
            app=mock_app,
            public_key="test_public",
            secret_key="test_secret",
            api_url="https://api.dmarket.com"
        )
        
        # Should register 2 handlers (dmarket and balance commands)
        assert mock_app.add_handler.call_count == 2

    def test_register_handlers_without_keys(self):
        """Test registering handlers without API keys."""
        mock_app = MagicMock()
        mock_app.add_handler = MagicMock()
        
        register_dmarket_handlers(
            app=mock_app,
            public_key="",
            secret_key="",
            api_url="https://api.dmarket.com"
        )
        
        # Handlers should still be registered
        assert mock_app.add_handler.call_count == 2
