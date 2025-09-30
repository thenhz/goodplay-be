from typing import Optional, Dict, Tuple, List
from flask import current_app
from flask_jwt_extended import create_access_token, create_refresh_token
from datetime import datetime, timezone, timedelta
import secrets
import hashlib

from app.admin.models.admin_user import AdminUser
from app.admin.models.admin_action import AdminAction, ActionType, TargetType
from app.admin.repositories.admin_repository import AdminRepository
from app.admin.repositories.audit_repository import AuditRepository

class AdminService:
    def __init__(self):
        self.admin_repository = AdminRepository()
        self.audit_repository = AuditRepository()

    def create_admin(self, username: str, email: str, password: str, role: str,
                    created_by_admin_id: str, ip_address: str = None) -> Tuple[bool, str, Optional[Dict]]:
        """Create a new admin user"""
        try:
            # Validate input data
            validation_error = self._validate_admin_data(username, email, password, role)
            if validation_error:
                return False, validation_error, None

            # Check if username or email already exists
            if self.admin_repository.find_by_username(username):
                return False, "ADMIN_USERNAME_EXISTS", None

            if self.admin_repository.find_by_email(email):
                return False, "ADMIN_EMAIL_EXISTS", None

            # Create admin user
            admin_user = AdminUser(
                username=username,
                email=email,
                role=role,
                created_by=created_by_admin_id
            )
            admin_user.set_password(password)

            admin_id = self.admin_repository.create_admin(admin_user)
            admin_user._id = admin_id

            # Log the action
            action = AdminAction.create_user_action(
                admin_id=created_by_admin_id,
                action_type=ActionType.ADMIN_CREATE.value,
                user_id=admin_id,
                reason=f"Created admin user with role {role}",
                details={"username": username, "email": email, "role": role},
                ip_address=ip_address
            )
            self.audit_repository.create_action(action)

            current_app.logger.info(f"Admin created: {username} by {created_by_admin_id}")

            return True, "ADMIN_CREATED_SUCCESS", {
                "admin": admin_user.to_dict(),
                "admin_id": admin_id
            }

        except Exception as e:
            current_app.logger.error(f"Admin creation error: {str(e)}")
            return False, "INTERNAL_SERVER_ERROR", None

    def authenticate_admin(self, username: str, password: str,
                          ip_address: str = None) -> Tuple[bool, str, Optional[Dict]]:
        """Authenticate admin user and return tokens"""
        try:
            admin = self.admin_repository.find_by_username(username)
            if not admin:
                admin = self.admin_repository.find_by_email(username)

            if not admin:
                # Log failed login attempt
                action = AdminAction(
                    admin_id="unknown",
                    action_type=ActionType.ADMIN_LOGIN.value,
                    target_type=TargetType.ADMIN.value,
                    action_details={"username": username, "result": "user_not_found"},
                    ip_address=ip_address
                )
                action.mark_failed("Admin not found")
                self.audit_repository.create_action(action)
                return False, "INVALID_CREDENTIALS", None

            if not admin.is_active:
                return False, "ADMIN_ACCOUNT_DISABLED", None

            if admin.is_locked():
                return False, "ADMIN_ACCOUNT_LOCKED", None

            # Check IP whitelist if configured
            if not admin.is_ip_whitelisted(ip_address):
                return False, "IP_NOT_WHITELISTED", None

            if not admin.check_password(password):
                # Increment failed attempts
                self.admin_repository.increment_login_attempts(admin._id)

                # Log failed login
                action = AdminAction(
                    admin_id=admin._id,
                    action_type=ActionType.ADMIN_LOGIN.value,
                    target_type=TargetType.ADMIN.value,
                    action_details={"username": username, "result": "invalid_password"},
                    ip_address=ip_address
                )
                action.mark_failed("Invalid password")
                self.audit_repository.create_action(action)

                return False, "INVALID_CREDENTIALS", None

            # Successful login
            self.admin_repository.update_last_login(admin._id, ip_address)

            # Generate tokens
            tokens = self._generate_admin_tokens(admin)

            # Log successful login
            action = AdminAction(
                admin_id=admin._id,
                action_type=ActionType.ADMIN_LOGIN.value,
                target_type=TargetType.ADMIN.value,
                action_details={"username": username, "result": "success"},
                ip_address=ip_address
            )
            action.mark_success()
            self.audit_repository.create_action(action)

            current_app.logger.info(f"Admin login: {username} from {ip_address}")

            return True, "ADMIN_LOGIN_SUCCESS", {
                "admin": admin.to_dict(),
                "tokens": tokens
            }

        except Exception as e:
            current_app.logger.error(f"Admin authentication error: {str(e)}")
            return False, "INTERNAL_SERVER_ERROR", None

    def get_admin_by_id(self, admin_id: str) -> Tuple[bool, str, Optional[Dict]]:
        """Get admin by ID"""
        try:
            admin = self.admin_repository.find_admin_by_id(admin_id)
            if not admin:
                return False, "ADMIN_NOT_FOUND", None

            return True, "ADMIN_RETRIEVED_SUCCESS", {
                "admin": admin.to_dict()
            }

        except Exception as e:
            current_app.logger.error(f"Get admin error: {str(e)}")
            return False, "INTERNAL_SERVER_ERROR", None

    def update_admin(self, admin_id: str, updates: Dict, updated_by_admin_id: str,
                    ip_address: str = None) -> Tuple[bool, str, Optional[Dict]]:
        """Update admin user"""
        try:
            admin = self.admin_repository.find_admin_by_id(admin_id)
            if not admin:
                return False, "ADMIN_NOT_FOUND", None

            # Store original values for audit
            original_values = {}
            changes = {}

            # Update allowed fields
            allowed_fields = ['role', 'is_active', 'permissions', 'session_timeout']
            for field in allowed_fields:
                if field in updates:
                    original_values[field] = getattr(admin, field, None)
                    setattr(admin, field, updates[field])
                    changes[field] = {"old": original_values[field], "new": updates[field]}

            if not changes:
                return False, "NO_CHANGES_PROVIDED", None

            # Update in database
            success = self.admin_repository.update_admin(admin_id, admin)
            if not success:
                return False, "ADMIN_UPDATE_FAILED", None

            # Log the action
            action = AdminAction.create_user_action(
                admin_id=updated_by_admin_id,
                action_type=ActionType.ADMIN_UPDATE.value,
                user_id=admin_id,
                reason="Admin details updated",
                details={"changes": changes},
                ip_address=ip_address
            )
            self.audit_repository.create_action(action)

            current_app.logger.info(f"Admin updated: {admin_id} by {updated_by_admin_id}")

            return True, "ADMIN_UPDATED_SUCCESS", {
                "admin": admin.to_dict(),
                "changes": changes
            }

        except Exception as e:
            current_app.logger.error(f"Admin update error: {str(e)}")
            return False, "INTERNAL_SERVER_ERROR", None

    def change_admin_password(self, admin_id: str, current_password: str,
                             new_password: str, changed_by_admin_id: str,
                             ip_address: str = None) -> Tuple[bool, str, Optional[Dict]]:
        """Change admin password"""
        try:
            admin = self.admin_repository.find_admin_by_id(admin_id)
            if not admin:
                return False, "ADMIN_NOT_FOUND", None

            # Verify current password (unless super admin is changing another admin's password)
            if admin_id == changed_by_admin_id:
                if not admin.check_password(current_password):
                    return False, "CURRENT_PASSWORD_INCORRECT", None

            # Validate new password
            if not self._validate_password(new_password):
                return False, "PASSWORD_TOO_WEAK", None

            # Update password
            admin.set_password(new_password)
            success = self.admin_repository.update_admin(admin_id, admin)

            if not success:
                return False, "PASSWORD_CHANGE_FAILED", None

            # Log the action
            action = AdminAction.create_user_action(
                admin_id=changed_by_admin_id,
                action_type=ActionType.USER_UPDATE.value,
                user_id=admin_id,
                reason="Password changed",
                details={"action": "password_change"},
                ip_address=ip_address
            )
            self.audit_repository.create_action(action)

            current_app.logger.info(f"Admin password changed: {admin_id} by {changed_by_admin_id}")

            return True, "PASSWORD_CHANGED_SUCCESS", None

        except Exception as e:
            current_app.logger.error(f"Password change error: {str(e)}")
            return False, "INTERNAL_SERVER_ERROR", None

    def activate_admin(self, admin_id: str, activated_by_admin_id: str,
                      ip_address: str = None) -> Tuple[bool, str, Optional[Dict]]:
        """Activate admin account"""
        try:
            success = self.admin_repository.activate_admin(admin_id)
            if not success:
                return False, "ADMIN_ACTIVATION_FAILED", None

            # Log the action
            action = AdminAction.create_user_action(
                admin_id=activated_by_admin_id,
                action_type=ActionType.USER_ACTIVATE.value,
                user_id=admin_id,
                reason="Admin account activated",
                ip_address=ip_address
            )
            self.audit_repository.create_action(action)

            current_app.logger.info(f"Admin activated: {admin_id} by {activated_by_admin_id}")

            return True, "ADMIN_ACTIVATED_SUCCESS", None

        except Exception as e:
            current_app.logger.error(f"Admin activation error: {str(e)}")
            return False, "INTERNAL_SERVER_ERROR", None

    def deactivate_admin(self, admin_id: str, deactivated_by_admin_id: str,
                        reason: str = None, ip_address: str = None) -> Tuple[bool, str, Optional[Dict]]:
        """Deactivate admin account"""
        try:
            # Prevent self-deactivation
            if admin_id == deactivated_by_admin_id:
                return False, "CANNOT_DEACTIVATE_SELF", None

            success = self.admin_repository.deactivate_admin(admin_id)
            if not success:
                return False, "ADMIN_DEACTIVATION_FAILED", None

            # Log the action
            action = AdminAction.create_user_action(
                admin_id=deactivated_by_admin_id,
                action_type=ActionType.USER_SUSPEND.value,
                user_id=admin_id,
                reason=reason or "Admin account deactivated",
                ip_address=ip_address
            )
            self.audit_repository.create_action(action)

            current_app.logger.info(f"Admin deactivated: {admin_id} by {deactivated_by_admin_id}")

            return True, "ADMIN_DEACTIVATED_SUCCESS", None

        except Exception as e:
            current_app.logger.error(f"Admin deactivation error: {str(e)}")
            return False, "INTERNAL_SERVER_ERROR", None

    def list_admins(self, active_only: bool = True, limit: int = 50,
                   skip: int = 0, role: str = None) -> Tuple[bool, str, Optional[Dict]]:
        """List admin users with pagination"""
        try:
            if role:
                admins = self.admin_repository.find_by_role(role, active_only)
            else:
                admins = self.admin_repository.find_all_admins(active_only, limit, skip)

            admin_data = [admin.to_dict() for admin in admins]
            total_count = self.admin_repository.count_admins(role, active_only)

            return True, "ADMINS_RETRIEVED_SUCCESS", {
                "admins": admin_data,
                "total": total_count,
                "limit": limit,
                "skip": skip
            }

        except Exception as e:
            current_app.logger.error(f"List admins error: {str(e)}")
            return False, "INTERNAL_SERVER_ERROR", None

    def search_admins(self, query: str, limit: int = 20) -> Tuple[bool, str, Optional[Dict]]:
        """Search admin users"""
        try:
            admins = self.admin_repository.search_admins(query, limit)
            admin_data = [admin.to_dict() for admin in admins]

            return True, "ADMINS_SEARCH_SUCCESS", {
                "admins": admin_data,
                "query": query,
                "count": len(admin_data)
            }

        except Exception as e:
            current_app.logger.error(f"Admin search error: {str(e)}")
            return False, "INTERNAL_SERVER_ERROR", None

    def get_admin_statistics(self) -> Tuple[bool, str, Optional[Dict]]:
        """Get admin statistics"""
        try:
            stats = self.admin_repository.get_admin_statistics()
            return True, "ADMIN_STATS_SUCCESS", stats

        except Exception as e:
            current_app.logger.error(f"Admin statistics error: {str(e)}")
            return False, "INTERNAL_SERVER_ERROR", None

    def unlock_admin_account(self, admin_id: str, unlocked_by_admin_id: str,
                           ip_address: str = None) -> Tuple[bool, str, Optional[Dict]]:
        """Unlock admin account"""
        try:
            admin = self.admin_repository.find_admin_by_id(admin_id)
            if not admin:
                return False, "ADMIN_NOT_FOUND", None

            if not admin.is_locked():
                return False, "ADMIN_NOT_LOCKED", None

            success = self.admin_repository.reset_login_attempts(admin_id)
            if not success:
                return False, "ADMIN_UNLOCK_FAILED", None

            # Log the action
            action = AdminAction.create_user_action(
                admin_id=unlocked_by_admin_id,
                action_type=ActionType.USER_ACTIVATE.value,
                user_id=admin_id,
                reason="Admin account unlocked",
                details={"action": "unlock_account"},
                ip_address=ip_address
            )
            self.audit_repository.create_action(action)

            current_app.logger.info(f"Admin unlocked: {admin_id} by {unlocked_by_admin_id}")

            return True, "ADMIN_UNLOCKED_SUCCESS", None

        except Exception as e:
            current_app.logger.error(f"Admin unlock error: {str(e)}")
            return False, "INTERNAL_SERVER_ERROR", None

    def enable_mfa(self, admin_id: str, enabled_by_admin_id: str,
                  ip_address: str = None) -> Tuple[bool, str, Optional[Dict]]:
        """Enable MFA for admin"""
        try:
            # Generate MFA secret
            mfa_secret = secrets.token_hex(32)

            success = self.admin_repository.enable_mfa(admin_id, mfa_secret)
            if not success:
                return False, "MFA_ENABLE_FAILED", None

            # Log the action
            action = AdminAction.create_user_action(
                admin_id=enabled_by_admin_id,
                action_type=ActionType.USER_UPDATE.value,
                user_id=admin_id,
                reason="MFA enabled",
                details={"action": "enable_mfa"},
                ip_address=ip_address
            )
            self.audit_repository.create_action(action)

            current_app.logger.info(f"MFA enabled for admin: {admin_id}")

            return True, "MFA_ENABLED_SUCCESS", {
                "mfa_secret": mfa_secret
            }

        except Exception as e:
            current_app.logger.error(f"MFA enable error: {str(e)}")
            return False, "INTERNAL_SERVER_ERROR", None

    def _validate_admin_data(self, username: str, email: str, password: str, role: str) -> Optional[str]:
        """Validate admin creation data"""
        if not username or len(username) < 3:
            return "USERNAME_TOO_SHORT"

        if not email or '@' not in email:
            return "INVALID_EMAIL_FORMAT"

        if not self._validate_password(password):
            return "PASSWORD_TOO_WEAK"

        if role not in AdminUser.ROLES:
            return "INVALID_ROLE"

        return None

    def _validate_password(self, password: str) -> bool:
        """Validate password strength"""
        if len(password) < 8:
            return False

        # At least one uppercase, one lowercase, one digit, one special char
        import re
        if not re.search(r'[A-Z]', password):
            return False
        if not re.search(r'[a-z]', password):
            return False
        if not re.search(r'\d', password):
            return False
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False

        return True

    def _generate_admin_tokens(self, admin: AdminUser) -> Dict[str, str]:
        """Generate JWT tokens for admin"""
        access_token = create_access_token(
            identity=admin._id,
            expires_delta=timedelta(seconds=admin.session_timeout),
            additional_claims={
                'type': 'admin',
                'role': admin.role,
                'permissions': admin.permissions
            }
        )

        refresh_token = create_refresh_token(
            identity=admin._id,
            expires_delta=timedelta(days=7),  # Admin refresh tokens expire in 7 days
            additional_claims={
                'type': 'admin',
                'role': admin.role
            }
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
            "expires_in": admin.session_timeout
        }

    def _is_session_expired(self, admin: AdminUser) -> bool:
        """Check if admin session is expired"""
        if not admin.last_activity:
            return True

        timeout_minutes = getattr(admin, 'session_timeout_minutes', 60)
        expiry_time = admin.last_activity + timedelta(minutes=timeout_minutes)
        return datetime.now(timezone.utc) > expiry_time

    def _can_create_user_with_role(self, creating_admin: AdminUser, target_role: str) -> bool:
        """Check if admin can create user with target role"""
        # Super admin can create any role
        if creating_admin.role == 'super_admin':
            return True

        # Admin can create moderator and analyst
        if creating_admin.role == 'admin':
            return target_role in ['moderator', 'analyst']

        # Moderator and analyst cannot create other admins
        return False