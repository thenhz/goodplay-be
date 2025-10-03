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
            return False, "USER_NOT_FOUND", None

        return True, "PROFILE_RETRIEVED_SUCCESS", {
            "user": user.to_dict()
        }

    def update_user_profile(self, user_id: str, profile_data: Dict) -> Tuple[bool, str, Optional[Dict]]:
        """Update user profile including basic info and extended fields"""
        user = self.user_repository.find_user_by_id(user_id)

        if not user:
            return False, "USER_NOT_FOUND", None

        try:
            # Update basic fields
            if 'first_name' in profile_data:
                user.first_name = profile_data['first_name']
            if 'last_name' in profile_data:
                user.last_name = profile_data['last_name']

            # Update preferred language with validation
            if 'preferred_language' in profile_data:
                language_code = profile_data['preferred_language'].lower()
                if not User.validate_language_code(language_code):
                    return False, "INVALID_LANGUAGE_CODE", None
                user.preferred_language = language_code

            # Update extended fields using new methods
            if 'preferences' in profile_data:
                user.update_preferences(**profile_data['preferences'])
            if 'social_profile' in profile_data:
                user.update_social_profile(**profile_data['social_profile'])

            # Save to database
            success = self.user_repository.update_user(user_id, user)

            if success:
                current_app.logger.info(f"Profile updated for user: {user.email}")
                return True, "PROFILE_UPDATED_SUCCESS", {"user": user.to_dict()}
            else:
                return False, "UPDATE_FAILED", None

        except Exception as e:
            current_app.logger.error(f"Profile update error: {str(e)}")
            return False, "PROFILE_UPDATE_ERROR", None


    def update_social_profile(self, user_id: str, profile_data: Dict) -> Tuple[bool, str, Optional[Dict]]:
        """Update user social profile only (display_name and privacy_level)"""
        # Filter allowed fields
        allowed_fields = {'display_name', 'privacy_level'}
        filtered_data = {k: v for k, v in profile_data.items() if k in allowed_fields}

        if not filtered_data:
            return False, "NO_VALID_FIELDS_TO_UPDATE", None

        validation_error = self._validate_social_profile(filtered_data)
        if validation_error:
            return False, validation_error, None

        try:
            success = self.user_repository.update_social_profile(user_id, filtered_data)

            if success:
                user = self.user_repository.find_user_by_id(user_id)
                current_app.logger.info(f"Social profile updated for user: {user_id}")
                return True, "SOCIAL_PROFILE_UPDATED_SUCCESS", {"user": user.to_dict()}
            else:
                return False, "UPDATE_FAILED", None

        except Exception as e:
            current_app.logger.error(f"Social profile update error: {str(e)}")
            return False, "SOCIAL_PROFILE_UPDATE_ERROR", None

    def get_user_gaming_stats(self, user_id: str) -> Tuple[bool, str, Optional[Dict]]:
        """Get user gaming statistics"""
        user = self.user_repository.find_user_by_id(user_id)

        if not user:
            return False, "USER_NOT_FOUND", None

        return True, "GAMING_STATS_RETRIEVED_SUCCESS", {
            "gaming_stats": user.gaming_stats,
            "impact_score": user.impact_score
        }

    def get_user_wallet(self, user_id: str) -> Tuple[bool, str, Optional[Dict]]:
        """Get user wallet information"""
        user = self.user_repository.find_user_by_id(user_id)

        if not user:
            return False, "USER_NOT_FOUND", None

        return True, "WALLET_RETRIEVED_SUCCESS", {
            "wallet_credits": user.wallet_credits
        }

    def update_gaming_stats(self, user_id: str, play_time: int = 0, game_category: str = None) -> Tuple[bool, str, Optional[Dict]]:
        """Update user gaming statistics"""
        try:
            success = self.user_repository.update_gaming_stats(user_id, play_time, game_category)

            if success:
                user = self.user_repository.find_user_by_id(user_id)
                current_app.logger.info(f"Gaming stats updated for user: {user_id}")
                return True, "GAMING_STATS_UPDATED_SUCCESS", {"user": user.to_dict()}
            else:
                return False, "UPDATE_FAILED", None

        except Exception as e:
            current_app.logger.error(f"Gaming stats update error: {str(e)}")
            return False, "GAMING_STATS_UPDATE_ERROR", None

    def add_user_credits(self, user_id: str, amount: float, transaction_type: str = 'earned') -> Tuple[bool, str, Optional[Dict]]:
        """Add credits to user wallet"""
        if amount <= 0:
            return False, "AMOUNT_MUST_BE_POSITIVE", None

        try:
            success = self.user_repository.update_wallet_credits(user_id, amount, transaction_type)

            if success:
                user = self.user_repository.find_user_by_id(user_id)
                current_app.logger.info(f"Credits added to user: {user_id}, amount: {amount}")
                return True, "CREDITS_ADDED_SUCCESS", {"user": user.to_dict()}
            else:
                return False, "UPDATE_FAILED", None

        except Exception as e:
            current_app.logger.error(f"Add credits error: {str(e)}")
            return False, "CREDITS_ADD_ERROR", None

    def donate_user_credits(self, user_id: str, amount: float, onlus_id: str = None) -> Tuple[bool, str, Optional[Dict]]:
        """Donate user credits to ONLUS"""
        if amount <= 0:
            return False, "AMOUNT_MUST_BE_POSITIVE", None

        try:
            user = self.user_repository.find_user_by_id(user_id)

            if not user:
                return False, "USER_NOT_FOUND", None

            if user.wallet_credits['current_balance'] < amount:
                return False, "INSUFFICIENT_CREDITS", None

            # Deduct from current balance and update donated total
            balance_success = self.user_repository.update_wallet_credits(user_id, -amount, 'balance_only')
            donate_success = self.user_repository.update_wallet_credits(user_id, amount, 'donated')
            success = balance_success and donate_success

            if success:
                updated_user = self.user_repository.find_user_by_id(user_id)
                current_app.logger.info(f"Credits donated by user: {user_id}, amount: {amount}")
                return True, "DONATION_SUCCESS", {"user": updated_user.to_dict()}
            else:
                return False, "DONATION_FAILED", None

        except Exception as e:
            current_app.logger.error(f"Donation error: {str(e)}")
            return False, "DONATION_ERROR", None


    def _validate_social_profile(self, profile_data: Dict) -> Optional[str]:
        """Validate social profile data"""
        valid_privacy_levels = ['public', 'friends', 'private']

        if 'privacy_level' in profile_data:
            if profile_data['privacy_level'] not in valid_privacy_levels:
                return "INVALID_PRIVACY_LEVEL"

        if 'display_name' in profile_data:
            display_name = profile_data['display_name'].strip()
            if len(display_name) < 2 or len(display_name) > 50:
                return "DISPLAY_NAME_LENGTH_INVALID"

        return None