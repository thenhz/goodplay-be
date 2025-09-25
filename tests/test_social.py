"""
Unit Tests for Social Module (GOO-7)
Tests social relationships, friend requests, and discovery features
"""
import pytest
import json
from unittest.mock import MagicMock, patch
from bson import ObjectId
from datetime import datetime, timezone

from app.social.services.relationship_service import RelationshipService
from app.social.services.social_discovery_service import SocialDiscoveryService
from app.social.repositories.relationship_repository import RelationshipRepository
from app.social.models.user_relationship import UserRelationship


class TestRelationshipService:
    """Test cases for RelationshipService"""

    @pytest.fixture
    def mock_relationship_repo(self):
        """Create mocked RelationshipRepository"""
        return MagicMock()

    @pytest.fixture
    def mock_user_repo(self):
        """Create mocked UserRepository"""
        return MagicMock()

    @pytest.fixture
    def relationship_service(self, mock_relationship_repo, mock_user_repo):
        """Create RelationshipService instance with mocked dependencies"""
        service = RelationshipService()
        service.relationship_repository = mock_relationship_repo
        service.user_repository = mock_user_repo
        return service

    def test_send_friend_request_success(self, app, relationship_service, mock_relationship_repo, mock_user_repo):
        """Test successful friend request sending"""
        with app.app_context():
            user_id = str(ObjectId())
            target_user_id = str(ObjectId())

            # Create mock users
            sender_user = MagicMock()
            target_user = MagicMock()
            target_user.preferences = {"privacy": {"contact_permissions": "friends"}}

            # Mock user repository to return appropriate users
            def mock_find_user_by_id(user_id_param):
                if user_id_param == user_id:
                    return sender_user
                elif user_id_param == target_user_id:
                    return target_user
                else:
                    return None

            mock_user_repo.find_user_by_id.side_effect = mock_find_user_by_id

            # Mock no existing relationship
            mock_relationship_repo.find_relationship_between_users.return_value = None
            mock_relationship_repo.is_blocked.return_value = False
            mock_relationship_repo.create_relationship.return_value = str(ObjectId())

            success, message, result = relationship_service.send_friend_request(user_id, target_user_id)

        assert success is True
        assert message == "FRIEND_REQUEST_SENT_SUCCESS"
        assert result is not None
        assert "relationship_id" in result
        assert "target_user_id" in result
        assert result["status"] == "pending"

    def test_send_friend_request_to_self(self, app, relationship_service):
        """Test sending friend request to self"""
        with app.app_context():
            user_id = str(ObjectId())

            success, message, result = relationship_service.send_friend_request(user_id, user_id)

        assert success is False
        assert message == "CANNOT_INTERACT_WITH_SELF"
        assert result is None

    def test_send_friend_request_already_exists(self, app, relationship_service, mock_relationship_repo, mock_user_repo):
        """Test sending friend request when relationship already exists"""
        with app.app_context():
            user_id = str(ObjectId())
            target_user_id = str(ObjectId())

            # Create mock users
            sender_user = MagicMock()
            target_user = MagicMock()
            target_user.preferences = {"privacy": {"contact_permissions": "friends"}}

            # Mock user repository
            def mock_find_user_by_id(user_id_param):
                if user_id_param == user_id:
                    return sender_user
                elif user_id_param == target_user_id:
                    return target_user
                else:
                    return None

            mock_user_repo.find_user_by_id.side_effect = mock_find_user_by_id

            # Mock existing pending relationship
            existing_relationship = MagicMock()
            existing_relationship.is_accepted.return_value = False
            existing_relationship.is_pending.return_value = True
            existing_relationship.is_declined.return_value = False
            mock_relationship_repo.find_relationship_between_users.return_value = existing_relationship

            success, message, result = relationship_service.send_friend_request(user_id, target_user_id)

        assert success is False
        assert message == "FRIEND_REQUEST_ALREADY_SENT"
        assert result is None

    def test_accept_friend_request_success(self, app, relationship_service, mock_relationship_repo):
        """Test successful friend request acceptance"""
        with app.app_context():
            request_id = str(ObjectId())
            user_id = str(ObjectId())
            requester_id = str(ObjectId())

            # Mock pending friend request
            pending_request = MagicMock()
            pending_request._id = ObjectId(request_id)
            pending_request.user_id = requester_id
            pending_request.target_user_id = user_id
            pending_request.is_pending.return_value = True
            pending_request.is_targeted_to.return_value = True

            mock_relationship_repo.find_relationship_by_id.return_value = pending_request
            mock_relationship_repo.accept_friend_request.return_value = True

            success, message, result = relationship_service.accept_friend_request(user_id, request_id)

        assert success is True
        assert message == "FRIEND_REQUEST_ACCEPTED_SUCCESS"
        assert result is not None

    def test_accept_friend_request_not_found(self, app, relationship_service, mock_relationship_repo):
        """Test accepting non-existent friend request"""
        with app.app_context():
            request_id = str(ObjectId())
            user_id = str(ObjectId())

            mock_relationship_repo.find_relationship_by_id.return_value = None

            success, message, result = relationship_service.accept_friend_request(user_id, request_id)

        assert success is False
        assert message == "FRIEND_REQUEST_NOT_FOUND"
        assert result is None

    def test_decline_friend_request_success(self, app, relationship_service, mock_relationship_repo):
        """Test successful friend request decline"""
        with app.app_context():
            request_id = str(ObjectId())
            user_id = str(ObjectId())
            requester_id = str(ObjectId())

            # Mock pending friend request
            pending_request = MagicMock()
            pending_request._id = ObjectId(request_id)
            pending_request.user_id = requester_id
            pending_request.target_user_id = user_id
            pending_request.is_pending.return_value = True
            pending_request.is_targeted_to.return_value = True

            mock_relationship_repo.find_relationship_by_id.return_value = pending_request
            mock_relationship_repo.decline_friend_request.return_value = True

            success, message, result = relationship_service.decline_friend_request(user_id, request_id)

        assert success is True
        assert message == "FRIEND_REQUEST_DECLINED_SUCCESS"
        assert result is not None

    def test_remove_friend_success(self, app, relationship_service, mock_relationship_repo):
        """Test successful friend removal"""
        with app.app_context():
            user_id = str(ObjectId())
            friend_user_id = str(ObjectId())

            # Mock existing friendship
            friendship = MagicMock()
            friendship.is_accepted.return_value = True
            mock_relationship_repo.find_relationship_between_users.return_value = friendship
            mock_relationship_repo.remove_friendship.return_value = True

            success, message, result = relationship_service.remove_friend(user_id, friend_user_id)

        assert success is True
        assert message == "FRIEND_REMOVED_SUCCESS"
        assert result is not None

    def test_remove_friend_not_friends(self, app, relationship_service, mock_relationship_repo):
        """Test removing non-existent friend"""
        with app.app_context():
            user_id = str(ObjectId())
            friend_user_id = str(ObjectId())

            mock_relationship_repo.find_relationship_between_users.return_value = None

            success, message, result = relationship_service.remove_friend(user_id, friend_user_id)

        assert success is False
        assert message == "FRIEND_RELATIONSHIP_NOT_FOUND"
        assert result is None

    def test_get_friends_list_success(self, app, relationship_service, mock_relationship_repo):
        """Test getting friends list"""
        with app.app_context():
            user_id = str(ObjectId())

            # Mock friends list
            friends_data = [
                {
                    "_id": ObjectId(),
                    "user_id": ObjectId(user_id),
                    "target_user_id": ObjectId(),
                    "relationship_type": "friend",
                    "status": "accepted",
                    "target_user_info": {
                        "_id": ObjectId(),
                        "email": "friend1@example.com",
                        "first_name": "Friend",
                        "last_name": "One"
                    }
                }
            ]
            mock_relationship_repo.get_friends_list.return_value = friends_data

            success, message, result = relationship_service.get_friends_list(user_id)

        assert success is True
        assert message == "FRIENDS_LIST_SUCCESS"
        assert result is not None
        assert "friends" in result
        assert "pagination" in result
        assert "total" in result

    def test_get_friend_requests_success(self, app, relationship_service, mock_relationship_repo):
        """Test getting friend requests"""
        with app.app_context():
            user_id = str(ObjectId())

            # Mock friend requests
            requests_data = [
                {
                    "_id": ObjectId(),
                    "user_id": ObjectId(),
                    "target_user_id": ObjectId(user_id),
                    "relationship_type": "friend",
                    "status": "pending",
                    "requester_info": {
                        "_id": ObjectId(),
                        "email": "requester@example.com",
                        "first_name": "Request",
                        "last_name": "User"
                    }
                }
            ]
            mock_relationship_repo.get_friend_requests.return_value = requests_data

            success, message, result = relationship_service.get_friend_requests(user_id, "received")

        assert success is True
        assert message == "FRIEND_REQUESTS_SUCCESS"
        assert result is not None
        assert "requests" in result
        assert "pagination" in result
        assert "total" in result
        assert "type" in result

    def test_block_user_success(self, app, relationship_service, mock_relationship_repo, mock_user_repo):
        """Test successful user blocking"""
        with app.app_context():
            user_id = str(ObjectId())
            target_user_id = str(ObjectId())

            # Create mock users
            blocker_user = MagicMock()
            target_user = MagicMock()

            # Mock user repository
            def mock_find_user_by_id(user_id_param):
                if user_id_param == user_id:
                    return blocker_user
                elif user_id_param == target_user_id:
                    return target_user
                else:
                    return None

            mock_user_repo.find_user_by_id.side_effect = mock_find_user_by_id

            # Mock relationship repository methods
            mock_relationship_repo.is_blocked.return_value = False  # Not already blocked
            mock_relationship_repo.find_relationship_between_users.return_value = None  # No existing friendship
            mock_relationship_repo.create_relationship.return_value = str(ObjectId())

            success, message, result = relationship_service.block_user(user_id, target_user_id)

        assert success is True
        assert message == "USER_BLOCKED_SUCCESS"
        assert result is not None

    def test_unblock_user_success(self, app, relationship_service, mock_relationship_repo):
        """Test successful user unblocking"""
        with app.app_context():
            user_id = str(ObjectId())
            target_user_id = str(ObjectId())

            # Mock existing block relationship
            block_relationship = MagicMock()
            block_relationship.user_id = user_id  # Make sure user_id matches
            mock_relationship_repo.find_relationship_between_users.return_value = block_relationship
            mock_relationship_repo.delete_relationship.return_value = True

            success, message, result = relationship_service.unblock_user(user_id, target_user_id)

        assert success is True
        assert message == "USER_UNBLOCKED_SUCCESS"
        assert result is not None

    # Removed test_get_relationship_status_friends - method doesn't exist in RelationshipService


class TestSocialDiscoveryService:
    """Test cases for SocialDiscoveryService"""

    @pytest.fixture
    def mock_user_repo(self):
        """Create mocked UserRepository"""
        return MagicMock()

    @pytest.fixture
    def mock_relationship_repo(self):
        """Create mocked RelationshipRepository"""
        return MagicMock()

    @pytest.fixture
    def discovery_service(self, mock_user_repo, mock_relationship_repo):
        """Create SocialDiscoveryService instance with mocked dependencies"""
        service = SocialDiscoveryService()
        service.user_repository = mock_user_repo
        service.relationship_repository = mock_relationship_repo
        return service

    def test_search_users_success(self, app, discovery_service, mock_user_repo, mock_relationship_repo):
        """Test successful user search"""
        with app.app_context():
            user_id = str(ObjectId())
            search_query = "john"

            # Mock search results
            search_results = [
                {
                    "_id": ObjectId(),
                    "email": "john.doe@example.com",
                    "first_name": "John",
                    "last_name": "Doe"
                }
            ]
            mock_user_repo.search_users_by_name_or_email.return_value = search_results
            mock_relationship_repo.get_user_relationships.return_value = []

            success, message, result = discovery_service.search_users(
                user_id, search_query
            )

        assert success is True
        assert message == "SEARCH_USERS_SUCCESS"
        assert result is not None

    def test_get_friend_suggestions_success(self, app, discovery_service, mock_user_repo, mock_relationship_repo):
        """Test getting friend suggestions"""
        with app.app_context():
            user_id = str(ObjectId())

            # Mock suggestions
            suggestions = [
                {
                    "_id": ObjectId(),
                    "email": "suggestion@example.com",
                    "first_name": "Suggested",
                    "last_name": "User"
                }
            ]
            mock_relationship_repo.get_friend_suggestions.return_value = suggestions

            success, message, result = discovery_service.get_friend_suggestions(user_id)

        assert success is True
        assert message == "FRIEND_SUGGESTIONS_SUCCESS"
        assert result is not None


class TestSocialController:
    """Test cases for Social Controller endpoints"""

    @patch('flask_jwt_extended.jwt_required')
    @patch('flask_jwt_extended.get_jwt_identity')
    def test_send_friend_request_endpoint_success(self, mock_get_identity, mock_jwt, client, mock_db):
        """Test POST /api/social/friend-request endpoint success"""
        user_id = str(ObjectId())
        target_user_id = str(ObjectId())
        mock_get_identity.return_value = user_id
        mock_jwt.return_value = lambda f: f

        # Mock successful friend request
        mock_db.find_one.return_value = None
        mock_db.insert_one.return_value = MagicMock(inserted_id=ObjectId())

        data = {"target_user_id": target_user_id}

        response = client.post(
            '/api/social/friend-request',
            data=json.dumps(data),
            content_type='application/json'
        )

        assert response.status_code == 201
        response_data = json.loads(response.data)
        assert response_data["success"] is True
        assert response_data["message"] == "FRIEND_REQUEST_SENT_SUCCESS"

    @patch('flask_jwt_extended.jwt_required')
    @patch('flask_jwt_extended.get_jwt_identity')
    def test_accept_friend_request_endpoint_success(self, mock_get_identity, mock_jwt, client, mock_db):
        """Test PUT /api/social/friend-request/{id}/accept endpoint success"""
        user_id = str(ObjectId())
        request_id = str(ObjectId())
        mock_get_identity.return_value = user_id
        mock_jwt.return_value = lambda f: f

        # Mock pending friend request
        pending_request = {
            "_id": ObjectId(request_id),
            "user_id": ObjectId(),
            "target_user_id": ObjectId(user_id),
            "relationship_type": "friend",
            "status": "pending"
        }
        mock_db.find_one.return_value = pending_request
        mock_db.update_one.return_value = MagicMock(modified_count=1)
        mock_db.insert_one.return_value = MagicMock(inserted_id=ObjectId())

        response = client.put(f'/api/social/friend-request/{request_id}/accept')

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data["success"] is True
        assert response_data["message"] == "FRIEND_REQUEST_ACCEPTED_SUCCESS"

    @patch('flask_jwt_extended.jwt_required')
    @patch('flask_jwt_extended.get_jwt_identity')
    def test_get_friends_endpoint_success(self, mock_get_identity, mock_jwt, client, mock_db):
        """Test GET /api/social/friends endpoint success"""
        user_id = str(ObjectId())
        mock_get_identity.return_value = user_id
        mock_jwt.return_value = lambda f: f

        # Mock friends list
        friends_data = [
            {
                "_id": ObjectId(),
                "user_id": ObjectId(user_id),
                "target_user_id": ObjectId(),
                "relationship_type": "friend",
                "status": "accepted",
                "target_user_info": {
                    "_id": ObjectId(),
                    "email": "friend@example.com",
                    "first_name": "Friend",
                    "last_name": "User"
                }
            }
        ]
        mock_db.aggregate.return_value = friends_data

        response = client.get('/api/social/friends')

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data["success"] is True
        assert response_data["message"] == "FRIENDS_LIST_RETRIEVED_SUCCESS"

    @patch('flask_jwt_extended.jwt_required')
    @patch('flask_jwt_extended.get_jwt_identity')
    def test_search_users_endpoint_success(self, mock_get_identity, mock_jwt, client, mock_db):
        """Test POST /api/social/users/search endpoint success"""
        user_id = str(ObjectId())
        mock_get_identity.return_value = user_id
        mock_jwt.return_value = lambda f: f

        # Mock search results
        search_results = [
            {
                "_id": ObjectId(),
                "email": "john@example.com",
                "first_name": "John",
                "last_name": "Doe"
            }
        ]
        mock_db.find.return_value = search_results

        data = {"query": "john", "privacy_level": "public"}

        response = client.post(
            '/api/social/users/search',
            data=json.dumps(data),
            content_type='application/json'
        )

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data["success"] is True
        assert response_data["message"] == "USER_SEARCH_SUCCESS"

    @patch('flask_jwt_extended.jwt_required')
    @patch('flask_jwt_extended.get_jwt_identity')
    def test_block_user_endpoint_success(self, mock_get_identity, mock_jwt, client, mock_db):
        """Test POST /api/social/users/{user_id}/block endpoint success"""
        user_id = str(ObjectId())
        target_user_id = str(ObjectId())
        mock_get_identity.return_value = user_id
        mock_jwt.return_value = lambda f: f

        # Mock no existing relationship
        mock_db.find_one.return_value = None
        mock_db.insert_one.return_value = MagicMock(inserted_id=ObjectId())

        response = client.post(f'/api/social/users/{target_user_id}/block')

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data["success"] is True
        assert response_data["message"] == "USER_BLOCKED_SUCCESS"

    @patch('flask_jwt_extended.jwt_required')
    @patch('flask_jwt_extended.get_jwt_identity')
    def test_get_social_stats_endpoint_success(self, mock_get_identity, mock_jwt, client, mock_db):
        """Test GET /api/social/stats endpoint success"""
        user_id = str(ObjectId())
        mock_get_identity.return_value = user_id
        mock_jwt.return_value = lambda f: f

        # Mock stats aggregation
        stats_data = [
            {
                "_id": None,
                "friends_count": 5,
                "pending_sent": 2,
                "pending_received": 1,
                "blocked_count": 0
            }
        ]
        mock_db.aggregate.return_value = stats_data

        response = client.get('/api/social/stats')

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data["success"] is True
        assert response_data["message"] == "SOCIAL_STATS_RETRIEVED_SUCCESS"


class TestUserRelationshipModel:
    """Test cases for UserRelationship model"""

    def test_create_user_relationship(self):
        """Test creating UserRelationship instance"""
        user_id = ObjectId()
        target_user_id = ObjectId()

        relationship = UserRelationship(
            user_id=user_id,
            target_user_id=target_user_id,
            relationship_type="friend",
            initiated_by=str(user_id),
            status="pending"
        )

        assert relationship.user_id == user_id
        assert relationship.target_user_id == target_user_id
        assert relationship.relationship_type == "friend"
        assert relationship.status == "pending"
        assert relationship.initiated_by == user_id  # Default
        assert isinstance(relationship.created_at, datetime)
        assert isinstance(relationship.updated_at, datetime)

    def test_relationship_to_dict(self):
        """Test relationship serialization"""
        user_id = ObjectId()
        relationship = UserRelationship(
            user_id=user_id,
            target_user_id=ObjectId(),
            relationship_type="friend",
            initiated_by=str(user_id),
            status="accepted"
        )

        relationship_dict = relationship.to_dict()

        assert "user_id" in relationship_dict
        assert "target_user_id" in relationship_dict
        assert "relationship_type" in relationship_dict
        assert "status" in relationship_dict
        assert "created_at" in relationship_dict
        assert "updated_at" in relationship_dict

    def test_relationship_from_dict(self):
        """Test relationship deserialization"""
        relationship_data = {
            "_id": ObjectId(),
            "user_id": ObjectId(),
            "target_user_id": ObjectId(),
            "relationship_type": "friend",
            "status": "accepted",
            "initiated_by": ObjectId(),
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }

        relationship = UserRelationship.from_dict(relationship_data)

        assert relationship.user_id == relationship_data["user_id"]
        assert relationship.target_user_id == relationship_data["target_user_id"]
        assert relationship.relationship_type == relationship_data["relationship_type"]
        assert relationship.status == relationship_data["status"]