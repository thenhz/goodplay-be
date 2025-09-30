from datetime import datetime, timezone
from bson import ObjectId
from typing import Dict, Any, Optional
from enum import Enum

class ActionType(Enum):
    # User Management Actions
    USER_CREATE = "user_create"
    USER_UPDATE = "user_update"
    USER_DELETE = "user_delete"
    USER_SUSPEND = "user_suspend"
    USER_ACTIVATE = "user_activate"
    USER_ROLE_CHANGE = "user_role_change"
    USER_BULK_ACTION = "user_bulk_action"

    # Content Moderation Actions
    CONTENT_APPROVE = "content_approve"
    CONTENT_REJECT = "content_reject"
    CONTENT_REMOVE = "content_remove"
    CONTENT_FLAG = "content_flag"
    GAME_APPROVE = "game_approve"
    GAME_REJECT = "game_reject"
    PLUGIN_REVIEW = "plugin_review"

    # ONLUS Management Actions
    ONLUS_APPROVE = "onlus_approve"
    ONLUS_REJECT = "onlus_reject"
    ONLUS_SUSPEND = "onlus_suspend"
    ONLUS_UPDATE = "onlus_update"
    ONLUS_VERIFY = "onlus_verify"

    # Financial Actions
    FINANCIAL_AUDIT = "financial_audit"
    DONATION_REVIEW = "donation_review"
    TRANSACTION_REFUND = "transaction_refund"
    FEE_ADJUSTMENT = "fee_adjustment"
    PAYMENT_INVESTIGATION = "payment_investigation"

    # System Actions
    SYSTEM_CONFIG = "system_config"
    SYSTEM_BACKUP = "system_backup"
    SYSTEM_MAINTENANCE = "system_maintenance"
    ALERT_ACKNOWLEDGE = "alert_acknowledge"
    ALERT_CONFIGURE = "alert_configure"

    # Security Actions
    SECURITY_INVESTIGATION = "security_investigation"
    IP_BLOCK = "ip_block"
    IP_UNBLOCK = "ip_unblock"
    FRAUD_INVESTIGATION = "fraud_investigation"
    ACCESS_GRANT = "access_grant"
    ACCESS_REVOKE = "access_revoke"

    # Admin Management Actions
    ADMIN_CREATE = "admin_create"
    ADMIN_UPDATE = "admin_update"
    ADMIN_DELETE = "admin_delete"
    ADMIN_LOGIN = "admin_login"
    ADMIN_LOGOUT = "admin_logout"
    PERMISSION_GRANT = "permission_grant"
    PERMISSION_REVOKE = "permission_revoke"

class TargetType(Enum):
    USER = "user"
    ADMIN = "admin"
    ONLUS = "onlus"
    GAME = "game"
    PLUGIN = "plugin"
    CONTENT = "content"
    TRANSACTION = "transaction"
    DONATION = "donation"
    SYSTEM = "system"
    ALERT = "alert"
    IP_ADDRESS = "ip_address"
    SESSION = "session"

class ActionStatus(Enum):
    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"
    CANCELLED = "cancelled"

class AdminAction:
    def __init__(self, admin_id: str, action_type: str, target_type: str,
                 target_id: str = None, action_details: Dict[str, Any] = None,
                 reason: str = None, status: str = ActionStatus.SUCCESS.value,
                 ip_address: str = None, user_agent: str = None,
                 session_id: str = None, result: Dict[str, Any] = None,
                 execution_time_ms: int = None, _id: str = None,
                 timestamp: datetime = None):

        self._id = _id
        self.admin_id = admin_id
        self.action_type = action_type
        self.target_type = target_type
        self.target_id = target_id
        self.action_details = action_details or {}
        self.details = action_details or {}  # Alias for compatibility
        self.reason = reason
        self.status = status
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.session_id = session_id
        self.result = result or {}
        self.execution_time_ms = execution_time_ms
        self.timestamp = timestamp or datetime.now(timezone.utc)

    def mark_success(self, result: Dict[str, Any] = None):
        """Mark action as successful"""
        self.status = ActionStatus.SUCCESS.value
        if result:
            self.result.update(result)

    def mark_failed(self, error_message: str = None, error_code: str = None):
        """Mark action as failed"""
        self.status = ActionStatus.FAILED.value
        if error_message:
            self.result['error_message'] = error_message
        if error_code:
            self.result['error_code'] = error_code

    def mark_pending(self):
        """Mark action as pending"""
        self.status = ActionStatus.PENDING.value

    def mark_cancelled(self, reason: str = None):
        """Mark action as cancelled"""
        self.status = ActionStatus.CANCELLED.value
        if reason:
            self.result['cancellation_reason'] = reason

    def set_execution_time(self, start_time: datetime):
        """Calculate and set execution time"""
        end_time = datetime.now(timezone.utc)
        delta = end_time - start_time
        self.execution_time_ms = int(delta.total_seconds() * 1000)

    def add_detail(self, key: str, value: Any):
        """Add detail to action"""
        self.action_details[key] = value

    def get_detail(self, key: str, default: Any = None) -> Any:
        """Get action detail"""
        return self.action_details.get(key, default)

    def add_result(self, key: str, value: Any):
        """Add result data"""
        self.result[key] = value

    def get_result(self, key: str, default: Any = None) -> Any:
        """Get result data"""
        return self.result.get(key, default)

    def is_sensitive_action(self) -> bool:
        """Check if this is a sensitive action requiring extra security"""
        sensitive_actions = [
            ActionType.USER_DELETE.value,
            ActionType.ADMIN_DELETE.value,
            ActionType.FINANCIAL_AUDIT.value,
            ActionType.SYSTEM_CONFIG.value,
            ActionType.PERMISSION_GRANT.value,
            ActionType.PERMISSION_REVOKE.value,
            ActionType.ONLUS_APPROVE.value,
            ActionType.TRANSACTION_REFUND.value
        ]
        return self.action_type in sensitive_actions

    def requires_approval(self) -> bool:
        """Check if this action requires approval from another admin"""
        approval_required_actions = [
            ActionType.USER_DELETE.value,
            ActionType.ADMIN_DELETE.value,
            ActionType.ONLUS_APPROVE.value,
            ActionType.TRANSACTION_REFUND.value,
            ActionType.SYSTEM_CONFIG.value
        ]
        return self.action_type in approval_required_actions

    def get_risk_level(self) -> str:
        """Get risk level of the action"""
        high_risk_actions = [
            ActionType.USER_DELETE.value,
            ActionType.ADMIN_DELETE.value,
            ActionType.SYSTEM_CONFIG.value,
            ActionType.FINANCIAL_AUDIT.value
        ]

        medium_risk_actions = [
            ActionType.USER_SUSPEND.value,
            ActionType.ONLUS_APPROVE.value,
            ActionType.CONTENT_REMOVE.value,
            ActionType.TRANSACTION_REFUND.value
        ]

        if self.action_type in high_risk_actions:
            return "high"
        elif self.action_type in medium_risk_actions:
            return "medium"
        else:
            return "low"

    @staticmethod
    def create_user_action(admin_id: str, action_type: str, user_id: str,
                          reason: str = None, details: Dict[str, Any] = None,
                          ip_address: str = None) -> 'AdminAction':
        """Create a user management action"""
        return AdminAction(
            admin_id=admin_id,
            action_type=action_type,
            target_type=TargetType.USER.value,
            target_id=user_id,
            reason=reason,
            action_details=details or {},
            ip_address=ip_address
        )

    @staticmethod
    def create_content_action(admin_id: str, action_type: str, content_id: str,
                             content_type: str = None, reason: str = None,
                             details: Dict[str, Any] = None,
                             ip_address: str = None) -> 'AdminAction':
        """Create a content moderation action"""
        action_details = details or {}
        if content_type:
            action_details['content_type'] = content_type

        return AdminAction(
            admin_id=admin_id,
            action_type=action_type,
            target_type=TargetType.CONTENT.value,
            target_id=content_id,
            reason=reason,
            action_details=action_details,
            ip_address=ip_address
        )

    @staticmethod
    def create_financial_action(admin_id: str, action_type: str, transaction_id: str = None,
                               amount: float = None, reason: str = None,
                               details: Dict[str, Any] = None,
                               ip_address: str = None) -> 'AdminAction':
        """Create a financial action"""
        action_details = details or {}
        if amount is not None:
            action_details['amount'] = amount

        return AdminAction(
            admin_id=admin_id,
            action_type=action_type,
            target_type=TargetType.TRANSACTION.value,
            target_id=transaction_id,
            reason=reason,
            action_details=action_details,
            ip_address=ip_address
        )

    @staticmethod
    def create_system_action(admin_id: str, action_type: str, component: str = None,
                            reason: str = None, details: Dict[str, Any] = None,
                            ip_address: str = None) -> 'AdminAction':
        """Create a system action"""
        action_details = details or {}
        if component:
            action_details['component'] = component

        return AdminAction(
            admin_id=admin_id,
            action_type=action_type,
            target_type=TargetType.SYSTEM.value,
            reason=reason,
            action_details=action_details,
            ip_address=ip_address
        )

    @staticmethod
    def create_security_action(admin_id: str, action_type: str, ip_address: str = None,
                              details: Dict[str, Any] = None) -> 'AdminAction':
        """Create a security-related action"""
        action_details = details or {}
        if ip_address:
            action_details['ip_address'] = ip_address

        return AdminAction(
            admin_id=admin_id,
            action_type=action_type,
            target_type=TargetType.SESSION.value,
            action_details=action_details,
            ip_address=ip_address
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            '_id': str(self._id) if self._id else None,
            'admin_id': self.admin_id,
            'action_type': self.action_type,
            'target_type': self.target_type,
            'target_id': self.target_id,
            'action_details': self.action_details,
            'reason': self.reason,
            'status': self.status,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'session_id': self.session_id,
            'result': self.result,
            'execution_time_ms': self.execution_time_ms,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'risk_level': self.get_risk_level(),
            'is_sensitive': self.is_sensitive_action(),
            'requires_approval': self.requires_approval()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AdminAction':
        """Create AdminAction instance from dictionary"""
        timestamp = None
        if data.get('timestamp'):
            if isinstance(data['timestamp'], str):
                timestamp = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
            else:
                timestamp = data['timestamp']

        return cls(
            _id=str(data['_id']) if data.get('_id') else None,
            admin_id=data['admin_id'],
            action_type=data['action_type'],
            target_type=data['target_type'],
            target_id=data.get('target_id'),
            action_details=data.get('action_details', {}),
            reason=data.get('reason'),
            status=data.get('status', ActionStatus.SUCCESS.value),
            ip_address=data.get('ip_address'),
            user_agent=data.get('user_agent'),
            session_id=data.get('session_id'),
            result=data.get('result', {}),
            execution_time_ms=data.get('execution_time_ms'),
            timestamp=timestamp
        )

    def __repr__(self):
        return f"<AdminAction {self.action_type} by {self.admin_id} on {self.target_type}:{self.target_id}>"