from typing import List, Optional
from datetime import datetime, timezone, timedelta
from flask import current_app
from app import get_db
from app.core.models.device_token import DeviceToken
from app.core.repositories.base_repository import BaseRepository
from app.core.utils.helpers import extract_user_id


class DeviceTokenRepository(BaseRepository):
    """Repository for device token operations"""

    def __init__(self):
        super().__init__('device_tokens')

    def create_indexes(self):
        """Create database indexes for device tokens"""
        import os
        if self.collection is None or os.getenv('TESTING') == 'true':
            return

        try:
            # Unique index on token_id
            self.collection.create_index('token_id', unique=True)

            # Index for querying user tokens
            self.collection.create_index('user_id')

            # Index for device_token (for checking duplicates)
            self.collection.create_index('device_token')

            # Compound index for user + platform
            self.collection.create_index([('user_id', 1), ('platform', 1)])

            # Index for cleanup queries
            self.collection.create_index('last_used_at')

            current_app.logger.info("DeviceToken indexes created successfully")
        except Exception as e:
            current_app.logger.error(f"Error creating DeviceToken indexes: {str(e)}")

    def create_token(self, device_token: DeviceToken) -> bool:
        """
        Create or update device token.

        If token already exists for this user/device, update it.

        Args:
            device_token: DeviceToken instance

        Returns:
            True if successful, False otherwise
        """
        try:
            user_id = extract_user_id(device_token.user_id)

            # Check if this device_token already exists
            existing = self.collection.find_one({'device_token': device_token.device_token})

            if existing:
                # Update existing token
                self.collection.update_one(
                    {'device_token': device_token.device_token},
                    {
                        '$set': {
                            'user_id': user_id,
                            'platform': device_token.platform,
                            'device_info': device_token.device_info,
                            'last_used_at': device_token.last_used_at
                        }
                    }
                )
                current_app.logger.info(f"Updated existing device token for user {user_id}")
            else:
                # Insert new token
                token_dict = {
                    'token_id': device_token.token_id,
                    'user_id': user_id,
                    'device_token': device_token.device_token,
                    'platform': device_token.platform,
                    'device_info': device_token.device_info,
                    'last_used_at': device_token.last_used_at,
                    'created_at': device_token.created_at
                }
                self.collection.insert_one(token_dict)
                current_app.logger.info(f"Created new device token for user {user_id}")

            return True
        except Exception as e:
            current_app.logger.error(f"Error creating device token: {str(e)}", exc_info=True)
            return False

    def get_token(self, token_id: str) -> Optional[DeviceToken]:
        """
        Get device token by token_id.

        Args:
            token_id: Token ID

        Returns:
            DeviceToken instance or None
        """
        try:
            token_doc = self.collection.find_one({'token_id': token_id})
            if token_doc:
                return DeviceToken.from_dict(token_doc)
            return None
        except Exception as e:
            current_app.logger.error(f"Error getting device token: {str(e)}", exc_info=True)
            return None

    def get_user_tokens(self, user_id: str) -> List[DeviceToken]:
        """
        Get all active tokens for a user.

        Args:
            user_id: User ID

        Returns:
            List of DeviceToken instances
        """
        try:
            user_id = extract_user_id(user_id)

            token_docs = self.collection.find({'user_id': user_id})

            tokens = []
            for doc in token_docs:
                token = DeviceToken.from_dict(doc)
                if token.is_valid():
                    tokens.append(token)

            return tokens
        except Exception as e:
            current_app.logger.error(f"Error getting user tokens: {str(e)}", exc_info=True)
            return []

    def get_user_tokens_by_platform(self, user_id: str, platform: str) -> List[DeviceToken]:
        """
        Get user tokens filtered by platform.

        Args:
            user_id: User ID
            platform: Platform (android/ios/web)

        Returns:
            List of DeviceToken instances
        """
        try:
            user_id = extract_user_id(user_id)

            token_docs = self.collection.find({
                'user_id': user_id,
                'platform': platform
            })

            tokens = []
            for doc in token_docs:
                token = DeviceToken.from_dict(doc)
                if token.is_valid():
                    tokens.append(token)

            return tokens
        except Exception as e:
            current_app.logger.error(f"Error getting user tokens by platform: {str(e)}", exc_info=True)
            return []

    def update_last_used(self, token_id: str) -> bool:
        """
        Update last_used_at timestamp for a token.

        Args:
            token_id: Token ID

        Returns:
            True if successful, False otherwise
        """
        try:
            result = self.collection.update_one(
                {'token_id': token_id},
                {'$set': {'last_used_at': datetime.now(timezone.utc)}}
            )
            return result.modified_count > 0
        except Exception as e:
            current_app.logger.error(f"Error updating last_used: {str(e)}", exc_info=True)
            return False

    def delete_token(self, token_id: str, user_id: str) -> bool:
        """
        Delete a device token (user owns the token).

        Args:
            token_id: Token ID
            user_id: User ID (for authorization)

        Returns:
            True if deleted, False otherwise
        """
        try:
            user_id = extract_user_id(user_id)

            result = self.collection.delete_one({
                'token_id': token_id,
                'user_id': user_id
            })
            return result.deleted_count > 0
        except Exception as e:
            current_app.logger.error(f"Error deleting device token: {str(e)}", exc_info=True)
            return False

    def delete_token_by_device_token(self, device_token: str) -> bool:
        """
        Delete token by FCM device token (for expired/invalid tokens).

        Args:
            device_token: FCM device token string

        Returns:
            True if deleted, False otherwise
        """
        try:
            result = self.collection.delete_one({'device_token': device_token})
            if result.deleted_count > 0:
                current_app.logger.info(f"Deleted invalid device token")
            return result.deleted_count > 0
        except Exception as e:
            current_app.logger.error(f"Error deleting device token by token string: {str(e)}", exc_info=True)
            return False

    def delete_user_tokens(self, user_id: str) -> int:
        """
        Delete all tokens for a user (e.g., on account deletion).

        Args:
            user_id: User ID

        Returns:
            Number of tokens deleted
        """
        try:
            user_id = extract_user_id(user_id)

            result = self.collection.delete_many({'user_id': user_id})
            return result.deleted_count
        except Exception as e:
            current_app.logger.error(f"Error deleting user tokens: {str(e)}", exc_info=True)
            return 0

    def delete_expired_tokens(self) -> int:
        """
        Delete tokens that haven't been used in TOKEN_EXPIRY_DAYS.

        Returns:
            Number of tokens deleted
        """
        try:
            expiry_threshold = datetime.now(timezone.utc) - timedelta(days=DeviceToken.TOKEN_EXPIRY_DAYS)

            result = self.collection.delete_many({
                'last_used_at': {'$lt': expiry_threshold}
            })

            if result.deleted_count > 0:
                current_app.logger.info(f"Deleted {result.deleted_count} expired device tokens")

            return result.deleted_count
        except Exception as e:
            current_app.logger.error(f"Error deleting expired tokens: {str(e)}", exc_info=True)
            return 0

    def count_user_tokens(self, user_id: str) -> int:
        """
        Count active tokens for a user.

        Args:
            user_id: User ID

        Returns:
            Number of active tokens
        """
        try:
            user_id = extract_user_id(user_id)
            return self.collection.count_documents({'user_id': user_id})
        except Exception as e:
            current_app.logger.error(f"Error counting user tokens: {str(e)}", exc_info=True)
            return 0
