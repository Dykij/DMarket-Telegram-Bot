# README для Sphinx Documentation

## Быстрый старт

### Установка зависимостей

```bash
cd docs-sphinx
pip install -r requirements.txt
```

### Генерация документации

```bash
# Сборка HTML документации
sphinx-build -b html . _build/html

# Или с помощью make (если есть Makefile)
make html
```

### Просмотр

Откройте `_build/html/index.html` в браузере.

## Автоматическая генерация из кода

```bash
# Генерация .rst файлов из Python модулей
sphinx-apidoc -o api ../src/
```

## Структура

```
docs-sphinx/
├── conf.py              # Конфигурация Sphinx
├── index.rst            # Главная страница
├── requirements.txt     # Зависимости
├── api/                 # API документация
│   └── telegram_bot.rst
├── _static/             # Статические файлы
├── _templates/          # Шаблоны
└── _build/              # Собранная документация (генерируется)
    └── html/
```

## Интеграция с MkDocs

Можно интегрировать Sphinx и MkDocs:

- **Sphinx** для API Reference
- **MkDocs** для User Guides

Оба доступны на разных URL или через навигацию.
