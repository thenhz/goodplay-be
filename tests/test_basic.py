"""
Basic Test Suite for GoodPlay Backend
Tests for core User model functionality using modern testing architecture
"""
import os
import sys
from bson import ObjectId
from datetime import datetime, timezone

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.core.base_auth_test import BaseAuthTest
from app.core.services.user_service import UserService


class TestUserModel(BaseAuthTest):
    """Test cases for User model using modern testing framework"""
    service_class = UserService

    def test_user_creation(self):
        """Test basic user creation"""
        user = self.create_test_user(
            email="test@goodplay.com",
            first_name="Test",
            last_name="Player"
        )

        self.assertEqual(user['email'], "test@goodplay.com")
        self.assertEqual(user['first_name'], "Test")
        self.assertEqual(user['last_name'], "Player")
        self.assertTrue(user['is_active'])
        self.assertEqual(user['role'], "user")

    def test_user_has_preferences(self):
        """Test user has preferences structure"""
        user_with_prefs = self.create_test_user_with_preferences()

        self.assertIn('preferences', user_with_prefs)
        preferences = user_with_prefs['preferences']

        self.assertIn("gaming", preferences)
        self.assertIn("notifications", preferences)
        self.assertIn("privacy", preferences)
        self.assertIn("donations", preferences)

    def test_user_gaming_preferences(self):
        """Test gaming preferences structure"""
        gaming_prefs = self.create_custom_gaming_preferences(
            difficulty_level="medium",
            tutorial_enabled=True,
            sound_enabled=True
        )

        gaming = gaming_prefs['preferences']['gaming']
        self.assertIn("difficulty_level", gaming)
        self.assertIn("tutorial_enabled", gaming)
        self.assertIn("preferred_categories", gaming)
        self.assertIn("sound_enabled", gaming)
        self.assertIn("music_enabled", gaming)

    def test_user_notification_preferences(self):
        """Test notification preferences structure"""
        notification_prefs = self.create_custom_notification_preferences(
            push_enabled=True,
            email_enabled=False,
            frequency="daily"
        )

        notifications = notification_prefs['preferences']['notifications']
        self.assertIn("push_enabled", notifications)
        self.assertIn("email_enabled", notifications)
        self.assertIn("frequency", notifications)
        self.assertIn("achievement_alerts", notifications)

    def test_user_privacy_preferences(self):
        """Test privacy preferences structure"""
        privacy_prefs = self.create_privacy_preferences(privacy_level='medium')

        privacy = privacy_prefs['preferences']['privacy']
        self.assertIn("profile_visibility", privacy)
        self.assertIn("stats_sharing", privacy)
        self.assertIn("activity_visibility", privacy)

    def test_user_donation_preferences(self):
        """Test donation preferences structure"""
        user_with_prefs = self.create_test_user_with_preferences()

        donations = user_with_prefs['preferences']['donations']
        self.assertIn("auto_donate_enabled", donations)
        self.assertIn("auto_donate_percentage", donations)
        self.assertIn("preferred_causes", donations)

    def test_user_data_structure(self):
        """Test user data structure completeness"""
        user = self.create_test_user(
            email="structure@test.com",
            role="admin"
        )

        # Validate required fields
        self.assertIn("email", user)
        self.assertIn("first_name", user)
        self.assertIn("last_name", user)
        self.assertIn("is_active", user)
        self.assertIn("role", user)
        self.assertIn("created_at", user)
        self.assertIn("updated_at", user)
        self.assertIsNotNone(user["_id"])

    def test_user_role_validation(self):
        """Test different user roles"""
        roles = ['user', 'admin', 'moderator', 'premium']

        for role in roles:
            user = self.create_test_user(
                email=f"{role}@test.com",
                role=role
            )
            self.assertEqual(user['role'], role)
            self.assert_user_valid(user, expected_role=role)

    def test_user_authentication_data(self):
        """Test user authentication related fields"""
        auth_data = self.create_test_auth_data(
            email="auth@test.com",
            verified=True
        )

        self.assertIn("password_hash", auth_data)
        self.assertIn("is_verified", auth_data)
        self.assertTrue(auth_data["is_verified"])
        self.assertIsNotNone(auth_data["password_hash"])

    def test_user_status_scenarios(self):
        """Test different user status scenarios"""
        # Active user
        active_user = self.create_test_user(is_active=True)
        self.assertTrue(active_user['is_active'])

        # Inactive user
        inactive_user = self.create_test_user(is_active=False)
        self.assertFalse(inactive_user['is_active'])

        # Verified user scenario
        verified_scenario = self.create_verified_user_scenario()
        self.assertTrue(verified_scenario['user']['is_verified'])

    def test_user_preferences_categories(self):
        """Test comprehensive user preferences categories"""
        user_with_prefs = self.create_test_user_with_preferences()
        preferences = user_with_prefs['preferences']

        # Test all expected preference categories
        expected_categories = [
            'gaming', 'notifications', 'privacy', 'donations',
            'accessibility', 'meta'
        ]

        for category in expected_categories:
            self.assertIn(category, preferences)
            self.assertIsInstance(preferences[category], dict)

    def test_user_meta_information(self):
        """Test user meta information and timestamps"""
        user = self.create_test_user()

        # Test timestamps exist
        self.assertIn('created_at', user)
        self.assertIn('updated_at', user)

        # Test meta information if present
        if 'preferences' in user and 'meta' in user['preferences']:
            meta = user['preferences']['meta']
            self.assertIn('version', meta)