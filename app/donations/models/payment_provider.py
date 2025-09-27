from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from bson import ObjectId
import json
import base64
from cryptography.fernet import Fernet
import os


class PaymentProviderType:
    """Payment provider type constants."""
    STRIPE = "stripe"
    PAYPAL = "paypal"
    BANK_TRANSFER = "bank_transfer"
    APPLE_PAY = "apple_pay"
    GOOGLE_PAY = "google_pay"

    @classmethod
    def get_all_types(cls) -> List[str]:
        return [cls.STRIPE, cls.PAYPAL, cls.BANK_TRANSFER, cls.APPLE_PAY, cls.GOOGLE_PAY]


class PaymentProvider:
    """
    Payment provider model for managing payment gateway integrations.

    Handles provider configuration, API credentials (encrypted), and processing capabilities.
    Supports multiple payment providers (Stripe, PayPal, etc.) with secure credential storage.
    """

    def __init__(self, provider_type: str, name: str, **kwargs):
        self._id = kwargs.get('_id', ObjectId())
        self.provider_id = kwargs.get('provider_id', str(self._id))
        self.provider_type = provider_type
        self.name = name
        self.display_name = kwargs.get('display_name', name)
        self.description = kwargs.get('description', '')

        # Encryption for sensitive data
        self._encryption_key = self._get_encryption_key()

        # API Configuration (encrypted)
        self.api_credentials = kwargs.get('api_credentials', {})
        self.webhook_secret = kwargs.get('webhook_secret', '')
        self.api_endpoint = kwargs.get('api_endpoint', '')

        # Provider capabilities
        self.supported_currencies = kwargs.get('supported_currencies', ['EUR', 'USD'])
        self.supported_countries = kwargs.get('supported_countries', ['IT', 'US', 'DE', 'FR'])
        self.min_amount = kwargs.get('min_amount', 1.0)  # Minimum transaction amount
        self.max_amount = kwargs.get('max_amount', 50000.0)  # Maximum transaction amount

        # Processing fees and configuration
        self.processing_fee_percentage = kwargs.get('processing_fee_percentage', 2.9)
        self.processing_fee_fixed = kwargs.get('processing_fee_fixed', 0.30)
        self.settlement_time_days = kwargs.get('settlement_time_days', 2)

        # Provider status and configuration
        self.is_active = kwargs.get('is_active', True)
        self.is_test_mode = kwargs.get('is_test_mode', True)
        self.priority = kwargs.get('priority', 1)  # Higher number = higher priority

        # Provider-specific configuration
        self.configuration = kwargs.get('configuration', {})

        # Metadata and tracking
        self.metadata = kwargs.get('metadata', {})
        self.created_at = kwargs.get('created_at', datetime.now(timezone.utc))
        self.updated_at = kwargs.get('updated_at', datetime.now(timezone.utc))
        self.last_health_check = kwargs.get('last_health_check')
        self.health_status = kwargs.get('health_status', 'unknown')  # healthy, degraded, down, unknown

        # Validate provider type
        if self.provider_type not in PaymentProviderType.get_all_types():
            raise ValueError(f"Invalid provider type: {self.provider_type}")

    def _get_encryption_key(self) -> bytes:
        """
        Get or create encryption key for sensitive data.
        In production, this should come from secure key management service.
        """
        # For testing, use a fixed key. In production, use proper key management
        key_env = os.getenv('PAYMENT_ENCRYPTION_KEY')
        if key_env:
            return base64.urlsafe_b64decode(key_env.encode())

        # Default key for development/testing (DO NOT use in production)
        default_key = b'test-key-32-chars-1234567890123456'
        return base64.urlsafe_b64encode(default_key)

    def encrypt_credentials(self, credentials: Dict[str, Any]) -> str:
        """
        Encrypt API credentials for secure storage.

        Args:
            credentials: Dictionary containing API keys, secrets, etc.

        Returns:
            Encrypted credentials as base64 string
        """
        try:
            fernet = Fernet(self._encryption_key)
            credentials_json = json.dumps(credentials).encode()
            encrypted = fernet.encrypt(credentials_json)
            return base64.b64encode(encrypted).decode()
        except Exception as e:
            raise ValueError(f"Failed to encrypt credentials: {str(e)}")

    def decrypt_credentials(self, encrypted_credentials: str) -> Dict[str, Any]:
        """
        Decrypt API credentials for use.

        Args:
            encrypted_credentials: Base64 encoded encrypted credentials

        Returns:
            Decrypted credentials dictionary
        """
        try:
            fernet = Fernet(self._encryption_key)
            encrypted_bytes = base64.b64decode(encrypted_credentials.encode())
            decrypted = fernet.decrypt(encrypted_bytes)
            return json.loads(decrypted.decode())
        except Exception as e:
            raise ValueError(f"Failed to decrypt credentials: {str(e)}")

    def set_credentials(self, credentials: Dict[str, Any]) -> None:
        """
        Set encrypted API credentials.

        Args:
            credentials: API credentials dictionary
        """
        self.api_credentials = self.encrypt_credentials(credentials)
        self.updated_at = datetime.now(timezone.utc)

    def get_credentials(self) -> Dict[str, Any]:
        """
        Get decrypted API credentials.

        Returns:
            Decrypted credentials dictionary
        """
        if not self.api_credentials:
            return {}
        return self.decrypt_credentials(self.api_credentials)

    def calculate_processing_fee(self, amount: float) -> float:
        """
        Calculate total processing fee for a given amount.

        Args:
            amount: Transaction amount

        Returns:
            Total processing fee
        """
        percentage_fee = amount * (self.processing_fee_percentage / 100)
        total_fee = percentage_fee + self.processing_fee_fixed
        return round(total_fee, 2)

    def validate_amount(self, amount: float, currency: str = 'EUR') -> tuple[bool, str]:
        """
        Validate transaction amount against provider limits.

        Args:
            amount: Transaction amount
            currency: Transaction currency

        Returns:
            Tuple of (is_valid, error_message)
        """
        if currency not in self.supported_currencies:
            return False, f"Currency {currency} not supported by {self.name}"

        if amount < self.min_amount:
            return False, f"Amount below minimum: {self.min_amount} {currency}"

        if amount > self.max_amount:
            return False, f"Amount above maximum: {self.max_amount} {currency}"

        return True, ""

    def supports_country(self, country_code: str) -> bool:
        """
        Check if provider supports transactions in given country.

        Args:
            country_code: ISO country code (e.g., 'IT', 'US')

        Returns:
            True if country is supported
        """
        return country_code.upper() in self.supported_countries

    def update_health_status(self, status: str, check_time: Optional[datetime] = None) -> None:
        """
        Update provider health status.

        Args:
            status: Health status (healthy, degraded, down, unknown)
            check_time: Time of health check
        """
        valid_statuses = ['healthy', 'degraded', 'down', 'unknown']
        if status not in valid_statuses:
            raise ValueError(f"Invalid health status: {status}")

        self.health_status = status
        self.last_health_check = check_time or datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    def is_healthy(self) -> bool:
        """
        Check if provider is healthy and available for processing.

        Returns:
            True if provider is healthy and active
        """
        return self.is_active and self.health_status == 'healthy'

    def get_provider_config(self) -> Dict[str, Any]:
        """
        Get provider-specific configuration for API calls.

        Returns:
            Configuration dictionary
        """
        config = {
            'provider_type': self.provider_type,
            'api_endpoint': self.api_endpoint,
            'is_test_mode': self.is_test_mode,
            'supported_currencies': self.supported_currencies,
            'min_amount': self.min_amount,
            'max_amount': self.max_amount,
            'settlement_time_days': self.settlement_time_days
        }

        # Add provider-specific configuration
        config.update(self.configuration)

        return config

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert PaymentProvider to dictionary for database storage.

        Returns:
            Dictionary representation
        """
        return {
            '_id': self._id,
            'provider_id': self.provider_id,
            'provider_type': self.provider_type,
            'name': self.name,
            'display_name': self.display_name,
            'description': self.description,
            'api_credentials': self.api_credentials,  # Already encrypted
            'webhook_secret': self.webhook_secret,
            'api_endpoint': self.api_endpoint,
            'supported_currencies': self.supported_currencies,
            'supported_countries': self.supported_countries,
            'min_amount': self.min_amount,
            'max_amount': self.max_amount,
            'processing_fee_percentage': self.processing_fee_percentage,
            'processing_fee_fixed': self.processing_fee_fixed,
            'settlement_time_days': self.settlement_time_days,
            'is_active': self.is_active,
            'is_test_mode': self.is_test_mode,
            'priority': self.priority,
            'configuration': self.configuration,
            'metadata': self.metadata,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'last_health_check': self.last_health_check,
            'health_status': self.health_status
        }

    def to_api_dict(self) -> Dict[str, Any]:
        """
        Convert PaymentProvider to dictionary for API responses (excluding sensitive data).

        Returns:
            Safe dictionary representation for API
        """
        return {
            'provider_id': self.provider_id,
            'provider_type': self.provider_type,
            'name': self.name,
            'display_name': self.display_name,
            'description': self.description,
            'supported_currencies': self.supported_currencies,
            'supported_countries': self.supported_countries,
            'min_amount': self.min_amount,
            'max_amount': self.max_amount,
            'processing_fee_percentage': self.processing_fee_percentage,
            'processing_fee_fixed': self.processing_fee_fixed,
            'settlement_time_days': self.settlement_time_days,
            'is_active': self.is_active,
            'is_test_mode': self.is_test_mode,
            'priority': self.priority,
            'health_status': self.health_status,
            'last_health_check': self.last_health_check,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PaymentProvider':
        """
        Create PaymentProvider from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            PaymentProvider instance
        """
        return cls(**data)

    def __str__(self) -> str:
        return f"PaymentProvider({self.provider_type}:{self.name})"

    def __repr__(self) -> str:
        return f"PaymentProvider(provider_id='{self.provider_id}', type='{self.provider_type}', name='{self.name}', active={self.is_active})"