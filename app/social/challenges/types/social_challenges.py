from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from app.social.challenges.models.social_challenge import SocialChallenge, ChallengeRules, ChallengeRewards


class SocialChallengeTypes:
    """Factory and configuration for social engagement challenges"""

    @staticmethod
    def create_friend_referral_challenge(creator_id: str, title: str, target_referrals: int = 5,
                                       duration_hours: int = 168) -> SocialChallenge:
        """Create a friend referral challenge"""
        rules = ChallengeRules(
            target_metric="friends_referred",
            target_value=target_referrals,
            time_limit_hours=duration_hours,
            min_participants=3,
            max_participants=25,
            requires_friends=False,
            allow_public_join=True,
            scoring_method="highest",
            difficulty_multiplier=1.4
        )

        rewards = ChallengeRewards(
            winner_credits=200,
            participant_credits=50,
            winner_badges=["super_recruiter", "network_builder"],
            participant_badges=["friend_inviter"],
            social_bonus_multiplier=2.0,  # High social bonus
            impact_multiplier=1.5
        )

        challenge = SocialChallenge(
            creator_id=creator_id,
            title=title,
            description=f"Invite {target_referrals} new friends to join the platform and participate in challenges!",
            challenge_type="social_engagement",
            challenge_category="friend_referral",
            difficulty_level=3,
            tags=["referral", "friends", "growth", "community"],
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
    def create_community_helper_challenge(creator_id: str, title: str, target_helps: int = 10,
                                        duration_hours: int = 168) -> SocialChallenge:
        """Create a community helper challenge"""
        rules = ChallengeRules(
            target_metric="community_helps",
            target_value=target_helps,
            time_limit_hours=duration_hours,
            min_participants=5,
            max_participants=30,
            requires_friends=False,
            allow_public_join=True,
            scoring_method="highest",
            difficulty_multiplier=1.2
        )

        rewards = ChallengeRewards(
            winner_credits=150,
            participant_credits=40,
            winner_badges=["community_champion", "helpful_hero"],
            participant_badges=["community_helper"],
            social_bonus_multiplier=2.5,  # Very high social bonus
            impact_multiplier=2.0
        )

        challenge = SocialChallenge(
            creator_id=creator_id,
            title=title,
            description=f"Help {target_helps} community members with questions, challenges, or guidance!",
            challenge_type="social_engagement",
            challenge_category="community_helper",
            difficulty_level=2,
            tags=["help", "support", "community", "guidance"],
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
    def create_content_creator_challenge(creator_id: str, title: str, target_posts: int = 15,
                                       duration_hours: int = 168) -> SocialChallenge:
        """Create a content creation challenge"""
        rules = ChallengeRules(
            target_metric="content_posts",
            target_value=target_posts,
            time_limit_hours=duration_hours,
            min_participants=3,
            max_participants=20,
            requires_friends=False,
            allow_public_join=True,
            scoring_method="highest",
            difficulty_multiplier=1.3
        )

        rewards = ChallengeRewards(
            winner_credits=180,
            participant_credits=45,
            winner_badges=["content_king", "creative_genius"],
            participant_badges=["content_creator"],
            social_bonus_multiplier=1.8,
            impact_multiplier=1.3
        )

        challenge = SocialChallenge(
            creator_id=creator_id,
            title=title,
            description=f"Create and share {target_posts} engaging posts, tips, or stories with the community!",
            challenge_type="social_engagement",
            challenge_category="content_creator",
            difficulty_level=3,
            tags=["content", "creativity", "sharing", "community"],
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
    def create_engagement_master_challenge(creator_id: str, title: str, target_interactions: int = 50,
                                         duration_hours: int = 168) -> SocialChallenge:
        """Create an engagement master challenge"""
        rules = ChallengeRules(
            target_metric="social_interactions",
            target_value=target_interactions,
            time_limit_hours=duration_hours,
            min_participants=4,
            max_participants=25,
            requires_friends=False,
            allow_public_join=True,
            scoring_method="highest",
            difficulty_multiplier=1.1
        )

        rewards = ChallengeRewards(
            winner_credits=140,
            participant_credits=35,
            winner_badges=["engagement_master", "social_butterfly"],
            participant_badges=["active_community_member"],
            social_bonus_multiplier=3.0,  # Maximum social bonus
            impact_multiplier=1.2
        )

        challenge = SocialChallenge(
            creator_id=creator_id,
            title=title,
            description=f"Receive {target_interactions} likes, comments, and positive interactions from community members!",
            challenge_type="social_engagement",
            challenge_category="engagement_master",
            difficulty_level=2,
            tags=["engagement", "interactions", "popularity", "community"],
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
    def create_mentor_challenge(creator_id: str, title: str, target_mentees: int = 3,
                              duration_hours: int = 336) -> SocialChallenge:
        """Create a mentoring challenge (2 weeks)"""
        rules = ChallengeRules(
            target_metric="mentees_helped",
            target_value=target_mentees,
            time_limit_hours=duration_hours,
            min_participants=2,
            max_participants=10,
            requires_friends=False,
            allow_public_join=True,
            scoring_method="highest",
            difficulty_multiplier=1.6
        )

        rewards = ChallengeRewards(
            winner_credits=250,
            participant_credits=75,
            winner_badges=["master_mentor", "wisdom_keeper"],
            participant_badges=["mentor"],
            social_bonus_multiplier=2.2,
            impact_multiplier=2.5  # High impact for mentoring
        )

        challenge = SocialChallenge(
            creator_id=creator_id,
            title=title,
            description=f"Mentor and guide {target_mentees} new users through their first week on the platform!",
            challenge_type="social_engagement",
            challenge_category="mentor",
            difficulty_level=4,
            tags=["mentoring", "guidance", "teaching", "leadership"],
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
    def create_social_connector_challenge(creator_id: str, title: str, target_connections: int = 20,
                                        duration_hours: int = 168) -> SocialChallenge:
        """Create a social connector challenge"""
        rules = ChallengeRules(
            target_metric="connections_facilitated",
            target_value=target_connections,
            time_limit_hours=duration_hours,
            min_participants=3,
            max_participants=15,
            requires_friends=True,
            allow_public_join=False,
            scoring_method="highest",
            difficulty_multiplier=1.4
        )

        rewards = ChallengeRewards(
            winner_credits=170,
            participant_credits=50,
            winner_badges=["social_connector", "networking_ninja"],
            participant_badges=["connector"],
            social_bonus_multiplier=2.3,
            impact_multiplier=1.8
        )

        challenge = SocialChallenge(
            creator_id=creator_id,
            title=title,
            description=f"Help facilitate {target_connections} new connections between community members!",
            challenge_type="social_engagement",
            challenge_category="social_connector",
            difficulty_level=3,
            tags=["networking", "connections", "introductions", "community"],
            rules=rules,
            rewards=rewards,
            end_date=datetime.utcnow() + timedelta(hours=duration_hours),
            friends_only=True,
            allow_cheering=True,
            allow_comments=True
        )

        return challenge

    @staticmethod
    def create_positivity_spreader_challenge(creator_id: str, title: str, target_positive_actions: int = 30,
                                           duration_hours: int = 168) -> SocialChallenge:
        """Create a positivity spreading challenge"""
        rules = ChallengeRules(
            target_metric="positive_actions",
            target_value=target_positive_actions,
            time_limit_hours=duration_hours,
            min_participants=5,
            max_participants=50,
            requires_friends=False,
            allow_public_join=True,
            scoring_method="highest",
            difficulty_multiplier=1.0  # Easy difficulty to encourage participation
        )

        rewards = ChallengeRewards(
            winner_credits=120,
            participant_credits=30,
            winner_badges=["positivity_champion", "sunshine_spreader"],
            participant_badges=["positive_vibes"],
            social_bonus_multiplier=2.8,
            impact_multiplier=1.5
        )

        challenge = SocialChallenge(
            creator_id=creator_id,
            title=title,
            description=f"Spread {target_positive_actions} positive actions: compliments, encouragement, and support!",
            challenge_type="social_engagement",
            challenge_category="positivity_spreader",
            difficulty_level=1,
            tags=["positivity", "encouragement", "support", "kindness"],
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
    def create_knowledge_sharer_challenge(creator_id: str, title: str, target_shares: int = 12,
                                        duration_hours: int = 168) -> SocialChallenge:
        """Create a knowledge sharing challenge"""
        rules = ChallengeRules(
            target_metric="knowledge_shares",
            target_value=target_shares,
            time_limit_hours=duration_hours,
            min_participants=3,
            max_participants=20,
            requires_friends=False,
            allow_public_join=True,
            scoring_method="highest",
            difficulty_multiplier=1.3
        )

        rewards = ChallengeRewards(
            winner_credits=160,
            participant_credits=40,
            winner_badges=["knowledge_guru", "wisdom_sharer"],
            participant_badges=["knowledge_contributor"],
            social_bonus_multiplier=1.9,
            impact_multiplier=2.0
        )

        challenge = SocialChallenge(
            creator_id=creator_id,
            title=title,
            description=f"Share {target_shares} valuable tips, tutorials, or insights with the community!",
            challenge_type="social_engagement",
            challenge_category="knowledge_sharer",
            difficulty_level=3,
            tags=["knowledge", "education", "tips", "tutorials"],
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
    def get_social_challenge_configurations() -> Dict[str, Dict[str, Any]]:
        """Get all social challenge type configurations"""
        return {
            "friend_referral": {
                "name": "Friend Referral Challenge",
                "description": "Invite new friends to join the community",
                "difficulty": "Hard",
                "typical_duration": "1 week",
                "min_participants": 3,
                "max_participants": 25,
                "tags": ["referral", "growth", "networking"]
            },
            "community_helper": {
                "name": "Community Helper Challenge",
                "description": "Help other community members",
                "difficulty": "Medium",
                "typical_duration": "1 week",
                "min_participants": 5,
                "max_participants": 30,
                "tags": ["help", "support", "guidance"]
            },
            "content_creator": {
                "name": "Content Creator Challenge",
                "description": "Create and share engaging content",
                "difficulty": "Hard",
                "typical_duration": "1 week",
                "min_participants": 3,
                "max_participants": 20,
                "tags": ["content", "creativity", "sharing"]
            },
            "engagement_master": {
                "name": "Engagement Master Challenge",
                "description": "Receive interactions from community",
                "difficulty": "Medium",
                "typical_duration": "1 week",
                "min_participants": 4,
                "max_participants": 25,
                "tags": ["engagement", "popularity", "interactions"]
            },
            "mentor": {
                "name": "Mentor Challenge",
                "description": "Guide and mentor new users",
                "difficulty": "Very Hard",
                "typical_duration": "2 weeks",
                "min_participants": 2,
                "max_participants": 10,
                "tags": ["mentoring", "teaching", "leadership"]
            },
            "social_connector": {
                "name": "Social Connector Challenge",
                "description": "Facilitate connections between users",
                "difficulty": "Hard",
                "typical_duration": "1 week",
                "min_participants": 3,
                "max_participants": 15,
                "tags": ["networking", "connections", "introductions"]
            },
            "positivity_spreader": {
                "name": "Positivity Spreader Challenge",
                "description": "Spread positivity and encouragement",
                "difficulty": "Easy",
                "typical_duration": "1 week",
                "min_participants": 5,
                "max_participants": 50,
                "tags": ["positivity", "encouragement", "kindness"]
            },
            "knowledge_sharer": {
                "name": "Knowledge Sharer Challenge",
                "description": "Share valuable knowledge and insights",
                "difficulty": "Hard",
                "typical_duration": "1 week",
                "min_participants": 3,
                "max_participants": 20,
                "tags": ["knowledge", "education", "insights"]
            }
        }

    @staticmethod
    def get_category_metrics() -> Dict[str, Dict[str, Any]]:
        """Get metrics configuration for each social challenge category"""
        return {
            "friend_referral": {
                "primary_metric": "friends_referred_count",
                "secondary_metrics": ["friends_joined_count", "referral_conversion_rate"],
                "scoring": "highest_wins",
                "units": "friends"
            },
            "community_helper": {
                "primary_metric": "help_actions_count",
                "secondary_metrics": ["help_rating", "people_helped"],
                "scoring": "highest_wins",
                "units": "actions"
            },
            "content_creator": {
                "primary_metric": "content_posts_count",
                "secondary_metrics": ["engagement_per_post", "content_quality_rating"],
                "scoring": "highest_wins",
                "units": "posts"
            },
            "engagement_master": {
                "primary_metric": "interactions_received",
                "secondary_metrics": ["unique_interactors", "engagement_rate"],
                "scoring": "highest_wins",
                "units": "interactions"
            },
            "mentor": {
                "primary_metric": "mentees_helped",
                "secondary_metrics": ["mentoring_hours", "mentee_success_rate"],
                "scoring": "highest_wins",
                "units": "people"
            },
            "social_connector": {
                "primary_metric": "connections_facilitated",
                "secondary_metrics": ["successful_connections", "network_growth"],
                "scoring": "highest_wins",
                "units": "connections"
            },
            "positivity_spreader": {
                "primary_metric": "positive_actions",
                "secondary_metrics": ["recipients_reached", "positivity_impact"],
                "scoring": "highest_wins",
                "units": "actions"
            },
            "knowledge_sharer": {
                "primary_metric": "knowledge_shares",
                "secondary_metrics": ["knowledge_rating", "learning_impact"],
                "scoring": "highest_wins",
                "units": "shares"
            }
        }

    @staticmethod
    def get_social_impact_weights() -> Dict[str, float]:
        """Get social impact weights for different challenge types"""
        return {
            "friend_referral": 2.0,      # High impact - grows community
            "community_helper": 2.5,     # Very high impact - helps others
            "content_creator": 1.5,      # Medium-high impact - creates value
            "engagement_master": 1.2,    # Medium impact - builds connections
            "mentor": 3.0,               # Maximum impact - teaches others
            "social_connector": 2.2,     # High impact - facilitates relationships
            "positivity_spreader": 2.8,  # Very high impact - improves atmosphere
            "knowledge_sharer": 2.3      # High impact - educates community
        }