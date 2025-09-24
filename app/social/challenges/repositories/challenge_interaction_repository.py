from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from bson import ObjectId
from app.core.repositories.base_repository import BaseRepository
from app.social.challenges.models.challenge_interaction import ChallengeInteraction

class ChallengeInteractionRepository(BaseRepository):
    """Repository for challenge interaction data operations"""

    def __init__(self):
        super().__init__("social_challenge_interactions")
        self.create_indexes()

    def create_indexes(self):
        """Create database indexes for optimal query performance"""
        if self.collection is None:
            return

        # Compound indexes for common queries
        self.collection.create_index([
            ("challenge_id", 1),
            ("created_at", -1)
        ])

        self.collection.create_index([
            ("from_user_id", 1),
            ("created_at", -1)
        ])

        self.collection.create_index([
            ("to_user_id", 1),
            ("interaction_type", 1),
            ("created_at", -1)
        ])

        self.collection.create_index([
            ("challenge_id", 1),
            ("interaction_type", 1),
            ("is_public", 1)
        ])

        # Moderation indexes
        self.collection.create_index([
            ("is_flagged", 1),
            ("moderation_status", 1)
        ])

        self.collection.create_index([
            ("is_deleted", 1),
            ("is_public", 1)
        ])

        # Context-based indexes
        self.collection.create_index([
            ("context_type", 1),
            ("challenge_id", 1)
        ])

        # Engagement indexes
        self.collection.create_index([
            ("likes_count", -1),
            ("interaction_type", 1)
        ])

    def create_interaction(self, interaction: ChallengeInteraction) -> Optional[str]:
        """Create a new challenge interaction"""
        try:
            interaction_data = interaction.to_dict()
            result = self.collection.insert_one(interaction_data)
            return str(result.inserted_id)
        except Exception as e:
            print(f"Error creating interaction: {str(e)}")
            return None

    def get_interaction_by_id(self, id: str) -> Optional[ChallengeInteraction]:
        """Get interaction by MongoDB ObjectId"""
        data = self.find_by_id(id)
        if data:
            return ChallengeInteraction.from_dict(data)
        return None

    def update_interaction(self, interaction_id: str, updates: Dict[str, Any]) -> bool:
        """Update interaction data"""
        updates["updated_at"] = datetime.utcnow()
        return self.update_by_id(interaction_id, updates)

    def delete_interaction(self, interaction_id: str) -> bool:
        """Delete interaction completely"""
        return self.delete_by_id(interaction_id)

    # Query methods for interactions
    def get_challenge_interactions(self, challenge_id: str,
                                 interaction_type: str = None,
                                 limit: int = 50, offset: int = 0) -> List[ChallengeInteraction]:
        """Get interactions for a challenge"""
        query_filters = {
            "challenge_id": challenge_id,
            "is_deleted": False,
            "is_public": True,
            "moderation_status": "approved"
        }

        if interaction_type:
            query_filters["interaction_type"] = interaction_type

        data_list = self.find_many(
            filter_dict=query_filters,
            sort=[("created_at", -1)],
            limit=limit,
            skip=offset
        )

        return [ChallengeInteraction.from_dict(data) for data in data_list]

    def get_user_interactions(self, user_id: str, interaction_type: str = None,
                            limit: int = 20, offset: int = 0) -> List[ChallengeInteraction]:
        """Get interactions by user"""
        query_filters = {
            "from_user_id": user_id,
            "is_deleted": False
        }

        if interaction_type:
            query_filters["interaction_type"] = interaction_type

        data_list = self.find_many(
            filter_dict=query_filters,
            sort=[("created_at", -1)],
            limit=limit,
            skip=offset
        )

        return [ChallengeInteraction.from_dict(data) for data in data_list]

    def get_interactions_for_user(self, user_id: str, interaction_type: str = None,
                                limit: int = 20, offset: int = 0) -> List[ChallengeInteraction]:
        """Get interactions targeting a user"""
        query_filters = {
            "to_user_id": user_id,
            "is_deleted": False,
            "is_public": True,
            "moderation_status": "approved"
        }

        if interaction_type:
            query_filters["interaction_type"] = interaction_type

        data_list = self.find_many(
            filter_dict=query_filters,
            sort=[("created_at", -1)],
            limit=limit,
            skip=offset
        )

        return [ChallengeInteraction.from_dict(data) for data in data_list]

    def get_challenge_activity_feed(self, challenge_id: str,
                                  limit: int = 50) -> List[ChallengeInteraction]:
        """Get activity feed for a challenge"""
        query_filters = {
            "challenge_id": challenge_id,
            "is_deleted": False,
            "is_public": True,
            "moderation_status": "approved"
        }

        data_list = self.find_many(
            filter_dict=query_filters,
            sort=[("created_at", -1)],
            limit=limit
        )

        return [ChallengeInteraction.from_dict(data) for data in data_list]

    def get_recent_interactions(self, hours: int = 24, limit: int = 100) -> List[ChallengeInteraction]:
        """Get recent interactions within specified hours"""
        since_time = datetime.utcnow() - timedelta(hours=hours)
        query_filters = {
            "created_at": {"$gte": since_time},
            "is_deleted": False,
            "is_public": True,
            "moderation_status": "approved"
        }

        data_list = self.find_many(
            filter_dict=query_filters,
            sort=[("created_at", -1)],
            limit=limit
        )

        return [ChallengeInteraction.from_dict(data) for data in data_list]

    # Interaction-specific methods
    def get_cheers_for_user(self, challenge_id: str, user_id: str) -> List[ChallengeInteraction]:
        """Get cheers received by user in a challenge"""
        query_filters = {
            "challenge_id": challenge_id,
            "to_user_id": user_id,
            "interaction_type": "cheer",
            "is_deleted": False,
            "moderation_status": "approved"
        }

        data_list = self.find_many(
            filter_dict=query_filters,
            sort=[("created_at", -1)]
        )

        return [ChallengeInteraction.from_dict(data) for data in data_list]

    def get_comments_for_user(self, challenge_id: str, user_id: str,
                            limit: int = 20) -> List[ChallengeInteraction]:
        """Get comments for user in a challenge"""
        query_filters = {
            "challenge_id": challenge_id,
            "to_user_id": user_id,
            "interaction_type": "comment",
            "is_deleted": False,
            "moderation_status": "approved"
        }

        data_list = self.find_many(
            filter_dict=query_filters,
            sort=[("created_at", -1)],
            limit=limit
        )

        return [ChallengeInteraction.from_dict(data) for data in data_list]

    def get_milestone_celebrations(self, challenge_id: str, user_id: str) -> List[ChallengeInteraction]:
        """Get milestone celebrations for user"""
        query_filters = {
            "challenge_id": challenge_id,
            "to_user_id": user_id,
            "context_type": "milestone",
            "is_deleted": False,
            "moderation_status": "approved"
        }

        data_list = self.find_many(
            filter_dict=query_filters,
            sort=[("created_at", -1)]
        )

        return [ChallengeInteraction.from_dict(data) for data in data_list]

    # Like and reply management
    def add_like(self, interaction_id: str, user_id: str) -> bool:
        """Add like to interaction"""
        result = self.collection.update_one(
            {
                "_id": ObjectId(interaction_id),
                "liked_by": {"$ne": user_id}  # Not already liked
            },
            {
                "$addToSet": {"liked_by": user_id},
                "$inc": {"likes_count": 1}
            }
        )
        return result.modified_count > 0

    def remove_like(self, interaction_id: str, user_id: str) -> bool:
        """Remove like from interaction"""
        result = self.collection.update_one(
            {
                "_id": ObjectId(interaction_id),
                "liked_by": user_id  # Already liked
            },
            {
                "$pull": {"liked_by": user_id},
                "$inc": {"likes_count": -1}
            }
        )
        return result.modified_count > 0

    def add_reply(self, interaction_id: str, from_user_id: str, content: str) -> Optional[str]:
        """Add reply to interaction"""
        reply_id = str(ObjectId())
        reply = {
            "reply_id": reply_id,
            "from_user_id": from_user_id,
            "content": content,
            "created_at": datetime.utcnow(),
            "is_deleted": False
        }

        result = self.collection.update_one(
            {"_id": ObjectId(interaction_id)},
            {"$push": {"replies": reply}}
        )

        return reply_id if result.modified_count > 0 else None

    def delete_reply(self, interaction_id: str, reply_id: str, user_id: str) -> bool:
        """Delete reply (mark as deleted)"""
        result = self.collection.update_one(
            {
                "_id": ObjectId(interaction_id),
                "replies.reply_id": reply_id,
                "replies.from_user_id": user_id
            },
            {
                "$set": {
                    "replies.$.is_deleted": True,
                    "replies.$.content": "[deleted]"
                }
            }
        )
        return result.modified_count > 0

    # Moderation methods
    def soft_delete_interaction(self, interaction_id: str, user_id: str) -> bool:
        """Soft delete interaction (only by original author)"""
        result = self.collection.update_one(
            {
                "_id": ObjectId(interaction_id),
                "from_user_id": user_id,
                "is_deleted": False
            },
            {
                "$set": {
                    "is_deleted": True,
                    "content": "[deleted]"
                }
            }
        )
        return result.modified_count > 0

    def flag_interaction(self, interaction_id: str, reason: str = "") -> bool:
        """Flag interaction for moderation"""
        updates = {
            "is_flagged": True,
            "moderation_status": "pending"
        }

        if reason:
            updates["context_data.flag_reason"] = reason
            updates["context_data.flagged_at"] = datetime.utcnow()

        result = self.collection.update_one(
            {
                "_id": ObjectId(interaction_id),
                "is_flagged": False
            },
            {"$set": updates}
        )
        return result.modified_count > 0

    def approve_interaction(self, interaction_id: str) -> bool:
        """Approve flagged interaction"""
        result = self.collection.update_one(
            {
                "_id": ObjectId(interaction_id),
                "is_flagged": True
            },
            {
                "$set": {
                    "is_flagged": False,
                    "moderation_status": "approved"
                }
            }
        )
        return result.modified_count > 0

    def reject_interaction(self, interaction_id: str, reason: str = "") -> bool:
        """Reject flagged interaction"""
        updates = {
            "moderation_status": "rejected",
            "is_deleted": True,
            "content": "[removed]"
        }

        if reason:
            updates["context_data.rejection_reason"] = reason

        result = self.collection.update_one(
            {
                "_id": ObjectId(interaction_id),
                "is_flagged": True
            },
            {"$set": updates}
        )
        return result.modified_count > 0

    def get_flagged_interactions(self, limit: int = 50) -> List[ChallengeInteraction]:
        """Get interactions pending moderation"""
        query_filters = {
            "is_flagged": True,
            "moderation_status": "pending"
        }

        data_list = self.find_many(
            filter_dict=query_filters,
            sort=[("created_at", 1)],  # Oldest first
            limit=limit
        )

        return [ChallengeInteraction.from_dict(data) for data in data_list]

    # Statistics and analytics
    def get_interaction_stats(self, challenge_id: str = None, user_id: str = None) -> Dict[str, Any]:
        """Get interaction statistics"""
        match_query = {"is_deleted": False}

        if challenge_id:
            match_query["challenge_id"] = challenge_id
        if user_id:
            match_query["from_user_id"] = user_id

        pipeline = [
            {"$match": match_query},
            {
                "$group": {
                    "_id": "$interaction_type",
                    "count": {"$sum": 1},
                    "avg_likes": {"$avg": "$likes_count"},
                    "total_replies": {"$sum": {"$size": "$replies"}}
                }
            }
        ]

        results = list(self.collection.aggregate(pipeline))

        stats = {
            "total_interactions": 0,
            "cheers": 0,
            "comments": 0,
            "reactions": 0,
            "avg_engagement": 0,
            "total_replies": 0
        }

        for result in results:
            interaction_type = result["_id"]
            count = result["count"]

            stats["total_interactions"] += count
            stats["total_replies"] += result.get("total_replies", 0)

            if interaction_type in stats:
                stats[interaction_type] = count

        return stats

    def get_most_liked_interactions(self, challenge_id: str = None,
                                   limit: int = 10) -> List[ChallengeInteraction]:
        """Get most liked interactions"""
        query_filters = {
            "is_deleted": False,
            "is_public": True,
            "moderation_status": "approved",
            "likes_count": {"$gt": 0}
        }

        if challenge_id:
            query_filters["challenge_id"] = challenge_id

        data_list = self.find_many(
            filter_dict=query_filters,
            sort=[("likes_count", -1), ("created_at", -1)],
            limit=limit
        )

        return [ChallengeInteraction.from_dict(data) for data in data_list]

    def get_user_engagement_summary(self, user_id: str) -> Dict[str, Any]:
        """Get engagement summary for user"""
        # Interactions given
        given_pipeline = [
            {"$match": {"from_user_id": user_id, "is_deleted": False}},
            {
                "$group": {
                    "_id": "$interaction_type",
                    "given_count": {"$sum": 1}
                }
            }
        ]

        # Interactions received
        received_pipeline = [
            {"$match": {"to_user_id": user_id, "is_deleted": False, "moderation_status": "approved"}},
            {
                "$group": {
                    "_id": "$interaction_type",
                    "received_count": {"$sum": 1},
                    "total_likes": {"$sum": "$likes_count"}
                }
            }
        ]

        given_results = list(self.collection.aggregate(given_pipeline))
        received_results = list(self.collection.aggregate(received_pipeline))

        summary = {
            "interactions_given": {},
            "interactions_received": {},
            "total_likes_received": 0,
            "engagement_ratio": 0.0
        }

        for result in given_results:
            interaction_type = result["_id"]
            summary["interactions_given"][interaction_type] = result["given_count"]

        for result in received_results:
            interaction_type = result["_id"]
            summary["interactions_received"][interaction_type] = result["received_count"]
            summary["total_likes_received"] += result.get("total_likes", 0)

        # Calculate engagement ratio
        total_given = sum(summary["interactions_given"].values())
        total_received = sum(summary["interactions_received"].values())

        if total_given > 0:
            summary["engagement_ratio"] = total_received / total_given

        return summary

    def count_user_interactions(self, challenge_id: str, user_id: str) -> Dict[str, int]:
        """Count interactions for user in specific challenge"""
        # Count interactions given
        given_query = {
            "challenge_id": challenge_id,
            "from_user_id": user_id,
            "is_deleted": False
        }

        # Count interactions received
        received_query = {
            "challenge_id": challenge_id,
            "to_user_id": user_id,
            "is_deleted": False,
            "moderation_status": "approved"
        }

        return {
            "cheers_given": self.count({**given_query, "interaction_type": "cheer"}),
            "comments_made": self.count({**given_query, "interaction_type": "comment"}),
            "cheers_received": self.count({**received_query, "interaction_type": "cheer"}),
            "comments_received": self.count({**received_query, "interaction_type": "comment"})
        }