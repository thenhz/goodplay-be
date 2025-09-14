from datetime import datetime, timezone
from typing import Optional, Dict, Tuple
from flask import current_app
from flask_jwt_extended import create_access_token, create_refresh_token
import re
from werkzeug.security import generate_password_hash

from app.core.models.user import User
from app.core.repositories.user_repository import UserRepository

class AuthService:
    def __init__(self):
        self.user_repository = UserRepository()
    
    def register_user(self, email: str, password: str, 
                     first_name: str = None, 
                     last_name: str = None) -> Tuple[bool, str, Optional[Dict]]:
        
        validation_error = self._validate_registration_data(email, password)
        if validation_error:
            return False, validation_error, None
        
        if self.user_repository.email_exists(email):
            return False, "Email already registered", None
        
        try:
            user = User(
                email=email,
                password_hash=generate_password_hash(password),
                first_name=first_name,
                last_name=last_name
            )
            
            user_id = self.user_repository.create_user(user)
            user._id = user_id
            
            tokens = self._generate_tokens(user)
            user_data = user.to_dict()
            
            current_app.logger.info(f"User registered: {email}")
            
            return True, "Registration completed successfully", {
                "user": user_data,
                "tokens": tokens
            }
            
        except Exception as e:
            current_app.logger.error(f"Registration error: {str(e)}")
            return False, "Error during registration", None
    
    def login_user(self, email: str, password: str) -> Tuple[bool, str, Optional[Dict]]:
        
        if not email or not password:
            return False, "Email and password are required", None
        
        user = self.user_repository.find_by_email(email)
        
        if not user or not user.check_password(password):
            return False, "Invalid credentials", None
        
        if not user.is_active:
            return False, "Account disabled", None
        
        try:
            tokens = self._generate_tokens(user)
            user_data = user.to_dict()
            
            current_app.logger.info(f"User logged in: {email}")
            
            return True, "Login successful", {
                "user": user_data,
                "tokens": tokens
            }
            
        except Exception as e:
            current_app.logger.error(f"Login error: {str(e)}")
            return False, "Error during login", None
    
    def refresh_token(self, user_id: str) -> Tuple[bool, str, Optional[Dict]]:
        user = self.user_repository.find_user_by_id(user_id)
        
        if not user or not user.is_active:
            return False, "User not found or disabled", None
        
        try:
            new_access_token = create_access_token(identity=user.get_id())
            
            return True, "Token refreshed successfully", {
                "access_token": new_access_token
            }
            
        except Exception as e:
            current_app.logger.error(f"Token refresh error: {str(e)}")
            return False, "Error refreshing token", None
    
    def get_user_profile(self, user_id: str) -> Tuple[bool, str, Optional[Dict]]:
        user = self.user_repository.find_user_by_id(user_id)
        
        if not user:
            return False, "User not found", None
        
        return True, "Profile retrieved successfully", {
            "user": user.to_dict()
        }
    
    def _generate_tokens(self, user: User) -> Dict[str, str]:
        access_token = create_access_token(identity=user.get_id())
        refresh_token = create_refresh_token(identity=user.get_id())
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer"
        }
    
    def _validate_registration_data(self, email: str, password: str) -> Optional[str]:
        
        if not email or not password:
            return "Email and password are required"
        
        if not self._is_valid_email(email):
            return "Invalid email format"
        
        if len(password) < 6:
            return "Password must be at least 6 characters long"
        
        return None
    
    def _is_valid_email(self, email: str) -> bool:
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(email_pattern, email) is not None

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