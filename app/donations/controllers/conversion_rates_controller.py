from flask import Blueprint, request, jsonify, current_app
from app.core.utils.decorators import auth_required
from app.core.utils import success_response, error_response
from app.donations.services.credit_calculation_service import CreditCalculationService

# Create blueprint for conversion rates management
rates_bp = Blueprint('conversion_rates', __name__, url_prefix='/api/conversion-rates')

# Initialize services
credit_calc_service = CreditCalculationService()


@rates_bp.route('', methods=['GET'])
@auth_required
def get_conversion_rates(current_user):
    """
    Retrieve current credit conversion rates and active multipliers.
    """
    try:
        success, message, rate_info = credit_calc_service.get_conversion_rate_info()

        if success:
            return success_response(message, rate_info)
        else:
            return error_response(message, status_code=404 if "NOT_AVAILABLE" in message else 500)

    except Exception as e:
        current_app.logger.error(f"Error getting conversion rates: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@rates_bp.route('/calculator', methods=['GET'])
@auth_required
def calculate_credits_estimate(current_user):
    """
    Calculate estimated credits for a given play duration with current rates and multipliers.
    """
    try:
        # Extract query parameters
        duration_minutes = request.args.get('duration_minutes', type=float)
        if duration_minutes is None:
            return error_response("DURATION_MINUTES_REQUIRED", status_code=400)

        if duration_minutes <= 0 or duration_minutes > 1440:  # Max 24 hours
            return error_response("INVALID_DURATION", status_code=400)

        # Extract context parameters for multiplier calculation
        context = {
            'is_tournament_mode': request.args.get('is_tournament', 'false').lower() == 'true',
            'is_challenge_mode': request.args.get('is_challenge', 'false').lower() == 'true',
            'has_daily_streak': request.args.get('has_daily_streak', 'false').lower() == 'true',
            'special_event_active': request.args.get('special_event_active', 'false').lower() == 'true',
            'user_loyalty_level': request.args.get('loyalty_level', 0, type=int),
            'is_first_time_player': request.args.get('is_first_time', 'false').lower() == 'true'
        }

        success, message, estimation = credit_calc_service.estimate_credits_for_duration(
            duration_minutes=duration_minutes,
            context=context
        )

        if success:
            return success_response(message, estimation)
        else:
            return error_response(message, status_code=400)

    except Exception as e:
        current_app.logger.error(f"Error calculating credit estimation: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@rates_bp.route('/multipliers', methods=['GET'])
@auth_required
def get_active_multipliers(current_user):
    """
    Get currently active multipliers for the user based on their context.
    """
    try:
        # Extract context from query parameters or request body
        context = {}

        # Check if context is provided in request body
        if request.content_type == 'application/json':
            data = request.get_json()
            context = data.get('context', {}) if data else {}

        # Also allow context via query parameters
        context.update({
            'is_tournament_mode': request.args.get('is_tournament', 'false').lower() == 'true',
            'is_challenge_mode': request.args.get('is_challenge', 'false').lower() == 'true',
            'has_daily_streak': request.args.get('has_daily_streak', 'false').lower() == 'true',
            'special_event_active': request.args.get('special_event_active', 'false').lower() == 'true',
            'user_loyalty_level': request.args.get('loyalty_level', 0, type=int),
            'is_first_time_player': request.args.get('is_first_time', 'false').lower() == 'true'
        })

        success, message, multiplier_data = credit_calc_service.get_active_multipliers(
            user_id=current_user.get_id(),
            session_context=context
        )

        if success:
            return success_response(message, multiplier_data)
        else:
            return error_response(message, status_code=404 if "NOT_AVAILABLE" in message else 400)

    except Exception as e:
        current_app.logger.error(f"Error getting active multipliers for user {current_user.get_id()}: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@rates_bp.route('/simulation', methods=['POST'])
@auth_required
def simulate_credit_calculation(current_user):
    """
    Simulate credit calculation for various scenarios without affecting the wallet.
    """
    try:
        data = request.get_json()
        if not data:
            return error_response("DATA_REQUIRED", status_code=400)

        scenarios = data.get('scenarios', [])
        if not scenarios or not isinstance(scenarios, list):
            return error_response("SIMULATION_SCENARIOS_REQUIRED", status_code=400)

        results = []

        for i, scenario in enumerate(scenarios):
            if not isinstance(scenario, dict):
                continue

            duration_minutes = scenario.get('duration_minutes')
            if not duration_minutes or duration_minutes <= 0:
                results.append({
                    'scenario_index': i,
                    'error': 'INVALID_DURATION'
                })
                continue

            context = scenario.get('context', {})

            success, message, estimation = credit_calc_service.estimate_credits_for_duration(
                duration_minutes=duration_minutes,
                context=context
            )

            if success:
                estimation['scenario_index'] = i
                estimation['scenario_name'] = scenario.get('name', f'Scenario {i + 1}')
                results.append(estimation)
            else:
                results.append({
                    'scenario_index': i,
                    'scenario_name': scenario.get('name', f'Scenario {i + 1}'),
                    'error': message
                })

        simulation_result = {
            'total_scenarios': len(scenarios),
            'successful_calculations': len([r for r in results if 'error' not in r]),
            'failed_calculations': len([r for r in results if 'error' in r]),
            'results': results
        }

        return success_response("CREDIT_SIMULATION_SUCCESS", simulation_result)

    except Exception as e:
        current_app.logger.error(f"Error running credit simulation: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@rates_bp.route('/breakdown', methods=['POST'])
@auth_required
def get_credit_breakdown(current_user):
    """
    Get detailed breakdown of credit calculation including each multiplier contribution.
    """
    try:
        data = request.get_json()
        if not data:
            return error_response("DATA_REQUIRED", status_code=400)

        duration_minutes = data.get('duration_minutes')
        if not duration_minutes or duration_minutes <= 0:
            return error_response("INVALID_DURATION", status_code=400)

        context = data.get('context', {})

        # Get conversion rate info
        rate_success, rate_message, rate_info = credit_calc_service.get_conversion_rate_info()
        if not rate_success:
            return error_response(rate_message, status_code=404)

        # Get active multipliers
        multiplier_success, multiplier_message, multiplier_data = credit_calc_service.get_active_multipliers(
            user_id=current_user.get_id(),
            session_context=context
        )
        if not multiplier_success:
            return error_response(multiplier_message, status_code=400)

        # Calculate base credits
        base_credits = duration_minutes * rate_info['base_rate_eur_per_minute']

        # Build breakdown
        breakdown = {
            'duration_minutes': duration_minutes,
            'base_rate_eur_per_minute': rate_info['base_rate_eur_per_minute'],
            'base_credits': round(base_credits, 4),
            'active_multipliers': multiplier_data['active_multipliers'],
            'multiplier_breakdown': {},
            'total_multiplier': multiplier_data['total_multiplier'],
            'final_credits': round(base_credits * multiplier_data['total_multiplier'], 2),
            'bonus_credits': round(base_credits * (multiplier_data['total_multiplier'] - 1.0), 2)
        }

        # Calculate contribution of each multiplier
        for multiplier_name in multiplier_data['active_multipliers']:
            multiplier_value = multiplier_data['multiplier_details'].get(multiplier_name, 1.0)
            contribution = (multiplier_value - 1.0) * base_credits
            breakdown['multiplier_breakdown'][multiplier_name] = {
                'multiplier_value': multiplier_value,
                'credit_contribution': round(contribution, 4),
                'percentage_boost': round((multiplier_value - 1.0) * 100, 1)
            }

        return success_response("CREDIT_BREAKDOWN_SUCCESS", breakdown)

    except Exception as e:
        current_app.logger.error(f"Error getting credit breakdown: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@rates_bp.route('/history', methods=['GET'])
@auth_required
def get_rate_history(current_user):
    """
    Get historical conversion rates (placeholder for future implementation).
    """
    try:
        # This would require additional repository methods to get historical rates
        # For now, return a placeholder response

        placeholder_data = {
            'message': 'Historical rates feature not yet implemented',
            'current_rate_info': {}
        }

        # Get current rate info as placeholder
        success, message, rate_info = credit_calc_service.get_conversion_rate_info()
        if success:
            placeholder_data['current_rate_info'] = rate_info

        return success_response("RATE_HISTORY_PLACEHOLDER", placeholder_data)

    except Exception as e:
        current_app.logger.error(f"Error getting rate history: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


# Error handlers for the blueprint
@rates_bp.errorhandler(400)
def bad_request(error):
    return error_response("INVALID_REQUEST", status_code=400)


@rates_bp.errorhandler(401)
def unauthorized(error):
    return error_response("UNAUTHORIZED_ACCESS", status_code=401)


@rates_bp.errorhandler(404)
def not_found(error):
    return error_response("RESOURCE_NOT_FOUND", status_code=404)


@rates_bp.errorhandler(422)
def unprocessable_entity(error):
    return error_response("VALIDATION_ERROR", status_code=422)


@rates_bp.errorhandler(500)
def internal_error(error):
    return error_response("INTERNAL_SERVER_ERROR", status_code=500)