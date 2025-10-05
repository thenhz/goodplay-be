from flask import Blueprint
from flask_socketio import SocketIO


def register_multiplayer_module(app, socketio: SocketIO):
    """
    Register multiplayer module with app and socketio.

    Args:
        app: Flask application instance
        socketio: SocketIO instance
    """
    # Register REST API blueprints
    from .controllers.multiplayer_controller import blueprint as multiplayer_bp
    from .controllers.auth_controller import blueprint as multiplayer_auth_bp

    app.register_blueprint(multiplayer_bp, url_prefix='/api/multiplayer')
    app.register_blueprint(multiplayer_auth_bp, url_prefix='/api/multiplayer/auth')

    # Register WebSocket namespace
    from .events.connection_events import MultiplayerNamespace
    from .services.connection_manager import ConnectionManager

    # Initialize connection manager with socketio
    connection_manager = ConnectionManager.initialize(socketio)

    # Create and register namespace
    multiplayer_namespace = MultiplayerNamespace('/multiplayer')
    multiplayer_namespace.set_connection_manager(connection_manager)
    socketio.on_namespace(multiplayer_namespace)

    # Initialize repository indexes
    from .repositories import MultiplayerSessionRepository, RoomRepository, PlayerStateRepository
    import os

    if os.getenv('SKIP_DB_INIT') != '1':
        with app.app_context():
            session_repo = MultiplayerSessionRepository()
            room_repo = RoomRepository()
            state_repo = PlayerStateRepository()

            session_repo.create_indexes()
            room_repo.create_indexes()
            state_repo.create_indexes()

            app.logger.info('Multiplayer module indexes created')

    app.logger.info('Multiplayer module registered successfully')


__all__ = ['register_multiplayer_module']
