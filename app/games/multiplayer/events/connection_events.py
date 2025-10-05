from flask_socketio import emit, join_room, leave_room
from flask import current_app, request
from .base_handler import BaseNamespace
from datetime import datetime, timezone


class MultiplayerNamespace(BaseNamespace):
    """
    Main multiplayer namespace for game WebSocket events.

    Handles:
    - Ping/pong for latency measurement
    - User authentication and session management
    - Room join/leave operations
    - Player state broadcasting
    """

    def __init__(self, namespace='/multiplayer'):
        super().__init__(namespace)
        self.connection_manager = None  # Will be injected by service

    def set_connection_manager(self, manager):
        """Inject connection manager service"""
        self.connection_manager = manager

    def on_connect(self):
        """Handle new WebSocket connection"""
        super().on_connect()
        current_app.logger.info(f"Multiplayer client connected: {request.sid}")
        return True

    def on_disconnect(self):
        """Handle WebSocket disconnection and cleanup"""
        super().on_disconnect()

        # Clean up session if connection manager is available
        if self.connection_manager:
            try:
                self.connection_manager.handle_disconnect(request.sid)
                current_app.logger.info(f"Cleaned up session for {request.sid}")
            except Exception as e:
                current_app.logger.error(f"Error cleaning up session {request.sid}: {str(e)}")

    def on_ping(self, data):
        """
        Handle ping for latency measurement.

        Client sends timestamp, server echoes it back for latency calculation.

        Event data:
            {
                "timestamp": <client_timestamp_ms>
            }

        Response:
            {
                "timestamp": <echoed_timestamp>,
                "server_time": <server_timestamp_ms>
            }
        """
        if not isinstance(data, dict):
            data = {}

        timestamp = data.get('timestamp', 0)
        server_time = int(datetime.now(timezone.utc).timestamp() * 1000)

        emit('pong', {
            'timestamp': timestamp,
            'server_time': server_time
        })

        # Update session latency if authenticated
        if self.connection_manager and hasattr(data, 'user_id'):
            try:
                latency_ms = server_time - timestamp if timestamp > 0 else 0
                self.connection_manager.update_latency(request.sid, latency_ms)
            except Exception as e:
                current_app.logger.debug(f"Could not update latency: {str(e)}")

    @BaseNamespace.require_auth
    def on_authenticate(self, data, current_user=None):
        """
        Authenticate WebSocket connection with JWT token.

        Creates a multiplayer session for the authenticated user.

        Event data:
            {
                "token": "<jwt_token>",
                "device_info": {
                    "platform": "ios|android|web",
                    "device_type": "mobile|tablet|desktop",
                    "app_version": "1.0.0"
                }
            }

        Response:
            {
                "user_id": "<user_id>",
                "session_id": "<socket_session_id>",
                "message": "WEBSOCKET_AUTH_SUCCESS"
            }
        """
        session_id = request.sid
        device_info = data.get('device_info', {})

        # Join user's personal room for targeted messages
        personal_room = f"user_{current_user}"
        join_room(personal_room)

        # Create multiplayer session if connection manager is available
        if self.connection_manager:
            try:
                self.connection_manager.create_session(
                    session_id=session_id,
                    user_id=current_user,
                    device_info=device_info
                )
                current_app.logger.info(f"Created multiplayer session for user {current_user}")
            except Exception as e:
                current_app.logger.error(f"Error creating session: {str(e)}")

        # Send authentication success
        emit('authenticated', {
            'user_id': current_user,
            'session_id': session_id,
            'message': 'WEBSOCKET_AUTH_SUCCESS',
            'timestamp': datetime.now(timezone.utc).isoformat()
        })

        current_app.logger.info(f"User {current_user} authenticated on WebSocket (sid={session_id})")

    @BaseNamespace.require_auth
    @BaseNamespace.validate_data
    def on_join_room(self, data, current_user=None):
        """
        Join a game room.

        Event data:
            {
                "token": "<jwt_token>",
                "room_id": "<room_id>"
            }

        Response to sender:
            {
                "room_id": "<room_id>",
                "message": "ROOM_JOINED_SUCCESS"
            }

        Broadcast to room (excluding sender):
            {
                "user_id": "<user_id>",
                "room_id": "<room_id>",
                "message": "PLAYER_JOINED"
            }
        """
        room_id = data.get('room_id')

        if not room_id:
            emit('error', {'message': 'ROOM_ID_REQUIRED'})
            return

        # Join the Socket.IO room
        room_name = f"room_{room_id}"
        join_room(room_name)

        # Update session with room info if connection manager available
        if self.connection_manager:
            try:
                self.connection_manager.join_room(request.sid, room_id)
            except Exception as e:
                current_app.logger.error(f"Error updating session room: {str(e)}")

        # Notify others in room about new player
        emit('player_joined', {
            'user_id': current_user,
            'room_id': room_id,
            'message': 'PLAYER_JOINED',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }, room=room_name, skip_sid=request.sid)

        # Confirm join to sender
        emit('room_joined', {
            'room_id': room_id,
            'message': 'ROOM_JOINED_SUCCESS',
            'timestamp': datetime.now(timezone.utc).isoformat()
        })

        current_app.logger.info(f"User {current_user} joined room {room_id}")

    @BaseNamespace.require_auth
    @BaseNamespace.validate_data
    def on_leave_room(self, data, current_user=None):
        """
        Leave a game room.

        Event data:
            {
                "token": "<jwt_token>",
                "room_id": "<room_id>"
            }

        Response to sender:
            {
                "room_id": "<room_id>",
                "message": "ROOM_LEFT_SUCCESS"
            }

        Broadcast to room:
            {
                "user_id": "<user_id>",
                "room_id": "<room_id>",
                "message": "PLAYER_LEFT"
            }
        """
        room_id = data.get('room_id')

        if not room_id:
            emit('error', {'message': 'ROOM_ID_REQUIRED'})
            return

        room_name = f"room_{room_id}"

        # Notify others about player leaving
        emit('player_left', {
            'user_id': current_user,
            'room_id': room_id,
            'message': 'PLAYER_LEFT',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }, room=room_name, skip_sid=request.sid)

        # Leave the Socket.IO room
        leave_room(room_name)

        # Update session
        if self.connection_manager:
            try:
                self.connection_manager.leave_room(request.sid)
            except Exception as e:
                current_app.logger.error(f"Error updating session: {str(e)}")

        # Confirm leave to sender
        emit('room_left', {
            'room_id': room_id,
            'message': 'ROOM_LEFT_SUCCESS',
            'timestamp': datetime.now(timezone.utc).isoformat()
        })

        current_app.logger.info(f"User {current_user} left room {room_id}")

    @BaseNamespace.require_auth
    @BaseNamespace.validate_data
    def on_game_action(self, data, current_user=None):
        """
        Handle generic game action and broadcast to room.

        Event data:
            {
                "token": "<jwt_token>",
                "room_id": "<room_id>",
                "action": "<action_type>",
                "payload": { ... }
            }

        Broadcast to room (excluding sender):
            {
                "user_id": "<user_id>",
                "action": "<action_type>",
                "payload": { ... },
                "timestamp": "<iso_timestamp>"
            }
        """
        room_id = data.get('room_id')
        action = data.get('action')
        payload = data.get('payload', {})

        if not room_id or not action:
            emit('error', {'message': 'ROOM_ID_AND_ACTION_REQUIRED'})
            return

        room_name = f"room_{room_id}"

        # Broadcast action to room
        emit('game_action', {
            'user_id': current_user,
            'action': action,
            'payload': payload,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }, room=room_name, skip_sid=request.sid)

        current_app.logger.debug(f"User {current_user} performed action '{action}' in room {room_id}")

    @BaseNamespace.require_auth
    @BaseNamespace.validate_data
    def on_update_state(self, data, current_user=None):
        """
        Update player state and broadcast to room.

        Event data:
            {
                "token": "<jwt_token>",
                "room_id": "<room_id>",
                "state": { ... player state ... }
            }

        Broadcast to room (excluding sender):
            {
                "user_id": "<user_id>",
                "state": { ... },
                "timestamp": "<iso_timestamp>"
            }
        """
        room_id = data.get('room_id')
        state = data.get('state', {})

        if not room_id:
            emit('error', {'message': 'ROOM_ID_REQUIRED'})
            return

        room_name = f"room_{room_id}"

        # Broadcast state update to room
        emit('state_updated', {
            'user_id': current_user,
            'state': state,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }, room=room_name, skip_sid=request.sid)

        current_app.logger.debug(f"User {current_user} updated state in room {room_id}")
