from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Any
from app.core.utils.json_encoder import serialize_model_dates, parse_datetime
from app.core.utils.helpers import extract_user_id


class RoomInvitation:
    """
    Model for room invitations.

    Attributes:
        invitation_id: Unique invitation identifier
        room_id: ID of the room
        sender_user_id: ID of user sending invitation
        recipient_user_id: ID of user receiving invitation
        status: Invitation status (pending, accepted, declined, expired)
        created_at: Invitation creation timestamp
        expires_at: Invitation expiry timestamp
        accepted_at: Acceptance timestamp
        declined_at: Decline timestamp
        metadata: Additional invitation data
    """

    COLLECTION_NAME = 'room_invitations'

    STATUS_PENDING = 'pending'
    STATUS_ACCEPTED = 'accepted'
    STATUS_DECLINED = 'declined'
    STATUS_EXPIRED = 'expired'

    def __init__(
        self,
        invitation_id: str,
        room_id: str,
        sender_user_id: str,
        recipient_user_id: str,
        status: str = STATUS_PENDING,
        created_at: Optional[datetime] = None,
        expires_at: Optional[datetime] = None,
        accepted_at: Optional[datetime] = None,
        declined_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
        room_code: Optional[str] = None,
        game_id: Optional[str] = None,
        game_name: Optional[str] = None,
        warning_sent: bool = False,
        warning_sent_at: Optional[datetime] = None
    ):
        self.invitation_id = invitation_id
        self.room_id = room_id
        self.sender_user_id = extract_user_id(sender_user_id)
        self.recipient_user_id = extract_user_id(recipient_user_id)
        self.status = status
        self.created_at = created_at or datetime.now(timezone.utc)
        # GOO-60: Invitations expire after 15 minutes
        self.expires_at = expires_at or (self.created_at + timedelta(minutes=15))
        self.accepted_at = accepted_at
        self.declined_at = declined_at
        self.metadata = metadata or {}

        # GOO-60: Explicit fields for easier frontend access
        self.room_code = room_code or (metadata.get('room_code') if metadata else None)
        self.game_id = game_id or (metadata.get('game_id') if metadata else None)
        self.game_name = game_name or (metadata.get('game_name') if metadata else None)

        # Expiry warning tracking (for notification system)
        self.warning_sent = warning_sent
        self.warning_sent_at = warning_sent_at

    def is_expired(self) -> bool:
        """
        Check if invitation has expired.

        Returns:
            True if invitation has passed expiry time
        """
        return datetime.now(timezone.utc) > self.expires_at

    def can_accept(self) -> bool:
        """
        Check if invitation can be accepted.

        Returns:
            True if invitation is pending and not expired
        """
        return self.status == self.STATUS_PENDING and not self.is_expired()

    def accept(self) -> bool:
        """
        Accept the invitation.

        Returns:
            True if successfully accepted, False otherwise
        """
        if self.can_accept():
            self.status = self.STATUS_ACCEPTED
            self.accepted_at = datetime.now(timezone.utc)
            return True
        return False

    def decline(self) -> bool:
        """
        Decline the invitation.

        Returns:
            True if successfully declined, False otherwise
        """
        if self.status == self.STATUS_PENDING:
            self.status = self.STATUS_DECLINED
            self.declined_at = datetime.now(timezone.utc)
            return True
        return False

    def mark_expired(self) -> bool:
        """
        Mark invitation as expired.

        Returns:
            True if status changed to expired
        """
        if self.status == self.STATUS_PENDING and self.is_expired():
            self.status = self.STATUS_EXPIRED
            return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary for MongoDB storage"""
        # Ensure user IDs are always strings, not User objects
        sender_id = extract_user_id(self.sender_user_id)
        recipient_id = extract_user_id(self.recipient_user_id)

        invitation_dict = {
            'invitation_id': self.invitation_id,
            'room_id': self.room_id,
            'room_code': self.room_code,
            'game_id': self.game_id,
            'game_name': self.game_name,
            'sender_user_id': sender_id,
            'recipient_user_id': recipient_id,
            'status': self.status,
            'created_at': self.created_at,
            'expires_at': self.expires_at,
            'accepted_at': self.accepted_at,
            'declined_at': self.declined_at,
            'metadata': self.metadata,
            'warning_sent': self.warning_sent,
            'warning_sent_at': self.warning_sent_at
        }
        return serialize_model_dates(invitation_dict)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'RoomInvitation':
        """Create RoomInvitation from dictionary, parsing datetime strings"""
        return RoomInvitation(
            invitation_id=data['invitation_id'],
            room_id=data['room_id'],
            sender_user_id=data['sender_user_id'],
            recipient_user_id=data['recipient_user_id'],
            status=data.get('status', RoomInvitation.STATUS_PENDING),
            created_at=parse_datetime(data.get('created_at')),
            expires_at=parse_datetime(data.get('expires_at')),
            accepted_at=parse_datetime(data.get('accepted_at')),
            declined_at=parse_datetime(data.get('declined_at')),
            metadata=data.get('metadata', {}),
            room_code=data.get('room_code'),
            game_id=data.get('game_id'),
            game_name=data.get('game_name'),
            warning_sent=data.get('warning_sent', False),
            warning_sent_at=parse_datetime(data.get('warning_sent_at'))
        )
