import os
from typing import Optional, List, Dict, Any
from bson import ObjectId
from datetime import datetime, timezone
from app.core.repositories.base_repository import BaseRepository
from app.admin.models.admin_user import AdminUser

class AdminRepository(BaseRepository):
    def __init__(self):
        super().__init__("admin_users")

    def create_indexes(self):
        if self.collection is None or os.getenv('TESTING') == 'true':
            return

        try:
            # Index for username (unique)
            self.collection.create_index("username", unique=True)

            # Index for email (unique)
            self.collection.create_index("email", unique=True)

            # Index for role filtering
            self.collection.create_index("role")

            # Index for active status
            self.collection.create_index("is_active")

            # Compound index for role and active status
            self.collection.create_index([("role", 1), ("is_active", 1)])

            # Index for last_login for session management
            self.collection.create_index("last_login")

            # Index for created_by for audit trails
            self.collection.create_index("created_by")

            # Index for login_attempts for security
            self.collection.create_index("login_attempts")

        except Exception as e:
            # Log error but don't fail on index creation
            print(f"Warning: Could not create indexes for admin_users: {str(e)}")

    def create_admin(self, admin_user: AdminUser) -> str:
        """Create a new admin user"""
        admin_data = admin_user.to_dict(include_sensitive=True)
        admin_data['created_at'] = admin_user.created_at
        admin_data['updated_at'] = admin_user.updated_at

        # Remove _id if None to let MongoDB generate it
        if admin_data.get('_id') is None:
            admin_data.pop('_id', None)

        return self.create(admin_data)

    def find_by_username(self, username: str) -> Optional[AdminUser]:
        """Find admin by username"""
        data = self.find_one({"username": username})
        if data:
            return AdminUser.from_dict(data)
        return None

    def find_by_email(self, email: str) -> Optional[AdminUser]:
        """Find admin by email"""
        data = self.find_one({"email": email.lower()})
        if data:
            return AdminUser.from_dict(data)
        return None

    def find_admin_by_id(self, admin_id: str) -> Optional[AdminUser]:
        """Find admin by ID and return AdminUser object"""
        data = self.find_by_id(admin_id)
        if data:
            return AdminUser.from_dict(data)
        return None

    def update_admin(self, admin_id: str, admin_user: AdminUser) -> bool:
        """Update admin user"""
        admin_data = admin_user.to_dict(include_sensitive=True)
        admin_data['updated_at'] = datetime.now(timezone.utc)

        # Remove _id from update data
        admin_data.pop('_id', None)

        return self.update_by_id(admin_id, admin_data)

    def update_last_login(self, admin_id: str, ip_address: str = None) -> bool:
        """Update last login timestamp and reset failed attempts"""
        update_data = {
            'last_login': datetime.now(timezone.utc),
            'login_attempts': 0,
            'updated_at': datetime.now(timezone.utc)
        }

        if ip_address:
            update_data['last_ip_address'] = ip_address

        return self.update_by_id(admin_id, update_data)

    def increment_login_attempts(self, admin_id: str) -> bool:
        """Increment failed login attempts"""
        if not ObjectId.is_valid(admin_id):
            return False

        result = self.collection.update_one(
            {"_id": ObjectId(admin_id)},
            {
                "$inc": {"login_attempts": 1},
                "$set": {"updated_at": datetime.now(timezone.utc)}
            }
        )
        return result.modified_count > 0

    def reset_login_attempts(self, admin_id: str) -> bool:
        """Reset failed login attempts"""
        return self.update_by_id(admin_id, {
            'login_attempts': 0,
            'updated_at': datetime.now(timezone.utc)
        })

    def find_by_role(self, role: str, active_only: bool = True) -> List[AdminUser]:
        """Find all admins with specific role"""
        filter_dict = {"role": role}
        if active_only:
            filter_dict["is_active"] = True

        data_list = self.find_many(filter_dict)
        return [AdminUser.from_dict(data) for data in data_list]

    def find_all_admins(self, active_only: bool = True, limit: int = None,
                       skip: int = None) -> List[AdminUser]:
        """Find all admin users with pagination"""
        filter_dict = {}
        if active_only:
            filter_dict["is_active"] = True

        data_list = self.find_many(filter_dict, limit=limit, skip=skip,
                                  sort=[("created_at", -1)])
        return [AdminUser.from_dict(data) for data in data_list]

    def count_admins(self, role: str = None, active_only: bool = True) -> int:
        """Count admins with optional filters"""
        filter_dict = {}
        if role:
            filter_dict["role"] = role
        if active_only:
            filter_dict["is_active"] = True

        return self.count(filter_dict)

    def find_recent_logins(self, hours: int = 24, limit: int = 50) -> List[AdminUser]:
        """Find admins who logged in recently"""
        since_time = datetime.now(timezone.utc).replace(
            hour=datetime.now(timezone.utc).hour - hours
        )

        filter_dict = {
            "last_login": {"$gte": since_time},
            "is_active": True
        }

        data_list = self.find_many(filter_dict, limit=limit,
                                  sort=[("last_login", -1)])
        return [AdminUser.from_dict(data) for data in data_list]

    def find_locked_accounts(self) -> List[AdminUser]:
        """Find admin accounts that are locked due to failed attempts"""
        filter_dict = {
            "login_attempts": {"$gte": 5},
            "is_active": True
        }

        data_list = self.find_many(filter_dict, sort=[("login_attempts", -1)])
        return [AdminUser.from_dict(data) for data in data_list]

    def activate_admin(self, admin_id: str) -> bool:
        """Activate admin account"""
        return self.update_by_id(admin_id, {
            'is_active': True,
            'login_attempts': 0,
            'updated_at': datetime.now(timezone.utc)
        })

    def deactivate_admin(self, admin_id: str) -> bool:
        """Deactivate admin account"""
        return self.update_by_id(admin_id, {
            'is_active': False,
            'updated_at': datetime.now(timezone.utc)
        })

    def update_permissions(self, admin_id: str, permissions: List[str]) -> bool:
        """Update admin permissions"""
        return self.update_by_id(admin_id, {
            'permissions': permissions,
            'updated_at': datetime.now(timezone.utc)
        })

    def update_role(self, admin_id: str, new_role: str) -> bool:
        """Update admin role and reset permissions to role defaults"""
        admin_user = self.find_admin_by_id(admin_id)
        if not admin_user:
            return False

        admin_user.update_role(new_role)
        return self.update_admin(admin_id, admin_user)

    def enable_mfa(self, admin_id: str, mfa_secret: str) -> bool:
        """Enable MFA for admin"""
        return self.update_by_id(admin_id, {
            'mfa_enabled': True,
            'mfa_secret': mfa_secret,
            'updated_at': datetime.now(timezone.utc)
        })

    def disable_mfa(self, admin_id: str) -> bool:
        """Disable MFA for admin"""
        return self.update_by_id(admin_id, {
            'mfa_enabled': False,
            'mfa_secret': None,
            'updated_at': datetime.now(timezone.utc)
        })

    def update_ip_whitelist(self, admin_id: str, ip_list: List[str]) -> bool:
        """Update IP whitelist for admin"""
        return self.update_by_id(admin_id, {
            'ip_whitelist': ip_list,
            'updated_at': datetime.now(timezone.utc)
        })

    def search_admins(self, query: str, limit: int = 20) -> List[AdminUser]:
        """Search admins by username or email"""
        filter_dict = {
            "$or": [
                {"username": {"$regex": query, "$options": "i"}},
                {"email": {"$regex": query, "$options": "i"}}
            ],
            "is_active": True
        }

        data_list = self.find_many(filter_dict, limit=limit,
                                  sort=[("username", 1)])
        return [AdminUser.from_dict(data) for data in data_list]

    def get_admin_statistics(self) -> Dict[str, Any]:
        """Get admin statistics"""
        if not self.collection:
            return {}

        try:
            total_admins = self.count()
            active_admins = self.count({"is_active": True})
            inactive_admins = total_admins - active_admins

            # Count by role
            role_counts = {}
            for role in AdminUser.ROLES.keys():
                role_counts[role] = self.count({"role": role, "is_active": True})

            # Count recent logins (last 24 hours)
            recent_logins = len(self.find_recent_logins(hours=24))

            # Count locked accounts
            locked_accounts = len(self.find_locked_accounts())

            return {
                'total_admins': total_admins,
                'active_admins': active_admins,
                'inactive_admins': inactive_admins,
                'role_distribution': role_counts,
                'recent_logins_24h': recent_logins,
                'locked_accounts': locked_accounts
            }

        except Exception as e:
            print(f"Error getting admin statistics: {str(e)}")
            return {}

    def cleanup_inactive_sessions(self, hours: int = 24) -> int:
        """Clean up admin records with old last_login (for session management)"""
        if not self.collection:
            return 0

        try:
            cutoff_time = datetime.now(timezone.utc).replace(
                hour=datetime.now(timezone.utc).hour - hours
            )

            # This doesn't delete admins, just resets their login attempts
            # for security purposes
            result = self.collection.update_many(
                {
                    "last_login": {"$lt": cutoff_time},
                    "login_attempts": {"$gt": 0}
                },
                {
                    "$set": {
                        "login_attempts": 0,
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )
            return result.modified_count

        except Exception as e:
            print(f"Error cleaning up inactive sessions: {str(e)}")
            return 0