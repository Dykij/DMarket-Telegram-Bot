# Deployment Guide

**Версия**: 3.0
**Последнее обновление**: 17 декабря 2025 г.

---

This guide covers various deployment options for the DMarket Telegram Bot, from development to production environments.

## Table of Contents

- [Development Deployment](#development-deployment)
- [Docker Deployment](#docker-deployment)
- [Production Deployment](#production-deployment)
- [Cloud Deployment](#cloud-deployment)
- [Monitoring & Maintenance](#monitoring--maintenance)

## Development Deployment

### Local Development Setup

1. **Clone and Setup**
   ```bash
   git clone https://github.com/your-username/dmarket-telegram-bot.git
   cd dmarket-telegram-bot

   # Create virtual environment
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate

   # Install dependencies
   pip install -r requirements.txt
   ```

2. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Initialize Database**
   ```bash
   # For PostgreSQL
   createdb dmarket_bot_dev

   # Run migrations (if using Alembic)
   alembic upgrade head
   ```

4. **Run Development Server**
   ```bash
   python -m src.main --debug
   ```

### Development Tools

```bash
# Quality checks
make qa

# Run tests with coverage
make test-cov

# Format code
make format

# Generate documentation
make docs
```

## Docker Deployment

### Basic Docker Setup

1. **Build Image**
   ```bash
   docker build -t dmarket-bot .
   ```

2. **Run Container**
   ```bash
   docker run -d \
     --name dmarket-bot \
     --env-file .env \
     -v $(pwd)/data:/app/data \
     -v $(pwd)/logs:/app/logs \
     dmarket-bot
   ```

### Docker Compose (Recommended)

1. **Development Environment**
   ```bash
   # Start all services
   docker-compose up -d

   # View logs
   docker-compose logs -f bot

   # Stop services
   docker-compose down
   ```

2. **Production Environment**
   ```bash
   # Use production compose file
   docker-compose -f docker-compose.prod.yml up -d
   ```

### Docker Configuration

**Dockerfile** (already provided):
- Multi-stage build for optimization
- Non-root user for security
- Health checks included
- Proper signal handling

**docker-compose.yml** includes:
- Bot service
- PostgreSQL database
- Redis cache
- Volume mounts for persistence

## Production Deployment

### Server Requirements

**Minimum Requirements:**
- 1 CPU core
- 512 MB RAM
- 1 GB disk space
- Python 3.11+

**Recommended for Production:**
- 2+ CPU cores
- 2+ GB RAM
- 10+ GB disk space
- SSD storage
- Load balancer (for multiple instances)

### Production Setup

1. **Server Preparation**
   ```bash
   # Update system
   sudo apt update && sudo apt upgrade -y

   # Install dependencies
   sudo apt install -y python3 python3-pip python3-venv git nginx postgresql redis-server

   # Create application user
   sudo useradd -m -s /bin/bash dmarketbot
   sudo su - dmarketbot
   ```

2. **Application Setup**
   ```bash
   # Clone repository
   git clone https://github.com/your-username/dmarket-telegram-bot.git
   cd dmarket-telegram-bot

   # Create virtual environment
   python3 -m venv .venv
   source .venv/bin/activate

   # Install dependencies
   pip install -r requirements.txt
   ```

3. **Database Setup**
   ```bash
   # Create database and user
   sudo -u postgres createdb dmarket_bot_prod
   sudo -u postgres createuser dmarketbot
   sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE dmarket_bot_prod TO dmarketbot;"
   ```

4. **Environment Configuration**
   ```bash
   # Production environment file
   cat > .env << EOF
   TELEGRAM_BOT_TOKEN=your_production_bot_token
   DMARKET_PUBLIC_KEY=your_production_public_key
   DMARKET_SECRET_KEY=your_production_secret_key
   DATABASE_URL=postgresql://dmarketbot:password@localhost/dmarket_bot_prod
   REDIS_URL=redis://localhost:6379/0
   LOG_LEVEL=INFO
   WEBHOOK_URL=https://your-domain.com/webhook
   SENTRY_DSN=your_sentry_dsn
   EOF

   # Secure the environment file
   chmod 600 .env
   ```

### Process Management

#### Using systemd

1. **Create Service File**
   ```bash
   sudo tee /etc/systemd/system/dmarket-bot.service << EOF
   [Unit]
   Description=DMarket Telegram Bot
   After=network.target postgresql.service redis.service

   [Service]
   Type=exec
   User=dmarketbot
   Group=dmarketbot
   WorkingDirectory=/home/dmarketbot/dmarket-telegram-bot
   Environment=PATH=/home/dmarketbot/dmarket-telegram-bot/.venv/bin
   ExecStart=/home/dmarketbot/dmarket-telegram-bot/.venv/bin/python -m src.main
   ExecReload=/bin/kill -HUP \$MAINPID
   Restart=always
   RestartSec=5

   [Install]
   WantedBy=multi-user.target
   EOF
   ```

2. **Enable and Start Service**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable dmarket-bot
   sudo systemctl start dmarket-bot

   # Check status
   sudo systemctl status dmarket-bot
   ```

#### Using PM2

```bash
# Install PM2
npm install -g pm2

# Create ecosystem file
cat > ecosystem.config.js << EOF
module.exports = {
  apps: [{
    name: 'dmarket-bot',
    script: '.venv/bin/python',
    args: '-m src.main',
    cwd: '/home/dmarketbot/dmarket-telegram-bot',
    instances: 1,
    exec_mode: 'fork',
    env: {
      NODE_ENV: 'production'
    }
  }]
};
EOF

# Start application
pm2 start ecosystem.config.js

# Save PM2 configuration
pm2 save
pm2 startup
```

### Nginx Configuration (for Webhooks)

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Redirect HTTP to HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /path/to/your/cert.pem;
    ssl_certificate_key /path/to/your/key.pem;

    location /webhook {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /health {
        proxy_pass http://localhost:8000;
        access_log off;
    }
}
```

## Cloud Deployment

### Heroku Deployment

1. **Prepare for Heroku**
   ```bash
   # Create Procfile
   echo "web: python -m src.main" > Procfile

   # Create runtime.txt
   echo "python-3.11.0" > runtime.txt
   ```

2. **Deploy to Heroku**
   ```bash
   # Install Heroku CLI and login
   heroku login

   # Create application
   heroku create your-dmarket-bot

   # Set environment variables
   heroku config:set TELEGRAM_BOT_TOKEN=your_token
   heroku config:set DMARKET_PUBLIC_KEY=your_key
   heroku config:set DMARKET_SECRET_KEY=your_secret

   # Add PostgreSQL addon
   heroku addons:create heroku-postgresql:mini

   # Add Redis addon
   heroku addons:create heroku-redis:mini

   # Deploy
   git push heroku main
   ```

3. **One-Click Deploy**

   [![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

### DigitalOcean App Platform

1. **Create app.yaml**
   ```yaml
   name: dmarket-telegram-bot
   services:
   - name: bot
     source_dir: /
     github:
       repo: your-username/dmarket-telegram-bot
       branch: main
     run_command: python -m src.main
     environment_slug: python
     instance_count: 1
     instance_size_slug: basic-xxs
     envs:
     - key: TELEGRAM_BOT_TOKEN
       scope: RUN_TIME
       value: your_token
     - key: DMARKET_PUBLIC_KEY
       scope: RUN_TIME
       value: your_key
   databases:
   - engine: PG
     name: dmarket-db
     num_nodes: 1
     size: db-s-1vcpu-1gb
   ```

2. **Deploy**
   ```bash
   # Using DigitalOcean CLI
   doctl apps create --spec app.yaml
   ```

### AWS Deployment

#### Using AWS Lambda + API Gateway

1. **Serverless Framework Setup**
   ```yaml
   # serverless.yml
   service: dmarket-telegram-bot

   provider:
     name: aws
     runtime: python3.9
     region: us-east-1

   functions:
     webhook:
       handler: src.lambda_handler.webhook_handler
       events:
         - http:
             path: webhook
             method: post

   plugins:
     - serverless-python-requirements
   ```

2. **Deploy**
   ```bash
   npm install -g serverless
   serverless deploy
   ```

#### Using ECS Fargate

1. **Create Task Definition**
   ```json
   {
     "family": "dmarket-bot",
     "taskRoleArn": "arn:aws:iam::account:role/ecsTaskRole",
     "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
     "networkMode": "awsvpc",
     "requiresCompatibilities": ["FARGATE"],
     "cpu": "256",
     "memory": "512",
     "containerDefinitions": [{
       "name": "dmarket-bot",
       "image": "your-account.dkr.ecr.region.amazonaws.com/dmarket-bot:latest",
       "essential": true,
       "logConfiguration": {
         "logDriver": "awslogs",
         "options": {
           "awslogs-group": "/ecs/dmarket-bot",
           "awslogs-region": "us-east-1",
           "awslogs-stream-prefix": "ecs"
         }
       }
     }]
   }
   ```

### Google Cloud Platform

#### Using Cloud Run

1. **Build and Push Image**
   ```bash
   # Build image
   docker build -t gcr.io/your-project/dmarket-bot .

   # Push to Container Registry
   docker push gcr.io/your-project/dmarket-bot
   ```

2. **Deploy to Cloud Run**
   ```bash
   gcloud run deploy dmarket-bot \
     --image gcr.io/your-project/dmarket-bot \
     --platform managed \
     --region us-central1 \
     --set-env-vars TELEGRAM_BOT_TOKEN=your_token \
     --allow-unauthenticated
   ```

## Monitoring & Maintenance

### Health Checks

Implement health check endpoints:

```python
# src/health.py
from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

@app.get("/ready")
async def readiness_check():
    # Check database connection
    # Check external API availability
    return {"status": "ready"}
```

### Logging and Monitoring

1. **Centralized Logging**
   ```bash
   # Using ELK Stack
   docker-compose -f docker-compose.monitoring.yml up -d
   ```

2. **Metrics Collection**
   ```python
   # Prometheus metrics
   from prometheus_client import Counter, Histogram, generate_latest

   request_count = Counter('bot_requests_total', 'Total bot requests')
   response_time = Histogram('bot_response_seconds', 'Bot response time')
   ```

3. **Error Tracking**
   ```python
   # Sentry integration
   import sentry_sdk

   sentry_sdk.init(
       dsn="your-sentry-dsn",
       traces_sample_rate=1.0,
   )
   ```

### Backup and Recovery

1. **Database Backups**
   ```bash
   # Automated backup script
   #!/bin/bash
   BACKUP_DIR="/backups"
   DATE=$(date +%Y%m%d_%H%M%S)

   pg_dump dmarket_bot_prod > $BACKUP_DIR/dmarket_bot_$DATE.sql

   # Keep only last 30 days
   find $BACKUP_DIR -name "dmarket_bot_*.sql" -mtime +30 -delete
   ```

2. **Configuration Backups**
   ```bash
   # Backup environment and configs
   tar -czf config_backup_$DATE.tar.gz .env config/ scripts/
   ```

### Security Considerations

1. **Regular Updates**
   ```bash
   # Update dependencies
   pip-audit  # Check for vulnerabilities
   pip install --upgrade -r requirements.txt
   ```

2. **SSL/TLS Configuration**
   - Use Let's Encrypt for free SSL certificates
   - Configure proper cipher suites
   - Enable HSTS headers

3. **Network Security**
   - Use firewalls to restrict access
   - Implement rate limiting
   - Monitor for unusual traffic patterns

4. **Secrets Management**
   - Use environment variables or secret management systems
   - Rotate API keys regularly
   - Monitor for exposed credentials

### Performance Optimization

1. **Database Optimization**
   ```sql
   -- Create indexes for frequently queried columns
   CREATE INDEX idx_users_telegram_id ON bot.users(telegram_id);
   CREATE INDEX idx_market_data_item_game ON analytics.market_data(item_id, game);
   ```

2. **Cache Configuration**
   ```python
   # Redis cache configuration
   CACHE_CONFIG = {
       'default': {
           'BACKEND': 'django_redis.cache.RedisCache',
           'LOCATION': 'redis://127.0.0.1:6379/1',
           'OPTIONS': {
               'CLIENT_CLASS': 'django_redis.client.DefaultClient',
           }
       }
   }
   ```

3. **Load Balancing**
   ```nginx
   upstream dmarket_bot {
       server 127.0.0.1:8000;
       server 127.0.0.1:8001;
       server 127.0.0.1:8002;
   }
   ```

This deployment guide should cover most scenarios from development to large-scale production deployments. Choose the approach that best fits your requirements and infrastructure.
