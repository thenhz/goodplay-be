from flask import Blueprint, request, jsonify
from app.core.utils.decorators import auth_required, admin_required
from app.core.utils.responses import success_response, error_response
from app.onlus.services.document_service import DocumentService

# Create blueprint
document_bp = Blueprint('onlus_documents', __name__)

# Initialize service
document_service = DocumentService()


@document_bp.route('/applications/<application_id>/documents', methods=['POST'])
@auth_required
def upload_document(current_user, application_id):
    """Upload a document for an application."""
    try:
        data = request.get_json()
        if not data:
            return error_response("DATA_REQUIRED")

        success, message, result = document_service.upload_document(
            application_id, data, current_user.get_id()
        )

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@document_bp.route('/applications/<application_id>/documents', methods=['GET'])
@auth_required
def get_application_documents(current_user, application_id):
    """Get all documents for an application."""
    try:
        success, message, result = document_service.get_application_documents(
            application_id, current_user.get_id()
        )

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@document_bp.route('/documents/<document_id>', methods=['DELETE'])
@auth_required
def delete_document(current_user, document_id):
    """Delete a document."""
    try:
        success, message, result = document_service.delete_document(
            document_id, current_user.get_id()
        )

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@document_bp.route('/documents/<document_id>/download', methods=['GET'])
@auth_required
def get_document_download_url(current_user, document_id):
    """Get secure download URL for a document."""
    try:
        success, message, result = document_service.get_document_download_url(
            document_id, current_user.get_id()
        )

        if success:
            return success_response(message, {"download_url": result})
        else:
            return error_response(message)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


# Admin-only document management endpoints
@document_bp.route('/admin/documents/<document_id>/download', methods=['GET'])
@admin_required
def admin_get_document_download_url(current_user, document_id):
    """Get secure download URL for a document (admin access)."""
    try:
        success, message, result = document_service.get_document_download_url(
            document_id, is_admin=True
        )

        if success:
            return success_response(message, {"download_url": result})
        else:
            return error_response(message)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@document_bp.route('/admin/applications/<application_id>/documents', methods=['GET'])
@admin_required
def admin_get_application_documents(current_user, application_id):
    """Get all documents for an application (admin view)."""
    try:
        success, message, result = document_service.get_application_documents(
            application_id, is_admin=True
        )

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@document_bp.route('/admin/documents/statistics', methods=['GET'])
@admin_required
def get_document_statistics(current_user):
    """Get document management statistics."""
    try:
        success, message, result = document_service.get_document_statistics()

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@document_bp.route('/admin/documents/process-expired', methods=['POST'])
@admin_required
def process_expired_documents(current_user):
    """Process expired documents."""
    try:
        success, message, result = document_service.process_expired_documents()

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)