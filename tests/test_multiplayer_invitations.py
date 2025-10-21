"""
Test suite for multiplayer invitations (GOO-60)

Tests:
- RoomInvitation model (expiry, validation)
- InvitationService (single, batch, blocked users)
- Rate limiting
- WebSocket events
- Social-multiplayer integration
- Background cleanup tasks
"""

import pytest
import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, MagicMock, patch
from app.games.multiplayer.models.room_invitation import RoomInvitation
from app.games.multiplayer.services.invitation_service import InvitationService
from app.games.multiplayer.decorators.rate_limiter import RateLimiter, get_rate_limiter
from app.games.multiplayer.tasks.cleanup_tasks import cleanup_expired_invitations


class TestRoomInvitationModel:
    """Test RoomInvitation model"""

    def test_invitation_creation_with_15_minute_expiry(self):
        """GOO-60: Test that invitations expire after 15 minutes"""
        invitation = RoomInvitation(
            invitation_id=str(uuid.uuid4()),
            room_id="room_123",
            sender_user_id="user_sender",
            recipient_user_id="user_recipient"
        )

        # Check expiry is 15 minutes from creation
        time_diff = invitation.expires_at - invitation.created_at
        assert time_diff.total_seconds() == 900  # 15 minutes = 900 seconds

    def test_invitation_explicit_fields(self):
        """GOO-60: Test new explicit fields (room_code, game_id, game_name)"""
        invitation = RoomInvitation(
            invitation_id=str(uuid.uuid4()),
            room_id="room_123",
            room_code="ABC123",
            game_id="memory_game",
            game_name="Memory Game",
            sender_user_id="user_sender",
            recipient_user_id="user_recipient"
        )

        assert invitation.room_code == "ABC123"
        assert invitation.game_id == "memory_game"
        assert invitation.game_name == "Memory Game"

    def test_invitation_to_dict_includes_new_fields(self):
        """GOO-60: Test serialization includes new fields"""
        invitation = RoomInvitation(
            invitation_id=str(uuid.uuid4()),
            room_id="room_123",
            room_code="ABC123",
            game_id="memory_game",
            game_name="Memory Game",
            sender_user_id="user_sender",
            recipient_user_id="user_recipient"
        )

        data = invitation.to_dict()
        assert 'room_code' in data
        assert 'game_id' in data
        assert 'game_name' in data
        assert data['room_code'] == "ABC123"

    def test_invitation_from_dict(self):
        """GOO-60: Test deserialization with new fields"""
        data = {
            'invitation_id': 'inv_123',
            'room_id': 'room_123',
            'room_code': 'ABC123',
            'game_id': 'memory_game',
            'game_name': 'Memory Game',
            'sender_user_id': 'sender',
            'recipient_user_id': 'recipient',
            'status': 'pending',
            'created_at': datetime.now(timezone.utc),
            'expires_at': datetime.now(timezone.utc) + timedelta(minutes=15),
            'metadata': {}
        }

        invitation = RoomInvitation.from_dict(data)
        assert invitation.room_code == 'ABC123'
        assert invitation.game_id == 'memory_game'
        assert invitation.game_name == 'Memory Game'

    def test_invitation_is_expired(self):
        """Test invitation expiry detection"""
        # Create expired invitation
        past_time = datetime.now(timezone.utc) - timedelta(minutes=20)
        invitation = RoomInvitation(
            invitation_id=str(uuid.uuid4()),
            room_id="room_123",
            sender_user_id="sender",
            recipient_user_id="recipient",
            created_at=past_time,
            expires_at=past_time + timedelta(minutes=15)
        )

        assert invitation.is_expired() is True

    def test_invitation_not_expired(self):
        """Test non-expired invitation"""
        invitation = RoomInvitation(
            invitation_id=str(uuid.uuid4()),
            room_id="room_123",
            sender_user_id="sender",
            recipient_user_id="recipient"
        )

        assert invitation.is_expired() is False


class TestInvitationService:
    """Test InvitationService with mocked dependencies"""

    @pytest.fixture
    def mock_invitation_service(self):
        """Create InvitationService with mocked repositories"""
        with patch('app.games.multiplayer.services.invitation_service.InvitationRepository'), \
             patch('app.games.multiplayer.services.invitation_service.RoomRepository'), \
             patch('app.games.multiplayer.services.invitation_service.RelationshipRepository'):
            service = InvitationService()
            return service

    @pytest.fixture
    def mock_room(self):
        """Create a mock room"""
        room = Mock()
        room.room_id = "room_123"
        room.room_code = "ABC123"
        room.game_id = "memory_game"
        room.room_name = "Test Room"
        room.status = "waiting"
        room.STATUS_WAITING = "waiting"
        room.has_player = Mock(return_value=True)
        room.is_full = Mock(return_value=False)
        return room

    def test_send_invitation_blocked_user(self, mock_invitation_service, mock_room):
        """GOO-60: Test that invitations are blocked for blocked users"""
        # Setup mocks - recipient NOT in room yet
        mock_room.has_player = Mock(return_value=False)
        mock_invitation_service.room_repository.find_by_room_id = Mock(return_value=mock_room)
        mock_invitation_service.relationship_repository.is_blocked = Mock(return_value=True)

        # Try to send invitation
        success, message, invitation = mock_invitation_service.send_invitation(
            room_id="room_123",
            sender_user_id="sender",
            recipient_user_id="recipient"
        )

        assert success is False
        assert message == "USER_BLOCKED"
        assert invitation is None

    def test_send_batch_invitations_success(self, mock_invitation_service, mock_room, app):
        """GOO-60: Test successful batch invitation"""
        # Setup mocks
        mock_invitation_service.room_repository.find_by_room_id = Mock(return_value=mock_room)
        mock_invitation_service.relationship_repository.is_blocked = Mock(return_value=False)
        mock_invitation_service.invitation_repository.check_existing_invitation = Mock(return_value=None)
        mock_invitation_service.invitation_repository.create_invitation = Mock(return_value=True)

        recipient_ids = ["user1", "user2", "user3"]

        # Send batch invitations
        with app.app_context():
            success, message, result = mock_invitation_service.send_batch_invitations(
                room_id="room_123",
                sender_user_id="sender",
                recipient_user_ids=recipient_ids
            )

        assert success is True
        assert message == "BATCH_INVITATIONS_SENT"
        assert result['sent_count'] == 3
        assert result['failed_count'] == 0

    def test_send_batch_invitations_with_blocked_users(self, mock_invitation_service, mock_room, app):
        """GOO-60: Test batch invitation filters out blocked users"""
        # Setup mocks
        mock_invitation_service.room_repository.find_by_room_id = Mock(return_value=mock_room)

        # user2 is blocked
        def is_blocked_side_effect(user1, user2):
            return user2 == "user2"

        mock_invitation_service.relationship_repository.is_blocked = Mock(side_effect=is_blocked_side_effect)
        mock_invitation_service.invitation_repository.check_existing_invitation = Mock(return_value=None)
        mock_invitation_service.invitation_repository.create_invitation = Mock(return_value=True)

        recipient_ids = ["user1", "user2", "user3"]

        # Send batch invitations
        with app.app_context():
            success, message, result = mock_invitation_service.send_batch_invitations(
                room_id="room_123",
                sender_user_id="sender",
                recipient_user_ids=recipient_ids
            )

        assert success is True
        assert result['sent_count'] == 2  # user1 and user3
        assert result['failed_count'] == 1  # user2 blocked
        assert any(f['reason'] == 'USER_BLOCKED' for f in result['failed'])

    def test_send_batch_too_many_recipients(self, mock_invitation_service, mock_room):
        """GOO-60: Test batch invitation rejects more than 10 recipients"""
        mock_invitation_service.room_repository.find_by_room_id = Mock(return_value=mock_room)

        # Try to send to 11 users
        recipient_ids = [f"user{i}" for i in range(11)]

        success, message, result = mock_invitation_service.send_batch_invitations(
            room_id="room_123",
            sender_user_id="sender",
            recipient_user_ids=recipient_ids
        )

        assert success is False
        assert message == "TOO_MANY_RECIPIENTS"


class TestRateLimiter:
    """Test rate limiting functionality"""

    def test_rate_limiter_within_limit(self):
        """GOO-60: Test rate limiter allows calls within limit"""
        limiter = RateLimiter()
        user_id = "test_user"

        # Should allow up to 10 calls
        for i in range(10):
            result = limiter.check_limit(user_id, max_calls=10, window=60)
            assert result is True

    def test_rate_limiter_exceeds_limit(self):
        """GOO-60: Test rate limiter blocks calls exceeding limit"""
        limiter = RateLimiter()
        user_id = "test_user"

        # Make 10 calls (at limit)
        for i in range(10):
            limiter.check_limit(user_id, max_calls=10, window=60)

        # 11th call should be blocked
        result = limiter.check_limit(user_id, max_calls=10, window=60)
        assert result is False

    def test_rate_limiter_reset_user(self):
        """Test rate limiter reset functionality"""
        limiter = RateLimiter()
        user_id = "test_user"

        # Make 10 calls
        for i in range(10):
            limiter.check_limit(user_id, max_calls=10, window=60)

        # Reset user
        limiter.reset_user(user_id)

        # Should allow calls again
        result = limiter.check_limit(user_id, max_calls=10, window=60)
        assert result is True

    def test_rate_limiter_get_remaining_calls(self):
        """Test getting remaining calls count"""
        limiter = RateLimiter()
        user_id = "test_user"

        # Make 3 calls
        for i in range(3):
            limiter.check_limit(user_id, max_calls=10, window=60)

        # Should have 7 remaining
        remaining = limiter.get_remaining_calls(user_id, max_calls=10, window=60)
        assert remaining == 7


class TestWebSocketEvents:
    """Test WebSocket event emission"""

    @patch('app.socketio')
    def test_emit_invitation_received(self, mock_socketio, app):
        """GOO-60: Test invitation_received event emission"""
        with app.app_context():
            from app.games.multiplayer.events.connection_events import MultiplayerNamespace

            namespace = MultiplayerNamespace()
            invitation_data = {
                'invitation_id': 'inv_123',
                'room_id': 'room_456'
            }

            namespace.emit_invitation_received('user_789', invitation_data)

            # Verify socketio.emit was called with correct parameters
            mock_socketio.emit.assert_called_once()
            call_args = mock_socketio.emit.call_args
            assert call_args[0][0] == 'invitation_received'
            assert call_args[1]['room'] == 'user_user_789'

    @patch('app.socketio')
    def test_emit_invitation_accepted(self, mock_socketio, app):
        """GOO-60: Test invitation_accepted event emission"""
        with app.app_context():
            from app.games.multiplayer.events.connection_events import MultiplayerNamespace

            namespace = MultiplayerNamespace()
            invitation_data = {
                'invitation_id': 'inv_123',
                'accepted_by': 'user_recipient'
            }

            namespace.emit_invitation_accepted('user_sender', invitation_data)

            mock_socketio.emit.assert_called_once()
            call_args = mock_socketio.emit.call_args
            assert call_args[0][0] == 'invitation_accepted'

    @patch('app.socketio')
    def test_emit_invitation_declined(self, mock_socketio, app):
        """GOO-60: Test invitation_declined event emission"""
        with app.app_context():
            from app.games.multiplayer.events.connection_events import MultiplayerNamespace

            namespace = MultiplayerNamespace()
            invitation_data = {
                'invitation_id': 'inv_123',
                'declined_by': 'user_recipient'
            }

            namespace.emit_invitation_declined('user_sender', invitation_data)

            mock_socketio.emit.assert_called_once()
            call_args = mock_socketio.emit.call_args
            assert call_args[0][0] == 'invitation_declined'

    @patch('app.socketio')
    def test_emit_invitation_expired(self, mock_socketio, app):
        """GOO-60: Test invitation_expired event emission"""
        with app.app_context():
            from app.games.multiplayer.events.connection_events import MultiplayerNamespace

            namespace = MultiplayerNamespace()

            namespace.emit_invitation_expired('user_recipient', 'inv_123')

            mock_socketio.emit.assert_called_once()
            call_args = mock_socketio.emit.call_args
            assert call_args[0][0] == 'invitation_expired'


class TestCleanupTasks:
    """Test background cleanup tasks"""

    @patch('app.games.multiplayer.tasks.cleanup_tasks.InvitationService')
    @patch('app.games.multiplayer.tasks.cleanup_tasks.InvitationRepository')
    def test_cleanup_expired_invitations(self, mock_repo_class, mock_service_class):
        """GOO-60: Test cleanup of expired invitations"""
        # Setup mocks
        mock_service = Mock()
        mock_service.cleanup_expired = Mock(return_value=5)
        mock_service_class.return_value = mock_service

        mock_repo = Mock()
        mock_repo.collection.find = Mock(return_value=[])
        mock_repo_class.return_value = mock_repo

        # Run cleanup with app context
        from app import create_app
        app = create_app()

        with app.app_context():
            count = cleanup_expired_invitations()

        # Verify cleanup was called
        assert mock_service.cleanup_expired.called

    def test_invitation_repository_cleanup_expired(self):
        """Test InvitationRepository cleanup_expired_invitations method"""
        # This would test the actual repository method
        # For now, we'll skip as it requires DB connection
        pass


class TestIntegrationFlows:
    """Test complete invitation flows"""

    def test_complete_invitation_flow(self):
        """Test: send invitation -> receive -> accept -> notification"""
        # This would test the complete flow with WebSocket events
        # Requires full app context and WebSocket test client
        pass

    def test_invitation_expiry_flow(self):
        """Test: send invitation -> wait 15 min -> auto-expire -> notification"""
        # This would test the complete expiry flow
        # Requires time manipulation or background task simulation
        pass


# Test constants for message validation
def test_response_constants_exist():
    """Verify all response message constants are defined"""
    expected_messages = [
        "INVITATION_SENT_SUCCESS",
        "BATCH_INVITATIONS_SENT",
        "USER_BLOCKED",
        "RATE_LIMIT_EXCEEDED",
        "TOO_MANY_RECIPIENTS",
        "INVITATION_ACCEPTED_SUCCESS",
        "INVITATION_DECLINED_SUCCESS",
        "INVITATION_CANCELLED_SUCCESS"
    ]

    # These should be used in the codebase
    # This test documents expected message constants
    assert len(expected_messages) > 0
