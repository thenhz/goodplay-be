"""Test module for teams functionality."""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from app.games.teams.models.global_team import GlobalTeam
from app.games.teams.models.team_tournament import TeamTournament
from app.games.teams.repositories.global_team_repository import GlobalTeamRepository
from app.games.teams.repositories.team_tournament_repository import TeamTournamentRepository
from app.games.teams.services.team_manager import TeamManager
from app.games.teams.services.tournament_engine import TournamentEngine
from app.core.utils.responses import success_response, error_response


class TestGlobalTeam:
    """Test GlobalTeam model"""

    def test_create_default_teams(self):
        """Test creating default teams"""
        teams = GlobalTeam.create_default_teams()

        assert len(teams) == 4
        team_names = [team.name for team in teams]
        assert "Fire Dragons" in team_names
        assert "Ice Phoenix" in team_names
        assert "Earth Guardians" in team_names
        assert "Storm Eagles" in team_names

    def test_add_score(self):
        """Test adding score to team"""
        team = GlobalTeam.create_default_teams()[0]
        initial_score = team.total_score

        team.add_score(100, "user1")

        assert team.total_score == initial_score + 100
        assert len(team.score_history) == 1
        assert team.score_history[0]["user_id"] == "user1"
        assert team.score_history[0]["points"] == 100

    def test_add_member(self):
        """Test adding member to team"""
        team = GlobalTeam.create_default_teams()[0]
        initial_count = team.member_count

        team.add_member("user1")

        assert team.member_count == initial_count + 1
        assert "user1" in team.member_ids

    def test_remove_member(self):
        """Test removing member from team"""
        team = GlobalTeam.create_default_teams()[0]
        team.add_member("user1")
        initial_count = team.member_count

        result = team.remove_member("user1")

        assert result is True
        assert team.member_count == initial_count - 1
        assert "user1" not in team.member_ids

    def test_remove_nonexistent_member(self):
        """Test removing nonexistent member"""
        team = GlobalTeam.create_default_teams()[0]

        result = team.remove_member("nonexistent")

        assert result is False

    def test_get_average_score_per_member(self):
        """Test calculating average score per member"""
        team = GlobalTeam.create_default_teams()[0]
        team.add_member("user1")
        team.add_member("user2")
        team.add_score(200, "user1")

        avg_score = team.get_average_score_per_member()

        assert avg_score == 100.0  # 200 points / 2 members

    def test_get_average_score_per_member_no_members(self):
        """Test average score with no members"""
        team = GlobalTeam.create_default_teams()[0]

        avg_score = team.get_average_score_per_member()

        assert avg_score == 0.0

    def test_to_dict_and_from_dict(self):
        """Test serialization and deserialization"""
        team = GlobalTeam.create_default_teams()[0]
        team.add_member("user1")
        team.add_score(100, "user1")

        team_dict = team.to_dict()
        restored_team = GlobalTeam.from_dict(team_dict)

        assert restored_team.team_id == team.team_id
        assert restored_team.name == team.name
        assert restored_team.total_score == team.total_score
        assert restored_team.member_count == team.member_count
        assert len(restored_team.score_history) == len(team.score_history)


class TestTeamTournament:
    """Test TeamTournament model"""

    def test_create_seasonal_war(self):
        """Test creating seasonal war tournament"""
        team_ids = ["team1", "team2", "team3"]
        tournament = TeamTournament.create_seasonal_war(
            "Summer War",
            team_ids,
            30,
            "admin1"
        )

        assert tournament.tournament_type == "seasonal_war"
        assert tournament.name == "Summer War"
        assert tournament.duration_days == 30
        assert tournament.participating_teams == team_ids
        assert tournament.status == "created"
        assert tournament.created_by == "admin1"

    def test_start_tournament(self):
        """Test starting a tournament"""
        team_ids = ["team1", "team2"]
        tournament = TeamTournament.create_seasonal_war("Test War", team_ids, 30, "admin1")

        tournament.start_tournament()

        assert tournament.status == "active"
        assert tournament.started_at is not None
        assert tournament.end_date is not None

    def test_complete_tournament(self):
        """Test completing a tournament"""
        team_ids = ["team1", "team2"]
        tournament = TeamTournament.create_seasonal_war("Test War", team_ids, 30, "admin1")
        tournament.start_tournament()

        leaderboard = [
            {"team_id": "team1", "score": 1000, "position": 1},
            {"team_id": "team2", "score": 800, "position": 2}
        ]
        tournament.complete_tournament(leaderboard)

        assert tournament.status == "completed"
        assert tournament.completed_at is not None
        assert tournament.final_results == leaderboard
        assert tournament.winner_team_id == "team1"

    def test_cancel_tournament(self):
        """Test canceling a tournament"""
        team_ids = ["team1", "team2"]
        tournament = TeamTournament.create_seasonal_war("Test War", team_ids, 30, "admin1")

        tournament.cancel_tournament("admin1")

        assert tournament.status == "cancelled"
        assert tournament.cancelled_by == "admin1"

    def test_is_active(self):
        """Test checking if tournament is active"""
        team_ids = ["team1", "team2"]
        tournament = TeamTournament.create_seasonal_war("Test War", team_ids, 30, "admin1")

        assert tournament.is_active() is False

        tournament.start_tournament()
        assert tournament.is_active() is True

        tournament.complete_tournament([])
        assert tournament.is_active() is False

    def test_is_expired(self):
        """Test checking if tournament is expired"""
        team_ids = ["team1", "team2"]
        tournament = TeamTournament.create_seasonal_war("Test War", team_ids, 1, "admin1")
        tournament.start_tournament()

        # Set end date to past
        tournament.end_date = datetime.utcnow() - timedelta(hours=1)

        assert tournament.is_expired() is True

    def test_to_dict_and_from_dict(self):
        """Test serialization and deserialization"""
        team_ids = ["team1", "team2"]
        tournament = TeamTournament.create_seasonal_war("Test War", team_ids, 30, "admin1")

        tournament_dict = tournament.to_dict()
        restored_tournament = TeamTournament.from_dict(tournament_dict)

        assert restored_tournament.tournament_id == tournament.tournament_id
        assert restored_tournament.name == tournament.name
        assert restored_tournament.tournament_type == tournament.tournament_type
        assert restored_tournament.duration_days == tournament.duration_days


class TestGlobalTeamRepository:
    """Test GlobalTeamRepository"""

    @pytest.fixture
    def mock_db(self):
        """Mock database"""
        return Mock()

    @pytest.fixture
    def team_repo(self, mock_db):
        """Create GlobalTeamRepository instance with mocked database"""
        with patch('app.games.teams.repositories.global_team_repository.get_db', return_value=mock_db):
            return GlobalTeamRepository()

    def test_create_team(self, team_repo, mock_db):
        """Test creating a team"""
        team = GlobalTeam.create_default_teams()[0]
        mock_db.global_teams.insert_one.return_value.inserted_id = "test_id"

        success, message, result = team_repo.create_team(team)

        assert success is True
        assert "Team created successfully" in message
        assert result["team_id"] == team.team_id
        mock_db.global_teams.insert_one.assert_called_once()

    def test_get_team_by_id_found(self, team_repo, mock_db):
        """Test getting team by ID when found"""
        team_data = {
            "team_id": "test_team",
            "name": "Test Team",
            "total_score": 0,
            "member_count": 0,
            "member_ids": [],
            "score_history": [],
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        mock_db.global_teams.find_one.return_value = team_data

        success, message, result = team_repo.get_team_by_id("test_team")

        assert success is True
        assert result.team_id == "test_team"
        mock_db.global_teams.find_one.assert_called_once_with({"team_id": "test_team"})

    def test_get_all_teams(self, team_repo, mock_db):
        """Test getting all teams"""
        team_data = [{
            "team_id": "test_team",
            "name": "Test Team",
            "total_score": 1000,
            "member_count": 10,
            "member_ids": [],
            "score_history": [],
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }]
        mock_db.global_teams.find.return_value.sort.return_value = team_data

        success, message, result = team_repo.get_all_teams()

        assert success is True
        assert len(result) == 1
        assert result[0].team_id == "test_team"

    def test_update_team(self, team_repo, mock_db):
        """Test updating a team"""
        mock_db.global_teams.update_one.return_value.modified_count = 1

        success, message, result = team_repo.update_team("test_team", {"total_score": 1000})

        assert success is True
        assert "Team updated successfully" in message
        mock_db.global_teams.update_one.assert_called_once()

    def test_get_team_leaderboard(self, team_repo, mock_db):
        """Test getting team leaderboard"""
        team_data = [
            {
                "team_id": "team1",
                "name": "Team 1",
                "total_score": 1000,
                "member_count": 10,
                "member_ids": [],
                "score_history": [],
                "is_active": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            },
            {
                "team_id": "team2",
                "name": "Team 2",
                "total_score": 800,
                "member_count": 8,
                "member_ids": [],
                "score_history": [],
                "is_active": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        ]
        mock_db.global_teams.find.return_value.sort.return_value.limit.return_value = team_data

        success, message, result = team_repo.get_team_leaderboard(10)

        assert success is True
        assert len(result) == 2
        assert result[0].total_score >= result[1].total_score  # Should be sorted by score


class TestTeamManager:
    """Test TeamManager service"""

    @pytest.fixture
    def mock_team_repo(self):
        """Mock team repository"""
        return Mock()

    @pytest.fixture
    def mock_user_repo(self):
        """Mock user repository"""
        return Mock()

    @pytest.fixture
    def mock_scorer(self):
        """Mock universal scorer"""
        return Mock()

    @pytest.fixture
    def team_manager(self, mock_team_repo, mock_user_repo, mock_scorer):
        """Create TeamManager instance with mocked dependencies"""
        with patch('app.games.teams.services.team_manager.GlobalTeamRepository', return_value=mock_team_repo), \
             patch('app.games.teams.services.team_manager.UserRepository', return_value=mock_user_repo), \
             patch('app.games.teams.services.team_manager.UniversalScorer', return_value=mock_scorer):
            return TeamManager()

    def test_initialize_teams_first_time(self, team_manager, mock_team_repo):
        """Test initializing teams for the first time"""
        mock_team_repo.get_all_teams.return_value = (True, "Success", [])
        mock_team_repo.create_team.return_value = (True, "Team created successfully", {"team_id": "test"})

        success, message, result = team_manager.initialize_teams()

        assert success is True
        assert "Teams initialized successfully" in message
        assert result["teams_created"] == 4
        assert mock_team_repo.create_team.call_count == 4

    def test_initialize_teams_already_exist(self, team_manager, mock_team_repo):
        """Test initializing teams when they already exist"""
        existing_teams = GlobalTeam.create_default_teams()
        mock_team_repo.get_all_teams.return_value = (True, "Success", existing_teams)

        success, message, result = team_manager.initialize_teams()

        assert success is True
        assert "Teams already initialized" in message
        mock_team_repo.create_team.assert_not_called()

    def test_assign_user_to_team_auto(self, team_manager, mock_team_repo, mock_user_repo):
        """Test auto-assigning user to team"""
        teams = GlobalTeam.create_default_teams()
        mock_team_repo.get_all_teams.return_value = (True, "Success", teams)
        mock_team_repo.update_team.return_value = (True, "Team updated successfully", None)
        mock_user_repo.update_user.return_value = (True, "User updated successfully", None)

        success, message, result = team_manager.assign_user_to_team("user1")

        assert success is True
        assert "User assigned to team successfully" in message
        assert "team_id" in result
        mock_team_repo.update_team.assert_called_once()
        mock_user_repo.update_user.assert_called_once()

    def test_assign_user_to_specific_team(self, team_manager, mock_team_repo, mock_user_repo):
        """Test assigning user to specific team"""
        team = GlobalTeam.create_default_teams()[0]
        mock_team_repo.get_team_by_id.return_value = (True, "Team found", team)
        mock_team_repo.update_team.return_value = (True, "Team updated successfully", None)
        mock_user_repo.update_user.return_value = (True, "User updated successfully", None)

        success, message, result = team_manager.assign_user_to_team("user1", team.team_id)

        assert success is True
        assert "User assigned to team successfully" in message
        assert result["team_id"] == team.team_id

    def test_assign_user_to_nonexistent_team(self, team_manager, mock_team_repo):
        """Test assigning user to nonexistent team"""
        mock_team_repo.get_team_by_id.return_value = (False, "Team not found", None)

        success, message, result = team_manager.assign_user_to_team("user1", "nonexistent")

        assert success is False
        assert "Team not found" in message

    def test_remove_user_from_team(self, team_manager, mock_team_repo, mock_user_repo):
        """Test removing user from team"""
        team = GlobalTeam.create_default_teams()[0]
        team.add_member("user1")
        mock_user_repo.get_user_by_id.return_value = (True, "User found", {"team_id": team.team_id})
        mock_team_repo.get_team_by_id.return_value = (True, "Team found", team)
        mock_team_repo.update_team.return_value = (True, "Team updated successfully", None)
        mock_user_repo.update_user.return_value = (True, "User updated successfully", None)

        success, message, result = team_manager.remove_user_from_team("user1")

        assert success is True
        assert "User removed from team successfully" in message
        mock_team_repo.update_team.assert_called_once()
        mock_user_repo.update_user.assert_called_once()

    def test_record_game_contribution(self, team_manager, mock_team_repo, mock_user_repo, mock_scorer):
        """Test recording game contribution"""
        team = GlobalTeam.create_default_teams()[0]
        team.add_member("user1")
        mock_user_repo.get_user_by_id.return_value = (True, "User found", {"team_id": team.team_id})
        mock_team_repo.get_team_by_id.return_value = (True, "Team found", team)
        mock_team_repo.update_team.return_value = (True, "Team updated successfully", None)
        mock_scorer.calculate_team_contribution.return_value = 150.0

        success, message, result = team_manager.record_game_contribution("user1", 100.0, "individual")

        assert success is True
        assert "Game contribution recorded successfully" in message
        assert result["contribution_points"] == 150.0
        mock_scorer.calculate_team_contribution.assert_called_once()
        mock_team_repo.update_team.assert_called_once()

    def test_balance_teams(self, team_manager, mock_team_repo, mock_user_repo):
        """Test balancing teams"""
        teams = GlobalTeam.create_default_teams()
        # Make teams unbalanced
        teams[0].member_count = 20
        teams[1].member_count = 5
        teams[2].member_count = 5
        teams[3].member_count = 5

        mock_team_repo.get_all_teams.return_value = (True, "Success", teams)
        mock_user_repo.find_users_by_team.return_value = (True, "Success", [
            {"_id": "user1"}, {"_id": "user2"}, {"_id": "user3"}
        ])
        mock_team_repo.update_team.return_value = (True, "Team updated successfully", None)
        mock_user_repo.update_user.return_value = (True, "User updated successfully", None)

        success, message, result = team_manager.balance_teams()

        assert success is True
        assert "Teams balanced successfully" in message
        assert result["users_moved"] >= 0

    def test_get_team_leaderboard(self, team_manager, mock_team_repo):
        """Test getting team leaderboard"""
        teams = GlobalTeam.create_default_teams()
        mock_team_repo.get_team_leaderboard.return_value = (True, "Success", teams)

        success, message, result = team_manager.get_team_leaderboard(10)

        assert success is True
        assert len(result) == 4
        mock_team_repo.get_team_leaderboard.assert_called_once_with(10)


class TestTournamentEngine:
    """Test TournamentEngine service"""

    @pytest.fixture
    def mock_tournament_repo(self):
        """Mock tournament repository"""
        return Mock()

    @pytest.fixture
    def mock_team_manager(self):
        """Mock team manager"""
        return Mock()

    @pytest.fixture
    def tournament_engine(self, mock_tournament_repo, mock_team_manager):
        """Create TournamentEngine instance with mocked dependencies"""
        with patch('app.games.teams.services.tournament_engine.TeamTournamentRepository', return_value=mock_tournament_repo), \
             patch('app.games.teams.services.tournament_engine.TeamManager', return_value=mock_team_manager):
            return TournamentEngine()

    def test_create_tournament(self, tournament_engine, mock_tournament_repo):
        """Test creating a tournament"""
        mock_tournament_repo.create_tournament.return_value = (True, "Tournament created successfully", {"tournament_id": "test"})

        team_ids = ["team1", "team2", "team3"]
        success, message, result = tournament_engine.create_tournament(
            tournament_type="seasonal_war",
            name="Test Tournament",
            duration_days=30,
            team_ids=team_ids,
            admin_user_id="admin1"
        )

        assert success is True
        assert "Tournament created successfully" in message
        mock_tournament_repo.create_tournament.assert_called_once()

    def test_start_tournament(self, tournament_engine, mock_tournament_repo, mock_team_manager):
        """Test starting a tournament"""
        tournament = TeamTournament.create_seasonal_war("Test Tournament", ["team1", "team2"], 30, "admin1")
        mock_tournament_repo.get_tournament_by_id.return_value = (True, "Tournament found", tournament)
        mock_tournament_repo.update_tournament.return_value = (True, "Tournament updated successfully", None)
        mock_team_manager.balance_teams.return_value = (True, "Teams balanced", {"users_moved": 5})

        success, message, result = tournament_engine.start_tournament("test_tournament", auto_assign_users=True)

        assert success is True
        assert "Tournament started successfully" in message
        mock_tournament_repo.update_tournament.assert_called_once()
        mock_team_manager.balance_teams.assert_called_once()

    def test_complete_tournament(self, tournament_engine, mock_tournament_repo):
        """Test completing a tournament"""
        tournament = TeamTournament.create_seasonal_war("Test Tournament", ["team1", "team2"], 30, "admin1")
        tournament.start_tournament()
        mock_tournament_repo.get_tournament_by_id.return_value = (True, "Tournament found", tournament)
        mock_tournament_repo.update_tournament.return_value = (True, "Tournament updated successfully", None)

        success, message, result = tournament_engine.complete_tournament("test_tournament")

        assert success is True
        assert "Tournament completed successfully" in message
        assert "winner_team_id" in result
        mock_tournament_repo.update_tournament.assert_called_once()

    def test_cancel_tournament(self, tournament_engine, mock_tournament_repo):
        """Test canceling a tournament"""
        tournament = TeamTournament.create_seasonal_war("Test Tournament", ["team1", "team2"], 30, "admin1")
        mock_tournament_repo.get_tournament_by_id.return_value = (True, "Tournament found", tournament)
        mock_tournament_repo.update_tournament.return_value = (True, "Tournament updated successfully", None)

        success, message, result = tournament_engine.cancel_tournament("test_tournament", "admin1")

        assert success is True
        assert "Tournament cancelled successfully" in message
        mock_tournament_repo.update_tournament.assert_called_once()

    def test_get_active_tournament(self, tournament_engine, mock_tournament_repo):
        """Test getting active tournament"""
        tournament = TeamTournament.create_seasonal_war("Active Tournament", ["team1", "team2"], 30, "admin1")
        tournament.start_tournament()
        mock_tournament_repo.get_active_tournament.return_value = (True, "Tournament found", tournament)

        success, message, result = tournament_engine.get_active_tournament()

        assert success is True
        assert result.status == "active"
        mock_tournament_repo.get_active_tournament.assert_called_once()

    def test_get_tournament_leaderboard(self, tournament_engine, mock_tournament_repo):
        """Test getting tournament leaderboard"""
        leaderboard_data = [
            {"team_id": "team1", "score": 1000, "position": 1},
            {"team_id": "team2", "score": 800, "position": 2}
        ]
        mock_tournament_repo.get_tournament_leaderboard.return_value = (True, "Success", leaderboard_data)

        success, message, result = tournament_engine.get_tournament_leaderboard("test_tournament")

        assert success is True
        assert len(result) == 2
        assert result[0]["position"] == 1
        mock_tournament_repo.get_tournament_leaderboard.assert_called_once()

    def test_end_expired_tournaments(self, tournament_engine, mock_tournament_repo):
        """Test ending expired tournaments"""
        expired_tournament = TeamTournament.create_seasonal_war("Expired Tournament", ["team1", "team2"], 1, "admin1")
        expired_tournament.start_tournament()
        expired_tournament.end_date = datetime.utcnow() - timedelta(hours=1)

        mock_tournament_repo.get_active_tournaments.return_value = (True, "Success", [expired_tournament])
        mock_tournament_repo.update_tournament.return_value = (True, "Tournament updated successfully", None)

        success, message, result = tournament_engine.end_expired_tournaments()

        assert success is True
        assert result["expired_tournaments"] == 1
        mock_tournament_repo.update_tournament.assert_called_once()