"""Smoke tests for CI/CD pipeline validation.

These tests verify that basic functionality works correctly
and help identify environment setup issues in CI/CD.
"""

import sys
from pathlib import Path


def test_python_version():
    """Verify Python version is 3.11 or higher."""
    assert sys.version_info >= (3, 11), f"Python 3.11+ required, got {sys.version_info}"


def test_project_structure():
    """Verify essential project directories exist."""
    project_root = Path(__file__).parent.parent

    essential_dirs = [
        project_root / "src",
        project_root / "src" / "dmarket",
        project_root / "src" / "telegram_bot",
        project_root / "src" / "utils",
        project_root / "tests",
    ]

    for directory in essential_dirs:
        assert directory.exists(), f"Missing essential directory: {directory}"


def test_imports_work():
    """Verify that basic imports work correctly."""
    try:
        # Test core module imports
        # Test that pytest is available
        import pytest  # noqa: F401

        import src
        import src.dmarket
        import src.telegram_bot
        import src.utils  # noqa: F401

    except ImportError as e:
        raise AssertionError(f"Import failed: {e}")


def test_config_example_exists():
    """Verify that configuration example exists."""
    project_root = Path(__file__).parent.parent
    env_example = project_root / ".env.example"

    assert env_example.exists(), ".env.example file is missing"


def test_requirements_file_exists():
    """Verify that requirements.txt exists."""
    project_root = Path(__file__).parent.parent
    requirements = project_root / "requirements.txt"

    assert requirements.exists(), "requirements.txt file is missing"


def test_basic_arithmetic():
    """Simple sanity check that pytest is working."""
    assert 1 + 1 == 2
    assert 2 * 3 == 6
    assert 10 / 2 == 5


def test_string_operations():
    """Basic string operations test."""
    test_string = "DMarket Bot"
    assert "Bot" in test_string
    assert test_string.lower() == "dmarket bot"
    assert len(test_string) > 0
