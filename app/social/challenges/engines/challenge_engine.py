from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from flask import current_app

from app.social.challenges.models.social_challenge import SocialChallenge
from app.social.challenges.models.challenge_participant import ChallengeParticipant
from app.social.challenges.types.gaming_challenges import GamingChallengeTypes
from app.social.challenges.types.social_challenges import SocialChallengeTypes
from app.social.challenges.types.impact_challenges import ImpactChallengeTypes


class ChallengeEngine:
    """Engine for managing challenge creation, validation, and execution logic"""

    def __init__(self):
        self.gaming_types = GamingChallengeTypes()
        self.social_types = SocialChallengeTypes()
        self.impact_types = ImpactChallengeTypes()

    def create_challenge_from_template(self, creator_id: str, template_type: str,
                                     template_category: str, custom_params: Dict[str, Any] = None) -> Tuple[bool, str, Optional[SocialChallenge]]:
        """Create a challenge from predefined templates"""
        try:
            custom_params = custom_params or {}

            # Get default title if not provided
            title = custom_params.get('title', f"{template_category.replace('_', ' ').title()} Challenge")

            challenge = None

            # Gaming challenges
            if template_type == "gaming_social":
                challenge = self._create_gaming_challenge(creator_id, template_category, title, custom_params)

            # Social engagement challenges
            elif template_type == "social_engagement":
                challenge = self._create_social_challenge(creator_id, template_category, title, custom_params)

            # Impact challenges
            elif template_type == "impact_challenge":
                challenge = self._create_impact_challenge(creator_id, template_category, title, custom_params)

            if not challenge:
                return False, f"Unknown challenge template: {template_type}/{template_category}", None

            # Apply custom parameters
            self._apply_custom_parameters(challenge, custom_params)

            current_app.logger.info(f"Challenge created from template {template_type}/{template_category} by {creator_id}")

            return True, "Challenge created successfully from template", challenge

        except Exception as e:
            current_app.logger.error(f"Error creating challenge from template: {str(e)}")
            return False, "Failed to create challenge from template", None

    def validate_challenge_configuration(self, challenge: SocialChallenge) -> Tuple[bool, List[str]]:
        """Validate challenge configuration and rules"""
        errors = []

        # Basic validation
        if not challenge.title or len(challenge.title.strip()) < 3:
            errors.append("Challenge title must be at least 3 characters long")

        if challenge.rules.target_value <= 0:
            errors.append("Target value must be greater than 0")

        if challenge.rules.min_participants < 1:
            errors.append("Minimum participants must be at least 1")

        if challenge.rules.max_participants < challenge.rules.min_participants:
            errors.append("Maximum participants cannot be less than minimum participants")

        if challenge.end_date <= datetime.utcnow():
            errors.append("End date must be in the future")

        # Type-specific validation
        type_errors = self._validate_challenge_type_specific(challenge)
        errors.extend(type_errors)

        # Difficulty validation
        if challenge.difficulty_level < 1 or challenge.difficulty_level > 5:
            errors.append("Difficulty level must be between 1 and 5")

        # Rewards validation
        if challenge.rewards.winner_credits < 0 or challenge.rewards.participant_credits < 0:
            errors.append("Reward credits cannot be negative")

        return len(errors) == 0, errors

    def calculate_challenge_difficulty(self, challenge: SocialChallenge) -> int:
        """Calculate appropriate difficulty level based on challenge parameters"""
        base_difficulty = 2  # Medium default

        # Adjust based on target value and type
        if challenge.challenge_type == "gaming_social":
            if challenge.challenge_category in ["speed_run", "perfect_game"]:
                base_difficulty += 2
            elif challenge.challenge_category in ["high_score", "endurance"]:
                base_difficulty += 1

        elif challenge.challenge_type == "social_engagement":
            if challenge.challenge_category in ["mentor", "content_creator"]:
                base_difficulty += 2
            elif challenge.challenge_category in ["friend_referral", "social_connector"]:
                base_difficulty += 1

        elif challenge.challenge_type == "impact_challenge":
            if challenge.challenge_category in ["cause_champion", "volunteer_hours"]:
                base_difficulty += 2
            elif challenge.challenge_category in ["donation_race", "local_impact"]:
                base_difficulty += 1

        # Adjust based on participant requirements
        if challenge.rules.min_participants >= 10:
            base_difficulty += 1

        # Adjust based on duration
        duration_hours = (challenge.end_date - challenge.start_date).total_seconds() / 3600
        if duration_hours < 72:  # Less than 3 days
            base_difficulty += 1
        elif duration_hours > 336:  # More than 2 weeks
            base_difficulty -= 1

        # Clamp to valid range
        return max(1, min(5, base_difficulty))

    def suggest_challenge_parameters(self, challenge_type: str, challenge_category: str,
                                   user_history: Dict[str, Any] = None) -> Dict[str, Any]:
        """Suggest optimal challenge parameters based on type and user history"""
        suggestions = {
            "duration_hours": 168,  # Default 1 week
            "difficulty_level": 2,
            "min_participants": 3,
            "max_participants": 10,
            "target_value": 100
        }

        # Get type-specific suggestions
        type_configs = self._get_challenge_type_configs()
        if challenge_type in type_configs and challenge_category in type_configs[challenge_type]:
            config = type_configs[challenge_type][challenge_category]
            suggestions.update({
                "min_participants": config.get("min_participants", suggestions["min_participants"]),
                "max_participants": config.get("max_participants", suggestions["max_participants"]),
                "typical_duration": config.get("typical_duration", "1 week"),
                "difficulty": config.get("difficulty", "Medium")
            })

        # Adjust based on user history
        if user_history:
            avg_participation = user_history.get("avg_participation", 5)
            if avg_participation > 15:
                suggestions["max_participants"] = min(50, suggestions["max_participants"] * 2)

            success_rate = user_history.get("success_rate", 0.7)
            if success_rate > 0.8:
                suggestions["difficulty_level"] = min(5, suggestions["difficulty_level"] + 1)
            elif success_rate < 0.5:
                suggestions["difficulty_level"] = max(1, suggestions["difficulty_level"] - 1)

        return suggestions

    def check_challenge_prerequisites(self, challenge: SocialChallenge, user_id: str,
                                    user_profile: Dict[str, Any] = None) -> Tuple[bool, List[str]]:
        """Check if user meets prerequisites to join challenge"""
        requirements = []

        # Basic requirements
        if challenge.friends_only and user_id != challenge.creator_id:
            requirements.append("Must be friends with challenge creator")

        # Experience-based requirements
        if user_profile:
            user_level = user_profile.get("level", 1)
            required_level = self._get_required_level(challenge)

            if user_level < required_level:
                requirements.append(f"Must be level {required_level} or higher")

            # Challenge-specific requirements
            challenge_count = user_profile.get("challenges_completed", 0)
            if challenge.difficulty_level >= 4 and challenge_count < 3:
                requirements.append("Must complete at least 3 challenges before joining hard difficulty")

        can_join = len(requirements) == 0
        return can_join, requirements

    def calculate_estimated_completion_time(self, challenge: SocialChallenge,
                                          user_profile: Dict[str, Any] = None) -> Dict[str, Any]:
        """Estimate time needed to complete challenge"""
        base_hours = {
            "gaming_social": {"speed_run": 2, "high_score": 8, "endurance": 12, "variety": 15},
            "social_engagement": {"friend_referral": 20, "community_helper": 10, "content_creator": 25},
            "impact_challenge": {"donation_race": 5, "volunteer_hours": 40, "awareness_campaign": 15}
        }

        category_hours = base_hours.get(challenge.challenge_type, {}).get(challenge.challenge_category, 10)

        # Adjust based on target value
        value_multiplier = max(0.5, min(3.0, challenge.rules.target_value / 100))
        estimated_hours = category_hours * value_multiplier

        # Adjust based on user experience
        if user_profile:
            experience_level = user_profile.get("level", 1)
            experience_multiplier = max(0.5, 2.0 - (experience_level * 0.1))
            estimated_hours *= experience_multiplier

        return {
            "estimated_hours": round(estimated_hours, 1),
            "confidence": "medium",
            "factors_considered": ["challenge_type", "target_value", "user_experience"]
        }

    def _create_gaming_challenge(self, creator_id: str, category: str, title: str, params: Dict[str, Any]) -> Optional[SocialChallenge]:
        """Create gaming challenge based on category"""
        if category == "speed_run":
            return self.gaming_types.create_speed_run_challenge(
                creator_id, title,
                params.get("game_id"),
                params.get("target_time_seconds", 300),
                params.get("duration_hours", 72)
            )
        elif category == "high_score":
            return self.gaming_types.create_high_score_challenge(
                creator_id, title,
                params.get("game_id"),
                params.get("target_score", 1000),
                params.get("duration_hours", 168)
            )
        elif category == "endurance":
            return self.gaming_types.create_endurance_challenge(
                creator_id, title,
                params.get("game_id"),
                params.get("target_minutes", 60),
                params.get("duration_hours", 168)
            )
        elif category == "variety":
            return self.gaming_types.create_variety_challenge(
                creator_id, title,
                params.get("target_games", 5),
                params.get("duration_hours", 168)
            )
        elif category == "perfect_game":
            return self.gaming_types.create_perfect_game_challenge(
                creator_id, title,
                params.get("game_id"),
                params.get("duration_hours", 72)
            )
        return None

    def _create_social_challenge(self, creator_id: str, category: str, title: str, params: Dict[str, Any]) -> Optional[SocialChallenge]:
        """Create social engagement challenge based on category"""
        if category == "friend_referral":
            return self.social_types.create_friend_referral_challenge(
                creator_id, title,
                params.get("target_referrals", 5),
                params.get("duration_hours", 168)
            )
        elif category == "community_helper":
            return self.social_types.create_community_helper_challenge(
                creator_id, title,
                params.get("target_helps", 10),
                params.get("duration_hours", 168)
            )
        elif category == "content_creator":
            return self.social_types.create_content_creator_challenge(
                creator_id, title,
                params.get("target_posts", 15),
                params.get("duration_hours", 168)
            )
        elif category == "engagement_master":
            return self.social_types.create_engagement_master_challenge(
                creator_id, title,
                params.get("target_interactions", 50),
                params.get("duration_hours", 168)
            )
        elif category == "mentor":
            return self.social_types.create_mentor_challenge(
                creator_id, title,
                params.get("target_mentees", 3),
                params.get("duration_hours", 336)
            )
        return None

    def _create_impact_challenge(self, creator_id: str, category: str, title: str, params: Dict[str, Any]) -> Optional[SocialChallenge]:
        """Create impact challenge based on category"""
        if category == "donation_race":
            return self.impact_types.create_donation_race_challenge(
                creator_id, title,
                params.get("target_amount", 100.0),
                params.get("duration_hours", 168)
            )
        elif category == "cause_champion":
            return self.impact_types.create_cause_champion_challenge(
                creator_id, title,
                params.get("cause_id"),
                params.get("target_supporters", 20),
                params.get("duration_hours", 336)
            )
        elif category == "impact_multiplier":
            return self.impact_types.create_impact_multiplier_challenge(
                creator_id, title,
                params.get("target_impact_score", 500.0),
                params.get("duration_hours", 168)
            )
        elif category == "community_impact":
            return self.impact_types.create_community_impact_challenge(
                creator_id, title,
                params.get("target_collective", 1000.0),
                params.get("duration_hours", 336)
            )
        return None

    def _apply_custom_parameters(self, challenge: SocialChallenge, params: Dict[str, Any]) -> None:
        """Apply custom parameters to challenge"""
        if "description" in params:
            challenge.description = params["description"]

        if "tags" in params and isinstance(params["tags"], list):
            challenge.tags.extend(params["tags"])

        if "is_public" in params:
            challenge.is_public = params["is_public"]

        if "friends_only" in params:
            challenge.friends_only = params["friends_only"]

    def _validate_challenge_type_specific(self, challenge: SocialChallenge) -> List[str]:
        """Validate challenge based on specific type requirements"""
        errors = []

        if challenge.challenge_type == "gaming_social":
            if challenge.challenge_category == "speed_run" and challenge.rules.target_value > 3600:
                errors.append("Speed run target time should be reasonable (under 1 hour)")

        elif challenge.challenge_type == "social_engagement":
            if challenge.challenge_category == "friend_referral" and challenge.rules.target_value > 50:
                errors.append("Friend referral target should be achievable (under 50 friends)")

        elif challenge.challenge_type == "impact_challenge":
            if challenge.challenge_category == "donation_race" and challenge.rules.target_value > 10000:
                errors.append("Donation target should be reasonable (under $10,000)")

        return errors

    def _get_challenge_type_configs(self) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """Get all challenge type configurations"""
        return {
            "gaming_social": self.gaming_types.get_gaming_challenge_configurations(),
            "social_engagement": self.social_types.get_social_challenge_configurations(),
            "impact_challenge": self.impact_types.get_impact_challenge_configurations()
        }

    def _get_required_level(self, challenge: SocialChallenge) -> int:
        """Get required user level for challenge"""
        base_level = 1

        if challenge.difficulty_level >= 4:
            base_level = 3
        elif challenge.difficulty_level >= 3:
            base_level = 2

        # Additional requirements for specific types
        if challenge.challenge_type == "impact_challenge":
            base_level += 1

        return base_level

    def get_challenge_templates(self) -> Dict[str, Any]:
        """Get all available challenge templates"""
        return {
            "gaming_social": {
                "name": "Gaming Social Challenges",
                "description": "Challenges focused on gaming achievements with friends",
                "categories": self.gaming_types.get_gaming_challenge_configurations()
            },
            "social_engagement": {
                "name": "Social Engagement Challenges",
                "description": "Challenges to build community and social connections",
                "categories": self.social_types.get_social_challenge_configurations()
            },
            "impact_challenge": {
                "name": "Impact Challenges",
                "description": "Challenges focused on making positive real-world impact",
                "categories": self.impact_types.get_impact_challenge_configurations()
            }
        }