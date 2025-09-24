from flask import Blueprint, request, current_app
from app.core.decorators.auth import auth_required
from app.core.decorators.admin import admin_required
from app.core.utils.response_helpers import success_response, error_response
from ..services.impact_calculator import ImpactCalculator
from ..services.leaderboard_service import LeaderboardService
from ..services.ranking_engine import RankingEngine


def register_routes(blueprint: Blueprint):
    """Register leaderboard API routes"""

    impact_calculator = ImpactCalculator()
    leaderboard_service = LeaderboardService()
    ranking_engine = RankingEngine()

    # === IMPACT SCORE ENDPOINTS === #

    @blueprint.route('/impact-score/me', methods=['GET'])
    @auth_required
    def get_my_impact_score(current_user):
        """Get current user's impact score with detailed breakdown"""
        try:
            user_id = str(current_user['_id'])

            success, message, impact_score = impact_calculator.calculate_user_impact_score(user_id)

            if success:
                return success_response("Impact score retrieved successfully", impact_score.to_response_dict())
            else:
                return error_response(message)

        except Exception as e:
            current_app.logger.error(f"Error getting impact score for user {current_user['_id']}: {str(e)}")
            return error_response("Failed to retrieve impact score", status_code=500)

    @blueprint.route('/impact-score/<user_id>', methods=['GET'])
    @auth_required
    def get_user_impact_score(current_user, user_id):
        """Get impact score for specific user (if public)"""
        try:
            success, message, impact_score = impact_calculator.calculate_user_impact_score(user_id)

            if success:
                # Check privacy settings would go here
                return success_response("Impact score retrieved successfully", impact_score.to_response_dict())
            else:
                return error_response(message)

        except Exception as e:
            current_app.logger.error(f"Error getting impact score for user {user_id}: {str(e)}")
            return error_response("Failed to retrieve impact score", status_code=500)

    @blueprint.route('/impact-score/refresh', methods=['POST'])
    @auth_required
    def refresh_my_impact_score(current_user):
        """Force refresh current user's impact score"""
        try:
            user_id = str(current_user['_id'])

            success, message, impact_score = impact_calculator.calculate_user_impact_score(
                user_id, force_recalculate=True
            )

            if success:
                return success_response("Impact score refreshed successfully", impact_score.to_response_dict())
            else:
                return error_response(message)

        except Exception as e:
            current_app.logger.error(f"Error refreshing impact score for user {current_user['_id']}: {str(e)}")
            return error_response("Failed to refresh impact score", status_code=500)

    @blueprint.route('/impact-score/history', methods=['GET'])
    @auth_required
    def get_impact_score_history(current_user):
        """Get user's impact score history and trends"""
        try:
            user_id = str(current_user['_id'])
            days = request.args.get('days', 30, type=int)

            success, message, impact_score = impact_calculator.calculate_user_impact_score(user_id)

            if not success:
                return error_response(message)

            # Get trend data
            trend = impact_score.get_score_trend(days=days)

            response_data = {
                'current_score': impact_score.impact_score,
                'trend': trend,
                'history': impact_score.score_history[-days:] if impact_score.score_history else []
            }

            return success_response("Impact score history retrieved successfully", response_data)

        except Exception as e:
            current_app.logger.error(f"Error getting impact score history for user {current_user['_id']}: {str(e)}")
            return error_response("Failed to retrieve impact score history", status_code=500)

    # === LEADERBOARD ENDPOINTS === #

    @blueprint.route('/leaderboards/<leaderboard_type>', methods=['GET'])
    @auth_required
    def get_leaderboard(current_user, leaderboard_type):
        """Get leaderboard by type with pagination"""
        try:
            period = request.args.get('period', 'all_time')
            page = request.args.get('page', 1, type=int)
            per_page = min(request.args.get('per_page', 50, type=int), 100)
            user_id = str(current_user['_id'])

            success, message, leaderboard_data = leaderboard_service.get_leaderboard(
                leaderboard_type, period, user_id, page, per_page
            )

            if success:
                return success_response("Leaderboard retrieved successfully", leaderboard_data)
            else:
                return error_response(message)

        except Exception as e:
            current_app.logger.error(f"Error getting leaderboard {leaderboard_type}: {str(e)}")
            return error_response("Failed to retrieve leaderboard", status_code=500)

    @blueprint.route('/leaderboards', methods=['GET'])
    @auth_required
    def get_leaderboard_summary(current_user):
        """Get summary of all available leaderboards"""
        try:
            # Get leaderboard types and their metadata
            from ..models.leaderboard import Leaderboard

            leaderboards = []
            for leaderboard_type in Leaderboard.VALID_TYPES:
                leaderboard_info = {
                    'type': leaderboard_type,
                    'display_name': Leaderboard({'leaderboard_type': leaderboard_type, 'period': 'all_time'}).get_type_display_name(),
                    'periods': []
                }

                for period in Leaderboard.VALID_PERIODS:
                    # Get basic stats for each period
                    stats_success, stats_message, stats = leaderboard_service.get_leaderboard_statistics(
                        leaderboard_type, period
                    )

                    period_info = {
                        'period': period,
                        'display_name': Leaderboard({'leaderboard_type': leaderboard_type, 'period': period}).get_period_display_name(),
                        'stats': stats if stats_success else None
                    }
                    leaderboard_info['periods'].append(period_info)

                leaderboards.append(leaderboard_info)

            return success_response("Leaderboard summary retrieved successfully", {
                'leaderboards': leaderboards,
                'total_types': len(Leaderboard.VALID_TYPES)
            })

        except Exception as e:
            current_app.logger.error(f"Error getting leaderboard summary: {str(e)}")
            return error_response("Failed to retrieve leaderboard summary", status_code=500)

    @blueprint.route('/leaderboards/friends', methods=['GET'])
    @auth_required
    def get_friends_leaderboard(current_user):
        """Get leaderboard showing user and their friends"""
        try:
            user_id = str(current_user['_id'])
            page = request.args.get('page', 1, type=int)
            per_page = min(request.args.get('per_page', 50, type=int), 100)

            success, message, leaderboard_data = leaderboard_service.get_friends_leaderboard(
                user_id, page, per_page
            )

            if success:
                return success_response("Friends leaderboard retrieved successfully", leaderboard_data)
            else:
                return error_response(message)

        except Exception as e:
            current_app.logger.error(f"Error getting friends leaderboard for user {current_user['_id']}: {str(e)}")
            return error_response("Failed to retrieve friends leaderboard", status_code=500)

    @blueprint.route('/leaderboards/my-positions', methods=['GET'])
    @auth_required
    def get_my_leaderboard_positions(current_user):
        """Get user's positions across all leaderboards"""
        try:
            user_id = str(current_user['_id'])

            success, message, summary_data = leaderboard_service.get_user_leaderboard_summary(user_id)

            if success:
                return success_response("User leaderboard positions retrieved successfully", summary_data)
            else:
                return error_response(message)

        except Exception as e:
            current_app.logger.error(f"Error getting leaderboard positions for user {current_user['_id']}: {str(e)}")
            return error_response("Failed to retrieve leaderboard positions", status_code=500)

    @blueprint.route('/leaderboards/<leaderboard_type>/statistics', methods=['GET'])
    @auth_required
    def get_leaderboard_statistics(current_user, leaderboard_type):
        """Get detailed statistics for a specific leaderboard"""
        try:
            period = request.args.get('period', 'all_time')

            success, message, stats = leaderboard_service.get_leaderboard_statistics(
                leaderboard_type, period
            )

            if success:
                return success_response("Leaderboard statistics retrieved successfully", stats)
            else:
                return error_response(message)

        except Exception as e:
            current_app.logger.error(f"Error getting statistics for {leaderboard_type}: {str(e)}")
            return error_response("Failed to retrieve leaderboard statistics", status_code=500)

    @blueprint.route('/leaderboards/<leaderboard_type>/top', methods=['GET'])
    @auth_required
    def get_top_performers(current_user, leaderboard_type):
        """Get top N performers from a leaderboard"""
        try:
            period = request.args.get('period', 'all_time')
            limit = min(request.args.get('limit', 10, type=int), 50)

            from ..repositories.leaderboard_repository import LeaderboardRepository
            leaderboard_repo = LeaderboardRepository()

            top_performers = leaderboard_repo.get_top_performers(leaderboard_type, period, limit)

            return success_response("Top performers retrieved successfully", {
                'leaderboard_type': leaderboard_type,
                'period': period,
                'limit': limit,
                'performers': top_performers
            })

        except Exception as e:
            current_app.logger.error(f"Error getting top performers for {leaderboard_type}: {str(e)}")
            return error_response("Failed to retrieve top performers", status_code=500)

    # === PRIVACY & SETTINGS ENDPOINTS === #

    @blueprint.route('/privacy/leaderboard-participation', methods=['POST'])
    @auth_required
    def update_leaderboard_privacy(current_user):
        """Update user's leaderboard privacy settings"""
        try:
            data = request.get_json()
            if not data:
                return error_response("Request data required")

            participation = data.get('participation')
            if participation is None:
                return error_response("Participation setting required")

            user_id = str(current_user['_id'])

            success, message = leaderboard_service.update_user_privacy_settings(
                user_id, bool(participation)
            )

            if success:
                return success_response("Privacy settings updated successfully")
            else:
                return error_response(message)

        except Exception as e:
            current_app.logger.error(f"Error updating privacy settings for user {current_user['_id']}: {str(e)}")
            return error_response("Failed to update privacy settings", status_code=500)

    @blueprint.route('/privacy/leaderboard-participation', methods=['GET'])
    @auth_required
    def get_leaderboard_privacy(current_user):
        """Get user's current leaderboard privacy settings"""
        try:
            participation = current_user.get('preferences', {}).get('privacy', {}).get('leaderboard_participation', True)

            return success_response("Privacy settings retrieved successfully", {
                'leaderboard_participation': participation
            })

        except Exception as e:
            current_app.logger.error(f"Error getting privacy settings for user {current_user['_id']}: {str(e)}")
            return error_response("Failed to retrieve privacy settings", status_code=500)

    # === RANKING ENGINE ENDPOINTS === #

    @blueprint.route('/rankings/trigger-update', methods=['POST'])
    @auth_required
    def trigger_ranking_update(current_user):
        """Trigger ranking update for current user"""
        try:
            data = request.get_json()
            activity_type = data.get('activity_type', 'general') if data else 'general'

            user_id = str(current_user['_id'])

            success, message = ranking_engine.trigger_user_score_update(
                user_id, activity_type
            )

            if success:
                return success_response("Ranking update triggered successfully")
            else:
                return error_response(message)

        except Exception as e:
            current_app.logger.error(f"Error triggering ranking update for user {current_user['_id']}: {str(e)}")
            return error_response("Failed to trigger ranking update", status_code=500)

    @blueprint.route('/rankings/health', methods=['GET'])
    @auth_required
    def get_ranking_health(current_user):
        """Get ranking system health status"""
        try:
            health_status = ranking_engine.get_ranking_health_status()

            return success_response("Ranking health status retrieved successfully", health_status)

        except Exception as e:
            current_app.logger.error(f"Error getting ranking health: {str(e)}")
            return error_response("Failed to retrieve ranking health", status_code=500)

    # === ADMIN ENDPOINTS === #

    @blueprint.route('/admin/impact-scores/recalculate', methods=['POST'])
    @admin_required
    def admin_recalculate_all_scores(current_admin):
        """Admin endpoint to recalculate all user impact scores"""
        try:
            data = request.get_json()
            batch_size = data.get('batch_size', 100) if data else 100

            success, message, stats = impact_calculator.recalculate_all_scores(batch_size)

            if success:
                return success_response("Impact scores recalculation completed", stats)
            else:
                return error_response(message)

        except Exception as e:
            current_app.logger.error(f"Error in admin score recalculation: {str(e)}")
            return error_response("Failed to recalculate scores", status_code=500)

    @blueprint.route('/admin/leaderboards/refresh', methods=['POST'])
    @admin_required
    def admin_refresh_leaderboards(current_admin):
        """Admin endpoint to refresh all leaderboards"""
        try:
            success, message, stats = leaderboard_service.refresh_all_leaderboards()

            if success:
                return success_response("Leaderboards refresh completed", stats)
            else:
                return error_response(message)

        except Exception as e:
            current_app.logger.error(f"Error in admin leaderboard refresh: {str(e)}")
            return error_response("Failed to refresh leaderboards", status_code=500)

    @blueprint.route('/admin/rankings/full-recalculate', methods=['POST'])
    @admin_required
    def admin_full_ranking_recalculate(current_admin):
        """Admin endpoint for full ranking system recalculation"""
        try:
            data = request.get_json()
            batch_size = data.get('batch_size', 100) if data else 100

            success, message, stats = ranking_engine.recalculate_all_rankings(batch_size)

            if success:
                return success_response("Full ranking recalculation completed", stats)
            else:
                return error_response(message)

        except Exception as e:
            current_app.logger.error(f"Error in admin full recalculation: {str(e)}")
            return error_response("Failed to perform full recalculation", status_code=500)

    @blueprint.route('/admin/rankings/optimize', methods=['POST'])
    @admin_required
    def admin_optimize_rankings(current_admin):
        """Admin endpoint to optimize ranking system performance"""
        try:
            success, message, stats = ranking_engine.optimize_rankings_performance()

            if success:
                return success_response("Ranking optimization completed", stats)
            else:
                return error_response(message)

        except Exception as e:
            current_app.logger.error(f"Error in ranking optimization: {str(e)}")
            return error_response("Failed to optimize rankings", status_code=500)

    @blueprint.route('/admin/rankings/background-updates', methods=['POST'])
    @admin_required
    def admin_control_background_updates(current_admin):
        """Admin endpoint to control background ranking updates"""
        try:
            data = request.get_json()
            if not data:
                return error_response("Request data required")

            action = data.get('action')  # 'start' or 'stop'

            if action == 'start':
                interval = data.get('interval_minutes', 60)
                ranking_engine.start_background_updates(interval)
                return success_response(f"Background updates started (interval: {interval}m)")

            elif action == 'stop':
                ranking_engine.stop_background_updates()
                return success_response("Background updates stopped")

            else:
                return error_response("Invalid action. Use 'start' or 'stop'")

        except Exception as e:
            current_app.logger.error(f"Error controlling background updates: {str(e)}")
            return error_response("Failed to control background updates", status_code=500)

    @blueprint.route('/admin/leaderboards/<leaderboard_type>/clear', methods=['DELETE'])
    @admin_required
    def admin_clear_leaderboard(current_admin, leaderboard_type):
        """Admin endpoint to clear a specific leaderboard"""
        try:
            period = request.args.get('period', 'all_time')

            from ..repositories.leaderboard_repository import LeaderboardRepository
            leaderboard_repo = LeaderboardRepository()

            success = leaderboard_repo.clear_leaderboard_entries(leaderboard_type, period)

            if success:
                return success_response(f"Leaderboard {leaderboard_type}_{period} cleared successfully")
            else:
                return error_response("Failed to clear leaderboard")

        except Exception as e:
            current_app.logger.error(f"Error clearing leaderboard {leaderboard_type}: {str(e)}")
            return error_response("Failed to clear leaderboard", status_code=500)

    @blueprint.route('/admin/system/stats', methods=['GET'])
    @admin_required
    def admin_get_system_stats(current_admin):
        """Admin endpoint to get comprehensive system statistics"""
        try:
            from ..repositories.impact_score_repository import ImpactScoreRepository
            from ..repositories.leaderboard_repository import LeaderboardRepository

            impact_score_repo = ImpactScoreRepository()
            leaderboard_repo = LeaderboardRepository()

            # Get various statistics
            score_stats = impact_score_repo.get_score_statistics()
            leaderboard_summary = leaderboard_repo.get_leaderboard_summary()
            health_status = ranking_engine.get_ranking_health_status()

            system_stats = {
                'impact_scores': score_stats,
                'leaderboards': leaderboard_summary,
                'system_health': health_status,
                'timestamp': health_status['timestamp']
            }

            return success_response("System statistics retrieved successfully", system_stats)

        except Exception as e:
            current_app.logger.error(f"Error getting system statistics: {str(e)}")
            return error_response("Failed to retrieve system statistics", status_code=500)