"""Скрипт для запуска Telegram бота в фоновом режиме."""

import logging
import subprocess
import sys
from pathlib import Path


# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def start_bot_service() -> bool:
    """Запускает бота в фоновом режиме.

    Returns:
        True при успешном запуске, False при ошибке
    """
    try:
        # Получаем текущую директорию проекта
        project_dir = Path(__file__).parent.absolute()
        logger.info("Директория проекта: %s", project_dir)

        # Проверяем наличие файла bot.lock
        lock_file = project_dir / "bot.lock"
        if lock_file.exists():
            logger.warning(
                "Обнаружен файл блокировки. Бот уже запущен?",
            )
            try:
                with open(lock_file, encoding="utf-8") as f:
                    pid = f.read().strip()
                logger.info("PID запущенного бота: %s", pid)
            except OSError:
                logger.exception("Ошибка при чтении файла блокировки")

        # Путь к Python интерпретатору в текущем окружении
        python_path = sys.executable
        logger.info("Используемый Python: %s", python_path)

        # Путь к скрипту бота
        bot_script = project_dir / "src" / "telegram_bot" / "bot_v2.py"

        # Запускаем бота в отдельном процессе
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 0  # SW_HIDE - скрыть окно

        # Create bot process with output redirection to log
        process = subprocess.Popen(  # noqa: S603
            [python_path, str(bot_script)],
            cwd=str(project_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            startupinfo=startupinfo,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            | subprocess.DETACHED_PROCESS,
        )

        logger.info("Бот запущен с PID: %s", process.pid)

        # Записываем PID в отдельный файл
        pid_file = project_dir / "bot_service_pid.txt"
        with open(pid_file, "w", encoding="utf-8") as f:
            f.write(str(process.pid))

        return True
    except (OSError, subprocess.SubprocessError):
        logger.exception("Ошибка при запуске бота")
        return False


if __name__ == "__main__":
    success = start_bot_service()
    if success:
        logger.info("Бот запущен. См. bot_service.log.")
    else:
        logger.error("Ошибка. См. bot_service.log.")
