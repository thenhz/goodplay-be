from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from bson import ObjectId
from flask import current_app
from app.core.repositories.base_repository import BaseRepository
from app.donations.models.payment_provider import PaymentProvider, PaymentProviderType


class PaymentProviderRepository(BaseRepository):
    """
    Repository for PaymentProvider data access operations.

    Handles CRUD operations and queries for payment provider configurations.
    Manages provider status, health checks, and priority ordering.
    """

    def __init__(self):
        super().__init__('payment_providers')

    def create_indexes(self):
        """Create database indexes for payment providers collection."""
        import os
        if self.collection is None or os.getenv('TESTING') == 'true':
            return

        try:
            # Create indexes for common queries
            self.collection.create_index("provider_id", unique=True)
            self.collection.create_index("provider_type")
            self.collection.create_index([("is_active", 1), ("priority", -1)])
            self.collection.create_index("health_status")
            self.collection.create_index("is_test_mode")
            self.collection.create_index("created_at")

            current_app.logger.info("PaymentProvider indexes created successfully")
        except Exception as e:
            current_app.logger.error(f"Failed to create PaymentProvider indexes: {str(e)}")

    def create_provider(self, provider: PaymentProvider) -> str:
        """
        Create a new payment provider.

        Args:
            provider: PaymentProvider instance

        Returns:
            Created provider ID
        """
        try:
            provider_data = provider.to_dict()
            result = self.collection.insert_one(provider_data)

            current_app.logger.info(f"Created payment provider: {provider.provider_id}")
            return str(result.inserted_id)

        except Exception as e:
            current_app.logger.error(f"Failed to create payment provider: {str(e)}")
            raise

    def find_by_provider_id(self, provider_id: str) -> Optional[PaymentProvider]:
        """
        Find payment provider by provider ID.

        Args:
            provider_id: Provider identifier

        Returns:
            PaymentProvider instance or None
        """
        try:
            provider_data = self.collection.find_one({"provider_id": provider_id})

            if provider_data:
                return PaymentProvider.from_dict(provider_data)
            return None

        except Exception as e:
            current_app.logger.error(f"Failed to find payment provider {provider_id}: {str(e)}")
            return None

    def find_by_type(self, provider_type: str) -> List[PaymentProvider]:
        """
        Find payment providers by type.

        Args:
            provider_type: Provider type (e.g., 'stripe', 'paypal')

        Returns:
            List of PaymentProvider instances
        """
        try:
            query = {"provider_type": provider_type}
            providers_data = self.collection.find(query).sort("priority", -1)

            return [PaymentProvider.from_dict(data) for data in providers_data]

        except Exception as e:
            current_app.logger.error(f"Failed to find providers by type {provider_type}: {str(e)}")
            return []

    def find_active_providers(self, country_code: str = None) -> List[PaymentProvider]:
        """
        Find active payment providers, optionally filtered by country.

        Args:
            country_code: Optional country code filter

        Returns:
            List of active PaymentProvider instances ordered by priority
        """
        try:
            query = {
                "is_active": True,
                "health_status": "healthy"
            }

            if country_code:
                query["supported_countries"] = country_code.upper()

            providers_data = self.collection.find(query).sort("priority", -1)

            return [PaymentProvider.from_dict(data) for data in providers_data]

        except Exception as e:
            current_app.logger.error(f"Failed to find active providers: {str(e)}")
            return []

    def get_primary_provider(self, provider_type: str = None) -> Optional[PaymentProvider]:
        """
        Get the primary (highest priority) active provider.

        Args:
            provider_type: Optional provider type filter

        Returns:
            Primary PaymentProvider or None
        """
        try:
            query = {
                "is_active": True,
                "health_status": "healthy"
            }

            if provider_type:
                query["provider_type"] = provider_type

            provider_data = self.collection.find_one(query, sort=[("priority", -1)])

            if provider_data:
                return PaymentProvider.from_dict(provider_data)
            return None

        except Exception as e:
            current_app.logger.error(f"Failed to get primary provider: {str(e)}")
            return None

    def update_provider(self, provider_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update payment provider configuration.

        Args:
            provider_id: Provider identifier
            updates: Dictionary of fields to update

        Returns:
            True if update was successful
        """
        try:
            updates['updated_at'] = datetime.now(timezone.utc)

            result = self.collection.update_one(
                {"provider_id": provider_id},
                {"$set": updates}
            )

            if result.modified_count > 0:
                current_app.logger.info(f"Updated payment provider {provider_id}")
                return True
            else:
                current_app.logger.warning(f"No changes made to payment provider {provider_id}")
                return False

        except Exception as e:
            current_app.logger.error(f"Failed to update payment provider {provider_id}: {str(e)}")
            return False

    def update_health_status(self, provider_id: str, status: str, check_time: datetime = None) -> bool:
        """
        Update provider health status.

        Args:
            provider_id: Provider identifier
            status: Health status
            check_time: Time of health check

        Returns:
            True if update was successful
        """
        try:
            updates = {
                'health_status': status,
                'last_health_check': check_time or datetime.now(timezone.utc),
                'updated_at': datetime.now(timezone.utc)
            }

            result = self.collection.update_one(
                {"provider_id": provider_id},
                {"$set": updates}
            )

            if result.modified_count > 0:
                current_app.logger.info(f"Updated health status for provider {provider_id}: {status}")
                return True
            return False

        except Exception as e:
            current_app.logger.error(f"Failed to update health status for provider {provider_id}: {str(e)}")
            return False

    def deactivate_provider(self, provider_id: str) -> bool:
        """
        Deactivate a payment provider.

        Args:
            provider_id: Provider identifier

        Returns:
            True if deactivation was successful
        """
        try:
            updates = {
                'is_active': False,
                'updated_at': datetime.now(timezone.utc)
            }

            result = self.collection.update_one(
                {"provider_id": provider_id},
                {"$set": updates}
            )

            if result.modified_count > 0:
                current_app.logger.info(f"Deactivated payment provider {provider_id}")
                return True
            return False

        except Exception as e:
            current_app.logger.error(f"Failed to deactivate payment provider {provider_id}: {str(e)}")
            return False

    def get_providers_by_currency(self, currency: str) -> List[PaymentProvider]:
        """
        Get active providers that support a specific currency.

        Args:
            currency: Currency code (e.g., 'EUR', 'USD')

        Returns:
            List of PaymentProvider instances
        """
        try:
            query = {
                "is_active": True,
                "health_status": "healthy",
                "supported_currencies": currency.upper()
            }

            providers_data = self.collection.find(query).sort("priority", -1)

            return [PaymentProvider.from_dict(data) for data in providers_data]

        except Exception as e:
            current_app.logger.error(f"Failed to find providers for currency {currency}: {str(e)}")
            return []

    def get_test_providers(self) -> List[PaymentProvider]:
        """
        Get providers configured for test mode.

        Returns:
            List of test mode PaymentProvider instances
        """
        try:
            query = {
                "is_active": True,
                "is_test_mode": True
            }

            providers_data = self.collection.find(query).sort("priority", -1)

            return [PaymentProvider.from_dict(data) for data in providers_data]

        except Exception as e:
            current_app.logger.error(f"Failed to find test providers: {str(e)}")
            return []

    def get_all_providers(self, include_inactive: bool = False) -> List[PaymentProvider]:
        """
        Get all payment providers.

        Args:
            include_inactive: Whether to include inactive providers

        Returns:
            List of PaymentProvider instances
        """
        try:
            query = {}
            if not include_inactive:
                query["is_active"] = True

            providers_data = self.collection.find(query).sort([("provider_type", 1), ("priority", -1)])

            return [PaymentProvider.from_dict(data) for data in providers_data]

        except Exception as e:
            current_app.logger.error(f"Failed to get all providers: {str(e)}")
            return []

    def delete_provider(self, provider_id: str) -> bool:
        """
        Delete a payment provider (use with caution).

        Args:
            provider_id: Provider identifier

        Returns:
            True if deletion was successful
        """
        try:
            result = self.collection.delete_one({"provider_id": provider_id})

            if result.deleted_count > 0:
                current_app.logger.warning(f"Deleted payment provider {provider_id}")
                return True
            return False

        except Exception as e:
            current_app.logger.error(f"Failed to delete payment provider {provider_id}: {str(e)}")
            return False

    def get_provider_statistics(self, provider_id: str) -> Optional[Dict[str, Any]]:
        """
        Get statistics for a specific provider (placeholder for future implementation).

        Args:
            provider_id: Provider identifier

        Returns:
            Provider statistics dictionary
        """
        try:
            # This would aggregate payment data from payment_intents collection
            # For now, return basic provider info
            provider = self.find_by_provider_id(provider_id)
            if not provider:
                return None

            return {
                'provider_id': provider_id,
                'provider_type': provider.provider_type,
                'is_active': provider.is_active,
                'health_status': provider.health_status,
                'last_health_check': provider.last_health_check,
                'supported_currencies': provider.supported_currencies,
                'processing_fee_percentage': provider.processing_fee_percentage,
                'created_at': provider.created_at
            }

        except Exception as e:
            current_app.logger.error(f"Failed to get provider statistics for {provider_id}: {str(e)}")
            return None