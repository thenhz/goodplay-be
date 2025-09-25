"""
BaseDonationTest - GOO-35 Testing Utilities
Specialized base class for donations and wallet testing
Provides domain-specific utilities for financial transactions
"""
import os
import sys
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any, Tuple
from unittest.mock import Mock, patch
from bson import ObjectId

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from tests.core.base_service_test import BaseServiceTest
from tests.utils.builders import BaseBuilder


class WalletBuilder(BaseBuilder):
    """Builder for Wallet test data"""

    def __init__(self):
        super().__init__()
        self._data = {
            '_id': str(ObjectId()),
            'user_id': str(ObjectId()),
            'balance': Decimal('0.00'),
            'currency': 'EUR',
            'status': 'active',
            'created_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc),
            'last_transaction_at': None,
            'total_donated': Decimal('0.00'),
            'total_earned': Decimal('0.00'),
            'frozen_amount': Decimal('0.00'),
            'version': 1
        }

    def with_balance(self, amount: float) -> 'WalletBuilder':
        """Set wallet balance"""
        self._data['balance'] = Decimal(str(amount))
        return self

    def with_currency(self, currency: str) -> 'WalletBuilder':
        """Set wallet currency"""
        self._data['currency'] = currency
        return self

    def with_status(self, status: str) -> 'WalletBuilder':
        """Set wallet status (active, suspended, frozen)"""
        self._data['status'] = status
        return self

    def with_donations(self, amount: float) -> 'WalletBuilder':
        """Set total donated amount"""
        self._data['total_donated'] = Decimal(str(amount))
        return self

    def with_earnings(self, amount: float) -> 'WalletBuilder':
        """Set total earned amount"""
        self._data['total_earned'] = Decimal(str(amount))
        return self

    def with_frozen_amount(self, amount: float) -> 'WalletBuilder':
        """Set frozen amount"""
        self._data['frozen_amount'] = Decimal(str(amount))
        return self


class TransactionBuilder(BaseBuilder):
    """Builder for Transaction test data"""

    def __init__(self):
        super().__init__()
        self._data = {
            '_id': str(self._generate_object_id()),
            'wallet_id': str(self._generate_object_id()),
            'user_id': str(ObjectId()),
            'type': 'donation',
            'amount': Decimal('10.00'),
            'currency': 'EUR',
            'status': 'completed',
            'description': 'Game donation',
            'reference_id': None,
            'onlus_id': None,
            'payment_method': 'credits',
            'external_reference': None,
            'metadata': {},
            'created_at': datetime.now(timezone.utc),
            'processed_at': datetime.now(timezone.utc),
            'failed_at': None,
            'failure_reason': None
        }

    def as_donation(self, amount: float, onlus_id: str = None) -> 'TransactionBuilder':
        """Create donation transaction"""
        self._data.update({
            'type': 'donation',
            'amount': Decimal(str(amount)),
            'onlus_id': onlus_id or str(self._generate_object_id())
        })
        return self

    def as_earning(self, amount: float, source: str = 'game_reward') -> 'TransactionBuilder':
        """Create earning transaction"""
        self._data.update({
            'type': 'earning',
            'amount': Decimal(str(amount)),
            'description': f'{source} reward'
        })
        return self

    def as_refund(self, amount: float, original_tx_id: str) -> 'TransactionBuilder':
        """Create refund transaction"""
        self._data.update({
            'type': 'refund',
            'amount': Decimal(str(amount)),
            'reference_id': original_tx_id,
            'description': 'Transaction refund'
        })
        return self

    def with_status(self, status: str) -> 'TransactionBuilder':
        """Set transaction status"""
        self._data['status'] = status
        if status == 'failed':
            self._data['failed_at'] = datetime.now(timezone.utc)
            self._data['failure_reason'] = 'Insufficient funds'
        return self

    def with_payment_method(self, method: str) -> 'TransactionBuilder':
        """Set payment method (credits, paypal, stripe, bank_transfer)"""
        self._data['payment_method'] = method
        return self

    def with_external_reference(self, reference: str) -> 'TransactionBuilder':
        """Set external payment reference"""
        self._data['external_reference'] = reference
        return self


class BaseDonationTest(BaseServiceTest):
    """Base class for donation and wallet testing with GOO-35 utilities"""

    def setUp(self):
        super().setUp()
        self._setup_donation_mocks()

    def _setup_donation_mocks(self):
        """Setup donation-specific mocks and repositories"""
        # Mock wallet repository
        self.mock_wallet_repository = Mock()
        self.mock_wallet_repository.create_indexes = Mock()

        # Mock transaction repository
        self.mock_transaction_repository = Mock()
        self.mock_transaction_repository.create_indexes = Mock()

        # Mock payment gateways
        self.mock_paypal_gateway = Mock()
        self.mock_stripe_gateway = Mock()

        # Register builders
        self._register_donation_builders()

    def _register_donation_builders(self):
        """Register donation-specific builders"""
        try:
            if hasattr(self.smart_fixtures, 'register_builder'):
                self.smart_fixtures.register_builder('wallet', WalletBuilder)
                self.smart_fixtures.register_builder('transaction', TransactionBuilder)
        except Exception:
            # Fallback to direct builder usage
            pass

    # Wallet Creation Utilities
    def create_test_wallet(self, user_id: str = None, balance: float = 0.0, **kwargs) -> Dict[str, Any]:
        """Create test wallet data with realistic defaults"""
        builder = WalletBuilder()

        if user_id:
            builder._data['user_id'] = user_id

        if balance != 0.0:
            builder.with_balance(balance)

        # Apply additional customizations
        for key, value in kwargs.items():
            if hasattr(builder, f'with_{key}'):
                getattr(builder, f'with_{key}')(value)
            else:
                builder._data[key] = value

        return builder.build()

    def create_test_transaction(self, wallet_id: str = None, tx_type: str = 'donation',
                              amount: float = 10.0, **kwargs) -> Dict[str, Any]:
        """Create test transaction data"""
        builder = TransactionBuilder()

        if wallet_id:
            builder._data['wallet_id'] = wallet_id

        # Set transaction type and amount
        if tx_type == 'donation':
            builder.as_donation(amount, kwargs.get('onlus_id'))
        elif tx_type == 'earning':
            builder.as_earning(amount, kwargs.get('source', 'game_reward'))
        elif tx_type == 'refund':
            builder.as_refund(amount, kwargs.get('original_tx_id', str(ObjectId())))

        # Apply additional customizations
        for key, value in kwargs.items():
            if key not in ['onlus_id', 'source', 'original_tx_id']:
                if hasattr(builder, f'with_{key}'):
                    getattr(builder, f'with_{key}')(value)
                else:
                    builder._data[key] = value

        return builder.build()

    # Wallet Scenarios
    def create_wallet_with_history(self, user_id: str = None, transactions_count: int = 5) -> Dict[str, Any]:
        """Create wallet with transaction history"""
        wallet = self.create_test_wallet(user_id=user_id, balance=100.0)

        # Create transaction history
        transactions = []
        total_balance = Decimal('0.00')

        for i in range(transactions_count):
            if i % 2 == 0:  # Earning
                amount = 20.0
                tx = self.create_test_transaction(
                    wallet_id=wallet['_id'],
                    tx_type='earning',
                    amount=amount
                )
                total_balance += Decimal(str(amount))
            else:  # Donation
                amount = 5.0
                tx = self.create_test_transaction(
                    wallet_id=wallet['_id'],
                    tx_type='donation',
                    amount=amount
                )
                total_balance -= Decimal(str(amount))

            transactions.append(tx)

        wallet['balance'] = total_balance
        wallet['transactions'] = transactions

        return wallet

    # Payment Gateway Mocking
    def mock_payment_gateway_success(self, gateway: str = 'paypal', amount: float = 10.0) -> Dict[str, Any]:
        """Mock successful payment gateway transaction"""
        payment_data = {
            'gateway': gateway,
            'amount': Decimal(str(amount)),
            'currency': 'EUR',
            'external_id': f'{gateway}_tx_123456',
            'status': 'completed',
            'fee': Decimal(str(amount * 0.029)),  # 2.9% fee
            'net_amount': Decimal(str(amount * 0.971))
        }

        if gateway == 'paypal':
            self.mock_paypal_gateway.process_payment.return_value = (True, 'Payment successful', payment_data)
        elif gateway == 'stripe':
            self.mock_stripe_gateway.process_payment.return_value = (True, 'Payment successful', payment_data)

        return payment_data

    def mock_payment_gateway_failure(self, gateway: str = 'paypal', reason: str = 'insufficient_funds'):
        """Mock failed payment gateway transaction"""
        error_data = {
            'gateway': gateway,
            'error_code': reason,
            'error_message': 'Payment failed - insufficient funds'
        }

        if gateway == 'paypal':
            self.mock_paypal_gateway.process_payment.return_value = (False, 'Payment failed', error_data)
        elif gateway == 'stripe':
            self.mock_stripe_gateway.process_payment.return_value = (False, 'Payment failed', error_data)

        return error_data

    # Transaction Scenarios
    def mock_wallet_transaction_success(self, wallet_id: str, transaction_data: Dict[str, Any]):
        """Mock successful wallet transaction processing"""
        self.mock_transaction_repository.create.return_value = transaction_data
        self.mock_wallet_repository.update_balance.return_value = True

        # Update wallet balance mock
        wallet_update = {
            'balance': transaction_data.get('amount', Decimal('0.00')),
            'last_transaction_at': datetime.now(timezone.utc),
            'version': 2
        }

        if transaction_data.get('type') == 'donation':
            wallet_update['total_donated'] = transaction_data['amount']
        elif transaction_data.get('type') == 'earning':
            wallet_update['total_earned'] = transaction_data['amount']

        return wallet_update

    def mock_wallet_insufficient_funds(self, wallet_id: str, required_amount: float):
        """Mock insufficient funds scenario"""
        self.mock_wallet_repository.get_balance.return_value = Decimal('5.00')  # Less than required

        error_data = {
            'error': 'insufficient_funds',
            'available_balance': Decimal('5.00'),
            'required_amount': Decimal(str(required_amount)),
            'deficit': Decimal(str(required_amount)) - Decimal('5.00')
        }

        return error_data

    # Multi-Currency Support
    def create_multi_currency_scenario(self, currencies: List[str] = None) -> Dict[str, Any]:
        """Create multi-currency testing scenario"""
        if currencies is None:
            currencies = ['EUR', 'USD', 'GBP']

        scenario = {
            'wallets': {},
            'exchange_rates': {},
            'transactions': []
        }

        # Create wallets for each currency
        user_id = str(ObjectId())
        for currency in currencies:
            wallet = self.create_test_wallet(
                user_id=user_id,
                currency=currency,
                balance=100.0
            )
            scenario['wallets'][currency] = wallet

        # Mock exchange rates
        base_rates = {'EUR': 1.0, 'USD': 1.12, 'GBP': 0.87}
        for currency in currencies:
            scenario['exchange_rates'][currency] = base_rates.get(currency, 1.0)

        return scenario

    # Bulk Operations
    def create_bulk_donation_scenario(self, donor_count: int = 10, onlus_count: int = 3) -> Dict[str, Any]:
        """Create bulk donation testing scenario"""
        scenario = {
            'donors': [],
            'onlus_list': [],
            'donations': [],
            'total_amount': Decimal('0.00')
        }

        # Create donors
        for i in range(donor_count):
            wallet = self.create_test_wallet(balance=50.0)
            scenario['donors'].append(wallet)

        # Create ONLUS recipients
        for i in range(onlus_count):
            onlus_id = str(ObjectId())
            scenario['onlus_list'].append(onlus_id)

        # Create donation transactions
        for donor in scenario['donors']:
            onlus_id = scenario['onlus_list'][len(scenario['donations']) % onlus_count]
            donation = self.create_test_transaction(
                wallet_id=donor['_id'],
                tx_type='donation',
                amount=10.0,
                onlus_id=onlus_id
            )
            scenario['donations'].append(donation)
            scenario['total_amount'] += donation['amount']

        return scenario

    # Assertion Utilities
    def assert_wallet_balance_valid(self, wallet_data: Dict[str, Any], expected_balance: float = None):
        """Assert wallet has valid balance structure"""
        assert 'balance' in wallet_data
        assert isinstance(wallet_data['balance'], (Decimal, float, int))
        assert wallet_data['balance'] >= 0  # No negative balances allowed

        if expected_balance is not None:
            assert float(wallet_data['balance']) == expected_balance

        # Assert required fields
        required_fields = ['_id', 'user_id', 'currency', 'status', 'created_at']
        for field in required_fields:
            assert field in wallet_data, f"Missing required field: {field}"

    def assert_transaction_valid(self, transaction_data: Dict[str, Any],
                               expected_type: str = None, expected_amount: float = None):
        """Assert transaction has valid structure"""
        required_fields = ['_id', 'wallet_id', 'type', 'amount', 'currency', 'status']
        for field in required_fields:
            assert field in transaction_data, f"Missing required field: {field}"

        # Validate amount
        assert isinstance(transaction_data['amount'], (Decimal, float, int))
        assert transaction_data['amount'] > 0

        # Validate status
        valid_statuses = ['pending', 'completed', 'failed', 'refunded']
        assert transaction_data['status'] in valid_statuses

        if expected_type:
            assert transaction_data['type'] == expected_type

        if expected_amount is not None:
            assert float(transaction_data['amount']) == expected_amount

    def assert_donation_flow_complete(self, donation_result: Dict[str, Any]):
        """Assert complete donation flow execution"""
        assert 'transaction_id' in donation_result
        assert 'wallet_balance' in donation_result
        assert 'onlus_credited' in donation_result

        # Verify transaction was recorded
        assert donation_result['transaction_id'] is not None

        # Verify wallet balance updated
        assert 'new_balance' in donation_result['wallet_balance']

        # Verify ONLUS received funds
        assert donation_result['onlus_credited'] is True


# Performance and Load Testing Utilities
class DonationLoadTestMixin:
    """Mixin for donation load testing utilities"""

    def simulate_concurrent_donations(self, user_count: int = 100, donation_amount: float = 5.0):
        """Simulate concurrent donation load"""
        donation_data = []

        for i in range(user_count):
            wallet = self.create_test_wallet(balance=20.0)
            donation = self.create_test_transaction(
                wallet_id=wallet['_id'],
                tx_type='donation',
                amount=donation_amount
            )
            donation_data.append({
                'wallet': wallet,
                'donation': donation,
                'user_index': i
            })

        return donation_data

    def validate_donation_performance(self, donations: List[Dict], max_processing_time: float = 0.1):
        """Validate donation processing performance"""
        for donation_data in donations:
            # Each donation should process within time limit
            processing_time = donation_data.get('processing_time_ms', 50)  # Default 50ms
            assert processing_time <= max_processing_time * 1000  # Convert to milliseconds

            # Verify data integrity
            self.assert_transaction_valid(donation_data['donation'])