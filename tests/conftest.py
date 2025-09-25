"""
Pytest configuration and shared fixtures for GoodPlay test suite

Enhanced configuration with GOO-35 Testing Utilities integration and
enterprise-grade testing infrastructure.
"""
import pytest
import sys
import os
import random
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from typing import Dict, Any, Optional, Type

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import TestConfig before setting environment
from tests.core.config import TestConfig, get_test_config

# Initialize test configuration
test_config = get_test_config()

# Import core GOO-35 Testing Utilities
try:
    from tests.utils import (
        # Fluent builders
        user, game, session, achievement,
        # Custom assertions
        assert_user_valid, assert_service_response_pattern,
    )
except ImportError as e:
    # Fallback if some imports not available yet
    print(f"⚠️ Some GOO-35 utilities not available: {e}")
    user = game = session = achievement = None
    assert_user_valid = assert_service_response_pattern = None

# Set testing environment (now handled by TestConfig, but kept for compatibility)
os.environ['TESTING'] = 'true'

# Mock database operations before importing app modules (enhanced with TestConfig)
with patch('pymongo.collection.Collection.create_index'), \
     patch('app.core.repositories.base_repository.get_db') as mock_get_db:
    # Use TestConfig to create consistent mock database
    mock_db = test_config.create_mock_db()
    mock_get_db.return_value = mock_db

    from app import create_app
    from app.core.models.user import User


@pytest.fixture(scope="session")
def app():
    """Create application for testing with TestConfig integration"""
    # Create app with TestConfig
    app = create_app()
    app.config.update(test_config.get_flask_config())
    return app


@pytest.fixture(scope="session")
def test_config_instance():
    """Provide access to test configuration"""
    return test_config


@pytest.fixture(scope="session")
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def auth_headers():
    """Mock authentication headers"""
    return {
        'Authorization': 'Bearer test-token',
        'Content-Type': 'application/json'
    }


@pytest.fixture
def sample_user():
    """Sample user for testing"""
    return User(
        email="test@goodplay.com",
        first_name="Test",
        last_name="User"
    )


@pytest.fixture
def sample_user_data():
    """Sample user data dictionary"""
    return {
        "email": "test@goodplay.com",
        "password": "password123",
        "first_name": "Test",
        "last_name": "User"
    }


@pytest.fixture
def sample_preferences():
    """Sample user preferences data"""
    return {
        "gaming": {
            "preferred_categories": ["puzzle", "strategy"],
            "difficulty_level": "medium",
            "tutorial_enabled": True,
            "auto_save": True,
            "sound_enabled": True,
            "music_enabled": False,
            "vibration_enabled": True
        },
        "notifications": {
            "push_enabled": True,
            "email_enabled": False,
            "frequency": "weekly",
            "achievement_alerts": True,
            "donation_confirmations": True,
            "friend_activity": False,
            "tournament_reminders": True,
            "maintenance_alerts": True
        },
        "privacy": {
            "profile_visibility": "friends",
            "stats_sharing": False,
            "friends_discovery": True,
            "leaderboard_participation": True,
            "activity_visibility": "private",
            "contact_permissions": "friends"
        },
        "donations": {
            "auto_donate_enabled": False,
            "auto_donate_percentage": 10.0,
            "preferred_causes": ["education", "environment"],
            "notification_threshold": 50.0,
            "monthly_goal": 100.0,
            "impact_sharing": True
        }
    }


@pytest.fixture
def mock_db():
    """Mock database connection"""
    with patch('app.core.repositories.base_repository.get_db') as mock:
        mock_collection = MagicMock()
        mock_db_instance = MagicMock()
        mock_db_instance.__getitem__ = MagicMock(return_value=mock_collection)
        mock.return_value = mock_db_instance
        yield mock_collection


@pytest.fixture
def mock_jwt():
    """Mock JWT token creation"""
    with patch('flask_jwt_extended.create_access_token') as mock_access, \
         patch('flask_jwt_extended.create_refresh_token') as mock_refresh:
        mock_access.return_value = 'test-access-token'
        mock_refresh.return_value = 'test-refresh-token'
        yield (mock_access, mock_refresh)


@pytest.fixture
def mock_bcrypt():
    """Mock bcrypt password hashing"""
    with patch('bcrypt.checkpw') as mock_check, \
         patch('bcrypt.hashpw') as mock_hash, \
         patch('bcrypt.gensalt') as mock_salt:
        mock_check.return_value = True
        mock_hash.return_value = b'hashed_password'
        mock_salt.return_value = b'salt'
        yield (mock_check, mock_hash, mock_salt)


# Enhanced fixtures with TestConfig integration

@pytest.fixture
def test_utils():
    """Test utilities instance with test config"""
    from tests.core.utils import TestUtils
    return TestUtils(test_config)


# Factory-Boy Integration and Registration

# Register all Factory-Boy factories with pytest-factoryboy
def pytest_configure(config):
    """Configure pytest with Factory-Boy integration"""
    # Import and register all factories for pytest-factoryboy
    try:
        import pytest_factoryboy

        # Import all our Factory-Boy factories
        from tests.factories.user_factory import UserFactory, UserPreferencesFactory
        from tests.factories.game_factory import GameFactory, GameSessionFactory
        from tests.factories.social_factory import (
            AchievementFactory, BadgeFactory, UserAchievementFactory,
            UserRelationshipFactory, LeaderboardFactory, LeaderboardEntryFactory,
            ImpactScoreFactory
        )
        from tests.factories.financial_factory import (
            WalletFactory, TransactionFactory, DonationFactory
        )
        from tests.factories.onlus_factory import (
            ONLUSFactory, CampaignFactory, ProjectFactory, VolunteerFactory
        )

        # Register factories with pytest-factoryboy
        # This makes them available as fixtures automatically
        pytest_factoryboy.register(UserFactory)
        pytest_factoryboy.register(UserPreferencesFactory)
        pytest_factoryboy.register(GameFactory)
        pytest_factoryboy.register(GameSessionFactory)
        pytest_factoryboy.register(AchievementFactory)
        pytest_factoryboy.register(BadgeFactory)
        pytest_factoryboy.register(UserAchievementFactory)
        pytest_factoryboy.register(UserRelationshipFactory)
        pytest_factoryboy.register(LeaderboardFactory)
        pytest_factoryboy.register(LeaderboardEntryFactory)
        pytest_factoryboy.register(ImpactScoreFactory)
        pytest_factoryboy.register(WalletFactory)
        pytest_factoryboy.register(TransactionFactory)
        pytest_factoryboy.register(DonationFactory)
        pytest_factoryboy.register(ONLUSFactory)
        pytest_factoryboy.register(CampaignFactory)
        pytest_factoryboy.register(ProjectFactory)
        pytest_factoryboy.register(VolunteerFactory)

    except ImportError:
        # pytest-factoryboy not installed, skip registration
        pass


# Direct factory fixtures for manual usage
@pytest.fixture
def user_factory():
    """Factory-Boy UserFactory fixture"""
    from tests.factories.user_factory import UserFactory
    return UserFactory

@pytest.fixture
def game_factory():
    """Factory-Boy GameFactory fixture"""
    from tests.factories.game_factory import GameFactory
    return GameFactory

@pytest.fixture
def game_session_factory():
    """Factory-Boy GameSessionFactory fixture"""
    from tests.factories.game_factory import GameSessionFactory
    return GameSessionFactory

@pytest.fixture
def achievement_factory():
    """Factory-Boy AchievementFactory fixture"""
    from tests.factories.social_factory import AchievementFactory
    return AchievementFactory

@pytest.fixture
def wallet_factory():
    """Factory-Boy WalletFactory fixture"""
    from tests.factories.financial_factory import WalletFactory
    return WalletFactory

@pytest.fixture
def onlus_factory():
    """Factory-Boy ONLUSFactory fixture"""
    from tests.factories.onlus_factory import ONLUSFactory
    return ONLUSFactory


# Legacy compatibility fixtures (for backward compatibility with existing tests)
@pytest.fixture
def user_factory_legacy(test_utils):
    """Legacy user factory for backward compatibility"""
    from tests.factories.user_factory import LegacyUserFactory
    return LegacyUserFactory(test_utils)


@pytest.fixture
def game_factory_legacy(test_utils):
    """Legacy game factory for backward compatibility"""
    from tests.factories.game_factory import LegacyGameFactory, LegacyGameSessionFactory
    return {
        'game': LegacyGameFactory(test_utils),
        'session': LegacyGameSessionFactory(test_utils)
    }


# Factory utility fixtures
@pytest.fixture
def factory_utils():
    """Utility functions for working with factories"""
    from tests.factories.base import BatchFactoryMixin, FactoryConfig

    class FactoryUtils:
        @staticmethod
        def create_test_ecosystem(count: int = 50):
            """Create a complete test ecosystem with all types of objects"""
            from tests.factories.user_factory import UserFactory
            from tests.factories.game_factory import GameFactory, GameSessionFactory
            from tests.factories.social_factory import AchievementFactory
            from tests.factories.financial_factory import WalletFactory
            from tests.factories.onlus_factory import ONLUSFactory

            ecosystem = {
                'users': UserFactory.create_diverse_group(count // 5),
                'games': GameFactory.create_game_collection(count // 10),
                'achievements': AchievementFactory.create_complete_achievement_system(),
                'onlus_orgs': ONLUSFactory.create_org_ecosystem(count // 20)
            }

            # Create sessions for users and games
            ecosystem['sessions'] = []
            for user in ecosystem['users'][:10]:  # Sessions for first 10 users
                user_sessions = GameSessionFactory.create_user_sessions(
                    user['_id'], count=random.randint(2, 8)
                )
                ecosystem['sessions'].extend(user_sessions)

            return ecosystem

        @staticmethod
        def performance_test_factories():
            """Test factory performance and return timing results"""
            import time
            from tests.factories.user_factory import UserFactory

            results = {}

            # Test single object creation speed
            start_time = time.time()
            UserFactory.build_batch(1000)
            single_batch_time = time.time() - start_time
            results['1000_users'] = single_batch_time

            # Test different factory types
            for factory_name, factory_class in [
                ('GameFactory', GameFactory),
                ('AchievementFactory', AchievementFactory),
                ('WalletFactory', WalletFactory),
            ]:
                start_time = time.time()
                factory_class.build_batch(100)
                batch_time = time.time() - start_time
                results[f'100_{factory_name}'] = batch_time

            return results

    return FactoryUtils()


@pytest.fixture
def enhanced_mock_db(test_config_instance):
    """Enhanced mock database with TestConfig"""
    return test_config_instance.create_mock_db()


@pytest.fixture(autouse=True)
def performance_monitoring(request, test_config_instance):
    """Automatic performance monitoring for all tests"""
    test_name = request.node.name
    test_config_instance.start_test_timing(test_name)

    yield

    duration = test_config_instance.end_test_timing(test_name)
    if duration > test_config_instance.performance.slow_test_threshold:
        print(f"\n[PERFORMANCE WARNING] Slow test: {test_name} took {duration:.2f}s")


@pytest.fixture
def performance_config():
    """Access to performance configuration for tests"""
    return test_config.performance


@pytest.fixture
def override_test_config():
    """Factory for creating test config overrides"""
    def _override(**kwargs):
        return test_config.override(**kwargs)
    return _override


# ========================================
# GOO-35 Testing Utilities Integration
# ========================================

@pytest.fixture
def base_test_utils():
    """Enhanced test utilities with GOO-35 integration"""
    class BaseTestUtils:
        """Utility class providing enhanced testing capabilities"""

        @staticmethod
        def get_base_test_class(test_type: str) -> Type:
            """Get appropriate base test class for given type"""
            base_classes = {
                'unit': BaseUnitTest,
                'service': BaseServiceTest,
                'controller': BaseControllerTest,
                'integration': BaseIntegrationTest
            }
            return base_classes.get(test_type, BaseUnitTest)

        @staticmethod
        def create_test_data_builder(entity_type: str):
            """Get fluent builder for specified entity type"""
            builders = {
                'user': user,
                'game': game,
                'session': session,
                'achievement': achievement
            }
            builder_func = builders.get(entity_type)
            if builder_func:
                return builder_func()
            raise ValueError(f"No builder available for entity type: {entity_type}")

        @staticmethod
        def get_assertion_func(assertion_type: str):
            """Get appropriate assertion function"""
            assertions = {
                'user_valid': assert_user_valid,
                'game_valid': assert_game_valid,
                'session_valid': assert_session_valid,
                'api_response': assert_api_response_structure,
                'service_response': assert_service_response_pattern
            }
            return assertions.get(assertion_type)

        @staticmethod
        def create_matcher(matcher_type: str, **kwargs):
            """Create appropriate matcher instance"""
            matchers = {
                'user': UserSchemaMatcher,
                'game': GameSchemaMatcher,
                'session': SessionSchemaMatcher
            }
            matcher_class = matchers.get(matcher_type)
            if matcher_class:
                return matcher_class(**kwargs)
            raise ValueError(f"No matcher available for type: {matcher_type}")

    return BaseTestUtils()


@pytest.fixture
def enhanced_builders():
    """Enhanced builders integrated with Factory-Boy"""
    class EnhancedBuilders:
        """Builders that integrate GOO-35 fluent builders with Factory-Boy factories"""

        def __init__(self):
            # Integration with existing Factory-Boy factories
            self._factory_integration = {
                'user': {
                    'factory': None,  # Will be loaded lazily
                    'builder': user
                },
                'game': {
                    'factory': None,
                    'builder': game
                },
                'session': {
                    'factory': None,
                    'builder': session
                }
            }

        def user_builder(self, use_factory: bool = False):
            """Get user builder, optionally backed by Factory-Boy"""
            if use_factory:
                try:
                    from tests.factories.user_factory import UserFactory
                    # Create factory-backed builder
                    factory_data = UserFactory.build()
                    return user().with_data(factory_data)
                except ImportError:
                    pass
            return user()

        def game_builder(self, use_factory: bool = False):
            """Get game builder, optionally backed by Factory-Boy"""
            if use_factory:
                try:
                    from tests.factories.game_factory import GameFactory
                    factory_data = GameFactory.build()
                    return game().with_data(factory_data)
                except ImportError:
                    pass
            return game()

        def batch_create(self, entity_type: str, count: int, use_factory: bool = True):
            """Create batch of entities using optimal method"""
            if use_factory:
                try:
                    if entity_type == 'user':
                        from tests.factories.user_factory import UserFactory
                        return UserFactory.build_batch(count)
                    elif entity_type == 'game':
                        from tests.factories.game_factory import GameFactory
                        return GameFactory.build_batch(count)
                except ImportError:
                    pass

            # Fallback to GOO-35 builders
            builder = getattr(self, f'{entity_type}_builder')()
            return builder.build_batch(count)

    return EnhancedBuilders()


@pytest.fixture
def enhanced_auth():
    """Enhanced authentication utilities for testing"""
    class EnhancedAuth:
        """Authentication testing utilities with GOO-35 integration"""

        def __init__(self):
            self.current_mock_user = None

        def create_mock_user_context(self, user_type: str = 'regular', **user_attrs):
            """Create authenticated user context"""
            # Use GOO-35 user builder for consistency
            user_data = user().as_type(user_type).build()
            user_data.update(user_attrs)

            return MockAuthenticatedUser(
                user_id=user_data.get('_id'),
                role=user_data.get('role', user_type),
                **user_data
            )

        def create_auth_headers(self, user_data: Optional[Dict[str, Any]] = None):
            """Create authentication headers for requests"""
            if user_data:
                # Create JWT token mock
                token = f"test-token-{user_data.get('_id', 'default')}"
            else:
                token = 'test-token-default'

            return {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }

        def parametrized_user_types(self):
            """Get all user types for parametrized testing"""
            return ['admin', 'regular', 'premium', 'guest']

        def create_multi_user_scenario(self, user_types: list):
            """Create multiple users for complex scenarios"""
            users = []
            for user_type in user_types:
                user_data = user().as_type(user_type).build()
                users.append(user_data)
            return users

    return EnhancedAuth()


@pytest.fixture
def enhanced_mocks():
    """Enhanced mock utilities with GOO-35 integration"""
    class EnhancedMocks:
        """Mock utilities that integrate with GOO-35 testing patterns"""

        def create_database_mock(self):
            """Create database mock with GOO-35 patterns"""
            return MockDatabase()

        def create_password_mock(self, return_value: bool = True):
            """Create password checking mock"""
            return MockPasswordCheck(return_value=return_value)

        def create_service_mock(self, service_class: Type, **mock_methods):
            """Create service mock with predefined method returns"""
            mock_service = MagicMock(spec=service_class)
            for method_name, return_value in mock_methods.items():
                getattr(mock_service, method_name).return_value = return_value
            return mock_service

        def create_repository_mock(self, repository_class: Type, **mock_data):
            """Create repository mock with test data"""
            mock_repo = MagicMock(spec=repository_class)

            # Standard repository method mocks
            if 'find_by_id_return' in mock_data:
                mock_repo.find_by_id.return_value = mock_data['find_by_id_return']
            if 'create_return' in mock_data:
                mock_repo.create.return_value = mock_data['create_return']
            if 'update_return' in mock_data:
                mock_repo.update.return_value = mock_data['update_return']

            return mock_repo

    return EnhancedMocks()


@pytest.fixture
def migration_helpers():
    """Helpers for migrating existing tests to GOO-35 patterns"""
    class MigrationHelpers:
        """Utilities to assist in migrating legacy tests to new patterns"""

        @staticmethod
        def convert_fixture_to_builder(fixture_data: Dict[str, Any], entity_type: str):
            """Convert legacy fixture data to use GOO-35 builders"""
            builder_func = {
                'user': user,
                'game': game,
                'session': session,
                'achievement': achievement
            }.get(entity_type)

            if builder_func:
                builder = builder_func()
                for key, value in fixture_data.items():
                    # Use builder methods if available
                    method_name = f'with_{key}'
                    if hasattr(builder, method_name):
                        builder = getattr(builder, method_name)(value)
                return builder.build()

            return fixture_data

        @staticmethod
        def analyze_test_patterns(test_file_path: str):
            """Analyze existing test file for migration patterns"""
            # This would be implemented to scan test files and identify patterns
            # For now, return placeholder analysis
            return {
                'fixture_count': 0,
                'mock_patterns': [],
                'recommended_base_class': 'BaseUnitTest'
            }

        @staticmethod
        def suggest_migration_plan(test_class_code: str):
            """Suggest migration plan for a test class"""
            suggestions = []

            if 'Mock(' in test_class_code:
                suggestions.append("Replace manual mocks with BaseTest auto-injection")
            if 'pytest.fixture' in test_class_code:
                suggestions.append("Convert fixtures to GOO-35 builders")
            if 'setUp' in test_class_code or 'setup_method' in test_class_code:
                suggestions.append("Use BaseTest classes to eliminate setup")

            return suggestions

    return MigrationHelpers()


# Integration with existing Factory-Boy system
@pytest.fixture
def integrated_factories(enhanced_builders, factory_utils):
    """Integrated factory system combining GOO-35 builders with Factory-Boy"""
    class IntegratedFactories:
        def __init__(self, builders, factory_utils):
            self.builders = builders
            self.factory_utils = factory_utils

        def create_optimal(self, entity_type: str, count: int = 1, **kwargs):
            """Create entities using optimal approach (Factory-Boy for bulk, builders for custom)"""
            if count > 10:
                # Use Factory-Boy for bulk creation
                return self.builders.batch_create(entity_type, count, use_factory=True)
            else:
                # Use GOO-35 builders for detailed customization
                builder = getattr(self.builders, f'{entity_type}_builder')(use_factory=False)
                if count == 1:
                    for key, value in kwargs.items():
                        method_name = f'with_{key}'
                        if hasattr(builder, method_name):
                            builder = getattr(builder, method_name)(value)
                    return builder.build()
                else:
                    return [builder.build() for _ in range(count)]

    return IntegratedFactories(enhanced_builders, factory_utils)


# Performance monitoring integration
@pytest.fixture(autouse=True)
def enhanced_performance_monitoring(request, test_config_instance, performance_config):
    """Enhanced performance monitoring with GOO-35 integration"""
    test_name = request.node.name
    test_class = getattr(request.node, 'cls', None)

    # Check if test uses GOO-35 base classes
    uses_goo35 = False
    if test_class:
        base_classes = [BaseUnitTest, BaseServiceTest, BaseControllerTest, BaseIntegrationTest]
        uses_goo35 = any(issubclass(test_class, base_class) for base_class in base_classes)

    test_config_instance.start_test_timing(test_name, uses_goo35_utilities=uses_goo35)

    yield

    duration = test_config_instance.end_test_timing(test_name)
    threshold = performance_config.goo35_test_threshold if uses_goo35 else performance_config.slow_test_threshold

    if duration > threshold:
        test_type = "GOO-35" if uses_goo35 else "Legacy"
        print(f"\n[PERFORMANCE WARNING] Slow {test_type} test: {test_name} took {duration:.2f}s")