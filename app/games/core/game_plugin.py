from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass

@dataclass
class GameRules:
    """Represents the rules for a specific game"""
    min_players: int
    max_players: int
    estimated_duration_minutes: int
    difficulty_level: str  # easy, medium, hard
    requires_internet: bool
    description: str
    instructions: str

@dataclass
class GameSession:
    """Represents an active game session"""
    session_id: str
    user_id: str
    game_id: str
    status: str  # active, paused, completed, abandoned
    current_state: Dict[str, Any]
    score: Optional[int] = None
    credits_earned: Optional[int] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None

@dataclass
class SessionResult:
    """Represents the result of a completed game session"""
    session_id: str
    final_score: int
    credits_earned: int
    completion_time_seconds: int
    achievements_unlocked: list
    statistics: Dict[str, Any]

class GamePlugin(ABC):
    """Base class for all game plugins"""

    def __init__(self):
        self.name: str = ""
        self.version: str = ""
        self.description: str = ""
        self.category: str = ""
        self.author: str = ""
        self.credit_rate: float = 1.0  # Credits per minute
        self.is_initialized: bool = False

    @abstractmethod
    def initialize(self) -> bool:
        """
        Initialize the game plugin.

        Returns:
            bool: True if initialization successful, False otherwise
        """
        pass

    @abstractmethod
    def start_session(self, user_id: str, session_config: Optional[Dict[str, Any]] = None) -> GameSession:
        """
        Start a new game session for a user.

        Args:
            user_id: The ID of the user starting the session
            session_config: Optional configuration for the session

        Returns:
            GameSession: The created game session
        """
        pass

    @abstractmethod
    def end_session(self, session_id: str, reason: str = "completed") -> SessionResult:
        """
        End an active game session.

        Args:
            session_id: The ID of the session to end
            reason: The reason for ending (completed, abandoned, error)

        Returns:
            SessionResult: The result of the ended session
        """
        pass

    @abstractmethod
    def get_rules(self) -> GameRules:
        """
        Get the rules and metadata for this game.

        Returns:
            GameRules: The game rules and metadata
        """
        pass

    @abstractmethod
    def validate_move(self, session_id: str, move: Dict[str, Any]) -> bool:
        """
        Validate a move within a game session.

        Args:
            session_id: The ID of the active session
            move: The move data to validate

        Returns:
            bool: True if move is valid, False otherwise
        """
        pass

    @abstractmethod
    def get_session_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the current state of a game session.

        Args:
            session_id: The ID of the session

        Returns:
            Optional[Dict[str, Any]]: The session state or None if not found
        """
        pass

    @abstractmethod
    def update_session_state(self, session_id: str, new_state: Dict[str, Any]) -> bool:
        """
        Update the state of a game session.

        Args:
            session_id: The ID of the session
            new_state: The new state data

        Returns:
            bool: True if update successful, False otherwise
        """
        pass

    def get_plugin_info(self) -> Dict[str, Any]:
        """
        Get basic information about this plugin.

        Returns:
            Dict[str, Any]: Plugin information
        """
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "category": self.category,
            "author": self.author,
            "credit_rate": self.credit_rate,
            "is_initialized": self.is_initialized
        }

    def validate_plugin(self) -> Dict[str, Any]:
        """
        Validate the plugin configuration and requirements.

        Returns:
            Dict[str, Any]: Validation result with status and messages
        """
        errors = []
        warnings = []

        if not self.name:
            errors.append("Plugin name is required")

        if not self.version:
            errors.append("Plugin version is required")

        if not self.description:
            warnings.append("Plugin description is recommended")

        if not self.category:
            warnings.append("Plugin category is recommended")

        if self.credit_rate <= 0:
            errors.append("Credit rate must be positive")

        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }