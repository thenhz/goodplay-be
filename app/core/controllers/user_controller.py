from flask import Blueprint, request, current_app

from app.core.services.user_service import UserService
from app.core.utils.decorators import auth_required
from app.core.utils.responses import success_response, error_response

user_bp = Blueprint('user', __name__)
user_service = UserService()

@user_bp.route('/profile', methods=['GET'])
@auth_required
def get_profile(current_user):
    try:
        return success_response(
            "User profile retrieved",
            {"user": current_user.to_dict()}
        )

    except Exception as e:
        current_app.logger.error(f"Get profile endpoint error: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@user_bp.route('/profile', methods=['PUT'])
@auth_required
def update_profile(current_user):
    try:
        data = request.get_json()

        if not data:
            return error_response("DATA_REQUIRED")

        success, message, result = user_service.update_user_profile(
            current_user.get_id(), data
        )

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Update profile endpoint error: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@user_bp.route('/social-profile', methods=['PUT'])
@auth_required
def update_social_profile(current_user):
    try:
        data = request.get_json()

        if not data:
            return error_response("DATA_REQUIRED")

        success, message, result = user_service.update_social_profile(
            current_user.get_id(), data
        )

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Update social profile endpoint error: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@user_bp.route('/gaming-stats', methods=['GET'])
@auth_required
def get_gaming_stats(current_user):
    try:
        success, message, result = user_service.get_user_gaming_stats(
            current_user.get_id()
        )

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Get gaming stats endpoint error: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@user_bp.route('/wallet', methods=['GET'])
@auth_required
def get_wallet(current_user):
    try:
        success, message, result = user_service.get_user_wallet(
            current_user.get_id()
        )

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Get wallet endpoint error: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@user_bp.route('/gaming-stats', methods=['PUT'])
@auth_required
def update_gaming_stats(current_user):
    try:
        data = request.get_json()

        if not data:
            return error_response("DATA_REQUIRED")

        play_time = data.get('play_time', 0)
        game_category = data.get('game_category')

        success, message, result = user_service.update_gaming_stats(
            current_user.get_id(), play_time, game_category
        )

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Update gaming stats endpoint error: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@user_bp.route('/credits', methods=['POST'])
@auth_required
def add_credits(current_user):
    try:
        data = request.get_json()

        if not data:
            return error_response("DATA_REQUIRED")

        amount = data.get('amount', 0)
        transaction_type = data.get('transaction_type', 'earned')

        success, message, result = user_service.add_user_credits(
            current_user.get_id(), amount, transaction_type
        )

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Add credits endpoint error: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@user_bp.route('/donate', methods=['POST'])
@auth_required
def donate_credits(current_user):
    try:
        data = request.get_json()

        if not data:
            return error_response("DATA_REQUIRED")

        amount = data.get('amount', 0)
        onlus_id = data.get('onlus_id')

        success, message, result = user_service.donate_user_credits(
            current_user.get_id(), amount, onlus_id
        )

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Donate credits endpoint error: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)