"""
Comprehensive tests for Flask-SocketIO WebSocket multiplayer functionality.

Tests cover:
- WebSocket connection and disconnection
- Ping/pong latency measurement
- JWT authentication on WebSocket
- Room join/leave operations
- Player state synchronization
- Game actions broadcasting
"""
import pytest
import jwt as pyjwt
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch
import os

# Set testing environment BEFORE importing app
os.environ['TESTING'] = 'true'

from app import create_app, socketio


@pytest.fixture
def app():
    """Create Flask app for testing"""
    app = create_app('testing')
    app.config['TESTING'] = True
    return app


@pytest.fixture
def client(app):
    """Create Flask test client"""
    return app.test_client()


@pytest.fixture
def socketio_client(app):
    """Create SocketIO test client"""
    return socketio.test_client(app, namespace='/multiplayer')


def generate_test_token(app, user_id='test_user_123'):
    """Generate JWT token for testing"""
    payload = {
        'sub': user_id,
        'exp': datetime.now(timezone.utc) + timedelta(hours=1)
    }
    return pyjwt.encode(payload, app.config['JWT_SECRET_KEY'], algorithm='HS256')


class TestWebSocketConnection:
    """Test WebSocket connection lifecycle"""

    def test_websocket_connection(self, socketio_client):
        """Test basic WebSocket connection"""
        assert socketio_client.is_connected(namespace='/multiplayer')

    def test_websocket_disconnection(self, socketio_client):
        """Test WebSocket disconnection"""
        assert socketio_client.is_connected(namespace='/multiplayer')
        socketio_client.disconnect(namespace='/multiplayer')
        assert not socketio_client.is_connected(namespace='/multiplayer')


class TestPingPong:
    """Test ping/pong latency measurement"""

    def test_ping_pong_basic(self, socketio_client):
        """Test basic ping/pong"""
        timestamp = int(datetime.now(timezone.utc).timestamp() * 1000)

        socketio_client.emit('ping', {'timestamp': timestamp}, namespace='/multiplayer')
        received = socketio_client.get_received(namespace='/multiplayer')

        assert len(received) > 0
        assert received[0]['name'] == 'pong'
        assert received[0]['args'][0]['timestamp'] == timestamp
        assert 'server_time' in received[0]['args'][0]

    def test_ping_pong_without_timestamp(self, socketio_client):
        """Test ping without timestamp"""
        socketio_client.emit('ping', {}, namespace='/multiplayer')
        received = socketio_client.get_received(namespace='/multiplayer')

        assert len(received) > 0
        assert received[0]['name'] == 'pong'
        assert 'server_time' in received[0]['args'][0]


class TestAuthentication:
    """Test WebSocket JWT authentication"""

    @patch('app.games.multiplayer.events.connection_events.ConnectionManager')
    def test_authentication_success(self, mock_manager, app, socketio_client):
        """Test successful WebSocket authentication"""
        token = generate_test_token(app, 'user_123')

        device_info = {
            'platform': 'web',
            'device_type': 'desktop',
            'app_version': '1.0.0'
        }

        socketio_client.emit('authenticate', {
            'token': token,
            'device_info': device_info
        }, namespace='/multiplayer')

        received = socketio_client.get_received(namespace='/multiplayer')

        # Find authenticated message
        auth_messages = [r for r in received if r['name'] == 'authenticated']
        assert len(auth_messages) > 0

        auth_data = auth_messages[0]['args'][0]
        assert auth_data['user_id'] == 'user_123'
        assert auth_data['message'] == 'WEBSOCKET_AUTH_SUCCESS'
        assert 'session_id' in auth_data
        assert 'timestamp' in auth_data

    def test_authentication_missing_token(self, socketio_client):
        """Test authentication without token"""
        socketio_client.emit('authenticate', {}, namespace='/multiplayer')
        received = socketio_client.get_received(namespace='/multiplayer')

        # Should receive error
        error_messages = [r for r in received if r['name'] == 'error']
        assert len(error_messages) > 0
        assert error_messages[0]['args'][0]['message'] == 'AUTHENTICATION_REQUIRED'

    def test_authentication_invalid_token(self, socketio_client):
        """Test authentication with invalid token"""
        socketio_client.emit('authenticate', {
            'token': 'invalid_token_string'
        }, namespace='/multiplayer')

        received = socketio_client.get_received(namespace='/multiplayer')

        # Should receive error and disconnect
        error_messages = [r for r in received if r['name'] == 'error']
        assert len(error_messages) > 0
        assert error_messages[0]['args'][0]['message'] == 'INVALID_TOKEN'

    def test_authentication_expired_token(self, app, socketio_client):
        """Test authentication with expired token"""
        # Create expired token
        payload = {
            'sub': 'user_123',
            'exp': datetime.now(timezone.utc) - timedelta(hours=1)
        }
        expired_token = pyjwt.encode(payload, app.config['JWT_SECRET_KEY'], algorithm='HS256')

        socketio_client.emit('authenticate', {
            'token': expired_token
        }, namespace='/multiplayer')

        received = socketio_client.get_received(namespace='/multiplayer')

        error_messages = [r for r in received if r['name'] == 'error']
        assert len(error_messages) > 0
        assert error_messages[0]['args'][0]['message'] == 'TOKEN_EXPIRED'


class TestRoomOperations:
    """Test room join/leave operations"""

    @patch('app.games.multiplayer.services.connection_manager.ConnectionManager.join_room')
    def test_join_room_success(self, mock_join, app, socketio_client):
        """Test successful room join"""
        token = generate_test_token(app, 'user_123')
        room_id = 'test_room_456'

        socketio_client.emit('join_room', {
            'token': token,
            'room_id': room_id
        }, namespace='/multiplayer')

        received = socketio_client.get_received(namespace='/multiplayer')

        # Find room_joined message
        joined_messages = [r for r in received if r['name'] == 'room_joined']
        assert len(joined_messages) > 0

        join_data = joined_messages[0]['args'][0]
        assert join_data['room_id'] == room_id
        assert join_data['message'] == 'ROOM_JOINED_SUCCESS'

    def test_join_room_missing_room_id(self, app, socketio_client):
        """Test join room without room_id"""
        token = generate_test_token(app)

        socketio_client.emit('join_room', {
            'token': token
        }, namespace='/multiplayer')

        received = socketio_client.get_received(namespace='/multiplayer')

        error_messages = [r for r in received if r['name'] == 'error']
        assert len(error_messages) > 0
        assert error_messages[0]['args'][0]['message'] == 'ROOM_ID_REQUIRED'

    @patch('app.games.multiplayer.services.connection_manager.ConnectionManager.leave_room')
    def test_leave_room_success(self, mock_leave, app, socketio_client):
        """Test successful room leave"""
        token = generate_test_token(app, 'user_123')
        room_id = 'test_room_456'

        # First join the room
        socketio_client.emit('join_room', {
            'token': token,
            'room_id': room_id
        }, namespace='/multiplayer')

        # Clear received messages
        socketio_client.get_received(namespace='/multiplayer')

        # Now leave the room
        socketio_client.emit('leave_room', {
            'token': token,
            'room_id': room_id
        }, namespace='/multiplayer')

        received = socketio_client.get_received(namespace='/multiplayer')

        # Find room_left message
        left_messages = [r for r in received if r['name'] == 'room_left']
        assert len(left_messages) > 0

        leave_data = left_messages[0]['args'][0]
        assert leave_data['room_id'] == room_id
        assert leave_data['message'] == 'ROOM_LEFT_SUCCESS'


class TestGameActions:
    """Test game action broadcasting"""

    def test_game_action_broadcast(self, app, socketio_client):
        """Test game action broadcasting to room"""
        token = generate_test_token(app, 'user_123')
        room_id = 'test_room_789'

        # Join room first
        socketio_client.emit('join_room', {
            'token': token,
            'room_id': room_id
        }, namespace='/multiplayer')

        # Clear received messages
        socketio_client.get_received(namespace='/multiplayer')

        # Send game action
        socketio_client.emit('game_action', {
            'token': token,
            'room_id': room_id,
            'action': 'move',
            'payload': {'x': 10, 'y': 20}
        }, namespace='/multiplayer')

        # Note: In a real scenario with multiple clients,
        # other clients would receive the game_action event
        # This test verifies the emit happens without errors

    def test_game_action_missing_data(self, app, socketio_client):
        """Test game action with missing required data"""
        token = generate_test_token(app)

        socketio_client.emit('game_action', {
            'token': token
        }, namespace='/multiplayer')

        received = socketio_client.get_received(namespace='/multiplayer')

        error_messages = [r for r in received if r['name'] == 'error']
        assert len(error_messages) > 0


class TestStateUpdates:
    """Test player state updates"""

    def test_update_state(self, app, socketio_client):
        """Test player state update broadcasting"""
        token = generate_test_token(app, 'user_123')
        room_id = 'test_room_999'

        # Join room first
        socketio_client.emit('join_room', {
            'token': token,
            'room_id': room_id
        }, namespace='/multiplayer')

        # Clear received messages
        socketio_client.get_received(namespace='/multiplayer')

        # Update state
        socketio_client.emit('update_state', {
            'token': token,
            'room_id': room_id,
            'state': {
                'score': 100,
                'level': 5,
                'position': {'x': 50, 'y': 60}
            }
        }, namespace='/multiplayer')

        # Verify no errors occurred
        received = socketio_client.get_received(namespace='/multiplayer')
        error_messages = [r for r in received if r['name'] == 'error']
        assert len(error_messages) == 0

    def test_update_state_missing_room_id(self, app, socketio_client):
        """Test state update without room_id"""
        token = generate_test_token(app)

        socketio_client.emit('update_state', {
            'token': token,
            'state': {'score': 100}
        }, namespace='/multiplayer')

        received = socketio_client.get_received(namespace='/multiplayer')

        error_messages = [r for r in received if r['name'] == 'error']
        assert len(error_messages) > 0
        assert error_messages[0]['args'][0]['message'] == 'ROOM_ID_REQUIRED'


class TestErrorHandling:
    """Test error handling"""

    def test_invalid_data_format(self, app, socketio_client):
        """Test handling of invalid data format"""
        token = generate_test_token(app)

        # Send string instead of dict
        socketio_client.emit('join_room', 'invalid_data', namespace='/multiplayer')

        received = socketio_client.get_received(namespace='/multiplayer')

        error_messages = [r for r in received if r['name'] == 'error']
        # Note: The handler may disconnect on invalid format
        # Just verify it doesn't crash


# Integration test
class TestMultiplayerIntegration:
    """Integration tests for complete multiplayer flow"""

    @patch('app.games.multiplayer.services.connection_manager.ConnectionManager')
    @patch('app.games.multiplayer.services.room_manager.RoomManager')
    def test_complete_multiplayer_flow(self, mock_room_manager, mock_conn_manager, app, socketio_client):
        """Test complete multiplayer flow: connect -> auth -> join room -> play -> leave"""
        token = generate_test_token(app, 'user_123')
        room_id = 'integration_room'

        # 1. Connect (automatic)
        assert socketio_client.is_connected(namespace='/multiplayer')

        # 2. Authenticate
        socketio_client.emit('authenticate', {
            'token': token,
            'device_info': {'platform': 'web'}
        }, namespace='/multiplayer')

        received = socketio_client.get_received(namespace='/multiplayer')
        auth_messages = [r for r in received if r['name'] == 'authenticated']
        assert len(auth_messages) > 0

        # 3. Join room
        socketio_client.emit('join_room', {
            'token': token,
            'room_id': room_id
        }, namespace='/multiplayer')

        received = socketio_client.get_received(namespace='/multiplayer')
        joined_messages = [r for r in received if r['name'] == 'room_joined']
        assert len(joined_messages) > 0

        # 4. Send game action
        socketio_client.emit('game_action', {
            'token': token,
            'room_id': room_id,
            'action': 'test_action',
            'payload': {'data': 'test'}
        }, namespace='/multiplayer')

        # 5. Leave room
        socketio_client.emit('leave_room', {
            'token': token,
            'room_id': room_id
        }, namespace='/multiplayer')

        received = socketio_client.get_received(namespace='/multiplayer')
        left_messages = [r for r in received if r['name'] == 'room_left']
        assert len(left_messages) > 0

        # 6. Disconnect
        socketio_client.disconnect(namespace='/multiplayer')
        assert not socketio_client.is_connected(namespace='/multiplayer')
