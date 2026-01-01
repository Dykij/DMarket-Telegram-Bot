"""Prometheus metrics for production monitoring."""

from prometheus_client import Counter, Gauge, Histogram, generate_latest

# Request counters
bot_requests_total = Counter(
    "bot_requests_total",
    "Total bot requests",
    ["command", "user_id", "status"],
)

# Response time histograms
bot_request_duration_seconds = Histogram(
    "bot_request_duration_seconds",
    "Bot request duration in seconds",
    ["command"],
)

# Active users gauge
bot_active_users = Gauge(
    "bot_active_users",
    "Number of active users in last 5 minutes",
)

# Error counters
bot_errors_total = Counter(
    "bot_errors_total",
    "Total bot errors",
    ["error_type", "command"],
)

# API call counters
dmarket_api_calls_total = Counter(
    "dmarket_api_calls_total",
    "Total DMarket API calls",
    ["endpoint", "status_code"],
)

# API response time
dmarket_api_duration_seconds = Histogram(
    "dmarket_api_duration_seconds",
    "DMarket API response time in seconds",
    ["endpoint"],
)

# Cache hits/misses
cache_operations_total = Counter(
    "cache_operations_total",
    "Total cache operations",
    ["operation", "result"],
)

# Database query time
database_query_duration_seconds = Histogram(
    "database_query_duration_seconds",
    "Database query duration in seconds",
    ["query_type"],
)

# Arbitrage opportunities found
arbitrage_opportunities_total = Counter(
    "arbitrage_opportunities_total",
    "Total arbitrage opportunities found",
    ["game", "level"],
)

# Targets created
targets_created_total = Counter(
    "targets_created_total",
    "Total targets created",
    ["game"],
)


def get_metrics() -> bytes:
    """Get Prometheus metrics in text format.

    Returns:
        Metrics in Prometheus exposition format
    """
    return generate_latest()
