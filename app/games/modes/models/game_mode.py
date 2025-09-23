from datetime import datetime
from typing import Dict, Any, Optional
from bson import ObjectId
from dataclasses import dataclass, field

@dataclass
class GameMode:
    """GameMode model representing available game modes and their status"""
    name: str  # 'normal', 'challenges', 'team_tournament'
    display_name: str
    description: str
    is_active: bool = False
    is_default: bool = False  # 'normal' mode should always be True
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    config: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    _id: Optional[ObjectId] = field(default=None)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the game mode to a dictionary for MongoDB storage"""
        data = {
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "is_active": self.is_active,
            "is_default": self.is_default,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "config": self.config,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

        if self._id:
            data["_id"] = self._id

        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GameMode':
        """Create a GameMode instance from a dictionary"""
        mode = cls(
            name=data.get("name", ""),
            display_name=data.get("display_name", ""),
            description=data.get("description", ""),
            is_active=data.get("is_active", False),
            is_default=data.get("is_default", False),
            start_date=data.get("start_date"),
            end_date=data.get("end_date"),
            config=data.get("config", {}),
            created_at=data.get("created_at", datetime.utcnow()),
            updated_at=data.get("updated_at", datetime.utcnow())
        )

        if "_id" in data:
            mode._id = data["_id"]

        return mode

    def to_api_dict(self) -> Dict[str, Any]:
        """Convert the game mode to a dictionary for API responses"""
        return {
            "id": str(self._id) if self._id else None,
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "is_active": self.is_active,
            "is_default": self.is_default,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "config": self.config,
            "is_currently_available": self.is_currently_available(),
            "time_remaining": self.get_time_remaining_seconds(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

    def activate(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> None:
        """Activate the game mode with optional date constraints"""
        self.is_active = True
        if start_date:
            self.start_date = start_date
        if end_date:
            self.end_date = end_date
        self.updated_at = datetime.utcnow()

    def deactivate(self) -> None:
        """Deactivate the game mode"""
        self.is_active = False
        self.updated_at = datetime.utcnow()

    def is_currently_available(self) -> bool:
        """Check if the mode is currently available considering time constraints"""
        if not self.is_active:
            return False

        now = datetime.utcnow()

        # Check start date
        if self.start_date and now < self.start_date:
            return False

        # Check end date
        if self.end_date and now > self.end_date:
            return False

        return True

    def get_time_remaining_seconds(self) -> Optional[int]:
        """Get remaining time in seconds if mode has an end date"""
        if not self.end_date:
            return None

        now = datetime.utcnow()
        if now >= self.end_date:
            return 0

        return int((self.end_date - now).total_seconds())

    def update_config(self, new_config: Dict[str, Any]) -> None:
        """Update mode configuration"""
        self.config.update(new_config)
        self.updated_at = datetime.utcnow()

    def is_scheduled_for_future(self) -> bool:
        """Check if mode is scheduled to start in the future"""
        if not self.start_date:
            return False
        return datetime.utcnow() < self.start_date

    def has_expired(self) -> bool:
        """Check if mode has expired"""
        if not self.end_date:
            return False
        return datetime.utcnow() > self.end_date

    @staticmethod
    def create_default_normal_mode() -> 'GameMode':
        """Create the default normal mode that should always be available"""
        return GameMode(
            name="normal",
            display_name="Normal Mode",
            description="Classic single-player game mode",
            is_active=True,
            is_default=True,
            config={
                "allows_single_player": True,
                "allows_multiplayer": False,
                "credits_enabled": True,
                "achievements_enabled": True
            }
        )

    @staticmethod
    def create_challenges_mode() -> 'GameMode':
        """Create challenges mode template"""
        return GameMode(
            name="challenges",
            display_name="Challenge Mode",
            description="Direct challenges between players",
            is_active=False,
            is_default=False,
            config={
                "allows_1v1": True,
                "allows_nvn": True,
                "max_participants": 8,
                "auto_matchmaking": True,
                "challenge_timeout_minutes": 60,
                "credits_multiplier": 1.5
            }
        )

    @staticmethod
    def create_team_tournament_mode() -> 'GameMode':
        """Create team tournament mode template"""
        return GameMode(
            name="team_tournament",
            display_name="Team Tournament",
            description="Global team competition with point accumulation",
            is_active=False,
            is_default=False,
            config={
                "auto_team_assignment": True,
                "team_count": 2,
                "tournament_duration_days": 7,
                "individual_weight": 0.7,
                "challenge_weight": 1.3,
                "credits_multiplier": 2.0,
                "special_events": True
            }
        )

    def __str__(self) -> str:
        return f"GameMode(id={self._id}, name={self.name}, active={self.is_active})"

    def __repr__(self) -> str:
        return self.__str__()