"""
Pytest configuration and shared fixtures for GoodPlay test suite

Enhanced configuration with TestConfig integration for enterprise-grade testing.
"""
import pytest
import sys
import os
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


@pytest.fixture
def user_factory(test_utils):
    """User factory for creating test users"""
    from tests.factories.user_factory import UserFactory
    return UserFactory(test_utils)


@pytest.fixture
def game_factory(test_utils):
    """Game factory for creating test games and sessions"""
    from tests.factories.game_factory import GameFactory, GameSessionFactory
    return {
        'game': GameFactory(test_utils),
        'session': GameSessionFactory(test_utils)
    }


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