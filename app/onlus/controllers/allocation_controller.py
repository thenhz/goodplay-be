from flask import Blueprint, request, current_app, jsonify
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import traceback

from app.core.utils.decorators import auth_required, admin_required
from app.core.utils.responses import success_response, error_response, paginated_response
from app.onlus.services.allocation_engine_service import AllocationEngineService
from app.onlus.services.audit_trail_service import AuditTrailService

from app.onlus.models.allocation_request import AllocationRequest, AllocationPriority
from app.onlus.models.funding_pool import FundingPool


# Create Blueprint
allocation_bp = Blueprint('allocation', __name__, url_prefix='/api/onlus/allocations')

# Initialize services
allocation_service = AllocationEngineService()
audit_service = AuditTrailService()


@allocation_bp.route('/request', methods=['POST'])
@auth_required
def create_allocation_request(current_user):
    """Create a new allocation request."""
    try:
        data = request.get_json()
        if not data:
            return error_response("DATA_REQUIRED")

        # Validate required fields
        required_fields = ['onlus_id', 'requested_amount', 'project_title', 'project_description']
        for field in required_fields:
            if not data.get(field):
                return error_response("MISSING_REQUIRED_FIELD", {"field": field})

        # Validate amount
        try:
            amount = float(data['requested_amount'])
            if amount <= 0 or amount > 1000000:  # Max 1M per request
                return error_response("INVALID_AMOUNT_RANGE")
        except (ValueError, TypeError):
            return error_response("INVALID_AMOUNT_FORMAT")

        # Create allocation request
        allocation_request = AllocationRequest(
            onlus_id=data['onlus_id'],
            requested_amount=amount,
            project_title=data['project_title'],
            project_description=data['project_description'],
            urgency_level=data.get('urgency_level', 2),
            category=data.get('category'),
            expected_impact=data.get('expected_impact'),
            deadline=datetime.fromisoformat(data['deadline']) if data.get('deadline') else None,
            special_requirements=data.get('special_requirements', {}),
            donor_preferences=data.get('donor_preferences', []),
            supporting_documents=data.get('supporting_documents', []),
            request_type=data.get('request_type', 'general'),
            priority=data.get('priority', 2)
        )

        # Save request
        success, message, result_data = allocation_service.request_repo.create_request(allocation_request)
        if not success:
            return error_response(message)

        # Create audit trail
        audit_service.audit_allocation_request_creation(
            str(allocation_request._id),
            current_user['user_id'],
            data,
            request.remote_addr
        )

        current_app.logger.info(
            f"Allocation request created: {allocation_request._id} by user {current_user['user_id']}"
        )

        return success_response("ALLOCATION_REQUEST_CREATED_SUCCESS", result_data)

    except Exception as e:
        current_app.logger.error(f"Create allocation request failed: {str(e)}")
        return error_response("ALLOCATION_REQUEST_CREATION_FAILED")


@allocation_bp.route('/request/<request_id>', methods=['GET'])
@auth_required
def get_allocation_request(current_user, request_id):
    """Get allocation request by ID."""
    try:
        success, message, allocation_request = allocation_service.request_repo.get_request_by_id(request_id)
        if not success:
            return error_response(message)

        return success_response("ALLOCATION_REQUEST_RETRIEVED_SUCCESS", allocation_request.to_dict())

    except Exception as e:
        current_app.logger.error(f"Get allocation request failed: {str(e)}")
        return error_response("ALLOCATION_REQUEST_RETRIEVAL_FAILED")


@allocation_bp.route('/request/<request_id>/process', methods=['POST'])
@admin_required
def process_allocation_request(current_user, request_id):
    """Process allocation request through the smart engine."""
    try:
        data = request.get_json() or {}

        # Get the request
        success, message, allocation_request = allocation_service.request_repo.get_request_by_id(request_id)
        if not success:
            return error_response(message)

        # Extract processing options
        donor_preferences = data.get('donor_preferences', [])
        force_allocation = data.get('force_allocation', False)

        # Process through allocation engine
        success, message, result_data = allocation_service.process_allocation_request(
            allocation_request,
            donor_preferences,
            force_allocation
        )

        if not success:
            return error_response(message, result_data)

        # Create audit trail
        audit_service.audit_allocation_processing(
            request_id,
            result_data.get('allocation_result_id'),
            result_data.get('allocation_score'),
            result_data.get('funding_pool_id'),
            current_user['user_id']
        )

        current_app.logger.info(
            f"Allocation request processed: {request_id} by admin {current_user['user_id']}, "
            f"Score: {result_data.get('allocation_score')}"
        )

        return success_response(message, result_data)

    except Exception as e:
        current_app.logger.error(f"Process allocation request failed: {str(e)}")
        return error_response("ALLOCATION_REQUEST_PROCESSING_FAILED")


@allocation_bp.route('/request/<request_id>/score', methods=['POST'])
@admin_required
def calculate_allocation_score(current_user, request_id):
    """Calculate allocation score for a request without processing."""
    try:
        data = request.get_json() or {}

        # Get the request
        success, message, allocation_request = allocation_service.request_repo.get_request_by_id(request_id)
        if not success:
            return error_response(message)

        # Get ONLUS data
        success, message, onlus = allocation_service.onlus_repo.get_organization_by_id(allocation_request.onlus_id)
        if not success:
            return error_response(message)

        # Calculate score
        success, message, score = allocation_service.calculate_allocation_score(
            allocation_request,
            onlus.to_dict(),
            data.get('donor_preferences', [])
        )

        if not success:
            return error_response(message)

        # Update request with score
        allocation_service.request_repo.update_allocation_score(request_id, score)

        return success_response("ALLOCATION_SCORE_CALCULATED_SUCCESS", {"allocation_score": score})

    except Exception as e:
        current_app.logger.error(f"Calculate allocation score failed: {str(e)}")
        return error_response("ALLOCATION_SCORE_CALCULATION_FAILED")


@allocation_bp.route('/pending', methods=['GET'])
@admin_required
def get_pending_requests(current_user):
    """Get pending allocation requests."""
    try:
        limit = min(int(request.args.get('limit', 50)), 100)
        skip = max(int(request.args.get('skip', 0)), 0)

        success, message, requests = allocation_service.request_repo.get_pending_requests(limit, skip)
        if not success:
            return error_response(message)

        return success_response("PENDING_REQUESTS_RETRIEVED_SUCCESS", {
            "requests": [req.to_dict() for req in requests],
            "count": len(requests),
            "limit": limit,
            "skip": skip
        })

    except Exception as e:
        current_app.logger.error(f"Get pending requests failed: {str(e)}")
        return error_response("PENDING_REQUESTS_RETRIEVAL_FAILED")


@allocation_bp.route('/emergency', methods=['GET'])
@admin_required
def get_emergency_requests(current_user):
    """Get emergency allocation requests."""
    try:
        success, message, requests = allocation_service.request_repo.get_emergency_requests()
        if not success:
            return error_response(message)

        return success_response("EMERGENCY_REQUESTS_RETRIEVED_SUCCESS", {
            "requests": [req.to_dict() for req in requests],
            "count": len(requests)
        })

    except Exception as e:
        current_app.logger.error(f"Get emergency requests failed: {str(e)}")
        return error_response("EMERGENCY_REQUESTS_RETRIEVAL_FAILED")


@allocation_bp.route('/batch/process', methods=['POST'])
@admin_required
def process_batch_allocations(current_user):
    """Process multiple allocation requests in batch."""
    try:
        data = request.get_json() or {}

        max_requests = min(int(data.get('max_requests', 50)), 100)
        min_score_threshold = float(data.get('min_score_threshold', 60.0))

        success, message, result_data = allocation_service.process_batch_allocations(
            max_requests, min_score_threshold
        )

        if not success:
            return error_response(message)

        current_app.logger.info(
            f"Batch allocation processed by admin {current_user['user_id']}: "
            f"{result_data['processed_count']} requests, "
            f"{result_data['successful_count']} successful"
        )

        return success_response(message, result_data)

    except Exception as e:
        current_app.logger.error(f"Batch allocation processing failed: {str(e)}")
        return error_response("BATCH_ALLOCATION_FAILED")


@allocation_bp.route('/result/<result_id>', methods=['GET'])
@auth_required
def get_allocation_result(current_user, result_id):
    """Get allocation result by ID."""
    try:
        success, message, allocation_result = allocation_service.result_repo.get_result_by_id(result_id)
        if not success:
            return error_response(message)

        return success_response("ALLOCATION_RESULT_RETRIEVED_SUCCESS", allocation_result.to_dict())

    except Exception as e:
        current_app.logger.error(f"Get allocation result failed: {str(e)}")
        return error_response("ALLOCATION_RESULT_RETRIEVAL_FAILED")


@allocation_bp.route('/result/<result_id>/execute', methods=['POST'])
@admin_required
def execute_allocation(current_user, result_id):
    """Execute approved allocation with donor transactions."""
    try:
        data = request.get_json()
        if not data or 'donor_transactions' not in data:
            return error_response("DONOR_TRANSACTIONS_REQUIRED")

        donor_transactions = data['donor_transactions']

        # Validate donor transactions format
        if not isinstance(donor_transactions, list) or not donor_transactions:
            return error_response("INVALID_DONOR_TRANSACTIONS_FORMAT")

        for tx in donor_transactions:
            if not isinstance(tx, dict) or not all(k in tx for k in ['donor_id', 'amount']):
                return error_response("INVALID_TRANSACTION_FORMAT")

        success, message, result_data = allocation_service.execute_allocation(
            result_id, donor_transactions
        )

        if not success:
            return error_response(message)

        # Create audit trail
        audit_service.audit_allocation_execution(
            result_id,
            result_data.get('transactions', []),
            result_data.get('processed_amount', 0),
            result_data.get('transaction_count', 0),
            current_user['user_id']
        )

        current_app.logger.info(
            f"Allocation executed: {result_id} by admin {current_user['user_id']}, "
            f"Amount: {result_data.get('processed_amount')}"
        )

        return success_response(message, result_data)

    except Exception as e:
        current_app.logger.error(f"Execute allocation failed: {str(e)}")
        return error_response("ALLOCATION_EXECUTION_FAILED")


@allocation_bp.route('/onlus/<onlus_id>/requests', methods=['GET'])
@auth_required
def get_onlus_requests(current_user, onlus_id):
    """Get allocation requests for a specific ONLUS."""
    try:
        status = request.args.get('status')
        limit = min(int(request.args.get('limit', 50)), 100)
        skip = max(int(request.args.get('skip', 0)), 0)

        success, message, requests = allocation_service.request_repo.get_requests_by_onlus(
            onlus_id, status, limit, skip
        )
        if not success:
            return error_response(message)

        return success_response("ONLUS_REQUESTS_RETRIEVED_SUCCESS", {
            "requests": [req.to_dict() for req in requests],
            "count": len(requests),
            "onlus_id": onlus_id,
            "status_filter": status,
            "limit": limit,
            "skip": skip
        })

    except Exception as e:
        current_app.logger.error(f"Get ONLUS requests failed: {str(e)}")
        return error_response("ONLUS_REQUESTS_RETRIEVAL_FAILED")


@allocation_bp.route('/onlus/<onlus_id>/results', methods=['GET'])
@auth_required
def get_onlus_results(current_user, onlus_id):
    """Get allocation results for a specific ONLUS."""
    try:
        status = request.args.get('status')
        limit = min(int(request.args.get('limit', 50)), 100)
        skip = max(int(request.args.get('skip', 0)), 0)

        success, message, results = allocation_service.result_repo.get_results_by_onlus(
            onlus_id, status, limit, skip
        )
        if not success:
            return error_response(message)

        return success_response("ONLUS_RESULTS_RETRIEVED_SUCCESS", {
            "results": [result.to_dict() for result in results],
            "count": len(results),
            "onlus_id": onlus_id,
            "status_filter": status,
            "limit": limit,
            "skip": skip
        })

    except Exception as e:
        current_app.logger.error(f"Get ONLUS results failed: {str(e)}")
        return error_response("ONLUS_RESULTS_RETRIEVAL_FAILED")


@allocation_bp.route('/onlus/<onlus_id>/recommendations', methods=['GET'])
@auth_required
def get_allocation_recommendations(current_user, onlus_id):
    """Get allocation recommendations for an ONLUS."""
    try:
        # Parse amount range if provided
        amount_range = None
        if request.args.get('min_amount') and request.args.get('max_amount'):
            try:
                min_amount = float(request.args.get('min_amount'))
                max_amount = float(request.args.get('max_amount'))
                if min_amount > 0 and max_amount > min_amount:
                    amount_range = (min_amount, max_amount)
            except ValueError:
                pass

        success, message, recommendations = allocation_service.get_allocation_recommendations(
            onlus_id, amount_range
        )

        if not success:
            return error_response(message)

        return success_response("ALLOCATION_RECOMMENDATIONS_SUCCESS", recommendations)

    except Exception as e:
        current_app.logger.error(f"Get allocation recommendations failed: {str(e)}")
        return error_response("ALLOCATION_RECOMMENDATIONS_FAILED")


@allocation_bp.route('/search', methods=['GET'])
@auth_required
def search_allocation_requests(current_user):
    """Search allocation requests by text and filters."""
    try:
        query_text = request.args.get('q', '').strip()
        if not query_text:
            return error_response("SEARCH_QUERY_REQUIRED")

        # Parse filters
        filters = {}
        if request.args.get('status'):
            filters['status'] = request.args.get('status')
        if request.args.get('category'):
            filters['category'] = request.args.get('category')
        if request.args.get('priority'):
            try:
                filters['priority'] = int(request.args.get('priority'))
            except ValueError:
                pass
        if request.args.get('urgency_min'):
            try:
                filters['urgency_min'] = int(request.args.get('urgency_min'))
            except ValueError:
                pass
        if request.args.get('amount_min'):
            try:
                filters['amount_min'] = float(request.args.get('amount_min'))
            except ValueError:
                pass
        if request.args.get('amount_max'):
            try:
                filters['amount_max'] = float(request.args.get('amount_max'))
            except ValueError:
                pass

        limit = min(int(request.args.get('limit', 50)), 100)
        skip = max(int(request.args.get('skip', 0)), 0)

        success, message, requests = allocation_service.request_repo.search_requests(
            query_text, filters, limit, skip
        )

        if not success:
            return error_response(message)

        return success_response("REQUESTS_SEARCH_SUCCESS", {
            "requests": [req.to_dict() for req in requests],
            "count": len(requests),
            "query": query_text,
            "filters": filters,
            "limit": limit,
            "skip": skip
        })

    except Exception as e:
        current_app.logger.error(f"Search allocation requests failed: {str(e)}")
        return error_response("REQUESTS_SEARCH_FAILED")


@allocation_bp.route('/statistics', methods=['GET'])
@admin_required
def get_allocation_statistics(current_user):
    """Get allocation statistics."""
    try:
        # Parse date range if provided
        start_date = None
        end_date = None

        if request.args.get('start_date'):
            try:
                start_date = datetime.fromisoformat(request.args.get('start_date'))
            except ValueError:
                return error_response("INVALID_START_DATE_FORMAT")

        if request.args.get('end_date'):
            try:
                end_date = datetime.fromisoformat(request.args.get('end_date'))
            except ValueError:
                return error_response("INVALID_END_DATE_FORMAT")

        # Get request statistics
        success, message, request_stats = allocation_service.request_repo.get_requests_statistics(
            start_date, end_date
        )
        if not success:
            return error_response(message)

        # Get allocation performance metrics
        success, message, performance_stats = allocation_service.result_repo.get_allocation_performance_metrics(
            start_date, end_date
        )
        if not success:
            performance_stats = {}

        statistics = {
            "request_statistics": request_stats,
            "performance_metrics": performance_stats,
            "period": {
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None
            },
            "generated_at": datetime.now(timezone.utc).isoformat()
        }

        return success_response("ALLOCATION_STATISTICS_SUCCESS", statistics)

    except Exception as e:
        current_app.logger.error(f"Get allocation statistics failed: {str(e)}")
        return error_response("ALLOCATION_STATISTICS_FAILED")


# Error handlers
@allocation_bp.errorhandler(400)
def bad_request(error):
    return error_response("BAD_REQUEST", status_code=400)


@allocation_bp.errorhandler(404)
def not_found(error):
    return error_response("RESOURCE_NOT_FOUND", status_code=404)


@allocation_bp.errorhandler(500)
def internal_error(error):
    current_app.logger.error(f"Internal server error in allocation controller: {str(error)}")
    return error_response("INTERNAL_SERVER_ERROR", status_code=500)