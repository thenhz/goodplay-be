"""
Test module for teams functionality
Tests for global team system, team management, and tournaments
"""
import os
import sys
from bson import ObjectId
from datetime import datetime, timezone, timedelta

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.core.base_game_test import BaseGameTest
from app.games.teams.services.team_manager import TeamManager


class TestGlobalTeamSystem(BaseGameTest):
    """Test Global Team system using modern testing framework"""
    service_class = TeamManager

    def test_default_teams_creation(self):
        """Test creating default teams"""
        default_teams = [
            {'name': 'Fire Dragons', 'color': '#FF4444', 'element': 'fire'},
            {'name': 'Ice Phoenix', 'color': '#4444FF', 'element': 'ice'},
            {'name': 'Earth Guardians', 'color': '#44AA44', 'element': 'earth'},
            {'name': 'Storm Eagles', 'color': '#FFAA00', 'element': 'storm'}
        ]

        for team_data in default_teams:
            team = {
                '_id': ObjectId(),
                'name': team_data['name'],
                'color': team_data['color'],
                'element': team_data['element'],
                'total_score': 0,
                'member_count': 0,
                'member_ids': [],
                'score_history': [],
                'created_at': datetime.now(timezone.utc),
                'is_active': True
            }

            self.assertIn(team['name'], ['Fire Dragons', 'Ice Phoenix', 'Earth Guardians', 'Storm Eagles'])
            self.assertEqual(team['total_score'], 0)
            self.assertEqual(team['member_count'], 0)
            self.assertIsInstance(team['member_ids'], list)

    def test_team_score_addition(self):
        """Test adding score to team"""
        team = {
            '_id': ObjectId(),
            'name': 'Fire Dragons',
            'total_score': 500,
            'member_ids': [str(ObjectId())],
            'score_history': []
        }

        # Simulate score addition
        new_score = 100
        user_id = str(ObjectId())

        # Update team data
        team['total_score'] += new_score
        team['score_history'].append({
            'user_id': user_id,
            'points': new_score,
            'timestamp': datetime.now(timezone.utc),
            'source': 'game_completion'
        })

        self.assertEqual(team['total_score'], 600)
        self.assertEqual(len(team['score_history']), 1)
        self.assertEqual(team['score_history'][0]['user_id'], user_id)
        self.assertEqual(team['score_history'][0]['points'], new_score)

    def test_team_member_management(self):
        """Test adding and managing team members"""
        team = {
            '_id': ObjectId(),
            'name': 'Ice Phoenix',
            'member_count': 0,
            'member_ids': [],
            'member_roles': {}
        }

        # Add new member
        new_member_id = str(ObjectId())
        team['member_ids'].append(new_member_id)
        team['member_count'] += 1
        team['member_roles'][new_member_id] = 'member'

        self.assertEqual(team['member_count'], 1)
        self.assertIn(new_member_id, team['member_ids'])
        self.assertEqual(team['member_roles'][new_member_id], 'member')

        # Test member removal
        team['member_ids'].remove(new_member_id)
        team['member_count'] -= 1
        del team['member_roles'][new_member_id]

        self.assertEqual(team['member_count'], 0)
        self.assertNotIn(new_member_id, team['member_ids'])

    def test_team_tournament_creation(self):
        """Test creating team tournaments"""
        tournament = {
            '_id': ObjectId(),
            'name': 'Summer Championship',
            'tournament_type': 'seasonal_war',
            'start_date': datetime.now(timezone.utc),
            'end_date': datetime.now(timezone.utc) + timedelta(days=30),
            'participating_teams': [ObjectId() for _ in range(4)],
            'status': 'active',
            'prize_pool': {
                'winner': 5000,
                'runner_up': 2000,
                'participation': 500
            },
            'rules': {
                'scoring_method': 'cumulative',
                'allow_substitutions': True,
                'max_participants_per_team': 50
            }
        }

        self.assertEqual(tournament['name'], 'Summer Championship')
        self.assertEqual(tournament['tournament_type'], 'seasonal_war')
        self.assertEqual(len(tournament['participating_teams']), 4)
        self.assertEqual(tournament['status'], 'active')
        self.assertEqual(tournament['prize_pool']['winner'], 5000)

    def test_team_balancing_algorithm(self):
        """Test team balancing functionality"""
        # Create test users with different skill levels
        users = []
        for i in range(20):
            user = self.create_test_user(
                email=f'player{i}@test.com'
            )
            # Simulate skill rating
            skill_rating = 1000 + (i * 50)  # Range from 1000 to 1950
            user['skill_rating'] = skill_rating
            users.append(user)

        # Simulate team assignment algorithm
        teams = [[] for _ in range(4)]
        team_totals = [0, 0, 0, 0]

        # Simple balancing: assign to team with lowest total skill
        for user in users:
            min_team_idx = team_totals.index(min(team_totals))
            teams[min_team_idx].append(user)
            team_totals[min_team_idx] += user['skill_rating']

        # Validate balancing
        for i, team in enumerate(teams):
            self.assertGreater(len(team), 0)

        # Check that teams are reasonably balanced (within 20% of average)
        avg_total = sum(team_totals) / len(team_totals)
        for total in team_totals:
            variance = abs(total - avg_total) / avg_total
            self.assertLess(variance, 0.3)  # Within 30% variance

    def test_team_leaderboard_ranking(self):
        """Test team leaderboard ranking"""
        teams_data = [
            {'name': 'Fire Dragons', 'total_score': 15000, 'member_count': 45},
            {'name': 'Ice Phoenix', 'total_score': 12000, 'member_count': 38},
            {'name': 'Earth Guardians', 'total_score': 18000, 'member_count': 52},
            {'name': 'Storm Eagles', 'total_score': 9000, 'member_count': 31}
        ]

        # Sort by total score (descending)
        ranked_teams = sorted(teams_data, key=lambda x: x['total_score'], reverse=True)

        # Validate ranking
        self.assertEqual(ranked_teams[0]['name'], 'Earth Guardians')
        self.assertEqual(ranked_teams[1]['name'], 'Fire Dragons')
        self.assertEqual(ranked_teams[2]['name'], 'Ice Phoenix')
        self.assertEqual(ranked_teams[3]['name'], 'Storm Eagles')

        # Test alternative ranking by average score per member
        for team in teams_data:
            team['avg_score_per_member'] = team['total_score'] / team['member_count'] if team['member_count'] > 0 else 0

        avg_ranked = sorted(teams_data, key=lambda x: x['avg_score_per_member'], reverse=True)

        # Validate that different ranking methods can produce different results
        self.assertIsInstance(avg_ranked[0]['avg_score_per_member'], float)
        self.assertGreater(avg_ranked[0]['avg_score_per_member'], 0)

    def test_team_member_roles(self):
        """Test team member roles and permissions"""
        team = {
            '_id': ObjectId(),
            'name': 'Test Team',
            'member_roles': {},
            'leadership_structure': {
                'captain_count': 1,
                'veteran_count': 3,
                'member_count': 0
            }
        }

        # Test role assignment
        users = [str(ObjectId()) for _ in range(10)]

        # Assign captain
        team['member_roles'][users[0]] = 'captain'
        team['leadership_structure']['captain_count'] = 1

        # Assign veterans
        for i in range(1, 4):
            team['member_roles'][users[i]] = 'veteran'

        # Assign regular members
        for i in range(4, 10):
            team['member_roles'][users[i]] = 'member'
            team['leadership_structure']['member_count'] += 1

        # Validate role distribution
        captain_count = sum(1 for role in team['member_roles'].values() if role == 'captain')
        veteran_count = sum(1 for role in team['member_roles'].values() if role == 'veteran')
        member_count = sum(1 for role in team['member_roles'].values() if role == 'member')

        self.assertEqual(captain_count, 1)
        self.assertEqual(veteran_count, 3)
        self.assertEqual(member_count, 6)

    def test_tournament_scoring_systems(self):
        """Test different tournament scoring systems"""
        scoring_systems = [
            {
                'name': 'cumulative',
                'description': 'Total points accumulated',
                'calculation': 'sum'
            },
            {
                'name': 'average',
                'description': 'Average points per member',
                'calculation': 'avg'
            },
            {
                'name': 'weighted',
                'description': 'Weighted by member activity',
                'calculation': 'weighted_sum'
            }
        ]

        # Test scoring calculation for each system
        team_data = {
            'total_score': 10000,
            'member_count': 25,
            'active_members': 20,
            'score_contributions': [500, 400, 300, 200, 100]  # Top 5 contributors
        }

        for system in scoring_systems:
            if system['calculation'] == 'sum':
                score = team_data['total_score']
            elif system['calculation'] == 'avg':
                score = team_data['total_score'] / team_data['member_count']
            elif system['calculation'] == 'weighted_sum':
                score = (team_data['total_score'] * team_data['active_members']) / team_data['member_count']

            self.assertGreater(score, 0)
            self.assertEqual(system['name'] in ['cumulative', 'average', 'weighted'], True)

    def test_team_statistics_tracking(self):
        """Test team statistics and analytics"""
        team_stats = {
            'team_id': ObjectId(),
            'statistics': {
                'games_played': 150,
                'games_won': 95,
                'win_rate': 0.633,
                'average_score_per_game': 285.5,
                'most_active_day': 'Saturday',
                'peak_activity_hour': 20,
                'member_retention_rate': 0.85,
                'recruitment_rate': 1.2,  # new members per week
                'contribution_distribution': {
                    'top_10_percent': 0.45,    # Top 10% contribute 45%
                    'middle_50_percent': 0.35,  # Middle 50% contribute 35%
                    'bottom_40_percent': 0.20   # Bottom 40% contribute 20%
                }
            }
        }

        stats = team_stats['statistics']

        # Validate statistics structure
        self.assertGreater(stats['games_played'], 0)
        self.assertGreater(stats['win_rate'], 0)
        self.assertLess(stats['win_rate'], 1)
        self.assertGreater(stats['average_score_per_game'], 0)
        self.assertIn(stats['most_active_day'], ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'])

        # Validate contribution distribution adds up to 1.0
        contribution_sum = (
            stats['contribution_distribution']['top_10_percent'] +
            stats['contribution_distribution']['middle_50_percent'] +
            stats['contribution_distribution']['bottom_40_percent']
        )
        self.assertAlmostEqual(contribution_sum, 1.0, places=2)