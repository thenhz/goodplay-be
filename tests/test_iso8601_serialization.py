"""
Tests for ISO 8601 datetime serialization across the application.
"""
import pytest
from datetime import datetime, timezone, date
from bson import ObjectId
from app.core.utils.json_encoder import (
    serialize_datetime,
    serialize_model_dates,
    ISO8601JSONProvider
)
from app.core.models.base_model import BaseModel


class TestISO8601Serialization:
    """Test ISO 8601 datetime serialization utilities"""

    def test_serialize_datetime_with_timezone(self):
        """Test serializing timezone-aware datetime"""
        dt = datetime(2025, 10, 2, 9, 36, 40, 123456, tzinfo=timezone.utc)
        result = serialize_datetime(dt)

        assert result == "2025-10-02T09:36:40.123456+00:00"
        assert "T" in result  # ISO 8601 format
        assert result.endswith("+00:00")  # UTC timezone

    def test_serialize_datetime_naive(self):
        """Test serializing naive datetime (assumes UTC)"""
        dt = datetime(2025, 10, 2, 9, 36, 40, 123456)
        result = serialize_datetime(dt)

        assert result == "2025-10-02T09:36:40.123456+00:00"
        assert result.endswith("+00:00")  # Assumes UTC

    def test_serialize_datetime_none(self):
        """Test serializing None value"""
        result = serialize_datetime(None)
        assert result is None

    def test_serialize_date_object(self):
        """Test serializing date object"""
        d = date(2025, 10, 2)
        data = {"date_field": d}
        result = serialize_model_dates(data)

        assert result["date_field"] == "2025-10-02"

    def test_serialize_objectid(self):
        """Test serializing MongoDB ObjectId"""
        obj_id = ObjectId()
        data = {"_id": obj_id}
        result = serialize_model_dates(data)

        assert result["_id"] == str(obj_id)
        assert isinstance(result["_id"], str)

    def test_serialize_nested_dict(self):
        """Test serializing nested dictionary with multiple datetime fields"""
        data = {
            "user": {
                "created_at": datetime(2025, 10, 2, 9, 0, 0, tzinfo=timezone.utc),
                "profile": {
                    "last_login": datetime(2025, 10, 2, 10, 0, 0, tzinfo=timezone.utc)
                }
            }
        }
        result = serialize_model_dates(data)

        assert result["user"]["created_at"] == "2025-10-02T09:00:00+00:00"
        assert result["user"]["profile"]["last_login"] == "2025-10-02T10:00:00+00:00"

    def test_serialize_list_of_dicts(self):
        """Test serializing list of dictionaries with datetime fields"""
        data = [
            {"created_at": datetime(2025, 10, 2, 9, 0, 0, tzinfo=timezone.utc)},
            {"created_at": datetime(2025, 10, 2, 10, 0, 0, tzinfo=timezone.utc)}
        ]
        result = serialize_model_dates(data)

        assert len(result) == 2
        assert result[0]["created_at"] == "2025-10-02T09:00:00+00:00"
        assert result[1]["created_at"] == "2025-10-02T10:00:00+00:00"

    def test_serialize_mixed_types(self):
        """Test serializing dictionary with mixed types"""
        data = {
            "string": "test",
            "number": 123,
            "boolean": True,
            "none": None,
            "datetime": datetime(2025, 10, 2, 9, 0, 0, tzinfo=timezone.utc),
            "list": [1, 2, 3],
            "nested": {
                "date": date(2025, 10, 2)
            }
        }
        result = serialize_model_dates(data)

        assert result["string"] == "test"
        assert result["number"] == 123
        assert result["boolean"] is True
        assert result["none"] is None
        assert result["datetime"] == "2025-10-02T09:00:00+00:00"
        assert result["list"] == [1, 2, 3]
        assert result["nested"]["date"] == "2025-10-02"

    def test_base_model_serialize_dates(self):
        """Test BaseModel.serialize_dates() method"""
        class TestModel(BaseModel):
            def __init__(self):
                self.created_at = datetime(2025, 10, 2, 9, 0, 0, tzinfo=timezone.utc)
                self.updated_at = datetime(2025, 10, 2, 10, 0, 0, tzinfo=timezone.utc)

            def to_dict(self):
                data = {
                    "created_at": self.created_at,
                    "updated_at": self.updated_at
                }
                return self.serialize_dates(data)

        model = TestModel()
        result = model.to_dict()

        assert result["created_at"] == "2025-10-02T09:00:00+00:00"
        assert result["updated_at"] == "2025-10-02T10:00:00+00:00"

    def test_user_model_serialization(self):
        """Test User model uses ISO 8601 serialization"""
        from app.core.models.user import User

        user = User(
            email="test@example.com",
            first_name="Test",
            last_name="User"
        )
        user.set_password("password123")

        user_dict = user.to_dict()

        # Check that datetime fields are strings in ISO 8601 format
        assert isinstance(user_dict["created_at"], str)
        assert isinstance(user_dict["updated_at"], str)
        assert "T" in user_dict["created_at"]
        assert "+" in user_dict["created_at"] or "Z" in user_dict["created_at"]

    def test_iso8601_format_validation(self):
        """Test that serialized dates are valid ISO 8601 format"""
        dt = datetime(2025, 10, 2, 9, 36, 40, 123456, tzinfo=timezone.utc)
        result = serialize_datetime(dt)

        # Try to parse it back to ensure it's valid ISO 8601
        parsed = datetime.fromisoformat(result)
        assert parsed.year == 2025
        assert parsed.month == 10
        assert parsed.day == 2
        assert parsed.hour == 9
        assert parsed.minute == 36
        assert parsed.second == 40

    def test_milliseconds_precision(self):
        """Test that milliseconds are preserved in serialization"""
        dt = datetime(2025, 10, 2, 9, 36, 40, 123000, tzinfo=timezone.utc)
        result = serialize_datetime(dt)

        assert ".123" in result  # Milliseconds should be present

    def test_empty_dict_serialization(self):
        """Test serializing empty dictionary"""
        result = serialize_model_dates({})
        assert result == {}

    def test_empty_list_serialization(self):
        """Test serializing empty list"""
        result = serialize_model_dates([])
        assert result == []
