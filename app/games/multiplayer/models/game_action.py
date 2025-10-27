"""
Game Action Model

Represents a game action performed by a player in a multiplayer session.
Used for action logging, replay, and anti-cheat validation.
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional
from bson import ObjectId
from dataclasses import dataclass, field
from app.core.utils.json_encoder import serialize_model_dates


@dataclass
class GameAction:
    """Model representing a game action in a multiplayer session"""

    room_id: str
    user_id: str
    action_type: str  # move, stateUpdate, chat, pause, resume, surrender, rematch
    payload: Dict[str, Any]
    timestamp: datetime
    sequence_number: int
    action_id: Optional[str] = None  # Client-generated ID for idempotency
    is_valid: bool = True
    validation_message: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    _id: Optional[ObjectId] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB storage"""
        data = {
            "room_id": self.room_id,
            "user_id": self.user_id,
            "action_type": self.action_type,
            "payload": self.payload,
            "timestamp": self.timestamp,
            "sequence_number": self.sequence_number,
            "action_id": self.action_id,
            "is_valid": self.is_valid,
            "validation_message": self.validation_message,
            "created_at": self.created_at
        }

        if self._id:
            data["_id"] = self._id

        return serialize_model_dates(data)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GameAction':
        """Create GameAction from dictionary"""
        action = cls(
            room_id=data.get("room_id", ""),
            user_id=data.get("user_id", ""),
            action_type=data.get("action_type", "move"),
            payload=data.get("payload", {}),
            timestamp=data.get("timestamp", datetime.now(timezone.utc)),
            sequence_number=data.get("sequence_number", 0),
            action_id=data.get("action_id"),
            is_valid=data.get("is_valid", True),
            validation_message=data.get("validation_message"),
            created_at=data.get("created_at", datetime.now(timezone.utc))
        )

        if "_id" in data:
            action._id = data["_id"]

        return action

    def to_api_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "id": str(self._id) if self._id else None,
            "room_id": self.room_id,
            "user_id": self.user_id,
            "action_type": self.action_type,
            "payload": self.payload,
            "timestamp": self.timestamp.isoformat() if isinstance(self.timestamp, datetime) else self.timestamp,
            "sequence_number": self.sequence_number,
            "action_id": self.action_id,
            "is_valid": self.is_valid,
            "validation_message": self.validation_message,
            "created_at": self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at
        }

    def __str__(self) -> str:
        return f"GameAction(room={self.room_id}, user={self.user_id}, type={self.action_type}, seq={self.sequence_number})"

    def __repr__(self) -> str:
        return self.__str__()
