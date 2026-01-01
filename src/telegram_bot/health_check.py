"""Health check HTTP server for bot monitoring.

Best practice for production deployments - allows external monitoring
and load balancers to check if bot is alive.
"""

import json
import logging
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from typing import Any

logger = logging.getLogger(__name__)


class HealthCheckHandler(BaseHTTPRequestHandler):
    """HTTP handler for health check requests."""

    bot_status: dict[str, Any] = {
        "status": "starting",
        "start_time": None,
        "last_update_time": None,
        "total_updates": 0,
        "errors": 0,
    }

    def do_GET(self) -> None:  # noqa: N802
        """Handle GET requests."""
        if self.path == "/health":
            self._handle_health()
        elif self.path == "/metrics":
            self._handle_metrics()
        elif self.path == "/ready":
            self._handle_ready()
        else:
            self.send_error(404, "Not Found")

    def _handle_health(self) -> None:
        """Handle /health endpoint."""
        status_code = 200 if self.bot_status["status"] == "running" else 503

        response = {
            "status": self.bot_status["status"],
            "uptime_seconds": self._get_uptime(),
        }

        self._send_json_response(response, status_code)

    def _handle_ready(self) -> None:
        """Handle /ready endpoint (Kubernetes readiness probe)."""
        is_ready = self.bot_status["status"] == "running"
        status_code = 200 if is_ready else 503

        response = {
            "ready": is_ready,
        }

        self._send_json_response(response, status_code)

    def _handle_metrics(self) -> None:
        """Handle /metrics endpoint."""
        response = {
            **self.bot_status,
            "uptime_seconds": self._get_uptime(),
            "error_rate": (
                self.bot_status["errors"] / self.bot_status["total_updates"]
                if self.bot_status["total_updates"] > 0
                else 0
            ),
        }

        self._send_json_response(response, 200)

    def _get_uptime(self) -> float | None:
        """Get bot uptime in seconds."""
        if not self.bot_status["start_time"]:
            return None
        start = datetime.fromisoformat(self.bot_status["start_time"])
        return (datetime.now() - start).total_seconds()

    def _send_json_response(self, data: dict[str, Any], status_code: int) -> None:
        """Send JSON response.

        Args:
            data: Response data
            status_code: HTTP status code
        """
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def log_message(self, format: str, *args: Any) -> None:
        """Override to use logger instead of stderr."""
        logger.debug(f"Health check: {format % args}")


class HealthCheckServer:
    """HTTP server for health checks."""

    def __init__(self, host: str = "0.0.0.0", port: int = 8080):
        """Initialize health check server.

        Args:
            host: Host to bind to
            port: Port to bind to
        """
        self.host = host
        self.port = port
        self.server: HTTPServer | None = None
        self.thread: Thread | None = None

    def start(self) -> None:
        """Start health check server in background thread."""
        try:
            self.server = HTTPServer((self.host, self.port), HealthCheckHandler)
            self.thread = Thread(target=self.server.serve_forever, daemon=True)
            self.thread.start()
            logger.info(f"Health check server started on {self.host}:{self.port}")
            logger.info(f"  - Health: http://{self.host}:{self.port}/health")
            logger.info(f"  - Ready:  http://{self.host}:{self.port}/ready")
            logger.info(f"  - Metrics: http://{self.host}:{self.port}/metrics")
        except Exception as e:
            logger.error(f"Failed to start health check server: {e}")

    def stop(self) -> None:
        """Stop health check server."""
        if self.server:
            logger.info("Stopping health check server...")
            self.server.shutdown()
            self.server.server_close()
            if self.thread:
                self.thread.join(timeout=5)
            logger.info("Health check server stopped")

    def update_status(
        self,
        status: str | None = None,
        last_update: bool = False,
        error: bool = False,
    ) -> None:
        """Update bot status.

        Args:
            status: New status ("starting", "running", "stopping", "error")
            last_update: Whether to update last_update_time
            error: Whether to increment error counter
        """
        if status:
            HealthCheckHandler.bot_status["status"] = status
            if status == "running" and not HealthCheckHandler.bot_status["start_time"]:
                HealthCheckHandler.bot_status["start_time"] = datetime.now().isoformat()

        if last_update:
            HealthCheckHandler.bot_status["last_update_time"] = datetime.now().isoformat()
            HealthCheckHandler.bot_status["total_updates"] += 1

        if error:
            HealthCheckHandler.bot_status["errors"] += 1


# Global health check server instance
health_check_server = HealthCheckServer()
