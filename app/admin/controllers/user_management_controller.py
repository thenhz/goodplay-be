from flask import Blueprint, request, current_app
from flask_jwt_extended import get_jwt_identity

from app.admin.utils.decorators import admin_permission_required
from app.core.utils.responses import success_response, error_response

# Import core services for user management
from app.core.services.user_service import UserService
from app.core.repositories.user_repository import UserRepository
from app.admin.models.admin_action import AdminAction, ActionType
from app.admin.repositories.audit_repository import AuditRepository

user_mgmt_bp = Blueprint('admin_user_management', __name__, url_prefix='/api/admin/users')
user_service = UserService()
user_repository = UserRepository()
audit_repository = AuditRepository()

@user_mgmt_bp.route('', methods=['GET'])
@admin_permission_required('user_management')
def list_users(current_admin):
    """List users with filtering and pagination"""
    try:
        # Get query parameters
        active_only = request.args.get('active_only', 'true').lower() == 'true'
        limit = int(request.args.get('limit', 50))
        skip = int(request.args.get('skip', 0))
        search = request.args.get('search', '').strip()
        role = request.args.get('role')
        created_since = request.args.get('created_since')

        # Build filter criteria
        filter_criteria = {}
        if active_only:
            filter_criteria['is_active'] = True
        if role:
            filter_criteria['role'] = role

        # Get users
        if search:
            users = user_repository.search_users(search, limit)
            total_count = len(users)
        else:
            users = user_repository.find_all_users(filter_criteria, limit, skip)
            total_count = user_repository.count_users(filter_criteria)

        # Convert to dict format
        user_data = [user.to_dict() for user in users]

        return success_response("USERS_RETRIEVED_SUCCESS", {
            "users": user_data,
            "total": total_count,
            "limit": limit,
            "skip": skip,
            "filters": {
                "active_only": active_only,
                "role": role,
                "search": search
            }
        })

    except Exception as e:
        current_app.logger.error(f"List users error: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@user_mgmt_bp.route('/<user_id>', methods=['GET'])
@admin_permission_required('user_management')
def get_user_details(current_admin, user_id):
    """Get detailed user information"""
    try:
        user = user_repository.find_user_by_id(user_id)
        if not user:
            return error_response("USER_NOT_FOUND")

        # Get user's activity summary
        user_data = user.to_dict()

        # Add additional admin-only information
        user_data['admin_info'] = {
            'created_at': user.created_at.isoformat() if user.created_at else None,
            'updated_at': user.updated_at.isoformat() if user.updated_at else None,
            'is_active': user.is_active,
            'role': user.role
        }

        return success_response("USER_DETAILS_SUCCESS", {
            "user": user_data
        })

    except Exception as e:
        current_app.logger.error(f"Get user details error: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@user_mgmt_bp.route('/<user_id>/suspend', methods=['POST'])
@admin_permission_required('user_management')
def suspend_user(current_admin, user_id):
    """Suspend user account"""
    try:
        data = request.get_json() or {}
        reason = data.get('reason', 'Account suspended by admin')
        ip_address = request.environ.get('REMOTE_ADDR')

        # Check if user exists
        user = user_repository.find_user_by_id(user_id)
        if not user:
            return error_response("USER_NOT_FOUND")

        if not user.is_active:
            return error_response("USER_ALREADY_SUSPENDED")

        # Suspend user
        success = user_repository.update_user_status(user_id, False)
        if not success:
            return error_response("USER_SUSPENSION_FAILED")

        # Log the action
        action = AdminAction.create_user_action(
            admin_id=current_admin._id,
            action_type=ActionType.USER_SUSPEND.value,
            user_id=user_id,
            reason=reason,
            details={"previous_status": "active"},
            ip_address=ip_address
        )
        audit_repository.create_action(action)

        current_app.logger.info(f"User {user_id} suspended by admin {current_admin._id}")

        return success_response("USER_SUSPENDED_SUCCESS", {
            "user_id": user_id,
            "reason": reason
        })

    except Exception as e:
        current_app.logger.error(f"Suspend user error: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@user_mgmt_bp.route('/<user_id>/activate', methods=['POST'])
@admin_permission_required('user_management')
def activate_user(current_admin, user_id):
    """Activate user account"""
    try:
        data = request.get_json() or {}
        reason = data.get('reason', 'Account activated by admin')
        ip_address = request.environ.get('REMOTE_ADDR')

        # Check if user exists
        user = user_repository.find_user_by_id(user_id)
        if not user:
            return error_response("USER_NOT_FOUND")

        if user.is_active:
            return error_response("USER_ALREADY_ACTIVE")

        # Activate user
        success = user_repository.update_user_status(user_id, True)
        if not success:
            return error_response("USER_ACTIVATION_FAILED")

        # Log the action
        action = AdminAction.create_user_action(
            admin_id=current_admin._id,
            action_type=ActionType.USER_ACTIVATE.value,
            user_id=user_id,
            reason=reason,
            details={"previous_status": "suspended"},
            ip_address=ip_address
        )
        audit_repository.create_action(action)

        current_app.logger.info(f"User {user_id} activated by admin {current_admin._id}")

        return success_response("USER_ACTIVATED_SUCCESS", {
            "user_id": user_id,
            "reason": reason
        })

    except Exception as e:
        current_app.logger.error(f"Activate user error: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@user_mgmt_bp.route('/<user_id>/role', methods=['PUT'])
@admin_permission_required('user_management')
def update_user_role(current_admin, user_id):
    """Update user role"""
    try:
        data = request.get_json()
        if not data or 'role' not in data:
            return error_response("ROLE_REQUIRED")

        new_role = data.get('role').strip()
        reason = data.get('reason', f'Role changed to {new_role}')
        ip_address = request.environ.get('REMOTE_ADDR')

        # Check if user exists
        user = user_repository.find_user_by_id(user_id)
        if not user:
            return error_response("USER_NOT_FOUND")

        old_role = user.role

        # Update user role
        success = user_repository.update_user_role(user_id, new_role)
        if not success:
            return error_response("ROLE_UPDATE_FAILED")

        # Log the action
        action = AdminAction.create_user_action(
            admin_id=current_admin._id,
            action_type=ActionType.USER_ROLE_CHANGE.value,
            user_id=user_id,
            reason=reason,
            details={"old_role": old_role, "new_role": new_role},
            ip_address=ip_address
        )
        audit_repository.create_action(action)

        current_app.logger.info(f"User {user_id} role changed from {old_role} to {new_role} by admin {current_admin._id}")

        return success_response("USER_ROLE_UPDATED_SUCCESS", {
            "user_id": user_id,
            "old_role": old_role,
            "new_role": new_role
        })

    except Exception as e:
        current_app.logger.error(f"Update user role error: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@user_mgmt_bp.route('/bulk-action', methods=['POST'])
@admin_permission_required('user_management')
def bulk_user_action(current_admin):
    """Perform bulk actions on multiple users"""
    try:
        data = request.get_json()
        if not data:
            return error_response("DATA_REQUIRED")

        user_ids = data.get('user_ids', [])
        action_type = data.get('action', '').strip()
        reason = data.get('reason', f'Bulk {action_type} by admin')
        ip_address = request.environ.get('REMOTE_ADDR')

        if not user_ids or not action_type:
            return error_response("USER_IDS_AND_ACTION_REQUIRED")

        if action_type not in ['suspend', 'activate', 'delete']:
            return error_response("INVALID_BULK_ACTION")

        results = []
        success_count = 0
        error_count = 0

        for user_id in user_ids:
            try:
                user = user_repository.find_user_by_id(user_id)
                if not user:
                    results.append({
                        "user_id": user_id,
                        "status": "error",
                        "message": "User not found"
                    })
                    error_count += 1
                    continue

                if action_type == 'suspend':
                    if not user.is_active:
                        results.append({
                            "user_id": user_id,
                            "status": "skipped",
                            "message": "User already suspended"
                        })
                        continue

                    success = user_repository.update_user_status(user_id, False)
                    status_msg = "User suspended successfully"

                elif action_type == 'activate':
                    if user.is_active:
                        results.append({
                            "user_id": user_id,
                            "status": "skipped",
                            "message": "User already active"
                        })
                        continue

                    success = user_repository.update_user_status(user_id, True)
                    status_msg = "User activated successfully"

                elif action_type == 'delete':
                    # For safety, we'll mark as deleted rather than actually delete
                    success = user_repository.mark_user_deleted(user_id)
                    status_msg = "User marked as deleted"

                if success:
                    results.append({
                        "user_id": user_id,
                        "status": "success",
                        "message": status_msg
                    })
                    success_count += 1

                    # Log the action
                    action = AdminAction.create_user_action(
                        admin_id=current_admin._id,
                        action_type=ActionType.USER_BULK_ACTION.value,
                        user_id=user_id,
                        reason=reason,
                        details={"bulk_action": action_type, "batch_size": len(user_ids)},
                        ip_address=ip_address
                    )
                    audit_repository.create_action(action)

                else:
                    results.append({
                        "user_id": user_id,
                        "status": "error",
                        "message": f"Failed to {action_type} user"
                    })
                    error_count += 1

            except Exception as e:
                results.append({
                    "user_id": user_id,
                    "status": "error",
                    "message": str(e)
                })
                error_count += 1

        current_app.logger.info(f"Bulk {action_type} completed by admin {current_admin._id}: {success_count} success, {error_count} errors")

        return success_response("BULK_ACTION_COMPLETED", {
            "action": action_type,
            "total_users": len(user_ids),
            "success_count": success_count,
            "error_count": error_count,
            "results": results
        })

    except Exception as e:
        current_app.logger.error(f"Bulk user action error: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@user_mgmt_bp.route('/<user_id>/activity', methods=['GET'])
@admin_permission_required('user_management')
def get_user_activity(current_admin, user_id):
    """Get user activity history"""
    try:
        # Check if user exists
        user = user_repository.find_user_by_id(user_id)
        if not user:
            return error_response("USER_NOT_FOUND")

        # Get audit trail for this user
        audit_actions = audit_repository.get_audit_trail("user", user_id, limit=50)

        activity_data = [
            {
                "timestamp": action.timestamp.isoformat(),
                "action_type": action.action_type,
                "admin_id": action.admin_id,
                "reason": action.reason,
                "details": action.action_details,
                "status": action.status
            }
            for action in audit_actions
        ]

        return success_response("USER_ACTIVITY_SUCCESS", {
            "user_id": user_id,
            "activity": activity_data,
            "total_actions": len(activity_data)
        })

    except Exception as e:
        current_app.logger.error(f"Get user activity error: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@user_mgmt_bp.route('/statistics', methods=['GET'])
@admin_permission_required('user_management')
def get_user_statistics(current_admin):
    """Get user management statistics"""
    try:
        stats = user_repository.get_user_statistics()

        return success_response("USER_STATISTICS_SUCCESS", stats)

    except Exception as e:
        current_app.logger.error(f"User statistics error: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@user_mgmt_bp.route('/export', methods=['POST'])
@admin_permission_required('user_management')
def export_users(current_admin):
    """Export user data for reporting"""
    try:
        data = request.get_json() or {}
        filters = data.get('filters', {})
        format_type = data.get('format', 'json')
        ip_address = request.environ.get('REMOTE_ADDR')

        # Log the export action
        action = AdminAction(
            admin_id=current_admin._id,
            action_type=ActionType.USER_CREATE.value,  # Using CREATE as placeholder
            target_type="user",
            reason="User data export",
            action_details={"export_format": format_type, "filters": filters},
            ip_address=ip_address
        )
        audit_repository.create_action(action)

        # Get users based on filters
        users = user_repository.find_all_users(filters, limit=None)

        # Format for export (simplified for now)
        export_data = [
            {
                "id": user._id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "is_active": user.is_active,
                "role": user.role,
                "created_at": user.created_at.isoformat() if user.created_at else None
            }
            for user in users
        ]

        current_app.logger.info(f"User data exported by admin {current_admin._id}: {len(export_data)} users")

        return success_response("USER_EXPORT_SUCCESS", {
            "users": export_data,
            "total_count": len(export_data),
            "format": format_type,
            "exported_at": current_app.logger.info(f"User data exported")
        })

    except Exception as e:
        current_app.logger.error(f"Export users error: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)