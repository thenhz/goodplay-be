"""
Dependency Injection Container for GoodPlay

Main DI container providing service registration, resolution, and lifecycle
management with support for singleton, transient, and scoped services.
"""
import inspect
from typing import Type, TypeVar, Any, Dict, Optional, Callable, Union
from threading import RLock
import uuid

from .registry import ServiceRegistry, ServiceLifecycle, ServiceDescriptor
from .exceptions import (
    ServiceNotFoundError,
    ServiceResolutionError,
    CircularDependencyError
)

T = TypeVar('T')


class DIContainer:
    """
    Thread-safe dependency injection container.

    Provides service registration, automatic dependency resolution,
    and lifecycle management for GoodPlay application services.
    """

    def __init__(self):
        self._registry = ServiceRegistry()
        self._lock = RLock()
        self._current_scope_id: Optional[str] = None

    def register_type(
        self,
        service_type: Type[T],
        implementation_type: Type[T],
        lifecycle: ServiceLifecycle = ServiceLifecycle.TRANSIENT
    ) -> 'DIContainer':
        """
        Register a service type with its implementation.

        Args:
            service_type: The abstract type or interface
            implementation_type: The concrete implementation
            lifecycle: Service lifecycle management

        Returns:
            DIContainer: Self for method chaining

        Example:
            container.register_type(IUserRepository, UserRepository, ServiceLifecycle.SINGLETON)
        """
        self._registry.register_type(service_type, implementation_type, lifecycle)
        return self

    def register_factory(
        self,
        service_type: Type[T],
        factory: Callable[..., T],
        lifecycle: ServiceLifecycle = ServiceLifecycle.TRANSIENT
    ) -> 'DIContainer':
        """
        Register a service with a factory function.

        Args:
            service_type: The service type
            factory: Factory function that creates instances
            lifecycle: Service lifecycle management

        Returns:
            DIContainer: Self for method chaining

        Example:
            container.register_factory(IUserService, lambda repo: UserService(repo))
        """
        self._registry.register_factory(service_type, factory, lifecycle)
        return self

    def register_instance(
        self,
        service_type: Type[T],
        instance: T
    ) -> 'DIContainer':
        """
        Register a service instance (always singleton).

        Args:
            service_type: The service type
            instance: Pre-created instance

        Returns:
            DIContainer: Self for method chaining

        Example:
            config = AppConfig()
            container.register_instance(IAppConfig, config)
        """
        self._registry.register_instance(service_type, instance)
        return self

    def resolve(self, service_type: Type[T]) -> T:
        """
        Resolve a service instance from the container.

        Args:
            service_type: The service type to resolve

        Returns:
            T: Service instance

        Raises:
            ServiceNotFoundError: If service is not registered
            ServiceResolutionError: If service cannot be created
            CircularDependencyError: If circular dependency is detected

        Example:
            user_service = container.resolve(IUserService)
        """
        service_name = self._get_service_name(service_type)

        with self._lock:
            try:
                self._registry.start_resolution(service_name)
                return self._resolve_service(service_type)
            except CircularDependencyError:
                raise
            except Exception as e:
                raise ServiceResolutionError(
                    service_name,
                    f"Failed to create instance: {str(e)}"
                )
            finally:
                self._registry.end_resolution(service_name)

    def try_resolve(self, service_type: Type[T]) -> Optional[T]:
        """
        Try to resolve a service instance, returning None if not registered.

        Args:
            service_type: The service type to resolve

        Returns:
            Optional[T]: Service instance or None if not registered
        """
        try:
            return self.resolve(service_type)
        except ServiceNotFoundError:
            return None

    def is_registered(self, service_type: Type[T]) -> bool:
        """
        Check if a service type is registered.

        Args:
            service_type: The service type to check

        Returns:
            bool: True if registered, False otherwise
        """
        return self._registry.is_registered(service_type)

    def get_services(self) -> Dict[str, ServiceDescriptor]:
        """
        Get all registered services with their descriptors.

        Returns:
            Dict[str, ServiceDescriptor]: All registered services
        """
        return self._registry.get_all_descriptors()

    def unregister(self, service_type: Type[T]) -> None:
        """
        Unregister a service (mainly for testing).

        Args:
            service_type: The service type to unregister
        """
        self._registry.unregister(service_type)

    def clear(self) -> None:
        """Clear all registered services (mainly for testing)"""
        self._registry.clear()

    def create_scope(self) -> 'DIScope':
        """
        Create a new scope for scoped services.

        Returns:
            DIScope: New scope context manager
        """
        return DIScope(self)

    def _resolve_service(self, service_type: Type[T]) -> T:
        """Internal service resolution logic"""
        service_name = self._get_service_name(service_type)
        descriptor = self._registry.get_descriptor(service_type)

        # Handle different lifecycles
        if descriptor.lifecycle == ServiceLifecycle.SINGLETON:
            return self._resolve_singleton(service_name, descriptor)
        elif descriptor.lifecycle == ServiceLifecycle.SCOPED:
            return self._resolve_scoped(service_name, descriptor)
        else:  # TRANSIENT
            return self._create_instance(descriptor)

    def _resolve_singleton(self, service_name: str, descriptor: ServiceDescriptor) -> Any:
        """Resolve singleton service"""
        # Check if we already have an instance
        if descriptor.instance is not None:
            return descriptor.instance

        instance = self._registry.get_singleton(service_name)
        if instance is not None:
            return instance

        # Create new singleton instance
        instance = self._create_instance(descriptor)
        self._registry.set_singleton(service_name, instance)
        return instance

    def _resolve_scoped(self, service_name: str, descriptor: ServiceDescriptor) -> Any:
        """Resolve scoped service"""
        if self._current_scope_id is None:
            raise ServiceResolutionError(
                service_name,
                "Scoped service requested outside of scope context"
            )

        instance = self._registry.get_scoped(service_name, self._current_scope_id)
        if instance is not None:
            return instance

        # Create new scoped instance
        instance = self._create_instance(descriptor)
        self._registry.set_scoped(service_name, self._current_scope_id, instance)
        return instance

    def _create_instance(self, descriptor: ServiceDescriptor) -> Any:
        """Create a new service instance"""
        if descriptor.factory is not None:
            return self._create_from_factory(descriptor.factory)
        elif descriptor.implementation_type is not None:
            return self._create_from_type(descriptor.implementation_type)
        else:
            raise ServiceResolutionError(
                descriptor.service_type.__name__,
                "No factory or implementation type specified"
            )

    def _create_from_factory(self, factory: Callable) -> Any:
        """Create instance from factory function"""
        # Resolve factory dependencies
        signature = inspect.signature(factory)
        args = []

        for param_name, param in signature.parameters.items():
            if param.annotation and param.annotation != inspect.Parameter.empty:
                dependency = self.resolve(param.annotation)
                args.append(dependency)

        return factory(*args)

    def _create_from_type(self, implementation_type: Type) -> Any:
        """Create instance from implementation type"""
        # Resolve constructor dependencies
        signature = inspect.signature(implementation_type.__init__)
        args = [implementation_type]  # self parameter

        for param_name, param in signature.parameters.items():
            if param_name == 'self':
                continue

            if param.annotation and param.annotation != inspect.Parameter.empty:
                dependency = self.resolve(param.annotation)
                args.append(dependency)
            elif param.default != inspect.Parameter.empty:
                # Use default value if available
                args.append(param.default)
            else:
                raise ServiceResolutionError(
                    implementation_type.__name__,
                    f"Cannot resolve parameter '{param_name}' (no type annotation or default value)"
                )

        # Create instance
        return implementation_type(*args[1:])  # Exclude self

    def _get_service_name(self, service_type: Type) -> str:
        """Get canonical service name from type"""
        return f"{service_type.__module__}.{service_type.__name__}"

    def _set_scope_id(self, scope_id: str) -> None:
        """Set current scope ID (internal use)"""
        self._current_scope_id = scope_id

    def _clear_scope_id(self) -> None:
        """Clear current scope ID (internal use)"""
        self._current_scope_id = None


class DIScope:
    """
    Context manager for scoped services.

    Ensures that scoped services are properly managed within
    a specific execution context (e.g., HTTP request).
    """

    def __init__(self, container: DIContainer):
        self.container = container
        self.scope_id = str(uuid.uuid4())
        self._previous_scope_id: Optional[str] = None

    def __enter__(self) -> 'DIScope':
        """Enter scope context"""
        self._previous_scope_id = self.container._current_scope_id
        self.container._set_scope_id(self.scope_id)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit scope context and cleanup scoped instances"""
        self.container._registry.clear_scope(self.scope_id)
        self.container._set_scope_id(self._previous_scope_id)