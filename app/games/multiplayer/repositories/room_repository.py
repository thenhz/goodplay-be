import os
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timezone, timedelta
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

        # Existing indexes
        self.collection.create_index('room_id', unique=True)
        self.collection.create_index('room_code', unique=True)
        self.collection.create_index('game_id')
        self.collection.create_index('host_user_id')
        self.collection.create_index('status')

        # Compound index for available rooms
        self.collection.create_index([
            ('game_id', 1),
            ('status', 1),
            ('created_at', -1)
        ])

        # New GOO-56 indexes
        self.collection.create_index('privacy')
        self.collection.create_index('tags')
        self.collection.create_index('player_ids')
        self.collection.create_index('spectator_ids')

        # Compound indexes for advanced search
        self.collection.create_index([
            ('privacy', 1),
            ('status', 1),
            ('created_at', -1)
        ])

        self.collection.create_index([
            ('game_id', 1),
            ('privacy', 1),
            ('status', 1)
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

    # New GOO-56 methods

    def search_rooms(
        self,
        game_id: Optional[str] = None,
        privacy: Optional[str] = None,
        min_players: Optional[int] = None,
        max_players: Optional[int] = None,
        tags: Optional[List[str]] = None,
        search_query: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> Tuple[List[GameRoom], int]:
        """
        Advanced room search with filters and pagination.

        Args:
            game_id: Filter by game ID
            privacy: Filter by privacy setting
            min_players: Minimum number of current players
            max_players: Maximum number of current players
            tags: Filter by tags (any match)
            search_query: Text search in room name and description
            status: Filter by status
            limit: Maximum results per page
            offset: Results offset for pagination

        Returns:
            Tuple of (rooms list, total count)
        """
        filter_dict = {}

        if game_id:
            filter_dict['game_id'] = game_id

        if privacy:
            filter_dict['privacy'] = privacy

        if tags:
            filter_dict['tags'] = {'$in': tags}

        if status:
            filter_dict['status'] = status
        else:
            # Default to active rooms
            filter_dict['status'] = {'$in': [GameRoom.STATUS_WAITING, GameRoom.STATUS_PLAYING]}

        if search_query:
            filter_dict['$or'] = [
                {'room_name': {'$regex': search_query, '$options': 'i'}},
                {'description': {'$regex': search_query, '$options': 'i'}}
            ]

        # Get total count
        total_count = self.count(filter_dict)

        # Get paginated results
        rooms_data = self.find_many(
            filter_dict,
            limit=limit,
            skip=offset,
            sort=[('created_at', -1)]
        )

        rooms = [GameRoom.from_dict(data) for data in rooms_data]

        # Filter by player count if specified (post-query filtering)
        if min_players is not None or max_players is not None:
            filtered_rooms = []
            for room in rooms:
                player_count = room.get_player_count()
                if min_players is not None and player_count < min_players:
                    continue
                if max_players is not None and player_count > max_players:
                    continue
                filtered_rooms.append(room)
            rooms = filtered_rooms

        return rooms, total_count

    def update_player_ready_state(
        self,
        room_id: str,
        user_id: str,
        is_ready: bool
    ) -> bool:
        """
        Update player ready state in room.

        Args:
            room_id: Room ID
            user_id: User ID
            is_ready: Ready state

        Returns:
            True if updated successfully
        """
        result = self.collection.update_one(
            {'room_id': room_id},
            {'$set': {f'player_ready_states.{user_id}': is_ready}}
        )
        return result.modified_count > 0

    def add_spectator(self, room_id: str, user_id: str) -> bool:
        """
        Add spectator to room.

        Args:
            room_id: Room ID
            user_id: User ID

        Returns:
            True if added successfully
        """
        result = self.collection.update_one(
            {'room_id': room_id},
            {'$addToSet': {'spectator_ids': user_id}}
        )
        return result.modified_count > 0

    def remove_spectator(self, room_id: str, user_id: str) -> bool:
        """
        Remove spectator from room.

        Args:
            room_id: Room ID
            user_id: User ID

        Returns:
            True if removed successfully
        """
        result = self.collection.update_one(
            {'room_id': room_id},
            {'$pull': {'spectator_ids': user_id}}
        )
        return result.modified_count > 0

    def get_rooms_by_tag(self, tag: str, limit: int = 20) -> List[GameRoom]:
        """
        Find rooms by tag.

        Args:
            tag: Tag to search for
            limit: Maximum number of results

        Returns:
            List of rooms with the specified tag
        """
        rooms_data = self.find_many(
            {'tags': tag, 'status': GameRoom.STATUS_WAITING},
            limit=limit,
            sort=[('created_at', -1)]
        )

        return [GameRoom.from_dict(data) for data in rooms_data]

    def get_user_hosted_rooms(self, user_id: str, active_only: bool = True) -> List[GameRoom]:
        """
        Get rooms hosted by user.

        Args:
            user_id: User ID
            active_only: Only return active rooms (waiting/playing)

        Returns:
            List of rooms hosted by user
        """
        filter_dict = {'host_user_id': user_id}

        if active_only:
            filter_dict['status'] = {'$in': [GameRoom.STATUS_WAITING, GameRoom.STATUS_PLAYING]}

        rooms_data = self.find_many(
            filter_dict,
            sort=[('created_at', -1)]
        )

        return [GameRoom.from_dict(data) for data in rooms_data]

    def update_room_settings(
        self,
        room_id: str,
        settings: Dict[str, Any]
    ) -> bool:
        """
        Update room configuration settings.

        Args:
            room_id: Room ID
            settings: Settings to update

        Returns:
            True if updated successfully
        """
        # Whitelist of updatable settings
        allowed_fields = [
            'room_name', 'description', 'tags', 'privacy',
            'allow_spectators', 'max_spectators',
            'auto_start_when_ready', 'auto_start_timer'
        ]

        updates = {k: v for k, v in settings.items() if k in allowed_fields}

        if not updates:
            return False

        return self.update_one({'room_id': room_id}, updates)

    def find_by_spectator(self, user_id: str) -> List[GameRoom]:
        """
        Find rooms where user is a spectator.

        Args:
            user_id: User ID

        Returns:
            List of rooms where user is spectator
        """
        rooms_data = self.find_many(
            {'spectator_ids': user_id},
            sort=[('created_at', -1)]
        )

        return [GameRoom.from_dict(data) for data in rooms_data]

    def cleanup_stale_rooms(self, timeout_minutes: int = 60) -> int:
        """
        Remove old inactive waiting rooms.

        Args:
            timeout_minutes: Inactivity timeout in minutes

        Returns:
            Number of rooms cleaned up
        """
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=timeout_minutes)

        result = self.collection.delete_many({
            'status': GameRoom.STATUS_WAITING,
            'created_at': {'$lt': cutoff_time}
        })

        return result.deleted_count
