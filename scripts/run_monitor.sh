#!/bin/bash
# Скрипт для запуска GitHub Actions Monitor
# Использование: ./scripts/run_monitor.sh

set -e  # Остановка при ошибке

echo -e "\n🔧 Настройка окружения..."

# Установка UTF-8 кодировки
export PYTHONIOENCODING=utf-8
export LC_ALL=en_US.UTF-8
export LANG=en_US.UTF-8

# Определение директории скрипта
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Путь к Python в виртуальном окружении
PYTHON_PATH="$PROJECT_ROOT/.venv/bin/python"
MONITOR_SCRIPT="$SCRIPT_DIR/github_actions_monitor.py"

# Проверка наличия виртуального окружения
if [ ! -f "$PYTHON_PATH" ]; then
    echo -e "❌ Виртуальное окружение не найдено!"
    echo -e "   Создайте его командой: python -m venv .venv"
    exit 1
fi

echo -e "✅ Окружение настроено\n"

# Запуск скрипта
"$PYTHON_PATH" "$MONITOR_SCRIPT"

# Сохранение кода завершения
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo -e "\n✅ Мониторинг завершен успешно\n"
else
    echo -e "\n⚠️  Мониторинг завершен с кодом: $EXIT_CODE\n"
fi

exit $EXIT_CODE
