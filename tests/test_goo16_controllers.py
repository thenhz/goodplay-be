"""
Tests for GOO-16 Impact Tracking Controllers

Tests all controller endpoints with mocked services,
focusing on API contract compliance and constant message usage.
"""

import pytest
import json
from datetime import datetime, timezone
from unittest.mock import Mock, patch
from bson import ObjectId

# Import Flask testing utilities
from flask import current_app

# Import controller blueprint
from app.donations.controllers.impact_controller import impact_bp

# Test data constants
SAMPLE_USER_ID = str(ObjectId())
SAMPLE_ONLUS_ID = str(ObjectId())
SAMPLE_DONATION_ID = str(ObjectId())
SAMPLE_STORY_ID = str(ObjectId())


class TestImpactController:
    """Tests for Impact Controller endpoints"""

    @pytest.fixture
    def mock_services(self):
        """Mock all services used by the controller"""
        return {
            'impact_tracking': Mock(),
            'story_unlocking': Mock(),
            'impact_visualization': Mock(),
            'community_impact': Mock()
        }

    @pytest.fixture
    def mock_current_user(self):
        """Mock current user for authentication"""
        user = Mock()
        user.get_id.return_value = SAMPLE_USER_ID
        user.is_admin.return_value = False
        return user

    @pytest.fixture
    def admin_user(self):
        """Mock admin user"""
        user = Mock()
        user.get_id.return_value = str(ObjectId())
        user.is_admin.return_value = True
        return user

    def test_get_user_impact_success(self, client, mock_services, mock_current_user):
        """Test successful user impact summary retrieval"""
        # Mock service response
        mock_impact_data = {
            'user_id': SAMPLE_USER_ID,
            'statistics': {
                'total_donated': 350.0,
                'donation_count': 7,
                'impact_score': 185.0
            },
            'milestones': [
                {'level': 1, 'reached': True, 'amount': 10.0},
                {'level': 2, 'reached': True, 'amount': 25.0}
            ],
            'unlocked_stories': [
                {'id': str(ObjectId()), 'title': 'First Impact'}
            ]
        }

        mock_services['impact_tracking'].get_user_impact_summary.return_value = (
            True, "USER_IMPACT_SUMMARY_SUCCESS", mock_impact_data
        )

        with patch('app.donations.controllers.impact_controller.get_impact_service',
                   return_value=mock_services['impact_tracking']):
            with patch('app.donations.controllers.impact_controller.auth_required') as mock_auth:
                mock_auth.return_value = lambda f: lambda: f(mock_current_user)

                response = client.get(f'/api/impact/user/{SAMPLE_USER_ID}')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['message'] == "USER_IMPACT_SUMMARY_SUCCESS"
        assert data['data']['user_id'] == SAMPLE_USER_ID
        assert data['data']['statistics']['total_donated'] == 350.0

    def test_get_user_impact_unauthorized(self, client, mock_current_user):
        """Test user impact access with wrong user ID"""
        different_user_id = str(ObjectId())

        with patch('app.donations.controllers.impact_controller.auth_required') as mock_auth:
            mock_auth.return_value = lambda f: lambda: f(mock_current_user)

            response = client.get(f'/api/impact/user/{different_user_id}')

        assert response.status_code == 403
        data = json.loads(response.data)
        assert data['success'] is False
        assert data['message'] == "ACCESS_DENIED"

    def test_get_user_impact_timeline_success(self, client, mock_services, mock_current_user):
        """Test successful user impact timeline retrieval"""
        mock_timeline_data = {
            'user_id': SAMPLE_USER_ID,
            'period_days': 30,
            'timeline': [
                {
                    'date': datetime.now(timezone.utc).isoformat(),
                    'event_type': 'donation',
                    'amount': 50.0,
                    'impact_description': 'Helped 2 children'
                }
            ]
        }

        mock_services['impact_tracking'].get_user_impact_timeline.return_value = (
            True, "USER_TIMELINE_SUCCESS", mock_timeline_data
        )

        with patch('app.donations.controllers.impact_controller.get_impact_service',
                   return_value=mock_services['impact_tracking']):
            with patch('app.donations.controllers.impact_controller.auth_required') as mock_auth:
                mock_auth.return_value = lambda f: lambda: f(mock_current_user)

                response = client.get(f'/api/impact/user/{SAMPLE_USER_ID}/timeline?days=30')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['message'] == "USER_TIMELINE_SUCCESS"
        assert len(data['data']['timeline']) == 1

    def test_get_donation_impact_details_success(self, client, mock_services, mock_current_user):
        """Test successful donation impact details retrieval"""
        mock_impact_details = {
            'donation_id': SAMPLE_DONATION_ID,
            'amount': 100.0,
            'onlus_id': SAMPLE_ONLUS_ID,
            'impact_metrics': [
                {
                    'metric_name': 'children_helped',
                    'impact_value': 5,
                    'efficiency_ratio': 0.05
                }
            ],
            'stories_unlocked': [],
            'impact_score': 85.0
        }

        mock_services['impact_tracking'].get_donation_impact_details.return_value = (
            True, "DONATION_IMPACT_DETAILS_SUCCESS", mock_impact_details
        )

        with patch('app.donations.controllers.impact_controller.get_impact_service',
                   return_value=mock_services['impact_tracking']):
            with patch('app.donations.controllers.impact_controller.auth_required') as mock_auth:
                mock_auth.return_value = lambda f: lambda: f(mock_current_user)

                response = client.get(f'/api/impact/donation/{SAMPLE_DONATION_ID}')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['message'] == "DONATION_IMPACT_DETAILS_SUCCESS"
        assert data['data']['donation_id'] == SAMPLE_DONATION_ID

    def test_get_available_stories_success(self, client, mock_services, mock_current_user):
        """Test successful available stories retrieval"""
        mock_stories_data = {
            'stories': [
                {
                    'id': SAMPLE_STORY_ID,
                    'title': 'First Impact Story',
                    'is_unlocked': True,
                    'unlock_level': 1,
                    'category': 'education'
                },
                {
                    'id': str(ObjectId()),
                    'title': 'Next Level Story',
                    'is_unlocked': False,
                    'unlock_level': 3,
                    'category': 'health'
                }
            ],
            'user_level': 2,
            'total_available': 2,
            'unlocked_count': 1
        }

        mock_services['story_unlocking'].get_available_stories.return_value = (
            True, "STORIES_RETRIEVED_SUCCESS", mock_stories_data
        )

        with patch('app.donations.controllers.impact_controller.get_story_service',
                   return_value=mock_services['story_unlocking']):
            with patch('app.donations.controllers.impact_controller.auth_required') as mock_auth:
                mock_auth.return_value = lambda f: lambda: f(mock_current_user)

                response = client.get(
                    f'/api/impact/stories/available?include_locked=true&category=education&limit=20'
                )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['message'] == "STORIES_RETRIEVED_SUCCESS"
        assert len(data['data']['stories']) == 2

    def test_get_story_details_success(self, client, mock_services, mock_current_user):
        """Test successful story details retrieval"""
        mock_story_data = {
            'story': {
                'id': SAMPLE_STORY_ID,
                'title': 'Impact Story',
                'content': 'Story content about impact',
                'is_unlocked': True,
                'unlock_level': 1,
                'onlus_name': 'Education ONLUS',
                'category': 'education'
            },
            'unlock_progress': {
                'progress_percent': 100.0,
                'requirements_met': True
            }
        }

        mock_services['story_unlocking'].get_story_details.return_value = (
            True, "STORIES_RETRIEVED_SUCCESS", mock_story_data
        )

        with patch('app.donations.controllers.impact_controller.get_story_service',
                   return_value=mock_services['story_unlocking']):
            with patch('app.donations.controllers.impact_controller.auth_required') as mock_auth:
                mock_auth.return_value = lambda f: lambda: f(mock_current_user)

                response = client.get(f'/api/impact/stories/{SAMPLE_STORY_ID}')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['message'] == "STORIES_RETRIEVED_SUCCESS"
        assert data['data']['story']['id'] == SAMPLE_STORY_ID

    def test_get_story_progress_success(self, client, mock_services, mock_current_user):
        """Test successful story progress retrieval"""
        mock_progress_data = {
            'progress': {
                'current_level': 2,
                'next_level': 3,
                'progress_to_next': 75.0
            },
            'next_unlocks': [
                {
                    'id': str(ObjectId()),
                    'title': 'Next Story',
                    'unlock_condition_value': 500.0,
                    'progress_percent': 75.0,
                    'remaining_amount': 125.0
                }
            ],
            'achievements': [
                {
                    'level': 1,
                    'title': 'First Donation',
                    'achieved_at': datetime.now(timezone.utc).isoformat()
                }
            ]
        }

        mock_services['story_unlocking'].get_story_progress.return_value = (
            True, "STORY_PROGRESS_SUCCESS", mock_progress_data
        )

        with patch('app.donations.controllers.impact_controller.get_story_service',
                   return_value=mock_services['story_unlocking']):
            with patch('app.donations.controllers.impact_controller.auth_required') as mock_auth:
                mock_auth.return_value = lambda f: lambda: f(mock_current_user)

                response = client.get('/api/impact/stories/progress')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['message'] == "STORY_PROGRESS_SUCCESS"
        assert data['data']['progress']['current_level'] == 2

    def test_get_community_statistics_success(self, client, mock_services, mock_current_user):
        """Test successful community statistics retrieval"""
        mock_stats_data = {
            'period': 'month',
            'statistics': {
                'total_donated': 50000.0,
                'total_donors': 500,
                'active_onlus_count': 25,
                'impact_metrics_summary': {
                    'children_helped': 1250,
                    'schools_built': 5,
                    'water_wells_built': 3
                }
            },
            'growth_rates': {
                'donations_growth': 15.5,
                'users_growth': 8.2
            },
            'top_categories': ['education', 'health', 'environment']
        }

        mock_services['community_impact'].get_community_statistics.return_value = (
            True, "COMMUNITY_STATS_SUCCESS", mock_stats_data
        )

        with patch('app.donations.controllers.impact_controller.get_community_service',
                   return_value=mock_services['community_impact']):
            with patch('app.donations.controllers.impact_controller.auth_required') as mock_auth:
                mock_auth.return_value = lambda f: lambda: f(mock_current_user)

                response = client.get('/api/impact/community/statistics?period=month')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['message'] == "COMMUNITY_STATS_SUCCESS"
        assert data['data']['statistics']['total_donated'] == 50000.0

    def test_get_community_leaderboard_success(self, client, mock_services, mock_current_user):
        """Test successful community leaderboard retrieval"""
        mock_leaderboard_data = {
            'metric': 'total_donated',
            'period': 'all_time',
            'leaderboard': [
                {
                    'rank': 1,
                    'user_id': str(ObjectId()),
                    'user_name': 'Top Donor',
                    'total_donated': 2500.0,
                    'impact_score': 1250.0
                },
                {
                    'rank': 2,
                    'user_id': str(ObjectId()),
                    'user_name': 'Second Donor',
                    'total_donated': 2000.0,
                    'impact_score': 1000.0
                }
            ],
            'user_position': {
                'rank': 15,
                'total_donated': 350.0
            }
        }

        mock_services['community_impact'].get_leaderboard.return_value = (
            True, "LEADERBOARD_SUCCESS", mock_leaderboard_data
        )

        with patch('app.donations.controllers.impact_controller.get_community_service',
                   return_value=mock_services['community_impact']):
            with patch('app.donations.controllers.impact_controller.auth_required') as mock_auth:
                mock_auth.return_value = lambda f: lambda: f(mock_current_user)

                response = client.get('/api/impact/community/leaderboard?metric=total_donated&limit=50')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['message'] == "LEADERBOARD_SUCCESS"
        assert len(data['data']['leaderboard']) == 2

    def test_get_dashboard_data_success(self, client, mock_services, mock_current_user):
        """Test successful dashboard data retrieval"""
        mock_dashboard_data = {
            'user_summary': {
                'total_donated': 350.0,
                'impact_score': 185.0,
                'unlocked_stories_count': 3,
                'current_level': 2
            },
            'featured_stories': [
                {
                    'id': str(ObjectId()),
                    'title': 'Featured Impact Story',
                    'category': 'education',
                    'is_unlocked': True
                }
            ],
            'community_highlights': {
                'total_platform_donated': 100000.0,
                'active_users_count': 750,
                'recent_milestones': [
                    'Reached 100,000€ in total donations!',
                    '50 new schools built this month'
                ]
            },
            'recent_updates': [
                {
                    'id': str(ObjectId()),
                    'title': 'New School Opened',
                    'onlus_name': 'Education ONLUS',
                    'created_at': datetime.now(timezone.utc).isoformat()
                }
            ]
        }

        mock_services['impact_visualization'].get_dashboard_data.return_value = (
            True, "DASHBOARD_DATA_SUCCESS", mock_dashboard_data
        )

        with patch('app.donations.controllers.impact_controller.get_visualization_service',
                   return_value=mock_services['impact_visualization']):
            with patch('app.donations.controllers.impact_controller.auth_required') as mock_auth:
                mock_auth.return_value = lambda f: lambda: f(mock_current_user)

                response = client.get('/api/impact/dashboard')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['message'] == "DASHBOARD_DATA_SUCCESS"
        assert 'user_summary' in data['data']
        assert 'featured_stories' in data['data']

    def test_get_onlus_impact_metrics_success(self, client, mock_services, mock_current_user):
        """Test successful ONLUS impact metrics retrieval"""
        mock_metrics_data = {
            'onlus_id': SAMPLE_ONLUS_ID,
            'metrics': [
                {
                    'metric_name': 'children_helped',
                    'current_value': 150,
                    'unit': 'count',
                    'efficiency_ratio': 0.06,
                    'trend': 'increasing'
                },
                {
                    'metric_name': 'schools_built',
                    'current_value': 3,
                    'unit': 'count',
                    'efficiency_ratio': 0.001,
                    'trend': 'stable'
                }
            ],
            'trends': {
                'children_helped': [
                    {'date': '2024-09-01', 'value': 120},
                    {'date': '2024-09-15', 'value': 135},
                    {'date': '2024-09-30', 'value': 150}
                ]
            },
            'summary': {
                'total_impact_value': 153,
                'efficiency_score': 8.5,
                'improvement_rate': 12.5
            }
        }

        mock_services['impact_visualization'].get_onlus_impact_visualization.return_value = (
            True, "ONLUS_VISUALIZATION_SUCCESS", mock_metrics_data
        )

        with patch('app.donations.controllers.impact_controller.get_visualization_service',
                   return_value=mock_services['impact_visualization']):
            with patch('app.donations.controllers.impact_controller.auth_required') as mock_auth:
                mock_auth.return_value = lambda f: lambda: f(mock_current_user)

                response = client.get(f'/api/impact/onlus/{SAMPLE_ONLUS_ID}/metrics?period=month&include_trends=true')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['message'] == "ONLUS_VISUALIZATION_SUCCESS"
        assert data['data']['onlus_id'] == SAMPLE_ONLUS_ID
        assert len(data['data']['metrics']) == 2

    def test_get_onlus_impact_updates_success(self, client, mock_services, mock_current_user):
        """Test successful ONLUS impact updates retrieval"""
        mock_updates_data = {
            'onlus_id': SAMPLE_ONLUS_ID,
            'updates': [
                {
                    'id': str(ObjectId()),
                    'title': 'New School Construction',
                    'content': 'Construction of new school in progress',
                    'update_type': 'progress',
                    'priority': 'high',
                    'created_at': datetime.now(timezone.utc).isoformat(),
                    'engagement_metrics': {
                        'views': 245,
                        'likes': 18,
                        'shares': 5
                    }
                }
            ],
            'pagination': {
                'total_count': 15,
                'has_more': True,
                'next_cursor': 'next_page_token'
            }
        }

        mock_services['impact_visualization'].get_onlus_updates_with_engagement.return_value = (
            True, "ONLUS_UPDATES_SUCCESS", mock_updates_data
        )

        with patch('app.donations.controllers.impact_controller.get_visualization_service',
                   return_value=mock_services['impact_visualization']):
            with patch('app.donations.controllers.impact_controller.auth_required') as mock_auth:
                mock_auth.return_value = lambda f: lambda: f(mock_current_user)

                response = client.get(f'/api/impact/onlus/{SAMPLE_ONLUS_ID}/updates?include_engagement=true&limit=20')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['message'] == "ONLUS_UPDATES_SUCCESS"
        assert len(data['data']['updates']) == 1

    def test_get_monthly_report_success(self, client, mock_services, mock_current_user):
        """Test successful monthly report retrieval"""
        mock_report_data = {
            'report': {
                'id': str(ObjectId()),
                'report_type': 'monthly',
                'title': 'September 2024 Community Report',
                'period': {
                    'year': 2024,
                    'month': 9,
                    'start_date': '2024-09-01T00:00:00Z',
                    'end_date': '2024-09-30T23:59:59Z'
                },
                'summary': {
                    'total_donations': 25000.0,
                    'total_donors': 300,
                    'active_onlus_count': 15,
                    'impact_highlights': [
                        '500 children received education support',
                        '5 new water wells constructed',
                        '25 families received medical aid'
                    ]
                },
                'detailed_metrics': {
                    'donations_by_category': {
                        'education': 10000.0,
                        'health': 8000.0,
                        'environment': 7000.0
                    },
                    'growth_compared_to_previous': {
                        'donations_growth': 18.5,
                        'users_growth': 12.3
                    }
                }
            }
        }

        mock_services['community_impact'].get_monthly_report.return_value = (
            True, "MONTHLY_REPORT_SUCCESS", mock_report_data
        )

        with patch('app.donations.controllers.impact_controller.get_community_service',
                   return_value=mock_services['community_impact']):
            with patch('app.donations.controllers.impact_controller.auth_required') as mock_auth:
                mock_auth.return_value = lambda f: lambda: f(mock_current_user)

                response = client.get('/api/impact/reports/monthly/2024/9')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['message'] == "MONTHLY_REPORT_SUCCESS"
        assert data['data']['report']['period']['year'] == 2024

    def test_get_annual_report_success(self, client, mock_services, mock_current_user):
        """Test successful annual report retrieval"""
        mock_report_data = {
            'report': {
                'id': str(ObjectId()),
                'report_type': 'annual',
                'title': '2024 Annual Impact Report',
                'year': 2024,
                'summary': {
                    'total_donations': 300000.0,
                    'total_donors': 2500,
                    'active_onlus_count': 50,
                    'major_achievements': [
                        'Reached 300,000€ in total donations',
                        '2,500 active donors joined the platform',
                        '15 major infrastructure projects completed'
                    ]
                },
                'monthly_breakdown': [
                    {'month': 1, 'donations': 20000.0, 'donors': 180},
                    {'month': 2, 'donations': 22000.0, 'donors': 200}
                ]
            }
        }

        mock_services['community_impact'].get_annual_report.return_value = (
            True, "ANNUAL_REPORT_SUCCESS", mock_report_data
        )

        with patch('app.donations.controllers.impact_controller.get_community_service',
                   return_value=mock_services['community_impact']):
            with patch('app.donations.controllers.impact_controller.auth_required') as mock_auth:
                mock_auth.return_value = lambda f: lambda: f(mock_current_user)

                response = client.get('/api/impact/reports/annual/2024')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['message'] == "ANNUAL_REPORT_SUCCESS"
        assert data['data']['report']['year'] == 2024

    def test_create_impact_metric_admin_success(self, client, mock_services, admin_user):
        """Test successful impact metric creation by admin"""
        metric_data = {
            'onlus_id': SAMPLE_ONLUS_ID,
            'metric_name': 'children_helped',
            'metric_type': 'cumulative',
            'current_value': 150,
            'unit': 'count',
            'description': 'Number of children helped through programs',
            'related_donations_amount': 2500.0
        }

        mock_response_data = {
            'metric_id': str(ObjectId()),
            'metric_name': 'children_helped',
            'current_value': 150,
            'created_at': datetime.now(timezone.utc).isoformat()
        }

        mock_services['impact_tracking'].create_impact_metric.return_value = (
            True, "METRIC_CREATED_SUCCESS", mock_response_data
        )

        with patch('app.donations.controllers.impact_controller.get_impact_service',
                   return_value=mock_services['impact_tracking']):
            with patch('app.donations.controllers.impact_controller.admin_required') as mock_admin:
                mock_admin.return_value = lambda f: lambda: f(admin_user)

                response = client.post(
                    '/api/impact/admin/metrics',
                    data=json.dumps(metric_data),
                    content_type='application/json'
                )

        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['message'] == "METRIC_CREATED_SUCCESS"
        assert 'metric_id' in data['data']

    def test_create_impact_metric_admin_required(self, client, mock_current_user):
        """Test impact metric creation requires admin access"""
        metric_data = {
            'onlus_id': SAMPLE_ONLUS_ID,
            'metric_name': 'children_helped',
            'current_value': 150
        }

        with patch('app.donations.controllers.impact_controller.admin_required') as mock_admin:
            # Simulate admin_required decorator denying access
            mock_admin.side_effect = lambda f: lambda: ({"success": False, "message": "ADMIN_ACCESS_REQUIRED"}, 403)

            response = client.post(
                '/api/impact/admin/metrics',
                data=json.dumps(metric_data),
                content_type='application/json'
            )

        assert response.status_code == 403

    def test_create_impact_update_admin_success(self, client, mock_services, admin_user):
        """Test successful impact update creation by admin"""
        update_data = {
            'onlus_id': SAMPLE_ONLUS_ID,
            'title': 'New School Opened',
            'content': 'We successfully opened a new school',
            'update_type': 'milestone',
            'priority': 'high',
            'tags': ['education', 'milestone'],
            'related_metrics': {
                'children_helped': 150,
                'schools_built': 1
            }
        }

        mock_response_data = {
            'update_id': str(ObjectId()),
            'title': 'New School Opened',
            'created_at': datetime.now(timezone.utc).isoformat(),
            'status': 'published'
        }

        mock_services['impact_tracking'].create_impact_update.return_value = (
            True, "IMPACT_UPDATE_CREATED_SUCCESS", mock_response_data
        )

        with patch('app.donations.controllers.impact_controller.get_impact_service',
                   return_value=mock_services['impact_tracking']):
            with patch('app.donations.controllers.impact_controller.admin_required') as mock_admin:
                mock_admin.return_value = lambda f: lambda: f(admin_user)

                response = client.post(
                    '/api/impact/admin/updates',
                    data=json.dumps(update_data),
                    content_type='application/json'
                )

        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['message'] == "IMPACT_UPDATE_CREATED_SUCCESS"
        assert 'update_id' in data['data']

    def test_generate_real_time_report_admin_success(self, client, mock_services, admin_user):
        """Test successful real-time report generation by admin"""
        report_request = {
            'report_type': 'real_time_snapshot',
            'include_projections': True,
            'filters': {
                'start_date': '2024-09-01T00:00:00Z',
                'end_date': '2024-09-30T23:59:59Z'
            }
        }

        mock_report_data = {
            'report': {
                'id': str(ObjectId()),
                'report_type': 'real_time_snapshot',
                'generated_at': datetime.now(timezone.utc).isoformat(),
                'platform_totals': {
                    'total_donations': 150000.0,
                    'total_users': 1200,
                    'active_onlus_count': 35
                },
                'projections': {
                    'monthly_growth_rate': 15.5,
                    'projected_year_end_donations': 600000.0
                }
            }
        }

        mock_services['community_impact'].generate_real_time_report.return_value = (
            True, "REAL_TIME_REPORT_GENERATED", mock_report_data
        )

        with patch('app.donations.controllers.impact_controller.get_community_service',
                   return_value=mock_services['community_impact']):
            with patch('app.donations.controllers.impact_controller.admin_required') as mock_admin:
                mock_admin.return_value = lambda f: lambda: f(admin_user)

                response = client.post(
                    '/api/impact/admin/reports/generate',
                    data=json.dumps(report_request),
                    content_type='application/json'
                )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['message'] == "REAL_TIME_REPORT_GENERATED"
        assert 'report' in data['data']

    def test_error_handling_service_failure(self, client, mock_services, mock_current_user):
        """Test error handling when service fails"""
        # Mock service failure
        mock_services['impact_tracking'].get_user_impact_summary.return_value = (
            False, "USER_IMPACT_SUMMARY_ERROR", None
        )

        with patch('app.donations.controllers.impact_controller.get_impact_service',
                   return_value=mock_services['impact_tracking']):
            with patch('app.donations.controllers.impact_controller.auth_required') as mock_auth:
                mock_auth.return_value = lambda f: lambda: f(mock_current_user)

                response = client.get(f'/api/impact/user/{SAMPLE_USER_ID}')

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert data['message'] == "USER_IMPACT_SUMMARY_ERROR"

    def test_validation_missing_data(self, client, admin_user):
        """Test validation for missing request data"""
        with patch('app.donations.controllers.impact_controller.admin_required') as mock_admin:
            mock_admin.return_value = lambda f: lambda: f(admin_user)

            # Send request without data
            response = client.post('/api/impact/admin/metrics')

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert "DATA_REQUIRED" in data['message']

    def test_validation_invalid_year_month(self, client, mock_current_user):
        """Test validation for invalid year/month parameters"""
        with patch('app.donations.controllers.impact_controller.auth_required') as mock_auth:
            mock_auth.return_value = lambda f: lambda: f(mock_current_user)

            # Invalid month
            response = client.get('/api/impact/reports/monthly/2024/13')

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert "INVALID_MONTH" in data['message']


if __name__ == '__main__':
    pytest.main([__file__])