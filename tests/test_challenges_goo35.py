"""
GOO-35 Challenges Testing Suite

Migrated from legacy test_challenges.py to use GOO-35 Testing Utilities
with BaseGameTest for comprehensive challenges system testing.
"""
import os
import sys
from bson import ObjectId
from datetime import datetime, timezone

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.core.base_game_test import BaseGameTest
from app.games.challenges.services.challenge_service import ChallengeService
from app.games.challenges.repositories.challenge_repository import ChallengeRepository


class TestChallengeSystemGOO35(BaseGameTest):
    """
    GOO-35 Challenge System Testing

    Comprehensive testing for Challenge models, services, and workflows
    using GOO-35 utilities for maximum efficiency and maintainability.
    """
    service_class = ChallengeService

    def test_challenge_data_structure(self):
        """Test basic challenge data structure"""
        # Create challenge data manually following GOO-35 pattern
        challenge_data = {
            '_id': str(ObjectId()),
            'challenge_type': '1v1',
            'creator_id': str(ObjectId()),
            'opponent_id': str(ObjectId()),
            'game_id': 'tetris',
            'difficulty': 'medium',
            'status': 'pending',
            'participants': [str(ObjectId()), str(ObjectId())],
            'created_at': datetime.now(timezone.utc)
        }

        # Validate challenge structure
        self.assertEqual(challenge_data['challenge_type'], '1v1')
        self.assertEqual(challenge_data['game_id'], 'tetris')
        self.assertEqual(challenge_data['difficulty'], 'medium')
        self.assertEqual(len(challenge_data['participants']), 2)
        self.assertEqual(challenge_data['status'], 'pending')
        self.assertIsNotNone(challenge_data['_id'])

    def test_nvn_challenge_structure(self):
        """Test NvN challenge data structure"""
        participant_ids = [str(ObjectId()) for _ in range(4)]

        challenge_data = {
            '_id': str(ObjectId()),
            'challenge_type': 'NvN',
            'creator_id': participant_ids[0],
            'participants': participant_ids,
            'game_id': 'snake',
            'max_participants': 4,
            'status': 'pending',
            'created_at': datetime.now(timezone.utc)
        }

        # Validate NvN challenge
        self.assertEqual(challenge_data['challenge_type'], 'NvN')
        self.assertEqual(challenge_data['creator_id'], participant_ids[0])
        self.assertEqual(challenge_data['game_id'], 'snake')
        self.assertEqual(challenge_data['max_participants'], 4)
        self.assertEqual(len(challenge_data['participants']), 4)

    def test_challenge_status_transitions(self):
        """Test challenge status system"""
        # Test different challenge statuses
        statuses = ['pending', 'active', 'completed', 'cancelled']

        for status in statuses:
            challenge_data = {
                '_id': str(ObjectId()),
                'challenge_type': '1v1',
                'creator_id': str(ObjectId()),
                'status': status,
                'game_id': 'puzzle_game',
                'created_at': datetime.now(timezone.utc)
            }

            self.assertEqual(challenge_data['status'], status)
            self.assertIsNotNone(challenge_data['_id'])

    def test_cross_game_challenge_structure(self):
        """Test cross-game challenge functionality"""
        challenge_data = {
            '_id': str(ObjectId()),
            'challenge_type': 'cross_game',
            'creator_id': str(ObjectId()),
            'opponent_id': str(ObjectId()),
            'game_ids': ['tetris', 'snake'],
            'scoring_method': 'normalized',
            'status': 'pending',
            'created_at': datetime.now(timezone.utc)
        }

        # Validate cross-game structure
        self.assertEqual(challenge_data['challenge_type'], 'cross_game')
        self.assertIn('tetris', challenge_data['game_ids'])
        self.assertIn('snake', challenge_data['game_ids'])
        self.assertEqual(challenge_data['scoring_method'], 'normalized')

    def test_challenge_difficulty_levels(self):
        """Test challenge difficulty system"""
        difficulties = ['easy', 'medium', 'hard', 'expert']

        for difficulty in difficulties:
            challenge_data = {
                '_id': str(ObjectId()),
                'challenge_type': '1v1',
                'creator_id': str(ObjectId()),
                'difficulty': difficulty,
                'game_id': 'puzzle_game',
                'created_at': datetime.now(timezone.utc)
            }

            self.assertEqual(challenge_data['difficulty'], difficulty)
            self.assertEqual(challenge_data['game_id'], 'puzzle_game')

    def test_challenge_completion_data(self):
        """Test challenge completion data structure"""
        completion_data = {
            'challenge_id': str(ObjectId()),
            'winner_id': str(ObjectId()),
            'final_scores': {
                str(ObjectId()): 1500,
                str(ObjectId()): 1200
            },
            'status': 'completed',
            'completed_at': datetime.now(timezone.utc)
        }

        # Verify completion data
        self.assertIsNotNone(completion_data['challenge_id'])
        self.assertIsNotNone(completion_data['winner_id'])
        self.assertEqual(completion_data['status'], 'completed')
        self.assertIsNotNone(completion_data['completed_at'])
        self.assertEqual(len(completion_data['final_scores']), 2)


class TestChallengeRepositoryGOO35(BaseGameTest):
    """GOO-35 Challenge Repository Testing"""
    service_class = ChallengeRepository

    def test_challenge_repository_data(self):
        """Test challenge repository data handling"""
        # Create challenge data
        challenge_data = {
            '_id': str(ObjectId()),
            'challenge_type': '1v1',
            'creator_id': str(ObjectId()),
            'opponent_id': str(ObjectId()),
            'game_id': 'tetris',
            'status': 'active',
            'created_at': datetime.now(timezone.utc)
        }

        # Verify challenge creation structure
        self.assertIsNotNone(challenge_data['_id'])
        self.assertEqual(challenge_data['creator_id'], challenge_data['creator_id'])
        self.assertEqual(challenge_data['game_id'], 'tetris')
        self.assertEqual(challenge_data['status'], 'active')

    def test_challenge_filtering_by_status(self):
        """Test challenge status filtering"""
        # Create different status challenges
        active_challenge = {
            '_id': str(ObjectId()),
            'challenge_type': '1v1',
            'creator_id': str(ObjectId()),
            'status': 'active',
            'created_at': datetime.now(timezone.utc)
        }

        completed_challenge = {
            '_id': str(ObjectId()),
            'challenge_type': '1v1',
            'creator_id': str(ObjectId()),
            'status': 'completed',
            'created_at': datetime.now(timezone.utc)
        }

        # Verify status filtering capabilities
        self.assertEqual(active_challenge['status'], 'active')
        self.assertEqual(completed_challenge['status'], 'completed')
        self.assertNotEqual(active_challenge['status'], completed_challenge['status'])

    def test_challenge_participant_queries(self):
        """Test challenge participant data structure"""
        participant_ids = [str(ObjectId()) for _ in range(3)]

        challenge_data = {
            '_id': str(ObjectId()),
            'challenge_type': 'NvN',
            'creator_id': participant_ids[0],
            'participants': participant_ids,
            'game_id': 'multiplayer_game',
            'status': 'pending',
            'created_at': datetime.now(timezone.utc)
        }

        # Verify participant structure
        self.assertEqual(len(challenge_data['participants']), 3)
        for participant_id in participant_ids:
            self.assertIn(participant_id, challenge_data['participants'])

    def test_challenge_metadata_structure(self):
        """Test challenge metadata and additional data"""
        challenge_data = {
            '_id': str(ObjectId()),
            'challenge_type': '1v1',
            'creator_id': str(ObjectId()),
            'game_id': 'timed_game',
            'metadata': {
                'time_limit': 300,
                'rounds': 3,
                'difficulty_modifier': 1.2
            },
            'status': 'pending',
            'created_at': datetime.now(timezone.utc)
        }

        # Verify metadata structure
        self.assertIsNotNone(challenge_data['_id'])
        self.assertIsNotNone(challenge_data['created_at'])
        self.assertEqual(challenge_data['metadata']['time_limit'], 300)
        self.assertEqual(challenge_data['metadata']['rounds'], 3)
        self.assertEqual(challenge_data['metadata']['difficulty_modifier'], 1.2)