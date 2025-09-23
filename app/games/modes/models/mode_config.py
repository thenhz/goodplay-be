from datetime import datetime
from typing import Dict, Any, Optional, List
from bson import ObjectId
from dataclasses import dataclass, field

@dataclass
class ModeConfig:
    """ModeConfig model for storing mode-specific configurations"""
    mode_name: str
    config_key: str
    config_value: Any
    config_type: str = "string"  # 'string', 'integer', 'float', 'boolean', 'object', 'array'
    description: str = ""
    is_default: bool = False
    is_override: bool = False  # True if this overrides default config
    applied_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    created_by: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    _id: Optional[ObjectId] = field(default=None)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the mode config to a dictionary for MongoDB storage"""
        data = {
            "mode_name": self.mode_name,
            "config_key": self.config_key,
            "config_value": self.config_value,
            "config_type": self.config_type,
            "description": self.description,
            "is_default": self.is_default,
            "is_override": self.is_override,
            "applied_at": self.applied_at,
            "expires_at": self.expires_at,
            "created_by": self.created_by,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

        if self._id:
            data["_id"] = self._id

        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModeConfig':
        """Create a ModeConfig instance from a dictionary"""
        config = cls(
            mode_name=data.get("mode_name", ""),
            config_key=data.get("config_key", ""),
            config_value=data.get("config_value"),
            config_type=data.get("config_type", "string"),
            description=data.get("description", ""),
            is_default=data.get("is_default", False),
            is_override=data.get("is_override", False),
            applied_at=data.get("applied_at"),
            expires_at=data.get("expires_at"),
            created_by=data.get("created_by"),
            created_at=data.get("created_at", datetime.utcnow()),
            updated_at=data.get("updated_at", datetime.utcnow())
        )

        if "_id" in data:
            config._id = data["_id"]

        return config

    def to_api_dict(self) -> Dict[str, Any]:
        """Convert the mode config to a dictionary for API responses"""
        return {
            "id": str(self._id) if self._id else None,
            "mode_name": self.mode_name,
            "config_key": self.config_key,
            "config_value": self.config_value,
            "config_type": self.config_type,
            "description": self.description,
            "is_default": self.is_default,
            "is_override": self.is_override,
            "is_active": self.is_active(),
            "applied_at": self.applied_at.isoformat() if self.applied_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

    def is_active(self) -> bool:
        """Check if the config is currently active"""
        now = datetime.utcnow()

        # Check if applied
        if self.applied_at and now < self.applied_at:
            return False

        # Check if expired
        if self.expires_at and now > self.expires_at:
            return False

        return True

    def apply(self) -> None:
        """Apply the configuration"""
        self.applied_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def expire(self) -> None:
        """Set the configuration to expire now"""
        self.expires_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def extend_expiry(self, hours: int) -> None:
        """Extend the expiry time by specified hours"""
        if self.expires_at:
            self.expires_at = self.expires_at + datetime.timedelta(hours=hours)
        else:
            self.expires_at = datetime.utcnow() + datetime.timedelta(hours=hours)
        self.updated_at = datetime.utcnow()

    @staticmethod
    def create_default_configs() -> List['ModeConfig']:
        """Create default configurations for all modes"""
        configs = []

        # Normal mode defaults
        normal_configs = [
            ModeConfig("normal", "allows_single_player", True, "boolean", "Allow single player games", True),
            ModeConfig("normal", "allows_multiplayer", False, "boolean", "Allow multiplayer games", True),
            ModeConfig("normal", "credits_enabled", True, "boolean", "Enable credit earning", True),
            ModeConfig("normal", "achievements_enabled", True, "boolean", "Enable achievements", True),
            ModeConfig("normal", "credits_multiplier", 1.0, "float", "Credit earning multiplier", True),
        ]

        # Challenge mode defaults
        challenge_configs = [
            ModeConfig("challenges", "allows_1v1", True, "boolean", "Allow 1v1 challenges", True),
            ModeConfig("challenges", "allows_nvn", True, "boolean", "Allow NvN challenges", True),
            ModeConfig("challenges", "max_participants", 8, "integer", "Maximum participants per challenge", True),
            ModeConfig("challenges", "auto_matchmaking", True, "boolean", "Enable automatic matchmaking", True),
            ModeConfig("challenges", "challenge_timeout_minutes", 60, "integer", "Challenge invitation timeout", True),
            ModeConfig("challenges", "credits_multiplier", 1.5, "float", "Credit earning multiplier for challenges", True),
            ModeConfig("challenges", "allow_cross_game", False, "boolean", "Allow cross-game challenges", True),
        ]

        # Team tournament mode defaults
        tournament_configs = [
            ModeConfig("team_tournament", "auto_team_assignment", True, "boolean", "Automatic team assignment", True),
            ModeConfig("team_tournament", "team_count", 2, "integer", "Number of teams", True),
            ModeConfig("team_tournament", "tournament_duration_days", 7, "integer", "Tournament duration in days", True),
            ModeConfig("team_tournament", "individual_weight", 0.7, "float", "Weight for individual scores", True),
            ModeConfig("team_tournament", "challenge_weight", 1.3, "float", "Weight for challenge scores", True),
            ModeConfig("team_tournament", "credits_multiplier", 2.0, "float", "Credit earning multiplier", True),
            ModeConfig("team_tournament", "special_events", True, "boolean", "Enable special events", True),
            ModeConfig("team_tournament", "leaderboard_update_minutes", 5, "integer", "Leaderboard update frequency", True),
        ]

        configs.extend(normal_configs)
        configs.extend(challenge_configs)
        configs.extend(tournament_configs)

        return configs

    @staticmethod
    def create_weekend_bonus_config() -> 'ModeConfig':
        """Create a weekend bonus credit multiplier override"""
        return ModeConfig(
            mode_name="all",  # Special value for all modes
            config_key="weekend_credits_bonus",
            config_value=1.2,
            config_type="float",
            description="Weekend bonus credit multiplier",
            is_override=True
        )

    @staticmethod
    def create_event_config(mode_name: str, event_multiplier: float, duration_hours: int) -> 'ModeConfig':
        """Create a temporary event configuration"""
        expires_at = datetime.utcnow() + datetime.timedelta(hours=duration_hours)

        return ModeConfig(
            mode_name=mode_name,
            config_key="event_credits_multiplier",
            config_value=event_multiplier,
            config_type="float",
            description=f"Special event {event_multiplier}x credits multiplier",
            is_override=True,
            expires_at=expires_at
        )

    def __str__(self) -> str:
        return f"ModeConfig(mode={self.mode_name}, key={self.config_key}, value={self.config_value})"

    def __repr__(self) -> str:
        return self.__str__()