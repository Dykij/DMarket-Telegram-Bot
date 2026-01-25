#!/usr/bin/env python3
"""Скрипт для проверки активных торговых предложений на DMarket.

Помогает узнать, где заблокированы ваши средства.
"""

import asyncio
import logging
import os
import sys

from dotenv import load_dotenv


# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger(__name__)


async def check_offers() -> None:
    """Проверяет активные торговые предложения пользователя."""
    print("\n" + "=" * 70)
    print("🔍 ПРОВЕРКА АКТИВНЫХ ТОРГОВЫХ ПРЕДЛОЖЕНИЙ")
    print("=" * 70 + "\n")

    # Загружаем переменные окружения
    load_dotenv()

    # Получаем API ключи
    public_key = os.getenv("DMARKET_PUBLIC_KEY", "")
    secret_key = os.getenv("DMARKET_SECRET_KEY", "")

    if not public_key or not secret_key:
        print("❌ ОШИБКА: API ключи не настроены!")
        return

    # Импортируем DMarket API
    try:
        from src.dmarket.dmarket_api import DMarketAPI
    except ImportError as e:
        print(f"❌ ОШИБКА ИМПОРТА: {e}")
        return

    # Создаём экземпляр API
    print("🔌 Подключение к DMarket API...")
    api_client = DMarketAPI(
        public_key=public_key,
        secret_key=secret_key,
        enable_cache=False,
    )

    try:
        # Получаем баланс для справки
        print("\n" + "─" * 70)
        print("💰 Текущий баланс")
        print("─" * 70)

        balance = await api_client.get_balance()

        if not balance.get("error"):
            total = balance.get("total_balance", 0.0)
            available = balance.get("available_balance", 0.0)
            locked = balance.get("locked_balance", 0.0)

            print(f"💰 Всего: ${total:.2f} USD")
            print(f"✅ Доступно: ${available:.2f} USD")
            print(f"🔒 Заблокировано: ${locked:.2f} USD")
        else:
            print("❌ Ошибка при получении баланса")

        # Получаем список активных предложений
        print("\n" + "─" * 70)
        print("📋 Активные торговые предложения (CS:GO)")
        print("─" * 70 + "\n")

        # CS:GO game ID
        game_id = "a8db"

        try:
            offers_response = await api_client.list_user_offers(
                game_id=game_id,
                status="OfferStatusActive",
                limit=100,
            )

            if "error" in offers_response or "code" in offers_response:
                print(
                    f"⚠️  Ошибка при получении предложений: {offers_response.get('message', 'Unknown error')}"
                )
                print("\n💡 Попробуем альтернативный метод...")

                # Пробуем альтернативный эндпоинт
                offers_response = await api_client.get_active_offers(
                    game="a8db",
                    status="active",
                    limit=100,
                )

            if "Items" in offers_response:
                items = offers_response.get("Items", [])

                if not items:
                    print("✅ У вас нет активных предложений на продажу")
                    print("💡 Возможно, средства заблокированы по другим причинам:")
                    print("   • Pending транзакции")
                    print("   • Withdrawal в процессе")
                    print("   • Trade holds после покупки")
                else:
                    print(f"📦 Найдено активных предложений: {len(items)}\n")

                    total_locked = 0.0

                    for i, item in enumerate(items, 1):
                        title = item.get("Title", "Unknown")
                        price_data = item.get("Price", {})

                        # Цена может быть в разных форматах
                        if isinstance(price_data, dict):
                            price_cents = price_data.get("Amount", 0)
                        else:
                            price_cents = 0

                        price_usd = price_cents / 100
                        total_locked += price_usd

                        offer_id = item.get("OfferID", "N/A")
                        created = item.get("CreatedAt", "N/A")

                        print(f"  {i}. {title}")
                        print(f"     💵 Цена: ${price_usd:.2f} USD")
                        print(f"     🆔 ID: {offer_id}")
                        print(f"     📅 Создано: {created}")
                        print()

                    print("─" * 70)
                    print(f"💰 Всего заблокировано в офферах: ${total_locked:.2f} USD")
                    print("─" * 70)

                    # Даём рекомендации
                    print("\n💡 Что делать:")
                    print("   1. Зайдите на dmarket.com → My Items → Active Offers")
                    print("   2. Проверьте, актуальны ли цены на ваши предметы")
                    print("   3. Отмените неактуальные предложения, чтобы освободить средства")
                    print("   4. После отмены средства станут доступны на балансе")
            else:
                print("⚠️  Неожиданный формат ответа API")
                print(f"Ответ: {offers_response}")

        except Exception as e:
            logger.exception(f"Ошибка при получении предложений: {e}")
            print(f"❌ Ошибка: {e}")

        # Проверяем другие игры (опционально)
        print("\n" + "─" * 70)
        print("🎮 Другие игры")
        print("─" * 70)
        print("💡 Если у вас есть предложения в других играх:")
        print("   • Dota 2: game_id = '9a92'")
        print("   • TF2: game_id = 'tf2'")
        print("   • Rust: game_id = 'rust'")

    finally:
        # Закрываем клиент
        await api_client._close_client()
        print("\n✅ Соединение закрыто")


if __name__ == "__main__":
    print("\n🔎 DMarket Offers Checker")
    print("Версия: 1.0.0")
    print("Дата: 14.11.2025\n")

    try:
        asyncio.run(check_offers())
    except KeyboardInterrupt:
        print("\n\n⚠️  Прервано пользователем")
    except Exception as e:
        print(f"\n\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        logger.exception("Детали ошибки:")

    print("\n" + "=" * 70)
    print("✅ Проверка завершена")
    print("=" * 70 + "\n")
