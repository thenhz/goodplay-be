from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
from bson import ObjectId
from app.core.repositories.base_repository import BaseRepository
from app.onlus.models.onlus_application import ONLUSApplication, ApplicationStatus, ApplicationPhase
import os


class ONLUSApplicationRepository(BaseRepository):
    """
    Repository for ONLUS application data access operations.
    Handles CRUD operations and application-specific queries.
    """

    def __init__(self):
        super().__init__('onlus_applications')

    def create_indexes(self):
        """Create database indexes for optimal query performance."""
        if self.collection is None or os.getenv('TESTING') == 'true':
            return

        # Create indexes for common queries
        self.collection.create_index("applicant_id")
        self.collection.create_index("status")
        self.collection.create_index("phase")
        self.collection.create_index("category")
        self.collection.create_index("submission_date")
        self.collection.create_index("review_deadline")
        self.collection.create_index("assigned_reviewer")
        self.collection.create_index([("status", 1), ("submission_date", -1)])
        self.collection.create_index([("assigned_reviewer", 1), ("status", 1)])
        self.collection.create_index([("category", 1), ("status", 1)])
        self.collection.create_index("organization_name")
        self.collection.create_index("priority")

    def find_by_applicant_id(self, applicant_id: str) -> List[ONLUSApplication]:
        """
        Find applications by applicant ID.

        Args:
            applicant_id: Applicant user ID

        Returns:
            List[ONLUSApplication]: Applications for the applicant
        """
        data_list = self.find_many(
            {"applicant_id": applicant_id},
            sort=[("created_at", -1)]
        )
        return [ONLUSApplication.from_dict(data) for data in data_list]

    def find_by_organization_name(self, organization_name: str) -> Optional[ONLUSApplication]:
        """
        Find application by organization name.

        Args:
            organization_name: Organization name

        Returns:
            Optional[ONLUSApplication]: Application if found, None otherwise
        """
        data = self.find_one({
            "organization_name": {"$regex": f"^{organization_name}$", "$options": "i"}
        })
        return ONLUSApplication.from_dict(data) if data else None

    def create_application(self, application: ONLUSApplication) -> str:
        """
        Create a new application.

        Args:
            application: Application to create

        Returns:
            str: Created application ID
        """
        application_data = application.to_dict()
        application_data.pop('_id', None)  # Remove _id to let MongoDB generate it
        return self.create(application_data)

    def update_application(self, application_id: str, application: ONLUSApplication) -> bool:
        """
        Update application.

        Args:
            application_id: Application ID to update
            application: Updated application

        Returns:
            bool: True if updated successfully, False otherwise
        """
        application_data = application.to_dict()
        application_data.pop('_id', None)  # Remove _id from update data
        return self.update_by_id(application_id, application_data)

    def get_applications_by_status(self, status: str, limit: int = None) -> List[ONLUSApplication]:
        """
        Get applications by status.

        Args:
            status: Application status
            limit: Maximum number of applications to return

        Returns:
            List[ONLUSApplication]: Applications with specified status
        """
        data_list = self.find_many(
            {"status": status},
            sort=[("submission_date", -1)],
            limit=limit
        )
        return [ONLUSApplication.from_dict(data) for data in data_list]

    def get_applications_by_phase(self, phase: str, limit: int = None) -> List[ONLUSApplication]:
        """
        Get applications by review phase.

        Args:
            phase: Application phase
            limit: Maximum number of applications to return

        Returns:
            List[ONLUSApplication]: Applications in specified phase
        """
        data_list = self.find_many(
            {"phase": phase},
            sort=[("submission_date", -1)],
            limit=limit
        )
        return [ONLUSApplication.from_dict(data) for data in data_list]

    def get_pending_applications(self, reviewer_id: str = None) -> List[ONLUSApplication]:
        """
        Get applications pending review.

        Args:
            reviewer_id: Optional reviewer ID to filter by

        Returns:
            List[ONLUSApplication]: Pending applications
        """
        filter_criteria = {
            "status": {"$in": [
                ApplicationStatus.SUBMITTED.value,
                ApplicationStatus.UNDER_REVIEW.value,
                ApplicationStatus.DOCUMENTATION_PENDING.value,
                ApplicationStatus.DUE_DILIGENCE.value
            ]}
        }

        if reviewer_id:
            filter_criteria["assigned_reviewer"] = reviewer_id

        data_list = self.find_many(
            filter_criteria,
            sort=[("priority", -1), ("submission_date", 1)]  # Priority then oldest first
        )
        return [ONLUSApplication.from_dict(data) for data in data_list]

    def get_overdue_applications(self) -> List[ONLUSApplication]:
        """
        Get applications that are overdue for review.

        Returns:
            List[ONLUSApplication]: Overdue applications
        """
        current_time = datetime.now(timezone.utc)
        data_list = self.find_many({
            "review_deadline": {"$lt": current_time},
            "status": {"$in": [
                ApplicationStatus.SUBMITTED.value,
                ApplicationStatus.UNDER_REVIEW.value,
                ApplicationStatus.DOCUMENTATION_PENDING.value,
                ApplicationStatus.DUE_DILIGENCE.value
            ]}
        })
        return [ONLUSApplication.from_dict(data) for data in data_list]

    def get_applications_by_category(self, category: str,
                                   status: str = None) -> List[ONLUSApplication]:
        """
        Get applications by category.

        Args:
            category: ONLUS category
            status: Optional status filter

        Returns:
            List[ONLUSApplication]: Applications in category
        """
        filter_criteria = {"category": category}
        if status:
            filter_criteria["status"] = status

        data_list = self.find_many(
            filter_criteria,
            sort=[("submission_date", -1)]
        )
        return [ONLUSApplication.from_dict(data) for data in data_list]

    def get_applications_by_reviewer(self, reviewer_id: str,
                                   limit: int = None) -> List[ONLUSApplication]:
        """
        Get applications assigned to a reviewer.

        Args:
            reviewer_id: Reviewer ID
            limit: Maximum number of applications to return

        Returns:
            List[ONLUSApplication]: Applications assigned to reviewer
        """
        data_list = self.find_many(
            {"assigned_reviewer": reviewer_id},
            sort=[("submission_date", -1)],
            limit=limit
        )
        return [ONLUSApplication.from_dict(data) for data in data_list]

    def update_application_status(self, application_id: str, status: str,
                                 reviewer_id: str = None, notes: str = None) -> bool:
        """
        Update application status.

        Args:
            application_id: Application ID
            status: New status
            reviewer_id: Reviewer ID
            notes: Reviewer notes

        Returns:
            bool: True if updated successfully, False otherwise
        """
        update_data = {
            "status": status,
            "updated_at": self._get_current_time()
        }

        if reviewer_id:
            update_data["assigned_reviewer"] = reviewer_id
        if notes:
            update_data["reviewer_notes"] = notes

        return self.update_by_id(application_id, update_data)

    def search_applications(self, query: str, status: str = None) -> List[ONLUSApplication]:
        """
        Search applications by organization name or description.

        Args:
            query: Search query
            status: Optional status filter

        Returns:
            List[ONLUSApplication]: Matching applications
        """
        if not query or len(query.strip()) < 2:
            return []

        search_filter = {
            "$or": [
                {"organization_name": {"$regex": query.strip(), "$options": "i"}},
                {"description": {"$regex": query.strip(), "$options": "i"}},
                {"mission_statement": {"$regex": query.strip(), "$options": "i"}}
            ]
        }

        if status:
            search_filter["status"] = status

        data_list = self.find_many(search_filter, sort=[("submission_date", -1)])
        return [ONLUSApplication.from_dict(data) for data in data_list]

    def get_application_stats(self) -> Dict[str, Any]:
        """
        Get application statistics.

        Returns:
            Dict[str, Any]: Application statistics
        """
        if not self.collection:
            return {}

        try:
            pipeline = [
                {
                    "$group": {
                        "_id": "$status",
                        "count": {"$sum": 1},
                        "avg_progress": {"$avg": "$progress_percentage"}
                    }
                }
            ]

            results = list(self.collection.aggregate(pipeline))
            stats = {
                "total_applications": 0,
                "by_status": {},
                "avg_progress_by_status": {}
            }

            for result in results:
                status = result["_id"]
                count = result["count"]
                avg_progress = result["avg_progress"]

                stats["total_applications"] += count
                stats["by_status"][status] = count
                stats["avg_progress_by_status"][status] = round(avg_progress, 2) if avg_progress else 0

            return stats

        except Exception:
            return {
                "total_applications": 0,
                "by_status": {},
                "avg_progress_by_status": {}
            }

    def get_category_stats(self) -> Dict[str, Any]:
        """
        Get statistics by category.

        Returns:
            Dict[str, Any]: Category statistics
        """
        if not self.collection:
            return {}

        try:
            pipeline = [
                {
                    "$group": {
                        "_id": "$category",
                        "total": {"$sum": 1},
                        "approved": {
                            "$sum": {"$cond": [{"$eq": ["$status", "approved"]}, 1, 0]}
                        },
                        "pending": {
                            "$sum": {"$cond": [{"$in": ["$status", ["submitted", "under_review", "documentation_pending", "due_diligence"]]}, 1, 0]}
                        },
                        "rejected": {
                            "$sum": {"$cond": [{"$eq": ["$status", "rejected"]}, 1, 0]}
                        }
                    }
                }
            ]

            results = list(self.collection.aggregate(pipeline))
            return {result["_id"]: result for result in results}

        except Exception:
            return {}

    def get_reviewer_workload(self) -> Dict[str, Any]:
        """
        Get reviewer workload statistics.

        Returns:
            Dict[str, Any]: Reviewer workload data
        """
        if not self.collection:
            return {}

        try:
            pipeline = [
                {
                    "$match": {
                        "assigned_reviewer": {"$exists": True, "$ne": None},
                        "status": {"$in": [
                            "under_review", "documentation_pending", "due_diligence"
                        ]}
                    }
                },
                {
                    "$group": {
                        "_id": "$assigned_reviewer",
                        "active_applications": {"$sum": 1},
                        "avg_progress": {"$avg": "$progress_percentage"},
                        "overdue_count": {
                            "$sum": {
                                "$cond": [
                                    {"$lt": ["$review_deadline", datetime.now(timezone.utc)]},
                                    1,
                                    0
                                ]
                            }
                        }
                    }
                }
            ]

            results = list(self.collection.aggregate(pipeline))
            return {result["_id"]: result for result in results}

        except Exception:
            return {}

    def mark_applications_as_expired(self) -> int:
        """
        Mark expired applications as expired.

        Returns:
            int: Number of applications marked as expired
        """
        current_time = datetime.now(timezone.utc)
        expiry_threshold = current_time - timedelta(days=ONLUSApplication.EXPIRATION_DAYS)

        try:
            result = self.collection.update_many(
                {
                    "submission_date": {"$lt": expiry_threshold},
                    "status": {"$in": [
                        ApplicationStatus.SUBMITTED.value,
                        ApplicationStatus.UNDER_REVIEW.value,
                        ApplicationStatus.DOCUMENTATION_PENDING.value
                    ]}
                },
                {
                    "$set": {
                        "status": ApplicationStatus.EXPIRED.value,
                        "updated_at": current_time
                    }
                }
            )
            return result.modified_count
        except Exception:
            return 0

    def get_applications_by_priority(self, priority: str,
                                   limit: int = None) -> List[ONLUSApplication]:
        """
        Get applications by priority level.

        Args:
            priority: Priority level
            limit: Maximum number of applications to return

        Returns:
            List[ONLUSApplication]: Applications with specified priority
        """
        data_list = self.find_many(
            {"priority": priority},
            sort=[("submission_date", 1)],  # Oldest first for high priority
            limit=limit
        )
        return [ONLUSApplication.from_dict(data) for data in data_list]

    def get_completed_applications_by_date_range(self, start_date: datetime,
                                               end_date: datetime) -> List[ONLUSApplication]:
        """
        Get completed applications within date range.

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            List[ONLUSApplication]: Completed applications in date range
        """
        data_list = self.find_many({
            "status": {"$in": [ApplicationStatus.APPROVED.value, ApplicationStatus.REJECTED.value]},
            "updated_at": {"$gte": start_date, "$lte": end_date}
        })
        return [ONLUSApplication.from_dict(data) for data in data_list]

    def update_progress_percentage(self, application_id: str, percentage: int) -> bool:
        """
        Update application progress percentage.

        Args:
            application_id: Application ID
            percentage: Progress percentage (0-100)

        Returns:
            bool: True if updated successfully, False otherwise
        """
        if 0 <= percentage <= 100:
            return self.update_by_id(application_id, {
                "progress_percentage": percentage,
                "updated_at": self._get_current_time()
            })
        return False