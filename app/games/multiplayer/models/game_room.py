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
        privacy: Room privacy setting (public, private, friends_only)
        password: Hashed password for private rooms
        room_name: Custom room name
        description: Room description
        tags: Searchable tags for room discovery
        player_ready_states: Dictionary of player ready states {user_id: is_ready}
        spectator_ids: List of spectator user IDs
        allow_spectators: Whether spectators are allowed
        max_spectators: Maximum number of spectators
        auto_start_when_ready: Auto-start when all players ready
        auto_start_timer: Delay before auto-start (seconds)
    """

    COLLECTION_NAME = 'game_rooms'

    STATUS_WAITING = 'waiting'
    STATUS_PLAYING = 'playing'
    STATUS_FINISHED = 'finished'
    STATUS_ABANDONED = 'abandoned'

    PRIVACY_PUBLIC = 'public'
    PRIVACY_PRIVATE = 'private'
    PRIVACY_FRIENDS_ONLY = 'friends_only'

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
        metadata: Optional[Dict[str, Any]] = None,
        # New GOO-56 fields
        privacy: str = PRIVACY_PUBLIC,
        password: Optional[str] = None,
        room_name: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        player_ready_states: Optional[Dict[str, bool]] = None,
        spectator_ids: Optional[List[str]] = None,
        allow_spectators: bool = False,
        max_spectators: int = 10,
        auto_start_when_ready: bool = False,
        auto_start_timer: Optional[int] = None
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
        # New GOO-56 fields
        self.privacy = privacy
        self.password = password
        self.room_name = room_name
        self.description = description
        self.tags = tags or []
        self.player_ready_states = player_ready_states or {}
        self.spectator_ids = spectator_ids or []
        self.allow_spectators = allow_spectators
        self.max_spectators = max_spectators
        self.auto_start_when_ready = auto_start_when_ready
        self.auto_start_timer = auto_start_timer

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
        spectator_ids = extract_user_ids(self.spectator_ids)

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
            'metadata': self.metadata,
            # New GOO-56 fields
            'privacy': self.privacy,
            'password': self.password,
            'room_name': self.room_name,
            'description': self.description,
            'tags': self.tags,
            'player_ready_states': self.player_ready_states,
            'spectator_ids': spectator_ids,
            'allow_spectators': self.allow_spectators,
            'max_spectators': self.max_spectators,
            'auto_start_when_ready': self.auto_start_when_ready,
            'auto_start_timer': self.auto_start_timer
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
            metadata=data.get('metadata', {}),
            # New GOO-56 fields
            privacy=data.get('privacy', GameRoom.PRIVACY_PUBLIC),
            password=data.get('password'),
            room_name=data.get('room_name'),
            description=data.get('description'),
            tags=data.get('tags', []),
            player_ready_states=data.get('player_ready_states', {}),
            spectator_ids=data.get('spectator_ids', []),
            allow_spectators=data.get('allow_spectators', False),
            max_spectators=data.get('max_spectators', 10),
            auto_start_when_ready=data.get('auto_start_when_ready', False),
            auto_start_timer=data.get('auto_start_timer')
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

    # New GOO-56 methods

    def set_player_ready(self, user_id: str, is_ready: bool) -> bool:
        """
        Set player ready state.

        Args:
            user_id: User ID
            is_ready: Ready state

        Returns:
            True if successfully set, False if player not in room
        """
        if not self.has_player(user_id):
            return False

        self.player_ready_states[user_id] = is_ready
        return True

    def all_players_ready(self) -> bool:
        """
        Check if all players are ready.

        Returns:
            True if all players have ready state = True
        """
        if not self.player_ids:
            return False

        for player_id in self.player_ids:
            if not self.player_ready_states.get(player_id, False):
                return False

        return True

    def get_ready_count(self) -> int:
        """
        Get count of ready players.

        Returns:
            Number of players marked as ready
        """
        return sum(1 for ready in self.player_ready_states.values() if ready)

    def add_spectator(self, user_id: str) -> bool:
        """
        Add spectator to room.

        Args:
            user_id: User ID

        Returns:
            True if successfully added, False otherwise
        """
        if not self.can_spectate(user_id):
            return False

        self.spectator_ids.append(user_id)
        return True

    def remove_spectator(self, user_id: str) -> bool:
        """
        Remove spectator from room.

        Args:
            user_id: User ID

        Returns:
            True if successfully removed, False if not a spectator
        """
        if user_id not in self.spectator_ids:
            return False

        self.spectator_ids.remove(user_id)
        return True

    def can_spectate(self, user_id: str) -> bool:
        """
        Check if user can join as spectator.

        Args:
            user_id: User ID

        Returns:
            True if user can spectate
        """
        return (
            self.allow_spectators and
            len(self.spectator_ids) < self.max_spectators and
            not self.has_player(user_id) and
            user_id not in self.spectator_ids
        )

    def is_private(self) -> bool:
        """
        Check if room is private.

        Returns:
            True if room privacy is private
        """
        return self.privacy == self.PRIVACY_PRIVATE

    def validate_password(self, password: str) -> bool:
        """
        Validate password for private room.

        Args:
            password: Password to validate

        Returns:
            True if password matches (plain text comparison for now)
        """
        if not self.is_private() or not self.password:
            return True

        # TODO: Implement proper password hashing with bcrypt
        return self.password == password

    def has_spectator(self, user_id: str) -> bool:
        """
        Check if user is a spectator.

        Args:
            user_id: User ID

        Returns:
            True if user is spectator
        """
        return user_id in self.spectator_ids

    def get_spectator_count(self) -> int:
        """
        Get current number of spectators.

        Returns:
            Count of spectators
        """
        return len(self.spectator_ids)
