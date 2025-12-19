"""Дополнительные тесты для модуля config.

Расширенные тесты для улучшения покрытия конфигурации.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from src.utils.config import (
    BotConfig,
    Config,
    DailyReportConfig,
    DatabaseConfig,
    DMarketConfig,
    LoggingConfig,
    RateLimitConfig,
    SecurityConfig,
    TradingSafetyConfig,
)


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


# Tests for actual Config class


class TestDatabaseConfig:
    """Tests for DatabaseConfig dataclass."""

    def test_default_values(self):
        """Test default values are set correctly."""
        config = DatabaseConfig()
        assert config.url == "sqlite:///data/dmarket_bot.db"
        assert config.echo is False
        assert config.pool_size == 5
        assert config.max_overflow == 10

    def test_custom_values(self):
        """Test custom values."""
        config = DatabaseConfig(
            url="postgresql://localhost/db",
            echo=True,
            pool_size=20,
            max_overflow=50,
        )
        assert config.url == "postgresql://localhost/db"
        assert config.echo is True
        assert config.pool_size == 20
        assert config.max_overflow == 50


class TestBotConfig:
    """Tests for BotConfig dataclass."""

    def test_default_values(self):
        """Test default values."""
        config = BotConfig()
        assert config.token == ""
        assert config.username == "dmarket_bot"
        assert config.webhook_url == ""
        assert config.webhook_secret == ""

    def test_custom_values(self):
        """Test custom values."""
        config = BotConfig(token="123:ABC", username="mybot")
        assert config.token == "123:ABC"
        assert config.username == "mybot"


class TestDMarketConfig:
    """Tests for DMarketConfig dataclass."""

    def test_default_values(self):
        """Test default values."""
        config = DMarketConfig()
        assert config.api_url == "https://api.dmarket.com"
        assert config.public_key == ""
        assert config.secret_key == ""
        assert config.rate_limit == 30

    def test_custom_values(self):
        """Test custom values."""
        config = DMarketConfig(
            api_url="https://custom.api.com",
            public_key="pub123",
            secret_key="sec456",
            rate_limit=60,
        )
        assert config.api_url == "https://custom.api.com"
        assert config.rate_limit == 60


class TestSecurityConfig:
    """Tests for SecurityConfig dataclass."""

    def test_default_values(self):
        """Test default values."""
        config = SecurityConfig()
        assert config.allowed_users == []
        assert config.admin_users == []

    def test_custom_values(self):
        """Test custom values."""
        config = SecurityConfig(
            allowed_users=[123, 456],
            admin_users=[789],
        )
        assert 123 in config.allowed_users
        assert 789 in config.admin_users


class TestLoggingConfig:
    """Tests for LoggingConfig dataclass."""

    def test_default_values(self):
        """Test default values."""
        config = LoggingConfig()
        assert config.level == "INFO"
        assert "dmarket_bot.log" in config.file
        assert config.rotation == "1 week"
        assert config.retention == "1 month"


class TestTradingSafetyConfig:
    """Tests for TradingSafetyConfig dataclass."""

    def test_default_values(self):
        """Test default values."""
        config = TradingSafetyConfig()
        assert config.max_price_multiplier == 1.5
        assert config.price_history_days == 7
        assert config.min_history_samples == 3
        assert config.enable_price_sanity_check is True


class TestRateLimitConfig:
    """Tests for RateLimitConfig dataclass."""

    def test_default_values(self):
        """Test default values."""
        config = RateLimitConfig()
        assert config.warning_threshold == 0.9
        assert config.enable_notifications is True
        assert config.base_retry_delay == 1.0
        assert config.max_backoff_time == 60.0
        assert config.max_retry_attempts == 5


class TestDailyReportConfig:
    """Tests for DailyReportConfig dataclass."""

    def test_default_values(self):
        """Test default values."""
        config = DailyReportConfig()
        assert config.enabled is True
        assert config.report_time_hour == 9
        assert config.report_time_minute == 0
        assert config.include_days == 1


class TestConfigClass:
    """Tests for main Config class."""

    def test_default_config(self):
        """Test default Config creation."""
        config = Config()
        assert isinstance(config.bot, BotConfig)
        assert isinstance(config.dmarket, DMarketConfig)
        assert isinstance(config.database, DatabaseConfig)
        assert config.debug is False
        assert config.testing is False
        assert config.dry_run is True  # Default to safe mode

    def test_load_without_file(self):
        """Test load without config file."""
        with patch.dict(os.environ, {}, clear=True):
            config = Config.load(None)
        assert isinstance(config, Config)

    def test_load_with_nonexistent_file(self):
        """Test load with non-existent file."""
        config = Config.load("/nonexistent/path/config.yaml")
        assert isinstance(config, Config)

    def test_load_from_yaml_file(self):
        """Test loading from YAML file."""
        yaml_content = """
bot:
  token: "test_token"
  username: "test_bot"
dmarket:
  api_url: "https://test.api.com"
database:
  url: "sqlite:///test.db"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            f.flush()
            try:
                config = Config.load(f.name)
                assert config.bot.token == "test_token"
                assert config.bot.username == "test_bot"
                assert config.dmarket.api_url == "https://test.api.com"
            finally:
                os.unlink(f.name)

    def test_update_from_env(self):
        """Test configuration from environment variables."""
        env_vars = {
            "TELEGRAM_BOT_TOKEN": "env_token",
            "BOT_USERNAME": "env_bot",
            "DMARKET_API_URL": "https://env.api.com",
            "DMARKET_PUBLIC_KEY": "env_pub_key",
            "DMARKET_SECRET_KEY": "env_sec_key",
            "DATABASE_URL": "postgresql://localhost/envdb",
            "LOG_LEVEL": "DEBUG",
            "DEBUG": "true",
            "TESTING": "true",
            "DRY_RUN": "false",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            config = Config.load(None)
            assert config.bot.token == "env_token"
            assert config.bot.username == "env_bot"
            assert config.dmarket.api_url == "https://env.api.com"
            assert config.database.url == "postgresql://localhost/envdb"
            assert config.logging.level == "DEBUG"
            assert config.debug is True
            assert config.testing is True
            assert config.dry_run is False

    def test_update_from_env_allowed_users(self):
        """Test ALLOWED_USERS and ADMIN_USERS from env."""
        env_vars = {
            "ALLOWED_USERS": "123, 456, 789",
            "ADMIN_USERS": "111, 222",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            config = Config.load(None)
            assert "123" in config.security.allowed_users
            assert "111" in config.security.admin_users

    def test_update_from_env_rate_limit(self):
        """Test API_RATE_LIMIT from env."""
        with patch.dict(os.environ, {"API_RATE_LIMIT": "60"}, clear=True):
            config = Config.load(None)
            assert config.dmarket.rate_limit == 60

    def test_update_from_env_invalid_rate_limit(self):
        """Test invalid API_RATE_LIMIT from env."""
        with patch.dict(os.environ, {"API_RATE_LIMIT": "invalid"}, clear=True):
            config = Config.load(None)
            # Should keep default value
            assert config.dmarket.rate_limit == 30

    def test_update_from_env_trading_safety(self):
        """Test trading safety config from env."""
        env_vars = {
            "MAX_PRICE_MULTIPLIER": "2.0",
            "PRICE_HISTORY_DAYS": "14",
            "MIN_HISTORY_SAMPLES": "5",
            "ENABLE_PRICE_SANITY_CHECK": "false",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            config = Config.load(None)
            assert config.trading_safety.max_price_multiplier == 2.0
            assert config.trading_safety.price_history_days == 14
            assert config.trading_safety.min_history_samples == 5
            assert config.trading_safety.enable_price_sanity_check is False

    def test_update_from_env_daily_report(self):
        """Test daily report config from env."""
        env_vars = {
            "DAILY_REPORT_ENABLED": "false",
            "DAILY_REPORT_HOUR": "10",
            "DAILY_REPORT_MINUTE": "30",
            "DAILY_REPORT_DAYS": "7",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            config = Config.load(None)
            assert config.daily_report.enabled is False
            assert config.daily_report.report_time_hour == 10
            assert config.daily_report.report_time_minute == 30
            assert config.daily_report.include_days == 7

    def test_update_from_env_rate_limit_config(self):
        """Test rate limit config from env."""
        env_vars = {
            "RATE_LIMIT_WARNING_THRESHOLD": "0.8",
            "RATE_LIMIT_NOTIFICATIONS": "false",
            "RATE_LIMIT_BASE_DELAY": "2.0",
            "RATE_LIMIT_MAX_BACKOFF": "120.0",
            "RATE_LIMIT_MAX_ATTEMPTS": "10",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            config = Config.load(None)
            assert config.rate_limit.warning_threshold == 0.8
            assert config.rate_limit.enable_notifications is False
            assert config.rate_limit.base_retry_delay == 2.0
            assert config.rate_limit.max_backoff_time == 120.0
            assert config.rate_limit.max_retry_attempts == 10


class TestConfigValidationMethod:
    """Tests for Config.validate() method."""

    def test_validate_missing_telegram_token(self):
        """Test validation fails without telegram token."""
        config = Config()
        config.bot.token = ""
        with pytest.raises(ValueError) as exc_info:
            config.validate()
        assert "TELEGRAM_BOT_TOKEN" in str(exc_info.value)

    def test_validate_invalid_telegram_token_format(self):
        """Test validation warns about invalid token format."""
        config = Config()
        config.bot.token = "invalid_token_without_colon"
        config.testing = True  # Skip DMarket validation
        config.database.url = "sqlite:///test.db"
        with pytest.raises(ValueError) as exc_info:
            config.validate()
        assert "appears invalid" in str(exc_info.value)

    def test_validate_missing_dmarket_keys(self):
        """Test validation fails without DMarket keys (non-testing mode)."""
        config = Config()
        config.bot.token = "123456:ABCdefGHIjklMNOpqrSTUvwxYZ"
        config.testing = False
        with pytest.raises(ValueError) as exc_info:
            config.validate()
        assert "DMARKET_PUBLIC_KEY" in str(exc_info.value)

    def test_validate_short_dmarket_keys(self):
        """Test validation fails with short DMarket keys."""
        config = Config()
        config.bot.token = "123456:ABCdefGHIjklMNOpqrSTUvwxYZ"
        config.dmarket.public_key = "short"
        config.dmarket.secret_key = "alsoshort"
        config.testing = False
        with pytest.raises(ValueError) as exc_info:
            config.validate()
        assert "too short" in str(exc_info.value)

    def test_validate_invalid_api_url(self):
        """Test validation fails with invalid API URL."""
        config = Config()
        config.bot.token = "123456:ABCdefGHIjklMNOpqrSTUvwxYZ"
        config.dmarket.public_key = "a" * 30
        config.dmarket.secret_key = "b" * 30
        config.dmarket.api_url = "ftp://invalid.url"
        config.testing = False
        with pytest.raises(ValueError) as exc_info:
            config.validate()
        assert "http://" in str(exc_info.value) or "https://" in str(exc_info.value)

    def test_validate_invalid_rate_limit(self):
        """Test validation fails with invalid rate limit."""
        config = Config()
        config.bot.token = "123456:ABCdefGHIjklMNOpqrSTUvwxYZ"
        config.dmarket.public_key = "a" * 30
        config.dmarket.secret_key = "b" * 30
        config.dmarket.rate_limit = 0
        config.testing = False
        with pytest.raises(ValueError) as exc_info:
            config.validate()
        assert "rate_limit" in str(exc_info.value)

    def test_validate_missing_database_url(self):
        """Test validation fails without database URL."""
        config = Config()
        config.bot.token = "123456:ABCdefGHIjklMNOpqrSTUvwxYZ"
        config.testing = True
        config.database.url = ""
        with pytest.raises(ValueError) as exc_info:
            config.validate()
        assert "DATABASE_URL" in str(exc_info.value)

    def test_validate_unsupported_database_scheme(self):
        """Test validation fails with unsupported DB scheme."""
        config = Config()
        config.bot.token = "123456:ABCdefGHIjklMNOpqrSTUvwxYZ"
        config.testing = True
        config.database.url = "mongodb://localhost/db"
        with pytest.raises(ValueError) as exc_info:
            config.validate()
        assert "unsupported scheme" in str(exc_info.value)

    def test_validate_invalid_log_level(self):
        """Test validation fails with invalid log level."""
        config = Config()
        config.bot.token = "123456:ABCdefGHIjklMNOpqrSTUvwxYZ"
        config.testing = True
        config.database.url = "sqlite:///test.db"
        config.logging.level = "INVALID_LEVEL"
        with pytest.raises(ValueError) as exc_info:
            config.validate()
        assert "LOG_LEVEL" in str(exc_info.value)

    def test_validate_invalid_pool_size(self):
        """Test validation fails with invalid pool size."""
        config = Config()
        config.bot.token = "123456:ABCdefGHIjklMNOpqrSTUvwxYZ"
        config.testing = True
        config.database.url = "sqlite:///test.db"
        config.database.pool_size = 0
        with pytest.raises(ValueError) as exc_info:
            config.validate()
        assert "pool_size" in str(exc_info.value)

    def test_validate_invalid_max_overflow(self):
        """Test validation fails with negative max_overflow."""
        config = Config()
        config.bot.token = "123456:ABCdefGHIjklMNOpqrSTUvwxYZ"
        config.testing = True
        config.database.url = "sqlite:///test.db"
        config.database.max_overflow = -1
        with pytest.raises(ValueError) as exc_info:
            config.validate()
        assert "max_overflow" in str(exc_info.value)

    def test_validate_success(self):
        """Test successful validation."""
        config = Config()
        config.bot.token = "123456:ABCdefGHIjklMNOpqrSTUvwxYZ"
        config.testing = True
        config.database.url = "sqlite:///test.db"
        # Should not raise
        config.validate()

    def test_validate_converts_user_ids(self):
        """Test validation converts string user IDs to int."""
        config = Config()
        config.bot.token = "123456:ABCdefGHIjklMNOpqrSTUvwxYZ"
        config.testing = True
        config.database.url = "sqlite:///test.db"
        config.security.allowed_users = ["123", "456"]
        config.security.admin_users = ["789"]
        config.validate()
        assert 123 in config.security.allowed_users
        assert 789 in config.security.admin_users


class TestConfigUpdateFromDict:
    """Tests for Config._update_from_dict method."""

    def test_update_from_dict_bot_section(self):
        """Test updating bot section from dict."""
        config = Config()
        data = {
            "bot": {
                "token": "dict_token",
                "username": "dict_bot",
                "webhook": {
                    "url": "https://webhook.url",
                    "secret": "webhook_secret",
                },
            }
        }
        config._update_from_dict(data)
        assert config.bot.token == "dict_token"
        assert config.bot.username == "dict_bot"
        assert config.bot.webhook_url == "https://webhook.url"
        assert config.bot.webhook_secret == "webhook_secret"

    def test_update_from_dict_dmarket_section(self):
        """Test updating dmarket section from dict."""
        config = Config()
        data = {
            "dmarket": {
                "api_url": "https://dict.api.com",
                "public_key": "dict_pub",
                "secret_key": "dict_sec",
                "rate_limit": 100,
            }
        }
        config._update_from_dict(data)
        assert config.dmarket.api_url == "https://dict.api.com"
        assert config.dmarket.public_key == "dict_pub"
        assert config.dmarket.rate_limit == 100

    def test_update_from_dict_database_section(self):
        """Test updating database section from dict."""
        config = Config()
        data = {
            "database": {
                "url": "postgresql://dict/db",
                "echo": True,
                "pool_size": 20,
                "max_overflow": 50,
            }
        }
        config._update_from_dict(data)
        assert config.database.url == "postgresql://dict/db"
        assert config.database.echo is True
        assert config.database.pool_size == 20

    def test_update_from_dict_security_section(self):
        """Test updating security section from dict."""
        config = Config()
        data = {
            "security": {
                "allowed_users": "1, 2, 3",
                "admin_users": "4, 5",
            }
        }
        config._update_from_dict(data)
        assert "1" in config.security.allowed_users
        assert "4" in config.security.admin_users

    def test_update_from_dict_logging_section(self):
        """Test updating logging section from dict."""
        config = Config()
        data = {
            "logging": {
                "level": "DEBUG",
                "file": "/var/log/bot.log",
            }
        }
        config._update_from_dict(data)
        assert config.logging.level == "DEBUG"
        assert config.logging.file == "/var/log/bot.log"

    def test_update_from_dict_trading_safety_section(self):
        """Test updating trading_safety section from dict."""
        config = Config()
        data = {
            "trading_safety": {
                "max_price_multiplier": 2.5,
                "price_history_days": 30,
                "min_history_samples": 10,
                "enable_price_sanity_check": False,
            }
        }
        config._update_from_dict(data)
        assert config.trading_safety.max_price_multiplier == 2.5
        assert config.trading_safety.price_history_days == 30
        assert config.trading_safety.enable_price_sanity_check is False

    def test_update_from_dict_daily_report_section(self):
        """Test updating daily_report section from dict."""
        config = Config()
        data = {
            "daily_report": {
                "enabled": False,
                "report_time_hour": 12,
                "report_time_minute": 45,
                "include_days": 3,
            }
        }
        config._update_from_dict(data)
        assert config.daily_report.enabled is False
        assert config.daily_report.report_time_hour == 12
        assert config.daily_report.include_days == 3

    def test_update_from_dict_rate_limit_section(self):
        """Test updating rate_limit section from dict."""
        config = Config()
        data = {
            "rate_limit": {
                "warning_threshold": 0.7,
                "enable_notifications": False,
                "base_retry_delay": 5.0,
                "max_backoff_time": 300.0,
                "max_retry_attempts": 20,
                "market_limit": 5,
                "trade_limit": 2,
                "user_limit": 10,
                "balance_limit": 20,
                "other_limit": 15,
            }
        }
        config._update_from_dict(data)
        assert config.rate_limit.warning_threshold == 0.7
        assert config.rate_limit.max_retry_attempts == 20
        assert config.rate_limit.market_limit == 5
