from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from bson import ObjectId
from dataclasses import dataclass, field
import uuid

@dataclass
class ChallengeRules:
    """Rules configuration for a social challenge"""
    target_metric: str  # 'games_played', 'friends_invited', 'donation_amount', etc.
    target_value: float
    time_limit_hours: Optional[int] = None
    min_participants: int = 2
    max_participants: int = 10
    requires_friends: bool = True
    allow_public_join: bool = False
    scoring_method: str = "highest"  # 'highest', 'lowest', 'target', 'collective'
    difficulty_multiplier: float = 1.0

@dataclass
class ChallengeRewards:
    """Rewards configuration for challenge completion"""
    winner_credits: int = 0
    participant_credits: int = 0
    winner_badges: List[str] = field(default_factory=list)
    participant_badges: List[str] = field(default_factory=list)
    social_bonus_multiplier: float = 1.0
    impact_multiplier: float = 1.0
    special_rewards: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SocialChallenge:
    """Social Challenge model for friend interactions and community challenges"""
    challenge_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    creator_id: str = ""
    title: str = ""
    description: str = ""
    challenge_type: str = "social"  # 'gaming_social', 'social_engagement', 'impact_challenge'
    challenge_category: str = ""  # 'speed_run', 'friend_referral', 'donation_race', etc.
    difficulty_level: int = 1  # 1-5 scale
    tags: List[str] = field(default_factory=list)

    # Challenge Configuration
    rules: ChallengeRules = field(default_factory=lambda: ChallengeRules(target_metric="", target_value=0))
    rewards: ChallengeRewards = field(default_factory=ChallengeRewards)

    # Participation Management
    max_participants: int = 10
    current_participants: int = 0
    invited_user_ids: List[str] = field(default_factory=list)
    participant_ids: List[str] = field(default_factory=list)

    # Timing
    created_at: datetime = field(default_factory=datetime.utcnow)
    start_date: datetime = field(default_factory=datetime.utcnow)
    end_date: datetime = field(default_factory=lambda: datetime.utcnow() + timedelta(days=7))

    # Status Management
    status: str = "open"  # 'open', 'active', 'completed', 'cancelled'
    is_public: bool = False
    friends_only: bool = True

    # Social Features
    allow_cheering: bool = True
    allow_comments: bool = True
    allow_spectators: bool = True

    # Progress & Results
    leaderboard_data: List[Dict[str, Any]] = field(default_factory=list)
    winner_ids: List[str] = field(default_factory=list)
    completion_percentage: float = 0.0

    # Metadata
    _id: Optional[ObjectId] = field(default=None)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the social challenge to a dictionary for MongoDB storage"""
        data = {
            "challenge_id": self.challenge_id,
            "creator_id": self.creator_id,
            "title": self.title,
            "description": self.description,
            "challenge_type": self.challenge_type,
            "challenge_category": self.challenge_category,
            "difficulty_level": self.difficulty_level,
            "tags": self.tags,
            "rules": {
                "target_metric": self.rules.target_metric,
                "target_value": self.rules.target_value,
                "time_limit_hours": self.rules.time_limit_hours,
                "min_participants": self.rules.min_participants,
                "max_participants": self.rules.max_participants,
                "requires_friends": self.rules.requires_friends,
                "allow_public_join": self.rules.allow_public_join,
                "scoring_method": self.rules.scoring_method,
                "difficulty_multiplier": self.rules.difficulty_multiplier
            },
            "rewards": {
                "winner_credits": self.rewards.winner_credits,
                "participant_credits": self.rewards.participant_credits,
                "winner_badges": self.rewards.winner_badges,
                "participant_badges": self.rewards.participant_badges,
                "social_bonus_multiplier": self.rewards.social_bonus_multiplier,
                "impact_multiplier": self.rewards.impact_multiplier,
                "special_rewards": self.rewards.special_rewards
            },
            "max_participants": self.max_participants,
            "current_participants": self.current_participants,
            "invited_user_ids": self.invited_user_ids,
            "participant_ids": self.participant_ids,
            "created_at": self.created_at,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "status": self.status,
            "is_public": self.is_public,
            "friends_only": self.friends_only,
            "allow_cheering": self.allow_cheering,
            "allow_comments": self.allow_comments,
            "allow_spectators": self.allow_spectators,
            "leaderboard_data": self.leaderboard_data,
            "winner_ids": self.winner_ids,
            "completion_percentage": self.completion_percentage
        }

        if self._id:
            data["_id"] = self._id

        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SocialChallenge':
        """Create a SocialChallenge instance from a dictionary"""
        # Parse rules
        rules_data = data.get("rules", {})
        rules = ChallengeRules(
            target_metric=rules_data.get("target_metric", ""),
            target_value=rules_data.get("target_value", 0),
            time_limit_hours=rules_data.get("time_limit_hours"),
            min_participants=rules_data.get("min_participants", 2),
            max_participants=rules_data.get("max_participants", 10),
            requires_friends=rules_data.get("requires_friends", True),
            allow_public_join=rules_data.get("allow_public_join", False),
            scoring_method=rules_data.get("scoring_method", "highest"),
            difficulty_multiplier=rules_data.get("difficulty_multiplier", 1.0)
        )

        # Parse rewards
        rewards_data = data.get("rewards", {})
        rewards = ChallengeRewards(
            winner_credits=rewards_data.get("winner_credits", 0),
            participant_credits=rewards_data.get("participant_credits", 0),
            winner_badges=rewards_data.get("winner_badges", []),
            participant_badges=rewards_data.get("participant_badges", []),
            social_bonus_multiplier=rewards_data.get("social_bonus_multiplier", 1.0),
            impact_multiplier=rewards_data.get("impact_multiplier", 1.0),
            special_rewards=rewards_data.get("special_rewards", {})
        )

        challenge = cls(
            challenge_id=data.get("challenge_id", str(uuid.uuid4())),
            creator_id=data.get("creator_id", ""),
            title=data.get("title", ""),
            description=data.get("description", ""),
            challenge_type=data.get("challenge_type", "social"),
            challenge_category=data.get("challenge_category", ""),
            difficulty_level=data.get("difficulty_level", 1),
            tags=data.get("tags", []),
            rules=rules,
            rewards=rewards,
            max_participants=data.get("max_participants", 10),
            current_participants=data.get("current_participants", 0),
            invited_user_ids=data.get("invited_user_ids", []),
            participant_ids=data.get("participant_ids", []),
            created_at=data.get("created_at", datetime.utcnow()),
            start_date=data.get("start_date", datetime.utcnow()),
            end_date=data.get("end_date", datetime.utcnow() + timedelta(days=7)),
            status=data.get("status", "open"),
            is_public=data.get("is_public", False),
            friends_only=data.get("friends_only", True),
            allow_cheering=data.get("allow_cheering", True),
            allow_comments=data.get("allow_comments", True),
            allow_spectators=data.get("allow_spectators", True),
            leaderboard_data=data.get("leaderboard_data", []),
            winner_ids=data.get("winner_ids", []),
            completion_percentage=data.get("completion_percentage", 0.0)
        )

        if "_id" in data:
            challenge._id = data["_id"]

        return challenge

    def to_api_dict(self) -> Dict[str, Any]:
        """Convert the challenge to a dictionary for API responses"""
        return {
            "id": str(self._id) if self._id else None,
            "challenge_id": self.challenge_id,
            "creator_id": self.creator_id,
            "title": self.title,
            "description": self.description,
            "challenge_type": self.challenge_type,
            "challenge_category": self.challenge_category,
            "difficulty_level": self.difficulty_level,
            "tags": self.tags,
            "rules": {
                "target_metric": self.rules.target_metric,
                "target_value": self.rules.target_value,
                "time_limit_hours": self.rules.time_limit_hours,
                "min_participants": self.rules.min_participants,
                "max_participants": self.rules.max_participants,
                "requires_friends": self.rules.requires_friends,
                "allow_public_join": self.rules.allow_public_join,
                "scoring_method": self.rules.scoring_method,
                "difficulty_multiplier": self.rules.difficulty_multiplier
            },
            "rewards": {
                "winner_credits": self.rewards.winner_credits,
                "participant_credits": self.rewards.participant_credits,
                "winner_badges": self.rewards.winner_badges,
                "participant_badges": self.rewards.participant_badges,
                "social_bonus_multiplier": self.rewards.social_bonus_multiplier,
                "impact_multiplier": self.rewards.impact_multiplier
            },
            "max_participants": self.max_participants,
            "current_participants": self.current_participants,
            "participant_count": len(self.participant_ids),
            "invited_count": len(self.invited_user_ids),
            "created_at": self.created_at.isoformat(),
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "status": self.status,
            "is_public": self.is_public,
            "friends_only": self.friends_only,
            "social_features": {
                "allow_cheering": self.allow_cheering,
                "allow_comments": self.allow_comments,
                "allow_spectators": self.allow_spectators
            },
            "leaderboard_data": self.leaderboard_data,
            "winner_ids": self.winner_ids,
            "completion_percentage": self.completion_percentage,
            "time_remaining_hours": self.get_time_remaining_hours(),
            "can_join": self.can_user_join(),
            "is_active": self.is_active(),
            "is_expired": self.is_expired()
        }

    # Challenge Lifecycle Methods
    def can_user_join(self, user_id: str = None) -> bool:
        """Check if a user can join this challenge"""
        if self.status != "open":
            return False

        if self.is_expired():
            return False

        if self.current_participants >= self.max_participants:
            return False

        if user_id and user_id in self.participant_ids:
            return False  # Already joined

        return True

    def add_participant(self, user_id: str) -> bool:
        """Add a participant to the challenge"""
        if not self.can_user_join(user_id):
            return False

        if user_id not in self.participant_ids:
            self.participant_ids.append(user_id)
            self.current_participants = len(self.participant_ids)

            # Remove from invited list if present
            if user_id in self.invited_user_ids:
                self.invited_user_ids.remove(user_id)

        return True

    def remove_participant(self, user_id: str) -> bool:
        """Remove a participant from the challenge"""
        if user_id == self.creator_id:
            return False  # Cannot remove creator

        if user_id in self.participant_ids:
            self.participant_ids.remove(user_id)
            self.current_participants = len(self.participant_ids)
            return True

        return False

    def invite_user(self, user_id: str) -> bool:
        """Invite a user to the challenge"""
        if user_id in self.invited_user_ids or user_id in self.participant_ids:
            return False  # Already invited or joined

        self.invited_user_ids.append(user_id)
        return True

    def start_challenge(self) -> bool:
        """Start the challenge if conditions are met"""
        if self.status != "open":
            return False

        if self.current_participants < self.rules.min_participants:
            return False

        self.status = "active"
        self.start_date = datetime.utcnow()
        return True

    def complete_challenge(self, results: List[Dict[str, Any]] = None) -> bool:
        """Complete the challenge"""
        if self.status not in ["active", "open"]:
            return False

        self.status = "completed"
        self.completion_percentage = 100.0

        if results:
            self.leaderboard_data = results
            # Determine winners based on scoring method
            if self.rules.scoring_method == "highest" and results:
                sorted_results = sorted(results, key=lambda x: x.get("score", 0), reverse=True)
                if sorted_results:
                    highest_score = sorted_results[0].get("score", 0)
                    self.winner_ids = [
                        r["user_id"] for r in sorted_results
                        if r.get("score", 0) == highest_score
                    ]

        return True

    def cancel_challenge(self) -> bool:
        """Cancel the challenge"""
        if self.status in ["completed", "cancelled"]:
            return False

        self.status = "cancelled"
        return True

    # Utility Methods
    def is_active(self) -> bool:
        """Check if challenge is currently active"""
        return self.status == "active" and not self.is_expired()

    def is_expired(self) -> bool:
        """Check if challenge has expired"""
        return datetime.utcnow() > self.end_date

    def get_time_remaining_hours(self) -> Optional[float]:
        """Get time remaining in hours"""
        if self.is_expired():
            return 0

        now = datetime.utcnow()
        if now >= self.end_date:
            return 0

        return (self.end_date - now).total_seconds() / 3600

    def is_participant(self, user_id: str) -> bool:
        """Check if user is a participant"""
        return user_id in self.participant_ids

    def is_invited(self, user_id: str) -> bool:
        """Check if user is invited"""
        return user_id in self.invited_user_ids

    def update_progress(self, user_id: str, progress_data: Dict[str, Any]) -> bool:
        """Update progress for a participant"""
        if not self.is_participant(user_id):
            return False

        # Find or create participant entry in leaderboard
        participant_entry = None
        for entry in self.leaderboard_data:
            if entry.get("user_id") == user_id:
                participant_entry = entry
                break

        if not participant_entry:
            participant_entry = {"user_id": user_id}
            self.leaderboard_data.append(participant_entry)

        # Update progress data
        participant_entry.update(progress_data)
        participant_entry["last_updated"] = datetime.utcnow()

        # Calculate completion percentage
        if self.rules.target_value > 0:
            current_value = progress_data.get("current_value", 0)
            self.completion_percentage = min(100.0, (current_value / self.rules.target_value) * 100)

        return True

    @staticmethod
    def create_gaming_social_challenge(
        creator_id: str,
        title: str,
        game_category: str,
        target_value: float,
        duration_hours: int = 168
    ) -> 'SocialChallenge':
        """Create a gaming social challenge (Speed Run, High Score, etc.)"""
        end_date = datetime.utcnow() + timedelta(hours=duration_hours)

        rules = ChallengeRules(
            target_metric=f"gaming_{game_category}",
            target_value=target_value,
            time_limit_hours=duration_hours,
            scoring_method="highest",
            requires_friends=True
        )

        rewards = ChallengeRewards(
            winner_credits=100,
            participant_credits=25,
            winner_badges=["social_gaming_champion"],
            social_bonus_multiplier=1.5
        )

        return SocialChallenge(
            creator_id=creator_id,
            title=title,
            description=f"Social gaming challenge: {game_category}",
            challenge_type="gaming_social",
            challenge_category=game_category,
            end_date=end_date,
            rules=rules,
            rewards=rewards
        )

    @staticmethod
    def create_social_engagement_challenge(
        creator_id: str,
        title: str,
        engagement_type: str,
        target_value: float,
        duration_hours: int = 168
    ) -> 'SocialChallenge':
        """Create a social engagement challenge (Friend Referral, etc.)"""
        end_date = datetime.utcnow() + timedelta(hours=duration_hours)

        rules = ChallengeRules(
            target_metric=f"social_{engagement_type}",
            target_value=target_value,
            time_limit_hours=duration_hours,
            scoring_method="highest",
            requires_friends=True
        )

        rewards = ChallengeRewards(
            winner_credits=150,
            participant_credits=50,
            winner_badges=["community_builder"],
            social_bonus_multiplier=2.0
        )

        return SocialChallenge(
            creator_id=creator_id,
            title=title,
            description=f"Social engagement challenge: {engagement_type}",
            challenge_type="social_engagement",
            challenge_category=engagement_type,
            end_date=end_date,
            rules=rules,
            rewards=rewards
        )

    @staticmethod
    def create_impact_challenge(
        creator_id: str,
        title: str,
        impact_type: str,
        target_value: float,
        duration_hours: int = 168
    ) -> 'SocialChallenge':
        """Create an impact challenge (Donation Race, etc.)"""
        end_date = datetime.utcnow() + timedelta(hours=duration_hours)

        rules = ChallengeRules(
            target_metric=f"impact_{impact_type}",
            target_value=target_value,
            time_limit_hours=duration_hours,
            scoring_method="highest" if impact_type != "collective" else "collective",
            requires_friends=False,
            allow_public_join=True
        )

        rewards = ChallengeRewards(
            winner_credits=200,
            participant_credits=75,
            winner_badges=["impact_champion"],
            impact_multiplier=2.0,
            social_bonus_multiplier=1.2
        )

        return SocialChallenge(
            creator_id=creator_id,
            title=title,
            description=f"Impact challenge: {impact_type}",
            challenge_type="impact_challenge",
            challenge_category=impact_type,
            end_date=end_date,
            rules=rules,
            rewards=rewards,
            is_public=True,
            friends_only=False
        )

    def __str__(self) -> str:
        return f"SocialChallenge(id={self._id}, title={self.title}, status={self.status})"

    def __repr__(self) -> str:
        return self.__str__()