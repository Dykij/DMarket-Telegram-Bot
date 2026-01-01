# 🚀 Production Deployment Guide

Полное руководство по развертыванию DMarket Telegram Bot в production с мониторингом, масштабированием и высокой доступностью.

---

## 📋 Содержание

1. [Webhook vs Polling](#webhook-vs-polling)
2. [Мониторинг (Prometheus + Grafana)](#мониторинг)
3. [Kubernetes Deployment](#kubernetes-deployment)
4. [CI/CD Pipeline](#cicd-pipeline)
5. [Масштабирование](#масштабирование)

---

## 🔄 Webhook vs Polling

### Polling (по умолчанию)

**Преимущества:**
- ✅ Простая настройка
- ✅ Не требует публичного IP
- ✅ Работает за NAT/Firewall

**Недостатки:**
- ❌ Постоянные запросы к Telegram
- ❌ Больше нагрузки на API
- ❌ Сложнее масштабировать

**Использование:**
```bash
python -m src.main  # Polling режим по умолчанию
```

### Webhook (для production)

**Преимущества:**
- ✅ Telegram отправляет updates сам
- ✅ Меньше нагрузки на API
- ✅ Легко масштабировать
- ✅ Работает с load balancers

**Недостатки:**
- ❌ Требует публичный HTTPS URL
- ❌ Требует SSL сертификат
- ❌ Сложнее настройка

**Использование:**

1. Настроить переменные окружения:
```bash
export WEBHOOK_URL="https://bot.example.com"
export WEBHOOK_PORT="8443"
```

2. Запустить с webhook:
```python
from src.telegram_bot.webhook import WebhookConfig, start_webhook

config = WebhookConfig(
    url="https://bot.example.com",
    port=8443,
    url_path="telegram-webhook"
)

await start_webhook(application, config)
```

**SSL сертификат:**
```bash
# Self-signed (для тестирования)
openssl req -newkey rsa:2048 -sha256 -nodes \
  -keyout private.key -x509 -days 365 \
  -out cert.pem

# Production: используйте Let's Encrypt
certbot certonly --standalone -d bot.example.com
```

---

## 📊 Мониторинг (Prometheus + Grafana)

### Быстрый старт

```bash
# Запустить все сервисы (бот + мониторинг)
docker-compose -f docker-compose.monitoring.yml up -d

# Проверить статус
docker-compose -f docker-compose.monitoring.yml ps
```

**Доступ:**
- **Grafana:** http://localhost:3000 (admin/admin)
- **Prometheus:** http://localhost:9090
- **Bot Metrics:** http://localhost:8080/metrics

### Prometheus метрики

Бот экспортирует следующие метрики:

```
# Bot status
bot_status{status="running|starting|stopping|error"}

# Uptime
bot_uptime_seconds

# Updates
bot_total_updates
bot_updates_per_second

# Errors
bot_total_errors
bot_error_rate

# Commands
bot_command_count{command="/start|/balance|..."}
```

### Grafana Dashboard

1. Открыть Grafana: http://localhost:3000
2. Войти: admin/admin
3. Импортировать dashboard: `grafana/dashboards/bot-metrics.json`

**Что отображается:**
- ✅ Bot Status (Up/Down)
- ✅ Uptime
- ✅ Updates per second
- ✅ Error rate
- ✅ Command statistics
- ✅ Response time

### Алерты

Настроить алерты в Prometheus:

```yaml
# prometheus-alerts.yml
groups:
  - name: bot_alerts
    rules:
      - alert: BotDown
        expr: up{job="telegram-bot"} == 0
        for: 2m
        annotations:
          summary: "Bot is down"
          description: "Bot has been down for 2 minutes"

      - alert: HighErrorRate
        expr: rate(bot_total_errors[5m]) > 0.1
        for: 5m
        annotations:
          summary: "High error rate"
          description: "Error rate > 10% for 5 minutes"
```

---

## ☸️ Kubernetes Deployment

### Требования

- Kubernetes cluster (1.20+)
- kubectl configured
- Ingress controller (nginx)
- cert-manager (для SSL)

### Шаг 1: Создать секреты

```bash
# Скопировать example
cp k8s/secrets.example.yml k8s/secrets.yml

# Отредактировать с реальными значениями
nano k8s/secrets.yml

# Применить
kubectl apply -f k8s/secrets.yml
```

### Шаг 2: Deploy бота

```bash
# Применить deployment
kubectl apply -f k8s/deployment.yml

# Проверить статус
kubectl get pods -l app=dmarket-bot
kubectl logs -f deployment/dmarket-telegram-bot
```

### Шаг 3: Настроить Ingress (для webhook)

```bash
# Установить cert-manager (если еще нет)
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Применить ingress
kubectl apply -f k8s/ingress.yml

# Проверить
kubectl get ingress
```

### Health Checks в Kubernetes

**Deployment уже настроен с:**

1. **Liveness Probe** - перезапускает pod если бот мертв
```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 30
  periodSeconds: 10
  failureThreshold: 3
```

2. **Readiness Probe** - убирает pod из балансировщика если не готов
```yaml
readinessProbe:
  httpGet:
    path: /ready
    port: 8080
  initialDelaySeconds: 10
  periodSeconds: 5
  failureThreshold: 3
```

3. **Startup Probe** - дает время на старт
```yaml
startupProbe:
  httpGet:
    path: /health
    port: 8080
  periodSeconds: 5
  failureThreshold: 12  # 60 sec max
```

### Масштабирование в Kubernetes

```bash
# Вручную
kubectl scale deployment dmarket-telegram-bot --replicas=3

# Auto-scaling (HPA)
kubectl autoscale deployment dmarket-telegram-bot \
  --cpu-percent=70 \
  --min=2 \
  --max=10
```

---

## 🔧 CI/CD Pipeline

### GitHub Actions

CI/CD pipeline уже настроен в `.github/workflows/healthcheck.yml`

**Что делает:**

1. **Health Check Tests** (при каждом push)
   - Запускает тесты улучшений
   - Проверяет /health, /ready, /metrics endpoints

2. **Docker Health Check** (при каждом push)
   - Собирает Docker образ
   - Запускает контейнер
   - Ждет healthy статус
   - Проверяет endpoints

3. **Scheduled Checks** (каждые 6 часов)
   - Мониторит production бота
   - Отправляет алерты при сбоях

### Запуск локально

```bash
# Тест health checks
python test_improvements.py

# Docker health check
docker build -t dmarket-bot:test .
docker run -d --name test-bot \
  --env-file .env \
  -p 8080:8080 \
  --health-cmd "curl -f http://localhost:8080/health || exit 1" \
  --health-interval 10s \
  dmarket-bot:test

# Проверить health
docker inspect --format='{{.State.Health.Status}}' test-bot

# Cleanup
docker stop test-bot && docker rm test-bot
```

### Deploy pipeline (пример)

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    tags:
      - 'v*'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build and push Docker image
        run: |
          docker build -t myregistry/dmarket-bot:${{ github.ref_name }} .
          docker push myregistry/dmarket-bot:${{ github.ref_name }}

      - name: Deploy to Kubernetes
        run: |
          kubectl set image deployment/dmarket-telegram-bot \
            bot=myregistry/dmarket-bot:${{ github.ref_name }}
          kubectl rollout status deployment/dmarket-telegram-bot

      - name: Health check
        run: |
          sleep 30
          curl -f https://bot.example.com/health
```

---

## 📈 Масштабирование

### Вертикальное (больше ресурсов)

```yaml
# k8s/deployment.yml
resources:
  requests:
    memory: "512Mi"  # Увеличено с 256Mi
    cpu: "200m"      # Увеличено с 100m
  limits:
    memory: "1Gi"    # Увеличено с 512Mi
    cpu: "1000m"     # Увеличено с 500m
```

### Горизонтальное (больше pods)

```bash
# Вручную
kubectl scale deployment dmarket-telegram-bot --replicas=5

# Auto (HPA)
kubectl autoscale deployment dmarket-telegram-bot \
  --cpu-percent=70 \
  --min=2 \
  --max=10

# Проверить
kubectl get hpa
```

### Load Balancing

**С Webhook режимом:**
- Ingress автоматически балансирует между pods
- Telegram отправляет updates на разные pods
- Каждый pod обрабатывает свою часть трафика

**С Polling режимом:**
- Используйте только 1 replica (чтобы избежать конфликтов)
- Или переключитесь на webhook для масштабирования

### Database Connection Pooling

```python
# src/utils/database.py
engine = create_async_engine(
    database_url,
    pool_size=20,        # Больше connections
    max_overflow=10,     # Дополнительные при пиковой нагрузке
    pool_pre_ping=True,  # Проверка здоровья connection
)
```

---

## 🔐 Security Checklist

- [ ] Использовать HTTPS для webhook
- [ ] Включить SSL certificate validation
- [ ] Ограничить доступ к /metrics (basic auth)
- [ ] Использовать Kubernetes secrets для credentials
- [ ] Включить network policies
- [ ] Настроить pod security policies
- [ ] Регулярно обновлять dependencies
- [ ] Включить DRY_RUN в staging

---

## 📊 Мониторинг Production

### Важные метрики

1. **Availability**
   - Target: 99.9% uptime
   - Alert: если down > 2 минуты

2. **Latency**
   - Target: p95 < 500ms
   - Alert: если p95 > 1000ms

3. **Error Rate**
   - Target: < 0.1%
   - Alert: если > 1%

4. **Throughput**
   - Мониторить updates/second
   - Capacity planning

### Dashboards

**Grafana дашборды:**
- Bot Overview (status, uptime, updates)
- Performance (latency, throughput)
- Errors (rate, types, recent)
- Infrastructure (CPU, memory, disk)

---

## 🎯 Quick Commands

```bash
# Local development
python -m src.main

# Docker
docker-compose up -d

# Monitoring stack
docker-compose -f docker-compose.monitoring.yml up -d

# Kubernetes deploy
kubectl apply -f k8s/

# Scale
kubectl scale deployment dmarket-telegram-bot --replicas=3

# Logs
kubectl logs -f deployment/dmarket-telegram-bot

# Health check
curl http://localhost:8080/health

# Metrics
curl http://localhost:8080/metrics
```

---

## 📚 Дополнительные ресурсы

- [Telegram Bot API - Webhooks](https://core.telegram.org/bots/webhooks)
- [Prometheus Best Practices](https://prometheus.io/docs/practices/)
- [Kubernetes Health Checks](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)
- [Grafana Documentation](https://grafana.com/docs/)

---

**Версия:** 1.0
**Дата:** 01 января 2026
**Статус:** Production Ready ✅
