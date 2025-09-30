from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from bson import ObjectId
from enum import Enum


class AllocationResultStatus(Enum):
    """Status of allocation result."""
    SCHEDULED = "scheduled"  # Allocation scheduled for processing
    IN_PROGRESS = "in_progress"  # Allocation is being processed
    COMPLETED = "completed"  # Allocation completed successfully
    FAILED = "failed"  # Allocation failed
    PARTIAL = "partial"  # Partial allocation completed
    CANCELLED = "cancelled"  # Allocation cancelled


class AllocationMethod(Enum):
    """Method used for allocation."""
    AUTOMATIC = "automatic"  # Automatic allocation by engine
    MANUAL = "manual"  # Manual allocation by admin
    EMERGENCY = "emergency"  # Emergency fast-track allocation
    BATCH = "batch"  # Batch processing allocation
    MATCHING = "matching"  # Corporate/institutional matching


class AllocationResult:
    """
    Model for donation allocation results.

    Represents the outcome of fund allocation to ONLUS organizations
    with detailed tracking and audit information.

    Collection: allocation_results
    """

    def __init__(self, request_id: str, onlus_id: str, donor_ids: List[str],
                 allocated_amount: float, total_donations_amount: float,
                 allocation_method: str = "automatic",
                 allocation_factors: Dict[str, float] = None,
                 processing_details: Dict[str, Any] = None,
                 transaction_ids: List[str] = None,
                 status: str = "scheduled", admin_user_id: str = None,
                 fees_deducted: float = 0.0, net_amount: float = None,
                 allocation_percentage: float = None,
                 donor_breakdown: List[Dict[str, Any]] = None,
                 matching_info: Dict[str, Any] = None,
                 impact_metrics: Dict[str, Any] = None,
                 _id: Optional[ObjectId] = None,
                 created_at: Optional[datetime] = None,
                 updated_at: Optional[datetime] = None,
                 processed_at: Optional[datetime] = None,
                 completed_at: Optional[datetime] = None,
                 error_details: Dict[str, Any] = None,
                 retry_count: int = 0, metadata: Dict[str, Any] = None):
        self._id = _id
        self.request_id = request_id
        self.onlus_id = onlus_id
        self.donor_ids = donor_ids or []
        self.allocated_amount = float(allocated_amount)
        self.total_donations_amount = float(total_donations_amount)
        self.allocation_method = allocation_method
        self.allocation_factors = allocation_factors or {}
        self.processing_details = processing_details or {}
        self.transaction_ids = transaction_ids or []
        self.status = status
        self.admin_user_id = admin_user_id
        self.fees_deducted = float(fees_deducted)
        self.net_amount = float(net_amount) if net_amount else allocated_amount - fees_deducted
        self.allocation_percentage = float(allocation_percentage) if allocation_percentage else None
        self.donor_breakdown = donor_breakdown or []
        self.matching_info = matching_info or {}
        self.impact_metrics = impact_metrics or {}
        self.error_details = error_details or {}
        self.retry_count = retry_count
        self.metadata = metadata or {}
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or datetime.now(timezone.utc)
        self.processed_at = processed_at
        self.completed_at = completed_at

    def mark_in_progress(self) -> None:
        """Mark allocation as in progress."""
        self.status = AllocationResultStatus.IN_PROGRESS.value
        self.processed_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    def mark_completed(self, transaction_ids: List[str] = None,
                      impact_metrics: Dict[str, Any] = None) -> None:
        """Mark allocation as completed."""
        self.status = AllocationResultStatus.COMPLETED.value
        self.completed_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

        if transaction_ids:
            self.transaction_ids.extend(transaction_ids)

        if impact_metrics:
            self.impact_metrics.update(impact_metrics)

    def mark_failed(self, error_message: str, error_details: Dict[str, Any] = None) -> None:
        """Mark allocation as failed with error details."""
        self.status = AllocationResultStatus.FAILED.value
        self.error_details = {
            'error_message': error_message,
            'error_time': datetime.now(timezone.utc).isoformat(),
            'retry_count': self.retry_count,
            **(error_details or {})
        }
        self.updated_at = datetime.now(timezone.utc)

    def mark_partial(self, partial_amount: float, reason: str) -> None:
        """Mark allocation as partially completed."""
        self.status = AllocationResultStatus.PARTIAL.value
        self.allocated_amount = float(partial_amount)
        self.net_amount = partial_amount - self.fees_deducted
        self.processing_details['partial_reason'] = reason
        self.processing_details['original_amount'] = self.total_donations_amount
        self.updated_at = datetime.now(timezone.utc)

    def cancel_allocation(self, reason: str) -> None:
        """Cancel the allocation."""
        self.status = AllocationResultStatus.CANCELLED.value
        self.processing_details['cancellation_reason'] = reason
        self.updated_at = datetime.now(timezone.utc)

    def retry_allocation(self) -> None:
        """Increment retry count and reset status for retry."""
        self.retry_count += 1
        self.status = AllocationResultStatus.SCHEDULED.value
        self.updated_at = datetime.now(timezone.utc)

    def add_transaction(self, transaction_id: str, donor_id: str, amount: float) -> None:
        """Add a transaction to this allocation result."""
        self.transaction_ids.append(transaction_id)

        # Update donor breakdown
        donor_entry = {
            'donor_id': donor_id,
            'amount': float(amount),
            'transaction_id': transaction_id,
            'timestamp': datetime.now(timezone.utc)
        }
        self.donor_breakdown.append(donor_entry)
        self.updated_at = datetime.now(timezone.utc)

    def calculate_efficiency_ratio(self) -> float:
        """Calculate allocation efficiency ratio (net/gross)."""
        if self.total_donations_amount <= 0:
            return 0.0
        return self.net_amount / self.total_donations_amount

    def get_processing_time_seconds(self) -> Optional[int]:
        """Get processing time in seconds."""
        if not self.processed_at or not self.completed_at:
            return None
        delta = self.completed_at - self.processed_at
        return int(delta.total_seconds())

    def is_successful(self) -> bool:
        """Check if allocation was successful (completed or partial)."""
        return self.status in [AllocationResultStatus.COMPLETED.value,
                              AllocationResultStatus.PARTIAL.value]

    def to_dict(self) -> Dict[str, Any]:
        """Convert allocation result to dictionary."""
        return {
            '_id': self._id,
            'request_id': self.request_id,
            'onlus_id': self.onlus_id,
            'donor_ids': self.donor_ids,
            'allocated_amount': self.allocated_amount,
            'total_donations_amount': self.total_donations_amount,
            'allocation_method': self.allocation_method,
            'allocation_factors': self.allocation_factors,
            'processing_details': self.processing_details,
            'transaction_ids': self.transaction_ids,
            'status': self.status,
            'admin_user_id': self.admin_user_id,
            'fees_deducted': self.fees_deducted,
            'net_amount': self.net_amount,
            'allocation_percentage': self.allocation_percentage,
            'donor_breakdown': self.donor_breakdown,
            'matching_info': self.matching_info,
            'impact_metrics': self.impact_metrics,
            'error_details': self.error_details,
            'retry_count': self.retry_count,
            'metadata': self.metadata,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'processed_at': self.processed_at,
            'completed_at': self.completed_at,
            'efficiency_ratio': self.calculate_efficiency_ratio(),
            'processing_time_seconds': self.get_processing_time_seconds(),
            'is_successful': self.is_successful()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AllocationResult':
        """Create allocation result from dictionary."""
        return cls(**data)

    def __str__(self) -> str:
        return f"AllocationResult({self.onlus_id}, {self.allocated_amount}€, {self.status})"

    def __repr__(self) -> str:
        return self.__str__()