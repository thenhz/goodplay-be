"""
Tests for GOO-16 Impact Tracking Integration

Integration tests that verify end-to-end functionality
of the impact tracking system components working together.
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch, MagicMock
from bson import ObjectId

# Import all components for integration testing
from app.donations.models.impact_story import ImpactStory, StoryType, UnlockConditionType
from app.donations.models.impact_metric import ImpactMetric, MetricType, MetricUnit
from app.donations.models.impact_update import ImpactUpdate, UpdateType, UpdatePriority
from app.donations.models.community_report import CommunityReport, ReportType

from app.donations.services.impact_tracking_service import ImpactTrackingService
from app.donations.services.story_unlocking_service import StoryUnlockingService
from app.donations.services.impact_visualization_service import ImpactVisualizationService
from app.donations.services.community_impact_service import CommunityImpactService


class TestImpactTrackingIntegration:
    """Integration tests for complete impact tracking workflows"""

    @pytest.fixture
    def mock_db_collections(self):
        """Mock MongoDB collections for all repositories"""
        collections = {
            'impact_stories': Mock(),
            'impact_metrics': Mock(),
            'impact_updates': Mock(),
            'community_reports': Mock()
        }

        # Configure basic find/insert behaviors
        for collection in collections.values():
            collection.insert_one.return_value = Mock(inserted_id=ObjectId())
            collection.find_one.return_value = None
            collection.find.return_value.sort.return_value.limit.return_value = []
            collection.update_one.return_value = Mock(modified_count=1)
            collection.count_documents.return_value = 0
            collection.aggregate.return_value = []

        return collections

    @pytest.fixture
    def integrated_services(self, mock_db_collections):
        """Create all services with mocked database connections"""
        services = {
            'impact_tracking': ImpactTrackingService(),
            'story_unlocking': StoryUnlockingService(),
            'impact_visualization': ImpactVisualizationService(),
            'community_impact': CommunityImpactService()
        }

        # Mock the repository collections
        with patch('app.donations.repositories.impact_story_repository.ImpactStoryRepository') as mock_story_repo:
            with patch('app.donations.repositories.impact_metric_repository.ImpactMetricRepository') as mock_metric_repo:
                with patch('app.donations.repositories.impact_update_repository.ImpactUpdateRepository') as mock_update_repo:
                    with patch('app.donations.repositories.community_report_repository.CommunityReportRepository') as mock_report_repo:

                        # Configure repository mocks
                        mock_story_repo.return_value.collection = mock_db_collections['impact_stories']
                        mock_metric_repo.return_value.collection = mock_db_collections['impact_metrics']
                        mock_update_repo.return_value.collection = mock_db_collections['impact_updates']
                        mock_report_repo.return_value.collection = mock_db_collections['community_reports']

                        yield services

    def test_complete_donation_to_impact_workflow(self, integrated_services, mock_db_collections):
        """Test complete workflow from donation to impact tracking"""
        # Setup test data
        donation_id = str(ObjectId())
        user_id = str(ObjectId())
        onlus_id = str(ObjectId())
        amount = 150.0

        # Mock user statistics (progressive user with some history)
        mock_user_stats = {
            'total_donated': 150.0,  # This donation brings them to €150
            'donation_count': 3,
            'onlus_diversity': 2,
            'impact_score': 125.0
        }

        # Mock existing metrics for the ONLUS
        existing_metric_doc = {
            '_id': ObjectId(),
            'onlus_id': onlus_id,
            'metric_name': 'children_helped',
            'metric_type': MetricType.CUMULATIVE.value,
            'current_value': 100,
            'unit': MetricUnit.COUNT.value,
            'related_donations_amount': 2000.0,
            'collection_date': datetime.now(timezone.utc),
            'is_active': True
        }

        # Mock stories that should be unlocked at €150 level
        story_docs = [
            {
                '_id': ObjectId(),
                'onlus_id': onlus_id,
                'title': 'Growing Impact Story',
                'content': 'Your donations are making a real difference...',
                'story_type': StoryType.MILESTONE.value,
                'unlock_condition_type': UnlockConditionType.TOTAL_DONATED.value,
                'unlock_condition_value': 100.0,  # Should unlock at €100
                'category': 'education',
                'is_active': True,
                'created_at': datetime.now(timezone.utc)
            }
        ]

        # Configure mocks for the workflow
        mock_db_collections['impact_metrics'].find.return_value.sort.return_value.limit.return_value = [existing_metric_doc]
        mock_db_collections['impact_stories'].find.return_value.sort.return_value.limit.return_value = story_docs

        # Mock cursor iteration
        mock_cursor = Mock()
        mock_cursor.__iter__ = Mock(return_value=iter(story_docs))
        mock_db_collections['impact_stories'].find.return_value.sort.return_value.limit.return_value = mock_cursor

        # Execute the complete workflow
        impact_service = integrated_services['impact_tracking']

        with patch.object(impact_service, '_get_user_statistics', return_value=mock_user_stats):
            with patch.object(impact_service, '_get_user_recent_donations', return_value=[]):
                with patch.object(impact_service, '_get_user_milestones_progress', return_value=[]):

                    # Track the donation impact
                    success, message, result = impact_service.track_donation_impact(
                        donation_id, user_id, amount, onlus_id
                    )

        # Verify the workflow completed successfully
        assert success is True
        assert "IMPACT_TRACKING_SUCCESS" in message
        assert result is not None
        assert result['donation_id'] == donation_id
        assert result['impact_recorded'] is True

        # Verify database interactions occurred
        mock_db_collections['impact_metrics'].find.assert_called()
        mock_db_collections['impact_stories'].find.assert_called()

    def test_story_unlocking_milestone_progression(self, integrated_services, mock_db_collections):
        """Test story unlocking as user progresses through milestones"""
        user_id = str(ObjectId())

        # Simulate user progression through different donation levels
        progression_stages = [
            {'total_donated': 25.0, 'expected_unlocks': 1},   # First milestone
            {'total_donated': 100.0, 'expected_unlocks': 3},  # Several stories unlocked
            {'total_donated': 500.0, 'expected_unlocks': 6}   # Higher level stories
        ]

        # Create stories at different unlock levels
        story_docs = []
        for i, unlock_value in enumerate([10, 25, 50, 100, 250, 500, 1000]):
            story_docs.append({
                '_id': ObjectId(),
                'onlus_id': str(ObjectId()),
                'title': f'Milestone Story {i+1}',
                'content': f'Story content for €{unlock_value} milestone',
                'story_type': StoryType.MILESTONE.value,
                'unlock_condition_type': UnlockConditionType.TOTAL_DONATED.value,
                'unlock_condition_value': float(unlock_value),
                'category': 'education',
                'priority': 10 - i,  # Higher priority for earlier milestones
                'is_active': True,
                'created_at': datetime.now(timezone.utc) - timedelta(days=i)
            })

        story_service = integrated_services['story_unlocking']

        for stage in progression_stages:
            # Mock user statistics for this stage
            user_stats = {
                'total_donated': stage['total_donated'],
                'donation_count': int(stage['total_donated'] / 25),  # Assume €25 avg donation
                'onlus_diversity': min(int(stage['total_donated'] / 100), 5)
            }

            # Filter stories that should be unlocked at this level
            available_stories = []
            for story_doc in story_docs:
                story = ImpactStory.from_dict(story_doc)
                is_unlocked = story.check_unlock_status(user_stats)

                story_response = story.to_response_dict(
                    user_stats=user_stats,
                    include_content=is_unlocked
                )
                available_stories.append(story_response)

            # Mock repository response
            mock_db_collections['impact_stories'].find.return_value.sort.return_value.limit.return_value = story_docs

            # Create mock cursor
            mock_cursor = Mock()
            mock_cursor.__iter__ = Mock(return_value=iter(story_docs))
            mock_db_collections['impact_stories'].find.return_value.sort.return_value.limit.return_value = mock_cursor

            with patch.object(story_service, '_get_user_statistics', return_value=user_stats):
                success, message, result = story_service.get_available_stories(
                    user_id, include_locked=False
                )

            assert success is True
            assert "STORIES_RETRIEVED_SUCCESS" in message

            # Count unlocked stories
            unlocked_count = sum(1 for story in available_stories if story['is_unlocked'])
            assert unlocked_count == stage['expected_unlocks']

    def test_community_impact_aggregation_workflow(self, integrated_services, mock_db_collections):
        """Test community impact data aggregation across multiple sources"""
        # Mock aggregated community data from different sources
        community_service = integrated_services['community_impact']

        # Mock donation aggregation results
        donations_aggregate = [
            {
                '_id': None,
                'total_donations': 50000.0,
                'total_count': 500,
                'avg_donation': 100.0
            }
        ]

        # Mock user statistics aggregation
        users_aggregate = [
            {
                '_id': None,
                'total_users': 350,
                'active_users': 280,
                'new_users_this_month': 45
            }
        ]

        # Mock ONLUS metrics aggregation
        onlus_aggregate = [
            {
                '_id': None,
                'active_onlus_count': 25,
                'total_impact_metrics': 150
            }
        ]

        # Configure aggregation pipeline responses
        mock_db_collections['community_reports'].aggregate.side_effect = [
            donations_aggregate,
            users_aggregate,
            onlus_aggregate
        ]

        # Generate real-time community snapshot
        success, message, result = community_service.generate_real_time_report('real_time_snapshot')

        assert success is True
        assert "REAL_TIME_REPORT_GENERATED" in message
        assert result is not None
        assert 'report' in result

        # Verify aggregated data structure
        report = result['report']
        assert 'timestamp' in report
        assert 'platform_totals' in report
        assert report['platform_totals']['total_donations'] == 50000.0

    def test_dashboard_data_integration(self, integrated_services, mock_db_collections):
        """Test dashboard data aggregation from multiple services"""
        user_id = str(ObjectId())
        visualization_service = integrated_services['impact_visualization']

        # Mock user impact summary
        mock_user_summary = {
            'total_donated': 350.0,
            'impact_score': 185.0,
            'unlocked_stories_count': 4,
            'current_level': 3
        }

        # Mock featured stories
        featured_story_docs = [
            {
                '_id': ObjectId(),
                'onlus_id': str(ObjectId()),
                'title': 'Featured Impact Story',
                'content': 'Amazing impact content...',
                'story_type': StoryType.FEATURED.value,
                'unlock_condition_type': UnlockConditionType.TOTAL_DONATED.value,
                'unlock_condition_value': 50.0,
                'category': 'education',
                'priority': 10,
                'featured_until': None,  # Permanently featured
                'is_active': True,
                'created_at': datetime.now(timezone.utc)
            }
        ]

        # Mock community highlights
        mock_community_highlights = {
            'total_platform_donated': 150000.0,
            'active_users_count': 500,
            'recent_milestones': [
                'Platform reached €150,000 in donations!',
                '500 active users milestone achieved'
            ]
        }

        # Configure mocks
        mock_cursor = Mock()
        mock_cursor.__iter__ = Mock(return_value=iter(featured_story_docs))
        mock_db_collections['impact_stories'].find.return_value.sort.return_value.limit.return_value = mock_cursor

        with patch.object(visualization_service, '_get_user_dashboard_summary', return_value=mock_user_summary):
            with patch.object(visualization_service, '_get_community_highlights', return_value=mock_community_highlights):

                success, message, result = visualization_service.get_dashboard_data(user_id)

        assert success is True
        assert "DASHBOARD_DATA_SUCCESS" in message
        assert result is not None

        # Verify integrated dashboard structure
        assert 'user_summary' in result
        assert 'featured_stories' in result
        assert 'community_highlights' in result

        assert result['user_summary']['total_donated'] == 350.0
        assert len(result['featured_stories']) == 1
        assert result['community_highlights']['total_platform_donated'] == 150000.0

    def test_onlus_impact_visualization_integration(self, integrated_services, mock_db_collections):
        """Test ONLUS impact visualization with metrics and updates"""
        onlus_id = str(ObjectId())
        visualization_service = integrated_services['impact_visualization']

        # Mock impact metrics for the ONLUS
        metric_docs = [
            {
                '_id': ObjectId(),
                'onlus_id': onlus_id,
                'metric_name': 'children_helped',
                'metric_type': MetricType.CUMULATIVE.value,
                'current_value': 250,
                'unit': MetricUnit.COUNT.value,
                'previous_value': 200,
                'related_donations_amount': 5000.0,
                'collection_date': datetime.now(timezone.utc),
                'is_active': True
            },
            {
                '_id': ObjectId(),
                'onlus_id': onlus_id,
                'metric_name': 'schools_built',
                'metric_type': MetricType.CUMULATIVE.value,
                'current_value': 5,
                'unit': MetricUnit.COUNT.value,
                'previous_value': 4,
                'related_donations_amount': 15000.0,
                'collection_date': datetime.now(timezone.utc),
                'is_active': True
            }
        ]

        # Mock recent updates for the ONLUS
        update_docs = [
            {
                '_id': ObjectId(),
                'onlus_id': onlus_id,
                'title': 'New School Construction Completed',
                'content': 'We are thrilled to announce the completion of our 5th school...',
                'update_type': UpdateType.MILESTONE.value,
                'priority': UpdatePriority.HIGH.value,
                'status': 'published',
                'engagement_metrics': {
                    'views': 450,
                    'likes': 35,
                    'shares': 8,
                    'comments': 12
                },
                'created_at': datetime.now(timezone.utc) - timedelta(days=2)
            }
        ]

        # Configure mock cursors
        metric_cursor = Mock()
        metric_cursor.__iter__ = Mock(return_value=iter(metric_docs))
        mock_db_collections['impact_metrics'].find.return_value.sort.return_value.limit.return_value = metric_cursor

        update_cursor = Mock()
        update_cursor.__iter__ = Mock(return_value=iter(update_docs))
        mock_db_collections['impact_updates'].find.return_value.sort.return_value.limit.return_value = update_cursor

        # Mock trend calculation
        with patch.object(visualization_service, '_calculate_impact_trends', return_value={
            'children_helped': {
                'trend': 'increasing',
                'growth_rate': 25.0,
                'data_points': [
                    {'date': '2024-09-01', 'value': 200},
                    {'date': '2024-09-15', 'value': 225},
                    {'date': '2024-09-30', 'value': 250}
                ]
            }
        }):
            success, message, result = visualization_service.get_onlus_impact_visualization(
                onlus_id, period='month', include_trends=True
            )

        assert success is True
        assert "ONLUS_VISUALIZATION_SUCCESS" in message
        assert result is not None

        # Verify integrated visualization data
        assert result['onlus_id'] == onlus_id
        assert len(result['metrics']) == 2
        assert len(result['recent_updates']) == 1

        # Verify metric calculations
        children_metric = next(m for m in result['metrics'] if m['metric_name'] == 'children_helped')
        assert children_metric['efficiency_ratio'] == 0.05  # 250/5000 = 0.05

        # Verify update engagement
        update = result['recent_updates'][0]
        assert update['engagement_metrics']['views'] == 450

    def test_error_cascade_handling(self, integrated_services, mock_db_collections):
        """Test error handling when one component fails in the integration"""
        user_id = str(ObjectId())
        impact_service = integrated_services['impact_tracking']

        # Simulate database connection failure
        mock_db_collections['impact_metrics'].find.side_effect = Exception("Database connection failed")

        with patch.object(impact_service, '_get_user_statistics', return_value={'total_donated': 100.0}):
            success, message, result = impact_service.get_user_impact_summary(user_id)

        # Should handle the error gracefully
        assert success is False
        assert "error" in message.lower() or "failed" in message.lower()
        assert result is None

    def test_concurrent_story_unlock_handling(self, integrated_services, mock_db_collections):
        """Test handling concurrent story unlocks from multiple donations"""
        user_id = str(ObjectId())
        story_service = integrated_services['story_unlocking']

        # Simulate rapid progression through multiple milestones
        final_user_stats = {
            'total_donated': 250.0,  # Jumped from €75 to €250 in one donation
            'donation_count': 4,
            'onlus_diversity': 3
        }

        # Stories that should all unlock at once
        story_docs = [
            {
                '_id': ObjectId(),
                'title': 'First Milestone',
                'unlock_condition_value': 100.0,
                'story_type': StoryType.MILESTONE.value,
                'unlock_condition_type': UnlockConditionType.TOTAL_DONATED.value,
                'is_active': True
            },
            {
                '_id': ObjectId(),
                'title': 'Second Milestone',
                'unlock_condition_value': 200.0,
                'story_type': StoryType.MILESTONE.value,
                'unlock_condition_type': UnlockConditionType.TOTAL_DONATED.value,
                'is_active': True
            },
            {
                '_id': ObjectId(),
                'title': 'Third Milestone',
                'unlock_condition_value': 250.0,
                'story_type': StoryType.MILESTONE.value,
                'unlock_condition_type': UnlockConditionType.TOTAL_DONATED.value,
                'is_active': True
            }
        ]

        # Mock the range query for unlockable stories
        mock_cursor = Mock()
        mock_cursor.__iter__ = Mock(return_value=iter(story_docs))
        mock_db_collections['impact_stories'].find.return_value.sort.return_value.limit.return_value = mock_cursor

        with patch.object(story_service, '_log_story_unlock', return_value=True):
            unlocked_stories = story_service.check_and_unlock_stories(user_id, 250.0)

        # Should unlock all three stories
        assert len(unlocked_stories) == 3
        assert all(story['just_unlocked'] for story in unlocked_stories)


if __name__ == '__main__':
    pytest.main([__file__])