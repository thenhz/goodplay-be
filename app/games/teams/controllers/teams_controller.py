from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.core.utils.decorators import auth_required, admin_required
from app.core.utils.responses import success_response, error_response

from ..services.team_manager import TeamManager
from ..services.tournament_engine import TournamentEngine

teams_bp = Blueprint('teams', __name__, url_prefix='/api/teams')

team_manager = TeamManager()
tournament_engine = TournamentEngine()

@teams_bp.route('/', methods=['GET'])
def get_all_teams():
    """Get all global teams"""
    try:
        active_only = request.args.get('active_only', 'true').lower() == 'true'

        success, message, data = team_manager.get_all_teams(active_only)

        if success:
            return success_response(message, data)
        else:
            return error_response(message)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@teams_bp.route('/leaderboard', methods=['GET'])
def get_team_leaderboard():
    """Get team leaderboard"""
    try:
        limit = int(request.args.get('limit', 10))

        success, message, data = team_manager.get_team_leaderboard(limit)

        if success:
            return success_response(message, data)
        else:
            return error_response(message)

    except ValueError:
        return error_response("INVALID_LIMIT_VALUE")
    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@teams_bp.route('/my-team', methods=['GET'])
@auth_required
def get_my_team(current_user):
    """Get current user's team"""
    try:
        user_id = current_user.get('id')

        success, message, data = team_manager.get_user_team(user_id)

        if success:
            return success_response(message, data)
        else:
            return error_response(message)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@teams_bp.route('/join', methods=['POST'])
@auth_required
def join_team(current_user):
    """Join a team (auto-assignment or specific team)"""
    try:
        data = request.get_json() or {}
        user_id = current_user.get('id')
        team_id = data.get('team_id')  # Optional - if not provided, auto-assign

        success, message, result = team_manager.assign_user_to_team(user_id, team_id)

        if success:
            return success_response(message, result)
        else:
            return error_response(message, result)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@teams_bp.route('/leave', methods=['POST'])
@auth_required
def leave_team(current_user):
    """Leave current team"""
    try:
        user_id = current_user.get('id')

        success, message, result = team_manager.remove_user_from_team(user_id)

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@teams_bp.route('/<team_id>/members', methods=['GET'])
def get_team_members(team_id):
    """Get team members"""
    try:
        success, message, data = team_manager.get_team_members(team_id)

        if success:
            return success_response(message, data)
        else:
            return error_response(message)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@teams_bp.route('/record-contribution', methods=['POST'])
@auth_required
def record_contribution(current_user):
    """Record a game contribution for the user's team"""
    try:
        data = request.get_json()
        if not data:
            return error_response("DATA_REQUIRED")

        user_id = current_user.get('id')
        score = data.get('score')
        game_type = data.get('game_type', 'individual')

        if score is None:
            return error_response("SCORE_REQUIRED")

        success, message, result = team_manager.record_game_contribution(user_id, score, game_type)

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@teams_bp.route('/record-challenge', methods=['POST'])
@auth_required
def record_challenge_result(current_user):
    """Record a challenge result for the user's team"""
    try:
        data = request.get_json()
        if not data:
            return error_response("DATA_REQUIRED")

        user_id = current_user.get('id')
        challenge_result = data.get('challenge_result')

        if not challenge_result:
            return error_response("CHALLENGE_RESULT_REQUIRED")

        success, message, result = team_manager.record_challenge_result(user_id, challenge_result)

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

# Tournament endpoints

@teams_bp.route('/tournament/current', methods=['GET'])
def get_current_tournament():
    """Get current active tournament"""
    try:
        success, message, data = tournament_engine.get_active_tournament()

        if success:
            return success_response(message, data)
        else:
            return error_response(message)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@teams_bp.route('/tournament/<tournament_id>/leaderboard', methods=['GET'])
def get_tournament_leaderboard(tournament_id):
    """Get tournament leaderboard"""
    try:
        success, message, data = tournament_engine.get_tournament_leaderboard(tournament_id)

        if success:
            return success_response(message, data)
        else:
            return error_response(message)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@teams_bp.route('/tournament/<tournament_id>/statistics', methods=['GET'])
def get_tournament_statistics(tournament_id):
    """Get tournament statistics"""
    try:
        success, message, data = tournament_engine.get_tournament_statistics(tournament_id)

        if success:
            return success_response(message, data)
        else:
            return error_response(message)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

# Admin endpoints

@teams_bp.route('/admin/initialize', methods=['POST'])
@admin_required
def initialize_teams(current_user):
    """Initialize default teams (admin only)"""
    try:
        success, message, data = team_manager.initialize_teams()

        if success:
            return success_response(message, data)
        else:
            return error_response(message)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@teams_bp.route('/admin/balance', methods=['POST'])
@admin_required
def balance_teams(current_user):
    """Balance team members across teams (admin only)"""
    try:
        success, message, data = team_manager.balance_teams()

        if success:
            return success_response(message, data)
        else:
            return error_response(message)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@teams_bp.route('/admin/tournament', methods=['POST'])
@admin_required
def create_tournament(current_user):
    """Create a new tournament (admin only)"""
    try:
        data = request.get_json()
        if not data:
            return error_response("DATA_REQUIRED")

        tournament_type = data.get('tournament_type', 'seasonal_war')
        name = data.get('name')
        duration_days = data.get('duration_days', 30)
        team_ids = data.get('team_ids')
        admin_user_id = current_user.get('id')

        success, message, result = tournament_engine.create_tournament(
            tournament_type=tournament_type,
            name=name,
            duration_days=duration_days,
            team_ids=team_ids,
            admin_user_id=admin_user_id
        )

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@teams_bp.route('/admin/tournament/<tournament_id>/start', methods=['POST'])
@admin_required
def start_tournament(current_user, tournament_id):
    """Start a tournament (admin only)"""
    try:
        data = request.get_json() or {}
        auto_assign_users = data.get('auto_assign_users', True)

        success, message, result = tournament_engine.start_tournament(tournament_id, auto_assign_users)

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@teams_bp.route('/admin/tournament/<tournament_id>/complete', methods=['POST'])
@admin_required
def complete_tournament(current_user, tournament_id):
    """Complete a tournament (admin only)"""
    try:
        success, message, result = tournament_engine.complete_tournament(tournament_id)

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@teams_bp.route('/admin/tournament/<tournament_id>/cancel', methods=['POST'])
@admin_required
def cancel_tournament(current_user, tournament_id):
    """Cancel a tournament (admin only)"""
    try:
        admin_user_id = current_user.get('id')

        success, message, result = tournament_engine.cancel_tournament(tournament_id, admin_user_id)

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)

@teams_bp.route('/admin/tournaments/end-expired', methods=['POST'])
@admin_required
def end_expired_tournaments(current_user):
    """End expired tournaments (admin only)"""
    try:
        success, message, data = tournament_engine.end_expired_tournaments()

        if success:
            return success_response(message, data)
        else:
            return error_response(message)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)