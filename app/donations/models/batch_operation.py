from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from bson import ObjectId
import json


class BatchOperationType:
    """Batch operation type constants."""
    DONATIONS = "donations"
    PAYOUTS = "payouts"
    RECONCILIATION = "reconciliation"
    REFUNDS = "refunds"
    COMPLIANCE_CHECK = "compliance_check"

    @classmethod
    def get_all_types(cls) -> List[str]:
        return [cls.DONATIONS, cls.PAYOUTS, cls.RECONCILIATION, cls.REFUNDS, cls.COMPLIANCE_CHECK]


class BatchOperationStatus:
    """Batch operation status constants."""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"
    CANCELLED = "cancelled"

    @classmethod
    def get_all_statuses(cls) -> List[str]:
        return [cls.QUEUED, cls.PROCESSING, cls.COMPLETED, cls.FAILED, cls.PARTIAL, cls.CANCELLED]

    @classmethod
    def get_final_statuses(cls) -> List[str]:
        """Get statuses that indicate batch is finalized."""
        return [cls.COMPLETED, cls.FAILED, cls.PARTIAL, cls.CANCELLED]


class BatchOperation:
    """
    Batch operation model for managing bulk operations.

    Represents a batch processing job for multiple donations, payouts, or other operations.
    Tracks progress, errors, and completion status for efficient bulk processing.
    """

    def __init__(self, operation_type: str, **kwargs):
        self._id = kwargs.get('_id', ObjectId())
        self.batch_id = kwargs.get('batch_id', str(self._id))
        self.operation_type = operation_type

        # Batch configuration
        self.total_items = kwargs.get('total_items', 0)
        self.processed_items = kwargs.get('processed_items', 0)
        self.successful_items = kwargs.get('successful_items', 0)
        self.failed_items = kwargs.get('failed_items', 0)
        self.skipped_items = kwargs.get('skipped_items', 0)

        # Status and progress
        self.status = kwargs.get('status', BatchOperationStatus.QUEUED)
        self.progress_percentage = kwargs.get('progress_percentage', 0.0)

        # Timing information
        self.created_at = kwargs.get('created_at', datetime.now(timezone.utc))
        self.started_at = kwargs.get('started_at')
        self.completed_at = kwargs.get('completed_at')
        self.last_updated_at = kwargs.get('last_updated_at', datetime.now(timezone.utc))

        # Processing configuration
        self.batch_size = kwargs.get('batch_size', 100)  # Items per batch
        self.max_retries = kwargs.get('max_retries', 3)
        self.retry_delay_seconds = kwargs.get('retry_delay_seconds', 30)

        # Error handling and logs
        self.error_log = kwargs.get('error_log', [])
        self.last_error = kwargs.get('last_error')
        self.error_count = kwargs.get('error_count', 0)

        # Processing metadata
        self.metadata = kwargs.get('metadata', {})
        self.configuration = kwargs.get('configuration', {})

        # Administrative information
        self.created_by = kwargs.get('created_by')  # User or system that created the batch
        self.assigned_worker = kwargs.get('assigned_worker')  # Worker processing the batch
        self.priority = kwargs.get('priority', 1)  # Processing priority (higher = more important)

        # Results and summary
        self.results_summary = kwargs.get('results_summary', {})
        self.output_data = kwargs.get('output_data', {})

        # Validate inputs
        self._validate_batch_operation()

    def _validate_batch_operation(self) -> None:
        """Validate batch operation data."""
        if self.operation_type not in BatchOperationType.get_all_types():
            raise ValueError(f"Invalid operation type: {self.operation_type}")

        if self.status not in BatchOperationStatus.get_all_statuses():
            raise ValueError(f"Invalid batch status: {self.status}")

        if self.total_items < 0:
            raise ValueError("Total items cannot be negative")

        if self.batch_size <= 0:
            raise ValueError("Batch size must be positive")

        if self.max_retries < 0:
            raise ValueError("Max retries cannot be negative")

    def start_processing(self, worker_id: str = None) -> None:
        """
        Mark batch as started and assign worker.

        Args:
            worker_id: Optional worker identifier
        """
        self.status = BatchOperationStatus.PROCESSING
        self.started_at = datetime.now(timezone.utc)
        self.last_updated_at = self.started_at
        self.assigned_worker = worker_id

    def update_progress(self, processed_count: int, successful_count: int = None,
                       failed_count: int = None) -> None:
        """
        Update batch processing progress.

        Args:
            processed_count: Total items processed so far
            successful_count: Number of successful items
            failed_count: Number of failed items
        """
        self.processed_items = processed_count

        if successful_count is not None:
            self.successful_items = successful_count

        if failed_count is not None:
            self.failed_items = failed_count

        # Calculate progress percentage
        if self.total_items > 0:
            self.progress_percentage = round((self.processed_items / self.total_items) * 100, 2)

        self.last_updated_at = datetime.now(timezone.utc)

        # Auto-update status based on progress
        if self.processed_items >= self.total_items:
            if self.failed_items == 0:
                self.status = BatchOperationStatus.COMPLETED
            elif self.successful_items > 0:
                self.status = BatchOperationStatus.PARTIAL
            else:
                self.status = BatchOperationStatus.FAILED

            self.completed_at = self.last_updated_at

    def add_error(self, error_message: str, item_id: str = None, error_details: Dict[str, Any] = None) -> None:
        """
        Add error to batch operation log.

        Args:
            error_message: Error message
            item_id: Optional item identifier that failed
            error_details: Additional error details
        """
        error_entry = {
            'timestamp': datetime.now(timezone.utc),
            'message': error_message,
            'item_id': item_id,
            'details': error_details or {}
        }

        self.error_log.append(error_entry)
        self.error_count += 1
        self.last_error = error_message
        self.last_updated_at = datetime.now(timezone.utc)

        # Limit error log size to prevent memory issues
        if len(self.error_log) > 1000:
            self.error_log = self.error_log[-1000:]

    def complete_operation(self, success: bool, results_summary: Dict[str, Any] = None) -> None:
        """
        Mark batch operation as completed.

        Args:
            success: Whether operation completed successfully
            results_summary: Summary of operation results
        """
        if success:
            if self.failed_items == 0:
                self.status = BatchOperationStatus.COMPLETED
            else:
                self.status = BatchOperationStatus.PARTIAL
        else:
            self.status = BatchOperationStatus.FAILED

        self.completed_at = datetime.now(timezone.utc)
        self.last_updated_at = self.completed_at

        if results_summary:
            self.results_summary = results_summary

        # Ensure progress is 100% if completed
        if self.status in [BatchOperationStatus.COMPLETED, BatchOperationStatus.PARTIAL]:
            self.progress_percentage = 100.0

    def cancel_operation(self, reason: str = None) -> None:
        """
        Cancel batch operation.

        Args:
            reason: Optional cancellation reason
        """
        self.status = BatchOperationStatus.CANCELLED
        self.completed_at = datetime.now(timezone.utc)
        self.last_updated_at = self.completed_at

        if reason:
            self.add_error(f"Operation cancelled: {reason}")

    def is_processing(self) -> bool:
        """
        Check if batch is currently being processed.

        Returns:
            True if batch is in processing state
        """
        return self.status == BatchOperationStatus.PROCESSING

    def is_completed(self) -> bool:
        """
        Check if batch operation is completed (successfully or with errors).

        Returns:
            True if batch is in a final state
        """
        return self.status in BatchOperationStatus.get_final_statuses()

    def can_be_retried(self) -> bool:
        """
        Check if batch operation can be retried.

        Returns:
            True if batch can be retried
        """
        return (
            self.status in [BatchOperationStatus.FAILED, BatchOperationStatus.PARTIAL] and
            self.error_count <= self.max_retries
        )

    def get_processing_duration(self) -> Optional[float]:
        """
        Get processing duration in seconds.

        Returns:
            Duration in seconds or None if not completed
        """
        if not self.started_at:
            return None

        end_time = self.completed_at or datetime.now(timezone.utc)
        duration = (end_time - self.started_at).total_seconds()
        return round(duration, 2)

    def get_success_rate(self) -> float:
        """
        Get success rate as percentage.

        Returns:
            Success rate percentage
        """
        if self.processed_items == 0:
            return 0.0

        return round((self.successful_items / self.processed_items) * 100, 2)

    def get_estimated_completion_time(self) -> Optional[datetime]:
        """
        Estimate completion time based on current progress.

        Returns:
            Estimated completion time or None if cannot estimate
        """
        if (
            not self.started_at or
            self.processed_items == 0 or
            self.progress_percentage >= 100.0 or
            self.status != BatchOperationStatus.PROCESSING
        ):
            return None

        # Calculate processing rate
        elapsed_seconds = (datetime.now(timezone.utc) - self.started_at).total_seconds()
        items_per_second = self.processed_items / elapsed_seconds

        if items_per_second <= 0:
            return None

        # Calculate remaining time
        remaining_items = self.total_items - self.processed_items
        remaining_seconds = remaining_items / items_per_second

        return datetime.now(timezone.utc) + timezone.utc.fromutc(
            datetime.fromtimestamp(remaining_seconds)
        ).replace(tzinfo=timezone.utc) - datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert BatchOperation to dictionary for database storage.

        Returns:
            Dictionary representation
        """
        return {
            '_id': self._id,
            'batch_id': self.batch_id,
            'operation_type': self.operation_type,
            'total_items': self.total_items,
            'processed_items': self.processed_items,
            'successful_items': self.successful_items,
            'failed_items': self.failed_items,
            'skipped_items': self.skipped_items,
            'status': self.status,
            'progress_percentage': self.progress_percentage,
            'created_at': self.created_at,
            'started_at': self.started_at,
            'completed_at': self.completed_at,
            'last_updated_at': self.last_updated_at,
            'batch_size': self.batch_size,
            'max_retries': self.max_retries,
            'retry_delay_seconds': self.retry_delay_seconds,
            'error_log': self.error_log,
            'last_error': self.last_error,
            'error_count': self.error_count,
            'metadata': self.metadata,
            'configuration': self.configuration,
            'created_by': self.created_by,
            'assigned_worker': self.assigned_worker,
            'priority': self.priority,
            'results_summary': self.results_summary,
            'output_data': self.output_data
        }

    def to_api_dict(self) -> Dict[str, Any]:
        """
        Convert BatchOperation to dictionary for API responses.

        Returns:
            API-safe dictionary representation
        """
        api_dict = {
            'batch_id': self.batch_id,
            'operation_type': self.operation_type,
            'status': self.status,
            'progress': {
                'total_items': self.total_items,
                'processed_items': self.processed_items,
                'successful_items': self.successful_items,
                'failed_items': self.failed_items,
                'skipped_items': self.skipped_items,
                'progress_percentage': self.progress_percentage,
                'success_rate': self.get_success_rate()
            },
            'timing': {
                'created_at': self.created_at,
                'started_at': self.started_at,
                'completed_at': self.completed_at,
                'last_updated_at': self.last_updated_at,
                'processing_duration': self.get_processing_duration(),
                'estimated_completion_time': self.get_estimated_completion_time()
            },
            'configuration': {
                'batch_size': self.batch_size,
                'max_retries': self.max_retries,
                'priority': self.priority
            },
            'error_info': {
                'error_count': self.error_count,
                'last_error': self.last_error,
                'recent_errors': self.error_log[-5:] if self.error_log else []  # Last 5 errors
            },
            'metadata': self.metadata,
            'results_summary': self.results_summary,
            'can_be_retried': self.can_be_retried(),
            'is_processing': self.is_processing(),
            'is_completed': self.is_completed()
        }

        return api_dict

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BatchOperation':
        """
        Create BatchOperation from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            BatchOperation instance
        """
        return cls(**data)

    def __str__(self) -> str:
        return f"BatchOperation({self.batch_id}:{self.operation_type}:{self.status})"

    def __repr__(self) -> str:
        return f"BatchOperation(batch_id='{self.batch_id}', type='{self.operation_type}', status='{self.status}', progress={self.progress_percentage}%)"