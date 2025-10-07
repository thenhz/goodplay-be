"""
Social-Multiplayer Integration Controller

GOO-60: Endpoints for integrating social features with multiplayer system.
"""

from flask import Blueprint, request, current_app
from app.core.utils.decorators import auth_required
from app.core.utils.responses import success_response, error_response
from app.social.services.relationship_service import RelationshipService
from app.core.utils.helpers import extract_user_id


social_multiplayer_bp = Blueprint('social_multiplayer', __name__)
relationship_service = RelationshipService()

# Lazy initialization to avoid circular imports
_connection_manager = None
_room_manager = None
_invitation_service = None


def get_connection_manager():
    """Lazy load connection manager"""
    global _connection_manager
    if _connection_manager is None:
        from app.games.multiplayer.services.connection_manager import ConnectionManager
        _connection_manager = ConnectionManager.get_instance()
    return _connection_manager


def get_room_manager():
    """Lazy load room manager"""
    global _room_manager
    if _room_manager is None:
        from app.games.multiplayer.services.room_manager import RoomManager
        _room_manager = RoomManager()
    return _room_manager


def get_invitation_service():
    """Lazy load invitation service"""
    global _invitation_service
    if _invitation_service is None:
        from app.games.multiplayer.services.invitation_service import InvitationService
        _invitation_service = InvitationService()
    return _invitation_service


@social_multiplayer_bp.route('/friends/online', methods=['GET'])
@auth_required
def get_online_friends(current_user):
    """
    Get list of online friends.

    GOO-60: Returns friends currently connected to multiplayer system.

    Response:
        {
            "friends": [
                {
                    "user_id": "...",
                    "display_name": "...",
                    "is_in_room": true/false,
                    "room_id": "..." (if in room)
                }
            ],
            "count": <number>
        }
    """
    try:
        user_id = extract_user_id(current_user)

        # Get user's friends list
        success, message, friends_data = relationship_service.get_friends_list(
            user_id, limit=100
        )

        if not success:
            return error_response(message)

        friends_list = friends_data.get('friends', [])

        # Check which friends are online (have active WebSocket sessions)
        online_friends = []
        connection_manager = get_connection_manager()

        for friend in friends_list:
            friend_id = friend['id']

            # Check if friend has active multiplayer session
            sessions = connection_manager.get_user_sessions(friend_id, active_only=True)

            if sessions and len(sessions) > 0:
                # Friend is online
                friend_info = {
                    'user_id': friend_id,
                    'display_name': friend.get('display_name', 'Unknown'),
                    'first_name': friend.get('first_name'),
                    'last_name': friend.get('last_name'),
                    'is_in_room': False,
                    'room_id': None
                }

                # Check if friend is in a room
                session = sessions[0]  # Get first active session
                if session.room_id:
                    friend_info['is_in_room'] = True
                    friend_info['room_id'] = session.room_id

                online_friends.append(friend_info)

        current_app.logger.info(
            f"Found {len(online_friends)} online friends for user {user_id}"
        )

        return success_response("ONLINE_FRIENDS_RETRIEVED", {
            'friends': online_friends,
            'count': len(online_friends)
        })

    except Exception as e:
        current_app.logger.error(f"Error getting online friends: {str(e)}", exc_info=True)
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@social_multiplayer_bp.route('/friends/<friend_id>/current-room', methods=['GET'])
@auth_required
def get_friend_current_room(current_user, friend_id):
    """
    Get friend's current multiplayer room.

    GOO-60: Returns room information if friend is currently in a multiplayer room.

    Response (in room):
        {
            "room": { ... room details ... },
            "is_joinable": true/false,
            "reason": "..." (if not joinable)
        }

    Response (not in room):
        {
            "in_room": false
        }
    """
    try:
        user_id = extract_user_id(current_user)
        friend_id = extract_user_id(friend_id)

        # Verify friendship exists
        # (In production, add validation that they are friends)

        # Get friend's active sessions
        connection_manager = get_connection_manager()
        sessions = connection_manager.get_user_sessions(friend_id, active_only=True)

        if not sessions or len(sessions) == 0:
            return success_response("FRIEND_NOT_ONLINE", {'in_room': False})

        # Check if friend is in a room
        session = sessions[0]
        if not session.room_id:
            return success_response("FRIEND_NOT_IN_ROOM", {'in_room': False})

        # Get room details
        room_manager = get_room_manager()
        room = room_manager.get_room(session.room_id)
        if not room:
            return success_response("FRIEND_NOT_IN_ROOM", {'in_room': False})

        # Check if room is joinable by current user
        is_joinable = True
        reason = None

        if room.status != room.STATUS_WAITING:
            is_joinable = False
            reason = "ROOM_NOT_ACCEPTING_PLAYERS"
        elif room.is_full():
            is_joinable = False
            reason = "ROOM_FULL"
        elif room.has_player(user_id):
            is_joinable = False
            reason = "ALREADY_IN_ROOM"

        return success_response("FRIEND_ROOM_RETRIEVED", {
            'in_room': True,
            'room': room.to_dict(),
            'is_joinable': is_joinable,
            'reason': reason
        })

    except Exception as e:
        current_app.logger.error(f"Error getting friend's room: {str(e)}", exc_info=True)
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@social_multiplayer_bp.route('/friends/<friend_id>/invite-to-room', methods=['POST'])
@auth_required
def invite_friend_to_room(current_user, friend_id):
    """
    Invite a friend to your current multiplayer room.

    GOO-60: Shortcut endpoint for inviting friends to your room.

    Body (optional):
        {
            "room_id": "..." (if not provided, uses current room)
        }

    Response:
        {
            "invitation": { ... invitation details ... }
        }
    """
    try:
        user_id = extract_user_id(current_user)
        friend_id = extract_user_id(friend_id)

        # Verify friendship exists
        # (In production, add validation that they are friends)

        data = request.get_json() or {}
        room_id = data.get('room_id')

        # If no room_id provided, try to get current user's room
        if not room_id:
            connection_manager = get_connection_manager()
            sessions = connection_manager.get_user_sessions(user_id, active_only=True)
            if not sessions or len(sessions) == 0:
                return error_response("NOT_IN_ANY_ROOM")

            session = sessions[0]
            if not session.room_id:
                return error_response("NOT_IN_ANY_ROOM")

            room_id = session.room_id

        # Send invitation using invitation service
        invitation_service = get_invitation_service()
        success, message, invitation = invitation_service.send_invitation(
            room_id, user_id, friend_id
        )

        if success:
            # Emit WebSocket event
            try:
                from app.games.multiplayer.events.connection_events import MultiplayerNamespace
                multiplayer_ns = MultiplayerNamespace()
                multiplayer_ns.emit_invitation_received(
                    friend_id,
                    invitation.to_dict() if invitation else {}
                )
            except Exception as ws_error:
                current_app.logger.warning(f"WebSocket emit failed: {str(ws_error)}")

            return success_response(message, {
                'invitation': invitation.to_dict() if invitation else None
            })
        else:
            return error_response(message, status_code=400)

    except Exception as e:
        current_app.logger.error(f"Error inviting friend to room: {str(e)}", exc_info=True)
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)
