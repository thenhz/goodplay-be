"""
BaseSocialTest - Specialized Base Class for Social Features Testing (GOO-35)

Provides specialized testing capabilities for social functionality including
social graph, achievements, leaderboards, friend systems, and team features.
"""
from typing import Dict, Any, Optional, List, Tuple
from unittest.mock import MagicMock, patch
from bson import ObjectId
from datetime import datetime, timezone

from tests.core.base_service_test import BaseServiceTest


class BaseSocialTest(BaseServiceTest):
    """
    Specialized base test class for social features functionality.

    Features:
    - Social graph and relationship testing
    - Achievement system utilities
    - Leaderboard testing
    - Friend system management
    - Team functionality testing
    - Social challenge scenarios
    - Notification system testing
    """

    # Default dependencies for social tests
    default_dependencies = [
        'user_repository',
        'achievement_repository',
        'leaderboard_repository',
        'social_graph_service',
        'achievement_service',
        'team_service',
        'notification_service'
    ]

    # External dependencies for social features
    default_external_dependencies = [
        'redis',
        'websocket',
        'push_notifications'
    ]

    def setUp(self):
        """Enhanced setup for social features testing"""
        super().setUp()
        self._setup_social_mocks()
        self._setup_achievement_mocks()
        self._setup_leaderboard_mocks()
        self._setup_notification_mocks()

    def _setup_social_mocks(self):
        """Setup social graph related mocks"""
        if hasattr(self, 'mock_social_graph_service'):
            # Default social graph behavior
            self.mock_social_graph_service.add_relationship.return_value = (True, "Relationship added", {})
            self.mock_social_graph_service.remove_relationship.return_value = (True, "Relationship removed", {})
            self.mock_social_graph_service.get_friends.return_value = (True, "Friends retrieved", [])
            self.mock_social_graph_service.get_mutual_friends.return_value = (True, "Mutual friends found", [])

    def _setup_achievement_mocks(self):
        """Setup achievement system mocks"""
        if hasattr(self, 'mock_achievement_repository'):
            self.mock_achievement_repository.find_by_id.return_value = None
            self.mock_achievement_repository.find_by_user.return_value = []
            self.mock_achievement_repository.create_user_achievement.return_value = str(ObjectId())

        if hasattr(self, 'mock_achievement_service'):
            self.mock_achievement_service.unlock_achievement.return_value = (True, "Achievement unlocked", {})
            self.mock_achievement_service.check_achievement_criteria.return_value = (True, "Criteria met", [])
            self.mock_achievement_service.get_user_achievements.return_value = (True, "Achievements retrieved", [])

    def _setup_leaderboard_mocks(self):
        """Setup leaderboard system mocks"""
        if hasattr(self, 'mock_leaderboard_repository'):
            self.mock_leaderboard_repository.find_by_game.return_value = []
            self.mock_leaderboard_repository.find_user_ranking.return_value = None
            self.mock_leaderboard_repository.update_score.return_value = True

        if hasattr(self, 'mock_leaderboard_service'):
            self.mock_leaderboard_service.update_user_score.return_value = (True, "Score updated", {})
            self.mock_leaderboard_service.get_rankings.return_value = (True, "Rankings retrieved", [])

    def _setup_notification_mocks(self):
        """Setup notification system mocks"""
        if hasattr(self, 'mock_notification_service'):
            self.mock_notification_service.send_notification.return_value = (True, "Notification sent", {})
            self.mock_notification_service.create_achievement_notification.return_value = (True, "Achievement notification created", {})
            self.mock_notification_service.create_friend_request_notification.return_value = (True, "Friend request notification created", {})

    # Social graph testing utilities

    def create_test_social_user(self, display_name: str = 'Test User', **kwargs) -> Dict[str, Any]:
        """Create test social user data with social-specific fields"""
        from tests.utils import user

        user_data = (user()
                    .as_type('user')
                    .with_field('display_name', display_name)
                    .with_field('social_stats', {
                        'friends_count': 0,
                        'achievements_count': 0,
                        'games_played': 0,
                        'total_score': 0
                    })
                    .with_field('privacy_settings', {
                        'profile_visibility': 'public',
                        'contact_permissions': 'friends'
                    })
                    .merge(kwargs)
                    .build())

        return user_data

    def create_test_friend_request(self, sender_id: str = None, target_id: str = None, status: str = 'pending', **kwargs) -> Dict[str, Any]:
        """Create test friend request data"""
        request_data = {
            'request_id': str(ObjectId()),
            'sender_id': sender_id or str(ObjectId()),
            'target_id': target_id or str(ObjectId()),
            'status': status,
            'sent_at': datetime.now(timezone.utc),
            'message': 'Hi! Let\'s be friends on GoodPlay!',
            **kwargs
        }
        return request_data

    def create_test_relationship(self, user1_id: str = None, user2_id: str = None,
                               relationship_type: str = 'friend', status: str = 'accepted', **kwargs) -> Dict[str, Any]:
        """Create test relationship data"""
        user1_id = user1_id or str(ObjectId())
        user2_id = user2_id or str(ObjectId())

        relationship = {
            '_id': ObjectId(),
            'user1_id': user1_id,
            'user2_id': user2_id,
            'relationship_type': relationship_type,
            'status': status,
            'created_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc)
        }
        relationship.update(kwargs)
        return relationship

    def create_social_network(self, user_count: int = 5, relationship_density: float = 0.3) -> Dict[str, Any]:
        """Create a test social network with multiple users and relationships"""
        from tests.utils import user

        # Create users
        users = []
        for i in range(user_count):
            test_user = user().with_email(f'user{i+1}@social.com').build()
            users.append(test_user)

        # Create relationships based on density
        relationships = []
        for i in range(user_count):
            for j in range(i + 1, user_count):
                if i != j and len(relationships) / (user_count * (user_count - 1) / 2) < relationship_density:
                    relationship = self.create_test_relationship(
                        users[i]['_id'],
                        users[j]['_id']
                    )
                    relationships.append(relationship)

        return {
            'users': users,
            'relationships': relationships,
            'user_count': user_count,
            'relationship_count': len(relationships)
        }

    def mock_friend_request_flow(self, requester_id: str, target_id: str):
        """Mock complete friend request flow"""
        # Mock friend request creation
        friend_request = self.create_test_relationship(
            requester_id, target_id,
            relationship_type='friend',
            status='pending'
        )

        self.mock_social_graph_service.send_friend_request.return_value = (
            True, "Friend request sent", friend_request
        )

        # Mock acceptance
        accepted_relationship = {**friend_request, 'status': 'accepted'}
        self.mock_social_graph_service.accept_friend_request.return_value = (
            True, "Friend request accepted", accepted_relationship
        )

        return friend_request, accepted_relationship

    def mock_mutual_friends_scenario(self, user_id: str, friend_ids: List[str], mutual_friend_ids: List[str]):
        """Mock mutual friends discovery scenario"""
        # Mock user's friends
        user_friends = [self.create_test_relationship(user_id, friend_id) for friend_id in friend_ids]
        self.mock_social_graph_service.get_friends.return_value = (True, "Friends retrieved", user_friends)

        # Mock mutual friends
        mutual_friends = [self.create_test_relationship(user_id, mutual_id) for mutual_id in mutual_friend_ids]
        self.mock_social_graph_service.get_mutual_friends.return_value = (True, "Mutual friends found", mutual_friends)

        return user_friends, mutual_friends

    # Achievement system testing utilities

    def create_test_achievement(self, achievement_type: str = 'score', criteria: Dict[str, Any] = None, **kwargs) -> Dict[str, Any]:
        """Create test achievement data"""
        criteria = criteria or {}

        achievement_types = {
            'score': {'min_score': 1000, 'game_category': 'puzzle'},
            'streak': {'win_streak': 5, 'consecutive': True},
            'social': {'friend_count': 10, 'interaction_type': 'game_invite'},
            'time': {'play_time_hours': 50, 'period_days': 30},
            'challenge': {'challenge_type': 'daily', 'completions': 7}
        }

        base_criteria = achievement_types.get(achievement_type, {})
        base_criteria.update(criteria)

        achievement = {
            '_id': ObjectId(),
            'name': f'Test {achievement_type.title()} Achievement',
            'description': f'Achievement for {achievement_type} testing',
            'type': achievement_type,
            'criteria': base_criteria,
            'points': 100,
            'badge_icon': f'{achievement_type}_badge.png',
            'is_hidden': False,
            'created_at': datetime.now(timezone.utc)
        }
        achievement.update(kwargs)
        return achievement

    def create_test_user_achievement(self, user_id: str = None, achievement_id: str = None,
                                   progress: float = 100.0, unlocked: bool = True, **kwargs) -> Dict[str, Any]:
        """Create test user achievement data"""
        user_id = user_id or str(ObjectId())
        achievement_id = achievement_id or str(ObjectId())

        user_achievement = {
            '_id': ObjectId(),
            'user_id': user_id,
            'achievement_id': achievement_id,
            'progress': progress,
            'unlocked': unlocked,
            'unlocked_at': datetime.now(timezone.utc) if unlocked else None,
            'created_at': datetime.now(timezone.utc)
        }
        user_achievement.update(kwargs)
        return user_achievement

    def mock_achievement_unlock_scenario(self, user_id: str, achievement_type: str = 'score'):
        """Mock achievement unlock scenario"""
        achievement = self.create_test_achievement(achievement_type)
        user_achievement = self.create_test_user_achievement(user_id, achievement['_id'])

        # Mock achievement service calls
        self.mock_achievement_service.check_achievement_criteria.return_value = (True, "Criteria met", [achievement['_id']])
        self.mock_achievement_service.unlock_achievement.return_value = (True, "Achievement unlocked", user_achievement)

        # Mock repository calls
        self.mock_achievement_repository.find_by_id.return_value = achievement
        self.mock_achievement_repository.create_user_achievement.return_value = user_achievement['_id']

        return achievement, user_achievement

    def assert_achievement_unlocked(self, result: Tuple[bool, str, Any], expected_achievement_id: str = None):
        """Assert achievement unlock result"""
        from tests.utils import assert_service_response_pattern

        assert_service_response_pattern(result)
        success, message, data = result

        assert success, f"Expected successful achievement unlock, got: {message}"
        assert 'unlocked' in message.lower() or 'achievement' in message.lower(), f"Expected achievement message, got: {message}"

        if expected_achievement_id and data:
            assert data.get('achievement_id') == expected_achievement_id, f"Expected achievement {expected_achievement_id}, got {data.get('achievement_id')}"

    # Leaderboard testing utilities

    def create_test_leaderboard_entry(self, user_id: str = None, game_id: str = None,
                                    score: int = 1000, rank: int = 1, **kwargs) -> Dict[str, Any]:
        """Create test leaderboard entry"""
        user_id = user_id or str(ObjectId())
        game_id = game_id or str(ObjectId())

        entry = {
            '_id': ObjectId(),
            'user_id': user_id,
            'game_id': game_id,
            'score': score,
            'rank': rank,
            'created_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc)
        }
        entry.update(kwargs)
        return entry

    def create_test_leaderboard(self, game_id: str = None, entry_count: int = 10) -> Dict[str, Any]:
        """Create test leaderboard with multiple entries"""
        from tests.utils import user

        game_id = game_id or str(ObjectId())
        entries = []

        for i in range(entry_count):
            test_user = user().with_email(f'player{i+1}@leaderboard.com').build()
            entry = self.create_test_leaderboard_entry(
                user_id=test_user['_id'],
                game_id=game_id,
                score=1000 - (i * 50),  # Descending scores
                rank=i + 1
            )
            entries.append(entry)

        return {
            'game_id': game_id,
            'entries': entries,
            'total_entries': len(entries)
        }

    def mock_leaderboard_update_scenario(self, user_id: str, game_id: str, new_score: int):
        """Mock leaderboard score update scenario"""
        # Mock current entry
        current_entry = self.create_test_leaderboard_entry(user_id, game_id, score=800, rank=5)
        self.mock_leaderboard_repository.find_user_ranking.return_value = current_entry

        # Mock updated entry
        updated_entry = {**current_entry, 'score': new_score, 'rank': 2}
        self.mock_leaderboard_service.update_user_score.return_value = (True, "Score updated", updated_entry)

        return current_entry, updated_entry

    # Team functionality testing

    def create_test_team(self, team_name: str = None, member_count: int = 5, **kwargs) -> Dict[str, Any]:
        """Create test team data"""
        from tests.utils import user

        team_name = team_name or 'Test Team'

        # Create team members
        members = []
        for i in range(member_count):
            member = user().with_email(f'member{i+1}@team.com').build()
            members.append({
                'user_id': member['_id'],
                'role': 'captain' if i == 0 else 'member',
                'joined_at': datetime.now(timezone.utc)
            })

        team = {
            '_id': ObjectId(),
            'name': team_name,
            'description': f'Test team for {team_name}',
            'members': members,
            'member_count': len(members),
            'total_score': sum(i * 100 for i in range(member_count)),  # Mock team score
            'created_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc)
        }
        team.update(kwargs)
        return team

    def mock_team_tournament_scenario(self, team_count: int = 4):
        """Mock team tournament scenario"""
        teams = []
        for i in range(team_count):
            team = self.create_test_team(f'Team {chr(65 + i)}', member_count=4)  # Team A, B, C, D
            teams.append(team)

        # Mock tournament data
        tournament = {
            '_id': ObjectId(),
            'name': 'Test Tournament',
            'teams': teams,
            'status': 'active',
            'start_time': datetime.now(timezone.utc),
            'leaderboard': [
                {'team_id': team['_id'], 'score': team['total_score'], 'rank': i + 1}
                for i, team in enumerate(sorted(teams, key=lambda t: t['total_score'], reverse=True))
            ]
        }

        if hasattr(self, 'mock_team_service'):
            self.mock_team_service.get_tournament.return_value = (True, "Tournament retrieved", tournament)
            self.mock_team_service.get_team_rankings.return_value = (True, "Rankings retrieved", tournament['leaderboard'])

        return tournament

    # Social challenge testing

    def create_test_social_challenge(self, challenge_type: str = 'friend_challenge',
                                   participants: List[str] = None, **kwargs) -> Dict[str, Any]:
        """Create test social challenge"""
        participants = participants or [str(ObjectId()), str(ObjectId())]

        challenge_types = {
            'friend_challenge': {'type': '1v1', 'game_mode': 'competitive'},
            'team_challenge': {'type': 'team', 'min_participants': 4},
            'daily_challenge': {'type': 'daily', 'duration_hours': 24},
            'tournament_challenge': {'type': 'tournament', 'bracket_size': 8}
        }

        base_config = challenge_types.get(challenge_type, {})

        challenge = {
            '_id': ObjectId(),
            'name': f'Test {challenge_type.replace("_", " ").title()}',
            'type': challenge_type,
            'participants': participants,
            'status': 'active',
            'config': base_config,
            'created_at': datetime.now(timezone.utc),
            'expires_at': datetime.now(timezone.utc).replace(hour=23, minute=59, second=59)
        }
        challenge.update(kwargs)
        return challenge

    def mock_social_challenge_flow(self, challenger_id: str, challenged_id: str):
        """Mock complete social challenge flow"""
        # Create challenge
        challenge = self.create_test_social_challenge(
            'friend_challenge',
            participants=[challenger_id, challenged_id]
        )

        # Mock challenge service
        if hasattr(self, 'mock_challenge_service'):
            self.mock_challenge_service.create_challenge.return_value = (True, "Challenge created", challenge)
            self.mock_challenge_service.accept_challenge.return_value = (True, "Challenge accepted", challenge)
            self.mock_challenge_service.complete_challenge.return_value = (True, "Challenge completed", {
                **challenge,
                'status': 'completed',
                'winner_id': challenger_id
            })

        return challenge

    # Notification testing utilities

    def create_test_notification(self, user_id: str = None, notification_type: str = 'achievement', **kwargs) -> Dict[str, Any]:
        """Create test notification data"""
        user_id = user_id or str(ObjectId())

        notification_templates = {
            'achievement': {
                'title': 'Achievement Unlocked!',
                'message': 'You unlocked a new achievement',
                'action_url': '/achievements'
            },
            'friend_request': {
                'title': 'New Friend Request',
                'message': 'Someone wants to be your friend',
                'action_url': '/friends/requests'
            },
            'challenge': {
                'title': 'Challenge Received',
                'message': 'You have been challenged to a game',
                'action_url': '/challenges'
            },
            'team_invitation': {
                'title': 'Team Invitation',
                'message': 'You have been invited to join a team',
                'action_url': '/teams'
            }
        }

        template = notification_templates.get(notification_type, notification_templates['achievement'])

        notification = {
            '_id': ObjectId(),
            'user_id': user_id,
            'type': notification_type,
            'title': template['title'],
            'message': template['message'],
            'action_url': template['action_url'],
            'read': False,
            'created_at': datetime.now(timezone.utc)
        }
        notification.update(kwargs)
        return notification

    def mock_notification_flow(self, user_id: str, notification_types: List[str]):
        """Mock notification creation and delivery flow"""
        notifications = []
        for notification_type in notification_types:
            notification = self.create_test_notification(user_id, notification_type)
            notifications.append(notification)

        self.mock_notification_service.get_user_notifications.return_value = (
            True, "Notifications retrieved", notifications
        )

        return notifications

    # Assertion utilities for social features

    def assert_social_relationship_valid(self, relationship: Dict[str, Any]):
        """Assert social relationship structure is valid"""
        required_fields = ['user1_id', 'user2_id', 'relationship_type', 'status']

        for field in required_fields:
            assert field in relationship, f"Relationship missing required field: {field}"

        valid_statuses = ['pending', 'accepted', 'blocked', 'declined']
        assert relationship['status'] in valid_statuses, f"Invalid relationship status: {relationship['status']}"

    def assert_leaderboard_entry_valid(self, entry: Dict[str, Any]):
        """Assert leaderboard entry structure is valid"""
        required_fields = ['user_id', 'game_id', 'score', 'rank']

        for field in required_fields:
            assert field in entry, f"Leaderboard entry missing required field: {field}"

        assert isinstance(entry['score'], (int, float)), "Score must be numeric"
        assert isinstance(entry['rank'], int) and entry['rank'] > 0, "Rank must be positive integer"

    def tearDown(self):
        """Clean up social-specific mocks"""
        super().tearDown()


# Convenience functions for social testing

def social_test(service_class=None, social_features: List[str] = None, **kwargs):
    """Decorator for creating social test class with specific configuration"""
    def decorator(cls):
        if service_class:
            cls.service_class = service_class

        # Add social feature-specific dependencies
        if social_features:
            feature_deps = {
                'achievements': ['achievement_service', 'badge_service'],
                'leaderboards': ['leaderboard_service', 'ranking_service'],
                'teams': ['team_service', 'tournament_service'],
                'challenges': ['challenge_service', 'matchmaking_service']
            }

            extra_deps = []
            for feature in social_features:
                extra_deps.extend(feature_deps.get(feature, []))

            cls.dependencies = BaseSocialTest.default_dependencies + extra_deps

        return cls

    return decorator


# Usage Examples:
"""
# Basic social service test
class TestSocialGraphService(BaseSocialTest):
    service_class = SocialGraphService

    def test_send_friend_request(self):
        user1_id = str(ObjectId())
        user2_id = str(ObjectId())

        friend_request, accepted = self.mock_friend_request_flow(user1_id, user2_id)

        result = self.service.send_friend_request(user1_id, user2_id)

        assert result[0] is True
        self.assert_social_relationship_valid(result[2])

# Achievement testing
@social_test(service_class=AchievementService, social_features=['achievements'])
class TestAchievementSystem(BaseSocialTest):
    def test_score_achievement_unlock(self):
        user_id = str(ObjectId())
        achievement, user_achievement = self.mock_achievement_unlock_scenario(user_id, 'score')

        result = self.service.process_score_update(user_id, 1500, 'puzzle')

        self.assert_achievement_unlocked(result, achievement['_id'])

# Social network testing
class TestSocialNetwork(BaseSocialTest):
    service_class = SocialGraphService

    def test_mutual_friends_discovery(self):
        network = self.create_social_network(10, 0.4)
        user_id = network['users'][0]['_id']

        friend_ids = [user['_id'] for user in network['users'][1:4]]
        mutual_ids = [user['_id'] for user in network['users'][4:6]]

        self.mock_mutual_friends_scenario(user_id, friend_ids, mutual_ids)

        result = self.service.find_mutual_friends(user_id, friend_ids[0])

        assert result[0] is True
        assert len(result[2]) > 0

# Team tournament testing
class TestTeamTournament(BaseSocialTest):
    service_class = TeamService

    def test_tournament_leaderboard(self):
        tournament = self.mock_team_tournament_scenario(8)

        result = self.service.get_tournament_rankings(tournament['_id'])

        assert result[0] is True
        assert len(result[2]) == 8

        # Verify rankings are sorted by score
        rankings = result[2]
        for i in range(len(rankings) - 1):
            assert rankings[i]['score'] >= rankings[i + 1]['score']
"""