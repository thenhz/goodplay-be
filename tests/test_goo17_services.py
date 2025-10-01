"""
Tests for GOO-17 ONLUS Registry & Verification System Services

Tests all ONLUS service layer business logic including application workflow,
verification processes, document management, and organization operations.
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch, MagicMock
from bson import ObjectId
from decimal import Decimal

# Import services to test
from app.onlus.services.application_service import ApplicationService
from app.onlus.services.verification_service import VerificationService
from app.onlus.services.document_service import DocumentService
from app.onlus.services.onlus_service import ONLUSService

# Import models for test data
from app.onlus.models.onlus_application import ApplicationStatus, ApplicationPhase, Priority
from app.onlus.models.onlus_document import DocumentType, DocumentStatus
from app.onlus.models.verification_check import VerificationCheckType, CheckStatus, RiskLevel
from app.onlus.models.onlus_organization import OrganizationStatus, ComplianceStatus
from app.onlus.models.onlus_category import ONLUSCategory


class TestApplicationService:
    """Tests for ApplicationService"""

    def setup_method(self):
        """Setup test fixtures"""
        self.service = ApplicationService()
        self.mock_app_repo = Mock()
        self.mock_doc_repo = Mock()
        self.mock_category_repo = Mock()

        # Patch repositories
        self.service.application_repo = self.mock_app_repo
        self.service.document_repo = self.mock_doc_repo
        self.service.category_repo = self.mock_category_repo

    def test_create_application_success(self):
        """Test successful application creation"""
        user_id = str(ObjectId())
        application_data = {
            'organization_name': 'Test ONLUS',
            'tax_id': '12345678901',
            'email': 'contact@testonlus.org',
            'category': ONLUSCategory.EDUCATION.value,
            'description': 'Educational non-profit organization'
        }

        # Mock category requirements
        self.mock_category_repo.get_verification_requirements_for_category.return_value = [
            'legal_certificate', 'tax_exempt_status'
        ]

        # Mock successful creation
        mock_application_id = str(ObjectId())
        self.mock_app_repo.create_application.return_value = mock_application_id

        success, message, result = self.service.create_application(user_id, application_data)

        assert success is True
        assert message == "APPLICATION_CREATED_SUCCESS"
        assert result['application_id'] == mock_application_id

        # Verify repository was called with correct data
        create_call = self.mock_app_repo.create_application.call_args[0][0]
        assert create_call['applicant_id'] == user_id
        assert create_call['organization_name'] == application_data['organization_name']
        assert 'legal_certificate' in create_call['required_documents']

    def test_create_application_invalid_data(self):
        """Test application creation with invalid data"""
        user_id = str(ObjectId())
        invalid_data = {
            'organization_name': '',  # Empty name
            'email': 'invalid-email'  # Invalid email
        }

        success, message, result = self.service.create_application(user_id, invalid_data)

        assert success is False
        assert message == "INVALID_APPLICATION_DATA"
        assert result is None

    def test_submit_application_success(self):
        """Test successful application submission"""
        application_id = str(ObjectId())
        user_id = str(ObjectId())

        # Mock application data
        mock_application_data = {
            '_id': application_id,
            'applicant_id': user_id,
            'organization_name': 'Test ONLUS',
            'status': ApplicationStatus.DRAFT.value,
            'required_documents': ['certificate.pdf'],
            'submitted_documents': ['certificate.pdf'],
            'contact_person': {'name': 'Test', 'email': 'test@example.com'},
            'bank_account': {'iban': 'IT60X0542811101000000123456'}
        }

        self.mock_app_repo.find_by_id.return_value = mock_application_data
        self.mock_app_repo.update_application.return_value = True

        success, message, result = self.service.submit_application(application_id, user_id)

        assert success is True
        assert message == "APPLICATION_SUBMITTED_SUCCESS"
        assert result['application_id'] == application_id
        assert 'review_deadline' in result

        # Verify application was updated
        update_call = self.mock_app_repo.update_application.call_args[0][1]
        assert update_call.status == ApplicationStatus.SUBMITTED.value

    def test_submit_application_not_found(self):
        """Test submitting non-existent application"""
        application_id = str(ObjectId())
        user_id = str(ObjectId())

        self.mock_app_repo.find_by_id.return_value = None

        success, message, result = self.service.submit_application(application_id, user_id)

        assert success is False
        assert message == "APPLICATION_NOT_FOUND"
        assert result is None

    def test_submit_application_unauthorized(self):
        """Test submitting application by unauthorized user"""
        application_id = str(ObjectId())
        user_id = str(ObjectId())
        different_user_id = str(ObjectId())

        mock_application_data = {
            '_id': application_id,
            'applicant_id': different_user_id,  # Different user
            'status': ApplicationStatus.DRAFT.value
        }

        self.mock_app_repo.find_by_id.return_value = mock_application_data

        success, message, result = self.service.submit_application(application_id, user_id)

        assert success is False
        assert message == "UNAUTHORIZED_ACCESS"
        assert result is None

    def test_submit_application_incomplete(self):
        """Test submitting incomplete application"""
        application_id = str(ObjectId())
        user_id = str(ObjectId())

        mock_application_data = {
            '_id': application_id,
            'applicant_id': user_id,
            'organization_name': 'Incomplete ONLUS',
            'status': ApplicationStatus.DRAFT.value,
            'required_documents': ['certificate.pdf'],
            'submitted_documents': []  # Missing documents
        }

        self.mock_app_repo.find_by_id.return_value = mock_application_data

        success, message, result = self.service.submit_application(application_id, user_id)

        assert success is False
        assert message == "APPLICATION_INCOMPLETE"
        assert result is None

    def test_get_application_success(self):
        """Test getting application details"""
        application_id = str(ObjectId())
        user_id = str(ObjectId())

        mock_application_data = {
            '_id': application_id,
            'applicant_id': user_id,
            'organization_name': 'Test ONLUS',
            'status': ApplicationStatus.SUBMITTED.value
        }

        self.mock_app_repo.find_by_id.return_value = mock_application_data

        success, message, result = self.service.get_application(application_id, user_id)

        assert success is True
        assert message == "APPLICATION_RETRIEVED_SUCCESS"
        assert result['_id'] == application_id

    def test_get_applications_for_admin_review(self):
        """Test getting applications for admin review"""
        reviewer_id = str(ObjectId())
        priority = Priority.HIGH.value

        mock_applications = [
            {
                '_id': str(ObjectId()),
                'organization_name': 'Review ONLUS 1',
                'status': ApplicationStatus.SUBMITTED.value,
                'priority': priority
            }
        ]

        self.mock_app_repo.get_pending_applications.return_value = mock_applications

        success, message, result = self.service.get_applications_for_admin_review(reviewer_id, priority)

        assert success is True
        assert message == "APPLICATIONS_FOR_REVIEW_SUCCESS"
        assert len(result) == 1

    def test_assign_reviewer_success(self):
        """Test successful reviewer assignment"""
        application_id = str(ObjectId())
        reviewer_id = str(ObjectId())
        admin_id = str(ObjectId())

        mock_application_data = {
            '_id': application_id,
            'status': ApplicationStatus.SUBMITTED.value
        }

        self.mock_app_repo.find_by_id.return_value = mock_application_data
        self.mock_app_repo.update_application.return_value = True

        success, message, result = self.service.assign_reviewer(application_id, reviewer_id, admin_id)

        assert success is True
        assert message == "REVIEWER_ASSIGNED_SUCCESS"
        assert result['reviewer_id'] == reviewer_id

        # Verify application was updated with reviewer
        update_call = self.mock_app_repo.update_application.call_args[0][1]
        assert update_call.assigned_reviewer == reviewer_id

    def test_get_application_statistics(self):
        """Test getting application statistics"""
        mock_stats = {
            'total_applications': 150,
            'by_status': {
                ApplicationStatus.APPROVED.value: 85,
                ApplicationStatus.SUBMITTED.value: 30,
                ApplicationStatus.REJECTED.value: 15
            },
            'by_category': {
                ONLUSCategory.EDUCATION.value: 45,
                ONLUSCategory.HEALTHCARE.value: 40
            }
        }

        self.mock_app_repo.get_application_statistics.return_value = mock_stats

        success, message, result = self.service.get_application_statistics()

        assert success is True
        assert message == "APPLICATION_STATISTICS_SUCCESS"
        assert result['total_applications'] == 150
        assert result['approval_rate'] == 56.67  # 85/150 * 100


class TestVerificationService:
    """Tests for VerificationService"""

    def setup_method(self):
        """Setup test fixtures"""
        self.service = VerificationService()
        self.mock_verification_repo = Mock()
        self.mock_app_repo = Mock()

        self.service.verification_repo = self.mock_verification_repo
        self.service.application_repo = self.mock_app_repo

    def test_initiate_verification_checks_success(self):
        """Test successful verification checks initiation"""
        application_id = str(ObjectId())
        admin_id = str(ObjectId())

        # Mock application data
        mock_application_data = {
            '_id': application_id,
            'category': ONLUSCategory.HEALTHCARE.value,
            'status': ApplicationStatus.SUBMITTED.value
        }

        self.mock_app_repo.find_by_id.return_value = mock_application_data
        self.mock_verification_repo.create_check.return_value = str(ObjectId())

        with patch.object(self.service, '_get_category_specific_checks', return_value=['medical_license_check']):
            success, message, result = self.service.initiate_verification_checks(application_id, admin_id)

        assert success is True
        assert message == "VERIFICATION_CHECKS_INITIATED_SUCCESS"
        assert 'checks_created' in result
        assert len(result['checks_created']) > 0

        # Verify checks were created
        assert self.mock_verification_repo.create_check.call_count >= 6  # Standard checks + category-specific

    def test_initiate_verification_checks_application_not_found(self):
        """Test verification initiation for non-existent application"""
        application_id = str(ObjectId())
        admin_id = str(ObjectId())

        self.mock_app_repo.find_by_id.return_value = None

        success, message, result = self.service.initiate_verification_checks(application_id, admin_id)

        assert success is False
        assert message == "APPLICATION_NOT_FOUND"
        assert result is None

    def test_get_verification_summary(self):
        """Test getting verification summary"""
        application_id = str(ObjectId())

        # Mock verification checks
        mock_checks = [
            Mock(check_type=VerificationCheckType.LEGAL_STATUS.value,
                 status=CheckStatus.COMPLETED.value, score=95.0, get_risk_score=Mock(return_value=1.0)),
            Mock(check_type=VerificationCheckType.FRAUD_SCREENING.value,
                 status=CheckStatus.COMPLETED.value, score=88.0, get_risk_score=Mock(return_value=2.0)),
            Mock(check_type=VerificationCheckType.BACKGROUND_CHECK.value,
                 status=CheckStatus.PENDING.value, score=None, get_risk_score=Mock(return_value=3.0))
        ]

        self.mock_verification_repo.find_by_application_id.return_value = mock_checks

        # Mock overall risk assessment
        mock_risk_assessment = {
            'average_risk_score': 2.0,
            'overall_risk_level': RiskLevel.MEDIUM.value,
            'completed_checks': 2
        }
        self.mock_verification_repo.get_overall_risk_assessment.return_value = mock_risk_assessment

        success, message, result = self.service.get_verification_summary(application_id)

        assert success is True
        assert message == "VERIFICATION_SUMMARY_SUCCESS"
        assert result['total_checks'] == 3
        assert result['completed_checks'] == 2
        assert result['pending_checks'] == 1
        assert result['overall_risk_level'] == RiskLevel.MEDIUM.value

    def test_approve_application_verification_success(self):
        """Test successful verification approval"""
        application_id = str(ObjectId())
        admin_id = str(ObjectId())

        # Mock completed checks with good scores
        mock_checks = [
            Mock(status=CheckStatus.COMPLETED.value, get_risk_score=Mock(return_value=1.0)),
            Mock(status=CheckStatus.COMPLETED.value, get_risk_score=Mock(return_value=1.5))
        ]

        self.mock_verification_repo.find_by_application_id.return_value = mock_checks

        # Mock application update
        mock_application_data = {
            '_id': application_id,
            'status': ApplicationStatus.UNDER_REVIEW.value
        }
        self.mock_app_repo.find_by_id.return_value = mock_application_data
        self.mock_app_repo.update_application.return_value = True

        success, message, result = self.service.approve_application_verification(application_id, admin_id)

        assert success is True
        assert message == "VERIFICATION_APPROVED_SUCCESS"
        assert result['application_id'] == application_id

        # Verify application was moved to due diligence phase
        update_call = self.mock_app_repo.update_application.call_args[0][1]
        assert update_call.phase == ApplicationPhase.DUE_DILIGENCE.value

    def test_approve_verification_incomplete_checks(self):
        """Test verification approval with incomplete checks"""
        application_id = str(ObjectId())
        admin_id = str(ObjectId())

        # Mock incomplete checks
        mock_checks = [
            Mock(status=CheckStatus.COMPLETED.value, get_risk_score=Mock(return_value=1.0)),
            Mock(status=CheckStatus.PENDING.value, get_risk_score=Mock(return_value=3.0))  # Still pending
        ]

        self.mock_verification_repo.find_by_application_id.return_value = mock_checks

        success, message, result = self.service.approve_application_verification(application_id, admin_id)

        assert success is False
        assert message == "VERIFICATION_INCOMPLETE"
        assert result is None

    def test_reject_application_verification(self):
        """Test verification rejection"""
        application_id = str(ObjectId())
        admin_id = str(ObjectId())
        rejection_reason = "Failed fraud screening check"

        mock_application_data = {
            '_id': application_id,
            'status': ApplicationStatus.UNDER_REVIEW.value
        }
        self.mock_app_repo.find_by_id.return_value = mock_application_data
        self.mock_app_repo.update_application.return_value = True

        success, message, result = self.service.reject_application_verification(
            application_id, admin_id, rejection_reason
        )

        assert success is True
        assert message == "VERIFICATION_REJECTED_SUCCESS"
        assert result['rejection_reason'] == rejection_reason

    def test_perform_manual_check_success(self):
        """Test successful manual verification check"""
        check_id = str(ObjectId())
        admin_id = str(ObjectId())
        check_data = {
            'result': 'approved',
            'score': 90.0,
            'notes': 'Background check passed',
            'findings': [{'type': 'identity', 'result': 'verified'}]
        }

        mock_check_data = {
            '_id': check_id,
            'check_type': VerificationCheckType.BACKGROUND_CHECK.value,
            'status': CheckStatus.PENDING.value,
            'automated': False
        }

        self.mock_verification_repo.find_by_id.return_value = mock_check_data
        self.mock_verification_repo.update_check.return_value = True

        success, message, result = self.service.perform_manual_check(check_id, admin_id, check_data)

        assert success is True
        assert message == "MANUAL_CHECK_COMPLETED_SUCCESS"
        assert result['check_id'] == check_id

        # Verify check was updated
        update_call = self.mock_verification_repo.update_check.call_args[0][1]
        assert update_call.status == CheckStatus.COMPLETED.value
        assert update_call.score == 90.0

    def test_get_verification_statistics(self):
        """Test getting verification statistics"""
        mock_stats = {
            'total_checks': 500,
            'by_check_type': {
                VerificationCheckType.LEGAL_STATUS.value: {'total': 100, 'completed': 95},
                VerificationCheckType.FRAUD_SCREENING.value: {'total': 100, 'completed': 98}
            },
            'success_rate': 92.5,
            'average_completion_time': 2.5  # days
        }

        self.mock_verification_repo.get_check_statistics.return_value = mock_stats

        success, message, result = self.service.get_verification_statistics()

        assert success is True
        assert message == "VERIFICATION_STATISTICS_SUCCESS"
        assert result['total_checks'] == 500
        assert result['success_rate'] == 92.5


class TestDocumentService:
    """Tests for DocumentService"""

    def setup_method(self):
        """Setup test fixtures"""
        self.service = DocumentService()
        self.mock_doc_repo = Mock()
        self.mock_app_repo = Mock()

        self.service.document_repo = self.mock_doc_repo
        self.service.application_repo = self.mock_app_repo

    def test_upload_document_success(self):
        """Test successful document upload"""
        application_id = str(ObjectId())
        user_id = str(ObjectId())
        document_data = {
            'document_type': DocumentType.LEGAL_CERTIFICATE.value,
            'filename': 'certificate.pdf',
            'file_path': '/uploads/certificate.pdf',
            'file_size': 1024000,
            'mime_type': 'application/pdf'
        }

        # Mock application exists and user authorized
        mock_application_data = {
            '_id': application_id,
            'applicant_id': user_id,
            'status': ApplicationStatus.DRAFT.value
        }
        self.mock_app_repo.find_by_id.return_value = mock_application_data

        # Mock successful document creation
        mock_document_id = str(ObjectId())
        self.mock_doc_repo.create_document.return_value = mock_document_id

        success, message, result = self.service.upload_document(application_id, document_data, user_id)

        assert success is True
        assert message == "DOCUMENT_UPLOADED_SUCCESS"
        assert result['document_id'] == mock_document_id

        # Verify document was created with correct data
        create_call = self.mock_doc_repo.create_document.call_args[0][0]
        assert create_call['application_id'] == application_id
        assert create_call['uploaded_by'] == user_id

    def test_upload_document_unauthorized(self):
        """Test document upload by unauthorized user"""
        application_id = str(ObjectId())
        user_id = str(ObjectId())
        different_user_id = str(ObjectId())
        document_data = {
            'document_type': DocumentType.TAX_EXEMPT_STATUS.value,
            'filename': 'tax.pdf'
        }

        mock_application_data = {
            '_id': application_id,
            'applicant_id': different_user_id,  # Different user
            'status': ApplicationStatus.DRAFT.value
        }
        self.mock_app_repo.find_by_id.return_value = mock_application_data

        success, message, result = self.service.upload_document(application_id, document_data, user_id)

        assert success is False
        assert message == "UNAUTHORIZED_ACCESS"
        assert result is None

    def test_upload_document_invalid_file_size(self):
        """Test document upload with oversized file"""
        application_id = str(ObjectId())
        user_id = str(ObjectId())
        document_data = {
            'document_type': DocumentType.FINANCIAL_REPORT.value,
            'filename': 'large_report.pdf',
            'file_size': 15 * 1024 * 1024  # 15MB - over limit
        }

        success, message, result = self.service.upload_document(application_id, document_data, user_id)

        assert success is False
        assert message == "FILE_SIZE_EXCEEDS_LIMIT"
        assert result is None

    def test_review_document_approve(self):
        """Test document approval by admin"""
        document_id = str(ObjectId())
        admin_id = str(ObjectId())
        review_data = {
            'action': 'approve',
            'notes': 'Document verified and approved'
        }

        mock_document_data = {
            '_id': document_id,
            'status': DocumentStatus.UNDER_REVIEW.value,
            'application_id': str(ObjectId())
        }

        self.mock_doc_repo.find_by_id.return_value = mock_document_data
        self.mock_doc_repo.update_document.return_value = True

        with patch.object(self.service, '_update_application_progress'):
            success, message, result = self.service.review_document(document_id, admin_id, review_data)

        assert success is True
        assert message == "DOCUMENT_REVIEWED_SUCCESS"
        assert result['action'] == 'approve'

        # Verify document was approved
        update_call = self.mock_doc_repo.update_document.call_args[0][1]
        assert update_call.status == DocumentStatus.APPROVED.value
        assert update_call.reviewed_by == admin_id

    def test_review_document_reject(self):
        """Test document rejection by admin"""
        document_id = str(ObjectId())
        admin_id = str(ObjectId())
        review_data = {
            'action': 'reject',
            'rejection_reason': 'Document format invalid',
            'notes': 'Please resubmit in correct format'
        }

        mock_document_data = {
            '_id': document_id,
            'status': DocumentStatus.UNDER_REVIEW.value,
            'application_id': str(ObjectId())
        }

        self.mock_doc_repo.find_by_id.return_value = mock_document_data
        self.mock_doc_repo.update_document.return_value = True

        with patch.object(self.service, '_update_application_progress'):
            success, message, result = self.service.review_document(document_id, admin_id, review_data)

        assert success is True
        assert message == "DOCUMENT_REVIEWED_SUCCESS"
        assert result['action'] == 'reject'

        # Verify document was rejected
        update_call = self.mock_doc_repo.update_document.call_args[0][1]
        assert update_call.status == DocumentStatus.REJECTED.value
        assert update_call.rejection_reason == review_data['rejection_reason']

    def test_get_document_download_url_success(self):
        """Test getting document download URL"""
        document_id = str(ObjectId())
        user_id = str(ObjectId())

        mock_document_data = {
            '_id': document_id,
            'filename': 'certificate.pdf',
            'file_path': '/uploads/certificate.pdf',
            'application_id': str(ObjectId())
        }

        # Mock application access check
        mock_application_data = {
            'applicant_id': user_id,
            'status': ApplicationStatus.SUBMITTED.value
        }

        self.mock_doc_repo.find_by_id.return_value = mock_document_data
        self.mock_app_repo.find_by_id.return_value = mock_application_data

        with patch.object(self.service, '_generate_secure_download_url', return_value='https://secure-url.com/download'):
            success, message, result = self.service.get_document_download_url(document_id, user_id)

        assert success is True
        assert message == "DOWNLOAD_URL_GENERATED_SUCCESS"
        assert result.startswith('https://secure-url.com/download')

    def test_get_documents_for_review(self):
        """Test getting documents pending review"""
        document_type = DocumentType.INSURANCE_COVERAGE.value
        limit = 10

        mock_documents = [
            {
                '_id': str(ObjectId()),
                'document_type': document_type,
                'status': DocumentStatus.UNDER_REVIEW.value,
                'uploaded_at': datetime.now(timezone.utc) - timedelta(hours=2)
            }
        ]

        self.mock_doc_repo.get_documents_for_review.return_value = mock_documents

        success, message, result = self.service.get_documents_for_review(document_type, limit)

        assert success is True
        assert message == "DOCUMENTS_FOR_REVIEW_SUCCESS"
        assert len(result) == 1

    def test_process_expired_documents(self):
        """Test processing expired documents"""
        mock_expired_docs = [
            {
                '_id': str(ObjectId()),
                'document_type': DocumentType.LEGAL_CERTIFICATE.value,
                'status': DocumentStatus.APPROVED.value,
                'expiration_date': datetime.now(timezone.utc) - timedelta(days=1)
            }
        ]

        self.mock_doc_repo.find_expired_documents.return_value = mock_expired_docs
        self.mock_doc_repo.update_document.return_value = True

        success, message, result = self.service.process_expired_documents()

        assert success is True
        assert message == "EXPIRED_DOCUMENTS_PROCESSED_SUCCESS"
        assert result['documents_processed'] == 1

    def test_get_document_statistics(self):
        """Test getting document statistics"""
        mock_stats = {
            'total_documents': 1500,
            'by_status': {
                DocumentStatus.APPROVED.value: 1200,
                DocumentStatus.PENDING.value: 150,
                DocumentStatus.REJECTED.value: 100,
                DocumentStatus.EXPIRED.value: 50
            },
            'by_type': {
                DocumentType.LEGAL_CERTIFICATE.value: 500,
                DocumentType.TAX_EXEMPT_STATUS.value: 400
            }
        }

        self.mock_doc_repo.get_document_statistics.return_value = mock_stats

        success, message, result = self.service.get_document_statistics()

        assert success is True
        assert message == "DOCUMENT_STATISTICS_SUCCESS"
        assert result['total_documents'] == 1500
        assert result['approval_rate'] == 80.0  # 1200/1500 * 100


class TestONLUSService:
    """Tests for ONLUSService"""

    def setup_method(self):
        """Setup test fixtures"""
        self.service = ONLUSService()
        self.mock_org_repo = Mock()
        self.mock_app_repo = Mock()
        self.mock_category_repo = Mock()

        self.service.organization_repo = self.mock_org_repo
        self.service.application_repo = self.mock_app_repo
        self.service.category_repo = self.mock_category_repo

    def test_create_organization_from_application_success(self):
        """Test successful organization creation from approved application"""
        application_id = str(ObjectId())
        admin_id = str(ObjectId())

        # Mock approved application
        mock_application_data = {
            '_id': application_id,
            'organization_name': 'Approved ONLUS',
            'tax_id': '12345678901',
            'email': 'contact@approved.org',
            'category': ONLUSCategory.HEALTHCARE.value,
            'status': ApplicationStatus.APPROVED.value,
            'contact_person': {'name': 'Mario Rossi', 'email': 'president@approved.org'},
            'bank_account': {'iban': 'IT60X0542811101000000123456', 'bank_name': 'Test Bank'},
            'address': {'street': 'Via Test 123', 'city': 'Milano', 'country': 'IT'}
        }

        self.mock_app_repo.find_by_id.return_value = mock_application_data

        # Mock successful organization creation
        mock_organization_id = str(ObjectId())
        self.mock_org_repo.create_organization.return_value = mock_organization_id

        success, message, result = self.service.create_organization_from_application(application_id, admin_id)

        assert success is True
        assert message == "ORGANIZATION_CREATED_SUCCESS"
        assert result['organization_id'] == mock_organization_id

        # Verify organization was created with correct data
        create_call = self.mock_org_repo.create_organization.call_args[0][0]
        assert create_call['name'] == 'Approved ONLUS'
        assert create_call['tax_id'] == '12345678901'
        assert create_call['status'] == OrganizationStatus.ACTIVE.value

    def test_create_organization_application_not_approved(self):
        """Test organization creation from non-approved application"""
        application_id = str(ObjectId())
        admin_id = str(ObjectId())

        mock_application_data = {
            '_id': application_id,
            'status': ApplicationStatus.UNDER_REVIEW.value  # Not approved
        }

        self.mock_app_repo.find_by_id.return_value = mock_application_data

        success, message, result = self.service.create_organization_from_application(application_id, admin_id)

        assert success is False
        assert message == "APPLICATION_NOT_APPROVED"
        assert result is None

    def test_get_public_organizations_success(self):
        """Test getting public organizations list"""
        category = ONLUSCategory.EDUCATION.value
        featured_only = False
        limit = 10
        search_query = "children education"

        mock_organizations = [
            {
                '_id': str(ObjectId()),
                'name': 'Education ONLUS',
                'category': category,
                'description': 'Helping children with education',
                'status': OrganizationStatus.ACTIVE.value,
                'featured': False
            }
        ]

        self.mock_org_repo.get_organizations_by_category.return_value = mock_organizations

        success, message, result = self.service.get_public_organizations(
            category=category,
            featured_only=featured_only,
            limit=limit,
            search_query=search_query
        )

        assert success is True
        assert message == "ORGANIZATIONS_RETRIEVED_SUCCESS"
        assert len(result) == 1
        assert 'tax_id' not in result[0]  # Sensitive data excluded

    def test_get_organization_with_sensitive_data(self):
        """Test getting organization with sensitive data (admin view)"""
        organization_id = str(ObjectId())

        mock_organization_data = {
            '_id': organization_id,
            'name': 'Test ONLUS',
            'tax_id': '12345678901',
            'compliance_score': 85,
            'status': OrganizationStatus.ACTIVE.value
        }

        self.mock_org_repo.find_by_id.return_value = mock_organization_data

        success, message, result = self.service.get_organization(organization_id, include_sensitive=True)

        assert success is True
        assert message == "ORGANIZATION_RETRIEVED_SUCCESS"
        assert result['tax_id'] == '12345678901'  # Sensitive data included
        assert result['compliance_score'] == 85

    def test_update_organization_status(self):
        """Test updating organization status"""
        organization_id = str(ObjectId())
        new_status = OrganizationStatus.SUSPENDED.value
        admin_id = str(ObjectId())
        reason = "Compliance violation"

        mock_organization_data = {
            '_id': organization_id,
            'name': 'Test ONLUS',
            'status': OrganizationStatus.ACTIVE.value
        }

        self.mock_org_repo.find_by_id.return_value = mock_organization_data
        self.mock_org_repo.update_organization.return_value = True

        success, message, result = self.service.update_organization_status(
            organization_id, new_status, admin_id, reason
        )

        assert success is True
        assert message == "ORGANIZATION_STATUS_UPDATED_SUCCESS"
        assert result['new_status'] == new_status

        # Verify organization was updated
        update_call = self.mock_org_repo.update_organization.call_args[0][1]
        assert update_call.status == new_status

    def test_set_featured_status(self):
        """Test setting organization as featured"""
        organization_id = str(ObjectId())
        duration_days = 30
        admin_id = str(ObjectId())

        mock_organization_data = {
            '_id': organization_id,
            'name': 'Featured ONLUS',
            'status': OrganizationStatus.ACTIVE.value,
            'featured': False
        }

        self.mock_org_repo.find_by_id.return_value = mock_organization_data
        self.mock_org_repo.update_organization.return_value = True

        success, message, result = self.service.set_featured_status(organization_id, duration_days, admin_id)

        assert success is True
        assert message == "FEATURED_STATUS_SET_SUCCESS"
        assert result['featured_until'] is not None

        # Verify organization was updated
        update_call = self.mock_org_repo.update_organization.call_args[0][1]
        assert update_call.featured is True
        assert update_call.featured_by == admin_id

    def test_get_organization_statistics(self):
        """Test getting comprehensive organization statistics"""
        mock_stats = {
            'total_organizations': 200,
            'by_status': {
                OrganizationStatus.ACTIVE.value: 180,
                OrganizationStatus.SUSPENDED.value: 15,
                OrganizationStatus.INACTIVE.value: 5
            },
            'by_category': {
                ONLUSCategory.EDUCATION.value: 60,
                ONLUSCategory.HEALTHCARE.value: 50,
                ONLUSCategory.ENVIRONMENT.value: 40
            },
            'total_donations': 1500000.0,
            'total_donors': 5000
        }

        self.mock_org_repo.get_organization_statistics.return_value = mock_stats

        success, message, result = self.service.get_organization_statistics()

        assert success is True
        assert message == "ORGANIZATION_STATISTICS_SUCCESS"
        assert result['organizations']['total_organizations'] == 200
        assert result['organizations']['total_donations'] == 1500000.0
        assert result['category_distribution'][ONLUSCategory.EDUCATION.value] == 60

    def test_get_top_rated_organizations(self):
        """Test getting top-rated organizations"""
        limit = 5

        mock_organizations = [
            {
                '_id': str(ObjectId()),
                'name': 'Top ONLUS 1',
                'compliance_score': 98,
                'total_donations_received': 50000.0
            },
            {
                '_id': str(ObjectId()),
                'name': 'Top ONLUS 2',
                'compliance_score': 95,
                'total_donations_received': 40000.0
            }
        ]

        self.mock_org_repo.get_top_rated_organizations.return_value = mock_organizations

        success, message, result = self.service.get_top_rated_organizations(limit)

        assert success is True
        assert message == "TOP_RATED_ORGANIZATIONS_SUCCESS"
        assert len(result) == 2
        assert result[0]['compliance_score'] == 98

    def test_update_compliance_status(self):
        """Test updating organization compliance status"""
        organization_id = str(ObjectId())
        compliance_status = ComplianceStatus.MINOR_ISSUES.value
        compliance_score = 75
        admin_id = str(ObjectId())
        notes = "Minor documentation issues found"

        mock_organization_data = {
            '_id': organization_id,
            'name': 'Compliance Test ONLUS',
            'compliance_status': ComplianceStatus.COMPLIANT.value,
            'compliance_score': 90
        }

        self.mock_org_repo.find_by_id.return_value = mock_organization_data
        self.mock_org_repo.update_organization.return_value = True

        success, message, result = self.service.update_compliance_status(
            organization_id, compliance_status, compliance_score, admin_id, notes
        )

        assert success is True
        assert message == "COMPLIANCE_STATUS_UPDATED_SUCCESS"
        assert result['new_compliance_status'] == compliance_status
        assert result['new_compliance_score'] == compliance_score

        # Verify organization was updated
        update_call = self.mock_org_repo.update_organization.call_args[0][1]
        assert update_call.compliance_status == compliance_status
        assert update_call.compliance_score == compliance_score