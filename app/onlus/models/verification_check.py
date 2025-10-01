from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from bson import ObjectId
from enum import Enum


class VerificationCheckType(Enum):
    """Types of verification checks performed on ONLUS applications."""
    LEGAL_STATUS = "legal_status"  # Legal entity verification
    TAX_EXEMPT_STATUS = "tax_exempt_status"  # Tax exemption verification
    FINANCIAL_HEALTH = "financial_health"  # Financial viability assessment
    BACKGROUND_CHECK = "background_check"  # Leadership background verification
    REFERENCE_CHECK = "reference_check"  # Third-party reference verification
    INSURANCE_VERIFICATION = "insurance_verification"  # Insurance coverage verification
    OPERATIONAL_ASSESSMENT = "operational_assessment"  # Operational capability review
    IMPACT_VALIDATION = "impact_validation"  # Impact and outcome verification
    COMPLIANCE_CHECK = "compliance_check"  # Regulatory compliance verification
    FRAUD_SCREENING = "fraud_screening"  # Fraud detection screening


class CheckStatus(Enum):
    """Status of verification checks."""
    PENDING = "pending"  # Check not yet started
    IN_PROGRESS = "in_progress"  # Check currently being performed
    COMPLETED = "completed"  # Check completed successfully
    FAILED = "failed"  # Check failed or revealed issues
    MANUAL_REVIEW_REQUIRED = "manual_review_required"  # Requires manual review
    EXPIRED = "expired"  # Check results have expired
    SKIPPED = "skipped"  # Check was skipped (not applicable)


class RiskLevel(Enum):
    """Risk levels determined by verification checks."""
    LOW = "low"  # Low risk, minimal concerns
    MEDIUM = "medium"  # Medium risk, some concerns
    HIGH = "high"  # High risk, significant concerns
    CRITICAL = "critical"  # Critical risk, major red flags
    UNKNOWN = "unknown"  # Risk level undetermined


class CheckSeverity(Enum):
    """Severity of check results."""
    INFO = "info"  # Informational finding
    WARNING = "warning"  # Warning level issue
    ERROR = "error"  # Error level issue
    CRITICAL = "critical"  # Critical issue requiring attention


class VerificationCheck:
    """
    Model for ONLUS verification checks.

    Tracks individual verification checks performed during
    the ONLUS application review process.

    Collection: verification_checks
    """

    def __init__(self, application_id: str, check_type: str,
                 status: str = CheckStatus.PENDING.value,
                 risk_level: str = RiskLevel.UNKNOWN.value,
                 severity: str = CheckSeverity.INFO.value,
                 title: str = None, description: str = None,
                 performed_by: str = None, automated: bool = False,
                 check_date: Optional[datetime] = None,
                 completion_date: Optional[datetime] = None,
                 expiration_date: Optional[datetime] = None,
                 result_summary: str = None, detailed_results: Dict[str, Any] = None,
                 findings: List[Dict[str, Any]] = None,
                 recommendations: List[str] = None,
                 follow_up_required: bool = False,
                 follow_up_notes: str = None,
                 external_reference: str = None,
                 score: float = None, max_score: float = None,
                 metadata: Dict[str, Any] = None,
                 _id: Optional[ObjectId] = None,
                 created_at: Optional[datetime] = None,
                 updated_at: Optional[datetime] = None):
        """
        Initialize VerificationCheck.

        Args:
            application_id: Associated application ID
            check_type: Type of verification check
            status: Current status of the check
            risk_level: Risk level determined by check
            severity: Severity of any issues found
            title: Check title/name
            description: Check description
            performed_by: Who performed the check (user ID or system)
            automated: Whether check was automated
            check_date: When check was initiated
            completion_date: When check was completed
            expiration_date: When check results expire
            result_summary: Summary of check results
            detailed_results: Detailed check results
            findings: List of specific findings
            recommendations: List of recommendations
            follow_up_required: Whether follow-up is needed
            follow_up_notes: Notes for follow-up actions
            external_reference: External system reference ID
            score: Numerical score (if applicable)
            max_score: Maximum possible score
            metadata: Additional check metadata
            _id: MongoDB document ID
            created_at: Creation timestamp
            updated_at: Last update timestamp
        """
        self._id = _id or ObjectId()
        self.application_id = application_id
        self.check_type = check_type
        self.status = status
        self.risk_level = risk_level
        self.severity = severity
        self.title = title or self._get_default_title(check_type)
        self.description = description
        self.performed_by = performed_by
        self.automated = automated
        self.check_date = check_date or datetime.now(timezone.utc)
        self.completion_date = completion_date
        self.expiration_date = expiration_date
        self.result_summary = result_summary
        self.detailed_results = detailed_results or {}
        self.findings = findings or []
        self.recommendations = recommendations or []
        self.follow_up_required = follow_up_required
        self.follow_up_notes = follow_up_notes
        self.external_reference = external_reference
        self.score = score
        self.max_score = max_score
        self.metadata = metadata or {}
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            '_id': self._id,
            'application_id': self.application_id,
            'check_type': self.check_type,
            'status': self.status,
            'risk_level': self.risk_level,
            'severity': self.severity,
            'title': self.title,
            'description': self.description,
            'performed_by': self.performed_by,
            'automated': self.automated,
            'check_date': self.check_date,
            'completion_date': self.completion_date,
            'expiration_date': self.expiration_date,
            'result_summary': self.result_summary,
            'detailed_results': self.detailed_results,
            'findings': self.findings,
            'recommendations': self.recommendations,
            'follow_up_required': self.follow_up_required,
            'follow_up_notes': self.follow_up_notes,
            'external_reference': self.external_reference,
            'score': self.score,
            'max_score': self.max_score,
            'metadata': self.metadata,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Create instance from dictionary."""
        if not data:
            return None

        return cls(
            _id=data.get('_id'),
            application_id=data.get('application_id'),
            check_type=data.get('check_type'),
            status=data.get('status', CheckStatus.PENDING.value),
            risk_level=data.get('risk_level', RiskLevel.UNKNOWN.value),
            severity=data.get('severity', CheckSeverity.INFO.value),
            title=data.get('title'),
            description=data.get('description'),
            performed_by=data.get('performed_by'),
            automated=data.get('automated', False),
            check_date=data.get('check_date'),
            completion_date=data.get('completion_date'),
            expiration_date=data.get('expiration_date'),
            result_summary=data.get('result_summary'),
            detailed_results=data.get('detailed_results', {}),
            findings=data.get('findings', []),
            recommendations=data.get('recommendations', []),
            follow_up_required=data.get('follow_up_required', False),
            follow_up_notes=data.get('follow_up_notes'),
            external_reference=data.get('external_reference'),
            score=data.get('score'),
            max_score=data.get('max_score'),
            metadata=data.get('metadata', {}),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )

    @staticmethod
    def validate_check_data(data: Dict[str, Any]) -> Optional[str]:
        """
        Validate verification check data.

        Args:
            data: Check data to validate

        Returns:
            str: Error message if validation fails, None if valid
        """
        if not isinstance(data, dict):
            return "CHECK_DATA_INVALID"

        # Required fields
        if not data.get('application_id'):
            return "APPLICATION_ID_REQUIRED"
        if not data.get('check_type'):
            return "CHECK_TYPE_REQUIRED"

        # Validate check type
        if data['check_type'] not in [ct.value for ct in VerificationCheckType]:
            return "CHECK_TYPE_INVALID"

        # Validate status
        status = data.get('status', CheckStatus.PENDING.value)
        if status not in [s.value for s in CheckStatus]:
            return "CHECK_STATUS_INVALID"

        # Validate risk level
        risk_level = data.get('risk_level', RiskLevel.UNKNOWN.value)
        if risk_level not in [rl.value for rl in RiskLevel]:
            return "RISK_LEVEL_INVALID"

        # Validate severity
        severity = data.get('severity', CheckSeverity.INFO.value)
        if severity not in [sev.value for sev in CheckSeverity]:
            return "SEVERITY_INVALID"

        # Validate score
        score = data.get('score')
        if score is not None and not isinstance(score, (int, float)):
            return "SCORE_INVALID"

        max_score = data.get('max_score')
        if max_score is not None and not isinstance(max_score, (int, float)):
            return "MAX_SCORE_INVALID"

        if score is not None and max_score is not None and score > max_score:
            return "SCORE_EXCEEDS_MAXIMUM"

        return None

    def start_check(self, performed_by: str = None):
        """Start the verification check."""
        self.status = CheckStatus.IN_PROGRESS.value
        self.performed_by = performed_by
        self.check_date = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    def complete_check(self, result_summary: str, risk_level: str = None,
                      findings: List[Dict[str, Any]] = None,
                      recommendations: List[str] = None,
                      score: float = None):
        """Complete the verification check with results."""
        self.status = CheckStatus.COMPLETED.value
        self.completion_date = datetime.now(timezone.utc)
        self.result_summary = result_summary

        if risk_level:
            self.risk_level = risk_level
        if findings:
            self.findings = findings
        if recommendations:
            self.recommendations = recommendations
        if score is not None:
            self.score = score

        self.updated_at = datetime.now(timezone.utc)

    def fail_check(self, reason: str, recommendations: List[str] = None):
        """Mark check as failed with reason."""
        self.status = CheckStatus.FAILED.value
        self.completion_date = datetime.now(timezone.utc)
        self.result_summary = reason
        self.risk_level = RiskLevel.HIGH.value

        if recommendations:
            self.recommendations = recommendations

        self.updated_at = datetime.now(timezone.utc)

    def require_manual_review(self, reason: str):
        """Mark check as requiring manual review."""
        self.status = CheckStatus.MANUAL_REVIEW_REQUIRED.value
        self.result_summary = reason
        self.updated_at = datetime.now(timezone.utc)

    def add_finding(self, finding_type: str, description: str,
                   severity: str = CheckSeverity.INFO.value):
        """Add a finding to the check results."""
        finding = {
            'type': finding_type,
            'description': description,
            'severity': severity,
            'timestamp': datetime.now(timezone.utc)
        }
        self.findings.append(finding)
        self.updated_at = datetime.now(timezone.utc)

    def add_recommendation(self, recommendation: str):
        """Add a recommendation based on check results."""
        if recommendation not in self.recommendations:
            self.recommendations.append(recommendation)
            self.updated_at = datetime.now(timezone.utc)

    def is_expired(self) -> bool:
        """Check if verification results have expired."""
        if self.expiration_date:
            return datetime.now(timezone.utc) > self.expiration_date
        return False

    def get_risk_score(self) -> int:
        """Get numerical risk score based on risk level."""
        risk_scores = {
            RiskLevel.LOW.value: 1,
            RiskLevel.MEDIUM.value: 2,
            RiskLevel.HIGH.value: 3,
            RiskLevel.CRITICAL.value: 4,
            RiskLevel.UNKNOWN.value: 0
        }
        return risk_scores.get(self.risk_level, 0)

    def _get_default_title(self, check_type: str) -> str:
        """Get default title for check type."""
        titles = {
            VerificationCheckType.LEGAL_STATUS.value: "Legal Status Verification",
            VerificationCheckType.TAX_EXEMPT_STATUS.value: "Tax Exempt Status Check",
            VerificationCheckType.FINANCIAL_HEALTH.value: "Financial Health Assessment",
            VerificationCheckType.BACKGROUND_CHECK.value: "Leadership Background Check",
            VerificationCheckType.REFERENCE_CHECK.value: "Reference Verification",
            VerificationCheckType.INSURANCE_VERIFICATION.value: "Insurance Coverage Verification",
            VerificationCheckType.OPERATIONAL_ASSESSMENT.value: "Operational Assessment",
            VerificationCheckType.IMPACT_VALIDATION.value: "Impact Validation",
            VerificationCheckType.COMPLIANCE_CHECK.value: "Compliance Verification",
            VerificationCheckType.FRAUD_SCREENING.value: "Fraud Screening"
        }
        return titles.get(check_type, "Verification Check")

    def __repr__(self):
        return f'<VerificationCheck {self.check_type}: {self.status} ({self.risk_level})>'