"""Проверка подключения к Telegram Bot API."""

import asyncio
import os

from dotenv import load_dotenv
from telegram import Bot

load_dotenv()


async def test_bot_connection():
    """Test bot connection and get bot info."""
    token = os.getenv("TELEGRAM_BOT_TOKEN")

    if not token:
        print("❌ TELEGRAM_BOT_TOKEN not found in environment!")
        return

    try:
        bot = Bot(token=token)
        me = await bot.get_me()

        print("✅ Bot connection successful!")
        print(f"📱 Bot username: @{me.username}")
        print(f"👤 Bot name: {me.first_name}")
        print(f"🆔 Bot ID: {me.id}")
        print(f"📨 Can read all group messages: {me.can_read_all_group_messages}")

        # Try to get updates
        print("\n🔍 Checking for pending updates...")
        updates = await bot.get_updates(limit=5)
        print(f"📬 Pending updates: {len(updates)}")

        if updates:
            print("\n📋 Last updates:")
            for update in updates[-3:]:
                print(f"  - Update ID: {update.update_id}")
                if update.message:
                    print(f"    From: {update.message.from_user.username}")
                    print(f"    Text: {update.message.text}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_bot_connection())
