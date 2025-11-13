# 🔍 GitHub Actions Monitor - Quick Reference

## Быстрый запуск

### Рекомендуемый способ (с wrapper-скриптом)

**Windows PowerShell:**
```powershell
.\scripts\run_monitor.ps1
```

**Linux/macOS:**
```bash
chmod +x scripts/run_monitor.sh  # Только первый раз
./scripts/run_monitor.sh
```

### Альтернативный способ (напрямую)

```bash
# Установка зависимостей (один раз)
pip install httpx rich

# Windows (с настройкой кодировки)
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
python scripts/github_actions_monitor.py

# Linux/macOS
python scripts/github_actions_monitor.py

# С GitHub Token для снятия rate limit
export GITHUB_TOKEN=your_token  # Linux/Mac
$env:GITHUB_TOKEN="your_token"   # Windows PowerShell
```

## Что получаете

✅ **Консольный вывод**:

- Общая статистика workflows
- Success rate по каждому workflow
- Цветовая индикация проблем

✅ **Детальный отчет** в `build/reports/`:

- Полный анализ всех запусков
- Список ошибок с прямыми ссылками
- Конкретные рекомендации по улучшению
- План действий с приоритетами

## Как читать результаты

### Success Rate

- 🟢 **95-100%** - Отлично, все работает
- 🟡 **80-95%** - Хорошо, но есть нестабильность
- 🔴 **<80%** - КРИТИЧНО, требуется исправление

### Статус workflows

- **🟢 Отлично** - Стабильный, проблем нет
- **🟡 Хорошо** - Работает, но иногда падает
- **🔴 Требует внимания** - Часто падает, нужно чинить

## План действий после получения отчета

### 1. Проверьте отчет (5 мин)

```bash
# Откройте последний отчет
code build/reports/github_actions_report_*.md
```

### 2. Изучите ошибки (10 мин)

- Найдите секцию "❌ Недавние Ошибки"
- Кликните на URL для просмотра логов
- Определите паттерны ошибок

### 3. Исправьте критичные проблемы (30-60 мин)

Приоритеты:

1. **Failing tests** - исправить в первую очередь
2. **Missing dependencies** - добавить в requirements.txt
3. **Configuration issues** - обновить config файлы

### 4. Запустите снова для проверки

```bash
# После исправлений
git add .
git commit -m "fix: resolve GitHub Actions issues"
git push

# Подождите 5-10 минут
# Запустите монитор снова
python scripts/github_actions_monitor.py
```

## Автоматизация

### Ежедневный мониторинг

#### Windows Task Scheduler

```powershell
# Создайте scheduled task
$action = New-ScheduledTaskAction -Execute "python" -Argument "scripts/github_actions_monitor.py" -WorkingDirectory "D:\BotDmarket-master"
$trigger = New-ScheduledTaskTrigger -Daily -At 9am
Register-ScheduledTask -Action $action -Trigger $trigger -TaskName "GitHub Actions Monitor"
```

#### Linux/Mac cron

```bash
# Добавьте в crontab
0 9 * * * cd /path/to/project && python scripts/github_actions_monitor.py
```

## Полезные команды

```bash
# Посмотреть все отчеты
ls build/reports/

# Открыть последний отчет
code build/reports/$(ls -t build/reports/ | head -1)

# Сравнить два отчета
diff build/reports/report1.md build/reports/report2.md

# Удалить старые отчеты (>30 дней)
find build/reports/ -name "*.md" -mtime +30 -delete
```

## Troubleshooting

### "Rate limit exceeded"

**Решение**: Используйте GitHub Token

```bash
# Создайте токен: https://github.com/settings/tokens
export GITHUB_TOKEN=ghp_xxxxx
```

### "No module named 'httpx'"

**Решение**: Установите зависимости

```bash
pip install httpx rich
```

### "Repository not found"

**Решение**: Проверьте настройки в скрипте (строки 111-112)

## Дополнительная информация

📖 Полная документация: `docs/github_actions_monitoring.md`
🔗 GitHub Actions: <https://github.com/Dykij/DMarket-Telegram-Bot/actions>
