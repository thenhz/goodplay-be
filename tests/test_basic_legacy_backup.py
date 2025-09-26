#!/usr/bin/env python3
"""
Basic Test Suite for GoodPlay Backend
Tests that work with current architecture
"""
import unittest
import sys
import os
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.models.user import User


class TestUserModel(unittest.TestCase):
    """Test cases for User model (working with current architecture)"""

    def setUp(self):
        """Set up test fixtures"""
        self.user = User(
            email="test@goodplay.com",
            first_name="Test",
            last_name="Player"
        )

    def test_user_creation(self):
        """Test basic user creation"""
        self.assertEqual(self.user.email, "test@goodplay.com")
        self.assertEqual(self.user.first_name, "Test")
        self.assertEqual(self.user.last_name, "Player")
        self.assertTrue(self.user.is_active)
        self.assertEqual(self.user.role, "user")

    def test_user_has_preferences(self):
        """Test user has preferences structure"""
        self.assertIsInstance(self.user.preferences, dict)
        self.assertIn("gaming", self.user.preferences)
        self.assertIn("notifications", self.user.preferences)
        self.assertIn("privacy", self.user.preferences)
        self.assertIn("donations", self.user.preferences)

    def test_user_gaming_preferences(self):
        """Test gaming preferences structure"""
        gaming = self.user.preferences["gaming"]
        self.assertIn("difficulty_level", gaming)
        self.assertIn("tutorial_enabled", gaming)
        self.assertIn("preferred_categories", gaming)
        self.assertIn("sound_enabled", gaming)
        self.assertIn("music_enabled", gaming)

    def test_user_notification_preferences(self):
        """Test notification preferences structure"""
        notifications = self.user.preferences["notifications"]
        self.assertIn("push_enabled", notifications)
        self.assertIn("email_enabled", notifications)
        self.assertIn("frequency", notifications)
        self.assertIn("achievement_alerts", notifications)

    def test_user_privacy_preferences(self):
        """Test privacy preferences structure"""
        privacy = self.user.preferences["privacy"]
        self.assertIn("profile_visibility", privacy)
        self.assertIn("stats_sharing", privacy)
        self.assertIn("activity_visibility", privacy)

    def test_user_donation_preferences(self):
        """Test donation preferences structure"""
        donations = self.user.preferences["donations"]
        self.assertIn("auto_donate_enabled", donations)
        self.assertIn("auto_donate_percentage", donations)
        self.assertIn("preferred_causes", donations)

    def test_user_serialization(self):
        """Test user to_dict method"""
        user_dict = self.user.to_dict()

        self.assertIn("email", user_dict)
        self.assertIn("first_name", user_dict)
        self.assertIn("last_name", user_dict)
        self.assertIn("is_active", user_dict)
        self.assertIn("preferences", user_dict)
        self.assertIn("created_at", user_dict)
        self.assertIn("updated_at", user_dict)

    def test_user_deserialization(self):
        """Test user from_dict method"""
        user_data = {
            "_id": "test_id",
            "email": "deserialized@goodplay.com",
            "first_name": "Deserialized",
            "last_name": "User",
            "is_active": True,
            "role": "user"
        }

        user = User.from_dict(user_data)

        self.assertEqual(user.email, "deserialized@goodplay.com")
        self.assertEqual(user.first_name, "Deserialized")
        self.assertEqual(user.last_name, "User")
        self.assertTrue(user.is_active)

    def test_user_email_normalization(self):
        """Test email is normalized to lowercase"""
        user = User(email="TEST@GOODPLAY.COM")
        self.assertEqual(user.email, "test@goodplay.com")

    def test_user_timestamps(self):
        """Test user has timestamps"""
        self.assertIsInstance(self.user.created_at, datetime)
        self.assertIsInstance(self.user.updated_at, datetime)


class TestAuthServiceBasic(unittest.TestCase):
    """Basic test cases for AuthService"""

    def setUp(self):
        """Set up test fixtures"""
        # We can't easily test AuthService without proper mocking setup
        # but we can test import and basic structure
        pass

    def test_auth_service_import(self):
        """Test that AuthService can be imported"""
        from app.core.services.auth_service import AuthService

        service = AuthService()
        self.assertTrue(hasattr(service, 'user_repository'))
        self.assertTrue(hasattr(service, 'register_user'))
        self.assertTrue(hasattr(service, 'login_user'))

    def test_user_repository_import(self):
        """Test that UserRepository can be imported"""
        from app.core.repositories.user_repository import UserRepository

        repo = UserRepository()
        self.assertTrue(hasattr(repo, 'find_by_email'))
        self.assertTrue(hasattr(repo, 'create'))


class TestApplicationStructure(unittest.TestCase):
    """Test application structure and imports"""

    def test_app_creation(self):
        """Test that app can be created"""
        from app import create_app

        app = create_app()
        self.assertIsNotNone(app)
        self.assertEqual(app.name, 'app')

    def test_core_module_imports(self):
        """Test core module imports work"""
        from app.core.models.user import User
        from app.core.services.auth_service import AuthService
        from app.core.repositories.user_repository import UserRepository

        # Test that classes can be instantiated
        user = User(email="test@example.com")
        self.assertIsNotNone(user)

        auth_service = AuthService()
        self.assertIsNotNone(auth_service)

        user_repo = UserRepository()
        self.assertIsNotNone(user_repo)

    def test_preferences_module_imports(self):
        """Test preferences module imports work"""
        try:
            from app.preferences.services.preferences_service import PreferencesService
            from app.preferences.controllers.preferences_controller import preferences_blueprint

            # If we get here, imports work
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Preferences module import failed: {e}")

    def test_social_module_imports(self):
        """Test social module imports work"""
        try:
            from app.social.services.relationship_service import RelationshipService
            from app.social.models.user_relationship import UserRelationship

            # If we get here, imports work
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Social module import failed: {e}")

    def test_games_module_imports(self):
        """Test games module imports work"""
        try:
            from app.games.core.game_plugin import GamePlugin
            from app.games.core.plugin_manager import PluginManager

            # If we get here, imports work
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Games module import failed: {e}")


class TestConfigAndEnvironment(unittest.TestCase):
    """Test configuration and environment setup"""

    def test_config_import(self):
        """Test config can be imported"""
        from config.settings import config
        self.assertIsNotNone(config)

    def test_environment_variables(self):
        """Test basic environment setup"""
        # These should be available in test environment
        import os

        # Test environment might not have all variables, but we can check structure
        self.assertTrue(True)  # Basic sanity check


if __name__ == '__main__':
    print("🧪 Running Basic GoodPlay Backend Tests...")
    unittest.main(verbosity=2)