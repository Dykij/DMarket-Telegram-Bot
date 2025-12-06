#!/usr/bin/env python3
"""Примеры использования DMarket API.

Этот скрипт демонстрирует основные возможности работы с DMarket API:
- Получение баланса пользователя
- Получение списка предметов на рынке
"""

import asyncio
import json
import os
import sys
from typing import Any


# Add the src directory to the path
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from dmarket.dmarket_api import DMarketAPI  # noqa: E402


# Load environment variables
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not installed")

# Get API keys from environment variables
PUBLIC_KEY = os.environ.get("DMARKET_PUBLIC_KEY", "")
SECRET_KEY = os.environ.get("DMARKET_SECRET_KEY", "")

if not PUBLIC_KEY or not SECRET_KEY:
    print("Error: DMARKET_PUBLIC_KEY and DMARKET_SECRET_KEY must be set in .env file")
    sys.exit(1)


async def main() -> None:
    """Запускает примеры использования DMarket API.

    Выполняет следующие операции:
    1. Получение баланса пользователя
    2. Получение списка предметов CS:GO на рынке
    """
    # Create API client
    api = DMarketAPI(PUBLIC_KEY, SECRET_KEY)

    try:
        # Get user balance
        print("Getting user balance...")
        balance: dict[str, Any] = await api.get_user_balance()
        print(f"Balance: {json.dumps(balance, indent=2)}")

        # Get market items for CS:GO
        print("\nGetting CS:GO market items...")
        items: dict[str, Any] = await api.get_market_items(game="csgo", limit=5)
        items_list = items.get("objects", [])
        print(f"Found {len(items_list)} items")
        print(f"Items: {json.dumps(items_list[:2], indent=2)}")

    except Exception as e:
        print(f"Error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
