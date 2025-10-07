from typing import Optional, Dict, List, Any, Tuple
from flask import current_app
from app.games.multiplayer.repositories.room_repository import RoomRepository
from app.games.multiplayer.models.game_room import GameRoom


class LobbyService:
    """
    Service for lobby and room discovery.

    Handles:
    - Room browsing and filtering
    - Quick match functionality
    - Room recommendations
    - Lobby statistics
    """

    def __init__(self):
        self.room_repository = RoomRepository()

    def browse_rooms(
        self,
        game_id: Optional[str] = None,
        privacy: str = GameRoom.PRIVACY_PUBLIC,
        tags: Optional[List[str]] = None,
        search_query: Optional[str] = None,
        page: int = 1,
        per_page: int = 20
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Browse available rooms with filters and pagination.

        Args:
            game_id: Filter by game ID
            privacy: Filter by privacy (default: public)
            tags: Filter by tags
            search_query: Text search in room name/description
            page: Page number (1-indexed)
            per_page: Results per page

        Returns:
            Tuple of (success, message, data)
        """
        try:
            offset = (page - 1) * per_page

            rooms, total_count = self.room_repository.search_rooms(
                game_id=game_id,
                privacy=privacy,
                tags=tags,
                search_query=search_query,
                status=GameRoom.STATUS_WAITING,
                limit=per_page,
                offset=offset
            )

            # Filter out full rooms
            available_rooms = [room for room in rooms if not room.is_full()]

            total_pages = (total_count + per_page - 1) // per_page

            data = {
                'rooms': [room.to_dict() for room in available_rooms],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total_count,
                    'total_pages': total_pages,
                    'has_next': page < total_pages,
                    'has_prev': page > 1
                }
            }

            return True, "ROOMS_RETRIEVED_SUCCESS", data

        except Exception as e:
            current_app.logger.error(f"Error browsing rooms: {str(e)}", exc_info=True)
            return False, "BROWSE_ROOMS_ERROR", None

    def quick_match(
        self,
        user_id: str,
        game_id: str
    ) -> Tuple[bool, str, Optional[GameRoom]]:
        """
        Find and return best available room for quick match.

        Strategy:
        1. Find public rooms for the game
        2. Prioritize rooms with players (social aspect)
        3. Avoid empty rooms if possible
        4. Return first suitable room

        Args:
            user_id: User ID
            game_id: Game ID

        Returns:
            Tuple of (success, message, room)
        """
        try:
            # Get available public rooms for game
            rooms = self.room_repository.find_available_rooms(
                game_id=game_id,
                limit=50
            )

            if not rooms:
                return False, "NO_ROOMS_AVAILABLE", None

            # Filter to only public rooms
            public_rooms = [r for r in rooms if r.privacy == GameRoom.PRIVACY_PUBLIC]

            if not public_rooms:
                return False, "NO_PUBLIC_ROOMS", None

            # Sort by player count (prefer rooms with players)
            public_rooms.sort(key=lambda r: r.get_player_count(), reverse=True)

            # Find first room user is not already in
            for room in public_rooms:
                if not room.has_player(user_id) and not room.is_full():
                    return True, "QUICK_MATCH_FOUND", room

            return False, "NO_SUITABLE_ROOM", None

        except Exception as e:
            current_app.logger.error(f"Error in quick match: {str(e)}", exc_info=True)
            return False, "QUICK_MATCH_ERROR", None

    def get_recommended_rooms(
        self,
        user_id: str,
        game_id: Optional[str] = None,
        limit: int = 10
    ) -> Tuple[bool, str, List[GameRoom]]:
        """
        Get recommended rooms for user.

        Recommendation strategy:
        1. Rooms with friends (future)
        2. Popular rooms (most players)
        3. Recently created rooms
        4. Rooms matching user's game history (future)

        Args:
            user_id: User ID
            game_id: Optional game ID filter
            limit: Maximum recommendations

        Returns:
            Tuple of (success, message, rooms)
        """
        try:
            # For now, return popular public rooms
            rooms, _ = self.room_repository.search_rooms(
                game_id=game_id,
                privacy=GameRoom.PRIVACY_PUBLIC,
                status=GameRoom.STATUS_WAITING,
                limit=limit * 2  # Get more to filter
            )

            # Filter out full rooms and rooms user is in
            recommended = [
                room for room in rooms
                if not room.is_full() and not room.has_player(user_id)
            ]

            # Sort by player count (popular rooms first)
            recommended.sort(key=lambda r: r.get_player_count(), reverse=True)

            # Limit results
            recommended = recommended[:limit]

            return True, "RECOMMENDATIONS_RETRIEVED", recommended

        except Exception as e:
            current_app.logger.error(f"Error getting recommendations: {str(e)}", exc_info=True)
            return False, "RECOMMENDATIONS_ERROR", []

    def get_lobby_statistics(
        self,
        game_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get lobby statistics.

        Args:
            game_id: Optional filter by game ID

        Returns:
            Dictionary with lobby statistics
        """
        try:
            stats = {
                'total_rooms': 0,
                'waiting_rooms': 0,
                'playing_rooms': 0,
                'total_players': 0,
                'total_spectators': 0,
                'average_players_per_room': 0
            }

            # Get room counts
            filter_waiting = {'status': GameRoom.STATUS_WAITING}
            filter_playing = {'status': GameRoom.STATUS_PLAYING}

            if game_id:
                filter_waiting['game_id'] = game_id
                filter_playing['game_id'] = game_id

            stats['waiting_rooms'] = self.room_repository.count(filter_waiting)
            stats['playing_rooms'] = self.room_repository.count(filter_playing)
            stats['total_rooms'] = stats['waiting_rooms'] + stats['playing_rooms']

            # Get aggregate player/spectator counts (simplified)
            # In production, you might want to use MongoDB aggregation
            all_active_rooms = self.room_repository.find_many(
                {'status': {'$in': [GameRoom.STATUS_WAITING, GameRoom.STATUS_PLAYING]}} |
                ({'game_id': game_id} if game_id else {})
            )

            total_players = 0
            total_spectators = 0

            for room_data in all_active_rooms:
                room = GameRoom.from_dict(room_data)
                total_players += room.get_player_count()
                total_spectators += room.get_spectator_count()

            stats['total_players'] = total_players
            stats['total_spectators'] = total_spectators

            if stats['total_rooms'] > 0:
                stats['average_players_per_room'] = round(
                    total_players / stats['total_rooms'], 1
                )

            return stats

        except Exception as e:
            current_app.logger.error(f"Error getting lobby stats: {str(e)}", exc_info=True)
            return {}

    def search_rooms_by_tag(
        self,
        tag: str,
        game_id: Optional[str] = None,
        limit: int = 20
    ) -> Tuple[bool, str, List[GameRoom]]:
        """
        Search rooms by tag.

        Args:
            tag: Tag to search for
            game_id: Optional game ID filter
            limit: Maximum results

        Returns:
            Tuple of (success, message, rooms)
        """
        try:
            rooms = self.room_repository.get_rooms_by_tag(tag, limit=limit)

            # Filter by game_id if provided
            if game_id:
                rooms = [room for room in rooms if room.game_id == game_id]

            # Filter out full rooms
            rooms = [room for room in rooms if not room.is_full()]

            return True, "ROOMS_BY_TAG_RETRIEVED", rooms

        except Exception as e:
            current_app.logger.error(f"Error searching by tag: {str(e)}", exc_info=True)
            return False, "TAG_SEARCH_ERROR", []

    def get_popular_tags(
        self,
        game_id: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get popular room tags.

        Args:
            game_id: Optional game ID filter
            limit: Maximum tags to return

        Returns:
            List of tag dictionaries with counts
        """
        try:
            # This would ideally use MongoDB aggregation
            # Simplified version for now
            filter_dict = {'status': GameRoom.STATUS_WAITING}
            if game_id:
                filter_dict['game_id'] = game_id

            rooms_data = self.room_repository.find_many(filter_dict, limit=1000)

            # Count tag occurrences
            tag_counts = {}
            for room_data in rooms_data:
                for tag in room_data.get('tags', []):
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1

            # Sort by count and format
            popular_tags = [
                {'tag': tag, 'count': count}
                for tag, count in sorted(
                    tag_counts.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:limit]
            ]

            return popular_tags

        except Exception as e:
            current_app.logger.error(f"Error getting popular tags: {str(e)}", exc_info=True)
            return []
