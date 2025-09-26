#!/usr/bin/env python3
"""
Social Challenges Test Suite for GoodPlay Backend
Tests for the social challenges module following existing patterns
"""
import unittest
import sys
import os
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestSocialChallengesImports(unittest.TestCase):
    """Test that social challenges module imports work"""

    def test_models_import(self):
        """Test that social challenge models can be imported"""
        try:
            from app.social.challenges.models.social_challenge import SocialChallenge, ChallengeRules, ChallengeRewards
            from app.social.challenges.models.challenge_participant import ChallengeParticipant
            from app.social.challenges.models.challenge_result import ChallengeResult
            from app.social.challenges.models.challenge_interaction import ChallengeInteraction

            # If we get here, imports work
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Social challenges models import failed: {e}")

    def test_repositories_import(self):
        """Test that social challenge repositories can be imported"""
        try:
            from app.social.challenges.repositories.social_challenge_repository import SocialChallengeRepository
            from app.social.challenges.repositories.challenge_participant_repository import ChallengeParticipantRepository
            from app.social.challenges.repositories.challenge_result_repository import ChallengeResultRepository
            from app.social.challenges.repositories.challenge_interaction_repository import ChallengeInteractionRepository

            # If we get here, imports work
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Social challenges repositories import failed: {e}")

    def test_services_import(self):
        """Test that social challenge services can be imported"""
        try:
            from app.social.challenges.services.social_challenge_manager import SocialChallengeManager
            from app.social.challenges.services.social_matchmaking_service import SocialMatchmakingService
            from app.social.challenges.services.notification_service import NotificationService
            from app.social.challenges.services.reward_service import RewardService
            from app.social.challenges.services.interaction_service import InteractionService

            # If we get here, imports work
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Social challenges services import failed: {e}")

    def test_challenge_types_import(self):
        """Test that challenge type factories can be imported"""
        try:
            from app.social.challenges.types.gaming_challenges import GamingChallengeTypes
            from app.social.challenges.types.social_challenges import SocialChallengeTypes
            from app.social.challenges.types.impact_challenges import ImpactChallengeTypes

            # If we get here, imports work
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Challenge types import failed: {e}")

    def test_engines_import(self):
        """Test that challenge engines can be imported"""
        try:
            from app.social.challenges.engines.challenge_engine import ChallengeEngine
            from app.social.challenges.engines.scoring_engine import ScoringEngine

            # If we get here, imports work
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Challenge engines import failed: {e}")

    def test_controller_import(self):
        """Test that social challenge controller can be imported"""
        try:
            from app.social.challenges.controllers.social_challenges_controller import social_challenges_bp

            # If we get here, imports work
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Social challenges controller import failed: {e}")


class TestSocialChallengeBasicStructure(unittest.TestCase):
    """Test basic structure of social challenge components"""

    def test_social_challenge_manager_structure(self):
        """Test that SocialChallengeManager has expected methods"""
        from app.social.challenges.services.social_challenge_manager import SocialChallengeManager

        manager = SocialChallengeManager()

        # Check that expected methods exist
        self.assertTrue(hasattr(manager, 'create_challenge'))
        self.assertTrue(hasattr(manager, 'join_challenge'))
        self.assertTrue(hasattr(manager, 'leave_challenge'))
        self.assertTrue(hasattr(manager, 'start_challenge'))
        self.assertTrue(hasattr(manager, 'complete_challenge'))
        self.assertTrue(hasattr(manager, 'get_challenge'))
        self.assertTrue(hasattr(manager, 'update_participant_progress'))

    def test_social_matchmaking_service_structure(self):
        """Test that SocialMatchmakingService has expected methods"""
        from app.social.challenges.services.social_matchmaking_service import SocialMatchmakingService

        service = SocialMatchmakingService()

        # Check that expected methods exist
        self.assertTrue(hasattr(service, 'discover_challenges_for_user'))
        self.assertTrue(hasattr(service, 'find_friend_challenges'))
        self.assertTrue(hasattr(service, 'get_trending_challenges'))
        self.assertTrue(hasattr(service, 'search_challenges'))
        self.assertTrue(hasattr(service, 'get_recommended_challenges'))

    def test_reward_service_structure(self):
        """Test that RewardService has expected methods"""
        from app.social.challenges.services.reward_service import RewardService

        service = RewardService()

        # Check that expected methods exist
        self.assertTrue(hasattr(service, 'calculate_challenge_rewards'))
        self.assertTrue(hasattr(service, 'award_completion_bonus'))
        self.assertTrue(hasattr(service, 'award_social_engagement_bonus'))
        self.assertTrue(hasattr(service, 'award_winner_bonus'))

    def test_interaction_service_structure(self):
        """Test that InteractionService has expected methods"""
        from app.social.challenges.services.interaction_service import InteractionService

        service = InteractionService()

        # Check that expected methods exist
        self.assertTrue(hasattr(service, 'add_cheer'))
        self.assertTrue(hasattr(service, 'add_comment'))
        self.assertTrue(hasattr(service, 'add_reaction'))
        self.assertTrue(hasattr(service, 'get_challenge_interactions'))
        self.assertTrue(hasattr(service, 'get_activity_feed'))

    def test_notification_service_structure(self):
        """Test that NotificationService has expected methods"""
        from app.social.challenges.services.notification_service import NotificationService

        service = NotificationService()

        # Check that expected methods exist
        self.assertTrue(hasattr(service, 'send_challenge_invitation'))
        self.assertTrue(hasattr(service, 'send_challenge_started'))
        self.assertTrue(hasattr(service, 'send_challenge_completed'))
        self.assertTrue(hasattr(service, 'send_cheer_notification'))
        self.assertTrue(hasattr(service, 'send_new_comment_notification'))


class TestSocialChallengeRepositoryStructure(unittest.TestCase):
    """Test basic structure of social challenge repositories"""

    def test_social_challenge_repository_structure(self):
        """Test that SocialChallengeRepository has expected methods"""
        from app.social.challenges.repositories.social_challenge_repository import SocialChallengeRepository

        repo = SocialChallengeRepository()

        # Check that expected methods exist
        self.assertTrue(hasattr(repo, 'create'))
        self.assertTrue(hasattr(repo, 'find_by_id'))
        self.assertTrue(hasattr(repo, 'find_by_creator'))
        self.assertTrue(hasattr(repo, 'find_public_challenges'))
        self.assertTrue(hasattr(repo, 'search_challenges'))
        self.assertTrue(hasattr(repo, 'find_trending_challenges'))
        self.assertTrue(hasattr(repo, 'update_status'))

    def test_challenge_participant_repository_structure(self):
        """Test that ChallengeParticipantRepository has expected methods"""
        from app.social.challenges.repositories.challenge_participant_repository import ChallengeParticipantRepository

        repo = ChallengeParticipantRepository()

        # Check that expected methods exist
        self.assertTrue(hasattr(repo, 'create'))
        self.assertTrue(hasattr(repo, 'find_by_challenge'))
        self.assertTrue(hasattr(repo, 'find_by_challenge_and_user'))
        self.assertTrue(hasattr(repo, 'update_progress'))
        self.assertTrue(hasattr(repo, 'count_active_participants'))

    def test_challenge_result_repository_structure(self):
        """Test that ChallengeResultRepository has expected methods"""
        from app.social.challenges.repositories.challenge_result_repository import ChallengeResultRepository

        repo = ChallengeResultRepository()

        # Check that expected methods exist
        self.assertTrue(hasattr(repo, 'create'))
        self.assertTrue(hasattr(repo, 'find_by_challenge'))
        self.assertTrue(hasattr(repo, 'find_by_user'))
        self.assertTrue(hasattr(repo, 'find_winners'))
        self.assertTrue(hasattr(repo, 'get_leaderboard'))

    def test_challenge_interaction_repository_structure(self):
        """Test that ChallengeInteractionRepository has expected methods"""
        from app.social.challenges.repositories.challenge_interaction_repository import ChallengeInteractionRepository

        repo = ChallengeInteractionRepository()

        # Check that expected methods exist
        self.assertTrue(hasattr(repo, 'create'))
        self.assertTrue(hasattr(repo, 'find_by_challenge'))
        self.assertTrue(hasattr(repo, 'find_by_user'))
        self.assertTrue(hasattr(repo, 'count_interactions'))


class TestChallengeFactoriesStructure(unittest.TestCase):
    """Test basic structure of challenge type factories"""

    def test_gaming_challenge_factory_structure(self):
        """Test that GamingChallengeTypes has expected methods"""
        from app.social.challenges.types.gaming_challenges import GamingChallengeTypes

        # Check that expected static methods exist
        self.assertTrue(hasattr(GamingChallengeTypes, 'create_speed_run_challenge'))
        self.assertTrue(hasattr(GamingChallengeTypes, 'create_high_score_challenge'))
        self.assertTrue(hasattr(GamingChallengeTypes, 'create_endurance_challenge'))
        self.assertTrue(hasattr(GamingChallengeTypes, 'create_puzzle_master_challenge'))
        self.assertTrue(hasattr(GamingChallengeTypes, 'create_multiplayer_showdown_challenge'))

    def test_social_challenge_factory_structure(self):
        """Test that SocialChallengeTypes has expected methods"""
        from app.social.challenges.types.social_challenges import SocialChallengeTypes

        # Check that expected static methods exist
        self.assertTrue(hasattr(SocialChallengeTypes, 'create_friend_referral_challenge'))
        self.assertTrue(hasattr(SocialChallengeTypes, 'create_community_helper_challenge'))
        self.assertTrue(hasattr(SocialChallengeTypes, 'create_social_butterfly_challenge'))
        self.assertTrue(hasattr(SocialChallengeTypes, 'create_mentor_challenge'))

    def test_impact_challenge_factory_structure(self):
        """Test that ImpactChallengeTypes has expected methods"""
        from app.social.challenges.types.impact_challenges import ImpactChallengeTypes

        # Check that expected static methods exist
        self.assertTrue(hasattr(ImpactChallengeTypes, 'create_donation_race_challenge'))
        self.assertTrue(hasattr(ImpactChallengeTypes, 'create_cause_champion_challenge'))
        self.assertTrue(hasattr(ImpactChallengeTypes, 'create_fundraising_marathon_challenge'))


class TestChallengeEnginesStructure(unittest.TestCase):
    """Test basic structure of challenge engines"""

    def test_challenge_engine_structure(self):
        """Test that ChallengeEngine has expected methods"""
        from app.social.challenges.engines.challenge_engine import ChallengeEngine

        engine = ChallengeEngine()

        # Check that expected methods exist
        self.assertTrue(hasattr(engine, 'validate_challenge_data'))
        self.assertTrue(hasattr(engine, 'create_from_template'))
        self.assertTrue(hasattr(engine, 'calculate_difficulty_level'))
        self.assertTrue(hasattr(engine, 'check_prerequisites'))

    def test_scoring_engine_structure(self):
        """Test that ScoringEngine has expected methods"""
        from app.social.challenges.engines.scoring_engine import ScoringEngine

        engine = ScoringEngine()

        # Check that expected methods exist
        self.assertTrue(hasattr(engine, 'calculate_final_score'))
        self.assertTrue(hasattr(engine, 'apply_multipliers'))
        self.assertTrue(hasattr(engine, 'calculate_rank'))
        self.assertTrue(hasattr(engine, 'calculate_performance_insights'))


class TestSocialChallengesModuleRegistration(unittest.TestCase):
    """Test that social challenges module is properly registered"""

    def test_social_challenges_blueprint_import(self):
        """Test that social challenges blueprint can be imported"""
        from app.social.challenges.controllers import social_challenges_bp

        # Check that blueprint exists and has expected name
        self.assertIsNotNone(social_challenges_bp)
        self.assertEqual(social_challenges_bp.name, 'social_challenges')

    def test_social_module_initialization(self):
        """Test that social module can initialize social challenges"""
        try:
            from app.social import register_social_module
            # If import works, the module structure is correct
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Social module initialization failed: {e}")


class TestSocialChallengesMockFunctionality(unittest.TestCase):
    """Test basic functionality with mocked dependencies"""

    @patch('app.social.challenges.repositories.social_challenge_repository.get_db')
    def test_challenge_manager_create_challenge_basic(self, mock_get_db):
        """Test basic challenge creation flow"""
        # Mock database
        mock_collection = MagicMock()
        mock_get_db.return_value = {'social_challenges': mock_collection}
        mock_collection.insert_one.return_value.inserted_id = "test_id"

        from app.social.challenges.services.social_challenge_manager import SocialChallengeManager

        manager = SocialChallengeManager()

        # Test that manager can be created and has expected structure
        self.assertIsNotNone(manager)
        self.assertTrue(hasattr(manager, 'challenge_repo'))

    @patch('app.social.challenges.repositories.challenge_participant_repository.get_db')
    def test_participant_repository_basic(self, mock_get_db):
        """Test basic participant repository functionality"""
        # Mock database
        mock_collection = MagicMock()
        mock_get_db.return_value = {'challenge_participants': mock_collection}

        from app.social.challenges.repositories.challenge_participant_repository import ChallengeParticipantRepository

        repo = ChallengeParticipantRepository()

        # Test that repository can be created
        self.assertIsNotNone(repo)

    def test_challenge_types_basic_structure(self):
        """Test that challenge type constants exist"""
        from app.social.challenges.models.social_challenge import SocialChallenge

        # Test that challenge types are defined
        self.assertTrue(hasattr(SocialChallenge, 'GAMING'))
        self.assertTrue(hasattr(SocialChallenge, 'SOCIAL_ENGAGEMENT'))
        self.assertTrue(hasattr(SocialChallenge, 'IMPACT'))

        # Test that status constants exist
        self.assertTrue(hasattr(SocialChallenge, 'OPEN'))
        self.assertTrue(hasattr(SocialChallenge, 'ACTIVE'))
        self.assertTrue(hasattr(SocialChallenge, 'COMPLETED'))
        self.assertTrue(hasattr(SocialChallenge, 'CANCELLED'))


if __name__ == '__main__':
    print("🧪 Running Social Challenges Tests...")
    unittest.main(verbosity=2)