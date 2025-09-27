from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from bson import ObjectId
import uuid
from enum import Enum


class TransactionType(Enum):
    """Transaction types for credits and donations."""
    EARNED = "earned"
    BONUS = "bonus"
    DONATED = "donated"
    REFUND = "refund"
    ADJUSTMENT = "adjustment"
    FEE = "fee"


class TransactionStatus(Enum):
    """Transaction status for processing tracking."""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class SourceType(Enum):
    """Source types for earned credits."""
    GAMEPLAY = "gameplay"
    TOURNAMENT = "tournament"
    CHALLENGE = "challenge"
    DAILY_BONUS = "daily_bonus"
    STREAK_BONUS = "streak_bonus"
    REFERRAL = "referral"
    MANUAL = "manual"


class Transaction:
    """
    Transaction model for tracking all credit movements and donations.
    Provides complete audit trail and supports batch operations.
    """

    def __init__(self, user_id: str, transaction_type: str, amount: float,
                 source_type: str = None, game_session_id: str = None,
                 onlus_id: str = None, multiplier_applied: float = 1.0,
                 metadata: Dict[str, Any] = None, status: str = "pending",
                 transaction_id: str = None, _id: Optional[ObjectId] = None,
                 created_at: Optional[datetime] = None, updated_at: Optional[datetime] = None,
                 processed_at: Optional[datetime] = None, receipt_data: Dict[str, Any] = None):
        self._id = _id
        self.transaction_id = transaction_id or str(uuid.uuid4())
        self.user_id = user_id
        self.transaction_type = transaction_type
        self.amount = float(amount)
        self.source_type = source_type
        self.game_session_id = game_session_id
        self.onlus_id = onlus_id
        self.multiplier_applied = float(multiplier_applied)
        self.metadata = metadata or {}
        self.status = status
        self.receipt_data = receipt_data or {}
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or datetime.now(timezone.utc)
        self.processed_at = processed_at

    def mark_completed(self, receipt_data: Dict[str, Any] = None) -> None:
        """Mark transaction as completed with optional receipt data."""
        self.status = TransactionStatus.COMPLETED.value
        self.processed_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
        if receipt_data:
            self.receipt_data.update(receipt_data)

    def mark_failed(self, error_reason: str = None) -> None:
        """Mark transaction as failed with optional error reason."""
        self.status = TransactionStatus.FAILED.value
        self.updated_at = datetime.now(timezone.utc)
        if error_reason:
            self.metadata['error_reason'] = error_reason

    def mark_cancelled(self, cancellation_reason: str = None) -> None:
        """Mark transaction as cancelled with optional reason."""
        self.status = TransactionStatus.CANCELLED.value
        self.updated_at = datetime.now(timezone.utc)
        if cancellation_reason:
            self.metadata['cancellation_reason'] = cancellation_reason

    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata to the transaction."""
        self.metadata[key] = value
        self.updated_at = datetime.now(timezone.utc)

    def is_completed(self) -> bool:
        """Check if transaction is completed."""
        return self.status == TransactionStatus.COMPLETED.value

    def is_pending(self) -> bool:
        """Check if transaction is pending."""
        return self.status == TransactionStatus.PENDING.value

    def is_failed(self) -> bool:
        """Check if transaction is failed."""
        return self.status == TransactionStatus.FAILED.value

    def get_effective_amount(self) -> float:
        """Get the effective amount after applying multipliers."""
        return round(self.amount * self.multiplier_applied, 2)

    def get_base_amount(self) -> float:
        """Get the base amount before multipliers."""
        return round(self.amount, 2)

    def generate_receipt(self) -> Dict[str, Any]:
        """Generate receipt data for the transaction."""
        receipt = {
            'transaction_id': self.transaction_id,
            'type': self.transaction_type,
            'amount': self.get_effective_amount(),
            'base_amount': self.get_base_amount(),
            'multiplier': self.multiplier_applied,
            'date': self.processed_at or self.created_at,
            'status': self.status
        }

        if self.transaction_type == TransactionType.DONATED.value:
            receipt.update({
                'onlus_id': self.onlus_id,
                'donation_receipt': self.receipt_data.get('donation_receipt'),
                'tax_deductible': self.receipt_data.get('tax_deductible', True)
            })
        elif self.transaction_type == TransactionType.EARNED.value:
            receipt.update({
                'source': self.source_type,
                'game_session_id': self.game_session_id,
                'play_duration': self.metadata.get('play_duration_ms'),
                'game_type': self.metadata.get('game_type')
            })

        return receipt

    def to_dict(self) -> Dict[str, Any]:
        """Convert transaction to dictionary for MongoDB storage."""
        return {
            '_id': self._id,
            'transaction_id': self.transaction_id,
            'user_id': self.user_id,
            'transaction_type': self.transaction_type,
            'amount': self.amount,
            'source_type': self.source_type,
            'game_session_id': self.game_session_id,
            'onlus_id': self.onlus_id,
            'multiplier_applied': self.multiplier_applied,
            'metadata': self.metadata,
            'status': self.status,
            'receipt_data': self.receipt_data,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'processed_at': self.processed_at
        }

    def to_api_dict(self) -> Dict[str, Any]:
        """Convert transaction to dictionary for API responses."""
        return {
            'id': str(self._id) if self._id else None,
            'transaction_id': self.transaction_id,
            'user_id': self.user_id,
            'type': self.transaction_type,
            'amount': self.get_base_amount(),
            'effective_amount': self.get_effective_amount(),
            'multiplier_applied': self.multiplier_applied,
            'source_type': self.source_type,
            'game_session_id': self.game_session_id,
            'onlus_id': self.onlus_id,
            'status': self.status,
            'metadata': self.metadata,
            'receipt_available': bool(self.receipt_data),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Transaction':
        """Create Transaction instance from dictionary."""
        return cls(
            _id=data.get('_id'),
            transaction_id=data.get('transaction_id'),
            user_id=data.get('user_id'),
            transaction_type=data.get('transaction_type'),
            amount=data.get('amount', 0.0),
            source_type=data.get('source_type'),
            game_session_id=data.get('game_session_id'),
            onlus_id=data.get('onlus_id'),
            multiplier_applied=data.get('multiplier_applied', 1.0),
            metadata=data.get('metadata', {}),
            status=data.get('status', 'pending'),
            receipt_data=data.get('receipt_data', {}),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
            processed_at=data.get('processed_at')
        )

    @staticmethod
    def validate_transaction_data(data: Dict[str, Any]) -> Optional[str]:
        """
        Validate transaction data for creation/updates.

        Args:
            data: Transaction data to validate

        Returns:
            str: Error message if validation fails, None if valid
        """
        if not isinstance(data, dict):
            return "TRANSACTION_DATA_INVALID_FORMAT"

        # Required fields
        required_fields = ['user_id', 'transaction_type', 'amount']
        for field in required_fields:
            if field not in data or not data[field]:
                return f"TRANSACTION_{field.upper()}_REQUIRED"

        # Validate transaction type
        if data['transaction_type'] not in [t.value for t in TransactionType]:
            return "TRANSACTION_TYPE_INVALID"

        # Validate amount
        amount = data['amount']
        if not isinstance(amount, (int, float)) or amount <= 0:
            return "TRANSACTION_AMOUNT_INVALID"

        # Validate large amounts (fraud prevention)
        if amount > 10000:  # €10,000 limit
            return "TRANSACTION_AMOUNT_TOO_LARGE"

        # Validate source type for earned transactions
        if data['transaction_type'] == TransactionType.EARNED.value:
            if 'source_type' not in data:
                return "TRANSACTION_SOURCE_TYPE_REQUIRED"
            if data['source_type'] not in [s.value for s in SourceType]:
                return "TRANSACTION_SOURCE_TYPE_INVALID"

        # Validate donation fields
        if data['transaction_type'] == TransactionType.DONATED.value:
            if 'onlus_id' not in data or not data['onlus_id']:
                return "TRANSACTION_ONLUS_ID_REQUIRED"

        # Validate multiplier
        if 'multiplier_applied' in data:
            multiplier = data['multiplier_applied']
            if not isinstance(multiplier, (int, float)) or multiplier < 0 or multiplier > 10:
                return "TRANSACTION_MULTIPLIER_INVALID"

        # Validate status
        if 'status' in data:
            if data['status'] not in [s.value for s in TransactionStatus]:
                return "TRANSACTION_STATUS_INVALID"

        return None

    @classmethod
    def create_earned_transaction(cls, user_id: str, amount: float, source_type: str,
                                  game_session_id: str = None, multiplier: float = 1.0,
                                  metadata: Dict[str, Any] = None) -> 'Transaction':
        """
        Create a new earned credits transaction.

        Args:
            user_id: User ID earning the credits
            amount: Base amount earned
            source_type: Source of the earnings
            game_session_id: Associated game session (if applicable)
            multiplier: Multiplier applied to base amount
            metadata: Additional transaction metadata

        Returns:
            Transaction: New transaction instance
        """
        return cls(
            user_id=user_id,
            transaction_type=TransactionType.EARNED.value,
            amount=amount,
            source_type=source_type,
            game_session_id=game_session_id,
            multiplier_applied=multiplier,
            metadata=metadata or {},
            status=TransactionStatus.PENDING.value
        )

    @classmethod
    def create_donation_transaction(cls, user_id: str, amount: float, onlus_id: str,
                                    metadata: Dict[str, Any] = None) -> 'Transaction':
        """
        Create a new donation transaction.

        Args:
            user_id: User ID making the donation
            amount: Donation amount
            onlus_id: ONLUS receiving the donation
            metadata: Additional transaction metadata

        Returns:
            Transaction: New transaction instance
        """
        return cls(
            user_id=user_id,
            transaction_type=TransactionType.DONATED.value,
            amount=amount,
            onlus_id=onlus_id,
            metadata=metadata or {},
            status=TransactionStatus.PENDING.value
        )

    @classmethod
    def create_batch_transactions(cls, transactions_data: List[Dict[str, Any]]) -> List['Transaction']:
        """
        Create multiple transactions for batch processing.

        Args:
            transactions_data: List of transaction data dictionaries

        Returns:
            List[Transaction]: List of transaction instances
        """
        transactions = []
        for data in transactions_data:
            validation_error = cls.validate_transaction_data(data)
            if validation_error:
                continue  # Skip invalid transactions
            transactions.append(cls.from_dict(data))
        return transactions

    def get_fraud_risk_indicators(self) -> Dict[str, Any]:
        """
        Get fraud risk indicators for this transaction.

        Returns:
            Dict containing fraud risk indicators
        """
        risk_indicators = {
            'large_amount': self.get_effective_amount() > 1000,
            'rapid_succession': False,  # Will be calculated by fraud service
            'unusual_source': self.source_type == SourceType.MANUAL.value,
            'high_multiplier': self.multiplier_applied > 3.0,
            'off_hours': self.created_at.hour < 6 or self.created_at.hour > 23,
            'weekend': self.created_at.weekday() >= 5
        }
        return risk_indicators

    def __repr__(self) -> str:
        return f'<Transaction {self.transaction_id}: {self.transaction_type} {self.get_effective_amount()}€>'