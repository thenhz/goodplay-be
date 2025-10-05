from datetime import datetime, timezone
from typing import Dict, Optional, Any
from app.core.utils.json_encoder import serialize_model_dates


class MultiplayerSession:
    """
    Model for tracking active WebSocket multiplayer sessions.

    Attributes:
        session_id: Unique WebSocket session identifier (socket.sid)
        user_id: ID of the authenticated user
        room_id: Optional game room ID if user is in a room
        device_info: Device information (platform, type, app_version)
        connected_at: Connection timestamp
        last_ping: Last ping/pong timestamp for latency monitoring
        latency_ms: Current latency in milliseconds
        status: Session status (active, idle, disconnected)
        metadata: Additional session metadata
    """

    COLLECTION_NAME = 'multiplayer_sessions'

    STATUS_ACTIVE = 'active'
    STATUS_IDLE = 'idle'
    STATUS_DISCONNECTED = 'disconnected'

    def __init__(
        self,
        session_id: str,
        user_id: str,
        device_info: Optional[Dict[str, str]] = None,
        room_id: Optional[str] = None,
        connected_at: Optional[datetime] = None,
        last_ping: Optional[datetime] = None,
        latency_ms: Optional[int] = None,
        status: str = STATUS_ACTIVE,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.session_id = session_id
        self.user_id = user_id
        self.room_id = room_id
        self.device_info = device_info or {}
        self.connected_at = connected_at or datetime.now(timezone.utc)
        self.last_ping = last_ping
        self.latency_ms = latency_ms
        self.status = status
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary for MongoDB storage"""
        session_dict = {
            'session_id': self.session_id,
            'user_id': self.user_id,
            'room_id': self.room_id,
            'device_info': self.device_info,
            'connected_at': self.connected_at,
            'last_ping': self.last_ping,
            'latency_ms': self.latency_ms,
            'status': self.status,
            'metadata': self.metadata
        }
        return serialize_model_dates(session_dict)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'MultiplayerSession':
        """Create MultiplayerSession from dictionary"""
        return MultiplayerSession(
            session_id=data['session_id'],
            user_id=data['user_id'],
            device_info=data.get('device_info'),
            room_id=data.get('room_id'),
            connected_at=data.get('connected_at'),
            last_ping=data.get('last_ping'),
            latency_ms=data.get('latency_ms'),
            status=data.get('status', MultiplayerSession.STATUS_ACTIVE),
            metadata=data.get('metadata', {})
        )

    def update_ping(self, latency_ms: int) -> None:
        """Update ping timestamp and latency"""
        self.last_ping = datetime.now(timezone.utc)
        self.latency_ms = latency_ms

    def join_room(self, room_id: str) -> None:
        """Update session with room information"""
        self.room_id = room_id

    def leave_room(self) -> None:
        """Remove room information from session"""
        self.room_id = None

    def disconnect(self) -> None:
        """Mark session as disconnected"""
        self.status = self.STATUS_DISCONNECTED
