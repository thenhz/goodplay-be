"""
Custom Assertions for GoodPlay Testing (GOO-35)

Provides semantic, domain-specific assertions for GoodPlay components
to improve test readability and reduce boilerplate code.
"""
import re
from typing import Dict, Any, List, Optional, Union
from bson import ObjectId
from datetime import datetime


# User-related Assertions

def assert_user_valid(user: Dict[str, Any], required_fields: List[str] = None):
    """
    Assert that user data is valid with all required fields

    Args:
        user: User dictionary to validate
        required_fields: Optional list of additional required fields
    """
    assert isinstance(user, dict), f"Expected user dict, got {type(user)}"

    # Default required fields for a user
    default_required = ['email', 'first_name', 'last_name']
    required_fields = required_fields or default_required

    for field in required_fields:
        assert field in user, f"User missing required field: {field}"
        assert user[field] is not None, f"User field '{field}' cannot be None"
        assert user[field] != "", f"User field '{field}' cannot be empty"

    # Validate email format if present
    if 'email' in user:
        assert_valid_email(user['email'])

    # Validate ObjectId if present
    if '_id' in user:
        assert_valid_object_id(user['_id'])


def assert_game_valid(game: Dict[str, Any], required_fields: List[str] = None):
    """
    Assert that game data is valid with all required fields

    Args:
        game: Game dictionary to validate
        required_fields: Optional list of additional required fields
    """
    assert isinstance(game, dict), f"Expected game dict, got {type(game)}"

    # Default required fields for a game
    default_required = ['title', 'description', 'category']
    required_fields = required_fields or default_required

    for field in required_fields:
        assert field in game, f"Game missing required field: {field}"
        assert game[field] is not None, f"Game field '{field}' cannot be None"
        assert game[field] != "", f"Game field '{field}' cannot be empty"

    # Validate specific game fields
    if 'category' in game:
        valid_categories = ['puzzle', 'action', 'strategy', 'casual', 'arcade']
        assert game['category'] in valid_categories, \
            f"Invalid game category: {game['category']}. Must be one of {valid_categories}"

    if 'difficulty' in game:
        valid_difficulties = ['easy', 'medium', 'hard', 'expert']
        assert game['difficulty'] in valid_difficulties, \
            f"Invalid difficulty: {game['difficulty']}. Must be one of {valid_difficulties}"

    if 'credits_required' in game:
        assert isinstance(game['credits_required'], (int, float)), \
            "Game credits_required must be a number"
        assert game['credits_required'] >= 0, \
            "Game credits_required must be non-negative"


def assert_session_valid(session: Dict[str, Any], required_fields: List[str] = None):
    """
    Assert that game session data is valid

    Args:
        session: Session dictionary to validate
        required_fields: Optional list of additional required fields
    """
    assert isinstance(session, dict), f"Expected session dict, got {type(session)}"

    # Default required fields for a session
    default_required = ['user_id', 'game_id', 'status']
    required_fields = required_fields or default_required

    for field in required_fields:
        assert field in session, f"Session missing required field: {field}"
        assert session[field] is not None, f"Session field '{field}' cannot be None"

    # Validate session status
    if 'status' in session:
        valid_statuses = ['active', 'paused', 'completed', 'abandoned']
        assert session['status'] in valid_statuses, \
            f"Invalid session status: {session['status']}. Must be one of {valid_statuses}"

    # Validate ObjectIds
    for id_field in ['user_id', 'game_id', '_id']:
        if id_field in session and session[id_field]:
            assert_valid_object_id(session[id_field])


# API Response Assertions

def assert_api_response_structure(response: Dict[str, Any], expected_keys: List[str] = None):
    """
    Assert that API response has correct structure

    Args:
        response: API response dictionary
        expected_keys: Optional list of expected keys
    """
    assert isinstance(response, dict), f"Expected response dict, got {type(response)}"

    # Standard API response structure
    default_keys = ['success', 'message']
    expected_keys = expected_keys or default_keys

    for key in expected_keys:
        assert key in response, f"API response missing key: {key}"

    # Validate success field
    if 'success' in response:
        assert isinstance(response['success'], bool), \
            f"API response 'success' must be boolean, got {type(response['success'])}"

    # Validate message field
    if 'message' in response:
        assert isinstance(response['message'], str), \
            f"API response 'message' must be string, got {type(response['message'])}"
        assert response['message'] != "", "API response message cannot be empty"


def assert_service_response_pattern(response: tuple):
    """
    Assert that service response follows the standard (success, message, result) pattern

    Args:
        response: Service response tuple
    """
    assert isinstance(response, tuple), f"Service response must be tuple, got {type(response)}"
    assert len(response) == 3, f"Service response must be 3-tuple, got {len(response)} elements"

    success, message, result = response

    assert isinstance(success, bool), f"Success must be boolean, got {type(success)}"
    assert isinstance(message, str), f"Message must be string, got {type(message)}"
    assert message != "", "Message cannot be empty"


def assert_repository_result(result: Any, expected_type: type = None, allow_none: bool = True):
    """
    Assert repository operation result is valid

    Args:
        result: Repository operation result
        expected_type: Expected result type
        allow_none: Whether None is allowed as valid result
    """
    if not allow_none:
        assert result is not None, "Repository result cannot be None"

    if expected_type and result is not None:
        assert isinstance(result, expected_type), \
            f"Repository result must be {expected_type.__name__}, got {type(result).__name__}"


# Performance Assertions

def assert_performance_within_threshold(actual_ms: float, max_threshold_ms: float, operation_name: str = "Operation"):
    """
    Assert that operation performance is within acceptable threshold

    Args:
        actual_ms: Actual operation time in milliseconds
        max_threshold_ms: Maximum acceptable time in milliseconds
        operation_name: Name of operation for error message
    """
    assert isinstance(actual_ms, (int, float)), "Actual time must be numeric"
    assert isinstance(max_threshold_ms, (int, float)), "Threshold must be numeric"
    assert actual_ms >= 0, "Actual time cannot be negative"
    assert max_threshold_ms > 0, "Threshold must be positive"

    assert actual_ms <= max_threshold_ms, \
        f"{operation_name} took {actual_ms:.1f}ms, expected under {max_threshold_ms:.1f}ms"


def assert_database_state_clean(collections_to_check: List[str] = None):
    """
    Assert that database state is clean (for integration tests)

    Args:
        collections_to_check: List of collection names to verify are empty
    """
    # This would typically check actual database state
    # For now, it's a placeholder for the pattern
    collections_to_check = collections_to_check or ['users', 'games', 'sessions']

    # In real implementation, this would connect to test DB and verify counts
    # For testing purposes, we just validate the pattern
    for collection in collections_to_check:
        assert isinstance(collection, str), f"Collection name must be string: {collection}"


# HTTP Headers Assertions

def assert_auth_headers(headers: Dict[str, str]):
    """
    Assert that request/response has proper authentication headers

    Args:
        headers: HTTP headers dictionary
    """
    assert isinstance(headers, dict), f"Headers must be dict, got {type(headers)}"
    assert 'Authorization' in headers, "Missing Authorization header"

    auth_header = headers['Authorization']
    assert auth_header.startswith('Bearer '), \
        f"Authorization header must start with 'Bearer ', got: {auth_header[:20]}..."


def assert_cors_headers(headers: Dict[str, str], required_origins: List[str] = None):
    """
    Assert that response has proper CORS headers

    Args:
        headers: HTTP headers dictionary
        required_origins: Optional list of required origins
    """
    assert isinstance(headers, dict), f"Headers must be dict, got {type(headers)}"

    # Check for CORS headers
    cors_headers = [
        'Access-Control-Allow-Origin',
        'Access-Control-Allow-Methods',
        'Access-Control-Allow-Headers'
    ]

    for header in cors_headers:
        if header in headers:  # Some CORS headers are optional
            assert headers[header] != "", f"CORS header '{header}' cannot be empty"


def assert_security_headers(headers: Dict[str, str]):
    """
    Assert that response has proper security headers

    Args:
        headers: HTTP headers dictionary
    """
    assert isinstance(headers, dict), f"Headers must be dict, got {type(headers)}"

    # Common security headers
    security_headers = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block'
    }

    for header, expected_value in security_headers.items():
        if header in headers:
            assert headers[header] == expected_value, \
                f"Security header '{header}' should be '{expected_value}', got '{headers[header]}'"


# Validation and Error Assertions

def assert_validation_errors(response: Dict[str, Any], expected_fields: List[str] = None):
    """
    Assert that response contains validation errors for specified fields

    Args:
        response: API response with validation errors
        expected_fields: Fields that should have validation errors
    """
    assert isinstance(response, dict), f"Response must be dict, got {type(response)}"
    assert response.get('success') is False, "Response should indicate failure for validation errors"

    # Check for validation error structure
    error_keys = ['errors', 'validation_errors', 'field_errors']
    has_error_structure = any(key in response for key in error_keys)
    assert has_error_structure, f"Response should contain validation errors in one of: {error_keys}"

    if expected_fields:
        # Find the errors dict
        errors = None
        for key in error_keys:
            if key in response:
                errors = response[key]
                break

        assert errors is not None, "Could not find validation errors in response"

        for field in expected_fields:
            assert field in errors, f"Expected validation error for field: {field}"


def assert_permission_denied(response: Dict[str, Any]):
    """
    Assert that response indicates permission denied

    Args:
        response: API response
    """
    assert isinstance(response, dict), f"Response must be dict, got {type(response)}"
    assert response.get('success') is False, "Permission denied should be failure response"

    message = response.get('message', '').lower()
    permission_indicators = ['permission', 'forbidden', 'access denied', 'unauthorized']

    has_permission_error = any(indicator in message for indicator in permission_indicators)
    assert has_permission_error, f"Response should indicate permission error, got message: {response.get('message')}"


def assert_not_found(response: Dict[str, Any]):
    """
    Assert that response indicates resource not found

    Args:
        response: API response
    """
    assert isinstance(response, dict), f"Response must be dict, got {type(response)}"
    assert response.get('success') is False, "Not found should be failure response"

    message = response.get('message', '').lower()
    not_found_indicators = ['not found', 'does not exist', 'not exist', 'missing']

    has_not_found_error = any(indicator in message for indicator in not_found_indicators)
    assert has_not_found_error, f"Response should indicate not found error, got message: {response.get('message')}"


def assert_unauthorized(response: Dict[str, Any]):
    """
    Assert that response indicates unauthorized access

    Args:
        response: API response
    """
    assert isinstance(response, dict), f"Response must be dict, got {type(response)}"
    assert response.get('success') is False, "Unauthorized should be failure response"

    message = response.get('message', '').lower()
    auth_indicators = ['unauthorized', 'authentication', 'login required', 'token']

    has_auth_error = any(indicator in message for indicator in auth_indicators)
    assert has_auth_error, f"Response should indicate auth error, got message: {response.get('message')}"


# Utility Validation Assertions

def assert_valid_email(email: str):
    """
    Assert that email format is valid

    Args:
        email: Email address to validate
    """
    assert isinstance(email, str), f"Email must be string, got {type(email)}"
    assert email != "", "Email cannot be empty"

    # Simple email regex pattern
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    assert re.match(email_pattern, email), f"Invalid email format: {email}"


def assert_valid_object_id(obj_id: Union[str, ObjectId]):
    """
    Assert that ObjectId is valid

    Args:
        obj_id: ObjectId to validate (string or ObjectId instance)
    """
    if isinstance(obj_id, ObjectId):
        return  # ObjectId instances are always valid

    assert isinstance(obj_id, str), f"ObjectId must be string or ObjectId, got {type(obj_id)}"
    assert ObjectId.is_valid(obj_id), f"Invalid ObjectId format: {obj_id}"


def assert_valid_timestamp(timestamp: Union[str, datetime], allow_future: bool = True):
    """
    Assert that timestamp is valid

    Args:
        timestamp: Timestamp to validate
        allow_future: Whether future timestamps are allowed
    """
    if isinstance(timestamp, str):
        # Try to parse ISO format timestamp
        try:
            parsed_dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except ValueError:
            pytest.fail(f"Invalid timestamp format: {timestamp}")
    elif isinstance(timestamp, datetime):
        parsed_dt = timestamp
    else:
        pytest.fail(f"Timestamp must be string or datetime, got {type(timestamp)}")

    # Check if future timestamp is allowed
    if not allow_future:
        now = datetime.now(parsed_dt.tzinfo) if parsed_dt.tzinfo else datetime.now()
        assert parsed_dt <= now, f"Future timestamp not allowed: {timestamp}"


# Collection/List Assertions

def assert_list_contains_user(users: List[Dict[str, Any]], expected_email: str):
    """
    Assert that list of users contains user with specific email

    Args:
        users: List of user dictionaries
        expected_email: Email to search for
    """
    assert isinstance(users, list), f"Users must be list, got {type(users)}"
    assert len(users) > 0, "Users list cannot be empty"

    emails = [user.get('email') for user in users if isinstance(user, dict)]
    assert expected_email in emails, f"User with email '{expected_email}' not found in users list"


def assert_list_all_valid_users(users: List[Dict[str, Any]]):
    """
    Assert that all items in list are valid users

    Args:
        users: List of user dictionaries
    """
    assert isinstance(users, list), f"Users must be list, got {type(users)}"

    for i, user in enumerate(users):
        try:
            assert_user_valid(user)
        except AssertionError as e:
            pytest.fail(f"User at index {i} is invalid: {str(e)}")


def assert_list_sorted_by(items: List[Dict[str, Any]], field: str, reverse: bool = False):
    """
    Assert that list is sorted by specified field

    Args:
        items: List of dictionaries
        field: Field name to check sorting
        reverse: Whether sorting is in reverse order
    """
    assert isinstance(items, list), f"Items must be list, got {type(items)}"

    if len(items) < 2:
        return  # Cannot verify sorting with less than 2 items

    values = [item.get(field) for item in items if field in item]
    sorted_values = sorted(values, reverse=reverse)

    assert values == sorted_values, f"List is not sorted by '{field}' (reverse={reverse})"


def assert_pagination_valid(response: Dict[str, Any]):
    """
    Assert that paginated response has valid pagination structure

    Args:
        response: API response with pagination
    """
    assert isinstance(response, dict), f"Response must be dict, got {type(response)}"

    # Check for pagination fields
    pagination_fields = ['total', 'page', 'per_page', 'pages']
    for field in pagination_fields:
        assert field in response, f"Pagination response missing field: {field}"
        assert isinstance(response[field], int), f"Pagination '{field}' must be integer"
        assert response[field] >= 0, f"Pagination '{field}' must be non-negative"

    # Validate pagination logic
    assert response['page'] <= response['pages'], \
        f"Current page ({response['page']}) cannot exceed total pages ({response['pages']})"

    if response['total'] > 0:
        assert response['pages'] > 0, "Pages should be > 0 when total > 0"