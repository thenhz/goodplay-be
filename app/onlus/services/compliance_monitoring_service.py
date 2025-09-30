from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timezone, timedelta
from flask import current_app

from app.onlus.repositories.compliance_score_repository import ComplianceScoreRepository
from app.onlus.repositories.onlus_organization_repository import ONLUSOrganizationRepository
from app.onlus.repositories.allocation_result_repository import AllocationResultRepository
from app.onlus.repositories.verification_check_repository import VerificationCheckRepository
from app.donations.repositories.transaction_repository import TransactionRepository

from app.onlus.models.compliance_score import ComplianceScore, ComplianceLevel, ComplianceCategory, RiskLevel
from app.onlus.models.onlus_organization import OrganizationStatus, ComplianceStatus


class ComplianceMonitoringService:
    """
    Comprehensive compliance monitoring service for ONLUS organizations.

    Provides continuous monitoring, health scoring, risk assessment,
    and automated compliance checks with real-time alerts.
    """

    def __init__(self):
        self.compliance_repo = ComplianceScoreRepository()
        self.onlus_repo = ONLUSOrganizationRepository()
        self.allocation_repo = AllocationResultRepository()
        self.verification_repo = VerificationCheckRepository()
        self.transaction_repo = TransactionRepository()

    def conduct_comprehensive_assessment(self, onlus_id: str,
                                       assessment_period_months: int = 12) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Conduct comprehensive compliance assessment for an ONLUS."""
        try:
            # Get ONLUS data
            success, _, onlus = self.onlus_repo.get_organization_by_id(onlus_id)
            if not success or not onlus:
                return False, "ONLUS_NOT_FOUND", None

            # Define assessment period
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=assessment_period_months * 30)

            # Create new compliance score
            compliance_score = ComplianceScore(
                onlus_id=onlus_id,
                assessment_period_start=start_date,
                assessment_period_end=end_date,
                is_current=True
            )

            # Calculate category scores
            category_scores = {}

            # 1. Financial Transparency (25% weight)
            category_scores[ComplianceCategory.FINANCIAL_TRANSPARENCY.value] = \
                self._assess_financial_transparency(onlus_id, start_date, end_date)

            # 2. Operational Efficiency (20% weight)
            category_scores[ComplianceCategory.OPERATIONAL_EFFICIENCY.value] = \
                self._assess_operational_efficiency(onlus_id, start_date, end_date)

            # 3. Governance (20% weight)
            category_scores[ComplianceCategory.GOVERNANCE.value] = \
                self._assess_governance(onlus_id, onlus)

            # 4. Impact Reporting (15% weight)
            category_scores[ComplianceCategory.IMPACT_REPORTING.value] = \
                self._assess_impact_reporting(onlus_id, start_date, end_date)

            # 5. Regulatory Compliance (15% weight)
            category_scores[ComplianceCategory.REGULATORY_COMPLIANCE.value] = \
                self._assess_regulatory_compliance(onlus_id, onlus)

            # 6. Donor Trust (5% weight)
            category_scores[ComplianceCategory.DONOR_TRUST.value] = \
                self._assess_donor_trust(onlus_id, start_date, end_date)

            # Set category scores
            compliance_score.category_scores = category_scores

            # Calculate overall score
            compliance_score.calculate_overall_score()

            # Set individual scores for detailed tracking
            compliance_score.financial_health_score = category_scores[ComplianceCategory.FINANCIAL_TRANSPARENCY.value]
            compliance_score.transparency_score = category_scores[ComplianceCategory.FINANCIAL_TRANSPARENCY.value]
            compliance_score.efficiency_score = category_scores[ComplianceCategory.OPERATIONAL_EFFICIENCY.value]
            compliance_score.governance_score = category_scores[ComplianceCategory.GOVERNANCE.value]
            compliance_score.impact_score = category_scores[ComplianceCategory.IMPACT_REPORTING.value]
            compliance_score.regulatory_score = category_scores[ComplianceCategory.REGULATORY_COMPLIANCE.value]

            # Conduct detailed assessments
            self._conduct_compliance_checks(compliance_score, onlus, start_date, end_date)
            self._generate_improvement_recommendations(compliance_score, category_scores)
            self._set_benchmark_comparisons(compliance_score, onlus_id)

            # Schedule next assessment
            compliance_score.schedule_next_assessment(90)  # 90 days ahead

            # Save compliance score
            success, _, score_data = self.compliance_repo.create_score(compliance_score)
            if not success:
                return False, "COMPLIANCE_SCORE_CREATION_FAILED", None

            # Update ONLUS compliance status based on score
            self._update_onlus_compliance_status(onlus, compliance_score)

            current_app.logger.info(
                f"Comprehensive compliance assessment completed for {onlus_id}: "
                f"Score {compliance_score.overall_score:.2f}, Level {compliance_score.compliance_level}"
            )

            return True, "COMPLIANCE_ASSESSMENT_SUCCESS", compliance_score.to_dict()

        except Exception as e:
            current_app.logger.error(f"Compliance assessment failed: {str(e)}")
            return False, "COMPLIANCE_ASSESSMENT_FAILED", None

    def _assess_financial_transparency(self, onlus_id: str, start_date: datetime, end_date: datetime) -> float:
        """Assess financial transparency score (0-100)."""
        try:
            score = 70.0  # Base score

            # Get allocation results for analysis
            success, _, allocations = self.allocation_repo.get_results_by_onlus(onlus_id, limit=50)
            if success and allocations:
                # Check allocation success rate
                successful = [a for a in allocations if a.is_successful()]
                success_rate = len(successful) / len(allocations)

                if success_rate >= 0.95:
                    score += 15
                elif success_rate >= 0.90:
                    score += 10
                elif success_rate >= 0.80:
                    score += 5
                elif success_rate < 0.70:
                    score -= 10

                # Check average efficiency ratio
                efficiency_ratios = [a.calculate_efficiency_ratio() for a in successful]
                if efficiency_ratios:
                    avg_efficiency = sum(efficiency_ratios) / len(efficiency_ratios)
                    if avg_efficiency >= 0.95:
                        score += 10
                    elif avg_efficiency >= 0.90:
                        score += 5
                    elif avg_efficiency < 0.80:
                        score -= 5

            # Check for financial documentation completeness
            success, _, onlus = self.onlus_repo.get_organization_by_id(onlus_id)
            if success and onlus:
                if onlus.tax_id:
                    score += 5
                if onlus.incorporation_date:
                    score += 2

            return max(0.0, min(100.0, score))

        except Exception:
            return 70.0  # Default score

    def _assess_operational_efficiency(self, onlus_id: str, start_date: datetime, end_date: datetime) -> float:
        """Assess operational efficiency score (0-100)."""
        try:
            score = 75.0  # Base score

            # Get allocation performance metrics
            success, _, metrics = self.allocation_repo.get_allocation_performance_metrics(start_date, end_date)
            if success and metrics:
                # Check processing time efficiency
                avg_processing_time = metrics.get('avg_processing_time', 0)
                if avg_processing_time > 0:
                    if avg_processing_time <= 60:  # 1 minute or less
                        score += 15
                    elif avg_processing_time <= 300:  # 5 minutes or less
                        score += 10
                    elif avg_processing_time <= 600:  # 10 minutes or less
                        score += 5
                    elif avg_processing_time > 1800:  # More than 30 minutes
                        score -= 10

                # Check success rate
                success_rate = metrics.get('success_rate', 0)
                if success_rate >= 95:
                    score += 10
                elif success_rate >= 90:
                    score += 5
                elif success_rate < 80:
                    score -= 10

            return max(0.0, min(100.0, score))

        except Exception:
            return 75.0

    def _assess_governance(self, onlus_id: str, onlus) -> float:
        """Assess governance score (0-100)."""
        try:
            score = 80.0  # Base score

            # Check verification level
            if onlus.verification_level == "gold":
                score += 15
            elif onlus.verification_level == "premium":
                score += 10
            elif onlus.verification_level == "standard":
                score += 5

            # Check organization status
            if onlus.status == OrganizationStatus.ACTIVE.value:
                score += 5
            elif onlus.status == OrganizationStatus.SUSPENDED.value:
                score -= 20

            # Check legal compliance
            if onlus.legal_entity_type:
                score += 5
            if onlus.tax_id:
                score += 5

            # Check verification completeness
            success, _, checks = self.verification_repo.get_checks_by_onlus(onlus_id, limit=10)
            if success and checks:
                passed_checks = [c for c in checks if c.status == "passed"]
                if len(passed_checks) >= 5:
                    score += 10
                elif len(passed_checks) >= 3:
                    score += 5

            return max(0.0, min(100.0, score))

        except Exception:
            return 80.0

    def _assess_impact_reporting(self, onlus_id: str, start_date: datetime, end_date: datetime) -> float:
        """Assess impact reporting score (0-100)."""
        try:
            score = 65.0  # Base score

            # Get recent allocations to assess impact reporting
            success, _, allocations = self.allocation_repo.get_results_by_onlus(onlus_id, limit=20)
            if success and allocations:
                # Check for impact metrics in allocation results
                allocations_with_impact = [a for a in allocations if a.impact_metrics]
                impact_reporting_rate = len(allocations_with_impact) / len(allocations)

                if impact_reporting_rate >= 0.9:
                    score += 20
                elif impact_reporting_rate >= 0.7:
                    score += 15
                elif impact_reporting_rate >= 0.5:
                    score += 10
                elif impact_reporting_rate < 0.3:
                    score -= 10

                # Check quality of impact data
                detailed_impact_count = 0
                for allocation in allocations_with_impact:
                    if len(allocation.impact_metrics) >= 3:  # Multiple metrics
                        detailed_impact_count += 1

                if detailed_impact_count > len(allocations_with_impact) * 0.5:
                    score += 10

            return max(0.0, min(100.0, score))

        except Exception:
            return 65.0

    def _assess_regulatory_compliance(self, onlus_id: str, onlus) -> float:
        """Assess regulatory compliance score (0-100)."""
        try:
            score = 85.0  # Base score

            # Check legal status and documentation
            if not onlus.tax_id:
                score -= 15
            if not onlus.legal_entity_type:
                score -= 10
            if not onlus.incorporation_date:
                score -= 5

            # Check verification status
            if onlus.compliance_status == ComplianceStatus.COMPLIANT.value:
                score += 10
            elif onlus.compliance_status == ComplianceStatus.NON_COMPLIANT.value:
                score -= 30
            elif onlus.compliance_status == ComplianceStatus.MAJOR_ISSUES.value:
                score -= 20
            elif onlus.compliance_status == ComplianceStatus.MINOR_ISSUES.value:
                score -= 5

            # Check recent verification checks
            success, _, recent_checks = self.verification_repo.get_recent_checks_by_onlus(onlus_id, 30)
            if success and recent_checks:
                failed_checks = [c for c in recent_checks if c.status == "failed"]
                if len(failed_checks) > 0:
                    score -= len(failed_checks) * 5

            return max(0.0, min(100.0, score))

        except Exception:
            return 85.0

    def _assess_donor_trust(self, onlus_id: str, start_date: datetime, end_date: datetime) -> float:
        """Assess donor trust score (0-100)."""
        try:
            score = 80.0  # Base score

            # Get recent allocations
            success, _, allocations = self.allocation_repo.get_results_by_onlus(onlus_id, limit=30)
            if success and allocations:
                # Check donor retention (unique donors across multiple allocations)
                all_donors = []
                for allocation in allocations:
                    all_donors.extend(allocation.donor_ids)

                unique_donors = set(all_donors)
                if len(unique_donors) > 0:
                    repeat_donation_rate = (len(all_donors) - len(unique_donors)) / len(all_donors)
                    if repeat_donation_rate >= 0.3:
                        score += 15
                    elif repeat_donation_rate >= 0.2:
                        score += 10
                    elif repeat_donation_rate >= 0.1:
                        score += 5

                # Check allocation completion rate
                completed_allocations = [a for a in allocations if a.status == "completed"]
                completion_rate = len(completed_allocations) / len(allocations)
                if completion_rate >= 0.95:
                    score += 5
                elif completion_rate < 0.8:
                    score -= 10

            return max(0.0, min(100.0, score))

        except Exception:
            return 80.0

    def _conduct_compliance_checks(self, compliance_score: ComplianceScore, onlus, start_date: datetime, end_date: datetime):
        """Conduct detailed compliance checks and add issues."""
        try:
            # Check for expired verification
            if onlus.verification_date:
                days_since_verification = (datetime.now(timezone.utc) - onlus.verification_date).days
                if days_since_verification > 365:  # More than 1 year
                    compliance_score.add_compliance_issue(
                        "expired_verification",
                        "Organization verification is more than 1 year old",
                        "warning",
                        ComplianceCategory.REGULATORY_COMPLIANCE.value
                    )

            # Check for low allocation success rate
            success, _, allocations = self.allocation_repo.get_results_by_onlus(onlus.onlus_id, limit=20)
            if success and allocations:
                successful = [a for a in allocations if a.is_successful()]
                success_rate = len(successful) / len(allocations)

                if success_rate < 0.8:
                    compliance_score.add_compliance_issue(
                        "low_allocation_success",
                        f"Low allocation success rate: {success_rate:.2f}",
                        "critical" if success_rate < 0.6 else "high",
                        ComplianceCategory.OPERATIONAL_EFFICIENCY.value
                    )

            # Check for missing documentation
            if not onlus.tax_id:
                compliance_score.add_compliance_issue(
                    "missing_tax_id",
                    "Missing tax identification number",
                    "high",
                    ComplianceCategory.REGULATORY_COMPLIANCE.value
                )

            if not onlus.legal_entity_type:
                compliance_score.add_compliance_issue(
                    "missing_legal_entity",
                    "Missing legal entity type information",
                    "medium",
                    ComplianceCategory.GOVERNANCE.value
                )

            # Check compliance status
            if onlus.compliance_status in [ComplianceStatus.NON_COMPLIANT.value, ComplianceStatus.MAJOR_ISSUES.value]:
                compliance_score.add_compliance_issue(
                    "compliance_status_issue",
                    f"Current compliance status: {onlus.compliance_status}",
                    "critical",
                    ComplianceCategory.REGULATORY_COMPLIANCE.value
                )

        except Exception as e:
            current_app.logger.error(f"Compliance checks failed: {str(e)}")

    def _generate_improvement_recommendations(self, compliance_score: ComplianceScore, category_scores: Dict[str, float]):
        """Generate improvement recommendations based on scores."""
        try:
            # Identify low-scoring categories
            for category, score in category_scores.items():
                if score < 70:
                    if category == ComplianceCategory.FINANCIAL_TRANSPARENCY.value:
                        compliance_score.add_improvement_recommendation(
                            category,
                            "Improve financial reporting and allocation efficiency tracking",
                            "high",
                            5.0
                        )
                    elif category == ComplianceCategory.OPERATIONAL_EFFICIENCY.value:
                        compliance_score.add_improvement_recommendation(
                            category,
                            "Optimize allocation processing times and success rates",
                            "high",
                            8.0
                        )
                    elif category == ComplianceCategory.GOVERNANCE.value:
                        compliance_score.add_improvement_recommendation(
                            category,
                            "Complete missing legal documentation and verification requirements",
                            "critical",
                            10.0
                        )
                    elif category == ComplianceCategory.IMPACT_REPORTING.value:
                        compliance_score.add_improvement_recommendation(
                            category,
                            "Enhance impact measurement and reporting capabilities",
                            "medium",
                            7.0
                        )
                    elif category == ComplianceCategory.REGULATORY_COMPLIANCE.value:
                        compliance_score.add_improvement_recommendation(
                            category,
                            "Address regulatory compliance issues and update documentation",
                            "critical",
                            15.0
                        )

            # General recommendations based on overall score
            if compliance_score.overall_score < 60:
                compliance_score.add_improvement_recommendation(
                    "overall",
                    "Comprehensive compliance review and improvement plan required",
                    "critical",
                    20.0
                )

        except Exception as e:
            current_app.logger.error(f"Improvement recommendations generation failed: {str(e)}")

    def _set_benchmark_comparisons(self, compliance_score: ComplianceScore, onlus_id: str):
        """Set benchmark comparisons with peer organizations."""
        try:
            # Get peer averages (would typically query database for similar organizations)
            # For now, using mock data
            benchmarks = {
                'overall_score': {
                    'peer_average': 75.0,
                    'percentile': 65 if compliance_score.overall_score > 75 else 35
                },
                'financial_transparency': {
                    'peer_average': 78.0,
                    'percentile': 70 if compliance_score.financial_health_score > 78 else 30
                },
                'operational_efficiency': {
                    'peer_average': 72.0,
                    'percentile': 60 if compliance_score.efficiency_score > 72 else 40
                }
            }

            for metric, data in benchmarks.items():
                org_value = compliance_score.overall_score if metric == 'overall_score' else \
                           getattr(compliance_score, f"{metric.split('_')[0]}_score", 0)

                compliance_score.set_benchmark_comparison(
                    metric,
                    org_value,
                    data['peer_average'],
                    data['percentile']
                )

        except Exception as e:
            current_app.logger.error(f"Benchmark comparison failed: {str(e)}")

    def _update_onlus_compliance_status(self, onlus, compliance_score: ComplianceScore):
        """Update ONLUS compliance status based on assessment."""
        try:
            old_status = onlus.compliance_status

            if compliance_score.overall_score >= 90:
                onlus.compliance_status = ComplianceStatus.COMPLIANT.value
            elif compliance_score.overall_score >= 70:
                onlus.compliance_status = ComplianceStatus.MINOR_ISSUES.value
            elif compliance_score.overall_score >= 50:
                onlus.compliance_status = ComplianceStatus.MAJOR_ISSUES.value
            else:
                onlus.compliance_status = ComplianceStatus.NON_COMPLIANT.value

            if old_status != onlus.compliance_status:
                self.onlus_repo.update_organization(onlus)
                current_app.logger.info(
                    f"ONLUS {onlus.onlus_id} compliance status updated: "
                    f"{old_status} -> {onlus.compliance_status}"
                )

        except Exception as e:
            current_app.logger.error(f"ONLUS compliance status update failed: {str(e)}")

    def monitor_real_time_compliance(self, max_alerts: int = 100) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Perform real-time compliance monitoring and generate alerts."""
        try:
            alerts_generated = 0
            monitoring_results = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'alerts': [],
                'summary': {}
            }

            # Get organizations that need immediate attention
            success, _, high_risk_scores = self.compliance_repo.get_high_risk_scores(current_only=True)
            if success and high_risk_scores:
                for score in high_risk_scores:
                    if alerts_generated >= max_alerts:
                        break

                    # Generate alert for high-risk organizations
                    alert = {
                        'alert_id': f"compliance_{score.onlus_id}_{int(datetime.now().timestamp())}",
                        'onlus_id': score.onlus_id,
                        'alert_type': 'high_risk_compliance',
                        'severity': 'high' if score.risk_level == RiskLevel.HIGH.value else 'critical',
                        'message': f"Organization requires immediate compliance attention (Score: {score.overall_score:.1f})",
                        'compliance_score': score.overall_score,
                        'risk_level': score.risk_level,
                        'open_issues': score.get_open_issues_count(),
                        'critical_issues': score.get_critical_issues_count()
                    }

                    monitoring_results['alerts'].append(alert)

                    # Add alert to compliance score
                    score.add_monitoring_alert(
                        'high_risk_compliance',
                        alert['message'],
                        alert['severity']
                    )
                    self.compliance_repo.update_score(score)

                    alerts_generated += 1

            # Check for overdue assessments
            success, _, overdue_scores = self.compliance_repo.get_scores_needing_assessment(days_overdue=7)
            if success and overdue_scores:
                for score in overdue_scores[:10]:  # Limit to 10
                    if alerts_generated >= max_alerts:
                        break

                    alert = {
                        'alert_id': f"assessment_overdue_{score.onlus_id}_{int(datetime.now().timestamp())}",
                        'onlus_id': score.onlus_id,
                        'alert_type': 'assessment_overdue',
                        'severity': 'medium',
                        'message': 'Compliance assessment is overdue',
                        'days_overdue': score.days_until_next_assessment() or 0,
                        'last_assessment': score.assessment_date.isoformat()
                    }

                    monitoring_results['alerts'].append(alert)
                    alerts_generated += 1

            # Generate summary
            monitoring_results['summary'] = {
                'total_alerts': alerts_generated,
                'high_risk_organizations': len([a for a in monitoring_results['alerts'] if a['alert_type'] == 'high_risk_compliance']),
                'overdue_assessments': len([a for a in monitoring_results['alerts'] if a['alert_type'] == 'assessment_overdue']),
                'critical_alerts': len([a for a in monitoring_results['alerts'] if a['severity'] == 'critical'])
            }

            current_app.logger.info(f"Real-time compliance monitoring completed: {alerts_generated} alerts generated")

            return True, "COMPLIANCE_MONITORING_SUCCESS", monitoring_results

        except Exception as e:
            current_app.logger.error(f"Real-time compliance monitoring failed: {str(e)}")
            return False, "COMPLIANCE_MONITORING_FAILED", None

    def get_compliance_dashboard_data(self, include_trends: bool = True) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Get comprehensive compliance dashboard data."""
        try:
            # Get current compliance statistics
            success, _, stats = self.compliance_repo.get_compliance_statistics(current_only=True)
            if not success:
                stats = {}

            dashboard_data = {
                'generated_at': datetime.now(timezone.utc).isoformat(),
                'statistics': stats,
                'risk_distribution': {
                    'low_risk': stats.get('low_risk_count', 0),
                    'moderate_risk': stats.get('moderate_risk_count', 0),
                    'high_risk': stats.get('high_risk_count', 0),
                    'critical_risk': stats.get('critical_risk_count', 0)
                },
                'compliance_levels': {
                    'excellent': stats.get('excellent_count', 0),
                    'good': stats.get('good_count', 0),
                    'satisfactory': stats.get('satisfactory_count', 0),
                    'needs_attention': stats.get('needs_attention_count', 0),
                    'critical': stats.get('critical_count', 0)
                }
            }

            # Add trends if requested
            if include_trends:
                success, _, trends = self.compliance_repo.get_compliance_trends(months=6)
                if success:
                    dashboard_data['trends'] = trends

            # Get critical issues summary
            success, _, critical_scores = self.compliance_repo.get_scores_with_critical_issues()
            if success and critical_scores:
                dashboard_data['critical_issues'] = [
                    {
                        'onlus_id': score.onlus_id,
                        'overall_score': score.overall_score,
                        'critical_issues_count': score.get_critical_issues_count(),
                        'risk_level': score.risk_level
                    }
                    for score in critical_scores[:10]  # Top 10
                ]

            return True, "COMPLIANCE_DASHBOARD_SUCCESS", dashboard_data

        except Exception as e:
            current_app.logger.error(f"Compliance dashboard data failed: {str(e)}")
            return False, "COMPLIANCE_DASHBOARD_FAILED", None

    def generate_compliance_alerts_report(self, days: int = 30) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Generate report of compliance alerts over specified period."""
        try:
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=days)

            # Get scores with alerts in the period
            success, _, scores = self.compliance_repo.get_compliance_statistics(
                start_date=start_date, end_date=end_date
            )

            if not success:
                return False, "COMPLIANCE_STATS_FAILED", None

            # Generate alerts summary report
            report_data = {
                'report_period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'days': days
                },
                'statistics': scores,
                'generated_at': datetime.now(timezone.utc).isoformat()
            }

            return True, "COMPLIANCE_ALERTS_REPORT_SUCCESS", report_data

        except Exception as e:
            current_app.logger.error(f"Compliance alerts report failed: {str(e)}")
            return False, "COMPLIANCE_ALERTS_REPORT_FAILED", None