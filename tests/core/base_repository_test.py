"""
BaseRepositoryTest - Enterprise Test Class for Repository Layer Testing (GOO-35)

Provides standardized testing patterns for repository layer classes with automatic
MongoDB mocking, Smart Fixture integration, and BaseRepository compliance validation.
"""
import pytest
import os
from typing import Dict, Any, List, Optional, Type
from unittest.mock import MagicMock, patch, Mock
from bson import ObjectId
from datetime import datetime, timezone

# Import Smart Fixture System
from tests.fixtures import (
    smart_fixture, factory_fixture, preset_fixture,
    smart_fixture_manager, performance_monitor, cleanup_manager,
    FixtureScope, get_system_health
)

# Import base test infrastructure
from .test_base import TestBase
from .config import TestConfig

# Import repository base class for compliance testing
from app.core.repositories.base_repository import BaseRepository


class BaseRepositoryTest(TestBase):
    """
    Base test class for repository layer testing with MongoDB mocking

    Features:
    - Automatic MongoDB collection and database mocking
    - CRUD operation testing patterns
    - BaseRepository compliance validation
    - Index creation testing with TESTING mode awareness
    - Smart Fixture integration for database state setup
    - MongoDB ObjectId handling and validation
    - Performance monitoring for database operations

    Usage:
    ```python
    class TestUserRepository(BaseRepositoryTest):
        repository_class = UserRepository
        collection_name = 'users'

        def test_find_user_by_email(self):
            # Setup test data using Smart Fixtures
            user_data = self.create_test_document()

            # Mock collection response
            self.setup_find_one_mock(user_data)

            # Test repository method
            result = self.repository.find_by_email('test@example.com')

            # Validate using built-in assertions
            self.assert_document_returned(result, user_data)
    ```
    """

    # Repository configuration - override in subclasses
    repository_class: Optional[Type[BaseRepository]] = None
    collection_name: str = 'test_collection'

    def setup_method(self, method):
        """Enhanced setup for repository layer testing"""
        super().setup_method(method)

        # Ensure TESTING environment is set
        self._ensure_testing_environment()

        # Setup MongoDB mocks
        self._setup_mongodb_mocks()

        # Setup repository instance with mocked database
        self._setup_repository_with_mocks()

        # Setup Smart Fixture integration
        self._setup_smart_fixture_integration()

        # Register repository test fixtures
        self._register_repository_test_fixtures()

        self.log_test_info(f"Repository test setup complete: {self.repository_class.__name__ if self.repository_class else 'Unknown'}")

    def teardown_method(self, method):
        """Enhanced teardown with Smart Fixture cleanup"""
        # Cleanup Smart Fixtures for this test
        cleanup_manager.cleanup_fixture_scope('function')

        # Parent teardown
        super().teardown_method(method)

        # Log repository performance if enabled
        self._log_repository_performance()

    def _ensure_testing_environment(self):
        """Ensure TESTING environment variable is set to prevent actual DB connections"""
        os.environ['TESTING'] = 'true'
        self.log_test_debug("TESTING environment variable set to 'true'")

    def _setup_mongodb_mocks(self):
        """Setup comprehensive MongoDB mocking"""
        # Mock the database and collection
        self.mock_db = MagicMock()
        self.mock_collection = MagicMock()

        # Setup collection retrieval
        self.mock_db.__getitem__ = MagicMock(return_value=self.mock_collection)
        self.mock_db.__contains__ = MagicMock(return_value=True)

        # Setup collection methods with sensible defaults
        self._setup_collection_method_defaults()

        # Track method calls for assertions
        self.collection_method_calls = {}

        self.log_test_debug(f"MongoDB mocks setup for collection: {self.collection_name}")

    def _setup_collection_method_defaults(self):
        """Setup default return values for collection methods"""
        # Read operations
        self.mock_collection.find_one.return_value = None
        self.mock_collection.find.return_value = []
        self.mock_collection.count_documents.return_value = 0

        # Write operations
        mock_insert_result = MagicMock()
        mock_insert_result.inserted_id = ObjectId()
        self.mock_collection.insert_one.return_value = mock_insert_result

        mock_update_result = MagicMock()
        mock_update_result.modified_count = 1
        mock_update_result.matched_count = 1
        self.mock_collection.update_one.return_value = mock_update_result
        self.mock_collection.update_many.return_value = mock_update_result

        mock_delete_result = MagicMock()
        mock_delete_result.deleted_count = 1
        self.mock_collection.delete_one.return_value = mock_delete_result
        self.mock_collection.delete_many.return_value = mock_delete_result

        # Index operations
        self.mock_collection.create_index.return_value = "index_created"
        self.mock_collection.create_indexes.return_value = ["index1", "index2"]

    def _setup_repository_with_mocks(self):
        """Setup repository instance with mocked MongoDB dependencies"""
        if not self.repository_class:
            self.log_test_debug("No repository_class specified, skipping repository setup")
            return

        # Patch get_db to return our mock
        self.get_db_patcher = patch('app.get_db', return_value=self.mock_db)
        self.get_db_patcher.start()

        # Create repository instance
        self.repository = self.repository_class(self.collection_name)

        # Ensure collection is our mock
        self.repository.collection = self.mock_collection
        self.repository.db = self.mock_db

        self.log_test_debug(f"Repository setup complete: {self.repository_class.__name__}")

    def _setup_smart_fixture_integration(self):
        """Initialize Smart Fixture system for repository testing"""
        if not hasattr(self, '_smart_fixtures_registered'):
            self._smart_fixtures_registered = True

    def _register_repository_test_fixtures(self):
        """Register common fixtures for repository testing"""

        @smart_fixture('test_document_data', scope=FixtureScope.FUNCTION)
        def test_document_data():
            return {
                '_id': ObjectId(),
                'created_at': datetime.now(timezone.utc),
                'updated_at': datetime.now(timezone.utc),
                'test_field': 'test_value',
                'numeric_field': 42,
                'boolean_field': True
            }

        @smart_fixture('test_user_document', scope=FixtureScope.FUNCTION)
        def test_user_document():
            return {
                '_id': ObjectId(),
                'email': 'test@goodplay.com',
                'first_name': 'Test',
                'last_name': 'User',
                'created_at': datetime.now(timezone.utc),
                'updated_at': datetime.now(timezone.utc),
                'preferences': {
                    'gaming': {'difficulty': 'medium'},
                    'notifications': {'email_enabled': True},
                    'privacy': {'profile_public': False},
                    'donations': {'auto_donate': False}
                }
            }

        @smart_fixture('test_game_document', scope=FixtureScope.FUNCTION)
        def test_game_document():
            return {
                '_id': ObjectId(),
                'title': 'Test Game',
                'description': 'A test game document',
                'category': 'puzzle',
                'difficulty': 'medium',
                'credits_required': 10,
                'created_at': datetime.now(timezone.utc),
                'updated_at': datetime.now(timezone.utc)
            }

    def _log_repository_performance(self):
        """Log repository performance metrics"""
        if hasattr(self, 'repository_operation_timings') and self.repository_operation_timings:
            self.log_test_debug("Repository operation timings:", self.repository_operation_timings)

    # Smart Fixture Integration Methods

    def create_test_document(self, document_type: str = 'test_document_data', **overrides) -> Dict[str, Any]:
        """Create test document using Smart Fixtures"""
        document = smart_fixture_manager.create_fixture(document_type)
        if overrides:
            document.update(overrides)
        return document

    def create_test_user_document(self, **overrides) -> Dict[str, Any]:
        """Create test user document using Smart Fixtures"""
        return self.create_test_document('test_user_document', **overrides)

    def create_test_game_document(self, **overrides) -> Dict[str, Any]:
        """Create test game document using Smart Fixtures"""
        return self.create_test_document('test_game_document', **overrides)

    def create_multiple_test_documents(self, count: int, document_type: str = 'test_document_data') -> List[Dict[str, Any]]:
        """Create multiple test documents using Smart Fixtures"""
        documents = []
        for i in range(count):
            doc = self.create_test_document(document_type)
            doc['_id'] = ObjectId()  # Ensure unique IDs
            doc['sequence_number'] = i
            documents.append(doc)
        return documents

    # MongoDB Mock Configuration Methods

    def setup_find_one_mock(self, return_value: Optional[Dict[str, Any]]):
        """Setup find_one mock to return specific document"""
        self.mock_collection.find_one.return_value = return_value
        self.log_test_debug(f"Setup find_one mock to return: {return_value is not None}")

    def setup_find_many_mock(self, return_value: List[Dict[str, Any]]):
        """Setup find mock to return list of documents"""
        mock_cursor = MagicMock()
        mock_cursor.__iter__ = MagicMock(return_value=iter(return_value))
        mock_cursor.sort = MagicMock(return_value=mock_cursor)
        mock_cursor.skip = MagicMock(return_value=mock_cursor)
        mock_cursor.limit = MagicMock(return_value=mock_cursor)

        self.mock_collection.find.return_value = mock_cursor
        self.log_test_debug(f"Setup find mock to return {len(return_value)} documents")

    def setup_insert_one_mock(self, inserted_id: Optional[ObjectId] = None):
        """Setup insert_one mock with specific inserted_id"""
        if inserted_id is None:
            inserted_id = ObjectId()

        mock_result = MagicMock()
        mock_result.inserted_id = inserted_id
        self.mock_collection.insert_one.return_value = mock_result
        self.log_test_debug(f"Setup insert_one mock with inserted_id: {inserted_id}")

    def setup_update_one_mock(self, modified_count: int = 1, matched_count: int = 1):
        """Setup update_one mock with specific counts"""
        mock_result = MagicMock()
        mock_result.modified_count = modified_count
        mock_result.matched_count = matched_count
        self.mock_collection.update_one.return_value = mock_result
        self.log_test_debug(f"Setup update_one mock with modified_count: {modified_count}")

    def setup_delete_one_mock(self, deleted_count: int = 1):
        """Setup delete_one mock with specific count"""
        mock_result = MagicMock()
        mock_result.deleted_count = deleted_count
        self.mock_collection.delete_one.return_value = mock_result
        self.log_test_debug(f"Setup delete_one mock with deleted_count: {deleted_count}")

    def setup_count_documents_mock(self, count: int = 0):
        """Setup count_documents mock with specific count"""
        self.mock_collection.count_documents.return_value = count
        self.log_test_debug(f"Setup count_documents mock to return: {count}")

    # Repository Method Assertion Helpers

    def assert_find_one_called_with(self, expected_filter: Dict[str, Any]):
        """Assert find_one was called with expected filter"""
        self.mock_collection.find_one.assert_called_with(expected_filter)
        self.log_test_debug(f"Verified find_one called with filter: {expected_filter}")

    def assert_insert_one_called_with(self, expected_document: Dict[str, Any]):
        """Assert insert_one was called with expected document"""
        self.mock_collection.insert_one.assert_called_with(expected_document)
        self.log_test_debug("Verified insert_one called with expected document")

    def assert_update_one_called_with(self, expected_filter: Dict[str, Any], expected_update: Dict[str, Any]):
        """Assert update_one was called with expected filter and update"""
        self.mock_collection.update_one.assert_called_with(expected_filter, expected_update)
        self.log_test_debug("Verified update_one called with expected parameters")

    def assert_delete_one_called_with(self, expected_filter: Dict[str, Any]):
        """Assert delete_one was called with expected filter"""
        self.mock_collection.delete_one.assert_called_with(expected_filter)
        self.log_test_debug(f"Verified delete_one called with filter: {expected_filter}")

    def assert_collection_method_not_called(self, method_name: str):
        """Assert that a collection method was not called"""
        method_mock = getattr(self.mock_collection, method_name)
        method_mock.assert_not_called()
        self.log_test_debug(f"Verified {method_name} was not called")

    def get_collection_method_call_count(self, method_name: str) -> int:
        """Get the number of times a collection method was called"""
        method_mock = getattr(self.mock_collection, method_name)
        return method_mock.call_count

    # Repository Result Assertion Helpers

    def assert_document_returned(self, result: Optional[Dict[str, Any]], expected: Dict[str, Any]):
        """Assert that repository returned expected document"""
        assert result is not None, "Expected document to be returned, got None"
        assert result == expected, f"Expected document {expected}, got {result}"
        self.log_test_debug("Document assertion passed")

    def assert_no_document_returned(self, result: Optional[Dict[str, Any]]):
        """Assert that repository returned None"""
        assert result is None, f"Expected None, got document: {result}"
        self.log_test_debug("No document assertion passed")

    def assert_document_list_returned(self, result: List[Dict[str, Any]], expected_count: int):
        """Assert that repository returned list with expected count"""
        assert isinstance(result, list), f"Expected list, got {type(result)}"
        assert len(result) == expected_count, f"Expected {expected_count} documents, got {len(result)}"
        self.log_test_debug(f"Document list assertion passed: {len(result)} documents")

    def assert_document_id_returned(self, result: str):
        """Assert that repository returned valid document ID"""
        assert result is not None, "Expected document ID, got None"
        assert isinstance(result, str), f"Expected string ID, got {type(result)}"
        assert ObjectId.is_valid(result), f"Expected valid ObjectId string, got: {result}"
        self.log_test_debug(f"Document ID assertion passed: {result}")

    def assert_boolean_result(self, result: bool, expected: bool):
        """Assert boolean repository operation result"""
        assert isinstance(result, bool), f"Expected boolean, got {type(result)}"
        assert result == expected, f"Expected {expected}, got {result}"
        self.log_test_debug(f"Boolean assertion passed: {result}")

    def assert_count_result(self, result: int, expected: int):
        """Assert count repository operation result"""
        assert isinstance(result, int), f"Expected integer, got {type(result)}"
        assert result == expected, f"Expected count {expected}, got {result}"
        self.log_test_debug(f"Count assertion passed: {result}")

    # BaseRepository Compliance Testing

    @pytest.mark.skip("Template test - not meant to be run directly")
    def test_base_repository_compliance(self):
        """Test that repository implements all BaseRepository abstract methods"""
        if not self.repository_class:
            pytest.skip("No repository_class specified")

        repository = self.repository_class(self.collection_name)

        # Check that it's a subclass of BaseRepository
        assert issubclass(self.repository_class, BaseRepository), \
            f"{self.repository_class.__name__} must extend BaseRepository"

        # Check that create_indexes is implemented
        assert hasattr(repository, 'create_indexes'), \
            f"{self.repository_class.__name__} must implement create_indexes method"

        # Test create_indexes handles TESTING mode
        with patch.dict(os.environ, {'TESTING': 'true'}):
            try:
                repository.create_indexes()  # Should not raise exception
                self.log_test_debug("create_indexes handles TESTING mode correctly")
            except Exception as e:
                pytest.fail(f"create_indexes should handle TESTING mode gracefully: {e}")

        self.log_test_debug("BaseRepository compliance test passed")

    @pytest.mark.skip("Template test - not meant to be run directly")
    def test_repository_crud_operations(self):
        """Test basic CRUD operations work correctly"""
        if not self.repository_class:
            pytest.skip("No repository_class specified")

        test_doc = self.create_test_document()
        test_id = str(test_doc['_id'])

        # Test create (covered by insert_one mock)
        self.setup_insert_one_mock(test_doc['_id'])
        result_id = self.repository.create(test_doc)
        self.assert_document_id_returned(result_id)

        # Test find_by_id
        self.setup_find_one_mock(test_doc)
        result = self.repository.find_by_id(test_id)
        self.assert_document_returned(result, test_doc)

        # Test find_one
        filter_dict = {'test_field': 'test_value'}
        self.setup_find_one_mock(test_doc)
        result = self.repository.find_one(filter_dict)
        self.assert_document_returned(result, test_doc)

        # Test update_by_id
        self.setup_update_one_mock(modified_count=1)
        update_data = {'test_field': 'updated_value'}
        result = self.repository.update_by_id(test_id, update_data)
        self.assert_boolean_result(result, True)

        # Test delete_by_id
        self.setup_delete_one_mock(deleted_count=1)
        result = self.repository.delete_by_id(test_id)
        self.assert_boolean_result(result, True)

        # Test count
        self.setup_count_documents_mock(count=5)
        result = self.repository.count()
        self.assert_count_result(result, 5)

        self.log_test_debug("CRUD operations test passed")

    # ObjectId Testing Utilities

    def create_valid_object_id(self) -> ObjectId:
        """Create a valid ObjectId for testing"""
        return ObjectId()

    def create_valid_object_id_string(self) -> str:
        """Create a valid ObjectId string for testing"""
        return str(ObjectId())

    def create_invalid_object_id_string(self) -> str:
        """Create an invalid ObjectId string for testing"""
        return "invalid_object_id"

    def assert_object_id_valid(self, object_id_str: str):
        """Assert that string is a valid ObjectId"""
        assert ObjectId.is_valid(object_id_str), f"Expected valid ObjectId, got: {object_id_str}"

    def assert_object_id_invalid(self, object_id_str: str):
        """Assert that string is not a valid ObjectId"""
        assert not ObjectId.is_valid(object_id_str), f"Expected invalid ObjectId, but was valid: {object_id_str}"

    # Performance and Health Monitoring

    def get_smart_fixture_performance_report(self) -> Dict[str, Any]:
        """Get Smart Fixture performance report for this test"""
        return performance_monitor.get_performance_report()

    def get_system_health_report(self) -> Dict[str, Any]:
        """Get system health report including Smart Fixtures"""
        return get_system_health()


class RepositoryTestMixin:
    """
    Mixin class providing additional utilities for repository testing
    Can be used with existing test classes that can't extend BaseRepositoryTest
    """

    def setup_mongodb_mocks(self):
        """Setup basic MongoDB mocking"""
        mock_db = MagicMock()
        mock_collection = MagicMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)
        return mock_db, mock_collection

    def create_mock_insert_result(self, inserted_id: ObjectId = None):
        """Create mock insert result"""
        if inserted_id is None:
            inserted_id = ObjectId()
        mock_result = MagicMock()
        mock_result.inserted_id = inserted_id
        return mock_result

    def create_mock_update_result(self, modified_count: int = 1, matched_count: int = 1):
        """Create mock update result"""
        mock_result = MagicMock()
        mock_result.modified_count = modified_count
        mock_result.matched_count = matched_count
        return mock_result

    def create_mock_delete_result(self, deleted_count: int = 1):
        """Create mock delete result"""
        mock_result = MagicMock()
        mock_result.deleted_count = deleted_count
        return mock_result