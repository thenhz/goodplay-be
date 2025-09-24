from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
from flask import current_app

from app.social.challenges.models.social_challenge import SocialChallenge, ChallengeRules, ChallengeRewards
from app.social.challenges.models.challenge_participant import ChallengeParticipant
from app.social.challenges.models.challenge_result import ChallengeResult
from app.social.challenges.repositories.social_challenge_repository import SocialChallengeRepository
from app.social.challenges.repositories.challenge_participant_repository import ChallengeParticipantRepository
from app.social.challenges.repositories.challenge_result_repository import ChallengeResultRepository


class SocialChallengeManager:
    """Service for managing social challenge lifecycle and operations"""

    def __init__(self):
        self.challenge_repo = SocialChallengeRepository()
        self.participant_repo = ChallengeParticipantRepository()
        self.result_repo = ChallengeResultRepository()

    def create_challenge(self, creator_id: str, challenge_data: Dict[str, Any]) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Create a new social challenge"""
        try:
            # Validate required fields
            required_fields = ['title', 'challenge_type', 'challenge_category']
            for field in required_fields:
                if field not in challenge_data:
                    return False, f"Missing required field: {field}", None

            # Create challenge rules
            rules_data = challenge_data.get('rules', {})
            rules = ChallengeRules(
                target_metric=rules_data.get('target_metric', ''),
                target_value=rules_data.get('target_value', 0),
                time_limit_hours=rules_data.get('time_limit_hours'),
                min_participants=rules_data.get('min_participants', 2),
                max_participants=rules_data.get('max_participants', 10),
                requires_friends=rules_data.get('requires_friends', True),
                allow_public_join=rules_data.get('allow_public_join', False),
                scoring_method=rules_data.get('scoring_method', 'highest'),
                difficulty_multiplier=rules_data.get('difficulty_multiplier', 1.0)
            )

            # Create challenge rewards
            rewards_data = challenge_data.get('rewards', {})
            rewards = ChallengeRewards(
                winner_credits=rewards_data.get('winner_credits', 100),
                participant_credits=rewards_data.get('participant_credits', 25),
                winner_badges=rewards_data.get('winner_badges', []),
                participant_badges=rewards_data.get('participant_badges', []),
                social_bonus_multiplier=rewards_data.get('social_bonus_multiplier', 1.0),
                impact_multiplier=rewards_data.get('impact_multiplier', 1.0)
            )

            # Set end date
            duration_hours = rules_data.get('time_limit_hours', 168)  # Default 7 days
            end_date = datetime.utcnow() + timedelta(hours=duration_hours)

            # Create challenge
            challenge = SocialChallenge(
                creator_id=creator_id,
                title=challenge_data['title'],
                description=challenge_data.get('description', ''),
                challenge_type=challenge_data['challenge_type'],
                challenge_category=challenge_data['challenge_category'],
                difficulty_level=challenge_data.get('difficulty_level', 1),
                tags=challenge_data.get('tags', []),
                rules=rules,
                rewards=rewards,
                max_participants=rules.max_participants,
                end_date=end_date,
                is_public=challenge_data.get('is_public', False),
                friends_only=challenge_data.get('friends_only', True)
            )

            # Save to database
            challenge_id = self.challenge_repo.create_challenge(challenge)
            if not challenge_id:
                return False, "Failed to create challenge", None

            # Auto-join creator as participant
            creator_participant = ChallengeParticipant(
                challenge_id=challenge.challenge_id,
                user_id=creator_id
            )

            participant_id = self.participant_repo.create_participant(creator_participant)
            if participant_id:
                # Update challenge participant count
                challenge.add_participant(creator_id)
                self.challenge_repo.update_challenge(challenge.challenge_id, {
                    "participant_ids": challenge.participant_ids,
                    "current_participants": challenge.current_participants
                })

            current_app.logger.info(f"Social challenge created: {challenge.challenge_id} by {creator_id}")

            return True, "Challenge created successfully", {
                "challenge_id": challenge.challenge_id,
                "creator_joined": participant_id is not None
            }

        except Exception as e:
            current_app.logger.error(f"Error creating challenge: {str(e)}")
            return False, "Failed to create challenge", None

    def join_challenge(self, challenge_id: str, user_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Join a social challenge"""
        try:
            # Get challenge
            challenge = self.challenge_repo.get_by_challenge_id(challenge_id)
            if not challenge:
                return False, "Challenge not found", None

            # Check if user can join
            if not challenge.can_user_join(user_id):
                if challenge.status != "open":
                    return False, "Challenge is not open for joining", None
                elif challenge.is_expired():
                    return False, "Challenge has expired", None
                elif challenge.current_participants >= challenge.max_participants:
                    return False, "Challenge is full", None
                elif user_id in challenge.participant_ids:
                    return False, "User already joined challenge", None
                else:
                    return False, "Cannot join challenge", None

            # Check friend requirements
            if challenge.friends_only and user_id != challenge.creator_id:
                # TODO: Check if user is friend with creator
                # For now, we'll allow joining
                pass

            # Add participant
            participant = ChallengeParticipant(
                challenge_id=challenge_id,
                user_id=user_id
            )

            participant_id = self.participant_repo.create_participant(participant)
            if not participant_id:
                return False, "Failed to join challenge", None

            # Update challenge
            success = challenge.add_participant(user_id)
            if success:
                self.challenge_repo.update_challenge(challenge_id, {
                    "participant_ids": challenge.participant_ids,
                    "current_participants": challenge.current_participants
                })

            current_app.logger.info(f"User {user_id} joined challenge {challenge_id}")

            return True, "Successfully joined challenge", {
                "participant_id": participant_id,
                "participant_count": challenge.current_participants
            }

        except Exception as e:
            current_app.logger.error(f"Error joining challenge: {str(e)}")
            return False, "Failed to join challenge", None

    def leave_challenge(self, challenge_id: str, user_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Leave a social challenge"""
        try:
            # Get challenge
            challenge = self.challenge_repo.get_by_challenge_id(challenge_id)
            if not challenge:
                return False, "Challenge not found", None

            # Check if user is participant
            if not challenge.is_participant(user_id):
                return False, "User is not a participant", None

            # Cannot leave if creator
            if user_id == challenge.creator_id:
                return False, "Creator cannot leave challenge", None

            # Update participant status
            participant_updated = self.participant_repo.quit_challenge(challenge_id, user_id)
            if not participant_updated:
                current_app.logger.warning(f"Failed to update participant status for {user_id} in {challenge_id}")

            # Remove from challenge
            success = challenge.remove_participant(user_id)
            if success:
                self.challenge_repo.update_challenge(challenge_id, {
                    "participant_ids": challenge.participant_ids,
                    "current_participants": challenge.current_participants
                })

            current_app.logger.info(f"User {user_id} left challenge {challenge_id}")

            return True, "Successfully left challenge", {
                "participant_count": challenge.current_participants
            }

        except Exception as e:
            current_app.logger.error(f"Error leaving challenge: {str(e)}")
            return False, "Failed to leave challenge", None

    def invite_users(self, challenge_id: str, inviter_id: str, user_ids: List[str]) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Invite users to a social challenge"""
        try:
            # Get challenge
            challenge = self.challenge_repo.get_by_challenge_id(challenge_id)
            if not challenge:
                return False, "Challenge not found", None

            # Check if inviter is creator or participant
            if inviter_id != challenge.creator_id and not challenge.is_participant(inviter_id):
                return False, "Only participants can invite others", None

            # Check challenge status
            if challenge.status != "open":
                return False, "Challenge is not open for invitations", None

            invited_count = 0
            already_invited = []
            invalid_users = []

            for user_id in user_ids:
                # Skip self
                if user_id == inviter_id:
                    continue

                # Skip if already participant or invited
                if user_id in challenge.participant_ids or user_id in challenge.invited_user_ids:
                    already_invited.append(user_id)
                    continue

                # TODO: Validate user exists
                # For now, we'll assume all users are valid

                # Add to invited list
                success = challenge.invite_user(user_id)
                if success:
                    invited_count += 1

            # Update challenge
            if invited_count > 0:
                self.challenge_repo.update_challenge(challenge_id, {
                    "invited_user_ids": challenge.invited_user_ids
                })

            current_app.logger.info(f"User {inviter_id} invited {invited_count} users to challenge {challenge_id}")

            return True, "Invitations sent successfully", {
                "invited_count": invited_count,
                "already_invited": already_invited,
                "total_invited": len(challenge.invited_user_ids)
            }

        except Exception as e:
            current_app.logger.error(f"Error inviting users: {str(e)}")
            return False, "Failed to send invitations", None

    def start_challenge(self, challenge_id: str, initiator_id: str = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Start a social challenge"""
        try:
            # Get challenge
            challenge = self.challenge_repo.get_by_challenge_id(challenge_id)
            if not challenge:
                return False, "Challenge not found", None

            # Check if challenge can start
            if not challenge.can_start():
                if challenge.status != "open":
                    return False, "Challenge is not in open status", None
                elif challenge.is_expired():
                    return False, "Challenge has expired", None
                elif challenge.current_participants < challenge.rules.min_participants:
                    return False, f"Need at least {challenge.rules.min_participants} participants", None
                else:
                    return False, "Challenge cannot be started", None

            # Start challenge
            success = challenge.start_challenge()
            if not success:
                return False, "Failed to start challenge", None

            # Update in database
            self.challenge_repo.update_challenge(challenge_id, {
                "status": challenge.status,
                "start_date": challenge.start_date
            })

            current_app.logger.info(f"Challenge {challenge_id} started by {initiator_id}")

            return True, "Challenge started successfully", {
                "start_date": challenge.start_date.isoformat(),
                "participant_count": challenge.current_participants
            }

        except Exception as e:
            current_app.logger.error(f"Error starting challenge: {str(e)}")
            return False, "Failed to start challenge", None

    def complete_challenge(self, challenge_id: str, results_data: List[Dict[str, Any]] = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Complete a social challenge and calculate final results"""
        try:
            # Get challenge
            challenge = self.challenge_repo.get_by_challenge_id(challenge_id)
            if not challenge:
                return False, "Challenge not found", None

            # Check if challenge can be completed
            if challenge.status not in ["active", "open"]:
                return False, "Challenge is not active", None

            # Get all participants
            participants = self.participant_repo.get_challenge_participants(challenge_id, status="active")

            # Calculate final results if not provided
            if not results_data:
                results_data = self._calculate_final_results(challenge, participants)

            # Complete challenge
            success = challenge.complete_challenge(results_data)
            if not success:
                return False, "Failed to complete challenge", None

            # Update participants
            completed_count = 0
            for result in results_data:
                user_id = result.get("user_id")
                final_score = result.get("score", 0)
                rank = result.get("rank", 0)

                # Update participant
                participant_updated = self.participant_repo.complete_participation(
                    challenge_id, user_id, final_score, rank
                )
                if participant_updated:
                    completed_count += 1

                # Create result record
                participant = next((p for p in participants if p.user_id == user_id), None)
                if participant:
                    challenge_result = ChallengeResult.create_from_participant(
                        participant, challenge.rules.__dict__
                    )
                    self.result_repo.create_result(challenge_result)

            # Update challenge in database
            self.challenge_repo.update_challenge(challenge_id, {
                "status": challenge.status,
                "completion_percentage": challenge.completion_percentage,
                "leaderboard_data": challenge.leaderboard_data,
                "winner_ids": challenge.winner_ids
            })

            current_app.logger.info(f"Challenge {challenge_id} completed with {completed_count} participants")

            return True, "Challenge completed successfully", {
                "winner_ids": challenge.winner_ids,
                "completed_participants": completed_count,
                "total_participants": len(participants)
            }

        except Exception as e:
            current_app.logger.error(f"Error completing challenge: {str(e)}")
            return False, "Failed to complete challenge", None

    def cancel_challenge(self, challenge_id: str, canceller_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Cancel a social challenge"""
        try:
            # Get challenge
            challenge = self.challenge_repo.get_by_challenge_id(challenge_id)
            if not challenge:
                return False, "Challenge not found", None

            # Check permissions (only creator can cancel)
            if canceller_id != challenge.creator_id:
                return False, "Only creator can cancel challenge", None

            # Cancel challenge
            success = challenge.cancel_challenge()
            if not success:
                return False, "Challenge cannot be cancelled", None

            # Update in database
            self.challenge_repo.update_challenge(challenge_id, {
                "status": challenge.status
            })

            current_app.logger.info(f"Challenge {challenge_id} cancelled by {canceller_id}")

            return True, "Challenge cancelled successfully", {
                "participant_count": challenge.current_participants
            }

        except Exception as e:
            current_app.logger.error(f"Error cancelling challenge: {str(e)}")
            return False, "Failed to cancel challenge", None

    def update_progress(self, challenge_id: str, user_id: str, progress_data: Dict[str, Any]) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Update participant progress in challenge"""
        try:
            # Get challenge
            challenge = self.challenge_repo.get_by_challenge_id(challenge_id)
            if not challenge:
                return False, "Challenge not found", None

            # Check if user is participant
            if not challenge.is_participant(user_id):
                return False, "User is not a participant", None

            # Check if challenge is active
            if challenge.status != "active":
                return False, "Challenge is not active", None

            # Update participant progress
            success = self.participant_repo.update_progress(challenge_id, user_id, progress_data)
            if not success:
                return False, "Failed to update progress", None

            # Update challenge progress if needed
            challenge.update_progress(user_id, progress_data)
            self.challenge_repo.update_challenge(challenge_id, {
                "leaderboard_data": challenge.leaderboard_data,
                "completion_percentage": challenge.completion_percentage
            })

            current_app.logger.info(f"Progress updated for {user_id} in challenge {challenge_id}")

            return True, "Progress updated successfully", {
                "current_progress": progress_data,
                "completion_percentage": challenge.completion_percentage
            }

        except Exception as e:
            current_app.logger.error(f"Error updating progress: {str(e)}")
            return False, "Failed to update progress", None

    def get_challenge_details(self, challenge_id: str, user_id: str = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Get detailed challenge information"""
        try:
            # Get challenge
            challenge = self.challenge_repo.get_by_challenge_id(challenge_id)
            if not challenge:
                return False, "Challenge not found", None

            # Get participants
            participants = self.participant_repo.get_challenge_participants(challenge_id)

            challenge_data = challenge.to_api_dict()
            challenge_data["participants"] = [p.to_api_dict() for p in participants]

            # Add user-specific information if provided
            if user_id:
                user_participant = next((p for p in participants if p.user_id == user_id), None)
                if user_participant:
                    challenge_data["user_participation"] = user_participant.to_api_dict(include_sensitive=True)

            return True, "Challenge details retrieved", challenge_data

        except Exception as e:
            current_app.logger.error(f"Error getting challenge details: {str(e)}")
            return False, "Failed to retrieve challenge details", None

    def get_user_challenges(self, user_id: str, include_completed: bool = False,
                           limit: int = 20, offset: int = 0) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Get challenges for a user"""
        try:
            challenges = self.challenge_repo.get_challenges_by_user(
                user_id, include_completed, limit, offset
            )

            challenges_data = [challenge.to_api_dict() for challenge in challenges]

            return True, "User challenges retrieved", {
                "challenges": challenges_data,
                "count": len(challenges_data)
            }

        except Exception as e:
            current_app.logger.error(f"Error getting user challenges: {str(e)}")
            return False, "Failed to retrieve challenges", None

    def _calculate_final_results(self, challenge: SocialChallenge,
                               participants: List[ChallengeParticipant]) -> List[Dict[str, Any]]:
        """Calculate final results for challenge completion"""
        results = []

        for participant in participants:
            if participant.status != "active":
                continue

            # Calculate final score based on current progress and social engagement
            base_score = participant.current_progress.get("current_value", 0)
            social_bonus = participant.social_score * 0.1  # 10% of social score as bonus
            final_score = base_score + social_bonus

            results.append({
                "user_id": participant.user_id,
                "score": final_score,
                "base_score": base_score,
                "social_bonus": social_bonus,
                "completion_percentage": participant.completion_percentage
            })

        # Sort by score and assign ranks
        results.sort(key=lambda x: x["score"], reverse=True)
        for i, result in enumerate(results):
            result["rank"] = i + 1

        return results

    def cleanup_expired_challenges(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Clean up expired challenges"""
        try:
            expired_challenges = self.challenge_repo.get_expired_challenges()
            updated_count = 0

            for challenge in expired_challenges:
                success = challenge.expire_challenge()
                if success:
                    self.challenge_repo.update_challenge(challenge.challenge_id, {
                        "status": challenge.status,
                        "completed_at": challenge.completion_percentage
                    })
                    updated_count += 1

            current_app.logger.info(f"Cleaned up {updated_count} expired challenges")

            return True, "Expired challenges cleaned up", {
                "expired_count": updated_count
            }

        except Exception as e:
            current_app.logger.error(f"Error cleaning up expired challenges: {str(e)}")
            return False, "Failed to cleanup expired challenges", None