"""Очистка всех старых обновлений бота."""

import asyncio
import os

from dotenv import load_dotenv
from telegram import Bot


load_dotenv()


async def clear_all_updates():
    """Clear all pending updates."""
    token = os.getenv("TELEGRAM_BOT_TOKEN")

    if not token:
        print("❌ TELEGRAM_BOT_TOKEN not found!")
        return

    try:
        bot = Bot(token=token)

        print("🔍 Checking for pending updates...")
        updates = await bot.get_updates(timeout=5)

        if not updates:
            print("✅ No pending updates. Queue is clean!")
            return

        print(f"📬 Found {len(updates)} pending updates")
        last_update_id = updates[-1].update_id

        print(f"🧹 Clearing all updates up to ID: {last_update_id}...")

        # Clear by setting offset to last_update_id + 1
        await bot.get_updates(offset=last_update_id + 1, timeout=1)

        print("✅ All old updates cleared!")
        print("🚀 Bot is ready to receive new messages")

        # Verify
        verify = await bot.get_updates(timeout=1)
        if verify:
            print(f"⚠️ Warning: Still {len(verify)} updates remaining")
        else:
            print("✅ Verified: No pending updates")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(clear_all_updates())
