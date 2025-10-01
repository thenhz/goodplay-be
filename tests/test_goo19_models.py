import pytest
from datetime import datetime, timezone, timedelta
from bson import ObjectId
import os

# Set testing environment before importing app modules
os.environ['TESTING'] = 'true'

from app.onlus.models.allocation_request import (
    AllocationRequest, AllocationRequestStatus, AllocationPriority
)
from app.onlus.models.allocation_result import (
    AllocationResult, AllocationResultStatus, AllocationMethod
)
from app.onlus.models.funding_pool import (
    FundingPool, FundingPoolStatus, FundingPoolType
)
from app.onlus.models.financial_report import (
    FinancialReport, ReportType, ReportStatus, ReportFormat
)
from app.onlus.models.compliance_score import (
    ComplianceScore, ComplianceLevel, ComplianceCategory, RiskLevel
)


class TestAllocationRequest:
    """Test cases for AllocationRequest model."""

    def test_allocation_request_creation_success(self):
        """Test successful allocation request creation."""
        request = AllocationRequest(
            onlus_id="onlus_123",
            requested_amount=1000.0,
            project_title="Test Project",
            project_description="A test project for allocation",
            urgency_level=3,
            category="healthcare"
        )

        assert request.onlus_id == "onlus_123"
        assert request.requested_amount == 1000.0
        assert request.project_title == "Test Project"
        assert request.project_description == "A test project for allocation"
        assert request.urgency_level == 3
        assert request.category == "healthcare"
        assert request.status == "pending"
        assert request.priority == 2
        assert request.allocation_score == 0.0
        assert isinstance(request.created_at, datetime)
        assert isinstance(request.updated_at, datetime)

    def test_allocation_request_approve(self):
        """Test allocation request approval."""
        request = AllocationRequest(
            onlus_id="onlus_123",
            requested_amount=1000.0,
            project_title="Test Project",
            project_description="Test description"
        )

        request.approve_request("Approved for high impact")

        assert request.status == AllocationRequestStatus.APPROVED.value
        assert request.approval_notes == "Approved for high impact"
        assert request.updated_at is not None

    def test_allocation_request_reject(self):
        """Test allocation request rejection."""
        request = AllocationRequest(
            onlus_id="onlus_123",
            requested_amount=1000.0,
            project_title="Test Project",
            project_description="Test description"
        )

        request.reject_request("Insufficient documentation")

        assert request.status == AllocationRequestStatus.REJECTED.value
        assert request.rejection_reason == "Insufficient documentation"

    def test_allocation_request_is_emergency(self):
        """Test emergency request identification."""
        regular_request = AllocationRequest(
            onlus_id="onlus_123",
            requested_amount=1000.0,
            project_title="Regular Project",
            project_description="Regular project",
            priority=2
        )

        emergency_request = AllocationRequest(
            onlus_id="onlus_456",
            requested_amount=5000.0,
            project_title="Emergency Project",
            project_description="Emergency project",
            priority=AllocationPriority.EMERGENCY.value
        )

        assert not regular_request.is_emergency()
        assert emergency_request.is_emergency()

    def test_allocation_request_deadline_handling(self):
        """Test deadline-related methods."""
        future_deadline = datetime.now(timezone.utc) + timedelta(days=10)
        past_deadline = datetime.now(timezone.utc) - timedelta(days=5)

        active_request = AllocationRequest(
            onlus_id="onlus_123",
            requested_amount=1000.0,
            project_title="Active Project",
            project_description="Active project",
            deadline=future_deadline
        )

        expired_request = AllocationRequest(
            onlus_id="onlus_456",
            requested_amount=2000.0,
            project_title="Expired Project",
            project_description="Expired project",
            deadline=past_deadline
        )

        assert not active_request.is_expired()
        assert expired_request.is_expired()
        assert active_request.get_days_until_deadline() >= 9  # Account for processing time
        assert expired_request.get_days_until_deadline() == 0

    def test_allocation_request_score_update(self):
        """Test allocation score update."""
        request = AllocationRequest(
            onlus_id="onlus_123",
            requested_amount=1000.0,
            project_title="Test Project",
            project_description="Test description"
        )

        assert request.allocation_score == 0.0

        request.update_allocation_score(85.5)

        assert request.allocation_score == 85.5
        assert request.updated_at is not None

    def test_allocation_request_to_dict(self):
        """Test allocation request dictionary conversion."""
        request = AllocationRequest(
            onlus_id="onlus_123",
            requested_amount=1000.0,
            project_title="Test Project",
            project_description="Test description",
            category="education",
            urgency_level=4
        )

        request_dict = request.to_dict()

        assert request_dict['onlus_id'] == "onlus_123"
        assert request_dict['requested_amount'] == 1000.0
        assert request_dict['project_title'] == "Test Project"
        assert request_dict['category'] == "education"
        assert request_dict['urgency_level'] == 4
        assert 'is_expired' in request_dict
        assert 'days_until_deadline' in request_dict


class TestAllocationResult:
    """Test cases for AllocationResult model."""

    def test_allocation_result_creation_success(self):
        """Test successful allocation result creation."""
        result = AllocationResult(
            request_id="req_123",
            onlus_id="onlus_456",
            donor_ids=["donor_1", "donor_2"],
            allocated_amount=1500.0,
            total_donations_amount=1600.0,
            allocation_method="automatic"
        )

        assert result.request_id == "req_123"
        assert result.onlus_id == "onlus_456"
        assert result.donor_ids == ["donor_1", "donor_2"]
        assert result.allocated_amount == 1500.0
        assert result.total_donations_amount == 1600.0
        assert result.allocation_method == "automatic"
        assert result.status == "scheduled"
        assert result.fees_deducted == 0.0
        assert result.net_amount == 1500.0
        assert isinstance(result.created_at, datetime)

    def test_allocation_result_mark_completed(self):
        """Test marking allocation result as completed."""
        result = AllocationResult(
            request_id="req_123",
            onlus_id="onlus_456",
            donor_ids=["donor_1"],
            allocated_amount=1000.0,
            total_donations_amount=1000.0
        )

        transaction_ids = ["tx_1", "tx_2"]
        impact_metrics = {"beneficiaries": 100, "impact_score": 8.5}

        result.mark_completed(transaction_ids, impact_metrics)

        assert result.status == AllocationResultStatus.COMPLETED.value
        assert result.completed_at is not None
        assert result.transaction_ids == transaction_ids
        assert result.impact_metrics == impact_metrics

    def test_allocation_result_mark_failed(self):
        """Test marking allocation result as failed."""
        result = AllocationResult(
            request_id="req_123",
            onlus_id="onlus_456",
            donor_ids=["donor_1"],
            allocated_amount=1000.0,
            total_donations_amount=1000.0
        )

        result.mark_failed("Payment processing failed", {"error_code": "PAYMENT_001"})

        assert result.status == AllocationResultStatus.FAILED.value
        assert "error_message" in result.error_details
        assert result.error_details["error_message"] == "Payment processing failed"
        assert result.error_details["error_code"] == "PAYMENT_001"

    def test_allocation_result_add_transaction(self):
        """Test adding transaction to allocation result."""
        result = AllocationResult(
            request_id="req_123",
            onlus_id="onlus_456",
            donor_ids=[],
            allocated_amount=1000.0,
            total_donations_amount=1000.0
        )

        result.add_transaction("tx_123", "donor_456", 500.0)

        assert "tx_123" in result.transaction_ids
        assert len(result.donor_breakdown) == 1
        assert result.donor_breakdown[0]['transaction_id'] == "tx_123"
        assert result.donor_breakdown[0]['donor_id'] == "donor_456"
        assert result.donor_breakdown[0]['amount'] == 500.0

    def test_allocation_result_efficiency_calculation(self):
        """Test efficiency ratio calculation."""
        result = AllocationResult(
            request_id="req_123",
            onlus_id="onlus_456",
            donor_ids=["donor_1"],
            allocated_amount=950.0,
            total_donations_amount=1000.0,
            fees_deducted=50.0
        )

        efficiency = result.calculate_efficiency_ratio()
        expected_efficiency = 900.0 / 1000.0  # (allocated - fees) / total

        assert abs(efficiency - expected_efficiency) < 0.001

    def test_allocation_result_is_successful(self):
        """Test successful allocation identification."""
        completed_result = AllocationResult(
            request_id="req_123",
            onlus_id="onlus_456",
            donor_ids=["donor_1"],
            allocated_amount=1000.0,
            total_donations_amount=1000.0,
            status="completed"
        )

        failed_result = AllocationResult(
            request_id="req_456",
            onlus_id="onlus_789",
            donor_ids=["donor_1"],
            allocated_amount=1000.0,
            total_donations_amount=1000.0,
            status="failed"
        )

        assert completed_result.is_successful()
        assert not failed_result.is_successful()


class TestFundingPool:
    """Test cases for FundingPool model."""

    def test_funding_pool_creation_success(self):
        """Test successful funding pool creation."""
        pool = FundingPool(
            pool_name="General Donation Pool",
            pool_type="general",
            total_balance=10000.0,
            available_balance=8000.0,
            allocated_balance=2000.0
        )

        assert pool.pool_name == "General Donation Pool"
        assert pool.pool_type == "general"
        assert pool.total_balance == 10000.0
        assert pool.available_balance == 8000.0
        assert pool.allocated_balance == 2000.0
        assert pool.reserved_balance == 0.0
        assert pool.status == "active"
        assert pool.auto_allocation_enabled is True
        assert isinstance(pool.created_at, datetime)

    def test_funding_pool_add_funds(self):
        """Test adding funds to pool."""
        pool = FundingPool(
            pool_name="Test Pool",
            pool_type="general",
            total_balance=5000.0,
            available_balance=5000.0
        )

        initial_total = pool.total_balance
        initial_available = pool.available_balance

        success = pool.add_funds(1000.0, "tx_123")

        assert success is True
        assert pool.total_balance == initial_total + 1000.0
        assert pool.available_balance == initial_available + 1000.0
        assert "tx_123" in pool.source_transactions

    def test_funding_pool_add_invalid_funds(self):
        """Test adding invalid funds to pool."""
        pool = FundingPool(
            pool_name="Test Pool",
            pool_type="general",
            total_balance=5000.0,
            available_balance=5000.0
        )

        # Test negative amount
        success = pool.add_funds(-100.0)
        assert success is False

        # Test zero amount
        success = pool.add_funds(0.0)
        assert success is False

    def test_funding_pool_reserve_funds(self):
        """Test reserving funds in pool."""
        pool = FundingPool(
            pool_name="Test Pool",
            pool_type="general",
            total_balance=5000.0,
            available_balance=5000.0
        )

        success = pool.reserve_funds(1000.0, "reservation_123")

        assert success is True
        assert pool.available_balance == 4000.0
        assert pool.reserved_balance == 1000.0

    def test_funding_pool_allocate_funds(self):
        """Test allocating funds from pool."""
        pool = FundingPool(
            pool_name="Test Pool",
            pool_type="general",
            total_balance=5000.0,
            available_balance=3000.0,
            reserved_balance=1000.0
        )

        success = pool.allocate_funds(2000.0, "alloc_123", "onlus_456")

        assert success is True
        assert pool.available_balance == 1000.0  # 3000 - 2000
        assert pool.allocated_balance == 2000.0
        assert len(pool.allocation_history) == 1
        assert pool.allocation_history[0]['allocation_id'] == "alloc_123"

    def test_funding_pool_can_allocate(self):
        """Test allocation eligibility check."""
        pool = FundingPool(
            pool_name="Test Pool",
            pool_type="general",
            total_balance=5000.0,
            available_balance=3000.0,
            reserved_balance=1000.0,
            minimum_allocation=100.0,
            maximum_allocation=5000.0,
            category_restrictions=["healthcare", "education"]
        )

        # Valid allocation
        assert pool.can_allocate(1000.0, "healthcare") is True

        # Amount too small
        assert pool.can_allocate(50.0, "healthcare") is False

        # Amount too large
        assert pool.can_allocate(6000.0, "healthcare") is False

        # Insufficient funds
        assert pool.can_allocate(5000.0, "healthcare") is False

        # Wrong category
        assert pool.can_allocate(1000.0, "environment") is False

    def test_funding_pool_utilization_rates(self):
        """Test utilization and availability rate calculations."""
        pool = FundingPool(
            pool_name="Test Pool",
            pool_type="general",
            total_balance=10000.0,
            available_balance=6000.0,
            allocated_balance=3000.0,
            reserved_balance=1000.0
        )

        utilization_rate = pool.get_utilization_rate()
        availability_rate = pool.get_availability_rate()

        assert abs(utilization_rate - 0.3) < 0.001  # 3000/10000
        assert abs(availability_rate - 0.6) < 0.001  # 6000/10000


class TestFinancialReport:
    """Test cases for FinancialReport model."""

    def test_financial_report_creation_success(self):
        """Test successful financial report creation."""
        start_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(2024, 1, 31, tzinfo=timezone.utc)

        report = FinancialReport(
            report_type="monthly",
            report_title="January 2024 Report",
            start_date=start_date,
            end_date=end_date,
            generated_for_id="onlus_123"
        )

        assert report.report_type == "monthly"
        assert report.report_title == "January 2024 Report"
        assert report.start_date == start_date
        assert report.end_date == end_date
        assert report.generated_for_id == "onlus_123"
        assert report.status == "pending"
        assert report.report_format == "pdf"
        assert report.is_confidential is False

    def test_financial_report_generation_workflow(self):
        """Test report generation workflow."""
        start_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(2024, 1, 31, tzinfo=timezone.utc)

        report = FinancialReport(
            report_type="monthly",
            report_title="Test Report",
            start_date=start_date,
            end_date=end_date
        )

        # Start generation
        report.start_generation()
        assert report.status == ReportStatus.GENERATING.value

        # Complete generation
        report.complete_generation("/reports/test.pdf", 1024)
        assert report.status == ReportStatus.COMPLETED.value
        assert report.file_url == "/reports/test.pdf"
        assert report.file_size == 1024
        assert report.generated_at is not None

    def test_financial_report_fail_generation(self):
        """Test report generation failure."""
        start_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(2024, 1, 31, tzinfo=timezone.utc)

        report = FinancialReport(
            report_type="monthly",
            report_title="Test Report",
            start_date=start_date,
            end_date=end_date
        )

        report.fail_generation("Database connection error")

        assert report.status == ReportStatus.FAILED.value
        assert report.error_message == "Database connection error"

    def test_financial_report_access_permissions(self):
        """Test report access permissions."""
        start_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(2024, 1, 31, tzinfo=timezone.utc)

        public_report = FinancialReport(
            report_type="monthly",
            report_title="Public Report",
            start_date=start_date,
            end_date=end_date,
            is_confidential=False
        )

        confidential_report = FinancialReport(
            report_type="donor_statement",
            report_title="Private Statement",
            start_date=start_date,
            end_date=end_date,
            generated_for_id="donor_123",
            is_confidential=True,
            access_permissions=["donor_123", "admin_456"]
        )

        # Public report accessible by anyone
        assert public_report.is_accessible_by("any_user")

        # Confidential report access rules
        assert confidential_report.is_accessible_by("donor_123")
        assert confidential_report.is_accessible_by("admin_456")
        assert not confidential_report.is_accessible_by("other_user")

    def test_financial_report_calculations(self):
        """Test report calculation methods."""
        start_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(2024, 1, 31, tzinfo=timezone.utc)

        report = FinancialReport(
            report_type="monthly",
            report_title="Test Report",
            start_date=start_date,
            end_date=end_date
        )

        # Add transaction details
        report.add_transaction_detail({
            'transaction_type': 'donated',
            'amount': 1000.0
        })
        report.add_transaction_detail({
            'transaction_type': 'donated',
            'amount': 500.0
        })
        report.add_transaction_detail({
            'transaction_type': 'earned',
            'amount': 200.0
        })

        # Set allocation breakdown
        report.set_allocation_breakdown({
            'onlus_1': {'amount': 800.0},
            'onlus_2': {'amount': 700.0}
        })

        total_donations = report.calculate_total_donations()
        total_allocations = report.calculate_total_allocations()
        efficiency_ratio = report.get_efficiency_ratio()

        assert total_donations == 1500.0  # Only donated transactions
        assert total_allocations == 1500.0  # Sum of allocations
        assert abs(efficiency_ratio - 1.0) < 0.001  # Perfect efficiency


class TestComplianceScore:
    """Test cases for ComplianceScore model."""

    def test_compliance_score_creation_success(self):
        """Test successful compliance score creation."""
        start_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(2024, 12, 31, tzinfo=timezone.utc)

        score = ComplianceScore(
            onlus_id="onlus_123",
            assessment_period_start=start_date,
            assessment_period_end=end_date,
            overall_score=85.0,
            compliance_level="good"
        )

        assert score.onlus_id == "onlus_123"
        assert score.assessment_period_start == start_date
        assert score.assessment_period_end == end_date
        assert score.overall_score == 85.0
        assert score.compliance_level == "good"
        assert score.risk_level == "moderate"
        assert score.is_current is True
        assert score.is_verified is False

    def test_compliance_score_calculation(self):
        """Test overall compliance score calculation."""
        start_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(2024, 12, 31, tzinfo=timezone.utc)

        score = ComplianceScore(
            onlus_id="onlus_123",
            assessment_period_start=start_date,
            assessment_period_end=end_date
        )

        # Set category scores
        score.category_scores = {
            ComplianceCategory.FINANCIAL_TRANSPARENCY.value: 90.0,
            ComplianceCategory.OPERATIONAL_EFFICIENCY.value: 85.0,
            ComplianceCategory.GOVERNANCE.value: 80.0,
            ComplianceCategory.IMPACT_REPORTING.value: 75.0,
            ComplianceCategory.REGULATORY_COMPLIANCE.value: 95.0,
            ComplianceCategory.DONOR_TRUST.value: 88.0
        }

        score.calculate_overall_score()

        # Expected: 90*0.25 + 85*0.20 + 80*0.20 + 75*0.15 + 95*0.15 + 88*0.05
        expected_score = 22.5 + 17.0 + 16.0 + 11.25 + 14.25 + 4.4  # = 85.4
        assert abs(score.overall_score - expected_score) < 0.1

    def test_compliance_score_level_update(self):
        """Test compliance level automatic update."""
        start_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(2024, 12, 31, tzinfo=timezone.utc)

        score = ComplianceScore(
            onlus_id="onlus_123",
            assessment_period_start=start_date,
            assessment_period_end=end_date
        )

        # Test excellent level
        score.overall_score = 95.0
        score.update_compliance_level()
        assert score.compliance_level == ComplianceLevel.EXCELLENT.value

        # Test critical level
        score.overall_score = 45.0
        score.update_compliance_level()
        assert score.compliance_level == ComplianceLevel.CRITICAL.value

    def test_compliance_score_issue_management(self):
        """Test compliance issue addition and resolution."""
        start_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(2024, 12, 31, tzinfo=timezone.utc)

        score = ComplianceScore(
            onlus_id="onlus_123",
            assessment_period_start=start_date,
            assessment_period_end=end_date
        )

        # Add compliance issue
        score.add_compliance_issue(
            "missing_documentation",
            "Tax ID documentation missing",
            "high",
            ComplianceCategory.REGULATORY_COMPLIANCE.value
        )

        assert len(score.compliance_issues) == 1
        issue = score.compliance_issues[0]
        assert issue['issue_type'] == "missing_documentation"
        assert issue['severity'] == "high"
        assert issue['status'] == 'open'

        # Resolve issue
        issue_id = issue['issue_id']
        success = score.resolve_compliance_issue(issue_id, "Documentation provided")

        assert success is True
        resolved_issue = next(i for i in score.compliance_issues if i['issue_id'] == issue_id)
        assert resolved_issue['status'] == 'resolved'
        assert resolved_issue['resolution_notes'] == "Documentation provided"

    def test_compliance_score_monitoring_alerts(self):
        """Test monitoring alert management."""
        start_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(2024, 12, 31, tzinfo=timezone.utc)

        score = ComplianceScore(
            onlus_id="onlus_123",
            assessment_period_start=start_date,
            assessment_period_end=end_date
        )

        # Add monitoring alert
        score.add_monitoring_alert(
            "performance_drop",
            "Allocation success rate dropped below 90%",
            "medium"
        )

        assert len(score.monitoring_alerts) == 1
        alert = score.monitoring_alerts[0]
        assert alert['alert_type'] == "performance_drop"
        assert alert['urgency'] == "medium"
        assert alert['status'] == 'active'

        # Dismiss alert
        alert_id = alert['alert_id']
        success = score.dismiss_monitoring_alert(alert_id)

        assert success is True
        dismissed_alert = next(a for a in score.monitoring_alerts if a['alert_id'] == alert_id)
        assert dismissed_alert['status'] == 'dismissed'

    def test_compliance_score_verification(self):
        """Test assessment verification."""
        start_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(2024, 12, 31, tzinfo=timezone.utc)

        score = ComplianceScore(
            onlus_id="onlus_123",
            assessment_period_start=start_date,
            assessment_period_end=end_date
        )

        assert score.is_verified is False

        score.verify_assessment("admin_456", "Assessment reviewed and approved")

        assert score.is_verified is True
        assert score.verification_details['verifier_id'] == "admin_456"
        assert score.verification_details['verification_notes'] == "Assessment reviewed and approved"

    def test_compliance_score_counts(self):
        """Test various count methods."""
        start_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(2024, 12, 31, tzinfo=timezone.utc)

        score = ComplianceScore(
            onlus_id="onlus_123",
            assessment_period_start=start_date,
            assessment_period_end=end_date
        )

        # Add issues of different severities
        score.add_compliance_issue("issue1", "Description 1", "critical")
        score.add_compliance_issue("issue2", "Description 2", "high")
        score.add_compliance_issue("issue3", "Description 3", "medium")

        # Add alerts
        score.add_monitoring_alert("alert1", "Alert 1", "high")
        score.add_monitoring_alert("alert2", "Alert 2", "medium")

        # Resolve one issue
        first_issue_id = score.compliance_issues[0]['issue_id']
        score.resolve_compliance_issue(first_issue_id)

        assert score.get_open_issues_count() == 2  # 3 total - 1 resolved
        assert score.get_critical_issues_count() == 0  # Critical issue was resolved
        assert score.get_active_alerts_count() == 2


if __name__ == '__main__':
    pytest.main([__file__])