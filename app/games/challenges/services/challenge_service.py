from typing import Tuple, Optional, Dict, Any, List
from flask import current_app
from datetime import datetime, timedelta

from ..repositories.challenge_repository import ChallengeRepository
from ..repositories.challenge_participant_repository import ChallengeParticipantRepository
from ..models.challenge import Challenge
from ..models.challenge_participant import ChallengeParticipant
from ..models.challenge_result import ChallengeResult
from ...repositories.game_repository import GameRepository

class ChallengeService:
    """Service for managing direct challenges between players"""

    def __init__(self):
        self.challenge_repository = ChallengeRepository()
        self.participant_repository = ChallengeParticipantRepository()
        self.game_repository = GameRepository()

    def create_1v1_challenge(self, challenger_id: str, challenged_id: str, game_id: str,
                           timeout_minutes: int = 60, game_config: Dict[str, Any] = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Create a 1v1 challenge between two players.

        Args:
            challenger_id: User ID of the challenger
            challenged_id: User ID of the challenged player
            game_id: ID of the game to play
            timeout_minutes: Minutes until challenge expires
            game_config: Optional game configuration

        Returns:
            Tuple[bool, str, Optional[Dict[str, Any]]]: (success, message, data)
        """
        try:
            # Validate inputs
            if challenger_id == challenged_id:
                return False, "CANNOT_CHALLENGE_YOURSELF", None

            # Validate game exists and supports multiplayer
            game = self.game_repository.get_game_by_id(game_id)
            if not game:
                return False, "GAME_NOT_FOUND", None

            if not game.is_active:
                return False, "GAME_NOT_ACTIVE", None

            if game.max_players < 2:
                return False, "GAME_DOES_NOT_SUPPORT_MULTIPLAYER", None

            # Check if users already have an active challenge
            existing_challenge = self._get_existing_challenge(challenger_id, challenged_id, game_id)
            if existing_challenge:
                return False, "ACTIVE_CHALLENGE_EXISTS", {
                    "existing_challenge": existing_challenge.to_api_dict()
                }

            # Create the challenge
            challenge = Challenge.create_1v1_challenge(
                challenger_id=challenger_id,
                challenged_id=challenged_id,
                game_id=game_id,
                timeout_minutes=timeout_minutes,
                game_config=game_config
            )

            challenge_id = self.challenge_repository.create_challenge(challenge)

            # Create participant records
            challenger_participant = ChallengeParticipant.create_challenger(challenge.challenge_id, challenger_id)
            challenged_participant = ChallengeParticipant.create_invited(challenge.challenge_id, challenged_id)

            self.participant_repository.create_participant(challenger_participant)
            self.participant_repository.create_participant(challenged_participant)

            current_app.logger.info(f"Created 1v1 challenge {challenge.challenge_id} between {challenger_id} and {challenged_id}")

            return True, "CHALLENGE_CREATED_SUCCESSFULLY", {
                "challenge": challenge.to_api_dict(),
                "challenge_id": challenge.challenge_id
            }

        except Exception as e:
            current_app.logger.error(f"Failed to create 1v1 challenge: {str(e)}")
            return False, "FAILED_TO_CREATE_CHALLENGE", None

    def create_nvn_challenge(self, challenger_id: str, max_participants: int, game_id: str,
                           min_participants: int = None, timeout_minutes: int = 60,
                           game_config: Dict[str, Any] = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Create an NvN challenge that others can join.

        Args:
            challenger_id: User ID of the challenger
            max_participants: Maximum number of participants
            game_id: ID of the game to play
            min_participants: Minimum participants to start (default: max/2)
            timeout_minutes: Minutes until challenge expires
            game_config: Optional game configuration

        Returns:
            Tuple[bool, str, Optional[Dict[str, Any]]]: (success, message, data)
        """
        try:
            # Validate inputs
            if max_participants < 2 or max_participants > 20:
                return False, "INVALID_PARTICIPANT_COUNT", None

            # Validate game
            game = self.game_repository.get_game_by_id(game_id)
            if not game:
                return False, "GAME_NOT_FOUND", None

            if not game.is_active:
                return False, "GAME_NOT_ACTIVE", None

            if game.max_players < max_participants:
                return False, "GAME_DOES_NOT_SUPPORT_PARTICIPANT_COUNT", None

            # Create the challenge
            challenge = Challenge.create_nvn_challenge(
                challenger_id=challenger_id,
                max_participants=max_participants,
                game_id=game_id,
                timeout_minutes=timeout_minutes,
                game_config=game_config,
                min_participants=min_participants
            )

            challenge_id = self.challenge_repository.create_challenge(challenge)

            # Create challenger participant
            challenger_participant = ChallengeParticipant.create_challenger(challenge.challenge_id, challenger_id)
            self.participant_repository.create_participant(challenger_participant)

            current_app.logger.info(f"Created NvN challenge {challenge.challenge_id} by {challenger_id} for {max_participants} participants")

            return True, "NVN_CHALLENGE_CREATED_SUCCESSFULLY", {
                "challenge": challenge.to_api_dict(),
                "challenge_id": challenge.challenge_id
            }

        except Exception as e:
            current_app.logger.error(f"Failed to create NvN challenge: {str(e)}")
            return False, "FAILED_TO_CREATE_CHALLENGE", None

    def join_public_challenge(self, user_id: str, challenge_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Join a public NvN challenge.

        Args:
            user_id: User ID joining the challenge
            challenge_id: Challenge ID to join

        Returns:
            Tuple[bool, str, Optional[Dict[str, Any]]]: (success, message, data)
        """
        try:
            challenge = self.challenge_repository.get_challenge_by_challenge_id(challenge_id)
            if not challenge:
                return False, "CHALLENGE_NOT_FOUND", None

            if challenge.status != "pending":
                return False, "CHALLENGE_NOT_JOINABLE", None

            if not challenge.is_public:
                return False, "CHALLENGE_NOT_PUBLIC", None

            if challenge.is_expired():
                return False, "CHALLENGE_EXPIRED", None

            # Check if user is already participating
            if challenge.is_participant(user_id):
                return False, "ALREADY_PARTICIPATING", None

            # Check if challenge is full
            if len(challenge.get_all_participant_ids()) >= challenge.max_participants:
                return False, "CHALLENGE_FULL", None

            # Add participant to challenge
            success = self.challenge_repository.add_participant_to_challenge(challenge_id, user_id)
            if not success:
                return False, "FAILED_TO_JOIN_CHALLENGE", None

            # Create participant record
            participant = ChallengeParticipant.create_joined(challenge_id, user_id)
            self.participant_repository.create_participant(participant)

            # Check if challenge can start
            updated_challenge = self.challenge_repository.get_challenge_by_challenge_id(challenge_id)
            if updated_challenge and updated_challenge.can_start():
                # Auto-start if configured
                if updated_challenge.challenge_config.get("auto_start", False):
                    self._start_challenge(challenge_id)

            current_app.logger.info(f"User {user_id} joined challenge {challenge_id}")

            return True, "JOINED_CHALLENGE_SUCCESSFULLY", {
                "challenge": updated_challenge.to_api_dict() if updated_challenge else None
            }

        except Exception as e:
            current_app.logger.error(f"Failed to join challenge {challenge_id}: {str(e)}")
            return False, "FAILED_TO_JOIN_CHALLENGE", None

    def accept_challenge_invitation(self, user_id: str, challenge_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Accept a challenge invitation.

        Args:
            user_id: User ID accepting the invitation
            challenge_id: Challenge ID

        Returns:
            Tuple[bool, str, Optional[Dict[str, Any]]]: (success, message, data)
        """
        try:
            # Get participant record
            participant = self.participant_repository.get_participant(challenge_id, user_id)
            if not participant:
                return False, "INVITATION_NOT_FOUND", None

            if participant.status != "invited":
                return False, "INVITATION_ALREADY_RESPONDED", None

            # Accept the invitation
            success = self.participant_repository.accept_invitation(challenge_id, user_id)
            if not success:
                return False, "FAILED_TO_ACCEPT_INVITATION", None

            # Check if challenge can start
            challenge = self.challenge_repository.get_challenge_by_challenge_id(challenge_id)
            if challenge and challenge.can_start():
                # Check if all participants have accepted
                participants = self.participant_repository.get_challenge_participants(challenge_id)
                all_accepted = all(p.status in ["accepted", "challenger"] for p in participants)

                if all_accepted:
                    self._start_challenge(challenge_id)

            current_app.logger.info(f"User {user_id} accepted challenge {challenge_id}")

            return True, "INVITATION_ACCEPTED_SUCCESSFULLY", {
                "challenge": challenge.to_api_dict() if challenge else None
            }

        except Exception as e:
            current_app.logger.error(f"Failed to accept invitation: {str(e)}")
            return False, "FAILED_TO_ACCEPT_INVITATION", None

    def decline_challenge_invitation(self, user_id: str, challenge_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Decline a challenge invitation.

        Args:
            user_id: User ID declining the invitation
            challenge_id: Challenge ID

        Returns:
            Tuple[bool, str, Optional[Dict[str, Any]]]: (success, message, data)
        """
        try:
            # Get participant record
            participant = self.participant_repository.get_participant(challenge_id, user_id)
            if not participant:
                return False, "INVITATION_NOT_FOUND", None

            if participant.status != "invited":
                return False, "INVITATION_ALREADY_RESPONDED", None

            # Decline the invitation
            success = self.participant_repository.decline_invitation(challenge_id, user_id)
            if not success:
                return False, "FAILED_TO_DECLINE_INVITATION", None

            # Remove from challenge participants
            self.challenge_repository.remove_participant_from_challenge(challenge_id, user_id)

            current_app.logger.info(f"User {user_id} declined challenge {challenge_id}")

            return True, "INVITATION_DECLINED_SUCCESSFULLY", None

        except Exception as e:
            current_app.logger.error(f"Failed to decline invitation: {str(e)}")
            return False, "FAILED_TO_DECLINE_INVITATION", None

    def start_challenge_participation(self, user_id: str, challenge_id: str, game_session_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Start a user's participation in an active challenge.

        Args:
            user_id: User ID starting participation
            challenge_id: Challenge ID
            game_session_id: Game session ID

        Returns:
            Tuple[bool, str, Optional[Dict[str, Any]]]: (success, message, data)
        """
        try:
            challenge = self.challenge_repository.get_challenge_by_challenge_id(challenge_id)
            if not challenge:
                return False, "CHALLENGE_NOT_FOUND", None

            if challenge.status != "active":
                return False, "CHALLENGE_NOT_ACTIVE", None

            if not challenge.is_participant(user_id):
                return False, "NOT_CHALLENGE_PARTICIPANT", None

            # Start participation
            success = self.participant_repository.start_participation(challenge_id, user_id, game_session_id)
            if not success:
                return False, "FAILED_TO_START_PARTICIPATION", None

            current_app.logger.info(f"User {user_id} started participation in challenge {challenge_id}")

            return True, "PARTICIPATION_STARTED_SUCCESSFULLY", {
                "challenge_id": challenge_id,
                "game_session_id": game_session_id
            }

        except Exception as e:
            current_app.logger.error(f"Failed to start participation: {str(e)}")
            return False, "FAILED_TO_START_PARTICIPATION", None

    def complete_challenge_participation(self, user_id: str, challenge_id: str, score: int,
                                       performance_data: Dict[str, Any] = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Complete a user's participation in a challenge.

        Args:
            user_id: User ID completing participation
            challenge_id: Challenge ID
            score: Final score
            performance_data: Optional performance data

        Returns:
            Tuple[bool, str, Optional[Dict[str, Any]]]: (success, message, data)
        """
        try:
            challenge = self.challenge_repository.get_challenge_by_challenge_id(challenge_id)
            if not challenge:
                return False, "CHALLENGE_NOT_FOUND", None

            if challenge.status != "active":
                return False, "CHALLENGE_NOT_ACTIVE", None

            # Complete participation
            success = self.participant_repository.complete_participation(
                challenge_id, user_id, score, performance_data=performance_data
            )
            if not success:
                return False, "FAILED_TO_COMPLETE_PARTICIPATION", None

            # Add result to challenge
            self.challenge_repository.add_challenge_result(challenge_id, user_id, score, performance_data)

            # Check if all participants have completed
            participants = self.participant_repository.get_challenge_participants(challenge_id)
            all_completed = all(
                p.status in ["completed", "dropped"] or p.participant_type == "challenger"
                for p in participants
            )

            if all_completed:
                self._complete_challenge(challenge_id)

            current_app.logger.info(f"User {user_id} completed participation in challenge {challenge_id} with score {score}")

            return True, "PARTICIPATION_COMPLETED_SUCCESSFULLY", {
                "challenge_id": challenge_id,
                "score": score
            }

        except Exception as e:
            current_app.logger.error(f"Failed to complete participation: {str(e)}")
            return False, "FAILED_TO_COMPLETE_PARTICIPATION", None

    def get_user_challenges(self, user_id: str, status: str = None, limit: int = 50) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Get challenges for a user.

        Args:
            user_id: User ID
            status: Optional status filter
            limit: Maximum number of challenges to return

        Returns:
            Tuple[bool, str, Optional[Dict[str, Any]]]: (success, message, data)
        """
        try:
            challenges = self.challenge_repository.get_challenges_by_user(user_id, status, limit)
            challenges_data = [challenge.to_api_dict() for challenge in challenges]

            return True, "USER_CHALLENGES_RETRIEVED", {
                "challenges": challenges_data,
                "count": len(challenges_data)
            }

        except Exception as e:
            current_app.logger.error(f"Failed to get user challenges: {str(e)}")
            return False, "FAILED_TO_GET_USER_CHALLENGES", None

    def get_public_challenges(self, game_id: str = None, limit: int = 20) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Get available public challenges."""
        try:
            challenges = self.challenge_repository.get_public_challenges(game_id, "pending", limit)
            challenges_data = [challenge.to_api_dict() for challenge in challenges]

            return True, "PUBLIC_CHALLENGES_RETRIEVED", {
                "challenges": challenges_data,
                "count": len(challenges_data)
            }

        except Exception as e:
            current_app.logger.error(f"Failed to get public challenges: {str(e)}")
            return False, "FAILED_TO_GET_PUBLIC_CHALLENGES", None

    def _get_existing_challenge(self, user1_id: str, user2_id: str, game_id: str) -> Optional[Challenge]:
        """Check for existing active challenge between two users"""
        challenges = self.challenge_repository.get_challenges_by_user(user1_id, "pending")
        for challenge in challenges:
            if challenge.game_id == game_id and user2_id in challenge.get_all_participant_ids():
                return challenge

        challenges = self.challenge_repository.get_challenges_by_user(user1_id, "active")
        for challenge in challenges:
            if challenge.game_id == game_id and user2_id in challenge.get_all_participant_ids():
                return challenge

        return None

    def _start_challenge(self, challenge_id: str) -> bool:
        """Start a challenge"""
        return self.challenge_repository.update_challenge_status(
            challenge_id, "active", {"started_at": datetime.utcnow()}
        )

    def _complete_challenge(self, challenge_id: str) -> bool:
        """Complete a challenge and calculate results"""
        try:
            challenge = self.challenge_repository.get_challenge_by_challenge_id(challenge_id)
            participants = self.participant_repository.get_challenge_participants(challenge_id)

            if challenge and participants:
                # Create challenge result
                participant_data = [p.to_dict() for p in participants if p.status == "completed"]
                challenge_result = ChallengeResult.create_from_challenge(challenge, participant_data)

                if challenge_result:
                    # Determine winners from results
                    winner_ids = challenge_result.winner_ids
                    self.challenge_repository.complete_challenge(challenge_id, winner_ids)

                return True

        except Exception as e:
            current_app.logger.error(f"Failed to complete challenge: {str(e)}")

        return False