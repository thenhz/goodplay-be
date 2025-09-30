import os
from typing import Optional, List, Dict, Any
from bson import ObjectId
from datetime import datetime, timezone, timedelta
from app.core.repositories.base_repository import BaseRepository
from app.admin.models.system_metric import SystemMetric, MetricType, MetricPeriod

class MetricsRepository(BaseRepository):
    def __init__(self):
        super().__init__("system_metrics")

    def create_indexes(self):
        if self.collection is None or os.getenv('TESTING') == 'true':
            return

        try:
            # Index for metric type filtering
            self.collection.create_index("metric_type")

            # Index for timestamp for time-based queries
            self.collection.create_index("timestamp")

            # Index for period filtering
            self.collection.create_index("period")

            # Compound index for metric type and timestamp
            self.collection.create_index([("metric_type", 1), ("timestamp", -1)])

            # Compound index for metric type, period, and timestamp
            self.collection.create_index([
                ("metric_type", 1),
                ("period", 1),
                ("timestamp", -1)
            ])

            # Index for tags for filtering
            self.collection.create_index("tags")

            # Index for source
            self.collection.create_index("source")

            # TTL index to automatically expire old metrics (30 days)
            self.collection.create_index("timestamp", expireAfterSeconds=2592000)  # 30 days

        except Exception as e:
            print(f"Warning: Could not create indexes for system_metrics: {str(e)}")

    def create_metric(self, metric: SystemMetric) -> str:
        """Create a new system metric"""
        metric_data = metric.to_dict()

        # Remove _id if None to let MongoDB generate it
        if metric_data.get('_id') is None:
            metric_data.pop('_id', None)

        return self.create(metric_data)

    def find_metric_by_id(self, metric_id: str) -> Optional[SystemMetric]:
        """Find metric by ID"""
        data = self.find_by_id(metric_id)
        if data:
            return SystemMetric.from_dict(data)
        return None

    def find_metrics_by_type(self, metric_type: str, period: str = None,
                           start_time: datetime = None, end_time: datetime = None,
                           limit: int = 100) -> List[SystemMetric]:
        """Find metrics by type with optional time range and period"""
        filter_dict = {"metric_type": metric_type}

        if period:
            filter_dict["period"] = period

        if start_time or end_time:
            time_filter = {}
            if start_time:
                time_filter["$gte"] = start_time
            if end_time:
                time_filter["$lte"] = end_time
            filter_dict["timestamp"] = time_filter

        data_list = self.find_many(filter_dict, limit=limit,
                                  sort=[("timestamp", -1)])
        return [SystemMetric.from_dict(data) for data in data_list]

    def find_latest_metric(self, metric_type: str, period: str = None) -> Optional[SystemMetric]:
        """Find the most recent metric of a specific type"""
        filter_dict = {"metric_type": metric_type}
        if period:
            filter_dict["period"] = period

        data_list = self.find_many(filter_dict, limit=1,
                                  sort=[("timestamp", -1)])
        if data_list:
            return SystemMetric.from_dict(data_list[0])
        return None

    def find_metrics_in_time_range(self, start_time: datetime, end_time: datetime,
                                  metric_types: List[str] = None,
                                  period: str = None, limit: int = 1000) -> List[SystemMetric]:
        """Find metrics within a time range"""
        filter_dict = {
            "timestamp": {
                "$gte": start_time,
                "$lte": end_time
            }
        }

        if metric_types:
            filter_dict["metric_type"] = {"$in": metric_types}

        if period:
            filter_dict["period"] = period

        data_list = self.find_many(filter_dict, limit=limit,
                                  sort=[("timestamp", -1)])
        return [SystemMetric.from_dict(data) for data in data_list]

    def find_metrics_by_tags(self, tags: Dict[str, str],
                           start_time: datetime = None, end_time: datetime = None,
                           limit: int = 100) -> List[SystemMetric]:
        """Find metrics by tags"""
        filter_dict = {}

        # Add tag filters
        for key, value in tags.items():
            filter_dict[f"tags.{key}"] = value

        if start_time or end_time:
            time_filter = {}
            if start_time:
                time_filter["$gte"] = start_time
            if end_time:
                time_filter["$lte"] = end_time
            filter_dict["timestamp"] = time_filter

        data_list = self.find_many(filter_dict, limit=limit,
                                  sort=[("timestamp", -1)])
        return [SystemMetric.from_dict(data) for data in data_list]

    def get_metric_aggregation(self, metric_type: str, field: str,
                             start_time: datetime, end_time: datetime,
                             aggregation: str = "avg") -> Optional[float]:
        """Get aggregated metric value (avg, sum, min, max, count)"""
        if not self.collection:
            return None

        try:
            pipeline = [
                {
                    "$match": {
                        "metric_type": metric_type,
                        "timestamp": {
                            "$gte": start_time,
                            "$lte": end_time
                        }
                    }
                }
            ]

            if aggregation == "avg":
                pipeline.append({
                    "$group": {
                        "_id": None,
                        "value": {"$avg": f"$data.{field}"}
                    }
                })
            elif aggregation == "sum":
                pipeline.append({
                    "$group": {
                        "_id": None,
                        "value": {"$sum": f"$data.{field}"}
                    }
                })
            elif aggregation == "min":
                pipeline.append({
                    "$group": {
                        "_id": None,
                        "value": {"$min": f"$data.{field}"}
                    }
                })
            elif aggregation == "max":
                pipeline.append({
                    "$group": {
                        "_id": None,
                        "value": {"$max": f"$data.{field}"}
                    }
                })
            elif aggregation == "count":
                pipeline.append({
                    "$count": "value"
                })

            result = list(self.collection.aggregate(pipeline))
            if result:
                return result[0].get("value")

        except Exception as e:
            print(f"Error in metric aggregation: {str(e)}")

        return None

    def get_time_series_data(self, metric_type: str, field: str,
                           start_time: datetime, end_time: datetime,
                           interval: str = "1h") -> List[Dict[str, Any]]:
        """Get time series data for charting"""
        if not self.collection:
            return []

        try:
            # Convert interval to MongoDB date format
            interval_mapping = {
                "1m": {"$minute": "$timestamp"},
                "5m": {"$subtract": [{"$minute": "$timestamp"}, {"$mod": [{"$minute": "$timestamp"}, 5]}]},
                "15m": {"$subtract": [{"$minute": "$timestamp"}, {"$mod": [{"$minute": "$timestamp"}, 15]}]},
                "1h": {"$hour": "$timestamp"},
                "1d": {"$dayOfYear": "$timestamp"}
            }

            if interval not in interval_mapping:
                interval = "1h"

            pipeline = [
                {
                    "$match": {
                        "metric_type": metric_type,
                        "timestamp": {
                            "$gte": start_time,
                            "$lte": end_time
                        }
                    }
                },
                {
                    "$group": {
                        "_id": {
                            "year": {"$year": "$timestamp"},
                            "month": {"$month": "$timestamp"},
                            "day": {"$dayOfMonth": "$timestamp"},
                            "interval": interval_mapping[interval]
                        },
                        "value": {"$avg": f"$data.{field}"},
                        "count": {"$sum": 1},
                        "timestamp": {"$first": "$timestamp"}
                    }
                },
                {
                    "$sort": {"timestamp": 1}
                }
            ]

            results = list(self.collection.aggregate(pipeline))
            return [
                {
                    "timestamp": result["timestamp"].isoformat(),
                    "value": result["value"],
                    "count": result["count"]
                }
                for result in results
            ]

        except Exception as e:
            print(f"Error getting time series data: {str(e)}")
            return []

    def get_metric_statistics(self, metric_type: str, field: str,
                            start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Get comprehensive statistics for a metric field"""
        if not self.collection:
            return {}

        try:
            pipeline = [
                {
                    "$match": {
                        "metric_type": metric_type,
                        "timestamp": {
                            "$gte": start_time,
                            "$lte": end_time
                        }
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "avg": {"$avg": f"$data.{field}"},
                        "min": {"$min": f"$data.{field}"},
                        "max": {"$max": f"$data.{field}"},
                        "count": {"$sum": 1},
                        "sum": {"$sum": f"$data.{field}"}
                    }
                }
            ]

            result = list(self.collection.aggregate(pipeline))
            if result:
                stats = result[0]
                stats.pop('_id', None)

                # Calculate additional statistics
                if stats['count'] > 0:
                    stats['median'] = self._calculate_median(metric_type, field, start_time, end_time)
                    stats['percentile_95'] = self._calculate_percentile(metric_type, field, start_time, end_time, 95)

                return stats

        except Exception as e:
            print(f"Error getting metric statistics: {str(e)}")

        return {}

    def _calculate_median(self, metric_type: str, field: str,
                         start_time: datetime, end_time: datetime) -> Optional[float]:
        """Calculate median value for a metric field"""
        try:
            pipeline = [
                {
                    "$match": {
                        "metric_type": metric_type,
                        "timestamp": {
                            "$gte": start_time,
                            "$lte": end_time
                        }
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "values": {"$push": f"$data.{field}"}
                    }
                },
                {
                    "$project": {
                        "median": {
                            "$let": {
                                "vars": {
                                    "sorted": {"$sortArray": {"input": "$values", "sortBy": 1}},
                                    "length": {"$size": "$values"}
                                },
                                "in": {
                                    "$cond": {
                                        "if": {"$eq": [{"$mod": ["$$length", 2]}, 0]},
                                        "then": {
                                            "$divide": [
                                                {"$add": [
                                                    {"$arrayElemAt": ["$$sorted", {"$subtract": [{"$divide": ["$$length", 2]}, 1]}]},
                                                    {"$arrayElemAt": ["$$sorted", {"$divide": ["$$length", 2]}]}
                                                ]},
                                                2
                                            ]
                                        },
                                        "else": {"$arrayElemAt": ["$$sorted", {"$floor": {"$divide": ["$$length", 2]}}]}
                                    }
                                }
                            }
                        }
                    }
                }
            ]

            result = list(self.collection.aggregate(pipeline))
            if result:
                return result[0].get("median")

        except Exception as e:
            print(f"Error calculating median: {str(e)}")

        return None

    def _calculate_percentile(self, metric_type: str, field: str,
                            start_time: datetime, end_time: datetime,
                            percentile: int) -> Optional[float]:
        """Calculate percentile value for a metric field"""
        try:
            pipeline = [
                {
                    "$match": {
                        "metric_type": metric_type,
                        "timestamp": {
                            "$gte": start_time,
                            "$lte": end_time
                        }
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "values": {"$push": f"$data.{field}"}
                    }
                },
                {
                    "$project": {
                        "percentile": {
                            "$let": {
                                "vars": {
                                    "sorted": {"$sortArray": {"input": "$values", "sortBy": 1}},
                                    "length": {"$size": "$values"},
                                    "index": {"$floor": {"$multiply": [{"$divide": [percentile, 100]}, {"$size": "$values"}]}}
                                },
                                "in": {"$arrayElemAt": ["$$sorted", "$$index"]}
                            }
                        }
                    }
                }
            ]

            result = list(self.collection.aggregate(pipeline))
            if result:
                return result[0].get("percentile")

        except Exception as e:
            print(f"Error calculating percentile: {str(e)}")

        return None

    def find_alert_worthy_metrics(self, hours: int = 1) -> List[SystemMetric]:
        """Find metrics that should trigger alerts"""
        start_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        end_time = datetime.now(timezone.utc)

        metrics = self.find_metrics_in_time_range(start_time, end_time)
        alert_metrics = []

        for metric in metrics:
            if metric.is_alert_worthy():
                alert_metrics.append(metric)

        return alert_metrics

    def cleanup_old_metrics(self, days: int = 30) -> int:
        """Clean up metrics older than specified days"""
        if not self.collection:
            return 0

        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(days=days)
            result = self.collection.delete_many({"timestamp": {"$lt": cutoff_time}})
            return result.deleted_count

        except Exception as e:
            print(f"Error cleaning up old metrics: {str(e)}")
            return 0

    def get_dashboard_metrics(self) -> Dict[str, Any]:
        """Get latest metrics for dashboard display"""
        now = datetime.now(timezone.utc)
        one_hour_ago = now - timedelta(hours=1)

        dashboard_data = {}

        # Performance metrics
        performance_metric = self.find_latest_metric(MetricType.PERFORMANCE.value)
        if performance_metric:
            dashboard_data['performance'] = performance_metric.data

        # User activity metrics
        user_activity_metric = self.find_latest_metric(MetricType.USER_ACTIVITY.value)
        if user_activity_metric:
            dashboard_data['user_activity'] = user_activity_metric.data

        # Financial metrics
        financial_metric = self.find_latest_metric(MetricType.FINANCIAL.value)
        if financial_metric:
            dashboard_data['financial'] = financial_metric.data

        # Security metrics
        security_metric = self.find_latest_metric(MetricType.SECURITY.value)
        if security_metric:
            dashboard_data['security'] = security_metric.data

        # Alert-worthy metrics
        alert_metrics = self.find_alert_worthy_metrics(hours=1)
        dashboard_data['alerts'] = [
            {
                'type': metric.metric_type,
                'message': metric.get_alert_message(),
                'timestamp': metric.timestamp.isoformat(),
                'data': metric.data
            }
            for metric in alert_metrics
        ]

        return dashboard_data