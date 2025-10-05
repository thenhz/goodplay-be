import os
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from app.core.repositories.base_repository import BaseRepository
from app.games.multiplayer.models.player_state import PlayerState


class PlayerStateRepository(BaseRepository):
    """Repository for player state data access"""

    def __init__(self):
        super().__init__(PlayerState.COLLECTION_NAME)

    def create_indexes(self):
        """Create database indexes for player states"""
        if self.collection is None or os.getenv('TESTING') == 'true':
            return

        # Index for state ID lookup
        self.collection.create_index('state_id', unique=True)

        # Index for room lookup
        self.collection.create_index('room_id')

        # Index for user lookup
        self.collection.create_index('user_id')

        # Index for session lookup
        self.collection.create_index('session_id')

        # Compound index for room player states
        self.collection.create_index([
            ('room_id', 1),
            ('user_id', 1)
        ], unique=True)

        # Index for active players in room
        self.collection.create_index([
            ('room_id', 1),
            ('is_active', 1)
        ])

    def create_state(self, state: PlayerState) -> bool:
        """Create a new player state"""
        try:
            self.create(state.to_dict())
            return True
        except Exception:
            return False

    def find_by_state_id(self, state_id: str) -> Optional[PlayerState]:
        """Find state by state ID"""
        data = self.find_one({'state_id': state_id})
        return PlayerState.from_dict(data) if data else None

    def find_by_room_and_user(self, room_id: str, user_id: str) -> Optional[PlayerState]:
        """Find player state in a room"""
        data = self.find_one({
            'room_id': room_id,
            'user_id': user_id
        })
        return PlayerState.from_dict(data) if data else None

    def find_by_room(
        self,
        room_id: str,
        active_only: bool = True
    ) -> List[PlayerState]:
        """Find all player states in a room"""
        filter_dict = {'room_id': room_id}

        if active_only:
            filter_dict['is_active'] = True

        states_data = self.find_many(
            filter_dict,
            sort=[('updated_at', -1)]
        )

        return [PlayerState.from_dict(data) for data in states_data]

    def find_by_session(self, session_id: str) -> Optional[PlayerState]:
        """Find player state by session ID"""
        data = self.find_one({'session_id': session_id})
        return PlayerState.from_dict(data) if data else None

    def update_state(self, state_id: str, updates: Dict[str, Any]) -> bool:
        """Update player state"""
        updates['updated_at'] = datetime.now(timezone.utc)
        return self.update_one({'state_id': state_id}, updates)

    def update_game_state(
        self,
        room_id: str,
        user_id: str,
        game_state: Dict[str, Any]
    ) -> bool:
        """Update player game state"""
        return self.update_one(
            {'room_id': room_id, 'user_id': user_id},
            {
                'game_state': game_state,
                'last_action': datetime.now(timezone.utc),
                'updated_at': datetime.now(timezone.utc),
                '$inc': {'sync_version': 1}
            }
        )

    def update_score(self, room_id: str, user_id: str, score: int) -> bool:
        """Update player score"""
        return self.update_one(
            {'room_id': room_id, 'user_id': user_id},
            {
                'score': score,
                'updated_at': datetime.now(timezone.utc),
                '$inc': {'sync_version': 1}
            }
        )

    def update_position(
        self,
        room_id: str,
        user_id: str,
        position: Dict[str, float]
    ) -> bool:
        """Update player position"""
        return self.update_one(
            {'room_id': room_id, 'user_id': user_id},
            {
                'position': position,
                'last_action': datetime.now(timezone.utc),
                'updated_at': datetime.now(timezone.utc),
                '$inc': {'sync_version': 1}
            }
        )

    def set_ready(self, room_id: str, user_id: str, is_ready: bool) -> bool:
        """Set player ready status"""
        return self.update_one(
            {'room_id': room_id, 'user_id': user_id},
            {
                'is_ready': is_ready,
                'updated_at': datetime.now(timezone.utc)
            }
        )

    def set_active(self, room_id: str, user_id: str, is_active: bool) -> bool:
        """Set player active status"""
        return self.update_one(
            {'room_id': room_id, 'user_id': user_id},
            {
                'is_active': is_active,
                'updated_at': datetime.now(timezone.utc)
            }
        )

    def delete_by_room(self, room_id: str) -> int:
        """Delete all player states in a room"""
        result = self.collection.delete_many({'room_id': room_id})
        return result.deleted_count

    def delete_by_session(self, session_id: str) -> bool:
        """Delete player state by session ID"""
        return self.delete_one({'session_id': session_id})

    def get_ready_count(self, room_id: str) -> int:
        """Get count of ready players in room"""
        return self.count({
            'room_id': room_id,
            'is_ready': True,
            'is_active': True
        })

    def get_active_count(self, room_id: str) -> int:
        """Get count of active players in room"""
        return self.count({
            'room_id': room_id,
            'is_active': True
        })

    def cleanup_inactive_states(self, hours: int = 24) -> int:
        """
        Clean up inactive player states.

        Args:
            hours: Age threshold in hours

        Returns:
            Number of states deleted
        """
        cutoff_time = datetime.now(timezone.utc)
        cutoff_time = cutoff_time.replace(hour=cutoff_time.hour - hours)

        result = self.collection.delete_many({
            'is_active': False,
            'updated_at': {'$lt': cutoff_time}
        })

        return result.deleted_count
