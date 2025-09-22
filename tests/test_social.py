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
    def relationship_service(self, mock_db):
        """Create RelationshipService instance with mocked dependencies"""
        relationship_repo = RelationshipRepository()
        relationship_repo.collection = mock_db
        return RelationshipService(relationship_repo)

    def test_send_friend_request_success(self, relationship_service, mock_db):
        """Test successful friend request sending"""
        user_id = str(ObjectId())
        target_user_id = str(ObjectId())

        # Mock no existing relationship
        mock_db.find_one.return_value = None
        mock_db.insert_one.return_value = MagicMock(inserted_id=ObjectId())

        success, message, result = relationship_service.send_friend_request(user_id, target_user_id)

        assert success is True
        assert message == "FRIEND_REQUEST_SENT_SUCCESS"
        assert result is not None

    def test_send_friend_request_to_self(self, relationship_service):
        """Test sending friend request to self"""
        user_id = str(ObjectId())

        success, message, result = relationship_service.send_friend_request(user_id, user_id)

        assert success is False
        assert message == "CANNOT_BEFRIEND_SELF"
        assert result is None

    def test_send_friend_request_already_exists(self, relationship_service, mock_db):
        """Test sending friend request when relationship already exists"""
        user_id = str(ObjectId())
        target_user_id = str(ObjectId())

        # Mock existing relationship
        existing_relationship = {
            "_id": ObjectId(),
            "user_id": ObjectId(user_id),
            "target_user_id": ObjectId(target_user_id),
            "relationship_type": "friend",
            "status": "pending"
        }
        mock_db.find_one.return_value = existing_relationship

        success, message, result = relationship_service.send_friend_request(user_id, target_user_id)

        assert success is False
        assert message == "FRIEND_REQUEST_ALREADY_EXISTS"
        assert result is None

    def test_accept_friend_request_success(self, relationship_service, mock_db):
        """Test successful friend request acceptance"""
        request_id = str(ObjectId())
        user_id = str(ObjectId())

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

        success, message, result = relationship_service.accept_friend_request(request_id, user_id)

        assert success is True
        assert message == "FRIEND_REQUEST_ACCEPTED_SUCCESS"
        assert result is not None

    def test_accept_friend_request_not_found(self, relationship_service, mock_db):
        """Test accepting non-existent friend request"""
        request_id = str(ObjectId())
        user_id = str(ObjectId())

        mock_db.find_one.return_value = None

        success, message, result = relationship_service.accept_friend_request(request_id, user_id)

        assert success is False
        assert message == "FRIEND_REQUEST_NOT_FOUND"
        assert result is None

    def test_decline_friend_request_success(self, relationship_service, mock_db):
        """Test successful friend request decline"""
        request_id = str(ObjectId())
        user_id = str(ObjectId())

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

        success, message, result = relationship_service.decline_friend_request(request_id, user_id)

        assert success is True
        assert message == "FRIEND_REQUEST_DECLINED_SUCCESS"
        assert result is not None

    def test_remove_friend_success(self, relationship_service, mock_db):
        """Test successful friend removal"""
        user_id = str(ObjectId())
        friend_user_id = str(ObjectId())

        # Mock existing friendship
        friendship = {
            "_id": ObjectId(),
            "user_id": ObjectId(user_id),
            "target_user_id": ObjectId(friend_user_id),
            "relationship_type": "friend",
            "status": "accepted"
        }
        mock_db.find_one.return_value = friendship
        mock_db.delete_many.return_value = MagicMock(deleted_count=2)

        success, message, result = relationship_service.remove_friend(user_id, friend_user_id)

        assert success is True
        assert message == "FRIEND_REMOVED_SUCCESS"
        assert result is not None

    def test_remove_friend_not_friends(self, relationship_service, mock_db):
        """Test removing non-existent friend"""
        user_id = str(ObjectId())
        friend_user_id = str(ObjectId())

        mock_db.find_one.return_value = None

        success, message, result = relationship_service.remove_friend(user_id, friend_user_id)

        assert success is False
        assert message == "FRIENDSHIP_NOT_FOUND"
        assert result is None

    def test_get_friends_list_success(self, relationship_service, mock_db):
        """Test getting friends list"""
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
        mock_db.aggregate.return_value = friends_data

        success, message, result = relationship_service.get_friends_list(user_id)

        assert success is True
        assert message == "FRIENDS_LIST_RETRIEVED_SUCCESS"
        assert result is not None
        assert len(result) == 1

    def test_get_friend_requests_success(self, relationship_service, mock_db):
        """Test getting friend requests"""
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
        mock_db.aggregate.return_value = requests_data

        success, message, result = relationship_service.get_friend_requests(user_id, "received")

        assert success is True
        assert message == "FRIEND_REQUESTS_RETRIEVED_SUCCESS"
        assert result is not None
        assert len(result) == 1

    def test_block_user_success(self, relationship_service, mock_db):
        """Test successful user blocking"""
        user_id = str(ObjectId())
        target_user_id = str(ObjectId())

        # Mock no existing relationship
        mock_db.find_one.return_value = None
        mock_db.insert_one.return_value = MagicMock(inserted_id=ObjectId())

        success, message, result = relationship_service.block_user(user_id, target_user_id)

        assert success is True
        assert message == "USER_BLOCKED_SUCCESS"
        assert result is not None

    def test_unblock_user_success(self, relationship_service, mock_db):
        """Test successful user unblocking"""
        user_id = str(ObjectId())
        target_user_id = str(ObjectId())

        # Mock existing block relationship
        block_relationship = {
            "_id": ObjectId(),
            "user_id": ObjectId(user_id),
            "target_user_id": ObjectId(target_user_id),
            "relationship_type": "blocked",
            "status": "active"
        }
        mock_db.find_one.return_value = block_relationship
        mock_db.delete_one.return_value = MagicMock(deleted_count=1)

        success, message, result = relationship_service.unblock_user(user_id, target_user_id)

        assert success is True
        assert message == "USER_UNBLOCKED_SUCCESS"
        assert result is not None

    def test_get_relationship_status_friends(self, relationship_service, mock_db):
        """Test getting relationship status between friends"""
        user_id = str(ObjectId())
        target_user_id = str(ObjectId())

        # Mock friendship
        friendship = {
            "_id": ObjectId(),
            "user_id": ObjectId(user_id),
            "target_user_id": ObjectId(target_user_id),
            "relationship_type": "friend",
            "status": "accepted"
        }
        mock_db.find_one.return_value = friendship

        success, message, result = relationship_service.get_relationship_status(user_id, target_user_id)

        assert success is True
        assert message == "RELATIONSHIP_STATUS_RETRIEVED_SUCCESS"
        assert result["status"] == "friends"


class TestSocialDiscoveryService:
    """Test cases for SocialDiscoveryService"""

    @pytest.fixture
    def discovery_service(self, mock_db):
        """Create SocialDiscoveryService instance"""
        return SocialDiscoveryService()

    def test_search_users_success(self, discovery_service, mock_db):
        """Test successful user search"""
        user_id = str(ObjectId())
        search_query = "john"

        with patch('app.core.repositories.user_repository.UserRepository') as mock_repo:
            mock_repo_instance = mock_repo.return_value
            mock_repo_instance.collection = mock_db

            # Mock search results
            search_results = [
                {
                    "_id": ObjectId(),
                    "email": "john.doe@example.com",
                    "first_name": "John",
                    "last_name": "Doe"
                }
            ]
            mock_db.find.return_value = search_results

            success, message, result = discovery_service.search_users(
                user_id, search_query, privacy_level="public"
            )

            assert success is True
            assert message == "USER_SEARCH_SUCCESS"
            assert result is not None

    def test_get_friend_suggestions_success(self, discovery_service, mock_db):
        """Test getting friend suggestions"""
        user_id = str(ObjectId())

        with patch('app.core.repositories.user_repository.UserRepository') as mock_repo, \
             patch('app.social.repositories.relationship_repository.RelationshipRepository') as mock_rel_repo:

            mock_repo_instance = mock_repo.return_value
            mock_rel_repo_instance = mock_rel_repo.return_value
            mock_repo_instance.collection = mock_db
            mock_rel_repo_instance.collection = mock_db

            # Mock suggestions
            suggestions = [
                {
                    "_id": ObjectId(),
                    "email": "suggestion@example.com",
                    "first_name": "Suggested",
                    "last_name": "User"
                }
            ]
            mock_db.aggregate.return_value = suggestions

            success, message, result = discovery_service.get_friend_suggestions(user_id)

            assert success is True
            assert message == "FRIEND_SUGGESTIONS_RETRIEVED_SUCCESS"
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
        relationship = UserRelationship(
            user_id=ObjectId(),
            target_user_id=ObjectId(),
            relationship_type="friend",
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