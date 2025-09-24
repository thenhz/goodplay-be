from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
from flask import current_app

from app.social.challenges.models.social_challenge import SocialChallenge
from app.social.challenges.models.challenge_interaction import ChallengeInteraction
from app.social.challenges.repositories.social_challenge_repository import SocialChallengeRepository
from app.social.challenges.repositories.challenge_interaction_repository import ChallengeInteractionRepository
from app.social.challenges.repositories.challenge_participant_repository import ChallengeParticipantRepository
from app.social.challenges.services.notification_service import NotificationService


class InteractionService:
    """Service for managing social interactions within challenges (cheering, comments, reactions)"""

    def __init__(self):
        self.challenge_repo = SocialChallengeRepository()
        self.interaction_repo = ChallengeInteractionRepository()
        self.participant_repo = ChallengeParticipantRepository()
        self.notification_service = NotificationService()

    def send_cheer(self, challenge_id: str, from_user_id: str, to_user_id: str,
                   emoji: str = "👏", reaction_type: str = "cheer") -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Send a cheer to another participant"""
        try:
            # Validate challenge and participants
            validation_result = self._validate_interaction(challenge_id, from_user_id, to_user_id)
            if not validation_result[0]:
                return validation_result

            challenge = validation_result[2]["challenge"]

            # Check if challenge allows cheering
            if not challenge.allow_cheering:
                return False, "Cheering is not allowed in this challenge", None

            # Create cheer interaction
            cheer = ChallengeInteraction.create_cheer(challenge_id, from_user_id, to_user_id, emoji, reaction_type)

            interaction_id = self.interaction_repo.create_interaction(cheer)
            if not interaction_id:
                return False, "Failed to send cheer", None

            # Update participant social metrics
            self._update_social_metrics(challenge_id, from_user_id, "cheer_given")
            self._update_social_metrics(challenge_id, to_user_id, "cheer_received")

            # Send notification
            self.notification_service.notify_social_interaction(challenge, cheer)

            current_app.logger.info(f"Cheer sent from {from_user_id} to {to_user_id} in challenge {challenge_id}")

            return True, "Cheer sent successfully", {
                "interaction_id": interaction_id,
                "emoji": emoji,
                "reaction_type": reaction_type
            }

        except Exception as e:
            current_app.logger.error(f"Error sending cheer: {str(e)}")
            return False, "Failed to send cheer", None

    def send_comment(self, challenge_id: str, from_user_id: str, to_user_id: str,
                    content: str, context_type: str = "general",
                    context_data: Dict[str, Any] = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Send a comment to another participant"""
        try:
            # Validate input
            if not content or len(content.strip()) == 0:
                return False, "Comment content cannot be empty", None

            if len(content) > 500:  # Reasonable limit
                return False, "Comment too long (max 500 characters)", None

            # Validate challenge and participants
            validation_result = self._validate_interaction(challenge_id, from_user_id, to_user_id)
            if not validation_result[0]:
                return validation_result

            challenge = validation_result[2]["challenge"]

            # Check if challenge allows comments
            if not challenge.allow_comments:
                return False, "Comments are not allowed in this challenge", None

            # Create comment interaction
            comment = ChallengeInteraction.create_comment(
                challenge_id, from_user_id, to_user_id, content.strip(), context_type, context_data
            )

            interaction_id = self.interaction_repo.create_interaction(comment)
            if not interaction_id:
                return False, "Failed to send comment", None

            # Update participant social metrics
            self._update_social_metrics(challenge_id, from_user_id, "comment_made")
            self._update_social_metrics(challenge_id, to_user_id, "comment_received")

            # Send notification
            self.notification_service.notify_social_interaction(challenge, comment)

            current_app.logger.info(f"Comment sent from {from_user_id} to {to_user_id} in challenge {challenge_id}")

            return True, "Comment sent successfully", {
                "interaction_id": interaction_id,
                "content": content.strip(),
                "context_type": context_type
            }

        except Exception as e:
            current_app.logger.error(f"Error sending comment: {str(e)}")
            return False, "Failed to send comment", None

    def celebrate_milestone(self, challenge_id: str, from_user_id: str, to_user_id: str,
                          milestone_data: Dict[str, Any]) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Send a milestone celebration"""
        try:
            # Validate challenge and participants
            validation_result = self._validate_interaction(challenge_id, from_user_id, to_user_id)
            if not validation_result[0]:
                return validation_result

            challenge = validation_result[2]["challenge"]

            # Create milestone celebration
            celebration = ChallengeInteraction.create_milestone_celebration(
                challenge_id, from_user_id, to_user_id, milestone_data
            )

            interaction_id = self.interaction_repo.create_interaction(celebration)
            if not interaction_id:
                return False, "Failed to send celebration", None

            # Update social metrics (celebrations count as special cheers)
            self._update_social_metrics(challenge_id, from_user_id, "cheer_given")
            self._update_social_metrics(challenge_id, to_user_id, "cheer_received")

            # Send notification
            self.notification_service.notify_social_interaction(challenge, celebration)

            current_app.logger.info(f"Milestone celebration sent from {from_user_id} to {to_user_id}")

            return True, "Milestone celebration sent", {
                "interaction_id": interaction_id,
                "milestone": milestone_data
            }

        except Exception as e:
            current_app.logger.error(f"Error sending milestone celebration: {str(e)}")
            return False, "Failed to send celebration", None

    def like_interaction(self, interaction_id: str, user_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Like an interaction"""
        try:
            # Get interaction
            interaction = self.interaction_repo.get_interaction_by_id(interaction_id)
            if not interaction:
                return False, "Interaction not found", None

            # Check if user can like this interaction
            if not interaction.can_user_interact(user_id):
                return False, "Cannot like this interaction", None

            # Add like
            success = self.interaction_repo.add_like(interaction_id, user_id)
            if not success:
                return False, "Already liked or failed to like", None

            current_app.logger.info(f"User {user_id} liked interaction {interaction_id}")

            return True, "Interaction liked successfully", {
                "likes_count": interaction.likes_count + 1
            }

        except Exception as e:
            current_app.logger.error(f"Error liking interaction: {str(e)}")
            return False, "Failed to like interaction", None

    def unlike_interaction(self, interaction_id: str, user_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Remove like from an interaction"""
        try:
            success = self.interaction_repo.remove_like(interaction_id, user_id)
            if not success:
                return False, "Not liked or failed to unlike", None

            current_app.logger.info(f"User {user_id} unliked interaction {interaction_id}")

            return True, "Like removed successfully", {}

        except Exception as e:
            current_app.logger.error(f"Error unliking interaction: {str(e)}")
            return False, "Failed to remove like", None

    def reply_to_interaction(self, interaction_id: str, from_user_id: str,
                           content: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Reply to an interaction"""
        try:
            # Validate content
            if not content or len(content.strip()) == 0:
                return False, "Reply content cannot be empty", None

            if len(content) > 300:  # Shorter limit for replies
                return False, "Reply too long (max 300 characters)", None

            # Add reply
            reply_id = self.interaction_repo.add_reply(interaction_id, from_user_id, content.strip())
            if not reply_id:
                return False, "Failed to add reply", None

            current_app.logger.info(f"Reply added by {from_user_id} to interaction {interaction_id}")

            return True, "Reply added successfully", {
                "reply_id": reply_id,
                "content": content.strip()
            }

        except Exception as e:
            current_app.logger.error(f"Error adding reply: {str(e)}")
            return False, "Failed to add reply", None

    def delete_interaction(self, interaction_id: str, user_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Delete an interaction (soft delete)"""
        try:
            success = self.interaction_repo.soft_delete_interaction(interaction_id, user_id)
            if not success:
                return False, "Not authorized or failed to delete", None

            current_app.logger.info(f"Interaction {interaction_id} deleted by {user_id}")

            return True, "Interaction deleted successfully", {}

        except Exception as e:
            current_app.logger.error(f"Error deleting interaction: {str(e)}")
            return False, "Failed to delete interaction", None

    def flag_interaction(self, interaction_id: str, flagger_id: str, reason: str = "") -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Flag an interaction for moderation"""
        try:
            success = self.interaction_repo.flag_interaction(interaction_id, reason)
            if not success:
                return False, "Already flagged or failed to flag", None

            current_app.logger.info(f"Interaction {interaction_id} flagged by {flagger_id}: {reason}")

            return True, "Interaction flagged for review", {}

        except Exception as e:
            current_app.logger.error(f"Error flagging interaction: {str(e)}")
            return False, "Failed to flag interaction", None

    def get_challenge_activity_feed(self, challenge_id: str, user_id: str = None,
                                  limit: int = 50, offset: int = 0) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Get activity feed for a challenge"""
        try:
            # Validate challenge access
            challenge = self.challenge_repo.get_by_challenge_id(challenge_id)
            if not challenge:
                return False, "Challenge not found", None

            # Check if user can view activity (participants and spectators if allowed)
            if user_id and not self._can_view_activity(challenge, user_id):
                return False, "Not authorized to view activity", None

            # Get interactions
            interactions = self.interaction_repo.get_challenge_activity_feed(challenge_id, limit)

            # Convert to API format
            activity_feed = []
            for interaction in interactions:
                activity_item = interaction.to_api_dict()
                activity_item["created_at_relative"] = self._get_relative_time(interaction.created_at)
                activity_feed.append(activity_item)

            return True, "Activity feed retrieved", {
                "challenge_id": challenge_id,
                "activity_feed": activity_feed,
                "count": len(activity_feed)
            }

        except Exception as e:
            current_app.logger.error(f"Error getting activity feed: {str(e)}")
            return False, "Failed to retrieve activity feed", None

    def get_user_interactions(self, challenge_id: str, user_id: str,
                            interaction_type: str = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Get interactions for a specific user in a challenge"""
        try:
            # Get interactions received by user
            received_interactions = self.interaction_repo.get_interactions_for_user(
                user_id, interaction_type, limit=100
            )

            # Filter by challenge
            challenge_interactions = [
                interaction for interaction in received_interactions
                if interaction.challenge_id == challenge_id
            ]

            # Get interaction counts
            interaction_counts = self.interaction_repo.count_user_interactions(challenge_id, user_id)

            return True, "User interactions retrieved", {
                "challenge_id": challenge_id,
                "user_id": user_id,
                "interactions": [interaction.to_api_dict() for interaction in challenge_interactions],
                "counts": interaction_counts,
                "total_interactions": len(challenge_interactions)
            }

        except Exception as e:
            current_app.logger.error(f"Error getting user interactions: {str(e)}")
            return False, "Failed to retrieve user interactions", None

    def get_interaction_statistics(self, challenge_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Get interaction statistics for a challenge"""
        try:
            stats = self.interaction_repo.get_interaction_stats(challenge_id=challenge_id)

            # Get most liked interactions
            popular_interactions = self.interaction_repo.get_most_liked_interactions(
                challenge_id=challenge_id, limit=5
            )

            return True, "Interaction statistics retrieved", {
                "challenge_id": challenge_id,
                "statistics": stats,
                "popular_interactions": [
                    interaction.to_api_dict() for interaction in popular_interactions
                ]
            }

        except Exception as e:
            current_app.logger.error(f"Error getting interaction statistics: {str(e)}")
            return False, "Failed to retrieve statistics", None

    def _validate_interaction(self, challenge_id: str, from_user_id: str,
                            to_user_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Validate that users can interact in this challenge"""
        # Get challenge
        challenge = self.challenge_repo.get_by_challenge_id(challenge_id)
        if not challenge:
            return False, "Challenge not found", None

        # Check if both users are participants (or allow spectators)
        from_participant = challenge.is_participant(from_user_id)
        to_participant = challenge.is_participant(to_user_id)

        if not from_participant and not challenge.allow_spectators:
            return False, "Only participants can interact", None

        if not to_participant:
            return False, "Target user is not a participant", None

        # Check challenge status
        if challenge.status not in ["active", "open"]:
            return False, "Challenge is not active for interactions", None

        return True, "Validation passed", {"challenge": challenge}

    def _update_social_metrics(self, challenge_id: str, user_id: str, interaction_type: str) -> None:
        """Update participant social metrics"""
        try:
            self.participant_repo.add_social_interaction(challenge_id, user_id, interaction_type, 1)
        except Exception as e:
            current_app.logger.warning(f"Failed to update social metrics: {str(e)}")

    def _can_view_activity(self, challenge: SocialChallenge, user_id: str) -> bool:
        """Check if user can view challenge activity"""
        # Participants can always view
        if challenge.is_participant(user_id):
            return True

        # Spectators can view if allowed
        if challenge.allow_spectators:
            return True

        # Creator can always view
        if user_id == challenge.creator_id:
            return True

        return False

    def _get_relative_time(self, timestamp: datetime) -> str:
        """Get human-readable relative time"""
        now = datetime.utcnow()
        diff = now - timestamp

        if diff.total_seconds() < 60:
            return "just now"
        elif diff.total_seconds() < 3600:
            minutes = int(diff.total_seconds() / 60)
            return f"{minutes}m ago"
        elif diff.total_seconds() < 86400:
            hours = int(diff.total_seconds() / 3600)
            return f"{hours}h ago"
        else:
            days = diff.days
            return f"{days}d ago"