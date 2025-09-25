"""
Unit Tests for User Preferences Module (GOO-6)
Tests preferences service, repository, and controller
"""
import pytest
import json
from functools import wraps
from unittest.mock import MagicMock, patch
from bson import ObjectId

from app.preferences.services.preferences_service import PreferencesService
from app.core.repositories.user_repository import UserRepository
from app.core.models.user import User


class TestPreferencesService:
    """Test cases for PreferencesService"""

    @pytest.fixture
    def mock_preferences_repo(self):
        """Create mocked PreferencesRepository"""
        return MagicMock()

    @pytest.fixture
    def preferences_service(self, mock_preferences_repo):
        """Create PreferencesService instance with mocked dependencies"""
        service = PreferencesService()
        service.preferences_repository = mock_preferences_repo
        return service

    def test_get_preferences_success(self, app, preferences_service, mock_preferences_repo, sample_user):
        """Test successful preferences retrieval"""
        with app.app_context():
            user_id = str(ObjectId())
            mock_preferences_repo.get_user_preferences.return_value = sample_user

            success, message, result = preferences_service.get_user_preferences(user_id)

        assert success is True
        assert message == "PREFERENCES_RETRIEVED_SUCCESS"
        assert result is not None
        assert "preferences" in result
        assert "gaming" in result["preferences"]
        assert "notifications" in result["preferences"]
        assert "privacy" in result["preferences"]
        assert "donations" in result["preferences"]

    def test_get_preferences_user_not_found(self, app, preferences_service, mock_preferences_repo):
        """Test preferences retrieval for non-existent user"""
        with app.app_context():
            mock_preferences_repo.get_user_preferences.return_value = None

            success, message, result = preferences_service.get_user_preferences(str(ObjectId()))

        assert success is False
        assert message == "USER_NOT_FOUND"
        assert result is None

    def test_update_preferences_success(self, app, preferences_service, mock_preferences_repo, sample_user, sample_preferences):
        """Test successful preferences update"""
        with app.app_context():
            user_id = str(ObjectId())
            updated_user = sample_user
            updated_user.preferences.update(sample_preferences)

            mock_preferences_repo.get_user_preferences.return_value = sample_user
            mock_preferences_repo.update_preferences.return_value = True

            success, message, result = preferences_service.update_user_preferences(user_id, sample_preferences)

        assert success is True
        assert message == "PREFERENCES_UPDATED_SUCCESS"
        assert result is not None

    def test_update_preferences_invalid_data(self, app, preferences_service):
        """Test preferences update with invalid data"""
        with app.app_context():
            invalid_preferences = {
                "gaming": {
                    "difficulty_level": "invalid_level"  # Invalid value
                }
            }

            success, message, result = preferences_service.update_user_preferences(
                str(ObjectId()),
                invalid_preferences
            )

        assert success is False
        assert message == "GAMING_DIFFICULTY_INVALID"
        assert result is None

    def test_get_category_preferences_success(self, app, preferences_service, mock_preferences_repo, sample_user):
        """Test getting specific category preferences"""
        with app.app_context():
            user_id = str(ObjectId())
            mock_preferences_repo.get_category_preferences.return_value = sample_user.preferences.get("gaming")

            success, message, result = preferences_service.get_preferences_category(user_id, "gaming")

        assert success is True
        assert message == "PREFERENCES_CATEGORY_RETRIEVED_SUCCESS"
        assert result is not None
        assert "category" in result
        assert "preferences" in result
        assert "difficulty_level" in result["preferences"]
        assert "tutorial_enabled" in result["preferences"]

    def test_get_category_preferences_invalid_category(self, preferences_service, mock_preferences_repo, sample_user):
        """Test getting invalid category preferences"""
        user_id = str(ObjectId())

        success, message, result = preferences_service.get_preferences_category(user_id, "invalid_category")

        assert success is False
        assert message == "PREFERENCES_CATEGORY_INVALID"
        assert result is None

    def test_update_category_preferences_success(self, app, preferences_service, mock_preferences_repo, sample_user):
        """Test updating specific category preferences"""
        with app.app_context():
            user_id = str(ObjectId())
            gaming_preferences = {
                "difficulty_level": "hard",
                "tutorial_enabled": False,
                "sound_enabled": False
            }

            mock_preferences_repo.get_user_preferences.return_value = sample_user
            mock_preferences_repo.update_category.return_value = True

            success, message, result = preferences_service.update_preferences_category(
                user_id,
                "gaming",
                gaming_preferences
            )

        assert success is True
        assert message == "PREFERENCES_CATEGORY_UPDATED_SUCCESS"
        assert result is not None

    def test_reset_preferences_success(self, app, preferences_service, mock_preferences_repo, sample_user):
        """Test resetting preferences to defaults"""
        with app.app_context():
            user_id = str(ObjectId())
            mock_preferences_repo.reset_to_defaults.return_value = True
            mock_preferences_repo.get_user_preferences.return_value = sample_user

            success, message, result = preferences_service.reset_user_preferences(user_id)

        assert success is True
        assert message == "PREFERENCES_RESET_SUCCESS"
        assert result is not None

    def test_get_default_preferences(self, app, preferences_service):
        """Test getting default preferences template"""
        with app.app_context():
            success, message, result = preferences_service.get_default_preferences()

        assert success is True
        assert message == "DEFAULT_PREFERENCES_RETRIEVED_SUCCESS"
        assert result is not None
        assert "default_preferences" in result
        assert "gaming" in result["default_preferences"]
        assert "notifications" in result["default_preferences"]
        assert "privacy" in result["default_preferences"]
        assert "donations" in result["default_preferences"]

    def test_validate_gaming_preferences_valid(self, preferences_service):
        """Test validation of valid gaming preferences"""
        valid_gaming = {
            "difficulty_level": "medium",
            "tutorial_enabled": True,
            "preferred_categories": ["puzzle", "strategy"],
            "sound_enabled": True
        }

        # Use User model validation directly since service doesn't expose private validation methods
        validation_data = {'gaming': valid_gaming}
        error = User.validate_preferences_data(validation_data)
        assert error is None

    def test_validate_gaming_preferences_invalid_difficulty(self, preferences_service):
        """Test validation of invalid gaming difficulty"""
        invalid_gaming = {
            "difficulty_level": "impossible"  # Invalid
        }

        # Use User model validation directly since service doesn't expose private validation methods
        validation_data = {'gaming': invalid_gaming}
        error = User.validate_preferences_data(validation_data)
        assert error == "GAMING_DIFFICULTY_INVALID"

    def test_validate_gaming_preferences_invalid_categories(self, preferences_service):
        """Test validation of invalid gaming categories"""
        invalid_gaming = {
            "preferred_categories": "not_a_list"  # Should be list
        }

        # Use User model validation directly since service doesn't expose private validation methods
        validation_data = {'gaming': invalid_gaming}
        error = User.validate_preferences_data(validation_data)
        assert error == "GAMING_CATEGORIES_INVALID"

    def test_validate_notification_preferences_valid(self, preferences_service):
        """Test validation of valid notification preferences"""
        valid_notifications = {
            "frequency": "weekly",
            "push_enabled": True,
            "email_enabled": False
        }

        # Use User model validation directly since service doesn't expose private validation methods
        validation_data = {'notifications': valid_notifications}
        error = User.validate_preferences_data(validation_data)
        assert error is None

    def test_validate_notification_preferences_invalid_frequency(self, preferences_service):
        """Test validation of invalid notification frequency"""
        invalid_notifications = {
            "frequency": "hourly"  # Invalid
        }

        # Use User model validation directly since service doesn't expose private validation methods
        validation_data = {'notifications': invalid_notifications}
        error = User.validate_preferences_data(validation_data)
        assert error == "NOTIFICATION_FREQUENCY_INVALID"

    def test_validate_privacy_preferences_valid(self, preferences_service):
        """Test validation of valid privacy preferences"""
        valid_privacy = {
            "profile_visibility": "friends",
            "stats_sharing": True,
            "activity_visibility": "private"
        }

        # Use User model validation directly since service doesn't expose private validation methods
        validation_data = {'privacy': valid_privacy}
        error = User.validate_preferences_data(validation_data)
        assert error is None

    def test_validate_privacy_preferences_invalid_visibility(self, preferences_service):
        """Test validation of invalid privacy visibility"""
        invalid_privacy = {
            "profile_visibility": "invisible"  # Invalid
        }

        # Use User model validation directly since service doesn't expose private validation methods
        validation_data = {'privacy': invalid_privacy}
        error = User.validate_preferences_data(validation_data)
        assert error == "PRIVACY_VISIBILITY_INVALID"

    def test_validate_donation_preferences_valid(self, preferences_service):
        """Test validation of valid donation preferences"""
        valid_donations = {
            "auto_donate_percentage": 15.0,
            "auto_donate_enabled": True,
            "preferred_causes": ["education"]
        }

        # Use User model validation directly since service doesn't expose private validation methods
        validation_data = {'donations': valid_donations}
        error = User.validate_preferences_data(validation_data)
        assert error is None

    def test_validate_donation_preferences_invalid_percentage(self, preferences_service):
        """Test validation of invalid donation percentage"""
        invalid_donations = {
            "auto_donate_percentage": 150.0  # > 100%
        }

        # Use User model validation directly since service doesn't expose private validation methods
        validation_data = {'donations': invalid_donations}
        error = User.validate_preferences_data(validation_data)
        assert error == "DONATION_PERCENTAGE_INVALID"


class TestPreferencesController:
    """Test cases for Preferences Controller endpoints"""

    @patch('flask_jwt_extended.jwt_required')
    @patch('flask_jwt_extended.get_jwt_identity')
    @patch('app.core.repositories.user_repository.UserRepository.find_user_by_id')
    def test_get_preferences_endpoint_success(self, mock_find_user, mock_get_identity, mock_jwt_required, client, mock_db, sample_user):
        """Test /api/preferences endpoint success"""
        user_id = str(ObjectId())
        sample_user._id = ObjectId(user_id)

        # Mock JWT authentication
        mock_jwt_required.return_value = lambda f: f  # Bypass JWT requirement
        mock_get_identity.return_value = user_id
        mock_find_user.return_value = sample_user

        user_doc = {
            "_id": ObjectId(user_id),
            "email": "test@goodplay.com",
            "preferences": {
                "gaming": {"difficulty_level": "medium"},
                "notifications": {"push_enabled": True},
                "privacy": {"profile_visibility": "public"},
                "donations": {"auto_donate_enabled": False}
            }
        }
        mock_db.find_one.return_value = user_doc

        response = client.get('/api/preferences')

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data["success"] is True
        assert response_data["message"] == "PREFERENCES_RETRIEVED_SUCCESS"

    @patch('app.preferences.controllers.preferences_controller.auth_required')
    def test_update_preferences_endpoint_success(self, mock_auth, client, mock_db, sample_user):
        """Test PUT /api/preferences endpoint success"""
        user_id = str(ObjectId())
        sample_user._id = ObjectId(user_id)

        # Mock the auth_required decorator to bypass authentication
        def mock_decorator(f):
            @wraps(f)
            def wrapper(*args, **kwargs):
                return f(current_user=sample_user, *args, **kwargs)
            return wrapper
        mock_auth.side_effect = mock_decorator

        user_doc = {
            "_id": ObjectId(user_id),
            "email": "test@goodplay.com",
            "preferences": {}
        }
        mock_db.find_one.return_value = user_doc
        mock_db.update_one.return_value = MagicMock(modified_count=1)

        preferences_data = {
            "gaming": {
                "difficulty_level": "hard",
                "tutorial_enabled": False
            }
        }

        response = client.put(
            '/api/preferences',
            data=json.dumps(preferences_data),
            content_type='application/json'
        )

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data["success"] is True
        assert response_data["message"] == "PREFERENCES_UPDATED_SUCCESS"

    @patch('flask_jwt_extended.jwt_required')
    @patch('flask_jwt_extended.get_jwt_identity')
    def test_get_category_preferences_endpoint_success(self, mock_get_identity, mock_jwt, client, mock_db):
        """Test GET /api/preferences/{category} endpoint success"""
        user_id = str(ObjectId())
        mock_get_identity.return_value = user_id
        mock_jwt.return_value = lambda f: f

        user_doc = {
            "_id": ObjectId(user_id),
            "email": "test@goodplay.com",
            "preferences": {
                "gaming": {
                    "difficulty_level": "medium",
                    "tutorial_enabled": True
                }
            }
        }
        mock_db.find_one.return_value = user_doc

        response = client.get('/api/preferences/gaming')

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data["success"] is True
        assert response_data["message"] == "PREFERENCES_CATEGORY_RETRIEVED_SUCCESS"

    @patch('flask_jwt_extended.jwt_required')
    @patch('flask_jwt_extended.get_jwt_identity')
    def test_update_category_preferences_endpoint_success(self, mock_get_identity, mock_jwt, client, mock_db):
        """Test PUT /api/preferences/{category} endpoint success"""
        user_id = str(ObjectId())
        mock_get_identity.return_value = user_id
        mock_jwt.return_value = lambda f: f

        user_doc = {
            "_id": ObjectId(user_id),
            "email": "test@goodplay.com",
            "preferences": {"gaming": {}}
        }
        mock_db.find_one.return_value = user_doc
        mock_db.update_one.return_value = MagicMock(modified_count=1)

        gaming_data = {
            "difficulty_level": "hard",
            "sound_enabled": False
        }

        response = client.put(
            '/api/preferences/gaming',
            data=json.dumps(gaming_data),
            content_type='application/json'
        )

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data["success"] is True
        assert response_data["message"] == "PREFERENCES_CATEGORY_UPDATED_SUCCESS"

    @patch('flask_jwt_extended.jwt_required')
    @patch('flask_jwt_extended.get_jwt_identity')
    def test_reset_preferences_endpoint_success(self, mock_get_identity, mock_jwt, client, mock_db):
        """Test POST /api/preferences/reset endpoint success"""
        user_id = str(ObjectId())
        mock_get_identity.return_value = user_id
        mock_jwt.return_value = lambda f: f

        user_doc = {
            "_id": ObjectId(user_id),
            "email": "test@goodplay.com",
            "preferences": {}
        }
        mock_db.find_one.return_value = user_doc
        mock_db.update_one.return_value = MagicMock(modified_count=1)

        response = client.post('/api/preferences/reset')

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data["success"] is True
        assert response_data["message"] == "PREFERENCES_RESET_SUCCESS"

    def test_get_defaults_endpoint_success(self, client):
        """Test GET /api/preferences/defaults endpoint success"""
        response = client.get('/api/preferences/defaults')

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data["success"] is True
        assert response_data["message"] == "DEFAULT_PREFERENCES_RETRIEVED_SUCCESS"
        assert "data" in response_data
        assert "default_preferences" in response_data["data"]
        assert "gaming" in response_data["data"]["default_preferences"]
        assert "notifications" in response_data["data"]["default_preferences"]
        assert "privacy" in response_data["data"]["default_preferences"]
        assert "donations" in response_data["data"]["default_preferences"]

    @patch('flask_jwt_extended.jwt_required')
    @patch('flask_jwt_extended.get_jwt_identity')
    def test_get_category_invalid_category(self, mock_get_identity, mock_jwt, client, mock_db):
        """Test GET /api/preferences/{category} with invalid category"""
        user_id = str(ObjectId())
        mock_get_identity.return_value = user_id
        mock_jwt.return_value = lambda f: f

        user_doc = {
            "_id": ObjectId(user_id),
            "email": "test@goodplay.com",
            "preferences": {}
        }
        mock_db.find_one.return_value = user_doc

        response = client.get('/api/preferences/invalid_category')

        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert response_data["success"] is False
        assert response_data["message"] == "PREFERENCES_CATEGORY_INVALID"

    @patch('flask_jwt_extended.jwt_required')
    @patch('flask_jwt_extended.get_jwt_identity')
    def test_update_preferences_no_data(self, mock_get_identity, mock_jwt, client):
        """Test PUT /api/preferences endpoint with no data"""
        user_id = str(ObjectId())
        mock_get_identity.return_value = user_id
        mock_jwt.return_value = lambda f: f

        response = client.put(
            '/api/preferences',
            data=json.dumps({}),
            content_type='application/json'
        )

        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert response_data["success"] is False
        assert response_data["message"] == "PREFERENCES_DATA_REQUIRED"