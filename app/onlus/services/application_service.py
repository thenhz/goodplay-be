from typing import Tuple, Optional, Dict, Any, List
from datetime import datetime, timezone, timedelta
from flask import current_app
from app.onlus.repositories.onlus_application_repository import ONLUSApplicationRepository
from app.onlus.repositories.onlus_document_repository import ONLUSDocumentRepository
from app.onlus.repositories.verification_check_repository import VerificationCheckRepository
from app.onlus.models.onlus_application import ONLUSApplication, ApplicationStatus, ApplicationPhase
from app.onlus.models.onlus_category import ONLUSCategory
from app.onlus.models.onlus_document import DocumentType


class ApplicationService:
    """
    Service for ONLUS application management.
    Handles application workflow, phase transitions, and business logic.
    """

    def __init__(self):
        self.application_repo = ONLUSApplicationRepository()
        self.document_repo = ONLUSDocumentRepository()
        self.verification_repo = VerificationCheckRepository()

    def create_application(self, applicant_id: str, application_data: Dict[str, Any]) -> Tuple[bool, str, Optional[Dict]]:
        """
        Create a new ONLUS application.

        Args:
            applicant_id: ID of the user creating the application
            application_data: Application form data

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success, message, application data
        """
        try:
            # Add applicant ID to data
            application_data['applicant_id'] = applicant_id

            # Validate application data
            validation_error = ONLUSApplication.validate_application_data(application_data)
            if validation_error:
                current_app.logger.warning(f"Application validation failed: {validation_error}")
                return False, validation_error, None

            # Check for duplicate organization name
            existing_app = self.application_repo.find_by_organization_name(
                application_data['organization_name']
            )
            if existing_app:
                current_app.logger.warning(f"Duplicate organization name: {application_data['organization_name']}")
                return False, "ORGANIZATION_NAME_EXISTS", None

            # Set required documents based on category
            required_docs = self._get_required_documents_for_category(
                application_data['category']
            )
            application_data['required_documents'] = required_docs

            # Create application instance
            application = ONLUSApplication(**application_data)

            # Calculate initial progress
            application.calculate_completion_percentage()

            # Save to database
            application_id = self.application_repo.create_application(application)

            current_app.logger.info(f"Application created: {application_id} for {application.organization_name}")

            return True, "APPLICATION_CREATED_SUCCESS", {
                "application_id": application_id,
                "organization_name": application.organization_name,
                "status": application.status,
                "progress_percentage": application.progress_percentage,
                "required_documents": application.required_documents
            }

        except Exception as e:
            current_app.logger.error(f"Failed to create application: {str(e)}")
            return False, "APPLICATION_CREATION_FAILED", None

    def get_application(self, application_id: str, user_id: str = None,
                       is_admin: bool = False) -> Tuple[bool, str, Optional[Dict]]:
        """
        Get application details.

        Args:
            application_id: Application ID
            user_id: User ID (for authorization)
            is_admin: Whether user is admin

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success, message, application data
        """
        try:
            application = self.application_repo.find_by_id(application_id)
            if not application:
                return False, "APPLICATION_NOT_FOUND", None

            application_obj = ONLUSApplication.from_dict(application)

            # Check authorization
            if not is_admin and user_id != application_obj.applicant_id:
                return False, "APPLICATION_ACCESS_DENIED", None

            # Get associated documents and checks
            documents = self.document_repo.find_by_application_id(application_id)
            verification_checks = self.verification_repo.find_by_application_id(application_id)

            application_data = application_obj.to_dict(include_sensitive=is_admin)
            application_data['documents'] = [doc.to_dict() for doc in documents]
            application_data['verification_checks'] = [check.to_dict() for check in verification_checks]

            current_app.logger.info(f"Application retrieved: {application_id}")

            return True, "APPLICATION_RETRIEVED_SUCCESS", application_data

        except Exception as e:
            current_app.logger.error(f"Failed to get application: {str(e)}")
            return False, "APPLICATION_RETRIEVAL_FAILED", None

    def update_application(self, application_id: str, update_data: Dict[str, Any],
                          user_id: str, is_admin: bool = False) -> Tuple[bool, str, Optional[Dict]]:
        """
        Update application details.

        Args:
            application_id: Application ID
            update_data: Data to update
            user_id: User ID (for authorization)
            is_admin: Whether user is admin

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success, message, updated data
        """
        try:
            # Get existing application
            application = self.application_repo.find_by_id(application_id)
            if not application:
                return False, "APPLICATION_NOT_FOUND", None

            application_obj = ONLUSApplication.from_dict(application)

            # Check authorization
            if not is_admin and user_id != application_obj.applicant_id:
                return False, "APPLICATION_ACCESS_DENIED", None

            # Check if application can be updated
            if application_obj.status not in [ApplicationStatus.DRAFT.value, ApplicationStatus.DOCUMENTATION_PENDING.value]:
                return False, "APPLICATION_UPDATE_NOT_ALLOWED", None

            # Validate update data
            merged_data = {**application_obj.to_dict(), **update_data}
            validation_error = ONLUSApplication.validate_application_data(merged_data)
            if validation_error:
                return False, validation_error, None

            # Update application fields
            for key, value in update_data.items():
                if hasattr(application_obj, key) and key not in ['_id', 'applicant_id', 'created_at']:
                    setattr(application_obj, key, value)

            application_obj.updated_at = datetime.now(timezone.utc)

            # Recalculate progress
            application_obj.calculate_completion_percentage()

            # Save updates
            success = self.application_repo.update_application(application_id, application_obj)
            if not success:
                return False, "APPLICATION_UPDATE_FAILED", None

            current_app.logger.info(f"Application updated: {application_id}")

            return True, "APPLICATION_UPDATED_SUCCESS", {
                "application_id": application_id,
                "progress_percentage": application_obj.progress_percentage,
                "updated_at": application_obj.updated_at
            }

        except Exception as e:
            current_app.logger.error(f"Failed to update application: {str(e)}")
            return False, "APPLICATION_UPDATE_FAILED", None

    def submit_application(self, application_id: str, user_id: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        Submit application for review.

        Args:
            application_id: Application ID
            user_id: User ID (for authorization)

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success, message, submission data
        """
        try:
            application = self.application_repo.find_by_id(application_id)
            if not application:
                return False, "APPLICATION_NOT_FOUND", None

            application_obj = ONLUSApplication.from_dict(application)

            # Check authorization
            if user_id != application_obj.applicant_id:
                return False, "APPLICATION_ACCESS_DENIED", None

            # Check if application can be submitted
            if not application_obj.can_be_submitted():
                return False, "APPLICATION_INCOMPLETE", None

            # Submit application
            if not application_obj.submit_application():
                return False, "APPLICATION_SUBMISSION_FAILED", None

            # Save updates
            success = self.application_repo.update_application(application_id, application_obj)
            if not success:
                return False, "APPLICATION_SUBMISSION_FAILED", None

            current_app.logger.info(f"Application submitted: {application_id} by user {user_id}")

            return True, "APPLICATION_SUBMITTED_SUCCESS", {
                "application_id": application_id,
                "submission_date": application_obj.submission_date,
                "review_deadline": application_obj.review_deadline,
                "status": application_obj.status
            }

        except Exception as e:
            current_app.logger.error(f"Failed to submit application: {str(e)}")
            return False, "APPLICATION_SUBMISSION_FAILED", None

    def withdraw_application(self, application_id: str, user_id: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        Withdraw application.

        Args:
            application_id: Application ID
            user_id: User ID (for authorization)

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success, message, result data
        """
        try:
            application = self.application_repo.find_by_id(application_id)
            if not application:
                return False, "APPLICATION_NOT_FOUND", None

            application_obj = ONLUSApplication.from_dict(application)

            # Check authorization
            if user_id != application_obj.applicant_id:
                return False, "APPLICATION_ACCESS_DENIED", None

            # Withdraw application
            if not application_obj.withdraw_application():
                return False, "APPLICATION_WITHDRAWAL_NOT_ALLOWED", None

            # Save updates
            success = self.application_repo.update_application(application_id, application_obj)
            if not success:
                return False, "APPLICATION_WITHDRAWAL_FAILED", None

            current_app.logger.info(f"Application withdrawn: {application_id} by user {user_id}")

            return True, "APPLICATION_WITHDRAWN_SUCCESS", {
                "application_id": application_id,
                "status": application_obj.status
            }

        except Exception as e:
            current_app.logger.error(f"Failed to withdraw application: {str(e)}")
            return False, "APPLICATION_WITHDRAWAL_FAILED", None

    def get_user_applications(self, user_id: str, status: str = None) -> Tuple[bool, str, Optional[List[Dict]]]:
        """
        Get applications for a user.

        Args:
            user_id: User ID
            status: Optional status filter

        Returns:
            Tuple[bool, str, Optional[List[Dict]]]: Success, message, applications list
        """
        try:
            applications = self.application_repo.find_by_applicant_id(user_id)

            # Filter by status if provided
            if status:
                applications = [app for app in applications if app.status == status]

            applications_data = []
            for app in applications:
                app_data = app.to_dict()

                # Add document count
                documents = self.document_repo.find_by_application_id(str(app._id))
                app_data['document_count'] = len(documents)

                # Add verification progress
                checks = self.verification_repo.find_by_application_id(str(app._id))
                completed_checks = len([c for c in checks if c.status == "completed"])
                total_checks = len(checks)
                app_data['verification_progress'] = {
                    'completed': completed_checks,
                    'total': total_checks,
                    'percentage': int((completed_checks / total_checks) * 100) if total_checks > 0 else 0
                }

                applications_data.append(app_data)

            current_app.logger.info(f"Retrieved {len(applications_data)} applications for user {user_id}")

            return True, "USER_APPLICATIONS_RETRIEVED_SUCCESS", applications_data

        except Exception as e:
            current_app.logger.error(f"Failed to get user applications: {str(e)}")
            return False, "USER_APPLICATIONS_RETRIEVAL_FAILED", None

    def get_application_progress(self, application_id: str, user_id: str = None,
                               is_admin: bool = False) -> Tuple[bool, str, Optional[Dict]]:
        """
        Get detailed application progress.

        Args:
            application_id: Application ID
            user_id: User ID (for authorization)
            is_admin: Whether user is admin

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success, message, progress data
        """
        try:
            application = self.application_repo.find_by_id(application_id)
            if not application:
                return False, "APPLICATION_NOT_FOUND", None

            application_obj = ONLUSApplication.from_dict(application)

            # Check authorization
            if not is_admin and user_id and user_id != application_obj.applicant_id:
                return False, "APPLICATION_ACCESS_DENIED", None

            # Get documents progress
            documents = self.document_repo.find_by_application_id(application_id)
            required_docs_status = self.document_repo.get_required_documents_status(
                application_id, application_obj.required_documents
            )

            # Get verification checks progress
            verification_checks = self.verification_repo.find_by_application_id(application_id)
            check_stats = self.verification_repo.get_application_check_stats(application_id)

            progress_data = {
                "application_id": application_id,
                "status": application_obj.status,
                "phase": application_obj.phase,
                "progress_percentage": application_obj.progress_percentage,
                "submission_date": application_obj.submission_date,
                "review_deadline": application_obj.review_deadline,
                "is_overdue": application_obj.is_overdue(),
                "documents": {
                    "required": application_obj.required_documents,
                    "submitted": len(application_obj.submitted_documents),
                    "total_required": len(application_obj.required_documents),
                    "status_by_type": required_docs_status,
                    "completion_percentage": self._calculate_document_completion(required_docs_status)
                },
                "verification": check_stats,
                "next_steps": self._get_next_steps(application_obj, required_docs_status, verification_checks)
            }

            return True, "APPLICATION_PROGRESS_RETRIEVED_SUCCESS", progress_data

        except Exception as e:
            current_app.logger.error(f"Failed to get application progress: {str(e)}")
            return False, "APPLICATION_PROGRESS_RETRIEVAL_FAILED", None

    def _get_required_documents_for_category(self, category: str) -> List[str]:
        """Get required documents for a specific ONLUS category."""
        # Base documents required for all categories
        base_documents = [
            DocumentType.LEGAL_CERTIFICATE.value,
            DocumentType.TAX_EXEMPT_STATUS.value,
            DocumentType.MISSION_STATEMENT.value,
            DocumentType.BOARD_COMPOSITION.value,
            DocumentType.INSURANCE_COVERAGE.value
        ]

        # Category-specific additional documents
        category_specific = {
            ONLUSCategory.HEALTHCARE.value: [
                DocumentType.OPERATIONAL_PLAN.value,
                DocumentType.COMPLIANCE_CERTIFICATE.value
            ],
            ONLUSCategory.EDUCATION.value: [
                DocumentType.OPERATIONAL_PLAN.value,
                DocumentType.IMPACT_EVIDENCE.value
            ],
            ONLUSCategory.ENVIRONMENT.value: [
                DocumentType.IMPACT_EVIDENCE.value,
                DocumentType.COMPLIANCE_CERTIFICATE.value
            ],
            ONLUSCategory.SOCIAL_SERVICES.value: [
                DocumentType.OPERATIONAL_PLAN.value,
                DocumentType.IMPACT_EVIDENCE.value
            ],
            ONLUSCategory.HUMANITARIAN.value: [
                DocumentType.OPERATIONAL_PLAN.value,
                DocumentType.COMPLIANCE_CERTIFICATE.value
            ],
            ONLUSCategory.ARTS_CULTURE.value: [
                DocumentType.OPERATIONAL_PLAN.value
            ],
            ONLUSCategory.ANIMAL_WELFARE.value: [
                DocumentType.OPERATIONAL_PLAN.value,
                DocumentType.COMPLIANCE_CERTIFICATE.value
            ]
        }

        additional_docs = category_specific.get(category, [])
        return base_documents + additional_docs

    def _calculate_document_completion(self, required_docs_status: Dict[str, str]) -> int:
        """Calculate document completion percentage."""
        if not required_docs_status:
            return 0

        approved_count = sum(1 for status in required_docs_status.values() if status == "approved")
        total_count = len(required_docs_status)

        return int((approved_count / total_count) * 100) if total_count > 0 else 0

    def _get_next_steps(self, application: ONLUSApplication,
                       docs_status: Dict[str, str],
                       verification_checks: List) -> List[str]:
        """Get next steps for application progress."""
        next_steps = []

        if application.status == ApplicationStatus.DRAFT.value:
            if application.progress_percentage < 80:
                next_steps.append("Complete required application fields")
            else:
                next_steps.append("Submit application for review")

        elif application.status == ApplicationStatus.DOCUMENTATION_PENDING.value:
            missing_docs = [doc_type for doc_type, status in docs_status.items()
                          if status == "missing"]
            if missing_docs:
                next_steps.append(f"Upload missing documents: {', '.join(missing_docs)}")

            rejected_docs = [doc_type for doc_type, status in docs_status.items()
                           if status == "rejected"]
            if rejected_docs:
                next_steps.append(f"Resubmit rejected documents: {', '.join(rejected_docs)}")

        elif application.status == ApplicationStatus.UNDER_REVIEW.value:
            pending_checks = [check for check in verification_checks if check.status == "pending"]
            if pending_checks:
                next_steps.append("Awaiting verification checks completion")
            else:
                next_steps.append("Awaiting admin review decision")

        elif application.status == ApplicationStatus.DUE_DILIGENCE.value:
            next_steps.append("Undergoing due diligence review")

        elif application.status == ApplicationStatus.APPROVED.value:
            next_steps.append("Application approved - ONLUS profile created")

        elif application.status == ApplicationStatus.REJECTED.value:
            next_steps.append("Application rejected - review rejection reason")

        return next_steps

    def get_applications_for_admin_review(self, reviewer_id: str = None,
                                        priority: str = None) -> Tuple[bool, str, Optional[List[Dict]]]:
        """
        Get applications pending admin review.

        Args:
            reviewer_id: Optional reviewer ID filter
            priority: Optional priority filter

        Returns:
            Tuple[bool, str, Optional[List[Dict]]]: Success, message, applications list
        """
        try:
            # Get pending applications
            applications = self.application_repo.get_pending_applications(reviewer_id)

            # Filter by priority if specified
            if priority:
                applications = [app for app in applications if app.priority == priority]

            applications_data = []
            for app in applications:
                app_data = app.to_dict()

                # Add document statistics
                doc_stats = self.document_repo.get_application_document_stats(str(app._id))
                app_data['document_stats'] = doc_stats

                # Add verification statistics
                check_stats = self.verification_repo.get_application_check_stats(str(app._id))
                app_data['verification_stats'] = check_stats

                # Add risk assessment
                risk_assessment = self.verification_repo.get_overall_risk_assessment(str(app._id))
                app_data['risk_assessment'] = risk_assessment

                applications_data.append(app_data)

            current_app.logger.info(f"Retrieved {len(applications_data)} applications for admin review")

            return True, "ADMIN_APPLICATIONS_RETRIEVED_SUCCESS", applications_data

        except Exception as e:
            current_app.logger.error(f"Failed to get applications for admin review: {str(e)}")
            return False, "ADMIN_APPLICATIONS_RETRIEVAL_FAILED", None

    def assign_reviewer(self, application_id: str, reviewer_id: str,
                       admin_id: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        Assign reviewer to application.

        Args:
            application_id: Application ID
            reviewer_id: Reviewer ID to assign
            admin_id: Admin performing the assignment

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success, message, assignment data
        """
        try:
            application = self.application_repo.find_by_id(application_id)
            if not application:
                return False, "APPLICATION_NOT_FOUND", None

            application_obj = ONLUSApplication.from_dict(application)

            # Check if application is in reviewable state
            if application_obj.status not in [
                ApplicationStatus.SUBMITTED.value,
                ApplicationStatus.UNDER_REVIEW.value
            ]:
                return False, "APPLICATION_NOT_REVIEWABLE", None

            # Assign reviewer and start review
            application_obj.start_review(reviewer_id)

            # Save updates
            success = self.application_repo.update_application(application_id, application_obj)
            if not success:
                return False, "REVIEWER_ASSIGNMENT_FAILED", None

            current_app.logger.info(f"Reviewer {reviewer_id} assigned to application {application_id} by admin {admin_id}")

            return True, "REVIEWER_ASSIGNED_SUCCESS", {
                "application_id": application_id,
                "assigned_reviewer": reviewer_id,
                "status": application_obj.status,
                "phase": application_obj.phase
            }

        except Exception as e:
            current_app.logger.error(f"Failed to assign reviewer: {str(e)}")
            return False, "REVIEWER_ASSIGNMENT_FAILED", None

    def get_application_statistics(self) -> Tuple[bool, str, Optional[Dict]]:
        """
        Get overall application statistics.

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success, message, statistics
        """
        try:
            # Get basic application stats
            app_stats = self.application_repo.get_application_stats()

            # Get category distribution
            category_stats = self.application_repo.get_category_stats()

            # Get reviewer workload
            reviewer_workload = self.application_repo.get_reviewer_workload()

            # Get overdue applications count
            overdue_apps = self.application_repo.get_overdue_applications()

            statistics = {
                "applications": app_stats,
                "categories": category_stats,
                "reviewers": reviewer_workload,
                "overdue_count": len(overdue_apps),
                "generated_at": datetime.now(timezone.utc)
            }

            return True, "APPLICATION_STATISTICS_RETRIEVED_SUCCESS", statistics

        except Exception as e:
            current_app.logger.error(f"Failed to get application statistics: {str(e)}")
            return False, "APPLICATION_STATISTICS_RETRIEVAL_FAILED", None