"""
Test Configuration Module

Centralized configuration management for the GoodPlay test suite.
Provides environment-specific settings, database isolation, and performance monitoring.
"""
import os
import time
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from unittest.mock import MagicMock


@dataclass
class DatabaseConfig:
    """Database configuration for testing"""
    test_uri: str = 'mongodb://localhost:27017/goodplay_test'
    isolation_mode: str = 'collection'  # 'collection' or 'transaction'
    mock_enabled: bool = True
    reset_between_tests: bool = True


@dataclass
class PerformanceConfig:
    """Performance monitoring configuration"""
    enable_timing: bool = True
    slow_test_threshold: float = 1.0  # seconds
    memory_monitoring: bool = False
    max_test_duration: float = 300.0  # 5 minutes
    report_slowest_count: int = 10


@dataclass
class LoggingConfig:
    """Logging configuration for tests"""
    level: str = 'ERROR'
    enable_test_logs: bool = False
    capture_warnings: bool = True
    structured_logging: bool = True
    log_database_queries: bool = False


@dataclass
class MockConfig:
    """Mock service configurations"""
    auto_mock_external: bool = True
    mock_jwt_tokens: bool = True
    mock_bcrypt: bool = True
    mock_email_service: bool = True
    mock_payment_service: bool = True


@dataclass
class GOO35Config:
    """Configuration for GOO-35 Testing Utilities integration"""
    enable_smart_fixtures: bool = True
    enable_factory_boy_integration: bool = True
    auto_use_builders: bool = True
    builder_factory_threshold: int = 5  # Use Factory-Boy for batch > 5
    cache_builder_results: bool = True
    performance_monitoring: bool = True
    goo35_test_threshold: float = 0.5  # seconds - GOO-35 tests should be faster


class TestConfig:
    """
    Centralized test configuration management.

    Provides configuration for database isolation, performance monitoring,
    logging, and mock services. Can be overridden per test or test module.
    """

    def __init__(self, environment: str = 'testing'):
        self.environment = environment
        self.database = DatabaseConfig()
        self.performance = PerformanceConfig()
        self.logging = LoggingConfig()
        self.mocks = MockConfig()
        self.goo35 = GOO35Config()

        # Performance tracking
        self._test_start_time: Optional[float] = None
        self._slow_tests: Dict[str, float] = {}
        self._goo35_stats: Dict[str, Any] = {
            'tests_using_goo35': 0,
            'builder_factory_usage': 0,
            'smart_fixture_hits': 0
        }

        # Environment setup
        self._setup_environment()
        self._setup_logging()
        self._setup_goo35_integration()

    def _setup_environment(self):
        """Setup test environment variables"""
        test_env = {
            'TESTING': 'true',
            'FLASK_ENV': 'testing',
            'MONGO_URI': self.database.test_uri,
            'JWT_SECRET_KEY': 'test-jwt-secret-key-for-testing',
            'SECRET_KEY': 'test-secret-key-for-testing',
            'LOG_LEVEL': self.logging.level,
            'CORS_ORIGINS': 'http://localhost:3000,http://127.0.0.1:3000'
        }

        for key, value in test_env.items():
            os.environ.setdefault(key, value)

    def _setup_logging(self):
        """Setup logging configuration for tests"""
        if self.logging.enable_test_logs:
            logging.basicConfig(
                level=getattr(logging, self.logging.level.upper()),
                format='[TEST] %(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )

        if self.logging.capture_warnings:
            logging.captureWarnings(True)

    def _setup_goo35_integration(self):
        """Setup GOO-35 Testing Utilities integration"""
        if self.goo35.enable_smart_fixtures:
            # Set environment variable for Smart Fixtures
            os.environ.setdefault('GOO35_SMART_FIXTURES_ENABLED', 'true')

        if self.goo35.enable_factory_boy_integration:
            # Set environment variable for Factory-Boy integration
            os.environ.setdefault('GOO35_FACTORY_BOY_ENABLED', 'true')
            os.environ.setdefault('GOO35_FACTORY_THRESHOLD', str(self.goo35.builder_factory_threshold))

        if self.goo35.performance_monitoring:
            # Enable GOO-35 performance monitoring
            os.environ.setdefault('GOO35_PERFORMANCE_MONITORING', 'true')

    def start_test_timing(self, test_name: str, uses_goo35_utilities: bool = False):
        """Start timing a test"""
        if self.performance.enable_timing:
            self._test_start_time = time.time()

        if uses_goo35_utilities:
            self._goo35_stats['tests_using_goo35'] += 1

    def end_test_timing(self, test_name: str) -> float:
        """End timing a test and record if slow"""
        if not self.performance.enable_timing or self._test_start_time is None:
            return 0.0

        duration = time.time() - self._test_start_time

        if duration > self.performance.slow_test_threshold:
            self._slow_tests[test_name] = duration

        self._test_start_time = None
        return duration

    def get_slow_tests(self) -> Dict[str, float]:
        """Get dictionary of slow tests and their durations"""
        return dict(sorted(
            self._slow_tests.items(),
            key=lambda x: x[1],
            reverse=True
        )[:self.performance.report_slowest_count])

    def create_mock_db(self) -> MagicMock:
        """Create a mock database instance"""
        mock_collection = MagicMock()
        mock_db = MagicMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)

        # Configure common database operations
        mock_collection.find_one.return_value = None
        mock_collection.find.return_value = []
        mock_collection.insert_one.return_value = MagicMock(inserted_id="test_id")
        mock_collection.update_one.return_value = MagicMock(modified_count=1)
        mock_collection.delete_one.return_value = MagicMock(deleted_count=1)
        mock_collection.count_documents.return_value = 0
        mock_collection.create_index.return_value = None

        return mock_db

    def get_test_database_uri(self) -> str:
        """Get the test database URI"""
        return self.database.test_uri

    def should_mock_service(self, service_name: str) -> bool:
        """Check if a service should be mocked"""
        mock_mapping = {
            'jwt': self.mocks.mock_jwt_tokens,
            'bcrypt': self.mocks.mock_bcrypt,
            'email': self.mocks.mock_email_service,
            'payment': self.mocks.mock_payment_service
        }
        return mock_mapping.get(service_name, self.mocks.auto_mock_external)

    def override(self, **kwargs) -> 'TestConfig':
        """
        Create a new TestConfig instance with overridden values.

        Args:
            **kwargs: Configuration values to override

        Returns:
            New TestConfig instance with overridden values
        """
        new_config = TestConfig(self.environment)

        # Override database config
        if 'database' in kwargs:
            for key, value in kwargs['database'].items():
                setattr(new_config.database, key, value)

        # Override performance config
        if 'performance' in kwargs:
            for key, value in kwargs['performance'].items():
                setattr(new_config.performance, key, value)

        # Override logging config
        if 'logging' in kwargs:
            for key, value in kwargs['logging'].items():
                setattr(new_config.logging, key, value)

        # Override mock config
        if 'mocks' in kwargs:
            for key, value in kwargs['mocks'].items():
                setattr(new_config.mocks, key, value)

        return new_config

    def reset_performance_tracking(self):
        """Reset performance tracking data"""
        self._slow_tests.clear()
        self._test_start_time = None

    def get_flask_config(self) -> Dict[str, Any]:
        """Get Flask application configuration for testing"""
        return {
            'TESTING': True,
            'MONGO_URI': self.database.test_uri,
            'JWT_SECRET_KEY': os.environ.get('JWT_SECRET_KEY'),
            'SECRET_KEY': os.environ.get('SECRET_KEY'),
            'WTF_CSRF_ENABLED': False,
            'LOGIN_DISABLED': False
        }

    def record_builder_factory_usage(self):
        """Record that Factory-Boy was used with builders"""
        self._goo35_stats['builder_factory_usage'] += 1

    def record_smart_fixture_hit(self):
        """Record a Smart Fixture cache hit"""
        self._goo35_stats['smart_fixture_hits'] += 1

    def get_goo35_statistics(self) -> Dict[str, Any]:
        """Get GOO-35 usage statistics"""
        return {
            **self._goo35_stats,
            'goo35_config': {
                'smart_fixtures_enabled': self.goo35.enable_smart_fixtures,
                'factory_boy_enabled': self.goo35.enable_factory_boy_integration,
                'auto_builders': self.goo35.auto_use_builders,
                'factory_threshold': self.goo35.builder_factory_threshold
            }
        }

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary including GOO-35 metrics"""
        base_summary = {
            'slow_tests': self.get_slow_tests(),
            'performance_config': {
                'slow_test_threshold': self.performance.slow_test_threshold,
                'goo35_test_threshold': self.goo35.goo35_test_threshold
            }
        }

        if self.goo35.performance_monitoring:
            base_summary['goo35_stats'] = self.get_goo35_statistics()

        return base_summary

    def is_goo35_enabled(self, feature: str) -> bool:
        """Check if a specific GOO-35 feature is enabled"""
        feature_mapping = {
            'smart_fixtures': self.goo35.enable_smart_fixtures,
            'factory_boy': self.goo35.enable_factory_boy_integration,
            'builders': self.goo35.auto_use_builders,
            'performance': self.goo35.performance_monitoring,
            'caching': self.goo35.cache_builder_results
        }
        return feature_mapping.get(feature, False)


# Global test configuration instance
default_test_config = TestConfig()


def get_test_config(environment: str = 'testing') -> TestConfig:
    """
    Get test configuration instance.

    Args:
        environment: Testing environment name

    Returns:
        TestConfig instance
    """
    if environment == 'testing':
        return default_test_config
    return TestConfig(environment)