from flask import Blueprint, request, current_app
from app.core.utils.decorators import auth_required
from app.core.utils.responses import success_response, error_response
from app.games.multiplayer.services.room_manager import RoomManager
from app.games.multiplayer.services.connection_manager import ConnectionManager
from app.games.multiplayer.services.state_manager import StateManager
from app.games.multiplayer.services.lobby_service import LobbyService
from app.games.multiplayer.services.invitation_service import InvitationService


blueprint = Blueprint('multiplayer', __name__)

# Initialize services
room_manager = RoomManager()
connection_manager = ConnectionManager.get_instance()
state_manager = StateManager()
lobby_service = LobbyService()
invitation_service = InvitationService()


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


# New GOO-56 endpoints

@blueprint.route('/rooms/search', methods=['POST'])
@auth_required
def search_rooms(current_user):
    """Search rooms with filters"""
    try:
        data = request.get_json() or {}

        success, message, result = lobby_service.browse_rooms(
            game_id=data.get('game_id'),
            privacy=data.get('privacy', 'public'),
            tags=data.get('tags'),
            search_query=data.get('search_query'),
            page=data.get('page', 1),
            per_page=data.get('per_page', 20)
        )

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Error searching rooms: {str(e)}", exc_info=True)
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@blueprint.route('/rooms/<room_id>/ready', methods=['POST'])
@auth_required
def toggle_ready(current_user, room_id):
    """Toggle player ready state"""
    try:
        data = request.get_json() or {}
        is_ready = data.get('is_ready', True)

        success, message, room = room_manager.set_player_ready(
            room_id, current_user, is_ready
        )

        if success:
            return success_response(message, {'room': room.to_dict() if room else None})
        else:
            return error_response(message, status_code=400)

    except Exception as e:
        current_app.logger.error(f"Error toggling ready: {str(e)}", exc_info=True)
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@blueprint.route('/rooms/<room_id>/ready-status', methods=['GET'])
@auth_required
def get_ready_status(current_user, room_id):
    """Get ready status for room"""
    try:
        success, message, status_data = room_manager.get_ready_status(room_id)

        if success:
            return success_response(message, status_data)
        else:
            return error_response(message, status_code=404)

    except Exception as e:
        current_app.logger.error(f"Error getting ready status: {str(e)}", exc_info=True)
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@blueprint.route('/rooms/<room_id>/settings', methods=['PUT'])
@auth_required
def update_room_settings(current_user, room_id):
    """Update room settings (host only)"""
    try:
        data = request.get_json()
        if not data:
            return error_response("DATA_REQUIRED")

        success, message, room = room_manager.update_room_settings(
            room_id, current_user, data
        )

        if success:
            return success_response(message, {'room': room.to_dict() if room else None})
        else:
            return error_response(message, status_code=400)

    except Exception as e:
        current_app.logger.error(f"Error updating settings: {str(e)}", exc_info=True)
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@blueprint.route('/rooms/<room_id>/spectate', methods=['POST'])
@auth_required
def join_as_spectator(current_user, room_id):
    """Join room as spectator"""
    try:
        success, message, room = room_manager.add_spectator(room_id, current_user)

        if success:
            return success_response(message, {'room': room.to_dict() if room else None})
        else:
            return error_response(message, status_code=400)

    except Exception as e:
        current_app.logger.error(f"Error joining as spectator: {str(e)}", exc_info=True)
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@blueprint.route('/rooms/<room_id>/spectate', methods=['DELETE'])
@auth_required
def leave_as_spectator(current_user, room_id):
    """Leave room as spectator"""
    try:
        success, message = room_manager.remove_spectator(room_id, current_user)

        if success:
            return success_response(message)
        else:
            return error_response(message, status_code=400)

    except Exception as e:
        current_app.logger.error(f"Error leaving as spectator: {str(e)}", exc_info=True)
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@blueprint.route('/rooms/<room_id>/invitations', methods=['POST'])
@auth_required
def send_invitation(current_user, room_id):
    """
    Send room invitation(s).

    GOO-60: Supports both single and batch invitations.

    Body (single):
        {"recipient_user_id": "user123"}

    Body (batch):
        {"recipient_ids": ["user1", "user2", "user3"]}
    """
    try:
        from app.games.multiplayer.decorators import rate_limit

        data = request.get_json()
        if not data:
            return error_response("DATA_REQUIRED")

        # Check if batch invitation (recipient_ids) or single (recipient_user_id)
        recipient_ids = data.get('recipient_ids')
        recipient_user_id = data.get('recipient_user_id')

        if recipient_ids and isinstance(recipient_ids, list):
            # Batch invitation - apply rate limiting via decorator
            from app.games.multiplayer.decorators import get_rate_limiter
            rate_limiter = get_rate_limiter()

            from app.core.utils.helpers import extract_user_id
            user_id = extract_user_id(current_user)

            if not rate_limiter.check_limit(user_id, max_calls=10, window=60):
                return error_response("RATE_LIMIT_EXCEEDED", status_code=429)

            success, message, result = invitation_service.send_batch_invitations(
                room_id, current_user, recipient_ids
            )

            if success:
                # Emit WebSocket events for each successful invitation
                try:
                    from app.games.multiplayer.events.connection_events import MultiplayerNamespace
                    multiplayer_ns = MultiplayerNamespace()

                    for sent_inv in result.get('sent', []):
                        multiplayer_ns.emit_invitation_received(
                            sent_inv['recipient_id'],
                            {'invitation_id': sent_inv['invitation_id'], 'room_id': room_id}
                        )
                except Exception as ws_error:
                    current_app.logger.warning(f"WebSocket emit failed: {str(ws_error)}")

                return success_response(message, result)
            else:
                return error_response(message, status_code=400)

        elif recipient_user_id:
            # Single invitation
            success, message, invitation = invitation_service.send_invitation(
                room_id, current_user, recipient_user_id
            )

            if success:
                # Emit WebSocket event
                try:
                    from app.games.multiplayer.events.connection_events import MultiplayerNamespace
                    multiplayer_ns = MultiplayerNamespace()
                    multiplayer_ns.emit_invitation_received(
                        recipient_user_id,
                        invitation.to_dict() if invitation else {}
                    )
                except Exception as ws_error:
                    current_app.logger.warning(f"WebSocket emit failed: {str(ws_error)}")

                return success_response(message, {
                    'invitation': invitation.to_dict() if invitation else None
                })
            else:
                return error_response(message, status_code=400)
        else:
            return error_response("RECIPIENT_USER_ID_OR_IDS_REQUIRED")

    except Exception as e:
        current_app.logger.error(f"Error sending invitation: {str(e)}", exc_info=True)
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@blueprint.route('/invitations', methods=['GET'])
@auth_required
def get_my_invitations(current_user):
    """Get user's invitations"""
    try:
        include_expired = request.args.get('include_expired', 'false').lower() == 'true'

        success, message, invitations = invitation_service.get_user_invitations(
            current_user, include_expired
        )

        if success:
            return success_response(message, {
                'invitations': [inv.to_dict() for inv in invitations],
                'count': len(invitations)
            })
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Error getting invitations: {str(e)}", exc_info=True)
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@blueprint.route('/invitations/<invitation_id>/accept', methods=['POST'])
@auth_required
def accept_invitation(current_user, invitation_id):
    """
    Accept invitation.

    GOO-60: Emits WebSocket event to sender upon acceptance.
    Client MUST call join_room via WebSocket after receiving room_id.
    """
    try:
        success, message, room_id = invitation_service.accept_invitation(
            invitation_id, current_user
        )

        if success:
            # Emit WebSocket event to sender
            try:
                # Get invitation details for sender notification
                invitation = invitation_service.invitation_repository.get_invitation(invitation_id)
                if invitation:
                    from app.games.multiplayer.events.connection_events import MultiplayerNamespace
                    multiplayer_ns = MultiplayerNamespace()
                    multiplayer_ns.emit_invitation_accepted(
                        invitation.sender_user_id,
                        {
                            'invitation_id': invitation_id,
                            'room_id': room_id,
                            'accepted_by': current_user
                        }
                    )
            except Exception as ws_error:
                current_app.logger.warning(f"WebSocket emit failed: {str(ws_error)}")

            # Log warning about client responsibility
            current_app.logger.warning(
                f"⚠️  [ACCEPT_FLOW] Client {current_user} MUST call join_room({room_id}) "
                f"via WebSocket within 30 seconds, or sender will not see player_joined event. "
                f"Frontend should handle this automatically."
            )

            return success_response(message, {
                'room_id': room_id,
                'next_step': 'CALL_JOIN_ROOM_VIA_WEBSOCKET',  # Hint for frontend
                'timeout_seconds': 30  # Expected timeout
            })
        else:
            return error_response(message, status_code=400)

    except Exception as e:
        current_app.logger.error(
            f"❌ [ACCEPT_FLOW] Error accepting invitation: {str(e)}",
            exc_info=True
        )
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@blueprint.route('/invitations/<invitation_id>/decline', methods=['POST'])
@auth_required
def decline_invitation(current_user, invitation_id):
    """
    Decline invitation.

    GOO-60: Emits WebSocket event to sender upon decline.
    """
    try:
        # Get invitation details before declining for sender notification
        invitation = invitation_service.invitation_repository.get_invitation(invitation_id)

        success, message = invitation_service.decline_invitation(
            invitation_id, current_user
        )

        if success:
            # Emit WebSocket event to sender
            try:
                if invitation:
                    from app.games.multiplayer.events.connection_events import MultiplayerNamespace
                    multiplayer_ns = MultiplayerNamespace()
                    multiplayer_ns.emit_invitation_declined(
                        invitation.sender_user_id,
                        {
                            'invitation_id': invitation_id,
                            'declined_by': current_user
                        }
                    )
            except Exception as ws_error:
                current_app.logger.warning(f"WebSocket emit failed: {str(ws_error)}")

            return success_response(message)
        else:
            return error_response(message, status_code=400)

    except Exception as e:
        current_app.logger.error(f"Error declining invitation: {str(e)}", exc_info=True)
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@blueprint.route('/invitations/<invitation_id>', methods=['DELETE'])
@auth_required
def cancel_invitation(current_user, invitation_id):
    """
    Cancel/delete invitation (sender only).

    GOO-60: Allow sender to cancel their sent invitations.
    """
    try:
        success, message = invitation_service.cancel_invitation(
            invitation_id, current_user
        )

        if success:
            return success_response(message)
        else:
            return error_response(message, status_code=400)

    except Exception as e:
        current_app.logger.error(f"Error canceling invitation: {str(e)}", exc_info=True)
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@blueprint.route('/quick-match', methods=['POST'])
@auth_required
def quick_match(current_user):
    """Quick match - find and join best available room"""
    try:
        data = request.get_json()
        if not data or not data.get('game_id'):
            return error_response("GAME_ID_REQUIRED")

        success, message, room = lobby_service.quick_match(
            current_user, data['game_id']
        )

        if success:
            return success_response(message, {'room': room.to_dict() if room else None})
        else:
            return error_response(message, status_code=404)

    except Exception as e:
        current_app.logger.error(f"Error in quick match: {str(e)}", exc_info=True)
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@blueprint.route('/lobby', methods=['GET'])
@auth_required
def get_lobby_data(current_user):
    """Get lobby data with statistics"""
    try:
        game_id = request.args.get('game_id')

        stats = lobby_service.get_lobby_statistics(game_id)

        success, message, rooms = lobby_service.get_recommended_rooms(
            current_user, game_id, limit=10
        )

        return success_response("LOBBY_DATA_RETRIEVED", {
            'statistics': stats,
            'recommended_rooms': [room.to_dict() for room in rooms]
        })

    except Exception as e:
        current_app.logger.error(f"Error getting lobby data: {str(e)}", exc_info=True)
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)
