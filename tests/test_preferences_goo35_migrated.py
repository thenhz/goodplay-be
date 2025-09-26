"""
GOO-35 Preferences Testing Suite - Migrated Legacy Version

Migrated from legacy test_preferences.py to use GOO-35 Testing Utilities
with BasePreferencesTest for comprehensive preferences system testing.
"""
import os
import sys
from bson import ObjectId
from datetime import datetime, timezone

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.core.base_preferences_test import BasePreferencesTest
from app.preferences.services.preferences_service import PreferencesService


class TestPreferencesSystemGOO35(BasePreferencesTest):
    """GOO-35 Preferences System Testing"""
    service_class = PreferencesService

    def test_user_preferences_creation(self):
        """Test user preferences data structure"""
        user = self.create_test_user_with_preferences()

        self.assertIsNotNone(user['_id'])
        self.assertIn('preferences', user)
        self.assertIsNotNone(user['preferences'])

    def test_preference_settings(self):
        """Test preference settings functionality"""
        preferences = self.create_test_preferences(
            notifications={'push_enabled': True, 'email_enabled': False}
        )

        self.assertIsNotNone(preferences['_id'])
        self.assertIn('preferences', preferences)
        self.assertTrue(preferences['preferences']['notifications']['push_enabled'])
        self.assertFalse(preferences['preferences']['notifications']['email_enabled'])

    def test_preference_conflicts(self):
        """Test preference conflict scenarios"""
        # Test using sync conflict scenario with user_id
        from bson import ObjectId
        user_id = str(ObjectId())
        sync_conflict = self.create_sync_conflict_scenario(user_id)

        self.assertIsNotNone(sync_conflict)
        self.assertIn('conflicts', sync_conflict)
        self.assertIsInstance(sync_conflict['conflicts'], list)

    def test_preference_categories(self):
        """Test different preference categories"""
        # Test specific preference categories that exist in the structure
        gaming_prefs = self.create_custom_gaming_preferences(difficulty_level='hard')
        notification_prefs = self.create_custom_notification_preferences(push_enabled=True)

        self.assertEqual(gaming_prefs['preferences']['gaming']['difficulty_level'], 'hard')
        self.assertTrue(notification_prefs['preferences']['notifications']['push_enabled'])

    def test_preference_category_combinations(self):
        """Test preference category combinations"""
        # Create preferences with multiple category overrides
        combined_prefs = self.create_test_preferences(
            gaming={'difficulty_level': 'expert'},
            notifications={'push_enabled': False}
        )

        self.assertEqual(combined_prefs['preferences']['gaming']['difficulty_level'], 'expert')
        self.assertFalse(combined_prefs['preferences']['notifications']['push_enabled'])

    def test_preference_validation(self):
        """Test preference validation"""
        valid_preferences = self.create_test_preferences(
            privacy={'profile_visibility': 'public'},
            donations={'auto_donate_percentage': 10.0}
        )

        self.assertEqual(valid_preferences['preferences']['privacy']['profile_visibility'], 'public')
        self.assertEqual(valid_preferences['preferences']['donations']['auto_donate_percentage'], 10.0)
        self.assertIsNotNone(valid_preferences['_id'])