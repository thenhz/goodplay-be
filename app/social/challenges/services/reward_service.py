from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from flask import current_app

from app.social.challenges.models.social_challenge import SocialChallenge
from app.social.challenges.models.challenge_participant import ChallengeParticipant
from app.social.challenges.models.challenge_result import ChallengeResult
from app.social.challenges.repositories.challenge_participant_repository import ChallengeParticipantRepository
from app.social.challenges.repositories.challenge_result_repository import ChallengeResultRepository


class RewardService:
    """Service for managing challenge rewards, achievements, and recognition"""

    def __init__(self):
        self.participant_repo = ChallengeParticipantRepository()
        self.result_repo = ChallengeResultRepository()

    def calculate_challenge_rewards(self, challenge: SocialChallenge,
                                  results: List[Dict[str, Any]]) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Calculate and distribute rewards for completed challenge"""
        try:
            total_participants = len(results)
            if total_participants == 0:
                return True, "No participants to reward", {"total_rewarded": 0}

            reward_summary = {
                "total_participants": total_participants,
                "winners": [],
                "participants_rewarded": 0,
                "total_credits_distributed": 0,
                "badges_awarded": [],
                "special_achievements": []
            }

            # Sort results by rank to identify winners
            results.sort(key=lambda x: x.get("rank", float('inf')))

            for result in results:
                user_id = result.get("user_id")
                rank = result.get("rank", 0)
                is_winner = rank == 1 or user_id in challenge.winner_ids

                # Calculate base rewards
                base_credits = self._calculate_base_credits(challenge, rank, is_winner)

                # Get participant for social bonuses
                participant = self.participant_repo.get_participant(challenge.challenge_id, user_id)
                if not participant:
                    continue

                # Calculate total rewards with multipliers
                reward_calculation = self._calculate_total_rewards(
                    challenge, participant, base_credits, is_winner
                )

                # Award credits
                final_credits = reward_calculation["total_credits"]
                badges_earned = reward_calculation["badges_earned"]

                # Update participant rewards
                success = self.participant_repo.claim_rewards(
                    challenge.challenge_id, user_id, final_credits, badges_earned
                )

                if success:
                    reward_summary["participants_rewarded"] += 1
                    reward_summary["total_credits_distributed"] += final_credits
                    reward_summary["badges_awarded"].extend(badges_earned)

                    if is_winner:
                        reward_summary["winners"].append({
                            "user_id": user_id,
                            "rank": rank,
                            "credits_earned": final_credits,
                            "badges_earned": badges_earned
                        })

                # Check for special achievements
                special_achievements = self._check_special_achievements(challenge, participant, result)
                if special_achievements:
                    reward_summary["special_achievements"].extend(special_achievements)

            current_app.logger.info(f"Rewards distributed for challenge {challenge.challenge_id}: {reward_summary['participants_rewarded']} participants, {reward_summary['total_credits_distributed']} credits")

            return True, "Rewards calculated and distributed", reward_summary

        except Exception as e:
            current_app.logger.error(f"Error calculating challenge rewards: {str(e)}")
            return False, "Failed to calculate rewards", None

    def award_milestone_achievement(self, challenge: SocialChallenge, participant: ChallengeParticipant,
                                  milestone_data: Dict[str, Any]) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Award achievement for reaching milestone"""
        try:
            milestone_type = milestone_data.get("type", "general")
            milestone_value = milestone_data.get("value", 0)

            # Calculate milestone rewards
            milestone_credits = self._calculate_milestone_credits(challenge, milestone_type, milestone_value)
            milestone_badges = self._get_milestone_badges(challenge, milestone_type, milestone_value)

            # Update participant
            success = self.participant_repo.record_milestone(
                challenge.challenge_id, participant.user_id, milestone_data
            )

            if not success:
                return False, "Failed to record milestone", None

            # Award credits and badges if significant milestone
            if milestone_credits > 0 or milestone_badges:
                participant.credits_earned += milestone_credits
                participant.badges_earned.extend(milestone_badges)

                # Update in database
                self.participant_repo.update_participant(
                    challenge.challenge_id, participant.user_id, {
                        "credits_earned": participant.credits_earned,
                        "badges_earned": participant.badges_earned
                    }
                )

            achievement_data = {
                "milestone_type": milestone_type,
                "milestone_value": milestone_value,
                "credits_awarded": milestone_credits,
                "badges_awarded": milestone_badges,
                "total_milestones": participant.milestones_reached + 1
            }

            current_app.logger.info(f"Milestone achievement awarded to {participant.user_id} in {challenge.challenge_id}")

            return True, "Milestone achievement awarded", achievement_data

        except Exception as e:
            current_app.logger.error(f"Error awarding milestone achievement: {str(e)}")
            return False, "Failed to award milestone achievement", None

    def award_social_engagement_bonus(self, challenge: SocialChallenge, participant: ChallengeParticipant) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Award bonus for high social engagement"""
        try:
            # Check if participant qualifies for social engagement bonus
            engagement_level = participant.get_engagement_level()
            if engagement_level in ["none", "low"]:
                return True, "No social engagement bonus", {"bonus_credits": 0}

            # Calculate bonus based on engagement level
            bonus_multiplier = {
                "medium": 0.1,   # 10% bonus
                "high": 0.2,     # 20% bonus
                "very_high": 0.3  # 30% bonus
            }.get(engagement_level, 0)

            base_credits = participant.credits_earned or 50  # Minimum base for calculation
            bonus_credits = int(base_credits * bonus_multiplier)

            # Award social engagement badge
            social_badges = []
            if engagement_level == "very_high":
                social_badges.append("social_butterfly")
            elif engagement_level == "high":
                social_badges.append("community_supporter")

            # Update participant
            if bonus_credits > 0 or social_badges:
                participant.credits_earned += bonus_credits
                participant.badges_earned.extend(social_badges)

                self.participant_repo.update_participant(
                    challenge.challenge_id, participant.user_id, {
                        "credits_earned": participant.credits_earned,
                        "badges_earned": participant.badges_earned
                    }
                )

            bonus_data = {
                "engagement_level": engagement_level,
                "bonus_credits": bonus_credits,
                "social_badges": social_badges,
                "social_score": participant.social_score,
                "total_interactions": (participant.cheers_received + participant.cheers_given +
                                     participant.comments_received + participant.comments_made)
            }

            current_app.logger.info(f"Social engagement bonus awarded to {participant.user_id}: {bonus_credits} credits")

            return True, "Social engagement bonus awarded", bonus_data

        except Exception as e:
            current_app.logger.error(f"Error awarding social engagement bonus: {str(e)}")
            return False, "Failed to award social engagement bonus", None

    def award_streak_bonus(self, user_id: str, consecutive_days: int) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Award bonus for consecutive participation days"""
        try:
            # Calculate streak bonus
            streak_credits = 0
            streak_badges = []

            # Award credits for significant streaks
            if consecutive_days >= 7:
                streak_credits = consecutive_days * 5  # 5 credits per day

            # Award streak badges
            if consecutive_days >= 30:
                streak_badges.append("streak_master")
            elif consecutive_days >= 14:
                streak_badges.append("consistent_challenger")
            elif consecutive_days >= 7:
                streak_badges.append("week_warrior")

            streak_data = {
                "consecutive_days": consecutive_days,
                "streak_credits": streak_credits,
                "streak_badges": streak_badges
            }

            # In real implementation, this would update user's global stats
            current_app.logger.info(f"Streak bonus awarded to {user_id}: {consecutive_days} days, {streak_credits} credits")

            return True, "Streak bonus awarded", streak_data

        except Exception as e:
            current_app.logger.error(f"Error awarding streak bonus: {str(e)}")
            return False, "Failed to award streak bonus", None

    def award_referral_bonus(self, challenge: SocialChallenge, referrer_id: str,
                           referred_user_ids: List[str]) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Award bonus for successfully referring friends"""
        try:
            successful_referrals = len(referred_user_ids)
            if successful_referrals == 0:
                return True, "No successful referrals", {"bonus_credits": 0}

            # Calculate referral bonus
            credits_per_referral = 25
            total_bonus_credits = successful_referrals * credits_per_referral

            # Award referral badges
            referral_badges = []
            if successful_referrals >= 10:
                referral_badges.append("super_recruiter")
            elif successful_referrals >= 5:
                referral_badges.append("community_builder")
            elif successful_referrals >= 1:
                referral_badges.append("friend_inviter")

            # Update referrer's participation
            participant = self.participant_repo.get_participant(challenge.challenge_id, referrer_id)
            if participant:
                self.participant_repo.update_friend_referrals(
                    challenge.challenge_id, referrer_id,
                    friends_joined=successful_referrals
                )

                # Award bonus credits
                participant.credits_earned += total_bonus_credits
                participant.badges_earned.extend(referral_badges)

                self.participant_repo.update_participant(
                    challenge.challenge_id, referrer_id, {
                        "credits_earned": participant.credits_earned,
                        "badges_earned": participant.badges_earned
                    }
                )

            referral_data = {
                "successful_referrals": successful_referrals,
                "bonus_credits": total_bonus_credits,
                "referral_badges": referral_badges,
                "referred_users": referred_user_ids
            }

            current_app.logger.info(f"Referral bonus awarded to {referrer_id}: {successful_referrals} referrals, {total_bonus_credits} credits")

            return True, "Referral bonus awarded", referral_data

        except Exception as e:
            current_app.logger.error(f"Error awarding referral bonus: {str(e)}")
            return False, "Failed to award referral bonus", None

    def get_user_achievements(self, user_id: str, challenge_id: str = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Get user's achievements and progress"""
        try:
            if challenge_id:
                # Get achievements for specific challenge
                participant = self.participant_repo.get_participant(challenge_id, user_id)
                if not participant:
                    return False, "Participant not found", None

                achievements = {
                    "challenge_id": challenge_id,
                    "credits_earned": participant.credits_earned,
                    "badges_earned": participant.badges_earned,
                    "milestones_reached": participant.milestones_reached,
                    "achievements_earned": participant.achievements_earned,
                    "social_score": participant.social_score,
                    "streak_days": participant.streak_days,
                    "best_rank": participant.best_rank,
                    "engagement_level": participant.get_engagement_level()
                }
            else:
                # Get overall achievements across all challenges
                stats = self.participant_repo.get_participant_stats(user_id)
                achievements = {
                    "total_participations": stats.get("total_participations", 0),
                    "completed_challenges": stats.get("completed", 0),
                    "active_challenges": stats.get("active", 0),
                    "avg_score": stats.get("avg_score", 0),
                    "avg_rank": stats.get("avg_rank", 0),
                    "total_social_engagement": stats.get("total_social_engagement", 0)
                }

            return True, "Achievements retrieved", achievements

        except Exception as e:
            current_app.logger.error(f"Error getting user achievements: {str(e)}")
            return False, "Failed to retrieve achievements", None

    def get_leaderboard_rewards(self, challenge_id: str, limit: int = 10) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Get leaderboard with reward information"""
        try:
            # Get challenge leaderboard
            participants = self.participant_repo.get_challenge_leaderboard(challenge_id, limit)

            leaderboard_data = []
            for participant in participants:
                participant_data = participant.to_api_dict()
                participant_data["rewards_summary"] = {
                    "credits_earned": participant.credits_earned,
                    "badges_count": len(participant.badges_earned),
                    "milestones_reached": participant.milestones_reached,
                    "social_engagement_level": participant.get_engagement_level()
                }
                leaderboard_data.append(participant_data)

            return True, "Leaderboard with rewards retrieved", {
                "leaderboard": leaderboard_data,
                "count": len(leaderboard_data)
            }

        except Exception as e:
            current_app.logger.error(f"Error getting leaderboard rewards: {str(e)}")
            return False, "Failed to retrieve leaderboard rewards", None

    def _calculate_base_credits(self, challenge: SocialChallenge, rank: int, is_winner: bool) -> int:
        """Calculate base credits for participation and ranking"""
        if is_winner or rank == 1:
            return challenge.rewards.winner_credits
        else:
            return challenge.rewards.participant_credits

    def _calculate_total_rewards(self, challenge: SocialChallenge, participant: ChallengeParticipant,
                               base_credits: int, is_winner: bool) -> Dict[str, Any]:
        """Calculate total rewards with all bonuses and multipliers"""
        # Start with base credits
        total_credits = base_credits

        # Social engagement bonus
        if participant.social_score > 0:
            social_multiplier = min(1 + (participant.social_score / 100), challenge.rewards.social_bonus_multiplier)
            total_credits = int(total_credits * social_multiplier)

        # Completion bonus (full completion gets extra credits)
        if participant.completion_percentage >= 100:
            completion_bonus = int(base_credits * 0.2)  # 20% bonus for full completion
            total_credits += completion_bonus

        # Friend referral bonus
        if participant.friends_joined > 0:
            referral_bonus = participant.friends_joined * 10  # 10 credits per friend joined
            total_credits += referral_bonus

        # Determine badges
        badges_earned = []

        # Winner badges
        if is_winner:
            badges_earned.extend(challenge.rewards.winner_badges)
        else:
            badges_earned.extend(challenge.rewards.participant_badges)

        # Performance badges
        if participant.completion_percentage >= 100:
            badges_earned.append("completionist")

        if participant.best_rank <= 3:
            badges_earned.append("top_performer")

        # Social badges
        engagement_level = participant.get_engagement_level()
        if engagement_level in ["high", "very_high"]:
            badges_earned.append("social_champion")

        return {
            "base_credits": base_credits,
            "total_credits": total_credits,
            "badges_earned": badges_earned,
            "bonuses_applied": {
                "social_bonus": participant.social_score > 0,
                "completion_bonus": participant.completion_percentage >= 100,
                "referral_bonus": participant.friends_joined > 0
            }
        }

    def _calculate_milestone_credits(self, challenge: SocialChallenge, milestone_type: str, milestone_value: float) -> int:
        """Calculate credits for milestone achievement"""
        base_credits = 10

        # Different milestone types have different values
        multipliers = {
            "progress": 1.0,      # Progress milestones (25%, 50%, 75%, 100%)
            "streak": 1.5,        # Consecutive day streaks
            "social": 2.0,        # Social interaction milestones
            "performance": 2.5,   # Performance achievement milestones
            "special": 3.0        # Special challenge-specific milestones
        }

        multiplier = multipliers.get(milestone_type, 1.0)
        credits = int(base_credits * multiplier * challenge.difficulty_level)

        return credits

    def _get_milestone_badges(self, challenge: SocialChallenge, milestone_type: str, milestone_value: float) -> List[str]:
        """Get badges for milestone achievement"""
        badges = []

        milestone_badges = {
            "progress": {
                25: ["quarter_master"],
                50: ["halfway_hero"],
                75: ["almost_there"],
                100: ["goal_crusher"]
            },
            "streak": {
                7: ["week_warrior"],
                14: ["fortnight_fighter"],
                30: ["month_master"]
            },
            "social": {
                10: ["social_starter"],
                25: ["interaction_expert"],
                50: ["community_champion"]
            }
        }

        type_badges = milestone_badges.get(milestone_type, {})
        for threshold, badge_list in type_badges.items():
            if milestone_value >= threshold:
                badges.extend(badge_list)

        return badges

    def _check_special_achievements(self, challenge: SocialChallenge, participant: ChallengeParticipant,
                                  result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for special achievements during challenge"""
        achievements = []

        # Perfect score achievement
        target_value = challenge.rules.target_value
        if target_value > 0 and result.get("score", 0) >= target_value:
            achievements.append({
                "type": "perfect_score",
                "title": "Perfect Score",
                "description": "Achieved the target score exactly or better",
                "credits_bonus": 50,
                "badge": "perfectionist"
            })

        # Underdog victory (low rank improved to win)
        if result.get("rank") == 1 and participant.best_rank > 5:
            achievements.append({
                "type": "underdog_victory",
                "title": "Underdog Victory",
                "description": "Rose from a low rank to claim victory",
                "credits_bonus": 75,
                "badge": "comeback_king"
            })

        # Social leader (highest social engagement)
        if participant.social_score > 50:  # High social engagement threshold
            achievements.append({
                "type": "social_leader",
                "title": "Social Leader",
                "description": "Highest social engagement in the challenge",
                "credits_bonus": 30,
                "badge": "social_butterfly"
            })

        # First to complete
        if participant.completion_percentage >= 100 and result.get("rank") == 1:
            achievements.append({
                "type": "speed_demon",
                "title": "Speed Demon",
                "description": "First to complete the challenge",
                "credits_bonus": 40,
                "badge": "speed_champion"
            })

        return achievements