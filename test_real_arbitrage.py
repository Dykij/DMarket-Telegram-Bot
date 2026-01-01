"""
Тестовый скрипт для реального поиска арбитража на DMarket.
Использует реальные API запросы для демонстрации работы функционала.
"""

import asyncio
import logging
import os
from pathlib import Path
import sys


# Добавляем корневую директорию в PYTHONPATH
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

from src.dmarket.dmarket_api import DMarketAPI


# Настройка логирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


async def test_real_market_data():
    """Тестовая функция для получения реальных данных с рынка."""

    # Загрузка переменных окружения
    try:
        from dotenv import load_dotenv

        load_dotenv(root_dir / ".env")
    except ImportError:
        logger.warning("python-dotenv не установлен")

    # Получение API ключей
    public_key = os.getenv("DMARKET_PUBLIC_KEY", "")
    secret_key = os.getenv("DMARKET_SECRET_KEY", "")

    if not public_key or not secret_key:
        logger.error("❌ API ключи не найдены в .env файле!")
        return

    logger.info("🛡️  DRY_RUN режим - безопасное чтение данных рынка")

    # Инициализация API клиента
    api_client = DMarketAPI(public_key=public_key, secret_key=secret_key)
    logger.info("✅ DMarket API клиент инициализирован\n")

    # Тестовые параметры для CS:GO
    game = "csgo"
    price_from = None  # Без фильтра
    price_to = None  # Без фильтра
    limit = 30

    logger.info("=" * 70)
    logger.info("🔍 ПОИСК ПРЕДМЕТОВ НА DMARKET")
    logger.info("=" * 70)
    logger.info(f"Игра: {game.upper()}")
    logger.info("Диапазон цен: Без ограничений (все предметы)")
    logger.info(f"Максимум результатов: {limit}\n")

    try:
        # Получаем предметы с рынка
        response = await api_client.get_market_items(
            game=game, price_from=price_from, price_to=price_to, limit=limit
        )

        items = response.get("objects", [])

        if not items:
            logger.info("ℹ️  Предметов не найдено в заданном диапазоне\n")
            return

        logger.info(f"✅ Найдено предметов: {len(items)}\n")
        logger.info("-" * 70)

        # Анализ найденных предметов
        arbitrage_opportunities = []

        for i, item in enumerate(items[:10], 1):  # Показываем первые 10
            title = item.get("title", "Unknown")
            price = item.get("price", {}).get("USD", 0)
            suggested_price = item.get("suggestedPrice", {}).get("USD", 0)

            # Простой расчет потенциальной прибыли
            if price and suggested_price and suggested_price > price:
                # Комиссия DMarket 7%
                commission = suggested_price * 0.07
                profit = suggested_price - price - commission
                profit_margin = (profit / price * 100) if price > 0 else 0

                if profit > 0 and profit_margin >= 3:  # Минимум 3% прибыли
                    arbitrage_opportunities.append({
                        "title": title,
                        "buy_price": price,
                        "sell_price": suggested_price,
                        "profit": profit,
                        "profit_margin": profit_margin,
                    })

            # Выводим информацию о предмете
            logger.info(f"#{i}. {title}")
            logger.info(f"   💰 Цена покупки: ${price / 100:.2f}")

            if suggested_price:
                logger.info(f"   📈 Рекомендованная цена: ${suggested_price / 100:.2f}")

                if suggested_price > price:
                    commission = suggested_price * 0.07
                    profit = suggested_price - price - commission
                    profit_margin = (profit / price * 100) if price > 0 else 0

                    if profit > 0:
                        logger.info(
                            f"   💵 Потенциальная прибыль: ${profit / 100:.2f} ({profit_margin:.1f}%)"
                        )
                        if profit_margin >= 3:
                            logger.info("   ⭐ ВОЗМОЖНОСТЬ ДЛЯ АРБИТРАЖА!")

            logger.info("")

        # Итоговая статистика
        logger.info("=" * 70)
        logger.info("📊 ИТОГОВАЯ СТАТИСТИКА")
        logger.info("=" * 70)
        logger.info(f"Всего проверено предметов: {len(items[:10])}")
        logger.info(f"Найдено арбитражных возможностей: {len(arbitrage_opportunities)}")

        if arbitrage_opportunities:
            logger.info("\n🎯 ТОП АРБИТРАЖНЫЕ ВОЗМОЖНОСТИ:")
            logger.info("-" * 70)

            # Сортируем по марже прибыли
            arbitrage_opportunities.sort(key=lambda x: x["profit_margin"], reverse=True)

            for i, opp in enumerate(arbitrage_opportunities[:5], 1):
                logger.info(f"\n#{i}. {opp['title']}")
                logger.info(f"   💰 Покупка: ${opp['buy_price'] / 100:.2f}")
                logger.info(f"   💸 Продажа: ${opp['sell_price'] / 100:.2f}")
                logger.info(f"   💵 Прибыль: ${opp['profit'] / 100:.2f}")
                logger.info(f"   📊 Маржа: {opp['profit_margin']:.1f}%")

            logger.info("\n✅ Система поиска арбитража работает корректно!")
            logger.info("\n💡 Для использования:")
            logger.info("   1. Проверьте ликвидность найденных предметов")
            logger.info("   2. Изучите историю продаж")
            logger.info("   3. Убедитесь в стабильности цен")
            logger.info("   4. Используйте DRY_RUN=true для безопасности")
        else:
            logger.info("\nℹ️  В данный момент прибыльных возможностей не найдено")
            logger.info("   Попробуйте:")
            logger.info("   - Изменить ценовой диапазон")
            logger.info("   - Проверить другие игры (dota2, rust, tf2)")
            logger.info("   - Повторить поиск позже")

    except Exception as e:
        logger.error(f"❌ Ошибка при получении данных: {e}", exc_info=True)

    finally:
        # API клиент автоматически управляет соединениями
        logger.info("\n✅ Тестирование завершено")


if __name__ == "__main__":
    try:
        asyncio.run(test_real_market_data())
    except KeyboardInterrupt:
        logger.info("\n⚠️  Тестирование прервано пользователем")
    except Exception as e:
        logger.error(f"\n❌ Критическая ошибка: {e}", exc_info=True)
