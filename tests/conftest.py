"""
Pytest configuration and shared fixtures for GoodPlay test suite
"""
import pytest
import sys
import os
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set testing environment before any imports
os.environ['TESTING'] = 'true'
os.environ['MONGO_URI'] = 'mongodb://localhost:27017/goodplay_test'
os.environ['JWT_SECRET_KEY'] = 'test-jwt-secret'
os.environ['SECRET_KEY'] = 'test-secret'

# Mock database operations before importing app modules
with patch('pymongo.collection.Collection.create_index'), \
     patch('app.core.repositories.base_repository.get_db') as mock_get_db:
    mock_collection = MagicMock()
    mock_db = MagicMock()
    mock_db.__getitem__ = MagicMock(return_value=mock_collection)
    mock_get_db.return_value = mock_db

    from app import create_app
    from app.core.models.user import User


@pytest.fixture(scope="session")
def app():
    """Create application for testing"""
    # Create app (env vars already set above)
    app = create_app()
    app.config.update({
        'TESTING': True,
        'MONGO_URI': 'mongodb://localhost:27017/goodplay_test',
        'JWT_SECRET_KEY': 'test-jwt-secret',
        'SECRET_KEY': 'test-secret'
    })
    return app


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