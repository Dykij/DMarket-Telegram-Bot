"""Скрипт для остановки Telegram бота."""

import logging
from pathlib import Path

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def stop_bot_service() -> bool:
    """Останавливает работающего бота.

    Returns:
        True при успешной остановке, False при ошибке
    """
    try:
        # Получаем текущую директорию проекта
        project_dir = Path(__file__).parent.absolute()

        # Проверяем наличие файла блокировки
        lock_file = project_dir / "bot.lock"
        if not lock_file.exists():
            logger.info("Бот не запущен (файл блокировки не найден).")
            return False

        # Читаем PID из файла блокировки
        try:
            with open(lock_file, encoding="utf-8") as f:
                pid = int(f.read().strip())
        except (OSError, ValueError):
            logger.exception("Ошибка при чтении файла блокировки")
            return False

        logger.info("Останавливаем бота с PID: %s...", pid)

        # Отправляем сигнал SIGTERM процессу
        try:
            import psutil  # type: ignore[import-untyped]

            if psutil.pid_exists(pid):
                process = psutil.Process(pid)
                process.terminate()  # Отправляем SIGTERM

                logger.info("Отправлен сигнал завершения процессу %s", pid)

                # Ждем завершения процесса
                _, still_alive = psutil.wait_procs([process], timeout=5)
                if still_alive:
                    # Force kill if not terminated
                    logger.warning(
                        "Процесс %s не завершился. Принудительно.",
                        pid,
                    )
                    process.kill()  # Отправляем SIGKILL

                # Удаляем файл блокировки
                if lock_file.exists():
                    lock_file.unlink()
                    logger.info("Файл блокировки удален")

                logger.info(
                    "Бот с PID %s успешно остановлен.",
                    pid,
                )
                return True
            logger.warning(
                "Процесс с PID %s не найден. Удаляем файл.",  # noqa: RUF001
                pid,
            )
            if lock_file.exists():
                lock_file.unlink()
                logger.info("Файл блокировки удален.")
            return False
        except (OSError, ImportError):
            logger.exception("Ошибка при остановке бота")
            return False
    except (OSError, ValueError):
        logger.exception("Ошибка при остановке бота")
        return False


if __name__ == "__main__":
    stop_bot_service()
