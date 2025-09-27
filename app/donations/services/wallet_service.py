from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
from flask import current_app
from app.donations.repositories.wallet_repository import WalletRepository
from app.donations.repositories.transaction_repository import TransactionRepository
from app.donations.models.wallet import Wallet
from app.donations.models.transaction import Transaction, TransactionType, SourceType
from app.donations.services.credit_calculation_service import CreditCalculationService


class WalletService:
    """
    Service for wallet management and transaction processing.
    Handles wallet operations, credit management, and auto-donation logic.
    """

    def __init__(self):
        self.wallet_repo = WalletRepository()
        self.transaction_repo = TransactionRepository()
        self.credit_calc_service = CreditCalculationService()

    def get_wallet(self, user_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Get or create user's wallet with current balance and statistics.

        Args:
            user_id: User identifier

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success, message, wallet data
        """
        try:
            wallet = self.wallet_repo.find_by_user_id(user_id)

            if not wallet:
                # Create new wallet for user
                wallet = Wallet(user_id=user_id)
                wallet_id = self.wallet_repo.create_wallet(wallet)
                current_app.logger.info(f"Created new wallet for user {user_id}: {wallet_id}")

            wallet_data = wallet.to_api_dict()
            return True, "WALLET_RETRIEVED_SUCCESS", wallet_data

        except Exception as e:
            current_app.logger.error(f"Failed to get wallet for user {user_id}: {str(e)}")
            return False, "WALLET_RETRIEVAL_ERROR", None

    def add_credits(self, user_id: str, amount: float, source: str,
                   metadata: Dict[str, Any] = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Add credits to user's wallet with transaction logging.

        Args:
            user_id: User identifier
            amount: Amount to add (must be positive)
            source: Source of credits (gameplay, tournament, etc.)
            metadata: Additional transaction metadata

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success, message, transaction data
        """
        try:
            if amount <= 0:
                return False, "AMOUNT_MUST_BE_POSITIVE", None

            # Get or create wallet
            wallet = self.wallet_repo.find_by_user_id(user_id)
            if not wallet:
                wallet = Wallet(user_id=user_id)
                self.wallet_repo.create_wallet(wallet)

            # Create transaction record
            transaction = Transaction.create_earned_transaction(
                user_id=user_id,
                amount=amount,
                source_type=source,
                metadata=metadata or {}
            )

            # Add credits to wallet
            if not wallet.add_credits(amount, 'earned'):
                return False, "CREDITS_ADD_FAILED", None

            # Save transaction and update wallet
            transaction_id = self.transaction_repo.create_transaction(transaction)
            transaction.mark_completed()
            self.transaction_repo.update_transaction(transaction)

            # Update wallet in database
            if not self.wallet_repo.update_wallet(wallet):
                current_app.logger.error(f"Failed to update wallet for user {user_id}")
                return False, "WALLET_UPDATE_FAILED", None

            # Check for auto-donation
            auto_donation_result = self._process_auto_donation_if_eligible(wallet)

            result_data = {
                'transaction_id': transaction.transaction_id,
                'new_balance': wallet.current_balance,
                'amount_added': amount,
                'auto_donation': auto_donation_result
            }

            current_app.logger.info(f"Added {amount}€ credits to user {user_id} wallet. New balance: {wallet.current_balance}€")
            return True, "CREDITS_ADDED_SUCCESS", result_data

        except Exception as e:
            current_app.logger.error(f"Failed to add credits for user {user_id}: {str(e)}")
            return False, "CREDITS_ADD_ERROR", None

    def process_donation(self, user_id: str, amount: float,
                        onlus_id: str, metadata: Dict[str, Any] = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Process a donation from user's wallet credits.

        Args:
            user_id: User identifier
            amount: Donation amount
            onlus_id: ONLUS receiving the donation
            metadata: Additional donation metadata

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success, message, donation data
        """
        try:
            if amount <= 0:
                return False, "AMOUNT_MUST_BE_POSITIVE", None

            # Get wallet
            wallet = self.wallet_repo.find_by_user_id(user_id)
            if not wallet:
                return False, "WALLET_NOT_FOUND", None

            # Check sufficient balance
            if not wallet.can_donate(amount):
                return False, "INSUFFICIENT_CREDITS", None

            # Ensure metadata is a dict
            safe_metadata = metadata or {}

            # Create donation transaction
            transaction = Transaction.create_donation_transaction(
                user_id=user_id,
                amount=amount,
                onlus_id=onlus_id,
                metadata=safe_metadata
            )

            # Deduct credits from wallet
            if not wallet.deduct_credits(amount, 'donated'):
                return False, "DONATION_DEDUCTION_FAILED", None

            # Save transaction and update wallet
            transaction_id = self.transaction_repo.create_transaction(transaction)
            transaction.mark_completed({
                'donation_receipt': f"receipt_{transaction.transaction_id}",
                'tax_deductible': True,
                'onlus_name': safe_metadata.get('onlus_name', 'Unknown')
            })
            self.transaction_repo.update_transaction(transaction)

            # Update wallet in database
            if not self.wallet_repo.update_wallet(wallet):
                current_app.logger.error(f"Failed to update wallet after donation for user {user_id}")
                return False, "WALLET_UPDATE_FAILED", None

            donation_data = {
                'transaction_id': transaction.transaction_id,
                'donation_amount': amount,
                'remaining_balance': wallet.current_balance,
                'onlus_id': onlus_id,
                'receipt': transaction.generate_receipt()
            }

            current_app.logger.info(f"Processed donation of {amount}€ from user {user_id} to ONLUS {onlus_id}")
            return True, "DONATION_SUCCESS", donation_data

        except Exception as e:
            current_app.logger.error(f"Failed to process donation for user {user_id}: {str(e)}")
            return False, "DONATION_ERROR", None

    def process_auto_donation(self, user_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Process auto-donation if user's wallet is eligible.

        Args:
            user_id: User identifier

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success, message, auto-donation data
        """
        try:
            wallet = self.wallet_repo.find_by_user_id(user_id)
            if not wallet:
                return False, "WALLET_NOT_FOUND", None

            auto_donation_result = self._process_auto_donation_if_eligible(wallet)

            if auto_donation_result and auto_donation_result.get('donated'):
                return True, "AUTO_DONATION_SUCCESS", auto_donation_result
            else:
                return True, "AUTO_DONATION_NOT_ELIGIBLE", auto_donation_result

        except Exception as e:
            current_app.logger.error(f"Failed to process auto-donation for user {user_id}: {str(e)}")
            return False, "AUTO_DONATION_ERROR", None

    def get_transaction_history(self, user_id: str, filters: Dict[str, Any] = None,
                               page: int = 1, page_size: int = 20) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Get user's transaction history with pagination and filtering.

        Args:
            user_id: User identifier
            filters: Optional filters (transaction_type, date_range, etc.)
            page: Page number
            page_size: Number of transactions per page

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success, message, transaction history
        """
        try:
            filters = filters or {}
            offset = (page - 1) * page_size

            # Extract filters
            transaction_type = filters.get('transaction_type')
            status = filters.get('status')
            sort_by = filters.get('sort_by', 'created_at')
            sort_order = -1 if filters.get('sort_order', 'desc') == 'desc' else 1

            # Get transactions
            transactions = self.transaction_repo.find_by_user_id(
                user_id=user_id,
                limit=page_size,
                offset=offset,
                transaction_type=transaction_type,
                status=status,
                sort_by=sort_by,
                sort_order=sort_order
            )

            # Convert to API format
            transactions_data = [transaction.to_api_dict() for transaction in transactions]

            # Get total count for pagination
            search_criteria = {'user_id': user_id}
            if transaction_type:
                search_criteria['transaction_type'] = transaction_type
            if status:
                search_criteria['status'] = status

            total_count = self.transaction_repo.count(search_criteria)
            total_pages = (total_count + page_size - 1) // page_size

            history_data = {
                'transactions': transactions_data,
                'pagination': {
                    'current_page': page,
                    'page_size': page_size,
                    'total_count': total_count,
                    'total_pages': total_pages,
                    'has_next': page < total_pages,
                    'has_prev': page > 1
                }
            }

            return True, "TRANSACTION_HISTORY_RETRIEVED_SUCCESS", history_data

        except Exception as e:
            current_app.logger.error(f"Failed to get transaction history for user {user_id}: {str(e)}")
            return False, "TRANSACTION_HISTORY_ERROR", None

    def get_wallet_statistics(self, user_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Get comprehensive wallet statistics for a user.

        Args:
            user_id: User identifier

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success, message, statistics data
        """
        try:
            wallet = self.wallet_repo.find_by_user_id(user_id)
            if not wallet:
                return False, "WALLET_NOT_FOUND", None

            # Get transaction summary
            transaction_summary = self.transaction_repo.get_user_transaction_summary(user_id)

            # Combine wallet and transaction statistics
            statistics = {
                'wallet': wallet.get_statistics(),
                'transactions': transaction_summary,
                'conversion_stats': {
                    'avg_credits_per_session': 0.0,
                    'most_productive_day': None,
                    'total_play_time_minutes': 0
                }
            }

            # Calculate additional stats
            if transaction_summary.get('by_type', {}).get('earned'):
                earned_data = transaction_summary['by_type']['earned']
                if earned_data['count'] > 0:
                    statistics['conversion_stats']['avg_credits_per_session'] = earned_data['avg_amount']

            return True, "WALLET_STATISTICS_SUCCESS", statistics

        except Exception as e:
            current_app.logger.error(f"Failed to get wallet statistics for user {user_id}: {str(e)}")
            return False, "WALLET_STATISTICS_ERROR", None

    def update_auto_donation_settings(self, user_id: str,
                                    settings: Dict[str, Any]) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Update user's auto-donation settings.

        Args:
            user_id: User identifier
            settings: New auto-donation settings

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success, message, updated settings
        """
        try:
            wallet = self.wallet_repo.find_by_user_id(user_id)
            if not wallet:
                return False, "WALLET_NOT_FOUND", None

            # Validate and update settings
            if not wallet.update_auto_donation_settings(settings):
                return False, "AUTO_DONATION_SETTINGS_INVALID", None

            # Save to database
            if not self.wallet_repo.update_wallet(wallet):
                return False, "WALLET_UPDATE_FAILED", None

            updated_settings = wallet.auto_donation_settings
            current_app.logger.info(f"Updated auto-donation settings for user {user_id}")

            return True, "AUTO_DONATION_SETTINGS_UPDATED_SUCCESS", updated_settings

        except Exception as e:
            current_app.logger.error(f"Failed to update auto-donation settings for user {user_id}: {str(e)}")
            return False, "AUTO_DONATION_SETTINGS_UPDATE_ERROR", None

    def convert_session_to_credits(self, session_data: Dict[str, Any],
                                 user_context: Dict[str, Any] = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Convert a game session to credits using the credit calculation service.

        Args:
            session_data: Game session data
            user_context: User context for multiplier calculation

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success, message, conversion result
        """
        try:
            # Calculate credits using credit calculation service
            success, message, calculation_result = self.credit_calc_service.calculate_credits_from_session(
                session_data, user_context
            )

            if not success:
                return False, message, calculation_result

            # Add credits to wallet
            user_id = calculation_result['user_id']
            credits_earned = calculation_result['effective_amount']
            source_type = calculation_result['source_type']

            # Create transaction metadata
            metadata = {
                'game_session_id': calculation_result['game_session_id'],
                'play_duration_ms': int(calculation_result['play_duration_minutes'] * 60 * 1000),
                'multiplier_applied': calculation_result['multiplier_applied'],
                'active_multipliers': calculation_result['active_multipliers'],
                'game_type': calculation_result.get('game_type'),
                'base_rate': calculation_result['base_rate']
            }

            # Add credits to wallet
            add_success, add_message, add_result = self.add_credits(
                user_id=user_id,
                amount=credits_earned,
                source=source_type,
                metadata=metadata
            )

            if not add_success:
                return False, add_message, add_result

            # Combine results
            conversion_result = {
                'credits_calculation': calculation_result,
                'wallet_update': add_result,
                'session_id': session_data.get('session_id')
            }

            return True, "SESSION_CONVERSION_SUCCESS", conversion_result

        except Exception as e:
            current_app.logger.error(f"Failed to convert session to credits: {str(e)}")
            return False, "SESSION_CONVERSION_ERROR", None

    def _process_auto_donation_if_eligible(self, wallet: Wallet) -> Optional[Dict[str, Any]]:
        """
        Process auto-donation if wallet is eligible.

        Args:
            wallet: Wallet instance to check

        Returns:
            Optional[Dict[str, Any]]: Auto-donation result or None
        """
        try:
            if not wallet.should_auto_donate():
                return {'eligible': False, 'donated': False}

            donation_amount = wallet.apply_auto_donation()
            if donation_amount is None or donation_amount <= 0:
                return {'eligible': True, 'donated': False, 'reason': 'calculation_failed'}

            # Get preferred ONLUS
            preferred_onlus = wallet.auto_donation_settings.get('preferred_onlus_id')
            if not preferred_onlus:
                # Use default ONLUS (could be configured)
                preferred_onlus = 'default_onlus'

            # Create donation transaction
            transaction = Transaction.create_donation_transaction(
                user_id=wallet.user_id,
                amount=donation_amount,
                onlus_id=preferred_onlus,
                metadata={'auto_donation': True}
            )

            # Save transaction
            self.transaction_repo.create_transaction(transaction)
            transaction.mark_completed({'auto_donation': True})
            self.transaction_repo.update_transaction(transaction)

            # Update wallet
            self.wallet_repo.update_wallet(wallet)

            current_app.logger.info(f"Auto-donation processed: {donation_amount}€ from user {wallet.user_id}")

            return {
                'eligible': True,
                'donated': True,
                'amount': donation_amount,
                'transaction_id': transaction.transaction_id,
                'onlus_id': preferred_onlus
            }

        except Exception as e:
            current_app.logger.error(f"Auto-donation processing failed for user {wallet.user_id}: {str(e)}")
            return {'eligible': True, 'donated': False, 'error': str(e)}

    def get_donation_receipt(self, user_id: str, transaction_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Get donation receipt for a transaction.

        Args:
            user_id: User identifier
            transaction_id: Transaction identifier

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success, message, receipt data
        """
        try:
            transaction = self.transaction_repo.find_by_transaction_id(transaction_id)
            if not transaction:
                return False, "TRANSACTION_NOT_FOUND", None

            if transaction.user_id != user_id:
                return False, "TRANSACTION_ACCESS_DENIED", None

            if transaction.transaction_type != TransactionType.DONATED.value:
                return False, "TRANSACTION_NOT_DONATION", None

            receipt = transaction.generate_receipt()
            return True, "RECEIPT_RETRIEVED_SUCCESS", receipt

        except Exception as e:
            current_app.logger.error(f"Failed to get donation receipt: {str(e)}")
            return False, "RECEIPT_RETRIEVAL_ERROR", None