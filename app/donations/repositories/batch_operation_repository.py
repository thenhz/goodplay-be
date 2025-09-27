from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone, timedelta
from bson import ObjectId
from flask import current_app
from app.core.repositories.base_repository import BaseRepository
from app.donations.models.batch_operation import BatchOperation, BatchOperationType, BatchOperationStatus


class BatchOperationRepository(BaseRepository):
    """
    Repository for BatchOperation data access operations.

    Handles CRUD operations and queries for batch operations throughout their lifecycle.
    Manages batch tracking, status updates, and historical data.
    """

    def __init__(self):
        super().__init__('batch_operations')

    def create_indexes(self):
        """Create database indexes for batch operations collection."""
        import os
        if self.collection is None or os.getenv('TESTING') == 'true':
            return

        try:
            # Create indexes for common queries
            self.collection.create_index("batch_id", unique=True)
            self.collection.create_index("operation_type")
            self.collection.create_index([("operation_type", 1), ("status", 1)])
            self.collection.create_index([("created_by", 1), ("status", 1)])
            self.collection.create_index("status")
            self.collection.create_index("priority", background=True)
            self.collection.create_index("created_at")
            self.collection.create_index("started_at")
            self.collection.create_index("completed_at")
            self.collection.create_index([("status", 1), ("created_at", -1)])

            current_app.logger.info("BatchOperation indexes created successfully")
        except Exception as e:
            current_app.logger.error(f"Failed to create BatchOperation indexes: {str(e)}")

    def create_batch_operation(self, batch_operation: BatchOperation) -> str:
        """
        Create a new batch operation.

        Args:
            batch_operation: BatchOperation instance

        Returns:
            Created batch ID
        """
        try:
            batch_data = batch_operation.to_dict()
            result = self.collection.insert_one(batch_data)

            current_app.logger.info(f"Created batch operation: {batch_operation.batch_id}")
            return str(result.inserted_id)

        except Exception as e:
            current_app.logger.error(f"Failed to create batch operation: {str(e)}")
            raise

    def find_by_batch_id(self, batch_id: str) -> Optional[BatchOperation]:
        """
        Find batch operation by batch ID.

        Args:
            batch_id: Batch operation identifier

        Returns:
            BatchOperation instance or None
        """
        try:
            batch_data = self.collection.find_one({"batch_id": batch_id})

            if batch_data:
                return BatchOperation.from_dict(batch_data)
            return None

        except Exception as e:
            current_app.logger.error(f"Failed to find batch operation {batch_id}: {str(e)}")
            return None

    def find_by_status(self, status: str, operation_type: str = None, limit: int = 50) -> List[BatchOperation]:
        """
        Find batch operations by status.

        Args:
            status: Batch operation status
            operation_type: Optional operation type filter
            limit: Maximum number of results

        Returns:
            List of BatchOperation instances
        """
        try:
            query = {"status": status}
            if operation_type:
                query["operation_type"] = operation_type

            batch_data = self.collection.find(query).sort("created_at", -1).limit(limit)

            return [BatchOperation.from_dict(data) for data in batch_data]

        except Exception as e:
            current_app.logger.error(f"Failed to find batch operations by status {status}: {str(e)}")
            return []

    def find_by_created_by(self, created_by: str, limit: int = 50) -> List[BatchOperation]:
        """
        Find batch operations created by a specific user/system.

        Args:
            created_by: Creator identifier
            limit: Maximum number of results

        Returns:
            List of BatchOperation instances
        """
        try:
            query = {"created_by": created_by}
            batch_data = self.collection.find(query).sort("created_at", -1).limit(limit)

            return [BatchOperation.from_dict(data) for data in batch_data]

        except Exception as e:
            current_app.logger.error(f"Failed to find batch operations by creator {created_by}: {str(e)}")
            return []

    def find_active_operations(self) -> List[BatchOperation]:
        """
        Find currently active (processing) batch operations.

        Returns:
            List of active BatchOperation instances
        """
        try:
            query = {
                "status": {"$in": [BatchOperationStatus.QUEUED, BatchOperationStatus.PROCESSING]}
            }

            batch_data = self.collection.find(query).sort([("priority", -1), ("created_at", 1)])

            return [BatchOperation.from_dict(data) for data in batch_data]

        except Exception as e:
            current_app.logger.error(f"Failed to find active batch operations: {str(e)}")
            return []

    def find_stalled_operations(self, stall_threshold_hours: int = 2) -> List[BatchOperation]:
        """
        Find batch operations that appear to be stalled.

        Args:
            stall_threshold_hours: Hours after which a processing batch is considered stalled

        Returns:
            List of potentially stalled BatchOperation instances
        """
        try:
            threshold_time = datetime.now(timezone.utc) - timedelta(hours=stall_threshold_hours)

            query = {
                "status": BatchOperationStatus.PROCESSING,
                "last_updated_at": {"$lt": threshold_time}
            }

            batch_data = self.collection.find(query).sort("last_updated_at", 1)

            return [BatchOperation.from_dict(data) for data in batch_data]

        except Exception as e:
            current_app.logger.error(f"Failed to find stalled batch operations: {str(e)}")
            return []

    def update_batch_operation(self, batch_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update batch operation with new data.

        Args:
            batch_id: Batch operation identifier
            updates: Dictionary of fields to update

        Returns:
            True if update was successful
        """
        try:
            updates['last_updated_at'] = datetime.now(timezone.utc)

            result = self.collection.update_one(
                {"batch_id": batch_id},
                {"$set": updates}
            )

            if result.modified_count > 0:
                current_app.logger.info(f"Updated batch operation {batch_id}")
                return True
            else:
                current_app.logger.warning(f"No changes made to batch operation {batch_id}")
                return False

        except Exception as e:
            current_app.logger.error(f"Failed to update batch operation {batch_id}: {str(e)}")
            return False

    def update_progress(self, batch_id: str, processed_count: int, successful_count: int = None,
                       failed_count: int = None, additional_data: Dict[str, Any] = None) -> bool:
        """
        Update batch operation progress.

        Args:
            batch_id: Batch operation identifier
            processed_count: Total items processed so far
            successful_count: Number of successful items
            failed_count: Number of failed items
            additional_data: Optional additional data to update

        Returns:
            True if update was successful
        """
        try:
            # Get current batch to calculate progress
            batch_operation = self.find_by_batch_id(batch_id)
            if not batch_operation:
                return False

            updates = {
                'processed_items': processed_count,
                'last_updated_at': datetime.now(timezone.utc)
            }

            if successful_count is not None:
                updates['successful_items'] = successful_count

            if failed_count is not None:
                updates['failed_items'] = failed_count

            # Calculate progress percentage
            if batch_operation.total_items > 0:
                progress = round((processed_count / batch_operation.total_items) * 100, 2)
                updates['progress_percentage'] = progress

            # Auto-update status based on progress
            if processed_count >= batch_operation.total_items:
                if failed_count == 0:
                    updates['status'] = BatchOperationStatus.COMPLETED
                elif successful_count and successful_count > 0:
                    updates['status'] = BatchOperationStatus.PARTIAL
                else:
                    updates['status'] = BatchOperationStatus.FAILED

                updates['completed_at'] = updates['last_updated_at']

            # Add any additional data
            if additional_data:
                updates.update(additional_data)

            return self.update_batch_operation(batch_id, updates)

        except Exception as e:
            current_app.logger.error(f"Failed to update batch progress {batch_id}: {str(e)}")
            return False

    def add_error_log(self, batch_id: str, error_message: str, item_id: str = None,
                     error_details: Dict[str, Any] = None) -> bool:
        """
        Add error entry to batch operation error log.

        Args:
            batch_id: Batch operation identifier
            error_message: Error message
            item_id: Optional item identifier that failed
            error_details: Additional error details

        Returns:
            True if error was added successfully
        """
        try:
            error_entry = {
                'timestamp': datetime.now(timezone.utc),
                'message': error_message,
                'item_id': item_id,
                'details': error_details or {}
            }

            result = self.collection.update_one(
                {"batch_id": batch_id},
                {
                    "$push": {"error_log": error_entry},
                    "$inc": {"error_count": 1},
                    "$set": {
                        "last_error": error_message,
                        "last_updated_at": datetime.now(timezone.utc)
                    }
                }
            )

            if result.modified_count > 0:
                current_app.logger.info(f"Added error to batch operation {batch_id}: {error_message}")

                # Limit error log size to prevent memory issues
                self.collection.update_one(
                    {"batch_id": batch_id},
                    {"$push": {"error_log": {"$each": [], "$slice": -1000}}}
                )

                return True
            return False

        except Exception as e:
            current_app.logger.error(f"Failed to add error to batch operation {batch_id}: {str(e)}")
            return False

    def get_batch_statistics(self, start_date: datetime, end_date: datetime,
                           operation_type: str = None) -> Dict[str, Any]:
        """
        Get batch operation statistics for a date range.

        Args:
            start_date: Start date for statistics
            end_date: End date for statistics
            operation_type: Optional operation type filter

        Returns:
            Batch statistics dictionary
        """
        try:
            match_stage = {
                "created_at": {
                    "$gte": start_date,
                    "$lte": end_date
                }
            }

            if operation_type:
                match_stage["operation_type"] = operation_type

            pipeline = [
                {"$match": match_stage},
                {
                    "$group": {
                        "_id": "$status",
                        "count": {"$sum": 1},
                        "total_items": {"$sum": "$total_items"},
                        "total_processed": {"$sum": "$processed_items"},
                        "total_successful": {"$sum": "$successful_items"},
                        "total_failed": {"$sum": "$failed_items"},
                        "avg_processing_time": {
                            "$avg": {
                                "$cond": [
                                    {"$and": [{"$ne": ["$started_at", None]}, {"$ne": ["$completed_at", None]}]},
                                    {"$subtract": ["$completed_at", "$started_at"]},
                                    None
                                ]
                            }
                        }
                    }
                }
            ]

            results = list(self.collection.aggregate(pipeline))

            statistics = {
                'period': {
                    'start_date': start_date,
                    'end_date': end_date
                },
                'by_status': {},
                'totals': {
                    'batch_count': 0,
                    'total_items': 0,
                    'total_processed': 0,
                    'total_successful': 0,
                    'total_failed': 0
                }
            }

            for result in results:
                status = result['_id']
                statistics['by_status'][status] = {
                    'count': result['count'],
                    'total_items': result['total_items'],
                    'total_processed': result['total_processed'],
                    'total_successful': result['total_successful'],
                    'total_failed': result['total_failed'],
                    'avg_processing_time_ms': round(result['avg_processing_time'] or 0)
                }

                # Update totals
                statistics['totals']['batch_count'] += result['count']
                statistics['totals']['total_items'] += result['total_items']
                statistics['totals']['total_processed'] += result['total_processed']
                statistics['totals']['total_successful'] += result['total_successful']
                statistics['totals']['total_failed'] += result['total_failed']

            # Calculate success rate
            if statistics['totals']['total_processed'] > 0:
                success_rate = (statistics['totals']['total_successful'] /
                              statistics['totals']['total_processed']) * 100
                statistics['totals']['success_rate'] = round(success_rate, 2)
            else:
                statistics['totals']['success_rate'] = 0.0

            return statistics

        except Exception as e:
            current_app.logger.error(f"Failed to get batch statistics: {str(e)}")
            return {}

    def cleanup_old_operations(self, retention_days: int = 90) -> int:
        """
        Clean up old batch operations to save storage space.

        Args:
            retention_days: Number of days to retain operations

        Returns:
            Number of operations cleaned up
        """
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)

            # Only delete completed operations older than retention period
            query = {
                "status": {"$in": BatchOperationStatus.get_final_statuses()},
                "completed_at": {"$lt": cutoff_date}
            }

            result = self.collection.delete_many(query)

            if result.deleted_count > 0:
                current_app.logger.info(f"Cleaned up {result.deleted_count} old batch operations")

            return result.deleted_count

        except Exception as e:
            current_app.logger.error(f"Failed to cleanup old batch operations: {str(e)}")
            return 0

    def get_recent_operations(self, limit: int = 20, operation_type: str = None) -> List[BatchOperation]:
        """
        Get most recent batch operations.

        Args:
            limit: Maximum number of results
            operation_type: Optional operation type filter

        Returns:
            List of recent BatchOperation instances
        """
        try:
            query = {}
            if operation_type:
                query["operation_type"] = operation_type

            batch_data = self.collection.find(query).sort("created_at", -1).limit(limit)

            return [BatchOperation.from_dict(data) for data in batch_data]

        except Exception as e:
            current_app.logger.error(f"Failed to get recent batch operations: {str(e)}")
            return []

    def delete_batch_operation(self, batch_id: str) -> bool:
        """
        Delete a batch operation (use with caution).

        Args:
            batch_id: Batch operation identifier

        Returns:
            True if deletion was successful
        """
        try:
            result = self.collection.delete_one({"batch_id": batch_id})

            if result.deleted_count > 0:
                current_app.logger.warning(f"Deleted batch operation {batch_id}")
                return True
            return False

        except Exception as e:
            current_app.logger.error(f"Failed to delete batch operation {batch_id}: {str(e)}")
            return False