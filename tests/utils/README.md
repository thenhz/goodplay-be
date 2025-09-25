# GoodPlay Testing Utilities (GOO-35)

This package provides a comprehensive testing infrastructure for GoodPlay, designed to reduce test boilerplate by 80%+ through standardized patterns, intelligent fixtures, and domain-specific utilities.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Architecture Overview](#architecture-overview)
3. [Core Components](#core-components)
4. [Usage Examples](#usage-examples)
5. [Migration Guide](#migration-guide)
6. [Best Practices](#best-practices)
7. [API Reference](#api-reference)

## Quick Start

```python
# Import the complete testing toolkit
from tests.utils import (
    # Base classes
    BaseUnitTest, BaseServiceTest, BaseControllerTest, BaseIntegrationTest,

    # Builders for test data
    user, game, session, achievement,

    # Custom assertions
    assert_user_valid, assert_game_valid, assert_api_response_structure,

    # Matchers for complex validation
    UserSchemaMatcher, GameSchemaMatcher, SessionSchemaMatcher,

    # Mock utilities
    MockAuthenticatedUser, MockGameRepository, MockDatabase,

    # Parametrized decorators
    test_all_user_types, test_all_games, test_all_auth_scenarios
)

# Example: Zero-boilerplate unit test
class TestUserService(BaseUnitTest):
    component_class = UserService
    dependencies = ['user_repository']

    def test_create_user_success(self):
        # Test data built fluently
        user_data = user().as_regular().with_email('test@example.com').build()

        # Automatic mocking, no setup required
        self.mock_user_repository.create.return_value = user_data

        # Service call
        result = self.component.create_user(user_data)

        # Domain-specific assertions
        assert_user_valid(result)
        assert_api_response_structure(result, ['user_id', 'email'])
```

## Architecture Overview

The testing utilities package is built on four core principles:

### 1. Zero-Setup Philosophy
- **BaseUnitTest**: Automatic dependency injection and mocking
- **Smart Fixtures**: Context-aware test data generation
- **Auto-Discovery**: Component dependencies detected automatically

### 2. Domain-Driven Testing
- **Custom Assertions**: `assert_user_valid()`, `assert_game_valid()`
- **Business Logic Matchers**: Schema validation with business rules
- **Semantic Builders**: Fluent APIs that mirror domain concepts

### 3. Parametrized Excellence
- **@test_all_user_types**: Test variations across user roles
- **@test_all_games**: Coverage for different game types
- **@test_all_auth_scenarios**: Authentication state combinations

### 4. Enterprise Integration
- **GOO-34 Smart Fixtures**: Seamless integration with fixture system
- **Performance Monitoring**: Built-in timing and memory tracking
- **Thread-Safe Execution**: Safe for parallel test runs

## Core Components

### Base Test Classes

#### `BaseUnitTest`
Generic unit testing with zero setup boilerplate.

```python
class TestMyService(BaseUnitTest):
    component_class = MyService
    dependencies = ['repository', 'validator']
    external_dependencies = ['redis_client']

    def test_method(self):
        # Dependencies automatically mocked as self.mock_repository, etc.
        pass
```

#### `BaseServiceTest`
Service layer testing with business logic focus.

```python
class TestUserService(BaseServiceTest):
    service_class = UserService

    @test_all_user_types()
    def test_get_profile(self, user_type):
        # Automatically tests with admin, regular, premium users
        pass
```

#### `BaseControllerTest`
Controller testing with HTTP context and authentication.

```python
class TestUserController(BaseControllerTest):
    controller_module = 'app.core.controllers.user_controller'

    @test_all_auth_scenarios()
    def test_get_profile(self, auth_scenario):
        # Tests with valid, invalid, expired tokens
        pass
```

#### `BaseIntegrationTest`
Full-stack integration testing with database.

```python
class TestUserFlow(BaseIntegrationTest):
    def test_complete_registration_flow(self):
        # Full database and service stack available
        pass
```

### Fluent Data Builders

#### User Builder
```python
from tests.utils import user

# Basic user
basic_user = user().build()

# Complex user with fluent API
admin_user = (user()
    .as_admin()
    .with_name('John', 'Doe')
    .with_email('john@example.com')
    .with_preferences({'theme': 'dark'})
    .with_achievements(['first_game', 'high_scorer'])
    .verified()
    .with_timestamps()
    .build())

# Batch generation
users_batch = user().build_batch(10)
admin_batch = user().as_admin().build_batch(5)
```

#### Game Builder
```python
from tests.utils import game

# Basic game
puzzle_game = (game()
    .as_puzzle()
    .with_difficulty('medium')
    .with_credits_required(10)
    .published()
    .build())

# Performance-optimized game
fast_game = (game()
    .as_arcade()
    .with_max_duration(30)
    .free()
    .lightweight()
    .build())
```

#### Session Builder
```python
from tests.utils import session

# Active session
active_session = (session()
    .for_user(user_id)
    .for_game(game_id)
    .active()
    .with_score(1500)
    .with_duration(120)  # seconds
    .build())
```

### Custom Assertions

#### User Validation
```python
# Basic validation
assert_user_valid(user_data)

# With custom required fields
assert_user_valid(user_data, required_fields=['email', 'first_name', 'phone'])

# Business rule validation
assert_user_has_valid_preferences(user_data)
assert_user_achievement_structure(user_data)
```

#### API Response Validation
```python
# Standard API response structure
assert_api_response_structure(response)

# With custom expected keys
assert_api_response_structure(response, expected_keys=['user_id', 'token'])

# Service layer response pattern
assert_service_response_pattern((True, "Success", result))
```

#### Error Scenarios
```python
assert_validation_errors(response, expected_fields=['email', 'password'])
assert_permission_denied(response)
assert_not_found(response)
assert_unauthorized(response)
```

### Specialized Matchers

#### Schema Matchers
```python
from tests.utils import UserSchemaMatcher, GameSchemaMatcher

# Flexible user validation
matcher = UserSchemaMatcher().require_email().allow_optional('phone')
assert matcher.matches(user_data)

# Game schema with business rules
game_matcher = (GameSchemaMatcher()
    .require_category()
    .validate_credits_range(0, 1000)
    .require_valid_difficulty())
```

#### Collection Matchers
```python
# List validation
assert_list_contains_user(users, 'john@example.com')
assert_list_all_valid_users(users)
assert_list_sorted_by(games, 'created_at', reverse=True)

# Pagination validation
assert_pagination_valid(paginated_response)
```

### Mock Utilities

#### Authentication Mocking
```python
with MockAuthenticatedUser(role='admin') as user:
    # All auth decorators return this user
    response = client.get('/api/admin/users')

# Token-based mocking
mock_jwt_token = create_mock_jwt_token(user_id='123', role='user')
```

#### Database Mocking
```python
with MockDatabase() as mock_db:
    mock_db.users.find_one.return_value = user_data
    # Database calls intercepted

# Repository mocking
with MockGameRepository() as mock_repo:
    mock_repo.find_by_category.return_value = games_list
```

#### External Service Mocking
```python
with MockRedisClient() as redis:
    redis.get.return_value = cached_data

with MockEmailService() as email:
    email.send_verification.return_value = True
```

### Parametrized Decorators

#### User Type Testing
```python
@test_all_user_types()
def test_user_access(self, user_type):
    # Automatically runs for: admin, regular, premium, guest
    pass

@test_all_user_types(types=['admin', 'regular'])
def test_limited_access(self, user_type):
    # Only admin and regular users
    pass

@test_all_user_types(exclude=['guest'])
def test_authenticated_access(self, user_type):
    # All except guest users
    pass
```

#### Game Testing
```python
@test_all_games()
def test_game_compatibility(self, game_type):
    # Tests across: puzzle, arcade, strategy, casual
    pass

@test_all_games(difficulties=['easy', 'medium'])
def test_beginner_games(self, game_type, difficulty):
    # Game type + difficulty combinations
    pass
```

#### Authentication Scenarios
```python
@test_all_auth_scenarios()
def test_endpoint_security(self, auth_scenario):
    # Tests: valid_token, invalid_token, expired_token, no_token
    pass

@test_permission_levels(['read', 'write', 'admin'])
def test_permissions(self, permission):
    # Permission-based testing
    pass
```

## Usage Examples

### Before: Traditional Testing (High Boilerplate)

```python
class TestUserService(unittest.TestCase):
    def setUp(self):
        self.mock_user_repo = Mock()
        self.mock_validator = Mock()
        self.mock_logger = Mock()

        self.service = UserService(
            user_repository=self.mock_user_repo,
            validator=self.mock_validator,
            logger=self.mock_logger
        )

        self.user_data = {
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'SecurePass123!',
            'preferences': {
                'theme': 'light',
                'notifications': True
            }
        }

    def test_create_user_success(self):
        # Setup mocks
        self.mock_validator.validate_email.return_value = True
        self.mock_validator.validate_password.return_value = True
        self.mock_user_repo.find_by_email.return_value = None
        self.mock_user_repo.create.return_value = {
            **self.user_data,
            '_id': ObjectId(),
            'created_at': datetime.now()
        }

        # Execute
        result = self.service.create_user(self.user_data)

        # Verify
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 3)
        success, message, user = result
        self.assertTrue(success)
        self.assertEqual(message, "User created successfully")
        self.assertIsInstance(user, dict)
        self.assertIn('email', user)
        self.assertEqual(user['email'], 'test@example.com')
        self.assertIn('_id', user)
        self.assertIsInstance(user['_id'], ObjectId)

        # Verify mock calls
        self.mock_validator.validate_email.assert_called_once_with('test@example.com')
        self.mock_user_repo.find_by_email.assert_called_once_with('test@example.com')
        self.mock_user_repo.create.assert_called_once()
```

### After: GoodPlay Testing Utilities (Zero Boilerplate)

```python
class TestUserService(BaseUnitTest):
    component_class = UserService
    dependencies = ['user_repository', 'validator']

    def test_create_user_success(self):
        # Fluent test data
        user_data = user().with_email('test@example.com').build()

        # Auto-mocked dependencies
        self.mock_validator.validate_email.return_value = True
        self.mock_user_repository.create.return_value = user_data

        # Execute
        result = self.component.create_user(user_data)

        # Domain-specific assertions
        assert_service_response_pattern(result)
        success, message, created_user = result
        assert_user_valid(created_user)
```

**Boilerplate Reduction**: From 45 lines to 12 lines = **73% reduction**

### Controller Testing Example

#### Before
```python
class TestUserController(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

        self.mock_service = Mock()
        self.patcher = patch('app.core.controllers.user_controller.user_service', self.mock_service)
        self.patcher.start()

        self.valid_token = create_jwt_token({'user_id': 'test_id', 'role': 'user'})
        self.auth_headers = {'Authorization': f'Bearer {self.valid_token}'}

    def tearDown(self):
        self.patcher.stop()
        self.app_context.pop()

    def test_get_profile_success(self):
        # Setup
        user_data = {
            'user_id': 'test_id',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User'
        }
        self.mock_service.get_user_profile.return_value = (True, "Success", user_data)

        # Execute
        response = self.client.get('/api/users/profile', headers=self.auth_headers)

        # Verify
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIsInstance(data, dict)
        self.assertTrue(data.get('success'))
        self.assertIn('data', data)
        self.assertEqual(data['data']['email'], 'test@example.com')
```

#### After
```python
class TestUserController(BaseControllerTest):
    controller_module = 'app.core.controllers.user_controller'

    @test_all_auth_scenarios(valid_only=True)
    def test_get_profile_success(self, auth_scenario):
        # Auto-authenticated request context
        user_data = user().with_id(auth_scenario.user_id).build()
        self.mock_user_service.get_user_profile.return_value = (True, "Success", user_data)

        response = self.client.get('/api/users/profile')

        assert_api_response_structure(response.get_json())
        assert response.status_code == 200
```

**Boilerplate Reduction**: From 35 lines to 8 lines = **77% reduction**

## Migration Guide

### Step 1: Update Imports
```python
# Replace individual imports
from unittest.mock import Mock, patch
from tests.conftest import app, client

# With unified testing utilities
from tests.utils import BaseUnitTest, user, assert_user_valid
```

### Step 2: Convert Test Classes
```python
# Old pattern
class TestMyService(unittest.TestCase):
    def setUp(self):
        # Manual mock setup

# New pattern
class TestMyService(BaseUnitTest):
    component_class = MyService
    dependencies = ['repository']
```

### Step 3: Replace Data Creation
```python
# Old: Manual dictionary creation
user_data = {
    'email': 'test@example.com',
    'first_name': 'Test',
    'last_name': 'User',
    # ... 20+ lines of setup
}

# New: Fluent builders
user_data = user().with_email('test@example.com').build()
```

### Step 4: Use Domain Assertions
```python
# Old: Generic assertions
assert isinstance(result, dict)
assert 'email' in result
assert result['email'] == expected_email

# New: Domain-specific assertions
assert_user_valid(result)
```

## Best Practices

### 1. Test Organization
- **One concept per test class**: Focus on single component or feature
- **Descriptive test names**: `test_create_user_with_invalid_email_returns_error`
- **Group related tests**: Use nested classes for complex scenarios

### 2. Data Management
- **Use builders for complex data**: More maintainable than raw dictionaries
- **Leverage batch creation**: `user().build_batch(10)` for multiple instances
- **Customize minimally**: Only specify values relevant to test

### 3. Mock Strategy
- **Mock at service boundaries**: Don't mock internal implementation details
- **Use context managers**: Automatic cleanup and thread safety
- **Verify behavior, not implementation**: Focus on what, not how

### 4. Assertion Strategy
- **Use domain assertions**: More descriptive failures
- **Assert one concept**: Single responsibility per assertion
- **Provide context**: Custom messages for complex scenarios

### 5. Performance Considerations
- **Batch operations**: Use `build_batch()` for multiple instances
- **Lazy evaluation**: Builders only create data when `.build()` called
- **Resource cleanup**: Base classes handle automatic cleanup

## API Reference

### Base Classes

#### `BaseUnitTest`
```python
class BaseUnitTest(TestBase):
    component_class: Optional[Type] = None
    dependencies: List[str] = []
    external_dependencies: List[str] = []
    auto_patch_imports: bool = True

    def setUp(self):
        # Automatic setup

    def tearDown(self):
        # Automatic cleanup
```

#### `BaseServiceTest`
```python
class BaseServiceTest(BaseUnitTest):
    service_class: Optional[Type] = None

    # Additional service-specific utilities
```

#### `BaseControllerTest`
```python
class BaseControllerTest(TestBase):
    controller_module: str

    @property
    def client(self) -> FlaskClient:
        # Test client with auth context

    def authenticated_request(self, method: str, url: str, **kwargs):
        # Pre-authenticated requests
```

#### `BaseIntegrationTest`
```python
class BaseIntegrationTest(TestBase):
    use_real_database: bool = False

    # Full application stack for integration testing
```

### Fluent Builders

#### User Builder
```python
def user() -> UserBuilder:
    """Create a fluent user builder"""

class UserBuilder:
    def as_admin(self) -> 'UserBuilder'
    def as_regular(self) -> 'UserBuilder'
    def as_premium(self) -> 'UserBuilder'
    def with_email(self, email: str) -> 'UserBuilder'
    def with_name(self, first: str, last: str) -> 'UserBuilder'
    def with_preferences(self, prefs: Dict) -> 'UserBuilder'
    def verified(self) -> 'UserBuilder'
    def with_achievements(self, achievements: List[str]) -> 'UserBuilder'
    def with_timestamps(self) -> 'UserBuilder'
    def build(self) -> Dict[str, Any]
    def build_batch(self, count: int) -> List[Dict[str, Any]]
```

#### Game Builder
```python
def game() -> GameBuilder:
    """Create a fluent game builder"""

class GameBuilder:
    def as_puzzle(self) -> 'GameBuilder'
    def as_arcade(self) -> 'GameBuilder'
    def as_strategy(self) -> 'GameBuilder'
    def with_difficulty(self, difficulty: str) -> 'GameBuilder'
    def with_credits_required(self, credits: int) -> 'GameBuilder'
    def free(self) -> 'GameBuilder'
    def published(self) -> 'GameBuilder'
    def lightweight(self) -> 'GameBuilder'
    def build(self) -> Dict[str, Any]
    def build_batch(self, count: int) -> List[Dict[str, Any]]
```

### Custom Assertions

#### User Assertions
```python
def assert_user_valid(user: Dict[str, Any], required_fields: List[str] = None)
def assert_user_has_valid_preferences(user: Dict[str, Any])
def assert_user_achievement_structure(user: Dict[str, Any])
```

#### API Assertions
```python
def assert_api_response_structure(response: Dict[str, Any], expected_keys: List[str] = None)
def assert_service_response_pattern(response: tuple)
def assert_validation_errors(response: Dict[str, Any], expected_fields: List[str] = None)
def assert_permission_denied(response: Dict[str, Any])
def assert_not_found(response: Dict[str, Any])
def assert_unauthorized(response: Dict[str, Any])
```

#### Performance Assertions
```python
def assert_performance_within_threshold(actual_ms: float, max_threshold_ms: float, operation_name: str = "Operation")
def assert_database_state_clean(collections_to_check: List[str] = None)
```

### Parametrized Decorators

#### User Type Testing
```python
def test_all_user_types(types: List[str] = None, exclude: List[str] = None)
def test_authenticated_users_only(exclude_guest: bool = True)
def test_admin_users_only()
```

#### Game Testing
```python
def test_all_games(categories: List[str] = None, difficulties: List[str] = None)
def test_free_games_only()
def test_premium_games_only()
```

#### Authentication Testing
```python
def test_all_auth_scenarios(valid_only: bool = False)
def test_permission_levels(permissions: List[str])
def test_token_scenarios(scenarios: List[str] = None)
```

### Mock Utilities

#### Authentication Mocks
```python
class MockAuthenticatedUser:
    def __init__(self, user_id: str = None, role: str = 'user', **user_attrs)
    def __enter__(self) -> Dict[str, Any]
    def __exit__(self, exc_type, exc_val, exc_tb)

def create_mock_jwt_token(user_id: str, role: str = 'user', **claims) -> str
```

#### Database Mocks
```python
class MockDatabase:
    def __enter__(self) -> Mock
    def __exit__(self, exc_type, exc_val, exc_tb)

class MockGameRepository:
    def __enter__(self) -> Mock
    def __exit__(self, exc_type, exc_val, exc_tb)
```

#### External Service Mocks
```python
class MockRedisClient:
    def __enter__(self) -> Mock
    def __exit__(self, exc_type, exc_val, exc_tb)

class MockEmailService:
    def __enter__(self) -> Mock
    def __exit__(self, exc_type, exc_val, exc_tb)
```

---

This testing utilities package transforms GoodPlay test development from verbose, repetitive code to expressive, maintainable tests that focus on business logic rather than setup boilerplate.

For questions or contributions, refer to the main GoodPlay development documentation.