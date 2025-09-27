from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone, timedelta
from flask import current_app
import asyncio
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from app.donations.repositories.wallet_repository import WalletRepository
from app.donations.repositories.batch_operation_repository import BatchOperationRepository
from app.donations.repositories.batch_donation_repository import BatchDonationRepository
from app.donations.models.batch_operation import BatchOperation, BatchOperationType, BatchOperationStatus
from app.donations.models.batch_donation import BatchDonation, BatchDonationStatus
from app.donations.services.wallet_service import WalletService
from app.donations.services.fraud_prevention_service import FraudPreventionService


class BatchProcessingService:
    """
    Service for batch processing of donations and other operations.

    Handles concurrent processing of multiple donations with error handling,
    retry mechanisms, and progress tracking. Supports different batch operation types.
    """

    def __init__(self):
        self.wallet_repo = WalletRepository()
        self.wallet_service = WalletService()
        self.fraud_service = FraudPreventionService()
        self.batch_repo = BatchOperationRepository()
        self.batch_donation_repo = BatchDonationRepository()

        # Processing configuration
        self.max_concurrent_workers = 5
        self.default_batch_size = 50
        self.max_batch_size = 500
        self.retry_delay_seconds = 30

    def create_batch_donation_operation(self, donations: List[Dict[str, Any]],
                                      created_by: str = None,
                                      configuration: Dict[str, Any] = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Create a batch donation operation.

        Args:
            donations: List of donation dictionaries
            created_by: User or system creating the batch
            configuration: Optional batch configuration

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success, message, batch operation data
        """
        try:
            # Validate input
            if not donations or len(donations) == 0:
                return False, "BATCH_DONATIONS_REQUIRED", None

            if len(donations) > self.max_batch_size:
                return False, "BATCH_SIZE_TOO_LARGE", None

            # Validate each donation
            validated_donations = []
            validation_errors = []

            for i, donation_data in enumerate(donations):
                validation_result = self._validate_donation_data(donation_data, i)
                if validation_result['is_valid']:
                    validated_donations.append(validation_result['donation'])
                else:
                    validation_errors.extend(validation_result['errors'])

            if validation_errors:
                return False, "BATCH_VALIDATION_FAILED", {
                    'validation_errors': validation_errors,
                    'valid_donations': len(validated_donations),
                    'invalid_donations': len(donations) - len(validated_donations)
                }

            # Create batch operation
            batch_config = configuration or {}
            batch_operation = BatchOperation(
                operation_type=BatchOperationType.DONATIONS,
                total_items=len(validated_donations),
                created_by=created_by,
                batch_size=batch_config.get('batch_size', self.default_batch_size),
                max_retries=batch_config.get('max_retries', 3),
                priority=batch_config.get('priority', 1),
                configuration=batch_config,
                metadata={
                    'donation_count': len(validated_donations),
                    'total_amount': sum(d.amount for d in validated_donations),
                    'unique_users': len(set(d.user_id for d in validated_donations)),
                    'unique_onlus': len(set(d.onlus_id for d in validated_donations))
                }
            )

            # Save batch operation
            batch_id = self.batch_repo.create_batch_operation(batch_operation)

            # Save batch donations
            for order, donation in enumerate(validated_donations):
                donation.batch_id = batch_operation.batch_id
                donation.processing_order = order

            # Bulk insert batch donations
            self.batch_donation_repo.create_batch_donations(validated_donations)

            current_app.logger.info(f"Created batch donation operation {batch_id} with {len(validated_donations)} donations")

            return True, "BATCH_OPERATION_CREATED", {
                'batch_id': batch_id,
                'total_donations': len(validated_donations),
                'total_amount': batch_operation.metadata['total_amount'],
                'estimated_processing_time': self._estimate_processing_time(len(validated_donations))
            }

        except Exception as e:
            current_app.logger.error(f"Failed to create batch donation operation: {str(e)}")
            return False, "BATCH_CREATION_ERROR", None

    def _validate_donation_data(self, donation_data: Dict[str, Any], index: int) -> Dict[str, Any]:
        """
        Validate individual donation data.

        Args:
            donation_data: Donation data dictionary
            index: Index in the batch for error reporting

        Returns:
            Validation result dictionary
        """
        errors = []

        # Required fields validation
        required_fields = ['user_id', 'onlus_id', 'amount']
        for field in required_fields:
            if field not in donation_data or not donation_data[field]:
                errors.append(f"Item {index}: Missing required field '{field}'")

        if errors:
            return {'is_valid': False, 'errors': errors, 'donation': None}

        try:
            # Amount validation
            amount = float(donation_data['amount'])
            if amount <= 0:
                errors.append(f"Item {index}: Amount must be positive")
            if amount > 10000:  # Max single donation
                errors.append(f"Item {index}: Amount exceeds maximum (€10,000)")

            # Create BatchDonation object
            batch_donation = BatchDonation(
                batch_id="",  # Will be set later
                user_id=str(donation_data['user_id']),
                onlus_id=str(donation_data['onlus_id']),
                amount=amount,
                donation_message=donation_data.get('message', ''),
                is_anonymous=donation_data.get('is_anonymous', False),
                source_reference=donation_data.get('source_reference'),
                metadata=donation_data.get('metadata', {})
            )

            # Validation passed
            batch_donation.clear_validation_errors()

            return {
                'is_valid': True,
                'errors': [],
                'donation': batch_donation
            }

        except (ValueError, TypeError) as e:
            errors.append(f"Item {index}: Invalid data format - {str(e)}")
            return {'is_valid': False, 'errors': errors, 'donation': None}

    def process_batch_donations(self, batch_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Process batch donations concurrently.

        Args:
            batch_id: Batch operation ID

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success, message, results
        """
        try:
            # Get batch operation
            batch_operation = self.batch_repo.find_by_batch_id(batch_id)
            if not batch_operation:
                return False, "BATCH_OPERATION_NOT_FOUND", None

            if batch_operation.is_processing():
                return False, "BATCH_ALREADY_PROCESSING", None

            if batch_operation.is_completed():
                return False, "BATCH_ALREADY_COMPLETED", None

            # Get batch donations
            batch_donations = self.batch_donation_repo.find_by_batch_id(batch_id)
            if not batch_donations:
                return False, "BATCH_DONATIONS_NOT_FOUND", None

            # Start processing
            batch_operation.start_processing(worker_id="batch_processor_1")
            self.batch_repo.update_batch_operation(batch_operation.batch_id, {
                'status': batch_operation.status,
                'started_at': batch_operation.started_at,
                'worker_id': batch_operation.worker_id
            })

            # Process donations in concurrent batches
            results = self._process_donations_concurrently(batch_operation, batch_donations)

            # Update final batch status
            success_count = results['successful_items']
            failed_count = results['failed_items']

            batch_operation.update_progress(
                processed_count=len(batch_donations),
                successful_count=success_count,
                failed_count=failed_count
            )

            # Complete the operation
            batch_operation.complete_operation(
                success=(failed_count == 0),
                results_summary=results
            )

            self.batch_repo.update_batch_operation(batch_operation.batch_id, {
                'status': batch_operation.status,
                'completed_at': batch_operation.completed_at,
                'processed_items': batch_operation.processed_items,
                'successful_items': batch_operation.successful_items,
                'failed_items': batch_operation.failed_items,
                'progress_percentage': batch_operation.progress_percentage,
                'results_summary': batch_operation.results_summary
            })

            current_app.logger.info(f"Completed batch processing {batch_id}: {success_count} successful, {failed_count} failed")

            return True, "BATCH_PROCESSING_COMPLETED", {
                'batch_id': batch_id,
                'results': results,
                'final_status': batch_operation.status
            }

        except Exception as e:
            current_app.logger.error(f"Failed to process batch donations {batch_id}: {str(e)}")

            # Mark batch as failed
            if 'batch_operation' in locals():
                batch_operation.complete_operation(success=False)
                self.batch_repo.add_error_log(
                    batch_operation.batch_id,
                    f"Processing failed: {str(e)}"
                )
                self.batch_repo.update_batch_operation(batch_operation.batch_id, {
                    'status': BatchOperationStatus.FAILED
                })

            return False, "BATCH_PROCESSING_ERROR", None

    def _process_donations_concurrently(self, batch_operation: BatchOperation,
                                      batch_donations: List[BatchDonation]) -> Dict[str, Any]:
        """
        Process donations using concurrent workers.

        Args:
            batch_operation: BatchOperation instance
            batch_donations: List of BatchDonation instances

        Returns:
            Processing results dictionary
        """
        successful_items = 0
        failed_items = 0
        skipped_items = 0
        processing_start = time.time()

        # Sort donations by processing order
        sorted_donations = sorted(batch_donations, key=lambda x: x.processing_order)

        # Process in batches using ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=self.max_concurrent_workers) as executor:
            # Submit all donations for processing
            future_to_donation = {
                executor.submit(self._process_single_donation, donation): donation
                for donation in sorted_donations
            }

            # Process completed futures
            processed_count = 0
            for future in as_completed(future_to_donation):
                donation = future_to_donation[future]

                try:
                    result = future.result()
                    processed_count += 1

                    # Update counters based on result
                    if result['success']:
                        successful_items += 1
                    elif result['skipped']:
                        skipped_items += 1
                    else:
                        failed_items += 1
                        self.batch_repo.add_error_log(
                            batch_operation.batch_id,
                            result['error_message'],
                            item_id=donation.item_id,
                            error_details=result.get('error_details', {})
                        )
                        batch_operation.error_count += 1

                    # Update progress every 10 items or at completion
                    if processed_count % 10 == 0 or processed_count == len(sorted_donations):
                        batch_operation.update_progress(
                            processed_count=processed_count,
                            successful_count=successful_items,
                            failed_count=failed_items
                        )
                        self.batch_repo.update_progress(
                            batch_operation.batch_id,
                            processed_count,
                            successful_items,
                            failed_items
                        )

                        current_app.logger.info(
                            f"Batch {batch_operation.batch_id} progress: "
                            f"{processed_count}/{len(sorted_donations)} processed"
                        )

                except Exception as e:
                    current_app.logger.error(f"Error processing donation {donation.item_id}: {str(e)}")
                    failed_items += 1
                    donation.fail_processing(f"Processing error: {str(e)}")

        processing_duration = time.time() - processing_start

        return {
            'successful_items': successful_items,
            'failed_items': failed_items,
            'skipped_items': skipped_items,
            'total_processed': len(sorted_donations),
            'processing_duration_seconds': round(processing_duration, 2),
            'items_per_second': round(len(sorted_donations) / processing_duration, 2) if processing_duration > 0 else 0,
            'success_rate': round((successful_items / len(sorted_donations)) * 100, 2) if sorted_donations else 0
        }

    def _process_single_donation(self, donation: BatchDonation) -> Dict[str, Any]:
        """
        Process a single donation.

        Args:
            donation: BatchDonation instance

        Returns:
            Processing result dictionary
        """
        try:
            # Start processing
            donation.start_processing()

            # Pre-validation checks
            if not donation.pre_validation_passed:
                donation.skip_processing("Pre-validation failed")
                return {
                    'success': False,
                    'skipped': True,
                    'error_message': "Pre-validation failed",
                    'donation_id': donation.item_id
                }

            # Check user wallet
            wallet = self.wallet_repo.find_by_user_id(donation.user_id)
            if not wallet:
                donation.fail_processing("User wallet not found", "WALLET_NOT_FOUND")
                return {
                    'success': False,
                    'skipped': False,
                    'error_message': "User wallet not found",
                    'donation_id': donation.item_id
                }

            # Check sufficient balance
            if wallet.current_balance < donation.amount:
                donation.fail_processing("Insufficient credits", "INSUFFICIENT_CREDITS")
                return {
                    'success': False,
                    'skipped': False,
                    'error_message': "Insufficient credits",
                    'donation_id': donation.item_id
                }

            # Fraud prevention check
            fraud_check = self.fraud_service.check_donation_fraud(
                user_id=donation.user_id,
                amount=donation.amount,
                onlus_id=donation.onlus_id,
                metadata=donation.metadata
            )

            if not fraud_check['is_safe']:
                donation.fail_processing("Fraud check failed", "FRAUD_DETECTION_TRIGGERED")
                return {
                    'success': False,
                    'skipped': False,
                    'error_message': "Fraud check failed",
                    'error_details': fraud_check,
                    'donation_id': donation.item_id
                }

            # Process the donation
            success, message, result = self.wallet_service.process_donation(
                user_id=donation.user_id,
                amount=donation.amount,
                onlus_id=donation.onlus_id,
                metadata={
                    'batch_id': donation.batch_id,
                    'item_id': donation.item_id,
                    'message': donation.donation_message,
                    'is_anonymous': donation.is_anonymous,
                    'source': 'batch_processing',
                    **donation.metadata
                }
            )

            if success and result:
                # Mark as completed
                donation.complete_processing(
                    transaction_id=result.get('transaction_id'),
                    processed_amount=donation.amount,
                    processing_fee=0.0  # No additional fees for batch processing
                )

                return {
                    'success': True,
                    'skipped': False,
                    'transaction_id': result.get('transaction_id'),
                    'donation_id': donation.item_id
                }
            else:
                # Mark as failed
                donation.fail_processing(message or "Donation processing failed", "DONATION_PROCESSING_FAILED")
                return {
                    'success': False,
                    'skipped': False,
                    'error_message': message or "Donation processing failed",
                    'donation_id': donation.item_id
                }

        except Exception as e:
            current_app.logger.error(f"Error processing single donation {donation.item_id}: {str(e)}")
            donation.fail_processing(f"Processing error: {str(e)}", "PROCESSING_EXCEPTION")
            return {
                'success': False,
                'skipped': False,
                'error_message': f"Processing error: {str(e)}",
                'donation_id': donation.item_id
            }

    def get_batch_status(self, batch_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Get batch operation status and progress.

        Args:
            batch_id: Batch operation ID

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success, message, batch status data
        """
        try:
            batch_operation = self.batch_repo.find_by_batch_id(batch_id)
            if not batch_operation:
                return False, "BATCH_OPERATION_NOT_FOUND", None

            batch_donations = self.batch_donation_repo.find_by_batch_id(batch_id)

            # Prepare detailed status
            status_data = batch_operation.to_api_dict()

            # Add donation-specific information
            status_data['donations'] = {
                'total_count': len(batch_donations),
                'by_status': self._get_donations_by_status(batch_donations),
                'recent_errors': [
                    {
                        'item_id': d.item_id,
                        'error_message': d.error_message,
                        'error_code': d.error_code,
                        'updated_at': d.updated_at
                    }
                    for d in batch_donations
                    if d.status == BatchDonationStatus.FAILED
                ][-10:]  # Last 10 errors
            }

            return True, "BATCH_STATUS_RETRIEVED", status_data

        except Exception as e:
            current_app.logger.error(f"Failed to get batch status {batch_id}: {str(e)}")
            return False, "BATCH_STATUS_ERROR", None

    def _get_donations_by_status(self, batch_donations: List[BatchDonation]) -> Dict[str, int]:
        """
        Get count of donations by status.

        Args:
            batch_donations: List of BatchDonation instances

        Returns:
            Dictionary with status counts
        """
        status_counts = {}
        for donation in batch_donations:
            status = donation.status
            status_counts[status] = status_counts.get(status, 0) + 1

        return status_counts

    def retry_failed_items(self, batch_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Retry failed items in a batch operation.

        Args:
            batch_id: Batch operation ID

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success, message, retry results
        """
        try:
            batch_operation = self.batch_repo.find_by_batch_id(batch_id)
            if not batch_operation:
                return False, "BATCH_OPERATION_NOT_FOUND", None

            if not batch_operation.can_be_retried():
                return False, "BATCH_CANNOT_BE_RETRIED", None

            # Get failed donations that can be retried
            failed_donations = self.batch_donation_repo.find_retryable_items(batch_id)

            if not failed_donations:
                return False, "NO_ITEMS_TO_RETRY", None

            # Reset batch operation for retry
            batch_operation.status = BatchOperationStatus.PROCESSING
            batch_operation.failed_items = len(failed_donations)
            batch_operation.last_updated_at = datetime.now(timezone.utc)

            # Process failed donations
            results = self._process_donations_concurrently(batch_operation, failed_donations)

            # Update batch operation
            batch_operation.complete_operation(
                success=(results['failed_items'] == 0),
                results_summary={**batch_operation.results_summary, 'retry_results': results}
            )

            self.batch_repo.update_batch_operation(batch_operation.batch_id, {
                'status': batch_operation.status,
                'completed_at': batch_operation.completed_at,
                'results_summary': batch_operation.results_summary
            })

            current_app.logger.info(f"Retried batch {batch_id}: {results['successful_items']} successful, {results['failed_items']} failed")

            return True, "BATCH_RETRY_COMPLETED", {
                'batch_id': batch_id,
                'retry_results': results,
                'items_retried': len(failed_donations)
            }

        except Exception as e:
            current_app.logger.error(f"Failed to retry batch items {batch_id}: {str(e)}")
            return False, "BATCH_RETRY_ERROR", None

    def _estimate_processing_time(self, donation_count: int) -> Dict[str, Any]:
        """
        Estimate processing time for a batch.

        Args:
            donation_count: Number of donations to process

        Returns:
            Time estimation dictionary
        """
        # Base processing time per donation (seconds)
        base_time_per_donation = 0.5

        # Account for concurrency
        effective_workers = min(self.max_concurrent_workers, donation_count)
        estimated_seconds = (donation_count * base_time_per_donation) / effective_workers

        return {
            'estimated_duration_seconds': round(estimated_seconds, 1),
            'estimated_duration_minutes': round(estimated_seconds / 60, 1),
            'concurrent_workers': effective_workers,
            'items_per_worker': round(donation_count / effective_workers, 1)
        }

    def cancel_batch_operation(self, batch_id: str, reason: str = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Cancel a batch operation.

        Args:
            batch_id: Batch operation ID
            reason: Cancellation reason

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success, message, cancellation result
        """
        try:
            batch_operation = self.batch_repo.find_by_batch_id(batch_id)
            if not batch_operation:
                return False, "BATCH_OPERATION_NOT_FOUND", None

            if batch_operation.is_completed():
                return False, "BATCH_ALREADY_COMPLETED", None

            # Cancel the operation
            batch_operation.cancel_operation(reason or "Cancelled by request")
            self.batch_repo.update_batch_operation(batch_operation.batch_id, {
                'status': batch_operation.status,
                'completed_at': batch_operation.completed_at,
                'cancellation_reason': reason or "Cancelled by request"
            })

            current_app.logger.info(f"Cancelled batch operation {batch_id}: {reason}")

            return True, "BATCH_OPERATION_CANCELLED", {
                'batch_id': batch_id,
                'cancelled_at': batch_operation.completed_at,
                'reason': reason
            }

        except Exception as e:
            current_app.logger.error(f"Failed to cancel batch operation {batch_id}: {str(e)}")
            return False, "BATCH_CANCELLATION_ERROR", None