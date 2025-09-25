"""
Comprehensive Test Suite for Dependency Injection Container

Tests all aspects of the GoodPlay DI container system including
service registration, resolution, lifecycle management, and Flask integration.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import Optional
import threading
import time

from app.core.di import (
    DIContainer,
    ServiceRegistry,
    ServiceLifecycle,
    RepositoryFactory,
    ServiceFactory,
    injectable,
    inject,
    auto_inject,
    DIConfig,
    DIConfigBuilder,
    EnvironmentType
)
from app.core.di.testing import (
    MockDIContainer,
    DITestCase,
    create_test_container,
    mock_service
)
from app.core.di.exceptions import (
    ServiceNotFoundError,
    CircularDependencyError,
    ServiceRegistrationError,
    ServiceResolutionError
)

# Test interfaces and implementations
from tests.core.interfaces import IUserRepository, IGameRepository
from abc import ABC, abstractmethod


# Mock services for testing
class ITestService(ABC):
    @abstractmethod
    def get_data(self) -> str:
        pass


class IDependentService(ABC):
    @abstractmethod
    def process(self) -> str:
        pass


class TestService(ITestService):
    def get_data(self) -> str:
        return "test_data"


class DependentService(IDependentService):
    def __init__(self, test_service: ITestService):
        self.test_service = test_service

    def process(self) -> str:
        return f"processed_{self.test_service.get_data()}"


class CircularDependencyA:
    def __init__(self, b: 'CircularDependencyB'):
        self.b = b


class CircularDependencyB:
    def __init__(self, a: CircularDependencyA):
        self.a = a


class TestDIContainer:
    """Test cases for the core DI container functionality"""

    def setup_method(self):
        self.container = DIContainer()

    def test_register_and_resolve_type(self):
        """Test basic type registration and resolution"""
        # Register service
        self.container.register_type(ITestService, TestService)

        # Resolve service
        service = self.container.resolve(ITestService)

        assert isinstance(service, TestService)
        assert service.get_data() == "test_data"

    def test_register_and_resolve_factory(self):
        """Test factory registration and resolution"""
        # Register with factory
        self.container.register_factory(
            ITestService,
            lambda: TestService(),
            ServiceLifecycle.SINGLETON
        )

        # Resolve service
        service = self.container.resolve(ITestService)

        assert isinstance(service, TestService)
        assert service.get_data() == "test_data"

    def test_register_and_resolve_instance(self):
        """Test instance registration and resolution"""
        instance = TestService()
        self.container.register_instance(ITestService, instance)

        resolved = self.container.resolve(ITestService)

        assert resolved is instance

    def test_singleton_lifecycle(self):
        """Test singleton lifecycle management"""
        self.container.register_type(ITestService, TestService, ServiceLifecycle.SINGLETON)

        service1 = self.container.resolve(ITestService)
        service2 = self.container.resolve(ITestService)

        assert service1 is service2

    def test_transient_lifecycle(self):
        """Test transient lifecycle management"""
        self.container.register_type(ITestService, TestService, ServiceLifecycle.TRANSIENT)

        service1 = self.container.resolve(ITestService)
        service2 = self.container.resolve(ITestService)

        assert service1 is not service2
        assert isinstance(service1, TestService)
        assert isinstance(service2, TestService)

    def test_scoped_lifecycle(self):
        """Test scoped lifecycle management"""
        self.container.register_type(ITestService, TestService, ServiceLifecycle.SCOPED)

        # Same scope - same instance
        with self.container.create_scope():
            service1 = self.container.resolve(ITestService)
            service2 = self.container.resolve(ITestService)
            assert service1 is service2

        # Different scope - different instance
        with self.container.create_scope():
            service3 = self.container.resolve(ITestService)
            assert service1 is not service3

    def test_dependency_injection(self):
        """Test automatic dependency injection"""
        # Register dependencies
        self.container.register_type(ITestService, TestService, ServiceLifecycle.SINGLETON)
        self.container.register_type(IDependentService, DependentService, ServiceLifecycle.TRANSIENT)

        # Resolve dependent service
        dependent = self.container.resolve(IDependentService)

        assert isinstance(dependent, DependentService)
        assert isinstance(dependent.test_service, TestService)
        assert dependent.process() == "processed_test_data"

    def test_circular_dependency_detection(self):
        """Test circular dependency detection"""
        self.container.register_type(CircularDependencyA, CircularDependencyA)
        self.container.register_type(CircularDependencyB, CircularDependencyB)

        with pytest.raises(CircularDependencyError) as exc_info:
            self.container.resolve(CircularDependencyA)

        assert "Circular dependency detected" in str(exc_info.value)

    def test_service_not_found(self):
        """Test service not found exception"""
        with pytest.raises(ServiceNotFoundError) as exc_info:
            self.container.resolve(ITestService)

        assert "not registered" in str(exc_info.value)

    def test_is_registered(self):
        """Test service registration checking"""
        assert not self.container.is_registered(ITestService)

        self.container.register_type(ITestService, TestService)

        assert self.container.is_registered(ITestService)

    def test_try_resolve(self):
        """Test try_resolve method"""
        # Unregistered service returns None
        result = self.container.try_resolve(ITestService)
        assert result is None

        # Registered service returns instance
        self.container.register_type(ITestService, TestService)
        result = self.container.try_resolve(ITestService)
        assert isinstance(result, TestService)

    def test_thread_safety(self):
        """Test thread safety of container operations"""
        self.container.register_type(ITestService, TestService, ServiceLifecycle.SINGLETON)

        results = []
        errors = []

        def resolve_service():
            try:
                service = self.container.resolve(ITestService)
                results.append(service)
            except Exception as e:
                errors.append(e)

        # Create multiple threads
        threads = [threading.Thread(target=resolve_service) for _ in range(10)]

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # Verify results
        assert len(errors) == 0
        assert len(results) == 10
        assert all(result is results[0] for result in results)  # All should be same singleton


class TestServiceRegistry:
    """Test cases for the service registry"""

    def setup_method(self):
        self.registry = ServiceRegistry()

    def test_register_type(self):
        """Test type registration"""
        self.registry.register_type(ITestService, TestService)

        descriptor = self.registry.get_descriptor(ITestService)
        assert descriptor.service_type == ITestService
        assert descriptor.implementation_type == TestService
        assert descriptor.lifecycle == ServiceLifecycle.TRANSIENT

    def test_register_factory(self):
        """Test factory registration"""
        factory = lambda: TestService()
        self.registry.register_factory(ITestService, factory, ServiceLifecycle.SINGLETON)

        descriptor = self.registry.get_descriptor(ITestService)
        assert descriptor.service_type == ITestService
        assert descriptor.factory == factory
        assert descriptor.lifecycle == ServiceLifecycle.SINGLETON

    def test_register_instance(self):
        """Test instance registration"""
        instance = TestService()
        self.registry.register_instance(ITestService, instance)

        descriptor = self.registry.get_descriptor(ITestService)
        assert descriptor.service_type == ITestService
        assert descriptor.instance == instance
        assert descriptor.lifecycle == ServiceLifecycle.SINGLETON

    def test_duplicate_registration_error(self):
        """Test duplicate registration error"""
        self.registry.register_type(ITestService, TestService)

        with pytest.raises(ServiceRegistrationError):
            self.registry.register_type(ITestService, TestService)

    def test_unregister(self):
        """Test service unregistration"""
        self.registry.register_type(ITestService, TestService)
        assert self.registry.is_registered(ITestService)

        self.registry.unregister(ITestService)
        assert not self.registry.is_registered(ITestService)

    def test_clear(self):
        """Test registry clearing"""
        self.registry.register_type(ITestService, TestService)
        self.registry.register_type(IDependentService, DependentService)

        assert len(self.registry.get_all_descriptors()) == 2

        self.registry.clear()

        assert len(self.registry.get_all_descriptors()) == 0


class TestDIConfig:
    """Test cases for DI configuration"""

    def test_config_creation(self):
        """Test configuration creation"""
        config = DIConfig('testing')
        assert config.environment == EnvironmentType.TESTING

    def test_register_type_with_config(self):
        """Test type registration through config"""
        config = DIConfig()
        config.register_type(ITestService, TestService, ServiceLifecycle.SINGLETON)

        registrations = config.get_registrations()
        assert len(registrations) == 1
        assert registrations[0].service_type == ITestService
        assert registrations[0].implementation_type == TestService

    def test_environment_specific_registration(self):
        """Test environment-specific service registration"""
        config = DIConfig('development')

        config.register_type(
            ITestService,
            TestService,
            environments=[EnvironmentType.DEVELOPMENT]
        )

        # Should be included in development
        registrations = config.get_registrations()
        assert len(registrations) == 1

        # Should not be included in testing
        config.environment = EnvironmentType.TESTING
        registrations = config.get_registrations()
        assert len(registrations) == 0

    def test_config_builder(self):
        """Test configuration builder pattern"""
        config = (
            DIConfigBuilder('testing')
            .for_testing()
            .register_type(ITestService, TestService)
            .for_development()
            .register_type(IDependentService, DependentService)
            .build()
        )

        # Should have registrations for testing environment
        config.environment = EnvironmentType.TESTING
        testing_registrations = config.get_registrations()
        assert len(testing_registrations) == 1
        assert testing_registrations[0].service_type == ITestService


class TestDecorators:
    """Test cases for DI decorators"""

    def test_injectable_decorator(self):
        """Test injectable decorator"""
        @injectable(ServiceLifecycle.SINGLETON, ITestService)
        class DecoratedService:
            pass

        assert hasattr(DecoratedService, '_di_injectable')
        assert DecoratedService._di_injectable
        assert DecoratedService._di_lifecycle == ServiceLifecycle.SINGLETON
        assert DecoratedService._di_service_type == ITestService

    def test_inject_decorator(self):
        """Test inject decorator (mocked Flask context)"""
        container = DIContainer()
        container.register_type(ITestService, TestService)

        with patch('app.core.di.decorators.current_app') as mock_app:
            mock_app.di_container = container

            @inject(ITestService)
            def test_endpoint(test_service: ITestService):
                return test_service.get_data()

            result = test_endpoint()
            assert result == "test_data"


class TestRepositoryFactory:
    """Test cases for repository factory"""

    def test_repository_factory_creation(self):
        """Test repository factory creation"""
        factory = RepositoryFactory()

        # Should create repositories without container
        user_repo = factory.create_user_repository()
        assert user_repo is not None

    def test_repository_factory_with_container(self):
        """Test repository factory with DI container"""
        container = DIContainer()
        mock_repo = Mock(spec=IUserRepository)
        container.register_instance(IUserRepository, mock_repo)

        factory = RepositoryFactory(container)
        user_repo = factory.create_user_repository()

        assert user_repo is mock_repo


class TestMockDIContainer:
    """Test cases for mock DI container"""

    def test_mock_container_auto_mock(self):
        """Test automatic mock creation"""
        container = MockDIContainer(auto_mock=True)

        service = container.resolve(ITestService)

        assert service is not None
        assert isinstance(service, Mock)

    def test_mock_container_register_mock(self):
        """Test explicit mock registration"""
        container = MockDIContainer()
        mock_service = Mock(spec=ITestService)

        container.register_mock(ITestService, mock_service)
        resolved = container.resolve(ITestService)

        assert resolved is mock_service

    def test_repository_mock_setup(self):
        """Test repository mock setup"""
        container = MockDIContainer()
        container.setup_repository_mocks()

        user_repo = container.resolve(IUserRepository)
        game_repo = container.resolve(IGameRepository)

        assert user_repo is not None
        assert game_repo is not None

    def test_service_mock_setup(self):
        """Test service mock setup"""
        container = MockDIContainer()
        container.setup_service_mocks()

        from tests.core.interfaces import IAuthService
        auth_service = container.resolve(IAuthService)

        assert auth_service is not None
        assert isinstance(auth_service, Mock)

    def test_mock_reset(self):
        """Test mock reset functionality"""
        container = MockDIContainer()
        mock_service = Mock(spec=ITestService)
        container.register_mock(ITestService, mock_service)

        # Call method to create call history
        mock_service.get_data()
        assert mock_service.get_data.called

        # Reset mocks
        container.reset_mocks()
        assert not mock_service.get_data.called


class TestDITestCase(DITestCase):
    """Test cases using DITestCase base class"""

    def test_test_case_setup(self):
        """Test that test case is properly set up"""
        assert hasattr(self, 'container')
        assert isinstance(self.container, MockDIContainer)

    def test_mock_retrieval(self):
        """Test mock retrieval from test case"""
        from tests.core.interfaces import IAuthService

        mock = self.get_mock(IAuthService)
        assert mock is not None
        assert isinstance(mock, Mock)

    def test_call_verification(self):
        """Test mock call verification"""
        from tests.core.interfaces import IAuthService

        mock = self.get_mock(IAuthService)
        mock.login('test@example.com', 'password')

        assert self.verify_called(IAuthService, 'login', 'test@example.com', 'password')


class TestIntegration:
    """Integration tests for the complete DI system"""

    def test_full_integration(self):
        """Test complete DI system integration"""
        # Setup configuration
        config = DIConfig('testing')
        config.register_type(ITestService, TestService, ServiceLifecycle.SINGLETON)
        config.register_type(IDependentService, DependentService, ServiceLifecycle.TRANSIENT)

        # Create container
        container = DIContainer()

        # Apply configuration
        for registration in config.get_registrations():
            if registration.implementation_type:
                container.register_type(
                    registration.service_type,
                    registration.implementation_type,
                    registration.lifecycle
                )

        # Test resolution
        service = container.resolve(IDependentService)
        assert isinstance(service, DependentService)
        assert service.process() == "processed_test_data"

        # Test singleton behavior
        test_service1 = container.resolve(ITestService)
        test_service2 = container.resolve(ITestService)
        assert test_service1 is test_service2

    def test_service_mock_builder(self):
        """Test service mock builder"""
        mock = (
            mock_service(ITestService)
            .returns('get_data', 'mocked_data')
            .build()
        )

        assert mock.get_data() == 'mocked_data'

    def test_performance(self):
        """Test container performance with many services"""
        container = DIContainer()

        # Register many services
        for i in range(100):
            service_name = f"service_{i}"

            class TempService:
                def __init__(self):
                    self.name = service_name

            # Create dynamic type
            DynamicService = type(service_name, (TempService,), {})
            container.register_type(DynamicService, DynamicService)

        # Time resolution
        start_time = time.time()
        for i in range(100):
            service_name = f"service_{i}"
            service_type = next(
                reg.service_type for reg in container.get_services().values()
                if reg.service_type.__name__ == service_name
            )
            container.resolve(service_type)

        end_time = time.time()

        # Should complete within reasonable time (less than 1 second)
        assert end_time - start_time < 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])