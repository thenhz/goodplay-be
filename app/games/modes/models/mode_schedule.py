from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from bson import ObjectId
from dataclasses import dataclass, field
import uuid

@dataclass
class ModeSchedule:
    """ModeSchedule model for managing scheduled activation/deactivation of game modes"""
    mode_name: str  # Name of the mode to schedule
    schedule_type: str  # 'one_time', 'recurring', 'event'
    action: str  # 'activate', 'deactivate'
    scheduled_at: datetime
    executed_at: Optional[datetime] = None
    is_executed: bool = False
    is_cancelled: bool = False
    recurrence_config: Dict[str, Any] = field(default_factory=dict)
    mode_config_override: Dict[str, Any] = field(default_factory=dict)
    event_metadata: Dict[str, Any] = field(default_factory=dict)
    created_by: Optional[str] = None  # Admin user ID who created the schedule
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    schedule_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    _id: Optional[ObjectId] = field(default=None)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the mode schedule to a dictionary for MongoDB storage"""
        data = {
            "schedule_id": self.schedule_id,
            "mode_name": self.mode_name,
            "schedule_type": self.schedule_type,
            "action": self.action,
            "scheduled_at": self.scheduled_at,
            "executed_at": self.executed_at,
            "is_executed": self.is_executed,
            "is_cancelled": self.is_cancelled,
            "recurrence_config": self.recurrence_config,
            "mode_config_override": self.mode_config_override,
            "event_metadata": self.event_metadata,
            "created_by": self.created_by,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

        if self._id:
            data["_id"] = self._id

        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModeSchedule':
        """Create a ModeSchedule instance from a dictionary"""
        schedule = cls(
            mode_name=data.get("mode_name", ""),
            schedule_type=data.get("schedule_type", "one_time"),
            action=data.get("action", "activate"),
            scheduled_at=data.get("scheduled_at", datetime.utcnow()),
            executed_at=data.get("executed_at"),
            is_executed=data.get("is_executed", False),
            is_cancelled=data.get("is_cancelled", False),
            recurrence_config=data.get("recurrence_config", {}),
            mode_config_override=data.get("mode_config_override", {}),
            event_metadata=data.get("event_metadata", {}),
            created_by=data.get("created_by"),
            created_at=data.get("created_at", datetime.utcnow()),
            updated_at=data.get("updated_at", datetime.utcnow()),
            schedule_id=data.get("schedule_id", str(uuid.uuid4()))
        )

        if "_id" in data:
            schedule._id = data["_id"]

        return schedule

    def to_api_dict(self) -> Dict[str, Any]:
        """Convert the mode schedule to a dictionary for API responses"""
        return {
            "id": str(self._id) if self._id else None,
            "schedule_id": self.schedule_id,
            "mode_name": self.mode_name,
            "schedule_type": self.schedule_type,
            "action": self.action,
            "scheduled_at": self.scheduled_at.isoformat(),
            "executed_at": self.executed_at.isoformat() if self.executed_at else None,
            "is_executed": self.is_executed,
            "is_cancelled": self.is_cancelled,
            "recurrence_config": self.recurrence_config,
            "mode_config_override": self.mode_config_override,
            "event_metadata": self.event_metadata,
            "created_by": self.created_by,
            "is_pending": self.is_pending(),
            "time_until_execution": self.get_time_until_execution_seconds(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

    def execute(self) -> None:
        """Mark the schedule as executed"""
        self.is_executed = True
        self.executed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def cancel(self) -> None:
        """Cancel the scheduled action"""
        self.is_cancelled = True
        self.updated_at = datetime.utcnow()

    def is_pending(self) -> bool:
        """Check if the schedule is pending execution"""
        return not self.is_executed and not self.is_cancelled and datetime.utcnow() >= self.scheduled_at

    def is_due(self) -> bool:
        """Check if the schedule is due for execution"""
        return not self.is_executed and not self.is_cancelled and datetime.utcnow() >= self.scheduled_at

    def get_time_until_execution_seconds(self) -> Optional[int]:
        """Get time remaining until execution in seconds"""
        if self.is_executed or self.is_cancelled:
            return None

        now = datetime.utcnow()
        if now >= self.scheduled_at:
            return 0

        return int((self.scheduled_at - now).total_seconds())

    def should_create_recurrence(self) -> bool:
        """Check if a new recurrence should be created after execution"""
        return (
            self.schedule_type == "recurring" and
            self.is_executed and
            not self.is_cancelled and
            bool(self.recurrence_config)
        )

    def create_next_recurrence(self) -> Optional['ModeSchedule']:
        """Create the next scheduled recurrence"""
        if not self.should_create_recurrence():
            return None

        recurrence_type = self.recurrence_config.get("type")  # 'daily', 'weekly', 'monthly'
        interval = self.recurrence_config.get("interval", 1)

        next_scheduled_at = None

        if recurrence_type == "daily":
            next_scheduled_at = self.scheduled_at + timedelta(days=interval)
        elif recurrence_type == "weekly":
            next_scheduled_at = self.scheduled_at + timedelta(weeks=interval)
        elif recurrence_type == "monthly":
            # Approximate monthly recurrence (30 days)
            next_scheduled_at = self.scheduled_at + timedelta(days=30 * interval)

        if not next_scheduled_at:
            return None

        # Check if recurrence has an end date
        end_date = self.recurrence_config.get("end_date")
        if end_date and isinstance(end_date, datetime) and next_scheduled_at > end_date:
            return None

        return ModeSchedule(
            mode_name=self.mode_name,
            schedule_type=self.schedule_type,
            action=self.action,
            scheduled_at=next_scheduled_at,
            recurrence_config=self.recurrence_config,
            mode_config_override=self.mode_config_override,
            event_metadata=self.event_metadata,
            created_by=self.created_by
        )

    @staticmethod
    def create_daily_challenge_activation(hour: int = 9, minute: int = 0, created_by: str = None) -> 'ModeSchedule':
        """Create a daily recurring schedule for challenge mode activation"""
        today = datetime.utcnow().replace(hour=hour, minute=minute, second=0, microsecond=0)
        if datetime.utcnow() >= today:
            # If time has passed today, schedule for tomorrow
            today += timedelta(days=1)

        return ModeSchedule(
            mode_name="challenges",
            schedule_type="recurring",
            action="activate",
            scheduled_at=today,
            recurrence_config={
                "type": "daily",
                "interval": 1,
                "end_date": None  # Infinite recurrence
            },
            mode_config_override={
                "challenge_timeout_minutes": 60,
                "auto_matchmaking": True
            },
            event_metadata={
                "event_name": "Daily Challenge",
                "description": "Daily challenge mode activation"
            },
            created_by=created_by
        )

    @staticmethod
    def create_weekend_tournament(start_friday_hour: int = 18, created_by: str = None) -> 'ModeSchedule':
        """Create a weekly weekend tournament schedule"""
        now = datetime.utcnow()
        # Find next Friday
        days_ahead = 4 - now.weekday()  # Friday is weekday 4
        if days_ahead <= 0:  # Target day already happened this week
            days_ahead += 7

        next_friday = now + timedelta(days=days_ahead)
        start_time = next_friday.replace(hour=start_friday_hour, minute=0, second=0, microsecond=0)

        return ModeSchedule(
            mode_name="team_tournament",
            schedule_type="recurring",
            action="activate",
            scheduled_at=start_time,
            recurrence_config={
                "type": "weekly",
                "interval": 1,
                "end_date": None
            },
            mode_config_override={
                "tournament_duration_days": 3,  # Friday to Sunday
                "team_count": 4,
                "credits_multiplier": 2.5
            },
            event_metadata={
                "event_name": "Weekend Tournament",
                "description": "Weekly weekend team tournament",
                "duration": "Friday 18:00 - Sunday 23:59"
            },
            created_by=created_by
        )

    @staticmethod
    def create_special_event(mode_name: str, start_date: datetime, end_date: datetime,
                           event_name: str, created_by: str = None) -> List['ModeSchedule']:
        """Create activation and deactivation schedules for a special event"""
        activation = ModeSchedule(
            mode_name=mode_name,
            schedule_type="event",
            action="activate",
            scheduled_at=start_date,
            event_metadata={
                "event_name": event_name,
                "description": f"Special event: {event_name}",
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            created_by=created_by
        )

        deactivation = ModeSchedule(
            mode_name=mode_name,
            schedule_type="event",
            action="deactivate",
            scheduled_at=end_date,
            event_metadata={
                "event_name": event_name,
                "description": f"End special event: {event_name}",
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            created_by=created_by
        )

        return [activation, deactivation]

    def __str__(self) -> str:
        return f"ModeSchedule(id={self._id}, mode={self.mode_name}, action={self.action}, at={self.scheduled_at})"

    def __repr__(self) -> str:
        return self.__str__()