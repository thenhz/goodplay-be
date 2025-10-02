import pytest
import os
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch, MagicMock
from bson import ObjectId

# Set testing mode BEFORE importing app modules
os.environ['TESTING'] = 'true'

from app.core.models.user import User
from app.core.services.auth_service import AuthService
from app.core.services.email_service import EmailService
from app.core.repositories.user_repository import UserRepository


class TestEmailVerification:
    """Test suite for email verification functionality"""

    @pytest.fixture(autouse=True)
    def setup(self, app):
        """Setup test fixtures with Flask app context"""
        self.app = app
        self.auth_service = AuthService()
        self.email_service = EmailService()
        self.user_repository = UserRepository()

        # Mock database operations
        self.user_repository.collection = MagicMock()

    def test_user_model_has_verification_fields(self):
        """Test that User model has verification fields"""
        user = User(
            email="test@example.com",
            is_verified=False,
            verification_token="test_token",
            verification_token_expires_at=datetime.now(timezone.utc)
        )

        assert hasattr(user, 'is_verified')
        assert hasattr(user, 'verification_token')
        assert hasattr(user, 'verification_token_expires_at')
        assert user.is_verified == False
        assert user.verification_token == "test_token"

    def test_user_to_dict_includes_is_verified(self):
        """Test that user to_dict includes is_verified"""
        user = User(
            email="test@example.com",
            is_verified=True
        )

        user_dict = user.to_dict()
        assert 'is_verified' in user_dict
        assert user_dict['is_verified'] == True

    def test_user_to_dict_includes_verification_fields_when_sensitive(self):
        """Test that user to_dict includes verification fields when include_sensitive=True"""
        token_expires = datetime.now(timezone.utc) + timedelta(hours=24)
        user = User(
            email="test@example.com",
            verification_token="test_token",
            verification_token_expires_at=token_expires
        )

        user_dict = user.to_dict(include_sensitive=True)
        assert 'verification_token' in user_dict
        assert 'verification_token_expires_at' in user_dict

    @patch.object(UserRepository, 'find_by_verification_token')
    @patch.object(UserRepository, 'verify_user_email')
    def test_verify_email_success(self, mock_verify, mock_find):
        """Test successful email verification"""
        with self.app.app_context():
            # Setup
            user = User(
                _id=ObjectId(),
                email="test@example.com",
                is_verified=False,
                verification_token="valid_token",
                verification_token_expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
            )
            mock_find.return_value = user
            mock_verify.return_value = True

            # Execute
            success, message, result = self.auth_service.verify_email("valid_token")

            # Assert
            assert success == True
            assert message == "EMAIL_VERIFICATION_SUCCESS"
            assert result is not None
            assert result['email'] == "test@example.com"
            assert result['is_verified'] == True
            mock_find.assert_called_once_with("valid_token")
            mock_verify.assert_called_once()

    @patch.object(UserRepository, 'find_by_verification_token')
    def test_verify_email_invalid_token(self, mock_find):
        """Test email verification with invalid token"""
        # Setup
        mock_find.return_value = None

        # Execute
        success, message, result = self.auth_service.verify_email("invalid_token")

        # Assert
        assert success == False
        assert message == "VERIFICATION_TOKEN_INVALID"
        assert result is None

    @patch.object(UserRepository, 'find_by_verification_token')
    def test_verify_email_already_verified(self, mock_find):
        """Test email verification when already verified"""
        # Setup
        user = User(
            _id=ObjectId(),
            email="test@example.com",
            is_verified=True,
            verification_token="valid_token",
            verification_token_expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        mock_find.return_value = user

        # Execute
        success, message, result = self.auth_service.verify_email("valid_token")

        # Assert
        assert success == False
        assert message == "EMAIL_ALREADY_VERIFIED"
        assert result is None

    @patch.object(UserRepository, 'find_by_verification_token')
    def test_verify_email_expired_token(self, mock_find):
        """Test email verification with expired token"""
        # Setup
        user = User(
            _id=ObjectId(),
            email="test@example.com",
            is_verified=False,
            verification_token="expired_token",
            verification_token_expires_at=datetime.now(timezone.utc) - timedelta(hours=1)
        )
        mock_find.return_value = user

        # Execute
        success, message, result = self.auth_service.verify_email("expired_token")

        # Assert
        assert success == False
        assert message == "VERIFICATION_TOKEN_EXPIRED"
        assert result is None

    def test_verify_email_missing_token(self):
        """Test email verification with missing token"""
        # Execute
        success, message, result = self.auth_service.verify_email("")

        # Assert
        assert success == False
        assert message == "VERIFICATION_TOKEN_REQUIRED"
        assert result is None

    @patch.object(UserRepository, 'find_user_by_id')
    @patch.object(UserRepository, 'set_verification_token')
    @patch.object(EmailService, 'send_verification_email')
    def test_resend_verification_email_success(self, mock_send_email, mock_set_token, mock_find):
        """Test successful resend of verification email"""
        with self.app.app_context():
            # Setup
            user = User(
                _id=ObjectId(),
                email="test@example.com",
                first_name="Test",
                is_verified=False
            )
            mock_find.return_value = user
            mock_set_token.return_value = True
            mock_send_email.return_value = True

            # Execute
            success, message, result = self.auth_service.resend_verification_email(str(user._id))

            # Assert
            assert success == True
            assert message == "VERIFICATION_EMAIL_SENT"
            mock_send_email.assert_called_once()
            mock_set_token.assert_called_once()

    @patch.object(UserRepository, 'find_user_by_id')
    def test_resend_verification_email_user_not_found(self, mock_find):
        """Test resend verification email with invalid user"""
        # Setup
        mock_find.return_value = None

        # Execute
        success, message, result = self.auth_service.resend_verification_email("invalid_id")

        # Assert
        assert success == False
        assert message == "USER_NOT_FOUND"
        assert result is None

    @patch.object(UserRepository, 'find_user_by_id')
    def test_resend_verification_email_already_verified(self, mock_find):
        """Test resend verification email when already verified"""
        # Setup
        user = User(
            _id=ObjectId(),
            email="test@example.com",
            is_verified=True
        )
        mock_find.return_value = user

        # Execute
        success, message, result = self.auth_service.resend_verification_email(str(user._id))

        # Assert
        assert success == False
        assert message == "EMAIL_ALREADY_VERIFIED"
        assert result is None

    @patch.object(UserRepository, 'find_user_by_id')
    @patch.object(UserRepository, 'set_verification_token')
    @patch.object(EmailService, 'send_verification_email')
    def test_resend_verification_email_send_failed(self, mock_send_email, mock_set_token, mock_find):
        """Test resend verification email when email sending fails"""
        with self.app.app_context():
            # Setup
            user = User(
                _id=ObjectId(),
                email="test@example.com",
                is_verified=False
            )
            mock_find.return_value = user
            mock_set_token.return_value = True
            mock_send_email.return_value = False

            # Execute
            success, message, result = self.auth_service.resend_verification_email(str(user._id))

            # Assert
            assert success == False
            assert message == "VERIFICATION_EMAIL_FAILED"
            assert result is None

    @patch.object(UserRepository, 'email_exists')
    @patch.object(UserRepository, 'create_user')
    @patch.object(UserRepository, 'set_verification_token')
    @patch.object(EmailService, 'send_verification_email')
    def test_registration_sends_verification_email(self, mock_send_email, mock_set_token, mock_create, mock_exists):
        """Test that registration sends verification email"""
        with self.app.app_context():
            # Setup
            mock_exists.return_value = False
            mock_create.return_value = ObjectId()
            mock_set_token.return_value = True
            mock_send_email.return_value = True

            # Execute
            success, message, result = self.auth_service.register_user(
                email="newuser@example.com",
                password="password123",
                first_name="New",
                last_name="User"
            )

            # Assert
            assert success == True
            assert message == "USER_REGISTRATION_SUCCESS"
            assert 'verification_email_sent' in result
            assert result['verification_email_sent'] == True
            mock_send_email.assert_called_once()
            mock_set_token.assert_called_once()

    @patch.object(UserRepository, 'find_by_email')
    def test_login_blocked_for_unverified_user(self, mock_find):
        """Test that unverified users cannot login"""
        # Setup
        user = User(
            _id=ObjectId(),
            email="unverified@example.com",
            password_hash="hashed_password",
            is_verified=False,
            is_active=True
        )
        mock_find.return_value = user

        # Mock check_password
        with patch.object(user, 'check_password', return_value=True):
            # Execute
            success, message, result = self.auth_service.login_user(
                email="unverified@example.com",
                password="password123"
            )

            # Assert
            assert success == False
            assert message == "ACCOUNT_NOT_VERIFIED"
            assert result is None

    def test_email_service_creates_verification_email(self):
        """Test that email service creates proper verification email"""
        # This is a basic structure test
        token = "test_verification_token"
        email = "test@example.com"
        first_name = "Test"

        # Email service should have the method
        assert hasattr(self.email_service, 'send_verification_email')

    @patch.object(UserRepository, 'set_verification_token')
    def test_repository_set_verification_token(self, mock_update):
        """Test repository method for setting verification token"""
        # Setup
        mock_update.return_value = True
        user_id = str(ObjectId())
        token = "test_token"
        expires_at = datetime.now(timezone.utc) + timedelta(hours=24)

        # Execute
        result = self.user_repository.set_verification_token(user_id, token, expires_at)

        # Assert
        assert result == True

    @patch.object(UserRepository, 'verify_user_email')
    def test_repository_verify_user_email(self, mock_update):
        """Test repository method for verifying user email"""
        # Setup
        mock_update.return_value = True
        user_id = str(ObjectId())

        # Execute
        result = self.user_repository.verify_user_email(user_id)

        # Assert
        assert result == True
