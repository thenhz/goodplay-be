from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from bson import ObjectId
from app.core.repositories.base_repository import BaseRepository
from app.donations.models.impact_update import ImpactUpdate, UpdateType, UpdatePriority, UpdateStatus


class ImpactUpdateRepository(BaseRepository):
    """
    Repository for managing impact updates in MongoDB.

    Handles CRUD operations and real-time feeds for
    ONLUS impact updates and notifications.
    """

    def __init__(self):
        super().__init__('impact_updates')

    def create_indexes(self):
        """Create database indexes for optimal query performance."""
        import os
        if self.collection is None or os.getenv('TESTING') == 'true':
            return

        # Compound indexes for common queries
        self.collection.create_index([
            ('onlus_id', 1),
            ('status', 1),
            ('published_at', -1)
        ])

        self.collection.create_index([
            ('status', 1),
            ('priority', -1),
            ('published_at', -1)
        ])

        self.collection.create_index([
            ('update_type', 1),
            ('status', 1),
            ('created_at', -1)
        ])

        self.collection.create_index([
            ('featured_until', 1),
            ('status', 1)
        ])

        # Index for auto-publishing
        self.collection.create_index([
            ('status', 1),
            ('publish_at', 1)
        ])

        # Index for engagement tracking
        self.collection.create_index([
            ('onlus_id', 1),
            ('published_at', -1)
        ])

        # Text index for search
        self.collection.create_index([
            ('title', 'text'),
            ('content', 'text'),
            ('tags', 'text')
        ])

    def create_update(self, update_data: Dict[str, Any]) -> ImpactUpdate:
        """
        Create a new impact update.

        Args:
            update_data: Update data dictionary

        Returns:
            ImpactUpdate: Created update instance

        Raises:
            ValueError: If validation fails
            Exception: If database operation fails
        """
        # Validate update data
        validation_error = ImpactUpdate.validate_update_data(update_data)
        if validation_error:
            raise ValueError(validation_error)

        # Create update instance
        update = ImpactUpdate.from_dict(update_data)

        # Insert into database
        result = self.collection.insert_one(update.to_dict())
        update._id = result.inserted_id

        return update

    def get_update_by_id(self, update_id: str) -> Optional[ImpactUpdate]:
        """
        Get update by ID.

        Args:
            update_id: Update ID

        Returns:
            ImpactUpdate: Update instance or None if not found
        """
        try:
            object_id = ObjectId(update_id)
        except:
            return None

        document = self.collection.find_one({'_id': object_id})
        if document:
            return ImpactUpdate.from_dict(document)
        return None

    def get_published_updates(self, page: int = 1, page_size: int = 20,
                            onlus_id: str = None,
                            update_type: str = None,
                            priority: str = None) -> Dict[str, Any]:
        """
        Get published updates with pagination.

        Args:
            page: Page number (1-based)
            page_size: Number of updates per page
            onlus_id: Filter by ONLUS ID
            update_type: Filter by update type
            priority: Filter by priority

        Returns:
            Dict: Paginated updates with metadata
        """
        # Build query for published updates
        query = {
            'status': {'$in': [UpdateStatus.PUBLISHED.value, UpdateStatus.FEATURED.value]}
        }

        if onlus_id:
            query['onlus_id'] = onlus_id

        if update_type:
            query['update_type'] = update_type

        if priority:
            query['priority'] = priority

        # Calculate skip value
        skip = (page - 1) * page_size

        # Get total count
        total_count = self.collection.count_documents(query)

        # Get updates
        cursor = self.collection.find(query).sort([
            ('priority', -1),  # Higher priority first
            ('published_at', -1)  # Most recent first
        ]).skip(skip).limit(page_size)

        updates = [ImpactUpdate.from_dict(doc) for doc in cursor]

        # Calculate pagination metadata
        total_pages = (total_count + page_size - 1) // page_size

        return {
            'updates': [update.to_response_dict() for update in updates],
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total_count': total_count,
                'total_pages': total_pages,
                'has_next': page < total_pages,
                'has_prev': page > 1
            }
        }

    def get_featured_updates(self, limit: int = 5) -> List[ImpactUpdate]:
        """
        Get currently featured updates.

        Args:
            limit: Maximum number of updates

        Returns:
            List[ImpactUpdate]: Featured updates
        """
        now = datetime.now(timezone.utc)

        query = {
            'status': UpdateStatus.FEATURED.value,
            '$or': [
                {'featured_until': None},  # Permanently featured
                {'featured_until': {'$gt': now}}  # Featured until future date
            ]
        }

        cursor = self.collection.find(query).sort([
            ('priority', -1),
            ('published_at', -1)
        ]).limit(limit)

        return [ImpactUpdate.from_dict(doc) for doc in cursor]

    def get_recent_updates_by_onlus(self, onlus_id: str,
                                  days: int = 7,
                                  limit: int = 10) -> List[ImpactUpdate]:
        """
        Get recent updates from a specific ONLUS.

        Args:
            onlus_id: ONLUS ID
            days: Number of days to look back
            limit: Maximum number of updates

        Returns:
            List[ImpactUpdate]: Recent updates
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

        query = {
            'onlus_id': onlus_id,
            'status': {'$in': [UpdateStatus.PUBLISHED.value, UpdateStatus.FEATURED.value]},
            'published_at': {'$gte': cutoff_date}
        }

        cursor = self.collection.find(query).sort([
            ('priority', -1),
            ('published_at', -1)
        ]).limit(limit)

        return [ImpactUpdate.from_dict(doc) for doc in cursor]

    def get_urgent_updates(self, limit: int = 10) -> List[ImpactUpdate]:
        """
        Get urgent and critical updates.

        Args:
            limit: Maximum number of updates

        Returns:
            List[ImpactUpdate]: Urgent updates
        """
        query = {
            'status': {'$in': [UpdateStatus.PUBLISHED.value, UpdateStatus.FEATURED.value]},
            'priority': {'$in': [UpdatePriority.URGENT.value, UpdatePriority.CRITICAL.value]}
        }

        cursor = self.collection.find(query).sort([
            ('priority', -1),
            ('published_at', -1)
        ]).limit(limit)

        return [ImpactUpdate.from_dict(doc) for doc in cursor]

    def get_updates_by_type(self, update_type: str,
                          limit: int = 20) -> List[ImpactUpdate]:
        """
        Get updates by type.

        Args:
            update_type: Type of updates
            limit: Maximum number of updates

        Returns:
            List[ImpactUpdate]: Updates of specified type
        """
        query = {
            'update_type': update_type,
            'status': {'$in': [UpdateStatus.PUBLISHED.value, UpdateStatus.FEATURED.value]}
        }

        cursor = self.collection.find(query).sort([
            ('priority', -1),
            ('published_at', -1)
        ]).limit(limit)

        return [ImpactUpdate.from_dict(doc) for doc in cursor]

    def get_updates_for_donation(self, donation_id: str) -> List[ImpactUpdate]:
        """
        Get updates related to a specific donation.

        Args:
            donation_id: Donation ID

        Returns:
            List[ImpactUpdate]: Related updates
        """
        query = {
            'affected_donation_ids': donation_id,
            'status': {'$in': [UpdateStatus.PUBLISHED.value, UpdateStatus.FEATURED.value]}
        }

        cursor = self.collection.find(query).sort('published_at', -1)

        return [ImpactUpdate.from_dict(doc) for doc in cursor]

    def get_scheduled_updates(self) -> List[ImpactUpdate]:
        """
        Get updates scheduled for auto-publishing.

        Returns:
            List[ImpactUpdate]: Updates ready to be published
        """
        now = datetime.now(timezone.utc)

        query = {
            'status': UpdateStatus.DRAFT.value,
            'publish_at': {'$lte': now}
        }

        cursor = self.collection.find(query).sort('publish_at', 1)

        return [ImpactUpdate.from_dict(doc) for doc in cursor]

    def publish_update(self, update_id: str) -> bool:
        """
        Publish a draft update.

        Args:
            update_id: Update ID

        Returns:
            bool: True if successful
        """
        try:
            object_id = ObjectId(update_id)
        except:
            return False

        update_data = {
            'status': UpdateStatus.PUBLISHED.value,
            'published_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc)
        }

        result = self.collection.update_one(
            {
                '_id': object_id,
                'status': UpdateStatus.DRAFT.value
            },
            {'$set': update_data}
        )

        return result.modified_count > 0

    def feature_update(self, update_id: str,
                      featured_until: datetime = None) -> bool:
        """
        Feature an update on the dashboard.

        Args:
            update_id: Update ID
            featured_until: When to stop featuring (None for permanent)

        Returns:
            bool: True if successful
        """
        try:
            object_id = ObjectId(update_id)
        except:
            return False

        update_data = {
            'status': UpdateStatus.FEATURED.value,
            'featured_until': featured_until,
            'updated_at': datetime.now(timezone.utc)
        }

        result = self.collection.update_one(
            {'_id': object_id},
            {'$set': update_data}
        )

        return result.modified_count > 0

    def unfeature_update(self, update_id: str) -> bool:
        """
        Remove featured status from an update.

        Args:
            update_id: Update ID

        Returns:
            bool: True if successful
        """
        try:
            object_id = ObjectId(update_id)
        except:
            return False

        update_data = {
            'status': UpdateStatus.PUBLISHED.value,
            'featured_until': None,
            'updated_at': datetime.now(timezone.utc)
        }

        result = self.collection.update_one(
            {
                '_id': object_id,
                'status': UpdateStatus.FEATURED.value
            },
            {'$set': update_data}
        )

        return result.modified_count > 0

    def archive_update(self, update_id: str) -> bool:
        """
        Archive an update.

        Args:
            update_id: Update ID

        Returns:
            bool: True if successful
        """
        try:
            object_id = ObjectId(update_id)
        except:
            return False

        update_data = {
            'status': UpdateStatus.ARCHIVED.value,
            'updated_at': datetime.now(timezone.utc)
        }

        result = self.collection.update_one(
            {'_id': object_id},
            {'$set': update_data}
        )

        return result.modified_count > 0

    def increment_view_count(self, update_id: str) -> bool:
        """
        Increment view count for an update.

        Args:
            update_id: Update ID

        Returns:
            bool: True if successful
        """
        try:
            object_id = ObjectId(update_id)
        except:
            return False

        result = self.collection.update_one(
            {'_id': object_id},
            {
                '$inc': {'metadata.view_count': 1},
                '$set': {'updated_at': datetime.now(timezone.utc)}
            }
        )

        return result.modified_count > 0

    def increment_engagement(self, update_id: str, action: str) -> bool:
        """
        Increment engagement metric for an update.

        Args:
            update_id: Update ID
            action: Engagement action (like, share, comment)

        Returns:
            bool: True if successful
        """
        if action not in ['like', 'share', 'comment']:
            return False

        try:
            object_id = ObjectId(update_id)
        except:
            return False

        field_name = f'metadata.{action}_count'

        result = self.collection.update_one(
            {'_id': object_id},
            {
                '$inc': {field_name: 1},
                '$set': {'updated_at': datetime.now(timezone.utc)}
            }
        )

        return result.modified_count > 0

    def add_related_metric(self, update_id: str, metric_id: str) -> bool:
        """
        Add a related metric to an update.

        Args:
            update_id: Update ID
            metric_id: Metric ID

        Returns:
            bool: True if successful
        """
        try:
            object_id = ObjectId(update_id)
        except:
            return False

        result = self.collection.update_one(
            {'_id': object_id},
            {
                '$addToSet': {'related_metric_ids': metric_id},
                '$set': {'updated_at': datetime.now(timezone.utc)}
            }
        )

        return result.modified_count > 0

    def add_affected_donation(self, update_id: str, donation_id: str) -> bool:
        """
        Add an affected donation to an update.

        Args:
            update_id: Update ID
            donation_id: Donation ID

        Returns:
            bool: True if successful
        """
        try:
            object_id = ObjectId(update_id)
        except:
            return False

        result = self.collection.update_one(
            {'_id': object_id},
            {
                '$addToSet': {'affected_donation_ids': donation_id},
                '$set': {'updated_at': datetime.now(timezone.utc)}
            }
        )

        return result.modified_count > 0

    def get_update_statistics_by_onlus(self, onlus_id: str) -> Dict[str, Any]:
        """
        Get update statistics for an ONLUS.

        Args:
            onlus_id: ONLUS ID

        Returns:
            Dict: Update statistics
        """
        pipeline = [
            {'$match': {'onlus_id': onlus_id}},
            {
                '$group': {
                    '_id': {
                        'status': '$status',
                        'update_type': '$update_type'
                    },
                    'count': {'$sum': 1},
                    'total_views': {'$sum': '$metadata.view_count'},
                    'total_likes': {'$sum': '$metadata.like_count'},
                    'total_shares': {'$sum': '$metadata.share_count'},
                    'avg_priority': {'$avg': {
                        '$switch': {
                            'branches': [
                                {'case': {'$eq': ['$priority', 'low']}, 'then': 1},
                                {'case': {'$eq': ['$priority', 'normal']}, 'then': 2},
                                {'case': {'$eq': ['$priority', 'high']}, 'then': 3},
                                {'case': {'$eq': ['$priority', 'urgent']}, 'then': 4},
                                {'case': {'$eq': ['$priority', 'critical']}, 'then': 5}
                            ],
                            'default': 2
                        }
                    }},
                    'latest_update': {'$max': '$updated_at'}
                }
            }
        ]

        results = list(self.collection.aggregate(pipeline))

        statistics = {}
        total_updates = 0
        total_engagement = 0

        for result in results:
            status = result['_id']['status']
            update_type = result['_id']['update_type']

            if status not in statistics:
                statistics[status] = {}

            engagement = (result['total_views'] or 0) + (result['total_likes'] or 0) + (result['total_shares'] or 0)

            statistics[status][update_type] = {
                'count': result['count'],
                'total_views': result['total_views'] or 0,
                'total_likes': result['total_likes'] or 0,
                'total_shares': result['total_shares'] or 0,
                'total_engagement': engagement,
                'avg_priority': round(result['avg_priority'], 1),
                'latest_update': result['latest_update'].isoformat() if result['latest_update'] else None
            }

            total_updates += result['count']
            total_engagement += engagement

        return {
            'onlus_id': onlus_id,
            'statistics_by_status': statistics,
            'totals': {
                'total_updates': total_updates,
                'total_engagement': total_engagement,
                'avg_engagement_per_update': round(total_engagement / total_updates, 2) if total_updates > 0 else 0
            }
        }

    def get_trending_updates(self, hours: int = 24, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get trending updates based on recent engagement.

        Args:
            hours: Number of hours to look back
            limit: Maximum number of updates

        Returns:
            List[Dict]: Trending updates with engagement metrics
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(hours=hours)

        pipeline = [
            {
                '$match': {
                    'status': {'$in': [UpdateStatus.PUBLISHED.value, UpdateStatus.FEATURED.value]},
                    'published_at': {'$gte': cutoff_date}
                }
            },
            {
                '$addFields': {
                    'engagement_score': {
                        '$add': [
                            {'$multiply': [{'$ifNull': ['$metadata.view_count', 0]}, 1]},
                            {'$multiply': [{'$ifNull': ['$metadata.like_count', 0]}, 3]},
                            {'$multiply': [{'$ifNull': ['$metadata.share_count', 0]}, 5]},
                            {'$multiply': [{'$ifNull': ['$metadata.comment_count', 0]}, 4]}
                        ]
                    },
                    'priority_score': {
                        '$switch': {
                            'branches': [
                                {'case': {'$eq': ['$priority', 'low']}, 'then': 1},
                                {'case': {'$eq': ['$priority', 'normal']}, 'then': 2},
                                {'case': {'$eq': ['$priority', 'high']}, 'then': 3},
                                {'case': {'$eq': ['$priority', 'urgent']}, 'then': 4},
                                {'case': {'$eq': ['$priority', 'critical']}, 'then': 5}
                            ],
                            'default': 2
                        }
                    }
                }
            },
            {
                '$addFields': {
                    'trending_score': {
                        '$multiply': ['$engagement_score', '$priority_score']
                    }
                }
            },
            {'$sort': {'trending_score': -1}},
            {'$limit': limit}
        ]

        results = list(self.collection.aggregate(pipeline))

        trending_updates = []
        for doc in results:
            update = ImpactUpdate.from_dict(doc)
            trending_data = update.to_response_dict()
            trending_data['trending_score'] = doc.get('trending_score', 0)
            trending_data['engagement_score'] = doc.get('engagement_score', 0)
            trending_updates.append(trending_data)

        return trending_updates

    def search_updates(self, query_text: str,
                      onlus_id: str = None,
                      update_type: str = None,
                      limit: int = 20) -> List[ImpactUpdate]:
        """
        Search updates by text query.

        Args:
            query_text: Text to search for
            onlus_id: Filter by ONLUS ID
            update_type: Filter by update type
            limit: Maximum number of results

        Returns:
            List[ImpactUpdate]: Matching updates
        """
        search_query = {
            'status': {'$in': [UpdateStatus.PUBLISHED.value, UpdateStatus.FEATURED.value]},
            '$text': {'$search': query_text}
        }

        if onlus_id:
            search_query['onlus_id'] = onlus_id

        if update_type:
            search_query['update_type'] = update_type

        cursor = self.collection.find(
            search_query,
            {'score': {'$meta': 'textScore'}}
        ).sort([
            ('score', {'$meta': 'textScore'}),
            ('priority', -1),
            ('published_at', -1)
        ]).limit(limit)

        return [ImpactUpdate.from_dict(doc) for doc in cursor]

    def update_update(self, update_id: str, update_data: Dict[str, Any]) -> bool:
        """
        Update an existing update.

        Args:
            update_id: Update ID
            update_data: Fields to update

        Returns:
            bool: True if update successful
        """
        try:
            object_id = ObjectId(update_id)
        except:
            return False

        # Add updated timestamp
        update_data['updated_at'] = datetime.now(timezone.utc)

        result = self.collection.update_one(
            {'_id': object_id},
            {'$set': update_data}
        )

        return result.modified_count > 0

    def delete_update(self, update_id: str) -> bool:
        """
        Delete an update permanently.

        Args:
            update_id: Update ID

        Returns:
            bool: True if deletion successful
        """
        try:
            object_id = ObjectId(update_id)
        except:
            return False

        result = self.collection.delete_one({'_id': object_id})
        return result.deleted_count > 0