from flask import Blueprint, request, jsonify, current_app
from app.core.utils.decorators import auth_required, admin_required
from app.core.utils import success_response, error_response
from app.donations.services.payment_gateway_service import PaymentGatewayService
from app.donations.models.payment_intent import PaymentIntentStatus

# Create blueprint for payment management
payment_bp = Blueprint('payments', __name__, url_prefix='/api/payments')

# Initialize services (lazy initialization)
payment_service = None

def get_payment_service():
    global payment_service
    if payment_service is None:
        payment_service = PaymentGatewayService()
    return payment_service


@payment_bp.route('/intent', methods=['POST'])
@auth_required
def create_payment_intent(current_user):
    """
    Create a payment intent for wallet funding.
    """
    try:
        data = request.get_json()
        if not data:
            return error_response("DATA_REQUIRED", status_code=400)

        # Validate required fields
        required_fields = ['amount']
        for field in required_fields:
            if field not in data:
                return error_response(f"PAYMENT_{field.upper()}_REQUIRED", status_code=400)

        amount = data['amount']
        if not isinstance(amount, (int, float)) or amount <= 0:
            return error_response("PAYMENT_AMOUNT_INVALID", status_code=400)

        # Validate amount limits
        if amount < 1.0:
            return error_response("PAYMENT_AMOUNT_TOO_SMALL", status_code=400)
        if amount > 50000.0:
            return error_response("PAYMENT_AMOUNT_TOO_LARGE", status_code=400)

        currency = data.get('currency', 'EUR').upper()
        description = data.get('description', 'Wallet top-up')

        # Build payment metadata
        metadata = {
            'user_id': current_user.get_id(),
            'source': 'web_app',
            'user_agent': request.headers.get('User-Agent', 'Unknown'),
            'ip_address': request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
        }

        # Add custom metadata if provided
        custom_metadata = data.get('metadata', {})
        if isinstance(custom_metadata, dict):
            metadata.update(custom_metadata)

        success, message, result = get_payment_service().create_payment_intent(
            user_id=current_user.get_id(),
            amount=amount,
            currency=currency,
            description=description,
            metadata=metadata
        )

        if success:
            current_app.logger.info(f"Payment intent created for user {current_user.get_id()}: {amount} {currency}")
            return success_response(message, result)
        else:
            return error_response(message, status_code=400)

    except Exception as e:
        current_app.logger.error(f"Error creating payment intent for user {current_user.get_id()}: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@payment_bp.route('/<intent_id>/confirm', methods=['POST'])
@auth_required
def confirm_payment(current_user, intent_id):
    """
    Confirm a payment intent and process payment.
    """
    try:
        data = request.get_json() or {}

        # Extract payment method ID if provided
        payment_method_id = data.get('payment_method_id')

        success, message, result = get_payment_service().confirm_payment(
            intent_id=intent_id,
            payment_method_id=payment_method_id
        )

        if success:
            current_app.logger.info(f"Payment confirmed for intent {intent_id}")
            return success_response(message, result)
        else:
            status_code = 404 if "NOT_FOUND" in message else 400
            return error_response(message, status_code=status_code)

    except Exception as e:
        current_app.logger.error(f"Error confirming payment {intent_id}: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@payment_bp.route('/<intent_id>/status', methods=['GET'])
@auth_required
def get_payment_status(current_user, intent_id):
    """
    Get payment intent status and details.
    """
    try:
        success, message, result = get_payment_service().get_payment_status(intent_id)

        if success:
            # Verify the payment intent belongs to the current user
            if result.get('user_id') != current_user.get_id():
                return error_response("PAYMENT_ACCESS_DENIED", status_code=403)

            return success_response(message, result)
        else:
            status_code = 404 if "NOT_FOUND" in message else 400
            return error_response(message, status_code=status_code)

    except Exception as e:
        current_app.logger.error(f"Error getting payment status {intent_id}: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@payment_bp.route('/<intent_id>/cancel', methods=['POST'])
@auth_required
def cancel_payment(current_user, intent_id):
    """
    Cancel a payment intent.
    """
    try:
        data = request.get_json() or {}
        reason = data.get('reason', 'Cancelled by user')

        # Validate reason length
        if isinstance(reason, str) and len(reason) > 200:
            return error_response("CANCELLATION_REASON_TOO_LONG", status_code=400)

        success, message, result = get_payment_service().cancel_payment(
            intent_id=intent_id,
            reason=reason
        )

        if success:
            current_app.logger.info(f"Payment cancelled for intent {intent_id}: {reason}")
            return success_response(message, result)
        else:
            status_code = 404 if "NOT_FOUND" in message else 400
            return error_response(message, status_code=status_code)

    except Exception as e:
        current_app.logger.error(f"Error cancelling payment {intent_id}: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@payment_bp.route('/webhook', methods=['POST'])
def payment_webhook():
    """
    Handle payment provider webhooks.
    """
    try:
        # Get provider type from headers or URL parameter
        provider_type = request.headers.get('X-Provider-Type', 'stripe')
        webhook_signature = request.headers.get('Stripe-Signature')  # For Stripe

        # Get webhook payload
        webhook_data = request.get_json()
        if not webhook_data:
            return error_response("WEBHOOK_DATA_REQUIRED", status_code=400)

        success, message = get_payment_service().handle_webhook(
            provider_type=provider_type,
            webhook_data=webhook_data,
            webhook_signature=webhook_signature
        )

        if success:
            current_app.logger.info(f"Processed webhook: {webhook_data.get('type', 'unknown')}")
            return success_response(message)
        else:
            current_app.logger.warning(f"Failed to process webhook: {message}")
            return error_response(message, status_code=400)

    except Exception as e:
        current_app.logger.error(f"Error processing webhook: {str(e)}")
        return error_response("WEBHOOK_PROCESSING_ERROR", status_code=500)


@payment_bp.route('/history', methods=['GET'])
@auth_required
def get_payment_history(current_user):
    """
    Get user's payment history.
    """
    try:
        # Extract query parameters
        limit = min(request.args.get('limit', 20, type=int), 100)  # Max 100
        status_filter = request.args.get('status')

        # Validate status filter
        if status_filter and status_filter not in PaymentIntentStatus.get_all_statuses():
            return error_response("INVALID_STATUS_FILTER", status_code=400)

        success, message, history = get_payment_service().get_user_payment_history(
            user_id=current_user.get_id(),
            limit=limit
        )

        if success:
            # Filter by status if requested
            if status_filter:
                history = [p for p in history if p.get('status') == status_filter]

            # Add pagination info
            result = {
                'payments': history,
                'pagination': {
                    'current_page': 1,
                    'page_size': len(history),
                    'total_count': len(history),
                    'has_more': len(history) == limit
                }
            }

            return success_response(message, result)
        else:
            return error_response(message, status_code=400)

    except Exception as e:
        current_app.logger.error(f"Error getting payment history for user {current_user.get_id()}: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@payment_bp.route('/<payment_id>/refund', methods=['POST'])
@auth_required
def request_refund(current_user, payment_id):
    """
    Request a refund for a payment (placeholder for future implementation).
    """
    try:
        data = request.get_json() or {}
        refund_amount = data.get('amount')
        reason = data.get('reason', 'User requested refund')

        # This is a placeholder for future refund functionality
        # For now, we'll return a not implemented response
        return error_response("REFUND_FEATURE_NOT_IMPLEMENTED", status_code=501)

    except Exception as e:
        current_app.logger.error(f"Error requesting refund for payment {payment_id}: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@payment_bp.route('/methods', methods=['GET'])
@auth_required
def get_payment_methods(current_user):
    """
    Get available payment methods for the user.
    """
    try:
        # For now, return static payment methods
        # In the future, this could be dynamic based on user location, provider availability, etc.
        payment_methods = [
            {
                'id': 'card',
                'type': 'card',
                'name': 'Credit/Debit Card',
                'description': 'Visa, Mastercard, American Express',
                'supported_currencies': ['EUR', 'USD', 'GBP'],
                'processing_time': 'Instant',
                'fees': {
                    'percentage': 2.9,
                    'fixed': 0.30
                }
            },
            {
                'id': 'bank_transfer',
                'type': 'bank_transfer',
                'name': 'Bank Transfer',
                'description': 'Direct bank transfer',
                'supported_currencies': ['EUR'],
                'processing_time': '1-3 business days',
                'fees': {
                    'percentage': 0.8,
                    'fixed': 0.25
                }
            }
        ]

        return success_response("PAYMENT_METHODS_RETRIEVED", {
            'payment_methods': payment_methods,
            'default_currency': 'EUR'
        })

    except Exception as e:
        current_app.logger.error(f"Error getting payment methods: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@payment_bp.route('/fees/calculate', methods=['GET'])
@auth_required
def calculate_fees(current_user):
    """
    Calculate payment fees for a given amount.
    """
    try:
        amount = request.args.get('amount', type=float)
        if not amount or amount <= 0:
            return error_response("INVALID_AMOUNT", status_code=400)

        currency = request.args.get('currency', 'EUR').upper()
        payment_method = request.args.get('payment_method', 'card')

        # Default fee structure (this would come from active payment provider)
        fee_structure = {
            'card': {'percentage': 2.9, 'fixed': 0.30},
            'bank_transfer': {'percentage': 0.8, 'fixed': 0.25}
        }

        if payment_method not in fee_structure:
            return error_response("INVALID_PAYMENT_METHOD", status_code=400)

        fees = fee_structure[payment_method]
        processing_fee = round(amount * (fees['percentage'] / 100) + fees['fixed'], 2)
        net_amount = round(amount - processing_fee, 2)

        result = {
            'amount': amount,
            'currency': currency,
            'payment_method': payment_method,
            'processing_fee': processing_fee,
            'net_amount': net_amount,
            'fee_breakdown': {
                'percentage_fee': round(amount * (fees['percentage'] / 100), 2),
                'fixed_fee': fees['fixed'],
                'total_fee': processing_fee
            }
        }

        return success_response("FEE_CALCULATION_SUCCESS", result)

    except Exception as e:
        current_app.logger.error(f"Error calculating fees: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


# Error handlers for the blueprint
@payment_bp.errorhandler(400)
def bad_request(error):
    return error_response("INVALID_REQUEST", status_code=400)


@payment_bp.errorhandler(401)
def unauthorized(error):
    return error_response("UNAUTHORIZED_ACCESS", status_code=401)


@payment_bp.errorhandler(403)
def forbidden(error):
    return error_response("FORBIDDEN_ACTION", status_code=403)


@payment_bp.errorhandler(404)
def not_found(error):
    return error_response("RESOURCE_NOT_FOUND", status_code=404)


@payment_bp.errorhandler(422)
def unprocessable_entity(error):
    return error_response("VALIDATION_ERROR", status_code=422)


@payment_bp.errorhandler(500)
def internal_error(error):
    return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@payment_bp.errorhandler(501)
def not_implemented(error):
    return error_response("FEATURE_NOT_IMPLEMENTED", status_code=501)


@payment_bp.errorhandler(503)
def service_unavailable(error):
    return error_response("SERVICE_UNAVAILABLE", status_code=503)