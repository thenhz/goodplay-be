"""
Tests for GOO-16 Impact Tracking Services

Tests all service classes with mocked repository dependencies,
focusing on business logic and service orchestration.
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, MagicMock, patch
from bson import ObjectId

# Import services to test
from app.donations.services.impact_tracking_service import ImpactTrackingService
from app.donations.services.story_unlocking_service import StoryUnlockingService
from app.donations.services.impact_visualization_service import ImpactVisualizationService
from app.donations.services.community_impact_service import CommunityImpactService

# Import models for mock data
from app.donations.models.impact_story import ImpactStory
from app.donations.models.impact_metric import ImpactMetric
from app.donations.models.impact_update import ImpactUpdate
from app.donations.models.community_report import CommunityReport


class TestImpactTrackingService:
    """Tests for ImpactTrackingService"""

    @pytest.fixture
    def mock_repositories(self):
        """Mock all repositories used by the service"""
        return {
            'impact_story_repo': Mock(),
            'impact_metric_repo': Mock(),
            'impact_update_repo': Mock(),
            'community_report_repo': Mock()
        }

    @pytest.fixture
    def impact_service(self, mock_repositories):
        """Create service with mocked repositories"""
        service = ImpactTrackingService()
        # Mock the lazy loading of repositories
        service._impact_story_repo = mock_repositories['impact_story_repo']
        service._impact_metric_repo = mock_repositories['impact_metric_repo']
        service._impact_update_repo = mock_repositories['impact_update_repo']
        service._community_report_repo = mock_repositories['community_report_repo']
        return service

    def test_track_donation_impact_success(self, impact_service, mock_repositories):
        """Test successful donation impact tracking"""
        donation_id = str(ObjectId())
        user_id = str(ObjectId())
        amount = 150.0
        onlus_id = str(ObjectId())

        # Mock user statistics
        mock_user_stats = {
            'total_donated': 150.0,
            'donation_count': 1,
            'onlus_diversity': 1,
            'impact_score': 75.0
        }

        # Mock repository responses
        mock_repositories['impact_metric_repo'].get_metrics_by_onlus.return_value = []
        mock_repositories['impact_story_repo'].get_stories_by_unlock_range.return_value = []

        with patch.object(impact_service, '_get_user_statistics', return_value=mock_user_stats):
            with patch.object(impact_service, '_update_onlus_metrics', return_value=True):
                with patch.object(impact_service, '_check_milestone_unlocks', return_value=[]):
                    success, message, result = impact_service.track_donation_impact(
                        donation_id, user_id, amount, onlus_id
                    )

        assert success is True
        assert "IMPACT_TRACKING_SUCCESS" in message
        assert result is not None
        assert result['donation_id'] == donation_id
        assert result['impact_recorded'] is True

    def test_track_donation_impact_invalid_amount(self, impact_service):
        """Test donation impact tracking with invalid amount"""
        donation_id = str(ObjectId())
        user_id = str(ObjectId())
        amount = -50.0  # Invalid negative amount
        onlus_id = str(ObjectId())

        success, message, result = impact_service.track_donation_impact(
            donation_id, user_id, amount, onlus_id
        )

        assert success is False
        assert "INVALID" in message or "amount" in message.lower()
        assert result is None

    def test_get_user_impact_summary_success(self, impact_service, mock_repositories):
        """Test successful user impact summary retrieval"""
        user_id = str(ObjectId())

        # Mock user statistics
        mock_user_stats = {
            'total_donated': 350.0,
            'donation_count': 7,
            'onlus_diversity': 3,
            'impact_score': 185.0
        }

        # Mock recent donations
        mock_donations = [
            {
                'donation_id': str(ObjectId()),
                'amount': 100.0,
                'onlus_id': str(ObjectId()),
                'created_at': datetime.now(timezone.utc)
            }
        ]

        # Mock unlocked stories
        mock_stories = [
            {
                'id': str(ObjectId()),
                'title': 'Your First Impact',
                'is_unlocked': True,
                'unlock_level': 1
            }
        ]

        with patch.object(impact_service, '_get_user_statistics', return_value=mock_user_stats):
            with patch.object(impact_service, '_get_user_recent_donations', return_value=mock_donations):
                with patch.object(impact_service, '_get_user_milestones_progress', return_value=[]):
                    mock_repositories['impact_story_repo'].get_stories_for_user.return_value = mock_stories

                    success, message, result = impact_service.get_user_impact_summary(user_id)

        assert success is True
        assert "USER_IMPACT_SUMMARY_SUCCESS" in message
        assert result is not None
        assert result['user_id'] == user_id
        assert result['statistics']['total_donated'] == 350.0
        assert len(result['unlocked_stories']) == 1

    def test_get_user_impact_summary_user_not_found(self, impact_service):
        """Test user impact summary for non-existent user"""
        user_id = str(ObjectId())

        with patch.object(impact_service, '_get_user_statistics', return_value=None):
            success, message, result = impact_service.get_user_impact_summary(user_id)

        assert success is False
        assert "USER_NOT_FOUND" in message or "not found" in message.lower()
        assert result is None

    def test_get_donation_impact_details_success(self, impact_service, mock_repositories):
        """Test successful donation impact details retrieval"""
        donation_id = str(ObjectId())

        # Mock donation details
        mock_donation = {
            'donation_id': donation_id,
            'user_id': str(ObjectId()),
            'onlus_id': str(ObjectId()),
            'amount': 100.0,
            'created_at': datetime.now(timezone.utc)
        }

        # Mock related metrics
        mock_metrics = [
            {
                'metric_name': 'children_helped',
                'impact_value': 5,
                'efficiency_ratio': 0.05
            }
        ]

        with patch.object(impact_service, '_get_donation_details', return_value=mock_donation):
            with patch.object(impact_service, '_get_donation_related_metrics', return_value=mock_metrics):
                with patch.object(impact_service, '_calculate_donation_impact_score', return_value=85.0):
                    success, message, result = impact_service.get_donation_impact_details(str(donation_id))

        assert success is True
        assert "DONATION_IMPACT_DETAILS_SUCCESS" in message
        assert result is not None
        assert result['donation_id'] == str(donation_id)
        assert len(result['impact_metrics']) == 1

    def test_get_user_impact_timeline_success(self, impact_service):
        """Test successful user impact timeline retrieval"""
        user_id = str(ObjectId())
        days = 30

        # Mock timeline events
        mock_timeline = [
            {
                'date': datetime.now(timezone.utc).date(),
                'event_type': 'donation',
                'amount': 50.0,
                'onlus_name': 'Test ONLUS',
                'impact_generated': 'Helped 2 children'
            },
            {
                'date': (datetime.now(timezone.utc) - timedelta(days=1)).date(),
                'event_type': 'story_unlock',
                'story_title': 'First Impact Story',
                'unlock_level': 1
            }
        ]

        with patch.object(impact_service, '_build_user_timeline', return_value=mock_timeline):
            success, message, result = impact_service.get_user_impact_timeline(user_id, days)

        assert success is True
        assert "USER_TIMELINE_SUCCESS" in message
        assert result is not None
        assert len(result['timeline']) == 2
        assert result['period_days'] == days


class TestStoryUnlockingService:
    """Tests for StoryUnlockingService"""

    @pytest.fixture
    def mock_story_repo(self):
        return Mock()

    @pytest.fixture
    def unlocking_service(self, mock_story_repo):
        service = StoryUnlockingService()
        service._impact_story_repo = mock_story_repo
        return service

    def test_get_available_stories_success(self, unlocking_service, mock_story_repo):
        """Test successful retrieval of available stories"""
        user_id = str(ObjectId())

        # Mock user statistics
        mock_user_stats = {
            'total_donated': 250.0,
            'donation_count': 5,
            'onlus_diversity': 2
        }

        # Mock available stories
        mock_stories = [
            {
                'id': str(ObjectId()),
                'title': 'First Milestone',
                'is_unlocked': True,
                'unlock_level': 1,
                'category': 'education'
            },
            {
                'id': str(ObjectId()),
                'title': 'Growing Impact',
                'is_unlocked': False,
                'unlock_level': 3,
                'category': 'health'
            }
        ]

        with patch.object(unlocking_service, '_get_user_statistics', return_value=mock_user_stats):
            mock_story_repo.get_stories_for_user.return_value = mock_stories

            success, message, result = unlocking_service.get_available_stories(
                user_id, include_locked=True, category='education'
            )

        assert success is True
        assert "STORIES_RETRIEVED_SUCCESS" in message
        assert result is not None
        assert len(result['stories']) == 2
        assert result['user_level'] >= 1

    def test_get_story_progress_success(self, unlocking_service, mock_story_repo):
        """Test successful story progress retrieval"""
        user_id = str(ObjectId())

        # Mock user statistics
        mock_user_stats = {
            'total_donated': 75.0,
            'donation_count': 3,
            'onlus_diversity': 1
        }

        # Mock next stories
        mock_next_stories = [
            {
                'id': str(ObjectId()),
                'title': 'Next Story',
                'unlock_condition_value': 100.0,
                'unlock_progress': {
                    'progress_percent': 75.0,
                    'remaining_amount': 25.0
                }
            }
        ]

        with patch.object(unlocking_service, '_get_user_statistics', return_value=mock_user_stats):
            mock_story_repo.get_next_unlock_stories.return_value = mock_next_stories

            success, message, result = unlocking_service.get_story_progress(user_id)

        assert success is True
        assert "STORY_PROGRESS_SUCCESS" in message
        assert result is not None
        assert len(result['next_unlocks']) == 1
        assert result['progress']['current_level'] >= 0

    def test_get_story_details_success(self, unlocking_service, mock_story_repo):
        """Test successful story details retrieval"""
        story_id = str(ObjectId())
        user_id = str(ObjectId())

        # Mock story
        mock_story = ImpactStory(
            onlus_id='test_onlus',
            title='Test Story',
            content='Story content',
            story_type='milestone',
            unlock_condition_type='total_donated',
            unlock_condition_value=100.0
        )
        mock_story._id = ObjectId(story_id)

        # Mock user statistics
        mock_user_stats = {
            'total_donated': 150.0,
            'donation_count': 3
        }

        mock_story_repo.get_story_by_id.return_value = mock_story

        with patch.object(unlocking_service, '_get_user_statistics', return_value=mock_user_stats):
            success, message, result = unlocking_service.get_story_details(story_id, user_id)

        assert success is True
        assert "STORIES_RETRIEVED_SUCCESS" in message
        assert result is not None
        assert result['story']['id'] == story_id
        assert result['story']['is_unlocked'] is True

    def test_get_story_details_not_found(self, unlocking_service, mock_story_repo):
        """Test story details for non-existent story"""
        story_id = str(ObjectId())
        user_id = str(ObjectId())

        mock_story_repo.get_story_by_id.return_value = None

        success, message, result = unlocking_service.get_story_details(story_id, user_id)

        assert success is False
        assert "STORY_NOT_FOUND" in message
        assert result is None

    def test_check_and_unlock_stories_milestone_reached(self, unlocking_service, mock_story_repo):
        """Test story unlocking when milestone is reached"""
        user_id = str(ObjectId())
        new_total_donated = 100.0

        # Mock stories in unlock range
        mock_unlockable_stories = [
            ImpactStory(
                onlus_id='test_onlus',
                title='Milestone Story',
                content='Content',
                story_type='milestone',
                unlock_condition_type='total_donated',
                unlock_condition_value=100.0
            )
        ]
        mock_unlockable_stories[0]._id = ObjectId()

        mock_story_repo.get_stories_by_unlock_range.return_value = mock_unlockable_stories

        with patch.object(unlocking_service, '_log_story_unlock', return_value=True):
            unlocked_stories = unlocking_service.check_and_unlock_stories(user_id, new_total_donated)

        assert len(unlocked_stories) == 1
        assert unlocked_stories[0]['title'] == 'Milestone Story'
        assert unlocked_stories[0]['just_unlocked'] is True


class TestImpactVisualizationService:
    """Tests for ImpactVisualizationService"""

    @pytest.fixture
    def mock_repositories(self):
        return {
            'impact_metric_repo': Mock(),
            'impact_update_repo': Mock(),
            'impact_story_repo': Mock()
        }

    @pytest.fixture
    def visualization_service(self, mock_repositories):
        service = ImpactVisualizationService()
        service._impact_metric_repo = mock_repositories['impact_metric_repo']
        service._impact_update_repo = mock_repositories['impact_update_repo']
        service._impact_story_repo = mock_repositories['impact_story_repo']
        return service

    def test_get_dashboard_data_success(self, visualization_service, mock_repositories):
        """Test successful dashboard data retrieval"""
        user_id = str(ObjectId())

        # Mock user summary
        mock_user_summary = {
            'total_donated': 200.0,
            'impact_score': 120.0,
            'unlocked_stories_count': 3
        }

        # Mock featured stories
        mock_featured_stories = [
            ImpactStory(
                onlus_id='test_onlus',
                title='Featured Story',
                content='Content',
                story_type='milestone',
                unlock_condition_type='total_donated',
                unlock_condition_value=50.0
            )
        ]

        # Mock community highlights
        mock_community_data = {
            'total_platform_donated': 50000.0,
            'active_users_count': 150,
            'top_onlus_this_month': 'Education ONLUS'
        }

        mock_repositories['impact_story_repo'].get_featured_stories.return_value = mock_featured_stories

        with patch.object(visualization_service, '_get_user_dashboard_summary', return_value=mock_user_summary):
            with patch.object(visualization_service, '_get_community_highlights', return_value=mock_community_data):
                success, message, result = visualization_service.get_dashboard_data(user_id)

        assert success is True
        assert "DASHBOARD_DATA_SUCCESS" in message
        assert result is not None
        assert 'user_summary' in result
        assert 'featured_stories' in result
        assert 'community_highlights' in result

    def test_get_onlus_impact_visualization_success(self, visualization_service, mock_repositories):
        """Test successful ONLUS impact visualization"""
        onlus_id = str(ObjectId())

        # Mock metrics
        mock_metrics = [
            ImpactMetric(
                onlus_id=str(onlus_id),
                metric_name='children_helped',
                metric_type='cumulative',
                current_value=150,
                unit='count',
                related_donations_amount=3000.0
            )
        ]

        # Mock recent updates
        mock_updates = [
            ImpactUpdate(
                onlus_id=str(onlus_id),
                title='Recent Update',
                content='Update content',
                update_type='regular',
                priority='medium'
            )
        ]

        mock_repositories['impact_metric_repo'].get_metrics_by_onlus.return_value = mock_metrics
        mock_repositories['impact_update_repo'].get_updates_by_onlus.return_value = mock_updates

        with patch.object(visualization_service, '_calculate_impact_trends', return_value={}):
            success, message, result = visualization_service.get_onlus_impact_visualization(
                str(onlus_id), period='month'
            )

        assert success is True
        assert "ONLUS_VISUALIZATION_SUCCESS" in message
        assert result is not None
        assert result['onlus_id'] == str(onlus_id)
        assert len(result['metrics']) == 1
        assert len(result['recent_updates']) == 1


class TestCommunityImpactService:
    """Tests for CommunityImpactService"""

    @pytest.fixture
    def mock_repositories(self):
        return {
            'community_report_repo': Mock(),
            'impact_metric_repo': Mock(),
            'impact_update_repo': Mock()
        }

    @pytest.fixture
    def community_service(self, mock_repositories):
        service = CommunityImpactService()
        service._community_report_repo = mock_repositories['community_report_repo']
        service._impact_metric_repo = mock_repositories['impact_metric_repo']
        service._impact_update_repo = mock_repositories['impact_update_repo']
        return service

    def test_get_community_statistics_success(self, community_service, mock_repositories):
        """Test successful community statistics retrieval"""
        period = 'month'

        # Mock aggregated statistics
        mock_stats = {
            'total_donated': 25000.0,
            'total_donors': 300,
            'active_onlus_count': 15,
            'impact_metrics_summary': {
                'children_helped': 500,
                'schools_built': 5
            }
        }

        with patch.object(community_service, '_aggregate_community_stats', return_value=mock_stats):
            with patch.object(community_service, '_calculate_growth_rates', return_value={}):
                success, message, result = community_service.get_community_statistics(period)

        assert success is True
        assert "COMMUNITY_STATS_SUCCESS" in message
        assert result is not None
        assert result['period'] == period
        assert result['statistics']['total_donated'] == 25000.0

    def test_get_leaderboard_success(self, community_service):
        """Test successful leaderboard retrieval"""
        metric = 'total_donated'
        limit = 50

        # Mock leaderboard data
        mock_leaderboard = [
            {
                'user_id': str(ObjectId()),
                'user_name': 'Top Donor',
                'total_donated': 1000.0,
                'rank': 1,
                'impact_score': 500.0
            },
            {
                'user_id': str(ObjectId()),
                'user_name': 'Second Donor',
                'total_donated': 800.0,
                'rank': 2,
                'impact_score': 400.0
            }
        ]

        with patch.object(community_service, '_build_leaderboard', return_value=mock_leaderboard):
            success, message, result = community_service.get_leaderboard(metric, limit)

        assert success is True
        assert "LEADERBOARD_SUCCESS" in message
        assert result is not None
        assert len(result['leaderboard']) == 2
        assert result['leaderboard'][0]['rank'] == 1

    def test_generate_real_time_report_success(self, community_service, mock_repositories):
        """Test successful real-time report generation"""
        report_type = 'real_time_snapshot'

        # Mock snapshot data
        mock_snapshot = {
            'timestamp': datetime.now(timezone.utc),
            'platform_totals': {
                'total_donations': 100000.0,
                'total_users': 500,
                'active_onlus_count': 25
            },
            'recent_activity': {
                'donations_last_24h': 2500.0,
                'new_users_last_24h': 5
            }
        }

        mock_repositories['community_report_repo'].generate_real_time_snapshot.return_value = mock_snapshot

        success, message, result = community_service.generate_real_time_report(report_type)

        assert success is True
        assert "REAL_TIME_REPORT_GENERATED" in message
        assert result is not None
        assert 'report' in result
        assert result['report']['platform_totals']['total_donations'] == 100000.0

    def test_get_monthly_report_success(self, community_service, mock_repositories):
        """Test successful monthly report retrieval"""
        year = 2024
        month = 9

        # Mock monthly report
        mock_report = CommunityReport(
            report_type='monthly',
            title='September 2024 Report',
            summary='Monthly summary',
            period_start=datetime(2024, 9, 1, tzinfo=timezone.utc),
            period_end=datetime(2024, 9, 30, tzinfo=timezone.utc),
            total_donations=15000.0,
            total_donors=250
        )
        mock_report._id = ObjectId()

        mock_repositories['community_report_repo'].get_report_by_period.return_value = mock_report

        success, message, result = community_service.get_monthly_report(year, month)

        assert success is True
        assert "MONTHLY_REPORT_SUCCESS" in message
        assert result is not None
        assert result['report']['title'] == 'September 2024 Report'

    def test_get_monthly_report_not_found(self, community_service, mock_repositories):
        """Test monthly report retrieval when report doesn't exist"""
        year = 2024
        month = 13  # Invalid month

        mock_repositories['community_report_repo'].get_report_by_period.return_value = None

        success, message, result = community_service.get_monthly_report(year, month)

        assert success is False
        assert "REPORT_NOT_FOUND" in message
        assert result is None


if __name__ == '__main__':
    pytest.main([__file__])