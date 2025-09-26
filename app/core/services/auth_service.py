from typing import Optional, Dict, Tuple
from flask import current_app
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity
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
            return False, "EMAIL_ALREADY_REGISTERED", None
        
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
            
            return True, "USER_REGISTRATION_SUCCESS", {
                "user": user_data,
                "tokens": tokens
            }
            
        except Exception as e:
            current_app.logger.error(f"Registration error: {str(e)}")
            return False, "INTERNAL_SERVER_ERROR", None
    
    def login_user(self, email: str, password: str) -> Tuple[bool, str, Optional[Dict]]:
        
        if not email or not password:
            return False, "CREDENTIALS_REQUIRED", None
        
        user = self.user_repository.find_by_email(email)
        
        if not user or not user.check_password(password):
            return False, "INVALID_CREDENTIALS", None
        
        if not user.is_active:
            return False, "ACCOUNT_DISABLED", None
        
        try:
            tokens = self._generate_tokens(user)
            user_data = user.to_dict()
            
            current_app.logger.info(f"User logged in: {email}")
            
            return True, "USER_LOGIN_SUCCESS", {
                "user": user_data,
                "tokens": tokens
            }
            
        except Exception as e:
            current_app.logger.error(f"Login error: {str(e)}")
            return False, "INTERNAL_SERVER_ERROR", None
    
    def refresh_token(self, user_id: str) -> Tuple[bool, str, Optional[Dict]]:
        user = self.user_repository.find_user_by_id(user_id)
        
        if not user or not user.is_active:
            return False, "USER_NOT_FOUND", None
        
        try:
            new_access_token = create_access_token(identity=user.get_id())
            
            return True, "TOKEN_REFRESH_SUCCESS", {
                "access_token": new_access_token
            }
            
        except Exception as e:
            current_app.logger.error(f"Token refresh error: {str(e)}")
            return False, "INTERNAL_SERVER_ERROR", None
    
    def get_user_profile(self, user_id: str) -> Tuple[bool, str, Optional[Dict]]:
        user = self.user_repository.find_user_by_id(user_id)
        
        if not user:
            return False, "USER_NOT_FOUND", None
        
        return True, "PROFILE_RETRIEVED_SUCCESS", {
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
            return "CREDENTIALS_REQUIRED"
        
        if not self._is_valid_email(email):
            return "INVALID_EMAIL_FORMAT"
        
        if len(password) < 6:
            return "PASSWORD_TOO_WEAK"
        
        return None
    
    def _is_valid_email(self, email: str) -> bool:
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(email_pattern, email) is not None

    def change_password(self, user_id: str, current_password: str, new_password: str) -> Tuple[bool, str, Optional[Dict]]:
        """Change user password with current password verification"""
        if not current_password or not new_password:
            return False, "CREDENTIALS_REQUIRED", None

        if len(new_password) < 6:
            return False, "NEW_PASSWORD_TOO_WEAK", None

        try:
            user = self.user_repository.find_user_by_id(user_id)
            if not user:
                return False, "USER_NOT_FOUND", None

            # Verify current password
            if not user.check_password(current_password):
                return False, "CURRENT_PASSWORD_INCORRECT", None

            # Update password
            new_password_hash = generate_password_hash(new_password)
            success = self.user_repository.update_password(user_id, new_password_hash)

            if success:
                current_app.logger.info(f"Password changed for user: {user_id}")
                return True, "PASSWORD_CHANGED_SUCCESS", None
            else:
                return False, "PASSWORD_CHANGE_FAILED", None

        except Exception as e:
            current_app.logger.error(f"Password change error: {str(e)}")
            return False, "INTERNAL_SERVER_ERROR", None

    def validate_token(self, user_id: str = None) -> Tuple[bool, str, Optional[Dict]]:
        """Validate current JWT token"""
        try:
            if user_id is None:
                user_id = get_jwt_identity()

            if not user_id:
                return False, "TOKEN_INVALID", None

            user = self.user_repository.find_user_by_id(user_id)
            if not user or not user.is_active:
                return False, "TOKEN_INVALID", None

            return True, "TOKEN_VALID", {
                "user_id": str(user.get_id()),
                "email": user.email
            }

        except Exception as e:
            current_app.logger.error(f"Token validation error: {str(e)}")
            return False, "TOKEN_INVALID", None

    def delete_account(self, user_id: str) -> Tuple[bool, str, Optional[Dict]]:
        """Delete user account"""
        try:
            user = self.user_repository.find_user_by_id(user_id)
            if not user:
                return False, "USER_NOT_FOUND", None

            # For security, we might want to deactivate instead of delete
            # Or implement proper cascading delete for user data
            success = self.user_repository.delete_user(user_id)

            if success:
                current_app.logger.info(f"Account deleted for user: {user_id}")
                return True, "ACCOUNT_DELETED_SUCCESS", None
            else:
                return False, "ACCOUNT_DELETION_FAILED", None

        except Exception as e:
            current_app.logger.error(f"Account deletion error: {str(e)}")
            return False, "INTERNAL_SERVER_ERROR", None

