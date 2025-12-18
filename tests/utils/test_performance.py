"""Тесты для модуля performance.

Проверяет утилиты оптимизации производительности.
"""

import time

from src.utils.performance import AdvancedCache


class TestAdvancedCache:
    """Тесты класса AdvancedCache."""

    def test_cache_initialization(self):
        """Тест инициализации кеша."""
        cache = AdvancedCache(default_ttl=300)
        assert cache._default_ttl == 300
        assert cache._hits == 0
        assert cache._misses == 0
        assert len(cache._caches) == 0

    def test_cache_initialization_default_ttl(self):
        """Тест инициализации с TTL по умолчанию."""
        cache = AdvancedCache()
        assert cache._default_ttl == 300

    def test_cache_initialization_custom_ttl(self):
        """Тест инициализации с custom TTL."""
        cache = AdvancedCache(default_ttl=600)
        assert cache._default_ttl == 600

    def test_register_cache(self):
        """Тест регистрации нового хранилища кеша."""
        cache = AdvancedCache()
        cache.register_cache("test_cache")
        assert "test_cache" in cache._caches
        assert cache._ttls["test_cache"] == 300

    def test_register_cache_with_custom_ttl(self):
        """Тест регистрации кеша с custom TTL."""
        cache = AdvancedCache()
        cache.register_cache("test_cache", ttl=600)
        assert cache._ttls["test_cache"] == 600

    def test_register_cache_idempotent(self):
        """Тест что повторная регистрация не меняет кеш."""
        cache = AdvancedCache()
        cache.register_cache("test_cache", ttl=100)
        cache.set("test_cache", "key1", "value1")

        # Регистрируем повторно
        cache.register_cache("test_cache", ttl=200)

        # TTL не должен измениться
        assert cache._ttls["test_cache"] == 100
        assert cache.get("test_cache", "key1") == "value1"

    def test_set_and_get_value(self):
        """Тест сохранения и получения значения."""
        cache = AdvancedCache()
        cache.set("test_cache", "key1", "value1")
        result = cache.get("test_cache", "key1")
        assert result == "value1"

    def test_get_nonexistent_key(self):
        """Тест получения несуществующего ключа."""
        cache = AdvancedCache()
        result = cache.get("test_cache", "nonexistent")
        assert result is None
        assert cache._misses == 1

    def test_get_from_nonexistent_cache(self):
        """Тест получения из несуществующего кеша."""
        cache = AdvancedCache()
        result = cache.get("nonexistent_cache", "key1")
        assert result is None
        assert "nonexistent_cache" in cache._caches  # Автоматически создается

    def test_cache_hit_counter(self):
        """Тест счетчика попаданий в кеш."""
        cache = AdvancedCache()
        cache.set("test_cache", "key1", "value1")
        cache.get("test_cache", "key1")
        cache.get("test_cache", "key1")
        assert cache._hits == 2

    def test_cache_miss_counter(self):
        """Тест счетчика промахов кеша."""
        cache = AdvancedCache()
        cache.get("test_cache", "key1")
        cache.get("test_cache", "key2")
        assert cache._misses == 2

    def test_cache_expiration(self):
        """Тест истечения срока действия кеша."""
        cache = AdvancedCache(default_ttl=1)
        cache.set("test_cache", "key1", "value1")

        # Ждем истечения TTL
        time.sleep(1.1)

        result = cache.get("test_cache", "key1")
        assert result is None
        assert cache._misses == 1

    def test_cache_not_expired(self):
        """Тест что кеш не истекает раньше времени."""
        cache = AdvancedCache(default_ttl=5)
        cache.set("test_cache", "key1", "value1")

        # Получаем сразу
        result = cache.get("test_cache", "key1")
        assert result == "value1"
        assert cache._hits == 1

    def test_multiple_caches(self):
        """Тест работы с несколькими хранилищами."""
        cache = AdvancedCache()
        cache.set("cache1", "key1", "value1")
        cache.set("cache2", "key2", "value2")

        assert cache.get("cache1", "key1") == "value1"
        assert cache.get("cache2", "key2") == "value2"

    def test_same_key_different_caches(self):
        """Тест одинаковых ключей в разных хранилищах."""
        cache = AdvancedCache()
        cache.set("cache1", "key", "value1")
        cache.set("cache2", "key", "value2")

        assert cache.get("cache1", "key") == "value1"
        assert cache.get("cache2", "key") == "value2"

    def test_overwrite_value(self):
        """Тест перезаписи значения."""
        cache = AdvancedCache()
        cache.set("test_cache", "key1", "value1")
        cache.set("test_cache", "key1", "value2")

        result = cache.get("test_cache", "key1")
        assert result == "value2"

    def test_cache_with_tuple_key(self):
        """Тест использования tuple в качестве ключа."""
        cache = AdvancedCache()
        cache.set("test_cache", ("key1", "key2"), "value")
        result = cache.get("test_cache", ("key1", "key2"))
        assert result == "value"

    def test_cache_with_complex_value(self):
        """Тест сохранения сложных объектов."""
        cache = AdvancedCache()
        complex_value = {"nested": {"data": [1, 2, 3]}}
        cache.set("test_cache", "key1", complex_value)
        result = cache.get("test_cache", "key1")
        assert result == complex_value

    def test_cache_with_none_value(self):
        """Тест сохранения None."""
        cache = AdvancedCache()
        cache.set("test_cache", "key1", None)
        result = cache.get("test_cache", "key1")
        assert result is None
        assert cache._hits == 1  # Должно быть попадание

    def test_expired_cache_removed(self):
        """Тест что истекший кеш удаляется."""
        cache = AdvancedCache(default_ttl=1)
        cache.set("test_cache", "key1", "value1")

        time.sleep(1.1)
        cache.get("test_cache", "key1")

        # Проверяем что ключ удален
        assert "key1" not in cache._caches["test_cache"]

    def test_different_ttls_for_different_caches(self):
        """Тест разных TTL для разных хранилищ."""
        cache = AdvancedCache()
        cache.register_cache("short_ttl", ttl=1)
        cache.register_cache("long_ttl", ttl=10)

        cache.set("short_ttl", "key", "value1")
        cache.set("long_ttl", "key", "value2")

        time.sleep(1.1)

        assert cache.get("short_ttl", "key") is None
        assert cache.get("long_ttl", "key") == "value2"

    def test_cache_statistics(self):
        """Тест статистики кеша."""
        cache = AdvancedCache()

        # 3 промаха
        cache.get("test_cache", "key1")
        cache.get("test_cache", "key2")
        cache.get("test_cache", "key3")

        # Добавляем значения
        cache.set("test_cache", "key1", "value1")
        cache.set("test_cache", "key2", "value2")

        # 2 попадания
        cache.get("test_cache", "key1")
        cache.get("test_cache", "key2")

        # 1 промах
        cache.get("test_cache", "key3")

        assert cache._hits == 2
        assert cache._misses == 4

    def test_empty_string_key(self):
        """Тест использования пустой строки в качестве ключа."""
        cache = AdvancedCache()
        cache.set("test_cache", "", "empty_key_value")
        result = cache.get("test_cache", "")
        assert result == "empty_key_value"

    def test_numeric_key(self):
        """Тест использования числового ключа."""
        cache = AdvancedCache()
        cache.set("test_cache", 123, "numeric_key")
        result = cache.get("test_cache", 123)
        assert result == "numeric_key"

    def test_boolean_value(self):
        """Тест сохранения boolean значений."""
        cache = AdvancedCache()
        cache.set("test_cache", "true_key", True)
        cache.set("test_cache", "false_key", False)

        assert cache.get("test_cache", "true_key") is True
        assert cache.get("test_cache", "false_key") is False

    def test_zero_ttl(self):
        """Тест с нулевым TTL (мгновенное истечение)."""
        cache = AdvancedCache(default_ttl=0)
        cache.set("test_cache", "key1", "value1")

        # Даже минимальная задержка должна привести к истечению
        time.sleep(0.01)
        result = cache.get("test_cache", "key1")
        assert result is None

    def test_very_long_ttl(self):
        """Тест с очень длинным TTL."""
        cache = AdvancedCache(default_ttl=86400)  # 1 день
        cache.set("test_cache", "key1", "value1")
        result = cache.get("test_cache", "key1")
        assert result == "value1"

    def test_cache_name_with_special_characters(self):
        """Тест имени кеша со спецсимволами."""
        cache = AdvancedCache()
        cache.set("cache-with-dash_and_underscore.123", "key", "value")
        result = cache.get("cache-with-dash_and_underscore.123", "key")
        assert result == "value"

    def test_large_number_of_keys(self):
        """Тест с большим количеством ключей."""
        cache = AdvancedCache()

        # Добавляем 1000 ключей
        for i in range(1000):
            cache.set("test_cache", f"key_{i}", f"value_{i}")

        # Проверяем несколько случайных
        assert cache.get("test_cache", "key_0") == "value_0"
        assert cache.get("test_cache", "key_500") == "value_500"
        assert cache.get("test_cache", "key_999") == "value_999"

    def test_cache_update_resets_timestamp(self):
        """Тест что обновление значения сбрасывает timestamp."""
        cache = AdvancedCache(default_ttl=2)
        cache.set("test_cache", "key1", "value1")

        time.sleep(1)

        # Обновляем значение
        cache.set("test_cache", "key1", "value2")

        # Ждем еще 1 секунду (в сумме 2, но обновление было 1 сек назад)
        time.sleep(1)

        # Значение должно быть доступно
        result = cache.get("test_cache", "key1")
        assert result == "value2"
