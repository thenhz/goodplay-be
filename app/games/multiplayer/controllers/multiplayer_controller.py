from flask import Blueprint, request, current_app
from app.core.utils.decorators import auth_required
from app.core.utils.responses import success_response, error_response
from app.games.multiplayer.services.room_manager import RoomManager
from app.games.multiplayer.services.connection_manager import ConnectionManager
from app.games.multiplayer.services.state_manager import StateManager


blueprint = Blueprint('multiplayer', __name__)

# Initialize services
room_manager = RoomManager()
connection_manager = ConnectionManager.get_instance()
state_manager = StateManager()


@blueprint.route('/rooms', methods=['POST'])
@auth_required
def create_room(current_user):
    """
    Create a new multiplayer game room.

    Request body:
        {
            "game_id": "game_123",
            "max_players": 8,
            "game_config": { ... }
        }

    Response:
        {
            "room": { ... room data ... },
            "message": "ROOM_CREATED_SUCCESS"
        }
    """
    try:
        data = request.get_json()

        if not data:
            return error_response("DATA_REQUIRED")

        game_id = data.get('game_id')
        if not game_id:
            return error_response("GAME_ID_REQUIRED")

        max_players = data.get('max_players', 8)
        game_config = data.get('game_config', {})

        success, message, room = room_manager.create_room(
            game_id=game_id,
            host_user_id=current_user,
            max_players=max_players,
            game_config=game_config
        )

        if success:
            return success_response(message, {'room': room.to_dict()})
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Error creating room: {str(e)}", exc_info=True)
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@blueprint.route('/rooms/<room_id>', methods=['GET'])
@auth_required
def get_room(current_user, room_id):
    """
    Get room details.

    Response:
        {
            "room": { ... room data ... },
            "message": "ROOM_RETRIEVED_SUCCESS"
        }
    """
    try:
        room = room_manager.get_room(room_id)

        if not room:
            return error_response("ROOM_NOT_FOUND", status_code=404)

        return success_response("ROOM_RETRIEVED_SUCCESS", {'room': room.to_dict()})

    except Exception as e:
        current_app.logger.error(f"Error getting room: {str(e)}", exc_info=True)
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@blueprint.route('/rooms/code/<room_code>', methods=['GET'])
@auth_required
def get_room_by_code(current_user, room_code):
    """
    Get room by code.

    Response:
        {
            "room": { ... room data ... },
            "message": "ROOM_RETRIEVED_SUCCESS"
        }
    """
    try:
        room = room_manager.get_room_by_code(room_code)

        if not room:
            return error_response("ROOM_NOT_FOUND", status_code=404)

        return success_response("ROOM_RETRIEVED_SUCCESS", {'room': room.to_dict()})

    except Exception as e:
        current_app.logger.error(f"Error getting room by code: {str(e)}", exc_info=True)
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@blueprint.route('/rooms/<room_id>/join', methods=['POST'])
@auth_required
def join_room(current_user, room_id):
    """
    Join a game room (REST API endpoint, also handled via WebSocket).

    Response:
        {
            "room": { ... room data ... },
            "message": "PLAYER_JOINED_SUCCESS"
        }
    """
    try:
        success, message, room = room_manager.join_room(room_id, current_user)

        if success:
            return success_response(message, {'room': room.to_dict()})
        else:
            return error_response(message, status_code=400)

    except Exception as e:
        current_app.logger.error(f"Error joining room: {str(e)}", exc_info=True)
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@blueprint.route('/rooms/<room_id>/leave', methods=['POST'])
@auth_required
def leave_room(current_user, room_id):
    """
    Leave a game room (REST API endpoint, also handled via WebSocket).

    Response:
        {
            "room": { ... room data ... },
            "message": "PLAYER_LEFT_SUCCESS"
        }
    """
    try:
        success, message, room = room_manager.leave_room(room_id, current_user)

        if success:
            return success_response(message, {'room': room.to_dict() if room else None})
        else:
            return error_response(message, status_code=400)

    except Exception as e:
        current_app.logger.error(f"Error leaving room: {str(e)}", exc_info=True)
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@blueprint.route('/rooms/<room_id>/start', methods=['POST'])
@auth_required
def start_game(current_user, room_id):
    """
    Start the game (host only).

    Response:
        {
            "room": { ... room data ... },
            "message": "GAME_STARTED_SUCCESS"
        }
    """
    try:
        success, message, room = room_manager.start_game(room_id, current_user)

        if success:
            return success_response(message, {'room': room.to_dict()})
        else:
            return error_response(message, status_code=400)

    except Exception as e:
        current_app.logger.error(f"Error starting game: {str(e)}", exc_info=True)
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@blueprint.route('/rooms/available', methods=['GET'])
@auth_required
def get_available_rooms(current_user):
    """
    Get available rooms (waiting and not full).

    Query params:
        - game_id (optional): Filter by game ID
        - limit (optional): Maximum number of rooms (default: 20)

    Response:
        {
            "rooms": [ ... array of room data ... ],
            "count": <number>,
            "message": "ROOMS_RETRIEVED_SUCCESS"
        }
    """
    try:
        game_id = request.args.get('game_id')
        limit = int(request.args.get('limit', 20))

        rooms = room_manager.get_available_rooms(game_id, limit)

        return success_response("ROOMS_RETRIEVED_SUCCESS", {
            'rooms': [room.to_dict() for room in rooms],
            'count': len(rooms)
        })

    except Exception as e:
        current_app.logger.error(f"Error getting available rooms: {str(e)}", exc_info=True)
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@blueprint.route('/rooms/my-rooms', methods=['GET'])
@auth_required
def get_my_rooms(current_user):
    """
    Get rooms where current user is a player.

    Response:
        {
            "rooms": [ ... array of room data ... ],
            "count": <number>,
            "message": "ROOMS_RETRIEVED_SUCCESS"
        }
    """
    try:
        rooms = room_manager.get_user_rooms(current_user)

        return success_response("ROOMS_RETRIEVED_SUCCESS", {
            'rooms': [room.to_dict() for room in rooms],
            'count': len(rooms)
        })

    except Exception as e:
        current_app.logger.error(f"Error getting user rooms: {str(e)}", exc_info=True)
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@blueprint.route('/rooms/<room_id>/state', methods=['GET'])
@auth_required
def get_room_state(current_user, room_id):
    """
    Get player states for a room.

    Response:
        {
            "states": [ ... array of player states ... ],
            "statistics": { ... room statistics ... },
            "message": "ROOM_STATE_RETRIEVED"
        }
    """
    try:
        states = state_manager.get_room_states(room_id)
        statistics = state_manager.get_room_statistics(room_id)

        return success_response("ROOM_STATE_RETRIEVED", {
            'states': [state.to_dict() for state in states],
            'statistics': statistics
        })

    except Exception as e:
        current_app.logger.error(f"Error getting room state: {str(e)}", exc_info=True)
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@blueprint.route('/sessions/active', methods=['GET'])
@auth_required
def get_active_sessions(current_user):
    """
    Get active WebSocket sessions for current user.

    Response:
        {
            "sessions": [ ... array of session data ... ],
            "count": <number>,
            "message": "SESSIONS_RETRIEVED_SUCCESS"
        }
    """
    try:
        sessions = connection_manager.get_user_sessions(current_user, active_only=True)

        return success_response("SESSIONS_RETRIEVED_SUCCESS", {
            'sessions': [session.to_dict() for session in sessions],
            'count': len(sessions)
        })

    except Exception as e:
        current_app.logger.error(f"Error getting sessions: {str(e)}", exc_info=True)
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@blueprint.route('/statistics', methods=['GET'])
@auth_required
def get_statistics(current_user):
    """
    Get multiplayer statistics.

    Response:
        {
            "connections": { ... connection stats ... },
            "rooms": { ... room stats ... },
            "message": "STATISTICS_RETRIEVED"
        }
    """
    try:
        connection_stats = connection_manager.get_statistics()
        room_stats = room_manager.get_statistics()

        return success_response("STATISTICS_RETRIEVED", {
            'connections': connection_stats,
            'rooms': room_stats
        })

    except Exception as e:
        current_app.logger.error(f"Error getting statistics: {str(e)}", exc_info=True)
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)
