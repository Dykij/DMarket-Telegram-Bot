---
description: 'Telegram bot handler conventions'
applyTo: 'src/telegram_bot/**/*.py'
---

# Telegram Bot Instructions

Apply these conventions to all Telegram bot files:

## Handler Pattern

```python
async def command_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle /command - brief description."""
    if not update.message:
        return
        
    user_id = update.effective_user.id
    logger.info("command_received", user_id=user_id, command="command")
    
    try:
        result = await business_logic()
        await update.message.reply_text(f"✅ {result}")
    except Exception as e:
        logger.error("command_failed", user_id=user_id, error=str(e))
        await update.message.reply_text("❌ Error occurred")
```

## Requirements
- Use python-telegram-bot 22.0+ async API
- Type parameters with `Update` and `ContextTypes.DEFAULT_TYPE`
- Always check `if not update.message: return`
- Log all commands with user_id
- Handle all exceptions with user-friendly messages

## Callback Handlers
- Always call `await query.answer()` first
- Use `match/case` for routing by callback_data
- Log unknown callbacks as warnings

## Inline Keyboards

```python
keyboard = [
    [InlineKeyboardButton("Option", callback_data="opt_1")],
]
reply_markup = InlineKeyboardMarkup(keyboard)
await update.message.reply_text("Choose:", reply_markup=reply_markup)
```

## Localization
- Use `get_text(key, lang)` for user-facing text
- Support RU, EN languages at minimum
- Never hardcode user-visible strings
