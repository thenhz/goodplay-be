from datetime import datetime, timezone, timedelta
from bson import ObjectId
from typing import List, Optional, Dict, Any
from werkzeug.security import generate_password_hash, check_password_hash

class AdminUser:
    ROLES = {
        'super_admin': {
            'name': 'Super Administrator',
            'permissions': ['*']  # All permissions
        },
        'admin': {
            'name': 'Administrator',
            'permissions': [
                'user_management', 'content_moderation', 'financial_oversight',
                'system_monitoring', 'onlus_management', 'game_management'
            ]
        },
        'moderator': {
            'name': 'Content Moderator',
            'permissions': [
                'content_moderation', 'user_moderation', 'game_content_review'
            ]
        },
        'analyst': {
            'name': 'Data Analyst',
            'permissions': [
                'analytics_view', 'reports_view', 'metrics_view'
            ]
        }
    }

    def __init__(self, username: str, email: str, password_hash: str = None,
                 role: str = 'analyst', permissions: List[str] = None,
                 is_active: bool = True, created_by: str = None,
                 last_login: datetime = None, login_attempts: int = 0,
                 mfa_enabled: bool = False, mfa_secret: str = None,
                 ip_whitelist: List[str] = None, session_timeout: int = 3600,
                 _id: str = None, created_at: datetime = None,
                 updated_at: datetime = None, failed_login_attempts: int = 0,
                 is_locked: bool = False, locked_until: datetime = None,
                 allowed_ips: List[str] = None, last_activity: datetime = None,
                 session_timeout_minutes: int = 60):

        self._id = _id
        self.username = username
        self.email = email.lower()
        self.password_hash = password_hash
        self.role = role
        self.permissions = permissions or self._get_role_permissions(role)
        self.is_active = is_active
        self.created_by = created_by
        self.last_login = last_login
        self.login_attempts = login_attempts
        self.mfa_enabled = mfa_enabled
        self.mfa_secret = mfa_secret
        self.ip_whitelist = ip_whitelist or []
        self.session_timeout = session_timeout
        self.failed_login_attempts = failed_login_attempts
        self.is_locked = is_locked
        self.locked_until = locked_until
        self.allowed_ips = allowed_ips or []
        self.last_activity = last_activity
        self.session_timeout_minutes = session_timeout_minutes
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or datetime.now(timezone.utc)

    def _get_role_permissions(self, role: str) -> List[str]:
        """Get default permissions for a role"""
        return self.ROLES.get(role, {}).get('permissions', [])

    def set_password(self, password: str):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
        self.updated_at = datetime.now(timezone.utc)

    def check_password(self, password: str) -> bool:
        """Check if provided password matches hash"""
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def has_permission(self, permission: str) -> bool:
        """Check if admin has specific permission"""
        if not self.is_active:
            return False

        # Super admin has all permissions
        if '*' in self.permissions:
            return True

        return permission in self.permissions

    def can_access_resource(self, resource: str) -> bool:
        """Check if admin can access a specific resource"""
        resource_permissions = {
            'users': 'user_management',
            'content': 'content_moderation',
            'financial': 'financial_oversight',
            'system': 'system_monitoring',
            'onlus': 'onlus_management',
            'games': 'game_management',
            'analytics': 'analytics_view'
        }

        required_permission = resource_permissions.get(resource)
        if not required_permission:
            return False

        return self.has_permission(required_permission)

    def add_permission(self, permission: str):
        """Add a permission to the admin user"""
        if permission not in self.permissions:
            self.permissions.append(permission)
            self.updated_at = datetime.now(timezone.utc)

    def remove_permission(self, permission: str):
        """Remove a permission from the admin user"""
        if permission in self.permissions:
            self.permissions.remove(permission)
            self.updated_at = datetime.now(timezone.utc)

    def update_role(self, new_role: str):
        """Update admin role and reset permissions"""
        if new_role in self.ROLES:
            self.role = new_role
            self.permissions = self._get_role_permissions(new_role)
            self.updated_at = datetime.now(timezone.utc)

    def record_login(self, ip_address: str = None):
        """Record successful login"""
        self.last_login = datetime.now(timezone.utc)
        self.login_attempts = 0
        self.updated_at = datetime.now(timezone.utc)

    def record_failed_login(self):
        """Record failed login attempt"""
        self.login_attempts += 1
        self.updated_at = datetime.now(timezone.utc)

    def is_locked(self) -> bool:
        """Check if account is locked due to failed attempts"""
        return self.login_attempts >= 5

    def unlock_account(self):
        """Unlock account by resetting failed attempts"""
        self.login_attempts = 0
        self.updated_at = datetime.now(timezone.utc)

    def enable_mfa(self, secret: str):
        """Enable multi-factor authentication"""
        self.mfa_enabled = True
        self.mfa_secret = secret
        self.updated_at = datetime.now(timezone.utc)

    def disable_mfa(self):
        """Disable multi-factor authentication"""
        self.mfa_enabled = False
        self.mfa_secret = None
        self.updated_at = datetime.now(timezone.utc)

    def add_whitelisted_ip(self, ip_address: str):
        """Add IP to whitelist"""
        if ip_address not in self.ip_whitelist:
            self.ip_whitelist.append(ip_address)
            self.updated_at = datetime.now(timezone.utc)

    def remove_whitelisted_ip(self, ip_address: str):
        """Remove IP from whitelist"""
        if ip_address in self.ip_whitelist:
            self.ip_whitelist.remove(ip_address)
            self.updated_at = datetime.now(timezone.utc)

    def is_ip_whitelisted(self, ip_address: str) -> bool:
        """Check if IP address is whitelisted"""
        if not self.ip_whitelist:  # If no whitelist, allow all
            return True
        return ip_address in self.ip_whitelist

    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = {
            '_id': str(self._id) if self._id else None,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'role_name': self.ROLES.get(self.role, {}).get('name', self.role),
            'permissions': self.permissions,
            'is_active': self.is_active,
            'created_by': self.created_by,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'login_attempts': self.login_attempts,
            'mfa_enabled': self.mfa_enabled,
            'session_timeout': self.session_timeout,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

        if include_sensitive:
            data.update({
                'password_hash': self.password_hash,
                'mfa_secret': self.mfa_secret,
                'ip_whitelist': self.ip_whitelist
            })

        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AdminUser':
        """Create AdminUser instance from dictionary"""
        # Convert string timestamps back to datetime objects
        created_at = None
        updated_at = None
        last_login = None

        if data.get('created_at'):
            if isinstance(data['created_at'], str):
                created_at = datetime.fromisoformat(data['created_at'].replace('Z', '+00:00'))
            else:
                created_at = data['created_at']

        if data.get('updated_at'):
            if isinstance(data['updated_at'], str):
                updated_at = datetime.fromisoformat(data['updated_at'].replace('Z', '+00:00'))
            else:
                updated_at = data['updated_at']

        if data.get('last_login'):
            if isinstance(data['last_login'], str):
                last_login = datetime.fromisoformat(data['last_login'].replace('Z', '+00:00'))
            else:
                last_login = data['last_login']

        return cls(
            _id=str(data['_id']) if data.get('_id') else None,
            username=data['username'],
            email=data['email'],
            password_hash=data.get('password_hash'),
            role=data.get('role', 'analyst'),
            permissions=data.get('permissions'),
            is_active=data.get('is_active', True),
            created_by=data.get('created_by'),
            last_login=last_login,
            login_attempts=data.get('login_attempts', 0),
            mfa_enabled=data.get('mfa_enabled', False),
            mfa_secret=data.get('mfa_secret'),
            ip_whitelist=data.get('ip_whitelist', []),
            session_timeout=data.get('session_timeout', 3600),
            created_at=created_at,
            updated_at=updated_at
        )

    def __repr__(self):
        return f"<AdminUser {self.username} ({self.role})>"

    # Additional methods for test compatibility
    def get_role_level(self) -> int:
        """Get numeric role level for hierarchy comparison"""
        role_levels = {
            'super_admin': 4,
            'admin': 3,
            'moderator': 2,
            'analyst': 1
        }
        return role_levels.get(self.role, 0)

    def can_manage_user(self, other_user: 'AdminUser') -> bool:
        """Check if this admin can manage another admin user"""
        return self.get_role_level() > other_user.get_role_level()

    def add_permissions(self, permissions: List[str]):
        """Add multiple permissions"""
        for permission in permissions:
            self.add_permission(permission)

    def remove_permissions(self, permissions: List[str]):
        """Remove multiple permissions"""
        for permission in permissions:
            self.remove_permission(permission)

    def _update_permissions_for_role(self):
        """Update permissions based on current role"""
        self.permissions = self._get_role_permissions(self.role)
        self.updated_at = datetime.now(timezone.utc)

    def add_temporary_permission(self, permission: str, hours: int = 1):
        """Add temporary permission (placeholder for future implementation)"""
        # This would be implemented with expiring permissions
        if not hasattr(self, 'temporary_permissions'):
            self.temporary_permissions = {}

        expiry = datetime.now(timezone.utc) + timedelta(hours=hours)
        self.temporary_permissions[permission] = expiry
        self.updated_at = datetime.now(timezone.utc)

    def has_permission_in_context(self, permission: str, context: str) -> bool:
        """Check permission in specific context"""
        # Basic implementation - could be extended for context-aware permissions
        return self.has_permission(permission)

    def can_perform_action(self, action: str) -> bool:
        """Check if admin can perform specific action"""
        action_permissions = {
            'suspend_user': 'user_management',
            'delete_content': 'content_moderation',
            'view_financials': 'financial_oversight',
            'manage_onlus': 'onlus_management',
            'system_config': 'system_administration'
        }

        required_permission = action_permissions.get(action)
        if not required_permission:
            return False

        return self.has_permission(required_permission)

    def has_department_permission(self, permission: str, department: str) -> bool:
        """Check permission for specific department"""
        # Basic implementation - could be extended for department-based permissions
        if hasattr(self, 'department') and self.department == department:
            return self.has_permission(permission)
        return False

    def is_ip_allowed(self, ip_address: str) -> bool:
        """Check if IP is in allowed list (with subnet support)"""
        if not hasattr(self, 'allowed_ips') or not self.allowed_ips:
            return True

        import ipaddress

        try:
            ip = ipaddress.ip_address(ip_address)
            for allowed in self.allowed_ips:
                if '/' in allowed:  # CIDR notation
                    network = ipaddress.ip_network(allowed, strict=False)
                    if ip in network:
                        return True
                else:  # Exact IP match
                    if str(ip) == allowed:
                        return True
            return False
        except ValueError:
            return False

    def has_session_permission(self, permission: str) -> bool:
        """Check session-specific permissions"""
        if hasattr(self, 'session_permissions'):
            return permission in self.session_permissions
        return False

    def generate_password_reset_token(self) -> str:
        """Generate password reset token"""
        import secrets
        token = secrets.token_urlsafe(32)

        # Store token and expiry
        self.password_reset_token = token
        self.password_reset_expires = datetime.now(timezone.utc) + timedelta(hours=1)
        self.updated_at = datetime.now(timezone.utc)

        return token

    def validate_password_reset_token(self, token: str) -> bool:
        """Validate password reset token"""
        if not hasattr(self, 'password_reset_token') or not self.password_reset_token:
            return False

        if not hasattr(self, 'password_reset_expires') or not self.password_reset_expires:
            return False

        if datetime.now(timezone.utc) > self.password_reset_expires:
            return False

        return self.password_reset_token == token