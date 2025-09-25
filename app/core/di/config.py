"""
Configuration Management for Dependency Injection Container

Provides centralized configuration for the DI container system with
environment-specific settings and service registration management.
"""
import os
from typing import Dict, Any, List, Callable, Type, Optional
from dataclasses import dataclass, field
from enum import Enum

from .registry import ServiceLifecycle


class EnvironmentType(Enum):
    """Supported environment types"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


@dataclass
class ServiceRegistration:
    """Configuration for a single service registration"""
    service_type: Type
    implementation_type: Optional[Type] = None
    factory: Optional[Callable] = None
    lifecycle: ServiceLifecycle = ServiceLifecycle.TRANSIENT
    instance: Optional[Any] = None
    enabled: bool = True
    environment_specific: bool = False
    environments: List[EnvironmentType] = field(default_factory=list)

    def is_enabled_for_environment(self, environment: EnvironmentType) -> bool:
        """Check if service is enabled for specific environment"""
        if not self.enabled:
            return False

        if not self.environment_specific:
            return True

        return environment in self.environments


class DIConfig:
    """
    Configuration manager for the dependency injection container.

    Provides environment-specific service registration and container
    configuration with support for conditional registrations.
    """

    def __init__(self, environment: Optional[str] = None):
        """
        Initialize DI configuration.

        Args:
            environment: Environment name (development, testing, production)
        """
        self.environment = self._determine_environment(environment)
        self._registrations: List[ServiceRegistration] = []
        self._container_settings: Dict[str, Any] = {}
        self._init_default_settings()

    def register_type(
        self,
        service_type: Type,
        implementation_type: Type,
        lifecycle: ServiceLifecycle = ServiceLifecycle.TRANSIENT,
        environments: Optional[List[EnvironmentType]] = None
    ) -> 'DIConfig':
        """
        Register a service type with implementation.

        Args:
            service_type: The abstract type or interface
            implementation_type: The concrete implementation
            lifecycle: Service lifecycle
            environments: Specific environments where this registration applies

        Returns:
            DIConfig: Self for method chaining
        """
        registration = ServiceRegistration(
            service_type=service_type,
            implementation_type=implementation_type,
            lifecycle=lifecycle,
            environment_specific=environments is not None,
            environments=environments or []
        )

        self._registrations.append(registration)
        return self

    def register_factory(
        self,
        service_type: Type,
        factory: Callable,
        lifecycle: ServiceLifecycle = ServiceLifecycle.TRANSIENT,
        environments: Optional[List[EnvironmentType]] = None
    ) -> 'DIConfig':
        """
        Register a service with factory function.

        Args:
            service_type: The service type
            factory: Factory function
            lifecycle: Service lifecycle
            environments: Specific environments where this registration applies

        Returns:
            DIConfig: Self for method chaining
        """
        registration = ServiceRegistration(
            service_type=service_type,
            factory=factory,
            lifecycle=lifecycle,
            environment_specific=environments is not None,
            environments=environments or []
        )

        self._registrations.append(registration)
        return self

    def register_instance(
        self,
        service_type: Type,
        instance: Any,
        environments: Optional[List[EnvironmentType]] = None
    ) -> 'DIConfig':
        """
        Register a service instance.

        Args:
            service_type: The service type
            instance: Pre-created instance
            environments: Specific environments where this registration applies

        Returns:
            DIConfig: Self for method chaining
        """
        registration = ServiceRegistration(
            service_type=service_type,
            instance=instance,
            lifecycle=ServiceLifecycle.SINGLETON,
            environment_specific=environments is not None,
            environments=environments or []
        )

        self._registrations.append(registration)
        return self

    def register_conditional(
        self,
        service_type: Type,
        condition: Callable[[], bool],
        implementation_type: Optional[Type] = None,
        factory: Optional[Callable] = None,
        lifecycle: ServiceLifecycle = ServiceLifecycle.TRANSIENT
    ) -> 'DIConfig':
        """
        Register a service conditionally.

        Args:
            service_type: The service type
            condition: Function that returns True if service should be registered
            implementation_type: Optional implementation type
            factory: Optional factory function
            lifecycle: Service lifecycle

        Returns:
            DIConfig: Self for method chaining
        """
        if condition():
            if implementation_type:
                self.register_type(service_type, implementation_type, lifecycle)
            elif factory:
                self.register_factory(service_type, factory, lifecycle)

        return self

    def get_registrations(self) -> List[ServiceRegistration]:
        """
        Get all service registrations for current environment.

        Returns:
            List[ServiceRegistration]: Enabled registrations for current environment
        """
        return [
            reg for reg in self._registrations
            if reg.is_enabled_for_environment(self.environment)
        ]

    def set_setting(self, key: str, value: Any) -> 'DIConfig':
        """
        Set container setting.

        Args:
            key: Setting key
            value: Setting value

        Returns:
            DIConfig: Self for method chaining
        """
        self._container_settings[key] = value
        return self

    def get_setting(self, key: str, default: Any = None) -> Any:
        """
        Get container setting.

        Args:
            key: Setting key
            default: Default value if key not found

        Returns:
            Any: Setting value
        """
        return self._container_settings.get(key, default)

    def enable_auto_registration(self, enabled: bool = True) -> 'DIConfig':
        """
        Enable/disable automatic service registration via decorators.

        Args:
            enabled: Whether to enable auto registration

        Returns:
            DIConfig: Self for method chaining
        """
        return self.set_setting('auto_registration', enabled)

    def enable_circular_dependency_detection(self, enabled: bool = True) -> 'DIConfig':
        """
        Enable/disable circular dependency detection.

        Args:
            enabled: Whether to enable detection

        Returns:
            DIConfig: Self for method chaining
        """
        return self.set_setting('circular_dependency_detection', enabled)

    def set_default_lifecycle(self, lifecycle: ServiceLifecycle) -> 'DIConfig':
        """
        Set default lifecycle for services without explicit lifecycle.

        Args:
            lifecycle: Default lifecycle

        Returns:
            DIConfig: Self for method chaining
        """
        return self.set_setting('default_lifecycle', lifecycle)

    def enable_performance_monitoring(self, enabled: bool = True) -> 'DIConfig':
        """
        Enable/disable performance monitoring for service resolution.

        Args:
            enabled: Whether to enable monitoring

        Returns:
            DIConfig: Self for method chaining
        """
        return self.set_setting('performance_monitoring', enabled)

    def _determine_environment(self, environment: Optional[str]) -> EnvironmentType:
        """Determine current environment from parameter or environment variables"""
        if environment:
            try:
                return EnvironmentType(environment.lower())
            except ValueError:
                pass

        # Check environment variables
        flask_env = os.getenv('FLASK_ENV', '').lower()
        if flask_env:
            try:
                return EnvironmentType(flask_env)
            except ValueError:
                pass

        testing = os.getenv('TESTING', '').lower()
        if testing in ('true', '1', 'yes'):
            return EnvironmentType.TESTING

        # Default to development
        return EnvironmentType.DEVELOPMENT

    def _init_default_settings(self) -> None:
        """Initialize default container settings"""
        self._container_settings.update({
            'auto_registration': True,
            'circular_dependency_detection': True,
            'default_lifecycle': ServiceLifecycle.TRANSIENT,
            'performance_monitoring': self.environment == EnvironmentType.DEVELOPMENT
        })


class DIConfigBuilder:
    """
    Builder pattern for creating DI configuration.

    Provides a fluent interface for building complex DI container
    configurations with conditional registrations.
    """

    def __init__(self, environment: Optional[str] = None):
        """Initialize configuration builder"""
        self._config = DIConfig(environment)

    def for_development(self) -> 'EnvironmentBuilder':
        """Configure services for development environment"""
        return EnvironmentBuilder(self._config, EnvironmentType.DEVELOPMENT)

    def for_testing(self) -> 'EnvironmentBuilder':
        """Configure services for testing environment"""
        return EnvironmentBuilder(self._config, EnvironmentType.TESTING)

    def for_production(self) -> 'EnvironmentBuilder':
        """Configure services for production environment"""
        return EnvironmentBuilder(self._config, EnvironmentType.PRODUCTION)

    def build(self) -> DIConfig:
        """Build the final configuration"""
        return self._config


class EnvironmentBuilder:
    """Builder for environment-specific service registrations"""

    def __init__(self, config: DIConfig, environment: EnvironmentType):
        self._config = config
        self._environment = environment

    def register_type(
        self,
        service_type: Type,
        implementation_type: Type,
        lifecycle: ServiceLifecycle = ServiceLifecycle.TRANSIENT
    ) -> 'EnvironmentBuilder':
        """Register type for this environment"""
        self._config.register_type(
            service_type,
            implementation_type,
            lifecycle,
            [self._environment]
        )
        return self

    def register_factory(
        self,
        service_type: Type,
        factory: Callable,
        lifecycle: ServiceLifecycle = ServiceLifecycle.TRANSIENT
    ) -> 'EnvironmentBuilder':
        """Register factory for this environment"""
        self._config.register_factory(
            service_type,
            factory,
            lifecycle,
            [self._environment]
        )
        return self

    def register_instance(self, service_type: Type, instance: Any) -> 'EnvironmentBuilder':
        """Register instance for this environment"""
        self._config.register_instance(service_type, instance, [self._environment])
        return self

    def and_for_environment(self, environment: EnvironmentType) -> 'EnvironmentBuilder':
        """Chain to another environment configuration"""
        return EnvironmentBuilder(self._config, environment)

    def build(self) -> DIConfig:
        """Build the final configuration"""
        return self._config