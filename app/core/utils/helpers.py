"""
Utility helper functions for common operations.
"""
from typing import Any, Union, List
from bson import ObjectId


def extract_user_id(value: Any) -> str:
    """
    Extract user ID from various input types.

    Handles conversion from:
    - String ID (returns as-is)
    - User object with user_id property
    - User object with get_id() method
    - User object with _id attribute
    - Dictionary with 'user_id' key
    - Dictionary with '_id' key
    - ObjectId (converts to string)

    Args:
        value: Input value that may contain or represent a user ID

    Returns:
        User ID as string

    Raises:
        ValueError: If value cannot be converted to a user ID

    Examples:
        >>> extract_user_id("user123")
        'user123'
        >>> extract_user_id(user_object)  # User with user_id property
        'user123'
        >>> extract_user_id({'user_id': 'user123'})
        'user123'
        >>> extract_user_id(ObjectId('507f1f77bcf86cd799439011'))
        '507f1f77bcf86cd799439011'
    """
    # Handle None
    if value is None:
        raise ValueError("Cannot extract user_id from None")

    # Already a string
    if isinstance(value, str):
        return value

    # ObjectId
    if isinstance(value, ObjectId):
        return str(value)

    # User object with user_id property (most common)
    if hasattr(value, 'user_id') and isinstance(value.user_id, (str, type(None))):
        user_id = value.user_id
        if user_id:
            return user_id

    # User object with get_id() method
    if hasattr(value, 'get_id') and callable(value.get_id):
        user_id = value.get_id()
        if user_id:
            return str(user_id)

    # User object with _id attribute
    if hasattr(value, '_id'):
        _id = value._id
        if _id:
            return str(_id)

    # Dictionary with 'user_id' key
    if isinstance(value, dict):
        if 'user_id' in value:
            return str(value['user_id'])
        if '_id' in value:
            return str(value['_id'])

    # Last resort: convert to string
    try:
        result = str(value)
        if result and result != 'None':
            return result
    except Exception:
        pass

    raise ValueError(f"Cannot extract user_id from value of type {type(value)}")


def extract_user_ids(values: List[Any]) -> List[str]:
    """
    Extract user IDs from a list of various input types.

    Args:
        values: List of values that may contain or represent user IDs

    Returns:
        List of user IDs as strings

    Examples:
        >>> extract_user_ids(["user1", user_object, {"user_id": "user3"}])
        ['user1', 'user2', 'user3']
    """
    if not values:
        return []

    user_ids = []
    for value in values:
        try:
            user_id = extract_user_id(value)
            user_ids.append(user_id)
        except ValueError:
            # Skip values that cannot be converted
            continue

    return user_ids


def safe_extract_user_id(value: Any, default: str = None) -> str:
    """
    Safely extract user ID from value, returning default if extraction fails.

    Args:
        value: Input value that may contain or represent a user ID
        default: Default value to return if extraction fails (default: None)

    Returns:
        User ID as string or default value

    Examples:
        >>> safe_extract_user_id("user123")
        'user123'
        >>> safe_extract_user_id(None, "unknown")
        'unknown'
        >>> safe_extract_user_id(invalid_obj, "fallback")
        'fallback'
    """
    try:
        return extract_user_id(value)
    except (ValueError, AttributeError, TypeError):
        return default
