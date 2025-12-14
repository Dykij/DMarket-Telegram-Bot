"""
Тесты для модуля json_utils.

Этот модуль тестирует функциональность JSON сериализации/десериализации
с использованием orjson или fallback на стандартный json.
"""

import io
import json as stdlib_json
from datetime import datetime
from unittest.mock import patch

import pytest

from src.utils import json_utils


class TestJsonDumps:
    """Тесты функции dumps."""

    def test_dumps_simple_dict(self):
        """Тест сериализации простого словаря."""
        # Arrange
        data = {"name": "AK-47", "price": 12.50, "count": 10}

        # Act
        result = json_utils.dumps(data)

        # Assert
        assert isinstance(result, str)
        parsed = stdlib_json.loads(result)
        assert parsed["name"] == "AK-47"
        assert parsed["price"] == 12.50
        assert parsed["count"] == 10

    def test_dumps_list(self):
        """Тест сериализации списка."""
        # Arrange
        data = ["item1", "item2", "item3"]

        # Act
        result = json_utils.dumps(data)

        # Assert
        assert isinstance(result, str)
        parsed = stdlib_json.loads(result)
        assert parsed == data

    def test_dumps_nested_structure(self):
        """Тест сериализации вложенной структуры."""
        # Arrange
        data = {
            "user": {
                "id": 123,
                "items": [{"name": "Item1", "price": 10.0}, {"name": "Item2", "price": 20.0}],
            }
        }

        # Act
        result = json_utils.dumps(data)

        # Assert
        assert isinstance(result, str)
        parsed = stdlib_json.loads(result)
        assert parsed["user"]["id"] == 123
        assert len(parsed["user"]["items"]) == 2

    def test_dumps_with_datetime(self):
        """Тест сериализации с datetime (если orjson доступен)."""
        # Arrange
        data = {"timestamp": datetime(2025, 1, 1, 12, 0, 0)}

        # Act & Assert
        if json_utils.ORJSON_AVAILABLE:
            # orjson поддерживает datetime
            result = json_utils.dumps(data)
            assert isinstance(result, str)
            assert "2025" in result
        else:
            # Стандартный json не поддерживает datetime
            with pytest.raises(TypeError):
                json_utils.dumps(data)

    def test_dumps_unicode(self):
        """Тест сериализации Unicode строк."""
        # Arrange
        data = {"name": "Русское название", "emoji": "🎮"}

        # Act
        result = json_utils.dumps(data)

        # Assert
        assert isinstance(result, str)
        parsed = stdlib_json.loads(result)
        assert parsed["name"] == "Русское название"
        assert parsed["emoji"] == "🎮"


class TestJsonLoads:
    """Тесты функции loads."""

    def test_loads_simple_dict(self):
        """Тест десериализации простого словаря."""
        # Arrange
        json_str = '{"name": "AK-47", "price": 12.50}'

        # Act
        result = json_utils.loads(json_str)

        # Assert
        assert isinstance(result, dict)
        assert result["name"] == "AK-47"
        assert result["price"] == 12.50

    def test_loads_from_bytes(self):
        """Тест десериализации из bytes."""
        # Arrange
        json_bytes = b'{"name": "M4A4", "price": 15.0}'

        # Act
        result = json_utils.loads(json_bytes)

        # Assert
        assert isinstance(result, dict)
        assert result["name"] == "M4A4"
        assert result["price"] == 15.0

    def test_loads_list(self):
        """Тест десериализации списка."""
        # Arrange
        json_str = '["item1", "item2", "item3"]'

        # Act
        result = json_utils.loads(json_str)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 3
        assert result[0] == "item1"

    def test_loads_invalid_json(self):
        """Тест обработки невалидного JSON."""
        # Arrange
        invalid_json = '{"name": "invalid", "price": }'

        # Act & Assert
        with pytest.raises(json_utils.JSONDecodeError):
            json_utils.loads(invalid_json)

    def test_loads_empty_object(self):
        """Тест десериализации пустого объекта."""
        # Arrange
        json_str = "{}"

        # Act
        result = json_utils.loads(json_str)

        # Assert
        assert isinstance(result, dict)
        assert len(result) == 0


class TestJsonDump:
    """Тесты функции dump."""

    def test_dump_to_file(self):
        """Тест записи JSON в файл."""
        # Arrange
        data = {"name": "Test Item", "price": 25.0}
        fp = io.BytesIO() if json_utils.ORJSON_AVAILABLE else io.StringIO()

        # Act
        json_utils.dump(data, fp)

        # Assert
        fp.seek(0)
        if json_utils.ORJSON_AVAILABLE:
            result = stdlib_json.loads(fp.read().decode("utf-8"))
        else:
            result = stdlib_json.loads(fp.read())
        assert result["name"] == "Test Item"
        assert result["price"] == 25.0

    def test_dump_list_to_file(self):
        """Тест записи списка в файл."""
        # Arrange
        data = ["item1", "item2", "item3"]
        fp = io.BytesIO() if json_utils.ORJSON_AVAILABLE else io.StringIO()

        # Act
        json_utils.dump(data, fp)

        # Assert
        fp.seek(0)
        if json_utils.ORJSON_AVAILABLE:
            result = stdlib_json.loads(fp.read().decode("utf-8"))
        else:
            result = stdlib_json.loads(fp.read())
        assert result == data


class TestJsonLoad:
    """Тесты функции load."""

    def test_load_from_file(self):
        """Тест чтения JSON из файла."""
        # Arrange
        data = '{"name": "File Item", "price": 30.0}'
        fp = io.BytesIO(data.encode("utf-8")) if json_utils.ORJSON_AVAILABLE else io.StringIO(data)

        # Act
        result = json_utils.load(fp)

        # Assert
        assert isinstance(result, dict)
        assert result["name"] == "File Item"
        assert result["price"] == 30.0

    def test_load_list_from_file(self):
        """Тест чтения списка из файла."""
        # Arrange
        data = '["a", "b", "c"]'
        fp = io.BytesIO(data.encode("utf-8")) if json_utils.ORJSON_AVAILABLE else io.StringIO(data)

        # Act
        result = json_utils.load(fp)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 3
        assert result[1] == "b"


class TestRoundTrip:
    """Тесты циклического преобразования (dumps -> loads)."""

    def test_roundtrip_dict(self):
        """Тест цикла сериализация -> десериализация."""
        # Arrange
        original_data = {
            "user_id": 12345,
            "username": "test_user",
            "balance": 1000.50,
            "items": ["item1", "item2"],
        }

        # Act
        json_str = json_utils.dumps(original_data)
        restored_data = json_utils.loads(json_str)

        # Assert
        assert restored_data == original_data

    def test_roundtrip_file_operations(self):
        """Тест цикла dump -> load через файл."""
        # Arrange
        original_data = {"test": "data", "number": 42}
        fp = io.BytesIO() if json_utils.ORJSON_AVAILABLE else io.StringIO()

        # Act
        json_utils.dump(original_data, fp)
        fp.seek(0)
        restored_data = json_utils.load(fp)

        # Assert
        assert restored_data == original_data


class TestFallbackBehavior:
    """Тесты fallback поведения на стандартный json."""

    def test_dumps_without_orjson(self):
        """Тест dumps без orjson."""
        # Arrange
        data = {"key": "value"}

        # Act
        with patch.object(json_utils, "ORJSON_AVAILABLE", False):
            result = json_utils.dumps(data)

        # Assert
        assert isinstance(result, str)
        assert json_utils.loads(result) == data

    def test_loads_without_orjson(self):
        """Тест loads без orjson."""
        # Arrange
        json_str = '{"key": "value"}'

        # Act
        with patch.object(json_utils, "ORJSON_AVAILABLE", False):
            result = json_utils.loads(json_str)

        # Assert
        assert isinstance(result, dict)
        assert result["key"] == "value"

    def test_dump_without_orjson(self):
        """Тест dump без orjson."""
        # Arrange
        data = {"key": "value"}
        fp = io.StringIO()

        # Act
        with patch.object(json_utils, "ORJSON_AVAILABLE", False):
            json_utils.dump(data, fp)

        # Assert
        fp.seek(0)
        result = stdlib_json.loads(fp.read())
        assert result == data

    def test_load_without_orjson(self):
        """Тест load без orjson."""
        # Arrange
        data = '{"key": "value"}'
        fp = io.StringIO(data)

        # Act
        with patch.object(json_utils, "ORJSON_AVAILABLE", False):
            result = json_utils.load(fp)

        # Assert
        assert result == {"key": "value"}


class TestEdgeCases:
    """Тесты граничных случаев."""

    def test_dumps_empty_dict(self):
        """Тест сериализации пустого словаря."""
        # Arrange
        data = {}

        # Act
        result = json_utils.dumps(data)

        # Assert
        assert result == "{}"

    def test_dumps_empty_list(self):
        """Тест сериализации пустого списка."""
        # Arrange
        data = []

        # Act
        result = json_utils.dumps(data)

        # Assert
        assert result == "[]"

    def test_dumps_null(self):
        """Тест сериализации None."""
        # Arrange
        data = None

        # Act
        result = json_utils.dumps(data)

        # Assert
        assert result == "null"

    def test_loads_null(self):
        """Тест десериализации null."""
        # Arrange
        json_str = "null"

        # Act
        result = json_utils.loads(json_str)

        # Assert
        assert result is None

    def test_dumps_boolean(self):
        """Тест сериализации булевых значений."""
        # Arrange
        data = {"enabled": True, "disabled": False}

        # Act
        result = json_utils.dumps(data)

        # Assert
        parsed = json_utils.loads(result)
        assert parsed["enabled"] is True
        assert parsed["disabled"] is False

    def test_dumps_number_types(self):
        """Тест сериализации различных числовых типов."""
        # Arrange
        data = {"int": 42, "float": 3.14, "negative": -10, "zero": 0}

        # Act
        result = json_utils.dumps(data)

        # Assert
        parsed = json_utils.loads(result)
        assert parsed["int"] == 42
        assert abs(parsed["float"] - 3.14) < 0.01
        assert parsed["negative"] == -10
        assert parsed["zero"] == 0
