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

