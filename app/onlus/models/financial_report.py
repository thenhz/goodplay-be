from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from bson import ObjectId
from enum import Enum


class ReportType(Enum):
    """Type of financial report."""
    MONTHLY = "monthly"  # Monthly financial report
    QUARTERLY = "quarterly"  # Quarterly financial report
    ANNUAL = "annual"  # Annual financial report
    CUSTOM = "custom"  # Custom date range report
    DONOR_STATEMENT = "donor_statement"  # Individual donor statement
    ONLUS_STATEMENT = "onlus_statement"  # ONLUS organization statement
    TAX_DOCUMENT = "tax_document"  # Tax deductibility document
    AUDIT_REPORT = "audit_report"  # Audit trail report


class ReportStatus(Enum):
    """Status of report generation."""
    PENDING = "pending"  # Report generation pending
    GENERATING = "generating"  # Report being generated
    COMPLETED = "completed"  # Report completed successfully
    FAILED = "failed"  # Report generation failed
    EXPIRED = "expired"  # Report has expired


class ReportFormat(Enum):
    """Format of generated report."""
    PDF = "pdf"  # PDF format
    CSV = "csv"  # CSV format
    JSON = "json"  # JSON format
    EXCEL = "excel"  # Excel format


class FinancialReport:
    """
    Model for financial reports and statements.

    Represents various types of financial reports including
    periodic summaries, donor statements, and audit documentation.

    Collection: financial_reports
    """

    def __init__(self, report_type: str, report_title: str,
                 start_date: datetime, end_date: datetime,
                 generated_for_id: str = None, generated_by_id: str = None,
                 report_data: Dict[str, Any] = None,
                 summary_metrics: Dict[str, float] = None,
                 detailed_transactions: List[Dict[str, Any]] = None,
                 allocation_breakdown: Dict[str, Any] = None,
                 compliance_data: Dict[str, Any] = None,
                 donor_information: Dict[str, Any] = None,
                 onlus_information: Dict[str, Any] = None,
                 tax_deductible_amount: float = 0.0,
                 report_format: str = "pdf",
                 file_url: str = None, file_size: int = None,
                 generation_parameters: Dict[str, Any] = None,
                 status: str = "pending", error_message: str = None,
                 expiry_date: Optional[datetime] = None,
                 is_confidential: bool = False,
                 access_permissions: List[str] = None,
                 _id: Optional[ObjectId] = None,
                 created_at: Optional[datetime] = None,
                 updated_at: Optional[datetime] = None,
                 generated_at: Optional[datetime] = None,
                 downloaded_at: Optional[datetime] = None,
                 metadata: Dict[str, Any] = None):
        self._id = _id
        self.report_type = report_type
        self.report_title = report_title.strip()
        self.start_date = start_date
        self.end_date = end_date
        self.generated_for_id = generated_for_id
        self.generated_by_id = generated_by_id
        self.report_data = report_data or {}
        self.summary_metrics = summary_metrics or {}
        self.detailed_transactions = detailed_transactions or []
        self.allocation_breakdown = allocation_breakdown or {}
        self.compliance_data = compliance_data or {}
        self.donor_information = donor_information or {}
        self.onlus_information = onlus_information or {}
        self.tax_deductible_amount = float(tax_deductible_amount)
        self.report_format = report_format
        self.file_url = file_url
        self.file_size = file_size
        self.generation_parameters = generation_parameters or {}
        self.status = status
        self.error_message = error_message
        self.expiry_date = expiry_date or (datetime.now(timezone.utc) + timedelta(days=90))
        self.is_confidential = is_confidential
        self.access_permissions = access_permissions or []
        self.metadata = metadata or {}
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or datetime.now(timezone.utc)
        self.generated_at = generated_at
        self.downloaded_at = downloaded_at

    def start_generation(self) -> None:
        """Mark report generation as started."""
        self.status = ReportStatus.GENERATING.value
        self.updated_at = datetime.now(timezone.utc)

    def complete_generation(self, file_url: str, file_size: int = None) -> None:
        """Mark report generation as completed."""
        self.status = ReportStatus.COMPLETED.value
        self.generated_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
        self.file_url = file_url
        self.file_size = file_size

    def fail_generation(self, error_message: str) -> None:
        """Mark report generation as failed."""
        self.status = ReportStatus.FAILED.value
        self.error_message = error_message
        self.updated_at = datetime.now(timezone.utc)

    def mark_downloaded(self, user_id: str = None) -> None:
        """Mark report as downloaded."""
        self.downloaded_at = datetime.now(timezone.utc)
        if user_id:
            if 'download_history' not in self.metadata:
                self.metadata['download_history'] = []
            self.metadata['download_history'].append({
                'user_id': user_id,
                'timestamp': datetime.now(timezone.utc)
            })
        self.updated_at = datetime.now(timezone.utc)

    def add_summary_metric(self, key: str, value: float) -> None:
        """Add a summary metric to the report."""
        self.summary_metrics[key] = float(value)
        self.updated_at = datetime.now(timezone.utc)

    def add_transaction_detail(self, transaction_data: Dict[str, Any]) -> None:
        """Add transaction detail to the report."""
        self.detailed_transactions.append({
            **transaction_data,
            'added_at': datetime.now(timezone.utc)
        })
        self.updated_at = datetime.now(timezone.utc)

    def set_allocation_breakdown(self, breakdown: Dict[str, Any]) -> None:
        """Set the allocation breakdown data."""
        self.allocation_breakdown = breakdown
        self.updated_at = datetime.now(timezone.utc)

    def is_expired(self) -> bool:
        """Check if report has expired."""
        if not self.expiry_date:
            return False
        return datetime.now(timezone.utc) > self.expiry_date

    def is_accessible_by(self, user_id: str) -> bool:
        """Check if user has access to this report."""
        if not self.is_confidential:
            return True

        if not self.access_permissions:
            return user_id == self.generated_for_id

        return user_id in self.access_permissions

    def get_period_description(self) -> str:
        """Get human-readable period description."""
        if self.report_type == ReportType.MONTHLY.value:
            return f"{self.start_date.strftime('%B %Y')}"
        elif self.report_type == ReportType.QUARTERLY.value:
            quarter = (self.start_date.month - 1) // 3 + 1
            return f"Q{quarter} {self.start_date.year}"
        elif self.report_type == ReportType.ANNUAL.value:
            return f"Year {self.start_date.year}"
        else:
            return f"{self.start_date.strftime('%Y-%m-%d')} to {self.end_date.strftime('%Y-%m-%d')}"

    def calculate_total_donations(self) -> float:
        """Calculate total donations from detailed transactions."""
        total = 0.0
        for transaction in self.detailed_transactions:
            if transaction.get('transaction_type') == 'donated':
                total += transaction.get('amount', 0.0)
        return total

    def calculate_total_allocations(self) -> float:
        """Calculate total allocations from breakdown."""
        total = 0.0
        if isinstance(self.allocation_breakdown, dict):
            for allocation in self.allocation_breakdown.values():
                if isinstance(allocation, dict) and 'amount' in allocation:
                    total += allocation['amount']
                elif isinstance(allocation, (int, float)):
                    total += allocation
        return total

    def get_efficiency_ratio(self) -> float:
        """Calculate allocation efficiency ratio."""
        total_donations = self.calculate_total_donations()
        total_allocations = self.calculate_total_allocations()

        if total_donations <= 0:
            return 0.0

        return total_allocations / total_donations

    def days_until_expiry(self) -> Optional[int]:
        """Get days until report expiry."""
        if not self.expiry_date:
            return None
        delta = self.expiry_date - datetime.now(timezone.utc)
        return max(0, delta.days)

    def to_dict(self) -> Dict[str, Any]:
        """Convert financial report to dictionary."""
        return {
            '_id': self._id,
            'report_type': self.report_type,
            'report_title': self.report_title,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'generated_for_id': self.generated_for_id,
            'generated_by_id': self.generated_by_id,
            'report_data': self.report_data,
            'summary_metrics': self.summary_metrics,
            'detailed_transactions': self.detailed_transactions,
            'allocation_breakdown': self.allocation_breakdown,
            'compliance_data': self.compliance_data,
            'donor_information': self.donor_information,
            'onlus_information': self.onlus_information,
            'tax_deductible_amount': self.tax_deductible_amount,
            'report_format': self.report_format,
            'file_url': self.file_url,
            'file_size': self.file_size,
            'generation_parameters': self.generation_parameters,
            'status': self.status,
            'error_message': self.error_message,
            'expiry_date': self.expiry_date,
            'is_confidential': self.is_confidential,
            'access_permissions': self.access_permissions,
            'metadata': self.metadata,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'generated_at': self.generated_at,
            'downloaded_at': self.downloaded_at,
            'period_description': self.get_period_description(),
            'total_donations': self.calculate_total_donations(),
            'total_allocations': self.calculate_total_allocations(),
            'efficiency_ratio': self.get_efficiency_ratio(),
            'is_expired': self.is_expired(),
            'days_until_expiry': self.days_until_expiry()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FinancialReport':
        """Create financial report from dictionary."""
        return cls(**data)

    def __str__(self) -> str:
        return f"FinancialReport({self.report_type}, {self.get_period_description()}, {self.status})"

    def __repr__(self) -> str:
        return self.__str__()