from typing import Optional, List, Dict, Any
from bson import ObjectId
from pymongo import ASCENDING, DESCENDING

from app.core.repositories.base_repository import BaseRepository
from ..models.game import Game

class GameRepository(BaseRepository):
    """Repository for Game collection operations"""

    def __init__(self):
        super().__init__("games")

    def create_indexes(self):
        """Create indexes for the games collection"""
        self.collection.create_index([("name", ASCENDING)], unique=True)
        self.collection.create_index([("plugin_id", ASCENDING)], unique=True)
        self.collection.create_index([("category", ASCENDING)])
        self.collection.create_index([("is_active", ASCENDING)])
        self.collection.create_index([("created_at", DESCENDING)])
        self.collection.create_index([("rating", DESCENDING)])
        self.collection.create_index([("install_count", DESCENDING)])

    def create_game(self, game: Game) -> Optional[str]:
        """
        Create a new game in the database.

        Args:
            game: Game instance to create

        Returns:
            Optional[str]: Game ID if successful, None otherwise
        """
        try:
            game_data = game.to_dict()
            game_data.pop("_id", None)  # Remove _id if present

            result = self.collection.insert_one(game_data)
            return str(result.inserted_id)
        except Exception:
            return None

    def get_game_by_id(self, game_id: str) -> Optional[Game]:
        """
        Get a game by its ID.

        Args:
            game_id: The game ID

        Returns:
            Optional[Game]: Game instance if found, None otherwise
        """
        game_data = self.find_by_id(game_id)
        if game_data:
            return Game.from_dict(game_data)
        return None

    def get_game_by_plugin_id(self, plugin_id: str) -> Optional[Game]:
        """
        Get a game by its plugin ID.

        Args:
            plugin_id: The plugin ID

        Returns:
            Optional[Game]: Game instance if found, None otherwise
        """
        game_data = self.find_one({"plugin_id": plugin_id})
        if game_data:
            return Game.from_dict(game_data)
        return None

    def get_game_by_name(self, name: str) -> Optional[Game]:
        """
        Get a game by its name.

        Args:
            name: The game name

        Returns:
            Optional[Game]: Game instance if found, None otherwise
        """
        game_data = self.find_one({"name": name})
        if game_data:
            return Game.from_dict(game_data)
        return None

    def get_games_by_category(self, category: str, active_only: bool = True) -> List[Game]:
        """
        Get games by category.

        Args:
            category: The game category
            active_only: If True, only return active games

        Returns:
            List[Game]: List of games in the category
        """
        filter_dict = {"category": category}
        if active_only:
            filter_dict["is_active"] = True

        games_data = self.find_many(filter_dict, sort=[("rating", DESCENDING)])
        return [Game.from_dict(data) for data in games_data]

    def get_all_games(self, active_only: bool = True, limit: int = None,
                      skip: int = None, sort_by: str = "created_at") -> List[Game]:
        """
        Get all games.

        Args:
            active_only: If True, only return active games
            limit: Maximum number of games to return
            skip: Number of games to skip
            sort_by: Field to sort by (created_at, rating, install_count, name)

        Returns:
            List[Game]: List of games
        """
        filter_dict = {}
        if active_only:
            filter_dict["is_active"] = True

        sort_direction = DESCENDING if sort_by in ["created_at", "rating", "install_count"] else ASCENDING
        sort_list = [(sort_by, sort_direction)]

        games_data = self.find_many(filter_dict, limit=limit, skip=skip, sort=sort_list)
        return [Game.from_dict(data) for data in games_data]

    def update_game(self, game_id: str, game: Game) -> bool:
        """
        Update a game.

        Args:
            game_id: The game ID
            game: Updated game instance

        Returns:
            bool: True if successful, False otherwise
        """
        game_data = game.to_dict()
        game_data.pop("_id", None)  # Remove _id
        game_data.pop("created_at", None)  # Don't update created_at

        return self.update_by_id(game_id, game_data)

    def update_game_rating(self, game_id: str, new_rating: float, total_ratings: int) -> bool:
        """
        Update a game's rating.

        Args:
            game_id: The game ID
            new_rating: The new average rating
            total_ratings: The total number of ratings

        Returns:
            bool: True if successful, False otherwise
        """
        update_data = {
            "rating": new_rating,
            "total_ratings": total_ratings,
            "updated_at": self._get_current_time()
        }
        return self.update_by_id(game_id, update_data)

    def increment_install_count(self, game_id: str) -> bool:
        """
        Increment the install count for a game.

        Args:
            game_id: The game ID

        Returns:
            bool: True if successful, False otherwise
        """
        if not ObjectId.is_valid(game_id):
            return False

        result = self.collection.update_one(
            {"_id": ObjectId(game_id)},
            {
                "$inc": {"install_count": 1},
                "$set": {"updated_at": self._get_current_time()}
            }
        )
        return result.modified_count > 0

    def set_game_active_status(self, game_id: str, is_active: bool) -> bool:
        """
        Set the active status of a game.

        Args:
            game_id: The game ID
            is_active: The new active status

        Returns:
            bool: True if successful, False otherwise
        """
        update_data = {
            "is_active": is_active,
            "updated_at": self._get_current_time()
        }
        return self.update_by_id(game_id, update_data)

    def delete_game(self, game_id: str) -> bool:
        """
        Delete a game.

        Args:
            game_id: The game ID

        Returns:
            bool: True if successful, False otherwise
        """
        return self.delete_by_id(game_id)

    def delete_game_by_plugin_id(self, plugin_id: str) -> bool:
        """
        Delete a game by plugin ID.

        Args:
            plugin_id: The plugin ID

        Returns:
            bool: True if successful, False otherwise
        """
        return self.delete_one({"plugin_id": plugin_id})

    def search_games(self, query: str, active_only: bool = True) -> List[Game]:
        """
        Search games by name or description.

        Args:
            query: Search query
            active_only: If True, only search active games

        Returns:
            List[Game]: List of matching games
        """
        filter_dict = {
            "$or": [
                {"name": {"$regex": query, "$options": "i"}},
                {"description": {"$regex": query, "$options": "i"}}
            ]
        }

        if active_only:
            filter_dict["is_active"] = True

        games_data = self.find_many(filter_dict, sort=[("rating", DESCENDING)])
        return [Game.from_dict(data) for data in games_data]

    def get_games_stats(self) -> Dict[str, Any]:
        """
        Get statistics about games.

        Returns:
            Dict[str, Any]: Games statistics
        """
        total_games = self.count()
        active_games = self.count({"is_active": True})

        # Get categories
        pipeline = [
            {"$group": {"_id": "$category", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        categories = list(self.collection.aggregate(pipeline))

        # Get average rating
        rating_pipeline = [
            {"$match": {"total_ratings": {"$gt": 0}}},
            {"$group": {"_id": None, "avg_rating": {"$avg": "$rating"}}}
        ]
        avg_rating_result = list(self.collection.aggregate(rating_pipeline))
        avg_rating = avg_rating_result[0]["avg_rating"] if avg_rating_result else 0

        return {
            "total_games": total_games,
            "active_games": active_games,
            "inactive_games": total_games - active_games,
            "categories": categories,
            "average_rating": round(avg_rating, 2) if avg_rating else 0
        }