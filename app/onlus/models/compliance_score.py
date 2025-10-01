from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from bson import ObjectId
from enum import Enum


class ComplianceLevel(Enum):
    """Compliance level categories."""
    EXCELLENT = "excellent"  # 90-100 score
    GOOD = "good"  # 80-89 score
    SATISFACTORY = "satisfactory"  # 70-79 score
    NEEDS_ATTENTION = "needs_attention"  # 60-69 score
    CRITICAL = "critical"  # Below 60 score


class RiskLevel(Enum):
    """Risk assessment levels."""
    LOW = "low"  # Low risk profile
    MODERATE = "moderate"  # Moderate risk
    HIGH = "high"  # High risk
    CRITICAL = "critical"  # Critical risk requiring immediate action


class ComplianceCategory(Enum):
    """Categories for compliance assessment."""
    FINANCIAL_TRANSPARENCY = "financial_transparency"
    OPERATIONAL_EFFICIENCY = "operational_efficiency"
    GOVERNANCE = "governance"
    IMPACT_REPORTING = "impact_reporting"
    REGULATORY_COMPLIANCE = "regulatory_compliance"
    DONOR_TRUST = "donor_trust"


class ComplianceScore:
    """
    Model for ONLUS compliance scoring and monitoring.

    Tracks compliance metrics, health scoring, and risk assessment
    for ONLUS organizations with continuous monitoring.

    Collection: compliance_scores
    """

    def __init__(self, onlus_id: str, assessment_period_start: datetime,
                 assessment_period_end: datetime,
                 overall_score: float = 0.0,
                 category_scores: Dict[str, float] = None,
                 compliance_level: str = "needs_attention",
                 risk_level: str = "moderate",
                 financial_health_score: float = 0.0,
                 transparency_score: float = 0.0,
                 efficiency_score: float = 0.0,
                 governance_score: float = 0.0,
                 impact_score: float = 0.0,
                 regulatory_score: float = 0.0,
                 performance_indicators: Dict[str, Any] = None,
                 benchmark_comparisons: Dict[str, Any] = None,
                 compliance_issues: List[Dict[str, Any]] = None,
                 improvement_recommendations: List[Dict[str, Any]] = None,
                 monitoring_alerts: List[Dict[str, Any]] = None,
                 trend_analysis: Dict[str, Any] = None,
                 peer_ranking: Dict[str, Any] = None,
                 assessment_methodology: Dict[str, Any] = None,
                 assessor_id: str = None, assessment_date: Optional[datetime] = None,
                 next_assessment_due: Optional[datetime] = None,
                 is_current: bool = True, is_verified: bool = False,
                 verification_details: Dict[str, Any] = None,
                 _id: Optional[ObjectId] = None,
                 created_at: Optional[datetime] = None,
                 updated_at: Optional[datetime] = None,
                 metadata: Dict[str, Any] = None):
        self._id = _id
        self.onlus_id = onlus_id
        self.assessment_period_start = assessment_period_start
        self.assessment_period_end = assessment_period_end
        self.overall_score = float(overall_score)
        self.category_scores = category_scores or {}
        self.compliance_level = compliance_level
        self.risk_level = risk_level
        self.financial_health_score = float(financial_health_score)
        self.transparency_score = float(transparency_score)
        self.efficiency_score = float(efficiency_score)
        self.governance_score = float(governance_score)
        self.impact_score = float(impact_score)
        self.regulatory_score = float(regulatory_score)
        self.performance_indicators = performance_indicators or {}
        self.benchmark_comparisons = benchmark_comparisons or {}
        self.compliance_issues = compliance_issues or []
        self.improvement_recommendations = improvement_recommendations or []
        self.monitoring_alerts = monitoring_alerts or []
        self.trend_analysis = trend_analysis or {}
        self.peer_ranking = peer_ranking or {}
        self.assessment_methodology = assessment_methodology or {}
        self.assessor_id = assessor_id
        self.assessment_date = assessment_date or datetime.now(timezone.utc)
        self.next_assessment_due = next_assessment_due
        self.is_current = is_current
        self.is_verified = is_verified
        self.verification_details = verification_details or {}
        self.metadata = metadata or {}
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or datetime.now(timezone.utc)

    def calculate_overall_score(self) -> None:
        """Calculate overall compliance score from category scores."""
        if not self.category_scores:
            self.overall_score = 0.0
            return

        # Standard weighting for compliance categories
        weights = {
            ComplianceCategory.FINANCIAL_TRANSPARENCY.value: 0.25,
            ComplianceCategory.OPERATIONAL_EFFICIENCY.value: 0.20,
            ComplianceCategory.GOVERNANCE.value: 0.20,
            ComplianceCategory.IMPACT_REPORTING.value: 0.15,
            ComplianceCategory.REGULATORY_COMPLIANCE.value: 0.15,
            ComplianceCategory.DONOR_TRUST.value: 0.05
        }

        weighted_sum = 0.0
        total_weight = 0.0

        for category, score in self.category_scores.items():
            weight = weights.get(category, 0.0)
            weighted_sum += score * weight
            total_weight += weight

        if total_weight > 0:
            self.overall_score = weighted_sum / total_weight
        else:
            self.overall_score = 0.0

        # Update compliance level based on score
        self.update_compliance_level()
        self.updated_at = datetime.now(timezone.utc)

    def update_compliance_level(self) -> None:
        """Update compliance level based on overall score."""
        if self.overall_score >= 90:
            self.compliance_level = ComplianceLevel.EXCELLENT.value
        elif self.overall_score >= 80:
            self.compliance_level = ComplianceLevel.GOOD.value
        elif self.overall_score >= 70:
            self.compliance_level = ComplianceLevel.SATISFACTORY.value
        elif self.overall_score >= 60:
            self.compliance_level = ComplianceLevel.NEEDS_ATTENTION.value
        else:
            self.compliance_level = ComplianceLevel.CRITICAL.value

    def update_risk_level(self) -> None:
        """Update risk level based on compliance issues and scores."""
        critical_issues = sum(1 for issue in self.compliance_issues
                            if issue.get('severity') == 'critical')
        high_issues = sum(1 for issue in self.compliance_issues
                         if issue.get('severity') == 'high')

        # Risk calculation based on score and issues
        if self.overall_score < 60 or critical_issues > 0:
            self.risk_level = RiskLevel.CRITICAL.value
        elif self.overall_score < 70 or high_issues > 2:
            self.risk_level = RiskLevel.HIGH.value
        elif self.overall_score < 80 or high_issues > 0:
            self.risk_level = RiskLevel.MODERATE.value
        else:
            self.risk_level = RiskLevel.LOW.value

    def add_compliance_issue(self, issue_type: str, description: str,
                            severity: str = "medium", category: str = None) -> None:
        """Add a compliance issue."""
        issue = {
            'issue_id': str(ObjectId()),
            'issue_type': issue_type,
            'description': description,
            'severity': severity,
            'category': category,
            'identified_at': datetime.now(timezone.utc),
            'status': 'open'
        }
        self.compliance_issues.append(issue)
        self.update_risk_level()
        self.updated_at = datetime.now(timezone.utc)

    def resolve_compliance_issue(self, issue_id: str, resolution_notes: str = None) -> bool:
        """Resolve a compliance issue."""
        for issue in self.compliance_issues:
            if issue.get('issue_id') == issue_id:
                issue['status'] = 'resolved'
                issue['resolved_at'] = datetime.now(timezone.utc)
                if resolution_notes:
                    issue['resolution_notes'] = resolution_notes
                self.update_risk_level()
                self.updated_at = datetime.now(timezone.utc)
                return True
        return False

    def add_improvement_recommendation(self, category: str, recommendation: str,
                                     priority: str = "medium",
                                     expected_impact: float = 0.0) -> None:
        """Add an improvement recommendation."""
        recommendation_entry = {
            'recommendation_id': str(ObjectId()),
            'category': category,
            'recommendation': recommendation,
            'priority': priority,
            'expected_impact': float(expected_impact),
            'suggested_at': datetime.now(timezone.utc),
            'status': 'pending'
        }
        self.improvement_recommendations.append(recommendation_entry)
        self.updated_at = datetime.now(timezone.utc)

    def add_monitoring_alert(self, alert_type: str, message: str,
                           urgency: str = "medium") -> None:
        """Add a monitoring alert."""
        alert = {
            'alert_id': str(ObjectId()),
            'alert_type': alert_type,
            'message': message,
            'urgency': urgency,
            'triggered_at': datetime.now(timezone.utc),
            'status': 'active'
        }
        self.monitoring_alerts.append(alert)
        self.updated_at = datetime.now(timezone.utc)

    def dismiss_monitoring_alert(self, alert_id: str) -> bool:
        """Dismiss a monitoring alert."""
        for alert in self.monitoring_alerts:
            if alert.get('alert_id') == alert_id:
                alert['status'] = 'dismissed'
                alert['dismissed_at'] = datetime.now(timezone.utc)
                self.updated_at = datetime.now(timezone.utc)
                return True
        return False

    def set_benchmark_comparison(self, metric: str, organization_value: float,
                               peer_average: float, percentile: int) -> None:
        """Set benchmark comparison data."""
        self.benchmark_comparisons[metric] = {
            'organization_value': float(organization_value),
            'peer_average': float(peer_average),
            'percentile': int(percentile),
            'performance': 'above_average' if organization_value > peer_average else 'below_average',
            'updated_at': datetime.now(timezone.utc)
        }
        self.updated_at = datetime.now(timezone.utc)

    def verify_assessment(self, verifier_id: str, verification_notes: str = None) -> None:
        """Verify the compliance assessment."""
        self.is_verified = True
        self.verification_details = {
            'verifier_id': verifier_id,
            'verified_at': datetime.now(timezone.utc),
            'verification_notes': verification_notes
        }
        self.updated_at = datetime.now(timezone.utc)

    def schedule_next_assessment(self, days_ahead: int = 90) -> None:
        """Schedule next compliance assessment."""
        self.next_assessment_due = datetime.now(timezone.utc) + timedelta(days=days_ahead)
        self.updated_at = datetime.now(timezone.utc)

    def is_assessment_overdue(self) -> bool:
        """Check if next assessment is overdue."""
        if not self.next_assessment_due:
            return False
        return datetime.now(timezone.utc) > self.next_assessment_due

    def get_open_issues_count(self) -> int:
        """Get count of open compliance issues."""
        return sum(1 for issue in self.compliance_issues
                  if issue.get('status') == 'open')

    def get_critical_issues_count(self) -> int:
        """Get count of critical issues."""
        return sum(1 for issue in self.compliance_issues
                  if issue.get('severity') == 'critical' and issue.get('status') == 'open')

    def get_active_alerts_count(self) -> int:
        """Get count of active monitoring alerts."""
        return sum(1 for alert in self.monitoring_alerts
                  if alert.get('status') == 'active')

    def days_until_next_assessment(self) -> Optional[int]:
        """Get days until next assessment is due."""
        if not self.next_assessment_due:
            return None
        delta = self.next_assessment_due - datetime.now(timezone.utc)
        return max(0, delta.days)

    def to_dict(self) -> Dict[str, Any]:
        """Convert compliance score to dictionary."""
        return {
            '_id': self._id,
            'onlus_id': self.onlus_id,
            'assessment_period_start': self.assessment_period_start,
            'assessment_period_end': self.assessment_period_end,
            'overall_score': self.overall_score,
            'category_scores': self.category_scores,
            'compliance_level': self.compliance_level,
            'risk_level': self.risk_level,
            'financial_health_score': self.financial_health_score,
            'transparency_score': self.transparency_score,
            'efficiency_score': self.efficiency_score,
            'governance_score': self.governance_score,
            'impact_score': self.impact_score,
            'regulatory_score': self.regulatory_score,
            'performance_indicators': self.performance_indicators,
            'benchmark_comparisons': self.benchmark_comparisons,
            'compliance_issues': self.compliance_issues,
            'improvement_recommendations': self.improvement_recommendations,
            'monitoring_alerts': self.monitoring_alerts,
            'trend_analysis': self.trend_analysis,
            'peer_ranking': self.peer_ranking,
            'assessment_methodology': self.assessment_methodology,
            'assessor_id': self.assessor_id,
            'assessment_date': self.assessment_date,
            'next_assessment_due': self.next_assessment_due,
            'is_current': self.is_current,
            'is_verified': self.is_verified,
            'verification_details': self.verification_details,
            'metadata': self.metadata,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'open_issues_count': self.get_open_issues_count(),
            'critical_issues_count': self.get_critical_issues_count(),
            'active_alerts_count': self.get_active_alerts_count(),
            'is_assessment_overdue': self.is_assessment_overdue(),
            'days_until_next_assessment': self.days_until_next_assessment()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ComplianceScore':
        """Create compliance score from dictionary."""
        return cls(**data)

    def __str__(self) -> str:
        return f"ComplianceScore({self.onlus_id}, {self.overall_score:.1f}, {self.compliance_level})"

    def __repr__(self) -> str:
        return self.__str__()