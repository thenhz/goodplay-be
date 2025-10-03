from typing import List, Dict, Any, Tuple, Optional
from flask import current_app
from app.core.repositories.user_repository import UserRepository
from app.social.repositories.relationship_repository import RelationshipRepository
from app.social.models.user_relationship import UserRelationship


class RelationshipService:
    """Service for managing user relationships (friends, following, blocking)"""

    def __init__(self):
        self.relationship_repository = RelationshipRepository()
        self.user_repository = UserRepository()

    def send_friend_request(self, user_id: str, target_user_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Send a friend request to another user

        Args:
            user_id: ID of user sending the request
            target_user_id: ID of user receiving the request

        Returns:
            Tuple[success, message, data]
        """
        try:
            current_app.logger.info(f"User {user_id} sending friend request to {target_user_id}")

            # Validate users exist and are active
            validation_result = self._validate_users(user_id, target_user_id)
            if not validation_result[0]:
                return validation_result

            # Check if relationship already exists
            existing_relationship = self.relationship_repository.find_relationship_between_users(
                user_id, target_user_id, UserRelationship.FRIEND
            )

            if existing_relationship:
                if existing_relationship.is_accepted():
                    return False, "FRIEND_REQUEST_ALREADY_FRIENDS", None
                elif existing_relationship.is_pending():
                    return False, "FRIEND_REQUEST_ALREADY_SENT", None
                elif existing_relationship.is_declined():
                    # Allow sending new request after decline
                    self.relationship_repository.delete_relationship(str(existing_relationship._id))

            # Check if user is blocked
            if self.relationship_repository.is_blocked(target_user_id, user_id):
                return False, "FRIEND_REQUEST_USER_BLOCKED", None

            # Check target user's privacy settings
            target_user = self.user_repository.find_user_by_id(target_user_id)
            privacy_prefs = target_user.preferences.get("privacy", {})
            contact_permissions = privacy_prefs.get("contact_permissions", "friends")

            if contact_permissions == "none":
                return False, "FRIEND_REQUEST_NOT_ALLOWED", None

            # Create friend request
            relationship = UserRelationship(
                user_id=user_id,
                target_user_id=target_user_id,
                relationship_type=UserRelationship.FRIEND,
                initiated_by=user_id,
                status=UserRelationship.PENDING
            )

            relationship_id = self.relationship_repository.create_relationship(relationship)

            current_app.logger.info(f"Friend request created with ID: {relationship_id}")

            return True, "FRIEND_REQUEST_SENT_SUCCESS", {
                "relationship_id": relationship_id,
                "target_user_id": target_user_id,
                "status": "pending"
            }

        except Exception as e:
            current_app.logger.error(f"Error sending friend request: {str(e)}")
            return False, "FRIEND_REQUEST_SEND_FAILED", None

    def accept_friend_request(self, user_id: str, relationship_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Accept a friend request

        Args:
            user_id: ID of user accepting the request
            relationship_id: ID of the relationship to accept

        Returns:
            Tuple[success, message, data]
        """
        try:
            current_app.logger.info(f"User {user_id} accepting friend request {relationship_id}")

            # Find the relationship
            relationship = self.relationship_repository.find_relationship_by_id(relationship_id)
            if not relationship:
                return False, "FRIEND_REQUEST_NOT_FOUND", None

            # Validate user can accept this request
            if str(relationship.target_user_id) != user_id:
                return False, "FRIEND_REQUEST_NOT_AUTHORIZED", None

            if not relationship.is_pending():
                return False, "FRIEND_REQUEST_NOT_PENDING", None

            # Update relationship status
            success = self.relationship_repository.update_relationship_status(
                relationship_id, UserRelationship.ACCEPTED
            )

            if not success:
                return False, "FRIEND_REQUEST_ACCEPT_FAILED", None

            # Update friends count for both users
            self._update_friends_count(str(relationship.user_id))
            self._update_friends_count(str(relationship.target_user_id))

            current_app.logger.info(f"Friend request {relationship_id} accepted successfully")

            return True, "FRIEND_REQUEST_ACCEPTED_SUCCESS", {
                "relationship_id": relationship_id,
                "friend_user_id": str(relationship.user_id),
                "status": "accepted"
            }

        except Exception as e:
            current_app.logger.error(f"Error accepting friend request: {str(e)}")
            return False, "FRIEND_REQUEST_ACCEPT_FAILED", None

    def decline_friend_request(self, user_id: str, relationship_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Decline a friend request

        Args:
            user_id: ID of user declining the request
            relationship_id: ID of the relationship to decline

        Returns:
            Tuple[success, message, data]
        """
        try:
            current_app.logger.info(f"User {user_id} declining friend request {relationship_id}")

            # Find the relationship
            relationship = self.relationship_repository.find_relationship_by_id(relationship_id)
            if not relationship:
                return False, "FRIEND_REQUEST_NOT_FOUND", None

            # Validate user can decline this request
            if str(relationship.target_user_id) != user_id:
                return False, "FRIEND_REQUEST_NOT_AUTHORIZED", None

            if not relationship.is_pending():
                return False, "FRIEND_REQUEST_NOT_PENDING", None

            # Update relationship status
            success = self.relationship_repository.update_relationship_status(
                relationship_id, UserRelationship.DECLINED
            )

            if not success:
                return False, "FRIEND_REQUEST_DECLINE_FAILED", None

            current_app.logger.info(f"Friend request {relationship_id} declined successfully")

            return True, "FRIEND_REQUEST_DECLINED_SUCCESS", {
                "relationship_id": relationship_id
            }

        except Exception as e:
            current_app.logger.error(f"Error declining friend request: {str(e)}")
            return False, "FRIEND_REQUEST_DECLINE_FAILED", None

    def remove_friend(self, user_id: str, friend_user_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Remove a friend relationship

        Args:
            user_id: ID of user removing the friend
            friend_user_id: ID of friend to remove

        Returns:
            Tuple[success, message, data]
        """
        try:
            current_app.logger.info(f"User {user_id} removing friend {friend_user_id}")

            # Validate users exist
            validation_result = self._validate_users(user_id, friend_user_id)
            if not validation_result[0]:
                return validation_result

            # Check if friendship exists
            relationship = self.relationship_repository.find_relationship_between_users(
                user_id, friend_user_id, UserRelationship.FRIEND
            )

            if not relationship or not relationship.is_accepted():
                return False, "FRIEND_RELATIONSHIP_NOT_FOUND", None

            # Delete the relationship
            success = self.relationship_repository.delete_relationship(str(relationship._id))
            if not success:
                return False, "FRIEND_REMOVE_FAILED", None

            # Update friends count for both users
            self._update_friends_count(user_id)
            self._update_friends_count(friend_user_id)

            current_app.logger.info(f"Friendship between {user_id} and {friend_user_id} removed")

            return True, "FRIEND_REMOVED_SUCCESS", {
                "removed_user_id": friend_user_id
            }

        except Exception as e:
            current_app.logger.error(f"Error removing friend: {str(e)}")
            return False, "FRIEND_REMOVE_FAILED", None

    def block_user(self, user_id: str, target_user_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Block another user

        Args:
            user_id: ID of user doing the blocking
            target_user_id: ID of user to block

        Returns:
            Tuple[success, message, data]
        """
        try:
            current_app.logger.info(f"User {user_id} blocking user {target_user_id}")

            # Validate users exist
            validation_result = self._validate_users(user_id, target_user_id)
            if not validation_result[0]:
                return validation_result

            # Check if user is already blocked
            if self.relationship_repository.is_blocked(user_id, target_user_id):
                return False, "USER_ALREADY_BLOCKED", None

            # Remove existing friendship if it exists
            existing_friendship = self.relationship_repository.find_relationship_between_users(
                user_id, target_user_id, UserRelationship.FRIEND
            )
            if existing_friendship:
                self.relationship_repository.delete_relationship(str(existing_friendship._id))
                # Update friends count
                self._update_friends_count(user_id)
                self._update_friends_count(target_user_id)

            # Create block relationship
            relationship = UserRelationship(
                user_id=user_id,
                target_user_id=target_user_id,
                relationship_type=UserRelationship.BLOCKED,
                initiated_by=user_id,
                status=UserRelationship.ACCEPTED  # Blocks are immediately active
            )

            relationship_id = self.relationship_repository.create_relationship(relationship)

            current_app.logger.info(f"User {target_user_id} blocked by {user_id}")

            return True, "USER_BLOCKED_SUCCESS", {
                "blocked_user_id": target_user_id,
                "relationship_id": relationship_id
            }

        except Exception as e:
            current_app.logger.error(f"Error blocking user: {str(e)}")
            return False, "USER_BLOCK_FAILED", None

    def unblock_user(self, user_id: str, target_user_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Unblock a user

        Args:
            user_id: ID of user doing the unblocking
            target_user_id: ID of user to unblock

        Returns:
            Tuple[success, message, data]
        """
        try:
            current_app.logger.info(f"User {user_id} unblocking user {target_user_id}")

            # Find block relationship
            block_relationship = self.relationship_repository.find_relationship_between_users(
                user_id, target_user_id, UserRelationship.BLOCKED
            )

            if not block_relationship or str(block_relationship.user_id) != user_id:
                return False, "USER_NOT_BLOCKED", None

            # Delete the block relationship
            success = self.relationship_repository.delete_relationship(str(block_relationship._id))
            if not success:
                return False, "USER_UNBLOCK_FAILED", None

            current_app.logger.info(f"User {target_user_id} unblocked by {user_id}")

            return True, "USER_UNBLOCKED_SUCCESS", {
                "unblocked_user_id": target_user_id
            }

        except Exception as e:
            current_app.logger.error(f"Error unblocking user: {str(e)}")
            return False, "USER_UNBLOCK_FAILED", None

    def get_friends_list(self, user_id: str, limit: int = 50, skip: int = 0) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Get user's friends list

        Args:
            user_id: ID of user whose friends to get
            limit: Maximum number of friends to return
            skip: Number of friends to skip for pagination

        Returns:
            Tuple[success, message, data] containing friends list
        """
        try:
            current_app.logger.info(f"Getting friends list for user {user_id}")

            # Validate user exists
            if not self.user_repository.find_user_by_id(user_id):
                return False, "USER_NOT_FOUND", None

            # Get friend relationships
            friend_relationships = self.relationship_repository.get_user_friends(user_id, limit, skip)

            # Get user details for friends
            friends_list = []
            for relationship in friend_relationships:
                # Determine which user is the friend (not the current user)
                friend_id = (str(relationship.target_user_id) if str(relationship.user_id) == user_id
                           else str(relationship.user_id))

                friend_user = self.user_repository.find_user_by_id(friend_id)
                if friend_user:
                    friend_info = {
                        "id": friend_id,
                        "display_name": friend_user.social_profile.get("display_name", "Unknown User"),
                        "first_name": friend_user.first_name,
                        "last_name": friend_user.last_name,
                        "impact_score": friend_user.impact_score,
                        "gaming_stats": {
                            "total_play_time": friend_user.gaming_stats.get("total_play_time", 0),
                            "favorite_category": friend_user.gaming_stats.get("favorite_category")
                        },
                        "friendship_date": relationship.created_at.isoformat(),
                        "is_active": friend_user.is_active
                    }
                    friends_list.append(friend_info)

            # Get total friends count
            total_friends = self.relationship_repository.get_friends_count(user_id)

            current_app.logger.info(f"Retrieved {len(friends_list)} friends for user {user_id}")

            # Calculate pagination metadata
            page = (skip // limit) + 1
            total_pages = (total_friends + limit - 1) // limit if total_friends > 0 else 1

            return True, "FRIENDS_LIST_SUCCESS", {
                "friends": friends_list,
                "total": total_friends,
                "pagination": {
                    "page": page,
                    "per_page": limit,
                    "total_items": total_friends,
                    "total_pages": total_pages,
                    "has_next": (skip + limit) < total_friends,
                    "has_prev": skip > 0
                }
            }

        except Exception as e:
            current_app.logger.error(f"Error getting friends list: {str(e)}")
            return False, "FRIENDS_LIST_FAILED", None

    def get_friend_requests(self, user_id: str, type_filter: str = "received",
                          limit: int = 20, skip: int = 0) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Get friend requests (received or sent)

        Args:
            user_id: ID of user whose requests to get
            type_filter: "received" or "sent"
            limit: Maximum number of requests to return
            skip: Number of requests to skip for pagination

        Returns:
            Tuple[success, message, data] containing friend requests
        """
        try:
            current_app.logger.info(f"Getting {type_filter} friend requests for user {user_id}")

            # Validate user exists
            if not self.user_repository.find_user_by_id(user_id):
                return False, "USER_NOT_FOUND", None

            # Get friend requests based on type
            if type_filter == "received":
                requests = self.relationship_repository.get_pending_friend_requests(user_id, limit, skip)
            elif type_filter == "sent":
                requests = self.relationship_repository.get_sent_friend_requests(user_id, limit, skip)
            else:
                return False, "INVALID_REQUEST_TYPE", None

            # Format requests with user details
            formatted_requests = []
            for request in requests:
                # Get the other user's details
                other_user_id = (str(request.user_id) if type_filter == "received"
                               else str(request.target_user_id))

                other_user = self.user_repository.find_user_by_id(other_user_id)
                if other_user:
                    request_info = {
                        "id": str(request._id),
                        "user_id": other_user_id,
                        "display_name": other_user.social_profile.get("display_name", "Unknown User"),
                        "first_name": other_user.first_name,
                        "last_name": other_user.last_name,
                        "impact_score": other_user.impact_score,
                        "created_at": request.created_at.isoformat(),
                        "status": request.status,
                        "type": type_filter
                    }
                    formatted_requests.append(request_info)

            # Get total count
            if type_filter == "received":
                total_count = self.relationship_repository.get_pending_requests_count(user_id)
            else:
                # For sent requests, we need to count manually
                all_sent = self.relationship_repository.get_sent_friend_requests(user_id)
                total_count = len(all_sent)

            current_app.logger.info(f"Retrieved {len(formatted_requests)} {type_filter} requests")

            # Calculate pagination metadata
            page = (skip // limit) + 1
            total_pages = (total_count + limit - 1) // limit if total_count > 0 else 1

            return True, "FRIEND_REQUESTS_SUCCESS", {
                "requests": formatted_requests,
                "total": total_count,
                "type": type_filter,
                "pagination": {
                    "page": page,
                    "per_page": limit,
                    "total_items": total_count,
                    "total_pages": total_pages,
                    "has_next": (skip + limit) < total_count,
                    "has_prev": skip > 0
                }
            }

        except Exception as e:
            current_app.logger.error(f"Error getting friend requests: {str(e)}")
            return False, "FRIEND_REQUESTS_FAILED", None

    def get_blocked_users(self, user_id: str, limit: int = 50, skip: int = 0) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Get list of blocked users

        Args:
            user_id: ID of user whose blocked list to get
            limit: Maximum number of blocked users to return
            skip: Number to skip for pagination

        Returns:
            Tuple[success, message, data] containing blocked users
        """
        try:
            current_app.logger.info(f"Getting blocked users for user {user_id}")

            # Validate user exists
            if not self.user_repository.find_user_by_id(user_id):
                return False, "USER_NOT_FOUND", None

            # Get blocked relationships
            blocked_relationships = self.relationship_repository.get_blocked_users(user_id, limit, skip)

            # Format blocked users list
            blocked_users = []
            for relationship in blocked_relationships:
                blocked_user_id = str(relationship.target_user_id)
                blocked_user = self.user_repository.find_user_by_id(blocked_user_id)

                if blocked_user:
                    user_info = {
                        "id": blocked_user_id,
                        "display_name": blocked_user.social_profile.get("display_name", "Unknown User"),
                        "first_name": blocked_user.first_name,
                        "last_name": blocked_user.last_name,
                        "blocked_at": relationship.created_at.isoformat()
                    }
                    blocked_users.append(user_info)

            current_app.logger.info(f"Retrieved {len(blocked_users)} blocked users")

            # Get total count for pagination
            total_blocked = len(blocked_users)
            page = (skip // limit) + 1
            total_pages = (total_blocked + limit - 1) // limit if total_blocked > 0 else 1

            return True, "BLOCKED_USERS_SUCCESS", {
                "blocked_users": blocked_users,
                "total": total_blocked,
                "pagination": {
                    "page": page,
                    "per_page": limit,
                    "total_items": total_blocked,
                    "total_pages": total_pages,
                    "has_next": (skip + limit) < total_blocked,
                    "has_prev": skip > 0
                }
            }

        except Exception as e:
            current_app.logger.error(f"Error getting blocked users: {str(e)}")
            return False, "BLOCKED_USERS_FAILED", None

    def _validate_users(self, user_id: str, target_user_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Validate that both users exist and are different"""
        if user_id == target_user_id:
            return False, "CANNOT_INTERACT_WITH_SELF", None

        if not self.user_repository.find_user_by_id(user_id):
            return False, "USER_NOT_FOUND", None

        if not self.user_repository.find_user_by_id(target_user_id):
            return False, "TARGET_USER_NOT_FOUND", None

        return True, "USERS_VALID", None

    def _update_friends_count(self, user_id: str):
        """Update friends count in user's social profile"""
        try:
            friends_count = self.relationship_repository.get_friends_count(user_id)
            self.user_repository.update_social_profile(user_id, {"friends_count": friends_count})
        except Exception as e:
            current_app.logger.error(f"Error updating friends count for user {user_id}: {str(e)}")