from datetime import datetime, timezone
from bson import ObjectId
from typing import Dict, Any, List, Optional
from enum import Enum

class WidgetType(Enum):
    METRIC_CARD = "metric_card"
    LINE_CHART = "line_chart"
    BAR_CHART = "bar_chart"
    PIE_CHART = "pie_chart"
    TABLE = "table"
    HEATMAP = "heatmap"
    GAUGE = "gauge"
    ALERT_LIST = "alert_list"
    USER_LIST = "user_list"
    ACTIVITY_FEED = "activity_feed"

class RefreshInterval(Enum):
    REAL_TIME = 0  # WebSocket updates
    FIVE_SECONDS = 5
    THIRTY_SECONDS = 30
    ONE_MINUTE = 60
    FIVE_MINUTES = 300
    FIFTEEN_MINUTES = 900
    ONE_HOUR = 3600

class DashboardConfig:
    def __init__(self, name: str, admin_id: str, layout: List[Dict[str, Any]] = None,
                 widgets: List[Dict[str, Any]] = None, is_default: bool = False,
                 is_public: bool = False, permissions: List[str] = None,
                 refresh_interval: int = RefreshInterval.ONE_MINUTE.value,
                 auto_refresh: bool = True, theme: str = "light",
                 _id: str = None, created_at: datetime = None,
                 updated_at: datetime = None):

        self._id = _id
        self.name = name
        self.admin_id = admin_id
        self.layout = layout or []
        self.widgets = widgets or []
        self.is_default = is_default
        self.is_public = is_public
        self.permissions = permissions or []
        self.refresh_interval = refresh_interval
        self.auto_refresh = auto_refresh
        self.theme = theme
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or datetime.now(timezone.utc)

    def add_widget(self, widget_config: Dict[str, Any]):
        """Add a widget to the dashboard"""
        widget_id = str(ObjectId())
        widget_config['id'] = widget_id
        widget_config['created_at'] = datetime.now(timezone.utc).isoformat()

        self.widgets.append(widget_config)
        self.updated_at = datetime.now(timezone.utc)

        return widget_id

    def remove_widget(self, widget_id: str) -> bool:
        """Remove a widget from the dashboard"""
        original_count = len(self.widgets)
        self.widgets = [w for w in self.widgets if w.get('id') != widget_id]

        if len(self.widgets) < original_count:
            self.updated_at = datetime.now(timezone.utc)
            return True
        return False

    def update_widget(self, widget_id: str, updates: Dict[str, Any]) -> bool:
        """Update a widget configuration"""
        for widget in self.widgets:
            if widget.get('id') == widget_id:
                widget.update(updates)
                widget['updated_at'] = datetime.now(timezone.utc).isoformat()
                self.updated_at = datetime.now(timezone.utc)
                return True
        return False

    def get_widget(self, widget_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific widget by ID"""
        for widget in self.widgets:
            if widget.get('id') == widget_id:
                return widget
        return None

    def update_layout(self, new_layout: List[Dict[str, Any]]):
        """Update dashboard layout"""
        self.layout = new_layout
        self.updated_at = datetime.now(timezone.utc)

    def add_permission(self, permission: str):
        """Add permission required to view this dashboard"""
        if permission not in self.permissions:
            self.permissions.append(permission)
            self.updated_at = datetime.now(timezone.utc)

    def remove_permission(self, permission: str):
        """Remove permission requirement"""
        if permission in self.permissions:
            self.permissions.remove(permission)
            self.updated_at = datetime.now(timezone.utc)

    def can_be_viewed_by(self, admin_permissions: List[str]) -> bool:
        """Check if admin with given permissions can view this dashboard"""
        if self.is_public:
            return True

        if not self.permissions:  # No specific permissions required
            return True

        # Check if admin has any required permission
        return any(perm in admin_permissions for perm in self.permissions)

    @staticmethod
    def create_default_dashboard(admin_id: str) -> 'DashboardConfig':
        """Create default admin dashboard with essential widgets"""
        config = DashboardConfig(
            name="Default Admin Dashboard",
            admin_id=admin_id,
            is_default=True,
            refresh_interval=RefreshInterval.THIRTY_SECONDS.value
        )

        # System Overview Widget
        config.add_widget({
            'type': WidgetType.METRIC_CARD.value,
            'title': 'System Overview',
            'data_source': 'system_metrics',
            'metrics': ['cpu_usage', 'memory_usage', 'active_sessions'],
            'position': {'x': 0, 'y': 0, 'w': 4, 'h': 2}
        })

        # User Activity Chart
        config.add_widget({
            'type': WidgetType.LINE_CHART.value,
            'title': 'User Activity (24h)',
            'data_source': 'user_activity',
            'metric': 'active_users',
            'time_range': '24h',
            'position': {'x': 4, 'y': 0, 'w': 8, 'h': 4}
        })

        # Donation Flow
        config.add_widget({
            'type': WidgetType.BAR_CHART.value,
            'title': 'Donation Flow',
            'data_source': 'financial_metrics',
            'metric': 'donations_per_hour',
            'time_range': '24h',
            'position': {'x': 0, 'y': 2, 'w': 4, 'h': 4}
        })

        # Recent Alerts
        config.add_widget({
            'type': WidgetType.ALERT_LIST.value,
            'title': 'Recent Alerts',
            'data_source': 'system_alerts',
            'limit': 10,
            'position': {'x': 0, 'y': 6, 'w': 6, 'h': 3}
        })

        # Performance Metrics
        config.add_widget({
            'type': WidgetType.GAUGE.value,
            'title': 'API Response Time',
            'data_source': 'performance_metrics',
            'metric': 'response_time_avg',
            'max_value': 2000,
            'position': {'x': 6, 'y': 6, 'w': 3, 'h': 3}
        })

        # Recent Admin Actions
        config.add_widget({
            'type': WidgetType.ACTIVITY_FEED.value,
            'title': 'Recent Admin Actions',
            'data_source': 'admin_actions',
            'limit': 15,
            'position': {'x': 9, 'y': 6, 'w': 3, 'h': 3}
        })

        return config

    @staticmethod
    def create_user_management_dashboard(admin_id: str) -> 'DashboardConfig':
        """Create dashboard focused on user management"""
        config = DashboardConfig(
            name="User Management Dashboard",
            admin_id=admin_id,
            permissions=['user_management']
        )

        # User Statistics
        config.add_widget({
            'type': WidgetType.METRIC_CARD.value,
            'title': 'User Statistics',
            'data_source': 'user_stats',
            'metrics': ['total_users', 'active_users', 'new_registrations'],
            'position': {'x': 0, 'y': 0, 'w': 6, 'h': 2}
        })

        # Registration Trend
        config.add_widget({
            'type': WidgetType.LINE_CHART.value,
            'title': 'Registration Trend (30 days)',
            'data_source': 'user_registrations',
            'time_range': '30d',
            'position': {'x': 6, 'y': 0, 'w': 6, 'h': 4}
        })

        # User Activity by Country
        config.add_widget({
            'type': WidgetType.PIE_CHART.value,
            'title': 'Users by Country',
            'data_source': 'user_demographics',
            'metric': 'country',
            'position': {'x': 0, 'y': 2, 'w': 6, 'h': 4}
        })

        # Recent User Actions
        config.add_widget({
            'type': WidgetType.TABLE.value,
            'title': 'Recent User Actions',
            'data_source': 'user_actions',
            'columns': ['user', 'action', 'timestamp', 'status'],
            'limit': 20,
            'position': {'x': 0, 'y': 6, 'w': 12, 'h': 4}
        })

        return config

    @staticmethod
    def create_financial_dashboard(admin_id: str) -> 'DashboardConfig':
        """Create dashboard focused on financial oversight"""
        config = DashboardConfig(
            name="Financial Dashboard",
            admin_id=admin_id,
            permissions=['financial_oversight']
        )

        # Financial Overview
        config.add_widget({
            'type': WidgetType.METRIC_CARD.value,
            'title': 'Financial Overview',
            'data_source': 'financial_stats',
            'metrics': ['total_donations', 'platform_revenue', 'processing_fees'],
            'position': {'x': 0, 'y': 0, 'w': 8, 'h': 2}
        })

        # Donation Trend
        config.add_widget({
            'type': WidgetType.LINE_CHART.value,
            'title': 'Donation Trend (30 days)',
            'data_source': 'donation_metrics',
            'metric': 'total_donations',
            'time_range': '30d',
            'position': {'x': 8, 'y': 0, 'w': 4, 'h': 4}
        })

        # ONLUS Allocation
        config.add_widget({
            'type': WidgetType.PIE_CHART.value,
            'title': 'ONLUS Allocation',
            'data_source': 'onlus_allocations',
            'position': {'x': 0, 'y': 2, 'w': 4, 'h': 4}
        })

        # Revenue vs Costs
        config.add_widget({
            'type': WidgetType.BAR_CHART.value,
            'title': 'Revenue vs Costs',
            'data_source': 'financial_comparison',
            'metrics': ['revenue', 'costs'],
            'position': {'x': 4, 'y': 2, 'w': 4, 'h': 4}
        })

        return config

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            '_id': str(self._id) if self._id else None,
            'name': self.name,
            'admin_id': self.admin_id,
            'layout': self.layout,
            'widgets': self.widgets,
            'is_default': self.is_default,
            'is_public': self.is_public,
            'permissions': self.permissions,
            'refresh_interval': self.refresh_interval,
            'auto_refresh': self.auto_refresh,
            'theme': self.theme,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DashboardConfig':
        """Create DashboardConfig instance from dictionary"""
        created_at = None
        updated_at = None

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

        return cls(
            _id=str(data['_id']) if data.get('_id') else None,
            name=data['name'],
            admin_id=data['admin_id'],
            layout=data.get('layout', []),
            widgets=data.get('widgets', []),
            is_default=data.get('is_default', False),
            is_public=data.get('is_public', False),
            permissions=data.get('permissions', []),
            refresh_interval=data.get('refresh_interval', RefreshInterval.ONE_MINUTE.value),
            auto_refresh=data.get('auto_refresh', True),
            theme=data.get('theme', 'light'),
            created_at=created_at,
            updated_at=updated_at
        )

    def __repr__(self):
        return f"<DashboardConfig {self.name} by {self.admin_id}>"