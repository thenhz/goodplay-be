import uuid
from typing import Tuple, Optional, List, Dict, Any
from flask import current_app
from datetime import datetime, timezone
from app.games.multiplayer.models.room_invitation import RoomInvitation
from app.games.multiplayer.repositories.invitation_repository import InvitationRepository
from app.games.multiplayer.repositories.room_repository import RoomRepository
from app.social.repositories.relationship_repository import RelationshipRepository
from app.social.models.user_relationship import UserRelationship
from app.core.utils.helpers import extract_user_id
from app.core.services.notification_service import NotificationService


class InvitationService:
    """Service for managing room invitations"""

    def __init__(self):
        self.invitation_repository = InvitationRepository()
        self.room_repository = RoomRepository()
        self.relationship_repository = RelationshipRepository()
        self.notification_service = NotificationService()

    def send_invitation(
        self,
        room_id: str,
        sender_user_id: str,
        recipient_user_id: str
    ) -> Tuple[bool, str, Optional[RoomInvitation]]:
        """
        Send room invitation.

        Args:
            room_id: Room ID
            sender_user_id: Sender user ID
            recipient_user_id: Recipient user ID

        Returns:
            Tuple of (success, message, invitation)
        """
        try:
            # Extract user IDs
            sender_id = extract_user_id(sender_user_id)
            recipient_id = extract_user_id(recipient_user_id)

            # Validate room exists
            room = self.room_repository.find_by_room_id(room_id)
            if not room:
                return False, "ROOM_NOT_FOUND", None

            # Check room status
            if room.status != room.STATUS_WAITING:
                return False, "ROOM_NOT_ACCEPTING_PLAYERS", None

            # Check if room is full
            if room.is_full():
                return False, "ROOM_FULL", None

            # Check if sender is in the room (only players can invite)
            if not room.has_player(sender_id):
                return False, "NOT_IN_ROOM", None

            # Check if recipient is already in room
            if room.has_player(recipient_id):
                return False, "ALREADY_IN_ROOM", None

            # GOO-60: Check if sender has blocked recipient or vice versa
            if self.relationship_repository.is_blocked(sender_id, recipient_id):
                return False, "USER_BLOCKED", None
            if self.relationship_repository.is_blocked(recipient_id, sender_id):
                return False, "USER_BLOCKED", None

            # Check for existing pending invitation
            existing = self.invitation_repository.check_existing_invitation(
                room_id, recipient_id
            )
            if existing:
                return False, "INVITATION_ALREADY_SENT", existing

            # Create invitation
            invitation = RoomInvitation(
                invitation_id=str(uuid.uuid4()),
                room_id=room_id,
                room_code=room.room_code,
                game_id=room.game_id,
                game_name=room.game_id,  # Will be enhanced with actual game name later
                sender_user_id=sender_id,
                recipient_user_id=recipient_id,
                metadata={
                    'room_name': room.room_name or room.room_code
                }
            )

            if self.invitation_repository.create_invitation(invitation):
                current_app.logger.info(
                    f"Invitation sent from {sender_id} to {recipient_id} for room {room_id}"
                )

                # Send notification to recipient
                self.notification_service.send_invitation_received(
                    recipient_user_id=recipient_id,
                    sender_name=sender_id,  # TODO: Get sender's display name
                    game_name=invitation.game_name or invitation.game_id,
                    room_code=invitation.room_code or room.room_code,
                    invitation_data={
                        'invitation_id': invitation.invitation_id,
                        'room_id': room_id,
                        'room_code': invitation.room_code,
                        'game_id': invitation.game_id,
                        'sender_user_id': sender_id
                    }
                )

                return True, "INVITATION_SENT_SUCCESS", invitation
            else:
                return False, "INVITATION_CREATION_FAILED", None

        except Exception as e:
            current_app.logger.error(f"Error sending invitation: {str(e)}", exc_info=True)
            return False, "SEND_INVITATION_ERROR", None

    def send_batch_invitations(
        self,
        room_id: str,
        sender_user_id: str,
        recipient_user_ids: List[str]
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Send invitations to multiple users at once.

        GOO-60: Batch invitation feature with validation and filtering.

        Args:
            room_id: Room ID
            sender_user_id: Sender user ID
            recipient_user_ids: List of recipient user IDs

        Returns:
            Tuple of (success, message, result_dict with sent/failed counts and details)
        """
        try:
            sender_id = extract_user_id(sender_user_id)

            # Validate room exists
            room = self.room_repository.find_by_room_id(room_id)
            if not room:
                return False, "ROOM_NOT_FOUND", {}

            # Check room status
            if room.status != room.STATUS_WAITING:
                return False, "ROOM_NOT_ACCEPTING_PLAYERS", {}

            # Check if sender is in the room
            if not room.has_player(sender_id):
                return False, "NOT_IN_ROOM", {}

            # Validate recipient list
            if not recipient_user_ids or len(recipient_user_ids) == 0:
                return False, "RECIPIENT_LIST_EMPTY", {}

            # Limit batch size
            if len(recipient_user_ids) > 10:
                return False, "TOO_MANY_RECIPIENTS", {}

            sent_invitations = []
            failed_invitations = []

            for recipient_id in recipient_user_ids:
                recipient_id = extract_user_id(recipient_id)

                # Skip if same as sender
                if recipient_id == sender_id:
                    failed_invitations.append({
                        'recipient_id': recipient_id,
                        'reason': 'CANNOT_INVITE_SELF'
                    })
                    continue

                # Skip if already in room
                if room.has_player(recipient_id):
                    failed_invitations.append({
                        'recipient_id': recipient_id,
                        'reason': 'ALREADY_IN_ROOM'
                    })
                    continue

                # Skip if room is now full
                if room.is_full():
                    failed_invitations.append({
                        'recipient_id': recipient_id,
                        'reason': 'ROOM_FULL'
                    })
                    continue

                # Skip if blocked
                if (self.relationship_repository.is_blocked(sender_id, recipient_id) or
                        self.relationship_repository.is_blocked(recipient_id, sender_id)):
                    failed_invitations.append({
                        'recipient_id': recipient_id,
                        'reason': 'USER_BLOCKED'
                    })
                    continue

                # Skip if already has pending invitation
                existing = self.invitation_repository.check_existing_invitation(
                    room_id, recipient_id
                )
                if existing:
                    failed_invitations.append({
                        'recipient_id': recipient_id,
                        'reason': 'INVITATION_ALREADY_SENT'
                    })
                    continue

                # Create and send invitation
                invitation = RoomInvitation(
                    invitation_id=str(uuid.uuid4()),
                    room_id=room_id,
                    room_code=room.room_code,
                    game_id=room.game_id,
                    game_name=room.game_id,
                    sender_user_id=sender_id,
                    recipient_user_id=recipient_id,
                    metadata={
                        'room_name': room.room_name or room.room_code
                    }
                )

                if self.invitation_repository.create_invitation(invitation):
                    sent_invitations.append({
                        'recipient_id': recipient_id,
                        'invitation_id': invitation.invitation_id
                    })

                    # Send notification to recipient
                    self.notification_service.send_invitation_received(
                        recipient_user_id=recipient_id,
                        sender_name=sender_id,  # TODO: Get sender's display name
                        game_name=invitation.game_name or invitation.game_id,
                        room_code=invitation.room_code or room.room_code,
                        invitation_data={
                            'invitation_id': invitation.invitation_id,
                            'room_id': room_id,
                            'room_code': invitation.room_code,
                            'game_id': invitation.game_id,
                            'sender_user_id': sender_id
                        }
                    )
                else:
                    failed_invitations.append({
                        'recipient_id': recipient_id,
                        'reason': 'INVITATION_CREATION_FAILED'
                    })

            current_app.logger.info(
                f"Batch invitation: {len(sent_invitations)} sent, {len(failed_invitations)} failed"
            )

            # Determine overall result
            if len(sent_invitations) == 0:
                return False, "NO_INVITATIONS_SENT", {
                    'sent': sent_invitations,
                    'failed': failed_invitations,
                    'total_requested': len(recipient_user_ids),
                    'sent_count': 0,
                    'failed_count': len(failed_invitations)
                }

            return True, "BATCH_INVITATIONS_SENT", {
                'sent': sent_invitations,
                'failed': failed_invitations,
                'total_requested': len(recipient_user_ids),
                'sent_count': len(sent_invitations),
                'failed_count': len(failed_invitations)
            }

        except Exception as e:
            current_app.logger.error(f"Error sending batch invitations: {str(e)}", exc_info=True)
            return False, "BATCH_INVITATION_ERROR", {}

    def accept_invitation(
        self,
        invitation_id: str,
        user_id: str
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Accept invitation and return room_id for joining.

        Args:
            invitation_id: Invitation ID
            user_id: User ID (must be recipient)

        Returns:
            Tuple of (success, message, room_id)
        """
        try:
            user_id = extract_user_id(user_id)

            # Get invitation
            invitation = self.invitation_repository.get_invitation(invitation_id)
            if not invitation:
                return False, "INVITATION_NOT_FOUND", None

            # Verify recipient
            if invitation.recipient_user_id != user_id:
                return False, "NOT_INVITATION_RECIPIENT", None

            # Check if can be accepted
            if not invitation.can_accept():
                if invitation.is_expired():
                    return False, "INVITATION_EXPIRED", None
                else:
                    return False, "INVITATION_ALREADY_PROCESSED", None

            # Verify room still exists and is joinable
            room = self.room_repository.find_by_room_id(invitation.room_id)
            if not room:
                return False, "ROOM_NO_LONGER_EXISTS", None

            if room.status != room.STATUS_WAITING:
                return False, "ROOM_NOT_ACCEPTING_PLAYERS", None

            if room.is_full():
                return False, "ROOM_FULL", None

            # Check if user already in room
            if room.has_player(user_id):
                return False, "ALREADY_IN_ROOM", None

            # Accept invitation
            invitation.accept()
            self.invitation_repository.update_invitation_status(
                invitation_id,
                RoomInvitation.STATUS_ACCEPTED,
                'accepted_at'
            )

            current_app.logger.info(
                f"✅ [ACCEPT_FLOW] Step 1/2: Invitation {invitation_id} accepted by {user_id} "
                f"for room {invitation.room_id}"
            )

            # Send notification to sender
            self.notification_service.send_invitation_accepted(
                sender_user_id=invitation.sender_user_id,
                acceptor_name=user_id,  # TODO: Get acceptor's display name
                room_code=invitation.room_code or invitation.room_id,
                invitation_data={
                    'invitation_id': invitation_id,
                    'room_id': invitation.room_id,
                    'room_code': invitation.room_code,
                    'accepted_by': user_id
                }
            )

            current_app.logger.info(
                f"✅ [ACCEPT_FLOW] Step 2/2: Notification sent to sender {invitation.sender_user_id}. "
                f"Returning room_id={invitation.room_id} to client. "
                f"⏳ WAITING for client to call join_room via WebSocket..."
            )

            return True, "INVITATION_ACCEPTED_SUCCESS", invitation.room_id

        except Exception as e:
            current_app.logger.error(f"Error accepting invitation: {str(e)}", exc_info=True)
            return False, "ACCEPT_INVITATION_ERROR", None

    def decline_invitation(
        self,
        invitation_id: str,
        user_id: str
    ) -> Tuple[bool, str]:
        """
        Decline invitation.

        Args:
            invitation_id: Invitation ID
            user_id: User ID (must be recipient)

        Returns:
            Tuple of (success, message)
        """
        try:
            user_id = extract_user_id(user_id)

            # Get invitation
            invitation = self.invitation_repository.get_invitation(invitation_id)
            if not invitation:
                return False, "INVITATION_NOT_FOUND"

            # Verify recipient
            if invitation.recipient_user_id != user_id:
                return False, "NOT_INVITATION_RECIPIENT"

            # Check if can be declined
            if invitation.status != RoomInvitation.STATUS_PENDING:
                return False, "INVITATION_ALREADY_PROCESSED"

            # Decline invitation
            invitation.decline()
            self.invitation_repository.update_invitation_status(
                invitation_id,
                RoomInvitation.STATUS_DECLINED,
                'declined_at'
            )

            current_app.logger.info(
                f"Invitation {invitation_id} declined by {user_id}"
            )

            # Send notification to sender
            self.notification_service.send_invitation_declined(
                sender_user_id=invitation.sender_user_id,
                decliner_name=user_id,  # TODO: Get decliner's display name
                room_code=invitation.room_code or invitation.room_id,
                invitation_data={
                    'invitation_id': invitation_id,
                    'room_id': invitation.room_id,
                    'room_code': invitation.room_code,
                    'declined_by': user_id
                }
            )

            return True, "INVITATION_DECLINED_SUCCESS"

        except Exception as e:
            current_app.logger.error(f"Error declining invitation: {str(e)}", exc_info=True)
            return False, "DECLINE_INVITATION_ERROR"

    def get_user_invitations(
        self,
        user_id: str,
        include_expired: bool = False
    ) -> Tuple[bool, str, List[RoomInvitation]]:
        """
        Get user's pending invitations.

        Args:
            user_id: User ID
            include_expired: Include expired invitations

        Returns:
            Tuple of (success, message, invitations)
        """
        try:
            user_id = extract_user_id(user_id)

            invitations = self.invitation_repository.get_user_invitations(
                user_id,
                status=None if include_expired else RoomInvitation.STATUS_PENDING,
                include_expired=include_expired
            )

            return True, "INVITATIONS_RETRIEVED_SUCCESS", invitations

        except Exception as e:
            current_app.logger.error(f"Error getting invitations: {str(e)}", exc_info=True)
            return False, "GET_INVITATIONS_ERROR", []

    def get_sent_invitations(
        self,
        user_id: str
    ) -> Tuple[bool, str, List[RoomInvitation]]:
        """
        Get invitations sent by user.

        Args:
            user_id: User ID

        Returns:
            Tuple of (success, message, invitations)
        """
        try:
            user_id = extract_user_id(user_id)

            invitations = self.invitation_repository.get_sent_invitations(user_id)

            return True, "SENT_INVITATIONS_RETRIEVED", invitations

        except Exception as e:
            current_app.logger.error(f"Error getting sent invitations: {str(e)}", exc_info=True)
            return False, "GET_SENT_INVITATIONS_ERROR", []

    def cancel_invitation(
        self,
        invitation_id: str,
        user_id: str
    ) -> Tuple[bool, str]:
        """
        Cancel invitation (sender only).

        Args:
            invitation_id: Invitation ID
            user_id: User ID (must be sender)

        Returns:
            Tuple of (success, message)
        """
        try:
            user_id = extract_user_id(user_id)

            # Get invitation
            invitation = self.invitation_repository.get_invitation(invitation_id)
            if not invitation:
                return False, "INVITATION_NOT_FOUND"

            # Verify sender
            if invitation.sender_user_id != user_id:
                return False, "NOT_INVITATION_SENDER"

            # Check if pending
            if invitation.status != RoomInvitation.STATUS_PENDING:
                return False, "INVITATION_ALREADY_PROCESSED"

            # Mark as declined (cancelled)
            self.invitation_repository.update_invitation_status(
                invitation_id,
                RoomInvitation.STATUS_DECLINED
            )

            current_app.logger.info(
                f"Invitation {invitation_id} cancelled by sender {user_id}"
            )

            return True, "INVITATION_CANCELLED_SUCCESS"

        except Exception as e:
            current_app.logger.error(f"Error cancelling invitation: {str(e)}", exc_info=True)
            return False, "CANCEL_INVITATION_ERROR"

    def cleanup_expired(self) -> int:
        """
        Cleanup expired invitations.

        Returns:
            Number of invitations marked as expired
        """
        try:
            count = self.invitation_repository.cleanup_expired_invitations()

            if count > 0:
                current_app.logger.info(f"Marked {count} invitations as expired")

            return count

        except Exception as e:
            current_app.logger.error(f"Error cleaning up invitations: {str(e)}", exc_info=True)
            return 0

    def get_room_invitations(
        self,
        room_id: str,
        user_id: str
    ) -> Tuple[bool, str, List[RoomInvitation]]:
        """
        Get invitations for a room (host only).

        Args:
            room_id: Room ID
            user_id: User ID (must be host)

        Returns:
            Tuple of (success, message, invitations)
        """
        try:
            user_id = extract_user_id(user_id)

            # Verify room and host
            room = self.room_repository.find_by_room_id(room_id)
            if not room:
                return False, "ROOM_NOT_FOUND", []

            if not room.is_host(user_id):
                return False, "NOT_ROOM_HOST", []

            # Get invitations
            invitations = self.invitation_repository.get_room_invitations(room_id)

            return True, "ROOM_INVITATIONS_RETRIEVED", invitations

        except Exception as e:
            current_app.logger.error(f"Error getting room invitations: {str(e)}", exc_info=True)
            return False, "GET_ROOM_INVITATIONS_ERROR", []
