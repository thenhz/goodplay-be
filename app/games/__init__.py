from flask import Blueprint

def create_games_blueprint():
    """Create and configure the games blueprint"""
    from .controllers.games_controller import games_bp
    return games_bp

def create_modes_blueprint():
    """Create and configure the modes blueprint"""
    from .modes.controllers.modes_controller import modes_bp
    return modes_bp

def create_challenges_blueprint():
    """Create and configure the challenges blueprint"""
    from .challenges.controllers.challenges_controller import challenges_bp
    return challenges_bp

def create_teams_blueprint():
    """Create and configure the teams blueprint"""
    from .teams.controllers.teams_controller import teams_bp
    return teams_bp

def init_games_module():
    """Initialize the games module and discover plugins"""
    from .core.plugin_manager import plugin_manager
    from .repositories.game_repository import GameRepository
    from .repositories.game_session_repository import GameSessionRepository
    from .modes.services.mode_manager import ModeManager

    # Create database indexes
    try:
        game_repo = GameRepository()
        session_repo = GameSessionRepository()
        game_repo.create_indexes()
        session_repo.create_indexes()
    except Exception as e:
        print(f"Warning: Failed to create indexes: {e}")

    # Initialize mode system
    try:
        mode_manager = ModeManager()
        success, message, data = mode_manager.initialize_system()
        if success:
            print(f"Mode system initialized: {data.get('default_modes', [])} default modes")
        else:
            print(f"Warning: Mode system initialization failed: {message}")
    except Exception as e:
        print(f"Warning: Mode system initialization failed: {e}")

    # Discover and load plugins
    try:
        discovered_plugins = plugin_manager.discover_plugins()
        print(f"Discovered {len(discovered_plugins)} game plugins")
    except Exception as e:
        print(f"Warning: Plugin discovery failed: {e}")

    return True