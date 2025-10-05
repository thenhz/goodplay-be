from datetime import datetime, timezone
from typing import Dict, Optional, Any
from app.core.utils.json_encoder import serialize_model_dates


class PlayerState:
    """
    Model for real-time player state in multiplayer games.

    Tracks synchronized game state for each player in a room,
    enabling real-time game state synchronization across devices.

    Attributes:
        state_id: Unique state identifier
        room_id: Associated game room ID
        user_id: Player user ID
        session_id: WebSocket session ID
        game_state: Current game state data
        score: Current player score
        position: Player position in game (if applicable)
        is_ready: Player ready status
        is_active: Player active in current round
        last_action: Timestamp of last player action
        updated_at: Last state update timestamp
        sync_version: Version number for optimistic locking
        metadata: Additional state metadata
    """

    COLLECTION_NAME = 'player_states'

    def __init__(
        self,
        state_id: str,
        room_id: str,
        user_id: str,
        session_id: str,
        game_state: Optional[Dict[str, Any]] = None,
        score: int = 0,
        position: Optional[Dict[str, float]] = None,
        is_ready: bool = False,
        is_active: bool = True,
        last_action: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        sync_version: int = 0,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.state_id = state_id
        self.room_id = room_id
        self.user_id = user_id
        self.session_id = session_id
        self.game_state = game_state or {}
        self.score = score
        self.position = position
        self.is_ready = is_ready
        self.is_active = is_active
        self.last_action = last_action
        self.updated_at = updated_at or datetime.now(timezone.utc)
        self.sync_version = sync_version
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary for MongoDB storage"""
        state_dict = {
            'state_id': self.state_id,
            'room_id': self.room_id,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'game_state': self.game_state,
            'score': self.score,
            'position': self.position,
            'is_ready': self.is_ready,
            'is_active': self.is_active,
            'last_action': self.last_action,
            'updated_at': self.updated_at,
            'sync_version': self.sync_version,
            'metadata': self.metadata
        }
        return serialize_model_dates(state_dict)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'PlayerState':
        """Create PlayerState from dictionary"""
        return PlayerState(
            state_id=data['state_id'],
            room_id=data['room_id'],
            user_id=data['user_id'],
            session_id=data['session_id'],
            game_state=data.get('game_state', {}),
            score=data.get('score', 0),
            position=data.get('position'),
            is_ready=data.get('is_ready', False),
            is_active=data.get('is_active', True),
            last_action=data.get('last_action'),
            updated_at=data.get('updated_at'),
            sync_version=data.get('sync_version', 0),
            metadata=data.get('metadata', {})
        )

    def update_state(self, game_state: Dict[str, Any]) -> None:
        """Update game state and increment sync version"""
        self.game_state = game_state
        self.last_action = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
        self.sync_version += 1

    def update_score(self, score: int) -> None:
        """Update player score"""
        self.score = score
        self.updated_at = datetime.now(timezone.utc)
        self.sync_version += 1

    def update_position(self, position: Dict[str, float]) -> None:
        """Update player position"""
        self.position = position
        self.last_action = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
        self.sync_version += 1

    def set_ready(self, is_ready: bool) -> None:
        """Set player ready status"""
        self.is_ready = is_ready
        self.updated_at = datetime.now(timezone.utc)

    def set_active(self, is_active: bool) -> None:
        """Set player active status"""
        self.is_active = is_active
        self.updated_at = datetime.now(timezone.utc)
