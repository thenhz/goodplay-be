"""
BaseUnitTest - Generic Unit Test Base Class (GOO-35)

Provides a generic, lightweight base class for unit testing any component
with automatic dependency mocking, Smart Fixture integration, and zero setup boilerplate.
"""
import pytest
import time
import os
from typing import Dict, Any, List, Optional, Type, Callable
from unittest.mock import MagicMock, patch, Mock
from abc import ABC

# Import Smart Fixture System
from tests.fixtures import (
    smart_fixture, factory_fixture, preset_fixture,
    smart_fixture_manager, performance_monitor, cleanup_manager,
    FixtureScope, get_system_health
)

# Import base test infrastructure
from .test_base import TestBase
from .config import TestConfig


class BaseUnitTest(TestBase):
    """
    Generic base class for unit testing with automatic dependency management

    This is the most generic unit testing base class that can be used for testing
    any component (services, repositories, controllers, models, utilities) with
    automatic mocking and Smart Fixture integration.

    Features:
    - Zero setup boilerplate - just specify dependencies
    - Automatic dependency mocking (services, repositories, external APIs)
    - Smart Fixture integration for test data generation
    - Performance monitoring with lightweight thresholds
    - Generic test utilities for common patterns
    - Flexible component testing (any class type)

    Usage:
    ```python
    class TestAnyComponent(BaseUnitTest):
        component_class = MyComponent
        dependencies = ['dependency1', 'dependency2']
        external_dependencies = ['external_api', 'email_service']

        def test_component_method(self):
            # Setup test data
            test_data = self.create_test_data()

            # Configure mock responses
            self.setup_mock_response('dependency1', 'method', 'expected_result')

            # Test component
            result = self.component.method(test_data)

            # Validate
            self.assert_result_valid(result)
            self.assert_mock_called('dependency1', 'method', test_data)
    ```
    """

    # Component configuration - override in subclasses
    component_class: Optional[Type] = None
    dependencies: List[str] = []
    external_dependencies: List[str] = []
    auto_patch_imports: bool = True  # Automatically patch component imports

    def setup_method(self, method):
        """Enhanced setup for generic unit testing"""
        super().setup_method(method)

        # Setup component instance with mocked dependencies
        self._setup_component_with_mocks()

        # Setup Smart Fixture integration
        self._setup_smart_fixture_integration()

        # Register generic test fixtures
        self._register_generic_test_fixtures()

        # Setup performance monitoring for unit operations
        self._setup_unit_performance_monitoring()

        self.log_test_info(f"Unit test setup complete: {self.component_class.__name__ if self.component_class else 'Generic'}")

    def teardown_method(self, method):
        """Enhanced teardown with Smart Fixture cleanup"""
        # Stop any patches
        self._stop_patches()

        # Cleanup Smart Fixtures for this test
        cleanup_manager.cleanup_fixture_scope('function')

        # Parent teardown
        super().teardown_method(method)

        # Log performance if enabled
        self._log_unit_performance()

    def _setup_component_with_mocks(self):
        """Setup component instance with automatically mocked dependencies"""
        if not self.component_class:
            self.log_test_debug("No component_class specified, creating generic mock component")
            self.component = MagicMock()
            return

        # Create component instance
        self.component = self.component_class()

        # Setup dependency mocks
        self.dependency_mocks = {}
        self.patches = []

        for dep_name in self.dependencies:
            mock_dep = self._create_dependency_mock(dep_name)
            self.dependency_mocks[dep_name] = mock_dep

            # Inject dependency into component
            setattr(self.component, dep_name, mock_dep)

        # Setup external dependency mocks with patching
        self.external_mocks = {}
        for ext_dep in self.external_dependencies:
            mock_ext = self._create_external_mock(ext_dep)
            self.external_mocks[ext_dep] = mock_ext

        self.log_test_debug(f"Component setup complete: {len(self.dependency_mocks)} deps, {len(self.external_mocks)} external")

    def _create_dependency_mock(self, dep_name: str) -> MagicMock:
        """Create a mock for an internal dependency"""
        mock_dep = MagicMock(name=f"mock_{dep_name}")

        # Setup common method defaults based on dependency type
        if 'repository' in dep_name.lower():
            # Repository-like methods
            mock_dep.find_by_id.return_value = None
            mock_dep.find_one.return_value = None
            mock_dep.find_many.return_value = []
            mock_dep.create.return_value = "test_id_123"
            mock_dep.update_by_id.return_value = True
            mock_dep.delete_by_id.return_value = True
            mock_dep.count.return_value = 0

        elif 'service' in dep_name.lower():
            # Service-like methods
            mock_dep.create.return_value = (True, "Created successfully", {"id": "test_123"})
            mock_dep.get.return_value = (True, "Retrieved successfully", {"data": "test"})
            mock_dep.update.return_value = (True, "Updated successfully", {"id": "test_123"})
            mock_dep.delete.return_value = (True, "Deleted successfully", None)

        elif 'client' in dep_name.lower():
            # Client-like methods
            mock_dep.get.return_value = {"status": "success", "data": {}}
            mock_dep.post.return_value = {"status": "success", "id": "test_123"}
            mock_dep.put.return_value = {"status": "success"}
            mock_dep.delete.return_value = {"status": "success"}

        return mock_dep

    def _create_external_mock(self, ext_name: str) -> MagicMock:
        """Create a mock for an external dependency with patching"""
        mock_ext = MagicMock(name=f"mock_{ext_name}")

        if self.auto_patch_imports:
            # Determine patch path
            patch_paths = self._get_patch_paths(ext_name)

            for patch_path in patch_paths:
                try:
                    patcher = patch(patch_path, mock_ext)
                    patcher.start()
                    self.patches.append(patcher)
                    self.log_test_debug(f"Patched {patch_path}")
                    break  # Success - use first working path
                except ImportError:
                    continue  # Try next path

        # Setup common external service methods
        if 'email' in ext_name.lower():
            mock_ext.send.return_value = True
            mock_ext.send_email.return_value = True

        elif 'payment' in ext_name.lower():
            mock_ext.charge.return_value = {"success": True, "transaction_id": "tx_123"}
            mock_ext.refund.return_value = {"success": True, "refund_id": "ref_123"}

        elif 'api' in ext_name.lower():
            mock_ext.get.return_value = {"status": 200, "data": {}}
            mock_ext.post.return_value = {"status": 201, "id": "api_123"}

        return mock_ext

    def _get_patch_paths(self, ext_name: str) -> List[str]:
        """Get possible patch paths for external dependency"""
        # Common external service patch paths
        patch_patterns = [
            f"app.core.services.{ext_name}",
            f"app.{ext_name}",
            f"{ext_name}",
            f"app.external.{ext_name}",
            f"app.integrations.{ext_name}"
        ]
        return patch_patterns

    def _setup_smart_fixture_integration(self):
        """Initialize Smart Fixture system for unit testing"""
        if not hasattr(self, '_smart_fixtures_registered'):
            self._smart_fixtures_registered = True

    def _register_generic_test_fixtures(self):
        """Register generic fixtures for unit testing"""

        @smart_fixture('test_data', scope=FixtureScope.FUNCTION)
        def test_data():
            return {
                'id': 'test_123',
                'name': 'Test Item',
                'value': 42,
                'active': True,
                'tags': ['test', 'unit'],
                'metadata': {'created_by': 'test', 'version': '1.0'}
            }

        @smart_fixture('test_user_data', scope=FixtureScope.FUNCTION)
        def test_user_data():
            return {
                'id': 'user_123',
                'email': 'test@example.com',
                'username': 'testuser',
                'first_name': 'Test',
                'last_name': 'User',
                'role': 'user',
                'active': True
            }

        @smart_fixture('test_api_response', scope=FixtureScope.FUNCTION)
        def test_api_response():
            return {
                'status': 'success',
                'data': {'id': 'api_123', 'result': 'test_result'},
                'message': 'Operation completed successfully',
                'timestamp': '2023-01-01T00:00:00Z'
            }

        @smart_fixture('test_error_response', scope=FixtureScope.FUNCTION)
        def test_error_response():
            return {
                'status': 'error',
                'error': {'code': 'TEST_ERROR', 'message': 'Test error occurred'},
                'details': 'This is a test error for unit testing'
            }

    def _setup_unit_performance_monitoring(self):
        """Setup performance monitoring for unit operations"""
        self.unit_operation_timings = {}
        self.performance_thresholds = {
            'max_operation_time_ms': 50.0,   # Unit tests should be very fast
            'max_memory_increase_mb': 5.0,   # Minimal memory usage
            'max_setup_time_ms': 10.0        # Fast setup
        }

    def _stop_patches(self):
        """Stop all active patches"""
        for patcher in getattr(self, 'patches', []):
            patcher.stop()

    def _log_unit_performance(self):
        """Log unit performance metrics"""
        if hasattr(self, 'unit_operation_timings') and self.unit_operation_timings:
            self.log_test_debug("Unit operation timings:", self.unit_operation_timings)

    # Generic Test Data Creation Methods

    def create_test_data(self, **overrides) -> Dict[str, Any]:
        """Create generic test data using Smart Fixtures"""
        test_data = smart_fixture_manager.create_fixture('test_data')
        if overrides:
            test_data.update(overrides)
        return test_data

    def create_test_user_data(self, **overrides) -> Dict[str, Any]:
        """Create test user data using Smart Fixtures"""
        user_data = smart_fixture_manager.create_fixture('test_user_data')
        if overrides:
            user_data.update(overrides)
        return user_data

    def create_test_api_response(self, **overrides) -> Dict[str, Any]:
        """Create test API response using Smart Fixtures"""
        api_response = smart_fixture_manager.create_fixture('test_api_response')
        if overrides:
            api_response.update(overrides)
        return api_response

    def create_test_error_response(self, **overrides) -> Dict[str, Any]:
        """Create test error response using Smart Fixtures"""
        error_response = smart_fixture_manager.create_fixture('test_error_response')
        if overrides:
            error_response.update(overrides)
        return error_response

    # Generic Mock Configuration Methods

    def setup_mock_response(self, mock_name: str, method_name: str, return_value: Any):
        """Setup a mock method response for any dependency"""
        mock_obj = None

        if mock_name in self.dependency_mocks:
            mock_obj = self.dependency_mocks[mock_name]
        elif mock_name in self.external_mocks:
            mock_obj = self.external_mocks[mock_name]
        else:
            raise ValueError(f"Mock '{mock_name}' not found. Available: {list(self.dependency_mocks.keys()) + list(self.external_mocks.keys())}")

        getattr(mock_obj, method_name).return_value = return_value
        self.log_test_debug(f"Setup {mock_name}.{method_name} mock response")

    def setup_mock_side_effect(self, mock_name: str, method_name: str, side_effect: Any):
        """Setup a mock method side effect for any dependency"""
        mock_obj = None

        if mock_name in self.dependency_mocks:
            mock_obj = self.dependency_mocks[mock_name]
        elif mock_name in self.external_mocks:
            mock_obj = self.external_mocks[mock_name]
        else:
            raise ValueError(f"Mock '{mock_name}' not found")

        getattr(mock_obj, method_name).side_effect = side_effect
        self.log_test_debug(f"Setup {mock_name}.{method_name} side effect")

    def reset_mock(self, mock_name: str):
        """Reset all calls on a specific mock"""
        if mock_name in self.dependency_mocks:
            self.dependency_mocks[mock_name].reset_mock()
        elif mock_name in self.external_mocks:
            self.external_mocks[mock_name].reset_mock()
        else:
            raise ValueError(f"Mock '{mock_name}' not found")

    def reset_all_mocks(self):
        """Reset all mocks"""
        for mock_obj in self.dependency_mocks.values():
            mock_obj.reset_mock()
        for mock_obj in self.external_mocks.values():
            mock_obj.reset_mock()

    # Generic Assertion Methods

    def assert_mock_called(self, mock_name: str, method_name: str, *args, **kwargs):
        """Assert that a mock method was called with specific arguments"""
        mock_obj = None

        if mock_name in self.dependency_mocks:
            mock_obj = self.dependency_mocks[mock_name]
        elif mock_name in self.external_mocks:
            mock_obj = self.external_mocks[mock_name]
        else:
            raise AssertionError(f"Mock '{mock_name}' not found")

        method_mock = getattr(mock_obj, method_name)

        if args or kwargs:
            method_mock.assert_called_with(*args, **kwargs)
        else:
            method_mock.assert_called()

        self.log_test_debug(f"Verified {mock_name}.{method_name} was called")

    def assert_mock_not_called(self, mock_name: str, method_name: str):
        """Assert that a mock method was not called"""
        mock_obj = None

        if mock_name in self.dependency_mocks:
            mock_obj = self.dependency_mocks[mock_name]
        elif mock_name in self.external_mocks:
            mock_obj = self.external_mocks[mock_name]
        else:
            raise AssertionError(f"Mock '{mock_name}' not found")

        method_mock = getattr(mock_obj, method_name)
        method_mock.assert_not_called()

        self.log_test_debug(f"Verified {mock_name}.{method_name} was not called")

    def assert_mock_call_count(self, mock_name: str, method_name: str, expected_count: int):
        """Assert that a mock method was called specific number of times"""
        mock_obj = None

        if mock_name in self.dependency_mocks:
            mock_obj = self.dependency_mocks[mock_name]
        elif mock_name in self.external_mocks:
            mock_obj = self.external_mocks[mock_name]
        else:
            raise AssertionError(f"Mock '{mock_name}' not found")

        method_mock = getattr(mock_obj, method_name)
        actual_count = method_mock.call_count

        assert actual_count == expected_count, \
            f"Expected {mock_name}.{method_name} to be called {expected_count} times, but was called {actual_count} times"

        self.log_test_debug(f"Verified {mock_name}.{method_name} call count: {actual_count}")

    def get_mock_call_args(self, mock_name: str, method_name: str, call_index: int = -1) -> tuple:
        """Get the arguments from a specific mock call"""
        mock_obj = None

        if mock_name in self.dependency_mocks:
            mock_obj = self.dependency_mocks[mock_name]
        elif mock_name in self.external_mocks:
            mock_obj = self.external_mocks[mock_name]
        else:
            raise ValueError(f"Mock '{mock_name}' not found")

        method_mock = getattr(mock_obj, method_name)

        if not method_mock.call_args_list:
            raise AssertionError(f"{mock_name}.{method_name} was never called")

        return method_mock.call_args_list[call_index]

    # Generic Result Validation Methods

    def assert_result_valid(self, result: Any, expected_type: Type = None):
        """Assert that a result is valid (not None and optionally of expected type)"""
        assert result is not None, "Expected valid result, got None"

        if expected_type:
            assert isinstance(result, expected_type), \
                f"Expected result of type {expected_type.__name__}, got {type(result).__name__}"

        self.log_test_debug(f"Result validation passed: {type(result).__name__}")

    def assert_result_equals(self, result: Any, expected: Any):
        """Assert that result equals expected value"""
        assert result == expected, f"Expected {expected}, got {result}"

    def assert_result_contains(self, result: Dict[str, Any], key: str, expected_value: Any = None):
        """Assert that result contains specific key and optionally specific value"""
        assert isinstance(result, dict), f"Expected dict result, got {type(result)}"
        assert key in result, f"Expected key '{key}' in result"

        if expected_value is not None:
            assert result[key] == expected_value, \
                f"Expected {key}='{expected_value}', got '{result[key]}'"

    def assert_result_has_keys(self, result: Dict[str, Any], required_keys: List[str]):
        """Assert that result has all required keys"""
        assert isinstance(result, dict), f"Expected dict result, got {type(result)}"

        for key in required_keys:
            assert key in result, f"Expected key '{key}' in result"

    # Performance Testing Methods

    def assert_operation_performance(self, operation_func: Callable, max_time_ms: float = None, *args, **kwargs):
        """Assert that an operation completes within performance thresholds"""
        max_time = max_time_ms or self.performance_thresholds['max_operation_time_ms']

        start_time = time.time()
        result = operation_func(*args, **kwargs)
        execution_time_ms = (time.time() - start_time) * 1000

        assert execution_time_ms <= max_time, \
            f"Operation took {execution_time_ms:.1f}ms, expected under {max_time}ms"

        # Track timing for reporting
        operation_name = operation_func.__name__ if hasattr(operation_func, '__name__') else str(operation_func)
        self.unit_operation_timings[operation_name] = execution_time_ms

        self.log_test_debug(f"Performance assertion passed: {operation_name} took {execution_time_ms:.1f}ms")
        return result

    # Exception Testing Methods

    def assert_raises_with_message(self, exception_class: Type[Exception], expected_message: str, operation_func: Callable, *args, **kwargs):
        """Assert that operation raises specific exception with expected message"""
        with pytest.raises(exception_class) as exc_info:
            operation_func(*args, **kwargs)

        assert expected_message in str(exc_info.value), \
            f"Expected exception message to contain '{expected_message}', got '{str(exc_info.value)}'"

        self.log_test_debug(f"Exception assertion passed: {exception_class.__name__}")

    def assert_no_exception(self, operation_func: Callable, *args, **kwargs):
        """Assert that operation completes without raising any exception"""
        try:
            result = operation_func(*args, **kwargs)
            self.log_test_debug("No exception assertion passed")
            return result
        except Exception as e:
            pytest.fail(f"Expected no exception, but {type(e).__name__} was raised: {str(e)}")

    # Smart Fixture Integration Methods

    def get_smart_fixture_performance_report(self) -> Dict[str, Any]:
        """Get Smart Fixture performance report for this test"""
        return performance_monitor.get_performance_report()

    def assert_smart_fixture_performance(self):
        """Assert that Smart Fixture performance meets thresholds"""
        report = self.get_smart_fixture_performance_report()

        # Check cache hit ratio (relaxed for unit tests)
        cache_hit_ratio = report.get('overall_cache_hit_ratio', 0.0)
        if report.get('cache_hits', 0) + report.get('cache_misses', 0) > 0:
            assert cache_hit_ratio >= 0.3, \
                f"Smart Fixture cache hit ratio {cache_hit_ratio:.1%} is below 30%"

        self.log_test_debug(f"Smart Fixture performance check passed - Cache: {cache_hit_ratio:.1%}")

    def get_system_health_report(self) -> Dict[str, Any]:
        """Get system health report including Smart Fixtures"""
        return get_system_health()

    # Component Testing Utilities

    @pytest.mark.skip("Template test - not meant to be run directly")
    def test_component_initialization(self):
        """Generic test for component initialization"""
        if not self.component_class:
            pytest.skip("No component_class specified")

        assert self.component is not None, "Component should be initialized"
        assert isinstance(self.component, self.component_class), \
            f"Component should be instance of {self.component_class.__name__}"

        self.log_test_debug("Component initialization test passed")

    @pytest.mark.skip("Template test - not meant to be run directly")
    def test_component_has_required_methods(self, required_methods: List[str]):
        """Test that component has all required methods"""
        if not self.component:
            pytest.skip("No component available")

        for method_name in required_methods:
            assert hasattr(self.component, method_name), \
                f"Component should have method '{method_name}'"
            assert callable(getattr(self.component, method_name)), \
                f"Component method '{method_name}' should be callable"

        self.log_test_debug(f"Component method requirements test passed: {required_methods}")

    @pytest.mark.skip("Template test - not meant to be run directly")
    def test_component_dependencies_injected(self):
        """Test that all configured dependencies are properly injected"""
        if not self.component or not self.dependencies:
            pytest.skip("No component or dependencies to test")

        for dep_name in self.dependencies:
            assert hasattr(self.component, dep_name), \
                f"Component should have dependency '{dep_name}' injected"

            dependency = getattr(self.component, dep_name)
            assert dependency is not None, f"Dependency '{dep_name}' should not be None"

        self.log_test_debug(f"Dependency injection test passed: {self.dependencies}")


class UnitTestMixin:
    """
    Mixin class providing additional utilities for unit testing
    Can be used with existing test classes that can't extend BaseUnitTest
    """

    def setup_generic_mocks(self, component, dependencies: List[str]):
        """Setup generic mocks for a component"""
        mocks = {}
        for dep_name in dependencies:
            mock_dep = MagicMock(name=f"mock_{dep_name}")
            mocks[dep_name] = mock_dep
            setattr(component, dep_name, mock_dep)
        return mocks

    def assert_generic_result_valid(self, result: Any):
        """Generic result validation"""
        assert result is not None, "Result should not be None"
        return result

    def time_operation(self, operation_func: Callable, *args, **kwargs) -> tuple:
        """Time an operation and return (result, duration_ms)"""
        start_time = time.time()
        result = operation_func(*args, **kwargs)
        duration_ms = (time.time() - start_time) * 1000
        return result, duration_ms