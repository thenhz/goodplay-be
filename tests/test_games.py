"""
Unit Tests for Game Engine Module (GOO-8)
Tests game plugin system, plugin manager, and game sessions
"""
import pytest
import json
from unittest.mock import MagicMock, patch
from bson import ObjectId
from datetime import datetime, timezone, timedelta

from app.games.core.game_plugin import GamePlugin
from app.games.core.plugin_manager import PluginManager
from app.games.core.plugin_registry import PluginRegistry
from app.games.models.game_session import GameSession
from app.games.models.game import Game
from app.games.services.state_synchronizer import StateSynchronizer
from app.games.repositories.game_session_repository import GameSessionRepository


class TestGamePlugin:
    """Test cases for GamePlugin base class"""

    class MockGamePlugin(GamePlugin):
        """Mock implementation of GamePlugin for testing"""

        def __init__(self):
            self.name = "Test Game"
            self.version = "1.0.0"
            self.description = "Test game plugin"
            self.category = "puzzle"
            self.author = "Test Author"
            self.min_players = 1
            self.max_players = 1

        def initialize(self) -> bool:
            return True

        def start_session(self, user_id: str) -> dict:
            return {
                "session_id": str(ObjectId()),
                "game_state": {"level": 1, "score": 0}
            }

        def end_session(self, session_id: str) -> dict:
            return {
                "session_id": session_id,
                "final_score": 100,
                "duration": 300
            }

        def get_rules(self) -> dict:
            return {
                "objective": "Test objective",
                "controls": ["click", "drag"],
                "scoring": "Points for completion"
            }

        def validate_move(self, session_id: str, move: dict) -> bool:
            return True

    def test_plugin_interface_implementation(self):
        """Test that plugin implements required interface"""
        plugin = self.MockGamePlugin()

        assert hasattr(plugin, 'name')
        assert hasattr(plugin, 'version')
        assert hasattr(plugin, 'description')
        assert hasattr(plugin, 'category')
        assert callable(plugin.initialize)
        assert callable(plugin.start_session)
        assert callable(plugin.end_session)
        assert callable(plugin.get_rules)
        assert callable(plugin.validate_move)

    def test_plugin_initialization(self):
        """Test plugin initialization"""
        plugin = self.MockGamePlugin()

        assert plugin.initialize() is True
        assert plugin.name == "Test Game"
        assert plugin.version == "1.0.0"
        assert plugin.category == "puzzle"

    def test_start_session(self):
        """Test starting game session"""
        plugin = self.MockGamePlugin()
        user_id = str(ObjectId())

        result = plugin.start_session(user_id)

        assert "session_id" in result
        assert "game_state" in result
        assert result["game_state"]["level"] == 1
        assert result["game_state"]["score"] == 0

    def test_end_session(self):
        """Test ending game session"""
        plugin = self.MockGamePlugin()
        session_id = str(ObjectId())

        result = plugin.end_session(session_id)

        assert "session_id" in result
        assert "final_score" in result
        assert "duration" in result
        assert result["session_id"] == session_id

    def test_get_rules(self):
        """Test getting game rules"""
        plugin = self.MockGamePlugin()

        rules = plugin.get_rules()

        assert "objective" in rules
        assert "controls" in rules
        assert "scoring" in rules

    def test_validate_move(self):
        """Test move validation"""
        plugin = self.MockGamePlugin()
        session_id = str(ObjectId())
        move = {"action": "click", "position": {"x": 10, "y": 20}}

        result = plugin.validate_move(session_id, move)

        assert result is True


class TestPluginManager:
    """Test cases for PluginManager"""

    @pytest.fixture
    def plugin_manager(self, mock_db):
        """Create PluginManager instance with mocked dependencies"""
        registry = PluginRegistry()
        registry.collection = mock_db
        return PluginManager(registry)

    def test_discover_plugins_success(self, plugin_manager, mock_db):
        """Test plugin discovery"""
        # Mock available plugins
        plugins_data = [
            {
                "_id": ObjectId(),
                "plugin_id": "test_game",
                "name": "Test Game",
                "version": "1.0.0",
                "category": "puzzle",
                "is_active": True
            }
        ]
        mock_db.find.return_value = plugins_data

        success, message, result = plugin_manager.discover_plugins()

        assert success is True
        assert message == "PLUGINS_DISCOVERED_SUCCESS"
        assert result is not None
        assert len(result) == 1

    def test_install_plugin_success(self, plugin_manager, mock_db):
        """Test plugin installation"""
        plugin_data = {
            "plugin_id": "new_game",
            "name": "New Game",
            "version": "1.0.0",
            "description": "A new game plugin",
            "category": "action",
            "author": "Developer"
        }

        # Mock plugin not exists
        mock_db.find_one.return_value = None
        mock_db.insert_one.return_value = MagicMock(inserted_id=ObjectId())

        success, message, result = plugin_manager.install_plugin(plugin_data)

        assert success is True
        assert message == "PLUGIN_INSTALLED_SUCCESS"
        assert result is not None

    def test_install_plugin_already_exists(self, plugin_manager, mock_db):
        """Test installing already existing plugin"""
        plugin_data = {
            "plugin_id": "existing_game",
            "name": "Existing Game",
            "version": "1.0.0"
        }

        # Mock plugin exists
        existing_plugin = {
            "_id": ObjectId(),
            "plugin_id": "existing_game",
            "name": "Existing Game"
        }
        mock_db.find_one.return_value = existing_plugin

        success, message, result = plugin_manager.install_plugin(plugin_data)

        assert success is False
        assert message == "PLUGIN_ALREADY_EXISTS"
        assert result is None

    def test_uninstall_plugin_success(self, plugin_manager, mock_db):
        """Test plugin uninstallation"""
        plugin_id = "test_game"

        # Mock plugin exists and is active
        existing_plugin = {
            "_id": ObjectId(),
            "plugin_id": plugin_id,
            "is_active": True
        }
        mock_db.find_one.return_value = existing_plugin
        mock_db.update_one.return_value = MagicMock(modified_count=1)

        success, message, result = plugin_manager.uninstall_plugin(plugin_id)

        assert success is True
        assert message == "PLUGIN_UNINSTALLED_SUCCESS"
        assert result is not None

    def test_uninstall_plugin_not_found(self, plugin_manager, mock_db):
        """Test uninstalling non-existent plugin"""
        plugin_id = "nonexistent_game"

        mock_db.find_one.return_value = None

        success, message, result = plugin_manager.uninstall_plugin(plugin_id)

        assert success is False
        assert message == "PLUGIN_NOT_FOUND"
        assert result is None

    def test_validate_plugin_success(self, plugin_manager):
        """Test plugin validation"""
        valid_plugin_data = {
            "plugin_id": "valid_game",
            "name": "Valid Game",
            "version": "1.0.0",
            "description": "A valid game plugin",
            "category": "puzzle",
            "author": "Developer"
        }

        success, message, result = plugin_manager.validate_plugin(valid_plugin_data)

        assert success is True
        assert message == "PLUGIN_VALIDATION_SUCCESS"
        assert result is not None

    def test_validate_plugin_missing_fields(self, plugin_manager):
        """Test plugin validation with missing fields"""
        invalid_plugin_data = {
            "plugin_id": "invalid_game"
            # Missing required fields
        }

        success, message, result = plugin_manager.validate_plugin(invalid_plugin_data)

        assert success is False
        assert message == "PLUGIN_VALIDATION_FAILED"
        assert result is None

    def test_get_plugin_info_success(self, plugin_manager, mock_db):
        """Test getting plugin information"""
        plugin_id = "test_game"

        # Mock plugin data
        plugin_data = {
            "_id": ObjectId(),
            "plugin_id": plugin_id,
            "name": "Test Game",
            "version": "1.0.0",
            "description": "Test game plugin",
            "category": "puzzle",
            "is_active": True
        }
        mock_db.find_one.return_value = plugin_data

        success, message, result = plugin_manager.get_plugin_info(plugin_id)

        assert success is True
        assert message == "PLUGIN_INFO_RETRIEVED_SUCCESS"
        assert result is not None
        assert result["plugin_id"] == plugin_id

    def test_load_plugin_success(self, plugin_manager):
        """Test loading plugin dynamically"""
        plugin_config = {
            "plugin_id": "test_game",
            "name": "Test Game",
            "module_path": "app.games.plugins.test_game",
            "class_name": "TestGamePlugin"
        }

        with patch('importlib.import_module') as mock_import:
            mock_module = MagicMock()
            mock_plugin_class = MagicMock()
            mock_plugin_instance = MagicMock()

            mock_import.return_value = mock_module
            mock_module.TestGamePlugin = mock_plugin_class
            mock_plugin_class.return_value = mock_plugin_instance
            mock_plugin_instance.initialize.return_value = True

            success, message, result = plugin_manager.load_plugin(plugin_config)

            assert success is True
            assert message == "PLUGIN_LOADED_SUCCESS"
            assert result is not None


class TestGameSession:
    """Test cases for GameSession model"""

    def test_create_game_session(self):
        """Test creating GameSession instance"""
        user_id = ObjectId()
        game_id = ObjectId()

        session = GameSession(
            user_id=user_id,
            game_id=game_id,
            game_state={"level": 1, "score": 0}
        )

        assert session.user_id == user_id
        assert session.game_id == game_id
        assert session.game_state == {"level": 1, "score": 0}
        assert session.status == "active"
        assert isinstance(session.created_at, datetime)
        assert isinstance(session.updated_at, datetime)

    def test_session_to_dict(self):
        """Test session serialization"""
        session = GameSession(
            user_id=ObjectId(),
            game_id=ObjectId(),
            game_state={"level": 1}
        )

        session_dict = session.to_dict()

        assert "user_id" in session_dict
        assert "game_id" in session_dict
        assert "game_state" in session_dict
        assert "status" in session_dict
        assert "created_at" in session_dict

    def test_session_from_dict(self):
        """Test session deserialization"""
        session_data = {
            "_id": ObjectId(),
            "user_id": ObjectId(),
            "game_id": ObjectId(),
            "game_state": {"level": 1, "score": 100},
            "status": "completed",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }

        session = GameSession.from_dict(session_data)

        assert session.user_id == session_data["user_id"]
        assert session.game_id == session_data["game_id"]
        assert session.game_state == session_data["game_state"]
        assert session.status == session_data["status"]

    def test_update_game_state(self):
        """Test updating game state"""
        session = GameSession(
            user_id=ObjectId(),
            game_id=ObjectId(),
            game_state={"level": 1, "score": 0}
        )

        original_updated_at = session.updated_at
        new_state = {"level": 2, "score": 150}

        session.update_game_state(new_state)

        assert session.game_state == new_state
        assert session.updated_at > original_updated_at

    def test_complete_session(self):
        """Test completing game session"""
        session = GameSession(
            user_id=ObjectId(),
            game_id=ObjectId(),
            game_state={"level": 1, "score": 0}
        )

        final_score = 500
        duration = 300

        session.complete_session(final_score, duration)

        assert session.status == "completed"
        assert session.final_score == final_score
        assert session.duration_seconds == duration
        assert session.completed_at is not None


class TestGamesController:
    """Test cases for Games Controller endpoints"""

    @patch('flask_jwt_extended.jwt_required')
    @patch('flask_jwt_extended.get_jwt_identity')
    def test_get_available_games_endpoint_success(self, mock_get_identity, mock_jwt, client, mock_db):
        """Test GET /api/games endpoint success"""
        user_id = str(ObjectId())
        mock_get_identity.return_value = user_id
        mock_jwt.return_value = lambda f: f

        # Mock available games
        games_data = [
            {
                "_id": ObjectId(),
                "plugin_id": "puzzle_game",
                "name": "Puzzle Game",
                "category": "puzzle",
                "is_active": True
            }
        ]
        mock_db.find.return_value = games_data

        response = client.get('/api/games/')

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data["success"] is True
        assert response_data["message"] == "GAMES_LIST_RETRIEVED_SUCCESS"

    @patch('flask_jwt_extended.jwt_required')
    @patch('flask_jwt_extended.get_jwt_identity')
    def test_get_game_info_endpoint_success(self, mock_get_identity, mock_jwt, client, mock_db):
        """Test GET /api/games/{game_id}/info endpoint success"""
        user_id = str(ObjectId())
        game_id = "puzzle_game"
        mock_get_identity.return_value = user_id
        mock_jwt.return_value = lambda f: f

        # Mock game data
        game_data = {
            "_id": ObjectId(),
            "plugin_id": game_id,
            "name": "Puzzle Game",
            "description": "A challenging puzzle game",
            "category": "puzzle",
            "is_active": True
        }
        mock_db.find_one.return_value = game_data

        response = client.get(f'/api/games/{game_id}/info')

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data["success"] is True
        assert response_data["message"] == "GAME_INFO_RETRIEVED_SUCCESS"

    @patch('flask_jwt_extended.jwt_required')
    @patch('flask_jwt_extended.get_jwt_identity')
    def test_install_plugin_endpoint_success(self, mock_get_identity, mock_jwt, client, mock_db):
        """Test POST /api/games/install endpoint success"""
        user_id = str(ObjectId())
        mock_get_identity.return_value = user_id
        mock_jwt.return_value = lambda f: f

        # Mock admin role check
        with patch('app.shared.decorators.admin_required', lambda f: f):
            # Mock plugin installation
            mock_db.find_one.return_value = None
            mock_db.insert_one.return_value = MagicMock(inserted_id=ObjectId())

            plugin_data = {
                "plugin_id": "new_game",
                "name": "New Game",
                "version": "1.0.0",
                "category": "action",
                "author": "Developer"
            }

            response = client.post(
                '/api/games/install',
                data=json.dumps(plugin_data),
                content_type='application/json'
            )

            assert response.status_code == 201
            response_data = json.loads(response.data)
            assert response_data["success"] is True
            assert response_data["message"] == "PLUGIN_INSTALLED_SUCCESS"

    @patch('flask_jwt_extended.jwt_required')
    @patch('flask_jwt_extended.get_jwt_identity')
    def test_validate_plugin_endpoint_success(self, mock_get_identity, mock_jwt, client):
        """Test POST /api/games/{game_id}/validate endpoint success"""
        user_id = str(ObjectId())
        game_id = "test_game"
        mock_get_identity.return_value = user_id
        mock_jwt.return_value = lambda f: f

        # Mock admin role check
        with patch('app.shared.decorators.admin_required', lambda f: f):
            plugin_data = {
                "plugin_id": game_id,
                "name": "Test Game",
                "version": "1.0.0",
                "category": "puzzle",
                "author": "Developer"
            }

            response = client.post(
                f'/api/games/{game_id}/validate',
                data=json.dumps(plugin_data),
                content_type='application/json'
            )

            assert response.status_code == 200
            response_data = json.loads(response.data)
            assert response_data["success"] is True
            assert response_data["message"] == "PLUGIN_VALIDATION_SUCCESS"

    def test_game_not_found_endpoint(self, client, mock_db):
        """Test accessing non-existent game"""
        game_id = "nonexistent_game"
        mock_db.find_one.return_value = None

        response = client.get(f'/api/games/{game_id}/info')

        assert response.status_code == 404
        response_data = json.loads(response.data)
        assert response_data["success"] is False
        assert response_data["message"] == "GAME_NOT_FOUND"


class TestPluginRegistry:
    """Test cases for PluginRegistry"""

    @pytest.fixture
    def plugin_registry(self, mock_db):
        """Create PluginRegistry instance with mocked database"""
        registry = PluginRegistry()
        registry.collection = mock_db
        return registry

    def test_register_plugin_success(self, plugin_registry, mock_db):
        """Test registering new plugin"""
        plugin_data = {
            "plugin_id": "test_game",
            "name": "Test Game",
            "version": "1.0.0",
            "category": "puzzle"
        }

        mock_db.insert_one.return_value = MagicMock(inserted_id=ObjectId())

        result = plugin_registry.register_plugin(plugin_data)

        assert result is not None
        mock_db.insert_one.assert_called_once()

    def test_find_plugin_by_id_success(self, plugin_registry, mock_db):
        """Test finding plugin by ID"""
        plugin_id = "test_game"
        expected_plugin = {
            "_id": ObjectId(),
            "plugin_id": plugin_id,
            "name": "Test Game"
        }
        mock_db.find_one.return_value = expected_plugin

        result = plugin_registry.find_by_plugin_id(plugin_id)

        assert result is not None
        mock_db.find_one.assert_called_once_with({"plugin_id": plugin_id})

    def test_get_active_plugins_success(self, plugin_registry, mock_db):
        """Test getting active plugins"""
        active_plugins = [
            {
                "_id": ObjectId(),
                "plugin_id": "game1",
                "is_active": True
            },
            {
                "_id": ObjectId(),
                "plugin_id": "game2",
                "is_active": True
            }
        ]
        mock_db.find.return_value = active_plugins

        result = plugin_registry.get_active_plugins()

        assert len(result) == 2
        mock_db.find.assert_called_once_with({"is_active": True})

    def test_update_plugin_success(self, plugin_registry, mock_db):
        """Test updating plugin"""
        plugin_id = "test_game"
        update_data = {"version": "1.1.0", "description": "Updated description"}

        mock_db.update_one.return_value = MagicMock(modified_count=1)

        result = plugin_registry.update_plugin(plugin_id, update_data)

        assert result is True
        mock_db.update_one.assert_called_once()

    def test_deactivate_plugin_success(self, plugin_registry, mock_db):
        """Test deactivating plugin"""
        plugin_id = "test_game"

        mock_db.update_one.return_value = MagicMock(modified_count=1)

        result = plugin_registry.deactivate_plugin(plugin_id)

        assert result is True
        mock_db.update_one.assert_called_once_with(
            {"plugin_id": plugin_id},
            {"$set": {"is_active": False, "updated_at": mock_db.update_one.call_args[1]["$set"]["updated_at"]}}
        )


# Enhanced GOO-9 Session Management Tests

class TestEnhancedGameSession:
    """Test cases for enhanced GameSession model with GOO-9 features"""

    def test_create_enhanced_session(self):
        """Test creating GameSession with enhanced GOO-9 fields"""
        user_id = str(ObjectId())
        game_id = str(ObjectId())
        device_info = {
            "device_id": "test-device-123",
            "device_type": "mobile",
            "platform": "iOS",
            "app_version": "1.0.0"
        }

        session = GameSession(
            user_id=user_id,
            game_id=game_id,
            current_state={"level": 1, "score": 0},
            device_info=device_info
        )

        assert session.user_id == user_id
        assert session.game_id == game_id
        assert session.play_duration == 0
        assert session.moves_count == 0
        assert session.device_info == device_info
        assert session.sync_version == 0
        assert session.paused_at is None
        assert session.resumed_at is None

    def test_precise_time_tracking_pause_resume(self):
        """Test precise time tracking with pause/resume functionality"""
        session = GameSession(
            user_id=str(ObjectId()),
            game_id=str(ObjectId())
        )

        # Simulate active play for a moment
        import time
        time.sleep(0.1)  # 100ms

        # Pause session
        session.pause_session()

        assert session.status == "paused"
        assert session.paused_at is not None
        assert session.play_duration > 0

        # Resume session
        session.resume_session()

        assert session.status == "active"
        assert session.resumed_at is not None

        # Complete session
        session.complete_session(final_score=100)

        assert session.status == "completed"
        assert session.ended_at is not None
        assert session.score == 100

    def test_precise_play_duration_calculation(self):
        """Test precise play duration calculation"""
        session = GameSession(
            user_id=str(ObjectId()),
            game_id=str(ObjectId())
        )

        # Test initial state
        assert session.get_precise_play_duration_ms() >= 0

        # Test with some play duration
        session.play_duration = 5000  # 5 seconds
        assert session.get_precise_play_duration_ms() >= 5000

    def test_device_info_tracking(self):
        """Test device information tracking"""
        session = GameSession(
            user_id=str(ObjectId()),
            game_id=str(ObjectId())
        )

        device_info = {
            "device_id": "mobile-123",
            "device_type": "mobile",
            "platform": "Android",
            "app_version": "2.1.0",
            "screen_resolution": "1920x1080"
        }

        session.update_device_info(device_info)

        assert session.device_info == device_info
        assert session.updated_at is not None

    def test_sync_versioning(self):
        """Test synchronization version management"""
        session = GameSession(
            user_id=str(ObjectId()),
            game_id=str(ObjectId())
        )

        initial_version = session.sync_version
        initial_sync_time = session.last_sync_at

        session.update_sync_info()

        assert session.sync_version == initial_version + 1
        assert session.last_sync_at != initial_sync_time

    def test_enhanced_move_tracking(self):
        """Test enhanced move tracking with counts"""
        session = GameSession(
            user_id=str(ObjectId()),
            game_id=str(ObjectId())
        )

        move1 = {"action": "click", "position": {"x": 10, "y": 20}}
        move2 = {"action": "drag", "from": {"x": 10, "y": 20}, "to": {"x": 30, "y": 40}}

        session.add_move(move1)
        assert session.moves_count == 1
        assert len(session.moves) == 1

        session.add_move(move2)
        assert session.moves_count == 2
        assert len(session.moves) == 2

        # Check move timestamps
        assert "timestamp" in session.moves[0]
        assert "move_number" in session.moves[0]

    def test_enhanced_api_dict_output(self):
        """Test enhanced API dictionary output with new fields"""
        device_info = {"device_type": "web", "browser": "Chrome"}
        session = GameSession(
            user_id=str(ObjectId()),
            game_id=str(ObjectId()),
            device_info=device_info,
            play_duration=10000  # 10 seconds
        )

        api_dict = session.to_api_dict()

        assert "play_duration_ms" in api_dict
        assert "play_duration_seconds" in api_dict
        assert "device_info" in api_dict
        assert "sync_version" in api_dict
        assert "last_sync_at" in api_dict
        assert "paused_at" in api_dict
        assert "resumed_at" in api_dict

        assert api_dict["play_duration_ms"] == 10000
        assert api_dict["play_duration_seconds"] == 10.0
        assert api_dict["device_info"] == device_info

    def test_credits_calculation_precise(self):
        """Test precise credits calculation based on play duration"""
        session = GameSession(
            user_id=str(ObjectId()),
            game_id=str(ObjectId()),
            play_duration=120000  # 2 minutes in milliseconds
        )

        credit_rate = 0.5  # 0.5 credits per minute
        credits = session.calculate_credits_earned_precise(credit_rate)

        assert credits == 1  # 2 minutes * 0.5 credits/minute = 1 credit
        assert session.credits_earned == 1


class TestStateSynchronizer:
    """Test cases for StateSynchronizer service"""

    @pytest.fixture
    def state_synchronizer(self, mock_db):
        """Create StateSynchronizer instance with mocked dependencies"""
        synchronizer = StateSynchronizer()
        # Mock the repository
        synchronizer.session_repository = MagicMock()
        return synchronizer

    def test_sync_session_state_success(self, state_synchronizer):
        """Test successful session state synchronization"""
        session_id = str(ObjectId())
        device_state = {
            "current_state": {"level": 2, "score": 200},
            "play_duration_ms": 30000,
            "sync_version": 1
        }
        device_info = {
            "device_id": "test-device-456",
            "device_type": "web"
        }

        # Mock existing session
        mock_session = MagicMock()
        mock_session.sync_version = 0
        mock_session.is_ended.return_value = False
        state_synchronizer.session_repository.get_session_by_session_id.return_value = mock_session
        state_synchronizer.session_repository.update_session.return_value = True

        success, message, result = state_synchronizer.sync_session_state(
            session_id, device_state, device_info
        )

        assert success is True
        assert message == "SESSION_SYNC_SUCCESS"
        assert result is not None

    def test_sync_conflict_detection(self, state_synchronizer):
        """Test synchronization conflict detection"""
        session_id = str(ObjectId())
        device_state = {
            "current_state": {"level": 1, "score": 50},
            "sync_version": 1
        }
        device_info = {"device_id": "old-device"}

        # Mock session with higher sync version (conflict)
        mock_session = MagicMock()
        mock_session.sync_version = 3
        mock_session.is_ended.return_value = False
        mock_session.to_api_dict.return_value = {"session_id": session_id}
        state_synchronizer.session_repository.get_session_by_session_id.return_value = mock_session

        success, message, result = state_synchronizer.sync_session_state(
            session_id, device_state, device_info
        )

        assert success is True
        assert message == "SYNC_CONFLICT_SERVER_WINS"
        assert result is not None
        assert "conflict_resolution" in result

    def test_get_session_for_device(self, state_synchronizer):
        """Test getting session optimized for specific device"""
        session_id = str(ObjectId())
        device_info = {
            "device_id": "mobile-789",
            "device_type": "mobile"
        }

        # Mock session
        mock_session = MagicMock()
        mock_session.to_api_dict.return_value = {"session_id": session_id}
        mock_session.sync_version = 2
        state_synchronizer.session_repository.get_session_by_session_id.return_value = mock_session
        state_synchronizer.session_repository.update_session.return_value = True

        success, message, result = state_synchronizer.get_session_for_device(
            session_id, device_info
        )

        assert success is True
        assert message == "SESSION_PROVIDED_SUCCESS"
        assert result is not None
        assert "session" in result
        assert "sync_version" in result
        assert "device_specific_data" in result

    def test_resolve_sync_conflict_server_wins(self, state_synchronizer):
        """Test conflict resolution with server wins strategy"""
        session_id = str(ObjectId())
        device_state = {"current_state": {"level": 1}}
        resolution_strategy = "server_wins"

        # Mock session
        mock_session = MagicMock()
        mock_session.to_api_dict.return_value = {"session_id": session_id}
        state_synchronizer.session_repository.get_session_by_session_id.return_value = mock_session

        success, message, result = state_synchronizer.resolve_sync_conflict(
            session_id, device_state, resolution_strategy
        )

        assert success is True
        assert message == "SYNC_CONFLICT_RESOLVED"
        assert result is not None
        assert result["resolution"] == "server_wins"

    def test_resolve_sync_conflict_device_wins(self, state_synchronizer):
        """Test conflict resolution with device wins strategy"""
        session_id = str(ObjectId())
        device_state = {
            "current_state": {"level": 3, "score": 500},
            "score": 500,
            "play_duration_ms": 60000
        }
        resolution_strategy = "device_wins"

        # Mock session
        mock_session = MagicMock()
        mock_session.to_api_dict.return_value = {"session_id": session_id}
        state_synchronizer.session_repository.get_session_by_session_id.return_value = mock_session
        state_synchronizer.session_repository.update_session.return_value = True

        success, message, result = state_synchronizer.resolve_sync_conflict(
            session_id, device_state, resolution_strategy
        )

        assert success is True
        assert message == "SYNC_CONFLICT_RESOLVED"
        assert result is not None
        assert result["resolution"] == "device_wins"

    def test_check_session_conflicts(self, state_synchronizer):
        """Test checking for session conflicts"""
        user_id = str(ObjectId())

        # Mock sessions with old sync times
        old_session = MagicMock()
        old_session.session_id = "old-session"
        old_session.game_id = "game1"
        old_session.last_sync_at = datetime.utcnow() - timedelta(minutes=10)
        old_session.device_info = {"device_type": "mobile"}
        old_session.status = "active"

        recent_session = MagicMock()
        recent_session.session_id = "recent-session"
        recent_session.last_sync_at = datetime.utcnow() - timedelta(minutes=1)

        state_synchronizer.session_repository.get_user_sessions.side_effect = [
            [old_session],  # active sessions
            [recent_session]  # paused sessions
        ]

        success, message, result = state_synchronizer.check_session_conflicts(user_id)

        assert success is True
        assert result["conflicts_count"] >= 0
        assert "conflicts" in result

    def test_intelligent_state_merge(self, state_synchronizer):
        """Test intelligent merging of session states"""
        session_id = str(ObjectId())

        # Mock server session
        mock_server_session = MagicMock()
        mock_server_session.session_id = session_id
        mock_server_session.score = 100
        mock_server_session.play_duration = 30000
        mock_server_session.achievements_unlocked = ["achievement1"]
        mock_server_session.moves = [{"action": "move1", "timestamp": datetime.utcnow()}]
        mock_server_session.statistics = {"deaths": 2}
        mock_server_session.to_api_dict.return_value = {"session_id": session_id}

        device_state = {
            "score": 150,  # Higher score
            "play_duration_ms": 25000,  # Lower duration
            "new_achievements": ["achievement2"],
            "new_moves": [{"action": "move2", "timestamp": datetime.utcnow()}],
            "statistics": {"kills": 5},
            "current_state": {"level": 3}
        }

        state_synchronizer.session_repository.get_session_by_session_id.return_value = mock_server_session
        state_synchronizer.session_repository.update_session.return_value = True

        success, message, result = state_synchronizer.resolve_sync_conflict(
            session_id, device_state, "merge"
        )

        assert success is True
        assert message == "SYNC_CONFLICT_RESOLVED"
        assert result["resolution"] == "merge"
        assert "merge_summary" in result


class TestEnhancedSessionController:
    """Test cases for enhanced session management endpoints"""

    @patch('app.games.controllers.games_controller.auth_required')
    def test_sync_session_endpoint_success(self, mock_auth, client, mock_db):
        """Test POST /api/games/sessions/{session_id}/sync endpoint"""
        user_id = str(ObjectId())
        session_id = str(ObjectId())

        # Mock auth_required decorator to pass through with current_user
        def mock_decorator(f):
            def wrapper(*args, **kwargs):
                return f({'_id': user_id})
            return wrapper
        mock_auth.side_effect = mock_decorator

        sync_data = {
            "device_state": {
                "current_state": {"level": 2, "score": 200},
                "play_duration_ms": 45000,
                "sync_version": 1
            },
            "device_info": {
                "device_id": "test-device",
                "device_type": "mobile"
            }
        }

        with patch('app.games.services.game_session_service.GameSessionService') as mock_service:
            with patch('app.games.services.state_synchronizer.StateSynchronizer') as mock_sync:
                # Mock session ownership check
                mock_service.return_value.get_session_by_id.return_value = (
                    True, "SESSION_RETRIEVED_SUCCESS",
                    {"session": {"user_id": user_id}}
                )

                # Mock sync success
                mock_sync.return_value.sync_session_state.return_value = (
                    True, "SESSION_SYNC_SUCCESS",
                    {"session": {"session_id": session_id}}
                )

                response = client.post(
                    f'/api/games/sessions/{session_id}/sync',
                    data=json.dumps(sync_data),
                    content_type='application/json',
                    headers={'Authorization': 'Bearer test-token'}
                )

                assert response.status_code == 200
                response_data = json.loads(response.data)
                assert response_data["success"] is True

    @patch('app.games.controllers.games_controller.auth_required')
    def test_get_active_sessions_endpoint(self, mock_auth, client):
        """Test GET /api/games/sessions/active endpoint"""
        user_id = str(ObjectId())

        # Mock auth_required decorator to pass through with current_user
        def mock_decorator(f):
            def wrapper(*args, **kwargs):
                return f({'_id': user_id})
            return wrapper
        mock_auth.side_effect = mock_decorator

        with patch('app.games.services.game_session_service.GameSessionService') as mock_service:
            # Mock active and paused sessions
            mock_service.return_value.get_user_sessions.side_effect = [
                (True, "SUCCESS", {"sessions": [{"session_id": "active1", "status": "active"}]}),
                (True, "SUCCESS", {"sessions": [{"session_id": "paused1", "status": "paused"}]})
            ]

            response = client.get(
                '/api/games/sessions/active',
                headers={'Authorization': 'Bearer test-token'}
            )

            assert response.status_code == 200
            response_data = json.loads(response.data)
            assert response_data["success"] is True
            assert "active_sessions" in response_data["data"]
            assert "paused_sessions" in response_data["data"]

    @patch('app.games.controllers.games_controller.auth_required')
    def test_check_conflicts_endpoint(self, mock_auth, client):
        """Test GET /api/games/sessions/conflicts endpoint"""
        user_id = str(ObjectId())

        # Mock auth_required decorator to pass through with current_user
        def mock_decorator(f):
            def wrapper(*args, **kwargs):
                return f({'_id': user_id})
            return wrapper
        mock_auth.side_effect = mock_decorator

        with patch('app.games.services.state_synchronizer.StateSynchronizer') as mock_sync:
            mock_sync.return_value.check_session_conflicts.return_value = (
                True, "NO_SYNC_CONFLICTS",
                {"conflicts_count": 0, "conflicts": []}
            )

            response = client.get(
                '/api/games/sessions/conflicts',
                headers={'Authorization': 'Bearer test-token'}
            )

            assert response.status_code == 200
            response_data = json.loads(response.data)
            assert response_data["success"] is True

    @patch('app.games.controllers.games_controller.auth_required')
    def test_session_access_control(self, mock_auth, client):
        """Test session access control for different users"""
        user1_id = str(ObjectId())
        user2_id = str(ObjectId())
        session_id = str(ObjectId())

        # Mock auth_required decorator to pass through with user2
        def mock_decorator(f):
            def wrapper(*args, **kwargs):
                return f({'_id': user2_id})
            return wrapper
        mock_auth.side_effect = mock_decorator

        with patch('app.games.services.game_session_service.GameSessionService') as mock_service:
            # Mock session owned by user1
            mock_service.return_value.get_session_by_id.return_value = (
                True, "SESSION_RETRIEVED_SUCCESS",
                {"session": {"user_id": user1_id}}
            )

            # User2 tries to access user1's session
            response = client.get(
                f'/api/games/sessions/{session_id}',
                headers={'Authorization': 'Bearer test-token'}
            )

            assert response.status_code == 403
            response_data = json.loads(response.data)
            assert response_data["message"] == "SESSION_ACCESS_DENIED"