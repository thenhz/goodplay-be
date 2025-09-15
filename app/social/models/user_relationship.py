from datetime import datetime
from typing import Optional, Dict, Any
from bson import ObjectId


class UserRelationship:
    """
    Model for user relationships (friends, following, blocked)

    Collection: user_relationships
    """

    # Relationship types
    FRIEND = 'friend'
    FOLLOWING = 'following'
    BLOCKED = 'blocked'

    # Relationship statuses
    PENDING = 'pending'
    ACCEPTED = 'accepted'
    DECLINED = 'declined'

    VALID_TYPES = [FRIEND, FOLLOWING, BLOCKED]
    VALID_STATUSES = [PENDING, ACCEPTED, DECLINED]

    def __init__(self, user_id: str, target_user_id: str, relationship_type: str,
                 initiated_by: str, status: str = PENDING, _id: Optional[str] = None,
                 created_at: Optional[datetime] = None, updated_at: Optional[datetime] = None):
        """
        Initialize UserRelationship

        Args:
            user_id: ID of the user in the relationship
            target_user_id: ID of the target user
            relationship_type: Type of relationship (friend, following, blocked)
            initiated_by: ID of user who initiated the relationship
            status: Current status (pending, accepted, declined)
            _id: MongoDB document ID
            created_at: Creation timestamp
            updated_at: Last update timestamp
        """
        self._id = ObjectId(_id) if _id else ObjectId()
        self.user_id = ObjectId(user_id)
        self.target_user_id = ObjectId(target_user_id)
        self.relationship_type = relationship_type
        self.status = status
        self.initiated_by = ObjectId(initiated_by)
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()

        self._validate()

    def _validate(self):
        """Validate relationship data"""
        if self.relationship_type not in self.VALID_TYPES:
            raise ValueError(f"Invalid relationship type: {self.relationship_type}")

        if self.status not in self.VALID_STATUSES:
            raise ValueError(f"Invalid status: {self.status}")

        if self.user_id == self.target_user_id:
            raise ValueError("User cannot have relationship with themselves")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB storage"""
        return {
            '_id': self._id,
            'user_id': self.user_id,
            'target_user_id': self.target_user_id,
            'relationship_type': self.relationship_type,
            'status': self.status,
            'initiated_by': self.initiated_by,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserRelationship':
        """Create UserRelationship from dictionary"""
        return cls(
            user_id=str(data['user_id']),
            target_user_id=str(data['target_user_id']),
            relationship_type=data['relationship_type'],
            initiated_by=str(data['initiated_by']),
            status=data['status'],
            _id=str(data['_id']),
            created_at=data['created_at'],
            updated_at=data['updated_at']
        )

    def to_response_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            'id': str(self._id),
            'user_id': str(self.user_id),
            'target_user_id': str(self.target_user_id),
            'relationship_type': self.relationship_type,
            'status': self.status,
            'initiated_by': str(self.initiated_by),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    def update_status(self, new_status: str):
        """Update relationship status"""
        if new_status not in self.VALID_STATUSES:
            raise ValueError(f"Invalid status: {new_status}")

        self.status = new_status
        self.updated_at = datetime.utcnow()

    def is_pending(self) -> bool:
        """Check if relationship is pending"""
        return self.status == self.PENDING

    def is_accepted(self) -> bool:
        """Check if relationship is accepted"""
        return self.status == self.ACCEPTED

    def is_declined(self) -> bool:
        """Check if relationship is declined"""
        return self.status == self.DECLINED

    def is_friend_request(self) -> bool:
        """Check if this is a friend request"""
        return self.relationship_type == self.FRIEND

    def is_follow_request(self) -> bool:
        """Check if this is a follow request"""
        return self.relationship_type == self.FOLLOWING

    def is_block(self) -> bool:
        """Check if this is a block relationship"""
        return self.relationship_type == self.BLOCKED