import uuid
from typing import List, Dict, Any, Optional, Tuple
from flask import current_app
from datetime import datetime, timezone
from flask_socketio import emit
from app.core.models.user_notification import UserNotification
from app.core.repositories.notification_repository import NotificationRepository
from app.core.repositories.notification_preferences_repository import NotificationPreferencesRepository
from app.core.services.fcm_service import FCMService
from app.core.utils.helpers import extract_user_id


class NotificationService:
    """
    Centralized service for sending notifications across multiple channels.

    Handles WebSocket real-time, FCM push, and persistent inbox storage.
    Respects user notification preferences and quiet hours.
    """

    def __init__(self):
        self.notification_repository = NotificationRepository()
        self.preferences_repository = NotificationPreferencesRepository()
        self.fcm_service = FCMService()

    def send_notification(
        self,
        user_id: str,
        type: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
        channels: Optional[List[str]] = None,
        badge: Optional[int] = None,
        sound: Optional[str] = None
    ) -> Dict[str, bool]:
        """
        Send notification to user via multiple channels.

        Args:
            user_id: User ID to send notification to
            type: Notification type (see UserNotification.TYPE_* constants)
            title: Notification title
            body: Notification body text
            data: Additional structured data
            channels: List of channels ['websocket', 'push', 'inbox'] (None = all)
            badge: Badge count for iOS push
            sound: Sound name for push notification

        Returns:
            Dict with delivery status per channel: {'websocket': bool, 'push': bool, 'inbox': bool}
        """
        try:
            user_id = extract_user_id(user_id)

            # Default to all channels if not specified
            if channels is None:
                channels = ['websocket', 'push', 'inbox']

            # Get user preferences
            preferences = self.preferences_repository.get_preferences(user_id)

            # Check if notification type is enabled
            if not preferences.is_type_enabled(type):
                current_app.logger.info(
                    f"Notification type {type} disabled for user {user_id}. Skipping all channels."
                )
                return {'websocket': False, 'push': False, 'inbox': False}

            delivery_status = {
                'websocket': False,
                'push': False,
                'inbox': False
            }

            # Store in inbox (always, regardless of preferences)
            if 'inbox' in channels:
                notification = UserNotification(
                    notification_id=str(uuid.uuid4()),
                    user_id=user_id,
                    type=type,
                    title=title,
                    body=body,
                    data=data or {}
                )
                delivery_status['inbox'] = self.notification_repository.create_notification(notification)

            # Send WebSocket notification (if user is online)
            if 'websocket' in channels:
                delivery_status['websocket'] = self._send_websocket(
                    user_id, type, title, body, data
                )

            # Send push notification (respect preferences and quiet hours)
            if 'push' in channels:
                should_send_push = preferences.should_send_notification(type)

                if should_send_push:
                    delivery_status['push'] = self._send_push(
                        user_id, title, body, data, badge, sound
                    )
                else:
                    current_app.logger.info(
                        f"Push notification blocked by preferences for user {user_id} "
                        f"(type: {type}, in_quiet_hours: {preferences.is_in_quiet_hours()})"
                    )
                    delivery_status['push'] = False

            return delivery_status

        except Exception as e:
            current_app.logger.error(f"Error sending notification: {str(e)}", exc_info=True)
            return {'websocket': False, 'push': False, 'inbox': False}

    def _send_websocket(
        self,
        user_id: str,
        type: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]]
    ) -> bool:
        """
        Send WebSocket notification to user's personal room.

        Args:
            user_id: User ID
            type: Notification type
            title: Title
            body: Body
            data: Additional data

        Returns:
            True if sent (doesn't guarantee delivery), False if error
        """
        try:
            # Import here to avoid circular dependency
            from app import socketio

            # Prepare payload
            payload = {
                'type': type,
                'title': title,
                'body': body,
                'data': data or {},
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

            # Emit to user's personal room
            # (User joins their personal room on WebSocket authentication)
            socketio.emit(
                'notification',
                payload,
                room=f'user_{user_id}',
                namespace='/multiplayer'
            )

            current_app.logger.info(
                f"WebSocket notification sent to user {user_id} (type: {type})"
            )
            return True

        except Exception as e:
            current_app.logger.error(f"Error sending WebSocket notification: {str(e)}", exc_info=True)
            return False

    def _send_push(
        self,
        user_id: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]],
        badge: Optional[int],
        sound: Optional[str]
    ) -> bool:
        """
        Send FCM push notification.

        Args:
            user_id: User ID
            title: Title
            body: Body
            data: Additional data
            badge: Badge count
            sound: Sound name

        Returns:
            True if at least one device received notification, False otherwise
        """
        try:
            success_count, failure_count = self.fcm_service.send_to_user(
                user_id=user_id,
                title=title,
                body=body,
                data=data,
                badge=badge,
                sound=sound
            )

            return success_count > 0

        except Exception as e:
            current_app.logger.error(f"Error sending push notification: {str(e)}", exc_info=True)
            return False

    def send_batch_notifications(
        self,
        notifications: List[Dict[str, Any]]
    ) -> List[Dict[str, bool]]:
        """
        Send batch of notifications to different users.

        Args:
            notifications: List of notification dicts with keys:
                - user_id: str
                - type: str
                - title: str
                - body: str
                - data: Optional[Dict]
                - channels: Optional[List[str]]
                - badge: Optional[int]
                - sound: Optional[str]

        Returns:
            List of delivery status dicts per notification
        """
        results = []

        try:
            for notif in notifications:
                status = self.send_notification(
                    user_id=notif['user_id'],
                    type=notif['type'],
                    title=notif['title'],
                    body=notif['body'],
                    data=notif.get('data'),
                    channels=notif.get('channels'),
                    badge=notif.get('badge'),
                    sound=notif.get('sound')
                )
                results.append(status)

            return results

        except Exception as e:
            current_app.logger.error(f"Error sending batch notifications: {str(e)}", exc_info=True)
            return results

    def send_multicast_notification(
        self,
        user_ids: List[str],
        type: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
        channels: Optional[List[str]] = None,
        badge: Optional[int] = None,
        sound: Optional[str] = None
    ) -> Dict[str, int]:
        """
        Send same notification to multiple users.

        Args:
            user_ids: List of user IDs
            type: Notification type
            title: Title
            body: Body
            data: Additional data
            channels: Channels to use
            badge: Badge count
            sound: Sound name

        Returns:
            Dict with counts: {'total': int, 'websocket': int, 'push': int, 'inbox': int}
        """
        counts = {'total': len(user_ids), 'websocket': 0, 'push': 0, 'inbox': 0}

        try:
            for user_id in user_ids:
                status = self.send_notification(
                    user_id=user_id,
                    type=type,
                    title=title,
                    body=body,
                    data=data,
                    channels=channels,
                    badge=badge,
                    sound=sound
                )

                if status.get('websocket'):
                    counts['websocket'] += 1
                if status.get('push'):
                    counts['push'] += 1
                if status.get('inbox'):
                    counts['inbox'] += 1

            current_app.logger.info(
                f"Multicast notification sent to {len(user_ids)} users: "
                f"ws={counts['websocket']}, push={counts['push']}, inbox={counts['inbox']}"
            )

            return counts

        except Exception as e:
            current_app.logger.error(f"Error sending multicast notification: {str(e)}", exc_info=True)
            return counts

    # Convenience methods for common notification types

    def send_invitation_received(
        self,
        recipient_user_id: str,
        sender_name: str,
        game_name: str,
        room_code: str,
        invitation_data: Dict[str, Any]
    ) -> Dict[str, bool]:
        """Send invitation received notification"""
        return self.send_notification(
            user_id=recipient_user_id,
            type=UserNotification.TYPE_INVITATION_RECEIVED,
            title=f"Invitation from {sender_name}",
            body=f"Join {game_name} - Room {room_code}",
            data=invitation_data,
            channels=['websocket', 'push', 'inbox']
        )

    def send_invitation_accepted(
        self,
        sender_user_id: str,
        acceptor_name: str,
        room_code: str,
        invitation_data: Dict[str, Any]
    ) -> Dict[str, bool]:
        """Send invitation accepted notification"""
        return self.send_notification(
            user_id=sender_user_id,
            type=UserNotification.TYPE_INVITATION_ACCEPTED,
            title=f"{acceptor_name} accepted your invitation",
            body=f"They joined room {room_code}",
            data=invitation_data,
            channels=['websocket', 'inbox']  # No push for accepts
        )

    def send_invitation_declined(
        self,
        sender_user_id: str,
        decliner_name: str,
        room_code: str,
        invitation_data: Dict[str, Any]
    ) -> Dict[str, bool]:
        """Send invitation declined notification"""
        return self.send_notification(
            user_id=sender_user_id,
            type=UserNotification.TYPE_INVITATION_DECLINED,
            title=f"{decliner_name} declined your invitation",
            body=f"Room {room_code}",
            data=invitation_data,
            channels=['websocket', 'inbox']  # No push for declines
        )

    def send_invitation_expired(
        self,
        recipient_user_id: str,
        room_code: str,
        invitation_data: Dict[str, Any]
    ) -> Dict[str, bool]:
        """Send invitation expired notification"""
        return self.send_notification(
            user_id=recipient_user_id,
            type=UserNotification.TYPE_INVITATION_EXPIRED,
            title="Invitation expired",
            body=f"Invitation to room {room_code} has expired",
            data=invitation_data,
            channels=['websocket', 'inbox']  # No push for expiry
        )

    def send_invitation_expiring_soon(
        self,
        recipient_user_id: str,
        game_name: str,
        room_code: str,
        minutes_remaining: int,
        invitation_data: Dict[str, Any]
    ) -> Dict[str, bool]:
        """Send invitation expiring soon warning"""
        return self.send_notification(
            user_id=recipient_user_id,
            type=UserNotification.TYPE_INVITATION_EXPIRING_SOON,
            title=f"Invitation expiring soon",
            body=f"Join {game_name} (Room {room_code}) - Expires in {minutes_remaining} minutes",
            data=invitation_data,
            channels=['websocket', 'push', 'inbox']  # Push for warnings
        )

    def send_friend_online(
        self,
        user_id: str,
        friend_name: str,
        friend_data: Dict[str, Any]
    ) -> Dict[str, bool]:
        """Send friend online notification"""
        return self.send_notification(
            user_id=user_id,
            type=UserNotification.TYPE_FRIEND_ONLINE,
            title=f"{friend_name} is online",
            body="Tap to invite them to play",
            data=friend_data,
            channels=['websocket', 'inbox']  # No push for friend online
        )

    def send_friend_joined_room(
        self,
        user_id: str,
        friend_name: str,
        room_code: str,
        room_data: Dict[str, Any]
    ) -> Dict[str, bool]:
        """Send friend joined room notification"""
        return self.send_notification(
            user_id=user_id,
            type=UserNotification.TYPE_FRIEND_JOINED_ROOM,
            title=f"{friend_name} joined a game",
            body=f"Room {room_code} - Tap to join",
            data=room_data,
            channels=['websocket', 'push', 'inbox']
        )
