"""
BaseOnlusTest - GOO-35 Testing Utilities
Specialized base class for ONLUS and campaign management testing
Provides domain-specific utilities for non-profit organizations
"""
import os
import sys
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any, Tuple
from unittest.mock import Mock, patch
from bson import ObjectId

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from tests.core.base_service_test import BaseServiceTest
from tests.utils.builders import BaseBuilder


class OnlusBuilder(BaseBuilder):
    """Builder for ONLUS test data"""

    def __init__(self):
        super().__init__()
        self._data = {
            '_id': str(self._generate_object_id()),
            'name': 'Test ONLUS',
            'description': 'A test non-profit organization',
            'tax_id': '12345678901',
            'email': 'contact@testonlus.org',
            'phone': '+39 123 456 7890',
            'website': 'https://testonlus.org',
            'address': {
                'street': 'Via Test 123',
                'city': 'Milano',
                'region': 'Lombardia',
                'postal_code': '20100',
                'country': 'IT'
            },
            'status': 'active',
            'verification_status': 'verified',
            'registration_date': datetime.now(timezone.utc) - timedelta(days=365),
            'created_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc),
            'total_received': Decimal('0.00'),
            'total_campaigns': 0,
            'active_campaigns': 0,
            'categories': ['education', 'health'],
            'logo_url': None,
            'documents': [],
            'bank_account': {
                'iban': 'IT60X0542811101000000123456',
                'bank_name': 'Test Bank',
                'verified': True
            },
            'contact_person': {
                'name': 'Mario Rossi',
                'role': 'President',
                'email': 'president@testonlus.org',
                'phone': '+39 123 456 7890'
            },
            'compliance': {
                'privacy_policy': True,
                'terms_accepted': True,
                'data_processing_consent': True,
                'last_compliance_check': datetime.now(timezone.utc)
            }
        }

    def with_name(self, name: str) -> 'OnlusBuilder':
        """Set ONLUS name"""
        self._data['name'] = name
        return self

    def with_status(self, status: str) -> 'OnlusBuilder':
        """Set ONLUS status (active, suspended, pending, inactive)"""
        self._data['status'] = status
        return self

    def with_verification(self, status: str) -> 'OnlusBuilder':
        """Set verification status (pending, verified, rejected)"""
        self._data['verification_status'] = status
        return self

    def with_categories(self, categories: List[str]) -> 'OnlusBuilder':
        """Set ONLUS categories"""
        self._data['categories'] = categories
        return self

    def with_total_received(self, amount: float) -> 'OnlusBuilder':
        """Set total amount received"""
        self._data['total_received'] = Decimal(str(amount))
        return self

    def with_bank_account(self, iban: str, bank_name: str = 'Test Bank') -> 'OnlusBuilder':
        """Set bank account information"""
        self._data['bank_account'] = {
            'iban': iban,
            'bank_name': bank_name,
            'verified': True
        }
        return self

    def as_pending_verification(self) -> 'OnlusBuilder':
        """Create ONLUS pending verification"""
        self._data.update({
            'status': 'pending',
            'verification_status': 'pending',
            'documents': ['certificate.pdf', 'statute.pdf']
        })
        return self

    def as_rejected(self, reason: str = 'Incomplete documentation') -> 'OnlusBuilder':
        """Create rejected ONLUS"""
        self._data.update({
            'status': 'inactive',
            'verification_status': 'rejected',
            'rejection_reason': reason,
            'rejected_at': datetime.now(timezone.utc)
        })
        return self


class CampaignBuilder(BaseBuilder):
    """Builder for Campaign test data"""

    def __init__(self):
        super().__init__()
        self._data = {
            '_id': str(self._generate_object_id()),
            'onlus_id': str(self._generate_object_id()),
            'title': 'Test Campaign',
            'description': 'A test fundraising campaign',
            'goal_amount': Decimal('1000.00'),
            'current_amount': Decimal('0.00'),
            'currency': 'EUR',
            'status': 'active',
            'category': 'education',
            'start_date': datetime.now(timezone.utc),
            'end_date': datetime.now(timezone.utc) + timedelta(days=30),
            'created_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc),
            'image_url': None,
            'story': 'This is the campaign story and why donations are needed.',
            'tags': ['education', 'children', 'school'],
            'location': {
                'city': 'Milano',
                'region': 'Lombardia',
                'country': 'IT'
            },
            'beneficiaries': {
                'count': 100,
                'description': '100 children will benefit from this campaign'
            },
            'progress': {
                'percentage': 0.0,
                'donors_count': 0,
                'last_donation_at': None
            },
            'featured': False,
            'urgent': False,
            'transparency': {
                'budget_breakdown': {
                    'materials': 60.0,
                    'logistics': 25.0,
                    'administration': 15.0
                },
                'reports_published': 0,
                'last_report_date': None
            }
        }

    def with_goal(self, amount: float) -> 'CampaignBuilder':
        """Set campaign goal amount"""
        self._data['goal_amount'] = Decimal(str(amount))
        return self

    def with_current_amount(self, amount: float) -> 'CampaignBuilder':
        """Set current raised amount"""
        self._data['current_amount'] = Decimal(str(amount))
        percentage = (float(amount) / float(self._data['goal_amount'])) * 100
        self._data['progress']['percentage'] = min(100.0, percentage)
        return self

    def with_category(self, category: str) -> 'CampaignBuilder':
        """Set campaign category"""
        self._data['category'] = category
        return self

    def with_duration(self, days: int) -> 'CampaignBuilder':
        """Set campaign duration"""
        self._data['end_date'] = self._data['start_date'] + timedelta(days=days)
        return self

    def as_featured(self) -> 'CampaignBuilder':
        """Mark campaign as featured"""
        self._data['featured'] = True
        return self

    def as_urgent(self) -> 'CampaignBuilder':
        """Mark campaign as urgent"""
        self._data['urgent'] = True
        return self

    def as_completed(self) -> 'CampaignBuilder':
        """Create completed campaign"""
        self._data.update({
            'status': 'completed',
            'current_amount': self._data['goal_amount'],
            'progress': {
                'percentage': 100.0,
                'donors_count': 50,
                'last_donation_at': datetime.now(timezone.utc) - timedelta(days=1)
            }
        })
        return self

    def as_expired(self) -> 'CampaignBuilder':
        """Create expired campaign"""
        self._data.update({
            'status': 'expired',
            'end_date': datetime.now(timezone.utc) - timedelta(days=1)
        })
        return self


class BaseOnlusTest(BaseServiceTest):
    """Base class for ONLUS and campaign testing with GOO-35 utilities"""

    def setUp(self):
        super().setUp()
        self._setup_onlus_mocks()

    def _setup_onlus_mocks(self):
        """Setup ONLUS-specific mocks and repositories"""
        # Mock ONLUS repository
        self.mock_onlus_repository = Mock()
        self.mock_onlus_repository.create_indexes = Mock()

        # Mock campaign repository
        self.mock_campaign_repository = Mock()
        self.mock_campaign_repository.create_indexes = Mock()

        # Mock verification services
        self.mock_document_verifier = Mock()
        self.mock_tax_id_validator = Mock()
        self.mock_bank_validator = Mock()

        # Mock notification services
        self.mock_email_service = Mock()
        self.mock_sms_service = Mock()

        # Register builders
        self._register_onlus_builders()

    def _register_onlus_builders(self):
        """Register ONLUS-specific builders"""
        try:
            if hasattr(self.smart_fixtures, 'register_builder'):
                self.smart_fixtures.register_builder('onlus', OnlusBuilder)
                self.smart_fixtures.register_builder('campaign', CampaignBuilder)
        except Exception:
            # Fallback to direct builder usage
            pass

    # ONLUS Creation Utilities
    def create_test_onlus(self, name: str = None, status: str = 'active', **kwargs) -> Dict[str, Any]:
        """Create test ONLUS data with realistic defaults"""
        builder = OnlusBuilder()

        if name:
            builder.with_name(name)

        if status != 'active':
            builder.with_status(status)

        # Apply additional customizations
        for key, value in kwargs.items():
            if hasattr(builder, f'with_{key}'):
                getattr(builder, f'with_{key}')(value)
            else:
                builder._data[key] = value

        return builder.build()

    def create_test_campaign(self, onlus_id: str = None, title: str = None,
                           goal: float = 1000.0, **kwargs) -> Dict[str, Any]:
        """Create test campaign data"""
        builder = CampaignBuilder()

        if onlus_id:
            builder._data['onlus_id'] = onlus_id

        if title:
            builder._data['title'] = title

        if goal != 1000.0:
            builder.with_goal(goal)

        # Apply additional customizations
        for key, value in kwargs.items():
            if hasattr(builder, f'with_{key}'):
                getattr(builder, f'with_{key}')(value)
            elif hasattr(builder, f'as_{key}'):
                getattr(builder, f'as_{key}')()
            else:
                builder._data[key] = value

        return builder.build()

    # ONLUS Scenarios
    def create_verification_scenario(self, verification_status: str = 'pending') -> Dict[str, Any]:
        """Create ONLUS verification scenario"""
        scenario = {
            'onlus': None,
            'documents': [],
            'verification_steps': [],
            'expected_outcome': verification_status
        }

        if verification_status == 'pending':
            scenario['onlus'] = self.create_test_onlus(status='pending', verification_status='pending')
            scenario['documents'] = ['certificate.pdf', 'statute.pdf', 'tax_document.pdf']
            scenario['verification_steps'] = ['document_check', 'tax_id_validation', 'bank_verification']
        elif verification_status == 'verified':
            scenario['onlus'] = self.create_test_onlus(status='active', verification_status='verified')
            scenario['verification_steps'] = ['completed']
        elif verification_status == 'rejected':
            scenario['onlus'] = self.create_test_onlus(status='inactive', verification_status='rejected')
            scenario['rejection_reason'] = 'Incomplete documentation'

        return scenario

    def create_multi_campaign_onlus(self, campaign_count: int = 3) -> Dict[str, Any]:
        """Create ONLUS with multiple campaigns"""
        onlus = self.create_test_onlus(
            name='Multi-Campaign ONLUS',
            total_campaigns=campaign_count
        )

        campaigns = []
        total_goal = Decimal('0.00')
        total_raised = Decimal('0.00')

        categories = ['education', 'health', 'environment', 'social']

        for i in range(campaign_count):
            goal_amount = 500.0 + (i * 200)  # Varying goal amounts
            current_amount = goal_amount * 0.3  # 30% funded

            campaign = self.create_test_campaign(
                onlus_id=onlus['_id'],
                title=f'Campaign {i+1}',
                goal=goal_amount,
                current_amount=current_amount,
                category=categories[i % len(categories)]
            )

            campaigns.append(campaign)
            total_goal += campaign['goal_amount']
            total_raised += campaign['current_amount']

        return {
            'onlus': onlus,
            'campaigns': campaigns,
            'total_goal': total_goal,
            'total_raised': total_raised,
            'active_campaigns': len([c for c in campaigns if c['status'] == 'active'])
        }

    # Campaign Scenarios
    def create_campaign_lifecycle_scenario(self) -> Dict[str, Any]:
        """Create complete campaign lifecycle scenario"""
        onlus = self.create_test_onlus()

        scenarios = {
            'draft': self.create_test_campaign(onlus_id=onlus['_id'], status='draft'),
            'active': self.create_test_campaign(onlus_id=onlus['_id'], status='active'),
            'funded': self.create_test_campaign(onlus_id=onlus['_id'], status='completed',
                                              current_amount=1000.0),
            'expired': self.create_test_campaign(onlus_id=onlus['_id'], status='expired'),
            'cancelled': self.create_test_campaign(onlus_id=onlus['_id'], status='cancelled')
        }

        return {
            'onlus': onlus,
            'campaigns': scenarios,
            'lifecycle_stages': ['draft', 'active', 'funded', 'expired', 'cancelled']
        }

    # Verification and Compliance Mocking
    def mock_document_verification_success(self, onlus_id: str, documents: List[str]):
        """Mock successful document verification"""
        verification_result = {
            'onlus_id': onlus_id,
            'documents_verified': documents,
            'verification_date': datetime.now(timezone.utc),
            'status': 'verified',
            'notes': 'All documents verified successfully'
        }

        self.mock_document_verifier.verify_documents.return_value = (
            True, 'Documents verified', verification_result
        )

        return verification_result

    def mock_document_verification_failure(self, onlus_id: str, failed_documents: List[str]):
        """Mock failed document verification"""
        verification_result = {
            'onlus_id': onlus_id,
            'failed_documents': failed_documents,
            'verification_date': datetime.now(timezone.utc),
            'status': 'rejected',
            'errors': ['Invalid certificate format', 'Missing required signatures']
        }

        self.mock_document_verifier.verify_documents.return_value = (
            False, 'Document verification failed', verification_result
        )

        return verification_result

    def mock_tax_id_validation(self, tax_id: str, valid: bool = True):
        """Mock tax ID validation"""
        if valid:
            result = {
                'tax_id': tax_id,
                'valid': True,
                'organization_name': 'Test ONLUS',
                'registration_status': 'active'
            }
            self.mock_tax_id_validator.validate.return_value = (True, 'Valid tax ID', result)
        else:
            result = {
                'tax_id': tax_id,
                'valid': False,
                'error': 'Invalid tax ID format'
            }
            self.mock_tax_id_validator.validate.return_value = (False, 'Invalid tax ID', result)

        return result

    def mock_bank_account_validation(self, iban: str, valid: bool = True):
        """Mock bank account validation"""
        if valid:
            result = {
                'iban': iban,
                'valid': True,
                'bank_name': 'Test Bank',
                'account_holder': 'Test ONLUS',
                'verified': True
            }
            self.mock_bank_validator.validate.return_value = (True, 'Valid bank account', result)
        else:
            result = {
                'iban': iban,
                'valid': False,
                'error': 'Invalid IBAN format'
            }
            self.mock_bank_validator.validate.return_value = (False, 'Invalid IBAN', result)

        return result

    # Donation Flow Mocking
    def mock_campaign_donation(self, campaign_id: str, amount: float, donor_id: str = None):
        """Mock donation to campaign"""
        donation_data = {
            'campaign_id': campaign_id,
            'donor_id': donor_id or str(ObjectId()),
            'amount': Decimal(str(amount)),
            'currency': 'EUR',
            'timestamp': datetime.now(timezone.utc),
            'anonymous': False
        }

        # Update campaign progress
        self.mock_campaign_repository.update_progress.return_value = True

        return donation_data

    def mock_campaign_completion(self, campaign_id: str, final_amount: float):
        """Mock campaign reaching its goal"""
        completion_data = {
            'campaign_id': campaign_id,
            'final_amount': Decimal(str(final_amount)),
            'completed_at': datetime.now(timezone.utc),
            'donors_count': 50,
            'status': 'completed'
        }

        # Mock notification sending
        self.mock_email_service.send_completion_notification.return_value = True

        return completion_data

    # Notification Mocking
    def mock_verification_notifications(self, onlus_id: str, status: str):
        """Mock verification status notifications"""
        if status == 'verified':
            notification_data = {
                'onlus_id': onlus_id,
                'type': 'verification_approved',
                'message': 'Your ONLUS has been verified and approved',
                'sent_at': datetime.now(timezone.utc)
            }
            self.mock_email_service.send_verification_approved.return_value = True
        else:
            notification_data = {
                'onlus_id': onlus_id,
                'type': 'verification_rejected',
                'message': 'Your ONLUS verification has been rejected',
                'reason': 'Incomplete documentation',
                'sent_at': datetime.now(timezone.utc)
            }
            self.mock_email_service.send_verification_rejected.return_value = True

        return notification_data

    # Search and Discovery
    def create_onlus_discovery_scenario(self, count: int = 10) -> Dict[str, Any]:
        """Create ONLUS discovery and search scenario"""
        scenario = {
            'onlus_list': [],
            'categories': {},
            'locations': {},
            'featured': []
        }

        categories = ['education', 'health', 'environment', 'social', 'animals']
        locations = ['Milano', 'Roma', 'Napoli', 'Torino', 'Bologna']

        for i in range(count):
            category = categories[i % len(categories)]
            location = locations[i % len(locations)]

            onlus = self.create_test_onlus(
                name=f'ONLUS {i+1}',
                categories=[category],
                total_received=float(100 + i * 50)
            )

            onlus['location'] = {'city': location, 'region': 'Test Region'}

            scenario['onlus_list'].append(onlus)

            # Group by category
            if category not in scenario['categories']:
                scenario['categories'][category] = []
            scenario['categories'][category].append(onlus)

            # Group by location
            if location not in scenario['locations']:
                scenario['locations'][location] = []
            scenario['locations'][location].append(onlus)

            # Featured ONLUS (every 3rd)
            if i % 3 == 0:
                scenario['featured'].append(onlus)

        return scenario

    # Assertion Utilities
    def assert_onlus_valid(self, onlus_data: Dict[str, Any], expected_status: str = None):
        """Assert ONLUS has valid structure"""
        required_fields = ['_id', 'name', 'tax_id', 'email', 'status', 'verification_status']
        for field in required_fields:
            assert field in onlus_data, f"Missing required field: {field}"

        # Validate status values
        valid_statuses = ['active', 'pending', 'suspended', 'inactive']
        assert onlus_data['status'] in valid_statuses

        valid_verification_statuses = ['pending', 'verified', 'rejected']
        assert onlus_data['verification_status'] in valid_verification_statuses

        if expected_status:
            assert onlus_data['status'] == expected_status

        # Validate contact information
        assert onlus_data['email']
        assert '@' in onlus_data['email']

        # Validate tax ID format (Italian)
        assert len(onlus_data['tax_id']) == 11  # Italian tax ID length

    def assert_campaign_valid(self, campaign_data: Dict[str, Any],
                            expected_status: str = None, min_goal: float = None):
        """Assert campaign has valid structure"""
        required_fields = ['_id', 'onlus_id', 'title', 'goal_amount', 'current_amount', 'status']
        for field in required_fields:
            assert field in campaign_data, f"Missing required field: {field}"

        # Validate amounts
        assert isinstance(campaign_data['goal_amount'], (Decimal, float, int))
        assert campaign_data['goal_amount'] > 0

        assert isinstance(campaign_data['current_amount'], (Decimal, float, int))
        assert campaign_data['current_amount'] >= 0
        assert campaign_data['current_amount'] <= campaign_data['goal_amount']

        # Validate status
        valid_statuses = ['draft', 'active', 'completed', 'expired', 'cancelled']
        assert campaign_data['status'] in valid_statuses

        # Validate dates
        if 'start_date' in campaign_data and 'end_date' in campaign_data:
            assert campaign_data['start_date'] <= campaign_data['end_date']

        if expected_status:
            assert campaign_data['status'] == expected_status

        if min_goal:
            assert float(campaign_data['goal_amount']) >= min_goal

    def assert_verification_complete(self, verification_result: Dict[str, Any]):
        """Assert verification process completion"""
        assert 'status' in verification_result
        assert verification_result['status'] in ['verified', 'rejected']

        if verification_result['status'] == 'verified':
            assert 'verification_date' in verification_result
            assert 'documents_verified' in verification_result
        else:
            assert 'rejection_reason' in verification_result
            assert 'errors' in verification_result

    def assert_donation_processed(self, donation_result: Dict[str, Any]):
        """Assert donation was properly processed"""
        assert 'campaign_id' in donation_result
        assert 'amount' in donation_result
        assert 'timestamp' in donation_result

        # Verify amount is positive
        assert float(donation_result['amount']) > 0

        # Verify campaign was updated
        assert 'campaign_updated' in donation_result or donation_result.get('success', False)


# Compliance and Regulatory Testing
class OnlusComplianceMixin:
    """Mixin for ONLUS compliance testing utilities"""

    def create_gdpr_compliance_scenario(self) -> Dict[str, Any]:
        """Create GDPR compliance testing scenario"""
        scenario = {
            'onlus': self.create_test_onlus(),
            'data_subjects': [],
            'processing_activities': [],
            'consent_records': []
        }

        # Create data subjects (donors)
        for i in range(5):
            data_subject = {
                'id': str(ObjectId()),
                'email': f'donor{i}@example.com',
                'consent_given': True,
                'consent_date': datetime.now(timezone.utc),
                'data_categories': ['contact', 'donation_history'],
                'retention_period': 'indefinite'
            }
            scenario['data_subjects'].append(data_subject)

        return scenario

    def validate_tax_reporting_compliance(self, onlus_data: Dict[str, Any],
                                        donations: List[Dict[str, Any]]):
        """Validate tax reporting compliance"""
        # Italian ONLUS tax reporting requirements
        total_donations = sum(float(d['amount']) for d in donations)

        compliance_check = {
            'total_donations': Decimal(str(total_donations)),
            'requires_detailed_reporting': total_donations > 10000,  # €10,000 threshold
            'donation_receipts_issued': len(donations),
            'tax_year': datetime.now().year,
            'compliance_status': 'compliant' if total_donations < 50000 else 'requires_audit'
        }

        return compliance_check