from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from enum import Enum


class ComplianceCheckType(Enum):
    """Types of compliance checks."""
    AML = "aml"  # Anti-Money Laundering
    KYC = "kyc"  # Know Your Customer
    SANCTIONS = "sanctions"  # Sanctions screening
    PEP = "pep"  # Politically Exposed Person
    FRAUD = "fraud"  # Fraud detection
    TAX_COMPLIANCE = "tax_compliance"  # Tax compliance check


class ComplianceCheckStatus(Enum):
    """Status of compliance checks."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    PASSED = "passed"
    FAILED = "failed"
    REQUIRES_REVIEW = "requires_review"
    EXEMPTED = "exempted"
    EXPIRED = "expired"


class ComplianceRiskLevel(Enum):
    """Risk levels for compliance."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ComplianceCheck:
    """
    Model for compliance checks (AML, KYC, etc.).

    Tracks compliance verification for users and transactions
    to ensure regulatory compliance and risk management.
    """

    def __init__(self, user_id: str, check_type: str, **kwargs):
        self.check_id: str = kwargs.get('check_id', self._generate_check_id())
        self.user_id: str = user_id
        self.check_type: ComplianceCheckType = ComplianceCheckType(check_type)
        self.status: ComplianceCheckStatus = ComplianceCheckStatus(kwargs.get('status', 'pending'))
        self.risk_level: ComplianceRiskLevel = ComplianceRiskLevel(kwargs.get('risk_level', 'medium'))

        # Check details
        self.transaction_id: Optional[str] = kwargs.get('transaction_id')
        self.check_reason: str = kwargs.get('check_reason', '')
        self.check_criteria: Dict[str, Any] = kwargs.get('check_criteria', {})
        self.check_results: Dict[str, Any] = kwargs.get('check_results', {})

        # Risk scoring
        self.risk_score: float = kwargs.get('risk_score', 0.0)  # 0-100 scale
        self.risk_factors: List[str] = kwargs.get('risk_factors', [])
        self.compliance_score: float = kwargs.get('compliance_score', 0.0)  # 0-100 scale

        # Check metadata
        self.data_sources: List[str] = kwargs.get('data_sources', [])
        self.external_check_ids: Dict[str, str] = kwargs.get('external_check_ids', {})
        self.manual_review_required: bool = kwargs.get('manual_review_required', False)
        self.exemption_reason: Optional[str] = kwargs.get('exemption_reason')

        # Timing
        self.created_at: datetime = kwargs.get('created_at', datetime.now(timezone.utc))
        self.started_at: Optional[datetime] = kwargs.get('started_at')
        self.completed_at: Optional[datetime] = kwargs.get('completed_at')
        self.expires_at: Optional[datetime] = kwargs.get('expires_at')
        self.last_updated_at: datetime = kwargs.get('last_updated_at', datetime.now(timezone.utc))

        # Review and approval
        self.reviewed_by: Optional[str] = kwargs.get('reviewed_by')
        self.reviewed_at: Optional[datetime] = kwargs.get('reviewed_at')
        self.approval_required: bool = kwargs.get('approval_required', False)
        self.approved_by: Optional[str] = kwargs.get('approved_by')
        self.approved_at: Optional[datetime] = kwargs.get('approved_at')

        # Notifications and escalation
        self.notifications_sent: List[Dict[str, Any]] = kwargs.get('notifications_sent', [])
        self.escalation_level: int = kwargs.get('escalation_level', 0)
        self.escalated_at: Optional[datetime] = kwargs.get('escalated_at')

        # Additional metadata
        self.metadata: Dict[str, Any] = kwargs.get('metadata', {})

    def _generate_check_id(self) -> str:
        """Generate unique check ID."""
        import uuid
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        unique_id = str(uuid.uuid4())[:8].upper()
        return f"CHK-{timestamp}-{unique_id}"

    def start_check(self, started_by: str = "system") -> None:
        """Start the compliance check process."""
        self.status = ComplianceCheckStatus.IN_PROGRESS
        self.started_at = datetime.now(timezone.utc)
        self.last_updated_at = datetime.now(timezone.utc)
        self.metadata['started_by'] = started_by

    def complete_check(self, passed: bool, results: Dict[str, Any],
                      completed_by: str = "system") -> None:
        """Complete the compliance check with results."""
        self.status = ComplianceCheckStatus.PASSED if passed else ComplianceCheckStatus.FAILED
        self.completed_at = datetime.now(timezone.utc)
        self.last_updated_at = datetime.now(timezone.utc)
        self.check_results.update(results)
        self.metadata['completed_by'] = completed_by

        # Determine if manual review is required
        if not passed or self.risk_score > 70:
            self.manual_review_required = True
            self.status = ComplianceCheckStatus.REQUIRES_REVIEW

    def require_review(self, reason: str) -> None:
        """Mark check as requiring manual review."""
        self.status = ComplianceCheckStatus.REQUIRES_REVIEW
        self.manual_review_required = True
        self.check_reason = reason
        self.last_updated_at = datetime.now(timezone.utc)

    def approve_check(self, approved_by: str, approval_reason: str = "") -> None:
        """Approve the compliance check after review."""
        self.status = ComplianceCheckStatus.PASSED
        self.approved_by = approved_by
        self.approved_at = datetime.now(timezone.utc)
        self.last_updated_at = datetime.now(timezone.utc)
        self.metadata['approval_reason'] = approval_reason

    def reject_check(self, rejected_by: str, rejection_reason: str) -> None:
        """Reject the compliance check after review."""
        self.status = ComplianceCheckStatus.FAILED
        self.reviewed_by = rejected_by
        self.reviewed_at = datetime.now(timezone.utc)
        self.last_updated_at = datetime.now(timezone.utc)
        self.metadata['rejection_reason'] = rejection_reason

    def exempt_check(self, exempted_by: str, exemption_reason: str) -> None:
        """Exempt the user/transaction from this compliance check."""
        self.status = ComplianceCheckStatus.EXEMPTED
        self.exemption_reason = exemption_reason
        self.approved_by = exempted_by
        self.approved_at = datetime.now(timezone.utc)
        self.last_updated_at = datetime.now(timezone.utc)

    def escalate_check(self, escalation_reason: str) -> None:
        """Escalate the compliance check to higher authority."""
        self.escalation_level += 1
        self.escalated_at = datetime.now(timezone.utc)
        self.last_updated_at = datetime.now(timezone.utc)
        self.metadata['escalation_reason'] = escalation_reason

    def add_risk_factor(self, risk_factor: str, weight: float = 1.0) -> None:
        """Add a risk factor and update risk score."""
        if risk_factor not in self.risk_factors:
            self.risk_factors.append(risk_factor)
            self.risk_score = min(100.0, self.risk_score + weight * 10)
            self.last_updated_at = datetime.now(timezone.utc)

    def update_risk_level(self) -> None:
        """Update risk level based on current risk score."""
        if self.risk_score >= 80:
            self.risk_level = ComplianceRiskLevel.CRITICAL
        elif self.risk_score >= 60:
            self.risk_level = ComplianceRiskLevel.HIGH
        elif self.risk_score >= 30:
            self.risk_level = ComplianceRiskLevel.MEDIUM
        else:
            self.risk_level = ComplianceRiskLevel.LOW

    def add_notification(self, notification_type: str, recipient: str,
                        message: str, sent_at: datetime = None) -> None:
        """Add notification record."""
        notification = {
            'type': notification_type,
            'recipient': recipient,
            'message': message,
            'sent_at': sent_at or datetime.now(timezone.utc),
            'notification_id': f"NOTIF-{len(self.notifications_sent) + 1}"
        }
        self.notifications_sent.append(notification)

    def is_expired(self) -> bool:
        """Check if the compliance check has expired."""
        if not self.expires_at:
            return False
        return datetime.now(timezone.utc) > self.expires_at

    def is_pending(self) -> bool:
        """Check if the compliance check is pending."""
        return self.status == ComplianceCheckStatus.PENDING

    def is_in_progress(self) -> bool:
        """Check if the compliance check is in progress."""
        return self.status == ComplianceCheckStatus.IN_PROGRESS

    def is_completed(self) -> bool:
        """Check if the compliance check is completed."""
        return self.status in [
            ComplianceCheckStatus.PASSED,
            ComplianceCheckStatus.FAILED,
            ComplianceCheckStatus.EXEMPTED
        ]

    def requires_manual_review(self) -> bool:
        """Check if manual review is required."""
        return self.manual_review_required or self.status == ComplianceCheckStatus.REQUIRES_REVIEW

    def get_duration_seconds(self) -> Optional[float]:
        """Get duration of the check in seconds."""
        if not self.started_at:
            return None
        end_time = self.completed_at or datetime.now(timezone.utc)
        return (end_time - self.started_at).total_seconds()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            'check_id': self.check_id,
            'user_id': self.user_id,
            'check_type': self.check_type.value,
            'status': self.status.value,
            'risk_level': self.risk_level.value,
            'transaction_id': self.transaction_id,
            'check_reason': self.check_reason,
            'check_criteria': self.check_criteria,
            'check_results': self.check_results,
            'risk_score': self.risk_score,
            'risk_factors': self.risk_factors,
            'compliance_score': self.compliance_score,
            'data_sources': self.data_sources,
            'external_check_ids': self.external_check_ids,
            'manual_review_required': self.manual_review_required,
            'exemption_reason': self.exemption_reason,
            'created_at': self.created_at,
            'started_at': self.started_at,
            'completed_at': self.completed_at,
            'expires_at': self.expires_at,
            'last_updated_at': self.last_updated_at,
            'reviewed_by': self.reviewed_by,
            'reviewed_at': self.reviewed_at,
            'approval_required': self.approval_required,
            'approved_by': self.approved_by,
            'approved_at': self.approved_at,
            'notifications_sent': self.notifications_sent,
            'escalation_level': self.escalation_level,
            'escalated_at': self.escalated_at,
            'metadata': self.metadata
        }

    def to_api_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            'check_id': self.check_id,
            'user_id': self.user_id,
            'check_type': self.check_type.value,
            'status': self.status.value,
            'risk_level': self.risk_level.value,
            'risk_score': self.risk_score,
            'compliance_score': self.compliance_score,
            'manual_review_required': self.manual_review_required,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'duration_seconds': self.get_duration_seconds(),
            'is_expired': self.is_expired(),
            'requires_review': self.requires_manual_review(),
            'escalation_level': self.escalation_level,
            'risk_factors_count': len(self.risk_factors),
            'notifications_count': len(self.notifications_sent)
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ComplianceCheck':
        """Create ComplianceCheck from dictionary."""
        return cls(
            user_id=data['user_id'],
            check_type=data['check_type'],
            **data
        )

    def __repr__(self) -> str:
        return (f"ComplianceCheck(check_id='{self.check_id}', "
                f"user_id='{self.user_id}', type='{self.check_type.value}', "
                f"status='{self.status.value}', risk_level='{self.risk_level.value}')")

    def __str__(self) -> str:
        return f"Compliance Check {self.check_id} for user {self.user_id}: {self.status.value}"