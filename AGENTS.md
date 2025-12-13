# AGENTS.md — DMarket Telegram Bot

> 📖 Этот файл предоставляет инструкции для AI-агентов (Cursor, Devin, Windsurf, Aider, Codex и др.)
> Полная документация: `.github/copilot-instructions.md`

## 🎯 Обзор проекта

**DMarket Telegram Bot** — enterprise-grade асинхронное Python-приложение для автоматизации торговли игровыми предметами на платформе DMarket.

| Параметр | Значение |
|----------|----------|
| **Python** | 3.11+ (3.12 рекомендуется) |
| **Async** | Везде для I/O операций |
| **Тесты** | 2688/2688 ✅ |
| **Покрытие** | 85%+ (цель) |

## ⚠️ Критические правила

### 1. Английская раскладка в терминале
```bash
# ✅ Правильно
pytest tests/
ruff check src/

# ❌ НЕПРАВИЛЬНО (кириллица!)
руtеst tests/   # р, у, е - русские буквы
```

### 2. Async/await обязательно
```python
# ✅ Правильно
async def fetch_data() -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()

# ❌ Неправильно - синхронный код для I/O
def fetch_data():
    return requests.get(url).json()
```

### 3. Type hints везде
```python
# ✅ Правильно
async def get_balance(user_id: int) -> dict[str, float]:
    ...

# ❌ Неправильно
async def get_balance(user_id):
    ...
```

### 4. Тесты для каждого изменения
- AAA паттерн (Arrange-Act-Assert)
- `@pytest.mark.asyncio` для async тестов
- Покрытие 80%+ для новых файлов

## 🛠️ Основные команды

```bash
# Линтинг и форматирование
ruff check src/ tests/ --fix
ruff format src/ tests/

# Проверка типов
mypy src/

# Тесты
pytest tests/ -v
pytest --cov=src --cov-report=html

# Запуск бота
python -m src.main
```

## 📁 Модульные инструкции

Для специфики отдельных модулей см. вложенные AGENTS.md:

| Модуль | Файл | Описание |
|--------|------|----------|
| DMarket API | `src/dmarket/AGENTS.md` | API клиент, цены в центах, rate limiting |
| Telegram Bot | `src/telegram_bot/AGENTS.md` | Handlers, клавиатуры, локализация |
| Тесты | `tests/AGENTS.md` | AAA паттерн, VCR.py, Pact contracts |

## 📚 Документация

- **Полные инструкции**: `.github/copilot-instructions.md` (1000+ строк)
- **Архитектура**: `docs/ARCHITECTURE.md`
- **API DMarket**: `docs/DMARKET_API_FULL_SPEC.md`
- **Арбитраж**: `docs/ARBITRAGE.md`
- **Тестирование**: `docs/testing_guide.md`

## 🔗 Ссылки

- [DMarket API Docs](https://docs.dmarket.com/)
- [python-telegram-bot](https://docs.python-telegram-bot.org/)
- [Ruff](https://docs.astral.sh/ruff/)
- [MyPy](https://mypy.readthedocs.io/)

---

*Файл соответствует стандарту [AGENTS.md](https://agents.md) для совместимости с AI-агентами.*
