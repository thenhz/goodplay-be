from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from bson import ObjectId
from dataclasses import dataclass, field
import uuid

@dataclass
class Challenge:
    """Challenge model representing a direct challenge between players"""
    challenger_id: str  # User ID who created the challenge
    challenged_ids: List[str] = field(default_factory=list)  # List of user IDs for NvN
    game_id: str = ""
    challenge_type: str = "1v1"  # '1v1', 'NvN', 'cross_game'
    status: str = "pending"  # 'pending', 'active', 'completed', 'cancelled', 'expired'
    game_config: Dict[str, Any] = field(default_factory=dict)
    challenge_config: Dict[str, Any] = field(default_factory=dict)
    results: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    winner_ids: List[str] = field(default_factory=list)
    total_participants: int = 0
    max_participants: int = 2
    min_participants: int = 2
    allow_spectators: bool = True
    is_public: bool = False
    challenge_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    _id: Optional[ObjectId] = field(default=None)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the challenge to a dictionary for MongoDB storage"""
        data = {
            "challenge_id": self.challenge_id,
            "challenger_id": self.challenger_id,
            "challenged_ids": self.challenged_ids,
            "game_id": self.game_id,
            "challenge_type": self.challenge_type,
            "status": self.status,
            "game_config": self.game_config,
            "challenge_config": self.challenge_config,
            "results": self.results,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "winner_ids": self.winner_ids,
            "total_participants": self.total_participants,
            "max_participants": self.max_participants,
            "min_participants": self.min_participants,
            "allow_spectators": self.allow_spectators,
            "is_public": self.is_public
        }

        if self._id:
            data["_id"] = self._id

        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Challenge':
        """Create a Challenge instance from a dictionary"""
        challenge = cls(
            challenger_id=data.get("challenger_id", ""),
            challenged_ids=data.get("challenged_ids", []),
            game_id=data.get("game_id", ""),
            challenge_type=data.get("challenge_type", "1v1"),
            status=data.get("status", "pending"),
            game_config=data.get("game_config", {}),
            challenge_config=data.get("challenge_config", {}),
            results=data.get("results", []),
            created_at=data.get("created_at", datetime.utcnow()),
            expires_at=data.get("expires_at"),
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at"),
            winner_ids=data.get("winner_ids", []),
            total_participants=data.get("total_participants", 0),
            max_participants=data.get("max_participants", 2),
            min_participants=data.get("min_participants", 2),
            allow_spectators=data.get("allow_spectators", True),
            is_public=data.get("is_public", False),
            challenge_id=data.get("challenge_id", str(uuid.uuid4()))
        )

        if "_id" in data:
            challenge._id = data["_id"]

        return challenge

    def to_api_dict(self) -> Dict[str, Any]:
        """Convert the challenge to a dictionary for API responses"""
        return {
            "id": str(self._id) if self._id else None,
            "challenge_id": self.challenge_id,
            "challenger_id": self.challenger_id,
            "challenged_ids": self.challenged_ids,
            "game_id": self.game_id,
            "challenge_type": self.challenge_type,
            "status": self.status,
            "game_config": self.game_config,
            "challenge_config": self.challenge_config,
            "results": self.results,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "winner_ids": self.winner_ids,
            "total_participants": self.total_participants,
            "max_participants": self.max_participants,
            "min_participants": self.min_participants,
            "allow_spectators": self.allow_spectators,
            "is_public": self.is_public,
            "time_remaining_seconds": self.get_time_remaining_seconds(),
            "can_start": self.can_start(),
            "all_participants": self.get_all_participant_ids()
        }

    def get_all_participant_ids(self) -> List[str]:
        """Get all participant IDs including challenger"""
        participants = [self.challenger_id]
        participants.extend(self.challenged_ids)
        return list(set(participants))  # Remove duplicates

    def add_participant(self, user_id: str) -> bool:
        """Add a participant to the challenge"""
        if user_id in self.get_all_participant_ids():
            return False  # Already participating

        if len(self.get_all_participant_ids()) >= self.max_participants:
            return False  # Challenge is full

        self.challenged_ids.append(user_id)
        self.total_participants = len(self.get_all_participant_ids())
        return True

    def remove_participant(self, user_id: str) -> bool:
        """Remove a participant from the challenge"""
        if user_id == self.challenger_id:
            return False  # Cannot remove challenger

        if user_id in self.challenged_ids:
            self.challenged_ids.remove(user_id)
            self.total_participants = len(self.get_all_participant_ids())
            return True

        return False

    def can_start(self) -> bool:
        """Check if challenge can start"""
        if self.status != "pending":
            return False

        if self.is_expired():
            return False

        participant_count = len(self.get_all_participant_ids())
        return participant_count >= self.min_participants

    def start_challenge(self) -> bool:
        """Start the challenge if conditions are met"""
        if not self.can_start():
            return False

        self.status = "active"
        self.started_at = datetime.utcnow()
        return True

    def complete_challenge(self, results: List[Dict[str, Any]]) -> bool:
        """Complete the challenge with results"""
        if self.status != "active":
            return False

        self.status = "completed"
        self.completed_at = datetime.utcnow()
        self.results = results

        # Determine winners
        if results:
            # Sort by score (descending) to find winners
            sorted_results = sorted(results, key=lambda x: x.get("score", 0), reverse=True)
            if sorted_results:
                highest_score = sorted_results[0].get("score", 0)
                self.winner_ids = [
                    r["user_id"] for r in sorted_results
                    if r.get("score", 0) == highest_score
                ]

        return True

    def cancel_challenge(self) -> bool:
        """Cancel the challenge"""
        if self.status in ["completed", "cancelled"]:
            return False

        self.status = "cancelled"
        self.completed_at = datetime.utcnow()
        return True

    def is_expired(self) -> bool:
        """Check if challenge has expired"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at

    def expire_challenge(self) -> bool:
        """Mark challenge as expired"""
        if self.status not in ["pending", "active"]:
            return False

        self.status = "expired"
        self.completed_at = datetime.utcnow()
        return True

    def get_time_remaining_seconds(self) -> Optional[int]:
        """Get time remaining until expiry in seconds"""
        if not self.expires_at:
            return None

        now = datetime.utcnow()
        if now >= self.expires_at:
            return 0

        return int((self.expires_at - now).total_seconds())

    def get_duration_seconds(self) -> Optional[int]:
        """Get challenge duration in seconds"""
        if not self.started_at:
            return None

        end_time = self.completed_at or datetime.utcnow()
        return int((end_time - self.started_at).total_seconds())

    def is_participant(self, user_id: str) -> bool:
        """Check if user is a participant"""
        return user_id in self.get_all_participant_ids()

    def get_participant_result(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get result for a specific participant"""
        for result in self.results:
            if result.get("user_id") == user_id:
                return result
        return None

    def add_result(self, user_id: str, score: int, additional_data: Dict[str, Any] = None) -> bool:
        """Add or update a participant's result"""
        if not self.is_participant(user_id):
            return False

        # Remove existing result if any
        self.results = [r for r in self.results if r.get("user_id") != user_id]

        # Add new result
        result = {
            "user_id": user_id,
            "score": score,
            "completed_at": datetime.utcnow(),
            **(additional_data or {})
        }
        self.results.append(result)
        return True

    @staticmethod
    def create_1v1_challenge(challenger_id: str, challenged_id: str, game_id: str,
                           timeout_minutes: int = 60, game_config: Dict[str, Any] = None) -> 'Challenge':
        """Create a 1v1 challenge"""
        expires_at = datetime.utcnow() + timedelta(minutes=timeout_minutes)

        return Challenge(
            challenger_id=challenger_id,
            challenged_ids=[challenged_id],
            game_id=game_id,
            challenge_type="1v1",
            max_participants=2,
            min_participants=2,
            expires_at=expires_at,
            game_config=game_config or {},
            challenge_config={
                "timeout_minutes": timeout_minutes,
                "auto_start": False
            }
        )

    @staticmethod
    def create_nvn_challenge(challenger_id: str, max_participants: int, game_id: str,
                           timeout_minutes: int = 60, game_config: Dict[str, Any] = None,
                           min_participants: int = None) -> 'Challenge':
        """Create an NvN challenge"""
        expires_at = datetime.utcnow() + timedelta(minutes=timeout_minutes)
        min_parts = min_participants or max(2, max_participants // 2)

        return Challenge(
            challenger_id=challenger_id,
            challenged_ids=[],
            game_id=game_id,
            challenge_type="NvN",
            max_participants=max_participants,
            min_participants=min_parts,
            expires_at=expires_at,
            game_config=game_config or {},
            challenge_config={
                "timeout_minutes": timeout_minutes,
                "auto_start": True,
                "public_join": True
            },
            is_public=True
        )

    @staticmethod
    def create_cross_game_challenge(challenger_id: str, challenged_id: str,
                                  challenger_game_id: str, challenged_game_id: str,
                                  timeout_minutes: int = 60) -> 'Challenge':
        """Create a cross-game challenge where each player plays a different game"""
        expires_at = datetime.utcnow() + timedelta(minutes=timeout_minutes)

        return Challenge(
            challenger_id=challenger_id,
            challenged_ids=[challenged_id],
            game_id="cross_game",  # Special identifier
            challenge_type="cross_game",
            max_participants=2,
            min_participants=2,
            expires_at=expires_at,
            game_config={
                "challenger_game": challenger_game_id,
                "challenged_game": challenged_game_id,
                "score_normalization": True
            },
            challenge_config={
                "timeout_minutes": timeout_minutes,
                "requires_score_normalization": True
            }
        )

    def __str__(self) -> str:
        return f"Challenge(id={self._id}, type={self.challenge_type}, status={self.status})"

    def __repr__(self) -> str:
        return self.__str__()