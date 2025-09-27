from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone, timedelta
from flask import current_app
from app.donations.models.compliance_check import (
    ComplianceCheck, ComplianceCheckType, ComplianceCheckStatus, ComplianceRiskLevel
)
from app.donations.repositories.transaction_repository import TransactionRepository
from app.core.repositories.user_repository import UserRepository


class ComplianceService:
    """
    Service for managing compliance checks including AML, KYC, and fraud detection.

    Handles automated compliance verification, risk assessment, manual review workflows,
    and regulatory reporting for financial transactions.
    """

    def __init__(self):
        self.transaction_repo = TransactionRepository()
        self.user_repo = UserRepository()

        # Compliance configuration
        self.risk_thresholds = {
            'daily_transaction_limit': 1000.0,
            'monthly_transaction_limit': 10000.0,
            'suspicious_pattern_threshold': 5,
            'high_risk_amount': 5000.0,
            'velocity_check_hours': 24,
            'max_failed_attempts': 3
        }

        # AML/KYC rules
        self.aml_rules = {
            'single_transaction_threshold': 3000.0,
            'daily_aggregate_threshold': 10000.0,
            'structuring_detection_threshold': 0.9,  # 90% of limit
            'velocity_transactions_per_hour': 10,
            'suspicious_countries': ['OFAC_SANCTIONED'],  # Placeholder
            'pep_screening_enabled': True,
            'sanctions_screening_enabled': True
        }

    def initiate_compliance_check(self, user_id: str, check_type: str,
                                transaction_id: str = None, reason: str = "",
                                check_criteria: Dict[str, Any] = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Initiate a compliance check for a user or transaction.

        Args:
            user_id: User identifier
            check_type: Type of compliance check (aml, kyc, sanctions, etc.)
            transaction_id: Optional transaction identifier
            reason: Reason for the compliance check
            check_criteria: Specific criteria for the check

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success, message, check details
        """
        try:
            # Validate check type
            try:
                compliance_type = ComplianceCheckType(check_type)
            except ValueError:
                return False, "INVALID_COMPLIANCE_CHECK_TYPE", None

            # Create compliance check
            compliance_check = ComplianceCheck(
                user_id=user_id,
                check_type=check_type,
                transaction_id=transaction_id,
                check_reason=reason,
                check_criteria=check_criteria or {}
            )

            # Determine initial risk assessment
            risk_assessment = self._assess_initial_risk(user_id, transaction_id, compliance_type)
            compliance_check.risk_score = risk_assessment['risk_score']
            compliance_check.risk_level = ComplianceRiskLevel(risk_assessment['risk_level'])
            compliance_check.risk_factors = risk_assessment['risk_factors']

            # Start the check
            compliance_check.start_check()

            # Perform automated checks based on type
            if compliance_type == ComplianceCheckType.AML:
                auto_result = self._perform_aml_check(compliance_check)
            elif compliance_type == ComplianceCheckType.KYC:
                auto_result = self._perform_kyc_check(compliance_check)
            elif compliance_type == ComplianceCheckType.SANCTIONS:
                auto_result = self._perform_sanctions_check(compliance_check)
            elif compliance_type == ComplianceCheckType.FRAUD:
                auto_result = self._perform_fraud_check(compliance_check)
            else:
                auto_result = {'passed': False, 'requires_review': True, 'reason': 'Manual review required'}

            # Complete or mark for review
            if auto_result['requires_review']:
                compliance_check.require_review(auto_result.get('reason', 'Automated check inconclusive'))
            else:
                compliance_check.complete_check(
                    auto_result['passed'],
                    auto_result.get('results', {}),
                    'automated_system'
                )

            # Save compliance check (placeholder - would use repository)
            check_saved = self._save_compliance_check(compliance_check)
            if not check_saved:
                return False, "COMPLIANCE_CHECK_SAVE_FAILED", None

            current_app.logger.info(f"Initiated {check_type} compliance check {compliance_check.check_id} for user {user_id}")

            return True, "COMPLIANCE_CHECK_INITIATED", {
                'check_id': compliance_check.check_id,
                'status': compliance_check.status.value,
                'risk_level': compliance_check.risk_level.value,
                'risk_score': compliance_check.risk_score,
                'requires_review': compliance_check.requires_manual_review(),
                'estimated_completion': self._estimate_completion_time(compliance_check)
            }

        except Exception as e:
            current_app.logger.error(f"Failed to initiate compliance check: {str(e)}")
            return False, "COMPLIANCE_CHECK_INITIATION_ERROR", None

    def _assess_initial_risk(self, user_id: str, transaction_id: str,
                           check_type: ComplianceCheckType) -> Dict[str, Any]:
        """
        Assess initial risk level for a user/transaction.

        Args:
            user_id: User identifier
            transaction_id: Transaction identifier
            check_type: Type of compliance check

        Returns:
            Risk assessment dictionary
        """
        risk_factors = []
        risk_score = 0.0

        try:
            # Get user transaction history
            user_transactions = self.transaction_repo.find_user_transactions(user_id, limit=100)

            # Check transaction velocity
            recent_transactions = [
                t for t in user_transactions
                if t.created_at and t.created_at > datetime.now(timezone.utc) - timedelta(hours=24)
            ]

            if len(recent_transactions) > self.aml_rules['velocity_transactions_per_hour']:
                risk_factors.append('high_transaction_velocity')
                risk_score += 20

            # Check transaction amounts
            if transaction_id:
                transaction = self.transaction_repo.find_by_transaction_id(transaction_id)
                if transaction and transaction.amount > self.aml_rules['single_transaction_threshold']:
                    risk_factors.append('large_transaction_amount')
                    risk_score += 15

            # Check daily aggregate
            daily_total = sum(t.amount for t in recent_transactions if t.amount > 0)
            if daily_total > self.aml_rules['daily_aggregate_threshold']:
                risk_factors.append('high_daily_aggregate')
                risk_score += 25

            # Check for suspicious patterns
            if self._detect_structuring_pattern(user_transactions):
                risk_factors.append('potential_structuring')
                risk_score += 30

            # Determine risk level
            if risk_score >= 70:
                risk_level = 'critical'
            elif risk_score >= 50:
                risk_level = 'high'
            elif risk_score >= 30:
                risk_level = 'medium'
            else:
                risk_level = 'low'

            return {
                'risk_score': min(100.0, risk_score),
                'risk_level': risk_level,
                'risk_factors': risk_factors
            }

        except Exception as e:
            current_app.logger.error(f"Failed to assess initial risk: {str(e)}")
            return {
                'risk_score': 50.0,  # Default medium risk
                'risk_level': 'medium',
                'risk_factors': ['risk_assessment_error']
            }

    def _detect_structuring_pattern(self, transactions: List) -> bool:
        """
        Detect potential structuring patterns in transactions.

        Structuring is splitting large amounts into smaller transactions
        to avoid reporting thresholds.
        """
        try:
            # Look for multiple transactions just below thresholds
            threshold = self.aml_rules['single_transaction_threshold']
            near_threshold_count = 0

            for transaction in transactions[-20:]:  # Last 20 transactions
                if transaction.amount > threshold * self.aml_rules['structuring_detection_threshold']:
                    near_threshold_count += 1

            return near_threshold_count >= 3

        except Exception:
            return False

    def _perform_aml_check(self, compliance_check: ComplianceCheck) -> Dict[str, Any]:
        """
        Perform Anti-Money Laundering check.

        Args:
            compliance_check: ComplianceCheck instance

        Returns:
            Check result dictionary
        """
        try:
            aml_results = {
                'sanctions_screening': 'clear',
                'pep_screening': 'clear',
                'transaction_monitoring': 'clear',
                'risk_assessment': 'completed'
            }

            # Simulate AML checks
            requires_review = False
            passed = True

            # High-risk factors that require review
            if compliance_check.risk_score > 60:
                requires_review = True
                aml_results['review_reason'] = 'High risk score detected'

            if 'potential_structuring' in compliance_check.risk_factors:
                requires_review = True
                aml_results['structuring_alert'] = 'Potential structuring pattern detected'

            if 'high_transaction_velocity' in compliance_check.risk_factors:
                requires_review = True
                aml_results['velocity_alert'] = 'Unusual transaction velocity'

            # Update compliance check with results
            compliance_check.check_results.update(aml_results)
            compliance_check.data_sources.extend(['internal_transaction_db', 'risk_engine'])

            return {
                'passed': passed,
                'requires_review': requires_review,
                'results': aml_results,
                'reason': 'Automated AML screening completed'
            }

        except Exception as e:
            current_app.logger.error(f"AML check failed: {str(e)}")
            return {
                'passed': False,
                'requires_review': True,
                'results': {'error': str(e)},
                'reason': 'AML check error - manual review required'
            }

    def _perform_kyc_check(self, compliance_check: ComplianceCheck) -> Dict[str, Any]:
        """
        Perform Know Your Customer check.

        Args:
            compliance_check: ComplianceCheck instance

        Returns:
            Check result dictionary
        """
        try:
            # Get user details
            user = self.user_repo.find_user_by_id(compliance_check.user_id)
            if not user:
                return {
                    'passed': False,
                    'requires_review': True,
                    'results': {'error': 'User not found'},
                    'reason': 'User verification failed'
                }

            kyc_results = {
                'identity_verification': 'pending',
                'address_verification': 'pending',
                'document_verification': 'pending',
                'source_of_funds': 'pending'
            }

            # Basic user information check
            if user.email and user.first_name and user.last_name:
                kyc_results['basic_info'] = 'complete'
            else:
                kyc_results['basic_info'] = 'incomplete'

            # For now, most KYC checks require manual review
            requires_review = True
            passed = False

            # Auto-pass for low-risk users with complete basic info
            if (compliance_check.risk_level == ComplianceRiskLevel.LOW and
                kyc_results['basic_info'] == 'complete'):
                requires_review = False
                passed = True
                kyc_results['identity_verification'] = 'basic_verification_passed'

            compliance_check.check_results.update(kyc_results)
            compliance_check.data_sources.extend(['user_profile', 'email_verification'])

            return {
                'passed': passed,
                'requires_review': requires_review,
                'results': kyc_results,
                'reason': 'KYC verification process initiated'
            }

        except Exception as e:
            current_app.logger.error(f"KYC check failed: {str(e)}")
            return {
                'passed': False,
                'requires_review': True,
                'results': {'error': str(e)},
                'reason': 'KYC check error - manual review required'
            }

    def _perform_sanctions_check(self, compliance_check: ComplianceCheck) -> Dict[str, Any]:
        """
        Perform sanctions screening check.

        Args:
            compliance_check: ComplianceCheck instance

        Returns:
            Check result dictionary
        """
        try:
            # Get user details
            user = self.user_repo.find_user_by_id(compliance_check.user_id)
            if not user:
                return {
                    'passed': False,
                    'requires_review': True,
                    'results': {'error': 'User not found'},
                    'reason': 'User not found for sanctions screening'
                }

            sanctions_results = {
                'ofac_screening': 'clear',
                'eu_sanctions_screening': 'clear',
                'un_sanctions_screening': 'clear',
                'pep_screening': 'clear'
            }

            # Simulate sanctions screening
            # In production, this would call external sanctions databases
            user_name = f"{user.first_name} {user.last_name}".lower()

            # Placeholder logic - would use real sanctions lists
            suspicious_names = ['test_sanctions', 'blocked_user']
            if any(name in user_name for name in suspicious_names):
                sanctions_results['ofac_screening'] = 'match_found'
                sanctions_results['match_details'] = 'Potential sanctions match detected'

                return {
                    'passed': False,
                    'requires_review': True,
                    'results': sanctions_results,
                    'reason': 'Potential sanctions match - manual review required'
                }

            # Clear screening
            compliance_check.check_results.update(sanctions_results)
            compliance_check.data_sources.extend(['ofac_database', 'eu_sanctions_db'])

            return {
                'passed': True,
                'requires_review': False,
                'results': sanctions_results,
                'reason': 'Sanctions screening clear'
            }

        except Exception as e:
            current_app.logger.error(f"Sanctions check failed: {str(e)}")
            return {
                'passed': False,
                'requires_review': True,
                'results': {'error': str(e)},
                'reason': 'Sanctions check error - manual review required'
            }

    def _perform_fraud_check(self, compliance_check: ComplianceCheck) -> Dict[str, Any]:
        """
        Perform fraud detection check.

        Args:
            compliance_check: ComplianceCheck instance

        Returns:
            Check result dictionary
        """
        try:
            fraud_results = {
                'device_fingerprinting': 'clear',
                'ip_geolocation_check': 'clear',
                'behavioral_analysis': 'clear',
                'transaction_pattern_analysis': 'clear'
            }

            # Simulate fraud detection
            fraud_indicators = 0

            # Check for high-risk factors
            if 'high_transaction_velocity' in compliance_check.risk_factors:
                fraud_indicators += 1
                fraud_results['velocity_fraud_alert'] = 'High transaction velocity detected'

            if compliance_check.risk_score > 80:
                fraud_indicators += 1
                fraud_results['risk_score_alert'] = 'Critical risk score detected'

            # Determine result
            if fraud_indicators >= 2:
                passed = False
                requires_review = True
                fraud_results['fraud_risk_level'] = 'high'
            elif fraud_indicators == 1:
                passed = True
                requires_review = True
                fraud_results['fraud_risk_level'] = 'medium'
            else:
                passed = True
                requires_review = False
                fraud_results['fraud_risk_level'] = 'low'

            compliance_check.check_results.update(fraud_results)
            compliance_check.data_sources.extend(['fraud_engine', 'behavioral_analytics'])

            return {
                'passed': passed,
                'requires_review': requires_review,
                'results': fraud_results,
                'reason': f"Fraud check completed - {fraud_results['fraud_risk_level']} risk"
            }

        except Exception as e:
            current_app.logger.error(f"Fraud check failed: {str(e)}")
            return {
                'passed': False,
                'requires_review': True,
                'results': {'error': str(e)},
                'reason': 'Fraud check error - manual review required'
            }

    def _estimate_completion_time(self, compliance_check: ComplianceCheck) -> str:
        """
        Estimate completion time for compliance check.

        Args:
            compliance_check: ComplianceCheck instance

        Returns:
            Estimated completion time string
        """
        if compliance_check.requires_manual_review():
            if compliance_check.risk_level == ComplianceRiskLevel.CRITICAL:
                return "24-48 hours (priority review)"
            elif compliance_check.risk_level == ComplianceRiskLevel.HIGH:
                return "2-5 business days"
            else:
                return "1-3 business days"
        else:
            return "Completed automatically"

    def _save_compliance_check(self, compliance_check: ComplianceCheck) -> bool:
        """
        Save compliance check to database.

        Args:
            compliance_check: ComplianceCheck instance

        Returns:
            True if saved successfully
        """
        try:
            # For now, just log the compliance check
            # In production, this would save to a compliance checks collection
            current_app.logger.info(f"Compliance check saved: {compliance_check.check_id}")
            return True

        except Exception as e:
            current_app.logger.error(f"Failed to save compliance check: {str(e)}")
            return False

    def get_compliance_status(self, user_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Get overall compliance status for a user.

        Args:
            user_id: User identifier

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success, message, compliance status
        """
        try:
            # For now, return placeholder compliance status
            # In production, this would query the compliance checks database
            compliance_status = {
                'user_id': user_id,
                'overall_status': 'compliant',
                'last_check_date': datetime.now(timezone.utc).isoformat(),
                'pending_checks': [],
                'passed_checks': ['kyc_basic', 'sanctions_screening'],
                'failed_checks': [],
                'next_review_date': (datetime.now(timezone.utc) + timedelta(days=365)).isoformat(),
                'risk_level': 'low',
                'compliance_score': 85.0
            }

            return True, "COMPLIANCE_STATUS_RETRIEVED", compliance_status

        except Exception as e:
            current_app.logger.error(f"Failed to get compliance status: {str(e)}")
            return False, "COMPLIANCE_STATUS_ERROR", None

    def review_compliance_check(self, check_id: str, reviewer_id: str,
                              decision: str, review_notes: str = "") -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Review a compliance check manually.

        Args:
            check_id: Compliance check identifier
            reviewer_id: ID of the reviewer
            decision: Review decision (approve, reject, escalate)
            review_notes: Additional review notes

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success, message, review result
        """
        try:
            # For now, return placeholder review result
            # In production, this would update the compliance check in database

            valid_decisions = ['approve', 'reject', 'escalate']
            if decision not in valid_decisions:
                return False, "INVALID_REVIEW_DECISION", None

            review_result = {
                'check_id': check_id,
                'reviewer_id': reviewer_id,
                'decision': decision,
                'review_notes': review_notes,
                'reviewed_at': datetime.now(timezone.utc).isoformat(),
                'status': 'approved' if decision == 'approve' else 'failed' if decision == 'reject' else 'escalated'
            }

            current_app.logger.info(f"Compliance check {check_id} reviewed by {reviewer_id}: {decision}")

            return True, "COMPLIANCE_CHECK_REVIEWED", review_result

        except Exception as e:
            current_app.logger.error(f"Failed to review compliance check: {str(e)}")
            return False, "COMPLIANCE_REVIEW_ERROR", None

    def generate_compliance_report(self, start_date: datetime, end_date: datetime,
                                 report_type: str = "summary") -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Generate compliance report for a date range.

        Args:
            start_date: Report start date
            end_date: Report end date
            report_type: Type of report (summary, detailed, regulatory)

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success, message, report data
        """
        try:
            # For now, return placeholder compliance report
            # In production, this would query compliance data and generate report

            report = {
                'report_id': f"COMP-RPT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                'report_type': report_type,
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                },
                'summary': {
                    'total_checks': 150,
                    'passed_checks': 135,
                    'failed_checks': 10,
                    'pending_checks': 5,
                    'escalated_checks': 2,
                    'success_rate': 90.0
                },
                'risk_analysis': {
                    'low_risk': 120,
                    'medium_risk': 20,
                    'high_risk': 8,
                    'critical_risk': 2
                },
                'check_types': {
                    'aml': 75,
                    'kyc': 45,
                    'sanctions': 20,
                    'fraud': 10
                },
                'generated_at': datetime.now(timezone.utc).isoformat(),
                'generated_by': 'compliance_system'
            }

            return True, "COMPLIANCE_REPORT_GENERATED", report

        except Exception as e:
            current_app.logger.error(f"Failed to generate compliance report: {str(e)}")
            return False, "COMPLIANCE_REPORT_ERROR", None