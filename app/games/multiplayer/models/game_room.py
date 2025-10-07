from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from app.core.utils.json_encoder import serialize_model_dates
from app.core.utils.helpers import extract_user_id, extract_user_ids
import random
import string


class GameRoom:
    """
    Model for multiplayer game rooms.

    Attributes:
        room_id: Unique room identifier
        room_code: Human-readable 6-character room code
        game_id: ID of the game being played
        host_user_id: ID of the room host/creator
        player_ids: List of player user IDs in the room
        max_players: Maximum number of players allowed
        status: Room status (waiting, playing, finished)
        created_at: Room creation timestamp
        started_at: Game start timestamp
        finished_at: Game finish timestamp
        game_config: Game-specific configuration
        metadata: Additional room metadata
    """

    COLLECTION_NAME = 'game_rooms'

    STATUS_WAITING = 'waiting'
    STATUS_PLAYING = 'playing'
    STATUS_FINISHED = 'finished'
    STATUS_ABANDONED = 'abandoned'

    def __init__(
        self,
        room_id: str,
        game_id: str,
        host_user_id: str,
        room_code: Optional[str] = None,
        player_ids: Optional[List[str]] = None,
        max_players: int = 8,
        status: str = STATUS_WAITING,
        created_at: Optional[datetime] = None,
        started_at: Optional[datetime] = None,
        finished_at: Optional[datetime] = None,
        game_config: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.room_id = room_id
        self.room_code = room_code or self._generate_room_code()
        self.game_id = game_id
        self.host_user_id = host_user_id
        self.player_ids = player_ids or [host_user_id]
        self.max_players = max_players
        self.status = status
        self.created_at = created_at or datetime.now(timezone.utc)
        self.started_at = started_at
        self.finished_at = finished_at
        self.game_config = game_config or {}
        self.metadata = metadata or {}

    @staticmethod
    def _generate_room_code(length: int = 6) -> str:
        """Generate a random room code"""
        chars = string.ascii_uppercase + string.digits
        return ''.join(random.choices(chars, k=length))

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary for MongoDB storage"""
        # Ensure host_user_id and player_ids are always strings, not User objects
        host_id = extract_user_id(self.host_user_id)
        player_ids = extract_user_ids(self.player_ids)

        room_dict = {
            'room_id': self.room_id,
            'room_code': self.room_code,
            'game_id': self.game_id,
            'host_user_id': host_id,
            'player_ids': player_ids,
            'max_players': self.max_players,
            'status': self.status,
            'created_at': self.created_at,
            'started_at': self.started_at,
            'finished_at': self.finished_at,
            'game_config': self.game_config,
            'metadata': self.metadata
        }
        return serialize_model_dates(room_dict)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'GameRoom':
        """Create GameRoom from dictionary"""
        return GameRoom(
            room_id=data['room_id'],
            game_id=data['game_id'],
            host_user_id=data['host_user_id'],
            room_code=data.get('room_code'),
            player_ids=data.get('player_ids', []),
            max_players=data.get('max_players', 8),
            status=data.get('status', GameRoom.STATUS_WAITING),
            created_at=data.get('created_at'),
            started_at=data.get('started_at'),
            finished_at=data.get('finished_at'),
            game_config=data.get('game_config', {}),
            metadata=data.get('metadata', {})
        )

    def is_host(self, user_id: str) -> bool:
        """
        Check if user is the host of this room.

        Safely handles both string IDs and User objects.

        Args:
            user_id: User ID to check

        Returns:
            True if user is the host
        """
        host_id = extract_user_id(self.host_user_id)
        return host_id == user_id

    def has_player(self, user_id: str) -> bool:
        """
        Check if user is in the player list.

        Safely handles both string IDs and User objects in player_ids.

        Args:
            user_id: User ID to check

        Returns:
            True if user is in player list
        """
        player_ids_str = extract_user_ids(self.player_ids)
        return user_id in player_ids_str

    def is_full(self) -> bool:
        """Check if room is full"""
        return len(self.player_ids) >= self.max_players

    def can_join(self, user_id: str) -> bool:
        """Check if user can join the room"""
        return (
            not self.is_full() and
            self.status == self.STATUS_WAITING and
            not self.has_player(user_id)
        )

    def add_player(self, user_id: str) -> bool:
        """Add player to room"""
        if self.can_join(user_id):
            self.player_ids.append(user_id)
            return True
        return False

    def remove_player(self, user_id: str) -> bool:
        """Remove player from room"""
        if not self.has_player(user_id):
            return False

        # Extract clean ID to remove
        player_ids_str = extract_user_ids(self.player_ids)
        if user_id in player_ids_str:
            # Find and remove the player (handle both string and object)
            for i, pid in enumerate(self.player_ids):
                if extract_user_id(pid) == user_id:
                    self.player_ids.pop(i)
                    break

        # If host leaves, assign new host or mark as abandoned
        if self.is_host(user_id):
            if self.player_ids:
                # Set first remaining player as new host
                self.host_user_id = extract_user_id(self.player_ids[0])
            else:
                self.status = self.STATUS_ABANDONED

        return True

    def start_game(self) -> bool:
        """Start the game"""
        if self.status == self.STATUS_WAITING and len(self.player_ids) > 1:
            self.status = self.STATUS_PLAYING
            self.started_at = datetime.now(timezone.utc)
            return True
        return False

    def finish_game(self) -> bool:
        """Finish the game"""
        if self.status == self.STATUS_PLAYING:
            self.status = self.STATUS_FINISHED
            self.finished_at = datetime.now(timezone.utc)
            return True
        return False

    def get_player_count(self) -> int:
        """Get current number of players"""
        return len(self.player_ids)
