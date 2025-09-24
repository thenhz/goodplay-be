from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from bson import ObjectId


class ImpactScore:
    """
    Model for user impact scores with component breakdown

    Collection: user_impact_scores

    Impact Score Calculation:
    - Gaming Activity (30%): Play time consistency, game variety, tournament participation, achievements
    - Social Engagement (20%): Friend interactions, challenges, community contributions
    - Donation Impact (50%): Amount, frequency, ONLUS diversity, special events
    """

    # Component weights for impact score calculation
    GAMING_WEIGHT = 0.30
    SOCIAL_WEIGHT = 0.20
    DONATION_WEIGHT = 0.50

    # Score scaling factors (max component scores)
    MAX_GAMING_SCORE = 1000.0
    MAX_SOCIAL_SCORE = 500.0
    MAX_DONATION_SCORE = 2000.0

    def __init__(self, user_id: str, impact_score: float = 0.0,
                 gaming_component: float = 0.0, social_component: float = 0.0,
                 donation_component: float = 0.0, rank_global: Optional[int] = None,
                 rank_weekly: Optional[int] = None, gaming_details: Optional[Dict] = None,
                 social_details: Optional[Dict] = None, donation_details: Optional[Dict] = None,
                 score_history: Optional[List[Dict]] = None, _id: Optional[str] = None,
                 created_at: Optional[datetime] = None, last_calculated: Optional[datetime] = None):
        """
        Initialize ImpactScore

        Args:
            user_id: ID of the user this score belongs to
            impact_score: Total calculated impact score
            gaming_component: Gaming activity component score
            social_component: Social engagement component score
            donation_component: Donation impact component score
            rank_global: Global ranking position
            rank_weekly: Weekly ranking position
            gaming_details: Detailed gaming metrics breakdown
            social_details: Detailed social engagement metrics
            donation_details: Detailed donation impact metrics
            score_history: Historical score tracking
            _id: MongoDB document ID
            created_at: Creation timestamp
            last_calculated: Last calculation timestamp
        """
        self._id = ObjectId(_id) if _id else ObjectId()
        self.user_id = ObjectId(user_id)
        self.impact_score = impact_score
        self.gaming_component = gaming_component
        self.social_component = social_component
        self.donation_component = donation_component
        self.rank_global = rank_global
        self.rank_weekly = rank_weekly
        self.created_at = created_at or datetime.now(timezone.utc)
        self.last_calculated = last_calculated or datetime.now(timezone.utc)

        # Detailed component breakdowns
        self.gaming_details = gaming_details or {
            'play_time_score': 0.0,
            'game_variety_score': 0.0,
            'tournament_score': 0.0,
            'achievement_score': 0.0,
            'consistency_multiplier': 1.0
        }

        self.social_details = social_details or {
            'friends_score': 0.0,
            'challenges_score': 0.0,
            'community_score': 0.0,
            'sharing_score': 0.0,
            'engagement_multiplier': 1.0
        }

        self.donation_details = donation_details or {
            'amount_score': 0.0,
            'frequency_score': 0.0,
            'diversity_score': 0.0,
            'event_score': 0.0,
            'consistency_multiplier': 1.0
        }

        # Historical tracking
        self.score_history = score_history or []

        self._validate()

    def _validate(self):
        """Validate impact score data"""
        if self.impact_score < 0:
            raise ValueError("Impact score cannot be negative")

        if not (0 <= self.gaming_component <= self.MAX_GAMING_SCORE):
            raise ValueError(f"Gaming component must be between 0 and {self.MAX_GAMING_SCORE}")

        if not (0 <= self.social_component <= self.MAX_SOCIAL_SCORE):
            raise ValueError(f"Social component must be between 0 and {self.MAX_SOCIAL_SCORE}")

        if not (0 <= self.donation_component <= self.MAX_DONATION_SCORE):
            raise ValueError(f"Donation component must be between 0 and {self.MAX_DONATION_SCORE}")

    def calculate_total_score(self) -> float:
        """Calculate total impact score from components"""
        gaming_weighted = self.gaming_component * self.GAMING_WEIGHT
        social_weighted = self.social_component * self.SOCIAL_WEIGHT
        donation_weighted = self.donation_component * self.DONATION_WEIGHT

        total = gaming_weighted + social_weighted + donation_weighted
        self.impact_score = round(total, 2)
        self.last_calculated = datetime.now(timezone.utc)

        return self.impact_score

    def update_component(self, component: str, score: float, details: Optional[Dict] = None):
        """Update a specific component score"""
        if component == 'gaming':
            if not (0 <= score <= self.MAX_GAMING_SCORE):
                raise ValueError(f"Gaming score must be between 0 and {self.MAX_GAMING_SCORE}")
            self.gaming_component = score
            if details:
                self.gaming_details.update(details)

        elif component == 'social':
            if not (0 <= score <= self.MAX_SOCIAL_SCORE):
                raise ValueError(f"Social score must be between 0 and {self.MAX_SOCIAL_SCORE}")
            self.social_component = score
            if details:
                self.social_details.update(details)

        elif component == 'donation':
            if not (0 <= score <= self.MAX_DONATION_SCORE):
                raise ValueError(f"Donation score must be between 0 and {self.MAX_DONATION_SCORE}")
            self.donation_component = score
            if details:
                self.donation_details.update(details)

        else:
            raise ValueError(f"Invalid component: {component}")

        # Recalculate total score
        self.calculate_total_score()

    def add_history_entry(self, score: float, rank: Optional[int] = None,
                         period: str = 'daily'):
        """Add entry to score history"""
        entry = {
            'date': datetime.now(timezone.utc),
            'score': score,
            'rank': rank,
            'period': period,
            'gaming_component': self.gaming_component,
            'social_component': self.social_component,
            'donation_component': self.donation_component
        }

        self.score_history.append(entry)

        # Keep only last 90 days of history
        if len(self.score_history) > 90:
            self.score_history = self.score_history[-90:]

    def get_score_trend(self, days: int = 7) -> Dict[str, Any]:
        """Get score trend over specified days"""
        if len(self.score_history) < 2:
            return {
                'trend': 'insufficient_data',
                'change': 0.0,
                'change_percentage': 0.0
            }

        # Get entries from last N days
        cutoff_date = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        cutoff_date = cutoff_date.replace(day=cutoff_date.day - days)

        relevant_entries = [
            entry for entry in self.score_history
            if entry['date'] >= cutoff_date
        ]

        if len(relevant_entries) < 2:
            return {
                'trend': 'insufficient_data',
                'change': 0.0,
                'change_percentage': 0.0
            }

        # Calculate trend
        oldest_score = relevant_entries[0]['score']
        newest_score = relevant_entries[-1]['score']

        change = newest_score - oldest_score
        change_percentage = (change / oldest_score * 100) if oldest_score > 0 else 0

        if change > 0:
            trend = 'increasing'
        elif change < 0:
            trend = 'decreasing'
        else:
            trend = 'stable'

        return {
            'trend': trend,
            'change': round(change, 2),
            'change_percentage': round(change_percentage, 2)
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB storage"""
        return {
            '_id': self._id,
            'user_id': self.user_id,
            'impact_score': self.impact_score,
            'gaming_component': self.gaming_component,
            'social_component': self.social_component,
            'donation_component': self.donation_component,
            'rank_global': self.rank_global,
            'rank_weekly': self.rank_weekly,
            'gaming_details': self.gaming_details,
            'social_details': self.social_details,
            'donation_details': self.donation_details,
            'score_history': self.score_history,
            'created_at': self.created_at,
            'last_calculated': self.last_calculated
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ImpactScore':
        """Create ImpactScore from dictionary"""
        return cls(
            user_id=str(data['user_id']),
            impact_score=data.get('impact_score', 0.0),
            gaming_component=data.get('gaming_component', 0.0),
            social_component=data.get('social_component', 0.0),
            donation_component=data.get('donation_component', 0.0),
            rank_global=data.get('rank_global'),
            rank_weekly=data.get('rank_weekly'),
            gaming_details=data.get('gaming_details', {}),
            social_details=data.get('social_details', {}),
            donation_details=data.get('donation_details', {}),
            score_history=data.get('score_history', []),
            _id=str(data['_id']) if '_id' in data else None,
            created_at=data.get('created_at'),
            last_calculated=data.get('last_calculated')
        )

    def to_response_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        trend = self.get_score_trend()

        return {
            'id': str(self._id),
            'user_id': str(self.user_id),
            'impact_score': self.impact_score,
            'components': {
                'gaming': {
                    'score': self.gaming_component,
                    'percentage': round((self.gaming_component / self.MAX_GAMING_SCORE) * 100, 1),
                    'details': self.gaming_details
                },
                'social': {
                    'score': self.social_component,
                    'percentage': round((self.social_component / self.MAX_SOCIAL_SCORE) * 100, 1),
                    'details': self.social_details
                },
                'donation': {
                    'score': self.donation_component,
                    'percentage': round((self.donation_component / self.MAX_DONATION_SCORE) * 100, 1),
                    'details': self.donation_details
                }
            },
            'rankings': {
                'global': self.rank_global,
                'weekly': self.rank_weekly
            },
            'trend': trend,
            'last_calculated': self.last_calculated.isoformat() if self.last_calculated else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def get_component_breakdown(self) -> Dict[str, float]:
        """Get weighted component contributions"""
        return {
            'gaming_weighted': round(self.gaming_component * self.GAMING_WEIGHT, 2),
            'social_weighted': round(self.social_component * self.SOCIAL_WEIGHT, 2),
            'donation_weighted': round(self.donation_component * self.DONATION_WEIGHT, 2)
        }

    def is_stale(self, hours: int = 24) -> bool:
        """Check if score calculation is stale"""
        if not self.last_calculated:
            return True

        time_diff = datetime.now(timezone.utc) - self.last_calculated
        return time_diff.total_seconds() > (hours * 3600)