from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from bson import ObjectId
from app.core.repositories.base_repository import BaseRepository
from app.donations.models.impact_metric import ImpactMetric, MetricType, MetricUnit, MetricPeriod


class ImpactMetricRepository(BaseRepository):
    """
    Repository for managing impact metrics in MongoDB.

    Handles CRUD operations and time-series aggregations for
    impact metrics from ONLUS organizations.
    """

    def __init__(self):
        super().__init__('impact_metrics')

    def create_indexes(self):
        """Create database indexes for optimal query performance."""
        import os
        if self.collection is None or os.getenv('TESTING') == 'true':
            return

        # Compound indexes for common queries
        self.collection.create_index([
            ('onlus_id', 1),
            ('metric_type', 1),
            ('period_type', 1)
        ])

        self.collection.create_index([
            ('onlus_id', 1),
            ('metric_name', 1),
            ('period_start', -1)
        ])

        self.collection.create_index([
            ('metric_type', 1),
            ('verification_status', 1),
            ('updated_at', -1)
        ])

        self.collection.create_index([
            ('period_start', 1),
            ('period_end', 1)
        ])

        # Index for trend analysis
        self.collection.create_index([
            ('onlus_id', 1),
            ('metric_name', 1),
            ('updated_at', -1)
        ])

        # Text index for search
        self.collection.create_index([
            ('metric_name', 'text'),
            ('description', 'text'),
            ('tags', 'text')
        ])

    def create_metric(self, metric_data: Dict[str, Any]) -> ImpactMetric:
        """
        Create a new impact metric.

        Args:
            metric_data: Metric data dictionary

        Returns:
            ImpactMetric: Created metric instance

        Raises:
            ValueError: If validation fails
            Exception: If database operation fails
        """
        # Validate metric data
        validation_error = ImpactMetric.validate_metric_data(metric_data)
        if validation_error:
            raise ValueError(validation_error)

        # Create metric instance
        metric = ImpactMetric.from_dict(metric_data)

        # Insert into database
        result = self.collection.insert_one(metric.to_dict())
        metric._id = result.inserted_id

        return metric

    def get_metric_by_id(self, metric_id: str) -> Optional[ImpactMetric]:
        """
        Get metric by ID.

        Args:
            metric_id: Metric ID

        Returns:
            ImpactMetric: Metric instance or None if not found
        """
        try:
            object_id = ObjectId(metric_id)
        except:
            return None

        document = self.collection.find_one({'_id': object_id})
        if document:
            return ImpactMetric.from_dict(document)
        return None

    def get_metrics_by_onlus(self, onlus_id: str,
                           metric_type: str = None,
                           period_type: str = None,
                           verified_only: bool = False,
                           limit: int = 50) -> List[ImpactMetric]:
        """
        Get metrics for a specific ONLUS.

        Args:
            onlus_id: ONLUS ID
            metric_type: Filter by metric type
            period_type: Filter by period type
            verified_only: Only return verified metrics
            limit: Maximum number of metrics

        Returns:
            List[ImpactMetric]: List of metrics
        """
        query = {'onlus_id': onlus_id}

        if metric_type:
            query['metric_type'] = metric_type

        if period_type:
            query['period_type'] = period_type

        if verified_only:
            query['verification_status'] = 'verified'

        cursor = self.collection.find(query).sort([
            ('metric_type', 1),
            ('updated_at', -1)
        ]).limit(limit)

        return [ImpactMetric.from_dict(doc) for doc in cursor]

    def get_latest_metrics_by_onlus(self, onlus_id: str) -> List[ImpactMetric]:
        """
        Get the latest version of each metric for an ONLUS.

        Args:
            onlus_id: ONLUS ID

        Returns:
            List[ImpactMetric]: Latest metrics
        """
        pipeline = [
            {'$match': {'onlus_id': onlus_id}},
            {'$sort': {'updated_at': -1}},
            {'$group': {
                '_id': {
                    'metric_name': '$metric_name',
                    'metric_type': '$metric_type'
                },
                'latest_metric': {'$first': '$$ROOT'}
            }},
            {'$replaceRoot': {'newRoot': '$latest_metric'}},
            {'$sort': {'metric_type': 1, 'metric_name': 1}}
        ]

        results = list(self.collection.aggregate(pipeline))
        return [ImpactMetric.from_dict(doc) for doc in results]

    def get_aggregated_metrics_by_type(self, metric_type: str,
                                     start_date: datetime = None,
                                     end_date: datetime = None) -> Dict[str, Any]:
        """
        Get aggregated metrics by type across all ONLUS.

        Args:
            metric_type: Type of metric to aggregate
            start_date: Start date for filtering
            end_date: End date for filtering

        Returns:
            Dict: Aggregated metric data
        """
        match_stage = {'metric_type': metric_type}

        if start_date or end_date:
            date_filter = {}
            if start_date:
                date_filter['$gte'] = start_date
            if end_date:
                date_filter['$lte'] = end_date
            match_stage['updated_at'] = date_filter

        pipeline = [
            {'$match': match_stage},
            {'$group': {
                '_id': '$metric_unit',
                'total_value': {'$sum': '$current_value'},
                'avg_value': {'$avg': '$current_value'},
                'min_value': {'$min': '$current_value'},
                'max_value': {'$max': '$current_value'},
                'count': {'$sum': 1},
                'onlus_count': {'$addToSet': '$onlus_id'},
                'verified_count': {
                    '$sum': {
                        '$cond': [{'$eq': ['$verification_status', 'verified']}, 1, 0]
                    }
                }
            }},
            {'$addFields': {
                'onlus_count': {'$size': '$onlus_count'}
            }}
        ]

        results = list(self.collection.aggregate(pipeline))

        aggregated = {}
        for result in results:
            unit = result['_id']
            aggregated[unit] = {
                'total_value': result['total_value'],
                'avg_value': round(result['avg_value'], 2),
                'min_value': result['min_value'],
                'max_value': result['max_value'],
                'metric_count': result['count'],
                'onlus_count': result['onlus_count'],
                'verified_count': result['verified_count'],
                'verification_rate': round(result['verified_count'] / result['count'] * 100, 1)
            }

        return {
            'metric_type': metric_type,
            'aggregated_by_unit': aggregated,
            'query_period': {
                'start_date': start_date.isoformat() if start_date else None,
                'end_date': end_date.isoformat() if end_date else None
            }
        }

    def get_metric_trends(self, onlus_id: str, metric_name: str,
                         days: int = 30) -> Dict[str, Any]:
        """
        Get trend data for a specific metric.

        Args:
            onlus_id: ONLUS ID
            metric_name: Name of the metric
            days: Number of days to look back

        Returns:
            Dict: Trend analysis data
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

        pipeline = [
            {
                '$match': {
                    'onlus_id': onlus_id,
                    'metric_name': metric_name,
                    'updated_at': {'$gte': cutoff_date}
                }
            },
            {
                '$sort': {'updated_at': 1}
            },
            {
                '$group': {
                    '_id': None,
                    'data_points': {
                        '$push': {
                            'date': '$updated_at',
                            'value': '$current_value',
                            'verification_status': '$verification_status'
                        }
                    },
                    'first_value': {'$first': '$current_value'},
                    'last_value': {'$last': '$current_value'},
                    'avg_value': {'$avg': '$current_value'},
                    'min_value': {'$min': '$current_value'},
                    'max_value': {'$max': '$current_value'},
                    'count': {'$sum': 1}
                }
            }
        ]

        result = list(self.collection.aggregate(pipeline))

        if not result:
            return {
                'onlus_id': onlus_id,
                'metric_name': metric_name,
                'trend': 'no_data',
                'data_points': [],
                'change_value': 0,
                'change_percentage': 0,
                'period_days': days
            }

        data = result[0]

        # Calculate trend
        first_value = data['first_value']
        last_value = data['last_value']
        change_value = last_value - first_value
        change_percentage = (change_value / first_value * 100) if first_value > 0 else 0

        if change_value > 0:
            trend = 'increasing'
        elif change_value < 0:
            trend = 'decreasing'
        else:
            trend = 'stable'

        return {
            'onlus_id': onlus_id,
            'metric_name': metric_name,
            'trend': trend,
            'change_value': round(change_value, 2),
            'change_percentage': round(change_percentage, 2),
            'statistics': {
                'avg_value': round(data['avg_value'], 2),
                'min_value': data['min_value'],
                'max_value': data['max_value'],
                'data_points_count': data['count']
            },
            'data_points': [
                {
                    'date': point['date'].isoformat(),
                    'value': point['value'],
                    'verification_status': point['verification_status']
                }
                for point in data['data_points']
            ],
            'period_days': days
        }

    def update_metric_value(self, metric_id: str, new_value: float,
                          source: str = None) -> bool:
        """
        Update a metric value and add to history.

        Args:
            metric_id: Metric ID
            new_value: New metric value
            source: Source of the update

        Returns:
            bool: True if update successful
        """
        # Get existing metric
        metric = self.get_metric_by_id(metric_id)
        if not metric:
            return False

        # Update the metric
        metric.update_value(new_value, source)

        # Save to database
        return self.update_metric(metric_id, metric.to_dict())

    def update_metric(self, metric_id: str, update_data: Dict[str, Any]) -> bool:
        """
        Update a metric.

        Args:
            metric_id: Metric ID
            update_data: Fields to update

        Returns:
            bool: True if update successful
        """
        try:
            object_id = ObjectId(metric_id)
        except:
            return False

        # Add updated timestamp
        update_data['updated_at'] = datetime.now(timezone.utc)

        result = self.collection.update_one(
            {'_id': object_id},
            {'$set': update_data}
        )

        return result.modified_count > 0

    def verify_metric(self, metric_id: str, verified_by: str = None) -> bool:
        """
        Mark a metric as verified.

        Args:
            metric_id: Metric ID
            verified_by: Who verified the metric

        Returns:
            bool: True if successful
        """
        update_data = {
            'verification_status': 'verified',
            'last_verified': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc)
        }

        if verified_by:
            if 'metadata' not in update_data:
                update_data['metadata'] = {}
            update_data['metadata.verified_by'] = verified_by

        return self.update_metric(metric_id, update_data)

    def dispute_metric(self, metric_id: str, reason: str = None) -> bool:
        """
        Mark a metric as disputed.

        Args:
            metric_id: Metric ID
            reason: Reason for dispute

        Returns:
            bool: True if successful
        """
        update_data = {
            'verification_status': 'disputed',
            'updated_at': datetime.now(timezone.utc)
        }

        if reason:
            if 'metadata' not in update_data:
                update_data['metadata'] = {}
            update_data['metadata.dispute_reason'] = reason

        return self.update_metric(metric_id, update_data)

    def get_stale_metrics(self, max_age_days: int = 30) -> List[ImpactMetric]:
        """
        Get metrics that haven't been updated recently.

        Args:
            max_age_days: Maximum age in days

        Returns:
            List[ImpactMetric]: Stale metrics
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=max_age_days)

        cursor = self.collection.find({
            'updated_at': {'$lt': cutoff_date}
        }).sort('updated_at', 1)

        return [ImpactMetric.from_dict(doc) for doc in cursor]

    def add_donation_contribution(self, metric_id: str,
                                donation_amount: float) -> bool:
        """
        Add a donation contribution to a metric.

        Args:
            metric_id: Metric ID
            donation_amount: Donation amount

        Returns:
            bool: True if successful
        """
        try:
            object_id = ObjectId(metric_id)
        except:
            return False

        result = self.collection.update_one(
            {'_id': object_id},
            {
                '$inc': {
                    'related_donations_count': 1,
                    'related_donations_amount': donation_amount
                },
                '$set': {
                    'updated_at': datetime.now(timezone.utc)
                }
            }
        )

        return result.modified_count > 0

    def get_top_performing_metrics(self, metric_type: str = None,
                                 limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get top performing metrics by efficiency ratio.

        Args:
            metric_type: Filter by metric type
            limit: Maximum number of metrics

        Returns:
            List[Dict]: Top performing metrics with efficiency data
        """
        match_stage = {
            'related_donations_amount': {'$gt': 0},
            'verification_status': 'verified'
        }

        if metric_type:
            match_stage['metric_type'] = metric_type

        pipeline = [
            {'$match': match_stage},
            {
                '$addFields': {
                    'efficiency_ratio': {
                        '$divide': ['$current_value', '$related_donations_amount']
                    }
                }
            },
            {'$sort': {'efficiency_ratio': -1}},
            {'$limit': limit}
        ]

        results = list(self.collection.aggregate(pipeline))

        return [
            {
                'metric_id': str(doc['_id']),
                'onlus_id': doc['onlus_id'],
                'metric_name': doc['metric_name'],
                'metric_type': doc['metric_type'],
                'current_value': doc['current_value'],
                'related_donations_amount': doc['related_donations_amount'],
                'efficiency_ratio': round(doc['efficiency_ratio'], 4),
                'formatted_value': ImpactMetric.from_dict(doc).get_formatted_value()
            }
            for doc in results
        ]

    def get_metrics_summary_by_onlus(self, onlus_id: str) -> Dict[str, Any]:
        """
        Get summary of all metrics for an ONLUS.

        Args:
            onlus_id: ONLUS ID

        Returns:
            Dict: Metrics summary
        """
        pipeline = [
            {'$match': {'onlus_id': onlus_id}},
            {
                '$group': {
                    '_id': '$metric_type',
                    'metrics_count': {'$sum': 1},
                    'total_value': {'$sum': '$current_value'},
                    'avg_value': {'$avg': '$current_value'},
                    'verified_count': {
                        '$sum': {
                            '$cond': [{'$eq': ['$verification_status', 'verified']}, 1, 0]
                        }
                    },
                    'total_donations_amount': {'$sum': '$related_donations_amount'},
                    'latest_update': {'$max': '$updated_at'},
                    'metrics': {
                        '$push': {
                            'metric_id': {'$toString': '$_id'},
                            'metric_name': '$metric_name',
                            'current_value': '$current_value',
                            'metric_unit': '$metric_unit',
                            'verification_status': '$verification_status'
                        }
                    }
                }
            },
            {'$sort': {'_id': 1}}
        ]

        results = list(self.collection.aggregate(pipeline))

        summary = {}
        total_metrics = 0
        total_verified = 0
        total_donations = 0.0

        for result in results:
            metric_type = result['_id']
            metrics_count = result['metrics_count']
            verified_count = result['verified_count']

            summary[metric_type] = {
                'metrics_count': metrics_count,
                'verified_count': verified_count,
                'verification_rate': round(verified_count / metrics_count * 100, 1),
                'total_value': result['total_value'],
                'avg_value': round(result['avg_value'], 2),
                'total_donations_amount': result['total_donations_amount'],
                'latest_update': result['latest_update'].isoformat() if result['latest_update'] else None,
                'metrics': result['metrics']
            }

            total_metrics += metrics_count
            total_verified += verified_count
            total_donations += result['total_donations_amount']

        return {
            'onlus_id': onlus_id,
            'summary_by_type': summary,
            'totals': {
                'total_metrics': total_metrics,
                'total_verified': total_verified,
                'overall_verification_rate': round(total_verified / total_metrics * 100, 1) if total_metrics > 0 else 0,
                'total_donations_amount': total_donations
            }
        }

    def search_metrics(self, query_text: str,
                      metric_type: str = None,
                      verified_only: bool = False,
                      limit: int = 20) -> List[ImpactMetric]:
        """
        Search metrics by text query.

        Args:
            query_text: Text to search for
            metric_type: Filter by metric type
            verified_only: Only return verified metrics
            limit: Maximum number of results

        Returns:
            List[ImpactMetric]: Matching metrics
        """
        search_query = {
            '$text': {'$search': query_text}
        }

        if metric_type:
            search_query['metric_type'] = metric_type

        if verified_only:
            search_query['verification_status'] = 'verified'

        cursor = self.collection.find(
            search_query,
            {'score': {'$meta': 'textScore'}}
        ).sort([
            ('score', {'$meta': 'textScore'}),
            ('updated_at', -1)
        ]).limit(limit)

        return [ImpactMetric.from_dict(doc) for doc in cursor]

    def delete_metric(self, metric_id: str) -> bool:
        """
        Delete a metric permanently.

        Args:
            metric_id: Metric ID

        Returns:
            bool: True if deletion successful
        """
        try:
            object_id = ObjectId(metric_id)
        except:
            return False

        result = self.collection.delete_one({'_id': object_id})
        return result.deleted_count > 0