from datetime import datetime
from typing import Dict, Any, Optional
from bson import ObjectId
from dataclasses import dataclass, field

@dataclass
class ChallengeParticipant:
    """Participant in a social challenge with social-specific tracking"""
    challenge_id: str
    user_id: str
    joined_at: datetime = field(default_factory=datetime.utcnow)
    status: str = "active"  # 'active', 'completed', 'quit', 'disqualified'

    # Social Progress Tracking
    current_progress: Dict[str, Any] = field(default_factory=dict)
    progress_updates: int = 0
    last_progress_update: Optional[datetime] = None

    # Social Interactions
    cheers_received: int = 0
    cheers_given: int = 0
    comments_received: int = 0
    comments_made: int = 0
    social_score: float = 0.0  # Based on interactions and engagement

    # Achievement Tracking
    milestones_reached: int = 0
    achievements_earned: int = 0
    streak_days: int = 0
    best_rank: int = 0

    # Final Results
    final_score: float = 0.0
    final_rank: int = 0
    completion_percentage: float = 0.0
    completed_at: Optional[datetime] = None

    # Rewards Tracking
    credits_earned: int = 0
    badges_earned: list = field(default_factory=list)
    bonus_multipliers: Dict[str, float] = field(default_factory=dict)
    rewards_claimed: bool = False
    rewards_claimed_at: Optional[datetime] = None

    # Social Impact Metrics
    friends_invited: int = 0
    friends_joined: int = 0
    community_impact: float = 0.0
    referral_bonus: float = 0.0

    _id: Optional[ObjectId] = field(default=None)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the participant to a dictionary for MongoDB storage"""
        data = {
            "challenge_id": self.challenge_id,
            "user_id": self.user_id,
            "joined_at": self.joined_at,
            "status": self.status,
            "current_progress": self.current_progress,
            "progress_updates": self.progress_updates,
            "last_progress_update": self.last_progress_update,
            "cheers_received": self.cheers_received,
            "cheers_given": self.cheers_given,
            "comments_received": self.comments_received,
            "comments_made": self.comments_made,
            "social_score": self.social_score,
            "milestones_reached": self.milestones_reached,
            "achievements_earned": self.achievements_earned,
            "streak_days": self.streak_days,
            "best_rank": self.best_rank,
            "final_score": self.final_score,
            "final_rank": self.final_rank,
            "completion_percentage": self.completion_percentage,
            "completed_at": self.completed_at,
            "credits_earned": self.credits_earned,
            "badges_earned": self.badges_earned,
            "bonus_multipliers": self.bonus_multipliers,
            "rewards_claimed": self.rewards_claimed,
            "rewards_claimed_at": self.rewards_claimed_at,
            "friends_invited": self.friends_invited,
            "friends_joined": self.friends_joined,
            "community_impact": self.community_impact,
            "referral_bonus": self.referral_bonus
        }

        if self._id:
            data["_id"] = self._id

        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChallengeParticipant':
        """Create a ChallengeParticipant instance from a dictionary"""
        participant = cls(
            challenge_id=data.get("challenge_id", ""),
            user_id=data.get("user_id", ""),
            joined_at=data.get("joined_at", datetime.utcnow()),
            status=data.get("status", "active"),
            current_progress=data.get("current_progress", {}),
            progress_updates=data.get("progress_updates", 0),
            last_progress_update=data.get("last_progress_update"),
            cheers_received=data.get("cheers_received", 0),
            cheers_given=data.get("cheers_given", 0),
            comments_received=data.get("comments_received", 0),
            comments_made=data.get("comments_made", 0),
            social_score=data.get("social_score", 0.0),
            milestones_reached=data.get("milestones_reached", 0),
            achievements_earned=data.get("achievements_earned", 0),
            streak_days=data.get("streak_days", 0),
            best_rank=data.get("best_rank", 0),
            final_score=data.get("final_score", 0.0),
            final_rank=data.get("final_rank", 0),
            completion_percentage=data.get("completion_percentage", 0.0),
            completed_at=data.get("completed_at"),
            credits_earned=data.get("credits_earned", 0),
            badges_earned=data.get("badges_earned", []),
            bonus_multipliers=data.get("bonus_multipliers", {}),
            rewards_claimed=data.get("rewards_claimed", False),
            rewards_claimed_at=data.get("rewards_claimed_at"),
            friends_invited=data.get("friends_invited", 0),
            friends_joined=data.get("friends_joined", 0),
            community_impact=data.get("community_impact", 0.0),
            referral_bonus=data.get("referral_bonus", 0.0)
        )

        if "_id" in data:
            participant._id = data["_id"]

        return participant

    def to_api_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """Convert the participant to a dictionary for API responses"""
        api_data = {
            "id": str(self._id) if self._id else None,
            "challenge_id": self.challenge_id,
            "user_id": self.user_id,
            "joined_at": self.joined_at.isoformat(),
            "status": self.status,
            "progress": {
                "current": self.current_progress,
                "updates_count": self.progress_updates,
                "last_updated": self.last_progress_update.isoformat() if self.last_progress_update else None,
                "completion_percentage": self.completion_percentage
            },
            "social_engagement": {
                "cheers_received": self.cheers_received,
                "cheers_given": self.cheers_given,
                "comments_received": self.comments_received,
                "comments_made": self.comments_made,
                "social_score": self.social_score
            },
            "achievements": {
                "milestones_reached": self.milestones_reached,
                "achievements_earned": self.achievements_earned,
                "streak_days": self.streak_days,
                "best_rank": self.best_rank
            },
            "results": {
                "final_score": self.final_score,
                "final_rank": self.final_rank,
                "completed_at": self.completed_at.isoformat() if self.completed_at else None
            },
            "community_impact": {
                "friends_invited": self.friends_invited,
                "friends_joined": self.friends_joined,
                "impact_score": self.community_impact,
                "referral_bonus": self.referral_bonus
            }
        }

        # Include sensitive information only if requested (for owner/admin)
        if include_sensitive:
            api_data["rewards"] = {
                "credits_earned": self.credits_earned,
                "badges_earned": self.badges_earned,
                "bonus_multipliers": self.bonus_multipliers,
                "claimed": self.rewards_claimed,
                "claimed_at": self.rewards_claimed_at.isoformat() if self.rewards_claimed_at else None
            }

        return api_data

    def update_progress(self, progress_data: Dict[str, Any]) -> bool:
        """Update participant's progress"""
        try:
            self.current_progress.update(progress_data)
            self.progress_updates += 1
            self.last_progress_update = datetime.utcnow()

            # Calculate completion percentage based on target
            if "target_value" in progress_data and progress_data["target_value"] > 0:
                current_value = progress_data.get("current_value", 0)
                self.completion_percentage = min(100.0, (current_value / progress_data["target_value"]) * 100)

            return True
        except Exception:
            return False

    def add_social_interaction(self, interaction_type: str, count: int = 1) -> bool:
        """Add social interaction (cheer, comment)"""
        try:
            if interaction_type == "cheer_received":
                self.cheers_received += count
            elif interaction_type == "cheer_given":
                self.cheers_given += count
            elif interaction_type == "comment_received":
                self.comments_received += count
            elif interaction_type == "comment_made":
                self.comments_made += count

            # Update social score
            self._calculate_social_score()
            return True
        except Exception:
            return False

    def _calculate_social_score(self) -> None:
        """Calculate social engagement score"""
        # Weight different interactions
        cheer_weight = 2.0
        comment_weight = 5.0
        engagement_bonus = 1.5

        raw_score = (
            (self.cheers_received * cheer_weight) +
            (self.cheers_given * cheer_weight * 0.5) +  # Giving cheers is worth less
            (self.comments_received * comment_weight) +
            (self.comments_made * comment_weight * 0.3)
        )

        # Bonus for being both active and engaging with others
        if self.cheers_given > 0 and self.comments_made > 0:
            raw_score *= engagement_bonus

        self.social_score = round(raw_score, 2)

    def reach_milestone(self, milestone_data: Dict[str, Any]) -> bool:
        """Record reaching a milestone"""
        try:
            self.milestones_reached += 1
            if "achievement" in milestone_data:
                self.achievements_earned += 1
            return True
        except Exception:
            return False

    def update_rank(self, new_rank: int) -> bool:
        """Update participant's current rank"""
        try:
            if self.best_rank == 0 or new_rank < self.best_rank:
                self.best_rank = new_rank
            return True
        except Exception:
            return False

    def complete_participation(self, final_score: float, final_rank: int) -> bool:
        """Mark participation as completed"""
        try:
            self.status = "completed"
            self.final_score = final_score
            self.final_rank = final_rank
            self.completed_at = datetime.utcnow()

            if self.best_rank == 0:
                self.best_rank = final_rank

            return True
        except Exception:
            return False

    def quit_challenge(self) -> bool:
        """Mark participant as quit"""
        if self.status in ["completed", "disqualified"]:
            return False

        self.status = "quit"
        return True

    def disqualify(self, reason: str = "") -> bool:
        """Disqualify participant"""
        if self.status == "completed":
            return False

        self.status = "disqualified"
        # Store reason in progress data
        self.current_progress["disqualification_reason"] = reason
        return True

    def calculate_rewards(self, base_credits: int, social_bonus: float = 1.0) -> Dict[str, Any]:
        """Calculate total rewards including social bonuses"""
        # Base credits
        total_credits = base_credits

        # Social engagement bonus
        social_multiplier = 1.0 + (self.social_score / 100)  # Up to 2x multiplier
        social_multiplier = min(social_multiplier, social_bonus)

        # Referral bonus
        referral_multiplier = 1.0 + (self.friends_joined * 0.1)  # 10% per friend joined

        # Community impact bonus
        impact_multiplier = 1.0 + (self.community_impact / 1000)  # Scale based on impact

        # Apply all multipliers
        final_multiplier = social_multiplier * referral_multiplier * impact_multiplier
        total_credits = int(total_credits * final_multiplier)

        # Store multipliers for transparency
        self.bonus_multipliers = {
            "social": social_multiplier,
            "referral": referral_multiplier,
            "impact": impact_multiplier,
            "total": final_multiplier
        }

        return {
            "base_credits": base_credits,
            "total_credits": total_credits,
            "multipliers": self.bonus_multipliers,
            "social_score": self.social_score,
            "community_impact": self.community_impact
        }

    def claim_rewards(self, credits: int, badges: list = None) -> bool:
        """Claim rewards for participation"""
        if self.rewards_claimed:
            return False

        try:
            self.credits_earned = credits
            self.badges_earned = badges or []
            self.rewards_claimed = True
            self.rewards_claimed_at = datetime.utcnow()
            return True
        except Exception:
            return False

    def is_active(self) -> bool:
        """Check if participant is actively participating"""
        return self.status == "active"

    def is_completed(self) -> bool:
        """Check if participant has completed the challenge"""
        return self.status == "completed"

    def get_engagement_level(self) -> str:
        """Get engagement level based on social interactions"""
        total_interactions = self.cheers_received + self.cheers_given + self.comments_received + self.comments_made

        if total_interactions == 0:
            return "none"
        elif total_interactions < 5:
            return "low"
        elif total_interactions < 15:
            return "medium"
        elif total_interactions < 30:
            return "high"
        else:
            return "very_high"

    def get_days_participated(self) -> int:
        """Get number of days since joining"""
        return (datetime.utcnow() - self.joined_at).days + 1

    def __str__(self) -> str:
        return f"ChallengeParticipant(user={self.user_id}, challenge={self.challenge_id}, status={self.status})"

    def __repr__(self) -> str:
        return self.__str__()