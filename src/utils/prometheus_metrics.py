"""Prometheus metrics для мониторинга DMarket Bot.

Этот модуль предоставляет /metrics endpoint для Prometheus с метриками:
- Счетчики команд бота
- Latency API запросов
- Состояние базы данных
- Активные пользователи
"""

import time

from prometheus_client import Counter, Gauge, Histogram, Info, generate_latest, make_asgi_app


# =============================================================================
# Bot Metrics
# =============================================================================

# Счетчик команд бота
bot_commands_total = Counter(
    "bot_commands_total",
    "Total number of bot commands executed",
    ["command", "status"],
)

# Счетчик ошибок бота
bot_errors_total = Counter(
    "bot_errors_total",
    "Total number of bot errors",
    ["error_type"],
)

# Активные пользователи
bot_active_users = Gauge(
    "bot_active_users",
    "Number of active bot users",
)

# =============================================================================
# API Metrics
# =============================================================================

# HTTP запросы к DMarket API
api_requests_total = Counter(
    "dmarket_api_requests_total",
    "Total number of DMarket API requests",
    ["endpoint", "method", "status_code"],
)

# Latency API запросов
api_request_duration = Histogram(
    "dmarket_api_request_duration_seconds",
    "DMarket API request latency in seconds",
    ["endpoint", "method"],
    buckets=(0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0),
)

# Ошибки API
api_errors_total = Counter(
    "dmarket_api_errors_total",
    "Total number of DMarket API errors",
    ["endpoint", "error_type"],
)

# =============================================================================
# Database Metrics
# =============================================================================

# Размер connection pool
db_connections_active = Gauge(
    "db_connections_active",
    "Number of active database connections",
)

# Время выполнения запросов
db_query_duration = Histogram(
    "db_query_duration_seconds",
    "Database query latency in seconds",
    ["query_type"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0),
)

# Ошибки БД
db_errors_total = Counter(
    "db_errors_total",
    "Total number of database errors",
    ["error_type"],
)

# =============================================================================
# Arbitrage Metrics
# =============================================================================

# Найденные возможности арбитража
arbitrage_opportunities_found = Counter(
    "arbitrage_opportunities_found_total",
    "Total number of arbitrage opportunities found",
    ["game", "level"],
)

# Среднее количество возможностей
arbitrage_opportunities_avg = Gauge(
    "arbitrage_opportunities_avg",
    "Average number of arbitrage opportunities per scan",
    ["game"],
)

# Средняя прибыль
arbitrage_profit_avg = Gauge(
    "arbitrage_profit_avg_usd",
    "Average profit per arbitrage opportunity in USD",
    ["game"],
)

# =============================================================================
# Target Metrics
# =============================================================================

# Созданные таргеты
targets_created_total = Counter(
    "targets_created_total",
    "Total number of targets created",
    ["game"],
)

# Исполненные таргеты
targets_executed_total = Counter(
    "targets_executed_total",
    "Total number of targets executed",
    ["game"],
)

# Активные таргеты
targets_active = Gauge(
    "targets_active",
    "Number of currently active targets",
    ["game"],
)

# =============================================================================
# Business Metrics
# =============================================================================

# Общая прибыль
total_profit_usd = Gauge(
    "total_profit_usd",
    "Total profit in USD",
)

# Транзакции
# Labels: type (buy/sell), status (success/failed)
transactions_total = Counter(
    "transactions_total",
    "Total number of transactions",
    ["type", "status"],
)

# Средняя сумма транзакции
transaction_amount_avg = Gauge(
    "transaction_amount_avg_usd",
    "Average transaction amount in USD",
    ["type"],
)

# =============================================================================
# System Metrics
# =============================================================================

# Информация о версии
app_info = Info(
    "app",
    "Application information",
)

# Uptime
app_uptime_seconds = Gauge(
    "app_uptime_seconds",
    "Application uptime in seconds",
)

# =============================================================================
# Utility Functions
# =============================================================================


def track_command(command: str, success: bool = True) -> None:
    """Track bot command execution.

    Args:
        command: Command name (e.g., 'start', 'arbitrage')
        success: Whether command succeeded
    """
    status = "success" if success else "failed"
    bot_commands_total.labels(command=command, status=status).inc()


def track_api_request(
    endpoint: str,
    method: str,
    status_code: int,
    duration: float,
) -> None:
    """Track API request.

    Args:
        endpoint: API endpoint path
        method: HTTP method (GET, POST, etc.)
        status_code: Response status code
        duration: Request duration in seconds
    """
    api_requests_total.labels(
        endpoint=endpoint,
        method=method,
        status_code=status_code,
    ).inc()

    api_request_duration.labels(endpoint=endpoint, method=method).observe(duration)


def track_db_query(query_type: str, duration: float) -> None:
    """Track database query.

    Args:
        query_type: Type of query (SELECT, INSERT, UPDATE, DELETE)
        duration: Query duration in seconds
    """
    db_query_duration.labels(query_type=query_type).observe(duration)


def track_arbitrage_scan(game: str, level: str, opportunities_count: int) -> None:
    """Track arbitrage scan results.

    Args:
        game: Game identifier
        level: Arbitrage level
        opportunities_count: Number of opportunities found
    """
    arbitrage_opportunities_found.labels(game=game, level=level).inc(opportunities_count)


def set_active_users(count: int) -> None:
    """Set number of active users.

    Args:
        count: Number of active users
    """
    bot_active_users.set(count)


def get_metrics() -> bytes:
    """Get Prometheus metrics in text format.

    Returns:
        Metrics in Prometheus text format
    """
    return generate_latest()


def create_metrics_app():
    """Create ASGI app for Prometheus metrics endpoint.

    Returns:
        ASGI application serving /metrics
    """
    return make_asgi_app()


# =============================================================================
# Context Managers
# =============================================================================


class Timer:
    """Context manager for timing code blocks.

    Usage:
        with Timer() as t:
            # code to time
            pass
        print(f"Elapsed: {t.elapsed}s")
    """

    def __init__(self):
        self.start_time = None
        self.elapsed = None

    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.elapsed = time.perf_counter() - self.start_time
        return False
