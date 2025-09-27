from flask import Blueprint, request, current_app
from datetime import datetime, timezone, timedelta
from app.core.utils.decorators import admin_required
from app.core.utils.responses import success_response, error_response
from app.donations.services.compliance_service import ComplianceService
from typing import Optional

compliance_bp = Blueprint('compliance', __name__, url_prefix='/api/compliance')

# Global service instance with lazy initialization
compliance_service = None

def get_compliance_service():
    """Get or create compliance service instance."""
    global compliance_service
    if compliance_service is None:
        compliance_service = ComplianceService()
    return compliance_service


@compliance_bp.route('/checks', methods=['POST'])
@admin_required
def initiate_compliance_check(current_user):
    """
    Initiate a compliance check for a user or transaction.

    Admin endpoint to start AML, KYC, sanctions, or fraud checks.
    Supports both user-level and transaction-level checks.
    """
    try:
        data = request.get_json()
        if not data:
            return error_response("DATA_REQUIRED")

        # Validate required fields
        user_id = data.get('user_id')
        check_type = data.get('check_type')

        if not user_id:
            return error_response("USER_ID_REQUIRED")

        if not check_type:
            return error_response("CHECK_TYPE_REQUIRED")

        # Optional fields
        transaction_id = data.get('transaction_id')
        reason = data.get('reason', f"Admin initiated {check_type} check")
        check_criteria = data.get('check_criteria', {})

        success, message, result = get_compliance_service().initiate_compliance_check(
            user_id=user_id,
            check_type=check_type,
            transaction_id=transaction_id,
            reason=reason,
            check_criteria=check_criteria
        )

        if success:
            return success_response(message, result)
        else:
            return error_response(message, result)

    except Exception as e:
        current_app.logger.error(f"Failed to initiate compliance check: {str(e)}")
        return error_response("COMPLIANCE_CHECK_INITIATION_ERROR", status_code=500)


@compliance_bp.route('/checks/<check_id>/review', methods=['POST'])
@admin_required
def review_compliance_check(current_user, check_id: str):
    """
    Review a compliance check manually.

    Admin endpoint to approve, reject, or escalate compliance checks
    that require manual review.
    """
    try:
        if not check_id:
            return error_response("CHECK_ID_REQUIRED")

        data = request.get_json()
        if not data:
            return error_response("DATA_REQUIRED")

        # Validate required fields
        decision = data.get('decision')
        if not decision:
            return error_response("REVIEW_DECISION_REQUIRED")

        valid_decisions = ['approve', 'reject', 'escalate']
        if decision not in valid_decisions:
            return error_response("INVALID_REVIEW_DECISION")

        review_notes = data.get('review_notes', '')
        reviewer_id = current_user.get('user_id', 'admin')

        success, message, result = get_compliance_service().review_compliance_check(
            check_id=check_id,
            reviewer_id=reviewer_id,
            decision=decision,
            review_notes=review_notes
        )

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Failed to review compliance check {check_id}: {str(e)}")
        return error_response("COMPLIANCE_REVIEW_ERROR", status_code=500)


@compliance_bp.route('/users/<user_id>/status', methods=['GET'])
@admin_required
def get_user_compliance_status(current_user, user_id: str):
    """
    Get overall compliance status for a specific user.

    Returns user's compliance history, current status,
    pending checks, and risk assessment.
    """
    try:
        if not user_id:
            return error_response("USER_ID_REQUIRED")

        success, message, status = get_compliance_service().get_compliance_status(user_id)

        if success:
            return success_response(message, status)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Failed to get compliance status for user {user_id}: {str(e)}")
        return error_response("COMPLIANCE_STATUS_ERROR", status_code=500)


@compliance_bp.route('/reports', methods=['GET'])
@admin_required
def generate_compliance_report(current_user):
    """
    Generate compliance report for admin dashboard.

    Supports different report types: summary, detailed, regulatory.
    Allows filtering by date range and compliance check types.
    """
    try:
        # Get query parameters
        report_type = request.args.get('report_type', 'summary')
        days_back = int(request.args.get('days', 30))

        # Calculate date range
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days_back)

        # Override with specific dates if provided
        start_date_param = request.args.get('start_date')
        end_date_param = request.args.get('end_date')

        if start_date_param:
            try:
                start_date = datetime.fromisoformat(start_date_param.replace('Z', '+00:00'))
            except ValueError:
                return error_response("INVALID_START_DATE_FORMAT")

        if end_date_param:
            try:
                end_date = datetime.fromisoformat(end_date_param.replace('Z', '+00:00'))
            except ValueError:
                return error_response("INVALID_END_DATE_FORMAT")

        # Validate date range
        if start_date >= end_date:
            return error_response("INVALID_DATE_RANGE")

        success, message, report = get_compliance_service().generate_compliance_report(
            start_date=start_date,
            end_date=end_date,
            report_type=report_type
        )

        if success:
            return success_response(message, report)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Failed to generate compliance report: {str(e)}")
        return error_response("COMPLIANCE_REPORT_ERROR", status_code=500)


@compliance_bp.route('/checks/pending', methods=['GET'])
@admin_required
def get_pending_compliance_checks(current_user):
    """
    Get all compliance checks pending manual review.

    Returns list of checks that require admin attention,
    sorted by priority and creation date.
    """
    try:
        # Get query parameters
        check_type = request.args.get('check_type')
        risk_level = request.args.get('risk_level')
        limit = min(int(request.args.get('limit', 50)), 100)  # Max 100 items

        # For now, return placeholder pending checks
        # In production, this would query the compliance checks database
        pending_checks = [
            {
                'check_id': 'CHK-20250927-001',
                'user_id': 'user123',
                'check_type': 'aml',
                'risk_level': 'high',
                'created_at': '2025-09-27T10:00:00Z',
                'pending_since_hours': 2,
                'reason': 'High transaction velocity detected',
                'priority': 'high'
            },
            {
                'check_id': 'CHK-20250927-002',
                'user_id': 'user456',
                'check_type': 'kyc',
                'risk_level': 'medium',
                'created_at': '2025-09-27T09:30:00Z',
                'pending_since_hours': 3,
                'reason': 'Document verification required',
                'priority': 'medium'
            },
            {
                'check_id': 'CHK-20250927-003',
                'user_id': 'user789',
                'check_type': 'sanctions',
                'risk_level': 'critical',
                'created_at': '2025-09-27T08:15:00Z',
                'pending_since_hours': 4,
                'reason': 'Potential sanctions match',
                'priority': 'critical'
            }
        ]

        # Apply filters
        if check_type:
            pending_checks = [c for c in pending_checks if c['check_type'] == check_type]

        if risk_level:
            pending_checks = [c for c in pending_checks if c['risk_level'] == risk_level]

        # Sort by priority (critical, high, medium, low) and creation date
        priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        pending_checks.sort(key=lambda x: (priority_order.get(x['priority'], 3), x['created_at']))

        # Limit results
        pending_checks = pending_checks[:limit]

        return success_response("PENDING_CHECKS_RETRIEVED", {
            'pending_checks': pending_checks,
            'total_count': len(pending_checks),
            'filters': {
                'check_type': check_type,
                'risk_level': risk_level,
                'limit': limit
            }
        })

    except Exception as e:
        current_app.logger.error(f"Failed to get pending compliance checks: {str(e)}")
        return error_response("PENDING_CHECKS_ERROR", status_code=500)


@compliance_bp.route('/alerts', methods=['GET'])
@admin_required
def get_compliance_alerts(current_user):
    """
    Get compliance alerts requiring immediate attention.

    Returns high-priority alerts for critical compliance issues,
    expired checks, and system anomalies.
    """
    try:
        # Get query parameters
        alert_type = request.args.get('alert_type')  # 'critical', 'expired', 'anomaly'
        limit = min(int(request.args.get('limit', 20)), 50)  # Max 50 alerts

        # For now, return placeholder alerts
        # In production, this would query compliance alerts from database
        alerts = [
            {
                'alert_id': 'ALERT-001',
                'alert_type': 'critical',
                'severity': 'high',
                'title': 'Multiple failed sanctions checks',
                'description': 'User user789 has failed sanctions screening multiple times',
                'check_id': 'CHK-20250927-003',
                'user_id': 'user789',
                'created_at': '2025-09-27T11:00:00Z',
                'requires_immediate_action': True,
                'escalation_level': 2
            },
            {
                'alert_id': 'ALERT-002',
                'alert_type': 'expired',
                'severity': 'medium',
                'title': 'KYC check expired',
                'description': 'KYC verification for user456 has expired without completion',
                'check_id': 'CHK-20250925-015',
                'user_id': 'user456',
                'created_at': '2025-09-27T09:00:00Z',
                'requires_immediate_action': False,
                'escalation_level': 0
            },
            {
                'alert_id': 'ALERT-003',
                'alert_type': 'anomaly',
                'severity': 'medium',
                'title': 'Unusual compliance pattern detected',
                'description': 'Spike in AML failures in the last 24 hours',
                'check_id': None,
                'user_id': None,
                'created_at': '2025-09-27T08:30:00Z',
                'requires_immediate_action': False,
                'escalation_level': 0
            }
        ]

        # Apply filters
        if alert_type:
            alerts = [a for a in alerts if a['alert_type'] == alert_type]

        # Sort by severity and creation date
        severity_order = {'high': 0, 'medium': 1, 'low': 2}
        alerts.sort(key=lambda x: (severity_order.get(x['severity'], 2), x['created_at']))

        # Limit results
        alerts = alerts[:limit]

        return success_response("COMPLIANCE_ALERTS_RETRIEVED", {
            'alerts': alerts,
            'critical_count': len([a for a in alerts if a['severity'] == 'high']),
            'total_count': len(alerts),
            'filters': {
                'alert_type': alert_type,
                'limit': limit
            }
        })

    except Exception as e:
        current_app.logger.error(f"Failed to get compliance alerts: {str(e)}")
        return error_response("COMPLIANCE_ALERTS_ERROR", status_code=500)


@compliance_bp.route('/settings', methods=['GET'])
@admin_required
def get_compliance_settings(current_user):
    """
    Get current compliance system settings and thresholds.

    Returns configurable compliance parameters, risk thresholds,
    and system configuration for admin review.
    """
    try:
        # Get current compliance settings from service
        service = get_compliance_service()

        settings = {
            'risk_thresholds': service.risk_thresholds,
            'aml_rules': service.aml_rules,
            'system_settings': {
                'auto_check_enabled': True,
                'manual_review_required_threshold': 70,
                'escalation_threshold': 2,
                'check_expiration_days': 30,
                'notification_enabled': True,
                'audit_logging_enabled': True
            },
            'supported_check_types': [
                'aml', 'kyc', 'sanctions', 'pep', 'fraud', 'tax_compliance'
            ],
            'supported_risk_levels': [
                'low', 'medium', 'high', 'critical'
            ],
            'last_updated': datetime.now(timezone.utc).isoformat(),
            'updated_by': 'system'
        }

        return success_response("COMPLIANCE_SETTINGS_RETRIEVED", settings)

    except Exception as e:
        current_app.logger.error(f"Failed to get compliance settings: {str(e)}")
        return error_response("COMPLIANCE_SETTINGS_ERROR", status_code=500)


@compliance_bp.route('/settings', methods=['PUT'])
@admin_required
def update_compliance_settings(current_user):
    """
    Update compliance system settings and thresholds.

    Admin endpoint to modify risk thresholds, AML rules,
    and other compliance configuration parameters.
    """
    try:
        data = request.get_json()
        if not data:
            return error_response("DATA_REQUIRED")

        # For now, return placeholder response
        # In production, this would update the compliance configuration
        updated_settings = {
            'updated_fields': list(data.keys()),
            'updated_at': datetime.now(timezone.utc).isoformat(),
            'updated_by': current_user.get('user_id', 'admin'),
            'changes_applied': True
        }

        current_app.logger.info(f"Compliance settings updated by {current_user.get('user_id')}: {list(data.keys())}")

        return success_response("COMPLIANCE_SETTINGS_UPDATED", updated_settings)

    except Exception as e:
        current_app.logger.error(f"Failed to update compliance settings: {str(e)}")
        return error_response("COMPLIANCE_SETTINGS_UPDATE_ERROR", status_code=500)


@compliance_bp.route('/export', methods=['POST'])
@admin_required
def export_compliance_data(current_user):
    """
    Export compliance data for regulatory reporting.

    Creates downloadable compliance reports in various formats
    for regulatory authorities and internal audits.
    """
    try:
        data = request.get_json()
        if not data:
            return error_response("DATA_REQUIRED")

        # Get export parameters
        export_format = data.get('format', 'csv')  # csv, excel, pdf
        date_range = data.get('date_range', {})
        include_types = data.get('include_types', ['aml', 'kyc', 'sanctions'])

        # Validate export format
        valid_formats = ['csv', 'excel', 'pdf']
        if export_format not in valid_formats:
            return error_response("INVALID_EXPORT_FORMAT")

        # For now, return placeholder export info
        # In production, this would generate the actual export file
        export_result = {
            'export_id': f"EXP-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'format': export_format,
            'status': 'processing',
            'estimated_completion': '5 minutes',
            'download_available_at': None,  # Will be populated when ready
            'includes': {
                'check_types': include_types,
                'date_range': date_range,
                'total_records': 150  # Estimated
            },
            'created_by': current_user.get('user_id', 'admin'),
            'created_at': datetime.now(timezone.utc).isoformat()
        }

        return success_response("COMPLIANCE_EXPORT_INITIATED", export_result)

    except Exception as e:
        current_app.logger.error(f"Failed to initiate compliance export: {str(e)}")
        return error_response("COMPLIANCE_EXPORT_ERROR", status_code=500)