from typing import Optional
from pymongo import ASCENDING
from bson import ObjectId
from app.core.repositories.base_repository import BaseRepository
from app.preferences.models.user_preferences import UserPreferences

class PreferencesRepository(BaseRepository):
    def __init__(self):
        super().__init__('user_preferences')

    def create_indexes(self):
        if self.collection is not None:
            # Create unique index on user_id to ensure one preferences document per user
            self.collection.create_index([("user_id", ASCENDING)], unique=True)

    def find_by_user_id(self, user_id: str) -> Optional[UserPreferences]:
        """Find preferences by user ID"""
        if not ObjectId.is_valid(user_id):
            return None

        prefs_data = self.find_one({"user_id": ObjectId(user_id)})
        return UserPreferences.from_dict(prefs_data) if prefs_data else None

    def create_preferences(self, preferences: UserPreferences) -> str:
        """Create new preferences document"""
        prefs_data = preferences.to_dict()
        prefs_data.pop('_id', None)  # Remove _id to let MongoDB generate it

        # Convert user_id to ObjectId if it's a string
        if isinstance(prefs_data.get('user_id'), str):
            prefs_data['user_id'] = ObjectId(prefs_data['user_id'])

        return self.create(prefs_data)

    def update_preferences(self, user_id: str, preferences: UserPreferences) -> bool:
        """Update preferences by user ID"""
        if not ObjectId.is_valid(user_id):
            return False

        prefs_data = preferences.to_dict()
        prefs_data.pop('_id', None)  # Don't update _id
        prefs_data.pop('user_id', None)  # Don't update user_id
        prefs_data.pop('created_at', None)  # Don't update created_at

        result = self.collection.update_one(
            {"user_id": ObjectId(user_id)},
            {"$set": prefs_data}
        )
        return result.modified_count > 0

    def update_category(self, user_id: str, category: str, category_preferences: dict) -> bool:
        """Update a specific category of preferences"""
        if not ObjectId.is_valid(user_id):
            return False

        # Build update document with category prefix
        update_data = {
            "updated_at": self._get_current_time()
        }

        for key, value in category_preferences.items():
            update_data[f"{category}.{key}"] = value

        result = self.collection.update_one(
            {"user_id": ObjectId(user_id)},
            {"$set": update_data}
        )
        return result.modified_count > 0

    def create_default_preferences(self, user_id: str) -> str:
        """Create default preferences for a new user"""
        if not ObjectId.is_valid(user_id):
            return None

        # Check if preferences already exist
        existing = self.find_by_user_id(user_id)
        if existing:
            return str(existing._id)

        # Create default preferences
        default_prefs = UserPreferences.get_default_preferences()
        preferences = UserPreferences(
            user_id=ObjectId(user_id),
            gaming=default_prefs['gaming'],
            notifications=default_prefs['notifications'],
            privacy=default_prefs['privacy'],
            donations=default_prefs['donations']
        )

        return self.create_preferences(preferences)

    def reset_to_defaults(self, user_id: str) -> bool:
        """Reset user preferences to default values"""
        if not ObjectId.is_valid(user_id):
            return False

        default_prefs = UserPreferences.get_default_preferences()

        update_data = {
            "gaming": default_prefs['gaming'],
            "notifications": default_prefs['notifications'],
            "privacy": default_prefs['privacy'],
            "donations": default_prefs['donations'],
            "updated_at": self._get_current_time()
        }

        result = self.collection.update_one(
            {"user_id": ObjectId(user_id)},
            {"$set": update_data}
        )
        return result.modified_count > 0

    def delete_preferences(self, user_id: str) -> bool:
        """Delete preferences for a user (typically when user is deleted)"""
        if not ObjectId.is_valid(user_id):
            return False

        result = self.collection.delete_one({"user_id": ObjectId(user_id)})
        return result.deleted_count > 0

    def get_category_preferences(self, user_id: str, category: str) -> Optional[dict]:
        """Get preferences for a specific category"""
        if not ObjectId.is_valid(user_id):
            return None

        prefs_data = self.find_one(
            {"user_id": ObjectId(user_id)},
            {category: 1}  # Only return the specified category
        )

        if prefs_data and category in prefs_data:
            return prefs_data[category]
        return None

    def find_users_with_notification_preferences(self, notification_type: str, enabled: bool = True):
        """Find users who have specific notification preferences enabled"""
        filter_query = {f"notifications.{notification_type}": enabled}
        prefs_data = self.find_many(filter_query)
        return [UserPreferences.from_dict(pref) for pref in prefs_data]

    def find_users_by_donation_preferences(self, auto_donate_enabled: bool = True):
        """Find users with auto-donation enabled"""
        filter_query = {"donations.auto_donate_enabled": auto_donate_enabled}
        prefs_data = self.find_many(filter_query)
        return [UserPreferences.from_dict(pref) for pref in prefs_data]

    def get_privacy_settings(self, user_id: str) -> Optional[dict]:
        """Get only privacy settings for a user"""
        return self.get_category_preferences(user_id, "privacy")

    def bulk_update_notification_preferences(self, user_ids: list, notification_updates: dict) -> int:
        """Bulk update notification preferences for multiple users"""
        if not user_ids or not notification_updates:
            return 0

        # Convert string IDs to ObjectIds
        object_ids = []
        for user_id in user_ids:
            if ObjectId.is_valid(user_id):
                object_ids.append(ObjectId(user_id))

        if not object_ids:
            return 0

        # Build update document
        update_data = {"updated_at": self._get_current_time()}
        for key, value in notification_updates.items():
            update_data[f"notifications.{key}"] = value

        result = self.collection.update_many(
            {"user_id": {"$in": object_ids}},
            {"$set": update_data}
        )
        return result.modified_count