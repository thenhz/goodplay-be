"""
Pytest configuration and shared fixtures for GoodPlay test suite

Enhanced configuration with TestConfig integration for enterprise-grade testing.
"""
import pytest
import sys
import os
import random
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import TestConfig before setting environment
from tests.core.config import TestConfig, get_test_config

# Initialize test configuration
test_config = get_test_config()

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