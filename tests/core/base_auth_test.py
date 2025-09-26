"""
BaseAuthTest - Specialized Base Class for Authentication Testing (GOO-35)

Provides specialized testing capabilities for authentication-related functionality
with automatic setup for auth services, JWT handling, and user management.
"""
from typing import Dict, Any, Optional, List
from unittest.mock import MagicMock, patch
from tests.core.base_service_test import BaseServiceTest


class BaseAuthTest(BaseServiceTest):
    """
    Specialized base test class for authentication functionality.

    Features:
    - Automatic auth service dependency injection
    - JWT token management and mocking
    - User authentication flows
    - Password hashing utilities
    - Session management
    - Permission testing utilities
    """

    # Default dependencies for auth tests
    repository_dependencies = [
        'user_repository',
    ]

    external_dependencies = [
        'auth_service',
        'jwt_manager',
        'password_hasher'
    ]

    def setUp(self):
        """Enhanced setup for authentication testing"""
        super().setUp()
        self._setup_auth_mocks()
        self._setup_jwt_mocks()
        self._setup_user_mocks()

    def _setup_auth_mocks(self):
        """Setup authentication-related mocks"""
        # Mock bcrypt operations
        self.bcrypt_check_patcher = patch('bcrypt.checkpw')
        self.bcrypt_hash_patcher = patch('bcrypt.hashpw')
        self.bcrypt_gensalt_patcher = patch('bcrypt.gensalt')

        self.mock_bcrypt_check = self.bcrypt_check_patcher.start()
        self.mock_bcrypt_hash = self.bcrypt_hash_patcher.start()
        self.mock_bcrypt_gensalt = self.bcrypt_gensalt_patcher.start()

        # Default bcrypt behavior
        self.mock_bcrypt_check.return_value = True
        self.mock_bcrypt_hash.return_value = b'hashed_password'
        self.mock_bcrypt_gensalt.return_value = b'salt'

        self.addCleanup(self.bcrypt_check_patcher.stop)
        self.addCleanup(self.bcrypt_hash_patcher.stop)
        self.addCleanup(self.bcrypt_gensalt_patcher.stop)

    def _setup_jwt_mocks(self):
        """Setup JWT-related mocks"""
        # Mock JWT token creation
        self.jwt_access_patcher = patch('flask_jwt_extended.create_access_token')
        self.jwt_refresh_patcher = patch('flask_jwt_extended.create_refresh_token')
        self.jwt_get_identity_patcher = patch('flask_jwt_extended.get_jwt_identity')

        self.mock_jwt_access = self.jwt_access_patcher.start()
        self.mock_jwt_refresh = self.jwt_refresh_patcher.start()
        self.mock_jwt_identity = self.jwt_get_identity_patcher.start()

        # Default JWT behavior
        self.mock_jwt_access.return_value = 'test_access_token'
        self.mock_jwt_refresh.return_value = 'test_refresh_token'
        self.mock_jwt_identity.return_value = 'test_user_id'

        self.addCleanup(self.jwt_access_patcher.stop)
        self.addCleanup(self.jwt_refresh_patcher.stop)
        self.addCleanup(self.jwt_get_identity_patcher.stop)

    def _setup_user_mocks(self):
        """Setup user-related mocks with common auth scenarios"""
        # Get the user repository mock from repository_mocks dict
        if hasattr(self, 'repository_mocks') and 'user_repository' in self.repository_mocks:
            self.mock_user_repository = self.repository_mocks['user_repository']
        else:
            # Fallback: create the mock directly
            from unittest.mock import MagicMock
            self.mock_user_repository = MagicMock()

        # Setup common user repository responses
        self.mock_user_repository.find_by_email.return_value = None
        self.mock_user_repository.find_by_id.return_value = None
        self.mock_user_repository.create_user.return_value = 'test_user_id'
        self.mock_user_repository.update_last_login.return_value = True

    # Auth-specific utility methods

    def create_test_user(self, role: str = 'user', verified: bool = True, **kwargs) -> Dict[str, Any]:
        """Create test user data with auth-specific defaults"""
        from tests.utils import user

        return (user()
                .as_type(role)
                .with_field('is_verified', verified)
                .with_field('is_active', True)
                .merge(kwargs)
                .build())

    def create_auth_headers(self, token: str = None) -> Dict[str, str]:
        """Create authentication headers for API requests"""
        token = token or 'test_access_token'
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

    def mock_successful_login(self, user_data: Dict[str, Any] = None):
        """Mock a successful user login scenario"""
        if user_data is None:
            user_data = self.create_test_user()

        self.mock_user_repository.find_by_email.return_value = user_data
        self.mock_bcrypt_check.return_value = True
        self.mock_jwt_access.return_value = f"access_token_for_{user_data.get('email', 'test')}"
        self.mock_jwt_refresh.return_value = f"refresh_token_for_{user_data.get('email', 'test')}"

        return user_data

    def mock_failed_login(self, failure_type: str = 'wrong_password'):
        """Mock failed login scenarios"""
        failure_scenarios = {
            'wrong_password': lambda: self.mock_bcrypt_check.__setattr__('return_value', False),
            'user_not_found': lambda: self.mock_user_repository.find_by_email.__setattr__('return_value', None),
            'user_not_verified': lambda: self.mock_user_repository.find_by_email.__setattr__(
                'return_value', self.create_test_user(verified=False)
            ),
            'user_inactive': lambda: self.mock_user_repository.find_by_email.__setattr__(
                'return_value', self.create_test_user(is_active=False)
            )
        }

        scenario_func = failure_scenarios.get(failure_type)
        if scenario_func:
            scenario_func()
        else:
            raise ValueError(f"Unknown failure type: {failure_type}")

    def assert_user_valid(self, user_data: Dict[str, Any], expected_role: str = 'user'):
        """Assert user data is valid with expected properties"""
        assert user_data is not None, "User data should not be None"
        assert '_id' in user_data, "User should have an ID"
        assert 'email' in user_data, "User should have an email"
        assert 'role' in user_data, "User should have a role"
        assert user_data['role'] == expected_role, f"Expected role {expected_role}, got {user_data['role']}"
        assert 'is_active' in user_data, "User should have is_active field"
        assert 'created_at' in user_data, "User should have created_at field"

    def create_test_auth_data(self, email: str = "test@example.com", verified: bool = True, **kwargs) -> Dict[str, Any]:
        """Create authentication-specific test data"""
        auth_data = self.create_test_user(email=email, verified=verified, **kwargs)
        auth_data.update({
            'password_hash': 'hashed_password_example',
            'is_verified': verified
        })
        return auth_data

    def create_verified_user_scenario(self) -> Dict[str, Any]:
        """Create a verified user test scenario"""
        user = self.create_test_user(verified=True, is_active=True)
        return {
            'user': user,
            'scenario_type': 'verified_user',
            'expected_auth': True
        }

    def create_test_user_with_preferences(self, **kwargs) -> Dict[str, Any]:
        """Create test user with preferences structure"""
        user = self.create_test_user(**kwargs)
        user['preferences'] = {
            'gaming': {
                'difficulty_level': 'medium',
                'tutorial_enabled': True,
                'preferred_categories': ['puzzle', 'strategy'],
                'sound_enabled': True,
                'music_enabled': True
            },
            'notifications': {
                'push_enabled': True,
                'email_enabled': False,
                'frequency': 'daily',
                'achievement_alerts': True
            },
            'privacy': {
                'profile_visibility': 'public',
                'stats_sharing': True,
                'activity_visibility': 'friends'
            },
            'donations': {
                'auto_donate_enabled': False,
                'auto_donate_percentage': 0.0,
                'preferred_causes': ['education', 'health']
            },
            'accessibility': {
                'high_contrast': False,
                'large_text': False,
                'screen_reader': False
            },
            'meta': {
                'version': '1.0',
                'last_updated': user.get('updated_at')
            }
        }
        return user

    def create_custom_gaming_preferences(self, difficulty_level: str = "medium", tutorial_enabled: bool = True, sound_enabled: bool = True) -> Dict[str, Any]:
        """Create user with custom gaming preferences"""
        user = self.create_test_user()
        user['preferences'] = {
            'gaming': {
                'difficulty_level': difficulty_level,
                'tutorial_enabled': tutorial_enabled,
                'preferred_categories': ['puzzle', 'strategy', 'action'],
                'sound_enabled': sound_enabled,
                'music_enabled': True
            },
            'notifications': {},
            'privacy': {},
            'donations': {},
            'accessibility': {},
            'meta': {'version': '1.0'}
        }
        return user

    def create_custom_notification_preferences(self, push_enabled: bool = True, email_enabled: bool = False, frequency: str = "daily") -> Dict[str, Any]:
        """Create user with custom notification preferences"""
        user = self.create_test_user()
        user['preferences'] = {
            'gaming': {},
            'notifications': {
                'push_enabled': push_enabled,
                'email_enabled': email_enabled,
                'frequency': frequency,
                'achievement_alerts': True
            },
            'privacy': {},
            'donations': {},
            'accessibility': {},
            'meta': {'version': '1.0'}
        }
        return user

    def create_privacy_preferences(self, privacy_level: str = 'medium') -> Dict[str, Any]:
        """Create user with privacy preferences"""
        privacy_settings = {
            'low': {'profile_visibility': 'public', 'stats_sharing': True, 'activity_visibility': 'public'},
            'medium': {'profile_visibility': 'friends', 'stats_sharing': True, 'activity_visibility': 'friends'},
            'high': {'profile_visibility': 'private', 'stats_sharing': False, 'activity_visibility': 'private'}
        }

        user = self.create_test_user()
        user['preferences'] = {
            'gaming': {},
            'notifications': {},
            'privacy': privacy_settings.get(privacy_level, privacy_settings['medium']),
            'donations': {},
            'accessibility': {},
            'meta': {'version': '1.0'}
        }
        return user

    def assert_auth_response_success(self, response_tuple, expected_tokens: bool = False):
        """Assert that an auth service response indicates success"""
        success, message, result = response_tuple
        assert success is True, f"Expected success, but got failure: {message}"
        assert message is not None, "Message should not be None"
        assert result is not None, "Result should not be None for successful auth"

        if expected_tokens:
            assert 'tokens' in result or 'access_token' in result, "Expected tokens in successful auth response"

    def mock_registration_scenario(self, scenario: str = 'success'):
        """Mock user registration scenarios"""
        if scenario == 'success':
            self.mock_user_repository.email_exists.return_value = False
            self.mock_user_repository.create_user.return_value = 'new_user_id'
        elif scenario == 'email_exists':
            self.mock_user_repository.email_exists.return_value = True
        elif scenario == 'creation_failed':
            self.mock_user_repository.email_exists.return_value = False
            self.mock_user_repository.create_user.side_effect = Exception("Database error")

    def assert_auth_response_success(self, response: tuple, expected_tokens: bool = True):
        """Assert successful authentication response pattern"""
        from tests.utils import assert_service_response_pattern

        assert_service_response_pattern(response)
        success, message, data = response

        assert success, f"Expected successful auth response, got: {message}"

        if expected_tokens and data:
            # Check if tokens are directly in data or nested in tokens object
            if 'tokens' in data:
                tokens = data['tokens']
                assert 'access_token' in tokens, "Expected access_token in successful auth response"
                assert 'refresh_token' in tokens, "Expected refresh_token in successful auth response"
            else:
                assert 'access_token' in data, "Expected access_token in successful auth response"
                assert 'refresh_token' in data, "Expected refresh_token in successful auth response"

            assert 'user' in data, "Expected user data in successful auth response"

    def assert_auth_response_failure(self, response: tuple, expected_message: str = None):
        """Assert failed authentication response pattern"""
        from tests.utils import assert_service_response_pattern

        assert_service_response_pattern(response)
        success, message, data = response

        assert not success, f"Expected failed auth response, got success with: {data}"

        if expected_message:
            assert expected_message.lower() in message.lower(), \
                f"Expected message containing '{expected_message}', got: {message}"

        assert data is None, f"Expected no data in failed auth response, got: {data}"

    def create_jwt_token_data(self, user_id: str, role: str = 'user', **claims) -> Dict[str, Any]:
        """Create JWT token payload data for testing"""
        token_data = {
            'user_id': user_id,
            'role': role,
            'iat': 1640995200,  # Fixed timestamp for testing
            'exp': 1640999200,  # 1 hour later
            **claims
        }
        return token_data

    def mock_jwt_decode(self, token_data: Dict[str, Any]):
        """Mock JWT token decoding with specific data"""
        with patch('jwt.decode') as mock_decode:
            mock_decode.return_value = token_data
            yield mock_decode

    # Permission testing utilities

    def assert_permission_required(self, test_func, required_permission: str):
        """Assert that a function requires specific permission"""
        # Mock user without required permission
        user_without_permission = self.create_test_user(role='user')
        user_without_permission['permissions'] = []

        self.mock_user_repository.find_by_id.return_value = user_without_permission

        result = test_func()
        self.assert_auth_response_failure(result, 'permission')

    def assert_role_required(self, test_func, required_role: str):
        """Assert that a function requires specific role"""
        # Mock user with insufficient role
        user_with_wrong_role = self.create_test_user(role='user')
        if required_role != 'user':
            self.mock_user_repository.find_by_id.return_value = user_with_wrong_role

            result = test_func()
            self.assert_auth_response_failure(result, 'permission')

    # Batch testing utilities

    def run_auth_scenarios(self, test_func, scenarios: List[str]):
        """Test multiple authentication scenarios"""
        results = {}

        for scenario in scenarios:
            # Reset mocks
            self._setup_auth_mocks()
            self._setup_user_mocks()

            # Configure scenario
            if scenario == 'success':
                self.mock_successful_login()
            elif scenario.startswith('fail_'):
                failure_type = scenario.replace('fail_', '')
                self.mock_failed_login(failure_type)

            # Execute test
            results[scenario] = test_func()

        return results

    def tearDown(self):
        """Clean up auth-specific mocks"""
        super().tearDown()


# Convenience functions for quick auth test creation

def auth_test(service_class=None, **kwargs):
    """Decorator to create auth test class with specific service"""
    def decorator(cls):
        # Set service class if provided
        if service_class:
            cls.service_class = service_class

        # Merge additional dependencies
        if 'dependencies' in kwargs:
            cls.dependencies = BaseAuthTest.default_dependencies + kwargs['dependencies']

        return cls

    return decorator


# Usage Examples:
"""
# Basic authentication service test
class TestAuthService(BaseAuthTest):
    service_class = AuthService

    def test_login_success(self):
        user_data = self.create_test_user()
        self.mock_successful_login(user_data)

        result = self.service.login(user_data['email'], 'password')
        self.assert_auth_response_success(result)

    def test_login_wrong_password(self):
        self.mock_failed_login('wrong_password')

        result = self.service.login('user@example.com', 'wrong_password')
        self.assert_auth_response_failure(result, 'Invalid credentials')

# Using decorator for custom auth service
@auth_test(service_class=CustomAuthService, dependencies=['oauth_service'])
class TestCustomAuth(BaseAuthTest):
    def test_oauth_login(self):
        # Test OAuth-specific functionality
        pass

# Multiple scenario testing
class TestAuthScenarios(BaseAuthTest):
    service_class = AuthService

    def test_all_login_scenarios(self):
        def login_test():
            return self.service.login('test@example.com', 'password')

        results = self.test_auth_scenarios(login_test, [
            'success',
            'fail_wrong_password',
            'fail_user_not_found',
            'fail_user_not_verified'
        ])

        # Assert results for each scenario
        assert results['success'][0] is True
        assert results['fail_wrong_password'][0] is False
"""