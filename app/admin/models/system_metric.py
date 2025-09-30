from datetime import datetime, timezone
from bson import ObjectId
from typing import Dict, Any, Optional
from enum import Enum

class MetricType(Enum):
    PERFORMANCE = "performance"
    USER_ACTIVITY = "user_activity"
    FINANCIAL = "financial"
    SECURITY = "security"
    INFRASTRUCTURE = "infrastructure"
    BUSINESS = "business"

class MetricPeriod(Enum):
    REAL_TIME = "realtime"
    ONE_MINUTE = "1m"
    FIVE_MINUTES = "5m"
    FIFTEEN_MINUTES = "15m"
    ONE_HOUR = "1h"
    ONE_DAY = "1d"
    ONE_WEEK = "1w"
    ONE_MONTH = "1M"

class SystemMetric:
    def __init__(self, metric_type: str, data: Dict[str, Any],
                 period: str = MetricPeriod.ONE_MINUTE.value,
                 timestamp: datetime = None, tags: Dict[str, str] = None,
                 source: str = None, _id: str = None):

        self._id = _id
        self.metric_type = metric_type
        self.data = data or {}
        self.period = period
        self.timestamp = timestamp or datetime.now(timezone.utc)
        self.tags = tags or {}
        self.source = source or "system"

    def add_tag(self, key: str, value: str):
        """Add a tag to the metric for filtering"""
        self.tags[key] = value

    def get_tag(self, key: str) -> Optional[str]:
        """Get a tag value"""
        return self.tags.get(key)

    def update_data(self, new_data: Dict[str, Any]):
        """Update metric data"""
        self.data.update(new_data)

    def get_value(self, key: str, default: Any = None) -> Any:
        """Get a specific data value"""
        return self.data.get(key, default)

    def set_value(self, key: str, value: Any):
        """Set a specific data value"""
        self.data[key] = value

    @staticmethod
    def create_performance_metric(cpu_usage: float, memory_usage: float,
                                 response_time_avg: float, error_rate: float,
                                 active_sessions: int, period: str = MetricPeriod.ONE_MINUTE.value) -> 'SystemMetric':
        """Create a performance metric"""
        data = {
            'cpu_usage': cpu_usage,
            'memory_usage': memory_usage,
            'response_time_avg': response_time_avg,
            'error_rate': error_rate,
            'active_sessions': active_sessions,
            'disk_usage': 0.0,  # Can be added later
            'network_io': 0.0,  # Can be added later
            'database_connections': 0   # Can be added later
        }

        return SystemMetric(
            metric_type=MetricType.PERFORMANCE.value,
            data=data,
            period=period,
            tags={'component': 'api_server'}
        )

    @staticmethod
    def create_user_activity_metric(active_users: int, new_registrations: int,
                                   total_sessions: int, page_views: int,
                                   period: str = MetricPeriod.ONE_HOUR.value) -> 'SystemMetric':
        """Create a user activity metric"""
        data = {
            'active_users': active_users,
            'new_registrations': new_registrations,
            'total_sessions': total_sessions,
            'page_views': page_views,
            'bounce_rate': 0.0,  # Can be calculated
            'session_duration_avg': 0.0,  # Can be calculated
            'retention_rate': 0.0  # Can be calculated
        }

        return SystemMetric(
            metric_type=MetricType.USER_ACTIVITY.value,
            data=data,
            period=period,
            tags={'source': 'user_tracking'}
        )

    @staticmethod
    def create_financial_metric(donations_per_hour: float, total_donations: float,
                               processing_fees: float, platform_revenue: float,
                               period: str = MetricPeriod.ONE_HOUR.value) -> 'SystemMetric':
        """Create a financial metric"""
        data = {
            'donations_per_hour': donations_per_hour,
            'total_donations': total_donations,
            'processing_fees': processing_fees,
            'platform_revenue': platform_revenue,
            'average_donation': 0.0,  # Can be calculated
            'conversion_rate': 0.0,  # Can be calculated
            'refund_rate': 0.0  # Can be calculated
        }

        return SystemMetric(
            metric_type=MetricType.FINANCIAL.value,
            data=data,
            period=period,
            tags={'currency': 'EUR'}
        )

    @staticmethod
    def create_security_metric(failed_logins: int, suspicious_activities: int,
                              blocked_ips: int, fraud_attempts: int,
                              period: str = MetricPeriod.FIFTEEN_MINUTES.value) -> 'SystemMetric':
        """Create a security metric"""
        data = {
            'failed_logins': failed_logins,
            'suspicious_activities': suspicious_activities,
            'blocked_ips': blocked_ips,
            'fraud_attempts': fraud_attempts,
            'ddos_attempts': 0,  # Can be added
            'malware_detected': 0,  # Can be added
            'security_alerts': 0   # Can be added
        }

        return SystemMetric(
            metric_type=MetricType.SECURITY.value,
            data=data,
            period=period,
            tags={'severity': 'medium'}
        )

    @staticmethod
    def create_infrastructure_metric(server_uptime: float, database_response_time: float,
                                   cdn_hit_rate: float, backup_status: str,
                                   period: str = MetricPeriod.FIVE_MINUTES.value) -> 'SystemMetric':
        """Create an infrastructure metric"""
        data = {
            'server_uptime': server_uptime,
            'database_response_time': database_response_time,
            'cdn_hit_rate': cdn_hit_rate,
            'backup_status': backup_status,
            'storage_usage': 0.0,  # Can be added
            'bandwidth_usage': 0.0,  # Can be added
            'api_rate_limit_hits': 0   # Can be added
        }

        return SystemMetric(
            metric_type=MetricType.INFRASTRUCTURE.value,
            data=data,
            period=period,
            tags={'environment': 'production'}
        )

    @staticmethod
    def create_business_metric(dau: int, mau: int, retention_rate: float,
                              ltv: float, churn_rate: float,
                              period: str = MetricPeriod.ONE_DAY.value) -> 'SystemMetric':
        """Create a business metric"""
        data = {
            'dau': dau,  # Daily Active Users
            'mau': mau,  # Monthly Active Users
            'retention_rate': retention_rate,
            'ltv': ltv,  # Lifetime Value
            'churn_rate': churn_rate,
            'arpu': 0.0,  # Average Revenue Per User
            'cac': 0.0,   # Customer Acquisition Cost
            'engagement_score': 0.0  # User Engagement Score
        }

        return SystemMetric(
            metric_type=MetricType.BUSINESS.value,
            data=data,
            period=period,
            tags={'cohort': 'monthly'}
        )

    def is_alert_worthy(self) -> bool:
        """Check if this metric should trigger an alert"""
        alert_thresholds = {
            MetricType.PERFORMANCE.value: {
                'cpu_usage': 80.0,
                'memory_usage': 85.0,
                'response_time_avg': 1000.0,  # 1 second
                'error_rate': 5.0  # 5%
            },
            MetricType.SECURITY.value: {
                'failed_logins': 100,
                'suspicious_activities': 10,
                'fraud_attempts': 5
            },
            MetricType.FINANCIAL.value: {
                'refund_rate': 10.0,  # 10%
                'processing_fees': 5.0  # 5% of revenue
            }
        }

        thresholds = alert_thresholds.get(self.metric_type, {})
        for key, threshold in thresholds.items():
            value = self.get_value(key)
            if value is not None and value > threshold:
                return True

        return False

    def get_alert_message(self) -> Optional[str]:
        """Get alert message if metric is alert-worthy"""
        if not self.is_alert_worthy():
            return None

        if self.metric_type == MetricType.PERFORMANCE.value:
            if self.get_value('cpu_usage', 0) > 80:
                return f"High CPU usage: {self.get_value('cpu_usage')}%"
            elif self.get_value('memory_usage', 0) > 85:
                return f"High memory usage: {self.get_value('memory_usage')}%"
            elif self.get_value('response_time_avg', 0) > 1000:
                return f"High response time: {self.get_value('response_time_avg')}ms"
            elif self.get_value('error_rate', 0) > 5:
                return f"High error rate: {self.get_value('error_rate')}%"

        elif self.metric_type == MetricType.SECURITY.value:
            if self.get_value('failed_logins', 0) > 100:
                return f"High failed login attempts: {self.get_value('failed_logins')}"
            elif self.get_value('fraud_attempts', 0) > 5:
                return f"Fraud attempts detected: {self.get_value('fraud_attempts')}"

        return f"Alert threshold exceeded for {self.metric_type}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            '_id': str(self._id) if self._id else None,
            'metric_type': self.metric_type,
            'data': self.data,
            'period': self.period,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'tags': self.tags,
            'source': self.source
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SystemMetric':
        """Create SystemMetric instance from dictionary"""
        timestamp = None
        if data.get('timestamp'):
            if isinstance(data['timestamp'], str):
                timestamp = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
            else:
                timestamp = data['timestamp']

        return cls(
            _id=str(data['_id']) if data.get('_id') else None,
            metric_type=data['metric_type'],
            data=data.get('data', {}),
            period=data.get('period', MetricPeriod.ONE_MINUTE.value),
            timestamp=timestamp,
            tags=data.get('tags', {}),
            source=data.get('source', 'system')
        )

    def __repr__(self):
        return f"<SystemMetric {self.metric_type} {self.period} at {self.timestamp}>"