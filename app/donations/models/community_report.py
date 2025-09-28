from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from bson import ObjectId
from enum import Enum


class ReportType(Enum):
    """Types of community reports."""
    DAILY = "daily"  # Daily impact summary
    WEEKLY = "weekly"  # Weekly impact summary
    MONTHLY = "monthly"  # Monthly comprehensive report
    QUARTERLY = "quarterly"  # Quarterly impact review
    ANNUAL = "annual"  # Annual impact report
    SPECIAL_EVENT = "special_event"  # Special event/campaign report
    REAL_TIME = "real_time"  # Real-time snapshot


class ReportStatus(Enum):
    """Status of community reports."""
    GENERATING = "generating"  # Report being generated
    COMPLETED = "completed"  # Report completed successfully
    ERROR = "error"  # Error during generation
    PUBLISHED = "published"  # Report published and visible
    ARCHIVED = "archived"  # Report archived


class CommunityReport:
    """
    Model for community-wide impact reports and statistics.

    Aggregates platform-wide donation and impact data for transparency
    and community engagement.

    Collection: community_reports
    """

    def __init__(self, report_type: str, period_start: datetime, period_end: datetime,
                 total_donations_amount: float = 0.0, total_donations_count: int = 0,
                 unique_donors_count: int = 0, onlus_supported_count: int = 0,
                 impact_metrics: Dict[str, Any] = None, donation_breakdown: Dict[str, Any] = None,
                 geographic_distribution: Dict[str, Any] = None, top_contributors: List[Dict] = None,
                 onlus_rankings: List[Dict] = None, fee_transparency: Dict[str, Any] = None,
                 milestones_reached: List[Dict] = None, user_engagement_stats: Dict[str, Any] = None,
                 growth_metrics: Dict[str, Any] = None, comparative_data: Dict[str, Any] = None,
                 status: str = "completed", generation_metadata: Dict[str, Any] = None,
                 highlights: List[str] = None, _id: Optional[ObjectId] = None,
                 created_at: Optional[datetime] = None, updated_at: Optional[datetime] = None):
        """
        Initialize CommunityReport.

        Args:
            report_type: Type of report (daily, weekly, monthly, etc.)
            period_start: Start date of the reporting period
            period_end: End date of the reporting period
            total_donations_amount: Total amount donated in period
            total_donations_count: Total number of donations in period
            unique_donors_count: Number of unique donors in period
            onlus_supported_count: Number of ONLUS organizations supported
            impact_metrics: Aggregated impact metrics
            donation_breakdown: Breakdown by category, amount, etc.
            geographic_distribution: Geographic spread of donations
            top_contributors: Top contributors (anonymized if needed)
            onlus_rankings: ONLUS organizations by donations received
            fee_transparency: Platform fee breakdown and allocation
            milestones_reached: Major milestones achieved in period
            user_engagement_stats: User engagement and activity stats
            growth_metrics: Growth compared to previous periods
            comparative_data: Comparison with historical data
            status: Current status of the report
            generation_metadata: Metadata about report generation
            highlights: Key highlights from the period
            _id: MongoDB document ID
            created_at: Creation timestamp
            updated_at: Last update timestamp
        """
        self._id = _id or ObjectId()
        self.report_type = report_type
        self.period_start = period_start
        self.period_end = period_end
        self.total_donations_amount = float(total_donations_amount)
        self.total_donations_count = total_donations_count
        self.unique_donors_count = unique_donors_count
        self.onlus_supported_count = onlus_supported_count
        self.status = status
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or datetime.now(timezone.utc)

        # Detailed statistics
        self.impact_metrics = impact_metrics or {
            'total_beneficiaries': 0,
            'projects_funded': 0,
            'environmental_impact': {},
            'social_impact': {},
            'educational_impact': {},
            'healthcare_impact': {}
        }

        self.donation_breakdown = donation_breakdown or {
            'by_category': {},
            'by_amount_range': {},
            'by_frequency': {},
            'by_source': {}
        }

        self.geographic_distribution = geographic_distribution or {
            'by_country': {},
            'by_region': {},
            'international_reach': 0
        }

        self.top_contributors = top_contributors or []
        self.onlus_rankings = onlus_rankings or []

        self.fee_transparency = fee_transparency or {
            'platform_fee_percentage': 5.0,
            'total_fees_collected': 0.0,
            'fees_to_onlus': 0.0,
            'operational_costs': 0.0,
            'transparency_score': 100.0
        }

        self.milestones_reached = milestones_reached or []

        self.user_engagement_stats = user_engagement_stats or {
            'active_donors': 0,
            'new_users': 0,
            'returning_donors': 0,
            'stories_unlocked': 0,
            'average_session_time': 0.0,
            'platform_retention_rate': 0.0
        }

        self.growth_metrics = growth_metrics or {
            'donation_growth_percentage': 0.0,
            'user_growth_percentage': 0.0,
            'onlus_growth_percentage': 0.0,
            'engagement_growth_percentage': 0.0
        }

        self.comparative_data = comparative_data or {
            'previous_period': {},
            'year_over_year': {},
            'all_time_comparison': {}
        }

        self.generation_metadata = generation_metadata or {
            'generation_time_seconds': 0.0,
            'data_sources': [],
            'calculation_methods': {},
            'data_quality_score': 100.0
        }

        self.highlights = highlights or []

        # Validation
        self._validate()

    def _validate(self):
        """Validate report data."""
        if self.report_type not in [t.value for t in ReportType]:
            raise ValueError(f"Invalid report type: {self.report_type}")

        if self.status not in [s.value for s in ReportStatus]:
            raise ValueError(f"Invalid status: {self.status}")

        if self.period_start >= self.period_end:
            raise ValueError("Period start must be before period end")

        if self.total_donations_amount < 0:
            raise ValueError("Total donations amount cannot be negative")

        if self.total_donations_count < 0:
            raise ValueError("Total donations count cannot be negative")

        if self.unique_donors_count < 0:
            raise ValueError("Unique donors count cannot be negative")

        if self.onlus_supported_count < 0:
            raise ValueError("ONLUS supported count cannot be negative")

    def get_period_duration_days(self) -> int:
        """Get duration of report period in days."""
        return (self.period_end - self.period_start).days + 1

    def get_average_donation_amount(self) -> float:
        """Calculate average donation amount."""
        if self.total_donations_count == 0:
            return 0.0
        return round(self.total_donations_amount / self.total_donations_count, 2)

    def get_donations_per_day(self) -> float:
        """Calculate average donations per day."""
        days = self.get_period_duration_days()
        if days == 0:
            return 0.0
        return round(self.total_donations_count / days, 2)

    def get_amount_per_day(self) -> float:
        """Calculate average donation amount per day."""
        days = self.get_period_duration_days()
        if days == 0:
            return 0.0
        return round(self.total_donations_amount / days, 2)

    def get_donor_engagement_rate(self) -> float:
        """Calculate donor engagement rate."""
        if self.unique_donors_count == 0:
            return 0.0
        return round((self.total_donations_count / self.unique_donors_count), 2)

    def get_platform_fee_amount(self) -> float:
        """Calculate total platform fees."""
        fee_percentage = self.fee_transparency.get('platform_fee_percentage', 5.0)
        return round(self.total_donations_amount * (fee_percentage / 100), 2)

    def get_net_impact_amount(self) -> float:
        """Calculate net amount going to ONLUS (after fees)."""
        return round(self.total_donations_amount - self.get_platform_fee_amount(), 2)

    def add_milestone(self, milestone_data: Dict[str, Any]) -> None:
        """Add a milestone to the report."""
        milestone = {
            'title': milestone_data.get('title'),
            'description': milestone_data.get('description'),
            'value': milestone_data.get('value'),
            'onlus_id': milestone_data.get('onlus_id'),
            'achieved_at': milestone_data.get('achieved_at', datetime.now(timezone.utc)),
            'impact_type': milestone_data.get('impact_type')
        }
        self.milestones_reached.append(milestone)
        self.updated_at = datetime.now(timezone.utc)

    def add_highlight(self, highlight: str) -> None:
        """Add a key highlight to the report."""
        if highlight and highlight not in self.highlights:
            self.highlights.append(highlight)
            self.updated_at = datetime.now(timezone.utc)

    def calculate_growth_metrics(self, previous_period_data: Dict[str, Any]) -> None:
        """Calculate growth metrics compared to previous period."""
        if not previous_period_data:
            return

        # Donation growth
        prev_amount = previous_period_data.get('total_donations_amount', 0)
        if prev_amount > 0:
            donation_growth = ((self.total_donations_amount - prev_amount) / prev_amount) * 100
            self.growth_metrics['donation_growth_percentage'] = round(donation_growth, 2)

        # User growth
        prev_users = previous_period_data.get('unique_donors_count', 0)
        if prev_users > 0:
            user_growth = ((self.unique_donors_count - prev_users) / prev_users) * 100
            self.growth_metrics['user_growth_percentage'] = round(user_growth, 2)

        # ONLUS growth
        prev_onlus = previous_period_data.get('onlus_supported_count', 0)
        if prev_onlus > 0:
            onlus_growth = ((self.onlus_supported_count - prev_onlus) / prev_onlus) * 100
            self.growth_metrics['onlus_growth_percentage'] = round(onlus_growth, 2)

        self.updated_at = datetime.now(timezone.utc)

    def generate_summary_statistics(self) -> Dict[str, Any]:
        """Generate summary statistics for quick overview."""
        return {
            'period': {
                'type': self.report_type,
                'start': self.period_start.isoformat(),
                'end': self.period_end.isoformat(),
                'duration_days': self.get_period_duration_days()
            },
            'donations': {
                'total_amount': self.total_donations_amount,
                'total_count': self.total_donations_count,
                'average_amount': self.get_average_donation_amount(),
                'per_day_count': self.get_donations_per_day(),
                'per_day_amount': self.get_amount_per_day()
            },
            'community': {
                'unique_donors': self.unique_donors_count,
                'onlus_supported': self.onlus_supported_count,
                'engagement_rate': self.get_donor_engagement_rate(),
                'new_users': self.user_engagement_stats.get('new_users', 0)
            },
            'impact': {
                'total_beneficiaries': self.impact_metrics.get('total_beneficiaries', 0),
                'projects_funded': self.impact_metrics.get('projects_funded', 0),
                'net_impact_amount': self.get_net_impact_amount()
            },
            'transparency': {
                'platform_fee_amount': self.get_platform_fee_amount(),
                'fee_percentage': self.fee_transparency.get('platform_fee_percentage', 5.0),
                'transparency_score': self.fee_transparency.get('transparency_score', 100.0)
            },
            'growth': self.growth_metrics,
            'milestones_count': len(self.milestones_reached),
            'highlights_count': len(self.highlights)
        }

    def is_current_period(self) -> bool:
        """Check if this report covers the current period."""
        now = datetime.now(timezone.utc)
        return self.period_start <= now <= self.period_end

    def is_completed(self) -> bool:
        """Check if report generation is completed."""
        return self.status == ReportStatus.COMPLETED.value

    def mark_as_published(self) -> None:
        """Mark report as published."""
        self.status = ReportStatus.PUBLISHED.value
        self.updated_at = datetime.now(timezone.utc)

    def mark_as_error(self, error_message: str = None) -> None:
        """Mark report as having an error."""
        self.status = ReportStatus.ERROR.value
        self.updated_at = datetime.now(timezone.utc)

        if error_message:
            self.generation_metadata['error_message'] = error_message

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary for MongoDB storage."""
        return {
            '_id': self._id,
            'report_type': self.report_type,
            'period_start': self.period_start,
            'period_end': self.period_end,
            'total_donations_amount': self.total_donations_amount,
            'total_donations_count': self.total_donations_count,
            'unique_donors_count': self.unique_donors_count,
            'onlus_supported_count': self.onlus_supported_count,
            'impact_metrics': self.impact_metrics,
            'donation_breakdown': self.donation_breakdown,
            'geographic_distribution': self.geographic_distribution,
            'top_contributors': self.top_contributors,
            'onlus_rankings': self.onlus_rankings,
            'fee_transparency': self.fee_transparency,
            'milestones_reached': self.milestones_reached,
            'user_engagement_stats': self.user_engagement_stats,
            'growth_metrics': self.growth_metrics,
            'comparative_data': self.comparative_data,
            'status': self.status,
            'generation_metadata': self.generation_metadata,
            'highlights': self.highlights,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

    def to_response_dict(self, include_detailed_breakdown: bool = False) -> Dict[str, Any]:
        """Convert report to dictionary for API responses."""
        response = {
            'id': str(self._id),
            'report_type': self.report_type,
            'period': {
                'start': self.period_start.isoformat(),
                'end': self.period_end.isoformat(),
                'duration_days': self.get_period_duration_days()
            },
            'status': self.status,
            'is_current': self.is_current_period(),
            'summary': self.generate_summary_statistics(),
            'impact_metrics': self.impact_metrics,
            'fee_transparency': self.fee_transparency,
            'growth_metrics': self.growth_metrics,
            'highlights': self.highlights,
            'milestones_reached': self.milestones_reached,
            'user_engagement_stats': self.user_engagement_stats,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

        # Include detailed breakdowns if requested
        if include_detailed_breakdown:
            response.update({
                'donation_breakdown': self.donation_breakdown,
                'geographic_distribution': self.geographic_distribution,
                'top_contributors': self.top_contributors,
                'onlus_rankings': self.onlus_rankings,
                'comparative_data': self.comparative_data,
                'generation_metadata': self.generation_metadata
            })

        return response

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CommunityReport':
        """Create CommunityReport instance from dictionary."""
        return cls(
            report_type=data.get('report_type'),
            period_start=data.get('period_start'),
            period_end=data.get('period_end'),
            total_donations_amount=data.get('total_donations_amount', 0.0),
            total_donations_count=data.get('total_donations_count', 0),
            unique_donors_count=data.get('unique_donors_count', 0),
            onlus_supported_count=data.get('onlus_supported_count', 0),
            impact_metrics=data.get('impact_metrics'),
            donation_breakdown=data.get('donation_breakdown'),
            geographic_distribution=data.get('geographic_distribution'),
            top_contributors=data.get('top_contributors'),
            onlus_rankings=data.get('onlus_rankings'),
            fee_transparency=data.get('fee_transparency'),
            milestones_reached=data.get('milestones_reached'),
            user_engagement_stats=data.get('user_engagement_stats'),
            growth_metrics=data.get('growth_metrics'),
            comparative_data=data.get('comparative_data'),
            status=data.get('status', 'completed'),
            generation_metadata=data.get('generation_metadata'),
            highlights=data.get('highlights'),
            _id=data.get('_id'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )

    @staticmethod
    def validate_report_data(data: Dict[str, Any]) -> Optional[str]:
        """
        Validate report data for creation/updates.

        Args:
            data: Report data to validate

        Returns:
            str: Error message if validation fails, None if valid
        """
        if not isinstance(data, dict):
            return "REPORT_DATA_INVALID_FORMAT"

        # Required fields
        required_fields = ['report_type', 'period_start', 'period_end']
        for field in required_fields:
            if field not in data or data[field] is None:
                return f"REPORT_{field.upper()}_REQUIRED"

        # Validate report type
        if data['report_type'] not in [t.value for t in ReportType]:
            return "REPORT_TYPE_INVALID"

        # Validate period dates
        try:
            period_start = data['period_start']
            period_end = data['period_end']
            if isinstance(period_start, str):
                period_start = datetime.fromisoformat(period_start.replace('Z', '+00:00'))
            if isinstance(period_end, str):
                period_end = datetime.fromisoformat(period_end.replace('Z', '+00:00'))

            if period_start >= period_end:
                return "REPORT_PERIOD_INVALID"
        except (ValueError, TypeError):
            return "REPORT_PERIOD_DATES_INVALID"

        # Validate numeric fields
        numeric_fields = ['total_donations_amount', 'total_donations_count',
                         'unique_donors_count', 'onlus_supported_count']
        for field in numeric_fields:
            if field in data and data[field] is not None:
                try:
                    value = float(data[field]) if 'amount' in field else int(data[field])
                    if value < 0:
                        return f"REPORT_{field.upper()}_NEGATIVE"
                except (ValueError, TypeError):
                    return f"REPORT_{field.upper()}_INVALID"

        return None

    @classmethod
    def create_monthly_report(cls, year: int, month: int) -> 'CommunityReport':
        """Create a monthly report template."""
        from calendar import monthrange

        period_start = datetime(year, month, 1, tzinfo=timezone.utc)
        last_day = monthrange(year, month)[1]
        period_end = datetime(year, month, last_day, 23, 59, 59, tzinfo=timezone.utc)

        return cls(
            report_type=ReportType.MONTHLY.value,
            period_start=period_start,
            period_end=period_end,
            status=ReportStatus.GENERATING.value
        )

    @classmethod
    def create_annual_report(cls, year: int) -> 'CommunityReport':
        """Create an annual report template."""
        period_start = datetime(year, 1, 1, tzinfo=timezone.utc)
        period_end = datetime(year, 12, 31, 23, 59, 59, tzinfo=timezone.utc)

        return cls(
            report_type=ReportType.ANNUAL.value,
            period_start=period_start,
            period_end=period_end,
            status=ReportStatus.GENERATING.value
        )

    @classmethod
    def create_real_time_snapshot(cls) -> 'CommunityReport':
        """Create a real-time platform snapshot."""
        now = datetime.now(timezone.utc)

        return cls(
            report_type=ReportType.REAL_TIME.value,
            period_start=now.replace(hour=0, minute=0, second=0, microsecond=0),
            period_end=now,
            status=ReportStatus.GENERATING.value
        )

    def __repr__(self) -> str:
        return f'<CommunityReport {self.report_type}: {self.period_start.date()} to {self.period_end.date()}>'