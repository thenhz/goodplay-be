from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime, timedelta
from flask import current_app
from bson import ObjectId

from app.core.repositories.user_repository import UserRepository
from app.games.repositories.game_session_repository import GameSessionRepository
from app.social.repositories.relationship_repository import RelationshipRepository
from ..repositories.impact_score_repository import ImpactScoreRepository
from ..models.impact_score import ImpactScore


class ImpactCalculator:
    """
    Service for calculating user impact scores with weighted components

    Impact Score = (Gaming Activity × 0.3) + (Social Engagement × 0.2) + (Donation Impact × 0.5)

    Gaming Activity (30%):
    - Play time consistency
    - Game variety exploration
    - Tournament participation
    - Achievement completions

    Social Engagement (20%):
    - Friends interactions
    - Social challenges completed
    - Community contributions
    - Content sharing

    Donation Impact (50%):
    - Total donations amount
    - Number of ONLUS supported
    - Donation frequency/consistency
    - Special event participation
    """

    def __init__(self):
        self.impact_score_repo = ImpactScoreRepository()
        self.user_repo = UserRepository()
        self.game_session_repo = GameSessionRepository()
        self.relationship_repo = RelationshipRepository()

    def calculate_user_impact_score(self, user_id: str,
                                   force_recalculate: bool = False) -> Tuple[bool, str, Optional[ImpactScore]]:
        """
        Calculate comprehensive impact score for a user

        Args:
            user_id: User ID to calculate score for
            force_recalculate: Force recalculation even if score is recent

        Returns:
            Tuple of (success, message, impact_score)
        """
        try:
            # Check if user exists
            user = self.user_repo.find_by_id(user_id)
            if not user:
                return False, "User not found", None

            # Check if recalculation is needed
            existing_score = self.impact_score_repo.find_by_user_id(user_id)
            if existing_score and not force_recalculate and not existing_score.is_stale(hours=1):
                return True, "Impact score retrieved from cache", existing_score

            # Calculate each component
            gaming_score, gaming_details = self._calculate_gaming_component(user_id)
            social_score, social_details = self._calculate_social_component(user_id)
            donation_score, donation_details = self._calculate_donation_component(user_id)

            # Create or update impact score
            if existing_score:
                existing_score.update_component('gaming', gaming_score, gaming_details)
                existing_score.update_component('social', social_score, social_details)
                existing_score.update_component('donation', donation_score, donation_details)

                # Add to history
                existing_score.add_history_entry(existing_score.impact_score)

                # Update in database
                success = self.impact_score_repo.update_impact_score(existing_score)
                if not success:
                    return False, "Failed to update impact score", None

                current_app.logger.info(f"Updated impact score for user {user_id}: {existing_score.impact_score}")
                return True, "Impact score updated successfully", existing_score

            else:
                # Create new impact score
                impact_score = ImpactScore(
                    user_id=user_id,
                    gaming_component=gaming_score,
                    social_component=social_score,
                    donation_component=donation_score,
                    gaming_details=gaming_details,
                    social_details=social_details,
                    donation_details=donation_details
                )

                impact_score.calculate_total_score()
                impact_score.add_history_entry(impact_score.impact_score)

                # Save to database
                score_id = self.impact_score_repo.create_impact_score(impact_score)
                if not score_id:
                    return False, "Failed to create impact score", None

                current_app.logger.info(f"Created impact score for user {user_id}: {impact_score.impact_score}")
                return True, "Impact score calculated successfully", impact_score

        except Exception as e:
            current_app.logger.error(f"Error calculating impact score for user {user_id}: {str(e)}")
            return False, "Failed to calculate impact score", None

    def _calculate_gaming_component(self, user_id: str) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate gaming activity component (30% of total score)
        Max possible score: 1000.0

        Components:
        - Play time consistency (25%)
        - Game variety exploration (25%)
        - Tournament participation (25%)
        - Achievement completions (25%)
        """
        try:
            # Get user's gaming data
            user = self.user_repo.find_by_id(user_id)
            gaming_stats = user.get('gaming_stats', {})

            # Calculate sub-components
            play_time_score = self._calculate_play_time_score(user_id)
            variety_score = self._calculate_game_variety_score(user_id)
            tournament_score = self._calculate_tournament_score(user_id)
            achievement_score = self._calculate_achievement_score(user_id)

            # Calculate consistency multiplier based on recent activity
            consistency_multiplier = self._calculate_consistency_multiplier(user_id)

            # Weighted gaming score
            base_score = (play_time_score + variety_score + tournament_score + achievement_score) / 4
            final_score = min(base_score * consistency_multiplier, ImpactScore.MAX_GAMING_SCORE)

            details = {
                'play_time_score': play_time_score,
                'game_variety_score': variety_score,
                'tournament_score': tournament_score,
                'achievement_score': achievement_score,
                'consistency_multiplier': consistency_multiplier,
                'base_score': base_score
            }

            return round(final_score, 2), details

        except Exception as e:
            current_app.logger.error(f"Error calculating gaming component for user {user_id}: {str(e)}")
            return 0.0, {}

    def _calculate_social_component(self, user_id: str) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate social engagement component (20% of total score)
        Max possible score: 500.0

        Components:
        - Friends interactions (30%)
        - Social challenges completed (30%)
        - Community contributions (20%)
        - Content sharing (20%)
        """
        try:
            # Calculate sub-components
            friends_score = self._calculate_friends_score(user_id)
            challenges_score = self._calculate_social_challenges_score(user_id)
            community_score = self._calculate_community_contribution_score(user_id)
            sharing_score = self._calculate_content_sharing_score(user_id)

            # Calculate engagement multiplier
            engagement_multiplier = self._calculate_engagement_multiplier(user_id)

            # Weighted social score
            weighted_score = (
                friends_score * 0.30 +
                challenges_score * 0.30 +
                community_score * 0.20 +
                sharing_score * 0.20
            )

            final_score = min(weighted_score * engagement_multiplier, ImpactScore.MAX_SOCIAL_SCORE)

            details = {
                'friends_score': friends_score,
                'challenges_score': challenges_score,
                'community_score': community_score,
                'sharing_score': sharing_score,
                'engagement_multiplier': engagement_multiplier
            }

            return round(final_score, 2), details

        except Exception as e:
            current_app.logger.error(f"Error calculating social component for user {user_id}: {str(e)}")
            return 0.0, {}

    def _calculate_donation_component(self, user_id: str) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate donation impact component (50% of total score)
        Max possible score: 2000.0

        Components:
        - Total donations amount (40%)
        - Donation frequency/consistency (30%)
        - Number of ONLUS supported (20%)
        - Special event participation (10%)
        """
        try:
            # Get user's wallet and donation data
            user = self.user_repo.find_by_id(user_id)
            wallet_credits = user.get('wallet_credits', {})
            total_donated = wallet_credits.get('total_donated', 0.0)

            # Calculate sub-components
            amount_score = self._calculate_donation_amount_score(total_donated)
            frequency_score = self._calculate_donation_frequency_score(user_id)
            diversity_score = self._calculate_onlus_diversity_score(user_id)
            event_score = self._calculate_special_event_score(user_id)

            # Calculate consistency multiplier
            consistency_multiplier = self._calculate_donation_consistency_multiplier(user_id)

            # Weighted donation score
            weighted_score = (
                amount_score * 0.40 +
                frequency_score * 0.30 +
                diversity_score * 0.20 +
                event_score * 0.10
            )

            final_score = min(weighted_score * consistency_multiplier, ImpactScore.MAX_DONATION_SCORE)

            details = {
                'amount_score': amount_score,
                'frequency_score': frequency_score,
                'diversity_score': diversity_score,
                'event_score': event_score,
                'consistency_multiplier': consistency_multiplier,
                'total_donated': total_donated
            }

            return round(final_score, 2), details

        except Exception as e:
            current_app.logger.error(f"Error calculating donation component for user {user_id}: {str(e)}")
            return 0.0, {}

    # Gaming sub-component calculations
    def _calculate_play_time_score(self, user_id: str) -> float:
        """Calculate score based on play time consistency"""
        try:
            # Get recent gaming sessions (last 30 days)
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            sessions = self.game_session_repo.find_user_sessions_by_date_range(
                user_id, cutoff_date, datetime.utcnow()
            )

            if not sessions:
                return 0.0

            # Calculate total play time and consistency
            total_minutes = sum(session.get('play_duration_ms', 0) for session in sessions) / 60000
            unique_days = len(set(session['created_at'].date() for session in sessions))

            # Score based on total time and consistency
            time_score = min(total_minutes / 10, 200)  # Max 200 for 100+ minutes
            consistency_bonus = min(unique_days * 10, 50)  # Max 50 for 5+ days

            return time_score + consistency_bonus

        except Exception as e:
            current_app.logger.error(f"Error calculating play time score: {str(e)}")
            return 0.0

    def _calculate_game_variety_score(self, user_id: str) -> float:
        """Calculate score based on game variety"""
        try:
            # Get games played in last 30 days
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            sessions = self.game_session_repo.find_user_sessions_by_date_range(
                user_id, cutoff_date, datetime.utcnow()
            )

            if not sessions:
                return 0.0

            unique_games = len(set(session.get('game_id') for session in sessions if session.get('game_id')))

            # Score based on variety (max 250 for 10+ different games)
            return min(unique_games * 25, 250)

        except Exception as e:
            current_app.logger.error(f"Error calculating game variety score: {str(e)}")
            return 0.0

    def _calculate_tournament_score(self, user_id: str) -> float:
        """Calculate score based on tournament participation"""
        try:
            # This would integrate with the tournament system
            # For now, return a placeholder based on user's competitive activity
            user = self.user_repo.find_by_id(user_id)
            gaming_stats = user.get('gaming_stats', {})

            # Placeholder calculation based on activity
            total_games = gaming_stats.get('games_played', 0)
            tournament_bonus = min(total_games * 2, 250)  # Max 250

            return tournament_bonus

        except Exception as e:
            current_app.logger.error(f"Error calculating tournament score: {str(e)}")
            return 0.0

    def _calculate_achievement_score(self, user_id: str) -> float:
        """Calculate score based on achievements unlocked"""
        try:
            # This would integrate with the achievement system
            # For now, return a placeholder
            return 100.0  # Placeholder

        except Exception as e:
            current_app.logger.error(f"Error calculating achievement score: {str(e)}")
            return 0.0

    # Social sub-component calculations
    def _calculate_friends_score(self, user_id: str) -> float:
        """Calculate score based on friends and social interactions"""
        try:
            # Get accepted friendships
            friendships = self.relationship_repo.get_user_relationships(user_id, 'friend', 'accepted')
            friend_count = len(friendships)

            # Score based on friend count and engagement
            base_score = min(friend_count * 20, 300)  # Max 300 for 15+ friends

            # Activity bonus for recent interactions
            recent_activity = self._get_recent_social_activity(user_id)
            activity_bonus = min(recent_activity * 5, 100)

            return base_score + activity_bonus

        except Exception as e:
            current_app.logger.error(f"Error calculating friends score: {str(e)}")
            return 0.0

    def _calculate_social_challenges_score(self, user_id: str) -> float:
        """Calculate score based on social challenges completed"""
        try:
            # This would integrate with the challenges system
            return 150.0  # Placeholder

        except Exception as e:
            current_app.logger.error(f"Error calculating social challenges score: {str(e)}")
            return 0.0

    def _calculate_community_contribution_score(self, user_id: str) -> float:
        """Calculate score based on community contributions"""
        try:
            # This would track user contributions to community
            return 100.0  # Placeholder

        except Exception as e:
            current_app.logger.error(f"Error calculating community contribution score: {str(e)}")
            return 0.0

    def _calculate_content_sharing_score(self, user_id: str) -> float:
        """Calculate score based on content sharing activity"""
        try:
            # This would track sharing and social media activity
            return 75.0  # Placeholder

        except Exception as e:
            current_app.logger.error(f"Error calculating content sharing score: {str(e)}")
            return 0.0

    # Donation sub-component calculations
    def _calculate_donation_amount_score(self, total_donated: float) -> float:
        """Calculate score based on total donation amount"""
        try:
            # Logarithmic scale to prevent extreme scores for large donations
            if total_donated <= 0:
                return 0.0

            # Score increases logarithmically
            import math
            score = math.log10(total_donated + 1) * 100
            return min(score, 800)  # Max 800 points

        except Exception as e:
            current_app.logger.error(f"Error calculating donation amount score: {str(e)}")
            return 0.0

    def _calculate_donation_frequency_score(self, user_id: str) -> float:
        """Calculate score based on donation frequency"""
        try:
            # This would integrate with the donations system
            return 300.0  # Placeholder

        except Exception as e:
            current_app.logger.error(f"Error calculating donation frequency score: {str(e)}")
            return 0.0

    def _calculate_onlus_diversity_score(self, user_id: str) -> float:
        """Calculate score based on number of ONLUS supported"""
        try:
            # This would integrate with the ONLUS system
            return 200.0  # Placeholder

        except Exception as e:
            current_app.logger.error(f"Error calculating ONLUS diversity score: {str(e)}")
            return 0.0

    def _calculate_special_event_score(self, user_id: str) -> float:
        """Calculate score based on special event participation"""
        try:
            # This would track participation in special donation events
            return 100.0  # Placeholder

        except Exception as e:
            current_app.logger.error(f"Error calculating special event score: {str(e)}")
            return 0.0

    # Multiplier calculations
    def _calculate_consistency_multiplier(self, user_id: str) -> float:
        """Calculate multiplier based on gaming consistency"""
        try:
            # Get gaming activity in last 7 days
            cutoff_date = datetime.utcnow() - timedelta(days=7)
            recent_sessions = self.game_session_repo.find_user_sessions_by_date_range(
                user_id, cutoff_date, datetime.utcnow()
            )

            if not recent_sessions:
                return 0.8  # Penalty for inactivity

            # Calculate days with activity
            unique_days = len(set(session['created_at'].date() for session in recent_sessions))

            # Multiplier based on consistency (1.0 baseline, up to 1.2 bonus)
            multiplier = 1.0 + (unique_days - 1) * 0.05
            return min(multiplier, 1.2)

        except Exception as e:
            current_app.logger.error(f"Error calculating consistency multiplier: {str(e)}")
            return 1.0

    def _calculate_engagement_multiplier(self, user_id: str) -> float:
        """Calculate multiplier based on social engagement"""
        try:
            # Get recent social activity
            activity_count = self._get_recent_social_activity(user_id)

            # Multiplier based on engagement
            if activity_count >= 10:
                return 1.15
            elif activity_count >= 5:
                return 1.1
            elif activity_count >= 1:
                return 1.05
            else:
                return 0.95  # Small penalty for low engagement

        except Exception as e:
            current_app.logger.error(f"Error calculating engagement multiplier: {str(e)}")
            return 1.0

    def _calculate_donation_consistency_multiplier(self, user_id: str) -> float:
        """Calculate multiplier based on donation consistency"""
        try:
            # This would analyze donation patterns
            return 1.1  # Placeholder positive multiplier

        except Exception as e:
            current_app.logger.error(f"Error calculating donation consistency multiplier: {str(e)}")
            return 1.0

    # Helper methods
    def _get_recent_social_activity(self, user_id: str) -> int:
        """Get count of recent social activities"""
        try:
            # Count recent relationship activities, challenges, etc.
            cutoff_date = datetime.utcnow() - timedelta(days=7)

            # This would count various social activities
            activity_count = 0

            # Count recent friend requests/acceptances
            recent_relationships = self.relationship_repo.find_many({
                'user_id': ObjectId(user_id),
                'updated_at': {'$gte': cutoff_date}
            })
            activity_count += len(recent_relationships)

            return activity_count

        except Exception as e:
            current_app.logger.error(f"Error getting recent social activity: {str(e)}")
            return 0

    def recalculate_all_scores(self, batch_size: int = 100) -> Tuple[bool, str, Dict[str, int]]:
        """
        Recalculate impact scores for all users in batches

        Args:
            batch_size: Number of users to process per batch

        Returns:
            Tuple of (success, message, stats)
        """
        try:
            # Get all users
            all_users = self.user_repo.find_many({}, limit=None)
            total_users = len(all_users)

            if total_users == 0:
                return True, "No users to process", {'processed': 0, 'errors': 0}

            processed = 0
            errors = 0

            # Process in batches
            for i in range(0, total_users, batch_size):
                batch = all_users[i:i + batch_size]

                for user in batch:
                    success, message, score = self.calculate_user_impact_score(
                        str(user['_id']),
                        force_recalculate=True
                    )

                    if success:
                        processed += 1
                    else:
                        errors += 1
                        current_app.logger.warning(f"Failed to calculate score for user {user['_id']}: {message}")

                # Log progress
                current_app.logger.info(f"Processed batch {i//batch_size + 1}: {processed}/{total_users} users")

            stats = {
                'total_users': total_users,
                'processed': processed,
                'errors': errors
            }

            message = f"Recalculated scores for {processed}/{total_users} users"
            return True, message, stats

        except Exception as e:
            current_app.logger.error(f"Error in batch recalculation: {str(e)}")
            return False, "Batch recalculation failed", {'processed': 0, 'errors': 0}