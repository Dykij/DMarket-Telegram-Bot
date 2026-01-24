#!/usr/bin/env python3
"""
Продвинутый пример: Управление портфелем.

Диверсифицированный подход к арбитражу с распределением капитала
по разным играм и уровням риска.
"""

import asyncio
import os
from pathlib import Path
import sys
from dataclasses import dataclass
from typing import List

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.dmarket.dmarket_api import DMarketAPI
from src.dmarket.ai_arbitrage_predictor import AIArbitragePredictor
from src.ml.enhanced_predictor import EnhancedPricePredictor


@dataclass
class PortfolioConfig:
    """Конфигурация портфеля."""
    game: str
    balance: float
    risk_level: str
    max_items: int = 5


async def build_portfolio(api: DMarketAPI, ai_arbitrage: AIArbitragePredictor,
                         configs: List[PortfolioConfig]) -> dict:
    """Построение диверсифицированного портфеля."""
    
    portfolio = {
        "positions": [],
        "total_invested": 0.0,
        "expected_profit": 0.0,
        "avg_confidence": 0.0,
        "risk_breakdown": {}
    }
    
    for config in configs:
        print(f"\n📊 Анализ {config.game.upper()} ({config.risk_level} risk)...")
        
        # Получение данных
        items = await api.get_market_items(config.game, limit=100)
        
        # AI-прогнозирование
        opportunities = await ai_arbitrage.predict_best_opportunities(
            items=items,
            current_balance=config.balance,
            risk_level=config.risk_level
        )
        
        # Выбор лучших
        selected = opportunities[:config.max_items]
        
        for opp in selected:
            position = {
                "game": config.game,
                "title": opp["title"],
                "price": opp["price"]["USD"] / 100,
                "predicted_profit": opp["predicted_profit"],
                "confidence": opp["confidence"],
                "risk_score": opp["risk_score"],
                "risk_level": config.risk_level
            }
            portfolio["positions"].append(position)
            portfolio["total_invested"] += position["price"]
            portfolio["expected_profit"] += position["predicted_profit"]
        
        print(f"   ✓ Выбрано {len(selected)} позиций")
    
    # Расчет средних
    if portfolio["positions"]:
        portfolio["avg_confidence"] = sum(
            p["confidence"] for p in portfolio["positions"]
        ) / len(portfolio["positions"])
        
        # Risk breakdown
        for risk in ["low", "medium", "high"]:
            count = sum(1 for p in portfolio["positions"] if p["risk_level"] == risk)
            portfolio["risk_breakdown"][risk] = count
    
    return portfolio


async def main():
    """Главная функция."""
    
    # Инициализация
    api = DMarketAPI(
        public_key=os.getenv("DMARKET_PUBLIC_KEY"),
        secret_key=os.getenv("DMARKET_SECRET_KEY")
    )
    
    ml_predictor = EnhancedPricePredictor()
    ai_arbitrage = AIArbitragePredictor(ml_predictor)
    
    print("💼 ДИВЕРСИФИЦИРОВАННЫЙ ПОРТФЕЛЬ АРБИТРАЖА")
    print("=" * 80)
    
    # Конфигурация портфеля
    total_capital = 500.0
    
    portfolio_configs = [
        # Консервативный подход - CS:GO
        PortfolioConfig(
            game="csgo",
            balance=150.0,  # 30% капитала
            risk_level="low",
            max_items=3
        ),
        # Сбалансированный подход - Dota 2
        PortfolioConfig(
            game="dota2",
            balance=200.0,  # 40% капитала
            risk_level="medium",
            max_items=4
        ),
        # Агрессивный подход - Rust
        PortfolioConfig(
            game="rust",
            balance=150.0,  # 30% капитала
            risk_level="high",
            max_items=3
        )
    ]
    
    print(f"💰 Общий капитал: ${total_capital:.2f}")
    print(f"📈 Стратегия: 30% low / 40% medium / 30% high risk\n")
    
    # Построение портфеля
    portfolio = await build_portfolio(api, ai_arbitrage, portfolio_configs)
    
    # Отчет
    print("\n" + "=" * 80)
    print("📊 ИТОГОВЫЙ ПОРТФЕЛЬ")
    print("=" * 80)
    
    print(f"\n💼 Позиций в портфеле: {len(portfolio['positions'])}")
    print(f"💵 Всего инвестировано: ${portfolio['total_invested']:.2f}")
    print(f"💰 Ожидаемая прибыль: ${portfolio['expected_profit']:.2f}")
    print(f"📈 Ожидаемый ROI: {(portfolio['expected_profit'] / portfolio['total_invested'] * 100):.1f}%")
    print(f"✨ Средняя уверенность: {portfolio['avg_confidence']:.1%}")
    
    print(f"\n⚠️ Risk Breakdown:")
    for risk, count in portfolio['risk_breakdown'].items():
        percentage = (count / len(portfolio['positions'])) * 100
        print(f"   {risk.upper()}: {count} позиций ({percentage:.0f}%)")
    
    # Детали позиций
    print("\n" + "-" * 80)
    print("📦 ПОЗИЦИИ В ПОРТФЕЛЕ:")
    print("-" * 80)
    
    for i, pos in enumerate(portfolio["positions"], 1):
        print(f"\n{i}. [{pos['game'].upper()}] {pos['title']}")
        print(f"   💵 Цена: ${pos['price']:.2f}")
        print(f"   💰 Прогноз прибыли: ${pos['predicted_profit']:.2f}")
        print(f"   ✨ Уверенность: {pos['confidence']:.1%}")
        print(f"   ⚠️ Risk: {pos['risk_level'].upper()} ({pos['risk_score']:.1f}/100)")
    
    # Группировка по играм
    print("\n" + "-" * 80)
    print("🎮 ПО ИГРАМ:")
    print("-" * 80)
    
    games = set(p["game"] for p in portfolio["positions"])
    for game in sorted(games):
        game_positions = [p for p in portfolio["positions"] if p["game"] == game]
        total_invested_game = sum(p["price"] for p in game_positions)
        total_profit_game = sum(p["predicted_profit"] for p in game_positions)
        
        print(f"\n{game.upper()}:")
        print(f"  Позиций: {len(game_positions)}")
        print(f"  Инвестировано: ${total_invested_game:.2f}")
        print(f"  Ожидаемая прибыль: ${total_profit_game:.2f}")
        print(f"  ROI: {(total_profit_game / total_invested_game * 100):.1f}%")
    
    print("\n" + "=" * 80)
    print("✅ Портфель построен успешно!")
    print(f"💡 Диверсификация: {len(games)} игр, {len(portfolio['risk_breakdown'])} уровней риска")
    
    await api.close()


if __name__ == "__main__":
    if not os.getenv("DMARKET_PUBLIC_KEY"):
        print("❌ Ошибка: DMARKET_PUBLIC_KEY не найден")
        sys.exit(1)
    
    asyncio.run(main())
