from typing import Dict, Any, Optional
from datetime import datetime, timezone
from bson import ObjectId


class BatchDonationStatus:
    """Batch donation item status constants."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRYING = "retrying"

    @classmethod
    def get_all_statuses(cls) -> list[str]:
        return [cls.PENDING, cls.PROCESSING, cls.COMPLETED, cls.FAILED, cls.SKIPPED, cls.RETRYING]

    @classmethod
    def get_final_statuses(cls) -> list[str]:
        """Get statuses that indicate item is finalized."""
        return [cls.COMPLETED, cls.FAILED, cls.SKIPPED]


class BatchDonation:
    """
    Batch donation item model for managing individual donation in batch operations.

    Represents a single donation within a batch processing operation.
    Tracks individual item status, retry attempts, and processing results.
    """

    def __init__(self, batch_id: str, user_id: str, onlus_id: str, amount: float, **kwargs):
        self._id = kwargs.get('_id', ObjectId())
        self.item_id = kwargs.get('item_id', str(self._id))
        self.batch_id = batch_id
        self.user_id = user_id
        self.onlus_id = onlus_id
        self.amount = float(amount)

        # Processing order and status
        self.processing_order = kwargs.get('processing_order', 0)
        self.status = kwargs.get('status', BatchDonationStatus.PENDING)

        # Retry handling
        self.retry_count = kwargs.get('retry_count', 0)
        self.max_retries = kwargs.get('max_retries', 3)
        self.last_retry_at = kwargs.get('last_retry_at')

        # Processing results
        self.transaction_id = kwargs.get('transaction_id')  # Resulting transaction ID
        self.processed_amount = kwargs.get('processed_amount')  # Actual processed amount
        self.processing_fee = kwargs.get('processing_fee', 0.0)

        # Error handling
        self.error_message = kwargs.get('error_message')
        self.error_code = kwargs.get('error_code')
        self.error_details = kwargs.get('error_details', {})

        # Timing information
        self.created_at = kwargs.get('created_at', datetime.now(timezone.utc))
        self.updated_at = kwargs.get('updated_at', datetime.now(timezone.utc))
        self.started_processing_at = kwargs.get('started_processing_at')
        self.completed_at = kwargs.get('completed_at')

        # Donation metadata
        self.donation_message = kwargs.get('donation_message', '')
        self.is_anonymous = kwargs.get('is_anonymous', False)
        self.source_reference = kwargs.get('source_reference')  # External reference
        self.metadata = kwargs.get('metadata', {})

        # Validation and pre-processing
        self.validation_errors = kwargs.get('validation_errors', [])
        self.pre_validation_passed = kwargs.get('pre_validation_passed', False)

        # Validate inputs
        self._validate_batch_donation()

    def _validate_batch_donation(self) -> None:
        """Validate batch donation data."""
        if self.amount <= 0:
            raise ValueError("Donation amount must be positive")

        if not self.user_id:
            raise ValueError("User ID is required")

        if not self.onlus_id:
            raise ValueError("ONLUS ID is required")

        if not self.batch_id:
            raise ValueError("Batch ID is required")

        if self.status not in BatchDonationStatus.get_all_statuses():
            raise ValueError(f"Invalid batch donation status: {self.status}")

        if self.retry_count < 0:
            raise ValueError("Retry count cannot be negative")

        if self.max_retries < 0:
            raise ValueError("Max retries cannot be negative")

    def start_processing(self) -> None:
        """Mark donation item as started processing."""
        self.status = BatchDonationStatus.PROCESSING
        self.started_processing_at = datetime.now(timezone.utc)
        self.updated_at = self.started_processing_at

    def complete_processing(self, transaction_id: str, processed_amount: float = None,
                          processing_fee: float = 0.0) -> None:
        """
        Mark donation item as completed successfully.

        Args:
            transaction_id: Resulting transaction ID
            processed_amount: Actual processed amount
            processing_fee: Processing fee charged
        """
        self.status = BatchDonationStatus.COMPLETED
        self.transaction_id = transaction_id
        self.processed_amount = processed_amount or self.amount
        self.processing_fee = processing_fee
        self.completed_at = datetime.now(timezone.utc)
        self.updated_at = self.completed_at

    def fail_processing(self, error_message: str, error_code: str = None,
                       error_details: Dict[str, Any] = None) -> None:
        """
        Mark donation item as failed.

        Args:
            error_message: Error message
            error_code: Optional error code
            error_details: Additional error details
        """
        self.status = BatchDonationStatus.FAILED
        self.error_message = error_message
        self.error_code = error_code
        self.error_details = error_details or {}
        self.completed_at = datetime.now(timezone.utc)
        self.updated_at = self.completed_at

    def skip_processing(self, reason: str) -> None:
        """
        Mark donation item as skipped.

        Args:
            reason: Reason for skipping
        """
        self.status = BatchDonationStatus.SKIPPED
        self.error_message = f"Skipped: {reason}"
        self.completed_at = datetime.now(timezone.utc)
        self.updated_at = self.completed_at

    def increment_retry(self) -> bool:
        """
        Increment retry count and check if retries are available.

        Returns:
            True if item can be retried, False if max retries exceeded
        """
        self.retry_count += 1
        self.last_retry_at = datetime.now(timezone.utc)
        self.updated_at = self.last_retry_at

        if self.retry_count >= self.max_retries:
            self.status = BatchDonationStatus.FAILED
            self.error_message = f"Maximum retries ({self.max_retries}) exceeded"
            self.completed_at = self.updated_at
            return False
        else:
            self.status = BatchDonationStatus.RETRYING
            return True

    def can_be_retried(self) -> bool:
        """
        Check if donation item can be retried.

        Returns:
            True if item can be retried
        """
        return (
            self.status in [BatchDonationStatus.FAILED, BatchDonationStatus.RETRYING] and
            self.retry_count < self.max_retries
        )

    def is_completed(self) -> bool:
        """
        Check if donation item is in final state.

        Returns:
            True if item is completed, failed, or skipped
        """
        return self.status in BatchDonationStatus.get_final_statuses()

    def is_successful(self) -> bool:
        """
        Check if donation item was processed successfully.

        Returns:
            True if item completed successfully
        """
        return self.status == BatchDonationStatus.COMPLETED and self.transaction_id is not None

    def get_processing_duration(self) -> Optional[float]:
        """
        Get processing duration in seconds.

        Returns:
            Duration in seconds or None if not completed
        """
        if not self.started_processing_at:
            return None

        end_time = self.completed_at or datetime.now(timezone.utc)
        duration = (end_time - self.started_processing_at).total_seconds()
        return round(duration, 2)

    def add_validation_error(self, error_message: str) -> None:
        """
        Add validation error to the item.

        Args:
            error_message: Validation error message
        """
        if error_message not in self.validation_errors:
            self.validation_errors.append(error_message)
        self.pre_validation_passed = False
        self.updated_at = datetime.now(timezone.utc)

    def clear_validation_errors(self) -> None:
        """Clear validation errors and mark pre-validation as passed."""
        self.validation_errors = []
        self.pre_validation_passed = True
        self.updated_at = datetime.now(timezone.utc)

    def get_net_amount(self) -> float:
        """
        Get net amount after processing fees.

        Returns:
            Net amount after fees
        """
        return round((self.processed_amount or self.amount) - self.processing_fee, 2)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert BatchDonation to dictionary for database storage.

        Returns:
            Dictionary representation
        """
        return {
            '_id': self._id,
            'item_id': self.item_id,
            'batch_id': self.batch_id,
            'user_id': self.user_id,
            'onlus_id': self.onlus_id,
            'amount': self.amount,
            'processing_order': self.processing_order,
            'status': self.status,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'last_retry_at': self.last_retry_at,
            'transaction_id': self.transaction_id,
            'processed_amount': self.processed_amount,
            'processing_fee': self.processing_fee,
            'error_message': self.error_message,
            'error_code': self.error_code,
            'error_details': self.error_details,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'started_processing_at': self.started_processing_at,
            'completed_at': self.completed_at,
            'donation_message': self.donation_message,
            'is_anonymous': self.is_anonymous,
            'source_reference': self.source_reference,
            'metadata': self.metadata,
            'validation_errors': self.validation_errors,
            'pre_validation_passed': self.pre_validation_passed
        }

    def to_api_dict(self) -> Dict[str, Any]:
        """
        Convert BatchDonation to dictionary for API responses.

        Returns:
            API-safe dictionary representation
        """
        return {
            'item_id': self.item_id,
            'batch_id': self.batch_id,
            'user_id': self.user_id,
            'onlus_id': self.onlus_id,
            'amount': self.amount,
            'processed_amount': self.processed_amount,
            'net_amount': self.get_net_amount(),
            'processing_fee': self.processing_fee,
            'processing_order': self.processing_order,
            'status': self.status,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'transaction_id': self.transaction_id,
            'error_info': {
                'error_message': self.error_message,
                'error_code': self.error_code,
                'validation_errors': self.validation_errors
            },
            'timing': {
                'created_at': self.created_at,
                'updated_at': self.updated_at,
                'started_processing_at': self.started_processing_at,
                'completed_at': self.completed_at,
                'processing_duration': self.get_processing_duration()
            },
            'donation_info': {
                'message': self.donation_message,
                'is_anonymous': self.is_anonymous,
                'source_reference': self.source_reference
            },
            'metadata': self.metadata,
            'can_be_retried': self.can_be_retried(),
            'is_completed': self.is_completed(),
            'is_successful': self.is_successful(),
            'pre_validation_passed': self.pre_validation_passed
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BatchDonation':
        """
        Create BatchDonation from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            BatchDonation instance
        """
        return cls(**data)

    def __str__(self) -> str:
        return f"BatchDonation({self.item_id}:{self.status}:{self.amount}EUR)"

    def __repr__(self) -> str:
        return f"BatchDonation(item_id='{self.item_id}', batch_id='{self.batch_id}', user_id='{self.user_id}', amount={self.amount}, status='{self.status}')"