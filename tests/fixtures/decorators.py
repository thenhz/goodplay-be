"""
Smart Fixture Decorators for GOO-34

Provides convenient decorators and utilities for intelligent fixture management.
"""
import functools
import inspect
from typing import Callable, List, Optional, Any
import pytest

from .smart_manager import (
    SmartFixtureManager,
    FixtureScope,
    smart_fixture_manager
)


def smart_fixture(
    name: str = None,
    scope: FixtureScope = FixtureScope.FUNCTION,
    dependencies: List[str] = None,
    factory_class: str = None,
    auto_register: bool = True
):
    """
    Decorator for creating smart fixtures with automatic dependency resolution

    Args:
        name: Fixture name (defaults to function name)
        scope: Fixture scope for caching
        dependencies: List of fixture names this fixture depends on
        factory_class: Associated Factory-Boy class name
        auto_register: Whether to auto-register with pytest

    Usage:
        @smart_fixture('user_with_wallet', dependencies=['basic_user', 'wallet'])
        def user_with_wallet(basic_user, wallet):
            return {**basic_user, 'wallet': wallet}
    """

    def decorator(func: Callable) -> Callable:
        fixture_name = name or func.__name__
        deps = dependencies or []

        # Auto-detect dependencies from function signature
        sig = inspect.signature(func)
        detected_deps = [
            param.name for param in sig.parameters.values()
            if param.name != 'request'  # Skip pytest request parameter
        ]

        # Combine explicit and detected dependencies
        all_deps = list(set(deps + detected_deps))

        # Register with smart fixture manager
        smart_fixture_manager.register_fixture(
            name=fixture_name,
            creator=func,
            scope=scope,
            dependencies=all_deps,
            factory_class=factory_class
        )

        @functools.wraps(func)
        def smart_wrapper(*args, **kwargs):
            """Smart wrapper that uses the fixture manager"""
            return smart_fixture_manager.create_fixture(
                fixture_name,
                scope=scope,
                **kwargs
            )

        # Also create a pytest fixture if auto_register is True
        if auto_register:
            pytest_scope = _fixture_scope_to_pytest(scope)
            pytest_fixture = pytest.fixture(scope=pytest_scope, name=fixture_name)(smart_wrapper)
            return pytest_fixture
        else:
            return smart_wrapper

    return decorator


def factory_fixture(
    factory_class: Any,
    name: str = None,
    scope: FixtureScope = FixtureScope.FUNCTION,
    trait: str = None,
    count: int = 1,
    **factory_kwargs
):
    """
    Decorator for creating fixtures from Factory-Boy factories

    Args:
        factory_class: Factory-Boy factory class
        name: Fixture name (defaults to factory class name)
        scope: Fixture scope for caching
        trait: Factory trait to apply
        count: Number of objects to create (>1 creates a list)
        **factory_kwargs: Default kwargs for factory creation

    Usage:
        @factory_fixture(UserFactory, trait='admin')
        def admin_user():
            pass  # Returns admin user created by UserFactory
    """

    def decorator(func: Callable) -> Callable:
        fixture_name = name or factory_class.__name__.lower().replace('factory', '')

        def factory_creator(**kwargs):
            """Create object using Factory-Boy factory"""
            merged_kwargs = {**factory_kwargs, **kwargs}

            if trait:
                merged_kwargs[trait] = True

            if count > 1:
                return factory_class.build_batch(count, **merged_kwargs)
            else:
                return factory_class.build(**merged_kwargs)

        # Register factory with smart manager
        smart_fixture_manager.register_factory(fixture_name, factory_class)

        # Register as smart fixture
        smart_fixture_manager.register_fixture(
            name=fixture_name,
            creator=factory_creator,
            scope=scope,
            factory_class=factory_class.__name__
        )

        @functools.wraps(func)
        def factory_wrapper(*args, **kwargs):
            return smart_fixture_manager.create_fixture(
                fixture_name,
                scope=scope,
                **kwargs
            )

        # Create pytest fixture
        pytest_scope = _fixture_scope_to_pytest(scope)
        return pytest.fixture(scope=pytest_scope, name=fixture_name)(factory_wrapper)

    return decorator


def preset_fixture(preset_name: str, scope: FixtureScope = FixtureScope.FUNCTION):
    """
    Decorator for creating preset fixture combinations

    Args:
        preset_name: Name of the preset (e.g., 'basic_user_setup')
        scope: Fixture scope for caching

    Usage:
        @preset_fixture('gaming_session_setup')
        def gaming_session_setup():
            # Will automatically resolve to user + game + session
            return smart_fixture_manager.create_preset('gaming_session_setup')
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def preset_wrapper(*args, **kwargs):
            return smart_fixture_manager.create_preset(preset_name, **kwargs)

        pytest_scope = _fixture_scope_to_pytest(scope)
        return pytest.fixture(scope=pytest_scope, name=preset_name)(preset_wrapper)

    return decorator


def lazy_fixture(
    name: str = None,
    scope: FixtureScope = FixtureScope.LAZY,
    dependencies: List[str] = None
):
    """
    Decorator for creating lazy-loaded fixtures

    Lazy fixtures are only created when actually accessed,
    not when the test function starts.

    Args:
        name: Fixture name
        scope: Fixture scope (defaults to LAZY)
        dependencies: Fixture dependencies

    Usage:
        @lazy_fixture('expensive_computation')
        def expensive_computation():
            # Only executed when actually needed
            return perform_expensive_operation()
    """

    def decorator(func: Callable) -> Callable:
        fixture_name = name or func.__name__

        class LazyFixture:
            """Lazy fixture wrapper"""

            def __init__(self):
                self._loaded = False
                self._value = None

            def __call__(self, *args, **kwargs):
                if not self._loaded:
                    self._value = func(*args, **kwargs)
                    self._loaded = True
                return self._value

            def __getattr__(self, item):
                # Access any attribute triggers loading
                value = self()
                return getattr(value, item)

            def __repr__(self):
                if self._loaded:
                    return f"LazyFixture({repr(self._value)})"
                return f"LazyFixture(unloaded: {fixture_name})"

        lazy_instance = LazyFixture()

        # Register with smart fixture manager
        smart_fixture_manager.register_fixture(
            name=fixture_name,
            creator=lambda: lazy_instance(),
            scope=scope,
            dependencies=dependencies or []
        )

        return lazy_instance

    return decorator


def performance_monitor(threshold_ms: float = 50.0):
    """
    Decorator to monitor fixture performance and log warnings

    Args:
        threshold_ms: Warning threshold in milliseconds

    Usage:
        @performance_monitor(threshold_ms=100.0)
        @smart_fixture('slow_fixture')
        def slow_fixture():
            return expensive_operation()
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def monitored_wrapper(*args, **kwargs):
            import time
            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration_ms = (time.time() - start_time) * 1000
                if duration_ms > threshold_ms:
                    import logging
                    logger = logging.getLogger('smart_fixtures')
                    logger.warning(
                        f"Fixture '{func.__name__}' took {duration_ms:.1f}ms "
                        f"(threshold: {threshold_ms}ms)"
                    )

        return monitored_wrapper

    return decorator


def _fixture_scope_to_pytest(scope: FixtureScope) -> str:
    """Convert FixtureScope to pytest scope string"""
    scope_mapping = {
        FixtureScope.FUNCTION: "function",
        FixtureScope.CLASS: "class",
        FixtureScope.MODULE: "module",
        FixtureScope.SESSION: "session",
        FixtureScope.LAZY: "function"  # Lazy fixtures default to function scope
    }
    return scope_mapping.get(scope, "function")


# Convenience aliases
smart = smart_fixture  # Shorter alias
factory = factory_fixture  # Shorter alias
preset = preset_fixture  # Shorter alias
lazy = lazy_fixture  # Shorter alias