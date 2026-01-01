"""Автоматическая очистка обновлений и перезапуск бота.

Используйте этот скрипт если бот перестал отвечать после очистки чата в Telegram.
"""

import asyncio
import os
import subprocess
import sys

from dotenv import load_dotenv
from telegram import Bot

load_dotenv()


async def clear_and_restart():
    """Очистить pending updates и перезапустить бота."""
    token = os.getenv("TELEGRAM_BOT_TOKEN")

    if not token:
        print("❌ TELEGRAM_BOT_TOKEN not found!")
        return False

    try:
        print("🔍 Checking for pending updates...")
        bot = Bot(token=token)
        updates = await bot.get_updates(timeout=5)

        if updates:
            last_update_id = updates[-1].update_id
            print(f"📬 Found {len(updates)} pending updates")
            print(f"🧹 Clearing updates up to ID: {last_update_id}...")
            await bot.get_updates(offset=last_update_id + 1, timeout=1)
            print("✅ All old updates cleared!")
        else:
            print("✅ No pending updates. Queue is clean!")

        print("\n🚀 Starting bot...")
        print("=" * 50)

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """Main function."""
    success = await clear_and_restart()

    if success:
        # Start bot in the same process
        print("\n🤖 Bot is starting...")
        print("📌 Use Ctrl+C to stop the bot\n")

        # Import and run main bot
        try:
            # Run the bot
            subprocess.run([sys.executable, "-m", "src.main"], check=True)
        except KeyboardInterrupt:
            print("\n\n👋 Bot stopped by user")
        except Exception as e:
            print(f"\n❌ Bot error: {e}")
    else:
        print("\n❌ Failed to prepare bot. Please check the error above.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
