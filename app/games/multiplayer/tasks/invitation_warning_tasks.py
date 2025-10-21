from datetime import datetime, timezone, timedelta
from flask import current_app
from app.games.multiplayer.repositories.invitation_repository import InvitationRepository
from app.games.multiplayer.models.room_invitation import RoomInvitation
from app.core.services.notification_service import NotificationService


def send_expiry_warnings():
    """
    Send warning notifications for invitations expiring soon.

    This task runs every 2 minutes and sends notifications to users
    who have invitations expiring in the next 5 minutes.

    Only sends one warning per invitation (tracked by warning_sent field).
    """
    try:
        current_app.logger.info("Starting expiry warning task")

        invitation_repository = InvitationRepository()
        notification_service = NotificationService()

        # Calculate time window: invitations expiring in next 5 minutes
        now = datetime.now(timezone.utc)
        warning_threshold = now + timedelta(minutes=5)

        # Find pending invitations expiring soon that haven't been warned yet
        db = invitation_repository.collection

        invitations = db.find({
            'status': RoomInvitation.STATUS_PENDING,
            'expires_at': {
                '$gt': now,  # Not expired yet
                '$lte': warning_threshold  # Expires within 5 minutes
            },
            'warning_sent': {'$ne': True}  # Warning not sent yet
        })

        warnings_sent = 0

        for inv_doc in invitations:
            try:
                invitation = RoomInvitation.from_dict(inv_doc)

                # Calculate minutes remaining
                time_remaining = invitation.expires_at - now
                minutes_remaining = int(time_remaining.total_seconds() / 60)

                # Send warning notification
                notification_service.send_invitation_expiring_soon(
                    recipient_user_id=invitation.recipient_user_id,
                    game_name=invitation.game_name or invitation.game_id,
                    room_code=invitation.room_code or invitation.room_id,
                    minutes_remaining=minutes_remaining,
                    invitation_data={
                        'invitation_id': invitation.invitation_id,
                        'room_id': invitation.room_id,
                        'room_code': invitation.room_code,
                        'game_id': invitation.game_id,
                        'sender_user_id': invitation.sender_user_id
                    }
                )

                # Mark warning as sent
                db.update_one(
                    {'invitation_id': invitation.invitation_id},
                    {
                        '$set': {
                            'warning_sent': True,
                            'warning_sent_at': now
                        }
                    }
                )

                warnings_sent += 1

                current_app.logger.info(
                    f"Expiry warning sent for invitation {invitation.invitation_id} "
                    f"(expires in {minutes_remaining} minutes)"
                )

            except Exception as e:
                current_app.logger.error(
                    f"Error sending warning for invitation {inv_doc.get('invitation_id')}: {str(e)}",
                    exc_info=True
                )
                continue

        if warnings_sent > 0:
            current_app.logger.info(f"Expiry warning task complete: {warnings_sent} warnings sent")
        else:
            current_app.logger.debug("Expiry warning task complete: no warnings to send")

        return warnings_sent

    except Exception as e:
        current_app.logger.error(f"Error in expiry warning task: {str(e)}", exc_info=True)
        return 0


def cleanup_expired_invitations():
    """
    Mark expired invitations as expired and send expiry notifications.

    This task runs every 5 minutes. This is the existing cleanup task
    from GOO-60, now enhanced with notification sending.
    """
    try:
        current_app.logger.info("Starting cleanup expired invitations task")

        invitation_repository = InvitationRepository()
        notification_service = NotificationService()

        # Get expired invitations that are still marked as pending
        now = datetime.now(timezone.utc)
        db = invitation_repository.collection

        expired_invitations = db.find({
            'status': RoomInvitation.STATUS_PENDING,
            'expires_at': {'$lt': now}
        })

        expired_count = 0

        for inv_doc in expired_invitations:
            try:
                invitation = RoomInvitation.from_dict(inv_doc)

                # Mark as expired
                invitation.mark_expired()
                db.update_one(
                    {'invitation_id': invitation.invitation_id},
                    {'$set': {'status': RoomInvitation.STATUS_EXPIRED}}
                )

                # Send expiry notification to recipient
                notification_service.send_invitation_expired(
                    recipient_user_id=invitation.recipient_user_id,
                    room_code=invitation.room_code or invitation.room_id,
                    invitation_data={
                        'invitation_id': invitation.invitation_id,
                        'room_id': invitation.room_id,
                        'room_code': invitation.room_code,
                        'game_id': invitation.game_id
                    }
                )

                expired_count += 1

            except Exception as e:
                current_app.logger.error(
                    f"Error processing expired invitation {inv_doc.get('invitation_id')}: {str(e)}",
                    exc_info=True
                )
                continue

        if expired_count > 0:
            current_app.logger.info(
                f"Cleanup task complete: {expired_count} invitations marked as expired"
            )

        return expired_count

    except Exception as e:
        current_app.logger.error(f"Error in cleanup expired invitations task: {str(e)}", exc_info=True)
        return 0


def cleanup_old_invitations():
    """
    Delete old processed invitations (older than 30 days).

    This task runs daily at 3 AM UTC. This is the existing cleanup task from GOO-60.
    """
    try:
        current_app.logger.info("Starting cleanup old invitations task")

        invitation_repository = InvitationRepository()

        # Delete invitations older than 30 days that have been processed
        days = 30
        threshold_date = datetime.now(timezone.utc) - timedelta(days=days)

        db = invitation_repository.collection

        result = db.delete_many({
            'created_at': {'$lt': threshold_date},
            'status': {'$in': [
                RoomInvitation.STATUS_ACCEPTED,
                RoomInvitation.STATUS_DECLINED,
                RoomInvitation.STATUS_EXPIRED
            ]}
        })

        deleted_count = result.deleted_count

        if deleted_count > 0:
            current_app.logger.info(
                f"Cleanup old invitations complete: {deleted_count} invitations deleted (>{days} days old)"
            )

        return deleted_count

    except Exception as e:
        current_app.logger.error(f"Error in cleanup old invitations task: {str(e)}", exc_info=True)
        return 0


def cleanup_old_notifications():
    """
    Delete old soft-deleted notifications (older than 90 days).

    This task runs daily at 3 AM UTC.
    """
    try:
        current_app.logger.info("Starting cleanup old notifications task")

        from app.core.repositories.notification_repository import NotificationRepository

        notification_repository = NotificationRepository()

        # Use repository method to cleanup old notifications
        deleted_count = notification_repository.cleanup_old_notifications(days=90)

        if deleted_count > 0:
            current_app.logger.info(
                f"Cleanup old notifications complete: {deleted_count} notifications deleted (>90 days old)"
            )

        return deleted_count

    except Exception as e:
        current_app.logger.error(f"Error in cleanup old notifications task: {str(e)}", exc_info=True)
        return 0


def cleanup_expired_device_tokens():
    """
    Delete device tokens that haven't been used in 90 days.

    This task runs daily at 3 AM UTC.
    """
    try:
        current_app.logger.info("Starting cleanup expired device tokens task")

        from app.core.repositories.device_token_repository import DeviceTokenRepository

        device_token_repository = DeviceTokenRepository()

        # Use repository method to cleanup expired tokens
        deleted_count = device_token_repository.delete_expired_tokens()

        if deleted_count > 0:
            current_app.logger.info(
                f"Cleanup expired device tokens complete: {deleted_count} tokens deleted (>90 days inactive)"
            )

        return deleted_count

    except Exception as e:
        current_app.logger.error(f"Error in cleanup expired device tokens task: {str(e)}", exc_info=True)
        return 0
