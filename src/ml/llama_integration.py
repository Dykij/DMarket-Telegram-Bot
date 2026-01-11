"""
Llama 3.1 8B Integration Module for DMarket Telegram Bot.

Специализированный модуль для интеграции Llama 3.1 8B (Q4 квантизация) с ботом.
Оптимизирован для Ryzen 7 5700X, 32GB RAM, RX 6600 (8GB VRAM).

Features:
- Market analysis (анализ рынка)
- Price prediction (прогнозирование цен)
- Arbitrage recommendations (рекомендации по арбитражу)
- Trading advice (торговые советы)
- Natural language queries (запросы на естественном языке)
"""

import asyncio
import json
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

import structlog

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False


logger = structlog.get_logger(__name__)


class LlamaTaskType(str, Enum):
    """Типы задач для Llama."""
    
    MARKET_ANALYSIS = "market_analysis"
    PRICE_PREDICTION = "price_prediction"
    ARBITRAGE_RECOMMENDATION = "arbitrage_recommendation"
    TRADING_ADVICE = "trading_advice"
    GENERAL_CHAT = "general_chat"
    ITEM_EVALUATION = "item_evaluation"
    RISK_ASSESSMENT = "risk_assessment"


@dataclass
class LlamaConfig:
    """Конфигурация Llama модели."""
    
    model_name: str = "llama3.1:8b"
    ollama_url: str = "http://localhost:11434"
    temperature: float = 0.7
    top_p: float = 0.9
    max_tokens: int = 1024
    timeout: float = 120.0
    
    # Параметры для Q4 квантизации
    quantization: str = "Q4_K_M"
    context_length: int = 8192
    
    # Hardware recommendations
    min_vram_gb: int = 6
    recommended_vram_gb: int = 8
    cpu_threads: int = 8


@dataclass
class LlamaResponse:
    """Ответ от Llama."""
    
    success: bool
    response: str
    task_type: LlamaTaskType
    tokens_used: int = 0
    processing_time_ms: float = 0
    error: str | None = None
    metadata: dict[str, Any] | None = None


# Специализированные промпты для разных задач
TASK_PROMPTS = {
    LlamaTaskType.MARKET_ANALYSIS: """Ты - эксперт по анализу рынка игровых скинов DMarket.
Анализируй рынок на основе предоставленных данных:
- Определяй тренды (рост/падение/стабильность)
- Выявляй аномалии цен
- Оценивай ликвидность предметов
- Давай прогнозы на основе паттернов

Формат ответа:
📊 ТРЕНД: [восходящий/нисходящий/боковой]
📈 СИЛА ТРЕНДА: [сильный/умеренный/слабый]
💰 РЕКОМЕНДАЦИЯ: [покупать/продавать/держать]
⚠️ РИСК: [низкий/средний/высокий]
📝 АНАЛИЗ: [подробный анализ]""",

    LlamaTaskType.PRICE_PREDICTION: """Ты - AI для прогнозирования цен на игровые предметы.
На основе исторических данных и текущих трендов:
- Прогнозируй изменение цены на 24ч/7д/30д
- Определяй уровни поддержки и сопротивления
- Оценивай вероятность прогноза

Формат ответа:
🎯 ПРОГНОЗ 24ч: [цена] ([+/-]X%)
🎯 ПРОГНОЗ 7д: [цена] ([+/-]X%)
🎯 ПРОГНОЗ 30д: [цена] ([+/-]X%)
📊 УРОВЕНЬ ПОДДЕРЖКИ: [цена]
📊 УРОВЕНЬ СОПРОТИВЛЕНИЯ: [цена]
🔮 УВЕРЕННОСТЬ: [низкая/средняя/высокая]
📝 ОБОСНОВАНИЕ: [анализ]""",

    LlamaTaskType.ARBITRAGE_RECOMMENDATION: """Ты - специалист по арбитражу между площадками.
Площадки и комиссии:
- DMarket: 7%
- Waxpeer: 6%
- Steam Market: 15%

Анализируй возможности арбитража:
- Рассчитывай чистую прибыль с учетом комиссий
- Оценивай риски (ликвидность, время продажи)
- Ранжируй по ROI

Формат ответа:
💎 ВОЗМОЖНОСТЬ: [описание]
💰 ЧИСТАЯ ПРИБЫЛЬ: $X.XX (Y%)
📈 ROI: Z%
⏱️ ВРЕМЯ РЕАЛИЗАЦИИ: [часы/дни]
⚠️ РИСК: [низкий/средний/высокий]
✅ РЕКОМЕНДАЦИЯ: [действовать/подождать/пропустить]""",

    LlamaTaskType.TRADING_ADVICE: """Ты - торговый советник для DMarket бота.
Давай рекомендации по:
- Моменту входа/выхода из позиции
- Размеру позиции
- Управлению рисками
- Диверсификации портфеля

Уровни арбитража:
- boost: $0.50-$3 (начинающие)
- standard: $3-$10 (стандарт)
- medium: $10-$30 (средний)
- advanced: $30-$100 (продвинутый)
- pro: $100+ (профессионал)

Формат ответа:
🎯 СОВЕТ: [краткий совет]
📊 ПОЗИЦИЯ: [открыть/закрыть/держать]
💰 РАЗМЕР: [% от баланса]
⚠️ СТОП-ЛОСС: [уровень]
🎯 ТЕЙК-ПРОФИТ: [уровень]
📝 ПОЯСНЕНИЕ: [детали]""",

    LlamaTaskType.ITEM_EVALUATION: """Ты - эксперт по оценке игровых предметов.
Оценивай предметы по критериям:
- Редкость и популярность
- Историческая динамика цен
- Ликвидность на разных площадках
- Потенциал роста/падения

Формат ответа:
🏷️ ПРЕДМЕТ: [название]
💰 СПРАВЕДЛИВАЯ ЦЕНА: $X.XX
📊 ЛИКВИДНОСТЬ: [высокая/средняя/низкая]
🔥 ПОПУЛЯРНОСТЬ: [высокая/средняя/низкая]
📈 ПОТЕНЦИАЛ РОСТА: [+X%]
⚠️ РИСК ПАДЕНИЯ: [-Y%]
✅ РЕКОМЕНДАЦИЯ: [покупать/держать/продавать]""",

    LlamaTaskType.RISK_ASSESSMENT: """Ты - риск-менеджер для торговли скинами.
Оценивай риски:
- Волатильность рынка
- Ликвидность позиции
- Концентрация портфеля
- Внешние факторы (обновления игры, турниры)

Формат ответа:
⚠️ ОБЩИЙ УРОВЕНЬ РИСКА: [1-10]
📊 ВОЛАТИЛЬНОСТЬ: [низкая/средняя/высокая]
💧 ЛИКВИДНОСТЬ: [высокая/средняя/низкая]
🎯 ДИВЕРСИФИКАЦИЯ: [хорошая/требует улучшения/плохая]
🛡️ РЕКОМЕНДАЦИИ:
- [пункт 1]
- [пункт 2]
- [пункт 3]""",

    LlamaTaskType.GENERAL_CHAT: """Ты - AI-помощник для DMarket Trading Bot.
Помогай пользователям:
1. Анализировать рынок CS:GO, Dota 2, Rust, TF2
2. Находить арбитражные возможности
3. Давать рекомендации по покупке/продаже
4. Объяснять торговые стратегии
5. Помогать с настройкой бота

Комиссии: DMarket 7%, Waxpeer 6%, Steam 15%
Отвечай на русском, кратко и по делу.""",
}


class LlamaIntegration:
    """
    Интеграция Llama 3.1 8B для DMarket бота.
    
    Оптимизировано для:
    - Ryzen 7 5700X (8 ядер)
    - 32 GB RAM
    - Radeon RX 6600 (8 GB VRAM)
    - Q4_K_M квантизация
    """
    
    def __init__(self, config: LlamaConfig | None = None):
        """Инициализация."""
        self.config = config or LlamaConfig()
        self._client: httpx.AsyncClient | None = None
        self._is_available: bool | None = None
        self._last_check: datetime | None = None
        
        # Статистика
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_tokens": 0,
            "avg_response_time_ms": 0.0,
        }
        
        logger.info(
            "llama_integration_initialized",
            model=self.config.model_name,
            url=self.config.ollama_url,
        )
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Получить HTTP клиент."""
        if not HTTPX_AVAILABLE:
            raise RuntimeError("httpx не установлен. Установите: pip install httpx")
        
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self.config.timeout)
        return self._client
    
    async def check_availability(self, force: bool = False) -> bool:
        """
        Проверить доступность Ollama и модели.
        
        Args:
            force: Принудительная проверка (игнорирует кэш)
            
        Returns:
            True если доступна
        """
        # Используем кэш если не прошло 30 секунд
        if not force and self._last_check:
            elapsed = (datetime.now() - self._last_check).total_seconds()
            if elapsed < 30 and self._is_available is not None:
                return self._is_available
        
        try:
            client = await self._get_client()
            response = await client.get(
                f"{self.config.ollama_url}/api/tags",
                timeout=5.0,
            )
            
            if response.status_code == 200:
                data = response.json()
                models = [m["name"] for m in data.get("models", [])]
                
                # Проверяем что нужная модель установлена
                model_available = any(
                    self.config.model_name in m or m.startswith(self.config.model_name.split(":")[0])
                    for m in models
                )
                
                self._is_available = model_available
                self._last_check = datetime.now()
                
                if not model_available:
                    logger.warning(
                        "llama_model_not_found",
                        model=self.config.model_name,
                        available_models=models,
                    )
                
                return model_available
            
            self._is_available = False
            return False
            
        except Exception as e:
            logger.error("llama_availability_check_failed", error=str(e))
            self._is_available = False
            self._last_check = datetime.now()
            return False
    
    async def get_available_models(self) -> list[str]:
        """Получить список доступных моделей."""
        try:
            client = await self._get_client()
            response = await client.get(f"{self.config.ollama_url}/api/tags")
            
            if response.status_code == 200:
                data = response.json()
                return [m["name"] for m in data.get("models", [])]
            return []
            
        except Exception as e:
            logger.error("get_models_failed", error=str(e))
            return []
    
    def _get_system_prompt(self, task_type: LlamaTaskType) -> str:
        """Получить системный промпт для задачи."""
        return TASK_PROMPTS.get(task_type, TASK_PROMPTS[LlamaTaskType.GENERAL_CHAT])
    
    async def execute_task(
        self,
        task_type: LlamaTaskType,
        user_message: str,
        context: dict[str, Any] | None = None,
        conversation_history: list[dict[str, str]] | None = None,
    ) -> LlamaResponse:
        """
        Выполнить задачу с помощью Llama.
        
        Args:
            task_type: Тип задачи
            user_message: Сообщение пользователя
            context: Дополнительный контекст (данные о рынке и т.д.)
            conversation_history: История разговора
            
        Returns:
            LlamaResponse с результатом
        """
        start_time = datetime.now()
        self.stats["total_requests"] += 1
        
        if not await self.check_availability():
            self.stats["failed_requests"] += 1
            return LlamaResponse(
                success=False,
                response="",
                task_type=task_type,
                error="Ollama или модель недоступны. Запустите: ollama serve",
            )
        
        try:
            client = await self._get_client()
            
            # Формируем сообщение с контекстом
            enhanced_message = user_message
            if context:
                context_str = json.dumps(context, ensure_ascii=False, indent=2)
                enhanced_message = f"{user_message}\n\n📊 Данные:\n```json\n{context_str}\n```"
            
            # Формируем сообщения
            messages = [
                {"role": "system", "content": self._get_system_prompt(task_type)},
            ]
            
            # Добавляем историю разговора
            if conversation_history:
                messages.extend(conversation_history[-10:])  # Последние 10 сообщений
            
            messages.append({"role": "user", "content": enhanced_message})
            
            # Отправляем запрос
            response = await client.post(
                f"{self.config.ollama_url}/api/chat",
                json={
                    "model": self.config.model_name,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": self.config.temperature,
                        "top_p": self.config.top_p,
                        "num_predict": self.config.max_tokens,
                        "num_ctx": self.config.context_length,
                    },
                },
            )
            
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            if response.status_code == 200:
                data = response.json()
                ai_response = data.get("message", {}).get("content", "")
                tokens = data.get("eval_count", 0) + data.get("prompt_eval_count", 0)
                
                self.stats["successful_requests"] += 1
                self.stats["total_tokens"] += tokens
                
                # Обновляем среднее время ответа
                n = self.stats["successful_requests"]
                avg = self.stats["avg_response_time_ms"]
                self.stats["avg_response_time_ms"] = avg + (processing_time - avg) / n
                
                logger.info(
                    "llama_task_completed",
                    task_type=task_type.value,
                    tokens=tokens,
                    time_ms=processing_time,
                )
                
                return LlamaResponse(
                    success=True,
                    response=ai_response,
                    task_type=task_type,
                    tokens_used=tokens,
                    processing_time_ms=processing_time,
                    metadata={
                        "model": self.config.model_name,
                        "context_provided": context is not None,
                    },
                )
            else:
                self.stats["failed_requests"] += 1
                error_msg = f"HTTP {response.status_code}: {response.text[:200]}"
                logger.error("llama_request_failed", error=error_msg)
                
                return LlamaResponse(
                    success=False,
                    response="",
                    task_type=task_type,
                    processing_time_ms=processing_time,
                    error=error_msg,
                )
                
        except httpx.TimeoutException:
            self.stats["failed_requests"] += 1
            return LlamaResponse(
                success=False,
                response="",
                task_type=task_type,
                error="Таймаут запроса. Попробуйте позже или уменьшите размер запроса.",
            )
        except Exception as e:
            self.stats["failed_requests"] += 1
            logger.error("llama_task_error", error=str(e), exc_info=True)
            
            return LlamaResponse(
                success=False,
                response="",
                task_type=task_type,
                error=str(e),
            )
    
    # === Высокоуровневые методы для конкретных задач ===
    
    async def analyze_market(
        self,
        game: str,
        market_data: dict[str, Any] | None = None,
    ) -> LlamaResponse:
        """
        Анализ рынка для указанной игры.
        
        Args:
            game: Игра (csgo, dota2, rust, tf2)
            market_data: Данные о рынке (цены, объемы и т.д.)
            
        Returns:
            LlamaResponse с анализом
        """
        message = f"Проанализируй текущий рынок {game.upper()}."
        return await self.execute_task(
            LlamaTaskType.MARKET_ANALYSIS,
            message,
            context=market_data,
        )
    
    async def predict_price(
        self,
        item_name: str,
        price_history: list[dict[str, Any]],
    ) -> LlamaResponse:
        """
        Прогноз цены предмета.
        
        Args:
            item_name: Название предмета
            price_history: История цен [{date, price, volume}, ...]
            
        Returns:
            LlamaResponse с прогнозом
        """
        message = f"Дай прогноз цены для предмета: {item_name}"
        return await self.execute_task(
            LlamaTaskType.PRICE_PREDICTION,
            message,
            context={"item": item_name, "history": price_history},
        )
    
    async def find_arbitrage(
        self,
        opportunities: list[dict[str, Any]],
    ) -> LlamaResponse:
        """
        Анализ арбитражных возможностей.
        
        Args:
            opportunities: Список возможностей [{item, buy_price, sell_price, platform_buy, platform_sell}, ...]
            
        Returns:
            LlamaResponse с рекомендациями
        """
        message = "Проанализируй арбитражные возможности и дай рекомендации."
        return await self.execute_task(
            LlamaTaskType.ARBITRAGE_RECOMMENDATION,
            message,
            context={"opportunities": opportunities},
        )
    
    async def get_trading_advice(
        self,
        portfolio: dict[str, Any],
        balance: float,
        risk_tolerance: str = "medium",
    ) -> LlamaResponse:
        """
        Торговые рекомендации.
        
        Args:
            portfolio: Текущий портфель
            balance: Доступный баланс
            risk_tolerance: Уровень риска (low, medium, high)
            
        Returns:
            LlamaResponse с советами
        """
        message = f"Дай торговые рекомендации. Мой уровень риска: {risk_tolerance}."
        return await self.execute_task(
            LlamaTaskType.TRADING_ADVICE,
            message,
            context={
                "portfolio": portfolio,
                "balance": balance,
                "risk_tolerance": risk_tolerance,
            },
        )
    
    async def evaluate_item(
        self,
        item_name: str,
        current_price: float,
        item_data: dict[str, Any] | None = None,
    ) -> LlamaResponse:
        """
        Оценка предмета.
        
        Args:
            item_name: Название предмета
            current_price: Текущая цена
            item_data: Дополнительные данные о предмете
            
        Returns:
            LlamaResponse с оценкой
        """
        message = f"Оцени предмет: {item_name} (текущая цена: ${current_price:.2f})"
        context = {"item": item_name, "price": current_price}
        if item_data:
            context.update(item_data)
            
        return await self.execute_task(
            LlamaTaskType.ITEM_EVALUATION,
            message,
            context=context,
        )
    
    async def assess_risk(
        self,
        portfolio: dict[str, Any],
    ) -> LlamaResponse:
        """
        Оценка рисков портфеля.
        
        Args:
            portfolio: Данные портфеля
            
        Returns:
            LlamaResponse с оценкой рисков
        """
        message = "Оцени риски моего портфеля и дай рекомендации."
        return await self.execute_task(
            LlamaTaskType.RISK_ASSESSMENT,
            message,
            context={"portfolio": portfolio},
        )
    
    async def chat(
        self,
        message: str,
        conversation_history: list[dict[str, str]] | None = None,
    ) -> LlamaResponse:
        """
        Общий чат с AI.
        
        Args:
            message: Сообщение пользователя
            conversation_history: История разговора
            
        Returns:
            LlamaResponse
        """
        return await self.execute_task(
            LlamaTaskType.GENERAL_CHAT,
            message,
            conversation_history=conversation_history,
        )
    
    def get_statistics(self) -> dict[str, Any]:
        """Получить статистику использования."""
        return {
            **self.stats,
            "success_rate": (
                self.stats["successful_requests"] / max(1, self.stats["total_requests"])
            ) * 100,
            "model": self.config.model_name,
            "is_available": self._is_available,
        }
    
    async def close(self) -> None:
        """Закрыть соединения."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None


# Глобальный экземпляр
_llama: LlamaIntegration | None = None


def get_llama() -> LlamaIntegration:
    """Получить глобальный экземпляр Llama интеграции."""
    global _llama
    if _llama is None:
        _llama = LlamaIntegration()
    return _llama


async def init_llama(config: LlamaConfig | None = None) -> LlamaIntegration:
    """Инициализировать Llama интеграцию."""
    global _llama
    _llama = LlamaIntegration(config)
    
    # Проверяем доступность
    available = await _llama.check_availability()
    if available:
        logger.info("llama_ready", model=_llama.config.model_name)
    else:
        logger.warning(
            "llama_not_available",
            model=_llama.config.model_name,
            hint="Запустите: ollama serve && ollama pull llama3.1:8b",
        )
    
    return _llama
