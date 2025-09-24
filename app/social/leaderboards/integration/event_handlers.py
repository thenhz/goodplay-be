"""
Event handlers for real-time impact score updates

These handlers are called when specific events occur in the system,
triggering automatic impact score recalculation and leaderboard updates.
"""

from typing import Dict, Any, Optional
from flask import current_app
from ..services.ranking_engine import RankingEngine


# Initialize ranking engine for event handling
ranking_engine = RankingEngine()


def handle_game_session_complete(user_id: str, session_data: Dict[str, Any]) -> bool:
    """
    Handle game session completion event

    Args:
        user_id: User who completed the session
        session_data: Session completion data

    Returns:
        bool: True if impact score was updated successfully
    """
    try:
        current_app.logger.info(f"Handling game session complete for user {user_id}")

        # Extract relevant session data
        activity_data = {
            'session_id': session_data.get('session_id'),
            'game_id': session_data.get('game_id'),
            'play_duration_ms': session_data.get('play_duration_ms', 0),
            'final_score': session_data.get('final_score', 0),
            'achievements_unlocked': session_data.get('achievements_unlocked', []),
            'session_type': session_data.get('session_type', 'normal')
        }

        # Trigger impact score update
        success, message = ranking_engine.trigger_user_score_update(
            user_id, 'gaming', activity_data
        )

        if not success:
            current_app.logger.warning(f"Failed to update impact score after game session: {message}")
            return False

        current_app.logger.debug(f"Impact score updated for user {user_id} after game session")
        return True

    except Exception as e:
        current_app.logger.error(f"Error handling game session complete for user {user_id}: {str(e)}")
        return False


def handle_social_activity(user_id: str, activity_type: str, activity_data: Dict[str, Any]) -> bool:
    """
    Handle social activity events

    Args:
        user_id: User who performed the activity
        activity_type: Type of social activity
        activity_data: Activity-specific data

    Returns:
        bool: True if impact score was updated successfully
    """
    try:
        current_app.logger.info(f"Handling social activity '{activity_type}' for user {user_id}")

        # Map activity types to impact calculation relevance
        relevant_activities = [
            'friend_request_sent',
            'friend_request_accepted',
            'challenge_sent',
            'challenge_completed',
            'social_share',
            'community_interaction'
        ]

        if activity_type not in relevant_activities:
            current_app.logger.debug(f"Social activity '{activity_type}' not relevant for impact score")
            return True

        # Prepare activity data for impact calculation
        impact_activity_data = {
            'activity_type': activity_type,
            'target_user_id': activity_data.get('target_user_id'),
            'interaction_score': activity_data.get('interaction_score', 1),
            'timestamp': activity_data.get('timestamp')
        }

        # Trigger impact score update
        success, message = ranking_engine.trigger_user_score_update(
            user_id, 'social', impact_activity_data
        )

        if not success:
            current_app.logger.warning(f"Failed to update impact score after social activity: {message}")
            return False

        current_app.logger.debug(f"Impact score updated for user {user_id} after social activity")
        return True

    except Exception as e:
        current_app.logger.error(f"Error handling social activity for user {user_id}: {str(e)}")
        return False


def handle_donation_activity(user_id: str, donation_data: Dict[str, Any]) -> bool:
    """
    Handle donation activity events

    Args:
        user_id: User who made the donation
        donation_data: Donation transaction data

    Returns:
        bool: True if impact score was updated successfully
    """
    try:
        current_app.logger.info(f"Handling donation activity for user {user_id}")

        # Extract relevant donation data
        activity_data = {
            'donation_amount': donation_data.get('amount', 0),
            'onlus_id': donation_data.get('onlus_id'),
            'transaction_type': donation_data.get('transaction_type', 'regular'),
            'is_recurring': donation_data.get('is_recurring', False),
            'special_event': donation_data.get('special_event'),
            'currency': donation_data.get('currency', 'EUR')
        }

        # Trigger impact score update (donation has highest weight)
        success, message = ranking_engine.trigger_user_score_update(
            user_id, 'donation', activity_data
        )

        if not success:
            current_app.logger.warning(f"Failed to update impact score after donation: {message}")
            return False

        current_app.logger.info(f"Impact score updated for user {user_id} after donation of {activity_data['donation_amount']}")
        return True

    except Exception as e:
        current_app.logger.error(f"Error handling donation activity for user {user_id}: {str(e)}")
        return False


def handle_achievement_unlock(user_id: str, achievement_data: Dict[str, Any]) -> bool:
    """
    Handle achievement unlock events

    Args:
        user_id: User who unlocked the achievement
        achievement_data: Achievement data

    Returns:
        bool: True if impact score was updated successfully
    """
    try:
        current_app.logger.info(f"Handling achievement unlock for user {user_id}")

        # Extract achievement information
        activity_data = {
            'achievement_id': achievement_data.get('achievement_id'),
            'achievement_category': achievement_data.get('category', 'general'),
            'badge_rarity': achievement_data.get('badge_rarity', 'common'),
            'reward_credits': achievement_data.get('reward_credits', 0)
        }

        # Determine which component to update based on achievement category
        activity_type = 'gaming'  # Default
        if activity_data['achievement_category'] == 'social':
            activity_type = 'social'
        elif activity_data['achievement_category'] == 'impact':
            activity_type = 'donation'

        # Trigger impact score update
        success, message = ranking_engine.trigger_user_score_update(
            user_id, activity_type, activity_data
        )

        if not success:
            current_app.logger.warning(f"Failed to update impact score after achievement unlock: {message}")
            return False

        current_app.logger.debug(f"Impact score updated for user {user_id} after achievement unlock")
        return True

    except Exception as e:
        current_app.logger.error(f"Error handling achievement unlock for user {user_id}: {str(e)}")
        return False


def handle_user_login(user_id: str, login_data: Dict[str, Any]) -> bool:
    """
    Handle user login events (for consistency tracking)

    Args:
        user_id: User who logged in
        login_data: Login data

    Returns:
        bool: True if processed successfully
    """
    try:
        # Check if this is a new day login for consistency tracking
        from datetime import datetime, timedelta
        from ..repositories.impact_score_repository import ImpactScoreRepository

        impact_score_repo = ImpactScoreRepository()
        impact_score = impact_score_repo.find_by_user_id(user_id)

        if impact_score:
            last_calculated = impact_score.last_calculated
            now = datetime.utcnow()

            # If last calculation was more than 12 hours ago, update score
            if last_calculated and (now - last_calculated) > timedelta(hours=12):
                success, message = ranking_engine.trigger_user_score_update(
                    user_id, 'general', {'login_event': True}
                )

                if success:
                    current_app.logger.debug(f"Impact score refreshed for user {user_id} on login")

        return True

    except Exception as e:
        current_app.logger.error(f"Error handling user login for user {user_id}: {str(e)}")
        return False


def handle_weekly_reset() -> bool:
    """
    Handle weekly leaderboard reset event

    Returns:
        bool: True if reset was successful
    """
    try:
        current_app.logger.info("Handling weekly leaderboard reset")

        from ..services.leaderboard_service import LeaderboardService
        from ..models.leaderboard import Leaderboard

        leaderboard_service = LeaderboardService()

        # Clear weekly leaderboards
        weekly_types = [
            Leaderboard.WEEKLY_WARRIORS,
            # Add other weekly-specific leaderboards if needed
        ]

        reset_count = 0
        for leaderboard_type in weekly_types:
            from ..repositories.leaderboard_repository import LeaderboardRepository
            leaderboard_repo = LeaderboardRepository()

            success = leaderboard_repo.clear_leaderboard_entries(leaderboard_type, 'weekly')
            if success:
                reset_count += 1

        current_app.logger.info(f"Weekly reset completed: {reset_count} leaderboards reset")
        return True

    except Exception as e:
        current_app.logger.error(f"Error in weekly leaderboard reset: {str(e)}")
        return False


def handle_tournament_result(tournament_data: Dict[str, Any]) -> bool:
    """
    Handle tournament completion events

    Args:
        tournament_data: Tournament result data

    Returns:
        bool: True if processed successfully
    """
    try:
        current_app.logger.info("Handling tournament completion")

        participants = tournament_data.get('participants', [])
        tournament_type = tournament_data.get('tournament_type', 'general')

        # Update impact scores for all participants
        updated_count = 0
        for participant in participants:
            user_id = participant.get('user_id')
            if not user_id:
                continue

            activity_data = {
                'tournament_id': tournament_data.get('tournament_id'),
                'tournament_type': tournament_type,
                'final_rank': participant.get('final_rank'),
                'score': participant.get('score', 0),
                'is_winner': participant.get('final_rank', 999) <= 3
            }

            success, message = ranking_engine.trigger_user_score_update(
                user_id, 'gaming', activity_data
            )

            if success:
                updated_count += 1

        current_app.logger.info(f"Tournament completion processed: {updated_count}/{len(participants)} participants updated")
        return True

    except Exception as e:
        current_app.logger.error(f"Error handling tournament result: {str(e)}")
        return False