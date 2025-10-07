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
