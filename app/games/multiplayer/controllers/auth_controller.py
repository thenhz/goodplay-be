from flask import Blueprint, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.core.utils.decorators import auth_required
from app.core.utils.responses import success_response, error_response
from app.core.services.auth_service import AuthService


blueprint = Blueprint('multiplayer_auth', __name__)


@blueprint.route('/websocket-token', methods=['POST'])
@jwt_required()
def get_websocket_token():
    """
    Generate a WebSocket-specific authentication token.

    WebSocket tokens have longer expiry (24 hours) and include a 'type' claim
    for additional validation.

    Headers:
        Authorization: Bearer <access_token>

    Response:
        {
            "token": "<websocket_jwt_token>",
            "expires_in": 86400,
            "message": "WEBSOCKET_TOKEN_GENERATED"
        }

    Error Response:
        {
            "message": "TOKEN_GENERATION_FAILED"
        }
    """
    try:
        user_id = get_jwt_identity()

        if not user_id:
            return error_response("USER_NOT_FOUND", status_code=401)

        # Generate WebSocket token (24 hours expiry)
        ws_token = AuthService.generate_websocket_token(user_id, expires_hours=24)

        current_app.logger.info(f"WebSocket token generated for user {user_id}")

        return success_response("WEBSOCKET_TOKEN_GENERATED", {
            'token': ws_token,
            'expires_in': 86400,  # 24 hours in seconds
            'token_type': 'websocket'
        })

    except Exception as e:
        current_app.logger.error(f"WebSocket token generation failed: {str(e)}", exc_info=True)
        return error_response("TOKEN_GENERATION_FAILED", status_code=500)


@blueprint.route('/websocket-token/refresh', methods=['POST'])
@jwt_required()
def refresh_websocket_token():
    """
    Refresh an existing WebSocket token.

    Similar to getting a new token, but used for explicit token refresh flow.

    Headers:
        Authorization: Bearer <access_token>

    Response:
        {
            "token": "<new_websocket_jwt_token>",
            "expires_in": 86400,
            "message": "WEBSOCKET_TOKEN_REFRESHED"
        }
    """
    try:
        user_id = get_jwt_identity()

        if not user_id:
            return error_response("USER_NOT_FOUND", status_code=401)

        # Generate new WebSocket token
        ws_token = AuthService.generate_websocket_token(user_id, expires_hours=24)

        current_app.logger.info(f"WebSocket token refreshed for user {user_id}")

        return success_response("WEBSOCKET_TOKEN_REFRESHED", {
            'token': ws_token,
            'expires_in': 86400,
            'token_type': 'websocket'
        })

    except Exception as e:
        current_app.logger.error(f"WebSocket token refresh failed: {str(e)}", exc_info=True)
        return error_response("TOKEN_REFRESH_FAILED", status_code=500)
