import pytest
import os
import json
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

# Set testing environment before importing app modules
os.environ['TESTING'] = 'true'

from app import create_app
from app.admin.models.admin_user import AdminUser
from app.admin.models.system_metric import SystemMetric


class TestAdminAPIEndpoints:
    """Test admin API endpoints with Flask test client"""

    @pytest.fixture
    def app(self):
        """Create test app"""
        app = create_app()
        app.config['TESTING'] = True
        return app

    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return app.test_client()

    @pytest.fixture
    def admin_user(self):
        """Create test admin user"""
        admin = AdminUser(
            username="testadmin",
            email="test@admin.com",
            role="admin"
        )
        admin.set_password("SecurePass123!")
        return admin

    @patch('app.admin.services.admin_service.AdminService.authenticate_admin')
    def test_admin_login_endpoint(self, mock_auth, client):
        """Test admin login endpoint"""
        # Mock successful authentication
        mock_auth.return_value = (True, "ADMIN_LOGIN_SUCCESS", {
            "admin_id": "admin123",
            "username": "testadmin",
            "role": "admin",
            "permissions": ["user_management", "content_moderation"]
        })

        # Test login request
        response = client.post('/api/admin/auth/login',
                             json={
                                 "username": "testadmin",
                                 "password": "SecurePass123!"
                             })

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['message'] == "ADMIN_LOGIN_SUCCESS"
        assert 'data' in data

    @patch('app.admin.services.admin_service.AdminService.authenticate_admin')
    def test_admin_login_failed(self, mock_auth, client):
        """Test failed admin login"""
        # Mock failed authentication
        mock_auth.return_value = (False, "INVALID_CREDENTIALS", None)

        response = client.post('/api/admin/auth/login',
                             json={
                                 "username": "testadmin",
                                 "password": "wrongpassword"
                             })

        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['success'] is False
        assert data['message'] == "INVALID_CREDENTIALS"

    def test_admin_login_missing_data(self, client):
        """Test admin login with missing data"""
        response = client.post('/api/admin/auth/login', json={})

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert data['message'] == "DATA_REQUIRED"

    @patch('app.admin.services.dashboard_service.DashboardService.get_overview_dashboard')
    @patch('app.admin.utils.decorators.verify_admin_token')
    def test_dashboard_overview_endpoint(self, mock_verify, mock_dashboard, client):
        """Test dashboard overview endpoint"""
        # Mock admin verification
        mock_verify.return_value = AdminUser(username="admin", email="admin@test.com", role="admin")

        # Mock dashboard data
        mock_dashboard.return_value = (True, "DASHBOARD_OVERVIEW_SUCCESS", {
            "system_health": {"status": "healthy", "score": 95},
            "user_stats": {"total": 1500, "active": 1200},
            "performance_metrics": {"avg_response_time": 85.0}
        })

        # Add Authorization header
        headers = {'Authorization': 'Bearer valid_admin_token'}
        response = client.get('/api/admin/dashboard', headers=headers)

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['message'] == "DASHBOARD_OVERVIEW_SUCCESS"
        assert 'system_health' in data['data']

    @patch('app.admin.services.dashboard_service.DashboardService.get_user_management_dashboard')
    @patch('app.admin.utils.decorators.verify_admin_token')
    def test_user_management_dashboard_endpoint(self, mock_verify, mock_user_dashboard, client):
        """Test user management dashboard endpoint"""
        # Mock admin verification
        mock_verify.return_value = AdminUser(username="admin", email="admin@test.com", role="admin")

        # Mock user dashboard data
        mock_user_dashboard.return_value = (True, "USER_DASHBOARD_SUCCESS", {
            "user_counts": {"active": 1200, "inactive": 150, "suspended": 25},
            "registration_trends": [{"date": "2024-01-15", "count": 45}]
        })

        headers = {'Authorization': 'Bearer valid_admin_token'}
        response = client.get('/api/admin/dashboard/users', headers=headers)

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'user_counts' in data['data']

    @patch('app.admin.services.user_management_service.UserManagementService.suspend_user')
    @patch('app.admin.utils.decorators.verify_admin_token')
    def test_suspend_user_endpoint(self, mock_verify, mock_suspend, client):
        """Test user suspension endpoint"""
        # Mock admin verification with proper permissions
        admin = AdminUser(username="admin", email="admin@test.com", role="admin")
        mock_verify.return_value = admin

        # Mock user suspension
        mock_suspend.return_value = (True, "USER_SUSPENDED_SUCCESS", {
            "user_id": "user123",
            "status": "suspended"
        })

        headers = {'Authorization': 'Bearer valid_admin_token'}
        response = client.post('/api/admin/users/user123/suspend',
                              headers=headers,
                              json={"reason": "Policy violation"})

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['message'] == "USER_SUSPENDED_SUCCESS"

    @patch('app.admin.services.user_management_service.UserManagementService.suspend_user')
    @patch('app.admin.utils.decorators.verify_admin_token')
    def test_suspend_user_insufficient_permissions(self, mock_verify, mock_suspend, client):
        """Test user suspension with insufficient permissions"""
        # Mock admin verification with insufficient permissions (analyst role)
        admin = AdminUser(username="analyst", email="analyst@test.com", role="analyst")
        mock_verify.return_value = admin

        headers = {'Authorization': 'Bearer valid_admin_token'}
        response = client.post('/api/admin/users/user123/suspend',
                              headers=headers,
                              json={"reason": "Policy violation"})

        assert response.status_code == 403
        data = json.loads(response.data)
        assert data['success'] is False
        assert data['message'] == "INSUFFICIENT_PERMISSIONS"

    @patch('app.admin.services.user_management_service.UserManagementService.get_users_list')
    @patch('app.admin.utils.decorators.verify_admin_token')
    def test_get_users_list_endpoint(self, mock_verify, mock_get_users, client):
        """Test get users list endpoint"""
        # Mock admin verification
        mock_verify.return_value = AdminUser(username="admin", email="admin@test.com", role="admin")

        # Mock users list
        mock_get_users.return_value = (True, "USERS_RETRIEVED_SUCCESS", {
            "users": [
                {"id": "user1", "username": "john", "status": "active"},
                {"id": "user2", "username": "jane", "status": "inactive"}
            ],
            "pagination": {"page": 1, "total": 2}
        })

        headers = {'Authorization': 'Bearer valid_admin_token'}
        response = client.get('/api/admin/users?page=1&limit=10', headers=headers)

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'users' in data['data']
        assert len(data['data']['users']) == 2

    @patch('app.admin.services.user_management_service.UserManagementService.bulk_user_action')
    @patch('app.admin.utils.decorators.verify_admin_token')
    def test_bulk_user_actions_endpoint(self, mock_verify, mock_bulk_action, client):
        """Test bulk user actions endpoint"""
        # Mock admin verification
        mock_verify.return_value = AdminUser(username="admin", email="admin@test.com", role="admin")

        # Mock bulk action
        mock_bulk_action.return_value = (True, "BULK_ACTION_COMPLETED", {
            "processed": 5,
            "successful": 4,
            "failed": 1,
            "results": []
        })

        headers = {'Authorization': 'Bearer valid_admin_token'}
        response = client.post('/api/admin/users/bulk-action',
                              headers=headers,
                              json={
                                  "action": "suspend",
                                  "user_ids": ["user1", "user2", "user3"],
                                  "reason": "Bulk suspension"
                              })

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['message'] == "BULK_ACTION_COMPLETED"
        assert 'processed' in data['data']

    @patch('app.admin.services.monitoring_service.MonitoringService.get_system_metrics')
    @patch('app.admin.utils.decorators.verify_admin_token')
    def test_system_metrics_endpoint(self, mock_verify, mock_metrics, client):
        """Test system metrics endpoint"""
        # Mock admin verification
        mock_verify.return_value = AdminUser(username="admin", email="admin@test.com", role="admin")

        # Mock system metrics
        mock_metrics.return_value = (True, "METRICS_RETRIEVED_SUCCESS", {
            "current_metrics": {
                "cpu_usage": 75.0,
                "memory_usage": 68.0,
                "response_time_avg": 95.0
            },
            "historical_data": []
        })

        headers = {'Authorization': 'Bearer valid_admin_token'}
        response = client.get('/api/admin/monitoring/metrics', headers=headers)

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'current_metrics' in data['data']

    @patch('app.admin.services.security_service.SecurityService.get_security_alerts')
    @patch('app.admin.utils.decorators.verify_admin_token')
    def test_security_alerts_endpoint(self, mock_verify, mock_alerts, client):
        """Test security alerts endpoint"""
        # Mock admin verification
        mock_verify.return_value = AdminUser(username="admin", email="admin@test.com", role="admin")

        # Mock security alerts
        mock_alerts.return_value = (True, "ALERTS_RETRIEVED_SUCCESS", {
            "active_alerts": [
                {"id": "alert1", "type": "failed_login", "severity": "medium"},
                {"id": "alert2", "type": "suspicious_activity", "severity": "high"}
            ],
            "total_count": 2
        })

        headers = {'Authorization': 'Bearer valid_admin_token'}
        response = client.get('/api/admin/security/alerts', headers=headers)

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'active_alerts' in data['data']

    @patch('app.admin.services.security_service.SecurityService.acknowledge_alert')
    @patch('app.admin.utils.decorators.verify_admin_token')
    def test_acknowledge_alert_endpoint(self, mock_verify, mock_acknowledge, client):
        """Test alert acknowledgment endpoint"""
        # Mock admin verification
        mock_verify.return_value = AdminUser(username="admin", email="admin@test.com", role="admin")

        # Mock alert acknowledgment
        mock_acknowledge.return_value = (True, "ALERT_ACKNOWLEDGED_SUCCESS", {
            "alert_id": "alert123",
            "acknowledged_by": "admin",
            "acknowledged_at": datetime.now(timezone.utc).isoformat()
        })

        headers = {'Authorization': 'Bearer valid_admin_token'}
        response = client.post('/api/admin/security/alerts/alert123/acknowledge',
                              headers=headers,
                              json={"note": "Investigated and resolved"})

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['message'] == "ALERT_ACKNOWLEDGED_SUCCESS"

    def test_unauthorized_access(self, client):
        """Test unauthorized access to admin endpoints"""
        # Test without token
        response = client.get('/api/admin/dashboard')
        assert response.status_code == 401

        # Test with invalid token
        headers = {'Authorization': 'Bearer invalid_token'}
        response = client.get('/api/admin/dashboard', headers=headers)
        assert response.status_code == 401

    @patch('app.admin.services.audit_service.AuditService.get_audit_logs')
    @patch('app.admin.utils.decorators.verify_admin_token')
    def test_audit_logs_endpoint(self, mock_verify, mock_audit, client):
        """Test audit logs endpoint"""
        # Mock admin verification with audit permissions
        admin = AdminUser(username="superadmin", email="super@test.com", role="super_admin")
        mock_verify.return_value = admin

        # Mock audit logs
        mock_audit.return_value = (True, "AUDIT_LOGS_SUCCESS", {
            "logs": [
                {"id": "log1", "action": "user_suspend", "admin": "admin1"},
                {"id": "log2", "action": "user_activate", "admin": "admin2"}
            ],
            "pagination": {"page": 1, "total": 2}
        })

        headers = {'Authorization': 'Bearer valid_super_admin_token'}
        response = client.get('/api/admin/audit/logs', headers=headers)

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'logs' in data['data']

    @patch('app.admin.services.config_service.ConfigService.update_system_config')
    @patch('app.admin.utils.decorators.verify_admin_token')
    def test_system_config_endpoint(self, mock_verify, mock_config, client):
        """Test system configuration endpoint"""
        # Mock super admin verification
        admin = AdminUser(username="superadmin", email="super@test.com", role="super_admin")
        mock_verify.return_value = admin

        # Mock config update
        mock_config.return_value = (True, "CONFIG_UPDATED_SUCCESS", {
            "updated_keys": ["max_login_attempts", "session_timeout"],
            "config": {"max_login_attempts": 5, "session_timeout": 3600}
        })

        headers = {'Authorization': 'Bearer valid_super_admin_token'}
        response = client.put('/api/admin/system/config',
                             headers=headers,
                             json={
                                 "max_login_attempts": 5,
                                 "session_timeout": 3600
                             })

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['message'] == "CONFIG_UPDATED_SUCCESS"

    @patch('app.admin.services.export_service.ExportService.export_dashboard_data')
    @patch('app.admin.utils.decorators.verify_admin_token')
    def test_dashboard_export_endpoint(self, mock_verify, mock_export, client):
        """Test dashboard data export endpoint"""
        # Mock admin verification
        mock_verify.return_value = AdminUser(username="admin", email="admin@test.com", role="admin")

        # Mock export data
        mock_export.return_value = (True, "EXPORT_SUCCESS", {
            "file_url": "/exports/dashboard_2024-01-15.csv",
            "format": "csv",
            "size": "2.5MB"
        })

        headers = {'Authorization': 'Bearer valid_admin_token'}
        response = client.post('/api/admin/dashboard/export',
                              headers=headers,
                              json={
                                  "format": "csv",
                                  "data_type": "overview",
                                  "date_range": "last_30_days"
                              })

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['message'] == "EXPORT_SUCCESS"
        assert 'file_url' in data['data']


class TestAdminAPIValidation:
    """Test API input validation and error handling"""

    @pytest.fixture
    def app(self):
        """Create test app"""
        app = create_app()
        app.config['TESTING'] = True
        return app

    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return app.test_client()

    def test_invalid_json_payload(self, client):
        """Test handling of invalid JSON payloads"""
        response = client.post('/api/admin/auth/login',
                              data="invalid json",
                              content_type='application/json')

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'INVALID_JSON' in data['message'] or 'DATA_REQUIRED' in data['message']

    def test_missing_required_fields(self, client):
        """Test validation of required fields"""
        # Login without username
        response = client.post('/api/admin/auth/login',
                              json={"password": "test123"})

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False

        # Login without password
        response = client.post('/api/admin/auth/login',
                              json={"username": "testuser"})

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False

    @patch('app.admin.utils.decorators.verify_admin_token')
    def test_pagination_validation(self, mock_verify, client):
        """Test pagination parameter validation"""
        # Mock admin verification
        mock_verify.return_value = AdminUser(username="admin", email="admin@test.com", role="admin")

        headers = {'Authorization': 'Bearer valid_admin_token'}

        # Test invalid page number
        response = client.get('/api/admin/users?page=-1', headers=headers)
        # Should handle gracefully or return error

        # Test invalid limit
        response = client.get('/api/admin/users?limit=0', headers=headers)
        # Should handle gracefully or return error

        # Test excessively large limit
        response = client.get('/api/admin/users?limit=10000', headers=headers)
        # Should cap at maximum allowed limit

    def test_sql_injection_protection(self, client):
        """Test protection against SQL injection attempts"""
        # Test malicious input in login
        response = client.post('/api/admin/auth/login',
                              json={
                                  "username": "admin'; DROP TABLE users; --",
                                  "password": "password"
                              })

        # Should not cause server error
        assert response.status_code in [400, 401]  # Bad request or unauthorized

    def test_xss_protection(self, client):
        """Test protection against XSS attempts"""
        # Test script injection in input fields
        xss_payload = "<script>alert('xss')</script>"

        response = client.post('/api/admin/auth/login',
                              json={
                                  "username": xss_payload,
                                  "password": "password"
                              })

        # Should handle malicious input safely
        assert response.status_code in [400, 401]


if __name__ == '__main__':
    pytest.main([__file__])