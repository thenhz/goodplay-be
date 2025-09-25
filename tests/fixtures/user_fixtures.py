"""
User-related fixtures for GoodPlay tests.

Provides pre-configured user data, authentication scenarios,
and user preference configurations.
"""
import pytest
from datetime import datetime, timezone, timedelta
from tests.core import TestUtils


@pytest.fixture
def test_utils():
    """Test utilities instance"""
    return TestUtils()


@pytest.fixture
def basic_user_data(test_utils):
    """Basic user registration data"""
    return {
        "email": test_utils.get_unique_email(),
        "password": "securepassword123",
        "first_name": "Test",
        "last_name": "User"
    }


@pytest.fixture
def admin_user_data(test_utils):
    """Admin user registration data"""
    return {
        "email": test_utils.get_unique_email(),
        "password": "adminpassword123",
        "first_name": "Admin",
        "last_name": "User",
        "is_admin": True
    }


@pytest.fixture
def complete_user_profile(test_utils):
    """Complete user profile with all optional fields"""
    return {
        "email": test_utils.get_unique_email(),
        "password": "completepassword123",
        "first_name": "Complete",
        "last_name": "User",
        "phone": test_utils.generate_random_phone(),
        "date_of_birth": "1990-05-15",
        "country": "US",
        "timezone": "America/New_York",
        "bio": "A complete test user profile",
        "avatar_url": "https://example.com/avatar.jpg"
    }


@pytest.fixture
def mock_user_in_db(test_utils):
    """Mock user already stored in database"""
    return test_utils.create_mock_user(
        email="existing@goodplay.test",
        is_verified=True,
        created_at=datetime.now(timezone.utc) - timedelta(days=30),
        last_login=datetime.now(timezone.utc) - timedelta(hours=2)
    )


@pytest.fixture
def unverified_user(test_utils):
    """Mock unverified user"""
    return test_utils.create_mock_user(
        email="unverified@goodplay.test",
        is_verified=False,
        created_at=datetime.now(timezone.utc) - timedelta(hours=1)
    )


@pytest.fixture
def inactive_user(test_utils):
    """Mock inactive user"""
    return test_utils.create_mock_user(
        email="inactive@goodplay.test",
        is_active=False,
        deactivated_at=datetime.now(timezone.utc) - timedelta(days=7)
    )


@pytest.fixture
def multiple_users(test_utils):
    """List of multiple mock users for testing"""
    return [
        test_utils.create_mock_user(
            email=f"user{i}@goodplay.test",
            first_name=f"User{i}",
            last_name="Test"
        ) for i in range(1, 6)
    ]


@pytest.fixture
def user_preferences_complete(test_utils):
    """Complete user preferences with all sections"""
    return test_utils.create_mock_user_preferences()


@pytest.fixture
def user_preferences_minimal():
    """Minimal user preferences"""
    return {
        "gaming": {
            "difficulty_level": "easy",
            "tutorial_enabled": True
        },
        "notifications": {
            "push_enabled": False,
            "email_enabled": False
        },
        "privacy": {
            "profile_visibility": "private"
        },
        "donations": {
            "auto_donate_enabled": False
        }
    }


@pytest.fixture
def user_preferences_gaming_focused():
    """Gaming-focused user preferences"""
    return {
        "gaming": {
            "preferred_categories": ["action", "adventure", "puzzle"],
            "difficulty_level": "hard",
            "tutorial_enabled": False,
            "auto_save": True,
            "sound_enabled": True,
            "music_enabled": True,
            "vibration_enabled": True
        },
        "notifications": {
            "achievement_alerts": True,
            "tournament_reminders": True,
            "friend_activity": True
        },
        "privacy": {
            "profile_visibility": "public",
            "stats_sharing": True,
            "leaderboard_participation": True,
            "activity_visibility": "friends"
        }
    }


@pytest.fixture
def user_preferences_privacy_focused():
    """Privacy-focused user preferences"""
    return {
        "gaming": {
            "difficulty_level": "medium",
            "tutorial_enabled": True
        },
        "notifications": {
            "push_enabled": False,
            "email_enabled": False,
            "achievement_alerts": False,
            "friend_activity": False
        },
        "privacy": {
            "profile_visibility": "private",
            "stats_sharing": False,
            "friends_discovery": False,
            "leaderboard_participation": False,
            "activity_visibility": "private",
            "contact_permissions": "none"
        }
    }


@pytest.fixture
def invalid_user_data_variants(basic_user_data, test_utils):
    """Invalid user data variants for error testing"""
    return test_utils.create_invalid_data_variants(basic_user_data)


@pytest.fixture
def auth_headers():
    """Mock authentication headers"""
    return {
        'Authorization': 'Bearer test-access-token',
        'Content-Type': 'application/json'
    }


@pytest.fixture
def expired_auth_headers():
    """Mock expired authentication headers"""
    return {
        'Authorization': 'Bearer expired-token',
        'Content-Type': 'application/json'
    }


@pytest.fixture
def invalid_auth_headers():
    """Invalid authentication headers"""
    return {
        'Authorization': 'Bearer invalid-token-format',
        'Content-Type': 'application/json'
    }