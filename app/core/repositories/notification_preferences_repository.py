from typing import Optional
from datetime import datetime, timezone
from flask import current_app
from app import get_db
from app.core.models.notification_preferences import NotificationPreferences
from app.core.repositories.base_repository import BaseRepository
from app.core.utils.helpers import extract_user_id


class NotificationPreferencesRepository(BaseRepository):
    """Repository for notification preferences operations"""

    def __init__(self):
        super().__init__('notification_preferences')

    def create_indexes(self):
        """Create database indexes for notification preferences"""
        import os
        if self.collection is None or os.getenv('TESTING') == 'true':
            return

        try:
            # Unique index on user_id (one preferences document per user)
            self.collection.create_index('user_id', unique=True)

            current_app.logger.info("NotificationPreferences indexes created successfully")
        except Exception as e:
            current_app.logger.error(f"Error creating NotificationPreferences indexes: {str(e)}")

    def get_preferences(self, user_id: str) -> NotificationPreferences:
        """
        Get notification preferences for user.
        Creates default preferences if none exist.

        Args:
            user_id: User ID

        Returns:
            NotificationPreferences instance
        """
        try:
            user_id = extract_user_id(user_id)

            prefs_doc = self.collection.find_one({'user_id': user_id})

            if prefs_doc:
                return NotificationPreferences.from_dict(prefs_doc)
            else:
                # Create default preferences
                default_prefs = NotificationPreferences.get_default_preferences(user_id)
                self.create_preferences(default_prefs)
                return default_prefs

        except Exception as e:
            current_app.logger.error(f"Error getting preferences: {str(e)}", exc_info=True)
            # Return default preferences on error
            return NotificationPreferences.get_default_preferences(user_id)

    def create_preferences(self, preferences: NotificationPreferences) -> bool:
        """
        Create notification preferences.

        Args:
            preferences: NotificationPreferences instance

        Returns:
            True if successful, False otherwise
        """
        try:
            user_id = extract_user_id(preferences.user_id)

            prefs_dict = {
                'user_id': user_id,
                'push_enabled': preferences.push_enabled,
                'quiet_hours_enabled': preferences.quiet_hours_enabled,
                'quiet_hours_start': preferences.quiet_hours_start,
                'quiet_hours_end': preferences.quiet_hours_end,
                'timezone': preferences.timezone,
                'notification_types': preferences.notification_types,
                'updated_at': preferences.updated_at
            }

            self.collection.insert_one(prefs_dict)
            current_app.logger.info(f"Notification preferences created for user {user_id}")
            return True

        except Exception as e:
            current_app.logger.error(f"Error creating preferences: {str(e)}", exc_info=True)
            return False

    def update_preferences(self, preferences: NotificationPreferences) -> bool:
        """
        Update notification preferences.

        Args:
            preferences: NotificationPreferences instance

        Returns:
            True if successful, False otherwise
        """
        try:
            user_id = extract_user_id(preferences.user_id)

            # Update timestamp
            preferences.updated_at = datetime.now(timezone.utc)

            result = self.collection.update_one(
                {'user_id': user_id},
                {
                    '$set': {
                        'push_enabled': preferences.push_enabled,
                        'quiet_hours_enabled': preferences.quiet_hours_enabled,
                        'quiet_hours_start': preferences.quiet_hours_start,
                        'quiet_hours_end': preferences.quiet_hours_end,
                        'timezone': preferences.timezone,
                        'notification_types': preferences.notification_types,
                        'updated_at': preferences.updated_at
                    }
                },
                upsert=True  # Create if doesn't exist
            )

            current_app.logger.info(f"Notification preferences updated for user {user_id}")
            return True

        except Exception as e:
            current_app.logger.error(f"Error updating preferences: {str(e)}", exc_info=True)
            return False

    def reset_preferences(self, user_id: str) -> bool:
        """
        Reset preferences to defaults.

        Args:
            user_id: User ID

        Returns:
            True if successful, False otherwise
        """
        try:
            user_id = extract_user_id(user_id)

            default_prefs = NotificationPreferences.get_default_preferences(user_id)
            return self.update_preferences(default_prefs)

        except Exception as e:
            current_app.logger.error(f"Error resetting preferences: {str(e)}", exc_info=True)
            return False

    def delete_preferences(self, user_id: str) -> bool:
        """
        Delete preferences (e.g., on account deletion).

        Args:
            user_id: User ID

        Returns:
            True if deleted, False otherwise
        """
        try:
            user_id = extract_user_id(user_id)

            result = self.collection.delete_one({'user_id': user_id})
            return result.deleted_count > 0

        except Exception as e:
            current_app.logger.error(f"Error deleting preferences: {str(e)}", exc_info=True)
            return False
