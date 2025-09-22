"""
Unit Tests for User Preferences Module (GOO-6)
Tests preferences service, repository, and controller
"""
import pytest
import json
from unittest.mock import MagicMock, patch
from bson import ObjectId

from app.preferences.services.preferences_service import PreferencesService
from app.core.repositories.user_repository import UserRepository
from app.core.models.user import User


class TestPreferencesService:
    """Test cases for PreferencesService"""

    @pytest.fixture
    def preferences_service(self, mock_db):
        """Create PreferencesService instance with mocked dependencies"""
        user_repo = UserRepository()
        user_repo.collection = mock_db
        return PreferencesService(user_repo)

    def test_get_preferences_success(self, preferences_service, mock_db, sample_user):
        """Test successful preferences retrieval"""
        user_id = str(ObjectId())
        user_doc = sample_user.to_dict()
        user_doc["_id"] = ObjectId(user_id)
        mock_db.find_one.return_value = user_doc

        success, message, result = preferences_service.get_preferences(user_id)

        assert success is True
        assert message == "PREFERENCES_RETRIEVED_SUCCESS"
        assert result is not None
        assert "gaming" in result
        assert "notifications" in result
        assert "privacy" in result
        assert "donations" in result

    def test_get_preferences_user_not_found(self, preferences_service, mock_db):
        """Test preferences retrieval for non-existent user"""
        mock_db.find_one.return_value = None

        success, message, result = preferences_service.get_preferences(str(ObjectId()))

        assert success is False
        assert message == "USER_NOT_FOUND"
        assert result is None

    def test_update_preferences_success(self, preferences_service, mock_db, sample_user, sample_preferences):
        """Test successful preferences update"""
        user_id = str(ObjectId())
        user_doc = sample_user.to_dict()
        user_doc["_id"] = ObjectId(user_id)
        mock_db.find_one.return_value = user_doc
        mock_db.update_one.return_value = MagicMock(modified_count=1)

        success, message, result = preferences_service.update_preferences(user_id, sample_preferences)

        assert success is True
        assert message == "PREFERENCES_UPDATED_SUCCESS"
        assert result is not None

    def test_update_preferences_invalid_data(self, preferences_service):
        """Test preferences update with invalid data"""
        invalid_preferences = {
            "gaming": {
                "difficulty_level": "invalid_level"  # Invalid value
            }
        }

        success, message, result = preferences_service.update_preferences(
            str(ObjectId()),
            invalid_preferences
        )

        assert success is False
        assert message == "GAMING_DIFFICULTY_INVALID"
        assert result is None

    def test_get_category_preferences_success(self, preferences_service, mock_db, sample_user):
        """Test getting specific category preferences"""
        user_id = str(ObjectId())
        user_doc = sample_user.to_dict()
        user_doc["_id"] = ObjectId(user_id)
        mock_db.find_one.return_value = user_doc

        success, message, result = preferences_service.get_category_preferences(user_id, "gaming")

        assert success is True
        assert message == "PREFERENCES_CATEGORY_RETRIEVED_SUCCESS"
        assert result is not None
        assert "difficulty_level" in result
        assert "tutorial_enabled" in result

    def test_get_category_preferences_invalid_category(self, preferences_service, mock_db, sample_user):
        """Test getting invalid category preferences"""
        user_id = str(ObjectId())
        user_doc = sample_user.to_dict()
        user_doc["_id"] = ObjectId(user_id)
        mock_db.find_one.return_value = user_doc

        success, message, result = preferences_service.get_category_preferences(user_id, "invalid_category")

        assert success is False
        assert message == "PREFERENCES_CATEGORY_INVALID"
        assert result is None

    def test_update_category_preferences_success(self, preferences_service, mock_db, sample_user):
        """Test updating specific category preferences"""
        user_id = str(ObjectId())
        user_doc = sample_user.to_dict()
        user_doc["_id"] = ObjectId(user_id)
        mock_db.find_one.return_value = user_doc
        mock_db.update_one.return_value = MagicMock(modified_count=1)

        gaming_preferences = {
            "difficulty_level": "hard",
            "tutorial_enabled": False,
            "sound_enabled": False
        }

        success, message, result = preferences_service.update_category_preferences(
            user_id,
            "gaming",
            gaming_preferences
        )

        assert success is True
        assert message == "PREFERENCES_CATEGORY_UPDATED_SUCCESS"
        assert result is not None

    def test_reset_preferences_success(self, preferences_service, mock_db, sample_user):
        """Test resetting preferences to defaults"""
        user_id = str(ObjectId())
        user_doc = sample_user.to_dict()
        user_doc["_id"] = ObjectId(user_id)
        mock_db.find_one.return_value = user_doc
        mock_db.update_one.return_value = MagicMock(modified_count=1)

        success, message, result = preferences_service.reset_preferences(user_id)

        assert success is True
        assert message == "PREFERENCES_RESET_SUCCESS"
        assert result is not None

    def test_get_default_preferences(self, preferences_service):
        """Test getting default preferences template"""
        success, message, result = preferences_service.get_default_preferences()

        assert success is True
        assert message == "DEFAULT_PREFERENCES_RETRIEVED_SUCCESS"
        assert result is not None
        assert "gaming" in result
        assert "notifications" in result
        assert "privacy" in result
        assert "donations" in result

    def test_validate_gaming_preferences_valid(self, preferences_service):
        """Test validation of valid gaming preferences"""
        valid_gaming = {
            "difficulty_level": "medium",
            "tutorial_enabled": True,
            "preferred_categories": ["puzzle", "strategy"],
            "sound_enabled": True
        }

        error = preferences_service._validate_gaming_preferences(valid_gaming)
        assert error is None

    def test_validate_gaming_preferences_invalid_difficulty(self, preferences_service):
        """Test validation of invalid gaming difficulty"""
        invalid_gaming = {
            "difficulty_level": "impossible"  # Invalid
        }

        error = preferences_service._validate_gaming_preferences(invalid_gaming)
        assert error == "GAMING_DIFFICULTY_INVALID"

    def test_validate_gaming_preferences_invalid_categories(self, preferences_service):
        """Test validation of invalid gaming categories"""
        invalid_gaming = {
            "preferred_categories": "not_a_list"  # Should be list
        }

        error = preferences_service._validate_gaming_preferences(invalid_gaming)
        assert error == "GAMING_CATEGORIES_INVALID"

    def test_validate_notification_preferences_valid(self, preferences_service):
        """Test validation of valid notification preferences"""
        valid_notifications = {
            "frequency": "weekly",
            "push_enabled": True,
            "email_enabled": False
        }

        error = preferences_service._validate_notification_preferences(valid_notifications)
        assert error is None

    def test_validate_notification_preferences_invalid_frequency(self, preferences_service):
        """Test validation of invalid notification frequency"""
        invalid_notifications = {
            "frequency": "hourly"  # Invalid
        }

        error = preferences_service._validate_notification_preferences(invalid_notifications)
        assert error == "NOTIFICATION_FREQUENCY_INVALID"

    def test_validate_privacy_preferences_valid(self, preferences_service):
        """Test validation of valid privacy preferences"""
        valid_privacy = {
            "profile_visibility": "friends",
            "stats_sharing": True,
            "activity_visibility": "private"
        }

        error = preferences_service._validate_privacy_preferences(valid_privacy)
        assert error is None

    def test_validate_privacy_preferences_invalid_visibility(self, preferences_service):
        """Test validation of invalid privacy visibility"""
        invalid_privacy = {
            "profile_visibility": "invisible"  # Invalid
        }

        error = preferences_service._validate_privacy_preferences(invalid_privacy)
        assert error == "PRIVACY_VISIBILITY_INVALID"

    def test_validate_donation_preferences_valid(self, preferences_service):
        """Test validation of valid donation preferences"""
        valid_donations = {
            "auto_donate_percentage": 15.0,
            "auto_donate_enabled": True,
            "preferred_causes": ["education"]
        }

        error = preferences_service._validate_donation_preferences(valid_donations)
        assert error is None

    def test_validate_donation_preferences_invalid_percentage(self, preferences_service):
        """Test validation of invalid donation percentage"""
        invalid_donations = {
            "auto_donate_percentage": 150.0  # > 100%
        }

        error = preferences_service._validate_donation_preferences(invalid_donations)
        assert error == "DONATION_PERCENTAGE_INVALID"


class TestPreferencesController:
    """Test cases for Preferences Controller endpoints"""

    @patch('flask_jwt_extended.jwt_required')
    @patch('flask_jwt_extended.get_jwt_identity')
    def test_get_preferences_endpoint_success(self, mock_get_identity, mock_jwt, client, mock_db):
        """Test /api/preferences endpoint success"""
        user_id = str(ObjectId())
        mock_get_identity.return_value = user_id
        mock_jwt.return_value = lambda f: f

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

        response = client.get('/api/preferences/')

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data["success"] is True
        assert response_data["message"] == "PREFERENCES_RETRIEVED_SUCCESS"

    @patch('flask_jwt_extended.jwt_required')
    @patch('flask_jwt_extended.get_jwt_identity')
    def test_update_preferences_endpoint_success(self, mock_get_identity, mock_jwt, client, mock_db):
        """Test PUT /api/preferences endpoint success"""
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

        preferences_data = {
            "gaming": {
                "difficulty_level": "hard",
                "tutorial_enabled": False
            }
        }

        response = client.put(
            '/api/preferences/',
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
        assert "gaming" in response_data["data"]
        assert "notifications" in response_data["data"]
        assert "privacy" in response_data["data"]
        assert "donations" in response_data["data"]

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
            '/api/preferences/',
            data=json.dumps({}),
            content_type='application/json'
        )

        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert response_data["success"] is False
        assert response_data["message"] == "PREFERENCES_DATA_REQUIRED"