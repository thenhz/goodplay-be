"""
Unit tests for the Donations module (GOO-14).
Tests models, repositories, and services for virtual wallet and credit system.
"""
import pytest
import os
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone, timedelta

# Set testing environment before importing app modules
os.environ['TESTING'] = 'true'

from app.donations.models.wallet import Wallet
from app.donations.models.transaction import Transaction, TransactionType, TransactionStatus, SourceType
from app.donations.models.conversion_rate import ConversionRate, MultiplierType
from app.donations.services.credit_calculation_service import CreditCalculationService
from app.donations.services.wallet_service import WalletService
from app.donations.services.batch_processing_service import BatchProcessingService
from app.donations.services.fraud_prevention_service import FraudPreventionService
from app.donations.services.receipt_generation_service import ReceiptGenerationService
from app.donations.services.tax_compliance_service import TaxComplianceService
from app.donations.services.compliance_service import ComplianceService
from app.donations.services.reconciliation_service import ReconciliationService
from app.donations.services.financial_analytics_service import FinancialAnalyticsService


class TestWalletModel:
    """Test the Wallet model functionality."""

    def test_wallet_creation(self):
        """Test wallet creation with default values."""
        wallet = Wallet(user_id="user_123")

        assert wallet.user_id == "user_123"
        assert wallet.current_balance == 0.0
        assert wallet.total_earned == 0.0
        assert wallet.total_donated == 0.0
        assert wallet.auto_donation_settings['enabled'] is False
        assert wallet.version == 1

    def test_add_credits_success(self):
        """Test successful credit addition."""
        wallet = Wallet(user_id="user_123")

        result = wallet.add_credits(50.0, 'earned')

        assert result is True
        assert wallet.current_balance == 50.0
        assert wallet.total_earned == 50.0
        assert wallet.version == 2

    def test_add_credits_invalid_amount(self):
        """Test credit addition with invalid amount."""
        wallet = Wallet(user_id="user_123")

        result = wallet.add_credits(-10.0, 'earned')

        assert result is False
        assert wallet.current_balance == 0.0
        assert wallet.total_earned == 0.0

    def test_add_credits_fraud_prevention(self):
        """Test credit addition fraud prevention."""
        wallet = Wallet(user_id="user_123")

        result = wallet.add_credits(1500.0, 'earned')  # Above daily limit

        assert result is False
        assert wallet.current_balance == 0.0

    def test_deduct_credits_success(self):
        """Test successful credit deduction."""
        wallet = Wallet(user_id="user_123", current_balance=100.0)

        result = wallet.deduct_credits(30.0, 'donated')

        assert result is True
        assert wallet.current_balance == 70.0
        assert wallet.total_donated == 30.0

    def test_deduct_credits_insufficient_balance(self):
        """Test credit deduction with insufficient balance."""
        wallet = Wallet(user_id="user_123", current_balance=20.0)

        result = wallet.deduct_credits(50.0, 'donated')

        assert result is False
        assert wallet.current_balance == 20.0
        assert wallet.total_donated == 0.0

    def test_auto_donation_settings_update(self):
        """Test auto-donation settings update."""
        wallet = Wallet(user_id="user_123")

        settings = {
            'enabled': True,
            'threshold': 50.0,
            'percentage': 25
        }

        result = wallet.update_auto_donation_settings(settings)

        assert result is True
        assert wallet.auto_donation_settings['enabled'] is True
        assert wallet.auto_donation_settings['threshold'] == 50.0
        assert wallet.auto_donation_settings['percentage'] == 25

    def test_should_auto_donate(self):
        """Test auto-donation eligibility check."""
        wallet = Wallet(user_id="user_123", current_balance=100.0)
        wallet.auto_donation_settings = {
            'enabled': True,
            'threshold': 50.0,
            'percentage': 25
        }

        assert wallet.should_auto_donate() is True

    def test_calculate_auto_donation_amount(self):
        """Test auto-donation amount calculation."""
        wallet = Wallet(user_id="user_123", current_balance=100.0)
        wallet.auto_donation_settings = {
            'enabled': True,
            'threshold': 50.0,
            'percentage': 50
        }

        amount = wallet.calculate_auto_donation_amount()

        assert amount == 25.0  # (100 - 50) * 50% = 25

    def test_wallet_validation(self):
        """Test wallet data validation."""
        valid_data = {
            'user_id': 'user_123',
            'current_balance': 50.0,
            'auto_donation_settings': {
                'enabled': True,
                'threshold': 25.0,
                'percentage': 30
            }
        }

        error = Wallet.validate_wallet_data(valid_data)
        assert error is None

    def test_wallet_validation_invalid_data(self):
        """Test wallet validation with invalid data."""
        invalid_data = {
            'user_id': '',
            'current_balance': -10.0
        }

        error = Wallet.validate_wallet_data(invalid_data)
        assert error == "WALLET_USER_ID_REQUIRED"


class TestTransactionModel:
    """Test the Transaction model functionality."""

    def test_transaction_creation(self):
        """Test transaction creation."""
        transaction = Transaction(
            user_id="user_123",
            transaction_type=TransactionType.EARNED.value,
            amount=25.0,
            source_type=SourceType.GAMEPLAY.value
        )

        assert transaction.user_id == "user_123"
        assert transaction.transaction_type == TransactionType.EARNED.value
        assert transaction.amount == 25.0
        assert transaction.status == TransactionStatus.PENDING.value

    def test_mark_completed(self):
        """Test marking transaction as completed."""
        transaction = Transaction(
            user_id="user_123",
            transaction_type=TransactionType.EARNED.value,
            amount=25.0
        )

        receipt_data = {'receipt_id': 'R123'}
        transaction.mark_completed(receipt_data)

        assert transaction.status == TransactionStatus.COMPLETED.value
        assert transaction.processed_at is not None
        assert transaction.receipt_data['receipt_id'] == 'R123'

    def test_get_effective_amount(self):
        """Test effective amount calculation with multiplier."""
        transaction = Transaction(
            user_id="user_123",
            transaction_type=TransactionType.EARNED.value,
            amount=20.0,
            multiplier_applied=1.5
        )

        effective_amount = transaction.get_effective_amount()
        assert effective_amount == 30.0

    def test_create_earned_transaction(self):
        """Test creating earned transaction with factory method."""
        transaction = Transaction.create_earned_transaction(
            user_id="user_123",
            amount=15.0,
            source_type=SourceType.TOURNAMENT.value,
            multiplier=2.0
        )

        assert transaction.transaction_type == TransactionType.EARNED.value
        assert transaction.amount == 15.0
        assert transaction.source_type == SourceType.TOURNAMENT.value
        assert transaction.multiplier_applied == 2.0

    def test_create_donation_transaction(self):
        """Test creating donation transaction with factory method."""
        transaction = Transaction.create_donation_transaction(
            user_id="user_123",
            amount=50.0,
            onlus_id="onlus_456"
        )

        assert transaction.transaction_type == TransactionType.DONATED.value
        assert transaction.amount == 50.0
        assert transaction.onlus_id == "onlus_456"

    def test_transaction_validation(self):
        """Test transaction data validation."""
        valid_data = {
            'user_id': 'user_123',
            'transaction_type': TransactionType.EARNED.value,
            'amount': 25.0,
            'source_type': SourceType.GAMEPLAY.value
        }

        error = Transaction.validate_transaction_data(valid_data)
        assert error is None

    def test_transaction_validation_invalid_type(self):
        """Test transaction validation with invalid type."""
        invalid_data = {
            'user_id': 'user_123',
            'transaction_type': 'invalid_type',
            'amount': 25.0
        }

        error = Transaction.validate_transaction_data(invalid_data)
        assert error == "TRANSACTION_TYPE_INVALID"


class TestConversionRateModel:
    """Test the ConversionRate model functionality."""

    def test_conversion_rate_creation(self):
        """Test conversion rate creation with defaults."""
        rate = ConversionRate()

        assert rate.base_rate == 0.01
        assert rate.is_active is True
        assert MultiplierType.TOURNAMENT.value in rate.multipliers
        assert rate.multipliers[MultiplierType.TOURNAMENT.value] == 2.0

    def test_calculate_credits_basic(self):
        """Test basic credit calculation."""
        rate = ConversionRate()

        # 5 minutes = 300,000 ms
        credits = rate.calculate_credits(300000, [])

        assert credits == 0.05  # 5 minutes * 0.01 EUR/min

    def test_calculate_credits_with_multipliers(self):
        """Test credit calculation with multipliers."""
        rate = ConversionRate()

        # 10 minutes with tournament multiplier (2.0x)
        credits = rate.calculate_credits(600000, [MultiplierType.TOURNAMENT.value])

        assert credits == 0.20  # 10 * 0.01 * 2.0

    def test_get_combined_multiplier(self):
        """Test combined multiplier calculation."""
        rate = ConversionRate()

        multipliers = [
            MultiplierType.TOURNAMENT.value,  # 2.0x
            MultiplierType.WEEKEND.value      # 1.1x
        ]

        combined = rate.get_combined_multiplier(multipliers)

        # Additive: 1.0 + (2.0-1.0) + (1.1-1.0) = 2.1
        assert combined == 2.1

    def test_update_multiplier(self):
        """Test updating individual multiplier."""
        rate = ConversionRate()

        result = rate.update_multiplier(MultiplierType.TOURNAMENT.value, 2.5)

        assert result is True
        assert rate.multipliers[MultiplierType.TOURNAMENT.value] == 2.5

    def test_is_valid_at(self):
        """Test rate validity check."""
        now = datetime.now(timezone.utc)
        future = now + timedelta(hours=1)

        rate = ConversionRate(
            valid_from=now,
            valid_until=future,
            is_active=True
        )

        assert rate.is_valid_at(now) is True
        assert rate.is_valid_at(future + timedelta(minutes=1)) is False

    def test_create_default_rates(self):
        """Test creating default conversion rates."""
        rate = ConversionRate.create_default_rates()

        assert rate.rate_id == "default"
        assert rate.base_rate == ConversionRate.DEFAULT_BASE_RATE
        assert rate.is_active is True

    def test_create_special_event_rates(self):
        """Test creating special event rates."""
        start_time = datetime.now(timezone.utc)
        end_time = start_time + timedelta(days=7)

        rate = ConversionRate.create_special_event_rates(
            event_name="Holiday Special",
            base_multiplier=2.0,
            valid_from=start_time,
            valid_until=end_time
        )

        assert "holiday_special" in rate.rate_id
        assert rate.base_rate == ConversionRate.DEFAULT_BASE_RATE * 2.0
        assert rate.valid_from == start_time
        assert rate.valid_until == end_time


class TestCreditCalculationService:
    """Test the CreditCalculationService."""

    def setUp(self):
        self.service = CreditCalculationService()

    @patch('app.donations.services.credit_calculation_service.ConversionRateRepository')
    def test_calculate_credits_from_session_success(self, mock_repo_class, app):
        """Test successful credit calculation from session."""
        # Setup mocks
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        mock_rate = ConversionRate()
        mock_repo.get_current_rate.return_value = mock_rate

        service = CreditCalculationService()

        session_data = {
            'user_id': 'user_123',
            'session_id': 'session_456',
            'play_duration_ms': 600000,  # 10 minutes
            'game_id': 'puzzle_game'
        }

        with app.app_context():
            success, message, result = service.calculate_credits_from_session(session_data)

        assert success is True
        assert message == "CREDITS_CALCULATED_SUCCESS"
        assert result is not None
        assert 'amount' in result
        assert 'effective_amount' in result

    @patch('app.donations.services.credit_calculation_service.ConversionRateRepository')
    def test_calculate_credits_invalid_session(self, mock_repo_class, app):
        """Test credit calculation with invalid session data."""
        service = CreditCalculationService()

        invalid_session = {
            'user_id': 'user_123'
            # Missing required fields
        }

        with app.app_context():
            success, message, result = service.calculate_credits_from_session(invalid_session)

        assert success is False
        assert "SESSION_" in message
        assert result is None

    @patch('app.donations.services.credit_calculation_service.ConversionRateRepository')
    def test_estimate_credits_for_duration(self, mock_repo_class):
        """Test credit estimation for duration."""
        # Setup mocks
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        mock_rate = ConversionRate()
        mock_repo.get_current_rate.return_value = mock_rate

        service = CreditCalculationService()

        success, message, result = service.estimate_credits_for_duration(10.0)

        assert success is True
        assert message == "CREDIT_ESTIMATION_SUCCESS"
        assert result['duration_minutes'] == 10.0
        assert result['base_credits'] == 0.10  # 10 minutes * 0.01


class TestWalletService:
    """Test the WalletService."""

    @patch('app.donations.services.wallet_service.WalletRepository')
    @patch('app.donations.services.wallet_service.TransactionRepository')
    def test_get_wallet_creates_new_wallet(self, mock_transaction_repo, mock_wallet_repo, app):
        """Test getting wallet creates new one if not exists."""
        # Setup mocks
        mock_wallet_repo.return_value.find_by_user_id.return_value = None
        mock_wallet_repo.return_value.create_wallet.return_value = "wallet_id_123"

        service = WalletService()

        with app.app_context():
            success, message, result = service.get_wallet("user_123")

        assert success is True
        assert message == "WALLET_RETRIEVED_SUCCESS"
        assert result is not None

    @patch('app.donations.services.wallet_service.WalletRepository')
    @patch('app.donations.services.wallet_service.TransactionRepository')
    def test_add_credits_success(self, mock_transaction_repo, mock_wallet_repo, app):
        """Test successful credit addition."""
        # Setup mocks
        mock_wallet = Wallet(user_id="user_123")
        mock_wallet_repo.return_value.find_by_user_id.return_value = mock_wallet
        mock_wallet_repo.return_value.update_wallet.return_value = True
        mock_transaction_repo.return_value.create_transaction.return_value = "tx_123"
        mock_transaction_repo.return_value.update_transaction.return_value = True

        service = WalletService()

        with app.app_context():
            success, message, result = service.add_credits(
                user_id="user_123",
                amount=25.0,
                source=SourceType.GAMEPLAY.value
            )

        assert success is True
        assert message == "CREDITS_ADDED_SUCCESS"
        assert result['amount_added'] == 25.0

    @patch('app.donations.services.wallet_service.WalletRepository')
    @patch('app.donations.services.wallet_service.TransactionRepository')
    def test_process_donation_success(self, mock_transaction_repo, mock_wallet_repo, app):
        """Test successful donation processing."""
        # Setup mocks
        mock_wallet = Wallet(user_id="user_123", current_balance=100.0)
        mock_wallet_repo.return_value.find_by_user_id.return_value = mock_wallet
        mock_wallet_repo.return_value.update_wallet.return_value = True
        mock_transaction_repo.return_value.create_transaction.return_value = "tx_456"
        mock_transaction_repo.return_value.update_transaction.return_value = True

        service = WalletService()

        with app.app_context():
            success, message, result = service.process_donation(
                user_id="user_123",
                amount=25.0,
                onlus_id="onlus_789"
            )

        assert success is True
        assert message == "DONATION_SUCCESS"
        assert result['donation_amount'] == 25.0
        assert result['onlus_id'] == "onlus_789"

    @patch('app.donations.services.wallet_service.WalletRepository')
    @patch('app.donations.services.wallet_service.TransactionRepository')
    def test_process_donation_insufficient_credits(self, mock_transaction_repo, mock_wallet_repo):
        """Test donation processing with insufficient credits."""
        # Setup mocks
        mock_wallet = Wallet(user_id="user_123", current_balance=10.0)
        mock_wallet_repo.return_value.find_by_user_id.return_value = mock_wallet

        service = WalletService()

        success, message, result = service.process_donation(
            user_id="user_123",
            amount=25.0,
            onlus_id="onlus_789"
        )

        assert success is False
        assert message == "INSUFFICIENT_CREDITS"
        assert result is None


class TestIntegration:
    """Integration tests for the complete donations system."""

    @patch('app.donations.services.credit_calculation_service.ConversionRateRepository')
    @patch('app.donations.services.wallet_service.WalletRepository')
    @patch('app.donations.services.wallet_service.TransactionRepository')
    def test_complete_session_to_donation_flow(self, mock_transaction_repo,
                                               mock_wallet_repo, mock_rate_repo, app):
        """Test complete flow from session to donation."""
        # Setup mocks
        mock_rate = ConversionRate()
        mock_rate_repo.return_value.get_current_rate.return_value = mock_rate

        mock_wallet = Wallet(user_id="user_123")
        mock_wallet_repo.return_value.find_by_user_id.return_value = mock_wallet
        mock_wallet_repo.return_value.update_wallet.return_value = True
        mock_transaction_repo.return_value.create_transaction.return_value = "tx_123"
        mock_transaction_repo.return_value.update_transaction.return_value = True

        wallet_service = WalletService()

        # Step 1: Convert session to credits
        session_data = {
            'user_id': 'user_123',
            'session_id': 'session_456',
            'play_duration_ms': 600000,  # 10 minutes
            'game_id': 'puzzle_game'
        }

        with app.app_context():
            success, message, result = wallet_service.convert_session_to_credits(session_data)

        assert success is True
        assert message == "SESSION_CONVERSION_SUCCESS"

        # Step 2: Process donation
        with app.app_context():
            success, message, result = wallet_service.process_donation(
                user_id="user_123",
                amount=0.05,  # Donate earned credits
                onlus_id="onlus_789"
            )

        assert success is True
        assert message == "DONATION_SUCCESS"

    def test_fraud_detection_triggers(self):
        """Test that fraud detection triggers appropriately."""
        service = CreditCalculationService()

        # Test with suspiciously high values
        session_data = {
            'user_id': 'user_123',
            'session_id': 'session_456',
            'play_duration_ms': 36000000,  # 10 hours
            'game_id': 'puzzle_game'
        }

        fraud_indicators = service._check_fraud_indicators(session_data, 1000.0, 6.0)

        assert fraud_indicators['is_suspicious'] is True
        assert 'high_earnings' in fraud_indicators['indicators']
        assert 'high_multiplier' in fraud_indicators['indicators']
        assert 'long_session' in fraud_indicators['indicators']


# GOO-15 New Services Tests

class TestBatchProcessingService:
    """Test BatchProcessingService functionality."""

    @patch('app.donations.services.batch_processing_service.BatchOperationRepository')
    @patch('app.donations.services.batch_processing_service.BatchDonationRepository')
    def test_create_batch_operation_success(self, mock_batch_donation_repo, mock_batch_op_repo, app):
        """Test successful batch operation creation."""
        # Setup mocks
        mock_batch_op_repo.return_value.create.return_value = "batch_123"
        mock_batch_donation_repo.return_value.create_batch_donations.return_value = True

        service = BatchProcessingService()

        donations_data = [
            {'user_id': 'user1', 'onlus_id': 'onlus1', 'amount': 10.0},
            {'user_id': 'user2', 'onlus_id': 'onlus1', 'amount': 15.0}
        ]

        with app.app_context():
            success, message, result = service.create_batch_donation_operation(
                donations=donations_data,
                created_by="test_admin"
            )

        assert success is True
        assert message == "BATCH_OPERATION_CREATED"
        assert result['batch_id'] == "batch_123"

    @patch('app.donations.services.batch_processing_service.BatchOperationRepository')
    @patch('app.donations.services.batch_processing_service.BatchDonationRepository')
    def test_process_batch_donations(self, mock_batch_donation_repo, mock_batch_op_repo, app):
        """Test batch donation processing."""
        # Setup mocks
        mock_batch_op_repo.return_value.find_by_id.return_value = {
            'batch_id': 'batch_123',
            'operation_type': 'donations',
            'status': 'pending'
        }
        mock_batch_donation_repo.return_value.find_by_batch_id.return_value = [
            {'user_id': 'user1', 'amount': 10.0, 'status': 'pending'},
            {'user_id': 'user2', 'amount': 15.0, 'status': 'pending'}
        ]

        service = BatchProcessingService()

        with app.app_context():
            success, message, result = service.process_batch_operation('batch_123')

        assert success is True
        assert message == "BATCH_PROCESSING_COMPLETED"


class TestFraudPreventionService:
    """Test FraudPreventionService functionality."""

    def test_validate_conversion_success(self, app):
        """Test successful conversion validation."""
        service = FraudPreventionService()

        conversion_data = {
            'user_id': 'user_123',
            'amount': 5.0,
            'play_duration_minutes': 500
        }

        with app.app_context():
            is_valid, reason = service.validate_conversion(conversion_data)

        assert is_valid is True
        assert reason is None

    def test_validate_conversion_excessive_amount(self, app):
        """Test conversion validation with excessive amount."""
        service = FraudPreventionService()

        conversion_data = {
            'user_id': 'user_123',
            'amount': 1500.0,  # Exceeds daily limit
            'play_duration_minutes': 500
        }

        with app.app_context():
            is_valid, reason = service.validate_conversion(conversion_data)

        assert is_valid is False
        assert "DAILY_LIMIT_EXCEEDED" in reason

    def test_detect_anomalies(self, app):
        """Test anomaly detection."""
        service = FraudPreventionService()

        user_id = 'user_123'
        transaction_data = {
            'amount': 100.0,
            'play_duration_minutes': 60
        }

        with app.app_context():
            anomalies = service.detect_anomalies(user_id, transaction_data)

        assert isinstance(anomalies, list)


class TestReceiptGenerationService:
    """Test ReceiptGenerationService functionality."""

    def test_generate_receipt_data(self, app):
        """Test receipt data generation."""
        service = ReceiptGenerationService()

        donation_data = {
            'donation_id': 'don_123',
            'user_id': 'user_123',
            'onlus_id': 'onlus_123',
            'amount': 50.0,
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
            'address': 'Via Test 123, Milano'
        }

        with app.app_context():
            receipt_data = service.generate_receipt_data(
                donation_data, user_data, onlus_data
            )

        assert receipt_data['donation_id'] == 'don_123'
        assert receipt_data['donor_name'] == 'Mario Rossi'
        assert receipt_data['amount'] == 50.0
        assert 'receipt_number' in receipt_data

    def test_generate_pdf_receipt(self, app):
        """Test PDF receipt generation."""
        service = ReceiptGenerationService()

        receipt_data = {
            'receipt_number': 'R-2025-001',
            'donation_id': 'don_123',
            'donor_name': 'Mario Rossi',
            'amount': 50.0,
            'onlus_name': 'Test ONLUS'
        }

        with app.app_context():
            success, message, pdf_data = service.generate_pdf_receipt(receipt_data)

        assert success is True
        assert message == "PDF_RECEIPT_GENERATED"
        assert 'pdf_content' in pdf_data


class TestTaxComplianceService:
    """Test TaxComplianceService functionality."""

    def test_calculate_deductibility(self, app):
        """Test tax deductibility calculation."""
        service = TaxComplianceService()

        donation_data = {
            'amount': 100.0,
            'onlus_type': 'ONLUS'
        }

        with app.app_context():
            deductibility = service.calculate_deductibility(donation_data)

        assert deductibility['deductible_amount'] == 100.0
        assert deductibility['deductible_percentage'] == 100.0
        assert deductibility['max_deductible'] > 0

    def test_generate_annual_summary(self, app):
        """Test annual tax summary generation."""
        service = TaxComplianceService()

        donations = [
            {'amount': 50.0, 'date': datetime.now(timezone.utc)},
            {'amount': 75.0, 'date': datetime.now(timezone.utc)}
        ]

        with app.app_context():
            summary = service.generate_annual_summary('user_123', donations, 2025)

        assert summary['total_donated'] == 125.0
        assert summary['tax_year'] == 2025
        assert summary['user_id'] == 'user_123'


class TestComplianceService:
    """Test ComplianceService functionality."""

    @patch('app.donations.services.compliance_service.ComplianceCheckRepository')
    def test_initiate_compliance_check(self, mock_repo, app):
        """Test compliance check initiation."""
        mock_repo.return_value.create_check.return_value = "check_123"

        service = ComplianceService()

        with app.app_context():
            success, message, result = service.initiate_compliance_check(
                user_id="user_123",
                check_type="aml",
                reason="Transaction review"
            )

        assert success is True
        assert message == "COMPLIANCE_CHECK_INITIATED"
        assert result['check_id'] == "check_123"

    @patch('app.donations.services.compliance_service.ComplianceCheckRepository')
    def test_review_compliance_check(self, mock_repo, app):
        """Test compliance check review."""
        mock_repo.return_value.find_by_id.return_value = {
            'check_id': 'check_123',
            'status': 'pending_review'
        }
        mock_repo.return_value.update_check.return_value = True

        service = ComplianceService()

        with app.app_context():
            success, message, result = service.review_compliance_check(
                check_id="check_123",
                reviewer_id="admin_456",
                decision="approve",
                review_notes="All clear"
            )

        assert success is True
        assert message == "COMPLIANCE_CHECK_REVIEWED"


class TestReconciliationService:
    """Test ReconciliationService functionality."""

    @patch('app.donations.services.reconciliation_service.ReconciliationRepository')
    @patch('app.donations.services.reconciliation_service.TransactionRepository')
    def test_start_reconciliation(self, mock_transaction_repo, mock_reconciliation_repo, app):
        """Test reconciliation initiation."""
        # Setup mocks
        mock_reconciliation_repo.return_value.create_reconciliation.return_value = "recon_123"
        mock_transaction_repo.return_value.find_by_date_range.return_value = [
            {'transaction_id': 'tx_1', 'amount': 50.0, 'payment_intent_id': 'pi_1'}
        ]

        service = ReconciliationService()

        start_date = datetime.now(timezone.utc) - timedelta(days=1)
        end_date = datetime.now(timezone.utc)

        with app.app_context():
            success, message, result = service.start_reconciliation(
                start_date=start_date,
                end_date=end_date,
                reconciliation_type="daily"
            )

        assert success is True
        assert message == "RECONCILIATION_STARTED"
        assert result['reconciliation_id'] == "recon_123"

    def test_match_transactions(self, app):
        """Test transaction matching logic."""
        service = ReconciliationService()

        internal_transactions = [
            {'transaction_id': 'tx_1', 'amount': 50.0, 'payment_intent_id': 'pi_1'},
            {'transaction_id': 'tx_2', 'amount': 25.0, 'payment_intent_id': 'pi_2'}
        ]

        external_payments = [
            {'payment_id': 'pay_1', 'amount': 50.0, 'payment_intent_id': 'pi_1'},
            {'payment_id': 'pay_2', 'amount': 25.0, 'payment_intent_id': 'pi_2'}
        ]

        with app.app_context():
            matched_pairs, unmatched_internal, unmatched_external = service._match_transactions(
                internal_transactions, external_payments
            )

        assert len(matched_pairs) == 2
        assert len(unmatched_internal) == 0
        assert len(unmatched_external) == 0


class TestFinancialAnalyticsService:
    """Test FinancialAnalyticsService functionality."""

    @patch('app.donations.services.financial_analytics_service.TransactionRepository')
    @patch('app.donations.services.financial_analytics_service.WalletRepository')
    def test_generate_financial_dashboard(self, mock_wallet_repo, mock_transaction_repo, app):
        """Test financial dashboard generation."""
        # Setup mocks
        mock_transaction_repo.return_value.get_aggregated_data.return_value = {
            'total_volume': 1000.0,
            'total_donations': 50,
            'average_donation': 20.0
        }
        mock_wallet_repo.return_value.get_user_stats.return_value = {
            'total_users': 100,
            'active_users': 80
        }

        service = FinancialAnalyticsService()

        date_range = {
            'start_date': datetime.now(timezone.utc) - timedelta(days=30),
            'end_date': datetime.now(timezone.utc)
        }

        with app.app_context():
            success, message, dashboard = service.generate_financial_dashboard(date_range)

        assert success is True
        assert message == "FINANCIAL_DASHBOARD_GENERATED"
        assert 'core_metrics' in dashboard
        assert 'trends' in dashboard
        assert 'user_analytics' in dashboard

    @patch('app.donations.services.financial_analytics_service.TransactionRepository')
    def test_get_trend_analysis(self, mock_transaction_repo, app):
        """Test trend analysis generation."""
        mock_transaction_repo.return_value.get_daily_aggregates.return_value = [
            {'date': '2025-09-01', 'volume': 100.0, 'count': 5},
            {'date': '2025-09-02', 'volume': 120.0, 'count': 6},
            {'date': '2025-09-03', 'volume': 110.0, 'count': 5}
        ]

        service = FinancialAnalyticsService()

        start_date = datetime.now(timezone.utc) - timedelta(days=7)
        end_date = datetime.now(timezone.utc)

        with app.app_context():
            success, message, trends = service.get_trend_analysis(
                start_date=start_date,
                end_date=end_date,
                metric='volume'
            )

        assert success is True
        assert message == "TREND_ANALYSIS_GENERATED"
        assert 'daily_data' in trends
        assert 'trend_direction' in trends


class TestGOO15Integration:
    """Integration tests for GOO-15 complete system."""

    @patch('app.donations.services.wallet_service.WalletRepository')
    @patch('app.donations.services.wallet_service.TransactionRepository')
    @patch('app.donations.services.batch_processing_service.BatchOperationRepository')
    @patch('app.donations.services.compliance_service.ComplianceCheckRepository')
    def test_complete_compliance_workflow(self, mock_compliance_repo, mock_batch_repo,
                                        mock_transaction_repo, mock_wallet_repo, app):
        """Test complete compliance workflow integration."""
        # Setup mocks for wallet operations
        mock_wallet = Wallet(user_id="user_123", current_balance=100.0)
        mock_wallet_repo.return_value.find_by_user_id.return_value = mock_wallet
        mock_wallet_repo.return_value.update_wallet.return_value = True

        # Setup mocks for compliance
        mock_compliance_repo.return_value.create_check.return_value = "check_123"
        mock_compliance_repo.return_value.find_by_id.return_value = {
            'check_id': 'check_123',
            'status': 'approved'
        }

        # Setup transaction mocks
        mock_transaction_repo.return_value.create_transaction.return_value = "tx_123"
        mock_transaction_repo.return_value.update_transaction.return_value = True

        wallet_service = WalletService()
        compliance_service = ComplianceService()

        with app.app_context():
            # Step 1: Initiate compliance check
            success, message, check_result = compliance_service.initiate_compliance_check(
                user_id="user_123",
                check_type="aml",
                reason="High value donation"
            )
            assert success is True

            # Step 2: Process donation after compliance approval
            success, message, donation_result = wallet_service.process_donation(
                user_id="user_123",
                amount=50.0,
                onlus_id="onlus_789"
            )
            assert success is True

    def test_batch_processing_with_analytics(self, app):
        """Test batch processing integration with analytics."""
        batch_service = BatchProcessingService()
        analytics_service = FinancialAnalyticsService()

        with app.app_context():
            # Test that services can be instantiated and work together
            assert batch_service is not None
            assert analytics_service is not None

            # Test basic functionality
            donations_data = [
                {'user_id': 'user1', 'onlus_id': 'onlus1', 'amount': 10.0}
            ]

            # This would test the integration in a real scenario
            # For now, we ensure the services are properly initialized


if __name__ == '__main__':
    pytest.main([__file__, '-v'])