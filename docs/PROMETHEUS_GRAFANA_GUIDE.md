# Prometheus + Grafana Observability

## Обзор

Полная система мониторинга для DMarket Telegram Bot с использованием Prometheus и Grafana.

## Архитектура

```
Bot → Prometheus Exporter (port 8000) → Prometheus → Grafana
```

## Метрики

### Counters (счетчики)

- `dmarket_bot_commands_total` - Всего команд
- `dmarket_bot_api_requests_total` - Всего API запросов
- `dmarket_bot_errors_total` - Всего ошибок
- `dmarket_bot_arbitrage_scans_total` - Сканирований арбитража
- `dmarket_bot_targets_created_total` - Создано таргетов
- `dmarket_bot_trades_total` - Всего сделок

### Gauges (текущее значение)

- `dmarket_bot_active_users` - Активных пользователей
- `dmarket_bot_active_targets` - Активных таргетов
- `dmarket_bot_balance_usd` - Баланс USD
- `dmarket_bot_cache_size` - Размер кэша

### Histograms (распределения)

- `dmarket_bot_api_request_duration_seconds` - Длительность API запросов
- `dmarket_bot_arbitrage_scan_duration_seconds` - Длительность сканирования

## Установка

### 1. Docker Compose

```yaml
# docker-compose.monitoring.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./config/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    volumes:
      - grafana_data:/var/lib/grafana
      - ./config/grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./config/grafana/datasources:/etc/grafana/provisioning/datasources
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false

volumes:
  prometheus_data:
  grafana_data:
```

### 2. Prometheus конфигурация

```yaml
# config/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'dmarket-bot'
    static_configs:
      - targets: ['bot:8000']
    metrics_path: '/metrics'
```

### 3. Запуск

```bash
# Запустить мониторинг
docker-compose -f docker-compose.monitoring.yml up -d

# Проверить статус
docker-compose -f docker-compose.monitoring.yml ps
```

## Использование

### В коде

```python
from src.utils.prometheus_exporter import MetricsCollector

# Записать команду
MetricsCollector.record_command("/start", user_id=123456)

# Записать API запрос
MetricsCollector.record_api_request(
    endpoint="/market/items",
    method="GET",
    status=200,
    duration=0.5
)

# Записать сканирование арбитража
MetricsCollector.record_arbitrage_scan(
    level="standard",
    game="csgo",
    duration=2.5,
    found=15
)

# Обновить активных пользователей
MetricsCollector.update_active_users(1250)
```

### Запуск metrics сервера

```python
# В main.py
from src.utils.prometheus_server import run_prometheus_server
import asyncio

async def main():
    # Запустить Prometheus сервер
    asyncio.create_task(run_prometheus_server(port=8000))

    # Запустить бота
    await bot.start()
```

## Grafana Дашборды

### Dashboard 1: Общая статистика

**Панели:**
- Активные пользователи (gauge)
- Команд за час (graph)
- API запросов за час (graph)
- Ошибок за час (graph)
- Top 10 команд (table)

**JSON:**
```json
{
  "panels": [
    {
      "title": "Active Users",
      "targets": [{
        "expr": "dmarket_bot_active_users"
      }],
      "type": "stat"
    },
    {
      "title": "Commands per hour",
      "targets": [{
        "expr": "rate(dmarket_bot_commands_total[1h])"
      }],
      "type": "graph"
    }
  ]
}
```

### Dashboard 2: Арбитраж

**Панели:**
- Сканирований за день по уровням (graph)
- Найдено возможностей (graph)
- Средняя длительность сканирования (gauge)
- Распределение по играм (pie chart)

### Dashboard 3: API Performance

**Панели:**
- Запросы в секунду (graph)
- P50/P95/P99 latency (graph)
- Ошибки по эндпоинтам (heatmap)
- Rate limit статус (gauge)

## Алерты

### Prometheus Alertmanager

```yaml
# config/alertmanager.yml
groups:
  - name: dmarket_bot
    interval: 1m
    rules:
      - alert: HighErrorRate
        expr: rate(dmarket_bot_errors_total[5m]) > 10
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"

      - alert: SlowAPIRequests
        expr: histogram_quantile(0.95, dmarket_bot_api_request_duration_seconds) > 5
        labels:
          severity: warning
        annotations:
          summary: "API requests are slow"

      - alert: LowActiveUsers
        expr: dmarket_bot_active_users < 100
        for: 1h
        labels:
          severity: info
        annotations:
          summary: "Low active users"
```

## Endpoints

- **Метрики**: http://localhost:8000/metrics
- **Health**: http://localhost:8000/health
- **Prometheus UI**: http://localhost:9090
- **Grafana UI**: http://localhost:3000 (admin/admin)

## Grafana Datasource

```yaml
# config/grafana/datasources/prometheus.yml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
```

## Best Practices

1. **Не экспортируйте high-cardinality лейблы** (user_id только для критичных метрик)
2. **Используйте counters для событий**, gauges для состояний
3. **Добавляйте unit в названия** (_seconds, _bytes, _total)
4. **Группируйте связанные метрики** одним префиксом
5. **Документируйте метрики** в коде

## Troubleshooting

### Метрики не появляются

```bash
# Проверить metrics endpoint
curl http://localhost:8000/metrics

# Проверить Prometheus targets
# http://localhost:9090/targets
```

### Grafana не подключается

```bash
# Проверить datasource
docker-compose logs grafana

# Проверить сеть
docker network ls
docker network inspect <network_name>
```

## Дополнительные ресурсы

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Dashboards](https://grafana.com/grafana/dashboards/)
- [Best Practices](https://prometheus.io/docs/practices/naming/)
