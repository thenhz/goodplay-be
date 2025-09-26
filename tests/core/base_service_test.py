"""
BaseServiceTest - Enterprise Test Class for Service Layer Testing (GOO-35)

Provides standardized testing patterns for service layer classes with automatic
repository mocking, Smart Fixture integration, and performance monitoring.
"""
import unittest
import time
import logging
from typing import Dict, Any, Callable, Optional, Type
from unittest.mock import MagicMock, patch, Mock
from abc import ABC
from flask import Flask

# Import configuration
from .config import TestConfig

try:
    # Import Smart Fixture System (optional)
    from tests.fixtures import (
        smart_fixture, factory_fixture, preset_fixture,
        smart_fixture_manager, performance_monitor, cleanup_manager,
        FixtureScope, get_system_health
    )
    SMART_FIXTURES_AVAILABLE = True
except ImportError:
    SMART_FIXTURES_AVAILABLE = False
    smart_fixture_manager = performance_monitor = None


class BaseServiceTest(unittest.TestCase):
    """
    Base test class for service layer testing with Smart Fixture integration

    Features:
    - Automatic repository dependency mocking
    - Smart Fixture integration for test data generation
    - Service method pattern validation (success/failure scenarios)
    - Performance monitoring and assertions
    - Business logic isolation with dependency injection
    - Common service testing utilities and patterns

    Usage:
    ```python
    class TestUserService(BaseServiceTest):
        service_class = UserService
        repository_dependencies = ['user_repository']

        def test_create_user_success(self):
            # Setup test data using Smart Fixtures
            user_data = self.create_test_user_data()

            # Test service method
            success, message, result = self.service.create_user(user_data)

            # Validate using built-in assertions
            self.assert_service_success(success, message, result)
    ```
    """

    # Service configuration - override in subclasses
    service_class: Optional[Type] = None
    repository_dependencies: list = []
    external_dependencies: list = []

    def setUp(self):
        """Enhanced setup for service layer testing"""
        super().setUp()

        # Setup Flask application context
        self._setup_flask_context()

        # Initialize Smart Fixture integration
        self._setup_smart_fixture_integration()

        # Setup service instance with mocked dependencies
        self._setup_service_with_mocks()

        # Setup performance monitoring for service operations
        self._setup_service_performance_monitoring()

        print(f"Service test setup complete: {self.service_class.__name__ if self.service_class else 'Unknown'}")

    def tearDown(self):
        """Enhanced teardown with Smart Fixture cleanup"""
        # Cleanup Flask context
        if hasattr(self, 'app_context'):
            self.app_context.pop()

        # Cleanup Smart Fixtures for this test
        if SMART_FIXTURES_AVAILABLE and cleanup_manager:
            try:
                if hasattr(cleanup_manager, 'cleanup_fixture_scope'):
                    cleanup_manager.cleanup_fixture_scope('function')
                # Skip cleanup_fixture() call since it requires fixture_name parameter
                # and we're not tracking individual fixture names in this context
            except Exception as e:
                print(f"Warning: Smart Fixture cleanup failed: {e}")

        # Log service performance if enabled
        self._log_service_performance()

        # Parent teardown
        super().tearDown()

    def _setup_flask_context(self):
        """Setup Flask application context for services that use current_app"""
        # Create minimal Flask app for testing if none exists
        if not hasattr(self, 'app'):
            from flask import Flask
            self.app = Flask(__name__)
            self.app.config['TESTING'] = True
            self.app.config['SECRET_KEY'] = 'test-secret-key'
            self.app.config['JWT_SECRET_KEY'] = 'jwt-test-secret-key'

        # Setup application context
        self.app_context = self.app.app_context()
        self.app_context.push()

        # Mock current_app.logger to prevent Flask context errors
        self.current_app_patcher = patch('flask.current_app')
        mock_current_app = self.current_app_patcher.start()
        mock_logger = MagicMock()
        mock_current_app.logger = mock_logger
        self.mock_current_app = mock_current_app
        self.mock_logger = mock_logger

        # Ensure cleanup
        self.addCleanup(self.current_app_patcher.stop)

    def _setup_smart_fixture_integration(self):
        """Initialize Smart Fixture system for service testing"""
        # Register common service test fixtures
        if not hasattr(self, '_smart_fixtures_registered'):
            self._register_service_test_fixtures()
            self._smart_fixtures_registered = True

    def _setup_service_with_mocks(self):
        """Setup service instance with automatically mocked dependencies"""
        if not self.service_class:
            print("No service_class specified, skipping service setup")
            return

        # Create service instance
        self.service = self.service_class()

        # Setup repository mocks
        self.repository_mocks = {}
        for repo_name in self.repository_dependencies:
            mock_repo = self._create_repository_mock(repo_name)
            self.repository_mocks[repo_name] = mock_repo
            setattr(self.service, repo_name, mock_repo)

        # Setup external dependency mocks
        self.external_mocks = {}
        for dep_name in self.external_dependencies:
            mock_dep = MagicMock()
            self.external_mocks[dep_name] = mock_dep
            setattr(self.service, dep_name, mock_dep)

        print(f"Service setup complete with {len(self.repository_mocks)} repository mocks and {len(self.external_mocks)} external mocks")

    def _setup_service_performance_monitoring(self):
        """Setup performance monitoring for service operations"""
        self.service_operation_timings = {}
        self.performance_thresholds = {
            'max_operation_time_ms': 100.0,  # Service operations should be fast
            'max_memory_increase_mb': 10.0   # Reasonable memory usage
        }

    def _create_repository_mock(self, repo_name: str) -> MagicMock:
        """Create a properly configured repository mock"""
        repo_mock = MagicMock()

        # Setup common repository method defaults
        repo_mock.find_by_id.return_value = None
        repo_mock.find_one.return_value = None
        repo_mock.find_many.return_value = []
        repo_mock.create.return_value = "test_id_123"
        repo_mock.update_by_id.return_value = True
        repo_mock.update_one.return_value = True
        repo_mock.delete_by_id.return_value = True
        repo_mock.delete_one.return_value = True
        repo_mock.count.return_value = 0
        repo_mock.create_indexes.return_value = None

        print(f"Created repository mock: {repo_name}")
        return repo_mock

    def _register_service_test_fixtures(self):
        """Register common fixtures for service testing"""

        @smart_fixture('test_user_data', scope=FixtureScope.FUNCTION)
        def test_user_data():
            return {
                'email': 'test@goodplay.com',
                'password': 'password123',
                'first_name': 'Test',
                'last_name': 'User',
                'preferences': {
                    'gaming': {'difficulty': 'medium'},
                    'notifications': {'email_enabled': True},
                    'privacy': {'profile_public': False},
                    'donations': {'auto_donate': False}
                }
            }

        @smart_fixture('test_game_data', scope=FixtureScope.FUNCTION)
        def test_game_data():
            return {
                'title': 'Test Game',
                'description': 'A test game for unit testing',
                'category': 'puzzle',
                'difficulty': 'medium',
                'credits_required': 10
            }

        @smart_fixture('test_session_data', scope=FixtureScope.FUNCTION)
        def test_session_data():
            return {
                'user_id': 'test_user_123',
                'game_id': 'test_game_123',
                'status': 'active',
                'play_duration_ms': 0,
                'device_info': {
                    'platform': 'web',
                    'device_type': 'desktop'
                }
            }

    def _log_service_performance(self):
        """Log service performance metrics"""
        if hasattr(self, 'service_operation_timings') and self.service_operation_timings:
            print("Service operation timings:", self.service_operation_timings)

    # Smart Fixture Integration Methods

    def create_test_user_data(self, **overrides) -> Dict[str, Any]:
        """Create test user data using Smart Fixtures"""
        user_data = smart_fixture_manager.create_fixture('test_user_data')
        if overrides:
            user_data.update(overrides)
        return user_data

    def create_test_game_data(self, **overrides) -> Dict[str, Any]:
        """Create test game data using Smart Fixtures"""
        game_data = smart_fixture_manager.create_fixture('test_game_data')
        if overrides:
            game_data.update(overrides)
        return game_data

    def create_test_session_data(self, **overrides) -> Dict[str, Any]:
        """Create test session data using Smart Fixtures"""
        session_data = smart_fixture_manager.create_fixture('test_session_data')
        if overrides:
            session_data.update(overrides)
        return session_data

    # Service Testing Utilities

    def setup_repository_mock_response(self, repo_name: str, method_name: str, return_value: Any):
        """Setup a specific repository mock method response"""
        if repo_name not in self.repository_mocks:
            raise ValueError(f"Repository mock '{repo_name}' not found. Available: {list(self.repository_mocks.keys())}")

        repo_mock = self.repository_mocks[repo_name]
        getattr(repo_mock, method_name).return_value = return_value

        print(f"Setup {repo_name}.{method_name} to return: {return_value}")

    def assert_repository_method_called(self, repo_name: str, method_name: str, *args, **kwargs):
        """Assert that a repository method was called with specific arguments"""
        if repo_name not in self.repository_mocks:
            raise AssertionError(f"Repository mock '{repo_name}' not found")

        repo_mock = self.repository_mocks[repo_name]
        method_mock = getattr(repo_mock, method_name)

        if args or kwargs:
            method_mock.assert_called_with(*args, **kwargs)
        else:
            method_mock.assert_called()

    def assert_repository_method_not_called(self, repo_name: str, method_name: str):
        """Assert that a repository method was not called"""
        if repo_name not in self.repository_mocks:
            raise AssertionError(f"Repository mock '{repo_name}' not found")

        repo_mock = self.repository_mocks[repo_name]
        method_mock = getattr(repo_mock, method_name)
        method_mock.assert_not_called()

    def get_repository_method_call_count(self, repo_name: str, method_name: str) -> int:
        """Get the number of times a repository method was called"""
        if repo_name not in self.repository_mocks:
            return 0

        repo_mock = self.repository_mocks[repo_name]
        method_mock = getattr(repo_mock, method_name)
        return method_mock.call_count

    # Service Method Testing Patterns

    def assert_service_success(self, success: bool, message: str, result: Any, expected_message: str = None):
        """Assert that a service method returned success"""
        assert success is True, f"Expected service operation to succeed, but got failure. Message: {message}"

        if expected_message:
            assert message == expected_message, f"Expected message '{expected_message}', got '{message}'"

        assert result is not None, "Expected service operation to return result data"

        print(f"Service success assertion passed: {message}")

    def assert_service_failure(self, success: bool, message: str, result: Any, expected_message: str = None):
        """Assert that a service method returned failure"""
        assert success is False, f"Expected service operation to fail, but got success. Message: {message}"

        if expected_message:
            assert message == expected_message, f"Expected message '{expected_message}', got '{message}'"

        # Result can be None for failures
        print(f"Service failure assertion passed: {message}")

    def assert_service_performance(self, operation_func: Callable, max_time_ms: float = None, *args, **kwargs):
        """Assert that a service operation completes within performance thresholds"""
        max_time = max_time_ms or self.performance_thresholds['max_operation_time_ms']

        start_time = time.time()
        result = operation_func(*args, **kwargs)
        execution_time_ms = (time.time() - start_time) * 1000

        assert execution_time_ms <= max_time, \
            f"Service operation took {execution_time_ms:.1f}ms, expected under {max_time}ms"

        # Track timing for reporting
        operation_name = operation_func.__name__ if hasattr(operation_func, '__name__') else str(operation_func)
        self.service_operation_timings[operation_name] = execution_time_ms

        print(f"Service performance assertion passed: {operation_name} took {execution_time_ms:.1f}ms")
        return result

    # Validation Utilities

    def validate_service_response_pattern(self, response: tuple):
        """Validate that service response follows the standard (success, message, result) pattern"""
        assert isinstance(response, tuple), f"Service response must be a tuple, got {type(response)}"
        assert len(response) == 3, f"Service response must be a 3-tuple (success, message, result), got {len(response)} elements"

        success, message, result = response
        assert isinstance(success, bool), f"First element (success) must be boolean, got {type(success)}"
        assert isinstance(message, str), f"Second element (message) must be string, got {type(message)}"
        # Result can be any type including None

        print("Service response pattern validation passed")
        return success, message, result

    def validate_service_error_handling(self, service_method: Callable, *args, **kwargs):
        """Validate that service method handles errors gracefully"""
        try:
            response = service_method(*args, **kwargs)
            success, message, result = self.validate_service_response_pattern(response)

            # If an exception was expected but not raised, the service should return failure
            if success:
                print("Service method completed successfully without raising exception")
            else:
                print(f"Service method returned failure gracefully: {message}")

        except Exception as e:
            # If service method raises exception, it should be logged and handled
            print(f"Service method raised exception: {str(e)}")
            # Re-raise for test to handle
            raise

    # Integration with Smart Fixture Performance Monitoring

    def get_smart_fixture_performance_report(self) -> Dict[str, Any]:
        """Get Smart Fixture performance report for this test"""
        return performance_monitor.get_performance_report()

    def assert_smart_fixture_performance(self):
        """Assert that Smart Fixture performance meets thresholds"""
        report = self.get_smart_fixture_performance_report()

        # Check cache hit ratio
        cache_hit_ratio = report.get('overall_cache_hit_ratio', 0.0)
        if report.get('cache_hits', 0) + report.get('cache_misses', 0) > 0:
            assert cache_hit_ratio >= 0.5, \
                f"Smart Fixture cache hit ratio {cache_hit_ratio:.1%} is below 50%"

        # Check memory usage
        memory_usage_mb = report.get('memory_usage_mb', 0.0)
        assert memory_usage_mb <= self.performance_thresholds['max_memory_increase_mb'], \
            f"Smart Fixture memory usage {memory_usage_mb:.1f}MB exceeds threshold"

        print(f"Smart Fixture performance check passed - Cache: {cache_hit_ratio:.1%}, Memory: {memory_usage_mb:.1f}MB")

    def get_system_health_report(self) -> Dict[str, Any]:
        """Get system health report including Smart Fixtures"""
        return get_system_health()


class ServiceTestMixin:
    """
    Mixin class providing additional utilities for service testing
    Can be used with existing test classes that can't extend BaseServiceTest
    """

    def setup_service_mocks(self, service_instance, repository_dependencies: list):
        """Setup repository mocks for a service instance"""
        mocks = {}
        for repo_name in repository_dependencies:
            mock_repo = MagicMock()
            mocks[repo_name] = mock_repo
            setattr(service_instance, repo_name, mock_repo)
        return mocks

    def assert_service_method_pattern(self, method_result: tuple):
        """Assert service method follows standard pattern"""
        assert isinstance(method_result, tuple) and len(method_result) == 3
        success, message, result = method_result
        assert isinstance(success, bool)
        assert isinstance(message, str)
        return success, message, result