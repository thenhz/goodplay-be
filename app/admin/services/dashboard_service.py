from typing import Optional, Dict, Tuple, List, Any
from flask import current_app
from datetime import datetime, timezone, timedelta

from app.admin.models.dashboard_config import DashboardConfig
from app.admin.models.admin_action import AdminAction, ActionType
from app.admin.repositories.admin_repository import AdminRepository
from app.admin.repositories.metrics_repository import MetricsRepository
from app.admin.repositories.audit_repository import AuditRepository

# Import other repositories for dashboard data
from app.core.repositories.user_repository import UserRepository
try:
    from app.donations.repositories.wallet_repository import WalletRepository
    from app.donations.repositories.transaction_repository import TransactionRepository
except ImportError:
    WalletRepository = None
    TransactionRepository = None

try:
    from app.onlus.repositories.onlus_repository import OnlusRepository
except ImportError:
    OnlusRepository = None

try:
    from app.games.repositories.game_repository import GameRepository
except ImportError:
    GameRepository = None

class DashboardService:
    def __init__(self):
        self.admin_repository = AdminRepository()
        self.metrics_repository = MetricsRepository()
        self.audit_repository = AuditRepository()

        # Core platform repositories
        self.user_repository = UserRepository()
        self.wallet_repository = WalletRepository() if WalletRepository else None
        self.transaction_repository = TransactionRepository() if TransactionRepository else None
        self.onlus_repository = OnlusRepository() if OnlusRepository else None
        self.game_repository = GameRepository() if GameRepository else None

    def get_dashboard_overview(self, admin_id: str) -> Tuple[bool, str, Optional[Dict]]:
        """Get comprehensive dashboard overview"""
        try:
            admin = self.admin_repository.find_admin_by_id(admin_id)
            if not admin:
                return False, "ADMIN_NOT_FOUND", None

            # Get current timestamp
            now = datetime.now(timezone.utc)
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            yesterday_start = today_start - timedelta(days=1)
            week_start = today_start - timedelta(days=7)
            month_start = today_start - timedelta(days=30)

            overview_data = {}

            # System health metrics
            if admin.has_permission('system_monitoring'):
                overview_data['system_health'] = self._get_system_health()

            # User metrics
            if admin.has_permission('user_management'):
                overview_data['user_metrics'] = self._get_user_metrics(today_start, yesterday_start)

            # Financial metrics
            if admin.has_permission('financial_oversight'):
                overview_data['financial_metrics'] = self._get_financial_metrics(today_start, month_start)

            # Content metrics
            if admin.has_permission('content_moderation'):
                overview_data['content_metrics'] = self._get_content_metrics(today_start, week_start)

            # Security alerts
            overview_data['security_alerts'] = self._get_security_alerts(admin_id)

            # Recent admin activity
            overview_data['recent_activity'] = self._get_recent_activity(admin_id, limit=10)

            return True, "DASHBOARD_OVERVIEW_SUCCESS", overview_data

        except Exception as e:
            current_app.logger.error(f"Dashboard overview error: {str(e)}")
            return False, "INTERNAL_SERVER_ERROR", None

    def get_user_management_data(self, admin_id: str, time_range: str = "7d") -> Tuple[bool, str, Optional[Dict]]:
        """Get user management dashboard data"""
        try:
            admin = self.admin_repository.find_admin_by_id(admin_id)
            if not admin or not admin.has_permission('user_management'):
                return False, "ACCESS_DENIED", None

            days = self._parse_time_range(time_range)
            start_time = datetime.now(timezone.utc) - timedelta(days=days)

            data = {
                'user_statistics': self._get_detailed_user_stats(start_time),
                'registration_trends': self._get_registration_trends(start_time, days),
                'user_activity_patterns': self._get_user_activity_patterns(start_time),
                'user_demographics': self._get_user_demographics(),
                'top_active_users': self._get_top_active_users(start_time),
                'user_support_metrics': self._get_user_support_metrics(start_time)
            }

            return True, "USER_MANAGEMENT_DATA_SUCCESS", data

        except Exception as e:
            current_app.logger.error(f"User management data error: {str(e)}")
            return False, "INTERNAL_SERVER_ERROR", None

    def get_financial_dashboard_data(self, admin_id: str, time_range: str = "30d") -> Tuple[bool, str, Optional[Dict]]:
        """Get financial dashboard data"""
        try:
            admin = self.admin_repository.find_admin_by_id(admin_id)
            if not admin or not admin.has_permission('financial_oversight'):
                return False, "ACCESS_DENIED", None

            days = self._parse_time_range(time_range)
            start_time = datetime.now(timezone.utc) - timedelta(days=days)

            data = {
                'financial_overview': self._get_financial_overview(start_time),
                'donation_trends': self._get_donation_trends(start_time, days),
                'onlus_allocation': self._get_onlus_allocation_data(start_time),
                'revenue_breakdown': self._get_revenue_breakdown(start_time),
                'transaction_analysis': self._get_transaction_analysis(start_time),
                'fee_analysis': self._get_fee_analysis(start_time)
            }

            return True, "FINANCIAL_DASHBOARD_SUCCESS", data

        except Exception as e:
            current_app.logger.error(f"Financial dashboard error: {str(e)}")
            return False, "INTERNAL_SERVER_ERROR", None

    def get_system_monitoring_data(self, admin_id: str) -> Tuple[bool, str, Optional[Dict]]:
        """Get system monitoring dashboard data"""
        try:
            admin = self.admin_repository.find_admin_by_id(admin_id)
            if not admin or not admin.has_permission('system_monitoring'):
                return False, "ACCESS_DENIED", None

            now = datetime.now(timezone.utc)
            hour_ago = now - timedelta(hours=1)
            day_ago = now - timedelta(days=1)

            data = {
                'current_metrics': self.metrics_repository.get_dashboard_metrics(),
                'performance_trends': self._get_performance_trends(day_ago),
                'infrastructure_status': self._get_infrastructure_status(),
                'api_metrics': self._get_api_metrics(hour_ago),
                'database_metrics': self._get_database_metrics(),
                'active_alerts': self._get_active_alerts(),
                'system_capacity': self._get_system_capacity_info()
            }

            return True, "SYSTEM_MONITORING_SUCCESS", data

        except Exception as e:
            current_app.logger.error(f"System monitoring error: {str(e)}")
            return False, "INTERNAL_SERVER_ERROR", None

    def get_content_moderation_data(self, admin_id: str, time_range: str = "7d") -> Tuple[bool, str, Optional[Dict]]:
        """Get content moderation dashboard data"""
        try:
            admin = self.admin_repository.find_admin_by_id(admin_id)
            if not admin or not admin.has_permission('content_moderation'):
                return False, "ACCESS_DENIED", None

            days = self._parse_time_range(time_range)
            start_time = datetime.now(timezone.utc) - timedelta(days=days)

            data = {
                'pending_reviews': self._get_pending_content_reviews(),
                'moderation_stats': self._get_moderation_statistics(start_time),
                'flagged_content': self._get_flagged_content(start_time),
                'game_submissions': self._get_game_submission_queue(),
                'onlus_verifications': self._get_onlus_verification_queue(),
                'community_reports': self._get_community_reports(start_time)
            }

            return True, "CONTENT_MODERATION_SUCCESS", data

        except Exception as e:
            current_app.logger.error(f"Content moderation error: {str(e)}")
            return False, "INTERNAL_SERVER_ERROR", None

    def get_analytics_data(self, admin_id: str, metric_type: str,
                          time_range: str = "30d") -> Tuple[bool, str, Optional[Dict]]:
        """Get analytics data for charts and reports"""
        try:
            admin = self.admin_repository.find_admin_by_id(admin_id)
            if not admin or not admin.has_permission('analytics_view'):
                return False, "ACCESS_DENIED", None

            days = self._parse_time_range(time_range)
            start_time = datetime.now(timezone.utc) - timedelta(days=days)
            end_time = datetime.now(timezone.utc)

            if metric_type == "user_activity":
                data = self.metrics_repository.get_time_series_data(
                    "user_activity", "active_users", start_time, end_time, "1d"
                )
            elif metric_type == "financial":
                data = self.metrics_repository.get_time_series_data(
                    "financial", "total_donations", start_time, end_time, "1d"
                )
            elif metric_type == "performance":
                data = self.metrics_repository.get_time_series_data(
                    "performance", "response_time_avg", start_time, end_time, "1h"
                )
            elif metric_type == "security":
                data = self.metrics_repository.get_time_series_data(
                    "security", "failed_logins", start_time, end_time, "1h"
                )
            else:
                return False, "INVALID_METRIC_TYPE", None

            return True, "ANALYTICS_DATA_SUCCESS", {
                "metric_type": metric_type,
                "time_range": time_range,
                "data": data
            }

        except Exception as e:
            current_app.logger.error(f"Analytics data error: {str(e)}")
            return False, "INTERNAL_SERVER_ERROR", None

    def _get_system_health(self) -> Dict[str, Any]:
        """Get current system health status"""
        try:
            latest_performance = self.metrics_repository.find_latest_metric("performance")
            latest_infrastructure = self.metrics_repository.find_latest_metric("infrastructure")

            health_status = "healthy"
            health_score = 100

            if latest_performance:
                cpu_usage = latest_performance.get_value('cpu_usage', 0)
                memory_usage = latest_performance.get_value('memory_usage', 0)
                response_time = latest_performance.get_value('response_time_avg', 0)

                if cpu_usage > 80 or memory_usage > 85 or response_time > 1000:
                    health_status = "warning"
                    health_score = 75

                if cpu_usage > 90 or memory_usage > 95 or response_time > 2000:
                    health_status = "critical"
                    health_score = 25

            return {
                "status": health_status,
                "score": health_score,
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "metrics": latest_performance.data if latest_performance else {}
            }

        except Exception as e:
            current_app.logger.error(f"System health error: {str(e)}")
            return {"status": "unknown", "score": 0}

    def _get_user_metrics(self, today_start: datetime, yesterday_start: datetime) -> Dict[str, Any]:
        """Get user statistics and metrics"""
        try:
            # Get basic user counts
            total_users = self.user_repository.count_users()
            active_users_today = self.user_repository.count_active_users_since(today_start)
            new_users_today = self.user_repository.count_new_users_since(today_start)
            new_users_yesterday = self.user_repository.count_new_users_between(yesterday_start, today_start)

            # Calculate growth rate
            growth_rate = 0
            if new_users_yesterday > 0:
                growth_rate = ((new_users_today - new_users_yesterday) / new_users_yesterday) * 100

            return {
                "total_users": total_users,
                "active_today": active_users_today,
                "new_today": new_users_today,
                "growth_rate": round(growth_rate, 2)
            }

        except Exception as e:
            current_app.logger.error(f"User metrics error: {str(e)}")
            return {}

    def _get_financial_metrics(self, today_start: datetime, month_start: datetime) -> Dict[str, Any]:
        """Get financial statistics"""
        try:
            if not self.transaction_repository:
                return {
                    "donations_today": 0,
                    "donations_month": 0,
                    "transactions_today": 0,
                    "average_donation": 0
                }

            # Get donation totals
            donations_today = self.transaction_repository.get_donation_total_since(today_start)
            donations_month = self.transaction_repository.get_donation_total_since(month_start)

            # Get transaction counts
            transactions_today = self.transaction_repository.count_transactions_since(today_start)

            # Get average donation
            avg_donation = donations_month / max(1, self.transaction_repository.count_donations_since(month_start))

            return {
                "donations_today": donations_today,
                "donations_month": donations_month,
                "transactions_today": transactions_today,
                "average_donation": round(avg_donation, 2)
            }

        except Exception as e:
            current_app.logger.error(f"Financial metrics error: {str(e)}")
            return {}

    def _get_content_metrics(self, today_start: datetime, week_start: datetime) -> Dict[str, Any]:
        """Get content moderation metrics"""
        try:
            # These would need to be implemented based on actual content models
            pending_games = 0  # self.game_repository.count_pending_approval()
            pending_onlus = 0  # self.onlus_repository.count_pending_verification()
            flagged_content = 0  # Content flagging system to be implemented

            return {
                "pending_game_reviews": pending_games,
                "pending_onlus_verifications": pending_onlus,
                "flagged_content_items": flagged_content
            }

        except Exception as e:
            current_app.logger.error(f"Content metrics error: {str(e)}")
            return {}

    def _get_security_alerts(self, admin_id: str) -> List[Dict[str, Any]]:
        """Get recent security alerts"""
        try:
            # Get recent failed admin actions
            failed_actions = self.audit_repository.find_failed_actions(hours=24, limit=5)

            # Get suspicious activity
            suspicious_activity = self.audit_repository.find_suspicious_activity(hours=24)

            alerts = []

            for action in failed_actions:
                alerts.append({
                    "type": "failed_action",
                    "message": f"Failed {action.action_type} by admin {action.admin_id}",
                    "timestamp": action.timestamp.isoformat(),
                    "severity": "medium"
                })

            for activity in suspicious_activity:
                alerts.append({
                    "type": activity["type"],
                    "message": f"{activity['type']}: {activity.get('count', 0)} occurrences",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "severity": activity.get("severity", "low")
                })

            return alerts[:10]  # Return top 10 alerts

        except Exception as e:
            current_app.logger.error(f"Security alerts error: {str(e)}")
            return []

    def _get_recent_activity(self, admin_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent admin activity"""
        try:
            recent_actions = self.audit_repository.find_actions_by_admin(admin_id, limit=limit)

            return [
                {
                    "action_type": action.action_type,
                    "target_type": action.target_type,
                    "target_id": action.target_id,
                    "timestamp": action.timestamp.isoformat(),
                    "status": action.status,
                    "reason": action.reason
                }
                for action in recent_actions
            ]

        except Exception as e:
            current_app.logger.error(f"Recent activity error: {str(e)}")
            return []

    def _parse_time_range(self, time_range: str) -> int:
        """Parse time range string to days"""
        if time_range.endswith('d'):
            return int(time_range[:-1])
        elif time_range.endswith('h'):
            return int(time_range[:-1]) / 24
        elif time_range.endswith('w'):
            return int(time_range[:-1]) * 7
        elif time_range.endswith('m'):
            return int(time_range[:-1]) * 30
        else:
            return 7  # Default to 7 days

    def _get_detailed_user_stats(self, start_time: datetime) -> Dict[str, Any]:
        """Get detailed user statistics"""
        # Implementation would depend on user repository methods
        return {}

    def _get_registration_trends(self, start_time: datetime, days: int) -> List[Dict[str, Any]]:
        """Get user registration trends"""
        # Implementation would depend on user repository aggregation methods
        return []

    def _get_user_activity_patterns(self, start_time: datetime) -> Dict[str, Any]:
        """Get user activity patterns"""
        # Implementation would depend on user activity tracking
        return {}

    def _get_user_demographics(self) -> Dict[str, Any]:
        """Get user demographic data"""
        # Implementation would depend on user profile data
        return {}

    def _get_top_active_users(self, start_time: datetime) -> List[Dict[str, Any]]:
        """Get most active users"""
        # Implementation would depend on user activity tracking
        return []

    def _get_user_support_metrics(self, start_time: datetime) -> Dict[str, Any]:
        """Get user support metrics"""
        # Implementation would depend on support ticket system
        return {}

    def _get_financial_overview(self, start_time: datetime) -> Dict[str, Any]:
        """Get financial overview data"""
        # Implementation would use transaction repository
        return {}

    def _get_donation_trends(self, start_time: datetime, days: int) -> List[Dict[str, Any]]:
        """Get donation trend data"""
        # Implementation would use transaction repository aggregation
        return []

    def _get_onlus_allocation_data(self, start_time: datetime) -> Dict[str, Any]:
        """Get ONLUS allocation breakdown"""
        # Implementation would use onlus and transaction repositories
        return {}

    def _get_revenue_breakdown(self, start_time: datetime) -> Dict[str, Any]:
        """Get revenue breakdown"""
        # Implementation would calculate platform fees and revenue
        return {}

    def _get_transaction_analysis(self, start_time: datetime) -> Dict[str, Any]:
        """Get transaction analysis"""
        # Implementation would analyze transaction patterns
        return {}

    def _get_fee_analysis(self, start_time: datetime) -> Dict[str, Any]:
        """Get fee analysis"""
        # Implementation would analyze processing fees
        return {}

    # Additional helper methods would be implemented as needed
    def _get_performance_trends(self, start_time: datetime) -> Dict[str, Any]:
        return {}

    def _get_infrastructure_status(self) -> Dict[str, Any]:
        return {}

    def _get_api_metrics(self, start_time: datetime) -> Dict[str, Any]:
        return {}

    def _get_database_metrics(self) -> Dict[str, Any]:
        return {}

    def _get_active_alerts(self) -> List[Dict[str, Any]]:
        return []

    def _get_system_capacity_info(self) -> Dict[str, Any]:
        return {}

    def _get_pending_content_reviews(self) -> Dict[str, Any]:
        return {}

    def _get_moderation_statistics(self, start_time: datetime) -> Dict[str, Any]:
        return {}

    def _get_flagged_content(self, start_time: datetime) -> List[Dict[str, Any]]:
        return []

    def _get_game_submission_queue(self) -> List[Dict[str, Any]]:
        return []

    def _get_onlus_verification_queue(self) -> List[Dict[str, Any]]:
        return []

    def _get_community_reports(self, start_time: datetime) -> List[Dict[str, Any]]:
        return []