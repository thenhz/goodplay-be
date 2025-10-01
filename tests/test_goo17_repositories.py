"""
Tests for GOO-17 ONLUS Registry & Verification System Repositories

Tests all ONLUS repository layer functionality including CRUD operations,
complex queries, aggregations, and database interactions.
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch, MagicMock
from bson import ObjectId
from decimal import Decimal

# Import repositories to test
from app.onlus.repositories.onlus_category_repository import ONLUSCategoryRepository
from app.onlus.repositories.onlus_document_repository import ONLUSDocumentRepository
from app.onlus.repositories.verification_check_repository import VerificationCheckRepository
from app.onlus.repositories.onlus_application_repository import ONLUSApplicationRepository
from app.onlus.repositories.onlus_organization_repository import ONLUSOrganizationRepository

# Import models
from app.onlus.models.onlus_category import ONLUSCategory
from app.onlus.models.onlus_document import DocumentType, DocumentStatus
from app.onlus.models.verification_check import VerificationCheckType, CheckStatus, RiskLevel
from app.onlus.models.onlus_application import ApplicationStatus, ApplicationPhase, Priority
from app.onlus.models.onlus_organization import OrganizationStatus, ComplianceStatus


class TestONLUSCategoryRepository:
    """Tests for ONLUSCategoryRepository"""

    def setup_method(self):
        """Setup test fixtures"""
        self.repository = ONLUSCategoryRepository()
        self.mock_collection = Mock()
        self.repository.collection = self.mock_collection

    def test_get_active_categories_success(self):
        """Test retrieving active categories"""
        # Mock database response
        mock_categories = [
            {
                '_id': str(ObjectId()),
                'category': 'healthcare',
                'name': 'Healthcare',
                'description': 'Healthcare organizations',
                'active': True
            },
            {
                '_id': str(ObjectId()),
                'category': 'education',
                'name': 'Education',
                'description': 'Educational institutions',
                'active': True
            }
        ]
        self.mock_collection.find.return_value = mock_categories

        categories = self.repository.get_active_categories()

        # Verify query
        self.mock_collection.find.assert_called_once_with({'active': True})
        assert len(categories) == 2
        assert categories[0].category == 'healthcare'
        assert categories[1].category == 'education'

    def test_get_category_by_name_found(self):
        """Test finding category by name"""
        mock_category = {
            '_id': str(ObjectId()),
            'category': 'environment',
            'name': 'Environment',
            'active': True
        }
        self.mock_collection.find_one.return_value = mock_category

        category = self.repository.get_category_by_name('environment')

        self.mock_collection.find_one.assert_called_once_with({'category': 'environment'})
        assert category is not None
        assert category.category == 'environment'

    def test_get_category_by_name_not_found(self):
        """Test finding non-existent category"""
        self.mock_collection.find_one.return_value = None

        category = self.repository.get_category_by_name('nonexistent')

        assert category is None

    def test_get_verification_requirements_for_category(self):
        """Test getting verification requirements for specific category"""
        mock_category = {
            '_id': str(ObjectId()),
            'category': 'healthcare',
            'verification_requirements': ['medical_license', 'insurance_coverage'],
            'compliance_standards': ['medical_regulations']
        }
        self.mock_collection.find_one.return_value = mock_category

        requirements = self.repository.get_verification_requirements_for_category('healthcare')

        assert requirements == ['medical_license', 'insurance_coverage']

    def test_get_verification_requirements_category_not_found(self):
        """Test getting requirements for non-existent category"""
        self.mock_collection.find_one.return_value = None

        requirements = self.repository.get_verification_requirements_for_category('nonexistent')

        assert requirements == []


class TestONLUSDocumentRepository:
    """Tests for ONLUSDocumentRepository"""

    def setup_method(self):
        """Setup test fixtures"""
        self.repository = ONLUSDocumentRepository()
        self.mock_collection = Mock()
        self.repository.collection = self.mock_collection

    def test_find_by_application_id_success(self):
        """Test finding documents by application ID"""
        application_id = str(ObjectId())
        mock_documents = [
            {
                '_id': str(ObjectId()),
                'application_id': application_id,
                'document_type': DocumentType.LEGAL_CERTIFICATE.value,
                'status': DocumentStatus.APPROVED.value
            },
            {
                '_id': str(ObjectId()),
                'application_id': application_id,
                'document_type': DocumentType.TAX_EXEMPT_STATUS.value,
                'status': DocumentStatus.PENDING.value
            }
        ]
        self.mock_collection.find.return_value = mock_documents

        documents = self.repository.find_by_application_id(application_id)

        self.mock_collection.find.assert_called_once_with({'application_id': application_id})
        assert len(documents) == 2
        assert documents[0].document_type == DocumentType.LEGAL_CERTIFICATE.value
        assert documents[1].status == DocumentStatus.PENDING.value

    def test_find_current_version_documents(self):
        """Test finding current version documents"""
        application_id = str(ObjectId())
        mock_documents = [
            {
                '_id': str(ObjectId()),
                'application_id': application_id,
                'document_type': DocumentType.FINANCIAL_REPORT.value,
                'is_current_version': True,
                'version': 2
            }
        ]
        self.mock_collection.find.return_value = mock_documents

        documents = self.repository.find_current_version_documents(application_id)

        expected_query = {
            'application_id': application_id,
            'is_current_version': True
        }
        self.mock_collection.find.assert_called_once_with(expected_query)
        assert len(documents) == 1
        assert documents[0].version == 2

    def test_find_expired_documents(self):
        """Test finding expired documents"""
        current_time = datetime.now(timezone.utc)
        mock_documents = [
            {
                '_id': str(ObjectId()),
                'document_type': DocumentType.INSURANCE_COVERAGE.value,
                'expiration_date': current_time - timedelta(days=1),
                'status': DocumentStatus.APPROVED.value
            }
        ]
        self.mock_collection.find.return_value = mock_documents

        documents = self.repository.find_expired_documents()

        # Verify query looks for expired documents
        query_call = self.mock_collection.find.call_args[0][0]
        assert '$lt' in query_call['expiration_date']
        assert len(documents) == 1

    def test_find_expiring_soon_documents(self):
        """Test finding documents expiring soon"""
        mock_documents = [
            {
                '_id': str(ObjectId()),
                'document_type': DocumentType.LEGAL_CERTIFICATE.value,
                'expiration_date': datetime.now(timezone.utc) + timedelta(days=5),
                'status': DocumentStatus.APPROVED.value
            }
        ]
        self.mock_collection.find.return_value = mock_documents

        days_ahead = 7
        documents = self.repository.find_expiring_soon_documents(days_ahead)

        # Verify query looks for documents expiring within specified days
        query_call = self.mock_collection.find.call_args[0][0]
        assert '$lte' in query_call['expiration_date']
        assert '$gt' in query_call['expiration_date']
        assert len(documents) == 1

    def test_get_documents_for_review(self):
        """Test getting documents pending review"""
        mock_documents = [
            {
                '_id': str(ObjectId()),
                'document_type': DocumentType.TAX_EXEMPT_STATUS.value,
                'status': DocumentStatus.UNDER_REVIEW.value,
                'uploaded_at': datetime.now(timezone.utc) - timedelta(hours=1)
            }
        ]
        self.mock_collection.find.return_value.sort.return_value.limit.return_value = mock_documents

        documents = self.repository.get_documents_for_review(
            document_type=DocumentType.TAX_EXEMPT_STATUS.value,
            limit=10
        )

        # Verify query filters for review status and document type
        query_call = self.mock_collection.find.call_args[0][0]
        assert query_call['status'] == DocumentStatus.UNDER_REVIEW.value
        assert query_call['document_type'] == DocumentType.TAX_EXEMPT_STATUS.value
        assert len(documents) == 1

    def test_get_document_statistics(self):
        """Test getting document statistics"""
        mock_stats = [
            {
                '_id': {'status': DocumentStatus.APPROVED.value},
                'count': 150
            },
            {
                '_id': {'status': DocumentStatus.PENDING.value},
                'count': 45
            },
            {
                '_id': {'status': DocumentStatus.REJECTED.value},
                'count': 12
            }
        ]
        self.mock_collection.aggregate.return_value = mock_stats

        stats = self.repository.get_document_statistics()

        # Verify aggregation pipeline
        pipeline_call = self.mock_collection.aggregate.call_args[0][0]
        assert any('$group' in stage for stage in pipeline_call)
        assert stats['total_documents'] == 207  # Sum of all counts
        assert stats['by_status'][DocumentStatus.APPROVED.value] == 150

    def test_update_document_success(self):
        """Test successful document update"""
        document_id = str(ObjectId())
        mock_document = Mock()
        mock_document.to_dict.return_value = {
            '_id': document_id,
            'status': DocumentStatus.APPROVED.value,
            'review_date': datetime.now(timezone.utc)
        }

        self.mock_collection.update_one.return_value.modified_count = 1

        success = self.repository.update_document(document_id, mock_document)

        self.mock_collection.update_one.assert_called_once()
        assert success is True

    def test_update_document_not_found(self):
        """Test document update when document not found"""
        document_id = str(ObjectId())
        mock_document = Mock()
        mock_document.to_dict.return_value = {'_id': document_id}

        self.mock_collection.update_one.return_value.modified_count = 0

        success = self.repository.update_document(document_id, mock_document)

        assert success is False


class TestVerificationCheckRepository:
    """Tests for VerificationCheckRepository"""

    def setup_method(self):
        """Setup test fixtures"""
        self.repository = VerificationCheckRepository()
        self.mock_collection = Mock()
        self.repository.collection = self.mock_collection

    def test_find_by_application_id_success(self):
        """Test finding verification checks by application ID"""
        application_id = str(ObjectId())
        mock_checks = [
            {
                '_id': str(ObjectId()),
                'application_id': application_id,
                'check_type': VerificationCheckType.LEGAL_STATUS.value,
                'status': CheckStatus.COMPLETED.value,
                'score': 95.0
            },
            {
                '_id': str(ObjectId()),
                'application_id': application_id,
                'check_type': VerificationCheckType.FRAUD_SCREENING.value,
                'status': CheckStatus.IN_PROGRESS.value
            }
        ]
        self.mock_collection.find.return_value = mock_checks

        checks = self.repository.find_by_application_id(application_id)

        self.mock_collection.find.assert_called_once_with({'application_id': application_id})
        assert len(checks) == 2
        assert checks[0].check_type == VerificationCheckType.LEGAL_STATUS.value
        assert checks[1].status == CheckStatus.IN_PROGRESS.value

    def test_find_pending_manual_checks(self):
        """Test finding checks that need manual review"""
        mock_checks = [
            {
                '_id': str(ObjectId()),
                'check_type': VerificationCheckType.BACKGROUND_CHECK.value,
                'status': CheckStatus.PENDING.value,
                'automated': False
            }
        ]
        self.mock_collection.find.return_value.sort.return_value = mock_checks

        checks = self.repository.find_pending_manual_checks()

        # Verify query for manual checks
        query_call = self.mock_collection.find.call_args[0][0]
        assert query_call['automated'] is False
        assert CheckStatus.PENDING.value in query_call['status']['$in']
        assert len(checks) == 1

    def test_find_failed_checks(self):
        """Test finding failed verification checks"""
        application_id = str(ObjectId())
        mock_checks = [
            {
                '_id': str(ObjectId()),
                'application_id': application_id,
                'check_type': VerificationCheckType.TAX_EXEMPT_STATUS.value,
                'status': CheckStatus.FAILED.value,
                'error_details': 'Tax ID not found'
            }
        ]
        self.mock_collection.find.return_value = mock_checks

        checks = self.repository.find_failed_checks(application_id)

        expected_query = {
            'application_id': application_id,
            'status': CheckStatus.FAILED.value
        }
        self.mock_collection.find.assert_called_once_with(expected_query)
        assert len(checks) == 1
        assert checks[0].error_details == 'Tax ID not found'

    def test_get_overall_risk_assessment(self):
        """Test calculating overall risk assessment"""
        application_id = str(ObjectId())
        mock_checks = [
            Mock(status=CheckStatus.COMPLETED.value, get_risk_score=Mock(return_value=2.0)),
            Mock(status=CheckStatus.COMPLETED.value, get_risk_score=Mock(return_value=1.0)),
            Mock(status=CheckStatus.COMPLETED.value, get_risk_score=Mock(return_value=3.0))
        ]

        with patch.object(self.repository, 'find_by_application_id', return_value=mock_checks):
            risk_assessment = self.repository.get_overall_risk_assessment(application_id)

        assert risk_assessment['average_risk_score'] == 2.0  # (2+1+3)/3
        assert risk_assessment['overall_risk_level'] == RiskLevel.MEDIUM.value
        assert risk_assessment['completed_checks'] == 3

    def test_get_check_statistics(self):
        """Test getting verification check statistics"""
        mock_stats = [
            {
                '_id': {'check_type': VerificationCheckType.LEGAL_STATUS.value},
                'total': 100,
                'completed': 95,
                'failed': 3,
                'pending': 2,
                'avg_score': 88.5
            }
        ]
        self.mock_collection.aggregate.return_value = mock_stats

        stats = self.repository.get_check_statistics()

        # Verify aggregation pipeline structure
        pipeline_call = self.mock_collection.aggregate.call_args[0][0]
        assert any('$group' in stage for stage in pipeline_call)
        assert stats['by_check_type'][VerificationCheckType.LEGAL_STATUS.value]['total'] == 100

    def test_create_check_success(self):
        """Test successful verification check creation"""
        check_data = {
            'application_id': str(ObjectId()),
            'check_type': VerificationCheckType.FRAUD_SCREENING.value,
            'initiated_by': str(ObjectId()),
            'automated': True
        }

        mock_result = Mock()
        mock_result.inserted_id = ObjectId()
        self.mock_collection.insert_one.return_value = mock_result

        check_id = self.repository.create_check(check_data)

        self.mock_collection.insert_one.assert_called_once()
        assert check_id is not None

    def test_update_check_success(self):
        """Test successful verification check update"""
        check_id = str(ObjectId())
        mock_check = Mock()
        mock_check.to_dict.return_value = {
            '_id': check_id,
            'status': CheckStatus.COMPLETED.value,
            'completion_date': datetime.now(timezone.utc)
        }

        self.mock_collection.update_one.return_value.modified_count = 1

        success = self.repository.update_check(check_id, mock_check)

        self.mock_collection.update_one.assert_called_once()
        assert success is True


class TestONLUSApplicationRepository:
    """Tests for ONLUSApplicationRepository"""

    def setup_method(self):
        """Setup test fixtures"""
        self.repository = ONLUSApplicationRepository()
        self.mock_collection = Mock()
        self.repository.collection = self.mock_collection

    def test_find_by_applicant_id_success(self):
        """Test finding applications by applicant ID"""
        applicant_id = str(ObjectId())
        mock_applications = [
            {
                '_id': str(ObjectId()),
                'applicant_id': applicant_id,
                'organization_name': 'Test ONLUS 1',
                'status': ApplicationStatus.SUBMITTED.value
            },
            {
                '_id': str(ObjectId()),
                'applicant_id': applicant_id,
                'organization_name': 'Test ONLUS 2',
                'status': ApplicationStatus.DRAFT.value
            }
        ]
        self.mock_collection.find.return_value = mock_applications

        applications = self.repository.find_by_applicant_id(applicant_id)

        self.mock_collection.find.assert_called_once_with({'applicant_id': applicant_id})
        assert len(applications) == 2

    def test_find_by_status_success(self):
        """Test finding applications by status"""
        status = ApplicationStatus.UNDER_REVIEW.value
        mock_applications = [
            {
                '_id': str(ObjectId()),
                'organization_name': 'Review ONLUS 1',
                'status': status
            }
        ]
        self.mock_collection.find.return_value.sort.return_value = mock_applications

        applications = self.repository.find_by_status(status)

        self.mock_collection.find.assert_called_once_with({'status': status})
        assert len(applications) == 1

    def test_get_pending_applications(self):
        """Test getting applications pending review"""
        mock_applications = [
            {
                '_id': str(ObjectId()),
                'organization_name': 'Pending ONLUS',
                'status': ApplicationStatus.SUBMITTED.value,
                'submission_date': datetime.now(timezone.utc) - timedelta(days=1)
            }
        ]
        self.mock_collection.find.return_value.sort.return_value = mock_applications

        applications = self.repository.get_pending_applications()

        # Verify query for pending statuses
        query_call = self.mock_collection.find.call_args[0][0]
        pending_statuses = [
            ApplicationStatus.SUBMITTED.value,
            ApplicationStatus.UNDER_REVIEW.value,
            ApplicationStatus.DOCUMENTATION_PENDING.value,
            ApplicationStatus.DUE_DILIGENCE.value
        ]
        assert query_call['status']['$in'] == pending_statuses

    def test_get_applications_by_reviewer(self):
        """Test getting applications assigned to specific reviewer"""
        reviewer_id = str(ObjectId())
        mock_applications = [
            {
                '_id': str(ObjectId()),
                'assigned_reviewer': reviewer_id,
                'organization_name': 'Assigned ONLUS',
                'status': ApplicationStatus.UNDER_REVIEW.value
            }
        ]
        self.mock_collection.find.return_value.sort.return_value = mock_applications

        applications = self.repository.get_applications_by_reviewer(reviewer_id)

        expected_query = {
            'assigned_reviewer': reviewer_id,
            'status': {'$in': [
                ApplicationStatus.SUBMITTED.value,
                ApplicationStatus.UNDER_REVIEW.value,
                ApplicationStatus.DOCUMENTATION_PENDING.value,
                ApplicationStatus.DUE_DILIGENCE.value
            ]}
        }
        self.mock_collection.find.assert_called_once_with(expected_query)

    def test_get_applications_by_priority(self):
        """Test getting applications by priority"""
        priority = Priority.HIGH.value
        mock_applications = [
            {
                '_id': str(ObjectId()),
                'priority': priority,
                'organization_name': 'High Priority ONLUS'
            }
        ]
        self.mock_collection.find.return_value.sort.return_value = mock_applications

        applications = self.repository.get_applications_by_priority(priority)

        self.mock_collection.find.assert_called_once_with({'priority': priority})

    def test_get_expired_applications(self):
        """Test finding expired applications"""
        mock_applications = [
            {
                '_id': str(ObjectId()),
                'organization_name': 'Expired ONLUS',
                'submission_date': datetime.now(timezone.utc) - timedelta(days=120)
            }
        ]
        self.mock_collection.find.return_value = mock_applications

        applications = self.repository.get_expired_applications()

        # Verify query looks for old applications
        query_call = self.mock_collection.find.call_args[0][0]
        assert '$lt' in query_call['submission_date']

    def test_get_application_statistics(self):
        """Test getting application statistics"""
        mock_stats = [
            {
                '_id': {'status': ApplicationStatus.APPROVED.value},
                'count': 85
            },
            {
                '_id': {'status': ApplicationStatus.SUBMITTED.value},
                'count': 23
            },
            {
                '_id': {'status': ApplicationStatus.REJECTED.value},
                'count': 12
            }
        ]
        self.mock_collection.aggregate.return_value = mock_stats

        stats = self.repository.get_application_statistics()

        # Verify aggregation pipeline
        pipeline_call = self.mock_collection.aggregate.call_args[0][0]
        assert any('$group' in stage for stage in pipeline_call)
        assert stats['total_applications'] == 120
        assert stats['by_status'][ApplicationStatus.APPROVED.value] == 85

    def test_update_application_success(self):
        """Test successful application update"""
        application_id = str(ObjectId())
        mock_application = Mock()
        mock_application.to_dict.return_value = {
            '_id': application_id,
            'status': ApplicationStatus.APPROVED.value,
            'approval_date': datetime.now(timezone.utc)
        }

        self.mock_collection.update_one.return_value.modified_count = 1

        success = self.repository.update_application(application_id, mock_application)

        self.mock_collection.update_one.assert_called_once()
        assert success is True


class TestONLUSOrganizationRepository:
    """Tests for ONLUSOrganizationRepository"""

    def setup_method(self):
        """Setup test fixtures"""
        self.repository = ONLUSOrganizationRepository()
        self.mock_collection = Mock()
        self.repository.collection = self.mock_collection

    def test_find_by_tax_id_success(self):
        """Test finding organization by tax ID"""
        tax_id = '12345678901'
        mock_organization = {
            '_id': str(ObjectId()),
            'name': 'Tax ID Test ONLUS',
            'tax_id': tax_id,
            'status': OrganizationStatus.ACTIVE.value
        }
        self.mock_collection.find_one.return_value = mock_organization

        organization = self.repository.find_by_tax_id(tax_id)

        self.mock_collection.find_one.assert_called_once_with({'tax_id': tax_id})
        assert organization is not None
        assert organization.tax_id == tax_id

    def test_find_by_tax_id_not_found(self):
        """Test finding non-existent organization by tax ID"""
        self.mock_collection.find_one.return_value = None

        organization = self.repository.find_by_tax_id('nonexistent')

        assert organization is None

    def test_get_organizations_by_category(self):
        """Test getting organizations by category"""
        category = ONLUSCategory.HEALTHCARE.value
        mock_organizations = [
            {
                '_id': str(ObjectId()),
                'name': 'Healthcare ONLUS 1',
                'category': category,
                'status': OrganizationStatus.ACTIVE.value
            }
        ]
        self.mock_collection.find.return_value = mock_organizations

        organizations = self.repository.get_organizations_by_category(category)

        expected_query = {
            'category': category,
            'status': OrganizationStatus.ACTIVE.value
        }
        self.mock_collection.find.assert_called_once_with(expected_query)

    def test_get_featured_organizations(self):
        """Test getting featured organizations"""
        mock_organizations = [
            {
                '_id': str(ObjectId()),
                'name': 'Featured ONLUS',
                'featured': True,
                'featured_until': datetime.now(timezone.utc) + timedelta(days=10)
            }
        ]
        self.mock_collection.find.return_value = mock_organizations

        organizations = self.repository.get_featured_organizations()

        # Verify query for featured organizations
        query_call = self.mock_collection.find.call_args[0][0]
        assert query_call['featured'] is True
        assert '$gt' in query_call['featured_until']

    def test_search_organizations(self):
        """Test searching organizations with text query"""
        search_query = 'education children'
        category = ONLUSCategory.EDUCATION.value

        mock_organizations = [
            {
                '_id': str(ObjectId()),
                'name': 'Children Education ONLUS',
                'description': 'Helping children with education',
                'category': category
            }
        ]
        self.mock_collection.find.return_value = mock_organizations

        organizations = self.repository.search_organizations(search_query, category)

        # Verify text search query
        query_call = self.mock_collection.find.call_args[0][0]
        assert '$text' in query_call
        assert query_call['$text']['$search'] == search_query
        assert query_call['category'] == category

    def test_get_top_rated_organizations(self):
        """Test getting top-rated organizations"""
        limit = 5
        mock_organizations = [
            {
                '_id': str(ObjectId()),
                'name': 'Top Rated ONLUS',
                'compliance_score': 95,
                'total_donations_received': 10000.0
            }
        ]
        self.mock_collection.find.return_value.sort.return_value.limit.return_value = mock_organizations

        organizations = self.repository.get_top_rated_organizations(limit)

        # Verify sorting by compliance score descending
        sort_call = self.mock_collection.find.return_value.sort.call_args[0][0]
        assert sort_call == [('compliance_score', -1), ('total_donations_received', -1)]

    def test_get_recent_organizations(self):
        """Test getting recently verified organizations"""
        days = 30
        mock_organizations = [
            {
                '_id': str(ObjectId()),
                'name': 'Recent ONLUS',
                'verification_date': datetime.now(timezone.utc) - timedelta(days=10)
            }
        ]
        self.mock_collection.find.return_value.sort.return_value = mock_organizations

        organizations = self.repository.get_recent_organizations(days)

        # Verify query for recent verification
        query_call = self.mock_collection.find.call_args[0][0]
        assert '$gte' in query_call['verification_date']

    def test_get_organizations_for_compliance_review(self):
        """Test getting organizations needing compliance review"""
        mock_organizations = [
            {
                '_id': str(ObjectId()),
                'name': 'Review Needed ONLUS',
                'compliance_score': 60,  # Below threshold
                'last_compliance_review': datetime.now(timezone.utc) - timedelta(days=400)
            }
        ]
        self.mock_collection.find.return_value.sort.return_value = mock_organizations

        organizations = self.repository.get_organizations_for_compliance_review()

        # Verify query for compliance review criteria
        query_call = self.mock_collection.find.call_args[0][0]
        assert '$or' in query_call
        # Should include low compliance score OR old review date

    def test_get_organization_statistics(self):
        """Test getting comprehensive organization statistics"""
        mock_stats = [
            {
                '_id': {'status': OrganizationStatus.ACTIVE.value},
                'count': 150,
                'total_donations': 500000.0,
                'total_donors': 2500
            },
            {
                '_id': {'status': OrganizationStatus.SUSPENDED.value},
                'count': 5,
                'total_donations': 0.0,
                'total_donors': 0
            }
        ]
        self.mock_collection.aggregate.return_value = mock_stats

        stats = self.repository.get_organization_statistics()

        # Verify aggregation pipeline
        pipeline_call = self.mock_collection.aggregate.call_args[0][0]
        assert any('$group' in stage for stage in pipeline_call)
        assert stats['total_organizations'] == 155
        assert stats['by_status'][OrganizationStatus.ACTIVE.value]['count'] == 150

    def test_update_organization_success(self):
        """Test successful organization update"""
        organization_id = str(ObjectId())
        mock_organization = Mock()
        mock_organization.to_dict.return_value = {
            '_id': organization_id,
            'status': OrganizationStatus.ACTIVE.value,
            'updated_at': datetime.now(timezone.utc)
        }

        self.mock_collection.update_one.return_value.modified_count = 1

        success = self.repository.update_organization(organization_id, mock_organization)

        self.mock_collection.update_one.assert_called_once()
        assert success is True

    def test_update_organization_not_found(self):
        """Test organization update when organization not found"""
        organization_id = str(ObjectId())
        mock_organization = Mock()
        mock_organization.to_dict.return_value = {'_id': organization_id}

        self.mock_collection.update_one.return_value.modified_count = 0

        success = self.repository.update_organization(organization_id, mock_organization)

        assert success is False

    def test_delete_organization_success(self):
        """Test successful organization deletion"""
        organization_id = str(ObjectId())
        self.mock_collection.delete_one.return_value.deleted_count = 1

        success = self.repository.delete_organization(organization_id)

        self.mock_collection.delete_one.assert_called_once_with({'_id': ObjectId(organization_id)})
        assert success is True

    def test_create_indexes_in_testing_mode(self):
        """Test that create_indexes is skipped in testing mode"""
        import os
        with patch.dict(os.environ, {'TESTING': 'true'}):
            # Should not raise any errors and should skip index creation
            self.repository.create_indexes()
            # In testing mode, collection should be None or mocked
            # This test ensures the testing guard works correctly