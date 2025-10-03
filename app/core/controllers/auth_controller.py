from flask import Blueprint, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.core.services.auth_service import AuthService
from app.core.utils.decorators import auth_required
from app.core.utils.responses import success_response, error_response

auth_bp = Blueprint('auth', __name__)
auth_service = AuthService()

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        if not data:
            return error_response("DATA_REQUIRED")
        
        email = data.get('email', '').strip()
        password = data.get('password', '').strip()
        first_name = data.get('first_name', '').strip() if data.get('first_name') else None
        last_name = data.get('last_name', '').strip() if data.get('last_name') else None
        
        success, message, result = auth_service.register_user(
            email, password, first_name, last_name
        )
        
        if success:
            return success_response(message, result, 201)
        else:
            return error_response(message)
            
    except Exception as e:
        current_app.logger.error(f"Registration endpoint error: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        if not data:
            return error_response("DATA_REQUIRED")
        
        email = data.get('email', '').strip()
        password = data.get('password', '').strip()
        
        success, message, result = auth_service.login_user(email, password)
        
        if success:
            return success_response(message, result)
        else:
            return error_response(message, status_code=401)
            
    except Exception as e:
        current_app.logger.error(f"Login endpoint error: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    try:
        current_user_id = get_jwt_identity()
        
        success, message, result = auth_service.refresh_token(current_user_id)
        
        if success:
            return success_response(message, result)
        else:
            return error_response(message, status_code=401)
            
    except Exception as e:
        current_app.logger.error(f"Token refresh endpoint error: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@auth_bp.route('/logout', methods=['POST'])
@auth_required
def logout(current_user):
    try:
        return success_response("USER_LOGOUT_SUCCESS")

    except Exception as e:
        current_app.logger.error(f"Logout endpoint error: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@auth_bp.route('/change-password', methods=['PUT'])
@auth_required
def change_password(current_user):
    try:
        data = request.get_json()

        if not data:
            return error_response("DATA_REQUIRED")

        current_password = data.get('current_password')
        new_password = data.get('new_password')

        if not current_password or not new_password:
            return error_response("CREDENTIALS_REQUIRED")

        success, message, result = auth_service.change_password(
            current_user.get_id(), current_password, new_password
        )

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Change password endpoint error: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@auth_bp.route('/validate-token', methods=['GET'])
@auth_required
def validate_token(current_user):
    try:
        success, message, result = auth_service.validate_token()

        if success:
            return success_response(message, result)
        else:
            return error_response(message, status_code=401)

    except Exception as e:
        current_app.logger.error(f"Validate token endpoint error: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@auth_bp.route('/delete-account', methods=['DELETE'])
@auth_required
def delete_account(current_user):
    try:
        success, message, result = auth_service.delete_account(current_user.get_id())

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Delete account endpoint error: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@auth_bp.route('/verify-email', methods=['POST'])
def verify_email():
    """Verify user email with verification token"""
    try:
        data = request.get_json()

        if not data:
            return error_response("DATA_REQUIRED")

        token = data.get('token', '').strip()

        if not token:
            return error_response("VERIFICATION_TOKEN_REQUIRED")

        success, message, result = auth_service.verify_email(token)

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Verify email endpoint error: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@auth_bp.route('/resend-verification', methods=['POST'])
@auth_required
def resend_verification(current_user):
    """Resend verification email to current user"""
    try:
        success, message, result = auth_service.resend_verification_email(current_user.get_id())

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Resend verification endpoint error: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """Request password reset - sends email with reset token"""
    try:
        data = request.get_json()

        if not data:
            return error_response("DATA_REQUIRED")

        email = data.get('email', '').strip()

        if not email:
            return error_response("EMAIL_REQUIRED")

        success, message, result = auth_service.forgot_password(email)

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Forgot password endpoint error: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """Reset password using reset token"""
    try:
        data = request.get_json()

        if not data:
            return error_response("DATA_REQUIRED")

        token = data.get('token', '').strip()
        new_password = data.get('new_password', '').strip()

        if not token:
            return error_response("RESET_TOKEN_REQUIRED")

        if not new_password:
            return error_response("NEW_PASSWORD_REQUIRED")

        success, message, result = auth_service.reset_password(token, new_password)

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Reset password endpoint error: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

