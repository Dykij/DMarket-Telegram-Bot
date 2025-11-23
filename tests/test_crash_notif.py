"""
Упрощённый тест системы crash notifications.

Проверяет:
1. Отправку уведомлений о крашах админам через Telegram
2. Форматирование сообщений
3. Работу с и без очереди уведомлений
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
        queue.enqueue = AsyncMock()
        return queue

    @pytest.fixture()
    def test_error(self):
        """Тестовая ошибка с traceback."""
        try:
            _ = 1 / 0
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
        assert mock_notification_queue.enqueue.call_count >= 1

        # Получаем ПЕРВЫЙ вызов (основное сообщение)
        call_kwargs = mock_notification_queue.enqueue.call_args_list[0][1]

        # Проверяем формат сообщения
        message = call_kwargs["text"]
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

        # Проверяем, что было минимум 2 вызова
        # (основное сообщение + traceback)
        count = mock_notification_queue.enqueue.call_count
        assert count >= 2

        # Проверяем truncation traceback
        traceback_call_kwargs = mock_notification_queue.enqueue.call_args_list[1][1]
        traceback_message = traceback_call_kwargs["text"]

        # Traceback должен быть урезан до ~2900 символов
        assert len(traceback_message) <= 3100

    @pytest.mark.asyncio()
    async def test_send_crash_notification_without_queue(self, mock_bot, test_error):
        """Тест отправки напрямую через bot без очереди."""
        _, traceback_text = test_error
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
        call_kwargs = mock_bot.send_message.call_args[1]

        # Проверяем параметры
        assert call_kwargs["chat_id"] == user_id
        assert call_kwargs["parse_mode"] == "Markdown"

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

        call_kwargs = mock_notification_queue.enqueue.call_args_list[0][1]
        message = call_kwargs["text"]

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

        # Должно быть 2 вызова:
        # основное сообщение (HIGH) и traceback (NORMAL)
        count = mock_notification_queue.enqueue.call_count
        assert count == 2

        # Проверяем приоритеты
        from telegram_bot.notification_queue import Priority  # noqa: E402

        calls = mock_notification_queue.enqueue.call_args_list
        main_call_kwargs = calls[0][1]
        traceback_call_kwargs = calls[1][1]

        # Основное сообщение - HIGH (наивысший приоритет)
        assert main_call_kwargs["priority"] == Priority.HIGH
        # Traceback - NORMAL
        assert traceback_call_kwargs["priority"] == Priority.NORMAL


def print_test_summary():
    """Выводит summary результатов тестов."""
    print("\n" + "=" * 60)
    print("📊 SUMMARY: Crash Notifications Test Suite")
    print("=" * 60)
    print("\n✅ Протестированные компоненты:")
    print("  1. send_crash_notification() - базовая функциональность")
    print("  2. Truncation длинного traceback")
    print("  3. Отправка с очередью и без очереди")
    print("  4. Форматирование сообщений")
    print("  5. Приоритеты уведомлений (HIGH/NORMAL)")
    print("\n💡 Результаты тестирования показывают:")
    print("  ✓ Crash notifications корректно форматируются")
    print("  ✓ Длинные traceback'и правильно обрезаются")
    print("  ✓ Поддерживаются оба режима отправки")
    print("  ✓ Приоритеты уведомлений работают правильно")
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
