"""
BaseGameTest - Specialized Base Class for Game Engine Testing (GOO-35)

Provides specialized testing capabilities for game engine functionality including
plugin system, session management, state synchronization, and scoring systems.
"""
from typing import Dict, Any, Optional, List, Union
from unittest.mock import MagicMock, patch
from bson import ObjectId
from datetime import datetime, timezone

from tests.core.base_service_test import BaseServiceTest


class BaseGameTest(BaseServiceTest):
    """
    Specialized base test class for game engine functionality.

    Features:
    - Automatic game service dependency injection
    - Plugin system testing utilities
    - Session state management
    - Score and achievement testing
    - Multi-player game scenarios
    - Performance testing for games
    """

    # Default dependencies for game tests
    default_dependencies = [
        'game_repository',
        'game_session_repository',
        'plugin_manager',
        'state_synchronizer',
        'scoring_service'
    ]

    # External dependencies for game engine
    default_external_dependencies = [
        'redis',
        'websocket',
        'game_plugins'
    ]

    def setUp(self):
        """Enhanced setup for game engine testing"""
        super().setUp()
        self._setup_game_mocks()
        self._setup_plugin_mocks()
        self._setup_session_mocks()
        self._setup_scoring_mocks()

    def _setup_game_mocks(self):
        """Setup game-related mocks"""
        if hasattr(self, 'mock_game_repository'):
            # Default game repository behavior
            self.mock_game_repository.find_by_id.return_value = None
            self.mock_game_repository.find_by_category.return_value = []
            self.mock_game_repository.find_published.return_value = []
            self.mock_game_repository.create.return_value = str(ObjectId())

    def _setup_plugin_mocks(self):
        """Setup game plugin system mocks"""
        # Mock plugin manager
        self.plugin_manager_patcher = patch('app.games.core.plugin_manager.PluginManager')
        self.mock_plugin_manager_class = self.plugin_manager_patcher.start()
        self.mock_plugin_manager = MagicMock()
        self.mock_plugin_manager_class.return_value = self.mock_plugin_manager

        # Default plugin manager behavior
        self.mock_plugin_manager.load_plugin.return_value = True
        self.mock_plugin_manager.get_plugin.return_value = self._create_mock_plugin()
        self.mock_plugin_manager.list_plugins.return_value = []
        self.mock_plugin_manager.is_plugin_loaded.return_value = False

        self.addCleanup(self.plugin_manager_patcher.stop)

    def _setup_session_mocks(self):
        """Setup game session mocks"""
        if hasattr(self, 'mock_game_session_repository'):
            # Default session repository behavior
            self.mock_game_session_repository.find_by_id.return_value = None
            self.mock_game_session_repository.find_active_by_user.return_value = []
            self.mock_game_session_repository.create.return_value = str(ObjectId())

        # Mock state synchronizer
        if hasattr(self, 'mock_state_synchronizer'):
            self.mock_state_synchronizer.sync_state.return_value = (True, "State synced", {})
            self.mock_state_synchronizer.resolve_conflict.return_value = (True, "Conflict resolved", {})

    def _setup_scoring_mocks(self):
        """Setup scoring system mocks"""
        if hasattr(self, 'mock_scoring_service'):
            self.mock_scoring_service.calculate_score.return_value = (True, "Score calculated", 100)
            self.mock_scoring_service.update_leaderboard.return_value = (True, "Leaderboard updated", {})

    def _create_mock_plugin(self, **plugin_attrs):
        """Create a mock game plugin with default behavior"""
        mock_plugin = MagicMock()

        # Default plugin attributes
        default_attrs = {
            'name': 'Test Game Plugin',
            'version': '1.0.0',
            'description': 'Test plugin for unit testing',
            'category': 'puzzle',
            'author': 'Test Author',
            'min_players': 1,
            'max_players': 1
        }
        default_attrs.update(plugin_attrs)

        for attr_name, attr_value in default_attrs.items():
            setattr(mock_plugin, attr_name, attr_value)

        # Mock plugin methods
        mock_plugin.initialize.return_value = True
        mock_plugin.start_session.return_value = self._create_mock_session()
        mock_plugin.end_session.return_value = self._create_mock_session_result()
        mock_plugin.validate_move.return_value = True
        mock_plugin.calculate_score.return_value = 100

        return mock_plugin

    def _create_mock_session(self, **session_attrs):
        """Create a mock game session object"""
        from app.games.core.game_plugin import GameSession as PluginGameSession

        session_id = str(ObjectId())
        default_attrs = {
            'session_id': session_id,
            'user_id': str(ObjectId()),
            'game_id': str(ObjectId()),
            'status': 'active',
            'current_state': {'level': 1, 'score': 0},
            'started_at': datetime.now(timezone.utc)
        }
        default_attrs.update(session_attrs)

        # Create mock session with attributes
        mock_session = MagicMock(spec=PluginGameSession)
        for attr_name, attr_value in default_attrs.items():
            setattr(mock_session, attr_name, attr_value)

        return mock_session

    def _create_mock_session_result(self, **result_attrs):
        """Create a mock session result object"""
        from app.games.core.game_plugin import SessionResult

        default_attrs = {
            'session_id': str(ObjectId()),
            'final_score': 100,
            'completion_status': 'completed',
            'duration_seconds': 120,
            'achievements_unlocked': [],
            'stats': {'moves': 10, 'time_played': 120}
        }
        default_attrs.update(result_attrs)

        mock_result = MagicMock(spec=SessionResult)
        for attr_name, attr_value in default_attrs.items():
            setattr(mock_result, attr_name, attr_value)

        return mock_result

    # Game-specific utility methods

    def create_test_user(self, email: str = None, role: str = 'user', **kwargs) -> Dict[str, Any]:
        """Create test user data for game scenarios"""
        from tests.utils import user

        # Generate unique email if not provided
        if email is None:
            import time
            email = f"gameuser_{int(time.time() * 1000)}@test.com"

        return (user()
                .with_email(email)
                .as_type(role)
                .with_field('is_active', True)
                .with_field('is_verified', True)
                .merge(kwargs)
                .build())

    def create_test_game(self, category: str = 'puzzle', difficulty: str = 'medium', **kwargs) -> Dict[str, Any]:
        """Create test game data with game-specific defaults"""
        from tests.utils import game

        return (game()
                .with_category(category)
                .with_difficulty(difficulty)
                .with_field('active', True)
                .merge(kwargs)
                .build())

    def create_test_game_plugin(self, name: str = 'Test Plugin', category: str = 'puzzle', **kwargs) -> Dict[str, Any]:
        """Create test game plugin data"""
        plugin_data = {
            'name': name,
            'version': '1.0.0',
            'description': f'Test plugin: {name}',
            'category': category,
            'author': 'Test Author',
            'min_players': 1,
            'max_players': 1,
            'status': 'active',
            'enabled': True,
            **kwargs
        }
        return plugin_data

    def create_test_session(self, user_id: str = None, game_id: str = None, status: str = 'active', **kwargs) -> Dict[str, Any]:
        """Create test game session data"""
        from tests.utils import session

        user_id = user_id or str(ObjectId())
        game_id = game_id or str(ObjectId())

        return (session()
                .for_user(user_id)
                .for_game(game_id)
                .with_status(status)
                .merge(kwargs)
                .build())

    def mock_plugin_loaded(self, plugin_name: str, plugin_attrs: Dict[str, Any] = None):
        """Mock a loaded game plugin"""
        plugin_attrs = plugin_attrs or {}
        mock_plugin = self._create_mock_plugin(name=plugin_name, **plugin_attrs)

        self.mock_plugin_manager.is_plugin_loaded.return_value = True
        self.mock_plugin_manager.get_plugin.return_value = mock_plugin

        return mock_plugin

    def mock_game_session_flow(self, session_attrs: Dict[str, Any] = None):
        """Mock complete game session flow"""
        session_attrs = session_attrs or {}
        test_session = self.create_test_session(**session_attrs)

        # Mock session creation
        self.mock_game_session_repository.create.return_value = test_session['_id']
        self.mock_game_session_repository.find_by_id.return_value = test_session

        # Mock plugin session
        plugin_session = self._create_mock_session(session_id=test_session['_id'])
        mock_plugin = self.mock_plugin_loaded('test_game')
        mock_plugin.start_session.return_value = plugin_session

        return test_session, plugin_session, mock_plugin

    # Session state testing utilities

    def create_session_state(self, level: int = 1, score: int = 0, **state_data) -> Dict[str, Any]:
        """Create test session state data"""
        base_state = {
            'level': level,
            'score': score,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'version': 1
        }
        base_state.update(state_data)
        return base_state

    def mock_state_synchronization(self, conflict: bool = False):
        """Mock session state synchronization scenarios"""
        if conflict:
            # Mock conflict scenario
            self.mock_state_synchronizer.sync_state.return_value = (
                False, "State conflict detected", {'conflict': True}
            )
            self.mock_state_synchronizer.has_conflict.return_value = True
        else:
            # Mock successful sync
            self.mock_state_synchronizer.sync_state.return_value = (
                True, "State synchronized", {'synced': True}
            )
            self.mock_state_synchronizer.has_conflict.return_value = False

    def assert_session_state_valid(self, state: Dict[str, Any], required_fields: List[str] = None):
        """Assert session state structure is valid"""
        from tests.utils import assert_session_valid

        # Check basic session state requirements
        required_fields = required_fields or ['level', 'score', 'timestamp']

        for field in required_fields:
            assert field in state, f"Session state missing required field: {field}"

        # Validate state data
        assert_session_valid(state)

    def assert_plugin_behavior(self, plugin, expected_methods: List[str]):
        """Assert plugin implements expected methods"""
        for method_name in expected_methods:
            assert hasattr(plugin, method_name), f"Plugin missing method: {method_name}"
            assert callable(getattr(plugin, method_name)), f"Plugin method not callable: {method_name}"

    # Multi-player testing utilities

    def create_multiplayer_scenario(self, player_count: int = 2, game_attrs: Dict[str, Any] = None):
        """Create multiplayer game testing scenario"""
        from tests.utils import user

        # Create game
        game_attrs = game_attrs or {}
        game_attrs.update({
            'min_players': player_count,
            'max_players': player_count,
            'multiplayer': True
        })
        test_game = self.create_test_game(**game_attrs)

        # Create players
        players = []
        sessions = []

        for i in range(player_count):
            player = user().with_email(f'player{i+1}@example.com').build()
            session = self.create_test_session(
                user_id=player['_id'],
                game_id=test_game['_id'],
                status='waiting' if i > 0 else 'active'
            )

            players.append(player)
            sessions.append(session)

        return {
            'game': test_game,
            'players': players,
            'sessions': sessions
        }

    def mock_multiplayer_match_making(self, scenario: Dict[str, Any]):
        """Mock multiplayer match making process"""
        game = scenario['game']
        sessions = scenario['sessions']

        # Mock game repository
        self.mock_game_repository.find_by_id.return_value = game

        # Mock session repository for match making
        self.mock_game_session_repository.find_waiting_sessions.return_value = sessions[1:]
        self.mock_game_session_repository.update_session_status.return_value = True

        # Mock plugin for multiplayer
        mock_plugin = self.mock_plugin_loaded(
            'multiplayer_game',
            {'multiplayer': True, 'min_players': game['min_players']}
        )

        return mock_plugin

    # Performance testing utilities

    def create_performance_test_scenario(self, operation_count: int = 100):
        """Create scenario for performance testing"""
        scenarios = []

        for i in range(operation_count):
            scenario = {
                'user_id': str(ObjectId()),
                'game_id': str(ObjectId()),
                'session_data': self.create_test_session(),
                'state_data': self.create_session_state(level=i % 10 + 1, score=i * 100)
            }
            scenarios.append(scenario)

        return scenarios

    def benchmark_game_operation(self, operation_func, scenarios: List[Dict[str, Any]]):
        """Benchmark game operations with multiple scenarios"""
        import time

        start_time = time.time()
        results = []

        for scenario in scenarios:
            op_start = time.time()
            result = operation_func(scenario)
            op_duration = time.time() - op_start

            results.append({
                'result': result,
                'duration_ms': op_duration * 1000,
                'scenario': scenario
            })

        total_duration = time.time() - start_time

        return {
            'total_duration_ms': total_duration * 1000,
            'operation_count': len(scenarios),
            'avg_duration_ms': (total_duration * 1000) / len(scenarios),
            'results': results
        }

    # Scoring and achievements testing

    def mock_scoring_calculation(self, base_score: int = 100, multiplier: float = 1.0):
        """Mock scoring calculation with various factors"""
        calculated_score = int(base_score * multiplier)

        self.mock_scoring_service.calculate_score.return_value = (
            True, "Score calculated", calculated_score
        )

        return calculated_score

    def create_achievement_scenario(self, achievement_type: str = 'score_based', **criteria):
        """Create achievement unlock scenario"""
        achievement_scenarios = {
            'score_based': {'min_score': 1000, 'game_category': 'puzzle'},
            'streak_based': {'win_streak': 5, 'consecutive': True},
            'time_based': {'max_duration': 60, 'game_category': 'arcade'},
            'challenge_based': {'challenge_type': 'daily', 'completion': True}
        }

        base_criteria = achievement_scenarios.get(achievement_type, {})
        base_criteria.update(criteria)

        return {
            'type': achievement_type,
            'criteria': base_criteria,
            'achievement_id': str(ObjectId())
        }

    def tearDown(self):
        """Clean up game-specific mocks"""
        super().tearDown()


# Convenience functions for game testing

def game_test(service_class=None, plugin_dependencies: List[str] = None, **kwargs):
    """Decorator for creating game test class with specific configuration"""
    def decorator(cls):
        if service_class:
            cls.service_class = service_class

        # Add plugin-specific dependencies
        if plugin_dependencies:
            base_deps = BaseGameTest.default_dependencies
            cls.dependencies = base_deps + plugin_dependencies

        return cls

    return decorator


class GamePluginTest(BaseGameTest):
    """Specialized base class for testing individual game plugins"""

    def setUp(self):
        super().setUp()
        self.plugin_under_test = None

    def set_plugin_under_test(self, plugin_class, **plugin_config):
        """Set the specific plugin being tested"""
        self.plugin_under_test = plugin_class(**plugin_config)
        return self.plugin_under_test

    def assert_plugin_compliance(self, required_interface_methods: List[str] = None):
        """Assert plugin complies with game plugin interface"""
        if not self.plugin_under_test:
            raise ValueError("No plugin set for testing. Use set_plugin_under_test() first.")

        default_methods = ['initialize', 'start_session', 'end_session', 'validate_move']
        methods_to_check = required_interface_methods or default_methods

        self.assert_plugin_behavior(self.plugin_under_test, methods_to_check)

    def test_plugin_lifecycle(self):
        """Test complete plugin lifecycle"""
        if not self.plugin_under_test:
            return

        # Test initialization
        assert self.plugin_under_test.initialize(), "Plugin initialization failed"

        # Test session creation
        test_user_id = str(ObjectId())
        session = self.plugin_under_test.start_session(test_user_id)
        assert session is not None, "Plugin failed to create session"

        # Test session completion
        result = self.plugin_under_test.end_session(session.session_id)
        assert result is not None, "Plugin failed to end session"


# Usage Examples:
"""
# Basic game service test
class TestGameService(BaseGameTest):
    service_class = GameService

    def test_create_game_session(self):
        test_game = self.create_test_game('puzzle')
        test_user_id = str(ObjectId())

        # Mock plugin
        self.mock_plugin_loaded('puzzle_game', {'category': 'puzzle'})

        session_data, plugin_session, mock_plugin = self.mock_game_session_flow({
            'user_id': test_user_id,
            'game_id': test_game['_id']
        })

        result = self.service.create_session(test_user_id, test_game['_id'])

        assert result[0] is True
        mock_plugin.start_session.assert_called_once()

# Plugin-specific testing
@game_test(plugin_dependencies=['puzzle_plugin', 'scoring_plugin'])
class TestPuzzlePlugin(GamePluginTest):
    def setUp(self):
        super().setUp()
        from app.games.plugins.puzzle_plugin import PuzzlePlugin
        self.set_plugin_under_test(PuzzlePlugin, difficulty='medium')

    def test_puzzle_plugin_compliance(self):
        self.assert_plugin_compliance()

    def test_puzzle_move_validation(self):
        session = self.plugin_under_test.start_session(str(ObjectId()))
        move_data = {'type': 'move', 'from': [0, 0], 'to': [0, 1]}

        is_valid = self.plugin_under_test.validate_move(session.session_id, move_data)
        assert is_valid is not None

# Multiplayer game testing
class TestMultiplayerGameService(BaseGameTest):
    service_class = MultiplayerGameService

    def test_match_making(self):
        scenario = self.create_multiplayer_scenario(4, {'category': 'strategy'})
        mock_plugin = self.mock_multiplayer_match_making(scenario)

        result = self.service.find_match(scenario['players'][0]['_id'], scenario['game']['_id'])

        assert result[0] is True
        assert 'match_id' in result[2]

# Performance testing
class TestGamePerformance(BaseGameTest):
    service_class = GameService

    def test_session_creation_performance(self):
        scenarios = self.create_performance_test_scenario(50)

        def create_session_operation(scenario):
            return self.service.create_session(scenario['user_id'], scenario['game_id'])

        benchmark = self.benchmark_game_operation(create_session_operation, scenarios)

        # Assert performance requirements
        assert benchmark['avg_duration_ms'] < 100, f"Average session creation too slow: {benchmark['avg_duration_ms']}ms"
"""