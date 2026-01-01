"""Проверка обработки updates и offset."""

import asyncio
import os

from dotenv import load_dotenv
from telegram import Bot

load_dotenv()


async def test_updates_processing():
    """Test if bot can process updates with correct offset."""
    token = os.getenv("TELEGRAM_BOT_TOKEN")

    if not token:
        print("❌ TELEGRAM_BOT_TOKEN not found!")
        return

    try:
        bot = Bot(token=token)

        # Get current updates
        print("🔍 Getting updates...")
        updates = await bot.get_updates(timeout=10)
        print(f"📬 Total updates: {len(updates)}")

        if updates:
            last_update_id = updates[-1].update_id
            print(f"📊 Last update ID: {last_update_id}")

            # Clear pending updates by acknowledging them
            print(f"\n🧹 Clearing updates (offset={last_update_id + 1})...")
            cleared = await bot.get_updates(offset=last_update_id + 1, timeout=1)
            print(f"✅ Cleared {len(cleared)} updates")

            # Check if there are new updates
            print("\n⏳ Waiting for new updates (10 seconds)...")
            new_updates = await bot.get_updates(timeout=10)
            print(f"📬 New updates: {len(new_updates)}")

            if new_updates:
                print("\n📋 New messages:")
                for update in new_updates:
                    if update.message:
                        print(f"  - From: @{update.message.from_user.username}")
                        print(f"    Text: {update.message.text}")
        else:
            print("📭 No pending updates. Send a message to the bot!")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_updates_processing())
