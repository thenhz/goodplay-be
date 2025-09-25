"""
Decorators for Dependency Injection Integration

Provides decorators for automatic service registration and dependency
injection in Flask applications and service classes.
"""
import inspect
import functools
from typing import Type, TypeVar, Callable, Any, Dict, List, Optional, get_type_hints
from flask import g, current_app

from .registry import ServiceLifecycle
from .exceptions import ServiceResolutionError

T = TypeVar('T')


def injectable(
    lifecycle: ServiceLifecycle = ServiceLifecycle.TRANSIENT,
    service_type: Optional[Type] = None
) -> Callable[[Type[T]], Type[T]]:
    """
    Decorator to mark a class as injectable and automatically register it.

    Args:
        lifecycle: Service lifecycle (singleton, transient, scoped)
        service_type: Service interface type (defaults to the decorated class)

    Returns:
        Decorated class with injection metadata

    Example:
        @injectable(ServiceLifecycle.SINGLETON)
        class UserService:
            def __init__(self, user_repo: IUserRepository):
                self.user_repo = user_repo
    """
    def decorator(cls: Type[T]) -> Type[T]:
        # Add metadata to the class
        cls._di_lifecycle = lifecycle
        cls._di_service_type = service_type or cls
        cls._di_injectable = True

        # Analyze dependencies from constructor
        cls._di_dependencies = _analyze_class_dependencies(cls)

        return cls

    return decorator


def inject(*service_types: Type) -> Callable:
    """
    Decorator for Flask route handlers to inject dependencies.

    Args:
        *service_types: Service types to inject as parameters

    Returns:
        Decorated function with dependency injection

    Example:
        @app.route('/users')
        @inject(IUserService)
        def get_users(user_service: IUserService):
            return user_service.get_all_users()
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Get DI container from Flask app context
            container = _get_container()
            if container is None:
                raise ServiceResolutionError(
                    func.__name__,
                    "DI container not found in Flask application context"
                )

            # Create scope for request-scoped services
            with container.create_scope():
                # Resolve dependencies
                injected_services = []
                for service_type in service_types:
                    service = container.resolve(service_type)
                    injected_services.append(service)

                # Call original function with injected services
                return func(*args, *injected_services, **kwargs)

        return wrapper

    return decorator


def auto_inject(func: Callable) -> Callable:
    """
    Decorator that automatically injects dependencies based on type hints.

    Args:
        func: Function to decorate

    Returns:
        Decorated function with automatic dependency injection

    Example:
        @app.route('/users/<user_id>')
        @auto_inject
        def get_user(user_id: str, user_service: IUserService):
            return user_service.get_user_by_id(user_id)
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Get DI container
        container = _get_container()
        if container is None:
            raise ServiceResolutionError(
                func.__name__,
                "DI container not found in Flask application context"
            )

        # Analyze function signature
        signature = inspect.signature(func)
        type_hints = get_type_hints(func)

        # Create scope for request-scoped services
        with container.create_scope():
            # Resolve dependencies based on type hints
            injected_kwargs = {}
            for param_name, param in signature.parameters.items():
                # Skip parameters already provided
                if param_name in kwargs:
                    continue

                # Check if parameter has type hint and is registered service
                if param_name in type_hints:
                    service_type = type_hints[param_name]
                    if container.is_registered(service_type):
                        injected_kwargs[param_name] = container.resolve(service_type)

            # Merge with existing kwargs
            kwargs.update(injected_kwargs)

            return func(*args, **kwargs)

    return wrapper


def scoped_inject(*service_types: Type) -> Callable:
    """
    Decorator for injecting scoped services that persist for the request.

    Args:
        *service_types: Service types to inject

    Returns:
        Decorated function with scoped dependency injection

    Example:
        @app.route('/users')
        @scoped_inject(IUserService, IAuthService)
        def get_users(user_service: IUserService, auth_service: IAuthService):
            # Services will be the same instance for this request
            return user_service.get_all_users()
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            container = _get_container()
            if container is None:
                raise ServiceResolutionError(
                    func.__name__,
                    "DI container not found in Flask application context"
                )

            # Use or create request scope
            scope = _get_or_create_request_scope(container)

            # Resolve services within scope
            injected_services = []
            for service_type in service_types:
                service = container.resolve(service_type)
                injected_services.append(service)

            return func(*args, *injected_services, **kwargs)

        return wrapper

    return decorator


def service_factory(service_type: Type, lifecycle: ServiceLifecycle = ServiceLifecycle.TRANSIENT):
    """
    Decorator to mark a function as a service factory.

    Args:
        service_type: The service type this factory creates
        lifecycle: Service lifecycle

    Returns:
        Decorated factory function

    Example:
        @service_factory(IUserService, ServiceLifecycle.SINGLETON)
        def create_user_service(user_repo: IUserRepository) -> IUserService:
            return UserService(user_repo)
    """
    def decorator(func: Callable) -> Callable:
        func._di_service_factory = True
        func._di_service_type = service_type
        func._di_lifecycle = lifecycle
        func._di_dependencies = _analyze_function_dependencies(func)
        return func

    return decorator


def _get_container():
    """Get DI container from Flask application context"""
    if hasattr(current_app, 'di_container'):
        return current_app.di_container

    if hasattr(g, 'di_container'):
        return g.di_container

    return None


def _get_or_create_request_scope(container):
    """Get or create request scope for scoped services"""
    if not hasattr(g, 'di_scope'):
        g.di_scope = container.create_scope()
        g.di_scope.__enter__()

        # Register cleanup at end of request
        @current_app.teardown_request
        def cleanup_scope(exception=None):
            if hasattr(g, 'di_scope'):
                g.di_scope.__exit__(None, None, None)
                delattr(g, 'di_scope')

    return g.di_scope


def _analyze_class_dependencies(cls: Type) -> List[str]:
    """Analyze constructor dependencies of a class"""
    dependencies = []

    try:
        signature = inspect.signature(cls.__init__)
        type_hints = get_type_hints(cls.__init__)

        for param_name, param in signature.parameters.items():
            if param_name == 'self':
                continue

            if param_name in type_hints:
                service_type = type_hints[param_name]
                dependencies.append(_get_service_name(service_type))

    except (ValueError, TypeError):
        # If we can't analyze dependencies, that's okay
        pass

    return dependencies


def _analyze_function_dependencies(func: Callable) -> List[str]:
    """Analyze dependencies of a function"""
    dependencies = []

    try:
        signature = inspect.signature(func)
        type_hints = get_type_hints(func)

        for param_name, param in signature.parameters.items():
            if param_name in type_hints:
                service_type = type_hints[param_name]
                dependencies.append(_get_service_name(service_type))

    except (ValueError, TypeError):
        # If we can't analyze dependencies, that's okay
        pass

    return dependencies


def _get_service_name(service_type: Type) -> str:
    """Get canonical service name from type"""
    return f"{service_type.__module__}.{service_type.__name__}"


# Flask integration utilities

class FlaskDIIntegration:
    """
    Flask integration utilities for dependency injection.

    Provides helpers for integrating the DI container with Flask
    application lifecycle and request handling.
    """

    @staticmethod
    def init_app(app, container, config=None):
        """
        Initialize Flask app with dependency injection.

        Args:
            app: Flask application
            container: DI container
            config: Optional DI configuration
        """
        # Store container in app context
        app.di_container = container

        # Apply configuration if provided
        if config:
            FlaskDIIntegration._apply_config(container, config)

        # Register request context handlers
        FlaskDIIntegration._setup_request_handlers(app)

    @staticmethod
    def _apply_config(container, config):
        """Apply DI configuration to container"""
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

    @staticmethod
    def _setup_request_handlers(app):
        """Setup request context handlers for scoped services"""
        @app.before_request
        def before_request():
            # Request scope will be created on demand
            pass

        @app.teardown_request
        def teardown_request(exception=None):
            # Cleanup happens in decorator
            pass