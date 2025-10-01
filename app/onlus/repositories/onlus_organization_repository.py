from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
from bson import ObjectId
from app.core.repositories.base_repository import BaseRepository
from app.onlus.models.onlus_organization import ONLUSOrganization, OrganizationStatus, ComplianceStatus
import os


class ONLUSOrganizationRepository(BaseRepository):
    """
    Repository for ONLUS organization data access operations.
    Handles CRUD operations and organization-specific queries.
    """

    def __init__(self):
        super().__init__('onlus_organizations')

    def create_indexes(self):
        """Create database indexes for optimal query performance."""
        if self.collection is None or os.getenv('TESTING') == 'true':
            return

        # Create indexes for common queries
        self.collection.create_index("application_id", unique=True)
        self.collection.create_index("organization_name")
        self.collection.create_index("legal_name")
        self.collection.create_index("category")
        self.collection.create_index("status")
        self.collection.create_index("compliance_status")
        self.collection.create_index("verification_level")
        self.collection.create_index("verification_date")
        self.collection.create_index("featured_until")
        self.collection.create_index([("status", 1), ("category", 1)])
        self.collection.create_index([("compliance_score", -1), ("status", 1)])
        self.collection.create_index([("total_donations_received", -1), ("status", 1)])
        self.collection.create_index([("donor_rating", -1), ("status", 1)])
        self.collection.create_index("tags")
        self.collection.create_index([("organization_name", "text"), ("description", "text")])

    def find_by_application_id(self, application_id: str) -> Optional[ONLUSOrganization]:
        """
        Find organization by application ID.

        Args:
            application_id: Application ID

        Returns:
            Optional[ONLUSOrganization]: Organization if found, None otherwise
        """
        data = self.find_one({"application_id": application_id})
        return ONLUSOrganization.from_dict(data) if data else None

    def find_by_organization_name(self, organization_name: str) -> Optional[ONLUSOrganization]:
        """
        Find organization by name.

        Args:
            organization_name: Organization name

        Returns:
            Optional[ONLUSOrganization]: Organization if found, None otherwise
        """
        data = self.find_one({
            "organization_name": {"$regex": f"^{organization_name}$", "$options": "i"}
        })
        return ONLUSOrganization.from_dict(data) if data else None

    def create_organization(self, organization: ONLUSOrganization) -> str:
        """
        Create a new organization.

        Args:
            organization: Organization to create

        Returns:
            str: Created organization ID
        """
        organization_data = organization.to_dict(include_sensitive=True)
        organization_data.pop('_id', None)  # Remove _id to let MongoDB generate it
        return self.create(organization_data)

    def update_organization(self, organization_id: str, organization: ONLUSOrganization) -> bool:
        """
        Update organization.

        Args:
            organization_id: Organization ID to update
            organization: Updated organization

        Returns:
            bool: True if updated successfully, False otherwise
        """
        organization_data = organization.to_dict(include_sensitive=True)
        organization_data.pop('_id', None)  # Remove _id from update data
        return self.update_by_id(organization_id, organization_data)

    def get_active_organizations(self, limit: int = None) -> List[ONLUSOrganization]:
        """
        Get active organizations.

        Args:
            limit: Maximum number of organizations to return

        Returns:
            List[ONLUSOrganization]: Active organizations
        """
        data_list = self.find_many(
            {"status": OrganizationStatus.ACTIVE.value},
            sort=[("verification_date", -1)],
            limit=limit
        )
        return [ONLUSOrganization.from_dict(data) for data in data_list]

    def get_organizations_by_category(self, category: str,
                                    status: str = None) -> List[ONLUSOrganization]:
        """
        Get organizations by category.

        Args:
            category: ONLUS category
            status: Optional status filter

        Returns:
            List[ONLUSOrganization]: Organizations in category
        """
        filter_criteria = {"category": category}
        if status:
            filter_criteria["status"] = status
        else:
            filter_criteria["status"] = OrganizationStatus.ACTIVE.value

        data_list = self.find_many(
            filter_criteria,
            sort=[("donor_rating", -1), ("total_donations_received", -1)]
        )
        return [ONLUSOrganization.from_dict(data) for data in data_list]

    def get_featured_organizations(self) -> List[ONLUSOrganization]:
        """
        Get currently featured organizations.

        Returns:
            List[ONLUSOrganization]: Featured organizations
        """
        current_time = datetime.now(timezone.utc)
        data_list = self.find_many({
            "featured_until": {"$gt": current_time},
            "status": OrganizationStatus.ACTIVE.value
        })
        return [ONLUSOrganization.from_dict(data) for data in data_list]

    def get_top_rated_organizations(self, limit: int = 10) -> List[ONLUSOrganization]:
        """
        Get top-rated organizations.

        Args:
            limit: Maximum number of organizations to return

        Returns:
            List[ONLUSOrganization]: Top-rated organizations
        """
        data_list = self.find_many(
            {
                "status": OrganizationStatus.ACTIVE.value,
                "donor_rating": {"$gte": 4.0}
            },
            sort=[("donor_rating", -1), ("total_donors", -1)],
            limit=limit
        )
        return [ONLUSOrganization.from_dict(data) for data in data_list]

    def get_organizations_by_donation_volume(self, limit: int = 10) -> List[ONLUSOrganization]:
        """
        Get organizations by donation volume.

        Args:
            limit: Maximum number of organizations to return

        Returns:
            List[ONLUSOrganization]: Organizations sorted by donation volume
        """
        data_list = self.find_many(
            {"status": OrganizationStatus.ACTIVE.value},
            sort=[("total_donations_received", -1)],
            limit=limit
        )
        return [ONLUSOrganization.from_dict(data) for data in data_list]

    def search_organizations(self, query: str, category: str = None) -> List[ONLUSOrganization]:
        """
        Search organizations by name, description, or tags.

        Args:
            query: Search query
            category: Optional category filter

        Returns:
            List[ONLUSOrganization]: Matching organizations
        """
        if not query or len(query.strip()) < 2:
            return []

        search_filter = {
            "$and": [
                {"status": OrganizationStatus.ACTIVE.value},
                {
                    "$or": [
                        {"organization_name": {"$regex": query.strip(), "$options": "i"}},
                        {"description": {"$regex": query.strip(), "$options": "i"}},
                        {"mission_statement": {"$regex": query.strip(), "$options": "i"}},
                        {"tags": {"$in": [query.strip()]}}
                    ]
                }
            ]
        }

        if category:
            search_filter["$and"].append({"category": category})

        data_list = self.find_many(search_filter, sort=[("donor_rating", -1)])
        return [ONLUSOrganization.from_dict(data) for data in data_list]

    def get_organizations_needing_review(self) -> List[ONLUSOrganization]:
        """
        Get organizations that need compliance review.

        Returns:
            List[ONLUSOrganization]: Organizations needing review
        """
        current_time = datetime.now(timezone.utc)
        data_list = self.find_many({
            "$or": [
                {"next_review_date": {"$lte": current_time}},
                {"next_review_date": {"$exists": False}},
                {"compliance_status": ComplianceStatus.UNDER_INVESTIGATION.value}
            ],
            "status": {"$ne": OrganizationStatus.DEACTIVATED.value}
        })
        return [ONLUSOrganization.from_dict(data) for data in data_list]

    def update_donation_stats(self, organization_id: str, amount: float,
                             is_new_donor: bool = False) -> bool:
        """
        Update donation statistics for an organization.

        Args:
            organization_id: Organization ID
            amount: Donation amount
            is_new_donor: Whether this is a new donor

        Returns:
            bool: True if updated successfully, False otherwise
        """
        update_data = {
            "$inc": {"total_donations_received": amount},
            "last_donation_date": self._get_current_time(),
            "updated_at": self._get_current_time()
        }

        if is_new_donor:
            update_data["$inc"]["total_donors"] = 1

        try:
            result = self.collection.update_one(
                {"_id": self._get_object_id(organization_id)},
                update_data
            )
            return result.modified_count > 0
        except Exception:
            return False

    def update_compliance_status(self, organization_id: str, status: str,
                                score: float = None) -> bool:
        """
        Update compliance status and score.

        Args:
            organization_id: Organization ID
            status: New compliance status
            score: Optional compliance score

        Returns:
            bool: True if updated successfully, False otherwise
        """
        update_data = {
            "compliance_status": status,
            "last_compliance_review": self._get_current_time(),
            "next_review_date": self._get_current_time() + timedelta(days=365),
            "updated_at": self._get_current_time()
        }

        if score is not None:
            update_data["compliance_score"] = score

        return self.update_by_id(organization_id, update_data)

    def get_organization_stats(self) -> Dict[str, Any]:
        """
        Get organization statistics.

        Returns:
            Dict[str, Any]: Organization statistics
        """
        if not self.collection:
            return {}

        try:
            pipeline = [
                {
                    "$group": {
                        "_id": "$status",
                        "count": {"$sum": 1},
                        "total_donations": {"$sum": "$total_donations_received"},
                        "total_donors": {"$sum": "$total_donors"},
                        "avg_rating": {"$avg": "$donor_rating"}
                    }
                }
            ]

            results = list(self.collection.aggregate(pipeline))
            stats = {
                "total_organizations": 0,
                "total_donations": 0,
                "total_donors": 0,
                "by_status": {}
            }

            for result in results:
                status = result["_id"]
                count = result["count"]
                donations = result["total_donations"]
                donors = result["total_donors"]
                rating = result["avg_rating"]

                stats["total_organizations"] += count
                stats["total_donations"] += donations or 0
                stats["total_donors"] += donors or 0

                stats["by_status"][status] = {
                    "count": count,
                    "total_donations": donations or 0,
                    "total_donors": donors or 0,
                    "avg_rating": round(rating, 2) if rating else 0
                }

            return stats

        except Exception:
            return {
                "total_organizations": 0,
                "total_donations": 0,
                "total_donors": 0,
                "by_status": {}
            }

    def get_category_distribution(self) -> Dict[str, int]:
        """
        Get distribution of organizations by category.

        Returns:
            Dict[str, int]: Category distribution
        """
        if not self.collection:
            return {}

        try:
            pipeline = [
                {"$match": {"status": OrganizationStatus.ACTIVE.value}},
                {"$group": {"_id": "$category", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]

            results = list(self.collection.aggregate(pipeline))
            return {result["_id"]: result["count"] for result in results}

        except Exception:
            return {}

    def get_compliance_summary(self) -> Dict[str, Any]:
        """
        Get compliance status summary.

        Returns:
            Dict[str, Any]: Compliance summary
        """
        if not self.collection:
            return {}

        try:
            pipeline = [
                {
                    "$group": {
                        "_id": "$compliance_status",
                        "count": {"$sum": 1},
                        "avg_score": {"$avg": "$compliance_score"}
                    }
                }
            ]

            results = list(self.collection.aggregate(pipeline))
            summary = {"total": 0, "by_status": {}}

            for result in results:
                status = result["_id"]
                count = result["count"]
                avg_score = result["avg_score"]

                summary["total"] += count
                summary["by_status"][status] = {
                    "count": count,
                    "avg_score": round(avg_score, 2) if avg_score else 0
                }

            return summary

        except Exception:
            return {"total": 0, "by_status": {}}

    def get_organizations_by_tag(self, tag: str) -> List[ONLUSOrganization]:
        """
        Get organizations by tag.

        Args:
            tag: Tag to search for

        Returns:
            List[ONLUSOrganization]: Organizations with the tag
        """
        data_list = self.find_many({
            "tags": tag,
            "status": OrganizationStatus.ACTIVE.value
        })
        return [ONLUSOrganization.from_dict(data) for data in data_list]

    def get_recent_organizations(self, days: int = 30,
                               limit: int = 10) -> List[ONLUSOrganization]:
        """
        Get recently verified organizations.

        Args:
            days: Number of days to look back
            limit: Maximum number of organizations to return

        Returns:
            List[ONLUSOrganization]: Recently verified organizations
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        data_list = self.find_many(
            {
                "verification_date": {"$gte": cutoff_date},
                "status": OrganizationStatus.ACTIVE.value
            },
            sort=[("verification_date", -1)],
            limit=limit
        )
        return [ONLUSOrganization.from_dict(data) for data in data_list]

    def update_featured_status(self, organization_id: str,
                             duration_days: int = 30) -> bool:
        """
        Set organization as featured.

        Args:
            organization_id: Organization ID
            duration_days: Duration in days

        Returns:
            bool: True if updated successfully, False otherwise
        """
        featured_until = datetime.now(timezone.utc) + timedelta(days=duration_days)
        return self.update_by_id(organization_id, {
            "featured_until": featured_until,
            "updated_at": self._get_current_time()
        })

    def remove_featured_status(self, organization_id: str) -> bool:
        """
        Remove featured status from organization.

        Args:
            organization_id: Organization ID

        Returns:
            bool: True if updated successfully, False otherwise
        """
        return self.update_by_id(organization_id, {
            "featured_until": None,
            "updated_at": self._get_current_time()
        })