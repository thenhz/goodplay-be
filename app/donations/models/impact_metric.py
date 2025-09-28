from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from bson import ObjectId
from enum import Enum


class MetricType(Enum):
    """Types of impact metrics tracked."""
    FINANCIAL = "financial"  # Financial impact metrics
    BENEFICIARIES = "beneficiaries"  # People/animals helped
    PROJECTS = "projects"  # Projects funded or completed
    GEOGRAPHIC = "geographic"  # Geographic reach/coverage
    ENVIRONMENTAL = "environmental"  # Environmental impact
    EDUCATIONAL = "educational"  # Educational outcomes
    HEALTHCARE = "healthcare"  # Healthcare outcomes
    SOCIAL = "social"  # Social impact metrics


class MetricUnit(Enum):
    """Units for measuring impact metrics."""
    CURRENCY_EUR = "eur"  # Euro amounts
    COUNT_PEOPLE = "people"  # Number of people
    COUNT_ANIMALS = "animals"  # Number of animals
    COUNT_PROJECTS = "projects"  # Number of projects
    AREA_SQM = "square_meters"  # Area in square meters
    VOLUME_LITERS = "liters"  # Volume in liters
    WEIGHT_KG = "kilograms"  # Weight in kilograms
    TIME_HOURS = "hours"  # Time in hours
    PERCENTAGE = "percentage"  # Percentage values
    SCORE = "score"  # Numeric scores
    CUSTOM = "custom"  # Custom units


class MetricPeriod(Enum):
    """Time periods for metric aggregation."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    ALL_TIME = "all_time"


class ImpactMetric:
    """
    Model for aggregated impact metrics from ONLUS organizations.

    Tracks quantifiable impact data that can be visualized in dashboards
    and used for transparency reporting.

    Collection: impact_metrics
    """

    def __init__(self, onlus_id: str, metric_name: str, metric_type: str,
                 metric_unit: str, current_value: float, target_value: float = None,
                 period_type: str = "all_time", period_start: Optional[datetime] = None,
                 period_end: Optional[datetime] = None, source: str = "onlus_report",
                 verification_status: str = "unverified", description: str = None,
                 methodology: str = None, data_points: List[Dict] = None,
                 related_donations_count: int = 0, related_donations_amount: float = 0.0,
                 metadata: Dict[str, Any] = None, tags: List[str] = None,
                 _id: Optional[ObjectId] = None, created_at: Optional[datetime] = None,
                 updated_at: Optional[datetime] = None, last_verified: Optional[datetime] = None):
        """
        Initialize ImpactMetric.

        Args:
            onlus_id: ID of the ONLUS organization
            metric_name: Name/title of the metric
            metric_type: Type of metric (financial, beneficiaries, etc.)
            metric_unit: Unit of measurement
            current_value: Current metric value
            target_value: Target value (if applicable)
            period_type: Time period for this metric
            period_start: Start date for the period
            period_end: End date for the period
            source: Source of the metric data
            verification_status: Verification status of the data
            description: Description of what this metric measures
            methodology: How the metric is calculated/measured
            data_points: Historical data points for trending
            related_donations_count: Number of donations contributing to this metric
            related_donations_amount: Total donation amount contributing
            metadata: Additional metric metadata
            tags: Tags for categorization
            _id: MongoDB document ID
            created_at: Creation timestamp
            updated_at: Last update timestamp
            last_verified: Last verification timestamp
        """
        self._id = _id or ObjectId()
        self.onlus_id = onlus_id
        self.metric_name = metric_name
        self.metric_type = metric_type
        self.metric_unit = metric_unit
        self.current_value = float(current_value)
        self.target_value = float(target_value) if target_value is not None else None
        self.period_type = period_type
        self.period_start = period_start
        self.period_end = period_end
        self.source = source
        self.verification_status = verification_status
        self.description = description
        self.methodology = methodology
        self.related_donations_count = related_donations_count
        self.related_donations_amount = float(related_donations_amount)
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or datetime.now(timezone.utc)
        self.last_verified = last_verified

        # Data tracking
        self.data_points = data_points or []
        self.metadata = metadata or {}
        self.tags = tags or []

        # Validation
        self._validate()

    def _validate(self):
        """Validate metric data."""
        if not self.onlus_id:
            raise ValueError("ONLUS ID cannot be empty")

        if not self.metric_name or len(self.metric_name.strip()) == 0:
            raise ValueError("Metric name cannot be empty")

        if self.metric_type not in [t.value for t in MetricType]:
            raise ValueError(f"Invalid metric type: {self.metric_type}")

        if self.metric_unit not in [u.value for u in MetricUnit]:
            raise ValueError(f"Invalid metric unit: {self.metric_unit}")

        if self.period_type not in [p.value for p in MetricPeriod]:
            raise ValueError(f"Invalid period type: {self.period_type}")

        if self.current_value < 0:
            raise ValueError("Current value cannot be negative")

        if self.target_value is not None and self.target_value < 0:
            raise ValueError("Target value cannot be negative")

        if self.related_donations_count < 0:
            raise ValueError("Related donations count cannot be negative")

        if self.related_donations_amount < 0:
            raise ValueError("Related donations amount cannot be negative")

        # Validate period dates
        if self.period_start and self.period_end:
            if self.period_start > self.period_end:
                raise ValueError("Period start cannot be after period end")

    def update_value(self, new_value: float, source: str = None) -> None:
        """Update metric value and track history."""
        if new_value < 0:
            raise ValueError("Metric value cannot be negative")

        # Add current value to data points for historical tracking
        self.add_data_point(self.current_value, datetime.now(timezone.utc))

        # Update current value
        self.current_value = float(new_value)
        self.updated_at = datetime.now(timezone.utc)

        if source:
            self.source = source

    def add_data_point(self, value: float, timestamp: datetime = None) -> None:
        """Add a data point for historical tracking."""
        data_point = {
            'value': float(value),
            'timestamp': timestamp or datetime.now(timezone.utc),
            'source': self.source
        }

        self.data_points.append(data_point)

        # Keep only last 365 data points for performance
        if len(self.data_points) > 365:
            self.data_points = self.data_points[-365:]

        self.updated_at = datetime.now(timezone.utc)

    def get_progress_percentage(self) -> Optional[float]:
        """Get progress towards target as percentage."""
        if self.target_value is None or self.target_value == 0:
            return None

        progress = (self.current_value / self.target_value) * 100
        return min(100.0, round(progress, 2))

    def get_trend_data(self, days: int = 30) -> Dict[str, Any]:
        """Get trend analysis for the metric over specified days."""
        if len(self.data_points) < 2:
            return {
                'trend': 'insufficient_data',
                'change_value': 0.0,
                'change_percentage': 0.0,
                'data_points': len(self.data_points)
            }

        # Filter data points within the specified period
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        recent_points = [
            point for point in self.data_points
            if point['timestamp'] >= cutoff_date
        ]

        if len(recent_points) < 2:
            return {
                'trend': 'insufficient_data',
                'change_value': 0.0,
                'change_percentage': 0.0,
                'data_points': len(recent_points)
            }

        # Calculate trend
        oldest_value = recent_points[0]['value']
        newest_value = recent_points[-1]['value']

        change_value = newest_value - oldest_value
        change_percentage = (change_value / oldest_value * 100) if oldest_value > 0 else 0

        if change_value > 0:
            trend = 'increasing'
        elif change_value < 0:
            trend = 'decreasing'
        else:
            trend = 'stable'

        return {
            'trend': trend,
            'change_value': round(change_value, 2),
            'change_percentage': round(change_percentage, 2),
            'data_points': len(recent_points),
            'period_days': days
        }

    def is_verified(self) -> bool:
        """Check if metric is verified."""
        return self.verification_status == "verified"

    def is_stale(self, max_age_days: int = 30) -> bool:
        """Check if metric data is stale (not updated recently)."""
        if not self.updated_at:
            return True

        age = datetime.now(timezone.utc) - self.updated_at
        return age.days > max_age_days

    def mark_verified(self, verified_by: str = None) -> None:
        """Mark metric as verified."""
        self.verification_status = "verified"
        self.last_verified = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

        if verified_by:
            self.metadata['verified_by'] = verified_by

    def mark_disputed(self, reason: str = None) -> None:
        """Mark metric as disputed."""
        self.verification_status = "disputed"
        self.updated_at = datetime.now(timezone.utc)

        if reason:
            self.metadata['dispute_reason'] = reason

    def calculate_efficiency_ratio(self) -> Optional[float]:
        """Calculate impact efficiency ratio (impact per euro donated)."""
        if self.related_donations_amount <= 0:
            return None

        # Different efficiency calculations based on metric unit
        if self.metric_unit in [MetricUnit.COUNT_PEOPLE.value, MetricUnit.COUNT_ANIMALS.value]:
            # Beneficiaries per euro
            return round(self.current_value / self.related_donations_amount, 4)

        elif self.metric_unit == MetricUnit.COUNT_PROJECTS.value:
            # Projects per euro
            return round(self.current_value / self.related_donations_amount, 4)

        elif self.metric_unit == MetricUnit.CURRENCY_EUR.value:
            # Euro impact per euro donated (leverage ratio)
            return round(self.current_value / self.related_donations_amount, 2)

        else:
            # Generic impact per euro
            return round(self.current_value / self.related_donations_amount, 4)

    def add_donation_contribution(self, donation_amount: float) -> None:
        """Add a donation contribution to this metric."""
        self.related_donations_count += 1
        self.related_donations_amount += donation_amount
        self.updated_at = datetime.now(timezone.utc)

    def get_formatted_value(self) -> str:
        """Get formatted value with appropriate unit."""
        if self.metric_unit == MetricUnit.CURRENCY_EUR.value:
            return f"€{self.current_value:,.2f}"

        elif self.metric_unit == MetricUnit.PERCENTAGE.value:
            return f"{self.current_value:.1f}%"

        elif self.metric_unit in [MetricUnit.COUNT_PEOPLE.value, MetricUnit.COUNT_ANIMALS.value,
                                  MetricUnit.COUNT_PROJECTS.value]:
            return f"{int(self.current_value):,}"

        elif self.metric_unit == MetricUnit.AREA_SQM.value:
            return f"{self.current_value:,.0f} m²"

        elif self.metric_unit == MetricUnit.VOLUME_LITERS.value:
            return f"{self.current_value:,.0f} L"

        elif self.metric_unit == MetricUnit.WEIGHT_KG.value:
            return f"{self.current_value:,.1f} kg"

        elif self.metric_unit == MetricUnit.TIME_HOURS.value:
            return f"{self.current_value:,.0f} hours"

        else:
            return f"{self.current_value:,.2f}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert metric to dictionary for MongoDB storage."""
        return {
            '_id': self._id,
            'onlus_id': self.onlus_id,
            'metric_name': self.metric_name,
            'metric_type': self.metric_type,
            'metric_unit': self.metric_unit,
            'current_value': self.current_value,
            'target_value': self.target_value,
            'period_type': self.period_type,
            'period_start': self.period_start,
            'period_end': self.period_end,
            'source': self.source,
            'verification_status': self.verification_status,
            'description': self.description,
            'methodology': self.methodology,
            'data_points': self.data_points,
            'related_donations_count': self.related_donations_count,
            'related_donations_amount': self.related_donations_amount,
            'metadata': self.metadata,
            'tags': self.tags,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'last_verified': self.last_verified
        }

    def to_response_dict(self, include_history: bool = False) -> Dict[str, Any]:
        """Convert metric to dictionary for API responses."""
        response = {
            'id': str(self._id),
            'onlus_id': self.onlus_id,
            'metric_name': self.metric_name,
            'metric_type': self.metric_type,
            'metric_unit': self.metric_unit,
            'current_value': self.current_value,
            'formatted_value': self.get_formatted_value(),
            'target_value': self.target_value,
            'progress_percentage': self.get_progress_percentage(),
            'period_type': self.period_type,
            'period_start': self.period_start.isoformat() if self.period_start else None,
            'period_end': self.period_end.isoformat() if self.period_end else None,
            'source': self.source,
            'verification_status': self.verification_status,
            'is_verified': self.is_verified(),
            'description': self.description,
            'methodology': self.methodology,
            'related_donations_count': self.related_donations_count,
            'related_donations_amount': self.related_donations_amount,
            'efficiency_ratio': self.calculate_efficiency_ratio(),
            'trend_30d': self.get_trend_data(30),
            'is_stale': self.is_stale(),
            'tags': self.tags,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_verified': self.last_verified.isoformat() if self.last_verified else None
        }

        # Include historical data if requested
        if include_history:
            response['data_points'] = [
                {
                    'value': point['value'],
                    'timestamp': point['timestamp'].isoformat(),
                    'source': point.get('source', self.source)
                }
                for point in self.data_points[-30:]  # Last 30 points
            ]

        return response

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ImpactMetric':
        """Create ImpactMetric instance from dictionary."""
        return cls(
            onlus_id=data.get('onlus_id'),
            metric_name=data.get('metric_name'),
            metric_type=data.get('metric_type'),
            metric_unit=data.get('metric_unit'),
            current_value=data.get('current_value', 0.0),
            target_value=data.get('target_value'),
            period_type=data.get('period_type', 'all_time'),
            period_start=data.get('period_start'),
            period_end=data.get('period_end'),
            source=data.get('source', 'onlus_report'),
            verification_status=data.get('verification_status', 'unverified'),
            description=data.get('description'),
            methodology=data.get('methodology'),
            data_points=data.get('data_points', []),
            related_donations_count=data.get('related_donations_count', 0),
            related_donations_amount=data.get('related_donations_amount', 0.0),
            metadata=data.get('metadata', {}),
            tags=data.get('tags', []),
            _id=data.get('_id'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
            last_verified=data.get('last_verified')
        )

    @staticmethod
    def validate_metric_data(data: Dict[str, Any]) -> Optional[str]:
        """
        Validate metric data for creation/updates.

        Args:
            data: Metric data to validate

        Returns:
            str: Error message if validation fails, None if valid
        """
        if not isinstance(data, dict):
            return "METRIC_DATA_INVALID_FORMAT"

        # Required fields
        required_fields = ['onlus_id', 'metric_name', 'metric_type', 'metric_unit', 'current_value']
        for field in required_fields:
            if field not in data or data[field] is None:
                return f"METRIC_{field.upper()}_REQUIRED"

        # Validate metric type
        if data['metric_type'] not in [t.value for t in MetricType]:
            return "METRIC_TYPE_INVALID"

        # Validate metric unit
        if data['metric_unit'] not in [u.value for u in MetricUnit]:
            return "METRIC_UNIT_INVALID"

        # Validate current value
        try:
            current_value = float(data['current_value'])
            if current_value < 0:
                return "METRIC_CURRENT_VALUE_NEGATIVE"
        except (ValueError, TypeError):
            return "METRIC_CURRENT_VALUE_INVALID"

        # Validate target value
        if 'target_value' in data and data['target_value'] is not None:
            try:
                target_value = float(data['target_value'])
                if target_value < 0:
                    return "METRIC_TARGET_VALUE_NEGATIVE"
            except (ValueError, TypeError):
                return "METRIC_TARGET_VALUE_INVALID"

        # Validate period type
        if 'period_type' in data:
            if data['period_type'] not in [p.value for p in MetricPeriod]:
                return "METRIC_PERIOD_TYPE_INVALID"

        return None

    @classmethod
    def create_financial_metric(cls, onlus_id: str, current_value: float,
                               target_value: float = None, description: str = None) -> 'ImpactMetric':
        """Create a financial impact metric."""
        return cls(
            onlus_id=onlus_id,
            metric_name="Financial Impact",
            metric_type=MetricType.FINANCIAL.value,
            metric_unit=MetricUnit.CURRENCY_EUR.value,
            current_value=current_value,
            target_value=target_value,
            description=description or "Total financial impact achieved through donations"
        )

    @classmethod
    def create_beneficiary_metric(cls, onlus_id: str, beneficiary_count: int,
                                 target_count: int = None, description: str = None) -> 'ImpactMetric':
        """Create a beneficiary count metric."""
        return cls(
            onlus_id=onlus_id,
            metric_name="People Helped",
            metric_type=MetricType.BENEFICIARIES.value,
            metric_unit=MetricUnit.COUNT_PEOPLE.value,
            current_value=float(beneficiary_count),
            target_value=float(target_count) if target_count else None,
            description=description or "Number of people directly helped"
        )

    def __repr__(self) -> str:
        return f'<ImpactMetric {self.metric_name}: {self.get_formatted_value()} ({self.onlus_id})>'