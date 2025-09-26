"""
Test suite for Social Impact Score & Leaderboards system (GOO-12)

This module tests all components of the leaderboard system including:
- Impact score calculation and management
- Leaderboard creation and ranking
- Privacy controls and settings
- Real-time updates and integration hooks
- Repository operations and data access
"""

import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone, timedelta
from bson import ObjectId

# Import system under test
from app.social.leaderboards.models.impact_score import ImpactScore
from app.social.leaderboards.models.leaderboard import Leaderboard
from app.social.leaderboards.models.leaderboard_entry import LeaderboardEntry
from app.social.leaderboards.repositories.impact_score_repository import ImpactScoreRepository
from app.social.leaderboards.repositories.leaderboard_repository import LeaderboardRepository
from app.social.leaderboards.services.impact_calculator import ImpactCalculator
from app.social.leaderboards.services.leaderboard_service import LeaderboardService
from app.social.leaderboards.services.ranking_engine import RankingEngine
from app.social.leaderboards.services.privacy_service import PrivacyService
from app.social.leaderboards.integration.event_handlers import (
    handle_game_session_complete,
    handle_social_activity,
    handle_donation_activity,
    handle_achievement_unlock
)


class TestImpactScoreModel(unittest.TestCase):
    """Test ImpactScore model functionality"""

    def setUp(self):
        self.user_id = str(ObjectId())
        self.sample_gaming_details = {
            'play_time_score': 200.0,
            'game_variety_score': 150.0,
            'tournament_score': 100.0,
            'achievement_score': 120.0,
            'consistency_multiplier': 1.1
        }

    def test_impact_score_creation(self):
        """Test basic impact score creation"""
        impact_score = ImpactScore(
            user_id=self.user_id,
            gaming_component=300.0,
            social_component=150.0,
            donation_component=500.0
        )

        self.assertEqual(impact_score.gaming_component, 300.0)
        self.assertEqual(impact_score.social_component, 150.0)
        self.assertEqual(impact_score.donation_component, 500.0)
        self.assertIsInstance(impact_score._id, ObjectId)

    def test_impact_score_calculation(self):
        """Test total impact score calculation"""
        impact_score = ImpactScore(
            user_id=self.user_id,
            gaming_component=600.0,  # 600 * 0.3 = 180
            social_component=400.0,  # 400 * 0.2 = 80
            donation_component=1000.0  # 1000 * 0.5 = 500
        )

        total = impact_score.calculate_total_score()
        expected = (600 * 0.3) + (400 * 0.2) + (1000 * 0.5)  # 760.0

        self.assertEqual(total, 760.0)
        self.assertEqual(impact_score.impact_score, 760.0)

    def test_component_update(self):
        """Test updating individual components"""
        impact_score = ImpactScore(user_id=self.user_id)

        impact_score.update_component('gaming', 400.0, self.sample_gaming_details)

        self.assertEqual(impact_score.gaming_component, 400.0)
        self.assertEqual(impact_score.gaming_details, self.sample_gaming_details)

    def test_score_validation(self):
        """Test score validation limits"""
        with self.assertRaises(ValueError):
            ImpactScore(user_id=self.user_id, gaming_component=-100.0)

        with self.assertRaises(ValueError):
            ImpactScore(user_id=self.user_id, gaming_component=2000.0)  # Exceeds MAX_GAMING_SCORE

    def test_score_trend_calculation(self):
        """Test score trend analysis"""
        impact_score = ImpactScore(user_id=self.user_id)

        # Add some history
        impact_score.add_history_entry(100.0)
        impact_score.add_history_entry(150.0)
        impact_score.add_history_entry(200.0)

        trend = impact_score.get_score_trend(days=7)

        self.assertEqual(trend['trend'], 'increasing')
        self.assertGreater(trend['change'], 0)

    def test_to_response_dict(self):
        """Test response dictionary conversion"""
        impact_score = ImpactScore(
            user_id=self.user_id,
            gaming_component=300.0,
            social_component=200.0,
            donation_component=500.0
        )

        response = impact_score.to_response_dict()

        self.assertIn('components', response)
        self.assertIn('gaming', response['components'])
        self.assertIn('social', response['components'])
        self.assertIn('donation', response['components'])
        self.assertIn('rankings', response)
        self.assertIn('trend', response)


class TestLeaderboardModel(unittest.TestCase):
    """Test Leaderboard model functionality"""

    def setUp(self):
        self.user_id = str(ObjectId())

    def test_leaderboard_creation(self):
        """Test basic leaderboard creation"""
        leaderboard = Leaderboard(
            leaderboard_type=Leaderboard.GLOBAL_IMPACT,
            period=Leaderboard.ALL_TIME
        )

        self.assertEqual(leaderboard.leaderboard_type, Leaderboard.GLOBAL_IMPACT)
        self.assertEqual(leaderboard.period, Leaderboard.ALL_TIME)
        self.assertEqual(len(leaderboard.entries), 0)

    def test_leaderboard_entry_management(self):
        """Test adding and managing leaderboard entries"""
        leaderboard = Leaderboard(
            leaderboard_type=Leaderboard.GLOBAL_IMPACT,
            period=Leaderboard.ALL_TIME
        )

        entry = LeaderboardEntry(
            user_id=self.user_id,
            score=500.0,
            rank=1,
            display_name="Test User"
        )

        result = leaderboard.add_entry(entry)
        self.assertTrue(result)
        self.assertEqual(len(leaderboard.entries), 1)

    def test_leaderboard_sorting(self):
        """Test automatic sorting of leaderboard entries"""
        leaderboard = Leaderboard(
            leaderboard_type=Leaderboard.GLOBAL_IMPACT,
            period=Leaderboard.ALL_TIME
        )

        # Add entries in random order
        entry1 = LeaderboardEntry(str(ObjectId()), 300.0, 1, "User 1")
        entry2 = LeaderboardEntry(str(ObjectId()), 500.0, 1, "User 2")
        entry3 = LeaderboardEntry(str(ObjectId()), 100.0, 1, "User 3")

        leaderboard.add_entry(entry1)
        leaderboard.add_entry(entry2)
        leaderboard.add_entry(entry3)

        # Check that entries are sorted by score (descending)
        self.assertEqual(leaderboard.entries[0].score, 500.0)  # Highest score first
        self.assertEqual(leaderboard.entries[1].score, 300.0)
        self.assertEqual(leaderboard.entries[2].score, 100.0)

        # Check that ranks are updated correctly
        self.assertEqual(leaderboard.entries[0].rank, 1)
        self.assertEqual(leaderboard.entries[1].rank, 2)
        self.assertEqual(leaderboard.entries[2].rank, 3)

    def test_leaderboard_pagination(self):
        """Test paginated entry retrieval"""
        leaderboard = Leaderboard(
            leaderboard_type=Leaderboard.GLOBAL_IMPACT,
            period=Leaderboard.ALL_TIME
        )

        # Add 25 entries
        for i in range(25):
            entry = LeaderboardEntry(str(ObjectId()), float(i * 10), 1, f"User {i}")
            leaderboard.add_entry(entry)

        # Test pagination
        page_1 = leaderboard.get_entries_paginated(page=1, per_page=10)
        page_2 = leaderboard.get_entries_paginated(page=2, per_page=10)

        self.assertEqual(len(page_1), 10)
        self.assertEqual(len(page_2), 10)

    def test_user_rank_retrieval(self):
        """Test getting user's rank from leaderboard"""
        leaderboard = Leaderboard(
            leaderboard_type=Leaderboard.GLOBAL_IMPACT,
            period=Leaderboard.ALL_TIME
        )

        test_user_id = str(ObjectId())
        entry = LeaderboardEntry(test_user_id, 300.0, 1, "Test User")
        leaderboard.add_entry(entry)

        rank = leaderboard.get_user_rank(test_user_id)
        self.assertEqual(rank, 1)

        percentile = leaderboard.get_user_percentile(test_user_id)
        self.assertEqual(percentile, 100.0)  # Only user, so 100th percentile

    def test_leaderboard_validation(self):
        """Test leaderboard validation"""
        with self.assertRaises(ValueError):
            Leaderboard("invalid_type", Leaderboard.ALL_TIME)

        with self.assertRaises(ValueError):
            Leaderboard(Leaderboard.GLOBAL_IMPACT, "invalid_period")


class TestLeaderboardEntry(unittest.TestCase):
    """Test LeaderboardEntry model functionality"""

    def test_entry_creation(self):
        """Test basic entry creation"""
        user_id = str(ObjectId())
        entry = LeaderboardEntry(
            user_id=user_id,
            score=500.0,
            rank=1,
            display_name="Test User"
        )

        self.assertEqual(entry.score, 500.0)
        self.assertEqual(entry.rank, 1)
        self.assertEqual(entry.display_name, "Test User")

    def test_entry_validation(self):
        """Test entry validation"""
        user_id = str(ObjectId())

        with self.assertRaises(ValueError):
            LeaderboardEntry(user_id, -100.0, 1, "User")  # Negative score

        with self.assertRaises(ValueError):
            LeaderboardEntry(user_id, 100.0, 0, "User")  # Invalid rank

        with self.assertRaises(ValueError):
            LeaderboardEntry(user_id, 100.0, 1, "")  # Empty display name

    def test_rank_suffix(self):
        """Test rank suffix generation"""
        user_id = str(ObjectId())

        entry1 = LeaderboardEntry(user_id, 100.0, 1, "User")
        self.assertEqual(entry1.get_rank_suffix(), "1st")

        entry2 = LeaderboardEntry(user_id, 100.0, 2, "User")
        self.assertEqual(entry2.get_rank_suffix(), "2nd")

        entry3 = LeaderboardEntry(user_id, 100.0, 3, "User")
        self.assertEqual(entry3.get_rank_suffix(), "3rd")

        entry4 = LeaderboardEntry(user_id, 100.0, 11, "User")
        self.assertEqual(entry4.get_rank_suffix(), "11th")

    def test_top_performer_check(self):
        """Test top performer identification"""
        user_id = str(ObjectId())

        entry1 = LeaderboardEntry(user_id, 100.0, 5, "User")
        self.assertTrue(entry1.is_top_performer(threshold=10))
        self.assertFalse(entry1.is_top_performer(threshold=3))


class TestImpactScoreRepository(unittest.TestCase):
    """Test ImpactScoreRepository data access"""

    def setUp(self):
        self.repo = ImpactScoreRepository()
        self.repo.collection = Mock()  # Mock MongoDB collection

    def test_find_by_user_id(self):
        """Test finding impact score by user ID"""
        user_id = str(ObjectId())
        mock_data = {
            '_id': ObjectId(),
            'user_id': ObjectId(user_id),
            'impact_score': 500.0,
            'gaming_component': 300.0,
            'social_component': 100.0,
            'donation_component': 400.0
        }

        self.repo.collection.find_one.return_value = mock_data

        result = self.repo.find_by_user_id(user_id)

        self.assertIsInstance(result, ImpactScore)
        self.assertEqual(result.impact_score, 500.0)
        self.repo.collection.find_one.assert_called_once()

    def test_create_impact_score(self):
        """Test creating new impact score"""
        user_id = str(ObjectId())
        impact_score = ImpactScore(user_id=user_id, impact_score=500.0)

        mock_result = Mock()
        mock_result.inserted_id = ObjectId()
        self.repo.collection.insert_one.return_value = mock_result

        result = self.repo.create_impact_score(impact_score)

        self.assertIsInstance(result, str)
        self.repo.collection.insert_one.assert_called_once()

    def test_update_rankings(self):
        """Test updating global rankings"""
        # Mock aggregation pipeline results
        mock_global_result = [{
            '_id': None,
            'users': [
                {'user_id': ObjectId(), 'impact_score': 500.0},
                {'user_id': ObjectId(), 'impact_score': 300.0}
            ]
        }]

        self.repo.collection.aggregate.return_value = mock_global_result
        self.repo.collection.update_one.return_value = Mock(modified_count=1)

        result = self.repo.update_rankings()

        self.assertEqual(result, 2)  # Two users updated
        self.assertTrue(self.repo.collection.aggregate.called)


class TestImpactCalculator(unittest.TestCase):
    """Test ImpactCalculator service"""

    def setUp(self):
        self.calculator = ImpactCalculator()

        # Mock dependencies
        self.calculator.impact_score_repo = Mock()
        self.calculator.user_repo = Mock()
        self.calculator.game_session_repo = Mock()
        self.calculator.relationship_repo = Mock()

    @patch('app.social.leaderboards.services.impact_calculator.current_app')
    def test_calculate_user_impact_score_new_user(self, mock_app):
        """Test calculating impact score for new user"""
        user_id = str(ObjectId())

        # Mock user exists
        self.calculator.user_repo.find_by_id.return_value = {
            '_id': ObjectId(user_id),
            'gaming_stats': {'total_play_time': 1000},
            'wallet_credits': {'total_donated': 50.0}
        }

        # Mock no existing score
        self.calculator.impact_score_repo.find_by_user_id.return_value = None

        # Mock score creation
        self.calculator.impact_score_repo.create_impact_score.return_value = str(ObjectId())

        # Mock gaming sessions
        self.calculator.game_session_repo.find_user_sessions_by_date_range.return_value = [
            {'play_duration_ms': 60000, 'created_at': datetime.now(timezone.utc)}
        ]

        # Mock relationships
        self.calculator.relationship_repo.get_user_relationships.return_value = []

        success, message, impact_score = self.calculator.calculate_user_impact_score(user_id)

        self.assertTrue(success)
        self.assertIsInstance(impact_score, ImpactScore)
        self.assertGreater(impact_score.impact_score, 0)

    @patch('app.social.leaderboards.services.impact_calculator.current_app')
    def test_calculate_user_impact_score_existing_user(self, mock_app):
        """Test calculating impact score for existing user"""
        user_id = str(ObjectId())

        # Mock existing score (not stale)
        existing_score = ImpactScore(user_id=user_id, impact_score=400.0)
        existing_score.last_calculated = datetime.now(timezone.utc)
        self.calculator.impact_score_repo.find_by_user_id.return_value = existing_score

        success, message, impact_score = self.calculator.calculate_user_impact_score(user_id)

        self.assertTrue(success)
        self.assertEqual(impact_score.impact_score, 400.0)

    def test_gaming_component_calculation(self):
        """Test gaming component calculation"""
        user_id = str(ObjectId())

        # Mock gaming sessions
        mock_sessions = [
            {
                'play_duration_ms': 120000,  # 2 minutes
                'created_at': datetime.now(timezone.utc),
                'game_id': 'game1'
            },
            {
                'play_duration_ms': 180000,  # 3 minutes
                'created_at': datetime.now(timezone.utc),
                'game_id': 'game2'
            }
        ]

        self.calculator.game_session_repo.find_user_sessions_by_date_range.return_value = mock_sessions

        # Mock user data
        self.calculator.user_repo.find_by_id.return_value = {
            'gaming_stats': {'games_played': 10}
        }

        score, details = self.calculator._calculate_gaming_component(user_id)

        self.assertGreater(score, 0)
        self.assertIn('play_time_score', details)
        self.assertIn('game_variety_score', details)

    def test_social_component_calculation(self):
        """Test social component calculation"""
        user_id = str(ObjectId())

        # Mock relationships
        mock_relationships = [Mock() for _ in range(5)]  # 5 friends
        self.calculator.relationship_repo.get_user_relationships.return_value = mock_relationships

        score, details = self.calculator._calculate_social_component(user_id)

        self.assertGreater(score, 0)
        self.assertIn('friends_score', details)

    def test_donation_component_calculation(self):
        """Test donation component calculation"""
        user_id = str(ObjectId())

        total_donated = 100.0

        score, details = self.calculator._calculate_donation_component(user_id)

        self.assertGreaterEqual(score, 0)
        self.assertIn('amount_score', details)


class TestLeaderboardService(unittest.TestCase):
    """Test LeaderboardService"""

    def setUp(self):
        self.service = LeaderboardService()

        # Mock dependencies
        self.service.leaderboard_repo = Mock()
        self.service.impact_score_repo = Mock()
        self.service.user_repo = Mock()
        self.service.relationship_repo = Mock()

    @patch('app.social.leaderboards.services.leaderboard_service.current_app')
    def test_get_leaderboard_existing(self, mock_app):
        """Test getting existing leaderboard"""
        # Mock existing leaderboard
        mock_leaderboard = Leaderboard(Leaderboard.GLOBAL_IMPACT, Leaderboard.ALL_TIME)
        mock_leaderboard.last_updated = datetime.now(timezone.utc)  # Not stale

        self.service.leaderboard_repo.find_by_type_and_period.return_value = mock_leaderboard

        success, message, data = self.service.get_leaderboard(
            Leaderboard.GLOBAL_IMPACT,
            Leaderboard.ALL_TIME
        )

        self.assertTrue(success)
        self.assertIn('leaderboard_type', data)

    @patch('app.social.leaderboards.services.leaderboard_service.current_app')
    def test_get_friends_leaderboard(self, mock_app):
        """Test getting friends leaderboard"""
        user_id = str(ObjectId())

        # Mock friendships
        mock_friendships = [Mock(target_user_id=ObjectId()) for _ in range(3)]
        self.service.relationship_repo.get_user_relationships.return_value = mock_friendships

        # Mock friends rankings
        mock_rankings = [
            {
                'user_id': ObjectId(user_id),
                'impact_score': 500.0,
                'user_profile': [{'first_name': 'Test User'}]
            }
        ]
        self.service.impact_score_repo.get_friends_rankings.return_value = mock_rankings

        success, message, data = self.service.get_friends_leaderboard(user_id)

        self.assertTrue(success)
        self.assertEqual(data['leaderboard_type'], 'friends_circle')

    def test_update_user_privacy_settings(self):
        """Test updating user privacy settings"""
        user_id = str(ObjectId())

        # Mock user
        mock_user = {
            '_id': ObjectId(user_id),
            'preferences': {'privacy': {'leaderboard_participation': True}}
        }
        self.service.user_repo.find_by_id.return_value = mock_user
        self.service.user_repo.update_by_id.return_value = True

        success, message = self.service.update_user_privacy_settings(user_id, False)

        self.assertTrue(success)
        self.service.user_repo.update_by_id.assert_called_once()


class TestRankingEngine(unittest.TestCase):
    """Test RankingEngine functionality"""

    def setUp(self):
        self.engine = RankingEngine()

        # Mock dependencies
        self.engine.impact_score_repo = Mock()
        self.engine.leaderboard_repo = Mock()
        self.engine.impact_calculator = Mock()
        self.engine.leaderboard_service = Mock()

    @patch('app.social.leaderboards.services.ranking_engine.current_app')
    def test_trigger_user_score_update(self, mock_app):
        """Test triggering user score update"""
        user_id = str(ObjectId())

        # Mock successful impact calculation
        mock_impact_score = ImpactScore(user_id=user_id, impact_score=500.0)
        self.engine.impact_calculator.calculate_user_impact_score.return_value = (
            True, "Success", mock_impact_score
        )

        success, message = self.engine.trigger_user_score_update(user_id, 'gaming')

        self.assertTrue(success)
        self.engine.impact_calculator.calculate_user_impact_score.assert_called_once()

    @patch('app.social.leaderboards.services.ranking_engine.current_app')
    def test_run_scheduled_updates(self, mock_app):
        """Test running scheduled updates"""
        # Mock ranking updates
        self.engine.impact_score_repo.update_rankings.return_value = 50

        # Mock stale leaderboards
        self.engine.leaderboard_repo.get_stale_leaderboards.return_value = [
            {'leaderboard_type': 'global_impact', 'period': 'all_time'}
        ]

        # Mock leaderboard finding and updating
        mock_leaderboard = Leaderboard('global_impact', 'all_time')
        self.engine.leaderboard_repo.find_by_type_and_period.return_value = mock_leaderboard
        self.engine.leaderboard_service._update_leaderboard_data.return_value = True

        success, message, stats = self.engine.run_scheduled_updates()

        self.assertTrue(success)
        self.assertIn('ranking_updates', stats)
        self.assertIn('leaderboard_updates', stats)

    def test_get_ranking_health_status(self):
        """Test getting ranking system health"""
        # Mock score statistics
        self.engine.impact_score_repo.get_score_statistics.return_value = {
            'total_users': 100
        }

        # Mock leaderboard summary
        self.engine.leaderboard_repo.get_leaderboard_summary.return_value = {}

        # Mock stale data
        self.engine.impact_score_repo.get_stale_scores.return_value = ['user1', 'user2']
        self.engine.leaderboard_repo.get_stale_leaderboards.return_value = []

        health = self.engine.get_ranking_health_status()

        self.assertIn('status', health)
        self.assertIn('health_score', health)
        self.assertIn('metrics', health)


class TestPrivacyService(unittest.TestCase):
    """Test PrivacyService functionality"""

    def setUp(self):
        self.service = PrivacyService()

        # Mock dependencies
        self.service.user_repo = Mock()
        self.service.impact_score_repo = Mock()
        self.service.leaderboard_repo = Mock()

    @patch('app.social.leaderboards.services.privacy_service.current_app')
    def test_update_leaderboard_participation(self, mock_app):
        """Test updating leaderboard participation"""
        user_id = str(ObjectId())

        # Mock user
        mock_user = {
            '_id': ObjectId(user_id),
            'preferences': {'privacy': {'leaderboard_participation': True}}
        }
        self.service.user_repo.find_by_id.return_value = mock_user
        self.service.user_repo.update_by_id.return_value = True

        success, message, settings = self.service.update_leaderboard_participation(user_id, False)

        self.assertTrue(success)
        self.service.user_repo.update_by_id.assert_called_once()

    def test_get_anonymized_user_data(self):
        """Test getting anonymized user data"""
        user_id = str(ObjectId())
        requester_id = str(ObjectId())

        # Mock user
        mock_user = {
            '_id': ObjectId(user_id),
            'social_profile': {'display_name': 'Test User'},
            'preferences': {'privacy': {'impact_score_visibility': 'public'}}
        }
        self.service.user_repo.find_by_id.return_value = mock_user

        # Mock impact score
        mock_impact_score = ImpactScore(user_id=user_id, impact_score=500.0)
        self.service.impact_score_repo.find_by_user_id.return_value = mock_impact_score

        data = self.service.get_anonymized_user_data(user_id, requester_id)

        self.assertIn('user_id', data)
        self.assertIn('display_name', data)
        self.assertIn('is_anonymous', data)

    @patch('app.social.leaderboards.services.privacy_service.current_app')
    def test_export_user_leaderboard_data(self, mock_app):
        """Test exporting user data for GDPR"""
        user_id = str(ObjectId())

        # Mock impact score
        mock_impact_score = ImpactScore(user_id=user_id, impact_score=500.0)
        self.service.impact_score_repo.find_by_user_id.return_value = mock_impact_score

        # Mock leaderboard positions
        self.service.leaderboard_repo.get_user_leaderboard_positions.return_value = []

        # Mock user data
        mock_user = {
            'preferences': {'privacy': {'leaderboard_participation': True}}
        }
        self.service.user_repo.find_by_id.return_value = mock_user

        success, message, data = self.service.export_user_leaderboard_data(user_id)

        self.assertTrue(success)
        self.assertIn('impact_score_data', data)
        self.assertIn('leaderboard_positions', data)
        self.assertIn('privacy_settings', data)


class TestEventHandlers(unittest.TestCase):
    """Test integration event handlers"""

    @patch('app.social.leaderboards.integration.event_handlers.ranking_engine')
    @patch('app.social.leaderboards.integration.event_handlers.current_app')
    def test_handle_game_session_complete(self, mock_app, mock_engine):
        """Test handling game session completion"""
        user_id = str(ObjectId())
        session_data = {
            'session_id': str(ObjectId()),
            'game_id': 'test_game',
            'play_duration_ms': 120000,
            'final_score': 1500
        }

        # Mock successful score update
        mock_engine.trigger_user_score_update.return_value = (True, "Success")

        result = handle_game_session_complete(user_id, session_data)

        self.assertTrue(result)
        mock_engine.trigger_user_score_update.assert_called_once_with(
            user_id, 'gaming', unittest.mock.ANY
        )

    @patch('app.social.leaderboards.integration.event_handlers.ranking_engine')
    @patch('app.social.leaderboards.integration.event_handlers.current_app')
    def test_handle_social_activity(self, mock_app, mock_engine):
        """Test handling social activity"""
        user_id = str(ObjectId())
        activity_data = {'target_user_id': str(ObjectId())}

        # Mock successful score update
        mock_engine.trigger_user_score_update.return_value = (True, "Success")

        result = handle_social_activity(user_id, 'friend_request_accepted', activity_data)

        self.assertTrue(result)
        mock_engine.trigger_user_score_update.assert_called_once()

    @patch('app.social.leaderboards.integration.event_handlers.ranking_engine')
    @patch('app.social.leaderboards.integration.event_handlers.current_app')
    def test_handle_donation_activity(self, mock_app, mock_engine):
        """Test handling donation activity"""
        user_id = str(ObjectId())
        donation_data = {
            'amount': 50.0,
            'onlus_id': str(ObjectId()),
            'transaction_type': 'regular'
        }

        # Mock successful score update
        mock_engine.trigger_user_score_update.return_value = (True, "Success")

        result = handle_donation_activity(user_id, donation_data)

        self.assertTrue(result)
        mock_engine.trigger_user_score_update.assert_called_once()

    @patch('app.social.leaderboards.integration.event_handlers.ranking_engine')
    @patch('app.social.leaderboards.integration.event_handlers.current_app')
    def test_handle_achievement_unlock(self, mock_app, mock_engine):
        """Test handling achievement unlock"""
        user_id = str(ObjectId())
        achievement_data = {
            'achievement_id': 'test_achievement',
            'category': 'gaming',
            'badge_rarity': 'rare'
        }

        # Mock successful score update
        mock_engine.trigger_user_score_update.return_value = (True, "Success")

        result = handle_achievement_unlock(user_id, achievement_data)

        self.assertTrue(result)
        mock_engine.trigger_user_score_update.assert_called_once()


if __name__ == '__main__':
    unittest.main()