from typing import Optional, List, Dict, Any
from bson import ObjectId
from pymongo import ASCENDING, DESCENDING
from app.core.repositories.base_repository import BaseRepository
from app.social.models.user_relationship import UserRelationship


class RelationshipRepository(BaseRepository):
    """Repository for managing user relationships"""

    def __init__(self):
        super().__init__('user_relationships')

    def create_indexes(self):
        """Create database indexes for optimal query performance"""
        import os
        if self.collection is None or os.getenv('TESTING') == 'true':
            return

        # Compound index for user_id + relationship_type + status
        self.collection.create_index([
            ("user_id", ASCENDING),
            ("relationship_type", ASCENDING),
            ("status", ASCENDING)
        ])

        # Compound index for target_user_id + relationship_type + status
        self.collection.create_index([
            ("target_user_id", ASCENDING),
            ("relationship_type", ASCENDING),
            ("status", ASCENDING)
        ])

        # Index for finding relationships between two users
        self.collection.create_index([
            ("user_id", ASCENDING),
            ("target_user_id", ASCENDING)
        ])

        # Index for finding relationships initiated by a user
        self.collection.create_index([
            ("initiated_by", ASCENDING),
            ("created_at", DESCENDING)
        ])

        # Sparse index for pending relationships (for notifications)
        self.collection.create_index([
            ("target_user_id", ASCENDING),
            ("status", ASCENDING),
            ("created_at", DESCENDING)
        ], sparse=True)

    def create_relationship(self, relationship: UserRelationship) -> str:
        """Create a new relationship"""
        relationship_data = relationship.to_dict()
        return self.create(relationship_data)

    def find_relationship_by_id(self, relationship_id: str) -> Optional[UserRelationship]:
        """Find relationship by ID"""
        data = self.find_by_id(relationship_id)
        if data:
            return UserRelationship.from_dict(data)
        return None

    def find_relationship_between_users(self, user_id: str, target_user_id: str,
                                       relationship_type: str = None) -> Optional[UserRelationship]:
        """Find relationship between two users"""
        filter_dict = {
            "$or": [
                {"user_id": ObjectId(user_id), "target_user_id": ObjectId(target_user_id)},
                {"user_id": ObjectId(target_user_id), "target_user_id": ObjectId(user_id)}
            ]
        }

        if relationship_type:
            filter_dict["relationship_type"] = relationship_type

        data = self.find_one(filter_dict)
        if data:
            return UserRelationship.from_dict(data)
        return None

    def get_user_relationships(self, user_id: str, relationship_type: str = None,
                             status: str = None, limit: int = None,
                             skip: int = None) -> List[UserRelationship]:
        """Get all relationships for a user"""
        filter_dict = {
            "$or": [
                {"user_id": ObjectId(user_id)},
                {"target_user_id": ObjectId(user_id)}
            ]
        }

        if relationship_type:
            filter_dict["relationship_type"] = relationship_type

        if status:
            filter_dict["status"] = status

        sort = [("created_at", DESCENDING)]
        data_list = self.find_many(filter_dict, limit=limit, skip=skip, sort=sort)

        return [UserRelationship.from_dict(data) for data in data_list]

    def get_user_friends(self, user_id: str, limit: int = None, skip: int = None) -> List[UserRelationship]:
        """Get accepted friend relationships for a user"""
        return self.get_user_relationships(
            user_id=user_id,
            relationship_type=UserRelationship.FRIEND,
            status=UserRelationship.ACCEPTED,
            limit=limit,
            skip=skip
        )

    def get_pending_friend_requests(self, user_id: str, limit: int = None,
                                   skip: int = None) -> List[UserRelationship]:
        """Get pending friend requests received by a user"""
        filter_dict = {
            "target_user_id": ObjectId(user_id),
            "relationship_type": UserRelationship.FRIEND,
            "status": UserRelationship.PENDING
        }

        sort = [("created_at", DESCENDING)]
        data_list = self.find_many(filter_dict, limit=limit, skip=skip, sort=sort)

        return [UserRelationship.from_dict(data) for data in data_list]

    def get_sent_friend_requests(self, user_id: str, limit: int = None,
                                skip: int = None) -> List[UserRelationship]:
        """Get pending friend requests sent by a user"""
        filter_dict = {
            "user_id": ObjectId(user_id),
            "relationship_type": UserRelationship.FRIEND,
            "status": UserRelationship.PENDING
        }

        sort = [("created_at", DESCENDING)]
        data_list = self.find_many(filter_dict, limit=limit, skip=skip, sort=sort)

        return [UserRelationship.from_dict(data) for data in data_list]

    def get_blocked_users(self, user_id: str, limit: int = None, skip: int = None) -> List[UserRelationship]:
        """Get blocked relationships for a user"""
        filter_dict = {
            "user_id": ObjectId(user_id),
            "relationship_type": UserRelationship.BLOCKED,
            "status": UserRelationship.ACCEPTED
        }

        sort = [("created_at", DESCENDING)]
        data_list = self.find_many(filter_dict, limit=limit, skip=skip, sort=sort)

        return [UserRelationship.from_dict(data) for data in data_list]

    def update_relationship_status(self, relationship_id: str, new_status: str) -> bool:
        """Update relationship status"""
        update_data = {
            "status": new_status,
            "updated_at": self._get_current_time()
        }
        return self.update_by_id(relationship_id, update_data)

    def delete_relationship(self, relationship_id: str) -> bool:
        """Delete a relationship"""
        return self.delete_by_id(relationship_id)

    def delete_relationship_between_users(self, user_id: str, target_user_id: str,
                                        relationship_type: str = None) -> bool:
        """Delete relationship between two users"""
        filter_dict = {
            "$or": [
                {"user_id": ObjectId(user_id), "target_user_id": ObjectId(target_user_id)},
                {"user_id": ObjectId(target_user_id), "target_user_id": ObjectId(user_id)}
            ]
        }

        if relationship_type:
            filter_dict["relationship_type"] = relationship_type

        return self.delete_one(filter_dict)

    def is_blocked(self, user_id: str, target_user_id: str) -> bool:
        """Check if one user has blocked another"""
        filter_dict = {
            "user_id": ObjectId(user_id),
            "target_user_id": ObjectId(target_user_id),
            "relationship_type": UserRelationship.BLOCKED,
            "status": UserRelationship.ACCEPTED
        }

        return self.find_one(filter_dict) is not None

    def are_friends(self, user_id: str, target_user_id: str) -> bool:
        """Check if two users are friends"""
        filter_dict = {
            "$or": [
                {"user_id": ObjectId(user_id), "target_user_id": ObjectId(target_user_id)},
                {"user_id": ObjectId(target_user_id), "target_user_id": ObjectId(user_id)}
            ],
            "relationship_type": UserRelationship.FRIEND,
            "status": UserRelationship.ACCEPTED
        }

        return self.find_one(filter_dict) is not None

    def get_friends_count(self, user_id: str) -> int:
        """Get count of user's friends"""
        filter_dict = {
            "$or": [
                {"user_id": ObjectId(user_id)},
                {"target_user_id": ObjectId(user_id)}
            ],
            "relationship_type": UserRelationship.FRIEND,
            "status": UserRelationship.ACCEPTED
        }

        return self.count(filter_dict)

    def get_pending_requests_count(self, user_id: str) -> int:
        """Get count of pending friend requests for user"""
        filter_dict = {
            "target_user_id": ObjectId(user_id),
            "relationship_type": UserRelationship.FRIEND,
            "status": UserRelationship.PENDING
        }

        return self.count(filter_dict)