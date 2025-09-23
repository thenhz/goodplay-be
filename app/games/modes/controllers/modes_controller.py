from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.core.utils.decorators import auth_required, admin_required
from app.core.utils.responses import success_response, error_response
from datetime import datetime

from ..services.mode_manager import ModeManager
from ..services.scheduler import ModeScheduler

modes_bp = Blueprint('modes', __name__, url_prefix='/api/modes')

mode_manager = ModeManager()
scheduler = ModeScheduler()

@modes_bp.route('/current', methods=['GET'])
def get_current_modes():
    """Get currently available game modes"""
    try:
        # Get user ID if authenticated
        user_id = None
        try:
            user_id = get_jwt_identity()
        except:
            pass  # Allow anonymous access

        success, message, data = mode_manager.get_available_modes(user_id)

        if success:
            return success_response(message, data)
        else:
            return error_response(message)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@modes_bp.route('/active', methods=['GET'])
@admin_required
def get_active_modes(current_user):
    """Get all currently active modes (admin only)"""
    try:
        success, message, data = mode_manager.get_current_active_modes()

        if success:
            return success_response(message, data)
        else:
            return error_response(message)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@modes_bp.route('/schedule', methods=['GET'])
def get_mode_schedule():
    """Get schedule information for modes"""
    try:
        mode_name = request.args.get('mode_name')

        success, message, data = mode_manager.get_mode_schedule(mode_name)

        if success:
            return success_response(message, data)
        else:
            return error_response(message)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@modes_bp.route('/<mode_name>/activate', methods=['POST'])
@admin_required
def activate_mode(current_user, mode_name):
    """Activate a game mode (admin only)"""
    try:
        data = request.get_json() or {}

        start_date = None
        end_date = None

        if data.get('start_date'):
            start_date = datetime.fromisoformat(data['start_date'].replace('Z', '+00:00'))

        if data.get('end_date'):
            end_date = datetime.fromisoformat(data['end_date'].replace('Z', '+00:00'))

        success, message, result = mode_manager.activate_mode(
            mode_name=mode_name,
            start_date=start_date,
            end_date=end_date,
            admin_user_id=current_user.get('id')
        )

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except ValueError as e:
        return error_response("INVALID_DATE_FORMAT")
    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@modes_bp.route('/<mode_name>/deactivate', methods=['POST'])
@admin_required
def deactivate_mode(current_user, mode_name):
    """Deactivate a game mode (admin only)"""
    try:
        success, message, result = mode_manager.deactivate_mode(
            mode_name=mode_name,
            admin_user_id=current_user.get('id')
        )

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@modes_bp.route('/schedule', methods=['POST'])
@admin_required
def schedule_mode_activation(current_user):
    """Schedule a mode activation (admin only)"""
    try:
        data = request.get_json()
        if not data:
            return error_response("DATA_REQUIRED")

        required_fields = ['mode_name', 'scheduled_at']
        for field in required_fields:
            if field not in data:
                return error_response(f"FIELD_REQUIRED_{field.upper()}")

        mode_name = data['mode_name']
        scheduled_at = datetime.fromisoformat(data['scheduled_at'].replace('Z', '+00:00'))

        end_date = None
        if data.get('end_date'):
            end_date = datetime.fromisoformat(data['end_date'].replace('Z', '+00:00'))

        config_override = data.get('config_override', {})

        success, message, result = mode_manager.schedule_mode_activation(
            mode_name=mode_name,
            scheduled_at=scheduled_at,
            end_date=end_date,
            config_override=config_override,
            admin_user_id=current_user.get('id')
        )

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except ValueError as e:
        return error_response("INVALID_DATE_FORMAT")
    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@modes_bp.route('/schedule/recurring', methods=['POST'])
@admin_required
def create_recurring_schedule(current_user):
    """Create a recurring schedule for mode activation (admin only)"""
    try:
        data = request.get_json()
        if not data:
            return error_response("DATA_REQUIRED")

        required_fields = ['mode_name', 'action', 'start_time', 'recurrence_config']
        for field in required_fields:
            if field not in data:
                return error_response(f"FIELD_REQUIRED_{field.upper()}")

        mode_name = data['mode_name']
        action = data['action']
        start_time = datetime.fromisoformat(data['start_time'].replace('Z', '+00:00'))
        recurrence_config = data['recurrence_config']

        end_date = None
        if data.get('end_date'):
            end_date = datetime.fromisoformat(data['end_date'].replace('Z', '+00:00'))

        success, message, result = mode_manager.create_recurring_schedule(
            mode_name=mode_name,
            action=action,
            start_time=start_time,
            recurrence_config=recurrence_config,
            end_date=end_date,
            admin_user_id=current_user.get('id')
        )

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except ValueError as e:
        return error_response("INVALID_DATE_FORMAT")
    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@modes_bp.route('/schedule/upcoming', methods=['GET'])
@admin_required
def get_upcoming_executions(current_user):
    """Get upcoming schedule executions (admin only)"""
    try:
        hours_ahead = int(request.args.get('hours_ahead', 24))

        success, message, data = scheduler.get_next_executions(hours_ahead)

        if success:
            return success_response(message, data)
        else:
            return error_response(message)

    except ValueError:
        return error_response("INVALID_HOURS_AHEAD_VALUE")
    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@modes_bp.route('/schedule/<schedule_id>/execute', methods=['POST'])
@admin_required
def force_execute_schedule(current_user, schedule_id):
    """Force execute a specific schedule (admin only)"""
    try:
        success, message, result = scheduler.force_execute_schedule(schedule_id)

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@modes_bp.route('/schedule/<schedule_id>/cancel', methods=['POST'])
@admin_required
def cancel_schedule(current_user, schedule_id):
    """Cancel a pending schedule (admin only)"""
    try:
        success, message, result = scheduler.cancel_schedule(schedule_id)

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@modes_bp.route('/statistics', methods=['GET'])
@admin_required
def get_mode_statistics(current_user):
    """Get mode and schedule statistics (admin only)"""
    try:
        success, message, data = mode_manager.get_mode_statistics()

        if success:
            return success_response(message, data)
        else:
            return error_response(message)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@modes_bp.route('/scheduler/status', methods=['GET'])
@admin_required
def get_scheduler_status(current_user):
    """Get scheduler status (admin only)"""
    try:
        status = scheduler.get_scheduler_status()
        return success_response("SCHEDULER_STATUS_RETRIEVED", status)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@modes_bp.route('/scheduler/start', methods=['POST'])
@admin_required
def start_scheduler(current_user):
    """Start the background scheduler (admin only)"""
    try:
        data = request.get_json() or {}
        check_interval = data.get('check_interval_seconds', 60)

        success = scheduler.start_background_scheduler(check_interval)

        if success:
            return success_response("SCHEDULER_STARTED", {"check_interval_seconds": check_interval})
        else:
            return error_response("SCHEDULER_ALREADY_RUNNING")

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@modes_bp.route('/scheduler/stop', methods=['POST'])
@admin_required
def stop_scheduler(current_user):
    """Stop the background scheduler (admin only)"""
    try:
        success = scheduler.stop_background_scheduler()

        if success:
            return success_response("SCHEDULER_STOPPED")
        else:
            return error_response("FAILED_TO_STOP_SCHEDULER")

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@modes_bp.route('/initialize', methods=['POST'])
@admin_required
def initialize_mode_system(current_user):
    """Initialize the mode system with defaults (admin only)"""
    try:
        success, message, data = mode_manager.initialize_system()

        if success:
            return success_response(message, data)
        else:
            return error_response(message)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@modes_bp.route('/cleanup', methods=['POST'])
@admin_required
def cleanup_old_data(current_user):
    """Clean up old schedule data (admin only)"""
    try:
        data = request.get_json() or {}
        days_old = data.get('days_old', 30)

        success, message, result = scheduler.cleanup_old_data(days_old)

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)