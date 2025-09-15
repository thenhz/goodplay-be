from flask import Blueprint, request, current_app
from app.preferences.services.preferences_service import PreferencesService
from app.core.utils.decorators import auth_required
from app.core.utils.responses import success_response, error_response

preferences_blueprint = Blueprint('preferences', __name__, url_prefix='/api/preferences')
preferences_service = PreferencesService()

@preferences_blueprint.route('', methods=['GET'])
@auth_required
def get_preferences(current_user):
    """Get user preferences"""
    try:
        user_id = str(current_user._id)
        success, message, result = preferences_service.get_user_preferences(user_id)

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Get preferences endpoint error: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@preferences_blueprint.route('', methods=['PUT'])
@auth_required
def update_preferences(current_user):
    """Update user preferences"""
    try:
        data = request.get_json()

        if not data:
            return error_response("PREFERENCES_DATA_REQUIRED")

        user_id = str(current_user._id)
        success, message, result = preferences_service.update_user_preferences(user_id, data)

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Update preferences endpoint error: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@preferences_blueprint.route('/<category>', methods=['GET'])
@auth_required
def get_preferences_category(current_user, category):
    """Get preferences for a specific category"""
    try:
        user_id = str(current_user._id)
        success, message, result = preferences_service.get_preferences_category(user_id, category)

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Get preferences category endpoint error: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@preferences_blueprint.route('/<category>', methods=['PUT'])
@auth_required
def update_preferences_category(current_user, category):
    """Update preferences for a specific category"""
    try:
        data = request.get_json()

        if not data:
            return error_response("PREFERENCES_CATEGORY_DATA_REQUIRED")

        user_id = str(current_user._id)
        success, message, result = preferences_service.update_preferences_category(user_id, category, data)

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Update preferences category endpoint error: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@preferences_blueprint.route('/reset', methods=['POST'])
@auth_required
def reset_preferences(current_user):
    """Reset user preferences to default values"""
    try:
        user_id = str(current_user._id)
        success, message, result = preferences_service.reset_user_preferences(user_id)

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Reset preferences endpoint error: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@preferences_blueprint.route('/defaults', methods=['GET'])
def get_default_preferences():
    """Get default preferences template (public endpoint for UI reference)"""
    try:
        success, message, result = preferences_service.get_default_preferences()

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Get default preferences endpoint error: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

# Additional helper endpoints for specific use cases

@preferences_blueprint.route('/notifications', methods=['GET'])
@auth_required
def get_notification_preferences(current_user):
    """Get notification preferences (helper endpoint)"""
    try:
        user_id = str(current_user._id)
        success, message, result = preferences_service.get_notification_preferences(user_id)

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Get notification preferences endpoint error: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@preferences_blueprint.route('/privacy', methods=['GET'])
@auth_required
def get_privacy_preferences(current_user):
    """Get privacy preferences (helper endpoint)"""
    try:
        user_id = str(current_user._id)
        success, message, result = preferences_service.get_privacy_preferences(user_id)

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Get privacy preferences endpoint error: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)