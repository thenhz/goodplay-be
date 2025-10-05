from flask_socketio import Namespace, emit, disconnect
from flask import request, current_app
from functools import wraps
import jwt
from typing import Callable, Any


class BaseNamespace(Namespace):
    """
    Base namespace with authentication and error handling for WebSocket events.

    Provides:
    - Connection lifecycle management
    - JWT authentication decorator
    - Global error handling
    - Structured logging
    """

    def on_connect(self):
        """Handle new WebSocket connection"""
        current_app.logger.info(f"WebSocket connected: {request.sid} from {request.remote_addr}")
        return True

    def on_disconnect(self):
        """Handle WebSocket disconnection"""
        current_app.logger.info(f"WebSocket disconnected: {request.sid}")
        # Override in subclasses to handle cleanup (sessions, rooms, etc.)

    def on_error(self, error):
        """Global error handler for WebSocket events"""
        current_app.logger.error(f"WebSocket error on {request.sid}: {str(error)}", exc_info=True)
        emit('error', {
            'message': 'INTERNAL_SERVER_ERROR',
            'details': str(error) if current_app.debug else None
        })

    @staticmethod
    def require_auth(f: Callable) -> Callable:
        """
        Decorator for authenticated WebSocket events.

        Usage:
            @BaseNamespace.require_auth
            def on_my_event(self, data, current_user=None):
                # current_user contains user_id from JWT
                pass

        The decorator expects a 'token' field in the event data payload.
        """
        @wraps(f)
        def wrapped(self, *args, **kwargs):
            # Extract data from args
            data = args[0] if args else {}

            if not isinstance(data, dict):
                current_app.logger.warning(f"Invalid data format for authenticated event: {type(data)}")
                emit('error', {'message': 'INVALID_DATA_FORMAT'})
                return False

            # Extract token from data
            token = data.get('token')

            if not token:
                current_app.logger.warning(f"Authentication attempt without token from {request.sid}")
                emit('error', {'message': 'AUTHENTICATION_REQUIRED'})
                return False

            try:
                # Verify JWT token
                decoded = jwt.decode(
                    token,
                    current_app.config['JWT_SECRET_KEY'],
                    algorithms=['HS256']
                )

                # Extract user_id from token
                user_id = decoded.get('sub')
                if not user_id:
                    current_app.logger.warning(f"Token missing 'sub' claim from {request.sid}")
                    emit('error', {'message': 'INVALID_TOKEN_CLAIMS'})
                    disconnect()
                    return False

                # Add user_id to kwargs
                kwargs['current_user'] = user_id

                current_app.logger.debug(f"WebSocket authenticated: user={user_id}, sid={request.sid}")

                # Call the original function
                return f(self, *args, **kwargs)

            except jwt.ExpiredSignatureError:
                current_app.logger.warning(f"Expired token from {request.sid}")
                emit('error', {'message': 'TOKEN_EXPIRED'})
                disconnect()
                return False

            except jwt.InvalidTokenError as e:
                current_app.logger.warning(f"Invalid token from {request.sid}: {str(e)}")
                emit('error', {'message': 'INVALID_TOKEN'})
                disconnect()
                return False

            except Exception as e:
                current_app.logger.error(f"Authentication error from {request.sid}: {str(e)}", exc_info=True)
                emit('error', {'message': 'AUTHENTICATION_ERROR'})
                disconnect()
                return False

        return wrapped

    @staticmethod
    def validate_data(f: Callable) -> Callable:
        """
        Decorator to validate event data format.

        Ensures data is a dictionary and not empty.
        """
        @wraps(f)
        def wrapped(self, *args, **kwargs):
            data = args[0] if args else {}

            if not isinstance(data, dict):
                current_app.logger.warning(f"Invalid data format from {request.sid}: {type(data)}")
                emit('error', {'message': 'INVALID_DATA_FORMAT'})
                return False

            if not data:
                current_app.logger.warning(f"Empty data payload from {request.sid}")
                emit('error', {'message': 'DATA_REQUIRED'})
                return False

            return f(self, *args, **kwargs)

        return wrapped

    def emit_to_user(self, user_id: str, event: str, data: dict) -> None:
        """
        Emit event to a specific user's personal room.

        Args:
            user_id: Target user ID
            event: Event name
            data: Event data payload
        """
        room = f"user_{user_id}"
        emit(event, data, room=room, namespace=self.namespace)
        current_app.logger.debug(f"Emitted {event} to user {user_id}")

    def emit_to_room(self, room_id: str, event: str, data: dict, include_sender: bool = True) -> None:
        """
        Emit event to a game room.

        Args:
            room_id: Target room ID
            event: Event name
            data: Event data payload
            include_sender: Whether to include the sender in broadcast
        """
        room = f"room_{room_id}"
        if include_sender:
            emit(event, data, room=room, namespace=self.namespace)
        else:
            emit(event, data, room=room, skip_sid=request.sid, namespace=self.namespace)

        current_app.logger.debug(f"Emitted {event} to room {room_id} (include_sender={include_sender})")
