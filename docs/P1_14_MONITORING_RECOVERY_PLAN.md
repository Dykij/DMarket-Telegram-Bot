# 📋 План реализации: P1-14 Мониторинг и Recovery

**Дата создания**: 11 декабря 2025 г.
**Статус**: 🟠 ПЛАН ГОТОВ
**Оценка времени**: 10-15 часов
**Сложность**: 🟡 Средняя

---

## 📌 Обзор

Задача P1-14 направлена на создание комплексной системы мониторинга и автоматического восстановления бота для обеспечения uptime >99%. Включает расширенные health checks, webhook failover, graceful shutdown и автоматическое резервное копирование базы данных.

---

## 📊 Анализ влияния

### Затронутые модули

| Файл | Действие | Описание |
|------|----------|----------|
| `scripts/health_check.py` | **Модификация** | Расширить для cron-запусков, heartbeat, alerts |
| `src/main.py` | **Модификация** | Улучшить graceful shutdown, signal handlers |
| `src/utils/health_monitor.py` | **Новый файл** | Heartbeat механизм, service monitoring |
| `src/utils/webhook_failover.py` | **Новый файл** | Telegram webhook failover логика |
| `scripts/backup_database.py` | **Новый файл** | Автоматическое резервное копирование |
| `src/telegram_bot/webhook_handler.py` | **Новый файл** | Health endpoint для webhook |
| `config/config.yaml` | **Модификация** | Добавить настройки мониторинга |

### Зависимости

- `aiohttp` - для webhook HTTP сервера (уже есть)
- `httpx` - для health check запросов (уже есть)
- `schedule` или `APScheduler` - для планировщика (APScheduler уже установлен)
- `redis` - для distributed heartbeat (опционально, уже интегрирован)

### Риски

1. **Webhook vs Polling конфликт** - Необходима атомарная логика переключения
2. **Потеря данных при shutdown** - Требуется корректное завершение pending requests
3. **Блокировка файлов при backup** - Использовать WAL mode в SQLite
4. **Race conditions** - Использовать locks для критических операций

---

## 🎯 Требования

### Функциональные требования

- [ ] Health checks выполняются по расписанию (cron-совместимо)
- [ ] Heartbeat механизм для всех критических сервисов (DB, Redis, API)
- [ ] Автоматические alerts при сбоях (в Telegram и/или Discord)
- [ ] Telegram webhook как альтернатива polling с автопереключением
- [ ] Graceful shutdown с сохранением состояния
- [ ] Автоматические backup базы данных по расписанию
- [ ] Возможность ручного restore из backup

### Нефункциональные требования

- Uptime целевой показатель: >99%
- Время обнаружения сбоя: <60 секунд
- Время восстановления (RTO): <5 минут
- Recovery Point Objective (RPO): <1 час (потеря данных)

---

## 🛠️ Шаги реализации

### Шаг 1: Health Check расширение (⏱️ 4 часа)

#### 1.1 Создать модуль health_monitor.py

**Файл**: `src/utils/health_monitor.py`

```python
"""Health monitoring and heartbeat system for DMarket Bot.

Provides continuous health monitoring for critical services:
- Database connectivity
- Redis connectivity
- DMarket API availability
- Telegram API connectivity
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any, Callable

import httpx

from src.utils.database import DatabaseManager
from src.utils.redis_cache import RedisCache

logger = logging.getLogger(__name__)


class ServiceStatus(str, Enum):
    """Service health status."""
    
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """Result of a health check."""
    
    service: str
    status: ServiceStatus
    response_time_ms: float
    message: str = ""
    last_check: datetime = field(default_factory=lambda: datetime.now(UTC))
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class HeartbeatConfig:
    """Configuration for heartbeat monitoring."""
    
    interval_seconds: int = 30
    timeout_seconds: int = 10
    failure_threshold: int = 3
    recovery_threshold: int = 2


class HealthMonitor:
    """Centralized health monitoring for all services."""
    
    def __init__(
        self,
        database: DatabaseManager | None = None,
        redis_cache: RedisCache | None = None,
        dmarket_api_url: str = "https://api.dmarket.com",
        telegram_bot_token: str | None = None,
        config: HeartbeatConfig | None = None,
    ):
        self.database = database
        self.redis_cache = redis_cache
        self.dmarket_api_url = dmarket_api_url
        self.telegram_bot_token = telegram_bot_token
        self.config = config or HeartbeatConfig()
        
        self._running = False
        self._heartbeat_task: asyncio.Task | None = None
        self._failure_counts: dict[str, int] = {}
        self._success_counts: dict[str, int] = {}
        self._last_results: dict[str, HealthCheckResult] = {}
        self._alert_callbacks: list[Callable[[HealthCheckResult], Any]] = []
    
    def register_alert_callback(
        self,
        callback: Callable[[HealthCheckResult], Any],
    ) -> None:
        """Register callback for health alerts.
        
        Args:
            callback: Async or sync function to call on health alerts
        """
        self._alert_callbacks.append(callback)
    
    async def check_database(self) -> HealthCheckResult:
        """Check database connectivity."""
        start_time = datetime.now(UTC)
        
        if not self.database:
            return HealthCheckResult(
                service="database",
                status=ServiceStatus.UNKNOWN,
                response_time_ms=0,
                message="Database not configured",
            )
        
        try:
            # Execute simple query to verify connectivity
            status = await self.database.get_db_status()
            
            response_time = (datetime.now(UTC) - start_time).total_seconds() * 1000
            
            return HealthCheckResult(
                service="database",
                status=ServiceStatus.HEALTHY,
                response_time_ms=response_time,
                message="Database connection OK",
                details=status,
            )
        except Exception as e:
            response_time = (datetime.now(UTC) - start_time).total_seconds() * 1000
            logger.error(f"Database health check failed: {e}")
            
            return HealthCheckResult(
                service="database",
                status=ServiceStatus.UNHEALTHY,
                response_time_ms=response_time,
                message=f"Database error: {e}",
            )
    
    async def check_redis(self) -> HealthCheckResult:
        """Check Redis connectivity."""
        start_time = datetime.now(UTC)
        
        if not self.redis_cache:
            return HealthCheckResult(
                service="redis",
                status=ServiceStatus.UNKNOWN,
                response_time_ms=0,
                message="Redis not configured",
            )
        
        try:
            health = await self.redis_cache.health_check()
            response_time = (datetime.now(UTC) - start_time).total_seconds() * 1000
            
            if health.get("redis_ping"):
                return HealthCheckResult(
                    service="redis",
                    status=ServiceStatus.HEALTHY,
                    response_time_ms=response_time,
                    message="Redis connection OK",
                    details=health,
                )
            else:
                # Fallback to memory cache is OK
                return HealthCheckResult(
                    service="redis",
                    status=ServiceStatus.DEGRADED,
                    response_time_ms=response_time,
                    message="Redis unavailable, using memory cache",
                    details=health,
                )
        except Exception as e:
            response_time = (datetime.now(UTC) - start_time).total_seconds() * 1000
            logger.error(f"Redis health check failed: {e}")
            
            return HealthCheckResult(
                service="redis",
                status=ServiceStatus.UNHEALTHY,
                response_time_ms=response_time,
                message=f"Redis error: {e}",
            )
    
    async def check_dmarket_api(self) -> HealthCheckResult:
        """Check DMarket API connectivity."""
        start_time = datetime.now(UTC)
        
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
                # Use public endpoint that doesn't require auth
                response = await client.get(
                    f"{self.dmarket_api_url}/exchange/v1/ping",
                )
                
                response_time = (datetime.now(UTC) - start_time).total_seconds() * 1000
                
                if response.status_code == 200:
                    return HealthCheckResult(
                        service="dmarket_api",
                        status=ServiceStatus.HEALTHY,
                        response_time_ms=response_time,
                        message="DMarket API accessible",
                    )
                elif response.status_code == 429:
                    return HealthCheckResult(
                        service="dmarket_api",
                        status=ServiceStatus.DEGRADED,
                        response_time_ms=response_time,
                        message="DMarket API rate limited",
                    )
                else:
                    return HealthCheckResult(
                        service="dmarket_api",
                        status=ServiceStatus.UNHEALTHY,
                        response_time_ms=response_time,
                        message=f"DMarket API error: {response.status_code}",
                    )
        except httpx.TimeoutException:
            response_time = (datetime.now(UTC) - start_time).total_seconds() * 1000
            return HealthCheckResult(
                service="dmarket_api",
                status=ServiceStatus.UNHEALTHY,
                response_time_ms=response_time,
                message="DMarket API timeout",
            )
        except Exception as e:
            response_time = (datetime.now(UTC) - start_time).total_seconds() * 1000
            logger.error(f"DMarket API health check failed: {e}")
            
            return HealthCheckResult(
                service="dmarket_api",
                status=ServiceStatus.UNHEALTHY,
                response_time_ms=response_time,
                message=f"DMarket API error: {e}",
            )
    
    async def check_telegram_api(self) -> HealthCheckResult:
        """Check Telegram API connectivity."""
        start_time = datetime.now(UTC)
        
        if not self.telegram_bot_token:
            return HealthCheckResult(
                service="telegram_api",
                status=ServiceStatus.UNKNOWN,
                response_time_ms=0,
                message="Telegram bot token not configured",
            )
        
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
                response = await client.get(
                    f"https://api.telegram.org/bot{self.telegram_bot_token}/getMe",
                )
                
                response_time = (datetime.now(UTC) - start_time).total_seconds() * 1000
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("ok"):
                        return HealthCheckResult(
                            service="telegram_api",
                            status=ServiceStatus.HEALTHY,
                            response_time_ms=response_time,
                            message="Telegram API accessible",
                            details={"bot_info": data.get("result", {})},
                        )
                
                return HealthCheckResult(
                    service="telegram_api",
                    status=ServiceStatus.UNHEALTHY,
                    response_time_ms=response_time,
                    message=f"Telegram API error: {response.status_code}",
                )
        except Exception as e:
            response_time = (datetime.now(UTC) - start_time).total_seconds() * 1000
            logger.error(f"Telegram API health check failed: {e}")
            
            return HealthCheckResult(
                service="telegram_api",
                status=ServiceStatus.UNHEALTHY,
                response_time_ms=response_time,
                message=f"Telegram API error: {e}",
            )
    
    async def run_all_checks(self) -> dict[str, HealthCheckResult]:
        """Run all health checks concurrently.
        
        Returns:
            Dictionary of service name to health check result
        """
        results = await asyncio.gather(
            self.check_database(),
            self.check_redis(),
            self.check_dmarket_api(),
            self.check_telegram_api(),
            return_exceptions=False,
        )
        
        self._last_results = {
            "database": results[0],
            "redis": results[1],
            "dmarket_api": results[2],
            "telegram_api": results[3],
        }
        
        # Update failure counts and trigger alerts
        for service, result in self._last_results.items():
            await self._update_service_status(service, result)
        
        return self._last_results
    
    async def _update_service_status(
        self,
        service: str,
        result: HealthCheckResult,
    ) -> None:
        """Update service status and trigger alerts if needed."""
        if result.status == ServiceStatus.UNHEALTHY:
            self._failure_counts[service] = self._failure_counts.get(service, 0) + 1
            self._success_counts[service] = 0
            
            if self._failure_counts[service] >= self.config.failure_threshold:
                await self._trigger_alert(result)
        else:
            self._success_counts[service] = self._success_counts.get(service, 0) + 1
            
            # Reset failure count after recovery
            if self._success_counts[service] >= self.config.recovery_threshold:
                if self._failure_counts.get(service, 0) > 0:
                    logger.info(f"Service {service} recovered")
                    # Trigger recovery alert
                    recovery_result = HealthCheckResult(
                        service=service,
                        status=ServiceStatus.HEALTHY,
                        response_time_ms=result.response_time_ms,
                        message=f"Service {service} recovered",
                    )
                    await self._trigger_alert(recovery_result)
                    
                self._failure_counts[service] = 0
    
    async def _trigger_alert(self, result: HealthCheckResult) -> None:
        """Trigger alert callbacks."""
        logger.warning(
            f"Health alert for {result.service}: {result.status.value} - {result.message}",
        )
        
        for callback in self._alert_callbacks:
            try:
                cb_result = callback(result)
                if asyncio.iscoroutine(cb_result):
                    await cb_result
            except Exception as e:
                logger.error(f"Error in alert callback: {e}")
    
    async def start_heartbeat(self) -> None:
        """Start the heartbeat monitoring loop."""
        if self._running:
            logger.warning("Heartbeat already running")
            return
        
        self._running = True
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        logger.info(
            f"Heartbeat monitoring started (interval: {self.config.interval_seconds}s)",
        )
    
    async def stop_heartbeat(self) -> None:
        """Stop the heartbeat monitoring loop."""
        self._running = False
        
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
            
            self._heartbeat_task = None
        
        logger.info("Heartbeat monitoring stopped")
    
    async def _heartbeat_loop(self) -> None:
        """Main heartbeat loop."""
        while self._running:
            try:
                await self.run_all_checks()
                await asyncio.sleep(self.config.interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")
                await asyncio.sleep(self.config.interval_seconds)
    
    def get_overall_status(self) -> ServiceStatus:
        """Get overall system health status.
        
        Returns:
            Worst status among all services
        """
        if not self._last_results:
            return ServiceStatus.UNKNOWN
        
        statuses = [r.status for r in self._last_results.values()]
        
        if ServiceStatus.UNHEALTHY in statuses:
            return ServiceStatus.UNHEALTHY
        if ServiceStatus.DEGRADED in statuses:
            return ServiceStatus.DEGRADED
        if ServiceStatus.UNKNOWN in statuses:
            return ServiceStatus.UNKNOWN
        
        return ServiceStatus.HEALTHY
    
    def get_status_summary(self) -> dict[str, Any]:
        """Get summary of all service statuses.
        
        Returns:
            Dictionary with overall status and individual service statuses
        """
        return {
            "overall_status": self.get_overall_status().value,
            "timestamp": datetime.now(UTC).isoformat(),
            "services": {
                name: {
                    "status": result.status.value,
                    "response_time_ms": result.response_time_ms,
                    "message": result.message,
                    "last_check": result.last_check.isoformat(),
                }
                for name, result in self._last_results.items()
            },
            "failure_counts": self._failure_counts,
        }
```

#### 1.2 Обновить health_check.py для cron-режима

**Файл**: `scripts/health_check.py` (модификация)

Добавить:
- Флаг `--cron` для machine-readable output (exit codes)
- Флаг `--json` для JSON output
- Флаг `--alert` для отправки alerts при сбоях
- Поддержка конфигурации через environment variables

```python
# Добавить в начало файла после импортов:

import argparse
import json as json_module
import os

# Добавить в конец файла:

async def run_health_check_cron(
    config: Config,
    output_json: bool = False,
    send_alerts: bool = False,
) -> int:
    """Run health checks in cron-compatible mode.
    
    Args:
        config: Application configuration
        output_json: Output results as JSON
        send_alerts: Send alerts on failures
        
    Returns:
        Exit code: 0 = all healthy, 1 = degraded, 2 = unhealthy
    """
    from src.utils.health_monitor import HealthMonitor, ServiceStatus
    
    monitor = HealthMonitor(
        telegram_bot_token=config.telegram.bot_token,
        dmarket_api_url=config.dmarket.api_url,
    )
    
    results = await monitor.run_all_checks()
    overall = monitor.get_overall_status()
    
    if output_json:
        print(json_module.dumps(monitor.get_status_summary(), indent=2))
    else:
        # Human-readable output
        for service, result in results.items():
            status_icon = {
                ServiceStatus.HEALTHY: "✅",
                ServiceStatus.DEGRADED: "⚠️",
                ServiceStatus.UNHEALTHY: "❌",
                ServiceStatus.UNKNOWN: "❓",
            }.get(result.status, "❓")
            
            print(f"{status_icon} {service}: {result.message} ({result.response_time_ms:.1f}ms)")
    
    # Determine exit code
    if overall == ServiceStatus.HEALTHY:
        return 0
    elif overall == ServiceStatus.DEGRADED:
        return 1
    else:
        return 2


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DMarket Bot Health Check")
    parser.add_argument(
        "--cron",
        action="store_true",
        help="Run in cron mode (machine-readable output)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON",
    )
    parser.add_argument(
        "--alert",
        action="store_true",
        help="Send alerts on failures",
    )
    
    args = parser.parse_args()
    
    if args.cron or args.json:
        try:
            config = Config.load()
            config.validate()
            exit_code = asyncio.run(
                run_health_check_cron(
                    config,
                    output_json=args.json,
                    send_alerts=args.alert,
                ),
            )
            sys.exit(exit_code)
        except Exception as e:
            if args.json:
                print(json_module.dumps({"error": str(e), "status": "unhealthy"}))
            else:
                print(f"❌ Error: {e}")
            sys.exit(2)
    else:
        sys.exit(asyncio.run(main()))
```

#### 1.3 Создать cron job конфигурацию

**Файл**: `scripts/deployment/cron/health_check.cron`

```cron
# Health check every 5 minutes
*/5 * * * * cd /app && python scripts/health_check.py --cron >> /var/log/dmarket-bot/health_check.log 2>&1

# Send alerts on failures every 5 minutes
*/5 * * * * cd /app && python scripts/health_check.py --cron --alert >> /var/log/dmarket-bot/health_alerts.log 2>&1
```

---

### Шаг 2: Webhook для failover (⏱️ 3 часа)

#### 2.1 Создать webhook handler

**Файл**: `src/telegram_bot/webhook_handler.py`

```python
"""Telegram Webhook handler with health endpoint.

Provides webhook functionality as alternative to polling
with automatic failover capability.
"""

import asyncio
import logging
from datetime import UTC, datetime
from typing import Any

from aiohttp import web
from telegram import Update
from telegram.ext import Application

logger = logging.getLogger(__name__)


class WebhookHandler:
    """Handler for Telegram webhook with health endpoints."""
    
    def __init__(
        self,
        bot_app: Application,
        host: str = "0.0.0.0",
        port: int = 8443,
        webhook_path: str = "/webhook",
        health_path: str = "/health",
    ):
        """Initialize webhook handler.
        
        Args:
            bot_app: Telegram Application instance
            host: Host to bind to
            port: Port to listen on
            webhook_path: Path for webhook endpoint
            health_path: Path for health endpoint
        """
        self.bot_app = bot_app
        self.host = host
        self.port = port
        self.webhook_path = webhook_path
        self.health_path = health_path
        
        self._app: web.Application | None = None
        self._runner: web.AppRunner | None = None
        self._site: web.TCPSite | None = None
        self._running = False
        self._request_count = 0
        self._last_request_time: datetime | None = None
        self._start_time: datetime | None = None
    
    async def setup(self) -> web.Application:
        """Setup aiohttp web application."""
        self._app = web.Application()
        self._app.router.add_post(self.webhook_path, self._handle_webhook)
        self._app.router.add_get(self.health_path, self._handle_health)
        self._app.router.add_get("/", self._handle_root)
        
        return self._app
    
    async def start(self) -> None:
        """Start the webhook server."""
        if self._running:
            logger.warning("Webhook server already running")
            return
        
        if not self._app:
            await self.setup()
        
        self._runner = web.AppRunner(self._app)
        await self._runner.setup()
        
        self._site = web.TCPSite(
            self._runner,
            self.host,
            self.port,
        )
        await self._site.start()
        
        self._running = True
        self._start_time = datetime.now(UTC)
        
        logger.info(f"Webhook server started on {self.host}:{self.port}")
    
    async def stop(self) -> None:
        """Stop the webhook server."""
        if not self._running:
            return
        
        if self._site:
            await self._site.stop()
        
        if self._runner:
            await self._runner.cleanup()
        
        self._running = False
        logger.info("Webhook server stopped")
    
    async def _handle_webhook(self, request: web.Request) -> web.Response:
        """Handle incoming webhook update."""
        try:
            data = await request.json()
            update = Update.de_json(data, self.bot_app.bot)
            
            if update:
                await self.bot_app.process_update(update)
                self._request_count += 1
                self._last_request_time = datetime.now(UTC)
            
            return web.Response(status=200)
        except Exception as e:
            logger.error(f"Webhook processing error: {e}")
            return web.Response(status=500)
    
    async def _handle_health(self, request: web.Request) -> web.Response:
        """Handle health check requests."""
        uptime = None
        if self._start_time:
            uptime = (datetime.now(UTC) - self._start_time).total_seconds()
        
        health_data: dict[str, Any] = {
            "status": "healthy" if self._running else "unhealthy",
            "timestamp": datetime.now(UTC).isoformat(),
            "uptime_seconds": uptime,
            "request_count": self._request_count,
            "last_request": (
                self._last_request_time.isoformat()
                if self._last_request_time
                else None
            ),
        }
        
        return web.json_response(health_data)
    
    async def _handle_root(self, request: web.Request) -> web.Response:
        """Handle root path requests."""
        return web.Response(text="DMarket Bot Webhook Server")
    
    @property
    def is_running(self) -> bool:
        """Check if webhook server is running."""
        return self._running


class WebhookFailover:
    """Manage failover between polling and webhook modes."""
    
    def __init__(
        self,
        bot_app: Application,
        webhook_url: str,
        webhook_handler: WebhookHandler,
        health_check_interval: int = 30,
    ):
        """Initialize failover manager.
        
        Args:
            bot_app: Telegram Application instance
            webhook_url: Public URL for webhook
            webhook_handler: WebhookHandler instance
            health_check_interval: Seconds between health checks
        """
        self.bot_app = bot_app
        self.webhook_url = webhook_url
        self.webhook_handler = webhook_handler
        self.health_check_interval = health_check_interval
        
        self._mode: str = "polling"  # "polling" or "webhook"
        self._failover_task: asyncio.Task | None = None
        self._running = False
    
    async def start_with_failover(self) -> None:
        """Start bot with automatic failover capability."""
        self._running = True
        
        # Try webhook first
        if await self._try_webhook_mode():
            self._mode = "webhook"
            logger.info("Started in webhook mode")
        else:
            # Fallback to polling
            await self._start_polling_mode()
            self._mode = "polling"
            logger.info("Started in polling mode (webhook unavailable)")
        
        # Start failover monitoring
        self._failover_task = asyncio.create_task(self._failover_loop())
    
    async def stop(self) -> None:
        """Stop bot and failover monitoring."""
        self._running = False
        
        if self._failover_task:
            self._failover_task.cancel()
            try:
                await self._failover_task
            except asyncio.CancelledError:
                pass
        
        if self._mode == "webhook":
            await self.webhook_handler.stop()
            await self.bot_app.bot.delete_webhook()
        else:
            if self.bot_app.updater.running:
                await self.bot_app.updater.stop()
    
    async def _try_webhook_mode(self) -> bool:
        """Try to set up webhook mode.
        
        Returns:
            True if webhook setup successful
        """
        try:
            await self.webhook_handler.start()
            
            # Set webhook
            success = await self.bot_app.bot.set_webhook(
                url=f"{self.webhook_url}{self.webhook_handler.webhook_path}",
                allowed_updates=["message", "callback_query", "inline_query"],
            )
            
            if success:
                return True
            
            # Cleanup on failure
            await self.webhook_handler.stop()
            return False
        except Exception as e:
            logger.error(f"Failed to setup webhook: {e}")
            if self.webhook_handler.is_running:
                await self.webhook_handler.stop()
            return False
    
    async def _start_polling_mode(self) -> None:
        """Start polling mode."""
        # Delete any existing webhook
        await self.bot_app.bot.delete_webhook()
        
        # Start polling
        await self.bot_app.start()
        await self.bot_app.updater.start_polling()
    
    async def _failover_loop(self) -> None:
        """Monitor health and perform failover if needed."""
        consecutive_failures = 0
        failure_threshold = 3
        
        while self._running:
            try:
                await asyncio.sleep(self.health_check_interval)
                
                if self._mode == "webhook":
                    # Check webhook health
                    if not self.webhook_handler.is_running:
                        consecutive_failures += 1
                        logger.warning(
                            f"Webhook unhealthy ({consecutive_failures}/{failure_threshold})",
                        )
                        
                        if consecutive_failures >= failure_threshold:
                            logger.error("Webhook failed, switching to polling")
                            await self._switch_to_polling()
                            consecutive_failures = 0
                    else:
                        consecutive_failures = 0
                else:
                    # In polling mode, try to switch back to webhook periodically
                    if await self._try_webhook_mode():
                        logger.info("Webhook recovered, switching from polling")
                        await self._switch_to_webhook()
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in failover loop: {e}")
    
    async def _switch_to_polling(self) -> None:
        """Switch from webhook to polling mode."""
        await self.webhook_handler.stop()
        await self.bot_app.bot.delete_webhook()
        await self._start_polling_mode()
        self._mode = "polling"
        logger.info("Switched to polling mode")
    
    async def _switch_to_webhook(self) -> None:
        """Switch from polling to webhook mode."""
        if self.bot_app.updater.running:
            await self.bot_app.updater.stop()
        
        # Webhook handler already started in _try_webhook_mode
        self._mode = "webhook"
        logger.info("Switched to webhook mode")
    
    @property
    def current_mode(self) -> str:
        """Get current operating mode."""
        return self._mode
```

---

### Шаг 3: Graceful Shutdown (⏱️ 3 часа)

#### 3.1 Улучшить shutdown в main.py

**Файл**: `src/main.py` (модификация)

Добавить улучшенную логику graceful shutdown:

```python
# Добавить импорты:
import signal
import functools
from typing import Set
from src.utils.health_monitor import HealthMonitor

# Добавить в класс Application:

class Application:
    """Main application class for DMarket Bot."""
    
    def __init__(self, config_path: str | None = None) -> None:
        # ... existing code ...
        self.health_monitor: HealthMonitor | None = None
        self._pending_tasks: Set[asyncio.Task] = set()
        self._shutdown_timeout = 30  # seconds
    
    async def shutdown(self) -> None:
        """Gracefully shutdown the application."""
        logger.info("Starting graceful shutdown...")
        shutdown_start = datetime.now(UTC)
        
        try:
            # 1. Stop accepting new requests
            logger.info("Stopping health monitor...")
            if self.health_monitor:
                await self.health_monitor.stop_heartbeat()
            
            # 2. Stop Daily Report Scheduler
            if self.daily_report_scheduler:
                logger.info("Stopping Daily Report Scheduler...")
                await self.daily_report_scheduler.stop()
            
            # 3. Save current state
            logger.info("Saving application state...")
            await self._save_shutdown_state()
            
            # 4. Wait for pending tasks with timeout
            if self._pending_tasks:
                logger.info(f"Waiting for {len(self._pending_tasks)} pending tasks...")
                try:
                    await asyncio.wait_for(
                        self._wait_for_pending_tasks(),
                        timeout=self._shutdown_timeout / 2,
                    )
                except asyncio.TimeoutError:
                    logger.warning("Timeout waiting for pending tasks, cancelling...")
                    await self._cancel_pending_tasks()
            
            # 5. Stop the bot
            if self.bot:
                logger.info("Stopping Telegram Bot...")
                if self.bot.updater and self.bot.updater.running:
                    await self.bot.updater.stop()
                if self.bot.running:
                    await self.bot.stop()
                await self.bot.shutdown()
                logger.info("Telegram Bot stopped")
            
            # 6. Close DMarket API connections
            if self.dmarket_api:
                logger.info("Closing DMarket API connections...")
                await self.dmarket_api._close_client()
                logger.info("DMarket API connections closed")
            
            # 7. Close database connections
            if self.database:
                logger.info("Closing database connections...")
                await self.database.close()
                logger.info("Database connections closed")
            
            shutdown_duration = (datetime.now(UTC) - shutdown_start).total_seconds()
            logger.info(f"Application shutdown complete in {shutdown_duration:.2f}s")
            
        except Exception as e:
            logger.exception(f"Error during shutdown: {e}")
    
    async def _save_shutdown_state(self) -> None:
        """Save application state before shutdown."""
        if self.state_manager:
            try:
                # Mark all active checkpoints as interrupted
                # This will be handled by StateManager's registered handlers
                logger.info("Saving state manager state...")
            except Exception as e:
                logger.error(f"Failed to save state: {e}")
    
    async def _wait_for_pending_tasks(self) -> None:
        """Wait for all pending tasks to complete."""
        if self._pending_tasks:
            await asyncio.gather(*self._pending_tasks, return_exceptions=True)
    
    async def _cancel_pending_tasks(self) -> None:
        """Cancel all pending tasks."""
        for task in self._pending_tasks:
            task.cancel()
        
        await asyncio.gather(*self._pending_tasks, return_exceptions=True)
        self._pending_tasks.clear()
    
    def track_task(self, task: asyncio.Task) -> None:
        """Track a task for graceful shutdown.
        
        Args:
            task: Task to track
        """
        self._pending_tasks.add(task)
        task.add_done_callback(self._pending_tasks.discard)
    
    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""
        loop = asyncio.get_event_loop()
        
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(
                sig,
                functools.partial(self._handle_signal, sig),
            )
        
        # Windows doesn't have SIGQUIT
        if hasattr(signal, "SIGQUIT"):
            loop.add_signal_handler(
                signal.SIGQUIT,
                functools.partial(self._handle_signal, signal.SIGQUIT),
            )
        
        logger.info("Signal handlers registered")
    
    def _handle_signal(self, sig: signal.Signals) -> None:
        """Handle shutdown signal.
        
        Args:
            sig: Received signal
        """
        logger.info(f"Received signal {sig.name}, initiating shutdown...")
        self._shutdown_event.set()
```

---

### Шаг 4: Database Backups (⏱️ 3 часа)

#### 4.1 Создать скрипт резервного копирования

**Файл**: `scripts/backup_database.py`

```python
"""Database backup and restore utilities for DMarket Bot.

Supports:
- SQLite database backup
- PostgreSQL database backup (via pg_dump)
- Scheduled automatic backups
- Backup rotation (keep last N backups)
- Compression (gzip)
"""

import argparse
import asyncio
import gzip
import logging
import os
import shutil
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.config import Config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class DatabaseBackup:
    """Handle database backup operations."""
    
    def __init__(
        self,
        database_url: str,
        backup_dir: str | Path = "backups",
        keep_last_n: int = 7,
        compress: bool = True,
    ):
        """Initialize backup handler.
        
        Args:
            database_url: Database connection URL
            backup_dir: Directory for backup files
            keep_last_n: Number of backups to keep
            compress: Whether to compress backups
        """
        self.database_url = database_url
        self.backup_dir = Path(backup_dir)
        self.keep_last_n = keep_last_n
        self.compress = compress
        
        # Create backup directory
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Determine database type
        self.db_type = self._detect_db_type()
    
    def _detect_db_type(self) -> str:
        """Detect database type from URL."""
        if "sqlite" in self.database_url:
            return "sqlite"
        elif "postgresql" in self.database_url:
            return "postgresql"
        else:
            raise ValueError(f"Unsupported database type: {self.database_url}")
    
    def _get_backup_filename(self) -> str:
        """Generate backup filename with timestamp."""
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        ext = ".sql.gz" if self.compress else ".sql"
        return f"dmarket_bot_{self.db_type}_{timestamp}{ext}"
    
    def _get_sqlite_path(self) -> Path:
        """Extract SQLite file path from URL."""
        # Handle: sqlite:///path/to/db.sqlite or sqlite+aiosqlite:///...
        url = self.database_url
        for prefix in ["sqlite+aiosqlite:///", "sqlite:///"]:
            if url.startswith(prefix):
                return Path(url[len(prefix):])
        raise ValueError(f"Cannot extract SQLite path from: {url}")
    
    async def backup(self) -> Path:
        """Create database backup.
        
        Returns:
            Path to backup file
        """
        logger.info(f"Starting {self.db_type} database backup...")
        
        if self.db_type == "sqlite":
            backup_path = await self._backup_sqlite()
        elif self.db_type == "postgresql":
            backup_path = await self._backup_postgresql()
        else:
            raise ValueError(f"Unsupported database type: {self.db_type}")
        
        logger.info(f"Backup created: {backup_path}")
        
        # Rotate old backups
        await self._rotate_backups()
        
        return backup_path
    
    async def _backup_sqlite(self) -> Path:
        """Backup SQLite database."""
        sqlite_path = self._get_sqlite_path()
        
        if not sqlite_path.exists():
            raise FileNotFoundError(f"SQLite database not found: {sqlite_path}")
        
        backup_filename = self._get_backup_filename().replace(".sql", ".db")
        backup_path = self.backup_dir / backup_filename
        
        # Use VACUUM INTO for clean backup (SQLite 3.27+)
        # Or simple copy for older versions
        try:
            import sqlite3
            
            conn = sqlite3.connect(str(sqlite_path))
            
            # Create backup using VACUUM INTO (atomic, consistent)
            if sqlite3.sqlite_version_info >= (3, 27, 0):
                backup_raw = str(backup_path).replace(".gz", "") if self.compress else str(backup_path)
                conn.execute(f"VACUUM INTO '{backup_raw}'")
                conn.close()
                
                if self.compress:
                    # Compress the backup
                    with open(backup_raw, 'rb') as f_in:
                        with gzip.open(backup_path, 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    os.remove(backup_raw)
            else:
                # Fallback: simple file copy
                conn.close()
                if self.compress:
                    with open(sqlite_path, 'rb') as f_in:
                        with gzip.open(backup_path, 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                else:
                    shutil.copy2(sqlite_path, backup_path)
                    
        except Exception as e:
            logger.error(f"SQLite backup failed: {e}")
            raise
        
        return backup_path
    
    async def _backup_postgresql(self) -> Path:
        """Backup PostgreSQL database using pg_dump."""
        backup_filename = self._get_backup_filename()
        backup_path = self.backup_dir / backup_filename
        
        # Parse PostgreSQL URL
        # postgresql://user:password@host:port/database
        import urllib.parse
        
        parsed = urllib.parse.urlparse(self.database_url)
        
        env = os.environ.copy()
        if parsed.password:
            env["PGPASSWORD"] = parsed.password
        
        cmd = [
            "pg_dump",
            "-h", parsed.hostname or "localhost",
            "-p", str(parsed.port or 5432),
            "-U", parsed.username or "postgres",
            "-d", parsed.path.lstrip("/"),
            "-F", "c",  # Custom format (compressed)
        ]
        
        try:
            if self.compress:
                # pg_dump with custom format is already compressed
                backup_path = backup_path.with_suffix("")  # Remove .gz
                
            with open(backup_path, 'wb') as f:
                result = subprocess.run(
                    cmd,
                    stdout=f,
                    stderr=subprocess.PIPE,
                    env=env,
                    check=True,
                )
                
        except subprocess.CalledProcessError as e:
            logger.error(f"pg_dump failed: {e.stderr.decode()}")
            raise
        except FileNotFoundError:
            logger.error("pg_dump not found. Install PostgreSQL client tools.")
            raise
        
        return backup_path
    
    async def restore(self, backup_path: str | Path) -> None:
        """Restore database from backup.
        
        Args:
            backup_path: Path to backup file
        """
        backup_path = Path(backup_path)
        
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_path}")
        
        logger.info(f"Restoring from {backup_path}...")
        
        if self.db_type == "sqlite":
            await self._restore_sqlite(backup_path)
        elif self.db_type == "postgresql":
            await self._restore_postgresql(backup_path)
        
        logger.info("Database restored successfully")
    
    async def _restore_sqlite(self, backup_path: Path) -> None:
        """Restore SQLite database from backup."""
        sqlite_path = self._get_sqlite_path()
        
        # Decompress if needed
        if backup_path.suffix == ".gz":
            with gzip.open(backup_path, 'rb') as f_in:
                with open(sqlite_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
        else:
            shutil.copy2(backup_path, sqlite_path)
    
    async def _restore_postgresql(self, backup_path: Path) -> None:
        """Restore PostgreSQL database from backup."""
        import urllib.parse
        
        parsed = urllib.parse.urlparse(self.database_url)
        
        env = os.environ.copy()
        if parsed.password:
            env["PGPASSWORD"] = parsed.password
        
        cmd = [
            "pg_restore",
            "-h", parsed.hostname or "localhost",
            "-p", str(parsed.port or 5432),
            "-U", parsed.username or "postgres",
            "-d", parsed.path.lstrip("/"),
            "-c",  # Clean (drop) database objects before recreating
            str(backup_path),
        ]
        
        try:
            subprocess.run(
                cmd,
                stderr=subprocess.PIPE,
                env=env,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            logger.error(f"pg_restore failed: {e.stderr.decode()}")
            raise
    
    async def _rotate_backups(self) -> None:
        """Remove old backups, keeping only the last N."""
        backups = sorted(
            self.backup_dir.glob(f"dmarket_bot_{self.db_type}_*"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        
        # Remove old backups
        for backup in backups[self.keep_last_n:]:
            logger.info(f"Removing old backup: {backup}")
            backup.unlink()
    
    def list_backups(self) -> list[dict[str, Any]]:
        """List available backups.
        
        Returns:
            List of backup info dictionaries
        """
        backups = []
        
        for backup_file in self.backup_dir.glob(f"dmarket_bot_{self.db_type}_*"):
            stat = backup_file.stat()
            backups.append({
                "filename": backup_file.name,
                "path": str(backup_file),
                "size_mb": stat.st_size / (1024 * 1024),
                "created_at": datetime.fromtimestamp(stat.st_mtime, tz=UTC),
            })
        
        return sorted(backups, key=lambda x: x["created_at"], reverse=True)


async def main() -> int:
    """Main entry point for backup script."""
    parser = argparse.ArgumentParser(description="DMarket Bot Database Backup")
    parser.add_argument(
        "action",
        choices=["backup", "restore", "list"],
        help="Action to perform",
    )
    parser.add_argument(
        "--backup-file",
        type=str,
        help="Backup file path (for restore)",
    )
    parser.add_argument(
        "--backup-dir",
        type=str,
        default="backups",
        help="Directory for backups",
    )
    parser.add_argument(
        "--keep",
        type=int,
        default=7,
        help="Number of backups to keep",
    )
    parser.add_argument(
        "--no-compress",
        action="store_true",
        help="Don't compress backups",
    )
    
    args = parser.parse_args()
    
    try:
        config = Config.load()
        config.validate()
        
        backup_handler = DatabaseBackup(
            database_url=config.database.url,
            backup_dir=args.backup_dir,
            keep_last_n=args.keep,
            compress=not args.no_compress,
        )
        
        if args.action == "backup":
            backup_path = await backup_handler.backup()
            print(f"✅ Backup created: {backup_path}")
            return 0
            
        elif args.action == "restore":
            if not args.backup_file:
                print("❌ --backup-file required for restore")
                return 1
            await backup_handler.restore(args.backup_file)
            print("✅ Database restored")
            return 0
            
        elif args.action == "list":
            backups = backup_handler.list_backups()
            if not backups:
                print("No backups found")
            else:
                print(f"Found {len(backups)} backup(s):")
                for b in backups:
                    print(f"  - {b['filename']} ({b['size_mb']:.2f} MB, {b['created_at']})")
            return 0
            
    except Exception as e:
        logger.error(f"Backup operation failed: {e}")
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
```

#### 4.2 Создать cron для бэкапов

**Файл**: `scripts/deployment/cron/backup.cron`

```cron
# Daily backup at 3:00 AM UTC
0 3 * * * cd /app && python scripts/backup_database.py backup >> /var/log/dmarket-bot/backup.log 2>&1
```

---

## 🧪 Тестирование

### Unit тесты

- [ ] `tests/utils/test_health_monitor.py::test_health_monitor_check_database`
- [ ] `tests/utils/test_health_monitor.py::test_health_monitor_check_redis`
- [ ] `tests/utils/test_health_monitor.py::test_health_monitor_check_dmarket_api`
- [ ] `tests/utils/test_health_monitor.py::test_health_monitor_check_telegram_api`
- [ ] `tests/utils/test_health_monitor.py::test_health_monitor_heartbeat_loop`
- [ ] `tests/utils/test_health_monitor.py::test_health_monitor_alert_callbacks`
- [ ] `tests/telegram_bot/test_webhook_handler.py::test_webhook_handler_health_endpoint`
- [ ] `tests/telegram_bot/test_webhook_handler.py::test_webhook_failover`
- [ ] `tests/scripts/test_backup_database.py::test_sqlite_backup`
- [ ] `tests/scripts/test_backup_database.py::test_backup_rotation`

### Integration тесты

- [ ] `tests/integration/test_graceful_shutdown.py::test_shutdown_saves_state`
- [ ] `tests/integration/test_graceful_shutdown.py::test_shutdown_closes_connections`
- [ ] `tests/integration/test_webhook_failover.py::test_failover_polling_to_webhook`

### Ручная проверка

- [ ] Запустить `python scripts/health_check.py --cron --json`
- [ ] Проверить webhook endpoint `/health`
- [ ] Протестировать SIGTERM graceful shutdown
- [ ] Создать и восстановить backup

---

## ✅ Критерии завершения

1. ✅ Health checks доступны через `scripts/health_check.py --cron`
2. ✅ Heartbeat мониторинг работает с интервалом 30 секунд
3. ✅ Alerts отправляются при failure_threshold (3 consecutive failures)
4. ✅ Webhook endpoint `/health` возвращает JSON статус
5. ✅ Graceful shutdown корректно завершает pending requests
6. ✅ SIGTERM/SIGINT корректно обрабатываются
7. ✅ Database backup создается и ротируется
8. ✅ Restore из backup работает
9. ✅ Все тесты проходят
10. ✅ MyPy/Ruff без новых ошибок
11. ✅ Документация обновлена

---

## 📁 Итоговый список файлов

### Новые файлы

| Файл | Строки | Описание |
|------|--------|----------|
| `src/utils/health_monitor.py` | ~350 | Health monitoring и heartbeat |
| `src/telegram_bot/webhook_handler.py` | ~300 | Webhook handler и failover |
| `scripts/backup_database.py` | ~350 | Backup/restore утилиты |
| `scripts/deployment/cron/health_check.cron` | ~5 | Cron для health checks |
| `scripts/deployment/cron/backup.cron` | ~3 | Cron для backups |
| `tests/utils/test_health_monitor.py` | ~200 | Тесты health monitor |
| `tests/telegram_bot/test_webhook_handler.py` | ~150 | Тесты webhook |
| `tests/scripts/test_backup_database.py` | ~150 | Тесты backup |
| `docs/MONITORING_GUIDE.md` | ~200 | Документация мониторинга |

### Модифицированные файлы

| Файл | Изменения |
|------|-----------|
| `scripts/health_check.py` | +50 строк (cron mode, JSON output) |
| `src/main.py` | +80 строк (improved graceful shutdown) |
| `config/config.yaml` | +20 строк (monitoring settings) |

---

## 📚 Ссылки

- [ROADMAP.md#P1-14](../ROADMAP.md) - Исходное описание задачи
- [Telegram Bot API - Webhooks](https://core.telegram.org/bots/api#setwebhook)
- [SQLite Backup API](https://www.sqlite.org/backup.html)
- [PostgreSQL pg_dump](https://www.postgresql.org/docs/current/app-pgdump.html)
- [APScheduler Documentation](https://apscheduler.readthedocs.io/)

---

**Версия плана**: 1.0
**Автор**: GitHub Copilot
**Дата**: 11 декабря 2025 г.
