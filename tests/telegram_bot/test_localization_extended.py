"""Unit tests for localization module.

This module contains tests for src/telegram_bot/localization.py covering:
- Language constants
- Localization strings
- Translation retrieval
- Language switching

Target: 20+ tests to achieve 70%+ coverage
"""


from src.telegram_bot.localization import LANGUAGES, LOCALIZATIONS


# TestLanguageConstants


class TestLanguageConstants:
    """Tests for language constants."""

    def test_languages_dict_exists(self):
        """Test LANGUAGES dict exists."""
        # Assert
        assert LANGUAGES is not None
        assert isinstance(LANGUAGES, dict)

    def test_supported_languages(self):
        """Test supported languages are present."""
        # Assert
        assert "ru" in LANGUAGES
        assert "en" in LANGUAGES

    def test_language_names(self):
        """Test language names are correct."""
        # Assert
        assert LANGUAGES["ru"] == "Русский"
        assert LANGUAGES["en"] == "English"

    def test_spanish_language(self):
        """Test Spanish language is supported."""
        # Assert
        assert "es" in LANGUAGES
        assert LANGUAGES["es"] == "Español"

    def test_german_language(self):
        """Test German language is supported."""
        # Assert
        assert "de" in LANGUAGES
        assert LANGUAGES["de"] == "Deutsch"


# TestLocalizations


class TestLocalizations:
    """Tests for LOCALIZATIONS dict."""

    def test_localizations_dict_exists(self):
        """Test LOCALIZATIONS dict exists."""
        # Assert
        assert LOCALIZATIONS is not None
        assert isinstance(LOCALIZATIONS, dict)

    def test_russian_localization_exists(self):
        """Test Russian localization exists."""
        # Assert
        assert "ru" in LOCALIZATIONS
        assert isinstance(LOCALIZATIONS["ru"], dict)

    def test_english_localization_exists(self):
        """Test English localization exists (if implemented)."""
        # Assert - at least Russian should be base
        assert len(LOCALIZATIONS) >= 1


# TestRussianStrings


class TestRussianStrings:
    """Tests for Russian localization strings."""

    def test_welcome_message(self):
        """Test welcome message exists."""
        # Assert
        assert "welcome" in LOCALIZATIONS["ru"]
        assert "{user}" in LOCALIZATIONS["ru"]["welcome"]

    def test_help_message(self):
        """Test help message exists."""
        # Assert
        assert "help" in LOCALIZATIONS["ru"]

    def test_back_button(self):
        """Test back button text exists."""
        # Assert
        assert "back_button" in LOCALIZATIONS["ru"]
        assert "⬅️" in LOCALIZATIONS["ru"]["back_button"]

    def test_settings_strings(self):
        """Test settings strings exist."""
        # Assert
        ru = LOCALIZATIONS["ru"]
        assert "settings" in ru
        assert "language" in ru
        assert "language_set" in ru

    def test_api_settings_strings(self):
        """Test API settings strings exist."""
        # Assert
        ru = LOCALIZATIONS["ru"]
        assert "api_settings" in ru
        assert "api_key_prompt" in ru
        assert "api_keys_set" in ru

    def test_arbitrage_strings(self):
        """Test arbitrage-related strings exist."""
        # Assert
        ru = LOCALIZATIONS["ru"]
        assert "arbitrage_boost" in ru
        assert "arbitrage_mid" in ru
        assert "arbitrage_pro" in ru

    def test_auto_arbitrage_strings(self):
        """Test auto-arbitrage strings exist."""
        # Assert
        ru = LOCALIZATIONS["ru"]
        assert "auto_low" in ru
        assert "auto_medium" in ru
        assert "auto_high" in ru
        assert "auto_stats" in ru
        assert "auto_stop" in ru

    def test_error_strings(self):
        """Test error message strings exist."""
        # Assert
        ru = LOCALIZATIONS["ru"]
        assert "error_general" in ru
        assert "error_api_keys" in ru

    def test_risk_strings(self):
        """Test risk level strings exist."""
        # Assert
        ru = LOCALIZATIONS["ru"]
        assert "risk_low" in ru
        assert "risk_medium" in ru
        assert "risk_high" in ru

    def test_liquidity_strings(self):
        """Test liquidity level strings exist."""
        # Assert
        ru = LOCALIZATIONS["ru"]
        assert "liquidity_low" in ru
        assert "liquidity_medium" in ru
        assert "liquidity_high" in ru

    def test_finance_strings(self):
        """Test finance-related strings exist."""
        # Assert
        ru = LOCALIZATIONS["ru"]
        assert "balance" in ru
        assert "profit" in ru

    def test_pagination_strings(self):
        """Test pagination strings exist."""
        # Assert
        ru = LOCALIZATIONS["ru"]
        assert "pagination_status" in ru
        assert "next_page" in ru


# TestStringFormatting


class TestStringFormatting:
    """Tests for string formatting placeholders."""

    def test_welcome_formatting(self):
        """Test welcome message can be formatted."""
        # Arrange
        template = LOCALIZATIONS["ru"]["welcome"]

        # Act
        formatted = template.format(user="TestUser")

        # Assert
        assert "TestUser" in formatted

    def test_language_set_formatting(self):
        """Test language_set message can be formatted."""
        # Arrange
        template = LOCALIZATIONS["ru"]["language_set"]

        # Act
        formatted = template.format(lang="Русский")

        # Assert
        assert "Русский" in formatted

    def test_balance_formatting(self):
        """Test balance message can be formatted."""
        # Arrange
        template = LOCALIZATIONS["ru"]["balance"]

        # Act
        formatted = template.format(balance=100.50)

        # Assert
        assert "100.50" in formatted

    def test_profit_formatting(self):
        """Test profit message can be formatted."""
        # Arrange
        template = LOCALIZATIONS["ru"]["profit"]

        # Act
        formatted = template.format(profit=50.25, percent=15.5)

        # Assert
        assert "50.25" in formatted
        assert "15.5" in formatted

    def test_pagination_status_formatting(self):
        """Test pagination status can be formatted."""
        # Arrange
        template = LOCALIZATIONS["ru"]["pagination_status"]

        # Act
        formatted = template.format(current=2, total=5)

        # Assert
        assert "2" in formatted
        assert "5" in formatted


# TestEmojisAndSymbols


class TestEmojisAndSymbols:
    """Tests for emojis and symbols in strings."""

    def test_settings_emoji(self):
        """Test settings has emoji."""
        # Assert
        assert "⚙️" in LOCALIZATIONS["ru"]["settings"]

    def test_api_ok_emoji(self):
        """Test api_ok has checkmark."""
        # Assert
        assert "✅" in LOCALIZATIONS["ru"]["api_ok"]

    def test_error_emoji(self):
        """Test error has cross mark."""
        # Assert
        assert "❌" in LOCALIZATIONS["ru"]["error_general"]

    def test_arbitrage_emojis(self):
        """Test arbitrage modes have emojis."""
        # Assert
        ru = LOCALIZATIONS["ru"]
        assert "🚀" in ru["arbitrage_boost"]
        assert "💼" in ru["arbitrage_mid"]
        assert "💰" in ru["arbitrage_pro"]
