from typing import Dict, Any, Optional
from datetime import datetime, timezone as dt_timezone, time
import pytz
from app.core.utils.json_encoder import serialize_model_dates


class NotificationPreferences:
    """
    Model for user notification preferences.

    Controls when and how users receive notifications.
    """

    # Default preferences
    DEFAULT_PREFERENCES = {
        'push_enabled': True,
        'quiet_hours_enabled': False,
        'quiet_hours_start': '22:00',  # 10 PM
        'quiet_hours_end': '08:00',     # 8 AM
        'timezone': 'UTC',
        'notification_types': {
            'invitation_received': True,
            'invitation_accepted': True,
            'invitation_declined': True,
            'invitation_expired': True,
            'invitation_expiring_soon': True,
            'friend_online': True,
            'friend_joined_room': True,
            'room_started': True,
            'system_announcement': True
        }
    }

    def __init__(
        self,
        user_id: str,
        push_enabled: bool = True,
        quiet_hours_enabled: bool = False,
        quiet_hours_start: str = '22:00',
        quiet_hours_end: str = '08:00',
        timezone: str = 'UTC',
        notification_types: Optional[Dict[str, bool]] = None,
        updated_at: Optional[datetime] = None,
        _id: Optional[str] = None
    ):
        """
        Initialize NotificationPreferences.

        Args:
            user_id: User ID
            push_enabled: Whether push notifications are enabled globally
            quiet_hours_enabled: Whether quiet hours are enabled
            quiet_hours_start: Start time for quiet hours (HH:MM format)
            quiet_hours_end: End time for quiet hours (HH:MM format)
            timezone: User's timezone (e.g., 'America/New_York', 'Europe/Rome')
            notification_types: Dict of notification type: enabled status
            updated_at: Last update timestamp
            _id: MongoDB document ID
        """
        self._id = _id
        self.user_id = user_id
        self.push_enabled = push_enabled
        self.quiet_hours_enabled = quiet_hours_enabled
        self.quiet_hours_start = quiet_hours_start
        self.quiet_hours_end = quiet_hours_end
        self.timezone = timezone
        self.notification_types = notification_types or self.DEFAULT_PREFERENCES['notification_types'].copy()
        self.updated_at = updated_at or datetime.now(dt_timezone.utc)

        # Validate timezone
        try:
            pytz.timezone(timezone)
        except pytz.exceptions.UnknownTimeZoneError:
            raise ValueError(f"Invalid timezone: {timezone}")

        # Validate time formats
        try:
            datetime.strptime(quiet_hours_start, '%H:%M')
            datetime.strptime(quiet_hours_end, '%H:%M')
        except ValueError:
            raise ValueError("Quiet hours must be in HH:MM format")

    def is_type_enabled(self, notification_type: str) -> bool:
        """
        Check if specific notification type is enabled.

        Args:
            notification_type: Notification type to check

        Returns:
            True if enabled, False otherwise
        """
        return self.notification_types.get(notification_type, False)

    def is_in_quiet_hours(self) -> bool:
        """
        Check if current time is within quiet hours.

        Returns:
            True if in quiet hours, False otherwise
        """
        if not self.quiet_hours_enabled:
            return False

        try:
            # Get current time in user's timezone
            user_tz = pytz.timezone(self.timezone)
            now = datetime.now(user_tz)
            current_time = now.time()

            # Parse quiet hours
            start_time = datetime.strptime(self.quiet_hours_start, '%H:%M').time()
            end_time = datetime.strptime(self.quiet_hours_end, '%H:%M').time()

            # Handle quiet hours that span midnight
            if start_time <= end_time:
                # Normal case: 08:00 - 22:00
                return start_time <= current_time <= end_time
            else:
                # Spans midnight: 22:00 - 08:00
                return current_time >= start_time or current_time <= end_time

        except Exception:
            # If any error, assume not in quiet hours
            return False

    def should_send_notification(self, notification_type: str) -> bool:
        """
        Check if notification should be sent based on preferences.

        Args:
            notification_type: Type of notification

        Returns:
            True if should send, False if blocked by preferences
        """
        # Check global push enabled
        if not self.push_enabled:
            return False

        # Check if notification type is enabled
        if not self.is_type_enabled(notification_type):
            return False

        # Check quiet hours
        if self.is_in_quiet_hours():
            return False

        return True

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary representation.

        Returns:
            Dictionary with all preference fields
        """
        prefs_dict = {
            'user_id': self.user_id,
            'push_enabled': self.push_enabled,
            'quiet_hours_enabled': self.quiet_hours_enabled,
            'quiet_hours_start': self.quiet_hours_start,
            'quiet_hours_end': self.quiet_hours_end,
            'timezone': self.timezone,
            'notification_types': self.notification_types,
            'updated_at': self.updated_at
        }

        # Serialize datetime fields to ISO 8601
        return serialize_model_dates(prefs_dict)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'NotificationPreferences':
        """
        Create NotificationPreferences from dictionary.

        Args:
            data: Dictionary with preferences data

        Returns:
            NotificationPreferences instance
        """
        return NotificationPreferences(
            user_id=data['user_id'],
            push_enabled=data.get('push_enabled', True),
            quiet_hours_enabled=data.get('quiet_hours_enabled', False),
            quiet_hours_start=data.get('quiet_hours_start', '22:00'),
            quiet_hours_end=data.get('quiet_hours_end', '08:00'),
            timezone=data.get('timezone', 'UTC'),
            notification_types=data.get('notification_types', NotificationPreferences.DEFAULT_PREFERENCES['notification_types'].copy()),
            updated_at=data.get('updated_at'),
            _id=str(data['_id']) if '_id' in data else None
        )

    @staticmethod
    def get_default_preferences(user_id: str) -> 'NotificationPreferences':
        """
        Create default preferences for a new user.

        Args:
            user_id: User ID

        Returns:
            NotificationPreferences with default values
        """
        return NotificationPreferences(
            user_id=user_id,
            **NotificationPreferences.DEFAULT_PREFERENCES
        )

    def __repr__(self) -> str:
        """String representation for logging"""
        return (
            f"<NotificationPreferences user_id={self.user_id} "
            f"push_enabled={self.push_enabled} quiet_hours={self.quiet_hours_enabled}>"
        )
