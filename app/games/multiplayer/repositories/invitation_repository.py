import os
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from app.core.repositories.base_repository import BaseRepository
from app.games.multiplayer.models.room_invitation import RoomInvitation


class InvitationRepository(BaseRepository):
    """Repository for room invitation operations"""

    def __init__(self):
        super().__init__(RoomInvitation.COLLECTION_NAME)

    def create_indexes(self):
        """Create database indexes for invitations"""
        if self.collection is None or os.getenv('TESTING') == 'true':
            return

        self.collection.create_index('invitation_id', unique=True)
        self.collection.create_index('room_id')
        self.collection.create_index('sender_user_id')
        self.collection.create_index('recipient_user_id')
        self.collection.create_index([('recipient_user_id', 1), ('status', 1)])
        self.collection.create_index('expires_at')
        self.collection.create_index('created_at')
        self.collection.create_index('status')

    def create_invitation(self, invitation: RoomInvitation) -> bool:
        """
        Create new invitation.

        Args:
            invitation: RoomInvitation object

        Returns:
            True if created successfully
        """
        try:
            self.create(invitation.to_dict())
            return True
        except Exception:
            return False

    def get_invitation(self, invitation_id: str) -> Optional[RoomInvitation]:
        """
        Get invitation by ID.

        Args:
            invitation_id: Invitation ID

        Returns:
            RoomInvitation or None
        """
        data = self.find_one({'invitation_id': invitation_id})
        return RoomInvitation.from_dict(data) if data else None

    def get_user_invitations(
        self,
        user_id: str,
        status: Optional[str] = None,
        include_expired: bool = False
    ) -> List[RoomInvitation]:
        """
        Get invitations for user.

        Args:
            user_id: User ID
            status: Filter by status (optional)
            include_expired: Include expired invitations

        Returns:
            List of invitations
        """
        filter_dict = {'recipient_user_id': user_id}

        if status:
            filter_dict['status'] = status
        elif not include_expired:
            filter_dict['status'] = RoomInvitation.STATUS_PENDING
            filter_dict['expires_at'] = {'$gt': datetime.now(timezone.utc)}

        invitations_data = self.find_many(
            filter_dict,
            sort=[('created_at', -1)]
        )

        return [RoomInvitation.from_dict(data) for data in invitations_data]

    def get_sent_invitations(
        self,
        sender_user_id: str,
        status: Optional[str] = None
    ) -> List[RoomInvitation]:
        """
        Get invitations sent by user.

        Args:
            sender_user_id: Sender user ID
            status: Filter by status (optional)

        Returns:
            List of sent invitations
        """
        filter_dict = {'sender_user_id': sender_user_id}

        if status:
            filter_dict['status'] = status

        invitations_data = self.find_many(
            filter_dict,
            sort=[('created_at', -1)]
        )

        return [RoomInvitation.from_dict(data) for data in invitations_data]

    def update_invitation_status(
        self,
        invitation_id: str,
        status: str,
        timestamp_field: Optional[str] = None
    ) -> bool:
        """
        Update invitation status.

        Args:
            invitation_id: Invitation ID
            status: New status
            timestamp_field: Optional timestamp field to update (accepted_at, declined_at)

        Returns:
            True if updated successfully
        """
        updates = {'status': status}

        if timestamp_field:
            updates[timestamp_field] = datetime.now(timezone.utc)

        return self.update_one({'invitation_id': invitation_id}, updates)

    def get_room_invitations(
        self,
        room_id: str,
        status: Optional[str] = None
    ) -> List[RoomInvitation]:
        """
        Get all invitations for room.

        Args:
            room_id: Room ID
            status: Filter by status (optional)

        Returns:
            List of invitations for the room
        """
        filter_dict = {'room_id': room_id}

        if status:
            filter_dict['status'] = status

        invitations_data = self.find_many(
            filter_dict,
            sort=[('created_at', -1)]
        )

        return [RoomInvitation.from_dict(data) for data in invitations_data]

    def check_existing_invitation(
        self,
        room_id: str,
        recipient_user_id: str
    ) -> Optional[RoomInvitation]:
        """
        Check if pending invitation already exists.

        Args:
            room_id: Room ID
            recipient_user_id: Recipient user ID

        Returns:
            Existing pending invitation or None
        """
        data = self.find_one({
            'room_id': room_id,
            'recipient_user_id': recipient_user_id,
            'status': RoomInvitation.STATUS_PENDING,
            'expires_at': {'$gt': datetime.now(timezone.utc)}
        })

        return RoomInvitation.from_dict(data) if data else None

    def cleanup_expired_invitations(self) -> int:
        """
        Mark expired invitations and optionally delete old ones.

        Returns:
            Number of invitations marked as expired
        """
        now = datetime.now(timezone.utc)

        # Mark pending invitations as expired
        result = self.collection.update_many(
            {
                'status': RoomInvitation.STATUS_PENDING,
                'expires_at': {'$lt': now}
            },
            {'$set': {'status': RoomInvitation.STATUS_EXPIRED}}
        )

        return result.modified_count

    def delete_old_invitations(self, days: int = 30) -> int:
        """
        Delete old non-pending invitations.

        Args:
            days: Delete invitations older than this many days

        Returns:
            Number of invitations deleted
        """
        from datetime import timedelta
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        result = self.collection.delete_many({
            'status': {'$in': [
                RoomInvitation.STATUS_ACCEPTED,
                RoomInvitation.STATUS_DECLINED,
                RoomInvitation.STATUS_EXPIRED
            ]},
            'created_at': {'$lt': cutoff}
        })

        return result.deleted_count

    def get_invitation_statistics(self) -> Dict[str, int]:
        """
        Get invitation statistics.

        Returns:
            Dictionary with invitation counts by status
        """
        return {
            'total': self.count({}),
            'pending': self.count({'status': RoomInvitation.STATUS_PENDING}),
            'accepted': self.count({'status': RoomInvitation.STATUS_ACCEPTED}),
            'declined': self.count({'status': RoomInvitation.STATUS_DECLINED}),
            'expired': self.count({'status': RoomInvitation.STATUS_EXPIRED})
        }
