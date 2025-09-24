from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime, timedelta, timezone
from flask import current_app
import threading
import time

from ..repositories.impact_score_repository import ImpactScoreRepository
from ..repositories.leaderboard_repository import LeaderboardRepository
from .impact_calculator import ImpactCalculator
from .leaderboard_service import LeaderboardService


class RankingEngine:
    """
    Service for real-time ranking updates and batch processing

    Handles:
    - Real-time score updates when users complete activities
    - Scheduled batch updates for all rankings
    - Efficient ranking recalculation algorithms
    - Performance optimization for large datasets
    """

    def __init__(self):
        self.impact_score_repo = ImpactScoreRepository()
        self.leaderboard_repo = LeaderboardRepository()
        self.impact_calculator = ImpactCalculator()
        self.leaderboard_service = LeaderboardService()

        # Threading for background updates
        self._update_thread = None
        self._stop_updates = False
        self._last_batch_update = datetime.now(timezone.utc)

    def trigger_user_score_update(self, user_id: str, activity_type: str,
                                 activity_data: Optional[Dict[str, Any]] = None) -> Tuple[bool, str]:
        """
        Trigger real-time score update for user based on activity

        Args:
            user_id: User ID who performed the activity
            activity_type: Type of activity (gaming, social, donation)
            activity_data: Additional activity context data

        Returns:
            Tuple of (success, message)
        """
        try:
            current_app.logger.info(f"Triggering score update for user {user_id}, activity: {activity_type}")

            # Update impact score
            success, message, impact_score = self.impact_calculator.calculate_user_impact_score(
                user_id, force_recalculate=True
            )

            if not success:
                return False, f"Failed to update impact score: {message}"

            # Update relevant leaderboards asynchronously
            self._queue_leaderboard_updates(user_id, impact_score, activity_type)

            return True, "Score update triggered successfully"

        except Exception as e:
            current_app.logger.error(f"Error triggering score update for user {user_id}: {str(e)}")
            return False, "Failed to trigger score update"

    def update_user_rankings(self, user_id: str) -> Tuple[bool, str, Dict[str, int]]:
        """
        Update user's positions across all leaderboards

        Args:
            user_id: User ID to update rankings for

        Returns:
            Tuple of (success, message, ranking_updates)
        """
        try:
            # Get user's current impact score
            impact_score = self.impact_score_repo.find_by_user_id(user_id)
            if not impact_score:
                return False, "User impact score not found", {}

            updates = {}

            # Update global rankings
            global_rank = self._calculate_global_rank(user_id, impact_score.impact_score)
            if global_rank:
                impact_score.rank_global = global_rank
                updates['global'] = global_rank

            # Update weekly rankings
            weekly_rank = self._calculate_weekly_rank(user_id, impact_score.impact_score)
            if weekly_rank:
                impact_score.rank_weekly = weekly_rank
                updates['weekly'] = weekly_rank

            # Save updated rankings
            self.impact_score_repo.update_impact_score(impact_score)

            # Update leaderboard entries
            self._update_user_leaderboard_entries(user_id, impact_score)

            return True, "User rankings updated successfully", updates

        except Exception as e:
            current_app.logger.error(f"Error updating rankings for user {user_id}: {str(e)}")
            return False, "Failed to update user rankings", {}

    def run_scheduled_updates(self) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Run scheduled batch updates for all rankings

        Returns:
            Tuple of (success, message, update_stats)
        """
        try:
            current_app.logger.info("Starting scheduled ranking updates")
            start_time = datetime.now(timezone.utc)

            # Update all impact score rankings
            ranking_updates = self.impact_score_repo.update_rankings()

            # Refresh stale leaderboards
            stale_leaderboards = self.leaderboard_repo.get_stale_leaderboards(hours_threshold=1)
            leaderboard_updates = 0

            for leaderboard_info in stale_leaderboards:
                leaderboard = self.leaderboard_repo.find_by_type_and_period(
                    leaderboard_info['leaderboard_type'],
                    leaderboard_info['period']
                )

                if leaderboard:
                    success = self.leaderboard_service._update_leaderboard_data(leaderboard)
                    if success:
                        leaderboard_updates += 1

            # Calculate execution time
            execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()

            stats = {
                'ranking_updates': ranking_updates,
                'leaderboard_updates': leaderboard_updates,
                'execution_time_seconds': execution_time,
                'timestamp': start_time.isoformat()
            }

            self._last_batch_update = start_time
            current_app.logger.info(f"Completed scheduled updates in {execution_time:.2f}s")

            return True, "Scheduled updates completed successfully", stats

        except Exception as e:
            current_app.logger.error(f"Error in scheduled updates: {str(e)}")
            return False, "Scheduled updates failed", {}

    def start_background_updates(self, update_interval_minutes: int = 60):
        """
        Start background thread for periodic ranking updates

        Args:
            update_interval_minutes: Minutes between updates
        """
        if self._update_thread and self._update_thread.is_alive():
            current_app.logger.warning("Background updates already running")
            return

        self._stop_updates = False
        self._update_thread = threading.Thread(
            target=self._background_update_worker,
            args=(update_interval_minutes,),
            daemon=True
        )
        self._update_thread.start()

        current_app.logger.info(f"Started background ranking updates (interval: {update_interval_minutes}m)")

    def stop_background_updates(self):
        """Stop background ranking updates"""
        self._stop_updates = True
        if self._update_thread and self._update_thread.is_alive():
            self._update_thread.join(timeout=30)

        current_app.logger.info("Stopped background ranking updates")

    def get_ranking_health_status(self) -> Dict[str, Any]:
        """
        Get health status of ranking system

        Returns:
            Dict with system health metrics
        """
        try:
            # Get score statistics
            score_stats = self.impact_score_repo.get_score_statistics()

            # Get leaderboard summary
            leaderboard_summary = self.leaderboard_repo.get_leaderboard_summary()

            # Get stale data counts
            stale_scores = len(self.impact_score_repo.get_stale_scores(hours_threshold=24))
            stale_leaderboards = len(self.leaderboard_repo.get_stale_leaderboards(hours_threshold=2))

            # Calculate health score
            total_users = score_stats.get('total_users', 0)
            health_score = 100

            if total_users > 0:
                stale_score_percentage = (stale_scores / total_users) * 100
                if stale_score_percentage > 10:
                    health_score -= 20
                elif stale_score_percentage > 5:
                    health_score -= 10

            if stale_leaderboards > 5:
                health_score -= 15
            elif stale_leaderboards > 2:
                health_score -= 5

            # Determine status
            if health_score >= 90:
                status = "healthy"
            elif health_score >= 70:
                status = "warning"
            else:
                status = "critical"

            return {
                'status': status,
                'health_score': health_score,
                'metrics': {
                    'total_users_with_scores': total_users,
                    'stale_scores': stale_scores,
                    'stale_leaderboards': stale_leaderboards,
                    'last_batch_update': self._last_batch_update.isoformat()
                },
                'score_statistics': score_stats,
                'leaderboard_summary': leaderboard_summary,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            current_app.logger.error(f"Error getting ranking health status: {str(e)}")
            return {
                'status': 'error',
                'health_score': 0,
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

    def recalculate_all_rankings(self, batch_size: int = 100) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Full recalculation of all rankings and leaderboards

        Args:
            batch_size: Users to process per batch

        Returns:
            Tuple of (success, message, stats)
        """
        try:
            current_app.logger.info("Starting full ranking recalculation")
            start_time = datetime.now(timezone.utc)

            # Recalculate all impact scores
            score_success, score_message, score_stats = self.impact_calculator.recalculate_all_scores(
                batch_size=batch_size
            )

            if not score_success:
                return False, f"Score recalculation failed: {score_message}", {}

            # Update all rankings
            ranking_updates = self.impact_score_repo.update_rankings()

            # Refresh all leaderboards
            leaderboard_success, leaderboard_message, leaderboard_stats = self.leaderboard_service.refresh_all_leaderboards()

            execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()

            combined_stats = {
                'execution_time_seconds': execution_time,
                'score_recalculation': score_stats,
                'ranking_updates': ranking_updates,
                'leaderboard_refresh': leaderboard_stats,
                'timestamp': start_time.isoformat()
            }

            current_app.logger.info(f"Completed full recalculation in {execution_time:.2f}s")

            return True, "Full ranking recalculation completed", combined_stats

        except Exception as e:
            current_app.logger.error(f"Error in full ranking recalculation: {str(e)}")
            return False, "Full recalculation failed", {}

    # Private methods

    def _background_update_worker(self, update_interval_minutes: int):
        """Background worker for periodic updates"""
        while not self._stop_updates:
            try:
                # Wait for interval
                for _ in range(update_interval_minutes * 60):
                    if self._stop_updates:
                        return
                    time.sleep(1)

                # Run scheduled updates
                if not self._stop_updates:
                    self.run_scheduled_updates()

            except Exception as e:
                current_app.logger.error(f"Error in background update worker: {str(e)}")

    def _queue_leaderboard_updates(self, user_id: str, impact_score, activity_type: str):
        """Queue leaderboard updates for user (async processing)"""
        try:
            # This would typically use a task queue like Celery
            # For now, we'll do direct updates for critical leaderboards

            # Update user's ranking positions
            self.update_user_rankings(user_id)

            current_app.logger.debug(f"Queued leaderboard updates for user {user_id}")

        except Exception as e:
            current_app.logger.error(f"Error queuing leaderboard updates: {str(e)}")

    def _calculate_global_rank(self, user_id: str, user_score: float) -> Optional[int]:
        """Calculate user's global rank"""
        try:
            # Count users with higher scores
            higher_score_count = self.impact_score_repo.count({
                'impact_score': {'$gt': user_score}
            })

            return higher_score_count + 1

        except Exception as e:
            current_app.logger.error(f"Error calculating global rank for user {user_id}: {str(e)}")
            return None

    def _calculate_weekly_rank(self, user_id: str, user_score: float) -> Optional[int]:
        """Calculate user's weekly rank"""
        try:
            # Get active users from last week
            cutoff_date = datetime.now(timezone.utc) - timedelta(weeks=1)

            # Count active users with higher scores
            higher_score_count = self.impact_score_repo.count({
                'impact_score': {'$gt': user_score},
                'last_calculated': {'$gte': cutoff_date}
            })

            return higher_score_count + 1

        except Exception as e:
            current_app.logger.error(f"Error calculating weekly rank for user {user_id}: {str(e)}")
            return None

    def _update_user_leaderboard_entries(self, user_id: str, impact_score):
        """Update user's entries in all relevant leaderboards"""
        try:
            from ..models.leaderboard import Leaderboard
            from ..models.leaderboard_entry import LeaderboardEntry

            # Get user data for display
            user = self.impact_score_repo.user_repo.find_by_id(user_id)
            if not user:
                return

            display_name = user.get('social_profile', {}).get('display_name')
            if not display_name:
                display_name = user.get('first_name', 'Unknown User')

            # Create leaderboard entry
            entry = LeaderboardEntry(
                user_id=user_id,
                score=impact_score.impact_score,
                rank=1,  # Will be recalculated
                display_name=display_name,
                score_components={
                    'gaming': impact_score.gaming_component,
                    'social': impact_score.social_component,
                    'donation': impact_score.donation_component
                }
            )

            # Update relevant leaderboards
            relevant_types = [
                Leaderboard.GLOBAL_IMPACT,
                Leaderboard.WEEKLY_WARRIORS
            ]

            for leaderboard_type in relevant_types:
                for period in Leaderboard.VALID_PERIODS:
                    self.leaderboard_repo.add_entry_to_leaderboard(
                        leaderboard_type, period, entry
                    )

        except Exception as e:
            current_app.logger.error(f"Error updating leaderboard entries for user {user_id}: {str(e)}")

    def optimize_rankings_performance(self) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Optimize ranking system performance

        Returns:
            Tuple of (success, message, optimization_stats)
        """
        try:
            current_app.logger.info("Starting ranking performance optimization")

            # Create indexes if they don't exist
            self.impact_score_repo.create_indexes()
            self.leaderboard_repo.create_indexes()

            # Clean up old history data (keep only last 90 days)
            cleanup_count = self._cleanup_old_history_data()

            # Optimize leaderboard storage
            optimization_count = self._optimize_leaderboard_storage()

            stats = {
                'history_records_cleaned': cleanup_count,
                'leaderboards_optimized': optimization_count,
                'indexes_created': True,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

            return True, "Performance optimization completed", stats

        except Exception as e:
            current_app.logger.error(f"Error in performance optimization: {str(e)}")
            return False, "Performance optimization failed", {}

    def _cleanup_old_history_data(self) -> int:
        """Clean up old score history data"""
        try:
            # This would clean up old history entries
            # Implementation depends on specific cleanup requirements
            return 0  # Placeholder

        except Exception as e:
            current_app.logger.error(f"Error cleaning up history data: {str(e)}")
            return 0

    def _optimize_leaderboard_storage(self) -> int:
        """Optimize leaderboard data storage"""
        try:
            # This would optimize leaderboard storage
            # Implementation depends on specific optimization strategies
            return 0  # Placeholder

        except Exception as e:
            current_app.logger.error(f"Error optimizing leaderboard storage: {str(e)}")
            return 0