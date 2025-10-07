"""
Background tasks for multiplayer system.

GOO-60: Cleanup expired invitations and emit WebSocket notifications.
"""

from flask import current_app
from app.games.multiplayer.services.invitation_service import InvitationService
from app.games.multiplayer.repositories.invitation_repository import InvitationRepository
from app.games.multiplayer.models.room_invitation import RoomInvitation


def cleanup_expired_invitations():
    """
    Cleanup expired invitations and notify users.

    GOO-60: Should be run periodically (e.g., every 5 minutes).

    Returns:
        Number of invitations marked as expired
    """
    try:
        invitation_service = InvitationService()

        # Get invitations that have just expired (still in PENDING status)
        invitation_repo = InvitationRepository()
        from datetime import datetime, timezone

        # Find recently expired pending invitations
        recently_expired = invitation_repo.collection.find({
            'status': RoomInvitation.STATUS_PENDING,
            'expires_at': {'$lt': datetime.now(timezone.utc)}
        })

        expired_invitations = [RoomInvitation.from_dict(inv) for inv in recently_expired]

        # Mark them as expired and notify users
        count = invitation_service.cleanup_expired()

        # Emit WebSocket events for each expired invitation
        if count > 0:
            try:
                from app.games.multiplayer.events.connection_events import MultiplayerNamespace
                multiplayer_ns = MultiplayerNamespace()

                for invitation in expired_invitations:
                    try:
                        multiplayer_ns.emit_invitation_expired(
                            invitation.recipient_user_id,
                            invitation.invitation_id
                        )
                    except Exception as emit_error:
                        current_app.logger.warning(
                            f"Failed to emit expired event for invitation {invitation.invitation_id}: "
                            f"{str(emit_error)}"
                        )

            except Exception as ws_error:
                current_app.logger.warning(f"WebSocket notification failed: {str(ws_error)}")

        if count > 0:
            current_app.logger.info(f"Cleaned up {count} expired invitations")

        return count

    except Exception as e:
        current_app.logger.error(f"Error in cleanup_expired_invitations: {str(e)}", exc_info=True)
        return 0


def cleanup_old_invitations(days: int = 30):
    """
    Delete old processed invitations (accepted/declined/expired).

    Args:
        days: Delete invitations older than this many days

    Returns:
        Number of invitations deleted
    """
    try:
        invitation_repo = InvitationRepository()
        count = invitation_repo.delete_old_invitations(days)

        if count > 0:
            current_app.logger.info(f"Deleted {count} old invitations (older than {days} days)")

        return count

    except Exception as e:
        current_app.logger.error(f"Error in cleanup_old_invitations: {str(e)}", exc_info=True)
        return 0


def get_invitation_statistics():
    """
    Get invitation statistics for monitoring.

    Returns:
        Dict with invitation counts by status
    """
    try:
        invitation_repo = InvitationRepository()
        stats = invitation_repo.get_invitation_statistics()

        current_app.logger.debug(f"Invitation statistics: {stats}")

        return stats

    except Exception as e:
        current_app.logger.error(f"Error getting invitation statistics: {str(e)}", exc_info=True)
        return {}
