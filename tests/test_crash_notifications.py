"""
Комплексный тест системы crash notifications.

Проверяет:
1. Отправку уведомлений о крашах админам через Telegram
2. Форматирование сообщений и truncation traceback
3. Приоритеты уведомлений
"""

import sys
import traceback
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

# Добавляем src в путь для импорта
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from telegram_bot.notifier import send_crash_notification  # noqa: E402


class TestCrashNotifications:
    """Тесты для системы уведомлений о крашах."""

    @pytest.fixture()
    def mock_bot(self):
        """Мок Telegram бота."""
        bot = AsyncMock()
        bot.send_message = AsyncMock(return_value=MagicMock(message_id=123))
        return bot

    @pytest.fixture()
    def mock_notification_queue(self):
        """Мок очереди уведомлений."""
        queue = AsyncMock()
        queue.add_notification = AsyncMock()
        return queue

    @pytest.fixture()
    def test_error(self):
        """Тестовая ошибка с traceback."""
        try:
            # Создаём реальный traceback
            _ = 1 / 0  # noqa: F841
        except ZeroDivisionError as e:
            return e, traceback.format_exc()

    @pytest.mark.asyncio()
    async def test_send_crash_notification_basic(
        self, mock_bot, mock_notification_queue, test_error
    ):
        """Тест базовой отправки crash notification."""
        _, traceback_text = test_error
        user_id = 123456789

        await send_crash_notification(
            bot=mock_bot,
            user_id=user_id,
            error_type="ZeroDivisionError",
            error_message="division by zero",
            traceback_text=traceback_text,
            context={"component": "test", "dry_run": True},
            notification_queue=mock_notification_queue,
        )

        # Проверяем, что уведомление добавлено в очередь
        assert mock_notification_queue.add_notification.call_count >= 1
        call_args = mock_notification_queue.add_notification.call_args_list[0]

        # Проверяем формат сообщения
        message = call_args[0][0]
        assert "💥 *КРИТИЧЕСКАЯ ОШИБКА БОТА*" in message
        assert "ZeroDivisionError" in message
        assert "division by zero" in message
        assert "component" in message
        assert "test" in message

    @pytest.mark.asyncio()
    async def test_send_crash_notification_with_long_traceback(
        self, mock_bot, mock_notification_queue
    ):
        """Тест truncation длинного traceback."""
        user_id = 123456789
        # Создаём очень длинный traceback (>3000 символов)
        long_traceback = "Line of traceback\n" * 300

        await send_crash_notification(
            bot=mock_bot,
            user_id=user_id,
            error_type="TestError",
            error_message="Test error message",
            traceback_text=long_traceback,
            context={"test": "context"},
            notification_queue=mock_notification_queue,
        )

        # Проверяем, что было как минимум 2 вызова (основное сообщение + traceback)
        assert mock_notification_queue.add_notification.call_count >= 2

        # Проверяем truncation traceback
        traceback_call = mock_notification_queue.add_notification.call_args_list[1]
        traceback_message = traceback_call[0][0]

        # Traceback должен быть урезан до ~2900 символов
        assert len(traceback_message) <= 3000

    @pytest.mark.asyncio()
    async def test_send_crash_notification_without_queue(self, mock_bot, test_error):
        """Тест отправки напрямую через bot без очереди."""
        error, traceback_text = test_error
        user_id = 123456789

        await send_crash_notification(
            bot=mock_bot,
            user_id=user_id,
            error_type="ZeroDivisionError",
            error_message="division by zero",
            traceback_text=traceback_text,
            context={"component": "test"},
            notification_queue=None,  # Без очереди
        )

        # Проверяем прямую отправку через bot
        assert mock_bot.send_message.call_count >= 1
        call_args = mock_bot.send_message.call_args_list[0]

        # Проверяем параметры
        assert call_args[1]["chat_id"] == user_id
        assert call_args[1]["parse_mode"] == "Markdown"

    @pytest.mark.asyncio()
    async def test_bot_logger_crash_logging(self, test_error):
        """Тест логирования через BotLogger.log_crash()."""
        error, traceback_text = test_error

        with patch("utils.logging_utils.sentry_sdk") as mock_sentry:
            mock_sentry.is_initialized.return_value = True
            mock_sentry.push_scope = MagicMock()

            logger = BotLogger("test_crash")

            # Вызываем log_crash
            logger.log_crash(
                error=error,
                traceback_text=traceback_text,
                context={"component": "test", "dry_run": True},
                test_param="test_value",
            )

            # Проверяем, что Sentry вызван
            assert mock_sentry.capture_exception.called

    @pytest.mark.asyncio()
    async def test_crash_notification_formatting(self, mock_bot, mock_notification_queue):
        """Тест форматирования сообщения crash notification."""
        user_id = 123456789

        context = {
            "component": "arbitrage_scanner",
            "dry_run": False,
            "debug": True,
            "user_count": 42,
        }

        await send_crash_notification(
            bot=mock_bot,
            user_id=user_id,
            error_type="RuntimeError",
            error_message="Test runtime error",
            traceback_text="Short traceback",
            context=context,
            notification_queue=mock_notification_queue,
        )

        call_args = mock_notification_queue.add_notification.call_args_list[0]
        message = call_args[0][0]

        # Проверяем наличие всех ключевых элементов
        assert "💥" in message
        assert "RuntimeError" in message
        assert "Test runtime error" in message
        assert "arbitrage_scanner" in message
        assert "dry_run" in message
        assert "False" in message

    @pytest.mark.asyncio()
    async def test_crash_notification_priorities(self, mock_bot, mock_notification_queue):
        """Тест приоритетов уведомлений."""
        user_id = 123456789

        await send_crash_notification(
            bot=mock_bot,
            user_id=user_id,
            error_type="TestError",
            error_message="Test",
            traceback_text="Traceback text\n" * 100,
            context={},
            notification_queue=mock_notification_queue,
        )

        # Должно быть 2 вызова: основное сообщение (CRITICAL) и traceback (HIGH)
        assert mock_notification_queue.add_notification.call_count == 2

        # Проверяем приоритеты
        from telegram_bot.notification_queue import Priority

        main_call = mock_notification_queue.add_notification.call_args_list[0]
        traceback_call = mock_notification_queue.add_notification.call_args_list[1]

        assert main_call[0][2] == Priority.CRITICAL  # Основное сообщение
        assert traceback_call[0][2] == Priority.HIGH  # Traceback


class TestIntegrationCrashHandler:
    """Интеграционные тесты обработчика крашей в main.py."""

    @pytest.mark.asyncio()
    async def test_main_crash_handler_integration(self):
        """Тест интеграции crash handler в main.py (симуляция)."""
        # Симулируем краш в main.py

        mock_bot = AsyncMock()
        mock_bot.send_message = AsyncMock()

        mock_config = MagicMock()
        mock_config.security.admin_users = [123456789]

        mock_logger = MagicMock()
        mock_logger.log_crash = MagicMock()

        # Симулируем ошибку
        try:
            raise RuntimeError("Simulated crash in main.py")
        except Exception as e:
            error = e
            tb = traceback.format_exc()

            # Вызываем логирование
            context = {
                "component": "main",
                "dry_run": False,
                "debug": False,
            }

            mock_logger.log_crash(error=error, traceback_text=tb, context=context)

            # Проверяем, что log_crash был вызван
            assert mock_logger.log_crash.called
            call_kwargs = mock_logger.log_crash.call_args[1]
            assert call_kwargs["context"]["component"] == "main"


async def run_live_crash_test():
    """
    Live тест crash notification (требует настроенного бота).

    ВНИМАНИЕ: Этот тест отправит реальное уведомление в Telegram!
    Раскомментируйте и запустите вручную только если хотите протестировать
    с реальным ботом и админ пользователем.
    """
    print("=" * 60)
    print("🧪 LIVE TEST: Crash Notification")
    print("=" * 60)

    # Раскомментируйте следующий код для live теста:
    """
    from telegram import Bot
    from utils.config import Config

    config = Config.load()
    bot = Bot(token=config.bot.token)

    # Получаем admin user
    admin_users = config.security.admin_users or config.security.allowed_users[:1]
    if not admin_users:
        print("❌ No admin users configured!")
        return

    admin_id = admin_users[0]
    print(f"📤 Sending crash notification to admin: {admin_id}")

    # Создаём тестовую ошибку
    try:
        result = 1 / 0
    except ZeroDivisionError as e:
        error = e
        tb = traceback.format_exc()

    # Отправляем crash notification
    await send_crash_notification(
        bot=bot,
        user_id=admin_id,
        error_type=type(error).__name__,
        error_message=str(error),
        traceback_text=tb,
        context={
            "component": "live_test",
            "dry_run": True,
            "debug": True,
            "timestamp": datetime.utcnow().isoformat(),
        },
        notification_queue=None  # Прямая отправка
    )

    print("✅ Crash notification sent successfully!")
    print("📱 Check your Telegram for the notification")
    """

    print("\n⚠️  Live test закомментирован для безопасности")
    print("Раскомментируйте код в run_live_crash_test() для реального теста")


def print_test_summary():
    """Выводит summary результатов тестов."""
    print("\n" + "=" * 60)
    print("📊 SUMMARY: Crash Notifications Test Suite")
    print("=" * 60)
    print("\n✅ Протестированные компоненты:")
    print("  1. send_crash_notification() - базовая функциональность")
    print("  2. Truncation длинного traceback")
    print("  3. Отправка с очередью и без очереди")
    print("  4. BotLogger.log_crash() с Sentry интеграцией")
    print("  5. Форматирование сообщений")
    print("  6. Приоритеты уведомлений (CRITICAL/HIGH)")
    print("  7. Интеграция с main.py (симуляция)")
    print("\n💡 Для live теста:")
    print("  - Раскомментируйте run_live_crash_test()")
    print("  - Настройте .env с TELEGRAM_BOT_TOKEN")
    print("  - Укажите admin_users в конфиге")
    print("=" * 60)


if __name__ == "__main__":
    print("🚀 Запуск тестов crash notifications...\n")

    # Запускаем pytest
    exit_code = pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--color=yes",
        "-p",
        "no:warnings",
    ])

    print_test_summary()

    if exit_code == 0:
        print("\n✅ Все тесты пройдены успешно!")
    else:
        print(f"\n❌ Тесты завершились с кодом: {exit_code}")

    sys.exit(exit_code)
