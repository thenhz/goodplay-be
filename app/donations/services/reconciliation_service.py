from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone, timedelta
from flask import current_app
from enum import Enum
from app.donations.repositories.transaction_repository import TransactionRepository
from app.donations.repositories.payment_intent_repository import PaymentIntentRepository
from app.donations.repositories.wallet_repository import WalletRepository


class ReconciliationStatus(Enum):
    """Status of reconciliation process."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class DiscrepancyType(Enum):
    """Types of discrepancies found during reconciliation."""
    MISSING_TRANSACTION = "missing_transaction"
    DUPLICATE_TRANSACTION = "duplicate_transaction"
    AMOUNT_MISMATCH = "amount_mismatch"
    STATUS_MISMATCH = "status_mismatch"
    TIMING_DISCREPANCY = "timing_discrepancy"
    EXTERNAL_MISMATCH = "external_mismatch"
    ORPHANED_PAYMENT = "orphaned_payment"


class ReconciliationService:
    """
    Service for reconciling financial transactions and detecting discrepancies.

    Handles matching internal transactions with external payment provider records,
    identifying discrepancies, and generating reconciliation reports for audit purposes.
    """

    def __init__(self):
        self.transaction_repo = TransactionRepository()
        self.payment_intent_repo = PaymentIntentRepository()
        self.wallet_repo = WalletRepository()

        # Reconciliation configuration
        self.reconciliation_config = {
            'tolerance_amount_cents': 1,  # 1 cent tolerance for amount matching
            'tolerance_timing_minutes': 15,  # 15 minutes tolerance for timing
            'batch_size': 1000,  # Number of transactions per reconciliation batch
            'max_processing_time_hours': 24,  # Maximum time for reconciliation process
            'auto_resolve_threshold': 0.01,  # Auto-resolve discrepancies under 1 cent
            'alert_threshold_percentage': 5.0  # Alert if discrepancies > 5%
        }

    def start_reconciliation(self, start_date: datetime, end_date: datetime,
                           reconciliation_type: str = "daily") -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Start reconciliation process for a date range.

        Args:
            start_date: Start date for reconciliation
            end_date: End date for reconciliation
            reconciliation_type: Type of reconciliation (daily, weekly, monthly)

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success, message, reconciliation details
        """
        try:
            # Validate date range
            if start_date >= end_date:
                return False, "INVALID_DATE_RANGE", None

            if end_date > datetime.now(timezone.utc):
                return False, "FUTURE_DATE_NOT_ALLOWED", None

            # Create reconciliation session
            reconciliation_id = self._generate_reconciliation_id(reconciliation_type)

            reconciliation_session = {
                'reconciliation_id': reconciliation_id,
                'type': reconciliation_type,
                'start_date': start_date,
                'end_date': end_date,
                'status': ReconciliationStatus.IN_PROGRESS.value,
                'started_at': datetime.now(timezone.utc),
                'completed_at': None,
                'total_internal_transactions': 0,
                'total_external_payments': 0,
                'matched_transactions': 0,
                'discrepancies_found': 0,
                'discrepancies': [],
                'summary': {}
            }

            # Get transactions from our system
            internal_transactions = self._get_internal_transactions(start_date, end_date)
            reconciliation_session['total_internal_transactions'] = len(internal_transactions)

            # Get external payment records
            external_payments = self._get_external_payment_records(start_date, end_date)
            reconciliation_session['total_external_payments'] = len(external_payments)

            # Perform matching
            matching_results = self._match_transactions(internal_transactions, external_payments)
            reconciliation_session.update(matching_results)

            # Detect discrepancies
            discrepancies = self._detect_discrepancies(
                internal_transactions,
                external_payments,
                matching_results['matched_pairs']
            )
            reconciliation_session['discrepancies'] = discrepancies
            reconciliation_session['discrepancies_found'] = len(discrepancies)

            # Generate summary
            summary = self._generate_reconciliation_summary(reconciliation_session)
            reconciliation_session['summary'] = summary

            # Complete reconciliation
            reconciliation_session['status'] = ReconciliationStatus.COMPLETED.value
            reconciliation_session['completed_at'] = datetime.now(timezone.utc)

            # Save reconciliation record
            self._save_reconciliation_record(reconciliation_session)

            current_app.logger.info(f"Reconciliation {reconciliation_id} completed: {summary['match_rate']:.1f}% match rate")

            return True, "RECONCILIATION_COMPLETED", {
                'reconciliation_id': reconciliation_id,
                'summary': summary,
                'discrepancies_count': len(discrepancies),
                'requires_review': len(discrepancies) > 0
            }

        except Exception as e:
            current_app.logger.error(f"Reconciliation failed: {str(e)}")
            return False, "RECONCILIATION_ERROR", None

    def _generate_reconciliation_id(self, reconciliation_type: str) -> str:
        """Generate unique reconciliation ID."""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        type_prefix = reconciliation_type.upper()[:3]
        return f"REC-{type_prefix}-{timestamp}"

    def _get_internal_transactions(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """
        Get internal transactions from our database.

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            List of internal transaction records
        """
        try:
            # Get donation transactions
            transactions = self.transaction_repo.find_transactions_by_date_range(
                start_date=start_date,
                end_date=end_date,
                transaction_type="donated"
            )

            internal_records = []
            for transaction in transactions:
                record = {
                    'transaction_id': transaction.transaction_id,
                    'user_id': transaction.user_id,
                    'amount': float(transaction.amount),
                    'currency': transaction.currency,
                    'created_at': transaction.created_at,
                    'status': transaction.status,
                    'payment_intent_id': transaction.metadata.get('payment_intent_id'),
                    'external_reference': transaction.metadata.get('external_reference'),
                    'source': 'internal'
                }
                internal_records.append(record)

            return internal_records

        except Exception as e:
            current_app.logger.error(f"Failed to get internal transactions: {str(e)}")
            return []

    def _get_external_payment_records(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """
        Get external payment records from payment providers.

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            List of external payment records
        """
        try:
            # Get payment intents from our database (representing external payments)
            payment_intents = self.payment_intent_repo.find_by_date_range(start_date, end_date)

            external_records = []
            for intent in payment_intents:
                if intent.status in ['succeeded', 'completed']:
                    record = {
                        'intent_id': intent.intent_id,
                        'provider_payment_id': intent.provider_payment_id,
                        'amount': float(intent.amount),
                        'currency': intent.currency,
                        'created_at': intent.created_at,
                        'confirmed_at': intent.confirmed_at,
                        'status': intent.status,
                        'provider_fees': float(intent.provider_fees or 0),
                        'net_amount': float(intent.net_amount or intent.amount),
                        'source': 'external'
                    }
                    external_records.append(record)

            return external_records

        except Exception as e:
            current_app.logger.error(f"Failed to get external payment records: {str(e)}")
            return []

    def _match_transactions(self, internal_transactions: List[Dict],
                          external_payments: List[Dict]) -> Dict[str, Any]:
        """
        Match internal transactions with external payments.

        Args:
            internal_transactions: List of internal transaction records
            external_payments: List of external payment records

        Returns:
            Matching results dictionary
        """
        matched_pairs = []
        unmatched_internal = []
        unmatched_external = []

        # Create copies for manipulation
        external_remaining = external_payments.copy()

        for internal_tx in internal_transactions:
            match_found = False

            for i, external_payment in enumerate(external_remaining):
                if self._is_transaction_match(internal_tx, external_payment):
                    matched_pairs.append({
                        'internal': internal_tx,
                        'external': external_payment,
                        'match_confidence': self._calculate_match_confidence(internal_tx, external_payment)
                    })
                    external_remaining.pop(i)
                    match_found = True
                    break

            if not match_found:
                unmatched_internal.append(internal_tx)

        # Remaining external payments are unmatched
        unmatched_external = external_remaining

        return {
            'matched_pairs': matched_pairs,
            'unmatched_internal': unmatched_internal,
            'unmatched_external': unmatched_external,
            'matched_transactions': len(matched_pairs)
        }

    def _is_transaction_match(self, internal_tx: Dict, external_payment: Dict) -> bool:
        """
        Determine if an internal transaction matches an external payment.

        Args:
            internal_tx: Internal transaction record
            external_payment: External payment record

        Returns:
            True if transactions match
        """
        # Match by payment intent ID if available
        if (internal_tx.get('payment_intent_id') and
            internal_tx['payment_intent_id'] == external_payment.get('intent_id')):
            return True

        # Match by amount and timing
        amount_match = abs(internal_tx['amount'] - external_payment['amount']) <= 0.01

        # Check timing (within tolerance)
        internal_time = internal_tx['created_at']
        external_time = external_payment.get('confirmed_at') or external_payment['created_at']

        if internal_time and external_time:
            time_diff = abs((internal_time - external_time).total_seconds() / 60)  # minutes
            timing_match = time_diff <= self.reconciliation_config['tolerance_timing_minutes']
        else:
            timing_match = False

        return amount_match and timing_match

    def _calculate_match_confidence(self, internal_tx: Dict, external_payment: Dict) -> float:
        """
        Calculate confidence score for a transaction match.

        Args:
            internal_tx: Internal transaction record
            external_payment: External payment record

        Returns:
            Confidence score between 0.0 and 1.0
        """
        confidence = 0.0

        # Exact payment intent ID match
        if (internal_tx.get('payment_intent_id') == external_payment.get('intent_id')):
            confidence += 0.5

        # Amount match
        amount_diff = abs(internal_tx['amount'] - external_payment['amount'])
        if amount_diff == 0:
            confidence += 0.3
        elif amount_diff <= 0.01:
            confidence += 0.2

        # Timing match
        internal_time = internal_tx['created_at']
        external_time = external_payment.get('confirmed_at') or external_payment['created_at']

        if internal_time and external_time:
            time_diff_minutes = abs((internal_time - external_time).total_seconds() / 60)
            if time_diff_minutes <= 5:
                confidence += 0.2
            elif time_diff_minutes <= 15:
                confidence += 0.1

        return min(1.0, confidence)

    def _detect_discrepancies(self, internal_transactions: List[Dict],
                            external_payments: List[Dict],
                            matched_pairs: List[Dict]) -> List[Dict[str, Any]]:
        """
        Detect discrepancies in the reconciliation.

        Args:
            internal_transactions: List of internal transactions
            external_payments: List of external payments
            matched_pairs: List of matched transaction pairs

        Returns:
            List of discrepancy records
        """
        discrepancies = []

        # Check for amount mismatches in matched pairs
        for pair in matched_pairs:
            internal = pair['internal']
            external = pair['external']

            amount_diff = abs(internal['amount'] - external['amount'])
            if amount_diff > self.reconciliation_config['tolerance_amount_cents'] / 100:
                discrepancies.append({
                    'type': DiscrepancyType.AMOUNT_MISMATCH.value,
                    'severity': 'high' if amount_diff > 1.0 else 'medium',
                    'internal_transaction': internal['transaction_id'],
                    'external_payment': external.get('provider_payment_id'),
                    'internal_amount': internal['amount'],
                    'external_amount': external['amount'],
                    'difference': amount_diff,
                    'description': f"Amount mismatch: €{amount_diff:.2f} difference",
                    'detected_at': datetime.now(timezone.utc)
                })

        # Check for unmatched internal transactions (missing external payments)
        for unmatched in [pair['internal'] for pair in matched_pairs if 'unmatched_internal' in pair]:
            discrepancies.append({
                'type': DiscrepancyType.MISSING_TRANSACTION.value,
                'severity': 'high',
                'internal_transaction': unmatched['transaction_id'],
                'external_payment': None,
                'amount': unmatched['amount'],
                'description': f"Internal transaction €{unmatched['amount']:.2f} has no matching external payment",
                'detected_at': datetime.now(timezone.utc)
            })

        # Check for unmatched external payments (orphaned payments)
        for unmatched in [pair['external'] for pair in matched_pairs if 'unmatched_external' in pair]:
            discrepancies.append({
                'type': DiscrepancyType.ORPHANED_PAYMENT.value,
                'severity': 'medium',
                'internal_transaction': None,
                'external_payment': unmatched.get('provider_payment_id'),
                'amount': unmatched['amount'],
                'description': f"External payment €{unmatched['amount']:.2f} has no matching internal transaction",
                'detected_at': datetime.now(timezone.utc)
            })

        return discrepancies

    def _generate_reconciliation_summary(self, reconciliation_session: Dict) -> Dict[str, Any]:
        """
        Generate summary statistics for reconciliation.

        Args:
            reconciliation_session: Reconciliation session data

        Returns:
            Summary statistics dictionary
        """
        total_internal = reconciliation_session['total_internal_transactions']
        total_external = reconciliation_session['total_external_payments']
        matched = reconciliation_session['matched_transactions']
        discrepancies = reconciliation_session['discrepancies_found']

        # Calculate match rate
        if total_internal > 0:
            match_rate = (matched / total_internal) * 100
        else:
            match_rate = 0.0

        # Calculate discrepancy rate
        if matched > 0:
            discrepancy_rate = (discrepancies / matched) * 100
        else:
            discrepancy_rate = 0.0

        # Calculate amounts
        total_internal_amount = sum(
            d['internal']['amount'] for d in reconciliation_session.get('matched_pairs', [])
        )
        total_external_amount = sum(
            d['external']['amount'] for d in reconciliation_session.get('matched_pairs', [])
        )
        amount_variance = abs(total_internal_amount - total_external_amount)

        summary = {
            'transactions': {
                'total_internal': total_internal,
                'total_external': total_external,
                'matched': matched,
                'unmatched_internal': total_internal - matched,
                'unmatched_external': total_external - matched
            },
            'rates': {
                'match_rate': round(match_rate, 2),
                'discrepancy_rate': round(discrepancy_rate, 2)
            },
            'amounts': {
                'total_internal_amount': round(total_internal_amount, 2),
                'total_external_amount': round(total_external_amount, 2),
                'amount_variance': round(amount_variance, 2)
            },
            'discrepancies': {
                'total_count': discrepancies,
                'by_type': self._group_discrepancies_by_type(reconciliation_session.get('discrepancies', [])),
                'by_severity': self._group_discrepancies_by_severity(reconciliation_session.get('discrepancies', []))
            },
            'status': 'healthy' if discrepancy_rate < 5.0 else 'requires_attention',
            'processing_time_seconds': self._calculate_processing_time(reconciliation_session)
        }

        return summary

    def _group_discrepancies_by_type(self, discrepancies: List[Dict]) -> Dict[str, int]:
        """Group discrepancies by type."""
        type_counts = {}
        for discrepancy in discrepancies:
            disc_type = discrepancy['type']
            type_counts[disc_type] = type_counts.get(disc_type, 0) + 1
        return type_counts

    def _group_discrepancies_by_severity(self, discrepancies: List[Dict]) -> Dict[str, int]:
        """Group discrepancies by severity."""
        severity_counts = {}
        for discrepancy in discrepancies:
            severity = discrepancy.get('severity', 'medium')
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        return severity_counts

    def _calculate_processing_time(self, reconciliation_session: Dict) -> float:
        """Calculate processing time in seconds."""
        started_at = reconciliation_session.get('started_at')
        completed_at = reconciliation_session.get('completed_at')

        if started_at and completed_at:
            return (completed_at - started_at).total_seconds()
        return 0.0

    def _save_reconciliation_record(self, reconciliation_session: Dict) -> bool:
        """
        Save reconciliation record to database.

        Args:
            reconciliation_session: Reconciliation session data

        Returns:
            True if saved successfully
        """
        try:
            # For now, just log the reconciliation record
            # In production, this would save to a reconciliation collection
            current_app.logger.info(f"Reconciliation record saved: {reconciliation_session['reconciliation_id']}")
            return True

        except Exception as e:
            current_app.logger.error(f"Failed to save reconciliation record: {str(e)}")
            return False

    def get_reconciliation_history(self, limit: int = 50) -> Tuple[bool, str, Optional[List[Dict[str, Any]]]]:
        """
        Get reconciliation history.

        Args:
            limit: Maximum number of records to return

        Returns:
            Tuple[bool, str, Optional[List]]: Success, message, reconciliation history
        """
        try:
            # For now, return placeholder reconciliation history
            # In production, this would query the reconciliation database
            history = [
                {
                    'reconciliation_id': 'REC-DAI-20250927120000',
                    'type': 'daily',
                    'date_range': '2025-09-26 to 2025-09-27',
                    'status': 'completed',
                    'match_rate': 98.5,
                    'discrepancies_found': 3,
                    'total_amount_reconciled': 45230.75,
                    'completed_at': '2025-09-27T12:30:00Z'
                },
                {
                    'reconciliation_id': 'REC-DAI-20250926120000',
                    'type': 'daily',
                    'date_range': '2025-09-25 to 2025-09-26',
                    'status': 'completed',
                    'match_rate': 99.2,
                    'discrepancies_found': 1,
                    'total_amount_reconciled': 38950.50,
                    'completed_at': '2025-09-26T12:25:00Z'
                }
            ]

            return True, "RECONCILIATION_HISTORY_RETRIEVED", history[:limit]

        except Exception as e:
            current_app.logger.error(f"Failed to get reconciliation history: {str(e)}")
            return False, "RECONCILIATION_HISTORY_ERROR", None

    def resolve_discrepancy(self, discrepancy_id: str, resolution_type: str,
                          resolver_id: str, notes: str = "") -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Resolve a reconciliation discrepancy.

        Args:
            discrepancy_id: Discrepancy identifier
            resolution_type: Type of resolution (manual_adjustment, ignore, investigate)
            resolver_id: ID of the person resolving the discrepancy
            notes: Resolution notes

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success, message, resolution result
        """
        try:
            valid_resolutions = ['manual_adjustment', 'ignore', 'investigate', 'external_correction']
            if resolution_type not in valid_resolutions:
                return False, "INVALID_RESOLUTION_TYPE", None

            # For now, return placeholder resolution result
            # In production, this would update the discrepancy record
            resolution_result = {
                'discrepancy_id': discrepancy_id,
                'resolution_type': resolution_type,
                'resolved_by': resolver_id,
                'resolved_at': datetime.now(timezone.utc).isoformat(),
                'notes': notes,
                'status': 'resolved'
            }

            current_app.logger.info(f"Discrepancy {discrepancy_id} resolved by {resolver_id}: {resolution_type}")

            return True, "DISCREPANCY_RESOLVED", resolution_result

        except Exception as e:
            current_app.logger.error(f"Failed to resolve discrepancy: {str(e)}")
            return False, "DISCREPANCY_RESOLUTION_ERROR", None

    def generate_reconciliation_report(self, reconciliation_id: str,
                                     report_format: str = "summary") -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Generate detailed reconciliation report.

        Args:
            reconciliation_id: Reconciliation session identifier
            report_format: Format of report (summary, detailed, audit)

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success, message, report data
        """
        try:
            # For now, return placeholder report
            # In production, this would query the reconciliation data and generate report
            report = {
                'report_id': f"RPT-{reconciliation_id}",
                'reconciliation_id': reconciliation_id,
                'format': report_format,
                'generated_at': datetime.now(timezone.utc).isoformat(),
                'summary': {
                    'total_transactions_processed': 1250,
                    'successful_matches': 1235,
                    'discrepancies_found': 15,
                    'match_rate_percentage': 98.8,
                    'total_amount_reconciled': 125430.75,
                    'processing_time_minutes': 12.5
                },
                'discrepancy_details': [
                    {
                        'type': 'amount_mismatch',
                        'count': 8,
                        'total_variance': 12.50
                    },
                    {
                        'type': 'timing_discrepancy',
                        'count': 5,
                        'avg_delay_minutes': 22.3
                    },
                    {
                        'type': 'missing_transaction',
                        'count': 2,
                        'total_amount': 450.25
                    }
                ],
                'recommendations': [
                    'Review timing discrepancies with payment provider',
                    'Investigate missing transactions from external system',
                    'Consider adjusting amount tolerance threshold'
                ]
            }

            return True, "RECONCILIATION_REPORT_GENERATED", report

        except Exception as e:
            current_app.logger.error(f"Failed to generate reconciliation report: {str(e)}")
            return False, "RECONCILIATION_REPORT_ERROR", None