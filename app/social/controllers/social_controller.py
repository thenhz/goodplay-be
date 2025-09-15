from flask import Blueprint, request, current_app
from app.core.utils.decorators import auth_required
from app.core.utils.responses import success_response, error_response
from app.social.services.relationship_service import RelationshipService
from app.social.services.social_discovery_service import SocialDiscoveryService

social_bp = Blueprint('social', __name__)
relationship_service = RelationshipService()
discovery_service = SocialDiscoveryService()


@social_bp.route('/friend-request', methods=['POST'])
@auth_required
def send_friend_request(current_user):
    """Send a friend request to another user"""
    try:
        data = request.get_json()
        if not data:
            return error_response("FRIEND_REQUEST_DATA_REQUIRED")

        target_user_id = data.get('target_user_id', '').strip()
        if not target_user_id:
            return error_response("FRIEND_REQUEST_TARGET_USER_REQUIRED")

        success, message, result = relationship_service.send_friend_request(
            current_user.get_id(), target_user_id
        )

        if success:
            return success_response(message, result, 201)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Send friend request error: {str(e)}")
        return error_response("FRIEND_REQUEST_SEND_FAILED", status_code=500)


@social_bp.route('/friend-request/<relationship_id>/accept', methods=['PUT'])
@auth_required
def accept_friend_request(current_user, relationship_id):
    """Accept a friend request"""
    try:
        if not relationship_id:
            return error_response("FRIEND_REQUEST_ID_REQUIRED")

        success, message, result = relationship_service.accept_friend_request(
            current_user.get_id(), relationship_id
        )

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Accept friend request error: {str(e)}")
        return error_response("FRIEND_REQUEST_ACCEPT_FAILED", status_code=500)


@social_bp.route('/friend-request/<relationship_id>/decline', methods=['PUT'])
@auth_required
def decline_friend_request(current_user, relationship_id):
    """Decline a friend request"""
    try:
        if not relationship_id:
            return error_response("FRIEND_REQUEST_ID_REQUIRED")

        success, message, result = relationship_service.decline_friend_request(
            current_user.get_id(), relationship_id
        )

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Decline friend request error: {str(e)}")
        return error_response("FRIEND_REQUEST_DECLINE_FAILED", status_code=500)


@social_bp.route('/friends/<friend_user_id>', methods=['DELETE'])
@auth_required
def remove_friend(current_user, friend_user_id):
    """Remove a friend"""
    try:
        if not friend_user_id:
            return error_response("FRIEND_USER_ID_REQUIRED")

        success, message, result = relationship_service.remove_friend(
            current_user.get_id(), friend_user_id
        )

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Remove friend error: {str(e)}")
        return error_response("FRIEND_REMOVE_FAILED", status_code=500)


@social_bp.route('/friends', methods=['GET'])
@auth_required
def get_friends(current_user):
    """Get user's friends list"""
    try:
        # Get pagination parameters
        limit = request.args.get('limit', 50, type=int)
        skip = request.args.get('skip', 0, type=int)

        # Validate parameters
        if limit > 100:
            limit = 100
        if skip < 0:
            skip = 0

        success, message, result = relationship_service.get_friends_list(
            current_user.get_id(), limit, skip
        )

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Get friends error: {str(e)}")
        return error_response("FRIENDS_LIST_FAILED", status_code=500)


@social_bp.route('/friend-requests', methods=['GET'])
@auth_required
def get_friend_requests(current_user):
    """Get friend requests (received or sent)"""
    try:
        # Get query parameters
        type_filter = request.args.get('type', 'received')
        limit = request.args.get('limit', 20, type=int)
        skip = request.args.get('skip', 0, type=int)

        # Validate parameters
        if type_filter not in ['received', 'sent']:
            return error_response("INVALID_REQUEST_TYPE")

        if limit > 100:
            limit = 100
        if skip < 0:
            skip = 0

        success, message, result = relationship_service.get_friend_requests(
            current_user.get_id(), type_filter, limit, skip
        )

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Get friend requests error: {str(e)}")
        return error_response("FRIEND_REQUESTS_FAILED", status_code=500)


@social_bp.route('/users/search', methods=['POST'])
@auth_required
def search_users(current_user):
    """Search for users"""
    try:
        data = request.get_json()
        if not data:
            return error_response("SEARCH_DATA_REQUIRED")

        query = data.get('query', '').strip()
        if not query:
            return error_response("SEARCH_QUERY_REQUIRED")

        # Get pagination parameters from request body or query params
        limit = data.get('limit', request.args.get('limit', 20, type=int))
        skip = data.get('skip', request.args.get('skip', 0, type=int))

        # Validate parameters
        if limit > 50:
            limit = 50
        if skip < 0:
            skip = 0

        success, message, result = discovery_service.search_users(
            current_user.get_id(), query, limit, skip
        )

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Search users error: {str(e)}")
        return error_response("SEARCH_USERS_FAILED", status_code=500)


@social_bp.route('/users/suggestions', methods=['GET'])
@auth_required
def get_friend_suggestions(current_user):
    """Get friend suggestions"""
    try:
        limit = request.args.get('limit', 10, type=int)

        # Validate parameters
        if limit > 20:
            limit = 20
        if limit < 1:
            limit = 10

        success, message, result = discovery_service.get_friend_suggestions(
            current_user.get_id(), limit
        )

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Get friend suggestions error: {str(e)}")
        return error_response("FRIEND_SUGGESTIONS_FAILED", status_code=500)


@social_bp.route('/users/<target_user_id>/block', methods=['POST'])
@auth_required
def block_user(current_user, target_user_id):
    """Block another user"""
    try:
        if not target_user_id:
            return error_response("TARGET_USER_ID_REQUIRED")

        success, message, result = relationship_service.block_user(
            current_user.get_id(), target_user_id
        )

        if success:
            return success_response(message, result, 201)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Block user error: {str(e)}")
        return error_response("USER_BLOCK_FAILED", status_code=500)


@social_bp.route('/users/<target_user_id>/unblock', methods=['DELETE'])
@auth_required
def unblock_user(current_user, target_user_id):
    """Unblock a user"""
    try:
        if not target_user_id:
            return error_response("TARGET_USER_ID_REQUIRED")

        success, message, result = relationship_service.unblock_user(
            current_user.get_id(), target_user_id
        )

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Unblock user error: {str(e)}")
        return error_response("USER_UNBLOCK_FAILED", status_code=500)


@social_bp.route('/blocked-users', methods=['GET'])
@auth_required
def get_blocked_users(current_user):
    """Get list of blocked users"""
    try:
        # Get pagination parameters
        limit = request.args.get('limit', 50, type=int)
        skip = request.args.get('skip', 0, type=int)

        # Validate parameters
        if limit > 100:
            limit = 100
        if skip < 0:
            skip = 0

        success, message, result = relationship_service.get_blocked_users(
            current_user.get_id(), limit, skip
        )

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Get blocked users error: {str(e)}")
        return error_response("BLOCKED_USERS_FAILED", status_code=500)


@social_bp.route('/relationship-status/<target_user_id>', methods=['GET'])
@auth_required
def get_relationship_status(current_user, target_user_id):
    """Get relationship status with another user"""
    try:
        if not target_user_id:
            return error_response("TARGET_USER_ID_REQUIRED")

        # Use the discovery service to get relationship status
        relationships = discovery_service._get_relationships_status(
            current_user.get_id(), [target_user_id]
        )

        relationship_status = relationships.get(target_user_id, {
            "type": None,
            "status": None,
            "is_friend": False,
            "is_pending": False,
            "is_blocked": False,
            "initiated_by_me": False
        })

        return success_response("RELATIONSHIP_STATUS_SUCCESS", {
            "target_user_id": target_user_id,
            "relationship": relationship_status
        })

    except Exception as e:
        current_app.logger.error(f"Get relationship status error: {str(e)}")
        return error_response("RELATIONSHIP_STATUS_FAILED", status_code=500)


@social_bp.route('/stats', methods=['GET'])
@auth_required
def get_social_stats(current_user):
    """Get user's social statistics"""
    try:
        from app.social.repositories.relationship_repository import RelationshipRepository
        repo = RelationshipRepository()

        user_id = current_user.get_id()

        # Get various counts
        friends_count = repo.get_friends_count(user_id)
        pending_requests_count = repo.get_pending_requests_count(user_id)

        # Get sent requests count
        sent_requests = repo.get_sent_friend_requests(user_id)
        sent_requests_count = len(sent_requests)

        # Get blocked users count
        blocked_users = repo.get_blocked_users(user_id)
        blocked_users_count = len(blocked_users)

        stats = {
            "friends_count": friends_count,
            "pending_requests_count": pending_requests_count,
            "sent_requests_count": sent_requests_count,
            "blocked_users_count": blocked_users_count
        }

        return success_response("SOCIAL_STATS_SUCCESS", stats)

    except Exception as e:
        current_app.logger.error(f"Get social stats error: {str(e)}")
        return error_response("SOCIAL_STATS_FAILED", status_code=500)