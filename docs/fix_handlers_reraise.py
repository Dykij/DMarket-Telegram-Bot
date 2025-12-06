"""Скрипт для автоматического добавления reraise=False к @handle_exceptions в telegram handlers.

Этот скрипт находит все использования декоратора @handle_exceptions в telegram bot handlers
и добавляет параметр reraise=False если его нет.
"""

import re
from pathlib import Path


def fix_handler_file(file_path: Path) -> tuple[bool, int]:
    """Исправить один файл обработчика.

    Args:
        file_path: Путь к файлу

    Returns:
        Tuple[bool, int]: (был_ли_изменен, количество_исправлений)

    """
    content = file_path.read_text(encoding="utf-8")
    original_content = content
    fixes_count = 0

    # Паттерн для поиска @handle_exceptions без reraise=False
    # Обрабатываем случаи:
    # 1. @handle_exceptions(...) на одной строке БЕЗ reraise
    # 2. @handle_exceptions(\n...\n) на нескольких строках БЕЗ reraise

    # Паттерн 1: Однострочный декоратор
    pattern1 = r"@handle_exceptions\(([^)]+)\)(?!\s*async\s+def.*reraise)"

    def replace1(match):
        nonlocal fixes_count
        params = match.group(1).strip()

        # Проверяем что reraise уже не указан
        if "reraise" in params:
            return match.group(0)

        # Добавляем запятую если нужно
        if params and not params.endswith(","):
            params += ","

        fixes_count += 1
        return f"@handle_exceptions({params} reraise=False)"

    # Паттерн 2: Многострочный декоратор
    pattern2 = r"@handle_exceptions\(\s*\n([^)]*)\n\s*\)"

    def replace2(match):
        nonlocal fixes_count
        params = match.group(1).strip()

        # Проверяем что reraise уже не указан
        if "reraise" in params:
            return match.group(0)

        # Добавляем запятую если нужно
        if params and not params.endswith(","):
            params += ","

        fixes_count += 1
        # Сохраняем отступы
        indent = "    "
        return f"@handle_exceptions(\n{params}\n{indent}reraise=False,\n)"

    content = re.sub(pattern1, replace1, content)
    content = re.sub(pattern2, replace2, content)

    if content != original_content:
        file_path.write_text(content, encoding="utf-8")
        return True, fixes_count

    return False, 0


def main():
    """Основная функция."""
    handlers_dir = Path("src/telegram_bot/handlers")

    if not handlers_dir.exists():
        print(f"❌ Директория не найдена: {handlers_dir}")
        return

    total_files = 0
    total_fixes = 0
    modified_files = []

    print("🔍 Поиск handler файлов...")

    for py_file in handlers_dir.glob("*.py"):
        if py_file.name.startswith("__"):
            continue

        total_files += 1
        was_modified, fixes_count = fix_handler_file(py_file)

        if was_modified:
            modified_files.append(py_file.name)
            total_fixes += fixes_count
            print(f"✅ {py_file.name}: {fixes_count} исправлений")

    print("\n" + "=" * 60)
    print("📊 Итого:")
    print(f"   Проверено файлов: {total_files}")
    print(f"   Изменено файлов: {len(modified_files)}")
    print(f"   Всего исправлений: {total_fixes}")

    if modified_files:
        print("\n📝 Измененные файлы:")
        for filename in modified_files:
            print(f"   - {filename}")


if __name__ == "__main__":
    main()
