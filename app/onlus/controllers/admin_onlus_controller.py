from flask import Blueprint, request, jsonify
from app.core.utils.decorators import admin_required
from app.core.utils.responses import success_response, error_response
from app.onlus.services.onlus_service import ONLUSService
from app.onlus.services.verification_service import VerificationService

# Create blueprint
admin_onlus_bp = Blueprint('admin_onlus', __name__)

# Initialize services
onlus_service = ONLUSService()
verification_service = VerificationService()


@admin_onlus_bp.route('/organizations', methods=['GET'])
@admin_required
def get_all_organizations(current_user):
    """Get all organizations for admin management."""
    try:
        category = request.args.get('category')
        status = request.args.get('status')
        limit = request.args.get('limit', type=int)
        search_query = request.args.get('search')

        # Use the public method but with admin access for sensitive data
        success, message, result = onlus_service.get_public_organizations(
            category=category,
            limit=limit,
            search_query=search_query
        )

        # Get additional admin data for each organization
        if success:
            for org_data in result:
                org_id = org_data['_id']
                admin_success, admin_message, admin_org_data = onlus_service.get_organization(
                    str(org_id), include_sensitive=True
                )
                if admin_success:
                    # Add admin-specific fields
                    org_data.update({
                        'tax_id': admin_org_data.get('tax_id'),
                        'legal_entity_type': admin_org_data.get('legal_entity_type'),
                        'compliance_status': admin_org_data.get('compliance_status'),
                        'compliance_score': admin_org_data.get('compliance_score'),
                        'needs_compliance_review': admin_org_data.get('needs_compliance_review')
                    })

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@admin_onlus_bp.route('/organizations/<organization_id>', methods=['GET'])
@admin_required
def get_organization_admin_view(current_user, organization_id):
    """Get organization details for admin management."""
    try:
        success, message, result = onlus_service.get_organization(
            organization_id, include_sensitive=True
        )

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@admin_onlus_bp.route('/organizations/<organization_id>', methods=['PUT'])
@admin_required
def update_organization(current_user, organization_id):
    """Update organization details."""
    try:
        data = request.get_json()
        if not data:
            return error_response("DATA_REQUIRED")

        success, message, result = onlus_service.update_organization(
            organization_id, data, current_user.get_id()
        )

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@admin_onlus_bp.route('/organizations/<organization_id>/status', methods=['PUT'])
@admin_required
def update_organization_status(current_user, organization_id):
    """Update organization status."""
    try:
        data = request.get_json()
        if not data or not data.get('status'):
            return error_response("STATUS_REQUIRED")

        success, message, result = onlus_service.update_organization_status(
            organization_id, data['status'], current_user.get_id(), data.get('reason')
        )

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@admin_onlus_bp.route('/organizations/<organization_id>/compliance', methods=['PUT'])
@admin_required
def update_compliance_status(current_user, organization_id):
    """Update organization compliance status and score."""
    try:
        data = request.get_json()
        if not data or not data.get('compliance_status') or data.get('compliance_score') is None:
            return error_response("COMPLIANCE_DATA_REQUIRED")

        success, message, result = onlus_service.update_compliance_status(
            organization_id,
            data['compliance_status'],
            data['compliance_score'],
            current_user.get_id(),
            data.get('notes')
        )

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@admin_onlus_bp.route('/organizations/<organization_id>/featured', methods=['POST'])
@admin_required
def set_featured_status(current_user, organization_id):
    """Set organization as featured."""
    try:
        data = request.get_json()
        duration_days = data.get('duration_days', 30) if data else 30

        success, message, result = onlus_service.set_featured_status(
            organization_id, duration_days, current_user.get_id()
        )

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@admin_onlus_bp.route('/organizations/<organization_id>/featured', methods=['DELETE'])
@admin_required
def remove_featured_status(current_user, organization_id):
    """Remove featured status from organization."""
    try:
        success, message, result = onlus_service.remove_featured_status(
            organization_id, current_user.get_id()
        )

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@admin_onlus_bp.route('/organizations/compliance-review', methods=['GET'])
@admin_required
def get_organizations_for_compliance_review(current_user):
    """Get organizations that need compliance review."""
    try:
        success, message, result = onlus_service.get_organizations_for_compliance_review()

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@admin_onlus_bp.route('/organizations/statistics', methods=['GET'])
@admin_required
def get_organization_statistics(current_user):
    """Get comprehensive organization statistics."""
    try:
        success, message, result = onlus_service.get_organization_statistics()

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@admin_onlus_bp.route('/verification/statistics', methods=['GET'])
@admin_required
def get_verification_statistics(current_user):
    """Get verification system statistics."""
    try:
        success, message, result = verification_service.get_verification_statistics()

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)