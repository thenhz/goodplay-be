import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from bson import ObjectId

# Import the classes we want to test
from app.social.achievements.models.achievement import Achievement
from app.social.achievements.models.user_achievement import UserAchievement
from app.social.achievements.models.badge import Badge
from app.social.achievements.repositories.achievement_repository import AchievementRepository
from app.social.achievements.services.achievement_engine import AchievementEngine
from app.social.achievements.services.progress_tracker import ProgressTracker
from app.social.achievements.services.badge_service import BadgeService


class TestAchievementModel(unittest.TestCase):
    """Test cases for Achievement model"""

    def test_achievement_creation_valid(self):
        """Test creating a valid achievement"""
        achievement = Achievement(
            achievement_id="test_achievement",
            name="Test Achievement",
            description="A test achievement",
            category=Achievement.GAMING,
            trigger_conditions={
                "type": Achievement.GAME_SESSION,
                "target_value": 1
            },
            badge_rarity=Achievement.COMMON,
            reward_credits=10
        )

        self.assertEqual(achievement.achievement_id, "test_achievement")
        self.assertEqual(achievement.name, "Test Achievement")
        self.assertEqual(achievement.category, Achievement.GAMING)
        self.assertEqual(achievement.badge_rarity, Achievement.COMMON)
        self.assertEqual(achievement.reward_credits, 10)
        self.assertTrue(achievement.is_active)

    def test_achievement_validation_invalid_category(self):
        """Test achievement validation with invalid category"""
        with self.assertRaises(ValueError) as context:
            Achievement(
                achievement_id="test_achievement",
                name="Test Achievement",
                description="A test achievement",
                category="invalid_category",
                trigger_conditions={
                    "type": Achievement.GAME_SESSION,
                    "target_value": 1
                }
            )
        self.assertIn("Invalid category", str(context.exception))

    def test_achievement_validation_invalid_rarity(self):
        """Test achievement validation with invalid badge rarity"""
        with self.assertRaises(ValueError) as context:
            Achievement(
                achievement_id="test_achievement",
                name="Test Achievement",
                description="A test achievement",
                category=Achievement.GAMING,
                trigger_conditions={
                    "type": Achievement.GAME_SESSION,
                    "target_value": 1
                },
                badge_rarity="invalid_rarity"
            )
        self.assertIn("Invalid badge rarity", str(context.exception))

    def test_achievement_validation_invalid_trigger_type(self):
        """Test achievement validation with invalid trigger type"""
        with self.assertRaises(ValueError) as context:
            Achievement(
                achievement_id="test_achievement",
                name="Test Achievement",
                description="A test achievement",
                category=Achievement.GAMING,
                trigger_conditions={
                    "type": "invalid_trigger",
                    "target_value": 1
                }
            )
        self.assertIn("Invalid trigger type", str(context.exception))

    def test_achievement_condition_checking(self):
        """Test achievement condition checking"""
        achievement = Achievement(
            achievement_id="score_achievement",
            name="Score Achievement",
            description="Score based achievement",
            category=Achievement.GAMING,
            trigger_conditions={
                "type": Achievement.GAME_SCORE,
                "target_value": 1000,
                "comparison": "gte"
            }
        )

        self.assertTrue(achievement.check_condition(1000))
        self.assertTrue(achievement.check_condition(1500))
        self.assertFalse(achievement.check_condition(500))

    def test_achievement_rarity_multiplier(self):
        """Test rarity multiplier calculation"""
        common_achievement = Achievement(
            achievement_id="common_test",
            name="Common",
            description="Common achievement",
            category=Achievement.GAMING,
            trigger_conditions={"type": Achievement.GAME_SESSION, "target_value": 1},
            badge_rarity=Achievement.COMMON,
            reward_credits=10
        )

        legendary_achievement = Achievement(
            achievement_id="legendary_test",
            name="Legendary",
            description="Legendary achievement",
            category=Achievement.GAMING,
            trigger_conditions={"type": Achievement.GAME_SESSION, "target_value": 1},
            badge_rarity=Achievement.LEGENDARY,
            reward_credits=10
        )

        self.assertEqual(common_achievement.get_rarity_multiplier(), 1.0)
        self.assertEqual(legendary_achievement.get_rarity_multiplier(), 3.0)
        self.assertEqual(common_achievement.calculate_final_reward(), 10)
        self.assertEqual(legendary_achievement.calculate_final_reward(), 30)

    def test_achievement_to_dict_conversion(self):
        """Test achievement to dictionary conversion"""
        achievement = Achievement(
            achievement_id="test_achievement",
            name="Test Achievement",
            description="A test achievement",
            category=Achievement.GAMING,
            trigger_conditions={
                "type": Achievement.GAME_SESSION,
                "target_value": 1
            }
        )

        data = achievement.to_dict()
        self.assertEqual(data['achievement_id'], "test_achievement")
        self.assertEqual(data['name'], "Test Achievement")
        self.assertEqual(data['category'], Achievement.GAMING)
        self.assertIn('_id', data)
        self.assertIn('created_at', data)

    def test_achievement_from_dict_creation(self):
        """Test creating achievement from dictionary"""
        data = {
            '_id': ObjectId(),
            'achievement_id': 'test_achievement',
            'name': 'Test Achievement',
            'description': 'A test achievement',
            'category': Achievement.GAMING,
            'trigger_conditions': {
                'type': Achievement.GAME_SESSION,
                'target_value': 1
            },
            'badge_rarity': Achievement.COMMON,
            'reward_credits': 10,
            'is_active': True,
            'created_at': datetime.utcnow()
        }

        achievement = Achievement.from_dict(data)
        self.assertEqual(achievement.achievement_id, 'test_achievement')
        self.assertEqual(achievement.name, 'Test Achievement')
        self.assertEqual(achievement.category, Achievement.GAMING)


class TestUserAchievementModel(unittest.TestCase):
    """Test cases for UserAchievement model"""

    def test_user_achievement_creation(self):
        """Test creating a user achievement"""
        user_achievement = UserAchievement(
            user_id="507f1f77bcf86cd799439011",
            achievement_id="test_achievement",
            progress=0,
            max_progress=10
        )

        self.assertEqual(str(user_achievement.user_id), "507f1f77bcf86cd799439011")
        self.assertEqual(user_achievement.achievement_id, "test_achievement")
        self.assertEqual(user_achievement.progress, 0)
        self.assertEqual(user_achievement.max_progress, 10)
        self.assertFalse(user_achievement.is_completed)
        self.assertFalse(user_achievement.reward_claimed)

    def test_user_achievement_progress_update(self):
        """Test updating user achievement progress"""
        user_achievement = UserAchievement(
            user_id="507f1f77bcf86cd799439011",
            achievement_id="test_achievement",
            progress=0,
            max_progress=5
        )

        # Test progress increment without completion
        was_completed = user_achievement.increment_progress(2)
        self.assertFalse(was_completed)
        self.assertEqual(user_achievement.progress, 2)
        self.assertFalse(user_achievement.is_completed)

        # Test progress increment with completion
        was_completed = user_achievement.increment_progress(3)
        self.assertTrue(was_completed)
        self.assertEqual(user_achievement.progress, 5)
        self.assertTrue(user_achievement.is_completed)
        self.assertIsNotNone(user_achievement.completed_at)

    def test_user_achievement_progress_percentage(self):
        """Test progress percentage calculation"""
        user_achievement = UserAchievement(
            user_id="507f1f77bcf86cd799439011",
            achievement_id="test_achievement",
            progress=3,
            max_progress=10
        )

        self.assertEqual(user_achievement.get_progress_percentage(), 30.0)

        user_achievement.progress = 10
        self.assertEqual(user_achievement.get_progress_percentage(), 100.0)

    def test_user_achievement_reward_claiming(self):
        """Test reward claiming functionality"""
        user_achievement = UserAchievement(
            user_id="507f1f77bcf86cd799439011",
            achievement_id="test_achievement",
            progress=5,
            max_progress=5,
            is_completed=True,
            completed_at=datetime.utcnow()
        )

        # Should be able to claim reward
        self.assertTrue(user_achievement.is_ready_to_claim())

        success = user_achievement.claim_reward()
        self.assertTrue(success)
        self.assertTrue(user_achievement.reward_claimed)
        self.assertIsNotNone(user_achievement.claimed_at)

        # Should not be able to claim again
        success = user_achievement.claim_reward()
        self.assertFalse(success)

    def test_user_achievement_validation(self):
        """Test user achievement validation"""
        # Test invalid progress values
        with self.assertRaises(ValueError):
            UserAchievement(
                user_id="507f1f77bcf86cd799439011",
                achievement_id="test_achievement",
                progress=-1,
                max_progress=10
            )

        with self.assertRaises(ValueError):
            UserAchievement(
                user_id="507f1f77bcf86cd799439011",
                achievement_id="test_achievement",
                progress=15,
                max_progress=10
            )


class TestBadgeModel(unittest.TestCase):
    """Test cases for Badge model"""

    def test_badge_creation(self):
        """Test creating a badge"""
        badge = Badge(
            user_id="507f1f77bcf86cd799439011",
            achievement_id="test_achievement",
            badge_name="Test Badge",
            badge_description="A test badge",
            rarity=Badge.RARE
        )

        self.assertEqual(str(badge.user_id), "507f1f77bcf86cd799439011")
        self.assertEqual(badge.achievement_id, "test_achievement")
        self.assertEqual(badge.badge_name, "Test Badge")
        self.assertEqual(badge.rarity, Badge.RARE)
        self.assertTrue(badge.is_visible)

    def test_badge_rarity_methods(self):
        """Test badge rarity checking methods"""
        common_badge = Badge(
            user_id="507f1f77bcf86cd799439011",
            achievement_id="test_achievement",
            badge_name="Common Badge",
            badge_description="A common badge",
            rarity=Badge.COMMON
        )

        legendary_badge = Badge(
            user_id="507f1f77bcf86cd799439011",
            achievement_id="test_achievement",
            badge_name="Legendary Badge",
            badge_description="A legendary badge",
            rarity=Badge.LEGENDARY
        )

        self.assertTrue(common_badge.is_common())
        self.assertFalse(common_badge.is_legendary())
        self.assertTrue(legendary_badge.is_legendary())
        self.assertFalse(legendary_badge.is_common())

    def test_badge_rarity_properties(self):
        """Test badge rarity display properties"""
        epic_badge = Badge(
            user_id="507f1f77bcf86cd799439011",
            achievement_id="test_achievement",
            badge_name="Epic Badge",
            badge_description="An epic badge",
            rarity=Badge.EPIC
        )

        self.assertEqual(epic_badge.get_rarity_display(), "Epic")
        self.assertEqual(epic_badge.get_rarity_priority(), 3)
        self.assertEqual(epic_badge.get_rarity_color(), "#9933CC")

    def test_badge_visibility_toggle(self):
        """Test badge visibility toggle"""
        badge = Badge(
            user_id="507f1f77bcf86cd799439011",
            achievement_id="test_achievement",
            badge_name="Test Badge",
            badge_description="A test badge",
            rarity=Badge.COMMON
        )

        self.assertTrue(badge.is_visible)

        badge.toggle_visibility()
        self.assertFalse(badge.is_visible)

        badge.set_visibility(True)
        self.assertTrue(badge.is_visible)


class TestAchievementRepository(unittest.TestCase):
    """Test cases for AchievementRepository"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_db = Mock()
        self.mock_collection = Mock()
        self.mock_user_achievements_collection = Mock()
        self.mock_user_badges_collection = Mock()

        # Mock the database collections
        self.mock_db.__getitem__.side_effect = lambda key: {
            'achievements': self.mock_collection,
            'user_achievements': self.mock_user_achievements_collection,
            'user_badges': self.mock_user_badges_collection
        }[key]

    @patch('app.social.achievements.repositories.achievement_repository.get_db')
    def test_create_achievement(self, mock_get_db):
        """Test creating an achievement in repository"""
        mock_get_db.return_value = self.mock_db
        self.mock_collection.insert_one.return_value.inserted_id = ObjectId()

        repo = AchievementRepository()
        achievement = Achievement(
            achievement_id="test_achievement",
            name="Test Achievement",
            description="A test achievement",
            category=Achievement.GAMING,
            trigger_conditions={
                "type": Achievement.GAME_SESSION,
                "target_value": 1
            }
        )

        result = repo.create_achievement(achievement)
        self.assertIsInstance(result, str)
        self.mock_collection.insert_one.assert_called_once()

    @patch('app.social.achievements.repositories.achievement_repository.get_db')
    def test_find_achievement_by_id(self, mock_get_db):
        """Test finding achievement by ID"""
        mock_get_db.return_value = self.mock_db

        # Mock achievement data
        achievement_data = {
            '_id': ObjectId(),
            'achievement_id': 'test_achievement',
            'name': 'Test Achievement',
            'description': 'A test achievement',
            'category': Achievement.GAMING,
            'trigger_conditions': {
                'type': Achievement.GAME_SESSION,
                'target_value': 1
            },
            'badge_rarity': Achievement.COMMON,
            'reward_credits': 10,
            'is_active': True,
            'created_at': datetime.utcnow()
        }

        self.mock_collection.find_one.return_value = achievement_data

        repo = AchievementRepository()
        achievement = repo.find_achievement_by_id("test_achievement")

        self.assertIsNotNone(achievement)
        self.assertEqual(achievement.achievement_id, "test_achievement")
        self.mock_collection.find_one.assert_called_once_with({"achievement_id": "test_achievement"})

    @patch('app.social.achievements.repositories.achievement_repository.get_db')
    def test_find_active_achievements(self, mock_get_db):
        """Test finding active achievements"""
        mock_get_db.return_value = self.mock_db
        self.mock_collection.find.return_value.sort.return_value = []

        repo = AchievementRepository()
        achievements = repo.find_active_achievements()

        self.assertIsInstance(achievements, list)
        self.mock_collection.find.assert_called_once_with({"is_active": True})


class TestAchievementEngine(unittest.TestCase):
    """Test cases for AchievementEngine"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_repo = Mock(spec=AchievementRepository)

    @patch('app.social.achievements.services.achievement_engine.AchievementRepository')
    def test_check_triggers_game_session(self, mock_repo_class):
        """Test checking triggers for game session events"""
        mock_repo_class.return_value = self.mock_repo

        # Mock active achievements
        achievement = Achievement(
            achievement_id="rookie_player",
            name="Rookie Player",
            description="Complete first game session",
            category=Achievement.GAMING,
            trigger_conditions={
                "type": Achievement.GAME_SESSION,
                "target_value": 1
            }
        )

        self.mock_repo.find_active_achievements.return_value = [achievement]
        self.mock_repo.find_user_achievement.return_value = None
        self.mock_repo.create_user_achievement.return_value = "user_achievement_id"

        engine = AchievementEngine()

        with patch('flask.current_app') as mock_app:
            mock_app.logger = Mock()

            success, message, unlocked_achievements = engine.check_triggers(
                "507f1f77bcf86cd799439011",
                Achievement.GAME_SESSION,
                {"game_id": "test_game", "score": 100}
            )

            self.assertTrue(success)
            self.assertIsInstance(unlocked_achievements, list)

    @patch('app.social.achievements.services.achievement_engine.AchievementRepository')
    def test_update_progress(self, mock_repo_class):
        """Test updating achievement progress"""
        mock_repo_class.return_value = self.mock_repo

        # Mock achievement and user achievement
        achievement = Achievement(
            achievement_id="test_achievement",
            name="Test Achievement",
            description="A test achievement",
            category=Achievement.GAMING,
            trigger_conditions={
                "type": Achievement.GAME_SESSION,
                "target_value": 5
            }
        )

        user_achievement = UserAchievement(
            user_id="507f1f77bcf86cd799439011",
            achievement_id="test_achievement",
            progress=3,
            max_progress=5
        )

        self.mock_repo.find_achievement_by_id.return_value = achievement
        self.mock_repo.find_user_achievement.return_value = user_achievement
        self.mock_repo.update_user_achievement.return_value = True

        engine = AchievementEngine()

        with patch('flask.current_app') as mock_app:
            mock_app.logger = Mock()

            success, message, result_data = engine.update_progress(
                "507f1f77bcf86cd799439011",
                "test_achievement",
                1
            )

            self.assertTrue(success)
            self.assertIn("Progress updated", message)
            self.assertIsInstance(result_data, dict)

    @patch('app.social.achievements.services.achievement_engine.AchievementRepository')
    def test_calculate_impact_score(self, mock_repo_class):
        """Test calculating user impact score"""
        mock_repo_class.return_value = self.mock_repo

        # Mock completed user achievements
        user_achievements = [
            UserAchievement(
                user_id="507f1f77bcf86cd799439011",
                achievement_id="first_donation",
                progress=1,
                max_progress=1,
                is_completed=True
            )
        ]

        achievement = Achievement(
            achievement_id="first_donation",
            name="First Donation",
            description="Make first donation",
            category=Achievement.IMPACT,
            trigger_conditions={
                "type": Achievement.DONATION_COUNT,
                "target_value": 1
            },
            reward_credits=15
        )

        self.mock_repo.find_user_achievements.return_value = user_achievements
        self.mock_repo.find_achievement_by_id.return_value = achievement

        engine = AchievementEngine()

        with patch('flask.current_app') as mock_app:
            mock_app.logger = Mock()

            success, message, impact_score = engine.calculate_impact_score(
                "507f1f77bcf86cd799439011"
            )

            self.assertTrue(success)
            self.assertGreater(impact_score, 0)


class TestProgressTracker(unittest.TestCase):
    """Test cases for ProgressTracker"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_engine = Mock(spec=AchievementEngine)
        self.mock_repo = Mock(spec=AchievementRepository)

    @patch('app.social.achievements.services.progress_tracker.AchievementEngine')
    @patch('app.social.achievements.services.progress_tracker.AchievementRepository')
    def test_track_game_session_completion(self, mock_repo_class, mock_engine_class):
        """Test tracking game session completion"""
        mock_engine_class.return_value = self.mock_engine
        mock_repo_class.return_value = self.mock_repo

        self.mock_engine.check_triggers.return_value = (True, "Success", [])

        tracker = ProgressTracker()

        with patch('flask.current_app') as mock_app:
            mock_app.logger = Mock()

            success, message, unlocked_achievements = tracker.track_game_session_completion(
                "507f1f77bcf86cd799439011",
                {"game_id": "test_game", "score": 100}
            )

            self.assertTrue(success)
            self.assertIsInstance(unlocked_achievements, list)

    @patch('app.social.achievements.services.progress_tracker.AchievementEngine')
    @patch('app.social.achievements.services.progress_tracker.AchievementRepository')
    def test_track_social_activity(self, mock_repo_class, mock_engine_class):
        """Test tracking social activity"""
        mock_engine_class.return_value = self.mock_engine
        mock_repo_class.return_value = self.mock_repo

        self.mock_engine.check_triggers.return_value = (True, "Success", [])

        tracker = ProgressTracker()

        with patch('flask.current_app') as mock_app:
            mock_app.logger = Mock()

            success, message, unlocked_achievements = tracker.track_social_activity(
                "507f1f77bcf86cd799439011",
                "friend_added",
                {"friend_id": "507f1f77bcf86cd799439012"}
            )

            self.assertTrue(success)
            self.assertIsInstance(unlocked_achievements, list)

    @patch('app.social.achievements.services.progress_tracker.AchievementEngine')
    @patch('app.social.achievements.services.progress_tracker.AchievementRepository')
    def test_track_donation_activity(self, mock_repo_class, mock_engine_class):
        """Test tracking donation activity"""
        mock_engine_class.return_value = self.mock_engine
        mock_repo_class.return_value = self.mock_repo

        self.mock_engine.check_triggers.return_value = (True, "Success", [])

        tracker = ProgressTracker()

        with patch('flask.current_app') as mock_app:
            mock_app.logger = Mock()

            success, message, unlocked_achievements = tracker.track_donation_activity(
                "507f1f77bcf86cd799439011",
                {"amount": 25.0, "onlus_id": "507f1f77bcf86cd799439013"}
            )

            self.assertTrue(success)
            self.assertIsInstance(unlocked_achievements, list)


class TestBadgeService(unittest.TestCase):
    """Test cases for BadgeService"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_repo = Mock(spec=AchievementRepository)

    @patch('app.social.achievements.services.badge_service.AchievementRepository')
    def test_get_user_badges(self, mock_repo_class):
        """Test getting user badges"""
        mock_repo_class.return_value = self.mock_repo

        badges = [
            Badge(
                user_id="507f1f77bcf86cd799439011",
                achievement_id="test_achievement",
                badge_name="Test Badge",
                badge_description="A test badge",
                rarity=Badge.COMMON
            )
        ]

        self.mock_repo.find_user_badges.return_value = badges

        service = BadgeService()

        with patch('flask.current_app') as mock_app:
            mock_app.logger = Mock()

            success, message, badges_data = service.get_user_badges(
                "507f1f77bcf86cd799439011"
            )

            self.assertTrue(success)
            self.assertIsInstance(badges_data, list)
            self.assertEqual(len(badges_data), 1)

    @patch('app.social.achievements.services.badge_service.AchievementRepository')
    def test_get_user_badge_collection(self, mock_repo_class):
        """Test getting comprehensive badge collection"""
        mock_repo_class.return_value = self.mock_repo

        badges = [
            Badge(
                user_id="507f1f77bcf86cd799439011",
                achievement_id="test_achievement",
                badge_name="Test Badge",
                badge_description="A test badge",
                rarity=Badge.COMMON
            )
        ]

        badge_counts = {
            Badge.COMMON: 1,
            Badge.RARE: 0,
            Badge.EPIC: 0,
            Badge.LEGENDARY: 0
        }

        self.mock_repo.find_user_badges.return_value = badges
        self.mock_repo.count_user_badges_by_rarity.return_value = badge_counts

        service = BadgeService()

        with patch('flask.current_app') as mock_app:
            mock_app.logger = Mock()

            success, message, collection_data = service.get_user_badge_collection(
                "507f1f77bcf86cd799439011"
            )

            self.assertTrue(success)
            self.assertIsInstance(collection_data, dict)
            self.assertIn('total_badges', collection_data)
            self.assertIn('badges_by_rarity', collection_data)
            self.assertIn('badge_counts', collection_data)


if __name__ == '__main__':
    unittest.main()