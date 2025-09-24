from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from bson import ObjectId
from app.core.repositories.base_repository import BaseRepository
from app.social.challenges.models.social_challenge import SocialChallenge

class SocialChallengeRepository(BaseRepository):
    """Repository for social challenge data operations"""

    def __init__(self):
        super().__init__("social_challenges")
        self.create_indexes()

    def create_indexes(self):
        """Create database indexes for optimal query performance"""
        if self.collection is None:
            return

        # Compound indexes for common queries
        self.collection.create_index([
            ("creator_id", 1),
            ("status", 1),
            ("created_at", -1)
        ])

        self.collection.create_index([
            ("status", 1),
            ("is_public", 1),
            ("friends_only", 1)
        ])

        self.collection.create_index([
            ("challenge_type", 1),
            ("challenge_category", 1)
        ])

        self.collection.create_index([
            ("participant_ids", 1),
            ("status", 1)
        ])

        self.collection.create_index([
            ("start_date", 1),
            ("end_date", 1)
        ])

        # Text index for search functionality
        self.collection.create_index([
            ("title", "text"),
            ("description", "text"),
            ("tags", "text")
        ])

        # Unique constraint on challenge_id
        self.collection.create_index("challenge_id", unique=True)

    def create_challenge(self, challenge: SocialChallenge) -> Optional[str]:
        """Create a new social challenge"""
        try:
            challenge_data = challenge.to_dict()
            result = self.collection.insert_one(challenge_data)
            return str(result.inserted_id)
        except Exception as e:
            print(f"Error creating challenge: {str(e)}")
            return None

    def get_by_challenge_id(self, challenge_id: str) -> Optional[SocialChallenge]:
        """Get challenge by challenge_id"""
        data = self.find_one({"challenge_id": challenge_id})
        if data:
            return SocialChallenge.from_dict(data)
        return None

    def get_by_id(self, id: str) -> Optional[SocialChallenge]:
        """Get challenge by MongoDB ObjectId"""
        data = self.find_by_id(id)
        if data:
            return SocialChallenge.from_dict(data)
        return None

    def update_challenge(self, challenge_id: str, updates: Dict[str, Any]) -> bool:
        """Update challenge by challenge_id"""
        updates["updated_at"] = datetime.utcnow()
        return self.update_one({"challenge_id": challenge_id}, updates)

    def update_by_id(self, id: str, updates: Dict[str, Any]) -> bool:
        """Update challenge by MongoDB ObjectId"""
        updates["updated_at"] = datetime.utcnow()
        return super().update_by_id(id, updates)

    def delete_challenge(self, challenge_id: str) -> bool:
        """Delete challenge by challenge_id"""
        return self.delete_one({"challenge_id": challenge_id})

    # Query methods for challenges
    def get_challenges_by_user(self, user_id: str, include_completed: bool = False,
                              limit: int = 20, offset: int = 0) -> List[SocialChallenge]:
        """Get challenges where user is creator or participant"""
        query_filters = {
            "$or": [
                {"creator_id": user_id},
                {"participant_ids": user_id}
            ]
        }

        if not include_completed:
            query_filters["status"] = {"$nin": ["completed", "cancelled"]}

        data_list = self.find_many(
            filter_dict=query_filters,
            sort=[("created_at", -1)],
            limit=limit,
            skip=offset
        )

        return [SocialChallenge.from_dict(data) for data in data_list]

    def get_public_challenges(self, challenge_type: str = None,
                            limit: int = 20, offset: int = 0) -> List[SocialChallenge]:
        """Get public challenges available for joining"""
        query_filters = {
            "is_public": True,
            "status": "open",
            "end_date": {"$gt": datetime.utcnow()}
        }

        if challenge_type:
            query_filters["challenge_type"] = challenge_type

        data_list = self.find_many(
            filter_dict=query_filters,
            sort=[("created_at", -1)],
            limit=limit,
            skip=offset
        )

        return [SocialChallenge.from_dict(data) for data in data_list]

    def get_friend_challenges(self, user_id: str, friend_ids: List[str],
                            limit: int = 20, offset: int = 0) -> List[SocialChallenge]:
        """Get challenges created by friends that user can join"""
        query_filters = {
            "creator_id": {"$in": friend_ids},
            "status": "open",
            "participant_ids": {"$ne": user_id},  # Not already joined
            "friends_only": True,
            "end_date": {"$gt": datetime.utcnow()}
        }

        data_list = self.find_many(
            filter_dict=query_filters,
            sort=[("created_at", -1)],
            limit=limit,
            skip=offset
        )

        return [SocialChallenge.from_dict(data) for data in data_list]

    def get_challenges_by_category(self, category: str, limit: int = 20,
                                 offset: int = 0) -> List[SocialChallenge]:
        """Get challenges by category"""
        query_filters = {
            "challenge_category": category,
            "status": {"$in": ["open", "active"]},
            "end_date": {"$gt": datetime.utcnow()}
        }

        data_list = self.find_many(
            filter_dict=query_filters,
            sort=[("created_at", -1)],
            limit=limit,
            skip=offset
        )

        return [SocialChallenge.from_dict(data) for data in data_list]

    def search_challenges(self, query: str, filters: Dict[str, Any] = None,
                         limit: int = 20, offset: int = 0) -> List[SocialChallenge]:
        """Search challenges by text query"""
        search_filters = {"$text": {"$search": query}}

        if filters:
            search_filters.update(filters)

        # Only active/open challenges by default
        if "status" not in search_filters:
            search_filters["status"] = {"$in": ["open", "active"]}

        if "end_date" not in search_filters:
            search_filters["end_date"] = {"$gt": datetime.utcnow()}

        data_list = self.find_many(
            filter_dict=search_filters,
            sort=[("score", {"$meta": "textScore"}), ("created_at", -1)],
            limit=limit,
            skip=offset
        )

        return [SocialChallenge.from_dict(data) for data in data_list]

    def get_active_challenges(self, limit: int = 50, offset: int = 0) -> List[SocialChallenge]:
        """Get all active challenges"""
        query_filters = {
            "status": "active",
            "end_date": {"$gt": datetime.utcnow()}
        }

        data_list = self.find_many(
            filter_dict=query_filters,
            sort=[("start_date", -1)],
            limit=limit,
            skip=offset
        )

        return [SocialChallenge.from_dict(data) for data in data_list]

    def get_expired_challenges(self, limit: int = 100) -> List[SocialChallenge]:
        """Get challenges that have expired but status not updated"""
        query_filters = {
            "status": {"$in": ["open", "active"]},
            "end_date": {"$lt": datetime.utcnow()}
        }

        data_list = self.find_many(
            filter_dict=query_filters,
            sort=[("end_date", 1)],
            limit=limit
        )

        return [SocialChallenge.from_dict(data) for data in data_list]

    def get_challenges_ending_soon(self, hours: int = 24) -> List[SocialChallenge]:
        """Get challenges ending within specified hours"""
        end_time = datetime.utcnow() + timedelta(hours=hours)
        query_filters = {
            "status": {"$in": ["open", "active"]},
            "end_date": {"$lt": end_time, "$gt": datetime.utcnow()}
        }

        data_list = self.find_many(
            filter_dict=query_filters,
            sort=[("end_date", 1)]
        )

        return [SocialChallenge.from_dict(data) for data in data_list]

    # Participant management
    def add_participant(self, challenge_id: str, user_id: str) -> bool:
        """Add participant to challenge"""
        return self.update_one(
            {"challenge_id": challenge_id},
            {"$addToSet": {"participant_ids": user_id}}
        )

    def remove_participant(self, challenge_id: str, user_id: str) -> bool:
        """Remove participant from challenge"""
        return self.update_one(
            {"challenge_id": challenge_id},
            {"$pull": {"participant_ids": user_id}}
        )

    def add_invited_user(self, challenge_id: str, user_id: str) -> bool:
        """Add user to invited list"""
        return self.update_one(
            {"challenge_id": challenge_id},
            {"$addToSet": {"invited_user_ids": user_id}}
        )

    def remove_invited_user(self, challenge_id: str, user_id: str) -> bool:
        """Remove user from invited list (when they join or decline)"""
        return self.update_one(
            {"challenge_id": challenge_id},
            {"$pull": {"invited_user_ids": user_id}}
        )

    # Progress and leaderboard updates
    def update_leaderboard(self, challenge_id: str,
                          leaderboard_data: List[Dict[str, Any]]) -> bool:
        """Update challenge leaderboard data"""
        return self.update_one(
            {"challenge_id": challenge_id},
            {"leaderboard_data": leaderboard_data}
        )

    def update_completion_percentage(self, challenge_id: str, percentage: float) -> bool:
        """Update challenge completion percentage"""
        return self.update_one(
            {"challenge_id": challenge_id},
            {"completion_percentage": min(100.0, max(0.0, percentage))}
        )

    # Statistics and analytics
    def get_challenge_stats_by_creator(self, creator_id: str) -> Dict[str, Any]:
        """Get statistics for challenges created by user"""
        pipeline = [
            {"$match": {"creator_id": creator_id}},
            {
                "$group": {
                    "_id": "$status",
                    "count": {"$sum": 1},
                    "total_participants": {"$sum": "$current_participants"}
                }
            }
        ]

        results = list(self.collection.aggregate(pipeline))

        stats = {
            "total_created": 0,
            "active": 0,
            "completed": 0,
            "cancelled": 0,
            "total_participants": 0
        }

        for result in results:
            status = result["_id"]
            count = result["count"]
            participants = result["total_participants"]

            stats["total_created"] += count
            stats["total_participants"] += participants

            if status in stats:
                stats[status] = count

        return stats

    def get_popular_categories(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most popular challenge categories"""
        pipeline = [
            {"$match": {"status": {"$in": ["open", "active", "completed"]}}},
            {
                "$group": {
                    "_id": "$challenge_category",
                    "count": {"$sum": 1},
                    "total_participants": {"$sum": "$current_participants"},
                    "avg_participants": {"$avg": "$current_participants"}
                }
            },
            {"$sort": {"count": -1}},
            {"$limit": limit}
        ]

        return list(self.collection.aggregate(pipeline))

    def get_user_participation_count(self, user_id: str) -> int:
        """Get count of challenges user is participating in"""
        return self.count({"participant_ids": user_id, "status": {"$in": ["open", "active"]}})

    def bulk_update_status(self, challenge_ids: List[str], new_status: str) -> int:
        """Bulk update status for multiple challenges"""
        result = self.collection.update_many(
            {"challenge_id": {"$in": challenge_ids}},
            {"$set": {"status": new_status, "updated_at": datetime.utcnow()}}
        )
        return result.modified_count