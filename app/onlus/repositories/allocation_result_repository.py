from __future__ import annotations
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timezone, timedelta
from bson import ObjectId
from app.core.repositories.base_repository import BaseRepository
from app.onlus.models.allocation_result import AllocationResult, AllocationResultStatus, AllocationMethod
import os


class AllocationResultRepository(BaseRepository):
    """Repository for managing allocation result data operations."""

    def __init__(self):
        super().__init__('allocation_results')

    def create_indexes(self):
        """Create database indexes for allocation results."""
        if self.collection is None or os.getenv('TESTING') == 'true':
            return

        try:
            self.collection.create_index([("request_id", 1), ("created_at", -1)])
            self.collection.create_index([("onlus_id", 1), ("created_at", -1)])
            self.collection.create_index([("status", 1), ("created_at", -1)])
            self.collection.create_index([("allocation_method", 1)])
            self.collection.create_index([("completed_at", -1)])
            self.collection.create_index("donor_ids", background=True)
            self.collection.create_index("transaction_ids", background=True)
        except Exception:
            pass

    def create_result(self, result: AllocationResult) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Create a new allocation result."""
        try:
            result_dict = result.to_dict()
            result_dict.pop('_id', None)

            insert_result = self.collection.insert_one(result_dict)
            result._id = insert_result.inserted_id

            return True, "ALLOCATION_RESULT_CREATED_SUCCESS", result.to_dict()
        except Exception as e:
            return False, "ALLOCATION_RESULT_CREATION_FAILED", None

    def get_result_by_id(self, result_id: str) -> Tuple[bool, str, Optional[AllocationResult]]:
        """Get allocation result by ID."""
        try:
            result_data = self.collection.find_one({"_id": ObjectId(result_id)})
            if result_data:
                result = AllocationResult.from_dict(result_data)
                return True, "ALLOCATION_RESULT_RETRIEVED_SUCCESS", result
            return False, "ALLOCATION_RESULT_NOT_FOUND", None
        except Exception as e:
            return False, "ALLOCATION_RESULT_RETRIEVAL_FAILED", None

    def get_result_by_request_id(self, request_id: str) -> Tuple[bool, str, Optional[AllocationResult]]:
        """Get allocation result by request ID."""
        try:
            result_data = self.collection.find_one({"request_id": request_id})
            if result_data:
                result = AllocationResult.from_dict(result_data)
                return True, "ALLOCATION_RESULT_RETRIEVED_SUCCESS", result
            return False, "ALLOCATION_RESULT_NOT_FOUND", None
        except Exception as e:
            return False, "ALLOCATION_RESULT_RETRIEVAL_FAILED", None

    def get_results_by_onlus(self, onlus_id: str, status: str = None,
                            limit: int = 50, skip: int = 0) -> Tuple[bool, str, Optional[List[AllocationResult]]]:
        """Get allocation results for a specific ONLUS."""
        try:
            query = {"onlus_id": onlus_id}
            if status:
                query["status"] = status

            cursor = self.collection.find(query).sort([("created_at", -1)]).skip(skip).limit(limit)
            results = [AllocationResult.from_dict(doc) for doc in cursor]

            return True, "ALLOCATION_RESULTS_RETRIEVED_SUCCESS", results
        except Exception as e:
            return False, "ALLOCATION_RESULTS_RETRIEVAL_FAILED", None

    def get_results_by_donor(self, donor_id: str, limit: int = 50, skip: int = 0) -> Tuple[bool, str, Optional[List[AllocationResult]]]:
        """Get allocation results for a specific donor."""
        try:
            query = {"donor_ids": donor_id}

            cursor = self.collection.find(query).sort([("created_at", -1)]).skip(skip).limit(limit)
            results = [AllocationResult.from_dict(doc) for doc in cursor]

            return True, "DONOR_ALLOCATION_RESULTS_SUCCESS", results
        except Exception as e:
            return False, "DONOR_ALLOCATION_RESULTS_FAILED", None

    def get_pending_allocations(self, limit: int = 100) -> Tuple[bool, str, Optional[List[AllocationResult]]]:
        """Get pending allocation results that need processing."""
        try:
            query = {"status": AllocationResultStatus.SCHEDULED.value}

            cursor = self.collection.find(query).sort([("created_at", 1)]).limit(limit)
            results = [AllocationResult.from_dict(doc) for doc in cursor]

            return True, "PENDING_ALLOCATIONS_RETRIEVED_SUCCESS", results
        except Exception as e:
            return False, "PENDING_ALLOCATIONS_RETRIEVAL_FAILED", None

    def get_failed_allocations(self, max_retry_count: int = 3,
                              limit: int = 50) -> Tuple[bool, str, Optional[List[AllocationResult]]]:
        """Get failed allocations that can be retried."""
        try:
            query = {
                "status": AllocationResultStatus.FAILED.value,
                "retry_count": {"$lt": max_retry_count}
            }

            cursor = self.collection.find(query).sort([("updated_at", 1)]).limit(limit)
            results = [AllocationResult.from_dict(doc) for doc in cursor]

            return True, "FAILED_ALLOCATIONS_RETRIEVED_SUCCESS", results
        except Exception as e:
            return False, "FAILED_ALLOCATIONS_RETRIEVAL_FAILED", None

    def update_result(self, result: AllocationResult) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Update allocation result."""
        try:
            result.updated_at = datetime.now(timezone.utc)
            result_dict = result.to_dict()
            result_id = result_dict.pop('_id')

            self.collection.update_one(
                {"_id": result_id},
                {"$set": result_dict}
            )

            return True, "ALLOCATION_RESULT_UPDATED_SUCCESS", result.to_dict()
        except Exception as e:
            return False, "ALLOCATION_RESULT_UPDATE_FAILED", None

    def update_result_status(self, result_id: str, new_status: str,
                            additional_data: Dict[str, Any] = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Update result status with additional data."""
        try:
            update_data = {
                "status": new_status,
                "updated_at": datetime.now(timezone.utc)
            }

            if new_status == AllocationResultStatus.IN_PROGRESS.value:
                update_data["processed_at"] = datetime.now(timezone.utc)
            elif new_status == AllocationResultStatus.COMPLETED.value:
                update_data["completed_at"] = datetime.now(timezone.utc)

            if additional_data:
                update_data.update(additional_data)

            result = self.collection.update_one(
                {"_id": ObjectId(result_id)},
                {"$set": update_data}
            )

            if result.matched_count:
                return True, "ALLOCATION_STATUS_UPDATED_SUCCESS", {"status": new_status}
            return False, "ALLOCATION_RESULT_NOT_FOUND", None
        except Exception as e:
            return False, "ALLOCATION_STATUS_UPDATE_FAILED", None

    def add_transaction_to_result(self, result_id: str, transaction_id: str,
                                 donor_id: str, amount: float) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Add a transaction to allocation result."""
        try:
            update_data = {
                "$push": {
                    "transaction_ids": transaction_id,
                    "donor_breakdown": {
                        "donor_id": donor_id,
                        "amount": float(amount),
                        "transaction_id": transaction_id,
                        "timestamp": datetime.now(timezone.utc)
                    }
                },
                "$set": {"updated_at": datetime.now(timezone.utc)}
            }

            result = self.collection.update_one(
                {"_id": ObjectId(result_id)},
                update_data
            )

            if result.matched_count:
                return True, "TRANSACTION_ADDED_SUCCESS", {
                    "transaction_id": transaction_id,
                    "donor_id": donor_id,
                    "amount": amount
                }
            return False, "ALLOCATION_RESULT_NOT_FOUND", None
        except Exception as e:
            return False, "TRANSACTION_ADD_FAILED", None

    def get_allocation_performance_metrics(self, start_date: datetime = None,
                                         end_date: datetime = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Get performance metrics for allocations."""
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
                        "total_allocations": {"$sum": 1},
                        "total_allocated_amount": {"$sum": "$allocated_amount"},
                        "total_donation_amount": {"$sum": "$total_donations_amount"},
                        "avg_allocated_amount": {"$avg": "$allocated_amount"},
                        "successful_allocations": {
                            "$sum": {"$cond": [
                                {"$in": ["$status", ["completed", "partial"]]}, 1, 0
                            ]}
                        },
                        "failed_allocations": {
                            "$sum": {"$cond": [{"$eq": ["$status", "failed"]}, 1, 0]}
                        },
                        "avg_processing_time": {"$avg": "$processing_time_seconds"},
                        "automatic_allocations": {
                            "$sum": {"$cond": [{"$eq": ["$allocation_method", "automatic"]}, 1, 0]}
                        },
                        "manual_allocations": {
                            "$sum": {"$cond": [{"$eq": ["$allocation_method", "manual"]}, 1, 0]}
                        },
                        "emergency_allocations": {
                            "$sum": {"$cond": [{"$eq": ["$allocation_method", "emergency"]}, 1, 0]}
                        },
                        "avg_efficiency_ratio": {"$avg": "$efficiency_ratio"}
                    }
                }
            ]

            result = list(self.collection.aggregate(pipeline))
            if result:
                metrics = result[0]
                metrics.pop('_id', None)

                # Calculate success rate
                total = metrics.get('total_allocations', 0)
                successful = metrics.get('successful_allocations', 0)
                metrics['success_rate'] = (successful / total * 100) if total > 0 else 0

                return True, "ALLOCATION_METRICS_SUCCESS", metrics
            else:
                return True, "ALLOCATION_METRICS_SUCCESS", {
                    "total_allocations": 0,
                    "total_allocated_amount": 0,
                    "total_donation_amount": 0,
                    "avg_allocated_amount": 0,
                    "successful_allocations": 0,
                    "failed_allocations": 0,
                    "avg_processing_time": 0,
                    "automatic_allocations": 0,
                    "manual_allocations": 0,
                    "emergency_allocations": 0,
                    "avg_efficiency_ratio": 0,
                    "success_rate": 0
                }
        except Exception as e:
            return False, "ALLOCATION_METRICS_FAILED", None

    def get_allocation_trends(self, days: int = 30) -> Tuple[bool, str, Optional[List[Dict[str, Any]]]]:
        """Get allocation trends over specified days."""
        try:
            start_date = datetime.now(timezone.utc) - timedelta(days=days)

            pipeline = [
                {"$match": {"created_at": {"$gte": start_date}}},
                {
                    "$group": {
                        "_id": {
                            "year": {"$year": "$created_at"},
                            "month": {"$month": "$created_at"},
                            "day": {"$dayOfMonth": "$created_at"}
                        },
                        "daily_allocations": {"$sum": 1},
                        "daily_amount": {"$sum": "$allocated_amount"},
                        "daily_success_rate": {
                            "$avg": {"$cond": [
                                {"$in": ["$status", ["completed", "partial"]]}, 1, 0
                            ]}
                        }
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        "date": {
                            "$dateFromParts": {
                                "year": "$_id.year",
                                "month": "$_id.month",
                                "day": "$_id.day"
                            }
                        },
                        "allocations": "$daily_allocations",
                        "amount": "$daily_amount",
                        "success_rate": {"$multiply": ["$daily_success_rate", 100]}
                    }
                },
                {"$sort": {"date": 1}}
            ]

            trends = list(self.collection.aggregate(pipeline))
            return True, "ALLOCATION_TRENDS_SUCCESS", trends
        except Exception as e:
            return False, "ALLOCATION_TRENDS_FAILED", None

    def get_onlus_allocation_summary(self, onlus_id: str, months: int = 12) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Get allocation summary for a specific ONLUS."""
        try:
            start_date = datetime.now(timezone.utc) - timedelta(days=months * 30)

            pipeline = [
                {"$match": {
                    "onlus_id": onlus_id,
                    "created_at": {"$gte": start_date}
                }},
                {
                    "$group": {
                        "_id": None,
                        "total_allocations": {"$sum": 1},
                        "total_amount_received": {"$sum": "$allocated_amount"},
                        "avg_allocation_amount": {"$avg": "$allocated_amount"},
                        "successful_allocations": {
                            "$sum": {"$cond": [
                                {"$in": ["$status", ["completed", "partial"]]}, 1, 0
                            ]}
                        },
                        "unique_donors": {"$addToSet": "$donor_ids"},
                        "allocation_methods": {"$push": "$allocation_method"}
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        "total_allocations": 1,
                        "total_amount_received": 1,
                        "avg_allocation_amount": 1,
                        "successful_allocations": 1,
                        "success_rate": {
                            "$multiply": [
                                {"$divide": ["$successful_allocations", "$total_allocations"]},
                                100
                            ]
                        },
                        "unique_donor_count": {"$size": {"$reduce": {
                            "input": "$unique_donors",
                            "initialValue": [],
                            "in": {"$setUnion": ["$$value", "$$this"]}
                        }}},
                        "allocation_methods": 1
                    }
                }
            ]

            result = list(self.collection.aggregate(pipeline))
            if result:
                summary = result[0]
                return True, "ONLUS_ALLOCATION_SUMMARY_SUCCESS", summary
            else:
                return True, "ONLUS_ALLOCATION_SUMMARY_SUCCESS", {
                    "total_allocations": 0,
                    "total_amount_received": 0,
                    "avg_allocation_amount": 0,
                    "successful_allocations": 0,
                    "success_rate": 0,
                    "unique_donor_count": 0,
                    "allocation_methods": []
                }
        except Exception as e:
            return False, "ONLUS_ALLOCATION_SUMMARY_FAILED", None

    def delete_result(self, result_id: str) -> Tuple[bool, str, None]:
        """Delete allocation result (hard delete for cleanup)."""
        try:
            result = self.collection.delete_one({"_id": ObjectId(result_id)})

            if result.deleted_count:
                return True, "ALLOCATION_RESULT_DELETED_SUCCESS", None
            return False, "ALLOCATION_RESULT_NOT_FOUND", None
        except Exception as e:
            return False, "ALLOCATION_RESULT_DELETE_FAILED", None