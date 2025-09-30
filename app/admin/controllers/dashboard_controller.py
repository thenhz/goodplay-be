from flask import Blueprint, request, current_app
from flask_jwt_extended import get_jwt_identity

from app.admin.services.dashboard_service import DashboardService
from app.admin.services.monitoring_service import MonitoringService
from app.admin.utils.decorators import admin_auth_required, admin_permission_required
from app.core.utils.responses import success_response, error_response

dashboard_bp = Blueprint('admin_dashboard', __name__, url_prefix='/api/admin')
dashboard_service = DashboardService()
monitoring_service = MonitoringService()

@dashboard_bp.route('/dashboard', methods=['GET'])
@admin_auth_required
def get_dashboard_overview(current_admin):
    """Get comprehensive dashboard overview"""
    try:
        success, message, result = dashboard_service.get_dashboard_overview(current_admin._id)

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Dashboard overview error: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@dashboard_bp.route('/dashboard/user-management', methods=['GET'])
@admin_permission_required('user_management')
def get_user_management_dashboard(current_admin):
    """Get user management dashboard data"""
    try:
        time_range = request.args.get('time_range', '7d')

        success, message, result = dashboard_service.get_user_management_data(
            current_admin._id, time_range
        )

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"User management dashboard error: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@dashboard_bp.route('/dashboard/financial', methods=['GET'])
@admin_permission_required('financial_oversight')
def get_financial_dashboard(current_admin):
    """Get financial dashboard data"""
    try:
        time_range = request.args.get('time_range', '30d')

        success, message, result = dashboard_service.get_financial_dashboard_data(
            current_admin._id, time_range
        )

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Financial dashboard error: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@dashboard_bp.route('/dashboard/system-monitoring', methods=['GET'])
@admin_permission_required('system_monitoring')
def get_system_monitoring_dashboard(current_admin):
    """Get system monitoring dashboard data"""
    try:
        success, message, result = dashboard_service.get_system_monitoring_data(current_admin._id)

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"System monitoring dashboard error: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@dashboard_bp.route('/dashboard/content-moderation', methods=['GET'])
@admin_permission_required('content_moderation')
def get_content_moderation_dashboard(current_admin):
    """Get content moderation dashboard data"""
    try:
        time_range = request.args.get('time_range', '7d')

        success, message, result = dashboard_service.get_content_moderation_data(
            current_admin._id, time_range
        )

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Content moderation dashboard error: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@dashboard_bp.route('/metrics/real-time', methods=['GET'])
@admin_permission_required('system_monitoring')
def get_real_time_metrics(current_admin):
    """Get real-time system metrics"""
    try:
        success, message, result = monitoring_service.get_real_time_metrics()

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Real-time metrics error: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@dashboard_bp.route('/metrics/performance', methods=['GET'])
@admin_permission_required('system_monitoring')
def get_performance_analytics(current_admin):
    """Get performance analytics"""
    try:
        hours = int(request.args.get('hours', 24))

        success, message, result = monitoring_service.get_performance_analytics(hours)

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Performance analytics error: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@dashboard_bp.route('/metrics/security', methods=['GET'])
@admin_permission_required('system_monitoring')
def get_security_monitoring(current_admin):
    """Get security monitoring data"""
    try:
        hours = int(request.args.get('hours', 24))

        success, message, result = monitoring_service.get_security_monitoring(hours)

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Security monitoring error: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@dashboard_bp.route('/alerts', methods=['GET'])
@admin_auth_required
def get_system_alerts(current_admin):
    """Get system alerts"""
    try:
        severity = request.args.get('severity')
        limit = int(request.args.get('limit', 50))

        success, message, result = monitoring_service.get_system_alerts(severity, limit)

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"System alerts error: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@dashboard_bp.route('/alerts/<alert_id>/acknowledge', methods=['POST'])
@admin_auth_required
def acknowledge_alert(current_admin, alert_id):
    """Acknowledge a system alert"""
    try:
        data = request.get_json() or {}
        notes = data.get('notes')
        ip_address = request.environ.get('REMOTE_ADDR')

        success, message, result = monitoring_service.acknowledge_alert(
            alert_id, current_admin._id, notes, ip_address
        )

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Alert acknowledgment error: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@dashboard_bp.route('/analytics/<metric_type>', methods=['GET'])
@admin_permission_required('analytics_view')
def get_analytics_data(current_admin, metric_type):
    """Get analytics data for charts and reports"""
    try:
        time_range = request.args.get('time_range', '30d')

        success, message, result = dashboard_service.get_analytics_data(
            current_admin._id, metric_type, time_range
        )

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Analytics data error: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@dashboard_bp.route('/metrics/collect', methods=['POST'])
@admin_permission_required('system_monitoring')
def collect_system_metrics(current_admin):
    """Manually trigger system metrics collection"""
    try:
        success, message, result = monitoring_service.collect_system_metrics()

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Metrics collection error: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)