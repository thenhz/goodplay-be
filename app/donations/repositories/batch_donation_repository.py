from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone, timedelta
from bson import ObjectId
from flask import current_app
from app.core.repositories.base_repository import BaseRepository
from app.donations.models.batch_donation import BatchDonation, BatchDonationStatus


class BatchDonationRepository(BaseRepository):
    """
    Repository for BatchDonation data access operations.

    Handles CRUD operations and queries for individual batch donation items.
    Manages item tracking, status updates, and retry processing.
    """

    def __init__(self):
        super().__init__('batch_donations')

    def create_indexes(self):
        """Create database indexes for batch donations collection."""
        import os
        if self.collection is None or os.getenv('TESTING') == 'true':
            return

        try:
            # Create indexes for common queries
            self.collection.create_index("item_id", unique=True)
            self.collection.create_index("batch_id")
            self.collection.create_index([("batch_id", 1), ("processing_order", 1)])
            self.collection.create_index([("batch_id", 1), ("status", 1)])
            self.collection.create_index([("user_id", 1), ("status", 1)])
            self.collection.create_index("user_id")
            self.collection.create_index("onlus_id")
            self.collection.create_index("status")
            self.collection.create_index("transaction_id")
            self.collection.create_index("created_at")
            self.collection.create_index("updated_at")
            self.collection.create_index([("status", 1), ("retry_count", 1)])
            self.collection.create_index([("batch_id", 1), ("status", 1), ("processing_order", 1)])

            current_app.logger.info("BatchDonation indexes created successfully")
        except Exception as e:
            current_app.logger.error(f"Failed to create BatchDonation indexes: {str(e)}")

    def create_batch_donation(self, batch_donation: BatchDonation) -> str:
        """
        Create a new batch donation item.

        Args:
            batch_donation: BatchDonation instance

        Returns:
            Created item ID
        """
        try:
            donation_data = batch_donation.to_dict()
            result = self.collection.insert_one(donation_data)

            current_app.logger.info(f"Created batch donation item: {batch_donation.item_id}")
            return str(result.inserted_id)

        except Exception as e:
            current_app.logger.error(f"Failed to create batch donation: {str(e)}")
            raise

    def create_batch_donations(self, batch_donations: List[BatchDonation]) -> List[str]:
        """
        Create multiple batch donation items in bulk.

        Args:
            batch_donations: List of BatchDonation instances

        Returns:
            List of created item IDs
        """
        try:
            donation_data = [donation.to_dict() for donation in batch_donations]
            result = self.collection.insert_many(donation_data)

            item_ids = [str(obj_id) for obj_id in result.inserted_ids]
            current_app.logger.info(f"Created {len(item_ids)} batch donation items")
            return item_ids

        except Exception as e:
            current_app.logger.error(f"Failed to create batch donations: {str(e)}")
            raise

    def find_by_item_id(self, item_id: str) -> Optional[BatchDonation]:
        """
        Find batch donation by item ID.

        Args:
            item_id: Batch donation item identifier

        Returns:
            BatchDonation instance or None
        """
        try:
            donation_data = self.collection.find_one({"item_id": item_id})

            if donation_data:
                return BatchDonation.from_dict(donation_data)
            return None

        except Exception as e:
            current_app.logger.error(f"Failed to find batch donation {item_id}: {str(e)}")
            return None

    def find_by_batch_id(self, batch_id: str, status_filter: List[str] = None) -> List[BatchDonation]:
        """
        Find all batch donations for a specific batch.

        Args:
            batch_id: Batch operation identifier
            status_filter: Optional list of statuses to filter by

        Returns:
            List of BatchDonation instances sorted by processing order
        """
        try:
            query = {"batch_id": batch_id}

            if status_filter:
                query["status"] = {"$in": status_filter}

            donation_data = self.collection.find(query).sort("processing_order", 1)

            return [BatchDonation.from_dict(data) for data in donation_data]

        except Exception as e:
            current_app.logger.error(f"Failed to find batch donations for batch {batch_id}: {str(e)}")
            return []

    def find_by_status(self, batch_id: str, status: str) -> List[BatchDonation]:
        """
        Find batch donations by status within a batch.

        Args:
            batch_id: Batch operation identifier
            status: Batch donation status

        Returns:
            List of BatchDonation instances with specified status
        """
        try:
            query = {
                "batch_id": batch_id,
                "status": status
            }

            donation_data = self.collection.find(query).sort("processing_order", 1)

            return [BatchDonation.from_dict(data) for data in donation_data]

        except Exception as e:
            current_app.logger.error(f"Failed to find batch donations by status {status}: {str(e)}")
            return []

    def find_retryable_items(self, batch_id: str) -> List[BatchDonation]:
        """
        Find batch donation items that can be retried.

        Args:
            batch_id: Batch operation identifier

        Returns:
            List of BatchDonation instances that can be retried
        """
        try:
            query = {
                "batch_id": batch_id,
                "status": {"$in": [BatchDonationStatus.FAILED, BatchDonationStatus.RETRYING]},
                "$expr": {"$lt": ["$retry_count", "$max_retries"]}
            }

            donation_data = self.collection.find(query).sort("processing_order", 1)

            return [BatchDonation.from_dict(data) for data in donation_data]

        except Exception as e:
            current_app.logger.error(f"Failed to find retryable items for batch {batch_id}: {str(e)}")
            return []

    def find_by_user_id(self, user_id: str, limit: int = 50) -> List[BatchDonation]:
        """
        Find batch donations for a specific user.

        Args:
            user_id: User identifier
            limit: Maximum number of results

        Returns:
            List of BatchDonation instances for the user
        """
        try:
            query = {"user_id": user_id}
            donation_data = self.collection.find(query).sort("created_at", -1).limit(limit)

            return [BatchDonation.from_dict(data) for data in donation_data]

        except Exception as e:
            current_app.logger.error(f"Failed to find batch donations for user {user_id}: {str(e)}")
            return []

    def find_by_transaction_id(self, transaction_id: str) -> Optional[BatchDonation]:
        """
        Find batch donation by resulting transaction ID.

        Args:
            transaction_id: Transaction identifier

        Returns:
            BatchDonation instance or None
        """
        try:
            donation_data = self.collection.find_one({"transaction_id": transaction_id})

            if donation_data:
                return BatchDonation.from_dict(donation_data)
            return None

        except Exception as e:
            current_app.logger.error(f"Failed to find batch donation by transaction {transaction_id}: {str(e)}")
            return None

    def update_batch_donation(self, item_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update batch donation with new data.

        Args:
            item_id: Batch donation item identifier
            updates: Dictionary of fields to update

        Returns:
            True if update was successful
        """
        try:
            updates['updated_at'] = datetime.now(timezone.utc)

            result = self.collection.update_one(
                {"item_id": item_id},
                {"$set": updates}
            )

            if result.modified_count > 0:
                current_app.logger.info(f"Updated batch donation {item_id}")
                return True
            else:
                current_app.logger.warning(f"No changes made to batch donation {item_id}")
                return False

        except Exception as e:
            current_app.logger.error(f"Failed to update batch donation {item_id}: {str(e)}")
            return False

    def update_status(self, item_id: str, new_status: str, error_message: str = None,
                     error_code: str = None, transaction_id: str = None,
                     processed_amount: float = None, processing_fee: float = None) -> bool:
        """
        Update batch donation status with optional completion data.

        Args:
            item_id: Batch donation item identifier
            new_status: New donation status
            error_message: Optional error message
            error_code: Optional error code
            transaction_id: Optional resulting transaction ID
            processed_amount: Optional processed amount
            processing_fee: Optional processing fee

        Returns:
            True if update was successful
        """
        try:
            updates = {
                'status': new_status,
                'updated_at': datetime.now(timezone.utc)
            }

            # Add completion data based on status
            if new_status == BatchDonationStatus.COMPLETED:
                updates['completed_at'] = updates['updated_at']
                if transaction_id:
                    updates['transaction_id'] = transaction_id
                if processed_amount is not None:
                    updates['processed_amount'] = processed_amount
                if processing_fee is not None:
                    updates['processing_fee'] = processing_fee

            elif new_status in [BatchDonationStatus.FAILED, BatchDonationStatus.SKIPPED]:
                updates['completed_at'] = updates['updated_at']
                if error_message:
                    updates['error_message'] = error_message
                if error_code:
                    updates['error_code'] = error_code

            elif new_status == BatchDonationStatus.PROCESSING:
                updates['started_processing_at'] = updates['updated_at']

            return self.update_batch_donation(item_id, updates)

        except Exception as e:
            current_app.logger.error(f"Failed to update batch donation status {item_id}: {str(e)}")
            return False

    def increment_retry_count(self, item_id: str) -> bool:
        """
        Increment retry count for a batch donation item.

        Args:
            item_id: Batch donation item identifier

        Returns:
            True if update was successful
        """
        try:
            updates = {
                'last_retry_at': datetime.now(timezone.utc),
                'updated_at': datetime.now(timezone.utc)
            }

            result = self.collection.update_one(
                {"item_id": item_id},
                {
                    "$inc": {"retry_count": 1},
                    "$set": updates
                }
            )

            if result.modified_count > 0:
                current_app.logger.info(f"Incremented retry count for batch donation {item_id}")
                return True
            return False

        except Exception as e:
            current_app.logger.error(f"Failed to increment retry count for batch donation {item_id}: {str(e)}")
            return False

    def add_validation_error(self, item_id: str, error_message: str) -> bool:
        """
        Add validation error to batch donation item.

        Args:
            item_id: Batch donation item identifier
            error_message: Validation error message

        Returns:
            True if error was added successfully
        """
        try:
            result = self.collection.update_one(
                {"item_id": item_id},
                {
                    "$addToSet": {"validation_errors": error_message},
                    "$set": {
                        "pre_validation_passed": False,
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )

            if result.modified_count > 0:
                current_app.logger.info(f"Added validation error to batch donation {item_id}: {error_message}")
                return True
            return False

        except Exception as e:
            current_app.logger.error(f"Failed to add validation error to batch donation {item_id}: {str(e)}")
            return False

    def clear_validation_errors(self, item_id: str) -> bool:
        """
        Clear validation errors and mark item as validated.

        Args:
            item_id: Batch donation item identifier

        Returns:
            True if errors were cleared successfully
        """
        try:
            updates = {
                'validation_errors': [],
                'pre_validation_passed': True,
                'updated_at': datetime.now(timezone.utc)
            }

            return self.update_batch_donation(item_id, updates)

        except Exception as e:
            current_app.logger.error(f"Failed to clear validation errors for batch donation {item_id}: {str(e)}")
            return False

    def get_batch_donation_statistics(self, batch_id: str) -> Dict[str, Any]:
        """
        Get statistics for batch donations within a batch.

        Args:
            batch_id: Batch operation identifier

        Returns:
            Batch donation statistics dictionary
        """
        try:
            pipeline = [
                {"$match": {"batch_id": batch_id}},
                {
                    "$group": {
                        "_id": "$status",
                        "count": {"$sum": 1},
                        "total_amount": {"$sum": "$amount"},
                        "total_processed_amount": {"$sum": "$processed_amount"},
                        "total_fees": {"$sum": "$processing_fee"},
                        "avg_amount": {"$avg": "$amount"},
                        "max_amount": {"$max": "$amount"},
                        "min_amount": {"$min": "$amount"},
                        "avg_retry_count": {"$avg": "$retry_count"},
                        "max_retry_count": {"$max": "$retry_count"}
                    }
                }
            ]

            results = list(self.collection.aggregate(pipeline))

            statistics = {
                'by_status': {},
                'totals': {
                    'count': 0,
                    'total_amount': 0.0,
                    'total_processed_amount': 0.0,
                    'total_fees': 0.0
                }
            }

            for result in results:
                status = result['_id']
                statistics['by_status'][status] = {
                    'count': result['count'],
                    'total_amount': round(result['total_amount'], 2),
                    'total_processed_amount': round(result['total_processed_amount'] or 0, 2),
                    'total_fees': round(result['total_fees'] or 0, 2),
                    'avg_amount': round(result['avg_amount'], 2),
                    'max_amount': round(result['max_amount'], 2),
                    'min_amount': round(result['min_amount'], 2),
                    'avg_retry_count': round(result['avg_retry_count'], 1),
                    'max_retry_count': result['max_retry_count']
                }

                # Update totals
                statistics['totals']['count'] += result['count']
                statistics['totals']['total_amount'] += result['total_amount']
                statistics['totals']['total_processed_amount'] += result['total_processed_amount'] or 0
                statistics['totals']['total_fees'] += result['total_fees'] or 0

            # Round totals
            statistics['totals']['total_amount'] = round(statistics['totals']['total_amount'], 2)
            statistics['totals']['total_processed_amount'] = round(statistics['totals']['total_processed_amount'], 2)
            statistics['totals']['total_fees'] = round(statistics['totals']['total_fees'], 2)

            # Calculate success rate
            successful_count = statistics['by_status'].get(BatchDonationStatus.COMPLETED, {}).get('count', 0)
            if statistics['totals']['count'] > 0:
                success_rate = (successful_count / statistics['totals']['count']) * 100
                statistics['totals']['success_rate'] = round(success_rate, 2)
            else:
                statistics['totals']['success_rate'] = 0.0

            return statistics

        except Exception as e:
            current_app.logger.error(f"Failed to get batch donation statistics for batch {batch_id}: {str(e)}")
            return {}

    def get_user_donation_summary(self, user_id: str, start_date: datetime = None,
                                 end_date: datetime = None) -> Dict[str, Any]:
        """
        Get donation summary for a specific user.

        Args:
            user_id: User identifier
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            User donation summary dictionary
        """
        try:
            match_stage = {"user_id": user_id}

            if start_date and end_date:
                match_stage["created_at"] = {
                    "$gte": start_date,
                    "$lte": end_date
                }

            pipeline = [
                {"$match": match_stage},
                {
                    "$group": {
                        "_id": "$status",
                        "count": {"$sum": 1},
                        "total_amount": {"$sum": "$amount"},
                        "total_processed_amount": {"$sum": "$processed_amount"}
                    }
                }
            ]

            results = list(self.collection.aggregate(pipeline))

            summary = {
                'user_id': user_id,
                'period': {
                    'start_date': start_date,
                    'end_date': end_date
                },
                'by_status': {},
                'totals': {
                    'count': 0,
                    'total_amount': 0.0,
                    'total_processed_amount': 0.0
                }
            }

            for result in results:
                status = result['_id']
                summary['by_status'][status] = {
                    'count': result['count'],
                    'total_amount': round(result['total_amount'], 2),
                    'total_processed_amount': round(result['total_processed_amount'] or 0, 2)
                }

                summary['totals']['count'] += result['count']
                summary['totals']['total_amount'] += result['total_amount']
                summary['totals']['total_processed_amount'] += result['total_processed_amount'] or 0

            # Round totals
            summary['totals']['total_amount'] = round(summary['totals']['total_amount'], 2)
            summary['totals']['total_processed_amount'] = round(summary['totals']['total_processed_amount'], 2)

            return summary

        except Exception as e:
            current_app.logger.error(f"Failed to get user donation summary for {user_id}: {str(e)}")
            return {}

    def cleanup_old_donations(self, retention_days: int = 90) -> int:
        """
        Clean up old batch donation items to save storage space.

        Args:
            retention_days: Number of days to retain donation items

        Returns:
            Number of donation items cleaned up
        """
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)

            # Only delete completed items older than retention period
            query = {
                "status": {"$in": BatchDonationStatus.get_final_statuses()},
                "completed_at": {"$lt": cutoff_date}
            }

            result = self.collection.delete_many(query)

            if result.deleted_count > 0:
                current_app.logger.info(f"Cleaned up {result.deleted_count} old batch donation items")

            return result.deleted_count

        except Exception as e:
            current_app.logger.error(f"Failed to cleanup old batch donation items: {str(e)}")
            return 0

    def delete_batch_donations(self, batch_id: str) -> int:
        """
        Delete all batch donation items for a specific batch (use with caution).

        Args:
            batch_id: Batch operation identifier

        Returns:
            Number of items deleted
        """
        try:
            result = self.collection.delete_many({"batch_id": batch_id})

            if result.deleted_count > 0:
                current_app.logger.warning(f"Deleted {result.deleted_count} batch donation items for batch {batch_id}")

            return result.deleted_count

        except Exception as e:
            current_app.logger.error(f"Failed to delete batch donation items for batch {batch_id}: {str(e)}")
            return 0