from flask import Blueprint, request, jsonify
from app.core.utils.responses import success_response, error_response
from app.onlus.services.onlus_service import ONLUSService
from app.onlus.repositories.onlus_category_repository import ONLUSCategoryRepository

# Create blueprint
onlus_bp = Blueprint('onlus', __name__)

# Initialize services
onlus_service = ONLUSService()
category_repo = ONLUSCategoryRepository()


@onlus_bp.route('/organizations', methods=['GET'])
def get_organizations():
    """Get public ONLUS organizations."""
    try:
        category = request.args.get('category')
        featured_only = request.args.get('featured', 'false').lower() == 'true'
        limit = request.args.get('limit', type=int)
        search_query = request.args.get('search')

        success, message, result = onlus_service.get_public_organizations(
            category=category,
            featured_only=featured_only,
            limit=limit,
            search_query=search_query
        )

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@onlus_bp.route('/organizations/<organization_id>', methods=['GET'])
def get_organization(organization_id):
    """Get organization details."""
    try:
        success, message, result = onlus_service.get_organization(
            organization_id, include_sensitive=False
        )

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@onlus_bp.route('/organizations/featured', methods=['GET'])
def get_featured_organizations():
    """Get featured organizations."""
    try:
        success, message, result = onlus_service.get_public_organizations(
            featured_only=True
        )

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@onlus_bp.route('/organizations/top-rated', methods=['GET'])
def get_top_rated_organizations():
    """Get top-rated organizations."""
    try:
        limit = request.args.get('limit', 10, type=int)

        success, message, result = onlus_service.get_top_rated_organizations(limit)

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@onlus_bp.route('/organizations/recent', methods=['GET'])
def get_recent_organizations():
    """Get recently verified organizations."""
    try:
        days = request.args.get('days', 30, type=int)

        success, message, result = onlus_service.get_recent_organizations(days)

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@onlus_bp.route('/organizations/search', methods=['GET'])
def search_organizations():
    """Search organizations."""
    try:
        query = request.args.get('q')
        if not query:
            return error_response("SEARCH_QUERY_REQUIRED")

        category = request.args.get('category')

        from app.onlus.repositories.onlus_organization_repository import ONLUSOrganizationRepository
        org_repo = ONLUSOrganizationRepository()
        organizations = org_repo.search_organizations(query, category)

        organizations_data = []
        for org in organizations:
            org_data = org.to_dict(include_sensitive=False)
            org_data['is_featured'] = org.is_featured()
            org_data['overall_score'] = org.get_overall_score()
            organizations_data.append(org_data)

        return success_response("ORGANIZATION_SEARCH_SUCCESS", organizations_data)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@onlus_bp.route('/categories', methods=['GET'])
def get_categories():
    """Get ONLUS categories."""
    try:
        categories = category_repo.get_active_categories()
        categories_data = [cat.to_dict() for cat in categories]

        return success_response("CATEGORIES_RETRIEVED_SUCCESS", categories_data)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@onlus_bp.route('/categories/<category>/organizations', methods=['GET'])
def get_organizations_by_category(category):
    """Get organizations by category."""
    try:
        limit = request.args.get('limit', type=int)

        from app.onlus.repositories.onlus_organization_repository import ONLUSOrganizationRepository
        org_repo = ONLUSOrganizationRepository()
        organizations = org_repo.get_organizations_by_category(category)

        if limit:
            organizations = organizations[:limit]

        organizations_data = []
        for org in organizations:
            org_data = org.to_dict(include_sensitive=False)
            org_data['is_featured'] = org.is_featured()
            org_data['overall_score'] = org.get_overall_score()
            organizations_data.append(org_data)

        return success_response("CATEGORY_ORGANIZATIONS_RETRIEVED_SUCCESS", organizations_data)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)


@onlus_bp.route('/statistics', methods=['GET'])
def get_public_statistics():
    """Get public ONLUS statistics."""
    try:
        success, message, result = onlus_service.get_organization_statistics()

        if success:
            # Filter out sensitive information for public view
            public_stats = {
                "total_organizations": result["organizations"]["total_organizations"],
                "total_donations": result["organizations"]["total_donations"],
                "total_donors": result["organizations"]["total_donors"],
                "active_organizations": result["organizations"]["by_status"].get("active", {}).get("count", 0),
                "category_distribution": result["category_distribution"],
                "generated_at": result["generated_at"]
            }
            return success_response("PUBLIC_STATISTICS_RETRIEVED_SUCCESS", public_stats)
        else:
            return error_response(message)

    except Exception as e:
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)