import pytest
import os
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta
import bcrypt

# Set testing environment before importing app modules
os.environ['TESTING'] = 'true'

from app import create_app
from app.admin.models.admin_user import AdminUser
from app.admin.services.admin_service import AdminService
from app.admin.repositories.admin_repository import AdminRepository
from app.admin.repositories.audit_repository import AuditRepository

@pytest.fixture(scope="function")
def app():
    """Create and configure a test app for each test function"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret-key'
    app.config['JWT_SECRET_KEY'] = 'test-jwt-secret'
    return app


class TestAdminAuthentication:
    """Comprehensive admin authentication tests"""

    @patch('app.admin.services.admin_service.AdminRepository')
    @patch('app.admin.services.admin_service.AuditRepository')
    def test_successful_admin_login(self, mock_audit_repo, mock_admin_repo, app):
        """Test successful admin authentication"""
        # Setup mocks
        mock_admin_repo_instance = MagicMock()
        mock_admin_repo.return_value = mock_admin_repo_instance

        # Create admin user with valid credentials
        admin_user = AdminUser(
            username="testadmin",
            email="test@admin.com",
            role="admin"
        )
        admin_user.set_password("SecurePass123!")
        admin_user.is_active = True
        admin_user.is_locked = False
        admin_user.failed_login_attempts = 0

        mock_admin_repo_instance.find_by_username.return_value = admin_user
        mock_audit_repo_instance = MagicMock()
        mock_audit_repo.return_value = mock_audit_repo_instance

        with app.app_context():
            service = AdminService()

            # Test successful authentication
            success, message, result = service.authenticate_admin(
                "testadmin",
                "SecurePass123!",
                "192.168.1.1"
            )

        assert success
        assert message == "ADMIN_LOGIN_SUCCESS"
        assert result is not None
        assert "admin_id" in result
        assert "role" in result
        assert "permissions" in result

    @patch('app.admin.services.admin_service.AdminRepository')
    @patch('app.admin.services.admin_service.AuditRepository')
    def test_failed_admin_login_wrong_password(self, mock_audit_repo, mock_admin_repo):
        """Test failed authentication with wrong password"""
        mock_admin_repo_instance = MagicMock()
        mock_admin_repo.return_value = mock_admin_repo_instance

        admin_user = AdminUser(
            username="testadmin",
            email="test@admin.com",
            role="admin"
        )
        admin_user.set_password("SecurePass123!")
        admin_user.is_active = True
        admin_user.is_locked = False

        mock_admin_repo_instance.find_by_username.return_value = admin_user
        mock_audit_repo_instance = MagicMock()
        mock_audit_repo.return_value = mock_audit_repo_instance

        service = AdminService()

        # Test failed authentication
        success, message, result = service.authenticate_admin(
            "testadmin",
            "WrongPassword",
            "192.168.1.1"
        )

        assert not success
        assert message == "INVALID_CREDENTIALS"
        assert result is None

    @patch('app.admin.services.admin_service.AdminRepository')
    @patch('app.admin.services.admin_service.AuditRepository')
    def test_admin_login_inactive_user(self, mock_audit_repo, mock_admin_repo):
        """Test authentication with inactive admin user"""
        mock_admin_repo_instance = MagicMock()
        mock_admin_repo.return_value = mock_admin_repo_instance

        admin_user = AdminUser(
            username="testadmin",
            email="test@admin.com",
            role="admin"
        )
        admin_user.set_password("SecurePass123!")
        admin_user.is_active = False  # Inactive user

        mock_admin_repo_instance.find_by_username.return_value = admin_user
        mock_audit_repo_instance = MagicMock()
        mock_audit_repo.return_value = mock_audit_repo_instance

        service = AdminService()

        success, message, result = service.authenticate_admin(
            "testadmin",
            "SecurePass123!",
            "192.168.1.1"
        )

        assert not success
        assert message == "ADMIN_ACCOUNT_DISABLED"
        assert result is None

    @patch('app.admin.services.admin_service.AdminRepository')
    @patch('app.admin.services.admin_service.AuditRepository')
    def test_admin_login_locked_user(self, mock_audit_repo, mock_admin_repo):
        """Test authentication with locked admin user"""
        mock_admin_repo_instance = MagicMock()
        mock_admin_repo.return_value = mock_admin_repo_instance

        admin_user = AdminUser(
            username="testadmin",
            email="test@admin.com",
            role="admin"
        )
        admin_user.set_password("SecurePass123!")
        admin_user.is_active = True
        admin_user.is_locked = True  # Locked user
        admin_user.locked_until = datetime.now(timezone.utc) + timedelta(hours=1)

        mock_admin_repo_instance.find_by_username.return_value = admin_user
        mock_audit_repo_instance = MagicMock()
        mock_audit_repo.return_value = mock_audit_repo_instance

        service = AdminService()

        success, message, result = service.authenticate_admin(
            "testadmin",
            "SecurePass123!",
            "192.168.1.1"
        )

        assert not success
        assert message == "ADMIN_ACCOUNT_LOCKED"
        assert result is None

    @patch('app.admin.services.admin_service.AdminRepository')
    @patch('app.admin.services.admin_service.AuditRepository')
    def test_admin_login_nonexistent_user(self, mock_audit_repo, mock_admin_repo):
        """Test authentication with non-existent user"""
        mock_admin_repo_instance = MagicMock()
        mock_admin_repo.return_value = mock_admin_repo_instance
        mock_admin_repo_instance.find_by_username.return_value = None

        mock_audit_repo_instance = MagicMock()
        mock_audit_repo.return_value = mock_audit_repo_instance

        service = AdminService()

        success, message, result = service.authenticate_admin(
            "nonexistent",
            "password",
            "192.168.1.1"
        )

        assert not success
        assert message == "ADMIN_ACCOUNT_LOCKED"
        assert result is None

    @patch('app.admin.services.admin_service.AdminRepository')
    @patch('app.admin.services.admin_service.AuditRepository')
    def test_admin_login_ip_whitelist_validation(self, mock_audit_repo, mock_admin_repo):
        """Test IP whitelist validation during authentication"""
        mock_admin_repo_instance = MagicMock()
        mock_admin_repo.return_value = mock_admin_repo_instance

        admin_user = AdminUser(
            username="testadmin",
            email="test@admin.com",
            role="admin"
        )
        admin_user.set_password("SecurePass123!")
        admin_user.is_active = True
        admin_user.is_locked = False
        admin_user.allowed_ips = ["192.168.1.100", "10.0.0.1"]  # Specific IPs allowed

        mock_admin_repo_instance.find_by_username.return_value = admin_user
        mock_audit_repo_instance = MagicMock()
        mock_audit_repo.return_value = mock_audit_repo_instance

        service = AdminService()

        # Test with disallowed IP
        success, message, result = service.authenticate_admin(
            "testadmin",
            "SecurePass123!",
            "192.168.1.50"  # Not in whitelist
        )

        assert not success
        assert message == "IP_NOT_ALLOWED"
        assert result is None

    def test_password_strength_validation(self):
        """Test comprehensive password strength validation"""
        service = AdminService()

        # Test valid passwords
        valid_passwords = [
            "SecurePass123!",
            "MyStr0ng@Password",
            "Admin2024#Security",
            "Test!Password123"
        ]

        for password in valid_passwords:
            assert service._validate_password(password), f"Password {password} should be valid"

        # Test invalid passwords
        invalid_passwords = [
            "short",  # Too short
            "nouppercase123!",  # No uppercase
            "NOLOWERCASE123!",  # No lowercase
            "NoNumbers!",  # No numbers
            "NoSpecialChars123",  # No special characters
            "Simple123",  # No special character
            "password123!",  # Common password
            "",  # Empty
            "12345678"  # Only numbers
        ]

        for password in invalid_passwords:
            assert not service._validate_password(password), f"Password {password} should be invalid"

    @patch('app.admin.services.admin_service.AdminRepository')
    @patch('app.admin.services.admin_service.AuditRepository')
    def test_failed_login_attempt_tracking(self, mock_audit_repo, mock_admin_repo):
        """Test tracking of failed login attempts"""
        mock_admin_repo_instance = MagicMock()
        mock_admin_repo.return_value = mock_admin_repo_instance

        admin_user = AdminUser(
            username="testadmin",
            email="test@admin.com",
            role="admin"
        )
        admin_user.set_password("SecurePass123!")
        admin_user.is_active = True
        admin_user.is_locked = False
        admin_user.failed_login_attempts = 2  # Already 2 failed attempts

        mock_admin_repo_instance.find_by_username.return_value = admin_user
        mock_admin_repo_instance.update.return_value = True

        mock_audit_repo_instance = MagicMock()
        mock_audit_repo.return_value = mock_audit_repo_instance

        service = AdminService()

        # Simulate another failed login (should lock account)
        success, message, result = service.authenticate_admin(
            "testadmin",
            "WrongPassword",
            "192.168.1.1"
        )

        assert not success
        # Check that update was called to increment failed attempts
        mock_admin_repo_instance.update.assert_called()

    @patch('app.admin.services.admin_service.AdminRepository')
    @patch('app.admin.services.admin_service.AuditRepository')
    def test_admin_session_timeout_validation(self, mock_audit_repo, mock_admin_repo):
        """Test session timeout validation"""
        mock_admin_repo_instance = MagicMock()
        mock_admin_repo.return_value = mock_admin_repo_instance

        admin_user = AdminUser(
            username="testadmin",
            email="test@admin.com",
            role="admin"
        )
        admin_user.set_password("SecurePass123!")
        admin_user.is_active = True
        admin_user.last_activity = datetime.now(timezone.utc) - timedelta(hours=25)  # Old activity
        admin_user.session_timeout_minutes = 60  # 1 hour timeout

        mock_admin_repo_instance.find_by_username.return_value = admin_user
        mock_audit_repo_instance = MagicMock()
        mock_audit_repo.return_value = mock_audit_repo_instance

        service = AdminService()

        # Check if session is expired
        is_expired = service._is_session_expired(admin_user)
        assert is_expired

    def test_mfa_token_validation(self):
        """Test multi-factor authentication token validation"""
        admin_user = AdminUser(
            username="testadmin",
            email="test@admin.com",
            role="admin"
        )
        admin_user.mfa_enabled = True
        admin_user.mfa_secret = "JBSWY3DPEHPK3PXP"  # Base32 encoded secret

        # Test MFA methods
        assert admin_user.mfa_enabled
        assert admin_user.mfa_secret is not None

        # Note: Actual TOTP validation would require time-based calculation
        # This tests the structure for MFA support

    @patch('app.admin.services.admin_service.AdminRepository')
    @patch('app.admin.services.admin_service.AuditRepository')
    def test_admin_login_audit_logging(self, mock_audit_repo, mock_admin_repo):
        """Test that login attempts are properly logged"""
        mock_admin_repo_instance = MagicMock()
        mock_admin_repo.return_value = mock_admin_repo_instance

        admin_user = AdminUser(
            username="testadmin",
            email="test@admin.com",
            role="admin"
        )
        admin_user.set_password("SecurePass123!")
        admin_user.is_active = True

        mock_admin_repo_instance.find_by_username.return_value = admin_user

        mock_audit_repo_instance = MagicMock()
        mock_audit_repo.return_value = mock_audit_repo_instance

        service = AdminService()

        # Test successful login audit
        success, message, result = service.authenticate_admin(
            "testadmin",
            "SecurePass123!",
            "192.168.1.1"
        )

        # Verify audit log was called
        mock_audit_repo_instance.create.assert_called()


class TestAdminPasswordManagement:
    """Test admin password management features"""

    def test_password_hashing(self):
        """Test password hashing functionality"""
        admin = AdminUser(username="test", email="test@admin.com")
        password = "SecurePass123!"

        admin.set_password(password)

        assert admin.password_hash is not None
        assert admin.password_hash != password  # Should be hashed
        assert admin.check_password(password)
        assert not admin.check_password("wrong_password")

    def test_password_salt_uniqueness(self):
        """Test that password salts are unique"""
        admin1 = AdminUser(username="test1", email="test1@admin.com")
        admin2 = AdminUser(username="test2", email="test2@admin.com")

        same_password = "SamePassword123!"
        admin1.set_password(same_password)
        admin2.set_password(same_password)

        # Even with same password, hashes should be different due to salt
        assert admin1.password_hash != admin2.password_hash

    def test_password_change_history(self):
        """Test password change history tracking"""
        admin = AdminUser(username="test", email="test@admin.com")

        # Set initial password
        admin.set_password("FirstPassword123!")
        first_hash = admin.password_hash

        # Change password
        admin.set_password("SecondPassword123!")
        second_hash = admin.password_hash

        assert first_hash != second_hash
        assert admin.check_password("SecondPassword123!")
        assert not admin.check_password("FirstPassword123!")

    def test_password_reset_functionality(self):
        """Test password reset token generation and validation"""
        admin = AdminUser(username="test", email="test@admin.com")
        admin.set_password("OriginalPass123!")

        # Generate reset token
        reset_token = admin.generate_password_reset_token()
        assert reset_token is not None
        assert admin.password_reset_token is not None
        assert admin.password_reset_expires is not None

        # Validate reset token
        assert admin.validate_password_reset_token(reset_token)

        # Invalid token should fail
        assert not admin.validate_password_reset_token("invalid_token")


if __name__ == '__main__':
    pytest.main([__file__])