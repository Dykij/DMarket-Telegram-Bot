import asyncio
import os
import sys
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(os.getcwd())


async def test_refactor():
    print("Verifying refactor...")

    # Mock dependencies to avoid import errors
    sys.modules["src.telegram_bot.utils.analytics"] = MagicMock()
    sys.modules["src.telegram_bot.utils.keyboards"] = MagicMock()
    sys.modules["src.telegram_bot.utils.formatters"] = MagicMock()
    sys.modules["src.dmarket.arbitrage"] = MagicMock()

    # Mock the scanner module
    mock_scanner_module = MagicMock()
    sys.modules["src.dmarket.arbitrage_scanner"] = mock_scanner_module

    # Import the handler
    try:
        from src.telegram_bot.handlers.arbitrage_callback_impl import handle_best_opportunities_impl

        print("Successfully imported handle_best_opportunities_impl")
    except ImportError as e:
        print(f"Failed to import handler: {e}")
        return

    # Mock the update and context
    update = MagicMock()
    query = MagicMock()
    update.callback_query = query
    context = MagicMock()
    context.user_data = {}

    # Make send_action awaitable
    async def async_send_action(*args, **kwargs):
        return None

    query.message.chat.send_action.side_effect = async_send_action
    query.edit_message_text.side_effect = async_send_action

    # Mock find_arbitrage_opportunities_async on the mocked module
    mock_scanner_module.find_arbitrage_opportunities_async = MagicMock()

    # We need to make sure the function is async
    async def async_return(*args, **kwargs):
        return []

    mock_scanner_module.find_arbitrage_opportunities_async.side_effect = async_return

    # Call the function
    try:
        # The handler expects query, context
        await handle_best_opportunities_impl(query, context)
        print("Successfully called handle_best_opportunities_impl")
    except Exception as e:
        print(f"Error calling handler: {e}")
        import traceback

        traceback.print_exc()

    # Verify the scanner was called
    if mock_scanner_module.find_arbitrage_opportunities_async.called:
        print("SUCCESS: find_arbitrage_opportunities_async was called!")
    else:
        print("FAILURE: find_arbitrage_opportunities_async was NOT called!")


if __name__ == "__main__":
    asyncio.run(test_refactor())
