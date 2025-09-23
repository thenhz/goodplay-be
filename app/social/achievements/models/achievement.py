from datetime import datetime
from typing import Optional, Dict, Any, List
from bson import ObjectId


class Achievement:
    """
    Model for achievement definitions with trigger conditions and metadata

    Collection: achievements
    """

    # Achievement categories
    GAMING = 'gaming'
    SOCIAL = 'social'
    IMPACT = 'impact'

    # Badge rarities
    COMMON = 'common'
    RARE = 'rare'
    EPIC = 'epic'
    LEGENDARY = 'legendary'

    # Trigger types
    GAME_SESSION = 'game_session'
    GAME_SCORE = 'game_score'
    SOCIAL_FRIEND = 'social_friend'
    SOCIAL_LIKE = 'social_like'
    DONATION_AMOUNT = 'donation_amount'
    DONATION_COUNT = 'donation_count'
    CONSECUTIVE_DAYS = 'consecutive_days'
    GAME_DIVERSITY = 'game_diversity'
    TOURNAMENT_VICTORY = 'tournament_victory'
    HELP_PROVIDED = 'help_provided'
    ONLUS_DIVERSITY = 'onlus_diversity'
    MONTHLY_DONATION_STREAK = 'monthly_donation_streak'

    VALID_CATEGORIES = [GAMING, SOCIAL, IMPACT]
    VALID_RARITIES = [COMMON, RARE, EPIC, LEGENDARY]
    VALID_TRIGGER_TYPES = [
        GAME_SESSION, GAME_SCORE, SOCIAL_FRIEND, SOCIAL_LIKE,
        DONATION_AMOUNT, DONATION_COUNT, CONSECUTIVE_DAYS,
        GAME_DIVERSITY, TOURNAMENT_VICTORY, HELP_PROVIDED,
        ONLUS_DIVERSITY, MONTHLY_DONATION_STREAK
    ]

    def __init__(self, achievement_id: str, name: str, description: str,
                 category: str, trigger_conditions: Dict[str, Any],
                 badge_rarity: str = COMMON, reward_credits: int = 0,
                 icon_url: Optional[str] = None, is_active: bool = True,
                 _id: Optional[str] = None, created_at: Optional[datetime] = None):
        """
        Initialize Achievement

        Args:
            achievement_id: Unique identifier for the achievement
            name: Display name of the achievement
            description: Description of how to unlock
            category: Achievement category (gaming, social, impact)
            trigger_conditions: Dictionary defining trigger rules
            badge_rarity: Rarity level of the badge reward
            reward_credits: Credit bonus for completing achievement
            icon_url: URL for achievement icon
            is_active: Whether achievement is currently active
            _id: MongoDB document ID
            created_at: Creation timestamp
        """
        self._id = ObjectId(_id) if _id else ObjectId()
        self.achievement_id = achievement_id
        self.name = name
        self.description = description
        self.category = category
        self.trigger_conditions = trigger_conditions
        self.badge_rarity = badge_rarity
        self.reward_credits = reward_credits
        self.icon_url = icon_url
        self.is_active = is_active
        self.created_at = created_at or datetime.utcnow()

        self._validate()

    def _validate(self):
        """Validate achievement data"""
        if not self.achievement_id or not isinstance(self.achievement_id, str):
            raise ValueError("Achievement ID is required and must be string")

        if not self.name or not isinstance(self.name, str):
            raise ValueError("Achievement name is required and must be string")

        if self.category not in self.VALID_CATEGORIES:
            raise ValueError(f"Invalid category: {self.category}")

        if self.badge_rarity not in self.VALID_RARITIES:
            raise ValueError(f"Invalid badge rarity: {self.badge_rarity}")

        if not isinstance(self.trigger_conditions, dict):
            raise ValueError("Trigger conditions must be a dictionary")

        if 'type' not in self.trigger_conditions:
            raise ValueError("Trigger conditions must include 'type'")

        if self.trigger_conditions['type'] not in self.VALID_TRIGGER_TYPES:
            raise ValueError(f"Invalid trigger type: {self.trigger_conditions['type']}")

        if self.reward_credits < 0:
            raise ValueError("Reward credits cannot be negative")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB storage"""
        return {
            '_id': self._id,
            'achievement_id': self.achievement_id,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'trigger_conditions': self.trigger_conditions,
            'badge_rarity': self.badge_rarity,
            'reward_credits': self.reward_credits,
            'icon_url': self.icon_url,
            'is_active': self.is_active,
            'created_at': self.created_at
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Achievement':
        """Create Achievement from dictionary"""
        return cls(
            achievement_id=data['achievement_id'],
            name=data['name'],
            description=data['description'],
            category=data['category'],
            trigger_conditions=data['trigger_conditions'],
            badge_rarity=data.get('badge_rarity', cls.COMMON),
            reward_credits=data.get('reward_credits', 0),
            icon_url=data.get('icon_url'),
            is_active=data.get('is_active', True),
            _id=str(data['_id']) if '_id' in data else None,
            created_at=data.get('created_at')
        )

    def to_response_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            'id': str(self._id),
            'achievement_id': self.achievement_id,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'trigger_conditions': self.trigger_conditions,
            'badge_rarity': self.badge_rarity,
            'reward_credits': self.reward_credits,
            'icon_url': self.icon_url,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def is_gaming_achievement(self) -> bool:
        """Check if this is a gaming achievement"""
        return self.category == self.GAMING

    def is_social_achievement(self) -> bool:
        """Check if this is a social achievement"""
        return self.category == self.SOCIAL

    def is_impact_achievement(self) -> bool:
        """Check if this is an impact achievement"""
        return self.category == self.IMPACT

    def get_trigger_type(self) -> str:
        """Get the trigger type for this achievement"""
        return self.trigger_conditions.get('type', '')

    def get_target_value(self) -> Any:
        """Get the target value needed to unlock this achievement"""
        return self.trigger_conditions.get('target_value')

    def check_condition(self, current_value: Any) -> bool:
        """
        Check if current value meets the achievement condition

        Args:
            current_value: Current value to check against trigger conditions

        Returns:
            bool: True if condition is met
        """
        trigger_type = self.get_trigger_type()
        target_value = self.get_target_value()

        if target_value is None:
            return False

        # For most achievements, we check if current value >= target value
        if trigger_type in [self.GAME_SESSION, self.SOCIAL_FRIEND, self.SOCIAL_LIKE,
                           self.DONATION_COUNT, self.CONSECUTIVE_DAYS]:
            return current_value >= target_value

        # For score-based achievements, check specific conditions
        elif trigger_type == self.GAME_SCORE:
            comparison = self.trigger_conditions.get('comparison', 'gte')
            if comparison == 'gte':
                return current_value >= target_value
            elif comparison == 'lte':
                return current_value <= target_value
            elif comparison == 'eq':
                return current_value == target_value

        # For donation amount, check total amount
        elif trigger_type == self.DONATION_AMOUNT:
            return current_value >= target_value

        return False

    def get_rarity_multiplier(self) -> float:
        """Get credit multiplier based on badge rarity"""
        multipliers = {
            self.COMMON: 1.0,
            self.RARE: 1.5,
            self.EPIC: 2.0,
            self.LEGENDARY: 3.0
        }
        return multipliers.get(self.badge_rarity, 1.0)

    def calculate_final_reward(self) -> int:
        """Calculate final credit reward including rarity multiplier"""
        base_reward = self.reward_credits
        multiplier = self.get_rarity_multiplier()
        return int(base_reward * multiplier)