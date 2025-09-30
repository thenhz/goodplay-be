import pytest
import os
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta

# Set testing environment before importing app modules
os.environ['TESTING'] = 'true'

from app.admin.models.admin_user import AdminUser
from app.admin.models.admin_action import AdminAction, ActionType, TargetType
from app.admin.services.security_service import SecurityService
from app.admin.services.audit_service import AuditService


class TestSecurityService:
    """Test security service functionality"""

    @patch('app.admin.services.security_service.AuditRepository')
    @patch('app.admin.services.security_service.AdminRepository')
    def test_security_service_initialization(self, mock_admin_repo, mock_audit_repo):
        """Test security service initialization"""
        service = SecurityService()
        assert service.audit_repository is not None
        assert service.admin_repository is not None

    @patch('app.admin.services.security_service.AuditRepository')
    @patch('app.admin.services.security_service.AdminRepository')
    def test_detect_suspicious_login_patterns(self, mock_admin_repo, mock_audit_repo):
        """Test detection of suspicious login patterns"""
        # Setup mocks
        mock_audit_instance = MagicMock()
        mock_audit_repo.return_value = mock_audit_instance

        # Mock failed login attempts from same IP
        failed_logins = []
        for i in range(5):
            action = AdminAction.create_security_action(
                admin_id="unknown",
                action_type="failed_login_attempt",
                ip_address="192.168.1.100",
                details={"username": f"admin{i}", "timestamp": datetime.now(timezone.utc)}
            )
            failed_logins.append(action)

        mock_audit_instance.get_actions_by_type.return_value = failed_logins

        service = SecurityService()

        # Detect suspicious patterns
        success, message, alerts = service.detect_suspicious_activity()

        assert success
        assert len(alerts) > 0
        assert any("Multiple failed login attempts" in alert['description'] for alert in alerts)

    @patch('app.admin.services.security_service.AuditRepository')
    @patch('app.admin.services.security_service.AdminRepository')
    def test_detect_unusual_access_patterns(self, mock_admin_repo, mock_audit_repo):
        """Test detection of unusual access patterns"""
        # Setup mocks
        mock_audit_instance = MagicMock()
        mock_audit_repo.return_value = mock_audit_instance

        # Mock access from unusual location/time
        unusual_access = AdminAction.create_security_action(
            admin_id="admin123",
            action_type="admin_login",
            ip_address="203.0.113.50",  # Different country IP
            details={
                "user_agent": "Unknown Browser",
                "timestamp": datetime.now(timezone.utc).replace(hour=3),  # 3 AM access
                "geolocation": {"country": "Unknown", "city": "Unknown"}
            }
        )

        mock_audit_instance.get_recent_actions.return_value = [unusual_access]

        service = SecurityService()

        alerts = service.analyze_access_patterns("admin123")
        assert len(alerts) > 0
        assert any("unusual" in alert['description'].lower() for alert in alerts)

    @patch('app.admin.services.security_service.AuditRepository')
    @patch('app.admin.services.security_service.AdminRepository')
    def test_detect_privilege_escalation_attempts(self, mock_admin_repo, mock_audit_repo):
        """Test detection of privilege escalation attempts"""
        # Setup mocks
        mock_audit_instance = MagicMock()
        mock_audit_repo.return_value = mock_audit_instance

        # Mock attempts to access higher privilege functions
        escalation_attempts = [
            AdminAction.create_user_action(
                admin_id="moderator123",
                action_type="attempted_system_config",
                user_id="",
                details={"permission_required": "system_administration", "has_permission": False}
            ),
            AdminAction.create_user_action(
                admin_id="moderator123",
                action_type="attempted_user_delete",
                user_id="user456",
                details={"permission_required": "user_management", "has_permission": False}
            )
        ]

        mock_audit_instance.get_actions_by_admin.return_value = escalation_attempts

        service = SecurityService()

        alerts = service.detect_privilege_escalation("moderator123")
        assert len(alerts) > 0
        assert any("privilege escalation" in alert['description'].lower() for alert in alerts)

    @patch('app.admin.services.security_service.AuditRepository')
    @patch('app.admin.services.security_service.AdminRepository')
    def test_brute_force_detection(self, mock_admin_repo, mock_audit_repo):
        """Test brute force attack detection"""
        # Setup mocks
        mock_audit_instance = MagicMock()
        mock_audit_repo.return_value = mock_audit_instance

        # Mock rapid failed login attempts
        failed_attempts = []
        base_time = datetime.now(timezone.utc)
        for i in range(10):
            action = AdminAction.create_security_action(
                admin_id="unknown",
                action_type="failed_login_attempt",
                ip_address="192.168.1.100",
                details={"username": "admin", "timestamp": base_time + timedelta(seconds=i*30)}
            )
            failed_attempts.append(action)

        mock_audit_instance.get_actions_in_timeframe.return_value = failed_attempts

        service = SecurityService()

        is_brute_force = service.detect_brute_force_attack("192.168.1.100")
        assert is_brute_force

    @patch('app.admin.services.security_service.AuditRepository')
    @patch('app.admin.services.security_service.AdminRepository')
    def test_account_lockout_management(self, mock_admin_repo, mock_audit_repo):
        """Test account lockout functionality"""
        # Setup mocks
        mock_admin_instance = MagicMock()
        mock_admin_repo.return_value = mock_admin_instance

        # Mock admin user
        admin_user = AdminUser(username="testadmin", email="test@admin.com", role="admin")
        admin_user.failed_login_attempts = 4  # One more failure should lock
        mock_admin_instance.find_by_username.return_value = admin_user

        service = SecurityService()

        # Test account lockout trigger
        should_lock = service.should_lock_account(admin_user)
        assert should_lock

        # Test account lockout execution
        success, message = service.lock_account("testadmin", "Too many failed attempts")
        assert success
        assert message == "ACCOUNT_LOCKED_SUCCESS"

    @patch('app.admin.services.security_service.AuditRepository')
    @patch('app.admin.services.security_service.AdminRepository')
    def test_security_audit_trail(self, mock_admin_repo, mock_audit_repo):
        """Test comprehensive security audit trail"""
        # Setup mocks
        mock_audit_instance = MagicMock()
        mock_audit_repo.return_value = mock_audit_instance

        # Mock security events
        security_events = [
            AdminAction.create_security_action("admin1", "login_success", "192.168.1.100"),
            AdminAction.create_security_action("admin1", "logout", "192.168.1.100"),
            AdminAction.create_security_action("unknown", "failed_login_attempt", "10.0.0.50"),
            AdminAction.create_security_action("admin2", "password_change", "192.168.1.200")
        ]

        mock_audit_instance.get_security_events.return_value = security_events

        service = SecurityService()

        success, message, audit_data = service.get_security_audit_trail()
        assert success
        assert len(audit_data['events']) == 4
        assert 'login_success' in [event.action_type for event in audit_data['events']]

    @patch('app.admin.services.security_service.AuditRepository')
    @patch('app.admin.services.security_service.AdminRepository')
    def test_ip_reputation_checking(self, mock_admin_repo, mock_audit_repo):
        """Test IP reputation and threat detection"""
        service = SecurityService()

        # Test known malicious IPs (would be from threat intelligence feeds)
        malicious_ips = ["198.51.100.1", "203.0.113.1"]

        for ip in malicious_ips:
            is_malicious = service.check_ip_reputation(ip)
            # In real implementation, this would check against threat feeds
            # For testing, we check the structure exists
            assert isinstance(is_malicious, bool)

        # Test legitimate IPs
        legitimate_ips = ["192.168.1.1", "10.0.0.1"]
        for ip in legitimate_ips:
            is_malicious = service.check_ip_reputation(ip)
            assert isinstance(is_malicious, bool)

    @patch('app.admin.services.security_service.AuditRepository')
    @patch('app.admin.services.security_service.AdminRepository')
    def test_session_hijacking_detection(self, mock_admin_repo, mock_audit_repo):
        """Test session hijacking detection"""
        # Setup mocks
        mock_audit_instance = MagicMock()
        mock_audit_repo.return_value = mock_audit_instance

        # Mock session activities from different IPs
        session_activities = [
            AdminAction.create_security_action(
                admin_id="admin123",
                action_type="api_access",
                ip_address="192.168.1.100",
                details={"session_id": "sess123", "timestamp": datetime.now(timezone.utc)}
            ),
            AdminAction.create_security_action(
                admin_id="admin123",
                action_type="api_access",
                ip_address="203.0.113.50",  # Different IP, same session
                details={"session_id": "sess123", "timestamp": datetime.now(timezone.utc)}
            )
        ]

        mock_audit_instance.get_session_activities.return_value = session_activities

        service = SecurityService()

        alerts = service.detect_session_anomalies("sess123")
        assert len(alerts) > 0
        assert any("session" in alert['description'].lower() for alert in alerts)

    def test_password_policy_enforcement(self):
        """Test password policy validation"""
        service = SecurityService()

        # Test strong passwords
        strong_passwords = [
            "MyStr0ng@Password2024",
            "Admin#Security!123",
            "C0mplex&P@ssw0rd"
        ]

        for password in strong_passwords:
            is_valid, issues = service.validate_password_strength(password)
            assert is_valid
            assert len(issues) == 0

        # Test weak passwords
        weak_passwords = [
            "password123",      # Too common
            "12345678",         # No letters
            "abcdefgh",         # No numbers/symbols
            "Pass1!",           # Too short
            "PASSWORD123!"      # No lowercase
        ]

        for password in weak_passwords:
            is_valid, issues = service.validate_password_strength(password)
            assert not is_valid
            assert len(issues) > 0

    @patch('app.admin.services.security_service.AuditRepository')
    @patch('app.admin.services.security_service.AdminRepository')
    def test_compliance_reporting(self, mock_admin_repo, mock_audit_repo):
        """Test compliance and regulatory reporting"""
        # Setup mocks
        mock_audit_instance = MagicMock()
        mock_audit_repo.return_value = mock_audit_instance

        # Mock compliance-relevant actions
        compliance_actions = [
            AdminAction.create_user_action("admin1", "user_data_access", "user123", reason="Support request"),
            AdminAction.create_user_action("admin2", "user_data_export", "user456", reason="GDPR request"),
            AdminAction.create_user_action("admin1", "user_data_deletion", "user789", reason="Account closure")
        ]

        mock_audit_instance.get_compliance_actions.return_value = compliance_actions

        service = SecurityService()

        success, message, report = service.generate_compliance_report("2024-01", "GDPR")
        assert success
        assert 'data_access_events' in report
        assert 'data_export_events' in report
        assert 'data_deletion_events' in report


class TestAuditService:
    """Test audit service functionality"""

    @patch('app.admin.services.audit_service.AuditRepository')
    def test_audit_service_initialization(self, mock_audit_repo):
        """Test audit service initialization"""
        service = AuditService()
        assert service.audit_repository is not None

    @patch('app.admin.services.audit_service.AuditRepository')
    def test_log_admin_action(self, mock_audit_repo):
        """Test logging of admin actions"""
        # Setup mocks
        mock_audit_instance = MagicMock()
        mock_audit_repo.return_value = mock_audit_instance
        mock_audit_instance.create.return_value = True

        service = AuditService()

        # Test action logging
        success, message = service.log_admin_action(
            admin_id="admin123",
            action_type="user_suspend",
            target_type="user",
            target_id="user456",
            details={"reason": "Policy violation", "duration": "7 days"}
        )

        assert success
        assert message == "ACTION_LOGGED_SUCCESS"
        mock_audit_instance.create.assert_called_once()

    @patch('app.admin.services.audit_service.AuditRepository')
    def test_get_audit_logs_with_filters(self, mock_audit_repo):
        """Test audit log retrieval with filters"""
        # Setup mocks
        mock_audit_instance = MagicMock()
        mock_audit_repo.return_value = mock_audit_instance

        # Mock audit logs
        audit_logs = [
            AdminAction.create_user_action("admin1", "user_suspend", "user123"),
            AdminAction.create_user_action("admin2", "user_activate", "user456"),
            AdminAction.create_security_action("admin1", "login_success", "192.168.1.100")
        ]

        mock_audit_instance.get_logs_with_filters.return_value = audit_logs

        service = AuditService()

        # Test filtered retrieval
        filters = {
            "admin_id": "admin1",
            "action_type": "user_suspend",
            "date_from": "2024-01-01",
            "date_to": "2024-01-31"
        }

        success, message, logs = service.get_audit_logs(filters)
        assert success
        assert len(logs) == 3

    @patch('app.admin.services.audit_service.AuditRepository')
    def test_audit_log_retention_policy(self, mock_audit_repo):
        """Test audit log retention and archival"""
        # Setup mocks
        mock_audit_instance = MagicMock()
        mock_audit_repo.return_value = mock_audit_instance

        # Mock old logs for deletion
        old_logs = [
            AdminAction.create_user_action(
                admin_id="admin1",
                action_type="user_login",
                user_id="user123"
            )
        ]
        # Set old timestamp
        for log in old_logs:
            log.timestamp = datetime.now(timezone.utc) - timedelta(days=400)  # Older than retention

        mock_audit_instance.get_logs_older_than.return_value = old_logs

        service = AuditService()

        # Test retention policy enforcement
        success, message, archived_count = service.enforce_retention_policy()
        assert success
        assert archived_count >= 0

    @patch('app.admin.services.audit_service.AuditRepository')
    def test_audit_log_integrity_verification(self, mock_audit_repo):
        """Test audit log integrity and tamper detection"""
        service = AuditService()

        # Test log integrity verification
        test_log = AdminAction.create_user_action("admin1", "user_suspend", "user123")

        # Calculate integrity hash
        original_hash = service.calculate_log_hash(test_log)
        assert original_hash is not None

        # Verify unchanged log
        is_valid = service.verify_log_integrity(test_log, original_hash)
        assert is_valid

        # Test tampered log detection
        test_log.reason = "Modified reason"  # Tamper with log
        is_valid = service.verify_log_integrity(test_log, original_hash)
        assert not is_valid

    @patch('app.admin.services.audit_service.AuditRepository')
    def test_audit_report_generation(self, mock_audit_repo):
        """Test audit report generation"""
        # Setup mocks
        mock_audit_instance = MagicMock()
        mock_audit_repo.return_value = mock_audit_instance

        # Mock varied audit data
        audit_data = [
            AdminAction.create_user_action("admin1", "user_suspend", "user1"),
            AdminAction.create_user_action("admin1", "user_activate", "user2"),
            AdminAction.create_user_action("admin2", "user_delete", "user3"),
            AdminAction.create_security_action("admin1", "login_success", "192.168.1.1")
        ]

        mock_audit_instance.get_logs_in_range.return_value = audit_data

        service = AuditService()

        # Test summary report generation
        success, message, report = service.generate_audit_report(
            start_date="2024-01-01",
            end_date="2024-01-31",
            report_type="summary"
        )

        assert success
        assert 'total_actions' in report
        assert 'admin_activity' in report
        assert 'action_breakdown' in report

    @patch('app.admin.services.audit_service.AuditRepository')
    def test_real_time_audit_alerts(self, mock_audit_repo):
        """Test real-time audit alerting"""
        service = AuditService()

        # Test high-risk action detection
        high_risk_action = AdminAction.create_user_action(
            admin_id="admin123",
            action_type="user_delete",
            user_id="user456",
            details={"reason": "Account termination"}
        )

        should_alert = service.should_trigger_real_time_alert(high_risk_action)
        assert should_alert

        # Test normal action (no alert)
        normal_action = AdminAction.create_user_action(
            admin_id="admin123",
            action_type="user_view",
            user_id="user456"
        )

        should_alert = service.should_trigger_real_time_alert(normal_action)
        assert not should_alert

    @patch('app.admin.services.audit_service.AuditRepository')
    def test_audit_search_functionality(self, mock_audit_repo):
        """Test audit log search capabilities"""
        # Setup mocks
        mock_audit_instance = MagicMock()
        mock_audit_repo.return_value = mock_audit_instance

        # Mock search results
        search_results = [
            AdminAction.create_user_action("admin1", "user_suspend", "user123"),
            AdminAction.create_user_action("admin2", "user_suspend", "user456")
        ]

        mock_audit_instance.search_logs.return_value = search_results

        service = AuditService()

        # Test text search
        success, message, results = service.search_audit_logs(
            query="user_suspend",
            search_fields=["action_type", "reason"]
        )

        assert success
        assert len(results) == 2
        assert all("user_suspend" in result.action_type for result in results)

    @patch('app.admin.services.audit_service.AuditRepository')
    def test_audit_export_functionality(self, mock_audit_repo):
        """Test audit log export in various formats"""
        # Setup mocks
        mock_audit_instance = MagicMock()
        mock_audit_repo.return_value = mock_audit_instance

        # Mock audit data for export
        export_data = [
            AdminAction.create_user_action("admin1", "user_suspend", "user123"),
            AdminAction.create_security_action("admin1", "login_success", "192.168.1.1")
        ]

        mock_audit_instance.get_logs_for_export.return_value = export_data

        service = AuditService()

        # Test CSV export
        success, message, csv_content = service.export_audit_logs(
            format="csv",
            date_range=("2024-01-01", "2024-01-31")
        )

        assert success
        assert csv_content is not None
        assert "admin_id" in csv_content
        assert "action_type" in csv_content

        # Test JSON export
        success, message, json_content = service.export_audit_logs(
            format="json",
            date_range=("2024-01-01", "2024-01-31")
        )

        assert success
        assert json_content is not None


if __name__ == '__main__':
    pytest.main([__file__])