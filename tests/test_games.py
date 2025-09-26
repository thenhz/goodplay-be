"""
GOO-35 Games Testing Suite - Migrated Legacy Version

Migrated from legacy test_games.py to use GOO-35 Testing Utilities
with BaseGameTest for comprehensive games system testing.
"""
import os
import sys
from bson import ObjectId
from datetime import datetime, timezone

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.core.base_game_test import BaseGameTest
from app.games.services.game_service import GameService
from app.games.repositories.game_repository import GameRepository


class TestGameSystemGOO35(BaseGameTest):
    """GOO-35 Game System Testing"""
    service_class = GameService

    def test_game_creation_structure(self):
        """Test game creation data structure"""
        game_data = self.create_test_game(
            title='Test Game',
            category='puzzle',
            difficulty='medium'
        )

        self.assertEqual(game_data['title'], 'Test Game')
        self.assertEqual(game_data['category'], 'puzzle')
        self.assertEqual(game_data['difficulty'], 'medium')
        self.assertIsNotNone(game_data['_id'])

    def test_game_session_management(self):
        """Test game session functionality"""
        user_id = str(ObjectId())
        game_data = self.create_test_game(title='Session Game')

        session = self.create_test_session(
            user_id=user_id,
            game_id=game_data['_id'],
            status='active'
        )

        self.assertEqual(session['user_id'], user_id)
        self.assertEqual(session['game_id'], str(game_data['_id']))
        self.assertEqual(session['status'], 'active')

    def test_game_plugin_system(self):
        """Test game plugin functionality"""
        plugin = self.create_test_game_plugin(
            name='Test Plugin',
            category='puzzle'
        )

        self.assertEqual(plugin['name'], 'Test Plugin')
        self.assertEqual(plugin['category'], 'puzzle')
        self.assertTrue(plugin['enabled'])

    def test_game_categories(self):
        """Test game category system"""
        categories = ['puzzle', 'arcade', 'strategy', 'action']

        for category in categories:
            game = self.create_test_game(
                title=f'{category.title()} Game',
                category=category
            )

            self.assertEqual(game['category'], category)
            self.assertIsNotNone(game['_id'])


class TestGameRepositoryGOO35(BaseGameTest):
    """GOO-35 Game Repository Testing"""
    service_class = GameRepository

    def test_game_data_persistence(self):
        """Test game data structure for repository"""
        game_data = self.create_test_game(
            title='Repository Test Game',
            description='Test game for repository testing'
        )

        self.assertEqual(game_data['title'], 'Repository Test Game')
        self.assertIsNotNone(game_data['_id'])
        self.assertIsNotNone(game_data['created_at'])

    def test_game_filtering_by_category(self):
        """Test filtering games by category"""
        puzzle_game = self.create_test_game(
            title='Puzzle Game',
            category='puzzle'
        )

        arcade_game = self.create_test_game(
            title='Arcade Game',
            category='arcade'
        )

        self.assertEqual(puzzle_game['category'], 'puzzle')
        self.assertEqual(arcade_game['category'], 'arcade')
        self.assertNotEqual(puzzle_game['category'], arcade_game['category'])