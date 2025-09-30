from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timezone, timedelta
from flask import current_app
import math

from app.onlus.repositories.allocation_request_repository import AllocationRequestRepository
from app.onlus.repositories.allocation_result_repository import AllocationResultRepository
from app.onlus.repositories.funding_pool_repository import FundingPoolRepository
from app.onlus.repositories.onlus_organization_repository import ONLUSOrganizationRepository
from app.onlus.repositories.compliance_score_repository import ComplianceScoreRepository
from app.donations.repositories.transaction_repository import TransactionRepository
from app.donations.repositories.wallet_repository import WalletRepository

from app.onlus.models.allocation_request import AllocationRequest, AllocationRequestStatus, AllocationPriority
from app.onlus.models.allocation_result import AllocationResult, AllocationResultStatus, AllocationMethod
from app.onlus.models.funding_pool import FundingPool, FundingPoolStatus
from app.donations.models.transaction import Transaction, TransactionType, TransactionStatus


class AllocationEngineService:
    """
    Smart allocation engine service for intelligent donation distribution.

    Implements the core allocation algorithm with multi-factor scoring:
    - Current funding gap (25%)
    - Project urgency level (20%)
    - Historical performance (20%)
    - Donor preferences match (15%)
    - Impact efficiency ratio (10%)
    - Seasonal factors (10%)
    """

    def __init__(self):
        self.request_repo = AllocationRequestRepository()
        self.result_repo = AllocationResultRepository()
        self.pool_repo = FundingPoolRepository()
        self.onlus_repo = ONLUSOrganizationRepository()
        self.compliance_repo = ComplianceScoreRepository()
        self.transaction_repo = TransactionRepository()
        self.wallet_repo = WalletRepository()

    def calculate_allocation_score(self, request: AllocationRequest,
                                  onlus_data: Dict[str, Any],
                                  donor_preferences: List[str] = None,
                                  seasonal_context: Dict[str, Any] = None) -> Tuple[bool, str, float]:
        """
        Calculate smart allocation score using multi-factor algorithm.

        Formula:
        allocation_score = (
            current_funding_gap * 0.25 +
            project_urgency_level * 0.20 +
            historical_performance * 0.20 +
            donor_preferences_match * 0.15 +
            impact_efficiency_ratio * 0.10 +
            seasonal_factors * 0.10
        )
        """
        try:
            score_components = {}

            # 1. Current funding gap (25% weight)
            funding_gap_score = self._calculate_funding_gap_score(request, onlus_data)
            score_components['funding_gap'] = funding_gap_score

            # 2. Project urgency level (20% weight)
            urgency_score = self._calculate_urgency_score(request)
            score_components['urgency'] = urgency_score

            # 3. Historical performance (20% weight)
            performance_score = self._calculate_performance_score(request.onlus_id)
            score_components['performance'] = performance_score

            # 4. Donor preferences match (15% weight)
            preferences_score = self._calculate_preferences_match_score(
                request, donor_preferences or []
            )
            score_components['preferences'] = preferences_score

            # 5. Impact efficiency ratio (10% weight)
            efficiency_score = self._calculate_efficiency_score(request.onlus_id)
            score_components['efficiency'] = efficiency_score

            # 6. Seasonal factors (10% weight)
            seasonal_score = self._calculate_seasonal_score(
                request, seasonal_context or {}
            )
            score_components['seasonal'] = seasonal_score

            # Calculate weighted final score
            final_score = (
                funding_gap_score * 0.25 +
                urgency_score * 0.20 +
                performance_score * 0.20 +
                preferences_score * 0.15 +
                efficiency_score * 0.10 +
                seasonal_score * 0.10
            )

            # Ensure score is within 0-100 range
            final_score = max(0.0, min(100.0, final_score))

            current_app.logger.info(
                f"Allocation score calculated: {final_score:.2f} for request {request._id} "
                f"(Components: {score_components})"
            )

            return True, "ALLOCATION_SCORE_CALCULATED_SUCCESS", final_score

        except Exception as e:
            current_app.logger.error(f"Allocation score calculation failed: {str(e)}")
            return False, "ALLOCATION_SCORE_CALCULATION_FAILED", 0.0

    def _calculate_funding_gap_score(self, request: AllocationRequest,
                                   onlus_data: Dict[str, Any]) -> float:
        """Calculate funding gap score (0-100)."""
        try:
            # Get ONLUS financial data
            total_budget = onlus_data.get('annual_budget', 100000)
            current_funding = onlus_data.get('current_funding', 0)
            funding_gap = max(0, total_budget - current_funding)

            if total_budget <= 0:
                return 50.0  # Neutral score if no budget data

            # Calculate gap percentage
            gap_percentage = funding_gap / total_budget

            # Score based on funding gap (higher gap = higher score)
            if gap_percentage >= 0.8:  # 80%+ gap
                return 95.0
            elif gap_percentage >= 0.6:  # 60-79% gap
                return 85.0
            elif gap_percentage >= 0.4:  # 40-59% gap
                return 70.0
            elif gap_percentage >= 0.2:  # 20-39% gap
                return 55.0
            else:  # <20% gap
                return 40.0

        except Exception:
            return 50.0  # Default neutral score

    def _calculate_urgency_score(self, request: AllocationRequest) -> float:
        """Calculate urgency score based on priority and deadline (0-100)."""
        try:
            base_score = request.urgency_level * 20  # 1-5 scale to 20-100

            # Adjust based on deadline proximity
            if request.deadline:
                days_until_deadline = request.get_days_until_deadline()
                if days_until_deadline is not None:
                    if days_until_deadline <= 7:
                        base_score += 20
                    elif days_until_deadline <= 30:
                        base_score += 10
                    elif days_until_deadline <= 90:
                        base_score += 5

            # Emergency priority gets maximum score
            if request.priority == AllocationPriority.EMERGENCY.value:
                return 100.0

            return max(0.0, min(100.0, base_score))

        except Exception:
            return 50.0

    def _calculate_performance_score(self, onlus_id: str) -> float:
        """Calculate historical performance score (0-100)."""
        try:
            # Get compliance score
            success, _, compliance_score = self.compliance_repo.get_current_score_by_onlus(onlus_id)
            if success and compliance_score:
                performance_score = compliance_score.overall_score
            else:
                performance_score = 70.0  # Default for new ONLUS

            # Get allocation history performance
            success, _, results = self.result_repo.get_results_by_onlus(onlus_id, limit=10)
            if success and results:
                successful_allocations = sum(1 for r in results if r.is_successful())
                success_rate = successful_allocations / len(results)

                # Combine compliance and success rate
                performance_score = (performance_score * 0.7) + (success_rate * 100 * 0.3)

            return max(0.0, min(100.0, performance_score))

        except Exception:
            return 70.0  # Default score

    def _calculate_preferences_match_score(self, request: AllocationRequest,
                                         donor_preferences: List[str]) -> float:
        """Calculate donor preferences match score (0-100)."""
        try:
            if not donor_preferences:
                return 50.0  # Neutral if no preferences

            matches = 0
            total_preferences = len(donor_preferences)

            # Check category match
            if request.category and request.category in donor_preferences:
                matches += 1

            # Check project type keywords
            project_keywords = request.project_title.lower().split() + \
                             request.project_description.lower().split()

            for preference in donor_preferences:
                if preference.lower() in project_keywords:
                    matches += 1

            # Calculate match percentage
            if total_preferences > 0:
                match_rate = matches / total_preferences
                return min(100.0, match_rate * 100)

            return 50.0

        except Exception:
            return 50.0

    def _calculate_efficiency_score(self, onlus_id: str) -> float:
        """Calculate impact efficiency ratio score (0-100)."""
        try:
            # Get recent allocation results
            success, _, results = self.result_repo.get_results_by_onlus(
                onlus_id, status="completed", limit=5
            )

            if not success or not results:
                return 70.0  # Default for new ONLUS

            # Calculate average efficiency ratio
            efficiency_ratios = [r.calculate_efficiency_ratio() for r in results]
            avg_efficiency = sum(efficiency_ratios) / len(efficiency_ratios)

            # Convert to 0-100 score
            efficiency_score = avg_efficiency * 100

            return max(0.0, min(100.0, efficiency_score))

        except Exception:
            return 70.0

    def _calculate_seasonal_score(self, request: AllocationRequest,
                                seasonal_context: Dict[str, Any]) -> float:
        """Calculate seasonal factors score (0-100)."""
        try:
            base_score = 50.0  # Neutral base
            current_month = datetime.now(timezone.utc).month

            # Holiday seasons (higher donation activity)
            if current_month in [11, 12]:  # November-December
                base_score += 20
            elif current_month in [3, 4]:  # March-April (tax season)
                base_score += 10

            # Category-specific seasonal factors
            category = request.category
            if category:
                if category.lower() in ['education'] and current_month in [8, 9]:
                    base_score += 15  # Back to school season
                elif category.lower() in ['healthcare'] and current_month in [10, 11]:
                    base_score += 10  # Flu season awareness
                elif category.lower() in ['environment'] and current_month in [4, 5]:
                    base_score += 10  # Earth Day season

            # Emergency situations override seasonal factors
            if request.request_type == "emergency":
                return 90.0

            return max(0.0, min(100.0, base_score))

        except Exception:
            return 50.0

    def process_allocation_request(self, request: AllocationRequest,
                                 donor_preferences: List[str] = None,
                                 force_allocation: bool = False) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Process a single allocation request through the smart engine."""
        try:
            # Get ONLUS data
            success, _, onlus = self.onlus_repo.get_organization_by_id(request.onlus_id)
            if not success or not onlus:
                return False, "ONLUS_NOT_FOUND", None

            onlus_data = onlus.to_dict()

            # Calculate allocation score
            success, _, score = self.calculate_allocation_score(
                request, onlus_data, donor_preferences
            )
            if not success:
                return False, "ALLOCATION_SCORE_CALCULATION_FAILED", None

            # Update request with calculated score
            request.update_allocation_score(score)
            self.request_repo.update_request(request)

            # Check if score meets minimum threshold (unless forced)
            min_threshold = 60.0
            if not force_allocation and score < min_threshold:
                request.reject_request(f"Allocation score {score:.2f} below threshold {min_threshold}")
                self.request_repo.update_request(request)
                return False, "ALLOCATION_SCORE_BELOW_THRESHOLD", {"score": score}

            # Find suitable funding pools
            success, _, pools = self.pool_repo.get_pools_for_allocation(
                request.requested_amount,
                category=request.category
            )

            if not success or not pools:
                return False, "NO_SUITABLE_FUNDING_POOLS", None

            # Select best pool based on priority weight and availability
            selected_pool = self._select_optimal_funding_pool(pools, request)

            if not selected_pool:
                return False, "NO_OPTIMAL_FUNDING_POOL", None

            # Create allocation result
            allocation_result = AllocationResult(
                request_id=str(request._id),
                onlus_id=request.onlus_id,
                donor_ids=[],  # Will be populated when processing donations
                allocated_amount=request.requested_amount,
                total_donations_amount=request.requested_amount,
                allocation_method=AllocationMethod.AUTOMATIC.value,
                allocation_factors={
                    'allocation_score': score,
                    'selected_pool_id': str(selected_pool._id),
                    'calculation_components': {
                        'funding_gap': 0.25,
                        'urgency': 0.20,
                        'performance': 0.20,
                        'preferences': 0.15,
                        'efficiency': 0.10,
                        'seasonal': 0.10
                    }
                }
            )

            # Save allocation result
            success, _, result_data = self.result_repo.create_result(allocation_result)
            if not success:
                return False, "ALLOCATION_RESULT_CREATION_FAILED", None

            # Reserve funds in the selected pool
            success, _, reservation_data = self.pool_repo.reserve_funds_in_pool(
                str(selected_pool._id),
                request.requested_amount,
                str(allocation_result._id)
            )

            if not success:
                return False, "FUNDING_RESERVATION_FAILED", None

            # Update request status
            request.approve_request(f"Auto-approved with score {score:.2f}")
            self.request_repo.update_request(request)

            current_app.logger.info(
                f"Allocation request processed successfully: {request._id} "
                f"with score {score:.2f}"
            )

            return True, "ALLOCATION_REQUEST_PROCESSED_SUCCESS", {
                "allocation_score": score,
                "allocation_result_id": str(allocation_result._id),
                "funding_pool_id": str(selected_pool._id),
                "reserved_amount": request.requested_amount
            }

        except Exception as e:
            current_app.logger.error(f"Allocation request processing failed: {str(e)}")
            return False, "ALLOCATION_REQUEST_PROCESSING_FAILED", None

    def _select_optimal_funding_pool(self, pools: List[FundingPool],
                                   request: AllocationRequest) -> Optional[FundingPool]:
        """Select the optimal funding pool for allocation."""
        try:
            if not pools:
                return None

            # Score each pool
            pool_scores = []
            for pool in pools:
                score = 0.0

                # Priority weight (40%)
                score += pool.priority_weight * 40

                # Availability ratio (30%)
                score += pool.get_availability_rate() * 30

                # Category match bonus (20%)
                if not pool.category_restrictions or request.category in pool.category_restrictions:
                    score += 20

                # Pool type bonus (10%)
                if pool.pool_type == "emergency" and request.is_emergency():
                    score += 10
                elif pool.pool_type == "general":
                    score += 5

                pool_scores.append((pool, score))

            # Sort by score and return best match
            pool_scores.sort(key=lambda x: x[1], reverse=True)
            return pool_scores[0][0] if pool_scores else None

        except Exception:
            return pools[0] if pools else None

    def execute_allocation(self, allocation_result_id: str,
                          donor_transactions: List[Dict[str, Any]]) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Execute approved allocation with actual donor transactions."""
        try:
            # Get allocation result
            success, _, allocation = self.result_repo.get_result_by_id(allocation_result_id)
            if not success or not allocation:
                return False, "ALLOCATION_RESULT_NOT_FOUND", None

            if allocation.status != AllocationResultStatus.SCHEDULED.value:
                return False, "ALLOCATION_NOT_SCHEDULED", None

            # Mark as in progress
            allocation.mark_in_progress()
            self.result_repo.update_result(allocation)

            total_processed = 0.0
            successful_transactions = []

            # Process each donor transaction
            for donor_tx in donor_transactions:
                donor_id = donor_tx.get('donor_id')
                amount = float(donor_tx.get('amount', 0))

                if amount <= 0:
                    continue

                # Create donation transaction
                transaction = Transaction(
                    user_id=donor_id,
                    transaction_type=TransactionType.DONATED.value,
                    amount=amount,
                    onlus_id=allocation.onlus_id,
                    metadata={
                        'allocation_result_id': allocation_result_id,
                        'allocation_method': allocation.allocation_method,
                        'project_title': donor_tx.get('project_title', '')
                    }
                )

                # Save transaction
                success, _, tx_data = self.transaction_repo.create_transaction(transaction)
                if success:
                    transaction.mark_completed()
                    self.transaction_repo.update_transaction(transaction)

                    # Add to allocation result
                    allocation.add_transaction(str(transaction._id), donor_id, amount)
                    successful_transactions.append({
                        'transaction_id': str(transaction._id),
                        'donor_id': donor_id,
                        'amount': amount
                    })

                    total_processed += amount

            # Update allocation result
            if total_processed > 0:
                if abs(total_processed - allocation.allocated_amount) < 0.01:
                    # Full allocation
                    allocation.mark_completed(
                        transaction_ids=[tx['transaction_id'] for tx in successful_transactions]
                    )
                    status_message = "ALLOCATION_EXECUTED_SUCCESS"
                else:
                    # Partial allocation
                    allocation.mark_partial(
                        total_processed,
                        f"Partial execution: {total_processed}/{allocation.allocated_amount}"
                    )
                    status_message = "ALLOCATION_PARTIALLY_EXECUTED"

                self.result_repo.update_result(allocation)

                # Update original request status
                self.request_repo.update_request_status(
                    allocation.request_id,
                    AllocationRequestStatus.COMPLETED.value
                )

                return True, status_message, {
                    "processed_amount": total_processed,
                    "target_amount": allocation.allocated_amount,
                    "transaction_count": len(successful_transactions),
                    "transactions": successful_transactions
                }
            else:
                # No successful transactions
                allocation.mark_failed("No successful transactions processed")
                self.result_repo.update_result(allocation)
                return False, "ALLOCATION_EXECUTION_FAILED", None

        except Exception as e:
            current_app.logger.error(f"Allocation execution failed: {str(e)}")
            return False, "ALLOCATION_EXECUTION_FAILED", None

    def process_batch_allocations(self, max_requests: int = 50,
                                min_score_threshold: float = 60.0) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Process multiple allocation requests in batch mode."""
        try:
            # Get pending high-priority requests
            success, _, requests = self.request_repo.get_high_priority_requests(
                min_score=min_score_threshold, limit=max_requests
            )

            if not success:
                return False, "PENDING_REQUESTS_RETRIEVAL_FAILED", None

            if not requests:
                return True, "NO_PENDING_REQUESTS", {"processed_count": 0}

            processed_count = 0
            successful_count = 0
            failed_count = 0
            results = []

            for request in requests:
                try:
                    success, message, result_data = self.process_allocation_request(
                        request, force_allocation=False
                    )

                    if success:
                        successful_count += 1
                        results.append({
                            'request_id': str(request._id),
                            'status': 'success',
                            'data': result_data
                        })
                    else:
                        failed_count += 1
                        results.append({
                            'request_id': str(request._id),
                            'status': 'failed',
                            'error': message
                        })

                    processed_count += 1

                except Exception as e:
                    failed_count += 1
                    current_app.logger.error(
                        f"Batch allocation failed for request {request._id}: {str(e)}"
                    )

            current_app.logger.info(
                f"Batch allocation completed: {processed_count} processed, "
                f"{successful_count} successful, {failed_count} failed"
            )

            return True, "BATCH_ALLOCATION_COMPLETED", {
                "processed_count": processed_count,
                "successful_count": successful_count,
                "failed_count": failed_count,
                "results": results
            }

        except Exception as e:
            current_app.logger.error(f"Batch allocation processing failed: {str(e)}")
            return False, "BATCH_ALLOCATION_FAILED", None

    def handle_emergency_allocation(self, request: AllocationRequest) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Handle emergency allocation with fast-track processing."""
        try:
            if not request.is_emergency():
                return False, "NOT_EMERGENCY_REQUEST", None

            current_app.logger.info(f"Processing emergency allocation: {request._id}")

            # Emergency requests bypass normal scoring thresholds
            success, message, result_data = self.process_allocation_request(
                request, force_allocation=True
            )

            if success:
                # Prioritize for immediate processing
                allocation_result_id = result_data.get('allocation_result_id')
                if allocation_result_id:
                    # Mark for immediate execution
                    success, _, allocation = self.result_repo.get_result_by_id(allocation_result_id)
                    if success and allocation:
                        allocation.allocation_method = AllocationMethod.EMERGENCY.value
                        allocation.metadata['emergency_processed'] = True
                        allocation.metadata['emergency_timestamp'] = datetime.now(timezone.utc).isoformat()
                        self.result_repo.update_result(allocation)

                return True, "EMERGENCY_ALLOCATION_SUCCESS", result_data
            else:
                return False, f"EMERGENCY_ALLOCATION_FAILED: {message}", None

        except Exception as e:
            current_app.logger.error(f"Emergency allocation failed: {str(e)}")
            return False, "EMERGENCY_ALLOCATION_FAILED", None

    def get_allocation_recommendations(self, onlus_id: str,
                                     amount_range: Tuple[float, float] = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Get allocation recommendations for an ONLUS."""
        try:
            # Get ONLUS data and compliance score
            success, _, onlus = self.onlus_repo.get_organization_by_id(onlus_id)
            if not success or not onlus:
                return False, "ONLUS_NOT_FOUND", None

            success, _, compliance = self.compliance_repo.get_current_score_by_onlus(onlus_id)
            if not success:
                compliance = None

            # Analyze recent allocation performance
            success, _, recent_results = self.result_repo.get_results_by_onlus(
                onlus_id, limit=5
            )

            recommendations = {
                'onlus_id': onlus_id,
                'current_eligibility': onlus.status == "active",
                'compliance_score': compliance.overall_score if compliance else None,
                'recommendations': []
            }

            # Compliance-based recommendations
            if compliance:
                if compliance.overall_score >= 90:
                    recommendations['recommendations'].append({
                        'type': 'positive',
                        'message': 'Excellent compliance score - eligible for premium allocations',
                        'priority': 'high'
                    })
                elif compliance.overall_score < 60:
                    recommendations['recommendations'].append({
                        'type': 'warning',
                        'message': 'Low compliance score may affect allocation eligibility',
                        'priority': 'critical'
                    })

            # Performance-based recommendations
            if recent_results:
                success_rate = sum(1 for r in recent_results if r.is_successful()) / len(recent_results)
                if success_rate >= 0.9:
                    recommendations['recommendations'].append({
                        'type': 'positive',
                        'message': 'High allocation success rate - reliable recipient',
                        'priority': 'medium'
                    })
                elif success_rate < 0.7:
                    recommendations['recommendations'].append({
                        'type': 'improvement',
                        'message': 'Consider reviewing allocation processes for better success rate',
                        'priority': 'medium'
                    })

            # Funding gap analysis
            if amount_range:
                min_amount, max_amount = amount_range
                avg_amount = (min_amount + max_amount) / 2

                recommendations['suggested_amount_range'] = {
                    'min': min_amount,
                    'max': max_amount,
                    'recommended': avg_amount
                }

            return True, "ALLOCATION_RECOMMENDATIONS_SUCCESS", recommendations

        except Exception as e:
            current_app.logger.error(f"Allocation recommendations failed: {str(e)}")
            return False, "ALLOCATION_RECOMMENDATIONS_FAILED", None