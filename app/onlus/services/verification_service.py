from typing import Tuple, Optional, Dict, Any, List
from datetime import datetime, timezone, timedelta
from flask import current_app
from app.onlus.repositories.verification_check_repository import VerificationCheckRepository
from app.onlus.repositories.onlus_application_repository import ONLUSApplicationRepository
from app.onlus.repositories.onlus_document_repository import ONLUSDocumentRepository
from app.onlus.models.verification_check import (
    VerificationCheck, VerificationCheckType, CheckStatus, RiskLevel, CheckSeverity
)
from app.onlus.models.onlus_application import ApplicationStatus, ApplicationPhase


class VerificationService:
    """
    Service for ONLUS verification engine.
    Handles verification checks, risk assessment, and compliance validation.
    """

    def __init__(self):
        self.verification_repo = VerificationCheckRepository()
        self.application_repo = ONLUSApplicationRepository()
        self.document_repo = ONLUSDocumentRepository()

    def initiate_verification_checks(self, application_id: str,
                                   admin_id: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        Initiate all required verification checks for an application.

        Args:
            application_id: Application ID
            admin_id: Admin initiating the checks

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success, message, checks data
        """
        try:
            # Get application
            application = self.application_repo.find_by_id(application_id)
            if not application:
                return False, "APPLICATION_NOT_FOUND", None

            application_obj = application
            if isinstance(application, dict):
                from app.onlus.models.onlus_application import ONLUSApplication
                application_obj = ONLUSApplication.from_dict(application)

            # Check if application is in correct state
            if application_obj.status != ApplicationStatus.UNDER_REVIEW.value:
                return False, "APPLICATION_NOT_UNDER_REVIEW", None

            # Define standard verification checks
            standard_checks = [
                VerificationCheckType.LEGAL_STATUS.value,
                VerificationCheckType.TAX_EXEMPT_STATUS.value,
                VerificationCheckType.FINANCIAL_HEALTH.value,
                VerificationCheckType.INSURANCE_VERIFICATION.value,
                VerificationCheckType.OPERATIONAL_ASSESSMENT.value,
                VerificationCheckType.FRAUD_SCREENING.value
            ]

            # Add category-specific checks
            additional_checks = self._get_category_specific_checks(application_obj.category)
            all_checks = standard_checks + additional_checks

            created_checks = []
            for check_type in all_checks:
                # Check if check already exists
                existing_check = self.verification_repo.find_by_application_and_type(
                    application_id, check_type
                )

                if not existing_check:
                    # Create new verification check
                    check = VerificationCheck(
                        application_id=application_id,
                        check_type=check_type,
                        automated=self._is_automated_check(check_type),
                        performed_by=admin_id if not self._is_automated_check(check_type) else "system"
                    )

                    check_id = self.verification_repo.create_check(check)
                    created_checks.append({
                        "check_id": check_id,
                        "check_type": check_type,
                        "automated": check.automated
                    })

                    # Start automated checks immediately
                    if check.automated:
                        self._run_automated_check(check_id, check_type, application_obj)

            # Update application with verification check references
            application_obj.verification_checks.extend([check["check_id"] for check in created_checks])
            self.application_repo.update_application(application_id, application_obj)

            current_app.logger.info(f"Initiated {len(created_checks)} verification checks for application {application_id}")

            return True, "VERIFICATION_CHECKS_INITIATED_SUCCESS", {
                "application_id": application_id,
                "checks_created": len(created_checks),
                "checks": created_checks
            }

        except Exception as e:
            current_app.logger.error(f"Failed to initiate verification checks: {str(e)}")
            return False, "VERIFICATION_CHECKS_INITIATION_FAILED", None

    def perform_manual_check(self, check_id: str, admin_id: str,
                           result_data: Dict[str, Any]) -> Tuple[bool, str, Optional[Dict]]:
        """
        Perform a manual verification check.

        Args:
            check_id: Verification check ID
            admin_id: Admin performing the check
            result_data: Check results and findings

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success, message, check results
        """
        try:
            # Get verification check
            check_data = self.verification_repo.find_by_id(check_id)
            if not check_data:
                return False, "VERIFICATION_CHECK_NOT_FOUND", None

            check = VerificationCheck.from_dict(check_data)

            # Validate check can be performed
            if check.status not in [CheckStatus.PENDING.value, CheckStatus.IN_PROGRESS.value]:
                return False, "CHECK_ALREADY_COMPLETED", None

            # Start check if not already started
            if check.status == CheckStatus.PENDING.value:
                check.start_check(admin_id)

            # Process results
            risk_level = result_data.get('risk_level', RiskLevel.UNKNOWN.value)
            result_summary = result_data.get('result_summary', '')
            findings = result_data.get('findings', [])
            recommendations = result_data.get('recommendations', [])
            score = result_data.get('score')

            # Validate results
            if not result_summary:
                return False, "RESULT_SUMMARY_REQUIRED", None

            # Complete the check
            check.complete_check(result_summary, risk_level, findings, recommendations, score)

            # Determine follow-up requirements
            if risk_level in [RiskLevel.HIGH.value, RiskLevel.CRITICAL.value]:
                check.follow_up_required = True
                check.follow_up_notes = result_data.get('follow_up_notes', 'High risk findings require follow-up')

            # Save check results
            success = self.verification_repo.update_check(check_id, check)
            if not success:
                return False, "CHECK_RESULT_SAVE_FAILED", None

            # Update application compliance score
            self._update_application_compliance_score(check.application_id)

            current_app.logger.info(f"Manual verification check completed: {check_id} by admin {admin_id}")

            return True, "MANUAL_CHECK_COMPLETED_SUCCESS", {
                "check_id": check_id,
                "check_type": check.check_type,
                "risk_level": check.risk_level,
                "status": check.status,
                "follow_up_required": check.follow_up_required
            }

        except Exception as e:
            current_app.logger.error(f"Failed to perform manual check: {str(e)}")
            return False, "MANUAL_CHECK_FAILED", None

    def get_verification_summary(self, application_id: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        Get verification summary for an application.

        Args:
            application_id: Application ID

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success, message, verification summary
        """
        try:
            # Get all verification checks for application
            checks = self.verification_repo.find_by_application_id(application_id)

            # Get overall statistics
            check_stats = self.verification_repo.get_application_check_stats(application_id)

            # Get risk assessment
            risk_assessment = self.verification_repo.get_overall_risk_assessment(application_id)

            # Calculate verification progress
            total_checks = len(checks)
            completed_checks = len([c for c in checks if c.status == CheckStatus.COMPLETED.value])
            failed_checks = len([c for c in checks if c.status == CheckStatus.FAILED.value])

            progress_percentage = int((completed_checks / total_checks) * 100) if total_checks > 0 else 0

            # Get pending checks
            pending_checks = [
                {
                    "check_id": str(c._id),
                    "check_type": c.check_type,
                    "status": c.status,
                    "automated": c.automated,
                    "check_date": c.check_date
                }
                for c in checks if c.status in [CheckStatus.PENDING.value, CheckStatus.IN_PROGRESS.value]
            ]

            # Get failed checks
            failed_check_details = [
                {
                    "check_id": str(c._id),
                    "check_type": c.check_type,
                    "result_summary": c.result_summary,
                    "recommendations": c.recommendations
                }
                for c in checks if c.status == CheckStatus.FAILED.value
            ]

            verification_summary = {
                "application_id": application_id,
                "overall_status": self._determine_overall_verification_status(checks),
                "progress_percentage": progress_percentage,
                "risk_assessment": risk_assessment,
                "statistics": check_stats,
                "pending_checks": pending_checks,
                "failed_checks": failed_check_details,
                "total_checks": total_checks,
                "completed_checks": completed_checks,
                "failed_checks_count": failed_checks,
                "checks_requiring_follow_up": len([c for c in checks if c.follow_up_required])
            }

            return True, "VERIFICATION_SUMMARY_RETRIEVED_SUCCESS", verification_summary

        except Exception as e:
            current_app.logger.error(f"Failed to get verification summary: {str(e)}")
            return False, "VERIFICATION_SUMMARY_RETRIEVAL_FAILED", None

    def approve_application_verification(self, application_id: str,
                                       admin_id: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        Approve application verification after all checks pass.

        Args:
            application_id: Application ID
            admin_id: Admin approving the verification

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success, message, approval data
        """
        try:
            # Get verification summary
            success, message, summary = self.get_verification_summary(application_id)
            if not success:
                return False, message, None

            # Check if all verifications are complete and passed
            if summary['overall_status'] != 'passed':
                return False, "VERIFICATION_NOT_COMPLETE", None

            # Get application
            application = self.application_repo.find_by_id(application_id)
            if not application:
                return False, "APPLICATION_NOT_FOUND", None

            application_obj = application
            if isinstance(application, dict):
                from app.onlus.models.onlus_application import ONLUSApplication
                application_obj = ONLUSApplication.from_dict(application)

            # Advance to final approval phase
            application_obj.advance_phase(ApplicationPhase.FINAL_APPROVAL.value)
            application_obj.assigned_reviewer = admin_id

            # Save updates
            self.application_repo.update_application(application_id, application_obj)

            current_app.logger.info(f"Application verification approved: {application_id} by admin {admin_id}")

            return True, "VERIFICATION_APPROVED_SUCCESS", {
                "application_id": application_id,
                "phase": application_obj.phase,
                "ready_for_final_approval": True
            }

        except Exception as e:
            current_app.logger.error(f"Failed to approve verification: {str(e)}")
            return False, "VERIFICATION_APPROVAL_FAILED", None

    def reject_application_verification(self, application_id: str, admin_id: str,
                                      rejection_reason: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        Reject application verification due to failed checks.

        Args:
            application_id: Application ID
            admin_id: Admin rejecting the verification
            rejection_reason: Reason for rejection

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success, message, rejection data
        """
        try:
            # Get application
            application = self.application_repo.find_by_id(application_id)
            if not application:
                return False, "APPLICATION_NOT_FOUND", None

            application_obj = application
            if isinstance(application, dict):
                from app.onlus.models.onlus_application import ONLUSApplication
                application_obj = ONLUSApplication.from_dict(application)

            # Reject application
            application_obj.reject_application(admin_id, rejection_reason)

            # Save updates
            self.application_repo.update_application(application_id, application_obj)

            current_app.logger.info(f"Application verification rejected: {application_id} by admin {admin_id}")

            return True, "VERIFICATION_REJECTED_SUCCESS", {
                "application_id": application_id,
                "status": application_obj.status,
                "rejection_reason": rejection_reason
            }

        except Exception as e:
            current_app.logger.error(f"Failed to reject verification: {str(e)}")
            return False, "VERIFICATION_REJECTION_FAILED", None

    def _get_category_specific_checks(self, category: str) -> List[str]:
        """Get additional verification checks based on ONLUS category."""
        category_checks = {
            "healthcare": [
                VerificationCheckType.COMPLIANCE_CHECK.value,
                VerificationCheckType.IMPACT_VALIDATION.value
            ],
            "education": [
                VerificationCheckType.IMPACT_VALIDATION.value
            ],
            "environment": [
                VerificationCheckType.COMPLIANCE_CHECK.value,
                VerificationCheckType.IMPACT_VALIDATION.value
            ],
            "social_services": [
                VerificationCheckType.BACKGROUND_CHECK.value,
                VerificationCheckType.IMPACT_VALIDATION.value
            ],
            "humanitarian": [
                VerificationCheckType.BACKGROUND_CHECK.value,
                VerificationCheckType.COMPLIANCE_CHECK.value
            ],
            "animal_welfare": [
                VerificationCheckType.COMPLIANCE_CHECK.value
            ]
        }

        return category_checks.get(category, [])

    def _is_automated_check(self, check_type: str) -> bool:
        """Determine if a check type is automated."""
        automated_checks = [
            VerificationCheckType.FRAUD_SCREENING.value,
            VerificationCheckType.LEGAL_STATUS.value,
            VerificationCheckType.TAX_EXEMPT_STATUS.value
        ]
        return check_type in automated_checks

    def _run_automated_check(self, check_id: str, check_type: str, application):
        """Run automated verification check."""
        try:
            check_data = self.verification_repo.find_by_id(check_id)
            if not check_data:
                return

            check = VerificationCheck.from_dict(check_data)
            check.start_check("system")

            # Simulate automated check logic
            if check_type == VerificationCheckType.FRAUD_SCREENING.value:
                result = self._perform_fraud_screening(application)
            elif check_type == VerificationCheckType.LEGAL_STATUS.value:
                result = self._verify_legal_status(application)
            elif check_type == VerificationCheckType.TAX_EXEMPT_STATUS.value:
                result = self._verify_tax_exempt_status(application)
            else:
                result = {"passed": True, "risk_level": RiskLevel.LOW.value, "summary": "Automated check passed"}

            # Complete check with results
            check.complete_check(
                result["summary"],
                result["risk_level"],
                result.get("findings", []),
                result.get("recommendations", []),
                result.get("score")
            )

            self.verification_repo.update_check(check_id, check)

            current_app.logger.info(f"Automated check completed: {check_type} for check {check_id}")

        except Exception as e:
            current_app.logger.error(f"Automated check failed: {check_type} - {str(e)}")

    def _perform_fraud_screening(self, application) -> Dict[str, Any]:
        """Perform automated fraud screening."""
        # Basic fraud screening logic
        risk_factors = []

        # Check for suspicious patterns
        if len(application.organization_name) < 3:
            risk_factors.append("Organization name too short")

        if not application.website_url:
            risk_factors.append("No website provided")

        if application.annual_budget and application.annual_budget > 10000000:  # 10M+ budget
            risk_factors.append("Very high reported budget")

        # Determine risk level
        if len(risk_factors) >= 3:
            risk_level = RiskLevel.HIGH.value
        elif len(risk_factors) >= 1:
            risk_level = RiskLevel.MEDIUM.value
        else:
            risk_level = RiskLevel.LOW.value

        return {
            "passed": len(risk_factors) < 3,
            "risk_level": risk_level,
            "summary": f"Fraud screening completed. {len(risk_factors)} risk factors identified.",
            "findings": [{"type": "risk_factor", "description": factor} for factor in risk_factors]
        }

    def _verify_legal_status(self, application) -> Dict[str, Any]:
        """Verify legal status (simplified simulation)."""
        # Basic legal status verification
        has_legal_entity_type = bool(application.legal_entity_type)
        has_tax_id = bool(application.tax_id)
        has_incorporation_date = bool(application.incorporation_date)

        score = sum([has_legal_entity_type, has_tax_id, has_incorporation_date])

        if score == 3:
            risk_level = RiskLevel.LOW.value
            summary = "Legal status verification passed"
        elif score == 2:
            risk_level = RiskLevel.MEDIUM.value
            summary = "Legal status verification partially passed"
        else:
            risk_level = RiskLevel.HIGH.value
            summary = "Legal status verification failed"

        return {
            "passed": score >= 2,
            "risk_level": risk_level,
            "summary": summary,
            "score": (score / 3) * 100
        }

    def _verify_tax_exempt_status(self, application) -> Dict[str, Any]:
        """Verify tax exempt status (simplified simulation)."""
        # Basic tax exempt verification
        has_tax_id = bool(application.tax_id)

        if has_tax_id:
            # Simulate tax ID validation
            risk_level = RiskLevel.LOW.value
            summary = "Tax exempt status verified"
            passed = True
        else:
            risk_level = RiskLevel.HIGH.value
            summary = "Tax exempt status verification failed - no tax ID"
            passed = False

        return {
            "passed": passed,
            "risk_level": risk_level,
            "summary": summary,
            "score": 100 if passed else 0
        }

    def _determine_overall_verification_status(self, checks: List) -> str:
        """Determine overall verification status from all checks."""
        if not checks:
            return "pending"

        completed_checks = [c for c in checks if c.status == CheckStatus.COMPLETED.value]
        failed_checks = [c for c in checks if c.status == CheckStatus.FAILED.value]
        pending_checks = [c for c in checks if c.status in [CheckStatus.PENDING.value, CheckStatus.IN_PROGRESS.value]]

        # If any checks failed, overall status is failed
        if failed_checks:
            return "failed"

        # If all checks completed, overall status is passed
        if len(completed_checks) == len(checks):
            # Check risk levels
            high_risk_checks = [c for c in completed_checks if c.risk_level in [RiskLevel.HIGH.value, RiskLevel.CRITICAL.value]]
            if high_risk_checks:
                return "high_risk"
            return "passed"

        # If there are pending checks, status is in progress
        if pending_checks:
            return "in_progress"

        return "pending"

    def _update_application_compliance_score(self, application_id: str):
        """Update application compliance score based on verification results."""
        try:
            checks = self.verification_repo.find_by_application_id(application_id)
            if not checks:
                return

            # Calculate compliance score from completed checks
            completed_checks = [c for c in checks if c.status == CheckStatus.COMPLETED.value and c.score is not None]

            if completed_checks:
                avg_score = sum(c.score for c in completed_checks) / len(completed_checks)

                # Update application
                application = self.application_repo.find_by_id(application_id)
                if application:
                    if isinstance(application, dict):
                        from app.onlus.models.onlus_application import ONLUSApplication
                        application_obj = ONLUSApplication.from_dict(application)
                    else:
                        application_obj = application

                    application_obj.compliance_score = avg_score
                    application_obj.updated_at = datetime.now(timezone.utc)

                    self.application_repo.update_application(application_id, application_obj)

        except Exception as e:
            current_app.logger.error(f"Failed to update compliance score: {str(e)}")

    def get_verification_statistics(self) -> Tuple[bool, str, Optional[Dict]]:
        """
        Get verification system statistics.

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success, message, statistics
        """
        try:
            # Get automated checks summary
            automated_summary = self.verification_repo.get_automated_checks_summary()

            # Get pending checks
            pending_checks = self.verification_repo.get_pending_checks()

            # Get checks requiring follow-up
            follow_up_checks = self.verification_repo.get_checks_requiring_follow_up()

            statistics = {
                "automated_checks": automated_summary,
                "pending_checks_count": len(pending_checks),
                "follow_up_required_count": len(follow_up_checks),
                "generated_at": datetime.now(timezone.utc)
            }

            return True, "VERIFICATION_STATISTICS_RETRIEVED_SUCCESS", statistics

        except Exception as e:
            current_app.logger.error(f"Failed to get verification statistics: {str(e)}")
            return False, "VERIFICATION_STATISTICS_RETRIEVAL_FAILED", None