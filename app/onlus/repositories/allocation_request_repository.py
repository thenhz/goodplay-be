from __future__ import annotations
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timezone, timedelta
from bson import ObjectId
from app.core.repositories.base_repository import BaseRepository
from app.onlus.models.allocation_request import AllocationRequest, AllocationRequestStatus, AllocationPriority
import os


class AllocationRequestRepository(BaseRepository):
    """Repository for managing allocation request data operations."""

    def __init__(self):
        super().__init__('allocation_requests')

    def create_indexes(self):
        """Create database indexes for allocation requests."""
        if self.collection is None or os.getenv('TESTING') == 'true':
            return

        try:
            self.collection.create_index([("onlus_id", 1), ("created_at", -1)])
            self.collection.create_index([("status", 1), ("priority", -1)])
            self.collection.create_index([("deadline", 1), ("status", 1)])
            self.collection.create_index([("urgency_level", -1), ("created_at", -1)])
            self.collection.create_index([("category", 1), ("status", 1)])
            self.collection.create_index([("allocation_score", -1)])
            self.collection.create_index("project_title", background=True)
        except Exception:
            pass

    def create_request(self, request: AllocationRequest) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Create a new allocation request."""
        try:
            request_dict = request.to_dict()
            request_dict.pop('_id', None)

            result = self.collection.insert_one(request_dict)
            request._id = result.inserted_id

            return True, "ALLOCATION_REQUEST_CREATED_SUCCESS", request.to_dict()
        except Exception as e:
            return False, "ALLOCATION_REQUEST_CREATION_FAILED", None

    def get_request_by_id(self, request_id: str) -> Tuple[bool, str, Optional[AllocationRequest]]:
        """Get allocation request by ID."""
        try:
            request_data = self.collection.find_one({"_id": ObjectId(request_id)})
            if request_data:
                request = AllocationRequest.from_dict(request_data)
                return True, "ALLOCATION_REQUEST_RETRIEVED_SUCCESS", request
            return False, "ALLOCATION_REQUEST_NOT_FOUND", None
        except Exception as e:
            return False, "ALLOCATION_REQUEST_RETRIEVAL_FAILED", None

    def get_requests_by_onlus(self, onlus_id: str, status: str = None,
                             limit: int = 50, skip: int = 0) -> Tuple[bool, str, Optional[List[AllocationRequest]]]:
        """Get allocation requests for a specific ONLUS."""
        try:
            query = {"onlus_id": onlus_id}
            if status:
                query["status"] = status

            cursor = self.collection.find(query).sort([("created_at", -1)]).skip(skip).limit(limit)
            requests = [AllocationRequest.from_dict(doc) for doc in cursor]

            return True, "ALLOCATION_REQUESTS_RETRIEVED_SUCCESS", requests
        except Exception as e:
            return False, "ALLOCATION_REQUESTS_RETRIEVAL_FAILED", None

    def get_pending_requests(self, limit: int = 100, skip: int = 0) -> Tuple[bool, str, Optional[List[AllocationRequest]]]:
        """Get pending allocation requests ordered by priority and urgency."""
        try:
            query = {"status": AllocationRequestStatus.PENDING.value}

            cursor = (self.collection.find(query)
                     .sort([("priority", -1), ("urgency_level", -1), ("created_at", 1)])
                     .skip(skip).limit(limit))

            requests = [AllocationRequest.from_dict(doc) for doc in cursor]
            return True, "PENDING_REQUESTS_RETRIEVED_SUCCESS", requests
        except Exception as e:
            return False, "PENDING_REQUESTS_RETRIEVAL_FAILED", None

    def get_emergency_requests(self) -> Tuple[bool, str, Optional[List[AllocationRequest]]]:
        """Get emergency allocation requests."""
        try:
            query = {
                "priority": AllocationPriority.EMERGENCY.value,
                "status": {"$in": [AllocationRequestStatus.PENDING.value,
                                 AllocationRequestStatus.APPROVED.value]}
            }

            cursor = self.collection.find(query).sort([("created_at", 1)])
            requests = [AllocationRequest.from_dict(doc) for doc in cursor]

            return True, "EMERGENCY_REQUESTS_RETRIEVED_SUCCESS", requests
        except Exception as e:
            return False, "EMERGENCY_REQUESTS_RETRIEVAL_FAILED", None

    def get_expiring_requests(self, days_ahead: int = 7) -> Tuple[bool, str, Optional[List[AllocationRequest]]]:
        """Get requests expiring within specified days."""
        try:
            expiry_date = datetime.now(timezone.utc) + timedelta(days=days_ahead)
            query = {
                "deadline": {"$lte": expiry_date, "$gte": datetime.now(timezone.utc)},
                "status": {"$in": [AllocationRequestStatus.PENDING.value,
                                 AllocationRequestStatus.APPROVED.value]}
            }

            cursor = self.collection.find(query).sort([("deadline", 1)])
            requests = [AllocationRequest.from_dict(doc) for doc in cursor]

            return True, "EXPIRING_REQUESTS_RETRIEVED_SUCCESS", requests
        except Exception as e:
            return False, "EXPIRING_REQUESTS_RETRIEVAL_FAILED", None

    def search_requests(self, query_text: str, filters: Dict[str, Any] = None,
                       limit: int = 50, skip: int = 0) -> Tuple[bool, str, Optional[List[AllocationRequest]]]:
        """Search allocation requests by text and filters."""
        try:
            search_query = {
                "$or": [
                    {"project_title": {"$regex": query_text, "$options": "i"}},
                    {"project_description": {"$regex": query_text, "$options": "i"}},
                    {"expected_impact": {"$regex": query_text, "$options": "i"}}
                ]
            }

            if filters:
                for key, value in filters.items():
                    if key in ["status", "category", "priority"]:
                        search_query[key] = value
                    elif key == "urgency_min":
                        search_query["urgency_level"] = {"$gte": value}
                    elif key == "amount_min":
                        search_query["requested_amount"] = {"$gte": value}
                    elif key == "amount_max":
                        if "requested_amount" not in search_query:
                            search_query["requested_amount"] = {}
                        search_query["requested_amount"]["$lte"] = value

            cursor = (self.collection.find(search_query)
                     .sort([("allocation_score", -1), ("created_at", -1)])
                     .skip(skip).limit(limit))

            requests = [AllocationRequest.from_dict(doc) for doc in cursor]
            return True, "REQUESTS_SEARCH_SUCCESS", requests
        except Exception as e:
            return False, "REQUESTS_SEARCH_FAILED", None

    def update_request(self, request: AllocationRequest) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Update allocation request."""
        try:
            request.updated_at = datetime.now(timezone.utc)
            request_dict = request.to_dict()
            request_id = request_dict.pop('_id')

            self.collection.update_one(
                {"_id": request_id},
                {"$set": request_dict}
            )

            return True, "ALLOCATION_REQUEST_UPDATED_SUCCESS", request.to_dict()
        except Exception as e:
            return False, "ALLOCATION_REQUEST_UPDATE_FAILED", None

    def update_request_status(self, request_id: str, new_status: str,
                             notes: str = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Update request status with notes."""
        try:
            update_data = {
                "status": new_status,
                "updated_at": datetime.now(timezone.utc)
            }

            if new_status == AllocationRequestStatus.APPROVED.value and notes:
                update_data["approval_notes"] = notes
            elif new_status == AllocationRequestStatus.REJECTED.value and notes:
                update_data["rejection_reason"] = notes
            elif new_status == AllocationRequestStatus.COMPLETED.value:
                update_data["processed_at"] = datetime.now(timezone.utc)

            result = self.collection.update_one(
                {"_id": ObjectId(request_id)},
                {"$set": update_data}
            )

            if result.matched_count:
                return True, "REQUEST_STATUS_UPDATED_SUCCESS", {"status": new_status}
            return False, "ALLOCATION_REQUEST_NOT_FOUND", None
        except Exception as e:
            return False, "REQUEST_STATUS_UPDATE_FAILED", None

    def update_allocation_score(self, request_id: str, score: float) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Update allocation score for a request."""
        try:
            result = self.collection.update_one(
                {"_id": ObjectId(request_id)},
                {
                    "$set": {
                        "allocation_score": float(score),
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )

            if result.matched_count:
                return True, "ALLOCATION_SCORE_UPDATED_SUCCESS", {"score": score}
            return False, "ALLOCATION_REQUEST_NOT_FOUND", None
        except Exception as e:
            return False, "ALLOCATION_SCORE_UPDATE_FAILED", None

    def get_requests_statistics(self, start_date: datetime = None,
                              end_date: datetime = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Get statistics for allocation requests."""
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
                        "total_requests": {"$sum": 1},
                        "total_amount_requested": {"$sum": "$requested_amount"},
                        "avg_amount_requested": {"$avg": "$requested_amount"},
                        "pending_requests": {
                            "$sum": {"$cond": [{"$eq": ["$status", "pending"]}, 1, 0]}
                        },
                        "approved_requests": {
                            "$sum": {"$cond": [{"$eq": ["$status", "approved"]}, 1, 0]}
                        },
                        "completed_requests": {
                            "$sum": {"$cond": [{"$eq": ["$status", "completed"]}, 1, 0]}
                        },
                        "rejected_requests": {
                            "$sum": {"$cond": [{"$eq": ["$status", "rejected"]}, 1, 0]}
                        },
                        "emergency_requests": {
                            "$sum": {"$cond": [{"$eq": ["$priority", 5]}, 1, 0]}
                        },
                        "avg_allocation_score": {"$avg": "$allocation_score"}
                    }
                }
            ]

            result = list(self.collection.aggregate(pipeline))
            if result:
                stats = result[0]
                stats.pop('_id', None)
                return True, "REQUESTS_STATISTICS_SUCCESS", stats
            else:
                return True, "REQUESTS_STATISTICS_SUCCESS", {
                    "total_requests": 0,
                    "total_amount_requested": 0,
                    "avg_amount_requested": 0,
                    "pending_requests": 0,
                    "approved_requests": 0,
                    "completed_requests": 0,
                    "rejected_requests": 0,
                    "emergency_requests": 0,
                    "avg_allocation_score": 0
                }
        except Exception as e:
            return False, "REQUESTS_STATISTICS_FAILED", None

    def delete_request(self, request_id: str) -> Tuple[bool, str, None]:
        """Delete allocation request (soft delete by updating status)."""
        try:
            result = self.collection.update_one(
                {"_id": ObjectId(request_id)},
                {
                    "$set": {
                        "status": AllocationRequestStatus.CANCELLED.value,
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )

            if result.matched_count:
                return True, "ALLOCATION_REQUEST_DELETED_SUCCESS", None
            return False, "ALLOCATION_REQUEST_NOT_FOUND", None
        except Exception as e:
            return False, "ALLOCATION_REQUEST_DELETE_FAILED", None

    def get_requests_by_category(self, category: str, status: str = None,
                               limit: int = 50) -> Tuple[bool, str, Optional[List[AllocationRequest]]]:
        """Get requests by category with optional status filter."""
        try:
            query = {"category": category}
            if status:
                query["status"] = status

            cursor = (self.collection.find(query)
                     .sort([("allocation_score", -1), ("created_at", -1)])
                     .limit(limit))

            requests = [AllocationRequest.from_dict(doc) for doc in cursor]
            return True, "CATEGORY_REQUESTS_RETRIEVED_SUCCESS", requests
        except Exception as e:
            return False, "CATEGORY_REQUESTS_RETRIEVAL_FAILED", None

    def get_high_priority_requests(self, min_score: float = 80.0,
                                  limit: int = 20) -> Tuple[bool, str, Optional[List[AllocationRequest]]]:
        """Get high-priority requests based on allocation score."""
        try:
            query = {
                "allocation_score": {"$gte": min_score},
                "status": {"$in": [AllocationRequestStatus.PENDING.value,
                                 AllocationRequestStatus.APPROVED.value]}
            }

            cursor = (self.collection.find(query)
                     .sort([("allocation_score", -1), ("priority", -1)])
                     .limit(limit))

            requests = [AllocationRequest.from_dict(doc) for doc in cursor]
            return True, "HIGH_PRIORITY_REQUESTS_SUCCESS", requests
        except Exception as e:
            return False, "HIGH_PRIORITY_REQUESTS_FAILED", None