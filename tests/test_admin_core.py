import pytest
import os
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta

# Set testing environment before importing app modules
os.environ['TESTING'] = 'true'

from app import create_app
from app.admin.models.admin_user import AdminUser
from app.admin.models.admin_action import AdminAction, ActionType
from app.admin.models.system_metric import SystemMetric, MetricType
from app.admin.services.admin_service import AdminService


@pytest.fixture(scope="function")
def app():
    """Create and configure a test app for each test function"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret-key'
    app.config['JWT_SECRET_KEY'] = 'test-jwt-secret'
    return app


class TestAdminModels:
    """Test admin models functionality"""

    def test_admin_user_creation(self):
        """Test AdminUser model creation"""
        admin = AdminUser(
            username="testadmin",
            email="test@admin.com",
            role="admin"
        )

        assert admin.username == "testadmin"
        assert admin.email == "test@admin.com"
        assert admin.role == "admin"
        assert admin.is_active is True
        assert "user_management" in admin.permissions

    def test_admin_user_password_management(self):
        """Test password setting and checking"""
        admin = AdminUser(username="test", email="test@admin.com")
        admin.set_password("SecurePassword123!")

        assert admin.password_hash is not None
        assert admin.check_password("SecurePassword123!")
        assert not admin.check_password("WrongPassword")

    def test_admin_user_permissions(self):
        """Test permission management"""
        admin = AdminUser(username="test", email="test@admin.com", role="moderator")

        assert admin.has_permission("content_moderation")
        assert not admin.has_permission("financial_oversight")

        admin.add_permission("analytics_view")
        assert admin.has_permission("analytics_view")

    def test_admin_user_role_hierarchy(self):
        """Test role hierarchy"""
        super_admin = AdminUser(username="super", email="super@admin.com", role="super_admin")
        admin = AdminUser(username="admin", email="admin@admin.com", role="admin")
        moderator = AdminUser(username="mod", email="mod@admin.com", role="moderator")

        assert super_admin.get_role_level() > admin.get_role_level()
        assert admin.get_role_level() > moderator.get_role_level()
        assert super_admin.can_manage_user(admin)
        assert not moderator.can_manage_user(admin)

    def test_admin_action_creation(self):
        """Test AdminAction model creation"""
        action = AdminAction.create_user_action(
            admin_id="admin123",
            action_type=ActionType.USER_SUSPEND.value,
            user_id="user456",
            reason="Policy violation"
        )

        assert action.admin_id == "admin123"
        assert action.action_type == ActionType.USER_SUSPEND.value
        assert action.target_id == "user456"
        assert action.reason == "Policy violation"

    def test_admin_action_risk_assessment(self):
        """Test action risk level assessment"""
        high_risk_action = AdminAction.create_user_action(
            admin_id="admin123",
            action_type=ActionType.USER_DELETE.value,
            user_id="user456"
        )

        medium_risk_action = AdminAction.create_user_action(
            admin_id="admin123",
            action_type=ActionType.USER_SUSPEND.value,
            user_id="user456"
        )

        assert high_risk_action.get_risk_level() == "high"
        assert medium_risk_action.get_risk_level() == "medium"
        assert high_risk_action.is_sensitive_action()

    def test_system_metric_creation(self):
        """Test SystemMetric model creation"""
        metric = SystemMetric.create_performance_metric(
            cpu_usage=75.5,
            memory_usage=68.2,
            response_time_avg=150.0,
            error_rate=0.5,
            active_sessions=100
        )

        assert metric.metric_type == MetricType.PERFORMANCE.value
        assert metric.get_value('cpu_usage') == 75.5
        assert metric.get_value('memory_usage') == 68.2

    def test_system_metric_alert_detection(self):
        """Test alert detection in metrics"""
        # Create metric with high CPU usage
        metric = SystemMetric.create_performance_metric(
            cpu_usage=95.0,  # High CPU
            memory_usage=60.0,
            response_time_avg=150.0,
            error_rate=0.5,
            active_sessions=100
        )

        assert metric.is_alert_worthy()
        assert "High CPU usage" in metric.get_alert_message()


class TestAdminSerialization:
    """Test serialization/deserialization of admin models"""

    def test_admin_user_serialization(self):
        """Test admin user to_dict and from_dict"""
        original_admin = AdminUser(
            username="testadmin",
            email="test@admin.com",
            role="admin"
        )
        original_admin.set_password("SecurePass123!")

        # Convert to dict
        admin_dict = original_admin.to_dict()
        assert 'username' in admin_dict
        assert 'email' in admin_dict
        assert 'role' in admin_dict

        # Convert back from dict
        restored_admin = AdminUser.from_dict(admin_dict)
        assert restored_admin.username == original_admin.username
        assert restored_admin.email == original_admin.email
        assert restored_admin.role == original_admin.role

    def test_admin_action_serialization(self):
        """Test admin action to_dict and from_dict"""
        original_action = AdminAction.create_user_action(
            admin_id="admin123",
            action_type=ActionType.USER_SUSPEND.value,
            user_id="user456",
            reason="Test suspension"
        )

        # Convert to dict
        action_dict = original_action.to_dict()
        assert 'admin_id' in action_dict
        assert 'action_type' in action_dict
        assert 'target_type' in action_dict

        # Convert back from dict
        restored_action = AdminAction.from_dict(action_dict)
        assert restored_action.admin_id == original_action.admin_id
        assert restored_action.action_type == original_action.action_type
        assert restored_action.target_id == original_action.target_id


class TestAdminService:
    """Test admin service basic functionality"""

    @patch('app.admin.services.admin_service.AdminRepository')
    @patch('app.admin.services.admin_service.AuditRepository')
    def test_admin_service_initialization(self, mock_audit_repo, mock_admin_repo, app):
        """Test AdminService initialization"""
        with app.app_context():
            service = AdminService()
            assert service.admin_repository is not None
            assert service.audit_repository is not None

    def test_password_validation(self, app):
        """Test password validation logic"""
        with app.app_context():
            service = AdminService()

            # Valid password
            assert service._validate_password("SecurePass123!")

            # Invalid passwords
            assert not service._validate_password("short")  # Too short
            assert not service._validate_password("nouppercase123!")  # No uppercase
            assert not service._validate_password("NOLOWERCASE123!")  # No lowercase
            assert not service._validate_password("NoNumbers!")  # No numbers
            assert not service._validate_password("NoSpecialChars123")  # No special chars

    @patch('app.admin.services.admin_service.AdminRepository')
    @patch('app.admin.services.admin_service.AuditRepository')
    def test_can_create_user_with_role(self, mock_audit_repo, mock_admin_repo, app):
        """Test role-based user creation permissions"""
        with app.app_context():
            service = AdminService()

            # Super admin can create any role
            super_admin = AdminUser(username="super", email="super@test.com", role="super_admin")
            assert service._can_create_user_with_role(super_admin, "admin")
            assert service._can_create_user_with_role(super_admin, "moderator")

            # Admin can create moderator and analyst
            admin = AdminUser(username="admin", email="admin@test.com", role="admin")
            assert service._can_create_user_with_role(admin, "moderator")
            assert service._can_create_user_with_role(admin, "analyst")
            assert not service._can_create_user_with_role(admin, "super_admin")

            # Moderator cannot create other admins
            moderator = AdminUser(username="mod", email="mod@test.com", role="moderator")
            assert not service._can_create_user_with_role(moderator, "admin")

    def test_session_expiry_check(self, app):
        """Test session expiry validation"""
        with app.app_context():
            service = AdminService()

            # Create admin with old last activity
            admin = AdminUser(username="test", email="test@admin.com", role="admin")
            admin.last_activity = datetime.now(timezone.utc) - timedelta(hours=2)
            admin.session_timeout_minutes = 60  # 1 hour timeout

            # Session should be expired
            assert service._is_session_expired(admin)

            # Recent activity should not be expired
            admin.last_activity = datetime.now(timezone.utc) - timedelta(minutes=30)
            assert not service._is_session_expired(admin)


class TestAdminSecurity:
    """Test admin security features"""

    def test_password_strength_validation(self):
        """Test password strength requirements"""
        admin = AdminUser(username="test", email="test@admin.com")

        # Strong password should work
        admin.set_password("StrongPassword123!")
        assert admin.check_password("StrongPassword123!")

        # Different passwords should have different hashes
        admin1 = AdminUser(username="test1", email="test1@admin.com")
        admin2 = AdminUser(username="test2", email="test2@admin.com")

        same_password = "SamePassword123!"
        admin1.set_password(same_password)
        admin2.set_password(same_password)

        # Even with same password, hashes should be different due to salt
        assert admin1.password_hash != admin2.password_hash

    def test_ip_validation(self):
        """Test IP address validation"""
        admin = AdminUser(username="test", email="test@admin.com", role="admin")
        admin.allowed_ips = ["192.168.1.100", "10.0.0.1", "203.0.113.0/24"]

        # Test exact IP matches
        assert admin.is_ip_allowed("192.168.1.100")
        assert admin.is_ip_allowed("10.0.0.1")

        # Test subnet validation
        assert admin.is_ip_allowed("203.0.113.50")  # Should be in subnet

        # Test disallowed IPs
        assert not admin.is_ip_allowed("192.168.1.200")
        assert not admin.is_ip_allowed("172.16.0.1")

    def test_role_based_permissions(self):
        """Test role-based permission system"""
        # Super admin should have all permissions
        super_admin = AdminUser(username="super", email="super@admin.com", role="super_admin")
        assert super_admin.has_permission("any_permission")  # Wildcard permission

        # Admin should have management permissions
        admin = AdminUser(username="admin", email="admin@admin.com", role="admin")
        assert admin.has_permission("user_management")
        assert admin.has_permission("content_moderation")

        # Moderator should have limited permissions
        moderator = AdminUser(username="mod", email="mod@admin.com", role="moderator")
        assert moderator.has_permission("content_moderation")
        assert not moderator.has_permission("user_management")

        # Analyst should only have view permissions
        analyst = AdminUser(username="analyst", email="analyst@admin.com", role="analyst")
        assert analyst.has_permission("analytics_view")
        assert not analyst.has_permission("content_moderation")


if __name__ == '__main__':
    pytest.main([__file__])