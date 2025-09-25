"""
Domain-Specific Repository Interfaces for GoodPlay

Defines abstract interfaces for all domain repository classes to enable
proper dependency injection, type safety, and comprehensive testing.

These interfaces provide 1:1 mapping with concrete repository implementations
while maintaining clean separation of concerns and enabling mock testing.
"""
from abc import abstractmethod
from typing import Optional, List, Dict, Any, Union
from datetime import datetime

from .base_interfaces import IBaseRepository


class IUserRepository(IBaseRepository['User']):
    """
    Abstract interface for User repository operations.

    Provides comprehensive user management functionality including
    authentication, profile management, and user statistics.
    """

    @abstractmethod
    def find_by_email(self, email: str) -> Optional['User']:
        """
        Find a user by email address.

        Args:
            email: User's email address (case insensitive)

        Returns:
            Optional[User]: User instance if found, None otherwise

        Example:
            user = repository.find_by_email("user@goodplay.com")
        """
        pass

    @abstractmethod
    def find_user_by_id(self, user_id: str) -> Optional['User']:
        """
        Find a user by their unique ID.

        Args:
            user_id: User's unique identifier

        Returns:
            Optional[User]: User instance if found, None otherwise
        """
        pass

    @abstractmethod
    def create_user(self, user: 'User') -> str:
        """
        Create a new user account.

        Args:
            user: User instance to create

        Returns:
            str: Created user's ID

        Raises:
            DuplicateError: If email already exists

        Example:
            user_id = repository.create_user(new_user)
        """
        pass

    @abstractmethod
    def update_user(self, user_id: str, user: 'User') -> bool:
        """
        Update an existing user.

        Args:
            user_id: User's unique identifier
            user: Updated user instance

        Returns:
            bool: True if updated successfully
        """
        pass

    @abstractmethod
    def email_exists(self, email: str, exclude_user_id: str = None) -> bool:
        """
        Check if an email address is already registered.

        Args:
            email: Email address to check
            exclude_user_id: User ID to exclude from check (for updates)

        Returns:
            bool: True if email exists, False otherwise

        Example:
            if repository.email_exists("test@example.com"):
                raise ValueError("Email already registered")
        """
        pass

    @abstractmethod
    def find_active_users(
        self,
        limit: Optional[int] = None,
        skip: Optional[int] = None
    ) -> List['User']:
        """
        Find active users sorted by creation date.

        Args:
            limit: Maximum number of users to return
            skip: Number of users to skip (pagination)

        Returns:
            List[User]: List of active users
        """
        pass

    @abstractmethod
    def deactivate_user(self, user_id: str) -> bool:
        """
        Deactivate a user account.

        Args:
            user_id: User's unique identifier

        Returns:
            bool: True if deactivated successfully
        """
        pass

    @abstractmethod
    def activate_user(self, user_id: str) -> bool:
        """
        Activate a user account.

        Args:
            user_id: User's unique identifier

        Returns:
            bool: True if activated successfully
        """
        pass

    @abstractmethod
    def update_gaming_stats(
        self,
        user_id: str,
        play_time: int = 0,
        game_category: Optional[str] = None
    ) -> bool:
        """
        Update user gaming statistics.

        Args:
            user_id: User's unique identifier
            play_time: Additional play time in seconds
            game_category: Game category to update as favorite

        Returns:
            bool: True if updated successfully

        Example:
            repository.update_gaming_stats(user_id, 1800, "puzzle")
        """
        pass

    @abstractmethod
    def update_wallet_credits(
        self,
        user_id: str,
        amount: float,
        transaction_type: str = 'earned'
    ) -> bool:
        """
        Update user wallet credits.

        Args:
            user_id: User's unique identifier
            amount: Credit amount to add/subtract
            transaction_type: Type of transaction ('earned', 'donated', 'balance_only')

        Returns:
            bool: True if updated successfully
        """
        pass

    @abstractmethod
    def get_leaderboard_data(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get users for leaderboard sorted by impact score.

        Args:
            limit: Maximum number of users to return

        Returns:
            List[Dict[str, Any]]: Leaderboard data with user info and scores
        """
        pass

    @abstractmethod
    def find_users_by_game_category(
        self,
        category: str,
        limit: int = 10
    ) -> List['User']:
        """
        Find users who prefer a specific game category.

        Args:
            category: Game category to filter by
            limit: Maximum number of users to return

        Returns:
            List[User]: Users who prefer the category
        """
        pass


class IGameRepository(IBaseRepository['Game']):
    """
    Abstract interface for Game repository operations.

    Manages game catalog, installations, ratings, and metadata.
    """

    @abstractmethod
    def create_game(self, game: 'Game') -> Optional[str]:
        """
        Create a new game in the catalog.

        Args:
            game: Game instance to create

        Returns:
            Optional[str]: Game ID if successful, None otherwise
        """
        pass

    @abstractmethod
    def get_game_by_id(self, game_id: str) -> Optional['Game']:
        """
        Get a game by its unique ID.

        Args:
            game_id: Game's unique identifier

        Returns:
            Optional[Game]: Game instance if found, None otherwise
        """
        pass

    @abstractmethod
    def get_game_by_plugin_id(self, plugin_id: str) -> Optional['Game']:
        """
        Get a game by its plugin identifier.

        Args:
            plugin_id: Game's plugin identifier

        Returns:
            Optional[Game]: Game instance if found, None otherwise
        """
        pass

    @abstractmethod
    def get_game_by_name(self, name: str) -> Optional['Game']:
        """
        Get a game by its name.

        Args:
            name: Game's name

        Returns:
            Optional[Game]: Game instance if found, None otherwise
        """
        pass

    @abstractmethod
    def get_games_by_category(
        self,
        category: str,
        active_only: bool = True
    ) -> List['Game']:
        """
        Get games in a specific category.

        Args:
            category: Game category to filter by
            active_only: If True, only return active games

        Returns:
            List[Game]: Games in the specified category
        """
        pass

    @abstractmethod
    def get_all_games(
        self,
        active_only: bool = True,
        limit: Optional[int] = None,
        skip: Optional[int] = None,
        sort_by: str = "created_at"
    ) -> List['Game']:
        """
        Get all games with optional filtering and sorting.

        Args:
            active_only: If True, only return active games
            limit: Maximum number of games to return
            skip: Number of games to skip (pagination)
            sort_by: Field to sort by (created_at, rating, install_count, name)

        Returns:
            List[Game]: List of games
        """
        pass

    @abstractmethod
    def update_game(self, game_id: str, game: 'Game') -> bool:
        """
        Update an existing game.

        Args:
            game_id: Game's unique identifier
            game: Updated game instance

        Returns:
            bool: True if updated successfully
        """
        pass

    @abstractmethod
    def update_game_rating(
        self,
        game_id: str,
        new_rating: float,
        total_ratings: int
    ) -> bool:
        """
        Update a game's rating statistics.

        Args:
            game_id: Game's unique identifier
            new_rating: New average rating
            total_ratings: Total number of ratings

        Returns:
            bool: True if updated successfully
        """
        pass

    @abstractmethod
    def increment_install_count(self, game_id: str) -> bool:
        """
        Increment the install count for a game.

        Args:
            game_id: Game's unique identifier

        Returns:
            bool: True if incremented successfully
        """
        pass

    @abstractmethod
    def set_game_active_status(self, game_id: str, is_active: bool) -> bool:
        """
        Set the active status of a game.

        Args:
            game_id: Game's unique identifier
            is_active: New active status

        Returns:
            bool: True if updated successfully
        """
        pass

    @abstractmethod
    def search_games(self, query: str, active_only: bool = True) -> List['Game']:
        """
        Search games by name or description.

        Args:
            query: Search query string
            active_only: If True, only search active games

        Returns:
            List[Game]: Matching games sorted by relevance
        """
        pass

    @abstractmethod
    def get_games_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive game catalog statistics.

        Args:
            None

        Returns:
            Dict[str, Any]: Statistics including total games, categories, ratings
        """
        pass


class IGameSessionRepository(IBaseRepository['GameSession']):
    """
    Abstract interface for Game Session repository operations.

    Manages game sessions, cross-device sync, and session state.
    """

    @abstractmethod
    def create_session(self, session: 'GameSession') -> str:
        """
        Create a new game session.

        Args:
            session: GameSession instance to create

        Returns:
            str: Created session's ID
        """
        pass

    @abstractmethod
    def get_session_by_id(self, session_id: str) -> Optional['GameSession']:
        """
        Get a session by its ID.

        Args:
            session_id: Session's unique identifier

        Returns:
            Optional[GameSession]: Session if found, None otherwise
        """
        pass

    @abstractmethod
    def get_active_sessions_by_user(self, user_id: str) -> List['GameSession']:
        """
        Get all active sessions for a user.

        Args:
            user_id: User's unique identifier

        Returns:
            List[GameSession]: Active sessions for the user
        """
        pass

    @abstractmethod
    def update_session_state(
        self,
        session_id: str,
        game_state: Dict[str, Any],
        sync_version: int
    ) -> bool:
        """
        Update session game state with sync version.

        Args:
            session_id: Session's unique identifier
            game_state: New game state data
            sync_version: Sync version for conflict resolution

        Returns:
            bool: True if updated successfully
        """
        pass

    @abstractmethod
    def complete_session(
        self,
        session_id: str,
        final_score: int,
        play_duration_ms: int
    ) -> bool:
        """
        Mark a session as completed.

        Args:
            session_id: Session's unique identifier
            final_score: Final game score
            play_duration_ms: Total play duration in milliseconds

        Returns:
            bool: True if completed successfully
        """
        pass


class IPreferencesRepository:
    """
    Abstract interface for User Preferences repository operations.

    Note: PreferencesRepository is a specialized repository that works
    with the User model rather than extending IBaseRepository directly.
    """

    @abstractmethod
    def get_user_preferences(self, user_id: str) -> Optional['User']:
        """
        Get full user object for preferences management.

        Args:
            user_id: User's unique identifier

        Returns:
            Optional[User]: User instance with preferences
        """
        pass

    @abstractmethod
    def update_preferences(
        self,
        user_id: str,
        preferences_data: Dict[str, Any]
    ) -> bool:
        """
        Update user preferences.

        Args:
            user_id: User's unique identifier
            preferences_data: Preferences data by category

        Returns:
            bool: True if updated successfully

        Example:
            repository.update_preferences(user_id, {
                "gaming": {"difficulty": "hard"},
                "notifications": {"email_enabled": True}
            })
        """
        pass

    @abstractmethod
    def update_category(
        self,
        user_id: str,
        category: str,
        category_preferences: Dict[str, Any]
    ) -> bool:
        """
        Update a specific preferences category.

        Args:
            user_id: User's unique identifier
            category: Preferences category (gaming, notifications, privacy, donations)
            category_preferences: Category-specific preferences

        Returns:
            bool: True if updated successfully
        """
        pass

    @abstractmethod
    def reset_to_defaults(self, user_id: str) -> bool:
        """
        Reset user preferences to default values.

        Args:
            user_id: User's unique identifier

        Returns:
            bool: True if reset successfully
        """
        pass

    @abstractmethod
    def get_category_preferences(
        self,
        user_id: str,
        category: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get preferences for a specific category.

        Args:
            user_id: User's unique identifier
            category: Preferences category to retrieve

        Returns:
            Optional[Dict[str, Any]]: Category preferences if found
        """
        pass

    @abstractmethod
    def create_indexes(self) -> None:
        """
        Create database indexes for optimal query performance.

        Args:
            None

        Returns:
            None
        """
        pass


class IAchievementRepository(IBaseRepository['Achievement']):
    """
    Abstract interface for Achievement system repository operations.

    Manages achievements, user progress, badges, and achievement statistics.
    """

    @abstractmethod
    def create_achievement(self, achievement: 'Achievement') -> str:
        """
        Create a new achievement.

        Args:
            achievement: Achievement instance to create

        Returns:
            str: Created achievement's ID
        """
        pass

    @abstractmethod
    def find_achievement_by_id(self, achievement_id: str) -> Optional['Achievement']:
        """
        Find achievement by its ID.

        Args:
            achievement_id: Achievement's unique identifier

        Returns:
            Optional[Achievement]: Achievement if found, None otherwise
        """
        pass

    @abstractmethod
    def find_active_achievements(self) -> List['Achievement']:
        """
        Find all active achievements.

        Returns:
            List[Achievement]: All active achievements
        """
        pass

    @abstractmethod
    def find_achievements_by_category(self, category: str) -> List['Achievement']:
        """
        Find achievements by category.

        Args:
            category: Achievement category to filter by

        Returns:
            List[Achievement]: Achievements in the specified category
        """
        pass

    @abstractmethod
    def create_user_achievement(self, user_achievement: 'UserAchievement') -> str:
        """
        Create a new user achievement tracking record.

        Args:
            user_achievement: UserAchievement instance to create

        Returns:
            str: Created user achievement's ID
        """
        pass

    @abstractmethod
    def find_user_achievement(
        self,
        user_id: str,
        achievement_id: str
    ) -> Optional['UserAchievement']:
        """
        Find user achievement by user and achievement IDs.

        Args:
            user_id: User's unique identifier
            achievement_id: Achievement's unique identifier

        Returns:
            Optional[UserAchievement]: User achievement if found
        """
        pass

    @abstractmethod
    def find_user_achievements(
        self,
        user_id: str,
        completed_only: bool = False
    ) -> List['UserAchievement']:
        """
        Find all user achievements.

        Args:
            user_id: User's unique identifier
            completed_only: If True, only return completed achievements

        Returns:
            List[UserAchievement]: User's achievements
        """
        pass

    @abstractmethod
    def increment_user_progress(
        self,
        user_id: str,
        achievement_id: str,
        increment: int = 1
    ) -> Optional['UserAchievement']:
        """
        Increment user achievement progress.

        Args:
            user_id: User's unique identifier
            achievement_id: Achievement's unique identifier
            increment: Amount to increment progress by

        Returns:
            Optional[UserAchievement]: Updated user achievement
        """
        pass

    @abstractmethod
    def complete_user_achievement(self, user_id: str, achievement_id: str) -> bool:
        """
        Mark user achievement as completed.

        Args:
            user_id: User's unique identifier
            achievement_id: Achievement's unique identifier

        Returns:
            bool: True if marked completed successfully
        """
        pass

    @abstractmethod
    def get_user_achievement_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Get user achievement statistics.

        Args:
            user_id: User's unique identifier

        Returns:
            Dict[str, Any]: Achievement statistics including completion rate
        """
        pass


class ISocialRepository(IBaseRepository['UserRelationship']):
    """
    Abstract interface for Social relationships repository operations.

    Manages user relationships, friendships, blocking, and social interactions.
    """

    @abstractmethod
    def create_relationship(self, relationship: 'UserRelationship') -> str:
        """
        Create a new user relationship.

        Args:
            relationship: UserRelationship instance to create

        Returns:
            str: Created relationship's ID
        """
        pass

    @abstractmethod
    def find_relationship_between_users(
        self,
        user_id: str,
        target_user_id: str,
        relationship_type: Optional[str] = None
    ) -> Optional['UserRelationship']:
        """
        Find relationship between two users.

        Args:
            user_id: First user's ID
            target_user_id: Second user's ID
            relationship_type: Type of relationship to find

        Returns:
            Optional[UserRelationship]: Relationship if found
        """
        pass

    @abstractmethod
    def get_user_relationships(
        self,
        user_id: str,
        relationship_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: Optional[int] = None,
        skip: Optional[int] = None
    ) -> List['UserRelationship']:
        """
        Get all relationships for a user.

        Args:
            user_id: User's unique identifier
            relationship_type: Filter by relationship type
            status: Filter by relationship status
            limit: Maximum number of results
            skip: Number of results to skip

        Returns:
            List[UserRelationship]: User's relationships
        """
        pass

    @abstractmethod
    def get_user_friends(
        self,
        user_id: str,
        limit: Optional[int] = None,
        skip: Optional[int] = None
    ) -> List['UserRelationship']:
        """
        Get accepted friend relationships for a user.

        Args:
            user_id: User's unique identifier
            limit: Maximum number of friends to return
            skip: Number of friends to skip

        Returns:
            List[UserRelationship]: User's friend relationships
        """
        pass

    @abstractmethod
    def get_pending_friend_requests(
        self,
        user_id: str,
        limit: Optional[int] = None,
        skip: Optional[int] = None
    ) -> List['UserRelationship']:
        """
        Get pending friend requests received by a user.

        Args:
            user_id: User's unique identifier
            limit: Maximum number of requests to return
            skip: Number of requests to skip

        Returns:
            List[UserRelationship]: Pending friend requests
        """
        pass

    @abstractmethod
    def update_relationship_status(self, relationship_id: str, new_status: str) -> bool:
        """
        Update relationship status.

        Args:
            relationship_id: Relationship's unique identifier
            new_status: New status ('pending', 'accepted', 'rejected', 'blocked')

        Returns:
            bool: True if updated successfully
        """
        pass

    @abstractmethod
    def are_friends(self, user_id: str, target_user_id: str) -> bool:
        """
        Check if two users are friends.

        Args:
            user_id: First user's ID
            target_user_id: Second user's ID

        Returns:
            bool: True if users are friends
        """
        pass

    @abstractmethod
    def is_blocked(self, user_id: str, target_user_id: str) -> bool:
        """
        Check if one user has blocked another.

        Args:
            user_id: Blocking user's ID
            target_user_id: Potentially blocked user's ID

        Returns:
            bool: True if user is blocked
        """
        pass

    @abstractmethod
    def get_friends_count(self, user_id: str) -> int:
        """
        Get count of user's friends.

        Args:
            user_id: User's unique identifier

        Returns:
            int: Number of friends
        """
        pass


# Forward declarations for type hints (will be resolved at runtime)
if False:  # TYPE_CHECKING equivalent
    from app.core.models.user import User
    from app.games.models.game import Game
    from app.games.models.game_session import GameSession
    from app.social.achievements.models.achievement import Achievement
    from app.social.achievements.models.user_achievement import UserAchievement
    from app.social.models.user_relationship import UserRelationship