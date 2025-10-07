from typing import Optional, Dict, List, Any, Tuple
from flask import current_app
from datetime import datetime, timezone
import uuid
from app.games.multiplayer.models.game_room import GameRoom
from app.games.multiplayer.repositories.room_repository import RoomRepository
from app.core.utils.helpers import extract_user_id


class RoomManager:
    """
    Service for managing multiplayer game rooms.

    Handles:
    - Room creation and deletion
    - Player join/leave operations
    - Room lifecycle (waiting -> playing -> finished)
    - Room discovery and filtering
    """

    def __init__(self):
        self.room_repository = RoomRepository()

    def create_room(
        self,
        game_id: str,
        host_user_id: str,
        max_players: int = 8,
        game_config: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, str, Optional[GameRoom]]:
        """
        Create a new game room.

        Args:
            game_id: ID of the game
            host_user_id: ID of the room host
            max_players: Maximum number of players (default: 8)
            game_config: Optional game configuration

        Returns:
            Tuple of (success, message, room)
        """
        try:
            room_id = str(uuid.uuid4())

            room = GameRoom(
                room_id=room_id,
                game_id=game_id,
                host_user_id=host_user_id,
                max_players=max_players,
                game_config=game_config or {},
                status=GameRoom.STATUS_WAITING
            )

            success = self.room_repository.create_room(room)

            if success:
                current_app.logger.info(
                    f"Created room {room_id} for game {game_id} (host: {host_user_id})"
                )
                return True, "ROOM_CREATED_SUCCESS", room
            else:
                return False, "ROOM_CREATION_FAILED", None

        except Exception as e:
            current_app.logger.error(f"Error creating room: {str(e)}", exc_info=True)
            return False, "ROOM_CREATION_ERROR", None

    def get_room(self, room_id: str) -> Optional[GameRoom]:
        """
        Get room by ID.

        Args:
            room_id: Room ID

        Returns:
            GameRoom or None
        """
        try:
            return self.room_repository.find_by_room_id(room_id)
        except Exception as e:
            current_app.logger.error(f"Error getting room {room_id}: {str(e)}")
            return None

    def get_room_by_code(self, room_code: str) -> Optional[GameRoom]:
        """
        Get room by code.

        Args:
            room_code: Room code (6-character)

        Returns:
            GameRoom or None
        """
        try:
            return self.room_repository.find_by_room_code(room_code)
        except Exception as e:
            current_app.logger.error(f"Error getting room by code {room_code}: {str(e)}")
            return None

    def join_room(
        self,
        room_id: str,
        user_id: str
    ) -> Tuple[bool, str, Optional[GameRoom]]:
        """
        Add player to room.

        Args:
            room_id: Room ID
            user_id: User ID (string) or User object

        Returns:
            Tuple of (success, message, room)
        """
        try:
            # Extract user ID if User object passed
            user_id = extract_user_id(user_id)

            room = self.room_repository.find_by_room_id(room_id)

            if not room:
                return False, "ROOM_NOT_FOUND", None

            if not room.can_join(user_id):
                if room.is_full():
                    return False, "ROOM_FULL", room
                if room.status != GameRoom.STATUS_WAITING:
                    return False, "ROOM_NOT_ACCEPTING_PLAYERS", room
                if room.has_player(user_id):
                    return False, "ALREADY_IN_ROOM", room

            # Add player
            room.add_player(user_id)

            # Update in database
            self.room_repository.update_room(room_id, room.to_dict())

            current_app.logger.info(f"User {user_id} joined room {room_id}")

            return True, "PLAYER_JOINED_SUCCESS", room

        except Exception as e:
            current_app.logger.error(f"Error joining room: {str(e)}", exc_info=True)
            return False, "JOIN_ROOM_ERROR", None

    def leave_room(
        self,
        room_id: str,
        user_id: str
    ) -> Tuple[bool, str, Optional[GameRoom]]:
        """
        Remove player from room.

        Args:
            room_id: Room ID
            user_id: User ID (string) or User object

        Returns:
            Tuple of (success, message, room)
        """
        try:
            # Extract user ID if User object passed
            user_id = extract_user_id(user_id)

            room = self.room_repository.find_by_room_id(room_id)

            if not room:
                return False, "ROOM_NOT_FOUND", None

            if not room.has_player(user_id):
                return False, "NOT_IN_ROOM", room

            # Remove player
            room.remove_player(user_id)

            # Update in database
            self.room_repository.update_room(room_id, room.to_dict())

            current_app.logger.info(f"User {user_id} left room {room_id}")

            return True, "PLAYER_LEFT_SUCCESS", room

        except Exception as e:
            current_app.logger.error(f"Error leaving room: {str(e)}", exc_info=True)
            return False, "LEAVE_ROOM_ERROR", None

    def start_game(
        self,
        room_id: str,
        user_id: str
    ) -> Tuple[bool, str, Optional[GameRoom]]:
        """
        Start the game (host only).

        Args:
            room_id: Room ID
            user_id: User ID (string) or User object (must be host)

        Returns:
            Tuple of (success, message, room)
        """
        try:
            # Extract user ID if User object passed
            user_id = extract_user_id(user_id)

            room = self.room_repository.find_by_room_id(room_id)

            if not room:
                return False, "ROOM_NOT_FOUND", None

            if not room.is_host(user_id):
                return False, "NOT_ROOM_HOST", room

            if not room.start_game():
                if room.status != GameRoom.STATUS_WAITING:
                    return False, "GAME_ALREADY_STARTED", room
                if len(room.player_ids) < 2:
                    return False, "NOT_ENOUGH_PLAYERS", room

            # Update in database
            self.room_repository.update_status(room_id, GameRoom.STATUS_PLAYING)

            current_app.logger.info(f"Game started in room {room_id}")

            return True, "GAME_STARTED_SUCCESS", room

        except Exception as e:
            current_app.logger.error(f"Error starting game: {str(e)}", exc_info=True)
            return False, "START_GAME_ERROR", None

    def finish_game(self, room_id: str) -> Tuple[bool, str]:
        """
        Finish the game.

        Args:
            room_id: Room ID

        Returns:
            Tuple of (success, message)
        """
        try:
            room = self.room_repository.find_by_room_id(room_id)

            if not room:
                return False, "ROOM_NOT_FOUND"

            if not room.finish_game():
                return False, "GAME_NOT_PLAYING"

            # Update in database
            self.room_repository.update_status(room_id, GameRoom.STATUS_FINISHED)

            current_app.logger.info(f"Game finished in room {room_id}")

            return True, "GAME_FINISHED_SUCCESS"

        except Exception as e:
            current_app.logger.error(f"Error finishing game: {str(e)}", exc_info=True)
            return False, "FINISH_GAME_ERROR"

    def get_available_rooms(
        self,
        game_id: Optional[str] = None,
        limit: int = 20
    ) -> List[GameRoom]:
        """
        Get available rooms (waiting and not full).

        Args:
            game_id: Optional filter by game ID
            limit: Maximum number of rooms to return

        Returns:
            List of GameRoom objects
        """
        try:
            return self.room_repository.find_available_rooms(game_id, limit)
        except Exception as e:
            current_app.logger.error(f"Error getting available rooms: {str(e)}")
            return []

    def get_user_rooms(self, user_id: str) -> List[GameRoom]:
        """
        Get rooms where user is a player.

        Args:
            user_id: User ID (string) or User object

        Returns:
            List of GameRoom objects
        """
        try:
            # Extract user ID if User object passed
            user_id = extract_user_id(user_id)
            return self.room_repository.find_by_player(user_id, active_only=True)
        except Exception as e:
            current_app.logger.error(f"Error getting user rooms: {str(e)}")
            return []

    def cleanup_old_rooms(self, hours: int = 24) -> int:
        """
        Clean up old finished or abandoned rooms.

        Args:
            hours: Age threshold in hours

        Returns:
            Number of rooms cleaned up
        """
        try:
            count = self.room_repository.cleanup_old_rooms(hours)

            if count > 0:
                current_app.logger.info(f"Cleaned up {count} old rooms")

            return count

        except Exception as e:
            current_app.logger.error(f"Error cleaning up rooms: {str(e)}")
            return 0

    def get_statistics(self) -> Dict[str, int]:
        """
        Get room statistics.

        Returns:
            Dictionary with room statistics
        """
        try:
            return self.room_repository.get_room_statistics()
        except Exception as e:
            current_app.logger.error(f"Error getting room statistics: {str(e)}")
            return {}

    # New GOO-56 methods

    def set_player_ready(
        self,
        room_id: str,
        user_id: str,
        is_ready: bool
    ) -> Tuple[bool, str, Optional[GameRoom]]:
        """
        Set player ready state.

        Args:
            room_id: Room ID
            user_id: User ID (string) or User object
            is_ready: Ready state

        Returns:
            Tuple of (success, message, room)
        """
        try:
            user_id = extract_user_id(user_id)

            room = self.room_repository.find_by_room_id(room_id)

            if not room:
                return False, "ROOM_NOT_FOUND", None

            if not room.has_player(user_id):
                return False, "NOT_IN_ROOM", None

            if room.status != GameRoom.STATUS_WAITING:
                return False, "GAME_ALREADY_STARTED", None

            # Update ready state
            room.set_player_ready(user_id, is_ready)

            # Save to database
            self.room_repository.update_player_ready_state(room_id, user_id, is_ready)

            # Reload room
            room = self.room_repository.find_by_room_id(room_id)

            current_app.logger.info(
                f"User {user_id} ready state set to {is_ready} in room {room_id}"
            )

            return True, "PLAYER_READY_UPDATED", room

        except Exception as e:
            current_app.logger.error(f"Error setting player ready: {str(e)}", exc_info=True)
            return False, "SET_READY_ERROR", None

    def update_room_settings(
        self,
        room_id: str,
        host_user_id: str,
        settings: Dict[str, Any]
    ) -> Tuple[bool, str, Optional[GameRoom]]:
        """
        Update room settings (host only).

        Args:
            room_id: Room ID
            host_user_id: User ID (must be host)
            settings: Settings to update

        Returns:
            Tuple of (success, message, room)
        """
        try:
            host_user_id = extract_user_id(host_user_id)

            room = self.room_repository.find_by_room_id(room_id)

            if not room:
                return False, "ROOM_NOT_FOUND", None

            if not room.is_host(host_user_id):
                return False, "NOT_ROOM_HOST", None

            if room.status != GameRoom.STATUS_WAITING:
                return False, "CANNOT_UPDATE_STARTED_ROOM", None

            # Update settings
            if self.room_repository.update_room_settings(room_id, settings):
                # Reload room
                room = self.room_repository.find_by_room_id(room_id)

                current_app.logger.info(
                    f"Room {room_id} settings updated by host {host_user_id}"
                )

                return True, "ROOM_SETTINGS_UPDATED", room
            else:
                return False, "SETTINGS_UPDATE_FAILED", None

        except Exception as e:
            current_app.logger.error(f"Error updating room settings: {str(e)}", exc_info=True)
            return False, "UPDATE_SETTINGS_ERROR", None

    def add_spectator(
        self,
        room_id: str,
        user_id: str
    ) -> Tuple[bool, str, Optional[GameRoom]]:
        """
        Add spectator to room.

        Args:
            room_id: Room ID
            user_id: User ID (string) or User object

        Returns:
            Tuple of (success, message, room)
        """
        try:
            user_id = extract_user_id(user_id)

            room = self.room_repository.find_by_room_id(room_id)

            if not room:
                return False, "ROOM_NOT_FOUND", None

            if not room.can_spectate(user_id):
                if not room.allow_spectators:
                    return False, "SPECTATORS_NOT_ALLOWED", None
                if room.get_spectator_count() >= room.max_spectators:
                    return False, "SPECTATOR_LIMIT_REACHED", None
                if room.has_player(user_id):
                    return False, "ALREADY_PLAYER", None
                if room.has_spectator(user_id):
                    return False, "ALREADY_SPECTATOR", None

            # Add spectator
            room.add_spectator(user_id)

            # Update in database
            self.room_repository.add_spectator(room_id, user_id)

            # Reload room
            room = self.room_repository.find_by_room_id(room_id)

            current_app.logger.info(f"User {user_id} joined room {room_id} as spectator")

            return True, "SPECTATOR_JOINED_SUCCESS", room

        except Exception as e:
            current_app.logger.error(f"Error adding spectator: {str(e)}", exc_info=True)
            return False, "ADD_SPECTATOR_ERROR", None

    def remove_spectator(
        self,
        room_id: str,
        user_id: str
    ) -> Tuple[bool, str]:
        """
        Remove spectator from room.

        Args:
            room_id: Room ID
            user_id: User ID (string) or User object

        Returns:
            Tuple of (success, message)
        """
        try:
            user_id = extract_user_id(user_id)

            room = self.room_repository.find_by_room_id(room_id)

            if not room:
                return False, "ROOM_NOT_FOUND"

            if not room.has_spectator(user_id):
                return False, "NOT_SPECTATOR"

            # Remove spectator
            room.remove_spectator(user_id)

            # Update in database
            self.room_repository.remove_spectator(room_id, user_id)

            current_app.logger.info(f"User {user_id} left room {room_id} as spectator")

            return True, "SPECTATOR_LEFT_SUCCESS"

        except Exception as e:
            current_app.logger.error(f"Error removing spectator: {str(e)}", exc_info=True)
            return False, "REMOVE_SPECTATOR_ERROR"

    def check_auto_start(
        self,
        room_id: str
    ) -> Tuple[bool, str]:
        """
        Check if room should auto-start when all players ready.

        Args:
            room_id: Room ID

        Returns:
            Tuple of (should_start, reason)
        """
        try:
            room = self.room_repository.find_by_room_id(room_id)

            if not room:
                return False, "ROOM_NOT_FOUND"

            if room.status != GameRoom.STATUS_WAITING:
                return False, "ROOM_NOT_WAITING"

            if not room.auto_start_when_ready:
                return False, "AUTO_START_DISABLED"

            if not room.all_players_ready():
                return False, "PLAYERS_NOT_READY"

            if len(room.player_ids) < 2:
                return False, "NOT_ENOUGH_PLAYERS"

            return True, "READY_TO_AUTO_START"

        except Exception as e:
            current_app.logger.error(f"Error checking auto-start: {str(e)}", exc_info=True)
            return False, "AUTO_START_CHECK_ERROR"

    def get_ready_status(
        self,
        room_id: str
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Get ready status for room.

        Args:
            room_id: Room ID

        Returns:
            Tuple of (success, message, status_data)
        """
        try:
            room = self.room_repository.find_by_room_id(room_id)

            if not room:
                return False, "ROOM_NOT_FOUND", None

            status_data = {
                'room_id': room_id,
                'total_players': room.get_player_count(),
                'ready_count': room.get_ready_count(),
                'all_ready': room.all_players_ready(),
                'player_ready_states': room.player_ready_states,
                'auto_start_enabled': room.auto_start_when_ready
            }

            return True, "READY_STATUS_RETRIEVED", status_data

        except Exception as e:
            current_app.logger.error(f"Error getting ready status: {str(e)}", exc_info=True)
            return False, "GET_READY_STATUS_ERROR", None
