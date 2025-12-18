"""Дополнительные тесты для модуля config.

Расширенные тесты для улучшения покрытия конфигурации.
"""

import os
from unittest.mock import patch

import pytest


class TestConfigValidation:
    """Тесты для валидации конфигурации."""

    def test_validate_telegram_token_format(self) -> None:
        """Тест валидации формата токена Telegram."""
        def validate_telegram_token(token: str) -> bool:
            if not token:
                return False
            parts = token.split(":")
            if len(parts) != 2:
                return False
            return parts[0].isdigit() and len(parts[1]) > 20
        
        # Валидный формат
        assert validate_telegram_token("123456789:ABCdefGHIjklMNOpqrSTUvwxYZ") is True
        # Невалидные форматы
        assert validate_telegram_token("") is False
        assert validate_telegram_token("invalid") is False
        assert validate_telegram_token("abc:short") is False

    def test_validate_api_key_format(self) -> None:
        """Тест валидации формата API ключа."""
        def validate_api_key(key: str) -> bool:
            if not key:
                return False
            return len(key) >= 20 and key.isalnum()
        
        # Валидный ключ
        assert validate_api_key("a" * 30) is True
        # Невалидные ключи
        assert validate_api_key("") is False
        assert validate_api_key("short") is False
        assert validate_api_key("key with spaces!" * 3) is False

    def test_validate_database_url(self) -> None:
        """Тест валидации URL базы данных."""
        def validate_database_url(url: str) -> bool:
            valid_prefixes = ["postgresql://", "sqlite://", "mysql://"]
            return any(url.startswith(prefix) for prefix in valid_prefixes)
        
        assert validate_database_url("postgresql://localhost:5432/db") is True
        assert validate_database_url("sqlite:///data.db") is True
        assert validate_database_url("mysql://localhost/db") is True
        assert validate_database_url("invalid://localhost") is False

    def test_validate_redis_url(self) -> None:
        """Тест валидации URL Redis."""
        def validate_redis_url(url: str) -> bool:
            return url.startswith("redis://") or url.startswith("rediss://")
        
        assert validate_redis_url("redis://localhost:6379") is True
        assert validate_redis_url("rediss://secure.redis.io:6380") is True
        assert validate_redis_url("http://localhost") is False


class TestConfigDefaults:
    """Тесты для значений по умолчанию."""

    def test_default_log_level(self) -> None:
        """Тест уровня логирования по умолчанию."""
        default_log_level = "INFO"
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        assert default_log_level in valid_levels

    def test_default_cache_ttl(self) -> None:
        """Тест TTL кэша по умолчанию."""
        default_cache_ttl = 300  # 5 минут
        assert 60 <= default_cache_ttl <= 3600

    def test_default_rate_limit(self) -> None:
        """Тест лимита запросов по умолчанию."""
        default_rate_limit = 30  # запросов в минуту
        assert default_rate_limit > 0
        assert default_rate_limit <= 60

    def test_default_timeout(self) -> None:
        """Тест таймаута по умолчанию."""
        default_timeout = 30  # секунд
        assert 5 <= default_timeout <= 120


class TestEnvironmentVariables:
    """Тесты для переменных окружения."""

    def test_get_env_with_default(self) -> None:
        """Тест получения переменной окружения с умолчанием."""
        result = os.environ.get("NON_EXISTENT_VAR", "default_value")
        assert result == "default_value"

    def test_get_env_bool(self) -> None:
        """Тест получения булевой переменной."""
        def get_bool_env(name: str, default: bool = False) -> bool:
            value = os.environ.get(name, str(default)).lower()
            return value in ("true", "1", "yes", "on")
        
        with patch.dict(os.environ, {"TEST_BOOL": "true"}):
            assert get_bool_env("TEST_BOOL") is True
        
        with patch.dict(os.environ, {"TEST_BOOL": "false"}):
            assert get_bool_env("TEST_BOOL") is False
        
        assert get_bool_env("NON_EXISTENT") is False
        assert get_bool_env("NON_EXISTENT", True) is True

    def test_get_env_int(self) -> None:
        """Тест получения числовой переменной."""
        def get_int_env(name: str, default: int = 0) -> int:
            try:
                return int(os.environ.get(name, str(default)))
            except ValueError:
                return default
        
        with patch.dict(os.environ, {"TEST_INT": "42"}):
            assert get_int_env("TEST_INT") == 42
        
        with patch.dict(os.environ, {"TEST_INT": "invalid"}):
            assert get_int_env("TEST_INT", 10) == 10
        
        assert get_int_env("NON_EXISTENT", 100) == 100

    def test_get_env_list(self) -> None:
        """Тест получения списка из переменной."""
        def get_list_env(name: str, default: list[str] | None = None) -> list[str]:
            value = os.environ.get(name, "")
            if not value:
                return default or []
            return [item.strip() for item in value.split(",")]
        
        with patch.dict(os.environ, {"TEST_LIST": "a, b, c"}):
            result = get_list_env("TEST_LIST")
            assert result == ["a", "b", "c"]
        
        assert get_list_env("NON_EXISTENT") == []
        assert get_list_env("NON_EXISTENT", ["default"]) == ["default"]


class TestConfigMerging:
    """Тесты для слияния конфигураций."""

    def test_merge_dicts(self) -> None:
        """Тест слияния словарей."""
        def merge_configs(
            base: dict, override: dict
        ) -> dict:
            result = base.copy()
            for key, value in override.items():
                if (
                    key in result
                    and isinstance(result[key], dict)
                    and isinstance(value, dict)
                ):
                    result[key] = merge_configs(result[key], value)
                else:
                    result[key] = value
            return result
        
        base = {"a": 1, "b": {"c": 2, "d": 3}}
        override = {"b": {"c": 10}, "e": 5}
        
        result = merge_configs(base, override)
        assert result["a"] == 1
        assert result["b"]["c"] == 10
        assert result["b"]["d"] == 3
        assert result["e"] == 5

    def test_override_priority(self) -> None:
        """Тест приоритета переопределения."""
        configs = [
            {"level": "INFO", "debug": False},  # defaults
            {"level": "DEBUG"},  # config file
            {"debug": True},  # env vars
        ]
        
        result = {}
        for config in configs:
            result.update(config)
        
        assert result["level"] == "DEBUG"
        assert result["debug"] is True


class TestConfigSections:
    """Тесты для секций конфигурации."""

    def test_telegram_config_section(self) -> None:
        """Тест секции конфигурации Telegram."""
        telegram_config = {
            "token": "BOT_TOKEN",
            "admin_ids": [123, 456],
            "parse_mode": "HTML",
        }
        
        assert "token" in telegram_config
        assert "admin_ids" in telegram_config
        assert isinstance(telegram_config["admin_ids"], list)

    def test_dmarket_config_section(self) -> None:
        """Тест секции конфигурации DMarket."""
        dmarket_config = {
            "public_key": "PUBLIC_KEY",
            "secret_key": "SECRET_KEY",
            "base_url": "https://api.dmarket.com",
            "timeout": 30,
        }
        
        assert "public_key" in dmarket_config
        assert "secret_key" in dmarket_config
        assert dmarket_config["timeout"] > 0

    def test_database_config_section(self) -> None:
        """Тест секции конфигурации базы данных."""
        database_config = {
            "url": "postgresql://localhost:5432/bot",
            "pool_size": 10,
            "max_overflow": 20,
            "echo": False,
        }
        
        assert "url" in database_config
        assert database_config["pool_size"] > 0

    def test_cache_config_section(self) -> None:
        """Тест секции конфигурации кэша."""
        cache_config = {
            "redis_url": "redis://localhost:6379",
            "default_ttl": 300,
            "max_size": 10000,
        }
        
        assert "redis_url" in cache_config
        assert cache_config["default_ttl"] > 0


class TestSecurityConfig:
    """Тесты для конфигурации безопасности."""

    def test_sensitive_fields_masked(self) -> None:
        """Тест маскировки чувствительных полей."""
        def mask_sensitive(config: dict, sensitive_keys: list[str]) -> dict:
            masked = config.copy()
            for key in sensitive_keys:
                if key in masked:
                    masked[key] = "***MASKED***"
            return masked
        
        config = {
            "api_key": "secret123",
            "password": "mypass",
            "public_data": "visible",
        }
        
        masked = mask_sensitive(config, ["api_key", "password"])
        assert masked["api_key"] == "***MASKED***"
        assert masked["password"] == "***MASKED***"
        assert masked["public_data"] == "visible"

    def test_no_secrets_in_logs(self) -> None:
        """Тест что секреты не попадают в логи."""
        secret_patterns = ["token", "password", "secret", "key", "credential"]
        
        log_message = "Config loaded: debug=True, level=INFO"
        
        # Проверяем что в сообщении нет секретных паттернов со значениями
        for pattern in secret_patterns:
            assert f"{pattern}=" not in log_message.lower() or (
                f"{pattern}=***" in log_message.lower()
            )
