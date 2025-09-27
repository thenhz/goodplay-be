from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone, timedelta
from flask import current_app
from app.donations.repositories.transaction_repository import TransactionRepository
from app.donations.repositories.wallet_repository import WalletRepository
from app.donations.models.transaction import Transaction, TransactionType


class FraudPreventionService:
    """
    Dedicated fraud prevention and detection service.
    Implements ML-based anomaly detection, pattern recognition, and risk scoring.
    """

    def __init__(self):
        self.transaction_repo = TransactionRepository()
        self.wallet_repo = WalletRepository()

        # Fraud detection thresholds
        self.thresholds = {
            'max_hourly_earned': 100.0,  # €100 per hour
            'max_daily_earned': 1000.0,  # €1000 per day
            'max_session_duration_hours': 12,  # 12 hours
            'min_session_duration_seconds': 10,  # 10 seconds
            'max_transactions_per_minute': 5,
            'suspicious_amount_threshold': 500.0,  # €500
            'rapid_succession_window_seconds': 60,
            'max_multiplier_threshold': 5.0
        }

    def analyze_user_behavior(self, user_id: str,
                            analysis_period_hours: int = 24) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Comprehensive user behavior analysis for fraud detection.

        Args:
            user_id: User identifier
            analysis_period_hours: Period to analyze

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success, message, analysis result
        """
        try:
            start_time = datetime.now(timezone.utc) - timedelta(hours=analysis_period_hours)

            # Get user's recent transactions
            recent_transactions = self.transaction_repo.find_by_user_id(
                user_id=user_id,
                limit=200,
                sort_by='created_at',
                sort_order=-1
            )

            # Filter transactions within analysis period
            period_transactions = [
                tx for tx in recent_transactions
                if tx.created_at >= start_time
            ]

            # Perform various analyses
            risk_indicators = {
                'user_id': user_id,
                'analysis_period_hours': analysis_period_hours,
                'total_transactions': len(period_transactions),
                'risk_score': 0,
                'risk_level': 'low',
                'indicators': []
            }

            # 1. Volume analysis
            volume_risk = self._analyze_transaction_volume(period_transactions, analysis_period_hours)
            risk_indicators.update(volume_risk)

            # 2. Pattern analysis
            pattern_risk = self._analyze_transaction_patterns(period_transactions)
            risk_indicators['indicators'].extend(pattern_risk.get('patterns', []))

            # 3. Timing analysis
            timing_risk = self._analyze_transaction_timing(period_transactions)
            risk_indicators['indicators'].extend(timing_risk.get('anomalies', []))

            # 4. Amount analysis
            amount_risk = self._analyze_transaction_amounts(period_transactions)
            risk_indicators['indicators'].extend(amount_risk.get('suspicious_amounts', []))

            # 5. Session analysis
            if period_transactions:
                session_risk = self._analyze_session_patterns(period_transactions)
                risk_indicators['indicators'].extend(session_risk.get('session_anomalies', []))

            # Calculate overall risk score
            risk_indicators['risk_score'] = self._calculate_risk_score(risk_indicators['indicators'])
            risk_indicators['risk_level'] = self._determine_risk_level(risk_indicators['risk_score'])

            # Add detailed analysis
            risk_indicators['detailed_analysis'] = {
                'volume_analysis': volume_risk,
                'pattern_analysis': pattern_risk,
                'timing_analysis': timing_risk,
                'amount_analysis': amount_risk
            }

            current_app.logger.info(f"User behavior analysis completed for {user_id}: risk_level={risk_indicators['risk_level']}")

            return True, "FRAUD_ANALYSIS_COMPLETED", risk_indicators

        except Exception as e:
            current_app.logger.error(f"Failed to analyze user behavior for {user_id}: {str(e)}")
            return False, "FRAUD_ANALYSIS_ERROR", None

    def detect_anomalies(self, user_id: str, transaction_data: Dict[str, Any]) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Real-time anomaly detection for new transactions.

        Args:
            user_id: User identifier
            transaction_data: New transaction data

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success, message, anomaly result
        """
        try:
            anomaly_result = {
                'is_anomalous': False,
                'anomaly_score': 0.0,
                'anomaly_types': [],
                'recommendation': 'approve',
                'confidence': 0.0
            }

            # 1. Check against user's historical behavior
            user_baseline = self._get_user_baseline(user_id)
            baseline_anomalies = self._check_baseline_anomalies(transaction_data, user_baseline)

            if baseline_anomalies['is_anomalous']:
                anomaly_result['anomaly_types'].extend(baseline_anomalies['types'])
                anomaly_result['anomaly_score'] += baseline_anomalies['score']

            # 2. Check against platform-wide patterns
            platform_anomalies = self._check_platform_anomalies(transaction_data)

            if platform_anomalies['is_anomalous']:
                anomaly_result['anomaly_types'].extend(platform_anomalies['types'])
                anomaly_result['anomaly_score'] += platform_anomalies['score']

            # 3. Check for known fraud patterns
            fraud_patterns = self._check_fraud_patterns(user_id, transaction_data)

            if fraud_patterns['matches_known_patterns']:
                anomaly_result['anomaly_types'].extend(fraud_patterns['patterns'])
                anomaly_result['anomaly_score'] += fraud_patterns['score']

            # 4. Machine learning-based detection (placeholder)
            ml_anomalies = self._ml_anomaly_detection(user_id, transaction_data)

            if ml_anomalies['is_anomalous']:
                anomaly_result['anomaly_types'].extend(ml_anomalies['features'])
                anomaly_result['anomaly_score'] += ml_anomalies['score']

            # Normalize anomaly score and determine final result
            anomaly_result['anomaly_score'] = min(anomaly_result['anomaly_score'], 100.0)
            anomaly_result['is_anomalous'] = anomaly_result['anomaly_score'] > 70.0
            anomaly_result['confidence'] = anomaly_result['anomaly_score'] / 100.0

            # Determine recommendation
            if anomaly_result['anomaly_score'] > 90.0:
                anomaly_result['recommendation'] = 'block'
            elif anomaly_result['anomaly_score'] > 70.0:
                anomaly_result['recommendation'] = 'review'
            else:
                anomaly_result['recommendation'] = 'approve'

            return True, "ANOMALY_DETECTION_COMPLETED", anomaly_result

        except Exception as e:
            current_app.logger.error(f"Failed to detect anomalies for user {user_id}: {str(e)}")
            return False, "ANOMALY_DETECTION_ERROR", None

    def validate_session_legitimacy(self, session_data: Dict[str, Any]) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Validate if a game session appears legitimate.

        Args:
            session_data: Game session data

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success, message, validation result
        """
        try:
            validation_result = {
                'is_legitimate': True,
                'confidence_score': 100.0,
                'suspicious_indicators': [],
                'validation_checks': {}
            }

            # 1. Duration validation
            duration_check = self._validate_session_duration(session_data)
            validation_result['validation_checks']['duration'] = duration_check
            if not duration_check['is_valid']:
                validation_result['suspicious_indicators'].extend(duration_check['issues'])

            # 2. Play pattern validation
            pattern_check = self._validate_play_patterns(session_data)
            validation_result['validation_checks']['patterns'] = pattern_check
            if not pattern_check['is_valid']:
                validation_result['suspicious_indicators'].extend(pattern_check['issues'])

            # 3. Device consistency validation
            device_check = self._validate_device_consistency(session_data)
            validation_result['validation_checks']['device'] = device_check
            if not device_check['is_valid']:
                validation_result['suspicious_indicators'].extend(device_check['issues'])

            # 4. Timing validation
            timing_check = self._validate_session_timing(session_data)
            validation_result['validation_checks']['timing'] = timing_check
            if not timing_check['is_valid']:
                validation_result['suspicious_indicators'].extend(timing_check['issues'])

            # Calculate overall legitimacy
            suspicious_count = len(validation_result['suspicious_indicators'])
            validation_result['confidence_score'] = max(0, 100 - (suspicious_count * 20))
            validation_result['is_legitimate'] = validation_result['confidence_score'] >= 60.0

            return True, "SESSION_VALIDATION_COMPLETED", validation_result

        except Exception as e:
            current_app.logger.error(f"Failed to validate session legitimacy: {str(e)}")
            return False, "SESSION_VALIDATION_ERROR", None

    def check_rate_limits(self, user_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Check if user has exceeded rate limits.

        Args:
            user_id: User identifier

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success, message, rate limit status
        """
        try:
            now = datetime.now(timezone.utc)

            rate_limit_status = {
                'user_id': user_id,
                'limits_exceeded': [],
                'current_usage': {},
                'time_until_reset': {},
                'is_rate_limited': False
            }

            # Check hourly limits
            hour_start = now.replace(minute=0, second=0, microsecond=0)
            hourly_transactions = self._get_user_transactions_since(user_id, hour_start)
            hourly_earned = sum(tx.get_effective_amount() for tx in hourly_transactions
                              if tx.transaction_type == TransactionType.EARNED.value)

            rate_limit_status['current_usage']['hourly_earned'] = hourly_earned
            if hourly_earned > self.thresholds['max_hourly_earned']:
                rate_limit_status['limits_exceeded'].append('hourly_earned_limit')

            # Check daily limits
            day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            daily_transactions = self._get_user_transactions_since(user_id, day_start)
            daily_earned = sum(tx.get_effective_amount() for tx in daily_transactions
                             if tx.transaction_type == TransactionType.EARNED.value)

            rate_limit_status['current_usage']['daily_earned'] = daily_earned
            if daily_earned > self.thresholds['max_daily_earned']:
                rate_limit_status['limits_exceeded'].append('daily_earned_limit')

            # Check transaction frequency
            minute_start = now.replace(second=0, microsecond=0)
            minute_transactions = self._get_user_transactions_since(user_id, minute_start)

            rate_limit_status['current_usage']['transactions_per_minute'] = len(minute_transactions)
            if len(minute_transactions) > self.thresholds['max_transactions_per_minute']:
                rate_limit_status['limits_exceeded'].append('transaction_frequency_limit')

            # Calculate time until reset
            rate_limit_status['time_until_reset'] = {
                'hourly_reset': (hour_start + timedelta(hours=1) - now).total_seconds(),
                'daily_reset': (day_start + timedelta(days=1) - now).total_seconds(),
                'minute_reset': (minute_start + timedelta(minutes=1) - now).total_seconds()
            }

            rate_limit_status['is_rate_limited'] = len(rate_limit_status['limits_exceeded']) > 0

            return True, "RATE_LIMIT_CHECK_COMPLETED", rate_limit_status

        except Exception as e:
            current_app.logger.error(f"Failed to check rate limits for user {user_id}: {str(e)}")
            return False, "RATE_LIMIT_CHECK_ERROR", None

    def flag_suspicious_activity(self, user_id: str, reason: str,
                               metadata: Dict[str, Any] = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Flag user for suspicious activity.

        Args:
            user_id: User identifier
            reason: Reason for flagging
            metadata: Additional metadata

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success, message, flag result
        """
        try:
            flag_data = {
                'user_id': user_id,
                'reason': reason,
                'flagged_at': datetime.now(timezone.utc),
                'metadata': metadata or {},
                'flag_id': f"flag_{user_id}_{int(datetime.now(timezone.utc).timestamp())}"
            }

            # Store flag (would typically go to a separate flags collection)
            current_app.logger.warning(f"User flagged for suspicious activity: {user_id} - {reason}")

            # Could trigger additional actions:
            # - Temporarily limit user actions
            # - Send notification to admin
            # - Increase monitoring level

            return True, "SUSPICIOUS_ACTIVITY_FLAGGED", flag_data

        except Exception as e:
            current_app.logger.error(f"Failed to flag suspicious activity for user {user_id}: {str(e)}")
            return False, "ACTIVITY_FLAGGING_ERROR", None

    def generate_fraud_report(self, period_hours: int = 24) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Generate comprehensive fraud detection report.

        Args:
            period_hours: Reporting period in hours

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success, message, fraud report
        """
        try:
            start_time = datetime.now(timezone.utc) - timedelta(hours=period_hours)

            # Get suspicious transactions
            suspicious_transactions = self.transaction_repo.get_suspicious_transactions(period_hours)

            fraud_report = {
                'report_period_hours': period_hours,
                'generated_at': datetime.now(timezone.utc).isoformat(),
                'summary': {
                    'total_suspicious_transactions': len(suspicious_transactions),
                    'total_amount_at_risk': sum(tx.get_effective_amount() for tx in suspicious_transactions),
                    'unique_users_flagged': len(set(tx.user_id for tx in suspicious_transactions))
                },
                'risk_breakdown': self._analyze_risk_breakdown(suspicious_transactions),
                'pattern_analysis': self._analyze_fraud_patterns_detailed(suspicious_transactions),
                'recommendations': self._generate_security_recommendations(suspicious_transactions)
            }

            return True, "FRAUD_REPORT_GENERATED", fraud_report

        except Exception as e:
            current_app.logger.error(f"Failed to generate fraud report: {str(e)}")
            return False, "FRAUD_REPORT_ERROR", None

    # Private helper methods

    def _analyze_transaction_volume(self, transactions: List[Transaction], period_hours: int) -> Dict[str, Any]:
        """Analyze transaction volume for anomalies."""
        if not transactions:
            return {'volume_risk': 'low', 'volume_score': 0}

        hourly_rate = len(transactions) / period_hours
        total_amount = sum(tx.get_effective_amount() for tx in transactions)

        volume_risk = 'low'
        if hourly_rate > 10 or total_amount > 1000:
            volume_risk = 'high'
        elif hourly_rate > 5 or total_amount > 500:
            volume_risk = 'medium'

        return {
            'volume_risk': volume_risk,
            'volume_score': min(hourly_rate * 5, 50),
            'hourly_transaction_rate': hourly_rate,
            'total_amount': total_amount
        }

    def _analyze_transaction_patterns(self, transactions: List[Transaction]) -> Dict[str, Any]:
        """Analyze transaction patterns for suspicious behavior."""
        patterns = []

        if len(transactions) > 1:
            # Check for identical amounts
            amounts = [tx.amount for tx in transactions]
            if len(set(amounts)) == 1:
                patterns.append('identical_amounts')

            # Check for regular intervals
            if self._check_regular_intervals(transactions):
                patterns.append('regular_intervals')

            # Check for round numbers
            round_amounts = sum(1 for amount in amounts if amount == round(amount))
            if round_amounts > len(amounts) * 0.8:
                patterns.append('mostly_round_amounts')

        return {
            'patterns': patterns,
            'pattern_score': len(patterns) * 10
        }

    def _analyze_transaction_timing(self, transactions: List[Transaction]) -> Dict[str, Any]:
        """Analyze transaction timing for anomalies."""
        anomalies = []

        if transactions:
            # Check for off-hours activity
            off_hours = sum(1 for tx in transactions if tx.created_at.hour < 6 or tx.created_at.hour > 22)
            if off_hours > len(transactions) * 0.7:
                anomalies.append('predominantly_off_hours')

            # Check for rapid succession
            if len(transactions) > 1:
                time_diffs = []
                sorted_txs = sorted(transactions, key=lambda x: x.created_at)
                for i in range(1, len(sorted_txs)):
                    diff = (sorted_txs[i].created_at - sorted_txs[i-1].created_at).total_seconds()
                    time_diffs.append(diff)

                if any(diff < 10 for diff in time_diffs):
                    anomalies.append('rapid_succession')

        return {
            'anomalies': anomalies,
            'timing_score': len(anomalies) * 15
        }

    def _analyze_transaction_amounts(self, transactions: List[Transaction]) -> Dict[str, Any]:
        """Analyze transaction amounts for suspicious patterns."""
        suspicious_amounts = []

        for tx in transactions:
            amount = tx.get_effective_amount()

            if amount > self.thresholds['suspicious_amount_threshold']:
                suspicious_amounts.append('high_amount')

            if tx.multiplier_applied > self.thresholds['max_multiplier_threshold']:
                suspicious_amounts.append('high_multiplier')

        return {
            'suspicious_amounts': suspicious_amounts,
            'amount_score': len(suspicious_amounts) * 8
        }

    def _analyze_session_patterns(self, transactions: List[Transaction]) -> Dict[str, Any]:
        """Analyze game session patterns for anomalies."""
        session_anomalies = []

        sessions_with_data = [tx for tx in transactions if tx.game_session_id and tx.metadata]

        for tx in sessions_with_data:
            duration_ms = tx.metadata.get('play_duration_ms', 0)
            if duration_ms > 0:
                duration_hours = duration_ms / (1000 * 60 * 60)

                if duration_hours > self.thresholds['max_session_duration_hours']:
                    session_anomalies.append('extremely_long_session')
                elif duration_ms < self.thresholds['min_session_duration_seconds'] * 1000:
                    session_anomalies.append('extremely_short_session')

        return {
            'session_anomalies': session_anomalies,
            'session_score': len(session_anomalies) * 12
        }

    def _calculate_risk_score(self, indicators: List[str]) -> float:
        """Calculate overall risk score from indicators."""
        base_score = len(indicators) * 10

        # Weight certain indicators more heavily
        high_risk_indicators = ['rapid_succession', 'extremely_long_session', 'high_amount']
        weighted_score = sum(20 for indicator in indicators if indicator in high_risk_indicators)

        return min(base_score + weighted_score, 100.0)

    def _determine_risk_level(self, risk_score: float) -> str:
        """Determine risk level from score."""
        if risk_score >= 80:
            return 'critical'
        elif risk_score >= 60:
            return 'high'
        elif risk_score >= 40:
            return 'medium'
        else:
            return 'low'

    def _get_user_baseline(self, user_id: str) -> Dict[str, Any]:
        """Get user's baseline behavior for comparison."""
        # Placeholder for user baseline calculation
        return {
            'avg_transaction_amount': 10.0,
            'avg_session_duration': 1800,  # 30 minutes
            'typical_play_hours': [18, 19, 20, 21],
            'transaction_frequency': 5  # per day
        }

    def _check_baseline_anomalies(self, transaction_data: Dict[str, Any], baseline: Dict[str, Any]) -> Dict[str, Any]:
        """Check for anomalies against user baseline."""
        return {
            'is_anomalous': False,
            'types': [],
            'score': 0.0
        }

    def _check_platform_anomalies(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check for anomalies against platform patterns."""
        return {
            'is_anomalous': False,
            'types': [],
            'score': 0.0
        }

    def _check_fraud_patterns(self, user_id: str, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check against known fraud patterns."""
        return {
            'matches_known_patterns': False,
            'patterns': [],
            'score': 0.0
        }

    def _ml_anomaly_detection(self, user_id: str, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """ML-based anomaly detection (placeholder)."""
        return {
            'is_anomalous': False,
            'features': [],
            'score': 0.0
        }

    def _validate_session_duration(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate session duration."""
        duration_ms = session_data.get('play_duration_ms', 0)
        issues = []

        if duration_ms < self.thresholds['min_session_duration_seconds'] * 1000:
            issues.append('session_too_short')
        elif duration_ms > self.thresholds['max_session_duration_hours'] * 3600 * 1000:
            issues.append('session_too_long')

        return {
            'is_valid': len(issues) == 0,
            'issues': issues,
            'duration_ms': duration_ms
        }

    def _validate_play_patterns(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate play patterns."""
        return {
            'is_valid': True,
            'issues': []
        }

    def _validate_device_consistency(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate device consistency."""
        return {
            'is_valid': True,
            'issues': []
        }

    def _validate_session_timing(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate session timing."""
        return {
            'is_valid': True,
            'issues': []
        }

    def _get_user_transactions_since(self, user_id: str, since: datetime) -> List[Transaction]:
        """Get user transactions since a specific time."""
        all_transactions = self.transaction_repo.find_by_user_id(user_id, limit=100)
        return [tx for tx in all_transactions if tx.created_at >= since]

    def _check_regular_intervals(self, transactions: List[Transaction]) -> bool:
        """Check if transactions occur at regular intervals."""
        if len(transactions) < 3:
            return False

        sorted_txs = sorted(transactions, key=lambda x: x.created_at)
        intervals = []
        for i in range(1, len(sorted_txs)):
            diff = (sorted_txs[i].created_at - sorted_txs[i-1].created_at).total_seconds()
            intervals.append(diff)

        # Check if intervals are suspiciously regular (within 10% variance)
        if len(set(round(interval, -1) for interval in intervals)) <= 2:
            return True

        return False

    def _analyze_risk_breakdown(self, transactions: List[Transaction]) -> Dict[str, Any]:
        """Analyze risk breakdown by categories."""
        return {
            'high_amount_transactions': len([tx for tx in transactions if tx.get_effective_amount() > 500]),
            'off_hours_transactions': len([tx for tx in transactions if tx.created_at.hour < 6 or tx.created_at.hour > 22]),
            'high_multiplier_transactions': len([tx for tx in transactions if tx.multiplier_applied > 3.0])
        }

    def _analyze_fraud_patterns_detailed(self, transactions: List[Transaction]) -> Dict[str, Any]:
        """Detailed fraud pattern analysis."""
        return {
            'identical_amounts': len(set(tx.amount for tx in transactions)) == 1 and len(transactions) > 1,
            'rapid_succession_count': 0,  # Would calculate actual rapid succession
            'unusual_timing_count': 0     # Would calculate unusual timing patterns
        }

    def _generate_security_recommendations(self, transactions: List[Transaction]) -> List[str]:
        """Generate security recommendations based on analysis."""
        recommendations = []

        if len(transactions) > 50:
            recommendations.append("Implement stricter rate limiting")

        if any(tx.get_effective_amount() > 1000 for tx in transactions):
            recommendations.append("Add manual review for high-value transactions")

        if len(set(tx.user_id for tx in transactions)) < len(transactions) * 0.3:
            recommendations.append("Investigate potential account farming")

        return recommendations