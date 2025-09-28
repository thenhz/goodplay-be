from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from bson import ObjectId
from app.core.repositories.base_repository import BaseRepository
from app.donations.models.impact_story import ImpactStory, StoryType, UnlockConditionType, StoryStatus


class ImpactStoryRepository(BaseRepository):
    """
    Repository for managing impact stories in MongoDB.

    Handles CRUD operations and specialized queries for progressive
    story unlocking and user engagement.
    """

    def __init__(self):
        super().__init__('impact_stories')

    def create_indexes(self):
        """Create database indexes for optimal query performance."""
        import os
        if self.collection is None or os.getenv('TESTING') == 'true':
            return

        # Compound indexes for common queries
        self.collection.create_index([
            ('onlus_id', 1),
            ('is_active', 1),
            ('story_type', 1)
        ])

        self.collection.create_index([
            ('unlock_condition_type', 1),
            ('unlock_condition_value', 1),
            ('is_active', 1)
        ])

        self.collection.create_index([
            ('category', 1),
            ('is_active', 1),
            ('priority', -1)
        ])

        self.collection.create_index([
            ('featured_until', 1),
            ('is_active', 1)
        ])

        # Text index for search
        self.collection.create_index([
            ('title', 'text'),
            ('content', 'text'),
            ('tags', 'text')
        ])

    def create_story(self, story_data: Dict[str, Any]) -> ImpactStory:
        """
        Create a new impact story.

        Args:
            story_data: Story data dictionary

        Returns:
            ImpactStory: Created story instance

        Raises:
            ValueError: If validation fails
            Exception: If database operation fails
        """
        # Validate story data
        validation_error = ImpactStory.validate_story_data(story_data)
        if validation_error:
            raise ValueError(validation_error)

        # Create story instance
        story = ImpactStory.from_dict(story_data)

        # Insert into database
        result = self.collection.insert_one(story.to_dict())
        story._id = result.inserted_id

        return story

    def get_story_by_id(self, story_id: str) -> Optional[ImpactStory]:
        """
        Get story by ID.

        Args:
            story_id: Story ID

        Returns:
            ImpactStory: Story instance or None if not found
        """
        try:
            object_id = ObjectId(story_id)
        except:
            return None

        document = self.collection.find_one({'_id': object_id})
        if document:
            return ImpactStory.from_dict(document)
        return None

    def get_stories_for_user(self, user_stats: Dict[str, Any],
                           include_locked: bool = False,
                           category: str = None,
                           limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get stories available for a user based on their unlock status.

        Args:
            user_stats: User statistics for unlock checking
            include_locked: Whether to include locked stories
            category: Filter by category
            limit: Maximum number of stories to return

        Returns:
            List[Dict]: List of story dictionaries with unlock status
        """
        query = {'is_active': True}

        if category:
            query['category'] = category

        # Get all active stories
        cursor = self.collection.find(query).sort([
            ('priority', -1),
            ('featured_until', -1),
            ('created_at', -1)
        ]).limit(limit)

        stories_with_status = []
        for doc in cursor:
            story = ImpactStory.from_dict(doc)

            # Check unlock status
            is_unlocked = story.check_unlock_status(user_stats)

            # Include based on unlock status and user preference
            if is_unlocked or include_locked:
                story_dict = story.to_response_dict(
                    user_stats=user_stats,
                    include_content=is_unlocked  # Only include content if unlocked
                )
                stories_with_status.append(story_dict)

        return stories_with_status

    def get_stories_by_onlus(self, onlus_id: str,
                           is_active: bool = True,
                           limit: int = 20) -> List[ImpactStory]:
        """
        Get stories by ONLUS ID.

        Args:
            onlus_id: ONLUS ID
            is_active: Filter by active status
            limit: Maximum number of stories

        Returns:
            List[ImpactStory]: List of stories
        """
        query = {'onlus_id': onlus_id}
        if is_active is not None:
            query['is_active'] = is_active

        cursor = self.collection.find(query).sort([
            ('priority', -1),
            ('created_at', -1)
        ]).limit(limit)

        return [ImpactStory.from_dict(doc) for doc in cursor]

    def get_featured_stories(self, limit: int = 10) -> List[ImpactStory]:
        """
        Get currently featured stories.

        Args:
            limit: Maximum number of stories

        Returns:
            List[ImpactStory]: List of featured stories
        """
        now = datetime.now(timezone.utc)

        query = {
            'is_active': True,
            '$or': [
                {'featured_until': None},  # Permanently featured
                {'featured_until': {'$gt': now}}  # Featured until future date
            ]
        }

        cursor = self.collection.find(query).sort([
            ('priority', -1),
            ('created_at', -1)
        ]).limit(limit)

        return [ImpactStory.from_dict(doc) for doc in cursor]

    def get_stories_by_unlock_range(self, min_value: float, max_value: float,
                                  unlock_type: str = 'total_donated') -> List[ImpactStory]:
        """
        Get stories within a specific unlock value range.

        Args:
            min_value: Minimum unlock value
            max_value: Maximum unlock value
            unlock_type: Type of unlock condition

        Returns:
            List[ImpactStory]: Stories in the range
        """
        query = {
            'is_active': True,
            'unlock_condition_type': unlock_type,
            'unlock_condition_value': {
                '$gte': min_value,
                '$lte': max_value
            }
        }

        cursor = self.collection.find(query).sort([
            ('unlock_condition_value', 1),
            ('priority', -1)
        ])

        return [ImpactStory.from_dict(doc) for doc in cursor]

    def get_next_unlock_stories(self, user_stats: Dict[str, Any],
                              limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get the next stories the user can unlock.

        Args:
            user_stats: User statistics
            limit: Maximum number of stories

        Returns:
            List[Dict]: Next unlockable stories with progress
        """
        # Get user's current progress values
        total_donated = user_stats.get('total_donated', 0)
        donation_count = user_stats.get('donation_count', 0)
        onlus_diversity = user_stats.get('onlus_diversity', 0)
        impact_score = user_stats.get('impact_score', 0)

        # Find next stories for each unlock type
        next_stories = []

        # Next by total donated
        query = {
            'is_active': True,
            'unlock_condition_type': UnlockConditionType.TOTAL_DONATED.value,
            'unlock_condition_value': {'$gt': total_donated}
        }
        cursor = self.collection.find(query).sort('unlock_condition_value', 1).limit(2)
        for doc in cursor:
            story = ImpactStory.from_dict(doc)
            next_stories.append(story.to_response_dict(user_stats=user_stats, include_content=False))

        # Next by donation count
        query = {
            'is_active': True,
            'unlock_condition_type': UnlockConditionType.DONATION_COUNT.value,
            'unlock_condition_value': {'$gt': donation_count}
        }
        cursor = self.collection.find(query).sort('unlock_condition_value', 1).limit(2)
        for doc in cursor:
            story = ImpactStory.from_dict(doc)
            next_stories.append(story.to_response_dict(user_stats=user_stats, include_content=False))

        # Sort by progress percentage and return top results
        next_stories.sort(key=lambda x: x.get('unlock_progress', {}).get('progress_percent', 0), reverse=True)

        return next_stories[:limit]

    def search_stories(self, query_text: str,
                      category: str = None,
                      story_type: str = None,
                      limit: int = 20) -> List[ImpactStory]:
        """
        Search stories by text query.

        Args:
            query_text: Text to search for
            category: Filter by category
            story_type: Filter by story type
            limit: Maximum number of results

        Returns:
            List[ImpactStory]: Matching stories
        """
        search_query = {
            'is_active': True,
            '$text': {'$search': query_text}
        }

        if category:
            search_query['category'] = category

        if story_type:
            search_query['story_type'] = story_type

        cursor = self.collection.find(
            search_query,
            {'score': {'$meta': 'textScore'}}
        ).sort([
            ('score', {'$meta': 'textScore'}),
            ('priority', -1)
        ]).limit(limit)

        return [ImpactStory.from_dict(doc) for doc in cursor]

    def get_stories_by_category(self, category: str,
                              is_active: bool = True,
                              limit: int = 20) -> List[ImpactStory]:
        """
        Get stories by category.

        Args:
            category: Story category
            is_active: Filter by active status
            limit: Maximum number of stories

        Returns:
            List[ImpactStory]: Stories in category
        """
        query = {'category': category}
        if is_active is not None:
            query['is_active'] = is_active

        cursor = self.collection.find(query).sort([
            ('priority', -1),
            ('created_at', -1)
        ]).limit(limit)

        return [ImpactStory.from_dict(doc) for doc in cursor]

    def update_story(self, story_id: str, update_data: Dict[str, Any]) -> bool:
        """
        Update an existing story.

        Args:
            story_id: Story ID
            update_data: Fields to update

        Returns:
            bool: True if update successful
        """
        try:
            object_id = ObjectId(story_id)
        except:
            return False

        # Add updated timestamp
        update_data['updated_at'] = datetime.now(timezone.utc)

        result = self.collection.update_one(
            {'_id': object_id},
            {'$set': update_data}
        )

        return result.modified_count > 0

    def feature_story(self, story_id: str,
                     featured_until: datetime = None) -> bool:
        """
        Feature a story on the dashboard.

        Args:
            story_id: Story ID
            featured_until: When to stop featuring (None for permanent)

        Returns:
            bool: True if successful
        """
        update_data = {
            'featured_until': featured_until,
            'updated_at': datetime.now(timezone.utc)
        }

        return self.update_story(story_id, update_data)

    def unfeature_story(self, story_id: str) -> bool:
        """
        Remove featured status from a story.

        Args:
            story_id: Story ID

        Returns:
            bool: True if successful
        """
        update_data = {
            'featured_until': None,
            'updated_at': datetime.now(timezone.utc)
        }

        return self.update_story(story_id, update_data)

    def deactivate_story(self, story_id: str) -> bool:
        """
        Deactivate a story.

        Args:
            story_id: Story ID

        Returns:
            bool: True if successful
        """
        update_data = {
            'is_active': False,
            'updated_at': datetime.now(timezone.utc)
        }

        return self.update_story(story_id, update_data)

    def get_unlock_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about story unlocks.

        Returns:
            Dict: Unlock statistics
        """
        pipeline = [
            {'$match': {'is_active': True}},
            {'$group': {
                '_id': {
                    'unlock_type': '$unlock_condition_type',
                    'story_type': '$story_type'
                },
                'count': {'$sum': 1},
                'avg_unlock_value': {'$avg': '$unlock_condition_value'},
                'min_unlock_value': {'$min': '$unlock_condition_value'},
                'max_unlock_value': {'$max': '$unlock_condition_value'}
            }},
            {'$sort': {'_id.unlock_type': 1}}
        ]

        stats = {}
        for result in self.collection.aggregate(pipeline):
            unlock_type = result['_id']['unlock_type']
            story_type = result['_id']['story_type']

            if unlock_type not in stats:
                stats[unlock_type] = {}

            stats[unlock_type][story_type] = {
                'count': result['count'],
                'avg_unlock_value': round(result['avg_unlock_value'], 2),
                'min_unlock_value': result['min_unlock_value'],
                'max_unlock_value': result['max_unlock_value']
            }

        return stats

    def get_stories_with_pagination(self, page: int = 1, page_size: int = 20,
                                   filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Get stories with pagination.

        Args:
            page: Page number (1-based)
            page_size: Number of stories per page
            filters: Optional filters

        Returns:
            Dict: Paginated stories with metadata
        """
        # Build query
        query = filters or {}
        if 'is_active' not in query:
            query['is_active'] = True

        # Calculate skip value
        skip = (page - 1) * page_size

        # Get total count
        total_count = self.collection.count_documents(query)

        # Get stories
        cursor = self.collection.find(query).sort([
            ('priority', -1),
            ('created_at', -1)
        ]).skip(skip).limit(page_size)

        stories = [ImpactStory.from_dict(doc) for doc in cursor]

        # Calculate pagination metadata
        total_pages = (total_count + page_size - 1) // page_size

        return {
            'stories': [story.to_response_dict(include_content=False) for story in stories],
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total_count': total_count,
                'total_pages': total_pages,
                'has_next': page < total_pages,
                'has_prev': page > 1
            }
        }

    def delete_story(self, story_id: str) -> bool:
        """
        Delete a story permanently.

        Args:
            story_id: Story ID

        Returns:
            bool: True if deletion successful
        """
        try:
            object_id = ObjectId(story_id)
        except:
            return False

        result = self.collection.delete_one({'_id': object_id})
        return result.deleted_count > 0

    def get_story_engagement_metrics(self, story_id: str) -> Dict[str, Any]:
        """
        Get engagement metrics for a story.

        This would typically integrate with user activity tracking,
        but for now returns basic structure.

        Args:
            story_id: Story ID

        Returns:
            Dict: Engagement metrics
        """
        # This would be implemented with additional collections tracking user interactions
        return {
            'story_id': story_id,
            'view_count': 0,
            'unlock_count': 0,
            'share_count': 0,
            'engagement_score': 0.0
        }