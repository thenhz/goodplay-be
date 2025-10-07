from typing import Optional, Dict, List, Any, Tuple
from flask import current_app
from datetime import datetime, timezone
import uuid
from app.games.multiplayer.models.player_state import PlayerState
from app.games.multiplayer.repositories.player_state_repository import PlayerStateRepository
from app.core.utils.helpers import extract_user_id


class StateManager:
    """
    Service for managing player state synchronization in multiplayer games.

    Handles:
    - Player state creation and updates
    - State synchronization across devices
    - Ready status management
    - State cleanup
    """

    def __init__(self):
        self.state_repository = PlayerStateRepository()

    def create_player_state(
        self,
        room_id: str,
        user_id: str,
        session_id: str,
        initial_state: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, str, Optional[PlayerState]]:
        """
        Create player state for a room.

        Args:
            room_id: Room ID
            user_id: User ID (string) or User object
            session_id: WebSocket session ID
            initial_state: Optional initial game state

        Returns:
            Tuple of (success, message, state)
        """
        try:
            # Extract user ID if User object passed
            user_id = extract_user_id(user_id)

            state_id = str(uuid.uuid4())

            state = PlayerState(
                state_id=state_id,
                room_id=room_id,
                user_id=user_id,
                session_id=session_id,
                game_state=initial_state or {},
                is_active=True
            )

            success = self.state_repository.create_state(state)

            if success:
                current_app.logger.info(
                    f"Created player state for user {user_id} in room {room_id}"
                )
                return True, "PLAYER_STATE_CREATED", state
            else:
                return False, "STATE_CREATION_FAILED", None

        except Exception as e:
            current_app.logger.error(f"Error creating player state: {str(e)}", exc_info=True)
            return False, "STATE_CREATION_ERROR", None

    def get_player_state(self, room_id: str, user_id: str) -> Optional[PlayerState]:
        """
        Get player state in a room.

        Args:
            room_id: Room ID
            user_id: User ID (string) or User object

        Returns:
            PlayerState or None
        """
        try:
            # Extract user ID if User object passed
            user_id = extract_user_id(user_id)
            return self.state_repository.find_by_room_and_user(room_id, user_id)
        except Exception as e:
            current_app.logger.error(f"Error getting player state: {str(e)}")
            return None

    def get_room_states(self, room_id: str, active_only: bool = True) -> List[PlayerState]:
        """
        Get all player states in a room.

        Args:
            room_id: Room ID
            active_only: Only return active players

        Returns:
            List of PlayerState objects
        """
        try:
            return self.state_repository.find_by_room(room_id, active_only)
        except Exception as e:
            current_app.logger.error(f"Error getting room states: {str(e)}")
            return []

    def update_game_state(
        self,
        room_id: str,
        user_id: str,
        game_state: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Update player's game state.

        Args:
            room_id: Room ID
            user_id: User ID (string) or User object
            game_state: New game state data

        Returns:
            Tuple of (success, message)
        """
        try:
            # Extract user ID if User object passed
            user_id = extract_user_id(user_id)

            success = self.state_repository.update_game_state(
                room_id, user_id, game_state
            )

            if success:
                current_app.logger.debug(
                    f"Updated game state for user {user_id} in room {room_id}"
                )
                return True, "GAME_STATE_UPDATED"
            else:
                return False, "STATE_UPDATE_FAILED"

        except Exception as e:
            current_app.logger.error(f"Error updating game state: {str(e)}", exc_info=True)
            return False, "STATE_UPDATE_ERROR"

    def update_score(
        self,
        room_id: str,
        user_id: str,
        score: int
    ) -> Tuple[bool, str]:
        """
        Update player's score.

        Args:
            room_id: Room ID
            user_id: User ID (string) or User object
            score: New score

        Returns:
            Tuple of (success, message)
        """
        try:
            # Extract user ID if User object passed
            user_id = extract_user_id(user_id)

            success = self.state_repository.update_score(room_id, user_id, score)

            if success:
                current_app.logger.debug(
                    f"Updated score for user {user_id} in room {room_id}: {score}"
                )
                return True, "SCORE_UPDATED"
            else:
                return False, "SCORE_UPDATE_FAILED"

        except Exception as e:
            current_app.logger.error(f"Error updating score: {str(e)}", exc_info=True)
            return False, "SCORE_UPDATE_ERROR"

    def update_position(
        self,
        room_id: str,
        user_id: str,
        position: Dict[str, float]
    ) -> Tuple[bool, str]:
        """
        Update player's position.

        Args:
            room_id: Room ID
            user_id: User ID (string) or User object
            position: Position data (e.g., {"x": 10.5, "y": 20.3})

        Returns:
            Tuple of (success, message)
        """
        try:
            # Extract user ID if User object passed
            user_id = extract_user_id(user_id)

            success = self.state_repository.update_position(room_id, user_id, position)

            if success:
                current_app.logger.debug(
                    f"Updated position for user {user_id} in room {room_id}"
                )
                return True, "POSITION_UPDATED"
            else:
                return False, "POSITION_UPDATE_FAILED"

        except Exception as e:
            current_app.logger.error(f"Error updating position: {str(e)}", exc_info=True)
            return False, "POSITION_UPDATE_ERROR"

    def set_ready(
        self,
        room_id: str,
        user_id: str,
        is_ready: bool = True
    ) -> Tuple[bool, str]:
        """
        Set player ready status.

        Args:
            room_id: Room ID
            user_id: User ID (string) or User object
            is_ready: Ready status

        Returns:
            Tuple of (success, message)
        """
        try:
            # Extract user ID if User object passed
            user_id = extract_user_id(user_id)

            success = self.state_repository.set_ready(room_id, user_id, is_ready)

            if success:
                status = "ready" if is_ready else "not ready"
                current_app.logger.info(
                    f"User {user_id} marked as {status} in room {room_id}"
                )
                return True, "READY_STATUS_UPDATED"
            else:
                return False, "READY_UPDATE_FAILED"

        except Exception as e:
            current_app.logger.error(f"Error setting ready status: {str(e)}", exc_info=True)
            return False, "READY_UPDATE_ERROR"

    def set_active(
        self,
        room_id: str,
        user_id: str,
        is_active: bool = True
    ) -> Tuple[bool, str]:
        """
        Set player active status.

        Args:
            room_id: Room ID
            user_id: User ID (string) or User object
            is_active: Active status

        Returns:
            Tuple of (success, message)
        """
        try:
            # Extract user ID if User object passed
            user_id = extract_user_id(user_id)

            success = self.state_repository.set_active(room_id, user_id, is_active)

            if success:
                status = "active" if is_active else "inactive"
                current_app.logger.info(
                    f"User {user_id} marked as {status} in room {room_id}"
                )
                return True, "ACTIVE_STATUS_UPDATED"
            else:
                return False, "ACTIVE_UPDATE_FAILED"

        except Exception as e:
            current_app.logger.error(f"Error setting active status: {str(e)}", exc_info=True)
            return False, "ACTIVE_UPDATE_ERROR"

    def get_ready_count(self, room_id: str) -> int:
        """
        Get count of ready players in room.

        Args:
            room_id: Room ID

        Returns:
            Number of ready players
        """
        try:
            return self.state_repository.get_ready_count(room_id)
        except Exception as e:
            current_app.logger.error(f"Error getting ready count: {str(e)}")
            return 0

    def are_all_ready(self, room_id: str) -> bool:
        """
        Check if all active players are ready.

        Args:
            room_id: Room ID

        Returns:
            True if all active players are ready
        """
        try:
            active_count = self.state_repository.get_active_count(room_id)
            ready_count = self.state_repository.get_ready_count(room_id)

            return active_count > 0 and active_count == ready_count

        except Exception as e:
            current_app.logger.error(f"Error checking ready status: {str(e)}")
            return False

    def cleanup_room_states(self, room_id: str) -> int:
        """
        Clean up all player states in a room.

        Args:
            room_id: Room ID

        Returns:
            Number of states deleted
        """
        try:
            count = self.state_repository.delete_by_room(room_id)

            if count > 0:
                current_app.logger.info(
                    f"Cleaned up {count} player states from room {room_id}"
                )

            return count

        except Exception as e:
            current_app.logger.error(f"Error cleaning up room states: {str(e)}")
            return 0

    def cleanup_inactive_states(self, hours: int = 24) -> int:
        """
        Clean up inactive player states.

        Args:
            hours: Age threshold in hours

        Returns:
            Number of states deleted
        """
        try:
            count = self.state_repository.cleanup_inactive_states(hours)

            if count > 0:
                current_app.logger.info(
                    f"Cleaned up {count} inactive player states"
                )

            return count

        except Exception as e:
            current_app.logger.error(f"Error cleaning up inactive states: {str(e)}")
            return 0

    def get_room_statistics(self, room_id: str) -> Dict[str, int]:
        """
        Get statistics for a room.

        Args:
            room_id: Room ID

        Returns:
            Dictionary with room statistics
        """
        try:
            active_count = self.state_repository.get_active_count(room_id)
            ready_count = self.state_repository.get_ready_count(room_id)

            return {
                'active_players': active_count,
                'ready_players': ready_count,
                'all_ready': active_count > 0 and active_count == ready_count
            }

        except Exception as e:
            current_app.logger.error(f"Error getting room statistics: {str(e)}")
            return {'active_players': 0, 'ready_players': 0, 'all_ready': False}
