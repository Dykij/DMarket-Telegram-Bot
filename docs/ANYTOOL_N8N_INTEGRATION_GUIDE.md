# 🤖 AnyTool и n8n: Руководство по интеграции AI агентов

**Версия**: 1.0  
**Дата**: Декабрь 2025  
**Статус**: Планирование

---

## 📋 Обзор

Это руководство описывает план интеграции двух мощных инструментов для автоматизации AI агентов:

1. **HKUDS/AnyTool** — Universal Tool-Use Layer для AI агентов
2. **n8n** — Visual workflow automation для production-grade AI агентов

Оба инструмента могут значительно улучшить работу GitHub Copilot и автоматизацию торгового бота.

---

## 🎯 Цели интеграции

| Цель | Инструмент | Приоритет |
|------|-----------|-----------|
| Улучшение GitHub Copilot workflow | AnyTool MCP | 🔴 Высокий |
| Visual automation для DevOps | n8n | 🟡 Средний |
| AI-powered trading decisions | AnyTool + n8n | 🟡 Средний |
| Multi-agent orchestration | AnyTool | 🟢 Низкий |

---

## 📊 Матрица совместимости с DMarket ToS

### ✅ Разрешенные функции

| Функция | AnyTool Backend | DMarket ToS | Применение |
|---------|-----------------|-------------|------------|
| API вызовы | MCP | ✅ Разрешено | Торговля через Trading API |
| Локальные скрипты | Shell | ✅ Разрешено | Анализ данных, бэкапы |
| CI/CD автоматизация | Shell | ✅ Разрешено | Деплой, тесты |
| n8n workflow с API | n8n + HTTP | ✅ Разрешено | Оркестрация через API |

### ❌ Запрещенные функции

| Функция | AnyTool Backend | DMarket ToS | Причина |
|---------|-----------------|-------------|---------|
| GUI automation | GUI | ❌ Запрещено | "no automated means (robots)" |
| Web scraping | Web | ❌ Запрещено | Explicitly forbidden |
| Browser automation | GUI | ❌ Запрещено | "spiders, scrapers" clause |
| Headless browsing | Web | ❌ Запрещено | Подпадает под ToS |

---

## 🔧 Часть 1: AnyTool Integration

### Что такое AnyTool?

**AnyTool** — это Universal Tool-Use Layer от HKUDS (Hong Kong University of Science), который решает три ключевые проблемы AI агентов:

1. **Tool Context Overload** — слишком много инструментов перегружают контекст
2. **Quality Issues** — ненадежные community tools
3. **Limited Scope** — ограниченные возможности MCP серверов

### Архитектура AnyTool

```
┌─────────────────────────────────────────────────────────────────┐
│                        AnyTool Layer                            │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐            │
│  │   MCP   │  │  Shell  │  │   GUI   │  │   Web   │            │
│  │ Backend │  │ Backend │  │ Backend │  │ Backend │            │
│  │   ✅    │  │   ✅    │  │   ❌    │  │   ❌    │            │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘            │
│       │            │            │            │                  │
│       ▼            ▼            ▼            ▼                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Smart Tool RAG & Quality Tracking           │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DMarket Trading Bot                          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌────────────────┐  │
│  │  DMarket API    │  │  Telegram Bot   │  │  Arbitrage     │  │
│  │  Client         │  │  Handlers       │  │  Scanner       │  │
│  └─────────────────┘  └─────────────────┘  └────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Настройка AnyTool для DMarket

#### Безопасная конфигурация

```python
from anytool import AnyTool
from anytool.tool_layer import AnyToolConfig

# Конфигурация БЕЗ запрещенных бэкендов
config = AnyToolConfig(
    # LLM Configuration
    llm_model="anthropic/claude-sonnet-4-5",
    llm_enable_thinking=False,
    llm_timeout=120.0,
    
    # ТОЛЬКО разрешенные бэкенды (БЕЗ "gui" и "web")
    backend_scope=["mcp", "shell", "system"],
    
    # Recording для аудита
    enable_recording=True,
    recording_backends=["mcp", "shell"],
    recording_log_dir="./logs/anytool",
    
    # Logging
    log_level="INFO",
)

async def execute_safe_task(task: str) -> dict:
    """Выполнить задачу через AnyTool безопасно."""
    async with AnyTool(config=config) as tool_layer:
        result = await tool_layer.execute(task)
        return result
```

#### MCP Server для DMarket API

Создание кастомного MCP сервера для DMarket:

```json
// anytool/config/config_mcp.json
{
  "mcpServers": {
    "dmarket": {
      "command": "python",
      "args": ["-m", "src.mcp_server.dmarket_mcp"],
      "env": {
        "DMARKET_PUBLIC_KEY": "${DMARKET_PUBLIC_KEY}",
        "DMARKET_SECRET_KEY": "${DMARKET_SECRET_KEY}"
      }
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}"
      }
    }
  }
}
```

#### Пример MCP Server для DMarket

```python
# src/mcp_server/dmarket_mcp.py
"""MCP Server для DMarket Trading API."""

from mcp.server import Server
from mcp.server.models import Tool, TextContent
from src.dmarket.dmarket_api import DMarketAPI

server = Server("dmarket-mcp")
api_client = DMarketAPI()

@server.list_tools()
async def list_tools():
    """Список доступных инструментов."""
    return [
        Tool(
            name="get_balance",
            description="Получить текущий баланс аккаунта DMarket",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_market_items",
            description="Получить предметы с маркетплейса DMarket",
            inputSchema={
                "type": "object",
                "properties": {
                    "game": {"type": "string", "enum": ["csgo", "dota2", "tf2", "rust"]},
                    "price_from": {"type": "integer", "description": "Минимальная цена в центах"},
                    "price_to": {"type": "integer", "description": "Максимальная цена в центах"},
                    "limit": {"type": "integer", "default": 100}
                },
                "required": ["game"]
            }
        ),
        Tool(
            name="create_target",
            description="Создать таргет (buy order) на покупку предмета",
            inputSchema={
                "type": "object",
                "properties": {
                    "game": {"type": "string"},
                    "title": {"type": "string"},
                    "price": {"type": "integer", "description": "Цена в центах"},
                    "amount": {"type": "integer", "default": 1}
                },
                "required": ["game", "title", "price"]
            }
        ),
        Tool(
            name="scan_arbitrage",
            description="Сканировать арбитражные возможности",
            inputSchema={
                "type": "object",
                "properties": {
                    "level": {"type": "string", "enum": ["boost", "standard", "medium", "advanced", "pro"]},
                    "game": {"type": "string", "default": "csgo"},
                    "min_profit_percent": {"type": "number", "default": 5.0}
                },
                "required": ["level"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    """Вызов инструмента."""
    if name == "get_balance":
        balance = await api_client.get_balance()
        return [TextContent(type="text", text=str(balance))]
    
    elif name == "get_market_items":
        items = await api_client.get_market_items(**arguments)
        return [TextContent(type="text", text=str(items))]
    
    elif name == "create_target":
        result = await api_client.create_target(**arguments)
        return [TextContent(type="text", text=str(result))]
    
    elif name == "scan_arbitrage":
        from src.dmarket.arbitrage_scanner import ArbitrageScanner
        scanner = ArbitrageScanner(api_client)
        opportunities = await scanner.scan_level(**arguments)
        return [TextContent(type="text", text=str(opportunities))]

if __name__ == "__main__":
    import asyncio
    asyncio.run(server.run())
```

### Улучшения от AnyTool

#### 1. Smart Tool RAG

AnyTool использует Progressive Tool Filtering для эффективного выбора инструментов:

```
Запрос: "Найди арбитражные возможности для CS:GO"
    │
    ▼
┌───────────────────────────────┐
│  Stage 1: Server Selection    │  → Выбрать dmarket MCP server
└───────────────────────────────┘
    │
    ▼
┌───────────────────────────────┐
│  Stage 2: Tool Name Matching  │  → scan_arbitrage, get_market_items
└───────────────────────────────┘
    │
    ▼
┌───────────────────────────────┐
│  Stage 3: Semantic Search     │  → scan_arbitrage (best match)
└───────────────────────────────┘
    │
    ▼
┌───────────────────────────────┐
│  Stage 4: LLM Ranking         │  → Финальный выбор инструмента
└───────────────────────────────┘
```

#### 2. Tool Quality Tracking

```python
# AnyTool автоматически отслеживает качество инструментов
{
    "tool_name": "get_market_items",
    "call_count": 150,
    "success_rate": 0.95,
    "avg_latency_ms": 450,
    "description_quality": 0.85,  # LLM-оценка описания
    "last_failure": "2025-12-10T15:30:00Z"
}
```

#### 3. Self-Healing Tool Management

При сбое инструмента AnyTool автоматически:
- Переключается на альтернативный инструмент
- Обновляет рейтинг качества
- Логирует инцидент

---

## 🔧 Часть 2: n8n Integration

### Что такое n8n?

**n8n** (произносится "nodemation") — это open-source visual workflow automation платформа с поддержкой 350+ интеграций и AI-агентов.

### Ключевые преимущества n8n

| Преимущество | Описание | Применение для бота |
|--------------|----------|---------------------|
| **Visual Builder** | Drag-and-drop создание workflows | DevOps, CI/CD |
| **350+ Integrations** | Готовые коннекторы | Telegram, Slack, DB |
| **AI Nodes** | OpenAI, Claude, LangChain | Intelligent trading |
| **Self-hosted** | Полный контроль данных | Security compliance |
| **Modular Design** | Переиспользуемые компоненты | Масштабирование |

### Архитектура n8n для бота

```
┌─────────────────────────────────────────────────────────────────┐
│                         n8n Workflows                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │  Telegram   │    │   DMarket   │    │  Database   │         │
│  │  Trigger    │───▶│   API Node  │───▶│   Store     │         │
│  └─────────────┘    └─────────────┘    └─────────────┘         │
│         │                                    │                  │
│         ▼                                    ▼                  │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │    AI       │    │   Filter    │    │   Notify    │         │
│  │  Analysis   │───▶│   Logic     │───▶│   User      │         │
│  └─────────────┘    └─────────────┘    └─────────────┘         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Примеры n8n Workflows

#### 1. Daily Trading Report Workflow

```json
{
  "name": "Daily Trading Report",
  "nodes": [
    {
      "name": "Schedule Trigger",
      "type": "n8n-nodes-base.scheduleTrigger",
      "parameters": {
        "rule": {
          "interval": [{"field": "hours", "hoursInterval": 24}]
        }
      }
    },
    {
      "name": "Get DMarket Balance",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "https://api.dmarket.com/account/v1/balance",
        "method": "GET",
        "authentication": "predefinedCredentialType",
        "nodeCredentialType": "dmarketApi"
      }
    },
    {
      "name": "Get Trade History",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "https://api.dmarket.com/marketplace-api/v1/user-offers/closed",
        "method": "GET"
      }
    },
    {
      "name": "AI Summarize",
      "type": "@n8n/n8n-nodes-langchain.openAi",
      "parameters": {
        "model": "gpt-4",
        "prompt": "Summarize trading performance: {{$json}}"
      }
    },
    {
      "name": "Send Telegram",
      "type": "n8n-nodes-base.telegram",
      "parameters": {
        "chatId": "{{$env.TELEGRAM_CHAT_ID}}",
        "text": "📊 Daily Report:\n{{$json.summary}}"
      }
    }
  ]
}
```

#### 2. Arbitrage Alert Workflow

```json
{
  "name": "Arbitrage Alert",
  "nodes": [
    {
      "name": "Webhook Trigger",
      "type": "n8n-nodes-base.webhook",
      "parameters": {
        "path": "arbitrage-alert"
      }
    },
    {
      "name": "Filter High Profit",
      "type": "n8n-nodes-base.filter",
      "parameters": {
        "conditions": {
          "number": [{
            "value1": "={{$json.profit_percent}}",
            "operation": "largerEqual",
            "value2": 10
          }]
        }
      }
    },
    {
      "name": "AI Risk Assessment",
      "type": "@n8n/n8n-nodes-langchain.openAi",
      "parameters": {
        "prompt": "Assess risk for this trade: {{$json}}"
      }
    },
    {
      "name": "Notify if Safe",
      "type": "n8n-nodes-base.telegram",
      "parameters": {
        "text": "🎯 Arbitrage Alert!\n{{$json.item}}\nProfit: {{$json.profit_percent}}%"
      }
    }
  ]
}
```

#### 3. CI/CD Integration Workflow

```json
{
  "name": "CI/CD Pipeline Notification",
  "nodes": [
    {
      "name": "GitHub Webhook",
      "type": "n8n-nodes-base.webhook",
      "parameters": {
        "path": "github-ci"
      }
    },
    {
      "name": "Check Build Status",
      "type": "n8n-nodes-base.if",
      "parameters": {
        "conditions": {
          "string": [{
            "value1": "={{$json.action}}",
            "value2": "completed"
          }]
        }
      }
    },
    {
      "name": "Notify Success",
      "type": "n8n-nodes-base.telegram",
      "parameters": {
        "text": "✅ CI passed: {{$json.workflow.name}}"
      }
    },
    {
      "name": "Notify Failure",
      "type": "n8n-nodes-base.telegram",
      "parameters": {
        "text": "❌ CI failed: {{$json.workflow.name}}\nCheck: {{$json.workflow.html_url}}"
      }
    }
  ]
}
```

### Настройка n8n

#### Docker Compose для n8n

```yaml
# docker-compose.n8n.yml
version: '3.8'
services:
  n8n:
    image: n8nio/n8n:latest
    restart: always
    ports:
      - "5678:5678"
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=${N8N_USER}
      - N8N_BASIC_AUTH_PASSWORD=${N8N_PASSWORD}
      - N8N_ENCRYPTION_KEY=${N8N_ENCRYPTION_KEY}
      - WEBHOOK_URL=https://your-domain.com/
    volumes:
      - n8n_data:/home/node/.n8n
    networks:
      - bot-network

volumes:
  n8n_data:

networks:
  bot-network:
    external: true
```

#### DMarket API Credentials в n8n

```json
{
  "name": "DMarket API",
  "type": "httpHeaderAuth",
  "data": {
    "X-Api-Key": "{{$credentials.publicKey}}",
    "X-Sign-Date": "{{$now.unix}}",
    "X-Request-Sign": "{{hmac('sha256', $credentials.secretKey, $signString)}}"
  }
}
```

---

## 🔗 Часть 3: GitHub Copilot Integration

### Улучшение GitHub Copilot с AnyTool

#### MCP Integration для VS Code

```json
// .vscode/settings.json
{
  "github.copilot.advanced": {
    "mcpServers": {
      "dmarket": {
        "command": "python",
        "args": ["-m", "src.mcp_server.dmarket_mcp"]
      }
    }
  }
}
```

#### Copilot Agent Mode + AnyTool

```python
# Пример использования с GitHub Copilot Background Agent
async def copilot_assisted_trading():
    """
    Copilot может использовать AnyTool для:
    - Анализа рынка
    - Создания таргетов
    - Отчетности
    """
    async with AnyTool(config=safe_config) as tool:
        # Copilot может запросить эту задачу
        result = await tool.execute(
            "Проанализируй рынок CS:GO и найди 5 лучших "
            "арбитражных возможностей с прибылью >10%"
        )
        return result
```

### Преимущества интеграции

| Компонент | Без интеграции | С AnyTool + n8n |
|-----------|---------------|-----------------|
| Tool Selection | Ручной | Smart RAG автоматический |
| Error Recovery | Manual retry | Self-healing |
| Workflow Creation | Code-only | Visual + Code |
| Monitoring | Basic logs | Full audit trail |
| Multi-agent | Сложно | Встроенная поддержка |

---

## 📋 План внедрения

### Phase 1: MCP Server (2-3 дня) ✅ ЗАВЕРШЕНО

- [x] Создать `src/mcp_server/dmarket_mcp.py`
- [x] Настроить AnyTool config без GUI/Web
- [x] Создать `src/utils/anytool_integration.py`
- [x] Документация MCP методов

### Phase 2: AnyTool Integration (1 неделя) ✅ БАЗОВАЯ РЕАЛИЗАЦИЯ

- [x] Интегрировать AnyTool в бота (fallback режим)
- [x] Настроить безопасную конфигурацию (DMarket ToS compliance)
- [ ] Настроить Smart Tool RAG (требует установки AnyTool)
- [ ] Включить Quality Tracking
- [x] Добавить logging и мониторинг

### Phase 3: n8n Workflows (1-2 недели)

- [ ] Развернуть n8n в Docker
- [ ] Создать базовые workflows:
  - Daily Reports
  - Arbitrage Alerts
  - CI/CD Notifications
- [ ] Интегрировать с Telegram ботом
- [ ] Настроить AI nodes

### Phase 4: Production (ongoing)

- [ ] Performance tuning
- [ ] Security audit
- [ ] Расширение workflows
- [ ] Мониторинг и алерты

---

## 🚀 Быстрый старт

### Установка AnyTool

```bash
# AnyTool не на PyPI, устанавливаем с GitHub
pip install git+https://github.com/HKUDS/AnyTool.git
```

### Использование MCP Server

```python
# Запуск MCP сервера напрямую
python -m src.mcp_server.dmarket_mcp

# Или через Python
from src.mcp_server.dmarket_mcp import create_dmarket_mcp_server

server = create_dmarket_mcp_server(dry_run=True)
tools = await server.list_tools()
result = await server.call_tool("get_balance", {})
```

### Использование AnyTool Integration

```python
from src.utils.anytool_integration import (
    execute_safe_task,
    get_anytool_status,
)

# Проверить статус интеграции
status = get_anytool_status()
print(f"AnyTool installed: {status['is_installed']}")
print(f"MCP Server available: {status['mcp_server_available']}")

# Выполнить задачу безопасно
result = await execute_safe_task(
    "Найди арбитражные возможности для CS:GO",
    dry_run=True
)
print(result)
```

---

## ⚠️ Важные ограничения

### Строго запрещено (DMarket ToS)

```python
# ❌ ЗАПРЕЩЕНО - нарушает ToS
config = AnyToolConfig(
    backend_scope=["mcp", "shell", "gui", "web"]  # GUI и Web ЗАПРЕЩЕНЫ
)

# ❌ ЗАПРЕЩЕНО - browser automation
await tool.execute("Открой браузер и зайди на dmarket.com")

# ❌ ЗАПРЕЩЕНО - web scraping
await tool.execute("Спарси цены со страницы dmarket.com/items")
```

### Разрешенные операции

```python
# ✅ РАЗРЕШЕНО - через официальный API
await tool.execute("Получи предметы через DMarket Trading API")

# ✅ РАЗРЕШЕНО - локальный анализ
await tool.execute("Проанализируй данные из базы данных")

# ✅ РАЗРЕШЕНО - shell operations
await tool.execute("Запусти pytest для проверки кода")
```

---

## 📚 Ресурсы

### AnyTool
- [GitHub: HKUDS/AnyTool](https://github.com/HKUDS/AnyTool)
- [MCP Documentation](https://modelcontextprotocol.io/)

### n8n
- [n8n Documentation](https://docs.n8n.io/)
- [freeCodeCamp Tutorial](https://www.freecodecamp.org/news/learn-n8n-to-design-develop-and-deploy-production-grade-ai-agents/)
- [n8n AI Workflows](https://www.freecodecamp.org/news/how-to-build-ai-workflows-with-n8n/)

### DMarket
- [Trading API Documentation](https://docs.dmarket.com/v1/swagger.html)
- [Terms of Service](https://dmarket.com/terms-of-use)

---

## 📝 Changelog

### v1.0 (Декабрь 2025)
- Начальная версия руководства
- Анализ AnyTool совместимости
- n8n workflow примеры
- План внедрения
- DMarket ToS compliance матрица
