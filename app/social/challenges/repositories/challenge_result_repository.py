from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from bson import ObjectId
from app.core.repositories.base_repository import BaseRepository
from app.social.challenges.models.challenge_result import ChallengeResult

class ChallengeResultRepository(BaseRepository):
    """Repository for challenge result data operations"""

    def __init__(self):
        super().__init__("social_challenge_results")
        self.create_indexes()

    def create_indexes(self):
        """Create database indexes for optimal query performance"""
        if self.collection is None:
            return

        # Compound indexes for common queries
        self.collection.create_index([
            ("challenge_id", 1),
            ("user_id", 1)
        ], unique=True)  # One result per user per challenge

        self.collection.create_index([
            ("challenge_id", 1),
            ("final_score", -1)  # For leaderboards
        ])

        self.collection.create_index([
            ("user_id", 1),
            ("completed_at", -1)
        ])

        self.collection.create_index([
            ("rank", 1),
            ("challenge_id", 1)
        ])

        # Performance analytics indexes
        self.collection.create_index([
            ("social_engagement_score", -1),
            ("result_status", 1)
        ])

        self.collection.create_index([
            ("community_impact_score", -1),
            ("is_verified", 1)
        ])

        self.collection.create_index([
            ("completed_at", -1),
            ("result_status", 1)
        ])

    def create_result(self, result: ChallengeResult) -> Optional[str]:
        """Create a new challenge result"""
        try:
            result_data = result.to_dict()
            db_result = self.collection.insert_one(result_data)
            return str(db_result.inserted_id)
        except Exception as e:
            print(f"Error creating result: {str(e)}")
            return None

    def get_result(self, challenge_id: str, user_id: str) -> Optional[ChallengeResult]:
        """Get result by challenge and user ID"""
        data = self.find_one({
            "challenge_id": challenge_id,
            "user_id": user_id
        })
        if data:
            return ChallengeResult.from_dict(data)
        return None

    def get_result_by_id(self, id: str) -> Optional[ChallengeResult]:
        """Get result by MongoDB ObjectId"""
        data = self.find_by_id(id)
        if data:
            return ChallengeResult.from_dict(data)
        return None

    def update_result(self, challenge_id: str, user_id: str,
                     updates: Dict[str, Any]) -> bool:
        """Update result data"""
        updates["updated_at"] = datetime.utcnow()
        return self.update_one(
            {"challenge_id": challenge_id, "user_id": user_id},
            updates
        )

    def delete_result(self, challenge_id: str, user_id: str) -> bool:
        """Delete result"""
        return self.delete_one({
            "challenge_id": challenge_id,
            "user_id": user_id
        })

    # Query methods for results
    def get_challenge_results(self, challenge_id: str,
                            verified_only: bool = False) -> List[ChallengeResult]:
        """Get all results for a challenge"""
        query_filters = {"challenge_id": challenge_id}

        if verified_only:
            query_filters["is_verified"] = True

        data_list = self.find_many(
            filter_dict=query_filters,
            sort=[("final_score", -1), ("completed_at", 1)]
        )

        return [ChallengeResult.from_dict(data) for data in data_list]

    def get_user_results(self, user_id: str, limit: int = 20,
                        offset: int = 0) -> List[ChallengeResult]:
        """Get all results for a user"""
        data_list = self.find_many(
            filter_dict={"user_id": user_id},
            sort=[("completed_at", -1)],
            limit=limit,
            skip=offset
        )

        return [ChallengeResult.from_dict(data) for data in data_list]

    def get_challenge_leaderboard(self, challenge_id: str,
                                limit: int = 50) -> List[ChallengeResult]:
        """Get challenge leaderboard"""
        query_filters = {
            "challenge_id": challenge_id,
            "result_status": "completed",
            "final_score": {"$gt": 0}
        }

        data_list = self.find_many(
            filter_dict=query_filters,
            sort=[("final_score", -1), ("completed_at", 1)],
            limit=limit
        )

        return [ChallengeResult.from_dict(data) for data in data_list]

    def get_top_performers(self, challenge_id: str = None,
                          metric: str = "final_score", limit: int = 10) -> List[ChallengeResult]:
        """Get top performers by specific metric"""
        query_filters = {"result_status": "completed"}

        if challenge_id:
            query_filters["challenge_id"] = challenge_id

        # Valid metrics for sorting
        valid_metrics = {
            "final_score": ("final_score", -1),
            "social_engagement": ("social_engagement_score", -1),
            "community_impact": ("community_impact_score", -1),
            "collaboration": ("collaboration_score", -1)
        }

        sort_field, sort_order = valid_metrics.get(metric, ("final_score", -1))

        data_list = self.find_many(
            filter_dict=query_filters,
            sort=[(sort_field, sort_order), ("completed_at", 1)],
            limit=limit
        )

        return [ChallengeResult.from_dict(data) for data in data_list]

    def get_recent_results(self, hours: int = 24, limit: int = 50) -> List[ChallengeResult]:
        """Get recent results within specified hours"""
        since_time = datetime.utcnow() - timedelta(hours=hours)
        query_filters = {
            "completed_at": {"$gte": since_time},
            "result_status": "completed"
        }

        data_list = self.find_many(
            filter_dict=query_filters,
            sort=[("completed_at", -1)],
            limit=limit
        )

        return [ChallengeResult.from_dict(data) for data in data_list]

    # Score and ranking operations
    def update_final_score(self, challenge_id: str, user_id: str,
                          final_score: float) -> bool:
        """Update final score for result"""
        return self.update_one(
            {"challenge_id": challenge_id, "user_id": user_id},
            {"final_score": final_score}
        )

    def bulk_update_ranks(self, challenge_id: str, rank_updates: List[Dict[str, Any]]) -> int:
        """Bulk update ranks for challenge results"""
        operations = []
        for update in rank_updates:
            user_id = update.get("user_id")
            new_rank = update.get("rank")
            if user_id and new_rank:
                operations.append({
                    "filter": {"challenge_id": challenge_id, "user_id": user_id},
                    "update": {"$set": {"rank": new_rank}}
                })

        if not operations:
            return 0

        # Use bulk_write for efficiency
        from pymongo import UpdateOne
        bulk_ops = [UpdateOne(op["filter"], op["update"]) for op in operations]

        try:
            result = self.collection.bulk_write(bulk_ops)
            return result.modified_count
        except Exception as e:
            print(f"Error in bulk rank update: {str(e)}")
            return 0

    def add_bonus_score(self, challenge_id: str, user_id: str,
                       bonus_type: str, amount: float, reason: str = "") -> bool:
        """Add bonus score to result"""
        bonus_field = f"bonus_scores.{bonus_type}"
        updates = {bonus_field: amount}

        if reason:
            reason_field = f"challenge_specific_data.bonus_reasons.{bonus_type}"
            updates[reason_field] = reason

        return self.update_one(
            {"challenge_id": challenge_id, "user_id": user_id},
            updates
        )

    def add_penalty_score(self, challenge_id: str, user_id: str,
                         penalty_type: str, amount: float, reason: str = "") -> bool:
        """Add penalty to result"""
        penalty_field = f"penalty_scores.{penalty_type}"
        updates = {penalty_field: amount}

        if reason:
            reason_field = f"challenge_specific_data.penalty_reasons.{penalty_type}"
            updates[reason_field] = reason

        return self.update_one(
            {"challenge_id": challenge_id, "user_id": user_id},
            updates
        )

    def apply_multiplier(self, challenge_id: str, user_id: str,
                        multiplier_type: str, value: float) -> bool:
        """Apply score multiplier"""
        multiplier_field = f"multipliers_applied.{multiplier_type}"
        return self.update_one(
            {"challenge_id": challenge_id, "user_id": user_id},
            {multiplier_field: value}
        )

    # Achievement and milestone tracking
    def add_milestone(self, challenge_id: str, user_id: str,
                     milestone: Dict[str, Any]) -> bool:
        """Add milestone to result"""
        milestone["achieved_at"] = datetime.utcnow()
        return self.update_one(
            {"challenge_id": challenge_id, "user_id": user_id},
            {"$push": {"milestones_achieved": milestone}}
        )

    def add_badge(self, challenge_id: str, user_id: str,
                 badge_id: str, badge_name: str = "") -> bool:
        """Add badge to result"""
        badge_data = {
            "badge_id": badge_id,
            "badge_name": badge_name,
            "earned_at": datetime.utcnow()
        }
        return self.update_one(
            {"challenge_id": challenge_id, "user_id": user_id},
            {"$push": {"badges_earned": badge_data}}
        )

    def record_broken_record(self, challenge_id: str, user_id: str,
                           record_type: str, old_value: float, new_value: float) -> bool:
        """Record a broken record"""
        record = {
            "record_type": record_type,
            "old_value": old_value,
            "new_value": new_value,
            "broken_at": datetime.utcnow()
        }
        return self.update_one(
            {"challenge_id": challenge_id, "user_id": user_id},
            {"$push": {"records_broken": record}}
        )

    # Social and community metrics
    def update_social_metrics(self, challenge_id: str, user_id: str,
                            cheers_received: int, cheers_given: int,
                            comments_received: int, comments_made: int) -> bool:
        """Update social interaction metrics"""
        # Calculate social engagement score
        cheer_weight = 2.0
        comment_weight = 5.0

        social_score = (
            (cheers_received * cheer_weight) +
            (cheers_given * cheer_weight * 0.5) +
            (comments_received * comment_weight) +
            (comments_made * comment_weight * 0.3)
        )

        updates = {
            "interactions_summary.cheers_received": cheers_received,
            "interactions_summary.cheers_given": cheers_given,
            "interactions_summary.comments_received": comments_received,
            "interactions_summary.comments_made": comments_made,
            "interactions_summary.total_interactions": (
                cheers_received + cheers_given + comments_received + comments_made
            ),
            "social_engagement_score": social_score
        }

        return self.update_one(
            {"challenge_id": challenge_id, "user_id": user_id},
            updates
        )

    def update_community_impact(self, challenge_id: str, user_id: str,
                              friends_invited: int, friends_joined: int,
                              donation_amount: float = 0.0) -> bool:
        """Update community impact metrics"""
        # Calculate impact score
        referral_impact = friends_joined * 10
        conversion_bonus = 0
        if friends_invited > 0:
            conversion_rate = friends_joined / friends_invited
            conversion_bonus = conversion_rate * 20

        donation_impact = donation_amount * 0.1
        community_impact_score = referral_impact + conversion_bonus + donation_impact
        friend_referral_bonus = friends_joined * 5

        updates = {
            "community_impact_score": community_impact_score,
            "friend_referral_bonus": friend_referral_bonus
        }

        return self.update_one(
            {"challenge_id": challenge_id, "user_id": user_id},
            updates
        )

    # Verification and moderation
    def verify_result(self, challenge_id: str, user_id: str, verifier_id: str) -> bool:
        """Verify result"""
        updates = {
            "is_verified": True,
            "verified_by": verifier_id,
            "verified_at": datetime.utcnow()
        }

        return self.update_one(
            {"challenge_id": challenge_id, "user_id": user_id, "is_verified": False},
            updates
        )

    def disqualify_result(self, challenge_id: str, user_id: str, reason: str) -> bool:
        """Disqualify result"""
        updates = {
            "result_status": "disqualified",
            "challenge_specific_data.disqualification_reason": reason,
            "challenge_specific_data.disqualified_at": datetime.utcnow()
        }

        return self.update_one(
            {"challenge_id": challenge_id, "user_id": user_id, "result_status": "completed"},
            updates
        )

    # Statistics and analytics
    def get_challenge_statistics(self, challenge_id: str) -> Dict[str, Any]:
        """Get comprehensive statistics for a challenge"""
        pipeline = [
            {"$match": {"challenge_id": challenge_id, "result_status": "completed"}},
            {
                "$group": {
                    "_id": None,
                    "total_participants": {"$sum": 1},
                    "avg_score": {"$avg": "$final_score"},
                    "max_score": {"$max": "$final_score"},
                    "min_score": {"$min": "$final_score"},
                    "avg_duration": {"$avg": "$total_duration_minutes"},
                    "avg_social_score": {"$avg": "$social_engagement_score"},
                    "avg_impact_score": {"$avg": "$community_impact_score"},
                    "total_credits_earned": {"$sum": "$credits_earned"},
                    "total_badges": {"$sum": {"$size": "$badges_earned"}},
                    "verified_results": {"$sum": {"$cond": ["$is_verified", 1, 0]}}
                }
            }
        ]

        results = list(self.collection.aggregate(pipeline))
        return results[0] if results else {}

    def get_user_performance_summary(self, user_id: str) -> Dict[str, Any]:
        """Get performance summary for user across all challenges"""
        pipeline = [
            {"$match": {"user_id": user_id, "result_status": "completed"}},
            {
                "$group": {
                    "_id": None,
                    "total_challenges": {"$sum": 1},
                    "avg_score": {"$avg": "$final_score"},
                    "best_score": {"$max": "$final_score"},
                    "avg_rank": {"$avg": "$rank"},
                    "best_rank": {"$min": "$rank"},
                    "total_social_score": {"$sum": "$social_engagement_score"},
                    "total_impact_score": {"$sum": "$community_impact_score"},
                    "total_credits": {"$sum": "$credits_earned"},
                    "total_badges": {"$sum": {"$size": "$badges_earned"}},
                    "first_place_finishes": {"$sum": {"$cond": [{"$eq": ["$rank", 1]}, 1, 0]}},
                    "top_3_finishes": {"$sum": {"$cond": [{"$lte": ["$rank", 3]}, 1, 0]}}
                }
            }
        ]

        results = list(self.collection.aggregate(pipeline))
        return results[0] if results else {}

    def get_leaderboard_by_category(self, challenge_category: str,
                                   limit: int = 10) -> List[Dict[str, Any]]:
        """Get cross-challenge leaderboard by category"""
        pipeline = [
            {
                "$lookup": {
                    "from": "social_challenges",
                    "localField": "challenge_id",
                    "foreignField": "challenge_id",
                    "as": "challenge_info"
                }
            },
            {"$unwind": "$challenge_info"},
            {
                "$match": {
                    "challenge_info.challenge_category": challenge_category,
                    "result_status": "completed"
                }
            },
            {
                "$group": {
                    "_id": "$user_id",
                    "total_score": {"$sum": "$final_score"},
                    "avg_score": {"$avg": "$final_score"},
                    "challenges_completed": {"$sum": 1},
                    "avg_rank": {"$avg": "$rank"},
                    "best_rank": {"$min": "$rank"},
                    "social_engagement": {"$sum": "$social_engagement_score"}
                }
            },
            {"$sort": {"total_score": -1}},
            {"$limit": limit}
        ]

        return list(self.collection.aggregate(pipeline))