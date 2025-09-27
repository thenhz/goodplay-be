from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone, timedelta
from flask import current_app
from enum import Enum
import statistics
from app.donations.repositories.transaction_repository import TransactionRepository
from app.donations.repositories.wallet_repository import WalletRepository
from app.donations.repositories.payment_intent_repository import PaymentIntentRepository
from app.core.repositories.user_repository import UserRepository


class AnalyticsPeriod(Enum):
    """Analytics time periods."""
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class MetricType(Enum):
    """Types of financial metrics."""
    VOLUME = "volume"
    COUNT = "count"
    AVERAGE = "average"
    GROWTH_RATE = "growth_rate"
    CONVERSION_RATE = "conversion_rate"
    DISTRIBUTION = "distribution"


class FinancialAnalyticsService:
    """
    Service for generating financial analytics and insights for admin dashboard.

    Provides comprehensive financial metrics, trends, forecasting, and KPIs
    for donation processing, user behavior, and system performance.
    """

    def __init__(self):
        self.transaction_repo = TransactionRepository()
        self.wallet_repo = WalletRepository()
        self.payment_intent_repo = PaymentIntentRepository()
        self.user_repo = UserRepository()

        # Analytics configuration
        self.analytics_config = {
            'default_period': AnalyticsPeriod.DAILY.value,
            'trend_analysis_days': 30,
            'forecasting_periods': 12,
            'outlier_threshold_std': 2.0,
            'growth_rate_periods': 7,  # days for growth rate calculation
            'cache_duration_minutes': 15
        }

    def generate_financial_dashboard(self, date_range: Dict[str, datetime] = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Generate comprehensive financial dashboard data.

        Args:
            date_range: Optional date range (start_date, end_date)

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success, message, dashboard data
        """
        try:
            # Set default date range (last 30 days)
            if not date_range:
                end_date = datetime.now(timezone.utc)
                start_date = end_date - timedelta(days=30)
                date_range = {'start_date': start_date, 'end_date': end_date}

            dashboard_data = {
                'period': {
                    'start_date': date_range['start_date'].isoformat(),
                    'end_date': date_range['end_date'].isoformat(),
                    'days': (date_range['end_date'] - date_range['start_date']).days
                },
                'generated_at': datetime.now(timezone.utc).isoformat()
            }

            # Generate core metrics
            core_metrics = self._generate_core_metrics(date_range)
            dashboard_data['core_metrics'] = core_metrics

            # Generate trend analysis
            trends = self._generate_trend_analysis(date_range)
            dashboard_data['trends'] = trends

            # Generate user analytics
            user_analytics = self._generate_user_analytics(date_range)
            dashboard_data['user_analytics'] = user_analytics

            # Generate payment analytics
            payment_analytics = self._generate_payment_analytics(date_range)
            dashboard_data['payment_analytics'] = payment_analytics

            # Generate performance metrics
            performance_metrics = self._generate_performance_metrics(date_range)
            dashboard_data['performance_metrics'] = performance_metrics

            # Generate forecasting
            forecasting = self._generate_forecasting_data(date_range)
            dashboard_data['forecasting'] = forecasting

            current_app.logger.info(f"Generated financial dashboard for {dashboard_data['period']['days']} days")

            return True, "FINANCIAL_DASHBOARD_GENERATED", dashboard_data

        except Exception as e:
            current_app.logger.error(f"Failed to generate financial dashboard: {str(e)}")
            return False, "FINANCIAL_DASHBOARD_ERROR", None

    def _generate_core_metrics(self, date_range: Dict[str, datetime]) -> Dict[str, Any]:
        """Generate core financial metrics."""
        try:
            start_date = date_range['start_date']
            end_date = date_range['end_date']

            # Get all transactions in date range
            transactions = self.transaction_repo.find_transactions_by_date_range(
                start_date=start_date,
                end_date=end_date
            )

            # Get donations only
            donations = [t for t in transactions if t.transaction_type == 'donated']

            # Calculate basic metrics
            total_donations = len(donations)
            total_volume = sum(t.amount for t in donations if t.amount > 0)
            average_donation = total_volume / total_donations if total_donations > 0 else 0

            # Get unique donors
            unique_donors = len(set(t.user_id for t in donations))

            # Calculate conversion metrics
            total_users = self._get_total_users_in_period(start_date, end_date)
            conversion_rate = (unique_donors / total_users * 100) if total_users > 0 else 0

            # Calculate growth rates
            previous_period_start = start_date - (end_date - start_date)
            previous_period_end = start_date

            previous_donations = self.transaction_repo.find_transactions_by_date_range(
                start_date=previous_period_start,
                end_date=previous_period_end,
                transaction_type='donated'
            )

            previous_volume = sum(t.amount for t in previous_donations if t.amount > 0)
            volume_growth = ((total_volume - previous_volume) / previous_volume * 100) if previous_volume > 0 else 0

            previous_count = len(previous_donations)
            count_growth = ((total_donations - previous_count) / previous_count * 100) if previous_count > 0 else 0

            return {
                'total_volume': {
                    'current': round(total_volume, 2),
                    'previous': round(previous_volume, 2),
                    'growth_rate': round(volume_growth, 2)
                },
                'total_donations': {
                    'current': total_donations,
                    'previous': previous_count,
                    'growth_rate': round(count_growth, 2)
                },
                'average_donation': {
                    'current': round(average_donation, 2),
                    'previous': round(previous_volume / previous_count, 2) if previous_count > 0 else 0
                },
                'unique_donors': unique_donors,
                'conversion_rate': round(conversion_rate, 2),
                'donations_per_donor': round(total_donations / unique_donors, 2) if unique_donors > 0 else 0
            }

        except Exception as e:
            current_app.logger.error(f"Failed to generate core metrics: {str(e)}")
            return {}

    def _generate_trend_analysis(self, date_range: Dict[str, datetime]) -> Dict[str, Any]:
        """Generate trend analysis data."""
        try:
            start_date = date_range['start_date']
            end_date = date_range['end_date']
            days = (end_date - start_date).days

            # Generate daily data points
            daily_data = []
            for i in range(days):
                day_start = start_date + timedelta(days=i)
                day_end = day_start + timedelta(days=1)

                day_transactions = self.transaction_repo.find_transactions_by_date_range(
                    start_date=day_start,
                    end_date=day_end,
                    transaction_type='donated'
                )

                day_volume = sum(t.amount for t in day_transactions if t.amount > 0)
                day_count = len(day_transactions)

                daily_data.append({
                    'date': day_start.strftime('%Y-%m-%d'),
                    'volume': round(day_volume, 2),
                    'count': day_count,
                    'average': round(day_volume / day_count, 2) if day_count > 0 else 0
                })

            # Calculate trends
            volumes = [d['volume'] for d in daily_data]
            counts = [d['count'] for d in daily_data]

            return {
                'daily_data': daily_data,
                'trends': {
                    'volume_trend': self._calculate_trend(volumes),
                    'count_trend': self._calculate_trend(counts),
                    'volatility': {
                        'volume_std': round(statistics.stdev(volumes), 2) if len(volumes) > 1 else 0,
                        'count_std': round(statistics.stdev(counts), 2) if len(counts) > 1 else 0
                    }
                },
                'peak_days': {
                    'highest_volume': max(daily_data, key=lambda x: x['volume']) if daily_data else None,
                    'highest_count': max(daily_data, key=lambda x: x['count']) if daily_data else None
                }
            }

        except Exception as e:
            current_app.logger.error(f"Failed to generate trend analysis: {str(e)}")
            return {}

    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction from a series of values."""
        if len(values) < 2:
            return "stable"

        # Simple linear trend calculation
        n = len(values)
        x_sum = sum(range(n))
        y_sum = sum(values)
        xy_sum = sum(i * values[i] for i in range(n))
        x_squared_sum = sum(i * i for i in range(n))

        slope = (n * xy_sum - x_sum * y_sum) / (n * x_squared_sum - x_sum * x_sum)

        if slope > 0.1:
            return "increasing"
        elif slope < -0.1:
            return "decreasing"
        else:
            return "stable"

    def _generate_user_analytics(self, date_range: Dict[str, datetime]) -> Dict[str, Any]:
        """Generate user behavior analytics."""
        try:
            start_date = date_range['start_date']
            end_date = date_range['end_date']

            # Get donation transactions
            donations = self.transaction_repo.find_transactions_by_date_range(
                start_date=start_date,
                end_date=end_date,
                transaction_type='donated'
            )

            # Analyze user segments
            user_donations = {}
            for donation in donations:
                user_id = donation.user_id
                if user_id not in user_donations:
                    user_donations[user_id] = {'count': 0, 'total': 0, 'donations': []}
                user_donations[user_id]['count'] += 1
                user_donations[user_id]['total'] += donation.amount
                user_donations[user_id]['donations'].append(donation)

            # Segment users
            segments = {
                'new_donors': 0,      # First donation in period
                'returning_donors': 0, # Multiple donations
                'high_value': 0,      # >100€ total
                'frequent': 0         # >5 donations
            }

            donation_amounts = []
            for user_data in user_donations.values():
                donation_amounts.append(user_data['total'])

                if user_data['count'] == 1:
                    segments['new_donors'] += 1
                else:
                    segments['returning_donors'] += 1

                if user_data['total'] > 100:
                    segments['high_value'] += 1

                if user_data['count'] > 5:
                    segments['frequent'] += 1

            # Calculate user metrics
            total_users = len(user_donations)

            return {
                'total_active_donors': total_users,
                'segments': segments,
                'behavior_metrics': {
                    'average_donations_per_user': round(sum(d['count'] for d in user_donations.values()) / total_users, 2) if total_users > 0 else 0,
                    'average_value_per_user': round(sum(donation_amounts) / total_users, 2) if total_users > 0 else 0,
                    'median_donation_value': round(statistics.median(donation_amounts), 2) if donation_amounts else 0,
                    'retention_rate': round(segments['returning_donors'] / total_users * 100, 2) if total_users > 0 else 0
                },
                'value_distribution': {
                    'under_10': len([a for a in donation_amounts if a < 10]),
                    '10_to_50': len([a for a in donation_amounts if 10 <= a < 50]),
                    '50_to_100': len([a for a in donation_amounts if 50 <= a < 100]),
                    'over_100': len([a for a in donation_amounts if a >= 100])
                }
            }

        except Exception as e:
            current_app.logger.error(f"Failed to generate user analytics: {str(e)}")
            return {}

    def _generate_payment_analytics(self, date_range: Dict[str, datetime]) -> Dict[str, Any]:
        """Generate payment processing analytics."""
        try:
            start_date = date_range['start_date']
            end_date = date_range['end_date']

            # Get payment intents
            payment_intents = self.payment_intent_repo.find_by_date_range(start_date, end_date)

            # Analyze payment success rates
            total_intents = len(payment_intents)
            successful_payments = len([p for p in payment_intents if p.status in ['succeeded', 'completed']])
            failed_payments = len([p for p in payment_intents if p.status in ['failed', 'cancelled']])
            pending_payments = total_intents - successful_payments - failed_payments

            success_rate = (successful_payments / total_intents * 100) if total_intents > 0 else 0

            # Analyze payment timing
            processing_times = []
            for intent in payment_intents:
                if intent.created_at and intent.confirmed_at:
                    processing_time = (intent.confirmed_at - intent.created_at).total_seconds()
                    processing_times.append(processing_time)

            avg_processing_time = statistics.mean(processing_times) if processing_times else 0

            # Analyze fees
            total_fees = sum(float(p.provider_fees or 0) for p in payment_intents)
            total_amount = sum(float(p.amount) for p in payment_intents if p.amount)
            average_fee_rate = (total_fees / total_amount * 100) if total_amount > 0 else 0

            return {
                'success_metrics': {
                    'total_payment_intents': total_intents,
                    'successful_payments': successful_payments,
                    'failed_payments': failed_payments,
                    'pending_payments': pending_payments,
                    'success_rate': round(success_rate, 2)
                },
                'performance_metrics': {
                    'average_processing_time_seconds': round(avg_processing_time, 2),
                    'median_processing_time_seconds': round(statistics.median(processing_times), 2) if processing_times else 0,
                    'fastest_payment_seconds': min(processing_times) if processing_times else 0,
                    'slowest_payment_seconds': max(processing_times) if processing_times else 0
                },
                'fee_analysis': {
                    'total_fees': round(total_fees, 2),
                    'average_fee_rate': round(average_fee_rate, 2),
                    'total_processed_amount': round(total_amount, 2),
                    'net_amount': round(total_amount - total_fees, 2)
                }
            }

        except Exception as e:
            current_app.logger.error(f"Failed to generate payment analytics: {str(e)}")
            return {}

    def _generate_performance_metrics(self, date_range: Dict[str, datetime]) -> Dict[str, Any]:
        """Generate system performance metrics."""
        try:
            start_date = date_range['start_date']
            end_date = date_range['end_date']

            # For now, return placeholder performance metrics
            # In production, this would analyze actual system performance data
            return {
                'transaction_processing': {
                    'average_response_time_ms': 150,
                    'peak_response_time_ms': 850,
                    'error_rate_percentage': 0.5,
                    'throughput_per_second': 25
                },
                'database_performance': {
                    'average_query_time_ms': 45,
                    'slow_queries_count': 12,
                    'connection_pool_utilization': 65
                },
                'system_health': {
                    'uptime_percentage': 99.8,
                    'memory_utilization': 72,
                    'cpu_utilization': 45,
                    'disk_usage_percentage': 34
                },
                'alerts_and_incidents': {
                    'total_alerts': 8,
                    'critical_incidents': 0,
                    'resolved_issues': 6,
                    'average_resolution_time_minutes': 12
                }
            }

        except Exception as e:
            current_app.logger.error(f"Failed to generate performance metrics: {str(e)}")
            return {}

    def _generate_forecasting_data(self, date_range: Dict[str, datetime]) -> Dict[str, Any]:
        """Generate forecasting predictions."""
        try:
            # Get historical data for forecasting
            start_date = date_range['start_date']
            end_date = date_range['end_date']

            # Simple forecasting based on trends
            historical_data = self._get_historical_daily_volumes(start_date, end_date)

            if len(historical_data) < 7:
                return {'error': 'Insufficient data for forecasting'}

            # Calculate simple moving average for next 7 days
            recent_avg = statistics.mean(historical_data[-7:])
            growth_rate = self._calculate_growth_rate(historical_data)

            forecasts = []
            for i in range(1, 8):  # Next 7 days
                forecast_date = end_date + timedelta(days=i)
                forecast_value = recent_avg * (1 + growth_rate) ** i

                forecasts.append({
                    'date': forecast_date.strftime('%Y-%m-%d'),
                    'predicted_volume': round(forecast_value, 2),
                    'confidence': max(0.5, 0.9 - (i * 0.05))  # Decreasing confidence
                })

            return {
                'forecasts': forecasts,
                'methodology': 'moving_average_with_growth',
                'confidence_note': 'Confidence decreases with prediction distance',
                'next_week_total': round(sum(f['predicted_volume'] for f in forecasts), 2),
                'growth_rate_daily': round(growth_rate * 100, 2)
            }

        except Exception as e:
            current_app.logger.error(f"Failed to generate forecasting data: {str(e)}")
            return {}

    def _get_total_users_in_period(self, start_date: datetime, end_date: datetime) -> int:
        """Get total number of users active in the period."""
        try:
            # For now, return a placeholder number
            # In production, this would query user activity in the period
            return 1000
        except Exception:
            return 0

    def _get_historical_daily_volumes(self, start_date: datetime, end_date: datetime) -> List[float]:
        """Get daily donation volumes for the period."""
        try:
            days = (end_date - start_date).days
            daily_volumes = []

            for i in range(days):
                day_start = start_date + timedelta(days=i)
                day_end = day_start + timedelta(days=1)

                day_transactions = self.transaction_repo.find_transactions_by_date_range(
                    start_date=day_start,
                    end_date=day_end,
                    transaction_type='donated'
                )

                day_volume = sum(t.amount for t in day_transactions if t.amount > 0)
                daily_volumes.append(day_volume)

            return daily_volumes

        except Exception as e:
            current_app.logger.error(f"Failed to get historical daily volumes: {str(e)}")
            return []

    def _calculate_growth_rate(self, historical_data: List[float]) -> float:
        """Calculate daily growth rate from historical data."""
        if len(historical_data) < 2:
            return 0.0

        # Calculate simple growth rate
        first_half = historical_data[:len(historical_data)//2]
        second_half = historical_data[len(historical_data)//2:]

        first_avg = statistics.mean(first_half) if first_half else 0
        second_avg = statistics.mean(second_half) if second_half else 0

        if first_avg == 0:
            return 0.0

        growth_rate = (second_avg - first_avg) / first_avg / len(second_half)
        return max(-0.1, min(0.1, growth_rate))  # Cap at ±10% daily growth

    def generate_custom_report(self, report_config: Dict[str, Any]) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Generate custom analytics report based on configuration.

        Args:
            report_config: Report configuration and parameters

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success, message, report data
        """
        try:
            report_type = report_config.get('type', 'summary')
            date_range = report_config.get('date_range', {})
            metrics = report_config.get('metrics', ['volume', 'count', 'users'])

            # Set default date range
            if not date_range:
                end_date = datetime.now(timezone.utc)
                start_date = end_date - timedelta(days=30)
                date_range = {'start_date': start_date, 'end_date': end_date}

            custom_report = {
                'report_id': f"CUSTOM-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                'type': report_type,
                'generated_at': datetime.now(timezone.utc).isoformat(),
                'parameters': report_config,
                'data': {}
            }

            # Generate requested metrics
            if 'volume' in metrics:
                custom_report['data']['volume_analysis'] = self._generate_volume_analysis(date_range)

            if 'count' in metrics:
                custom_report['data']['transaction_count_analysis'] = self._generate_count_analysis(date_range)

            if 'users' in metrics:
                custom_report['data']['user_behavior_analysis'] = self._generate_user_analytics(date_range)

            if 'trends' in metrics:
                custom_report['data']['trend_analysis'] = self._generate_trend_analysis(date_range)

            return True, "CUSTOM_REPORT_GENERATED", custom_report

        except Exception as e:
            current_app.logger.error(f"Failed to generate custom report: {str(e)}")
            return False, "CUSTOM_REPORT_ERROR", None

    def _generate_volume_analysis(self, date_range: Dict[str, datetime]) -> Dict[str, Any]:
        """Generate detailed volume analysis."""
        try:
            start_date = date_range['start_date']
            end_date = date_range['end_date']

            donations = self.transaction_repo.find_transactions_by_date_range(
                start_date=start_date,
                end_date=end_date,
                transaction_type='donated'
            )

            amounts = [float(d.amount) for d in donations if d.amount > 0]

            if not amounts:
                return {'error': 'No donation data found'}

            return {
                'total_volume': round(sum(amounts), 2),
                'average_amount': round(statistics.mean(amounts), 2),
                'median_amount': round(statistics.median(amounts), 2),
                'min_amount': round(min(amounts), 2),
                'max_amount': round(max(amounts), 2),
                'standard_deviation': round(statistics.stdev(amounts), 2) if len(amounts) > 1 else 0,
                'percentiles': {
                    '25th': round(statistics.quantiles(amounts, n=4)[0], 2) if len(amounts) >= 4 else 0,
                    '75th': round(statistics.quantiles(amounts, n=4)[2], 2) if len(amounts) >= 4 else 0,
                    '90th': round(statistics.quantiles(amounts, n=10)[8], 2) if len(amounts) >= 10 else 0
                }
            }

        except Exception as e:
            current_app.logger.error(f"Failed to generate volume analysis: {str(e)}")
            return {}

    def _generate_count_analysis(self, date_range: Dict[str, datetime]) -> Dict[str, Any]:
        """Generate transaction count analysis."""
        try:
            start_date = date_range['start_date']
            end_date = date_range['end_date']

            donations = self.transaction_repo.find_transactions_by_date_range(
                start_date=start_date,
                end_date=end_date,
                transaction_type='donated'
            )

            total_days = (end_date - start_date).days
            total_count = len(donations)

            return {
                'total_transactions': total_count,
                'daily_average': round(total_count / total_days, 2) if total_days > 0 else 0,
                'peak_day_transactions': 0,  # Would need daily breakdown
                'transactions_per_hour': round(total_count / (total_days * 24), 2) if total_days > 0 else 0
            }

        except Exception as e:
            current_app.logger.error(f"Failed to generate count analysis: {str(e)}")
            return {}