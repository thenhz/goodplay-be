from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
from bson import ObjectId
from app.core.repositories.base_repository import BaseRepository
from app.onlus.models.verification_check import VerificationCheck, CheckStatus, RiskLevel
import os


class VerificationCheckRepository(BaseRepository):
    """
    Repository for verification check data access operations.
    Handles CRUD operations and verification-specific queries.
    """

    def __init__(self):
        super().__init__('verification_checks')

    def create_indexes(self):
        """Create database indexes for optimal query performance."""
        if self.collection is None or os.getenv('TESTING') == 'true':
            return

        # Create indexes for common queries
        self.collection.create_index("application_id")
        self.collection.create_index([("application_id", 1), ("check_type", 1)])
        self.collection.create_index("status")
        self.collection.create_index("risk_level")
        self.collection.create_index("check_date")
        self.collection.create_index("completion_date")
        self.collection.create_index("expiration_date")
        self.collection.create_index("performed_by")
        self.collection.create_index([("status", 1), ("check_date", -1)])
        self.collection.create_index([("risk_level", 1), ("completion_date", -1)])

    def find_by_application_id(self, application_id: str) -> List[VerificationCheck]:
        """
        Find all verification checks for an application.

        Args:
            application_id: Application ID

        Returns:
            List[VerificationCheck]: List of checks for the application
        """
        data_list = self.find_many(
            {"application_id": application_id},
            sort=[("check_date", -1)]
        )
        return [VerificationCheck.from_dict(data) for data in data_list]

    def find_by_application_and_type(self, application_id: str,
                                   check_type: str) -> Optional[VerificationCheck]:
        """
        Find verification check by application and type.

        Args:
            application_id: Application ID
            check_type: Check type

        Returns:
            Optional[VerificationCheck]: Check if found, None otherwise
        """
        data = self.find_one({
            "application_id": application_id,
            "check_type": check_type
        })
        return VerificationCheck.from_dict(data) if data else None

    def create_check(self, check: VerificationCheck) -> str:
        """
        Create a new verification check.

        Args:
            check: Verification check to create

        Returns:
            str: Created check ID
        """
        check_data = check.to_dict()
        check_data.pop('_id', None)  # Remove _id to let MongoDB generate it
        return self.create(check_data)

    def update_check(self, check_id: str, check: VerificationCheck) -> bool:
        """
        Update verification check.

        Args:
            check_id: Check ID to update
            check: Updated check

        Returns:
            bool: True if updated successfully, False otherwise
        """
        check_data = check.to_dict()
        check_data.pop('_id', None)  # Remove _id from update data
        return self.update_by_id(check_id, check_data)

    def get_checks_by_status(self, status: str, limit: int = None) -> List[VerificationCheck]:
        """
        Get verification checks by status.

        Args:
            status: Check status
            limit: Maximum number of checks to return

        Returns:
            List[VerificationCheck]: Checks with specified status
        """
        data_list = self.find_many(
            {"status": status},
            sort=[("check_date", -1)],
            limit=limit
        )
        return [VerificationCheck.from_dict(data) for data in data_list]

    def get_pending_checks(self, performer_id: str = None) -> List[VerificationCheck]:
        """
        Get pending verification checks.

        Args:
            performer_id: Optional performer ID to filter by

        Returns:
            List[VerificationCheck]: Pending checks
        """
        filter_criteria = {"status": CheckStatus.PENDING.value}
        if performer_id:
            filter_criteria["performed_by"] = performer_id

        data_list = self.find_many(
            filter_criteria,
            sort=[("check_date", 1)]  # Oldest first
        )
        return [VerificationCheck.from_dict(data) for data in data_list]

    def get_checks_by_risk_level(self, risk_level: str,
                                limit: int = None) -> List[VerificationCheck]:
        """
        Get checks by risk level.

        Args:
            risk_level: Risk level
            limit: Maximum number of checks to return

        Returns:
            List[VerificationCheck]: Checks with specified risk level
        """
        data_list = self.find_many(
            {"risk_level": risk_level},
            sort=[("completion_date", -1)],
            limit=limit
        )
        return [VerificationCheck.from_dict(data) for data in data_list]

    def get_expired_checks(self) -> List[VerificationCheck]:
        """
        Get verification checks that have expired.

        Returns:
            List[VerificationCheck]: Expired checks
        """
        current_time = datetime.now(timezone.utc)
        data_list = self.find_many({
            "expiration_date": {"$lt": current_time},
            "status": {"$ne": CheckStatus.EXPIRED.value}
        })
        return [VerificationCheck.from_dict(data) for data in data_list]

    def get_checks_requiring_follow_up(self) -> List[VerificationCheck]:
        """
        Get checks that require follow-up.

        Returns:
            List[VerificationCheck]: Checks requiring follow-up
        """
        data_list = self.find_many(
            {"follow_up_required": True},
            sort=[("completion_date", 1)]
        )
        return [VerificationCheck.from_dict(data) for data in data_list]

    def update_check_status(self, check_id: str, status: str,
                           completion_date: datetime = None,
                           result_summary: str = None) -> bool:
        """
        Update check status.

        Args:
            check_id: Check ID
            status: New status
            completion_date: Completion date
            result_summary: Result summary

        Returns:
            bool: True if updated successfully, False otherwise
        """
        update_data = {
            "status": status,
            "updated_at": self._get_current_time()
        }

        if completion_date:
            update_data["completion_date"] = completion_date
        if result_summary:
            update_data["result_summary"] = result_summary

        return self.update_by_id(check_id, update_data)

    def get_checks_by_performer(self, performer_id: str,
                               limit: int = None) -> List[VerificationCheck]:
        """
        Get checks performed by specific performer.

        Args:
            performer_id: Performer ID
            limit: Maximum number of checks to return

        Returns:
            List[VerificationCheck]: Checks performed by performer
        """
        data_list = self.find_many(
            {"performed_by": performer_id},
            sort=[("check_date", -1)],
            limit=limit
        )
        return [VerificationCheck.from_dict(data) for data in data_list]

    def get_application_check_stats(self, application_id: str) -> Dict[str, Any]:
        """
        Get verification check statistics for an application.

        Args:
            application_id: Application ID

        Returns:
            Dict[str, Any]: Check statistics
        """
        if not self.collection:
            return {}

        try:
            pipeline = [
                {"$match": {"application_id": application_id}},
                {
                    "$group": {
                        "_id": None,
                        "total_checks": {"$sum": 1},
                        "completed_checks": {
                            "$sum": {"$cond": [{"$eq": ["$status", "completed"]}, 1, 0]}
                        },
                        "failed_checks": {
                            "$sum": {"$cond": [{"$eq": ["$status", "failed"]}, 1, 0]}
                        },
                        "pending_checks": {
                            "$sum": {"$cond": [{"$eq": ["$status", "pending"]}, 1, 0]}
                        },
                        "high_risk_checks": {
                            "$sum": {"$cond": [{"$in": ["$risk_level", ["high", "critical"]]}, 1, 0]}
                        },
                        "avg_score": {"$avg": "$score"},
                        "checks_by_status": {
                            "$push": {
                                "status": "$status",
                                "risk_level": "$risk_level",
                                "check_type": "$check_type"
                            }
                        }
                    }
                }
            ]

            result = list(self.collection.aggregate(pipeline))
            if result:
                stats = result[0]
                stats.pop('_id', None)
                return stats
            else:
                return {
                    "total_checks": 0,
                    "completed_checks": 0,
                    "failed_checks": 0,
                    "pending_checks": 0,
                    "high_risk_checks": 0,
                    "avg_score": None,
                    "checks_by_status": []
                }

        except Exception:
            return {
                "total_checks": 0,
                "completed_checks": 0,
                "failed_checks": 0,
                "pending_checks": 0,
                "high_risk_checks": 0,
                "avg_score": None,
                "checks_by_status": []
            }

    def get_overall_risk_assessment(self, application_id: str) -> Dict[str, Any]:
        """
        Get overall risk assessment for an application.

        Args:
            application_id: Application ID

        Returns:
            Dict[str, Any]: Risk assessment
        """
        checks = self.find_by_application_id(application_id)

        if not checks:
            return {
                "overall_risk": RiskLevel.UNKNOWN.value,
                "risk_score": 0,
                "high_risk_areas": [],
                "recommendations": []
            }

        risk_scores = []
        high_risk_areas = []
        all_recommendations = []

        for check in checks:
            if check.status == CheckStatus.COMPLETED.value:
                risk_scores.append(check.get_risk_score())

                if check.risk_level in [RiskLevel.HIGH.value, RiskLevel.CRITICAL.value]:
                    high_risk_areas.append({
                        "check_type": check.check_type,
                        "risk_level": check.risk_level,
                        "findings": len(check.findings)
                    })

                all_recommendations.extend(check.recommendations)

        # Calculate overall risk
        if not risk_scores:
            overall_risk = RiskLevel.UNKNOWN.value
            risk_score = 0
        else:
            avg_risk_score = sum(risk_scores) / len(risk_scores)
            if avg_risk_score >= 3.5:
                overall_risk = RiskLevel.CRITICAL.value
            elif avg_risk_score >= 2.5:
                overall_risk = RiskLevel.HIGH.value
            elif avg_risk_score >= 1.5:
                overall_risk = RiskLevel.MEDIUM.value
            else:
                overall_risk = RiskLevel.LOW.value

            risk_score = int(avg_risk_score * 25)  # Convert to 0-100 scale

        return {
            "overall_risk": overall_risk,
            "risk_score": risk_score,
            "high_risk_areas": high_risk_areas,
            "recommendations": list(set(all_recommendations))  # Remove duplicates
        }

    def mark_checks_as_expired(self) -> int:
        """
        Mark expired checks as expired.

        Returns:
            int: Number of checks marked as expired
        """
        current_time = datetime.now(timezone.utc)

        try:
            result = self.collection.update_many(
                {
                    "expiration_date": {"$lt": current_time},
                    "status": {"$ne": CheckStatus.EXPIRED.value}
                },
                {
                    "$set": {
                        "status": CheckStatus.EXPIRED.value,
                        "updated_at": current_time
                    }
                }
            )
            return result.modified_count
        except Exception:
            return 0

    def get_automated_checks_summary(self) -> Dict[str, Any]:
        """
        Get summary of automated checks.

        Returns:
            Dict[str, Any]: Automated checks summary
        """
        if not self.collection:
            return {}

        try:
            pipeline = [
                {"$match": {"automated": True}},
                {
                    "$group": {
                        "_id": "$check_type",
                        "total": {"$sum": 1},
                        "completed": {
                            "$sum": {"$cond": [{"$eq": ["$status", "completed"]}, 1, 0]}
                        },
                        "failed": {
                            "$sum": {"$cond": [{"$eq": ["$status", "failed"]}, 1, 0]}
                        },
                        "avg_completion_time": {
                            "$avg": {
                                "$subtract": ["$completion_date", "$check_date"]
                            }
                        }
                    }
                }
            ]

            results = list(self.collection.aggregate(pipeline))
            return {result["_id"]: result for result in results}

        except Exception:
            return {}