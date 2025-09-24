from flask import Blueprint
from .controllers.social_controller import social_bp
from .achievements import register_achievement_module
from .leaderboards import create_leaderboards_blueprint

def register_social_module(app):
    """Register social module blueprints and initialize repositories"""
    # Register social blueprint with URL prefix
    app.register_blueprint(social_bp, url_prefix='/api/social')

    # Register leaderboards blueprint
    leaderboards_bp = create_leaderboards_blueprint()
    app.register_blueprint(leaderboards_bp, url_prefix='/api/social')

    # Register achievement module
    register_achievement_module(app)

    # Initialize database indexes
    try:
        from .repositories.relationship_repository import RelationshipRepository
        from .leaderboards.repositories.impact_score_repository import ImpactScoreRepository
        from .leaderboards.repositories.leaderboard_repository import LeaderboardRepository

        relationship_repo = RelationshipRepository()
        relationship_repo.create_indexes()

        impact_score_repo = ImpactScoreRepository()
        impact_score_repo.create_indexes()

        leaderboard_repo = LeaderboardRepository()
        leaderboard_repo.create_indexes()

        app.logger.info("Social module indexes created successfully")
    except Exception as e:
        app.logger.error(f"Error creating social module indexes: {str(e)}")

    # Initialize impact score integration hooks
    try:
        from .leaderboards.integration.hooks import setup_all_integrations

        # Set up integrations after a delay to ensure all modules are loaded
        def setup_integrations():
            setup_all_integrations()

        # Use app context to delay integration setup
        with app.app_context():
            app.after_first_request(setup_integrations)

    except Exception as e:
        app.logger.error(f"Error setting up impact score integrations: {str(e)}")

__all__ = ['register_social_module']