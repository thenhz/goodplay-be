from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Tuple
from flask import current_app
from app.donations.repositories.impact_story_repository import ImpactStoryRepository
from app.donations.repositories.impact_metric_repository import ImpactMetricRepository
from app.donations.repositories.impact_update_repository import ImpactUpdateRepository
from app.donations.repositories.transaction_repository import TransactionRepository
from app.donations.repositories.wallet_repository import WalletRepository


class ImpactTrackingService:
    """
    Service for tracking impact of donations and managing impact data.

    This service handles the core logic of mapping donations to impact metrics,
    updating impact stories, and coordinating with ONLUS data.
    """

    def __init__(self):
        self.story_repository = ImpactStoryRepository()
        self.metric_repository = ImpactMetricRepository()
        self.update_repository = ImpactUpdateRepository()
        self.transaction_repository = TransactionRepository()
        self.wallet_repository = WalletRepository()

    def track_donation_impact(self, donation_id: str, user_id: str,
                            amount: float, onlus_id: str,
                            metadata: Dict[str, Any] = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Track the impact of a donation and update relevant metrics.

        Args:
            donation_id: ID of the donation transaction
            user_id: ID of the user making the donation
            amount: Donation amount
            onlus_id: ID of the ONLUS receiving the donation
            metadata: Additional donation metadata

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success status, message, impact data
        """
        try:
            current_app.logger.info(f"Tracking impact for donation {donation_id}: €{amount} to ONLUS {onlus_id}")

            # Get user statistics for story unlocking
            user_stats = self._get_user_statistics(user_id)

            # Update ONLUS metrics with donation contribution
            metrics_updated = self._update_onlus_metrics(onlus_id, amount, donation_id)

            # Check for story unlocks
            unlocked_stories = self._check_story_unlocks(user_id, user_stats, amount)

            # Create impact tracking record
            impact_data = {
                'donation_id': donation_id,
                'user_id': user_id,
                'onlus_id': onlus_id,
                'amount': amount,
                'tracked_at': datetime.now(timezone.utc),
                'metrics_updated': len(metrics_updated),
                'stories_unlocked': len(unlocked_stories),
                'user_stats': user_stats,
                'metadata': metadata or {}
            }

            # Log significant milestones
            self._check_and_log_milestones(user_id, user_stats, amount, onlus_id)

            current_app.logger.info(f"Impact tracking completed for donation {donation_id}: "
                                   f"{len(metrics_updated)} metrics updated, "
                                   f"{len(unlocked_stories)} stories unlocked")

            return True, "IMPACT_TRACKING_SUCCESS", impact_data

        except Exception as e:
            current_app.logger.error(f"Error tracking donation impact for {donation_id}: {str(e)}")
            return False, "IMPACT_TRACKING_ERROR", None

    def get_user_impact_summary(self, user_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Get comprehensive impact summary for a user.

        Args:
            user_id: User ID

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success status, message, impact summary
        """
        try:
            # Get user statistics
            user_stats = self._get_user_statistics(user_id)

            # Get unlocked stories
            unlocked_stories = self.story_repository.get_stories_for_user(
                user_stats=user_stats,
                include_locked=False
            )

            # Get next unlockable stories
            next_stories = self.story_repository.get_next_unlock_stories(
                user_stats=user_stats,
                limit=3
            )

            # Get donation history impact
            donation_history = self._get_user_donation_impact_history(user_id)

            # Calculate impact score components
            impact_score_data = self._calculate_impact_score_components(user_stats, donation_history)

            impact_summary = {
                'user_id': user_id,
                'statistics': user_stats,
                'impact_score': impact_score_data,
                'stories': {
                    'unlocked_count': len(unlocked_stories),
                    'unlocked_stories': unlocked_stories[:5],  # Latest 5
                    'next_unlockable': next_stories
                },
                'donation_impact': donation_history,
                'milestones': self._get_user_milestones(user_id),
                'generated_at': datetime.now(timezone.utc).isoformat()
            }

            return True, "USER_IMPACT_SUMMARY_SUCCESS", impact_summary

        except Exception as e:
            current_app.logger.error(f"Error getting user impact summary for {user_id}: {str(e)}")
            return False, "USER_IMPACT_SUMMARY_ERROR", None

    def get_donation_impact_details(self, donation_id: str,
                                  user_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Get detailed impact information for a specific donation.

        Args:
            donation_id: Donation transaction ID
            user_id: User ID (for access control)

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success status, message, impact details
        """
        try:
            # Get donation transaction
            transaction = self.transaction_repository.get_transaction_by_id(donation_id)
            if not transaction or transaction.user_id != user_id:
                return False, "DONATION_NOT_FOUND", None

            if transaction.transaction_type != 'donated':
                return False, "TRANSACTION_NOT_DONATION", None

            # Get related impact updates
            related_updates = self.update_repository.get_updates_for_donation(donation_id)

            # Get ONLUS metrics affected by this donation
            onlus_metrics = self.metric_repository.get_latest_metrics_by_onlus(transaction.onlus_id)

            # Calculate donation efficiency
            efficiency_data = self._calculate_donation_efficiency(transaction, onlus_metrics)

            # Get stories unlocked around the time of this donation
            unlocked_stories = self._get_stories_unlocked_by_donation(user_id, donation_id, transaction.created_at)

            impact_details = {
                'donation_id': donation_id,
                'transaction_data': transaction.to_api_dict(),
                'related_updates': [update.to_response_dict() for update in related_updates],
                'onlus_metrics': [metric.to_response_dict() for metric in onlus_metrics],
                'efficiency_analysis': efficiency_data,
                'stories_unlocked': unlocked_stories,
                'impact_timeline': self._build_donation_impact_timeline(donation_id, transaction)
            }

            return True, "DONATION_IMPACT_DETAILS_SUCCESS", impact_details

        except Exception as e:
            current_app.logger.error(f"Error getting donation impact details for {donation_id}: {str(e)}")
            return False, "DONATION_IMPACT_DETAILS_ERROR", None

    def update_onlus_impact_metric(self, onlus_id: str, metric_data: Dict[str, Any],
                                 source: str = "onlus_report") -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Update or create an impact metric for an ONLUS.

        Args:
            onlus_id: ONLUS ID
            metric_data: Metric data to update
            source: Source of the metric update

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success status, message, metric data
        """
        try:
            # Validate metric data
            from app.donations.models.impact_metric import ImpactMetric
            validation_error = ImpactMetric.validate_metric_data(metric_data)
            if validation_error:
                return False, validation_error, None

            # Check if metric already exists
            existing_metrics = self.metric_repository.get_metrics_by_onlus(
                onlus_id=onlus_id,
                metric_type=metric_data.get('metric_type'),
                limit=1
            )

            if existing_metrics and existing_metrics[0].metric_name == metric_data.get('metric_name'):
                # Update existing metric
                metric = existing_metrics[0]
                metric.update_value(metric_data['current_value'], source)

                # Update other fields if provided
                for field in ['target_value', 'description', 'methodology']:
                    if field in metric_data:
                        setattr(metric, field, metric_data[field])

                success = self.metric_repository.update_metric(str(metric._id), metric.to_dict())
                if success:
                    current_app.logger.info(f"Updated metric {metric.metric_name} for ONLUS {onlus_id}")
                    return True, "METRIC_UPDATED_SUCCESS", metric.to_response_dict()
                else:
                    return False, "METRIC_UPDATE_FAILED", None
            else:
                # Create new metric
                metric_data['onlus_id'] = onlus_id
                metric_data['source'] = source
                metric = self.metric_repository.create_metric(metric_data)

                current_app.logger.info(f"Created new metric {metric.metric_name} for ONLUS {onlus_id}")
                return True, "METRIC_CREATED_SUCCESS", metric.to_response_dict()

        except Exception as e:
            current_app.logger.error(f"Error updating ONLUS metric for {onlus_id}: {str(e)}")
            return False, "METRIC_UPDATE_ERROR", None

    def create_impact_update(self, onlus_id: str, update_data: Dict[str, Any]) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Create a new impact update from an ONLUS.

        Args:
            onlus_id: ONLUS ID
            update_data: Update data

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success status, message, update data
        """
        try:
            # Validate update data
            from app.donations.models.impact_update import ImpactUpdate
            validation_error = ImpactUpdate.validate_update_data(update_data)
            if validation_error:
                return False, validation_error, None

            # Ensure ONLUS ID is set
            update_data['onlus_id'] = onlus_id

            # Create the update
            update = self.update_repository.create_update(update_data)

            # If it's a milestone or emergency update, consider auto-featuring
            if update.update_type in ['milestone_reached', 'emergency_response']:
                if update.priority in ['urgent', 'critical']:
                    # Feature for 24 hours
                    featured_until = datetime.now(timezone.utc) + timedelta(hours=24)
                    self.update_repository.feature_update(str(update._id), featured_until)

            current_app.logger.info(f"Created impact update {update._id} for ONLUS {onlus_id}")
            return True, "IMPACT_UPDATE_CREATED_SUCCESS", update.to_response_dict()

        except Exception as e:
            current_app.logger.error(f"Error creating impact update for {onlus_id}: {str(e)}")
            return False, "IMPACT_UPDATE_CREATION_ERROR", None

    def _get_user_statistics(self, user_id: str) -> Dict[str, Any]:
        """
        Get comprehensive user statistics for impact tracking.

        Args:
            user_id: User ID

        Returns:
            Dict: User statistics
        """
        try:
            # Get wallet statistics
            wallet_success, _, wallet_stats = self.wallet_repository.get_wallet_statistics(user_id)

            if not wallet_success:
                # Return default stats if wallet not found
                return {
                    'total_donated': 0.0,
                    'donation_count': 0,
                    'onlus_diversity': 0,
                    'impact_score': 0.0,
                    'special_events': [],
                    'last_donation_date': None
                }

            # Extract relevant statistics
            wallet_data = wallet_stats.get('wallet', {})
            transaction_data = wallet_stats.get('transactions', {})

            # Get ONLUS diversity
            onlus_diversity = self._calculate_onlus_diversity(user_id)

            # Get impact score (from social module if available)
            impact_score = self._get_user_impact_score(user_id)

            # Get special events participation
            special_events = self._get_user_special_events(user_id)

            return {
                'total_donated': wallet_data.get('total_donated', 0.0),
                'donation_count': transaction_data.get('by_type', {}).get('donated', {}).get('count', 0),
                'onlus_diversity': onlus_diversity,
                'impact_score': impact_score,
                'special_events': special_events,
                'last_donation_date': transaction_data.get('last_donation_date'),
                'avg_donation_amount': transaction_data.get('by_type', {}).get('donated', {}).get('avg_amount', 0.0)
            }

        except Exception as e:
            current_app.logger.error(f"Error getting user statistics for {user_id}: {str(e)}")
            return {'total_donated': 0.0, 'donation_count': 0, 'onlus_diversity': 0, 'impact_score': 0.0, 'special_events': []}

    def _update_onlus_metrics(self, onlus_id: str, donation_amount: float,
                            donation_id: str) -> List[str]:
        """
        Update ONLUS metrics with a donation contribution.

        Args:
            onlus_id: ONLUS ID
            donation_amount: Donation amount
            donation_id: Donation ID

        Returns:
            List[str]: List of updated metric IDs
        """
        updated_metrics = []

        try:
            # Get all metrics for this ONLUS
            metrics = self.metric_repository.get_latest_metrics_by_onlus(onlus_id)

            for metric in metrics:
                # Add donation contribution to metric
                success = self.metric_repository.add_donation_contribution(
                    str(metric._id), donation_amount
                )

                if success:
                    updated_metrics.append(str(metric._id))

                    # For financial metrics, also update the current value
                    if metric.metric_type == 'financial':
                        new_value = metric.current_value + donation_amount
                        self.metric_repository.update_metric_value(
                            str(metric._id), new_value, f"donation_{donation_id}"
                        )

        except Exception as e:
            current_app.logger.error(f"Error updating ONLUS metrics for {onlus_id}: {str(e)}")

        return updated_metrics

    def _check_story_unlocks(self, user_id: str, user_stats: Dict[str, Any],
                           new_donation_amount: float) -> List[Dict[str, Any]]:
        """
        Check if any new stories are unlocked by this donation.

        Args:
            user_id: User ID
            user_stats: Current user statistics
            new_donation_amount: Amount of the new donation

        Returns:
            List[Dict]: Newly unlocked stories
        """
        unlocked_stories = []

        try:
            # Get current total donated including this donation
            new_total_donated = user_stats.get('total_donated', 0) + new_donation_amount
            new_donation_count = user_stats.get('donation_count', 0) + 1

            # Update stats for checking
            updated_stats = user_stats.copy()
            updated_stats['total_donated'] = new_total_donated
            updated_stats['donation_count'] = new_donation_count

            # Get all active stories
            all_stories = self.story_repository.get_stories_for_user(
                user_stats=updated_stats,
                include_locked=True
            )

            # Check which stories are newly unlocked
            for story_data in all_stories:
                if story_data.get('is_unlocked', False):
                    # Check if this story was locked with previous stats
                    was_locked = not self.story_repository.get_story_by_id(
                        story_data['id']
                    ).check_unlock_status(user_stats)

                    if was_locked:
                        unlocked_stories.append(story_data)
                        current_app.logger.info(f"Story unlocked for user {user_id}: {story_data['title']}")

        except Exception as e:
            current_app.logger.error(f"Error checking story unlocks for user {user_id}: {str(e)}")

        return unlocked_stories

    def _check_and_log_milestones(self, user_id: str, user_stats: Dict[str, Any],
                                donation_amount: float, onlus_id: str) -> None:
        """
        Check for and log significant milestones.

        Args:
            user_id: User ID
            user_stats: User statistics
            donation_amount: Donation amount
            onlus_id: ONLUS ID
        """
        try:
            total_donated = user_stats.get('total_donated', 0)
            donation_count = user_stats.get('donation_count', 0)

            # Check for donation amount milestones
            milestones = [10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000]
            for milestone in milestones:
                if total_donated >= milestone and (total_donated - donation_amount) < milestone:
                    current_app.logger.info(f"User {user_id} reached €{milestone} total donated milestone")
                    break

            # Check for donation count milestones
            count_milestones = [1, 5, 10, 25, 50, 100, 250, 500]
            for milestone in count_milestones:
                if donation_count >= milestone and (donation_count - 1) < milestone:
                    current_app.logger.info(f"User {user_id} reached {milestone} donations milestone")
                    break

        except Exception as e:
            current_app.logger.error(f"Error checking milestones for user {user_id}: {str(e)}")

    def _calculate_onlus_diversity(self, user_id: str) -> int:
        """
        Calculate how many different ONLUS the user has supported.

        Args:
            user_id: User ID

        Returns:
            int: Number of different ONLUS supported
        """
        try:
            # This would be implemented with a proper aggregation query
            # For now, return a placeholder value
            return 1
        except Exception:
            return 0

    def _get_user_impact_score(self, user_id: str) -> float:
        """
        Get user's impact score from the social module.

        Args:
            user_id: User ID

        Returns:
            float: Impact score
        """
        try:
            # This would integrate with the social module's impact score
            # For now, return a placeholder value
            return 0.0
        except Exception:
            return 0.0

    def _get_user_special_events(self, user_id: str) -> List[str]:
        """
        Get list of special events the user participated in.

        Args:
            user_id: User ID

        Returns:
            List[str]: Special event IDs
        """
        try:
            # This would be implemented with proper event tracking
            # For now, return empty list
            return []
        except Exception:
            return []

    def _get_user_donation_impact_history(self, user_id: str) -> Dict[str, Any]:
        """
        Get donation impact history for a user.

        Args:
            user_id: User ID

        Returns:
            Dict: Donation impact history
        """
        try:
            # Get recent donations
            recent_donations = self.transaction_repository.get_transactions_by_user(
                user_id=user_id,
                filters={'transaction_type': 'donated'},
                limit=10
            )

            impact_history = {
                'recent_donations': [tx.to_api_dict() for tx in recent_donations],
                'total_impact_tracked': len(recent_donations),
                'estimated_beneficiaries': 0,  # Would be calculated from metrics
                'projects_supported': 0  # Would be calculated from metrics
            }

            return impact_history

        except Exception as e:
            current_app.logger.error(f"Error getting donation impact history for {user_id}: {str(e)}")
            return {'recent_donations': [], 'total_impact_tracked': 0}

    def _calculate_impact_score_components(self, user_stats: Dict[str, Any],
                                         donation_history: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate impact score components for a user.

        Args:
            user_stats: User statistics
            donation_history: Donation history

        Returns:
            Dict: Impact score components
        """
        try:
            # This would integrate with the existing impact score calculation
            # For now, return basic calculations
            total_donated = user_stats.get('total_donated', 0)
            donation_count = user_stats.get('donation_count', 0)
            onlus_diversity = user_stats.get('onlus_diversity', 0)

            # Calculate donation component (50% of total impact score)
            donation_component = min(2000.0, total_donated * 2)  # €1 = 2 points, max 2000

            return {
                'donation_component': donation_component,
                'total_donated': total_donated,
                'donation_count': donation_count,
                'onlus_diversity': onlus_diversity,
                'component_breakdown': {
                    'amount_score': donation_component * 0.6,
                    'frequency_score': min(400.0, donation_count * 10),
                    'diversity_score': min(400.0, onlus_diversity * 100)
                }
            }

        except Exception as e:
            current_app.logger.error(f"Error calculating impact score components: {str(e)}")
            return {'donation_component': 0, 'total_donated': 0, 'donation_count': 0}

    def _get_user_milestones(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get user milestones achieved.

        Args:
            user_id: User ID

        Returns:
            List[Dict]: User milestones
        """
        try:
            # This would be implemented with proper milestone tracking
            # For now, return empty list
            return []
        except Exception:
            return []

    def _calculate_donation_efficiency(self, transaction: Any,
                                     onlus_metrics: List[Any]) -> Dict[str, Any]:
        """
        Calculate efficiency metrics for a donation.

        Args:
            transaction: Donation transaction
            onlus_metrics: ONLUS metrics

        Returns:
            Dict: Efficiency analysis
        """
        try:
            # Calculate basic efficiency metrics
            efficiency_data = {
                'donation_amount': transaction.get_effective_amount(),
                'platform_fee': transaction.amount * 0.05,  # 5% platform fee
                'net_to_onlus': transaction.get_effective_amount() * 0.95,
                'estimated_impact_per_euro': 0.0
            }

            # Calculate impact per euro if metrics available
            if onlus_metrics:
                total_impact = sum(metric.current_value for metric in onlus_metrics
                                 if metric.metric_unit in ['people', 'projects'])
                total_donations = sum(metric.related_donations_amount for metric in onlus_metrics)

                if total_donations > 0:
                    efficiency_data['estimated_impact_per_euro'] = total_impact / total_donations

            return efficiency_data

        except Exception as e:
            current_app.logger.error(f"Error calculating donation efficiency: {str(e)}")
            return {'donation_amount': 0, 'estimated_impact_per_euro': 0}

    def _get_stories_unlocked_by_donation(self, user_id: str, donation_id: str,
                                        donation_date: datetime) -> List[Dict[str, Any]]:
        """
        Get stories that were unlocked around the time of a specific donation.

        Args:
            user_id: User ID
            donation_id: Donation ID
            donation_date: Date of the donation

        Returns:
            List[Dict]: Stories unlocked by this donation
        """
        try:
            # This would be implemented with proper tracking
            # For now, return empty list
            return []
        except Exception:
            return []

    def _build_donation_impact_timeline(self, donation_id: str,
                                      transaction: Any) -> List[Dict[str, Any]]:
        """
        Build a timeline of impact events for a donation.

        Args:
            donation_id: Donation ID
            transaction: Donation transaction

        Returns:
            List[Dict]: Impact timeline events
        """
        try:
            timeline = [
                {
                    'event_type': 'donation_made',
                    'timestamp': transaction.created_at.isoformat(),
                    'description': f'Donation of €{transaction.get_effective_amount()} made',
                    'data': {'amount': transaction.get_effective_amount()}
                }
            ]

            if transaction.processed_at:
                timeline.append({
                    'event_type': 'donation_processed',
                    'timestamp': transaction.processed_at.isoformat(),
                    'description': 'Donation processed and transferred to ONLUS',
                    'data': {'status': transaction.status}
                })

            return sorted(timeline, key=lambda x: x['timestamp'])

        except Exception as e:
            current_app.logger.error(f"Error building donation impact timeline: {str(e)}")
            return []