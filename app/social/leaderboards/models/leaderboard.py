from datetime import datetime
from typing import Optional, Dict, Any, List
from bson import ObjectId
from .leaderboard_entry import LeaderboardEntry


class Leaderboard:
    """
    Model for dynamic leaderboards with multi-category support

    Collection: leaderboards

    Supports various leaderboard types:
    - Global Impact: Overall impact score ranking
    - Weekly Warriors: Top players this week
    - Gaming Masters: Top gaming performance
    - Social Champions: Top social engagement
    - Donation Heroes: Top donation contributors
    - Friends Circle: Ranking among friends
    """

    # Leaderboard types
    GLOBAL_IMPACT = 'global_impact'
    WEEKLY_WARRIORS = 'weekly_warriors'
    GAMING_MASTERS = 'gaming_masters'
    SOCIAL_CHAMPIONS = 'social_champions'
    DONATION_HEROES = 'donation_heroes'
    FRIENDS_CIRCLE = 'friends_circle'

    # Time periods
    DAILY = 'daily'
    WEEKLY = 'weekly'
    MONTHLY = 'monthly'
    ALL_TIME = 'all_time'

    VALID_TYPES = [
        GLOBAL_IMPACT, WEEKLY_WARRIORS, GAMING_MASTERS,
        SOCIAL_CHAMPIONS, DONATION_HEROES, FRIENDS_CIRCLE
    ]

    VALID_PERIODS = [DAILY, WEEKLY, MONTHLY, ALL_TIME]

    def __init__(self, leaderboard_type: str, period: str,
                 entries: Optional[List[Dict]] = None,
                 metadata: Optional[Dict] = None,
                 _id: Optional[str] = None,
                 created_at: Optional[datetime] = None,
                 last_updated: Optional[datetime] = None):
        """
        Initialize Leaderboard

        Args:
            leaderboard_type: Type of leaderboard (global_impact, weekly_warriors, etc.)
            period: Time period (daily, weekly, monthly, all_time)
            entries: List of leaderboard entries
            metadata: Additional leaderboard metadata
            _id: MongoDB document ID
            created_at: Creation timestamp
            last_updated: Last update timestamp
        """
        self._id = ObjectId(_id) if _id else ObjectId()
        self.leaderboard_type = leaderboard_type
        self.period = period
        self.entries = []
        self.created_at = created_at or datetime.utcnow()
        self.last_updated = last_updated or datetime.utcnow()

        # Leaderboard metadata
        self.metadata = metadata or {
            'total_participants': 0,
            'min_score': 0.0,
            'max_score': 0.0,
            'avg_score': 0.0,
            'score_range': 0.0,
            'update_frequency': 'hourly'
        }

        # Convert entry dictionaries to LeaderboardEntry objects
        if entries:
            self.entries = [
                LeaderboardEntry.from_dict(entry) if isinstance(entry, dict) else entry
                for entry in entries
            ]

        self._validate()

    def _validate(self):
        """Validate leaderboard data"""
        if self.leaderboard_type not in self.VALID_TYPES:
            raise ValueError(f"Invalid leaderboard type: {self.leaderboard_type}")

        if self.period not in self.VALID_PERIODS:
            raise ValueError(f"Invalid period: {self.period}")

    def add_entry(self, entry: LeaderboardEntry) -> bool:
        """
        Add entry to leaderboard

        Args:
            entry: LeaderboardEntry to add

        Returns:
            bool: True if entry was added successfully
        """
        if not isinstance(entry, LeaderboardEntry):
            raise ValueError("Entry must be a LeaderboardEntry instance")

        # Check if user already exists in leaderboard
        existing_entry = self.get_entry_by_user_id(str(entry.user_id))
        if existing_entry:
            # Update existing entry
            existing_entry.update_score(entry.score, entry.score_components)
            existing_entry.update_rank(entry.rank)
        else:
            self.entries.append(entry)

        self._sort_entries()
        self._update_metadata()
        self.last_updated = datetime.utcnow()

        return True

    def get_entry_by_user_id(self, user_id: str) -> Optional[LeaderboardEntry]:
        """Get leaderboard entry for specific user"""
        for entry in self.entries:
            if str(entry.user_id) == user_id:
                return entry
        return None

    def get_entries_paginated(self, page: int = 1, per_page: int = 50) -> List[LeaderboardEntry]:
        """Get paginated leaderboard entries"""
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        return self.entries[start_idx:end_idx]

    def get_top_entries(self, limit: int = 10) -> List[LeaderboardEntry]:
        """Get top N entries from leaderboard"""
        return self.entries[:limit]

    def get_user_rank(self, user_id: str) -> Optional[int]:
        """Get user's rank in this leaderboard"""
        entry = self.get_entry_by_user_id(user_id)
        return entry.rank if entry else None

    def get_user_percentile(self, user_id: str) -> Optional[float]:
        """Get user's percentile rank in this leaderboard"""
        entry = self.get_entry_by_user_id(user_id)
        if not entry or len(self.entries) == 0:
            return None

        percentile = (len(self.entries) - entry.rank + 1) / len(self.entries) * 100
        return round(percentile, 2)

    def _sort_entries(self):
        """Sort entries by score (descending) and update ranks"""
        self.entries.sort(key=lambda x: x.score, reverse=True)

        # Update ranks
        for i, entry in enumerate(self.entries):
            entry.update_rank(i + 1)

    def _update_metadata(self):
        """Update leaderboard metadata"""
        if not self.entries:
            self.metadata.update({
                'total_participants': 0,
                'min_score': 0.0,
                'max_score': 0.0,
                'avg_score': 0.0,
                'score_range': 0.0
            })
            return

        scores = [entry.score for entry in self.entries]

        self.metadata.update({
            'total_participants': len(self.entries),
            'min_score': min(scores),
            'max_score': max(scores),
            'avg_score': round(sum(scores) / len(scores), 2),
            'score_range': max(scores) - min(scores)
        })

    def clear_entries(self):
        """Clear all entries (for period resets)"""
        self.entries = []
        self._update_metadata()
        self.last_updated = datetime.utcnow()

    def get_leaderboard_id(self) -> str:
        """Generate unique leaderboard identifier"""
        return f"{self.leaderboard_type}_{self.period}"

    def is_stale(self, hours: int = 1) -> bool:
        """Check if leaderboard needs updating"""
        if not self.last_updated:
            return True

        time_diff = datetime.utcnow() - self.last_updated
        return time_diff.total_seconds() > (hours * 3600)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB storage"""
        return {
            '_id': self._id,
            'leaderboard_type': self.leaderboard_type,
            'period': self.period,
            'entries': [entry.to_dict() for entry in self.entries],
            'metadata': self.metadata,
            'created_at': self.created_at,
            'last_updated': self.last_updated
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Leaderboard':
        """Create Leaderboard from dictionary"""
        return cls(
            leaderboard_type=data['leaderboard_type'],
            period=data['period'],
            entries=data.get('entries', []),
            metadata=data.get('metadata', {}),
            _id=str(data['_id']) if '_id' in data else None,
            created_at=data.get('created_at'),
            last_updated=data.get('last_updated')
        )

    def to_response_dict(self, include_entries: bool = True,
                        page: int = 1, per_page: int = 50) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        response = {
            'id': str(self._id),
            'leaderboard_type': self.leaderboard_type,
            'period': self.period,
            'metadata': self.metadata,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }

        if include_entries:
            entries = self.get_entries_paginated(page, per_page)
            response['entries'] = [entry.to_response_dict() for entry in entries]
            total_items = len(self.entries)
            total_pages = (total_items + per_page - 1) // per_page if total_items > 0 else 1
            response['pagination'] = {
                'page': page,
                'per_page': per_page,
                'total_items': total_items,
                'total_pages': total_pages,
                'has_next': page < total_pages,
                'has_prev': page > 1
            }

        return response

    def get_type_display_name(self) -> str:
        """Get human-readable leaderboard type name"""
        display_names = {
            self.GLOBAL_IMPACT: "Global Impact Leaders",
            self.WEEKLY_WARRIORS: "Weekly Warriors",
            self.GAMING_MASTERS: "Gaming Masters",
            self.SOCIAL_CHAMPIONS: "Social Champions",
            self.DONATION_HEROES: "Donation Heroes",
            self.FRIENDS_CIRCLE: "Friends Leaderboard"
        }
        return display_names.get(self.leaderboard_type, self.leaderboard_type.title())

    def get_period_display_name(self) -> str:
        """Get human-readable period name"""
        display_names = {
            self.DAILY: "Daily",
            self.WEEKLY: "Weekly",
            self.MONTHLY: "Monthly",
            self.ALL_TIME: "All Time"
        }
        return display_names.get(self.period, self.period.title())