from flask import Blueprint, request, jsonify
from app.core.utils.decorators import auth_required, admin_required
from app.core.utils.responses import success_response, error_response
from app.onlus.services.application_service import ApplicationService
from app.onlus.services.verification_service import VerificationService
from app.onlus.services.document_service import DocumentService
from app.onlus.services.onlus_service import ONLUSService

# Create blueprint
admin_application_bp = Blueprint('admin_onlus_applications', __name__)

# Initialize services
application_service = ApplicationService()
verification_service = VerificationService()
document_service = DocumentService()
onlus_service = ONLUSService()


@admin_application_bp.route('/applications', methods=['GET'])
@admin_required
def get_applications_for_review(current_user):
    """Get applications pending admin review."""
    try:
        reviewer_id = request.args.get('reviewer_id')
        priority = request.args.get('priority')

        success, message, result = application_service.get_applications_for_admin_review(
            reviewer_id, priority
        )

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@admin_application_bp.route('/applications/<application_id>', methods=['GET'])
@admin_required
def get_application_admin_view(current_user, application_id):
    """Get application details for admin review."""
    try:
        success, message, result = application_service.get_application(
            application_id, is_admin=True
        )

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@admin_application_bp.route('/applications/<application_id>/assign', methods=['POST'])
@admin_required
def assign_reviewer(current_user, application_id):
    """Assign reviewer to application."""
    try:
        data = request.get_json()
        if not data or not data.get('reviewer_id'):
            return error_response("REVIEWER_ID_REQUIRED")

        success, message, result = application_service.assign_reviewer(
            application_id, data['reviewer_id'], current_user.get_id()
        )

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@admin_application_bp.route('/applications/<application_id>/verification/initiate', methods=['POST'])
@admin_required
def initiate_verification(current_user, application_id):
    """Initiate verification checks for application."""
    try:
        success, message, result = verification_service.initiate_verification_checks(
            application_id, current_user.get_id()
        )

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@admin_application_bp.route('/applications/<application_id>/verification/summary', methods=['GET'])
@admin_required
def get_verification_summary(current_user, application_id):
    """Get verification summary for application."""
    try:
        success, message, result = verification_service.get_verification_summary(application_id)

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@admin_application_bp.route('/applications/<application_id>/verification/approve', methods=['POST'])
@admin_required
def approve_verification(current_user, application_id):
    """Approve application verification."""
    try:
        success, message, result = verification_service.approve_application_verification(
            application_id, current_user.get_id()
        )

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@admin_application_bp.route('/applications/<application_id>/verification/reject', methods=['POST'])
@admin_required
def reject_verification(current_user, application_id):
    """Reject application verification."""
    try:
        data = request.get_json()
        if not data or not data.get('rejection_reason'):
            return error_response("REJECTION_REASON_REQUIRED")

        success, message, result = verification_service.reject_application_verification(
            application_id, current_user.get_id(), data['rejection_reason']
        )

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@admin_application_bp.route('/applications/<application_id>/approve', methods=['POST'])
@admin_required
def approve_application(current_user, application_id):
    """Give final approval to application and create ONLUS organization."""
    try:
        data = request.get_json() or {}
        conditions = data.get('conditions', [])

        # First approve the application
        from app.onlus.repositories.onlus_application_repository import ONLUSApplicationRepository
        from app.onlus.models.onlus_application import ONLUSApplication

        app_repo = ONLUSApplicationRepository()
        application = app_repo.find_by_id(application_id)
        if not application:
            return error_response("APPLICATION_NOT_FOUND")

        application_obj = ONLUSApplication.from_dict(application)
        application_obj.approve_application(current_user.get_id(), conditions)

        # Save application approval
        app_repo.update_application(application_id, application_obj)

        # Create ONLUS organization
        success, message, result = onlus_service.create_organization_from_application(
            application_id, current_user.get_id()
        )

        if success:
            return success_response("APPLICATION_APPROVED_SUCCESS", {
                "application_id": application_id,
                "organization": result
            })
        else:
            return error_response(message)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@admin_application_bp.route('/applications/<application_id>/reject', methods=['POST'])
@admin_required
def reject_application(current_user, application_id):
    """Reject application with reason."""
    try:
        data = request.get_json()
        if not data or not data.get('rejection_reason'):
            return error_response("REJECTION_REASON_REQUIRED")

        from app.onlus.repositories.onlus_application_repository import ONLUSApplicationRepository
        from app.onlus.models.onlus_application import ONLUSApplication

        app_repo = ONLUSApplicationRepository()
        application = app_repo.find_by_id(application_id)
        if not application:
            return error_response("APPLICATION_NOT_FOUND")

        application_obj = ONLUSApplication.from_dict(application)
        application_obj.reject_application(current_user.get_id(), data['rejection_reason'])

        # Save rejection
        success = app_repo.update_application(application_id, application_obj)
        if not success:
            return error_response("APPLICATION_REJECTION_FAILED")

        return success_response("APPLICATION_REJECTED_SUCCESS", {
            "application_id": application_id,
            "rejection_reason": data['rejection_reason']
        })

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@admin_application_bp.route('/applications/statistics', methods=['GET'])
@admin_required
def get_application_statistics(current_user):
    """Get application statistics."""
    try:
        success, message, result = application_service.get_application_statistics()

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@admin_application_bp.route('/verification/checks/<check_id>/review', methods=['POST'])
@admin_required
def review_verification_check(current_user, check_id):
    """Perform manual verification check review."""
    try:
        data = request.get_json()
        if not data:
            return error_response("DATA_REQUIRED")

        success, message, result = verification_service.perform_manual_check(
            check_id, current_user.get_id(), data
        )

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@admin_application_bp.route('/documents/review', methods=['GET'])
@admin_required
def get_documents_for_review(current_user):
    """Get documents pending review."""
    try:
        document_type = request.args.get('document_type')
        limit = request.args.get('limit', type=int)

        success, message, result = document_service.get_documents_for_review(
            document_type, limit
        )

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@admin_application_bp.route('/documents/<document_id>/review', methods=['POST'])
@admin_required
def review_document(current_user, document_id):
    """Review a document (approve/reject/resubmit)."""
    try:
        data = request.get_json()
        if not data:
            return error_response("DATA_REQUIRED")

        success, message, result = document_service.review_document(
            document_id, current_user.get_id(), data
        )

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)