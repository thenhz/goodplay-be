"""
Testing Infrastructure for Dependency Injection Container

Provides mock containers, utilities, and helpers for testing applications
that use dependency injection patterns.
"""
from typing import Dict, Any, Type, TypeVar, Optional, Callable, List
from unittest.mock import Mock, MagicMock
import inspect

from .container import DIContainer, DIScope
from .registry import ServiceRegistry, ServiceLifecycle, ServiceDescriptor
from .factories import MockRepositoryFactory
from .config import DIConfig, EnvironmentType
from .exceptions import ServiceNotFoundError

T = TypeVar('T')


class MockDIContainer(DIContainer):
    """
    Mock dependency injection container for testing.

    Provides the same interface as DIContainer but with additional
    testing utilities and automatic mock creation.
    """

    def __init__(self, auto_mock: bool = True):
        """
        Initialize mock DI container.

        Args:
            auto_mock: Whether to automatically create mocks for unregistered services
        """
        super().__init__()
        self._auto_mock = auto_mock
        self._mocks: Dict[str, Mock] = {}
        self._mock_factory = MockRepositoryFactory()

    def resolve(self, service_type: Type[T]) -> T:
        """
        Resolve service with automatic mock creation for testing.

        Args:
            service_type: Service type to resolve

        Returns:
            T: Service instance or mock
        """
        try:
            return super().resolve(service_type)
        except ServiceNotFoundError:
            if self._auto_mock:
                return self._create_mock(service_type)
            raise

    def register_mock(self, service_type: Type[T], mock_instance: T) -> 'MockDIContainer':
        """
        Register a specific mock for a service type.

        Args:
            service_type: Service type
            mock_instance: Mock instance

        Returns:
            MockDIContainer: Self for method chaining
        """
        self.register_instance(service_type, mock_instance)
        service_name = self._get_service_name(service_type)
        self._mocks[service_name] = mock_instance
        return self

    def get_mock(self, service_type: Type[T]) -> Optional[T]:
        """
        Get mock instance for a service type.

        Args:
            service_type: Service type

        Returns:
            Optional[T]: Mock instance if registered
        """
        service_name = self._get_service_name(service_type)
        return self._mocks.get(service_name)

    def setup_repository_mocks(self) -> None:
        """Setup standard repository mocks using MockRepositoryFactory"""
        from tests.core.interfaces import (
            IUserRepository,
            IGameRepository,
            IPreferencesRepository,
            IAchievementRepository,
            ISocialRepository
        )

        # Register repository mocks
        self.register_instance(IUserRepository, self._mock_factory.create_user_repository())
        self.register_instance(IGameRepository, self._mock_factory.create_game_repository())
        self.register_instance(IPreferencesRepository, self._mock_factory.create_preferences_repository())
        self.register_instance(IAchievementRepository, self._mock_factory.create_achievement_repository())
        self.register_instance(ISocialRepository, self._mock_factory.create_social_repository())

    def setup_service_mocks(self) -> None:
        """Setup standard service mocks"""
        from tests.core.interfaces import (
            IAuthService,
            IGameService,
            ISocialService,
            IPreferencesService
        )

        # Create and register service mocks
        auth_service = Mock(spec=IAuthService)
        game_service = Mock(spec=IGameService)
        social_service = Mock(spec=ISocialService)
        preferences_service = Mock(spec=IPreferencesService)

        self.register_mock(IAuthService, auth_service)
        self.register_mock(IGameService, game_service)
        self.register_mock(ISocialService, social_service)
        self.register_mock(IPreferencesService, preferences_service)

    def reset_mocks(self) -> None:
        """Reset all registered mocks"""
        for mock in self._mocks.values():
            if hasattr(mock, 'reset_mock'):
                mock.reset_mock()

        # Reset mock repository factory
        self._mock_factory.reset_repositories()

    def clear_all_data(self) -> None:
        """Clear all data from mock repositories"""
        self._mock_factory.clear_all_data()

    def verify_mock_calls(self, service_type: Type, method_name: str, *args, **kwargs) -> bool:
        """
        Verify that a mock method was called with specific arguments.

        Args:
            service_type: Service type
            method_name: Method name
            *args: Expected positional arguments
            **kwargs: Expected keyword arguments

        Returns:
            bool: True if call was made with specified arguments
        """
        mock = self.get_mock(service_type)
        if not mock:
            return False

        if not hasattr(mock, method_name):
            return False

        method_mock = getattr(mock, method_name)
        return method_mock.called and (args, kwargs) in method_mock.call_args_list

    def _create_mock(self, service_type: Type[T]) -> T:
        """Create automatic mock for service type"""
        service_name = self._get_service_name(service_type)

        if service_name in self._mocks:
            return self._mocks[service_name]

        # Create mock with spec from service type
        mock = Mock(spec=service_type)
        self._mocks[service_name] = mock

        # Register as singleton so it's reused
        self.register_instance(service_type, mock)

        return mock


class DITestCase:
    """
    Base test case class for dependency injection testing.

    Provides common utilities and setup for testing with DI containers.
    """

    def setup_method(self, method):
        """Setup method called before each test"""
        self.container = MockDIContainer()
        self.container.setup_repository_mocks()
        self.container.setup_service_mocks()

    def teardown_method(self, method):
        """Teardown method called after each test"""
        if hasattr(self, 'container'):
            self.container.clear()
            self.container.clear_all_data()

    def get_mock(self, service_type: Type[T]) -> T:
        """Get mock for service type"""
        return self.container.get_mock(service_type)

    def verify_called(self, service_type: Type, method_name: str, *args, **kwargs) -> bool:
        """Verify mock method was called"""
        return self.container.verify_mock_calls(service_type, method_name, *args, **kwargs)

    def reset_mocks(self) -> None:
        """Reset all mocks"""
        self.container.reset_mocks()


class DITestBuilder:
    """
    Builder for creating test configurations with dependency injection.

    Provides a fluent interface for setting up test scenarios with
    specific service configurations and mock behaviors.
    """

    def __init__(self):
        self._container = MockDIContainer()
        self._config = DIConfig('testing')

    def with_repository_mocks(self) -> 'DITestBuilder':
        """Add standard repository mocks"""
        self._container.setup_repository_mocks()
        return self

    def with_service_mocks(self) -> 'DITestBuilder':
        """Add standard service mocks"""
        self._container.setup_service_mocks()
        return self

    def with_mock(self, service_type: Type[T], mock_instance: T) -> 'DITestBuilder':
        """Add specific mock"""
        self._container.register_mock(service_type, mock_instance)
        return self

    def with_real_service(
        self,
        service_type: Type[T],
        implementation_type: Type[T],
        lifecycle: ServiceLifecycle = ServiceLifecycle.SINGLETON
    ) -> 'DITestBuilder':
        """Add real service implementation"""
        self._container.register_type(service_type, implementation_type, lifecycle)
        return self

    def with_factory(
        self,
        service_type: Type[T],
        factory: Callable[..., T]
    ) -> 'DITestBuilder':
        """Add service factory"""
        self._container.register_factory(service_type, factory)
        return self

    def build(self) -> MockDIContainer:
        """Build configured test container"""
        return self._container


def create_test_container() -> MockDIContainer:
    """
    Create a standard test container with common mocks.

    Returns:
        MockDIContainer: Configured test container
    """
    return (
        DITestBuilder()
        .with_repository_mocks()
        .with_service_mocks()
        .build()
    )


def create_minimal_test_container() -> MockDIContainer:
    """
    Create minimal test container without automatic mocks.

    Returns:
        MockDIContainer: Minimal test container
    """
    return MockDIContainer(auto_mock=False)


class ServiceMockBuilder:
    """
    Builder for creating configured service mocks.

    Provides utilities for setting up service mocks with specific
    behaviors and return values for testing scenarios.
    """

    def __init__(self, service_type: Type[T]):
        self.service_type = service_type
        self._mock = Mock(spec=service_type)
        self._method_configs: Dict[str, Any] = {}

    def returns(self, method_name: str, return_value: Any) -> 'ServiceMockBuilder':
        """Configure method to return specific value"""
        getattr(self._mock, method_name).return_value = return_value
        return self

    def raises(self, method_name: str, exception: Exception) -> 'ServiceMockBuilder':
        """Configure method to raise exception"""
        getattr(self._mock, method_name).side_effect = exception
        return self

    def calls_real(self, method_name: str, real_method: Callable) -> 'ServiceMockBuilder':
        """Configure method to call real implementation"""
        getattr(self._mock, method_name).side_effect = real_method
        return self

    def with_side_effect(self, method_name: str, side_effect: Callable) -> 'ServiceMockBuilder':
        """Configure method with custom side effect"""
        getattr(self._mock, method_name).side_effect = side_effect
        return self

    def build(self) -> T:
        """Build configured mock"""
        return self._mock


def mock_service(service_type: Type[T]) -> ServiceMockBuilder:
    """
    Create service mock builder.

    Args:
        service_type: Service type to mock

    Returns:
        ServiceMockBuilder: Mock builder for service type
    """
    return ServiceMockBuilder(service_type)


# Integration with existing test utilities
def patch_di_container(test_func: Callable) -> Callable:
    """
    Decorator to patch DI container in Flask tests.

    Args:
        test_func: Test function to patch

    Returns:
        Decorated test function
    """
    def wrapper(*args, **kwargs):
        container = create_test_container()

        # Mock Flask current_app.di_container
        import unittest.mock
        with unittest.mock.patch('flask.current_app') as mock_app:
            mock_app.di_container = container
            return test_func(*args, container=container, **kwargs)

    return wrapper