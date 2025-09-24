"""
Social Leaderboards Module

This module handles impact score calculation and dynamic leaderboard management
for the GoodPlay platform, implementing the GOO-12 requirements.

Provides:
- Impact score calculation with weighted components
- Multi-category dynamic leaderboards
- Real-time ranking updates
- Privacy controls for users
"""

from flask import Blueprint

def create_leaderboards_blueprint():
    """Create and configure leaderboards blueprint"""
    blueprint = Blueprint('leaderboards', __name__, url_prefix='/api/social')

    # Import controllers to register routes
    from .controllers.leaderboard_controller import register_routes
    register_routes(blueprint)

    return blueprint