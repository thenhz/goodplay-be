from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from flask import current_app

from app.social.challenges.models.social_challenge import SocialChallenge
from app.social.challenges.models.challenge_participant import ChallengeParticipant
from app.social.challenges.models.challenge_interaction import ChallengeInteraction


class NotificationService:
    """Service for managing challenge-related notifications and real-time updates"""

    def __init__(self):
        # In a real implementation, this would integrate with:
        # - WebSocket service for real-time updates
        # - Push notification service (Firebase, AWS SNS, etc.)
        # - Email notification service
        # For now, we'll log notifications and store them for later retrieval
        pass

    def notify_challenge_created(self, challenge: SocialChallenge) -> bool:
        """Notify about new challenge creation"""
        try:
            notification_data = {
                "type": "challenge_created",
                "challenge_id": challenge.challenge_id,
                "creator_id": challenge.creator_id,
                "title": challenge.title,
                "challenge_type": challenge.challenge_type,
                "is_public": challenge.is_public,
                "created_at": datetime.utcnow()
            }

            # Log notification
            current_app.logger.info(f"Challenge created notification: {challenge.challenge_id}")

            # In real implementation:
            # - Send WebSocket message to relevant users
            # - Send push notifications to friends if friends_only
            # - Send email notifications if configured

            return True

        except Exception as e:
            current_app.logger.error(f"Error sending challenge created notification: {str(e)}")
            return False

    def notify_challenge_invitation(self, challenge: SocialChallenge, inviter_id: str,
                                  invited_user_ids: List[str]) -> bool:
        """Notify users about challenge invitations"""
        try:
            for user_id in invited_user_ids:
                notification_data = {
                    "type": "challenge_invitation",
                    "challenge_id": challenge.challenge_id,
                    "inviter_id": inviter_id,
                    "invited_user_id": user_id,
                    "title": challenge.title,
                    "challenge_type": challenge.challenge_type,
                    "end_date": challenge.end_date,
                    "created_at": datetime.utcnow()
                }

                # Log notification
                current_app.logger.info(f"Challenge invitation sent to {user_id} for {challenge.challenge_id}")

                # In real implementation:
                # - Send WebSocket message to user
                # - Send push notification
                # - Send email notification
                # - Store in user's notification inbox

            return True

        except Exception as e:
            current_app.logger.error(f"Error sending challenge invitation notifications: {str(e)}")
            return False

    def notify_user_joined(self, challenge: SocialChallenge, user_id: str) -> bool:
        """Notify about user joining challenge"""
        try:
            notification_data = {
                "type": "user_joined_challenge",
                "challenge_id": challenge.challenge_id,
                "user_id": user_id,
                "title": challenge.title,
                "current_participants": challenge.current_participants,
                "max_participants": challenge.max_participants,
                "created_at": datetime.utcnow()
            }

            # Notify creator and other participants
            notify_users = [challenge.creator_id] + challenge.participant_ids
            notify_users = list(set(notify_users))  # Remove duplicates
            if user_id in notify_users:
                notify_users.remove(user_id)  # Don't notify the user who joined

            for notify_user in notify_users:
                current_app.logger.info(f"User joined notification sent to {notify_user} for {challenge.challenge_id}")

            return True

        except Exception as e:
            current_app.logger.error(f"Error sending user joined notification: {str(e)}")
            return False

    def notify_challenge_started(self, challenge: SocialChallenge) -> bool:
        """Notify participants about challenge starting"""
        try:
            notification_data = {
                "type": "challenge_started",
                "challenge_id": challenge.challenge_id,
                "title": challenge.title,
                "start_date": challenge.start_date,
                "end_date": challenge.end_date,
                "participant_count": challenge.current_participants,
                "created_at": datetime.utcnow()
            }

            # Notify all participants
            for user_id in challenge.participant_ids:
                current_app.logger.info(f"Challenge started notification sent to {user_id} for {challenge.challenge_id}")

            return True

        except Exception as e:
            current_app.logger.error(f"Error sending challenge started notification: {str(e)}")
            return False

    def notify_milestone_reached(self, challenge: SocialChallenge, participant: ChallengeParticipant,
                               milestone_data: Dict[str, Any]) -> bool:
        """Notify about milestone achievements"""
        try:
            notification_data = {
                "type": "milestone_reached",
                "challenge_id": challenge.challenge_id,
                "user_id": participant.user_id,
                "title": challenge.title,
                "milestone": milestone_data,
                "current_progress": participant.current_progress,
                "completion_percentage": participant.completion_percentage,
                "created_at": datetime.utcnow()
            }

            # Notify the achiever
            current_app.logger.info(f"Milestone reached notification sent to {participant.user_id}")

            # Notify other participants if it's a significant milestone
            if milestone_data.get("significance", "normal") == "major":
                other_participants = [pid for pid in challenge.participant_ids if pid != participant.user_id]
                for user_id in other_participants:
                    current_app.logger.info(f"Major milestone notification sent to {user_id}")

            return True

        except Exception as e:
            current_app.logger.error(f"Error sending milestone notification: {str(e)}")
            return False

    def notify_progress_update(self, challenge: SocialChallenge, participant: ChallengeParticipant,
                             progress_data: Dict[str, Any]) -> bool:
        """Notify about significant progress updates"""
        try:
            # Only notify for significant progress updates (>10% change)
            previous_percentage = progress_data.get("previous_percentage", 0)
            current_percentage = participant.completion_percentage
            percentage_change = current_percentage - previous_percentage

            if percentage_change < 10:  # Skip minor updates
                return True

            notification_data = {
                "type": "progress_update",
                "challenge_id": challenge.challenge_id,
                "user_id": participant.user_id,
                "title": challenge.title,
                "completion_percentage": current_percentage,
                "percentage_change": percentage_change,
                "created_at": datetime.utcnow()
            }

            # Log significant progress
            current_app.logger.info(f"Progress update: {participant.user_id} reached {current_percentage}% in {challenge.challenge_id}")

            return True

        except Exception as e:
            current_app.logger.error(f"Error sending progress notification: {str(e)}")
            return False

    def notify_social_interaction(self, challenge: SocialChallenge, interaction: ChallengeInteraction) -> bool:
        """Notify about social interactions (cheers, comments)"""
        try:
            notification_data = {
                "type": f"social_{interaction.interaction_type}",
                "challenge_id": challenge.challenge_id,
                "from_user_id": interaction.from_user_id,
                "to_user_id": interaction.to_user_id,
                "interaction_type": interaction.interaction_type,
                "content": interaction.content,
                "emoji": interaction.emoji,
                "context_type": interaction.context_type,
                "created_at": datetime.utcnow()
            }

            # Notify the target user (don't notify if user is interacting with themselves)
            if interaction.from_user_id != interaction.to_user_id:
                current_app.logger.info(f"Social interaction notification: {interaction.interaction_type} from {interaction.from_user_id} to {interaction.to_user_id}")

            return True

        except Exception as e:
            current_app.logger.error(f"Error sending social interaction notification: {str(e)}")
            return False

    def notify_challenge_ending_soon(self, challenge: SocialChallenge, hours_remaining: int) -> bool:
        """Notify participants about challenge ending soon"""
        try:
            notification_data = {
                "type": "challenge_ending_soon",
                "challenge_id": challenge.challenge_id,
                "title": challenge.title,
                "hours_remaining": hours_remaining,
                "end_date": challenge.end_date,
                "created_at": datetime.utcnow()
            }

            # Notify all active participants
            for user_id in challenge.participant_ids:
                current_app.logger.info(f"Challenge ending soon notification sent to {user_id} for {challenge.challenge_id}")

            return True

        except Exception as e:
            current_app.logger.error(f"Error sending challenge ending soon notification: {str(e)}")
            return False

    def notify_challenge_completed(self, challenge: SocialChallenge, results: List[Dict[str, Any]]) -> bool:
        """Notify participants about challenge completion"""
        try:
            notification_data = {
                "type": "challenge_completed",
                "challenge_id": challenge.challenge_id,
                "title": challenge.title,
                "winner_ids": challenge.winner_ids,
                "participant_count": len(results),
                "completed_at": datetime.utcnow(),
                "created_at": datetime.utcnow()
            }

            # Notify all participants with their individual results
            for result in results:
                user_id = result.get("user_id")
                user_notification = {
                    **notification_data,
                    "user_result": {
                        "rank": result.get("rank"),
                        "score": result.get("score"),
                        "is_winner": user_id in challenge.winner_ids
                    }
                }

                current_app.logger.info(f"Challenge completed notification sent to {user_id} (rank: {result.get('rank')})")

            return True

        except Exception as e:
            current_app.logger.error(f"Error sending challenge completed notification: {str(e)}")
            return False

    def notify_badge_earned(self, challenge: SocialChallenge, user_id: str,
                          badge_data: Dict[str, Any]) -> bool:
        """Notify about badge achievements"""
        try:
            notification_data = {
                "type": "badge_earned",
                "challenge_id": challenge.challenge_id,
                "user_id": user_id,
                "title": challenge.title,
                "badge": badge_data,
                "created_at": datetime.utcnow()
            }

            current_app.logger.info(f"Badge earned notification sent to {user_id}: {badge_data.get('name', 'Unknown Badge')}")

            return True

        except Exception as e:
            current_app.logger.error(f"Error sending badge earned notification: {str(e)}")
            return False

    def notify_leaderboard_change(self, challenge: SocialChallenge, user_id: str,
                                old_rank: int, new_rank: int) -> bool:
        """Notify about significant leaderboard position changes"""
        try:
            # Only notify for improvements or significant changes
            rank_improvement = old_rank - new_rank
            if rank_improvement <= 0:  # No improvement
                return True

            # Only notify for top 10 positions or significant improvements
            if new_rank > 10 and rank_improvement < 5:
                return True

            notification_data = {
                "type": "leaderboard_change",
                "challenge_id": challenge.challenge_id,
                "user_id": user_id,
                "title": challenge.title,
                "old_rank": old_rank,
                "new_rank": new_rank,
                "rank_improvement": rank_improvement,
                "created_at": datetime.utcnow()
            }

            current_app.logger.info(f"Leaderboard change notification sent to {user_id}: rank {old_rank} -> {new_rank}")

            return True

        except Exception as e:
            current_app.logger.error(f"Error sending leaderboard change notification: {str(e)}")
            return False

    def send_daily_digest(self, user_id: str, digest_data: Dict[str, Any]) -> bool:
        """Send daily digest of challenge activities"""
        try:
            notification_data = {
                "type": "daily_digest",
                "user_id": user_id,
                "active_challenges": digest_data.get("active_challenges", []),
                "new_invitations": digest_data.get("new_invitations", []),
                "milestones_reached": digest_data.get("milestones_reached", []),
                "social_interactions": digest_data.get("social_interactions", {}),
                "recommended_challenges": digest_data.get("recommended_challenges", []),
                "created_at": datetime.utcnow()
            }

            current_app.logger.info(f"Daily digest sent to {user_id}")

            # In real implementation:
            # - Send email digest
            # - Update user's notification preferences
            # - Track digest engagement

            return True

        except Exception as e:
            current_app.logger.error(f"Error sending daily digest: {str(e)}")
            return False

    def send_weekly_summary(self, user_id: str, summary_data: Dict[str, Any]) -> bool:
        """Send weekly summary of achievements and statistics"""
        try:
            notification_data = {
                "type": "weekly_summary",
                "user_id": user_id,
                "challenges_completed": summary_data.get("challenges_completed", 0),
                "badges_earned": summary_data.get("badges_earned", []),
                "social_engagement": summary_data.get("social_engagement", {}),
                "personal_records": summary_data.get("personal_records", []),
                "week_highlights": summary_data.get("week_highlights", []),
                "created_at": datetime.utcnow()
            }

            current_app.logger.info(f"Weekly summary sent to {user_id}")

            return True

        except Exception as e:
            current_app.logger.error(f"Error sending weekly summary: {str(e)}")
            return False

    def broadcast_system_announcement(self, announcement_data: Dict[str, Any],
                                    target_users: List[str] = None) -> bool:
        """Broadcast system announcements about challenges"""
        try:
            notification_data = {
                "type": "system_announcement",
                "announcement": announcement_data,
                "created_at": datetime.utcnow()
            }

            if target_users:
                # Send to specific users
                for user_id in target_users:
                    current_app.logger.info(f"System announcement sent to {user_id}")
            else:
                # Broadcast to all users
                current_app.logger.info("System announcement broadcast to all users")

            return True

        except Exception as e:
            current_app.logger.error(f"Error broadcasting system announcement: {str(e)}")
            return False

    # Real-time WebSocket methods (would integrate with WebSocket service)
    def send_real_time_update(self, user_ids: List[str], update_data: Dict[str, Any]) -> bool:
        """Send real-time update via WebSocket"""
        try:
            # In real implementation, this would:
            # - Connect to WebSocket service
            # - Send update to connected users
            # - Handle offline users by queuing notifications

            for user_id in user_ids:
                current_app.logger.info(f"Real-time update sent to {user_id}: {update_data.get('type', 'unknown')}")

            return True

        except Exception as e:
            current_app.logger.error(f"Error sending real-time update: {str(e)}")
            return False

    def send_push_notification(self, user_id: str, title: str, body: str,
                             data: Dict[str, Any] = None) -> bool:
        """Send push notification to user's devices"""
        try:
            # In real implementation, this would:
            # - Get user's device tokens
            # - Send via FCM/APNS
            # - Handle delivery failures

            current_app.logger.info(f"Push notification sent to {user_id}: {title}")

            return True

        except Exception as e:
            current_app.logger.error(f"Error sending push notification: {str(e)}")
            return False

    # Notification preferences and management
    def get_user_notification_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get user's notification preferences"""
        # In real implementation, this would fetch from user preferences
        # For now, return default preferences
        return {
            "challenge_invitations": True,
            "challenge_started": True,
            "milestone_achievements": True,
            "social_interactions": True,
            "challenge_endings": True,
            "daily_digest": True,
            "weekly_summary": True,
            "push_notifications": True,
            "email_notifications": True
        }

    def update_notification_preferences(self, user_id: str,
                                      preferences: Dict[str, Any]) -> bool:
        """Update user's notification preferences"""
        try:
            # In real implementation, this would update user preferences in database
            current_app.logger.info(f"Notification preferences updated for {user_id}")
            return True

        except Exception as e:
            current_app.logger.error(f"Error updating notification preferences: {str(e)}")
            return False