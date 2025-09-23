from datetime import datetime
from typing import Optional, Dict, Any
from bson import ObjectId


class UserAchievement:
    """
    Model for user achievement progress tracking

    Collection: user_achievements
    """

    def __init__(self, user_id: str, achievement_id: str, progress: int = 0,
                 max_progress: int = 1, is_completed: bool = False,
                 completed_at: Optional[datetime] = None, reward_claimed: bool = False,
                 claimed_at: Optional[datetime] = None, _id: Optional[str] = None,
                 created_at: Optional[datetime] = None, updated_at: Optional[datetime] = None):
        """
        Initialize UserAchievement

        Args:
            user_id: ID of the user
            achievement_id: ID of the achievement
            progress: Current progress value
            max_progress: Maximum progress needed to complete
            is_completed: Whether achievement is completed
            completed_at: Timestamp when achievement was completed
            reward_claimed: Whether reward has been claimed
            claimed_at: Timestamp when reward was claimed
            _id: MongoDB document ID
            created_at: Creation timestamp
            updated_at: Last update timestamp
        """
        self._id = ObjectId(_id) if _id else ObjectId()
        self.user_id = ObjectId(user_id)
        self.achievement_id = achievement_id
        self.progress = progress
        self.max_progress = max_progress
        self.is_completed = is_completed
        self.completed_at = completed_at
        self.reward_claimed = reward_claimed
        self.claimed_at = claimed_at
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()

        self._validate()

    def _validate(self):
        """Validate user achievement data"""
        if self.progress < 0:
            raise ValueError("Progress cannot be negative")

        if self.max_progress <= 0:
            raise ValueError("Max progress must be positive")

        if self.progress > self.max_progress:
            raise ValueError("Progress cannot exceed max progress")

        if self.is_completed and not self.completed_at:
            self.completed_at = datetime.utcnow()

        if self.reward_claimed and not self.claimed_at:
            self.claimed_at = datetime.utcnow()

        if self.reward_claimed and not self.is_completed:
            raise ValueError("Cannot claim reward for incomplete achievement")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB storage"""
        return {
            '_id': self._id,
            'user_id': self.user_id,
            'achievement_id': self.achievement_id,
            'progress': self.progress,
            'max_progress': self.max_progress,
            'is_completed': self.is_completed,
            'completed_at': self.completed_at,
            'reward_claimed': self.reward_claimed,
            'claimed_at': self.claimed_at,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserAchievement':
        """Create UserAchievement from dictionary"""
        return cls(
            user_id=str(data['user_id']),
            achievement_id=data['achievement_id'],
            progress=data.get('progress', 0),
            max_progress=data.get('max_progress', 1),
            is_completed=data.get('is_completed', False),
            completed_at=data.get('completed_at'),
            reward_claimed=data.get('reward_claimed', False),
            claimed_at=data.get('claimed_at'),
            _id=str(data['_id']) if '_id' in data else None,
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )

    def to_response_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            'id': str(self._id),
            'user_id': str(self.user_id),
            'achievement_id': self.achievement_id,
            'progress': self.progress,
            'max_progress': self.max_progress,
            'progress_percentage': self.get_progress_percentage(),
            'is_completed': self.is_completed,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'reward_claimed': self.reward_claimed,
            'claimed_at': self.claimed_at.isoformat() if self.claimed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def update_progress(self, new_progress: int) -> bool:
        """
        Update progress and check for completion

        Args:
            new_progress: New progress value

        Returns:
            bool: True if achievement was just completed
        """
        if new_progress < 0:
            raise ValueError("Progress cannot be negative")

        old_progress = self.progress
        self.progress = min(new_progress, self.max_progress)
        self.updated_at = datetime.utcnow()

        # Check for completion
        was_completed = self.is_completed
        if self.progress >= self.max_progress and not self.is_completed:
            self.is_completed = True
            self.completed_at = datetime.utcnow()
            return True  # Just completed

        return False  # Not just completed

    def increment_progress(self, increment: int = 1) -> bool:
        """
        Increment progress by specified amount

        Args:
            increment: Amount to increment progress

        Returns:
            bool: True if achievement was just completed
        """
        return self.update_progress(self.progress + increment)

    def claim_reward(self) -> bool:
        """
        Claim the achievement reward

        Returns:
            bool: True if reward was successfully claimed
        """
        if not self.is_completed:
            raise ValueError("Cannot claim reward for incomplete achievement")

        if self.reward_claimed:
            return False  # Already claimed

        self.reward_claimed = True
        self.claimed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        return True

    def get_progress_percentage(self) -> float:
        """Get progress as percentage (0-100)"""
        if self.max_progress == 0:
            return 0.0
        return min(100.0, (self.progress / self.max_progress) * 100.0)

    def is_ready_to_claim(self) -> bool:
        """Check if reward is ready to claim"""
        return self.is_completed and not self.reward_claimed

    def reset_progress(self):
        """Reset progress (for repeatable achievements)"""
        self.progress = 0
        self.is_completed = False
        self.completed_at = None
        self.reward_claimed = False
        self.claimed_at = None
        self.updated_at = datetime.utcnow()

    def get_time_to_complete(self) -> Optional[float]:
        """Get time taken to complete in seconds"""
        if not self.completed_at or not self.created_at:
            return None

        delta = self.completed_at - self.created_at
        return delta.total_seconds()

    def get_time_to_claim(self) -> Optional[float]:
        """Get time between completion and claiming in seconds"""
        if not self.claimed_at or not self.completed_at:
            return None

        delta = self.claimed_at - self.completed_at
        return delta.total_seconds()