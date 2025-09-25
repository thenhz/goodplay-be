"""
Test Matchers for GoodPlay Testing (GOO-35)

Provides expressive, reusable matchers for common testing patterns
to improve test readability and reduce repetitive validation code.
"""
import re
from typing import Dict, Any, List, Optional, Union, Callable
from bson import ObjectId
from datetime import datetime


class Matcher:
    """Base class for all matchers with fluent interface"""

    def __init__(self, description: str):
        self.description = description
        self._errors = []

    def matches(self, value: Any) -> bool:
        """Check if value matches the criteria"""
        raise NotImplementedError("Subclasses must implement matches()")

    def __call__(self, value: Any) -> bool:
        """Allow matcher to be called as function"""
        return self.matches(value)

    def get_error_message(self) -> str:
        """Get detailed error message for failed match"""
        if self._errors:
            return f"{self.description}: {'; '.join(self._errors)}"
        return f"Value does not match {self.description}"

    def _add_error(self, error: str):
        """Add error to error list"""
        self._errors.append(error)

    def _reset_errors(self):
        """Reset error list for new match attempt"""
        self._errors = []


# Schema Matchers

class UserSchemaMatcher(Matcher):
    """Matcher for user schema validation"""

    def __init__(self, required_fields: List[str] = None, strict: bool = False):
        super().__init__("valid user schema")
        self.required_fields = required_fields or ['email', 'first_name', 'last_name']
        self.strict = strict

    def matches(self, user: Any) -> bool:
        self._reset_errors()

        if not isinstance(user, dict):
            self._add_error(f"Expected dict, got {type(user)}")
            return False

        # Check required fields
        for field in self.required_fields:
            if field not in user:
                self._add_error(f"Missing required field: {field}")
            elif user[field] is None or user[field] == "":
                self._add_error(f"Field '{field}' cannot be empty")

        # Validate email format if present
        if 'email' in user and user['email']:
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, user['email']):
                self._add_error(f"Invalid email format: {user['email']}")

        # Validate ObjectId if present
        if '_id' in user and user['_id']:
            if not ObjectId.is_valid(str(user['_id'])):
                self._add_error(f"Invalid ObjectId: {user['_id']}")

        # Strict mode: check for unexpected fields
        if self.strict:
            allowed_fields = self.required_fields + ['_id', 'created_at', 'updated_at', 'preferences']
            for field in user:
                if field not in allowed_fields:
                    self._add_error(f"Unexpected field in strict mode: {field}")

        return len(self._errors) == 0


class GameSchemaMatcher(Matcher):
    """Matcher for game schema validation"""

    def __init__(self, required_fields: List[str] = None, strict: bool = False):
        super().__init__("valid game schema")
        self.required_fields = required_fields or ['title', 'description', 'category']
        self.strict = strict

    def matches(self, game: Any) -> bool:
        self._reset_errors()

        if not isinstance(game, dict):
            self._add_error(f"Expected dict, got {type(game)}")
            return False

        # Check required fields
        for field in self.required_fields:
            if field not in game:
                self._add_error(f"Missing required field: {field}")
            elif game[field] is None or game[field] == "":
                self._add_error(f"Field '{field}' cannot be empty")

        # Validate category
        if 'category' in game and game['category']:
            valid_categories = ['puzzle', 'action', 'strategy', 'casual', 'arcade']
            if game['category'] not in valid_categories:
                self._add_error(f"Invalid category: {game['category']}. Must be one of {valid_categories}")

        # Validate difficulty
        if 'difficulty' in game and game['difficulty']:
            valid_difficulties = ['easy', 'medium', 'hard', 'expert']
            if game['difficulty'] not in valid_difficulties:
                self._add_error(f"Invalid difficulty: {game['difficulty']}. Must be one of {valid_difficulties}")

        # Validate credits
        if 'credits_required' in game and game['credits_required'] is not None:
            if not isinstance(game['credits_required'], (int, float)):
                self._add_error("Credits must be numeric")
            elif game['credits_required'] < 0:
                self._add_error("Credits cannot be negative")

        return len(self._errors) == 0


class SessionSchemaMatcher(Matcher):
    """Matcher for game session schema validation"""

    def __init__(self, required_fields: List[str] = None):
        super().__init__("valid session schema")
        self.required_fields = required_fields or ['user_id', 'game_id', 'status']

    def matches(self, session: Any) -> bool:
        self._reset_errors()

        if not isinstance(session, dict):
            self._add_error(f"Expected dict, got {type(session)}")
            return False

        # Check required fields
        for field in self.required_fields:
            if field not in session:
                self._add_error(f"Missing required field: {field}")

        # Validate status
        if 'status' in session and session['status']:
            valid_statuses = ['active', 'paused', 'completed', 'abandoned']
            if session['status'] not in valid_statuses:
                self._add_error(f"Invalid status: {session['status']}. Must be one of {valid_statuses}")

        # Validate ObjectIds
        for id_field in ['user_id', 'game_id', '_id']:
            if id_field in session and session[id_field]:
                if not ObjectId.is_valid(str(session[id_field])):
                    self._add_error(f"Invalid ObjectId for {id_field}: {session[id_field]}")

        return len(self._errors) == 0


# API Response Matchers

class APIResponseFormatMatcher(Matcher):
    """Matcher for API response format validation"""

    def __init__(self, expected_keys: List[str] = None, require_data: bool = False):
        super().__init__("valid API response format")
        self.expected_keys = expected_keys or ['success', 'message']
        self.require_data = require_data

    def matches(self, response: Any) -> bool:
        self._reset_errors()

        if not isinstance(response, dict):
            self._add_error(f"Expected dict, got {type(response)}")
            return False

        # Check expected keys
        for key in self.expected_keys:
            if key not in response:
                self._add_error(f"Missing required key: {key}")

        # Validate success field
        if 'success' in response:
            if not isinstance(response['success'], bool):
                self._add_error(f"'success' must be boolean, got {type(response['success'])}")

        # Validate message field
        if 'message' in response:
            if not isinstance(response['message'], str):
                self._add_error(f"'message' must be string, got {type(response['message'])}")
            elif response['message'] == "":
                self._add_error("'message' cannot be empty")

        # Check for data field if required
        if self.require_data and response.get('success', False):
            if 'data' not in response and 'result' not in response:
                self._add_error("Successful response must include 'data' or 'result'")

        return len(self._errors) == 0


# HTTP Headers Matchers

class AuthHeadersMatcher(Matcher):
    """Matcher for authentication headers"""

    def __init__(self, token_type: str = "Bearer"):
        super().__init__(f"valid {token_type} authentication headers")
        self.token_type = token_type

    def matches(self, headers: Any) -> bool:
        self._reset_errors()

        if not isinstance(headers, dict):
            self._add_error(f"Expected dict, got {type(headers)}")
            return False

        if 'Authorization' not in headers:
            self._add_error("Missing Authorization header")
            return False

        auth_header = headers['Authorization']
        if not auth_header.startswith(f"{self.token_type} "):
            self._add_error(f"Authorization header must start with '{self.token_type} '")

        return len(self._errors) == 0


class CORSHeadersMatcher(Matcher):
    """Matcher for CORS headers"""

    def __init__(self, required_origins: List[str] = None):
        super().__init__("valid CORS headers")
        self.required_origins = required_origins or []

    def matches(self, headers: Any) -> bool:
        self._reset_errors()

        if not isinstance(headers, dict):
            self._add_error(f"Expected dict, got {type(headers)}")
            return False

        # Check for Access-Control-Allow-Origin
        if 'Access-Control-Allow-Origin' in headers:
            origin = headers['Access-Control-Allow-Origin']
            if self.required_origins and origin not in self.required_origins and origin != '*':
                self._add_error(f"Origin '{origin}' not in allowed origins: {self.required_origins}")

        return len(self._errors) == 0


# Field Validation Matchers

class RequiredFieldsMatcher(Matcher):
    """Matcher for required fields presence"""

    def __init__(self, required_fields: List[str]):
        super().__init__(f"required fields: {', '.join(required_fields)}")
        self.required_fields = required_fields

    def matches(self, obj: Any) -> bool:
        self._reset_errors()

        if not isinstance(obj, dict):
            self._add_error(f"Expected dict, got {type(obj)}")
            return False

        for field in self.required_fields:
            if field not in obj:
                self._add_error(f"Missing required field: {field}")
            elif obj[field] is None:
                self._add_error(f"Field '{field}' cannot be None")

        return len(self._errors) == 0


class ValidationErrorsMatcher(Matcher):
    """Matcher for validation error responses"""

    def __init__(self, expected_fields: List[str] = None):
        super().__init__("validation errors")
        self.expected_fields = expected_fields or []

    def matches(self, response: Any) -> bool:
        self._reset_errors()

        if not isinstance(response, dict):
            self._add_error(f"Expected dict, got {type(response)}")
            return False

        # Should be a failure response
        if response.get('success') is not False:
            self._add_error("Validation error response should have success=False")

        # Check for error structure
        error_keys = ['errors', 'validation_errors', 'field_errors']
        has_errors = any(key in response for key in error_keys)
        if not has_errors:
            self._add_error(f"Response should contain validation errors in one of: {error_keys}")

        # Check specific field errors if expected
        if self.expected_fields and has_errors:
            errors = None
            for key in error_keys:
                if key in response:
                    errors = response[key]
                    break

            if isinstance(errors, dict):
                for field in self.expected_fields:
                    if field not in errors:
                        self._add_error(f"Expected validation error for field: {field}")

        return len(self._errors) == 0


# Performance Matchers

class PerformanceThresholdMatcher(Matcher):
    """Matcher for performance thresholds"""

    def __init__(self, max_time_ms: float, operation_name: str = "Operation"):
        super().__init__(f"{operation_name} performance under {max_time_ms}ms")
        self.max_time_ms = max_time_ms
        self.operation_name = operation_name

    def matches(self, actual_time_ms: Any) -> bool:
        self._reset_errors()

        if not isinstance(actual_time_ms, (int, float)):
            self._add_error(f"Expected numeric time, got {type(actual_time_ms)}")
            return False

        if actual_time_ms < 0:
            self._add_error("Time cannot be negative")
            return False

        if actual_time_ms > self.max_time_ms:
            self._add_error(f"{self.operation_name} took {actual_time_ms:.1f}ms, expected under {self.max_time_ms:.1f}ms")

        return len(self._errors) == 0


# Data Type Matchers

class ObjectIdMatcher(Matcher):
    """Matcher for valid ObjectId"""

    def __init__(self):
        super().__init__("valid ObjectId")

    def matches(self, value: Any) -> bool:
        self._reset_errors()

        if isinstance(value, ObjectId):
            return True

        if isinstance(value, str):
            if not ObjectId.is_valid(value):
                self._add_error(f"Invalid ObjectId format: {value}")
                return False
            return True

        self._add_error(f"Expected ObjectId or string, got {type(value)}")
        return False


class EmailMatcher(Matcher):
    """Matcher for valid email addresses"""

    def __init__(self):
        super().__init__("valid email address")

    def matches(self, email: Any) -> bool:
        self._reset_errors()

        if not isinstance(email, str):
            self._add_error(f"Expected string, got {type(email)}")
            return False

        if email == "":
            self._add_error("Email cannot be empty")
            return False

        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            self._add_error(f"Invalid email format: {email}")

        return len(self._errors) == 0


class TimestampMatcher(Matcher):
    """Matcher for valid timestamps"""

    def __init__(self, allow_future: bool = True, format_type: str = "iso"):
        super().__init__(f"valid timestamp ({format_type})")
        self.allow_future = allow_future
        self.format_type = format_type

    def matches(self, timestamp: Any) -> bool:
        self._reset_errors()

        if isinstance(timestamp, datetime):
            parsed_dt = timestamp
        elif isinstance(timestamp, str):
            try:
                if self.format_type == "iso":
                    parsed_dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                else:
                    self._add_error(f"Unsupported timestamp format: {self.format_type}")
                    return False
            except ValueError:
                self._add_error(f"Invalid timestamp format: {timestamp}")
                return False
        else:
            self._add_error(f"Expected datetime or string, got {type(timestamp)}")
            return False

        # Check if future timestamps are allowed
        if not self.allow_future:
            now = datetime.now(parsed_dt.tzinfo) if parsed_dt.tzinfo else datetime.now()
            if parsed_dt > now:
                self._add_error(f"Future timestamp not allowed: {timestamp}")

        return len(self._errors) == 0


# Convenience Functions for Creating Matchers

def matches_user_schema(required_fields: List[str] = None, strict: bool = False) -> UserSchemaMatcher:
    """Create a user schema matcher"""
    return UserSchemaMatcher(required_fields, strict)


def matches_game_schema(required_fields: List[str] = None, strict: bool = False) -> GameSchemaMatcher:
    """Create a game schema matcher"""
    return GameSchemaMatcher(required_fields, strict)


def matches_session_schema(required_fields: List[str] = None) -> SessionSchemaMatcher:
    """Create a session schema matcher"""
    return SessionSchemaMatcher(required_fields)


def matches_api_response_format(expected_keys: List[str] = None, require_data: bool = False) -> APIResponseFormatMatcher:
    """Create an API response format matcher"""
    return APIResponseFormatMatcher(expected_keys, require_data)


def has_auth_headers(token_type: str = "Bearer") -> AuthHeadersMatcher:
    """Create an authentication headers matcher"""
    return AuthHeadersMatcher(token_type)


def has_cors_headers(required_origins: List[str] = None) -> CORSHeadersMatcher:
    """Create a CORS headers matcher"""
    return CORSHeadersMatcher(required_origins)


def has_required_fields(required_fields: List[str]) -> RequiredFieldsMatcher:
    """Create a required fields matcher"""
    return RequiredFieldsMatcher(required_fields)


def contains_validation_errors(expected_fields: List[str] = None) -> ValidationErrorsMatcher:
    """Create a validation errors matcher"""
    return ValidationErrorsMatcher(expected_fields)


def matches_performance_threshold(max_time_ms: float, operation_name: str = "Operation") -> PerformanceThresholdMatcher:
    """Create a performance threshold matcher"""
    return PerformanceThresholdMatcher(max_time_ms, operation_name)


def is_valid_object_id() -> ObjectIdMatcher:
    """Create an ObjectId matcher"""
    return ObjectIdMatcher()


def is_valid_email() -> EmailMatcher:
    """Create an email matcher"""
    return EmailMatcher()


def is_valid_timestamp(allow_future: bool = True, format_type: str = "iso") -> TimestampMatcher:
    """Create a timestamp matcher"""
    return TimestampMatcher(allow_future, format_type)


# Composite Matchers

class CompositeMatcher(Matcher):
    """Matcher that combines multiple matchers"""

    def __init__(self, matchers: List[Matcher], operation: str = "all"):
        """
        Args:
            matchers: List of matchers to combine
            operation: 'all' (AND) or 'any' (OR)
        """
        self.matchers = matchers
        self.operation = operation
        descriptions = [matcher.description for matcher in matchers]
        op_word = "all of" if operation == "all" else "any of"
        super().__init__(f"{op_word}: {', '.join(descriptions)}")

    def matches(self, value: Any) -> bool:
        self._reset_errors()

        results = []
        for matcher in self.matchers:
            result = matcher.matches(value)
            results.append(result)
            if not result:
                self._add_error(matcher.get_error_message())

        if self.operation == "all":
            return all(results)
        else:  # any
            return any(results)


def all_of(*matchers: Matcher) -> CompositeMatcher:
    """Create a matcher that requires all sub-matchers to pass"""
    return CompositeMatcher(list(matchers), "all")


def any_of(*matchers: Matcher) -> CompositeMatcher:
    """Create a matcher that requires any sub-matcher to pass"""
    return CompositeMatcher(list(matchers), "any")


# Usage in Tests Example:
"""
def test_user_validation():
    user = {"email": "test@example.com", "first_name": "Test", "last_name": "User"}

    # Using individual matcher
    assert matches_user_schema().matches(user), matches_user_schema().get_error_message()

    # Using composite matcher
    composite = all_of(
        matches_user_schema(['email', 'first_name']),
        has_required_fields(['email'])
    )
    assert composite.matches(user), composite.get_error_message()
"""