from flask import Blueprint

def create_games_blueprint():
    """Create and configure the games blueprint"""
    from .controllers.games_controller import games_bp
    return games_bp

def init_games_module():
    """Initialize the games module and discover plugins"""
    from .core.plugin_manager import plugin_manager
    from .repositories.game_repository import GameRepository
    from .repositories.game_session_repository import GameSessionRepository

    # Create database indexes
    try:
        game_repo = GameRepository()
        session_repo = GameSessionRepository()
        game_repo.create_indexes()
        session_repo.create_indexes()
    except Exception as e:
        print(f"Warning: Failed to create indexes: {e}")

    # Discover and load plugins
    try:
        discovered_plugins = plugin_manager.discover_plugins()
        print(f"Discovered {len(discovered_plugins)} game plugins")
    except Exception as e:
        print(f"Warning: Plugin discovery failed: {e}")

    return True