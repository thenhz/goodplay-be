"""
Game-related fixtures for GoodPlay tests.

Provides pre-configured game data, session scenarios,
and game state configurations.
"""
import pytest
from datetime import datetime, timezone, timedelta
from tests.core import TestUtils


@pytest.fixture
def basic_game_data(test_utils):
    """Basic game data"""
    return test_utils.create_mock_game()


@pytest.fixture
def puzzle_game_data(test_utils):
    """Puzzle game data"""
    return test_utils.create_mock_game(
        name="Test Puzzle Game",
        category="puzzle",
        difficulty="medium",
        min_players=1,
        max_players=1,
        estimated_duration=600  # 10 minutes
    )


@pytest.fixture
def multiplayer_game_data(test_utils):
    """Multiplayer game data"""
    return test_utils.create_mock_game(
        name="Test Multiplayer Game",
        category="strategy",
        difficulty="hard",
        min_players=2,
        max_players=8,
        estimated_duration=1800  # 30 minutes
    )


@pytest.fixture
def quick_game_data(test_utils):
    """Quick game data (under 5 minutes)"""
    return test_utils.create_mock_game(
        name="Test Quick Game",
        category="action",
        difficulty="easy",
        min_players=1,
        max_players=4,
        estimated_duration=240  # 4 minutes
    )


@pytest.fixture
def multiple_games(test_utils):
    """List of multiple games for testing"""
    categories = ["puzzle", "strategy", "action", "adventure", "simulation"]
    difficulties = ["easy", "medium", "hard"]

    games = []
    for i in range(5):
        game = test_utils.create_mock_game(
            name=f"Test Game {i+1}",
            category=categories[i],
            difficulty=difficulties[i % len(difficulties)],
            estimated_duration=300 * (i + 1)  # Increasing duration
        )
        games.append(game)

    return games


@pytest.fixture
def active_session_data(test_utils):
    """Active game session data"""
    return test_utils.create_mock_game_session(
        status="active",
        started_at=datetime.now(timezone.utc) - timedelta(minutes=10),
        updated_at=datetime.now(timezone.utc) - timedelta(seconds=30),
        play_duration_ms=600000,  # 10 minutes
        score=750
    )


@pytest.fixture
def paused_session_data(test_utils):
    """Paused game session data"""
    return test_utils.create_mock_game_session(
        status="paused",
        started_at=datetime.now(timezone.utc) - timedelta(minutes=15),
        paused_at=datetime.now(timezone.utc) - timedelta(minutes=5),
        updated_at=datetime.now(timezone.utc) - timedelta(minutes=5),
        play_duration_ms=600000,  # 10 minutes played before pause
        score=500
    )


@pytest.fixture
def completed_session_data(test_utils):
    """Completed game session data"""
    return test_utils.create_mock_game_session(
        status="completed",
        started_at=datetime.now(timezone.utc) - timedelta(hours=1),
        completed_at=datetime.now(timezone.utc) - timedelta(minutes=30),
        updated_at=datetime.now(timezone.utc) - timedelta(minutes=30),
        play_duration_ms=1800000,  # 30 minutes
        score=1200,
        final_score=1200
    )


@pytest.fixture
def abandoned_session_data(test_utils):
    """Abandoned game session data"""
    return test_utils.create_mock_game_session(
        status="abandoned",
        started_at=datetime.now(timezone.utc) - timedelta(hours=2),
        updated_at=datetime.now(timezone.utc) - timedelta(hours=1, minutes=55),
        play_duration_ms=300000,  # 5 minutes before abandonment
        score=150
    )


@pytest.fixture
def cross_device_session_data(test_utils):
    """Cross-device game session data"""
    return test_utils.create_mock_game_session(
        status="active",
        sync_version=3,
        device_info={
            "platform": "mobile",
            "device_type": "smartphone",
            "user_agent": "GoodPlay Mobile App 1.2.0",
            "app_version": "1.2.0",
            "os": "iOS 15.0",
            "screen_resolution": "1170x2532"
        },
        started_at=datetime.now(timezone.utc) - timedelta(hours=1),
        updated_at=datetime.now(timezone.utc) - timedelta(minutes=2),
        play_duration_ms=3300000,  # 55 minutes
        last_sync_at=datetime.now(timezone.utc) - timedelta(minutes=2)
    )


@pytest.fixture
def session_with_conflict(test_utils):
    """Game session data with sync conflict"""
    return test_utils.create_mock_game_session(
        status="active",
        sync_version=5,
        has_conflict=True,
        conflict_resolution="pending",
        conflicted_fields=["score", "game_state"],
        device_info={
            "platform": "web",
            "device_type": "tablet",
            "user_agent": "Chrome/91.0.4472.124",
            "app_version": "1.0.0"
        }
    )


@pytest.fixture
def multiple_sessions_same_user(test_utils):
    """Multiple sessions for the same user"""
    user_id = test_utils.get_unique_id()

    return [
        test_utils.create_mock_game_session(
            user_id=user_id,
            status="completed",
            score=800,
            completed_at=datetime.now(timezone.utc) - timedelta(days=1)
        ),
        test_utils.create_mock_game_session(
            user_id=user_id,
            status="active",
            score=400,
            started_at=datetime.now(timezone.utc) - timedelta(hours=2)
        ),
        test_utils.create_mock_game_session(
            user_id=user_id,
            status="paused",
            score=600,
            paused_at=datetime.now(timezone.utc) - timedelta(hours=4)
        )
    ]


@pytest.fixture
def high_score_session_data(test_utils):
    """High score game session data"""
    return test_utils.create_mock_game_session(
        status="completed",
        score=9999,
        final_score=9999,
        achievements_unlocked=["high_score", "perfect_game"],
        play_duration_ms=2400000,  # 40 minutes
        performance_metrics={
            "accuracy": 98.5,
            "speed": 85.2,
            "consistency": 92.1
        }
    )


@pytest.fixture
def game_state_data():
    """Sample game state data"""
    return {
        "level": 5,
        "lives": 3,
        "power_ups": ["shield", "double_score"],
        "inventory": {
            "coins": 150,
            "gems": 25,
            "keys": 3
        },
        "progress": {
            "checkpoints": [1, 3, 5],
            "completion_percentage": 75.5,
            "unlocked_areas": ["forest", "cave", "mountain"]
        },
        "settings": {
            "difficulty": "medium",
            "sound_volume": 0.8,
            "music_volume": 0.6
        }
    }


@pytest.fixture
def device_info_desktop():
    """Desktop device info"""
    return {
        "platform": "web",
        "device_type": "desktop",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "app_version": "1.0.0",
        "os": "Windows 10",
        "screen_resolution": "1920x1080",
        "browser": "Chrome 91.0.4472.124"
    }


@pytest.fixture
def device_info_mobile():
    """Mobile device info"""
    return {
        "platform": "mobile",
        "device_type": "smartphone",
        "user_agent": "GoodPlay Mobile App 1.2.0",
        "app_version": "1.2.0",
        "os": "Android 11",
        "screen_resolution": "1080x2400",
        "device_model": "Samsung Galaxy S21"
    }


@pytest.fixture
def device_info_tablet():
    """Tablet device info"""
    return {
        "platform": "mobile",
        "device_type": "tablet",
        "user_agent": "GoodPlay Mobile App 1.2.0",
        "app_version": "1.2.0",
        "os": "iPadOS 15.0",
        "screen_resolution": "2048x2732",
        "device_model": "iPad Pro 12.9"
    }