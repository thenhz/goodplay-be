from typing import Optional, List, Dict, Any
from bson import ObjectId
from pymongo import ASCENDING, DESCENDING

from app.core.repositories.base_repository import BaseRepository
from ..models.game_session import GameSession

class GameSessionRepository(BaseRepository):
    """Repository for GameSession collection operations"""

    def __init__(self):
        super().__init__("game_sessions")

    def create_indexes(self):
        """Create indexes for the game_sessions collection"""
        self.collection.create_index([("session_id", ASCENDING)], unique=True)
        self.collection.create_index([("user_id", ASCENDING)])
        self.collection.create_index([("game_id", ASCENDING)])
        self.collection.create_index([("status", ASCENDING)])
        self.collection.create_index([("user_id", ASCENDING), ("status", ASCENDING)])
        self.collection.create_index([("started_at", DESCENDING)])
        self.collection.create_index([("ended_at", DESCENDING)])

    def create_session(self, session: GameSession) -> Optional[str]:
        """
        Create a new game session in the database.

        Args:
            session: GameSession instance to create

        Returns:
            Optional[str]: Session document ID if successful, None otherwise
        """
        try:
            session_data = session.to_dict()
            session_data.pop("_id", None)  # Remove _id if present

            result = self.collection.insert_one(session_data)
            return str(result.inserted_id)
        except Exception:
            return None

    def get_session_by_id(self, session_doc_id: str) -> Optional[GameSession]:
        """
        Get a session by its document ID.

        Args:
            session_doc_id: The session document ID

        Returns:
            Optional[GameSession]: GameSession instance if found, None otherwise
        """
        session_data = self.find_by_id(session_doc_id)
        if session_data:
            return GameSession.from_dict(session_data)
        return None

    def get_session_by_session_id(self, session_id: str) -> Optional[GameSession]:
        """
        Get a session by its session ID.

        Args:
            session_id: The session ID

        Returns:
            Optional[GameSession]: GameSession instance if found, None otherwise
        """
        session_data = self.find_one({"session_id": session_id})
        if session_data:
            return GameSession.from_dict(session_data)
        return None

    def get_user_sessions(self, user_id: str, status: str = None,
                         limit: int = None, skip: int = None) -> List[GameSession]:
        """
        Get sessions for a specific user.

        Args:
            user_id: The user ID
            status: Optional status filter (active, paused, completed, abandoned)
            limit: Maximum number of sessions to return
            skip: Number of sessions to skip

        Returns:
            List[GameSession]: List of user sessions
        """
        filter_dict = {"user_id": user_id}
        if status:
            filter_dict["status"] = status

        sessions_data = self.find_many(
            filter_dict,
            limit=limit,
            skip=skip,
            sort=[("started_at", DESCENDING)]
        )
        return [GameSession.from_dict(data) for data in sessions_data]

    def get_game_sessions(self, game_id: str, status: str = None,
                         limit: int = None, skip: int = None) -> List[GameSession]:
        """
        Get sessions for a specific game.

        Args:
            game_id: The game ID
            status: Optional status filter
            limit: Maximum number of sessions to return
            skip: Number of sessions to skip

        Returns:
            List[GameSession]: List of game sessions
        """
        filter_dict = {"game_id": game_id}
        if status:
            filter_dict["status"] = status

        sessions_data = self.find_many(
            filter_dict,
            limit=limit,
            skip=skip,
            sort=[("started_at", DESCENDING)]
        )
        return [GameSession.from_dict(data) for data in sessions_data]

    def get_active_user_session(self, user_id: str, game_id: str = None) -> Optional[GameSession]:
        """
        Get an active session for a user.

        Args:
            user_id: The user ID
            game_id: Optional game ID filter

        Returns:
            Optional[GameSession]: Active session if found, None otherwise
        """
        filter_dict = {
            "user_id": user_id,
            "status": {"$in": ["active", "paused"]}
        }
        if game_id:
            filter_dict["game_id"] = game_id

        session_data = self.find_one(filter_dict)
        if session_data:
            return GameSession.from_dict(session_data)
        return None

    def update_session(self, session_id: str, session: GameSession) -> bool:
        """
        Update a session.

        Args:
            session_id: The session ID (session_id field, not document _id)
            session: Updated session instance

        Returns:
            bool: True if successful, False otherwise
        """
        session_data = session.to_dict()
        session_data.pop("_id", None)  # Remove _id
        session_data.pop("session_id", None)  # Don't update session_id
        session_data.pop("started_at", None)  # Don't update started_at

        return self.update_one({"session_id": session_id}, session_data)

    def update_session_state(self, session_id: str, new_state: Dict[str, Any]) -> bool:
        """
        Update the current state of a session.

        Args:
            session_id: The session ID
            new_state: The new state data

        Returns:
            bool: True if successful, False otherwise
        """
        update_data = {"current_state": new_state}
        return self.update_one({"session_id": session_id}, update_data)

    def update_session_score(self, session_id: str, new_score: int) -> bool:
        """
        Update the score of a session.

        Args:
            session_id: The session ID
            new_score: The new score

        Returns:
            bool: True if successful, False otherwise
        """
        update_data = {"score": new_score}
        return self.update_one({"session_id": session_id}, update_data)

    def add_session_move(self, session_id: str, move: Dict[str, Any]) -> bool:
        """
        Add a move to a session.

        Args:
            session_id: The session ID
            move: The move data

        Returns:
            bool: True if successful, False otherwise
        """
        if not ObjectId.is_valid(session_id) and not self.find_one({"session_id": session_id}):
            return False

        move_with_timestamp = {
            **move,
            "timestamp": self._get_current_time(),
        }

        result = self.collection.update_one(
            {"session_id": session_id},
            {"$push": {"moves": move_with_timestamp}}
        )
        return result.modified_count > 0

    def complete_session(self, session_id: str, final_score: int = None,
                        credits_earned: int = None, achievements: List[str] = None) -> bool:
        """
        Complete a session.

        Args:
            session_id: The session ID
            final_score: Optional final score
            credits_earned: Optional credits earned
            achievements: Optional list of achievements unlocked

        Returns:
            bool: True if successful, False otherwise
        """
        update_data = {
            "status": "completed",
            "ended_at": self._get_current_time()
        }

        if final_score is not None:
            update_data["score"] = final_score

        if credits_earned is not None:
            update_data["credits_earned"] = credits_earned

        if achievements:
            update_data["achievements_unlocked"] = achievements

        return self.update_one({"session_id": session_id}, update_data)

    def abandon_session(self, session_id: str) -> bool:
        """
        Abandon a session.

        Args:
            session_id: The session ID

        Returns:
            bool: True if successful, False otherwise
        """
        update_data = {
            "status": "abandoned",
            "ended_at": self._get_current_time()
        }
        return self.update_one({"session_id": session_id}, update_data)

    def pause_session(self, session_id: str) -> bool:
        """
        Pause a session.

        Args:
            session_id: The session ID

        Returns:
            bool: True if successful, False otherwise
        """
        return self.update_one({"session_id": session_id}, {"status": "paused"})

    def resume_session(self, session_id: str) -> bool:
        """
        Resume a paused session.

        Args:
            session_id: The session ID

        Returns:
            bool: True if successful, False otherwise
        """
        return self.update_one({"session_id": session_id}, {"status": "active"})

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.

        Args:
            session_id: The session ID

        Returns:
            bool: True if successful, False otherwise
        """
        return self.delete_one({"session_id": session_id})

    def get_user_session_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Get session statistics for a user.

        Args:
            user_id: The user ID

        Returns:
            Dict[str, Any]: User session statistics
        """
        pipeline = [
            {"$match": {"user_id": user_id}},
            {
                "$group": {
                    "_id": "$status",
                    "count": {"$sum": 1},
                    "total_score": {"$sum": "$score"},
                    "total_credits": {"$sum": "$credits_earned"}
                }
            }
        ]

        stats_by_status = {doc["_id"]: doc for doc in self.collection.aggregate(pipeline)}

        total_sessions = self.count({"user_id": user_id})
        completed_sessions = stats_by_status.get("completed", {}).get("count", 0)
        total_score = sum(stats.get("total_score", 0) for stats in stats_by_status.values())
        total_credits = sum(stats.get("total_credits", 0) for stats in stats_by_status.values())

        return {
            "total_sessions": total_sessions,
            "completed_sessions": completed_sessions,
            "completion_rate": (completed_sessions / total_sessions * 100) if total_sessions > 0 else 0,
            "total_score": total_score or 0,
            "total_credits_earned": total_credits or 0,
            "stats_by_status": stats_by_status
        }

    def get_game_session_stats(self, game_id: str) -> Dict[str, Any]:
        """
        Get session statistics for a game.

        Args:
            game_id: The game ID

        Returns:
            Dict[str, Any]: Game session statistics
        """
        pipeline = [
            {"$match": {"game_id": game_id}},
            {
                "$group": {
                    "_id": None,
                    "total_sessions": {"$sum": 1},
                    "completed_sessions": {
                        "$sum": {"$cond": [{"$eq": ["$status", "completed"]}, 1, 0]}
                    },
                    "avg_score": {"$avg": "$score"},
                    "max_score": {"$max": "$score"},
                    "total_playtime": {
                        "$sum": {
                            "$divide": [
                                {"$subtract": [
                                    {"$ifNull": ["$ended_at", "$$NOW"]},
                                    "$started_at"
                                ]},
                                1000  # Convert to seconds
                            ]
                        }
                    }
                }
            }
        ]

        result = list(self.collection.aggregate(pipeline))
        if result:
            stats = result[0]
            return {
                "total_sessions": stats.get("total_sessions", 0),
                "completed_sessions": stats.get("completed_sessions", 0),
                "completion_rate": (stats.get("completed_sessions", 0) / stats.get("total_sessions", 1) * 100),
                "average_score": round(stats.get("avg_score", 0), 2) if stats.get("avg_score") else 0,
                "highest_score": stats.get("max_score", 0),
                "total_playtime_seconds": int(stats.get("total_playtime", 0))
            }

        return {
            "total_sessions": 0,
            "completed_sessions": 0,
            "completion_rate": 0,
            "average_score": 0,
            "highest_score": 0,
            "total_playtime_seconds": 0
        }

    def get_recent_sessions_by_game(self, game_id: str, days: int = 7, limit: int = 100) -> List[GameSession]:
        """
        Get recent sessions for a specific game.

        Args:
            game_id: The game ID
            days: Number of days to look back
            limit: Maximum number of sessions to return

        Returns:
            List[GameSession]: List of recent game sessions
        """
        from datetime import datetime, timedelta

        since_date = datetime.utcnow() - timedelta(days=days)
        sessions_data = self.find_many(
            {
                "game_id": game_id,
                "created_at": {"$gte": since_date}
            },
            limit=limit,
            sort=[("created_at", -1)]
        )

        return [GameSession.from_dict(data) for data in sessions_data]