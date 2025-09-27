"""
Comprehensive unit tests for GOO-15 Donation Processing Engine services.
Tests all new services introduced in GOO-15 implementation.
"""
import pytest
import os
from unittest.mock import MagicMock, patch, call
from datetime import datetime, timezone, timedelta
from decimal import Decimal

# Set testing environment before importing app modules
os.environ['TESTING'] = 'true'

from app import create_app
from app.donations.services.batch_processing_service import BatchProcessingService
from app.donations.services.compliance_service import ComplianceService
from app.donations.services.financial_analytics_service import FinancialAnalyticsService
from app.donations.services.reconciliation_service import ReconciliationService
from app.donations.services.receipt_generation_service import ReceiptGenerationService
from app.donations.services.tax_compliance_service import TaxComplianceService


@pytest.fixture
def app():
    """Create test app with testing configuration."""
    return create_app('testing')


class TestBatchProcessingService:
    """Comprehensive tests for BatchProcessingService."""

    @pytest.fixture
    def batch_service(self):
        """Create batch service with mocked dependencies."""
        with patch('app.donations.services.batch_processing_service.BatchOperationRepository') as mock_batch_repo, \
             patch('app.donations.services.batch_processing_service.BatchDonationRepository') as mock_donation_repo, \
             patch('app.donations.services.batch_processing_service.WalletService') as mock_wallet_service:

            service = BatchProcessingService()
            service.batch_repo = mock_batch_repo.return_value
            service.batch_donation_repo = mock_donation_repo.return_value
            service.wallet_service = mock_wallet_service.return_value
            return service

    def test_create_batch_donation_operation_success(self, batch_service, app):
        """Test successful batch donation operation creation."""
        # Mock successful repository calls
        batch_service.batch_repo.create.return_value = "batch_123"
        batch_service.batch_donation_repo.create_batch_donations.return_value = True

        donations_data = [
            {'user_id': 'user1', 'onlus_id': 'onlus1', 'amount': 10.0},
            {'user_id': 'user2', 'onlus_id': 'onlus1', 'amount': 15.0}
        ]

        with app.app_context():
            success, message, result = batch_service.create_batch_donation_operation(
                donations=donations_data,
                created_by="admin_123"
            )

        assert success is True
        assert message == "BATCH_OPERATION_CREATED"
        assert result['batch_id'] == "batch_123"
        assert result['total_items'] == 2

        # Verify repository calls
        batch_service.batch_repo.create.assert_called_once()
        batch_service.batch_donation_repo.create_batch_donations.assert_called_once()

    def test_create_batch_donation_operation_validation_error(self, batch_service, app):
        """Test batch operation creation with validation errors."""
        # Empty donations list
        with app.app_context():
            success, message, result = batch_service.create_batch_donation_operation(
                donations=[],
                created_by="admin_123"
            )

        assert success is False
        assert "VALIDATION_ERROR" in message
        assert result is None

    def test_create_batch_donation_operation_too_large(self, batch_service, app):
        """Test batch operation creation with too many items."""
        # Create a batch larger than max size
        large_donations = [
            {'user_id': f'user{i}', 'onlus_id': 'onlus1', 'amount': 10.0}
            for i in range(1000)  # Exceeds max_batch_size
        ]

        with app.app_context():
            success, message, result = batch_service.create_batch_donation_operation(
                donations=large_donations,
                created_by="admin_123"
            )

        assert success is False
        assert "BATCH_TOO_LARGE" in message

    def test_process_batch_operation_success(self, batch_service, app):
        """Test successful batch operation processing."""
        # Mock batch operation data
        batch_service.batch_repo.find_by_id.return_value = {
            'batch_id': 'batch_123',
            'operation_type': 'donations',
            'status': 'pending',
            'total_items': 2
        }

        # Mock batch donations
        batch_service.batch_donation_repo.find_by_batch_id.return_value = [
            {'donation_id': 'don1', 'user_id': 'user1', 'amount': 10.0, 'status': 'pending'},
            {'donation_id': 'don2', 'user_id': 'user2', 'amount': 15.0, 'status': 'pending'}
        ]

        # Mock successful donation processing
        batch_service.wallet_service.process_donation.return_value = (True, "DONATION_SUCCESS", {'donation_id': 'don1'})

        with app.app_context():
            success, message, result = batch_service.process_batch_operation('batch_123')

        assert success is True
        assert message == "BATCH_PROCESSING_COMPLETED"
        assert 'processed_items' in result
        assert 'failed_items' in result

    def test_get_batch_operation_status(self, batch_service, app):
        """Test getting batch operation status."""
        # Mock batch operation with progress
        batch_service.batch_repo.find_by_id.return_value = {
            'batch_id': 'batch_123',
            'status': 'processing',
            'total_items': 10,
            'processed_items': 7,
            'failed_items': 1,
            'created_at': datetime.now(timezone.utc),
            'started_at': datetime.now(timezone.utc) - timedelta(minutes=5)
        }

        with app.app_context():
            success, message, result = batch_service.get_batch_operation_status('batch_123')

        assert success is True
        assert message == "BATCH_STATUS_RETRIEVED"
        assert result['batch_id'] == 'batch_123'
        assert result['progress_percentage'] == 70.0  # 7/10 * 100

    def test_cancel_batch_operation(self, batch_service, app):
        """Test cancelling a batch operation."""
        batch_service.batch_repo.find_by_id.return_value = {
            'batch_id': 'batch_123',
            'status': 'processing'
        }
        batch_service.batch_repo.update_status.return_value = True

        with app.app_context():
            success, message, result = batch_service.cancel_batch_operation('batch_123', 'admin_456')

        assert success is True
        assert message == "BATCH_OPERATION_CANCELLED"

        # Verify status was updated
        batch_service.batch_repo.update_status.assert_called_with('batch_123', 'cancelled')


class TestComplianceService:
    """Comprehensive tests for ComplianceService."""

    @pytest.fixture
    def compliance_service(self):
        """Create compliance service with mocked dependencies."""
        with patch('app.donations.services.compliance_service.ComplianceCheckRepository') as mock_repo:
            service = ComplianceService()
            service.compliance_repo = mock_repo.return_value
            return service

    def test_initiate_compliance_check_success(self, compliance_service, app):
        """Test successful compliance check initiation."""
        # Mock repository response
        compliance_service.compliance_repo.create_check.return_value = "check_123"

        with app.app_context():
            success, message, result = compliance_service.initiate_compliance_check(
                user_id="user_123",
                check_type="aml",
                reason="High value transaction review"
            )

        assert success is True
        assert message == "COMPLIANCE_CHECK_INITIATED"
        assert result['check_id'] == "check_123"
        assert result['check_type'] == "aml"

        # Verify repository call
        compliance_service.compliance_repo.create_check.assert_called_once()

    def test_initiate_compliance_check_invalid_type(self, compliance_service, app):
        """Test compliance check with invalid check type."""
        with app.app_context():
            success, message, result = compliance_service.initiate_compliance_check(
                user_id="user_123",
                check_type="invalid_type",
                reason="Test"
            )

        assert success is False
        assert "INVALID_CHECK_TYPE" in message
        assert result is None

    def test_review_compliance_check_success(self, compliance_service, app):
        """Test successful compliance check review."""
        # Mock existing check
        compliance_service.compliance_repo.find_by_id.return_value = {
            'check_id': 'check_123',
            'status': 'pending_review',
            'user_id': 'user_123',
            'check_type': 'aml'
        }
        compliance_service.compliance_repo.update_check.return_value = True

        with app.app_context():
            success, message, result = compliance_service.review_compliance_check(
                check_id="check_123",
                reviewer_id="admin_456",
                decision="approve",
                review_notes="All documents verified"
            )

        assert success is True
        assert message == "COMPLIANCE_CHECK_REVIEWED"
        assert result['decision'] == "approve"

        # Verify repository update
        compliance_service.compliance_repo.update_check.assert_called_once()

    def test_review_compliance_check_invalid_decision(self, compliance_service, app):
        """Test compliance check review with invalid decision."""
        with app.app_context():
            success, message, result = compliance_service.review_compliance_check(
                check_id="check_123",
                reviewer_id="admin_456",
                decision="invalid_decision",
                review_notes="Test"
            )

        assert success is False
        assert "INVALID_DECISION" in message

    def test_get_compliance_status(self, compliance_service, app):
        """Test getting user compliance status."""
        # Mock user compliance history
        compliance_service.compliance_repo.find_by_user_id.return_value = [
            {'check_type': 'aml', 'status': 'approved', 'completed_at': datetime.now(timezone.utc)},
            {'check_type': 'kyc', 'status': 'pending_review', 'created_at': datetime.now(timezone.utc)}
        ]

        with app.app_context():
            success, message, result = compliance_service.get_compliance_status("user_123")

        assert success is True
        assert message == "COMPLIANCE_STATUS_RETRIEVED"
        assert 'overall_status' in result
        assert 'checks_history' in result
        assert len(result['checks_history']) == 2

    def test_perform_aml_check(self, compliance_service, app):
        """Test automated AML check logic."""
        transaction_data = {
            'user_id': 'user_123',
            'amount': 1000.0,
            'transaction_type': 'donation'
        }

        with app.app_context():
            risk_score, flags = compliance_service._perform_aml_check(transaction_data)

        assert isinstance(risk_score, (int, float))
        assert 0 <= risk_score <= 100
        assert isinstance(flags, list)

    def test_perform_kyc_check(self, compliance_service, app):
        """Test automated KYC check logic."""
        user_data = {
            'user_id': 'user_123',
            'documents_verified': True,
            'address_verified': False,
            'identity_verified': True
        }

        with app.app_context():
            kyc_status, missing_items = compliance_service._perform_kyc_check(user_data)

        assert kyc_status in ['approved', 'rejected', 'pending']
        assert isinstance(missing_items, list)


class TestFinancialAnalyticsService:
    """Comprehensive tests for FinancialAnalyticsService."""

    @pytest.fixture
    def analytics_service(self):
        """Create analytics service with mocked dependencies."""
        with patch('app.donations.services.financial_analytics_service.TransactionRepository') as mock_trans_repo, \
             patch('app.donations.services.financial_analytics_service.WalletRepository') as mock_wallet_repo:

            service = FinancialAnalyticsService()
            service.transaction_repo = mock_trans_repo.return_value
            service.wallet_repo = mock_wallet_repo.return_value
            return service

    def test_generate_financial_dashboard_success(self, analytics_service, app):
        """Test successful financial dashboard generation."""
        # Mock repository responses
        analytics_service.transaction_repo.get_aggregated_data.return_value = {
            'total_volume': 10000.0,
            'total_donations': 150,
            'average_donation': 66.67
        }

        analytics_service.wallet_repo.get_user_stats.return_value = {
            'total_users': 500,
            'active_users': 350
        }

        analytics_service.transaction_repo.get_daily_aggregates.return_value = [
            {'date': '2025-09-25', 'volume': 500.0, 'count': 10},
            {'date': '2025-09-26', 'volume': 750.0, 'count': 15},
            {'date': '2025-09-27', 'volume': 600.0, 'count': 12}
        ]

        date_range = {
            'start_date': datetime.now(timezone.utc) - timedelta(days=30),
            'end_date': datetime.now(timezone.utc)
        }

        with app.app_context():
            success, message, dashboard = analytics_service.generate_financial_dashboard(date_range)

        assert success is True
        assert message == "FINANCIAL_DASHBOARD_GENERATED"
        assert 'core_metrics' in dashboard
        assert 'trends' in dashboard
        assert 'user_analytics' in dashboard
        assert 'payment_analytics' in dashboard
        assert 'performance_metrics' in dashboard

        # Verify core metrics
        assert dashboard['core_metrics']['total_volume'] == 10000.0
        assert dashboard['core_metrics']['total_donations'] == 150

    def test_get_trend_analysis_success(self, analytics_service, app):
        """Test successful trend analysis generation."""
        # Mock daily data
        analytics_service.transaction_repo.get_daily_aggregates.return_value = [
            {'date': '2025-09-01', 'volume': 100.0, 'count': 5},
            {'date': '2025-09-02', 'volume': 120.0, 'count': 6},
            {'date': '2025-09-03', 'volume': 110.0, 'count': 5},
            {'date': '2025-09-04', 'volume': 140.0, 'count': 7},
            {'date': '2025-09-05', 'volume': 130.0, 'count': 6}
        ]

        start_date = datetime.now(timezone.utc) - timedelta(days=7)
        end_date = datetime.now(timezone.utc)

        with app.app_context():
            success, message, trends = analytics_service.get_trend_analysis(
                start_date=start_date,
                end_date=end_date,
                metric='volume'
            )

        assert success is True
        assert message == "TREND_ANALYSIS_GENERATED"
        assert 'daily_data' in trends
        assert 'trend_direction' in trends
        assert 'volatility' in trends
        assert len(trends['daily_data']) == 5

    def test_get_user_behavior_analytics(self, analytics_service, app):
        """Test user behavior analytics generation."""
        # Mock user data
        analytics_service.wallet_repo.get_user_segments.return_value = {
            'new_donors': 50,
            'returning_donors': 200,
            'high_value': 25,
            'frequent_donors': 75
        }

        analytics_service.transaction_repo.get_user_behavior_data.return_value = {
            'retention_rate': 0.65,
            'average_time_between_donations': 14.5,
            'donation_frequency_distribution': {'weekly': 30, 'monthly': 50, 'quarterly': 20}
        }

        start_date = datetime.now(timezone.utc) - timedelta(days=30)
        end_date = datetime.now(timezone.utc)

        with app.app_context():
            success, message, user_analytics = analytics_service.get_user_behavior_analytics(
                start_date=start_date,
                end_date=end_date
            )

        assert success is True
        assert message == "USER_ANALYTICS_GENERATED"
        assert 'user_segments' in user_analytics
        assert 'behavior_metrics' in user_analytics
        assert user_analytics['user_segments']['new_donors'] == 50

    def test_generate_forecasting_report(self, analytics_service, app):
        """Test forecasting report generation."""
        # Mock historical data for forecasting
        analytics_service.transaction_repo.get_daily_aggregates.return_value = [
            {'date': f'2025-09-{20+i:02d}', 'volume': 100 + i*10, 'count': 5 + i}
            for i in range(7)
        ]

        with app.app_context():
            success, message, forecast = analytics_service.generate_forecasting_report(
                forecast_days=7,
                metric='volume'
            )

        assert success is True
        assert message == "FORECASTING_REPORT_GENERATED"
        assert 'forecast_data' in forecast
        assert 'confidence_intervals' in forecast
        assert 'methodology' in forecast
        assert len(forecast['forecast_data']) == 7

    def test_get_custom_metrics(self, analytics_service, app):
        """Test custom metrics retrieval."""
        analytics_service.transaction_repo.get_custom_aggregates.return_value = {
            'volume': 5000.0,
            'count': 75,
            'average': 66.67
        }

        start_date = datetime.now(timezone.utc) - timedelta(days=7)
        end_date = datetime.now(timezone.utc)

        with app.app_context():
            success, message, metrics = analytics_service.get_custom_metrics(
                start_date=start_date,
                end_date=end_date,
                metric_types=['volume', 'count', 'average'],
                period='daily'
            )

        assert success is True
        assert message == "CUSTOM_METRICS_RETRIEVED"
        assert 'metrics' in metrics
        assert 'period' in metrics
        assert metrics['metrics']['volume'] == 5000.0


class TestReconciliationService:
    """Comprehensive tests for ReconciliationService."""

    @pytest.fixture
    def reconciliation_service(self):
        """Create reconciliation service with mocked dependencies."""
        with patch('app.donations.services.reconciliation_service.ReconciliationRepository') as mock_recon_repo, \
             patch('app.donations.services.reconciliation_service.TransactionRepository') as mock_trans_repo:

            service = ReconciliationService()
            service.reconciliation_repo = mock_recon_repo.return_value
            service.transaction_repo = mock_trans_repo.return_value
            return service

    def test_start_reconciliation_success(self, reconciliation_service, app):
        """Test successful reconciliation initiation."""
        # Mock repository responses
        reconciliation_service.reconciliation_repo.create_reconciliation.return_value = "recon_123"

        # Mock internal transactions
        reconciliation_service.transaction_repo.find_by_date_range.return_value = [
            {'transaction_id': 'tx_1', 'amount': 50.0, 'payment_intent_id': 'pi_1', 'status': 'completed'},
            {'transaction_id': 'tx_2', 'amount': 25.0, 'payment_intent_id': 'pi_2', 'status': 'completed'}
        ]

        start_date = datetime.now(timezone.utc) - timedelta(days=1)
        end_date = datetime.now(timezone.utc)

        with app.app_context():
            success, message, result = reconciliation_service.start_reconciliation(
                start_date=start_date,
                end_date=end_date,
                reconciliation_type="daily"
            )

        assert success is True
        assert message == "RECONCILIATION_STARTED"
        assert result['reconciliation_id'] == "recon_123"
        assert result['total_internal_transactions'] == 2

    def test_match_transactions_exact_match(self, reconciliation_service, app):
        """Test exact transaction matching by payment_intent_id."""
        internal_transactions = [
            {'transaction_id': 'tx_1', 'amount': 50.0, 'payment_intent_id': 'pi_1'},
            {'transaction_id': 'tx_2', 'amount': 25.0, 'payment_intent_id': 'pi_2'}
        ]

        external_payments = [
            {'payment_id': 'pay_1', 'amount': 50.0, 'payment_intent_id': 'pi_1'},
            {'payment_id': 'pay_2', 'amount': 25.0, 'payment_intent_id': 'pi_2'}
        ]

        with app.app_context():
            matched_pairs, unmatched_internal, unmatched_external = reconciliation_service._match_transactions(
                internal_transactions, external_payments
            )

        assert len(matched_pairs) == 2
        assert len(unmatched_internal) == 0
        assert len(unmatched_external) == 0

        # Verify match confidence
        for match in matched_pairs:
            assert match['confidence'] == 1.0  # Exact match

    def test_match_transactions_fuzzy_match(self, reconciliation_service, app):
        """Test fuzzy transaction matching by amount and timing."""
        internal_transactions = [
            {
                'transaction_id': 'tx_1',
                'amount': 50.0,
                'payment_intent_id': None,
                'created_at': datetime.now(timezone.utc)
            }
        ]

        external_payments = [
            {
                'payment_id': 'pay_1',
                'amount': 50.0,
                'payment_intent_id': None,
                'created_at': datetime.now(timezone.utc) + timedelta(minutes=5)
            }
        ]

        with app.app_context():
            matched_pairs, unmatched_internal, unmatched_external = reconciliation_service._match_transactions(
                internal_transactions, external_payments
            )

        assert len(matched_pairs) == 1
        assert matched_pairs[0]['confidence'] < 1.0  # Fuzzy match
        assert matched_pairs[0]['confidence'] > 0.8  # High confidence

    def test_detect_discrepancies(self, reconciliation_service, app):
        """Test discrepancy detection."""
        internal_transactions = [
            {'transaction_id': 'tx_1', 'amount': 50.0, 'payment_intent_id': 'pi_1'},
            {'transaction_id': 'tx_2', 'amount': 25.0, 'payment_intent_id': 'pi_2'}
        ]

        external_payments = [
            {'payment_id': 'pay_1', 'amount': 55.0, 'payment_intent_id': 'pi_1'},  # Amount mismatch
            {'payment_id': 'pay_3', 'amount': 30.0, 'payment_intent_id': 'pi_3'}   # Orphaned payment
        ]

        matched_pairs = [
            {
                'internal': internal_transactions[0],
                'external': external_payments[0],
                'confidence': 0.9
            }
        ]

        with app.app_context():
            discrepancies = reconciliation_service._detect_discrepancies(
                internal_transactions, external_payments, matched_pairs
            )

        assert len(discrepancies) >= 2  # Amount mismatch + missing transaction + orphaned payment

        # Check for amount mismatch discrepancy
        amount_mismatch = next((d for d in discrepancies if d['type'] == 'amount_mismatch'), None)
        assert amount_mismatch is not None
        assert amount_mismatch['severity'] == 'medium'

    def test_resolve_discrepancy(self, reconciliation_service, app):
        """Test discrepancy resolution."""
        reconciliation_service.reconciliation_repo.find_discrepancy.return_value = {
            'discrepancy_id': 'disc_123',
            'type': 'amount_mismatch',
            'status': 'pending'
        }
        reconciliation_service.reconciliation_repo.update_discrepancy.return_value = True

        with app.app_context():
            success, message, result = reconciliation_service.resolve_discrepancy(
                discrepancy_id="disc_123",
                resolution="manual_adjustment",
                resolved_by="admin_456",
                notes="Amount difference due to currency conversion"
            )

        assert success is True
        assert message == "DISCREPANCY_RESOLVED"
        assert result['resolution'] == "manual_adjustment"

    def test_get_reconciliation_report(self, reconciliation_service, app):
        """Test reconciliation report generation."""
        reconciliation_service.reconciliation_repo.find_by_id.return_value = {
            'reconciliation_id': 'recon_123',
            'status': 'completed',
            'total_internal_transactions': 100,
            'total_external_payments': 98,
            'matched_transactions': 95,
            'discrepancies_found': 5,
            'match_rate': 0.95
        }

        with app.app_context():
            success, message, report = reconciliation_service.get_reconciliation_report("recon_123")

        assert success is True
        assert message == "RECONCILIATION_REPORT_GENERATED"
        assert report['match_rate'] == 0.95
        assert report['total_discrepancies'] == 5


class TestReceiptGenerationService:
    """Comprehensive tests for ReceiptGenerationService."""

    @pytest.fixture
    def receipt_service(self):
        """Create receipt service."""
        return ReceiptGenerationService()

    def test_generate_receipt_data_success(self, receipt_service, app):
        """Test successful receipt data generation."""
        donation_data = {
            'donation_id': 'don_123',
            'user_id': 'user_123',
            'onlus_id': 'onlus_123',
            'amount': 100.0,
            'transaction_date': datetime.now(timezone.utc)
        }

        user_data = {
            'name': 'Mario',
            'surname': 'Rossi',
            'email': 'mario.rossi@email.com',
            'tax_code': 'RSSMRA80A01H501U'
        }

        onlus_data = {
            'name': 'Test ONLUS',
            'tax_code': '12345678901',
            'address': 'Via Test 123, Milano MI 20100'
        }

        with app.app_context():
            receipt_data = receipt_service.generate_receipt_data(
                donation_data, user_data, onlus_data
            )

        assert receipt_data['donation_id'] == 'don_123'
        assert receipt_data['donor_name'] == 'Mario Rossi'
        assert receipt_data['donor_tax_code'] == 'RSSMRA80A01H501U'
        assert receipt_data['amount'] == 100.0
        assert receipt_data['onlus_name'] == 'Test ONLUS'
        assert 'receipt_number' in receipt_data
        assert 'tax_year' in receipt_data
        assert 'qr_code_data' in receipt_data

    def test_generate_pdf_receipt_success(self, receipt_service, app):
        """Test successful PDF receipt generation."""
        receipt_data = {
            'receipt_number': 'R-2025-001',
            'donation_id': 'don_123',
            'donor_name': 'Mario Rossi',
            'donor_tax_code': 'RSSMRA80A01H501U',
            'amount': 100.0,
            'onlus_name': 'Test ONLUS',
            'onlus_tax_code': '12345678901',
            'tax_year': 2025,
            'issue_date': datetime.now(timezone.utc).strftime('%d/%m/%Y')
        }

        with app.app_context():
            success, message, pdf_result = receipt_service.generate_pdf_receipt(receipt_data)

        assert success is True
        assert message == "PDF_RECEIPT_GENERATED"
        assert 'pdf_content' in pdf_result
        assert 'file_size' in pdf_result
        assert pdf_result['file_size'] > 0

    def test_generate_receipt_number(self, receipt_service, app):
        """Test receipt number generation."""
        with app.app_context():
            receipt_number = receipt_service._generate_receipt_number()

        assert receipt_number.startswith('R-2025-')
        assert len(receipt_number) == 11  # R-YYYY-XXX format

        # Test uniqueness
        receipt_number2 = receipt_service._generate_receipt_number()
        assert receipt_number != receipt_number2

    def test_generate_qr_code(self, receipt_service, app):
        """Test QR code generation for receipts."""
        receipt_data = {
            'receipt_number': 'R-2025-001',
            'donation_id': 'don_123',
            'amount': 100.0
        }

        with app.app_context():
            qr_data = receipt_service._generate_qr_code(receipt_data)

        assert 'R-2025-001' in qr_data
        assert 'don_123' in qr_data
        assert '100.0' in qr_data

    def test_validate_receipt_data(self, receipt_service, app):
        """Test receipt data validation."""
        # Valid data
        valid_data = {
            'donation_id': 'don_123',
            'donor_name': 'Mario Rossi',
            'amount': 100.0,
            'onlus_name': 'Test ONLUS'
        }

        with app.app_context():
            is_valid, error = receipt_service._validate_receipt_data(valid_data)

        assert is_valid is True
        assert error is None

        # Invalid data - missing required fields
        invalid_data = {
            'donation_id': 'don_123'
            # Missing required fields
        }

        with app.app_context():
            is_valid, error = receipt_service._validate_receipt_data(invalid_data)

        assert is_valid is False
        assert error is not None


class TestTaxComplianceService:
    """Comprehensive tests for TaxComplianceService."""

    @pytest.fixture
    def tax_service(self):
        """Create tax compliance service."""
        return TaxComplianceService()

    def test_calculate_deductibility_onlus(self, tax_service, app):
        """Test tax deductibility calculation for ONLUS donations."""
        donation_data = {
            'amount': 200.0,
            'onlus_type': 'ONLUS',
            'donation_date': datetime.now(timezone.utc)
        }

        with app.app_context():
            deductibility = tax_service.calculate_deductibility(donation_data)

        assert deductibility['deductible_amount'] == 200.0
        assert deductibility['deductible_percentage'] == 100.0
        assert deductibility['max_deductible'] > 0
        assert deductibility['tax_benefit_category'] == 'full_deduction'

    def test_calculate_deductibility_odv(self, tax_service, app):
        """Test tax deductibility calculation for ODV donations."""
        donation_data = {
            'amount': 150.0,
            'onlus_type': 'ODV',
            'donation_date': datetime.now(timezone.utc)
        }

        with app.app_context():
            deductibility = tax_service.calculate_deductibility(donation_data)

        assert deductibility['deductible_amount'] <= 150.0
        assert deductibility['deductible_percentage'] <= 100.0
        assert 'tax_benefit_category' in deductibility

    def test_generate_annual_summary(self, tax_service, app):
        """Test annual tax summary generation."""
        donations = [
            {'amount': 100.0, 'date': datetime(2025, 3, 15, tzinfo=timezone.utc), 'onlus_type': 'ONLUS'},
            {'amount': 50.0, 'date': datetime(2025, 6, 20, tzinfo=timezone.utc), 'onlus_type': 'ONLUS'},
            {'amount': 75.0, 'date': datetime(2025, 9, 10, tzinfo=timezone.utc), 'onlus_type': 'ODV'}
        ]

        with app.app_context():
            summary = tax_service.generate_annual_summary('user_123', donations, 2025)

        assert summary['user_id'] == 'user_123'
        assert summary['tax_year'] == 2025
        assert summary['total_donated'] == 225.0
        assert summary['total_deductible'] <= 225.0
        assert summary['number_of_donations'] == 3
        assert len(summary['monthly_breakdown']) <= 12

    def test_get_tax_limits(self, tax_service, app):
        """Test tax deduction limits retrieval."""
        with app.app_context():
            limits = tax_service.get_tax_limits(2025)

        assert 'onlus_max_deduction' in limits
        assert 'odv_max_deduction' in limits
        assert 'percentage_limit' in limits
        assert limits['tax_year'] == 2025

    def test_validate_tax_code(self, tax_service, app):
        """Test Italian tax code validation."""
        # Valid tax codes
        valid_codes = [
            'RSSMRA80A01H501U',  # Personal tax code
            '12345678901',       # Company tax code
        ]

        for code in valid_codes:
            with app.app_context():
                is_valid = tax_service._validate_tax_code(code)
            assert is_valid is True

        # Invalid tax codes
        invalid_codes = [
            'INVALID',
            '123',
            'RSSMRA80A01H501X'  # Wrong check digit
        ]

        for code in invalid_codes:
            with app.app_context():
                is_valid = tax_service._validate_tax_code(code)
            assert is_valid is False

    def test_calculate_monthly_breakdown(self, tax_service, app):
        """Test monthly donation breakdown calculation."""
        donations = [
            {'amount': 100.0, 'date': datetime(2025, 1, 15, tzinfo=timezone.utc)},
            {'amount': 50.0, 'date': datetime(2025, 1, 20, tzinfo=timezone.utc)},
            {'amount': 75.0, 'date': datetime(2025, 3, 10, tzinfo=timezone.utc)}
        ]

        with app.app_context():
            breakdown = tax_service._calculate_monthly_breakdown(donations)

        assert breakdown[1] == 150.0  # January total
        assert breakdown[3] == 75.0   # March total
        assert breakdown[2] == 0.0    # February (no donations)

    def test_generate_tax_certificate(self, tax_service, app):
        """Test tax certificate generation."""
        summary_data = {
            'user_id': 'user_123',
            'tax_year': 2025,
            'total_donated': 500.0,
            'total_deductible': 500.0,
            'number_of_donations': 5
        }

        with app.app_context():
            success, message, certificate = tax_service.generate_tax_certificate(summary_data)

        assert success is True
        assert message == "TAX_CERTIFICATE_GENERATED"
        assert certificate['certificate_number'].startswith('TC-2025-')
        assert certificate['total_deductible'] == 500.0
        assert 'issue_date' in certificate


if __name__ == '__main__':
    pytest.main([__file__, '-v'])