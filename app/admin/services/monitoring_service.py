from typing import Optional, Dict, Tuple, List, Any
from flask import current_app
from datetime import datetime, timezone, timedelta
import psutil
import os
import time

from app.admin.models.system_metric import SystemMetric, MetricType, MetricPeriod
from app.admin.models.admin_action import AdminAction, ActionType
from app.admin.repositories.metrics_repository import MetricsRepository
from app.admin.repositories.audit_repository import AuditRepository
from app.admin.repositories.admin_repository import AdminRepository

class MonitoringService:
    def __init__(self):
        self.metrics_repository = MetricsRepository()
        self.audit_repository = AuditRepository()
        self.admin_repository = AdminRepository()

    def collect_system_metrics(self) -> Tuple[bool, str, Optional[Dict]]:
        """Collect and store current system metrics"""
        try:
            # Collect performance metrics
            performance_metric = self._collect_performance_metrics()
            if performance_metric:
                self.metrics_repository.create_metric(performance_metric)

            # Collect infrastructure metrics
            infrastructure_metric = self._collect_infrastructure_metrics()
            if infrastructure_metric:
                self.metrics_repository.create_metric(infrastructure_metric)

            # Collect security metrics
            security_metric = self._collect_security_metrics()
            if security_metric:
                self.metrics_repository.create_metric(security_metric)

            current_app.logger.info("System metrics collected successfully")

            return True, "METRICS_COLLECTED_SUCCESS", {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "metrics_collected": ["performance", "infrastructure", "security"]
            }

        except Exception as e:
            current_app.logger.error(f"Metrics collection error: {str(e)}")
            return False, "METRICS_COLLECTION_FAILED", None

    def get_real_time_metrics(self) -> Tuple[bool, str, Optional[Dict]]:
        """Get real-time system metrics"""
        try:
            # Get current performance data
            performance_data = self._get_current_performance()

            # Get latest stored metrics
            latest_performance = self.metrics_repository.find_latest_metric(MetricType.PERFORMANCE.value)
            latest_security = self.metrics_repository.find_latest_metric(MetricType.SECURITY.value)

            # Check for alerts
            alert_metrics = self.metrics_repository.find_alert_worthy_metrics(hours=1)

            real_time_data = {
                "current_performance": performance_data,
                "latest_metrics": {
                    "performance": latest_performance.data if latest_performance else {},
                    "security": latest_security.data if latest_security else {}
                },
                "alerts": [
                    {
                        "type": metric.metric_type,
                        "message": metric.get_alert_message(),
                        "timestamp": metric.timestamp.isoformat(),
                        "severity": "high" if metric.get_value('cpu_usage', 0) > 90 else "medium"
                    }
                    for metric in alert_metrics
                ],
                "system_status": self._get_system_status(),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

            return True, "REAL_TIME_METRICS_SUCCESS", real_time_data

        except Exception as e:
            current_app.logger.error(f"Real-time metrics error: {str(e)}")
            return False, "INTERNAL_SERVER_ERROR", None

    def get_performance_analytics(self, hours: int = 24) -> Tuple[bool, str, Optional[Dict]]:
        """Get performance analytics for the specified time period"""
        try:
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(hours=hours)

            # Get performance metrics
            performance_metrics = self.metrics_repository.find_metrics_by_type(
                MetricType.PERFORMANCE.value, start_time=start_time, end_time=end_time
            )

            if not performance_metrics:
                return True, "NO_PERFORMANCE_DATA", {"message": "No performance data available"}

            # Calculate statistics for key metrics
            cpu_stats = self.metrics_repository.get_metric_statistics(
                MetricType.PERFORMANCE.value, "cpu_usage", start_time, end_time
            )
            memory_stats = self.metrics_repository.get_metric_statistics(
                MetricType.PERFORMANCE.value, "memory_usage", start_time, end_time
            )
            response_time_stats = self.metrics_repository.get_metric_statistics(
                MetricType.PERFORMANCE.value, "response_time_avg", start_time, end_time
            )

            # Get time series data for charts
            cpu_timeline = self.metrics_repository.get_time_series_data(
                MetricType.PERFORMANCE.value, "cpu_usage", start_time, end_time, "1h"
            )
            memory_timeline = self.metrics_repository.get_time_series_data(
                MetricType.PERFORMANCE.value, "memory_usage", start_time, end_time, "1h"
            )
            response_time_timeline = self.metrics_repository.get_time_series_data(
                MetricType.PERFORMANCE.value, "response_time_avg", start_time, end_time, "1h"
            )

            analytics_data = {
                "time_period": f"{hours} hours",
                "statistics": {
                    "cpu_usage": cpu_stats,
                    "memory_usage": memory_stats,
                    "response_time": response_time_stats
                },
                "timelines": {
                    "cpu_usage": cpu_timeline,
                    "memory_usage": memory_timeline,
                    "response_time": response_time_timeline
                },
                "performance_score": self._calculate_performance_score(cpu_stats, memory_stats, response_time_stats),
                "recommendations": self._generate_performance_recommendations(cpu_stats, memory_stats, response_time_stats)
            }

            return True, "PERFORMANCE_ANALYTICS_SUCCESS", analytics_data

        except Exception as e:
            current_app.logger.error(f"Performance analytics error: {str(e)}")
            return False, "INTERNAL_SERVER_ERROR", None

    def get_security_monitoring(self, hours: int = 24) -> Tuple[bool, str, Optional[Dict]]:
        """Get security monitoring data"""
        try:
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(hours=hours)

            # Get security metrics
            security_metrics = self.metrics_repository.find_metrics_by_type(
                MetricType.SECURITY.value, start_time=start_time, end_time=end_time
            )

            # Get failed admin actions
            failed_actions = self.audit_repository.find_failed_actions(hours=hours, limit=50)

            # Get suspicious activity
            suspicious_activity = self.audit_repository.find_suspicious_activity(hours=hours)

            # Get sensitive actions
            sensitive_actions = self.audit_repository.find_sensitive_actions(hours=hours, limit=20)

            # Calculate security scores
            security_score = self._calculate_security_score(failed_actions, suspicious_activity)

            security_data = {
                "time_period": f"{hours} hours",
                "security_score": security_score,
                "failed_actions": [
                    {
                        "action_type": action.action_type,
                        "admin_id": action.admin_id,
                        "timestamp": action.timestamp.isoformat(),
                        "ip_address": action.ip_address,
                        "error": action.result.get('error_message', 'Unknown error')
                    }
                    for action in failed_actions
                ],
                "suspicious_activity": suspicious_activity,
                "sensitive_actions": [
                    {
                        "action_type": action.action_type,
                        "admin_id": action.admin_id,
                        "target_type": action.target_type,
                        "timestamp": action.timestamp.isoformat(),
                        "risk_level": action.get_risk_level()
                    }
                    for action in sensitive_actions
                ],
                "security_metrics": [metric.data for metric in security_metrics[-10:]],  # Last 10 metrics
                "threat_assessment": self._assess_security_threats(failed_actions, suspicious_activity),
                "recommendations": self._generate_security_recommendations(failed_actions, suspicious_activity)
            }

            return True, "SECURITY_MONITORING_SUCCESS", security_data

        except Exception as e:
            current_app.logger.error(f"Security monitoring error: {str(e)}")
            return False, "INTERNAL_SERVER_ERROR", None

    def get_system_alerts(self, severity: str = None, limit: int = 50) -> Tuple[bool, str, Optional[Dict]]:
        """Get system alerts with optional severity filtering"""
        try:
            # Get alert-worthy metrics
            alert_metrics = self.metrics_repository.find_alert_worthy_metrics(hours=24)

            # Get recent failed actions
            failed_actions = self.audit_repository.find_failed_actions(hours=24, limit=20)

            # Get suspicious activity
            suspicious_activity = self.audit_repository.find_suspicious_activity(hours=24)

            alerts = []

            # Process metric alerts
            for metric in alert_metrics:
                alert_severity = self._determine_alert_severity(metric)
                if severity is None or alert_severity == severity:
                    alerts.append({
                        "id": str(metric._id) if metric._id else None,
                        "type": "system_metric",
                        "severity": alert_severity,
                        "title": f"{metric.metric_type.title()} Alert",
                        "message": metric.get_alert_message(),
                        "timestamp": metric.timestamp.isoformat(),
                        "data": metric.data,
                        "source": "metrics"
                    })

            # Process security alerts
            for action in failed_actions:
                if severity is None or severity == "medium":
                    alerts.append({
                        "id": str(action._id) if action._id else None,
                        "type": "security",
                        "severity": "medium",
                        "title": "Failed Admin Action",
                        "message": f"Failed {action.action_type} by admin {action.admin_id}",
                        "timestamp": action.timestamp.isoformat(),
                        "data": {
                            "admin_id": action.admin_id,
                            "action_type": action.action_type,
                            "ip_address": action.ip_address
                        },
                        "source": "audit"
                    })

            # Process suspicious activity alerts
            for activity in suspicious_activity:
                alert_severity = activity.get('severity', 'low')
                if severity is None or alert_severity == severity:
                    alerts.append({
                        "id": f"suspicious_{activity['type']}_{int(time.time())}",
                        "type": "security",
                        "severity": alert_severity,
                        "title": "Suspicious Activity Detected",
                        "message": f"{activity['type']}: {activity.get('count', 0)} occurrences",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "data": activity,
                        "source": "security_analysis"
                    })

            # Sort by timestamp (newest first) and apply limit
            alerts.sort(key=lambda x: x['timestamp'], reverse=True)
            alerts = alerts[:limit]

            return True, "SYSTEM_ALERTS_SUCCESS", {
                "alerts": alerts,
                "total_count": len(alerts),
                "severity_filter": severity,
                "severity_distribution": self._get_alert_severity_distribution(alerts)
            }

        except Exception as e:
            current_app.logger.error(f"System alerts error: {str(e)}")
            return False, "INTERNAL_SERVER_ERROR", None

    def acknowledge_alert(self, alert_id: str, admin_id: str, notes: str = None,
                         ip_address: str = None) -> Tuple[bool, str, Optional[Dict]]:
        """Acknowledge a system alert"""
        try:
            # Log the acknowledgment action
            action = AdminAction(
                admin_id=admin_id,
                action_type=ActionType.ALERT_ACKNOWLEDGE.value,
                target_type="alert",
                target_id=alert_id,
                reason=notes or "Alert acknowledged",
                ip_address=ip_address
            )
            action.mark_success()
            self.audit_repository.create_action(action)

            current_app.logger.info(f"Alert {alert_id} acknowledged by admin {admin_id}")

            return True, "ALERT_ACKNOWLEDGED_SUCCESS", {
                "alert_id": alert_id,
                "acknowledged_by": admin_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            current_app.logger.error(f"Alert acknowledgment error: {str(e)}")
            return False, "INTERNAL_SERVER_ERROR", None

    def _collect_performance_metrics(self) -> Optional[SystemMetric]:
        """Collect current performance metrics"""
        try:
            # Get CPU usage
            cpu_usage = psutil.cpu_percent(interval=1)

            # Get memory usage
            memory = psutil.virtual_memory()
            memory_usage = memory.percent

            # Get active sessions (mock data for now)
            active_sessions = 100  # This would come from session tracking

            # Mock response time (would come from application metrics)
            response_time_avg = 150.0

            # Mock error rate (would come from application logs)
            error_rate = 0.5

            return SystemMetric.create_performance_metric(
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                response_time_avg=response_time_avg,
                error_rate=error_rate,
                active_sessions=active_sessions
            )

        except Exception as e:
            current_app.logger.error(f"Performance metrics collection error: {str(e)}")
            return None

    def _collect_infrastructure_metrics(self) -> Optional[SystemMetric]:
        """Collect infrastructure metrics"""
        try:
            # Get disk usage
            disk = psutil.disk_usage('/')
            disk_usage = (disk.used / disk.total) * 100

            # Mock database response time
            database_response_time = 25.0

            # Mock CDN hit rate
            cdn_hit_rate = 95.0

            # Mock backup status
            backup_status = "completed"

            # Mock server uptime (would get from system)
            server_uptime = 99.9

            return SystemMetric.create_infrastructure_metric(
                server_uptime=server_uptime,
                database_response_time=database_response_time,
                cdn_hit_rate=cdn_hit_rate,
                backup_status=backup_status
            )

        except Exception as e:
            current_app.logger.error(f"Infrastructure metrics collection error: {str(e)}")
            return None

    def _collect_security_metrics(self) -> Optional[SystemMetric]:
        """Collect security metrics"""
        try:
            # Count failed logins in the last 15 minutes
            fifteen_min_ago = datetime.now(timezone.utc) - timedelta(minutes=15)
            failed_logins = len(self.audit_repository.find_failed_actions(hours=0.25))

            # Count suspicious activities
            suspicious_activities = len(self.audit_repository.find_suspicious_activity(hours=1))

            # Mock data for other security metrics
            blocked_ips = 0
            fraud_attempts = 0

            return SystemMetric.create_security_metric(
                failed_logins=failed_logins,
                suspicious_activities=suspicious_activities,
                blocked_ips=blocked_ips,
                fraud_attempts=fraud_attempts
            )

        except Exception as e:
            current_app.logger.error(f"Security metrics collection error: {str(e)}")
            return None

    def _get_current_performance(self) -> Dict[str, Any]:
        """Get current performance data"""
        try:
            return {
                "cpu_usage": psutil.cpu_percent(),
                "memory_usage": psutil.virtual_memory().percent,
                "disk_usage": (psutil.disk_usage('/').used / psutil.disk_usage('/').total) * 100,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except:
            return {}

    def _get_system_status(self) -> str:
        """Determine overall system status"""
        try:
            cpu_usage = psutil.cpu_percent()
            memory_usage = psutil.virtual_memory().percent

            if cpu_usage > 90 or memory_usage > 95:
                return "critical"
            elif cpu_usage > 80 or memory_usage > 85:
                return "warning"
            else:
                return "healthy"
        except:
            return "unknown"

    def _calculate_performance_score(self, cpu_stats: Dict, memory_stats: Dict,
                                   response_time_stats: Dict) -> int:
        """Calculate overall performance score (0-100)"""
        try:
            score = 100

            # Deduct points for high CPU usage
            if cpu_stats.get('avg', 0) > 80:
                score -= 20
            elif cpu_stats.get('avg', 0) > 60:
                score -= 10

            # Deduct points for high memory usage
            if memory_stats.get('avg', 0) > 85:
                score -= 20
            elif memory_stats.get('avg', 0) > 70:
                score -= 10

            # Deduct points for high response time
            if response_time_stats.get('avg', 0) > 1000:
                score -= 30
            elif response_time_stats.get('avg', 0) > 500:
                score -= 15

            return max(0, score)

        except:
            return 50  # Default score if calculation fails

    def _calculate_security_score(self, failed_actions: List, suspicious_activity: List) -> int:
        """Calculate security score (0-100)"""
        try:
            score = 100

            # Deduct points for failed actions
            failed_count = len(failed_actions)
            if failed_count > 50:
                score -= 40
            elif failed_count > 20:
                score -= 20
            elif failed_count > 10:
                score -= 10

            # Deduct points for suspicious activity
            suspicious_count = len(suspicious_activity)
            if suspicious_count > 10:
                score -= 30
            elif suspicious_count > 5:
                score -= 15
            elif suspicious_count > 0:
                score -= 5

            return max(0, score)

        except:
            return 50

    def _determine_alert_severity(self, metric: SystemMetric) -> str:
        """Determine alert severity based on metric values"""
        if metric.metric_type == MetricType.PERFORMANCE.value:
            cpu_usage = metric.get_value('cpu_usage', 0)
            memory_usage = metric.get_value('memory_usage', 0)

            if cpu_usage > 95 or memory_usage > 98:
                return "critical"
            elif cpu_usage > 85 or memory_usage > 90:
                return "high"
            else:
                return "medium"

        return "medium"

    def _get_alert_severity_distribution(self, alerts: List[Dict]) -> Dict[str, int]:
        """Get distribution of alert severities"""
        distribution = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for alert in alerts:
            severity = alert.get('severity', 'low')
            distribution[severity] = distribution.get(severity, 0) + 1
        return distribution

    def _generate_performance_recommendations(self, cpu_stats: Dict, memory_stats: Dict,
                                            response_time_stats: Dict) -> List[str]:
        """Generate performance improvement recommendations"""
        recommendations = []

        if cpu_stats.get('avg', 0) > 80:
            recommendations.append("Consider scaling CPU resources or optimizing high-CPU processes")

        if memory_stats.get('avg', 0) > 85:
            recommendations.append("Monitor memory usage and consider increasing available RAM")

        if response_time_stats.get('avg', 0) > 500:
            recommendations.append("Investigate API performance bottlenecks and optimize slow endpoints")

        if not recommendations:
            recommendations.append("System performance is within normal parameters")

        return recommendations

    def _generate_security_recommendations(self, failed_actions: List, suspicious_activity: List) -> List[str]:
        """Generate security recommendations"""
        recommendations = []

        if len(failed_actions) > 20:
            recommendations.append("Review and investigate high number of failed admin actions")

        if len(suspicious_activity) > 5:
            recommendations.append("Enable additional security monitoring and consider IP restrictions")

        if not recommendations:
            recommendations.append("Security metrics are within acceptable ranges")

        return recommendations

    def _assess_security_threats(self, failed_actions: List, suspicious_activity: List) -> str:
        """Assess overall security threat level"""
        if len(failed_actions) > 50 or len(suspicious_activity) > 10:
            return "high"
        elif len(failed_actions) > 20 or len(suspicious_activity) > 5:
            return "medium"
        else:
            return "low"