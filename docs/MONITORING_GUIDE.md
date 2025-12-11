# 📊 Monitoring and Recovery Guide

**Version**: 1.0.0
**Last Updated**: December 11, 2025

---

## 📌 Overview

This guide covers the monitoring and recovery capabilities of the DMarket Bot, including:

- **Health Monitoring**: Continuous health checks for all critical services
- **Database Backups**: Automated backup and restore functionality
- **Graceful Shutdown**: Safe termination with state preservation
- **Alerting**: Configurable alerts on service failures

---

## 🔍 Health Monitoring

### Quick Start

```python
from src.utils.health_monitor import HealthMonitor, HeartbeatConfig

# Initialize monitor with services
monitor = HealthMonitor(
    database=db_manager,
    redis_cache=redis_cache,
    telegram_bot_token="your_token",
)

# Run single health check
results = await monitor.run_all_checks()

# Or start continuous monitoring
await monitor.start_heartbeat()
```

### Monitored Services

| Service | Check Method | Status Levels |
|---------|-------------|---------------|
| Database | `check_database()` | Healthy, Unhealthy |
| Redis | `check_redis()` | Healthy, Degraded (memory fallback), Unhealthy |
| DMarket API | `check_dmarket_api()` | Healthy, Degraded (rate limited), Unhealthy |
| Telegram API | `check_telegram_api()` | Healthy, Unhealthy |

### Status Levels

- **Healthy**: Service is fully operational
- **Degraded**: Service has reduced functionality but is operational
- **Unhealthy**: Service is not operational
- **Unknown**: Service not configured or status cannot be determined

### Alert Callbacks

Register callbacks to be notified on status changes:

```python
async def send_telegram_alert(result: HealthCheckResult):
    if result.status == ServiceStatus.UNHEALTHY:
        await bot.send_message(
            admin_chat_id,
            f"⚠️ Service Alert: {result.service} is {result.status.value}\n"
            f"Message: {result.message}"
        )

monitor.register_alert_callback(send_telegram_alert)
```

### Configuration

```python
from src.utils.health_monitor import HeartbeatConfig

config = HeartbeatConfig(
    interval_seconds=30,      # Check interval
    timeout_seconds=10,       # Request timeout
    failure_threshold=3,      # Failures before alert
    recovery_threshold=2,     # Successes before recovery alert
)
```

---

## 💾 Database Backups

### Command Line Usage

```bash
# Create backup
python scripts/backup_database.py backup

# List backups
python scripts/backup_database.py list

# Restore from backup
python scripts/backup_database.py restore --backup-file backups/dmarket_bot_sqlite_20251211.db.gz

# Custom options
python scripts/backup_database.py backup --backup-dir /path/to/backups --keep 14 --no-compress
```

### Programmatic Usage

```python
from scripts.backup_database import DatabaseBackup

backup_handler = DatabaseBackup(
    database_url="sqlite:///data/dmarket_bot.db",
    backup_dir="backups",
    keep_last_n=7,      # Keep last 7 backups
    compress=True,       # Use gzip compression
)

# Create backup
backup_path = await backup_handler.backup()

# Restore from backup
await backup_handler.restore("backups/dmarket_bot_sqlite_20251211.db.gz")

# List available backups
backups = backup_handler.list_backups()
```

### Features

- **SQLite Support**: VACUUM INTO for atomic backups
- **PostgreSQL Support**: pg_dump/pg_restore
- **Compression**: Gzip compression for smaller files
- **Rotation**: Automatic removal of old backups
- **Pre-restore Backup**: Creates backup before restore

### Scheduled Backups

Add to crontab for automated backups:

```cron
# Daily backup at 3:00 AM
0 3 * * * cd /app && python scripts/backup_database.py backup >> /var/log/backup.log 2>&1
```

---

## 🔧 Health Check Script

### Interactive Mode

```bash
python scripts/health_check.py
```

Output:
```
============================================================
DMarket Bot - Health Check
============================================================

🔍 Checking Telegram API...
  ✅ Telegram API accessible (@dmarket_bot)
🔍 Checking DMarket API...
  ✅ DMarket API accessible (Balance: $100.00)
🔍 Checking database...
  ✅ Database accessible (sqlite)
ℹ️  Redis not configured (optional)

============================================================
✅ All health checks passed!
============================================================
```

### Cron Mode

For use in monitoring scripts with exit codes:

```bash
python scripts/health_check.py --cron

# Exit codes:
# 0 - All healthy
# 1 - Degraded
# 2 - Unhealthy
```

### JSON Mode

For integration with monitoring systems:

```bash
python scripts/health_check.py --json
```

Output:
```json
{
  "overall_status": "healthy",
  "timestamp": "2025-12-11T23:00:00+00:00",
  "services": {
    "database": {
      "status": "healthy",
      "response_time_ms": 15.2,
      "message": "Database connection OK"
    }
  }
}
```

---

## 🚀 Graceful Shutdown

The bot handles shutdown signals properly:

- `SIGTERM`: Graceful shutdown (Docker/Kubernetes)
- `SIGINT`: Graceful shutdown (Ctrl+C)

### Shutdown Process

1. Stop accepting new requests
2. Stop health monitoring
3. Save application state
4. Wait for pending tasks (with timeout)
5. Cancel remaining tasks
6. Stop Telegram bot
7. Close API connections
8. Close database connections

---

## 📈 Best Practices

### Monitoring Setup

1. **Production**: Start heartbeat monitoring with 30s interval
2. **Development**: Use on-demand `run_all_checks()`
3. **CI/CD**: Use `--json` mode for integration tests

### Backup Strategy

1. **Daily Backups**: Keep 7-14 days of backups
2. **Before Migrations**: Always backup before database changes
3. **Off-site Storage**: Copy backups to external storage
4. **Test Restores**: Periodically test restore procedure

### Alert Configuration

1. **Failure Threshold**: 3 consecutive failures before alerting
2. **Recovery Threshold**: 2 consecutive successes before recovery alert
3. **Alert Channels**: Telegram for critical, logs for informational

---

## 📚 API Reference

### HealthMonitor

```python
class HealthMonitor:
    async def check_database() -> HealthCheckResult
    async def check_redis() -> HealthCheckResult
    async def check_dmarket_api() -> HealthCheckResult
    async def check_telegram_api() -> HealthCheckResult
    async def run_all_checks() -> dict[str, HealthCheckResult]
    async def start_heartbeat() -> None
    async def stop_heartbeat() -> None
    def get_overall_status() -> ServiceStatus
    def get_status_summary() -> dict[str, Any]
    def register_alert_callback(callback) -> None
```

### DatabaseBackup

```python
class DatabaseBackup:
    async def backup() -> Path
    async def restore(backup_path: Path) -> None
    def list_backups() -> list[dict]
```

---

## 🔗 Related Documentation

- [ROADMAP.md](../ROADMAP.md) - Task P1-14 details
- [P1_14_MONITORING_RECOVERY_PLAN.md](./P1_14_MONITORING_RECOVERY_PLAN.md) - Implementation plan
- [deployment.md](./deployment.md) - Deployment guide
