"""
Модуль для rate limiting пользователей бота.

Защищает бот от злоупотреблений, ограничивая количество команд
которые пользователь может выполнить за определенный период.
"""

import asyncio
from collections import defaultdict
from dataclasses import dataclass
import time
from typing import Any

from redis.asyncio import Redis
import structlog


logger = structlog.get_logger(__name__)


@dataclass
class RateLimitConfig:
    """Конфигурация rate limit для действия."""

    requests: int  # Количество запросов
    window: int  # Временное окно в секундах
    burst: int | None = None  # Burst limit (опционально)


class UserRateLimiter:
    """
    Rate limiter для пользователей бота.

    Использует sliding window algorithm с Redis для распределенного rate limiting.
    """

    # Лимиты по умолчанию для различных действий
    DEFAULT_LIMITS = {
        "scan": RateLimitConfig(requests=10, window=60, burst=15),  # 10 сканов/мин
        "target_create": RateLimitConfig(requests=5, window=60),  # 5 таргетов/мин
        "target_delete": RateLimitConfig(requests=10, window=60),  # 10 удалений/мин
        "balance": RateLimitConfig(requests=20, window=60),  # 20 проверок баланса/мин
        "portfolio": RateLimitConfig(requests=15, window=60),  # 15 проверок портфолио/мин
        "settings": RateLimitConfig(requests=5, window=60),  # 5 изменений настроек/мин
        "default": RateLimitConfig(requests=30, window=60, burst=40),  # 30 команд/мин
    }

    def __init__(
        self,
        redis_client: Redis | None = None,
        custom_limits: dict[str, RateLimitConfig] | None = None,
        enable_burst: bool = True,
    ):
        """
        Инициализация rate limiter.

        Args:
            redis_client: Redis клиент для распределенного хранения
            custom_limits: Кастомные лимиты для переопределения
            enable_burst: Разрешить burst режим
        """
        self.redis = redis_client
        self.limits = {**self.DEFAULT_LIMITS}
        if custom_limits:
            self.limits.update(custom_limits)

        self.enable_burst = enable_burst

        # Локальный кэш для случаев без Redis
        self._local_cache: dict[str, list[float]] = defaultdict(list)
        self._lock = asyncio.Lock()

    def _get_limit(self, action: str) -> RateLimitConfig:
        """Получить лимит для действия."""
        return self.limits.get(action, self.limits["default"])

    async def check_limit(
        self,
        user_id: int,
        action: str = "default",
        cost: int = 1,
    ) -> tuple[bool, dict[str, Any]]:
        """
        Проверить лимит для пользователя.

        Args:
            user_id: ID пользователя
            action: Тип действия
            cost: Стоимость действия (для weighted rate limiting)

        Returns:
            Tuple[bool, dict]: (разрешено, info)
                - bool: True если запрос разрешен
                - dict: Информация о лимитах
        """
        limit_config = self._get_limit(action)

        if self.redis:
            return await self._check_limit_redis(user_id, action, limit_config, cost)
        return await self._check_limit_local(user_id, action, limit_config, cost)

    async def _check_limit_redis(
        self,
        user_id: int,
        action: str,
        config: RateLimitConfig,
        cost: int,
    ) -> tuple[bool, dict[str, Any]]:
        """Проверка с использованием Redis (sliding window)."""
        key = f"rate_limit:{user_id}:{action}"
        now = time.time()
        window_start = now - config.window

        # Используем Redis sorted set для sliding window
        pipe = self.redis.pipeline()

        # Удалить старые записи
        pipe.zremrangebyscore(key, 0, window_start)

        # Получить текущее количество запросов
        pipe.zcard(key)

        # Добавить текущий запрос
        pipe.zadd(key, {f"{now}:{cost}": now})

        # Установить TTL
        pipe.expire(key, config.window)

        results = await pipe.execute()
        current_count = results[1]

        # Проверка burst limit
        max_requests = config.requests
        if self.enable_burst and config.burst:
            max_requests = config.burst

        allowed = current_count < max_requests

        # Вычислить время до сброса
        reset_time = int(window_start + config.window)
        retry_after = max(0, reset_time - int(now))

        info = {
            "limit": max_requests,
            "remaining": max(0, max_requests - current_count - cost),
            "reset": reset_time,
            "retry_after": retry_after if not allowed else 0,
            "action": action,
        }

        if not allowed:
            logger.warning(
                "rate_limit_exceeded",
                user_id=user_id,
                action=action,
                current=current_count,
                limit=max_requests,
            )

        return allowed, info

    async def _check_limit_local(
        self,
        user_id: int,
        action: str,
        config: RateLimitConfig,
        cost: int,
    ) -> tuple[bool, dict[str, Any]]:
        """Проверка с использованием локального кэша."""
        async with self._lock:
            key = f"{user_id}:{action}"
            now = time.time()
            window_start = now - config.window

            # Очистить старые записи
            self._local_cache[key] = [ts for ts in self._local_cache[key] if ts > window_start]

            current_count = len(self._local_cache[key])

            max_requests = config.requests
            if self.enable_burst and config.burst:
                max_requests = config.burst

            allowed = current_count < max_requests

            if allowed:
                # Добавить текущий запрос с учетом стоимости
                for _ in range(cost):
                    self._local_cache[key].append(now)

            reset_time = int(window_start + config.window)
            retry_after = max(0, reset_time - int(now))

            info = {
                "limit": max_requests,
                "remaining": max(0, max_requests - current_count - cost),
                "reset": reset_time,
                "retry_after": retry_after if not allowed else 0,
                "action": action,
            }

            if not allowed:
                logger.warning(
                    "rate_limit_exceeded",
                    user_id=user_id,
                    action=action,
                    current=current_count,
                    limit=max_requests,
                )

            return allowed, info

    async def get_user_stats(self, user_id: int) -> dict[str, Any]:
        """
        Получить статистику использования для пользователя.

        Args:
            user_id: ID пользователя

        Returns:
            Статистика по всем действиям
        """
        stats = {}

        for action in self.limits:
            _, info = await self.check_limit(user_id, action, cost=0)
            stats[action] = info

        return stats

    async def reset_user_limits(self, user_id: int, action: str | None = None) -> None:
        """
        Сбросить лимиты пользователя.

        Args:
            user_id: ID пользователя
            action: Конкретное действие или None для всех
        """
        if self.redis:
            if action:
                key = f"rate_limit:{user_id}:{action}"
                await self.redis.delete(key)
            else:
                pattern = f"rate_limit:{user_id}:*"
                keys = []
                async for key in self.redis.scan_iter(match=pattern):
                    keys.append(key)
                if keys:
                    await self.redis.delete(*keys)
        else:
            async with self._lock:
                if action:
                    key = f"{user_id}:{action}"
                    if key in self._local_cache:
                        del self._local_cache[key]
                else:
                    # Удалить все ключи пользователя
                    keys_to_delete = [
                        k for k in self._local_cache if k.startswith(f"{user_id}:")
                    ]
                    for key in keys_to_delete:
                        del self._local_cache[key]

        logger.info(
            "user_limits_reset",
            user_id=user_id,
            action=action or "all",
        )

    async def add_whitelist(self, user_id: int) -> None:
        """
        Добавить пользователя в whitelist (без лимитов).

        Args:
            user_id: ID пользователя
        """
        if self.redis:
            key = f"rate_limit:whitelist:{user_id}"
            await self.redis.set(key, "1", ex=86400 * 30)  # 30 дней

        logger.info("user_whitelisted", user_id=user_id)

    async def is_whitelisted(self, user_id: int) -> bool:
        """
        Проверить находится ли пользователь в whitelist.

        Args:
            user_id: ID пользователя

        Returns:
            True если в whitelist
        """
        if self.redis:
            key = f"rate_limit:whitelist:{user_id}"
            result = await self.redis.get(key)
            return result is not None

        return False

    async def remove_whitelist(self, user_id: int) -> None:
        """
        Удалить пользователя из whitelist.

        Args:
            user_id: ID пользователя
        """
        if self.redis:
            key = f"rate_limit:whitelist:{user_id}"
            await self.redis.delete(key)

        logger.info("user_removed_from_whitelist", user_id=user_id)

    def update_limit(self, action: str, config: RateLimitConfig) -> None:
        """
        Обновить лимит для действия.

        Args:
            action: Тип действия
            config: Новая конфигурация лимита
        """
        self.limits[action] = config
        logger.info(
            "limit_updated",
            action=action,
            requests=config.requests,
            window=config.window,
        )
