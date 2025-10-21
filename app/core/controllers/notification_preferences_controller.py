from flask import Blueprint, request, current_app
from app.core.utils.decorators import auth_required
from app.core.utils.responses import success_response, error_response
from app.core.repositories.notification_preferences_repository import NotificationPreferencesRepository

preferences_bp = Blueprint('notification_preferences', __name__, url_prefix='/api/notifications/preferences')


@preferences_bp.route('', methods=['GET'])
@auth_required
def get_preferences(current_user):
    """Get user notification preferences"""
    try:
        repository = NotificationPreferencesRepository()
        preferences = repository.get_preferences(current_user.user_id)

        return success_response(
            "NOTIFICATION_PREFERENCES_RETRIEVED",
            {"preferences": preferences.to_dict()}
        )

    except Exception as e:
        current_app.logger.error(f"Error getting preferences: {str(e)}", exc_info=True)
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@preferences_bp.route('', methods=['PUT'])
@auth_required
def update_preferences(current_user):
    """
    Update user notification preferences.

    Body:
        {
            "push_enabled": true,
            "quiet_hours_enabled": false,
            "quiet_hours_start": "22:00",
            "quiet_hours_end": "08:00",
            "timezone": "America/New_York",
            "notification_types": {
                "invitation_received": true,
                "invitation_accepted": true,
                ...
            }
        }
    """
    try:
        data = request.get_json()
        if not data:
            return error_response("DATA_REQUIRED")

        repository = NotificationPreferencesRepository()

        # Get current preferences
        preferences = repository.get_preferences(current_user.user_id)

        # Update fields if provided
        if 'push_enabled' in data:
            preferences.push_enabled = data['push_enabled']

        if 'quiet_hours_enabled' in data:
            preferences.quiet_hours_enabled = data['quiet_hours_enabled']

        if 'quiet_hours_start' in data:
            # Validate format
            from datetime import datetime
            try:
                datetime.strptime(data['quiet_hours_start'], '%H:%M')
                preferences.quiet_hours_start = data['quiet_hours_start']
            except ValueError:
                return error_response("INVALID_TIME_FORMAT")

        if 'quiet_hours_end' in data:
            from datetime import datetime
            try:
                datetime.strptime(data['quiet_hours_end'], '%H:%M')
                preferences.quiet_hours_end = data['quiet_hours_end']
            except ValueError:
                return error_response("INVALID_TIME_FORMAT")

        if 'timezone' in data:
            # Validate timezone
            import pytz
            try:
                pytz.timezone(data['timezone'])
                preferences.timezone = data['timezone']
            except pytz.exceptions.UnknownTimeZoneError:
                return error_response("INVALID_TIMEZONE")

        if 'notification_types' in data:
            # Merge with existing notification types
            if isinstance(data['notification_types'], dict):
                preferences.notification_types.update(data['notification_types'])
            else:
                return error_response("NOTIFICATION_TYPES_MUST_BE_OBJECT")

        # Save preferences
        if repository.update_preferences(preferences):
            current_app.logger.info(
                f"Notification preferences updated for user {current_user.user_id}"
            )
            return success_response(
                "NOTIFICATION_PREFERENCES_UPDATED",
                {"preferences": preferences.to_dict()}
            )
        else:
            return error_response("PREFERENCES_UPDATE_FAILED", status_code=500)

    except ValueError as ve:
        return error_response(str(ve), status_code=400)
    except Exception as e:
        current_app.logger.error(f"Error updating preferences: {str(e)}", exc_info=True)
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@preferences_bp.route('/reset', methods=['POST'])
@auth_required
def reset_preferences(current_user):
    """Reset preferences to defaults"""
    try:
        repository = NotificationPreferencesRepository()

        if repository.reset_preferences(current_user.user_id):
            preferences = repository.get_preferences(current_user.user_id)

            current_app.logger.info(
                f"Notification preferences reset for user {current_user.user_id}"
            )

            return success_response(
                "NOTIFICATION_PREFERENCES_RESET",
                {"preferences": preferences.to_dict()}
            )
        else:
            return error_response("PREFERENCES_RESET_FAILED", status_code=500)

    except Exception as e:
        current_app.logger.error(f"Error resetting preferences: {str(e)}", exc_info=True)
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)
