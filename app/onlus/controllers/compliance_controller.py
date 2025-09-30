from flask import Blueprint, request, current_app
from typing import Dict, Any, Optional
from datetime import datetime, timezone, timedelta

from app.core.auth_decorators import auth_required, admin_required
from app.core.response_helpers import success_response, error_response
from app.onlus.services.compliance_monitoring_service import ComplianceMonitoringService
from app.onlus.services.audit_trail_service import AuditTrailService


# Create Blueprint
compliance_bp = Blueprint('compliance', __name__, url_prefix='/api/onlus/compliance')

# Initialize services
compliance_service = ComplianceMonitoringService()
audit_service = AuditTrailService()


@compliance_bp.route('/assessment/<onlus_id>', methods=['POST'])
@admin_required
def conduct_assessment(current_user, onlus_id):
    """Conduct comprehensive compliance assessment for an ONLUS."""
    try:
        data = request.get_json() or {}
        assessment_period_months = min(int(data.get('period_months', 12)), 60)  # Max 5 years

        success, message, result_data = compliance_service.conduct_comprehensive_assessment(
            onlus_id, assessment_period_months
        )

        if not success:
            return error_response(message)

        # Create audit trail
        audit_service.audit_compliance_assessment(
            str(result_data['_id']),
            onlus_id,
            result_data['overall_score'],
            result_data['compliance_level'],
            current_user['user_id'],
            {
                'category_scores': result_data.get('category_scores', {}),
                'issues_count': result_data.get('open_issues_count', 0),
                'recommendations_count': len(result_data.get('improvement_recommendations', []))
            }
        )

        current_app.logger.info(
            f"Compliance assessment conducted for {onlus_id} by admin {current_user['user_id']}: "
            f"Score {result_data['overall_score']:.2f}, Level {result_data['compliance_level']}"
        )

        return success_response(message, result_data)

    except Exception as e:
        current_app.logger.error(f"Conduct assessment failed: {str(e)}")
        return error_response("COMPLIANCE_ASSESSMENT_FAILED")


@compliance_bp.route('/score/<onlus_id>/current', methods=['GET'])
@auth_required
def get_current_compliance_score(current_user, onlus_id):
    """Get current compliance score for an ONLUS."""
    try:
        success, message, compliance_score = compliance_service.compliance_repo.get_current_score_by_onlus(onlus_id)
        if not success:
            return error_response(message)

        return success_response("CURRENT_COMPLIANCE_SCORE_SUCCESS", compliance_score.to_dict())

    except Exception as e:
        current_app.logger.error(f"Get current compliance score failed: {str(e)}")
        return error_response("CURRENT_COMPLIANCE_SCORE_FAILED")


@compliance_bp.route('/score/<onlus_id>/history', methods=['GET'])
@auth_required
def get_compliance_history(current_user, onlus_id):
    """Get compliance score history for an ONLUS."""
    try:
        limit = min(int(request.args.get('limit', 50)), 100)
        skip = max(int(request.args.get('skip', 0)), 0)

        success, message, scores = compliance_service.compliance_repo.get_scores_by_onlus(
            onlus_id, limit, skip
        )
        if not success:
            return error_response(message)

        return success_response("ONLUS_COMPLIANCE_SCORES_SUCCESS", {
            "scores": [score.to_dict() for score in scores],
            "count": len(scores),
            "onlus_id": onlus_id,
            "pagination": {
                "limit": limit,
                "skip": skip
            }
        })

    except Exception as e:
        current_app.logger.error(f"Get compliance history failed: {str(e)}")
        return error_response("ONLUS_COMPLIANCE_SCORES_FAILED")


@compliance_bp.route('/monitoring/real-time', methods=['POST'])
@admin_required
def real_time_monitoring(current_user):
    """Perform real-time compliance monitoring."""
    try:
        data = request.get_json() or {}
        max_alerts = min(int(data.get('max_alerts', 100)), 500)

        success, message, monitoring_results = compliance_service.monitor_real_time_compliance(max_alerts)
        if not success:
            return error_response(message)

        current_app.logger.info(
            f"Real-time compliance monitoring by admin {current_user['user_id']}: "
            f"{monitoring_results['summary']['total_alerts']} alerts generated"
        )

        return success_response(message, monitoring_results)

    except Exception as e:
        current_app.logger.error(f"Real-time monitoring failed: {str(e)}")
        return error_response("COMPLIANCE_MONITORING_FAILED")


@compliance_bp.route('/dashboard', methods=['GET'])
@admin_required
def get_compliance_dashboard(current_user):
    """Get comprehensive compliance dashboard data."""
    try:
        include_trends = request.args.get('include_trends', 'true').lower() == 'true'

        success, message, dashboard_data = compliance_service.get_compliance_dashboard_data(include_trends)
        if not success:
            return error_response(message)

        return success_response(message, dashboard_data)

    except Exception as e:
        current_app.logger.error(f"Get compliance dashboard failed: {str(e)}")
        return error_response("COMPLIANCE_DASHBOARD_FAILED")


@compliance_bp.route('/high-risk', methods=['GET'])
@admin_required
def get_high_risk_organizations(current_user):
    """Get high-risk organizations requiring attention."""
    try:
        current_only = request.args.get('current_only', 'true').lower() == 'true'
        limit = min(int(request.args.get('limit', 50)), 100)

        success, message, scores = compliance_service.compliance_repo.get_high_risk_scores(
            current_only, limit
        )
        if not success:
            return error_response(message)

        return success_response("HIGH_RISK_SCORES_SUCCESS", {
            "high_risk_organizations": [score.to_dict() for score in scores],
            "count": len(scores),
            "current_only": current_only
        })

    except Exception as e:
        current_app.logger.error(f"Get high-risk organizations failed: {str(e)}")
        return error_response("HIGH_RISK_SCORES_FAILED")


@compliance_bp.route('/critical-issues', methods=['GET'])
@admin_required
def get_critical_issues(current_user):
    """Get organizations with critical compliance issues."""
    try:
        current_only = request.args.get('current_only', 'true').lower() == 'true'

        success, message, scores = compliance_service.compliance_repo.get_scores_with_critical_issues(current_only)
        if not success:
            return error_response(message)

        return success_response("CRITICAL_ISSUES_SCORES_SUCCESS", {
            "organizations_with_critical_issues": [score.to_dict() for score in scores],
            "count": len(scores)
        })

    except Exception as e:
        current_app.logger.error(f"Get critical issues failed: {str(e)}")
        return error_response("CRITICAL_ISSUES_SCORES_FAILED")


@compliance_bp.route('/score/<score_id>/issue', methods=['POST'])
@admin_required
def add_compliance_issue(current_user, score_id):
    """Add a compliance issue to a score."""
    try:
        data = request.get_json()
        if not data:
            return error_response("DATA_REQUIRED")

        required_fields = ['issue_type', 'description']
        for field in required_fields:
            if not data.get(field):
                return error_response("MISSING_REQUIRED_FIELD", {"field": field})

        issue_type = data['issue_type']
        description = data['description']
        severity = data.get('severity', 'medium')
        category = data.get('category')

        success, message, result_data = compliance_service.compliance_repo.add_compliance_issue(
            score_id, issue_type, description, severity, category
        )

        if not success:
            return error_response(message)

        current_app.logger.info(
            f"Compliance issue added to score {score_id} by admin {current_user['user_id']}: "
            f"{issue_type} ({severity})"
        )

        return success_response(message, result_data)

    except Exception as e:
        current_app.logger.error(f"Add compliance issue failed: {str(e)}")
        return error_response("COMPLIANCE_ISSUE_ADD_FAILED")


@compliance_bp.route('/score/<score_id>/issue/<issue_id>/resolve', methods=['POST'])
@admin_required
def resolve_compliance_issue(current_user, score_id, issue_id):
    """Resolve a compliance issue."""
    try:
        data = request.get_json() or {}
        resolution_notes = data.get('resolution_notes')

        success, message, result_data = compliance_service.compliance_repo.resolve_compliance_issue(
            score_id, issue_id, resolution_notes
        )

        if not success:
            return error_response(message)

        current_app.logger.info(
            f"Compliance issue resolved: {issue_id} in score {score_id} "
            f"by admin {current_user['user_id']}"
        )

        return success_response(message, result_data)

    except Exception as e:
        current_app.logger.error(f"Resolve compliance issue failed: {str(e)}")
        return error_response("COMPLIANCE_ISSUE_RESOLVE_FAILED")


@compliance_bp.route('/score/<score_id>/alert', methods=['POST'])
@admin_required
def add_monitoring_alert(current_user, score_id):
    """Add a monitoring alert to a compliance score."""
    try:
        data = request.get_json()
        if not data:
            return error_response("DATA_REQUIRED")

        required_fields = ['alert_type', 'message']
        for field in required_fields:
            if not data.get(field):
                return error_response("MISSING_REQUIRED_FIELD", {"field": field})

        alert_type = data['alert_type']
        message_text = data['message']
        urgency = data.get('urgency', 'medium')

        success, message, result_data = compliance_service.compliance_repo.add_monitoring_alert(
            score_id, alert_type, message_text, urgency
        )

        if not success:
            return error_response(message)

        return success_response(message, result_data)

    except Exception as e:
        current_app.logger.error(f"Add monitoring alert failed: {str(e)}")
        return error_response("MONITORING_ALERT_ADD_FAILED")


@compliance_bp.route('/score/<score_id>/alert/<alert_id>/dismiss', methods=['POST'])
@admin_required
def dismiss_monitoring_alert(current_user, score_id, alert_id):
    """Dismiss a monitoring alert."""
    try:
        success, message, result_data = compliance_service.compliance_repo.dismiss_monitoring_alert(
            score_id, alert_id
        )

        if not success:
            return error_response(message)

        return success_response(message, result_data)

    except Exception as e:
        current_app.logger.error(f"Dismiss monitoring alert failed: {str(e)}")
        return error_response("MONITORING_ALERT_DISMISS_FAILED")


@compliance_bp.route('/score/<score_id>/verify', methods=['POST'])
@admin_required
def verify_assessment(current_user, score_id):
    """Verify a compliance assessment."""
    try:
        data = request.get_json() or {}
        verification_notes = data.get('verification_notes')

        success, message, result_data = compliance_service.compliance_repo.verify_assessment(
            score_id, current_user['user_id'], verification_notes
        )

        if not success:
            return error_response(message)

        current_app.logger.info(
            f"Compliance assessment verified: {score_id} by admin {current_user['user_id']}"
        )

        return success_response(message, result_data)

    except Exception as e:
        current_app.logger.error(f"Verify assessment failed: {str(e)}")
        return error_response("ASSESSMENT_VERIFICATION_FAILED")


@compliance_bp.route('/statistics', methods=['GET'])
@admin_required
def get_compliance_statistics(current_user):
    """Get compliance statistics."""
    try:
        # Parse date range if provided
        start_date = None
        end_date = None
        current_only = request.args.get('current_only', 'true').lower() == 'true'

        if request.args.get('start_date'):
            try:
                start_date = datetime.fromisoformat(request.args.get('start_date'))
            except ValueError:
                return error_response("INVALID_START_DATE_FORMAT")

        if request.args.get('end_date'):
            try:
                end_date = datetime.fromisoformat(request.args.get('end_date'))
            except ValueError:
                return error_response("INVALID_END_DATE_FORMAT")

        success, message, statistics = compliance_service.compliance_repo.get_compliance_statistics(
            start_date, end_date, current_only
        )

        if not success:
            return error_response(message)

        return success_response("COMPLIANCE_STATISTICS_SUCCESS", {
            "statistics": statistics,
            "period": {
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
                "current_only": current_only
            },
            "generated_at": datetime.now(timezone.utc).isoformat()
        })

    except Exception as e:
        current_app.logger.error(f"Get compliance statistics failed: {str(e)}")
        return error_response("COMPLIANCE_STATISTICS_FAILED")


@compliance_bp.route('/trends', methods=['GET'])
@admin_required
def get_compliance_trends(current_user):
    """Get compliance score trends."""
    try:
        onlus_id = request.args.get('onlus_id')
        months = min(int(request.args.get('months', 12)), 60)

        success, message, trends = compliance_service.compliance_repo.get_compliance_trends(
            onlus_id, months
        )

        if not success:
            return error_response(message)

        return success_response("COMPLIANCE_TRENDS_SUCCESS", {
            "trends": trends,
            "onlus_id": onlus_id,
            "period_months": months
        })

    except Exception as e:
        current_app.logger.error(f"Get compliance trends failed: {str(e)}")
        return error_response("COMPLIANCE_TRENDS_FAILED")


@compliance_bp.route('/alerts/report', methods=['GET'])
@admin_required
def get_alerts_report(current_user):
    """Generate compliance alerts report."""
    try:
        days = min(int(request.args.get('days', 30)), 365)

        success, message, report_data = compliance_service.generate_compliance_alerts_report(days)
        if not success:
            return error_response(message)

        return success_response(message, report_data)

    except Exception as e:
        current_app.logger.error(f"Get alerts report failed: {str(e)}")
        return error_response("COMPLIANCE_ALERTS_REPORT_FAILED")


@compliance_bp.route('/assessment-due', methods=['GET'])
@admin_required
def get_assessments_due(current_user):
    """Get organizations with assessments due."""
    try:
        days_overdue = max(int(request.args.get('days_overdue', 0)), 0)

        success, message, scores = compliance_service.compliance_repo.get_scores_needing_assessment(days_overdue)
        if not success:
            return error_response(message)

        return success_response("ASSESSMENT_DUE_SCORES_SUCCESS", {
            "organizations_needing_assessment": [score.to_dict() for score in scores],
            "count": len(scores),
            "days_overdue_threshold": days_overdue
        })

    except Exception as e:
        current_app.logger.error(f"Get assessments due failed: {str(e)}")
        return error_response("ASSESSMENT_DUE_SCORES_FAILED")


@compliance_bp.route('/top-performers', methods=['GET'])
@auth_required
def get_top_performers(current_user):
    """Get top performing organizations by compliance score."""
    try:
        limit = min(int(request.args.get('limit', 20)), 100)
        current_only = request.args.get('current_only', 'true').lower() == 'true'

        success, message, scores = compliance_service.compliance_repo.get_top_performing_scores(
            limit, current_only
        )
        if not success:
            return error_response(message)

        return success_response("TOP_PERFORMING_SCORES_SUCCESS", {
            "top_performers": [score.to_dict() for score in scores],
            "count": len(scores),
            "limit": limit
        })

    except Exception as e:
        current_app.logger.error(f"Get top performers failed: {str(e)}")
        return error_response("TOP_PERFORMING_SCORES_FAILED")


# Error handlers
@compliance_bp.errorhandler(400)
def bad_request(error):
    return error_response("BAD_REQUEST", status_code=400)


@compliance_bp.errorhandler(403)
def forbidden(error):
    return error_response("ACCESS_DENIED", status_code=403)


@compliance_bp.errorhandler(404)
def not_found(error):
    return error_response("RESOURCE_NOT_FOUND", status_code=404)


@compliance_bp.errorhandler(500)
def internal_error(error):
    current_app.logger.error(f"Internal server error in compliance controller: {str(error)}")
    return error_response("INTERNAL_SERVER_ERROR", status_code=500)