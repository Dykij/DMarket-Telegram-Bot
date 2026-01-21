---
description: 'Generate Telegram bot handlers for DMarket Telegram Bot'
mode: 'agent'
---

# Telegram Handler Generator

Generate Telegram bot handlers following project conventions:

## Requirements

1. **Use `python-telegram-bot` 22.0+** async API
2. **Type all parameters** with `Update` and `ContextTypes`
3. **Add error handling** with user-friendly messages
4. **Log all actions** with structlog
5. **Use inline keyboards** for navigation

## Handler Template

```python
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

import structlog

logger = structlog.get_logger(__name__)

async def command_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle /command - brief description.
    
    Args:
        update: Telegram update object
        context: Bot context with user data
    """
    if not update.message:
        return
        
    user_id = update.effective_user.id
    logger.info("command_received", user_id=user_id, command="command")
    
    try:
        # Business logic here
        result = await some_async_operation()
        
        # Create response
        keyboard = [
            [InlineKeyboardButton("Option 1", callback_data="opt_1")],
            [InlineKeyboardButton("Option 2", callback_data="opt_2")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"✅ Result: {result}",
            reply_markup=reply_markup
        )
        
    except Exception as e:
        logger.error("command_failed", user_id=user_id, error=str(e))
        await update.message.reply_text(
            "❌ An error occurred. Please try again later."
        )

async def callback_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle callback query from inline keyboard."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    callback_data = query.data
    
    logger.info("callback_received", user_id=user_id, data=callback_data)
    
    # Handle different callbacks
    match callback_data:
        case "opt_1":
            await query.edit_message_text("You selected Option 1")
        case "opt_2":
            await query.edit_message_text("You selected Option 2")
        case _:
            logger.warning("unknown_callback", data=callback_data)
```

## Apply this prompt when:
- Creating new bot commands
- Adding callback handlers
- Building interactive menus
