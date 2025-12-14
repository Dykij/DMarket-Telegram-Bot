# 🎯 БЫСТРАЯ АКТИВАЦИЯ - Ручная инструкция

**Время выполнения:** 10-15 минут
**Статус:** Браузер открыт → выполните 4 шага ниже

---

## ✅ ШАГ 1: Создать Labels (5 минут)

**Вкладка уже открыта:** https://github.com/Dykij/DMarket-Telegram-Bot/labels

Нажать **"New label"** 6 раз и создать:

### 1. copilot-task
- **Name:** `copilot-task`
- **Color:** `#0E8A16` (зелёный)
- **Description:** `Task for GitHub Copilot Coding Agent`
- **Нажать:** Create label

### 2. copilot-test
- **Name:** `copilot-test`
- **Color:** `#1D76DB` (синий)
- **Description:** `Test coverage improvement task`
- **Нажать:** Create label

### 3. copilot-refactor
- **Name:** `copilot-refactor`
- **Color:** `#FBCA04` (жёлтый)
- **Description:** `Code refactoring task`
- **Нажать:** Create label

### 4. copilot-docs
- **Name:** `copilot-docs`
- **Color:** `#5319E7` (фиолетовый)
- **Description:** `Documentation update task`
- **Нажать:** Create label

### 5. copilot-security
- **Name:** `copilot-security`
- **Color:** `#D93F0B` (красный)
- **Description:** `Security fix task`
- **Нажать:** Create label

### 6. copilot-bugfix
- **Name:** `copilot-bugfix`
- **Color:** `#EE0701` (тёмно-красный)
- **Description:** `Bug fix task`
- **Нажать:** Create label

---

## ✅ ШАГ 2: Активировать Copilot Agent (2 минуты)

**Вкладка уже открыта:** https://github.com/Dykij/DMarket-Telegram-Bot/settings

1. В левом меню найти **"Code and automation"**
2. Кликнуть на **"Copilot"**
3. Найти опцию **"Enable Copilot coding agent"**
4. Включить переключатель ✅
5. Нажать **"Save"** (если есть)

**⚠️ Требование:** Подписка GitHub Copilot Pro/Business/Enterprise

---

## ✅ ШАГ 3: Настроить Actions Permissions (1 минута)

**Вкладка уже открыта:** https://github.com/Dykij/DMarket-Telegram-Bot/settings/actions

### 3.1 Workflow permissions
Прокрутить до раздела **"Workflow permissions"**

Выбрать:
- ✅ **"Read and write permissions"**

### 3.2 Fork pull request workflows
Найти секцию **"Fork pull request workflows from outside collaborators"**

Включить:
- ✅ **"Allow GitHub Actions to create and approve pull requests"**

**Нажать:** Save

---

## ✅ ШАГ 4: Создать тестовое Issue (3 минуты)

**Открыть:** https://github.com/Dykij/DMarket-Telegram-Bot/issues/new/choose

1. Выбрать шаблон: **"Copilot Task"**
2. Заполнить поля:

```markdown
Title: @copilot: Add GitHub Copilot integration section to README

## 📋 Описание задачи
Добавить новую секцию в README.md о GitHub Copilot Background Agent

## 🎯 Цель
Документировать для разработчиков как использовать Copilot Agent

## 📁 Затрагиваемые файлы
- `README.md`

## ✅ Требования
1. Добавить секцию "GitHub Copilot Integration" после Features
2. Описать как создавать issues для агента
3. Добавить примеры использования
4. Ссылки на .github/COPILOT_AGENT_GUIDE.md

## ✔️ Критерии успеха
- [ ] Секция добавлена в README.md
- [ ] Примеры понятны и работают
- [ ] Ссылки корректны
```

3. **Labels:** Добавить `copilot-task` (кликнуть на шестерёнку справа)
4. **Assignees:** Выбрать `@copilot` (если доступно)
5. **Нажать:** Submit new issue

---

## 🎉 ГОТОВО!

После создания issue:

1. **Автоматически** появится комментарий от workflow
2. **Copilot начнёт** работу над задачей
3. **Создастся draft PR** в ветке `copilot/issue-{номер}`
4. **Вы получите** уведомление с запросом ревью

---

## 📊 Проверка статуса

### Workflows
https://github.com/Dykij/DMarket-Telegram-Bot/actions

Должны появиться:
- ✅ Copilot Coding Agent Setup
- ✅ Copilot Scheduled Tasks
- ✅ Copilot Security Audit
- ✅ Copilot Issue Templates

### Issues
https://github.com/Dykij/DMarket-Telegram-Bot/issues

Ваше тестовое issue должно иметь:
- Label: `copilot-task`
- Assignee: `@copilot`
- Комментарий от workflow

### Pull Requests
https://github.com/Dykij/DMarket-Telegram-Bot/pulls

Через несколько минут появится draft PR от Copilot

---

## ⏱️ Время выполнения

- Шаг 1 (Labels): ~5 минут
- Шаг 2 (Activation): ~2 минуты
- Шаг 3 (Permissions): ~1 минута
- Шаг 4 (Test Issue): ~3 минуты

**Итого: ~11 минут** ⚡

---

## 🐛 Troubleshooting

### Не вижу опцию "Enable Copilot coding agent"
**Причина:** Нет подписки или недостаточно прав
**Решение:** Проверить https://github.com/settings/copilot

### Агент не назначается на issue
**Причина:** Ещё не активирован
**Решение:** Выполнить Шаг 2 полностью

### Workflows не появляются
**Причина:** Push ещё не выполнен или Actions отключены
**Решение:** Проверить Settings → Actions → General → Allow all actions

---

## 📚 Следующие шаги

После успешной активации:

1. **Прочитать:** `.github/COPILOT_AGENT_GUIDE.md`
2. **Создать** несколько тестовых задач
3. **Проверить** scheduled tasks
4. **Собрать** первые метрики

---

**Удачи! 🚀**

Если возникли вопросы: см. `.github/ACTIVATION_GUIDE.md` (полная версия)
