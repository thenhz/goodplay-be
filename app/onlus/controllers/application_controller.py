from flask import Blueprint, request, jsonify
from app.core.utils.decorators import auth_required
from app.core.utils.responses import success_response, error_response
from app.onlus.services.application_service import ApplicationService

# Create blueprint
application_bp = Blueprint('onlus_applications', __name__)

# Initialize service
application_service = ApplicationService()


@application_bp.route('/applications', methods=['POST'])
@auth_required
def create_application(current_user):
    """Create a new ONLUS application."""
    try:
        data = request.get_json()
        if not data:
            return error_response("DATA_REQUIRED")

        success, message, result = application_service.create_application(
            current_user.get_id(), data
        )

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@application_bp.route('/applications/<application_id>', methods=['GET'])
@auth_required
def get_application(current_user, application_id):
    """Get application details."""
    try:
        success, message, result = application_service.get_application(
            application_id, current_user.get_id()
        )

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@application_bp.route('/applications/<application_id>', methods=['PUT'])
@auth_required
def update_application(current_user, application_id):
    """Update application details."""
    try:
        data = request.get_json()
        if not data:
            return error_response("DATA_REQUIRED")

        success, message, result = application_service.update_application(
            application_id, data, current_user.get_id()
        )

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@application_bp.route('/applications/<application_id>/submit', methods=['POST'])
@auth_required
def submit_application(current_user, application_id):
    """Submit application for review."""
    try:
        success, message, result = application_service.submit_application(
            application_id, current_user.get_id()
        )

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@application_bp.route('/applications/<application_id>/withdraw', methods=['POST'])
@auth_required
def withdraw_application(current_user, application_id):
    """Withdraw application."""
    try:
        success, message, result = application_service.withdraw_application(
            application_id, current_user.get_id()
        )

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@application_bp.route('/applications', methods=['GET'])
@auth_required
def get_user_applications(current_user):
    """Get applications for current user."""
    try:
        status = request.args.get('status')

        success, message, result = application_service.get_user_applications(
            current_user.get_id(), status
        )

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@application_bp.route('/applications/<application_id>/progress', methods=['GET'])
@auth_required
def get_application_progress(current_user, application_id):
    """Get detailed application progress."""
    try:
        success, message, result = application_service.get_application_progress(
            application_id, current_user.get_id()
        )

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)