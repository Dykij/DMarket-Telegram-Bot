# 🚀 n8n Integration - Deployment Guide

Quick guide to deploying n8n workflow automation with DMarket Bot.

---

## 📋 Prerequisites

- Docker & Docker Compose installed
- DMarket Bot configured and running
- PostgreSQL database available
- `.env` file configured

---

## ⚡ Quick Start (5 minutes)

### 1. Update Environment Variables

Add to your `.env` file:

```bash
# n8n Configuration
N8N_ENABLED=true
N8N_USER=admin
N8N_PASSWORD=YourSecurePassword123!  # CHANGE THIS!
N8N_ENCRYPTION_KEY=your-32-char-encryption-key-here
N8N_DB_PASSWORD=n8n_password
N8N_BOT_API_URL=http://bot:8080
N8N_TELEGRAM_CHAT_ID=your-telegram-chat-id
```

Generate encryption key:
```bash
python -c "import secrets; print(secrets.token_hex(16))"
```

### 2. Start Services

```bash
# Start all services including n8n
docker-compose up -d

# Check status
docker ps

# You should see:
# - dmarket-bot
# - dmarket-postgres
# - dmarket-redis
# - dmarket-n8n  ← NEW!
```

### 3. Access n8n UI

- URL: http://localhost:5678
- Login with credentials from `.env`

### 4. Import First Workflow

1. In n8n UI: **Workflows** → **Import from File**
2. Select: `n8n/workflows/daily-trading-report.json`
3. Configure credentials (see below)
4. Test workflow
5. Activate

---

## 🔧 Configuration Details

### Telegram Bot Credentials in n8n

1. Go to: **Credentials** → **Add Credential**
2. Select: **Telegram**
3. Name: `Telegram Bot API`
4. Access Token: `YOUR_BOT_TOKEN` (from .env)
5. **Save**

### HTTP Request Configuration

n8n workflows use `http://bot:8080` to communicate with the bot API.

**Important**: Use container name `bot`, not `localhost`!

Test endpoint:
```bash
# From inside n8n container
docker exec dmarket-n8n curl http://bot:8080/api/v1/n8n/health

# Expected response:
{
  "status": "healthy",
  "service": "n8n-integration-api",
  "timestamp": "2026-01-13T12:00:00Z",
  "version": "1.0.0"
}
```

---

## 📊 Available Workflows

### 1. Daily Trading Report

**File**: `daily-trading-report.json`  
**Schedule**: Every day at 9:00 AM UTC  
**Requirements**: Telegram credentials, TELEGRAM_CHAT_ID

**Flow**:
1. Schedule trigger at 9:00 AM
2. GET `/api/v1/n8n/stats/daily`
3. Format data with JavaScript
4. Send to Telegram

**Setup**:
1. Import workflow
2. Add Telegram credentials
3. Set environment variable: `TELEGRAM_CHAT_ID`
4. Activate workflow

---

## 🔒 Security Checklist

- [ ] Changed default n8n password
- [ ] Set strong encryption key
- [ ] Configured firewall (port 5678 restricted)
- [ ] Using HTTPS in production (via nginx)
- [ ] Credentials encrypted in n8n
- [ ] Bot API protected (JWT/API key)
- [ ] Rate limiting enabled
- [ ] Regular backups configured

---

## 🐛 Troubleshooting

### n8n Container Won't Start

```bash
# Check logs
docker logs dmarket-n8n

# Common issues:
# 1. PostgreSQL not ready → Wait 30s, try again
# 2. Port 5678 in use → Change port in docker-compose.yml
# 3. Missing encryption key → Set N8N_ENCRYPTION_KEY in .env
```

### Can't Access n8n UI

```bash
# Check if running
docker ps | grep n8n

# Check port binding
netstat -tlnp | grep 5678

# Access from host machine
curl http://localhost:5678/healthz
```

### Workflow Fails: "Cannot reach bot API"

```bash
# Test connectivity from n8n container
docker exec dmarket-n8n ping bot

# If fails, check Docker network
docker network inspect dmarket-telegram-bot_bot-network

# Ensure both containers in same network
```

### Workflow Fails: "Telegram API error"

1. **Check credentials**: Credentials → Test connection
2. **Check bot token**: Must be valid from @BotFather
3. **Check chat ID**: Use @userinfobot to get your ID
4. **Check permissions**: Bot must be able to send messages

---

## 📈 Monitoring

### Check n8n Health

```bash
# Via Docker
docker logs -f dmarket-n8n

# Via HTTP
curl http://localhost:5678/healthz
```

### Check Workflow Executions

In n8n UI:
- **Executions** → View all runs
- Filter by status: Success / Error
- View execution details
- Check execution time

### Performance Metrics

n8n tracks:
- Total executions
- Success rate
- Average execution time
- Error rate

Access: **Executions** → **Statistics**

---

## 🔄 Backup & Restore

### Backup n8n Data

```bash
# Backup workflows
docker exec dmarket-n8n tar czf /backup/workflows.tar.gz /home/node/.n8n/workflows

# Copy to host
docker cp dmarket-n8n:/backup/workflows.tar.gz ./backups/

# Backup database (PostgreSQL)
docker exec dmarket-postgres pg_dump -U n8n_user n8n > n8n_db_backup.sql
```

### Restore n8n Data

```bash
# Restore workflows
docker cp ./backups/workflows.tar.gz dmarket-n8n:/tmp/
docker exec dmarket-n8n tar xzf /tmp/workflows.tar.gz -C /

# Restore database
docker exec -i dmarket-postgres psql -U n8n_user n8n < n8n_db_backup.sql
```

---

## 🌐 Production Deployment

### Using Nginx Reverse Proxy

```nginx
# /etc/nginx/sites-available/n8n

server {
    listen 443 ssl http2;
    server_name n8n.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://localhost:5678;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        
        # WebSocket support
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Update `.env`:
```bash
N8N_HOST=n8n.yourdomain.com
N8N_PROTOCOL=https
N8N_PORT=443
```

### Using Docker Compose Production

```yaml
# docker-compose.prod.yml

services:
  n8n:
    image: n8nio/n8n:latest
    restart: always
    environment:
      - N8N_HOST=${N8N_HOST}
      - N8N_PROTOCOL=https
      - N8N_PORT=443
      - NODE_ENV=production
    # ... rest of config
```

---

## 🧪 Testing

### Test API Endpoints

```bash
# Health check
curl http://localhost:8080/api/v1/n8n/health

# Get daily stats
curl http://localhost:8080/api/v1/n8n/stats/daily

# Send test arbitrage alert
curl -X POST http://localhost:8080/api/v1/n8n/webhooks/arbitrage \
  -H "Content-Type: application/json" \
  -d '{
    "item_name": "Test Item",
    "game": "csgo",
    "buy_price": 10.0,
    "sell_price": 12.0,
    "profit": 2.0,
    "profit_margin": 20.0,
    "platform_from": "dmarket",
    "platform_to": "waxpeer"
  }'
```

### Test Workflow Manually

In n8n UI:
1. Open workflow
2. Click **Execute Workflow**
3. Check execution result
4. View output of each node
5. Fix any errors
6. Save changes

---

## 📚 Next Steps

1. **Explore Templates**: Check `n8n/workflows/` for more examples
2. **Create Custom Workflows**: Use n8n visual editor
3. **Add More Integrations**: 400+ nodes available
4. **Monitor Performance**: Check execution logs
5. **Scale Up**: Add more workflows as needed

---

## 📖 Additional Resources

- **Full Analysis**: [N8N_INTEGRATION_ANALYSIS.md](N8N_INTEGRATION_ANALYSIS.md)
- **Quick Summary**: [N8N_QUICK_SUMMARY_RU.md](N8N_QUICK_SUMMARY_RU.md)
- **Architecture**: [N8N_ARCHITECTURE_DIAGRAMS.md](N8N_ARCHITECTURE_DIAGRAMS.md)
- **n8n Docs**: https://docs.n8n.io
- **ai_agents_az Examples**: https://github.com/gyoridavid/ai_agents_az

---

## 🆘 Getting Help

1. **Check logs**: `docker logs dmarket-n8n`
2. **Check docs**: n8n documentation
3. **Community**: n8n community forum
4. **Issues**: GitHub issues

---

**Last Updated**: January 13, 2026  
**Version**: 1.0.0
