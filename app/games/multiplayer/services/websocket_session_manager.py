from typing import Dict, Optional, Set
from datetime import datetime, timezone
from threading import Lock
from flask import current_app


class WebSocketSessionManager:
    """
    Thread-safe manager for WebSocket sessions and authentication state.

    Manages the mapping between WebSocket session IDs and authenticated users,
    supporting multiple concurrent sessions per user.
    """

    def __init__(self):
        """Initialize session manager with thread-safe dictionaries"""
        self._sessions: Dict[str, Dict] = {}
        self._user_sessions: Dict[str, Set[str]] = {}  # user_id -> set of session_ids
        self._lock = Lock()

    def create_session(
        self,
        session_id: str,
        user_id: str,
        token: str,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Create new authenticated session.

        Args:
            session_id: WebSocket session ID (socket.sid)
            user_id: Authenticated user ID
            token: JWT token used for authentication
            metadata: Optional additional session metadata

        Returns:
            True if session created successfully
        """
        with self._lock:
            self._sessions[session_id] = {
                'user_id': user_id,
                'token': token,
                'authenticated_at': datetime.now(timezone.utc),
                'last_activity': datetime.now(timezone.utc),
                'rooms': set(),
                'metadata': metadata or {}
            }

            # Track user sessions
            if user_id not in self._user_sessions:
                self._user_sessions[user_id] = set()
            self._user_sessions[user_id].add(session_id)

            current_app.logger.debug(
                f"Session created: sid={session_id}, user={user_id}"
            )

            return True

    def get_session(self, session_id: str) -> Optional[Dict]:
        """
        Get session data by session ID.

        Args:
            session_id: WebSocket session ID

        Returns:
            Session data dict or None if not found
        """
        return self._sessions.get(session_id)

    def get_user_id(self, session_id: str) -> Optional[str]:
        """
        Get user ID for a session.

        Args:
            session_id: WebSocket session ID

        Returns:
            User ID string or None if session not found
        """
        session = self._sessions.get(session_id)
        return session['user_id'] if session else None

    def update_activity(self, session_id: str) -> bool:
        """
        Update last activity timestamp for session.

        Args:
            session_id: WebSocket session ID

        Returns:
            True if session found and updated
        """
        if session_id in self._sessions:
            self._sessions[session_id]['last_activity'] = datetime.now(timezone.utc)
            return True
        return False

    def update_token(self, session_id: str, new_token: str) -> bool:
        """
        Update authentication token for session.

        Used for token refresh.

        Args:
            session_id: WebSocket session ID
            new_token: New JWT token

        Returns:
            True if session found and token updated
        """
        with self._lock:
            if session_id in self._sessions:
                self._sessions[session_id]['token'] = new_token
                self._sessions[session_id]['last_activity'] = datetime.now(timezone.utc)

                current_app.logger.debug(f"Token updated for session: {session_id}")
                return True
            return False

    def add_room(self, session_id: str, room_id: str) -> bool:
        """
        Add room to session's room list.

        Args:
            session_id: WebSocket session ID
            room_id: Room ID to add

        Returns:
            True if room added successfully
        """
        with self._lock:
            if session_id in self._sessions:
                self._sessions[session_id]['rooms'].add(room_id)
                return True
            return False

    def remove_room(self, session_id: str, room_id: str) -> bool:
        """
        Remove room from session's room list.

        Args:
            session_id: WebSocket session ID
            room_id: Room ID to remove

        Returns:
            True if room removed successfully
        """
        with self._lock:
            if session_id in self._sessions:
                self._sessions[session_id]['rooms'].discard(room_id)
                return True
            return False

    def get_session_rooms(self, session_id: str) -> Set[str]:
        """
        Get all rooms for a session.

        Args:
            session_id: WebSocket session ID

        Returns:
            Set of room IDs
        """
        session = self._sessions.get(session_id)
        return session['rooms'].copy() if session else set()

    def is_in_room(self, session_id: str, room_id: str) -> bool:
        """
        Check if session is in a specific room.

        Args:
            session_id: WebSocket session ID
            room_id: Room ID to check

        Returns:
            True if session is in the room
        """
        session = self._sessions.get(session_id)
        return room_id in session['rooms'] if session else False

    def remove_session(self, session_id: str) -> bool:
        """
        Remove session on disconnect.

        Args:
            session_id: WebSocket session ID to remove

        Returns:
            True if session was found and removed
        """
        with self._lock:
            session = self._sessions.pop(session_id, None)

            if session:
                user_id = session['user_id']

                # Remove from user sessions tracking
                if user_id in self._user_sessions:
                    self._user_sessions[user_id].discard(session_id)

                    # Clean up empty user entry
                    if not self._user_sessions[user_id]:
                        del self._user_sessions[user_id]

                current_app.logger.debug(
                    f"Session removed: sid={session_id}, user={user_id}"
                )
                return True

            return False

    def get_user_sessions(self, user_id: str) -> Set[str]:
        """
        Get all active sessions for a user.

        Supports multiple concurrent sessions per user.

        Args:
            user_id: User ID

        Returns:
            Set of session IDs for the user
        """
        return self._user_sessions.get(user_id, set()).copy()

    def is_authenticated(self, session_id: str) -> bool:
        """
        Check if session is authenticated.

        Args:
            session_id: WebSocket session ID

        Returns:
            True if session exists and is authenticated
        """
        return session_id in self._sessions

    def get_session_count(self) -> int:
        """
        Get total number of active sessions.

        Returns:
            Count of active sessions
        """
        return len(self._sessions)

    def get_user_count(self) -> int:
        """
        Get number of unique authenticated users.

        Returns:
            Count of unique users with active sessions
        """
        return len(self._user_sessions)

    def cleanup_inactive_sessions(self, timeout_minutes: int = 60) -> int:
        """
        Clean up sessions inactive for longer than timeout.

        Args:
            timeout_minutes: Inactivity timeout in minutes

        Returns:
            Number of sessions cleaned up
        """
        with self._lock:
            now = datetime.now(timezone.utc)
            inactive_sessions = []

            for session_id, session_data in self._sessions.items():
                last_activity = session_data['last_activity']
                inactive_duration = (now - last_activity).total_seconds() / 60

                if inactive_duration > timeout_minutes:
                    inactive_sessions.append(session_id)

            # Remove inactive sessions
            for session_id in inactive_sessions:
                self.remove_session(session_id)

            if inactive_sessions:
                current_app.logger.info(
                    f"Cleaned up {len(inactive_sessions)} inactive sessions"
                )

            return len(inactive_sessions)

    def get_statistics(self) -> Dict:
        """
        Get session statistics.

        Returns:
            Dictionary with session statistics
        """
        return {
            'total_sessions': self.get_session_count(),
            'unique_users': self.get_user_count(),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }


# Global singleton instance
websocket_session_manager = WebSocketSessionManager()
