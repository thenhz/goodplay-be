from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from app.social.challenges.models.social_challenge import SocialChallenge, ChallengeRules, ChallengeRewards


class ImpactChallengeTypes:
    """Factory and configuration for impact and donation-related challenges"""

    @staticmethod
    def create_donation_race_challenge(creator_id: str, title: str, target_amount: float = 100.0,
                                     duration_hours: int = 168) -> SocialChallenge:
        """Create a donation race challenge"""
        rules = ChallengeRules(
            target_metric="donation_amount",
            target_value=target_amount,
            time_limit_hours=duration_hours,
            min_participants=3,
            max_participants=50,
            requires_friends=False,
            allow_public_join=True,
            scoring_method="highest",
            difficulty_multiplier=1.5
        )

        rewards = ChallengeRewards(
            winner_credits=300,  # Higher credits for impact challenges
            participant_credits=75,
            winner_badges=["donation_champion", "philanthropy_hero"],
            participant_badges=["generous_giver"],
            social_bonus_multiplier=1.5,
            impact_multiplier=3.0  # Maximum impact multiplier
        )

        challenge = SocialChallenge(
            creator_id=creator_id,
            title=title,
            description=f"Race to donate ${target_amount:.2f} to your chosen causes! Every dollar makes a difference!",
            challenge_type="impact_challenge",
            challenge_category="donation_race",
            difficulty_level=3,
            tags=["donations", "charity", "impact", "giving"],
            rules=rules,
            rewards=rewards,
            end_date=datetime.utcnow() + timedelta(hours=duration_hours),
            is_public=True,
            friends_only=False,
            allow_cheering=True,
            allow_comments=True
        )

        return challenge

    @staticmethod
    def create_cause_champion_challenge(creator_id: str, title: str, cause_id: str = None,
                                      target_supporters: int = 20, duration_hours: int = 336) -> SocialChallenge:
        """Create a cause champion challenge (2 weeks)"""
        rules = ChallengeRules(
            target_metric="cause_supporters",
            target_value=target_supporters,
            time_limit_hours=duration_hours,
            min_participants=2,
            max_participants=15,
            requires_friends=False,
            allow_public_join=True,
            scoring_method="highest",
            difficulty_multiplier=1.8
        )

        rewards = ChallengeRewards(
            winner_credits=400,
            participant_credits=100,
            winner_badges=["cause_champion", "advocacy_leader"],
            participant_badges=["cause_supporter"],
            social_bonus_multiplier=2.0,
            impact_multiplier=2.8
        )

        challenge = SocialChallenge(
            creator_id=creator_id,
            title=title,
            description=f"Champion a cause and rally {target_supporters} supporters to join your mission!",
            challenge_type="impact_challenge",
            challenge_category="cause_champion",
            difficulty_level=4,
            tags=["advocacy", "cause", "supporters", "mission"],
            rules=rules,
            rewards=rewards,
            end_date=datetime.utcnow() + timedelta(hours=duration_hours),
            is_public=True,
            friends_only=False,
            allow_cheering=True,
            allow_comments=True
        )

        return challenge

    @staticmethod
    def create_impact_multiplier_challenge(creator_id: str, title: str, target_impact_score: float = 500.0,
                                         duration_hours: int = 168) -> SocialChallenge:
        """Create an impact multiplier challenge"""
        rules = ChallengeRules(
            target_metric="impact_score",
            target_value=target_impact_score,
            time_limit_hours=duration_hours,
            min_participants=5,
            max_participants=30,
            requires_friends=False,
            allow_public_join=True,
            scoring_method="highest",
            difficulty_multiplier=1.4
        )

        rewards = ChallengeRewards(
            winner_credits=250,
            participant_credits=60,
            winner_badges=["impact_multiplier", "change_maker"],
            participant_badges=["impact_contributor"],
            social_bonus_multiplier=1.8,
            impact_multiplier=2.5
        )

        challenge = SocialChallenge(
            creator_id=creator_id,
            title=title,
            description=f"Reach {target_impact_score:.0f} impact points through donations, volunteering, and advocacy!",
            challenge_type="impact_challenge",
            challenge_category="impact_multiplier",
            difficulty_level=3,
            tags=["impact", "change", "multiplier", "contribution"],
            rules=rules,
            rewards=rewards,
            end_date=datetime.utcnow() + timedelta(hours=duration_hours),
            is_public=True,
            friends_only=False,
            allow_cheering=True,
            allow_comments=True
        )

        return challenge

    @staticmethod
    def create_community_impact_challenge(creator_id: str, title: str, target_collective: float = 1000.0,
                                        duration_hours: int = 336) -> SocialChallenge:
        """Create a community collective impact challenge"""
        rules = ChallengeRules(
            target_metric="collective_impact",
            target_value=target_collective,
            time_limit_hours=duration_hours,
            min_participants=10,
            max_participants=100,
            requires_friends=False,
            allow_public_join=True,
            scoring_method="collective",  # Everyone wins if target is reached
            difficulty_multiplier=1.2
        )

        rewards = ChallengeRewards(
            winner_credits=200,  # Everyone gets winner rewards if target reached
            participant_credits=50,
            winner_badges=["community_hero", "collective_impact"],
            participant_badges=["community_contributor"],
            social_bonus_multiplier=2.5,
            impact_multiplier=2.0
        )

        challenge = SocialChallenge(
            creator_id=creator_id,
            title=title,
            description=f"Work together to reach ${target_collective:.2f} in collective community impact!",
            challenge_type="impact_challenge",
            challenge_category="community_impact",
            difficulty_level=2,
            tags=["community", "collective", "teamwork", "together"],
            rules=rules,
            rewards=rewards,
            end_date=datetime.utcnow() + timedelta(hours=duration_hours),
            is_public=True,
            friends_only=False,
            allow_cheering=True,
            allow_comments=True
        )

        return challenge

    @staticmethod
    def create_volunteer_hours_challenge(creator_id: str, title: str, target_hours: int = 20,
                                       duration_hours: int = 336) -> SocialChallenge:
        """Create a volunteer hours challenge"""
        rules = ChallengeRules(
            target_metric="volunteer_hours",
            target_value=target_hours,
            time_limit_hours=duration_hours,
            min_participants=3,
            max_participants=25,
            requires_friends=False,
            allow_public_join=True,
            scoring_method="highest",
            difficulty_multiplier=1.6
        )

        rewards = ChallengeRewards(
            winner_credits=350,
            participant_credits=80,
            winner_badges=["volunteer_champion", "time_giver"],
            participant_badges=["volunteer"],
            social_bonus_multiplier=1.7,
            impact_multiplier=2.8
        )

        challenge = SocialChallenge(
            creator_id=creator_id,
            title=title,
            description=f"Volunteer {target_hours} hours of your time to make a difference in your community!",
            challenge_type="impact_challenge",
            challenge_category="volunteer_hours",
            difficulty_level=4,
            tags=["volunteer", "time", "service", "community"],
            rules=rules,
            rewards=rewards,
            end_date=datetime.utcnow() + timedelta(hours=duration_hours),
            is_public=True,
            friends_only=False,
            allow_cheering=True,
            allow_comments=True
        )

        return challenge

    @staticmethod
    def create_awareness_campaign_challenge(creator_id: str, title: str, target_reach: int = 100,
                                          duration_hours: int = 168) -> SocialChallenge:
        """Create an awareness campaign challenge"""
        rules = ChallengeRules(
            target_metric="awareness_reach",
            target_value=target_reach,
            time_limit_hours=duration_hours,
            min_participants=5,
            max_participants=40,
            requires_friends=False,
            allow_public_join=True,
            scoring_method="highest",
            difficulty_multiplier=1.3
        )

        rewards = ChallengeRewards(
            winner_credits=220,
            participant_credits=55,
            winner_badges=["awareness_champion", "voice_for_change"],
            participant_badges=["awareness_advocate"],
            social_bonus_multiplier=2.2,
            impact_multiplier=2.3
        )

        challenge = SocialChallenge(
            creator_id=creator_id,
            title=title,
            description=f"Spread awareness to {target_reach} people about important causes and issues!",
            challenge_type="impact_challenge",
            challenge_category="awareness_campaign",
            difficulty_level=3,
            tags=["awareness", "education", "advocacy", "spread"],
            rules=rules,
            rewards=rewards,
            end_date=datetime.utcnow() + timedelta(hours=duration_hours),
            is_public=True,
            friends_only=False,
            allow_cheering=True,
            allow_comments=True
        )

        return challenge

    @staticmethod
    def create_sustainable_action_challenge(creator_id: str, title: str, target_actions: int = 30,
                                          duration_hours: int = 168) -> SocialChallenge:
        """Create a sustainable actions challenge"""
        rules = ChallengeRules(
            target_metric="sustainable_actions",
            target_value=target_actions,
            time_limit_hours=duration_hours,
            min_participants=4,
            max_participants=35,
            requires_friends=False,
            allow_public_join=True,
            scoring_method="highest",
            difficulty_multiplier=1.1
        )

        rewards = ChallengeRewards(
            winner_credits=180,
            participant_credits=45,
            winner_badges=["eco_warrior", "sustainability_champion"],
            participant_badges=["green_advocate"],
            social_bonus_multiplier=1.9,
            impact_multiplier=2.4
        )

        challenge = SocialChallenge(
            creator_id=creator_id,
            title=title,
            description=f"Take {target_actions} sustainable actions to protect our environment!",
            challenge_type="impact_challenge",
            challenge_category="sustainable_action",
            difficulty_level=2,
            tags=["sustainability", "environment", "green", "eco"],
            rules=rules,
            rewards=rewards,
            end_date=datetime.utcnow() + timedelta(hours=duration_hours),
            is_public=True,
            friends_only=False,
            allow_cheering=True,
            allow_comments=True
        )

        return challenge

    @staticmethod
    def create_local_impact_challenge(creator_id: str, title: str, target_local_actions: int = 15,
                                    duration_hours: int = 168) -> SocialChallenge:
        """Create a local community impact challenge"""
        rules = ChallengeRules(
            target_metric="local_impact_actions",
            target_value=target_local_actions,
            time_limit_hours=duration_hours,
            min_participants=3,
            max_participants=20,
            requires_friends=True,  # Local challenges work better with friends
            allow_public_join=False,
            scoring_method="highest",
            difficulty_multiplier=1.4
        )

        rewards = ChallengeRewards(
            winner_credits=280,
            participant_credits=70,
            winner_badges=["local_hero", "neighborhood_champion"],
            participant_badges=["community_member"],
            social_bonus_multiplier=2.1,
            impact_multiplier=2.6
        )

        challenge = SocialChallenge(
            creator_id=creator_id,
            title=title,
            description=f"Make {target_local_actions} positive impacts in your local community and neighborhood!",
            challenge_type="impact_challenge",
            challenge_category="local_impact",
            difficulty_level=3,
            tags=["local", "neighborhood", "community", "grassroots"],
            rules=rules,
            rewards=rewards,
            end_date=datetime.utcnow() + timedelta(hours=duration_hours),
            friends_only=True,
            allow_cheering=True,
            allow_comments=True
        )

        return challenge

    @staticmethod
    def get_impact_challenge_configurations() -> Dict[str, Dict[str, Any]]:
        """Get all impact challenge type configurations"""
        return {
            "donation_race": {
                "name": "Donation Race Challenge",
                "description": "Compete to donate the most to causes",
                "difficulty": "Hard",
                "typical_duration": "1 week",
                "min_participants": 3,
                "max_participants": 50,
                "tags": ["donations", "charity", "giving"]
            },
            "cause_champion": {
                "name": "Cause Champion Challenge",
                "description": "Rally supporters for important causes",
                "difficulty": "Very Hard",
                "typical_duration": "2 weeks",
                "min_participants": 2,
                "max_participants": 15,
                "tags": ["advocacy", "causes", "leadership"]
            },
            "impact_multiplier": {
                "name": "Impact Multiplier Challenge",
                "description": "Maximize your overall impact score",
                "difficulty": "Hard",
                "typical_duration": "1 week",
                "min_participants": 5,
                "max_participants": 30,
                "tags": ["impact", "multiplier", "comprehensive"]
            },
            "community_impact": {
                "name": "Community Impact Challenge",
                "description": "Work together for collective impact",
                "difficulty": "Medium",
                "typical_duration": "2 weeks",
                "min_participants": 10,
                "max_participants": 100,
                "tags": ["community", "collective", "teamwork"]
            },
            "volunteer_hours": {
                "name": "Volunteer Hours Challenge",
                "description": "Contribute volunteer time to causes",
                "difficulty": "Very Hard",
                "typical_duration": "2 weeks",
                "min_participants": 3,
                "max_participants": 25,
                "tags": ["volunteer", "time", "service"]
            },
            "awareness_campaign": {
                "name": "Awareness Campaign Challenge",
                "description": "Spread awareness about important issues",
                "difficulty": "Hard",
                "typical_duration": "1 week",
                "min_participants": 5,
                "max_participants": 40,
                "tags": ["awareness", "education", "advocacy"]
            },
            "sustainable_action": {
                "name": "Sustainable Action Challenge",
                "description": "Take actions to protect the environment",
                "difficulty": "Medium",
                "typical_duration": "1 week",
                "min_participants": 4,
                "max_participants": 35,
                "tags": ["sustainability", "environment", "green"]
            },
            "local_impact": {
                "name": "Local Impact Challenge",
                "description": "Make positive impacts in your community",
                "difficulty": "Hard",
                "typical_duration": "1 week",
                "min_participants": 3,
                "max_participants": 20,
                "tags": ["local", "community", "grassroots"]
            }
        }

    @staticmethod
    def get_category_metrics() -> Dict[str, Dict[str, Any]]:
        """Get metrics configuration for each impact challenge category"""
        return {
            "donation_race": {
                "primary_metric": "total_donations_usd",
                "secondary_metrics": ["donation_count", "average_donation"],
                "scoring": "highest_wins",
                "units": "dollars"
            },
            "cause_champion": {
                "primary_metric": "supporters_rallied",
                "secondary_metrics": ["total_support_raised", "engagement_rate"],
                "scoring": "highest_wins",
                "units": "supporters"
            },
            "impact_multiplier": {
                "primary_metric": "total_impact_score",
                "secondary_metrics": ["impact_categories", "consistency_rating"],
                "scoring": "highest_wins",
                "units": "points"
            },
            "community_impact": {
                "primary_metric": "collective_contribution",
                "secondary_metrics": ["individual_contribution", "participation_rate"],
                "scoring": "collective_target",
                "units": "dollars"
            },
            "volunteer_hours": {
                "primary_metric": "volunteer_hours_total",
                "secondary_metrics": ["volunteer_sessions", "causes_supported"],
                "scoring": "highest_wins",
                "units": "hours"
            },
            "awareness_campaign": {
                "primary_metric": "people_reached",
                "secondary_metrics": ["shares_generated", "engagement_rate"],
                "scoring": "highest_wins",
                "units": "people"
            },
            "sustainable_action": {
                "primary_metric": "sustainable_actions_count",
                "secondary_metrics": ["action_categories", "environmental_impact"],
                "scoring": "highest_wins",
                "units": "actions"
            },
            "local_impact": {
                "primary_metric": "local_actions_count",
                "secondary_metrics": ["community_feedback", "local_engagement"],
                "scoring": "highest_wins",
                "units": "actions"
            }
        }

    @staticmethod
    def get_impact_multipliers() -> Dict[str, float]:
        """Get impact multipliers for different challenge types"""
        return {
            "donation_race": 3.0,         # Maximum impact - direct donations
            "cause_champion": 2.8,        # Very high impact - rallying support
            "impact_multiplier": 2.5,     # High impact - comprehensive approach
            "community_impact": 2.0,      # Medium-high impact - collective effort
            "volunteer_hours": 2.8,       # Very high impact - time contribution
            "awareness_campaign": 2.3,    # High impact - education and awareness
            "sustainable_action": 2.4,    # High impact - environmental protection
            "local_impact": 2.6           # Very high impact - direct community benefit
        }

    @staticmethod
    def get_suggested_onlus_categories() -> Dict[str, List[str]]:
        """Get suggested ONLUS categories for different impact challenges"""
        return {
            "donation_race": ["general", "emergency_relief", "poverty_alleviation"],
            "cause_champion": ["advocacy", "human_rights", "social_justice"],
            "impact_multiplier": ["comprehensive", "multi_cause", "community_development"],
            "community_impact": ["local_community", "neighborhood_improvement", "civic_engagement"],
            "volunteer_hours": ["volunteer_organizations", "service_groups", "community_centers"],
            "awareness_campaign": ["education", "public_awareness", "social_issues"],
            "sustainable_action": ["environmental", "climate_change", "conservation"],
            "local_impact": ["local_charities", "community_organizations", "neighborhood_groups"]
        }