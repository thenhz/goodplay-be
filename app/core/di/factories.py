"""
Factory Classes for Dependency Injection Container

Provides concrete factory implementations for creating repository and
service instances with proper dependency injection support.
"""
from typing import TYPE_CHECKING

# Import interfaces
from tests.core.interfaces import (
    IRepositoryFactory,
    IUserRepository,
    IGameRepository,
    IPreferencesRepository,
    IAchievementRepository,
    ISocialRepository
)

# Import concrete implementations
from app.core.repositories.user_repository import UserRepository
from app.games.repositories.game_repository import GameRepository
from app.preferences.repositories.preferences_repository import PreferencesRepository
from app.social.achievements.repositories.achievement_repository import AchievementRepository
from app.social.repositories.relationship_repository import RelationshipRepository

if TYPE_CHECKING:
    from .container import DIContainer


class RepositoryFactory(IRepositoryFactory):
    """
    Concrete repository factory implementation.

    Creates repository instances with proper dependency injection support.
    Can be used standalone or within the DI container system.
    """

    def __init__(self, container: 'DIContainer' = None):
        """
        Initialize repository factory.

        Args:
            container: Optional DI container for resolving dependencies
        """
        self._container = container

    def create_user_repository(self) -> IUserRepository:
        """
        Create a user repository instance.

        Returns:
            IUserRepository: User repository instance
        """
        if self._container and self._container.is_registered(IUserRepository):
            return self._container.resolve(IUserRepository)
        return UserRepository()

    def create_game_repository(self) -> IGameRepository:
        """
        Create a game repository instance.

        Returns:
            IGameRepository: Game repository instance
        """
        if self._container and self._container.is_registered(IGameRepository):
            return self._container.resolve(IGameRepository)
        return GameRepository()

    def create_preferences_repository(self) -> IPreferencesRepository:
        """
        Create a preferences repository instance.

        Returns:
            IPreferencesRepository: Preferences repository instance
        """
        if self._container and self._container.is_registered(IPreferencesRepository):
            return self._container.resolve(IPreferencesRepository)
        return PreferencesRepository()

    def create_achievement_repository(self) -> IAchievementRepository:
        """
        Create an achievement repository instance.

        Returns:
            IAchievementRepository: Achievement repository instance
        """
        if self._container and self._container.is_registered(IAchievementRepository):
            return self._container.resolve(IAchievementRepository)
        return AchievementRepository()

    def create_social_repository(self) -> ISocialRepository:
        """
        Create a social repository instance.

        Returns:
            ISocialRepository: Social repository instance
        """
        if self._container and self._container.is_registered(ISocialRepository):
            return self._container.resolve(ISocialRepository)
        return RelationshipRepository()


class ServiceFactory:
    """
    Factory for creating service instances with dependency injection.

    Provides a centralized way to create service instances with their
    dependencies properly resolved through the DI container.
    """

    def __init__(self, container: 'DIContainer'):
        """
        Initialize service factory.

        Args:
            container: DI container for resolving dependencies
        """
        self._container = container

    def create_auth_service(self):
        """Create authentication service with dependencies"""
        from tests.core.interfaces import IAuthService
        return self._container.resolve(IAuthService)

    def create_user_service(self):
        """Create user service with dependencies"""
        from tests.core.interfaces import IUserService
        return self._container.resolve(IUserService)

    def create_game_service(self):
        """Create game service with dependencies"""
        from tests.core.interfaces import IGameService
        return self._container.resolve(IGameService)

    def create_preferences_service(self):
        """Create preferences service with dependencies"""
        from tests.core.interfaces import IPreferencesService
        return self._container.resolve(IPreferencesService)

    def create_social_service(self):
        """Create social service with dependencies"""
        from tests.core.interfaces import ISocialService
        return self._container.resolve(ISocialService)

    def create_achievement_service(self):
        """Create achievement service with dependencies"""
        # Achievement service is part of social services for now
        return self.create_social_service()

    def create_challenge_service(self):
        """Create challenge service with dependencies"""
        from tests.core.interfaces import IChallengeService
        return self._container.resolve(IChallengeService)

    def create_team_service(self):
        """Create team service with dependencies"""
        from tests.core.interfaces import ITeamService
        return self._container.resolve(ITeamService)

    def create_notification_service(self):
        """Create notification service with dependencies"""
        from tests.core.interfaces import INotificationService
        return self._container.resolve(INotificationService)


class MockRepositoryFactory(IRepositoryFactory):
    """
    Mock repository factory for testing.

    Creates mock repository instances that implement the repository
    interfaces but store data in memory for fast testing.
    """

    def __init__(self):
        """Initialize mock repository factory"""
        self._repositories = {}

    def create_user_repository(self) -> IUserRepository:
        """Create a mock user repository instance"""
        if 'user' not in self._repositories:
            from unittest.mock import Mock
            self._repositories['user'] = Mock(spec=IUserRepository)
        return self._repositories['user']

    def create_game_repository(self) -> IGameRepository:
        """Create a mock game repository instance"""
        if 'game' not in self._repositories:
            from unittest.mock import Mock
            self._repositories['game'] = Mock(spec=IGameRepository)
        return self._repositories['game']

    def create_preferences_repository(self) -> IPreferencesRepository:
        """Create a mock preferences repository instance"""
        if 'preferences' not in self._repositories:
            from unittest.mock import Mock
            self._repositories['preferences'] = Mock(spec=IPreferencesRepository)
        return self._repositories['preferences']

    def create_achievement_repository(self) -> IAchievementRepository:
        """Create a mock achievement repository instance"""
        if 'achievement' not in self._repositories:
            from unittest.mock import Mock
            self._repositories['achievement'] = Mock(spec=IAchievementRepository)
        return self._repositories['achievement']

    def create_social_repository(self) -> ISocialRepository:
        """Create a mock social repository instance"""
        if 'social' not in self._repositories:
            from unittest.mock import Mock
            self._repositories['social'] = Mock(spec=ISocialRepository)
        return self._repositories['social']

    def clear_all_data(self) -> None:
        """Clear all data from mock repositories"""
        for repo in self._repositories.values():
            if hasattr(repo, 'clear_all_data'):
                repo.clear_all_data()

    def reset_repositories(self) -> None:
        """Reset all repositories to fresh state"""
        self._repositories.clear()