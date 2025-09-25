from typing import Optional
from pymongo import ASCENDING
from app.core.models.user import User
from app.core.repositories.base_repository import BaseRepository

class UserRepository(BaseRepository):
    def __init__(self):
        super().__init__('users')
    
    def create_indexes(self):
        import os
        if self.collection is None or os.getenv('TESTING') == 'true':
            return

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

    def update_gaming_stats(self, user_id: str, play_time: int = 0, game_category: str = None) -> bool:
        """Update user gaming statistics"""
        update_data = {
            "$inc": {"gaming_stats.total_play_time": play_time, "gaming_stats.games_played": 1},
            "$set": {"gaming_stats.last_activity": self._get_current_time(), "updated_at": self._get_current_time()}
        }

        if game_category:
            update_data["$set"]["gaming_stats.favorite_category"] = game_category

        return self.collection.update_one({"_id": self._get_object_id(user_id)}, update_data).modified_count > 0

    def update_wallet_credits(self, user_id: str, amount: float, transaction_type: str = 'earned') -> bool:
        """Update user wallet credits"""
        update_data = {
            "$set": {"updated_at": self._get_current_time()}
        }

        if transaction_type == 'balance_only':
            # Only update current balance, not totals
            update_data["$inc"] = {"wallet_credits.current_balance": amount}
        else:
            # Update current balance and appropriate total
            update_data["$inc"] = {"wallet_credits.current_balance": amount}
            if transaction_type == 'earned':
                update_data["$inc"]["wallet_credits.total_earned"] = amount
            elif transaction_type == 'donated':
                update_data["$inc"]["wallet_credits.total_donated"] = amount

        return self.collection.update_one({"_id": self._get_object_id(user_id)}, update_data).modified_count > 0

    def update_preferences(self, user_id: str, preferences: dict) -> bool:
        """Update user preferences"""
        update_data = {"$set": {"updated_at": self._get_current_time()}}

        for key, value in preferences.items():
            update_data["$set"][f"preferences.{key}"] = value

        return self.collection.update_one({"_id": self._get_object_id(user_id)}, update_data).modified_count > 0

    def update_social_profile(self, user_id: str, profile_data: dict) -> bool:
        """Update user social profile"""
        update_data = {"$set": {"updated_at": self._get_current_time()}}

        for key, value in profile_data.items():
            update_data["$set"][f"social_profile.{key}"] = value

        return self.collection.update_one({"_id": self._get_object_id(user_id)}, update_data).modified_count > 0

    def get_leaderboard_data(self, limit: int = 10):
        """Get users for leaderboard sorted by impact score"""
        pipeline = [
            {"$match": {"is_active": True}},
            {"$sort": {"impact_score": -1}},
            {"$limit": limit},
            {"$project": {
                "email": 1,
                "social_profile.display_name": 1,
                "impact_score": 1,
                "gaming_stats.total_play_time": 1,
                "wallet_credits.total_donated": 1
            }}
        ]

        return list(self.collection.aggregate(pipeline))

    def find_users_by_game_category(self, category: str, limit: int = 10):
        """Find users who prefer a specific game category"""
        users_data = self.find_many(
            filter_dict={"gaming_stats.favorite_category": category, "is_active": True},
            limit=limit,
            sort=[("gaming_stats.total_play_time", -1)]
        )
        return [User.from_dict(user_data) for user_data in users_data]

    def migrate_existing_users(self):
        """Migrate existing users to add new fields with default values"""
        from datetime import datetime, timezone

        default_gaming_stats = {
            'total_play_time': 0,
            'games_played': 0,
            'favorite_category': None,
            'last_activity': None
        }

        default_preferences = {
            'notification_enabled': True,
            'preferred_game_categories': [],
            'donation_frequency': 'weekly'
        }

        default_wallet_credits = {
            'current_balance': 0.0,
            'total_earned': 0.0,
            'total_donated': 0.0
        }

        # Find users missing new fields
        users_to_migrate = self.collection.find({
            "$or": [
                {"gaming_stats": {"$exists": False}},
                {"preferences": {"$exists": False}},
                {"wallet_credits": {"$exists": False}},
                {"impact_score": {"$exists": False}}
            ]
        })

        migrated_count = 0
        for user in users_to_migrate:
            update_data = {"$set": {"updated_at": datetime.now(timezone.utc)}}

            if "gaming_stats" not in user:
                update_data["$set"]["gaming_stats"] = default_gaming_stats
            if "preferences" not in user:
                update_data["$set"]["preferences"] = default_preferences
                # Set display_name from first_name or email
                display_name = user.get('first_name') or user.get('email', '').split('@')[0]
                update_data["$set"]["social_profile"] = {
                    'display_name': display_name,
                    'privacy_level': 'public',
                    'friends_count': 0
                }
            if "wallet_credits" not in user:
                update_data["$set"]["wallet_credits"] = default_wallet_credits
            if "impact_score" not in user:
                update_data["$set"]["impact_score"] = 0

            self.collection.update_one({"_id": user["_id"]}, update_data)
            migrated_count += 1

        return migrated_count