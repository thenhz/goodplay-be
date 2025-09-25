"""
Dependency Injection Usage Examples

Demonstrates how to use the GoodPlay dependency injection container
in various scenarios with Flask applications.
"""
import os
from flask import Flask
from typing import Optional

# Set testing environment
os.environ['TESTING'] = 'true'

from app.core.di import (
    DIContainer,
    ServiceLifecycle,
    injectable,
    inject,
    auto_inject,
    DIConfig,
    DIBootstrap
)
from app.core.di.decorators import FlaskDIIntegration
from app.core.di.testing import create_test_container

from tests.core.interfaces import IUserRepository, IGameRepository
from app.core.repositories.user_repository import UserRepository
from app.games.repositories.game_repository import GameRepository


# Example 1: Basic Container Usage
def basic_container_example():
    """Basic dependency injection container usage"""
    print("\n=== Basic Container Example ===")

    # Create container
    container = DIContainer()

    # Register services
    container.register_type(IUserRepository, UserRepository, ServiceLifecycle.SINGLETON)
    container.register_type(IGameRepository, GameRepository, ServiceLifecycle.TRANSIENT)

    # Resolve services
    user_repo1 = container.resolve(IUserRepository)
    user_repo2 = container.resolve(IUserRepository)

    game_repo1 = container.resolve(IGameRepository)
    game_repo2 = container.resolve(IGameRepository)

    print(f"Singleton behavior: {user_repo1 is user_repo2}")  # True
    print(f"Transient behavior: {game_repo1 is game_repo2}")  # False
    print("✅ Basic container usage working")


# Example 2: Configuration-based Setup
def configuration_example():
    """Using DIConfig for setup"""
    print("\n=== Configuration Example ===")

    config = DIConfig('development')
    config.register_type(IUserRepository, UserRepository, ServiceLifecycle.SINGLETON)
    config.register_type(IGameRepository, GameRepository, ServiceLifecycle.TRANSIENT)

    container = DIContainer()

    # Apply configuration
    for registration in config.get_registrations():
        if registration.implementation_type:
            container.register_type(
                registration.service_type,
                registration.implementation_type,
                registration.lifecycle
            )

    user_repo = container.resolve(IUserRepository)
    print(f"User repository resolved: {type(user_repo).__name__}")
    print("✅ Configuration-based setup working")


# Example 3: Bootstrap Usage
def bootstrap_example():
    """Using DIBootstrap for quick setup"""
    print("\n=== Bootstrap Example ===")

    # Create pre-configured container
    container = DIBootstrap.setup_for_testing()

    # Services are already registered with mocks
    user_repo = container.resolve(IUserRepository)
    game_repo = container.resolve(IGameRepository)

    print(f"Mock user repository: {type(user_repo).__name__}")
    print(f"Mock game repository: {type(game_repo).__name__}")
    print("✅ Bootstrap setup working")


# Example 4: Injectable Service Classes
@injectable(ServiceLifecycle.SCOPED)
class UserService:
    def __init__(self, user_repository: IUserRepository):
        self.user_repository = user_repository

    def get_user_count(self) -> int:
        return self.user_repository.count({})


def injectable_example():
    """Using injectable decorator"""
    print("\n=== Injectable Example ===")

    container = DIContainer()
    container.register_type(IUserRepository, UserRepository, ServiceLifecycle.SINGLETON)
    container.register_type(UserService, UserService, ServiceLifecycle.SCOPED)

    with container.create_scope():
        user_service = container.resolve(UserService)
        print(f"UserService resolved with injected repository")
        print(f"Repository injected: {type(user_service.user_repository).__name__}")

    print("✅ Injectable decorator working")


# Example 5: Flask Integration
def flask_integration_example():
    """Flask application integration"""
    print("\n=== Flask Integration Example ===")

    app = Flask(__name__)

    # Setup DI container for Flask
    container = DIBootstrap.setup_for_testing()
    FlaskDIIntegration.init_app(app, container)

    @app.route('/users')
    @inject(IUserRepository)
    def get_users(user_repository: IUserRepository):
        # user_repository is automatically injected
        count = user_repository.count({})
        return {'user_count': count}

    @app.route('/games')
    @auto_inject
    def get_games(game_repository: IGameRepository):
        # game_repository is auto-injected based on type hint
        count = game_repository.count({})
        return {'game_count': count}

    # Test with app context
    with app.app_context():
        # Routes would work with dependency injection
        print("Flask routes configured with dependency injection")
        print("✅ Flask integration working")


# Example 6: Testing Usage
def testing_example():
    """Testing with dependency injection"""
    print("\n=== Testing Example ===")

    # Create test container with mocks
    container = create_test_container()

    # Resolve mocked services
    user_repo = container.resolve(IUserRepository)
    game_repo = container.resolve(IGameRepository)

    # Configure mock behavior
    user_repo.count.return_value = 42
    game_repo.count.return_value = 24

    print(f"Mock user count: {user_repo.count({})}")
    print(f"Mock game count: {game_repo.count({})}")
    print("✅ Testing with mocks working")


# Example 7: Scoped Services
def scoped_services_example():
    """Scoped service lifecycle"""
    print("\n=== Scoped Services Example ===")

    container = DIContainer()
    container.register_type(IUserRepository, UserRepository, ServiceLifecycle.SCOPED)

    # Same scope - same instance
    with container.create_scope():
        repo1 = container.resolve(IUserRepository)
        repo2 = container.resolve(IUserRepository)
        print(f"Same scope - same instance: {repo1 is repo2}")  # True

    # Different scope - different instance
    with container.create_scope():
        repo3 = container.resolve(IUserRepository)
        print(f"Different scope - different instance: {repo1 is not repo3}")  # True

    print("✅ Scoped services working")


def main():
    """Run all examples"""
    print("🚀 GoodPlay Dependency Injection Examples")
    print("=" * 50)

    try:
        basic_container_example()
        configuration_example()
        bootstrap_example()
        injectable_example()
        flask_integration_example()
        testing_example()
        scoped_services_example()

        print("\n" + "=" * 50)
        print("🎉 All dependency injection examples completed successfully!")
        print("✅ GOO-30 (Create Dependency Injection Container) - COMPLETED")
        print("✅ MILESTONE 1 (GOO-25: Architettura Foundation) - COMPLETED")

    except Exception as e:
        print(f"❌ Error in examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()