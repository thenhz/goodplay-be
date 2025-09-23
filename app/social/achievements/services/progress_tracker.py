from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime, timedelta
from flask import current_app

from .achievement_engine import AchievementEngine
from ..repositories.achievement_repository import AchievementRepository


class ProgressTracker:
    """
    Service for tracking achievement progress automatically based on user activities
    """

    def __init__(self):
        self.achievement_engine = AchievementEngine()
        self.achievement_repo = AchievementRepository()

    def track_game_session_completion(self, user_id: str, game_data: Dict[str, Any]) -> Tuple[bool, str, List[Dict[str, Any]]]:
        """
        Track game session completion and check for related achievements

        Args:
            user_id: ID of the user
            game_data: Game session data

        Returns:
            Tuple[bool, str, List[Dict]]: Success, message, unlocked achievements
        """
        try:
            unlocked_achievements = []

            # Track game session achievements
            success, message, session_achievements = self.achievement_engine.check_triggers(
                user_id, 'game_session', game_data
            )

            if session_achievements:
                unlocked_achievements.extend([ach.to_response_dict() for ach in session_achievements])

            # Track score-based achievements if score is provided
            if 'score' in game_data:
                success, message, score_achievements = self.achievement_engine.check_triggers(
                    user_id, 'game_score', game_data
                )

                if score_achievements:
                    unlocked_achievements.extend([ach.to_response_dict() for ach in score_achievements])

            # Check for consecutive days playing
            consecutive_days = self._calculate_consecutive_days(user_id)
            if consecutive_days > 1:
                game_data_with_streak = {**game_data, 'consecutive_days': consecutive_days}
                success, message, streak_achievements = self.achievement_engine.check_triggers(
                    user_id, 'consecutive_days', game_data_with_streak
                )

                if streak_achievements:
                    unlocked_achievements.extend([ach.to_response_dict() for ach in streak_achievements])

            return True, f"Tracked game session, {len(unlocked_achievements)} achievements unlocked", unlocked_achievements

        except Exception as e:
            current_app.logger.error(f"Error tracking game session: {str(e)}")
            return False, "Error tracking game session progress", []

    def track_social_activity(self, user_id: str, activity_type: str, activity_data: Dict[str, Any]) -> Tuple[bool, str, List[Dict[str, Any]]]:
        """
        Track social activities and check for related achievements

        Args:
            user_id: ID of the user
            activity_type: Type of social activity (friend_added, like_received, etc.)
            activity_data: Activity data

        Returns:
            Tuple[bool, str, List[Dict]]: Success, message, unlocked achievements
        """
        try:
            unlocked_achievements = []

            if activity_type == 'friend_added':
                success, message, achievements = self.achievement_engine.check_triggers(
                    user_id, 'social_friend', activity_data
                )

                if achievements:
                    unlocked_achievements.extend([ach.to_response_dict() for ach in achievements])

            elif activity_type == 'like_received':
                success, message, achievements = self.achievement_engine.check_triggers(
                    user_id, 'social_like', activity_data
                )

                if achievements:
                    unlocked_achievements.extend([ach.to_response_dict() for ach in achievements])

            return True, f"Tracked social activity, {len(unlocked_achievements)} achievements unlocked", unlocked_achievements

        except Exception as e:
            current_app.logger.error(f"Error tracking social activity: {str(e)}")
            return False, "Error tracking social activity progress", []

    def track_donation_activity(self, user_id: str, donation_data: Dict[str, Any]) -> Tuple[bool, str, List[Dict[str, Any]]]:
        """
        Track donation activities and check for related achievements

        Args:
            user_id: ID of the user
            donation_data: Donation data (amount, onlus_id, etc.)

        Returns:
            Tuple[bool, str, List[Dict]]: Success, message, unlocked achievements
        """
        try:
            unlocked_achievements = []

            # Track donation amount achievements
            success, message, amount_achievements = self.achievement_engine.check_triggers(
                user_id, 'donation_amount', donation_data
            )

            if amount_achievements:
                unlocked_achievements.extend([ach.to_response_dict() for ach in amount_achievements])

            # Track donation count achievements
            success, message, count_achievements = self.achievement_engine.check_triggers(
                user_id, 'donation_count', donation_data
            )

            if count_achievements:
                unlocked_achievements.extend([ach.to_response_dict() for ach in count_achievements])

            return True, f"Tracked donation activity, {len(unlocked_achievements)} achievements unlocked", unlocked_achievements

        except Exception as e:
            current_app.logger.error(f"Error tracking donation activity: {str(e)}")
            return False, "Error tracking donation activity progress", []

    def get_user_progress_summary(self, user_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Get comprehensive progress summary for a user

        Args:
            user_id: ID of the user

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success, message, progress data
        """
        try:
            # Get basic achievement stats
            stats = self.achievement_repo.get_user_achievement_stats(user_id)

            # Get badge counts by rarity
            badge_counts = self.achievement_repo.count_user_badges_by_rarity(user_id)

            # Get recent achievements (last 7 days)
            recent_achievements = self._get_recent_achievements(user_id, days=7)

            # Get achievements close to completion
            close_to_completion = self._get_close_to_completion(user_id)

            # Calculate impact score
            success, message, impact_score = self.achievement_engine.calculate_impact_score(user_id)

            progress_summary = {
                "stats": stats,
                "badge_counts": badge_counts,
                "recent_achievements": recent_achievements,
                "close_to_completion": close_to_completion,
                "impact_score": impact_score,
                "next_milestones": self._get_next_milestones(user_id)
            }

            return True, "Progress summary retrieved", progress_summary

        except Exception as e:
            current_app.logger.error(f"Error getting progress summary: {str(e)}")
            return False, "Error retrieving progress summary", None

    def get_achievement_recommendations(self, user_id: str) -> Tuple[bool, str, List[Dict[str, Any]]]:
        """
        Get achievement recommendations based on user activity

        Args:
            user_id: ID of the user

        Returns:
            Tuple[bool, str, List[Dict]]: Success, message, recommended achievements
        """
        try:
            recommendations = []

            # Get user's current achievements
            user_achievements = self.achievement_repo.find_user_achievements(user_id)
            completed_achievement_ids = {
                ua.achievement_id for ua in user_achievements if ua.is_completed
            }

            # Get all active achievements
            all_achievements = self.achievement_repo.find_active_achievements()

            # Find uncompleted achievements and rank by difficulty/progress
            for achievement in all_achievements:
                if achievement.achievement_id not in completed_achievement_ids:
                    user_achievement = next(
                        (ua for ua in user_achievements if ua.achievement_id == achievement.achievement_id),
                        None
                    )

                    progress_percentage = 0
                    if user_achievement:
                        progress_percentage = user_achievement.get_progress_percentage()

                    # Calculate recommendation score
                    recommendation_score = self._calculate_recommendation_score(
                        achievement, progress_percentage
                    )

                    recommendation = {
                        "achievement": achievement.to_response_dict(),
                        "current_progress": progress_percentage,
                        "recommendation_score": recommendation_score,
                        "difficulty": self._get_achievement_difficulty(achievement),
                        "estimated_time": self._estimate_completion_time(achievement)
                    }

                    recommendations.append(recommendation)

            # Sort by recommendation score (descending)
            recommendations.sort(key=lambda x: x["recommendation_score"], reverse=True)

            # Return top 10 recommendations
            return True, "Achievement recommendations generated", recommendations[:10]

        except Exception as e:
            current_app.logger.error(f"Error generating recommendations: {str(e)}")
            return False, "Error generating achievement recommendations", []

    def _calculate_consecutive_days(self, user_id: str) -> int:
        """Calculate consecutive days the user has been active"""
        # This is a simplified implementation
        # In a real scenario, you'd check game session history
        # For now, return a placeholder value
        return 1

    def _get_recent_achievements(self, user_id: str, days: int = 7) -> List[Dict[str, Any]]:
        """Get achievements completed in the last N days"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            user_achievements = self.achievement_repo.find_user_achievements(user_id, completed_only=True)

            recent = []
            for user_achievement in user_achievements:
                if (user_achievement.completed_at and
                    user_achievement.completed_at >= cutoff_date):
                    recent.append(user_achievement.to_response_dict())

            return recent
        except Exception:
            return []

    def _get_close_to_completion(self, user_id: str, threshold: float = 80.0) -> List[Dict[str, Any]]:
        """Get achievements that are close to completion (>80% progress)"""
        try:
            user_achievements = self.achievement_repo.find_user_achievements(user_id)

            close_to_completion = []
            for user_achievement in user_achievements:
                if (not user_achievement.is_completed and
                    user_achievement.get_progress_percentage() >= threshold):
                    close_to_completion.append(user_achievement.to_response_dict())

            return close_to_completion
        except Exception:
            return []

    def _get_next_milestones(self, user_id: str) -> List[Dict[str, Any]]:
        """Get next milestone achievements to work towards"""
        try:
            # Get user's badge counts
            badge_counts = self.achievement_repo.count_user_badges_by_rarity(user_id)

            milestones = []

            # Define milestone targets
            milestone_targets = {
                "common_badges": [5, 10, 25, 50],
                "rare_badges": [3, 5, 10, 20],
                "epic_badges": [1, 3, 5, 10],
                "legendary_badges": [1, 2, 3, 5]
            }

            rarity_mapping = {
                "common_badges": "common",
                "rare_badges": "rare",
                "epic_badges": "epic",
                "legendary_badges": "legendary"
            }

            for milestone_type, targets in milestone_targets.items():
                rarity = rarity_mapping[milestone_type]
                current_count = badge_counts.get(rarity, 0)

                # Find next target
                next_target = next((target for target in targets if target > current_count), None)

                if next_target:
                    milestones.append({
                        "type": milestone_type,
                        "current": current_count,
                        "target": next_target,
                        "progress_percentage": (current_count / next_target) * 100
                    })

            return milestones
        except Exception:
            return []

    def _calculate_recommendation_score(self, achievement, progress_percentage: float) -> float:
        """Calculate recommendation score for an achievement"""
        # Base score starts with progress
        score = progress_percentage

        # Bonus for partially started achievements
        if progress_percentage > 0:
            score += 20

        # Bonus for easier achievements (common/rare)
        if achievement.badge_rarity in ['common', 'rare']:
            score += 15

        # Bonus for gaming achievements (most engaging)
        if achievement.is_gaming_achievement():
            score += 10

        # Penalty for very difficult achievements
        if achievement.badge_rarity == 'legendary':
            score -= 10

        return min(score, 100)  # Cap at 100

    def _get_achievement_difficulty(self, achievement) -> str:
        """Get difficulty level of an achievement"""
        target_value = achievement.get_target_value()
        rarity = achievement.badge_rarity

        if rarity == 'legendary' or (target_value and target_value > 100):
            return 'very_hard'
        elif rarity == 'epic' or (target_value and target_value > 50):
            return 'hard'
        elif rarity == 'rare' or (target_value and target_value > 10):
            return 'medium'
        else:
            return 'easy'

    def _estimate_completion_time(self, achievement) -> str:
        """Estimate time to complete achievement"""
        difficulty = self._get_achievement_difficulty(achievement)
        trigger_type = achievement.get_trigger_type()

        if trigger_type == 'consecutive_days':
            target = achievement.get_target_value()
            return f"{target} days"

        time_estimates = {
            'easy': '1-2 sessions',
            'medium': '1-2 weeks',
            'hard': '2-4 weeks',
            'very_hard': '1-2 months'
        }

        return time_estimates.get(difficulty, 'Unknown')