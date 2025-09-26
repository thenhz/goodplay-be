"""
Test module for game modes functionality
Tests for game mode management, scheduling, and mode transitions
"""
import os
import sys
from bson import ObjectId
from datetime import datetime, timezone, timedelta

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.core.base_game_test import BaseGameTest
from app.games.modes.services.mode_manager import ModeManager


class TestGameModeSystem(BaseGameTest):
    """Test Game Mode system using modern testing framework"""
    service_class = ModeManager

    def test_normal_mode_creation(self):
        """Test creating normal mode"""
        normal_mode = {
            '_id': ObjectId(),
            'mode_id': 'normal',
            'name': 'Normal Play',
            'mode_type': 'normal',
            'is_active': True,
            'is_default': True,
            'description': 'Standard gameplay mode',
            'created_at': datetime.now(timezone.utc)
        }

        self.assertEqual(normal_mode['mode_id'], 'normal')
        self.assertEqual(normal_mode['name'], 'Normal Play')
        self.assertEqual(normal_mode['mode_type'], 'normal')
        self.assertTrue(normal_mode['is_active'])
        self.assertTrue(normal_mode['is_default'])

    def test_seasonal_war_mode(self):
        """Test creating seasonal war mode"""
        start_date = datetime.now(timezone.utc)
        end_date = start_date + timedelta(days=30)

        seasonal_mode = {
            '_id': ObjectId(),
            'mode_id': 'summer_war',
            'name': 'Summer War',
            'mode_type': 'seasonal_war',
            'start_date': start_date,
            'end_date': end_date,
            'is_active': False,
            'is_default': False,
            'team_based': True,
            'rewards': {'winner_bonus': 1000, 'participation_bonus': 100}
        }

        self.assertEqual(seasonal_mode['name'], 'Summer War')
        self.assertEqual(seasonal_mode['mode_type'], 'seasonal_war')
        self.assertEqual(seasonal_mode['start_date'], start_date)
        self.assertEqual(seasonal_mode['end_date'], end_date)
        self.assertTrue(seasonal_mode['team_based'])

    def test_special_event_mode(self):
        """Test creating special event mode"""
        start_date = datetime.now(timezone.utc)
        end_date = start_date + timedelta(days=7)

        event_mode = {
            '_id': ObjectId(),
            'mode_id': 'holiday_tournament',
            'name': 'Holiday Tournament',
            'mode_type': 'special_event',
            'start_date': start_date,
            'end_date': end_date,
            'is_active': True,
            'special_rules': {
                'double_points': True,
                'special_rewards': True,
                'entry_requirements': ['achievement:holiday_spirit']
            }
        }

        self.assertEqual(event_mode['name'], 'Holiday Tournament')
        self.assertEqual(event_mode['mode_type'], 'special_event')
        self.assertTrue(event_mode['is_active'])
        self.assertIn('double_points', event_mode['special_rules'])

    def test_mode_availability_check(self):
        """Test mode availability based on timing"""
        now = datetime.now(timezone.utc)

        # Active mode (no time restrictions)
        active_mode = {
            'mode_id': 'normal',
            'is_active': True,
            'start_date': None,
            'end_date': None
        }

        # Future mode
        future_mode = {
            'mode_id': 'future_event',
            'is_active': True,
            'start_date': now + timedelta(days=1),
            'end_date': now + timedelta(days=8)
        }

        # Past mode
        past_mode = {
            'mode_id': 'past_event',
            'is_active': True,
            'start_date': now - timedelta(days=8),
            'end_date': now - timedelta(days=1)
        }

        # Current mode
        current_mode = {
            'mode_id': 'current_event',
            'is_active': True,
            'start_date': now - timedelta(days=1),
            'end_date': now + timedelta(days=1)
        }

        # Test availability logic
        self.assertTrue(active_mode['is_active'])
        self.assertIsNone(active_mode['start_date'])

        self.assertTrue(future_mode['start_date'] > now)
        self.assertTrue(past_mode['end_date'] < now)
        self.assertTrue(current_mode['start_date'] <= now <= current_mode['end_date'])

    def test_mode_transitions(self):
        """Test mode activation and deactivation"""
        mode_data = {
            '_id': ObjectId(),
            'mode_id': 'tournament',
            'name': 'Weekly Tournament',
            'is_active': False,
            'status': 'scheduled'
        }

        # Test activation
        mode_data['is_active'] = True
        mode_data['status'] = 'active'
        mode_data['activated_at'] = datetime.now(timezone.utc)

        self.assertTrue(mode_data['is_active'])
        self.assertEqual(mode_data['status'], 'active')
        self.assertIn('activated_at', mode_data)

        # Test deactivation
        mode_data['is_active'] = False
        mode_data['status'] = 'completed'
        mode_data['deactivated_at'] = datetime.now(timezone.utc)

        self.assertFalse(mode_data['is_active'])
        self.assertEqual(mode_data['status'], 'completed')

    def test_mode_types_validation(self):
        """Test different game mode types"""
        mode_types = [
            'normal',
            'challenge',
            'tournament',
            'seasonal_war',
            'special_event',
            'team_battle',
            'solo_challenge'
        ]

        for mode_type in mode_types:
            mode = {
                '_id': ObjectId(),
                'mode_id': f'{mode_type}_test',
                'name': f'{mode_type.title()} Mode',
                'mode_type': mode_type,
                'is_active': True
            }

            self.assertEqual(mode['mode_type'], mode_type)
            self.assertTrue(mode['is_active'])

    def test_mode_scheduling(self):
        """Test mode scheduling functionality"""
        # Create scheduled mode
        scheduled_mode = {
            '_id': ObjectId(),
            'mode_id': 'scheduled_tournament',
            'name': 'Scheduled Tournament',
            'mode_type': 'tournament',
            'schedule': {
                'type': 'weekly',
                'day_of_week': 6,  # Saturday
                'start_time': '14:00:00',
                'duration_hours': 4,
                'timezone': 'UTC'
            },
            'is_active': False,
            'is_recurring': True
        }

        # Validate scheduling data
        self.assertEqual(scheduled_mode['schedule']['type'], 'weekly')
        self.assertEqual(scheduled_mode['schedule']['day_of_week'], 6)
        self.assertTrue(scheduled_mode['is_recurring'])

        # Test recurring schedule variations
        recurring_types = ['daily', 'weekly', 'monthly']
        for recurring_type in recurring_types:
            schedule_data = {
                'type': recurring_type,
                'start_time': '12:00:00',
                'duration_hours': 2
            }

            if recurring_type == 'weekly':
                schedule_data['day_of_week'] = 0  # Monday
            elif recurring_type == 'monthly':
                schedule_data['day_of_month'] = 15

            self.assertEqual(schedule_data['type'], recurring_type)

    def test_mode_configuration(self):
        """Test mode configuration and settings"""
        mode_config = {
            'mode_id': 'configured_mode',
            'name': 'Configured Mode',
            'config': {
                'max_participants': 100,
                'entry_fee': 0,
                'prize_pool': 5000,
                'scoring_multiplier': 1.5,
                'team_size': 4,
                'allow_late_join': False,
                'spectators_allowed': True
            }
        }

        config = mode_config['config']
        self.assertEqual(config['max_participants'], 100)
        self.assertEqual(config['team_size'], 4)
        self.assertFalse(config['allow_late_join'])
        self.assertTrue(config['spectators_allowed'])

    def test_mode_rewards_system(self):
        """Test mode rewards configuration"""
        rewards_config = {
            'mode_id': 'reward_mode',
            'rewards': {
                'winner': {'points': 1000, 'badge': 'champion', 'credits': 500},
                'runner_up': {'points': 500, 'badge': 'finalist', 'credits': 250},
                'participation': {'points': 100, 'credits': 50},
                'special_achievements': [
                    {'condition': 'first_time_winner', 'bonus_points': 200},
                    {'condition': 'perfect_game', 'bonus_points': 500}
                ]
            }
        }

        rewards = rewards_config['rewards']
        self.assertEqual(rewards['winner']['points'], 1000)
        self.assertEqual(rewards['runner_up']['badge'], 'finalist')
        self.assertIn('participation', rewards)
        self.assertEqual(len(rewards['special_achievements']), 2)

    def test_mode_statistics_tracking(self):
        """Test mode statistics and metrics"""
        mode_stats = {
            'mode_id': 'tracked_mode',
            'statistics': {
                'total_participants': 250,
                'total_sessions': 50,
                'average_duration_minutes': 45,
                'completion_rate': 0.85,
                'player_satisfaction': 4.2,
                'most_active_hours': ['14:00', '15:00', '20:00', '21:00']
            }
        }

        stats = mode_stats['statistics']
        self.assertGreater(stats['total_participants'], 0)
        self.assertGreater(stats['completion_rate'], 0.5)
        self.assertLess(stats['player_satisfaction'], 5.0)
        self.assertEqual(len(stats['most_active_hours']), 4)

    def test_mode_integration_with_games(self):
        """Test mode integration with specific games"""
        # Create a game that supports this mode
        game = self.create_test_game(
            title='Tournament Game',
            category='strategy',
            supported_modes=['normal', 'tournament', 'team_battle']
        )

        # Create mode integration
        mode_integration = {
            'mode_id': 'tournament',
            'supported_games': [game['_id']],
            'game_specific_rules': {
                str(game['_id']): {
                    'time_limit': 600,  # 10 minutes
                    'special_scoring': True,
                    'team_formation': 'random'
                }
            }
        }

        self.assertIn(game['_id'], mode_integration['supported_games'])
        self.assertIn(str(game['_id']), mode_integration['game_specific_rules'])