"""Watchdog - система мониторинга и автоматического перезапуска бота.

Этот модуль обеспечивает:
1. Мониторинг состояния основного процесса бота
2. Автоматический перезапуск при падении
3. Health check через HTTP endpoint
4. Логирование критических ошибок в Telegram
5. Graceful shutdown с сохранением состояния

Использование:
    Вместо запуска main.py напрямую, используйте:
    ```bash
    python src/utils/watchdog.py
    ```

    Или добавьте в start_bot.bat:
    ```batch
    python src/utils/watchdog.py
    ```
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
import logging
import os
from pathlib import Path
import signal
import subprocess  # noqa: S404 - Required for process management in watchdog
import sys
from typing import Any

import aiohttp


logger = logging.getLogger(__name__)


class ProcessState(StrEnum):
    """Состояние процесса."""

    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    CRASHED = "crashed"
    RESTARTING = "restarting"


@dataclass
class WatchdogConfig:
    """Конфигурация Watchdog."""

    # Основной процесс
    main_script: str = "src/main.py"
    python_executable: str = sys.executable

    # Health check
    health_check_url: str = "http://localhost:8080/health"
    health_check_interval_seconds: int = 60  # Каждую минуту
    health_check_timeout_seconds: int = 10
    max_health_failures: int = 3  # После 3 неудачных проверок - перезапуск

    # Перезапуск
    restart_delay_seconds: int = 10
    max_restart_attempts: int = 5
    restart_cooldown_seconds: int = 300  # 5 минут между сериями перезапусков

    # Telegram уведомления
    telegram_bot_token: str | None = None
    telegram_chat_id: str | None = None
    notify_on_crash: bool = True
    notify_on_restart: bool = True

    # Логирование
    log_file: str = "logs/watchdog.log"
    max_log_size_mb: int = 10


@dataclass
class ProcessStats:
    """Статистика процесса."""

    start_time: datetime | None = None
    restart_count: int = 0
    crash_count: int = 0
    last_crash_time: datetime | None = None
    last_health_check: datetime | None = None
    health_failures: int = 0
    uptime_seconds: float = 0
    last_restart_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Преобразовать в словарь."""
        return {
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "restart_count": self.restart_count,
            "crash_count": self.crash_count,
            "last_crash_time": self.last_crash_time.isoformat() if self.last_crash_time else None,
            "uptime_seconds": self.uptime_seconds,
            "health_failures": self.health_failures,
            "last_restart_reason": self.last_restart_reason,
        }


class Watchdog:
    """Сторожевой пес для мониторинга и перезапуска бота.

    Обеспечивает бесперебойную работу бота 24/7.
    """

    def __init__(self, config: WatchdogConfig | None = None) -> None:
        """Инициализация Watchdog.

        Args:
            config: Конфигурация (опционально)
        """
        self.config = config or WatchdogConfig()
        self.stats = ProcessStats()
        self.state = ProcessState.STOPPED
        self._process: subprocess.Popen | None = None
        self._should_run = True
        self._consecutive_restarts = 0
        self._last_restart_series_time: datetime | None = None

        # Настройка логирования
        self._setup_logging()

        # Загрузка Telegram credentials из окружения
        if not self.config.telegram_bot_token:
            self.config.telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not self.config.telegram_chat_id:
            self.config.telegram_chat_id = os.getenv("TELEGRAM_ADMIN_CHAT_ID")

        logger.info("Watchdog initialized")

    def _setup_logging(self) -> None:
        """Настроить логирование."""
        log_dir = Path(self.config.log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(self.config.log_file, encoding="utf-8")
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))

        logging.getLogger().addHandler(file_handler)
        logging.getLogger().setLevel(logging.INFO)

    async def start(self) -> None:
        """Запустить Watchdog."""
        logger.info("🐕 Watchdog starting...")
        self._should_run = True

        # Обработка сигналов для graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        try:
            while self._should_run:
                # Запускаем основной процесс
                await self._start_main_process()

                # Мониторим его работу
                await self._monitor_process()

                # Если процесс упал и нужно перезапускать
                if self._should_run and self.state == ProcessState.CRASHED:
                    await self._handle_crash()

        except Exception as e:
            logger.exception(f"Watchdog critical error: {e}")
            await self._send_telegram_alert(
                f"🚨 **WATCHDOG CRITICAL ERROR**\n\n"
                f"Watchdog сам упал с ошибкой:\n`{e}`\n\n"
                f"Требуется ручное вмешательство!"
            )
        finally:
            await self._cleanup()

    async def stop(self) -> None:
        """Остановить Watchdog и процесс."""
        logger.info("🛑 Watchdog stopping...")
        self._should_run = False

        if self._process and self._process.poll() is None:
            logger.info("Terminating main process...")
            self._process.terminate()
            try:
                self._process.wait(timeout=30)
            except subprocess.TimeoutExpired:
                logger.warning("Process didn't terminate, killing...")
                self._process.kill()

        self.state = ProcessState.STOPPED

    def _signal_handler(self, signum: int, frame: Any) -> None:
        """Обработчик сигналов."""
        logger.info(f"Received signal {signum}, initiating shutdown...")
        self._should_run = False

    async def _start_main_process(self) -> None:
        """Запустить основной процесс бота."""
        self.state = ProcessState.STARTING
        logger.info(f"🚀 Starting main process: {self.config.main_script}")

        try:
            # Определяем рабочую директорию
            working_dir = Path(__file__).parent.parent.parent  # Корень проекта

            self._process = subprocess.Popen(  # noqa: ASYNC220, S603 - Required for process management
                [self.config.python_executable, "-m", "src.main"],
                cwd=working_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,  # Line buffered
            )

            self.stats.start_time = datetime.now(UTC)
            self.state = ProcessState.RUNNING
            logger.info(f"✅ Main process started (PID: {self._process.pid})")

            if self.config.notify_on_restart and self.stats.restart_count > 0:
                await self._send_telegram_alert(
                    f"🔄 **BOT RESTARTED**\n\n"
                    f"Бот перезапущен (попытка #{self.stats.restart_count})\n"
                    f"Причина: {self.stats.last_restart_reason}"
                )

        except Exception as e:
            logger.exception(f"Failed to start main process: {e}")
            self.state = ProcessState.CRASHED
            raise

    async def _monitor_process(self) -> None:
        """Мониторить работу процесса."""
        logger.info("👁️ Starting process monitoring...")

        while self._should_run and self._process:
            # Проверяем, жив ли процесс
            return_code = self._process.poll()

            if return_code is not None:
                # Процесс завершился
                logger.warning(f"Main process exited with code {return_code}")

                if return_code == 0:
                    # Нормальное завершение
                    logger.info("Process exited normally")
                    self._should_run = False
                else:
                    # Аварийное завершение
                    self.state = ProcessState.CRASHED
                    self.stats.crash_count += 1
                    self.stats.last_crash_time = datetime.now(UTC)
                    self.stats.last_restart_reason = f"Exit code: {return_code}"

                break

            # Health check
            if await self._perform_health_check():
                self.stats.health_failures = 0
            else:
                self.stats.health_failures += 1
                logger.warning(
                    f"Health check failed ({self.stats.health_failures}/{self.config.max_health_failures})"
                )

                if self.stats.health_failures >= self.config.max_health_failures:
                    logger.error("Too many health check failures, restarting...")
                    self.state = ProcessState.CRASHED
                    self.stats.last_restart_reason = "Health check failures"
                    break

            # Обновляем uptime
            if self.stats.start_time:
                self.stats.uptime_seconds = (
                    datetime.now(UTC) - self.stats.start_time
                ).total_seconds()

            # Ждем до следующей проверки
            await asyncio.sleep(self.config.health_check_interval_seconds)

    async def _perform_health_check(self) -> bool:
        """Выполнить health check.

        Returns:
            True если проверка прошла успешно
        """
        self.stats.last_health_check = datetime.now(UTC)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.config.health_check_url,
                    timeout=aiohttp.ClientTimeout(total=self.config.health_check_timeout_seconds),
                ) as response:
                    if response.status == 200:
                        return True
                    logger.warning(f"Health check returned status {response.status}")
                    return False

        except aiohttp.ClientError as e:
            logger.warning(f"Health check connection error: {e}")
            return False
        except TimeoutError:
            logger.warning("Health check timeout")
            return False
        except Exception as e:
            logger.exception(f"Health check unexpected error: {e}")
            return False

    async def _handle_crash(self) -> None:
        """Обработать падение процесса."""
        logger.info("💥 Handling process crash...")

        # Уведомление о падении
        if self.config.notify_on_crash:
            await self._send_telegram_alert(
                f"💥 **BOT CRASHED**\n\n"
                f"Бот упал!\n"
                f"Причина: {self.stats.last_restart_reason}\n"
                f"Всего падений: {self.stats.crash_count}\n"
                f"Uptime до падения: {self._format_uptime(self.stats.uptime_seconds)}\n\n"
                f"Перезапуск через {self.config.restart_delay_seconds} сек..."
            )

        # Проверяем cooldown между сериями перезапусков
        now = datetime.now(UTC)
        if self._last_restart_series_time:
            time_since_last = (now - self._last_restart_series_time).total_seconds()
            if time_since_last > self.config.restart_cooldown_seconds:
                # Прошло достаточно времени, сбрасываем счетчик
                self._consecutive_restarts = 0

        self._consecutive_restarts += 1

        # Проверяем лимит перезапусков
        if self._consecutive_restarts > self.config.max_restart_attempts:
            logger.error(f"Max restart attempts ({self.config.max_restart_attempts}) exceeded")
            await self._send_telegram_alert(
                f"🚨 **CRITICAL: BOT STOPPED**\n\n"
                f"Превышен лимит перезапусков ({self.config.max_restart_attempts})!\n"
                f"Бот остановлен.\n\n"
                f"Требуется ручное вмешательство."
            )
            self._should_run = False
            return

        # Ждем перед перезапуском
        self.state = ProcessState.RESTARTING
        logger.info(f"Waiting {self.config.restart_delay_seconds}s before restart...")
        await asyncio.sleep(self.config.restart_delay_seconds)

        self.stats.restart_count += 1
        self._last_restart_series_time = now

        # Убиваем старый процесс, если он еще жив
        if self._process and self._process.poll() is None:
            self._process.kill()
            self._process.wait()

    async def _cleanup(self) -> None:
        """Очистка ресурсов."""
        logger.info("Cleaning up...")

        if self._process and self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self._process.kill()

    async def _send_telegram_alert(self, message: str) -> None:
        """Отправить уведомление в Telegram.

        Args:
            message: Текст сообщения
        """
        if not self.config.telegram_bot_token or not self.config.telegram_chat_id:
            logger.debug("Telegram not configured, skipping alert")
            return

        try:
            url = f"https://api.telegram.org/bot{self.config.telegram_bot_token}/sendMessage"
            payload = {
                "chat_id": self.config.telegram_chat_id,
                "text": message,
                "parse_mode": "Markdown",
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=10) as response:
                    if response.status != 200:
                        logger.warning(f"Failed to send Telegram alert: {response.status}")

        except Exception as e:
            logger.exception(f"Error sending Telegram alert: {e}")

    @staticmethod
    def _format_uptime(seconds: float) -> str:
        """Форматировать uptime."""
        if seconds < 60:
            return f"{int(seconds)}с"
        if seconds < 3600:
            return f"{int(seconds // 60)}м {int(seconds % 60)}с"
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}ч {minutes}м"

    def get_status(self) -> dict[str, Any]:
        """Получить статус Watchdog."""
        return {
            "state": self.state,
            "process_pid": self._process.pid if self._process else None,
            "stats": self.stats.to_dict(),
            "config": {
                "main_script": self.config.main_script,
                "health_check_interval": self.config.health_check_interval_seconds,
                "max_restart_attempts": self.config.max_restart_attempts,
            },
        }


async def main() -> None:
    """Точка входа для Watchdog."""
    print("🐕 Starting DMarket Bot Watchdog...")
    print("=" * 50)

    # Создаем конфигурацию
    config = WatchdogConfig(
        main_script="src/main.py",
        health_check_interval_seconds=60,
        restart_delay_seconds=10,
        max_restart_attempts=5,
    )

    # Запускаем Watchdog
    watchdog = Watchdog(config)

    try:
        await watchdog.start()
    except KeyboardInterrupt:
        print("\n⚠️ Keyboard interrupt received")
        await watchdog.stop()

    print("🛑 Watchdog stopped")


if __name__ == "__main__":
    asyncio.run(main())
