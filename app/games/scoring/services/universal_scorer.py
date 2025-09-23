from typing import Dict, Any, Optional, List
from flask import current_app
from datetime import datetime
import math

class UniversalScorer:
    """Universal scoring system for normalizing scores across different games"""

    def __init__(self):
        # Game difficulty multipliers
        self.difficulty_multipliers = {
            "easy": 0.8,
            "medium": 1.0,
            "hard": 1.3,
            "expert": 1.6
        }

        # Game type base scores
        self.game_type_bases = {
            "puzzle": 100,
            "action": 150,
            "strategy": 200,
            "arcade": 120,
            "simulation": 180
        }

    def normalize_score(self, game_type: str, raw_score: int, difficulty: str,
                       session_time_seconds: int, game_id: str = None) -> float:
        """
        Normalize a raw score to a universal scoring system.

        Args:
            game_type: Type of game (puzzle, action, strategy, etc.)
            raw_score: The raw score from the game
            difficulty: Game difficulty level
            session_time_seconds: Time spent playing in seconds
            game_id: Optional specific game ID for game-specific adjustments

        Returns:
            float: Normalized score
        """
        try:
            # Base score calculation
            base_score = self.game_type_bases.get(game_type, 100)

            # Apply difficulty multiplier
            difficulty_mult = self.difficulty_multipliers.get(difficulty, 1.0)

            # Time-based adjustment (optimal time around 5-15 minutes)
            time_minutes = session_time_seconds / 60
            time_factor = self._calculate_time_factor(time_minutes)

            # Score scaling (logarithmic to prevent extreme scores)
            score_factor = math.log10(max(1, raw_score)) / 4  # Scale down large scores

            # Game-specific adjustments
            game_adjustment = self._get_game_specific_adjustment(game_id, raw_score)

            # Final calculation
            normalized_score = (
                base_score *
                difficulty_mult *
                time_factor *
                score_factor *
                game_adjustment
            )

            return round(normalized_score, 2)

        except Exception as e:
            current_app.logger.error(f"Score normalization error: {str(e)}")
            return float(raw_score / 10)  # Fallback normalization

    def calculate_elo_change(self, player_elo: int, opponent_elo: int,
                           result: str, k_factor: int = 32) -> int:
        """
        Calculate ELO rating change based on match result.

        Args:
            player_elo: Player's current ELO rating
            opponent_elo: Opponent's current ELO rating
            result: Match result ('win', 'loss', 'draw')
            k_factor: K-factor for ELO calculation

        Returns:
            int: ELO change (positive or negative)
        """
        try:
            # Expected score calculation
            expected_score = 1 / (1 + 10 ** ((opponent_elo - player_elo) / 400))

            # Actual score based on result
            if result == "win":
                actual_score = 1.0
            elif result == "loss":
                actual_score = 0.0
            elif result == "draw":
                actual_score = 0.5
            else:
                return 0  # Invalid result

            # ELO change calculation
            elo_change = k_factor * (actual_score - expected_score)

            return round(elo_change)

        except Exception as e:
            current_app.logger.error(f"ELO calculation error: {str(e)}")
            return 0

    def get_percentile_rank(self, user_score: float, all_scores: List[float]) -> float:
        """
        Calculate percentile rank for a user's score.

        Args:
            user_score: The user's score
            all_scores: List of all scores to compare against

        Returns:
            float: Percentile rank (0-100)
        """
        if not all_scores:
            return 50.0  # Default to 50th percentile if no data

        scores_below = sum(1 for score in all_scores if score < user_score)
        percentile = (scores_below / len(all_scores)) * 100

        return round(percentile, 2)

    def calculate_team_contribution(self, individual_score: float, team_size: int,
                                  difficulty_bonus: float = 1.0) -> float:
        """
        Calculate how much an individual score contributes to team score.

        Args:
            individual_score: Player's individual normalized score
            team_size: Size of the team
            difficulty_bonus: Additional multiplier for difficulty

        Returns:
            float: Team contribution points
        """
        # Base contribution is individual score
        base_contribution = individual_score

        # Team size factor (larger teams get slightly less per person)
        team_factor = max(0.7, 1 - (team_size - 1) * 0.05)

        # Apply bonuses
        contribution = base_contribution * team_factor * difficulty_bonus

        return round(contribution, 2)

    def calculate_challenge_bonus(self, challenge_type: str, participants: int,
                                duration_minutes: int, position: int = None) -> float:
        """
        Calculate bonus points for challenge participation.

        Args:
            challenge_type: Type of challenge ('1v1', 'NvN', 'cross_game')
            participants: Number of participants
            duration_minutes: Challenge duration
            position: Final position (1st, 2nd, etc.)

        Returns:
            float: Bonus multiplier
        """
        base_bonus = 1.0

        # Challenge type bonuses
        type_bonuses = {
            "1v1": 1.2,
            "NvN": 1.5,
            "cross_game": 1.8
        }
        base_bonus *= type_bonuses.get(challenge_type, 1.0)

        # Participant count bonus (more competitive = higher bonus)
        if participants >= 8:
            base_bonus *= 1.4
        elif participants >= 4:
            base_bonus *= 1.2

        # Duration bonus (longer challenges get slight bonus)
        if duration_minutes >= 30:
            base_bonus *= 1.1

        # Position bonus
        if position:
            if position == 1:
                base_bonus *= 2.0  # Winner bonus
            elif position == 2:
                base_bonus *= 1.5  # Runner-up bonus
            elif position == 3:
                base_bonus *= 1.2  # Third place bonus

        return round(base_bonus, 2)

    def aggregate_team_score(self, team_contributions: List[float],
                           scoring_method: str = "weighted") -> float:
        """
        Aggregate individual contributions into team score.

        Args:
            team_contributions: List of individual contribution scores
            scoring_method: Method for aggregation ('sum', 'average', 'weighted')

        Returns:
            float: Aggregated team score
        """
        if not team_contributions:
            return 0.0

        if scoring_method == "sum":
            return sum(team_contributions)
        elif scoring_method == "average":
            return sum(team_contributions) / len(team_contributions)
        elif scoring_method == "weighted":
            # Weighted average giving more weight to higher scores
            sorted_contributions = sorted(team_contributions, reverse=True)
            weights = [1.0 / (i + 1) for i in range(len(sorted_contributions))]
            weighted_sum = sum(score * weight for score, weight in zip(sorted_contributions, weights))
            total_weight = sum(weights)
            return weighted_sum / total_weight if total_weight > 0 else 0.0

        return sum(team_contributions)  # Default to sum

    def calculate_streak_bonus(self, streak_count: int, streak_type: str = "win") -> float:
        """
        Calculate bonus for winning/playing streaks.

        Args:
            streak_count: Number of consecutive wins/games
            streak_type: Type of streak ('win', 'play', 'daily')

        Returns:
            float: Streak bonus multiplier
        """
        if streak_count <= 1:
            return 1.0

        base_multipliers = {
            "win": 0.1,    # 10% per win
            "play": 0.05,  # 5% per game
            "daily": 0.15  # 15% per day
        }

        multiplier = base_multipliers.get(streak_type, 0.05)
        max_bonus = 2.0  # Cap at 200% bonus

        bonus = 1.0 + (streak_count - 1) * multiplier
        return min(bonus, max_bonus)

    def _calculate_time_factor(self, time_minutes: float) -> float:
        """Calculate time-based scoring factor"""
        if time_minutes <= 1:
            return 0.5  # Very short sessions get penalized
        elif time_minutes <= 5:
            return 0.8  # Short sessions
        elif time_minutes <= 15:
            return 1.0  # Optimal time range
        elif time_minutes <= 30:
            return 0.9  # Slightly longer sessions
        elif time_minutes <= 60:
            return 0.8  # Long sessions
        else:
            return 0.7  # Very long sessions get diminishing returns

    def _get_game_specific_adjustment(self, game_id: str, raw_score: int) -> float:
        """Get game-specific score adjustments"""
        # This could be expanded with a database of game-specific rules
        game_adjustments = {
            # Example adjustments for specific games
            "tetris": lambda score: min(2.0, score / 10000),  # Tetris scores can be very high
            "snake": lambda score: max(0.5, score / 100),     # Snake scores are usually lower
        }

        if game_id in game_adjustments:
            try:
                return game_adjustments[game_id](raw_score)
            except:
                return 1.0

        return 1.0  # Default: no adjustment

    def get_score_distribution_stats(self, scores: List[float]) -> Dict[str, float]:
        """Get statistical distribution of scores"""
        if not scores:
            return {}

        scores_sorted = sorted(scores)
        n = len(scores_sorted)

        return {
            "mean": sum(scores) / n,
            "median": scores_sorted[n // 2] if n % 2 == 1 else (scores_sorted[n // 2 - 1] + scores_sorted[n // 2]) / 2,
            "min": min(scores),
            "max": max(scores),
            "std_dev": self._calculate_std_dev(scores),
            "q1": scores_sorted[n // 4],
            "q3": scores_sorted[3 * n // 4]
        }

    def _calculate_std_dev(self, scores: List[float]) -> float:
        """Calculate standard deviation"""
        if len(scores) < 2:
            return 0.0

        mean = sum(scores) / len(scores)
        variance = sum((x - mean) ** 2 for x in scores) / (len(scores) - 1)
        return math.sqrt(variance)