from typing import Optional, Dict, List, Any
from flask import current_app
from datetime import datetime, timezone
from app.games.multiplayer.models.multiplayer_session import MultiplayerSession
from app.games.multiplayer.repositories.multiplayer_session_repository import MultiplayerSessionRepository


class ConnectionManager:
    """
    Service for managing WebSocket connections and multiplayer sessions.

    Handles:
    - Session creation and destruction
    - Connection tracking
    - Latency monitoring
    - Session cleanup
    """

    _instance = None
    _socketio = None

    def __init__(self):
        self.session_repository = MultiplayerSessionRepository()

    @classmethod
    def initialize(cls, socketio):
        """Initialize the connection manager with SocketIO instance"""
        cls._socketio = socketio
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def get_instance(cls):
        """Get the singleton instance"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def create_session(
        self,
        session_id: str,
        user_id: str,
        device_info: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Create a new multiplayer session (idempotent).

        Args:
            session_id: WebSocket session ID
            user_id: Authenticated user ID
            device_info: Optional device information

        Returns:
            True if session created successfully
        """
        try:
            # Check if session already exists (idempotent)
            existing = self.session_repository.find_by_session_id(session_id)
            if existing:
                current_app.logger.debug(
                    f"Session {session_id} already exists for user {user_id}, skipping creation (idempotent)"
                )
                return True  # Idempotent: treat as success

            # Create new session
            session = MultiplayerSession(
                session_id=session_id,
                user_id=user_id,
                device_info=device_info or {},
                connected_at=datetime.now(timezone.utc),
                status=MultiplayerSession.STATUS_ACTIVE
            )

            success = self.session_repository.create_session(session)

            if success:
                current_app.logger.info(
                    f"✅ Created multiplayer session: user={user_id}, sid={session_id}"
                )
            else:
                current_app.logger.error(
                    f"❌ Failed to create session: user={user_id}, sid={session_id}"
                )

            return success

        except Exception as e:
            current_app.logger.error(
                f"❌ Error creating session: {str(e)}",
                exc_info=True
            )
            return False

    def get_session(self, session_id: str) -> Optional[MultiplayerSession]:
        """
        Get session by session ID.

        Args:
            session_id: WebSocket session ID

        Returns:
            MultiplayerSession or None
        """
        try:
            return self.session_repository.find_by_session_id(session_id)
        except Exception as e:
            current_app.logger.error(f"Error getting session {session_id}: {str(e)}")
            return None

    def get_user_sessions(self, user_id: str, active_only: bool = True) -> List[MultiplayerSession]:
        """
        Get all sessions for a user.

        Args:
            user_id: User ID
            active_only: Only return active sessions

        Returns:
            List of MultiplayerSession objects
        """
        try:
            return self.session_repository.find_by_user_id(user_id, active_only)
        except Exception as e:
            current_app.logger.error(f"Error getting user sessions for {user_id}: {str(e)}")
            return []

    def update_latency(self, session_id: str, latency_ms: int) -> bool:
        """
        Update session latency from ping/pong.

        Args:
            session_id: WebSocket session ID
            latency_ms: Latency in milliseconds

        Returns:
            True if updated successfully
        """
        try:
            success = self.session_repository.update_ping(session_id, latency_ms)

            if success:
                current_app.logger.debug(
                    f"Updated latency for session {session_id}: {latency_ms}ms"
                )

            return success

        except Exception as e:
            current_app.logger.error(f"Error updating latency: {str(e)}")
            return False

    def join_room(self, session_id: str, room_id: str) -> bool:
        """
        Update session when user joins a room.

        Args:
            session_id: WebSocket session ID
            room_id: Game room ID

        Returns:
            True if updated successfully
        """
        try:
            success = self.session_repository.update_room(session_id, room_id)

            if success:
                current_app.logger.info(
                    f"Session {session_id} joined room {room_id}"
                )

            return success

        except Exception as e:
            current_app.logger.error(f"Error joining room: {str(e)}")
            return False

    def leave_room(self, session_id: str) -> bool:
        """
        Update session when user leaves a room.

        Args:
            session_id: WebSocket session ID

        Returns:
            True if updated successfully
        """
        try:
            success = self.session_repository.update_room(session_id, None)

            if success:
                current_app.logger.info(
                    f"Session {session_id} left room"
                )

            return success

        except Exception as e:
            current_app.logger.error(f"Error leaving room: {str(e)}")
            return False

    def handle_disconnect(self, session_id: str) -> bool:
        """
        Handle session disconnection and cleanup.

        Args:
            session_id: WebSocket session ID

        Returns:
            True if handled successfully
        """
        try:
            # Mark session as disconnected
            success = self.session_repository.mark_disconnected(session_id)

            if success:
                current_app.logger.info(
                    f"Marked session {session_id} as disconnected"
                )

            return success

        except Exception as e:
            current_app.logger.error(f"Error handling disconnect: {str(e)}")
            return False

    def cleanup_inactive_sessions(self, timeout_minutes: int = 60) -> int:
        """
        Clean up inactive sessions.

        Args:
            timeout_minutes: Session timeout in minutes

        Returns:
            Number of sessions cleaned up
        """
        try:
            count = self.session_repository.cleanup_inactive_sessions(timeout_minutes)

            if count > 0:
                current_app.logger.info(
                    f"Cleaned up {count} inactive sessions"
                )

            return count

        except Exception as e:
            current_app.logger.error(f"Error cleaning up sessions: {str(e)}")
            return 0

    def get_active_session_count(self) -> int:
        """
        Get count of active sessions.

        Returns:
            Number of active sessions
        """
        try:
            return self.session_repository.get_active_session_count()
        except Exception as e:
            current_app.logger.error(f"Error getting session count: {str(e)}")
            return 0

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get connection statistics.

        Returns:
            Dictionary with connection statistics
        """
        try:
            active_count = self.session_repository.get_active_session_count()

            return {
                'active_sessions': active_count,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            current_app.logger.error(f"Error getting statistics: {str(e)}")
            return {'active_sessions': 0}
