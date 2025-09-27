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


if __name__ == '__main__':
    pytest.main([__file__, '-v'])