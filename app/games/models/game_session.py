from datetime import datetime
from typing import Dict, Any, Optional, List
from bson import ObjectId
from dataclasses import dataclass, field
import uuid

@dataclass
class GameSession:
    """GameSession model representing an active or completed game session"""
    user_id: str
    game_id: str
    status: str = "active"  # active, paused, completed, abandoned
    current_state: Dict[str, Any] = field(default_factory=dict)
    score: Optional[int] = None
    credits_earned: Optional[int] = None
    started_at: datetime = field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None
    session_config: Dict[str, Any] = field(default_factory=dict)
    moves: List[Dict[str, Any]] = field(default_factory=list)
    achievements_unlocked: List[str] = field(default_factory=list)
    statistics: Dict[str, Any] = field(default_factory=dict)
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    _id: Optional[ObjectId] = field(default=None)

    # Enhanced fields for GOO-9
    play_duration: int = 0  # milliseconds of actual play time
    paused_at: Optional[datetime] = None
    resumed_at: Optional[datetime] = None
    moves_count: int = 0
    device_info: Dict[str, Any] = field(default_factory=dict)
    last_sync_at: Optional[datetime] = None
    sync_version: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the game session to a dictionary for MongoDB storage"""
        data = {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "game_id": self.game_id,
            "status": self.status,
            "current_state": self.current_state,
            "score": self.score,
            "credits_earned": self.credits_earned,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "session_config": self.session_config,
            "moves": self.moves,
            "achievements_unlocked": self.achievements_unlocked,
            "statistics": self.statistics,
            "play_duration": self.play_duration,
            "paused_at": self.paused_at,
            "resumed_at": self.resumed_at,
            "moves_count": self.moves_count,
            "device_info": self.device_info,
            "last_sync_at": self.last_sync_at,
            "sync_version": self.sync_version,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

        if self._id:
            data["_id"] = self._id

        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GameSession':
        """Create a GameSession instance from a dictionary"""
        session = cls(
            user_id=data.get("user_id", ""),
            game_id=data.get("game_id", ""),
            status=data.get("status", "active"),
            current_state=data.get("current_state", {}),
            score=data.get("score"),
            credits_earned=data.get("credits_earned"),
            started_at=data.get("started_at", datetime.utcnow()),
            ended_at=data.get("ended_at"),
            session_config=data.get("session_config", {}),
            moves=data.get("moves", []),
            achievements_unlocked=data.get("achievements_unlocked", []),
            statistics=data.get("statistics", {}),
            session_id=data.get("session_id", str(uuid.uuid4())),
            play_duration=data.get("play_duration", 0),
            paused_at=data.get("paused_at"),
            resumed_at=data.get("resumed_at"),
            moves_count=data.get("moves_count", 0),
            device_info=data.get("device_info", {}),
            last_sync_at=data.get("last_sync_at"),
            sync_version=data.get("sync_version", 0),
            created_at=data.get("created_at", datetime.utcnow()),
            updated_at=data.get("updated_at", datetime.utcnow())
        )

        if "_id" in data:
            session._id = data["_id"]

        return session

    def to_api_dict(self) -> Dict[str, Any]:
        """Convert the game session to a dictionary for API responses"""
        return {
            "id": str(self._id) if self._id else None,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "game_id": self.game_id,
            "status": self.status,
            "current_state": self.current_state,
            "score": self.score,
            "credits_earned": self.credits_earned,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "session_config": self.session_config,
            "moves_count": self.moves_count or len(self.moves),
            "achievements_unlocked": self.achievements_unlocked,
            "statistics": self.statistics,
            "duration_seconds": self.get_duration_seconds(),
            "play_duration_ms": self.play_duration,
            "play_duration_seconds": self.play_duration / 1000 if self.play_duration else 0,
            "paused_at": self.paused_at.isoformat() if self.paused_at else None,
            "resumed_at": self.resumed_at.isoformat() if self.resumed_at else None,
            "device_info": self.device_info,
            "last_sync_at": self.last_sync_at.isoformat() if self.last_sync_at else None,
            "sync_version": self.sync_version,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    def get_duration_seconds(self) -> Optional[int]:
        """Get the duration of the session in seconds"""
        if not self.started_at:
            return None

        end_time = self.ended_at or datetime.utcnow()
        duration = end_time - self.started_at
        return int(duration.total_seconds())

    def add_move(self, move: Dict[str, Any]) -> None:
        """Add a move to the session"""
        move_with_timestamp = {
            **move,
            "timestamp": datetime.utcnow(),
            "move_number": len(self.moves) + 1
        }
        self.moves.append(move_with_timestamp)
        self.moves_count = len(self.moves)
        self.updated_at = datetime.utcnow()

    def update_state(self, new_state: Dict[str, Any]) -> None:
        """Update the current game state"""
        self.current_state = new_state
        self.updated_at = datetime.utcnow()

    def update_score(self, new_score: int) -> None:
        """Update the session score"""
        self.score = new_score
        self.updated_at = datetime.utcnow()

    def calculate_credits_earned_precise(self, credit_rate: float) -> int:
        """Calculate credits earned based on precise play duration and rate"""
        play_duration_minutes = self.play_duration / (1000 * 60) if self.play_duration else 0
        credits = int(play_duration_minutes * credit_rate)
        self.credits_earned = credits
        return credits

    def calculate_credits_earned(self, credit_rate: float) -> int:
        """Calculate credits earned based on duration and rate (legacy method)"""
        duration_seconds = self.get_duration_seconds()
        if duration_seconds is None:
            return 0

        duration_minutes = duration_seconds / 60
        credits = int(duration_minutes * credit_rate)
        self.credits_earned = credits
        return credits

    def add_achievement(self, achievement_id: str) -> None:
        """Add an achievement to the session"""
        if achievement_id not in self.achievements_unlocked:
            self.achievements_unlocked.append(achievement_id)
            self.updated_at = datetime.utcnow()

    def update_statistics(self, stats: Dict[str, Any]) -> None:
        """Update session statistics"""
        self.statistics.update(stats)
        self.updated_at = datetime.utcnow()

    def pause_session(self) -> None:
        """Pause the session with precise time tracking"""
        if self.status == "active":
            now = datetime.utcnow()

            # Update play duration before pausing
            if self.resumed_at:
                # Add time since last resume
                play_time_ms = int((now - self.resumed_at).total_seconds() * 1000)
                self.play_duration += play_time_ms
            elif self.paused_at is None and self.started_at:
                # First pause - add time since start
                play_time_ms = int((now - self.started_at).total_seconds() * 1000)
                self.play_duration += play_time_ms

            self.status = "paused"
            self.paused_at = now
            self.updated_at = now

    def resume_session(self) -> None:
        """Resume a paused session with precise time tracking"""
        if self.status == "paused":
            self.status = "active"
            self.resumed_at = datetime.utcnow()
            self.updated_at = datetime.utcnow()

    def get_precise_play_duration_ms(self) -> int:
        """Get precise play duration in milliseconds"""
        if self.status == "active":
            # Calculate current play time
            now = datetime.utcnow()
            if self.resumed_at:
                # Add current active time since last resume
                current_play_ms = int((now - self.resumed_at).total_seconds() * 1000)
                return self.play_duration + current_play_ms
            elif not self.paused_at and self.started_at:
                # Never paused, add time since start
                current_play_ms = int((now - self.started_at).total_seconds() * 1000)
                return self.play_duration + current_play_ms

        return self.play_duration

    def update_device_info(self, device_info: Dict[str, Any]) -> None:
        """Update device information for cross-device sync"""
        self.device_info = device_info
        self.updated_at = datetime.utcnow()

    def update_sync_info(self) -> None:
        """Update synchronization information"""
        self.last_sync_at = datetime.utcnow()
        self.sync_version += 1
        self.updated_at = datetime.utcnow()

    def complete_session(self, final_score: Optional[int] = None) -> None:
        """Complete the session with precise time tracking"""
        now = datetime.utcnow()

        # Update final play duration if session was active
        if self.status == "active":
            if self.resumed_at:
                # Add time since last resume
                play_time_ms = int((now - self.resumed_at).total_seconds() * 1000)
                self.play_duration += play_time_ms
            elif self.paused_at is None and self.started_at:
                # Never paused, add time since start
                play_time_ms = int((now - self.started_at).total_seconds() * 1000)
                self.play_duration += play_time_ms

        self.status = "completed"
        self.ended_at = now

        if final_score is not None:
            self.score = final_score

        self.updated_at = now

    def abandon_session(self) -> None:
        """Abandon the session with precise time tracking"""
        now = datetime.utcnow()

        # Update final play duration if session was active
        if self.status == "active":
            if self.resumed_at:
                # Add time since last resume
                play_time_ms = int((now - self.resumed_at).total_seconds() * 1000)
                self.play_duration += play_time_ms
            elif self.paused_at is None and self.started_at:
                # Never paused, add time since start
                play_time_ms = int((now - self.started_at).total_seconds() * 1000)
                self.play_duration += play_time_ms

        self.status = "abandoned"
        self.ended_at = now
        self.updated_at = now

    def is_active(self) -> bool:
        """Check if the session is active"""
        return self.status == "active"

    def is_completed(self) -> bool:
        """Check if the session is completed"""
        return self.status == "completed"

    def is_ended(self) -> bool:
        """Check if the session has ended (completed or abandoned)"""
        return self.status in ["completed", "abandoned"]

    def get_session_summary(self) -> Dict[str, Any]:
        """Get a summary of the session"""
        return {
            "session_id": self.session_id,
            "status": self.status,
            "duration_seconds": self.get_duration_seconds(),
            "score": self.score,
            "credits_earned": self.credits_earned,
            "moves_count": len(self.moves),
            "achievements_count": len(self.achievements_unlocked),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None
        }

    def __str__(self) -> str:
        return f"GameSession(id={self._id}, session_id={self.session_id}, status={self.status})"

    def __repr__(self) -> str:
        return self.__str__()