from typing import Optional, List, Dict, Any
from bson import ObjectId
from app.core.repositories.base_repository import BaseRepository
from ..models.achievement import Achievement
from ..models.user_achievement import UserAchievement
from ..models.badge import Badge


class AchievementRepository(BaseRepository):
    """Repository for achievement system data access"""

    def __init__(self):
        super().__init__('achievements')
        self.user_achievements_collection = self.db['user_achievements']
        self.user_badges_collection = self.db['user_badges']

    def create_indexes(self):
        """Create database indexes for optimal performance"""
        try:
            # Achievement indexes
            self.collection.create_index("achievement_id", unique=True)
            self.collection.create_index("category")
            self.collection.create_index("is_active")
            self.collection.create_index([("category", 1), ("is_active", 1)])

            # User achievement indexes
            self.user_achievements_collection.create_index([("user_id", 1), ("achievement_id", 1)], unique=True)
            self.user_achievements_collection.create_index("user_id")
            self.user_achievements_collection.create_index("achievement_id")
            self.user_achievements_collection.create_index("is_completed")
            self.user_achievements_collection.create_index("reward_claimed")
            self.user_achievements_collection.create_index([("user_id", 1), ("is_completed", 1)])

            # User badge indexes
            self.user_badges_collection.create_index("user_id")
            self.user_badges_collection.create_index("achievement_id")
            self.user_badges_collection.create_index("rarity")
            self.user_badges_collection.create_index("is_visible")
            self.user_badges_collection.create_index([("user_id", 1), ("is_visible", 1)])

        except Exception as e:
            print(f"Error creating achievement indexes: {str(e)}")

    # Achievement methods
    def create_achievement(self, achievement: Achievement) -> str:
        """Create a new achievement"""
        return self.create(achievement.to_dict())

    def find_achievement_by_id(self, achievement_id: str) -> Optional[Achievement]:
        """Find achievement by achievement_id"""
        data = self.find_one({"achievement_id": achievement_id})
        if data:
            return Achievement.from_dict(data)
        return None

    def find_active_achievements(self) -> List[Achievement]:
        """Find all active achievements"""
        data_list = self.find_many({"is_active": True}, sort=[("category", 1), ("name", 1)])
        return [Achievement.from_dict(data) for data in data_list]

    def find_achievements_by_category(self, category: str) -> List[Achievement]:
        """Find achievements by category"""
        data_list = self.find_many(
            {"category": category, "is_active": True},
            sort=[("name", 1)]
        )
        return [Achievement.from_dict(data) for data in data_list]

    def update_achievement(self, achievement_id: str, updates: Dict[str, Any]) -> bool:
        """Update achievement by achievement_id"""
        return self.update_one({"achievement_id": achievement_id}, updates)

    def deactivate_achievement(self, achievement_id: str) -> bool:
        """Deactivate an achievement"""
        return self.update_one({"achievement_id": achievement_id}, {"is_active": False})

    # UserAchievement methods
    def create_user_achievement(self, user_achievement: UserAchievement) -> str:
        """Create a new user achievement"""
        result = self.user_achievements_collection.insert_one(user_achievement.to_dict())
        return str(result.inserted_id)

    def find_user_achievement(self, user_id: str, achievement_id: str) -> Optional[UserAchievement]:
        """Find user achievement by user_id and achievement_id"""
        data = self.user_achievements_collection.find_one({
            "user_id": ObjectId(user_id),
            "achievement_id": achievement_id
        })
        if data:
            return UserAchievement.from_dict(data)
        return None

    def find_user_achievements(self, user_id: str, completed_only: bool = False) -> List[UserAchievement]:
        """Find all user achievements"""
        filter_dict = {"user_id": ObjectId(user_id)}
        if completed_only:
            filter_dict["is_completed"] = True

        data_list = self.user_achievements_collection.find(filter_dict).sort("updated_at", -1)
        return [UserAchievement.from_dict(data) for data in data_list]

    def find_unclaimed_achievements(self, user_id: str) -> List[UserAchievement]:
        """Find completed but unclaimed achievements"""
        data_list = self.user_achievements_collection.find({
            "user_id": ObjectId(user_id),
            "is_completed": True,
            "reward_claimed": False
        }).sort("completed_at", 1)
        return [UserAchievement.from_dict(data) for data in data_list]

    def update_user_achievement(self, user_id: str, achievement_id: str,
                               updates: Dict[str, Any]) -> bool:
        """Update user achievement"""
        result = self.user_achievements_collection.update_one(
            {
                "user_id": ObjectId(user_id),
                "achievement_id": achievement_id
            },
            {"$set": updates}
        )
        return result.modified_count > 0

    def increment_user_progress(self, user_id: str, achievement_id: str,
                               increment: int = 1) -> Optional[UserAchievement]:
        """Increment user achievement progress"""
        result = self.user_achievements_collection.find_one_and_update(
            {
                "user_id": ObjectId(user_id),
                "achievement_id": achievement_id
            },
            {
                "$inc": {"progress": increment},
                "$set": {"updated_at": self._get_current_time()}
            },
            return_document=True
        )
        if result:
            return UserAchievement.from_dict(result)
        return None

    def set_user_progress(self, user_id: str, achievement_id: str,
                         progress: int) -> Optional[UserAchievement]:
        """Set user achievement progress to specific value"""
        result = self.user_achievements_collection.find_one_and_update(
            {
                "user_id": ObjectId(user_id),
                "achievement_id": achievement_id
            },
            {
                "$set": {
                    "progress": progress,
                    "updated_at": self._get_current_time()
                }
            },
            return_document=True
        )
        if result:
            return UserAchievement.from_dict(result)
        return None

    def complete_user_achievement(self, user_id: str, achievement_id: str) -> bool:
        """Mark user achievement as completed"""
        current_time = self._get_current_time()
        result = self.user_achievements_collection.update_one(
            {
                "user_id": ObjectId(user_id),
                "achievement_id": achievement_id
            },
            {
                "$set": {
                    "is_completed": True,
                    "completed_at": current_time,
                    "updated_at": current_time
                }
            }
        )
        return result.modified_count > 0

    def claim_achievement_reward(self, user_id: str, achievement_id: str) -> bool:
        """Mark achievement reward as claimed"""
        current_time = self._get_current_time()
        result = self.user_achievements_collection.update_one(
            {
                "user_id": ObjectId(user_id),
                "achievement_id": achievement_id,
                "is_completed": True,
                "reward_claimed": False
            },
            {
                "$set": {
                    "reward_claimed": True,
                    "claimed_at": current_time,
                    "updated_at": current_time
                }
            }
        )
        return result.modified_count > 0

    # Badge methods
    def create_badge(self, badge: Badge) -> str:
        """Create a new badge"""
        result = self.user_badges_collection.insert_one(badge.to_dict())
        return str(result.inserted_id)

    def find_user_badges(self, user_id: str, visible_only: bool = False) -> List[Badge]:
        """Find all user badges"""
        filter_dict = {"user_id": ObjectId(user_id)}
        if visible_only:
            filter_dict["is_visible"] = True

        data_list = self.user_badges_collection.find(filter_dict).sort("earned_at", -1)
        return [Badge.from_dict(data) for data in data_list]

    def find_user_badges_by_rarity(self, user_id: str, rarity: str) -> List[Badge]:
        """Find user badges by rarity"""
        data_list = self.user_badges_collection.find({
            "user_id": ObjectId(user_id),
            "rarity": rarity
        }).sort("earned_at", -1)
        return [Badge.from_dict(data) for data in data_list]

    def count_user_badges_by_rarity(self, user_id: str) -> Dict[str, int]:
        """Count user badges by rarity"""
        pipeline = [
            {"$match": {"user_id": ObjectId(user_id)}},
            {"$group": {"_id": "$rarity", "count": {"$sum": 1}}}
        ]
        results = list(self.user_badges_collection.aggregate(pipeline))

        counts = {rarity: 0 for rarity in Badge.VALID_RARITIES}
        for result in results:
            counts[result["_id"]] = result["count"]

        return counts

    def update_badge_visibility(self, user_id: str, badge_id: str, visible: bool) -> bool:
        """Update badge visibility"""
        result = self.user_badges_collection.update_one(
            {
                "_id": ObjectId(badge_id),
                "user_id": ObjectId(user_id)
            },
            {"$set": {"is_visible": visible}}
        )
        return result.modified_count > 0

    # Statistics methods
    def get_user_achievement_stats(self, user_id: str) -> Dict[str, Any]:
        """Get user achievement statistics"""
        pipeline = [
            {"$match": {"user_id": ObjectId(user_id)}},
            {
                "$group": {
                    "_id": None,
                    "total_achievements": {"$sum": 1},
                    "completed_achievements": {
                        "$sum": {"$cond": [{"$eq": ["$is_completed", True]}, 1, 0]}
                    },
                    "claimed_rewards": {
                        "$sum": {"$cond": [{"$eq": ["$reward_claimed", True]}, 1, 0]}
                    },
                    "total_progress": {"$sum": "$progress"}
                }
            }
        ]
        result = list(self.user_achievements_collection.aggregate(pipeline))

        if result:
            stats = result[0]
            del stats["_id"]
            stats["completion_rate"] = (
                stats["completed_achievements"] / stats["total_achievements"] * 100
                if stats["total_achievements"] > 0 else 0
            )
            return stats

        return {
            "total_achievements": 0,
            "completed_achievements": 0,
            "claimed_rewards": 0,
            "total_progress": 0,
            "completion_rate": 0
        }

    def get_leaderboard(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get achievement leaderboard"""
        pipeline = [
            {
                "$group": {
                    "_id": "$user_id",
                    "completed_achievements": {
                        "$sum": {"$cond": [{"$eq": ["$is_completed", True]}, 1, 0]}
                    },
                    "total_progress": {"$sum": "$progress"}
                }
            },
            {"$sort": {"completed_achievements": -1, "total_progress": -1}},
            {"$limit": limit}
        ]
        results = list(self.user_achievements_collection.aggregate(pipeline))

        leaderboard = []
        for i, result in enumerate(results):
            leaderboard.append({
                "rank": i + 1,
                "user_id": str(result["_id"]),
                "completed_achievements": result["completed_achievements"],
                "total_progress": result["total_progress"]
            })

        return leaderboard