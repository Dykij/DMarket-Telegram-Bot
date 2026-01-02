"""Тестовый скрипт для запуска реального сканера арбитража.

Демонстрирует работу ArbitrageScanner с реальными данными DMarket API.
Использует DRY_RUN режим для безопасности.
"""

import asyncio
import logging
import os

from dotenv import load_dotenv

from src.dmarket.arbitrage_scanner import ArbitrageScanner
from src.dmarket.dmarket_api import DMarketAPI

# Настройка логирования
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_arbitrage_scanner():
    """Тестовый запуск сканера арбитража."""
    # Загрузить переменные окружения
    load_dotenv()

    public_key = os.getenv("DMARKET_PUBLIC_KEY")
    secret_key = os.getenv("DMARKET_SECRET_KEY")

    if not public_key or not secret_key:
        logger.error("❌ Не найдены DMARKET_PUBLIC_KEY или DMARKET_SECRET_KEY в .env файле")
        logger.info("Пример .env файла:")
        logger.info("DMARKET_PUBLIC_KEY=your_public_key")
        logger.info("DMARKET_SECRET_KEY=your_secret_key")
        return

    logger.info("🚀 Запуск мультиигрового сканера арбитража")
    logger.info("=" * 60)

    # Создать API клиент
    api_client = DMarketAPI(public_key=public_key, secret_key=secret_key)

    # Создать сканер
    scanner = ArbitrageScanner(
        api_client=api_client,
        enable_liquidity_filter=True,
        enable_competition_filter=True,
        max_competition=3,
    )

    logger.info("✅ ArbitrageScanner инициализирован")

    # Конфигурация для мультиигрового сканирования
    scan_configs = [
        {"game": "csgo", "level": "boost", "limit": 5, "name": "CS:GO Разгон"},
        {"game": "csgo", "level": "standard", "limit": 10, "name": "CS:GO Стандарт"},
        {"game": "dota2", "level": "boost", "limit": 5, "name": "Dota 2 Разгон"},
        {"game": "dota2", "level": "standard", "limit": 10, "name": "Dota 2 Стандарт"},
        {"game": "rust", "level": "boost", "limit": 5, "name": "Rust Разгон"},
        {"game": "tf2", "level": "boost", "limit": 5, "name": "TF2 Разгон"},
    ]

    all_opportunities = []
    successful_scans = 0
    failed_scans = 0

    logger.info("\n" + "=" * 60)
    logger.info("🌍 МУЛЬТИИГРОВОЕ СКАНИРОВАНИЕ")
    logger.info("=" * 60)

    for config in scan_configs:
        game = config["game"]
        level = config["level"]
        limit = config["limit"]
        name = config["name"]

        logger.info(f"\n🎮 Сканирование: {name}")
        logger.info(f"   Параметры: {game} | {level} | лимит {limit}")

        try:
            # Запустить сканирование для игры
            opportunities = await scanner.scan_game(game=game, mode=level, max_items=limit)

            if opportunities:
                logger.info(f"   ✅ Найдено: {len(opportunities)} возможностей")
                # Добавить информацию об игре к каждой возможности
                for opp in opportunities:
                    opp["game"] = game
                    opp["game_name"] = name
                all_opportunities.extend(opportunities)
                successful_scans += 1
            else:
                logger.info("   ⚠️ Возможности не найдены")
                successful_scans += 1

        except Exception as e:
            logger.error(f"   ❌ Ошибка: {str(e)[:100]}")
            failed_scans += 1

    # Итоговая статистика
    logger.info("\n" + "=" * 60)
    logger.info("📊 ИТОГОВАЯ СТАТИСТИКА")
    logger.info("=" * 60)
    logger.info(f"Успешных сканирований: {successful_scans}/{len(scan_configs)}")
    logger.info(f"Неудачных сканирований: {failed_scans}/{len(scan_configs)}")
    logger.info(f"Всего найдено возможностей: {len(all_opportunities)}")

    if all_opportunities:
        # Сортировать по марже прибыли
        sorted_opps = sorted(
            all_opportunities, key=lambda x: x.get("profit_margin", 0), reverse=True
        )

        logger.info("\n🏆 ТОП-10 ЛУЧШИХ ВОЗМОЖНОСТЕЙ (все игры):\n")

        for idx, opp in enumerate(sorted_opps[:10], 1):
            title = opp.get("title", "Unknown Item")[:60]
            
            # Безопасное извлечение цен (могут быть dict или int)
            price_raw = opp.get("price", 0)
            suggested_raw = opp.get("suggested_price", 0)
            profit_raw = opp.get("profit", 0)
            
            # Обработка разных форматов
            if isinstance(price_raw, dict):
                price = price_raw.get("amount", 0) / 100
            else:
                price = price_raw / 100 if price_raw else 0
            
            if isinstance(suggested_raw, dict):
                suggested = suggested_raw.get("amount", 0) / 100
            else:
                suggested = suggested_raw / 100 if suggested_raw else 0
            
            if isinstance(profit_raw, dict):
                profit = profit_raw.get("amount", 0) / 100
            else:
                profit = profit_raw / 100 if profit_raw else 0
            
            margin = opp.get("profit_margin", 0)
            game_name = opp.get("game_name", "Unknown Game")

            logger.info(f"{idx}. [{game_name}] {title}")
            logger.info(f"   💰 Купить: ${price:.2f} | Продать: ${suggested:.2f}")
            logger.info(f"   📊 Маржа: {margin:.2f}% | Прибыль: ${profit:.2f}\n")

        # Статистика по играм
        logger.info("\n📈 Распределение по играм:")
        game_stats = {}
        for opp in all_opportunities:
            game_name = opp.get("game_name", "Unknown")
            game_stats[game_name] = game_stats.get(game_name, 0) + 1

        for game_name, count in sorted(
            game_stats.items(), key=lambda x: x[1], reverse=True
        ):
            logger.info(f"   {game_name}: {count} возможностей")
    else:
        logger.warning("\n⚠️ Арбитражные возможности не найдены ни в одной игре")
        logger.info("\n💡 Возможные причины:")
        logger.info("  • Рынок сейчас неактивен (время суток)")
        logger.info("  • Все хорошие предложения уже разобрали")
        logger.info("  • Высокая конкуренция на рынке")
        logger.info("  • Попробуйте позже или измените параметры")

    logger.info("\n✅ Мультиигровое сканирование завершено")


async def test_balance_check():
    """Проверка баланса для демонстрации работы API."""
    load_dotenv()

    public_key = os.getenv("DMARKET_PUBLIC_KEY")
    secret_key = os.getenv("DMARKET_SECRET_KEY")

    if not public_key or not secret_key:
        return

    logger.info("\n💰 Проверка баланса DMarket...")

    api_client = DMarketAPI(public_key=public_key, secret_key=secret_key)

    try:
        balance = await api_client.get_balance()
        if isinstance(balance, dict) and "error" not in balance:
            logger.info("✅ Баланс получен:")
            usd_balance = balance.get("usd", 0)
            dmc_balance = balance.get("dmc", 0)

            # Handle if balance is already in dollars or cents
            if isinstance(usd_balance, (int, float)):
                usd_display = usd_balance / 100 if usd_balance > 100 else usd_balance
                dmc_display = dmc_balance / 100 if dmc_balance > 100 else dmc_balance
            else:
                usd_display = 0.0
                dmc_display = 0.0

            logger.info(f"   USD: ${usd_display:.2f}")
            logger.info(f"   DMC: {dmc_display:.2f}")
        else:
            logger.warning(f"⚠️ Ошибка получения баланса: {balance}")
    except Exception as e:
        logger.error(f"❌ Ошибка получения баланса: {e}")


async def main():
    """Главная функция."""
    logger.info("🤖 DMarket Arbitrage Scanner - Тестовый запуск")
    logger.info("=" * 60)
    logger.info("⚠️ DRY_RUN режим: сделки не выполняются")
    logger.info("=" * 60)

    # Проверить баланс
    await test_balance_check()

    # Запустить сканер
    await test_arbitrage_scanner()

    logger.info("\n🎉 Тестирование завершено!")


if __name__ == "__main__":
    asyncio.run(main())
