"""
Base Test Class Module

Provides base test class with common setup, teardown, utilities and
performance monitoring for all GoodPlay tests.
"""
import pytest
import time
import logging
from abc import ABC
from typing import Optional, Dict, Any, Type
from unittest.mock import MagicMock, patch

from .config import TestConfig, get_test_config
from .utils import TestUtils


class TestBase(ABC):
    """
    Base test class for all GoodPlay tests.

    Provides common functionality including:
    - Test configuration management
    - Database setup and teardown
    - Performance monitoring
    - Mock management
    - Logging configuration
    - Common assertions and utilities
    """

    # Class-level configuration
    test_config: TestConfig = None
    test_utils: TestUtils = None

    @classmethod
    def setup_class(cls):
        """Setup for the entire test class"""
        cls.test_config = get_test_config()
        cls.test_utils = TestUtils(cls.test_config)

        # Reset performance tracking
        cls.test_config.reset_performance_tracking()

    @classmethod
    def teardown_class(cls):
        """Teardown for the entire test class"""
        # Report slow tests if any
        slow_tests = cls.test_config.get_slow_tests()
        if slow_tests:
            print(f"\n[PERFORMANCE] Slow tests in {cls.__name__}:")
            for test_name, duration in slow_tests.items():
                print(f"  - {test_name}: {duration:.2f}s")

    def setup_method(self, method):
        """Setup for each test method"""
        self.test_name = f"{self.__class__.__name__}::{method.__name__}"

        # Start performance timing
        self.test_config.start_test_timing(self.test_name)

        # Setup logging for this test
        self.logger = logging.getLogger(self.test_name)

        # Reset database state if configured
        if self.test_config.database.reset_between_tests:
            self._reset_database_state()

    def teardown_method(self, method):
        """Teardown for each test method"""
        # End performance timing
        duration = self.test_config.end_test_timing(self.test_name)

        # Log if test was slow
        if duration > self.test_config.performance.slow_test_threshold:
            self.logger.warning(f"Slow test detected: {duration:.2f}s")

    def _reset_database_state(self):
        """Reset database state between tests"""
        # This will be enhanced when we implement actual database reset logic
        pass

    # Common Assertions

    def assert_success_response(self, response: Dict[str, Any], expected_message: str = None):
        """Assert that a response indicates success"""
        assert response.get('success') is True, f"Expected success response, got: {response}"
        if expected_message:
            assert response.get('message') == expected_message

    def assert_error_response(self, response: Dict[str, Any], expected_message: str = None, expected_code: int = None):
        """Assert that a response indicates an error"""
        assert response.get('success') is False, f"Expected error response, got: {response}"
        if expected_message:
            assert response.get('message') == expected_message
        if expected_code:
            assert response.get('code') == expected_code

    def assert_api_response_status(self, response, expected_status: int):
        """Assert API response has expected status code"""
        assert response.status_code == expected_status, \
            f"Expected status {expected_status}, got {response.status_code}: {response.get_json()}"

    def assert_api_success(self, response, expected_message: str = None):
        """Assert API response is successful"""
        self.assert_api_response_status(response, 200)
        data = response.get_json()
        self.assert_success_response(data, expected_message)

    def assert_api_error(self, response, expected_status: int, expected_message: str = None):
        """Assert API response is an error"""
        self.assert_api_response_status(response, expected_status)
        data = response.get_json()
        self.assert_error_response(data, expected_message)

    # Mock Management

    def create_mock_user(self, **overrides) -> Dict[str, Any]:
        """Create a mock user with default values"""
        return self.test_utils.create_mock_user(**overrides)

    def create_mock_db_response(self, data: Any = None, count: int = 0) -> MagicMock:
        """Create a mock database response"""
        return self.test_utils.create_mock_db_response(data, count)

    def setup_auth_mock(self, user_id: str = "test_user_id") -> MagicMock:
        """Setup authentication mock for protected endpoints"""
        return self.test_utils.setup_auth_mock(user_id)

    # Configuration Override

    def override_config(self, **kwargs) -> TestConfig:
        """Create a test config with overridden values for this test"""
        return self.test_config.override(**kwargs)

    def use_config(self, config: TestConfig):
        """Use a different configuration for this test"""
        self.test_config = config
        self.test_utils.config = config

    # Performance Testing

    def measure_execution_time(self, func, *args, **kwargs) -> tuple:
        """Measure execution time of a function"""
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time = time.time() - start_time
        return result, execution_time

    def assert_execution_time_under(self, func, max_time: float, *args, **kwargs):
        """Assert that function executes under specified time"""
        result, execution_time = self.measure_execution_time(func, *args, **kwargs)
        assert execution_time <= max_time, \
            f"Function took {execution_time:.3f}s, expected under {max_time}s"
        return result

    # Database Testing Utilities

    def mock_collection_find_one(self, collection_mock: MagicMock, return_value: Any = None):
        """Mock collection find_one method"""
        collection_mock.find_one.return_value = return_value
        return collection_mock

    def mock_collection_insert_one(self, collection_mock: MagicMock, inserted_id: str = "test_id"):
        """Mock collection insert_one method"""
        mock_result = MagicMock()
        mock_result.inserted_id = inserted_id
        collection_mock.insert_one.return_value = mock_result
        return collection_mock

    def mock_collection_update_one(self, collection_mock: MagicMock, modified_count: int = 1):
        """Mock collection update_one method"""
        mock_result = MagicMock()
        mock_result.modified_count = modified_count
        collection_mock.update_one.return_value = mock_result
        return collection_mock

    def mock_collection_delete_one(self, collection_mock: MagicMock, deleted_count: int = 1):
        """Mock collection delete_one method"""
        mock_result = MagicMock()
        mock_result.deleted_count = deleted_count
        collection_mock.delete_one.return_value = mock_result
        return collection_mock

    # Logging Utilities

    def log_test_info(self, message: str):
        """Log test information"""
        self.logger.info(f"[{self.test_name}] {message}")

    def log_test_debug(self, message: str, data: Any = None):
        """Log test debug information"""
        if data:
            self.logger.debug(f"[{self.test_name}] {message}: {data}")
        else:
            self.logger.debug(f"[{self.test_name}] {message}")


class UnitTestBase(TestBase):
    """Base class for unit tests with enhanced mocking"""

    def setup_method(self, method):
        super().setup_method(method)
        # Enhanced setup for unit tests
        self._setup_unit_test_mocks()

    def _setup_unit_test_mocks(self):
        """Setup common mocks for unit tests"""
        # Mock database by default for unit tests
        self.mock_db = self.test_config.create_mock_db()


class IntegrationTestBase(TestBase):
    """Base class for integration tests with minimal mocking"""

    def setup_method(self, method):
        super().setup_method(method)
        # Minimal mocking for integration tests
        self._setup_integration_test_environment()

    def _setup_integration_test_environment(self):
        """Setup environment for integration tests"""
        # Only mock external services, keep internal logic intact
        pass


class ApiTestBase(TestBase):
    """Base class for API endpoint tests"""

    def setup_method(self, method):
        super().setup_method(method)
        # Setup for API testing
        self._setup_api_test_environment()

    def _setup_api_test_environment(self):
        """Setup environment for API tests"""
        # Mock authentication and external services
        self.auth_headers = {
            'Authorization': 'Bearer test-token',
            'Content-Type': 'application/json'
        }