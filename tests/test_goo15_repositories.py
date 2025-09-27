"""
Comprehensive tests for GOO-15 Donation System repositories.

Tests cover:
- BatchOperationRepository: Batch operation data access
- BatchDonationRepository: Batch donation data access
- Database operations with mocked MongoDB collections
- Index creation and query optimization
- Error handling and edge cases

Author: Claude Code Assistant
Date: 2025-09-27
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
from datetime import datetime, timezone
from bson import ObjectId
import os

# Import repositories to test
from app.donations.repositories.batch_operation_repository import BatchOperationRepository
from app.donations.repositories.batch_donation_repository import BatchDonationRepository
from app.donations.models.batch_operation import BatchOperation, BatchOperationType
from app.donations.models.batch_donation import BatchDonation


class TestBatchOperationRepository:
    """Test suite for BatchOperationRepository."""

    @pytest.fixture
    def mock_collection(self):
        """Mock MongoDB collection."""
        collection = MagicMock()
        collection.name = "batch_operations"
        return collection

    @pytest.fixture
    def batch_operation_repo(self, mock_collection):
        """Create BatchOperationRepository with mocked collection."""
        with patch('app.donations.repositories.batch_operation_repository.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_db.batch_operations = mock_collection
            mock_get_db.return_value = mock_db

            repo = BatchOperationRepository()
            repo.collection = mock_collection
            return repo

    @pytest.fixture
    def app(self):
        """Create Flask app for testing."""
        with patch.dict(os.environ, {'TESTING': 'true'}):
            from app import create_app
            app = create_app()
            return app

    def test_create_batch_operation_success(self, batch_operation_repo, mock_collection, app):
        """Test successful batch operation creation."""
        # Arrange
        operation_type = BatchOperationType.DONATIONS
        total_items = 100
        created_by = "admin_123"

        mock_collection.insert_one.return_value = MagicMock(inserted_id=ObjectId())

        # Act
        with app.app_context():
            batch_operation = batch_operation_repo.create(
                operation_type=operation_type,
                total_items=total_items,
                created_by=created_by
            )

        # Assert
        assert batch_operation is not None
        assert batch_operation.operation_type == operation_type
        assert batch_operation.total_items == total_items
        assert batch_operation.created_by == created_by
        assert batch_operation.status == "pending"
        assert batch_operation.processed_items == 0
        assert batch_operation.failed_items == 0

        mock_collection.insert_one.assert_called_once()
        inserted_doc = mock_collection.insert_one.call_args[0][0]
        assert inserted_doc['operation_type'] == operation_type.value
        assert inserted_doc['total_items'] == total_items
        assert inserted_doc['created_by'] == created_by

    def test_create_batch_operation_validation_error(self, batch_operation_repo, app):
        """Test batch operation creation with validation errors."""
        with app.app_context():
            # Test invalid operation type
            with pytest.raises(ValueError, match="Invalid operation type"):
                batch_operation_repo.create(
                    operation_type="invalid_type",
                    total_items=100,
                    created_by="admin_123"
                )

            # Test zero total items
            with pytest.raises(ValueError, match="Total items must be positive"):
                batch_operation_repo.create(
                    operation_type=BatchOperationType.DONATIONS,
                    total_items=0,
                    created_by="admin_123"
                )

            # Test missing created_by
            with pytest.raises(ValueError, match="created_by is required"):
                batch_operation_repo.create(
                    operation_type=BatchOperationType.DONATIONS,
                    total_items=100,
                    created_by=""
                )

    def test_find_by_id_success(self, batch_operation_repo, mock_collection, app):
        """Test successful batch operation retrieval by ID."""
        # Arrange
        operation_id = str(ObjectId())
        mock_doc = {
            '_id': ObjectId(operation_id),
            'operation_type': 'donations',
            'total_items': 100,
            'processed_items': 50,
            'failed_items': 5,
            'status': 'processing',
            'created_by': 'admin_123',
            'created_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc),
            'metadata': {'batch_name': 'Test Batch'}
        }

        mock_collection.find_one.return_value = mock_doc

        # Act
        with app.app_context():
            batch_operation = batch_operation_repo.find_by_id(operation_id)

        # Assert
        assert batch_operation is not None
        assert batch_operation.id == operation_id
        assert batch_operation.operation_type == BatchOperationType.DONATIONS
        assert batch_operation.total_items == 100
        assert batch_operation.processed_items == 50
        assert batch_operation.failed_items == 5
        assert batch_operation.status == 'processing'
        assert batch_operation.created_by == 'admin_123'

        mock_collection.find_one.assert_called_once_with({'_id': ObjectId(operation_id)})

    def test_find_by_id_not_found(self, batch_operation_repo, mock_collection, app):
        """Test batch operation retrieval when not found."""
        # Arrange
        operation_id = str(ObjectId())
        mock_collection.find_one.return_value = None

        # Act
        with app.app_context():
            batch_operation = batch_operation_repo.find_by_id(operation_id)

        # Assert
        assert batch_operation is None
        mock_collection.find_one.assert_called_once_with({'_id': ObjectId(operation_id)})

    def test_update_progress_success(self, batch_operation_repo, mock_collection, app):
        """Test successful batch operation progress update."""
        # Arrange
        operation_id = str(ObjectId())
        processed_items = 75
        failed_items = 3

        mock_collection.update_one.return_value = MagicMock(modified_count=1)

        # Act
        with app.app_context():
            success = batch_operation_repo.update_progress(
                operation_id=operation_id,
                processed_items=processed_items,
                failed_items=failed_items
            )

        # Assert
        assert success is True

        mock_collection.update_one.assert_called_once()
        call_args = mock_collection.update_one.call_args

        # Check filter
        assert call_args[0][0] == {'_id': ObjectId(operation_id)}

        # Check update document
        update_doc = call_args[0][1]
        assert update_doc['$set']['processed_items'] == processed_items
        assert update_doc['$set']['failed_items'] == failed_items
        assert 'updated_at' in update_doc['$set']

    def test_update_status_success(self, batch_operation_repo, mock_collection, app):
        """Test successful batch operation status update."""
        # Arrange
        operation_id = str(ObjectId())
        new_status = "completed"

        mock_collection.update_one.return_value = MagicMock(modified_count=1)

        # Act
        with app.app_context():
            success = batch_operation_repo.update_status(
                operation_id=operation_id,
                status=new_status
            )

        # Assert
        assert success is True

        mock_collection.update_one.assert_called_once()
        call_args = mock_collection.update_one.call_args

        # Check filter
        assert call_args[0][0] == {'_id': ObjectId(operation_id)}

        # Check update document
        update_doc = call_args[0][1]
        assert update_doc['$set']['status'] == new_status
        assert 'updated_at' in update_doc['$set']

    def test_find_by_status_with_pagination(self, batch_operation_repo, mock_collection, app):
        """Test finding batch operations by status with pagination."""
        # Arrange
        status = "processing"
        page = 2
        per_page = 10

        mock_docs = [
            {
                '_id': ObjectId(),
                'operation_type': 'donations',
                'status': 'processing',
                'total_items': 100,
                'processed_items': 30,
                'failed_items': 2,
                'created_by': 'admin_123',
                'created_at': datetime.now(timezone.utc),
                'updated_at': datetime.now(timezone.utc)
            }
        ]

        mock_collection.find.return_value.skip.return_value.limit.return_value = mock_docs
        mock_collection.count_documents.return_value = 25

        # Act
        with app.app_context():
            operations, total_count = batch_operation_repo.find_by_status(
                status=status,
                page=page,
                per_page=per_page
            )

        # Assert
        assert len(operations) == 1
        assert total_count == 25
        assert operations[0].status == 'processing'

        # Verify pagination
        skip_count = (page - 1) * per_page
        mock_collection.find.assert_called_once_with({'status': status})
        mock_collection.find.return_value.skip.assert_called_once_with(skip_count)
        mock_collection.find.return_value.skip.return_value.limit.assert_called_once_with(per_page)

    def test_get_statistics_success(self, batch_operation_repo, mock_collection, app):
        """Test getting batch operation statistics."""
        # Arrange
        start_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(2024, 12, 31, tzinfo=timezone.utc)

        mock_aggregation_result = [
            {
                '_id': 'completed',
                'count': 150,
                'total_items': 15000,
                'avg_items': 100.0
            },
            {
                '_id': 'processing',
                'count': 5,
                'total_items': 500,
                'avg_items': 100.0
            },
            {
                '_id': 'failed',
                'count': 2,
                'total_items': 200,
                'avg_items': 100.0
            }
        ]

        mock_collection.aggregate.return_value = mock_aggregation_result

        # Act
        with app.app_context():
            stats = batch_operation_repo.get_statistics(start_date, end_date)

        # Assert
        assert 'by_status' in stats
        assert 'total_operations' in stats
        assert 'total_items_processed' in stats

        assert stats['total_operations'] == 157  # 150 + 5 + 2
        assert stats['total_items_processed'] == 15700  # 15000 + 500 + 200

        # Check aggregation pipeline call
        mock_collection.aggregate.assert_called_once()
        pipeline = mock_collection.aggregate.call_args[0][0]

        # Verify date filtering stage
        match_stage = pipeline[0]
        assert match_stage['$match']['created_at']['$gte'] == start_date
        assert match_stage['$match']['created_at']['$lte'] == end_date

    def test_create_indexes_not_in_testing(self, batch_operation_repo, mock_collection):
        """Test index creation when not in testing mode."""
        with patch.dict(os.environ, {'TESTING': 'false'}):
            # Act
            batch_operation_repo.create_indexes()

            # Assert
            mock_collection.create_index.assert_called()

            # Verify compound indexes are created
            call_args_list = mock_collection.create_index.call_args_list
            assert len(call_args_list) >= 3  # At least status, created_by, and compound indexes

    def test_create_indexes_skipped_in_testing(self, batch_operation_repo, mock_collection):
        """Test index creation is skipped in testing mode."""
        with patch.dict(os.environ, {'TESTING': 'true'}):
            # Act
            batch_operation_repo.create_indexes()

            # Assert
            mock_collection.create_index.assert_not_called()


class TestBatchDonationRepository:
    """Test suite for BatchDonationRepository."""

    @pytest.fixture
    def mock_collection(self):
        """Mock MongoDB collection."""
        collection = MagicMock()
        collection.name = "batch_donations"
        return collection

    @pytest.fixture
    def batch_donation_repo(self, mock_collection):
        """Create BatchDonationRepository with mocked collection."""
        with patch('app.donations.repositories.batch_donation_repository.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_db.batch_donations = mock_collection
            mock_get_db.return_value = mock_db

            repo = BatchDonationRepository()
            repo.collection = mock_collection
            return repo

    @pytest.fixture
    def app(self):
        """Create Flask app for testing."""
        with patch.dict(os.environ, {'TESTING': 'true'}):
            from app import create_app
            app = create_app()
            return app

    def test_create_batch_donations_success(self, batch_donation_repo, mock_collection, app):
        """Test successful batch donations creation."""
        # Arrange
        batch_operation_id = str(ObjectId())
        donations_data = [
            {
                'donor_user_id': 'user_123',
                'onlus_id': 'onlus_456',
                'amount': 25.50,
                'currency': 'EUR'
            },
            {
                'donor_user_id': 'user_789',
                'onlus_id': 'onlus_456',
                'amount': 50.00,
                'currency': 'EUR'
            }
        ]

        mock_collection.insert_many.return_value = MagicMock(
            inserted_ids=[ObjectId(), ObjectId()]
        )

        # Act
        with app.app_context():
            created_count = batch_donation_repo.create_batch_donations(
                batch_operation_id=batch_operation_id,
                donations_data=donations_data
            )

        # Assert
        assert created_count == 2

        mock_collection.insert_many.assert_called_once()
        inserted_docs = mock_collection.insert_many.call_args[0][0]

        assert len(inserted_docs) == 2
        assert inserted_docs[0]['batch_operation_id'] == batch_operation_id
        assert inserted_docs[0]['donor_user_id'] == 'user_123'
        assert inserted_docs[0]['amount'] == 25.50
        assert inserted_docs[0]['status'] == 'pending'

        assert inserted_docs[1]['batch_operation_id'] == batch_operation_id
        assert inserted_docs[1]['donor_user_id'] == 'user_789'
        assert inserted_docs[1]['amount'] == 50.00
        assert inserted_docs[1]['status'] == 'pending'

    def test_create_batch_donations_validation_error(self, batch_donation_repo, app):
        """Test batch donations creation with validation errors."""
        with app.app_context():
            # Test empty batch operation ID
            with pytest.raises(ValueError, match="batch_operation_id is required"):
                batch_donation_repo.create_batch_donations(
                    batch_operation_id="",
                    donations_data=[{'amount': 25.0}]
                )

            # Test empty donations data
            with pytest.raises(ValueError, match="donations_data cannot be empty"):
                batch_donation_repo.create_batch_donations(
                    batch_operation_id=str(ObjectId()),
                    donations_data=[]
                )

            # Test missing required field
            with pytest.raises(ValueError, match="Missing required field"):
                batch_donation_repo.create_batch_donations(
                    batch_operation_id=str(ObjectId()),
                    donations_data=[{'amount': 25.0}]  # Missing donor_user_id
                )

    def test_find_by_batch_id_success(self, batch_donation_repo, mock_collection, app):
        """Test successful batch donations retrieval by batch ID."""
        # Arrange
        batch_operation_id = str(ObjectId())

        mock_docs = [
            {
                '_id': ObjectId(),
                'batch_operation_id': batch_operation_id,
                'donor_user_id': 'user_123',
                'onlus_id': 'onlus_456',
                'amount': 25.50,
                'currency': 'EUR',
                'status': 'pending',
                'created_at': datetime.now(timezone.utc),
                'updated_at': datetime.now(timezone.utc)
            },
            {
                '_id': ObjectId(),
                'batch_operation_id': batch_operation_id,
                'donor_user_id': 'user_789',
                'onlus_id': 'onlus_456',
                'amount': 50.00,
                'currency': 'EUR',
                'status': 'completed',
                'created_at': datetime.now(timezone.utc),
                'updated_at': datetime.now(timezone.utc)
            }
        ]

        mock_collection.find.return_value = mock_docs

        # Act
        with app.app_context():
            donations = batch_donation_repo.find_by_batch_id(batch_operation_id)

        # Assert
        assert len(donations) == 2

        assert donations[0].batch_operation_id == batch_operation_id
        assert donations[0].donor_user_id == 'user_123'
        assert donations[0].amount == 25.50
        assert donations[0].status == 'pending'

        assert donations[1].batch_operation_id == batch_operation_id
        assert donations[1].donor_user_id == 'user_789'
        assert donations[1].amount == 50.00
        assert donations[1].status == 'completed'

        mock_collection.find.assert_called_once_with({'batch_operation_id': batch_operation_id})

    def test_update_status_success(self, batch_donation_repo, mock_collection, app):
        """Test successful batch donation status update."""
        # Arrange
        donation_id = str(ObjectId())
        new_status = "completed"
        error_message = None

        mock_collection.update_one.return_value = MagicMock(modified_count=1)

        # Act
        with app.app_context():
            success = batch_donation_repo.update_status(
                donation_id=donation_id,
                status=new_status,
                error_message=error_message
            )

        # Assert
        assert success is True

        mock_collection.update_one.assert_called_once()
        call_args = mock_collection.update_one.call_args

        # Check filter
        assert call_args[0][0] == {'_id': ObjectId(donation_id)}

        # Check update document
        update_doc = call_args[0][1]
        assert update_doc['$set']['status'] == new_status
        assert 'updated_at' in update_doc['$set']
        assert '$unset' not in update_doc  # No error message to unset

    def test_update_status_with_error_message(self, batch_donation_repo, mock_collection, app):
        """Test batch donation status update with error message."""
        # Arrange
        donation_id = str(ObjectId())
        new_status = "failed"
        error_message = "Insufficient balance"

        mock_collection.update_one.return_value = MagicMock(modified_count=1)

        # Act
        with app.app_context():
            success = batch_donation_repo.update_status(
                donation_id=donation_id,
                status=new_status,
                error_message=error_message
            )

        # Assert
        assert success is True

        mock_collection.update_one.assert_called_once()
        call_args = mock_collection.update_one.call_args

        # Check update document
        update_doc = call_args[0][1]
        assert update_doc['$set']['status'] == new_status
        assert update_doc['$set']['error_message'] == error_message
        assert 'updated_at' in update_doc['$set']

    def test_get_status_summary_success(self, batch_donation_repo, mock_collection, app):
        """Test getting batch donation status summary."""
        # Arrange
        batch_operation_id = str(ObjectId())

        mock_aggregation_result = [
            {'_id': 'pending', 'count': 50, 'total_amount': 1250.00},
            {'_id': 'completed', 'count': 40, 'total_amount': 2000.00},
            {'_id': 'failed', 'count': 10, 'total_amount': 250.00}
        ]

        mock_collection.aggregate.return_value = mock_aggregation_result

        # Act
        with app.app_context():
            summary = batch_donation_repo.get_status_summary(batch_operation_id)

        # Assert
        assert 'pending' in summary
        assert 'completed' in summary
        assert 'failed' in summary

        assert summary['pending']['count'] == 50
        assert summary['pending']['total_amount'] == 1250.00
        assert summary['completed']['count'] == 40
        assert summary['completed']['total_amount'] == 2000.00
        assert summary['failed']['count'] == 10
        assert summary['failed']['total_amount'] == 250.00

        # Verify aggregation pipeline
        mock_collection.aggregate.assert_called_once()
        pipeline = mock_collection.aggregate.call_args[0][0]

        # Check match stage
        match_stage = pipeline[0]
        assert match_stage['$match']['batch_operation_id'] == batch_operation_id

        # Check group stage
        group_stage = pipeline[1]
        assert group_stage['$group']['_id'] == '$status'

    def test_bulk_update_status_success(self, batch_donation_repo, mock_collection, app):
        """Test bulk status update for multiple donations."""
        # Arrange
        donation_ids = [str(ObjectId()), str(ObjectId()), str(ObjectId())]
        new_status = "processed"

        mock_collection.update_many.return_value = MagicMock(modified_count=3)

        # Act
        with app.app_context():
            updated_count = batch_donation_repo.bulk_update_status(
                donation_ids=donation_ids,
                status=new_status
            )

        # Assert
        assert updated_count == 3

        mock_collection.update_many.assert_called_once()
        call_args = mock_collection.update_many.call_args

        # Check filter
        filter_doc = call_args[0][0]
        expected_object_ids = [ObjectId(id_str) for id_str in donation_ids]
        assert filter_doc == {'_id': {'$in': expected_object_ids}}

        # Check update document
        update_doc = call_args[0][1]
        assert update_doc['$set']['status'] == new_status
        assert 'updated_at' in update_doc['$set']

    def test_find_failed_donations(self, batch_donation_repo, mock_collection, app):
        """Test finding failed donations for retry."""
        # Arrange
        batch_operation_id = str(ObjectId())

        mock_docs = [
            {
                '_id': ObjectId(),
                'batch_operation_id': batch_operation_id,
                'donor_user_id': 'user_123',
                'status': 'failed',
                'error_message': 'Insufficient balance',
                'retry_count': 2
            }
        ]

        mock_collection.find.return_value = mock_docs

        # Act
        with app.app_context():
            failed_donations = batch_donation_repo.find_failed_donations(
                batch_operation_id=batch_operation_id
            )

        # Assert
        assert len(failed_donations) == 1
        assert failed_donations[0].status == 'failed'
        assert failed_donations[0].error_message == 'Insufficient balance'
        assert failed_donations[0].retry_count == 2

        mock_collection.find.assert_called_once_with({
            'batch_operation_id': batch_operation_id,
            'status': 'failed'
        })

    def test_create_indexes_not_in_testing(self, batch_donation_repo, mock_collection):
        """Test index creation when not in testing mode."""
        with patch.dict(os.environ, {'TESTING': 'false'}):
            # Act
            batch_donation_repo.create_indexes()

            # Assert
            mock_collection.create_index.assert_called()

            # Verify compound indexes are created
            call_args_list = mock_collection.create_index.call_args_list
            assert len(call_args_list) >= 4  # batch_operation_id, status, and compound indexes

    def test_create_indexes_skipped_in_testing(self, batch_donation_repo, mock_collection):
        """Test index creation is skipped in testing mode."""
        with patch.dict(os.environ, {'TESTING': 'true'}):
            # Act
            batch_donation_repo.create_indexes()

            # Assert
            mock_collection.create_index.assert_not_called()


class TestRepositoryIntegration:
    """Integration tests for repository interactions."""

    @pytest.fixture
    def app(self):
        """Create Flask app for testing."""
        with patch.dict(os.environ, {'TESTING': 'true'}):
            from app import create_app
            app = create_app()
            return app

    def test_repository_initialization(self, app):
        """Test that repositories can be initialized correctly."""
        with app.app_context():
            # Test BatchOperationRepository initialization
            batch_op_repo = BatchOperationRepository()
            assert batch_op_repo is not None

            # Test BatchDonationRepository initialization
            batch_donation_repo = BatchDonationRepository()
            assert batch_donation_repo is not None

    @patch('app.donations.repositories.batch_operation_repository.get_db')
    @patch('app.donations.repositories.batch_donation_repository.get_db')
    def test_repository_database_connection_mocking(self, mock_get_db_donation, mock_get_db_operation, app):
        """Test that database connections are properly mocked."""
        # Arrange
        mock_db = MagicMock()
        mock_get_db_operation.return_value = mock_db
        mock_get_db_donation.return_value = mock_db

        with app.app_context():
            # Act
            batch_op_repo = BatchOperationRepository()
            batch_donation_repo = BatchDonationRepository()

            # Assert
            assert batch_op_repo.collection == mock_db.batch_operations
            assert batch_donation_repo.collection == mock_db.batch_donations

    def test_repository_error_handling(self, app):
        """Test repository error handling for database operations."""
        with app.app_context():
            with patch('app.donations.repositories.batch_operation_repository.get_db') as mock_get_db:
                # Arrange - Simulate database connection error
                mock_get_db.side_effect = Exception("Database connection failed")

                # Act & Assert
                with pytest.raises(Exception, match="Database connection failed"):
                    BatchOperationRepository()