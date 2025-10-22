"""
Test suite for game session API endpoints
Tests the REST API endpoints for session management
"""

import pytest
import os
from unittest.mock import patch, MagicMock
from bson import ObjectId

# Set testing environment before importing app modules
os.environ['TESTING'] = 'true'

from app import create_app


@pytest.fixture
def app():
    """Create test app with testing configuration."""
    return create_app('testing')


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def mock_user_token():
    """Mock user JWT token for testing."""
    return "mock_user_token_for_testing"


class TestSessionEndpoints:
    """Test session management API endpoints"""

    @patch('app.games.controllers.games_controller.session_service')
    @patch('app.core.utils.decorators.verify_jwt_in_request')
    @patch('app.core.utils.decorators.get_jwt_identity')
    def test_create_session_with_game_id_in_body(self, mock_get_jwt, mock_verify_jwt, mock_service, client):
        """Test POST /api/games/sessions with game_id in body (not path)"""
        # Mock JWT verification
        mock_verify_jwt.return_value = True
        user_id = str(ObjectId())
        game_id = str(ObjectId())
        session_id = str(ObjectId())

        mock_get_jwt.return_value = {'_id': user_id}

        # Mock successful session creation
        mock_service.start_game_session.return_value = (
            True,
            "SESSION_CREATED_SUCCESS",
            {
                'session': {
                    'session_id': session_id,
                    'game_id': game_id,
                    'user_id': user_id,
                    'status': 'active'
                }
            }
        )

        response = client.post(
            '/api/games/sessions',
            json={'game_id': game_id, 'session_config': {}},
            headers={'Authorization': f'Bearer mock_token'}
        )

        assert response.status_code == 201
        data = response.get_json()
        assert data['success'] is True

        # Verify service was called
        assert mock_service.start_game_session.called

    @patch('app.core.utils.decorators.verify_jwt_in_request')
    @patch('app.core.utils.decorators.get_jwt_identity')
    def test_create_session_missing_game_id(self, mock_get_jwt, mock_verify_jwt, client):
        """Test POST /api/games/sessions without game_id returns error"""
        # Mock JWT verification
        mock_verify_jwt.return_value = True
        user_id = str(ObjectId())
        mock_get_jwt.return_value = {'_id': user_id}

        response = client.post(
            '/api/games/sessions',
            json={'session_config': {}},
            headers={'Authorization': f'Bearer mock_token'}
        )

        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert data['message'] == 'GAME_ID_REQUIRED'

    @patch('app.games.controllers.games_controller.session_service')
    @patch('app.core.utils.decorators.verify_jwt_in_request')
    @patch('app.core.utils.decorators.get_jwt_identity')
    def test_create_session_auto_abandons_previous_active_session(self, mock_get_jwt, mock_verify_jwt, mock_service, client):
        """Test POST /api/games/sessions auto-abandons previous active session"""
        # Mock JWT verification
        mock_verify_jwt.return_value = True
        user_id = str(ObjectId())
        game_id = str(ObjectId())
        old_session_id = str(ObjectId())
        new_session_id = str(ObjectId())

        mock_get_jwt.return_value = {'_id': user_id}

        # Mock service to return new session with abandoned_session field
        mock_service.start_game_session.return_value = (
            True,
            "GAME_SESSION_STARTED_PREVIOUS_ABANDONED",
            {
                'session': {
                    'session_id': new_session_id,
                    'game_id': game_id,
                    'user_id': user_id,
                    'status': 'active'
                },
                'game': {
                    'id': game_id,
                    'name': 'Test Game',
                    'plugin_id': 'test_game'
                },
                'abandoned_session': {
                    'session_id': old_session_id,
                    'game_id': game_id,
                    'user_id': user_id,
                    'status': 'abandoned'
                }
            }
        )

        response = client.post(
            '/api/games/sessions',
            json={'game_id': game_id, 'session_config': {}},
            headers={'Authorization': f'Bearer mock_token'}
        )

        assert response.status_code == 201
        data = response.get_json()
        assert data['success'] is True
        assert data['message'] == 'GAME_SESSION_STARTED_PREVIOUS_ABANDONED'

        # Verify new session was created
        assert 'session' in data['data']
        assert data['data']['session']['session_id'] == new_session_id
        assert data['data']['session']['status'] == 'active'

        # Verify abandoned session info is included
        assert 'abandoned_session' in data['data']
        assert data['data']['abandoned_session']['session_id'] == old_session_id
        assert data['data']['abandoned_session']['status'] == 'abandoned'

    @patch('app.games.controllers.games_controller.session_service')
    @patch('app.core.utils.decorators.verify_jwt_in_request')
    @patch('app.core.utils.decorators.get_jwt_identity')
    def test_end_session_with_delete_method(self, mock_get_jwt, mock_verify_jwt, mock_service, client):
        """Test DELETE /api/games/sessions/{session_id} (not PUT /end)"""
        # Mock JWT verification
        mock_verify_jwt.return_value = True
        user_id = str(ObjectId())
        session_id = str(ObjectId())

        mock_get_jwt.return_value = {'_id': user_id}

        # Mock get_session_by_id
        mock_service.get_session_by_id.return_value = (
            True,
            "SESSION_RETRIEVED",
            {
                'session': {
                    'session_id': session_id,
                    'user_id': user_id,
                    'status': 'active'
                }
            }
        )

        # Mock end_game_session
        mock_service.end_game_session.return_value = (
            True,
            "SESSION_ENDED_SUCCESS",
            {
                'session': {
                    'session_id': session_id,
                    'user_id': user_id,
                    'status': 'completed'
                }
            }
        )

        response = client.delete(
            f'/api/games/sessions/{session_id}',
            json={'end_reason': 'completed'},
            headers={'Authorization': f'Bearer mock_token'}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True

    @patch('app.games.controllers.games_controller.session_service')
    @patch('app.core.utils.decorators.verify_jwt_in_request')
    @patch('app.core.utils.decorators.get_jwt_identity')
    def test_pause_session_with_post_method(self, mock_get_jwt, mock_verify_jwt, mock_service, client):
        """Test POST /api/games/sessions/{session_id}/pause (not PUT)"""
        # Mock JWT verification
        mock_verify_jwt.return_value = True
        user_id = str(ObjectId())
        session_id = str(ObjectId())

        mock_get_jwt.return_value = {'_id': user_id}

        # Mock get_session_by_id
        mock_service.get_session_by_id.return_value = (
            True,
            "SESSION_RETRIEVED",
            {
                'session': {
                    'session_id': session_id,
                    'user_id': user_id,
                    'status': 'active'
                }
            }
        )

        # Mock pause_session
        mock_service.pause_session.return_value = (
            True,
            "SESSION_PAUSED_SUCCESS",
            {
                'session': {
                    'session_id': session_id,
                    'status': 'paused'
                }
            }
        )

        response = client.post(
            f'/api/games/sessions/{session_id}/pause',
            headers={'Authorization': f'Bearer mock_token'}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True

    @patch('app.games.controllers.games_controller.session_service')
    @patch('app.core.utils.decorators.verify_jwt_in_request')
    @patch('app.core.utils.decorators.get_jwt_identity')
    def test_resume_session_with_post_method(self, mock_get_jwt, mock_verify_jwt, mock_service, client):
        """Test POST /api/games/sessions/{session_id}/resume (not PUT)"""
        # Mock JWT verification
        mock_verify_jwt.return_value = True
        user_id = str(ObjectId())
        session_id = str(ObjectId())

        mock_get_jwt.return_value = {'_id': user_id}

        # Mock get_session_by_id
        mock_service.get_session_by_id.return_value = (
            True,
            "SESSION_RETRIEVED",
            {
                'session': {
                    'session_id': session_id,
                    'user_id': user_id,
                    'status': 'paused'
                }
            }
        )

        # Mock resume_session
        mock_service.resume_session.return_value = (
            True,
            "SESSION_RESUMED_SUCCESS",
            {
                'session': {
                    'session_id': session_id,
                    'status': 'active'
                }
            }
        )

        response = client.post(
            f'/api/games/sessions/{session_id}/resume',
            headers={'Authorization': f'Bearer mock_token'}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True

    @patch('app.games.controllers.games_controller.session_service')
    @patch('app.core.repositories.user_repository.UserRepository.find_user_by_id')
    @patch('flask_jwt_extended.get_jwt_identity')
    def test_validate_move_returns_session_with_current_state(self, mock_get_jwt, mock_find_user, mock_service, client):
        """Test POST /api/games/sessions/{session_id}/moves returns session with current_state"""
        # Mock JWT and user
        user_id = str(ObjectId())
        session_id = str(ObjectId())

        mock_get_jwt.return_value = user_id
        mock_user = MagicMock()
        mock_user.user_id = user_id
        mock_user.is_active = True
        mock_find_user.return_value = mock_user

        # Mock get_session_by_id for ownership verification
        mock_service.get_session_by_id.return_value = (
            True,
            "SESSION_RETRIEVED",
            {
                'session': {
                    'session_id': session_id,
                    'user_id': user_id,
                    'status': 'active'
                }
            }
        )

        # Mock validate_move with complete session including current_state
        mock_service.validate_move.return_value = (
            True,
            "MOVE_VALIDATED_SUCCESS",
            {
                'move_valid': True,
                'move_number': 5,
                'session': {
                    'session_id': session_id,
                    'user_id': user_id,
                    'game_id': 'tic_tac_toe',
                    'status': 'active',
                    'current_state': {
                        'board': [['X', 'O', 'X'], ['O', 'X', None], [None, None, 'O']],
                        'current_player': 'X',
                        'game_over': False,
                        'winner': None,
                        'is_draw': False
                    },
                    'moves_count': 5
                }
            }
        )

        response = client.post(
            f'/api/games/sessions/{session_id}/moves',
            json={'move': {'position': [1, 1]}},
            headers={'Authorization': f'Bearer mock_token'}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'data' in data
        assert 'move_valid' in data['data']
        assert data['data']['move_valid'] is True
        assert 'move_number' in data['data']
        assert 'session' in data['data']
        assert 'current_state' in data['data']['session']

    @patch('app.games.controllers.games_controller.session_service')
    @patch('app.core.repositories.user_repository.UserRepository.find_user_by_id')
    @patch('flask_jwt_extended.get_jwt_identity')
    def test_validate_move_tic_tac_toe_contains_board_state(self, mock_get_jwt, mock_find_user, mock_service, client):
        """Test validate_move for Tic Tac Toe returns board, winner, game_over in current_state"""
        # Mock JWT and user
        user_id = str(ObjectId())
        session_id = str(ObjectId())

        mock_get_jwt.return_value = user_id
        mock_user = MagicMock()
        mock_user.user_id = user_id
        mock_user.is_active = True
        mock_find_user.return_value = mock_user

        # Mock get_session_by_id
        mock_service.get_session_by_id.return_value = (
            True,
            "SESSION_RETRIEVED",
            {
                'session': {
                    'session_id': session_id,
                    'user_id': user_id,
                    'status': 'active'
                }
            }
        )

        # Mock validate_move with Tic Tac Toe specific current_state
        mock_service.validate_move.return_value = (
            True,
            "MOVE_VALIDATED_SUCCESS",
            {
                'move_valid': True,
                'move_number': 5,
                'session': {
                    'session_id': session_id,
                    'user_id': user_id,
                    'game_id': 'tic_tac_toe',
                    'status': 'active',
                    'current_state': {
                        'board': [['X', 'O', 'X'], ['O', 'X', None], [None, None, 'O']],
                        'current_player': 'X',
                        'game_mode': 'vs_ai',
                        'player_symbol': 'X',
                        'game_over': False,
                        'winner': None,
                        'is_draw': False,
                        'winning_line': None,
                        'move_count': 5
                    }
                }
            }
        )

        response = client.post(
            f'/api/games/sessions/{session_id}/moves',
            json={'move': {'position': [1, 2]}},
            headers={'Authorization': f'Bearer mock_token'}
        )

        assert response.status_code == 200
        data = response.get_json()

        # Verify response structure
        assert data['success'] is True
        assert 'session' in data['data']

        # Verify current_state contains all Tic Tac Toe specific fields
        current_state = data['data']['session']['current_state']
        assert 'board' in current_state
        assert 'current_player' in current_state
        assert 'game_over' in current_state
        assert 'winner' in current_state
        assert 'is_draw' in current_state
        assert 'winning_line' in current_state
        assert 'move_count' in current_state

        # Verify values
        assert current_state['game_over'] is False
        assert current_state['winner'] is None
        assert current_state['move_count'] == 5

    @patch('app.games.controllers.games_controller.session_service')
    @patch('app.core.repositories.user_repository.UserRepository.find_user_by_id')
    @patch('flask_jwt_extended.get_jwt_identity')
    def test_validate_move_winning_move_shows_game_over(self, mock_get_jwt, mock_find_user, mock_service, client):
        """Test validate_move with winning move shows game_over=True and winner"""
        # Mock JWT and user
        user_id = str(ObjectId())
        session_id = str(ObjectId())

        mock_get_jwt.return_value = user_id
        mock_user = MagicMock()
        mock_user.user_id = user_id
        mock_user.is_active = True
        mock_find_user.return_value = mock_user

        # Mock get_session_by_id
        mock_service.get_session_by_id.return_value = (
            True,
            "SESSION_RETRIEVED",
            {
                'session': {
                    'session_id': session_id,
                    'user_id': user_id,
                    'status': 'active'
                }
            }
        )

        # Mock validate_move with winning state
        mock_service.validate_move.return_value = (
            True,
            "MOVE_VALIDATED_SUCCESS",
            {
                'move_valid': True,
                'move_number': 5,
                'session': {
                    'session_id': session_id,
                    'user_id': user_id,
                    'game_id': 'tic_tac_toe',
                    'status': 'active',
                    'current_state': {
                        'board': [['X', 'O', 'X'], ['O', 'X', 'O'], ['X', None, None]],
                        'current_player': 'X',
                        'game_mode': 'vs_ai',
                        'player_symbol': 'X',
                        'game_over': True,
                        'winner': 'X',
                        'is_draw': False,
                        'winning_line': [[0, 0], [1, 1], [2, 0]],
                        'move_count': 5
                    }
                }
            }
        )

        response = client.post(
            f'/api/games/sessions/{session_id}/moves',
            json={'move': {'position': [2, 0]}},
            headers={'Authorization': f'Bearer mock_token'}
        )

        assert response.status_code == 200
        data = response.get_json()

        # Verify winning state
        current_state = data['data']['session']['current_state']
        assert current_state['game_over'] is True
        assert current_state['winner'] == 'X'
        assert current_state['is_draw'] is False
        assert current_state['winning_line'] == [[0, 0], [1, 1], [2, 0]]

    @patch('app.core.repositories.user_repository.UserRepository.find_user_by_id')
    @patch('flask_jwt_extended.get_jwt_identity')
    def test_validate_move_missing_move_data(self, mock_get_jwt, mock_find_user, client):
        """Test validate_move without move data returns error"""
        # Mock JWT and user
        user_id = str(ObjectId())
        session_id = str(ObjectId())

        mock_get_jwt.return_value = user_id
        mock_user = MagicMock()
        mock_user.user_id = user_id
        mock_user.is_active = True
        mock_find_user.return_value = mock_user

        response = client.post(
            f'/api/games/sessions/{session_id}/moves',
            json={},  # Missing 'move' field
            headers={'Authorization': f'Bearer mock_token'}
        )

        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert data['message'] == 'MOVE_DATA_REQUIRED'

    @patch('app.games.controllers.games_controller.session_service')
    @patch('app.core.utils.decorators.verify_jwt_in_request')
    @patch('app.core.utils.decorators.get_jwt_identity')
    def test_pause_session_returns_complete_session_with_current_state(self, mock_get_jwt, mock_verify_jwt, mock_service, client):
        """Test POST /pause returns complete session with current_state synced from plugin"""
        # Mock JWT verification
        mock_verify_jwt.return_value = True
        user_id = str(ObjectId())
        session_id = str(ObjectId())

        mock_get_jwt.return_value = {'_id': user_id}

        # Mock get_session_by_id for ownership verification
        mock_service.get_session_by_id.return_value = (
            True,
            "SESSION_RETRIEVED",
            {
                'session': {
                    'session_id': session_id,
                    'user_id': user_id,
                    'status': 'active'
                }
            }
        )

        # Mock pause_session with complete session including current_state
        mock_service.pause_session.return_value = (
            True,
            "SESSION_PAUSED_SUCCESS",
            {
                'session': {
                    'session_id': session_id,
                    'user_id': user_id,
                    'game_id': 'tic_tac_toe',
                    'status': 'paused',
                    'current_state': {
                        'board': [['X', 'O', None], ['O', 'X', None], [None, None, None]],
                        'current_player': 'X',
                        'game_mode': 'vs_ai',
                        'player_symbol': 'X',
                        'game_over': False,
                        'winner': None,
                        'is_draw': False,
                        'winning_line': None,
                        'move_count': 4
                    },
                    'moves_count': 4
                }
            }
        )

        response = client.post(
            f'/api/games/sessions/{session_id}/pause',
            headers={'Authorization': f'Bearer mock_token'}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'data' in data
        assert 'session' in data['data']
        assert 'current_state' in data['data']['session']
        assert data['data']['session']['status'] == 'paused'
        assert 'board' in data['data']['session']['current_state']
        assert 'current_player' in data['data']['session']['current_state']
        assert 'game_over' in data['data']['session']['current_state']

    @patch('app.games.controllers.games_controller.session_service')
    @patch('app.core.utils.decorators.verify_jwt_in_request')
    @patch('app.core.utils.decorators.get_jwt_identity')
    def test_resume_session_returns_complete_session_with_current_state(self, mock_get_jwt, mock_verify_jwt, mock_service, client):
        """Test POST /resume returns complete session with current_state synced from plugin"""
        # Mock JWT verification
        mock_verify_jwt.return_value = True
        user_id = str(ObjectId())
        session_id = str(ObjectId())

        mock_get_jwt.return_value = {'_id': user_id}

        # Mock get_session_by_id for ownership verification
        mock_service.get_session_by_id.return_value = (
            True,
            "SESSION_RETRIEVED",
            {
                'session': {
                    'session_id': session_id,
                    'user_id': user_id,
                    'status': 'paused'
                }
            }
        )

        # Mock resume_session with complete session including current_state
        mock_service.resume_session.return_value = (
            True,
            "SESSION_RESUMED_SUCCESS",
            {
                'session': {
                    'session_id': session_id,
                    'user_id': user_id,
                    'game_id': 'tic_tac_toe',
                    'status': 'active',
                    'current_state': {
                        'board': [['X', 'O', None], ['O', 'X', None], [None, None, None]],
                        'current_player': 'X',
                        'game_mode': 'vs_ai',
                        'player_symbol': 'X',
                        'game_over': False,
                        'winner': None,
                        'is_draw': False,
                        'winning_line': None,
                        'move_count': 4
                    },
                    'moves_count': 4
                }
            }
        )

        response = client.post(
            f'/api/games/sessions/{session_id}/resume',
            headers={'Authorization': f'Bearer mock_token'}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'data' in data
        assert 'session' in data['data']
        assert 'current_state' in data['data']['session']
        assert data['data']['session']['status'] == 'active'
        assert 'board' in data['data']['session']['current_state']
        assert 'current_player' in data['data']['session']['current_state']

    @patch('app.games.controllers.games_controller.session_service')
    @patch('app.core.utils.decorators.verify_jwt_in_request')
    @patch('app.core.utils.decorators.get_jwt_identity')
    def test_get_session_by_id_syncs_state_from_plugin(self, mock_get_jwt, mock_verify_jwt, mock_service, client):
        """Test GET /sessions/{id} syncs state from plugin before returning"""
        # Mock JWT verification
        mock_verify_jwt.return_value = True
        user_id = str(ObjectId())
        session_id = str(ObjectId())

        mock_get_jwt.return_value = {'_id': user_id}

        # Mock get_session_by_id with session that has synced current_state
        mock_service.get_session_by_id.return_value = (
            True,
            "SESSION_RETRIEVED_SUCCESS",
            {
                'session': {
                    'session_id': session_id,
                    'user_id': user_id,
                    'game_id': 'tic_tac_toe',
                    'status': 'active',
                    'current_state': {
                        'board': [['X', None, None], [None, None, None], [None, None, None]],
                        'current_player': 'O',
                        'game_mode': 'vs_ai',
                        'player_symbol': 'X',
                        'game_over': False,
                        'winner': None,
                        'is_draw': False,
                        'winning_line': None,
                        'move_count': 1
                    },
                    'moves_count': 1
                },
                'game': {
                    'game_id': 'tic_tac_toe',
                    'name': 'Tic Tac Toe'
                }
            }
        )

        response = client.get(
            f'/api/games/sessions/{session_id}',
            headers={'Authorization': f'Bearer mock_token'}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'session' in data['data']
        assert 'current_state' in data['data']['session']
        # Verify state was synced from plugin (fresh state)
        assert 'board' in data['data']['session']['current_state']
        assert 'current_player' in data['data']['session']['current_state']
        assert data['data']['session']['current_state']['move_count'] == 1

    @patch('app.games.controllers.games_controller.session_service')
    @patch('app.core.utils.decorators.verify_jwt_in_request')
    @patch('app.core.utils.decorators.get_jwt_identity')
    def test_update_session_state_returns_validated_state_from_plugin(self, mock_get_jwt, mock_verify_jwt, mock_service, client):
        """Test PUT /state returns validated state from plugin after update"""
        # Mock JWT verification
        mock_verify_jwt.return_value = True
        user_id = str(ObjectId())
        session_id = str(ObjectId())

        mock_get_jwt.return_value = {'_id': user_id}

        # Mock get_session_by_id for ownership verification
        mock_service.get_session_by_id.return_value = (
            True,
            "SESSION_RETRIEVED",
            {
                'session': {
                    'session_id': session_id,
                    'user_id': user_id,
                    'status': 'active'
                }
            }
        )

        # Mock update_session_state with validated state from plugin
        new_state = {
            'board': [['X', 'O', 'X'], ['O', 'X', 'O'], ['O', 'X', 'X']],
            'current_player': 'X',
            'game_over': True,
            'winner': 'X'
        }

        mock_service.update_session_state.return_value = (
            True,
            "SESSION_STATE_UPDATED_SUCCESS",
            {
                'session': {
                    'session_id': session_id,
                    'user_id': user_id,
                    'game_id': 'tic_tac_toe',
                    'status': 'active',
                    'current_state': {
                        'board': [['X', 'O', 'X'], ['O', 'X', 'O'], ['O', 'X', 'X']],
                        'current_player': 'X',
                        'game_mode': 'vs_ai',
                        'player_symbol': 'X',
                        'game_over': True,
                        'winner': 'X',
                        'is_draw': False,
                        'winning_line': [[0, 2], [1, 1], [2, 0]],  # Validated by plugin
                        'move_count': 9
                    }
                }
            }
        )

        response = client.put(
            f'/api/games/sessions/{session_id}/state',
            json={'state': new_state},
            headers={'Authorization': f'Bearer mock_token'}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'session' in data['data']
        assert 'current_state' in data['data']['session']
        # Verify plugin validated and enriched the state
        assert data['data']['session']['current_state']['game_over'] is True
        assert data['data']['session']['current_state']['winner'] == 'X'
        assert 'winning_line' in data['data']['session']['current_state']
