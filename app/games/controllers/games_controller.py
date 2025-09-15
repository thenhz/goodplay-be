from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.core.decorators import auth_required, admin_required
from app.core.utils.responses import success_response, error_response

from ..services.game_service import GameService
from ..services.game_session_service import GameSessionService

games_bp = Blueprint('games', __name__, url_prefix='/api/games')

game_service = GameService()
session_service = GameSessionService()

@games_bp.route('/', methods=['GET'])
def get_games():
    """Get all available games with pagination and filtering"""
    try:
        # Get query parameters
        active_only = request.args.get('active_only', 'true').lower() == 'true'
        category = request.args.get('category')
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        sort_by = request.args.get('sort_by', 'created_at')

        # Validate parameters
        if page < 1:
            return error_response("INVALID_PAGE_NUMBER")

        if limit < 1 or limit > 100:
            return error_response("INVALID_LIMIT_VALUE")

        allowed_sort_fields = ['created_at', 'rating', 'install_count', 'name']
        if sort_by not in allowed_sort_fields:
            return error_response("INVALID_SORT_FIELD")

        success, message, data = game_service.get_all_games(
            active_only=active_only,
            category=category,
            page=page,
            limit=limit,
            sort_by=sort_by
        )

        if success:
            return success_response(message, data)
        else:
            return error_response(message)

    except ValueError:
        return error_response("INVALID_QUERY_PARAMETERS")
    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@games_bp.route('/<game_id>', methods=['GET'])
def get_game(game_id):
    """Get detailed information about a specific game"""
    try:
        success, message, data = game_service.get_game_info(game_id)

        if success:
            return success_response(message, data)
        else:
            return error_response(message, status_code=404 if message == "GAME_NOT_FOUND" else 400)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@games_bp.route('/search', methods=['GET'])
def search_games():
    """Search games by name or description"""
    try:
        query = request.args.get('q', '').strip()
        active_only = request.args.get('active_only', 'true').lower() == 'true'

        if not query:
            return error_response("SEARCH_QUERY_REQUIRED")

        success, message, data = game_service.search_games(query, active_only)

        if success:
            return success_response(message, data)
        else:
            return error_response(message)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@games_bp.route('/categories', methods=['GET'])
def get_game_categories():
    """Get available game categories"""
    try:
        success, message, data = game_service.get_game_categories()

        if success:
            return success_response(message, data)
        else:
            return error_response(message)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@games_bp.route('/stats', methods=['GET'])
def get_games_stats():
    """Get games statistics"""
    try:
        success, message, data = game_service.get_games_stats()

        if success:
            return success_response(message, data)
        else:
            return error_response(message)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@games_bp.route('/install', methods=['POST'])
@admin_required
def install_game_plugin():
    """Install a new game plugin (admin only)"""
    try:
        # Check if file is present
        if 'plugin_file' not in request.files:
            return error_response("PLUGIN_FILE_REQUIRED")

        plugin_file = request.files['plugin_file']
        if plugin_file.filename == '':
            return error_response("PLUGIN_FILE_REQUIRED")

        # Get optional plugin ID
        plugin_id = request.form.get('plugin_id')

        # Read file data
        plugin_data = plugin_file.read()
        if not plugin_data:
            return error_response("PLUGIN_FILE_EMPTY")

        success, message, data = game_service.install_game_plugin(plugin_data, plugin_id)

        if success:
            return success_response(message, data, status_code=201)
        else:
            return error_response(message)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@games_bp.route('/<game_id>/uninstall', methods=['DELETE'])
@admin_required
def uninstall_game_plugin(game_id):
    """Uninstall a game plugin (admin only)"""
    try:
        success, message, data = game_service.uninstall_game_plugin(game_id)

        if success:
            return success_response(message, data)
        else:
            return error_response(message, status_code=404 if message == "GAME_NOT_FOUND" else 400)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@games_bp.route('/<game_id>/validate', methods=['POST'])
@admin_required
def validate_game_plugin(game_id):
    """Validate a game plugin (admin only)"""
    try:
        success, message, data = game_service.validate_game_plugin(game_id)

        if success:
            return success_response(message, data)
        else:
            return error_response(message, status_code=404 if message == "GAME_NOT_FOUND" else 400)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@games_bp.route('/<game_id>/rate', methods=['POST'])
@auth_required
def rate_game(current_user, game_id):
    """Rate a game (authenticated users only)"""
    try:
        data = request.get_json()
        if not data or 'rating' not in data:
            return error_response("RATING_REQUIRED")

        rating = data['rating']
        if not isinstance(rating, (int, float)) or not (1.0 <= rating <= 5.0):
            return error_response("INVALID_RATING_VALUE")

        success, message, result = game_service.rate_game(game_id, float(rating))

        if success:
            return success_response(message, result)
        else:
            return error_response(message, status_code=404 if message == "GAME_NOT_FOUND" else 400)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

# Game Session Endpoints

@games_bp.route('/<game_id>/sessions', methods=['POST'])
@auth_required
def start_game_session(current_user, game_id):
    """Start a new game session"""
    try:
        user_id = str(current_user['_id'])
        data = request.get_json() or {}
        session_config = data.get('session_config', {})

        success, message, result = session_service.start_game_session(
            user_id, game_id, session_config
        )

        if success:
            return success_response(message, result, status_code=201)
        else:
            return error_response(message, status_code=404 if "NOT_FOUND" in message else 400)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@games_bp.route('/sessions/<session_id>', methods=['GET'])
@auth_required
def get_game_session(current_user, session_id):
    """Get a game session by ID"""
    try:
        success, message, data = session_service.get_session_by_id(session_id)

        if success:
            # Check if user owns this session
            user_id = str(current_user['_id'])
            if data['session']['user_id'] != user_id:
                return error_response("SESSION_ACCESS_DENIED", status_code=403)

            return success_response(message, data)
        else:
            return error_response(message, status_code=404 if message == "SESSION_NOT_FOUND" else 400)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@games_bp.route('/sessions/<session_id>/end', methods=['PUT'])
@auth_required
def end_game_session(current_user, session_id):
    """End a game session"""
    try:
        data = request.get_json() or {}
        reason = data.get('reason', 'completed')

        if reason not in ['completed', 'abandoned']:
            return error_response("INVALID_END_REASON")

        # First check if user owns this session
        success, message, session_data = session_service.get_session_by_id(session_id)
        if not success:
            return error_response(message, status_code=404 if message == "SESSION_NOT_FOUND" else 400)

        user_id = str(current_user['_id'])
        if session_data['session']['user_id'] != user_id:
            return error_response("SESSION_ACCESS_DENIED", status_code=403)

        success, message, result = session_service.end_game_session(session_id, reason)

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@games_bp.route('/sessions/<session_id>/state', methods=['PUT'])
@auth_required
def update_session_state(current_user, session_id):
    """Update the state of a game session"""
    try:
        data = request.get_json()
        if not data or 'state' not in data:
            return error_response("SESSION_STATE_REQUIRED")

        # First check if user owns this session
        success, message, session_data = session_service.get_session_by_id(session_id)
        if not success:
            return error_response(message, status_code=404 if message == "SESSION_NOT_FOUND" else 400)

        user_id = str(current_user['_id'])
        if session_data['session']['user_id'] != user_id:
            return error_response("SESSION_ACCESS_DENIED", status_code=403)

        success, message, result = session_service.update_session_state(session_id, data['state'])

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@games_bp.route('/sessions/<session_id>/moves', methods=['POST'])
@auth_required
def validate_move(current_user, session_id):
    """Validate and record a move in a game session"""
    try:
        data = request.get_json()
        if not data or 'move' not in data:
            return error_response("MOVE_DATA_REQUIRED")

        # First check if user owns this session
        success, message, session_data = session_service.get_session_by_id(session_id)
        if not success:
            return error_response(message, status_code=404 if message == "SESSION_NOT_FOUND" else 400)

        user_id = str(current_user['_id'])
        if session_data['session']['user_id'] != user_id:
            return error_response("SESSION_ACCESS_DENIED", status_code=403)

        success, message, result = session_service.validate_move(session_id, data['move'])

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@games_bp.route('/sessions/<session_id>/pause', methods=['PUT'])
@auth_required
def pause_session(current_user, session_id):
    """Pause a game session"""
    try:
        # First check if user owns this session
        success, message, session_data = session_service.get_session_by_id(session_id)
        if not success:
            return error_response(message, status_code=404 if message == "SESSION_NOT_FOUND" else 400)

        user_id = str(current_user['_id'])
        if session_data['session']['user_id'] != user_id:
            return error_response("SESSION_ACCESS_DENIED", status_code=403)

        success, message, result = session_service.pause_session(session_id)

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@games_bp.route('/sessions/<session_id>/resume', methods=['PUT'])
@auth_required
def resume_session(current_user, session_id):
    """Resume a paused game session"""
    try:
        # First check if user owns this session
        success, message, session_data = session_service.get_session_by_id(session_id)
        if not success:
            return error_response(message, status_code=404 if message == "SESSION_NOT_FOUND" else 400)

        user_id = str(current_user['_id'])
        if session_data['session']['user_id'] != user_id:
            return error_response("SESSION_ACCESS_DENIED", status_code=403)

        success, message, result = session_service.resume_session(session_id)

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

# User session endpoints

@games_bp.route('/sessions', methods=['GET'])
@auth_required
def get_user_sessions(current_user):
    """Get sessions for the current user"""
    try:
        user_id = str(current_user['_id'])
        status = request.args.get('status')
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))

        if page < 1:
            return error_response("INVALID_PAGE_NUMBER")

        if limit < 1 or limit > 100:
            return error_response("INVALID_LIMIT_VALUE")

        success, message, data = session_service.get_user_sessions(user_id, status, page, limit)

        if success:
            return success_response(message, data)
        else:
            return error_response(message)

    except ValueError:
        return error_response("INVALID_QUERY_PARAMETERS")
    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@games_bp.route('/sessions/stats', methods=['GET'])
@auth_required
def get_user_session_stats(current_user):
    """Get session statistics for the current user"""
    try:
        user_id = str(current_user['_id'])

        success, message, data = session_service.get_user_session_stats(user_id)

        if success:
            return success_response(message, data)
        else:
            return error_response(message)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)