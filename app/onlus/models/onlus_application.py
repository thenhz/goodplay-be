from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from bson import ObjectId
from enum import Enum


class ApplicationStatus(Enum):
    """Status of ONLUS application."""
    DRAFT = "draft"  # Application being prepared
    SUBMITTED = "submitted"  # Application submitted for review
    UNDER_REVIEW = "under_review"  # Currently being reviewed
    DOCUMENTATION_PENDING = "documentation_pending"  # Waiting for documents
    DUE_DILIGENCE = "due_diligence"  # In due diligence phase
    APPROVED = "approved"  # Application approved
    REJECTED = "rejected"  # Application rejected
    WITHDRAWN = "withdrawn"  # Application withdrawn by applicant
    EXPIRED = "expired"  # Application expired due to inactivity


class ApplicationPhase(Enum):
    """Current phase of application review."""
    INITIAL = "initial"  # Initial application submission
    DOCUMENTATION = "documentation"  # Document review phase
    DUE_DILIGENCE = "due_diligence"  # Due diligence investigation
    FINAL_APPROVAL = "final_approval"  # Final approval decision


class Priority(Enum):
    """Application review priority."""
    LOW = "low"  # Standard processing
    NORMAL = "normal"  # Normal priority
    HIGH = "high"  # High priority (special circumstances)
    URGENT = "urgent"  # Urgent processing required


class ONLUSApplication:
    """
    Model for ONLUS registration applications.

    Manages the complete application lifecycle from initial submission
    through verification to final approval or rejection.

    Collection: onlus_applications
    """

    # Application expiration period (90 days)
    EXPIRATION_DAYS = 90

    def __init__(self, applicant_id: str, organization_name: str,
                 mission_statement: str, category: str,
                 contact_email: str, contact_phone: str,
                 website_url: str = None, address: Dict[str, str] = None,
                 legal_entity_type: str = None, tax_id: str = None,
                 incorporation_date: Optional[datetime] = None,
                 description: str = None, operational_scope: str = None,
                 target_beneficiaries: str = None,
                 primary_activities: List[str] = None,
                 leadership_team: List[Dict[str, str]] = None,
                 board_members: List[Dict[str, str]] = None,
                 annual_budget: float = None, funding_sources: List[str] = None,
                 bank_account_info: Dict[str, str] = None,
                 status: str = ApplicationStatus.DRAFT.value,
                 phase: str = ApplicationPhase.INITIAL.value,
                 priority: str = Priority.NORMAL.value,
                 submission_date: Optional[datetime] = None,
                 review_deadline: Optional[datetime] = None,
                 assigned_reviewer: str = None, reviewer_notes: str = None,
                 rejection_reason: str = None,
                 approval_conditions: List[str] = None,
                 metadata: Dict[str, Any] = None,
                 progress_percentage: int = 0,
                 required_documents: List[str] = None,
                 submitted_documents: List[str] = None,
                 verification_checks: List[str] = None,
                 compliance_score: float = None,
                 risk_assessment: str = None,
                 _id: Optional[ObjectId] = None,
                 created_at: Optional[datetime] = None,
                 updated_at: Optional[datetime] = None):
        """
        Initialize ONLUSApplication.

        Args:
            applicant_id: ID of user submitting application
            organization_name: Name of the organization
            mission_statement: Organization's mission statement
            category: ONLUS category (healthcare, education, etc.)
            contact_email: Primary contact email
            contact_phone: Primary contact phone
            website_url: Organization website URL
            address: Organization address details
            legal_entity_type: Type of legal entity
            tax_id: Tax identification number
            incorporation_date: When organization was incorporated
            description: Detailed organization description
            operational_scope: Geographic/demographic scope
            target_beneficiaries: Description of target beneficiaries
            primary_activities: List of primary activities
            leadership_team: Leadership team information
            board_members: Board member information
            annual_budget: Annual budget amount
            funding_sources: Sources of funding
            bank_account_info: Bank account details
            status: Current application status
            phase: Current review phase
            priority: Application priority level
            submission_date: When application was submitted
            review_deadline: Deadline for review completion
            assigned_reviewer: Admin assigned to review
            reviewer_notes: Notes from reviewer
            rejection_reason: Reason for rejection (if applicable)
            approval_conditions: Conditions for approval
            metadata: Additional application metadata
            progress_percentage: Application completion percentage
            required_documents: List of required document types
            submitted_documents: List of submitted document IDs
            verification_checks: List of verification check IDs
            compliance_score: Overall compliance score
            risk_assessment: Risk assessment result
            _id: MongoDB document ID
            created_at: Creation timestamp
            updated_at: Last update timestamp
        """
        self._id = _id or ObjectId()
        self.applicant_id = applicant_id
        self.organization_name = organization_name
        self.mission_statement = mission_statement
        self.category = category
        self.contact_email = contact_email.lower()
        self.contact_phone = contact_phone
        self.website_url = website_url
        self.address = address or {}
        self.legal_entity_type = legal_entity_type
        self.tax_id = tax_id
        self.incorporation_date = incorporation_date
        self.description = description
        self.operational_scope = operational_scope
        self.target_beneficiaries = target_beneficiaries
        self.primary_activities = primary_activities or []
        self.leadership_team = leadership_team or []
        self.board_members = board_members or []
        self.annual_budget = annual_budget
        self.funding_sources = funding_sources or []
        self.bank_account_info = bank_account_info or {}
        self.status = status
        self.phase = phase
        self.priority = priority
        self.submission_date = submission_date
        self.review_deadline = review_deadline
        self.assigned_reviewer = assigned_reviewer
        self.reviewer_notes = reviewer_notes
        self.rejection_reason = rejection_reason
        self.approval_conditions = approval_conditions or []
        self.metadata = metadata or {}
        self.progress_percentage = progress_percentage
        self.required_documents = required_documents or []
        self.submitted_documents = submitted_documents or []
        self.verification_checks = verification_checks or []
        self.compliance_score = compliance_score
        self.risk_assessment = risk_assessment
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or datetime.now(timezone.utc)

    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        app_dict = {
            '_id': self._id,
            'applicant_id': self.applicant_id,
            'organization_name': self.organization_name,
            'mission_statement': self.mission_statement,
            'category': self.category,
            'contact_email': self.contact_email,
            'contact_phone': self.contact_phone,
            'website_url': self.website_url,
            'address': self.address,
            'legal_entity_type': self.legal_entity_type,
            'incorporation_date': self.incorporation_date,
            'description': self.description,
            'operational_scope': self.operational_scope,
            'target_beneficiaries': self.target_beneficiaries,
            'primary_activities': self.primary_activities,
            'annual_budget': self.annual_budget,
            'funding_sources': self.funding_sources,
            'status': self.status,
            'phase': self.phase,
            'priority': self.priority,
            'submission_date': self.submission_date,
            'review_deadline': self.review_deadline,
            'assigned_reviewer': self.assigned_reviewer,
            'reviewer_notes': self.reviewer_notes,
            'rejection_reason': self.rejection_reason,
            'approval_conditions': self.approval_conditions,
            'metadata': self.metadata,
            'progress_percentage': self.progress_percentage,
            'required_documents': self.required_documents,
            'submitted_documents': self.submitted_documents,
            'verification_checks': self.verification_checks,
            'compliance_score': self.compliance_score,
            'risk_assessment': self.risk_assessment,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

        # Include sensitive information only for authorized users
        if include_sensitive:
            app_dict.update({
                'tax_id': self.tax_id,
                'leadership_team': self.leadership_team,
                'board_members': self.board_members,
                'bank_account_info': self.bank_account_info
            })

        return app_dict

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Create instance from dictionary."""
        if not data:
            return None

        return cls(
            _id=data.get('_id'),
            applicant_id=data.get('applicant_id'),
            organization_name=data.get('organization_name'),
            mission_statement=data.get('mission_statement'),
            category=data.get('category'),
            contact_email=data.get('contact_email'),
            contact_phone=data.get('contact_phone'),
            website_url=data.get('website_url'),
            address=data.get('address', {}),
            legal_entity_type=data.get('legal_entity_type'),
            tax_id=data.get('tax_id'),
            incorporation_date=data.get('incorporation_date'),
            description=data.get('description'),
            operational_scope=data.get('operational_scope'),
            target_beneficiaries=data.get('target_beneficiaries'),
            primary_activities=data.get('primary_activities', []),
            leadership_team=data.get('leadership_team', []),
            board_members=data.get('board_members', []),
            annual_budget=data.get('annual_budget'),
            funding_sources=data.get('funding_sources', []),
            bank_account_info=data.get('bank_account_info', {}),
            status=data.get('status', ApplicationStatus.DRAFT.value),
            phase=data.get('phase', ApplicationPhase.INITIAL.value),
            priority=data.get('priority', Priority.NORMAL.value),
            submission_date=data.get('submission_date'),
            review_deadline=data.get('review_deadline'),
            assigned_reviewer=data.get('assigned_reviewer'),
            reviewer_notes=data.get('reviewer_notes'),
            rejection_reason=data.get('rejection_reason'),
            approval_conditions=data.get('approval_conditions', []),
            metadata=data.get('metadata', {}),
            progress_percentage=data.get('progress_percentage', 0),
            required_documents=data.get('required_documents', []),
            submitted_documents=data.get('submitted_documents', []),
            verification_checks=data.get('verification_checks', []),
            compliance_score=data.get('compliance_score'),
            risk_assessment=data.get('risk_assessment'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )

    @staticmethod
    def validate_application_data(data: Dict[str, Any]) -> Optional[str]:
        """
        Validate application data.

        Args:
            data: Application data to validate

        Returns:
            str: Error message if validation fails, None if valid
        """
        if not isinstance(data, dict):
            return "APPLICATION_DATA_INVALID"

        # Required fields
        required_fields = [
            'applicant_id', 'organization_name', 'mission_statement',
            'category', 'contact_email', 'contact_phone'
        ]

        for field in required_fields:
            if not data.get(field):
                return f"{field.upper()}_REQUIRED"

        # Validate email format
        email = data.get('contact_email', '')
        if '@' not in email or '.' not in email:
            return "CONTACT_EMAIL_INVALID"

        # Validate category
        from app.onlus.models.onlus_category import ONLUSCategory
        if data['category'] not in [cat.value for cat in ONLUSCategory]:
            return "ONLUS_CATEGORY_INVALID"

        # Validate status and phase
        status = data.get('status', ApplicationStatus.DRAFT.value)
        if status not in [s.value for s in ApplicationStatus]:
            return "APPLICATION_STATUS_INVALID"

        phase = data.get('phase', ApplicationPhase.INITIAL.value)
        if phase not in [p.value for p in ApplicationPhase]:
            return "APPLICATION_PHASE_INVALID"

        # Validate priority
        priority = data.get('priority', Priority.NORMAL.value)
        if priority not in [p.value for p in Priority]:
            return "APPLICATION_PRIORITY_INVALID"

        # Validate budget
        budget = data.get('annual_budget')
        if budget is not None and (not isinstance(budget, (int, float)) or budget < 0):
            return "ANNUAL_BUDGET_INVALID"

        # Validate progress percentage
        progress = data.get('progress_percentage', 0)
        if not isinstance(progress, int) or progress < 0 or progress > 100:
            return "PROGRESS_PERCENTAGE_INVALID"

        return None

    def submit_application(self):
        """Submit the application for review."""
        if self.status == ApplicationStatus.DRAFT.value:
            self.status = ApplicationStatus.SUBMITTED.value
            self.submission_date = datetime.now(timezone.utc)
            self.review_deadline = datetime.now(timezone.utc) + timedelta(days=14)
            self.updated_at = datetime.now(timezone.utc)
            return True
        return False

    def start_review(self, reviewer_id: str):
        """Start the review process."""
        if self.status == ApplicationStatus.SUBMITTED.value:
            self.status = ApplicationStatus.UNDER_REVIEW.value
            self.phase = ApplicationPhase.DOCUMENTATION.value
            self.assigned_reviewer = reviewer_id
            self.updated_at = datetime.now(timezone.utc)
            return True
        return False

    def approve_application(self, reviewer_id: str, conditions: List[str] = None):
        """Approve the application."""
        self.status = ApplicationStatus.APPROVED.value
        self.assigned_reviewer = reviewer_id
        self.approval_conditions = conditions or []
        self.progress_percentage = 100
        self.updated_at = datetime.now(timezone.utc)

    def reject_application(self, reviewer_id: str, reason: str):
        """Reject the application with reason."""
        self.status = ApplicationStatus.REJECTED.value
        self.assigned_reviewer = reviewer_id
        self.rejection_reason = reason
        self.updated_at = datetime.now(timezone.utc)

    def withdraw_application(self):
        """Withdraw the application."""
        if self.status not in [ApplicationStatus.APPROVED.value, ApplicationStatus.REJECTED.value]:
            self.status = ApplicationStatus.WITHDRAWN.value
            self.updated_at = datetime.now(timezone.utc)
            return True
        return False

    def advance_phase(self, new_phase: str):
        """Advance to next review phase."""
        if new_phase in [p.value for p in ApplicationPhase]:
            self.phase = new_phase
            self.updated_at = datetime.now(timezone.utc)
            return True
        return False

    def update_progress(self, percentage: int):
        """Update application progress percentage."""
        if 0 <= percentage <= 100:
            self.progress_percentage = percentage
            self.updated_at = datetime.now(timezone.utc)
            return True
        return False

    def add_document(self, document_id: str):
        """Add a submitted document to the application."""
        if document_id not in self.submitted_documents:
            self.submitted_documents.append(document_id)
            self.updated_at = datetime.now(timezone.utc)

    def add_verification_check(self, check_id: str):
        """Add a verification check to the application."""
        if check_id not in self.verification_checks:
            self.verification_checks.append(check_id)
            self.updated_at = datetime.now(timezone.utc)

    def calculate_completion_percentage(self) -> int:
        """Calculate application completion percentage."""
        total_requirements = len(self.required_documents) + 5  # Base requirements
        completed_requirements = len(self.submitted_documents)

        # Add basic information completion
        if self.organization_name and self.mission_statement:
            completed_requirements += 1
        if self.contact_email and self.contact_phone:
            completed_requirements += 1
        if self.legal_entity_type and self.tax_id:
            completed_requirements += 1
        if self.description and self.operational_scope:
            completed_requirements += 1
        if self.leadership_team and self.board_members:
            completed_requirements += 1

        percentage = min(100, int((completed_requirements / total_requirements) * 100))
        self.progress_percentage = percentage
        return percentage

    def is_expired(self) -> bool:
        """Check if application has expired."""
        if self.submission_date:
            expiry_date = self.submission_date + timedelta(days=self.EXPIRATION_DAYS)
            return datetime.now(timezone.utc) > expiry_date
        return False

    def is_overdue(self) -> bool:
        """Check if application review is overdue."""
        if self.review_deadline:
            return datetime.now(timezone.utc) > self.review_deadline
        return False

    def can_be_submitted(self) -> bool:
        """Check if application can be submitted."""
        return (self.status == ApplicationStatus.DRAFT.value and
                self.progress_percentage >= 80)

    def __repr__(self):
        return f'<ONLUSApplication {self.organization_name}: {self.status}>'