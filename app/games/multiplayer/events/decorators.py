from functools import wraps
from flask_socketio import emit
from flask import request, current_app
from app.games.multiplayer.services.websocket_session_manager import websocket_session_manager


def ws_auth_required(f):
    """
    Decorator to require authentication for WebSocket events.

    Verifies that the session is authenticated before allowing access to the event.
    Automatically injects user_id and session_id into kwargs.

    Usage:
        @ws_auth_required
        def on_my_event(self, data, user_id=None, session_id=None):
            # user_id and session_id are automatically provided
            pass
    """
    @wraps(f)
    def decorated_function(self, *args, **kwargs):
        session_id = request.sid

        # Check if authenticated
        if not websocket_session_manager.is_authenticated(session_id):
            emit('auth_required', {
                'message': 'AUTHENTICATION_REQUIRED',
                'event': f.__name__.replace('on_', '')
            })
            current_app.logger.warning(
                f"Unauthenticated access attempt to {f.__name__} from {session_id}"
            )
            return False

        # Update activity timestamp
        websocket_session_manager.update_activity(session_id)

        # Add user_id and session_id to kwargs
        kwargs['user_id'] = websocket_session_manager.get_user_id(session_id)
        kwargs['session_id'] = session_id

        return f(self, *args, **kwargs)

    return decorated_function


def ws_room_member_required(room_param='room_id'):
    """
    Decorator to verify user is a member of the specified room.

    Checks that the session has joined the room before allowing access.

    Args:
        room_param: Name of the parameter containing the room ID (default: 'room_id')

    Usage:
        @ws_room_member_required()
        def on_send_message(self, data, user_id=None, session_id=None, room_id=None):
            # user is verified to be in the room
            pass

        @ws_room_member_required('game_room')
        def on_game_action(self, data, user_id=None, session_id=None, room_id=None):
            # custom room parameter name
            pass
    """
    def decorator(f):
        @wraps(f)
        @ws_auth_required
        def decorated_function(self, *args, **kwargs):
            session_id = kwargs.get('session_id')
            data = args[0] if args else {}

            # Extract room_id from data
            room_id = data.get(room_param)

            if not room_id:
                emit('error', {
                    'message': 'ROOM_ID_REQUIRED',
                    'event': f.__name__.replace('on_', '')
                })
                return False

            # Check if session is in the room
            if not websocket_session_manager.is_in_room(session_id, room_id):
                emit('error', {
                    'message': 'NOT_IN_ROOM',
                    'room_id': room_id
                })
                current_app.logger.warning(
                    f"User {kwargs.get('user_id')} attempted to access room {room_id} without being a member"
                )
                return False

            # Add room_id to kwargs
            kwargs['room_id'] = room_id

            return f(self, *args, **kwargs)

        return decorated_function
    return decorator


def ws_data_required(*required_fields):
    """
    Decorator to validate required fields in event data.

    Args:
        *required_fields: Names of required fields in the data payload

    Usage:
        @ws_data_required('action', 'target')
        def on_perform_action(self, data, user_id=None):
            # data is guaranteed to have 'action' and 'target' fields
            action = data['action']
            target = data['target']
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(self, *args, **kwargs):
            data = args[0] if args else {}

            # Check for required fields
            missing_fields = [field for field in required_fields if field not in data]

            if missing_fields:
                emit('error', {
                    'message': 'MISSING_REQUIRED_FIELDS',
                    'missing_fields': missing_fields,
                    'event': f.__name__.replace('on_', '')
                })
                return False

            return f(self, *args, **kwargs)

        return decorated_function
    return decorator


def ws_rate_limit(max_calls=10, period_seconds=60):
    """
    Decorator to rate limit WebSocket events per session.

    Args:
        max_calls: Maximum number of calls allowed
        period_seconds: Time period in seconds

    Usage:
        @ws_rate_limit(max_calls=5, period_seconds=10)
        def on_send_message(self, data):
            # Limited to 5 calls per 10 seconds per session
            pass
    """
    from collections import defaultdict
    from time import time

    # Store call timestamps per session
    call_history = defaultdict(list)

    def decorator(f):
        @wraps(f)
        def decorated_function(self, *args, **kwargs):
            session_id = request.sid
            now = time()

            # Clean old timestamps
            call_history[session_id] = [
                ts for ts in call_history[session_id]
                if now - ts < period_seconds
            ]

            # Check rate limit
            if len(call_history[session_id]) >= max_calls:
                emit('rate_limit_exceeded', {
                    'message': 'RATE_LIMIT_EXCEEDED',
                    'max_calls': max_calls,
                    'period_seconds': period_seconds,
                    'retry_after': period_seconds
                })
                current_app.logger.warning(
                    f"Rate limit exceeded for session {session_id} on event {f.__name__}"
                )
                return False

            # Record this call
            call_history[session_id].append(now)

            return f(self, *args, **kwargs)

        return decorated_function
    return decorator
