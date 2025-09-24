from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime, timedelta
from flask import current_app

from app.core.repositories.user_repository import UserRepository
from app.social.repositories.relationship_repository import RelationshipRepository
from ..repositories.leaderboard_repository import LeaderboardRepository
from ..repositories.impact_score_repository import ImpactScoreRepository
from ..models.leaderboard import Leaderboard
from ..models.leaderboard_entry import LeaderboardEntry
from .impact_calculator import ImpactCalculator


class LeaderboardService:
    """
    Service for dynamic leaderboard management and ranking operations

    Handles:
    - Multiple leaderboard categories (Global Impact, Gaming Masters, etc.)
    - Time period management (daily, weekly, monthly, all-time)
    - Privacy controls and filtering
    - Pagination and ranking display
    """

    def __init__(self):
        self.leaderboard_repo = LeaderboardRepository()
        self.impact_score_repo = ImpactScoreRepository()
        self.user_repo = UserRepository()
        self.relationship_repo = RelationshipRepository()
        self.impact_calculator = ImpactCalculator()

    def get_leaderboard(self, leaderboard_type: str, period: str,
                       user_id: Optional[str] = None,
                       page: int = 1, per_page: int = 50) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Get leaderboard data with pagination

        Args:
            leaderboard_type: Type of leaderboard to retrieve
            period: Time period (daily, weekly, monthly, all_time)
            user_id: Optional user ID for personalized data
            page: Page number for pagination
            per_page: Entries per page

        Returns:
            Tuple of (success, message, leaderboard_data)
        """
        try:
            # Validate parameters
            if leaderboard_type not in Leaderboard.VALID_TYPES:
                return False, "Invalid leaderboard type", None

            if period not in Leaderboard.VALID_PERIODS:
                return False, "Invalid period", None

            # Get or create leaderboard
            leaderboard = self.leaderboard_repo.find_by_type_and_period(leaderboard_type, period)

            if not leaderboard:
                # Create new leaderboard
                leaderboard = Leaderboard(leaderboard_type, period)
                self.leaderboard_repo.create_leaderboard(leaderboard)

            # Check if leaderboard needs updating
            if leaderboard.is_stale(hours=1):
                success = self._update_leaderboard_data(leaderboard)
                if not success:
                    current_app.logger.warning(f"Failed to update leaderboard {leaderboard_type}_{period}")

            # Get user's position if specified
            user_position = None
            if user_id:
                user_position = self._get_user_position(leaderboard, user_id)

            # Get leaderboard response
            response_data = leaderboard.to_response_dict(
                include_entries=True,
                page=page,
                per_page=per_page
            )

            # Add user position data
            if user_position:
                response_data['user_position'] = user_position

            return True, "Leaderboard retrieved successfully", response_data

        except Exception as e:
            current_app.logger.error(f"Error getting leaderboard {leaderboard_type}_{period}: {str(e)}")
            return False, "Failed to retrieve leaderboard", None

    def get_friends_leaderboard(self, user_id: str, page: int = 1,
                               per_page: int = 50) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Get leaderboard showing user and their friends

        Args:
            user_id: User ID to get friends for
            page: Page number for pagination
            per_page: Entries per page

        Returns:
            Tuple of (success, message, leaderboard_data)
        """
        try:
            # Get user's friends
            friendships = self.relationship_repo.get_user_relationships(user_id, 'friend', 'accepted')
            friend_ids = [str(rel.target_user_id) for rel in friendships]

            # Get impact scores for user and friends
            friends_rankings = self.impact_score_repo.get_friends_rankings(user_id, friend_ids)

            if not friends_rankings:
                return True, "No friends data available", {
                    'leaderboard_type': 'friends_circle',
                    'period': 'all_time',
                    'entries': [],
                    'metadata': {'total_participants': 0}
                }

            # Create leaderboard entries
            entries = []
            for rank, ranking in enumerate(friends_rankings, 1):
                user_profile = ranking.get('user_profile', [{}])[0]
                display_name = user_profile.get('social_profile', {}).get('display_name')
                if not display_name:
                    display_name = user_profile.get('first_name', 'Unknown User')

                entry = LeaderboardEntry(
                    user_id=str(ranking['user_id']),
                    score=ranking['impact_score'],
                    rank=rank,
                    display_name=display_name,
                    user_data={
                        'avatar_url': None,
                        'level': 1,
                        'badge_count': 0,
                        'join_date': user_profile.get('created_at')
                    },
                    score_components={
                        'gaming': ranking.get('gaming_component', 0),
                        'social': ranking.get('social_component', 0),
                        'donation': ranking.get('donation_component', 0)
                    }
                )
                entries.append(entry)

            # Create temporary leaderboard
            leaderboard = Leaderboard('friends_circle', 'all_time', [])
            leaderboard.entries = entries
            leaderboard._update_metadata()

            # Get paginated response
            response_data = leaderboard.to_response_dict(
                include_entries=True,
                page=page,
                per_page=per_page
            )

            return True, "Friends leaderboard retrieved successfully", response_data

        except Exception as e:
            current_app.logger.error(f"Error getting friends leaderboard for user {user_id}: {str(e)}")
            return False, "Failed to retrieve friends leaderboard", None

    def get_user_leaderboard_summary(self, user_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Get user's positions across all leaderboards

        Args:
            user_id: User ID to get summary for

        Returns:
            Tuple of (success, message, summary_data)
        """
        try:
            # Get user's impact score
            impact_score = self.impact_score_repo.find_by_user_id(user_id)
            if not impact_score:
                return False, "User impact score not found", None

            # Get positions across leaderboards
            positions = self.leaderboard_repo.get_user_leaderboard_positions(user_id)

            # Get rank info
            rank_info = self.impact_score_repo.get_user_rank_info(user_id)

            summary = {
                'user_id': user_id,
                'impact_score': impact_score.to_response_dict(),
                'leaderboard_positions': positions,
                'global_ranking': rank_info,
                'achievements': {
                    'top_10_positions': len([p for p in positions if p['rank'] <= 10]),
                    'top_100_positions': len([p for p in positions if p['rank'] <= 100])
                }
            }

            return True, "User leaderboard summary retrieved successfully", summary

        except Exception as e:
            current_app.logger.error(f"Error getting leaderboard summary for user {user_id}: {str(e)}")
            return False, "Failed to retrieve leaderboard summary", None

    def get_leaderboard_statistics(self, leaderboard_type: str,
                                  period: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Get detailed statistics for a leaderboard

        Args:
            leaderboard_type: Type of leaderboard
            period: Time period

        Returns:
            Tuple of (success, message, statistics_data)
        """
        try:
            stats = self.leaderboard_repo.get_leaderboard_statistics(leaderboard_type, period)

            if not stats:
                return False, "Leaderboard statistics not found", None

            return True, "Leaderboard statistics retrieved successfully", stats

        except Exception as e:
            current_app.logger.error(f"Error getting statistics for {leaderboard_type}_{period}: {str(e)}")
            return False, "Failed to retrieve leaderboard statistics", None

    def update_user_privacy_settings(self, user_id: str,
                                    leaderboard_participation: bool) -> Tuple[bool, str]:
        """
        Update user's leaderboard privacy settings

        Args:
            user_id: User ID
            leaderboard_participation: Whether user participates in leaderboards

        Returns:
            Tuple of (success, message)
        """
        try:
            # Update user preferences
            user = self.user_repo.find_by_id(user_id)
            if not user:
                return False, "User not found"

            # Update preferences
            preferences = user.get('preferences', {})
            if 'privacy' not in preferences:
                preferences['privacy'] = {}

            preferences['privacy']['leaderboard_participation'] = leaderboard_participation

            success = self.user_repo.update_by_id(user_id, {'preferences': preferences})

            if not success:
                return False, "Failed to update privacy settings"

            # If user opted out, remove from all leaderboards
            if not leaderboard_participation:
                self._remove_user_from_all_leaderboards(user_id)

            return True, "Privacy settings updated successfully"

        except Exception as e:
            current_app.logger.error(f"Error updating privacy settings for user {user_id}: {str(e)}")
            return False, "Failed to update privacy settings"

    def refresh_all_leaderboards(self) -> Tuple[bool, str, Dict[str, int]]:
        """
        Refresh all leaderboards with current data

        Returns:
            Tuple of (success, message, refresh_stats)
        """
        try:
            refreshed = 0
            errors = 0

            # Get all leaderboard types and periods
            for leaderboard_type in Leaderboard.VALID_TYPES:
                for period in Leaderboard.VALID_PERIODS:
                    try:
                        # Get or create leaderboard
                        leaderboard = self.leaderboard_repo.find_by_type_and_period(
                            leaderboard_type, period
                        )

                        if not leaderboard:
                            leaderboard = Leaderboard(leaderboard_type, period)
                            self.leaderboard_repo.create_leaderboard(leaderboard)

                        # Update leaderboard data
                        success = self._update_leaderboard_data(leaderboard)
                        if success:
                            refreshed += 1
                        else:
                            errors += 1

                    except Exception as e:
                        current_app.logger.error(f"Error refreshing {leaderboard_type}_{period}: {str(e)}")
                        errors += 1

            stats = {
                'total_leaderboards': len(Leaderboard.VALID_TYPES) * len(Leaderboard.VALID_PERIODS),
                'refreshed': refreshed,
                'errors': errors
            }

            message = f"Refreshed {refreshed} leaderboards with {errors} errors"
            return True, message, stats

        except Exception as e:
            current_app.logger.error(f"Error in refresh all leaderboards: {str(e)}")
            return False, "Failed to refresh leaderboards", {'refreshed': 0, 'errors': 0}

    def _update_leaderboard_data(self, leaderboard: Leaderboard) -> bool:
        """Update leaderboard with current data"""
        try:
            # Clear existing entries
            leaderboard.clear_entries()

            # Get data based on leaderboard type
            if leaderboard.leaderboard_type == Leaderboard.GLOBAL_IMPACT:
                rankings = self._get_global_impact_rankings(leaderboard.period)
            elif leaderboard.leaderboard_type == Leaderboard.GAMING_MASTERS:
                rankings = self._get_gaming_masters_rankings(leaderboard.period)
            elif leaderboard.leaderboard_type == Leaderboard.SOCIAL_CHAMPIONS:
                rankings = self._get_social_champions_rankings(leaderboard.period)
            elif leaderboard.leaderboard_type == Leaderboard.DONATION_HEROES:
                rankings = self._get_donation_heroes_rankings(leaderboard.period)
            elif leaderboard.leaderboard_type == Leaderboard.WEEKLY_WARRIORS:
                rankings = self._get_weekly_warriors_rankings()
            else:
                return False

            # Add entries to leaderboard
            for rank, ranking in enumerate(rankings, 1):
                # Check privacy settings
                user_profile = ranking.get('user_profile', [{}])[0]
                privacy_settings = user_profile.get('preferences', {}).get('privacy', {})

                if not privacy_settings.get('leaderboard_participation', True):
                    continue  # Skip users who opted out

                display_name = user_profile.get('social_profile', {}).get('display_name')
                if not display_name:
                    display_name = user_profile.get('first_name', 'Unknown User')

                entry = LeaderboardEntry(
                    user_id=str(ranking['user_id']),
                    score=ranking.get('impact_score', ranking.get('score', 0)),
                    rank=rank,
                    display_name=display_name,
                    user_data={
                        'avatar_url': None,
                        'level': 1,
                        'badge_count': 0,
                        'join_date': user_profile.get('created_at')
                    },
                    score_components=self._get_score_components(ranking, leaderboard.leaderboard_type)
                )

                leaderboard.add_entry(entry)

            # Update leaderboard in database
            return self.leaderboard_repo.update_leaderboard(leaderboard)

        except Exception as e:
            current_app.logger.error(f"Error updating leaderboard data: {str(e)}")
            return False

    def _get_global_impact_rankings(self, period: str) -> List[Dict[str, Any]]:
        """Get rankings for global impact leaderboard"""
        if period == 'weekly':
            return self.impact_score_repo.get_weekly_active_users(weeks_back=1)
        else:
            return self.impact_score_repo.get_global_rankings(limit=1000)

    def _get_gaming_masters_rankings(self, period: str) -> List[Dict[str, Any]]:
        """Get rankings for gaming masters leaderboard"""
        return self.impact_score_repo.get_component_rankings('gaming', limit=1000)

    def _get_social_champions_rankings(self, period: str) -> List[Dict[str, Any]]:
        """Get rankings for social champions leaderboard"""
        return self.impact_score_repo.get_component_rankings('social', limit=1000)

    def _get_donation_heroes_rankings(self, period: str) -> List[Dict[str, Any]]:
        """Get rankings for donation heroes leaderboard"""
        return self.impact_score_repo.get_component_rankings('donation', limit=1000)

    def _get_weekly_warriors_rankings(self) -> List[Dict[str, Any]]:
        """Get rankings for weekly warriors leaderboard"""
        return self.impact_score_repo.get_weekly_active_users(weeks_back=1)

    def _get_score_components(self, ranking: Dict[str, Any],
                             leaderboard_type: str) -> Dict[str, Any]:
        """Get score components for leaderboard entry"""
        components = {}

        if leaderboard_type == Leaderboard.GLOBAL_IMPACT:
            components = {
                'gaming': ranking.get('gaming_component', 0),
                'social': ranking.get('social_component', 0),
                'donation': ranking.get('donation_component', 0)
            }
        elif leaderboard_type == Leaderboard.GAMING_MASTERS:
            components = ranking.get('gaming_details', {})
        elif leaderboard_type == Leaderboard.SOCIAL_CHAMPIONS:
            components = ranking.get('social_details', {})
        elif leaderboard_type == Leaderboard.DONATION_HEROES:
            components = ranking.get('donation_details', {})

        return components

    def _get_user_position(self, leaderboard: Leaderboard, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user's position in leaderboard"""
        entry = leaderboard.get_entry_by_user_id(user_id)
        if not entry:
            return None

        percentile = leaderboard.get_user_percentile(user_id)

        return {
            'rank': entry.rank,
            'score': entry.score,
            'percentile': percentile,
            'rank_display': entry.get_rank_suffix(),
            'is_top_performer': entry.is_top_performer()
        }

    def _remove_user_from_all_leaderboards(self, user_id: str):
        """Remove user from all leaderboards (privacy opt-out)"""
        try:
            for leaderboard_type in Leaderboard.VALID_TYPES:
                for period in Leaderboard.VALID_PERIODS:
                    self.leaderboard_repo.remove_entry_from_leaderboard(
                        leaderboard_type, period, user_id
                    )

            current_app.logger.info(f"Removed user {user_id} from all leaderboards")

        except Exception as e:
            current_app.logger.error(f"Error removing user {user_id} from leaderboards: {str(e)}")