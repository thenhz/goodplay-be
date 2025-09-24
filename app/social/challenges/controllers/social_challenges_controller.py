from flask import Blueprint, request, current_app
from flask_jwt_extended import get_jwt_identity

from app.core.utils.decorators import auth_required
from app.core.utils.responses import success_response, error_response, validation_error_response
from app.social.challenges.services.social_challenge_manager import SocialChallengeManager
from app.social.challenges.services.social_matchmaking_service import SocialMatchmakingService
from app.social.challenges.services.interaction_service import InteractionService
from app.social.challenges.services.reward_service import RewardService
from app.social.challenges.engines.challenge_engine import ChallengeEngine

social_challenges_bp = Blueprint('social_challenges', __name__)

# Initialize services
challenge_manager = SocialChallengeManager()
matchmaking_service = SocialMatchmakingService()
interaction_service = InteractionService()
reward_service = RewardService()
challenge_engine = ChallengeEngine()


# Challenge Management Endpoints

@social_challenges_bp.route('', methods=['POST'])
@auth_required
def create_challenge():
    """Create a new social challenge"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()

        if not data:
            return error_response("CHALLENGE_DATA_REQUIRED")

        success, message, result = challenge_manager.create_challenge(current_user_id, data)

        if success:
            return success_response(message, result, 201)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Create challenge endpoint error: {str(e)}")
        return error_response("CHALLENGE_CREATION_FAILED", status_code=500)


@social_challenges_bp.route('/templates', methods=['GET'])
@auth_required
def get_challenge_templates():
    """Get available challenge templates"""
    try:
        templates = challenge_engine.get_challenge_templates()
        return success_response("CHALLENGE_TEMPLATES_RETRIEVED", templates)

    except Exception as e:
        current_app.logger.error(f"Get templates endpoint error: {str(e)}")
        return error_response("TEMPLATES_RETRIEVAL_FAILED", status_code=500)


@social_challenges_bp.route('/templates/<template_type>/<template_category>', methods=['POST'])
@auth_required
def create_from_template(template_type, template_category):
    """Create challenge from template"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json() or {}

        success, message, challenge = challenge_engine.create_challenge_from_template(
            current_user_id, template_type, template_category, data
        )

        if success and challenge:
            # Save challenge using manager
            challenge_data = challenge.to_dict()
            save_success, save_message, save_result = challenge_manager.create_challenge(
                current_user_id, challenge_data
            )

            if save_success:
                return success_response(save_message, save_result, 201)
            else:
                return error_response(save_message)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Create from template endpoint error: {str(e)}")
        return error_response("TEMPLATE_CREATION_FAILED", status_code=500)


@social_challenges_bp.route('/<challenge_id>', methods=['GET'])
@auth_required
def get_challenge_details(challenge_id):
    """Get detailed challenge information"""
    try:
        current_user_id = get_jwt_identity()

        success, message, result = challenge_manager.get_challenge_details(challenge_id, current_user_id)

        if success:
            return success_response(message, result)
        else:
            return error_response(message, status_code=404 if "not found" in message.lower() else 400)

    except Exception as e:
        current_app.logger.error(f"Get challenge details endpoint error: {str(e)}")
        return error_response("CHALLENGE_DETAILS_FAILED", status_code=500)


@social_challenges_bp.route('/<challenge_id>/join', methods=['POST'])
@auth_required
def join_challenge(challenge_id):
    """Join a social challenge"""
    try:
        current_user_id = get_jwt_identity()

        success, message, result = challenge_manager.join_challenge(challenge_id, current_user_id)

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Join challenge endpoint error: {str(e)}")
        return error_response("CHALLENGE_JOIN_FAILED", status_code=500)


@social_challenges_bp.route('/<challenge_id>/leave', methods=['POST'])
@auth_required
def leave_challenge(challenge_id):
    """Leave a social challenge"""
    try:
        current_user_id = get_jwt_identity()

        success, message, result = challenge_manager.leave_challenge(challenge_id, current_user_id)

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Leave challenge endpoint error: {str(e)}")
        return error_response("CHALLENGE_LEAVE_FAILED", status_code=500)


@social_challenges_bp.route('/<challenge_id>/invite', methods=['POST'])
@auth_required
def invite_users(challenge_id):
    """Invite users to a challenge"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()

        if not data or 'user_ids' not in data:
            return error_response("USER_IDS_REQUIRED")

        user_ids = data.get('user_ids', [])
        if not isinstance(user_ids, list):
            return error_response("USER_IDS_MUST_BE_LIST")

        success, message, result = challenge_manager.invite_users(challenge_id, current_user_id, user_ids)

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Invite users endpoint error: {str(e)}")
        return error_response("INVITATION_FAILED", status_code=500)


@social_challenges_bp.route('/<challenge_id>/start', methods=['POST'])
@auth_required
def start_challenge(challenge_id):
    """Start a challenge"""
    try:
        current_user_id = get_jwt_identity()

        success, message, result = challenge_manager.start_challenge(challenge_id, current_user_id)

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Start challenge endpoint error: {str(e)}")
        return error_response("CHALLENGE_START_FAILED", status_code=500)


@social_challenges_bp.route('/<challenge_id>/progress', methods=['POST'])
@auth_required
def update_progress(challenge_id):
    """Update user's progress in challenge"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()

        if not data:
            return error_response("PROGRESS_DATA_REQUIRED")

        success, message, result = challenge_manager.update_progress(challenge_id, current_user_id, data)

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Update progress endpoint error: {str(e)}")
        return error_response("PROGRESS_UPDATE_FAILED", status_code=500)


# Discovery and Matchmaking Endpoints

@social_challenges_bp.route('/discover/public', methods=['GET'])
@auth_required
def discover_public_challenges():
    """Discover public challenges"""
    try:
        current_user_id = get_jwt_identity()

        # Get query parameters
        challenge_type = request.args.get('type')
        limit = int(request.args.get('limit', 20))
        offset = int(request.args.get('offset', 0))

        filters = {}
        if challenge_type:
            filters['challenge_type'] = challenge_type

        success, message, result = matchmaking_service.discover_public_challenges(
            current_user_id, filters, limit, offset
        )

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Discover public challenges endpoint error: {str(e)}")
        return error_response("DISCOVERY_FAILED", status_code=500)


@social_challenges_bp.route('/discover/friends', methods=['GET'])
@auth_required
def discover_friend_challenges():
    """Discover challenges from friends"""
    try:
        current_user_id = get_jwt_identity()

        # Get friend IDs from query or request body
        friend_ids = request.args.getlist('friend_ids') or []
        limit = int(request.args.get('limit', 20))
        offset = int(request.args.get('offset', 0))

        success, message, result = matchmaking_service.discover_friend_challenges(
            current_user_id, friend_ids, limit, offset
        )

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Discover friend challenges endpoint error: {str(e)}")
        return error_response("FRIEND_DISCOVERY_FAILED", status_code=500)


@social_challenges_bp.route('/discover/recommended', methods=['GET'])
@auth_required
def get_recommended_challenges():
    """Get personalized challenge recommendations"""
    try:
        current_user_id = get_jwt_identity()
        limit = int(request.args.get('limit', 10))

        success, message, result = matchmaking_service.get_recommended_challenges(current_user_id, limit)

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Get recommendations endpoint error: {str(e)}")
        return error_response("RECOMMENDATIONS_FAILED", status_code=500)


@social_challenges_bp.route('/search', methods=['GET'])
@auth_required
def search_challenges():
    """Search challenges by text query"""
    try:
        current_user_id = get_jwt_identity()

        query = request.args.get('q', '').strip()
        if not query:
            return error_response("SEARCH_QUERY_REQUIRED")

        challenge_type = request.args.get('type')
        difficulty = request.args.get('difficulty')
        limit = int(request.args.get('limit', 20))
        offset = int(request.args.get('offset', 0))

        filters = {}
        if challenge_type:
            filters['challenge_type'] = challenge_type
        if difficulty:
            filters['difficulty_level'] = int(difficulty)

        success, message, result = matchmaking_service.search_challenges(
            current_user_id, query, filters, limit, offset
        )

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Search challenges endpoint error: {str(e)}")
        return error_response("SEARCH_FAILED", status_code=500)


@social_challenges_bp.route('/trending', methods=['GET'])
@auth_required
def get_trending_challenges():
    """Get trending challenges"""
    try:
        current_user_id = get_jwt_identity()
        limit = int(request.args.get('limit', 10))

        success, message, result = matchmaking_service.get_trending_challenges(current_user_id, limit)

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Get trending challenges endpoint error: {str(e)}")
        return error_response("TRENDING_FAILED", status_code=500)


# Social Interaction Endpoints

@social_challenges_bp.route('/<challenge_id>/cheer', methods=['POST'])
@auth_required
def send_cheer(challenge_id):
    """Send a cheer to another participant"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()

        if not data or 'to_user_id' not in data:
            return error_response("TARGET_USER_REQUIRED")

        to_user_id = data.get('to_user_id')
        emoji = data.get('emoji', '👏')
        reaction_type = data.get('reaction_type', 'cheer')

        success, message, result = interaction_service.send_cheer(
            challenge_id, current_user_id, to_user_id, emoji, reaction_type
        )

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Send cheer endpoint error: {str(e)}")
        return error_response("CHEER_FAILED", status_code=500)


@social_challenges_bp.route('/<challenge_id>/comment', methods=['POST'])
@auth_required
def send_comment(challenge_id):
    """Send a comment to another participant"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()

        if not data or 'to_user_id' not in data or 'content' not in data:
            return error_response("COMMENT_DATA_REQUIRED")

        to_user_id = data.get('to_user_id')
        content = data.get('content', '').strip()
        context_type = data.get('context_type', 'general')
        context_data = data.get('context_data', {})

        success, message, result = interaction_service.send_comment(
            challenge_id, current_user_id, to_user_id, content, context_type, context_data
        )

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Send comment endpoint error: {str(e)}")
        return error_response("COMMENT_FAILED", status_code=500)


@social_challenges_bp.route('/<challenge_id>/activity', methods=['GET'])
@auth_required
def get_activity_feed(challenge_id):
    """Get challenge activity feed"""
    try:
        current_user_id = get_jwt_identity()
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))

        success, message, result = interaction_service.get_challenge_activity_feed(
            challenge_id, current_user_id, limit, offset
        )

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Get activity feed endpoint error: {str(e)}")
        return error_response("ACTIVITY_FEED_FAILED", status_code=500)


@social_challenges_bp.route('/interactions/<interaction_id>/like', methods=['POST'])
@auth_required
def like_interaction(interaction_id):
    """Like an interaction"""
    try:
        current_user_id = get_jwt_identity()

        success, message, result = interaction_service.like_interaction(interaction_id, current_user_id)

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Like interaction endpoint error: {str(e)}")
        return error_response("LIKE_FAILED", status_code=500)


@social_challenges_bp.route('/interactions/<interaction_id>/unlike', methods=['POST'])
@auth_required
def unlike_interaction(interaction_id):
    """Remove like from an interaction"""
    try:
        current_user_id = get_jwt_identity()

        success, message, result = interaction_service.unlike_interaction(interaction_id, current_user_id)

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Unlike interaction endpoint error: {str(e)}")
        return error_response("UNLIKE_FAILED", status_code=500)


@social_challenges_bp.route('/interactions/<interaction_id>/reply', methods=['POST'])
@auth_required
def reply_to_interaction(interaction_id):
    """Reply to an interaction"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()

        if not data or 'content' not in data:
            return error_response("REPLY_CONTENT_REQUIRED")

        content = data.get('content', '').strip()

        success, message, result = interaction_service.reply_to_interaction(
            interaction_id, current_user_id, content
        )

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Reply to interaction endpoint error: {str(e)}")
        return error_response("REPLY_FAILED", status_code=500)


# User Dashboard Endpoints

@social_challenges_bp.route('/my', methods=['GET'])
@auth_required
def get_my_challenges():
    """Get user's challenges"""
    try:
        current_user_id = get_jwt_identity()

        include_completed = request.args.get('include_completed', 'false').lower() == 'true'
        limit = int(request.args.get('limit', 20))
        offset = int(request.args.get('offset', 0))

        success, message, result = challenge_manager.get_user_challenges(
            current_user_id, include_completed, limit, offset
        )

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Get my challenges endpoint error: {str(e)}")
        return error_response("MY_CHALLENGES_FAILED", status_code=500)


@social_challenges_bp.route('/<challenge_id>/achievements', methods=['GET'])
@auth_required
def get_challenge_achievements(challenge_id):
    """Get user achievements for specific challenge"""
    try:
        current_user_id = get_jwt_identity()

        success, message, result = reward_service.get_user_achievements(current_user_id, challenge_id)

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Get achievements endpoint error: {str(e)}")
        return error_response("ACHIEVEMENTS_FAILED", status_code=500)


@social_challenges_bp.route('/<challenge_id>/leaderboard', methods=['GET'])
@auth_required
def get_challenge_leaderboard(challenge_id):
    """Get challenge leaderboard with rewards"""
    try:
        limit = int(request.args.get('limit', 10))

        success, message, result = reward_service.get_leaderboard_rewards(challenge_id, limit)

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Get leaderboard endpoint error: {str(e)}")
        return error_response("LEADERBOARD_FAILED", status_code=500)


# Admin/Management Endpoints

@social_challenges_bp.route('/<challenge_id>/cancel', methods=['POST'])
@auth_required
def cancel_challenge(challenge_id):
    """Cancel a challenge (creator only)"""
    try:
        current_user_id = get_jwt_identity()

        success, message, result = challenge_manager.cancel_challenge(challenge_id, current_user_id)

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Cancel challenge endpoint error: {str(e)}")
        return error_response("CANCEL_FAILED", status_code=500)


@social_challenges_bp.route('/cleanup/expired', methods=['POST'])
@auth_required  # Would typically require admin privileges
def cleanup_expired_challenges():
    """Cleanup expired challenges"""
    try:
        success, message, result = challenge_manager.cleanup_expired_challenges()

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Cleanup expired challenges endpoint error: {str(e)}")
        return error_response("CLEANUP_FAILED", status_code=500)