from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
from bson import ObjectId
from app.core.repositories.base_repository import BaseRepository
from app.donations.models.transaction import Transaction, TransactionType, TransactionStatus
import os


class TransactionRepository(BaseRepository):
    """
    Repository for transaction data access operations.
    Handles CRUD operations, batch processing, and transaction-specific queries.
    """

    def __init__(self):
        super().__init__('transactions')

    def create_indexes(self):
        """Create database indexes for optimal query performance."""
        if self.collection is None or os.getenv('TESTING') == 'true':
            return

        # Create indexes for common queries
        self.collection.create_index("user_id")
        self.collection.create_index("transaction_id", unique=True)
        self.collection.create_index("transaction_type")
        self.collection.create_index("status")
        self.collection.create_index("created_at")
        self.collection.create_index("processed_at")
        self.collection.create_index("game_session_id")
        self.collection.create_index("onlus_id")

        # Compound indexes for complex queries
        self.collection.create_index([("user_id", 1), ("created_at", -1)])
        self.collection.create_index([("user_id", 1), ("transaction_type", 1)])
        self.collection.create_index([("status", 1), ("created_at", 1)])
        self.collection.create_index([("transaction_type", 1), ("status", 1)])

    def find_by_transaction_id(self, transaction_id: str) -> Optional[Transaction]:
        """
        Find transaction by transaction ID.

        Args:
            transaction_id: Transaction identifier

        Returns:
            Optional[Transaction]: Transaction instance if found, None otherwise
        """
        data = self.find_one({"transaction_id": transaction_id})
        return Transaction.from_dict(data) if data else None

    def find_by_user_id(self, user_id: str, limit: int = 50,
                        offset: int = 0, transaction_type: str = None,
                        status: str = None, sort_by: str = "created_at",
                        sort_order: int = -1) -> List[Transaction]:
        """
        Find transactions by user ID with filtering and pagination.

        Args:
            user_id: User identifier
            limit: Maximum number of transactions to return
            offset: Number of transactions to skip
            transaction_type: Filter by transaction type
            status: Filter by transaction status
            sort_by: Field to sort by
            sort_order: Sort order (1 for ascending, -1 for descending)

        Returns:
            List[Transaction]: List of transactions
        """
        filter_criteria = {"user_id": user_id}

        if transaction_type:
            filter_criteria["transaction_type"] = transaction_type

        if status:
            filter_criteria["status"] = status

        transactions_data = self.find_many(
            filter_criteria,
            limit=limit,
            skip=offset,
            sort=[(sort_by, sort_order)]
        )

        return [Transaction.from_dict(data) for data in transactions_data]

    def find_by_session_id(self, game_session_id: str) -> List[Transaction]:
        """
        Find transactions by game session ID.

        Args:
            game_session_id: Game session identifier

        Returns:
            List[Transaction]: List of transactions for the session
        """
        transactions_data = self.find_many(
            {"game_session_id": game_session_id},
            sort=[("created_at", 1)]
        )

        return [Transaction.from_dict(data) for data in transactions_data]

    def create_transaction(self, transaction: Transaction) -> str:
        """
        Create a new transaction.

        Args:
            transaction: Transaction instance to create

        Returns:
            str: Created transaction ID
        """
        transaction_data = transaction.to_dict()
        if '_id' in transaction_data and transaction_data['_id'] is None:
            del transaction_data['_id']

        transaction_id = self.create(transaction_data)
        transaction._id = ObjectId(transaction_id)
        return transaction_id

    def update_transaction(self, transaction: Transaction) -> bool:
        """
        Update an existing transaction.

        Args:
            transaction: Transaction instance to update

        Returns:
            bool: True if update was successful
        """
        if not transaction._id:
            return False

        transaction_data = transaction.to_dict()
        del transaction_data['_id']  # Remove _id from update data

        return self.update_by_id(str(transaction._id), transaction_data)

    def batch_create_transactions(self, transactions: List[Transaction]) -> List[str]:
        """
        Create multiple transactions in batch.

        Args:
            transactions: List of Transaction instances to create

        Returns:
            List[str]: List of created transaction IDs
        """
        if not self.collection or not transactions:
            return []

        transactions_data = []
        for transaction in transactions:
            data = transaction.to_dict()
            if '_id' in data and data['_id'] is None:
                del data['_id']
            transactions_data.append(data)

        try:
            result = self.collection.insert_many(transactions_data)
            transaction_ids = [str(oid) for oid in result.inserted_ids]

            # Update transaction objects with their new IDs
            for i, transaction in enumerate(transactions):
                transaction._id = result.inserted_ids[i]

            return transaction_ids
        except Exception:
            return []

    def batch_update_status(self, transaction_ids: List[str],
                           new_status: str, metadata: Dict[str, Any] = None) -> int:
        """
        Batch update transaction status.

        Args:
            transaction_ids: List of transaction IDs to update
            new_status: New status to set
            metadata: Optional metadata to add

        Returns:
            int: Number of transactions updated
        """
        if not self.collection or not transaction_ids:
            return 0

        object_ids = []
        for tid in transaction_ids:
            if ObjectId.is_valid(tid):
                object_ids.append(ObjectId(tid))

        update_data = {
            "status": new_status,
            "updated_at": self._get_current_time()
        }

        if new_status == TransactionStatus.COMPLETED.value:
            update_data["processed_at"] = self._get_current_time()

        if metadata:
            update_data.update({f"metadata.{k}": v for k, v in metadata.items()})

        result = self.collection.update_many(
            {"_id": {"$in": object_ids}},
            {"$set": update_data}
        )
        return result.modified_count

    def get_user_transaction_summary(self, user_id: str,
                                   start_date: datetime = None,
                                   end_date: datetime = None) -> Dict[str, Any]:
        """
        Get transaction summary for a user within a date range.

        Args:
            user_id: User identifier
            start_date: Start date for summary (inclusive)
            end_date: End date for summary (inclusive)

        Returns:
            Dict[str, Any]: Transaction summary statistics
        """
        if not self.collection:
            return {}

        match_criteria = {"user_id": user_id}

        if start_date or end_date:
            date_filter = {}
            if start_date:
                date_filter["$gte"] = start_date
            if end_date:
                date_filter["$lte"] = end_date
            match_criteria["created_at"] = date_filter

        pipeline = [
            {"$match": match_criteria},
            {
                "$group": {
                    "_id": "$transaction_type",
                    "count": {"$sum": 1},
                    "total_amount": {"$sum": "$amount"},
                    "total_effective_amount": {
                        "$sum": {"$multiply": ["$amount", "$multiplier_applied"]}
                    },
                    "avg_amount": {"$avg": "$amount"},
                    "completed_count": {
                        "$sum": {"$cond": [{"$eq": ["$status", "completed"]}, 1, 0]}
                    }
                }
            }
        ]

        results = list(self.collection.aggregate(pipeline))

        summary = {
            "total_transactions": 0,
            "total_earned": 0.0,
            "total_donated": 0.0,
            "total_effective_earned": 0.0,
            "total_effective_donated": 0.0,
            "completed_transactions": 0,
            "by_type": {}
        }

        for result in results:
            transaction_type = result["_id"]
            summary["by_type"][transaction_type] = result
            summary["total_transactions"] += result["count"]
            summary["completed_transactions"] += result["completed_count"]

            if transaction_type == TransactionType.EARNED.value:
                summary["total_earned"] += result["total_amount"]
                summary["total_effective_earned"] += result["total_effective_amount"]
            elif transaction_type == TransactionType.DONATED.value:
                summary["total_donated"] += result["total_amount"]
                summary["total_effective_donated"] += result["total_effective_amount"]

        return summary

    def get_pending_transactions(self, limit: int = 100) -> List[Transaction]:
        """
        Get pending transactions for processing.

        Args:
            limit: Maximum number of transactions to return

        Returns:
            List[Transaction]: List of pending transactions
        """
        transactions_data = self.find_many(
            {"status": TransactionStatus.PENDING.value},
            limit=limit,
            sort=[("created_at", 1)]  # Process oldest first
        )

        return [Transaction.from_dict(data) for data in transactions_data]

    def get_transactions_by_date_range(self, start_date: datetime,
                                     end_date: datetime,
                                     transaction_type: str = None,
                                     status: str = None,
                                     limit: int = 1000) -> List[Transaction]:
        """
        Get transactions within a date range.

        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            transaction_type: Optional transaction type filter
            status: Optional status filter
            limit: Maximum number of transactions to return

        Returns:
            List[Transaction]: List of transactions in date range
        """
        filter_criteria = {
            "created_at": {
                "$gte": start_date,
                "$lte": end_date
            }
        }

        if transaction_type:
            filter_criteria["transaction_type"] = transaction_type

        if status:
            filter_criteria["status"] = status

        transactions_data = self.find_many(
            filter_criteria,
            limit=limit,
            sort=[("created_at", -1)]
        )

        return [Transaction.from_dict(data) for data in transactions_data]

    def get_failed_transactions(self, hours_back: int = 24,
                               limit: int = 100) -> List[Transaction]:
        """
        Get failed transactions within specified time period.

        Args:
            hours_back: Number of hours to look back
            limit: Maximum number of transactions to return

        Returns:
            List[Transaction]: List of failed transactions
        """
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours_back)

        transactions_data = self.find_many(
            {
                "status": TransactionStatus.FAILED.value,
                "created_at": {"$gte": cutoff_time}
            },
            limit=limit,
            sort=[("created_at", -1)]
        )

        return [Transaction.from_dict(data) for data in transactions_data]

    def get_transaction_statistics(self) -> Dict[str, Any]:
        """
        Get overall transaction statistics for reporting.

        Returns:
            Dict[str, Any]: Aggregated transaction statistics
        """
        if not self.collection:
            return {}

        pipeline = [
            {
                "$group": {
                    "_id": None,
                    "total_transactions": {"$sum": 1},
                    "total_amount": {"$sum": "$amount"},
                    "total_effective_amount": {
                        "$sum": {"$multiply": ["$amount", "$multiplier_applied"]}
                    },
                    "avg_amount": {"$avg": "$amount"},
                    "completed_count": {
                        "$sum": {"$cond": [{"$eq": ["$status", "completed"]}, 1, 0]}
                    },
                    "pending_count": {
                        "$sum": {"$cond": [{"$eq": ["$status", "pending"]}, 1, 0]}
                    },
                    "failed_count": {
                        "$sum": {"$cond": [{"$eq": ["$status", "failed"]}, 1, 0]}
                    }
                }
            }
        ]

        result = list(self.collection.aggregate(pipeline))
        if result:
            stats = result[0]
            del stats['_id']
            return stats

        return {
            "total_transactions": 0,
            "total_amount": 0.0,
            "total_effective_amount": 0.0,
            "avg_amount": 0.0,
            "completed_count": 0,
            "pending_count": 0,
            "failed_count": 0
        }

    def search_transactions(self, search_criteria: Dict[str, Any],
                           page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """
        Search transactions with pagination.

        Args:
            search_criteria: Search criteria dictionary
            page: Page number (1-based)
            page_size: Number of results per page

        Returns:
            Dict containing transactions and pagination info
        """
        skip = (page - 1) * page_size

        transactions_data = self.find_many(
            search_criteria,
            limit=page_size,
            skip=skip,
            sort=[("created_at", -1)]
        )

        total_count = self.count(search_criteria)
        total_pages = (total_count + page_size - 1) // page_size

        return {
            "transactions": [Transaction.from_dict(data) for data in transactions_data],
            "pagination": {
                "page": page,
                "per_page": page_size,
                "total_items": total_count,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        }

    def delete_old_transactions(self, days_old: int = 365) -> int:
        """
        Delete old transactions for data retention.

        Args:
            days_old: Delete transactions older than this many days

        Returns:
            int: Number of transactions deleted
        """
        if not self.collection:
            return 0

        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_old)

        result = self.collection.delete_many({
            "created_at": {"$lt": cutoff_date},
            "status": {"$in": [TransactionStatus.COMPLETED.value, TransactionStatus.CANCELLED.value]}
        })

        return result.deleted_count

    def get_suspicious_transactions(self, hours_back: int = 24) -> List[Transaction]:
        """
        Get potentially suspicious transactions for fraud review.

        Args:
            hours_back: Number of hours to look back

        Returns:
            List[Transaction]: List of suspicious transactions
        """
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours_back)

        # Look for transactions with high amounts or unusual patterns
        suspicious_criteria = {
            "$and": [
                {"created_at": {"$gte": cutoff_time}},
                {
                    "$or": [
                        {"amount": {"$gte": 1000}},  # Large amounts
                        {"multiplier_applied": {"$gte": 5.0}},  # High multipliers
                        {"source_type": "manual"},  # Manual adjustments
                        {
                            "$and": [
                                {"transaction_type": "earned"},
                                {"created_at": {"$gte": datetime.now(timezone.utc) - timedelta(hours=1)}},
                                {"amount": {"$gte": 100}}
                            ]
                        }
                    ]
                }
            ]
        }

        transactions_data = self.find_many(
            suspicious_criteria,
            limit=200,
            sort=[("created_at", -1)]
        )

        return [Transaction.from_dict(data) for data in transactions_data]