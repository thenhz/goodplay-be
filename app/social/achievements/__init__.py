from .controllers.achievement_controller import achievement_bp
from .repositories.achievement_repository import AchievementRepository
from .data.default_achievements import initialize_default_achievements

def register_achievement_module(app):
    """Register achievement module blueprints and initialize repositories"""
    # Register blueprint with URL prefix
    app.register_blueprint(achievement_bp, url_prefix='/api/achievements')

    # Initialize database indexes
    try:
        achievement_repo = AchievementRepository()
        achievement_repo.create_indexes()
        app.logger.info("Achievement module indexes created successfully")

        # Initialize default achievements
        initialize_default_achievements(achievement_repo)
        app.logger.info("Default achievements initialized successfully")

    except Exception as e:
        app.logger.error(f"Error creating achievement module indexes: {str(e)}")

__all__ = ['register_achievement_module', 'achievement_bp']