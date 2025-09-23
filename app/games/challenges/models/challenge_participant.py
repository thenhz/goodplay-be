from datetime import datetime
from typing import Dict, Any, Optional
from bson import ObjectId
from dataclasses import dataclass, field

@dataclass
class ChallengeParticipant:
    """ChallengeParticipant model representing a participant's involvement in a challenge"""
    challenge_id: str
    user_id: str
    participant_type: str = "challenged"  # 'challenger', 'challenged', 'joined'
    status: str = "invited"  # 'invited', 'accepted', 'declined', 'active', 'completed', 'dropped'
    joined_at: datetime = field(default_factory=datetime.utcnow)
    accepted_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    game_session_id: Optional[str] = None
    score: Optional[int] = None
    final_position: Optional[int] = None  # 1st, 2nd, 3rd, etc.
    performance_data: Dict[str, Any] = field(default_factory=dict)
    notification_preferences: Dict[str, Any] = field(default_factory=dict)
    _id: Optional[ObjectId] = field(default=None)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the participant to a dictionary for MongoDB storage"""
        data = {
            "challenge_id": self.challenge_id,
            "user_id": self.user_id,
            "participant_type": self.participant_type,
            "status": self.status,
            "joined_at": self.joined_at,
            "accepted_at": self.accepted_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "game_session_id": self.game_session_id,
            "score": self.score,
            "final_position": self.final_position,
            "performance_data": self.performance_data,
            "notification_preferences": self.notification_preferences
        }

        if self._id:
            data["_id"] = self._id

        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChallengeParticipant':
        """Create a ChallengeParticipant instance from a dictionary"""
        participant = cls(
            challenge_id=data.get("challenge_id", ""),
            user_id=data.get("user_id", ""),
            participant_type=data.get("participant_type", "challenged"),
            status=data.get("status", "invited"),
            joined_at=data.get("joined_at", datetime.utcnow()),
            accepted_at=data.get("accepted_at"),
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at"),
            game_session_id=data.get("game_session_id"),
            score=data.get("score"),
            final_position=data.get("final_position"),
            performance_data=data.get("performance_data", {}),
            notification_preferences=data.get("notification_preferences", {})
        )

        if "_id" in data:
            participant._id = data["_id"]

        return participant

    def to_api_dict(self) -> Dict[str, Any]:
        """Convert the participant to a dictionary for API responses"""
        return {
            "id": str(self._id) if self._id else None,
            "challenge_id": self.challenge_id,
            "user_id": self.user_id,
            "participant_type": self.participant_type,
            "status": self.status,
            "joined_at": self.joined_at.isoformat(),
            "accepted_at": self.accepted_at.isoformat() if self.accepted_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "game_session_id": self.game_session_id,
            "score": self.score,
            "final_position": self.final_position,
            "performance_data": self.performance_data,
            "notification_preferences": self.notification_preferences,
            "response_time_seconds": self.get_response_time_seconds(),
            "play_duration_seconds": self.get_play_duration_seconds()
        }

    def accept_challenge(self) -> bool:
        """Accept the challenge invitation"""
        if self.status != "invited":
            return False

        self.status = "accepted"
        self.accepted_at = datetime.utcnow()
        return True

    def decline_challenge(self) -> bool:
        """Decline the challenge invitation"""
        if self.status not in ["invited", "accepted"]:
            return False

        self.status = "declined"
        self.completed_at = datetime.utcnow()
        return True

    def start_playing(self, game_session_id: str) -> bool:
        """Mark participant as actively playing"""
        if self.status != "accepted":
            return False

        self.status = "active"
        self.started_at = datetime.utcnow()
        self.game_session_id = game_session_id
        return True

    def complete_participation(self, score: int, final_position: int = None,
                             performance_data: Dict[str, Any] = None) -> bool:
        """Complete the participant's involvement in the challenge"""
        if self.status != "active":
            return False

        self.status = "completed"
        self.completed_at = datetime.utcnow()
        self.score = score
        self.final_position = final_position

        if performance_data:
            self.performance_data.update(performance_data)

        return True

    def drop_out(self) -> bool:
        """Drop out from an active challenge"""
        if self.status not in ["accepted", "active"]:
            return False

        self.status = "dropped"
        self.completed_at = datetime.utcnow()
        return True

    def get_response_time_seconds(self) -> Optional[int]:
        """Get time taken to respond to invitation"""
        if not self.accepted_at:
            return None

        return int((self.accepted_at - self.joined_at).total_seconds())

    def get_play_duration_seconds(self) -> Optional[int]:
        """Get duration of actual gameplay"""
        if not self.started_at:
            return None

        end_time = self.completed_at or datetime.utcnow()
        return int((end_time - self.started_at).total_seconds())

    def is_challenger(self) -> bool:
        """Check if this participant is the challenger"""
        return self.participant_type == "challenger"

    def is_active(self) -> bool:
        """Check if participant is currently active in the challenge"""
        return self.status == "active"

    def has_completed(self) -> bool:
        """Check if participant has completed the challenge"""
        return self.status == "completed"

    def has_responded(self) -> bool:
        """Check if participant has responded to invitation"""
        return self.status not in ["invited"]

    def update_performance_data(self, data: Dict[str, Any]) -> None:
        """Update performance data"""
        self.performance_data.update(data)

    def set_notification_preferences(self, preferences: Dict[str, Any]) -> None:
        """Set notification preferences"""
        self.notification_preferences = preferences

    @staticmethod
    def create_challenger(challenge_id: str, user_id: str) -> 'ChallengeParticipant':
        """Create a challenger participant"""
        return ChallengeParticipant(
            challenge_id=challenge_id,
            user_id=user_id,
            participant_type="challenger",
            status="accepted",  # Challenger is automatically accepted
            accepted_at=datetime.utcnow(),
            notification_preferences={
                "accept_notifications": True,
                "start_notifications": True,
                "completion_notifications": True
            }
        )

    @staticmethod
    def create_invited(challenge_id: str, user_id: str) -> 'ChallengeParticipant':
        """Create an invited participant"""
        return ChallengeParticipant(
            challenge_id=challenge_id,
            user_id=user_id,
            participant_type="challenged",
            status="invited",
            notification_preferences={
                "accept_notifications": True,
                "start_notifications": True,
                "completion_notifications": True
            }
        )

    @staticmethod
    def create_joined(challenge_id: str, user_id: str) -> 'ChallengeParticipant':
        """Create a participant who joined a public challenge"""
        return ChallengeParticipant(
            challenge_id=challenge_id,
            user_id=user_id,
            participant_type="joined",
            status="accepted",  # Auto-accepted for public challenges
            accepted_at=datetime.utcnow(),
            notification_preferences={
                "accept_notifications": False,  # Already joined
                "start_notifications": True,
                "completion_notifications": True
            }
        )

    def __str__(self) -> str:
        return f"ChallengeParticipant(user={self.user_id}, challenge={self.challenge_id}, status={self.status})"

    def __repr__(self) -> str:
        return self.__str__()