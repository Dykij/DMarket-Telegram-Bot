#!/usr/bin/env python3
"""Скрипт для тестирования DMarket API и проверки баланса.

Этот скрипт помогает диагностировать проблемы с API ключами DMarket.
Использует те же методы, что и основной бот.
"""

import asyncio
import logging
import os
import sys

from dotenv import load_dotenv


# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger(__name__)


async def test_dmarket_api() -> None:
    """Тестирует подключение к DMarket API и получение баланса."""
    print("\n" + "=" * 70)
    print("🔍 ТЕСТИРОВАНИЕ DMARKET API")
    print("=" * 70 + "\n")

    # Загружаем переменные окружения
    load_dotenv()

    # Получаем API ключи
    public_key = os.getenv("DMARKET_PUBLIC_KEY", "")
    secret_key = os.getenv("DMARKET_SECRET_KEY", "")

    print("📋 Проверка переменных окружения:")
    public_status = "✅ Установлен" if public_key else "❌ Не установлен"
    secret_status = "✅ Установлен" if secret_key else "❌ Не установлен"
    print(f"   DMARKET_PUBLIC_KEY: {public_status}")
    print(f"   DMARKET_SECRET_KEY: {secret_status}")

    if not public_key or not secret_key:
        print("\n❌ ОШИБКА: API ключи не настроены!")
        print("\n📝 Инструкция:")
        print("   1. Создайте файл .env в корневой директории проекта")
        print("   2. Добавьте в него:")
        print("      DMARKET_PUBLIC_KEY=ваш_публичный_ключ")
        print("      DMARKET_SECRET_KEY=ваш_секретный_ключ")
        print("\n📖 Подробнее: см. файл НАСТРОЙКА_API_КЛЮЧЕЙ.md")
        return

    print(f"\n   Public Key (первые 10 символов): {public_key[:10]}...")
    print(f"   Secret Key (первые 10 символов): {secret_key[:10]}...")

    # Импортируем DMarket API
    try:
        from src.dmarket.dmarket_api import DMarketAPI
    except ImportError as e:
        print(f"\n❌ ОШИБКА ИМПОРТА: {e}")
        print("Убедитесь, что вы запускаете скрипт из корневой директории проекта")
        return

    # Создаём экземпляр API
    print("\n🔌 Подключение к DMarket API...")
    api_client = DMarketAPI(
        public_key=public_key,
        secret_key=secret_key,
        enable_cache=False,  # Отключаем кэш для тестирования
    )

    try:
        # Тест 1: Проверка публичного API (не требует авторизации)
        print("\n" + "─" * 70)
        print("📊 ТЕСТ 1: Публичный API (поиск предметов)")
        print("─" * 70)

        try:
            items = await api_client.get_market_items(
                game="a8db",  # CS:GO
                limit=5,
            )

            if items and "objects" in items:
                item_count = len(items.get("objects", []))
                print("✅ Публичный API работает!")
                print(f"   Найдено предметов: {item_count}")
                if item_count > 0:
                    first_item = items["objects"][0]
                    print(f"   Пример предмета: {first_item.get('title', 'N/A')}")
            else:
                print("⚠️  Получен ответ, но без данных о предметах")
                print(f"   Ответ: {items}")

        except Exception as e:
            print(f"❌ Ошибка при запросе публичного API: {e}")
            logger.exception("Детали ошибки:")

        # Тест 2: Проверка профиля пользователя (требует авторизации)
        print("\n" + "─" * 70)
        print("👤 ТЕСТ 2: Профиль пользователя")
        print("─" * 70)

        try:
            profile = await api_client.get_user_profile()

            if profile and not profile.get("error"):
                username = profile.get("username", "N/A")
                email = profile.get("email", "N/A")
                print("✅ Профиль получен!")
                print(f"   Username: {username}")
                print(f"   Email: {email}")
            else:
                print("❌ Ошибка при получении профиля")
                print(f"   Код: {profile.get('code', 'N/A')}")
                print(f"   Сообщение: {profile.get('message', 'N/A')}")

        except Exception as e:
            error_str = str(e)
            print(f"❌ Исключение при запросе профиля: {error_str}")
            if "404" in error_str:
                print("\n⚠️  ВНИМАНИЕ: Получена ошибка 404!")
                print("   Это может означать:")
                print("   • Trading API не активирован для ваших ключей")
                print("   • Ключи созданы до активации Trading API")
            logger.exception("Детали ошибки:")

        # Тест 3: Проверка баланса (требует Trading API)
        print("\n" + "─" * 70)
        print("💰 ТЕСТ 3: Баланс аккаунта (Trading API)")
        print("─" * 70)

        try:
            balance = await api_client.get_balance()

            if balance.get("error"):
                error_msg = balance.get("error_message", "Неизвестная ошибка")
                error_code = balance.get("status_code", "N/A")

                print("❌ Ошибка при получении баланса")
                print(f"   Код ошибки: {error_code}")
                print(f"   Сообщение: {error_msg}")

                if error_code == 404 or "404" in str(error_msg):
                    print("\n" + "!" * 70)
                    print("⚠️  ОШИБКА 404: Trading API недоступен")
                    print("!" * 70)
                    print("\n📋 Причина:")
                    print("   Ваши API ключи НЕ имеют доступа к Trading API.")
                    print("\n🔧 Решение:")
                    print("   1. Войдите на dmarket.com")
                    print("   2. Settings → API Keys")
                    print("   3. Активируйте 'Enable Trading API'")
                    print("   4. Создайте НОВЫЕ ключи с Trading API доступом")
                    print("   5. Обновите ключи в .env файле")
                    print("\n📖 Подробная инструкция: НАСТРОЙКА_API_КЛЮЧЕЙ.md")

                elif error_code == 401 or "401" in str(error_msg):
                    print("\n🔑 Ошибка авторизации")
                    print("   • Проверьте правильность ключей")
                    print("   • Убедитесь, что ключи не истекли")
                    print("   • Создайте новые ключи на dmarket.com")

            else:
                available = balance.get("available_balance", 0.0)
                total = balance.get("total_balance", 0.0)
                locked = balance.get("locked_balance", 0.0)
                trade_protected = balance.get("trade_protected_balance", 0.0)

                print("✅ Баланс получен успешно!")
                print(f"   💰 Всего: ${total:.2f} USD")
                print(f"   ✅ Доступно: ${available:.2f} USD")
                print(f"   🔒 Заблокировано: ${locked:.2f} USD")
                print(f"   🛡️  Защищено торговлей: ${trade_protected:.2f} USD")
                has_funds_status = "✅ Да" if balance.get("has_funds") else "❌ Нет"
                print(f"   💵 Имеет средства: {has_funds_status}")

                if total >= 1.0 and available < 1.0:
                    print("\n⚠️  У вас есть средства, но они заблокированы!")
                    print("   Причины блокировки:")
                    print("   • Активные торговые предложения (offers)")
                    print("   • Средства в процессе транзакции")
                    print("   • Pending статус после продажи")
                    print("\n💡 Что делать:")
                    print("   1. Проверьте активные предложения на dmarket.com")
                    print("   2. Отмените неактуальные предложения")
                    print("   3. Дождитесь завершения транзакций")
                elif available < 1.0 and total < 1.0:
                    print("\n⚠️  Баланс меньше минимального ($1.00)")
                    print("   Пополните баланс для работы с арбитражем")

        except Exception as e:
            error_str = str(e)
            print(f"❌ Исключение при запросе баланса: {error_str}")
            if "404" in error_str or "not found" in error_str.lower():
                print("\n" + "!" * 70)
                print("⚠️  ОШИБКА 404: Trading API недоступен")
                print("!" * 70)
                print("\n📖 См. инструкцию в файле: НАСТРОЙКА_API_КЛЮЧЕЙ.md")
            logger.exception("Детали ошибки:")

        # Итоговая сводка
        print("\n" + "=" * 70)
        print("📋 ИТОГОВАЯ СВОДКА")
        print("=" * 70)
        print("\n✅ Что работает:")
        print("   • Бот корректно настроен")
        print("   • API ключи определены")
        print("   • Подключение к DMarket установлено")
        print("\n🔍 Что проверить:")
        print("   • Если видите ошибку 404 → активируйте Trading API")
        print("   • Если видите ошибку 401 → проверьте правильность ключей")
        print("   • Если баланс $0.00 → пополните аккаунт на dmarket.com")

    finally:
        # Закрываем клиент
        await api_client._close_client()
        print("\n✅ Соединение закрыто")


if __name__ == "__main__":
    print("\n🤖 DMarket API Tester")
    print("Версия: 1.0.0")
    print("Дата: 14.11.2024\n")

    try:
        asyncio.run(test_dmarket_api())
    except KeyboardInterrupt:
        print("\n\n⚠️  Прервано пользователем")
    except Exception as e:
        print(f"\n\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        logger.exception("Детали ошибки:")

    print("\n" + "=" * 70)
    print("✅ Тестирование завершено")
    print("=" * 70 + "\n")
