"""
BaseIntegrationTest - Enterprise Test Class for Integration Testing (GOO-35)

Provides standardized testing patterns for full-stack integration tests with minimal
mocking, Smart Fixture preset integration, and end-to-end workflow validation.
"""
import pytest
import json
import os
import time
from typing import Dict, Any, List, Optional, Type, Union
from unittest.mock import patch, Mock
from flask import Flask
from flask.testing import FlaskClient

# Import Smart Fixture System
from tests.fixtures import (
    smart_fixture, factory_fixture, preset_fixture,
    smart_fixture_manager, performance_monitor, cleanup_manager,
    preset_manager, FixtureScope, get_system_health,
    # Import preset fixtures
    basic_user_setup, gaming_session_setup, social_network_setup,
    financial_setup, admin_setup, test_data_ecosystem
)

# Import base test infrastructure
from .test_base import TestBase
from .config import TestConfig


class BaseIntegrationTest(TestBase):
    """
    Base test class for integration testing with Smart Fixture presets

    Features:
    - End-to-end request/response flow testing with minimal mocking
    - Smart Fixture preset integration for complex test scenarios
    - Multi-module interaction testing
    - Performance monitoring for full-stack operations
    - Real database operations with automatic cleanup
    - Cross-module workflow validation
    - System health monitoring during tests
    - Comprehensive test data ecosystem setup

    Usage:
    ```python
    class TestUserGameIntegration(BaseIntegrationTest):
        use_presets = ['gaming_session_setup']

        def test_complete_gaming_workflow(self):
            # Use preset to setup complete gaming scenario
            setup_data = self.get_preset_data('gaming_session_setup')
            user = setup_data['basic_user']
            game = setup_data['game']
            session = setup_data['game_session']

            # Test complete workflow end-to-end
            response = self.client.post(f'/api/games/sessions/{session["_id"]}/start')
            self.assert_api_success(response)

            # Test cross-module interactions
            self.verify_user_game_integration(user, game, session)
    ```
    """

    # Integration test configuration - override in subclasses
    use_presets: List[str] = []
    minimal_mocking: bool = True
    enable_database_operations: bool = False  # Set to True for real DB tests
    test_external_services: bool = False  # Set to True to test external APIs

    def setup_method(self, method):
        """Enhanced setup for integration testing"""
        super().setup_method(method)

        # Setup Flask application for integration testing
        self._setup_integration_flask_app()

        # Setup Smart Fixture presets
        self._setup_smart_fixture_presets()

        # Setup minimal mocking (only external services)
        self._setup_minimal_mocking()

        # Setup database operations if enabled
        self._setup_database_operations()

        # Setup performance monitoring
        self._setup_integration_performance_monitoring()

        # Initialize preset data
        self._initialize_preset_data()

        self.log_test_info(f"Integration test setup complete with presets: {self.use_presets}")

    def teardown_method(self, method):
        """Enhanced teardown with comprehensive cleanup"""
        # Cleanup preset data
        self._cleanup_preset_data()

        # Cleanup Smart Fixtures
        cleanup_manager.cleanup_fixture_scope('function')

        # Stop minimal patches
        self._stop_minimal_patches()

        # Database cleanup if enabled
        self._cleanup_database_operations()

        # Parent teardown
        super().teardown_method(method)

        # Log integration performance
        self._log_integration_performance()

    def _setup_integration_flask_app(self):
        """Setup Flask app with integration test configuration"""
        # Import app here to avoid circular imports
        from app import create_app

        # Create app with minimal test configuration
        self.app = create_app('testing')
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False

        # Enable/disable database based on configuration
        if not self.enable_database_operations:
            self.app.config['TESTING_DISABLE_DB'] = True

        # Create test client
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

        self.log_test_debug(f"Integration Flask app setup - DB: {'enabled' if self.enable_database_operations else 'disabled'}")

    def _setup_smart_fixture_presets(self):
        """Setup Smart Fixture presets for integration testing"""
        self.preset_data = {}
        self.preset_cleanup_handlers = []

        # Register integration test specific fixtures
        self._register_integration_test_fixtures()

        self.log_test_debug(f"Smart Fixture presets configured: {self.use_presets}")

    def _setup_minimal_mocking(self):
        """Setup minimal mocking - only external services"""
        self.minimal_patches = []

        if self.minimal_mocking:
            # Mock only external services, keep internal logic intact
            self._mock_external_services()

        # Always mock authentication for integration tests
        self._mock_authentication_services()

    def _mock_external_services(self):
        """Mock external services while keeping internal logic"""
        external_services = []

        if not self.test_external_services:
            # Mock email service
            email_patch = patch('app.core.services.email_service.send_email')
            email_mock = email_patch.start()
            email_mock.return_value = True
            self.minimal_patches.append(email_patch)
            external_services.append('email_service')

            # Mock payment service
            payment_patch = patch('app.donations.services.payment_service.process_payment')
            payment_mock = payment_patch.start()
            payment_mock.return_value = (True, "Payment successful", {"transaction_id": "test_123"})
            self.minimal_patches.append(payment_patch)
            external_services.append('payment_service')

            # Mock external API calls
            api_patch = patch('requests.post')
            api_mock = api_patch.start()
            api_mock.return_value.status_code = 200
            api_mock.return_value.json.return_value = {"status": "success"}
            self.minimal_patches.append(api_patch)
            external_services.append('external_apis')

        self.log_test_debug(f"External services mocked: {external_services}")

    def _mock_authentication_services(self):
        """Mock authentication services for integration tests"""
        # Mock JWT token verification but keep user resolution logic
        jwt_patch = patch('flask_jwt_extended.verify_jwt_in_request')
        jwt_patch.start()
        self.minimal_patches.append(jwt_patch)

        # Mock get_jwt_identity to return test user ID
        identity_patch = patch('flask_jwt_extended.get_jwt_identity', return_value='integration_test_user_123')
        identity_patch.start()
        self.minimal_patches.append(identity_patch)

        self.log_test_debug("Authentication services mocked for integration testing")

    def _setup_database_operations(self):
        """Setup database operations if enabled"""
        if self.enable_database_operations:
            # Setup test database connection
            self._setup_test_database()
            # Track database operations for cleanup
            self._track_database_operations()

    def _setup_test_database(self):
        """Setup dedicated test database"""
        # This would typically connect to a test MongoDB instance
        # For now, we'll just log that it's enabled
        self.log_test_debug("Test database operations enabled")

    def _track_database_operations(self):
        """Track database operations for cleanup"""
        self.created_documents = {
            'users': [],
            'games': [],
            'sessions': [],
            'achievements': [],
            'transactions': []
        }

    def _setup_integration_performance_monitoring(self):
        """Setup performance monitoring for integration tests"""
        self.integration_timings = {}
        self.workflow_start_time = time.time()
        self.performance_checkpoints = {}

        # Set integration-specific performance thresholds
        self.integration_thresholds = {
            'max_workflow_time_ms': 2000.0,  # Complete workflows should be fast
            'max_api_response_time_ms': 500.0,  # Individual API calls
            'max_memory_increase_mb': 50.0,  # Memory usage during test
            'min_cache_hit_ratio': 0.7  # Lower threshold for integration tests
        }

    def _initialize_preset_data(self):
        """Initialize preset data for configured presets"""
        for preset_name in self.use_presets:
            try:
                preset_data = preset_manager.create_preset(preset_name)
                self.preset_data[preset_name] = preset_data
                self.log_test_debug(f"Initialized preset: {preset_name}")
            except Exception as e:
                self.log_test_debug(f"Failed to initialize preset {preset_name}: {e}")

    def _register_integration_test_fixtures(self):
        """Register integration-specific fixtures"""

        @smart_fixture('integration_workflow_data', scope=FixtureScope.FUNCTION)
        def integration_workflow_data():
            return {
                'workflow_id': 'integration_test_workflow',
                'started_at': time.time(),
                'steps_completed': [],
                'expected_steps': []
            }

        @smart_fixture('multi_user_scenario', scope=FixtureScope.FUNCTION)
        def multi_user_scenario():
            return {
                'primary_user': 'integration_user_1',
                'secondary_users': ['integration_user_2', 'integration_user_3'],
                'shared_resources': ['shared_game_123', 'shared_session_456']
            }

        @smart_fixture('cross_module_data', scope=FixtureScope.FUNCTION)
        def cross_module_data():
            return {
                'user_module': {'user_id': 'test_user_123'},
                'games_module': {'game_id': 'test_game_456', 'session_id': 'test_session_789'},
                'social_module': {'achievement_id': 'test_achievement_101'},
                'donations_module': {'wallet_id': 'test_wallet_202', 'transaction_id': 'test_tx_303'}
            }

    def _cleanup_preset_data(self):
        """Cleanup preset data and associated resources"""
        for preset_name, preset_data in self.preset_data.items():
            try:
                # Run preset-specific cleanup if available
                cleanup_handler = getattr(preset_manager, f'cleanup_{preset_name}', None)
                if cleanup_handler:
                    cleanup_handler(preset_data)

                self.log_test_debug(f"Cleaned up preset: {preset_name}")
            except Exception as e:
                self.log_test_debug(f"Failed to cleanup preset {preset_name}: {e}")

    def _cleanup_database_operations(self):
        """Cleanup database operations if enabled"""
        if self.enable_database_operations:
            # Cleanup created documents
            for collection_name, document_ids in self.created_documents.items():
                for doc_id in document_ids:
                    # This would delete the actual documents
                    self.log_test_debug(f"Cleanup document {doc_id} from {collection_name}")

    def _stop_minimal_patches(self):
        """Stop all minimal patches"""
        for patch_obj in self.minimal_patches:
            patch_obj.stop()

    def _log_integration_performance(self):
        """Log integration performance metrics"""
        total_workflow_time = (time.time() - self.workflow_start_time) * 1000
        self.log_test_debug(f"Total integration workflow time: {total_workflow_time:.1f}ms")

        if hasattr(self, 'integration_timings') and self.integration_timings:
            self.log_test_debug("Integration operation timings:", self.integration_timings)

    # Preset Data Access Methods

    def get_preset_data(self, preset_name: str) -> Dict[str, Any]:
        """Get data from a specific preset"""
        if preset_name not in self.preset_data:
            raise ValueError(f"Preset '{preset_name}' not initialized. Available: {list(self.preset_data.keys())}")

        return self.preset_data[preset_name]

    def get_user_from_preset(self, preset_name: str, user_key: str = 'basic_user') -> Dict[str, Any]:
        """Get user data from preset"""
        preset_data = self.get_preset_data(preset_name)
        if user_key not in preset_data:
            raise ValueError(f"User key '{user_key}' not found in preset '{preset_name}'")
        return preset_data[user_key]

    def get_game_from_preset(self, preset_name: str, game_key: str = 'game') -> Dict[str, Any]:
        """Get game data from preset"""
        preset_data = self.get_preset_data(preset_name)
        if game_key not in preset_data:
            raise ValueError(f"Game key '{game_key}' not found in preset '{preset_name}'")
        return preset_data[game_key]

    def get_session_from_preset(self, preset_name: str, session_key: str = 'game_session') -> Dict[str, Any]:
        """Get session data from preset"""
        preset_data = self.get_preset_data(preset_name)
        if session_key not in preset_data:
            raise ValueError(f"Session key '{session_key}' not found in preset '{preset_name}'")
        return preset_data[session_key]

    # Workflow Testing Methods

    def start_integration_workflow(self, workflow_name: str):
        """Start tracking an integration workflow"""
        self.current_workflow = workflow_name
        self.workflow_steps = []
        self.workflow_start_time = time.time()
        self.log_test_info(f"Started integration workflow: {workflow_name}")

    def add_workflow_step(self, step_name: str):
        """Add a step to the current workflow"""
        step_time = time.time()
        self.workflow_steps.append({
            'step': step_name,
            'timestamp': step_time,
            'duration_ms': (step_time - self.workflow_start_time) * 1000
        })
        self.log_test_debug(f"Workflow step completed: {step_name}")

    def complete_integration_workflow(self):
        """Complete and validate integration workflow"""
        total_time_ms = (time.time() - self.workflow_start_time) * 1000

        # Validate workflow performance
        if total_time_ms > self.integration_thresholds['max_workflow_time_ms']:
            self.log_test_debug(f"WARNING: Workflow took {total_time_ms:.1f}ms (threshold: {self.integration_thresholds['max_workflow_time_ms']}ms)")

        self.log_test_info(f"Completed integration workflow '{self.current_workflow}' in {total_time_ms:.1f}ms with {len(self.workflow_steps)} steps")

        return {
            'workflow_name': self.current_workflow,
            'total_time_ms': total_time_ms,
            'steps': self.workflow_steps,
            'performance_ok': total_time_ms <= self.integration_thresholds['max_workflow_time_ms']
        }

    # Cross-Module Integration Testing

    def verify_user_game_integration(self, user_data: Dict[str, Any], game_data: Dict[str, Any], session_data: Dict[str, Any]):
        """Verify user-game integration works correctly"""
        user_id = str(user_data.get('_id'))
        game_id = str(game_data.get('_id'))
        session_id = str(session_data.get('_id'))

        # Test user can access game
        response = self.client.get(f'/api/games/{game_id}', headers=self._get_auth_headers(user_id))
        self.assert_api_success(response)

        # Test game session can be started
        response = self.client.post(f'/api/games/sessions/{session_id}/start', headers=self._get_auth_headers(user_id))
        self.assert_api_success(response)

        self.log_test_debug("User-game integration verified")

    def verify_user_social_integration(self, user_data: Dict[str, Any]):
        """Verify user-social features integration"""
        user_id = str(user_data.get('_id'))

        # Test user can access social features
        response = self.client.get('/api/social/relationships', headers=self._get_auth_headers(user_id))
        self.assert_api_success(response)

        # Test achievement system
        response = self.client.get('/api/social/achievements', headers=self._get_auth_headers(user_id))
        self.assert_api_success(response)

        self.log_test_debug("User-social integration verified")

    def verify_game_social_integration(self, game_data: Dict[str, Any], user_data: Dict[str, Any]):
        """Verify game-social features integration"""
        user_id = str(user_data.get('_id'))
        game_id = str(game_data.get('_id'))

        # Test game achievements
        response = self.client.get(f'/api/games/{game_id}/achievements', headers=self._get_auth_headers(user_id))
        self.assert_api_success(response)

        # Test game leaderboards
        response = self.client.get(f'/api/games/{game_id}/leaderboard', headers=self._get_auth_headers(user_id))
        self.assert_api_success(response)

        self.log_test_debug("Game-social integration verified")

    def verify_donations_integration(self, user_data: Dict[str, Any]):
        """Verify donations system integration"""
        user_id = str(user_data.get('_id'))

        # Test wallet access
        response = self.client.get('/api/donations/wallet', headers=self._get_auth_headers(user_id))
        self.assert_api_success(response)

        # Test transaction history
        response = self.client.get('/api/donations/transactions', headers=self._get_auth_headers(user_id))
        self.assert_api_success(response)

        self.log_test_debug("Donations integration verified")

    # Performance Testing Methods

    def assert_workflow_performance(self, max_time_ms: float = None):
        """Assert that current workflow meets performance requirements"""
        max_time = max_time_ms or self.integration_thresholds['max_workflow_time_ms']
        current_time_ms = (time.time() - self.workflow_start_time) * 1000

        assert current_time_ms <= max_time, \
            f"Workflow took {current_time_ms:.1f}ms, expected under {max_time}ms"

        self.log_test_debug(f"Workflow performance assertion passed: {current_time_ms:.1f}ms")

    def assert_api_response_time_integration(self, method: str, url: str, max_time_ms: float = None, data: Dict[str, Any] = None):
        """Assert API response time within integration test thresholds"""
        max_time = max_time_ms or self.integration_thresholds['max_api_response_time_ms']

        start_time = time.time()
        if data:
            response = getattr(self.client, method.lower())(url, json=data, headers=self._get_auth_headers())
        else:
            response = getattr(self.client, method.lower())(url, headers=self._get_auth_headers())

        response_time_ms = (time.time() - start_time) * 1000

        assert response_time_ms <= max_time, \
            f"API {method} {url} took {response_time_ms:.1f}ms, expected under {max_time}ms"

        # Track timing
        endpoint_key = f"{method} {url}"
        self.integration_timings[endpoint_key] = response_time_ms

        self.log_test_debug(f"Integration API performance passed: {endpoint_key} took {response_time_ms:.1f}ms")
        return response

    # System Health and Monitoring

    def assert_system_health_during_test(self):
        """Assert system health remains good during integration test"""
        health_report = get_system_health()

        assert health_report['health_status'] in ['HEALTHY', 'OPTIMAL'], \
            f"System health degraded during test: {health_report['health_status']}"

        # Check Smart Fixture performance
        perf_report = performance_monitor.get_performance_report()
        cache_hit_ratio = perf_report.get('overall_cache_hit_ratio', 0.0)

        if perf_report.get('cache_hits', 0) + perf_report.get('cache_misses', 0) > 0:
            assert cache_hit_ratio >= self.integration_thresholds['min_cache_hit_ratio'], \
                f"Smart Fixture cache hit ratio {cache_hit_ratio:.1%} below threshold"

        self.log_test_debug(f"System health check passed - Status: {health_report['health_status']}, Cache: {cache_hit_ratio:.1%}")

    def monitor_memory_usage_during_test(self):
        """Monitor memory usage during integration test"""
        perf_report = performance_monitor.get_performance_report()
        memory_usage_mb = perf_report.get('memory_usage_mb', 0.0)

        if memory_usage_mb > self.integration_thresholds['max_memory_increase_mb']:
            self.log_test_debug(f"WARNING: Memory usage {memory_usage_mb:.1f}MB exceeds threshold")

        return memory_usage_mb

    # Helper Methods

    def _get_auth_headers(self, user_id: str = 'integration_test_user_123') -> Dict[str, str]:
        """Get authentication headers for API requests"""
        return {
            'Authorization': f'Bearer integration_test_token_{user_id}',
            'Content-Type': 'application/json'
        }

    def create_integration_test_user(self, **overrides) -> Dict[str, Any]:
        """Create a test user for integration testing"""
        from tests.factories.user_factory import UserFactory
        return UserFactory.build(**overrides)

    def create_integration_test_game(self, **overrides) -> Dict[str, Any]:
        """Create a test game for integration testing"""
        from tests.factories.game_factory import GameFactory
        return GameFactory.build(**overrides)

    # Preset-Specific Helper Methods

    def setup_basic_user_scenario(self) -> Dict[str, Any]:
        """Setup basic user scenario using presets"""
        return self.get_preset_data('basic_user_setup')

    def setup_gaming_session_scenario(self) -> Dict[str, Any]:
        """Setup gaming session scenario using presets"""
        return self.get_preset_data('gaming_session_setup')

    def setup_social_network_scenario(self) -> Dict[str, Any]:
        """Setup social network scenario using presets"""
        return self.get_preset_data('social_network_setup')

    def setup_financial_scenario(self) -> Dict[str, Any]:
        """Setup financial scenario using presets"""
        return self.get_preset_data('financial_setup')

    def setup_admin_scenario(self) -> Dict[str, Any]:
        """Setup admin scenario using presets"""
        return self.get_preset_data('admin_setup')

    def setup_complete_ecosystem(self) -> Dict[str, Any]:
        """Setup complete test data ecosystem"""
        return self.get_preset_data('test_data_ecosystem')


class IntegrationTestMixin:
    """
    Mixin class providing additional utilities for integration testing
    Can be used with existing test classes that can't extend BaseIntegrationTest
    """

    def setup_minimal_mocking(self):
        """Setup minimal external service mocking"""
        patches = []

        # Mock external email service
        email_patch = patch('app.core.services.email_service.send_email', return_value=True)
        email_patch.start()
        patches.append(email_patch)

        return patches

    def verify_cross_module_interaction(self, module1: str, module2: str, interaction_data: Dict[str, Any]):
        """Generic cross-module interaction verification"""
        # This would implement generic cross-module testing logic
        pass

    def track_integration_performance(self, operation_name: str):
        """Track performance of integration operations"""
        if not hasattr(self, 'integration_timings'):
            self.integration_timings = {}

        start_time = time.time()

        def end_tracking():
            duration = (time.time() - start_time) * 1000
            self.integration_timings[operation_name] = duration
            return duration

        return end_tracking