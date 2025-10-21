from typing import Dict, Any, Optional
from datetime import datetime, timezone
from app.core.utils.json_encoder import serialize_model_dates


class UserNotification:
    """
    Model for storing user notifications in persistent inbox.

    All notifications are stored regardless of delivery status.
    """

    # Notification types (matching OpenAPI spec)
    TYPE_ROOM_INVITATION = 'room_invitation'
    TYPE_INVITATION_RECEIVED = 'invitation_received'  # GOO-60: New invitation received
    TYPE_FRIEND_REQUEST = 'friend_request'
    TYPE_FRIEND_ONLINE = 'friend_online'
    TYPE_ROOM_STARTED = 'room_started'
    TYPE_FRIEND_JOINED_ROOM = 'friend_joined_room'
    TYPE_INVITATION_ACCEPTED = 'invitation_accepted'
    TYPE_INVITATION_DECLINED = 'invitation_declined'
    TYPE_INVITATION_EXPIRED = 'invitation_expired'
    TYPE_INVITATION_EXPIRING_SOON = 'invitation_expiring_soon'  # GOO-60: Invitation expiring warning

    VALID_TYPES = [
        TYPE_ROOM_INVITATION,
        TYPE_INVITATION_RECEIVED,
        TYPE_FRIEND_REQUEST,
        TYPE_FRIEND_ONLINE,
        TYPE_ROOM_STARTED,
        TYPE_FRIEND_JOINED_ROOM,
        TYPE_INVITATION_ACCEPTED,
        TYPE_INVITATION_DECLINED,
        TYPE_INVITATION_EXPIRED,
        TYPE_INVITATION_EXPIRING_SOON
    ]

    def __init__(
        self,
        notification_id: str,  # Internal field name, will be exposed as 'id' in API
        user_id: str,
        type: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
        is_read: bool = False,  # Changed from 'read' to 'is_read'
        read_at: Optional[datetime] = None,
        expires_at: Optional[datetime] = None,  # New field for time-sensitive notifications
        deleted: bool = False,
        created_at: Optional[datetime] = None,
        _id: Optional[str] = None
    ):
        """
        Initialize UserNotification.

        Args:
            notification_id: Unique notification identifier (exposed as 'id' in API)
            user_id: User ID who receives this notification
            type: Notification type (see TYPE_* constants)
            title: Notification title (localized on backend)
            body: Notification body text (localized on backend)
            data: Additional structured data
            is_read: Whether notification has been read
            read_at: Timestamp when notification was read
            expires_at: Optional expiration timestamp (for time-sensitive notifications)
            deleted: Soft delete flag
            created_at: Creation timestamp
            _id: MongoDB document ID
        """
        self._id = _id
        self.notification_id = notification_id  # Internal: notification_id, API: id
        self.user_id = user_id
        self.type = type
        self.title = title
        self.body = body
        self.data = data or {}
        self.is_read = is_read  # Changed from 'read'
        self.read_at = read_at
        self.expires_at = expires_at  # New field
        self.deleted = deleted
        self.created_at = created_at or datetime.now(timezone.utc)

        # Validate type
        if type not in self.VALID_TYPES:
            raise ValueError(f"Invalid notification type. Must be one of: {self.VALID_TYPES}")

    def mark_as_read(self):
        """Mark notification as read"""
        self.is_read = True
        self.read_at = datetime.now(timezone.utc)

    def mark_as_unread(self):
        """Mark notification as unread"""
        self.is_read = False
        self.read_at = None

    def mark_as_deleted(self):
        """Soft delete notification"""
        self.deleted = True

    def is_expired(self) -> bool:
        """Check if notification has expired"""
        if not self.expires_at:
            return False
        return datetime.now(timezone.utc) > self.expires_at

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary representation for API response.

        Returns:
            Dictionary with all notification fields in ISO 8601 format.
            Maps internal field names to API field names.
        """
        notif_dict = {
            'id': self.notification_id,  # API expects 'id', not 'notification_id'
            'user_id': self.user_id,
            'type': self.type,
            'title': self.title,
            'body': self.body,
            'data': self.data,
            'is_read': self.is_read,  # API expects 'is_read', not 'read'
            'read_at': self.read_at,
            'expires_at': self.expires_at,
            'created_at': self.created_at
        }

        # Don't include internal fields in API response
        # (deleted flag is internal only)

        # Serialize datetime fields to ISO 8601
        return serialize_model_dates(notif_dict)

    def to_db_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary for database storage.

        Returns:
            Dictionary with internal field names for MongoDB.
        """
        db_dict = {
            'notification_id': self.notification_id,
            'user_id': self.user_id,
            'type': self.type,
            'title': self.title,
            'body': self.body,
            'data': self.data,
            'is_read': self.is_read,
            'read_at': self.read_at,
            'expires_at': self.expires_at,
            'deleted': self.deleted,
            'created_at': self.created_at
        }

        if self._id:
            db_dict['_id'] = self._id

        return db_dict

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'UserNotification':
        """
        Create UserNotification from dictionary (database format).

        Args:
            data: Dictionary with notification data

        Returns:
            UserNotification instance
        """
        # Handle both old field names (for migration) and new field names
        is_read = data.get('is_read', data.get('read', False))

        return UserNotification(
            notification_id=data['notification_id'],
            user_id=data['user_id'],
            type=data['type'],
            title=data['title'],
            body=data['body'],
            data=data.get('data'),
            is_read=is_read,
            read_at=data.get('read_at'),
            expires_at=data.get('expires_at'),  # New field
            deleted=data.get('deleted', False),
            created_at=data.get('created_at'),
            _id=str(data['_id']) if '_id' in data else None
        )

    def __repr__(self) -> str:
        """String representation for logging"""
        return (
            f"<UserNotification id={self.notification_id} "
            f"user_id={self.user_id} type={self.type} is_read={self.is_read}>"
        )