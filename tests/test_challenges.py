"""Test module for challenges functionality."""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from app.games.challenges.models.challenge import Challenge
from app.games.challenges.repositories.challenge_repository import ChallengeRepository
from app.games.challenges.services.challenge_service import ChallengeService
from app.games.challenges.services.matchmaking_service import MatchmakingService
from app.core.models.response import Response


class TestChallenge:
    """Test Challenge model"""

    def test_create_1v1_challenge(self):
        """Test creating 1v1 challenge"""
        challenge = Challenge.create_1v1_challenge(
            creator_id="user1",
            opponent_id="user2",
            game_id="tetris",
            difficulty="medium"
        )

        assert challenge.challenge_type == "1v1"
        assert challenge.creator_id == "user1"
        assert challenge.game_id == "tetris"
        assert challenge.difficulty == "medium"
        assert len(challenge.participants) == 2
        assert challenge.status == "pending"

    def test_create_nvn_challenge(self):
        """Test creating NvN challenge"""
        participants = ["user1", "user2", "user3", "user4"]
        challenge = Challenge.create_nvn_challenge(
            creator_id="user1",
            participant_ids=participants,
            game_id="snake",
            max_participants=4
        )

        assert challenge.challenge_type == "NvN"
        assert challenge.creator_id == "user1"
        assert challenge.game_id == "snake"
        assert challenge.max_participants == 4
        assert len(challenge.participants) == 4
        assert challenge.status == "pending"

    def test_create_cross_game_challenge(self):
        """Test creating cross-game challenge"""
        participants = ["user1", "user2"]
        challenge = Challenge.create_cross_game_challenge(
            creator_id="user1",
            participant_ids=participants,
            game_ids=["tetris", "snake"]
        )

        assert challenge.challenge_type == "cross_game"
        assert challenge.creator_id == "user1"
        assert challenge.game_ids == ["tetris", "snake"]
        assert len(challenge.participants) == 2
        assert challenge.status == "pending"

    def test_start_challenge(self):
        """Test starting a challenge"""
        challenge = Challenge.create_1v1_challenge("user1", "user2", "tetris")
        challenge.start_challenge()

        assert challenge.status == "active"
        assert challenge.started_at is not None

    def test_complete_challenge(self):
        """Test completing a challenge"""
        challenge = Challenge.create_1v1_challenge("user1", "user2", "tetris")
        challenge.start_challenge()

        results = {
            "user1": {"score": 1000, "position": 1},
            "user2": {"score": 800, "position": 2}
        }
        challenge.complete_challenge(results)

        assert challenge.status == "completed"
        assert challenge.completed_at is not None
        assert challenge.results == results
        assert challenge.winner_id == "user1"

    def test_cancel_challenge(self):
        """Test canceling a challenge"""
        challenge = Challenge.create_1v1_challenge("user1", "user2", "tetris")
        challenge.cancel_challenge("user1")

        assert challenge.status == "cancelled"
        assert challenge.cancelled_by == "user1"

    def test_is_participant(self):
        """Test checking if user is participant"""
        challenge = Challenge.create_1v1_challenge("user1", "user2", "tetris")

        assert challenge.is_participant("user1") is True
        assert challenge.is_participant("user2") is True
        assert challenge.is_participant("user3") is False

    def test_get_opponent_1v1(self):
        """Test getting opponent in 1v1 challenge"""
        challenge = Challenge.create_1v1_challenge("user1", "user2", "tetris")

        assert challenge.get_opponent("user1") == "user2"
        assert challenge.get_opponent("user2") == "user1"
        assert challenge.get_opponent("user3") is None

    def test_add_participant_nvn(self):
        """Test adding participant to NvN challenge"""
        challenge = Challenge.create_nvn_challenge(
            creator_id="user1",
            participant_ids=["user1"],
            game_id="snake",
            max_participants=4
        )

        result = challenge.add_participant("user2")
        assert result is True
        assert "user2" in challenge.participants

    def test_add_participant_full_challenge(self):
        """Test adding participant to full challenge"""
        participants = ["user1", "user2", "user3", "user4"]
        challenge = Challenge.create_nvn_challenge(
            creator_id="user1",
            participant_ids=participants,
            game_id="snake",
            max_participants=4
        )

        result = challenge.add_participant("user5")
        assert result is False
        assert "user5" not in challenge.participants

    def test_remove_participant(self):
        """Test removing participant from challenge"""
        challenge = Challenge.create_nvn_challenge(
            creator_id="user1",
            participant_ids=["user1", "user2", "user3"],
            game_id="snake",
            max_participants=4
        )

        result = challenge.remove_participant("user2")
        assert result is True
        assert "user2" not in challenge.participants

    def test_to_dict_and_from_dict(self):
        """Test serialization and deserialization"""
        challenge = Challenge.create_1v1_challenge("user1", "user2", "tetris", "hard")

        challenge_dict = challenge.to_dict()
        restored_challenge = Challenge.from_dict(challenge_dict)

        assert restored_challenge.challenge_id == challenge.challenge_id
        assert restored_challenge.challenge_type == challenge.challenge_type
        assert restored_challenge.creator_id == challenge.creator_id
        assert restored_challenge.game_id == challenge.game_id
        assert restored_challenge.difficulty == challenge.difficulty


class TestChallengeRepository:
    """Test ChallengeRepository"""

    @pytest.fixture
    def mock_db(self):
        """Mock database"""
        return Mock()

    @pytest.fixture
    def challenge_repo(self, mock_db):
        """Create ChallengeRepository instance with mocked database"""
        with patch('app.games.challenges.repositories.challenge_repository.get_db', return_value=mock_db):
            return ChallengeRepository()

    def test_create_challenge(self, challenge_repo, mock_db):
        """Test creating a challenge"""
        challenge = Challenge.create_1v1_challenge("user1", "user2", "tetris")
        mock_db.challenges.insert_one.return_value.inserted_id = "test_id"

        success, message, result = challenge_repo.create_challenge(challenge)

        assert success is True
        assert "Challenge created successfully" in message
        assert result["challenge_id"] == challenge.challenge_id
        mock_db.challenges.insert_one.assert_called_once()

    def test_get_challenge_by_id_found(self, challenge_repo, mock_db):
        """Test getting challenge by ID when found"""
        challenge_data = {
            "challenge_id": "test_challenge",
            "challenge_type": "1v1",
            "creator_id": "user1",
            "game_id": "tetris",
            "participants": ["user1", "user2"],
            "status": "pending",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        mock_db.challenges.find_one.return_value = challenge_data

        success, message, result = challenge_repo.get_challenge_by_id("test_challenge")

        assert success is True
        assert result.challenge_id == "test_challenge"
        mock_db.challenges.find_one.assert_called_once_with({"challenge_id": "test_challenge"})

    def test_get_challenge_by_id_not_found(self, challenge_repo, mock_db):
        """Test getting challenge by ID when not found"""
        mock_db.challenges.find_one.return_value = None

        success, message, result = challenge_repo.get_challenge_by_id("nonexistent")

        assert success is False
        assert "Challenge not found" in message
        assert result is None

    def test_get_user_challenges(self, challenge_repo, mock_db):
        """Test getting user challenges"""
        challenge_data = [{
            "challenge_id": "test_challenge",
            "challenge_type": "1v1",
            "creator_id": "user1",
            "game_id": "tetris",
            "participants": ["user1", "user2"],
            "status": "pending",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }]
        mock_db.challenges.find.return_value.sort.return_value.limit.return_value = challenge_data

        success, message, result = challenge_repo.get_user_challenges("user1", limit=10)

        assert success is True
        assert len(result) == 1
        assert result[0].challenge_id == "test_challenge"
        mock_db.challenges.find.assert_called_once()

    def test_update_challenge(self, challenge_repo, mock_db):
        """Test updating a challenge"""
        mock_db.challenges.update_one.return_value.modified_count = 1

        success, message, result = challenge_repo.update_challenge("test_challenge", {"status": "active"})

        assert success is True
        assert "Challenge updated successfully" in message
        mock_db.challenges.update_one.assert_called_once()

    def test_get_pending_challenges(self, challenge_repo, mock_db):
        """Test getting pending challenges"""
        challenge_data = [{
            "challenge_id": "test_challenge",
            "challenge_type": "1v1",
            "creator_id": "user1",
            "game_id": "tetris",
            "participants": ["user1", "user2"],
            "status": "pending",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }]
        mock_db.challenges.find.return_value.sort.return_value.limit.return_value = challenge_data

        success, message, result = challenge_repo.get_pending_challenges(limit=10)

        assert success is True
        assert len(result) == 1
        assert result[0].status == "pending"
        mock_db.challenges.find.assert_called_once_with({"status": "pending"})


class TestChallengeService:
    """Test ChallengeService service"""

    @pytest.fixture
    def mock_repo(self):
        """Mock repository"""
        return Mock()

    @pytest.fixture
    def mock_matchmaker(self):
        """Mock matchmaker"""
        return Mock()

    @pytest.fixture
    def challenge_service(self, mock_repo, mock_matchmaker):
        """Create ChallengeService instance with mocked dependencies"""
        with patch('app.games.challenges.services.challenge_service.ChallengeRepository', return_value=mock_repo), \
             patch('app.games.challenges.services.challenge_service.MatchmakingService', return_value=mock_matchmaker):
            return ChallengeService()

    def test_create_1v1_challenge(self, challenge_service, mock_repo):
        """Test creating 1v1 challenge"""
        mock_repo.create_challenge.return_value = (True, "Challenge created successfully", {"challenge_id": "test"})

        success, message, result = challenge_service.create_1v1_challenge(
            creator_id="user1",
            opponent_id="user2",
            game_id="tetris",
            difficulty="medium"
        )

        assert success is True
        assert "1v1 challenge created successfully" in message
        mock_repo.create_challenge.assert_called_once()

    def test_create_nvn_challenge(self, challenge_service, mock_repo):
        """Test creating NvN challenge"""
        mock_repo.create_challenge.return_value = (True, "Challenge created successfully", {"challenge_id": "test"})

        participants = ["user1", "user2", "user3"]
        success, message, result = challenge_service.create_nvn_challenge(
            creator_id="user1",
            participant_ids=participants,
            game_id="snake",
            max_participants=4
        )

        assert success is True
        assert "NvN challenge created successfully" in message
        mock_repo.create_challenge.assert_called_once()

    def test_create_cross_game_challenge(self, challenge_service, mock_repo):
        """Test creating cross-game challenge"""
        mock_repo.create_challenge.return_value = (True, "Challenge created successfully", {"challenge_id": "test"})

        participants = ["user1", "user2"]
        game_ids = ["tetris", "snake"]
        success, message, result = challenge_service.create_cross_game_challenge(
            creator_id="user1",
            participant_ids=participants,
            game_ids=game_ids
        )

        assert success is True
        assert "Cross-game challenge created successfully" in message
        mock_repo.create_challenge.assert_called_once()

    def test_join_challenge(self, challenge_service, mock_repo):
        """Test joining a challenge"""
        challenge = Challenge.create_nvn_challenge(
            creator_id="user1",
            participant_ids=["user1"],
            game_id="snake",
            max_participants=4
        )
        mock_repo.get_challenge_by_id.return_value = (True, "Challenge found", challenge)
        mock_repo.update_challenge.return_value = (True, "Challenge updated successfully", None)

        success, message, result = challenge_service.join_challenge("test_challenge", "user2")

        assert success is True
        assert "Successfully joined challenge" in message
        mock_repo.update_challenge.assert_called_once()

    def test_join_challenge_already_full(self, challenge_service, mock_repo):
        """Test joining a full challenge"""
        participants = ["user1", "user2", "user3", "user4"]
        challenge = Challenge.create_nvn_challenge(
            creator_id="user1",
            participant_ids=participants,
            game_id="snake",
            max_participants=4
        )
        mock_repo.get_challenge_by_id.return_value = (True, "Challenge found", challenge)

        success, message, result = challenge_service.join_challenge("test_challenge", "user5")

        assert success is False
        assert "Challenge is full" in message

    def test_start_challenge(self, challenge_service, mock_repo):
        """Test starting a challenge"""
        challenge = Challenge.create_1v1_challenge("user1", "user2", "tetris")
        mock_repo.get_challenge_by_id.return_value = (True, "Challenge found", challenge)
        mock_repo.update_challenge.return_value = (True, "Challenge updated successfully", None)

        success, message, result = challenge_service.start_challenge("test_challenge", "user1")

        assert success is True
        assert "Challenge started successfully" in message
        mock_repo.update_challenge.assert_called_once()

    def test_start_challenge_not_creator(self, challenge_service, mock_repo):
        """Test starting challenge by non-creator"""
        challenge = Challenge.create_1v1_challenge("user1", "user2", "tetris")
        mock_repo.get_challenge_by_id.return_value = (True, "Challenge found", challenge)

        success, message, result = challenge_service.start_challenge("test_challenge", "user3")

        assert success is False
        assert "Only challenge creator can start" in message

    def test_complete_challenge(self, challenge_service, mock_repo):
        """Test completing a challenge"""
        challenge = Challenge.create_1v1_challenge("user1", "user2", "tetris")
        challenge.start_challenge()
        mock_repo.get_challenge_by_id.return_value = (True, "Challenge found", challenge)
        mock_repo.update_challenge.return_value = (True, "Challenge updated successfully", None)

        results = {
            "user1": {"score": 1000, "position": 1},
            "user2": {"score": 800, "position": 2}
        }

        success, message, result = challenge_service.complete_challenge("test_challenge", results)

        assert success is True
        assert "Challenge completed successfully" in message
        assert result["winner_id"] == "user1"
        mock_repo.update_challenge.assert_called_once()

    def test_cancel_challenge(self, challenge_service, mock_repo):
        """Test canceling a challenge"""
        challenge = Challenge.create_1v1_challenge("user1", "user2", "tetris")
        mock_repo.get_challenge_by_id.return_value = (True, "Challenge found", challenge)
        mock_repo.update_challenge.return_value = (True, "Challenge updated successfully", None)

        success, message, result = challenge_service.cancel_challenge("test_challenge", "user1")

        assert success is True
        assert "Challenge cancelled successfully" in message
        mock_repo.update_challenge.assert_called_once()

    def test_get_user_challenges(self, challenge_service, mock_repo):
        """Test getting user challenges"""
        challenges = [Challenge.create_1v1_challenge("user1", "user2", "tetris")]
        mock_repo.get_user_challenges.return_value = (True, "Success", challenges)

        success, message, result = challenge_service.get_user_challenges("user1", limit=10)

        assert success is True
        assert len(result) == 1
        mock_repo.get_user_challenges.assert_called_once_with("user1", limit=10)

    def test_find_match_auto(self, challenge_service, mock_matchmaker):
        """Test automatic matchmaking"""
        mock_matchmaker.find_match.return_value = (True, "Match found", {"opponent_id": "user2"})

        success, message, result = challenge_service.find_match_auto("user1", "tetris", "medium")

        assert success is True
        assert "Match found" in message
        assert result["opponent_id"] == "user2"
        mock_matchmaker.find_match.assert_called_once()


class TestMatchmakingService:
    """Test MatchmakingService service"""

    @pytest.fixture
    def mock_user_repo(self):
        """Mock user repository"""
        return Mock()

    @pytest.fixture
    def mock_session_repo(self):
        """Mock session repository"""
        return Mock()

    @pytest.fixture
    def matchmaker(self, mock_user_repo, mock_session_repo):
        """Create MatchmakingService instance with mocked dependencies"""
        with patch('app.games.challenges.services.matchmaking_service.UserRepository', return_value=mock_user_repo), \
             patch('app.games.challenges.services.matchmaking_service.GameSessionRepository', return_value=mock_session_repo):
            return MatchmakingService()

    def test_find_match_success(self, matchmaker, mock_user_repo, mock_session_repo):
        """Test successful match finding"""
        # Mock available users
        mock_user_repo.find_users_by_criteria.return_value = (True, "Success", [
            {"_id": "user2", "username": "player2", "elo_rating": 1200}
        ])

        # Mock recent sessions for skill assessment
        mock_session_repo.get_recent_sessions_by_game.return_value = (True, "Success", [])

        success, message, result = matchmaker.find_match("user1", "tetris", "medium")

        assert success is True
        assert "Match found" in message
        assert result["opponent_id"] == "user2"

    def test_find_match_no_opponents(self, matchmaker, mock_user_repo):
        """Test match finding with no available opponents"""
        mock_user_repo.find_users_by_criteria.return_value = (True, "Success", [])

        success, message, result = matchmaker.find_match("user1", "tetris", "medium")

        assert success is False
        assert "No suitable opponents found" in message

    def test_calculate_compatibility_score_perfect_match(self, matchmaker):
        """Test compatibility calculation for perfect match"""
        user_stats = {"elo_rating": 1200, "games_played": 100}
        opponent_stats = {"elo_rating": 1200, "games_played": 100}

        score = matchmaker._calculate_compatibility_score(user_stats, opponent_stats)

        assert score > 0.8  # Should be high compatibility

    def test_calculate_compatibility_score_skill_gap(self, matchmaker):
        """Test compatibility calculation with skill gap"""
        user_stats = {"elo_rating": 1200, "games_played": 100}
        opponent_stats = {"elo_rating": 1600, "games_played": 100}

        score = matchmaker._calculate_compatibility_score(user_stats, opponent_stats)

        assert score < 0.5  # Should be lower compatibility due to skill gap

    def test_get_user_game_stats(self, matchmaker, mock_session_repo):
        """Test getting user game statistics"""
        mock_sessions = [
            {"final_score": 1000, "session_outcome": "win"},
            {"final_score": 800, "session_outcome": "loss"}
        ]
        mock_session_repo.get_recent_sessions_by_game.return_value = (True, "Success", mock_sessions)

        stats = matchmaker._get_user_game_stats("user1", "tetris")

        assert stats["games_played"] == 2
        assert stats["wins"] == 1
        assert stats["win_rate"] == 0.5
        assert stats["avg_score"] == 900