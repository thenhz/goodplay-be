from flask import Blueprint, request, current_app
from flask_jwt_extended import get_jwt_identity

from app.admin.services.admin_service import AdminService
from app.admin.utils.decorators import admin_auth_required, super_admin_required, admin_permission_required
from app.core.utils.responses import success_response, error_response

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')
admin_service = AdminService()

@admin_bp.route('/auth/login', methods=['POST'])
def admin_login():
    """Admin login endpoint"""
    try:
        data = request.get_json()

        if not data:
            return error_response("DATA_REQUIRED")

        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        ip_address = request.environ.get('REMOTE_ADDR')

        success, message, result = admin_service.authenticate_admin(
            username, password, ip_address
        )

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Admin login error: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@admin_bp.route('/auth/profile', methods=['GET'])
@admin_auth_required
def get_admin_profile(current_admin):
    """Get current admin profile"""
    try:
        return success_response("ADMIN_PROFILE_SUCCESS", {
            "admin": current_admin.to_dict()
        })

    except Exception as e:
        current_app.logger.error(f"Admin profile error: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@admin_bp.route('/auth/change-password', methods=['PUT'])
@admin_auth_required
def change_admin_password(current_admin):
    """Change admin password"""
    try:
        data = request.get_json()

        if not data:
            return error_response("DATA_REQUIRED")

        current_password = data.get('current_password', '').strip()
        new_password = data.get('new_password', '').strip()
        ip_address = request.environ.get('REMOTE_ADDR')

        success, message, result = admin_service.change_admin_password(
            current_admin._id, current_password, new_password,
            current_admin._id, ip_address
        )

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Password change error: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@admin_bp.route('/admins', methods=['GET'])
@admin_permission_required('user_management')
def list_admins(current_admin):
    """List admin users"""
    try:
        active_only = request.args.get('active_only', 'true').lower() == 'true'
        limit = int(request.args.get('limit', 50))
        skip = int(request.args.get('skip', 0))
        role = request.args.get('role')

        success, message, result = admin_service.list_admins(
            active_only, limit, skip, role
        )

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"List admins error: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@admin_bp.route('/admins', methods=['POST'])
@super_admin_required
def create_admin(current_admin):
    """Create new admin user"""
    try:
        data = request.get_json()

        if not data:
            return error_response("DATA_REQUIRED")

        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '').strip()
        role = data.get('role', 'analyst').strip()
        ip_address = request.environ.get('REMOTE_ADDR')

        success, message, result = admin_service.create_admin(
            username, email, password, role, current_admin._id, ip_address
        )

        if success:
            return success_response(message, result, 201)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Create admin error: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@admin_bp.route('/admins/<admin_id>', methods=['GET'])
@admin_permission_required('user_management')
def get_admin(current_admin, admin_id):
    """Get admin by ID"""
    try:
        success, message, result = admin_service.get_admin_by_id(admin_id)

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Get admin error: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@admin_bp.route('/admins/<admin_id>', methods=['PUT'])
@admin_permission_required('user_management')
def update_admin(current_admin, admin_id):
    """Update admin user"""
    try:
        data = request.get_json()

        if not data:
            return error_response("DATA_REQUIRED")

        ip_address = request.environ.get('REMOTE_ADDR')

        success, message, result = admin_service.update_admin(
            admin_id, data, current_admin._id, ip_address
        )

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Update admin error: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@admin_bp.route('/admins/<admin_id>/activate', methods=['POST'])
@admin_permission_required('user_management')
def activate_admin(current_admin, admin_id):
    """Activate admin account"""
    try:
        ip_address = request.environ.get('REMOTE_ADDR')

        success, message, result = admin_service.activate_admin(
            admin_id, current_admin._id, ip_address
        )

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Activate admin error: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@admin_bp.route('/admins/<admin_id>/deactivate', methods=['POST'])
@admin_permission_required('user_management')
def deactivate_admin(current_admin, admin_id):
    """Deactivate admin account"""
    try:
        data = request.get_json() or {}
        reason = data.get('reason')
        ip_address = request.environ.get('REMOTE_ADDR')

        success, message, result = admin_service.deactivate_admin(
            admin_id, current_admin._id, reason, ip_address
        )

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Deactivate admin error: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@admin_bp.route('/admins/<admin_id>/unlock', methods=['POST'])
@admin_permission_required('user_management')
def unlock_admin(current_admin, admin_id):
    """Unlock admin account"""
    try:
        ip_address = request.environ.get('REMOTE_ADDR')

        success, message, result = admin_service.unlock_admin_account(
            admin_id, current_admin._id, ip_address
        )

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Unlock admin error: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@admin_bp.route('/admins/<admin_id>/enable-mfa', methods=['POST'])
@admin_permission_required('user_management')
def enable_admin_mfa(current_admin, admin_id):
    """Enable MFA for admin"""
    try:
        ip_address = request.environ.get('REMOTE_ADDR')

        success, message, result = admin_service.enable_mfa(
            admin_id, current_admin._id, ip_address
        )

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Enable MFA error: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@admin_bp.route('/admins/search', methods=['GET'])
@admin_permission_required('user_management')
def search_admins(current_admin):
    """Search admin users"""
    try:
        query = request.args.get('q', '').strip()
        limit = int(request.args.get('limit', 20))

        if not query:
            return error_response("SEARCH_QUERY_REQUIRED")

        success, message, result = admin_service.search_admins(query, limit)

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Search admins error: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@admin_bp.route('/statistics', methods=['GET'])
@admin_permission_required('analytics_view')
def get_admin_statistics(current_admin):
    """Get admin statistics"""
    try:
        success, message, result = admin_service.get_admin_statistics()

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Admin statistics error: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)