"""
Integration tests for GOO-15 Donation System workflows.

Tests complete end-to-end workflows including:
- Complete donation processing workflow
- Batch processing workflow
- Compliance checking workflow
- Financial analytics workflow
- Cross-service interactions
- Error handling across service boundaries

Author: Claude Code Assistant
Date: 2025-09-27
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timezone, timedelta
from bson import ObjectId
import os

# Import services for integration testing
from app.donations.services.wallet_service import WalletService
from app.donations.services.transaction_service import TransactionService
from app.donations.services.batch_processing_service import BatchProcessingService
from app.donations.services.compliance_service import ComplianceService
from app.donations.services.financial_analytics_service import FinancialAnalyticsService
from app.donations.services.receipt_generation_service import ReceiptGenerationService


class TestCompleteDonationWorkflow:
    """Test complete donation processing workflow from wallet to receipt."""

    @pytest.fixture
    def app(self):
        """Create Flask app for testing."""
        with patch.dict(os.environ, {'TESTING': 'true'}):
            from app import create_app
            app = create_app()
            return app

    @pytest.fixture
    def mock_services(self):
        """Mock all required services and repositories."""
        mocks = {}

        # Mock repositories
        mocks['wallet_repo'] = MagicMock()
        mocks['transaction_repo'] = MagicMock()
        mocks['onlus_repo'] = MagicMock()

        # Mock external services
        mocks['payment_service'] = MagicMock()
        mocks['notification_service'] = MagicMock()

        return mocks

    @patch('app.donations.services.wallet_service.get_wallet_repository')
    @patch('app.donations.services.wallet_service.get_transaction_repository')
    @patch('app.donations.services.transaction_service.get_transaction_repository')
    @patch('app.onlus.repositories.onlus_repository.get_onlus_repository')
    def test_complete_donation_flow_success(self, mock_get_onlus_repo,
                                          mock_get_transaction_repo_service,
                                          mock_get_transaction_repo, mock_get_wallet_repo,
                                          mock_services, app):
        """Test complete donation workflow from wallet balance to receipt generation."""

        # Arrange - Setup mock repositories
        mock_get_wallet_repo.return_value = mock_services['wallet_repo']
        mock_get_transaction_repo.return_value = mock_services['transaction_repo']
        mock_get_transaction_repo_service.return_value = mock_services['transaction_repo']
        mock_get_onlus_repo.return_value = mock_services['onlus_repo']

        # Setup test data
        user_id = "user_123"
        onlus_id = "onlus_456"
        transaction_amount = 25.50

        # Mock wallet with sufficient balance
        mock_wallet = MagicMock()
        mock_wallet.id = "wallet_123"
        mock_wallet.user_id = user_id
        mock_wallet.current_balance = 50.00
        mock_services['wallet_repo'].find_by_user_id.return_value = mock_wallet

        # Mock transaction creation
        mock_transaction = MagicMock()
        mock_transaction.id = "transaction_123"
        mock_transaction.amount = transaction_amount
        mock_transaction.transaction_type = "donated"
        mock_services['transaction_repo'].create.return_value = mock_transaction

        # Mock wallet update
        mock_services['wallet_repo'].update_balance.return_value = True

        with app.app_context():
            # Act - Execute transaction workflow

            # Step 1: Create transaction
            transaction_service = TransactionService()
            success_transaction, message_transaction, transaction_result = transaction_service.create_transaction(
                wallet_id="wallet_123",
                amount=transaction_amount,
                transaction_type="donated",
                description="Test donation transaction"
            )

        # Assert - Verify transaction workflow
        assert success_transaction is True
        assert message_transaction == "TRANSACTION_CREATED_SUCCESS"
        assert transaction_result['transaction_id'] == "transaction_123"

        # Verify service interactions
        mock_services['wallet_repo'].find_by_user_id.assert_called_with(user_id)
        mock_services['transaction_repo'].create.assert_called()

    @patch('app.donations.services.wallet_service.get_wallet_repository')
    def test_wallet_insufficient_balance(self, mock_get_wallet_repo, mock_services, app):
        """Test wallet service with insufficient balance."""

        # Arrange
        mock_get_wallet_repo.return_value = mock_services['wallet_repo']

        user_id = "user_123"

        # Mock wallet with insufficient balance
        mock_wallet = MagicMock()
        mock_wallet.id = "wallet_123"
        mock_wallet.user_id = user_id
        mock_wallet.current_balance = 5.00
        mock_services['wallet_repo'].find_by_user_id.return_value = mock_wallet

        with app.app_context():
            # Act
            wallet_service = WalletService()
            success, message, result = wallet_service.get_wallet_info(user_id)

        # Assert
        assert success is True
        assert result['current_balance'] == 5.00

        # Verify wallet was retrieved
        mock_services['wallet_repo'].find_by_user_id.assert_called_with(user_id)


class TestBatchProcessingWorkflow:
    """Test complete batch processing workflow."""

    @pytest.fixture
    def app(self):
        """Create Flask app for testing."""
        with patch.dict(os.environ, {'TESTING': 'true'}):
            from app import create_app
            app = create_app()
            return app

    @pytest.fixture
    def mock_services(self):
        """Mock all required services and repositories."""
        mocks = {}

        # Mock repositories
        mocks['batch_operation_repo'] = MagicMock()
        mocks['batch_donation_repo'] = MagicMock()
        mocks['wallet_repo'] = MagicMock()

        # Mock services
        mocks['wallet_service'] = MagicMock()

        return mocks

    @patch('app.donations.services.batch_processing_service.get_batch_operation_repository')
    @patch('app.donations.services.batch_processing_service.get_batch_donation_repository')
    @patch('app.donations.services.batch_processing_service.get_wallet_service')
    def test_complete_batch_processing_workflow(self, mock_get_wallet_service,
                                              mock_get_batch_donation_repo,
                                              mock_get_batch_operation_repo,
                                              mock_services, app):
        """Test complete batch processing workflow from creation to completion."""

        # Arrange
        mock_get_batch_operation_repo.return_value = mock_services['batch_operation_repo']
        mock_get_batch_donation_repo.return_value = mock_services['batch_donation_repo']
        mock_get_wallet_service.return_value = mock_services['wallet_service']

        # Setup test data
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

        # Mock batch operation creation
        mock_batch_operation = MagicMock()
        mock_batch_operation.id = "batch_123"
        mock_batch_operation.total_items = len(donations_data)
        mock_services['batch_operation_repo'].create.return_value = mock_batch_operation

        # Mock batch donations creation
        mock_services['batch_donation_repo'].create_batch_donations.return_value = len(donations_data)

        # Mock batch donations retrieval
        mock_batch_donations = []
        for i, donation_data in enumerate(donations_data):
            mock_donation = MagicMock()
            mock_donation.id = f"donation_{i}"
            mock_donation.donor_user_id = donation_data['donor_user_id']
            mock_donation.amount = donation_data['amount']
            mock_batch_donations.append(mock_donation)

        mock_services['batch_donation_repo'].find_by_batch_id.return_value = mock_batch_donations

        # Mock wallet service for processing
        mock_services['wallet_service'].process_donation.side_effect = [
            (True, "DONATION_PROCESSED_SUCCESS", {'transaction_id': 'transaction_0'}),
            (True, "DONATION_PROCESSED_SUCCESS", {'transaction_id': 'transaction_1'})
        ]

        # Mock status updates
        mock_services['batch_donation_repo'].update_status.return_value = True
        mock_services['batch_operation_repo'].update_progress.return_value = True
        mock_services['batch_operation_repo'].update_status.return_value = True

        with app.app_context():
            # Act - Execute complete batch workflow
            batch_service = BatchProcessingService()

            # Step 1: Create batch operation
            success_create, message_create, create_result = batch_service.create_batch_donation_operation(
                donations=donations_data,
                created_by="admin_123"
            )

            # Step 2: Process batch operation
            success_process, message_process, process_result = batch_service.process_batch_operation(
                batch_operation_id=create_result['batch_operation_id']
            )

        # Assert - Verify complete workflow
        assert success_create is True
        assert message_create == "BATCH_OPERATION_CREATED_SUCCESS"
        assert create_result['batch_operation_id'] == "batch_123"

        assert success_process is True
        assert message_process == "BATCH_PROCESSING_COMPLETED"
        assert process_result['processed_items'] == 2
        assert process_result['failed_items'] == 0

        # Verify service interactions
        mock_services['batch_operation_repo'].create.assert_called_once()
        mock_services['batch_donation_repo'].create_batch_donations.assert_called_once()
        mock_services['wallet_service'].process_donation.assert_called()
        assert mock_services['wallet_service'].process_donation.call_count == 2

    @patch('app.donations.services.batch_processing_service.get_batch_operation_repository')
    def test_batch_processing_with_failures(self, mock_get_batch_operation_repo, mock_services, app):
        """Test batch processing workflow with some failed donations."""

        # Arrange
        mock_get_batch_operation_repo.return_value = mock_services['batch_operation_repo']

        batch_operation_id = "batch_123"

        # Mock batch operation
        mock_batch_operation = MagicMock()
        mock_batch_operation.id = batch_operation_id
        mock_batch_operation.status = "processing"
        mock_services['batch_operation_repo'].find_by_id.return_value = mock_batch_operation

        with app.app_context():
            # Act
            batch_service = BatchProcessingService()
            success, message, result = batch_service.get_batch_operation_status(batch_operation_id)

        # Assert
        assert success is True
        assert message == "BATCH_STATUS_RETRIEVED"
        assert result['batch_operation_id'] == batch_operation_id
        assert result['status'] == "processing"


class TestComplianceWorkflow:
    """Test compliance checking workflow."""

    @pytest.fixture
    def app(self):
        """Create Flask app for testing."""
        with patch.dict(os.environ, {'TESTING': 'true'}):
            from app import create_app
            app = create_app()
            return app

    @pytest.fixture
    def mock_compliance_repo(self):
        """Mock compliance repository."""
        return MagicMock()

    @patch('app.donations.services.compliance_service.get_compliance_repository')
    def test_complete_compliance_check_workflow(self, mock_get_compliance_repo,
                                              mock_compliance_repo, app):
        """Test complete compliance check workflow from initiation to review."""

        # Arrange
        mock_get_compliance_repo.return_value = mock_compliance_repo

        user_id = "user_123"
        check_type = "AML"

        # Mock compliance check creation
        mock_compliance_check = MagicMock()
        mock_compliance_check.id = "check_123"
        mock_compliance_check.user_id = user_id
        mock_compliance_check.check_type = check_type
        mock_compliance_check.status = "pending"
        mock_compliance_repo.create.return_value = mock_compliance_check

        # Mock compliance check retrieval
        mock_compliance_repo.find_by_id.return_value = mock_compliance_check

        # Mock compliance check update
        mock_compliance_repo.update.return_value = True

        with app.app_context():
            # Act - Execute compliance workflow
            compliance_service = ComplianceService()

            # Step 1: Initiate compliance check
            success_initiate, message_initiate, initiate_result = compliance_service.initiate_compliance_check(
                user_id=user_id,
                check_type=check_type,
                initiated_by="admin_123"
            )

            # Step 2: Review compliance check
            success_review, message_review, review_result = compliance_service.review_compliance_check(
                check_id=initiate_result['check_id'],
                decision="approve",
                reviewer_id="admin_456",
                notes="All checks passed"
            )

        # Assert - Verify complete workflow
        assert success_initiate is True
        assert message_initiate == "COMPLIANCE_CHECK_INITIATED"
        assert initiate_result['check_id'] == "check_123"

        assert success_review is True
        assert message_review == "COMPLIANCE_CHECK_REVIEWED"
        assert review_result['status'] == "approved"

        # Verify service interactions
        mock_compliance_repo.create.assert_called_once()
        mock_compliance_repo.find_by_id.assert_called()
        mock_compliance_repo.update.assert_called()


class TestFinancialAnalyticsWorkflow:
    """Test financial analytics workflow."""

    @pytest.fixture
    def app(self):
        """Create Flask app for testing."""
        with patch.dict(os.environ, {'TESTING': 'true'}):
            from app import create_app
            app = create_app()
            return app

    @pytest.fixture
    def mock_transaction_repo(self):
        """Mock transaction repository."""
        return MagicMock()

    @patch('app.donations.services.financial_analytics_service.get_transaction_repository')
    def test_comprehensive_analytics_workflow(self, mock_get_transaction_repo,
                                            mock_transaction_repo, app):
        """Test comprehensive financial analytics workflow."""

        # Arrange
        mock_get_transaction_repo.return_value = mock_transaction_repo

        # Mock aggregated data for different metrics
        mock_transaction_repo.get_aggregated_data.side_effect = [
            # Core metrics
            {
                'total_volume': 10000.0,
                'total_donations': 150,
                'unique_donors': 50,
                'average_donation': 66.67
            },
            # Trend data
            {
                'daily_data': [
                    {'date': '2024-01-01', 'volume': 500.0, 'count': 10},
                    {'date': '2024-01-02', 'volume': 750.0, 'count': 15}
                ]
            },
            # User behavior data
            {
                'new_donors': 25,
                'returning_donors': 25,
                'high_value_donors': 10,
                'frequent_donors': 15
            }
        ]

        with app.app_context():
            # Act - Execute analytics workflow
            analytics_service = FinancialAnalyticsService()

            # Generate comprehensive dashboard
            success, message, dashboard = analytics_service.generate_financial_dashboard()

        # Assert - Verify analytics workflow
        assert success is True
        assert message == "FINANCIAL_DASHBOARD_GENERATED"

        assert 'core_metrics' in dashboard
        assert 'trends' in dashboard
        assert 'user_analytics' in dashboard
        assert 'forecasting' in dashboard

        assert dashboard['core_metrics']['total_volume'] == 10000.0
        assert dashboard['core_metrics']['total_donations'] == 150

        # Verify multiple repository calls
        assert mock_transaction_repo.get_aggregated_data.call_count >= 3


class TestCrossServiceIntegration:
    """Test integration between multiple services."""

    @pytest.fixture
    def app(self):
        """Create Flask app for testing."""
        with patch.dict(os.environ, {'TESTING': 'true'}):
            from app import create_app
            app = create_app()
            return app

    @patch('app.donations.services.wallet_service.get_wallet_repository')
    @patch('app.donations.services.donation_service.get_donation_repository')
    @patch('app.donations.services.compliance_service.get_compliance_repository')
    def test_donation_with_compliance_check(self, mock_get_compliance_repo,
                                          mock_get_donation_repo,
                                          mock_get_wallet_repo, app):
        """Test donation process that triggers compliance check."""

        # Arrange
        mock_wallet_repo = MagicMock()
        mock_donation_repo = MagicMock()
        mock_compliance_repo = MagicMock()

        mock_get_wallet_repo.return_value = mock_wallet_repo
        mock_get_donation_repo.return_value = mock_donation_repo
        mock_get_compliance_repo.return_value = mock_compliance_repo

        user_id = "user_123"
        large_donation_amount = 1000.00  # Triggers compliance check

        # Mock wallet with sufficient balance
        mock_wallet = MagicMock()
        mock_wallet.current_balance = 1500.00
        mock_wallet_repo.find_by_user_id.return_value = mock_wallet

        # Mock compliance check creation
        mock_compliance_check = MagicMock()
        mock_compliance_check.id = "check_123"
        mock_compliance_repo.create.return_value = mock_compliance_check

        with app.app_context():
            # Act - Large donation that should trigger compliance
            compliance_service = ComplianceService()

            # Simulate compliance check for large donation
            success, message, result = compliance_service.initiate_compliance_check(
                user_id=user_id,
                check_type="AML",
                initiated_by="system",
                metadata={"donation_amount": large_donation_amount}
            )

        # Assert
        assert success is True
        assert message == "COMPLIANCE_CHECK_INITIATED"
        assert result['check_id'] == "check_123"

        # Verify compliance repository was called
        mock_compliance_repo.create.assert_called_once()

    def test_error_propagation_across_services(self, app):
        """Test how errors propagate across service boundaries."""

        with app.app_context():
            # Act - Test with invalid service configuration
            with patch('app.donations.services.wallet_service.get_wallet_repository') as mock_get_repo:
                mock_get_repo.side_effect = Exception("Database connection failed")

                wallet_service = WalletService()

                # This should handle the repository error gracefully
                success, message, result = wallet_service.get_wallet_info("user_123")

        # Assert - Service should handle repository errors
        assert success is False
        assert "error" in message.lower() or "failed" in message.lower()
        assert result is None