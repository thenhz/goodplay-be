import uuid
from flask import Blueprint, request, current_app
from app.core.utils.decorators import auth_required
from app.core.utils.responses import success_response, error_response
from app.core.models.device_token import DeviceToken
from app.core.repositories.device_token_repository import DeviceTokenRepository

device_bp = Blueprint('device', __name__, url_prefix='/api/devices')


@device_bp.route('/register', methods=['POST'])
@auth_required
def register_device(current_user):
    """
    Register device for push notifications (FCM).

    Supports iOS and Android platforms only (no web support).
    Updates existing token if device_id matches.

    Body:
        {
            "device_token": "fcm_token_string",
            "platform": "android|ios",
            "device_id": "unique_device_id" (optional),
            "device_info": {
                "model": "iPhone 14 Pro",
                "os_version": "iOS 17.0",
                "app_version": "1.0.0"
            }
        }
    """
    try:
        data = request.get_json()
        if not data:
            return error_response("DATA_REQUIRED")

        # Validate required fields
        device_token_str = data.get('device_token')
        platform = data.get('platform')

        if not device_token_str:
            return error_response("DEVICE_TOKEN_REQUIRED")

        if not platform:
            return error_response("PLATFORM_REQUIRED")

        # Validate platform (only android/ios allowed)
        if platform not in DeviceToken.VALID_PLATFORMS:
            return error_response("PLATFORM_INVALID")

        # Get or generate device_id
        device_id = data.get('device_id')
        if not device_id:
            device_id = f"device_{uuid.uuid4().hex[:12]}"

        # Check if we need to update existing token for this device
        repository = DeviceTokenRepository()

        # First, check if device_id already exists for this user
        existing_tokens = repository.get_user_tokens(current_user.user_id)
        existing_device = None
        for token in existing_tokens:
            if hasattr(token, 'device_id') and token.device_id == device_id:
                existing_device = token
                break

        if existing_device:
            # Update existing device token
            existing_device.device_token = device_token_str
            existing_device.platform = platform
            existing_device.device_info = data.get('device_info', {})
            existing_device.update_last_used()

            if repository.create_token(existing_device):  # create_token handles updates
                current_app.logger.info(
                    f"Device token updated for user {current_user.user_id}, device {device_id}"
                )
            else:
                return error_response("DEVICE_REGISTRATION_FAILED", status_code=500)
        else:
            # Create new device token
            device_token = DeviceToken(
                token_id=str(uuid.uuid4()),
                user_id=current_user.user_id,
                device_token=device_token_str,
                platform=platform,
                device_id=device_id,
                device_info=data.get('device_info', {})
            )

            if not repository.create_token(device_token):
                return error_response("DEVICE_REGISTRATION_FAILED", status_code=500)

            current_app.logger.info(
                f"Device token registered for user {current_user.user_id}, device {device_id}"
            )

        # Return response matching OpenAPI spec
        registered_at = existing_device.last_used_at if existing_device else device_token.created_at
        return success_response(
            "DEVICE_REGISTERED_SUCCESS",
            {
                "device_id": device_id,
                "device_token": device_token_str,
                "registered_at": registered_at
            }
        )

    except ValueError as ve:
        return error_response(str(ve), status_code=400)
    except Exception as e:
        current_app.logger.error(f"Error registering device token: {str(e)}", exc_info=True)
        return error_response("DEVICE_REGISTRATION_FAILED", status_code=500)


@device_bp.route('/unregister', methods=['DELETE'])
@auth_required
def unregister_device(current_user):
    """
    Unregister device (delete FCM token).

    Remove device token to stop receiving push notifications.
    Called on logout.

    Body:
        {
            "device_token": "fcm_token_string" (optional if device_id provided),
            "device_id": "device_id" (optional if device_token provided)
        }
    """
    try:
        data = request.get_json()
        if not data:
            return error_response("DATA_REQUIRED")

        device_token_str = data.get('device_token')
        device_id = data.get('device_id')

        # At least one identifier required
        if not device_token_str and not device_id:
            return error_response("DEVICE_TOKEN_OR_ID_REQUIRED")

        repository = DeviceTokenRepository()
        deleted = False

        if device_token_str:
            # Delete by device token
            deleted = repository.delete_token_by_device_token(device_token_str)
            if deleted:
                current_app.logger.info(
                    f"Device unregistered by token for user {current_user.user_id}"
                )
        elif device_id:
            # Delete by device_id
            # Find the token with this device_id for the user
            user_tokens = repository.get_user_tokens(current_user.user_id)
            for token in user_tokens:
                if hasattr(token, 'device_id') and token.device_id == device_id:
                    deleted = repository.delete_token(token.token_id, current_user.user_id)
                    if deleted:
                        current_app.logger.info(
                            f"Device unregistered by device_id {device_id} for user {current_user.user_id}"
                        )
                    break

        if deleted:
            return success_response("DEVICE_UNREGISTERED_SUCCESS")
        else:
            return error_response("DEVICE_TOKEN_OR_ID_REQUIRED", status_code=400)

    except Exception as e:
        current_app.logger.error(f"Error unregistering device: {str(e)}", exc_info=True)
        return error_response("DEVICE_REGISTRATION_FAILED", status_code=500)