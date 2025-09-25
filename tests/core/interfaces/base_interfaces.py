"""
Base Abstract Interfaces for GoodPlay Repository Pattern

Provides the foundational abstract interfaces that all repository interfaces
must extend, ensuring consistent patterns and type safety across the application.
"""
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, Generic, TypeVar, Union
from datetime import datetime

# Generic type variable for domain entities
T = TypeVar('T')


class IBaseRepository(ABC, Generic[T]):
    """
    Abstract base repository interface defining common CRUD operations.

    All concrete repository interfaces should extend this interface to ensure
    consistent behavior and enable proper dependency injection.

    Generic Type:
        T: The domain entity type (e.g., User, Game, Achievement)
    """

    @abstractmethod
    def find_by_id(self, id: str) -> Optional[T]:
        """
        Find an entity by its unique identifier.

        Args:
            id: The entity's unique identifier (ObjectId string)

        Returns:
            Optional[T]: The entity if found, None otherwise

        Raises:
            ValueError: If the ID format is invalid

        Example:
            user = repository.find_by_id("507f1f77bcf86cd799439011")
            if user:
                print(f"Found user: {user.email}")
        """
        pass

    @abstractmethod
    def find_one(self, filter_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Find a single entity matching the filter criteria.

        Args:
            filter_dict: MongoDB-style filter dictionary

        Returns:
            Optional[Dict[str, Any]]: Raw entity data if found, None otherwise

        Example:
            user_data = repository.find_one({"email": "user@example.com"})
        """
        pass

    @abstractmethod
    def find_many(
        self,
        filter_dict: Dict[str, Any] = None,
        limit: Optional[int] = None,
        skip: Optional[int] = None,
        sort: Optional[List[tuple]] = None
    ) -> List[Dict[str, Any]]:
        """
        Find multiple entities matching the filter criteria.

        Args:
            filter_dict: MongoDB-style filter dictionary (defaults to empty)
            limit: Maximum number of results to return
            skip: Number of results to skip (for pagination)
            sort: List of (field, direction) tuples for sorting

        Returns:
            List[Dict[str, Any]]: List of raw entity data

        Example:
            users = repository.find_many(
                {"is_active": True},
                limit=10,
                sort=[("created_at", -1)]
            )
        """
        pass

    @abstractmethod
    def create(self, data: Dict[str, Any]) -> str:
        """
        Create a new entity in the repository.

        Args:
            data: Entity data dictionary

        Returns:
            str: The created entity's ID

        Raises:
            ValueError: If required fields are missing
            DuplicateError: If unique constraints are violated

        Example:
            user_id = repository.create({
                "email": "new@example.com",
                "name": "New User"
            })
        """
        pass

    @abstractmethod
    def update_by_id(self, id: str, data: Dict[str, Any]) -> bool:
        """
        Update an entity by its ID.

        Args:
            id: The entity's unique identifier
            data: Dictionary of fields to update

        Returns:
            bool: True if the entity was updated, False otherwise

        Example:
            success = repository.update_by_id(user_id, {
                "last_login": datetime.now(),
                "login_count": 5
            })
        """
        pass

    @abstractmethod
    def update_one(self, filter_dict: Dict[str, Any], data: Dict[str, Any]) -> bool:
        """
        Update the first entity matching the filter.

        Args:
            filter_dict: MongoDB-style filter dictionary
            data: Dictionary of fields to update

        Returns:
            bool: True if an entity was updated, False otherwise
        """
        pass

    @abstractmethod
    def delete_by_id(self, id: str) -> bool:
        """
        Delete an entity by its ID.

        Args:
            id: The entity's unique identifier

        Returns:
            bool: True if the entity was deleted, False otherwise

        Example:
            deleted = repository.delete_by_id("507f1f77bcf86cd799439011")
        """
        pass

    @abstractmethod
    def delete_one(self, filter_dict: Dict[str, Any]) -> bool:
        """
        Delete the first entity matching the filter.

        Args:
            filter_dict: MongoDB-style filter dictionary

        Returns:
            bool: True if an entity was deleted, False otherwise
        """
        pass

    @abstractmethod
    def count(self, filter_dict: Dict[str, Any] = None) -> int:
        """
        Count entities matching the filter criteria.

        Args:
            filter_dict: MongoDB-style filter dictionary (defaults to empty)

        Returns:
            int: Number of matching entities

        Example:
            active_users = repository.count({"is_active": True})
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

        This method should be implemented to create all necessary indexes
        for the specific repository. It should handle the testing environment
        gracefully by checking for TESTING=true.

        Example:
            def create_indexes(self):
                if os.getenv('TESTING') == 'true':
                    return
                self.collection.create_index("email", unique=True)
        """
        pass


class IRepositoryFactory(ABC):
    """
    Abstract factory interface for creating repository instances.

    This interface enables dependency injection by providing a consistent
    way to create repository instances without tight coupling.
    """

    @abstractmethod
    def create_user_repository(self) -> 'IUserRepository':
        """Create a user repository instance."""
        pass

    @abstractmethod
    def create_game_repository(self) -> 'IGameRepository':
        """Create a game repository instance."""
        pass

    @abstractmethod
    def create_preferences_repository(self) -> 'IPreferencesRepository':
        """Create a preferences repository instance."""
        pass

    @abstractmethod
    def create_achievement_repository(self) -> 'IAchievementRepository':
        """Create an achievement repository instance."""
        pass

    @abstractmethod
    def create_social_repository(self) -> 'ISocialRepository':
        """Create a social repository instance."""
        pass


class IMockRepository(IBaseRepository[T]):
    """
    Interface for mock repositories used in testing.

    Extends IBaseRepository with additional methods useful for testing,
    such as data seeding and state management.
    """

    @abstractmethod
    def seed_data(self, data: List[Dict[str, Any]]) -> None:
        """
        Seed the repository with test data.

        Args:
            data: List of entity data dictionaries to seed
        """
        pass

    @abstractmethod
    def clear_all_data(self) -> None:
        """Clear all data from the repository (test use only)."""
        pass

    @abstractmethod
    def get_all_data(self) -> List[Dict[str, Any]]:
        """Get all data from the repository (test use only)."""
        pass


# Forward declarations for type hints (will be imported in __init__.py)
if False:  # TYPE_CHECKING equivalent
    from .repository_interfaces import (
        IUserRepository,
        IGameRepository,
        IPreferencesRepository,
        IAchievementRepository,
        ISocialRepository
    )