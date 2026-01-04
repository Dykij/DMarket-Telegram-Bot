# 🚀 Deployment Guide

**Версия**: 1.0.0
**Последнее обновление: Январь 2026 г.

---

## 📋 Обзор

Руководство по развертыванию DMarket Telegram Bot.

## 🐳 Docker (Рекомендуется)

### Быстрый запуск

```bash
# Клонировать репозиторий
git clone https://github.com/Dykij/DMarket-Telegram-Bot.git
cd DMarket-Telegram-Bot

# Создать .env
cp .env.example .env
# Отредактировать .env

# Собрать и запустить
docker-compose up -d
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  bot:
    build: .
    restart: unless-stopped
    env_file: .env
    depends_on:
      - db
      - redis

  db:
    image: postgres:14
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      POSTGRES_DB: dmarket_bot
      POSTGRES_USER: bot_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

### Команды Docker

```bash
# Сборка
docker-compose build

# Запуск
docker-compose up -d

# Логи
docker-compose logs -f bot

# Остановка
docker-compose down

# Пересборка
docker-compose build --no-cache
```

## ☁️ Cloud Deployment

### Heroku

```bash
# Установить Heroku CLI
# Создать приложение
heroku create dmarket-bot

# Установить переменные окружения
heroku config:set TELEGRAM_BOT_TOKEN=xxx
heroku config:set DMARKET_PUBLIC_KEY=xxx
heroku config:set DMARKET_SECRET_KEY=xxx

# Добавить PostgreSQL
heroku addons:create heroku-postgresql:hobby-dev

# Добавить Redis
heroku addons:create heroku-redis:hobby-dev

# Деплой
git push heroku main
```

### AWS (EC2 + RDS)

1. Создать EC2 instance (t3.micro минимум)
2. Создать RDS PostgreSQL instance
3. Создать ElastiCache Redis instance
4. Установить Docker на EC2
5. Настроить Security Groups
6. Развернуть через docker-compose

### Google Cloud Platform

```bash
# Cloud Run
gcloud run deploy dmarket-bot \
  --source . \
  --region us-central1 \
  --set-env-vars TELEGRAM_BOT_TOKEN=xxx
```

## 🔧 Manual Deployment

### Требования

- Python 3.11+
- PostgreSQL 14+
- Redis 7+

### Установка

```bash
# Виртуальное окружение
python -m venv .venv
source .venv/bin/activate

# Зависимости
pip install -r requirements.txt

# Конфигурация
cp .env.example .env
nano .env

# Миграции БД
alembic upgrade head

# Запуск
python -m src.main
```

### Systemd Service

```ini
# /etc/systemd/system/dmarket-bot.service
[Unit]
Description=DMarket Telegram Bot
After=network.target

[Service]
User=bot
WorkingDirectory=/home/bot/DMarket-Telegram-Bot
Environment="PATH=/home/bot/DMarket-Telegram-Bot/.venv/bin"
EnvironmentFile=/home/bot/DMarket-Telegram-Bot/.env
ExecStart=/home/bot/DMarket-Telegram-Bot/.venv/bin/python -m src.main
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Активация
sudo systemctl daemon-reload
sudo systemctl enable dmarket-bot
sudo systemctl start dmarket-bot
```

## 📊 Мониторинг

### Sentry

```bash
# Добавить в .env
SENTRY_DSN=https://xxx@sentry.io/xxx
```

### Prometheus Metrics

Доступны на `/metrics` endpoint (если включены).

---

**Подробнее**: [ARCHITECTURE.md](ARCHITECTURE.md)
