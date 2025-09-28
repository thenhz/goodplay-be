from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from bson import ObjectId
from app.core.repositories.base_repository import BaseRepository
from app.donations.models.community_report import CommunityReport, ReportType, ReportStatus


class CommunityReportRepository(BaseRepository):
    """
    Repository for managing community reports in MongoDB.

    Handles CRUD operations and complex aggregations for
    platform-wide impact reporting and transparency.
    """

    def __init__(self):
        super().__init__('community_reports')

    def create_indexes(self):
        """Create database indexes for optimal query performance."""
        import os
        if self.collection is None or os.getenv('TESTING') == 'true':
            return

        # Compound indexes for common queries
        self.collection.create_index([
            ('report_type', 1),
            ('period_start', -1),
            ('status', 1)
        ])

        self.collection.create_index([
            ('period_start', 1),
            ('period_end', 1)
        ])

        self.collection.create_index([
            ('status', 1),
            ('created_at', -1)
        ])

        # Index for current period queries
        self.collection.create_index([
            ('report_type', 1),
            ('period_end', -1)
        ])

    def create_report(self, report_data: Dict[str, Any]) -> CommunityReport:
        """
        Create a new community report.

        Args:
            report_data: Report data dictionary

        Returns:
            CommunityReport: Created report instance

        Raises:
            ValueError: If validation fails
            Exception: If database operation fails
        """
        # Validate report data
        validation_error = CommunityReport.validate_report_data(report_data)
        if validation_error:
            raise ValueError(validation_error)

        # Create report instance
        report = CommunityReport.from_dict(report_data)

        # Insert into database
        result = self.collection.insert_one(report.to_dict())
        report._id = result.inserted_id

        return report

    def get_report_by_id(self, report_id: str) -> Optional[CommunityReport]:
        """
        Get report by ID.

        Args:
            report_id: Report ID

        Returns:
            CommunityReport: Report instance or None if not found
        """
        try:
            object_id = ObjectId(report_id)
        except:
            return None

        document = self.collection.find_one({'_id': object_id})
        if document:
            return CommunityReport.from_dict(document)
        return None

    def get_latest_report_by_type(self, report_type: str) -> Optional[CommunityReport]:
        """
        Get the latest report of a specific type.

        Args:
            report_type: Type of report

        Returns:
            CommunityReport: Latest report or None if not found
        """
        document = self.collection.find_one(
            {
                'report_type': report_type,
                'status': {'$in': [ReportStatus.COMPLETED.value, ReportStatus.PUBLISHED.value]}
            },
            sort=[('period_end', -1)]
        )

        if document:
            return CommunityReport.from_dict(document)
        return None

    def get_reports_by_type(self, report_type: str,
                          status: str = None,
                          limit: int = 12) -> List[CommunityReport]:
        """
        Get reports by type with optional status filter.

        Args:
            report_type: Type of report
            status: Filter by status
            limit: Maximum number of reports

        Returns:
            List[CommunityReport]: List of reports
        """
        query = {'report_type': report_type}

        if status:
            query['status'] = status

        cursor = self.collection.find(query).sort('period_end', -1).limit(limit)

        return [CommunityReport.from_dict(doc) for doc in cursor]

    def get_report_for_period(self, report_type: str,
                            period_start: datetime,
                            period_end: datetime) -> Optional[CommunityReport]:
        """
        Get report for a specific period.

        Args:
            report_type: Type of report
            period_start: Start of period
            period_end: End of period

        Returns:
            CommunityReport: Report for the period or None
        """
        document = self.collection.find_one({
            'report_type': report_type,
            'period_start': period_start,
            'period_end': period_end
        })

        if document:
            return CommunityReport.from_dict(document)
        return None

    def get_monthly_reports(self, year: int, month: int = None) -> List[CommunityReport]:
        """
        Get monthly reports for a year or specific month.

        Args:
            year: Year to filter by
            month: Optional month to filter by

        Returns:
            List[CommunityReport]: Monthly reports
        """
        # Build date range query
        if month:
            from calendar import monthrange
            start_date = datetime(year, month, 1, tzinfo=timezone.utc)
            last_day = monthrange(year, month)[1]
            end_date = datetime(year, month, last_day, 23, 59, 59, tzinfo=timezone.utc)
        else:
            start_date = datetime(year, 1, 1, tzinfo=timezone.utc)
            end_date = datetime(year, 12, 31, 23, 59, 59, tzinfo=timezone.utc)

        query = {
            'report_type': ReportType.MONTHLY.value,
            'period_start': {'$gte': start_date, '$lte': end_date}
        }

        cursor = self.collection.find(query).sort('period_start', -1)

        return [CommunityReport.from_dict(doc) for doc in cursor]

    def get_annual_reports(self, start_year: int = None,
                         end_year: int = None) -> List[CommunityReport]:
        """
        Get annual reports within a year range.

        Args:
            start_year: Starting year
            end_year: Ending year

        Returns:
            List[CommunityReport]: Annual reports
        """
        query = {'report_type': ReportType.ANNUAL.value}

        if start_year or end_year:
            date_filter = {}
            if start_year:
                date_filter['$gte'] = datetime(start_year, 1, 1, tzinfo=timezone.utc)
            if end_year:
                date_filter['$lte'] = datetime(end_year, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
            query['period_start'] = date_filter

        cursor = self.collection.find(query).sort('period_start', -1)

        return [CommunityReport.from_dict(doc) for doc in cursor]

    def get_current_real_time_report(self) -> Optional[CommunityReport]:
        """
        Get the current real-time report snapshot.

        Returns:
            CommunityReport: Current real-time report or None
        """
        # Real-time reports are current day snapshots
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

        document = self.collection.find_one(
            {
                'report_type': ReportType.REAL_TIME.value,
                'period_start': {'$gte': today}
            },
            sort=[('created_at', -1)]
        )

        if document:
            return CommunityReport.from_dict(document)
        return None

    def get_published_reports(self, page: int = 1, page_size: int = 20,
                            report_type: str = None) -> Dict[str, Any]:
        """
        Get published reports with pagination.

        Args:
            page: Page number (1-based)
            page_size: Number of reports per page
            report_type: Filter by report type

        Returns:
            Dict: Paginated reports with metadata
        """
        query = {'status': ReportStatus.PUBLISHED.value}

        if report_type:
            query['report_type'] = report_type

        # Calculate skip value
        skip = (page - 1) * page_size

        # Get total count
        total_count = self.collection.count_documents(query)

        # Get reports
        cursor = self.collection.find(query).sort([
            ('period_end', -1)
        ]).skip(skip).limit(page_size)

        reports = [CommunityReport.from_dict(doc) for doc in cursor]

        # Calculate pagination metadata
        total_pages = (total_count + page_size - 1) // page_size

        return {
            'reports': [report.to_response_dict() for report in reports],
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total_count': total_count,
                'total_pages': total_pages,
                'has_next': page < total_pages,
                'has_prev': page > 1
            }
        }

    def update_report(self, report_id: str, update_data: Dict[str, Any]) -> bool:
        """
        Update an existing report.

        Args:
            report_id: Report ID
            update_data: Fields to update

        Returns:
            bool: True if update successful
        """
        try:
            object_id = ObjectId(report_id)
        except:
            return False

        # Add updated timestamp
        update_data['updated_at'] = datetime.now(timezone.utc)

        result = self.collection.update_one(
            {'_id': object_id},
            {'$set': update_data}
        )

        return result.modified_count > 0

    def mark_report_completed(self, report_id: str) -> bool:
        """
        Mark a report as completed.

        Args:
            report_id: Report ID

        Returns:
            bool: True if successful
        """
        update_data = {
            'status': ReportStatus.COMPLETED.value,
            'updated_at': datetime.now(timezone.utc)
        }

        return self.update_report(report_id, update_data)

    def publish_report(self, report_id: str) -> bool:
        """
        Publish a completed report.

        Args:
            report_id: Report ID

        Returns:
            bool: True if successful
        """
        try:
            object_id = ObjectId(report_id)
        except:
            return False

        update_data = {
            'status': ReportStatus.PUBLISHED.value,
            'updated_at': datetime.now(timezone.utc)
        }

        result = self.collection.update_one(
            {
                '_id': object_id,
                'status': ReportStatus.COMPLETED.value
            },
            {'$set': update_data}
        )

        return result.modified_count > 0

    def mark_report_error(self, report_id: str, error_message: str = None) -> bool:
        """
        Mark a report as having an error.

        Args:
            report_id: Report ID
            error_message: Error details

        Returns:
            bool: True if successful
        """
        update_data = {
            'status': ReportStatus.ERROR.value,
            'updated_at': datetime.now(timezone.utc)
        }

        if error_message:
            update_data['generation_metadata.error_message'] = error_message

        return self.update_report(report_id, update_data)

    def add_milestone_to_report(self, report_id: str,
                              milestone_data: Dict[str, Any]) -> bool:
        """
        Add a milestone to a report.

        Args:
            report_id: Report ID
            milestone_data: Milestone information

        Returns:
            bool: True if successful
        """
        try:
            object_id = ObjectId(report_id)
        except:
            return False

        milestone = {
            'title': milestone_data.get('title'),
            'description': milestone_data.get('description'),
            'value': milestone_data.get('value'),
            'onlus_id': milestone_data.get('onlus_id'),
            'achieved_at': milestone_data.get('achieved_at', datetime.now(timezone.utc)),
            'impact_type': milestone_data.get('impact_type')
        }

        result = self.collection.update_one(
            {'_id': object_id},
            {
                '$push': {'milestones_reached': milestone},
                '$set': {'updated_at': datetime.now(timezone.utc)}
            }
        )

        return result.modified_count > 0

    def add_highlight_to_report(self, report_id: str, highlight: str) -> bool:
        """
        Add a highlight to a report.

        Args:
            report_id: Report ID
            highlight: Highlight text

        Returns:
            bool: True if successful
        """
        try:
            object_id = ObjectId(report_id)
        except:
            return False

        result = self.collection.update_one(
            {'_id': object_id},
            {
                '$addToSet': {'highlights': highlight},
                '$set': {'updated_at': datetime.now(timezone.utc)}
            }
        )

        return result.modified_count > 0

    def get_generation_queue(self) -> List[CommunityReport]:
        """
        Get reports that are being generated.

        Returns:
            List[CommunityReport]: Reports in generation queue
        """
        cursor = self.collection.find({
            'status': ReportStatus.GENERATING.value
        }).sort('created_at', 1)

        return [CommunityReport.from_dict(doc) for doc in cursor]

    def get_failed_reports(self, days: int = 7) -> List[CommunityReport]:
        """
        Get reports that failed generation in the last N days.

        Args:
            days: Number of days to look back

        Returns:
            List[CommunityReport]: Failed reports
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

        cursor = self.collection.find({
            'status': ReportStatus.ERROR.value,
            'updated_at': {'$gte': cutoff_date}
        }).sort('updated_at', -1)

        return [CommunityReport.from_dict(doc) for doc in cursor]

    def get_platform_growth_trends(self, months: int = 12) -> Dict[str, Any]:
        """
        Get platform growth trends from monthly reports.

        Args:
            months: Number of months to analyze

        Returns:
            Dict: Growth trend analysis
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=months * 30)

        pipeline = [
            {
                '$match': {
                    'report_type': ReportType.MONTHLY.value,
                    'status': {'$in': [ReportStatus.COMPLETED.value, ReportStatus.PUBLISHED.value]},
                    'period_start': {'$gte': cutoff_date}
                }
            },
            {
                '$sort': {'period_start': 1}
            },
            {
                '$project': {
                    'period_start': 1,
                    'total_donations_amount': 1,
                    'total_donations_count': 1,
                    'unique_donors_count': 1,
                    'onlus_supported_count': 1,
                    'impact_beneficiaries': '$impact_metrics.total_beneficiaries',
                    'projects_funded': '$impact_metrics.projects_funded'
                }
            }
        ]

        results = list(self.collection.aggregate(pipeline))

        if len(results) < 2:
            return {
                'trend_analysis': 'insufficient_data',
                'data_points': len(results),
                'months_analyzed': months
            }

        # Calculate trends
        first_month = results[0]
        last_month = results[-1]

        trends = {}
        metrics = ['total_donations_amount', 'total_donations_count', 'unique_donors_count',
                  'onlus_supported_count', 'impact_beneficiaries', 'projects_funded']

        for metric in metrics:
            first_value = first_month.get(metric, 0) or 0
            last_value = last_month.get(metric, 0) or 0

            if first_value > 0:
                growth_percentage = ((last_value - first_value) / first_value) * 100
            else:
                growth_percentage = 100 if last_value > 0 else 0

            trends[metric] = {
                'first_value': first_value,
                'last_value': last_value,
                'growth_percentage': round(growth_percentage, 2),
                'trend': 'increasing' if growth_percentage > 0 else 'decreasing' if growth_percentage < 0 else 'stable'
            }

        return {
            'trend_analysis': trends,
            'data_points': len(results),
            'months_analyzed': months,
            'period_start': first_month['period_start'].isoformat(),
            'period_end': last_month['period_start'].isoformat()
        }

    def get_year_over_year_comparison(self, current_year: int,
                                    comparison_year: int) -> Dict[str, Any]:
        """
        Compare annual reports between two years.

        Args:
            current_year: Current year
            comparison_year: Year to compare against

        Returns:
            Dict: Year-over-year comparison
        """
        # Get annual reports for both years
        current_report = self.collection.find_one({
            'report_type': ReportType.ANNUAL.value,
            'period_start': {
                '$gte': datetime(current_year, 1, 1, tzinfo=timezone.utc),
                '$lt': datetime(current_year + 1, 1, 1, tzinfo=timezone.utc)
            }
        })

        comparison_report = self.collection.find_one({
            'report_type': ReportType.ANNUAL.value,
            'period_start': {
                '$gte': datetime(comparison_year, 1, 1, tzinfo=timezone.utc),
                '$lt': datetime(comparison_year + 1, 1, 1, tzinfo=timezone.utc)
            }
        })

        if not current_report or not comparison_report:
            return {
                'comparison_available': False,
                'current_year': current_year,
                'comparison_year': comparison_year,
                'missing_data': {
                    'current_year_report': current_report is None,
                    'comparison_year_report': comparison_report is None
                }
            }

        # Calculate differences
        metrics = ['total_donations_amount', 'total_donations_count', 'unique_donors_count', 'onlus_supported_count']
        comparisons = {}

        for metric in metrics:
            current_value = current_report.get(metric, 0)
            comparison_value = comparison_report.get(metric, 0)

            difference = current_value - comparison_value
            if comparison_value > 0:
                growth_percentage = (difference / comparison_value) * 100
            else:
                growth_percentage = 100 if current_value > 0 else 0

            comparisons[metric] = {
                'current_year_value': current_value,
                'comparison_year_value': comparison_value,
                'difference': difference,
                'growth_percentage': round(growth_percentage, 2),
                'trend': 'up' if difference > 0 else 'down' if difference < 0 else 'flat'
            }

        return {
            'comparison_available': True,
            'current_year': current_year,
            'comparison_year': comparison_year,
            'metrics_comparison': comparisons,
            'overall_trend': self._calculate_overall_trend(comparisons)
        }

    def _calculate_overall_trend(self, comparisons: Dict[str, Any]) -> str:
        """
        Calculate overall trend from metric comparisons.

        Args:
            comparisons: Metric comparison data

        Returns:
            str: Overall trend direction
        """
        positive_trends = sum(1 for metric in comparisons.values() if metric['trend'] == 'up')
        negative_trends = sum(1 for metric in comparisons.values() if metric['trend'] == 'down')

        if positive_trends > negative_trends:
            return 'overall_growth'
        elif negative_trends > positive_trends:
            return 'overall_decline'
        else:
            return 'mixed_trends'

    def archive_old_reports(self, days: int = 365) -> int:
        """
        Archive reports older than specified days.

        Args:
            days: Age threshold in days

        Returns:
            int: Number of reports archived
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

        result = self.collection.update_many(
            {
                'created_at': {'$lt': cutoff_date},
                'status': {'$ne': ReportStatus.ARCHIVED.value}
            },
            {
                '$set': {
                    'status': ReportStatus.ARCHIVED.value,
                    'updated_at': datetime.now(timezone.utc)
                }
            }
        )

        return result.modified_count

    def delete_report(self, report_id: str) -> bool:
        """
        Delete a report permanently.

        Args:
            report_id: Report ID

        Returns:
            bool: True if deletion successful
        """
        try:
            object_id = ObjectId(report_id)
        except:
            return False

        result = self.collection.delete_one({'_id': object_id})
        return result.deleted_count > 0

    def get_report_generation_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about report generation.

        Returns:
            Dict: Generation statistics
        """
        pipeline = [
            {
                '$group': {
                    '_id': {
                        'report_type': '$report_type',
                        'status': '$status'
                    },
                    'count': {'$sum': 1},
                    'avg_generation_time': {'$avg': '$generation_metadata.generation_time_seconds'},
                    'latest_report': {'$max': '$created_at'}
                }
            }
        ]

        results = list(self.collection.aggregate(pipeline))

        statistics = {}
        for result in results:
            report_type = result['_id']['report_type']
            status = result['_id']['status']

            if report_type not in statistics:
                statistics[report_type] = {}

            statistics[report_type][status] = {
                'count': result['count'],
                'avg_generation_time': round(result['avg_generation_time'], 2) if result['avg_generation_time'] else 0,
                'latest_report': result['latest_report'].isoformat() if result['latest_report'] else None
            }

        return {
            'generation_statistics': statistics,
            'summary': {
                'total_reports': sum(
                    sum(statuses.values() for statuses in report_stats.values())
                    for report_stats in statistics.values()
                )
            }
        }