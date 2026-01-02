# 🚀 Quick Start - Production Features

Быстрый гайд по запуску production функций: мониторинг, webhook, Kubernetes.

---

## 📊 1. Мониторинг (Prometheus + Grafana)

### Запуск

```bash
# Запустить все сервисы (бот + Prometheus + Grafana)
docker-compose -f docker-compose.monitoring.yml up -d

# Проверить статус
docker-compose -f docker-compose.monitoring.yml ps
```

### Доступ

- **Grafana:** http://localhost:3000
  - Login: `admin`
  - Password: `admin`

- **Prometheus:** http://localhost:9090

- **Bot Metrics:** http://localhost:8080/metrics

### Просмотр метрик

1. Открыть Grafana: http://localhost:3000
2. Войти (admin/admin)
3. Dashboards → DMarket Bot Metrics

**Что видно:**
- ✅ Bot Status (Up/Down)
- ✅ Uptime (время работы)
- ✅ Total Updates (количество обновлений)
- ✅ Error Rate (процент ошибок)

### Остановка

```bash
docker-compose -f docker-compose.monitoring.yml down
```

---

## 🔄 2. Webhook (вместо Polling)

### Зачем?

- ✅ Меньше нагрузки на Telegram API
- ✅ Лучше масштабируется
- ✅ Работает с load balancers

### Настройка

**1. Получить публичный URL:**

```bash
# Локально (ngrok для тестирования)
ngrok http 8443

# Production (ваш домен)
# https://bot.example.com
```

**2. Создать SSL сертификат:**

```bash
# Self-signed (для тестирования)
openssl req -newkey rsa:2048 -sha256 -nodes \
  -keyout private.key -x509 -days 365 \
  -out cert.pem -subj "/CN=bot.example.com"

# Production: Let's Encrypt
certbot certonly --standalone -d bot.example.com
```

**3. Настроить переменные окружения:**

```bash
# .env
WEBHOOK_URL=https://your-ngrok-url.ngrok.io
WEBHOOK_PORT=8443
WEBHOOK_CERT_PATH=cert.pem
WEBHOOK_KEY_PATH=private.key
```

**4. Запустить с webhook:**

```python
# В src/main.py добавить:
from src.telegram_bot.webhook import WebhookConfig, is_webhook_mode, start_webhook

webhook_url = os.getenv("WEBHOOK_URL")
if is_webhook_mode(webhook_url):
    config = WebhookConfig(
        url=webhook_url,
        port=int(os.getenv("WEBHOOK_PORT", "8443")),
        cert_path=os.getenv("WEBHOOK_CERT_PATH"),
        key_path=os.getenv("WEBHOOK_KEY_PATH"),
    )
    await start_webhook(application, config)
else:
    # Polling mode (по умолчанию)
    await application.run_polling()
```

---

## ☸️ 3. Kubernetes Deployment

### Требования

- Kubernetes cluster
- kubectl configured
- Docker registry

### Шаг 1: Создать секреты

```bash
# Копировать example
cp k8s/secrets.example.yml k8s/secrets.yml

# Отредактировать с реальными значениями
nano k8s/secrets.yml

# Применить
kubectl apply -f k8s/secrets.yml
```

### Шаг 2: Deploy

```bash
# Применить все манифесты
kubectl apply -f k8s/

# Проверить статус
kubectl get pods -l app=dmarket-bot
kubectl get svc
kubectl get ingress

# Логи
kubectl logs -f deployment/dmarket-telegram-bot
```

### Шаг 3: Проверить Health Checks

```bash
# Liveness probe
kubectl get pods  # STATUS должен быть Running

# Health endpoint
kubectl port-forward deployment/dmarket-telegram-bot 8080:8080
curl http://localhost:8080/health
```

### Масштабирование

```bash
# Вручную
kubectl scale deployment dmarket-telegram-bot --replicas=3

# Auto-scaling
kubectl autoscale deployment dmarket-telegram-bot \
  --cpu-percent=70 \
  --min=2 \
  --max=10
```

---

## 🔧 4. CI/CD Health Checks

CI/CD pipeline уже настроен в `.github/workflows/healthcheck.yml`

### Что проверяет

1. **Health Check Tests**
   - Запускает `test_improvements.py`
   - Проверяет /health, /ready, /metrics

2. **Docker Health Check**
   - Собирает Docker образ
   - Запускает контейнер
   - Ждет healthy статус
   - Проверяет endpoints

3. **Scheduled Checks** (каждые 6 часов)
   - Мониторит production
   - Отправляет алерты

### Запуск локально

```bash
# Health check тесты
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

---

## 📋 Checklist Deployment

### Локальная разработка
- [ ] Бот работает: `python -m src.main`
- [ ] Health check доступен: `curl http://localhost:8080/health`
- [ ] Тесты проходят: `python test_improvements.py`

### Docker
- [ ] Образ собирается: `docker build -t dmarket-bot .`
- [ ] Контейнер запускается: `docker run ...`
- [ ] Health check работает в контейнере

### Monitoring
- [ ] Prometheus scrapes метрики
- [ ] Grafana показывает dashboard
- [ ] Алерты настроены

### Kubernetes
- [ ] Секреты созданы
- [ ] Deployment применен
- [ ] Pods в статусе Running
- [ ] Liveness/Readiness probes работают
- [ ] Ingress настроен (для webhook)

### Production
- [ ] DRY_RUN=false
- [ ] SSL сертификат валидный
- [ ] Webhook URL публичный
- [ ] Мониторинг настроен
- [ ] Алерты работают
- [ ] Backup настроен

---

## 🆘 Troubleshooting

### Бот не стартует

```bash
# Проверить логи
docker logs dmarket-bot
kubectl logs deployment/dmarket-telegram-bot

# Проверить health
curl http://localhost:8080/health
```

### Health check fails

```bash
# Проверить что бот слушает на 8080
netstat -tulpn | grep 8080

# Проверить health check сервер
curl -v http://localhost:8080/health
```

### Prometheus не видит метрики

```bash
# Проверить targets в Prometheus
# http://localhost:9090/targets

# Проверить что метрики доступны
curl http://localhost:8080/metrics
```

### Kubernetes pods не становятся Ready

```bash
# Проверить события
kubectl describe pod <pod-name>

# Проверить логи
kubectl logs <pod-name>

# Проверить probes
kubectl get pods -o yaml | grep -A 10 "livenessProbe\|readinessProbe"
```

---

## 📚 Дополнительные документы

- **[PRODUCTION_DEPLOYMENT.md](docs/PRODUCTION_DEPLOYMENT.md)** - Полное руководство
- **[BOT_IMPROVEMENTS.md](docs/BOT_IMPROVEMENTS.md)** - Best practices
- **[IMPROVEMENTS_SUMMARY.md](IMPROVEMENTS_SUMMARY.md)** - Краткая сводка

---

**Дата:** 01 января 2026
**Статус:** Production Ready ✅
