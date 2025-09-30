from .admin_controller import admin_bp
from .dashboard_controller import dashboard_bp
from .user_management_controller import user_mgmt_bp

__all__ = [
    'admin_bp',
    'dashboard_bp',
    'user_mgmt_bp'
]