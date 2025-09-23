from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.core.utils.decorators import auth_required, admin_required
from app.core.utils.responses import success_response, error_response

from ..services.challenge_service import ChallengeService
from ..services.matchmaking_service import MatchmakingService

challenges_bp = Blueprint('challenges', __name__, url_prefix='/api/challenges')

challenge_service = ChallengeService()
matchmaking_service = MatchmakingService()

@challenges_bp.route('/', methods=['POST'])
@auth_required
def create_challenge(current_user):
    """Create a new challenge"""
    try:
        data = request.get_json()
        if not data:
            return error_response("DATA_REQUIRED")

        challenge_type = data.get('challenge_type', '1v1')
        game_id = data.get('game_id')

        if not game_id:
            return error_response("GAME_ID_REQUIRED")

        user_id = current_user.get('id')

        if challenge_type == '1v1':
            challenged_id = data.get('challenged_id')
            if not challenged_id:
                return error_response("CHALLENGED_ID_REQUIRED")

            timeout_minutes = data.get('timeout_minutes', 60)
            game_config = data.get('game_config', {})

            success, message, result = challenge_service.create_1v1_challenge(
                challenger_id=user_id,
                challenged_id=challenged_id,
                game_id=game_id,
                timeout_minutes=timeout_minutes,
                game_config=game_config
            )

        elif challenge_type == 'NvN':
            max_participants = data.get('max_participants', 4)
            min_participants = data.get('min_participants')
            timeout_minutes = data.get('timeout_minutes', 60)
            game_config = data.get('game_config', {})

            success, message, result = challenge_service.create_nvn_challenge(
                challenger_id=user_id,
                max_participants=max_participants,
                game_id=game_id,
                min_participants=min_participants,
                timeout_minutes=timeout_minutes,
                game_config=game_config
            )

        else:
            return error_response("INVALID_CHALLENGE_TYPE")

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@challenges_bp.route('/public', methods=['GET'])
def get_public_challenges():
    """Get available public challenges"""
    try:
        game_id = request.args.get('game_id')
        limit = int(request.args.get('limit', 20))

        success, message, data = challenge_service.get_public_challenges(game_id, limit)

        if success:
            return success_response(message, data)
        else:
            return error_response(message)

    except ValueError:
        return error_response("INVALID_LIMIT_VALUE")
    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@challenges_bp.route('/<challenge_id>/join', methods=['POST'])
@auth_required
def join_challenge(current_user, challenge_id):
    """Join a public challenge"""
    try:
        user_id = current_user.get('id')

        success, message, data = challenge_service.join_public_challenge(user_id, challenge_id)

        if success:
            return success_response(message, data)
        else:
            return error_response(message)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@challenges_bp.route('/<challenge_id>/accept', methods=['POST'])
@auth_required
def accept_invitation(current_user, challenge_id):
    """Accept a challenge invitation"""
    try:
        user_id = current_user.get('id')

        success, message, data = challenge_service.accept_challenge_invitation(user_id, challenge_id)

        if success:
            return success_response(message, data)
        else:
            return error_response(message)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@challenges_bp.route('/<challenge_id>/decline', methods=['POST'])
@auth_required
def decline_invitation(current_user, challenge_id):
    """Decline a challenge invitation"""
    try:
        user_id = current_user.get('id')

        success, message, data = challenge_service.decline_challenge_invitation(user_id, challenge_id)

        if success:
            return success_response(message, data)
        else:
            return error_response(message)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@challenges_bp.route('/<challenge_id>/start', methods=['POST'])
@auth_required
def start_participation(current_user, challenge_id):
    """Start participation in a challenge"""
    try:
        data = request.get_json() or {}
        user_id = current_user.get('id')
        game_session_id = data.get('game_session_id')

        if not game_session_id:
            return error_response("GAME_SESSION_ID_REQUIRED")

        success, message, result = challenge_service.start_challenge_participation(
            user_id, challenge_id, game_session_id
        )

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@challenges_bp.route('/<challenge_id>/complete', methods=['POST'])
@auth_required
def complete_participation(current_user, challenge_id):
    """Complete participation in a challenge"""
    try:
        data = request.get_json()
        if not data:
            return error_response("DATA_REQUIRED")

        user_id = current_user.get('id')
        score = data.get('score')
        performance_data = data.get('performance_data', {})

        if score is None:
            return error_response("SCORE_REQUIRED")

        success, message, result = challenge_service.complete_challenge_participation(
            user_id, challenge_id, score, performance_data
        )

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@challenges_bp.route('/my', methods=['GET'])
@auth_required
def get_my_challenges(current_user):
    """Get challenges for the current user"""
    try:
        user_id = current_user.get('id')
        status = request.args.get('status')
        limit = int(request.args.get('limit', 50))

        success, message, data = challenge_service.get_user_challenges(user_id, status, limit)

        if success:
            return success_response(message, data)
        else:
            return error_response(message)

    except ValueError:
        return error_response("INVALID_LIMIT_VALUE")
    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

# Matchmaking endpoints

@challenges_bp.route('/matchmaking/find-opponent', methods=['POST'])
@auth_required
def find_opponent(current_user):
    """Find an opponent for matchmaking"""
    try:
        data = request.get_json()
        if not data:
            return error_response("DATA_REQUIRED")

        user_id = current_user.get('id')
        game_id = data.get('game_id')
        challenge_type = data.get('challenge_type', '1v1')
        skill_range = data.get('skill_range', 100)

        if not game_id:
            return error_response("GAME_ID_REQUIRED")

        success, message, result = matchmaking_service.find_opponent(
            user_id, game_id, challenge_type, skill_range
        )

        if success:
            return success_response(message, result)
        else:
            return error_response(message, result)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@challenges_bp.route('/matchmaking/quick-match', methods=['POST'])
@auth_required
def quick_match(current_user):
    """Find a quick match"""
    try:
        data = request.get_json()
        if not data:
            return error_response("DATA_REQUIRED")

        user_id = current_user.get('id')
        game_id = data.get('game_id')

        if not game_id:
            return error_response("GAME_ID_REQUIRED")

        success, message, result = matchmaking_service.find_quick_match(user_id, game_id)

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@challenges_bp.route('/matchmaking/recommendations', methods=['GET'])
@auth_required
def get_recommendations(current_user):
    """Get recommended opponents"""
    try:
        user_id = current_user.get('id')
        game_id = request.args.get('game_id')
        limit = int(request.args.get('limit', 10))

        if not game_id:
            return error_response("GAME_ID_REQUIRED")

        success, message, data = matchmaking_service.get_recommended_opponents(user_id, game_id, limit)

        if success:
            return success_response(message, data)
        else:
            return error_response(message)

    except ValueError:
        return error_response("INVALID_LIMIT_VALUE")
    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@challenges_bp.route('/matchmaking/statistics', methods=['GET'])
@auth_required
def get_matchmaking_statistics(current_user):
    """Get matchmaking statistics for the current user"""
    try:
        user_id = current_user.get('id')

        success, message, data = matchmaking_service.get_matchmaking_statistics(user_id)

        if success:
            return success_response(message, data)
        else:
            return error_response(message)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

# Admin endpoints

@challenges_bp.route('/admin/statistics', methods=['GET'])
@admin_required
def get_admin_statistics(current_user):
    """Get challenge statistics for admins"""
    try:
        game_id = request.args.get('game_id')
        days_back = int(request.args.get('days_back', 30))

        from ..repositories.challenge_repository import ChallengeRepository
        challenge_repo = ChallengeRepository()
        stats = challenge_repo.get_challenge_statistics(game_id, days_back)

        return success_response("CHALLENGE_STATISTICS_RETRIEVED", stats)

    except ValueError:
        return error_response("INVALID_DAYS_BACK_VALUE")
    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@challenges_bp.route('/admin/cleanup', methods=['POST'])
@admin_required
def cleanup_old_challenges(current_user):
    """Clean up old challenge data"""
    try:
        data = request.get_json() or {}
        days_old = data.get('days_old', 90)

        from ..repositories.challenge_repository import ChallengeRepository
        from ..repositories.challenge_participant_repository import ChallengeParticipantRepository

        challenge_repo = ChallengeRepository()
        participant_repo = ChallengeParticipantRepository()

        deleted_challenges = challenge_repo.cleanup_old_challenges(days_old)
        deleted_participants = participant_repo.cleanup_old_participants(days_old)

        return success_response("CLEANUP_COMPLETED", {
            "deleted_challenges": deleted_challenges,
            "deleted_participants": deleted_participants,
            "days_old": days_old
        })

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@challenges_bp.route('/admin/expire-old', methods=['POST'])
@admin_required
def expire_old_challenges(current_user):
    """Expire old pending/active challenges"""
    try:
        data = request.get_json() or {}
        hours_old = data.get('hours_old', 24)

        from ..repositories.challenge_repository import ChallengeRepository
        challenge_repo = ChallengeRepository()

        expired_count = challenge_repo.expire_old_challenges(hours_old)

        return success_response("OLD_CHALLENGES_EXPIRED", {
            "expired_count": expired_count,
            "hours_old": hours_old
        })

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)