from typing import Dict, Any, Optional
from datetime import datetime, timezone, timedelta
from app.core.utils.json_encoder import serialize_model_dates


class DeviceToken:
    """
    Model for storing user device tokens for push notifications.

    Supports both Android (FCM) and iOS (APNs via FCM).
    """

    # Platform constants (mobile only, no web support)
    PLATFORM_ANDROID = 'android'
    PLATFORM_IOS = 'ios'

    VALID_PLATFORMS = [PLATFORM_ANDROID, PLATFORM_IOS]

    # Token expiry duration (90 days of inactivity)
    TOKEN_EXPIRY_DAYS = 90

    def __init__(
        self,
        token_id: str,
        user_id: str,
        device_token: str,
        platform: str,
        device_id: Optional[str] = None,
        device_info: Optional[Dict[str, Any]] = None,
        last_used_at: Optional[datetime] = None,
        created_at: Optional[datetime] = None,
        _id: Optional[str] = None
    ):
        """
        Initialize DeviceToken.

        Args:
            token_id: Unique token identifier
            user_id: User ID who owns this device
            device_token: FCM device token
            platform: Device platform (android/ios only)
            device_id: Unique device identifier (generated if not provided)
            device_info: Additional device information
            last_used_at: Last time this token was used
            created_at: Token creation timestamp
            _id: MongoDB document ID
        """
        import uuid

        self._id = _id
        self.token_id = token_id
        self.user_id = user_id
        self.device_token = device_token
        self.platform = platform
        self.device_id = device_id or f"device_{uuid.uuid4().hex[:12]}"
        self.device_info = device_info or {}
        self.last_used_at = last_used_at or datetime.now(timezone.utc)
        self.created_at = created_at or datetime.now(timezone.utc)

        # Validate platform
        if platform not in self.VALID_PLATFORMS:
            raise ValueError(f"Invalid platform. Must be one of: {self.VALID_PLATFORMS}")

    def is_valid(self) -> bool:
        """
        Check if token is still valid (not expired due to inactivity).

        Returns:
            True if token is valid, False if expired
        """
        if not self.last_used_at:
            return True

        expiry_threshold = datetime.now(timezone.utc) - timedelta(days=self.TOKEN_EXPIRY_DAYS)
        return self.last_used_at > expiry_threshold

    def update_last_used(self):
        """Update last_used_at to current timestamp"""
        self.last_used_at = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary representation.

        Returns:
            Dictionary with all device token fields in ISO 8601 format
        """
        token_dict = {
            'token_id': self.token_id,
            'user_id': self.user_id,
            'device_id': self.device_id,
            'device_token': self.device_token,
            'platform': self.platform,
            'device_info': self.device_info,
            'last_used_at': self.last_used_at,
            'created_at': self.created_at,
            'is_valid': self.is_valid()
        }

        # Serialize datetime fields to ISO 8601
        return serialize_model_dates(token_dict)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'DeviceToken':
        """
        Create DeviceToken from dictionary.

        Args:
            data: Dictionary with device token data

        Returns:
            DeviceToken instance
        """
        return DeviceToken(
            token_id=data['token_id'],
            user_id=data['user_id'],
            device_token=data['device_token'],
            platform=data['platform'],
            device_id=data.get('device_id'),
            device_info=data.get('device_info'),
            last_used_at=data.get('last_used_at'),
            created_at=data.get('created_at'),
            _id=str(data['_id']) if '_id' in data else None
        )

    def __repr__(self) -> str:
        """String representation for logging"""
        return f"<DeviceToken token_id={self.token_id} user_id={self.user_id} platform={self.platform}>"
