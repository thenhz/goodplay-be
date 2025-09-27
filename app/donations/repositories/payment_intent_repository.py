from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone, timedelta
from bson import ObjectId
from flask import current_app
from app.core.repositories.base_repository import BaseRepository
from app.donations.models.payment_intent import PaymentIntent, PaymentIntentStatus


class PaymentIntentRepository(BaseRepository):
    """
    Repository for PaymentIntent data access operations.

    Handles CRUD operations and queries for payment intents throughout their lifecycle.
    Manages payment tracking, status updates, and historical data.
    """

    def __init__(self):
        super().__init__('payment_intents')

    def create_indexes(self):
        """Create database indexes for payment intents collection."""
        import os
        if self.collection is None or os.getenv('TESTING') == 'true':
            return

        try:
            # Create indexes for common queries
            self.collection.create_index("intent_id", unique=True)
            self.collection.create_index("user_id")
            self.collection.create_index("wallet_id")
            self.collection.create_index([("user_id", 1), ("status", 1)])
            self.collection.create_index([("provider_id", 1), ("status", 1)])
            self.collection.create_index("provider_payment_id")
            self.collection.create_index("status")
            self.collection.create_index("created_at")
            self.collection.create_index("expires_at")
            self.collection.create_index([("status", 1), ("expires_at", 1)])

            current_app.logger.info("PaymentIntent indexes created successfully")
        except Exception as e:
            current_app.logger.error(f"Failed to create PaymentIntent indexes: {str(e)}")

    def create_intent(self, payment_intent: PaymentIntent) -> str:
        """
        Create a new payment intent.

        Args:
            payment_intent: PaymentIntent instance

        Returns:
            Created intent ID
        """
        try:
            intent_data = payment_intent.to_dict()
            result = self.collection.insert_one(intent_data)

            current_app.logger.info(f"Created payment intent: {payment_intent.intent_id}")
            return str(result.inserted_id)

        except Exception as e:
            current_app.logger.error(f"Failed to create payment intent: {str(e)}")
            raise

    def find_by_intent_id(self, intent_id: str) -> Optional[PaymentIntent]:
        """
        Find payment intent by intent ID.

        Args:
            intent_id: Payment intent identifier

        Returns:
            PaymentIntent instance or None
        """
        try:
            intent_data = self.collection.find_one({"intent_id": intent_id})

            if intent_data:
                return PaymentIntent.from_dict(intent_data)
            return None

        except Exception as e:
            current_app.logger.error(f"Failed to find payment intent {intent_id}: {str(e)}")
            return None

    def find_by_provider_payment_id(self, provider_payment_id: str, provider_id: str = None) -> Optional[PaymentIntent]:
        """
        Find payment intent by provider payment ID.

        Args:
            provider_payment_id: External provider payment ID
            provider_id: Optional provider ID filter

        Returns:
            PaymentIntent instance or None
        """
        try:
            query = {"provider_payment_id": provider_payment_id}
            if provider_id:
                query["provider_id"] = provider_id

            intent_data = self.collection.find_one(query)

            if intent_data:
                return PaymentIntent.from_dict(intent_data)
            return None

        except Exception as e:
            current_app.logger.error(f"Failed to find payment intent by provider ID {provider_payment_id}: {str(e)}")
            return None

    def find_by_user_id(self, user_id: str, status_filter: List[str] = None, limit: int = 50) -> List[PaymentIntent]:
        """
        Find payment intents for a specific user.

        Args:
            user_id: User identifier
            status_filter: Optional list of statuses to filter by
            limit: Maximum number of results

        Returns:
            List of PaymentIntent instances
        """
        try:
            query = {"user_id": user_id}

            if status_filter:
                query["status"] = {"$in": status_filter}

            intents_data = self.collection.find(query).sort("created_at", -1).limit(limit)

            return [PaymentIntent.from_dict(data) for data in intents_data]

        except Exception as e:
            current_app.logger.error(f"Failed to find payment intents for user {user_id}: {str(e)}")
            return []

    def find_pending_intents(self, max_age_hours: int = 24) -> List[PaymentIntent]:
        """
        Find payment intents that are still pending.

        Args:
            max_age_hours: Maximum age in hours to consider

        Returns:
            List of pending PaymentIntent instances
        """
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)

            query = {
                "status": {"$in": [PaymentIntentStatus.PENDING, PaymentIntentStatus.PROCESSING]},
                "created_at": {"$gte": cutoff_time}
            }

            intents_data = self.collection.find(query).sort("created_at", 1)

            return [PaymentIntent.from_dict(data) for data in intents_data]

        except Exception as e:
            current_app.logger.error(f"Failed to find pending payment intents: {str(e)}")
            return []

    def find_expired_intents(self) -> List[PaymentIntent]:
        """
        Find payment intents that have expired.

        Returns:
            List of expired PaymentIntent instances
        """
        try:
            now = datetime.now(timezone.utc)

            query = {
                "status": {"$in": [PaymentIntentStatus.PENDING, PaymentIntentStatus.PROCESSING]},
                "expires_at": {"$lt": now}
            }

            intents_data = self.collection.find(query)

            return [PaymentIntent.from_dict(data) for data in intents_data]

        except Exception as e:
            current_app.logger.error(f"Failed to find expired payment intents: {str(e)}")
            return []

    def update_intent(self, intent_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update payment intent with new data.

        Args:
            intent_id: Payment intent identifier
            updates: Dictionary of fields to update

        Returns:
            True if update was successful
        """
        try:
            updates['updated_at'] = datetime.now(timezone.utc)

            result = self.collection.update_one(
                {"intent_id": intent_id},
                {"$set": updates}
            )

            if result.modified_count > 0:
                current_app.logger.info(f"Updated payment intent {intent_id}")
                return True
            else:
                current_app.logger.warning(f"No changes made to payment intent {intent_id}")
                return False

        except Exception as e:
            current_app.logger.error(f"Failed to update payment intent {intent_id}: {str(e)}")
            return False

    def update_status(self, intent_id: str, new_status: str, error_message: str = None,
                     error_code: str = None, additional_data: Dict[str, Any] = None) -> bool:
        """
        Update payment intent status with optional error information.

        Args:
            intent_id: Payment intent identifier
            new_status: New payment status
            error_message: Optional error message
            error_code: Optional error code
            additional_data: Optional additional data to update

        Returns:
            True if update was successful
        """
        try:
            updates = {
                'status': new_status,
                'updated_at': datetime.now(timezone.utc)
            }

            # Add error information if provided
            if error_message:
                updates['last_error'] = error_message
            if error_code:
                updates['error_code'] = error_code

            # Add timestamps for final statuses
            if new_status == PaymentIntentStatus.SUCCEEDED:
                updates['confirmed_at'] = updates['updated_at']
                updates['processed_at'] = updates['updated_at']
            elif new_status in [PaymentIntentStatus.FAILED, PaymentIntentStatus.CANCELLED]:
                updates['processed_at'] = updates['updated_at']

            # Add any additional data
            if additional_data:
                updates.update(additional_data)

            result = self.collection.update_one(
                {"intent_id": intent_id},
                {"$set": updates}
            )

            if result.modified_count > 0:
                current_app.logger.info(f"Updated payment intent {intent_id} status to {new_status}")
                return True
            return False

        except Exception as e:
            current_app.logger.error(f"Failed to update payment intent status {intent_id}: {str(e)}")
            return False

    def add_webhook_event(self, intent_id: str, event_type: str, event_data: Dict[str, Any]) -> bool:
        """
        Add webhook event to payment intent history.

        Args:
            intent_id: Payment intent identifier
            event_type: Type of webhook event
            event_data: Event data from provider

        Returns:
            True if event was added successfully
        """
        try:
            webhook_event = {
                'event_type': event_type,
                'event_data': event_data,
                'received_at': datetime.now(timezone.utc)
            }

            result = self.collection.update_one(
                {"intent_id": intent_id},
                {
                    "$push": {"webhook_events": webhook_event},
                    "$set": {"updated_at": datetime.now(timezone.utc)}
                }
            )

            if result.modified_count > 0:
                current_app.logger.info(f"Added webhook event to payment intent {intent_id}: {event_type}")
                return True
            return False

        except Exception as e:
            current_app.logger.error(f"Failed to add webhook event to payment intent {intent_id}: {str(e)}")
            return False

    def get_intents_by_status(self, status: str, provider_id: str = None, limit: int = 100) -> List[PaymentIntent]:
        """
        Get payment intents by status.

        Args:
            status: Payment intent status
            provider_id: Optional provider ID filter
            limit: Maximum number of results

        Returns:
            List of PaymentIntent instances
        """
        try:
            query = {"status": status}
            if provider_id:
                query["provider_id"] = provider_id

            intents_data = self.collection.find(query).sort("created_at", -1).limit(limit)

            return [PaymentIntent.from_dict(data) for data in intents_data]

        except Exception as e:
            current_app.logger.error(f"Failed to get payment intents by status {status}: {str(e)}")
            return []

    def get_intents_for_reconciliation(self, start_date: datetime, end_date: datetime,
                                     provider_id: str = None) -> List[PaymentIntent]:
        """
        Get payment intents for reconciliation within date range.

        Args:
            start_date: Start date for reconciliation
            end_date: End date for reconciliation
            provider_id: Optional provider ID filter

        Returns:
            List of PaymentIntent instances
        """
        try:
            query = {
                "status": {"$in": PaymentIntentStatus.get_final_statuses()},
                "processed_at": {
                    "$gte": start_date,
                    "$lte": end_date
                }
            }

            if provider_id:
                query["provider_id"] = provider_id

            intents_data = self.collection.find(query).sort("processed_at", 1)

            return [PaymentIntent.from_dict(data) for data in intents_data]

        except Exception as e:
            current_app.logger.error(f"Failed to get payment intents for reconciliation: {str(e)}")
            return []

    def get_payment_statistics(self, start_date: datetime, end_date: datetime,
                             provider_id: str = None) -> Dict[str, Any]:
        """
        Get payment statistics for a date range.

        Args:
            start_date: Start date for statistics
            end_date: End date for statistics
            provider_id: Optional provider ID filter

        Returns:
            Payment statistics dictionary
        """
        try:
            match_stage = {
                "created_at": {
                    "$gte": start_date,
                    "$lte": end_date
                }
            }

            if provider_id:
                match_stage["provider_id"] = provider_id

            pipeline = [
                {"$match": match_stage},
                {
                    "$group": {
                        "_id": "$status",
                        "count": {"$sum": 1},
                        "total_amount": {"$sum": "$amount"},
                        "total_fees": {"$sum": "$total_fees"},
                        "avg_amount": {"$avg": "$amount"}
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
                    'count': 0,
                    'amount': 0.0,
                    'fees': 0.0
                }
            }

            for result in results:
                status = result['_id']
                statistics['by_status'][status] = {
                    'count': result['count'],
                    'total_amount': round(result['total_amount'], 2),
                    'total_fees': round(result['total_fees'], 2),
                    'avg_amount': round(result['avg_amount'], 2)
                }

                statistics['totals']['count'] += result['count']
                statistics['totals']['amount'] += result['total_amount']
                statistics['totals']['fees'] += result['total_fees']

            # Round totals
            statistics['totals']['amount'] = round(statistics['totals']['amount'], 2)
            statistics['totals']['fees'] = round(statistics['totals']['fees'], 2)

            return statistics

        except Exception as e:
            current_app.logger.error(f"Failed to get payment statistics: {str(e)}")
            return {}

    def cleanup_expired_intents(self) -> int:
        """
        Clean up expired payment intents by marking them as cancelled.

        Returns:
            Number of intents cleaned up
        """
        try:
            expired_intents = self.find_expired_intents()
            cleaned_count = 0

            for intent in expired_intents:
                if self.update_status(intent.intent_id, PaymentIntentStatus.CANCELLED,
                                    error_message="Payment intent expired"):
                    cleaned_count += 1

            if cleaned_count > 0:
                current_app.logger.info(f"Cleaned up {cleaned_count} expired payment intents")

            return cleaned_count

        except Exception as e:
            current_app.logger.error(f"Failed to cleanup expired payment intents: {str(e)}")
            return 0

    def delete_intent(self, intent_id: str) -> bool:
        """
        Delete a payment intent (use with caution - prefer status updates).

        Args:
            intent_id: Payment intent identifier

        Returns:
            True if deletion was successful
        """
        try:
            result = self.collection.delete_one({"intent_id": intent_id})

            if result.deleted_count > 0:
                current_app.logger.warning(f"Deleted payment intent {intent_id}")
                return True
            return False

        except Exception as e:
            current_app.logger.error(f"Failed to delete payment intent {intent_id}: {str(e)}")
            return False