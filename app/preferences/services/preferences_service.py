from typing import Optional, Dict, Tuple, Any
from flask import current_app
from app.preferences.models.user_preferences import UserPreferences
from app.preferences.repositories.preferences_repository import PreferencesRepository

class PreferencesService:
    def __init__(self):
        self.preferences_repository = PreferencesRepository()

    def get_user_preferences(self, user_id: str) -> Tuple[bool, str, Optional[Dict]]:
        """Get user preferences, creating defaults if they don't exist"""
        try:
            preferences = self.preferences_repository.find_by_user_id(user_id)

            if not preferences:
                # Create default preferences for the user
                current_app.logger.info(f"Creating default preferences for user: {user_id}")
                prefs_id = self.preferences_repository.create_default_preferences(user_id)
                if prefs_id:
                    preferences = self.preferences_repository.find_by_user_id(user_id)

            if preferences:
                current_app.logger.info(f"Preferences retrieved for user: {user_id}")
                return True, "PREFERENCES_RETRIEVED_SUCCESS", {
                    "preferences": preferences.to_dict()
                }
            else:
                current_app.logger.error(f"Failed to create or retrieve preferences for user: {user_id}")
                return False, "PREFERENCES_RETRIEVAL_FAILED", None

        except Exception as e:
            current_app.logger.error(f"Error retrieving preferences: {str(e)}")
            return False, "INTERNAL_SERVER_ERROR", None

    def update_user_preferences(self, user_id: str, preferences_data: Dict[str, Any]) -> Tuple[bool, str, Optional[Dict]]:
        """Update user preferences with validation"""
        # Validate preferences data
        validation_error = UserPreferences.validate_preferences_data(preferences_data)
        if validation_error:
            current_app.logger.warning(f"Preferences validation failed for user {user_id}: {validation_error}")
            return False, validation_error, None

        try:
            # Get current preferences or create defaults
            current_preferences = self.preferences_repository.find_by_user_id(user_id)
            if not current_preferences:
                self.preferences_repository.create_default_preferences(user_id)
                current_preferences = self.preferences_repository.find_by_user_id(user_id)

            if not current_preferences:
                current_app.logger.error(f"Could not create preferences for user: {user_id}")
                return False, "PREFERENCES_CREATION_FAILED", None

            # Update preferences with new data
            for category, category_data in preferences_data.items():
                if hasattr(current_preferences, category) and isinstance(category_data, dict):
                    current_preferences.update_category(category, category_data)

            # Save updated preferences
            success = self.preferences_repository.update_preferences(user_id, current_preferences)

            if success:
                current_app.logger.info(f"Preferences updated for user: {user_id}")
                return True, "PREFERENCES_UPDATED_SUCCESS", {
                    "preferences": current_preferences.to_dict()
                }
            else:
                current_app.logger.error(f"Failed to update preferences for user: {user_id}")
                return False, "PREFERENCES_UPDATE_FAILED", None

        except Exception as e:
            current_app.logger.error(f"Error updating preferences: {str(e)}")
            return False, "INTERNAL_SERVER_ERROR", None

    def update_preferences_category(self, user_id: str, category: str, category_preferences: Dict[str, Any]) -> Tuple[bool, str, Optional[Dict]]:
        """Update a specific category of preferences"""
        # Validate category exists
        valid_categories = ['gaming', 'notifications', 'privacy', 'donations']
        if category not in valid_categories:
            return False, "PREFERENCES_CATEGORY_INVALID", None

        # Validate category data
        validation_data = {category: category_preferences}
        validation_error = UserPreferences.validate_preferences_data(validation_data)
        if validation_error:
            current_app.logger.warning(f"Category {category} validation failed for user {user_id}: {validation_error}")
            return False, validation_error, None

        try:
            # Ensure user has preferences
            current_preferences = self.preferences_repository.find_by_user_id(user_id)
            if not current_preferences:
                self.preferences_repository.create_default_preferences(user_id)

            # Update specific category
            success = self.preferences_repository.update_category(user_id, category, category_preferences)

            if success:
                # Get updated preferences
                updated_preferences = self.preferences_repository.find_by_user_id(user_id)
                current_app.logger.info(f"Category {category} updated for user: {user_id}")
                return True, "PREFERENCES_CATEGORY_UPDATED_SUCCESS", {
                    "preferences": updated_preferences.to_dict(),
                    "updated_category": category
                }
            else:
                current_app.logger.error(f"Failed to update category {category} for user: {user_id}")
                return False, "PREFERENCES_CATEGORY_UPDATE_FAILED", None

        except Exception as e:
            current_app.logger.error(f"Error updating preferences category {category}: {str(e)}")
            return False, "INTERNAL_SERVER_ERROR", None

    def reset_user_preferences(self, user_id: str) -> Tuple[bool, str, Optional[Dict]]:
        """Reset user preferences to default values"""
        try:
            success = self.preferences_repository.reset_to_defaults(user_id)

            if success:
                # Get the reset preferences
                preferences = self.preferences_repository.find_by_user_id(user_id)
                current_app.logger.info(f"Preferences reset to defaults for user: {user_id}")
                return True, "PREFERENCES_RESET_SUCCESS", {
                    "preferences": preferences.to_dict()
                }
            else:
                # Try to create default preferences if reset failed (user might not have preferences yet)
                prefs_id = self.preferences_repository.create_default_preferences(user_id)
                if prefs_id:
                    preferences = self.preferences_repository.find_by_user_id(user_id)
                    current_app.logger.info(f"Default preferences created for user: {user_id}")
                    return True, "PREFERENCES_RESET_SUCCESS", {
                        "preferences": preferences.to_dict()
                    }

                current_app.logger.error(f"Failed to reset preferences for user: {user_id}")
                return False, "PREFERENCES_RESET_FAILED", None

        except Exception as e:
            current_app.logger.error(f"Error resetting preferences: {str(e)}")
            return False, "INTERNAL_SERVER_ERROR", None

    def get_preferences_category(self, user_id: str, category: str) -> Tuple[bool, str, Optional[Dict]]:
        """Get preferences for a specific category"""
        # Validate category
        valid_categories = ['gaming', 'notifications', 'privacy', 'donations']
        if category not in valid_categories:
            return False, "PREFERENCES_CATEGORY_INVALID", None

        try:
            preferences = self.preferences_repository.find_by_user_id(user_id)

            if not preferences:
                # Create default preferences
                self.preferences_repository.create_default_preferences(user_id)
                preferences = self.preferences_repository.find_by_user_id(user_id)

            if preferences:
                category_data = preferences.get_category(category)
                current_app.logger.info(f"Category {category} retrieved for user: {user_id}")
                return True, "PREFERENCES_CATEGORY_RETRIEVED_SUCCESS", {
                    "category": category,
                    "preferences": category_data
                }
            else:
                current_app.logger.error(f"Could not retrieve category {category} for user: {user_id}")
                return False, "PREFERENCES_CATEGORY_RETRIEVAL_FAILED", None

        except Exception as e:
            current_app.logger.error(f"Error retrieving preferences category {category}: {str(e)}")
            return False, "INTERNAL_SERVER_ERROR", None

    def get_default_preferences(self) -> Tuple[bool, str, Optional[Dict]]:
        """Get default preferences template for new users"""
        try:
            default_prefs = UserPreferences.get_default_preferences()
            current_app.logger.info("Default preferences template retrieved")
            return True, "DEFAULT_PREFERENCES_RETRIEVED_SUCCESS", {
                "default_preferences": default_prefs
            }
        except Exception as e:
            current_app.logger.error(f"Error retrieving default preferences: {str(e)}")
            return False, "INTERNAL_SERVER_ERROR", None

    def delete_user_preferences(self, user_id: str) -> Tuple[bool, str, Optional[Dict]]:
        """Delete user preferences (used when user account is deleted)"""
        try:
            success = self.preferences_repository.delete_preferences(user_id)

            if success:
                current_app.logger.info(f"Preferences deleted for user: {user_id}")
                return True, "PREFERENCES_DELETED_SUCCESS", None
            else:
                current_app.logger.warning(f"No preferences found to delete for user: {user_id}")
                return True, "PREFERENCES_NOT_FOUND", None  # Not an error if preferences don't exist

        except Exception as e:
            current_app.logger.error(f"Error deleting preferences: {str(e)}")
            return False, "INTERNAL_SERVER_ERROR", None

    def get_notification_preferences(self, user_id: str) -> Tuple[bool, str, Optional[Dict]]:
        """Get notification preferences (helper method for external services)"""
        return self.get_preferences_category(user_id, 'notifications')

    def get_privacy_preferences(self, user_id: str) -> Tuple[bool, str, Optional[Dict]]:
        """Get privacy preferences (helper method for external services)"""
        return self.get_preferences_category(user_id, 'privacy')

    def bulk_update_notifications(self, user_ids: list, notification_updates: dict) -> Tuple[bool, str, Optional[Dict]]:
        """Bulk update notification preferences for multiple users"""
        if not user_ids or not notification_updates:
            return False, "PREFERENCES_BULK_UPDATE_INVALID_DATA", None

        try:
            # Validate notification updates
            validation_data = {'notifications': notification_updates}
            validation_error = UserPreferences.validate_preferences_data(validation_data)
            if validation_error:
                return False, validation_error, None

            updated_count = self.preferences_repository.bulk_update_notification_preferences(
                user_ids, notification_updates
            )

            current_app.logger.info(f"Bulk notification update completed: {updated_count} users updated")
            return True, "PREFERENCES_BULK_UPDATE_SUCCESS", {
                "updated_count": updated_count,
                "total_requested": len(user_ids)
            }

        except Exception as e:
            current_app.logger.error(f"Error in bulk notification update: {str(e)}")
            return False, "INTERNAL_SERVER_ERROR", None