# Documentation Context Prompt

> Используй этот промпт для автоматического подключения документации к запросам

## Быстрый доступ к документации

При работе с кодом, всегда учитывай соответствующую документацию:

### По типу файла

| Путь | Документация |
|------|--------------|
| `src/dmarket/**` | `docs/DMARKET_API_FULL_SPEC.md`, `docs/ARBITRAGE.md` |
| `src/waxpeer/**` | `docs/WAXPEER_API_SPEC.md`, `docs/WAXPEER_INTEGRATION_GUIDE.md` |
| `src/telegram_bot/**` | `docs/TELEGRAM_BOT_API.md`, `docs/SIMPLIFIED_MENU_GUIDE.md` |
| `src/ml/**` | `docs/ML_AI_GUIDE.md`, `docs/ML_AI_IMPROVEMENTS_GUIDE.md` |
| `tests/**` | `docs/TESTING_COMPLETE_GUIDE.md`, `docs/CONTRACT_TESTING.md` |
| `.github/workflows/**` | `docs/CI_CD_GUIDE.md` |

### По задаче

| Задача | Документация |
|--------|--------------|
| Арбитраж | `docs/ARBITRAGE.md`, `docs/DUAL_STRATEGY_ARBITRAGE_GUIDE.md` |
| Обработка ошибок | `docs/ERROR_HANDLING_COMPLETE_GUIDE.md` |
| Кэширование | `docs/CACHING_GUIDE.md` |
| Уведомления | `docs/NOTIFICATIONS_GUIDE.md` |
| Безопасность | `docs/SECURITY.md` |
| Производительность | `docs/PERFORMANCE_COMPLETE_GUIDE.md` |

## Ключевые правила из документации

### DMARKET_API_FULL_SPEC.md
- Цены всегда в **ЦЕНТАХ** (price: 1000 = $10.00)
- HMAC-SHA256 авторизация
- Rate limit: 30 req/min

### WAXPEER_API_SPEC.md
- Цены в **МИЛАХ** (1 USD = 1000 mils)
- Комиссия продавца: 6%
- Steam trade link обязателен

### ARBITRAGE.md
- 5 уровней: boost, standard, medium, advanced, pro
- Минимальный профит для каждого уровня
- Проверка ликвидности обязательна

### TESTING_COMPLETE_GUIDE.md
- AAA паттерн: Arrange-Act-Assert
- pytest-asyncio для async тестов
- VCR.py для HTTP записей
- Pact для контрактного тестирования
