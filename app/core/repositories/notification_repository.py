from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from flask import current_app
from app import get_db
from app.core.models.user_notification import UserNotification
from app.core.repositories.base_repository import BaseRepository
from app.core.utils.helpers import extract_user_id


class NotificationRepository(BaseRepository):
    """Repository for user notification operations"""

    def __init__(self):
        super().__init__('user_notifications')

    def create_indexes(self):
        """Create database indexes for notifications"""
        import os
        if self.collection is None or os.getenv('TESTING') == 'true':
            return

        try:
            # Unique index on notification_id
            self.collection.create_index('notification_id', unique=True)

            # Index for querying user notifications
            self.collection.create_index('user_id')

            # Compound index for user + read status (updated to is_read)
            self.collection.create_index([('user_id', 1), ('is_read', 1)])

            # Compound index for user + deleted status
            self.collection.create_index([('user_id', 1), ('deleted', 1)])

            # Compound index for user + type
            self.collection.create_index([('user_id', 1), ('type', 1)])

            # Index for created_at (for sorting and cleanup)
            self.collection.create_index([('created_at', -1)])

            # Index for expires_at (for cleanup of expired notifications)
            self.collection.create_index('expires_at')

            # Compound index for efficient inbox queries
            self.collection.create_index([
                ('user_id', 1),
                ('deleted', 1),
                ('created_at', -1)
            ])

            current_app.logger.info("UserNotification indexes created successfully")
        except Exception as e:
            current_app.logger.error(f"Error creating UserNotification indexes: {str(e)}")

    def create_notification(self, notification: UserNotification) -> bool:
        """
        Create notification in database.

        Args:
            notification: UserNotification instance

        Returns:
            True if successful, False otherwise
        """
        try:
            user_id = extract_user_id(notification.user_id)
            notification.user_id = user_id  # Ensure user_id is a string

            # Use to_db_dict for database storage
            notif_dict = notification.to_db_dict()

            self.collection.insert_one(notif_dict)
            current_app.logger.info(
                f"Notification {notification.notification_id} created for user {user_id}"
            )
            return True

        except Exception as e:
            current_app.logger.error(f"Error creating notification: {str(e)}", exc_info=True)
            return False

    def get_notification(self, notification_id: str, user_id: str = None) -> Optional[UserNotification]:
        """
        Get notification by ID, optionally filtered by user_id for security.

        Args:
            notification_id: Notification ID
            user_id: User ID (optional, for authorization check)

        Returns:
            UserNotification instance or None
        """
        try:
            query = {'notification_id': notification_id}

            # Add user_id filter if provided (for authorization)
            if user_id:
                query['user_id'] = extract_user_id(user_id)

            notif_doc = self.collection.find_one(query)
            if notif_doc:
                return UserNotification.from_dict(notif_doc)
            return None
        except Exception as e:
            current_app.logger.error(f"Error getting notification: {str(e)}", exc_info=True)
            return None

    def get_user_notifications(
        self,
        user_id: str,
        read: Optional[bool] = None,
        type: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[UserNotification]:
        """
        Get notifications for a user with pagination and filters.

        Args:
            user_id: User ID
            read: Filter by read status (None = all)
            type: Filter by notification type (None = all)
            limit: Maximum number of notifications to return
            offset: Number of notifications to skip

        Returns:
            List of UserNotification instances
        """
        try:
            user_id = extract_user_id(user_id)

            # Build query
            query = {
                'user_id': user_id,
                'deleted': False
            }

            if read is not None:
                # Use is_read field (migration-friendly: also check old 'read' field)
                query['$or'] = [
                    {'is_read': read},
                    {'read': read}  # For backwards compatibility during migration
                ]

            if type is not None:
                query['type'] = type

            # Execute query with pagination
            notif_docs = self.collection.find(query).sort(
                'created_at', -1
            ).skip(offset).limit(limit)

            notifications = []
            for doc in notif_docs:
                notifications.append(UserNotification.from_dict(doc))

            return notifications

        except Exception as e:
            current_app.logger.error(f"Error getting user notifications: {str(e)}", exc_info=True)
            return []

    def count_user_notifications(
        self,
        user_id: str,
        read: Optional[bool] = None,
        type: Optional[str] = None
    ) -> int:
        """
        Count notifications for a user with filters.

        Args:
            user_id: User ID
            read: Filter by read status (None = all)
            type: Filter by notification type (None = all)

        Returns:
            Count of notifications matching filters
        """
        try:
            user_id = extract_user_id(user_id)

            # Build query
            query = {
                'user_id': user_id,
                'deleted': False
            }

            if read is not None:
                # Use is_read field (migration-friendly: also check old 'read' field)
                query['$or'] = [
                    {'is_read': read},
                    {'read': read}  # For backwards compatibility during migration
                ]

            if type is not None:
                query['type'] = type

            return self.collection.count_documents(query)

        except Exception as e:
            current_app.logger.error(f"Error counting user notifications: {str(e)}", exc_info=True)
            return 0

    def get_unread_count(self, user_id: str) -> int:
        """
        Get count of unread notifications for user.

        Args:
            user_id: User ID

        Returns:
            Count of unread notifications
        """
        try:
            user_id = extract_user_id(user_id)

            count = self.collection.count_documents({
                'user_id': user_id,
                '$or': [
                    {'is_read': False},
                    {'read': False}  # For backwards compatibility
                ],
                'deleted': False
            })

            return count

        except Exception as e:
            current_app.logger.error(f"Error counting unread notifications: {str(e)}", exc_info=True)
            return 0

    def mark_as_read(self, notification_id: str, user_id: str) -> bool:
        """
        Mark notification as read.

        Args:
            notification_id: Notification ID
            user_id: User ID (for authorization)

        Returns:
            True if successful, False otherwise
        """
        try:
            user_id = extract_user_id(user_id)

            result = self.collection.update_one(
                {
                    'notification_id': notification_id,
                    'user_id': user_id
                },
                {
                    '$set': {
                        'is_read': True,  # Use new field name
                        'read': True,  # Also set old field for compatibility
                        'read_at': datetime.now(timezone.utc)
                    }
                }
            )

            return result.modified_count > 0

        except Exception as e:
            current_app.logger.error(f"Error marking notification as read: {str(e)}", exc_info=True)
            return False

    def mark_all_as_read(self, user_id: str) -> int:
        """
        Mark all unread notifications as read for user.

        Args:
            user_id: User ID

        Returns:
            Number of notifications marked as read
        """
        try:
            user_id = extract_user_id(user_id)

            result = self.collection.update_many(
                {
                    'user_id': user_id,
                    '$or': [
                        {'is_read': False},
                        {'read': False}  # For backwards compatibility
                    ],
                    'deleted': False
                },
                {
                    '$set': {
                        'is_read': True,  # Use new field name
                        'read': True,  # Also set old field for compatibility
                        'read_at': datetime.now(timezone.utc)
                    }
                }
            )

            if result.modified_count > 0:
                current_app.logger.info(
                    f"Marked {result.modified_count} notifications as read for user {user_id}"
                )

            return result.modified_count

        except Exception as e:
            current_app.logger.error(f"Error marking all as read: {str(e)}", exc_info=True)
            return 0

    def delete_notification(self, notification_id: str, user_id: str) -> bool:
        """
        Soft delete notification.

        Args:
            notification_id: Notification ID
            user_id: User ID (for authorization)

        Returns:
            True if successful, False otherwise
        """
        try:
            user_id = extract_user_id(user_id)

            result = self.collection.update_one(
                {
                    'notification_id': notification_id,
                    'user_id': user_id
                },
                {
                    '$set': {'deleted': True}
                }
            )

            return result.modified_count > 0

        except Exception as e:
            current_app.logger.error(f"Error deleting notification: {str(e)}", exc_info=True)
            return False

    def clear_all_notifications(self, user_id: str) -> int:
        """
        Soft delete all notifications for user.

        Args:
            user_id: User ID

        Returns:
            Number of notifications deleted
        """
        try:
            user_id = extract_user_id(user_id)

            result = self.collection.update_many(
                {
                    'user_id': user_id,
                    'deleted': False
                },
                {
                    '$set': {'deleted': True}
                }
            )

            if result.modified_count > 0:
                current_app.logger.info(
                    f"Cleared {result.modified_count} notifications for user {user_id}"
                )

            return result.modified_count

        except Exception as e:
            current_app.logger.error(f"Error clearing notifications: {str(e)}", exc_info=True)
            return 0

    def cleanup_expired_notifications(self) -> int:
        """
        Delete notifications that have expired.

        Returns:
            Number of notifications deleted
        """
        try:
            now = datetime.now(timezone.utc)

            # Soft delete expired notifications
            result = self.collection.update_many(
                {
                    'expires_at': {'$lt': now},
                    'deleted': False
                },
                {
                    '$set': {'deleted': True}
                }
            )

            if result.modified_count > 0:
                current_app.logger.info(
                    f"Marked {result.modified_count} expired notifications as deleted"
                )

            return result.modified_count

        except Exception as e:
            current_app.logger.error(f"Error cleaning up expired notifications: {str(e)}", exc_info=True)
            return 0

    def cleanup_old_notifications(self, days: int = 90) -> int:
        """
        Permanently delete notifications older than specified days.

        Args:
            days: Age threshold in days

        Returns:
            Number of notifications deleted
        """
        try:
            threshold_date = datetime.now(timezone.utc) - timedelta(days=days)

            result = self.collection.delete_many({
                'created_at': {'$lt': threshold_date},
                'deleted': True  # Only delete already soft-deleted items
            })

            if result.deleted_count > 0:
                current_app.logger.info(
                    f"Cleaned up {result.deleted_count} old notifications (>{days} days)"
                )

            return result.deleted_count

        except Exception as e:
            current_app.logger.error(f"Error cleaning up old notifications: {str(e)}", exc_info=True)
            return 0

    def get_notification_statistics(self, user_id: str) -> Dict[str, Any]:
        """
        Get notification statistics for user.

        Args:
            user_id: User ID

        Returns:
            Dictionary with statistics
        """
        try:
            user_id = extract_user_id(user_id)

            total = self.collection.count_documents({
                'user_id': user_id,
                'deleted': False
            })

            unread = self.collection.count_documents({
                'user_id': user_id,
                '$or': [
                    {'is_read': False},
                    {'read': False}  # For backwards compatibility
                ],
                'deleted': False
            })

            # Count by type
            pipeline = [
                {
                    '$match': {
                        'user_id': user_id,
                        'deleted': False
                    }
                },
                {
                    '$group': {
                        '_id': '$type',
                        'count': {'$sum': 1}
                    }
                }
            ]

            type_counts = {}
            for result in self.collection.aggregate(pipeline):
                type_counts[result['_id']] = result['count']

            return {
                'total_notifications': total,
                'unread_notifications': unread,
                'read_notifications': total - unread,
                'by_type': type_counts
            }

        except Exception as e:
            current_app.logger.error(f"Error getting notification statistics: {str(e)}", exc_info=True)
            return {
                'total_notifications': 0,
                'unread_notifications': 0,
                'read_notifications': 0,
                'by_type': {}
            }