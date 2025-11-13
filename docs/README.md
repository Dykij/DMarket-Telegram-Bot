# 📚 Документация DMarket Telegram Bot

**Дата обновления**: 13 ноября 2025 г.
**Версия проекта**: 1.1.0

---

## 🚀 Быстрый старт

- **[QUICK_START.md](QUICK_START.md)** - Запуск бота за 5 минут
- **[deployment.md](deployment.md)** - Полное руководство по развертыванию

---

## 📖 Основная документация

### Архитектура и структура

- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Архитектура проекта и принципы построения
- **[project_structure.md](project_structure.md)** - Структура файлов и директорий

### API и интеграции

- **[api_reference.md](api_reference.md)** - Справочник API методов
- **[DMARKET_API_FULL_SPEC.md](DMARKET_API_FULL_SPEC.md)** - Полная спецификация DMarket API
- **[rate_limiter_and_api_handling_guide.md](rate_limiter_and_api_handling_guide.md)** - Обработка ошибок и rate limiting

### Функциональность

- **[MULTI_LEVEL_ARBITRAGE_GUIDE.md](MULTI_LEVEL_ARBITRAGE_GUIDE.md)** - Многоуровневый арбитраж
- **[auto_arbitrage_guide.md](auto_arbitrage_guide.md)** - Автоматический арбитраж
- **[game_filters_guide.md](game_filters_guide.md)** - Фильтры для игр
- **[arbitrage_filters_guide.md](arbitrage_filters_guide.md)** - Фильтрация арбитражных возможностей
- **[sales_analysis_guide.md](sales_analysis_guide.md)** - Анализ продаж
- **[realtime_price_monitoring.md](realtime_price_monitoring.md)** - Мониторинг цен в реальном времени

---

## 🛠️ Разработка

### Настройка окружения

- **[vscode_setup.md](vscode_setup.md)** - Настройка VS Code
- **[docker_guide.md](docker_guide.md)** - Использование Docker

### Качество кода

- **[code_quality_tools_guide.md](code_quality_tools_guide.md)** - Инструменты качества кода (Ruff, Black, MyPy)
- **[testing_guide.md](testing_guide.md)** - Руководство по тестированию

### Логирование и обработка ошибок

- **[logging_and_error_handling.md](logging_and_error_handling.md)** - Логирование и обработка исключений

---

## 🤝 Вклад в проект

- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Как внести вклад
- **[CHANGELOG.md](CHANGELOG.md)** - История изменений

---

## 🔒 Безопасность

- **[SECURITY.md](SECURITY.md)** - Руководство по безопасности

---

## 💬 Telegram Bot

- **[telegram_bot_guide.md](telegram_bot_guide.md)** - Руководство по Telegram боту
- **[localization_guide.md](localization_guide.md)** - Локализация и языки

---

## 📊 Производительность

- **[PERFORMANCE_IMPROVEMENTS.md](PERFORMANCE_IMPROVEMENTS.md)** - Оптимизация производительности

---

## 🎯 Полезные ссылки

- **GitHub репозиторий**: <https://github.com/yourusername/BotDmarket>
- **DMarket API**: <https://docs.dmarket.com/>
- **Telegram Bot API**: <https://core.telegram.org/bots/api>

---

## 📋 Структура документации

```
docs/
├── README.md                           # Этот файл (индекс документации)
│
├── 🚀 Быстрый старт
│   ├── QUICK_START.md                 # Запуск за 5 минут
│   └── deployment.md                  # Развертывание
│
├── 📖 Основная документация
│   ├── ARCHITECTURE.md                # Архитектура проекта
│   ├── project_structure.md           # Структура файлов
│   ├── api_reference.md               # API методы
│   ├── DMARKET_API_FULL_SPEC.md      # DMarket API спецификация
│   └── rate_limiter_and_api_handling_guide.md
│
├── 🎯 Функциональность
│   ├── MULTI_LEVEL_ARBITRAGE_GUIDE.md # Многоуровневый арбитраж
│   ├── auto_arbitrage_guide.md        # Автоматический арбитраж
│   ├── game_filters_guide.md          # Фильтры игр
│   ├── arbitrage_filters_guide.md     # Фильтрация арбитража
│   ├── sales_analysis_guide.md        # Анализ продаж
│   └── realtime_price_monitoring.md   # Мониторинг цен
│
├── 🛠️ Разработка
│   ├── code_quality_tools_guide.md    # Ruff, Black, MyPy
│   ├── testing_guide.md               # Тестирование
│   ├── logging_and_error_handling.md  # Логирование
│   ├── vscode_setup.md                # Настройка VS Code
│   └── docker_guide.md                # Docker
│
├── 🤝 Вклад
│   ├── CONTRIBUTING.md                # Как помочь проекту
│   └── CHANGELOG.md                   # История изменений
│
├── 🔒 Безопасность
│   └── SECURITY.md                    # Безопасность
│
├── 💬 Telegram Bot
│   ├── telegram_bot_guide.md          # Руководство по боту
│   └── localization_guide.md          # Локализация
│
├── 📊 Производительность
│   └── PERFORMANCE_IMPROVEMENTS.md    # Оптимизация
│
└── source/                            # Sphinx documentation
    ├── conf.py
    ├── index.rst
    └── ...
```

---

## 🔍 Поиск в документации

### По темам

#### Начало работы

- Установка и запуск → [QUICK_START.md](QUICK_START.md)
- Развертывание → [deployment.md](deployment.md)
- Настройка окружения → [vscode_setup.md](vscode_setup.md)

#### API и интеграции

- Методы API → [api_reference.md](api_reference.md)
- DMarket API → [DMARKET_API_FULL_SPEC.md](DMARKET_API_FULL_SPEC.md)
- Обработка ошибок → [rate_limiter_and_api_handling_guide.md](rate_limiter_and_api_handling_guide.md)

#### Арбитраж

- Многоуровневый → [MULTI_LEVEL_ARBITRAGE_GUIDE.md](MULTI_LEVEL_ARBITRAGE_GUIDE.md)
- Автоматический → [auto_arbitrage_guide.md](auto_arbitrage_guide.md)
- Фильтры → [arbitrage_filters_guide.md](arbitrage_filters_guide.md)

#### Разработка

- Качество кода → [code_quality_tools_guide.md](code_quality_tools_guide.md)
- Тестирование → [testing_guide.md](testing_guide.md)
- Безопасность → [SECURITY.md](SECURITY.md)

---

## 📝 Обновления документации

Последние обновления (13 ноября 2025 г.):

- ✅ Добавлен SECURITY.md - руководство по безопасности
- ✅ Добавлен ARCHITECTURE.md - архитектура проекта
- ✅ Добавлен README.md - индекс документации
- ✅ Удалены устаревшие документы:
  - CODE_QUALITY_IMPROVEMENTS.md (дублировался)
  - GITHUB_UPLOAD_GUIDE.md (устарело)
  - IMPLEMENTATION_PLAN.md (реализовано)
  - INTEGRATION_CHECKLIST.md (устарело)
  - ci_cd_setup.md (дублируется в code_quality_tools_guide.md)
  - REFACTORING.md (устарело)
  - RUFF_USAGE.md (дублируется в code_quality_tools_guide.md)
- ✅ Обновлен CHANGELOG.md с актуальной информацией

---

## 💡 Как использовать документацию

### Для новых пользователей

1. Начните с [QUICK_START.md](QUICK_START.md)
2. Изучите [MULTI_LEVEL_ARBITRAGE_GUIDE.md](MULTI_LEVEL_ARBITRAGE_GUIDE.md)
3. Прочитайте [telegram_bot_guide.md](telegram_bot_guide.md)

### Для разработчиков

1. Изучите [ARCHITECTURE.md](ARCHITECTURE.md)
2. Настройте окружение по [vscode_setup.md](vscode_setup.md)
3. Следуйте [CONTRIBUTING.md](CONTRIBUTING.md)
4. Прочитайте [code_quality_tools_guide.md](code_quality_tools_guide.md)

### Для администраторов

1. Изучите [deployment.md](deployment.md)
2. Прочитайте [SECURITY.md](SECURITY.md)
3. Настройте мониторинг по [logging_and_error_handling.md](logging_and_error_handling.md)

---

## 🆘 Поддержка

Если вы не нашли ответ на свой вопрос в документации:

1. Проверьте [Issues на GitHub](https://github.com/yourusername/BotDmarket/issues)
2. Создайте новый Issue с меткой `documentation`
3. Свяжитесь с разработчиками

---

**Документация постоянно обновляется. Предложения по улучшению приветствуются!**
