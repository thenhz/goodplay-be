from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timezone, timedelta
from bson import ObjectId
from app.core.database import get_db
from app.core.repositories.base_repository import BaseRepository
from app.onlus.models.financial_report import FinancialReport, ReportType, ReportStatus, ReportFormat
import os


class FinancialReportRepository(BaseRepository[FinancialReport]):
    """Repository for managing financial report data operations."""

    def __init__(self):
        super().__init__()
        self.collection_name = 'financial_reports'

    def create_indexes(self):
        """Create database indexes for financial reports."""
        if self.collection is None or os.getenv('TESTING') == 'true':
            return

        try:
            self.collection.create_index([("report_type", 1), ("created_at", -1)])
            self.collection.create_index([("generated_for_id", 1), ("created_at", -1)])
            self.collection.create_index([("status", 1), ("created_at", -1)])
            self.collection.create_index([("start_date", 1), ("end_date", 1)])
            self.collection.create_index([("expiry_date", 1)])
            self.collection.create_index([("is_confidential", 1)])
            self.collection.create_index("access_permissions", background=True)
            self.collection.create_index("report_title", background=True)
        except Exception:
            pass

    def create_report(self, report: FinancialReport) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Create a new financial report."""
        try:
            report_dict = report.to_dict()
            report_dict.pop('_id', None)

            result = self.collection.insert_one(report_dict)
            report._id = result.inserted_id

            return True, "FINANCIAL_REPORT_CREATED_SUCCESS", report.to_dict()
        except Exception as e:
            return False, "FINANCIAL_REPORT_CREATION_FAILED", None

    def get_report_by_id(self, report_id: str) -> Tuple[bool, str, Optional[FinancialReport]]:
        """Get financial report by ID."""
        try:
            report_data = self.collection.find_one({"_id": ObjectId(report_id)})
            if report_data:
                report = FinancialReport.from_dict(report_data)
                return True, "FINANCIAL_REPORT_RETRIEVED_SUCCESS", report
            return False, "FINANCIAL_REPORT_NOT_FOUND", None
        except Exception as e:
            return False, "FINANCIAL_REPORT_RETRIEVAL_FAILED", None

    def get_reports_by_entity(self, entity_id: str, entity_type: str = "onlus",
                             report_type: str = None, limit: int = 50,
                             skip: int = 0) -> Tuple[bool, str, Optional[List[FinancialReport]]]:
        """Get reports for a specific entity (ONLUS or donor)."""
        try:
            query = {"generated_for_id": entity_id}

            if report_type:
                query["report_type"] = report_type

            cursor = self.collection.find(query).sort([("created_at", -1)]).skip(skip).limit(limit)
            reports = [FinancialReport.from_dict(doc) for doc in cursor]

            return True, "ENTITY_REPORTS_RETRIEVED_SUCCESS", reports
        except Exception as e:
            return False, "ENTITY_REPORTS_RETRIEVAL_FAILED", None

    def get_reports_by_type(self, report_type: str, status: str = None,
                           limit: int = 50, skip: int = 0) -> Tuple[bool, str, Optional[List[FinancialReport]]]:
        """Get reports by type with optional status filter."""
        try:
            query = {"report_type": report_type}
            if status:
                query["status"] = status

            cursor = self.collection.find(query).sort([("created_at", -1)]).skip(skip).limit(limit)
            reports = [FinancialReport.from_dict(doc) for doc in cursor]

            return True, "TYPE_REPORTS_RETRIEVED_SUCCESS", reports
        except Exception as e:
            return False, "TYPE_REPORTS_RETRIEVAL_FAILED", None

    def get_reports_by_date_range(self, start_date: datetime, end_date: datetime,
                                 report_type: str = None,
                                 limit: int = 100) -> Tuple[bool, str, Optional[List[FinancialReport]]]:
        """Get reports within a specific date range."""
        try:
            query = {
                "$or": [
                    {
                        "start_date": {"$lte": end_date},
                        "end_date": {"$gte": start_date}
                    },
                    {
                        "created_at": {"$gte": start_date, "$lte": end_date}
                    }
                ]
            }

            if report_type:
                query["report_type"] = report_type

            cursor = self.collection.find(query).sort([("start_date", -1)]).limit(limit)
            reports = [FinancialReport.from_dict(doc) for doc in cursor]

            return True, "DATE_RANGE_REPORTS_SUCCESS", reports
        except Exception as e:
            return False, "DATE_RANGE_REPORTS_FAILED", None

    def get_pending_reports(self, limit: int = 50) -> Tuple[bool, str, Optional[List[FinancialReport]]]:
        """Get reports pending generation."""
        try:
            query = {"status": ReportStatus.PENDING.value}

            cursor = self.collection.find(query).sort([("created_at", 1)]).limit(limit)
            reports = [FinancialReport.from_dict(doc) for doc in cursor]

            return True, "PENDING_REPORTS_RETRIEVED_SUCCESS", reports
        except Exception as e:
            return False, "PENDING_REPORTS_RETRIEVAL_FAILED", None

    def get_expiring_reports(self, days_ahead: int = 7) -> Tuple[bool, str, Optional[List[FinancialReport]]]:
        """Get reports expiring within specified days."""
        try:
            expiry_date = datetime.now(timezone.utc) + timedelta(days=days_ahead)
            query = {
                "expiry_date": {
                    "$lte": expiry_date,
                    "$gte": datetime.now(timezone.utc)
                },
                "status": ReportStatus.COMPLETED.value
            }

            cursor = self.collection.find(query).sort([("expiry_date", 1)])
            reports = [FinancialReport.from_dict(doc) for doc in cursor]

            return True, "EXPIRING_REPORTS_RETRIEVED_SUCCESS", reports
        except Exception as e:
            return False, "EXPIRING_REPORTS_RETRIEVAL_FAILED", None

    def get_accessible_reports(self, user_id: str, is_confidential: bool = None,
                              limit: int = 50, skip: int = 0) -> Tuple[bool, str, Optional[List[FinancialReport]]]:
        """Get reports accessible by a specific user."""
        try:
            query = {
                "$or": [
                    {"is_confidential": False},
                    {"generated_for_id": user_id},
                    {"access_permissions": {"$in": [user_id]}}
                ]
            }

            if is_confidential is not None:
                query["is_confidential"] = is_confidential

            cursor = self.collection.find(query).sort([("created_at", -1)]).skip(skip).limit(limit)
            reports = [FinancialReport.from_dict(doc) for doc in cursor]

            return True, "ACCESSIBLE_REPORTS_SUCCESS", reports
        except Exception as e:
            return False, "ACCESSIBLE_REPORTS_FAILED", None

    def search_reports(self, query_text: str, filters: Dict[str, Any] = None,
                      limit: int = 50, skip: int = 0) -> Tuple[bool, str, Optional[List[FinancialReport]]]:
        """Search reports by text and filters."""
        try:
            search_query = {
                "report_title": {"$regex": query_text, "$options": "i"}
            }

            if filters:
                for key, value in filters.items():
                    if key in ["report_type", "status", "report_format"]:
                        search_query[key] = value
                    elif key == "generated_for_id":
                        search_query["generated_for_id"] = value
                    elif key == "start_date_from":
                        search_query["start_date"] = {"$gte": value}
                    elif key == "end_date_to":
                        if "end_date" not in search_query:
                            search_query["end_date"] = {}
                        search_query["end_date"]["$lte"] = value
                    elif key == "is_confidential":
                        search_query["is_confidential"] = value

            cursor = (self.collection.find(search_query)
                     .sort([("created_at", -1)])
                     .skip(skip).limit(limit))

            reports = [FinancialReport.from_dict(doc) for doc in cursor]
            return True, "REPORTS_SEARCH_SUCCESS", reports
        except Exception as e:
            return False, "REPORTS_SEARCH_FAILED", None

    def update_report(self, report: FinancialReport) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Update financial report."""
        try:
            report.updated_at = datetime.now(timezone.utc)
            report_dict = report.to_dict()
            report_id = report_dict.pop('_id')

            self.collection.update_one(
                {"_id": report_id},
                {"$set": report_dict}
            )

            return True, "FINANCIAL_REPORT_UPDATED_SUCCESS", report.to_dict()
        except Exception as e:
            return False, "FINANCIAL_REPORT_UPDATE_FAILED", None

    def update_report_status(self, report_id: str, new_status: str,
                            file_url: str = None, file_size: int = None,
                            error_message: str = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Update report generation status."""
        try:
            update_data = {
                "status": new_status,
                "updated_at": datetime.now(timezone.utc)
            }

            if new_status == ReportStatus.GENERATING.value:
                # No additional fields needed for generating status
                pass
            elif new_status == ReportStatus.COMPLETED.value:
                update_data["generated_at"] = datetime.now(timezone.utc)
                if file_url:
                    update_data["file_url"] = file_url
                if file_size:
                    update_data["file_size"] = file_size
            elif new_status == ReportStatus.FAILED.value:
                if error_message:
                    update_data["error_message"] = error_message

            result = self.collection.update_one(
                {"_id": ObjectId(report_id)},
                {"$set": update_data}
            )

            if result.matched_count:
                return True, "REPORT_STATUS_UPDATED_SUCCESS", {"status": new_status}
            return False, "FINANCIAL_REPORT_NOT_FOUND", None
        except Exception as e:
            return False, "REPORT_STATUS_UPDATE_FAILED", None

    def mark_report_downloaded(self, report_id: str, user_id: str = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Mark report as downloaded."""
        try:
            update_data = {
                "downloaded_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }

            if user_id:
                update_data["$push"] = {
                    "metadata.download_history": {
                        "user_id": user_id,
                        "timestamp": datetime.now(timezone.utc)
                    }
                }

            result = self.collection.update_one(
                {"_id": ObjectId(report_id)},
                {"$set": update_data} if not user_id else {
                    "$set": {k: v for k, v in update_data.items() if k != "$push"},
                    "$push": update_data["$push"]
                }
            )

            if result.matched_count:
                return True, "REPORT_DOWNLOAD_MARKED_SUCCESS", {"downloaded_at": update_data["downloaded_at"]}
            return False, "FINANCIAL_REPORT_NOT_FOUND", None
        except Exception as e:
            return False, "REPORT_DOWNLOAD_MARK_FAILED", None

    def add_report_data(self, report_id: str, key: str, data: Any) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Add data to report's report_data field."""
        try:
            result = self.collection.update_one(
                {"_id": ObjectId(report_id)},
                {
                    "$set": {
                        f"report_data.{key}": data,
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )

            if result.matched_count:
                return True, "REPORT_DATA_ADDED_SUCCESS", {key: data}
            return False, "FINANCIAL_REPORT_NOT_FOUND", None
        except Exception as e:
            return False, "REPORT_DATA_ADD_FAILED", None

    def add_summary_metric(self, report_id: str, metric_name: str,
                          metric_value: float) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Add summary metric to report."""
        try:
            result = self.collection.update_one(
                {"_id": ObjectId(report_id)},
                {
                    "$set": {
                        f"summary_metrics.{metric_name}": float(metric_value),
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )

            if result.matched_count:
                return True, "SUMMARY_METRIC_ADDED_SUCCESS", {metric_name: metric_value}
            return False, "FINANCIAL_REPORT_NOT_FOUND", None
        except Exception as e:
            return False, "SUMMARY_METRIC_ADD_FAILED", None

    def add_transaction_detail(self, report_id: str,
                              transaction_data: Dict[str, Any]) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Add transaction detail to report."""
        try:
            transaction_entry = {
                **transaction_data,
                "added_at": datetime.now(timezone.utc)
            }

            result = self.collection.update_one(
                {"_id": ObjectId(report_id)},
                {
                    "$push": {"detailed_transactions": transaction_entry},
                    "$set": {"updated_at": datetime.now(timezone.utc)}
                }
            )

            if result.matched_count:
                return True, "TRANSACTION_DETAIL_ADDED_SUCCESS", transaction_entry
            return False, "FINANCIAL_REPORT_NOT_FOUND", None
        except Exception as e:
            return False, "TRANSACTION_DETAIL_ADD_FAILED", None

    def set_allocation_breakdown(self, report_id: str,
                               breakdown: Dict[str, Any]) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Set allocation breakdown data for report."""
        try:
            result = self.collection.update_one(
                {"_id": ObjectId(report_id)},
                {
                    "$set": {
                        "allocation_breakdown": breakdown,
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )

            if result.matched_count:
                return True, "ALLOCATION_BREAKDOWN_SET_SUCCESS", breakdown
            return False, "FINANCIAL_REPORT_NOT_FOUND", None
        except Exception as e:
            return False, "ALLOCATION_BREAKDOWN_SET_FAILED", None

    def grant_report_access(self, report_id: str, user_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Grant access to confidential report for specific user."""
        try:
            result = self.collection.update_one(
                {"_id": ObjectId(report_id)},
                {
                    "$addToSet": {"access_permissions": user_id},
                    "$set": {"updated_at": datetime.now(timezone.utc)}
                }
            )

            if result.matched_count:
                return True, "REPORT_ACCESS_GRANTED_SUCCESS", {"user_id": user_id}
            return False, "FINANCIAL_REPORT_NOT_FOUND", None
        except Exception as e:
            return False, "REPORT_ACCESS_GRANT_FAILED", None

    def revoke_report_access(self, report_id: str, user_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Revoke access to confidential report for specific user."""
        try:
            result = self.collection.update_one(
                {"_id": ObjectId(report_id)},
                {
                    "$pull": {"access_permissions": user_id},
                    "$set": {"updated_at": datetime.now(timezone.utc)}
                }
            )

            if result.matched_count:
                return True, "REPORT_ACCESS_REVOKED_SUCCESS", {"user_id": user_id}
            return False, "FINANCIAL_REPORT_NOT_FOUND", None
        except Exception as e:
            return False, "REPORT_ACCESS_REVOKE_FAILED", None

    def get_reports_statistics(self, start_date: datetime = None,
                              end_date: datetime = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Get statistics for financial reports."""
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
                        "total_reports": {"$sum": 1},
                        "completed_reports": {
                            "$sum": {"$cond": [{"$eq": ["$status", "completed"]}, 1, 0]}
                        },
                        "pending_reports": {
                            "$sum": {"$cond": [{"$eq": ["$status", "pending"]}, 1, 0]}
                        },
                        "failed_reports": {
                            "$sum": {"$cond": [{"$eq": ["$status", "failed"]}, 1, 0]}
                        },
                        "confidential_reports": {
                            "$sum": {"$cond": ["$is_confidential", 1, 0]}
                        },
                        "report_types": {"$push": "$report_type"},
                        "avg_file_size": {"$avg": "$file_size"},
                        "total_downloads": {"$sum": {"$cond": [{"$ne": ["$downloaded_at", None]}, 1, 0]}}
                    }
                }
            ]

            result = list(self.collection.aggregate(pipeline))
            if result:
                stats = result[0]
                stats.pop('_id', None)

                # Calculate completion rate
                total = stats.get('total_reports', 0)
                completed = stats.get('completed_reports', 0)
                stats['completion_rate'] = (completed / total * 100) if total > 0 else 0

                return True, "REPORTS_STATISTICS_SUCCESS", stats
            else:
                return True, "REPORTS_STATISTICS_SUCCESS", {
                    "total_reports": 0,
                    "completed_reports": 0,
                    "pending_reports": 0,
                    "failed_reports": 0,
                    "confidential_reports": 0,
                    "report_types": [],
                    "avg_file_size": 0,
                    "total_downloads": 0,
                    "completion_rate": 0
                }
        except Exception as e:
            return False, "REPORTS_STATISTICS_FAILED", None

    def cleanup_expired_reports(self, days_expired: int = 30) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Clean up expired reports."""
        try:
            expiry_date = datetime.now(timezone.utc) - timedelta(days=days_expired)
            query = {
                "expiry_date": {"$lt": datetime.now(timezone.utc)},
                "status": ReportStatus.COMPLETED.value,
                "created_at": {"$lt": expiry_date}
            }

            # Update status to expired instead of deleting
            result = self.collection.update_many(
                query,
                {
                    "$set": {
                        "status": ReportStatus.EXPIRED.value,
                        "updated_at": datetime.now(timezone.utc),
                        "file_url": None  # Remove file URL for expired reports
                    }
                }
            )

            return True, "EXPIRED_REPORTS_CLEANUP_SUCCESS", {
                "cleaned_up_count": result.modified_count
            }
        except Exception as e:
            return False, "EXPIRED_REPORTS_CLEANUP_FAILED", None

    def delete_report(self, report_id: str) -> Tuple[bool, str, None]:
        """Delete financial report (hard delete)."""
        try:
            result = self.collection.delete_one({"_id": ObjectId(report_id)})

            if result.deleted_count:
                return True, "FINANCIAL_REPORT_DELETED_SUCCESS", None
            return False, "FINANCIAL_REPORT_NOT_FOUND", None
        except Exception as e:
            return False, "FINANCIAL_REPORT_DELETE_FAILED", None