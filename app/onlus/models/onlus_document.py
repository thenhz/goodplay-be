from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from bson import ObjectId
from enum import Enum


class DocumentType(Enum):
    """Types of documents required for ONLUS verification."""
    LEGAL_CERTIFICATE = "legal_certificate"  # Incorporation certificate
    TAX_EXEMPT_STATUS = "tax_exempt_status"  # Tax exemption documentation
    FINANCIAL_REPORT = "financial_report"  # Annual financial statements
    INSURANCE_COVERAGE = "insurance_coverage"  # Liability insurance documentation
    REFERENCES = "references"  # Third-party references
    MISSION_STATEMENT = "mission_statement"  # Official mission statement
    BOARD_COMPOSITION = "board_composition"  # Board member documentation
    OPERATIONAL_PLAN = "operational_plan"  # Operational and strategic plans
    IMPACT_EVIDENCE = "impact_evidence"  # Evidence of impact and outcomes
    COMPLIANCE_CERTIFICATE = "compliance_certificate"  # Regulatory compliance docs
    OTHER = "other"  # Other supporting documents


class DocumentStatus(Enum):
    """Status of document verification."""
    PENDING = "pending"  # Document uploaded, pending review
    UNDER_REVIEW = "under_review"  # Currently being reviewed
    APPROVED = "approved"  # Document approved
    REJECTED = "rejected"  # Document rejected
    EXPIRED = "expired"  # Document has expired
    RESUBMISSION_REQUIRED = "resubmission_required"  # Needs resubmission


class DocumentFormat(Enum):
    """Supported document formats."""
    PDF = "pdf"
    DOC = "doc"
    DOCX = "docx"
    JPG = "jpg"
    JPEG = "jpeg"
    PNG = "png"
    ZIP = "zip"


class ONLUSDocument:
    """
    Model for ONLUS verification documents.

    Manages document upload, verification, and lifecycle tracking
    for ONLUS application process.

    Collection: onlus_documents
    """

    # Maximum file size in bytes (10MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024

    def __init__(self, application_id: str, document_type: str, filename: str,
                 file_url: str, file_size: int, file_format: str,
                 title: str = None, description: str = None,
                 status: str = DocumentStatus.PENDING.value,
                 upload_date: Optional[datetime] = None,
                 review_date: Optional[datetime] = None,
                 expiration_date: Optional[datetime] = None,
                 reviewed_by: str = None, reviewer_notes: str = None,
                 rejection_reason: str = None,
                 metadata: Dict[str, Any] = None,
                 is_required: bool = True, is_confidential: bool = False,
                 version: int = 1, previous_version_id: str = None,
                 _id: Optional[ObjectId] = None,
                 created_at: Optional[datetime] = None,
                 updated_at: Optional[datetime] = None):
        """
        Initialize ONLUSDocument.

        Args:
            application_id: Associated application ID
            document_type: Type of document (DocumentType enum)
            filename: Original filename
            file_url: Storage URL for the document
            file_size: File size in bytes
            file_format: Document format (DocumentFormat enum)
            title: Document title/name
            description: Document description
            status: Verification status
            upload_date: When document was uploaded
            review_date: When document was reviewed
            expiration_date: When document expires (if applicable)
            reviewed_by: Admin user who reviewed the document
            reviewer_notes: Notes from reviewer
            rejection_reason: Reason for rejection (if applicable)
            metadata: Additional document metadata
            is_required: Whether this document is required for approval
            is_confidential: Whether document contains sensitive information
            version: Document version number
            previous_version_id: ID of previous version (if resubmitted)
            _id: MongoDB document ID
            created_at: Creation timestamp
            updated_at: Last update timestamp
        """
        self._id = _id or ObjectId()
        self.application_id = application_id
        self.document_type = document_type
        self.filename = filename
        self.file_url = file_url
        self.file_size = file_size
        self.file_format = file_format.lower()
        self.title = title or filename
        self.description = description
        self.status = status
        self.upload_date = upload_date or datetime.now(timezone.utc)
        self.review_date = review_date
        self.expiration_date = expiration_date
        self.reviewed_by = reviewed_by
        self.reviewer_notes = reviewer_notes
        self.rejection_reason = rejection_reason
        self.metadata = metadata or {}
        self.is_required = is_required
        self.is_confidential = is_confidential
        self.version = version
        self.previous_version_id = previous_version_id
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or datetime.now(timezone.utc)

    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        doc_dict = {
            '_id': self._id,
            'application_id': self.application_id,
            'document_type': self.document_type,
            'filename': self.filename,
            'file_size': self.file_size,
            'file_format': self.file_format,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'upload_date': self.upload_date,
            'review_date': self.review_date,
            'expiration_date': self.expiration_date,
            'reviewed_by': self.reviewed_by,
            'reviewer_notes': self.reviewer_notes,
            'rejection_reason': self.rejection_reason,
            'metadata': self.metadata,
            'is_required': self.is_required,
            'is_confidential': self.is_confidential,
            'version': self.version,
            'previous_version_id': self.previous_version_id,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

        # Include file URL only for authorized users
        if include_sensitive:
            doc_dict['file_url'] = self.file_url

        return doc_dict

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Create instance from dictionary."""
        if not data:
            return None

        return cls(
            _id=data.get('_id'),
            application_id=data.get('application_id'),
            document_type=data.get('document_type'),
            filename=data.get('filename'),
            file_url=data.get('file_url'),
            file_size=data.get('file_size'),
            file_format=data.get('file_format'),
            title=data.get('title'),
            description=data.get('description'),
            status=data.get('status', DocumentStatus.PENDING.value),
            upload_date=data.get('upload_date'),
            review_date=data.get('review_date'),
            expiration_date=data.get('expiration_date'),
            reviewed_by=data.get('reviewed_by'),
            reviewer_notes=data.get('reviewer_notes'),
            rejection_reason=data.get('rejection_reason'),
            metadata=data.get('metadata', {}),
            is_required=data.get('is_required', True),
            is_confidential=data.get('is_confidential', False),
            version=data.get('version', 1),
            previous_version_id=data.get('previous_version_id'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )

    @staticmethod
    def validate_document_data(data: Dict[str, Any]) -> Optional[str]:
        """
        Validate document data.

        Args:
            data: Document data to validate

        Returns:
            str: Error message if validation fails, None if valid
        """
        if not isinstance(data, dict):
            return "DOCUMENT_DATA_INVALID"

        # Required fields
        if not data.get('application_id'):
            return "APPLICATION_ID_REQUIRED"
        if not data.get('document_type'):
            return "DOCUMENT_TYPE_REQUIRED"
        if not data.get('filename'):
            return "FILENAME_REQUIRED"
        if not data.get('file_url'):
            return "FILE_URL_REQUIRED"
        if not data.get('file_size'):
            return "FILE_SIZE_REQUIRED"
        if not data.get('file_format'):
            return "FILE_FORMAT_REQUIRED"

        # Validate document type
        if data['document_type'] not in [dt.value for dt in DocumentType]:
            return "DOCUMENT_TYPE_INVALID"

        # Validate file format
        file_format = data['file_format'].lower()
        if file_format not in [fmt.value for fmt in DocumentFormat]:
            return "FILE_FORMAT_UNSUPPORTED"

        # Validate file size
        file_size = data.get('file_size', 0)
        if not isinstance(file_size, int) or file_size <= 0:
            return "FILE_SIZE_INVALID"
        if file_size > ONLUSDocument.MAX_FILE_SIZE:
            return "FILE_SIZE_TOO_LARGE"

        # Validate status
        status = data.get('status', DocumentStatus.PENDING.value)
        if status not in [s.value for s in DocumentStatus]:
            return "DOCUMENT_STATUS_INVALID"

        return None

    def approve_document(self, reviewed_by: str, notes: str = None):
        """Approve the document."""
        self.status = DocumentStatus.APPROVED.value
        self.reviewed_by = reviewed_by
        self.reviewer_notes = notes
        self.review_date = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    def reject_document(self, reviewed_by: str, reason: str, notes: str = None):
        """Reject the document with reason."""
        self.status = DocumentStatus.REJECTED.value
        self.reviewed_by = reviewed_by
        self.rejection_reason = reason
        self.reviewer_notes = notes
        self.review_date = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    def request_resubmission(self, reviewed_by: str, reason: str):
        """Request document resubmission."""
        self.status = DocumentStatus.RESUBMISSION_REQUIRED.value
        self.reviewed_by = reviewed_by
        self.rejection_reason = reason
        self.review_date = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    def is_expired(self) -> bool:
        """Check if document has expired."""
        if self.expiration_date:
            return datetime.now(timezone.utc) > self.expiration_date
        return False

    def is_expiring_soon(self, days: int = 30) -> bool:
        """Check if document is expiring within specified days."""
        if self.expiration_date:
            expiry_threshold = datetime.now(timezone.utc) + timedelta(days=days)
            return self.expiration_date <= expiry_threshold
        return False

    def get_file_extension(self) -> str:
        """Get file extension from filename."""
        return self.filename.split('.')[-1].lower() if '.' in self.filename else ''

    def is_image(self) -> bool:
        """Check if document is an image file."""
        return self.file_format in [DocumentFormat.JPG.value, DocumentFormat.JPEG.value, DocumentFormat.PNG.value]

    def is_document(self) -> bool:
        """Check if document is a text document."""
        return self.file_format in [DocumentFormat.PDF.value, DocumentFormat.DOC.value, DocumentFormat.DOCX.value]

    def __repr__(self):
        return f'<ONLUSDocument {self.document_type}: {self.filename} ({self.status})>'