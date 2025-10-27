"""
Game Actions Controller

REST API endpoints for game actions, synchronization, results, and polling.
"""

from flask import Blueprint, request, current_app
from datetime import datetime, timezone, timedelta
from app.core.utils.decorators import auth_required
from app.core.utils.responses import success_response, error_response
from app.games.multiplayer.repositories.game_action_repository import GameActionRepository
from app.games.multiplayer.models.game_action import GameAction
from app.games.multiplayer.services.room_manager import RoomManager
from app.games.multiplayer.services.state_manager import StateManager
from app.core.utils.helpers import extract_user_id


blueprint = Blueprint('game_actions', __name__)

# Initialize repositories and services
action_repository = GameActionRepository()
room_manager = RoomManager()
state_manager = StateManager()


@blueprint.route('/rooms/<room_id>/actions', methods=['POST'])
@auth_required
def send_action(current_user, room_id):
    """
    Send a game action (REST endpoint).

    Request body:
        {
            "action_id": "timestamp_microsecond",
            "type": "move" | "stateUpdate" | "chat" | "pause" | "resume" | "surrender" | "rematch",
            "player_id": "uuid",
            "payload": { ... },
            "timestamp": "2025-01-27T10:05:00.123Z",
            "sequence_number": 42
        }

    Response:
        {
            "success": true,
            "message": "ACTION_PROCESSED",
            "data": {
                "action_id": "...",
                "acknowledged": true
            }
        }
    """
    try:
        data = request.get_json()

        if not data:
            return error_response("DATA_REQUIRED")

        # Validate required fields
        if "type" not in data or "payload" not in data:
            return error_response("ACTION_TYPE_AND_PAYLOAD_REQUIRED")

        # Extract user ID
        user_id = extract_user_id(current_user)

        # Get room to validate membership
        room = room_manager.get_room(room_id)
        if not room:
            return error_response("ROOM_NOT_FOUND", status_code=404)

        # Verify user is in room
        if user_id not in room.player_ids:
            return error_response("NOT_IN_ROOM", status_code=403)

        # Get or generate sequence number
        sequence_number = data.get("sequence_number")
        if not sequence_number:
            sequence_number = action_repository.get_latest_sequence_number(room_id) + 1

        # Create action
        action = GameAction(
            room_id=room_id,
            user_id=user_id,
            action_type=data["type"],
            payload=data["payload"],
            timestamp=datetime.fromisoformat(data["timestamp"].replace('Z', '+00:00')) if "timestamp" in data else datetime.now(timezone.utc),
            sequence_number=sequence_number,
            action_id=data.get("action_id")
        )

        # TODO: Validate action using plugin validator
        # For now, mark all as valid
        action.is_valid = True
        action.validation_message = "MOVE_VALID"

        # Save action
        action_repository.save_action(action)

        # Broadcast via WebSocket
        try:
            from app.games.multiplayer.events.connection_events import MultiplayerNamespace
            multiplayer_ns = MultiplayerNamespace()
            multiplayer_ns.emit_game_action(room_id, action.to_api_dict())
        except Exception as ws_error:
            current_app.logger.warning(f"WebSocket broadcast failed: {str(ws_error)}")

        return success_response("ACTION_PROCESSED", {
            "action_id": action.action_id,
            "acknowledged": True,
            "sequence_number": action.sequence_number
        })

    except Exception as e:
        current_app.logger.error(f"Error processing action: {str(e)}", exc_info=True)
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@blueprint.route('/rooms/<room_id>/sync', methods=['POST'])
@auth_required
def sync_state(current_user, room_id):
    """
    Synchronize game state.

    Request body:
        {
            "game_state": { ... },
            "sync_version": 6
        }

    Response:
        {
            "data": {
                "game_state": {...},
                "sync_version": 6
            }
        }
    """
    try:
        data = request.get_json()

        if not data or "game_state" not in data:
            return error_response("GAME_STATE_REQUIRED")

        user_id = extract_user_id(current_user)

        # Get room
        room = room_manager.get_room(room_id)
        if not room:
            return error_response("ROOM_NOT_FOUND", status_code=404)

        # Verify user is in room
        if user_id not in room.player_ids:
            return error_response("NOT_IN_ROOM", status_code=403)

        # Get current sync version
        sync_version = data.get("sync_version", 0)

        # Get or create player state
        player_state = state_manager.get_player_state(room_id, user_id)

        if not player_state:
            # Create new state
            player_state = state_manager.create_player_state(
                room_id=room_id,
                user_id=user_id,
                game_state=data["game_state"]
            )
        else:
            # Update existing state
            state_manager.update_player_state(
                room_id=room_id,
                user_id=user_id,
                game_state=data["game_state"],
                sync_version=sync_version
            )

        # Return authoritative state
        return success_response("STATE_SYNCED", {
            "game_state": data["game_state"],
            "sync_version": sync_version + 1
        })

    except Exception as e:
        current_app.logger.error(f"Error syncing state: {str(e)}", exc_info=True)
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@blueprint.route('/rooms/<room_id>/result', methods=['POST'])
@auth_required
def submit_result(current_user, room_id):
    """
    Submit match result.

    Request body:
        {
            "result_type": "win" | "draw" | "abandoned",
            "winner_id": "uuid" | null,
            "player_scores": [
                {
                    "player_id": "uuid",
                    "score": 150,
                    "rank": 1,
                    "stats": { ... }
                }
            ],
            "duration_ms": 180000
        }

    Response:
        {
            "success": true,
            "message": "RESULT_SAVED",
            "data": {
                "result_id": "..."
            }
        }
    """
    try:
        data = request.get_json()

        if not data or "result_type" not in data:
            return error_response("RESULT_TYPE_REQUIRED")

        user_id = extract_user_id(current_user)

        # Get room
        room = room_manager.get_room(room_id)
        if not room:
            return error_response("ROOM_NOT_FOUND", status_code=404)

        # Only host can submit results
        if room.host_user_id != user_id:
            return error_response("ONLY_HOST_CAN_SUBMIT_RESULT", status_code=403)

        # TODO: Save result to database and calculate credits
        # For now, just acknowledge

        return success_response("RESULT_SAVED", {
            "result_id": room_id,
            "result_type": data["result_type"]
        })

    except Exception as e:
        current_app.logger.error(f"Error submitting result: {str(e)}", exc_info=True)
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@blueprint.route('/poll', methods=['GET'])
@auth_required
def poll_events(current_user):
    """
    Poll for events (REST fallback when WebSocket unavailable).

    Query params:
        - room_id: string
        - player_id: string
        - since: number (timestamp milliseconds)

    Response:
        {
            "data": {
                "messages": [
                    {
                        "type": "game:action",
                        "payload": {...},
                        "timestamp": 1706353200123
                    }
                ]
            }
        }
    """
    try:
        room_id = request.args.get('room_id')
        since_str = request.args.get('since')

        if not room_id:
            return error_response("ROOM_ID_REQUIRED")

        user_id = extract_user_id(current_user)

        # Verify user is in room
        room = room_manager.get_room(room_id)
        if not room or user_id not in room.player_ids:
            return error_response("NOT_IN_ROOM", status_code=403)

        # Parse since timestamp
        if since_str:
            since_ms = int(since_str)
            since_dt = datetime.fromtimestamp(since_ms / 1000, tz=timezone.utc)
        else:
            # Default to last 10 seconds
            since_dt = datetime.now(timezone.utc) - timedelta(seconds=10)

        # Get actions since timestamp
        actions = action_repository.get_actions_since(room_id, since_dt)

        # Format as messages
        messages = []
        for action in actions:
            messages.append({
                "type": f"game:{action.action_type}",
                "payload": action.payload,
                "timestamp": int(action.timestamp.timestamp() * 1000),
                "user_id": action.user_id,
                "sequence_number": action.sequence_number
            })

        return success_response("EVENTS_RETRIEVED", {
            "messages": messages,
            "count": len(messages)
        })

    except Exception as e:
        current_app.logger.error(f"Error polling events: {str(e)}", exc_info=True)
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)
