"""Tests for AnyTool integration module.

This module contains tests for the safe AnyTool integration with DMarket ToS compliance.
"""

import pytest

from src.utils.anytool_integration import (
    AnyToolConfig,
    AnyToolIntegration,
    create_safe_anytool_config,
    get_anytool_status,
)


class TestAnyToolConfig:
    """Tests for AnyToolConfig dataclass."""

    def test_default_config_is_safe(self) -> None:
        """Test that default config only uses safe backends."""
        config = AnyToolConfig()

        # Default should not include gui or web
        assert "gui" not in config.backend_scope
        assert "web" not in config.backend_scope

        # Should include safe backends
        assert "mcp" in config.backend_scope
        assert "shell" in config.backend_scope

    def test_safe_config_validates(self) -> None:
        """Test that safe config passes validation."""
        config = AnyToolConfig(backend_scope=["mcp", "shell", "system"])

        # Should not raise
        result = config.validate()
        assert result is True

    def test_prohibited_backends_raise_error(self) -> None:
        """Test that prohibited backends raise ValueError."""
        # GUI is prohibited
        config_gui = AnyToolConfig(backend_scope=["mcp", "gui"])
        with pytest.raises(ValueError) as exc_info:
            config_gui.validate()
        assert "gui" in str(exc_info.value).lower()
        assert "blocked" in str(exc_info.value).lower()

        # Web is prohibited
        config_web = AnyToolConfig(backend_scope=["mcp", "web"])
        with pytest.raises(ValueError) as exc_info:
            config_web.validate()
        assert "web" in str(exc_info.value).lower()

    def test_both_prohibited_backends_raise_error(self) -> None:
        """Test that both gui and web in config raises error."""
        config = AnyToolConfig(backend_scope=["mcp", "gui", "web"])
        with pytest.raises(ValueError) as exc_info:
            config.validate()

        error_msg = str(exc_info.value).lower()
        # Should mention DMarket ToS
        assert "dmarket" in error_msg or "tos" in error_msg

    def test_config_to_dict(self) -> None:
        """Test converting config to dictionary."""
        config = AnyToolConfig(
            llm_model="test-model",
            dry_run=True,
            backend_scope=["mcp", "shell"],
        )

        config_dict = config.to_dict()

        assert config_dict["llm"]["model"] == "test-model"
        assert config_dict["trading"]["dry_run"] is True
        assert config_dict["backends"]["scope"] == ["mcp", "shell"]


class TestCreateSafeConfig:
    """Tests for create_safe_anytool_config function."""

    def test_creates_safe_config(self) -> None:
        """Test that factory creates safe config."""
        config = create_safe_anytool_config()

        # Should be validated (no prohibited backends)
        assert "gui" not in config.backend_scope
        assert "web" not in config.backend_scope

    def test_dry_run_parameter(self) -> None:
        """Test dry_run parameter is passed correctly."""
        config_dry = create_safe_anytool_config(dry_run=True)
        assert config_dry.dry_run is True

        config_live = create_safe_anytool_config(dry_run=False)
        assert config_live.dry_run is False

    def test_log_level_parameter(self) -> None:
        """Test log_level parameter is passed correctly."""
        config = create_safe_anytool_config(log_level="DEBUG")
        assert config.log_level == "DEBUG"


class TestGetAnyToolStatus:
    """Tests for get_anytool_status function."""

    def test_returns_status_dict(self) -> None:
        """Test that status function returns expected keys."""
        status = get_anytool_status()

        assert "is_installed" in status
        assert "install_command" in status
        assert "config_path" in status
        assert "allowed_backends" in status
        assert "blocked_backends" in status
        assert "dmarket_tos_compliant" in status

    def test_blocked_backends_are_gui_and_web(self) -> None:
        """Test that blocked backends are gui and web."""
        status = get_anytool_status()

        assert "gui" in status["blocked_backends"]
        assert "web" in status["blocked_backends"]

    def test_allowed_backends_are_safe(self) -> None:
        """Test that allowed backends are safe."""
        status = get_anytool_status()

        assert "mcp" in status["allowed_backends"]
        assert "shell" in status["allowed_backends"]
        # gui and web should NOT be in allowed
        assert "gui" not in status["allowed_backends"]
        assert "web" not in status["allowed_backends"]

    def test_dmarket_tos_compliant(self) -> None:
        """Test that status reports ToS compliance."""
        status = get_anytool_status()
        assert status["dmarket_tos_compliant"] is True


class TestAnyToolIntegration:
    """Tests for AnyToolIntegration class."""

    def test_initialization_with_defaults(self) -> None:
        """Test integration initializes with default config."""
        integration = AnyToolIntegration()

        assert integration.dry_run is True
        assert integration.config is not None

    def test_initialization_with_dry_run_false(self) -> None:
        """Test integration with dry_run=False."""
        integration = AnyToolIntegration(dry_run=False)

        assert integration.dry_run is False

    def test_initialization_with_custom_config(self) -> None:
        """Test integration with custom config."""
        config = create_safe_anytool_config(log_level="DEBUG")
        integration = AnyToolIntegration(config=config)

        assert integration.config.log_level == "DEBUG"


class TestTaskValidation:
    """Tests for task validation in AnyToolIntegration."""

    def test_validate_task_blocks_browser(self) -> None:
        """Test that browser-related tasks are blocked."""
        integration = AnyToolIntegration()

        with pytest.raises(ValueError) as exc_info:
            integration._validate_task("Open browser and navigate to website")

        assert "blocked" in str(exc_info.value).lower()

    def test_validate_task_blocks_scraping(self) -> None:
        """Test that scraping tasks are blocked."""
        integration = AnyToolIntegration()

        with pytest.raises(ValueError) as exc_info:
            integration._validate_task("Scrape prices from the web page")

        assert "blocked" in str(exc_info.value).lower()

    def test_validate_task_blocks_selenium(self) -> None:
        """Test that Selenium tasks are blocked."""
        integration = AnyToolIntegration()

        with pytest.raises(ValueError) as exc_info:
            integration._validate_task("Use selenium to click button")

        assert "blocked" in str(exc_info.value).lower()

    def test_validate_task_allows_api_requests(self) -> None:
        """Test that API-related tasks are allowed."""
        integration = AnyToolIntegration()

        # These should NOT raise
        integration._validate_task("Get my balance using the API")
        integration._validate_task("Find arbitrage opportunities")
        integration._validate_task("Create a target for AK-47")


class TestTaskParsing:
    """Tests for task parsing in AnyToolIntegration."""

    def test_parse_balance_task(self) -> None:
        """Test parsing balance-related tasks."""
        integration = AnyToolIntegration()

        tool_name, args = integration._parse_task("Get my balance")
        assert tool_name == "get_balance"

        tool_name, args = integration._parse_task("Сколько денег на счету?")
        assert tool_name == "get_balance"

    def test_parse_arbitrage_task(self) -> None:
        """Test parsing arbitrage-related tasks."""
        integration = AnyToolIntegration()

        tool_name, args = integration._parse_task("Find arbitrage for csgo")
        assert tool_name == "scan_arbitrage"
        assert args.get("game") == "csgo"

        tool_name, args = integration._parse_task("Find profit in dota2")
        assert tool_name == "scan_arbitrage"
        assert args.get("game") == "dota2"

    def test_parse_target_task(self) -> None:
        """Test parsing target-related tasks."""
        integration = AnyToolIntegration()

        tool_name, args = integration._parse_task("Show my targets")
        assert tool_name == "get_user_targets"

    def test_parse_market_task(self) -> None:
        """Test parsing market-related tasks."""
        integration = AnyToolIntegration()

        tool_name, args = integration._parse_task("Show items on market")
        assert tool_name == "get_market_items"

    def test_parse_unknown_task(self) -> None:
        """Test parsing unknown tasks returns None."""
        integration = AnyToolIntegration()

        tool_name, args = integration._parse_task("Do something random")
        assert tool_name is None
