"""
GoodPlay Testing Utilities Package (GOO-35)

Complete testing utilities package with assertions, matchers, builders,
mocks, and parametrized test decorators for standardized testing patterns.
"""

# Core utilities
from .assertions import *
from .matchers import *
from .builders import *
from .mocks import *
from .decorators import *

# Package metadata
__version__ = '1.0.0'
__author__ = 'GoodPlay Team'
__description__ = 'Complete testing utilities package for GoodPlay'

__all__ = [
    # Assertions
    'assert_user_valid',
    'assert_game_valid',
    'assert_session_valid',
    'assert_api_response_structure',
    'assert_service_response_pattern',
    'assert_repository_result',
    'assert_performance_within_threshold',
    'assert_database_state_clean',
    'assert_auth_headers',
    'assert_cors_headers',
    'assert_security_headers',
    'assert_validation_errors',
    'assert_permission_denied',
    'assert_not_found',
    'assert_unauthorized',

    # Matchers
    'matches_user_schema',
    'matches_game_schema',
    'matches_session_schema',
    'matches_api_response_format',
    'has_auth_headers',
    'has_cors_headers',
    'has_required_fields',
    'contains_validation_errors',
    'matches_performance_threshold',
    'is_valid_object_id',
    'is_valid_email',
    'is_valid_timestamp',

    # Builders
    'UserBuilder',
    'GameBuilder',
    'SessionBuilder',
    'APIRequestBuilder',
    'AuthTokenBuilder',
    'PreferencesBuilder',
    'AchievementBuilder',
    'TransactionBuilder',

    # Mocks
    'create_service_mock',
    'create_repository_mock',
    'create_api_client_mock',
    'mock_authentication',
    'mock_database',
    'mock_external_service',
    'create_flask_test_client',
    'mock_jwt_token',
    'mock_user_session',

    # Decorators
    'test_all_user_types',
    'test_all_games',
    'test_all_auth_scenarios',
    'test_with_permissions',
    'test_performance_scenarios',
    'parametrize_users',
    'parametrize_games',
    'parametrize_auth'
]