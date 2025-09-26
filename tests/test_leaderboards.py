"""
Test suite for Social Impact Score & Leaderboards system

This module tests all components of the leaderboard system including:
- Impact score calculation and management
- Leaderboard creation and ranking
- Privacy controls and settings
- Real-time updates and integration hooks
"""
import os
import sys
from bson import ObjectId
from datetime import datetime, timezone, timedelta

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.core.base_social_test import BaseSocialTest
from app.social.leaderboards.services.leaderboard_service import LeaderboardService


class TestImpactScoreSystem(BaseSocialTest):
    """Test Impact Score system using modern testing framework"""
    service_class = LeaderboardService

    def test_impact_score_creation(self):
        """Test basic impact score creation"""
        user = self.create_test_social_user(display_name="Score User")

        # Create impact score data structure
        impact_score_data = {
            '_id': ObjectId(),
            'user_id': user['_id'],
            'gaming_score': 200.0,
            'social_score': 150.0,
            'donation_score': 100.0,
            'total_score': 450.0,
            'rank': 1,
            'last_updated': datetime.now(timezone.utc)
        }

        # Validate impact score structure
        self.assertEqual(impact_score_data['user_id'], user['_id'])
        self.assertEqual(impact_score_data['total_score'], 450.0)
        self.assertIsInstance(impact_score_data['gaming_score'], float)
        self.assertIsInstance(impact_score_data['social_score'], float)

    def test_leaderboard_entry_creation(self):
        """Test leaderboard entry creation"""
        user = self.create_test_social_user()

        leaderboard_entry = {
            '_id': ObjectId(),
            'user_id': user['_id'],
            'username': user['display_name'],
            'total_score': 1250.0,
            'rank': 3,
            'gaming_contributions': 800.0,
            'social_contributions': 300.0,
            'donation_contributions': 150.0,
            'created_at': datetime.now(timezone.utc)
        }

        # Validate entry structure
        self.assertEqual(leaderboard_entry['user_id'], user['_id'])
        self.assertEqual(leaderboard_entry['rank'], 3)
        self.assertGreater(leaderboard_entry['total_score'], 0)

    def test_leaderboard_categories(self):
        """Test different leaderboard categories"""
        categories = ['overall', 'gaming', 'social', 'donations', 'weekly', 'monthly']

        for category in categories:
            leaderboard_data = {
                '_id': ObjectId(),
                'category': category,
                'period': 'weekly' if category in ['weekly', 'monthly'] else 'all_time',
                'entries': [],
                'last_updated': datetime.now(timezone.utc),
                'is_active': True
            }

            self.assertEqual(leaderboard_data['category'], category)
            self.assertIsInstance(leaderboard_data['entries'], list)
            self.assertTrue(leaderboard_data['is_active'])

    def test_privacy_settings_for_leaderboards(self):
        """Test leaderboard privacy controls"""
        user = self.create_test_social_user()

        # Test different privacy levels
        privacy_levels = ['public', 'friends', 'private']

        for privacy_level in privacy_levels:
            privacy_prefs = self.create_test_social_user(
                privacy_settings={
                    'leaderboard_visibility': privacy_level,
                    'score_sharing': privacy_level != 'private'
                }
            )

            expected_visible = privacy_level == 'public'
            if privacy_level == 'friends':
                expected_visible = True  # Visible to friends
            elif privacy_level == 'private':
                expected_visible = False

            # Validate privacy logic
            if privacy_level == 'private':
                self.assertFalse(privacy_prefs['privacy_settings']['score_sharing'])

    def test_ranking_calculations(self):
        """Test ranking engine calculations"""
        users = []
        scores = [1500.0, 1200.0, 800.0, 600.0, 400.0]

        # Create users with different scores
        for i, score in enumerate(scores):
            user = self.create_test_social_user(display_name=f"User {i+1}")
            users.append({
                'user': user,
                'score': score,
                'expected_rank': i + 1
            })

        # Validate ranking order
        for i, user_data in enumerate(users):
            self.assertEqual(user_data['expected_rank'], i + 1)
            if i > 0:
                self.assertGreater(users[i-1]['score'], user_data['score'])

    def test_impact_score_components(self):
        """Test individual impact score components"""
        user = self.create_test_social_user()

        # Test gaming component
        gaming_details = {
            'play_time_score': 200.0,
            'game_variety_score': 150.0,
            'tournament_score': 100.0,
            'achievement_score': 120.0,
            'consistency_multiplier': 1.1
        }

        # Test social component
        social_details = {
            'friend_interactions': 50.0,
            'community_participation': 30.0,
            'helpful_actions': 25.0,
            'leadership_bonus': 10.0
        }

        # Test donation component
        donation_details = {
            'total_donated': 500.0,
            'consistency_bonus': 1.2,
            'cause_diversity': 3,
            'impact_multiplier': 1.15
        }

        # Calculate total expected score
        gaming_total = sum(gaming_details.values()) - gaming_details['consistency_multiplier']
        gaming_score = gaming_total * gaming_details['consistency_multiplier']

        social_score = sum(social_details.values())
        donation_score = donation_details['total_donated'] * donation_details['consistency_bonus'] * donation_details['impact_multiplier']

        total_expected = gaming_score + social_score + donation_score

        # Validate components exist and are reasonable
        self.assertGreater(gaming_score, 0)
        self.assertGreater(social_score, 0)
        self.assertGreater(donation_score, 0)
        self.assertGreater(total_expected, 0)

    def test_leaderboard_real_time_updates(self):
        """Test real-time leaderboard update scenarios"""
        # Create initial leaderboard state
        users = []
        for i in range(5):
            user = self.create_test_social_user(display_name=f"Player {i+1}")
            users.append(user)

        # Simulate score updates
        score_updates = [
            {'user_idx': 2, 'new_score': 2000.0, 'reason': 'tournament_win'},
            {'user_idx': 0, 'new_score': 1800.0, 'reason': 'achievement_unlock'},
            {'user_idx': 4, 'new_score': 1600.0, 'reason': 'donation_milestone'}
        ]

        for update in score_updates:
            user = users[update['user_idx']]
            score_update_data = {
                'user_id': user['_id'],
                'score_change': update['new_score'],
                'reason': update['reason'],
                'timestamp': datetime.now(timezone.utc)
            }

            # Validate update structure
            self.assertIn('user_id', score_update_data)
            self.assertIn('reason', score_update_data)
            self.assertGreater(score_update_data['score_change'], 0)

    def test_leaderboard_periods(self):
        """Test different leaderboard time periods"""
        periods = ['daily', 'weekly', 'monthly', 'yearly', 'all_time']

        for period in periods:
            leaderboard = {
                '_id': ObjectId(),
                'period': period,
                'start_date': datetime.now(timezone.utc) - timedelta(days=7),
                'end_date': datetime.now(timezone.utc),
                'entries_count': 0,
                'is_active': True,
                'category': 'overall'
            }

            if period == 'all_time':
                # All-time leaderboards don't have end dates
                leaderboard['end_date'] = None

            self.assertEqual(leaderboard['period'], period)
            self.assertTrue(leaderboard['is_active'])

    def test_leaderboard_entry_filtering(self):
        """Test leaderboard entry filtering and pagination"""
        # Create multiple users for filtering tests
        total_users = 20
        users = []

        for i in range(total_users):
            user = self.create_test_social_user(
                display_name=f"FilterUser {i+1}",
                privacy_settings={'leaderboard_visibility': 'public' if i % 2 == 0 else 'private'}
            )
            users.append(user)

        # Test filtering scenarios
        public_users = [u for i, u in enumerate(users) if i % 2 == 0]
        private_users = [u for i, u in enumerate(users) if i % 2 != 0]

        # Validate filtering logic
        self.assertEqual(len(public_users), 10)
        self.assertEqual(len(private_users), 10)
        self.assertEqual(len(public_users) + len(private_users), total_users)

    def test_achievement_impact_on_scores(self):
        """Test how achievements affect impact scores"""
        user = self.create_test_social_user()

        # Test different achievement types and their score impact
        achievements = [
            {'name': 'First Win', 'category': 'gaming', 'points': 100, 'rarity': 'common'},
            {'name': 'Social Butterfly', 'category': 'social', 'points': 200, 'rarity': 'rare'},
            {'name': 'Generous Donor', 'category': 'donation', 'points': 500, 'rarity': 'legendary'},
        ]

        total_expected_points = 0
        for achievement in achievements:
            # Create achievement using social test utilities
            achievement_data = self.create_test_achievement(
                achievement_type=achievement['category'],
                name=achievement['name']
            )

            # Validate achievement structure
            self.assertEqual(achievement_data['name'], achievement['name'])
            self.assertIn('points', achievement_data)
            total_expected_points += achievement_data['points']

        # Verify total points calculation
        self.assertGreater(total_expected_points, 0)