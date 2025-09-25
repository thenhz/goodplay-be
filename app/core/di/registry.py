"""
Service Registry for Dependency Injection Container

Manages service registration, lifecycle, and resolution within the
GoodPlay dependency injection system.
"""
import inspect
from enum import Enum
from typing import Dict, Any, Callable, Optional, Type, TypeVar, Generic, List
from dataclasses import dataclass, field
from threading import RLock
from datetime import datetime

from .exceptions import (
    ServiceNotFoundError,
    ServiceRegistrationError,
    CircularDependencyError,
    InvalidServiceLifecycleError
)

T = TypeVar('T')


class ServiceLifecycle(Enum):
    """
    Defines the lifecycle of services in the DI container.

    - SINGLETON: One instance per container (shared across all requests)
    - TRANSIENT: New instance every time service is requested
    - SCOPED: One instance per request/scope (Flask request context)
    """
    SINGLETON = "singleton"
    TRANSIENT = "transient"
    SCOPED = "scoped"


@dataclass
class ServiceDescriptor:
    """
    Describes a service registered in the DI container.

    Contains all metadata needed to create and manage service instances.
    """
    service_type: Type[T]
    implementation_type: Optional[Type[T]] = None
    factory: Optional[Callable[..., T]] = None
    lifecycle: ServiceLifecycle = ServiceLifecycle.TRANSIENT
    instance: Optional[T] = None
    dependencies: List[str] = field(default_factory=list)
    registered_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Validate service descriptor after initialization"""
        if self.implementation_type is None and self.factory is None and self.instance is None:
            raise ServiceRegistrationError(
                self.service_type.__name__,
                "Either implementation_type, factory, or instance must be provided"
            )

        provided_count = sum([
            self.implementation_type is not None,
            self.factory is not None,
            self.instance is not None
        ])

        if provided_count > 1:
            raise ServiceRegistrationError(
                self.service_type.__name__,
                "Cannot specify more than one of: implementation_type, factory, or instance"
            )


class ServiceRegistry:
    """
    Thread-safe service registry for the DI container.

    Manages service registration, lifecycle, and provides metadata
    about registered services.
    """

    def __init__(self):
        self._services: Dict[str, ServiceDescriptor] = {}
        self._singletons: Dict[str, Any] = {}
        self._scoped_instances: Dict[str, Dict[str, Any]] = {}
        self._lock = RLock()
        self._resolution_stack: List[str] = []

    def register_type(
        self,
        service_type: Type[T],
        implementation_type: Type[T],
        lifecycle: ServiceLifecycle = ServiceLifecycle.TRANSIENT
    ) -> None:
        """
        Register a service type with its implementation.

        Args:
            service_type: The abstract type or interface
            implementation_type: The concrete implementation
            lifecycle: Service lifecycle management
        """
        service_name = self._get_service_name(service_type)

        with self._lock:
            if service_name in self._services:
                raise ServiceRegistrationError(
                    service_name,
                    "Service already registered"
                )

            # Analyze dependencies
            dependencies = self._analyze_dependencies(implementation_type)

            descriptor = ServiceDescriptor(
                service_type=service_type,
                implementation_type=implementation_type,
                lifecycle=lifecycle,
                dependencies=dependencies
            )

            self._services[service_name] = descriptor

    def register_factory(
        self,
        service_type: Type[T],
        factory: Callable[..., T],
        lifecycle: ServiceLifecycle = ServiceLifecycle.TRANSIENT
    ) -> None:
        """
        Register a service with a factory function.

        Args:
            service_type: The service type
            factory: Factory function that creates instances
            lifecycle: Service lifecycle management
        """
        service_name = self._get_service_name(service_type)

        with self._lock:
            if service_name in self._services:
                raise ServiceRegistrationError(
                    service_name,
                    "Service already registered"
                )

            # Analyze factory dependencies
            dependencies = self._analyze_factory_dependencies(factory)

            descriptor = ServiceDescriptor(
                service_type=service_type,
                factory=factory,
                lifecycle=lifecycle,
                dependencies=dependencies
            )

            self._services[service_name] = descriptor

    def register_instance(
        self,
        service_type: Type[T],
        instance: T
    ) -> None:
        """
        Register a service instance (always singleton).

        Args:
            service_type: The service type
            instance: Pre-created instance
        """
        service_name = self._get_service_name(service_type)

        with self._lock:
            if service_name in self._services:
                raise ServiceRegistrationError(
                    service_name,
                    "Service already registered"
                )

            descriptor = ServiceDescriptor(
                service_type=service_type,
                lifecycle=ServiceLifecycle.SINGLETON,
                instance=instance
            )

            self._services[service_name] = descriptor
            self._singletons[service_name] = instance

    def is_registered(self, service_type: Type[T]) -> bool:
        """Check if a service type is registered"""
        service_name = self._get_service_name(service_type)
        return service_name in self._services

    def get_descriptor(self, service_type: Type[T]) -> ServiceDescriptor:
        """Get service descriptor for a registered service"""
        service_name = self._get_service_name(service_type)

        with self._lock:
            if service_name not in self._services:
                raise ServiceNotFoundError(service_name)

            return self._services[service_name]

    def get_all_descriptors(self) -> Dict[str, ServiceDescriptor]:
        """Get all registered service descriptors"""
        with self._lock:
            return self._services.copy()

    def unregister(self, service_type: Type[T]) -> None:
        """Unregister a service (mainly for testing)"""
        service_name = self._get_service_name(service_type)

        with self._lock:
            if service_name in self._services:
                del self._services[service_name]

            if service_name in self._singletons:
                del self._singletons[service_name]

            # Clean up scoped instances
            for scope_id in list(self._scoped_instances.keys()):
                if service_name in self._scoped_instances[scope_id]:
                    del self._scoped_instances[scope_id][service_name]

    def clear(self) -> None:
        """Clear all registered services (mainly for testing)"""
        with self._lock:
            self._services.clear()
            self._singletons.clear()
            self._scoped_instances.clear()
            self._resolution_stack.clear()

    def start_resolution(self, service_name: str) -> None:
        """Start service resolution and check for circular dependencies"""
        if service_name in self._resolution_stack:
            chain = self._resolution_stack + [service_name]
            raise CircularDependencyError(chain)

        self._resolution_stack.append(service_name)

    def end_resolution(self, service_name: str) -> None:
        """End service resolution"""
        if self._resolution_stack and self._resolution_stack[-1] == service_name:
            self._resolution_stack.pop()

    def get_singleton(self, service_name: str) -> Optional[Any]:
        """Get singleton instance if exists"""
        return self._singletons.get(service_name)

    def set_singleton(self, service_name: str, instance: Any) -> None:
        """Set singleton instance"""
        self._singletons[service_name] = instance

    def get_scoped(self, service_name: str, scope_id: str) -> Optional[Any]:
        """Get scoped instance if exists"""
        return self._scoped_instances.get(scope_id, {}).get(service_name)

    def set_scoped(self, service_name: str, scope_id: str, instance: Any) -> None:
        """Set scoped instance"""
        if scope_id not in self._scoped_instances:
            self._scoped_instances[scope_id] = {}

        self._scoped_instances[scope_id][service_name] = instance

    def clear_scope(self, scope_id: str) -> None:
        """Clear all instances for a specific scope"""
        if scope_id in self._scoped_instances:
            del self._scoped_instances[scope_id]

    def _get_service_name(self, service_type: Type) -> str:
        """Get canonical service name from type"""
        return f"{service_type.__module__}.{service_type.__name__}"

    def _analyze_dependencies(self, implementation_type: Type) -> List[str]:
        """Analyze constructor dependencies of an implementation type"""
        dependencies = []

        try:
            signature = inspect.signature(implementation_type.__init__)
            for param_name, param in signature.parameters.items():
                if param_name == 'self':
                    continue

                if param.annotation and param.annotation != inspect.Parameter.empty:
                    dep_name = self._get_service_name(param.annotation)
                    dependencies.append(dep_name)
        except (ValueError, TypeError):
            # If we can't analyze dependencies, that's okay
            pass

        return dependencies

    def _analyze_factory_dependencies(self, factory: Callable) -> List[str]:
        """Analyze dependencies of a factory function"""
        dependencies = []

        try:
            signature = inspect.signature(factory)
            for param_name, param in signature.parameters.items():
                if param.annotation and param.annotation != inspect.Parameter.empty:
                    dep_name = self._get_service_name(param.annotation)
                    dependencies.append(dep_name)
        except (ValueError, TypeError):
            # If we can't analyze dependencies, that's okay
            pass

        return dependencies