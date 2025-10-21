"""
Custom JSON encoder for consistent datetime serialization to ISO 8601 format
"""
from datetime import datetime, date
from bson import ObjectId
from flask.json.provider import DefaultJSONProvider


class ISO8601JSONProvider(DefaultJSONProvider):
    """
    Custom JSON provider that ensures datetime objects are serialized in ISO 8601 format.

    This provider handles:
    - datetime objects -> ISO 8601 string with timezone (e.g., "2025-10-02T09:36:40.123Z")
    - date objects -> ISO 8601 date string (e.g., "2025-10-02")
    - ObjectId -> string representation

    Usage:
        In app initialization:
        app.json = ISO8601JSONProvider(app)
    """

    def default(self, obj):
        """Convert custom types to JSON-serializable formats"""
        if isinstance(obj, datetime):
            # Ensure timezone-aware datetime and format as ISO 8601
            if obj.tzinfo is None:
                # If naive datetime, assume UTC
                from datetime import timezone
                obj = obj.replace(tzinfo=timezone.utc)
            return obj.isoformat()

        elif isinstance(obj, date):
            # Convert date to ISO 8601 format (YYYY-MM-DD)
            return obj.isoformat()

        elif isinstance(obj, ObjectId):
            # Convert MongoDB ObjectId to string
            return str(obj)

        # Let the default provider handle other types
        return super().default(obj)


def serialize_datetime(dt):
    """
    Utility function to serialize a single datetime to ISO 8601 format.

    Args:
        dt: datetime object or None

    Returns:
        ISO 8601 string or None
    """
    if dt is None:
        return None

    if isinstance(dt, datetime):
        from datetime import timezone
        # Ensure timezone-aware
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()

    return str(dt)


def parse_datetime(dt_value):
    """
    Parse a datetime value from various formats to datetime object.

    Args:
        dt_value: datetime object, ISO 8601 string, or None

    Returns:
        datetime object or None

    Raises:
        ValueError: If string cannot be parsed as datetime
    """
    if dt_value is None:
        return None

    if isinstance(dt_value, datetime):
        # Already a datetime object
        from datetime import timezone
        # Ensure timezone-aware
        if dt_value.tzinfo is None:
            dt_value = dt_value.replace(tzinfo=timezone.utc)
        return dt_value

    if isinstance(dt_value, str):
        # Parse ISO 8601 string
        try:
            # Handle various ISO 8601 formats
            from datetime import timezone
            # Try parsing with fromisoformat (Python 3.7+)
            parsed_dt = datetime.fromisoformat(dt_value.replace('Z', '+00:00'))
            # Ensure timezone-aware
            if parsed_dt.tzinfo is None:
                parsed_dt = parsed_dt.replace(tzinfo=timezone.utc)
            return parsed_dt
        except (ValueError, AttributeError):
            # Fallback to strptime for older formats
            try:
                parsed_dt = datetime.strptime(dt_value, '%Y-%m-%dT%H:%M:%S.%f%z')
                return parsed_dt
            except ValueError:
                try:
                    parsed_dt = datetime.strptime(dt_value, '%Y-%m-%dT%H:%M:%S%z')
                    return parsed_dt
                except ValueError:
                    raise ValueError(f"Cannot parse datetime string: {dt_value}")

    raise ValueError(f"Unsupported datetime type: {type(dt_value)}")


def serialize_model_dates(data):
    """
    Recursively serialize all datetime fields in a dict or list to ISO 8601 format.

    This function is useful for model to_dict() methods to ensure consistent date formatting.

    Args:
        data: dict, list, or any other type

    Returns:
        Data with all datetime objects converted to ISO 8601 strings
    """
    if isinstance(data, dict):
        return {key: serialize_model_dates(value) for key, value in data.items()}

    elif isinstance(data, list):
        return [serialize_model_dates(item) for item in data]

    elif isinstance(data, datetime):
        return serialize_datetime(data)

    elif isinstance(data, date):
        return data.isoformat()

    elif isinstance(data, ObjectId):
        return str(data)

    else:
        return data
