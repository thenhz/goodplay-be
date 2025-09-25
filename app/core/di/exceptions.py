"""
Dependency Injection Exceptions

Custom exceptions for the GoodPlay DI container system to provide
clear error messages and proper exception hierarchy.
"""


class DIContainerError(Exception):
    """Base exception for all DI container errors"""
    pass


class ServiceNotFoundError(DIContainerError):
    """Raised when a requested service is not registered in the container"""

    def __init__(self, service_name: str):
        self.service_name = service_name
        super().__init__(f"Service '{service_name}' is not registered in the DI container")


class CircularDependencyError(DIContainerError):
    """Raised when a circular dependency is detected during service resolution"""

    def __init__(self, dependency_chain: list):
        self.dependency_chain = dependency_chain
        chain_str = " -> ".join(dependency_chain)
        super().__init__(f"Circular dependency detected: {chain_str}")


class ServiceRegistrationError(DIContainerError):
    """Raised when there's an error during service registration"""

    def __init__(self, service_name: str, reason: str):
        self.service_name = service_name
        self.reason = reason
        super().__init__(f"Failed to register service '{service_name}': {reason}")


class ServiceResolutionError(DIContainerError):
    """Raised when there's an error during service resolution"""

    def __init__(self, service_name: str, reason: str):
        self.service_name = service_name
        self.reason = reason
        super().__init__(f"Failed to resolve service '{service_name}': {reason}")


class InvalidServiceLifecycleError(DIContainerError):
    """Raised when an invalid service lifecycle is specified"""

    def __init__(self, lifecycle: str):
        self.lifecycle = lifecycle
        super().__init__(f"Invalid service lifecycle: '{lifecycle}'. Must be one of: singleton, transient, scoped")