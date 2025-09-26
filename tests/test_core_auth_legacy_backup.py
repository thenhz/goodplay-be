"""
Working Unit Tests for Core Authentication Module
Tests that match the actual implementation
"""
import pytest
import json
import os
from unittest.mock import MagicMock, patch, Mock
from bson import ObjectId
from datetime import datetime, timezone

# Add app to path
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.services.auth_service import AuthService
from app.core.repositories.user_repository import UserRepository
from app.core.models.user import User


class TestAuthServiceWorking:
    """Test cases for AuthService with actual method signatures"""

    @pytest.fixture
    def mock_user_repo(self):
        """Create mocked UserRepository"""
        mock_repo = Mock(spec=UserRepository)
        return mock_repo

    @pytest.fixture
    def auth_service(self, mock_user_repo):
        """Create AuthService instance with mocked dependencies"""
        service = AuthService()
        service.user_repository = mock_user_repo
        return service

    def test_register_user_success(self, app, auth_service, mock_user_repo):
        """Test successful user registration"""
        with app.app_context():
            # Setup mocks
            mock_user_repo.email_exists.return_value = False
            mock_user_repo.create_user.return_value = str(ObjectId())

            with patch('app.core.services.auth_service.create_access_token', return_value='access_token'), \
                 patch('app.core.services.auth_service.create_refresh_token', return_value='refresh_token'):

                success, message, result = auth_service.register_user(
                    "test@goodplay.com", "password123", "Test", "User"
                )

                assert success is True
                assert message == "Registration completed successfully"
            assert result is not None
            assert "user" in result
            assert "tokens" in result

    def test_register_user_email_exists(self, auth_service, mock_user_repo):
        """Test registration with existing email"""
        mock_user_repo.email_exists.return_value = True

        success, message, result = auth_service.register_user(
            "existing@goodplay.com", "password123"
        )

        assert success is False
        assert message == "Email already registered"
        assert result is None

    def test_register_user_invalid_email(self, auth_service):
        """Test registration with invalid email"""
        success, message, result = auth_service.register_user(
            "invalid-email", "password123"
        )

        assert success is False
        assert "Invalid email format" in message
        assert result is None

    def test_register_user_weak_password(self, auth_service):
        """Test registration with weak password"""
        success, message, result = auth_service.register_user(
            "test@goodplay.com", "123"
        )

        assert success is False
        assert "Password must be at least 6 characters long" in message
        assert result is None

    def test_register_user_missing_email(self, auth_service):
        """Test registration with missing email"""
        success, message, result = auth_service.register_user(
            "", "password123"
        )

        assert success is False
        assert "Email and password are required" in message
        assert result is None

    def test_login_user_success(self, app, auth_service, mock_user_repo):
        """Test successful user login"""
        with app.app_context():
            # Create mock user
            mock_user = Mock(spec=User)
            mock_user.check_password.return_value = True
            mock_user.is_active = True
            mock_user.get_id.return_value = str(ObjectId())
            mock_user.to_dict.return_value = {"email": "test@goodplay.com"}

            mock_user_repo.find_by_email.return_value = mock_user

            with patch('app.core.services.auth_service.create_access_token', return_value='access_token'), \
                 patch('app.core.services.auth_service.create_refresh_token', return_value='refresh_token'):

                success, message, result = auth_service.login_user(
                    "test@goodplay.com", "password123"
                )

                assert success is True
                assert message == "Login successful"
            assert result is not None
            assert "user" in result
            assert "tokens" in result

    def test_login_user_not_found(self, auth_service, mock_user_repo):
        """Test login with non-existent user"""
        mock_user_repo.find_by_email.return_value = None

        success, message, result = auth_service.login_user(
            "nonexistent@example.com", "password123"
        )

        assert success is False
        assert message == "Invalid credentials"
        assert result is None

    def test_login_user_wrong_password(self, auth_service, mock_user_repo):
        """Test login with wrong password"""
        mock_user = Mock(spec=User)
        mock_user.check_password.return_value = False
        mock_user_repo.find_by_email.return_value = mock_user

        success, message, result = auth_service.login_user(
            "test@goodplay.com", "wrong_password"
        )

        assert success is False
        assert message == "Invalid credentials"
        assert result is None

    def test_login_inactive_user(self, auth_service, mock_user_repo):
        """Test login with inactive user"""
        mock_user = Mock(spec=User)
        mock_user.check_password.return_value = True
        mock_user.is_active = False
        mock_user_repo.find_by_email.return_value = mock_user

        success, message, result = auth_service.login_user(
            "test@goodplay.com", "password123"
        )

        assert success is False
        assert message == "Account disabled"
        assert result is None

    def test_login_missing_credentials(self, auth_service):
        """Test login with missing email or password"""
        success, message, result = auth_service.login_user("", "password123")
        assert success is False
        assert message == "Email and password are required"

        success, message, result = auth_service.login_user("test@example.com", "")
        assert success is False
        assert message == "Email and password are required"

    def test_refresh_token_success(self, auth_service, mock_user_repo):
        """Test successful token refresh"""
        user_id = str(ObjectId())
        mock_user = Mock(spec=User)
        mock_user.is_active = True
        mock_user.get_id.return_value = user_id
        mock_user_repo.find_user_by_id.return_value = mock_user

        with patch('app.core.services.auth_service.create_access_token', return_value='new_access_token'):
            success, message, result = auth_service.refresh_token(user_id)

            assert success is True
            assert message == "Token refreshed successfully"
            assert result is not None
            assert "access_token" in result

    def test_refresh_token_user_not_found(self, auth_service, mock_user_repo):
        """Test token refresh with non-existent user"""
        mock_user_repo.find_user_by_id.return_value = None

        success, message, result = auth_service.refresh_token(str(ObjectId()))

        assert success is False
        assert message == "User not found or disabled"
        assert result is None

    def test_get_user_profile_success(self, auth_service, mock_user_repo):
        """Test successful profile retrieval"""
        user_id = str(ObjectId())
        mock_user = Mock(spec=User)
        mock_user.to_dict.return_value = {"email": "test@goodplay.com"}
        mock_user_repo.find_user_by_id.return_value = mock_user

        success, message, result = auth_service.get_user_profile(user_id)

        assert success is True
        assert message == "Profile retrieved successfully"
        assert result is not None
        assert "user" in result

    def test_get_user_profile_not_found(self, auth_service, mock_user_repo):
        """Test profile retrieval for non-existent user"""
        mock_user_repo.find_user_by_id.return_value = None

        success, message, result = auth_service.get_user_profile(str(ObjectId()))

        assert success is False
        assert message == "User not found"
        assert result is None


class TestUserRepositoryWorking:
    """Test cases for UserRepository with correct methods"""

    @pytest.fixture
    def mock_collection(self):
        """Mock MongoDB collection"""
        return Mock()

    @pytest.fixture
    def user_repo(self, mock_collection):
        """Create UserRepository with mocked collection"""
        repo = UserRepository()
        repo.collection = mock_collection
        return repo

    def test_find_by_email_success(self, user_repo, mock_collection):
        """Test finding user by email"""
        expected_user_data = {
            "_id": ObjectId(),
            "email": "test@goodplay.com",
            "first_name": "Test"
        }
        mock_collection.find_one.return_value = expected_user_data

        result = user_repo.find_by_email("test@goodplay.com")

        assert result is not None
        assert result.email == "test@goodplay.com"
        mock_collection.find_one.assert_called_once_with({"email": "test@goodplay.com"})

    def test_find_by_email_not_found(self, user_repo, mock_collection):
        """Test finding non-existent user by email"""
        mock_collection.find_one.return_value = None

        result = user_repo.find_by_email("nonexistent@example.com")

        assert result is None

    def test_email_exists_true(self, user_repo, mock_collection):
        """Test email exists check - exists"""
        mock_collection.find_one.return_value = {"email": "existing@example.com"}

        result = user_repo.email_exists("existing@example.com")

        assert result is True

    def test_email_exists_false(self, user_repo, mock_collection):
        """Test email exists check - doesn't exist"""
        mock_collection.find_one.return_value = None

        result = user_repo.email_exists("new@example.com")

        assert result is False

    def test_create_user_success(self, user_repo):
        """Test creating new user"""
        user = User(email="test@goodplay.com", first_name="Test")
        mock_inserted_id = str(ObjectId())

        with patch.object(user_repo, 'create', return_value=mock_inserted_id):
            result = user_repo.create_user(user)

            assert result == mock_inserted_id

    def test_find_user_by_id_success(self, user_repo):
        """Test finding user by ID"""
        user_id = str(ObjectId())
        expected_user_data = {
            "_id": ObjectId(user_id),
            "email": "test@goodplay.com"
        }

        with patch.object(user_repo, 'find_by_id', return_value=expected_user_data):
            result = user_repo.find_user_by_id(user_id)

            assert result is not None
            assert result.email == "test@goodplay.com"

    def test_update_user_success(self, user_repo):
        """Test updating user"""
        user_id = str(ObjectId())
        user = User(email="updated@goodplay.com")

        with patch.object(user_repo, 'update_by_id', return_value=True):
            result = user_repo.update_user(user_id, user)

            assert result is True


class TestUserModelWorking:
    """Test cases for User model functionality"""

    def test_user_creation_with_preferences(self):
        """Test user creation includes preferences"""
        user = User(email="test@goodplay.com")

        assert user.email == "test@goodplay.com"
        assert isinstance(user.preferences, dict)
        assert "gaming" in user.preferences
        assert "notifications" in user.preferences
        assert "privacy" in user.preferences
        assert "donations" in user.preferences

    def test_user_email_normalization(self):
        """Test email normalization"""
        user = User(email="TEST@GOODPLAY.COM")

        assert user.email == "test@goodplay.com"

    def test_user_check_password_method(self):
        """Test user password checking"""
        user = User(
            email="test@goodplay.com",
            password_hash="hashed_password"
        )

        with patch('app.core.models.user.check_password_hash', return_value=True):
            result = user.check_password("correct_password")
            assert result is True

        with patch('app.core.models.user.check_password_hash', return_value=False):
            result = user.check_password("wrong_password")
            assert result is False

    def test_user_get_id_method(self):
        """Test user get_id method"""
        user_id = str(ObjectId())
        user = User(email="test@goodplay.com")
        user._id = user_id

        assert user.get_id() == user_id

    def test_user_serialization_excludes_sensitive(self):
        """Test user serialization excludes sensitive data by default"""
        user = User(
            email="test@goodplay.com",
            password_hash="secret_hash"
        )

        user_dict = user.to_dict()

        assert "email" in user_dict
        assert "password_hash" not in user_dict

    def test_user_serialization_includes_sensitive_when_requested(self):
        """Test user serialization includes sensitive data when requested"""
        user = User(
            email="test@goodplay.com",
            password_hash="secret_hash"
        )

        user_dict = user.to_dict(include_sensitive=True)

        assert "email" in user_dict
        assert "password_hash" in user_dict


class TestValidationMethodsWorking:
    """Test validation methods in AuthService"""

    def test_is_valid_email_valid(self):
        """Test email validation with valid emails"""
        service = AuthService()

        valid_emails = [
            "test@goodplay.com",
            "user.name@example.org",
            "valid+email@domain.co.uk"
        ]

        for email in valid_emails:
            result = service._is_valid_email(email)
            assert result is True, f"Should be valid: {email}"

    def test_is_valid_email_invalid(self):
        """Test email validation with invalid emails"""
        service = AuthService()

        invalid_emails = [
            "invalid-email",
            "@domain.com",
            "user@",
            "user name@domain.com",
            ""
        ]

        for email in invalid_emails:
            result = service._is_valid_email(email)
            assert result is False, f"Should be invalid: {email}"

    def test_validate_registration_data_valid(self):
        """Test registration validation with valid data"""
        service = AuthService()

        result = service._validate_registration_data("test@goodplay.com", "password123")
        assert result is None

    def test_validate_registration_data_invalid(self):
        """Test registration validation with invalid data"""
        service = AuthService()

        # Invalid email
        result = service._validate_registration_data("invalid-email", "password123")
        assert result == "Invalid email format"

        # Short password
        result = service._validate_registration_data("test@goodplay.com", "123")
        assert result == "Password must be at least 6 characters long"

        # Missing email
        result = service._validate_registration_data("", "password123")
        assert result == "Email and password are required"

        # Missing password
        result = service._validate_registration_data("test@goodplay.com", "")
        assert result == "Email and password are required"


class TestTokenGeneration:
    """Test token generation methods"""

    def test_generate_tokens(self):
        """Test token generation"""
        service = AuthService()
        mock_user = Mock(spec=User)
        mock_user.get_id.return_value = str(ObjectId())

        with patch('app.core.services.auth_service.create_access_token', return_value='access_token'), \
             patch('app.core.services.auth_service.create_refresh_token', return_value='refresh_token'):

            tokens = service._generate_tokens(mock_user)

            assert "access_token" in tokens
            assert "refresh_token" in tokens
            assert "token_type" in tokens
            assert tokens["token_type"] == "Bearer"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])