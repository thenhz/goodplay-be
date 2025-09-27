from flask import Blueprint, request, jsonify, current_app
from app.core.utils.decorators import auth_required
from app.core.utils import success_response, error_response
from app.donations.services.wallet_service import WalletService
from app.donations.services.credit_calculation_service import CreditCalculationService

# Create blueprint for wallet management
wallet_bp = Blueprint('wallet', __name__, url_prefix='/api/wallet')

# Initialize services
wallet_service = WalletService()
credit_calc_service = CreditCalculationService()


@wallet_bp.route('', methods=['GET'])
@auth_required
def get_wallet(current_user):
    """
    Get user's wallet information including balance and statistics.
    """
    try:
        success, message, wallet_data = wallet_service.get_wallet(current_user.get_id())

        if success:
            return success_response(message, wallet_data)
        else:
            return error_response(message, status_code=404 if "NOT_FOUND" in message else 400)

    except Exception as e:
        current_app.logger.error(f"Error getting wallet for user {current_user.get_id()}: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@wallet_bp.route('/transactions', methods=['GET'])
@auth_required
def get_transaction_history(current_user):
    """
    Get user's transaction history with pagination and filtering.
    """
    try:
        # Extract query parameters
        page = request.args.get('page', 1, type=int)
        page_size = min(request.args.get('page_size', 20, type=int), 100)  # Max 100 per page
        transaction_type = request.args.get('transaction_type')
        status = request.args.get('status')
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')

        # Build filters
        filters = {}
        if transaction_type:
            filters['transaction_type'] = transaction_type
        if status:
            filters['status'] = status
        filters['sort_by'] = sort_by
        filters['sort_order'] = sort_order

        success, message, history_data = wallet_service.get_transaction_history(
            user_id=current_user.get_id(),
            filters=filters,
            page=page,
            page_size=page_size
        )

        if success:
            return success_response(message, history_data)
        else:
            return error_response(message, status_code=400)

    except Exception as e:
        current_app.logger.error(f"Error getting transaction history for user {current_user.get_id()}: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@wallet_bp.route('/statistics', methods=['GET'])
@auth_required
def get_wallet_statistics(current_user):
    """
    Get comprehensive wallet statistics and analytics.
    """
    try:
        success, message, statistics = wallet_service.get_wallet_statistics(current_user.get_id())

        if success:
            return success_response(message, statistics)
        else:
            return error_response(message, status_code=404 if "NOT_FOUND" in message else 400)

    except Exception as e:
        current_app.logger.error(f"Error getting wallet statistics for user {current_user.get_id()}: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@wallet_bp.route('/convert-session', methods=['POST'])
@auth_required
def convert_session_to_credits(current_user):
    """
    Convert a completed game session to wallet credits using current conversion rates.
    """
    try:
        data = request.get_json()
        if not data:
            return error_response("DATA_REQUIRED", status_code=400)

        # Validate required fields
        required_fields = ['session_id', 'play_duration_ms', 'game_id']
        for field in required_fields:
            if field not in data:
                return error_response(f"SESSION_{field.upper()}_REQUIRED", status_code=400)

        # Build session data
        session_data = {
            'user_id': current_user.get_id(),
            'session_id': data['session_id'],
            'play_duration_ms': data['play_duration_ms'],
            'game_id': data['game_id'],
            'game_mode': data.get('game_mode', 'normal')
        }

        # Extract user context
        user_context = data.get('user_context', {})
        user_context['user_id'] = current_user.get_id()

        success, message, result = wallet_service.convert_session_to_credits(
            session_data=session_data,
            user_context=user_context
        )

        if success:
            return success_response(message, result)
        else:
            status_code = 400
            if "FRAUD_DETECTION" in message:
                status_code = 422  # Unprocessable Entity
            return error_response(message, status_code=status_code)

    except Exception as e:
        current_app.logger.error(f"Error converting session to credits for user {current_user.get_id()}: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@wallet_bp.route('/auto-donation', methods=['PUT'])
@auth_required
def update_auto_donation_settings(current_user):
    """
    Configure automatic donation settings for the user's wallet.
    """
    try:
        data = request.get_json()
        if not data:
            return error_response("DATA_REQUIRED", status_code=400)

        # Validate auto-donation settings
        if 'enabled' in data and not isinstance(data['enabled'], bool):
            return error_response("AUTO_DONATION_ENABLED_INVALID", status_code=400)

        if 'threshold' in data:
            threshold = data['threshold']
            if not isinstance(threshold, (int, float)) or threshold < 0:
                return error_response("WALLET_AUTO_DONATION_THRESHOLD_INVALID", status_code=400)

        if 'percentage' in data:
            percentage = data['percentage']
            if not isinstance(percentage, int) or not (1 <= percentage <= 100):
                return error_response("WALLET_AUTO_DONATION_PERCENTAGE_INVALID", status_code=400)

        success, message, updated_settings = wallet_service.update_auto_donation_settings(
            user_id=current_user.get_id(),
            settings=data
        )

        if success:
            return success_response(message, updated_settings)
        else:
            return error_response(message, status_code=404 if "NOT_FOUND" in message else 400)

    except Exception as e:
        current_app.logger.error(f"Error updating auto-donation settings for user {current_user.get_id()}: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@wallet_bp.route('/auto-donation/process', methods=['POST'])
@auth_required
def process_auto_donation(current_user):
    """
    Manually trigger auto-donation processing if conditions are met.
    """
    try:
        success, message, result = wallet_service.process_auto_donation(current_user.get_id())

        if success:
            return success_response(message, result)
        else:
            return error_response(message, status_code=404 if "NOT_FOUND" in message else 400)

    except Exception as e:
        current_app.logger.error(f"Error processing auto-donation for user {current_user.get_id()}: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@wallet_bp.route('/credits/add', methods=['POST'])
@auth_required
def add_credits_manual(current_user):
    """
    Manually add credits to wallet (for admin use or special cases).
    """
    try:
        data = request.get_json()
        if not data:
            return error_response("DATA_REQUIRED", status_code=400)

        # Validate required fields
        if 'amount' not in data:
            return error_response("AMOUNT_REQUIRED", status_code=400)

        amount = data['amount']
        if not isinstance(amount, (int, float)) or amount <= 0:
            return error_response("AMOUNT_MUST_BE_POSITIVE", status_code=400)

        source = data.get('source', 'manual')
        metadata = data.get('metadata', {})
        metadata['manual_addition'] = True
        metadata['admin_user'] = getattr(current_user, 'email', 'unknown')

        success, message, result = wallet_service.add_credits(
            user_id=current_user.get_id(),
            amount=amount,
            source=source,
            metadata=metadata
        )

        if success:
            return success_response(message, result)
        else:
            return error_response(message, status_code=400)

    except Exception as e:
        current_app.logger.error(f"Error adding credits manually for user {current_user.get_id()}: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


# Error handlers for the blueprint
@wallet_bp.errorhandler(400)
def bad_request(error):
    return error_response("INVALID_REQUEST", status_code=400)


@wallet_bp.errorhandler(401)
def unauthorized(error):
    return error_response("UNAUTHORIZED_ACCESS", status_code=401)


@wallet_bp.errorhandler(404)
def not_found(error):
    return error_response("RESOURCE_NOT_FOUND", status_code=404)


@wallet_bp.errorhandler(422)
def unprocessable_entity(error):
    return error_response("VALIDATION_ERROR", status_code=422)


@wallet_bp.errorhandler(500)
def internal_error(error):
    return error_response("INTERNAL_SERVER_ERROR", status_code=500)