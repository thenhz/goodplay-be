"""
Social features fixtures for GoodPlay tests.

Provides pre-configured social data including achievements,
challenges, teams, and leaderboards.
"""
import pytest
from datetime import datetime, timezone, timedelta
from tests.core import TestUtils


@pytest.fixture
def basic_achievement_data(test_utils):
    """Basic achievement data"""
    return test_utils.create_mock_achievement()


@pytest.fixture
def gaming_achievement_data(test_utils):
    """Gaming-specific achievement data"""
    return test_utils.create_mock_achievement(
        name="First Victory",
        description="Win your first game",
        category="gaming",
        points=50,
        icon="trophy",
        rarity="common",
        conditions={
            "type": "game_wins",
            "threshold": 1
        }
    )


@pytest.fixture
def rare_achievement_data(test_utils):
    """Rare achievement data"""
    return test_utils.create_mock_achievement(
        name="Legendary Player",
        description="Achieve a perfect score in 10 consecutive games",
        category="gaming",
        points=500,
        icon="crown",
        rarity="legendary",
        conditions={
            "type": "perfect_streak",
            "threshold": 10
        }
    )


@pytest.fixture
def donation_achievement_data(test_utils):
    """Donation-related achievement data"""
    return test_utils.create_mock_achievement(
        name="Generous Heart",
        description="Donate $100 total to causes",
        category="donations",
        points=100,
        icon="heart",
        rarity="uncommon",
        conditions={
            "type": "total_donations",
            "threshold": 100.0
        }
    )


@pytest.fixture
def multiple_achievements(test_utils):
    """List of multiple achievements"""
    achievements = [
        test_utils.create_mock_achievement(
            name="Quick Starter",
            description="Complete tutorial",
            category="onboarding",
            points=10,
            rarity="common"
        ),
        test_utils.create_mock_achievement(
            name="Score Master",
            description="Achieve score over 1000",
            category="gaming",
            points=75,
            rarity="uncommon"
        ),
        test_utils.create_mock_achievement(
            name="Social Butterfly",
            description="Add 10 friends",
            category="social",
            points=50,
            rarity="common"
        ),
        test_utils.create_mock_achievement(
            name="Challenger",
            description="Complete 5 challenges",
            category="challenges",
            points=100,
            rarity="uncommon"
        ),
        test_utils.create_mock_achievement(
            name="Team Player",
            description="Win 3 team tournaments",
            category="teams",
            points=200,
            rarity="rare"
        )
    ]
    return achievements


@pytest.fixture
def user_achievement_earned(test_utils):
    """User achievement that's been earned"""
    return test_utils.create_mock_user_achievement(
        earned_at=datetime.now(timezone.utc) - timedelta(hours=2),
        progress=100,
        metadata={
            "score_achieved": 1250,
            "game_duration": 1800
        }
    )


@pytest.fixture
def user_achievement_in_progress(test_utils):
    """User achievement in progress"""
    return test_utils.create_mock_user_achievement(
        earned_at=None,
        progress=65,
        metadata={
            "current_count": 6,
            "required_count": 10
        }
    )


@pytest.fixture
def basic_challenge_data(test_utils):
    """Basic challenge data"""
    return test_utils.create_mock_challenge()


@pytest.fixture
def one_vs_one_challenge(test_utils):
    """1v1 challenge data"""
    return test_utils.create_mock_challenge(
        title="Speed Challenge",
        description="Who can solve puzzles faster?",
        challenge_type="1v1",
        max_participants=2,
        duration_minutes=15,
        skill_level="medium",
        is_public=False
    )


@pytest.fixture
def public_nvn_challenge(test_utils):
    """Public NvN challenge data"""
    return test_utils.create_mock_challenge(
        title="Weekly Puzzle Tournament",
        description="Open puzzle tournament for all skill levels",
        challenge_type="NvN",
        max_participants=50,
        duration_minutes=60,
        skill_level="mixed",
        is_public=True,
        entry_fee=0,
        prize_pool=500
    )


@pytest.fixture
def skill_based_challenge(test_utils):
    """Skill-based matchmaking challenge"""
    return test_utils.create_mock_challenge(
        title="Expert Level Challenge",
        description="High-skill challenge for experienced players",
        challenge_type="1v1",
        max_participants=2,
        duration_minutes=30,
        skill_level="expert",
        is_public=True,
        skill_requirements={
            "min_rating": 1500,
            "min_games_played": 50,
            "win_rate_threshold": 0.6
        }
    )


@pytest.fixture
def expired_challenge(test_utils):
    """Expired challenge data"""
    return test_utils.create_mock_challenge(
        status="expired",
        created_at=datetime.now(timezone.utc) - timedelta(days=3),
        starts_at=datetime.now(timezone.utc) - timedelta(days=2),
        expires_at=datetime.now(timezone.utc) - timedelta(days=1)
    )


@pytest.fixture
def active_challenge_in_progress(test_utils):
    """Active challenge currently in progress"""
    return test_utils.create_mock_challenge(
        status="in_progress",
        created_at=datetime.now(timezone.utc) - timedelta(hours=2),
        starts_at=datetime.now(timezone.utc) - timedelta(hours=1),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
        current_participants=2,
        max_participants=2
    )


@pytest.fixture
def challenge_participant_data(test_utils):
    """Challenge participant data"""
    return {
        "_id": test_utils.get_unique_id(),
        "user_id": test_utils.get_unique_id(),
        "challenge_id": test_utils.get_unique_id(),
        "status": "accepted",
        "joined_at": datetime.now(timezone.utc) - timedelta(minutes=30),
        "ready": True,
        "current_score": 450,
        "submission_time": None,
        "final_score": None
    }


@pytest.fixture
def global_team_data(test_utils):
    """Global team data"""
    return {
        "_id": test_utils.get_unique_id(),
        "name": "Team Phoenix",
        "description": "Rise from the ashes to victory",
        "color": "#FF6B35",
        "icon": "phoenix",
        "member_count": 1247,
        "total_score": 98765,
        "rank": 2,
        "created_at": datetime.now(timezone.utc) - timedelta(days=90),
        "is_active": True
    }


@pytest.fixture
def team_member_data(test_utils):
    """Team member data"""
    return {
        "_id": test_utils.get_unique_id(),
        "user_id": test_utils.get_unique_id(),
        "team_id": test_utils.get_unique_id(),
        "role": "member",
        "joined_at": datetime.now(timezone.utc) - timedelta(days=30),
        "contribution_score": 1250,
        "games_played": 45,
        "tournaments_participated": 3,
        "is_active": True
    }


@pytest.fixture
def team_captain_data(test_utils):
    """Team captain data"""
    return {
        "_id": test_utils.get_unique_id(),
        "user_id": test_utils.get_unique_id(),
        "team_id": test_utils.get_unique_id(),
        "role": "captain",
        "joined_at": datetime.now(timezone.utc) - timedelta(days=180),
        "contribution_score": 5680,
        "games_played": 234,
        "tournaments_participated": 15,
        "leadership_score": 92.5,
        "is_active": True
    }


@pytest.fixture
def tournament_data(test_utils):
    """Tournament data"""
    return {
        "_id": test_utils.get_unique_id(),
        "name": "Monthly Team Battle",
        "description": "Monthly competition between global teams",
        "tournament_type": "monthly_battle",
        "status": "active",
        "start_date": datetime.now(timezone.utc) - timedelta(days=10),
        "end_date": datetime.now(timezone.utc) + timedelta(days=20),
        "prize_pool": 10000,
        "participating_teams": 4,
        "total_games": 1247,
        "created_at": datetime.now(timezone.utc) - timedelta(days=15)
    }


@pytest.fixture
def leaderboard_entry_data(test_utils):
    """Leaderboard entry data"""
    return {
        "_id": test_utils.get_unique_id(),
        "user_id": test_utils.get_unique_id(),
        "leaderboard_type": "global_score",
        "period": "weekly",
        "rank": 15,
        "score": 8542,
        "games_played": 28,
        "win_rate": 0.75,
        "average_score": 305.1,
        "streak": 5,
        "last_updated": datetime.now(timezone.utc) - timedelta(hours=1)
    }


@pytest.fixture
def social_relationship_data(test_utils):
    """Social relationship data"""
    return {
        "_id": test_utils.get_unique_id(),
        "user_id": test_utils.get_unique_id(),
        "target_user_id": test_utils.get_unique_id(),
        "relationship_type": "friend",
        "status": "accepted",
        "created_at": datetime.now(timezone.utc) - timedelta(days=7),
        "accepted_at": datetime.now(timezone.utc) - timedelta(days=6),
        "mutual_friends": 3
    }


@pytest.fixture
def friend_request_pending(test_utils):
    """Pending friend request data"""
    return {
        "_id": test_utils.get_unique_id(),
        "user_id": test_utils.get_unique_id(),
        "target_user_id": test_utils.get_unique_id(),
        "relationship_type": "friend",
        "status": "pending",
        "created_at": datetime.now(timezone.utc) - timedelta(hours=6),
        "message": "Let's be friends and play together!"
    }


@pytest.fixture
def multiple_social_relationships(test_utils):
    """Multiple social relationships for testing"""
    user_id = test_utils.get_unique_id()

    return [
        {
            "_id": test_utils.get_unique_id(),
            "user_id": user_id,
            "target_user_id": test_utils.get_unique_id(),
            "relationship_type": "friend",
            "status": "accepted",
            "created_at": datetime.now(timezone.utc) - timedelta(days=30)
        },
        {
            "_id": test_utils.get_unique_id(),
            "user_id": user_id,
            "target_user_id": test_utils.get_unique_id(),
            "relationship_type": "friend",
            "status": "pending",
            "created_at": datetime.now(timezone.utc) - timedelta(hours=12)
        },
        {
            "_id": test_utils.get_unique_id(),
            "user_id": user_id,
            "target_user_id": test_utils.get_unique_id(),
            "relationship_type": "blocked",
            "status": "active",
            "created_at": datetime.now(timezone.utc) - timedelta(days=5)
        }
    ]