"""
Bootstrap Configuration for GoodPlay Dependency Injection

Provides the standard DI container configuration for the GoodPlay application
with all repository and service registrations properly configured.
"""
from typing import Optional

from .container import DIContainer
from .registry import ServiceLifecycle
from .config import DIConfig, DIConfigBuilder, EnvironmentType
from .decorators import FlaskDIIntegration
from .factories import RepositoryFactory, ServiceFactory

# Import interfaces
from tests.core.interfaces import (
    # Base interfaces
    IRepositoryFactory,

    # Repository interfaces
    IUserRepository,
    IGameRepository,
    IPreferencesRepository,
    IAchievementRepository,
    ISocialRepository,

    # Service interfaces
    IAuthService,
    IGameService,
    ISocialService,
    IPreferencesService
)

# Import concrete implementations
from app.core.repositories.user_repository import UserRepository
from app.games.repositories.game_repository import GameRepository
from app.preferences.repositories.preferences_repository import PreferencesRepository
from app.social.achievements.repositories.achievement_repository import AchievementRepository
from app.social.repositories.relationship_repository import RelationshipRepository

# Import service implementations (when available)
from app.core.services.auth_service import AuthService
from app.core.services.user_service import UserService


def create_default_config(environment: Optional[str] = None) -> DIConfig:
    """
    Create the default DI configuration for GoodPlay application.

    Args:
        environment: Environment name (development, testing, production)

    Returns:
        DIConfig: Configured DI configuration
    """
    config = DIConfig(environment)

    # Core repository registrations (singleton for performance)
    config.register_type(
        IUserRepository,
        UserRepository,
        ServiceLifecycle.SINGLETON
    )

    config.register_type(
        IGameRepository,
        GameRepository,
        ServiceLifecycle.SINGLETON
    )

    config.register_type(
        IPreferencesRepository,
        PreferencesRepository,
        ServiceLifecycle.SINGLETON
    )

    config.register_type(
        IAchievementRepository,
        AchievementRepository,
        ServiceLifecycle.SINGLETON
    )

    config.register_type(
        ISocialRepository,
        RelationshipRepository,
        ServiceLifecycle.SINGLETON
    )

    # Repository factory (singleton)
    config.register_factory(
        IRepositoryFactory,
        lambda container=None: RepositoryFactory(container),
        ServiceLifecycle.SINGLETON
    )

    # Core service registrations (scoped for request isolation)
    config.register_type(
        IAuthService,
        AuthService,
        ServiceLifecycle.SCOPED
    )

    config.register_type(
        'IUserService',  # Use string for forward reference
        UserService,
        ServiceLifecycle.SCOPED
    )

    # Environment-specific configurations
    return config


def create_production_config() -> DIConfig:
    """Create production-specific DI configuration"""
    return (
        DIConfigBuilder('production')
        .for_production()
        .register_type(IUserRepository, UserRepository, ServiceLifecycle.SINGLETON)
        .register_type(IGameRepository, GameRepository, ServiceLifecycle.SINGLETON)
        .register_type(IPreferencesRepository, PreferencesRepository, ServiceLifecycle.SINGLETON)
        .register_type(IAchievementRepository, AchievementRepository, ServiceLifecycle.SINGLETON)
        .register_type(ISocialRepository, RelationshipRepository, ServiceLifecycle.SINGLETON)
        .register_type(IAuthService, AuthService, ServiceLifecycle.SCOPED)
        .build()
        .enable_performance_monitoring(False)
        .enable_circular_dependency_detection(True)
    )


def create_development_config() -> DIConfig:
    """Create development-specific DI configuration"""
    return (
        DIConfigBuilder('development')
        .for_development()
        .register_type(IUserRepository, UserRepository, ServiceLifecycle.SINGLETON)
        .register_type(IGameRepository, GameRepository, ServiceLifecycle.SINGLETON)
        .register_type(IPreferencesRepository, PreferencesRepository, ServiceLifecycle.SINGLETON)
        .register_type(IAchievementRepository, AchievementRepository, ServiceLifecycle.SINGLETON)
        .register_type(ISocialRepository, RelationshipRepository, ServiceLifecycle.SINGLETON)
        .register_type(IAuthService, AuthService, ServiceLifecycle.SCOPED)
        .build()
        .enable_performance_monitoring(True)
        .enable_circular_dependency_detection(True)
    )


def create_testing_config() -> DIConfig:
    """Create testing-specific DI configuration (uses mocks by default)"""
    from .testing import MockRepositoryFactory

    config = DIConfig('testing')

    # Use mock repository factory for testing
    mock_factory = MockRepositoryFactory()

    config.register_instance(IUserRepository, mock_factory.create_user_repository())
    config.register_instance(IGameRepository, mock_factory.create_game_repository())
    config.register_instance(IPreferencesRepository, mock_factory.create_preferences_repository())
    config.register_instance(IAchievementRepository, mock_factory.create_achievement_repository())
    config.register_instance(ISocialRepository, mock_factory.create_social_repository())

    # Register factory instance
    config.register_instance(IRepositoryFactory, mock_factory)

    return config


def bootstrap_container(environment: Optional[str] = None) -> DIContainer:
    """
    Bootstrap a fully configured DI container for the GoodPlay application.

    Args:
        environment: Environment name (development, testing, production)

    Returns:
        DIContainer: Configured DI container
    """
    # Create appropriate configuration
    if environment == 'testing':
        config = create_testing_config()
    elif environment == 'production':
        config = create_production_config()
    elif environment == 'development':
        config = create_development_config()
    else:
        config = create_default_config(environment)

    # Create and configure container
    container = DIContainer()

    # Apply configuration
    for registration in config.get_registrations():
        if registration.instance is not None:
            container.register_instance(
                registration.service_type,
                registration.instance
            )
        elif registration.factory is not None:
            container.register_factory(
                registration.service_type,
                registration.factory,
                registration.lifecycle
            )
        elif registration.implementation_type is not None:
            container.register_type(
                registration.service_type,
                registration.implementation_type,
                registration.lifecycle
            )

    return container


def integrate_with_flask(app, environment: Optional[str] = None):
    """
    Integrate DI container with Flask application.

    Args:
        app: Flask application instance
        environment: Environment name
    """
    # Bootstrap container
    container = bootstrap_container(environment)

    # Integrate with Flask
    FlaskDIIntegration.init_app(app, container)

    return container


class DIBootstrap:
    """
    Bootstrap utility class for setting up dependency injection.

    Provides a convenient way to set up DI container with different
    configurations and integrate with Flask applications.
    """

    @staticmethod
    def setup_for_app(app, environment: Optional[str] = None) -> DIContainer:
        """
        Setup DI container for Flask application.

        Args:
            app: Flask application
            environment: Environment name

        Returns:
            DIContainer: Configured container
        """
        return integrate_with_flask(app, environment)

    @staticmethod
    def setup_for_testing() -> DIContainer:
        """
        Setup DI container for testing.

        Returns:
            DIContainer: Testing container with mocks
        """
        return bootstrap_container('testing')

    @staticmethod
    def setup_for_production() -> DIContainer:
        """
        Setup DI container for production.

        Returns:
            DIContainer: Production container
        """
        return bootstrap_container('production')

    @staticmethod
    def create_service_factory(container: DIContainer) -> ServiceFactory:
        """
        Create service factory with the container.

        Args:
            container: DI container

        Returns:
            ServiceFactory: Configured service factory
        """
        return ServiceFactory(container)

    @staticmethod
    def create_repository_factory(container: DIContainer) -> RepositoryFactory:
        """
        Create repository factory with the container.

        Args:
            container: DI container

        Returns:
            RepositoryFactory: Configured repository factory
        """
        return RepositoryFactory(container)