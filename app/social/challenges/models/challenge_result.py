from datetime import datetime
from typing import Dict, Any, Optional
from bson import ObjectId
from dataclasses import dataclass, field

@dataclass
class ChallengeResult:
    """Result of a social challenge with detailed metrics and social impact"""
    challenge_id: str
    user_id: str

    # Core Performance Metrics
    final_score: float
    rank: int
    completion_percentage: float

    # Time Tracking
    started_at: datetime
    completed_at: datetime = field(default_factory=datetime.utcnow)
    total_duration_minutes: int = 0

    # Performance Breakdown
    base_score: float = 0.0
    bonus_scores: Dict[str, float] = field(default_factory=dict)
    penalty_scores: Dict[str, float] = field(default_factory=dict)

    # Social Impact Metrics
    social_engagement_score: float = 0.0
    community_impact_score: float = 0.0
    friend_referral_bonus: float = 0.0
    collaboration_score: float = 0.0

    # Achievement Tracking
    milestones_achieved: list = field(default_factory=list)
    badges_earned: list = field(default_factory=list)
    records_broken: list = field(default_factory=list)

    # Rewards Summary
    credits_earned: int = 0
    impact_points_earned: int = 0
    social_points_earned: int = 0
    multipliers_applied: Dict[str, float] = field(default_factory=dict)

    # Challenge-Specific Metrics
    challenge_specific_data: Dict[str, Any] = field(default_factory=dict)

    # Social Interactions During Challenge
    interactions_summary: Dict[str, int] = field(default_factory=dict)

    # Status and Validation
    result_status: str = "completed"  # 'completed', 'disqualified', 'partial'
    is_verified: bool = False
    verified_by: Optional[str] = None
    verified_at: Optional[datetime] = None

    _id: Optional[ObjectId] = field(default=None)

    def __post_init__(self):
        """Calculate derived metrics after initialization"""
        if self.started_at and self.completed_at:
            self.total_duration_minutes = int((self.completed_at - self.started_at).total_seconds() / 60)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the result to a dictionary for MongoDB storage"""
        data = {
            "challenge_id": self.challenge_id,
            "user_id": self.user_id,
            "final_score": self.final_score,
            "rank": self.rank,
            "completion_percentage": self.completion_percentage,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "total_duration_minutes": self.total_duration_minutes,
            "base_score": self.base_score,
            "bonus_scores": self.bonus_scores,
            "penalty_scores": self.penalty_scores,
            "social_engagement_score": self.social_engagement_score,
            "community_impact_score": self.community_impact_score,
            "friend_referral_bonus": self.friend_referral_bonus,
            "collaboration_score": self.collaboration_score,
            "milestones_achieved": self.milestones_achieved,
            "badges_earned": self.badges_earned,
            "records_broken": self.records_broken,
            "credits_earned": self.credits_earned,
            "impact_points_earned": self.impact_points_earned,
            "social_points_earned": self.social_points_earned,
            "multipliers_applied": self.multipliers_applied,
            "challenge_specific_data": self.challenge_specific_data,
            "interactions_summary": self.interactions_summary,
            "result_status": self.result_status,
            "is_verified": self.is_verified,
            "verified_by": self.verified_by,
            "verified_at": self.verified_at
        }

        if self._id:
            data["_id"] = self._id

        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChallengeResult':
        """Create a ChallengeResult instance from a dictionary"""
        result = cls(
            challenge_id=data.get("challenge_id", ""),
            user_id=data.get("user_id", ""),
            final_score=data.get("final_score", 0.0),
            rank=data.get("rank", 0),
            completion_percentage=data.get("completion_percentage", 0.0),
            started_at=data.get("started_at", datetime.utcnow()),
            completed_at=data.get("completed_at", datetime.utcnow()),
            total_duration_minutes=data.get("total_duration_minutes", 0),
            base_score=data.get("base_score", 0.0),
            bonus_scores=data.get("bonus_scores", {}),
            penalty_scores=data.get("penalty_scores", {}),
            social_engagement_score=data.get("social_engagement_score", 0.0),
            community_impact_score=data.get("community_impact_score", 0.0),
            friend_referral_bonus=data.get("friend_referral_bonus", 0.0),
            collaboration_score=data.get("collaboration_score", 0.0),
            milestones_achieved=data.get("milestones_achieved", []),
            badges_earned=data.get("badges_earned", []),
            records_broken=data.get("records_broken", []),
            credits_earned=data.get("credits_earned", 0),
            impact_points_earned=data.get("impact_points_earned", 0),
            social_points_earned=data.get("social_points_earned", 0),
            multipliers_applied=data.get("multipliers_applied", {}),
            challenge_specific_data=data.get("challenge_specific_data", {}),
            interactions_summary=data.get("interactions_summary", {}),
            result_status=data.get("result_status", "completed"),
            is_verified=data.get("is_verified", False),
            verified_by=data.get("verified_by"),
            verified_at=data.get("verified_at")
        )

        if "_id" in data:
            result._id = data["_id"]

        return result

    def to_api_dict(self, include_detailed: bool = False) -> Dict[str, Any]:
        """Convert the result to a dictionary for API responses"""
        api_data = {
            "id": str(self._id) if self._id else None,
            "challenge_id": self.challenge_id,
            "user_id": self.user_id,
            "performance": {
                "final_score": self.final_score,
                "rank": self.rank,
                "completion_percentage": self.completion_percentage
            },
            "timing": {
                "started_at": self.started_at.isoformat(),
                "completed_at": self.completed_at.isoformat(),
                "duration_minutes": self.total_duration_minutes
            },
            "social_impact": {
                "engagement_score": self.social_engagement_score,
                "community_impact": self.community_impact_score,
                "referral_bonus": self.friend_referral_bonus,
                "collaboration_score": self.collaboration_score
            },
            "achievements": {
                "milestones": len(self.milestones_achieved),
                "badges": len(self.badges_earned),
                "records": len(self.records_broken)
            },
            "rewards": {
                "credits_earned": self.credits_earned,
                "impact_points": self.impact_points_earned,
                "social_points": self.social_points_earned
            },
            "status": {
                "result_status": self.result_status,
                "is_verified": self.is_verified
            }
        }

        # Include detailed breakdown if requested
        if include_detailed:
            api_data["detailed_breakdown"] = {
                "base_score": self.base_score,
                "bonus_scores": self.bonus_scores,
                "penalty_scores": self.penalty_scores,
                "multipliers_applied": self.multipliers_applied,
                "milestones_achieved": self.milestones_achieved,
                "badges_earned": self.badges_earned,
                "records_broken": self.records_broken,
                "interactions_summary": self.interactions_summary,
                "challenge_specific_data": self.challenge_specific_data
            }

            if self.is_verified:
                api_data["verification"] = {
                    "verified_by": self.verified_by,
                    "verified_at": self.verified_at.isoformat() if self.verified_at else None
                }

        return api_data

    def calculate_final_score(self) -> float:
        """Calculate the final score from all components"""
        # Start with base score
        final = self.base_score

        # Add bonus scores
        for bonus_type, bonus_value in self.bonus_scores.items():
            final += bonus_value

        # Subtract penalty scores
        for penalty_type, penalty_value in self.penalty_scores.items():
            final -= penalty_value

        # Apply multipliers
        for multiplier_type, multiplier_value in self.multipliers_applied.items():
            final *= multiplier_value

        self.final_score = max(0.0, final)  # Ensure non-negative
        return self.final_score

    def add_bonus_score(self, bonus_type: str, amount: float, reason: str = "") -> None:
        """Add a bonus to the score"""
        if bonus_type not in self.bonus_scores:
            self.bonus_scores[bonus_type] = 0.0

        self.bonus_scores[bonus_type] += amount

        # Store reason in challenge-specific data
        if reason:
            if "bonus_reasons" not in self.challenge_specific_data:
                self.challenge_specific_data["bonus_reasons"] = {}
            self.challenge_specific_data["bonus_reasons"][bonus_type] = reason

    def add_penalty_score(self, penalty_type: str, amount: float, reason: str = "") -> None:
        """Add a penalty to the score"""
        if penalty_type not in self.penalty_scores:
            self.penalty_scores[penalty_type] = 0.0

        self.penalty_scores[penalty_type] += amount

        # Store reason in challenge-specific data
        if reason:
            if "penalty_reasons" not in self.challenge_specific_data:
                self.challenge_specific_data["penalty_reasons"] = {}
            self.challenge_specific_data["penalty_reasons"][penalty_type] = reason

    def apply_multiplier(self, multiplier_type: str, value: float) -> None:
        """Apply a score multiplier"""
        self.multipliers_applied[multiplier_type] = value

    def add_milestone(self, milestone: Dict[str, Any]) -> None:
        """Add a milestone achievement"""
        milestone["achieved_at"] = datetime.utcnow()
        self.milestones_achieved.append(milestone)

    def add_badge(self, badge_id: str, badge_name: str = "") -> None:
        """Add a badge earned during the challenge"""
        badge_data = {
            "badge_id": badge_id,
            "badge_name": badge_name,
            "earned_at": datetime.utcnow()
        }
        self.badges_earned.append(badge_data)

    def add_record_broken(self, record_type: str, old_value: float, new_value: float) -> None:
        """Record a personal or community record broken"""
        record = {
            "record_type": record_type,
            "old_value": old_value,
            "new_value": new_value,
            "broken_at": datetime.utcnow()
        }
        self.records_broken.append(record)

    def update_social_metrics(self, cheers_received: int, cheers_given: int,
                            comments_received: int, comments_made: int) -> None:
        """Update social interaction metrics"""
        # Store interaction counts
        self.interactions_summary = {
            "cheers_received": cheers_received,
            "cheers_given": cheers_given,
            "comments_received": comments_received,
            "comments_made": comments_made,
            "total_interactions": cheers_received + cheers_given + comments_received + comments_made
        }

        # Calculate social engagement score
        cheer_weight = 2.0
        comment_weight = 5.0

        self.social_engagement_score = (
            (cheers_received * cheer_weight) +
            (cheers_given * cheer_weight * 0.5) +
            (comments_received * comment_weight) +
            (comments_made * comment_weight * 0.3)
        )

    def calculate_community_impact(self, friends_invited: int, friends_joined: int,
                                 donation_amount: float = 0.0) -> None:
        """Calculate community impact score"""
        # Base impact from referrals
        referral_impact = friends_joined * 10  # 10 points per friend joined

        # Bonus for invitation conversion rate
        if friends_invited > 0:
            conversion_rate = friends_joined / friends_invited
            conversion_bonus = conversion_rate * 20  # Up to 20 bonus points
        else:
            conversion_bonus = 0

        # Impact from donations (if applicable)
        donation_impact = donation_amount * 0.1  # 0.1 points per dollar donated

        self.community_impact_score = referral_impact + conversion_bonus + donation_impact
        self.friend_referral_bonus = friends_joined * 5  # Credits bonus

    def verify_result(self, verifier_id: str) -> bool:
        """Verify the result (admin/system verification)"""
        if self.is_verified:
            return False

        self.is_verified = True
        self.verified_by = verifier_id
        self.verified_at = datetime.utcnow()
        return True

    def disqualify(self, reason: str) -> bool:
        """Disqualify the result"""
        if self.result_status == "completed":
            self.result_status = "disqualified"
            self.challenge_specific_data["disqualification_reason"] = reason
            self.challenge_specific_data["disqualified_at"] = datetime.utcnow()
            return True
        return False

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get a summary of performance metrics"""
        return {
            "score": self.final_score,
            "rank": self.rank,
            "completion": f"{self.completion_percentage:.1f}%",
            "duration": f"{self.total_duration_minutes} minutes",
            "social_engagement": self.social_engagement_score,
            "community_impact": self.community_impact_score,
            "achievements": {
                "milestones": len(self.milestones_achieved),
                "badges": len(self.badges_earned),
                "records": len(self.records_broken)
            }
        }

    def get_rewards_summary(self) -> Dict[str, Any]:
        """Get a summary of earned rewards"""
        total_bonus_credits = sum(self.bonus_scores.values())
        return {
            "credits_earned": self.credits_earned,
            "bonus_credits": int(total_bonus_credits),
            "impact_points": self.impact_points_earned,
            "social_points": self.social_points_earned,
            "badges_count": len(self.badges_earned),
            "multipliers": self.multipliers_applied
        }

    @staticmethod
    def create_from_participant(participant, challenge_rules: Dict[str, Any]) -> 'ChallengeResult':
        """Create a result from a participant's final state"""
        from .challenge_participant import ChallengeParticipant

        if not isinstance(participant, ChallengeParticipant):
            raise ValueError("participant must be a ChallengeParticipant instance")

        result = ChallengeResult(
            challenge_id=participant.challenge_id,
            user_id=participant.user_id,
            final_score=participant.final_score,
            rank=participant.final_rank,
            completion_percentage=participant.completion_percentage,
            started_at=participant.joined_at,
            completed_at=participant.completed_at or datetime.utcnow(),
            base_score=participant.final_score,
            credits_earned=participant.credits_earned,
            social_points_earned=int(participant.social_score)
        )

        # Copy social metrics
        result.update_social_metrics(
            participant.cheers_received,
            participant.cheers_given,
            participant.comments_received,
            participant.comments_made
        )

        # Copy community impact
        result.calculate_community_impact(
            participant.friends_invited,
            participant.friends_joined,
            participant.community_impact
        )

        # Copy achievements
        if hasattr(participant, 'milestones_reached') and participant.milestones_reached > 0:
            for i in range(participant.milestones_reached):
                result.add_milestone({
                    "milestone_number": i + 1,
                    "description": f"Milestone {i + 1} reached"
                })

        return result

    def __str__(self) -> str:
        return f"ChallengeResult(user={self.user_id}, score={self.final_score}, rank={self.rank})"

    def __repr__(self) -> str:
        return self.__str__()