"""
WebSocket Authentication Controller

Generates and refreshes WebSocket authentication tokens.
"""

from flask import Blueprint, current_app
from datetime import datetime, timedelta
from app.core.utils.decorators import auth_required
from app.core.utils.responses import success_response, error_response
from app.core.services.auth_service import AuthService


blueprint = Blueprint('websocket_auth', __name__)


@blueprint.route('/websocket-token', methods=['POST'])
@auth_required
def generate_websocket_token(current_user):
    """
    Generate WebSocket authentication token.

    Response:
        {
            "success": true,
            "message": "WEBSOCKET_TOKEN_GENERATED",
            "data": {
                "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "expires_in": 3600,
                "token_type": "Bearer"
            }
        }
    """
    try:
        # Generate WebSocket-specific token (1 hour expiry)
        token = AuthService.generate_websocket_token(current_user)

        return success_response("WEBSOCKET_TOKEN_GENERATED", {
            "token": token,
            "expires_in": 3600,  # 1 hour in seconds
            "token_type": "Bearer"
        })

    except Exception as e:
        current_app.logger.error(f"Error generating WebSocket token: {str(e)}", exc_info=True)
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@blueprint.route('/websocket-token/refresh', methods=['POST'])
@auth_required
def refresh_websocket_token(current_user):
    """
    Refresh WebSocket authentication token.

    Response:
        {
            "success": true,
            "message": "WEBSOCKET_TOKEN_REFRESHED",
            "data": {
                "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "expires_in": 3600,
                "token_type": "Bearer"
            }
        }
    """
    try:
        # Generate new token
        token = AuthService.generate_websocket_token(current_user)

        return success_response("WEBSOCKET_TOKEN_REFRESHED", {
            "token": token,
            "expires_in": 3600,  # 1 hour in seconds
            "token_type": "Bearer"
        })

    except Exception as e:
        current_app.logger.error(f"Error refreshing WebSocket token: {str(e)}", exc_info=True)
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)
