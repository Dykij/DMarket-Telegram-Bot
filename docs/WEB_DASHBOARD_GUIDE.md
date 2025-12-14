# Web Dashboard

## Обзор

Веб-дашборд для мониторинга и управления DMarket Telegram Bot.

## Архитектура

```
Frontend (React) ← REST API → Backend (FastAPI) ← Bot
```

## Технологии

### Backend
- **FastAPI** - современный async веб-фреймворк
- **Uvicorn** - ASGI сервер
- **Pydantic** - валидация данных
- **SQLAlchemy** - ORM для БД

### Frontend
- **React** - UI библиотека
- **TypeScript** - типизация
- **Tailwind CSS** - стили
- **Chart.js** - графики
- **React Query** - data fetching

## Установка

### Backend

```bash
# Установить зависимости
pip install fastapi uvicorn[standard] python-multipart

# Запустить сервер
cd src/web_dashboard
python app.py

# Или через uvicorn
uvicorn app:app --reload --port 8080
```

### Frontend

```bash
# Создать React проект
npx create-react-app dashboard-ui --template typescript

# Установить зависимости
cd dashboard-ui
npm install axios react-query chart.js react-chartjs-2 tailwindcss

# Запустить dev server
npm start
```

## API Endpoints

### Статус бота

```bash
GET /api/v1/status
```

**Response:**
```json
{
  "running": true,
  "uptime_seconds": 86400,
  "active_users": 1250,
  "total_commands": 50000
}
```

### Пользователи

```bash
GET /api/v1/users?limit=100&offset=0
```

**Response:**
```json
{
  "users": [
    {
      "user_id": 123456,
      "username": "trader1",
      "commands_count": 150,
      "balance_usd": 5000.0,
      "active_targets": 5
    }
  ],
  "total": 1250
}
```

### Сканирование арбитража

```bash
POST /api/v1/arbitrage/scan
Content-Type: application/json

{
  "level": "standard",
  "game": "csgo",
  "min_profit": 1.0
}
```

### Таргеты

```bash
# Создать таргет
POST /api/v1/targets
{
  "user_id": 123456,
  "game": "csgo",
  "item_name": "AK-47 | Redline (FT)",
  "price": 10.50
}

# Получить таргеты
GET /api/v1/targets?user_id=123456&game=csgo&status=active

# Удалить таргет
DELETE /api/v1/targets/{target_id}
```

### Аналитика

```bash
# Dashboard данные
GET /api/v1/analytics/dashboard

# График команд
GET /api/v1/analytics/charts/commands?period=24h

# График арбитража
GET /api/v1/analytics/charts/arbitrage?period=7d
```

## Frontend Components

### Dashboard

```tsx
// src/components/Dashboard.tsx
import React from 'react';
import { useQuery } from 'react-query';
import axios from 'axios';

const API_URL = 'http://localhost:8080/api/v1';

export const Dashboard: React.FC = () => {
  const { data: status } = useQuery('bot-status', async () => {
    const res = await axios.get(`${API_URL}/status`);
    return res.data;
  });

  const { data: analytics } = useQuery('dashboard-analytics', async () => {
    const res = await axios.get(`${API_URL}/analytics/dashboard`);
    return res.data;
  });

  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold mb-6">DMarket Bot Dashboard</h1>
      
      <div className="grid grid-cols-4 gap-4 mb-8">
        <StatsCard 
          title="Active Users" 
          value={analytics?.active_today} 
          icon="👥"
        />
        <StatsCard 
          title="Commands Today" 
          value={analytics?.commands_today} 
          icon="⚡"
        />
        <StatsCard 
          title="Scans Today" 
          value={analytics?.arbitrage_scans_today} 
          icon="🔍"
        />
        <StatsCard 
          title="Profit Today" 
          value={`$${analytics?.profit_today_usd}`} 
          icon="💰"
        />
      </div>

      <div className="grid grid-cols-2 gap-6">
        <CommandsChart />
        <ArbitrageChart />
      </div>
    </div>
  );
};
```

### StatsCard

```tsx
interface StatsCardProps {
  title: string;
  value: number | string;
  icon: string;
}

const StatsCard: React.FC<StatsCardProps> = ({ title, value, icon }) => (
  <div className="bg-white rounded-lg shadow p-6">
    <div className="flex items-center justify-between">
      <div>
        <p className="text-gray-500 text-sm">{title}</p>
        <p className="text-2xl font-bold mt-2">{value}</p>
      </div>
      <span className="text-4xl">{icon}</span>
    </div>
  </div>
);
```

### Charts

```tsx
import { Line } from 'react-chartjs-2';

const CommandsChart: React.FC = () => {
  const { data } = useQuery('commands-chart', async () => {
    const res = await axios.get(`${API_URL}/analytics/charts/commands`);
    return res.data;
  });

  const chartData = {
    labels: data?.labels || [],
    datasets: [{
      label: 'Commands',
      data: data?.data || [],
      borderColor: 'rgb(59, 130, 246)',
      tension: 0.1
    }]
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-xl font-bold mb-4">Commands (24h)</h2>
      <Line data={chartData} />
    </div>
  );
};
```

## Docker Deployment

### Backend Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/web_dashboard /app

EXPOSE 8080

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
```

### Frontend Dockerfile

```dockerfile
FROM node:18-alpine as build

WORKDIR /app

COPY dashboard-ui/package*.json ./
RUN npm install

COPY dashboard-ui/ ./
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
```

### Docker Compose

```yaml
version: '3.8'

services:
  dashboard-api:
    build:
      context: .
      dockerfile: Dockerfile.api
    ports:
      - "8080:8080"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/dmarket
    depends_on:
      - db

  dashboard-ui:
    build:
      context: .
      dockerfile: Dockerfile.ui
    ports:
      - "80:80"
    depends_on:
      - dashboard-api

  db:
    image: postgres:15
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=dmarket
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

## Страницы дашборда

1. **Home** - Общая статистика, графики
2. **Users** - Список пользователей, статистика
3. **Arbitrage** - Сканирование, возможности
4. **Targets** - Управление таргетами
5. **Analytics** - Детальная аналитика
6. **Settings** - Настройки бота
7. **Logs** - Просмотр логов

## Security

```python
from fastapi import Security, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Проверить JWT токен."""
    token = credentials.credentials
    # TODO: Проверить токен
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    return token
```

## Запуск

```bash
# Backend
cd src/web_dashboard
python app.py

# Frontend
cd dashboard-ui
npm start

# Полный стек
docker-compose up -d
```

## Endpoints

- **API**: http://localhost:8080
- **UI**: http://localhost:3000
- **API Docs**: http://localhost:8080/docs

## Development

```bash
# Hot reload backend
uvicorn app:app --reload

# Hot reload frontend
npm start

# Build production
npm run build
```

## Дополнительно

- WebSocket для real-time обновлений
- JWT authentication
- Role-based access control
- Rate limiting для API
- API versioning
