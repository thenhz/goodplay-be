from typing import Dict, Any, List
from flask import current_app
from ..services.progress_tracker import ProgressTracker


class GameTriggers:
    """
    Trigger handlers for game-related achievement events
    """

    def __init__(self):
        self.progress_tracker = ProgressTracker()

    def on_game_session_completed(self, user_id: str, session_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Trigger when a game session is completed

        Args:
            user_id: ID of the user
            session_data: Game session data

        Returns:
            List[Dict]: List of unlocked achievements
        """
        try:
            current_app.logger.info(f"Processing game session completion for user {user_id}")

            # Track the game session completion
            success, message, unlocked_achievements = self.progress_tracker.track_game_session_completion(
                user_id, session_data
            )

            if success:
                current_app.logger.info(f"Game session tracked: {message}")
                return unlocked_achievements
            else:
                current_app.logger.error(f"Error tracking game session: {message}")
                return []

        except Exception as e:
            current_app.logger.error(f"Error in game session trigger: {str(e)}")
            return []

    def on_high_score_achieved(self, user_id: str, score_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Trigger when a high score is achieved

        Args:
            user_id: ID of the user
            score_data: Score achievement data (score, game_id, rank, etc.)

        Returns:
            List[Dict]: List of unlocked achievements
        """
        try:
            current_app.logger.info(f"Processing high score achievement for user {user_id}")

            # Add score-specific event data
            event_data = {
                **score_data,
                'event_type': 'high_score'
            }

            success, message, unlocked_achievements = self.progress_tracker.track_game_session_completion(
                user_id, event_data
            )

            if success:
                current_app.logger.info(f"High score tracked: {message}")
                return unlocked_achievements
            else:
                current_app.logger.error(f"Error tracking high score: {message}")
                return []

        except Exception as e:
            current_app.logger.error(f"Error in high score trigger: {str(e)}")
            return []

    def on_game_mastery(self, user_id: str, mastery_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Trigger when a user masters a game (plays multiple times, achieves consistency)

        Args:
            user_id: ID of the user
            mastery_data: Game mastery data

        Returns:
            List[Dict]: List of unlocked achievements
        """
        try:
            current_app.logger.info(f"Processing game mastery for user {user_id}")

            # Add mastery-specific event data
            event_data = {
                **mastery_data,
                'event_type': 'game_mastery'
            }

            success, message, unlocked_achievements = self.progress_tracker.track_game_session_completion(
                user_id, event_data
            )

            return unlocked_achievements if success else []

        except Exception as e:
            current_app.logger.error(f"Error in game mastery trigger: {str(e)}")
            return []

    def on_tournament_participation(self, user_id: str, tournament_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Trigger when a user participates in a tournament

        Args:
            user_id: ID of the user
            tournament_data: Tournament participation data

        Returns:
            List[Dict]: List of unlocked achievements
        """
        try:
            current_app.logger.info(f"Processing tournament participation for user {user_id}")

            # Add tournament-specific event data
            event_data = {
                **tournament_data,
                'event_type': 'tournament_participation'
            }

            success, message, unlocked_achievements = self.progress_tracker.track_game_session_completion(
                user_id, event_data
            )

            return unlocked_achievements if success else []

        except Exception as e:
            current_app.logger.error(f"Error in tournament participation trigger: {str(e)}")
            return []

    def on_tournament_victory(self, user_id: str, victory_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Trigger when a user wins a tournament

        Args:
            user_id: ID of the user
            victory_data: Tournament victory data

        Returns:
            List[Dict]: List of unlocked achievements
        """
        try:
            current_app.logger.info(f"Processing tournament victory for user {user_id}")

            # Add victory-specific event data
            event_data = {
                **victory_data,
                'event_type': 'tournament_victory',
                'score': victory_data.get('final_score', 0)
            }

            success, message, unlocked_achievements = self.progress_tracker.track_game_session_completion(
                user_id, event_data
            )

            return unlocked_achievements if success else []

        except Exception as e:
            current_app.logger.error(f"Error in tournament victory trigger: {str(e)}")
            return []

    def on_challenge_completed(self, user_id: str, challenge_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Trigger when a user completes a challenge

        Args:
            user_id: ID of the user
            challenge_data: Challenge completion data

        Returns:
            List[Dict]: List of unlocked achievements
        """
        try:
            current_app.logger.info(f"Processing challenge completion for user {user_id}")

            # Add challenge-specific event data
            event_data = {
                **challenge_data,
                'event_type': 'challenge_completed'
            }

            success, message, unlocked_achievements = self.progress_tracker.track_game_session_completion(
                user_id, event_data
            )

            return unlocked_achievements if success else []

        except Exception as e:
            current_app.logger.error(f"Error in challenge completion trigger: {str(e)}")
            return []

    def on_streak_milestone(self, user_id: str, streak_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Trigger when a user reaches a playing streak milestone

        Args:
            user_id: ID of the user
            streak_data: Streak milestone data

        Returns:
            List[Dict]: List of unlocked achievements
        """
        try:
            current_app.logger.info(f"Processing streak milestone for user {user_id}")

            # Add streak-specific event data
            event_data = {
                **streak_data,
                'event_type': 'streak_milestone',
                'consecutive_days': streak_data.get('consecutive_days', 1)
            }

            success, message, unlocked_achievements = self.progress_tracker.track_game_session_completion(
                user_id, event_data
            )

            return unlocked_achievements if success else []

        except Exception as e:
            current_app.logger.error(f"Error in streak milestone trigger: {str(e)}")
            return []

    def on_multiple_games_played(self, user_id: str, diversity_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Trigger when a user plays multiple different games

        Args:
            user_id: ID of the user
            diversity_data: Game diversity data

        Returns:
            List[Dict]: List of unlocked achievements
        """
        try:
            current_app.logger.info(f"Processing game diversity for user {user_id}")

            # Add diversity-specific event data
            event_data = {
                **diversity_data,
                'event_type': 'game_diversity',
                'games_played_count': diversity_data.get('unique_games_count', 1)
            }

            success, message, unlocked_achievements = self.progress_tracker.track_game_session_completion(
                user_id, event_data
            )

            return unlocked_achievements if success else []

        except Exception as e:
            current_app.logger.error(f"Error in game diversity trigger: {str(e)}")
            return []


# Global instance for easy import
game_triggers = GameTriggers()