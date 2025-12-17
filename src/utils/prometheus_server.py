"""HTTP сервер для экспорта Prometheus метрик."""

import asyncio
import os

from aiohttp import web
import structlog

from src.utils.prometheus_exporter import MetricsCollector


logger = structlog.get_logger(__name__)


# Security: Default to localhost. Use 0.0.0.0 only in Docker/container environments
DEFAULT_HOST = os.environ.get("PROMETHEUS_HOST", "127.0.0.1")


class PrometheusServer:
    """HTTP сервер для Prometheus метрик."""

    def __init__(self, port: int = 8000, host: str | None = None) -> None:
        """
        Инициализация сервера.

        Args:
            port: Порт для HTTP сервера
            host: Хост для привязки (по умолчанию 127.0.0.1 для безопасности,
                  используйте 0.0.0.0 в контейнерах)
        """
        self.port = port
        self.host = host or DEFAULT_HOST
        self.app = web.Application()
        self.runner: web.AppRunner | None = None
        self.site: web.TCPSite | None = None

        # Роуты
        self.app.router.add_get("/metrics", self.metrics_handler)
        self.app.router.add_get("/health", self.health_handler)

    async def metrics_handler(self, request: web.Request) -> web.Response:
        """Обработчик /metrics endpoint."""
        metrics = MetricsCollector.get_metrics()
        return web.Response(body=metrics, content_type="text/plain; charset=utf-8")

    async def health_handler(self, request: web.Request) -> web.Response:
        """Обработчик /health endpoint."""
        return web.json_response({"status": "ok"})

    async def start(self) -> None:
        """Запустить сервер."""
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()

        self.site = web.TCPSite(self.runner, self.host, self.port)
        await self.site.start()

        logger.info("prometheus_server_started", host=self.host, port=self.port)

    async def stop(self) -> None:
        """Остановить сервер."""
        if self.site:
            await self.site.stop()
        if self.runner:
            await self.runner.cleanup()

        logger.info("prometheus_server_stopped")


async def run_prometheus_server(port: int = 8000) -> None:
    """
    Запустить Prometheus сервер.

    Args:
        port: Порт для сервера
    """
    server = PrometheusServer(port)
    await server.start()

    try:
        # Держать сервер запущенным
        while True:
            await asyncio.sleep(3600)
    except asyncio.CancelledError:
        await server.stop()
