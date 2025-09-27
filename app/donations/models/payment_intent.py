from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from bson import ObjectId
import json


class PaymentIntentStatus:
    """Payment intent status constants."""
    PENDING = "pending"
    PROCESSING = "processing"
    REQUIRES_ACTION = "requires_action"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"

    @classmethod
    def get_all_statuses(cls) -> List[str]:
        return [
            cls.PENDING, cls.PROCESSING, cls.REQUIRES_ACTION,
            cls.SUCCEEDED, cls.FAILED, cls.CANCELLED,
            cls.REFUNDED, cls.PARTIALLY_REFUNDED
        ]

    @classmethod
    def get_final_statuses(cls) -> List[str]:
        """Get statuses that indicate payment is finalized."""
        return [cls.SUCCEEDED, cls.FAILED, cls.CANCELLED, cls.REFUNDED]

    @classmethod
    def get_success_statuses(cls) -> List[str]:
        """Get statuses that indicate successful payment."""
        return [cls.SUCCEEDED, cls.REFUNDED, cls.PARTIALLY_REFUNDED]


class PaymentMethod:
    """Payment method type constants."""
    CARD = "card"
    BANK_TRANSFER = "bank_transfer"
    PAYPAL = "paypal"
    APPLE_PAY = "apple_pay"
    GOOGLE_PAY = "google_pay"
    SEPA = "sepa"
    KLARNA = "klarna"

    @classmethod
    def get_all_methods(cls) -> List[str]:
        return [
            cls.CARD, cls.BANK_TRANSFER, cls.PAYPAL,
            cls.APPLE_PAY, cls.GOOGLE_PAY, cls.SEPA, cls.KLARNA
        ]


class PaymentIntent:
    """
    Payment intent model for managing payment processing workflows.

    Represents a payment intent from initial creation through completion.
    Tracks payment status, amount, fees, and provider-specific details.
    """

    def __init__(self, user_id: str, wallet_id: str, amount: float, currency: str = 'EUR', **kwargs):
        self._id = kwargs.get('_id', ObjectId())
        self.intent_id = kwargs.get('intent_id', str(self._id))
        self.user_id = user_id
        self.wallet_id = wallet_id

        # Payment amount and currency
        self.amount = float(amount)
        self.currency = currency.upper()
        self.net_amount = kwargs.get('net_amount', self.amount)  # Amount after fees

        # Payment provider information
        self.provider_id = kwargs.get('provider_id')
        self.provider_type = kwargs.get('provider_type')
        self.provider_payment_id = kwargs.get('provider_payment_id')  # External provider ID

        # Payment status and processing
        self.status = kwargs.get('status', PaymentIntentStatus.PENDING)
        self.payment_method = kwargs.get('payment_method')
        self.payment_method_details = kwargs.get('payment_method_details', {})

        # Fees and processing
        self.processing_fee = kwargs.get('processing_fee', 0.0)
        self.platform_fee = kwargs.get('platform_fee', 0.0)
        self.total_fees = kwargs.get('total_fees', 0.0)

        # Client and request information
        self.client_secret = kwargs.get('client_secret')  # For frontend payment confirmation
        self.return_url = kwargs.get('return_url')
        self.cancel_url = kwargs.get('cancel_url')

        # Processing attempts and retries
        self.confirmation_attempts = kwargs.get('confirmation_attempts', 0)
        self.max_confirmation_attempts = kwargs.get('max_confirmation_attempts', 3)
        self.last_attempt_at = kwargs.get('last_attempt_at')

        # Error handling
        self.last_error = kwargs.get('last_error')
        self.error_code = kwargs.get('error_code')
        self.error_details = kwargs.get('error_details', {})

        # Refund information
        self.refunded_amount = kwargs.get('refunded_amount', 0.0)
        self.refund_reason = kwargs.get('refund_reason')
        self.refunded_at = kwargs.get('refunded_at')

        # Metadata and tracking
        self.description = kwargs.get('description', 'Wallet top-up')
        self.metadata = kwargs.get('metadata', {})
        self.webhook_events = kwargs.get('webhook_events', [])

        # User context
        self.user_ip_address = kwargs.get('user_ip_address')
        self.user_agent = kwargs.get('user_agent')
        self.user_country = kwargs.get('user_country')

        # Timestamps
        self.created_at = kwargs.get('created_at', datetime.now(timezone.utc))
        self.updated_at = kwargs.get('updated_at', datetime.now(timezone.utc))
        self.expires_at = kwargs.get('expires_at')  # Payment intent expiration
        self.confirmed_at = kwargs.get('confirmed_at')
        self.processed_at = kwargs.get('processed_at')

        # Validate inputs
        self._validate_payment_intent()

    def _validate_payment_intent(self) -> None:
        """Validate payment intent data."""
        if self.amount <= 0:
            raise ValueError("Payment amount must be positive")

        if self.currency not in ['EUR', 'USD', 'GBP']:
            raise ValueError(f"Unsupported currency: {self.currency}")

        if self.status not in PaymentIntentStatus.get_all_statuses():
            raise ValueError(f"Invalid payment status: {self.status}")

        if self.payment_method and self.payment_method not in PaymentMethod.get_all_methods():
            raise ValueError(f"Invalid payment method: {self.payment_method}")

    def update_status(self, new_status: str, error_message: str = None, error_code: str = None) -> None:
        """
        Update payment intent status with optional error information.

        Args:
            new_status: New payment status
            error_message: Error message if payment failed
            error_code: Provider-specific error code
        """
        if new_status not in PaymentIntentStatus.get_all_statuses():
            raise ValueError(f"Invalid payment status: {new_status}")

        old_status = self.status
        self.status = new_status
        self.updated_at = datetime.now(timezone.utc)

        # Track status transitions
        if not hasattr(self, 'status_history'):
            self.status_history = []

        self.status_history.append({
            'from_status': old_status,
            'to_status': new_status,
            'timestamp': self.updated_at,
            'error_message': error_message,
            'error_code': error_code
        })

        # Set error information
        if error_message:
            self.last_error = error_message
            self.error_code = error_code

        # Set completion timestamps
        if new_status == PaymentIntentStatus.SUCCEEDED:
            self.confirmed_at = self.updated_at
            self.processed_at = self.updated_at
        elif new_status in [PaymentIntentStatus.FAILED, PaymentIntentStatus.CANCELLED]:
            self.processed_at = self.updated_at

    def add_webhook_event(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """
        Add webhook event to payment intent history.

        Args:
            event_type: Type of webhook event
            event_data: Event data from provider
        """
        webhook_event = {
            'event_type': event_type,
            'event_data': event_data,
            'received_at': datetime.now(timezone.utc)
        }

        if not hasattr(self, 'webhook_events'):
            self.webhook_events = []

        self.webhook_events.append(webhook_event)
        self.updated_at = datetime.now(timezone.utc)

    def calculate_fees(self, processing_fee_percentage: float, processing_fee_fixed: float,
                      platform_fee_percentage: float = 0.0) -> None:
        """
        Calculate processing and platform fees.

        Args:
            processing_fee_percentage: Provider processing fee percentage
            processing_fee_fixed: Provider fixed fee
            platform_fee_percentage: Platform fee percentage
        """
        # Calculate processing fee
        percentage_fee = self.amount * (processing_fee_percentage / 100)
        self.processing_fee = round(percentage_fee + processing_fee_fixed, 2)

        # Calculate platform fee
        self.platform_fee = round(self.amount * (platform_fee_percentage / 100), 2)

        # Calculate total fees and net amount
        self.total_fees = round(self.processing_fee + self.platform_fee, 2)
        self.net_amount = round(self.amount - self.total_fees, 2)

        self.updated_at = datetime.now(timezone.utc)

    def increment_confirmation_attempt(self) -> bool:
        """
        Increment confirmation attempt counter.

        Returns:
            True if attempts are within limit, False if exceeded
        """
        self.confirmation_attempts += 1
        self.last_attempt_at = datetime.now(timezone.utc)
        self.updated_at = self.last_attempt_at

        return self.confirmation_attempts <= self.max_confirmation_attempts

    def is_expired(self) -> bool:
        """
        Check if payment intent has expired.

        Returns:
            True if payment intent has expired
        """
        if not self.expires_at:
            return False

        return datetime.now(timezone.utc) > self.expires_at

    def can_be_confirmed(self) -> bool:
        """
        Check if payment intent can be confirmed.

        Returns:
            True if payment can be confirmed
        """
        return (
            self.status in [PaymentIntentStatus.PENDING, PaymentIntentStatus.REQUIRES_ACTION] and
            not self.is_expired() and
            self.confirmation_attempts < self.max_confirmation_attempts
        )

    def can_be_refunded(self) -> bool:
        """
        Check if payment intent can be refunded.

        Returns:
            True if payment can be refunded
        """
        return (
            self.status == PaymentIntentStatus.SUCCEEDED and
            self.refunded_amount < self.amount
        )

    def get_refundable_amount(self) -> float:
        """
        Get amount available for refund.

        Returns:
            Amount that can be refunded
        """
        if not self.can_be_refunded():
            return 0.0

        return round(self.amount - self.refunded_amount, 2)

    def process_refund(self, refund_amount: float, reason: str = None) -> bool:
        """
        Process a refund for this payment intent.

        Args:
            refund_amount: Amount to refund
            reason: Reason for refund

        Returns:
            True if refund was processed successfully
        """
        if not self.can_be_refunded():
            return False

        available_amount = self.get_refundable_amount()
        if refund_amount > available_amount:
            return False

        # Update refund information
        self.refunded_amount += refund_amount
        self.refund_reason = reason
        self.refunded_at = datetime.now(timezone.utc)

        # Update status based on refund amount
        if self.refunded_amount >= self.amount:
            self.update_status(PaymentIntentStatus.REFUNDED)
        else:
            self.update_status(PaymentIntentStatus.PARTIALLY_REFUNDED)

        return True

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert PaymentIntent to dictionary for database storage.

        Returns:
            Dictionary representation
        """
        return {
            '_id': self._id,
            'intent_id': self.intent_id,
            'user_id': self.user_id,
            'wallet_id': self.wallet_id,
            'amount': self.amount,
            'currency': self.currency,
            'net_amount': self.net_amount,
            'provider_id': self.provider_id,
            'provider_type': self.provider_type,
            'provider_payment_id': self.provider_payment_id,
            'status': self.status,
            'payment_method': self.payment_method,
            'payment_method_details': self.payment_method_details,
            'processing_fee': self.processing_fee,
            'platform_fee': self.platform_fee,
            'total_fees': self.total_fees,
            'client_secret': self.client_secret,
            'return_url': self.return_url,
            'cancel_url': self.cancel_url,
            'confirmation_attempts': self.confirmation_attempts,
            'max_confirmation_attempts': self.max_confirmation_attempts,
            'last_attempt_at': self.last_attempt_at,
            'last_error': self.last_error,
            'error_code': self.error_code,
            'error_details': self.error_details,
            'refunded_amount': self.refunded_amount,
            'refund_reason': self.refund_reason,
            'refunded_at': self.refunded_at,
            'description': self.description,
            'metadata': self.metadata,
            'webhook_events': getattr(self, 'webhook_events', []),
            'status_history': getattr(self, 'status_history', []),
            'user_ip_address': self.user_ip_address,
            'user_agent': self.user_agent,
            'user_country': self.user_country,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'expires_at': self.expires_at,
            'confirmed_at': self.confirmed_at,
            'processed_at': self.processed_at
        }

    def to_api_dict(self) -> Dict[str, Any]:
        """
        Convert PaymentIntent to dictionary for API responses.

        Returns:
            API-safe dictionary representation
        """
        return {
            'intent_id': self.intent_id,
            'amount': self.amount,
            'currency': self.currency,
            'net_amount': self.net_amount,
            'status': self.status,
            'payment_method': self.payment_method,
            'processing_fee': self.processing_fee,
            'platform_fee': self.platform_fee,
            'total_fees': self.total_fees,
            'client_secret': self.client_secret,  # Needed for frontend
            'confirmation_attempts': self.confirmation_attempts,
            'last_error': self.last_error,
            'error_code': self.error_code,
            'refunded_amount': self.refunded_amount,
            'refund_reason': self.refund_reason,
            'description': self.description,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'expires_at': self.expires_at,
            'confirmed_at': self.confirmed_at,
            'processed_at': self.processed_at,
            'can_be_confirmed': self.can_be_confirmed(),
            'can_be_refunded': self.can_be_refunded(),
            'refundable_amount': self.get_refundable_amount()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PaymentIntent':
        """
        Create PaymentIntent from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            PaymentIntent instance
        """
        return cls(**data)

    def __str__(self) -> str:
        return f"PaymentIntent({self.intent_id}:{self.status}:{self.amount}{self.currency})"

    def __repr__(self) -> str:
        return f"PaymentIntent(intent_id='{self.intent_id}', user_id='{self.user_id}', amount={self.amount}, status='{self.status}')"