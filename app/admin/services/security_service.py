"""
Security Service for Admin Module
Handles security monitoring, threat detection, and compliance
"""

import hashlib
import ipaddress
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Tuple, Optional, Any
from flask import current_app

from app.admin.repositories.audit_repository import AuditRepository
from app.admin.repositories.admin_repository import AdminRepository
from app.admin.models.admin_action import AdminAction, ActionType


class SecurityService:
    """Service for handling admin security operations"""

    def __init__(self):
        self.audit_repository = AuditRepository()
        self.admin_repository = AdminRepository()
        self.max_failed_attempts = 5
        self.lockout_duration_hours = 24
        self.brute_force_threshold = 10
        self.brute_force_window_minutes = 15

    def detect_suspicious_activity(self) -> Tuple[bool, str, List[Dict]]:
        """Detect suspicious activity patterns"""
        try:
            alerts = []

            # Check for multiple failed login attempts
            failed_logins = self.audit_repository.get_actions_by_type("failed_login_attempt")

            # Group by IP address
            ip_failures = {}
            for action in failed_logins:
                ip = action.details.get('ip_address', 'unknown')
                if ip not in ip_failures:
                    ip_failures[ip] = []
                ip_failures[ip].append(action)

            # Alert on multiple failures from same IP
            for ip, failures in ip_failures.items():
                if len(failures) >= 5:
                    alerts.append({
                        'type': 'multiple_failed_logins',
                        'severity': 'high',
                        'description': f'Multiple failed login attempts from IP {ip}',
                        'count': len(failures),
                        'ip_address': ip,
                        'timestamp': datetime.now(timezone.utc).isoformat()
                    })

            # Check for privilege escalation attempts
            escalation_alerts = self._detect_privilege_escalation_attempts()
            alerts.extend(escalation_alerts)

            # Check for unusual access patterns
            access_alerts = self._detect_unusual_access_patterns()
            alerts.extend(access_alerts)

            current_app.logger.info(f"Detected {len(alerts)} security alerts")
            return True, "SECURITY_ANALYSIS_COMPLETE", alerts

        except Exception as e:
            current_app.logger.error(f"Error detecting suspicious activity: {str(e)}")
            return False, "SECURITY_ANALYSIS_FAILED", []

    def analyze_access_patterns(self, admin_id: str) -> List[Dict]:
        """Analyze access patterns for specific admin"""
        try:
            alerts = []
            recent_actions = self.audit_repository.get_recent_actions(admin_id, hours=24)

            # Check for unusual time access
            for action in recent_actions:
                hour = action.timestamp.hour
                if hour < 6 or hour > 22:  # Outside business hours
                    alerts.append({
                        'type': 'unusual_time_access',
                        'severity': 'medium',
                        'description': f'Access outside business hours at {hour}:00',
                        'admin_id': admin_id,
                        'timestamp': action.timestamp.isoformat()
                    })

            # Check for access from multiple locations
            ip_addresses = set()
            for action in recent_actions:
                if 'ip_address' in action.details:
                    ip_addresses.add(action.details['ip_address'])

            if len(ip_addresses) > 3:  # Multiple IPs in 24h
                alerts.append({
                    'type': 'multiple_ip_access',
                    'severity': 'medium',
                    'description': f'Access from {len(ip_addresses)} different IP addresses',
                    'admin_id': admin_id,
                    'ip_count': len(ip_addresses)
                })

            return alerts

        except Exception as e:
            current_app.logger.error(f"Error analyzing access patterns: {str(e)}")
            return []

    def detect_privilege_escalation(self, admin_id: str) -> List[Dict]:
        """Detect privilege escalation attempts"""
        try:
            alerts = []
            admin_actions = self.audit_repository.get_actions_by_admin(admin_id)

            # Look for attempts to access higher privilege functions
            for action in admin_actions:
                if action.details and not action.details.get('has_permission', True):
                    alerts.append({
                        'type': 'privilege_escalation_attempt',
                        'severity': 'high',
                        'description': f'Attempted access to {action.action_type} without permission',
                        'admin_id': admin_id,
                        'action_type': action.action_type,
                        'timestamp': action.timestamp.isoformat()
                    })

            return alerts

        except Exception as e:
            current_app.logger.error(f"Error detecting privilege escalation: {str(e)}")
            return []

    def detect_brute_force_attack(self, ip_address: str) -> bool:
        """Detect brute force attacks from IP"""
        try:
            # Get failed attempts in the last window
            since = datetime.now(timezone.utc) - timedelta(minutes=self.brute_force_window_minutes)
            failed_attempts = self.audit_repository.get_actions_in_timeframe(
                "failed_login_attempt", since, datetime.now(timezone.utc)
            )

            # Count attempts from this IP
            ip_attempts = [
                attempt for attempt in failed_attempts
                if attempt.details.get('ip_address') == ip_address
            ]

            return len(ip_attempts) >= self.brute_force_threshold

        except Exception as e:
            current_app.logger.error(f"Error detecting brute force: {str(e)}")
            return False

    def should_lock_account(self, admin_user) -> bool:
        """Determine if account should be locked"""
        return admin_user.failed_login_attempts >= self.max_failed_attempts

    def lock_account(self, username: str, reason: str) -> Tuple[bool, str]:
        """Lock admin account"""
        try:
            admin_user = self.admin_repository.find_by_username(username)
            if not admin_user:
                return False, "USER_NOT_FOUND"

            # Set lock parameters
            admin_user.is_locked = True
            admin_user.locked_until = datetime.now(timezone.utc) + timedelta(hours=self.lockout_duration_hours)
            admin_user.lock_reason = reason

            # Update in database
            success = self.admin_repository.update(admin_user.id, {
                'is_locked': True,
                'locked_until': admin_user.locked_until,
                'lock_reason': reason
            })

            if success:
                # Log the lockout
                self.audit_repository.create(AdminAction.create_security_action(
                    admin_id="system",
                    action_type="account_locked",
                    ip_address="",
                    details={"username": username, "reason": reason}
                ))

                current_app.logger.warning(f"Account locked: {username} - {reason}")
                return True, "ACCOUNT_LOCKED_SUCCESS"
            else:
                return False, "ACCOUNT_LOCK_FAILED"

        except Exception as e:
            current_app.logger.error(f"Error locking account: {str(e)}")
            return False, "ACCOUNT_LOCK_FAILED"

    def get_security_audit_trail(self) -> Tuple[bool, str, Dict]:
        """Get comprehensive security audit trail"""
        try:
            security_events = self.audit_repository.get_security_events()

            audit_data = {
                'events': security_events,
                'summary': {
                    'total_events': len(security_events),
                    'login_attempts': len([e for e in security_events if 'login' in e.action_type]),
                    'failed_attempts': len([e for e in security_events if 'failed' in e.action_type]),
                    'lockouts': len([e for e in security_events if 'locked' in e.action_type])
                }
            }

            return True, "AUDIT_TRAIL_SUCCESS", audit_data

        except Exception as e:
            current_app.logger.error(f"Error getting audit trail: {str(e)}")
            return False, "AUDIT_TRAIL_FAILED", {}

    def check_ip_reputation(self, ip_address: str) -> bool:
        """Check IP reputation against threat databases"""
        try:
            # In real implementation, this would check against threat intelligence feeds
            # For now, we'll implement basic checks

            # Check if IP is in private ranges (generally safe)
            try:
                ip = ipaddress.ip_address(ip_address)
                if ip.is_private:
                    return False  # Private IPs are not malicious
            except ValueError:
                return True  # Invalid IP format is suspicious

            # Mock threat database check
            # In production, integrate with services like VirusTotal, AbuseIPDB, etc.
            known_malicious = ["198.51.100.1", "203.0.113.1"]
            return ip_address in known_malicious

        except Exception as e:
            current_app.logger.error(f"Error checking IP reputation: {str(e)}")
            return False

    def detect_session_anomalies(self, session_id: str) -> List[Dict]:
        """Detect session-related anomalies"""
        try:
            alerts = []
            session_activities = self.audit_repository.get_session_activities(session_id)

            # Check for session from multiple IPs
            ip_addresses = set()
            for activity in session_activities:
                if 'ip_address' in activity.details:
                    ip_addresses.add(activity.details['ip_address'])

            if len(ip_addresses) > 1:
                alerts.append({
                    'type': 'session_multiple_ips',
                    'severity': 'high',
                    'description': f'Session {session_id} accessed from multiple IP addresses',
                    'session_id': session_id,
                    'ip_addresses': list(ip_addresses)
                })

            return alerts

        except Exception as e:
            current_app.logger.error(f"Error detecting session anomalies: {str(e)}")
            return []

    def validate_password_strength(self, password: str) -> Tuple[bool, List[str]]:
        """Validate password strength against security policy"""
        issues = []

        # Length check
        if len(password) < 8:
            issues.append("Password must be at least 8 characters long")

        # Character type checks
        if not any(c.isupper() for c in password):
            issues.append("Password must contain at least one uppercase letter")

        if not any(c.islower() for c in password):
            issues.append("Password must contain at least one lowercase letter")

        if not any(c.isdigit() for c in password):
            issues.append("Password must contain at least one number")

        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            issues.append("Password must contain at least one special character")

        # Common password check
        common_passwords = ["password", "123456", "admin", "qwerty"]
        if password.lower() in common_passwords:
            issues.append("Password is too common")

        return len(issues) == 0, issues

    def generate_compliance_report(self, period: str, regulation: str) -> Tuple[bool, str, Dict]:
        """Generate compliance report for regulations like GDPR"""
        try:
            # Get compliance-relevant actions for the period
            compliance_actions = self.audit_repository.get_compliance_actions(period, regulation)

            report = {
                'period': period,
                'regulation': regulation,
                'data_access_events': [],
                'data_export_events': [],
                'data_deletion_events': [],
                'policy_violations': [],
                'summary': {
                    'total_events': len(compliance_actions),
                    'data_accesses': 0,
                    'data_exports': 0,
                    'data_deletions': 0
                }
            }

            # Categorize actions
            for action in compliance_actions:
                if 'data_access' in action.action_type:
                    report['data_access_events'].append(action.to_dict())
                    report['summary']['data_accesses'] += 1
                elif 'data_export' in action.action_type:
                    report['data_export_events'].append(action.to_dict())
                    report['summary']['data_exports'] += 1
                elif 'data_deletion' in action.action_type:
                    report['data_deletion_events'].append(action.to_dict())
                    report['summary']['data_deletions'] += 1

            return True, "COMPLIANCE_REPORT_SUCCESS", report

        except Exception as e:
            current_app.logger.error(f"Error generating compliance report: {str(e)}")
            return False, "COMPLIANCE_REPORT_FAILED", {}

    def _detect_privilege_escalation_attempts(self) -> List[Dict]:
        """Internal method to detect privilege escalation"""
        try:
            alerts = []
            # Get recent actions with permission failures
            recent_actions = self.audit_repository.get_recent_actions_with_failures()

            for action in recent_actions:
                if action.details and not action.details.get('has_permission', True):
                    alerts.append({
                        'type': 'privilege_escalation',
                        'severity': 'high',
                        'description': f'Privilege escalation attempt: {action.action_type}',
                        'admin_id': action.admin_id,
                        'timestamp': action.timestamp.isoformat()
                    })

            return alerts

        except Exception as e:
            current_app.logger.error(f"Error detecting privilege escalation attempts: {str(e)}")
            return []

    def _detect_unusual_access_patterns(self) -> List[Dict]:
        """Internal method to detect unusual access patterns"""
        try:
            alerts = []
            # Get recent login events
            recent_logins = self.audit_repository.get_actions_by_type("admin_login")

            # Check for unusual times, locations, etc.
            for login in recent_logins:
                hour = login.timestamp.hour
                if hour < 6 or hour > 22:  # Outside business hours
                    alerts.append({
                        'type': 'unusual_time_access',
                        'severity': 'medium',
                        'description': f'Login outside business hours at {hour}:00',
                        'admin_id': login.admin_id,
                        'timestamp': login.timestamp.isoformat()
                    })

            return alerts

        except Exception as e:
            current_app.logger.error(f"Error detecting unusual access patterns: {str(e)}")
            return []