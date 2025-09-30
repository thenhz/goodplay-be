"""
Admin Module for GoodPlay Backend

This module provides comprehensive administrative capabilities including:
- Admin user management with role-based access control
- Real-time system monitoring and metrics collection
- Dashboard views for different admin functions
- Audit logging and security monitoring
- Content moderation and financial oversight

The admin module follows the established pattern of:
- Models: Data structures for admin entities
- Repositories: Data access layer with MongoDB integration
- Services: Business logic layer
- Controllers: API endpoints with proper authentication and authorization
"""

from .models import (
    AdminUser, SystemMetric, AdminAction, DashboardConfig,
    MetricType, MetricPeriod, ActionType, TargetType, ActionStatus,
    WidgetType, RefreshInterval
)

from .services import (
    AdminService, DashboardService, MonitoringService
)

from .repositories import (
    AdminRepository, MetricsRepository, AuditRepository
)

from .controllers import (
    admin_bp, dashboard_bp, user_mgmt_bp
)

__all__ = [
    # Models
    'AdminUser', 'SystemMetric', 'AdminAction', 'DashboardConfig',
    'MetricType', 'MetricPeriod', 'ActionType', 'TargetType', 'ActionStatus',
    'WidgetType', 'RefreshInterval',

    # Services
    'AdminService', 'DashboardService', 'MonitoringService',

    # Repositories
    'AdminRepository', 'MetricsRepository', 'AuditRepository',

    # Controllers
    'admin_bp', 'dashboard_bp', 'user_mgmt_bp'
]