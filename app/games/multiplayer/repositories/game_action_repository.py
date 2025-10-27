"""
Game Action Repository

Data access layer for game actions in multiplayer sessions.
"""

from typing import List, Optional
from datetime import datetime, timezone
from bson import ObjectId

from app.core.repositories.base_repository import BaseRepository
from app.games.multiplayer.models.game_action import GameAction


class GameActionRepository(BaseRepository):
    """Repository for managing game actions"""

    def __init__(self):
        super().__init__("game_actions")

    def create_indexes(self):
        """Create MongoDB indexes for performance"""
        import os
        if self.collection is None or os.getenv('TESTING') == 'true':
            return

        # Index for room actions (most common query)
        self.collection.create_index([("room_id", 1), ("sequence_number", 1)])

        # Index for user actions
        self.collection.create_index("user_id")

        # Index for timestamp (for cleanup/replay)
        self.collection.create_index("timestamp")

        # Index for action_id (idempotency)
        self.collection.create_index("action_id", unique=True, sparse=True)

    def save_action(self, action: GameAction) -> bool:
        """
        Save a game action.

        Args:
            action: GameAction to save

        Returns:
            bool: True if saved successfully
        """
        try:
            result = self.collection.insert_one(action.to_dict())
            action._id = result.inserted_id
            return True
        except Exception as e:
            print(f"Error saving action: {e}")
            return False

    def get_room_actions(self, room_id: str, since_sequence: int = 0, limit: int = 100) -> List[GameAction]:
        """
        Get actions for a room since a specific sequence number.

        Args:
            room_id: Room ID
            since_sequence: Get actions after this sequence number
            limit: Maximum number of actions to return

        Returns:
            List of GameActions
        """
        try:
            query = {
                "room_id": room_id,
                "sequence_number": {"$gt": since_sequence}
            }

            cursor = self.collection.find(query).sort("sequence_number", 1).limit(limit)
            return [GameAction.from_dict(doc) for doc in cursor]
        except Exception as e:
            print(f"Error getting room actions: {e}")
            return []

    def get_action_by_id(self, action_id: str) -> Optional[GameAction]:
        """
        Get action by its client-generated ID (for idempotency).

        Args:
            action_id: Client-generated action ID

        Returns:
            GameAction or None
        """
        try:
            doc = self.collection.find_one({"action_id": action_id})
            return GameAction.from_dict(doc) if doc else None
        except Exception:
            return None

    def get_latest_sequence_number(self, room_id: str) -> int:
        """
        Get the latest sequence number for a room.

        Args:
            room_id: Room ID

        Returns:
            int: Latest sequence number (0 if no actions)
        """
        try:
            latest = self.collection.find_one(
                {"room_id": room_id},
                sort=[("sequence_number", -1)]
            )
            return latest["sequence_number"] if latest else 0
        except Exception:
            return 0

    def get_user_actions(self, user_id: str, limit: int = 50) -> List[GameAction]:
        """
        Get recent actions by a user.

        Args:
            user_id: User ID
            limit: Maximum number of actions

        Returns:
            List of GameActions
        """
        try:
            cursor = self.collection.find({"user_id": user_id}).sort("timestamp", -1).limit(limit)
            return [GameAction.from_dict(doc) for doc in cursor]
        except Exception as e:
            print(f"Error getting user actions: {e}")
            return []

    def delete_room_actions(self, room_id: str) -> bool:
        """
        Delete all actions for a room (cleanup after session end).

        Args:
            room_id: Room ID

        Returns:
            bool: True if deleted successfully
        """
        try:
            self.collection.delete_many({"room_id": room_id})
            return True
        except Exception as e:
            print(f"Error deleting room actions: {e}")
            return False

    def get_actions_since(self, room_id: str, since_timestamp: datetime) -> List[GameAction]:
        """
        Get actions since a specific timestamp (for polling).

        Args:
            room_id: Room ID
            since_timestamp: Get actions after this timestamp

        Returns:
            List of GameActions
        """
        try:
            query = {
                "room_id": room_id,
                "timestamp": {"$gt": since_timestamp}
            }

            cursor = self.collection.find(query).sort("timestamp", 1)
            return [GameAction.from_dict(doc) for doc in cursor]
        except Exception as e:
            print(f"Error getting actions since timestamp: {e}")
            return []

    def count_room_actions(self, room_id: str) -> int:
        """
        Count total actions in a room.

        Args:
            room_id: Room ID

        Returns:
            int: Number of actions
        """
        try:
            return self.collection.count_documents({"room_id": room_id})
        except Exception:
            return 0

    def get_invalid_actions(self, room_id: str) -> List[GameAction]:
        """
        Get all invalid actions for a room (anti-cheat analysis).

        Args:
            room_id: Room ID

        Returns:
            List of invalid GameActions
        """
        try:
            cursor = self.collection.find({"room_id": room_id, "is_valid": False})
            return [GameAction.from_dict(doc) for doc in cursor]
        except Exception as e:
            print(f"Error getting invalid actions: {e}")
            return []
