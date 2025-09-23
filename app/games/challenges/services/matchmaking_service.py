from typing import Tuple, Optional, Dict, Any, List
from flask import current_app
from datetime import datetime, timedelta
import random

from ..repositories.challenge_repository import ChallengeRepository
from ..repositories.challenge_participant_repository import ChallengeParticipantRepository
from ..models.challenge import Challenge
from ..models.challenge_participant import ChallengeParticipant
from ...repositories.game_repository import GameRepository
from ...repositories.game_session_repository import GameSessionRepository

class MatchmakingService:
    """Service for automatic matchmaking and opponent finding"""

    def __init__(self):
        self.challenge_repository = ChallengeRepository()
        self.participant_repository = ChallengeParticipantRepository()
        self.game_repository = GameRepository()
        self.session_repository = GameSessionRepository()

    def find_opponent(self, user_id: str, game_id: str, challenge_type: str = "1v1",
                     skill_range: int = 100) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Find an opponent for automatic matchmaking.

        Args:
            user_id: User ID looking for opponent
            game_id: Game ID to play
            challenge_type: Type of challenge (1v1, NvN)
            skill_range: Skill level range for matching

        Returns:
            Tuple[bool, str, Optional[Dict[str, Any]]]: (success, message, data)
        """
        try:
            # Validate game
            game = self.game_repository.get_game_by_id(game_id)
            if not game:
                return False, "GAME_NOT_FOUND", None

            if not game.is_active:
                return False, "GAME_NOT_ACTIVE", None

            # First, try to find existing public challenges to join
            existing_challenges = self.challenge_repository.find_matchmaking_candidates(
                user_id, game_id, challenge_type
            )

            if existing_challenges:
                # Join the oldest available challenge
                challenge = existing_challenges[0]

                # Use the challenge service to join
                from .challenge_service import ChallengeService
                challenge_service = ChallengeService()
                success, message, data = challenge_service.join_public_challenge(user_id, challenge.challenge_id)

                if success:
                    current_app.logger.info(f"Matchmaking: User {user_id} joined existing challenge {challenge.challenge_id}")
                    return True, "OPPONENT_FOUND_EXISTING_CHALLENGE", {
                        "challenge": challenge.to_api_dict(),
                        "matchmaking_type": "joined_existing"
                    }

            # If no existing challenges, try to find potential opponents
            potential_opponents = self._find_potential_opponents(user_id, game_id, skill_range)

            if potential_opponents:
                # Create a challenge with a random opponent
                opponent = random.choice(potential_opponents)

                from .challenge_service import ChallengeService
                challenge_service = ChallengeService()

                if challenge_type == "1v1":
                    success, message, data = challenge_service.create_1v1_challenge(
                        challenger_id=user_id,
                        challenged_id=opponent["user_id"],
                        game_id=game_id,
                        timeout_minutes=10,  # Shorter timeout for matchmaking
                        game_config={"matchmaking": True}
                    )
                else:
                    # Create public NvN challenge
                    success, message, data = challenge_service.create_nvn_challenge(
                        challenger_id=user_id,
                        max_participants=4,  # Default NvN size
                        game_id=game_id,
                        min_participants=2,
                        timeout_minutes=15,
                        game_config={"matchmaking": True}
                    )

                if success:
                    current_app.logger.info(f"Matchmaking: Created challenge for user {user_id}")
                    return True, "CHALLENGE_CREATED_FOR_MATCHMAKING", {
                        **data,
                        "matchmaking_type": "created_new",
                        "matched_with": opponent if challenge_type == "1v1" else None
                    }

            # No opponents available
            return False, "NO_OPPONENTS_AVAILABLE", {
                "suggestions": self._get_matchmaking_suggestions(user_id, game_id)
            }

        except Exception as e:
            current_app.logger.error(f"Matchmaking failed for user {user_id}: {str(e)}")
            return False, "MATCHMAKING_FAILED", None

    def find_quick_match(self, user_id: str, game_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Find a quick match - either join existing or create new public challenge.

        Args:
            user_id: User ID looking for quick match
            game_id: Game ID to play

        Returns:
            Tuple[bool, str, Optional[Dict[str, Any]]]: (success, message, data)
        """
        try:
            # Look for public challenges that need players
            public_challenges = self.challenge_repository.get_public_challenges(game_id, "pending", 10)

            # Filter challenges that have space and aren't expired
            available_challenges = []
            for challenge in public_challenges:
                if (not challenge.is_expired() and
                    len(challenge.get_all_participant_ids()) < challenge.max_participants and
                    not challenge.is_participant(user_id)):
                    available_challenges.append(challenge)

            if available_challenges:
                # Join the challenge that's closest to starting
                best_challenge = max(available_challenges,
                                   key=lambda c: len(c.get_all_participant_ids()))

                from .challenge_service import ChallengeService
                challenge_service = ChallengeService()
                success, message, data = challenge_service.join_public_challenge(user_id, best_challenge.challenge_id)

                if success:
                    return True, "QUICK_MATCH_JOINED", data

            # Create new public challenge if none available
            from .challenge_service import ChallengeService
            challenge_service = ChallengeService()
            success, message, data = challenge_service.create_nvn_challenge(
                challenger_id=user_id,
                max_participants=4,
                game_id=game_id,
                min_participants=2,
                timeout_minutes=10,
                game_config={"quick_match": True}
            )

            if success:
                return True, "QUICK_MATCH_CREATED", data

            return False, "QUICK_MATCH_FAILED", None

        except Exception as e:
            current_app.logger.error(f"Quick match failed for user {user_id}: {str(e)}")
            return False, "QUICK_MATCH_FAILED", None

    def get_recommended_opponents(self, user_id: str, game_id: str, limit: int = 10) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Get recommended opponents for a user.

        Args:
            user_id: User ID
            game_id: Game ID
            limit: Maximum number of recommendations

        Returns:
            Tuple[bool, str, Optional[Dict[str, Any]]]: (success, message, data)
        """
        try:
            recommendations = self._find_potential_opponents(user_id, game_id, skill_range=200, limit=limit)

            # Add more details to recommendations
            detailed_recommendations = []
            for opponent in recommendations:
                opponent_stats = self.participant_repository.get_user_challenge_stats(opponent["user_id"])
                opponent_info = {
                    **opponent,
                    "stats": opponent_stats,
                    "compatibility_score": self._calculate_compatibility_score(user_id, opponent["user_id"], game_id)
                }
                detailed_recommendations.append(opponent_info)

            # Sort by compatibility score
            detailed_recommendations.sort(key=lambda x: x["compatibility_score"], reverse=True)

            return True, "RECOMMENDATIONS_RETRIEVED", {
                "recommendations": detailed_recommendations,
                "count": len(detailed_recommendations)
            }

        except Exception as e:
            current_app.logger.error(f"Failed to get recommendations for user {user_id}: {str(e)}")
            return False, "FAILED_TO_GET_RECOMMENDATIONS", None

    def get_matchmaking_statistics(self, user_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Get matchmaking statistics for a user."""
        try:
            user_stats = self.participant_repository.get_user_challenge_stats(user_id)

            # Get recent matchmaking activity
            recent_challenges = self.challenge_repository.get_challenges_by_user(user_id, limit=20)
            matchmaking_challenges = [
                c for c in recent_challenges
                if c.game_config.get("matchmaking") or c.game_config.get("quick_match")
            ]

            stats = {
                "user_stats": user_stats,
                "recent_matchmaking_challenges": len(matchmaking_challenges),
                "matchmaking_success_rate": self._calculate_matchmaking_success_rate(user_id),
                "preferred_games": self._get_preferred_games(user_id),
                "average_waiting_time": self._calculate_average_waiting_time(user_id)
            }

            return True, "MATCHMAKING_STATISTICS_RETRIEVED", stats

        except Exception as e:
            current_app.logger.error(f"Failed to get matchmaking statistics: {str(e)}")
            return False, "FAILED_TO_GET_STATISTICS", None

    def _find_potential_opponents(self, user_id: str, game_id: str, skill_range: int = 100, limit: int = 10) -> List[Dict[str, Any]]:
        """Find potential opponents based on skill level and activity"""
        try:
            # Get user's skill level (simplified - could be based on ELO rating)
            user_stats = self.participant_repository.get_user_challenge_stats(user_id)
            user_skill = user_stats.get("average_score", 0)

            # Find users who have played this game recently
            recent_sessions = self.session_repository.get_recent_sessions_by_game(game_id, days=7, limit=100)

            potential_opponents = []
            for session in recent_sessions:
                if session.user_id == user_id:
                    continue

                # Get opponent stats
                opponent_stats = self.participant_repository.get_user_challenge_stats(session.user_id)
                opponent_skill = opponent_stats.get("average_score", 0)

                # Check skill range
                if abs(opponent_skill - user_skill) <= skill_range:
                    potential_opponents.append({
                        "user_id": session.user_id,
                        "skill_level": opponent_skill,
                        "skill_difference": abs(opponent_skill - user_skill),
                        "last_played": session.created_at.isoformat(),
                        "games_played": opponent_stats.get("total_challenges", 0),
                        "win_rate": opponent_stats.get("win_rate", 0)
                    })

            # Sort by skill similarity and recent activity
            potential_opponents.sort(key=lambda x: (x["skill_difference"], x["games_played"]))

            return potential_opponents[:limit]

        except Exception as e:
            current_app.logger.error(f"Failed to find potential opponents: {str(e)}")
            return []

    def _calculate_compatibility_score(self, user1_id: str, user2_id: str, game_id: str) -> float:
        """Calculate compatibility score between two users"""
        try:
            user1_stats = self.participant_repository.get_user_challenge_stats(user1_id)
            user2_stats = self.participant_repository.get_user_challenge_stats(user2_id)

            # Base score from skill similarity (0-50 points)
            skill_diff = abs(user1_stats.get("average_score", 0) - user2_stats.get("average_score", 0))
            skill_score = max(0, 50 - skill_diff / 10)

            # Activity level similarity (0-25 points)
            activity_diff = abs(user1_stats.get("total_challenges", 0) - user2_stats.get("total_challenges", 0))
            activity_score = max(0, 25 - activity_diff / 5)

            # Response time compatibility (0-25 points)
            response_diff = abs(
                user1_stats.get("average_response_time_seconds", 30) -
                user2_stats.get("average_response_time_seconds", 30)
            )
            response_score = max(0, 25 - response_diff / 2)

            total_score = skill_score + activity_score + response_score
            return min(100, total_score)

        except Exception:
            return 50.0  # Default neutral score

    def _get_matchmaking_suggestions(self, user_id: str, game_id: str) -> Dict[str, Any]:
        """Get suggestions when no opponents are available"""
        return {
            "create_public_challenge": "Create a public challenge that others can join",
            "try_different_game": "Try matchmaking with a different game",
            "invite_friends": "Invite friends directly for a private challenge",
            "check_back_later": "More players may be available later"
        }

    def _calculate_matchmaking_success_rate(self, user_id: str) -> float:
        """Calculate user's matchmaking success rate"""
        try:
            challenges = self.challenge_repository.get_challenges_by_user(user_id, limit=50)
            matchmaking_challenges = [
                c for c in challenges
                if c.game_config.get("matchmaking") or c.game_config.get("quick_match")
            ]

            if not matchmaking_challenges:
                return 0.0

            successful = len([c for c in matchmaking_challenges if c.status == "completed"])
            return (successful / len(matchmaking_challenges)) * 100

        except Exception:
            return 0.0

    def _get_preferred_games(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's preferred games based on activity"""
        try:
            challenges = self.challenge_repository.get_challenges_by_user(user_id, limit=100)

            game_counts = {}
            for challenge in challenges:
                game_id = challenge.game_id
                if game_id not in game_counts:
                    game_counts[game_id] = 0
                game_counts[game_id] += 1

            # Sort by frequency
            sorted_games = sorted(game_counts.items(), key=lambda x: x[1], reverse=True)

            return [
                {"game_id": game_id, "play_count": count}
                for game_id, count in sorted_games[:5]
            ]

        except Exception:
            return []

    def _calculate_average_waiting_time(self, user_id: str) -> float:
        """Calculate average waiting time for matchmaking"""
        try:
            challenges = self.challenge_repository.get_challenges_by_user(user_id, limit=20)
            matchmaking_challenges = [
                c for c in challenges
                if (c.game_config.get("matchmaking") or c.game_config.get("quick_match")) and c.started_at
            ]

            if not matchmaking_challenges:
                return 0.0

            total_wait_time = 0
            for challenge in matchmaking_challenges:
                wait_time = (challenge.started_at - challenge.created_at).total_seconds()
                total_wait_time += wait_time

            return total_wait_time / len(matchmaking_challenges)

        except Exception:
            return 0.0