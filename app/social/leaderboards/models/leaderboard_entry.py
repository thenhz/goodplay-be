from datetime import datetime
from typing import Optional, Dict, Any
from bson import ObjectId


class LeaderboardEntry:
    """
    Model for individual leaderboard entries

    Represents a single user's position and data within a leaderboard
    """

    def __init__(self, user_id: str, score: float, rank: int,
                 display_name: str, user_data: Optional[Dict] = None,
                 score_components: Optional[Dict] = None,
                 _id: Optional[str] = None,
                 created_at: Optional[datetime] = None):
        """
        Initialize LeaderboardEntry

        Args:
            user_id: ID of the user this entry represents
            score: User's score for this leaderboard
            rank: User's rank position (1-based)
            display_name: User's display name
            user_data: Additional user profile data for display
            score_components: Breakdown of score components
            _id: MongoDB document ID
            created_at: Creation timestamp
        """
        self._id = ObjectId(_id) if _id else ObjectId()
        self.user_id = ObjectId(user_id)
        self.score = score
        self.rank = rank
        self.display_name = display_name
        self.created_at = created_at or datetime.utcnow()

        # Optional user profile data for rich leaderboard display
        self.user_data = user_data or {
            'avatar_url': None,
            'level': 1,
            'badge_count': 0,
            'join_date': None
        }

        # Score breakdown for detailed view
        self.score_components = score_components or {}

        self._validate()

    def _validate(self):
        """Validate leaderboard entry data"""
        if self.score < 0:
            raise ValueError("Score cannot be negative")

        if self.rank < 1:
            raise ValueError("Rank must be positive")

        if not self.display_name or not self.display_name.strip():
            raise ValueError("Display name is required")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB storage"""
        return {
            '_id': self._id,
            'user_id': self.user_id,
            'score': self.score,
            'rank': self.rank,
            'display_name': self.display_name,
            'user_data': self.user_data,
            'score_components': self.score_components,
            'created_at': self.created_at
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LeaderboardEntry':
        """Create LeaderboardEntry from dictionary"""
        return cls(
            user_id=str(data['user_id']),
            score=data['score'],
            rank=data['rank'],
            display_name=data['display_name'],
            user_data=data.get('user_data', {}),
            score_components=data.get('score_components', {}),
            _id=str(data['_id']) if '_id' in data else None,
            created_at=data.get('created_at')
        )

    def to_response_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            'user_id': str(self.user_id),
            'score': self.score,
            'rank': self.rank,
            'display_name': self.display_name,
            'user_profile': {
                'avatar_url': self.user_data.get('avatar_url'),
                'level': self.user_data.get('level', 1),
                'badge_count': self.user_data.get('badge_count', 0),
                'member_since': self.user_data.get('join_date').isoformat()
                               if self.user_data.get('join_date') else None
            },
            'score_breakdown': self.score_components,
            'last_updated': self.created_at.isoformat() if self.created_at else None
        }

    def update_rank(self, new_rank: int):
        """Update the rank position"""
        if new_rank < 1:
            raise ValueError("Rank must be positive")
        self.rank = new_rank

    def update_score(self, new_score: float, components: Optional[Dict] = None):
        """Update the score and optionally its components"""
        if new_score < 0:
            raise ValueError("Score cannot be negative")

        self.score = new_score
        if components:
            self.score_components = components

    def is_top_performer(self, threshold: int = 10) -> bool:
        """Check if this entry is in the top N positions"""
        return self.rank <= threshold

    def get_rank_suffix(self) -> str:
        """Get rank display suffix (1st, 2nd, 3rd, etc.)"""
        if 11 <= self.rank <= 13:
            return f"{self.rank}th"
        elif self.rank % 10 == 1:
            return f"{self.rank}st"
        elif self.rank % 10 == 2:
            return f"{self.rank}nd"
        elif self.rank % 10 == 3:
            return f"{self.rank}rd"
        else:
            return f"{self.rank}th"