from typing import Dict, Any, List
from flask import current_app
from ..services.progress_tracker import ProgressTracker


class DonationTriggers:
    """
    Trigger handlers for donation-related achievement events
    """

    def __init__(self):
        self.progress_tracker = ProgressTracker()

    def on_first_donation(self, user_id: str, donation_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Trigger when a user makes their first donation

        Args:
            user_id: ID of the user
            donation_data: Donation data

        Returns:
            List[Dict]: List of unlocked achievements
        """
        try:
            current_app.logger.info(f"Processing first donation for user {user_id}")

            # Track the donation activity
            success, message, unlocked_achievements = self.progress_tracker.track_donation_activity(
                user_id, donation_data
            )

            if success:
                current_app.logger.info(f"First donation tracked: {message}")
                return unlocked_achievements
            else:
                current_app.logger.error(f"Error tracking first donation: {message}")
                return []

        except Exception as e:
            current_app.logger.error(f"Error in first donation trigger: {str(e)}")
            return []

    def on_donation_amount_milestone(self, user_id: str, milestone_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Trigger when a user reaches a donation amount milestone

        Args:
            user_id: ID of the user
            milestone_data: Milestone data including total amount

        Returns:
            List[Dict]: List of unlocked achievements
        """
        try:
            current_app.logger.info(f"Processing donation amount milestone for user {user_id}")

            # Track the donation activity
            success, message, unlocked_achievements = self.progress_tracker.track_donation_activity(
                user_id, milestone_data
            )

            return unlocked_achievements if success else []

        except Exception as e:
            current_app.logger.error(f"Error in donation amount milestone trigger: {str(e)}")
            return []

    def on_donation_frequency_milestone(self, user_id: str, frequency_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Trigger when a user reaches a donation frequency milestone

        Args:
            user_id: ID of the user
            frequency_data: Frequency milestone data

        Returns:
            List[Dict]: List of unlocked achievements
        """
        try:
            current_app.logger.info(f"Processing donation frequency milestone for user {user_id}")

            # Track the donation activity
            success, message, unlocked_achievements = self.progress_tracker.track_donation_activity(
                user_id, frequency_data
            )

            return unlocked_achievements if success else []

        except Exception as e:
            current_app.logger.error(f"Error in donation frequency milestone trigger: {str(e)}")
            return []

    def on_multiple_onlus_support(self, user_id: str, onlus_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Trigger when a user supports multiple different ONLUS organizations

        Args:
            user_id: ID of the user
            onlus_data: ONLUS diversity data

        Returns:
            List[Dict]: List of unlocked achievements
        """
        try:
            current_app.logger.info(f"Processing multiple ONLUS support for user {user_id}")

            # Add specific event data for ONLUS diversity
            event_data = {
                **onlus_data,
                'event_type': 'onlus_diversity',
                'unique_onlus_count': onlus_data.get('unique_onlus_count', 1)
            }

            success, message, unlocked_achievements = self.progress_tracker.track_donation_activity(
                user_id, event_data
            )

            return unlocked_achievements if success else []

        except Exception as e:
            current_app.logger.error(f"Error in multiple ONLUS support trigger: {str(e)}")
            return []

    def on_monthly_donor_streak(self, user_id: str, streak_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Trigger when a user maintains a monthly donation streak

        Args:
            user_id: ID of the user
            streak_data: Monthly donation streak data

        Returns:
            List[Dict]: List of unlocked achievements
        """
        try:
            current_app.logger.info(f"Processing monthly donor streak for user {user_id}")

            # Add specific event data for monthly streak
            event_data = {
                **streak_data,
                'event_type': 'monthly_donation_streak',
                'consecutive_months': streak_data.get('consecutive_months', 1)
            }

            success, message, unlocked_achievements = self.progress_tracker.track_donation_activity(
                user_id, event_data
            )

            return unlocked_achievements if success else []

        except Exception as e:
            current_app.logger.error(f"Error in monthly donor streak trigger: {str(e)}")
            return []

    def on_campaign_support(self, user_id: str, campaign_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Trigger when a user supports a specific campaign

        Args:
            user_id: ID of the user
            campaign_data: Campaign support data

        Returns:
            List[Dict]: List of unlocked achievements
        """
        try:
            current_app.logger.info(f"Processing campaign support for user {user_id}")

            # Track as regular donation activity
            success, message, unlocked_achievements = self.progress_tracker.track_donation_activity(
                user_id, campaign_data
            )

            return unlocked_achievements if success else []

        except Exception as e:
            current_app.logger.error(f"Error in campaign support trigger: {str(e)}")
            return []

    def on_large_donation(self, user_id: str, donation_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Trigger when a user makes a large single donation

        Args:
            user_id: ID of the user
            donation_data: Large donation data

        Returns:
            List[Dict]: List of unlocked achievements
        """
        try:
            current_app.logger.info(f"Processing large donation for user {user_id}")

            # Add specific event data for large donation
            event_data = {
                **donation_data,
                'event_type': 'large_donation'
            }

            success, message, unlocked_achievements = self.progress_tracker.track_donation_activity(
                user_id, event_data
            )

            return unlocked_achievements if success else []

        except Exception as e:
            current_app.logger.error(f"Error in large donation trigger: {str(e)}")
            return []

    def on_emergency_response(self, user_id: str, emergency_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Trigger when a user donates to emergency campaigns

        Args:
            user_id: ID of the user
            emergency_data: Emergency response data

        Returns:
            List[Dict]: List of unlocked achievements
        """
        try:
            current_app.logger.info(f"Processing emergency response for user {user_id}")

            # Add specific event data for emergency response
            event_data = {
                **emergency_data,
                'event_type': 'emergency_response'
            }

            success, message, unlocked_achievements = self.progress_tracker.track_donation_activity(
                user_id, event_data
            )

            return unlocked_achievements if success else []

        except Exception as e:
            current_app.logger.error(f"Error in emergency response trigger: {str(e)}")
            return []

    def on_recurring_donation_setup(self, user_id: str, recurring_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Trigger when a user sets up recurring donations

        Args:
            user_id: ID of the user
            recurring_data: Recurring donation data

        Returns:
            List[Dict]: List of unlocked achievements
        """
        try:
            current_app.logger.info(f"Processing recurring donation setup for user {user_id}")

            # Add specific event data for recurring donations
            event_data = {
                **recurring_data,
                'event_type': 'recurring_donation_setup'
            }

            success, message, unlocked_achievements = self.progress_tracker.track_donation_activity(
                user_id, event_data
            )

            return unlocked_achievements if success else []

        except Exception as e:
            current_app.logger.error(f"Error in recurring donation setup trigger: {str(e)}")
            return []

    def on_donation_goal_reached(self, user_id: str, goal_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Trigger when a user reaches a personal donation goal

        Args:
            user_id: ID of the user
            goal_data: Donation goal data

        Returns:
            List[Dict]: List of unlocked achievements
        """
        try:
            current_app.logger.info(f"Processing donation goal reached for user {user_id}")

            # Track as milestone achievement
            success, message, unlocked_achievements = self.progress_tracker.track_donation_activity(
                user_id, goal_data
            )

            return unlocked_achievements if success else []

        except Exception as e:
            current_app.logger.error(f"Error in donation goal reached trigger: {str(e)}")
            return []

    def on_impact_milestone(self, user_id: str, impact_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Trigger when a user's donations reach an impact milestone

        Args:
            user_id: ID of the user
            impact_data: Impact milestone data

        Returns:
            List[Dict]: List of unlocked achievements
        """
        try:
            current_app.logger.info(f"Processing impact milestone for user {user_id}")

            # Add specific event data for impact milestone
            event_data = {
                **impact_data,
                'event_type': 'impact_milestone'
            }

            success, message, unlocked_achievements = self.progress_tracker.track_donation_activity(
                user_id, event_data
            )

            return unlocked_achievements if success else []

        except Exception as e:
            current_app.logger.error(f"Error in impact milestone trigger: {str(e)}")
            return []


# Global instance for easy import
donation_triggers = DonationTriggers()