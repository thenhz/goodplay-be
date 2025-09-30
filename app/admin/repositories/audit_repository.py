import os
from typing import Optional, List, Dict, Any
from bson import ObjectId
from datetime import datetime, timezone, timedelta
from app.core.repositories.base_repository import BaseRepository
from app.admin.models.admin_action import AdminAction, ActionType, TargetType, ActionStatus

class AuditRepository(BaseRepository):
    def __init__(self):
        super().__init__("admin_actions")

    def create_indexes(self):
        if self.collection is None or os.getenv('TESTING') == 'true':
            return

        try:
            # Index for admin_id for filtering actions by admin
            self.collection.create_index("admin_id")

            # Index for action_type for filtering by action type
            self.collection.create_index("action_type")

            # Index for target_type for filtering by target type
            self.collection.create_index("target_type")

            # Index for target_id for finding actions on specific targets
            self.collection.create_index("target_id")

            # Index for timestamp for time-based queries
            self.collection.create_index("timestamp")

            # Index for status for filtering by action status
            self.collection.create_index("status")

            # Compound index for admin and timestamp
            self.collection.create_index([("admin_id", 1), ("timestamp", -1)])

            # Compound index for action type and timestamp
            self.collection.create_index([("action_type", 1), ("timestamp", -1)])

            # Compound index for target type and target id
            self.collection.create_index([("target_type", 1), ("target_id", 1)])

            # Index for IP address for security analysis
            self.collection.create_index("ip_address")

            # Index for session_id for session tracking
            self.collection.create_index("session_id")

            # TTL index to automatically expire old audit logs (2 years)
            self.collection.create_index("timestamp", expireAfterSeconds=63072000)  # 2 years

        except Exception as e:
            print(f"Warning: Could not create indexes for admin_actions: {str(e)}")

    def create_action(self, action: AdminAction) -> str:
        """Create a new admin action log entry"""
        action_data = action.to_dict()

        # Remove _id if None to let MongoDB generate it
        if action_data.get('_id') is None:
            action_data.pop('_id', None)

        return self.create(action_data)

    def find_action_by_id(self, action_id: str) -> Optional[AdminAction]:
        """Find action by ID"""
        data = self.find_by_id(action_id)
        if data:
            return AdminAction.from_dict(data)
        return None

    def find_actions_by_admin(self, admin_id: str, limit: int = 50,
                             skip: int = None, start_time: datetime = None,
                             end_time: datetime = None) -> List[AdminAction]:
        """Find actions performed by a specific admin"""
        filter_dict = {"admin_id": admin_id}

        if start_time or end_time:
            time_filter = {}
            if start_time:
                time_filter["$gte"] = start_time
            if end_time:
                time_filter["$lte"] = end_time
            filter_dict["timestamp"] = time_filter

        data_list = self.find_many(filter_dict, limit=limit, skip=skip,
                                  sort=[("timestamp", -1)])
        return [AdminAction.from_dict(data) for data in data_list]

    def find_actions_by_type(self, action_type: str, limit: int = 50,
                           start_time: datetime = None,
                           end_time: datetime = None) -> List[AdminAction]:
        """Find actions by type"""
        filter_dict = {"action_type": action_type}

        if start_time or end_time:
            time_filter = {}
            if start_time:
                time_filter["$gte"] = start_time
            if end_time:
                time_filter["$lte"] = end_time
            filter_dict["timestamp"] = time_filter

        data_list = self.find_many(filter_dict, limit=limit,
                                  sort=[("timestamp", -1)])
        return [AdminAction.from_dict(data) for data in data_list]

    def find_actions_by_target(self, target_type: str, target_id: str = None,
                             limit: int = 50) -> List[AdminAction]:
        """Find actions performed on a specific target"""
        filter_dict = {"target_type": target_type}
        if target_id:
            filter_dict["target_id"] = target_id

        data_list = self.find_many(filter_dict, limit=limit,
                                  sort=[("timestamp", -1)])
        return [AdminAction.from_dict(data) for data in data_list]

    def find_actions_in_time_range(self, start_time: datetime, end_time: datetime,
                                  admin_id: str = None, action_types: List[str] = None,
                                  limit: int = 100) -> List[AdminAction]:
        """Find actions within a time range"""
        filter_dict = {
            "timestamp": {
                "$gte": start_time,
                "$lte": end_time
            }
        }

        if admin_id:
            filter_dict["admin_id"] = admin_id

        if action_types:
            filter_dict["action_type"] = {"$in": action_types}

        data_list = self.find_many(filter_dict, limit=limit,
                                  sort=[("timestamp", -1)])
        return [AdminAction.from_dict(data) for data in data_list]

    def find_failed_actions(self, hours: int = 24, limit: int = 50) -> List[AdminAction]:
        """Find failed actions in the last N hours"""
        start_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        filter_dict = {
            "status": ActionStatus.FAILED.value,
            "timestamp": {"$gte": start_time}
        }

        data_list = self.find_many(filter_dict, limit=limit,
                                  sort=[("timestamp", -1)])
        return [AdminAction.from_dict(data) for data in data_list]

    def find_sensitive_actions(self, hours: int = 24, limit: int = 50) -> List[AdminAction]:
        """Find sensitive actions in the last N hours"""
        start_time = datetime.now(timezone.utc) - timedelta(hours=hours)

        sensitive_action_types = [
            ActionType.USER_DELETE.value,
            ActionType.ADMIN_DELETE.value,
            ActionType.FINANCIAL_AUDIT.value,
            ActionType.SYSTEM_CONFIG.value,
            ActionType.PERMISSION_GRANT.value,
            ActionType.PERMISSION_REVOKE.value,
            ActionType.ONLUS_APPROVE.value,
            ActionType.TRANSACTION_REFUND.value
        ]

        filter_dict = {
            "action_type": {"$in": sensitive_action_types},
            "timestamp": {"$gte": start_time}
        }

        data_list = self.find_many(filter_dict, limit=limit,
                                  sort=[("timestamp", -1)])
        return [AdminAction.from_dict(data) for data in data_list]

    def find_actions_by_ip(self, ip_address: str, hours: int = 24,
                          limit: int = 50) -> List[AdminAction]:
        """Find actions from a specific IP address"""
        start_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        filter_dict = {
            "ip_address": ip_address,
            "timestamp": {"$gte": start_time}
        }

        data_list = self.find_many(filter_dict, limit=limit,
                                  sort=[("timestamp", -1)])
        return [AdminAction.from_dict(data) for data in data_list]

    def update_action_status(self, action_id: str, status: str,
                           result: Dict[str, Any] = None) -> bool:
        """Update action status and result"""
        update_data = {"status": status}
        if result:
            update_data["result"] = result

        return self.update_by_id(action_id, update_data)

    def get_action_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """Get action statistics for the last N hours"""
        if not self.collection:
            return {}

        try:
            start_time = datetime.now(timezone.utc) - timedelta(hours=hours)

            # Total actions
            total_actions = self.count({"timestamp": {"$gte": start_time}})

            # Actions by status
            status_pipeline = [
                {"$match": {"timestamp": {"$gte": start_time}}},
                {"$group": {"_id": "$status", "count": {"$sum": 1}}}
            ]
            status_results = list(self.collection.aggregate(status_pipeline))
            status_counts = {result["_id"]: result["count"] for result in status_results}

            # Actions by type
            type_pipeline = [
                {"$match": {"timestamp": {"$gte": start_time}}},
                {"$group": {"_id": "$action_type", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 10}
            ]
            type_results = list(self.collection.aggregate(type_pipeline))
            type_counts = {result["_id"]: result["count"] for result in type_results}

            # Actions by admin
            admin_pipeline = [
                {"$match": {"timestamp": {"$gte": start_time}}},
                {"$group": {"_id": "$admin_id", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 10}
            ]
            admin_results = list(self.collection.aggregate(admin_pipeline))
            admin_counts = {result["_id"]: result["count"] for result in admin_results}

            # Failed actions count
            failed_actions = self.count({
                "status": ActionStatus.FAILED.value,
                "timestamp": {"$gte": start_time}
            })

            # Sensitive actions count
            sensitive_action_types = [
                ActionType.USER_DELETE.value,
                ActionType.ADMIN_DELETE.value,
                ActionType.FINANCIAL_AUDIT.value,
                ActionType.SYSTEM_CONFIG.value
            ]
            sensitive_actions = self.count({
                "action_type": {"$in": sensitive_action_types},
                "timestamp": {"$gte": start_time}
            })

            # Average execution time
            execution_time_pipeline = [
                {"$match": {
                    "timestamp": {"$gte": start_time},
                    "execution_time_ms": {"$exists": True, "$ne": None}
                }},
                {"$group": {
                    "_id": None,
                    "avg_execution_time": {"$avg": "$execution_time_ms"},
                    "max_execution_time": {"$max": "$execution_time_ms"},
                    "min_execution_time": {"$min": "$execution_time_ms"}
                }}
            ]
            execution_results = list(self.collection.aggregate(execution_time_pipeline))
            execution_stats = execution_results[0] if execution_results else {}

            return {
                'total_actions': total_actions,
                'status_distribution': status_counts,
                'action_type_distribution': type_counts,
                'admin_activity': admin_counts,
                'failed_actions': failed_actions,
                'sensitive_actions': sensitive_actions,
                'execution_time_stats': execution_stats,
                'time_period_hours': hours
            }

        except Exception as e:
            print(f"Error getting action statistics: {str(e)}")
            return {}

    def get_audit_trail(self, target_type: str, target_id: str,
                       limit: int = 50) -> List[AdminAction]:
        """Get complete audit trail for a specific target"""
        filter_dict = {
            "target_type": target_type,
            "target_id": target_id
        }

        data_list = self.find_many(filter_dict, limit=limit,
                                  sort=[("timestamp", -1)])
        return [AdminAction.from_dict(data) for data in data_list]

    def get_admin_activity_summary(self, admin_id: str,
                                  days: int = 30) -> Dict[str, Any]:
        """Get activity summary for a specific admin"""
        if not self.collection:
            return {}

        try:
            start_time = datetime.now(timezone.utc) - timedelta(days=days)

            filter_dict = {
                "admin_id": admin_id,
                "timestamp": {"$gte": start_time}
            }

            # Total actions
            total_actions = self.count(filter_dict)

            # Actions by type
            type_pipeline = [
                {"$match": filter_dict},
                {"$group": {"_id": "$action_type", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]
            type_results = list(self.collection.aggregate(type_pipeline))
            action_types = {result["_id"]: result["count"] for result in type_results}

            # Actions by day
            daily_pipeline = [
                {"$match": filter_dict},
                {"$group": {
                    "_id": {
                        "year": {"$year": "$timestamp"},
                        "month": {"$month": "$timestamp"},
                        "day": {"$dayOfMonth": "$timestamp"}
                    },
                    "count": {"$sum": 1}
                }},
                {"$sort": {"_id": 1}}
            ]
            daily_results = list(self.collection.aggregate(daily_pipeline))
            daily_activity = [
                {
                    "date": f"{result['_id']['year']}-{result['_id']['month']:02d}-{result['_id']['day']:02d}",
                    "count": result["count"]
                }
                for result in daily_results
            ]

            # Recent actions
            recent_actions = self.find_actions_by_admin(admin_id, limit=10)

            # Failed actions
            failed_count = self.count({
                **filter_dict,
                "status": ActionStatus.FAILED.value
            })

            return {
                'admin_id': admin_id,
                'total_actions': total_actions,
                'action_types': action_types,
                'daily_activity': daily_activity,
                'recent_actions': [action.to_dict() for action in recent_actions],
                'failed_actions': failed_count,
                'period_days': days
            }

        except Exception as e:
            print(f"Error getting admin activity summary: {str(e)}")
            return {}

    def find_suspicious_activity(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Find potentially suspicious admin activity"""
        if not self.collection:
            return []

        try:
            start_time = datetime.now(timezone.utc) - timedelta(hours=hours)
            suspicious_activities = []

            # Multiple failed actions from same IP
            failed_ip_pipeline = [
                {"$match": {
                    "status": ActionStatus.FAILED.value,
                    "timestamp": {"$gte": start_time},
                    "ip_address": {"$exists": True, "$ne": None}
                }},
                {"$group": {
                    "_id": "$ip_address",
                    "count": {"$sum": 1},
                    "admin_ids": {"$addToSet": "$admin_id"}
                }},
                {"$match": {"count": {"$gte": 5}}}
            ]
            failed_ip_results = list(self.collection.aggregate(failed_ip_pipeline))

            for result in failed_ip_results:
                suspicious_activities.append({
                    'type': 'multiple_failed_logins',
                    'ip_address': result['_id'],
                    'count': result['count'],
                    'admin_ids': result['admin_ids'],
                    'severity': 'high' if result['count'] >= 10 else 'medium'
                })

            # Unusual action patterns
            pattern_pipeline = [
                {"$match": {"timestamp": {"$gte": start_time}}},
                {"$group": {
                    "_id": {
                        "admin_id": "$admin_id",
                        "action_type": "$action_type"
                    },
                    "count": {"$sum": 1}
                }},
                {"$match": {"count": {"$gte": 20}}}  # More than 20 same actions
            ]
            pattern_results = list(self.collection.aggregate(pattern_pipeline))

            for result in pattern_results:
                suspicious_activities.append({
                    'type': 'unusual_action_pattern',
                    'admin_id': result['_id']['admin_id'],
                    'action_type': result['_id']['action_type'],
                    'count': result['count'],
                    'severity': 'medium'
                })

            # Off-hours activity (outside 9-17)
            current_hour = datetime.now(timezone.utc).hour
            if current_hour < 9 or current_hour > 17:
                off_hours_count = self.count({
                    "timestamp": {"$gte": start_time}
                })

                if off_hours_count > 0:
                    suspicious_activities.append({
                        'type': 'off_hours_activity',
                        'count': off_hours_count,
                        'hour': current_hour,
                        'severity': 'low'
                    })

            return suspicious_activities

        except Exception as e:
            print(f"Error finding suspicious activity: {str(e)}")
            return []

    def cleanup_old_actions(self, days: int = 730) -> int:  # 2 years default
        """Clean up audit logs older than specified days"""
        if not self.collection:
            return 0

        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(days=days)
            result = self.collection.delete_many({"timestamp": {"$lt": cutoff_time}})
            return result.deleted_count

        except Exception as e:
            print(f"Error cleaning up old audit logs: {str(e)}")
            return 0

    def export_audit_data(self, start_time: datetime, end_time: datetime,
                         admin_id: str = None, action_types: List[str] = None) -> List[Dict[str, Any]]:
        """Export audit data for compliance reporting"""
        actions = self.find_actions_in_time_range(
            start_time, end_time, admin_id, action_types, limit=None
        )

        return [
            {
                'timestamp': action.timestamp.isoformat(),
                'admin_id': action.admin_id,
                'action_type': action.action_type,
                'target_type': action.target_type,
                'target_id': action.target_id,
                'status': action.status,
                'ip_address': action.ip_address,
                'reason': action.reason,
                'execution_time_ms': action.execution_time_ms,
                'risk_level': action.get_risk_level()
            }
            for action in actions
        ]