from flask import Blueprint
from .controllers.social_controller import social_bp
from .achievements import register_achievement_module
from .leaderboards import create_leaderboards_blueprint
from .challenges.controllers import social_challenges_bp

def register_social_module(app):
    """Register social module blueprints and initialize repositories"""
    # Register social blueprint with URL prefix
    app.register_blueprint(social_bp, url_prefix='/api/social')

    # Register leaderboards blueprint
    leaderboards_bp = create_leaderboards_blueprint()
    app.register_blueprint(leaderboards_bp, url_prefix='/api/social')

    # Register social challenges blueprint
    app.register_blueprint(social_challenges_bp, url_prefix='/api/social/challenges')

    # Register achievement module
    register_achievement_module(app)

    # Initialize database indexes
    try:
        from .repositories.relationship_repository import RelationshipRepository
        from .leaderboards.repositories.impact_score_repository import ImpactScoreRepository
        from .leaderboards.repositories.leaderboard_repository import LeaderboardRepository
        from .challenges.repositories.social_challenge_repository import SocialChallengeRepository
        from .challenges.repositories.challenge_participant_repository import ChallengeParticipantRepository
        from .challenges.repositories.challenge_result_repository import ChallengeResultRepository
        from .challenges.repositories.challenge_interaction_repository import ChallengeInteractionRepository

        relationship_repo = RelationshipRepository()
        relationship_repo.create_indexes()

        impact_score_repo = ImpactScoreRepository()
        impact_score_repo.create_indexes()

        leaderboard_repo = LeaderboardRepository()
        leaderboard_repo.create_indexes()

        # Initialize social challenges repositories
        social_challenge_repo = SocialChallengeRepository()
        social_challenge_repo.create_indexes()

        challenge_participant_repo = ChallengeParticipantRepository()
        challenge_participant_repo.create_indexes()

        challenge_result_repo = ChallengeResultRepository()
        challenge_result_repo.create_indexes()

        challenge_interaction_repo = ChallengeInteractionRepository()
        challenge_interaction_repo.create_indexes()

        app.logger.info("Social module indexes created successfully")
    except Exception as e:
        app.logger.error(f"Error creating social module indexes: {str(e)}")

    # Initialize impact score integration hooks
    try:
        from .leaderboards.integration.hooks import register_integration_hooks

        # Register event hooks for impact score integration
        with app.app_context():
            register_integration_hooks()

    except Exception as e:
        app.logger.error(f"Error registering impact score integration hooks: {str(e)}")

__all__ = ['register_social_module']