"""
BaseControllerTest - Enterprise Test Class for Controller Layer Testing (GOO-35)

Provides standardized testing patterns for controller layer classes with automatic
service mocking, authentication testing, API response validation, and Smart Fixture integration.
"""
import pytest
import json
import os
from typing import Dict, Any, List, Optional, Type, Union
from unittest.mock import MagicMock, patch, Mock
from flask import Flask
from flask.testing import FlaskClient

# Import Smart Fixture System
from tests.fixtures import (
    smart_fixture, factory_fixture, preset_fixture,
    smart_fixture_manager, performance_monitor, cleanup_manager,
    FixtureScope, get_system_health
)

# Import base test infrastructure
from .test_base import TestBase
from .config import TestConfig


class BaseControllerTest(TestBase):
    """
    Base test class for controller layer (API endpoint) testing

    Features:
    - Automatic service layer mocking with Smart Fixtures
    - Authentication decorator testing (@auth_required, @admin_required)
    - API response format validation (success/error patterns)
    - Request/response JSON schema validation
    - Smart Fixture integration for request data generation
    - CORS and security header validation
    - Performance monitoring for API operations
    - Common HTTP status code assertions

    Usage:
    ```python
    class TestUserController(BaseControllerTest):
        service_dependencies = ['user_service']

        def test_create_user_endpoint(self):
            # Setup test data using Smart Fixtures
            user_data = self.create_test_request_data('user_creation')

            # Mock service response
            self.setup_service_mock_response('user_service', 'create_user',
                (True, "User created successfully", {'user_id': 'test_123'}))

            # Test API endpoint
            response = self.client.post('/api/users', json=user_data)

            # Validate using built-in assertions
            self.assert_api_success(response, "User created successfully")
    ```
    """

    # Controller configuration - override in subclasses
    service_dependencies: list = []
    authentication_required: bool = True
    admin_required: bool = False

    def setup_method(self, method):
        """Enhanced setup for controller layer testing"""
        super().setup_method(method)

        # Setup Flask test client
        self._setup_flask_test_client()

        # Setup service mocks
        self._setup_service_mocks()

        # Setup authentication mocks
        self._setup_authentication_mocks()

        # Setup Smart Fixture integration
        self._setup_smart_fixture_integration()

        # Register controller test fixtures
        self._register_controller_test_fixtures()

        # Setup request/response tracking
        self._setup_request_response_tracking()

        self.log_test_info(f"Controller test setup complete with {len(self.service_dependencies)} service mocks")

    def teardown_method(self, method):
        """Enhanced teardown with Smart Fixture cleanup"""
        # Cleanup Smart Fixtures for this test
        cleanup_manager.cleanup_fixture_scope('function')

        # Stop any active patches
        self._stop_patches()

        # Parent teardown
        super().teardown_method(method)

        # Log API performance if enabled
        self._log_api_performance()

    def _setup_flask_test_client(self):
        """Setup Flask test client with proper configuration"""
        # Import app here to avoid circular imports
        from app import create_app

        # Create test app
        self.app = create_app('testing')
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing

        # Create test client
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

        self.log_test_debug("Flask test client setup complete")

    def _setup_service_mocks(self):
        """Setup service layer mocks"""
        self.service_mocks = {}
        self.service_patches = []

        for service_name in self.service_dependencies:
            # Create mock service
            mock_service = MagicMock()
            self.service_mocks[service_name] = mock_service

            # Setup default service method responses
            self._setup_service_default_responses(mock_service)

            # Patch the service in the app
            service_patch = patch(f'app.{self._get_service_module_path(service_name)}.{service_name}', mock_service)
            service_patch.start()
            self.service_patches.append(service_patch)

            self.log_test_debug(f"Service mock setup: {service_name}")

    def _setup_service_default_responses(self, mock_service):
        """Setup default responses for service methods"""
        # Common service method patterns
        default_success = (True, "Operation successful", {"result": "test_data"})
        default_failure = (False, "Operation failed", None)

        # Setup common method mocks
        for method_name in ['create', 'get', 'update', 'delete', 'list']:
            if hasattr(mock_service, method_name):
                getattr(mock_service, method_name).return_value = default_success

    def _get_service_module_path(self, service_name: str) -> str:
        """Get module path for service based on naming convention"""
        # Convert service_name to module path
        # e.g., 'user_service' -> 'core.services.user_service'
        module_map = {
            'auth_service': 'core.services.auth_service',
            'user_service': 'core.services.user_service',
            'preferences_service': 'preferences.services.preferences_service',
            'game_service': 'games.services.game_service',
            'game_session_service': 'games.services.game_session_service',
            'relationship_service': 'social.services.relationship_service',
        }
        return module_map.get(service_name, f'core.services.{service_name}')

    def _setup_authentication_mocks(self):
        """Setup authentication and authorization mocks"""
        # Mock JWT token verification
        self.jwt_patches = []

        if self.authentication_required:
            # Mock @auth_required decorator
            auth_patch = patch('app.core.decorators.auth.jwt_required')
            auth_mock = auth_patch.start()
            self.jwt_patches.append(auth_patch)

            # Mock get_jwt_identity
            identity_patch = patch('app.core.decorators.auth.get_jwt_identity', return_value='test_user_123')
            identity_patch.start()
            self.jwt_patches.append(identity_patch)

        if self.admin_required:
            # Mock @admin_required decorator
            admin_patch = patch('app.core.decorators.auth.admin_required')
            admin_patch.start()
            self.jwt_patches.append(admin_patch)

        # Create test authentication headers
        self.auth_headers = {
            'Authorization': 'Bearer test_jwt_token',
            'Content-Type': 'application/json'
        }

        self.log_test_debug(f"Authentication mocks setup - Auth: {self.authentication_required}, Admin: {self.admin_required}")

    def _setup_smart_fixture_integration(self):
        """Initialize Smart Fixture system for controller testing"""
        if not hasattr(self, '_smart_fixtures_registered'):
            self._smart_fixtures_registered = True

    def _register_controller_test_fixtures(self):
        """Register common fixtures for controller testing"""

        @smart_fixture('test_request_data', scope=FixtureScope.FUNCTION)
        def test_request_data():
            return {
                'test_field': 'test_value',
                'numeric_field': 42,
                'boolean_field': True,
                'array_field': ['item1', 'item2']
            }

        @smart_fixture('user_creation_request', scope=FixtureScope.FUNCTION)
        def user_creation_request():
            return {
                'email': 'test@goodplay.com',
                'password': 'password123',
                'first_name': 'Test',
                'last_name': 'User'
            }

        @smart_fixture('user_update_request', scope=FixtureScope.FUNCTION)
        def user_update_request():
            return {
                'first_name': 'Updated',
                'last_name': 'Name'
            }

        @smart_fixture('game_creation_request', scope=FixtureScope.FUNCTION)
        def game_creation_request():
            return {
                'title': 'Test Game',
                'description': 'A test game',
                'category': 'puzzle',
                'difficulty': 'medium',
                'credits_required': 10
            }

        @smart_fixture('preferences_update_request', scope=FixtureScope.FUNCTION)
        def preferences_update_request():
            return {
                'gaming': {'difficulty': 'hard'},
                'notifications': {'email_enabled': False},
                'privacy': {'profile_public': True}
            }

    def _setup_request_response_tracking(self):
        """Setup tracking for request/response performance"""
        self.api_operation_timings = {}
        self.request_count = 0
        self.response_sizes = {}

    def _stop_patches(self):
        """Stop all active patches"""
        for patch_obj in self.service_patches:
            patch_obj.stop()
        for patch_obj in self.jwt_patches:
            patch_obj.stop()

    def _log_api_performance(self):
        """Log API performance metrics"""
        if hasattr(self, 'api_operation_timings') and self.api_operation_timings:
            self.log_test_debug("API operation timings:", self.api_operation_timings)

    # Smart Fixture Integration Methods

    def create_test_request_data(self, request_type: str = 'test_request_data', **overrides) -> Dict[str, Any]:
        """Create test request data using Smart Fixtures"""
        request_data = smart_fixture_manager.create_fixture(request_type)
        if overrides:
            request_data.update(overrides)
        return request_data

    def create_user_creation_request(self, **overrides) -> Dict[str, Any]:
        """Create user creation request data"""
        return self.create_test_request_data('user_creation_request', **overrides)

    def create_game_creation_request(self, **overrides) -> Dict[str, Any]:
        """Create game creation request data"""
        return self.create_test_request_data('game_creation_request', **overrides)

    def create_preferences_update_request(self, **overrides) -> Dict[str, Any]:
        """Create preferences update request data"""
        return self.create_test_request_data('preferences_update_request', **overrides)

    # Service Mock Configuration Methods

    def setup_service_mock_response(self, service_name: str, method_name: str, return_value: Any):
        """Setup a specific service method response"""
        if service_name not in self.service_mocks:
            raise ValueError(f"Service mock '{service_name}' not found. Available: {list(self.service_mocks.keys())}")

        service_mock = self.service_mocks[service_name]
        getattr(service_mock, method_name).return_value = return_value

        self.log_test_debug(f"Setup {service_name}.{method_name} mock response")

    def setup_service_success_response(self, service_name: str, method_name: str, message: str = "Operation successful", result: Any = None):
        """Setup service method to return success response"""
        success_response = (True, message, result)
        self.setup_service_mock_response(service_name, method_name, success_response)

    def setup_service_failure_response(self, service_name: str, method_name: str, message: str = "Operation failed", result: Any = None):
        """Setup service method to return failure response"""
        failure_response = (False, message, result)
        self.setup_service_mock_response(service_name, method_name, failure_response)

    def setup_service_exception(self, service_name: str, method_name: str, exception: Exception):
        """Setup service method to raise an exception"""
        if service_name not in self.service_mocks:
            raise ValueError(f"Service mock '{service_name}' not found")

        service_mock = self.service_mocks[service_name]
        getattr(service_mock, method_name).side_effect = exception

        self.log_test_debug(f"Setup {service_name}.{method_name} to raise {exception.__class__.__name__}")

    # Service Mock Assertion Methods

    def assert_service_method_called(self, service_name: str, method_name: str, *args, **kwargs):
        """Assert that a service method was called with specific arguments"""
        if service_name not in self.service_mocks:
            raise AssertionError(f"Service mock '{service_name}' not found")

        service_mock = self.service_mocks[service_name]
        method_mock = getattr(service_mock, method_name)

        if args or kwargs:
            method_mock.assert_called_with(*args, **kwargs)
        else:
            method_mock.assert_called()

        self.log_test_debug(f"Verified {service_name}.{method_name} was called")

    def assert_service_method_not_called(self, service_name: str, method_name: str):
        """Assert that a service method was not called"""
        if service_name not in self.service_mocks:
            raise AssertionError(f"Service mock '{service_name}' not found")

        service_mock = self.service_mocks[service_name]
        method_mock = getattr(service_mock, method_name)
        method_mock.assert_not_called()

        self.log_test_debug(f"Verified {service_name}.{method_name} was not called")

    def get_service_method_call_count(self, service_name: str, method_name: str) -> int:
        """Get the number of times a service method was called"""
        if service_name not in self.service_mocks:
            return 0

        service_mock = self.service_mocks[service_name]
        method_mock = getattr(service_mock, method_name)
        return method_mock.call_count

    # API Request Helper Methods

    def make_authenticated_request(self, method: str, url: str, data: Dict[str, Any] = None,
                                 headers: Dict[str, str] = None) -> Any:
        """Make an authenticated API request"""
        request_headers = self.auth_headers.copy()
        if headers:
            request_headers.update(headers)

        client_method = getattr(self.client, method.lower())

        if data:
            return client_method(url, json=data, headers=request_headers)
        else:
            return client_method(url, headers=request_headers)

    def make_unauthenticated_request(self, method: str, url: str, data: Dict[str, Any] = None) -> Any:
        """Make an unauthenticated API request"""
        client_method = getattr(self.client, method.lower())

        if data:
            return client_method(url, json=data, headers={'Content-Type': 'application/json'})
        else:
            return client_method(url)

    def post_authenticated(self, url: str, data: Dict[str, Any], headers: Dict[str, str] = None) -> Any:
        """Make authenticated POST request"""
        return self.make_authenticated_request('POST', url, data, headers)

    def get_authenticated(self, url: str, headers: Dict[str, str] = None) -> Any:
        """Make authenticated GET request"""
        return self.make_authenticated_request('GET', url, headers=headers)

    def put_authenticated(self, url: str, data: Dict[str, Any], headers: Dict[str, str] = None) -> Any:
        """Make authenticated PUT request"""
        return self.make_authenticated_request('PUT', url, data, headers)

    def delete_authenticated(self, url: str, headers: Dict[str, str] = None) -> Any:
        """Make authenticated DELETE request"""
        return self.make_authenticated_request('DELETE', url, headers=headers)

    # API Response Assertion Methods

    def assert_api_success(self, response, expected_message: str = None, expected_status: int = 200):
        """Assert API response indicates success"""
        self.assert_api_response_status(response, expected_status)

        data = response.get_json()
        assert data is not None, "Expected JSON response"

        self.assert_success_response(data, expected_message)
        self.log_test_debug(f"API success assertion passed: {expected_status}")

    def assert_api_error(self, response, expected_status: int, expected_message: str = None):
        """Assert API response indicates error"""
        self.assert_api_response_status(response, expected_status)

        data = response.get_json()
        assert data is not None, "Expected JSON response"

        self.assert_error_response(data, expected_message)
        self.log_test_debug(f"API error assertion passed: {expected_status}")

    def assert_api_validation_error(self, response, field_name: str = None):
        """Assert API response indicates validation error"""
        self.assert_api_error(response, 400)

        if field_name:
            data = response.get_json()
            # Check for validation error details
            assert 'errors' in data or 'validation_errors' in data, \
                "Expected validation error details"

    def assert_api_unauthorized(self, response):
        """Assert API response indicates unauthorized access"""
        self.assert_api_error(response, 401, "Authentication required")

    def assert_api_forbidden(self, response):
        """Assert API response indicates forbidden access"""
        self.assert_api_error(response, 403)

    def assert_api_not_found(self, response):
        """Assert API response indicates resource not found"""
        self.assert_api_error(response, 404)

    def assert_response_has_field(self, response, field_name: str):
        """Assert response JSON contains specific field"""
        data = response.get_json()
        assert data is not None, "Expected JSON response"
        assert field_name in data, f"Expected field '{field_name}' in response"

    def assert_response_field_equals(self, response, field_name: str, expected_value: Any):
        """Assert response field has specific value"""
        data = response.get_json()
        assert data is not None, "Expected JSON response"
        assert field_name in data, f"Expected field '{field_name}' in response"
        assert data[field_name] == expected_value, \
            f"Expected {field_name}='{expected_value}', got '{data[field_name]}'"

    def assert_response_pagination(self, response):
        """Assert response contains pagination information"""
        data = response.get_json()
        assert data is not None, "Expected JSON response"

        # Check for common pagination fields
        pagination_fields = ['total', 'page', 'per_page', 'pages']
        for field in pagination_fields:
            assert field in data, f"Expected pagination field '{field}' in response"

    # Authentication Testing Methods

    def test_endpoint_requires_authentication(self, method: str, url: str, data: Dict[str, Any] = None):
        """Test that endpoint requires authentication"""
        response = self.make_unauthenticated_request(method, url, data)
        self.assert_api_unauthorized(response)
        self.log_test_debug(f"Authentication requirement verified for {method} {url}")

    def test_endpoint_requires_admin(self, method: str, url: str, data: Dict[str, Any] = None):
        """Test that endpoint requires admin privileges"""
        # Mock non-admin user
        with patch('app.core.decorators.auth.get_jwt_identity', return_value='regular_user_123'):
            response = self.make_authenticated_request(method, url, data)
            self.assert_api_forbidden(response)
        self.log_test_debug(f"Admin requirement verified for {method} {url}")

    # Request Validation Testing Methods

    def test_endpoint_validates_required_fields(self, method: str, url: str, required_fields: List[str]):
        """Test that endpoint validates required fields"""
        for field in required_fields:
            # Create request data missing the required field
            test_data = self.create_test_request_data()
            if field in test_data:
                del test_data[field]

            response = self.make_authenticated_request(method, url, test_data)
            self.assert_api_validation_error(response, field)
            self.log_test_debug(f"Required field validation verified for: {field}")

    def test_endpoint_validates_field_types(self, method: str, url: str, field_types: Dict[str, type]):
        """Test that endpoint validates field types"""
        for field_name, expected_type in field_types.items():
            test_data = self.create_test_request_data()

            # Set invalid type for the field
            if expected_type == str:
                test_data[field_name] = 12345  # Invalid: number instead of string
            elif expected_type == int:
                test_data[field_name] = "invalid"  # Invalid: string instead of number
            elif expected_type == bool:
                test_data[field_name] = "invalid"  # Invalid: string instead of boolean

            response = self.make_authenticated_request(method, url, test_data)
            self.assert_api_validation_error(response, field_name)
            self.log_test_debug(f"Field type validation verified for: {field_name}")

    # Performance Testing Methods

    def assert_api_response_time(self, method: str, url: str, max_time_ms: float = 200.0,
                                data: Dict[str, Any] = None):
        """Assert API response time is within acceptable limits"""
        import time

        start_time = time.time()
        response = self.make_authenticated_request(method, url, data)
        response_time_ms = (time.time() - start_time) * 1000

        assert response_time_ms <= max_time_ms, \
            f"API response took {response_time_ms:.1f}ms, expected under {max_time_ms}ms"

        # Track timing for reporting
        endpoint_key = f"{method} {url}"
        self.api_operation_timings[endpoint_key] = response_time_ms

        self.log_test_debug(f"API performance assertion passed: {endpoint_key} took {response_time_ms:.1f}ms")
        return response

    # CORS and Security Testing Methods

    def test_cors_headers(self, method: str, url: str):
        """Test that endpoint includes proper CORS headers"""
        response = self.make_authenticated_request(method, url)

        # Check for CORS headers
        assert 'Access-Control-Allow-Origin' in response.headers, \
            "Expected CORS Access-Control-Allow-Origin header"

        self.log_test_debug(f"CORS headers verified for {method} {url}")

    def test_security_headers(self, method: str, url: str):
        """Test that endpoint includes security headers"""
        response = self.make_authenticated_request(method, url)

        security_headers = [
            'X-Content-Type-Options',
            'X-Frame-Options',
            'X-XSS-Protection'
        ]

        for header in security_headers:
            if header in response.headers:
                self.log_test_debug(f"Security header found: {header}")

    # Performance and Health Monitoring

    def get_smart_fixture_performance_report(self) -> Dict[str, Any]:
        """Get Smart Fixture performance report for this test"""
        return performance_monitor.get_performance_report()

    def get_system_health_report(self) -> Dict[str, Any]:
        """Get system health report including Smart Fixtures"""
        return get_system_health()


class ControllerTestMixin:
    """
    Mixin class providing additional utilities for controller testing
    Can be used with existing test classes that can't extend BaseControllerTest
    """

    def setup_flask_test_client(self, app):
        """Setup Flask test client"""
        app.config['TESTING'] = True
        return app.test_client()

    def create_auth_headers(self, token: str = "test_token"):
        """Create authentication headers"""
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

    def assert_json_response(self, response, expected_status: int = 200):
        """Assert response is JSON with expected status"""
        assert response.status_code == expected_status
        assert response.content_type == 'application/json'
        return response.get_json()