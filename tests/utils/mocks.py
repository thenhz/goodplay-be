"""
Specialized Mock Utilities for GoodPlay Testing (GOO-35)

Provides pre-configured mocks and mock factories for common GoodPlay
components to reduce boilerplate and standardize testing patterns.
"""
import uuid
from typing import Dict, Any, List, Optional, Union, Type
from unittest.mock import MagicMock, Mock, patch
from bson import ObjectId
from datetime import datetime, timezone
from flask import Flask
from flask.testing import FlaskClient


# Service Mock Factories

def create_service_mock(service_type: str = "generic") -> MagicMock:
    """
    Create a pre-configured service mock with common method patterns

    Args:
        service_type: Type of service (generic, auth, user, game, etc.)
    """
    service_mock = MagicMock(name=f"mock_{service_type}_service")

    # Common service response pattern: (success, message, result)
    default_success = (True, "Operation successful", {"id": "test_123"})
    default_failure = (False, "Operation failed", None)

    # Setup common CRUD operations
    service_mock.create.return_value = (True, "Created successfully", {"id": "test_123"})
    service_mock.get.return_value = (True, "Retrieved successfully", {"data": "test_data"})
    service_mock.update.return_value = (True, "Updated successfully", {"id": "test_123"})
    service_mock.delete.return_value = (True, "Deleted successfully", None)
    service_mock.list.return_value = (True, "List retrieved", {"items": [], "total": 0})

    # Service-specific configurations
    if service_type == "auth":
        service_mock.register_user.return_value = (True, "Registration completed successfully", {
            "user": {"id": "user_123", "email": "test@example.com"},
            "tokens": {"access_token": "token_123", "refresh_token": "refresh_123"}
        })
        service_mock.login_user.return_value = (True, "Login successful", {
            "user": {"id": "user_123", "email": "test@example.com"},
            "tokens": {"access_token": "token_123", "refresh_token": "refresh_123"}
        })
        service_mock.validate_token.return_value = (True, "Token valid", {"user_id": "user_123"})

    elif service_type == "user":
        service_mock.get_user_profile.return_value = (True, "Profile retrieved", {
            "id": "user_123",
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User"
        })
        service_mock.update_profile.return_value = (True, "Profile updated", {"id": "user_123"})

    elif service_type == "game":
        service_mock.start_session.return_value = (True, "Session started", {"session_id": "session_123"})
        service_mock.end_session.return_value = (True, "Session ended", {"final_score": 100})
        service_mock.get_leaderboard.return_value = (True, "Leaderboard retrieved", {"rankings": []})

    return service_mock


def create_repository_mock(repository_type: str = "generic") -> MagicMock:
    """
    Create a pre-configured repository mock with common CRUD operations

    Args:
        repository_type: Type of repository (generic, user, game, etc.)
    """
    repo_mock = MagicMock(name=f"mock_{repository_type}_repository")

    # Setup common CRUD operations
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

    # Repository-specific configurations
    if repository_type == "user":
        repo_mock.find_by_email.return_value = None
        repo_mock.email_exists.return_value = False
        repo_mock.create_user.return_value = "user_123"

    elif repository_type == "game":
        repo_mock.find_active_games.return_value = []
        repo_mock.find_by_category.return_value = []
        repo_mock.get_game_stats.return_value = {"plays": 0, "avg_score": 0}

    elif repository_type == "session":
        repo_mock.find_active_sessions.return_value = []
        repo_mock.find_by_user.return_value = []
        repo_mock.end_session.return_value = True

    return repo_mock


def create_api_client_mock() -> MagicMock:
    """Create a mock for external API clients"""
    client_mock = MagicMock(name="mock_api_client")

    # HTTP methods
    client_mock.get.return_value = {"status": "success", "data": {}}
    client_mock.post.return_value = {"status": "success", "id": "api_123"}
    client_mock.put.return_value = {"status": "success"}
    client_mock.delete.return_value = {"status": "success"}
    client_mock.patch.return_value = {"status": "success"}

    # Common API patterns
    client_mock.authenticate.return_value = {"token": "api_token_123", "expires_in": 3600}
    client_mock.send_request.return_value = {"success": True, "response": {}}

    return client_mock


# Authentication Mocking

class AuthenticationMocker:
    """Helper class for mocking authentication components"""

    def __init__(self):
        self.patches = []
        self.current_user = None

    def mock_jwt_token(self, user_id: str = "test_user_123", role: str = "user", **claims) -> str:
        """Mock JWT token validation and return token string"""
        token_data = {
            'user_id': user_id,
            'role': role,
            'exp': datetime.now(timezone.utc).replace(year=2025).timestamp(),
            **claims
        }
        self.current_user = token_data

        # Mock flask-jwt-extended functions
        jwt_patch = patch('flask_jwt_extended.verify_jwt_in_request')
        jwt_patch.start()
        self.patches.append(jwt_patch)

        identity_patch = patch('flask_jwt_extended.get_jwt_identity', return_value=user_id)
        identity_patch.start()
        self.patches.append(identity_patch)

        claims_patch = patch('flask_jwt_extended.get_jwt', return_value=token_data)
        claims_patch.start()
        self.patches.append(claims_patch)

        return f"test_jwt_token_{user_id}"

    def mock_admin_user(self, user_id: str = "admin_123") -> str:
        """Mock admin user authentication"""
        return self.mock_jwt_token(user_id=user_id, role="admin", permissions=["read", "write", "admin"])

    def mock_guest_user(self, user_id: str = "guest_123") -> str:
        """Mock guest user authentication"""
        return self.mock_jwt_token(user_id=user_id, role="guest", permissions=["read"])

    def mock_no_authentication(self):
        """Mock no authentication (should trigger auth required errors)"""
        # Mock jwt functions to raise exceptions
        jwt_patch = patch('flask_jwt_extended.verify_jwt_in_request', side_effect=Exception("No token"))
        jwt_patch.start()
        self.patches.append(jwt_patch)

        identity_patch = patch('flask_jwt_extended.get_jwt_identity', return_value=None)
        identity_patch.start()
        self.patches.append(identity_patch)

    def stop_mocking(self):
        """Stop all authentication mocks"""
        for patcher in self.patches:
            patcher.stop()
        self.patches.clear()
        self.current_user = None


def mock_authentication(user_id: str = "test_user_123", role: str = "user") -> AuthenticationMocker:
    """Quick function to mock authentication"""
    mocker = AuthenticationMocker()
    mocker.mock_jwt_token(user_id, role)
    return mocker


# Database Mocking

class DatabaseMocker:
    """Helper class for mocking MongoDB operations"""

    def __init__(self):
        self.patches = []
        self.collections = {}

    def mock_database(self, database_name: str = "test_db"):
        """Mock the entire database connection"""
        mock_db = MagicMock(name=f"mock_{database_name}")
        mock_collections = {}

        # Common collections
        for collection_name in ['users', 'games', 'sessions', 'achievements', 'transactions']:
            mock_collection = self._create_collection_mock(collection_name)
            mock_collections[collection_name] = mock_collection
            mock_db[collection_name] = mock_collection

        self.collections = mock_collections

        # Mock get_db function
        db_patch = patch('app.get_db', return_value=mock_db)
        db_patch.start()
        self.patches.append(db_patch)

        return mock_db

    def _create_collection_mock(self, collection_name: str) -> MagicMock:
        """Create a mock for a MongoDB collection"""
        collection_mock = MagicMock(name=f"mock_{collection_name}_collection")

        # Setup default responses
        collection_mock.find_one.return_value = None
        collection_mock.find.return_value = []
        collection_mock.count_documents.return_value = 0

        # Insert operations
        mock_insert_result = MagicMock()
        mock_insert_result.inserted_id = ObjectId()
        collection_mock.insert_one.return_value = mock_insert_result

        # Update operations
        mock_update_result = MagicMock()
        mock_update_result.modified_count = 1
        mock_update_result.matched_count = 1
        collection_mock.update_one.return_value = mock_update_result
        collection_mock.update_many.return_value = mock_update_result

        # Delete operations
        mock_delete_result = MagicMock()
        mock_delete_result.deleted_count = 1
        collection_mock.delete_one.return_value = mock_delete_result
        collection_mock.delete_many.return_value = mock_delete_result

        # Index operations
        collection_mock.create_index.return_value = "index_created"
        collection_mock.create_indexes.return_value = ["index1", "index2"]

        return collection_mock

    def setup_collection_data(self, collection_name: str, data: List[Dict[str, Any]]):
        """Setup mock data for a specific collection"""
        if collection_name not in self.collections:
            raise ValueError(f"Collection '{collection_name}' not mocked")

        collection = self.collections[collection_name]

        # Setup find operations to return data
        collection.find.return_value = data
        collection.count_documents.return_value = len(data)

        # Setup find_one to return first item or None
        if data:
            collection.find_one.return_value = data[0]
        else:
            collection.find_one.return_value = None

    def stop_mocking(self):
        """Stop all database mocks"""
        for patcher in self.patches:
            patcher.stop()
        self.patches.clear()
        self.collections.clear()


def mock_database(database_name: str = "test_db") -> DatabaseMocker:
    """Quick function to mock database"""
    mocker = DatabaseMocker()
    mocker.mock_database(database_name)
    return mocker


# External Service Mocking

class ExternalServiceMocker:
    """Helper class for mocking external services"""

    def __init__(self):
        self.patches = []

    def mock_email_service(self, success: bool = True):
        """Mock email service"""
        email_mock = MagicMock(name="mock_email_service")
        email_mock.send.return_value = success
        email_mock.send_email.return_value = success
        email_mock.send_notification.return_value = success

        # Common email service paths
        paths_to_mock = [
            'app.core.services.email_service',
            'app.external.email_service',
            'app.integrations.email_service'
        ]

        for path in paths_to_mock:
            try:
                patch_obj = patch(path, email_mock)
                patch_obj.start()
                self.patches.append(patch_obj)
                break
            except ImportError:
                continue

        return email_mock

    def mock_payment_service(self):
        """Mock payment/billing service"""
        payment_mock = MagicMock(name="mock_payment_service")
        payment_mock.charge.return_value = {
            "success": True,
            "transaction_id": "tx_test_123",
            "amount": 10.00
        }
        payment_mock.refund.return_value = {
            "success": True,
            "refund_id": "ref_test_123"
        }
        payment_mock.validate_card.return_value = {"valid": True}

        # Mock payment service paths
        paths_to_mock = [
            'app.donations.services.payment_service',
            'app.external.payment_service',
            'app.integrations.stripe_service'
        ]

        for path in paths_to_mock:
            try:
                patch_obj = patch(path, payment_mock)
                patch_obj.start()
                self.patches.append(patch_obj)
                break
            except ImportError:
                continue

        return payment_mock

    def mock_external_api(self, api_name: str, responses: Dict[str, Any] = None):
        """Mock generic external API"""
        api_mock = MagicMock(name=f"mock_{api_name}_api")

        default_responses = {
            'get': {"status": "success", "data": {}},
            'post': {"status": "success", "id": f"{api_name}_123"},
            'put': {"status": "success"},
            'delete': {"status": "success"}
        }

        responses = responses or default_responses

        for method, response in responses.items():
            getattr(api_mock, method).return_value = response

        return api_mock

    def stop_mocking(self):
        """Stop all external service mocks"""
        for patcher in self.patches:
            patcher.stop()
        self.patches.clear()


def mock_external_service(service_type: str) -> ExternalServiceMocker:
    """Quick function to mock external services"""
    mocker = ExternalServiceMocker()

    if service_type == "email":
        mocker.mock_email_service()
    elif service_type == "payment":
        mocker.mock_payment_service()
    else:
        mocker.mock_external_api(service_type)

    return mocker


# Flask Test Client Mocking

def create_flask_test_client(app: Flask = None) -> FlaskClient:
    """Create a Flask test client with proper configuration"""
    if app is None:
        # Create a minimal test app
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False

    return app.test_client()


class MockFlaskResponse:
    """Mock Flask response for testing"""

    def __init__(self, json_data: Dict[str, Any], status_code: int = 200, headers: Dict[str, str] = None):
        self.json_data = json_data
        self.status_code = status_code
        self.headers = headers or {}

    def get_json(self) -> Dict[str, Any]:
        """Get JSON response data"""
        return self.json_data

    def get_data(self) -> bytes:
        """Get response data as bytes"""
        import json
        return json.dumps(self.json_data).encode('utf-8')


# User Session Mocking

def mock_user_session(user_id: str = "test_user_123", session_data: Dict[str, Any] = None):
    """Mock user session data"""
    default_session_data = {
        'user_id': user_id,
        'logged_in': True,
        'role': 'user',
        'last_activity': datetime.now(timezone.utc)
    }

    session_data = session_data or default_session_data

    # Mock Flask session
    session_patch = patch('flask.session', session_data)
    session_patch.start()

    return session_patch


# Comprehensive Mock Factory

class MockFactory:
    """Factory for creating comprehensive mock setups"""

    def __init__(self):
        self.auth_mocker = AuthenticationMocker()
        self.db_mocker = DatabaseMocker()
        self.external_mocker = ExternalServiceMocker()

    def setup_complete_test_environment(self, user_id: str = "test_user_123", role: str = "user"):
        """Setup complete mock environment for testing"""
        # Mock authentication
        self.auth_mocker.mock_jwt_token(user_id, role)

        # Mock database
        self.db_mocker.mock_database()

        # Mock external services
        self.external_mocker.mock_email_service()

        return {
            'auth': self.auth_mocker,
            'database': self.db_mocker,
            'external': self.external_mocker
        }

    def setup_integration_test_environment(self):
        """Setup environment for integration tests (minimal mocking)"""
        # Only mock external services, keep internal logic
        self.external_mocker.mock_email_service()
        self.external_mocker.mock_payment_service()

        return {'external': self.external_mocker}

    def cleanup(self):
        """Clean up all mocks"""
        self.auth_mocker.stop_mocking()
        self.db_mocker.stop_mocking()
        self.external_mocker.stop_mocking()


# Convenience functions for quick access

def setup_test_mocks(user_id: str = "test_user_123", role: str = "user") -> MockFactory:
    """Quick setup for complete test mock environment"""
    factory = MockFactory()
    factory.setup_complete_test_environment(user_id, role)
    return factory


def setup_integration_mocks() -> MockFactory:
    """Quick setup for integration test mocks"""
    factory = MockFactory()
    factory.setup_integration_test_environment()
    return factory


# Context Managers for Mock Management

class MockContext:
    """Context manager for managing mocks in tests"""

    def __init__(self, mock_factory: MockFactory):
        self.mock_factory = mock_factory

    def __enter__(self):
        return self.mock_factory

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.mock_factory.cleanup()


def mock_context(user_id: str = "test_user_123", role: str = "user") -> MockContext:
    """Context manager for complete mock setup"""
    factory = setup_test_mocks(user_id, role)
    return MockContext(factory)


# Usage Examples:
"""
# Simple service mock
service_mock = create_service_mock("auth")
service_mock.register_user.return_value = (True, "Success", {"id": "user_123"})

# Authentication mocking
auth_mocker = mock_authentication("user_123", "admin")

# Database mocking
db_mocker = mock_database()
db_mocker.setup_collection_data("users", [{"_id": "user_123", "email": "test@example.com"}])

# Complete environment
with mock_context("admin_123", "admin") as mocks:
    # All mocks are set up
    # Test code here
    pass
# All mocks are automatically cleaned up

# Factory usage
factory = MockFactory()
mocks = factory.setup_complete_test_environment()
# ... run tests ...
factory.cleanup()
"""