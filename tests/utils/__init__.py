"""
GoodPlay Testing Utilities Package (GOO-35)

Complete testing utilities package with assertions, matchers, builders,
mocks, and parametrized test decorators for standardized testing patterns.

Integrated Systems:
- GOO-34 Smart Fixtures: Intelligent fixture management and caching
- GOO-33 Factory-Boy: Scalable test data generation
- GOO-30-32 TestConfig: Enterprise test configuration

Usage Examples:

    # Zero-setup unit testing
    class TestUserService(BaseUnitTest):
        component_class = UserService
        dependencies = ['user_repository']

        def test_create_user(self):
            user_data = user().build()
            assert_user_valid(result)

    # Smart Fixtures integration
    @smart_fixture_integration
    class TestWithSmartFixtures(BaseServiceTest):
        def test_with_cached_data(self):
            # Automatic Smart Fixtures integration
            pass
"""

# Core utilities
from .assertions import *
from .matchers import *
from .builders import *
from .mocks import *
from .decorators import *

# Smart Fixtures Integration
try:
    from ..fixtures import (
        smart_fixture,
        factory_fixture,
        preset_fixture,
        smart_fixture_manager,
        preset_manager
    )

    # Create integrated smart fixture builders
    def smart_fixture_user(user_type='regular', **kwargs):
        """Create smart fixture for user with specified type"""
        @smart_fixture(f'user_{user_type}')
        def _user_fixture():
            return user().as_type(user_type).build(**kwargs)
        return _user_fixture

    def smart_fixture_game(category='puzzle', **kwargs):
        """Create smart fixture for game with specified category"""
        @smart_fixture(f'game_{category}')
        def _game_fixture():
            return game().as_category(category).build(**kwargs)
        return _game_fixture

    def smart_fixture_session(status='active', **kwargs):
        """Create smart fixture for session with specified status"""
        @smart_fixture(f'session_{status}')
        def _session_fixture():
            return session().with_status(status).build(**kwargs)
        return _session_fixture

    # Integration utilities
    def register_builder_fixtures():
        """Register GOO-35 builders as Smart Fixtures"""
        # Register builders with smart fixture manager (if method exists)
        if hasattr(smart_fixture_manager, 'register_builder'):
            smart_fixture_manager.register_builder('user', user)
            smart_fixture_manager.register_builder('game', game)
            smart_fixture_manager.register_builder('session', session)
            smart_fixture_manager.register_builder('achievement', achievement)
        else:
            # Alternative: store builders in manager's context for future use
            if not hasattr(smart_fixture_manager, '_goo35_builders'):
                smart_fixture_manager._goo35_builders = {}
            smart_fixture_manager._goo35_builders.update({
                'user': user,
                'game': game,
                'session': session,
                'achievement': achievement
            })

        # Create preset combinations using builders
        preset_manager.register_preset('goo35_user_setup', lambda: {
            'user': user().build(),
            'preferences': user().with_preferences({}).build()
        })

        preset_manager.register_preset('goo35_gaming_setup', lambda: {
            'user': user().build(),
            'game': game().build(),
            'session': session().build()
        })

    # Auto-register when imported
    register_builder_fixtures()

    SMART_FIXTURES_AVAILABLE = True
    print("✅ GOO-35 Testing Utilities integrated with Smart Fixtures (GOO-34)")

except ImportError as e:
    SMART_FIXTURES_AVAILABLE = False
    print(f"⚠️  Smart Fixtures integration not available: {e}")

    # Provide fallback functions
    def smart_fixture_user(*args, **kwargs):
        return lambda: user().build()
    def smart_fixture_game(*args, **kwargs):
        return lambda: game().build()
    def smart_fixture_session(*args, **kwargs):
        return lambda: session().build()
    def register_builder_fixtures():
        pass

# Import base test classes
try:
    from ..core.base_unit_test import BaseUnitTest
    from ..core.base_service_test import BaseServiceTest
    from ..core.base_controller_test import BaseControllerTest
    from ..core.base_integration_test import BaseIntegrationTest
    BASE_CLASSES_AVAILABLE = True
except ImportError:
    # Create placeholder classes if not available
    class BaseUnitTest: pass
    class BaseServiceTest: pass
    class BaseControllerTest: pass
    class BaseIntegrationTest: pass
    BASE_CLASSES_AVAILABLE = False

# Package metadata
__version__ = '1.0.0'
__author__ = 'GoodPlay Team'
__description__ = 'Complete testing utilities package for GoodPlay with Smart Fixtures integration'

__all__ = [
    # Base Test Classes
    'BaseUnitTest',
    'BaseServiceTest',
    'BaseControllerTest',
    'BaseIntegrationTest',

    # Fluent Builders (function-style)
    'user',
    'game',
    'session',
    'achievement',

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
    'UserSchemaMatcher',
    'GameSchemaMatcher',
    'SessionSchemaMatcher',
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

    # Builder Classes
    'UserBuilder',
    'GameBuilder',
    'SessionBuilder',
    'APIRequestBuilder',
    'AuthTokenBuilder',
    'PreferencesBuilder',
    'AchievementBuilder',
    'TransactionBuilder',

    # Mock Utilities
    'MockDatabase',
    'MockPasswordCheck',
    'create_service_mock',
    'create_repository_mock',
    'create_api_client_mock',
    'mock_authentication',
    'mock_database',
    'mock_external_service',
    'create_flask_test_client',
    'mock_jwt_token',
    'mock_user_session',

    # Parametrized Test Decorators
    'test_all_user_types',
    'test_all_games',
    'test_all_auth_scenarios',
    'test_with_permissions',
    'test_performance_scenarios',
    'parametrize_users',
    'parametrize_games',
    'parametrize_auth',

    # Smart Fixtures Integration (if available)
    'smart_fixture_user',
    'smart_fixture_game',
    'smart_fixture_session',
    'register_builder_fixtures',
    'SMART_FIXTURES_AVAILABLE',
    'BASE_CLASSES_AVAILABLE'
]