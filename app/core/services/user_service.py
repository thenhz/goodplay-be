from datetime import datetime, timezone
from typing import Optional, Dict, Tuple
from flask import current_app

from app.core.models.user import User
from app.core.repositories.user_repository import UserRepository

class UserService:
    def __init__(self):
        self.user_repository = UserRepository()

    def get_user_profile(self, user_id: str) -> Tuple[bool, str, Optional[Dict]]:
        user = self.user_repository.find_user_by_id(user_id)

        if not user:
            return False, "User not found", None

        return True, "Profile retrieved successfully", {
            "user": user.to_dict()
        }

    def update_user_profile(self, user_id: str, profile_data: Dict) -> Tuple[bool, str, Optional[Dict]]:
        """Update user profile including basic info and extended fields"""
        user = self.user_repository.find_user_by_id(user_id)

        if not user:
            return False, "User not found", None

        try:
            # Update basic fields
            if 'first_name' in profile_data:
                user.first_name = profile_data['first_name']
            if 'last_name' in profile_data:
                user.last_name = profile_data['last_name']

            # Update extended fields using new methods
            if 'preferences' in profile_data:
                user.update_preferences(**profile_data['preferences'])
            if 'social_profile' in profile_data:
                user.update_social_profile(**profile_data['social_profile'])

            # Save to database
            success = self.user_repository.update_user(user_id, user)

            if success:
                current_app.logger.info(f"Profile updated for user: {user.email}")
                return True, "Profile updated successfully", {"user": user.to_dict()}
            else:
                return False, "Failed to update profile", None

        except Exception as e:
            current_app.logger.error(f"Profile update error: {str(e)}")
            return False, "Error updating profile", None

    def update_user_preferences(self, user_id: str, preferences: Dict) -> Tuple[bool, str, Optional[Dict]]:
        """Update user preferences only"""
        validation_error = self._validate_preferences(preferences)
        if validation_error:
            return False, validation_error, None

        try:
            success = self.user_repository.update_preferences(user_id, preferences)

            if success:
                user = self.user_repository.find_user_by_id(user_id)
                current_app.logger.info(f"Preferences updated for user: {user_id}")
                return True, "Preferences updated successfully", {"user": user.to_dict()}
            else:
                return False, "User not found or update failed", None

        except Exception as e:
            current_app.logger.error(f"Preferences update error: {str(e)}")
            return False, "Error updating preferences", None

    def update_social_profile(self, user_id: str, profile_data: Dict) -> Tuple[bool, str, Optional[Dict]]:
        """Update user social profile only"""
        validation_error = self._validate_social_profile(profile_data)
        if validation_error:
            return False, validation_error, None

        try:
            success = self.user_repository.update_social_profile(user_id, profile_data)

            if success:
                user = self.user_repository.find_user_by_id(user_id)
                current_app.logger.info(f"Social profile updated for user: {user_id}")
                return True, "Social profile updated successfully", {"user": user.to_dict()}
            else:
                return False, "User not found or update failed", None

        except Exception as e:
            current_app.logger.error(f"Social profile update error: {str(e)}")
            return False, "Error updating social profile", None

    def get_user_gaming_stats(self, user_id: str) -> Tuple[bool, str, Optional[Dict]]:
        """Get user gaming statistics"""
        user = self.user_repository.find_user_by_id(user_id)

        if not user:
            return False, "User not found", None

        return True, "Gaming stats retrieved successfully", {
            "gaming_stats": user.gaming_stats,
            "impact_score": user.impact_score
        }

    def get_user_wallet(self, user_id: str) -> Tuple[bool, str, Optional[Dict]]:
        """Get user wallet information"""
        user = self.user_repository.find_user_by_id(user_id)

        if not user:
            return False, "User not found", None

        return True, "Wallet information retrieved successfully", {
            "wallet_credits": user.wallet_credits
        }

    def update_gaming_stats(self, user_id: str, play_time: int = 0, game_category: str = None) -> Tuple[bool, str, Optional[Dict]]:
        """Update user gaming statistics"""
        try:
            success = self.user_repository.update_gaming_stats(user_id, play_time, game_category)

            if success:
                user = self.user_repository.find_user_by_id(user_id)
                current_app.logger.info(f"Gaming stats updated for user: {user_id}")
                return True, "Gaming stats updated successfully", {"user": user.to_dict()}
            else:
                return False, "User not found or update failed", None

        except Exception as e:
            current_app.logger.error(f"Gaming stats update error: {str(e)}")
            return False, "Error updating gaming stats", None

    def add_user_credits(self, user_id: str, amount: float, transaction_type: str = 'earned') -> Tuple[bool, str, Optional[Dict]]:
        """Add credits to user wallet"""
        if amount <= 0:
            return False, "Amount must be positive", None

        try:
            success = self.user_repository.update_wallet_credits(user_id, amount, transaction_type)

            if success:
                user = self.user_repository.find_user_by_id(user_id)
                current_app.logger.info(f"Credits added to user: {user_id}, amount: {amount}")
                return True, f"Credits added successfully", {"user": user.to_dict()}
            else:
                return False, "User not found or update failed", None

        except Exception as e:
            current_app.logger.error(f"Add credits error: {str(e)}")
            return False, "Error adding credits", None

    def donate_user_credits(self, user_id: str, amount: float, onlus_id: str = None) -> Tuple[bool, str, Optional[Dict]]:
        """Donate user credits to ONLUS"""
        if amount <= 0:
            return False, "Amount must be positive", None

        try:
            user = self.user_repository.find_user_by_id(user_id)

            if not user:
                return False, "User not found", None

            if user.wallet_credits['current_balance'] < amount:
                return False, "Insufficient credits", None

            # Deduct from current balance and update donated total
            balance_success = self.user_repository.update_wallet_credits(user_id, -amount, 'balance_only')
            donate_success = self.user_repository.update_wallet_credits(user_id, amount, 'donated')
            success = balance_success and donate_success

            if success:
                updated_user = self.user_repository.find_user_by_id(user_id)
                current_app.logger.info(f"Credits donated by user: {user_id}, amount: {amount}")
                return True, "Donation successful", {"user": updated_user.to_dict()}
            else:
                return False, "Donation failed", None

        except Exception as e:
            current_app.logger.error(f"Donation error: {str(e)}")
            return False, "Error processing donation", None

    def _validate_preferences(self, preferences: Dict) -> Optional[str]:
        """Validate preferences data"""
        valid_frequencies = ['daily', 'weekly', 'monthly', 'never']

        if 'donation_frequency' in preferences:
            if preferences['donation_frequency'] not in valid_frequencies:
                return f"Invalid donation frequency. Must be one of: {', '.join(valid_frequencies)}"

        if 'notification_enabled' in preferences:
            if not isinstance(preferences['notification_enabled'], bool):
                return "notification_enabled must be a boolean"

        if 'preferred_game_categories' in preferences:
            if not isinstance(preferences['preferred_game_categories'], list):
                return "preferred_game_categories must be a list"

        return None

    def _validate_social_profile(self, profile_data: Dict) -> Optional[str]:
        """Validate social profile data"""
        valid_privacy_levels = ['public', 'friends', 'private']

        if 'privacy_level' in profile_data:
            if profile_data['privacy_level'] not in valid_privacy_levels:
                return f"Invalid privacy level. Must be one of: {', '.join(valid_privacy_levels)}"

        if 'display_name' in profile_data:
            display_name = profile_data['display_name'].strip()
            if len(display_name) < 2 or len(display_name) > 50:
                return "Display name must be between 2 and 50 characters"

        return None