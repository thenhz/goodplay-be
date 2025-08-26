from typing import Optional
from pymongo import ASCENDING
from app.models.user import User
from app.repositories.base_repository import BaseRepository

class UserRepository(BaseRepository):
    def __init__(self):
        super().__init__('users')
    
    def create_indexes(self):
        if self.collection is not None:
            self.collection.create_index([("email", ASCENDING)], unique=True)
    
    def find_by_email(self, email: str) -> Optional[User]:
        user_data = self.find_one({"email": email.lower()})
        return User.from_dict(user_data, include_sensitive=True) if user_data else None
    
    def find_user_by_id(self, user_id: str) -> Optional[User]:
        user_data = self.find_by_id(user_id)
        return User.from_dict(user_data) if user_data else None
    
    def create_user(self, user: User) -> str:
        user_data = user.to_dict(include_sensitive=True)
        user_data.pop('_id', None)
        return self.create(user_data)
    
    def update_user(self, user_id: str, user: User) -> bool:
        user_data = user.to_dict(include_sensitive=True)
        user_data.pop('_id', None)
        return self.update_by_id(user_id, user_data)
    
    def email_exists(self, email: str, exclude_user_id: str = None) -> bool:
        filter_query = {"email": email.lower()}
        if exclude_user_id:
            filter_query["_id"] = {"$ne": exclude_user_id}
        return self.find_one(filter_query) is not None
    
    def find_active_users(self, limit: int = None, skip: int = None):
        users_data = self.find_many(
            filter_dict={"is_active": True}, 
            limit=limit, 
            skip=skip,
            sort=[("created_at", -1)]
        )
        return [User.from_dict(user_data) for user_data in users_data]
    
    def deactivate_user(self, user_id: str) -> bool:
        return self.update_by_id(user_id, {"is_active": False})
    
    def activate_user(self, user_id: str) -> bool:
        return self.update_by_id(user_id, {"is_active": True})