from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
from app.core.utils.decorators import auth_required
from app.core.utils.responses import success_response, error_response
from app.donations.services.wallet_service import WalletService
from app.donations.services.receipt_generation_service import ReceiptGenerationService
from app.donations.services.tax_compliance_service import TaxComplianceService

# Create blueprint for donation management
donation_bp = Blueprint('donations', __name__, url_prefix='/api/donations')

# Initialize services with lazy loading
wallet_service = None
receipt_service = None
tax_service = None

def get_wallet_service():
    global wallet_service
    if wallet_service is None:
        wallet_service = WalletService()
    return wallet_service

def get_receipt_service():
    global receipt_service
    if receipt_service is None:
        receipt_service = ReceiptGenerationService()
    return receipt_service

def get_tax_service():
    global tax_service
    if tax_service is None:
        tax_service = TaxComplianceService()
    return tax_service


@donation_bp.route('/create', methods=['POST'])
@auth_required
def create_donation(current_user):
    """
    Process a donation from user's wallet credits to an ONLUS.
    """
    try:
        data = request.get_json()
        if not data:
            return error_response("DATA_REQUIRED", status_code=400)

        # Validate required fields
        required_fields = ['amount', 'onlus_id']
        for field in required_fields:
            if field not in data:
                return error_response(f"DONATION_{field.upper()}_REQUIRED", status_code=400)

        amount = data['amount']
        if not isinstance(amount, (int, float)) or amount <= 0:
            return error_response("AMOUNT_MUST_BE_POSITIVE", status_code=400)

        # Maximum single donation limit
        if amount > 10000:  # €10,000 limit
            return error_response("DONATION_AMOUNT_TOO_LARGE", status_code=400)

        onlus_id = data['onlus_id']
        if not onlus_id or not isinstance(onlus_id, str):
            return error_response("DONATION_ONLUS_ID_INVALID", status_code=400)

        # Build donation metadata
        metadata = {
            'message': data.get('message', ''),
            'is_anonymous': data.get('is_anonymous', False),
            'onlus_name': data.get('onlus_name', 'Unknown ONLUS'),
            'donation_source': 'user_initiated',
            'user_agent': request.headers.get('User-Agent', 'Unknown'),
            'ip_address': request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
        }

        # Validate message length
        if metadata['message'] and len(metadata['message']) > 500:
            return error_response("DONATION_MESSAGE_TOO_LONG", status_code=400)

        success, message, result = get_wallet_service().process_donation(
            user_id=current_user.get_id(),
            amount=amount,
            onlus_id=onlus_id,
            metadata=metadata
        )

        if success:
            current_app.logger.info(f"Donation processed: {amount}€ from user {current_user.get_id()} to ONLUS {onlus_id}")
            return success_response(message, result)
        else:
            return error_response(message, status_code=404 if "NOT_FOUND" in message else 400)

    except Exception as e:
        current_app.logger.error(f"Error processing donation for user {current_user.get_id()}: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@donation_bp.route('/history', methods=['GET'])
@auth_required
def get_donation_history(current_user):
    """
    Retrieve user's donation history with pagination.
    """
    try:
        # Extract query parameters
        page = request.args.get('page', 1, type=int)
        page_size = min(request.args.get('page_size', 20, type=int), 50)  # Max 50 per page for donations

        # Build filters for donations only
        filters = {
            'transaction_type': 'donated',
            'sort_by': 'created_at',
            'sort_order': 'desc'
        }

        success, message, history_data = get_wallet_service().get_transaction_history(
            user_id=current_user.get_id(),
            filters=filters,
            page=page,
            page_size=page_size
        )

        if success:
            # Calculate total donated for the response
            transactions = history_data.get('transactions', [])
            total_donated = sum(tx.get('effective_amount', 0) for tx in transactions if tx.get('type') == 'donated')

            # Enhance response with donation-specific data
            donation_history = {
                'donations': transactions,
                'pagination': history_data.get('pagination', {}),
                'total_donated': total_donated,
                'donation_count': len(transactions)
            }

            return success_response("DONATION_HISTORY_RETRIEVED_SUCCESS", donation_history)
        else:
            return error_response(message, status_code=400)

    except Exception as e:
        current_app.logger.error(f"Error getting donation history for user {current_user.get_id()}: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@donation_bp.route('/<transaction_id>/receipt', methods=['GET'])
@auth_required
def get_donation_receipt(current_user, transaction_id):
    """
    Retrieve detailed receipt for a specific donation.
    """
    try:
        if not transaction_id:
            return error_response("TRANSACTION_ID_REQUIRED", status_code=400)

        success, message, receipt = get_wallet_service().get_donation_receipt(
            user_id=current_user.get_id(),
            transaction_id=transaction_id
        )

        if success:
            return success_response(message, receipt)
        else:
            status_code = 404 if "NOT_FOUND" in message else 403 if "ACCESS_DENIED" in message else 400
            return error_response(message, status_code=status_code)

    except Exception as e:
        current_app.logger.error(f"Error getting donation receipt for user {current_user.get_id()}: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@donation_bp.route('/summary', methods=['GET'])
@auth_required
def get_donation_summary(current_user):
    """
    Get donation summary statistics for the user.
    """
    try:
        # Get wallet statistics which include donation information
        success, message, statistics = get_wallet_service().get_wallet_statistics(current_user.get_id())

        if success:
            # Extract donation-specific statistics
            wallet_stats = statistics.get('wallet', {})
            transaction_stats = statistics.get('transactions', {})

            donation_summary = {
                'total_donated': wallet_stats.get('total_donated', 0.0),
                'donation_ratio': wallet_stats.get('donation_ratio', 0.0),
                'donation_count': transaction_stats.get('by_type', {}).get('donated', {}).get('count', 0),
                'avg_donation_amount': transaction_stats.get('by_type', {}).get('donated', {}).get('avg_amount', 0.0),
                'largest_donation': 0.0,  # Could be calculated with additional query
                'recent_donations_count': 0,  # Last 30 days
                'preferred_causes': [],  # From user preferences
                'impact_score': 0.0  # Could be calculated based on donations
            }

            return success_response("DONATION_SUMMARY_RETRIEVED_SUCCESS", donation_summary)
        else:
            return error_response(message, status_code=404 if "NOT_FOUND" in message else 400)

    except Exception as e:
        current_app.logger.error(f"Error getting donation summary for user {current_user.get_id()}: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@donation_bp.route('/validate', methods=['POST'])
@auth_required
def validate_donation(current_user):
    """
    Validate a donation request without processing it.
    """
    try:
        data = request.get_json()
        if not data:
            return error_response("DATA_REQUIRED", status_code=400)

        # Validate required fields
        if 'amount' not in data:
            return error_response("DONATION_AMOUNT_REQUIRED", status_code=400)

        amount = data['amount']
        if not isinstance(amount, (int, float)) or amount <= 0:
            return error_response("AMOUNT_MUST_BE_POSITIVE", status_code=400)

        if amount > 10000:  # €10,000 limit
            return error_response("DONATION_AMOUNT_TOO_LARGE", status_code=400)

        # Get user's wallet to check balance
        wallet_success, wallet_message, wallet_data = get_wallet_service().get_wallet(current_user.get_id())

        if not wallet_success:
            return error_response(wallet_message, status_code=404)

        current_balance = wallet_data.get('current_balance', 0.0)

        validation_result = {
            'is_valid': current_balance >= amount,
            'amount': amount,
            'current_balance': current_balance,
            'remaining_balance': max(0, current_balance - amount),
            'validation_errors': []
        }

        if current_balance < amount:
            validation_result['validation_errors'].append('INSUFFICIENT_CREDITS')

        if amount < 0.01:  # Minimum donation amount
            validation_result['validation_errors'].append('DONATION_AMOUNT_TOO_SMALL')
            validation_result['is_valid'] = False

        return success_response("DONATION_VALIDATION_SUCCESS", validation_result)

    except Exception as e:
        current_app.logger.error(f"Error validating donation for user {current_user.get_id()}: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@donation_bp.route('/recurring/setup', methods=['POST'])
@auth_required
def setup_recurring_donation(current_user):
    """
    Setup a recurring donation schedule (placeholder for future implementation).
    """
    try:
        data = request.get_json()
        if not data:
            return error_response("DATA_REQUIRED", status_code=400)

        # This is a placeholder for future recurring donation functionality
        # For now, we'll return a not implemented response
        return error_response("FEATURE_NOT_IMPLEMENTED", status_code=501)

    except Exception as e:
        current_app.logger.error(f"Error setting up recurring donation for user {current_user.get_id()}: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@donation_bp.route('/<transaction_id>/receipt/generate', methods=['POST'])
@auth_required
def generate_donation_receipt(current_user, transaction_id):
    """
    Generate a PDF receipt for a specific donation.

    Supports different receipt types: standard, tax_deductible, annual_summary.
    """
    try:
        if not transaction_id:
            return error_response("TRANSACTION_ID_REQUIRED", status_code=400)

        data = request.get_json() or {}
        receipt_type = data.get('receipt_type', 'standard')

        # Validate receipt type
        valid_types = ['standard', 'tax_deductible', 'annual_summary']
        if receipt_type not in valid_types:
            return error_response("INVALID_RECEIPT_TYPE", status_code=400)

        success, message, result = get_receipt_service().generate_donation_receipt(
            transaction_id=transaction_id,
            receipt_type=receipt_type
        )

        if success:
            return success_response(message, result)
        else:
            status_code = 404 if "NOT_FOUND" in message else 400
            return error_response(message, status_code=status_code)

    except Exception as e:
        current_app.logger.error(f"Error generating receipt for transaction {transaction_id}: {str(e)}")
        return error_response("RECEIPT_GENERATION_ERROR", status_code=500)


@donation_bp.route('/<transaction_id>/receipt/download', methods=['GET'])
@auth_required
def download_donation_receipt(current_user, transaction_id):
    """
    Download PDF receipt for a specific donation.
    """
    try:
        if not transaction_id:
            return error_response("TRANSACTION_ID_REQUIRED", status_code=400)

        # For now, return placeholder response
        # In production, this would serve the actual PDF file
        return error_response("RECEIPT_DOWNLOAD_NOT_IMPLEMENTED", status_code=501)

    except Exception as e:
        current_app.logger.error(f"Error downloading receipt for transaction {transaction_id}: {str(e)}")
        return error_response("RECEIPT_DOWNLOAD_ERROR", status_code=500)


@donation_bp.route('/receipts', methods=['GET'])
@auth_required
def get_user_receipts(current_user):
    """
    Get all receipts for the current user with optional tax year filter.
    """
    try:
        # Get query parameters
        tax_year = request.args.get('tax_year', type=int)

        success, message, receipts = get_receipt_service().get_user_receipts(
            user_id=current_user.get_id(),
            tax_year=tax_year
        )

        if success:
            return success_response(message, {
                'receipts': receipts,
                'tax_year_filter': tax_year,
                'total_receipts': len(receipts or [])
            })
        else:
            return error_response(message, status_code=400)

    except Exception as e:
        current_app.logger.error(f"Error getting user receipts for {current_user.get_id()}: {str(e)}")
        return error_response("RECEIPTS_RETRIEVAL_ERROR", status_code=500)


@donation_bp.route('/annual-summary/<int:tax_year>', methods=['GET'])
@auth_required
def get_annual_donation_summary(current_user, tax_year):
    """
    Get annual donation summary for tax purposes.
    """
    try:
        if tax_year < 2020 or tax_year > datetime.now().year:
            return error_response("INVALID_TAX_YEAR", status_code=400)

        success, message, summary = get_receipt_service().generate_annual_summary(
            user_id=current_user.get_id(),
            tax_year=tax_year
        )

        if success:
            return success_response(message, summary)
        else:
            return error_response(message, status_code=400)

    except Exception as e:
        current_app.logger.error(f"Error generating annual summary for {current_user.get_id()}: {str(e)}")
        return error_response("ANNUAL_SUMMARY_ERROR", status_code=500)


@donation_bp.route('/annual-summary/<int:tax_year>/download', methods=['GET'])
@auth_required
def download_annual_summary(current_user, tax_year):
    """
    Download annual donation summary PDF.
    """
    try:
        if tax_year < 2020 or tax_year > datetime.now().year:
            return error_response("INVALID_TAX_YEAR", status_code=400)

        # For now, return placeholder response
        # In production, this would serve the actual PDF file
        return error_response("ANNUAL_SUMMARY_DOWNLOAD_NOT_IMPLEMENTED", status_code=501)

    except Exception as e:
        current_app.logger.error(f"Error downloading annual summary for {current_user.get_id()}: {str(e)}")
        return error_response("ANNUAL_SUMMARY_DOWNLOAD_ERROR", status_code=500)


@donation_bp.route('/tax/validate', methods=['POST'])
@auth_required
def validate_tax_deductibility(current_user):
    """
    Validate if a proposed donation is tax deductible.
    """
    try:
        data = request.get_json()
        if not data:
            return error_response("DATA_REQUIRED", status_code=400)

        # Validate required fields
        amount = data.get('amount')
        onlus_id = data.get('onlus_id')
        jurisdiction = data.get('jurisdiction', 'IT')

        if not amount or not isinstance(amount, (int, float)) or amount <= 0:
            return error_response("INVALID_AMOUNT", status_code=400)

        if not onlus_id:
            return error_response("ONLUS_ID_REQUIRED", status_code=400)

        success, message, validation_details = get_tax_service().validate_tax_deductibility(
            user_id=current_user.get_id(),
            amount=amount,
            onlus_id=onlus_id,
            jurisdiction=jurisdiction
        )

        if success:
            return success_response(message, validation_details)
        else:
            return error_response(message, validation_details, status_code=400)

    except Exception as e:
        current_app.logger.error(f"Error validating tax deductibility for {current_user.get_id()}: {str(e)}")
        return error_response("TAX_VALIDATION_ERROR", status_code=500)


@donation_bp.route('/tax/benefit/calculate', methods=['POST'])
@auth_required
def calculate_tax_benefit(current_user):
    """
    Calculate potential tax benefit from a donation.
    """
    try:
        data = request.get_json()
        if not data:
            return error_response("DATA_REQUIRED", status_code=400)

        # Validate required fields
        amount = data.get('amount')
        user_income = data.get('user_income')  # Optional
        jurisdiction = data.get('jurisdiction', 'IT')

        if not amount or not isinstance(amount, (int, float)) or amount <= 0:
            return error_response("INVALID_AMOUNT", status_code=400)

        success, message, benefit_details = get_tax_service().calculate_tax_benefit(
            user_id=current_user.get_id(),
            donation_amount=amount,
            user_income=user_income,
            jurisdiction=jurisdiction
        )

        if success:
            return success_response(message, benefit_details)
        else:
            return error_response(message, status_code=400)

    except Exception as e:
        current_app.logger.error(f"Error calculating tax benefit for {current_user.get_id()}: {str(e)}")
        return error_response("TAX_BENEFIT_CALCULATION_ERROR", status_code=500)


@donation_bp.route('/tax/requirements', methods=['GET'])
@auth_required
def get_tax_requirements(current_user):
    """
    Get tax documentation requirements for a jurisdiction.
    """
    try:
        jurisdiction = request.args.get('jurisdiction', 'IT')

        success, message, requirements = get_tax_service().get_tax_documentation_requirements(
            jurisdiction=jurisdiction
        )

        if success:
            return success_response(message, requirements)
        else:
            return error_response(message, status_code=400)

    except Exception as e:
        current_app.logger.error(f"Error getting tax requirements: {str(e)}")
        return error_response("TAX_REQUIREMENTS_ERROR", status_code=500)


@donation_bp.route('/tax/summary/<int:tax_year>', methods=['GET'])
@auth_required
def get_annual_tax_summary(current_user, tax_year):
    """
    Get annual tax summary for a user.
    """
    try:
        if tax_year < 2020 or tax_year > datetime.now().year:
            return error_response("INVALID_TAX_YEAR", status_code=400)

        success, message, tax_summary = get_tax_service().get_annual_tax_summary(
            user_id=current_user.get_id(),
            tax_year=tax_year
        )

        if success:
            return success_response(message, tax_summary)
        else:
            return error_response(message, status_code=400)

    except Exception as e:
        current_app.logger.error(f"Error getting annual tax summary for {current_user.get_id()}: {str(e)}")
        return error_response("ANNUAL_TAX_SUMMARY_ERROR", status_code=500)


# Error handlers for the blueprint
@donation_bp.errorhandler(400)
def bad_request(error):
    return error_response("INVALID_REQUEST", status_code=400)


@donation_bp.errorhandler(401)
def unauthorized(error):
    return error_response("UNAUTHORIZED_ACCESS", status_code=401)


@donation_bp.errorhandler(403)
def forbidden(error):
    return error_response("FORBIDDEN_ACTION", status_code=403)


@donation_bp.errorhandler(404)
def not_found(error):
    return error_response("RESOURCE_NOT_FOUND", status_code=404)


@donation_bp.errorhandler(422)
def unprocessable_entity(error):
    return error_response("VALIDATION_ERROR", status_code=422)


@donation_bp.errorhandler(500)
def internal_error(error):
    return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@donation_bp.errorhandler(501)
def not_implemented(error):
    return error_response("FEATURE_NOT_IMPLEMENTED", status_code=501)