"""
Dependency Injection Module for GoodPlay

Provides comprehensive dependency injection container system with service
registration, lifecycle management, and automatic dependency resolution.

Components:
- DIContainer: Main dependency injection container
- ServiceRegistry: Service registration and lifecycle management
- RepositoryFactory: Factory for repository instances
- ServiceFactory: Factory for service instances
- Injectable: Decorators for automatic service registration
"""

from .container import DIContainer
from .registry import ServiceRegistry, ServiceLifecycle
from .factories import RepositoryFactory, ServiceFactory
from .decorators import injectable, inject, auto_inject
from .config import DIConfig
from .bootstrap import DIBootstrap
from .exceptions import (
    DIContainerError,
    ServiceNotFoundError,
    CircularDependencyError,
    ServiceRegistrationError,
    ServiceResolutionError,
    InvalidServiceLifecycleError
)

__all__ = [
    'DIContainer',
    'ServiceRegistry',
    'ServiceLifecycle',
    'RepositoryFactory',
    'ServiceFactory',
    'injectable',
    'inject',
    'auto_inject',
    'DIConfig',
    'DIBootstrap',
    'DIContainerError',
    'ServiceNotFoundError',
    'CircularDependencyError',
    'ServiceRegistrationError',
    'ServiceResolutionError',
    'InvalidServiceLifecycleError'
]