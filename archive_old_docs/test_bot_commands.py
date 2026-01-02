"""Тестовый скрипт для проверки всех команд и кнопок Telegram бота.

Этот скрипт проверяет:
- Регистрацию всех команд
- Доступность всех обработчиков
- Корректность импортов
"""

import asyncio
import logging
import sys
from pathlib import Path

# Добавить корневую директорию в путь
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

from telegram.ext import ApplicationBuilder

from src.telegram_bot.register_all_handlers import register_all_handlers

# Настройка логирования
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_bot_handlers():
    """Тестирование регистрации всех обработчиков бота."""
    logger.info("🤖 Тест регистрации обработчиков Telegram бота")
    logger.info("=" * 60)

    # Создать тестовое приложение (токен не важен для проверки регистрации)
    test_token = "123456789:ABCdefGHIjklMNOpqrSTUvwxyz"

    try:
        logger.info("📝 Создание тестового приложения бота...")
        application = ApplicationBuilder().token(test_token).build()

        # Добавить тестовые данные в bot_data
        application.bot_data["config"] = None
        application.bot_data["dmarket_api"] = None
        application.bot_data["database"] = None
        application.bot_data["state_manager"] = None

        logger.info("✅ Тестовое приложение создано")

        # Зарегистрировать обработчики
        logger.info("\n📋 Регистрация обработчиков...")
        register_all_handlers(application)

        logger.info("\n" + "=" * 60)
        logger.info("📊 СТАТИСТИКА РЕГИСТРАЦИИ")
        logger.info("=" * 60)

        # Подсчитать зарегистрированные обработчики
        total_handlers = len(application.handlers[0])  # Group 0
        logger.info(f"✅ Всего обработчиков зарегистрировано: {total_handlers}")

        # Анализ типов обработчиков
        from telegram.ext import CallbackQueryHandler, CommandHandler, MessageHandler

        command_handlers = []
        callback_handlers = []
        message_handlers = []
        other_handlers = []

        for handler in application.handlers[0]:
            if isinstance(handler, CommandHandler):
                command_handlers.append(handler)
            elif isinstance(handler, CallbackQueryHandler):
                callback_handlers.append(handler)
            elif isinstance(handler, MessageHandler):
                message_handlers.append(handler)
            else:
                other_handlers.append(handler)

        logger.info(f"\n📱 Команды (CommandHandler): {len(command_handlers)}")
        for handler in command_handlers:
            commands = handler.commands if hasattr(handler, "commands") else ["unknown"]
            logger.info(f"   /{', /'.join(commands)}")

        logger.info(f"\n🔘 Callback-кнопки (CallbackQueryHandler): {len(callback_handlers)}")
        for i, handler in enumerate(callback_handlers[:10], 1):  # Показать первые 10
            pattern = getattr(handler, "pattern", "No pattern")
            logger.info(f"   {i}. Pattern: {pattern}")
        if len(callback_handlers) > 10:
            logger.info(f"   ... и еще {len(callback_handlers) - 10} обработчиков")

        logger.info(f"\n💬 Текстовые сообщения (MessageHandler): {len(message_handlers)}")

        logger.info(f"\n🔧 Другие обработчики: {len(other_handlers)}")

        # Проверка критических команд
        logger.info("\n" + "=" * 60)
        logger.info("🔍 ПРОВЕРКА КРИТИЧЕСКИХ КОМАНД")
        logger.info("=" * 60)

        critical_commands = [
            "/start",
            "/help",
            "/dashboard",
            "/arbitrage",
            "/dmarket",
            "/status",
            "/markets",
            "/backtest",
            "/dailyreport",
        ]

        registered_commands = set()
        for handler in command_handlers:
            if hasattr(handler, "commands"):
                registered_commands.update(handler.commands)

        all_ok = True
        for cmd in critical_commands:
            cmd_name = cmd[1:]  # Убрать /
            if cmd_name in registered_commands:
                logger.info(f"   ✅ {cmd}")
            else:
                logger.error(f"   ❌ {cmd} - НЕ ЗАРЕГИСТРИРОВАНА!")
                all_ok = False

        # Проверка обработчиков callback
        logger.info("\n" + "=" * 60)
        logger.info("🔍 ПРОВЕРКА CALLBACK ОБРАБОТЧИКОВ")
        logger.info("=" * 60)

        critical_patterns = [
            "^mode_",  # Автоматический арбитраж
            "^api_check",  # Проверка API
            "^view_items",  # Просмотр предметов
        ]

        registered_patterns = []
        for handler in callback_handlers:
            if hasattr(handler, "pattern") and handler.pattern:
                registered_patterns.append(str(handler.pattern))

        for pattern in critical_patterns:
            found = any(pattern in p for p in registered_patterns)
            if found:
                logger.info(f"   ✅ Pattern: {pattern}")
            else:
                logger.warning(f"   ⚠️ Pattern: {pattern} - не найден (может быть не критичен)")

        # Итоговый результат
        logger.info("\n" + "=" * 60)
        if all_ok and total_handlers > 0:
            logger.info("✅ ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ УСПЕШНО!")
            logger.info(f"✅ {total_handlers} обработчиков готовы к работе")
        elif total_handlers > 0:
            logger.warning("⚠️ ПРОВЕРКИ ЗАВЕРШЕНЫ С ПРЕДУПРЕЖДЕНИЯМИ")
            logger.warning(f"⚠️ {total_handlers} обработчиков зарегистрировано")
            logger.warning("⚠️ Некоторые критические команды могут отсутствовать")
        else:
            logger.error("❌ КРИТИЧЕСКАЯ ОШИБКА: Обработчики не зарегистрированы!")

        logger.info("=" * 60)

        return all_ok and total_handlers > 0

    except Exception as e:
        logger.error(f"❌ Ошибка при тестировании: {e}", exc_info=True)
        return False


async def test_imports():
    """Проверка импортов всех модулей."""
    logger.info("\n" + "=" * 60)
    logger.info("📦 ПРОВЕРКА ИМПОРТОВ МОДУЛЕЙ")
    logger.info("=" * 60)

    modules_to_test = [
        "src.telegram_bot.handlers.commands",
        "src.telegram_bot.handlers.callbacks",
        "src.telegram_bot.handlers.scanner_handler",
        "src.telegram_bot.handlers.market_alerts_handler",
        "src.telegram_bot.handlers.market_analysis_handler",
        "src.telegram_bot.handlers.intramarket_arbitrage_handler",
        "src.telegram_bot.handlers.target_handler",
        "src.telegram_bot.handlers.dashboard_handler",
        "src.telegram_bot.handlers.notification_digest_handler",
        "src.telegram_bot.handlers.dmarket_handlers",
    ]

    success_count = 0
    failed_imports = []

    for module_name in modules_to_test:
        try:
            __import__(module_name)
            logger.info(f"   ✅ {module_name}")
            success_count += 1
        except Exception as e:
            logger.error(f"   ❌ {module_name}: {str(e)[:100]}")
            failed_imports.append((module_name, str(e)))

    logger.info("\n📊 Результаты импортов:")
    logger.info(f"   Успешных: {success_count}/{len(modules_to_test)}")
    logger.info(f"   Неудачных: {len(failed_imports)}/{len(modules_to_test)}")

    if failed_imports:
        logger.warning("\n⚠️ Модули с ошибками импорта:")
        for module, error in failed_imports:
            logger.warning(f"   • {module}")
            logger.warning(f"     Ошибка: {error[:150]}")

    return len(failed_imports) == 0


async def main():
    """Главная функция тестирования."""
    logger.info("🚀 Запуск полной проверки Telegram бота")
    logger.info("=" * 60)

    # Проверка 1: Импорты
    imports_ok = await test_imports()

    # Проверка 2: Регистрация обработчиков
    handlers_ok = await test_bot_handlers()

    # Итоговый результат
    logger.info("\n" + "=" * 60)
    logger.info("🏁 ИТОГОВЫЙ РЕЗУЛЬТАТ")
    logger.info("=" * 60)

    if imports_ok and handlers_ok:
        logger.info("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        logger.info("✅ Бот готов к запуску")
        return 0
    if handlers_ok:
        logger.warning("⚠️ ТЕСТЫ ЗАВЕРШЕНЫ С ПРЕДУПРЕЖДЕНИЯМИ")
        logger.warning("⚠️ Некоторые модули имеют проблемы с импортом")
        logger.warning("⚠️ Бот может работать с ограниченной функциональностью")
        return 1
    logger.error("❌ ТЕСТЫ НЕ ПРОЙДЕНЫ!")
    logger.error("❌ Бот НЕ готов к запуску")
    logger.error("❌ Необходимо исправить критические ошибки")
    return 2


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
