from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from app.core.repositories.base_repository import BaseRepository
from ..models.challenge import Challenge

class ChallengeRepository(BaseRepository):
    """Repository for challenge operations"""

    def __init__(self):
        super().__init__("challenges")

    def create_challenge(self, challenge: Challenge) -> str:
        """Create a new challenge"""
        return self.create(challenge.to_dict())

    def get_challenge_by_id(self, challenge_id: str) -> Optional[Challenge]:
        """Get a challenge by ID"""
        data = self.find_by_id(challenge_id)
        return Challenge.from_dict(data) if data else None

    def get_challenge_by_challenge_id(self, challenge_id: str) -> Optional[Challenge]:
        """Get a challenge by challenge_id field"""
        data = self.find_one({"challenge_id": challenge_id})
        return Challenge.from_dict(data) if data else None

    def get_challenges_by_user(self, user_id: str, status: str = None, limit: int = 50) -> List[Challenge]:
        """Get challenges involving a specific user"""
        filter_dict = {
            "$or": [
                {"challenger_id": user_id},
                {"challenged_ids": {"$in": [user_id]}}
            ]
        }

        if status:
            filter_dict["status"] = status

        challenges_data = self.find_many(filter_dict, limit=limit, sort=[("created_at", -1)])
        return [Challenge.from_dict(data) for data in challenges_data]

    def get_pending_challenges_for_user(self, user_id: str) -> List[Challenge]:
        """Get pending challenges for a user"""
        challenges_data = self.find_many({
            "challenged_ids": {"$in": [user_id]},
            "status": "pending"
        }, sort=[("created_at", -1)])
        return [Challenge.from_dict(data) for data in challenges_data]

    def get_active_challenges_for_user(self, user_id: str) -> List[Challenge]:
        """Get active challenges for a user"""
        challenges_data = self.find_many({
            "$or": [
                {"challenger_id": user_id},
                {"challenged_ids": {"$in": [user_id]}}
            ],
            "status": "active"
        }, sort=[("started_at", -1)])
        return [Challenge.from_dict(data) for data in challenges_data]

    def get_public_challenges(self, game_id: str = None, status: str = "pending", limit: int = 20) -> List[Challenge]:
        """Get public challenges that users can join"""
        filter_dict = {
            "is_public": True,
            "status": status
        }

        if game_id:
            filter_dict["game_id"] = game_id

        challenges_data = self.find_many(filter_dict, limit=limit, sort=[("created_at", -1)])
        return [Challenge.from_dict(data) for data in challenges_data]

    def get_challenges_by_game(self, game_id: str, limit: int = 50) -> List[Challenge]:
        """Get challenges for a specific game"""
        challenges_data = self.find_many(
            {"game_id": game_id},
            limit=limit,
            sort=[("created_at", -1)]
        )
        return [Challenge.from_dict(data) for data in challenges_data]

    def get_challenges_by_status(self, status: str, limit: int = 100) -> List[Challenge]:
        """Get challenges by status"""
        challenges_data = self.find_many(
            {"status": status},
            limit=limit,
            sort=[("created_at", -1)]
        )
        return [Challenge.from_dict(data) for data in challenges_data]

    def get_expired_challenges(self) -> List[Challenge]:
        """Get challenges that have expired"""
        now = datetime.utcnow()
        challenges_data = self.find_many({
            "status": {"$in": ["pending", "active"]},
            "expires_at": {"$lt": now}
        })
        return [Challenge.from_dict(data) for data in challenges_data]

    def update_challenge_status(self, challenge_id: str, status: str, additional_data: Dict[str, Any] = None) -> bool:
        """Update challenge status"""
        update_data = {
            "status": status,
            "updated_at": datetime.utcnow()
        }

        if additional_data:
            update_data.update(additional_data)

        result = self.collection.update_one(
            {"challenge_id": challenge_id},
            {"$set": update_data}
        )
        return result.modified_count > 0

    def add_participant_to_challenge(self, challenge_id: str, user_id: str) -> bool:
        """Add a participant to a challenge"""
        result = self.collection.update_one(
            {
                "challenge_id": challenge_id,
                "challenged_ids": {"$ne": user_id},  # Don't add if already present
                "challenger_id": {"$ne": user_id}    # Don't add challenger again
            },
            {
                "$addToSet": {"challenged_ids": user_id},
                "$inc": {"total_participants": 1},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        return result.modified_count > 0

    def remove_participant_from_challenge(self, challenge_id: str, user_id: str) -> bool:
        """Remove a participant from a challenge"""
        result = self.collection.update_one(
            {"challenge_id": challenge_id},
            {
                "$pull": {"challenged_ids": user_id},
                "$inc": {"total_participants": -1},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        return result.modified_count > 0

    def add_challenge_result(self, challenge_id: str, user_id: str, score: int,
                           additional_data: Dict[str, Any] = None) -> bool:
        """Add or update a result for a challenge participant"""
        # Remove existing result for this user
        self.collection.update_one(
            {"challenge_id": challenge_id},
            {"$pull": {"results": {"user_id": user_id}}}
        )

        # Add new result
        result_data = {
            "user_id": user_id,
            "score": score,
            "completed_at": datetime.utcnow(),
            **(additional_data or {})
        }

        update_result = self.collection.update_one(
            {"challenge_id": challenge_id},
            {
                "$push": {"results": result_data},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        return update_result.modified_count > 0

    def complete_challenge(self, challenge_id: str, winner_ids: List[str] = None) -> bool:
        """Mark challenge as completed"""
        update_data = {
            "status": "completed",
            "completed_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        if winner_ids:
            update_data["winner_ids"] = winner_ids

        result = self.collection.update_one(
            {"challenge_id": challenge_id},
            {"$set": update_data}
        )
        return result.modified_count > 0

    def expire_old_challenges(self, hours_old: int = 24) -> int:
        """Mark old expired challenges as expired"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_old)

        result = self.collection.update_many(
            {
                "status": {"$in": ["pending", "active"]},
                "$or": [
                    {"expires_at": {"$lt": datetime.utcnow()}},
                    {"created_at": {"$lt": cutoff_time}, "expires_at": {"$exists": False}}
                ]
            },
            {"$set": {
                "status": "expired",
                "completed_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }}
        )
        return result.modified_count

    def get_challenge_statistics(self, game_id: str = None, days_back: int = 30) -> Dict[str, Any]:
        """Get challenge statistics"""
        since_date = datetime.utcnow() - timedelta(days=days_back)

        filter_dict = {"created_at": {"$gte": since_date}}
        if game_id:
            filter_dict["game_id"] = game_id

        total_challenges = self.collection.count_documents(filter_dict)
        completed_challenges = self.collection.count_documents({**filter_dict, "status": "completed"})
        active_challenges = self.collection.count_documents({**filter_dict, "status": "active"})
        pending_challenges = self.collection.count_documents({**filter_dict, "status": "pending"})

        # Challenge type breakdown
        type_breakdown = list(self.collection.aggregate([
            {"$match": filter_dict},
            {"$group": {"_id": "$challenge_type", "count": {"$sum": 1}}}
        ]))

        return {
            "total_challenges": total_challenges,
            "completed_challenges": completed_challenges,
            "active_challenges": active_challenges,
            "pending_challenges": pending_challenges,
            "completion_rate": (completed_challenges / total_challenges * 100) if total_challenges > 0 else 0,
            "type_breakdown": {item["_id"]: item["count"] for item in type_breakdown},
            "days_analyzed": days_back
        }

    def get_user_challenge_history(self, user_id: str, limit: int = 50) -> List[Challenge]:
        """Get challenge history for a user"""
        challenges_data = self.find_many({
            "$or": [
                {"challenger_id": user_id},
                {"challenged_ids": {"$in": [user_id]}}
            ],
            "status": {"$in": ["completed", "cancelled", "expired"]}
        }, limit=limit, sort=[("completed_at", -1)])
        return [Challenge.from_dict(data) for data in challenges_data]

    def get_popular_games_for_challenges(self, days_back: int = 7, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most popular games for challenges"""
        since_date = datetime.utcnow() - timedelta(days=days_back)

        pipeline = [
            {"$match": {"created_at": {"$gte": since_date}}},
            {"$group": {
                "_id": "$game_id",
                "challenge_count": {"$sum": 1},
                "completed_count": {
                    "$sum": {"$cond": [{"$eq": ["$status", "completed"]}, 1, 0]}
                }
            }},
            {"$sort": {"challenge_count": -1}},
            {"$limit": limit}
        ]

        return list(self.collection.aggregate(pipeline))

    def find_matchmaking_candidates(self, user_id: str, game_id: str, challenge_type: str = "1v1") -> List[Challenge]:
        """Find challenges suitable for matchmaking"""
        filter_dict = {
            "game_id": game_id,
            "challenge_type": challenge_type,
            "status": "pending",
            "is_public": True,
            "challenger_id": {"$ne": user_id},  # Not created by this user
            "challenged_ids": {"$ne": user_id}, # User not already invited
            "expires_at": {"$gt": datetime.utcnow()}  # Not expired
        }

        # For NvN challenges, check if there's space
        if challenge_type == "NvN":
            # This would need a more complex query in MongoDB to check array size
            pass

        challenges_data = self.find_many(filter_dict, limit=10, sort=[("created_at", 1)])
        return [Challenge.from_dict(data) for data in challenges_data]

    def cleanup_old_challenges(self, days_old: int = 90) -> int:
        """Delete very old completed/cancelled challenges"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)

        result = self.collection.delete_many({
            "status": {"$in": ["completed", "cancelled", "expired"]},
            "completed_at": {"$lt": cutoff_date}
        })
        return result.deleted_count