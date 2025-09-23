"""Test module for game modes functionality."""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from app.games.modes.models.game_mode import GameMode
from app.games.modes.repositories.game_mode_repository import GameModeRepository
from app.games.modes.services.mode_manager import ModeManager
from app.core.models.response import Response


class TestGameMode:
    """Test GameMode model"""

    def test_create_normal_mode(self):
        """Test creating normal mode"""
        mode = GameMode.create_default_normal_mode()

        assert mode.mode_id == "normal"
        assert mode.name == "Normal Play"
        assert mode.mode_type == "normal"
        assert mode.is_active is True
        assert mode.is_default is True

    def test_create_seasonal_war(self):
        """Test creating seasonal war mode"""
        start_date = datetime.utcnow()
        end_date = start_date + timedelta(days=30)

        mode = GameMode.create_seasonal_war("Summer War", start_date, end_date)

        assert mode.name == "Summer War"
        assert mode.mode_type == "seasonal_war"
        assert mode.start_date == start_date
        assert mode.end_date == end_date
        assert mode.is_active is False

    def test_create_special_event(self):
        """Test creating special event mode"""
        start_date = datetime.utcnow()
        end_date = start_date + timedelta(days=7)

        mode = GameMode.create_special_event("Holiday Tournament", start_date, end_date)

        assert mode.name == "Holiday Tournament"
        assert mode.mode_type == "special_event"
        assert mode.start_date == start_date
        assert mode.end_date == end_date

    def test_is_currently_available_active_mode(self):
        """Test if active mode is available"""
        mode = GameMode.create_default_normal_mode()
        assert mode.is_currently_available() is True

    def test_is_currently_available_scheduled_mode_active(self):
        """Test if scheduled mode in active period is available"""
        start_date = datetime.utcnow() - timedelta(hours=1)
        end_date = datetime.utcnow() + timedelta(hours=1)
        mode = GameMode.create_seasonal_war("Test War", start_date, end_date)
        mode.activate()

        assert mode.is_currently_available() is True

    def test_is_currently_available_scheduled_mode_future(self):
        """Test if scheduled mode in future is not available"""
        start_date = datetime.utcnow() + timedelta(hours=1)
        end_date = datetime.utcnow() + timedelta(hours=2)
        mode = GameMode.create_seasonal_war("Future War", start_date, end_date)

        assert mode.is_currently_available() is False

    def test_is_currently_available_scheduled_mode_past(self):
        """Test if scheduled mode in past is not available"""
        start_date = datetime.utcnow() - timedelta(hours=2)
        end_date = datetime.utcnow() - timedelta(hours=1)
        mode = GameMode.create_seasonal_war("Past War", start_date, end_date)
        mode.activate()

        assert mode.is_currently_available() is False

    def test_activate_mode(self):
        """Test activating a mode"""
        mode = GameMode.create_seasonal_war("Test War", None, None)
        assert mode.is_active is False

        mode.activate()
        assert mode.is_active is True

    def test_deactivate_mode(self):
        """Test deactivating a mode"""
        mode = GameMode.create_default_normal_mode()
        assert mode.is_active is True

        mode.deactivate()
        assert mode.is_active is False

    def test_to_dict_and_from_dict(self):
        """Test serialization and deserialization"""
        start_date = datetime.utcnow()
        end_date = start_date + timedelta(days=30)
        mode = GameMode.create_seasonal_war("Test War", start_date, end_date)

        mode_dict = mode.to_dict()
        restored_mode = GameMode.from_dict(mode_dict)

        assert restored_mode.mode_id == mode.mode_id
        assert restored_mode.name == mode.name
        assert restored_mode.mode_type == mode.mode_type
        assert restored_mode.start_date == mode.start_date
        assert restored_mode.end_date == mode.end_date


class TestModeRepository:
    """Test ModeRepository"""

    @pytest.fixture
    def mock_db(self):
        """Mock database"""
        return Mock()

    @pytest.fixture
    def mode_repo(self, mock_db):
        """Create GameModeRepository instance with mocked database"""
        with patch('app.games.modes.repositories.game_mode_repository.get_db', return_value=mock_db):
            return GameModeRepository()

    def test_create_mode(self, mode_repo, mock_db):
        """Test creating a mode"""
        mode = GameMode.create_default_normal_mode()
        mock_db.game_modes.insert_one.return_value.inserted_id = "test_id"

        success, message, result = mode_repo.create_mode(mode)

        assert success is True
        assert "Mode created successfully" in message
        assert result["mode_id"] == mode.mode_id
        mock_db.game_modes.insert_one.assert_called_once()

    def test_get_mode_by_id_found(self, mode_repo, mock_db):
        """Test getting mode by ID when found"""
        mode_data = {
            "mode_id": "test_mode",
            "name": "Test Mode",
            "mode_type": "normal",
            "is_active": True,
            "is_default": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        mock_db.game_modes.find_one.return_value = mode_data

        success, message, result = mode_repo.get_mode_by_id("test_mode")

        assert success is True
        assert result.mode_id == "test_mode"
        mock_db.game_modes.find_one.assert_called_once_with({"mode_id": "test_mode"})

    def test_get_mode_by_id_not_found(self, mode_repo, mock_db):
        """Test getting mode by ID when not found"""
        mock_db.game_modes.find_one.return_value = None

        success, message, result = mode_repo.get_mode_by_id("nonexistent")

        assert success is False
        assert "Mode not found" in message
        assert result is None

    def test_get_active_modes(self, mode_repo, mock_db):
        """Test getting active modes"""
        mode_data = [{
            "mode_id": "active_mode",
            "name": "Active Mode",
            "mode_type": "normal",
            "is_active": True,
            "is_default": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }]
        mock_db.game_modes.find.return_value.sort.return_value = mode_data

        success, message, result = mode_repo.get_active_modes()

        assert success is True
        assert len(result) == 1
        assert result[0].mode_id == "active_mode"
        mock_db.game_modes.find.assert_called_once_with({"is_active": True})

    def test_update_mode(self, mode_repo, mock_db):
        """Test updating a mode"""
        mock_db.game_modes.update_one.return_value.modified_count = 1

        success, message, result = mode_repo.update_mode("test_mode", {"name": "Updated Name"})

        assert success is True
        assert "Mode updated successfully" in message
        mock_db.game_modes.update_one.assert_called_once()

    def test_deactivate_mode(self, mode_repo, mock_db):
        """Test deactivating a mode"""
        mock_db.game_modes.update_one.return_value.modified_count = 1

        success, message, result = mode_repo.deactivate_mode("test_mode")

        assert success is True
        assert "Mode deactivated successfully" in message
        mock_db.game_modes.update_one.assert_called_once_with(
            {"mode_id": "test_mode"},
            {"$set": {"is_active": False, "updated_at": pytest.any(datetime)}}
        )


class TestModeManager:
    """Test ModeManager service"""

    @pytest.fixture
    def mock_repo(self):
        """Mock repository"""
        return Mock()

    @pytest.fixture
    def mode_manager(self, mock_repo):
        """Create ModeManager instance with mocked repository"""
        with patch('app.games.modes.services.mode_manager.GameModeRepository', return_value=mock_repo):
            return ModeManager()

    def test_initialize_system_first_time(self, mode_manager, mock_repo):
        """Test initializing system for the first time"""
        mock_repo.get_mode_by_id.return_value = (False, "Mode not found", None)
        mock_repo.create_mode.return_value = (True, "Mode created successfully", {"mode_id": "normal"})

        success, message, result = mode_manager.initialize_system()

        assert success is True
        assert "System initialized successfully" in message
        assert "normal" in result["default_modes"]
        mock_repo.create_mode.assert_called_once()

    def test_initialize_system_already_initialized(self, mode_manager, mock_repo):
        """Test initializing system when already initialized"""
        normal_mode = GameMode.create_default_normal_mode()
        mock_repo.get_mode_by_id.return_value = (True, "Mode found", normal_mode)

        success, message, result = mode_manager.initialize_system()

        assert success is True
        assert "System already initialized" in message
        mock_repo.create_mode.assert_not_called()

    def test_create_seasonal_war_mode(self, mode_manager, mock_repo):
        """Test creating seasonal war mode"""
        mock_repo.create_mode.return_value = (True, "Mode created successfully", {"mode_id": "test_war"})

        start_date = datetime.utcnow()
        end_date = start_date + timedelta(days=30)

        success, message, result = mode_manager.create_seasonal_war_mode(
            "Test War", start_date, end_date
        )

        assert success is True
        assert "Seasonal war mode created successfully" in message
        mock_repo.create_mode.assert_called_once()

    def test_create_special_event_mode(self, mode_manager, mock_repo):
        """Test creating special event mode"""
        mock_repo.create_mode.return_value = (True, "Mode created successfully", {"mode_id": "test_event"})

        start_date = datetime.utcnow()
        end_date = start_date + timedelta(days=7)

        success, message, result = mode_manager.create_special_event_mode(
            "Test Event", start_date, end_date
        )

        assert success is True
        assert "Special event mode created successfully" in message
        mock_repo.create_mode.assert_called_once()

    def test_get_available_modes(self, mode_manager, mock_repo):
        """Test getting available modes"""
        normal_mode = GameMode.create_default_normal_mode()
        seasonal_mode = GameMode.create_seasonal_war(
            "Active War",
            datetime.utcnow() - timedelta(hours=1),
            datetime.utcnow() + timedelta(hours=1)
        )
        seasonal_mode.activate()

        mock_repo.get_active_modes.return_value = (True, "Success", [normal_mode, seasonal_mode])

        success, message, result = mode_manager.get_available_modes()

        assert success is True
        assert len(result) == 2
        mock_repo.get_active_modes.assert_called_once()

    def test_activate_mode(self, mode_manager, mock_repo):
        """Test activating a mode"""
        mode = GameMode.create_seasonal_war("Test War", None, None)
        mock_repo.get_mode_by_id.return_value = (True, "Mode found", mode)
        mock_repo.update_mode.return_value = (True, "Mode updated successfully", None)

        success, message, result = mode_manager.activate_mode("test_war")

        assert success is True
        assert "Mode activated successfully" in message
        mock_repo.update_mode.assert_called_once()

    def test_deactivate_mode(self, mode_manager, mock_repo):
        """Test deactivating a mode"""
        mode = GameMode.create_seasonal_war("Test War", None, None)
        mode.activate()
        mock_repo.get_mode_by_id.return_value = (True, "Mode found", mode)
        mock_repo.deactivate_mode.return_value = (True, "Mode deactivated successfully", None)

        success, message, result = mode_manager.deactivate_mode("test_war")

        assert success is True
        assert "Mode deactivated successfully" in message
        mock_repo.deactivate_mode.assert_called_once()

    def test_cleanup_expired_modes(self, mode_manager, mock_repo):
        """Test cleaning up expired modes"""
        expired_mode = GameMode.create_seasonal_war(
            "Expired War",
            datetime.utcnow() - timedelta(days=2),
            datetime.utcnow() - timedelta(days=1)
        )
        expired_mode.activate()

        mock_repo.get_active_modes.return_value = (True, "Success", [expired_mode])
        mock_repo.deactivate_mode.return_value = (True, "Mode deactivated successfully", None)

        success, message, result = mode_manager.cleanup_expired_modes()

        assert success is True
        assert result["expired_count"] == 1
        mock_repo.deactivate_mode.assert_called_once()

    def test_get_current_active_mode(self, mode_manager, mock_repo):
        """Test getting current active mode"""
        normal_mode = GameMode.create_default_normal_mode()
        seasonal_mode = GameMode.create_seasonal_war(
            "Active War",
            datetime.utcnow() - timedelta(hours=1),
            datetime.utcnow() + timedelta(hours=1)
        )
        seasonal_mode.activate()

        mock_repo.get_active_modes.return_value = (True, "Success", [normal_mode, seasonal_mode])

        success, message, result = mode_manager.get_current_active_mode()

        assert success is True
        assert result.mode_type == "seasonal_war"  # Should prioritize non-normal modes

    def test_get_current_active_mode_normal_only(self, mode_manager, mock_repo):
        """Test getting current active mode when only normal mode is available"""
        normal_mode = GameMode.create_default_normal_mode()

        mock_repo.get_active_modes.return_value = (True, "Success", [normal_mode])

        success, message, result = mode_manager.get_current_active_mode()

        assert success is True
        assert result.mode_type == "normal"