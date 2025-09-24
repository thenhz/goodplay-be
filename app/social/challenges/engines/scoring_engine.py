from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import math
from flask import current_app

from app.social.challenges.models.social_challenge import SocialChallenge
from app.social.challenges.models.challenge_participant import ChallengeParticipant


class ScoringEngine:
    """Engine for calculating scores, rankings, and performance metrics in social challenges"""

    def __init__(self):
        pass

    def calculate_participant_score(self, challenge: SocialChallenge, participant: ChallengeParticipant,
                                   raw_metrics: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
        """Calculate final score for participant including all bonuses and multipliers"""
        try:
            # Get base score from raw metrics
            base_score = self._calculate_base_score(challenge, raw_metrics)

            # Calculate various bonus components
            bonuses = {
                "social_engagement": self._calculate_social_engagement_bonus(participant),
                "completion_bonus": self._calculate_completion_bonus(challenge, participant),
                "time_bonus": self._calculate_time_bonus(challenge, participant, raw_metrics),
                "consistency_bonus": self._calculate_consistency_bonus(participant),
                "difficulty_bonus": self._calculate_difficulty_bonus(challenge),
                "collaboration_bonus": self._calculate_collaboration_bonus(challenge, participant)
            }

            # Apply multipliers
            multipliers = {
                "social_multiplier": self._get_social_multiplier(participant),
                "difficulty_multiplier": challenge.rules.difficulty_multiplier,
                "challenge_type_multiplier": self._get_challenge_type_multiplier(challenge),
                "streak_multiplier": self._get_streak_multiplier(participant)
            }

            # Calculate final score
            total_bonus = sum(bonuses.values())
            score_with_bonuses = base_score + total_bonus

            # Apply multipliers
            final_multiplier = 1.0
            for multiplier in multipliers.values():
                final_multiplier *= multiplier

            final_score = score_with_bonuses * final_multiplier

            # Ensure non-negative score
            final_score = max(0.0, final_score)

            scoring_breakdown = {
                "base_score": base_score,
                "bonuses": bonuses,
                "total_bonus": total_bonus,
                "multipliers": multipliers,
                "final_multiplier": final_multiplier,
                "final_score": final_score
            }

            return final_score, scoring_breakdown

        except Exception as e:
            current_app.logger.error(f"Error calculating participant score: {str(e)}")
            return 0.0, {"error": str(e)}

    def calculate_challenge_rankings(self, challenge: SocialChallenge,
                                   participants_scores: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Calculate rankings for all participants in challenge"""
        try:
            # Sort participants by score based on scoring method
            if challenge.rules.scoring_method == "lowest":
                # For challenges where lower is better (e.g., speed runs)
                sorted_participants = sorted(participants_scores, key=lambda x: x.get("final_score", float('inf')))
            elif challenge.rules.scoring_method == "collective":
                # For collective challenges, everyone gets same rank if target is met
                total_collective = sum(p.get("final_score", 0) for p in participants_scores)
                target_met = total_collective >= challenge.rules.target_value

                for participant in participants_scores:
                    participant["rank"] = 1 if target_met else len(participants_scores)
                    participant["collective_total"] = total_collective
                    participant["target_met"] = target_met

                return participants_scores
            else:
                # Default: highest score wins
                sorted_participants = sorted(participants_scores, key=lambda x: x.get("final_score", 0), reverse=True)

            # Assign ranks handling ties
            current_rank = 1
            previous_score = None
            participants_with_rank = []

            for i, participant in enumerate(sorted_participants):
                score = participant.get("final_score", 0)

                # Handle ties (same score gets same rank)
                if previous_score is not None and score != previous_score:
                    current_rank = i + 1

                participant["rank"] = current_rank
                participant["total_participants"] = len(sorted_participants)
                participants_with_rank.append(participant)

                previous_score = score

            return participants_with_rank

        except Exception as e:
            current_app.logger.error(f"Error calculating rankings: {str(e)}")
            return participants_scores

    def calculate_progress_percentage(self, challenge: SocialChallenge, current_value: float) -> float:
        """Calculate completion percentage for challenge progress"""
        if challenge.rules.target_value <= 0:
            return 0.0

        percentage = (current_value / challenge.rules.target_value) * 100
        return min(100.0, max(0.0, percentage))

    def calculate_social_engagement_score(self, participant: ChallengeParticipant) -> float:
        """Calculate social engagement score based on interactions"""
        # Weights for different interaction types
        cheer_weight = 2.0
        comment_weight = 5.0
        given_weight = 0.5  # Giving interactions worth less than receiving

        # Calculate raw engagement score
        received_score = (participant.cheers_received * cheer_weight +
                         participant.comments_received * comment_weight)

        given_score = (participant.cheers_given * cheer_weight * given_weight +
                      participant.comments_made * comment_weight * given_weight)

        total_score = received_score + given_score

        # Apply engagement bonus for balanced interaction
        if participant.cheers_given > 0 and participant.comments_made > 0:
            engagement_bonus = 1.5
            total_score *= engagement_bonus

        return round(total_score, 2)

    def calculate_leaderboard_movement(self, previous_rank: int, current_rank: int,
                                     total_participants: int) -> Dict[str, Any]:
        """Calculate leaderboard movement metrics"""
        if previous_rank == 0:  # First time ranking
            return {
                "movement": "new",
                "rank_change": 0,
                "percentile_change": 0,
                "movement_description": "New to leaderboard"
            }

        rank_change = previous_rank - current_rank  # Positive = improvement

        # Calculate percentile positions
        previous_percentile = ((total_participants - previous_rank + 1) / total_participants) * 100
        current_percentile = ((total_participants - current_rank + 1) / total_participants) * 100
        percentile_change = current_percentile - previous_percentile

        # Determine movement type
        if rank_change > 0:
            movement = "up"
            if rank_change >= 5:
                movement_description = f"Climbed {rank_change} positions!"
            else:
                movement_description = f"Moved up {rank_change} position(s)"
        elif rank_change < 0:
            movement = "down"
            movement_description = f"Dropped {abs(rank_change)} position(s)"
        else:
            movement = "stable"
            movement_description = "Position unchanged"

        return {
            "movement": movement,
            "rank_change": rank_change,
            "percentile_change": round(percentile_change, 1),
            "movement_description": movement_description,
            "previous_rank": previous_rank,
            "current_rank": current_rank
        }

    def calculate_achievement_thresholds(self, challenge: SocialChallenge) -> Dict[str, float]:
        """Calculate achievement thresholds for challenge milestones"""
        target = challenge.rules.target_value

        return {
            "bronze": target * 0.25,    # 25% of target
            "silver": target * 0.50,    # 50% of target
            "gold": target * 0.75,      # 75% of target
            "platinum": target * 1.0,   # 100% of target
            "diamond": target * 1.25    # 125% of target (overachievement)
        }

    def get_performance_insights(self, challenge: SocialChallenge, participant: ChallengeParticipant,
                               scoring_breakdown: Dict[str, Any]) -> Dict[str, Any]:
        """Generate performance insights and suggestions for participant"""
        insights = {
            "strengths": [],
            "improvement_areas": [],
            "suggestions": [],
            "performance_level": "average"
        }

        # Analyze social engagement
        social_score = participant.social_score
        if social_score > 30:
            insights["strengths"].append("High social engagement")
        elif social_score < 10:
            insights["improvement_areas"].append("Limited social interaction")
            insights["suggestions"].append("Try cheering for other participants or leaving encouraging comments")

        # Analyze completion rate
        completion_rate = participant.completion_percentage
        if completion_rate >= 90:
            insights["strengths"].append("Excellent completion rate")
            insights["performance_level"] = "excellent"
        elif completion_rate >= 70:
            insights["strengths"].append("Good progress towards goal")
            insights["performance_level"] = "good"
        elif completion_rate < 50:
            insights["improvement_areas"].append("Below halfway to goal")
            insights["suggestions"].append("Consider breaking down the challenge into smaller daily tasks")
            insights["performance_level"] = "needs_improvement"

        # Analyze consistency
        if participant.progress_updates > 0:
            days_active = participant.get_days_participated()
            updates_per_day = participant.progress_updates / max(1, days_active)

            if updates_per_day >= 1:
                insights["strengths"].append("Consistent daily progress")
            elif updates_per_day < 0.5:
                insights["improvement_areas"].append("Inconsistent progress updates")
                insights["suggestions"].append("Try to log progress daily to maintain momentum")

        # Challenge-specific insights
        if challenge.challenge_type == "social_engagement":
            if participant.friends_joined > 0:
                insights["strengths"].append("Successfully brought friends into the community")
            else:
                insights["suggestions"].append("Consider inviting friends to join your challenges")

        return insights

    def _calculate_base_score(self, challenge: SocialChallenge, raw_metrics: Dict[str, Any]) -> float:
        """Calculate base score from raw metrics"""
        primary_metric = raw_metrics.get("primary_value", 0)

        # Normalize based on target value
        if challenge.rules.target_value > 0:
            normalized_score = (primary_metric / challenge.rules.target_value) * 100
        else:
            normalized_score = primary_metric

        return max(0.0, normalized_score)

    def _calculate_social_engagement_bonus(self, participant: ChallengeParticipant) -> float:
        """Calculate bonus points for social engagement"""
        return participant.social_score * 0.5  # 50% of social score as bonus

    def _calculate_completion_bonus(self, challenge: SocialChallenge, participant: ChallengeParticipant) -> float:
        """Calculate bonus for completion percentage"""
        if participant.completion_percentage >= 100:
            return 25.0  # Full completion bonus
        elif participant.completion_percentage >= 75:
            return 15.0  # Partial completion bonus
        return 0.0

    def _calculate_time_bonus(self, challenge: SocialChallenge, participant: ChallengeParticipant,
                            raw_metrics: Dict[str, Any]) -> float:
        """Calculate bonus based on timing (early completion, consistency)"""
        time_bonus = 0.0

        # Early completion bonus
        if participant.completion_percentage >= 100:
            total_duration = (challenge.end_date - challenge.start_date).total_seconds()
            participant_duration = (participant.completed_at or datetime.utcnow() - participant.joined_at).total_seconds()

            if participant_duration < total_duration * 0.5:  # Completed in first half
                time_bonus += 20.0
            elif participant_duration < total_duration * 0.75:  # Completed in first 3/4
                time_bonus += 10.0

        return time_bonus

    def _calculate_consistency_bonus(self, participant: ChallengeParticipant) -> float:
        """Calculate bonus for consistent participation"""
        if participant.progress_updates == 0:
            return 0.0

        days_participated = participant.get_days_participated()
        updates_per_day = participant.progress_updates / max(1, days_participated)

        if updates_per_day >= 1:
            return 15.0  # Daily updates
        elif updates_per_day >= 0.5:
            return 8.0   # Regular updates

        return 0.0

    def _calculate_difficulty_bonus(self, challenge: SocialChallenge) -> float:
        """Calculate bonus based on challenge difficulty"""
        difficulty_bonuses = {
            1: 0.0,    # Easy
            2: 5.0,    # Medium
            3: 10.0,   # Hard
            4: 20.0,   # Very Hard
            5: 30.0    # Extreme
        }
        return difficulty_bonuses.get(challenge.difficulty_level, 0.0)

    def _calculate_collaboration_bonus(self, challenge: SocialChallenge, participant: ChallengeParticipant) -> float:
        """Calculate bonus for collaborative behavior"""
        if challenge.challenge_type == "impact_challenge" and challenge.rules.scoring_method == "collective":
            # Higher bonus for collective challenges
            return participant.social_score * 0.3

        return 0.0

    def _get_social_multiplier(self, participant: ChallengeParticipant) -> float:
        """Get multiplier based on social engagement level"""
        engagement_level = participant.get_engagement_level()

        multipliers = {
            "none": 1.0,
            "low": 1.1,
            "medium": 1.2,
            "high": 1.3,
            "very_high": 1.5
        }

        return multipliers.get(engagement_level, 1.0)

    def _get_challenge_type_multiplier(self, challenge: SocialChallenge) -> float:
        """Get multiplier based on challenge type"""
        type_multipliers = {
            "gaming_social": 1.0,
            "social_engagement": 1.2,  # Higher value for social challenges
            "impact_challenge": 1.3    # Highest value for impact challenges
        }

        return type_multipliers.get(challenge.challenge_type, 1.0)

    def _get_streak_multiplier(self, participant: ChallengeParticipant) -> float:
        """Get multiplier based on participation streak"""
        if participant.streak_days >= 7:
            return 1.2  # Weekly streak bonus
        elif participant.streak_days >= 3:
            return 1.1  # Short streak bonus

        return 1.0

    def calculate_elo_rating_change(self, participant_rating: float, opponent_ratings: List[float],
                                  participant_rank: int, total_participants: int) -> float:
        """Calculate ELO rating change for competitive challenges"""
        if not opponent_ratings or total_participants < 2:
            return 0.0

        # Calculate expected score based on ratings
        average_opponent_rating = sum(opponent_ratings) / len(opponent_ratings)
        expected_score = 1 / (1 + math.pow(10, (average_opponent_rating - participant_rating) / 400))

        # Calculate actual score based on rank
        actual_score = (total_participants - participant_rank) / (total_participants - 1)

        # K-factor (rating volatility)
        k_factor = 32 if participant_rating < 1200 else 16

        # Calculate rating change
        rating_change = k_factor * (actual_score - expected_score)

        return round(rating_change, 2)