from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from bson import ObjectId
from enum import Enum


class AllocationRequestStatus(Enum):
    """Status of allocation request."""
    PENDING = "pending"  # Request created, waiting for processing
    APPROVED = "approved"  # Request approved for processing
    PROCESSING = "processing"  # Currently being processed
    COMPLETED = "completed"  # Allocation completed successfully
    REJECTED = "rejected"  # Request rejected
    CANCELLED = "cancelled"  # Request cancelled


class AllocationPriority(Enum):
    """Priority levels for allocation requests."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4
    EMERGENCY = 5


class AllocationRequest:
    """
    Model for donation allocation requests.

    Represents requests for fund allocation to ONLUS organizations
    with priority scoring and smart allocation criteria.

    Collection: allocation_requests
    """

    def __init__(self, onlus_id: str, requested_amount: float,
                 project_title: str, project_description: str,
                 urgency_level: int = 2, category: str = None,
                 expected_impact: str = None, deadline: Optional[datetime] = None,
                 special_requirements: Dict[str, Any] = None,
                 donor_preferences: List[str] = None,
                 supporting_documents: List[str] = None,
                 request_type: str = "general",
                 status: str = "pending", priority: int = 2,
                 _id: Optional[ObjectId] = None,
                 created_at: Optional[datetime] = None,
                 updated_at: Optional[datetime] = None,
                 processed_at: Optional[datetime] = None,
                 approval_notes: str = None, rejection_reason: str = None,
                 allocation_score: float = 0.0, metadata: Dict[str, Any] = None):
        self._id = _id
        self.onlus_id = onlus_id
        self.requested_amount = float(requested_amount)
        self.project_title = project_title.strip()
        self.project_description = project_description.strip()
        self.urgency_level = urgency_level
        self.category = category
        self.expected_impact = expected_impact
        self.deadline = deadline
        self.special_requirements = special_requirements or {}
        self.donor_preferences = donor_preferences or []
        self.supporting_documents = supporting_documents or []
        self.request_type = request_type
        self.status = status
        self.priority = priority
        self.approval_notes = approval_notes
        self.rejection_reason = rejection_reason
        self.allocation_score = float(allocation_score)
        self.metadata = metadata or {}
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or datetime.now(timezone.utc)
        self.processed_at = processed_at

    def approve_request(self, approval_notes: str = None) -> None:
        """Approve the allocation request."""
        self.status = AllocationRequestStatus.APPROVED.value
        self.approval_notes = approval_notes
        self.updated_at = datetime.now(timezone.utc)

    def reject_request(self, rejection_reason: str) -> None:
        """Reject the allocation request with reason."""
        self.status = AllocationRequestStatus.REJECTED.value
        self.rejection_reason = rejection_reason
        self.updated_at = datetime.now(timezone.utc)

    def start_processing(self) -> None:
        """Mark request as being processed."""
        self.status = AllocationRequestStatus.PROCESSING.value
        self.updated_at = datetime.now(timezone.utc)

    def complete_processing(self) -> None:
        """Mark request as completed."""
        self.status = AllocationRequestStatus.COMPLETED.value
        self.processed_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    def cancel_request(self) -> None:
        """Cancel the allocation request."""
        self.status = AllocationRequestStatus.CANCELLED.value
        self.updated_at = datetime.now(timezone.utc)

    def update_allocation_score(self, score: float) -> None:
        """Update the allocation score calculated by the engine."""
        self.allocation_score = float(score)
        self.updated_at = datetime.now(timezone.utc)

    def is_expired(self) -> bool:
        """Check if request has expired based on deadline."""
        if not self.deadline:
            return False
        return datetime.now(timezone.utc) > self.deadline

    def is_emergency(self) -> bool:
        """Check if this is an emergency allocation request."""
        return self.priority == AllocationPriority.EMERGENCY.value

    def get_days_until_deadline(self) -> Optional[int]:
        """Get number of days until deadline."""
        if not self.deadline:
            return None
        delta = self.deadline - datetime.now(timezone.utc)
        return max(0, delta.days)

    def to_dict(self) -> Dict[str, Any]:
        """Convert allocation request to dictionary."""
        return {
            '_id': self._id,
            'onlus_id': self.onlus_id,
            'requested_amount': self.requested_amount,
            'project_title': self.project_title,
            'project_description': self.project_description,
            'urgency_level': self.urgency_level,
            'category': self.category,
            'expected_impact': self.expected_impact,
            'deadline': self.deadline,
            'special_requirements': self.special_requirements,
            'donor_preferences': self.donor_preferences,
            'supporting_documents': self.supporting_documents,
            'request_type': self.request_type,
            'status': self.status,
            'priority': self.priority,
            'approval_notes': self.approval_notes,
            'rejection_reason': self.rejection_reason,
            'allocation_score': self.allocation_score,
            'metadata': self.metadata,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'processed_at': self.processed_at,
            'is_expired': self.is_expired(),
            'days_until_deadline': self.get_days_until_deadline()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AllocationRequest':
        """Create allocation request from dictionary."""
        return cls(**data)

    def __str__(self) -> str:
        return f"AllocationRequest({self.project_title}, {self.requested_amount}€, {self.status})"

    def __repr__(self) -> str:
        return self.__str__()