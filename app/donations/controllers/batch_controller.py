from flask import Blueprint, request, current_app
from flask_jwt_extended import get_jwt_identity
from app.core.utils.decorators import admin_required
from app.core.utils.responses import success_response, error_response
from app.donations.services.batch_processing_service import BatchProcessingService
from typing import Optional

batch_bp = Blueprint('batch', __name__, url_prefix='/api/batch')

# Global service instance with lazy initialization
batch_service = None

def get_batch_service():
    """Get or create batch processing service instance."""
    global batch_service
    if batch_service is None:
        batch_service = BatchProcessingService()
    return batch_service


@batch_bp.route('/donations', methods=['POST'])
@admin_required
def create_batch_donation_operation(current_user):
    """
    Create a new batch donation operation.

    Admin endpoint to process multiple donations in a batch.
    Maximum 500 donations per batch for performance optimization.
    """
    try:
        data = request.get_json()
        if not data:
            return error_response("DATA_REQUIRED")

        # Validate required fields
        donations = data.get('donations', [])
        if not donations:
            return error_response("DONATIONS_LIST_REQUIRED")

        if len(donations) > 500:
            return error_response("BATCH_SIZE_TOO_LARGE")

        # Optional configuration
        configuration = data.get('configuration', {})
        created_by = current_user.get('user_id', 'admin')

        # Create batch operation
        success, message, result = get_batch_service().create_batch_donation_operation(
            donations=donations,
            created_by=created_by,
            configuration=configuration
        )

        if success:
            return success_response(message, result)
        else:
            return error_response(message, result)

    except Exception as e:
        current_app.logger.error(f"Failed to create batch donation operation: {str(e)}")
        return error_response("BATCH_CREATION_ERROR", status_code=500)


@batch_bp.route('/<batch_id>/status', methods=['GET'])
@admin_required
def get_batch_status(current_user, batch_id: str):
    """
    Get batch operation status and progress.

    Returns detailed status including progress percentage,
    item counts, error logs, and estimated completion time.
    """
    try:
        if not batch_id:
            return error_response("BATCH_ID_REQUIRED")

        success, message, result = get_batch_service().get_batch_status(batch_id)

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Failed to get batch status {batch_id}: {str(e)}")
        return error_response("BATCH_STATUS_ERROR", status_code=500)


@batch_bp.route('/<batch_id>/process', methods=['POST'])
@admin_required
def process_batch_donations(current_user, batch_id: str):
    """
    Start processing a batch donation operation.

    Processes all donations in the batch concurrently using
    ThreadPoolExecutor with 5 workers for optimal performance.
    """
    try:
        if not batch_id:
            return error_response("BATCH_ID_REQUIRED")

        success, message, result = get_batch_service().process_batch_donations(batch_id)

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Failed to process batch donations {batch_id}: {str(e)}")
        return error_response("BATCH_PROCESSING_ERROR", status_code=500)


@batch_bp.route('/<batch_id>/retry', methods=['POST'])
@admin_required
def retry_failed_items(current_user, batch_id: str):
    """
    Retry failed items in a batch operation.

    Reprocesses only the items that failed and can be retried
    based on retry count and error type.
    """
    try:
        if not batch_id:
            return error_response("BATCH_ID_REQUIRED")

        success, message, result = get_batch_service().retry_failed_items(batch_id)

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Failed to retry batch items {batch_id}: {str(e)}")
        return error_response("BATCH_RETRY_ERROR", status_code=500)


@batch_bp.route('/<batch_id>/cancel', methods=['POST'])
@admin_required
def cancel_batch_operation(current_user, batch_id: str):
    """
    Cancel a batch operation.

    Stops processing and marks the batch as cancelled.
    Already processed items remain completed.
    """
    try:
        if not batch_id:
            return error_response("BATCH_ID_REQUIRED")

        data = request.get_json() or {}
        reason = data.get('reason', 'Cancelled by admin')

        success, message, result = get_batch_service().cancel_batch_operation(batch_id, reason)

        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Failed to cancel batch operation {batch_id}: {str(e)}")
        return error_response("BATCH_CANCELLATION_ERROR", status_code=500)


@batch_bp.route('/history', methods=['GET'])
@admin_required
def get_batch_history(current_user):
    """
    Get batch operation history with filtering and pagination.

    Returns list of batch operations with status, progress,
    and summary information for admin monitoring.
    """
    try:
        # Get query parameters
        operation_type = request.args.get('operation_type', 'donations')
        status = request.args.get('status')
        limit = min(int(request.args.get('limit', 20)), 100)  # Max 100 items
        created_by = request.args.get('created_by')

        from app.donations.repositories.batch_operation_repository import BatchOperationRepository
        batch_repo = BatchOperationRepository()

        # Get batch operations based on filters
        if status:
            batch_operations = batch_repo.find_by_status(status, operation_type, limit)
        elif created_by:
            batch_operations = batch_repo.find_by_created_by(created_by, limit)
        else:
            batch_operations = batch_repo.get_recent_operations(limit, operation_type)

        # Convert to API format
        history_data = []
        for batch_op in batch_operations:
            history_data.append({
                'batch_id': batch_op.batch_id,
                'operation_type': batch_op.operation_type,
                'status': batch_op.status,
                'total_items': batch_op.total_items,
                'processed_items': batch_op.processed_items,
                'successful_items': batch_op.successful_items,
                'failed_items': batch_op.failed_items,
                'progress_percentage': batch_op.progress_percentage,
                'created_by': batch_op.created_by,
                'created_at': batch_op.created_at.isoformat() if batch_op.created_at else None,
                'started_at': batch_op.started_at.isoformat() if batch_op.started_at else None,
                'completed_at': batch_op.completed_at.isoformat() if batch_op.completed_at else None,
                'error_count': batch_op.error_count,
                'last_error': batch_op.last_error
            })

        return success_response("BATCH_HISTORY_RETRIEVED", {
            'batch_operations': history_data,
            'total_count': len(history_data),
            'filters': {
                'operation_type': operation_type,
                'status': status,
                'created_by': created_by,
                'limit': limit
            }
        })

    except Exception as e:
        current_app.logger.error(f"Failed to get batch history: {str(e)}")
        return error_response("BATCH_HISTORY_ERROR", status_code=500)


@batch_bp.route('/payouts', methods=['POST'])
@admin_required
def create_batch_payout_operation(current_user):
    """
    Create a batch payout operation for ONLUS organizations.

    Processes multiple payouts to transfer accumulated donations
    to ONLUS organizations in batches.
    """
    try:
        data = request.get_json()
        if not data:
            return error_response("DATA_REQUIRED")

        # For now, return placeholder response
        # This will be implemented when payout system is developed
        return error_response("BATCH_PAYOUTS_NOT_IMPLEMENTED")

    except Exception as e:
        current_app.logger.error(f"Failed to create batch payout operation: {str(e)}")
        return error_response("BATCH_PAYOUT_ERROR", status_code=500)


@batch_bp.route('/statistics', methods=['GET'])
@admin_required
def get_batch_statistics(current_user):
    """
    Get batch processing statistics for admin dashboard.

    Returns aggregated statistics including success rates,
    processing times, and error analysis.
    """
    try:
        from datetime import datetime, timezone, timedelta
        from app.donations.repositories.batch_operation_repository import BatchOperationRepository

        # Get query parameters
        days_back = int(request.args.get('days', 7))
        operation_type = request.args.get('operation_type')

        # Calculate date range
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days_back)

        batch_repo = BatchOperationRepository()
        statistics = batch_repo.get_batch_statistics(start_date, end_date, operation_type)

        if not statistics:
            return error_response("BATCH_STATISTICS_ERROR")

        return success_response("BATCH_STATISTICS_RETRIEVED", {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'days': days_back
            },
            'statistics': statistics,
            'operation_type': operation_type
        })

    except Exception as e:
        current_app.logger.error(f"Failed to get batch statistics: {str(e)}")
        return error_response("BATCH_STATISTICS_ERROR", status_code=500)