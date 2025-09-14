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
            return error_response("Data required")
        
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
        return error_response("Internal server error", status_code=500)

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        if not data:
            return error_response("Data required")
        
        email = data.get('email', '').strip()
        password = data.get('password', '').strip()
        
        success, message, result = auth_service.login_user(email, password)
        
        if success:
            return success_response(message, result)
        else:
            return error_response(message, status_code=401)
            
    except Exception as e:
        current_app.logger.error(f"Login endpoint error: {str(e)}")
        return error_response("Internal server error", status_code=500)

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
        return error_response("Internal server error", status_code=500)


@auth_bp.route('/logout', methods=['POST'])
@auth_required
def logout(current_user):
    try:
        return success_response("Logout successful")

    except Exception as e:
        current_app.logger.error(f"Logout endpoint error: {str(e)}")
        return error_response("Internal server error", status_code=500)

