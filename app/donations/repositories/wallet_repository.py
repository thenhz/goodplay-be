from typing import Optional, List, Dict, Any
from bson import ObjectId
from app.core.repositories.base_repository import BaseRepository
from app.donations.models.wallet import Wallet
import os


class WalletRepository(BaseRepository):
    """
    Repository for wallet data access operations.
    Handles CRUD operations and wallet-specific queries.
    """

    def __init__(self):
        super().__init__('wallets')

    def create_indexes(self):
        """Create database indexes for optimal query performance."""
        if self.collection is None or os.getenv('TESTING') == 'true':
            return

        # Create indexes for common queries
        self.collection.create_index("user_id", unique=True)
        self.collection.create_index("created_at")
        self.collection.create_index("updated_at")
        self.collection.create_index([("user_id", 1), ("current_balance", -1)])

    def find_by_user_id(self, user_id: str) -> Optional[Wallet]:
        """
        Find wallet by user ID.

        Args:
            user_id: User identifier

        Returns:
            Optional[Wallet]: Wallet instance if found, None otherwise
        """
        data = self.find_one({"user_id": user_id})
        return Wallet.from_dict(data) if data else None

    def create_wallet(self, wallet: Wallet) -> str:
        """
        Create a new wallet.

        Args:
            wallet: Wallet instance to create

        Returns:
            str: Created wallet ID
        """
        wallet_data = wallet.to_dict()
        if '_id' in wallet_data and wallet_data['_id'] is None:
            del wallet_data['_id']

        wallet_id = self.create(wallet_data)
        wallet._id = ObjectId(wallet_id)
        return wallet_id

    def update_wallet(self, wallet: Wallet) -> bool:
        """
        Update an existing wallet.

        Args:
            wallet: Wallet instance to update

        Returns:
            bool: True if update was successful
        """
        if not wallet._id:
            return False

        wallet_data = wallet.to_dict()
        del wallet_data['_id']  # Remove _id from update data

        return self.update_by_id(str(wallet._id), wallet_data)

    def update_balance(self, user_id: str, balance_change: float,
                       transaction_type: str = 'earned') -> bool:
        """
        Update wallet balance atomically.

        Args:
            user_id: User identifier
            balance_change: Amount to add (positive) or subtract (negative)
            transaction_type: Type of transaction

        Returns:
            bool: True if update was successful
        """
        if not self.collection:
            return False

        update_operations = {
            "$inc": {"current_balance": balance_change},
            "$set": {"updated_at": self._get_current_time()}
        }

        if balance_change > 0 and transaction_type == 'earned':
            update_operations["$inc"]["total_earned"] = balance_change
        elif balance_change < 0 and transaction_type == 'donated':
            update_operations["$inc"]["total_donated"] = abs(balance_change)

        result = self.collection.update_one(
            {"user_id": user_id},
            update_operations
        )
        return result.modified_count > 0

    def update_balance_with_version_check(self, user_id: str, balance_change: float,
                                          expected_version: int,
                                          transaction_type: str = 'earned') -> bool:
        """
        Update wallet balance with optimistic locking using version check.

        Args:
            user_id: User identifier
            balance_change: Amount to add or subtract
            expected_version: Expected wallet version for optimistic locking
            transaction_type: Type of transaction

        Returns:
            bool: True if update was successful
        """
        if not self.collection:
            return False

        update_operations = {
            "$inc": {
                "current_balance": balance_change,
                "version": 1
            },
            "$set": {"updated_at": self._get_current_time()}
        }

        if balance_change > 0 and transaction_type == 'earned':
            update_operations["$inc"]["total_earned"] = balance_change
        elif balance_change < 0 and transaction_type == 'donated':
            update_operations["$inc"]["total_donated"] = abs(balance_change)

        result = self.collection.update_one(
            {"user_id": user_id, "version": expected_version},
            update_operations
        )
        return result.modified_count > 0

    def get_wallets_with_auto_donation_enabled(self, limit: int = 100) -> List[Wallet]:
        """
        Get wallets that have auto-donation enabled and are eligible for processing.

        Args:
            limit: Maximum number of wallets to return

        Returns:
            List[Wallet]: List of wallets eligible for auto-donation
        """
        filter_criteria = {
            "auto_donation_settings.enabled": True,
            "$expr": {
                "$gte": [
                    "$current_balance",
                    "$auto_donation_settings.threshold"
                ]
            }
        }

        wallet_data = self.find_many(
            filter_criteria,
            limit=limit,
            sort=[("updated_at", 1)]  # Process oldest first
        )

        return [Wallet.from_dict(data) for data in wallet_data]

    def get_wallets_by_balance_range(self, min_balance: float = None,
                                     max_balance: float = None,
                                     limit: int = 100) -> List[Wallet]:
        """
        Get wallets within a specific balance range.

        Args:
            min_balance: Minimum balance (inclusive)
            max_balance: Maximum balance (inclusive)
            limit: Maximum number of wallets to return

        Returns:
            List[Wallet]: List of wallets in the specified range
        """
        filter_criteria = {}

        if min_balance is not None:
            filter_criteria["current_balance"] = {"$gte": min_balance}

        if max_balance is not None:
            if "current_balance" in filter_criteria:
                filter_criteria["current_balance"]["$lte"] = max_balance
            else:
                filter_criteria["current_balance"] = {"$lte": max_balance}

        wallet_data = self.find_many(
            filter_criteria,
            limit=limit,
            sort=[("current_balance", -1)]
        )

        return [Wallet.from_dict(data) for data in wallet_data]

    def get_wallet_statistics(self) -> Dict[str, Any]:
        """
        Get overall wallet statistics for reporting.

        Returns:
            Dict[str, Any]: Aggregated wallet statistics
        """
        if not self.collection:
            return {}

        pipeline = [
            {
                "$group": {
                    "_id": None,
                    "total_wallets": {"$sum": 1},
                    "total_balance": {"$sum": "$current_balance"},
                    "total_earned": {"$sum": "$total_earned"},
                    "total_donated": {"$sum": "$total_donated"},
                    "avg_balance": {"$avg": "$current_balance"},
                    "auto_donation_enabled_count": {
                        "$sum": {
                            "$cond": ["$auto_donation_settings.enabled", 1, 0]
                        }
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
            "total_wallets": 0,
            "total_balance": 0.0,
            "total_earned": 0.0,
            "total_donated": 0.0,
            "avg_balance": 0.0,
            "auto_donation_enabled_count": 0
        }

    def get_top_earners(self, limit: int = 10) -> List[Wallet]:
        """
        Get top earning wallets.

        Args:
            limit: Number of top earners to return

        Returns:
            List[Wallet]: List of top earning wallets
        """
        wallet_data = self.find_many(
            {},
            limit=limit,
            sort=[("total_earned", -1)]
        )

        return [Wallet.from_dict(data) for data in wallet_data]

    def get_top_donors(self, limit: int = 10) -> List[Wallet]:
        """
        Get top donating wallets.

        Args:
            limit: Number of top donors to return

        Returns:
            List[Wallet]: List of top donating wallets
        """
        wallet_data = self.find_many(
            {},
            limit=limit,
            sort=[("total_donated", -1)]
        )

        return [Wallet.from_dict(data) for data in wallet_data]

    def search_wallets(self, search_criteria: Dict[str, Any],
                       page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """
        Search wallets with pagination.

        Args:
            search_criteria: Search criteria dictionary
            page: Page number (1-based)
            page_size: Number of results per page

        Returns:
            Dict containing wallets and pagination info
        """
        skip = (page - 1) * page_size

        wallets_data = self.find_many(
            search_criteria,
            limit=page_size,
            skip=skip,
            sort=[("updated_at", -1)]
        )

        total_count = self.count(search_criteria)
        total_pages = (total_count + page_size - 1) // page_size

        return {
            "wallets": [Wallet.from_dict(data) for data in wallets_data],
            "pagination": {
                "page": page,
                "per_page": page_size,
                "total_items": total_count,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        }

    def delete_wallet(self, user_id: str) -> bool:
        """
        Delete a wallet by user ID.

        Args:
            user_id: User identifier

        Returns:
            bool: True if deletion was successful
        """
        return self.delete_one({"user_id": user_id})

    def bulk_update_auto_donation_settings(self, updates: List[Dict[str, Any]]) -> int:
        """
        Bulk update auto-donation settings for multiple wallets.

        Args:
            updates: List of update dictionaries with user_id and settings

        Returns:
            int: Number of wallets updated
        """
        if not self.collection or not updates:
            return 0

        bulk_operations = []
        for update in updates:
            if 'user_id' not in update or 'settings' not in update:
                continue

            bulk_operations.append({
                "updateOne": {
                    "filter": {"user_id": update['user_id']},
                    "update": {
                        "$set": {
                            "auto_donation_settings": update['settings'],
                            "updated_at": self._get_current_time()
                        }
                    }
                }
            })

        if bulk_operations:
            result = self.collection.bulk_write(bulk_operations)
            return result.modified_count

        return 0