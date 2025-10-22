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
