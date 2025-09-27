from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
from flask import current_app
from app.donations.repositories.conversion_rate_repository import ConversionRateRepository
from app.donations.models.conversion_rate import ConversionRate, MultiplierType
from app.donations.models.transaction import Transaction, SourceType


class CreditCalculationService:
    """
    Service for calculating credits earned from game sessions.
    Handles multiplier application, fraud detection, and precise calculations.
    """

    def __init__(self):
        self.conversion_rate_repo = ConversionRateRepository()

    def calculate_credits_from_session(self, session_data: Dict[str, Any],
                                     user_context: Dict[str, Any] = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Calculate credits earned from a game session with precise time tracking.

        Args:
            session_data: Game session data including play_duration_ms
            user_context: User context for multiplier calculation

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success, message, result data
        """
        try:
            # Validate session data
            validation_error = self._validate_session_for_credits(session_data)
            if validation_error:
                current_app.logger.warning(f"Session validation failed: {validation_error}")
                return False, validation_error, None

            # Get current conversion rate
            conversion_rate = self.conversion_rate_repo.get_current_rate()
            if not conversion_rate:
                current_app.logger.error("No active conversion rate found")
                return False, "CONVERSION_RATE_NOT_AVAILABLE", None

            # Extract session info
            play_duration_ms = session_data.get('play_duration_ms', 0)
            session_id = session_data.get('session_id')
            game_type = session_data.get('game_id')
            user_id = session_data.get('user_id')

            # Build context for multiplier calculation
            multiplier_context = self._build_multiplier_context(session_data, user_context or {})

            # Get active multipliers
            active_multipliers = conversion_rate.get_active_multipliers(multiplier_context)

            # Calculate credits
            base_credits = conversion_rate.calculate_credits(play_duration_ms, [])
            total_multiplier = conversion_rate.get_combined_multiplier(active_multipliers)
            final_credits = round(base_credits * total_multiplier, 2)

            # Fraud detection
            fraud_indicators = self._check_fraud_indicators(session_data, final_credits, total_multiplier)
            if fraud_indicators.get('is_suspicious', False):
                current_app.logger.warning(f"Suspicious session detected: {session_id}, indicators: {fraud_indicators}")
                return False, "FRAUD_DETECTION_TRIGGERED", {
                    'fraud_indicators': fraud_indicators,
                    'session_id': session_id
                }

            # Create transaction data
            transaction_data = {
                'user_id': user_id,
                'amount': base_credits,
                'effective_amount': final_credits,
                'multiplier_applied': total_multiplier,
                'source_type': self._determine_source_type(multiplier_context),
                'game_session_id': session_id,
                'active_multipliers': active_multipliers,
                'play_duration_minutes': play_duration_ms / (1000 * 60),
                'base_rate': conversion_rate.base_rate,
                'game_type': game_type
            }

            current_app.logger.info(f"Credits calculated for session {session_id}: {final_credits}€ (base: {base_credits}€, multiplier: {total_multiplier}x)")

            return True, "CREDITS_CALCULATED_SUCCESS", transaction_data

        except Exception as e:
            current_app.logger.error(f"Credit calculation failed: {str(e)}")
            return False, "CREDIT_CALCULATION_ERROR", None

    def apply_multipliers(self, base_credits: float, context: Dict[str, Any]) -> Tuple[float, List[str]]:
        """
        Apply multipliers to base credits based on context.

        Args:
            base_credits: Base credit amount
            context: Context for multiplier calculation

        Returns:
            Tuple[float, List[str]]: Final credits and list of applied multipliers
        """
        try:
            conversion_rate = self.conversion_rate_repo.get_current_rate()
            if not conversion_rate:
                return base_credits, []

            active_multipliers = conversion_rate.get_active_multipliers(context)
            total_multiplier = conversion_rate.get_combined_multiplier(active_multipliers)
            final_credits = round(base_credits * total_multiplier, 2)

            return final_credits, active_multipliers

        except Exception as e:
            current_app.logger.error(f"Multiplier application failed: {str(e)}")
            return base_credits, []

    def get_active_multipliers(self, user_id: str, session_context: Dict[str, Any] = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Get currently active multipliers for a user.

        Args:
            user_id: User identifier
            session_context: Session context for multiplier calculation

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success, message, multiplier data
        """
        try:
            conversion_rate = self.conversion_rate_repo.get_current_rate()
            if not conversion_rate:
                return False, "CONVERSION_RATE_NOT_AVAILABLE", None

            # Build context
            context = session_context or {}
            context['user_id'] = user_id

            # Get active multipliers
            active_multipliers = conversion_rate.get_active_multipliers(context)
            total_multiplier = conversion_rate.get_combined_multiplier(active_multipliers)

            multiplier_data = {
                'active_multipliers': active_multipliers,
                'total_multiplier': total_multiplier,
                'base_rate': conversion_rate.base_rate,
                'multiplier_details': {
                    multiplier: conversion_rate.multipliers.get(multiplier, 1.0)
                    for multiplier in active_multipliers
                }
            }

            return True, "MULTIPLIERS_RETRIEVED_SUCCESS", multiplier_data

        except Exception as e:
            current_app.logger.error(f"Failed to get active multipliers: {str(e)}")
            return False, "MULTIPLIERS_RETRIEVAL_ERROR", None

    def estimate_credits_for_duration(self, duration_minutes: float,
                                    context: Dict[str, Any] = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Estimate credits that would be earned for a given duration.

        Args:
            duration_minutes: Play duration in minutes
            context: Context for multiplier calculation

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success, message, estimation data
        """
        try:
            if duration_minutes <= 0:
                return False, "INVALID_DURATION", None

            conversion_rate = self.conversion_rate_repo.get_current_rate()
            if not conversion_rate:
                return False, "CONVERSION_RATE_NOT_AVAILABLE", None

            # Convert to milliseconds for consistency
            duration_ms = int(duration_minutes * 60 * 1000)

            # Calculate with no multipliers (base case)
            base_credits = conversion_rate.calculate_credits(duration_ms, [])

            # Calculate with current multipliers
            active_multipliers = conversion_rate.get_active_multipliers(context or {})
            credits_with_multipliers = conversion_rate.calculate_credits(duration_ms, active_multipliers)

            estimation = {
                'duration_minutes': duration_minutes,
                'base_credits': base_credits,
                'credits_with_multipliers': credits_with_multipliers,
                'active_multipliers': active_multipliers,
                'total_multiplier': conversion_rate.get_combined_multiplier(active_multipliers),
                'base_rate': conversion_rate.base_rate
            }

            return True, "CREDIT_ESTIMATION_SUCCESS", estimation

        except Exception as e:
            current_app.logger.error(f"Credit estimation failed: {str(e)}")
            return False, "CREDIT_ESTIMATION_ERROR", None

    def _validate_session_for_credits(self, session_data: Dict[str, Any]) -> Optional[str]:
        """
        Validate session data for credit calculation.

        Args:
            session_data: Session data to validate

        Returns:
            Optional[str]: Error message if validation fails, None if valid
        """
        required_fields = ['user_id', 'session_id', 'play_duration_ms']
        for field in required_fields:
            if field not in session_data or session_data[field] is None:
                return f"SESSION_{field.upper()}_REQUIRED"

        play_duration_ms = session_data.get('play_duration_ms', 0)
        if not isinstance(play_duration_ms, (int, float)) or play_duration_ms < 0:
            return "SESSION_INVALID_PLAY_DURATION"

        # Maximum session length check (24 hours)
        max_duration_ms = 24 * 60 * 60 * 1000  # 24 hours in ms
        if play_duration_ms > max_duration_ms:
            return "SESSION_DURATION_TOO_LONG"

        # Minimum session length check (10 seconds)
        min_duration_ms = 10 * 1000  # 10 seconds in ms
        if play_duration_ms < min_duration_ms:
            return "SESSION_DURATION_TOO_SHORT"

        return None

    def _build_multiplier_context(self, session_data: Dict[str, Any],
                                user_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build context for multiplier calculation.

        Args:
            session_data: Game session data
            user_context: User-specific context

        Returns:
            Dict[str, Any]: Combined context for multiplier calculation
        """
        context = user_context.copy()

        # Add session-specific context
        if 'game_mode' in session_data:
            context['is_tournament_mode'] = session_data['game_mode'] == 'tournament'
            context['is_challenge_mode'] = session_data['game_mode'] == 'challenge'

        # Add time-based context
        current_time = datetime.now(timezone.utc)
        context['current_time'] = current_time
        context['is_weekend'] = current_time.weekday() >= 5

        # Add user-specific flags from context
        context.setdefault('has_daily_streak', False)
        context.setdefault('special_event_active', False)
        context.setdefault('user_loyalty_level', 0)
        context.setdefault('is_first_time_player', False)

        return context

    def _determine_source_type(self, context: Dict[str, Any]) -> str:
        """
        Determine the source type of credits based on context.

        Args:
            context: Multiplier context

        Returns:
            str: Source type for the transaction
        """
        if context.get('is_tournament_mode', False):
            return SourceType.TOURNAMENT.value
        elif context.get('is_challenge_mode', False):
            return SourceType.CHALLENGE.value
        elif context.get('has_daily_streak', False):
            return SourceType.STREAK_BONUS.value
        else:
            return SourceType.GAMEPLAY.value

    def _check_fraud_indicators(self, session_data: Dict[str, Any],
                               credits_earned: float, multiplier: float) -> Dict[str, Any]:
        """
        Check for fraud indicators in credit calculation.

        Args:
            session_data: Session data
            credits_earned: Calculated credits
            multiplier: Applied multiplier

        Returns:
            Dict[str, Any]: Fraud indicators and risk assessment
        """
        indicators = {
            'is_suspicious': False,
            'risk_level': 'low',
            'indicators': []
        }

        # Check for unusually high earnings
        if credits_earned > 100:  # More than €100 in one session
            indicators['indicators'].append('high_earnings')
            indicators['risk_level'] = 'high'

        # Check for unusually high multipliers
        if multiplier > 5.0:
            indicators['indicators'].append('high_multiplier')
            indicators['risk_level'] = 'medium'

        # Check for unusually long sessions
        play_duration_hours = session_data.get('play_duration_ms', 0) / (1000 * 60 * 60)
        if play_duration_hours > 8:  # More than 8 hours
            indicators['indicators'].append('long_session')
            indicators['risk_level'] = 'medium'

        # Check for suspicious timing (off-hours automation)
        current_hour = datetime.now(timezone.utc).hour
        if current_hour < 4 or current_hour > 23:
            indicators['indicators'].append('off_hours')
            if indicators['risk_level'] == 'low':
                indicators['risk_level'] = 'medium'

        # Mark as suspicious if high risk
        if indicators['risk_level'] == 'high' or len(indicators['indicators']) >= 3:
            indicators['is_suspicious'] = True

        return indicators

    def get_conversion_rate_info(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Get current conversion rate information.

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success, message, rate info
        """
        try:
            conversion_rate = self.conversion_rate_repo.get_current_rate()
            if not conversion_rate:
                # Try to get or create default rate
                conversion_rate = self.conversion_rate_repo.ensure_default_rate_exists()

            if not conversion_rate:
                return False, "CONVERSION_RATE_NOT_AVAILABLE", None

            rate_info = conversion_rate.get_rate_summary()
            return True, "CONVERSION_RATE_RETRIEVED_SUCCESS", rate_info

        except Exception as e:
            current_app.logger.error(f"Failed to get conversion rate info: {str(e)}")
            return False, "CONVERSION_RATE_RETRIEVAL_ERROR", None