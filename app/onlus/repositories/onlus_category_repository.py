from typing import Optional, List, Dict, Any
from bson import ObjectId
from app.core.repositories.base_repository import BaseRepository
from app.onlus.models.onlus_category import ONLUSCategoryInfo
import os


class ONLUSCategoryRepository(BaseRepository):
    """
    Repository for ONLUS category data access operations.
    Handles CRUD operations and category-specific queries.
    """

    def __init__(self):
        super().__init__('onlus_categories')

    def create_indexes(self):
        """Create database indexes for optimal query performance."""
        if self.collection is None or os.getenv('TESTING') == 'true':
            return

        # Create indexes for common queries
        self.collection.create_index("category", unique=True)
        self.collection.create_index("is_active")
        self.collection.create_index([("priority", -1), ("name", 1)])
        self.collection.create_index("created_at")

    def find_by_category(self, category: str) -> Optional[ONLUSCategoryInfo]:
        """
        Find category info by category enum value.

        Args:
            category: Category enum value

        Returns:
            Optional[ONLUSCategoryInfo]: Category info if found, None otherwise
        """
        data = self.find_one({"category": category})
        return ONLUSCategoryInfo.from_dict(data) if data else None

    def create_category(self, category_info: ONLUSCategoryInfo) -> str:
        """
        Create a new category info.

        Args:
            category_info: Category info to create

        Returns:
            str: Created category ID
        """
        category_data = category_info.to_dict()
        category_data.pop('_id', None)  # Remove _id to let MongoDB generate it
        return self.create(category_data)

    def update_category(self, category_id: str, category_info: ONLUSCategoryInfo) -> bool:
        """
        Update category info.

        Args:
            category_id: Category ID to update
            category_info: Updated category info

        Returns:
            bool: True if updated successfully, False otherwise
        """
        category_data = category_info.to_dict()
        category_data.pop('_id', None)  # Remove _id from update data
        return self.update_by_id(category_id, category_data)

    def get_active_categories(self, sort_by_priority: bool = True) -> List[ONLUSCategoryInfo]:
        """
        Get all active categories.

        Args:
            sort_by_priority: Whether to sort by priority

        Returns:
            List[ONLUSCategoryInfo]: List of active categories
        """
        sort_criteria = [("priority", -1), ("name", 1)] if sort_by_priority else None
        data_list = self.find_many(
            {"is_active": True},
            sort=sort_criteria
        )
        return [ONLUSCategoryInfo.from_dict(data) for data in data_list]

    def get_categories_with_requirements(self) -> List[ONLUSCategoryInfo]:
        """
        Get categories that have specific verification requirements.

        Returns:
            List[ONLUSCategoryInfo]: Categories with requirements
        """
        data_list = self.find_many({
            "is_active": True,
            "verification_requirements": {"$exists": True, "$ne": []}
        })
        return [ONLUSCategoryInfo.from_dict(data) for data in data_list]

    def search_categories(self, query: str) -> List[ONLUSCategoryInfo]:
        """
        Search categories by name or description.

        Args:
            query: Search query

        Returns:
            List[ONLUSCategoryInfo]: Matching categories
        """
        if not query or len(query.strip()) < 2:
            return []

        search_filter = {
            "$and": [
                {"is_active": True},
                {
                    "$or": [
                        {"name": {"$regex": query.strip(), "$options": "i"}},
                        {"description": {"$regex": query.strip(), "$options": "i"}},
                        {"category": {"$regex": query.strip(), "$options": "i"}}
                    ]
                }
            ]
        }

        data_list = self.find_many(search_filter, sort=[("priority", -1)])
        return [ONLUSCategoryInfo.from_dict(data) for data in data_list]

    def get_category_stats(self) -> Dict[str, Any]:
        """
        Get category statistics.

        Returns:
            Dict[str, Any]: Category statistics
        """
        if not self.collection:
            return {}

        try:
            pipeline = [
                {
                    "$group": {
                        "_id": None,
                        "total_categories": {"$sum": 1},
                        "active_categories": {
                            "$sum": {"$cond": ["$is_active", 1, 0]}
                        },
                        "categories_with_requirements": {
                            "$sum": {
                                "$cond": [
                                    {"$gt": [{"$size": "$verification_requirements"}, 0]},
                                    1,
                                    0
                                ]
                            }
                        }
                    }
                }
            ]

            result = list(self.collection.aggregate(pipeline))
            return result[0] if result else {
                "total_categories": 0,
                "active_categories": 0,
                "categories_with_requirements": 0
            }

        except Exception:
            return {
                "total_categories": 0,
                "active_categories": 0,
                "categories_with_requirements": 0
            }

    def update_verification_requirements(self, category: str,
                                       requirements: List[str]) -> bool:
        """
        Update verification requirements for a category.

        Args:
            category: Category enum value
            requirements: List of verification requirements

        Returns:
            bool: True if updated successfully, False otherwise
        """
        return self.update_one(
            {"category": category},
            {
                "verification_requirements": requirements,
                "updated_at": self._get_current_time()
            }
        )

    def update_compliance_standards(self, category: str,
                                   standards: List[str]) -> bool:
        """
        Update compliance standards for a category.

        Args:
            category: Category enum value
            standards: List of compliance standards

        Returns:
            bool: True if updated successfully, False otherwise
        """
        return self.update_one(
            {"category": category},
            {
                "compliance_standards": standards,
                "updated_at": self._get_current_time()
            }
        )

    def activate_category(self, category_id: str) -> bool:
        """
        Activate a category.

        Args:
            category_id: Category ID to activate

        Returns:
            bool: True if activated successfully, False otherwise
        """
        return self.update_by_id(category_id, {
            "is_active": True,
            "updated_at": self._get_current_time()
        })

    def deactivate_category(self, category_id: str) -> bool:
        """
        Deactivate a category.

        Args:
            category_id: Category ID to deactivate

        Returns:
            bool: True if deactivated successfully, False otherwise
        """
        return self.update_by_id(category_id, {
            "is_active": False,
            "updated_at": self._get_current_time()
        })

    def get_categories_by_priority(self, limit: int = None) -> List[ONLUSCategoryInfo]:
        """
        Get categories ordered by priority.

        Args:
            limit: Maximum number of categories to return

        Returns:
            List[ONLUSCategoryInfo]: Categories ordered by priority
        """
        data_list = self.find_many(
            {"is_active": True},
            sort=[("priority", -1), ("name", 1)],
            limit=limit
        )
        return [ONLUSCategoryInfo.from_dict(data) for data in data_list]