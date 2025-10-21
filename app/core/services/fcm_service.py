import os
import logging
from typing import List, Dict, Any, Optional, Tuple
from flask import current_app, has_app_context
import firebase_admin
from firebase_admin import credentials, messaging
from app.core.repositories.device_token_repository import DeviceTokenRepository
from app.core.utils.helpers import extract_user_id

# Fallback logger for when there's no app context
logger = logging.getLogger(__name__)


class FCMService:
    """
    Service for sending push notifications via Firebase Cloud Messaging.

    Supports both Android (FCM) and iOS (APNs via FCM).
    """

    def __init__(self):
        self.device_token_repository = DeviceTokenRepository()
        self._initialized = False
        self._init_attempted = False

    def _get_logger(self):
        """Get logger with app context if available, otherwise use module logger"""
        if has_app_context():
            return current_app.logger
        return logger

    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK (lazy initialization)"""
        # Only attempt initialization once
        if self._init_attempted:
            return

        self._init_attempted = True

        try:
            # Check if already initialized
            if firebase_admin._apps:
                self._initialized = True
                self._get_logger().info("Firebase already initialized")
                return

            # Get credentials path from environment
            creds_path = os.getenv('FIREBASE_CREDENTIALS_PATH')

            if not creds_path:
                self._get_logger().warning(
                    "FIREBASE_CREDENTIALS_PATH not set. FCM push notifications will be disabled."
                )
                return

            if not os.path.exists(creds_path):
                self._get_logger().warning(
                    f"Firebase credentials file not found at {creds_path}. "
                    "FCM push notifications will be disabled."
                )
                return

            # Initialize Firebase
            cred = credentials.Certificate(creds_path)
            firebase_admin.initialize_app(cred)

            self._initialized = True
            self._get_logger().info("Firebase Cloud Messaging initialized successfully")

        except Exception as e:
            self._get_logger().error(f"Error initializing Firebase: {str(e)}", exc_info=True)
            self._initialized = False

    def is_initialized(self) -> bool:
        """Check if FCM is initialized and ready"""
        return self._initialized

    def send_notification(
        self,
        device_tokens: List[str],
        title: str,
        body: str,
        data: Optional[Dict[str, str]] = None,
        badge: Optional[int] = None,
        sound: Optional[str] = None
    ) -> Tuple[int, int, List[str]]:
        """
        Send push notification to specific device tokens.

        Args:
            device_tokens: List of FCM device tokens
            title: Notification title
            body: Notification body
            data: Additional data payload
            badge: Badge count for iOS
            sound: Sound name

        Returns:
            Tuple of (success_count, failure_count, failed_tokens)
        """
        # Lazy initialization
        if not self._init_attempted:
            self._initialize_firebase()

        if not self._initialized:
            self._get_logger().warning("FCM not initialized. Skipping push notification.")
            return 0, len(device_tokens), device_tokens

        if not device_tokens:
            return 0, 0, []

        try:
            # Prepare notification
            notification = messaging.Notification(
                title=title,
                body=body
            )

            # Prepare Android config
            android_config = messaging.AndroidConfig(
                priority='high',
                notification=messaging.AndroidNotification(
                    sound=sound or 'default',
                    channel_id='goodplay_invitations'
                )
            )

            # Prepare iOS config
            apns_config = messaging.APNSConfig(
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(
                        alert=messaging.ApsAlert(
                            title=title,
                            body=body
                        ),
                        badge=badge,
                        sound=sound or 'default'
                    )
                )
            )

            # Prepare data payload (must be strings)
            data_payload = {}
            if data:
                for key, value in data.items():
                    data_payload[key] = str(value)

            # Send to each token (FCM supports batch, but we handle individually for better error tracking)
            success_count = 0
            failure_count = 0
            failed_tokens = []

            for token in device_tokens:
                try:
                    message = messaging.Message(
                        notification=notification,
                        data=data_payload,
                        token=token,
                        android=android_config,
                        apns=apns_config
                    )

                    response = messaging.send(message)
                    success_count += 1

                    self._get_logger().info(f"Push notification sent successfully: {response}")

                except messaging.UnregisteredError:
                    # Token is invalid/expired, mark for deletion
                    failure_count += 1
                    failed_tokens.append(token)
                    self._get_logger().warning(f"Device token unregistered: {token}")
                    self.device_token_repository.delete_token_by_device_token(token)

                except messaging.SenderIdMismatchError:
                    # Token belongs to different sender
                    failure_count += 1
                    failed_tokens.append(token)
                    self._get_logger().warning(f"Sender ID mismatch for token: {token}")
                    self.device_token_repository.delete_token_by_device_token(token)

                except Exception as e:
                    failure_count += 1
                    failed_tokens.append(token)
                    self._get_logger().error(f"Error sending to token {token}: {str(e)}")

            self._get_logger().info(
                f"Push notification batch: {success_count} succeeded, {failure_count} failed"
            )

            return success_count, failure_count, failed_tokens

        except Exception as e:
            self._get_logger().error(f"Error sending push notifications: {str(e)}", exc_info=True)
            return 0, len(device_tokens), device_tokens

    def send_to_user(
        self,
        user_id: str,
        title: str,
        body: str,
        data: Optional[Dict[str, str]] = None,
        badge: Optional[int] = None,
        sound: Optional[str] = None
    ) -> Tuple[int, int]:
        """
        Send push notification to all devices of a user.

        Args:
            user_id: User ID
            title: Notification title
            body: Notification body
            data: Additional data payload
            badge: Badge count for iOS
            sound: Sound name

        Returns:
            Tuple of (success_count, failure_count)
        """
        try:
            user_id = extract_user_id(user_id)

            # Get all user's device tokens
            device_tokens_obj = self.device_token_repository.get_user_tokens(user_id)

            if not device_tokens_obj:
                self._get_logger().info(f"No device tokens found for user {user_id}")
                return 0, 0

            # Extract token strings
            device_tokens = [token.device_token for token in device_tokens_obj]

            # Send notifications
            success_count, failure_count, failed_tokens = self.send_notification(
                device_tokens=device_tokens,
                title=title,
                body=body,
                data=data,
                badge=badge,
                sound=sound
            )

            # Update last_used_at for successfully sent tokens
            for token_obj in device_tokens_obj:
                if token_obj.device_token not in failed_tokens:
                    self.device_token_repository.update_last_used(token_obj.token_id)

            return success_count, failure_count

        except Exception as e:
            self._get_logger().error(f"Error sending push to user: {str(e)}", exc_info=True)
            return 0, 0

    def send_batch(
        self,
        notifications: List[Dict[str, Any]]
    ) -> Tuple[int, int]:
        """
        Send batch of different notifications to different users.

        Args:
            notifications: List of notification dicts with keys:
                - user_id: str
                - title: str
                - body: str
                - data: Optional[Dict]
                - badge: Optional[int]
                - sound: Optional[str]

        Returns:
            Tuple of (total_success_count, total_failure_count)
        """
        total_success = 0
        total_failure = 0

        try:
            for notif in notifications:
                success, failure = self.send_to_user(
                    user_id=notif['user_id'],
                    title=notif['title'],
                    body=notif['body'],
                    data=notif.get('data'),
                    badge=notif.get('badge'),
                    sound=notif.get('sound')
                )
                total_success += success
                total_failure += failure

            self._get_logger().info(
                f"Batch notification complete: {total_success} succeeded, {total_failure} failed"
            )

            return total_success, total_failure

        except Exception as e:
            self._get_logger().error(f"Error sending batch notifications: {str(e)}", exc_info=True)
            return total_success, total_failure

    def send_multicast(
        self,
        user_ids: List[str],
        title: str,
        body: str,
        data: Optional[Dict[str, str]] = None,
        badge: Optional[int] = None,
        sound: Optional[str] = None
    ) -> Tuple[int, int]:
        """
        Send same notification to multiple users.

        Args:
            user_ids: List of user IDs
            title: Notification title
            body: Notification body
            data: Additional data payload
            badge: Badge count
            sound: Sound name

        Returns:
            Tuple of (total_success_count, total_failure_count)
        """
        total_success = 0
        total_failure = 0

        try:
            for user_id in user_ids:
                success, failure = self.send_to_user(
                    user_id=user_id,
                    title=title,
                    body=body,
                    data=data,
                    badge=badge,
                    sound=sound
                )
                total_success += success
                total_failure += failure

            return total_success, total_failure

        except Exception as e:
            self._get_logger().error(f"Error sending multicast: {str(e)}", exc_info=True)
            return total_success, total_failure
