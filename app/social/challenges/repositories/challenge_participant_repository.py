from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from bson import ObjectId
from app.core.repositories.base_repository import BaseRepository
from app.social.challenges.models.challenge_participant import ChallengeParticipant

class ChallengeParticipantRepository(BaseRepository):
    """Repository for challenge participant data operations"""

    def __init__(self):
        super().__init__("social_challenge_participants")
        self.create_indexes()

    def create_indexes(self):
        """Create database indexes for optimal query performance"""
        if self.collection is None:
            return

        # Compound indexes for common queries
        self.collection.create_index([
            ("challenge_id", 1),
            ("user_id", 1)
        ], unique=True)  # Unique constraint: one participation per user per challenge

        self.collection.create_index([
            ("user_id", 1),
            ("status", 1),
            ("joined_at", -1)
        ])

        self.collection.create_index([
            ("challenge_id", 1),
            ("status", 1),
            ("final_rank", 1)
        ])

        self.collection.create_index([
            ("challenge_id", 1),
            ("final_score", -1)  # For leaderboard queries
        ])

        # Social engagement indexes
        self.collection.create_index([
            ("social_score", -1),
            ("status", 1)
        ])

        self.collection.create_index([
            ("completion_percentage", -1),
            ("challenge_id", 1)
        ])

    def create_participant(self, participant: ChallengeParticipant) -> Optional[str]:
        """Create a new challenge participant"""
        try:
            participant_data = participant.to_dict()
            result = self.collection.insert_one(participant_data)
            return str(result.inserted_id)
        except Exception as e:
            print(f"Error creating participant: {str(e)}")
            return None

    def get_participant(self, challenge_id: str, user_id: str) -> Optional[ChallengeParticipant]:
        """Get participant by challenge and user ID"""
        data = self.find_one({
            "challenge_id": challenge_id,
            "user_id": user_id
        })
        if data:
            return ChallengeParticipant.from_dict(data)
        return None

    def get_participant_by_id(self, id: str) -> Optional[ChallengeParticipant]:
        """Get participant by MongoDB ObjectId"""
        data = self.find_by_id(id)
        if data:
            return ChallengeParticipant.from_dict(data)
        return None

    def update_participant(self, challenge_id: str, user_id: str,
                          updates: Dict[str, Any]) -> bool:
        """Update participant data"""
        updates["last_updated"] = datetime.utcnow()
        return self.update_one(
            {"challenge_id": challenge_id, "user_id": user_id},
            updates
        )

    def delete_participant(self, challenge_id: str, user_id: str) -> bool:
        """Delete participant (when leaving challenge)"""
        return self.delete_one({
            "challenge_id": challenge_id,
            "user_id": user_id
        })

    # Query methods for participants
    def get_challenge_participants(self, challenge_id: str,
                                 status: str = None) -> List[ChallengeParticipant]:
        """Get all participants for a challenge"""
        query_filters = {"challenge_id": challenge_id}

        if status:
            query_filters["status"] = status

        data_list = self.find_many(
            filter_dict=query_filters,
            sort=[("joined_at", 1)]
        )

        return [ChallengeParticipant.from_dict(data) for data in data_list]

    def get_user_participations(self, user_id: str, status: str = None,
                               limit: int = 20, offset: int = 0) -> List[ChallengeParticipant]:
        """Get all participations for a user"""
        query_filters = {"user_id": user_id}

        if status:
            query_filters["status"] = status

        data_list = self.find_many(
            filter_dict=query_filters,
            sort=[("joined_at", -1)],
            limit=limit,
            skip=offset
        )

        return [ChallengeParticipant.from_dict(data) for data in data_list]

    def get_challenge_leaderboard(self, challenge_id: str,
                                limit: int = 50) -> List[ChallengeParticipant]:
        """Get challenge leaderboard sorted by final score"""
        query_filters = {
            "challenge_id": challenge_id,
            "status": {"$in": ["active", "completed"]},
            "final_score": {"$gt": 0}
        }

        data_list = self.find_many(
            filter_dict=query_filters,
            sort=[("final_score", -1), ("completed_at", 1)],
            limit=limit
        )

        return [ChallengeParticipant.from_dict(data) for data in data_list]

    def get_active_participants(self, challenge_id: str) -> List[ChallengeParticipant]:
        """Get active participants for a challenge"""
        return self.get_challenge_participants(challenge_id, status="active")

    def get_completed_participants(self, challenge_id: str) -> List[ChallengeParticipant]:
        """Get completed participants for a challenge"""
        return self.get_challenge_participants(challenge_id, status="completed")

    # Progress tracking methods
    def update_progress(self, challenge_id: str, user_id: str,
                       progress_data: Dict[str, Any]) -> bool:
        """Update participant's progress"""
        updates = {
            "current_progress": progress_data,
            "progress_updates": {"$inc": 1},
            "last_progress_update": datetime.utcnow()
        }

        # Calculate completion percentage if target is provided
        if "target_value" in progress_data and progress_data["target_value"] > 0:
            current_value = progress_data.get("current_value", 0)
            completion = min(100.0, (current_value / progress_data["target_value"]) * 100)
            updates["completion_percentage"] = completion

        result = self.collection.update_one(
            {"challenge_id": challenge_id, "user_id": user_id},
            {"$set": updates}
        )
        return result.modified_count > 0

    def add_social_interaction(self, challenge_id: str, user_id: str,
                             interaction_type: str, count: int = 1) -> bool:
        """Add social interaction count"""
        field_map = {
            "cheer_received": "cheers_received",
            "cheer_given": "cheers_given",
            "comment_received": "comments_received",
            "comment_made": "comments_made"
        }

        if interaction_type not in field_map:
            return False

        field_name = field_map[interaction_type]
        result = self.collection.update_one(
            {"challenge_id": challenge_id, "user_id": user_id},
            {"$inc": {field_name: count}}
        )

        # Recalculate social score
        if result.modified_count > 0:
            self._recalculate_social_score(challenge_id, user_id)

        return result.modified_count > 0

    def _recalculate_social_score(self, challenge_id: str, user_id: str) -> None:
        """Recalculate social engagement score for participant"""
        participant_data = self.find_one({
            "challenge_id": challenge_id,
            "user_id": user_id
        })

        if not participant_data:
            return

        # Calculate social score using same logic as model
        cheer_weight = 2.0
        comment_weight = 5.0
        engagement_bonus = 1.5

        cheers_received = participant_data.get("cheers_received", 0)
        cheers_given = participant_data.get("cheers_given", 0)
        comments_received = participant_data.get("comments_received", 0)
        comments_made = participant_data.get("comments_made", 0)

        raw_score = (
            (cheers_received * cheer_weight) +
            (cheers_given * cheer_weight * 0.5) +
            (comments_received * comment_weight) +
            (comments_made * comment_weight * 0.3)
        )

        # Bonus for being both active and engaging
        if cheers_given > 0 and comments_made > 0:
            raw_score *= engagement_bonus

        social_score = round(raw_score, 2)

        self.update_one(
            {"challenge_id": challenge_id, "user_id": user_id},
            {"social_score": social_score}
        )

    def record_milestone(self, challenge_id: str, user_id: str,
                        milestone_data: Dict[str, Any]) -> bool:
        """Record milestone achievement"""
        updates = {"$inc": {"milestones_reached": 1}}

        if "achievement" in milestone_data:
            updates["$inc"]["achievements_earned"] = 1

        result = self.collection.update_one(
            {"challenge_id": challenge_id, "user_id": user_id},
            updates
        )
        return result.modified_count > 0

    def update_rank(self, challenge_id: str, user_id: str, new_rank: int) -> bool:
        """Update participant's rank"""
        # Get current best rank
        participant_data = self.find_one({
            "challenge_id": challenge_id,
            "user_id": user_id
        })

        if not participant_data:
            return False

        current_best = participant_data.get("best_rank", 0)
        updates = {}

        if current_best == 0 or new_rank < current_best:
            updates["best_rank"] = new_rank

        result = self.collection.update_one(
            {"challenge_id": challenge_id, "user_id": user_id},
            {"$set": updates}
        )
        return result.modified_count > 0

    def complete_participation(self, challenge_id: str, user_id: str,
                             final_score: float, final_rank: int) -> bool:
        """Mark participation as completed"""
        updates = {
            "status": "completed",
            "final_score": final_score,
            "final_rank": final_rank,
            "completed_at": datetime.utcnow()
        }

        # Update best rank if this is better
        participant_data = self.find_one({
            "challenge_id": challenge_id,
            "user_id": user_id
        })

        if participant_data:
            current_best = participant_data.get("best_rank", 0)
            if current_best == 0 or final_rank < current_best:
                updates["best_rank"] = final_rank

        result = self.collection.update_one(
            {"challenge_id": challenge_id, "user_id": user_id},
            {"$set": updates}
        )
        return result.modified_count > 0

    def quit_challenge(self, challenge_id: str, user_id: str) -> bool:
        """Mark participant as quit"""
        result = self.collection.update_one(
            {
                "challenge_id": challenge_id,
                "user_id": user_id,
                "status": {"$nin": ["completed", "disqualified"]}
            },
            {"$set": {"status": "quit"}}
        )
        return result.modified_count > 0

    def disqualify_participant(self, challenge_id: str, user_id: str, reason: str = "") -> bool:
        """Disqualify participant"""
        updates = {"status": "disqualified"}
        if reason:
            updates["current_progress.disqualification_reason"] = reason

        result = self.collection.update_one(
            {
                "challenge_id": challenge_id,
                "user_id": user_id,
                "status": {"$ne": "completed"}
            },
            {"$set": updates}
        )
        return result.modified_count > 0

    # Rewards and achievements
    def claim_rewards(self, challenge_id: str, user_id: str,
                     credits: int, badges: List[str] = None) -> bool:
        """Mark rewards as claimed"""
        updates = {
            "credits_earned": credits,
            "badges_earned": badges or [],
            "rewards_claimed": True,
            "rewards_claimed_at": datetime.utcnow()
        }

        result = self.collection.update_one(
            {"challenge_id": challenge_id, "user_id": user_id},
            {"$set": updates}
        )
        return result.modified_count > 0

    def update_friend_referrals(self, challenge_id: str, user_id: str,
                               friends_invited: int = 0, friends_joined: int = 0) -> bool:
        """Update friend referral metrics"""
        updates = {}
        if friends_invited > 0:
            updates["friends_invited"] = {"$inc": friends_invited}
        if friends_joined > 0:
            updates["friends_joined"] = {"$inc": friends_joined}

        if not updates:
            return False

        result = self.collection.update_one(
            {"challenge_id": challenge_id, "user_id": user_id},
            updates
        )
        return result.modified_count > 0

    # Statistics and analytics
    def get_participant_stats(self, user_id: str) -> Dict[str, Any]:
        """Get participation statistics for user"""
        pipeline = [
            {"$match": {"user_id": user_id}},
            {
                "$group": {
                    "_id": "$status",
                    "count": {"$sum": 1},
                    "avg_score": {"$avg": "$final_score"},
                    "avg_rank": {"$avg": "$final_rank"},
                    "total_social_score": {"$sum": "$social_score"}
                }
            }
        ]

        results = list(self.collection.aggregate(pipeline))

        stats = {
            "total_participations": 0,
            "active": 0,
            "completed": 0,
            "quit": 0,
            "avg_score": 0,
            "avg_rank": 0,
            "total_social_engagement": 0
        }

        for result in results:
            status = result["_id"]
            count = result["count"]

            stats["total_participations"] += count

            if status in stats:
                stats[status] = count

            if status == "completed":
                stats["avg_score"] = result.get("avg_score", 0)
                stats["avg_rank"] = result.get("avg_rank", 0)

            stats["total_social_engagement"] += result.get("total_social_score", 0)

        return stats

    def get_top_performers(self, challenge_id: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top performing participants"""
        match_query = {"status": "completed"}
        if challenge_id:
            match_query["challenge_id"] = challenge_id

        pipeline = [
            {"$match": match_query},
            {
                "$group": {
                    "_id": "$user_id",
                    "total_score": {"$sum": "$final_score"},
                    "avg_score": {"$avg": "$final_score"},
                    "best_rank": {"$min": "$final_rank"},
                    "participations": {"$sum": 1},
                    "social_score": {"$sum": "$social_score"}
                }
            },
            {"$sort": {"total_score": -1}},
            {"$limit": limit}
        ]

        return list(self.collection.aggregate(pipeline))

    def get_most_social_participants(self, challenge_id: str = None,
                                   limit: int = 10) -> List[Dict[str, Any]]:
        """Get participants with highest social engagement"""
        match_query = {}
        if challenge_id:
            match_query["challenge_id"] = challenge_id

        pipeline = [
            {"$match": match_query},
            {
                "$group": {
                    "_id": "$user_id",
                    "total_social_score": {"$sum": "$social_score"},
                    "avg_social_score": {"$avg": "$social_score"},
                    "total_cheers_given": {"$sum": "$cheers_given"},
                    "total_comments_made": {"$sum": "$comments_made"},
                    "participations": {"$sum": 1}
                }
            },
            {"$sort": {"total_social_score": -1}},
            {"$limit": limit}
        ]

        return list(self.collection.aggregate(pipeline))