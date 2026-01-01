# README Badges - Quick Reference
# Добавьте эти badges в начало вашего README.md

## Основные Badges

### Status Badges
```markdown
![Build Status](https://img.shields.io/github/actions/workflow/status/Dykij/DMarket-Telegram-Bot/ci.yml?branch=main&label=build&logo=github)
![Tests](https://img.shields.io/github/actions/workflow/status/Dykij/DMarket-Telegram-Bot/python-tests.yml?branch=main&label=tests&logo=pytest)
![CodeQL](https://img.shields.io/github/actions/workflow/status/Dykij/DMarket-Telegram-Bot/codeql.yml?label=CodeQL&logo=github)
```

### Code Quality
```markdown
![Code Coverage](https://img.shields.io/codecov/c/github/Dykij/DMarket-Telegram-Bot?logo=codecov)
![Code Quality](https://img.shields.io/codefactor/grade/github/Dykij/DMarket-Telegram-Bot?logo=codefactor)
![Ruff](https://img.shields.io/badge/linter-ruff-yellow?logo=ruff)
![MyPy](https://img.shields.io/badge/type--checked-mypy-blue?logo=python)
```

### Project Info
```markdown
![Python Version](https://img.shields.io/badge/python-3.11%2B%20%7C%203.12-blue?logo=python&logoColor=white)
![License](https://img.shields.io/github/license/Dykij/DMarket-Telegram-Bot?color=blue)
![Version](https://img.shields.io/github/v/release/Dykij/DMarket-Telegram-Bot?label=version)
```

### Community
```markdown
![Stars](https://img.shields.io/github/stars/Dykij/DMarket-Telegram-Bot?style=social)
![Forks](https://img.shields.io/github/forks/Dykij/DMarket-Telegram-Bot?style=social)
![Issues](https://img.shields.io/github/issues/Dykij/DMarket-Telegram-Bot)
![Pull Requests](https://img.shields.io/github/issues-pr/Dykij/DMarket-Telegram-Bot)
![Contributors](https://img.shields.io/github/contributors/Dykij/DMarket-Telegram-Bot)
```

### Activity
```markdown
![Last Commit](https://img.shields.io/github/last-commit/Dykij/DMarket-Telegram-Bot)
![Commit Activity](https://img.shields.io/github/commit-activity/m/Dykij/DMarket-Telegram-Bot)
![Repo Size](https://img.shields.io/github/repo-size/Dykij/DMarket-Telegram-Bot)
```

### Dependencies
```markdown
![Dependencies](https://img.shields.io/librariesio/github/Dykij/DMarket-Telegram-Bot)
![Dependabot](https://img.shields.io/badge/dependabot-enabled-success?logo=dependabot)
```

## Рекомендуемое размещение в README.md

```markdown
<div align="center">

# DMarket Telegram Bot 🤖

[![Build Status](https://img.shields.io/github/actions/workflow/status/Dykij/DMarket-Telegram-Bot/ci.yml?branch=main)](https://github.com/Dykij/DMarket-Telegram-Bot/actions)
[![Tests](https://img.shields.io/github/actions/workflow/status/Dykij/DMarket-Telegram-Bot/python-tests.yml?branch=main&label=tests)](https://github.com/Dykij/DMarket-Telegram-Bot/actions)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B%20%7C%203.12-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/github/license/Dykij/DMarket-Telegram-Bot)](LICENSE)

[![Stars](https://img.shields.io/github/stars/Dykij/DMarket-Telegram-Bot?style=social)](https://github.com/Dykij/DMarket-Telegram-Bot/stargazers)
[![Forks](https://img.shields.io/github/forks/Dykij/DMarket-Telegram-Bot?style=social)](https://github.com/Dykij/DMarket-Telegram-Bot/network/members)
[![Issues](https://img.shields.io/github/issues/Dykij/DMarket-Telegram-Bot)](https://github.com/Dykij/DMarket-Telegram-Bot/issues)
[![Pull Requests](https://img.shields.io/github/issues-pr/Dykij/DMarket-Telegram-Bot)](https://github.com/Dykij/DMarket-Telegram-Bot/pulls)

**Автоматизированный торговый бот для DMarket с поддержкой многоуровневого арбитража**

[Начать работу](#quick-start) • [Документация](docs/README.md) • [Contributing](CONTRIBUTING.md) • [Discord](#)

</div>

---

## 📊 Статус проекта

| Метрика        | Значение                   |
| -------------- | -------------------------- |
| **Версия**     | 1.0.0                      |
| **Готовность** | 78% (39/50 задач)          |
| **Тесты**      | 2356/2356 ✅                |
| **Покрытие**   | 85%+ (цель)                |
| **Python**     | 3.11+ (3.12 рекомендуется) |

---
```

## Дополнительные специализированные badges

### Games Support
```markdown
![CS:GO](https://img.shields.io/badge/game-CS%3AGO%2FCS2-orange?logo=steam)
![Dota 2](https://img.shields.io/badge/game-Dota%202-red?logo=steam)
![TF2](https://img.shields.io/badge/game-TF2-yellow?logo=steam)
![Rust](https://img.shields.io/badge/game-Rust-brown?logo=steam)
```

### Features
```markdown
![Arbitrage](https://img.shields.io/badge/feature-5--level%20arbitrage-success)
![Real-time](https://img.shields.io/badge/monitoring-real--time-blue)
![Multilang](https://img.shields.io/badge/i18n-4%20languages-brightgreen)
![Docker](https://img.shields.io/badge/docker-supported-blue?logo=docker)
```

### Security
```markdown
![Security](https://img.shields.io/badge/security-encrypted%20keys-success?logo=security)
![Sentry](https://img.shields.io/badge/monitoring-sentry-purple?logo=sentry)
```

## После добавления badges:

1. **Включите Codecov** (для coverage badge):
   ```bash
   # В .github/workflows/python-tests.yml добавьте:
   - name: Upload coverage to Codecov
     uses: codecov/codecov-action@v4
     with:
       token: ${{ secrets.CODECOV_TOKEN }}
   ```

2. **Добавьте topics в GitHub**:
   - Settings → Topics → Добавить:
   - `trading-bot`, `dmarket`, `csgo`, `telegram-bot`, `arbitrage`
   - `python`, `asyncio`, `pytest`, `docker`

3. **Добавьте description**:
   - Settings → About → Description:
   - "Automated trading bot for DMarket with multi-level arbitrage, real-time monitoring, and smart notifications"

4. **Создайте Discussions**:
   - Settings → Features → Enable Discussions

## Примеры из популярных проектов:

### Minimal (рекомендуется для начала)
```markdown
![Build](https://img.shields.io/github/actions/workflow/status/Dykij/DMarket-Telegram-Bot/ci.yml)
![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)
![License](https://img.shields.io/github/license/Dykij/DMarket-Telegram-Bot)
```

### Full (максимальная информация)
```markdown
![Build](https://img.shields.io/github/actions/workflow/status/Dykij/DMarket-Telegram-Bot/ci.yml?branch=main&logo=github)
![Tests](https://img.shields.io/github/actions/workflow/status/Dykij/DMarket-Telegram-Bot/python-tests.yml?label=tests&logo=pytest)
![Coverage](https://img.shields.io/codecov/c/github/Dykij/DMarket-Telegram-Bot?logo=codecov)
![Python 3.11+](https://img.shields.io/badge/python-3.11%2B%20%7C%203.12-blue?logo=python)
![License](https://img.shields.io/github/license/Dykij/DMarket-Telegram-Bot)
![Stars](https://img.shields.io/github/stars/Dykij/DMarket-Telegram-Bot?style=social)
![Last Commit](https://img.shields.io/github/last-commit/Dykij/DMarket-Telegram-Bot)
```

---

**Совет**: Начните с minimal набора, затем добавляйте по мере роста проекта.
