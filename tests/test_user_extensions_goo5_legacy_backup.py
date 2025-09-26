#!/usr/bin/env python3
"""
Unit Tests for GOO-5: User Model Extensions
Tests gaming stats, preferences, social profile, and wallet functionality
"""
import unittest
from datetime import datetime, timezone
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.models.user import User

class TestUserExtensions(unittest.TestCase):
    """Test cases for User model extensions"""

    def setUp(self):
        """Set up test fixtures"""
        self.user = User(
            email="test@goodplay.com",
            first_name="Test",
            last_name="Player"
        )

    def test_user_creation_with_defaults(self):
        """Test user creation includes all default extended fields"""
        self.assertIsInstance(self.user.gaming_stats, dict)
        self.assertEqual(self.user.gaming_stats['total_play_time'], 0)
        self.assertEqual(self.user.gaming_stats['games_played'], 0)
        self.assertIsNone(self.user.gaming_stats['favorite_category'])
        self.assertIsNone(self.user.gaming_stats['last_activity'])

        self.assertIsInstance(self.user.preferences, dict)
        self.assertTrue(self.user.preferences['notification_enabled'])
        self.assertEqual(self.user.preferences['preferred_game_categories'], [])
        self.assertEqual(self.user.preferences['donation_frequency'], 'weekly')

        self.assertIsInstance(self.user.social_profile, dict)
        self.assertEqual(self.user.social_profile['display_name'], 'Test')
        self.assertEqual(self.user.social_profile['privacy_level'], 'public')
        self.assertEqual(self.user.social_profile['friends_count'], 0)

        self.assertIsInstance(self.user.wallet_credits, dict)
        self.assertEqual(self.user.wallet_credits['current_balance'], 0.0)
        self.assertEqual(self.user.wallet_credits['total_earned'], 0.0)
        self.assertEqual(self.user.wallet_credits['total_donated'], 0.0)

        self.assertEqual(self.user.impact_score, 0)

    def test_update_gaming_stats(self):
        """Test updating gaming statistics"""
        initial_updated_at = self.user.updated_at

        self.user.update_gaming_stats(play_time=45, game_category="puzzle")

        self.assertEqual(self.user.gaming_stats['total_play_time'], 45)
        self.assertEqual(self.user.gaming_stats['favorite_category'], "puzzle")
        self.assertIsInstance(self.user.gaming_stats['last_activity'], datetime)
        self.assertGreater(self.user.updated_at, initial_updated_at)

    def test_add_credits(self):
        """Test adding credits to wallet"""
        initial_updated_at = self.user.updated_at

        self.user.add_credits(25.5, 'earned')

        self.assertEqual(self.user.wallet_credits['current_balance'], 25.5)
        self.assertEqual(self.user.wallet_credits['total_earned'], 25.5)
        self.assertEqual(self.user.wallet_credits['total_donated'], 0.0)
        self.assertGreater(self.user.updated_at, initial_updated_at)

    def test_donate_credits_successful(self):
        """Test successful credit donation"""
        self.user.add_credits(50.0)
        initial_updated_at = self.user.updated_at

        result = self.user.donate_credits(20.0)

        self.assertTrue(result)
        self.assertEqual(self.user.wallet_credits['current_balance'], 30.0)
        self.assertEqual(self.user.wallet_credits['total_donated'], 20.0)
        self.assertGreater(self.user.updated_at, initial_updated_at)

    def test_donate_credits_insufficient_balance(self):
        """Test donation with insufficient balance"""
        self.user.add_credits(10.0)

        result = self.user.donate_credits(20.0)

        self.assertFalse(result)
        self.assertEqual(self.user.wallet_credits['current_balance'], 10.0)
        self.assertEqual(self.user.wallet_credits['total_donated'], 0.0)

    def test_update_preferences(self):
        """Test updating user preferences"""
        initial_updated_at = self.user.updated_at

        self.user.update_preferences(
            notification_enabled=False,
            donation_frequency='monthly'
        )

        self.assertFalse(self.user.preferences['notification_enabled'])
        self.assertEqual(self.user.preferences['donation_frequency'], 'monthly')
        self.assertGreater(self.user.updated_at, initial_updated_at)

    def test_update_social_profile(self):
        """Test updating social profile"""
        initial_updated_at = self.user.updated_at

        self.user.update_social_profile(
            display_name='SuperPlayer',
            privacy_level='friends'
        )

        self.assertEqual(self.user.social_profile['display_name'], 'SuperPlayer')
        self.assertEqual(self.user.social_profile['privacy_level'], 'friends')
        self.assertGreater(self.user.updated_at, initial_updated_at)

    def test_to_dict_includes_extended_fields(self):
        """Test serialization includes all extended fields"""
        user_dict = self.user.to_dict()

        self.assertIn('gaming_stats', user_dict)
        self.assertIn('impact_score', user_dict)
        self.assertIn('preferences', user_dict)
        self.assertIn('social_profile', user_dict)
        self.assertIn('wallet_credits', user_dict)

    def test_from_dict_with_extended_fields(self):
        """Test deserialization with extended fields"""
        # First serialize
        user_dict = self.user.to_dict()

        # Modify some extended fields
        user_dict['gaming_stats']['total_play_time'] = 120
        user_dict['impact_score'] = 85
        user_dict['preferences']['notification_enabled'] = False

        # Deserialize
        restored_user = User.from_dict(user_dict)

        self.assertEqual(restored_user.gaming_stats['total_play_time'], 120)
        self.assertEqual(restored_user.impact_score, 85)
        self.assertFalse(restored_user.preferences['notification_enabled'])

    def test_backward_compatibility(self):
        """Test that User can be created from old format data"""
        old_user_data = {
            '_id': 'test_id',
            'email': 'old@goodplay.com',
            'first_name': 'Old',
            'last_name': 'User',
            'is_active': True,
            'role': 'user'
        }

        user = User.from_dict(old_user_data)

        # Should have all new fields with defaults
        self.assertIsNotNone(user.gaming_stats)
        self.assertIsNotNone(user.preferences)
        self.assertIsNotNone(user.social_profile)
        self.assertIsNotNone(user.wallet_credits)
        self.assertEqual(user.impact_score, 0)

if __name__ == '__main__':
    print("🧪 Running GOO-5 User Extensions Tests...")
    unittest.main(verbosity=2)