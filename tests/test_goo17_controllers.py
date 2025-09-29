"""
Tests for GOO-17 ONLUS Registry & Verification System Controllers

Tests all ONLUS API endpoints including user application management,
admin review workflows, document handling, and public organization APIs.
"""

import pytest
import json
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch, MagicMock
from bson import ObjectId

from tests.core.base_onlus_test import BaseOnlusTest

# Import models for test data
from app.onlus.models.onlus_application import ApplicationStatus, ApplicationPhase
from app.onlus.models.onlus_document import DocumentType, DocumentStatus
from app.onlus.models.verification_check import VerificationCheckType, CheckStatus
from app.onlus.models.onlus_organization import OrganizationStatus, ComplianceStatus
from app.onlus.models.onlus_category import ONLUSCategory


class TestApplicationController(BaseOnlusTest):
    """Tests for user application management endpoints"""

    def setUp(self):
        super().setUp()
        self.base_url = '/api/onlus/applications'
        self.mock_application_service = Mock()

        # Patch the service
        self.application_service_patcher = patch('app.onlus.controllers.application_controller.application_service')
        self.mock_service = self.application_service_patcher.start()
        self.mock_service = self.mock_application_service

    def tearDown(self):
        super().tearDown()
        self.application_service_patcher.stop()

    def test_create_application_success(self):
        """Test successful application creation"""
        application_data = {
            'organization_name': 'Test ONLUS',
            'tax_id': '12345678901',
            'email': 'contact@testonlus.org',
            'category': ONLUSCategory.EDUCATION.value,
            'description': 'Educational non-profit organization',
            'address': {
                'street': 'Via Test 123',
                'city': 'Milano',
                'postal_code': '20100',
                'country': 'IT'
            }
        }

        # Mock service response
        mock_application_id = str(ObjectId())
        self.mock_application_service.create_application.return_value = (
            True, "APPLICATION_CREATED_SUCCESS", {'application_id': mock_application_id}
        )

        response = self.client.post(
            self.base_url,
            json=application_data,
            headers=self.get_auth_headers()
        )

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['success'] is True
        assert response_data['message'] == "APPLICATION_CREATED_SUCCESS"
        assert response_data['data']['application_id'] == mock_application_id

        # Verify service was called with correct data
        self.mock_application_service.create_application.assert_called_once()

    def test_create_application_missing_data(self):
        """Test application creation with missing required data"""
        response = self.client.post(
            self.base_url,
            json={},  # Empty data
            headers=self.get_auth_headers()
        )

        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert response_data['success'] is False
        assert response_data['message'] == "DATA_REQUIRED"

    def test_create_application_unauthorized(self):
        """Test application creation without authentication"""
        application_data = {
            'organization_name': 'Test ONLUS',
            'tax_id': '12345678901'
        }

        response = self.client.post(self.base_url, json=application_data)

        assert response.status_code == 401

    def test_get_application_success(self):
        """Test getting application details"""
        application_id = str(ObjectId())

        mock_application_data = {
            '_id': application_id,
            'organization_name': 'Test ONLUS',
            'status': ApplicationStatus.DRAFT.value,
            'completion_percentage': 75
        }

        self.mock_application_service.get_application.return_value = (
            True, "APPLICATION_RETRIEVED_SUCCESS", mock_application_data
        )

        response = self.client.get(
            f"{self.base_url}/{application_id}",
            headers=self.get_auth_headers()
        )

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['success'] is True
        assert response_data['data']['_id'] == application_id

    def test_get_application_not_found(self):
        """Test getting non-existent application"""
        application_id = str(ObjectId())

        self.mock_application_service.get_application.return_value = (
            False, "APPLICATION_NOT_FOUND", None
        )

        response = self.client.get(
            f"{self.base_url}/{application_id}",
            headers=self.get_auth_headers()
        )

        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert response_data['success'] is False
        assert response_data['message'] == "APPLICATION_NOT_FOUND"

    def test_submit_application_success(self):
        """Test successful application submission"""
        application_id = str(ObjectId())

        self.mock_application_service.submit_application.return_value = (
            True, "APPLICATION_SUBMITTED_SUCCESS", {
                'application_id': application_id,
                'review_deadline': datetime.now(timezone.utc) + timedelta(days=14)
            }
        )

        response = self.client.post(
            f"{self.base_url}/{application_id}/submit",
            headers=self.get_auth_headers()
        )

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['success'] is True
        assert response_data['message'] == "APPLICATION_SUBMITTED_SUCCESS"

    def test_submit_application_incomplete(self):
        """Test submitting incomplete application"""
        application_id = str(ObjectId())

        self.mock_application_service.submit_application.return_value = (
            False, "APPLICATION_INCOMPLETE", None
        )

        response = self.client.post(
            f"{self.base_url}/{application_id}/submit",
            headers=self.get_auth_headers()
        )

        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert response_data['success'] is False
        assert response_data['message'] == "APPLICATION_INCOMPLETE"

    def test_get_user_applications(self):
        """Test getting applications for current user"""
        mock_applications = [
            {
                '_id': str(ObjectId()),
                'organization_name': 'User ONLUS 1',
                'status': ApplicationStatus.DRAFT.value
            },
            {
                '_id': str(ObjectId()),
                'organization_name': 'User ONLUS 2',
                'status': ApplicationStatus.SUBMITTED.value
            }
        ]

        self.mock_application_service.get_user_applications.return_value = (
            True, "USER_APPLICATIONS_SUCCESS", mock_applications
        )

        response = self.client.get(
            self.base_url,
            headers=self.get_auth_headers()
        )

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['success'] is True
        assert len(response_data['data']) == 2

    def test_update_application_success(self):
        """Test successful application update"""
        application_id = str(ObjectId())
        update_data = {
            'description': 'Updated description',
            'contact_person': {
                'name': 'Mario Rossi',
                'email': 'mario@testonlus.org'
            }
        }

        self.mock_application_service.update_application.return_value = (
            True, "APPLICATION_UPDATED_SUCCESS", {'application_id': application_id}
        )

        response = self.client.put(
            f"{self.base_url}/{application_id}",
            json=update_data,
            headers=self.get_auth_headers()
        )

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['success'] is True
        assert response_data['message'] == "APPLICATION_UPDATED_SUCCESS"

    def test_withdraw_application_success(self):
        """Test successful application withdrawal"""
        application_id = str(ObjectId())

        self.mock_application_service.withdraw_application.return_value = (
            True, "APPLICATION_WITHDRAWN_SUCCESS", {'application_id': application_id}
        )

        response = self.client.post(
            f"{self.base_url}/{application_id}/withdraw",
            headers=self.get_auth_headers()
        )

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['success'] is True
        assert response_data['message'] == "APPLICATION_WITHDRAWN_SUCCESS"

    def test_get_application_progress(self):
        """Test getting application progress details"""
        application_id = str(ObjectId())

        mock_progress_data = {
            'completion_percentage': 85,
            'required_steps': ['documents', 'contact_info', 'bank_account'],
            'completed_steps': ['documents', 'contact_info'],
            'current_phase': ApplicationPhase.DOCUMENTATION.value
        }

        self.mock_application_service.get_application_progress.return_value = (
            True, "APPLICATION_PROGRESS_SUCCESS", mock_progress_data
        )

        response = self.client.get(
            f"{self.base_url}/{application_id}/progress",
            headers=self.get_auth_headers()
        )

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['success'] is True
        assert response_data['data']['completion_percentage'] == 85


class TestAdminApplicationController(BaseOnlusTest):
    """Tests for admin application review endpoints"""

    def setUp(self):
        super().setUp()
        self.base_url = '/api/admin/onlus/applications'
        self.mock_application_service = Mock()
        self.mock_verification_service = Mock()
        self.mock_onlus_service = Mock()

        # Patch services
        self.application_service_patcher = patch('app.onlus.controllers.admin_application_controller.application_service')
        self.verification_service_patcher = patch('app.onlus.controllers.admin_application_controller.verification_service')
        self.onlus_service_patcher = patch('app.onlus.controllers.admin_application_controller.onlus_service')

        self.mock_app_service = self.application_service_patcher.start()
        self.mock_ver_service = self.verification_service_patcher.start()
        self.mock_onlus_svc = self.onlus_service_patcher.start()

        self.mock_app_service = self.mock_application_service
        self.mock_ver_service = self.mock_verification_service
        self.mock_onlus_svc = self.mock_onlus_service

    def tearDown(self):
        super().tearDown()
        self.application_service_patcher.stop()
        self.verification_service_patcher.stop()
        self.onlus_service_patcher.stop()

    def test_get_applications_for_review(self):
        """Test getting applications pending admin review"""
        mock_applications = [
            {
                '_id': str(ObjectId()),
                'organization_name': 'Review ONLUS 1',
                'status': ApplicationStatus.SUBMITTED.value,
                'submission_date': datetime.now(timezone.utc) - timedelta(days=2)
            }
        ]

        self.mock_application_service.get_applications_for_admin_review.return_value = (
            True, "APPLICATIONS_FOR_REVIEW_SUCCESS", mock_applications
        )

        response = self.client.get(
            self.base_url,
            headers=self.get_admin_headers()
        )

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['success'] is True
        assert len(response_data['data']) == 1

    def test_assign_reviewer_success(self):
        """Test successful reviewer assignment"""
        application_id = str(ObjectId())
        reviewer_id = str(ObjectId())

        assignment_data = {'reviewer_id': reviewer_id}

        self.mock_application_service.assign_reviewer.return_value = (
            True, "REVIEWER_ASSIGNED_SUCCESS", {'reviewer_id': reviewer_id}
        )

        response = self.client.post(
            f"{self.base_url}/{application_id}/assign",
            json=assignment_data,
            headers=self.get_admin_headers()
        )

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['success'] is True
        assert response_data['message'] == "REVIEWER_ASSIGNED_SUCCESS"

    def test_initiate_verification_success(self):
        """Test successful verification initiation"""
        application_id = str(ObjectId())

        mock_checks_result = {
            'checks_created': [str(ObjectId()), str(ObjectId())],
            'automated_checks_started': 2,
            'manual_checks_pending': 1
        }

        self.mock_verification_service.initiate_verification_checks.return_value = (
            True, "VERIFICATION_CHECKS_INITIATED_SUCCESS", mock_checks_result
        )

        response = self.client.post(
            f"{self.base_url}/{application_id}/verification/initiate",
            headers=self.get_admin_headers()
        )

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['success'] is True
        assert len(response_data['data']['checks_created']) == 2

    def test_get_verification_summary(self):
        """Test getting verification summary"""
        application_id = str(ObjectId())

        mock_summary = {
            'total_checks': 6,
            'completed_checks': 4,
            'pending_checks': 2,
            'overall_risk_level': 'medium',
            'verification_status': 'in_progress'
        }

        self.mock_verification_service.get_verification_summary.return_value = (
            True, "VERIFICATION_SUMMARY_SUCCESS", mock_summary
        )

        response = self.client.get(
            f"{self.base_url}/{application_id}/verification/summary",
            headers=self.get_admin_headers()
        )

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['success'] is True
        assert response_data['data']['total_checks'] == 6

    def test_approve_verification_success(self):
        """Test successful verification approval"""
        application_id = str(ObjectId())

        self.mock_verification_service.approve_application_verification.return_value = (
            True, "VERIFICATION_APPROVED_SUCCESS", {'application_id': application_id}
        )

        response = self.client.post(
            f"{self.base_url}/{application_id}/verification/approve",
            headers=self.get_admin_headers()
        )

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['success'] is True
        assert response_data['message'] == "VERIFICATION_APPROVED_SUCCESS"

    def test_reject_verification_success(self):
        """Test successful verification rejection"""
        application_id = str(ObjectId())
        rejection_data = {'rejection_reason': 'Failed fraud screening'}

        self.mock_verification_service.reject_application_verification.return_value = (
            True, "VERIFICATION_REJECTED_SUCCESS", {'rejection_reason': rejection_data['rejection_reason']}
        )

        response = self.client.post(
            f"{self.base_url}/{application_id}/verification/reject",
            json=rejection_data,
            headers=self.get_admin_headers()
        )

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['success'] is True
        assert response_data['message'] == "VERIFICATION_REJECTED_SUCCESS"

    def test_approve_application_final_success(self):
        """Test final application approval and organization creation"""
        application_id = str(ObjectId())
        approval_data = {
            'conditions': ['Annual reporting required', 'Compliance check in 6 months']
        }

        mock_organization_id = str(ObjectId())
        self.mock_onlus_service.create_organization_from_application.return_value = (
            True, "ORGANIZATION_CREATED_SUCCESS", {'organization_id': mock_organization_id}
        )

        # Mock application repository operations
        with patch('app.onlus.controllers.admin_application_controller.ONLUSApplicationRepository') as mock_repo_class:
            mock_repo = Mock()
            mock_repo_class.return_value = mock_repo

            mock_application_data = {
                '_id': application_id,
                'applicant_id': str(ObjectId()),
                'organization_name': 'Approved ONLUS',
                'status': ApplicationStatus.DUE_DILIGENCE.value
            }
            mock_repo.find_by_id.return_value = mock_application_data
            mock_repo.update_application.return_value = True

            response = self.client.post(
                f"{self.base_url}/{application_id}/approve",
                json=approval_data,
                headers=self.get_admin_headers()
            )

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['success'] is True
        assert response_data['message'] == "APPLICATION_APPROVED_SUCCESS"

    def test_reject_application_final(self):
        """Test final application rejection"""
        application_id = str(ObjectId())
        rejection_data = {'rejection_reason': 'Incomplete documentation'}

        # Mock application repository operations
        with patch('app.onlus.controllers.admin_application_controller.ONLUSApplicationRepository') as mock_repo_class:
            mock_repo = Mock()
            mock_repo_class.return_value = mock_repo

            mock_application_data = {
                '_id': application_id,
                'applicant_id': str(ObjectId()),
                'status': ApplicationStatus.UNDER_REVIEW.value
            }
            mock_repo.find_by_id.return_value = mock_application_data
            mock_repo.update_application.return_value = True

            response = self.client.post(
                f"{self.base_url}/{application_id}/reject",
                json=rejection_data,
                headers=self.get_admin_headers()
            )

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['success'] is True
        assert response_data['message'] == "APPLICATION_REJECTED_SUCCESS"

    def test_get_application_statistics(self):
        """Test getting application statistics"""
        mock_stats = {
            'total_applications': 150,
            'by_status': {
                ApplicationStatus.APPROVED.value: 85,
                ApplicationStatus.SUBMITTED.value: 30
            },
            'approval_rate': 56.67
        }

        self.mock_application_service.get_application_statistics.return_value = (
            True, "APPLICATION_STATISTICS_SUCCESS", mock_stats
        )

        response = self.client.get(
            f"{self.base_url}/statistics",
            headers=self.get_admin_headers()
        )

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['success'] is True
        assert response_data['data']['total_applications'] == 150


class TestDocumentController(BaseOnlusTest):
    """Tests for document management endpoints"""

    def setUp(self):
        super().setUp()
        self.base_url = '/api/onlus'
        self.mock_document_service = Mock()

        # Patch the service
        self.document_service_patcher = patch('app.onlus.controllers.document_controller.document_service')
        self.mock_service = self.document_service_patcher.start()
        self.mock_service = self.mock_document_service

    def tearDown(self):
        super().tearDown()
        self.document_service_patcher.stop()

    def test_upload_document_success(self):
        """Test successful document upload"""
        application_id = str(ObjectId())
        document_data = {
            'document_type': DocumentType.LEGAL_CERTIFICATE.value,
            'filename': 'certificate.pdf',
            'file_path': '/uploads/certificate.pdf',
            'file_size': 1024000,
            'mime_type': 'application/pdf'
        }

        mock_document_id = str(ObjectId())
        self.mock_document_service.upload_document.return_value = (
            True, "DOCUMENT_UPLOADED_SUCCESS", {'document_id': mock_document_id}
        )

        response = self.client.post(
            f"{self.base_url}/applications/{application_id}/documents",
            json=document_data,
            headers=self.get_auth_headers()
        )

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['success'] is True
        assert response_data['data']['document_id'] == mock_document_id

    def test_get_application_documents(self):
        """Test getting documents for application"""
        application_id = str(ObjectId())

        mock_documents = [
            {
                '_id': str(ObjectId()),
                'document_type': DocumentType.LEGAL_CERTIFICATE.value,
                'filename': 'certificate.pdf',
                'status': DocumentStatus.APPROVED.value
            }
        ]

        self.mock_document_service.get_application_documents.return_value = (
            True, "APPLICATION_DOCUMENTS_SUCCESS", mock_documents
        )

        response = self.client.get(
            f"{self.base_url}/applications/{application_id}/documents",
            headers=self.get_auth_headers()
        )

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['success'] is True
        assert len(response_data['data']) == 1

    def test_get_document_download_url(self):
        """Test getting document download URL"""
        document_id = str(ObjectId())

        mock_download_url = "https://secure-download.example.com/certificate.pdf"
        self.mock_document_service.get_document_download_url.return_value = (
            True, "DOWNLOAD_URL_GENERATED_SUCCESS", mock_download_url
        )

        response = self.client.get(
            f"{self.base_url}/documents/{document_id}/download",
            headers=self.get_auth_headers()
        )

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['success'] is True
        assert response_data['data']['download_url'] == mock_download_url

    def test_delete_document_success(self):
        """Test successful document deletion"""
        document_id = str(ObjectId())

        self.mock_document_service.delete_document.return_value = (
            True, "DOCUMENT_DELETED_SUCCESS", {'document_id': document_id}
        )

        response = self.client.delete(
            f"{self.base_url}/documents/{document_id}",
            headers=self.get_auth_headers()
        )

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['success'] is True
        assert response_data['message'] == "DOCUMENT_DELETED_SUCCESS"


class TestONLUSController(BaseOnlusTest):
    """Tests for public ONLUS organization endpoints"""

    def setUp(self):
        super().setUp()
        self.base_url = '/api/onlus'
        self.mock_onlus_service = Mock()
        self.mock_category_repo = Mock()

        # Patch services
        self.onlus_service_patcher = patch('app.onlus.controllers.onlus_controller.onlus_service')
        self.category_repo_patcher = patch('app.onlus.controllers.onlus_controller.category_repo')

        self.mock_service = self.onlus_service_patcher.start()
        self.mock_cat_repo = self.category_repo_patcher.start()

        self.mock_service = self.mock_onlus_service
        self.mock_cat_repo = self.mock_category_repo

    def tearDown(self):
        super().tearDown()
        self.onlus_service_patcher.stop()
        self.category_repo_patcher.stop()

    def test_get_organizations_success(self):
        """Test getting public organizations list"""
        mock_organizations = [
            {
                '_id': str(ObjectId()),
                'name': 'Public ONLUS 1',
                'category': ONLUSCategory.EDUCATION.value,
                'description': 'Educational organization',
                'status': OrganizationStatus.ACTIVE.value
            }
        ]

        self.mock_onlus_service.get_public_organizations.return_value = (
            True, "ORGANIZATIONS_RETRIEVED_SUCCESS", mock_organizations
        )

        response = self.client.get(f"{self.base_url}/organizations")

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['success'] is True
        assert len(response_data['data']) == 1

    def test_get_organizations_with_filters(self):
        """Test getting organizations with category and search filters"""
        category = ONLUSCategory.HEALTHCARE.value
        search_query = "children hospital"

        mock_organizations = [
            {
                '_id': str(ObjectId()),
                'name': 'Children Hospital ONLUS',
                'category': category,
                'description': 'Healthcare for children'
            }
        ]

        self.mock_onlus_service.get_public_organizations.return_value = (
            True, "ORGANIZATIONS_RETRIEVED_SUCCESS", mock_organizations
        )

        response = self.client.get(
            f"{self.base_url}/organizations?category={category}&search={search_query}&limit=10"
        )

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['success'] is True

        # Verify service was called with correct parameters
        self.mock_onlus_service.get_public_organizations.assert_called_once_with(
            category=category,
            featured_only=False,
            limit=10,
            search_query=search_query
        )

    def test_get_organization_details(self):
        """Test getting individual organization details"""
        organization_id = str(ObjectId())

        mock_organization = {
            '_id': organization_id,
            'name': 'Detailed ONLUS',
            'description': 'Detailed organization information',
            'status': OrganizationStatus.ACTIVE.value
        }

        self.mock_onlus_service.get_organization.return_value = (
            True, "ORGANIZATION_RETRIEVED_SUCCESS", mock_organization
        )

        response = self.client.get(f"{self.base_url}/organizations/{organization_id}")

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['success'] is True
        assert response_data['data']['_id'] == organization_id

    def test_get_featured_organizations(self):
        """Test getting featured organizations"""
        mock_featured = [
            {
                '_id': str(ObjectId()),
                'name': 'Featured ONLUS',
                'featured': True,
                'featured_until': datetime.now(timezone.utc) + timedelta(days=10)
            }
        ]

        self.mock_onlus_service.get_public_organizations.return_value = (
            True, "ORGANIZATIONS_RETRIEVED_SUCCESS", mock_featured
        )

        response = self.client.get(f"{self.base_url}/organizations/featured")

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['success'] is True

        # Verify featured_only=True was passed
        self.mock_onlus_service.get_public_organizations.assert_called_once_with(
            featured_only=True
        )

    def test_get_top_rated_organizations(self):
        """Test getting top-rated organizations"""
        limit = 5

        mock_top_rated = [
            {
                '_id': str(ObjectId()),
                'name': 'Top Rated ONLUS',
                'compliance_score': 98,
                'total_donations_received': 50000.0
            }
        ]

        self.mock_onlus_service.get_top_rated_organizations.return_value = (
            True, "TOP_RATED_ORGANIZATIONS_SUCCESS", mock_top_rated
        )

        response = self.client.get(f"{self.base_url}/organizations/top-rated?limit={limit}")

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['success'] is True
        assert len(response_data['data']) == 1

    def test_get_recent_organizations(self):
        """Test getting recently verified organizations"""
        days = 30

        mock_recent = [
            {
                '_id': str(ObjectId()),
                'name': 'Recent ONLUS',
                'verification_date': datetime.now(timezone.utc) - timedelta(days=5)
            }
        ]

        self.mock_onlus_service.get_recent_organizations.return_value = (
            True, "RECENT_ORGANIZATIONS_SUCCESS", mock_recent
        )

        response = self.client.get(f"{self.base_url}/organizations/recent?days={days}")

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['success'] is True

    def test_search_organizations(self):
        """Test organization search functionality"""
        search_query = "education children"
        category = ONLUSCategory.EDUCATION.value

        # Mock repository search
        with patch('app.onlus.controllers.onlus_controller.ONLUSOrganizationRepository') as mock_repo_class:
            mock_repo = Mock()
            mock_repo_class.return_value = mock_repo

            mock_organizations = [
                Mock(
                    to_dict=Mock(return_value={
                        '_id': str(ObjectId()),
                        'name': 'Education ONLUS',
                        'category': category
                    }),
                    is_featured=Mock(return_value=False),
                    get_overall_score=Mock(return_value=85.0)
                )
            ]
            mock_repo.search_organizations.return_value = mock_organizations

            response = self.client.get(
                f"{self.base_url}/organizations/search?q={search_query}&category={category}"
            )

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['success'] is True
        assert response_data['message'] == "ORGANIZATION_SEARCH_SUCCESS"

    def test_get_categories(self):
        """Test getting ONLUS categories"""
        mock_categories = [
            Mock(to_dict=Mock(return_value={
                'category': ONLUSCategory.EDUCATION.value,
                'name': 'Education',
                'description': 'Educational institutions'
            })),
            Mock(to_dict=Mock(return_value={
                'category': ONLUSCategory.HEALTHCARE.value,
                'name': 'Healthcare',
                'description': 'Healthcare organizations'
            }))
        ]

        self.mock_category_repo.get_active_categories.return_value = mock_categories

        response = self.client.get(f"{self.base_url}/categories")

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['success'] is True
        assert response_data['message'] == "CATEGORIES_RETRIEVED_SUCCESS"
        assert len(response_data['data']) == 2

    def test_get_public_statistics(self):
        """Test getting public statistics"""
        mock_stats = {
            'organizations': {
                'total_organizations': 200,
                'total_donations': 1500000.0,
                'total_donors': 5000,
                'by_status': {
                    'active': {'count': 180}
                }
            },
            'category_distribution': {
                ONLUSCategory.EDUCATION.value: 60,
                ONLUSCategory.HEALTHCARE.value: 50
            },
            'generated_at': datetime.now(timezone.utc)
        }

        self.mock_onlus_service.get_organization_statistics.return_value = (
            True, "ORGANIZATION_STATISTICS_SUCCESS", mock_stats
        )

        response = self.client.get(f"{self.base_url}/statistics")

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['success'] is True
        assert response_data['message'] == "PUBLIC_STATISTICS_RETRIEVED_SUCCESS"

        # Verify sensitive data is filtered out
        public_stats = response_data['data']
        assert 'total_organizations' in public_stats
        assert 'total_donations' in public_stats
        assert 'active_organizations' in public_stats
        assert 'category_distribution' in public_stats


class TestAdminONLUSController(BaseOnlusTest):
    """Tests for admin ONLUS management endpoints"""

    def setUp(self):
        super().setUp()
        self.base_url = '/api/admin/onlus'
        self.mock_onlus_service = Mock()
        self.mock_verification_service = Mock()

        # Patch services
        self.onlus_service_patcher = patch('app.onlus.controllers.admin_onlus_controller.onlus_service')
        self.verification_service_patcher = patch('app.onlus.controllers.admin_onlus_controller.verification_service')

        self.mock_onlus_svc = self.onlus_service_patcher.start()
        self.mock_ver_svc = self.verification_service_patcher.start()

        self.mock_onlus_svc = self.mock_onlus_service
        self.mock_ver_svc = self.mock_verification_service

    def tearDown(self):
        super().tearDown()
        self.onlus_service_patcher.stop()
        self.verification_service_patcher.stop()

    def test_get_all_organizations_admin_view(self):
        """Test getting all organizations with admin data"""
        mock_organizations = [
            {
                '_id': str(ObjectId()),
                'name': 'Admin View ONLUS',
                'tax_id': '12345678901',
                'compliance_score': 85,
                'status': OrganizationStatus.ACTIVE.value
            }
        ]

        self.mock_onlus_service.get_public_organizations.return_value = (
            True, "ORGANIZATIONS_RETRIEVED_SUCCESS", mock_organizations
        )

        # Mock admin data enrichment
        admin_org_data = {
            'tax_id': '12345678901',
            'legal_entity_type': 'Association',
            'compliance_status': ComplianceStatus.COMPLIANT.value,
            'compliance_score': 85,
            'needs_compliance_review': False
        }

        self.mock_onlus_service.get_organization.return_value = (
            True, "ORGANIZATION_RETRIEVED_SUCCESS", admin_org_data
        )

        response = self.client.get(
            f"{self.base_url}/organizations",
            headers=self.get_admin_headers()
        )

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['success'] is True

    def test_update_organization_status(self):
        """Test updating organization status"""
        organization_id = str(ObjectId())
        status_data = {
            'status': OrganizationStatus.SUSPENDED.value,
            'reason': 'Compliance violation detected'
        }

        self.mock_onlus_service.update_organization_status.return_value = (
            True, "ORGANIZATION_STATUS_UPDATED_SUCCESS", {
                'organization_id': organization_id,
                'new_status': status_data['status']
            }
        )

        response = self.client.put(
            f"{self.base_url}/organizations/{organization_id}/status",
            json=status_data,
            headers=self.get_admin_headers()
        )

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['success'] is True
        assert response_data['message'] == "ORGANIZATION_STATUS_UPDATED_SUCCESS"

    def test_update_compliance_status(self):
        """Test updating organization compliance status"""
        organization_id = str(ObjectId())
        compliance_data = {
            'compliance_status': ComplianceStatus.MINOR_ISSUES.value,
            'compliance_score': 75,
            'notes': 'Minor documentation issues found'
        }

        self.mock_onlus_service.update_compliance_status.return_value = (
            True, "COMPLIANCE_STATUS_UPDATED_SUCCESS", compliance_data
        )

        response = self.client.put(
            f"{self.base_url}/organizations/{organization_id}/compliance",
            json=compliance_data,
            headers=self.get_admin_headers()
        )

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['success'] is True
        assert response_data['message'] == "COMPLIANCE_STATUS_UPDATED_SUCCESS"

    def test_set_featured_status(self):
        """Test setting organization as featured"""
        organization_id = str(ObjectId())
        featured_data = {'duration_days': 30}

        self.mock_onlus_service.set_featured_status.return_value = (
            True, "FEATURED_STATUS_SET_SUCCESS", {
                'organization_id': organization_id,
                'featured_until': datetime.now(timezone.utc) + timedelta(days=30)
            }
        )

        response = self.client.post(
            f"{self.base_url}/organizations/{organization_id}/featured",
            json=featured_data,
            headers=self.get_admin_headers()
        )

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['success'] is True
        assert response_data['message'] == "FEATURED_STATUS_SET_SUCCESS"

    def test_remove_featured_status(self):
        """Test removing featured status"""
        organization_id = str(ObjectId())

        self.mock_onlus_service.remove_featured_status.return_value = (
            True, "FEATURED_STATUS_REMOVED_SUCCESS", {'organization_id': organization_id}
        )

        response = self.client.delete(
            f"{self.base_url}/organizations/{organization_id}/featured",
            headers=self.get_admin_headers()
        )

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['success'] is True
        assert response_data['message'] == "FEATURED_STATUS_REMOVED_SUCCESS"

    def test_get_organizations_for_compliance_review(self):
        """Test getting organizations needing compliance review"""
        mock_organizations = [
            {
                '_id': str(ObjectId()),
                'name': 'Review Needed ONLUS',
                'compliance_score': 60,
                'last_compliance_review': datetime.now(timezone.utc) - timedelta(days=400)
            }
        ]

        self.mock_onlus_service.get_organizations_for_compliance_review.return_value = (
            True, "COMPLIANCE_REVIEW_ORGANIZATIONS_SUCCESS", mock_organizations
        )

        response = self.client.get(
            f"{self.base_url}/organizations/compliance-review",
            headers=self.get_admin_headers()
        )

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['success'] is True

    def test_get_verification_statistics(self):
        """Test getting verification statistics"""
        mock_stats = {
            'total_checks': 500,
            'success_rate': 92.5,
            'average_completion_time': 2.5,
            'by_check_type': {
                VerificationCheckType.LEGAL_STATUS.value: {'total': 100, 'completed': 95}
            }
        }

        self.mock_verification_service.get_verification_statistics.return_value = (
            True, "VERIFICATION_STATISTICS_SUCCESS", mock_stats
        )

        response = self.client.get(
            f"{self.base_url}/verification/statistics",
            headers=self.get_admin_headers()
        )

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['success'] is True
        assert response_data['data']['total_checks'] == 500