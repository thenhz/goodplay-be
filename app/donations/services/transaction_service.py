from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone, timedelta
from flask import current_app
from app.donations.repositories.transaction_repository import TransactionRepository
from app.donations.models.transaction import Transaction, TransactionType, TransactionStatus


class TransactionService:
    """
    Advanced transaction service with fraud prevention and batch processing.
    Handles complex transaction operations, validation, and integrity checks.
    """

    def __init__(self):
        self.transaction_repo = TransactionRepository()

    def create_transaction(self, transaction_data: Dict[str, Any]) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Create a new transaction with comprehensive validation.

        Args:
            transaction_data: Transaction data to create

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success, message, transaction data
        """
        try:
            # Validate transaction data
            validation_error = Transaction.validate_transaction_data(transaction_data)
            if validation_error:
                return False, validation_error, None

            # Additional business logic validation
            business_validation_error = self._validate_business_rules(transaction_data)
            if business_validation_error:
                return False, business_validation_error, None

            # Create transaction instance
            transaction = Transaction.from_dict(transaction_data)

            # Pre-processing fraud checks
            if transaction.transaction_type == TransactionType.EARNED.value:
                fraud_check = self._check_earned_transaction_fraud(transaction)
                if fraud_check['is_suspicious']:
                    current_app.logger.warning(f"Suspicious earned transaction detected: {transaction.transaction_id}")
                    return False, "FRAUD_DETECTION_TRIGGERED", fraud_check

            # Save transaction
            transaction_id = self.transaction_repo.create_transaction(transaction)

            # Post-creation processing
            self._post_transaction_processing(transaction)

            result_data = transaction.to_api_dict()
            current_app.logger.info(f"Transaction created: {transaction.transaction_id} ({transaction.transaction_type})")

            return True, "TRANSACTION_CREATED_SUCCESS", result_data

        except Exception as e:
            current_app.logger.error(f"Failed to create transaction: {str(e)}")
            return False, "TRANSACTION_CREATION_ERROR", None

    def batch_create_transactions(self, transactions_data: List[Dict[str, Any]]) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Create multiple transactions in batch with validation.

        Args:
            transactions_data: List of transaction data dictionaries

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success, message, batch result
        """
        try:
            if not transactions_data:
                return False, "BATCH_TRANSACTIONS_EMPTY", None

            if len(transactions_data) > 1000:  # Batch size limit
                return False, "BATCH_SIZE_TOO_LARGE", None

            valid_transactions = []
            validation_errors = []

            # Validate all transactions first
            for i, tx_data in enumerate(transactions_data):
                validation_error = Transaction.validate_transaction_data(tx_data)
                if validation_error:
                    validation_errors.append({
                        'index': i,
                        'error': validation_error,
                        'data': tx_data
                    })
                else:
                    transaction = Transaction.from_dict(tx_data)
                    valid_transactions.append(transaction)

            if len(validation_errors) > 0:
                current_app.logger.warning(f"Batch validation failed: {len(validation_errors)} invalid transactions")
                return False, "BATCH_VALIDATION_FAILED", {
                    'validation_errors': validation_errors,
                    'valid_count': len(valid_transactions),
                    'invalid_count': len(validation_errors)
                }

            # Check for batch fraud patterns
            batch_fraud_check = self._check_batch_fraud_patterns(valid_transactions)
            if batch_fraud_check['is_suspicious']:
                current_app.logger.warning(f"Suspicious batch transaction pattern detected")
                return False, "BATCH_FRAUD_DETECTION_TRIGGERED", batch_fraud_check

            # Create transactions in batch
            transaction_ids = self.transaction_repo.batch_create_transactions(valid_transactions)

            if len(transaction_ids) != len(valid_transactions):
                current_app.logger.error("Batch creation incomplete")
                return False, "BATCH_CREATION_INCOMPLETE", None

            # Post-processing for all transactions
            for transaction in valid_transactions:
                self._post_transaction_processing(transaction)

            batch_result = {
                'created_count': len(transaction_ids),
                'transaction_ids': transaction_ids,
                'total_amount': sum(tx.get_effective_amount() for tx in valid_transactions),
                'types_breakdown': self._get_types_breakdown(valid_transactions)
            }

            current_app.logger.info(f"Batch transaction created: {len(transaction_ids)} transactions")
            return True, "BATCH_TRANSACTIONS_CREATED_SUCCESS", batch_result

        except Exception as e:
            current_app.logger.error(f"Failed to create batch transactions: {str(e)}")
            return False, "BATCH_TRANSACTION_ERROR", None

    def process_pending_transactions(self, limit: int = 100) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Process pending transactions in batch.

        Args:
            limit: Maximum number of transactions to process

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success, message, processing result
        """
        try:
            pending_transactions = self.transaction_repo.get_pending_transactions(limit)

            if not pending_transactions:
                return True, "NO_PENDING_TRANSACTIONS", {'processed_count': 0}

            processed_count = 0
            failed_count = 0
            processing_results = []

            for transaction in pending_transactions:
                try:
                    # Process based on transaction type
                    success = self._process_individual_transaction(transaction)

                    if success:
                        transaction.mark_completed()
                        self.transaction_repo.update_transaction(transaction)
                        processed_count += 1
                        current_app.logger.debug(f"Processed transaction: {transaction.transaction_id}")
                    else:
                        transaction.mark_failed("Processing failed")
                        self.transaction_repo.update_transaction(transaction)
                        failed_count += 1

                    processing_results.append({
                        'transaction_id': transaction.transaction_id,
                        'success': success,
                        'type': transaction.transaction_type
                    })

                except Exception as e:
                    transaction.mark_failed(f"Processing error: {str(e)}")
                    self.transaction_repo.update_transaction(transaction)
                    failed_count += 1
                    current_app.logger.error(f"Error processing transaction {transaction.transaction_id}: {str(e)}")

            result = {
                'total_pending': len(pending_transactions),
                'processed_count': processed_count,
                'failed_count': failed_count,
                'success_rate': (processed_count / len(pending_transactions)) * 100 if pending_transactions else 0,
                'processing_results': processing_results
            }

            current_app.logger.info(f"Processed {processed_count}/{len(pending_transactions)} pending transactions")
            return True, "PENDING_TRANSACTIONS_PROCESSED", result

        except Exception as e:
            current_app.logger.error(f"Failed to process pending transactions: {str(e)}")
            return False, "PENDING_PROCESSING_ERROR", None

    def get_transaction_analytics(self, user_id: str = None,
                                days_back: int = 30) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Get comprehensive transaction analytics.

        Args:
            user_id: Optional user ID for user-specific analytics
            days_back: Number of days to analyze

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success, message, analytics data
        """
        try:
            start_date = datetime.now(timezone.utc) - timedelta(days=days_back)
            end_date = datetime.now(timezone.utc)

            if user_id:
                # User-specific analytics
                summary = self.transaction_repo.get_user_transaction_summary(
                    user_id=user_id,
                    start_date=start_date,
                    end_date=end_date
                )
                analytics_type = "user"
            else:
                # Platform-wide analytics
                summary = self.transaction_repo.get_transaction_statistics()
                analytics_type = "platform"

            # Calculate additional metrics
            analytics = {
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'days': days_back
                },
                'summary': summary,
                'analytics_type': analytics_type,
                'performance_metrics': self._calculate_performance_metrics(summary),
                'trends': self._calculate_trend_metrics(user_id, days_back)
            }

            return True, "TRANSACTION_ANALYTICS_SUCCESS", analytics

        except Exception as e:
            current_app.logger.error(f"Failed to get transaction analytics: {str(e)}")
            return False, "TRANSACTION_ANALYTICS_ERROR", None

    def cleanup_old_transactions(self, days_old: int = 365) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Clean up old completed transactions for data retention.

        Args:
            days_old: Age threshold for cleanup

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success, message, cleanup result
        """
        try:
            if days_old < 90:  # Minimum retention period
                return False, "CLEANUP_RETENTION_TOO_SHORT", None

            deleted_count = self.transaction_repo.delete_old_transactions(days_old)

            cleanup_result = {
                'deleted_count': deleted_count,
                'retention_days': days_old,
                'cleanup_date': datetime.now(timezone.utc).isoformat()
            }

            current_app.logger.info(f"Cleaned up {deleted_count} old transactions (>{days_old} days)")
            return True, "TRANSACTION_CLEANUP_SUCCESS", cleanup_result

        except Exception as e:
            current_app.logger.error(f"Failed to cleanup old transactions: {str(e)}")
            return False, "TRANSACTION_CLEANUP_ERROR", None

    def get_fraud_report(self, hours_back: int = 24) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Generate fraud detection report.

        Args:
            hours_back: Number of hours to analyze

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success, message, fraud report
        """
        try:
            suspicious_transactions = self.transaction_repo.get_suspicious_transactions(hours_back)
            failed_transactions = self.transaction_repo.get_failed_transactions(hours_back)

            fraud_report = {
                'analysis_period_hours': hours_back,
                'suspicious_transactions': len(suspicious_transactions),
                'failed_transactions': len(failed_transactions),
                'fraud_indicators': self._analyze_fraud_patterns(suspicious_transactions),
                'risk_assessment': self._calculate_risk_assessment(suspicious_transactions, failed_transactions),
                'recommendations': self._generate_fraud_recommendations(suspicious_transactions)
            }

            return True, "FRAUD_REPORT_GENERATED", fraud_report

        except Exception as e:
            current_app.logger.error(f"Failed to generate fraud report: {str(e)}")
            return False, "FRAUD_REPORT_ERROR", None

    def _validate_business_rules(self, transaction_data: Dict[str, Any]) -> Optional[str]:
        """Validate business-specific rules for transactions."""
        transaction_type = transaction_data.get('transaction_type')
        amount = transaction_data.get('amount', 0)

        # Daily transaction limits per user
        if transaction_type == TransactionType.EARNED.value:
            user_id = transaction_data.get('user_id')
            if user_id:
                today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
                today_summary = self.transaction_repo.get_user_transaction_summary(
                    user_id=user_id,
                    start_date=today_start
                )
                daily_earned = today_summary.get('total_effective_earned', 0)
                if daily_earned + amount > 1000:  # €1000 daily limit
                    return "DAILY_EARNING_LIMIT_EXCEEDED"

        # Maximum single transaction amount
        if amount > 10000:  # €10,000 limit
            return "TRANSACTION_AMOUNT_TOO_LARGE"

        return None

    def _check_earned_transaction_fraud(self, transaction: Transaction) -> Dict[str, Any]:
        """Check for fraud indicators in earned transactions."""
        fraud_indicators = transaction.get_fraud_risk_indicators()

        # Additional checks
        user_recent_transactions = self.transaction_repo.find_by_user_id(
            user_id=transaction.user_id,
            limit=10,
            offset=0,
            transaction_type=TransactionType.EARNED.value
        )

        # Check for rapid succession
        if len(user_recent_transactions) >= 5:
            recent_times = [tx.created_at for tx in user_recent_transactions[:5]]
            time_diffs = [(recent_times[i] - recent_times[i+1]).total_seconds()
                         for i in range(len(recent_times)-1)]
            if all(diff < 60 for diff in time_diffs):  # All within 1 minute
                fraud_indicators['rapid_succession'] = True

        # Calculate overall risk
        risk_score = sum(1 for indicator in fraud_indicators.values() if indicator)
        fraud_indicators['risk_score'] = risk_score
        fraud_indicators['is_suspicious'] = risk_score >= 3

        return fraud_indicators

    def _check_batch_fraud_patterns(self, transactions: List[Transaction]) -> Dict[str, Any]:
        """Check for fraud patterns in batch transactions."""
        patterns = {
            'is_suspicious': False,
            'patterns_detected': []
        }

        # Check for identical amounts
        amounts = [tx.amount for tx in transactions]
        if len(set(amounts)) == 1 and len(amounts) > 5:
            patterns['patterns_detected'].append('identical_amounts')

        # Check for same user flooding
        user_counts = {}
        for tx in transactions:
            user_counts[tx.user_id] = user_counts.get(tx.user_id, 0) + 1

        max_user_count = max(user_counts.values()) if user_counts else 0
        if max_user_count > len(transactions) * 0.5:  # One user > 50% of batch
            patterns['patterns_detected'].append('user_flooding')

        # Check for suspicious timing
        if all(tx.created_at.hour < 4 or tx.created_at.hour > 23 for tx in transactions):
            patterns['patterns_detected'].append('off_hours_batch')

        patterns['is_suspicious'] = len(patterns['patterns_detected']) >= 2
        return patterns

    def _process_individual_transaction(self, transaction: Transaction) -> bool:
        """Process an individual pending transaction."""
        try:
            # Implement specific processing logic based on transaction type
            if transaction.transaction_type == TransactionType.EARNED.value:
                return self._process_earned_transaction(transaction)
            elif transaction.transaction_type == TransactionType.DONATED.value:
                return self._process_donation_transaction(transaction)
            else:
                return True  # Default success for other types

        except Exception as e:
            current_app.logger.error(f"Error processing transaction {transaction.transaction_id}: {str(e)}")
            return False

    def _process_earned_transaction(self, transaction: Transaction) -> bool:
        """Process earned credit transaction."""
        # Additional validation for earned transactions
        if transaction.game_session_id:
            # Could validate session exists and is legitimate
            pass

        # Mark as completed
        return True

    def _process_donation_transaction(self, transaction: Transaction) -> bool:
        """Process donation transaction."""
        # Additional validation for donations
        if transaction.onlus_id:
            # Could validate ONLUS exists and is active
            pass

        # Generate receipt
        receipt_data = {
            'receipt_id': f"receipt_{transaction.transaction_id}",
            'tax_deductible': True,
            'processing_fee': 0.0
        }
        transaction.receipt_data.update(receipt_data)

        return True

    def _post_transaction_processing(self, transaction: Transaction) -> None:
        """Post-processing tasks after transaction creation."""
        # Could include notifications, webhooks, etc.
        pass

    def _get_types_breakdown(self, transactions: List[Transaction]) -> Dict[str, int]:
        """Get breakdown of transaction types."""
        breakdown = {}
        for tx in transactions:
            breakdown[tx.transaction_type] = breakdown.get(tx.transaction_type, 0) + 1
        return breakdown

    def _calculate_performance_metrics(self, summary: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate performance metrics from transaction summary."""
        total_transactions = summary.get('total_transactions', 0)
        completed_count = summary.get('completed_count', 0)

        return {
            'completion_rate': (completed_count / total_transactions * 100) if total_transactions > 0 else 0,
            'avg_transaction_amount': summary.get('avg_amount', 0),
            'total_volume': summary.get('total_effective_amount', 0)
        }

    def _calculate_trend_metrics(self, user_id: str = None, days_back: int = 30) -> Dict[str, Any]:
        """Calculate trend metrics (placeholder for advanced analytics)."""
        return {
            'daily_average': 0.0,
            'growth_rate': 0.0,
            'trend_direction': 'stable'
        }

    def _analyze_fraud_patterns(self, suspicious_transactions: List[Transaction]) -> List[str]:
        """Analyze patterns in suspicious transactions."""
        patterns = []

        if len(suspicious_transactions) > 10:
            patterns.append('high_volume_suspicious_activity')

        # Check for common fraud indicators
        high_amounts = [tx for tx in suspicious_transactions if tx.get_effective_amount() > 1000]
        if len(high_amounts) > 5:
            patterns.append('multiple_high_value_transactions')

        return patterns

    def _calculate_risk_assessment(self, suspicious_transactions: List[Transaction],
                                 failed_transactions: List[Transaction]) -> str:
        """Calculate overall risk assessment."""
        total_suspicious = len(suspicious_transactions)
        total_failed = len(failed_transactions)

        if total_suspicious > 50 or total_failed > 100:
            return 'high'
        elif total_suspicious > 20 or total_failed > 50:
            return 'medium'
        else:
            return 'low'

    def _generate_fraud_recommendations(self, suspicious_transactions: List[Transaction]) -> List[str]:
        """Generate recommendations based on fraud analysis."""
        recommendations = []

        if len(suspicious_transactions) > 20:
            recommendations.append('Increase monitoring frequency')
            recommendations.append('Review user verification requirements')

        if any(tx.get_effective_amount() > 1000 for tx in suspicious_transactions):
            recommendations.append('Implement additional verification for high-value transactions')

        return recommendations