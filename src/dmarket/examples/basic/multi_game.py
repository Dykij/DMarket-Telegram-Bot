#!/usr/bin/env python3
"""
Базовый пример: Мультиигровой анализ.

Сканирует все 4 поддерживаемые игры (CS:GO, Dota 2, TF2, Rust) и находит
лучшую арбитражную возможность независимо от игры.
"""

import asyncio
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.dmarket.dmarket_api import DMarketAPI
from src.dmarket.ai_arbitrage_predictor import AIArbitragePredictor
from src.ml.enhanced_predictor import EnhancedPricePredictor


async def scan_game(api: DMarketAPI, ai_arbitrage: AIArbitragePredictor, 
                    game: str, balance: float) -> list[dict]:
    """Сканирование одной игры."""
    print(f"  🎮 Сканирование {game.upper()}...")
    
    items = await api.get_market_items(game=game, limit=50)
    opportunities = await ai_arbitrage.predict_best_opportunities(
        items=items,
        current_balance=balance,
        risk_level="medium"
    )
    
    print(f"     ✓ Найдено {len(opportunities)} возможностей")
    return opportunities


async def main():
    """Мультиигровой анализ."""
    
    # Инициализация
    api = DMarketAPI(
        public_key=os.getenv("DMARKET_PUBLIC_KEY"),
        secret_key=os.getenv("DMARKET_SECRET_KEY")
    )
    
    ml_predictor = EnhancedPricePredictor()
    ai_arbitrage = AIArbitragePredictor(ml_predictor)
    
    # Список игр для сканирования
    games = ["csgo", "dota2", "tf2", "rust"]
    balance_per_game = 100.0  # $100 на каждую игру
    
    print("🔍 Мультиигровой анализ арбитража")
    print(f"💰 Баланс на игру: ${balance_per_game:.2f}\n")
    
    # Параллельное сканирование всех игр
    all_opportunities = []
    
    for game in games:
        try:
            opps = await scan_game(api, ai_arbitrage, game, balance_per_game)
            # Добавляем game_id для каждой возможности
            for opp in opps:
                opp["scanned_game"] = game
            all_opportunities.extend(opps)
        except Exception as e:
            print(f"     ❌ Ошибка в {game}: {e}")
    
    # Сортировка по комбинированному score (confidence * profit)
    all_opportunities.sort(
        key=lambda x: x["confidence"] * x["predicted_profit"],
        reverse=True
    )
    
    # Результаты
    print("\n" + "=" * 80)
    print("🏆 ЛУЧШАЯ ВОЗМОЖНОСТЬ ACROSS ALL GAMES:")
    print("=" * 80)
    
    if all_opportunities:
        best = all_opportunities[0]
        print(f"\n🎮 Игра: {best['scanned_game'].upper()}")
        print(f"📦 Предмет: {best['title']}")
        print(f"💵 Цена: ${best['price']['USD'] / 100:.2f}")
        print(f"💰 Прогноз прибыли: ${best['predicted_profit']:.2f}")
        print(f"✨ Уверенность: {best['confidence']:.1%}")
        print(f"⚠️ Risk Score: {best['risk_score']:.1f}/100")
        print(f"📈 ROI: {best['roi_percent']:.1f}%")
        print(f"🎯 Combined Score: {best['confidence'] * best['predicted_profit']:.2f}")
    
    # Топ-5 по играм
    print("\n" + "-" * 80)
    print("📊 Топ-5 возможностей:")
    print("-" * 80)
    
    for i, opp in enumerate(all_opportunities[:5], 1):
        print(f"\n{i}. [{opp['scanned_game'].upper()}] {opp['title']}")
        print(f"   Profit: ${opp['predicted_profit']:.2f} | "
              f"Confidence: {opp['confidence']:.1%} | "
              f"ROI: {opp['roi_percent']:.1f}%")
    
    # Статистика по играм
    print("\n" + "-" * 80)
    print("📈 Статистика по играм:")
    print("-" * 80)
    
    for game in games:
        game_opps = [o for o in all_opportunities if o.get("scanned_game") == game]
        if game_opps:
            avg_profit = sum(o["predicted_profit"] for o in game_opps) / len(game_opps)
            avg_confidence = sum(o["confidence"] for o in game_opps) / len(game_opps)
            print(f"  {game.upper()}: {len(game_opps)} opportunities | "
                  f"Avg profit: ${avg_profit:.2f} | "
                  f"Avg confidence: {avg_confidence:.1%}")
    
    print("\n" + "=" * 80)
    print(f"✅ Всего найдено {len(all_opportunities)} возможностей в {len(games)} играх")
    
    await api.close()


if __name__ == "__main__":
    if not os.getenv("DMARKET_PUBLIC_KEY"):
        print("❌ Ошибка: DMARKET_PUBLIC_KEY не найден")
        sys.exit(1)
    
    asyncio.run(main())
