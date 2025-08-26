from functools import wraps
from flask import jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.repositories.user_repository import UserRepository

def auth_required(f):
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        try:
            current_user_id = get_jwt_identity()
            user_repository = UserRepository()
            user = user_repository.find_user_by_id(current_user_id)
            
            if not user or not user.is_active:
                return jsonify({
                    'success': False,
                    'message': 'Invalid token or user disabled'
                }), 401
            
            return f(current_user=user, *args, **kwargs)
            
        except Exception as e:
            current_app.logger.error(f"Auth decorator error: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Authentication error'
            }), 401
    
    return decorated_function

def admin_required(f):
    @wraps(f)
    @auth_required
    def decorated_function(current_user, *args, **kwargs):
        if current_user.role != 'admin':
            return jsonify({
                'success': False,
                'message': 'Admin access required'
            }), 403
        
        return f(current_user=current_user, *args, **kwargs)
    
    return decorated_function