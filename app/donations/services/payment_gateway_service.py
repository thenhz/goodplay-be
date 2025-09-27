from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone, timedelta
from flask import current_app
import stripe
import os
from app.donations.repositories.payment_provider_repository import PaymentProviderRepository
from app.donations.repositories.payment_intent_repository import PaymentIntentRepository
from app.donations.repositories.wallet_repository import WalletRepository
from app.donations.models.payment_provider import PaymentProvider, PaymentProviderType
from app.donations.models.payment_intent import PaymentIntent, PaymentIntentStatus, PaymentMethod
from app.donations.services.wallet_service import WalletService


class PaymentGatewayService:
    """
    Service for payment gateway integration and processing.

    Handles payment intent creation, confirmation, webhooks, and refunds.
    Currently supports Stripe with extensible architecture for other providers.
    """

    def __init__(self):
        self.provider_repo = PaymentProviderRepository()
        self.intent_repo = PaymentIntentRepository()
        self.wallet_repo = WalletRepository()
        self.wallet_service = WalletService()

        # Initialize Stripe with test keys for development
        self._initialize_stripe()

    def _initialize_stripe(self) -> None:
        """Initialize Stripe configuration."""
        try:
            # Use test keys for development
            stripe_key = os.getenv('STRIPE_SECRET_KEY', 'sk_test_')
            stripe.api_key = stripe_key

            # Validate Stripe configuration
            if not stripe_key.startswith(('sk_test_', 'sk_live_')):
                current_app.logger.warning("Invalid Stripe API key format")

            current_app.logger.info("Stripe payment gateway initialized")
        except Exception as e:
            current_app.logger.error(f"Failed to initialize Stripe: {str(e)}")

    def create_payment_intent(self, user_id: str, amount: float, currency: str = 'EUR',
                            description: str = None, metadata: Dict[str, Any] = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Create a payment intent for wallet funding.

        Args:
            user_id: User identifier
            amount: Payment amount
            currency: Payment currency
            description: Payment description
            metadata: Additional metadata

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success, message, payment intent data
        """
        try:
            # Validate amount
            if amount < 1.0 or amount > 50000.0:
                return False, "PAYMENT_AMOUNT_INVALID", None

            # Get user's wallet
            wallet = self.wallet_repo.find_by_user_id(user_id)
            if not wallet:
                return False, "WALLET_NOT_FOUND", None

            # Get primary payment provider (Stripe for now)
            provider = self.provider_repo.get_primary_provider(PaymentProviderType.STRIPE)
            if not provider or not provider.is_healthy():
                return False, "PAYMENT_PROVIDER_UNAVAILABLE", None

            # Validate amount against provider limits
            is_valid, error_msg = provider.validate_amount(amount, currency)
            if not is_valid:
                return False, "PAYMENT_AMOUNT_INVALID", None

            # Calculate fees
            processing_fee = provider.calculate_processing_fee(amount)
            net_amount = amount - processing_fee

            # Create PaymentIntent model
            payment_intent = PaymentIntent(
                user_id=user_id,
                wallet_id=wallet.wallet_id,
                amount=amount,
                currency=currency,
                provider_id=provider.provider_id,
                provider_type=provider.provider_type,
                description=description or f"Wallet top-up - {amount} {currency}",
                metadata=metadata or {},
                expires_at=datetime.now(timezone.utc) + timedelta(hours=1)  # 1 hour expiry
            )

            # Calculate fees and update intent
            payment_intent.calculate_fees(
                provider.processing_fee_percentage,
                provider.processing_fee_fixed
            )

            # Create Stripe payment intent
            stripe_intent = self._create_stripe_intent(payment_intent, provider)
            if not stripe_intent:
                return False, "PAYMENT_PROVIDER_ERROR", None

            # Update payment intent with Stripe data
            payment_intent.provider_payment_id = stripe_intent['id']
            payment_intent.client_secret = stripe_intent['client_secret']
            payment_intent.status = PaymentIntentStatus.PENDING

            # Save payment intent to database
            intent_id = self.intent_repo.create_intent(payment_intent)

            # Prepare response data
            intent_data = payment_intent.to_api_dict()

            current_app.logger.info(f"Created payment intent {payment_intent.intent_id} for user {user_id}")
            return True, "PAYMENT_INTENT_CREATED", intent_data

        except Exception as e:
            current_app.logger.error(f"Failed to create payment intent for user {user_id}: {str(e)}")
            return False, "PAYMENT_INTENT_CREATION_FAILED", None

    def _create_stripe_intent(self, payment_intent: PaymentIntent, provider: PaymentProvider) -> Optional[Dict[str, Any]]:
        """
        Create Stripe payment intent.

        Args:
            payment_intent: PaymentIntent instance
            provider: PaymentProvider instance

        Returns:
            Stripe payment intent data or None
        """
        try:
            # Get provider credentials
            credentials = provider.get_credentials()
            if not credentials.get('secret_key'):
                current_app.logger.error("Missing Stripe secret key")
                return None

            # Temporarily set Stripe key for this request
            stripe.api_key = credentials['secret_key']

            # Create Stripe payment intent
            stripe_intent = stripe.PaymentIntent.create(
                amount=int(payment_intent.amount * 100),  # Convert to cents
                currency=payment_intent.currency.lower(),
                description=payment_intent.description,
                metadata={
                    'user_id': payment_intent.user_id,
                    'wallet_id': payment_intent.wallet_id,
                    'intent_id': payment_intent.intent_id,
                    **payment_intent.metadata
                },
                automatic_payment_methods={'enabled': True},
                confirmation_method='automatic',
                capture_method='automatic'
            )

            return stripe_intent

        except stripe.error.StripeError as e:
            current_app.logger.error(f"Stripe error creating payment intent: {str(e)}")
            return None
        except Exception as e:
            current_app.logger.error(f"Error creating Stripe payment intent: {str(e)}")
            return None

    def confirm_payment(self, intent_id: str, payment_method_id: str = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Confirm payment intent and process successful payment.

        Args:
            intent_id: Payment intent identifier
            payment_method_id: Optional payment method ID

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success, message, result data
        """
        try:
            # Find payment intent
            payment_intent = self.intent_repo.find_by_intent_id(intent_id)
            if not payment_intent:
                return False, "PAYMENT_INTENT_NOT_FOUND", None

            # Check if payment can be confirmed
            if not payment_intent.can_be_confirmed():
                return False, "PAYMENT_INTENT_CANNOT_BE_CONFIRMED", None

            # Get provider
            provider = self.provider_repo.find_by_provider_id(payment_intent.provider_id)
            if not provider:
                return False, "PAYMENT_PROVIDER_NOT_FOUND", None

            # Increment confirmation attempt
            if not payment_intent.increment_confirmation_attempt():
                self.intent_repo.update_status(intent_id, PaymentIntentStatus.FAILED,
                                             "Maximum confirmation attempts exceeded")
                return False, "PAYMENT_CONFIRMATION_ATTEMPTS_EXCEEDED", None

            # Confirm with Stripe
            if provider.provider_type == PaymentProviderType.STRIPE:
                success, message, stripe_data = self._confirm_stripe_payment(payment_intent, provider, payment_method_id)
                if not success:
                    self.intent_repo.update_status(intent_id, PaymentIntentStatus.FAILED, message)
                    return False, message, None

                # Update payment intent with Stripe data
                payment_intent.status = PaymentIntentStatus.SUCCEEDED
                payment_intent.payment_method = stripe_data.get('payment_method_type', PaymentMethod.CARD)
                payment_intent.payment_method_details = stripe_data.get('payment_method_details', {})

                # Process successful payment
                return self._process_successful_payment(payment_intent)
            else:
                return False, "PAYMENT_PROVIDER_NOT_SUPPORTED", None

        except Exception as e:
            current_app.logger.error(f"Failed to confirm payment intent {intent_id}: {str(e)}")
            return False, "PAYMENT_CONFIRMATION_ERROR", None

    def _confirm_stripe_payment(self, payment_intent: PaymentIntent, provider: PaymentProvider,
                              payment_method_id: str = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Confirm payment with Stripe.

        Args:
            payment_intent: PaymentIntent instance
            provider: PaymentProvider instance
            payment_method_id: Optional payment method ID

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success, message, Stripe data
        """
        try:
            # Get provider credentials
            credentials = provider.get_credentials()
            stripe.api_key = credentials['secret_key']

            # Retrieve Stripe payment intent
            stripe_intent = stripe.PaymentIntent.retrieve(payment_intent.provider_payment_id)

            # Confirm if needed
            if stripe_intent.status == 'requires_confirmation':
                if payment_method_id:
                    stripe_intent = stripe.PaymentIntent.confirm(
                        payment_intent.provider_payment_id,
                        payment_method=payment_method_id
                    )
                else:
                    stripe_intent = stripe.PaymentIntent.confirm(payment_intent.provider_payment_id)

            # Check payment status
            if stripe_intent.status == 'succeeded':
                stripe_data = {
                    'payment_method_type': stripe_intent.charges.data[0].payment_method_details.type if stripe_intent.charges.data else 'card',
                    'payment_method_details': stripe_intent.charges.data[0].payment_method_details if stripe_intent.charges.data else {},
                    'stripe_charge_id': stripe_intent.charges.data[0].id if stripe_intent.charges.data else None
                }
                return True, "PAYMENT_SUCCEEDED", stripe_data
            elif stripe_intent.status == 'requires_action':
                return False, "PAYMENT_REQUIRES_ACTION", None
            elif stripe_intent.status in ['requires_payment_method', 'requires_confirmation']:
                return False, "PAYMENT_REQUIRES_CONFIRMATION", None
            else:
                return False, "PAYMENT_FAILED", None

        except stripe.error.StripeError as e:
            current_app.logger.error(f"Stripe error confirming payment: {str(e)}")
            return False, "PAYMENT_PROVIDER_ERROR", None
        except Exception as e:
            current_app.logger.error(f"Error confirming Stripe payment: {str(e)}")
            return False, "PAYMENT_CONFIRMATION_ERROR", None

    def _process_successful_payment(self, payment_intent: PaymentIntent) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Process successful payment by adding credits to wallet.

        Args:
            payment_intent: PaymentIntent instance

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success, message, result data
        """
        try:
            # Update payment intent status
            self.intent_repo.update_status(payment_intent.intent_id, PaymentIntentStatus.SUCCEEDED)

            # Add credits to wallet (net amount after fees)
            success, message, wallet_data = self.wallet_service.add_credits(
                user_id=payment_intent.user_id,
                amount=payment_intent.net_amount,
                source='payment_gateway',
                metadata={
                    'payment_intent_id': payment_intent.intent_id,
                    'payment_method': payment_intent.payment_method,
                    'gross_amount': payment_intent.amount,
                    'processing_fee': payment_intent.processing_fee,
                    'provider_id': payment_intent.provider_id
                }
            )

            if not success:
                current_app.logger.error(f"Failed to add credits for payment {payment_intent.intent_id}: {message}")
                return False, "WALLET_UPDATE_FAILED", None

            # Prepare result data
            result = {
                'payment_intent': payment_intent.to_api_dict(),
                'wallet': wallet_data,
                'credits_added': payment_intent.net_amount,
                'processing_fee': payment_intent.processing_fee
            }

            current_app.logger.info(f"Successfully processed payment {payment_intent.intent_id}")
            return True, "PAYMENT_PROCESSING_SUCCESS", result

        except Exception as e:
            current_app.logger.error(f"Failed to process successful payment {payment_intent.intent_id}: {str(e)}")
            return False, "PAYMENT_PROCESSING_ERROR", None

    def get_payment_status(self, intent_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Get payment intent status.

        Args:
            intent_id: Payment intent identifier

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success, message, payment status data
        """
        try:
            payment_intent = self.intent_repo.find_by_intent_id(intent_id)
            if not payment_intent:
                return False, "PAYMENT_INTENT_NOT_FOUND", None

            # Get latest status from provider if pending
            if payment_intent.status in [PaymentIntentStatus.PENDING, PaymentIntentStatus.PROCESSING]:
                self._sync_payment_status(payment_intent)

            status_data = payment_intent.to_api_dict()

            return True, "PAYMENT_STATUS_RETRIEVED", status_data

        except Exception as e:
            current_app.logger.error(f"Failed to get payment status for {intent_id}: {str(e)}")
            return False, "PAYMENT_STATUS_ERROR", None

    def _sync_payment_status(self, payment_intent: PaymentIntent) -> None:
        """
        Sync payment status with provider.

        Args:
            payment_intent: PaymentIntent instance
        """
        try:
            if payment_intent.provider_type == PaymentProviderType.STRIPE:
                provider = self.provider_repo.find_by_provider_id(payment_intent.provider_id)
                if provider:
                    credentials = provider.get_credentials()
                    stripe.api_key = credentials['secret_key']

                    stripe_intent = stripe.PaymentIntent.retrieve(payment_intent.provider_payment_id)

                    # Map Stripe status to our status
                    status_mapping = {
                        'requires_payment_method': PaymentIntentStatus.PENDING,
                        'requires_confirmation': PaymentIntentStatus.PENDING,
                        'requires_action': PaymentIntentStatus.REQUIRES_ACTION,
                        'processing': PaymentIntentStatus.PROCESSING,
                        'succeeded': PaymentIntentStatus.SUCCEEDED,
                        'canceled': PaymentIntentStatus.CANCELLED
                    }

                    new_status = status_mapping.get(stripe_intent.status, payment_intent.status)
                    if new_status != payment_intent.status:
                        self.intent_repo.update_status(payment_intent.intent_id, new_status)

        except Exception as e:
            current_app.logger.error(f"Failed to sync payment status: {str(e)}")

    def cancel_payment(self, intent_id: str, reason: str = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Cancel a payment intent.

        Args:
            intent_id: Payment intent identifier
            reason: Cancellation reason

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success, message, result data
        """
        try:
            payment_intent = self.intent_repo.find_by_intent_id(intent_id)
            if not payment_intent:
                return False, "PAYMENT_INTENT_NOT_FOUND", None

            # Check if payment can be cancelled
            if payment_intent.status not in [PaymentIntentStatus.PENDING, PaymentIntentStatus.REQUIRES_ACTION]:
                return False, "PAYMENT_INTENT_CANNOT_BE_CANCELLED", None

            # Cancel with provider
            if payment_intent.provider_type == PaymentProviderType.STRIPE:
                success, message = self._cancel_stripe_payment(payment_intent)
                if not success:
                    return False, message, None

            # Update status
            self.intent_repo.update_status(
                intent_id,
                PaymentIntentStatus.CANCELLED,
                error_message=reason or "Payment cancelled by user"
            )

            result = {
                'intent_id': intent_id,
                'status': PaymentIntentStatus.CANCELLED,
                'cancelled_at': datetime.now(timezone.utc)
            }

            current_app.logger.info(f"Cancelled payment intent {intent_id}")
            return True, "PAYMENT_CANCELLED", result

        except Exception as e:
            current_app.logger.error(f"Failed to cancel payment intent {intent_id}: {str(e)}")
            return False, "PAYMENT_CANCELLATION_ERROR", None

    def _cancel_stripe_payment(self, payment_intent: PaymentIntent) -> Tuple[bool, str]:
        """
        Cancel Stripe payment intent.

        Args:
            payment_intent: PaymentIntent instance

        Returns:
            Tuple[bool, str]: Success, message
        """
        try:
            provider = self.provider_repo.find_by_provider_id(payment_intent.provider_id)
            if not provider:
                return False, "PAYMENT_PROVIDER_NOT_FOUND"

            credentials = provider.get_credentials()
            stripe.api_key = credentials['secret_key']

            stripe.PaymentIntent.cancel(payment_intent.provider_payment_id)

            return True, "PAYMENT_CANCELLED"

        except stripe.error.StripeError as e:
            current_app.logger.error(f"Stripe error cancelling payment: {str(e)}")
            return False, "PAYMENT_PROVIDER_ERROR"
        except Exception as e:
            current_app.logger.error(f"Error cancelling Stripe payment: {str(e)}")
            return False, "PAYMENT_CANCELLATION_ERROR"

    def handle_webhook(self, provider_type: str, webhook_data: Dict[str, Any],
                      webhook_signature: str = None) -> Tuple[bool, str]:
        """
        Handle payment provider webhook.

        Args:
            provider_type: Payment provider type
            webhook_data: Webhook payload
            webhook_signature: Webhook signature for verification

        Returns:
            Tuple[bool, str]: Success, message
        """
        try:
            if provider_type == PaymentProviderType.STRIPE:
                return self._handle_stripe_webhook(webhook_data, webhook_signature)
            else:
                return False, "WEBHOOK_PROVIDER_NOT_SUPPORTED"

        except Exception as e:
            current_app.logger.error(f"Failed to handle webhook: {str(e)}")
            return False, "WEBHOOK_PROCESSING_ERROR"

    def _handle_stripe_webhook(self, webhook_data: Dict[str, Any], signature: str = None) -> Tuple[bool, str]:
        """
        Handle Stripe webhook events.

        Args:
            webhook_data: Stripe webhook payload
            signature: Stripe webhook signature

        Returns:
            Tuple[bool, str]: Success, message
        """
        try:
            event_type = webhook_data.get('type')
            event_data = webhook_data.get('data', {}).get('object', {})

            # Handle payment intent events
            if event_type.startswith('payment_intent.'):
                payment_intent_id = event_data.get('id')

                # Find our payment intent by provider payment ID
                payment_intent = self.intent_repo.find_by_provider_payment_id(payment_intent_id)
                if not payment_intent:
                    current_app.logger.warning(f"Payment intent not found for webhook: {payment_intent_id}")
                    return True, "WEBHOOK_PROCESSED"

                # Add webhook event to payment intent
                self.intent_repo.add_webhook_event(payment_intent.intent_id, event_type, event_data)

                # Process specific events
                if event_type == 'payment_intent.succeeded':
                    if payment_intent.status != PaymentIntentStatus.SUCCEEDED:
                        self._process_successful_payment(payment_intent)
                elif event_type == 'payment_intent.payment_failed':
                    self.intent_repo.update_status(
                        payment_intent.intent_id,
                        PaymentIntentStatus.FAILED,
                        "Payment failed (webhook)"
                    )

            current_app.logger.info(f"Processed Stripe webhook: {event_type}")
            return True, "WEBHOOK_PROCESSED"

        except Exception as e:
            current_app.logger.error(f"Failed to handle Stripe webhook: {str(e)}")
            return False, "WEBHOOK_PROCESSING_ERROR"

    def get_user_payment_history(self, user_id: str, limit: int = 50) -> Tuple[bool, str, Optional[List[Dict[str, Any]]]]:
        """
        Get user's payment history.

        Args:
            user_id: User identifier
            limit: Maximum number of results

        Returns:
            Tuple[bool, str, Optional[List[Dict]]]: Success, message, payment history
        """
        try:
            payment_intents = self.intent_repo.find_by_user_id(user_id, limit=limit)

            history = []
            for intent in payment_intents:
                history.append({
                    'intent_id': intent.intent_id,
                    'amount': intent.amount,
                    'currency': intent.currency,
                    'net_amount': intent.net_amount,
                    'status': intent.status,
                    'payment_method': intent.payment_method,
                    'processing_fee': intent.processing_fee,
                    'created_at': intent.created_at,
                    'processed_at': intent.processed_at
                })

            return True, "PAYMENT_HISTORY_RETRIEVED", history

        except Exception as e:
            current_app.logger.error(f"Failed to get payment history for user {user_id}: {str(e)}")
            return False, "PAYMENT_HISTORY_ERROR", None