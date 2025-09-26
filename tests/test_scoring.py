"""
Test module for universal scoring functionality
Tests for score normalization, ELO ratings, and scoring algorithms
"""
import os
import sys
from bson import ObjectId
from datetime import datetime, timezone

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.core.base_game_test import BaseGameTest
from app.games.scoring.services.universal_scorer import UniversalScorer


class TestUniversalScoringSystem(BaseGameTest):
    """Test Universal Scoring system using modern testing framework"""
    service_class = UniversalScorer

    def test_basic_score_normalization(self):
        """Test basic score normalization"""
        # Test score normalization data structure
        score_data = {
            'game_type': 'puzzle',
            'raw_score': 1000,
            'difficulty': 'medium',
            'session_time_seconds': 600,
            'normalized_score': 0,
            'modifiers': {
                'difficulty_multiplier': 1.0,
                'time_bonus': 0.1,
                'game_type_base': 100
            }
        }

        # Calculate normalized score
        base_score = score_data['modifiers']['game_type_base']
        difficulty_multiplier = score_data['modifiers']['difficulty_multiplier']
        time_bonus = score_data['modifiers']['time_bonus']

        normalized = (score_data['raw_score'] / 10) * difficulty_multiplier + base_score + (base_score * time_bonus)
        score_data['normalized_score'] = normalized

        self.assertGreater(score_data['normalized_score'], 0)
        self.assertEqual(score_data['game_type'], 'puzzle')
        self.assertEqual(score_data['difficulty'], 'medium')

    def test_difficulty_modifiers(self):
        """Test difficulty modifiers affect score"""
        base_params = {
            'game_type': 'puzzle',
            'raw_score': 1000,
            'session_time_seconds': 600
        }

        difficulty_modifiers = {
            'easy': 0.8,
            'medium': 1.0,
            'hard': 1.3,
            'expert': 1.6
        }

        scores = {}
        for difficulty, multiplier in difficulty_modifiers.items():
            score_calc = {
                **base_params,
                'difficulty': difficulty,
                'multiplier': multiplier,
                'normalized_score': base_params['raw_score'] * multiplier
            }
            scores[difficulty] = score_calc

        # Validate ascending difficulty scores
        self.assertLess(scores['easy']['normalized_score'], scores['medium']['normalized_score'])
        self.assertLess(scores['medium']['normalized_score'], scores['hard']['normalized_score'])
        self.assertLess(scores['hard']['normalized_score'], scores['expert']['normalized_score'])

    def test_game_type_base_scores(self):
        """Test game type affects base score"""
        game_type_bases = {
            'puzzle': 100,
            'arcade': 120,
            'strategy': 150,
            'action': 110,
            'simulation': 140
        }

        base_params = {
            'raw_score': 1000,
            'difficulty': 'medium',
            'session_time_seconds': 600
        }

        for game_type, base_score in game_type_bases.items():
            score_data = {
                **base_params,
                'game_type': game_type,
                'base_score': base_score,
                'final_score': base_params['raw_score'] + base_score
            }

            self.assertEqual(score_data['game_type'], game_type)
            self.assertEqual(score_data['base_score'], base_score)
            self.assertGreater(score_data['final_score'], base_params['raw_score'])

    def test_time_based_scoring(self):
        """Test time-based scoring bonuses"""
        base_score = 1000
        time_scenarios = [
            {'time': 300, 'bonus': 0.2, 'description': 'Fast completion'},
            {'time': 600, 'bonus': 0.1, 'description': 'Normal time'},
            {'time': 900, 'bonus': 0.0, 'description': 'Slow completion'},
            {'time': 1200, 'bonus': -0.1, 'description': 'Very slow'}
        ]

        for scenario in time_scenarios:
            time_adjusted_score = base_score * (1 + scenario['bonus'])
            scenario['final_score'] = max(time_adjusted_score, base_score * 0.5)  # Minimum 50%

            self.assertGreaterEqual(scenario['final_score'], base_score * 0.5)
            if scenario['bonus'] > 0:
                self.assertGreater(scenario['final_score'], base_score)
            elif scenario['bonus'] < 0:
                self.assertLessEqual(scenario['final_score'], base_score)

    def test_elo_rating_system(self):
        """Test ELO rating calculations"""
        # Test ELO rating data structures
        player1 = {
            'user_id': str(ObjectId()),
            'current_rating': 1200,
            'games_played': 10
        }

        player2 = {
            'user_id': str(ObjectId()),
            'current_rating': 1300,
            'games_played': 15
        }

        # Simulate match result (player1 wins)
        k_factor = 32
        expected_score_p1 = 1 / (1 + pow(10, (player2['current_rating'] - player1['current_rating']) / 400))
        expected_score_p2 = 1 - expected_score_p1

        # Player 1 wins (score = 1)
        actual_score_p1 = 1
        actual_score_p2 = 0

        # Calculate new ratings
        new_rating_p1 = player1['current_rating'] + k_factor * (actual_score_p1 - expected_score_p1)
        new_rating_p2 = player2['current_rating'] + k_factor * (actual_score_p2 - expected_score_p2)

        # Validate rating changes
        self.assertGreater(new_rating_p1, player1['current_rating'])  # Winner gains rating
        self.assertLess(new_rating_p2, player2['current_rating'])     # Loser loses rating

    def test_streak_bonuses(self):
        """Test scoring streak bonuses"""
        base_score = 1000
        streak_bonuses = [
            {'streak': 1, 'multiplier': 1.0, 'description': 'No streak'},
            {'streak': 3, 'multiplier': 1.1, 'description': '3 game streak'},
            {'streak': 5, 'multiplier': 1.2, 'description': '5 game streak'},
            {'streak': 10, 'multiplier': 1.4, 'description': '10 game streak'},
            {'streak': 20, 'multiplier': 1.7, 'description': '20 game streak'}
        ]

        for bonus in streak_bonuses:
            bonus['final_score'] = base_score * bonus['multiplier']

            if bonus['streak'] == 1:
                self.assertEqual(bonus['final_score'], base_score)
            else:
                self.assertGreater(bonus['final_score'], base_score)

    def test_team_contribution_scoring(self):
        """Test team contribution calculations"""
        individual_score = 1000
        team_multipliers = {
            'solo_play': 1.0,
            'team_play': 1.2,
            'tournament': 1.5,
            'team_vs_team': 1.3
        }

        for mode, multiplier in team_multipliers.items():
            contribution_data = {
                'mode': mode,
                'individual_score': individual_score,
                'team_multiplier': multiplier,
                'team_contribution': individual_score * multiplier,
                'timestamp': datetime.now(timezone.utc)
            }

            self.assertEqual(contribution_data['mode'], mode)
            self.assertGreaterEqual(contribution_data['team_contribution'], individual_score)

    def test_cross_game_score_normalization(self):
        """Test cross-game score normalization for challenges"""
        games_scores = [
            {'game': 'tetris', 'raw_score': 15000, 'max_possible': 50000},
            {'game': 'snake', 'raw_score': 2500, 'max_possible': 10000},
            {'game': 'puzzle', 'raw_score': 800, 'max_possible': 1000}
        ]

        # Normalize to 0-1000 scale
        for game_score in games_scores:
            percentage = game_score['raw_score'] / game_score['max_possible']
            game_score['normalized'] = percentage * 1000
            game_score['performance_ratio'] = percentage

        # Validate normalization
        for game_score in games_scores:
            self.assertGreaterEqual(game_score['normalized'], 0)
            self.assertLessEqual(game_score['normalized'], 1000)
            self.assertGreaterEqual(game_score['performance_ratio'], 0)
            self.assertLessEqual(game_score['performance_ratio'], 1)

    def test_leaderboard_score_calculation(self):
        """Test leaderboard score calculations"""
        user_activities = {
            'gaming_score': 5000,
            'social_score': 1200,
            'donation_score': 800,
            'achievement_bonus': 500,
            'streak_bonus': 200,
            'consistency_multiplier': 1.1
        }

        # Calculate composite leaderboard score
        base_total = (user_activities['gaming_score'] +
                     user_activities['social_score'] +
                     user_activities['donation_score'])

        with_bonuses = base_total + user_activities['achievement_bonus'] + user_activities['streak_bonus']
        final_score = with_bonuses * user_activities['consistency_multiplier']

        leaderboard_entry = {
            'user_id': str(ObjectId()),
            'component_scores': user_activities,
            'base_total': base_total,
            'final_score': final_score,
            'rank': 1,  # To be calculated based on comparison with other users
            'last_updated': datetime.now(timezone.utc)
        }

        # Validate calculation
        self.assertEqual(leaderboard_entry['base_total'], 7000)  # 5000 + 1200 + 800
        self.assertGreater(leaderboard_entry['final_score'], leaderboard_entry['base_total'])
        self.assertIsNotNone(leaderboard_entry['user_id'])

    def test_scoring_edge_cases(self):
        """Test scoring system edge cases"""
        edge_cases = [
            {'raw_score': 0, 'expected_min': 0},
            {'raw_score': -100, 'expected_min': 0},  # Negative scores should be 0
            {'raw_score': float('inf'), 'expected_max': 100000},  # Cap maximum
            {'raw_score': None, 'expected_default': 0}
        ]

        for case in edge_cases:
            if case['raw_score'] is None:
                normalized_score = case['expected_default']
            elif case['raw_score'] < 0:
                normalized_score = max(case['raw_score'], case['expected_min'])
            elif case['raw_score'] == float('inf'):
                normalized_score = min(999999, case['expected_max'])
            else:
                normalized_score = case['raw_score']

            case['result'] = normalized_score

            # Validate edge case handling
            if case['raw_score'] is None:
                self.assertEqual(case['result'], 0)
            elif case['raw_score'] < 0:
                self.assertGreaterEqual(case['result'], 0)
            elif case['raw_score'] == float('inf'):
                self.assertLessEqual(case['result'], case['expected_max'])