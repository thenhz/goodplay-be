"""
Tests for GOO-17 ONLUS Registry & Verification System Integration

End-to-end integration tests covering complete workflows including
application submission, verification process, document management,
and organization lifecycle.
"""

import pytest
import json
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch, MagicMock
from bson import ObjectId

from tests.core.base_onlus_test import BaseOnlusTest

# Import models for test scenarios
from app.onlus.models.onlus_application import ApplicationStatus, ApplicationPhase, Priority
from app.onlus.models.onlus_document import DocumentType, DocumentStatus
from app.onlus.models.verification_check import VerificationCheckType, CheckStatus, RiskLevel
from app.onlus.models.onlus_organization import OrganizationStatus, ComplianceStatus
from app.onlus.models.onlus_category import ONLUSCategory


class TestApplicationWorkflowIntegration(BaseOnlusTest):
    """Integration tests for complete application workflow"""

    def setUp(self):
        super().setUp()
        self.user_id = str(ObjectId())
        self.admin_id = str(ObjectId())

    def test_complete_application_approval_workflow(self):
        """Test complete application workflow from creation to approval"""

        # Step 1: Create application
        application_data = {
            'organization_name': 'Integration Test ONLUS',
            'tax_id': '12345678901',
            'email': 'contact@integration-test.org',
            'category': ONLUSCategory.EDUCATION.value,
            'description': 'Educational non-profit organization for integration testing',
            'address': {
                'street': 'Via Test 123',
                'city': 'Milano',
                'postal_code': '20100',
                'country': 'IT'
            },
            'contact_person': {
                'name': 'Mario Rossi',
                'role': 'President',
                'email': 'president@integration-test.org',
                'phone': '+39 123 456 7890'
            },
            'bank_account': {
                'iban': 'IT60X0542811101000000123456',
                'bank_name': 'Integration Test Bank'
            }
        }

        # Mock services for each step
        with patch('app.onlus.controllers.application_controller.application_service') as mock_app_service:
            application_id = str(ObjectId())
            mock_app_service.create_application.return_value = (
                True, "APPLICATION_CREATED_SUCCESS", {'application_id': application_id}
            )

            response = self.client.post(
                '/api/onlus/applications',
                json=application_data,
                headers=self.get_auth_headers()
            )

            assert response.status_code == 200
            create_result = json.loads(response.data)
            assert create_result['success'] is True
            application_id = create_result['data']['application_id']

        # Step 2: Upload required documents
        documents_to_upload = [
            {
                'document_type': DocumentType.LEGAL_CERTIFICATE.value,
                'filename': 'legal_certificate.pdf',
                'file_path': '/uploads/legal_certificate.pdf',
                'file_size': 1024000,
                'mime_type': 'application/pdf'
            },
            {
                'document_type': DocumentType.TAX_EXEMPT_STATUS.value,
                'filename': 'tax_exempt.pdf',
                'file_path': '/uploads/tax_exempt.pdf',
                'file_size': 512000,
                'mime_type': 'application/pdf'
            },
            {
                'document_type': DocumentType.FINANCIAL_REPORT.value,
                'filename': 'financial_report.pdf',
                'file_path': '/uploads/financial_report.pdf',
                'file_size': 2048000,
                'mime_type': 'application/pdf'
            }
        ]

        document_ids = []
        with patch('app.onlus.controllers.document_controller.document_service') as mock_doc_service:
            for doc_data in documents_to_upload:
                doc_id = str(ObjectId())
                document_ids.append(doc_id)
                mock_doc_service.upload_document.return_value = (
                    True, "DOCUMENT_UPLOADED_SUCCESS", {'document_id': doc_id}
                )

                response = self.client.post(
                    f'/api/onlus/applications/{application_id}/documents',
                    json=doc_data,
                    headers=self.get_auth_headers()
                )

                assert response.status_code == 200
                upload_result = json.loads(response.data)
                assert upload_result['success'] is True

        # Step 3: Submit application for review
        with patch('app.onlus.controllers.application_controller.application_service') as mock_app_service:
            mock_app_service.submit_application.return_value = (
                True, "APPLICATION_SUBMITTED_SUCCESS", {
                    'application_id': application_id,
                    'review_deadline': datetime.now(timezone.utc) + timedelta(days=14)
                }
            )

            response = self.client.post(
                f'/api/onlus/applications/{application_id}/submit',
                headers=self.get_auth_headers()
            )

            assert response.status_code == 200
            submit_result = json.loads(response.data)
            assert submit_result['success'] is True

        # Step 4: Admin assigns reviewer
        reviewer_id = str(ObjectId())
        with patch('app.onlus.controllers.admin_application_controller.application_service') as mock_admin_service:
            mock_admin_service.assign_reviewer.return_value = (
                True, "REVIEWER_ASSIGNED_SUCCESS", {'reviewer_id': reviewer_id}
            )

            response = self.client.post(
                f'/api/admin/onlus/applications/{application_id}/assign',
                json={'reviewer_id': reviewer_id},
                headers=self.get_admin_headers()
            )

            assert response.status_code == 200
            assign_result = json.loads(response.data)
            assert assign_result['success'] is True

        # Step 5: Initiate verification checks
        with patch('app.onlus.controllers.admin_application_controller.verification_service') as mock_ver_service:
            mock_checks_result = {
                'checks_created': [str(ObjectId()) for _ in range(6)],
                'automated_checks_started': 4,
                'manual_checks_pending': 2
            }
            mock_ver_service.initiate_verification_checks.return_value = (
                True, "VERIFICATION_CHECKS_INITIATED_SUCCESS", mock_checks_result
            )

            response = self.client.post(
                f'/api/admin/onlus/applications/{application_id}/verification/initiate',
                headers=self.get_admin_headers()
            )

            assert response.status_code == 200
            verification_result = json.loads(response.data)
            assert verification_result['success'] is True
            assert len(verification_result['data']['checks_created']) == 6

        # Step 6: Review and approve documents
        with patch('app.onlus.controllers.admin_application_controller.document_service') as mock_doc_service:
            for doc_id in document_ids:
                mock_doc_service.review_document.return_value = (
                    True, "DOCUMENT_REVIEWED_SUCCESS", {'action': 'approve', 'document_id': doc_id}
                )

                response = self.client.post(
                    f'/api/admin/onlus/documents/{doc_id}/review',
                    json={
                        'action': 'approve',
                        'notes': 'Document verified and approved'
                    },
                    headers=self.get_admin_headers()
                )

                assert response.status_code == 200
                review_result = json.loads(response.data)
                assert review_result['success'] is True

        # Step 7: Complete verification checks and approve
        with patch('app.onlus.controllers.admin_application_controller.verification_service') as mock_ver_service:
            mock_ver_service.approve_application_verification.return_value = (
                True, "VERIFICATION_APPROVED_SUCCESS", {'application_id': application_id}
            )

            response = self.client.post(
                f'/api/admin/onlus/applications/{application_id}/verification/approve',
                headers=self.get_admin_headers()
            )

            assert response.status_code == 200
            verification_approval = json.loads(response.data)
            assert verification_approval['success'] is True

        # Step 8: Final application approval and organization creation
        organization_id = str(ObjectId())

        with patch('app.onlus.controllers.admin_application_controller.ONLUSApplicationRepository') as mock_app_repo_class, \
             patch('app.onlus.controllers.admin_application_controller.onlus_service') as mock_onlus_service:

            # Mock application repository
            mock_app_repo = Mock()
            mock_app_repo_class.return_value = mock_app_repo

            mock_application_data = {
                '_id': application_id,
                'applicant_id': self.user_id,
                'organization_name': 'Integration Test ONLUS',
                'status': ApplicationStatus.DUE_DILIGENCE.value
            }
            mock_app_repo.find_by_id.return_value = mock_application_data
            mock_app_repo.update_application.return_value = True

            # Mock organization creation
            mock_onlus_service.create_organization_from_application.return_value = (
                True, "ORGANIZATION_CREATED_SUCCESS", {'organization_id': organization_id}
            )

            response = self.client.post(
                f'/api/admin/onlus/applications/{application_id}/approve',
                json={'conditions': ['Annual reporting required']},
                headers=self.get_admin_headers()
            )

            assert response.status_code == 200
            approval_result = json.loads(response.data)
            assert approval_result['success'] is True
            assert approval_result['data']['organization']['organization_id'] == organization_id

        # Verify complete workflow success
        assert application_id is not None
        assert len(document_ids) == 3
        assert organization_id is not None

    def test_application_rejection_workflow(self):
        """Test application rejection workflow"""
        application_id = str(ObjectId())

        # Step 1: Submit application (mocked as already done)

        # Step 2: Verification checks fail
        with patch('app.onlus.controllers.admin_application_controller.verification_service') as mock_ver_service:
            mock_ver_service.reject_application_verification.return_value = (
                True, "VERIFICATION_REJECTED_SUCCESS", {
                    'application_id': application_id,
                    'rejection_reason': 'Failed fraud screening check'
                }
            )

            response = self.client.post(
                f'/api/admin/onlus/applications/{application_id}/verification/reject',
                json={'rejection_reason': 'Failed fraud screening check'},
                headers=self.get_admin_headers()
            )

            assert response.status_code == 200
            rejection_result = json.loads(response.data)
            assert rejection_result['success'] is True

        # Step 3: Final application rejection
        with patch('app.onlus.controllers.admin_application_controller.ONLUSApplicationRepository') as mock_app_repo_class:
            mock_app_repo = Mock()
            mock_app_repo_class.return_value = mock_app_repo

            mock_application_data = {
                '_id': application_id,
                'applicant_id': self.user_id,
                'status': ApplicationStatus.UNDER_REVIEW.value
            }
            mock_app_repo.find_by_id.return_value = mock_application_data
            mock_app_repo.update_application.return_value = True

            response = self.client.post(
                f'/api/admin/onlus/applications/{application_id}/reject',
                json={'rejection_reason': 'Incomplete documentation and failed verification'},
                headers=self.get_admin_headers()
            )

            assert response.status_code == 200
            final_rejection = json.loads(response.data)
            assert final_rejection['success'] is True
            assert final_rejection['message'] == "APPLICATION_REJECTED_SUCCESS"


class TestDocumentManagementIntegration(BaseOnlusTest):
    """Integration tests for document management workflow"""

    def setUp(self):
        super().setUp()
        self.application_id = str(ObjectId())
        self.user_id = str(ObjectId())
        self.admin_id = str(ObjectId())

    def test_document_lifecycle_workflow(self):
        """Test complete document lifecycle from upload to approval"""

        # Step 1: Upload document
        document_data = {
            'document_type': DocumentType.LEGAL_CERTIFICATE.value,
            'filename': 'certificate.pdf',
            'file_path': '/uploads/certificate.pdf',
            'file_size': 1024000,
            'mime_type': 'application/pdf'
        }

        document_id = str(ObjectId())
        with patch('app.onlus.controllers.document_controller.document_service') as mock_doc_service:
            mock_doc_service.upload_document.return_value = (
                True, "DOCUMENT_UPLOADED_SUCCESS", {'document_id': document_id}
            )

            response = self.client.post(
                f'/api/onlus/applications/{self.application_id}/documents',
                json=document_data,
                headers=self.get_auth_headers()
            )

            assert response.status_code == 200
            upload_result = json.loads(response.data)
            assert upload_result['success'] is True

        # Step 2: Admin reviews and requests resubmission
        with patch('app.onlus.controllers.admin_application_controller.document_service') as mock_doc_service:
            mock_doc_service.review_document.return_value = (
                True, "DOCUMENT_REVIEWED_SUCCESS", {
                    'action': 'resubmit',
                    'document_id': document_id
                }
            )

            response = self.client.post(
                f'/api/admin/onlus/documents/{document_id}/review',
                json={
                    'action': 'resubmit',
                    'resubmission_reason': 'Document quality is poor, please provide clearer scan'
                },
                headers=self.get_admin_headers()
            )

            assert response.status_code == 200
            review_result = json.loads(response.data)
            assert review_result['success'] is True

        # Step 3: User resubmits updated document
        updated_document_data = {
            'document_type': DocumentType.LEGAL_CERTIFICATE.value,
            'filename': 'certificate_updated.pdf',
            'file_path': '/uploads/certificate_updated.pdf',
            'file_size': 1536000,
            'mime_type': 'application/pdf',
            'previous_version_id': document_id
        }

        new_document_id = str(ObjectId())
        with patch('app.onlus.controllers.document_controller.document_service') as mock_doc_service:
            mock_doc_service.upload_document.return_value = (
                True, "DOCUMENT_UPLOADED_SUCCESS", {'document_id': new_document_id}
            )

            response = self.client.post(
                f'/api/onlus/applications/{self.application_id}/documents',
                json=updated_document_data,
                headers=self.get_auth_headers()
            )

            assert response.status_code == 200
            resubmit_result = json.loads(response.data)
            assert resubmit_result['success'] is True

        # Step 4: Admin approves updated document
        with patch('app.onlus.controllers.admin_application_controller.document_service') as mock_doc_service:
            mock_doc_service.review_document.return_value = (
                True, "DOCUMENT_REVIEWED_SUCCESS", {
                    'action': 'approve',
                    'document_id': new_document_id
                }
            )

            response = self.client.post(
                f'/api/admin/onlus/documents/{new_document_id}/review',
                json={
                    'action': 'approve',
                    'notes': 'Updated document is clear and meets requirements'
                },
                headers=self.get_admin_headers()
            )

            assert response.status_code == 200
            approval_result = json.loads(response.data)
            assert approval_result['success'] is True

        # Step 5: User downloads approved document
        with patch('app.onlus.controllers.document_controller.document_service') as mock_doc_service:
            mock_download_url = "https://secure-download.example.com/certificate_updated.pdf"
            mock_doc_service.get_document_download_url.return_value = (
                True, "DOWNLOAD_URL_GENERATED_SUCCESS", mock_download_url
            )

            response = self.client.get(
                f'/api/onlus/documents/{new_document_id}/download',
                headers=self.get_auth_headers()
            )

            assert response.status_code == 200
            download_result = json.loads(response.data)
            assert download_result['success'] is True
            assert download_result['data']['download_url'] == mock_download_url

    def test_document_expiration_workflow(self):
        """Test document expiration and renewal workflow"""
        document_id = str(ObjectId())

        # Step 1: Document expires
        with patch('app.onlus.controllers.admin_application_controller.document_service') as mock_doc_service:
            mock_expired_result = {
                'documents_processed': 5,
                'notifications_sent': 3,
                'organizations_affected': 2
            }
            mock_doc_service.process_expired_documents.return_value = (
                True, "EXPIRED_DOCUMENTS_PROCESSED_SUCCESS", mock_expired_result
            )

            response = self.client.post(
                '/api/admin/onlus/documents/process-expired',
                headers=self.get_admin_headers()
            )

            assert response.status_code == 200
            expiry_result = json.loads(response.data)
            assert expiry_result['success'] is True
            assert expiry_result['data']['documents_processed'] == 5

        # Step 2: Organization uploads renewal document
        renewal_document_data = {
            'document_type': DocumentType.LEGAL_CERTIFICATE.value,
            'filename': 'certificate_renewal.pdf',
            'file_path': '/uploads/certificate_renewal.pdf',
            'file_size': 1024000,
            'mime_type': 'application/pdf',
            'expiration_date': (datetime.now(timezone.utc) + timedelta(days=365)).isoformat()
        }

        renewal_document_id = str(ObjectId())
        with patch('app.onlus.controllers.document_controller.document_service') as mock_doc_service:
            mock_doc_service.upload_document.return_value = (
                True, "DOCUMENT_UPLOADED_SUCCESS", {'document_id': renewal_document_id}
            )

            response = self.client.post(
                f'/api/onlus/applications/{self.application_id}/documents',
                json=renewal_document_data,
                headers=self.get_auth_headers()
            )

            assert response.status_code == 200
            renewal_result = json.loads(response.data)
            assert renewal_result['success'] is True


class TestVerificationProcessIntegration(BaseOnlusTest):
    """Integration tests for verification process"""

    def setUp(self):
        super().setUp()
        self.application_id = str(ObjectId())
        self.admin_id = str(ObjectId())

    def test_automated_verification_workflow(self):
        """Test automated verification checks workflow"""

        # Step 1: Initiate verification checks
        with patch('app.onlus.controllers.admin_application_controller.verification_service') as mock_ver_service:
            mock_checks_result = {
                'checks_created': [str(ObjectId()) for _ in range(6)],
                'automated_checks_started': 4,
                'manual_checks_pending': 2
            }
            mock_ver_service.initiate_verification_checks.return_value = (
                True, "VERIFICATION_CHECKS_INITIATED_SUCCESS", mock_checks_result
            )

            response = self.client.post(
                f'/api/admin/onlus/applications/{self.application_id}/verification/initiate',
                headers=self.get_admin_headers()
            )

            assert response.status_code == 200
            initiation_result = json.loads(response.data)
            assert initiation_result['success'] is True
            check_ids = initiation_result['data']['checks_created']

        # Step 2: Get verification summary (checks in progress)
        with patch('app.onlus.controllers.admin_application_controller.verification_service') as mock_ver_service:
            mock_summary = {
                'total_checks': 6,
                'completed_checks': 2,
                'pending_checks': 4,
                'overall_risk_level': RiskLevel.MEDIUM.value,
                'verification_status': 'in_progress'
            }
            mock_ver_service.get_verification_summary.return_value = (
                True, "VERIFICATION_SUMMARY_SUCCESS", mock_summary
            )

            response = self.client.get(
                f'/api/admin/onlus/applications/{self.application_id}/verification/summary',
                headers=self.get_admin_headers()
            )

            assert response.status_code == 200
            summary_result = json.loads(response.data)
            assert summary_result['success'] is True
            assert summary_result['data']['total_checks'] == 6

        # Step 3: Complete manual verification check
        manual_check_id = check_ids[0] if check_ids else str(ObjectId())
        with patch('app.onlus.controllers.admin_application_controller.verification_service') as mock_ver_service:
            mock_ver_service.perform_manual_check.return_value = (
                True, "MANUAL_CHECK_COMPLETED_SUCCESS", {'check_id': manual_check_id}
            )

            response = self.client.post(
                f'/api/admin/onlus/verification/checks/{manual_check_id}/review',
                json={
                    'result': 'approved',
                    'score': 92.0,
                    'notes': 'Background check completed successfully',
                    'findings': [{'type': 'identity_verification', 'result': 'passed'}]
                },
                headers=self.get_admin_headers()
            )

            assert response.status_code == 200
            manual_result = json.loads(response.data)
            assert manual_result['success'] is True

        # Step 4: Final verification summary (all checks completed)
        with patch('app.onlus.controllers.admin_application_controller.verification_service') as mock_ver_service:
            mock_final_summary = {
                'total_checks': 6,
                'completed_checks': 6,
                'pending_checks': 0,
                'overall_risk_level': RiskLevel.LOW.value,
                'verification_status': 'completed',
                'average_score': 88.5
            }
            mock_ver_service.get_verification_summary.return_value = (
                True, "VERIFICATION_SUMMARY_SUCCESS", mock_final_summary
            )

            response = self.client.get(
                f'/api/admin/onlus/applications/{self.application_id}/verification/summary',
                headers=self.get_admin_headers()
            )

            assert response.status_code == 200
            final_summary = json.loads(response.data)
            assert final_summary['success'] is True
            assert final_summary['data']['completed_checks'] == 6
            assert final_summary['data']['overall_risk_level'] == RiskLevel.LOW.value

    def test_high_risk_verification_workflow(self):
        """Test verification workflow for high-risk application"""

        # Step 1: Verification checks reveal high risk
        with patch('app.onlus.controllers.admin_application_controller.verification_service') as mock_ver_service:
            mock_high_risk_summary = {
                'total_checks': 6,
                'completed_checks': 6,
                'pending_checks': 0,
                'overall_risk_level': RiskLevel.HIGH.value,
                'verification_status': 'requires_review',
                'risk_factors': ['Suspicious financial patterns', 'Incomplete documentation']
            }
            mock_ver_service.get_verification_summary.return_value = (
                True, "VERIFICATION_SUMMARY_SUCCESS", mock_high_risk_summary
            )

            response = self.client.get(
                f'/api/admin/onlus/applications/{self.application_id}/verification/summary',
                headers=self.get_admin_headers()
            )

            assert response.status_code == 200
            risk_summary = json.loads(response.data)
            assert risk_summary['success'] is True
            assert risk_summary['data']['overall_risk_level'] == RiskLevel.HIGH.value

        # Step 2: Admin rejects due to high risk
        with patch('app.onlus.controllers.admin_application_controller.verification_service') as mock_ver_service:
            mock_ver_service.reject_application_verification.return_value = (
                True, "VERIFICATION_REJECTED_SUCCESS", {
                    'application_id': self.application_id,
                    'rejection_reason': 'High-risk profile detected in verification checks'
                }
            )

            response = self.client.post(
                f'/api/admin/onlus/applications/{self.application_id}/verification/reject',
                json={'rejection_reason': 'High-risk profile detected in verification checks'},
                headers=self.get_admin_headers()
            )

            assert response.status_code == 200
            rejection_result = json.loads(response.data)
            assert rejection_result['success'] is True


class TestOrganizationManagementIntegration(BaseOnlusTest):
    """Integration tests for organization management"""

    def setUp(self):
        super().setUp()
        self.organization_id = str(ObjectId())
        self.admin_id = str(ObjectId())

    def test_organization_lifecycle_workflow(self):
        """Test complete organization lifecycle management"""

        # Step 1: Get organization details (admin view)
        with patch('app.onlus.controllers.admin_onlus_controller.onlus_service') as mock_onlus_service:
            mock_org_data = {
                '_id': self.organization_id,
                'name': 'Lifecycle Test ONLUS',
                'tax_id': '12345678901',
                'status': OrganizationStatus.ACTIVE.value,
                'compliance_status': ComplianceStatus.COMPLIANT.value,
                'compliance_score': 85
            }
            mock_onlus_service.get_organization.return_value = (
                True, "ORGANIZATION_RETRIEVED_SUCCESS", mock_org_data
            )

            response = self.client.get(
                f'/api/admin/onlus/organizations/{self.organization_id}',
                headers=self.get_admin_headers()
            )

            assert response.status_code == 200
            org_result = json.loads(response.data)
            assert org_result['success'] is True
            assert org_result['data']['status'] == OrganizationStatus.ACTIVE.value

        # Step 2: Set organization as featured
        with patch('app.onlus.controllers.admin_onlus_controller.onlus_service') as mock_onlus_service:
            mock_onlus_service.set_featured_status.return_value = (
                True, "FEATURED_STATUS_SET_SUCCESS", {
                    'organization_id': self.organization_id,
                    'featured_until': datetime.now(timezone.utc) + timedelta(days=30)
                }
            )

            response = self.client.post(
                f'/api/admin/onlus/organizations/{self.organization_id}/featured',
                json={'duration_days': 30},
                headers=self.get_admin_headers()
            )

            assert response.status_code == 200
            featured_result = json.loads(response.data)
            assert featured_result['success'] is True

        # Step 3: Update compliance status
        with patch('app.onlus.controllers.admin_onlus_controller.onlus_service') as mock_onlus_service:
            mock_onlus_service.update_compliance_status.return_value = (
                True, "COMPLIANCE_STATUS_UPDATED_SUCCESS", {
                    'organization_id': self.organization_id,
                    'new_compliance_status': ComplianceStatus.MINOR_ISSUES.value,
                    'new_compliance_score': 75
                }
            )

            response = self.client.put(
                f'/api/admin/onlus/organizations/{self.organization_id}/compliance',
                json={
                    'compliance_status': ComplianceStatus.MINOR_ISSUES.value,
                    'compliance_score': 75,
                    'notes': 'Minor documentation issues found during review'
                },
                headers=self.get_admin_headers()
            )

            assert response.status_code == 200
            compliance_result = json.loads(response.data)
            assert compliance_result['success'] is True

        # Step 4: Suspend organization due to compliance issues
        with patch('app.onlus.controllers.admin_onlus_controller.onlus_service') as mock_onlus_service:
            mock_onlus_service.update_organization_status.return_value = (
                True, "ORGANIZATION_STATUS_UPDATED_SUCCESS", {
                    'organization_id': self.organization_id,
                    'new_status': OrganizationStatus.SUSPENDED.value
                }
            )

            response = self.client.put(
                f'/api/admin/onlus/organizations/{self.organization_id}/status',
                json={
                    'status': OrganizationStatus.SUSPENDED.value,
                    'reason': 'Compliance issues require immediate attention'
                },
                headers=self.get_admin_headers()
            )

            assert response.status_code == 200
            suspension_result = json.loads(response.data)
            assert suspension_result['success'] is True

        # Step 5: Remove featured status (suspended organizations shouldn't be featured)
        with patch('app.onlus.controllers.admin_onlus_controller.onlus_service') as mock_onlus_service:
            mock_onlus_service.remove_featured_status.return_value = (
                True, "FEATURED_STATUS_REMOVED_SUCCESS", {'organization_id': self.organization_id}
            )

            response = self.client.delete(
                f'/api/admin/onlus/organizations/{self.organization_id}/featured',
                headers=self.get_admin_headers()
            )

            assert response.status_code == 200
            removal_result = json.loads(response.data)
            assert removal_result['success'] is True

    def test_public_organization_discovery_workflow(self):
        """Test public organization discovery and search"""

        # Step 1: Get all organizations (public view)
        with patch('app.onlus.controllers.onlus_controller.onlus_service') as mock_onlus_service:
            mock_organizations = [
                {
                    '_id': str(ObjectId()),
                    'name': 'Public ONLUS 1',
                    'category': ONLUSCategory.EDUCATION.value,
                    'description': 'Educational organization',
                    'status': OrganizationStatus.ACTIVE.value
                },
                {
                    '_id': str(ObjectId()),
                    'name': 'Public ONLUS 2',
                    'category': ONLUSCategory.HEALTHCARE.value,
                    'description': 'Healthcare organization',
                    'status': OrganizationStatus.ACTIVE.value
                }
            ]
            mock_onlus_service.get_public_organizations.return_value = (
                True, "ORGANIZATIONS_RETRIEVED_SUCCESS", mock_organizations
            )

            response = self.client.get('/api/onlus/organizations')

            assert response.status_code == 200
            orgs_result = json.loads(response.data)
            assert orgs_result['success'] is True
            assert len(orgs_result['data']) == 2

        # Step 2: Search organizations by category
        with patch('app.onlus.controllers.onlus_controller.onlus_service') as mock_onlus_service:
            mock_education_orgs = [mock_organizations[0]]  # Only education org
            mock_onlus_service.get_public_organizations.return_value = (
                True, "ORGANIZATIONS_RETRIEVED_SUCCESS", mock_education_orgs
            )

            response = self.client.get(
                f'/api/onlus/organizations?category={ONLUSCategory.EDUCATION.value}&limit=10'
            )

            assert response.status_code == 200
            category_result = json.loads(response.data)
            assert category_result['success'] is True
            assert len(category_result['data']) == 1

        # Step 3: Get featured organizations
        with patch('app.onlus.controllers.onlus_controller.onlus_service') as mock_onlus_service:
            mock_featured = [
                {
                    '_id': str(ObjectId()),
                    'name': 'Featured ONLUS',
                    'featured': True,
                    'featured_until': datetime.now(timezone.utc) + timedelta(days=10)
                }
            ]
            mock_onlus_service.get_public_organizations.return_value = (
                True, "ORGANIZATIONS_RETRIEVED_SUCCESS", mock_featured
            )

            response = self.client.get('/api/onlus/organizations/featured')

            assert response.status_code == 200
            featured_result = json.loads(response.data)
            assert featured_result['success'] is True

        # Step 4: Get top-rated organizations
        with patch('app.onlus.controllers.onlus_controller.onlus_service') as mock_onlus_service:
            mock_top_rated = [
                {
                    '_id': str(ObjectId()),
                    'name': 'Top Rated ONLUS',
                    'compliance_score': 98,
                    'total_donations_received': 50000.0
                }
            ]
            mock_onlus_service.get_top_rated_organizations.return_value = (
                True, "TOP_RATED_ORGANIZATIONS_SUCCESS", mock_top_rated
            )

            response = self.client.get('/api/onlus/organizations/top-rated?limit=5')

            assert response.status_code == 200
            top_rated_result = json.loads(response.data)
            assert top_rated_result['success'] is True

        # Step 5: Get public statistics
        with patch('app.onlus.controllers.onlus_controller.onlus_service') as mock_onlus_service:
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
            mock_onlus_service.get_organization_statistics.return_value = (
                True, "ORGANIZATION_STATISTICS_SUCCESS", mock_stats
            )

            response = self.client.get('/api/onlus/statistics')

            assert response.status_code == 200
            stats_result = json.loads(response.data)
            assert stats_result['success'] is True
            assert stats_result['message'] == "PUBLIC_STATISTICS_RETRIEVED_SUCCESS"

            # Verify sensitive data is filtered out in public view
            public_stats = stats_result['data']
            assert 'total_organizations' in public_stats
            assert 'total_donations' in public_stats
            assert 'active_organizations' in public_stats
            assert 'category_distribution' in public_stats


class TestSystemIntegrationScenarios(BaseOnlusTest):
    """Integration tests for complex system scenarios"""

    def test_multi_application_processing(self):
        """Test processing multiple applications simultaneously"""
        application_ids = [str(ObjectId()) for _ in range(3)]

        # Mock multiple applications for admin review
        with patch('app.onlus.controllers.admin_application_controller.application_service') as mock_app_service:
            mock_applications = [
                {
                    '_id': app_id,
                    'organization_name': f'Multi Test ONLUS {i+1}',
                    'status': ApplicationStatus.SUBMITTED.value,
                    'submission_date': datetime.now(timezone.utc) - timedelta(days=i+1)
                }
                for i, app_id in enumerate(application_ids)
            ]
            mock_app_service.get_applications_for_admin_review.return_value = (
                True, "APPLICATIONS_FOR_REVIEW_SUCCESS", mock_applications
            )

            response = self.client.get(
                '/api/admin/onlus/applications',
                headers=self.get_admin_headers()
            )

            assert response.status_code == 200
            apps_result = json.loads(response.data)
            assert apps_result['success'] is True
            assert len(apps_result['data']) == 3

    def test_system_statistics_integration(self):
        """Test comprehensive system statistics"""

        # Get application statistics
        with patch('app.onlus.controllers.admin_application_controller.application_service') as mock_app_service:
            mock_app_stats = {
                'total_applications': 150,
                'by_status': {
                    ApplicationStatus.APPROVED.value: 85,
                    ApplicationStatus.SUBMITTED.value: 30
                },
                'approval_rate': 56.67
            }
            mock_app_service.get_application_statistics.return_value = (
                True, "APPLICATION_STATISTICS_SUCCESS", mock_app_stats
            )

            response = self.client.get(
                '/api/admin/onlus/applications/statistics',
                headers=self.get_admin_headers()
            )

            assert response.status_code == 200
            app_stats_result = json.loads(response.data)
            assert app_stats_result['success'] is True
            assert app_stats_result['data']['total_applications'] == 150

        # Get organization statistics
        with patch('app.onlus.controllers.admin_onlus_controller.onlus_service') as mock_onlus_service:
            mock_org_stats = {
                'organizations': {
                    'total_organizations': 200,
                    'total_donations': 1500000.0,
                    'total_donors': 5000
                },
                'category_distribution': {
                    ONLUSCategory.EDUCATION.value: 60,
                    ONLUSCategory.HEALTHCARE.value: 50
                }
            }
            mock_onlus_service.get_organization_statistics.return_value = (
                True, "ORGANIZATION_STATISTICS_SUCCESS", mock_org_stats
            )

            response = self.client.get(
                '/api/admin/onlus/organizations/statistics',
                headers=self.get_admin_headers()
            )

            assert response.status_code == 200
            org_stats_result = json.loads(response.data)
            assert org_stats_result['success'] is True
            assert org_stats_result['data']['organizations']['total_organizations'] == 200

        # Get verification statistics
        with patch('app.onlus.controllers.admin_onlus_controller.verification_service') as mock_ver_service:
            mock_ver_stats = {
                'total_checks': 500,
                'success_rate': 92.5,
                'average_completion_time': 2.5
            }
            mock_ver_service.get_verification_statistics.return_value = (
                True, "VERIFICATION_STATISTICS_SUCCESS", mock_ver_stats
            )

            response = self.client.get(
                '/api/admin/onlus/verification/statistics',
                headers=self.get_admin_headers()
            )

            assert response.status_code == 200
            ver_stats_result = json.loads(response.data)
            assert ver_stats_result['success'] is True
            assert ver_stats_result['data']['total_checks'] == 500

        # Get document statistics
        with patch('app.onlus.controllers.admin_application_controller.document_service') as mock_doc_service:
            mock_doc_stats = {
                'total_documents': 1500,
                'approval_rate': 80.0,
                'by_status': {
                    DocumentStatus.APPROVED.value: 1200,
                    DocumentStatus.PENDING.value: 150
                }
            }
            mock_doc_service.get_document_statistics.return_value = (
                True, "DOCUMENT_STATISTICS_SUCCESS", mock_doc_stats
            )

            response = self.client.get(
                '/api/admin/onlus/documents/statistics',
                headers=self.get_admin_headers()
            )

            assert response.status_code == 200
            doc_stats_result = json.loads(response.data)
            assert doc_stats_result['success'] is True
            assert doc_stats_result['data']['total_documents'] == 1500