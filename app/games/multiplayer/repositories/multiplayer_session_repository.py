import os
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from app.core.repositories.base_repository import BaseRepository
from app.games.multiplayer.models.multiplayer_session import MultiplayerSession


class MultiplayerSessionRepository(BaseRepository):
    """Repository for multiplayer session data access"""

    def __init__(self):
        super().__init__(MultiplayerSession.COLLECTION_NAME)

    def create_indexes(self):
        """Create database indexes for multiplayer sessions"""
        if self.collection is None or os.getenv('TESTING') == 'true':
            return

        # Index for session lookup
        self.collection.create_index('session_id', unique=True)

        # Index for user sessions lookup
        self.collection.create_index('user_id')

        # Index for room sessions lookup
        self.collection.create_index('room_id')

        # Index for status filtering
        self.collection.create_index('status')

        # Compound index for active user sessions
        self.collection.create_index([
            ('user_id', 1),
            ('status', 1),
            ('connected_at', -1)
        ])

    def create_session(self, session: MultiplayerSession) -> bool:
        """Create a new multiplayer session"""
        try:
            self.create(session.to_dict())
            return True
        except Exception:
            return False

    def find_by_session_id(self, session_id: str) -> Optional[MultiplayerSession]:
        """Find session by session ID"""
        data = self.find_one({'session_id': session_id})
        return MultiplayerSession.from_dict(data) if data else None

    def find_by_user_id(self, user_id: str, active_only: bool = True) -> List[MultiplayerSession]:
        """Find all sessions for a user"""
        filter_dict = {'user_id': user_id}

        if active_only:
            filter_dict['status'] = MultiplayerSession.STATUS_ACTIVE

        sessions_data = self.find_many(
            filter_dict,
            sort=[('connected_at', -1)]
        )

        return [MultiplayerSession.from_dict(data) for data in sessions_data]

    def find_by_room_id(self, room_id: str) -> List[MultiplayerSession]:
        """Find all active sessions in a room"""
        sessions_data = self.find_many({
            'room_id': room_id,
            'status': MultiplayerSession.STATUS_ACTIVE
        })

        return [MultiplayerSession.from_dict(data) for data in sessions_data]

    def update_session(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """Update session by session ID"""
        return self.update_one({'session_id': session_id}, updates)

    def update_ping(self, session_id: str, latency_ms: int) -> bool:
        """Update session ping timestamp and latency"""
        return self.update_one(
            {'session_id': session_id},
            {
                'last_ping': datetime.now(timezone.utc),
                'latency_ms': latency_ms
            }
        )

    def update_room(self, session_id: str, room_id: Optional[str]) -> bool:
        """Update session room ID"""
        return self.update_one(
            {'session_id': session_id},
            {'room_id': room_id}
        )

    def mark_disconnected(self, session_id: str) -> bool:
        """Mark session as disconnected"""
        return self.update_one(
            {'session_id': session_id},
            {'status': MultiplayerSession.STATUS_DISCONNECTED}
        )

    def cleanup_inactive_sessions(self, timeout_minutes: int = 60) -> int:
        """
        Clean up inactive sessions older than timeout.

        Args:
            timeout_minutes: Session timeout in minutes

        Returns:
            Number of sessions deleted
        """
        cutoff_time = datetime.now(timezone.utc)
        cutoff_time = cutoff_time.replace(
            minute=cutoff_time.minute - timeout_minutes
        )

        result = self.collection.delete_many({
            '$or': [
                {'status': MultiplayerSession.STATUS_DISCONNECTED},
                {
                    'status': MultiplayerSession.STATUS_IDLE,
                    'last_ping': {'$lt': cutoff_time}
                }
            ]
        })

        return result.deleted_count

    def get_active_session_count(self) -> int:
        """Get count of active sessions"""
        return self.count({'status': MultiplayerSession.STATUS_ACTIVE})

    def get_user_session_count(self, user_id: str) -> int:
        """Get count of active sessions for a user"""
        return self.count({
            'user_id': user_id,
            'status': MultiplayerSession.STATUS_ACTIVE
        })
