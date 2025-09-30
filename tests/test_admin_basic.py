import pytest
import os
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

# Set testing environment before importing app modules
os.environ['TESTING'] = 'true'

from app.admin.models.admin_user import AdminUser
from app.admin.models.system_metric import SystemMetric, MetricType
from app.admin.models.admin_action import AdminAction, ActionType, TargetType
from app.admin.repositories.admin_repository import AdminRepository
from app.admin.repositories.metrics_repository import MetricsRepository
from app.admin.repositories.audit_repository import AuditRepository
from app.admin.services.admin_service import AdminService

class TestAdminModels:
    """Test admin models"""

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
        assert action.target_type == TargetType.USER.value
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


class TestAdminRepositories:
    """Test admin repositories with mocked database"""

    @patch('app.get_db')
    def test_admin_repository_initialization(self, mock_get_db):
        """Test AdminRepository initialization"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        repo = AdminRepository()
        assert repo.collection_name == "admin_users"

    @patch('app.get_db')
    def test_metrics_repository_initialization(self, mock_get_db):
        """Test MetricsRepository initialization"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        repo = MetricsRepository()
        assert repo.collection_name == "system_metrics"

    @patch('app.get_db')
    def test_audit_repository_initialization(self, mock_get_db):
        """Test AuditRepository initialization"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        repo = AuditRepository()
        assert repo.collection_name == "admin_actions"


class TestAdminServices:
    """Test admin services with mocked dependencies"""

    @patch('app.admin.services.admin_service.AdminRepository')
    @patch('app.admin.services.admin_service.AuditRepository')
    def test_admin_service_initialization(self, mock_audit_repo, mock_admin_repo):
        """Test AdminService initialization"""
        service = AdminService()
        assert service.admin_repository is not None
        assert service.audit_repository is not None

    @patch('app.admin.services.admin_service.AdminRepository')
    @patch('app.admin.services.admin_service.AuditRepository')
    def test_admin_authentication_validation(self, mock_audit_repo, mock_admin_repo):
        """Test admin authentication input validation"""
        # Mock repository
        mock_admin_repo_instance = MagicMock()
        mock_admin_repo.return_value = mock_admin_repo_instance
        mock_admin_repo_instance.find_by_username.return_value = None
        mock_admin_repo_instance.find_by_email.return_value = None

        mock_audit_repo_instance = MagicMock()
        mock_audit_repo.return_value = mock_audit_repo_instance

        service = AdminService()

        # Test with invalid credentials (non-existent user)
        success, message, result = service.authenticate_admin("nonexistent", "password")
        assert not success
        assert message == "INVALID_CREDENTIALS"

    def test_password_validation(self):
        """Test password validation logic"""
        service = AdminService()

        # Valid password
        assert service._validate_password("SecurePass123!")

        # Invalid passwords
        assert not service._validate_password("short")  # Too short
        assert not service._validate_password("nouppercase123!")  # No uppercase
        assert not service._validate_password("NOLOWERCASE123!")  # No lowercase
        assert not service._validate_password("NoNumbers!")  # No numbers
        assert not service._validate_password("NoSpecialChars123")  # No special chars


class TestAdminIntegration:
    """Integration tests for admin module"""

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

    def test_system_metric_serialization(self):
        """Test system metric to_dict and from_dict"""
        original_metric = SystemMetric.create_performance_metric(
            cpu_usage=75.0,
            memory_usage=68.0,
            response_time_avg=150.0,
            error_rate=0.5,
            active_sessions=100
        )

        # Convert to dict
        metric_dict = original_metric.to_dict()
        assert 'metric_type' in metric_dict
        assert 'data' in metric_dict
        assert 'timestamp' in metric_dict

        # Convert back from dict
        restored_metric = SystemMetric.from_dict(metric_dict)
        assert restored_metric.metric_type == original_metric.metric_type
        assert restored_metric.get_value('cpu_usage') == original_metric.get_value('cpu_usage')

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


if __name__ == '__main__':
    pytest.main([__file__])