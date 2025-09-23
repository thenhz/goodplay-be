from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from app.core.repositories.base_repository import BaseRepository
from ..models.challenge_participant import ChallengeParticipant

class ChallengeParticipantRepository(BaseRepository):
    """Repository for challenge participant operations"""

    def __init__(self):
        super().__init__("challenge_participants")

    def create_participant(self, participant: ChallengeParticipant) -> str:
        """Create a new challenge participant"""
        return self.create(participant.to_dict())

    def get_participant_by_id(self, participant_id: str) -> Optional[ChallengeParticipant]:
        """Get a participant by ID"""
        data = self.find_by_id(participant_id)
        return ChallengeParticipant.from_dict(data) if data else None

    def get_participant(self, challenge_id: str, user_id: str) -> Optional[ChallengeParticipant]:
        """Get a specific participant in a challenge"""
        data = self.find_one({
            "challenge_id": challenge_id,
            "user_id": user_id
        })
        return ChallengeParticipant.from_dict(data) if data else None

    def get_challenge_participants(self, challenge_id: str) -> List[ChallengeParticipant]:
        """Get all participants for a challenge"""
        participants_data = self.find_many(
            {"challenge_id": challenge_id},
            sort=[("joined_at", 1)]
        )
        return [ChallengeParticipant.from_dict(data) for data in participants_data]

    def get_user_participations(self, user_id: str, status: str = None, limit: int = 50) -> List[ChallengeParticipant]:
        """Get all participations for a user"""
        filter_dict = {"user_id": user_id}
        if status:
            filter_dict["status"] = status

        participations_data = self.find_many(
            filter_dict,
            limit=limit,
            sort=[("joined_at", -1)]
        )
        return [ChallengeParticipant.from_dict(data) for data in participations_data]

    def get_pending_invitations(self, user_id: str) -> List[ChallengeParticipant]:
        """Get pending challenge invitations for a user"""
        participations_data = self.find_many({
            "user_id": user_id,
            "status": "invited"
        }, sort=[("joined_at", -1)])
        return [ChallengeParticipant.from_dict(data) for data in participations_data]

    def get_active_participations(self, user_id: str) -> List[ChallengeParticipant]:
        """Get active participations for a user"""
        participations_data = self.find_many({
            "user_id": user_id,
            "status": {"$in": ["accepted", "active"]}
        }, sort=[("started_at", -1)])
        return [ChallengeParticipant.from_dict(data) for data in participations_data]

    def update_participant_status(self, challenge_id: str, user_id: str, status: str,
                                 additional_data: Dict[str, Any] = None) -> bool:
        """Update participant status"""
        update_data = {"status": status}

        # Add timestamps based on status
        now = datetime.utcnow()
        if status == "accepted":
            update_data["accepted_at"] = now
        elif status == "active":
            update_data["started_at"] = now
        elif status in ["completed", "declined", "dropped"]:
            update_data["completed_at"] = now

        if additional_data:
            update_data.update(additional_data)

        result = self.collection.update_one(
            {"challenge_id": challenge_id, "user_id": user_id},
            {"$set": update_data}
        )
        return result.modified_count > 0

    def accept_invitation(self, challenge_id: str, user_id: str) -> bool:
        """Accept a challenge invitation"""
        return self.update_participant_status(
            challenge_id, user_id, "accepted",
            {"accepted_at": datetime.utcnow()}
        )

    def decline_invitation(self, challenge_id: str, user_id: str) -> bool:
        """Decline a challenge invitation"""
        return self.update_participant_status(
            challenge_id, user_id, "declined",
            {"completed_at": datetime.utcnow()}
        )

    def start_participation(self, challenge_id: str, user_id: str, game_session_id: str) -> bool:
        """Start active participation in a challenge"""
        return self.update_participant_status(
            challenge_id, user_id, "active",
            {
                "started_at": datetime.utcnow(),
                "game_session_id": game_session_id
            }
        )

    def complete_participation(self, challenge_id: str, user_id: str, score: int,
                             final_position: int = None, performance_data: Dict[str, Any] = None) -> bool:
        """Complete a participant's involvement in a challenge"""
        update_data = {
            "status": "completed",
            "completed_at": datetime.utcnow(),
            "score": score
        }

        if final_position is not None:
            update_data["final_position"] = final_position

        if performance_data:
            update_data["performance_data"] = performance_data

        result = self.collection.update_one(
            {"challenge_id": challenge_id, "user_id": user_id},
            {"$set": update_data}
        )
        return result.modified_count > 0

    def drop_out(self, challenge_id: str, user_id: str) -> bool:
        """Mark participant as dropped out"""
        return self.update_participant_status(
            challenge_id, user_id, "dropped",
            {"completed_at": datetime.utcnow()}
        )

    def update_performance_data(self, challenge_id: str, user_id: str, performance_data: Dict[str, Any]) -> bool:
        """Update performance data for a participant"""
        result = self.collection.update_one(
            {"challenge_id": challenge_id, "user_id": user_id},
            {"$set": {"performance_data": performance_data}}
        )
        return result.modified_count > 0

    def set_notification_preferences(self, challenge_id: str, user_id: str,
                                   preferences: Dict[str, Any]) -> bool:
        """Set notification preferences for a participant"""
        result = self.collection.update_one(
            {"challenge_id": challenge_id, "user_id": user_id},
            {"$set": {"notification_preferences": preferences}}
        )
        return result.modified_count > 0

    def get_challenge_acceptance_rate(self, challenger_id: str, days_back: int = 30) -> Dict[str, Any]:
        """Get acceptance rate for challenges created by a user"""
        since_date = datetime.utcnow() - timedelta(days=days_back)

        # Get challenges created by this user
        pipeline = [
            {
                "$lookup": {
                    "from": "challenges",
                    "localField": "challenge_id",
                    "foreignField": "challenge_id",
                    "as": "challenge"
                }
            },
            {"$unwind": "$challenge"},
            {
                "$match": {
                    "challenge.challenger_id": challenger_id,
                    "challenge.created_at": {"$gte": since_date},
                    "participant_type": {"$ne": "challenger"}  # Exclude the challenger themselves
                }
            },
            {
                "$group": {
                    "_id": None,
                    "total_invitations": {"$sum": 1},
                    "accepted_invitations": {
                        "$sum": {"$cond": [{"$eq": ["$status", "accepted"]}, 1, 0]}
                    },
                    "declined_invitations": {
                        "$sum": {"$cond": [{"$eq": ["$status", "declined"]}, 1, 0]}
                    }
                }
            }
        ]

        result = list(self.collection.aggregate(pipeline))
        if result:
            stats = result[0]
            total = stats["total_invitations"]
            accepted = stats["accepted_invitations"]
            return {
                "total_invitations": total,
                "accepted_invitations": accepted,
                "declined_invitations": stats["declined_invitations"],
                "acceptance_rate": (accepted / total * 100) if total > 0 else 0
            }

        return {
            "total_invitations": 0,
            "accepted_invitations": 0,
            "declined_invitations": 0,
            "acceptance_rate": 0
        }

    def get_user_challenge_stats(self, user_id: str, days_back: int = 30) -> Dict[str, Any]:
        """Get challenge statistics for a user"""
        since_date = datetime.utcnow() - timedelta(days=days_back)

        stats_pipeline = [
            {
                "$match": {
                    "user_id": user_id,
                    "joined_at": {"$gte": since_date}
                }
            },
            {
                "$group": {
                    "_id": None,
                    "total_challenges": {"$sum": 1},
                    "completed_challenges": {
                        "$sum": {"$cond": [{"$eq": ["$status", "completed"]}, 1, 0]}
                    },
                    "won_challenges": {
                        "$sum": {"$cond": [{"$eq": ["$final_position", 1]}, 1, 0]}
                    },
                    "declined_challenges": {
                        "$sum": {"$cond": [{"$eq": ["$status", "declined"]}, 1, 0]}
                    },
                    "dropped_challenges": {
                        "$sum": {"$cond": [{"$eq": ["$status", "dropped"]}, 1, 0]}
                    },
                    "average_score": {"$avg": "$score"},
                    "total_response_time": {"$sum": {
                        "$cond": [
                            {"$ne": ["$accepted_at", None]},
                            {"$subtract": ["$accepted_at", "$joined_at"]},
                            0
                        ]
                    }}
                }
            }
        ]

        result = list(self.collection.aggregate(stats_pipeline))
        if result:
            stats = result[0]
            total = stats["total_challenges"]
            completed = stats["completed_challenges"]
            won = stats["won_challenges"]

            return {
                "total_challenges": total,
                "completed_challenges": completed,
                "won_challenges": won,
                "declined_challenges": stats["declined_challenges"],
                "dropped_challenges": stats["dropped_challenges"],
                "completion_rate": (completed / total * 100) if total > 0 else 0,
                "win_rate": (won / completed * 100) if completed > 0 else 0,
                "average_score": stats["average_score"] or 0,
                "average_response_time_seconds": (stats["total_response_time"] / total / 1000) if total > 0 else 0
            }

        return {
            "total_challenges": 0,
            "completed_challenges": 0,
            "won_challenges": 0,
            "declined_challenges": 0,
            "dropped_challenges": 0,
            "completion_rate": 0,
            "win_rate": 0,
            "average_score": 0,
            "average_response_time_seconds": 0
        }

    def get_response_time_statistics(self, days_back: int = 30) -> Dict[str, Any]:
        """Get response time statistics for all users"""
        since_date = datetime.utcnow() - timedelta(days=days_back)

        pipeline = [
            {
                "$match": {
                    "joined_at": {"$gte": since_date},
                    "accepted_at": {"$ne": None}
                }
            },
            {
                "$project": {
                    "response_time_ms": {
                        "$subtract": ["$accepted_at", "$joined_at"]
                    }
                }
            },
            {
                "$group": {
                    "_id": None,
                    "count": {"$sum": 1},
                    "average_response_time": {"$avg": "$response_time_ms"},
                    "min_response_time": {"$min": "$response_time_ms"},
                    "max_response_time": {"$max": "$response_time_ms"}
                }
            }
        ]

        result = list(self.collection.aggregate(pipeline))
        if result:
            stats = result[0]
            return {
                "sample_size": stats["count"],
                "average_response_time_seconds": stats["average_response_time"] / 1000,
                "fastest_response_seconds": stats["min_response_time"] / 1000,
                "slowest_response_seconds": stats["max_response_time"] / 1000
            }

        return {
            "sample_size": 0,
            "average_response_time_seconds": 0,
            "fastest_response_seconds": 0,
            "slowest_response_seconds": 0
        }

    def cleanup_old_participants(self, days_old: int = 90) -> int:
        """Delete old participant records"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)

        result = self.collection.delete_many({
            "status": {"$in": ["completed", "declined", "dropped"]},
            "completed_at": {"$lt": cutoff_date}
        })
        return result.deleted_count