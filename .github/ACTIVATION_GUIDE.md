# 🚀 Инструкция по активации GitHub Copilot Agent

**Дата:** 14 декабря 2025
**Статус:** ⏳ Требует ручной активации

---

## ✅ Что уже сделано

- [x] Создано виртуальное окружение `.venv`
- [x] Установлены зависимости из `requirements.txt`
- [x] Созданы 4 workflow файла
- [x] Написаны инструкции для агента (389 строк)
- [x] Создано полное руководство (529 строк)
- [x] Определены 5 кастомных агентов
- [x] Подготовлены 4 issue шаблона
- [x] Сделан коммит в git

---

## 📋 Что нужно сделать вручную

### 1. Установить GitHub CLI (если нужно)

**Windows:**
```powershell
# Через winget
winget install --id GitHub.cli

# Через Chocolatey
choco install gh

# Через Scoop
scoop install gh
```

**После установки:**
```bash
gh auth login
```

### 2. Создать labels в репозитории

**Вариант А: Через GitHub CLI (если установлен)**
```bash
cd D:\DMarket-Telegram-Bot-main

gh label create "copilot-task" --color "0E8A16" --description "Task for GitHub Copilot Coding Agent"
gh label create "copilot-test" --color "1D76DB" --description "Test coverage improvement task"
gh label create "copilot-refactor" --color "FBCA04" --description "Code refactoring task"
gh label create "copilot-docs" --color "5319E7" --description "Documentation update task"
gh label create "copilot-security" --color "D93F0B" --description "Security fix task"
gh label create "copilot-bugfix" --color "EE0701" --description "Bug fix task"
```

**Вариант Б: Через веб-интерфейс GitHub**

1. Открыть: https://github.com/Dykij/DMarket-Telegram-Bot/labels
2. Нажать "New label" для каждого:

| Название         | Цвет                    | Описание                             |
| ---------------- | ----------------------- | ------------------------------------ |
| copilot-task     | #0E8A16 (зелёный)       | Task for GitHub Copilot Coding Agent |
| copilot-test     | #1D76DB (синий)         | Test coverage improvement task       |
| copilot-refactor | #FBCA04 (жёлтый)        | Code refactoring task                |
| copilot-docs     | #5319E7 (фиолетовый)    | Documentation update task            |
| copilot-security | #D93F0B (красный)       | Security fix task                    |
| copilot-bugfix   | #EE0701 (тёмно-красный) | Bug fix task                         |

### 3. Активировать GitHub Copilot Agent

**Шаги:**
1. Открыть: https://github.com/Dykij/DMarket-Telegram-Bot/settings
2. Перейти в: **Code and automation → Copilot**
3. Найти опцию: **"Enable Copilot coding agent"**
4. Включить её ✅

**Требования:**
- Подписка GitHub Copilot Pro, Pro+, Business или Enterprise
- Владелец репозитория должен иметь права администратора

### 4. Настроить GitHub Actions permissions

**Шаги:**
1. Открыть: https://github.com/Dykij/DMarket-Telegram-Bot/settings/actions
2. В разделе **Workflow permissions** выбрать:
   - ✅ **Read and write permissions**
3. В разделе **Fork pull request workflows** включить:
   - ✅ **Allow GitHub Actions to create and approve pull requests**

**Важно:** Эти права нужны для workflows, которые создают PR автоматически.

### 5. Push коммита в GitHub

```bash
cd D:\DMarket-Telegram-Bot-main

# Проверить статус
git status

# Push в main
git push origin main
```

### 6. Проверить workflows

После push:
1. Открыть: https://github.com/Dykij/DMarket-Telegram-Bot/actions
2. Проверить что workflows появились:
   - ✅ Copilot Coding Agent Setup
   - ✅ Copilot Scheduled Tasks
   - ✅ Copilot Security Audit
   - ✅ Copilot Issue Templates

### 7. Создать тестовое issue

**Через веб-интерфейс:**
1. Открыть: https://github.com/Dykij/DMarket-Telegram-Bot/issues/new/choose
2. Выбрать: **"Copilot Task"**
3. Заполнить шаблон:
   ```markdown
   ## 📋 Описание задачи
   Проверка работы Copilot Agent

   ## 🎯 Цель
   Убедиться что агент корректно отвечает

   ## 📁 Затрагиваемые файлы
   - `README.md`

   ## ✅ Требования
   1. Добавить секцию "GitHub Copilot Integration" в README.md
   2. Описать как использовать Background Agent

   ## ✔️ Критерии успеха
   - [ ] Секция добавлена
   - [ ] Примеры использования добавлены
   ```
4. Добавить label: **copilot-task**
5. Assignee: **@copilot** (если доступно)
6. Создать issue

**Через GitHub CLI (если установлен):**
```bash
gh issue create \
  --title "@copilot: Add Copilot integration docs to README" \
  --label "copilot-task" \
  --body "Add a new section describing GitHub Copilot Background Agent integration"
```

---

## 🧪 Проверка работы

### Ожидаемое поведение:

1. **Issue создан** → автоматически добавится комментарий от workflow
2. **@copilot назначен** → агент начнёт работу
3. **Создан draft PR** → в ветке `copilot/issue-{number}`
4. **Запрос ревью** → вы получите notification

### Проверка scheduled tasks:

```bash
# Если установлен gh
gh workflow run copilot-scheduled-tasks.yaml

# Проверить статус
gh run list --workflow=copilot-scheduled-tasks.yaml
```

**Или через веб:**
1. Actions → Copilot Scheduled Tasks
2. Нажать "Run workflow" → "Run workflow"

---

## 📊 Мониторинг

### Статус агента
```bash
# Если установлен gh
gh copilot agent status
```

### Логи workflows
```bash
gh run list --limit 10
gh run view <run-id> --log
```

### Метрики
1. Открыть: https://github.com/Dykij/DMarket-Telegram-Bot/actions
2. Проверить:
   - Время выполнения workflows
   - Успешность запусков
   - Использование минут Actions

---

## 🐛 Troubleshooting

### Агент не назначается автоматически
**Причина:** Workflow `copilot-issue-templates.yaml` не запустился

**Решение:**
1. Проверить что workflow файл есть в `.github/workflows/`
2. Проверить Actions permissions
3. Вручную назначить @copilot в issue

### Workflows не появляются в Actions
**Причина:** Файлы ещё не в main ветке

**Решение:**
```bash
git push origin main
```

### Ошибка "gh command not found"
**Причина:** GitHub CLI не установлен

**Решение:**
- Установить через инструкцию выше
- Или использовать веб-интерфейс

---

## 📚 Документация

После активации читать:

1. **Полное руководство:**
   - `.github/COPILOT_AGENT_GUIDE.md`

2. **Инструкции для агента:**
   - `.github/copilot-agent-instructions.md`

3. **Кастомные агенты:**
   - `.github/copilot-custom-agents.yaml`

4. **Резюме улучшений:**
   - `.github/COPILOT_IMPROVEMENTS_SUMMARY.md`

---

## ✅ Checklist активации

Отметьте после выполнения:

- [ ] Установлен GitHub CLI (опционально)
- [ ] Созданы 6 labels в репозитории
- [ ] Активирован Copilot Agent в настройках
- [ ] Настроены Actions permissions
- [ ] Сделан push коммита в main
- [ ] Проверены workflows в Actions
- [ ] Создано тестовое issue
- [ ] Агент ответил на issue
- [ ] Draft PR создан
- [ ] Ревью прошёл успешно

---

## 🎉 После активации

**Агент готов к работе!**

Теперь можно:
- ✅ Создавать issues с шаблонами
- ✅ Использовать @copilot в комментариях PR
- ✅ Получать автоматические улучшения кода
- ✅ Мониторить scheduled tasks
- ✅ Просматривать security alerts

**Следующие шаги:**
1. Прочитать COPILOT_AGENT_GUIDE.md
2. Создать несколько тестовых задач
3. Настроить custom agents под проект
4. Собрать первые метрики использования

---

**Удачи с GitHub Copilot Agent! 🚀**

**Вопросы?** См. `.github/COPILOT_AGENT_GUIDE.md` → Troubleshooting
