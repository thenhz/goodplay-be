from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Tuple
from flask import current_app
from app.donations.repositories.impact_metric_repository import ImpactMetricRepository
from app.donations.repositories.impact_update_repository import ImpactUpdateRepository
from app.donations.repositories.community_report_repository import CommunityReportRepository


class ImpactVisualizationService:
    """
    Service for generating data visualizations and dashboard analytics.

    Handles aggregation and formatting of impact data for frontend consumption.
    """

    def __init__(self):
        self.metric_repository = ImpactMetricRepository()
        self.update_repository = ImpactUpdateRepository()
        self.report_repository = CommunityReportRepository()

    def get_dashboard_data(self, user_id: str = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Get comprehensive dashboard data."""
        try:
            # Get latest community report
            latest_report = self.report_repository.get_latest_report_by_type('real_time')

            # Get featured updates
            featured_updates = self.update_repository.get_featured_updates()

            # Get trending updates
            trending_updates = self.update_repository.get_trending_updates()

            dashboard_data = {
                'platform_stats': latest_report.to_response_dict() if latest_report else {},
                'featured_updates': [update.to_response_dict() for update in featured_updates],
                'trending_updates': trending_updates,
                'generated_at': datetime.now(timezone.utc).isoformat()
            }

            return True, "DASHBOARD_DATA_SUCCESS", dashboard_data
        except Exception as e:
            current_app.logger.error(f"Error getting dashboard data: {str(e)}")
            return False, "DASHBOARD_DATA_ERROR", None

    def get_onlus_impact_visualization(self, onlus_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Get impact visualization data for an ONLUS."""
        try:
            # Get ONLUS metrics
            metrics = self.metric_repository.get_latest_metrics_by_onlus(onlus_id)

            # Get recent updates
            recent_updates = self.update_repository.get_recent_updates_by_onlus(onlus_id)

            visualization_data = {
                'onlus_id': onlus_id,
                'metrics': [metric.to_response_dict() for metric in metrics],
                'recent_updates': [update.to_response_dict() for update in recent_updates],
                'metrics_summary': self.metric_repository.get_metrics_summary_by_onlus(onlus_id)
            }

            return True, "ONLUS_VISUALIZATION_SUCCESS", visualization_data
        except Exception as e:
            current_app.logger.error(f"Error getting ONLUS visualization for {onlus_id}: {str(e)}")
            return False, "ONLUS_VISUALIZATION_ERROR", None