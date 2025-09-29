from typing import Tuple, Optional, Dict, Any, List
from datetime import datetime, timezone, timedelta
from flask import current_app
from app.onlus.repositories.onlus_organization_repository import ONLUSOrganizationRepository
from app.onlus.repositories.onlus_application_repository import ONLUSApplicationRepository
from app.onlus.repositories.onlus_category_repository import ONLUSCategoryRepository
from app.onlus.models.onlus_organization import ONLUSOrganization, OrganizationStatus, ComplianceStatus
from app.onlus.models.onlus_application import ApplicationStatus


class ONLUSService:
    """
    Service for ONLUS organization management.
    Handles organization profile creation, updates, compliance monitoring, and public queries.
    """

    def __init__(self):
        self.organization_repo = ONLUSOrganizationRepository()
        self.application_repo = ONLUSApplicationRepository()
        self.category_repo = ONLUSCategoryRepository()

    def create_organization_from_application(self, application_id: str,
                                           admin_id: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        Create ONLUS organization from approved application.

        Args:
            application_id: Approved application ID
            admin_id: Admin creating the organization

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success, message, organization data
        """
        try:
            # Get approved application
            application = self.application_repo.find_by_id(application_id)
            if not application:
                return False, "APPLICATION_NOT_FOUND", None

            application_obj = application
            if isinstance(application, dict):
                from app.onlus.models.onlus_application import ONLUSApplication
                application_obj = ONLUSApplication.from_dict(application)

            # Verify application is approved
            if application_obj.status != ApplicationStatus.APPROVED.value:
                return False, "APPLICATION_NOT_APPROVED", None

            # Check if organization already exists
            existing_org = self.organization_repo.find_by_application_id(application_id)
            if existing_org:
                return False, "ORGANIZATION_ALREADY_EXISTS", None

            # Create organization from application data
            organization_data = {
                "application_id": application_id,
                "organization_name": application_obj.organization_name,
                "legal_name": application_obj.organization_name,  # Could be different if specified
                "category": application_obj.category,
                "mission_statement": application_obj.mission_statement,
                "description": application_obj.description,
                "contact_email": application_obj.contact_email,
                "contact_phone": application_obj.contact_phone,
                "website_url": application_obj.website_url,
                "address": application_obj.address,
                "legal_entity_type": application_obj.legal_entity_type,
                "tax_id": application_obj.tax_id,
                "incorporation_date": application_obj.incorporation_date,
                "operational_scope": application_obj.operational_scope,
                "target_beneficiaries": application_obj.target_beneficiaries,
                "primary_activities": application_obj.primary_activities,
                "leadership_team": application_obj.leadership_team,
                "board_members": application_obj.board_members,
                "annual_budget": application_obj.annual_budget,
                "funding_sources": application_obj.funding_sources,
                "verification_date": datetime.now(timezone.utc),
                "documents": application_obj.submitted_documents,
                "verification_checks": application_obj.verification_checks,
                "compliance_score": application_obj.compliance_score,
                "next_review_date": datetime.now(timezone.utc) + timedelta(days=365)
            }

            # Create organization instance
            organization = ONLUSOrganization(**organization_data)

            # Save organization
            organization_id = self.organization_repo.create_organization(organization)

            current_app.logger.info(f"ONLUS organization created: {organization_id} from application {application_id} by admin {admin_id}")

            return True, "ORGANIZATION_CREATED_SUCCESS", {
                "organization_id": organization_id,
                "organization_name": organization.organization_name,
                "category": organization.category,
                "status": organization.status,
                "verification_date": organization.verification_date
            }

        except Exception as e:
            current_app.logger.error(f"Failed to create organization: {str(e)}")
            return False, "ORGANIZATION_CREATION_FAILED", None

    def get_organization(self, organization_id: str,
                        include_sensitive: bool = False) -> Tuple[bool, str, Optional[Dict]]:
        """
        Get organization details.

        Args:
            organization_id: Organization ID
            include_sensitive: Whether to include sensitive information

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success, message, organization data
        """
        try:
            organization = self.organization_repo.find_by_id(organization_id)
            if not organization:
                return False, "ORGANIZATION_NOT_FOUND", None

            organization_obj = ONLUSOrganization.from_dict(organization)

            # Check if organization is public
            if not include_sensitive and organization_obj.status != OrganizationStatus.ACTIVE.value:
                return False, "ORGANIZATION_NOT_PUBLIC", None

            organization_data = organization_obj.to_dict(include_sensitive=include_sensitive)

            # Add additional computed fields
            organization_data['is_featured'] = organization_obj.is_featured()
            organization_data['is_eligible_for_donations'] = organization_obj.is_eligible_for_donations()
            organization_data['needs_compliance_review'] = organization_obj.needs_compliance_review()
            organization_data['overall_score'] = organization_obj.get_overall_score()

            return True, "ORGANIZATION_RETRIEVED_SUCCESS", organization_data

        except Exception as e:
            current_app.logger.error(f"Failed to get organization: {str(e)}")
            return False, "ORGANIZATION_RETRIEVAL_FAILED", None

    def get_public_organizations(self, category: str = None, featured_only: bool = False,
                               limit: int = None, search_query: str = None) -> Tuple[bool, str, Optional[List[Dict]]]:
        """
        Get public ONLUS organizations.

        Args:
            category: Optional category filter
            featured_only: Whether to return only featured organizations
            limit: Optional limit on number of organizations
            search_query: Optional search query

        Returns:
            Tuple[bool, str, Optional[List[Dict]]]: Success, message, organizations list
        """
        try:
            organizations = []

            if featured_only:
                organizations = self.organization_repo.get_featured_organizations()
            elif search_query:
                organizations = self.organization_repo.search_organizations(search_query, category)
            elif category:
                organizations = self.organization_repo.get_organizations_by_category(category)
            else:
                organizations = self.organization_repo.get_active_organizations(limit)

            # Apply limit if specified and not already applied
            if limit and len(organizations) > limit:
                organizations = organizations[:limit]

            organizations_data = []
            for org in organizations:
                org_data = org.to_dict(include_sensitive=False)

                # Add computed fields for public display
                org_data['is_featured'] = org.is_featured()
                org_data['overall_score'] = org.get_overall_score()

                # Remove sensitive information
                sensitive_fields = ['tax_id', 'legal_entity_type', 'leadership_team', 'board_members']
                for field in sensitive_fields:
                    org_data.pop(field, None)

                organizations_data.append(org_data)

            return True, "PUBLIC_ORGANIZATIONS_RETRIEVED_SUCCESS", organizations_data

        except Exception as e:
            current_app.logger.error(f"Failed to get public organizations: {str(e)}")
            return False, "PUBLIC_ORGANIZATIONS_RETRIEVAL_FAILED", None

    def get_top_rated_organizations(self, limit: int = 10) -> Tuple[bool, str, Optional[List[Dict]]]:
        """
        Get top-rated organizations.

        Args:
            limit: Number of organizations to return

        Returns:
            Tuple[bool, str, Optional[List[Dict]]]: Success, message, organizations list
        """
        try:
            organizations = self.organization_repo.get_top_rated_organizations(limit)

            organizations_data = []
            for org in organizations:
                org_data = org.to_dict(include_sensitive=False)
                org_data['overall_score'] = org.get_overall_score()
                organizations_data.append(org_data)

            return True, "TOP_RATED_ORGANIZATIONS_RETRIEVED_SUCCESS", organizations_data

        except Exception as e:
            current_app.logger.error(f"Failed to get top-rated organizations: {str(e)}")
            return False, "TOP_RATED_ORGANIZATIONS_RETRIEVAL_FAILED", None

    def update_organization(self, organization_id: str, update_data: Dict[str, Any],
                           admin_id: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        Update organization details (admin only).

        Args:
            organization_id: Organization ID
            update_data: Data to update
            admin_id: Admin performing the update

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success, message, updated data
        """
        try:
            # Get organization
            organization = self.organization_repo.find_by_id(organization_id)
            if not organization:
                return False, "ORGANIZATION_NOT_FOUND", None

            organization_obj = ONLUSOrganization.from_dict(organization)

            # Validate update data
            merged_data = {**organization_obj.to_dict(include_sensitive=True), **update_data}
            validation_error = ONLUSOrganization.validate_organization_data(merged_data)
            if validation_error:
                return False, validation_error, None

            # Update organization fields
            for key, value in update_data.items():
                if hasattr(organization_obj, key) and key not in ['_id', 'application_id', 'created_at']:
                    setattr(organization_obj, key, value)

            organization_obj.updated_at = datetime.now(timezone.utc)

            # Save updates
            success = self.organization_repo.update_organization(organization_id, organization_obj)
            if not success:
                return False, "ORGANIZATION_UPDATE_FAILED", None

            current_app.logger.info(f"Organization updated: {organization_id} by admin {admin_id}")

            return True, "ORGANIZATION_UPDATED_SUCCESS", {
                "organization_id": organization_id,
                "updated_at": organization_obj.updated_at
            }

        except Exception as e:
            current_app.logger.error(f"Failed to update organization: {str(e)}")
            return False, "ORGANIZATION_UPDATE_FAILED", None

    def update_organization_status(self, organization_id: str, status: str,
                                 admin_id: str, reason: str = None) -> Tuple[bool, str, Optional[Dict]]:
        """
        Update organization status.

        Args:
            organization_id: Organization ID
            status: New status
            admin_id: Admin performing the update
            reason: Reason for status change

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success, message, status data
        """
        try:
            # Get organization
            organization = self.organization_repo.find_by_id(organization_id)
            if not organization:
                return False, "ORGANIZATION_NOT_FOUND", None

            organization_obj = ONLUSOrganization.from_dict(organization)

            # Validate new status
            if status not in [s.value for s in OrganizationStatus]:
                return False, "INVALID_ORGANIZATION_STATUS", None

            old_status = organization_obj.status

            # Handle status-specific logic
            if status == OrganizationStatus.SUSPENDED.value:
                if not reason:
                    return False, "SUSPENSION_REASON_REQUIRED", None
                organization_obj.suspend_organization(reason)

            elif status == OrganizationStatus.ACTIVE.value and old_status == OrganizationStatus.SUSPENDED.value:
                organization_obj.reactivate_organization()

            else:
                organization_obj.status = status
                organization_obj.updated_at = datetime.now(timezone.utc)

            # Save updates
            success = self.organization_repo.update_organization(organization_id, organization_obj)
            if not success:
                return False, "ORGANIZATION_STATUS_UPDATE_FAILED", None

            current_app.logger.info(f"Organization status updated: {organization_id} from {old_status} to {status} by admin {admin_id}")

            return True, "ORGANIZATION_STATUS_UPDATED_SUCCESS", {
                "organization_id": organization_id,
                "old_status": old_status,
                "new_status": status,
                "updated_at": organization_obj.updated_at
            }

        except Exception as e:
            current_app.logger.error(f"Failed to update organization status: {str(e)}")
            return False, "ORGANIZATION_STATUS_UPDATE_FAILED", None

    def update_compliance_status(self, organization_id: str, compliance_status: str,
                               compliance_score: float, admin_id: str,
                               notes: str = None) -> Tuple[bool, str, Optional[Dict]]:
        """
        Update organization compliance status and score.

        Args:
            organization_id: Organization ID
            compliance_status: New compliance status
            compliance_score: Compliance score (0-100)
            admin_id: Admin performing the update
            notes: Optional compliance notes

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success, message, compliance data
        """
        try:
            # Get organization
            organization = self.organization_repo.find_by_id(organization_id)
            if not organization:
                return False, "ORGANIZATION_NOT_FOUND", None

            organization_obj = ONLUSOrganization.from_dict(organization)

            # Validate compliance status
            if compliance_status not in [s.value for s in ComplianceStatus]:
                return False, "INVALID_COMPLIANCE_STATUS", None

            # Validate compliance score
            if not 0 <= compliance_score <= 100:
                return False, "INVALID_COMPLIANCE_SCORE", None

            # Update compliance information
            organization_obj.update_compliance_status(compliance_status, compliance_score)

            # Add notes to metadata
            if notes:
                organization_obj.metadata['compliance_notes'] = notes
                organization_obj.metadata['compliance_reviewer'] = admin_id

            # Save updates
            success = self.organization_repo.update_organization(organization_id, organization_obj)
            if not success:
                return False, "COMPLIANCE_STATUS_UPDATE_FAILED", None

            current_app.logger.info(f"Compliance status updated for organization {organization_id} by admin {admin_id}")

            return True, "COMPLIANCE_STATUS_UPDATED_SUCCESS", {
                "organization_id": organization_id,
                "compliance_status": organization_obj.compliance_status,
                "compliance_score": organization_obj.compliance_score,
                "next_review_date": organization_obj.next_review_date
            }

        except Exception as e:
            current_app.logger.error(f"Failed to update compliance status: {str(e)}")
            return False, "COMPLIANCE_STATUS_UPDATE_FAILED", None

    def set_featured_status(self, organization_id: str, duration_days: int,
                          admin_id: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        Set organization as featured.

        Args:
            organization_id: Organization ID
            duration_days: Duration in days
            admin_id: Admin setting featured status

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success, message, featured data
        """
        try:
            # Validate duration
            if duration_days <= 0 or duration_days > 365:
                return False, "INVALID_FEATURED_DURATION", None

            # Update featured status
            success = self.organization_repo.update_featured_status(organization_id, duration_days)
            if not success:
                return False, "FEATURED_STATUS_UPDATE_FAILED", None

            current_app.logger.info(f"Organization {organization_id} set as featured for {duration_days} days by admin {admin_id}")

            featured_until = datetime.now(timezone.utc) + timedelta(days=duration_days)

            return True, "FEATURED_STATUS_SET_SUCCESS", {
                "organization_id": organization_id,
                "featured_until": featured_until,
                "duration_days": duration_days
            }

        except Exception as e:
            current_app.logger.error(f"Failed to set featured status: {str(e)}")
            return False, "FEATURED_STATUS_UPDATE_FAILED", None

    def remove_featured_status(self, organization_id: str,
                             admin_id: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        Remove featured status from organization.

        Args:
            organization_id: Organization ID
            admin_id: Admin removing featured status

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success, message, result data
        """
        try:
            success = self.organization_repo.remove_featured_status(organization_id)
            if not success:
                return False, "FEATURED_STATUS_REMOVAL_FAILED", None

            current_app.logger.info(f"Featured status removed from organization {organization_id} by admin {admin_id}")

            return True, "FEATURED_STATUS_REMOVED_SUCCESS", {
                "organization_id": organization_id
            }

        except Exception as e:
            current_app.logger.error(f"Failed to remove featured status: {str(e)}")
            return False, "FEATURED_STATUS_REMOVAL_FAILED", None

    def process_donation(self, organization_id: str, amount: float,
                        donor_id: str = None) -> Tuple[bool, str, Optional[Dict]]:
        """
        Process a donation to an organization (update statistics).

        Args:
            organization_id: Organization ID
            amount: Donation amount
            donor_id: Optional donor ID

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success, message, donation data
        """
        try:
            # Get organization
            organization = self.organization_repo.find_by_id(organization_id)
            if not organization:
                return False, "ORGANIZATION_NOT_FOUND", None

            organization_obj = ONLUSOrganization.from_dict(organization)

            # Check if organization can receive donations
            if not organization_obj.is_eligible_for_donations():
                return False, "ORGANIZATION_NOT_ELIGIBLE_FOR_DONATIONS", None

            # Determine if this is a new donor (simplified - would need donor tracking)
            is_new_donor = True  # This would be determined by checking donor history

            # Update donation statistics
            organization_obj.update_donation_stats(amount, is_new_donor)

            # Save updates
            success = self.organization_repo.update_organization(organization_id, organization_obj)
            if not success:
                return False, "DONATION_PROCESSING_FAILED", None

            current_app.logger.info(f"Donation processed: €{amount} to organization {organization_id}")

            return True, "DONATION_PROCESSED_SUCCESS", {
                "organization_id": organization_id,
                "amount": amount,
                "total_donations": organization_obj.total_donations_received,
                "total_donors": organization_obj.total_donors
            }

        except Exception as e:
            current_app.logger.error(f"Failed to process donation: {str(e)}")
            return False, "DONATION_PROCESSING_FAILED", None

    def get_organization_statistics(self) -> Tuple[bool, str, Optional[Dict]]:
        """
        Get overall organization statistics.

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success, message, statistics
        """
        try:
            # Get basic organization stats
            org_stats = self.organization_repo.get_organization_stats()

            # Get category distribution
            category_distribution = self.organization_repo.get_category_distribution()

            # Get compliance summary
            compliance_summary = self.organization_repo.get_compliance_summary()

            # Get organizations needing review
            needing_review = self.organization_repo.get_organizations_needing_review()

            statistics = {
                "organizations": org_stats,
                "category_distribution": category_distribution,
                "compliance": compliance_summary,
                "organizations_needing_review": len(needing_review),
                "generated_at": datetime.now(timezone.utc)
            }

            return True, "ORGANIZATION_STATISTICS_RETRIEVED_SUCCESS", statistics

        except Exception as e:
            current_app.logger.error(f"Failed to get organization statistics: {str(e)}")
            return False, "ORGANIZATION_STATISTICS_RETRIEVAL_FAILED", None

    def get_organizations_for_compliance_review(self) -> Tuple[bool, str, Optional[List[Dict]]]:
        """
        Get organizations that need compliance review.

        Returns:
            Tuple[bool, str, Optional[List[Dict]]]: Success, message, organizations list
        """
        try:
            organizations = self.organization_repo.get_organizations_needing_review()

            organizations_data = []
            for org in organizations:
                org_data = org.to_dict(include_sensitive=True)
                org_data['days_since_last_review'] = (
                    (datetime.now(timezone.utc) - org.last_compliance_review).days
                    if org.last_compliance_review else None
                )
                organizations_data.append(org_data)

            # Sort by priority (overdue first, then by last review date)
            organizations_data.sort(key=lambda x: (
                x['next_review_date'] < datetime.now(timezone.utc) if x['next_review_date'] else True,
                x['last_compliance_review'] or datetime.min.replace(tzinfo=timezone.utc)
            ))

            return True, "COMPLIANCE_REVIEW_ORGANIZATIONS_RETRIEVED_SUCCESS", organizations_data

        except Exception as e:
            current_app.logger.error(f"Failed to get organizations for compliance review: {str(e)}")
            return False, "COMPLIANCE_REVIEW_ORGANIZATIONS_RETRIEVAL_FAILED", None

    def get_recent_organizations(self, days: int = 30) -> Tuple[bool, str, Optional[List[Dict]]]:
        """
        Get recently verified organizations.

        Args:
            days: Number of days to look back

        Returns:
            Tuple[bool, str, Optional[List[Dict]]]: Success, message, organizations list
        """
        try:
            organizations = self.organization_repo.get_recent_organizations(days, limit=20)

            organizations_data = []
            for org in organizations:
                org_data = org.to_dict(include_sensitive=False)
                org_data['days_since_verification'] = (
                    datetime.now(timezone.utc) - org.verification_date
                ).days
                organizations_data.append(org_data)

            return True, "RECENT_ORGANIZATIONS_RETRIEVED_SUCCESS", organizations_data

        except Exception as e:
            current_app.logger.error(f"Failed to get recent organizations: {str(e)}")
            return False, "RECENT_ORGANIZATIONS_RETRIEVAL_FAILED", None