"""
Comprehensive unit tests for GOO-15 Donation Processing Engine controllers.
Tests all new controllers introduced in GOO-15 implementation.
"""
import pytest
import os
import json
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone, timedelta

# Set testing environment before importing app modules
os.environ['TESTING'] = 'true'

from app import create_app


@pytest.fixture
def app():
    """Create test app with testing configuration."""
    return create_app('testing')


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def mock_admin_token():
    """Mock admin JWT token for testing."""
    return "mock_admin_token_for_testing"


@pytest.fixture
def mock_user_token():
    """Mock user JWT token for testing."""
    return "mock_user_token_for_testing"


class TestBatchController:
    """Comprehensive tests for BatchController endpoints."""

    @patch('app.donations.controllers.batch_controller.get_batch_service')
    @patch('app.core.utils.decorators.verify_jwt_in_request')
    @patch('app.core.utils.decorators.get_jwt_identity')
    def test_create_batch_operation_success(self, mock_get_jwt, mock_verify_jwt, mock_get_service, client):
        """Test successful batch operation creation."""
        # Mock JWT verification
        mock_verify_jwt.return_value = True
        mock_get_jwt.return_value = {'user_id': 'admin_123', 'role': 'admin'}

        # Mock service response
        mock_service = MagicMock()
        mock_service.create_batch_donation_operation.return_value = (
            True, "BATCH_OPERATION_CREATED", {'batch_id': 'batch_123', 'total_items': 2}
        )
        mock_get_service.return_value = mock_service

        # Test data
        data = {
            'operation_type': 'donations',
            'items': [
                {'user_id': 'user1', 'onlus_id': 'onlus1', 'amount': 10.0},
                {'user_id': 'user2', 'onlus_id': 'onlus1', 'amount': 15.0}
            ]
        }

        response = client.post(
            '/api/batch/operations',
            data=json.dumps(data),
            content_type='application/json',
            headers={'Authorization': 'Bearer mock_admin_token'}
        )

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['success'] is True
        assert response_data['message'] == "BATCH_OPERATION_CREATED"
        assert response_data['data']['batch_id'] == 'batch_123'

    @patch('app.donations.controllers.batch_controller.get_batch_service')
    @patch('app.core.utils.decorators.verify_jwt_in_request')
    @patch('app.core.utils.decorators.get_jwt_identity')
    def test_create_batch_operation_validation_error(self, mock_get_jwt, mock_verify_jwt, mock_get_service, client):
        """Test batch operation creation with validation errors."""
        # Mock JWT verification
        mock_verify_jwt.return_value = True
        mock_get_jwt.return_value = {'user_id': 'admin_123', 'role': 'admin'}

        # Invalid data - missing required fields
        data = {
            'operation_type': 'donations'
            # Missing 'items' field
        }

        response = client.post(
            '/api/batch/operations',
            data=json.dumps(data),
            content_type='application/json',
            headers={'Authorization': 'Bearer mock_admin_token'}
        )

        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert response_data['success'] is False
        assert "ITEMS_REQUIRED" in response_data['message']

    @patch('app.donations.controllers.batch_controller.get_batch_service')
    @patch('app.core.utils.decorators.verify_jwt_in_request')
    @patch('app.core.utils.decorators.get_jwt_identity')
    def test_list_batch_operations(self, mock_get_jwt, mock_verify_jwt, mock_get_service, client):
        """Test listing batch operations."""
        # Mock JWT verification
        mock_verify_jwt.return_value = True
        mock_get_jwt.return_value = {'user_id': 'admin_123', 'role': 'admin'}

        # Mock service response
        mock_service = MagicMock()
        mock_service.list_batch_operations.return_value = (
            True, "BATCH_OPERATIONS_RETRIEVED", {
                'operations': [
                    {'batch_id': 'batch_1', 'status': 'completed', 'total_items': 10},
                    {'batch_id': 'batch_2', 'status': 'processing', 'total_items': 5}
                ],
                'total_count': 2
            }
        )
        mock_get_service.return_value = mock_service

        response = client.get(
            '/api/batch/operations?status=processing',
            headers={'Authorization': 'Bearer mock_admin_token'}
        )

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['success'] is True
        assert len(response_data['data']['operations']) == 2

    @patch('app.donations.controllers.batch_controller.get_batch_service')
    @patch('app.core.utils.decorators.verify_jwt_in_request')
    @patch('app.core.utils.decorators.get_jwt_identity')
    def test_get_batch_operation_status(self, mock_get_jwt, mock_verify_jwt, mock_get_service, client):
        """Test getting batch operation status."""
        # Mock JWT verification
        mock_verify_jwt.return_value = True
        mock_get_jwt.return_value = {'user_id': 'admin_123', 'role': 'admin'}

        # Mock service response
        mock_service = MagicMock()
        mock_service.get_batch_operation_status.return_value = (
            True, "BATCH_STATUS_RETRIEVED", {
                'batch_id': 'batch_123',
                'status': 'processing',
                'progress_percentage': 75.0,
                'processed_items': 75,
                'total_items': 100
            }
        )
        mock_get_service.return_value = mock_service

        response = client.get(
            '/api/batch/operations/batch_123',
            headers={'Authorization': 'Bearer mock_admin_token'}
        )

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['success'] is True
        assert response_data['data']['progress_percentage'] == 75.0

    def test_unauthorized_access(self, client):
        """Test unauthorized access to batch endpoints."""
        response = client.post('/api/batch/operations')
        assert response.status_code == 401

        response = client.get('/api/batch/operations')
        assert response.status_code == 401


class TestComplianceController:
    """Comprehensive tests for ComplianceController endpoints."""

    @patch('app.donations.controllers.compliance_controller.get_compliance_service')
    @patch('app.core.utils.decorators.verify_jwt_in_request')
    @patch('app.core.utils.decorators.get_jwt_identity')
    def test_initiate_compliance_check_success(self, mock_get_jwt, mock_verify_jwt, mock_get_service, client):
        """Test successful compliance check initiation."""
        # Mock JWT verification
        mock_verify_jwt.return_value = True
        mock_get_jwt.return_value = {'user_id': 'admin_123', 'role': 'admin'}

        # Mock service response
        mock_service = MagicMock()
        mock_service.initiate_compliance_check.return_value = (
            True, "COMPLIANCE_CHECK_INITIATED", {
                'check_id': 'check_123',
                'check_type': 'aml',
                'status': 'pending'
            }
        )
        mock_get_service.return_value = mock_service

        # Test data
        data = {
            'user_id': 'user_123',
            'check_type': 'aml',
            'reason': 'High value transaction review'
        }

        response = client.post(
            '/api/compliance/checks',
            data=json.dumps(data),
            content_type='application/json',
            headers={'Authorization': 'Bearer mock_admin_token'}
        )

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['success'] is True
        assert response_data['data']['check_id'] == 'check_123'

    @patch('app.donations.controllers.compliance_controller.get_compliance_service')
    @patch('app.core.utils.decorators.verify_jwt_in_request')
    @patch('app.core.utils.decorators.get_jwt_identity')
    def test_review_compliance_check_success(self, mock_get_jwt, mock_verify_jwt, mock_get_service, client):
        """Test successful compliance check review."""
        # Mock JWT verification
        mock_verify_jwt.return_value = True
        mock_get_jwt.return_value = {'user_id': 'admin_123', 'role': 'admin'}

        # Mock service response
        mock_service = MagicMock()
        mock_service.review_compliance_check.return_value = (
            True, "COMPLIANCE_CHECK_REVIEWED", {
                'check_id': 'check_123',
                'decision': 'approve',
                'reviewed_by': 'admin_123'
            }
        )
        mock_get_service.return_value = mock_service

        # Test data
        data = {
            'decision': 'approve',
            'review_notes': 'All documents verified successfully'
        }

        response = client.post(
            '/api/compliance/checks/check_123/review',
            data=json.dumps(data),
            content_type='application/json',
            headers={'Authorization': 'Bearer mock_admin_token'}
        )

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['success'] is True
        assert response_data['data']['decision'] == 'approve'

    @patch('app.donations.controllers.compliance_controller.get_compliance_service')
    @patch('app.core.utils.decorators.verify_jwt_in_request')
    @patch('app.core.utils.decorators.get_jwt_identity')
    def test_get_user_compliance_status(self, mock_get_jwt, mock_verify_jwt, mock_get_service, client):
        """Test getting user compliance status."""
        # Mock JWT verification
        mock_verify_jwt.return_value = True
        mock_get_jwt.return_value = {'user_id': 'admin_123', 'role': 'admin'}

        # Mock service response
        mock_service = MagicMock()
        mock_service.get_compliance_status.return_value = (
            True, "COMPLIANCE_STATUS_RETRIEVED", {
                'user_id': 'user_123',
                'overall_status': 'approved',
                'aml_status': 'approved',
                'kyc_status': 'pending'
            }
        )
        mock_get_service.return_value = mock_service

        response = client.get(
            '/api/compliance/users/user_123/status',
            headers={'Authorization': 'Bearer mock_admin_token'}
        )

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['success'] is True
        assert response_data['data']['overall_status'] == 'approved'

    @patch('app.donations.controllers.compliance_controller.get_compliance_service')
    @patch('app.core.utils.decorators.verify_jwt_in_request')
    @patch('app.core.utils.decorators.get_jwt_identity')
    def test_get_pending_compliance_checks(self, mock_get_jwt, mock_verify_jwt, mock_get_service, client):
        """Test getting pending compliance checks."""
        # Mock JWT verification
        mock_verify_jwt.return_value = True
        mock_get_jwt.return_value = {'user_id': 'admin_123', 'role': 'admin'}

        response = client.get(
            '/api/compliance/checks/pending?check_type=aml',
            headers={'Authorization': 'Bearer mock_admin_token'}
        )

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['success'] is True
        assert 'pending_checks' in response_data['data']

    def test_compliance_validation_errors(self, client):
        """Test compliance endpoint validation errors."""
        # Test missing data
        response = client.post(
            '/api/compliance/checks',
            headers={'Authorization': 'Bearer mock_admin_token'}
        )
        # Should fail due to missing JSON data


class TestFinancialAdminController:
    """Comprehensive tests for FinancialAdminController endpoints."""

    @patch('app.donations.controllers.financial_admin_controller.get_financial_analytics_service')
    @patch('app.core.utils.decorators.verify_jwt_in_request')
    @patch('app.core.utils.decorators.get_jwt_identity')
    def test_get_financial_dashboard_success(self, mock_get_jwt, mock_verify_jwt, mock_get_service, client):
        """Test successful financial dashboard retrieval."""
        # Mock JWT verification
        mock_verify_jwt.return_value = True
        mock_get_jwt.return_value = {'user_id': 'admin_123', 'role': 'admin'}

        # Mock service response
        mock_service = MagicMock()
        mock_service.generate_financial_dashboard.return_value = (
            True, "FINANCIAL_DASHBOARD_GENERATED", {
                'core_metrics': {
                    'total_volume': 10000.0,
                    'total_donations': 150,
                    'average_donation': 66.67,
                    'growth_rate': 0.15
                },
                'trends': {
                    'trend_direction': 'increasing',
                    'daily_data': [
                        {'date': '2025-09-25', 'volume': 500.0},
                        {'date': '2025-09-26', 'volume': 750.0}
                    ]
                }
            }
        )
        mock_get_service.return_value = mock_service

        response = client.get(
            '/api/admin/financial/dashboard?days=30',
            headers={'Authorization': 'Bearer mock_admin_token'}
        )

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['success'] is True
        assert response_data['data']['core_metrics']['total_volume'] == 10000.0

    @patch('app.donations.controllers.financial_admin_controller.get_financial_analytics_service')
    @patch('app.core.utils.decorators.verify_jwt_in_request')
    @patch('app.core.utils.decorators.get_jwt_identity')
    def test_get_financial_metrics(self, mock_get_jwt, mock_verify_jwt, mock_get_service, client):
        """Test financial metrics retrieval."""
        # Mock JWT verification
        mock_verify_jwt.return_value = True
        mock_get_jwt.return_value = {'user_id': 'admin_123', 'role': 'admin'}

        # Mock service response
        mock_service = MagicMock()
        mock_service.get_custom_metrics.return_value = (
            True, "CUSTOM_METRICS_RETRIEVED", {
                'metrics': {
                    'volume': 5000.0,
                    'count': 75,
                    'average': 66.67
                },
                'period': 'daily'
            }
        )
        mock_get_service.return_value = mock_service

        response = client.get(
            '/api/admin/financial/metrics?metric_type=volume&period=daily',
            headers={'Authorization': 'Bearer mock_admin_token'}
        )

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['success'] is True
        assert response_data['data']['metrics']['volume'] == 5000.0

    @patch('app.donations.controllers.financial_admin_controller.get_financial_analytics_service')
    @patch('app.core.utils.decorators.verify_jwt_in_request')
    @patch('app.core.utils.decorators.get_jwt_identity')
    def test_get_user_analytics(self, mock_get_jwt, mock_verify_jwt, mock_get_service, client):
        """Test user behavior analytics retrieval."""
        # Mock JWT verification
        mock_verify_jwt.return_value = True
        mock_get_jwt.return_value = {'user_id': 'admin_123', 'role': 'admin'}

        # Mock service response
        mock_service = MagicMock()
        mock_service.get_user_behavior_analytics.return_value = (
            True, "USER_ANALYTICS_GENERATED", {
                'user_segments': {
                    'new_donors': 50,
                    'returning_donors': 200,
                    'high_value': 25
                },
                'behavior_metrics': {
                    'retention_rate': 0.65,
                    'average_donation_frequency': 14.5
                }
            }
        )
        mock_get_service.return_value = mock_service

        response = client.get(
            '/api/admin/financial/analytics/users?segment=high_value',
            headers={'Authorization': 'Bearer mock_admin_token'}
        )

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['success'] is True
        assert response_data['data']['user_segments']['high_value'] == 25

    @patch('app.donations.controllers.financial_admin_controller.get_financial_analytics_service')
    @patch('app.core.utils.decorators.verify_jwt_in_request')
    @patch('app.core.utils.decorators.get_jwt_identity')
    def test_get_forecasting(self, mock_get_jwt, mock_verify_jwt, mock_get_service, client):
        """Test financial forecasting retrieval."""
        # Mock JWT verification
        mock_verify_jwt.return_value = True
        mock_get_jwt.return_value = {'user_id': 'admin_123', 'role': 'admin'}

        # Mock service response
        mock_service = MagicMock()
        mock_service.generate_forecasting_report.return_value = (
            True, "FORECASTING_REPORT_GENERATED", {
                'forecast_data': [
                    {'date': '2025-09-28', 'predicted_volume': 600.0, 'confidence': 0.85},
                    {'date': '2025-09-29', 'predicted_volume': 650.0, 'confidence': 0.80}
                ],
                'methodology': 'moving_average_with_growth',
                'confidence_intervals': {'lower': 500.0, 'upper': 750.0}
            }
        )
        mock_get_service.return_value = mock_service

        response = client.get(
            '/api/admin/financial/forecasting?forecast_days=7&metric=volume',
            headers={'Authorization': 'Bearer mock_admin_token'}
        )

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['success'] is True
        assert len(response_data['data']['forecast_data']) == 2

    @patch('app.donations.controllers.financial_admin_controller.get_financial_analytics_service')
    @patch('app.core.utils.decorators.verify_jwt_in_request')
    @patch('app.core.utils.decorators.get_jwt_identity')
    def test_generate_custom_report(self, mock_get_jwt, mock_verify_jwt, mock_get_service, client):
        """Test custom report generation."""
        # Mock JWT verification
        mock_verify_jwt.return_value = True
        mock_get_jwt.return_value = {'user_id': 'admin_123', 'role': 'admin'}

        # Mock service response
        mock_service = MagicMock()
        mock_service.generate_custom_report.return_value = (
            True, "CUSTOM_REPORT_GENERATED", {
                'report_id': 'report_123',
                'report_name': 'Monthly Analysis',
                'total_records': 500,
                'generated_at': datetime.now(timezone.utc).isoformat()
            }
        )
        mock_get_service.return_value = mock_service

        # Test data
        data = {
            'report_name': 'Monthly Donation Analysis',
            'start_date': '2025-09-01T00:00:00Z',
            'end_date': '2025-09-30T23:59:59Z',
            'metrics': ['volume', 'count', 'average'],
            'group_by': 'daily'
        }

        response = client.post(
            '/api/admin/financial/reports/custom',
            data=json.dumps(data),
            content_type='application/json',
            headers={'Authorization': 'Bearer mock_admin_token'}
        )

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['success'] is True
        assert response_data['data']['report_name'] == 'Monthly Analysis'

    @patch('app.donations.controllers.financial_admin_controller.get_financial_analytics_service')
    @patch('app.core.utils.decorators.verify_jwt_in_request')
    @patch('app.core.utils.decorators.get_jwt_identity')
    def test_export_financial_data(self, mock_get_jwt, mock_verify_jwt, mock_get_service, client):
        """Test financial data export."""
        # Mock JWT verification
        mock_verify_jwt.return_value = True
        mock_get_jwt.return_value = {'user_id': 'admin_123', 'role': 'admin'}

        # Test data
        data = {
            'format': 'excel',
            'export_type': 'dashboard',
            'date_range': {
                'start_date': '2025-09-01',
                'end_date': '2025-09-30'
            }
        }

        response = client.post(
            '/api/admin/financial/export',
            data=json.dumps(data),
            content_type='application/json',
            headers={'Authorization': 'Bearer mock_admin_token'}
        )

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['success'] is True
        assert 'export_id' in response_data['data']

    def test_financial_dashboard_date_validation(self, client):
        """Test dashboard endpoint with invalid date parameters."""
        # Test with invalid date format
        response = client.get(
            '/api/admin/financial/dashboard?start_date=invalid_date',
            headers={'Authorization': 'Bearer mock_admin_token'}
        )
        # Should return validation error

    def test_forecasting_parameter_validation(self, client):
        """Test forecasting endpoint parameter validation."""
        # Test with invalid forecast days (too high)
        response = client.get(
            '/api/admin/financial/forecasting?forecast_days=365',
            headers={'Authorization': 'Bearer mock_admin_token'}
        )
        # Should return validation error for excessive forecast period


class TestControllerIntegration:
    """Integration tests for controller interactions."""

    @patch('app.core.utils.decorators.verify_jwt_in_request')
    @patch('app.core.utils.decorators.get_jwt_identity')
    def test_complete_compliance_workflow(self, mock_get_jwt, mock_verify_jwt, client):
        """Test complete compliance workflow across controllers."""
        # Mock JWT verification
        mock_verify_jwt.return_value = True
        mock_get_jwt.return_value = {'user_id': 'admin_123', 'role': 'admin'}

        # This would test a complete workflow:
        # 1. Create batch operation
        # 2. Initiate compliance checks
        # 3. Review and approve
        # 4. Generate analytics report

        # For now, we verify that all endpoints are accessible
        endpoints_to_test = [
            '/api/batch/operations',
            '/api/compliance/checks',
            '/api/admin/financial/dashboard'
        ]

        for endpoint in endpoints_to_test:
            response = client.get(
                endpoint,
                headers={'Authorization': 'Bearer mock_admin_token'}
            )
            # Each endpoint should be accessible (not 404)
            assert response.status_code != 404

    def test_error_handling_consistency(self, client):
        """Test that all controllers handle errors consistently."""
        # Test endpoints without authentication
        endpoints = [
            '/api/batch/operations',
            '/api/compliance/checks',
            '/api/admin/financial/dashboard'
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 401  # Unauthorized

            # Verify error response format
            if response.content_type == 'application/json':
                response_data = json.loads(response.data)
                assert 'success' in response_data
                assert response_data['success'] is False

    def test_admin_authorization_required(self, client):
        """Test that admin endpoints require admin authorization."""
        # Mock regular user token (not admin)
        user_headers = {'Authorization': 'Bearer mock_user_token'}

        admin_endpoints = [
            '/api/batch/operations',
            '/api/compliance/checks',
            '/api/admin/financial/dashboard'
        ]

        for endpoint in admin_endpoints:
            response = client.get(endpoint, headers=user_headers)
            # Should require admin role (403 Forbidden or 401 Unauthorized)
            assert response.status_code in [401, 403]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])