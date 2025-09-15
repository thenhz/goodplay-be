from typing import Optional, Dict, Tuple, Any
from flask import current_app
from app.core.models.user import User
from app.preferences.repositories.preferences_repository import PreferencesRepository

class PreferencesService:
    def __init__(self):
        self.preferences_repository = PreferencesRepository()

    def get_user_preferences(self, user_id: str) -> Tuple[bool, str, Optional[Dict]]:
        """Get user preferences, ensuring defaults exist"""
        try:
            user = self.preferences_repository.get_user_preferences(user_id)

            if not user:
                current_app.logger.error(f"User not found: {user_id}")
                return False, "USER_NOT_FOUND", None

            # Ensure user has comprehensive preferences
            if not self._has_comprehensive_preferences(user.preferences):
                current_app.logger.info(f"Upgrading preferences to comprehensive structure for user: {user_id}")
                self.preferences_repository.create_default_preferences(user_id)
                # Re-fetch user with updated preferences
                user = self.preferences_repository.get_user_preferences(user_id)

            if user:
                current_app.logger.info(f"Preferences retrieved for user: {user_id}")
                return True, "PREFERENCES_RETRIEVED_SUCCESS", {
                    "preferences": user.preferences
                }
            else:
                current_app.logger.error(f"Failed to retrieve preferences for user: {user_id}")
                return False, "PREFERENCES_RETRIEVAL_FAILED", None

        except Exception as e:
            current_app.logger.error(f"Error retrieving preferences: {str(e)}")
            return False, "INTERNAL_SERVER_ERROR", None

    def _has_comprehensive_preferences(self, preferences: dict) -> bool:
        """Check if user has comprehensive preferences structure"""
        required_categories = ['gaming', 'notifications', 'privacy', 'donations']
        return all(category in preferences for category in required_categories)

    def update_user_preferences(self, user_id: str, preferences_data: Dict[str, Any]) -> Tuple[bool, str, Optional[Dict]]:
        """Update user preferences with validation"""
        # Validate preferences data using User model validation
        validation_error = User.validate_preferences_data(preferences_data)
        if validation_error:
            current_app.logger.warning(f"Preferences validation failed for user {user_id}: {validation_error}")
            return False, validation_error, None

        try:
            # Get current user
            user = self.preferences_repository.get_user_preferences(user_id)
            if not user:
                current_app.logger.error(f"User not found: {user_id}")
                return False, "USER_NOT_FOUND", None

            # Ensure user has comprehensive preferences structure
            if not self._has_comprehensive_preferences(user.preferences):
                self.preferences_repository.create_default_preferences(user_id)
                user = self.preferences_repository.get_user_preferences(user_id)

            # Save updated preferences
            success = self.preferences_repository.update_preferences(user_id, preferences_data)

            if success:
                # Re-fetch user to get updated preferences
                updated_user = self.preferences_repository.get_user_preferences(user_id)
                current_app.logger.info(f"Preferences updated for user: {user_id}")
                return True, "PREFERENCES_UPDATED_SUCCESS", {
                    "preferences": updated_user.preferences
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

        # Validate category data using User model validation
        validation_data = {category: category_preferences}
        validation_error = User.validate_preferences_data(validation_data)
        if validation_error:
            current_app.logger.warning(f"Category {category} validation failed for user {user_id}: {validation_error}")
            return False, validation_error, None

        try:
            # Ensure user exists and has comprehensive preferences
            user = self.preferences_repository.get_user_preferences(user_id)
            if not user:
                current_app.logger.error(f"User not found: {user_id}")
                return False, "USER_NOT_FOUND", None

            if not self._has_comprehensive_preferences(user.preferences):
                self.preferences_repository.create_default_preferences(user_id)

            # Update specific category
            success = self.preferences_repository.update_category(user_id, category, category_preferences)

            if success:
                # Get updated user
                updated_user = self.preferences_repository.get_user_preferences(user_id)
                current_app.logger.info(f"Category {category} updated for user: {user_id}")
                return True, "PREFERENCES_CATEGORY_UPDATED_SUCCESS", {
                    "preferences": updated_user.preferences,
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
                user = self.preferences_repository.get_user_preferences(user_id)
                if user:
                    current_app.logger.info(f"Preferences reset to defaults for user: {user_id}")
                    return True, "PREFERENCES_RESET_SUCCESS", {
                        "preferences": user.preferences
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
            category_data = self.preferences_repository.get_category_preferences(user_id, category)

            if category_data is not None:
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
            # Create a temporary user instance to get default preferences structure
            temp_user = User(email="temp@example.com")
            default_prefs = temp_user.preferences
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