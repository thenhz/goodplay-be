"""
GOO-35 Achievement Testing Suite

Migrated from legacy test_achievements.py to use GOO-35 Testing Utilities
with BaseSocialTest for comprehensive achievement system testing.
"""
import os
import sys
from bson import ObjectId
from datetime import datetime, timezone

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.core.base_social_test import BaseSocialTest
from app.social.achievements.services.achievement_engine import AchievementEngine
from app.social.achievements.repositories.achievement_repository import AchievementRepository


class TestAchievementSystemGOO35(BaseSocialTest):
    """
    GOO-35 Achievement System Testing

    Comprehensive testing for Achievement models, services, and workflows
    using GOO-35 utilities for maximum efficiency and maintainability.
    """
    service_class = AchievementEngine

    def test_achievement_creation_and_validation(self):
        """Test achievement creation with comprehensive validation"""
        # Create test achievement using GOO-35 utilities
        achievement = self.create_test_achievement(
            achievement_type='gaming',
            criteria={'games_played': 10},
            name='Gaming Master',
            description='Play 10 games',
            category='gaming',
            reward_credits=100
        )

        # Validate achievement structure
        self.assertEqual(achievement['name'], 'Gaming Master')
        self.assertEqual(achievement['reward_credits'], 100)
        self.assertIsNotNone(achievement['_id'])
        self.assertEqual(achievement['category'], 'gaming')

    def test_achievement_rarity_system(self):
        """Test achievement rarity system"""
        # Test different rarities
        rarities = ['common', 'rare', 'epic', 'legendary']

        for rarity in rarities:
            achievement = self.create_test_achievement(
                achievement_type='score',
                criteria={'min_score': 1000},
                badge_rarity=rarity
            )

            self.assertEqual(achievement['badge_rarity'], rarity)
            self.assertIsNotNone(achievement['_id'])

    def test_user_achievement_progress_tracking(self):
        """Test user achievement progress and completion"""
        # Create user and achievement
        user = self.create_test_social_user(display_name='Achievement Hunter')
        achievement = self.create_test_achievement(
            achievement_type='social',
            criteria={'friends_count': 5}
        )

        # Create user achievement with progress
        user_achievement = self.create_test_user_achievement(
            user_id=user['_id'],
            achievement_id=achievement['_id'],
            progress={'current_friends': 3},
            status='in_progress'
        )

        # Test progress structure
        self.assertEqual(user_achievement['status'], 'in_progress')
        self.assertIsNotNone(user_achievement['progress'])
        self.assertEqual(user_achievement['progress']['current_friends'], 3)

    def test_achievement_unlock_flow(self):
        """Test complete achievement unlock workflow"""
        # Setup achievement unlock scenario
        user = self.create_test_social_user()
        unlock_result = self.mock_achievement_unlock_scenario(
            user['_id'],
            achievement_type='score'
        )

        # Verify achievement was unlocked correctly
        self.assert_achievement_unlocked(
            unlock_result,
            expected_achievement_id=unlock_result[2]['achievement']['_id']
        )

        # Verify user received credits
        self.assertGreater(unlock_result[2]['credits_awarded'], 0)

    def test_achievement_categories(self):
        """Test achievement category system"""
        # Create achievements in different categories
        categories = ['gaming', 'social', 'donation']
        created_achievements = []

        for category in categories:
            achievement = self.create_test_achievement(
                achievement_type=category,
                criteria={'activity_count': 1},
                category=category
            )
            created_achievements.append(achievement)

        # Verify all achievements were created with correct categories
        for i, achievement in enumerate(created_achievements):
            self.assertEqual(achievement['category'], categories[i])

    def test_achievement_notifications(self):
        """Test achievement progress notifications"""
        user = self.create_test_social_user()
        achievement = self.create_test_achievement(
            achievement_type='progress',
            criteria={'daily_logins': 7},
            notify_on_progress=True
        )

        # Create progress notification scenario
        notification = self.create_test_notification(
            user_id=user['_id'],
            notification_type='achievement',
            content={
                'achievement_id': achievement['_id'],
                'progress': 5,
                'target': 7,
                'message': 'Keep going! 2 more days to unlock!'
            }
        )

        self.assertEqual(notification['type'], 'achievement')
        self.assertEqual(notification['content']['progress'], 5)
        self.assertEqual(notification['content']['target'], 7)


class TestAchievementRepositoryGOO35(BaseSocialTest):
    """GOO-35 Achievement Repository Testing"""
    service_class = AchievementRepository

    def test_achievement_data_structure(self):
        """Test achievement data structure and validation"""
        # Create achievement data
        achievement_data = self.create_test_achievement(
            achievement_type='gaming',
            name='Repository Test Achievement',
            description='Test achievement for repository',
            reward_credits=50
        )

        # Verify data structure
        self.assertEqual(achievement_data['name'], 'Repository Test Achievement')
        self.assertEqual(achievement_data['reward_credits'], 50)
        self.assertIsNotNone(achievement_data['_id'])
        self.assertIsNotNone(achievement_data['created_at'])

    def test_achievement_status_filtering(self):
        """Test achievement status filtering"""
        # Create active and inactive achievements
        active_achievement = self.create_test_achievement(
            achievement_type='gaming',
            is_active=True,
            name='Active Achievement'
        )

        inactive_achievement = self.create_test_achievement(
            achievement_type='social',
            is_active=False,
            name='Inactive Achievement'
        )

        # Verify status properties
        self.assertTrue(active_achievement['is_active'])
        self.assertFalse(inactive_achievement['is_active'])