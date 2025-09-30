from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timezone, timedelta
from bson import ObjectId
from app.core.database import get_db
from app.core.repositories.base_repository import BaseRepository
from app.onlus.models.funding_pool import FundingPool, FundingPoolStatus, FundingPoolType
import os


class FundingPoolRepository(BaseRepository[FundingPool]):
    """Repository for managing funding pool data operations."""

    def __init__(self):
        super().__init__()
        self.collection_name = 'funding_pools'

    def create_indexes(self):
        """Create database indexes for funding pools."""
        if self.collection is None or os.getenv('TESTING') == 'true':
            return

        try:
            self.collection.create_index([("pool_type", 1), ("status", 1)])
            self.collection.create_index([("status", 1), ("available_balance", -1)])
            self.collection.create_index([("expiry_date", 1)])
            self.collection.create_index([("priority_weight", -1)])
            self.collection.create_index("category_restrictions", background=True)
            self.collection.create_index("geographical_restrictions", background=True)
            self.collection.create_index([("auto_allocation_enabled", 1), ("status", 1)])
        except Exception:
            pass

    def create_pool(self, pool: FundingPool) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Create a new funding pool."""
        try:
            pool_dict = pool.to_dict()
            pool_dict.pop('_id', None)

            result = self.collection.insert_one(pool_dict)
            pool._id = result.inserted_id

            return True, "FUNDING_POOL_CREATED_SUCCESS", pool.to_dict()
        except Exception as e:
            return False, "FUNDING_POOL_CREATION_FAILED", None

    def get_pool_by_id(self, pool_id: str) -> Tuple[bool, str, Optional[FundingPool]]:
        """Get funding pool by ID."""
        try:
            pool_data = self.collection.find_one({"_id": ObjectId(pool_id)})
            if pool_data:
                pool = FundingPool.from_dict(pool_data)
                return True, "FUNDING_POOL_RETRIEVED_SUCCESS", pool
            return False, "FUNDING_POOL_NOT_FOUND", None
        except Exception as e:
            return False, "FUNDING_POOL_RETRIEVAL_FAILED", None

    def get_pool_by_name(self, pool_name: str) -> Tuple[bool, str, Optional[FundingPool]]:
        """Get funding pool by name."""
        try:
            pool_data = self.collection.find_one({"pool_name": pool_name})
            if pool_data:
                pool = FundingPool.from_dict(pool_data)
                return True, "FUNDING_POOL_RETRIEVED_SUCCESS", pool
            return False, "FUNDING_POOL_NOT_FOUND", None
        except Exception as e:
            return False, "FUNDING_POOL_RETRIEVAL_FAILED", None

    def get_active_pools(self, pool_type: str = None, category: str = None,
                        limit: int = 50) -> Tuple[bool, str, Optional[List[FundingPool]]]:
        """Get active funding pools with optional filters."""
        try:
            query = {"status": FundingPoolStatus.ACTIVE.value}

            if pool_type:
                query["pool_type"] = pool_type

            if category:
                query["category_restrictions"] = {"$in": [category]}

            cursor = (self.collection.find(query)
                     .sort([("priority_weight", -1), ("available_balance", -1)])
                     .limit(limit))

            pools = [FundingPool.from_dict(doc) for doc in cursor]
            return True, "ACTIVE_POOLS_RETRIEVED_SUCCESS", pools
        except Exception as e:
            return False, "ACTIVE_POOLS_RETRIEVAL_FAILED", None

    def get_pools_for_allocation(self, amount: float, category: str = None,
                               geography: str = None) -> Tuple[bool, str, Optional[List[FundingPool]]]:
        """Get pools available for specific allocation criteria."""
        try:
            query = {
                "status": FundingPoolStatus.ACTIVE.value,
                "auto_allocation_enabled": True,
                "available_balance": {"$gte": amount}
            }

            # Add minimum allocation constraint
            query["$or"] = [
                {"minimum_allocation": {"$lte": amount}},
                {"minimum_allocation": {"$exists": False}},
                {"minimum_allocation": 0}
            ]

            # Add maximum allocation constraint
            if amount > 0:
                query["$or"].extend([
                    {"maximum_allocation": {"$gte": amount}},
                    {"maximum_allocation": {"$exists": False}},
                    {"maximum_allocation": None}
                ])

            # Category restrictions
            if category:
                query["$or"].extend([
                    {"category_restrictions": {"$in": [category]}},
                    {"category_restrictions": {"$size": 0}}
                ])

            # Geographical restrictions
            if geography:
                query["$or"].extend([
                    {"geographical_restrictions": {"$in": [geography]}},
                    {"geographical_restrictions": {"$size": 0}}
                ])

            # Check expiry date
            query["$or"].extend([
                {"expiry_date": {"$gt": datetime.now(timezone.utc)}},
                {"expiry_date": {"$exists": False}},
                {"expiry_date": None}
            ])

            cursor = self.collection.find(query).sort([("priority_weight", -1)])
            pools = [FundingPool.from_dict(doc) for doc in cursor]

            return True, "ALLOCATION_POOLS_RETRIEVED_SUCCESS", pools
        except Exception as e:
            return False, "ALLOCATION_POOLS_RETRIEVAL_FAILED", None

    def get_pools_by_type(self, pool_type: str, status: str = None,
                         limit: int = 50) -> Tuple[bool, str, Optional[List[FundingPool]]]:
        """Get pools by type with optional status filter."""
        try:
            query = {"pool_type": pool_type}
            if status:
                query["status"] = status

            cursor = (self.collection.find(query)
                     .sort([("available_balance", -1)])
                     .limit(limit))

            pools = [FundingPool.from_dict(doc) for doc in cursor]
            return True, "POOL_TYPE_RETRIEVED_SUCCESS", pools
        except Exception as e:
            return False, "POOL_TYPE_RETRIEVAL_FAILED", None

    def get_expiring_pools(self, days_ahead: int = 30) -> Tuple[bool, str, Optional[List[FundingPool]]]:
        """Get pools expiring within specified days."""
        try:
            expiry_date = datetime.now(timezone.utc) + timedelta(days=days_ahead)
            query = {
                "expiry_date": {
                    "$lte": expiry_date,
                    "$gte": datetime.now(timezone.utc)
                },
                "status": FundingPoolStatus.ACTIVE.value
            }

            cursor = self.collection.find(query).sort([("expiry_date", 1)])
            pools = [FundingPool.from_dict(doc) for doc in cursor]

            return True, "EXPIRING_POOLS_RETRIEVED_SUCCESS", pools
        except Exception as e:
            return False, "EXPIRING_POOLS_RETRIEVAL_FAILED", None

    def get_depleted_pools(self, threshold: float = 100.0) -> Tuple[bool, str, Optional[List[FundingPool]]]:
        """Get pools that are depleted or below threshold."""
        try:
            query = {
                "available_balance": {"$lt": threshold},
                "status": {"$in": [FundingPoolStatus.ACTIVE.value, FundingPoolStatus.DEPLETED.value]}
            }

            cursor = self.collection.find(query).sort([("available_balance", 1)])
            pools = [FundingPool.from_dict(doc) for doc in cursor]

            return True, "DEPLETED_POOLS_RETRIEVED_SUCCESS", pools
        except Exception as e:
            return False, "DEPLETED_POOLS_RETRIEVAL_FAILED", None

    def update_pool(self, pool: FundingPool) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Update funding pool."""
        try:
            pool.updated_at = datetime.now(timezone.utc)
            pool_dict = pool.to_dict()
            pool_id = pool_dict.pop('_id')

            self.collection.update_one(
                {"_id": pool_id},
                {"$set": pool_dict}
            )

            return True, "FUNDING_POOL_UPDATED_SUCCESS", pool.to_dict()
        except Exception as e:
            return False, "FUNDING_POOL_UPDATE_FAILED", None

    def add_funds_to_pool(self, pool_id: str, amount: float,
                         transaction_id: str = None,
                         source_info: Dict[str, Any] = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Add funds to a specific pool."""
        try:
            if amount <= 0:
                return False, "INVALID_FUND_AMOUNT", None

            update_data = {
                "$inc": {
                    "total_balance": amount,
                    "available_balance": amount
                },
                "$set": {"updated_at": datetime.now(timezone.utc)}
            }

            if transaction_id:
                update_data["$push"] = {"source_transactions": transaction_id}

            # Add fund entry to metadata
            fund_entry = {
                "amount": amount,
                "transaction_id": transaction_id,
                "source_info": source_info or {},
                "timestamp": datetime.now(timezone.utc)
            }
            update_data["$push"]["metadata.fund_additions"] = fund_entry

            result = self.collection.update_one(
                {"_id": ObjectId(pool_id)},
                update_data
            )

            if result.matched_count:
                # Update status if pool was depleted
                self.collection.update_one(
                    {"_id": ObjectId(pool_id), "status": FundingPoolStatus.DEPLETED.value},
                    {"$set": {"status": FundingPoolStatus.ACTIVE.value}}
                )

                return True, "FUNDS_ADDED_SUCCESS", {"amount": amount}
            return False, "FUNDING_POOL_NOT_FOUND", None
        except Exception as e:
            return False, "FUNDS_ADD_FAILED", None

    def allocate_funds_from_pool(self, pool_id: str, amount: float,
                                allocation_id: str, onlus_id: str,
                                request_id: str = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Allocate funds from a specific pool."""
        try:
            if amount <= 0:
                return False, "INVALID_ALLOCATION_AMOUNT", None

            # Get current pool state
            pool_data = self.collection.find_one({"_id": ObjectId(pool_id)})
            if not pool_data:
                return False, "FUNDING_POOL_NOT_FOUND", None

            available = pool_data.get('available_balance', 0)
            reserved = pool_data.get('reserved_balance', 0)

            if amount > (available + reserved):
                return False, "INSUFFICIENT_FUNDS", None

            # Calculate deduction from available and reserved
            deduct_available = min(amount, available)
            deduct_reserved = amount - deduct_available

            update_data = {
                "$inc": {
                    "available_balance": -deduct_available,
                    "reserved_balance": -deduct_reserved,
                    "allocated_balance": amount
                },
                "$set": {
                    "updated_at": datetime.now(timezone.utc),
                    "last_allocation_at": datetime.now(timezone.utc)
                },
                "$push": {
                    "allocation_history": {
                        "allocation_id": allocation_id,
                        "onlus_id": onlus_id,
                        "request_id": request_id,
                        "amount": amount,
                        "timestamp": datetime.now(timezone.utc)
                    }
                }
            }

            result = self.collection.update_one(
                {"_id": ObjectId(pool_id)},
                update_data
            )

            if result.matched_count:
                # Update status if depleted
                new_available = available - deduct_available
                new_reserved = reserved - deduct_reserved
                if new_available <= 0 and new_reserved <= 0:
                    self.collection.update_one(
                        {"_id": ObjectId(pool_id)},
                        {"$set": {"status": FundingPoolStatus.DEPLETED.value}}
                    )

                return True, "FUNDS_ALLOCATED_SUCCESS", {
                    "amount": amount,
                    "allocation_id": allocation_id,
                    "remaining_balance": new_available + new_reserved
                }
            return False, "FUNDING_POOL_NOT_FOUND", None
        except Exception as e:
            return False, "FUNDS_ALLOCATION_FAILED", None

    def reserve_funds_in_pool(self, pool_id: str, amount: float,
                             reservation_id: str = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Reserve funds in a specific pool."""
        try:
            if amount <= 0:
                return False, "INVALID_RESERVATION_AMOUNT", None

            reservation_id = reservation_id or str(ObjectId())

            update_data = {
                "$inc": {
                    "available_balance": -amount,
                    "reserved_balance": amount
                },
                "$set": {"updated_at": datetime.now(timezone.utc)},
                "$push": {
                    "metadata.reservations": {
                        "amount": amount,
                        "reservation_id": reservation_id,
                        "timestamp": datetime.now(timezone.utc)
                    }
                }
            }

            result = self.collection.update_one(
                {
                    "_id": ObjectId(pool_id),
                    "available_balance": {"$gte": amount}
                },
                update_data
            )

            if result.matched_count:
                return True, "FUNDS_RESERVED_SUCCESS", {
                    "amount": amount,
                    "reservation_id": reservation_id
                }
            return False, "INSUFFICIENT_AVAILABLE_FUNDS", None
        except Exception as e:
            return False, "FUNDS_RESERVATION_FAILED", None

    def release_reservation(self, pool_id: str, reservation_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Release reserved funds back to available balance."""
        try:
            # Find the reservation
            pool_data = self.collection.find_one({"_id": ObjectId(pool_id)})
            if not pool_data:
                return False, "FUNDING_POOL_NOT_FOUND", None

            reservations = pool_data.get('metadata', {}).get('reservations', [])
            reservation_amount = None

            for reservation in reservations:
                if reservation.get('reservation_id') == reservation_id:
                    reservation_amount = reservation['amount']
                    break

            if reservation_amount is None:
                return False, "RESERVATION_NOT_FOUND", None

            update_data = {
                "$inc": {
                    "available_balance": reservation_amount,
                    "reserved_balance": -reservation_amount
                },
                "$set": {"updated_at": datetime.now(timezone.utc)},
                "$pull": {
                    "metadata.reservations": {"reservation_id": reservation_id}
                }
            }

            result = self.collection.update_one(
                {"_id": ObjectId(pool_id)},
                update_data
            )

            if result.matched_count:
                return True, "RESERVATION_RELEASED_SUCCESS", {
                    "amount": reservation_amount,
                    "reservation_id": reservation_id
                }
            return False, "RESERVATION_RELEASE_FAILED", None
        except Exception as e:
            return False, "RESERVATION_RELEASE_FAILED", None

    def get_pool_statistics(self, start_date: datetime = None,
                          end_date: datetime = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Get statistics for funding pools."""
        try:
            match_stage = {}
            if start_date or end_date:
                date_filter = {}
                if start_date:
                    date_filter["$gte"] = start_date
                if end_date:
                    date_filter["$lte"] = end_date
                match_stage["created_at"] = date_filter

            pipeline = [
                {"$match": match_stage},
                {
                    "$group": {
                        "_id": None,
                        "total_pools": {"$sum": 1},
                        "total_balance": {"$sum": "$total_balance"},
                        "total_available": {"$sum": "$available_balance"},
                        "total_allocated": {"$sum": "$allocated_balance"},
                        "total_reserved": {"$sum": "$reserved_balance"},
                        "active_pools": {
                            "$sum": {"$cond": [{"$eq": ["$status", "active"]}, 1, 0]}
                        },
                        "depleted_pools": {
                            "$sum": {"$cond": [{"$eq": ["$status", "depleted"]}, 1, 0]}
                        },
                        "auto_enabled_pools": {
                            "$sum": {"$cond": ["$auto_allocation_enabled", 1, 0]}
                        },
                        "avg_utilization": {"$avg": "$utilization_rate"},
                        "avg_availability": {"$avg": "$availability_rate"}
                    }
                }
            ]

            result = list(self.collection.aggregate(pipeline))
            if result:
                stats = result[0]
                stats.pop('_id', None)
                return True, "POOL_STATISTICS_SUCCESS", stats
            else:
                return True, "POOL_STATISTICS_SUCCESS", {
                    "total_pools": 0,
                    "total_balance": 0,
                    "total_available": 0,
                    "total_allocated": 0,
                    "total_reserved": 0,
                    "active_pools": 0,
                    "depleted_pools": 0,
                    "auto_enabled_pools": 0,
                    "avg_utilization": 0,
                    "avg_availability": 0
                }
        except Exception as e:
            return False, "POOL_STATISTICS_FAILED", None

    def pause_pool(self, pool_id: str, reason: str = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Pause a funding pool."""
        try:
            update_data = {
                "status": FundingPoolStatus.PAUSED.value,
                "updated_at": datetime.now(timezone.utc)
            }

            if reason:
                update_data["metadata.pause_reason"] = reason

            result = self.collection.update_one(
                {"_id": ObjectId(pool_id)},
                {"$set": update_data}
            )

            if result.matched_count:
                return True, "POOL_PAUSED_SUCCESS", {"status": "paused"}
            return False, "FUNDING_POOL_NOT_FOUND", None
        except Exception as e:
            return False, "POOL_PAUSE_FAILED", None

    def reactivate_pool(self, pool_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Reactivate a paused funding pool."""
        try:
            # Get pool to check balance
            pool_data = self.collection.find_one({"_id": ObjectId(pool_id)})
            if not pool_data:
                return False, "FUNDING_POOL_NOT_FOUND", None

            available = pool_data.get('available_balance', 0)
            reserved = pool_data.get('reserved_balance', 0)

            new_status = FundingPoolStatus.ACTIVE.value if (available + reserved) > 0 else FundingPoolStatus.DEPLETED.value

            update_data = {
                "status": new_status,
                "updated_at": datetime.now(timezone.utc)
            }

            result = self.collection.update_one(
                {"_id": ObjectId(pool_id)},
                {
                    "$set": update_data,
                    "$unset": {"metadata.pause_reason": ""}
                }
            )

            if result.matched_count:
                return True, "POOL_REACTIVATED_SUCCESS", {"status": new_status}
            return False, "FUNDING_POOL_NOT_FOUND", None
        except Exception as e:
            return False, "POOL_REACTIVATION_FAILED", None

    def delete_pool(self, pool_id: str) -> Tuple[bool, str, None]:
        """Delete funding pool (only if empty)."""
        try:
            # Check if pool has any balance
            pool_data = self.collection.find_one({"_id": ObjectId(pool_id)})
            if not pool_data:
                return False, "FUNDING_POOL_NOT_FOUND", None

            total_balance = pool_data.get('total_balance', 0)
            if total_balance > 0:
                return False, "POOL_NOT_EMPTY_DELETE_FAILED", None

            result = self.collection.delete_one({"_id": ObjectId(pool_id)})

            if result.deleted_count:
                return True, "FUNDING_POOL_DELETED_SUCCESS", None
            return False, "FUNDING_POOL_NOT_FOUND", None
        except Exception as e:
            return False, "FUNDING_POOL_DELETE_FAILED", None