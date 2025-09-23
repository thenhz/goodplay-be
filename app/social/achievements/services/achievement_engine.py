from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from flask import current_app
from bson import ObjectId

from ..repositories.achievement_repository import AchievementRepository
from ..models.achievement import Achievement
from ..models.user_achievement import UserAchievement
from ..models.badge import Badge


class AchievementEngine:
    """
    Core achievement engine for processing triggers and managing unlocks
    """

    def __init__(self):
        self.achievement_repo = AchievementRepository()

    def check_triggers(self, user_id: str, event_type: str,
                      event_data: Dict[str, Any]) -> Tuple[bool, str, List[Achievement]]:
        """
        Check if any achievements should be triggered by an event

        Args:
            user_id: ID of the user
            event_type: Type of event (game_session, social_friend, etc.)
            event_data: Event data containing relevant information

        Returns:
            Tuple[bool, str, List[Achievement]]: Success, message, unlocked achievements
        """
        try:
            unlocked_achievements = []

            # Get all active achievements that match this trigger type
            active_achievements = self.achievement_repo.find_active_achievements()
            relevant_achievements = [
                ach for ach in active_achievements
                if ach.get_trigger_type() == event_type
            ]

            current_app.logger.info(
                f"Checking {len(relevant_achievements)} achievements for event {event_type}"
            )

            for achievement in relevant_achievements:
                # Check if user already has this achievement
                user_achievement = self.achievement_repo.find_user_achievement(
                    user_id, achievement.achievement_id
                )

                if not user_achievement:
                    # Create new user achievement if it doesn't exist
                    user_achievement = UserAchievement(
                        user_id=user_id,
                        achievement_id=achievement.achievement_id,
                        max_progress=achievement.get_target_value() or 1
                    )
                    self.achievement_repo.create_user_achievement(user_achievement)

                # Skip if already completed
                if user_achievement.is_completed:
                    continue

                # Process the trigger based on event type
                was_unlocked = self._process_trigger(
                    user_id, achievement, user_achievement, event_data
                )

                if was_unlocked:
                    unlocked_achievements.append(achievement)

            message = f"{len(unlocked_achievements)} achievements unlocked"
            return True, message, unlocked_achievements

        except Exception as e:
            current_app.logger.error(f"Error checking triggers: {str(e)}")
            return False, "Error processing achievement triggers", []

    def _process_trigger(self, user_id: str, achievement: Achievement,
                        user_achievement: UserAchievement,
                        event_data: Dict[str, Any]) -> bool:
        """
        Process a specific trigger for an achievement

        Args:
            user_id: ID of the user
            achievement: Achievement definition
            user_achievement: User's progress for this achievement
            event_data: Event data

        Returns:
            bool: True if achievement was unlocked
        """
        trigger_type = achievement.get_trigger_type()

        try:
            if trigger_type == Achievement.GAME_SESSION:
                return self._process_game_session_trigger(
                    user_id, achievement, user_achievement, event_data
                )
            elif trigger_type == Achievement.GAME_SCORE:
                return self._process_game_score_trigger(
                    user_id, achievement, user_achievement, event_data
                )
            elif trigger_type == Achievement.SOCIAL_FRIEND:
                return self._process_social_friend_trigger(
                    user_id, achievement, user_achievement, event_data
                )
            elif trigger_type == Achievement.SOCIAL_LIKE:
                return self._process_social_like_trigger(
                    user_id, achievement, user_achievement, event_data
                )
            elif trigger_type == Achievement.DONATION_AMOUNT:
                return self._process_donation_amount_trigger(
                    user_id, achievement, user_achievement, event_data
                )
            elif trigger_type == Achievement.DONATION_COUNT:
                return self._process_donation_count_trigger(
                    user_id, achievement, user_achievement, event_data
                )
            elif trigger_type == Achievement.CONSECUTIVE_DAYS:
                return self._process_consecutive_days_trigger(
                    user_id, achievement, user_achievement, event_data
                )

        except Exception as e:
            current_app.logger.error(
                f"Error processing trigger {trigger_type}: {str(e)}"
            )

        return False

    def _process_game_session_trigger(self, user_id: str, achievement: Achievement,
                                    user_achievement: UserAchievement,
                                    event_data: Dict[str, Any]) -> bool:
        """Process game session completion trigger"""
        # Increment progress for each game session
        was_completed = user_achievement.increment_progress(1)

        # Update in database
        self.achievement_repo.update_user_achievement(
            user_id, achievement.achievement_id,
            {
                "progress": user_achievement.progress,
                "is_completed": user_achievement.is_completed,
                "completed_at": user_achievement.completed_at,
                "updated_at": user_achievement.updated_at
            }
        )

        if was_completed:
            return self._unlock_achievement(user_id, achievement)

        return False

    def _process_game_score_trigger(self, user_id: str, achievement: Achievement,
                                  user_achievement: UserAchievement,
                                  event_data: Dict[str, Any]) -> bool:
        """Process game score achievement trigger"""
        score = event_data.get('score', 0)
        target_value = achievement.get_target_value()

        if achievement.check_condition(score):
            # For score achievements, completing once is enough
            if not user_achievement.is_completed:
                user_achievement.update_progress(target_value)
                self.achievement_repo.update_user_achievement(
                    user_id, achievement.achievement_id,
                    {
                        "progress": user_achievement.progress,
                        "is_completed": user_achievement.is_completed,
                        "completed_at": user_achievement.completed_at,
                        "updated_at": user_achievement.updated_at
                    }
                )
                return self._unlock_achievement(user_id, achievement)

        return False

    def _process_social_friend_trigger(self, user_id: str, achievement: Achievement,
                                     user_achievement: UserAchievement,
                                     event_data: Dict[str, Any]) -> bool:
        """Process social friend addition trigger"""
        # Increment progress for each new friend
        was_completed = user_achievement.increment_progress(1)

        self.achievement_repo.update_user_achievement(
            user_id, achievement.achievement_id,
            {
                "progress": user_achievement.progress,
                "is_completed": user_achievement.is_completed,
                "completed_at": user_achievement.completed_at,
                "updated_at": user_achievement.updated_at
            }
        )

        if was_completed:
            return self._unlock_achievement(user_id, achievement)

        return False

    def _process_social_like_trigger(self, user_id: str, achievement: Achievement,
                                   user_achievement: UserAchievement,
                                   event_data: Dict[str, Any]) -> bool:
        """Process social like received trigger"""
        # Increment progress for each like received
        was_completed = user_achievement.increment_progress(1)

        self.achievement_repo.update_user_achievement(
            user_id, achievement.achievement_id,
            {
                "progress": user_achievement.progress,
                "is_completed": user_achievement.is_completed,
                "completed_at": user_achievement.completed_at,
                "updated_at": user_achievement.updated_at
            }
        )

        if was_completed:
            return self._unlock_achievement(user_id, achievement)

        return False

    def _process_donation_amount_trigger(self, user_id: str, achievement: Achievement,
                                       user_achievement: UserAchievement,
                                       event_data: Dict[str, Any]) -> bool:
        """Process donation amount trigger"""
        amount = event_data.get('amount', 0)

        # Add to total donation amount
        was_completed = user_achievement.increment_progress(int(amount * 100))  # Store in cents

        self.achievement_repo.update_user_achievement(
            user_id, achievement.achievement_id,
            {
                "progress": user_achievement.progress,
                "is_completed": user_achievement.is_completed,
                "completed_at": user_achievement.completed_at,
                "updated_at": user_achievement.updated_at
            }
        )

        if was_completed:
            return self._unlock_achievement(user_id, achievement)

        return False

    def _process_donation_count_trigger(self, user_id: str, achievement: Achievement,
                                      user_achievement: UserAchievement,
                                      event_data: Dict[str, Any]) -> bool:
        """Process donation count trigger"""
        # Increment for each donation
        was_completed = user_achievement.increment_progress(1)

        self.achievement_repo.update_user_achievement(
            user_id, achievement.achievement_id,
            {
                "progress": user_achievement.progress,
                "is_completed": user_achievement.is_completed,
                "completed_at": user_achievement.completed_at,
                "updated_at": user_achievement.updated_at
            }
        )

        if was_completed:
            return self._unlock_achievement(user_id, achievement)

        return False

    def _process_consecutive_days_trigger(self, user_id: str, achievement: Achievement,
                                        user_achievement: UserAchievement,
                                        event_data: Dict[str, Any]) -> bool:
        """Process consecutive days playing trigger"""
        # This requires checking user's play history
        # For now, assume event_data contains consecutive_days count
        consecutive_days = event_data.get('consecutive_days', 1)

        # Update progress to current consecutive days
        if consecutive_days > user_achievement.progress:
            user_achievement.update_progress(consecutive_days)

            self.achievement_repo.update_user_achievement(
                user_id, achievement.achievement_id,
                {
                    "progress": user_achievement.progress,
                    "is_completed": user_achievement.is_completed,
                    "completed_at": user_achievement.completed_at,
                    "updated_at": user_achievement.updated_at
                }
            )

            if user_achievement.is_completed:
                return self._unlock_achievement(user_id, achievement)

        return False

    def _unlock_achievement(self, user_id: str, achievement: Achievement) -> bool:
        """
        Unlock an achievement and create associated badge

        Args:
            user_id: ID of the user
            achievement: Achievement to unlock

        Returns:
            bool: True if successfully unlocked
        """
        try:
            # Create badge for the achievement
            badge = Badge(
                user_id=user_id,
                achievement_id=achievement.achievement_id,
                badge_name=achievement.name,
                badge_description=achievement.description,
                rarity=achievement.badge_rarity,
                icon_url=achievement.icon_url
            )

            self.achievement_repo.create_badge(badge)

            current_app.logger.info(
                f"Achievement unlocked: {achievement.achievement_id} for user {user_id}"
            )

            return True

        except Exception as e:
            current_app.logger.error(f"Error unlocking achievement: {str(e)}")
            return False

    def update_progress(self, user_id: str, achievement_id: str,
                       increment: int) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Update progress for a specific achievement

        Args:
            user_id: ID of the user
            achievement_id: ID of the achievement
            increment: Amount to increment progress

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success, message, achievement data
        """
        try:
            # Find the achievement definition
            achievement = self.achievement_repo.find_achievement_by_id(achievement_id)
            if not achievement:
                return False, "Achievement not found", None

            # Find or create user achievement
            user_achievement = self.achievement_repo.find_user_achievement(
                user_id, achievement_id
            )

            if not user_achievement:
                user_achievement = UserAchievement(
                    user_id=user_id,
                    achievement_id=achievement_id,
                    max_progress=achievement.get_target_value() or 1
                )
                self.achievement_repo.create_user_achievement(user_achievement)

            # Update progress
            was_completed = user_achievement.increment_progress(increment)

            # Update in database
            self.achievement_repo.update_user_achievement(
                user_id, achievement_id,
                {
                    "progress": user_achievement.progress,
                    "is_completed": user_achievement.is_completed,
                    "completed_at": user_achievement.completed_at,
                    "updated_at": user_achievement.updated_at
                }
            )

            result_data = user_achievement.to_response_dict()

            if was_completed:
                # Unlock achievement and create badge
                self._unlock_achievement(user_id, achievement)
                result_data["just_completed"] = True
                return True, "Achievement completed", result_data
            else:
                result_data["just_completed"] = False
                return True, "Progress updated", result_data

        except Exception as e:
            current_app.logger.error(f"Error updating progress: {str(e)}")
            return False, "Error updating achievement progress", None

    def calculate_impact_score(self, user_id: str) -> Tuple[bool, str, int]:
        """
        Calculate user's impact score based on completed achievements

        Args:
            user_id: ID of the user

        Returns:
            Tuple[bool, str, int]: Success, message, impact score
        """
        try:
            # Get user's completed achievements
            completed_achievements = self.achievement_repo.find_user_achievements(
                user_id, completed_only=True
            )

            impact_score = 0

            for user_achievement in completed_achievements:
                # Find achievement definition
                achievement = self.achievement_repo.find_achievement_by_id(
                    user_achievement.achievement_id
                )

                if achievement:
                    # Calculate score based on rarity and category
                    base_score = achievement.reward_credits
                    rarity_multiplier = achievement.get_rarity_multiplier()

                    # Additional multipliers for impact achievements
                    category_multiplier = 2.0 if achievement.is_impact_achievement() else 1.0

                    achievement_score = int(base_score * rarity_multiplier * category_multiplier)
                    impact_score += achievement_score

            return True, "Impact score calculated", impact_score

        except Exception as e:
            current_app.logger.error(f"Error calculating impact score: {str(e)}")
            return False, "Error calculating impact score", 0