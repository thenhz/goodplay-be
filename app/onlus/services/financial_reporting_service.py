from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timezone, timedelta
from flask import current_app
import json
import io
import csv
from decimal import Decimal

from app.onlus.repositories.financial_report_repository import FinancialReportRepository
from app.onlus.repositories.allocation_result_repository import AllocationResultRepository
from app.onlus.repositories.onlus_organization_repository import ONLUSOrganizationRepository
from app.donations.repositories.transaction_repository import TransactionRepository
from app.donations.repositories.wallet_repository import WalletRepository

from app.onlus.models.financial_report import FinancialReport, ReportType, ReportStatus, ReportFormat
from app.donations.models.transaction import TransactionType


class FinancialReportingService:
    """
    Financial reporting service with advanced analytics.

    Provides comprehensive financial reporting capabilities including:
    - Periodic reports (monthly, quarterly, annual)
    - On-demand analytics and dashboards
    - Donor statements and tax documentation
    - Audit reports and compliance documentation
    - Advanced analytics and trend analysis
    """

    def __init__(self):
        self.report_repo = FinancialReportRepository()
        self.allocation_repo = AllocationResultRepository()
        self.onlus_repo = ONLUSOrganizationRepository()
        self.transaction_repo = TransactionRepository()
        self.wallet_repo = WalletRepository()

    def generate_periodic_report(self, report_type: str, period_start: datetime,
                               period_end: datetime, entity_id: str = None,
                               report_format: str = "pdf") -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Generate periodic financial report (monthly, quarterly, annual)."""
        try:
            # Determine report title
            if report_type == ReportType.MONTHLY.value:
                title = f"Monthly Financial Report - {period_start.strftime('%B %Y')}"
            elif report_type == ReportType.QUARTERLY.value:
                quarter = (period_start.month - 1) // 3 + 1
                title = f"Q{quarter} {period_start.year} Financial Report"
            elif report_type == ReportType.ANNUAL.value:
                title = f"Annual Financial Report - {period_start.year}"
            else:
                title = f"Financial Report - {period_start.strftime('%Y-%m-%d')} to {period_end.strftime('%Y-%m-%d')}"

            # Create report instance
            report = FinancialReport(
                report_type=report_type,
                report_title=title,
                start_date=period_start,
                end_date=period_end,
                generated_for_id=entity_id,
                report_format=report_format,
                status=ReportStatus.PENDING.value
            )

            # Save initial report
            success, _, report_data = self.report_repo.create_report(report)
            if not success:
                return False, "REPORT_CREATION_FAILED", None

            # Generate report data
            success, message = self._generate_periodic_report_data(report, period_start, period_end)
            if not success:
                report.fail_generation(message)
                self.report_repo.update_report(report)
                return False, message, None

            # Generate file (mock file generation for now)
            file_url = f"/reports/{report._id}/financial_report.{report_format}"
            file_size = 1024 * 50  # Mock file size

            report.complete_generation(file_url, file_size)
            self.report_repo.update_report(report)

            current_app.logger.info(f"Periodic report generated successfully: {report._id}")

            return True, "PERIODIC_REPORT_GENERATED_SUCCESS", report.to_dict()

        except Exception as e:
            current_app.logger.error(f"Periodic report generation failed: {str(e)}")
            return False, "PERIODIC_REPORT_GENERATION_FAILED", None

    def _generate_periodic_report_data(self, report: FinancialReport,
                                     start_date: datetime, end_date: datetime) -> Tuple[bool, str]:
        """Generate data for periodic report."""
        try:
            # Get transaction data for the period
            success, _, transactions = self.transaction_repo.get_transactions_by_date_range(
                start_date, end_date, limit=1000
            )
            if not success:
                transactions = []

            # Get allocation data for the period
            success, _, allocations = self.allocation_repo.get_allocation_performance_metrics(
                start_date, end_date
            )
            if not success:
                allocations = {}

            # Calculate summary metrics
            total_donations = sum(t.amount for t in transactions if t.transaction_type == TransactionType.DONATED.value)
            total_earned = sum(t.amount for t in transactions if t.transaction_type == TransactionType.EARNED.value)
            transaction_count = len(transactions)

            unique_donors = len(set(t.user_id for t in transactions if t.transaction_type == TransactionType.DONATED.value))
            avg_donation = total_donations / unique_donors if unique_donors > 0 else 0

            # Set summary metrics
            summary_metrics = {
                'total_donations': float(total_donations),
                'total_earned_credits': float(total_earned),
                'transaction_count': transaction_count,
                'unique_donors': unique_donors,
                'average_donation': float(avg_donation),
                'allocation_count': allocations.get('total_allocations', 0),
                'allocation_success_rate': allocations.get('success_rate', 0),
                'total_allocated_amount': allocations.get('total_allocated_amount', 0)
            }

            report.summary_metrics = summary_metrics

            # Add detailed transactions
            for transaction in transactions[:100]:  # Limit to first 100 for report
                report.add_transaction_detail({
                    'transaction_id': transaction.transaction_id,
                    'user_id': transaction.user_id,
                    'type': transaction.transaction_type,
                    'amount': transaction.amount,
                    'date': transaction.created_at.isoformat(),
                    'onlus_id': transaction.onlus_id,
                    'status': transaction.status
                })

            # Set allocation breakdown
            if allocations:
                report.set_allocation_breakdown({
                    'total_allocations': allocations.get('total_allocations', 0),
                    'successful_allocations': allocations.get('successful_allocations', 0),
                    'failed_allocations': allocations.get('failed_allocations', 0),
                    'total_amount': allocations.get('total_allocated_amount', 0),
                    'average_amount': allocations.get('avg_allocated_amount', 0),
                    'efficiency_ratio': allocations.get('avg_efficiency_ratio', 0)
                })

            return True, "REPORT_DATA_GENERATED_SUCCESS"

        except Exception as e:
            return False, f"REPORT_DATA_GENERATION_FAILED: {str(e)}"

    def generate_donor_statement(self, donor_id: str, start_date: datetime,
                               end_date: datetime, include_tax_info: bool = True,
                               report_format: str = "pdf") -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Generate donor statement with tax deductibility information."""
        try:
            title = f"Donor Statement - {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"

            # Create donor statement report
            report = FinancialReport(
                report_type=ReportType.DONOR_STATEMENT.value,
                report_title=title,
                start_date=start_date,
                end_date=end_date,
                generated_for_id=donor_id,
                report_format=report_format,
                status=ReportStatus.PENDING.value,
                is_confidential=True,
                access_permissions=[donor_id]
            )

            # Save initial report
            success, _, report_data = self.report_repo.create_report(report)
            if not success:
                return False, "DONOR_STATEMENT_CREATION_FAILED", None

            # Get donor's transactions
            success, _, transactions = self.transaction_repo.get_transactions_by_user_and_date(
                donor_id, start_date, end_date
            )
            if not success:
                transactions = []

            # Filter donation transactions
            donations = [t for t in transactions if t.transaction_type == TransactionType.DONATED.value and t.status == "completed"]

            # Calculate tax-deductible amount
            tax_deductible_amount = sum(t.amount for t in donations if t.onlus_id)  # Only donations to verified ONLUS

            # Generate donor information
            donor_info = {
                'donor_id': donor_id,
                'statement_period': f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
                'total_donations': len(donations),
                'total_amount': float(sum(t.amount for t in donations)),
                'tax_deductible_amount': float(tax_deductible_amount),
                'currency': 'EUR'
            }

            report.donor_information = donor_info
            report.tax_deductible_amount = tax_deductible_amount

            # Add donation details
            for donation in donations:
                # Get ONLUS information
                onlus_info = {}
                if donation.onlus_id:
                    success, _, onlus = self.onlus_repo.get_organization_by_id(donation.onlus_id)
                    if success and onlus:
                        onlus_info = {
                            'name': onlus.organization_name,
                            'tax_id': onlus.tax_id,
                            'category': onlus.category
                        }

                report.add_transaction_detail({
                    'transaction_id': donation.transaction_id,
                    'date': donation.created_at.isoformat(),
                    'amount': donation.amount,
                    'onlus_info': onlus_info,
                    'is_tax_deductible': bool(donation.onlus_id),
                    'receipt_data': donation.receipt_data
                })

            # Generate summary metrics
            summary_metrics = {
                'total_donations_count': len(donations),
                'total_donated_amount': donor_info['total_amount'],
                'tax_deductible_amount': donor_info['tax_deductible_amount'],
                'average_donation': donor_info['total_amount'] / len(donations) if donations else 0,
                'unique_onlus_count': len(set(d.onlus_id for d in donations if d.onlus_id))
            }

            report.summary_metrics = summary_metrics

            # Generate file
            file_url = f"/reports/{report._id}/donor_statement.{report_format}"
            file_size = 1024 * 25  # Mock file size

            report.complete_generation(file_url, file_size)
            self.report_repo.update_report(report)

            current_app.logger.info(f"Donor statement generated successfully: {report._id} for donor {donor_id}")

            return True, "DONOR_STATEMENT_GENERATED_SUCCESS", report.to_dict()

        except Exception as e:
            current_app.logger.error(f"Donor statement generation failed: {str(e)}")
            return False, "DONOR_STATEMENT_GENERATION_FAILED", None

    def generate_onlus_financial_summary(self, onlus_id: str, months: int = 12,
                                       report_format: str = "pdf") -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Generate financial summary for ONLUS organization."""
        try:
            # Get ONLUS information
            success, _, onlus = self.onlus_repo.get_organization_by_id(onlus_id)
            if not success or not onlus:
                return False, "ONLUS_NOT_FOUND", None

            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=months * 30)

            title = f"Financial Summary - {onlus.organization_name} ({months} months)"

            # Create report
            report = FinancialReport(
                report_type=ReportType.ONLUS_STATEMENT.value,
                report_title=title,
                start_date=start_date,
                end_date=end_date,
                generated_for_id=onlus_id,
                report_format=report_format,
                status=ReportStatus.PENDING.value
            )

            # Save initial report
            success, _, report_data = self.report_repo.create_report(report)
            if not success:
                return False, "ONLUS_SUMMARY_CREATION_FAILED", None

            # Get allocation summary
            success, _, allocation_summary = self.allocation_repo.get_onlus_allocation_summary(
                onlus_id, months
            )
            if not success:
                allocation_summary = {}

            # Get transactions to this ONLUS
            success, _, transactions = self.transaction_repo.get_transactions_by_onlus_and_date(
                onlus_id, start_date, end_date
            )
            if not success:
                transactions = []

            # Set ONLUS information
            onlus_info = {
                'onlus_id': onlus_id,
                'organization_name': onlus.organization_name,
                'legal_name': onlus.legal_name,
                'category': onlus.category,
                'tax_id': onlus.tax_id,
                'status': onlus.status,
                'verification_level': onlus.verification_level
            }

            report.onlus_information = onlus_info

            # Calculate summary metrics
            total_received = allocation_summary.get('total_amount_received', 0)
            allocation_count = allocation_summary.get('total_allocations', 0)
            success_rate = allocation_summary.get('success_rate', 0)
            unique_donors = allocation_summary.get('unique_donor_count', 0)

            summary_metrics = {
                'total_amount_received': float(total_received),
                'allocation_count': allocation_count,
                'average_allocation': float(allocation_summary.get('avg_allocation_amount', 0)),
                'success_rate': float(success_rate),
                'unique_donors': unique_donors,
                'transaction_count': len(transactions),
                'period_months': months
            }

            report.summary_metrics = summary_metrics

            # Set allocation breakdown
            report.set_allocation_breakdown({
                'total_allocations': allocation_count,
                'successful_allocations': allocation_summary.get('successful_allocations', 0),
                'success_rate': success_rate,
                'total_amount': total_received,
                'average_amount': allocation_summary.get('avg_allocation_amount', 0),
                'unique_donors': unique_donors,
                'allocation_methods': allocation_summary.get('allocation_methods', [])
            })

            # Add recent transactions
            for transaction in transactions[-50:]:  # Last 50 transactions
                report.add_transaction_detail({
                    'transaction_id': transaction.transaction_id,
                    'donor_id': transaction.user_id,
                    'amount': transaction.amount,
                    'date': transaction.created_at.isoformat(),
                    'type': transaction.transaction_type,
                    'status': transaction.status
                })

            # Generate file
            file_url = f"/reports/{report._id}/onlus_summary.{report_format}"
            file_size = 1024 * 40  # Mock file size

            report.complete_generation(file_url, file_size)
            self.report_repo.update_report(report)

            current_app.logger.info(f"ONLUS financial summary generated: {report._id} for {onlus_id}")

            return True, "ONLUS_FINANCIAL_SUMMARY_SUCCESS", report.to_dict()

        except Exception as e:
            current_app.logger.error(f"ONLUS financial summary failed: {str(e)}")
            return False, "ONLUS_FINANCIAL_SUMMARY_FAILED", None

    def generate_audit_report(self, start_date: datetime, end_date: datetime,
                            audit_scope: List[str] = None,
                            report_format: str = "pdf") -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Generate comprehensive audit report."""
        try:
            title = f"Audit Report - {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"

            # Create audit report
            report = FinancialReport(
                report_type=ReportType.AUDIT_REPORT.value,
                report_title=title,
                start_date=start_date,
                end_date=end_date,
                report_format=report_format,
                status=ReportStatus.PENDING.value,
                is_confidential=True
            )

            # Save initial report
            success, _, report_data = self.report_repo.create_report(report)
            if not success:
                return False, "AUDIT_REPORT_CREATION_FAILED", None

            # Audit scope (default to all if not specified)
            if not audit_scope:
                audit_scope = ['transactions', 'allocations', 'compliance', 'funding_pools']

            audit_findings = {}

            # Transaction audit
            if 'transactions' in audit_scope:
                audit_findings['transactions'] = self._audit_transactions(start_date, end_date)

            # Allocation audit
            if 'allocations' in audit_scope:
                audit_findings['allocations'] = self._audit_allocations(start_date, end_date)

            # Compliance audit
            if 'compliance' in audit_scope:
                audit_findings['compliance'] = self._audit_compliance(start_date, end_date)

            # Funding pools audit
            if 'funding_pools' in audit_scope:
                audit_findings['funding_pools'] = self._audit_funding_pools()

            # Set audit data
            report.report_data = {
                'audit_scope': audit_scope,
                'audit_findings': audit_findings,
                'audit_summary': self._generate_audit_summary(audit_findings)
            }

            # Generate comprehensive metrics
            summary_metrics = {
                'audit_period_days': (end_date - start_date).days,
                'scope_count': len(audit_scope),
                'findings_count': sum(len(v.get('issues', [])) for v in audit_findings.values()),
                'critical_findings': sum(len([i for i in v.get('issues', []) if i.get('severity') == 'critical'])
                                       for v in audit_findings.values()),
                'audit_score': self._calculate_audit_score(audit_findings)
            }

            report.summary_metrics = summary_metrics

            # Generate file
            file_url = f"/reports/{report._id}/audit_report.{report_format}"
            file_size = 1024 * 100  # Mock file size

            report.complete_generation(file_url, file_size)
            self.report_repo.update_report(report)

            current_app.logger.info(f"Audit report generated successfully: {report._id}")

            return True, "AUDIT_REPORT_GENERATED_SUCCESS", report.to_dict()

        except Exception as e:
            current_app.logger.error(f"Audit report generation failed: {str(e)}")
            return False, "AUDIT_REPORT_GENERATION_FAILED", None

    def _audit_transactions(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Perform transaction audit."""
        try:
            # Get all transactions in period
            success, _, transactions = self.transaction_repo.get_transactions_by_date_range(
                start_date, end_date, limit=5000
            )

            if not success:
                transactions = []

            issues = []
            total_transactions = len(transactions)
            failed_transactions = [t for t in transactions if t.status == "failed"]
            pending_transactions = [t for t in transactions if t.status == "pending"]

            # Check for issues
            if len(failed_transactions) > total_transactions * 0.05:  # More than 5% failed
                issues.append({
                    'type': 'high_failure_rate',
                    'severity': 'warning',
                    'description': f'High transaction failure rate: {len(failed_transactions)}/{total_transactions}',
                    'count': len(failed_transactions)
                })

            if len(pending_transactions) > total_transactions * 0.02:  # More than 2% pending
                issues.append({
                    'type': 'high_pending_rate',
                    'severity': 'warning',
                    'description': f'High pending transaction rate: {len(pending_transactions)}/{total_transactions}',
                    'count': len(pending_transactions)
                })

            return {
                'total_transactions': total_transactions,
                'successful_transactions': len([t for t in transactions if t.status == "completed"]),
                'failed_transactions': len(failed_transactions),
                'pending_transactions': len(pending_transactions),
                'issues': issues
            }

        except Exception:
            return {'error': 'Transaction audit failed'}

    def _audit_allocations(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Perform allocation audit."""
        try:
            success, _, metrics = self.allocation_repo.get_allocation_performance_metrics(
                start_date, end_date
            )

            if not success:
                return {'error': 'Allocation metrics retrieval failed'}

            issues = []
            success_rate = metrics.get('success_rate', 0)
            avg_processing_time = metrics.get('avg_processing_time', 0)

            # Check for issues
            if success_rate < 90:  # Less than 90% success rate
                issues.append({
                    'type': 'low_success_rate',
                    'severity': 'critical' if success_rate < 80 else 'warning',
                    'description': f'Low allocation success rate: {success_rate:.2f}%',
                    'value': success_rate
                })

            if avg_processing_time > 300:  # More than 5 minutes average
                issues.append({
                    'type': 'slow_processing',
                    'severity': 'warning',
                    'description': f'Slow allocation processing: {avg_processing_time:.2f}s average',
                    'value': avg_processing_time
                })

            return {
                'total_allocations': metrics.get('total_allocations', 0),
                'successful_allocations': metrics.get('successful_allocations', 0),
                'failed_allocations': metrics.get('failed_allocations', 0),
                'success_rate': success_rate,
                'avg_processing_time': avg_processing_time,
                'issues': issues
            }

        except Exception:
            return {'error': 'Allocation audit failed'}

    def _audit_compliance(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Perform compliance audit."""
        try:
            # This would typically involve checking compliance scores, regulations, etc.
            # For now, return basic audit structure
            issues = []

            return {
                'compliance_checks_performed': 0,
                'compliance_violations': 0,
                'average_compliance_score': 0,
                'issues': issues
            }

        except Exception:
            return {'error': 'Compliance audit failed'}

    def _audit_funding_pools(self) -> Dict[str, Any]:
        """Perform funding pools audit."""
        try:
            success, _, stats = self.pool_repo.get_pool_statistics()

            if not success:
                return {'error': 'Funding pool statistics retrieval failed'}

            issues = []
            depleted_pools = stats.get('depleted_pools', 0)
            total_pools = stats.get('total_pools', 1)

            if depleted_pools > total_pools * 0.3:  # More than 30% depleted
                issues.append({
                    'type': 'high_depletion_rate',
                    'severity': 'warning',
                    'description': f'High pool depletion rate: {depleted_pools}/{total_pools}',
                    'count': depleted_pools
                })

            return {
                'total_pools': total_pools,
                'active_pools': stats.get('active_pools', 0),
                'depleted_pools': depleted_pools,
                'total_balance': stats.get('total_balance', 0),
                'utilization_rate': stats.get('avg_utilization', 0),
                'issues': issues
            }

        except Exception:
            return {'error': 'Funding pools audit failed'}

    def _generate_audit_summary(self, audit_findings: Dict[str, Any]) -> Dict[str, Any]:
        """Generate audit summary from findings."""
        total_issues = 0
        critical_issues = 0

        for category, findings in audit_findings.items():
            issues = findings.get('issues', [])
            total_issues += len(issues)
            critical_issues += len([i for i in issues if i.get('severity') == 'critical'])

        return {
            'total_issues': total_issues,
            'critical_issues': critical_issues,
            'warning_issues': total_issues - critical_issues,
            'categories_audited': len(audit_findings),
            'overall_status': 'critical' if critical_issues > 0 else 'warning' if total_issues > 0 else 'clean'
        }

    def _calculate_audit_score(self, audit_findings: Dict[str, Any]) -> float:
        """Calculate overall audit score (0-100)."""
        try:
            base_score = 100.0

            for category, findings in audit_findings.items():
                issues = findings.get('issues', [])
                for issue in issues:
                    if issue.get('severity') == 'critical':
                        base_score -= 20
                    elif issue.get('severity') == 'warning':
                        base_score -= 10

            return max(0.0, base_score)

        except Exception:
            return 0.0

    def get_analytics_dashboard_data(self, period_days: int = 30) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Get real-time analytics data for dashboard."""
        try:
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=period_days)

            # Get transaction trends
            success, _, transaction_trends = self.transaction_repo.get_transaction_trends(period_days)
            if not success:
                transaction_trends = []

            # Get allocation trends
            success, _, allocation_trends = self.allocation_repo.get_allocation_trends(period_days)
            if not success:
                allocation_trends = []

            # Get current statistics
            success, _, current_stats = self._get_current_financial_stats()
            if not success:
                current_stats = {}

            dashboard_data = {
                'period_days': period_days,
                'generated_at': datetime.now(timezone.utc).isoformat(),
                'transaction_trends': transaction_trends,
                'allocation_trends': allocation_trends,
                'current_statistics': current_stats,
                'key_metrics': {
                    'total_active_onlus': current_stats.get('active_onlus_count', 0),
                    'total_donations_today': current_stats.get('donations_today', 0),
                    'allocation_success_rate': current_stats.get('allocation_success_rate', 0),
                    'avg_donation_amount': current_stats.get('avg_donation_amount', 0)
                }
            }

            return True, "ANALYTICS_DASHBOARD_SUCCESS", dashboard_data

        except Exception as e:
            current_app.logger.error(f"Analytics dashboard data failed: {str(e)}")
            return False, "ANALYTICS_DASHBOARD_FAILED", None

    def _get_current_financial_stats(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Get current financial statistics."""
        try:
            today = datetime.now(timezone.utc).date()
            start_of_day = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)
            end_of_day = datetime.combine(today, datetime.max.time()).replace(tzinfo=timezone.utc)

            # Get today's transactions
            success, _, today_transactions = self.transaction_repo.get_transactions_by_date_range(
                start_of_day, end_of_day
            )

            if not success:
                today_transactions = []

            # Calculate stats
            donations_today = [t for t in today_transactions if t.transaction_type == TransactionType.DONATED.value]
            total_donations_today = sum(t.amount for t in donations_today)
            avg_donation = total_donations_today / len(donations_today) if donations_today else 0

            stats = {
                'donations_today': len(donations_today),
                'total_amount_today': float(total_donations_today),
                'avg_donation_amount': float(avg_donation),
                'transactions_today': len(today_transactions),
                'active_onlus_count': 0,  # Would need to query ONLUS repo
                'allocation_success_rate': 0  # Would need recent allocation data
            }

            return True, "CURRENT_STATS_SUCCESS", stats

        except Exception as e:
            return False, f"CURRENT_STATS_FAILED: {str(e)}", None

    def export_report_data(self, report_id: str, export_format: str = "csv") -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Export report data in specified format."""
        try:
            # Get report
            success, _, report = self.report_repo.get_report_by_id(report_id)
            if not success or not report:
                return False, "REPORT_NOT_FOUND", None

            if export_format.lower() == "csv":
                # Export to CSV format
                csv_data = self._export_to_csv(report)
                return True, "REPORT_EXPORTED_CSV_SUCCESS", {
                    "format": "csv",
                    "data": csv_data,
                    "filename": f"report_{report_id}.csv"
                }

            elif export_format.lower() == "json":
                # Export to JSON format
                json_data = self._export_to_json(report)
                return True, "REPORT_EXPORTED_JSON_SUCCESS", {
                    "format": "json",
                    "data": json_data,
                    "filename": f"report_{report_id}.json"
                }

            else:
                return False, "UNSUPPORTED_EXPORT_FORMAT", None

        except Exception as e:
            current_app.logger.error(f"Report export failed: {str(e)}")
            return False, "REPORT_EXPORT_FAILED", None

    def _export_to_csv(self, report: FinancialReport) -> str:
        """Export report data to CSV format."""
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow(['Report Title', report.report_title])
        writer.writerow(['Report Type', report.report_type])
        writer.writerow(['Period', f"{report.start_date.isoformat()} to {report.end_date.isoformat()}"])
        writer.writerow(['Generated', report.generated_at.isoformat() if report.generated_at else 'N/A'])
        writer.writerow([])  # Empty row

        # Write summary metrics
        writer.writerow(['Summary Metrics'])
        for key, value in report.summary_metrics.items():
            writer.writerow([key.replace('_', ' ').title(), value])
        writer.writerow([])  # Empty row

        # Write transaction details if available
        if report.detailed_transactions:
            writer.writerow(['Transaction Details'])
            if report.detailed_transactions:
                # Get headers from first transaction
                headers = list(report.detailed_transactions[0].keys())
                writer.writerow(headers)

                for transaction in report.detailed_transactions:
                    writer.writerow([transaction.get(h, '') for h in headers])

        return output.getvalue()

    def _export_to_json(self, report: FinancialReport) -> str:
        """Export report data to JSON format."""
        export_data = {
            'report_info': {
                'title': report.report_title,
                'type': report.report_type,
                'period_start': report.start_date.isoformat(),
                'period_end': report.end_date.isoformat(),
                'generated_at': report.generated_at.isoformat() if report.generated_at else None
            },
            'summary_metrics': report.summary_metrics,
            'detailed_transactions': report.detailed_transactions,
            'allocation_breakdown': report.allocation_breakdown,
            'report_data': report.report_data
        }

        return json.dumps(export_data, indent=2, default=str)