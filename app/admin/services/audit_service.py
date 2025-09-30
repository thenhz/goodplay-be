"""
Audit Service for Admin Module
Handles audit logging, compliance, and audit trail management
"""

import hashlib
import json
import csv
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Tuple, Optional, Any
from flask import current_app
from io import StringIO

from app.admin.repositories.audit_repository import AuditRepository
from app.admin.models.admin_action import AdminAction, ActionType, TargetType


class AuditService:
    """Service for handling audit operations"""

    def __init__(self):
        self.audit_repository = AuditRepository()
        self.retention_days = 365  # Default retention period
        self.critical_actions = [
            ActionType.USER_DELETE.value,
            ActionType.SYSTEM_CONFIG.value,
            ActionType.ADMIN_CREATE.value,
            ActionType.ADMIN_DELETE.value
        ]

    def log_admin_action(self, admin_id: str, action_type: str, target_type: str,
                        target_id: str, details: Optional[Dict] = None) -> Tuple[bool, str]:
        """Log an admin action to the audit trail"""
        try:
            # Create admin action
            action = AdminAction(
                admin_id=admin_id,
                action_type=action_type,
                target_type=target_type,
                target_id=target_id,
                details=details or {},
                timestamp=datetime.now(timezone.utc)
            )

            # Calculate integrity hash
            action.integrity_hash = self.calculate_log_hash(action)

            # Save to repository
            success = self.audit_repository.create(action)

            if success:
                # Check if this is a critical action that needs real-time alerting
                if self.should_trigger_real_time_alert(action):
                    self._send_real_time_alert(action)

                current_app.logger.info(f"Audit log created: {action_type} by {admin_id}")
                return True, "ACTION_LOGGED_SUCCESS"
            else:
                return False, "ACTION_LOG_FAILED"

        except Exception as e:
            current_app.logger.error(f"Error logging admin action: {str(e)}")
            return False, "ACTION_LOG_FAILED"

    def get_audit_logs(self, filters: Optional[Dict] = None) -> Tuple[bool, str, List[AdminAction]]:
        """Retrieve audit logs with optional filters"""
        try:
            if filters:
                logs = self.audit_repository.get_logs_with_filters(filters)
            else:
                logs = self.audit_repository.get_all()

            current_app.logger.info(f"Retrieved {len(logs)} audit logs")
            return True, "AUDIT_LOGS_RETRIEVED", logs

        except Exception as e:
            current_app.logger.error(f"Error retrieving audit logs: {str(e)}")
            return False, "AUDIT_LOGS_FAILED", []

    def enforce_retention_policy(self) -> Tuple[bool, str, int]:
        """Enforce audit log retention policy"""
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=self.retention_days)
            old_logs = self.audit_repository.get_logs_older_than(cutoff_date)

            archived_count = 0
            for log in old_logs:
                # Archive instead of delete for compliance
                if self._archive_log(log):
                    archived_count += 1

            current_app.logger.info(f"Archived {archived_count} old audit logs")
            return True, "RETENTION_POLICY_ENFORCED", archived_count

        except Exception as e:
            current_app.logger.error(f"Error enforcing retention policy: {str(e)}")
            return False, "RETENTION_POLICY_FAILED", 0

    def calculate_log_hash(self, action: AdminAction) -> str:
        """Calculate integrity hash for audit log"""
        try:
            # Create a canonical string representation
            hash_data = {
                'admin_id': action.admin_id,
                'action_type': action.action_type,
                'target_type': action.target_type,
                'target_id': action.target_id,
                'timestamp': action.timestamp.isoformat(),
                'details': action.details
            }

            # Convert to JSON string with sorted keys for consistency
            canonical_str = json.dumps(hash_data, sort_keys=True, separators=(',', ':'))

            # Calculate SHA-256 hash
            return hashlib.sha256(canonical_str.encode('utf-8')).hexdigest()

        except Exception as e:
            current_app.logger.error(f"Error calculating log hash: {str(e)}")
            return ""

    def verify_log_integrity(self, action: AdminAction, expected_hash: str) -> bool:
        """Verify the integrity of an audit log"""
        try:
            calculated_hash = self.calculate_log_hash(action)
            return calculated_hash == expected_hash

        except Exception as e:
            current_app.logger.error(f"Error verifying log integrity: {str(e)}")
            return False

    def generate_audit_report(self, start_date: str, end_date: str,
                            report_type: str = "summary") -> Tuple[bool, str, Dict]:
        """Generate comprehensive audit report"""
        try:
            # Get logs in date range
            logs = self.audit_repository.get_logs_in_range(start_date, end_date)

            if report_type == "summary":
                report = self._generate_summary_report(logs)
            elif report_type == "detailed":
                report = self._generate_detailed_report(logs)
            elif report_type == "compliance":
                report = self._generate_compliance_report(logs)
            else:
                return False, "INVALID_REPORT_TYPE", {}

            report['metadata'] = {
                'generated_at': datetime.now(timezone.utc).isoformat(),
                'period': f"{start_date} to {end_date}",
                'total_logs': len(logs),
                'report_type': report_type
            }

            return True, "AUDIT_REPORT_GENERATED", report

        except Exception as e:
            current_app.logger.error(f"Error generating audit report: {str(e)}")
            return False, "AUDIT_REPORT_FAILED", {}

    def should_trigger_real_time_alert(self, action: AdminAction) -> bool:
        """Determine if action should trigger real-time alert"""
        # Critical actions always trigger alerts
        if action.action_type in self.critical_actions:
            return True

        # High-risk actions
        if action.get_risk_level() == "high":
            return True

        # Multiple failed attempts
        if "failed" in action.action_type and action.details.get("consecutive_failures", 0) > 3:
            return True

        return False

    def search_audit_logs(self, query: str, search_fields: List[str]) -> Tuple[bool, str, List[AdminAction]]:
        """Search audit logs with text query"""
        try:
            results = self.audit_repository.search_logs(query, search_fields)
            return True, "SEARCH_COMPLETED", results

        except Exception as e:
            current_app.logger.error(f"Error searching audit logs: {str(e)}")
            return False, "SEARCH_FAILED", []

    def export_audit_logs(self, format: str, date_range: Tuple[str, str]) -> Tuple[bool, str, str]:
        """Export audit logs in specified format"""
        try:
            start_date, end_date = date_range
            logs = self.audit_repository.get_logs_for_export(start_date, end_date)

            if format.lower() == "csv":
                content = self._export_to_csv(logs)
            elif format.lower() == "json":
                content = self._export_to_json(logs)
            else:
                return False, "UNSUPPORTED_FORMAT", ""

            return True, "EXPORT_COMPLETED", content

        except Exception as e:
            current_app.logger.error(f"Error exporting audit logs: {str(e)}")
            return False, "EXPORT_FAILED", ""

    def _generate_summary_report(self, logs: List[AdminAction]) -> Dict:
        """Generate summary audit report"""
        # Count actions by type
        action_counts = {}
        admin_activity = {}
        risk_levels = {"low": 0, "medium": 0, "high": 0}

        for log in logs:
            # Count by action type
            action_counts[log.action_type] = action_counts.get(log.action_type, 0) + 1

            # Count by admin
            admin_activity[log.admin_id] = admin_activity.get(log.admin_id, 0) + 1

            # Count by risk level
            risk_level = log.get_risk_level()
            risk_levels[risk_level] = risk_levels.get(risk_level, 0) + 1

        return {
            'total_actions': len(logs),
            'action_breakdown': action_counts,
            'admin_activity': admin_activity,
            'risk_distribution': risk_levels,
            'most_active_admin': max(admin_activity.items(), key=lambda x: x[1]) if admin_activity else None,
            'most_common_action': max(action_counts.items(), key=lambda x: x[1]) if action_counts else None
        }

    def _generate_detailed_report(self, logs: List[AdminAction]) -> Dict:
        """Generate detailed audit report"""
        return {
            'total_actions': len(logs),
            'actions': [log.to_dict() for log in logs],
            'timeline': self._create_timeline(logs),
            'patterns': self._analyze_patterns(logs)
        }

    def _generate_compliance_report(self, logs: List[AdminAction]) -> Dict:
        """Generate compliance-focused audit report"""
        # Filter for compliance-relevant actions
        compliance_actions = [
            log for log in logs
            if any(keyword in log.action_type.lower()
                  for keyword in ['data', 'access', 'export', 'delete', 'privacy'])
        ]

        return {
            'total_compliance_actions': len(compliance_actions),
            'data_access_logs': [log.to_dict() for log in compliance_actions if 'access' in log.action_type],
            'data_export_logs': [log.to_dict() for log in compliance_actions if 'export' in log.action_type],
            'data_deletion_logs': [log.to_dict() for log in compliance_actions if 'delete' in log.action_type],
            'privacy_actions': [log.to_dict() for log in compliance_actions if 'privacy' in log.action_type]
        }

    def _export_to_csv(self, logs: List[AdminAction]) -> str:
        """Export logs to CSV format"""
        output = StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow([
            'admin_id', 'action_type', 'target_type', 'target_id',
            'timestamp', 'risk_level', 'details'
        ])

        # Write data
        for log in logs:
            writer.writerow([
                log.admin_id,
                log.action_type,
                log.target_type,
                log.target_id,
                log.timestamp.isoformat(),
                log.get_risk_level(),
                json.dumps(log.details) if log.details else ""
            ])

        return output.getvalue()

    def _export_to_json(self, logs: List[AdminAction]) -> str:
        """Export logs to JSON format"""
        export_data = {
            'exported_at': datetime.now(timezone.utc).isoformat(),
            'total_logs': len(logs),
            'logs': [log.to_dict() for log in logs]
        }

        return json.dumps(export_data, indent=2, default=str)

    def _create_timeline(self, logs: List[AdminAction]) -> List[Dict]:
        """Create timeline of actions"""
        # Sort logs by timestamp
        sorted_logs = sorted(logs, key=lambda x: x.timestamp)

        timeline = []
        for log in sorted_logs:
            timeline.append({
                'timestamp': log.timestamp.isoformat(),
                'admin_id': log.admin_id,
                'action_type': log.action_type,
                'target': f"{log.target_type}:{log.target_id}",
                'risk_level': log.get_risk_level()
            })

        return timeline

    def _analyze_patterns(self, logs: List[AdminAction]) -> Dict:
        """Analyze patterns in audit logs"""
        patterns = {
            'peak_hours': {},
            'frequent_actions': {},
            'admin_behavior': {}
        }

        # Analyze peak hours
        for log in logs:
            hour = log.timestamp.hour
            patterns['peak_hours'][hour] = patterns['peak_hours'].get(hour, 0) + 1

        # Find most frequent actions
        action_freq = {}
        for log in logs:
            action_freq[log.action_type] = action_freq.get(log.action_type, 0) + 1

        patterns['frequent_actions'] = dict(sorted(action_freq.items(), key=lambda x: x[1], reverse=True)[:10])

        return patterns

    def _archive_log(self, log: AdminAction) -> bool:
        """Archive old log (placeholder for archival system)"""
        try:
            # In real implementation, this would move logs to archive storage
            # For now, we'll just mark as archived
            return True

        except Exception as e:
            current_app.logger.error(f"Error archiving log: {str(e)}")
            return False

    def _send_real_time_alert(self, action: AdminAction):
        """Send real-time alert for critical actions"""
        try:
            # In real implementation, this would send alerts via email, Slack, etc.
            current_app.logger.warning(f"CRITICAL ACTION ALERT: {action.action_type} by {action.admin_id}")

        except Exception as e:
            current_app.logger.error(f"Error sending real-time alert: {str(e)}")