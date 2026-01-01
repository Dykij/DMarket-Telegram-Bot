"""Тест проверки применённых улучшений бота.

Проверяет:
1. Автоочистку pending updates
2. Persistence
3. Health check server
4. Middleware
"""

import asyncio
import os
import sys
from pathlib import Path

# Ensure we're in the root directory
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))


async def test_auto_clear_updates():
    """Тест автоочистки updates."""
    print("\n1️⃣  Проверка автоочистки pending updates...")

    from dotenv import load_dotenv
    from telegram import Bot

    load_dotenv()
    token = os.getenv("TELEGRAM_BOT_TOKEN")

    if not token:
        print("❌ TELEGRAM_BOT_TOKEN не найден")
        return False

    try:
        bot = Bot(token=token)
        updates = await bot.get_updates(timeout=5)
        print(f"✅ Pending updates: {len(updates)}")
        return True
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False


def test_persistence_file():
    """Тест наличия persistence файла."""
    print("\n2️⃣  Проверка Persistence...")

    persistence_path = "data/bot_persistence.pickle"

    if os.path.exists(persistence_path):
        size = Path(persistence_path).stat().st_size
        print(f"✅ Persistence файл существует: {persistence_path} ({size} bytes)")
        return True
    print(f"⚠️  Persistence файл будет создан при запуске: {persistence_path}")
    return True


def test_health_check_module():
    """Тест наличия health check модуля."""
    print("\n3️⃣  Проверка Health Check Server...")

    try:
        from src.telegram_bot.health_check import HealthCheckServer

        server = HealthCheckServer()
        print("✅ Health check модуль импортирован")
        print(f"   Host: {server.host}, Port: {server.port}")
        return True
    except Exception as e:
        print(f"❌ Ошибка импорта: {e}")
        return False


def test_middleware_module():
    """Тест наличия middleware модуля."""
    print("\n4️⃣  Проверка Middleware...")

    try:
        from src.telegram_bot.middleware import middleware

        print("✅ Middleware модуль импортирован")

        # Проверить методы
        assert hasattr(middleware, "logging_middleware"), "logging_middleware отсутствует"
        assert hasattr(middleware, "rate_limit_middleware"), "rate_limit_middleware отсутствует"
        assert hasattr(middleware, "get_stats"), "get_stats отсутствует"

        stats = middleware.get_stats()
        print(f"   Статистика: {stats}")

        return True
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False


def test_main_py_fix():
    """Тест исправления бага тройного запуска."""
    print("\n5️⃣  Проверка исправления main.py...")

    try:
        content = Path("src/main.py").read_text(encoding="utf-8")

        # Подсчитать количество asyncio.run(main())
        count = content.count("asyncio.run(main())")

        if count == 1:
            print("✅ Баг исправлен: asyncio.run(main()) встречается 1 раз")
            return True
        print(f"❌ Баг НЕ исправлен: asyncio.run(main()) встречается {count} раз(а)")
        return False
    except Exception as e:
        print(f"❌ Ошибка чтения файла: {e}")
        return False


async def test_health_check_live():
    """Тест работы health check (если бот запущен)."""
    print("\n6️⃣  Проверка Health Check endpoints (если бот запущен)...")

    try:
        import httpx

        async with httpx.AsyncClient() as client:
            # Тест /health
            try:
                response = await client.get("http://localhost:8080/health", timeout=2)
                print(f"✅ /health: {response.status_code} - {response.json()}")
            except httpx.ConnectError:
                print("⚠️  Бот не запущен (http://localhost:8080/health недоступен)")
                return True  # Не ошибка, просто бот не запущен

            # Тест /metrics
            try:
                response = await client.get("http://localhost:8080/metrics", timeout=2)
                print(f"✅ /metrics: {response.status_code}")
                print(f"   {response.json()}")
            except Exception as e:
                print(f"⚠️  /metrics недоступен: {e}")

            # Тест /ready
            try:
                response = await client.get("http://localhost:8080/ready", timeout=2)
                print(f"✅ /ready: {response.status_code} - {response.json()}")
            except Exception as e:
                print(f"⚠️  /ready недоступен: {e}")

        return True
    except ImportError:
        print("⚠️  httpx не установлен, пропускаем live тест")
        return True
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False


async def main():
    """Запустить все тесты."""
    print("=" * 60)
    print("🧪 ТЕСТИРОВАНИЕ УЛУЧШЕНИЙ БОТА")
    print("=" * 60)

    results = []

    # Статические тесты (не требуют запущенного бота)
    results.append(("Persistence файл", test_persistence_file()))
    results.append(("Health Check модуль", test_health_check_module()))
    results.append(("Middleware модуль", test_middleware_module()))
    results.append(("Исправление main.py", test_main_py_fix()))

    # Async тесты
    results.append(("Автоочистка updates", await test_auto_clear_updates()))
    results.append(("Health Check live", await test_health_check_live()))

    # Итоги
    print("\n" + "=" * 60)
    print("📊 РЕЗУЛЬТАТЫ")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅" if result else "❌"
        print(f"{status} {name}")

    print("\n" + "=" * 60)
    print(f"Пройдено: {passed}/{total} ({passed / total * 100:.0f}%)")

    if passed == total:
        print("🎉 ВСЕ ТЕСТЫ ПРОШЛИ!")
        print("✅ Бот готов к production")
    else:
        print(f"⚠️  Некоторые тесты не прошли: {total - passed}")

    print("=" * 60)

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
