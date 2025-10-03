from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from bson import ObjectId
from app.core.repositories.base_repository import BaseRepository
from app.donations.models.conversion_rate import ConversionRate
import os


class ConversionRateRepository(BaseRepository):
    """
    Repository for conversion rate data access operations.
    Handles CRUD operations and rate-specific queries.
    """

    def __init__(self):
        super().__init__('conversion_rates')

    def create_indexes(self):
        """Create database indexes for optimal query performance."""
        if self.collection is None or os.getenv('TESTING') == 'true':
            return

        # Create indexes for common queries
        self.collection.create_index("rate_id", unique=True)
        self.collection.create_index("is_active")
        self.collection.create_index("valid_from")
        self.collection.create_index("valid_until")
        self.collection.create_index("created_at")

        # Compound indexes for complex queries
        self.collection.create_index([("is_active", 1), ("valid_from", 1), ("valid_until", 1)])
        self.collection.create_index([("is_active", 1), ("created_at", -1)])

    def find_by_rate_id(self, rate_id: str) -> Optional[ConversionRate]:
        """
        Find conversion rate by rate ID.

        Args:
            rate_id: Rate identifier

        Returns:
            Optional[ConversionRate]: ConversionRate instance if found, None otherwise
        """
        data = self.find_one({"rate_id": rate_id})
        return ConversionRate.from_dict(data) if data else None

    def get_current_rate(self, check_time: datetime = None) -> Optional[ConversionRate]:
        """
        Get the currently active conversion rate.

        Args:
            check_time: Time to check validity (defaults to now)

        Returns:
            Optional[ConversionRate]: Current active rate or None
        """
        check_time = check_time or datetime.now(timezone.utc)

        # Find active rate that is valid at the given time
        filter_criteria = {
            "is_active": True,
            "$or": [
                {"valid_from": {"$lte": check_time}, "valid_until": {"$gte": check_time}},
                {"valid_from": {"$lte": check_time}, "valid_until": None}
            ]
        }

        data = self.find_one(filter_criteria)
        return ConversionRate.from_dict(data) if data else None

    def get_default_rate(self) -> Optional[ConversionRate]:
        """
        Get the default conversion rate.

        Returns:
            Optional[ConversionRate]: Default rate or None
        """
        return self.find_by_rate_id("default")

    def create_rate(self, conversion_rate: ConversionRate) -> str:
        """
        Create a new conversion rate.

        Args:
            conversion_rate: ConversionRate instance to create

        Returns:
            str: Created rate ID
        """
        rate_data = conversion_rate.to_dict()
        if '_id' in rate_data and rate_data['_id'] is None:
            del rate_data['_id']

        rate_id = self.create(rate_data)
        conversion_rate._id = ObjectId(rate_id)
        return rate_id

    def update_rate(self, conversion_rate: ConversionRate) -> bool:
        """
        Update an existing conversion rate.

        Args:
            conversion_rate: ConversionRate instance to update

        Returns:
            bool: True if update was successful
        """
        if not conversion_rate._id:
            return False

        rate_data = conversion_rate.to_dict()
        del rate_data['_id']  # Remove _id from update data

        return self.update_by_id(str(conversion_rate._id), rate_data)

    def activate_rate(self, rate_id: str) -> bool:
        """
        Activate a conversion rate and deactivate all others.

        Args:
            rate_id: Rate ID to activate

        Returns:
            bool: True if activation was successful
        """
        if not self.collection:
            return False

        # First deactivate all rates
        self.collection.update_many(
            {"is_active": True},
            {"$set": {"is_active": False, "updated_at": self._get_current_time()}}
        )

        # Then activate the specified rate
        result = self.collection.update_one(
            {"rate_id": rate_id},
            {"$set": {"is_active": True, "updated_at": self._get_current_time()}}
        )

        return result.modified_count > 0

    def deactivate_rate(self, rate_id: str) -> bool:
        """
        Deactivate a specific conversion rate.

        Args:
            rate_id: Rate ID to deactivate

        Returns:
            bool: True if deactivation was successful
        """
        result = self.update_one(
            {"rate_id": rate_id},
            {"is_active": False, "updated_at": self._get_current_time()}
        )
        return result

    def get_active_rates(self) -> List[ConversionRate]:
        """
        Get all currently active conversion rates.

        Returns:
            List[ConversionRate]: List of active rates
        """
        rates_data = self.find_many(
            {"is_active": True},
            sort=[("created_at", -1)]
        )

        return [ConversionRate.from_dict(data) for data in rates_data]

    def get_historical_rates(self, start_date: datetime = None,
                            end_date: datetime = None,
                            limit: int = 100) -> List[ConversionRate]:
        """
        Get historical conversion rates within a date range.

        Args:
            start_date: Start date for filtering (inclusive)
            end_date: End date for filtering (inclusive)
            limit: Maximum number of rates to return

        Returns:
            List[ConversionRate]: List of historical rates
        """
        filter_criteria = {}

        if start_date or end_date:
            date_filter = {}
            if start_date:
                date_filter["$gte"] = start_date
            if end_date:
                date_filter["$lte"] = end_date
            filter_criteria["created_at"] = date_filter

        rates_data = self.find_many(
            filter_criteria,
            limit=limit,
            sort=[("created_at", -1)]
        )

        return [ConversionRate.from_dict(data) for data in rates_data]

    def get_rates_valid_at(self, check_time: datetime) -> List[ConversionRate]:
        """
        Get all conversion rates that were valid at a specific time.

        Args:
            check_time: Time to check validity

        Returns:
            List[ConversionRate]: List of rates valid at the given time
        """
        filter_criteria = {
            "$or": [
                {"valid_from": {"$lte": check_time}, "valid_until": {"$gte": check_time}},
                {"valid_from": {"$lte": check_time}, "valid_until": None}
            ]
        }

        rates_data = self.find_many(
            filter_criteria,
            sort=[("created_at", -1)]
        )

        return [ConversionRate.from_dict(data) for data in rates_data]

    def update_multiplier(self, rate_id: str, multiplier_type: str,
                         new_value: float) -> bool:
        """
        Update a specific multiplier in a conversion rate.

        Args:
            rate_id: Rate identifier
            multiplier_type: Type of multiplier to update
            new_value: New multiplier value

        Returns:
            bool: True if update was successful
        """
        if not isinstance(new_value, (int, float)) or new_value < 0 or new_value > 10:
            return False

        result = self.update_one(
            {"rate_id": rate_id},
            {
                f"multipliers.{multiplier_type}": float(new_value),
                "updated_at": self._get_current_time()
            }
        )
        return result

    def batch_update_multipliers(self, rate_id: str,
                                multipliers: Dict[str, float]) -> bool:
        """
        Batch update multiple multipliers in a conversion rate.

        Args:
            rate_id: Rate identifier
            multipliers: Dictionary of multiplier type -> value mappings

        Returns:
            bool: True if update was successful
        """
        if not multipliers:
            return False

        # Validate all multipliers first
        for multiplier_type, value in multipliers.items():
            if not isinstance(value, (int, float)) or value < 0 or value > 10:
                return False

        update_data = {"updated_at": self._get_current_time()}
        for multiplier_type, value in multipliers.items():
            update_data[f"multipliers.{multiplier_type}"] = float(value)

        result = self.update_one({"rate_id": rate_id}, update_data)
        return result

    def create_special_event_rate(self, event_name: str, base_multiplier: float,
                                 valid_from: datetime, valid_until: datetime,
                                 description: str = None) -> Optional[ConversionRate]:
        """
        Create a special event conversion rate.

        Args:
            event_name: Name of the special event
            base_multiplier: Base multiplier for the event
            valid_from: Event start time
            valid_until: Event end time
            description: Optional event description

        Returns:
            Optional[ConversionRate]: Created rate or None if failed
        """
        # Get current default rate as base
        default_rate = self.get_default_rate()
        if not default_rate:
            return None

        event_rate = ConversionRate.create_special_event_rates(
            event_name=event_name,
            base_multiplier=base_multiplier,
            valid_from=valid_from,
            valid_until=valid_until
        )

        if description:
            event_rate.description = description

        try:
            rate_id = self.create_rate(event_rate)
            return event_rate
        except Exception:
            return None

    def expire_old_rates(self) -> int:
        """
        Expire old conversion rates that are past their validity period.

        Returns:
            int: Number of rates expired
        """
        if not self.collection:
            return 0

        current_time = datetime.now(timezone.utc)

        result = self.collection.update_many(
            {
                "is_active": True,
                "valid_until": {"$lt": current_time}
            },
            {
                "$set": {
                    "is_active": False,
                    "updated_at": current_time
                }
            }
        )

        return result.modified_count

    def get_rate_statistics(self) -> Dict[str, Any]:
        """
        Get conversion rate statistics for reporting.

        Returns:
            Dict[str, Any]: Rate statistics
        """
        if not self.collection:
            return {}

        pipeline = [
            {
                "$group": {
                    "_id": None,
                    "total_rates": {"$sum": 1},
                    "active_rates": {
                        "$sum": {"$cond": ["$is_active", 1, 0]}
                    },
                    "avg_base_rate": {"$avg": "$base_rate"},
                    "max_base_rate": {"$max": "$base_rate"},
                    "min_base_rate": {"$min": "$base_rate"}
                }
            }
        ]

        result = list(self.collection.aggregate(pipeline))
        if result:
            stats = result[0]
            del stats['_id']
            return stats

        return {
            "total_rates": 0,
            "active_rates": 0,
            "avg_base_rate": 0.0,
            "max_base_rate": 0.0,
            "min_base_rate": 0.0
        }

    def search_rates(self, search_criteria: Dict[str, Any],
                    page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """
        Search conversion rates with pagination.

        Args:
            search_criteria: Search criteria dictionary
            page: Page number (1-based)
            page_size: Number of results per page

        Returns:
            Dict containing rates and pagination info
        """
        skip = (page - 1) * page_size

        rates_data = self.find_many(
            search_criteria,
            limit=page_size,
            skip=skip,
            sort=[("created_at", -1)]
        )

        total_count = self.count(search_criteria)
        total_pages = (total_count + page_size - 1) // page_size

        return {
            "rates": [ConversionRate.from_dict(data) for data in rates_data],
            "pagination": {
                "page": page,
                "per_page": page_size,
                "total_items": total_count,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        }

    def delete_rate(self, rate_id: str) -> bool:
        """
        Delete a conversion rate.

        Args:
            rate_id: Rate identifier to delete

        Returns:
            bool: True if deletion was successful
        """
        return self.delete_one({"rate_id": rate_id})

    def ensure_default_rate_exists(self) -> ConversionRate:
        """
        Ensure that a default conversion rate exists in the database.
        Creates one if it doesn't exist.

        Returns:
            ConversionRate: The default conversion rate
        """
        default_rate = self.get_default_rate()

        if not default_rate:
            # Create default rate
            default_rate = ConversionRate.create_default_rates()
            self.create_rate(default_rate)

        return default_rate