from flask import Blueprint
from .controllers.social_controller import social_bp

def register_social_module(app):
    """Register social module blueprints and initialize repositories"""
    # Register blueprint with URL prefix
    app.register_blueprint(social_bp, url_prefix='/api/social')

    # Initialize database indexes
    try:
        from .repositories.relationship_repository import RelationshipRepository
        relationship_repo = RelationshipRepository()
        relationship_repo.create_indexes()
        app.logger.info("Social module indexes created successfully")
    except Exception as e:
        app.logger.error(f"Error creating social module indexes: {str(e)}")

__all__ = ['register_social_module']