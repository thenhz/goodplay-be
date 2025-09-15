from typing import Optional, Dict, Any
from bson import ObjectId
from app.core.repositories.user_repository import UserRepository
from app.core.models.user import User

class PreferencesRepository:
    def __init__(self):
        self.user_repository = UserRepository()

    def create_indexes(self):
        """Create indexes for preferences - delegated to UserRepository"""
        self.user_repository.create_indexes()

    def find_by_user_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Find preferences by user ID - returns the preferences dict from User"""
        if not ObjectId.is_valid(user_id):
            return None

        user = self.user_repository.find_user_by_id(user_id)
        return user.preferences if user else None

    def get_user_preferences(self, user_id: str) -> Optional[User]:
        """Get full user object for preferences management"""
        return self.user_repository.find_user_by_id(user_id)

    def update_preferences(self, user_id: str, preferences_data: Dict[str, Any]) -> bool:
        """Update user preferences"""
        if not ObjectId.is_valid(user_id):
            return False

        user = self.user_repository.find_user_by_id(user_id)
        if not user:
            return False

        # Update preferences in user object
        for category, category_data in preferences_data.items():
            if category in user.preferences and isinstance(category_data, dict):
                user.update_preferences_category(category, category_data)

        # Save updated user
        return self.user_repository.update_user(user_id, user)

    def update_category(self, user_id: str, category: str, category_preferences: Dict[str, Any]) -> bool:
        """Update a specific category of preferences"""
        if not ObjectId.is_valid(user_id):
            return False

        user = self.user_repository.find_user_by_id(user_id)
        if not user:
            return False

        # Update specific category
        if user.update_preferences_category(category, category_preferences):
            return self.user_repository.update_user(user_id, user)

        return False

    def create_default_preferences(self, user_id: str) -> bool:
        """Ensure user has default preferences (they should already exist from User model)"""
        if not ObjectId.is_valid(user_id):
            return False

        user = self.user_repository.find_user_by_id(user_id)
        if not user:
            return False

        # Check if user already has comprehensive preferences
        if ('gaming' in user.preferences and 'notifications' in user.preferences and
            'privacy' in user.preferences and 'donations' in user.preferences):
            return True  # Already has full preferences

        # Reset to comprehensive defaults
        user.reset_preferences_to_defaults()
        return self.user_repository.update_user(user_id, user)

    def reset_to_defaults(self, user_id: str) -> bool:
        """Reset user preferences to default values"""
        if not ObjectId.is_valid(user_id):
            return False

        user = self.user_repository.find_user_by_id(user_id)
        if not user:
            return False

        user.reset_preferences_to_defaults()
        return self.user_repository.update_user(user_id, user)

    def delete_preferences(self, user_id: str) -> bool:
        """Reset preferences to defaults (can't actually delete from user)"""
        return self.reset_to_defaults(user_id)

    def get_category_preferences(self, user_id: str, category: str) -> Optional[Dict[str, Any]]:
        """Get preferences for a specific category"""
        if not ObjectId.is_valid(user_id):
            return None

        user = self.user_repository.find_user_by_id(user_id)
        if not user:
            return None

        return user.get_preferences_category(category)

    def find_users_with_notification_preferences(self, notification_type: str, enabled: bool = True):
        """Find users who have specific notification preferences enabled"""
        # This would require aggregation queries on the users collection
        # For now, return empty list - can be implemented later if needed
        return []

    def find_users_by_donation_preferences(self, auto_donate_enabled: bool = True):
        """Find users with auto-donation enabled"""
        # This would require aggregation queries on the users collection
        # For now, return empty list - can be implemented later if needed
        return []

    def get_privacy_settings(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get only privacy settings for a user"""
        return self.get_category_preferences(user_id, "privacy")

    def bulk_update_notification_preferences(self, user_ids: list, notification_updates: Dict[str, Any]) -> int:
        """Bulk update notification preferences for multiple users"""
        if not user_ids or not notification_updates:
            return 0

        updated_count = 0
        for user_id in user_ids:
            if self.update_category(user_id, 'notifications', notification_updates):
                updated_count += 1

        return updated_count