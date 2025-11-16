"""Тесты для модуля performance."""

import asyncio
import time

import pytest

from src.utils.performance import (
    AdvancedCache,
    AsyncBatch,
    cached,
    global_cache,
    profile_performance,
)


class TestAdvancedCache:
    """Тесты для класса AdvancedCache."""

    def test_init_default_ttl(self):
        """Тест инициализации с TTL по умолчанию."""
        cache = AdvancedCache()
        assert cache._default_ttl == 300

    def test_init_custom_ttl(self):
        """Тест инициализации с кастомным TTL."""
        cache = AdvancedCache(default_ttl=600)
        assert cache._default_ttl == 600

    def test_register_cache(self):
        """Тест регистрации нового кеша."""
        cache = AdvancedCache()
        cache.register_cache("test_cache", ttl=100)

        assert "test_cache" in cache._caches
        assert cache._ttls["test_cache"] == 100

    def test_register_cache_default_ttl(self):
        """Тест регистрации кеша с TTL по умолчанию."""
        cache = AdvancedCache(default_ttl=500)
        cache.register_cache("test_cache")

        assert cache._ttls["test_cache"] == 500

    def test_set_and_get(self):
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

    def test_get_expired_cache(self):
        """Тест получения устаревшего кеша."""
        cache = AdvancedCache()
        cache.register_cache("test_cache", ttl=0)  # TTL = 0 секунд
        cache.set("test_cache", "key1", "value1")

        # Ждем немного, чтобы кеш устарел
        time.sleep(0.01)

        result = cache.get("test_cache", "key1")
        assert result is None

    def test_invalidate_by_key(self):
        """Тест инвалидации по ключу."""
        cache = AdvancedCache()
        cache.set("test_cache", "key1", "value1")
        cache.set("test_cache", "key2", "value2")

        cache.invalidate("test_cache", "key1")

        assert cache.get("test_cache", "key1") is None
        assert cache.get("test_cache", "key2") == "value2"

    def test_invalidate_entire_cache(self):
        """Тест полной инвалидации кеша."""
        cache = AdvancedCache()
        cache.set("test_cache", "key1", "value1")
        cache.set("test_cache", "key2", "value2")

        cache.invalidate("test_cache")

        assert cache.get("test_cache", "key1") is None
        assert cache.get("test_cache", "key2") is None

    def test_clear_all(self):
        """Тест очистки всех кешей."""
        cache = AdvancedCache()
        cache.set("cache1", "key1", "value1")
        cache.set("cache2", "key2", "value2")

        cache.clear_all()

        assert cache.get("cache1", "key1") is None
        assert cache.get("cache2", "key2") is None

    def test_stats(self):
        """Тест получения статистики кеша."""
        cache = AdvancedCache()
        cache.register_cache("test_cache", ttl=100)

        # Несколько операций для статистики
        cache.get("test_cache", "key1")  # miss
        cache.set("test_cache", "key1", "value1")
        cache.get("test_cache", "key1")  # hit
        cache.get("test_cache", "key2")  # miss

        stats = cache.get_stats()

        assert stats["hits"] == 1
        assert stats["misses"] == 2
        assert "test_cache" in stats["caches"]
        assert stats["caches"]["test_cache"]["size"] == 1
        assert stats["caches"]["test_cache"]["ttl"] == 100

    def test_hit_rate_calculation(self):
        """Тест расчета hit rate."""
        cache = AdvancedCache()
        cache.set("test_cache", "key1", "value1")

        # 3 hits, 1 miss
        cache.get("test_cache", "key1")  # hit
        cache.get("test_cache", "key1")  # hit
        cache.get("test_cache", "key1")  # hit
        cache.get("test_cache", "key2")  # miss

        stats = cache.get_stats()
        assert stats["hit_rate_percent"] == 75.0


class TestCachedDecorator:
    """Тесты для декоратора @cached."""

    def test_cached_sync_function(self):
        """Тест кеширования синхронной функции."""
        call_count = 0

        @cached(cache_name="test_sync", ttl=10)
        def expensive_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        # Первый вызов
        result1 = expensive_function(5)
        assert result1 == 10
        assert call_count == 1

        # Второй вызов (должен вернуть из кеша)
        result2 = expensive_function(5)
        assert result2 == 10
        assert call_count == 1  # Функция не вызывалась повторно

    @pytest.mark.asyncio()
    async def test_cached_async_function(self):
        """Тест кеширования асинхронной функции."""
        call_count = 0

        @cached(cache_name="test_async", ttl=10)
        async def expensive_async_function(x):
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.01)
            return x * 2

        # Первый вызов
        result1 = await expensive_async_function(5)
        assert result1 == 10
        assert call_count == 1

        # Второй вызов (должен вернуть из кеша)
        result2 = await expensive_async_function(5)
        assert result2 == 10
        assert call_count == 1

    def test_cached_with_custom_key_function(self):
        """Тест кеширования с кастомной функцией ключа."""
        call_count = 0

        def key_func(x, y):
            return f"{x}_{y}"

        @cached(cache_name="test_custom_key", key_function=key_func, ttl=10)
        def add_numbers(x, y):
            nonlocal call_count
            call_count += 1
            return x + y

        # Первый вызов
        result1 = add_numbers(2, 3)
        assert result1 == 5
        assert call_count == 1

        # Второй вызов (из кеша)
        result2 = add_numbers(2, 3)
        assert result2 == 5
        assert call_count == 1

        # Другие аргументы
        result3 = add_numbers(3, 4)
        assert result3 == 7
        assert call_count == 2


class TestProfilePerformance:
    """Тесты для декоратора @profile_performance."""

    def test_profile_sync_function(self, caplog):
        """Тест профилирования синхронной функции."""

        @profile_performance
        def slow_function():
            time.sleep(0.01)
            return "done"

        result = slow_function()
        assert result == "done"

        # Проверяем что время выполнения было залогировано
        assert any("Время выполнения" in record.message for record in caplog.records)

    @pytest.mark.asyncio()
    async def test_profile_async_function(self, caplog):
        """Тест профилирования асинхронной функции."""

        @profile_performance
        async def slow_async_function():
            await asyncio.sleep(0.01)
            return "done"

        result = await slow_async_function()
        assert result == "done"

        # Проверяем что время выполнения было залогировано
        assert any("Время выполнения" in record.message for record in caplog.records)


class TestAsyncBatch:
    """Тесты для класса AsyncBatch."""

    def test_init_default_values(self):
        """Тест инициализации с параметрами по умолчанию."""
        batch = AsyncBatch()
        assert batch.max_concurrent == 5
        assert batch.delay == 0.1

    def test_init_custom_values(self):
        """Тест инициализации с кастомными параметрами."""
        batch = AsyncBatch(max_concurrent=10, delay_between_batches=0.5)
        assert batch.max_concurrent == 10
        assert batch.delay == 0.5

    @pytest.mark.asyncio()
    async def test_execute_tasks(self):
        """Тест выполнения асинхронных задач."""

        async def task(x):
            await asyncio.sleep(0.01)
            return x * 2

        batch = AsyncBatch(max_concurrent=3)
        tasks = [task(i) for i in range(5)]

        results = await batch.execute(tasks)

        assert len(results) == 5
        assert results == [0, 2, 4, 6, 8]

    @pytest.mark.asyncio()
    async def test_execute_with_concurrency_limit(self):
        """Тест ограничения конкурентности."""
        concurrent_count = 0
        max_concurrent = 0

        async def tracked_task(x):
            nonlocal concurrent_count, max_concurrent
            concurrent_count += 1
            max_concurrent = max(max_concurrent, concurrent_count)
            await asyncio.sleep(0.01)
            concurrent_count -= 1
            return x

        batch = AsyncBatch(max_concurrent=3)
        tasks = [tracked_task(i) for i in range(10)]

        await batch.execute(tasks)

        # Проверяем что не было более 3 одновременных задач
        assert max_concurrent <= 3

    @pytest.mark.asyncio()
    async def test_execute_empty_list(self):
        """Тест выполнения пустого списка задач."""
        batch = AsyncBatch()
        results = await batch.execute([])
        assert results == []

    @pytest.mark.asyncio()
    async def test_execute_single_task(self):
        """Тест выполнения одной задачи."""

        async def task():
            return "result"

        batch = AsyncBatch()
        results = await batch.execute([task()])

        assert len(results) == 1
        assert results[0] == "result"


class TestGlobalCache:
    """Тесты для глобального кеша."""

    def test_global_cache_exists(self):
        """Проверка существования глобального кеша."""
        assert global_cache is not None
        assert isinstance(global_cache, AdvancedCache)

    def test_global_cache_shared_state(self):
        """Проверка что глобальный кеш имеет общее состояние."""
        global_cache.set("test", "key1", "value1")

        # Импортируем глобальный кеш снова
        from src.utils.performance import global_cache as gc2

        assert gc2.get("test", "key1") == "value1"


class TestCacheIntegration:
    """Интеграционные тесты для кеша."""

    def test_multiple_caches(self):
        """Тест работы с несколькими кешами одновременно."""
        cache = AdvancedCache()

        cache.register_cache("cache1", ttl=100)
        cache.register_cache("cache2", ttl=200)

        cache.set("cache1", "key", "value1")
        cache.set("cache2", "key", "value2")

        assert cache.get("cache1", "key") == "value1"
        assert cache.get("cache2", "key") == "value2"

    def test_cache_with_complex_keys(self):
        """Тест кеширования с составными ключами."""
        cache = AdvancedCache()

        # Tuple как ключ
        cache.set("test", ("arg1", "arg2"), "result")
        assert cache.get("test", ("arg1", "arg2")) == "result"

        # Dict items как ключ
        cache.set("test", (("key1", "value1"), ("key2", "value2")), "result2")
        assert cache.get("test", (("key1", "value1"), ("key2", "value2"))) == "result2"

    @pytest.mark.asyncio()
    async def test_async_cache_performance(self):
        """Тест производительности асинхронного кеширования."""
        execution_times = []

        @cached(cache_name="perf_test", ttl=60)
        async def slow_calculation(x):
            start = time.time()
            await asyncio.sleep(0.1)  # Имитация долгой операции
            execution_times.append(time.time() - start)
            return x * 2

        # Первый вызов - медленный
        await slow_calculation(5)

        # Второй вызов - из кеша, должен быть быстрее
        await slow_calculation(5)

        assert len(execution_times) == 1  # Только первый вызов выполнил функцию
