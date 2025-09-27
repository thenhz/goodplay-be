from flask import Blueprint, request, current_app
from datetime import datetime, timezone, timedelta
from app.core.utils.decorators import admin_required
from app.core.utils.responses import success_response, error_response
from app.donations.services.financial_analytics_service import FinancialAnalyticsService
from typing import Optional, Dict, Any

financial_admin_bp = Blueprint('financial_admin', __name__, url_prefix='/api/admin/financial')

# Global service instance with lazy initialization
financial_analytics_service = None

def get_financial_analytics_service():
    """Get or create financial analytics service instance."""
    global financial_analytics_service
    if financial_analytics_service is None:
        financial_analytics_service = FinancialAnalyticsService()
    return financial_analytics_service


@financial_admin_bp.route('/dashboard', methods=['GET'])
@admin_required
def get_financial_dashboard(current_user):
    """
    Get comprehensive financial dashboard for admin.

    Returns financial KPIs, trends, user analytics, payment metrics,
    performance data, and forecasting for admin oversight.
    """
    try:
        # Get query parameters for date range
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

        date_range = {
            'start_date': start_date,
            'end_date': end_date
        }

        success, message, dashboard_data = get_financial_analytics_service().generate_financial_dashboard(date_range)

        if success:
            return success_response(message, dashboard_data)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Failed to generate financial dashboard: {str(e)}")
        return error_response("FINANCIAL_DASHBOARD_ERROR", status_code=500)


@financial_admin_bp.route('/metrics', methods=['GET'])
@admin_required
def get_financial_metrics(current_user):
    """
    Get specific financial metrics with custom parameters.

    Allows filtering by metric type, period, and custom date ranges
    for detailed financial analysis.
    """
    try:
        # Get query parameters
        metric_types = request.args.getlist('metric_type')  # Multiple metrics allowed
        period = request.args.get('period', 'daily')
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

        # Validate parameters
        valid_periods = ['hourly', 'daily', 'weekly', 'monthly']
        if period not in valid_periods:
            return error_response("INVALID_PERIOD")

        valid_metric_types = ['volume', 'count', 'average', 'growth_rate', 'conversion_rate', 'distribution']
        if metric_types:
            invalid_metrics = [m for m in metric_types if m not in valid_metric_types]
            if invalid_metrics:
                return error_response("INVALID_METRIC_TYPES")

        success, message, metrics_data = get_financial_analytics_service().get_custom_metrics(
            start_date=start_date,
            end_date=end_date,
            metric_types=metric_types or valid_metric_types,
            period=period
        )

        if success:
            return success_response(message, metrics_data)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Failed to get financial metrics: {str(e)}")
        return error_response("FINANCIAL_METRICS_ERROR", status_code=500)


@financial_admin_bp.route('/trends', methods=['GET'])
@admin_required
def get_financial_trends(current_user):
    """
    Get financial trend analysis for specific metrics.

    Returns detailed trend data with moving averages, volatility,
    and trend direction for admin financial monitoring.
    """
    try:
        # Get query parameters
        metric = request.args.get('metric', 'volume')
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

        # Validate metric
        valid_metrics = ['volume', 'count', 'average']
        if metric not in valid_metrics:
            return error_response("INVALID_METRIC")

        success, message, trend_data = get_financial_analytics_service().get_trend_analysis(
            start_date=start_date,
            end_date=end_date,
            metric=metric
        )

        if success:
            return success_response(message, trend_data)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Failed to get financial trends: {str(e)}")
        return error_response("FINANCIAL_TRENDS_ERROR", status_code=500)


@financial_admin_bp.route('/analytics/users', methods=['GET'])
@admin_required
def get_user_analytics(current_user):
    """
    Get user behavior analytics and segmentation.

    Returns detailed user segmentation, behavior patterns,
    retention metrics, and value distribution analysis.
    """
    try:
        # Get query parameters
        days_back = int(request.args.get('days', 30))
        segment = request.args.get('segment')  # Optional filter by segment

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

        # Validate segment if provided
        if segment:
            valid_segments = ['new_donors', 'returning_donors', 'high_value', 'frequent_donors']
            if segment not in valid_segments:
                return error_response("INVALID_USER_SEGMENT")

        success, message, user_analytics = get_financial_analytics_service().get_user_behavior_analytics(
            start_date=start_date,
            end_date=end_date,
            segment_filter=segment
        )

        if success:
            return success_response(message, user_analytics)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Failed to get user analytics: {str(e)}")
        return error_response("USER_ANALYTICS_ERROR", status_code=500)


@financial_admin_bp.route('/analytics/payments', methods=['GET'])
@admin_required
def get_payment_analytics(current_user):
    """
    Get payment processing analytics and insights.

    Returns payment method distribution, success rates, processing times,
    fee analysis, and failure pattern detection.
    """
    try:
        # Get query parameters
        days_back = int(request.args.get('days', 30))
        payment_method = request.args.get('payment_method')  # Optional filter

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

        success, message, payment_analytics = get_financial_analytics_service().get_payment_analytics(
            start_date=start_date,
            end_date=end_date,
            payment_method_filter=payment_method
        )

        if success:
            return success_response(message, payment_analytics)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Failed to get payment analytics: {str(e)}")
        return error_response("PAYMENT_ANALYTICS_ERROR", status_code=500)


@financial_admin_bp.route('/forecasting', methods=['GET'])
@admin_required
def get_financial_forecasting(current_user):
    """
    Get financial forecasting data and predictions.

    Returns short-term and medium-term predictions for donation volumes,
    user growth, and revenue projections with confidence intervals.
    """
    try:
        # Get query parameters
        forecast_days = int(request.args.get('forecast_days', 7))
        metric = request.args.get('metric', 'volume')

        # Validate parameters
        if forecast_days < 1 or forecast_days > 90:
            return error_response("INVALID_FORECAST_PERIOD")

        valid_metrics = ['volume', 'count', 'average']
        if metric not in valid_metrics:
            return error_response("INVALID_FORECAST_METRIC")

        success, message, forecast_data = get_financial_analytics_service().generate_forecasting_report(
            forecast_days=forecast_days,
            metric=metric
        )

        if success:
            return success_response(message, forecast_data)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Failed to get financial forecasting: {str(e)}")
        return error_response("FINANCIAL_FORECASTING_ERROR", status_code=500)


@financial_admin_bp.route('/performance', methods=['GET'])
@admin_required
def get_system_performance(current_user):
    """
    Get financial system performance metrics.

    Returns API response times, throughput metrics, error rates,
    and system health indicators for operational monitoring.
    """
    try:
        # Get query parameters
        hours_back = int(request.args.get('hours', 24))

        # Calculate time range
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=hours_back)

        success, message, performance_data = get_financial_analytics_service().get_system_performance_metrics(
            start_time=start_time,
            end_time=end_time
        )

        if success:
            return success_response(message, performance_data)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Failed to get system performance: {str(e)}")
        return error_response("SYSTEM_PERFORMANCE_ERROR", status_code=500)


@financial_admin_bp.route('/reports/custom', methods=['POST'])
@admin_required
def generate_custom_report(current_user):
    """
    Generate custom financial report with specific parameters.

    Admin endpoint to create tailored reports with custom metrics,
    date ranges, filters, and export formats.
    """
    try:
        data = request.get_json()
        if not data:
            return error_response("DATA_REQUIRED")

        # Extract report parameters
        report_name = data.get('report_name', 'Custom Financial Report')
        start_date_str = data.get('start_date')
        end_date_str = data.get('end_date')
        metrics = data.get('metrics', ['volume', 'count', 'average'])
        filters = data.get('filters', {})
        group_by = data.get('group_by', 'daily')

        # Validate required fields
        if not start_date_str or not end_date_str:
            return error_response("DATE_RANGE_REQUIRED")

        # Parse dates
        try:
            start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
            end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
        except ValueError:
            return error_response("INVALID_DATE_FORMAT")

        # Validate date range
        if start_date >= end_date:
            return error_response("INVALID_DATE_RANGE")

        # Validate metrics
        valid_metrics = ['volume', 'count', 'average', 'growth_rate', 'conversion_rate']
        invalid_metrics = [m for m in metrics if m not in valid_metrics]
        if invalid_metrics:
            return error_response("INVALID_METRICS")

        # Validate group_by
        valid_group_by = ['hourly', 'daily', 'weekly', 'monthly']
        if group_by not in valid_group_by:
            return error_response("INVALID_GROUP_BY")

        success, message, report_data = get_financial_analytics_service().generate_custom_report(
            report_name=report_name,
            start_date=start_date,
            end_date=end_date,
            metrics=metrics,
            filters=filters,
            group_by=group_by
        )

        if success:
            return success_response(message, report_data)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Failed to generate custom report: {str(e)}")
        return error_response("CUSTOM_REPORT_ERROR", status_code=500)


@financial_admin_bp.route('/export', methods=['POST'])
@admin_required
def export_financial_data(current_user):
    """
    Export financial data in various formats.

    Creates downloadable financial reports in CSV, Excel, or PDF
    for external analysis and regulatory reporting.
    """
    try:
        data = request.get_json()
        if not data:
            return error_response("DATA_REQUIRED")

        # Get export parameters
        export_format = data.get('format', 'csv')  # csv, excel, pdf
        export_type = data.get('export_type', 'dashboard')  # dashboard, metrics, transactions
        date_range = data.get('date_range', {})
        filters = data.get('filters', {})

        # Validate export format
        valid_formats = ['csv', 'excel', 'pdf']
        if export_format not in valid_formats:
            return error_response("INVALID_EXPORT_FORMAT")

        # Validate export type
        valid_types = ['dashboard', 'metrics', 'transactions', 'analytics']
        if export_type not in valid_types:
            return error_response("INVALID_EXPORT_TYPE")

        # For now, return placeholder export info
        # In production, this would generate the actual export file
        export_result = {
            'export_id': f"FINEXP-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'format': export_format,
            'export_type': export_type,
            'status': 'processing',
            'estimated_completion': '3 minutes',
            'download_available_at': None,  # Will be populated when ready
            'includes': {
                'date_range': date_range,
                'filters': filters,
                'estimated_records': 500
            },
            'created_by': current_user.get('user_id', 'admin'),
            'created_at': datetime.now(timezone.utc).isoformat()
        }

        return success_response("FINANCIAL_EXPORT_INITIATED", export_result)

    except Exception as e:
        current_app.logger.error(f"Failed to initiate financial export: {str(e)}")
        return error_response("FINANCIAL_EXPORT_ERROR", status_code=500)


@financial_admin_bp.route('/alerts', methods=['GET'])
@admin_required
def get_financial_alerts(current_user):
    """
    Get financial system alerts and anomalies.

    Returns alerts for unusual patterns, system issues,
    threshold breaches, and other financial anomalies.
    """
    try:
        # Get query parameters
        alert_type = request.args.get('alert_type')  # 'anomaly', 'threshold', 'system'
        severity = request.args.get('severity')  # 'low', 'medium', 'high', 'critical'
        limit = min(int(request.args.get('limit', 20)), 50)

        # For now, return placeholder alerts
        # In production, this would query the alerts database
        alerts = [
            {
                'alert_id': 'FINA-001',
                'alert_type': 'anomaly',
                'severity': 'high',
                'title': 'Unusual donation spike detected',
                'description': 'Donation volume 300% higher than normal in last hour',
                'metric': 'volume',
                'threshold': 1000.00,
                'current_value': 3000.00,
                'created_at': datetime.now(timezone.utc).isoformat(),
                'requires_attention': True
            },
            {
                'alert_id': 'FINA-002',
                'alert_type': 'threshold',
                'severity': 'medium',
                'title': 'Payment failure rate exceeded threshold',
                'description': 'Payment failure rate at 8.5%, threshold is 5%',
                'metric': 'failure_rate',
                'threshold': 5.0,
                'current_value': 8.5,
                'created_at': (datetime.now(timezone.utc) - timedelta(minutes=30)).isoformat(),
                'requires_attention': True
            },
            {
                'alert_id': 'FINA-003',
                'alert_type': 'system',
                'severity': 'low',
                'title': 'Analytics cache invalidated',
                'description': 'Financial analytics cache was cleared due to data update',
                'metric': 'system_health',
                'threshold': None,
                'current_value': None,
                'created_at': (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(),
                'requires_attention': False
            }
        ]

        # Apply filters
        if alert_type:
            alerts = [a for a in alerts if a['alert_type'] == alert_type]

        if severity:
            alerts = [a for a in alerts if a['severity'] == severity]

        # Sort by severity and creation date
        severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        alerts.sort(key=lambda x: (severity_order.get(x['severity'], 3), x['created_at']))

        # Limit results
        alerts = alerts[:limit]

        return success_response("FINANCIAL_ALERTS_RETRIEVED", {
            'alerts': alerts,
            'critical_count': len([a for a in alerts if a['severity'] == 'critical']),
            'high_count': len([a for a in alerts if a['severity'] == 'high']),
            'total_count': len(alerts),
            'filters': {
                'alert_type': alert_type,
                'severity': severity,
                'limit': limit
            }
        })

    except Exception as e:
        current_app.logger.error(f"Failed to get financial alerts: {str(e)}")
        return error_response("FINANCIAL_ALERTS_ERROR", status_code=500)