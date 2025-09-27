from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from bson import ObjectId
from enum import Enum


class MultiplierType(Enum):
    """Types of multipliers that can be applied to credit conversion."""
    BASE = "base"
    TOURNAMENT = "tournament"
    CHALLENGE = "challenge"
    DAILY_STREAK = "daily_streak"
    WEEKEND = "weekend"
    SPECIAL_EVENT = "special_event"
    LOYALTY = "loyalty"
    FIRST_TIME = "first_time"


class ConversionRate:
    """
    Conversion rate model for managing credit calculation rates and multipliers.
    Handles base rates, multipliers, and time-based rate changes.
    """

    # Default conversion rates in EUR per minute
    DEFAULT_BASE_RATE = 0.01  # €0.01 per minute
    DEFAULT_MULTIPLIERS = {
        MultiplierType.TOURNAMENT.value: 2.0,
        MultiplierType.CHALLENGE.value: 1.5,
        MultiplierType.DAILY_STREAK.value: 1.2,
        MultiplierType.WEEKEND.value: 1.1,
        MultiplierType.SPECIAL_EVENT.value: 3.0,
        MultiplierType.LOYALTY.value: 1.3,
        MultiplierType.FIRST_TIME.value: 2.0
    }

    def __init__(self, rate_id: str = "default", base_rate: float = DEFAULT_BASE_RATE,
                 multipliers: Dict[str, float] = None, is_active: bool = True,
                 valid_from: Optional[datetime] = None, valid_until: Optional[datetime] = None,
                 description: str = None, metadata: Dict[str, Any] = None,
                 _id: Optional[ObjectId] = None, created_at: Optional[datetime] = None,
                 updated_at: Optional[datetime] = None):
        self._id = _id
        self.rate_id = rate_id
        self.base_rate = float(base_rate)
        self.multipliers = multipliers or self.DEFAULT_MULTIPLIERS.copy()
        self.is_active = is_active
        self.valid_from = valid_from or datetime.now(timezone.utc)
        self.valid_until = valid_until
        self.description = description or "Default conversion rates"
        self.metadata = metadata or {}
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or datetime.now(timezone.utc)

    def calculate_credits(self, play_duration_ms: int, multiplier_types: List[str] = None) -> float:
        """
        Calculate credits earned based on play duration and applied multipliers.

        Args:
            play_duration_ms: Play duration in milliseconds
            multiplier_types: List of multiplier types to apply

        Returns:
            float: Credits earned (rounded to 2 decimal places)
        """
        if play_duration_ms <= 0:
            return 0.0

        # Convert milliseconds to minutes
        play_duration_minutes = play_duration_ms / (1000 * 60)

        # Calculate base credits
        base_credits = play_duration_minutes * self.base_rate

        # Apply multipliers
        total_multiplier = self.get_combined_multiplier(multiplier_types or [])
        final_credits = base_credits * total_multiplier

        return round(final_credits, 2)

    def get_combined_multiplier(self, multiplier_types: List[str]) -> float:
        """
        Calculate combined multiplier from multiple multiplier types.

        Args:
            multiplier_types: List of multiplier type strings

        Returns:
            float: Combined multiplier value
        """
        if not multiplier_types:
            return 1.0

        total_multiplier = 1.0
        for multiplier_type in multiplier_types:
            if multiplier_type in self.multipliers:
                # Use additive approach for better balance: (m1-1) + (m2-1) + 1
                total_multiplier += (self.multipliers[multiplier_type] - 1.0)

        return max(total_multiplier, 1.0)  # Ensure minimum 1.0x multiplier

    def get_active_multipliers(self, context: Dict[str, Any] = None) -> List[str]:
        """
        Get list of currently active multipliers based on context.

        Args:
            context: Context information (time, user state, game type, etc.)

        Returns:
            List[str]: List of active multiplier type names
        """
        if not context:
            context = {}

        active_multipliers = []
        current_time = datetime.now(timezone.utc)

        # Tournament multiplier
        if context.get('is_tournament_mode', False):
            active_multipliers.append(MultiplierType.TOURNAMENT.value)

        # Challenge multiplier
        if context.get('is_challenge_mode', False):
            active_multipliers.append(MultiplierType.CHALLENGE.value)

        # Daily streak multiplier
        if context.get('has_daily_streak', False):
            active_multipliers.append(MultiplierType.DAILY_STREAK.value)

        # Weekend multiplier (Friday 18:00 to Sunday 23:59)
        if self._is_weekend_period(current_time):
            active_multipliers.append(MultiplierType.WEEKEND.value)

        # Special event multiplier
        if context.get('special_event_active', False):
            active_multipliers.append(MultiplierType.SPECIAL_EVENT.value)

        # Loyalty multiplier (based on user loyalty level)
        loyalty_level = context.get('user_loyalty_level', 0)
        if loyalty_level >= 3:  # Bronze, Silver, Gold, Platinum
            active_multipliers.append(MultiplierType.LOYALTY.value)

        # First time player multiplier
        if context.get('is_first_time_player', False):
            active_multipliers.append(MultiplierType.FIRST_TIME.value)

        return active_multipliers

    def _is_weekend_period(self, check_time: datetime) -> bool:
        """
        Check if the given time falls within weekend period.
        Weekend period: Friday 18:00 to Sunday 23:59

        Args:
            check_time: Time to check

        Returns:
            bool: True if within weekend period
        """
        weekday = check_time.weekday()  # Monday=0, Sunday=6
        hour = check_time.hour

        # Friday evening (after 18:00)
        if weekday == 4 and hour >= 18:
            return True

        # Saturday (all day)
        if weekday == 5:
            return True

        # Sunday (all day)
        if weekday == 6:
            return True

        return False

    def update_multiplier(self, multiplier_type: str, value: float) -> bool:
        """
        Update a specific multiplier value.

        Args:
            multiplier_type: Type of multiplier to update
            value: New multiplier value

        Returns:
            bool: True if update was successful
        """
        if not isinstance(value, (int, float)) or value < 0 or value > 10:
            return False

        self.multipliers[multiplier_type] = float(value)
        self.updated_at = datetime.now(timezone.utc)
        return True

    def add_custom_multiplier(self, name: str, value: float, description: str = None) -> bool:
        """
        Add a custom multiplier.

        Args:
            name: Multiplier name
            value: Multiplier value
            description: Optional description

        Returns:
            bool: True if multiplier was added successfully
        """
        if not isinstance(value, (int, float)) or value < 0 or value > 10:
            return False

        self.multipliers[name] = float(value)
        if description:
            self.metadata[f"{name}_description"] = description
        self.updated_at = datetime.now(timezone.utc)
        return True

    def is_valid_at(self, check_time: datetime = None) -> bool:
        """
        Check if conversion rate is valid at the given time.

        Args:
            check_time: Time to check (defaults to now)

        Returns:
            bool: True if conversion rate is valid
        """
        if not self.is_active:
            return False

        check_time = check_time or datetime.now(timezone.utc)

        if self.valid_from and check_time < self.valid_from:
            return False

        if self.valid_until and check_time > self.valid_until:
            return False

        return True

    def get_rate_summary(self) -> Dict[str, Any]:
        """
        Get a summary of current rates and multipliers.

        Returns:
            Dict containing rate summary information
        """
        return {
            'rate_id': self.rate_id,
            'base_rate_eur_per_minute': self.base_rate,
            'is_active': self.is_active,
            'is_currently_valid': self.is_valid_at(),
            'multipliers': self.multipliers,
            'max_possible_multiplier': self.get_combined_multiplier(list(self.multipliers.keys())),
            'valid_from': self.valid_from.isoformat() if self.valid_from else None,
            'valid_until': self.valid_until.isoformat() if self.valid_until else None,
            'description': self.description
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert conversion rate to dictionary for MongoDB storage."""
        return {
            '_id': self._id,
            'rate_id': self.rate_id,
            'base_rate': self.base_rate,
            'multipliers': self.multipliers,
            'is_active': self.is_active,
            'valid_from': self.valid_from,
            'valid_until': self.valid_until,
            'description': self.description,
            'metadata': self.metadata,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

    def to_api_dict(self) -> Dict[str, Any]:
        """Convert conversion rate to dictionary for API responses."""
        return {
            'id': str(self._id) if self._id else None,
            'rate_id': self.rate_id,
            'base_rate': self.base_rate,
            'multipliers': self.multipliers,
            'is_active': self.is_active,
            'is_currently_valid': self.is_valid_at(),
            'valid_from': self.valid_from.isoformat() if self.valid_from else None,
            'valid_until': self.valid_until.isoformat() if self.valid_until else None,
            'description': self.description,
            'summary': self.get_rate_summary(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversionRate':
        """Create ConversionRate instance from dictionary."""
        return cls(
            _id=data.get('_id'),
            rate_id=data.get('rate_id', 'default'),
            base_rate=data.get('base_rate', cls.DEFAULT_BASE_RATE),
            multipliers=data.get('multipliers'),
            is_active=data.get('is_active', True),
            valid_from=data.get('valid_from'),
            valid_until=data.get('valid_until'),
            description=data.get('description'),
            metadata=data.get('metadata', {}),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )

    @classmethod
    def create_default_rates(cls) -> 'ConversionRate':
        """Create default conversion rates configuration."""
        return cls(
            rate_id="default",
            base_rate=cls.DEFAULT_BASE_RATE,
            multipliers=cls.DEFAULT_MULTIPLIERS.copy(),
            description="Default GoodPlay conversion rates",
            metadata={
                'version': '1.0',
                'created_by': 'system',
                'notes': 'Initial rate configuration for GOO-14'
            }
        )

    @classmethod
    def create_special_event_rates(cls, event_name: str, base_multiplier: float = 2.0,
                                   valid_from: datetime = None, valid_until: datetime = None) -> 'ConversionRate':
        """
        Create special event conversion rates.

        Args:
            event_name: Name of the special event
            base_multiplier: Base multiplier for all activities during event
            valid_from: Event start time
            valid_until: Event end time

        Returns:
            ConversionRate: Special event rate configuration
        """
        multipliers = cls.DEFAULT_MULTIPLIERS.copy()
        # Apply base multiplier to all existing multipliers
        for key in multipliers:
            multipliers[key] = multipliers[key] * base_multiplier

        return cls(
            rate_id=f"special_event_{event_name.lower().replace(' ', '_')}",
            base_rate=cls.DEFAULT_BASE_RATE * base_multiplier,
            multipliers=multipliers,
            valid_from=valid_from,
            valid_until=valid_until,
            description=f"Special event rates for {event_name}",
            metadata={
                'event_name': event_name,
                'base_multiplier': base_multiplier,
                'event_type': 'special_promotion'
            }
        )

    @staticmethod
    def validate_conversion_rate_data(data: Dict[str, Any]) -> Optional[str]:
        """
        Validate conversion rate data for creation/updates.

        Args:
            data: Conversion rate data to validate

        Returns:
            str: Error message if validation fails, None if valid
        """
        if not isinstance(data, dict):
            return "CONVERSION_RATE_DATA_INVALID_FORMAT"

        if 'base_rate' in data:
            base_rate = data['base_rate']
            if not isinstance(base_rate, (int, float)) or base_rate < 0 or base_rate > 1:
                return "CONVERSION_RATE_BASE_RATE_INVALID"

        if 'multipliers' in data:
            multipliers = data['multipliers']
            if not isinstance(multipliers, dict):
                return "CONVERSION_RATE_MULTIPLIERS_INVALID_FORMAT"

            for key, value in multipliers.items():
                if not isinstance(value, (int, float)) or value < 0 or value > 10:
                    return f"CONVERSION_RATE_MULTIPLIER_{key.upper()}_INVALID"

        if 'valid_from' in data and 'valid_until' in data:
            if data['valid_from'] and data['valid_until']:
                if data['valid_from'] >= data['valid_until']:
                    return "CONVERSION_RATE_VALIDITY_PERIOD_INVALID"

        return None

    def __repr__(self) -> str:
        return f'<ConversionRate {self.rate_id}: {self.base_rate}€/min ({"active" if self.is_active else "inactive"})>'