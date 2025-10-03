from flask import Blueprint, request, current_app, jsonify
from typing import Dict, Any, Optional
from datetime import datetime, timezone, timedelta
import traceback

from app.core.utils.decorators import auth_required, admin_required
from app.core.utils.responses import success_response, error_response
from app.onlus.services.financial_reporting_service import FinancialReportingService
from app.onlus.services.audit_trail_service import AuditTrailService

from app.onlus.models.financial_report import ReportType, ReportFormat


# Create Blueprint
financial_bp = Blueprint('financial', __name__, url_prefix='/api/onlus/financial')

# Initialize services
reporting_service = FinancialReportingService()
audit_service = AuditTrailService()


@financial_bp.route('/reports', methods=['POST'])
@admin_required
def generate_report(current_user):
    """Generate a new financial report."""
    try:
        data = request.get_json()
        if not data:
            return error_response("DATA_REQUIRED")

        # Validate required fields
        required_fields = ['report_type', 'start_date', 'end_date']
        for field in required_fields:
            if not data.get(field):
                return error_response("MISSING_REQUIRED_FIELD", {"field": field})

        # Parse dates
        try:
            start_date = datetime.fromisoformat(data['start_date'])
            end_date = datetime.fromisoformat(data['end_date'])
        except ValueError:
            return error_response("INVALID_DATE_FORMAT")

        if start_date >= end_date:
            return error_response("INVALID_DATE_RANGE")

        # Validate report type
        valid_types = [e.value for e in ReportType]
        if data['report_type'] not in valid_types:
            return error_response("INVALID_REPORT_TYPE")

        # Validate format
        report_format = data.get('report_format', 'pdf')
        valid_formats = [e.value for e in ReportFormat]
        if report_format not in valid_formats:
            return error_response("INVALID_REPORT_FORMAT")

        entity_id = data.get('entity_id')  # ONLUS ID or donor ID

        # Generate report based on type
        if data['report_type'] == ReportType.DONOR_STATEMENT.value:
            if not entity_id:
                return error_response("DONOR_ID_REQUIRED_FOR_STATEMENT")

            include_tax_info = data.get('include_tax_info', True)
            success, message, result_data = reporting_service.generate_donor_statement(
                entity_id, start_date, end_date, include_tax_info, report_format
            )
        elif data['report_type'] == ReportType.ONLUS_STATEMENT.value:
            if not entity_id:
                return error_response("ONLUS_ID_REQUIRED_FOR_STATEMENT")

            months = data.get('months', 12)
            success, message, result_data = reporting_service.generate_onlus_financial_summary(
                entity_id, months, report_format
            )
        elif data['report_type'] == ReportType.AUDIT_REPORT.value:
            audit_scope = data.get('audit_scope', ['transactions', 'allocations', 'compliance'])
            success, message, result_data = reporting_service.generate_audit_report(
                start_date, end_date, audit_scope, report_format
            )
        else:
            # Periodic reports (monthly, quarterly, annual)
            success, message, result_data = reporting_service.generate_periodic_report(
                data['report_type'], start_date, end_date, entity_id, report_format
            )

        if not success:
            return error_response(message)

        # Create audit trail
        audit_service.audit_financial_report_generation(
            str(result_data['_id']),
            data['report_type'],
            start_date,
            end_date,
            current_user['user_id'],
            data
        )

        current_app.logger.info(
            f"Financial report generated: {result_data['_id']} "
            f"({data['report_type']}) by admin {current_user['user_id']}"
        )

        return success_response(message, result_data)

    except Exception as e:
        current_app.logger.error(f"Generate report failed: {str(e)}")
        return error_response("REPORT_GENERATION_FAILED")


@financial_bp.route('/reports/<report_id>', methods=['GET'])
@auth_required
def get_report(current_user, report_id):
    """Get financial report by ID."""
    try:
        success, message, report = reporting_service.report_repo.get_report_by_id(report_id)
        if not success:
            return error_response(message)

        # Check access permissions
        if not report.is_accessible_by(current_user['user_id']) and current_user['role'] != 'admin':
            return error_response("REPORT_ACCESS_DENIED", status_code=403)

        # Mark as downloaded if completed
        if report.status == "completed":
            reporting_service.report_repo.mark_report_downloaded(report_id, current_user['user_id'])

        return success_response("FINANCIAL_REPORT_RETRIEVED_SUCCESS", report.to_dict())

    except Exception as e:
        current_app.logger.error(f"Get report failed: {str(e)}")
        return error_response("FINANCIAL_REPORT_RETRIEVAL_FAILED")


@financial_bp.route('/reports', methods=['GET'])
@auth_required
def get_reports(current_user):
    """Get financial reports with filtering."""
    try:
        # Parse query parameters
        report_type = request.args.get('type')
        status = request.args.get('status')
        entity_id = request.args.get('entity_id')
        limit = min(int(request.args.get('limit', 50)), 100)
        skip = max(int(request.args.get('skip', 0)), 0)

        if report_type:
            success, message, reports = reporting_service.report_repo.get_reports_by_type(
                report_type, status, limit, skip
            )
        elif entity_id:
            success, message, reports = reporting_service.report_repo.get_reports_by_entity(
                entity_id, limit=limit, skip=skip
            )
        else:
            # Get accessible reports for user
            success, message, reports = reporting_service.report_repo.get_accessible_reports(
                current_user['user_id'], limit=limit, skip=skip
            )

        if not success:
            return error_response(message)

        # Calculate pagination metadata
        total_items = len(reports)
        page = (skip // limit) + 1
        total_pages = (total_items + limit - 1) // limit if total_items > 0 else 1

        return success_response("REPORTS_RETRIEVED_SUCCESS", {
            "reports": [report.to_dict() for report in reports],
            "count": total_items,
            "filters": {
                "type": report_type,
                "status": status,
                "entity_id": entity_id
            },
            "pagination": {
                "page": page,
                "per_page": limit,
                "total_items": total_items,
                "total_pages": total_pages,
                "has_next": (skip + limit) < total_items,
                "has_prev": skip > 0
            }
        })

    except Exception as e:
        current_app.logger.error(f"Get reports failed: {str(e)}")
        return error_response("REPORTS_RETRIEVAL_FAILED")


@financial_bp.route('/reports/<report_id>/export', methods=['POST'])
@auth_required
def export_report(current_user, report_id):
    """Export report data in specified format."""
    try:
        data = request.get_json() or {}
        export_format = data.get('format', 'csv').lower()

        if export_format not in ['csv', 'json']:
            return error_response("UNSUPPORTED_EXPORT_FORMAT")

        success, message, export_data = reporting_service.export_report_data(report_id, export_format)
        if not success:
            return error_response(message)

        # Create audit trail
        audit_service.audit_data_access(
            'financial_report',
            report_id,
            'export',
            current_user['user_id'],
            request.remote_addr,
            f"Export to {export_format}"
        )

        return success_response(message, export_data)

    except Exception as e:
        current_app.logger.error(f"Export report failed: {str(e)}")
        return error_response("REPORT_EXPORT_FAILED")


@financial_bp.route('/analytics/dashboard', methods=['GET'])
@auth_required
def get_analytics_dashboard(current_user):
    """Get real-time analytics dashboard data."""
    try:
        period_days = min(int(request.args.get('period', 30)), 365)

        success, message, dashboard_data = reporting_service.get_analytics_dashboard_data(period_days)
        if not success:
            return error_response(message)

        return success_response(message, dashboard_data)

    except Exception as e:
        current_app.logger.error(f"Get analytics dashboard failed: {str(e)}")
        return error_response("ANALYTICS_DASHBOARD_FAILED")


@financial_bp.route('/donor/<donor_id>/statement', methods=['POST'])
@auth_required
def generate_donor_statement(current_user, donor_id):
    """Generate donor statement for specific donor."""
    try:
        # Check access permissions (user can only access their own statement)
        if current_user['user_id'] != donor_id and current_user['role'] != 'admin':
            return error_response("ACCESS_DENIED", status_code=403)

        data = request.get_json()
        if not data:
            return error_response("DATA_REQUIRED")

        # Parse dates
        try:
            start_date = datetime.fromisoformat(data['start_date'])
            end_date = datetime.fromisoformat(data['end_date'])
        except (ValueError, KeyError):
            return error_response("INVALID_DATE_RANGE")

        include_tax_info = data.get('include_tax_info', True)
        report_format = data.get('format', 'pdf')

        success, message, result_data = reporting_service.generate_donor_statement(
            donor_id, start_date, end_date, include_tax_info, report_format
        )

        if not success:
            return error_response(message)

        return success_response(message, result_data)

    except Exception as e:
        current_app.logger.error(f"Generate donor statement failed: {str(e)}")
        return error_response("DONOR_STATEMENT_GENERATION_FAILED")


@financial_bp.route('/onlus/<onlus_id>/summary', methods=['POST'])
@auth_required
def generate_onlus_summary(current_user, onlus_id):
    """Generate financial summary for ONLUS."""
    try:
        data = request.get_json() or {}
        months = min(int(data.get('months', 12)), 60)  # Max 5 years
        report_format = data.get('format', 'pdf')

        success, message, result_data = reporting_service.generate_onlus_financial_summary(
            onlus_id, months, report_format
        )

        if not success:
            return error_response(message)

        return success_response(message, result_data)

    except Exception as e:
        current_app.logger.error(f"Generate ONLUS summary failed: {str(e)}")
        return error_response("ONLUS_SUMMARY_GENERATION_FAILED")


@financial_bp.route('/reports/search', methods=['GET'])
@auth_required
def search_reports(current_user):
    """Search financial reports."""
    try:
        query_text = request.args.get('q', '').strip()
        if not query_text:
            return error_response("SEARCH_QUERY_REQUIRED")

        # Parse filters
        filters = {}
        if request.args.get('type'):
            filters['report_type'] = request.args.get('type')
        if request.args.get('status'):
            filters['status'] = request.args.get('status')
        if request.args.get('entity_id'):
            filters['generated_for_id'] = request.args.get('entity_id')
        if request.args.get('start_date'):
            try:
                filters['start_date_from'] = datetime.fromisoformat(request.args.get('start_date'))
            except ValueError:
                pass
        if request.args.get('end_date'):
            try:
                filters['end_date_to'] = datetime.fromisoformat(request.args.get('end_date'))
            except ValueError:
                pass
        if request.args.get('confidential') is not None:
            filters['is_confidential'] = request.args.get('confidential').lower() == 'true'

        limit = min(int(request.args.get('limit', 50)), 100)
        skip = max(int(request.args.get('skip', 0)), 0)

        success, message, reports = reporting_service.report_repo.search_reports(
            query_text, filters, limit, skip
        )

        if not success:
            return error_response(message)

        # Calculate pagination metadata
        total_items = len(reports)
        page = (skip // limit) + 1
        total_pages = (total_items + limit - 1) // limit if total_items > 0 else 1

        return success_response(message, {
            "reports": [report.to_dict() for report in reports],
            "count": total_items,
            "query": query_text,
            "filters": filters,
            "pagination": {
                "page": page,
                "per_page": limit,
                "total_items": total_items,
                "total_pages": total_pages,
                "has_next": (skip + limit) < total_items,
                "has_prev": skip > 0
            }
        })

    except Exception as e:
        current_app.logger.error(f"Search reports failed: {str(e)}")
        return error_response("REPORTS_SEARCH_FAILED")


@financial_bp.route('/reports/statistics', methods=['GET'])
@admin_required
def get_reports_statistics(current_user):
    """Get financial reports statistics."""
    try:
        # Parse date range if provided
        start_date = None
        end_date = None

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

        success, message, statistics = reporting_service.report_repo.get_reports_statistics(
            start_date, end_date
        )

        if not success:
            return error_response(message)

        return success_response("REPORTS_STATISTICS_SUCCESS", {
            "statistics": statistics,
            "period": {
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None
            },
            "generated_at": datetime.now(timezone.utc).isoformat()
        })

    except Exception as e:
        current_app.logger.error(f"Get reports statistics failed: {str(e)}")
        return error_response("REPORTS_STATISTICS_FAILED")


@financial_bp.route('/reports/<report_id>/access', methods=['POST'])
@admin_required
def grant_report_access(current_user, report_id):
    """Grant access to confidential report."""
    try:
        data = request.get_json()
        if not data or 'user_id' not in data:
            return error_response("USER_ID_REQUIRED")

        user_id = data['user_id']

        success, message, result_data = reporting_service.report_repo.grant_report_access(
            report_id, user_id
        )

        if not success:
            return error_response(message)

        current_app.logger.info(
            f"Report access granted: {report_id} to user {user_id} "
            f"by admin {current_user['user_id']}"
        )

        return success_response(message, result_data)

    except Exception as e:
        current_app.logger.error(f"Grant report access failed: {str(e)}")
        return error_response("REPORT_ACCESS_GRANT_FAILED")


@financial_bp.route('/reports/<report_id>/access/<user_id>', methods=['DELETE'])
@admin_required
def revoke_report_access(current_user, report_id, user_id):
    """Revoke access to confidential report."""
    try:
        success, message, result_data = reporting_service.report_repo.revoke_report_access(
            report_id, user_id
        )

        if not success:
            return error_response(message)

        current_app.logger.info(
            f"Report access revoked: {report_id} from user {user_id} "
            f"by admin {current_user['user_id']}"
        )

        return success_response(message, result_data)

    except Exception as e:
        current_app.logger.error(f"Revoke report access failed: {str(e)}")
        return error_response("REPORT_ACCESS_REVOKE_FAILED")


# Error handlers
@financial_bp.errorhandler(400)
def bad_request(error):
    return error_response("BAD_REQUEST", status_code=400)


@financial_bp.errorhandler(403)
def forbidden(error):
    return error_response("ACCESS_DENIED", status_code=403)


@financial_bp.errorhandler(404)
def not_found(error):
    return error_response("RESOURCE_NOT_FOUND", status_code=404)


@financial_bp.errorhandler(500)
def internal_error(error):
    current_app.logger.error(f"Internal server error in financial controller: {str(error)}")
    return error_response("INTERNAL_SERVER_ERROR", status_code=500)