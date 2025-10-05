import os
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from app.core.repositories.base_repository import BaseRepository
from app.games.multiplayer.models.game_room import GameRoom


class RoomRepository(BaseRepository):
    """Repository for game room data access"""

    def __init__(self):
        super().__init__(GameRoom.COLLECTION_NAME)

    def create_indexes(self):
        """Create database indexes for game rooms"""
        if self.collection is None or os.getenv('TESTING') == 'true':
            return

        # Index for room ID lookup
        self.collection.create_index('room_id', unique=True)

        # Index for room code lookup
        self.collection.create_index('room_code', unique=True)

        # Index for game ID filtering
        self.collection.create_index('game_id')

        # Index for host lookup
        self.collection.create_index('host_user_id')

        # Index for status filtering
        self.collection.create_index('status')

        # Compound index for available rooms
        self.collection.create_index([
            ('game_id', 1),
            ('status', 1),
            ('created_at', -1)
        ])

    def create_room(self, room: GameRoom) -> bool:
        """Create a new game room"""
        try:
            self.create(room.to_dict())
            return True
        except Exception:
            return False

    def find_by_room_id(self, room_id: str) -> Optional[GameRoom]:
        """Find room by room ID"""
        data = self.find_one({'room_id': room_id})
        return GameRoom.from_dict(data) if data else None

    def find_by_room_code(self, room_code: str) -> Optional[GameRoom]:
        """Find room by room code"""
        data = self.find_one({'room_code': room_code.upper()})
        return GameRoom.from_dict(data) if data else None

    def find_by_game_id(
        self,
        game_id: str,
        status: Optional[str] = None,
        limit: int = 20
    ) -> List[GameRoom]:
        """Find rooms by game ID"""
        filter_dict = {'game_id': game_id}

        if status:
            filter_dict['status'] = status

        rooms_data = self.find_many(
            filter_dict,
            limit=limit,
            sort=[('created_at', -1)]
        )

        return [GameRoom.from_dict(data) for data in rooms_data]

    def find_by_host(self, user_id: str) -> List[GameRoom]:
        """Find rooms hosted by user"""
        rooms_data = self.find_many(
            {'host_user_id': user_id},
            sort=[('created_at', -1)]
        )

        return [GameRoom.from_dict(data) for data in rooms_data]

    def find_by_player(self, user_id: str, active_only: bool = True) -> List[GameRoom]:
        """Find rooms where user is a player"""
        filter_dict = {'player_ids': user_id}

        if active_only:
            filter_dict['status'] = {'$in': [GameRoom.STATUS_WAITING, GameRoom.STATUS_PLAYING]}

        rooms_data = self.find_many(
            filter_dict,
            sort=[('created_at', -1)]
        )

        return [GameRoom.from_dict(data) for data in rooms_data]

    def find_available_rooms(
        self,
        game_id: Optional[str] = None,
        limit: int = 20
    ) -> List[GameRoom]:
        """Find available rooms (waiting status and not full)"""
        filter_dict = {'status': GameRoom.STATUS_WAITING}

        if game_id:
            filter_dict['game_id'] = game_id

        # Note: This is a simplified query. In production, you might want
        # to add a computed field or use aggregation to filter by room capacity
        rooms_data = self.find_many(
            filter_dict,
            limit=limit,
            sort=[('created_at', -1)]
        )

        rooms = [GameRoom.from_dict(data) for data in rooms_data]

        # Filter out full rooms
        return [room for room in rooms if not room.is_full()]

    def update_room(self, room_id: str, updates: Dict[str, Any]) -> bool:
        """Update room by room ID"""
        return self.update_one({'room_id': room_id}, updates)

    def add_player(self, room_id: str, user_id: str) -> bool:
        """Add player to room"""
        result = self.collection.update_one(
            {'room_id': room_id},
            {'$addToSet': {'player_ids': user_id}}
        )
        return result.modified_count > 0

    def remove_player(self, room_id: str, user_id: str) -> bool:
        """Remove player from room"""
        result = self.collection.update_one(
            {'room_id': room_id},
            {'$pull': {'player_ids': user_id}}
        )
        return result.modified_count > 0

    def update_status(self, room_id: str, status: str) -> bool:
        """Update room status"""
        updates = {'status': status}

        if status == GameRoom.STATUS_PLAYING:
            updates['started_at'] = datetime.now(timezone.utc)
        elif status == GameRoom.STATUS_FINISHED:
            updates['finished_at'] = datetime.now(timezone.utc)

        return self.update_one({'room_id': room_id}, updates)

    def cleanup_old_rooms(self, hours: int = 24) -> int:
        """
        Clean up old finished or abandoned rooms.

        Args:
            hours: Age threshold in hours

        Returns:
            Number of rooms deleted
        """
        cutoff_time = datetime.now(timezone.utc)
        cutoff_time = cutoff_time.replace(hour=cutoff_time.hour - hours)

        result = self.collection.delete_many({
            'status': {'$in': [GameRoom.STATUS_FINISHED, GameRoom.STATUS_ABANDONED]},
            'created_at': {'$lt': cutoff_time}
        })

        return result.deleted_count

    def get_room_statistics(self) -> Dict[str, int]:
        """Get room statistics"""
        return {
            'total': self.count({}),
            'waiting': self.count({'status': GameRoom.STATUS_WAITING}),
            'playing': self.count({'status': GameRoom.STATUS_PLAYING}),
            'finished': self.count({'status': GameRoom.STATUS_FINISHED}),
            'abandoned': self.count({'status': GameRoom.STATUS_ABANDONED})
        }
