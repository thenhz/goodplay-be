"""
Service Layer Abstract Interfaces for GoodPlay

Defines abstract interfaces for service layer classes to enable
dependency injection, proper testing, and maintainable architecture.

These interfaces define the business logic contracts that services
must implement, promoting loose coupling and testability.
"""
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, Tuple, Union
from datetime import datetime


class IAuthService(ABC):
    """
    Abstract interface for Authentication service operations.

    Handles user registration, login, token management, and authentication.
    """

    @abstractmethod
    def register_user(self, user_data: Dict[str, Any]) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Register a new user account.

        Args:
            user_data: User registration data

        Returns:
            Tuple[bool, str, Optional[Dict]]: (success, message, user_data)

        Example:
            success, message, user = auth_service.register_user({
                "email": "user@example.com",
                "password": "secure123",
                "first_name": "John",
                "last_name": "Doe"
            })
        """
        pass

    @abstractmethod
    def login_user(self, email: str, password: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Authenticate user login.

        Args:
            email: User's email address
            password: User's password

        Returns:
            Tuple[bool, str, Optional[Dict]]: (success, message, token_data)
        """
        pass

    @abstractmethod
    def refresh_token(self, refresh_token: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: Valid refresh token

        Returns:
            Tuple[bool, str, Optional[Dict]]: (success, message, new_token_data)
        """
        pass

    @abstractmethod
    def validate_token(self, access_token: str) -> Tuple[bool, Optional[str]]:
        """
        Validate access token and get user ID.

        Args:
            access_token: JWT access token

        Returns:
            Tuple[bool, Optional[str]]: (is_valid, user_id)
        """
        pass

    @abstractmethod
    def logout_user(self, user_id: str) -> Tuple[bool, str]:
        """
        Log out user and invalidate tokens.

        Args:
            user_id: User's unique identifier

        Returns:
            Tuple[bool, str]: (success, message)
        """
        pass


class IGameService(ABC):
    """
    Abstract interface for Game service operations.

    Handles game management, installation, session tracking, and game statistics.
    """

    @abstractmethod
    def create_game_session(
        self,
        user_id: str,
        game_id: str,
        device_info: Dict[str, Any]
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Create a new game session.

        Args:
            user_id: User's unique identifier
            game_id: Game's unique identifier
            device_info: Device information for cross-platform sync

        Returns:
            Tuple[bool, str, Optional[str]]: (success, message, session_id)
        """
        pass

    @abstractmethod
    def update_session_state(
        self,
        session_id: str,
        game_state: Dict[str, Any],
        score: int,
        play_duration_ms: int
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Update game session state and sync across devices.

        Args:
            session_id: Session's unique identifier
            game_state: Current game state data
            score: Current game score
            play_duration_ms: Play duration in milliseconds

        Returns:
            Tuple[bool, str, Optional[Dict]]: (success, message, sync_data)
        """
        pass

    @abstractmethod
    def complete_session(
        self,
        session_id: str,
        final_score: int,
        achievements_unlocked: List[str] = None
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Complete a game session and process results.

        Args:
            session_id: Session's unique identifier
            final_score: Final game score
            achievements_unlocked: List of achievement IDs unlocked

        Returns:
            Tuple[bool, str, Optional[Dict]]: (success, message, completion_data)
        """
        pass

    @abstractmethod
    def get_user_sessions(
        self,
        user_id: str,
        status: Optional[str] = None,
        limit: int = 20
    ) -> Tuple[bool, str, Optional[List[Dict[str, Any]]]]:
        """
        Get user's game sessions.

        Args:
            user_id: User's unique identifier
            status: Filter by session status
            limit: Maximum number of sessions to return

        Returns:
            Tuple[bool, str, Optional[List[Dict]]]: (success, message, sessions)
        """
        pass

    @abstractmethod
    def sync_cross_device_session(
        self,
        user_id: str,
        session_id: str,
        device_info: Dict[str, Any]
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Synchronize session across devices.

        Args:
            user_id: User's unique identifier
            session_id: Session's unique identifier
            device_info: Target device information

        Returns:
            Tuple[bool, str, Optional[Dict]]: (success, message, sync_result)
        """
        pass


class ISocialService(ABC):
    """
    Abstract interface for Social service operations.

    Handles friendships, achievements, leaderboards, and social interactions.
    """

    @abstractmethod
    def send_friend_request(self, user_id: str, target_user_id: str) -> Tuple[bool, str]:
        """
        Send a friend request.

        Args:
            user_id: Requesting user's ID
            target_user_id: Target user's ID

        Returns:
            Tuple[bool, str]: (success, message)
        """
        pass

    @abstractmethod
    def accept_friend_request(self, user_id: str, request_id: str) -> Tuple[bool, str]:
        """
        Accept a friend request.

        Args:
            user_id: User accepting the request
            request_id: Friend request ID

        Returns:
            Tuple[bool, str]: (success, message)
        """
        pass

    @abstractmethod
    def get_user_friends(
        self,
        user_id: str,
        limit: int = 50
    ) -> Tuple[bool, str, Optional[List[Dict[str, Any]]]]:
        """
        Get user's friends list.

        Args:
            user_id: User's unique identifier
            limit: Maximum number of friends to return

        Returns:
            Tuple[bool, str, Optional[List[Dict]]]: (success, message, friends)
        """
        pass

    @abstractmethod
    def track_achievement_progress(
        self,
        user_id: str,
        achievement_type: str,
        progress_data: Dict[str, Any]
    ) -> Tuple[bool, str, Optional[List[str]]]:
        """
        Track user achievement progress and unlock achievements.

        Args:
            user_id: User's unique identifier
            achievement_type: Type of achievement to track
            progress_data: Progress information

        Returns:
            Tuple[bool, str, Optional[List[str]]]: (success, message, unlocked_achievement_ids)
        """
        pass

    @abstractmethod
    def get_leaderboard(
        self,
        leaderboard_type: str = "global",
        period: str = "weekly",
        limit: int = 50
    ) -> Tuple[bool, str, Optional[List[Dict[str, Any]]]]:
        """
        Get leaderboard data.

        Args:
            leaderboard_type: Type of leaderboard
            period: Time period
            limit: Maximum number of entries

        Returns:
            Tuple[bool, str, Optional[List[Dict]]]: (success, message, leaderboard)
        """
        pass


class IPreferencesService(ABC):
    """
    Abstract interface for User Preferences service operations.

    Manages user preferences across gaming, notifications, privacy, and donations.
    """

    @abstractmethod
    def get_user_preferences(
        self,
        user_id: str
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Get all user preferences.

        Args:
            user_id: User's unique identifier

        Returns:
            Tuple[bool, str, Optional[Dict]]: (success, message, preferences)
        """
        pass

    @abstractmethod
    def update_preferences(
        self,
        user_id: str,
        preferences_data: Dict[str, Any]
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Update user preferences.

        Args:
            user_id: User's unique identifier
            preferences_data: Preferences data by category

        Returns:
            Tuple[bool, str, Optional[Dict]]: (success, message, updated_preferences)
        """
        pass

    @abstractmethod
    def update_category(
        self,
        user_id: str,
        category: str,
        category_preferences: Dict[str, Any]
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Update a specific preferences category.

        Args:
            user_id: User's unique identifier
            category: Preferences category
            category_preferences: Category-specific preferences

        Returns:
            Tuple[bool, str, Optional[Dict]]: (success, message, updated_category)
        """
        pass

    @abstractmethod
    def reset_to_defaults(self, user_id: str) -> Tuple[bool, str]:
        """
        Reset user preferences to default values.

        Args:
            user_id: User's unique identifier

        Returns:
            Tuple[bool, str]: (success, message)
        """
        pass


class IChallengeService(ABC):
    """
    Abstract interface for Challenge service operations.

    Manages player challenges, matchmaking, and competitive gameplay.
    """

    @abstractmethod
    def create_challenge(
        self,
        creator_id: str,
        challenge_data: Dict[str, Any]
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Create a new challenge.

        Args:
            creator_id: Challenge creator's ID
            challenge_data: Challenge configuration data

        Returns:
            Tuple[bool, str, Optional[str]]: (success, message, challenge_id)
        """
        pass

    @abstractmethod
    def join_challenge(self, user_id: str, challenge_id: str) -> Tuple[bool, str]:
        """
        Join an existing challenge.

        Args:
            user_id: User's unique identifier
            challenge_id: Challenge's unique identifier

        Returns:
            Tuple[bool, str]: (success, message)
        """
        pass

    @abstractmethod
    def find_matchmaking_opponent(
        self,
        user_id: str,
        game_id: str,
        skill_level: str
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Find a suitable opponent for matchmaking.

        Args:
            user_id: User's unique identifier
            game_id: Game's unique identifier
            skill_level: User's skill level

        Returns:
            Tuple[bool, str, Optional[str]]: (success, message, challenge_id)
        """
        pass

    @abstractmethod
    def submit_challenge_result(
        self,
        user_id: str,
        challenge_id: str,
        result_data: Dict[str, Any]
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Submit challenge result.

        Args:
            user_id: User's unique identifier
            challenge_id: Challenge's unique identifier
            result_data: Challenge result data

        Returns:
            Tuple[bool, str, Optional[Dict]]: (success, message, final_results)
        """
        pass


class ITeamService(ABC):
    """
    Abstract interface for Team service operations.

    Manages global teams, team tournaments, and team-based competitions.
    """

    @abstractmethod
    def assign_user_to_team(self, user_id: str) -> Tuple[bool, str, Optional[str]]:
        """
        Automatically assign user to a balanced team.

        Args:
            user_id: User's unique identifier

        Returns:
            Tuple[bool, str, Optional[str]]: (success, message, team_id)
        """
        pass

    @abstractmethod
    def get_team_info(self, team_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Get team information and statistics.

        Args:
            team_id: Team's unique identifier

        Returns:
            Tuple[bool, str, Optional[Dict]]: (success, message, team_info)
        """
        pass

    @abstractmethod
    def get_team_leaderboard(
        self,
        limit: int = 10
    ) -> Tuple[bool, str, Optional[List[Dict[str, Any]]]]:
        """
        Get team leaderboard.

        Args:
            limit: Maximum number of teams to return

        Returns:
            Tuple[bool, str, Optional[List[Dict]]]: (success, message, leaderboard)
        """
        pass

    @abstractmethod
    def contribute_to_team_score(
        self,
        user_id: str,
        score_contribution: int,
        source: str
    ) -> Tuple[bool, str]:
        """
        Add score contribution to user's team.

        Args:
            user_id: User's unique identifier
            score_contribution: Score points to contribute
            source: Source of the contribution (game, challenge, etc.)

        Returns:
            Tuple[bool, str]: (success, message)
        """
        pass


class INotificationService(ABC):
    """
    Abstract interface for Notification service operations.

    Handles push notifications, email notifications, and in-app notifications.
    """

    @abstractmethod
    def send_push_notification(
        self,
        user_id: str,
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, str]:
        """
        Send push notification to user.

        Args:
            user_id: User's unique identifier
            title: Notification title
            message: Notification message
            data: Additional notification data

        Returns:
            Tuple[bool, str]: (success, message)
        """
        pass

    @abstractmethod
    def send_achievement_notification(
        self,
        user_id: str,
        achievement_id: str
    ) -> Tuple[bool, str]:
        """
        Send achievement unlock notification.

        Args:
            user_id: User's unique identifier
            achievement_id: Achievement's unique identifier

        Returns:
            Tuple[bool, str]: (success, message)
        """
        pass

    @abstractmethod
    def send_friend_request_notification(
        self,
        target_user_id: str,
        sender_user_id: str
    ) -> Tuple[bool, str]:
        """
        Send friend request notification.

        Args:
            target_user_id: Recipient user's ID
            sender_user_id: Sender user's ID

        Returns:
            Tuple[bool, str]: (success, message)
        """
        pass