# 🚀 DMarket Bot - Development Container

This directory contains configuration files for GitHub Codespaces and VS Code Dev Containers.

## 📋 Contents

```
.devcontainer/
├── devcontainer.json       # Main configuration
├── Dockerfile              # Development container image
├── docker-compose.yml      # Services (PostgreSQL, Redis)
├── README.md               # This file
├── scripts/
│   ├── onCreate.sh         # Runs once when container is created
│   ├── postCreate.sh       # Runs after creation, installs dependencies
│   └── postStart.sh        # Runs each time container starts
└── init-scripts/
    └── postgres/
        └── 01-init-databases.sh  # PostgreSQL initialization
```

## 🎯 Quick Start

### GitHub Codespaces

1. Click the green **"Code"** button on the repository
2. Select **"Codespaces"** tab
3. Click **"Create codespace on main"**
4. Wait for the environment to build (~2-5 minutes)

### VS Code Dev Containers

1. Install [Docker Desktop](https://www.docker.com/products/docker-desktop)
2. Install [VS Code](https://code.visualstudio.com/) with the [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)
3. Clone the repository:
   ```bash
   git clone https://github.com/Dykij/DMarket-Telegram-Bot.git
   cd DMarket-Telegram-Bot
   ```
4. Open in VS Code: `code .`
5. Press `F1` and select **"Dev Containers: Reopen in Container"**

## 🛠️ Included Services

| Service | Port | Description |
|---------|------|-------------|
| PostgreSQL | 5432 | Main database |
| Redis | 6379 | Cache & rate limiting |
| Adminer | 8081 | Database UI (optional) |
| Redis Commander | 8082 | Redis UI (optional) |

### Starting Optional Services

```bash
# Start Adminer and Redis Commander
docker compose -f .devcontainer/docker-compose.yml --profile tools up -d
```

## 🔧 Environment Configuration

After the container starts:

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Update `.env` with your credentials:
   ```env
   TELEGRAM_BOT_TOKEN=your_actual_token
   DMARKET_PUBLIC_KEY=your_public_key
   DMARKET_SECRET_KEY=your_secret_key
   ```

3. The following are pre-configured for development:
   - `DATABASE_URL=postgresql://dmarket_user:dmarket_password@postgres:5432/dmarket_bot`
   - `REDIS_URL=redis://redis:6379/0`
   - `DRY_RUN=true` (safe mode enabled)

## 📦 Installed Tools

### Python Development
- Python 3.12
- Ruff (linting & formatting)
- MyPy (type checking)
- pytest (testing)
- pre-commit hooks

### Utilities
- Git & Git LFS
- GitHub CLI (`gh`)
- Docker & Docker Compose
- PostgreSQL client
- Redis CLI
- ripgrep, fd, fzf, bat, jq

## 🎨 VS Code Extensions

All recommended extensions are automatically installed:

- **Python**: Python, Pylance, debugpy, Ruff, MyPy
- **Testing**: Test Explorer
- **Docker**: Docker, Dev Containers
- **Git**: GitLens, GitHub Pull Requests
- **Database**: SQLTools with PostgreSQL/SQLite drivers
- **Productivity**: Error Lens, Todo Tree, Material Icons
- **GitHub Copilot**: Copilot & Copilot Chat

## 🧪 Running Tests

```bash
# All tests
make test

# With coverage
make test-cov

# Fast tests (timeout 10s)
make test-fast

# Specific test file
pytest tests/unit/test_dmarket_api.py -v
```

## 📝 Code Quality

```bash
# Lint check
make lint

# Auto-fix issues
make fix

# Full check (lint + types + format)
make check

# Quality assurance (all checks + tests)
make qa
```

## 🚀 Running the Bot

```bash
# Start the bot (DRY_RUN=true by default)
make run

# Or directly
python -m src.main
```

## 🗄️ Database Access

### Using SQLTools (VS Code)

SQLTools is pre-configured with the PostgreSQL connection. Look for the database icon in the sidebar.

### Using psql

```bash
psql -h postgres -U dmarket_user -d dmarket_bot
```

### Using Adminer (Web UI)

Start the tools profile and open http://localhost:8081:
- System: PostgreSQL
- Server: postgres
- Username: dmarket_user
- Password: dmarket_password
- Database: dmarket_bot

## 🔄 Rebuilding the Container

If you need to rebuild:

1. In VS Code: `F1` → **"Dev Containers: Rebuild Container"**
2. In Codespaces: Click the gear icon → **"Rebuild codespace"**

## ❓ Troubleshooting

### Container won't start
- Check Docker is running
- Try rebuilding: `F1` → "Dev Containers: Rebuild Container Without Cache"

### PostgreSQL connection refused
- Wait a few seconds for the database to initialize
- Check logs: `docker compose logs postgres`

### Python packages missing
- Rerun: `pip install -r requirements.txt`
- Or: `make install`

### Permission denied on scripts
```bash
chmod +x .devcontainer/scripts/*.sh
```

## 📚 More Information

- [Main Documentation](../docs/README.md)
- [Quick Start Guide](../docs/QUICK_START.md)
- [Contributing Guide](../CONTRIBUTING.md)
- [Security Guidelines](../SECURITY.md)

---

**Happy coding! 🎉**
