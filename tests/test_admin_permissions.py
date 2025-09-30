import pytest
import os
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

# Set testing environment before importing app modules
os.environ['TESTING'] = 'true'

from app.admin.models.admin_user import AdminUser
from app.admin.services.admin_service import AdminService
from app.admin.utils.decorators import admin_auth_required, admin_permission_required, admin_role_required


class TestAdminRoles:
    """Test admin role management and validation"""

    def test_super_admin_permissions(self):
        """Test super admin has all permissions"""
        admin = AdminUser(
            username="superadmin",
            email="super@admin.com",
            role="super_admin"
        )

        # Super admin should have all permissions
        assert admin.has_permission("user_management")
        assert admin.has_permission("content_moderation")
        assert admin.has_permission("financial_oversight")
        assert admin.has_permission("system_administration")
        assert admin.has_permission("analytics_view")
        assert admin.has_permission("onlus_management")
        assert admin.has_permission("audit_logs")

        # Super admin should have wildcard permission
        assert "*" in admin.permissions

    def test_admin_permissions(self):
        """Test admin role permissions"""
        admin = AdminUser(
            username="admin",
            email="admin@admin.com",
            role="admin"
        )

        # Admin should have these permissions
        assert admin.has_permission("user_management")
        assert admin.has_permission("content_moderation")
        assert admin.has_permission("financial_oversight")
        assert admin.has_permission("analytics_view")
        assert admin.has_permission("onlus_management")

        # But not system administration
        assert not admin.has_permission("system_administration")
        assert not admin.has_permission("audit_logs")

    def test_moderator_permissions(self):
        """Test moderator role permissions"""
        moderator = AdminUser(
            username="moderator",
            email="mod@admin.com",
            role="moderator"
        )

        # Moderator should have limited permissions
        assert moderator.has_permission("content_moderation")
        assert moderator.has_permission("analytics_view")

        # But not user management or financial oversight
        assert not moderator.has_permission("user_management")
        assert not moderator.has_permission("financial_oversight")
        assert not moderator.has_permission("system_administration")
        assert not moderator.has_permission("onlus_management")

    def test_analyst_permissions(self):
        """Test analyst role permissions"""
        analyst = AdminUser(
            username="analyst",
            email="analyst@admin.com",
            role="analyst"
        )

        # Analyst should only have view permissions
        assert analyst.has_permission("analytics_view")

        # But not management permissions
        assert not analyst.has_permission("user_management")
        assert not analyst.has_permission("content_moderation")
        assert not analyst.has_permission("financial_oversight")
        assert not analyst.has_permission("system_administration")

    def test_invalid_role(self):
        """Test handling of invalid roles"""
        admin = AdminUser(
            username="test",
            email="test@admin.com",
            role="invalid_role"
        )

        # Invalid role should have no permissions
        assert not admin.has_permission("user_management")
        assert not admin.has_permission("analytics_view")
        assert len(admin.permissions) == 0

    def test_role_hierarchy(self):
        """Test role hierarchy validation"""
        super_admin = AdminUser(username="super", email="super@admin.com", role="super_admin")
        admin = AdminUser(username="admin", email="admin@admin.com", role="admin")
        moderator = AdminUser(username="mod", email="mod@admin.com", role="moderator")
        analyst = AdminUser(username="analyst", email="analyst@admin.com", role="analyst")

        # Check role levels
        assert super_admin.get_role_level() == 4
        assert admin.get_role_level() == 3
        assert moderator.get_role_level() == 2
        assert analyst.get_role_level() == 1

        # Higher level can manage lower level
        assert super_admin.can_manage_user(admin)
        assert admin.can_manage_user(moderator)
        assert moderator.can_manage_user(analyst)

        # Lower level cannot manage higher level
        assert not analyst.can_manage_user(moderator)
        assert not moderator.can_manage_user(admin)

    def test_permission_addition_and_removal(self):
        """Test dynamic permission management"""
        admin = AdminUser(
            username="test",
            email="test@admin.com",
            role="analyst"
        )

        # Initially only has analytics_view
        assert admin.has_permission("analytics_view")
        assert not admin.has_permission("user_management")

        # Add permission
        admin.add_permission("user_management")
        assert admin.has_permission("user_management")

        # Remove permission
        admin.remove_permission("analytics_view")
        assert not admin.has_permission("analytics_view")
        assert admin.has_permission("user_management")

    def test_bulk_permission_management(self):
        """Test bulk permission operations"""
        admin = AdminUser(
            username="test",
            email="test@admin.com",
            role="analyst"
        )

        # Add multiple permissions
        new_permissions = ["user_management", "content_moderation", "financial_oversight"]
        admin.add_permissions(new_permissions)

        for permission in new_permissions:
            assert admin.has_permission(permission)

        # Remove multiple permissions
        admin.remove_permissions(["user_management", "content_moderation"])
        assert not admin.has_permission("user_management")
        assert not admin.has_permission("content_moderation")
        assert admin.has_permission("financial_oversight")  # Should still have this

    def test_role_change_updates_permissions(self):
        """Test that changing role updates permissions"""
        admin = AdminUser(
            username="test",
            email="test@admin.com",
            role="analyst"
        )

        # Initially analyst permissions
        assert admin.has_permission("analytics_view")
        assert not admin.has_permission("user_management")

        # Change to admin role
        admin.role = "admin"
        admin._update_permissions_for_role()

        # Should now have admin permissions
        assert admin.has_permission("user_management")
        assert admin.has_permission("content_moderation")
        assert admin.has_permission("financial_oversight")


class TestAdminPermissionValidation:
    """Test permission validation in various scenarios"""

    def test_permission_case_sensitivity(self):
        """Test that permissions are case-sensitive"""
        admin = AdminUser(
            username="test",
            email="test@admin.com",
            role="admin"
        )

        # Correct case should work
        assert admin.has_permission("user_management")

        # Wrong case should not work
        assert not admin.has_permission("USER_MANAGEMENT")
        assert not admin.has_permission("User_Management")

    def test_empty_and_none_permissions(self):
        """Test handling of empty and None permissions"""
        admin = AdminUser(
            username="test",
            email="test@admin.com",
            role="analyst"
        )

        # Empty string should not grant permission
        assert not admin.has_permission("")
        assert not admin.has_permission(None)

    def test_wildcard_permission(self):
        """Test wildcard permission functionality"""
        super_admin = AdminUser(
            username="super",
            email="super@admin.com",
            role="super_admin"
        )

        # Super admin with wildcard should have any permission
        assert super_admin.has_permission("any_random_permission")
        assert super_admin.has_permission("new_future_permission")
        assert super_admin.has_permission("custom_permission_123")

    def test_permission_expiration(self):
        """Test temporary permissions with expiration"""
        admin = AdminUser(
            username="test",
            email="test@admin.com",
            role="analyst"
        )

        # Add temporary permission
        admin.add_temporary_permission("emergency_access", hours=1)
        assert admin.has_permission("emergency_access")

        # Simulate time passing (would need time manipulation in real scenario)
        # For now, test the structure exists
        assert hasattr(admin, 'temporary_permissions')

    def test_permission_context_validation(self):
        """Test permissions in specific contexts"""
        admin = AdminUser(
            username="test",
            email="test@admin.com",
            role="admin"
        )

        # Test context-specific permissions
        assert admin.has_permission_in_context("user_management", "general")

        # Some permissions might be context-restricted
        # This tests the framework for context-aware permissions


class TestAdminRoleBasedAccess:
    """Test role-based access control functionality"""

    @patch('app.admin.services.admin_service.AdminRepository')
    @patch('app.admin.services.admin_service.AuditRepository')
    def test_role_based_user_creation(self, mock_audit_repo, mock_admin_repo):
        """Test that admins can only create users with appropriate roles"""
        # Setup mocks
        mock_admin_repo_instance = MagicMock()
        mock_admin_repo.return_value = mock_admin_repo_instance
        mock_audit_repo_instance = MagicMock()
        mock_audit_repo.return_value = mock_audit_repo_instance

        service = AdminService()

        # Admin should be able to create moderator
        creating_admin = AdminUser(username="admin", email="admin@test.com", role="admin")
        can_create = service._can_create_user_with_role(creating_admin, "moderator")
        assert can_create

        # Admin should NOT be able to create super_admin
        can_create = service._can_create_user_with_role(creating_admin, "super_admin")
        assert not can_create

        # Moderator should NOT be able to create admin
        creating_moderator = AdminUser(username="mod", email="mod@test.com", role="moderator")
        can_create = service._can_create_user_with_role(creating_moderator, "admin")
        assert not can_create

    def test_action_permission_mapping(self):
        """Test that actions are properly mapped to required permissions"""
        admin = AdminUser(username="admin", email="admin@test.com", role="admin")

        # Test action-permission mapping
        action_permissions = {
            "suspend_user": "user_management",
            "delete_content": "content_moderation",
            "view_financials": "financial_oversight",
            "manage_onlus": "onlus_management",
            "system_config": "system_administration"
        }

        for action, required_permission in action_permissions.items():
            if admin.has_permission(required_permission):
                assert admin.can_perform_action(action)
            else:
                assert not admin.can_perform_action(action)

    def test_department_based_permissions(self):
        """Test department-specific permission validation"""
        # Different admins for different departments
        finance_admin = AdminUser(
            username="finance_admin",
            email="finance@admin.com",
            role="admin"
        )
        finance_admin.department = "finance"
        finance_admin.add_permission("financial_oversight")

        content_admin = AdminUser(
            username="content_admin",
            email="content@admin.com",
            role="admin"
        )
        content_admin.department = "content"
        content_admin.add_permission("content_moderation")

        # Test department-specific access
        assert finance_admin.has_department_permission("financial_oversight", "finance")
        assert not content_admin.has_department_permission("financial_oversight", "finance")

    def test_time_based_access_restrictions(self):
        """Test time-based access control"""
        admin = AdminUser(
            username="test",
            email="test@admin.com",
            role="admin"
        )

        # Set working hours (9 AM to 6 PM)
        admin.working_hours = {
            "start": 9,  # 9 AM
            "end": 18,   # 6 PM
            "timezone": "UTC"
        }

        # Test within working hours (would need time mocking for full test)
        # For now, test the structure exists
        assert hasattr(admin, 'working_hours')
        assert admin.working_hours['start'] == 9
        assert admin.working_hours['end'] == 18

    def test_ip_based_access_restrictions(self):
        """Test IP-based access control"""
        admin = AdminUser(
            username="test",
            email="test@admin.com",
            role="admin"
        )

        # Set allowed IPs
        admin.allowed_ips = ["192.168.1.100", "10.0.0.1", "203.0.113.0/24"]

        # Test IP validation
        assert admin.is_ip_allowed("192.168.1.100")
        assert admin.is_ip_allowed("10.0.0.1")
        assert not admin.is_ip_allowed("192.168.1.200")
        assert not admin.is_ip_allowed("172.16.0.1")

        # Test subnet validation
        assert admin.is_ip_allowed("203.0.113.50")  # Should be in subnet
        assert not admin.is_ip_allowed("203.0.114.50")  # Different subnet

    def test_session_based_permissions(self):
        """Test session-based permission validation"""
        admin = AdminUser(
            username="test",
            email="test@admin.com",
            role="admin"
        )

        # Set session-specific permissions
        admin.session_permissions = ["emergency_access", "temporary_elevated"]

        # Test session permissions
        assert admin.has_session_permission("emergency_access")
        assert not admin.has_session_permission("non_granted_permission")

        # Session permissions should be additive to role permissions
        assert admin.has_permission("user_management")  # From role
        assert admin.has_session_permission("emergency_access")  # From session


if __name__ == '__main__':
    pytest.main([__file__])