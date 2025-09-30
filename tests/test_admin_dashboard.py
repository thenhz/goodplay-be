import pytest
import os
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta

# Set testing environment before importing app modules
os.environ['TESTING'] = 'true'

from app.admin.services.dashboard_service import DashboardService
from app.admin.services.monitoring_service import MonitoringService
from app.admin.models.system_metric import SystemMetric, MetricType
from app.admin.models.admin_action import AdminAction, ActionType


class TestDashboardService:
    """Test dashboard service functionality"""

    @patch('app.admin.services.dashboard_service.MetricsRepository')
    @patch('app.admin.services.dashboard_service.AuditRepository')
    def test_dashboard_service_initialization(self, mock_audit_repo, mock_metrics_repo):
        """Test dashboard service initialization"""
        service = DashboardService()
        assert service.metrics_repository is not None
        assert service.audit_repository is not None

    @patch('app.admin.services.dashboard_service.MetricsRepository')
    @patch('app.admin.services.dashboard_service.AuditRepository')
    def test_get_overview_dashboard_data(self, mock_audit_repo, mock_metrics_repo):
        """Test overview dashboard data retrieval"""
        # Setup mocks
        mock_metrics_instance = MagicMock()
        mock_metrics_repo.return_value = mock_metrics_instance
        mock_audit_instance = MagicMock()
        mock_audit_repo.return_value = mock_audit_instance

        # Mock recent metrics
        mock_performance_metric = SystemMetric.create_performance_metric(
            cpu_usage=75.0,
            memory_usage=68.0,
            response_time_avg=95.0,
            error_rate=0.05,
            active_sessions=150
        )
        mock_metrics_instance.get_latest_by_type.return_value = mock_performance_metric

        # Mock recent actions
        mock_actions = [
            AdminAction.create_user_action("admin1", "user_suspend", "user123"),
            AdminAction.create_user_action("admin2", "user_activate", "user456")
        ]
        mock_audit_instance.get_recent_actions.return_value = mock_actions

        service = DashboardService()

        # Get overview data
        success, message, data = service.get_overview_dashboard()

        assert success
        assert message == "DASHBOARD_OVERVIEW_SUCCESS"
        assert data is not None
        assert "system_health" in data
        assert "user_stats" in data
        assert "recent_activities" in data
        assert "performance_metrics" in data

    @patch('app.admin.services.dashboard_service.MetricsRepository')
    @patch('app.admin.services.dashboard_service.AuditRepository')
    @patch('app.admin.services.dashboard_service.UserRepository')
    def test_get_user_management_dashboard(self, mock_user_repo, mock_audit_repo, mock_metrics_repo):
        """Test user management dashboard data"""
        # Setup mocks
        mock_user_instance = MagicMock()
        mock_user_repo.return_value = mock_user_instance

        # Mock user statistics
        mock_user_instance.count_by_status.return_value = {
            'active': 1250,
            'inactive': 150,
            'suspended': 25,
            'pending': 75
        }
        mock_user_instance.get_registration_trends.return_value = [
            {'date': '2024-01-15', 'count': 45},
            {'date': '2024-01-16', 'count': 52},
            {'date': '2024-01-17', 'count': 38}
        ]

        service = DashboardService()

        success, message, data = service.get_user_management_dashboard()

        assert success
        assert message == "USER_DASHBOARD_SUCCESS"
        assert data is not None
        assert "user_counts" in data
        assert "registration_trends" in data
        assert "activity_metrics" in data

    @patch('app.admin.services.dashboard_service.MetricsRepository')
    def test_get_financial_dashboard(self, mock_metrics_repo):
        """Test financial dashboard data retrieval"""
        # Setup mocks
        mock_metrics_instance = MagicMock()
        mock_metrics_repo.return_value = mock_metrics_instance

        # Mock financial metrics
        mock_financial_metric = SystemMetric(
            metric_type=MetricType.FINANCIAL.value,
            data={
                'total_donations': 25000.50,
                'avg_donation': 15.75,
                'transaction_volume': 1580,
                'conversion_rate': 3.2
            },
            timestamp=datetime.now(timezone.utc)
        )
        mock_metrics_instance.get_latest_by_type.return_value = mock_financial_metric

        service = DashboardService()

        success, message, data = service.get_financial_dashboard()

        assert success
        assert message == "FINANCIAL_DASHBOARD_SUCCESS"
        assert data is not None
        assert "donation_stats" in data
        assert "revenue_trends" in data
        assert "transaction_metrics" in data

    @patch('app.admin.services.dashboard_service.MetricsRepository')
    def test_get_performance_monitoring_dashboard(self, mock_metrics_repo):
        """Test performance monitoring dashboard"""
        # Setup mocks
        mock_metrics_instance = MagicMock()
        mock_metrics_repo.return_value = mock_metrics_instance

        # Mock performance history
        performance_history = [
            SystemMetric.create_performance_metric(75.0, 68.0, 95.0, 0.05, 150),
            SystemMetric.create_performance_metric(78.0, 70.0, 98.0, 0.06, 155),
            SystemMetric.create_performance_metric(72.0, 65.0, 92.0, 0.04, 145)
        ]
        mock_metrics_instance.get_metrics_in_range.return_value = performance_history

        service = DashboardService()

        success, message, data = service.get_monitoring_dashboard()

        assert success
        assert message == "MONITORING_DASHBOARD_SUCCESS"
        assert data is not None
        assert "performance_history" in data
        assert "alert_summary" in data
        assert "system_health" in data

    @patch('app.admin.services.dashboard_service.MetricsRepository')
    @patch('app.admin.services.dashboard_service.AuditRepository')
    def test_get_security_dashboard(self, mock_audit_repo, mock_metrics_repo):
        """Test security dashboard data"""
        # Setup mocks
        mock_audit_instance = MagicMock()
        mock_audit_repo.return_value = mock_audit_instance

        # Mock security events
        security_events = [
            AdminAction.create_security_action("admin1", "failed_login_attempt", "192.168.1.100"),
            AdminAction.create_security_action("admin2", "suspicious_activity", "10.0.0.50")
        ]
        mock_audit_instance.get_security_events.return_value = security_events

        service = DashboardService()

        success, message, data = service.get_security_dashboard()

        assert success
        assert message == "SECURITY_DASHBOARD_SUCCESS"
        assert data is not None
        assert "security_events" in data
        assert "threat_analysis" in data
        assert "access_patterns" in data

    @patch('app.admin.services.dashboard_service.MetricsRepository')
    def test_dashboard_data_aggregation(self, mock_metrics_repo):
        """Test dashboard data aggregation functionality"""
        # Setup mocks
        mock_metrics_instance = MagicMock()
        mock_metrics_repo.return_value = mock_metrics_instance

        # Mock metrics for aggregation
        hourly_metrics = []
        for i in range(24):
            metric = SystemMetric.create_performance_metric(
                cpu_usage=70.0 + i * 2,
                memory_usage=60.0 + i * 1.5,
                response_time_avg=90.0 + i * 3,
                error_rate=0.05,
                active_sessions=100 + i * 5
            )
            metric.timestamp = datetime.now(timezone.utc) - timedelta(hours=i)
            hourly_metrics.append(metric)

        mock_metrics_instance.get_metrics_in_range.return_value = hourly_metrics

        service = DashboardService()

        # Test hourly aggregation
        aggregated_data = service._aggregate_metrics_by_hour(hourly_metrics)
        assert len(aggregated_data) <= 24
        assert all('timestamp' in item for item in aggregated_data)
        assert all('avg_cpu' in item for item in aggregated_data)

    def test_dashboard_alert_detection(self):
        """Test alert detection in dashboard data"""
        service = DashboardService()

        # Create metrics with alert conditions
        high_cpu_metric = SystemMetric.create_performance_metric(
            cpu_usage=95.0,  # High CPU
            memory_usage=60.0,
            response_time_avg=120.0,
            error_rate=0.05,
            active_sessions=100
        )

        high_error_metric = SystemMetric.create_performance_metric(
            cpu_usage=70.0,
            memory_usage=60.0,
            response_time_avg=120.0,
            error_rate=1.5,  # High error rate
            active_sessions=100
        )

        # Test alert detection
        alerts = service._detect_alerts([high_cpu_metric, high_error_metric])
        assert len(alerts) >= 2  # Should detect CPU and error rate alerts

        # Test alert categorization
        critical_alerts = [alert for alert in alerts if alert['severity'] == 'critical']
        warning_alerts = [alert for alert in alerts if alert['severity'] == 'warning']

        assert len(critical_alerts) > 0 or len(warning_alerts) > 0

    @patch('app.admin.services.dashboard_service.MetricsRepository')
    def test_dashboard_time_range_filtering(self, mock_metrics_repo):
        """Test dashboard data filtering by time range"""
        # Setup mocks
        mock_metrics_instance = MagicMock()
        mock_metrics_repo.return_value = mock_metrics_instance

        service = DashboardService()

        # Test different time ranges
        time_ranges = ['1h', '24h', '7d', '30d']

        for time_range in time_ranges:
            success, message, data = service.get_dashboard_data_for_range(time_range)

            # Should handle all time ranges
            assert success or message == "INVALID_TIME_RANGE"

    def test_dashboard_data_caching(self):
        """Test dashboard data caching functionality"""
        service = DashboardService()

        # Test cache key generation
        cache_key = service._generate_cache_key("overview", {"time_range": "24h"})
        assert cache_key is not None
        assert isinstance(cache_key, str)

        # Test cache expiration
        assert service.cache_ttl > 0  # Should have positive cache TTL

    @patch('app.admin.services.dashboard_service.MetricsRepository')
    def test_dashboard_export_functionality(self, mock_metrics_repo):
        """Test dashboard data export"""
        # Setup mocks
        mock_metrics_instance = MagicMock()
        mock_metrics_repo.return_value = mock_metrics_instance

        service = DashboardService()

        # Test CSV export
        export_data = {
            'metrics': [{'timestamp': '2024-01-15T10:00:00Z', 'cpu_usage': 75.0}],
            'summary': {'avg_cpu': 75.0, 'max_memory': 80.0}
        }

        csv_content = service.export_to_csv(export_data)
        assert csv_content is not None
        assert 'timestamp' in csv_content
        assert 'cpu_usage' in csv_content

        # Test JSON export
        json_content = service.export_to_json(export_data)
        assert json_content is not None
        assert '"metrics"' in json_content


class TestMonitoringService:
    """Test monitoring service functionality"""

    @patch('app.admin.services.monitoring_service.MetricsRepository')
    def test_monitoring_service_initialization(self, mock_metrics_repo):
        """Test monitoring service initialization"""
        service = MonitoringService()
        assert service.metrics_repository is not None

    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('app.admin.services.monitoring_service.MetricsRepository')
    def test_collect_system_metrics(self, mock_metrics_repo, mock_memory, mock_cpu):
        """Test system metrics collection"""
        # Setup mocks
        mock_cpu.return_value = 75.5
        mock_memory.return_value = MagicMock(percent=68.2)

        mock_metrics_instance = MagicMock()
        mock_metrics_repo.return_value = mock_metrics_instance

        service = MonitoringService()

        # Collect metrics
        success, message, metric = service.collect_system_metrics()

        assert success
        assert message == "METRICS_COLLECTED_SUCCESS"
        assert metric is not None
        assert metric.get_value('cpu_usage') == 75.5
        assert metric.get_value('memory_usage') == 68.2

    @patch('app.admin.services.monitoring_service.MetricsRepository')
    def test_alert_threshold_detection(self, mock_metrics_repo):
        """Test alert threshold detection"""
        service = MonitoringService()

        # Test CPU threshold
        high_cpu_metric = SystemMetric.create_performance_metric(
            cpu_usage=95.0,  # Above threshold
            memory_usage=60.0,
            response_time_avg=100.0,
            error_rate=0.05,
            active_sessions=100
        )

        alerts = service.check_alert_thresholds(high_cpu_metric)
        assert len(alerts) > 0
        assert any('CPU' in alert['message'] for alert in alerts)

    @patch('app.admin.services.monitoring_service.MetricsRepository')
    def test_performance_trend_analysis(self, mock_metrics_repo):
        """Test performance trend analysis"""
        # Setup mocks
        mock_metrics_instance = MagicMock()
        mock_metrics_repo.return_value = mock_metrics_instance

        # Create trending data (increasing CPU usage)
        trending_metrics = []
        for i in range(10):
            metric = SystemMetric.create_performance_metric(
                cpu_usage=50.0 + i * 5,  # Increasing trend
                memory_usage=60.0,
                response_time_avg=100.0,
                error_rate=0.05,
                active_sessions=100
            )
            trending_metrics.append(metric)

        mock_metrics_instance.get_recent_metrics.return_value = trending_metrics

        service = MonitoringService()

        trend_analysis = service.analyze_performance_trends()
        assert trend_analysis is not None
        assert 'cpu_trend' in trend_analysis
        assert trend_analysis['cpu_trend'] == 'increasing'

    @patch('app.admin.services.monitoring_service.MetricsRepository')
    def test_system_health_scoring(self, mock_metrics_repo):
        """Test system health scoring"""
        service = MonitoringService()

        # Test good health metrics
        good_metric = SystemMetric.create_performance_metric(
            cpu_usage=50.0,  # Good
            memory_usage=60.0,  # Good
            response_time_avg=80.0,  # Good
            error_rate=0.01,  # Very good
            active_sessions=100
        )

        health_score = service.calculate_health_score(good_metric)
        assert health_score >= 80  # Should be high score

        # Test poor health metrics
        poor_metric = SystemMetric.create_performance_metric(
            cpu_usage=95.0,  # Poor
            memory_usage=90.0,  # Poor
            response_time_avg=200.0,  # Poor
            error_rate=2.0,  # Very poor
            active_sessions=100
        )

        health_score = service.calculate_health_score(poor_metric)
        assert health_score <= 50  # Should be low score

    @patch('app.admin.services.monitoring_service.MetricsRepository')
    def test_predictive_alerts(self, mock_metrics_repo):
        """Test predictive alert generation"""
        # Setup mocks with trending data
        mock_metrics_instance = MagicMock()
        mock_metrics_repo.return_value = mock_metrics_instance

        # Create data showing increasing resource usage
        historical_metrics = []
        for i in range(20):
            metric = SystemMetric.create_performance_metric(
                cpu_usage=30.0 + i * 3,  # Gradually increasing
                memory_usage=40.0 + i * 2,
                response_time_avg=80.0 + i * 4,
                error_rate=0.01,
                active_sessions=100
            )
            metric.timestamp = datetime.now(timezone.utc) - timedelta(minutes=i*5)
            historical_metrics.append(metric)

        mock_metrics_instance.get_metrics_in_range.return_value = historical_metrics

        service = MonitoringService()

        predictive_alerts = service.generate_predictive_alerts()
        assert isinstance(predictive_alerts, list)

        # Should predict potential issues based on trends
        if len(predictive_alerts) > 0:
            assert all('predicted_time' in alert for alert in predictive_alerts)
            assert all('metric' in alert for alert in predictive_alerts)


if __name__ == '__main__':
    pytest.main([__file__])