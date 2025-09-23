from typing import Dict, Any, List
from flask import current_app
from ..services.progress_tracker import ProgressTracker


class SocialTriggers:
    """
    Trigger handlers for social-related achievement events
    """

    def __init__(self):
        self.progress_tracker = ProgressTracker()

    def on_friend_added(self, user_id: str, friend_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Trigger when a user adds a friend

        Args:
            user_id: ID of the user
            friend_data: Friend addition data

        Returns:
            List[Dict]: List of unlocked achievements
        """
        try:
            current_app.logger.info(f"Processing friend addition for user {user_id}")

            # Track the social activity
            success, message, unlocked_achievements = self.progress_tracker.track_social_activity(
                user_id, 'friend_added', friend_data
            )

            if success:
                current_app.logger.info(f"Friend addition tracked: {message}")
                return unlocked_achievements
            else:
                current_app.logger.error(f"Error tracking friend addition: {message}")
                return []

        except Exception as e:
            current_app.logger.error(f"Error in friend addition trigger: {str(e)}")
            return []

    def on_like_received(self, user_id: str, like_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Trigger when a user receives a like on their activity

        Args:
            user_id: ID of the user
            like_data: Like received data

        Returns:
            List[Dict]: List of unlocked achievements
        """
        try:
            current_app.logger.info(f"Processing like received for user {user_id}")

            # Track the social activity
            success, message, unlocked_achievements = self.progress_tracker.track_social_activity(
                user_id, 'like_received', like_data
            )

            if success:
                current_app.logger.info(f"Like received tracked: {message}")
                return unlocked_achievements
            else:
                current_app.logger.error(f"Error tracking like received: {message}")
                return []

        except Exception as e:
            current_app.logger.error(f"Error in like received trigger: {str(e)}")
            return []

    def on_comment_received(self, user_id: str, comment_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Trigger when a user receives a comment on their activity

        Args:
            user_id: ID of the user
            comment_data: Comment received data

        Returns:
            List[Dict]: List of unlocked achievements
        """
        try:
            current_app.logger.info(f"Processing comment received for user {user_id}")

            # Track as like activity for achievement purposes
            success, message, unlocked_achievements = self.progress_tracker.track_social_activity(
                user_id, 'like_received', comment_data
            )

            return unlocked_achievements if success else []

        except Exception as e:
            current_app.logger.error(f"Error in comment received trigger: {str(e)}")
            return []

    def on_community_participation(self, user_id: str, participation_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Trigger when a user participates in community activities

        Args:
            user_id: ID of the user
            participation_data: Community participation data

        Returns:
            List[Dict]: List of unlocked achievements
        """
        try:
            current_app.logger.info(f"Processing community participation for user {user_id}")

            # Track as social activity
            success, message, unlocked_achievements = self.progress_tracker.track_social_activity(
                user_id, 'community_participation', participation_data
            )

            return unlocked_achievements if success else []

        except Exception as e:
            current_app.logger.error(f"Error in community participation trigger: {str(e)}")
            return []

    def on_profile_completed(self, user_id: str, profile_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Trigger when a user completes their profile

        Args:
            user_id: ID of the user
            profile_data: Profile completion data

        Returns:
            List[Dict]: List of unlocked achievements
        """
        try:
            current_app.logger.info(f"Processing profile completion for user {user_id}")

            # Track as social activity
            success, message, unlocked_achievements = self.progress_tracker.track_social_activity(
                user_id, 'profile_completed', profile_data
            )

            return unlocked_achievements if success else []

        except Exception as e:
            current_app.logger.error(f"Error in profile completion trigger: {str(e)}")
            return []

    def on_help_provided(self, user_id: str, help_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Trigger when a user helps another user with challenges

        Args:
            user_id: ID of the user
            help_data: Help provided data

        Returns:
            List[Dict]: List of unlocked achievements
        """
        try:
            current_app.logger.info(f"Processing help provided for user {user_id}")

            # Track as social activity
            success, message, unlocked_achievements = self.progress_tracker.track_social_activity(
                user_id, 'help_provided', help_data
            )

            return unlocked_achievements if success else []

        except Exception as e:
            current_app.logger.error(f"Error in help provided trigger: {str(e)}")
            return []

    def on_social_sharing(self, user_id: str, sharing_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Trigger when a user shares achievements or activities

        Args:
            user_id: ID of the user
            sharing_data: Social sharing data

        Returns:
            List[Dict]: List of unlocked achievements
        """
        try:
            current_app.logger.info(f"Processing social sharing for user {user_id}")

            # Track as social activity
            success, message, unlocked_achievements = self.progress_tracker.track_social_activity(
                user_id, 'social_sharing', sharing_data
            )

            return unlocked_achievements if success else []

        except Exception as e:
            current_app.logger.error(f"Error in social sharing trigger: {str(e)}")
            return []

    def on_group_creation(self, user_id: str, group_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Trigger when a user creates a group or community

        Args:
            user_id: ID of the user
            group_data: Group creation data

        Returns:
            List[Dict]: List of unlocked achievements
        """
        try:
            current_app.logger.info(f"Processing group creation for user {user_id}")

            # Track as social activity
            success, message, unlocked_achievements = self.progress_tracker.track_social_activity(
                user_id, 'group_creation', group_data
            )

            return unlocked_achievements if success else []

        except Exception as e:
            current_app.logger.error(f"Error in group creation trigger: {str(e)}")
            return []

    def on_mentorship_activity(self, user_id: str, mentorship_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Trigger when a user engages in mentorship activities

        Args:
            user_id: ID of the user
            mentorship_data: Mentorship activity data

        Returns:
            List[Dict]: List of unlocked achievements
        """
        try:
            current_app.logger.info(f"Processing mentorship activity for user {user_id}")

            # Track as help provided activity
            success, message, unlocked_achievements = self.progress_tracker.track_social_activity(
                user_id, 'help_provided', mentorship_data
            )

            return unlocked_achievements if success else []

        except Exception as e:
            current_app.logger.error(f"Error in mentorship activity trigger: {str(e)}")
            return []

    def on_social_milestone(self, user_id: str, milestone_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Trigger when a user reaches a social milestone (e.g., 100 friends, 1000 likes)

        Args:
            user_id: ID of the user
            milestone_data: Social milestone data

        Returns:
            List[Dict]: List of unlocked achievements
        """
        try:
            current_app.logger.info(f"Processing social milestone for user {user_id}")

            milestone_type = milestone_data.get('milestone_type', 'unknown')

            if milestone_type == 'friends_milestone':
                activity_type = 'friend_added'
            elif milestone_type == 'likes_milestone':
                activity_type = 'like_received'
            else:
                activity_type = 'social_milestone'

            # Track the appropriate social activity
            success, message, unlocked_achievements = self.progress_tracker.track_social_activity(
                user_id, activity_type, milestone_data
            )

            return unlocked_achievements if success else []

        except Exception as e:
            current_app.logger.error(f"Error in social milestone trigger: {str(e)}")
            return []


# Global instance for easy import
social_triggers = SocialTriggers()