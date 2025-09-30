from functools import wraps
from flask import jsonify, current_app, request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.admin.repositories.admin_repository import AdminRepository

def admin_auth_required(f):
    """Decorator for admin authentication"""
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        try:
            current_admin_id = get_jwt_identity()
            claims = get_jwt()

            # Check if token is for admin
            if claims.get('type') != 'admin':
                return jsonify({
                    'success': False,
                    'message': 'ADMIN_TOKEN_REQUIRED'
                }), 401

            admin_repository = AdminRepository()
            admin = admin_repository.find_admin_by_id(current_admin_id)

            if not admin or not admin.is_active:
                return jsonify({
                    'success': False,
                    'message': 'INVALID_ADMIN_TOKEN_OR_DISABLED'
                }), 401

            # Check if admin account is locked
            if admin.is_locked():
                return jsonify({
                    'success': False,
                    'message': 'ADMIN_ACCOUNT_LOCKED'
                }), 401

            # Check IP whitelist if configured
            ip_address = request.environ.get('REMOTE_ADDR')
            if not admin.is_ip_whitelisted(ip_address):
                return jsonify({
                    'success': False,
                    'message': 'IP_NOT_WHITELISTED'
                }), 403

            return f(current_admin=admin, *args, **kwargs)

        except Exception as e:
            current_app.logger.error(f"Admin auth decorator error: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'ADMIN_AUTHENTICATION_ERROR'
            }), 401

    return decorated_function

def admin_permission_required(permission):
    """Decorator for admin permission checking"""
    def decorator(f):
        @wraps(f)
        @admin_auth_required
        def decorated_function(current_admin, *args, **kwargs):
            if not current_admin.has_permission(permission):
                return jsonify({
                    'success': False,
                    'message': 'INSUFFICIENT_PERMISSIONS'
                }), 403

            return f(current_admin=current_admin, *args, **kwargs)

        return decorated_function
    return decorator

def admin_role_required(required_roles):
    """Decorator for admin role checking"""
    if isinstance(required_roles, str):
        required_roles = [required_roles]

    def decorator(f):
        @wraps(f)
        @admin_auth_required
        def decorated_function(current_admin, *args, **kwargs):
            if current_admin.role not in required_roles:
                return jsonify({
                    'success': False,
                    'message': 'INSUFFICIENT_ROLE'
                }), 403

            return f(current_admin=current_admin, *args, **kwargs)

        return decorated_function
    return decorator

def super_admin_required(f):
    """Decorator for super admin only access"""
    @wraps(f)
    @admin_role_required(['super_admin'])
    def decorated_function(*args, **kwargs):
        return f(*args, **kwargs)

    return decorated_function

def audit_action(action_type, target_type=None, get_target_id=None, get_reason=None):
    """Decorator to automatically log admin actions"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # This would be implemented to automatically log actions
            # For now, we'll let the service methods handle logging
            return f(*args, **kwargs)

        return decorated_function
    return decorator