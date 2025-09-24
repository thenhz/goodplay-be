from datetime import datetime
from typing import Dict, Any, Optional, List
from bson import ObjectId
from dataclasses import dataclass, field

@dataclass
class ChallengeInteraction:
    """Social interaction within a challenge (cheers, comments, reactions)"""
    challenge_id: str
    from_user_id: str  # User performing the interaction
    to_user_id: str    # Target user (can be same as from_user for general challenge interactions)

    interaction_type: str  # 'cheer', 'comment', 'reaction', 'share', 'spectate'
    content: str = ""  # Text content for comments, empty for cheers/reactions

    # Interaction Metadata
    emoji: Optional[str] = None  # For reactions/cheers: 👏, 🔥, 💪, etc.
    reaction_type: Optional[str] = None  # 'cheer', 'celebrate', 'encourage', 'wow'

    # Context
    context_type: str = "general"  # 'progress_update', 'milestone', 'completion', 'general'
    context_data: Dict[str, Any] = field(default_factory=dict)

    # Timing
    created_at: datetime = field(default_factory=datetime.utcnow)

    # Visibility and Moderation
    is_public: bool = True
    is_deleted: bool = False
    is_flagged: bool = False
    moderation_status: str = "approved"  # 'approved', 'pending', 'rejected'

    # Response and Engagement
    replies: List[Dict[str, Any]] = field(default_factory=list)
    likes_count: int = 0
    liked_by: List[str] = field(default_factory=list)

    _id: Optional[ObjectId] = field(default=None)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the interaction to a dictionary for MongoDB storage"""
        data = {
            "challenge_id": self.challenge_id,
            "from_user_id": self.from_user_id,
            "to_user_id": self.to_user_id,
            "interaction_type": self.interaction_type,
            "content": self.content,
            "emoji": self.emoji,
            "reaction_type": self.reaction_type,
            "context_type": self.context_type,
            "context_data": self.context_data,
            "created_at": self.created_at,
            "is_public": self.is_public,
            "is_deleted": self.is_deleted,
            "is_flagged": self.is_flagged,
            "moderation_status": self.moderation_status,
            "replies": self.replies,
            "likes_count": self.likes_count,
            "liked_by": self.liked_by
        }

        if self._id:
            data["_id"] = self._id

        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChallengeInteraction':
        """Create a ChallengeInteraction instance from a dictionary"""
        interaction = cls(
            challenge_id=data.get("challenge_id", ""),
            from_user_id=data.get("from_user_id", ""),
            to_user_id=data.get("to_user_id", ""),
            interaction_type=data.get("interaction_type", ""),
            content=data.get("content", ""),
            emoji=data.get("emoji"),
            reaction_type=data.get("reaction_type"),
            context_type=data.get("context_type", "general"),
            context_data=data.get("context_data", {}),
            created_at=data.get("created_at", datetime.utcnow()),
            is_public=data.get("is_public", True),
            is_deleted=data.get("is_deleted", False),
            is_flagged=data.get("is_flagged", False),
            moderation_status=data.get("moderation_status", "approved"),
            replies=data.get("replies", []),
            likes_count=data.get("likes_count", 0),
            liked_by=data.get("liked_by", [])
        )

        if "_id" in data:
            interaction._id = data["_id"]

        return interaction

    def to_api_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """Convert the interaction to a dictionary for API responses"""
        api_data = {
            "id": str(self._id) if self._id else None,
            "challenge_id": self.challenge_id,
            "from_user_id": self.from_user_id,
            "to_user_id": self.to_user_id,
            "interaction_type": self.interaction_type,
            "content": self.content if not self.is_deleted else "[deleted]",
            "emoji": self.emoji,
            "reaction_type": self.reaction_type,
            "context_type": self.context_type,
            "created_at": self.created_at.isoformat(),
            "likes_count": self.likes_count,
            "replies_count": len(self.replies),
            "is_public": self.is_public
        }

        # Include context data for relevant interactions
        if self.context_type != "general" and self.context_data:
            api_data["context"] = self.context_data

        # Include sensitive data only if requested (for moderation/admin)
        if include_sensitive:
            api_data["moderation"] = {
                "is_deleted": self.is_deleted,
                "is_flagged": self.is_flagged,
                "status": self.moderation_status,
                "liked_by": self.liked_by
            }

        return api_data

    def add_reply(self, from_user_id: str, content: str) -> Dict[str, Any]:
        """Add a reply to this interaction"""
        reply = {
            "reply_id": str(ObjectId()),
            "from_user_id": from_user_id,
            "content": content,
            "created_at": datetime.utcnow(),
            "is_deleted": False
        }

        self.replies.append(reply)
        return reply

    def delete_reply(self, reply_id: str, user_id: str) -> bool:
        """Delete a reply (only by original author or admin)"""
        for reply in self.replies:
            if (reply.get("reply_id") == reply_id and
                reply.get("from_user_id") == user_id):
                reply["is_deleted"] = True
                reply["content"] = "[deleted]"
                return True
        return False

    def add_like(self, user_id: str) -> bool:
        """Add a like to this interaction"""
        if user_id in self.liked_by:
            return False  # Already liked

        self.liked_by.append(user_id)
        self.likes_count = len(self.liked_by)
        return True

    def remove_like(self, user_id: str) -> bool:
        """Remove a like from this interaction"""
        if user_id not in self.liked_by:
            return False  # Not liked

        self.liked_by.remove(user_id)
        self.likes_count = len(self.liked_by)
        return True

    def delete(self, user_id: str) -> bool:
        """Delete the interaction (only by original author)"""
        if user_id != self.from_user_id:
            return False

        self.is_deleted = True
        self.content = "[deleted]"
        return True

    def flag(self, reason: str = "") -> bool:
        """Flag interaction for moderation"""
        if self.is_flagged:
            return False

        self.is_flagged = True
        self.moderation_status = "pending"
        if reason:
            self.context_data["flag_reason"] = reason
            self.context_data["flagged_at"] = datetime.utcnow()

        return True

    def approve_moderation(self) -> bool:
        """Approve flagged interaction"""
        if not self.is_flagged:
            return False

        self.is_flagged = False
        self.moderation_status = "approved"
        return True

    def reject_moderation(self, reason: str = "") -> bool:
        """Reject flagged interaction"""
        if not self.is_flagged:
            return False

        self.moderation_status = "rejected"
        self.is_deleted = True
        self.content = "[removed]"
        if reason:
            self.context_data["rejection_reason"] = reason

        return True

    def is_visible(self) -> bool:
        """Check if interaction is visible to users"""
        return (not self.is_deleted and
                self.is_public and
                self.moderation_status == "approved")

    def can_user_interact(self, user_id: str) -> bool:
        """Check if user can interact with this item (like, reply)"""
        return self.is_visible() and user_id != self.from_user_id

    @staticmethod
    def create_cheer(challenge_id: str, from_user_id: str, to_user_id: str,
                    emoji: str = "👏", reaction_type: str = "cheer") -> 'ChallengeInteraction':
        """Create a cheer interaction"""
        return ChallengeInteraction(
            challenge_id=challenge_id,
            from_user_id=from_user_id,
            to_user_id=to_user_id,
            interaction_type="cheer",
            emoji=emoji,
            reaction_type=reaction_type,
            context_type="encouragement"
        )

    @staticmethod
    def create_comment(challenge_id: str, from_user_id: str, to_user_id: str,
                      content: str, context_type: str = "general",
                      context_data: Dict[str, Any] = None) -> 'ChallengeInteraction':
        """Create a comment interaction"""
        return ChallengeInteraction(
            challenge_id=challenge_id,
            from_user_id=from_user_id,
            to_user_id=to_user_id,
            interaction_type="comment",
            content=content,
            context_type=context_type,
            context_data=context_data or {}
        )

    @staticmethod
    def create_milestone_celebration(challenge_id: str, from_user_id: str, to_user_id: str,
                                   milestone_data: Dict[str, Any]) -> 'ChallengeInteraction':
        """Create a milestone celebration interaction"""
        return ChallengeInteraction(
            challenge_id=challenge_id,
            from_user_id=from_user_id,
            to_user_id=to_user_id,
            interaction_type="cheer",
            emoji="🎉",
            reaction_type="celebrate",
            context_type="milestone",
            context_data=milestone_data
        )

    @staticmethod
    def create_progress_comment(challenge_id: str, from_user_id: str, to_user_id: str,
                              content: str, progress_data: Dict[str, Any]) -> 'ChallengeInteraction':
        """Create a comment on progress update"""
        return ChallengeInteraction(
            challenge_id=challenge_id,
            from_user_id=from_user_id,
            to_user_id=to_user_id,
            interaction_type="comment",
            content=content,
            context_type="progress_update",
            context_data=progress_data
        )

    @staticmethod
    def create_completion_congratulation(challenge_id: str, from_user_id: str, to_user_id: str) -> 'ChallengeInteraction':
        """Create a completion congratulation"""
        return ChallengeInteraction(
            challenge_id=challenge_id,
            from_user_id=from_user_id,
            to_user_id=to_user_id,
            interaction_type="cheer",
            emoji="🏆",
            reaction_type="congratulate",
            context_type="completion"
        )

    def get_interaction_summary(self) -> Dict[str, Any]:
        """Get a summary of the interaction for analytics"""
        return {
            "type": self.interaction_type,
            "context": self.context_type,
            "engagement": {
                "likes": self.likes_count,
                "replies": len(self.replies)
            },
            "visibility": {
                "is_public": self.is_public,
                "is_visible": self.is_visible()
            },
            "created_at": self.created_at.isoformat()
        }

    def __str__(self) -> str:
        return f"ChallengeInteraction(type={self.interaction_type}, from={self.from_user_id}, to={self.to_user_id})"

    def __repr__(self) -> str:
        return self.__str__()