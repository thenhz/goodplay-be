from typing import Tuple, Optional, Dict, Any, List
from flask import current_app
from datetime import datetime, timedelta

from ..repositories.game_session_repository import GameSessionRepository
from ..repositories.game_repository import GameRepository
from ..models.game_session import GameSession
from ..core.plugin_registry import plugin_registry

class GameSessionService:
    """Service for game session management operations"""

    def __init__(self):
        self.session_repository = GameSessionRepository()
        self.game_repository = GameRepository()

    def start_game_session(self, user_id: str, game_id: str,
                          session_config: Dict[str, Any] = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Start a new game session.

        Args:
            user_id: The user ID
            game_id: The game ID
            session_config: Optional session configuration

        Returns:
            Tuple[bool, str, Optional[Dict[str, Any]]]: (success, message, data)
        """
        try:
            # Validate game exists and is active
            game = self.game_repository.get_game_by_id(game_id)
            if not game:
                return False, "GAME_NOT_FOUND", None

            if not game.is_active:
                return False, "GAME_NOT_ACTIVE", None

            # Check if user has active session for this game
            existing_session = self.session_repository.get_active_user_session(user_id, game_id)
            if existing_session:
                return False, "ACTIVE_SESSION_EXISTS", {
                    "existing_session": existing_session.to_api_dict()
                }

            # Get plugin and start session
            plugin = plugin_registry.get_plugin(game.plugin_id) if game.plugin_id else None
            if not plugin:
                return False, "GAME_PLUGIN_NOT_FOUND", None

            # Create session using plugin
            try:
                plugin_session = plugin.start_session(user_id, session_config or {})

                # Create our session record
                session = GameSession(
                    user_id=user_id,
                    game_id=game_id,
                    session_id=plugin_session.session_id,
                    status="active",
                    current_state=plugin_session.current_state,
                    session_config=session_config or {}
                )

            except Exception as e:
                current_app.logger.error(f"Plugin failed to start session: {str(e)}")
                return False, "PLUGIN_SESSION_START_FAILED", None

            # Save session to database
            session_doc_id = self.session_repository.create_session(session)
            if not session_doc_id:
                return False, "SESSION_CREATION_FAILED", None

            session._id = session_doc_id

            result = {
                "session": session.to_api_dict(),
                "game": game.to_api_dict()
            }

            current_app.logger.info(f"Started session {session.session_id} for user {user_id}")
            return True, "GAME_SESSION_STARTED_SUCCESS", result

        except Exception as e:
            current_app.logger.error(f"Failed to start game session: {str(e)}")
            return False, "GAME_SESSION_START_FAILED", None

    def end_game_session(self, session_id: str, reason: str = "completed") -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        End a game session.

        Args:
            session_id: The session ID
            reason: Reason for ending (completed, abandoned)

        Returns:
            Tuple[bool, str, Optional[Dict[str, Any]]]: (success, message, data)
        """
        try:
            # Get session
            session = self.session_repository.get_session_by_session_id(session_id)
            if not session:
                return False, "SESSION_NOT_FOUND", None

            if session.is_ended():
                return False, "SESSION_ALREADY_ENDED", None

            # Get game and plugin
            game = self.game_repository.get_game_by_id(session.game_id)
            if not game:
                return False, "GAME_NOT_FOUND", None

            plugin = plugin_registry.get_plugin(game.plugin_id) if game.plugin_id else None

            # End session using plugin
            session_result = None
            if plugin:
                try:
                    session_result = plugin.end_session(session_id, reason)
                except Exception as e:
                    current_app.logger.warning(f"Plugin failed to end session: {str(e)}")

            # Calculate credits earned
            credits_earned = session.calculate_credits_earned(game.credit_rate)

            # Update session in database
            if reason == "completed":
                final_score = session_result.final_score if session_result else session.score
                achievements = session_result.achievements_unlocked if session_result else []

                success = self.session_repository.complete_session(
                    session_id, final_score, credits_earned, achievements
                )
            else:
                success = self.session_repository.abandon_session(session_id)

            if not success:
                return False, "SESSION_END_UPDATE_FAILED", None

            # Get updated session
            updated_session = self.session_repository.get_session_by_session_id(session_id)

            result = {
                "session": updated_session.to_api_dict() if updated_session else session.to_api_dict(),
                "session_result": session_result.__dict__ if session_result else None
            }

            current_app.logger.info(f"Ended session {session_id} with reason: {reason}")
            return True, "GAME_SESSION_ENDED_SUCCESS", result

        except Exception as e:
            current_app.logger.error(f"Failed to end game session {session_id}: {str(e)}")
            return False, "GAME_SESSION_END_FAILED", None

    def get_session_by_id(self, session_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Get a game session by ID.

        Args:
            session_id: The session ID

        Returns:
            Tuple[bool, str, Optional[Dict[str, Any]]]: (success, message, data)
        """
        try:
            session = self.session_repository.get_session_by_session_id(session_id)
            if not session:
                return False, "SESSION_NOT_FOUND", None

            # Get game info
            game = self.game_repository.get_game_by_id(session.game_id)

            result = {
                "session": session.to_api_dict(),
                "game": game.to_api_dict() if game else None
            }

            current_app.logger.info(f"Retrieved session {session_id}")
            return True, "SESSION_RETRIEVED_SUCCESS", result

        except Exception as e:
            current_app.logger.error(f"Failed to get session {session_id}: {str(e)}")
            return False, "SESSION_RETRIEVAL_FAILED", None

    def get_user_sessions(self, user_id: str, status: str = None,
                         page: int = 1, limit: int = 20) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Get sessions for a user.

        Args:
            user_id: The user ID
            status: Optional status filter
            page: Page number
            limit: Number of sessions per page

        Returns:
            Tuple[bool, str, Optional[Dict[str, Any]]]: (success, message, data)
        """
        try:
            skip = (page - 1) * limit
            sessions = self.session_repository.get_user_sessions(user_id, status, limit, skip)

            # Get total count
            filter_dict = {"user_id": user_id}
            if status:
                filter_dict["status"] = status
            total_count = self.session_repository.count(filter_dict)

            total_pages = (total_count + limit - 1) // limit

            # Enrich with game data
            sessions_data = []
            for session in sessions:
                game = self.game_repository.get_game_by_id(session.game_id)
                session_data = session.to_api_dict()
                session_data["game"] = game.to_api_dict() if game else None
                sessions_data.append(session_data)

            result = {
                "sessions": sessions_data,
                "pagination": {
                    "page": page,
                    "per_page": limit,
                    "total_items": total_count,
                    "total_pages": total_pages,
                    "has_next": page < total_pages,
                    "has_prev": page > 1
                }
            }

            current_app.logger.info(f"Retrieved {len(sessions)} sessions for user {user_id}")
            return True, "USER_SESSIONS_RETRIEVED_SUCCESS", result

        except Exception as e:
            current_app.logger.error(f"Failed to get user sessions: {str(e)}")
            return False, "USER_SESSIONS_RETRIEVAL_FAILED", None

    def update_session_state(self, session_id: str, new_state: Dict[str, Any]) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Update the state of a game session.

        Args:
            session_id: The session ID
            new_state: The new state data

        Returns:
            Tuple[bool, str, Optional[Dict[str, Any]]]: (success, message, data)
        """
        try:
            # Get session
            session = self.session_repository.get_session_by_session_id(session_id)
            if not session:
                return False, "SESSION_NOT_FOUND", None

            if not session.is_active():
                return False, "SESSION_NOT_ACTIVE", None

            # Get plugin and validate state update
            game = self.game_repository.get_game_by_id(session.game_id)
            if not game:
                return False, "GAME_NOT_FOUND", None

            plugin = plugin_registry.get_plugin(game.plugin_id) if game.plugin_id else None
            if plugin:
                try:
                    # Let plugin update its internal state
                    if not plugin.update_session_state(session_id, new_state):
                        return False, "PLUGIN_STATE_UPDATE_REJECTED", None
                except Exception as e:
                    current_app.logger.warning(f"Plugin state update failed: {str(e)}")

            # Update in database
            if not self.session_repository.update_session_state(session_id, new_state):
                return False, "SESSION_STATE_UPDATE_FAILED", None

            # Get updated session
            updated_session = self.session_repository.get_session_by_session_id(session_id)

            result = {
                "session": updated_session.to_api_dict() if updated_session else None
            }

            current_app.logger.info(f"Updated state for session {session_id}")
            return True, "SESSION_STATE_UPDATED_SUCCESS", result

        except Exception as e:
            current_app.logger.error(f"Failed to update session state {session_id}: {str(e)}")
            return False, "SESSION_STATE_UPDATE_FAILED", None

    def validate_move(self, session_id: str, move: Dict[str, Any]) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Validate and process a move in a game session.

        Args:
            session_id: The session ID
            move: The move data

        Returns:
            Tuple[bool, str, Optional[Dict[str, Any]]]: (success, message, data)
        """
        try:
            # Get session
            session = self.session_repository.get_session_by_session_id(session_id)
            if not session:
                return False, "SESSION_NOT_FOUND", None

            if not session.is_active():
                return False, "SESSION_NOT_ACTIVE", None

            # Get plugin and validate move
            game = self.game_repository.get_game_by_id(session.game_id)
            if not game:
                return False, "GAME_NOT_FOUND", None

            plugin = plugin_registry.get_plugin(game.plugin_id) if game.plugin_id else None
            if not plugin:
                return False, "GAME_PLUGIN_NOT_FOUND", None

            # Validate move using plugin
            try:
                is_valid = plugin.validate_move(session_id, move)
                if not is_valid:
                    return False, "INVALID_MOVE", None
            except Exception as e:
                current_app.logger.error(f"Plugin move validation failed: {str(e)}")
                return False, "MOVE_VALIDATION_FAILED", None

            # Add move to session
            if not self.session_repository.add_session_move(session_id, move):
                return False, "MOVE_RECORDING_FAILED", None

            result = {
                "session_id": session_id,
                "move_valid": True,
                "move_number": len(session.moves) + 1
            }

            current_app.logger.info(f"Validated move for session {session_id}")
            return True, "MOVE_VALIDATED_SUCCESS", result

        except Exception as e:
            current_app.logger.error(f"Failed to validate move for session {session_id}: {str(e)}")
            return False, "MOVE_VALIDATION_FAILED", None

    def pause_session(self, session_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Pause a game session.

        Args:
            session_id: The session ID

        Returns:
            Tuple[bool, str, Optional[Dict[str, Any]]]: (success, message, data)
        """
        try:
            session = self.session_repository.get_session_by_session_id(session_id)
            if not session:
                return False, "SESSION_NOT_FOUND", None

            if session.status != "active":
                return False, "SESSION_NOT_ACTIVE", None

            if not self.session_repository.pause_session(session_id):
                return False, "SESSION_PAUSE_FAILED", None

            current_app.logger.info(f"Paused session {session_id}")
            return True, "SESSION_PAUSED_SUCCESS", None

        except Exception as e:
            current_app.logger.error(f"Failed to pause session {session_id}: {str(e)}")
            return False, "SESSION_PAUSE_FAILED", None

    def resume_session(self, session_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Resume a paused game session.

        Args:
            session_id: The session ID

        Returns:
            Tuple[bool, str, Optional[Dict[str, Any]]]: (success, message, data)
        """
        try:
            session = self.session_repository.get_session_by_session_id(session_id)
            if not session:
                return False, "SESSION_NOT_FOUND", None

            if session.status != "paused":
                return False, "SESSION_NOT_PAUSED", None

            if not self.session_repository.resume_session(session_id):
                return False, "SESSION_RESUME_FAILED", None

            current_app.logger.info(f"Resumed session {session_id}")
            return True, "SESSION_RESUMED_SUCCESS", None

        except Exception as e:
            current_app.logger.error(f"Failed to resume session {session_id}: {str(e)}")
            return False, "SESSION_RESUME_FAILED", None

    def get_user_session_stats(self, user_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Get session statistics for a user.

        Args:
            user_id: The user ID

        Returns:
            Tuple[bool, str, Optional[Dict[str, Any]]]: (success, message, data)
        """
        try:
            stats = self.session_repository.get_user_session_stats(user_id)

            current_app.logger.info(f"Retrieved session stats for user {user_id}")
            return True, "USER_SESSION_STATS_RETRIEVED_SUCCESS", stats

        except Exception as e:
            current_app.logger.error(f"Failed to get user session stats: {str(e)}")
            return False, "USER_SESSION_STATS_RETRIEVAL_FAILED", None