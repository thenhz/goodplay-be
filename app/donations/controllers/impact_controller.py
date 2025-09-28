from flask import Blueprint, request, current_app
from app.core.utils.decorators import auth_required, admin_required
from app.core.utils.responses import success_response, error_response
from app.donations.services.impact_tracking_service import ImpactTrackingService
from app.donations.services.story_unlocking_service import StoryUnlockingService
from app.donations.services.impact_visualization_service import ImpactVisualizationService
from app.donations.services.community_impact_service import CommunityImpactService

# Create blueprint for impact tracking
impact_bp = Blueprint('impact', __name__, url_prefix='/api/impact')

# Initialize services with lazy loading
impact_service = None
story_service = None
visualization_service = None
community_service = None

def get_impact_service():
    global impact_service
    if impact_service is None:
        impact_service = ImpactTrackingService()
    return impact_service

def get_story_service():
    global story_service
    if story_service is None:
        story_service = StoryUnlockingService()
    return story_service

def get_visualization_service():
    global visualization_service
    if visualization_service is None:
        visualization_service = ImpactVisualizationService()
    return visualization_service

def get_community_service():
    global community_service
    if community_service is None:
        community_service = CommunityImpactService()
    return community_service


# =============================================================================
# USER IMPACT ENDPOINTS
# =============================================================================

@impact_bp.route('/user/<user_id>', methods=['GET'])
@auth_required
def get_user_impact(current_user, user_id):
    """Get comprehensive impact summary for a user."""
    try:
        # Ensure user can only access their own data or admin access
        if current_user.get_id() != user_id and not current_user.is_admin():
            return error_response("ACCESS_DENIED", status_code=403)

        success, message, impact_data = get_impact_service().get_user_impact_summary(user_id)

        if success:
            return success_response(message, impact_data)
        else:
            return error_response(message, status_code=404 if "NOT_FOUND" in message else 400)

    except Exception as e:
        current_app.logger.error(f"Error getting user impact for {user_id}: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@impact_bp.route('/user/<user_id>/timeline', methods=['GET'])
@auth_required
def get_user_impact_timeline(current_user, user_id):
    """Get user's impact timeline with milestones and story unlocks."""
    try:
        if current_user.get_id() != user_id and not current_user.is_admin():
            return error_response("ACCESS_DENIED", status_code=403)

        # Get query parameters
        limit = min(request.args.get('limit', 20, type=int), 100)
        days = min(request.args.get('days', 30, type=int), 365)

        success, message, impact_data = get_impact_service().get_user_impact_summary(user_id)

        if success:
            # Build timeline from impact data
            timeline_data = {
                'user_id': user_id,
                'timeline_events': impact_data.get('milestones', []),
                'period_days': days,
                'limit': limit
            }
            return success_response("USER_TIMELINE_SUCCESS", timeline_data)
        else:
            return error_response(message, status_code=400)

    except Exception as e:
        current_app.logger.error(f"Error getting user timeline for {user_id}: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@impact_bp.route('/donation/<donation_id>', methods=['GET'])
@auth_required
def get_donation_impact(current_user, donation_id):
    """Get detailed impact information for a specific donation."""
    try:
        success, message, impact_data = get_impact_service().get_donation_impact_details(
            donation_id, current_user.get_id()
        )

        if success:
            return success_response(message, impact_data)
        else:
            status_code = 404 if "NOT_FOUND" in message else 403 if "ACCESS_DENIED" in message else 400
            return error_response(message, status_code=status_code)

    except Exception as e:
        current_app.logger.error(f"Error getting donation impact for {donation_id}: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


# =============================================================================
# STORY UNLOCKING ENDPOINTS
# =============================================================================

@impact_bp.route('/stories/available', methods=['GET'])
@auth_required
def get_available_stories(current_user):
    """Get stories available for the current user."""
    try:
        category = request.args.get('category')

        success, message, story_data = get_story_service().get_available_stories(
            current_user.get_id(), category
        )

        if success:
            return success_response(message, story_data)
        else:
            return error_response(message, status_code=400)

    except Exception as e:
        current_app.logger.error(f"Error getting available stories for {current_user.get_id()}: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@impact_bp.route('/stories/<story_id>', methods=['GET'])
@auth_required
def get_story_details(current_user, story_id):
    """Get detailed information about a specific story."""
    try:
        success, message, story_data = get_story_service().get_story_progress(
            current_user.get_id(), story_id
        )

        if success:
            return success_response(message, story_data)
        else:
            return error_response(message, status_code=404 if "NOT_FOUND" in message else 400)

    except Exception as e:
        current_app.logger.error(f"Error getting story details for {story_id}: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@impact_bp.route('/stories/progress', methods=['GET'])
@auth_required
def get_story_unlock_progress(current_user):
    """Get unlock progress for next available stories."""
    try:
        success, message, progress_data = get_story_service().get_next_unlockable_stories(
            current_user.get_id()
        )

        if success:
            return success_response(message, progress_data)
        else:
            return error_response(message, status_code=400)

    except Exception as e:
        current_app.logger.error(f"Error getting story progress for {current_user.get_id()}: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


# =============================================================================
# COMMUNITY & DASHBOARD ENDPOINTS
# =============================================================================

@impact_bp.route('/community/statistics', methods=['GET'])
def get_community_statistics():
    """Get platform-wide community statistics."""
    try:
        success, message, stats_data = get_community_service().get_community_statistics()

        if success:
            return success_response(message, stats_data)
        else:
            return error_response(message, status_code=400)

    except Exception as e:
        current_app.logger.error(f"Error getting community statistics: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@impact_bp.route('/community/leaderboard', methods=['GET'])
def get_community_leaderboard():
    """Get community impact leaderboard."""
    try:
        period = request.args.get('period', 'monthly')

        success, message, leaderboard_data = get_community_service().get_leaderboard(period)

        if success:
            return success_response(message, leaderboard_data)
        else:
            return error_response(message, status_code=400)

    except Exception as e:
        current_app.logger.error(f"Error getting community leaderboard: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@impact_bp.route('/dashboard', methods=['GET'])
def get_dashboard_data():
    """Get comprehensive dashboard data for impact visualization."""
    try:
        # Optional user context for personalization
        user_id = request.args.get('user_id')

        success, message, dashboard_data = get_visualization_service().get_dashboard_data(user_id)

        if success:
            return success_response(message, dashboard_data)
        else:
            return error_response(message, status_code=400)

    except Exception as e:
        current_app.logger.error(f"Error getting dashboard data: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


# =============================================================================
# ONLUS IMPACT ENDPOINTS
# =============================================================================

@impact_bp.route('/onlus/<onlus_id>/metrics', methods=['GET'])
def get_onlus_impact_metrics(onlus_id):
    """Get impact metrics for a specific ONLUS."""
    try:
        success, message, metrics_data = get_visualization_service().get_onlus_impact_visualization(onlus_id)

        if success:
            return success_response(message, metrics_data)
        else:
            return error_response(message, status_code=404 if "NOT_FOUND" in message else 400)

    except Exception as e:
        current_app.logger.error(f"Error getting ONLUS metrics for {onlus_id}: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@impact_bp.route('/onlus/<onlus_id>/updates', methods=['GET'])
def get_onlus_updates(onlus_id):
    """Get recent updates from a specific ONLUS."""
    try:
        from app.donations.repositories.impact_update_repository import ImpactUpdateRepository

        update_repo = ImpactUpdateRepository()
        days = min(request.args.get('days', 30, type=int), 90)
        limit = min(request.args.get('limit', 10, type=int), 50)

        updates = update_repo.get_recent_updates_by_onlus(onlus_id, days, limit)

        update_data = {
            'onlus_id': onlus_id,
            'updates': [update.to_response_dict() for update in updates],
            'period_days': days,
            'total_updates': len(updates)
        }

        return success_response("ONLUS_UPDATES_SUCCESS", update_data)

    except Exception as e:
        current_app.logger.error(f"Error getting ONLUS updates for {onlus_id}: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


# =============================================================================
# REPORTS ENDPOINTS
# =============================================================================

@impact_bp.route('/reports/monthly/<int:year>/<int:month>', methods=['GET'])
def get_monthly_report(year, month):
    """Get monthly community impact report."""
    try:
        if not (1 <= month <= 12):
            return error_response("INVALID_MONTH", status_code=400)

        if not (2020 <= year <= 2030):
            return error_response("INVALID_YEAR", status_code=400)

        from app.donations.repositories.community_report_repository import CommunityReportRepository

        report_repo = CommunityReportRepository()
        reports = report_repo.get_monthly_reports(year, month)

        if reports:
            return success_response("MONTHLY_REPORT_SUCCESS", reports[0].to_response_dict())
        else:
            return error_response("REPORT_NOT_FOUND", status_code=404)

    except Exception as e:
        current_app.logger.error(f"Error getting monthly report for {year}/{month}: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@impact_bp.route('/reports/annual/<int:year>', methods=['GET'])
def get_annual_report(year):
    """Get annual community impact report."""
    try:
        if not (2020 <= year <= 2030):
            return error_response("INVALID_YEAR", status_code=400)

        from app.donations.repositories.community_report_repository import CommunityReportRepository

        report_repo = CommunityReportRepository()
        reports = report_repo.get_annual_reports(year, year)

        if reports:
            return success_response("ANNUAL_REPORT_SUCCESS", reports[0].to_response_dict())
        else:
            return error_response("REPORT_NOT_FOUND", status_code=404)

    except Exception as e:
        current_app.logger.error(f"Error getting annual report for {year}: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


# =============================================================================
# ADMIN ENDPOINTS
# =============================================================================

@impact_bp.route('/admin/metrics', methods=['POST'])
@admin_required
def create_impact_metric(current_user):
    """Create or update an impact metric (admin only)."""
    try:
        data = request.get_json()
        if not data:
            return error_response("DATA_REQUIRED", status_code=400)

        if 'onlus_id' not in data:
            return error_response("ONLUS_ID_REQUIRED", status_code=400)

        onlus_id = data['onlus_id']
        success, message, metric_data = get_impact_service().update_onlus_impact_metric(
            onlus_id, data, "admin_update"
        )

        if success:
            return success_response(message, metric_data)
        else:
            return error_response(message, status_code=400)

    except Exception as e:
        current_app.logger.error(f"Error creating impact metric: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@impact_bp.route('/admin/updates', methods=['POST'])
@admin_required
def create_impact_update(current_user):
    """Create an impact update (admin only)."""
    try:
        data = request.get_json()
        if not data:
            return error_response("DATA_REQUIRED", status_code=400)

        if 'onlus_id' not in data:
            return error_response("ONLUS_ID_REQUIRED", status_code=400)

        onlus_id = data['onlus_id']
        success, message, update_data = get_impact_service().create_impact_update(onlus_id, data)

        if success:
            return success_response(message, update_data)
        else:
            return error_response(message, status_code=400)

    except Exception as e:
        current_app.logger.error(f"Error creating impact update: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@impact_bp.route('/admin/reports/generate', methods=['POST'])
@admin_required
def generate_community_report(current_user):
    """Generate a new community report (admin only)."""
    try:
        data = request.get_json()
        if not data or 'report_type' not in data:
            return error_response("REPORT_TYPE_REQUIRED", status_code=400)

        report_type = data['report_type']

        if report_type == 'real_time':
            success, message, report = get_community_service().generate_real_time_report()
        else:
            return error_response("UNSUPPORTED_REPORT_TYPE", status_code=400)

        if success:
            return success_response(message, report.to_response_dict() if report else {})
        else:
            return error_response(message, status_code=400)

    except Exception as e:
        current_app.logger.error(f"Error generating community report: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


# =============================================================================
# ERROR HANDLERS
# =============================================================================

@impact_bp.errorhandler(400)
def bad_request(error):
    return error_response("INVALID_REQUEST", status_code=400)

@impact_bp.errorhandler(401)
def unauthorized(error):
    return error_response("UNAUTHORIZED_ACCESS", status_code=401)

@impact_bp.errorhandler(403)
def forbidden(error):
    return error_response("FORBIDDEN_ACTION", status_code=403)

@impact_bp.errorhandler(404)
def not_found(error):
    return error_response("RESOURCE_NOT_FOUND", status_code=404)

@impact_bp.errorhandler(500)
def internal_error(error):
    return error_response("INTERNAL_SERVER_ERROR", status_code=500)