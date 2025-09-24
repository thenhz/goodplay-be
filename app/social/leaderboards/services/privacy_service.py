from typing import Dict, Any, Optional, Tuple, List
from flask import current_app
from bson import ObjectId

from app.core.repositories.user_repository import UserRepository
from ..repositories.impact_score_repository import ImpactScoreRepository
from ..repositories.leaderboard_repository import LeaderboardRepository
from ..models.leaderboard import Leaderboard


class PrivacyService:
    """
    Service for managing user privacy settings related to leaderboards and impact scores

    Handles:
    - Leaderboard participation opt-in/opt-out
    - Impact score visibility settings
    - Data anonymization for privacy-conscious users
    - GDPR compliance for leaderboard data
    """

    def __init__(self):
        self.user_repo = UserRepository()
        self.impact_score_repo = ImpactScoreRepository()
        self.leaderboard_repo = LeaderboardRepository()

    def update_leaderboard_participation(self, user_id: str,
                                       participation: bool) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Update user's leaderboard participation setting

        Args:
            user_id: User ID
            participation: Whether user wants to participate in leaderboards

        Returns:
            Tuple of (success, message, privacy_settings)
        """
        try:
            # Get user
            user = self.user_repo.find_by_id(user_id)
            if not user:
                return False, "User not found", {}

            # Update preferences
            preferences = user.get('preferences', {})
            if 'privacy' not in preferences:
                preferences['privacy'] = {}

            old_participation = preferences['privacy'].get('leaderboard_participation', True)
            preferences['privacy']['leaderboard_participation'] = participation

            # Update user
            success = self.user_repo.update_by_id(user_id, {'preferences': preferences})
            if not success:
                return False, "Failed to update privacy settings", {}

            # If user opted out and was previously opted in, remove from leaderboards
            if old_participation and not participation:
                self._remove_user_from_all_leaderboards(user_id)
                current_app.logger.info(f"User {user_id} opted out of leaderboards - removed from all leaderboards")

            # If user opted in and was previously opted out, add to leaderboards
            elif not old_participation and participation:
                self._add_user_to_relevant_leaderboards(user_id)
                current_app.logger.info(f"User {user_id} opted into leaderboards - added to relevant leaderboards")

            privacy_settings = self.get_user_privacy_settings(user_id)[2]

            return True, "Privacy settings updated successfully", privacy_settings

        except Exception as e:
            current_app.logger.error(f"Error updating leaderboard participation for user {user_id}: {str(e)}")
            return False, "Failed to update privacy settings", {}

    def update_impact_score_visibility(self, user_id: str,
                                     visibility: str) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Update user's impact score visibility setting

        Args:
            user_id: User ID
            visibility: Visibility level ('public', 'friends', 'private')

        Returns:
            Tuple of (success, message, privacy_settings)
        """
        try:
            valid_levels = ['public', 'friends', 'private']
            if visibility not in valid_levels:
                return False, f"Invalid visibility level. Must be one of: {valid_levels}", {}

            # Get user
            user = self.user_repo.find_by_id(user_id)
            if not user:
                return False, "User not found", {}

            # Update preferences
            preferences = user.get('preferences', {})
            if 'privacy' not in preferences:
                preferences['privacy'] = {}

            preferences['privacy']['impact_score_visibility'] = visibility

            # Update user
            success = self.user_repo.update_by_id(user_id, {'preferences': preferences})
            if not success:
                return False, "Failed to update visibility settings", {}

            # If set to private, remove from public leaderboards
            if visibility == 'private':
                self._remove_user_from_public_leaderboards(user_id)

            privacy_settings = self.get_user_privacy_settings(user_id)[2]

            return True, "Visibility settings updated successfully", privacy_settings

        except Exception as e:
            current_app.logger.error(f"Error updating impact score visibility for user {user_id}: {str(e)}")
            return False, "Failed to update visibility settings", {}

    def get_user_privacy_settings(self, user_id: str) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Get user's current privacy settings

        Args:
            user_id: User ID

        Returns:
            Tuple of (success, message, privacy_settings)
        """
        try:
            user = self.user_repo.find_by_id(user_id)
            if not user:
                return False, "User not found", {}

            preferences = user.get('preferences', {})
            privacy = preferences.get('privacy', {})

            settings = {
                'leaderboard_participation': privacy.get('leaderboard_participation', True),
                'impact_score_visibility': privacy.get('impact_score_visibility', 'public'),
                'profile_visibility': privacy.get('profile_visibility', 'public'),
                'stats_sharing': privacy.get('stats_sharing', True),
                'activity_visibility': privacy.get('activity_visibility', 'friends'),
                'contact_permissions': privacy.get('contact_permissions', 'friends')
            }

            return True, "Privacy settings retrieved successfully", settings

        except Exception as e:
            current_app.logger.error(f"Error getting privacy settings for user {user_id}: {str(e)}")
            return False, "Failed to retrieve privacy settings", {}

    def get_anonymized_user_data(self, user_id: str, requester_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get user data with appropriate anonymization based on privacy settings

        Args:
            user_id: User whose data is being requested
            requester_id: User making the request (None for public view)

        Returns:
            Dict with appropriately anonymized user data
        """
        try:
            user = self.user_repo.find_by_id(user_id)
            if not user:
                return {}

            privacy_settings = self.get_user_privacy_settings(user_id)[2]
            if not privacy_settings:
                return {}

            # Determine relationship between users if requester is specified
            is_friend = False
            if requester_id and requester_id != user_id:
                is_friend = self._check_friendship(user_id, requester_id)

            # Get base anonymized data
            anonymized_data = {
                'user_id': user_id,
                'display_name': self._get_display_name(user, privacy_settings, is_friend, requester_id == user_id),
                'avatar_url': None,  # Would be implemented with actual avatar system
                'is_anonymous': True
            }

            # Add additional data based on privacy settings
            visibility = privacy_settings.get('impact_score_visibility', 'public')
            profile_visibility = privacy_settings.get('profile_visibility', 'public')

            # Public data
            if visibility == 'public' or (visibility == 'friends' and is_friend) or requester_id == user_id:
                anonymized_data['is_anonymous'] = False

                if privacy_settings.get('stats_sharing', True):
                    impact_score = self.impact_score_repo.find_by_user_id(user_id)
                    if impact_score:
                        anonymized_data['impact_score'] = impact_score.impact_score

            # Profile data
            if profile_visibility == 'public' or (profile_visibility == 'friends' and is_friend) or requester_id == user_id:
                social_profile = user.get('social_profile', {})
                anonymized_data['member_since'] = user.get('created_at')
                anonymized_data['privacy_level'] = profile_visibility

            return anonymized_data

        except Exception as e:
            current_app.logger.error(f"Error getting anonymized data for user {user_id}: {str(e)}")
            return {}

    def bulk_apply_privacy_settings(self, user_ids: List[str]) -> Tuple[bool, str, Dict[str, int]]:
        """
        Bulk apply privacy settings for multiple users (admin function)

        Args:
            user_ids: List of user IDs to process

        Returns:
            Tuple of (success, message, processing_stats)
        """
        try:
            processed = 0
            errors = 0

            for user_id in user_ids:
                try:
                    # Get user's current privacy settings
                    success, message, settings = self.get_user_privacy_settings(user_id)
                    if not success:
                        errors += 1
                        continue

                    # Apply leaderboard participation setting
                    participation = settings.get('leaderboard_participation', True)
                    if not participation:
                        self._remove_user_from_all_leaderboards(user_id)

                    # Apply visibility settings
                    visibility = settings.get('impact_score_visibility', 'public')
                    if visibility == 'private':
                        self._remove_user_from_public_leaderboards(user_id)

                    processed += 1

                except Exception as e:
                    current_app.logger.error(f"Error processing privacy settings for user {user_id}: {str(e)}")
                    errors += 1

            stats = {
                'total_users': len(user_ids),
                'processed': processed,
                'errors': errors
            }

            return True, f"Bulk privacy application completed", stats

        except Exception as e:
            current_app.logger.error(f"Error in bulk privacy settings application: {str(e)}")
            return False, "Bulk privacy application failed", {'processed': 0, 'errors': len(user_ids)}

    def export_user_leaderboard_data(self, user_id: str) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Export user's leaderboard data for GDPR compliance

        Args:
            user_id: User ID

        Returns:
            Tuple of (success, message, exported_data)
        """
        try:
            # Get impact score
            impact_score = self.impact_score_repo.find_by_user_id(user_id)
            impact_data = impact_score.to_response_dict() if impact_score else None

            # Get leaderboard positions
            positions = self.leaderboard_repo.get_user_leaderboard_positions(user_id)

            # Get privacy settings
            privacy_success, privacy_message, privacy_settings = self.get_user_privacy_settings(user_id)

            exported_data = {
                'user_id': user_id,
                'export_timestamp': current_app.logger.handlers[0].formatter.formatTime(current_app.logger.makeRecord("", 0, "", 0, "", (), None)) if current_app.logger.handlers else None,
                'impact_score_data': impact_data,
                'leaderboard_positions': positions,
                'privacy_settings': privacy_settings if privacy_success else {},
                'data_processing_consent': True  # Assumed if they're using the service
            }

            return True, "User data exported successfully", exported_data

        except Exception as e:
            current_app.logger.error(f"Error exporting user data for {user_id}: {str(e)}")
            return False, "Failed to export user data", {}

    def delete_user_leaderboard_data(self, user_id: str) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Delete user's leaderboard data for GDPR right to erasure

        Args:
            user_id: User ID

        Returns:
            Tuple of (success, message, deletion_stats)
        """
        try:
            deletion_stats = {
                'impact_score_deleted': False,
                'leaderboard_entries_removed': 0,
                'privacy_settings_cleared': False
            }

            # Delete impact score
            if self.impact_score_repo.delete_user_score(user_id):
                deletion_stats['impact_score_deleted'] = True

            # Remove from all leaderboards
            removed_count = self._remove_user_from_all_leaderboards(user_id)
            deletion_stats['leaderboard_entries_removed'] = removed_count

            # Clear privacy settings (reset to defaults)
            user = self.user_repo.find_by_id(user_id)
            if user:
                preferences = user.get('preferences', {})
                if 'privacy' in preferences:
                    # Reset privacy settings to defaults
                    preferences['privacy'] = {
                        'leaderboard_participation': False,  # Opt-out by default after deletion
                        'impact_score_visibility': 'private',
                        'profile_visibility': 'private',
                        'stats_sharing': False,
                        'activity_visibility': 'private',
                        'contact_permissions': 'friends'
                    }

                    if self.user_repo.update_by_id(user_id, {'preferences': preferences}):
                        deletion_stats['privacy_settings_cleared'] = True

            return True, "User leaderboard data deleted successfully", deletion_stats

        except Exception as e:
            current_app.logger.error(f"Error deleting user leaderboard data for {user_id}: {str(e)}")
            return False, "Failed to delete user data", {}

    # Private helper methods

    def _remove_user_from_all_leaderboards(self, user_id: str) -> int:
        """Remove user from all leaderboards"""
        removed_count = 0
        try:
            for leaderboard_type in Leaderboard.VALID_TYPES:
                for period in Leaderboard.VALID_PERIODS:
                    if self.leaderboard_repo.remove_entry_from_leaderboard(
                        leaderboard_type, period, user_id
                    ):
                        removed_count += 1
        except Exception as e:
            current_app.logger.error(f"Error removing user {user_id} from leaderboards: {str(e)}")

        return removed_count

    def _remove_user_from_public_leaderboards(self, user_id: str) -> int:
        """Remove user from public leaderboards only"""
        removed_count = 0
        try:
            # Remove from public leaderboards (not friends leaderboard)
            public_types = [t for t in Leaderboard.VALID_TYPES if t != Leaderboard.FRIENDS_CIRCLE]

            for leaderboard_type in public_types:
                for period in Leaderboard.VALID_PERIODS:
                    if self.leaderboard_repo.remove_entry_from_leaderboard(
                        leaderboard_type, period, user_id
                    ):
                        removed_count += 1
        except Exception as e:
            current_app.logger.error(f"Error removing user {user_id} from public leaderboards: {str(e)}")

        return removed_count

    def _add_user_to_relevant_leaderboards(self, user_id: str):
        """Add user back to relevant leaderboards when opting in"""
        try:
            # Get user's impact score
            impact_score = self.impact_score_repo.find_by_user_id(user_id)
            if not impact_score:
                return

            # This would trigger a full leaderboard refresh to include the user
            # For now, we'll just trigger a score update which will add them back
            from ..services.ranking_engine import RankingEngine
            ranking_engine = RankingEngine()
            ranking_engine.update_user_rankings(user_id)

        except Exception as e:
            current_app.logger.error(f"Error adding user {user_id} back to leaderboards: {str(e)}")

    def _check_friendship(self, user_id: str, requester_id: str) -> bool:
        """Check if two users are friends"""
        try:
            from app.social.repositories.relationship_repository import RelationshipRepository
            relationship_repo = RelationshipRepository()

            # Check if friendship exists
            friendship = relationship_repo.find_relationship(user_id, requester_id, 'friend')
            return friendship and friendship.is_accepted()

        except Exception as e:
            current_app.logger.error(f"Error checking friendship between {user_id} and {requester_id}: {str(e)}")
            return False

    def _get_display_name(self, user: Dict[str, Any], privacy_settings: Dict[str, Any],
                         is_friend: bool, is_self: bool) -> str:
        """Get appropriate display name based on privacy settings"""
        try:
            if is_self:
                return user.get('social_profile', {}).get('display_name', user.get('first_name', 'You'))

            profile_visibility = privacy_settings.get('profile_visibility', 'public')

            if profile_visibility == 'public' or (profile_visibility == 'friends' and is_friend):
                return user.get('social_profile', {}).get('display_name', user.get('first_name', 'Anonymous User'))
            else:
                return 'Anonymous User'

        except Exception:
            return 'Anonymous User'