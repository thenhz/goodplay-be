# Backend Implementation Guide - Notification System
**GoodPlay Flutter App - Notification & Device Management Endpoints**

## 📋 Overview

This document specifies all backend endpoints required for the GoodPlay notification system. The Flutter app is **fully implemented** and ready to integrate with these endpoints.

**OpenAPI Specification**: `docs/openapi/notifications.yaml`

---

## 🎯 Required Endpoints Summary

| Endpoint | Method | Purpose | Priority |
|----------|--------|---------|----------|
| `/api/devices/register` | POST | Register FCM token | **CRITICAL** |
| `/api/devices/unregister` | DELETE | Remove FCM token | **CRITICAL** |
| `/api/notifications` | GET | Fetch notification inbox | **HIGH** |
| `/api/notifications/unread-count` | GET | Get unread count | **MEDIUM** |
| `/api/notifications/{id}` | PUT | Mark as read | **HIGH** |
| `/api/notifications/read-all` | PUT | Mark all as read | **MEDIUM** |
| `/api/notifications/{id}` | DELETE | Delete notification | **HIGH** |
| `/api/notifications` | DELETE | Clear all | **LOW** |

---

## 🔐 Authentication

All endpoints require JWT Bearer token:
```http
Authorization: Bearer <access_token>
```

**Error Responses**:
- `401 Unauthorized`: Invalid or missing token
- Response constant: `INVALID_TOKEN_OR_USER_DISABLED` or `AUTHENTICATION_ERROR`

---

## 📱 1. Device Management Endpoints

### 1.1 Register Device (FCM Token)

**Endpoint**: `POST /api/devices/register`

**Purpose**: Register user's device to receive push notifications

**Request Body**:
```json
{
  "device_token": "fKj3k2Jd9s...FCM_TOKEN_HERE",
  "platform": "android", // or "ios"
  "device_id": "device_abc123", // optional, generate if not provided
  "device_info": { // optional metadata
    "model": "iPhone 14 Pro",
    "os_version": "iOS 17.0",
    "app_version": "1.0.0"
  }
}
```

**Validation**:
- `device_token` (required): Non-empty string
- `platform` (required): Must be exactly `"android"` or `"ios"`
- `device_id` (optional): If provided, update existing device instead of creating new
- `device_info` (optional): Any additional metadata

**Success Response** (200 OK):
```json
{
  "message": "DEVICE_REGISTERED_SUCCESS",
  "data": {
    "device_id": "device_abc123",
    "device_token": "fKj3k2Jd9s...FCM_TOKEN_HERE",
    "registered_at": "2025-10-20T10:00:00.000000+00:00"
  }
}
```

**Error Responses**:
- `400 Bad Request`:
  - `DEVICE_TOKEN_REQUIRED`: Missing device_token
  - `PLATFORM_INVALID`: Platform not "android" or "ios"
  - `DEVICE_REGISTRATION_FAILED`: Database error

**Database Schema** (suggested):
```sql
CREATE TABLE devices (
  device_id VARCHAR(255) PRIMARY KEY,
  user_id VARCHAR(255) NOT NULL,
  device_token TEXT NOT NULL,
  platform ENUM('android', 'ios') NOT NULL,
  device_info JSONB,
  registered_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
  INDEX idx_user_devices (user_id),
  UNIQUE INDEX idx_device_token (device_token)
);
```

**Implementation Notes**:
- One user can have multiple devices
- If `device_id` exists for this user, UPDATE instead of INSERT
- Store `device_token` with UNIQUE constraint (one token per device globally)
- Called on every app login (may be called multiple times - ensure idempotent)

---

### 1.2 Unregister Device (Remove FCM Token)

**Endpoint**: `DELETE /api/devices/unregister`

**Purpose**: Remove device token to stop push notifications (called on logout)

**Request Body**:
```json
{
  "device_token": "fKj3k2Jd9s...FCM_TOKEN_HERE", // optional if device_id provided
  "device_id": "device_abc123" // optional if device_token provided
}
```

**Validation**:
- At least one of `device_token` or `device_id` must be provided
- If both provided, prefer `device_id`

**Success Response** (200 OK):
```json
{
  "message": "DEVICE_UNREGISTERED_SUCCESS"
}
```

**Error Responses**:
- `400 Bad Request`:
  - `DEVICE_TOKEN_OR_ID_REQUIRED`: Neither provided
  - `DEVICE_NOT_FOUND`: Device doesn't exist or doesn't belong to user

**Implementation Notes**:
- DELETE from devices table WHERE (device_token = ? OR device_id = ?) AND user_id = ?
- Must verify device belongs to authenticated user
- If device not found, return success (idempotent)

---

## 📬 2. Notification Inbox Endpoints

### 2.1 Get Notifications (Inbox)

**Endpoint**: `GET /api/notifications`

**Purpose**: Fetch user's notification inbox with pagination and filters

**Query Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `limit` | integer | No | 20 | Items per page (1-100) |
| `offset` | integer | No | 0 | Pagination offset |
| `read` | boolean | No | null | Filter: true=read, false=unread, omit=all |
| `type` | string | No | null | Filter by notification type |

**Valid Notification Types**:
- `room_invitation`
- `friend_request`
- `friend_online`
- `room_started`
- `friend_joined_room`
- `invitation_accepted`
- `invitation_declined`
- `invitation_expired`

**Success Response** (200 OK):
```json
{
  "message": "NOTIFICATIONS_RETRIEVED_SUCCESS",
  "data": {
    "notifications": [
      {
        "id": "notif_123",
        "type": "room_invitation",
        "title": "New Game Invitation",
        "body": "Alice invited you to play TicTacToe",
        "data": {
          "invitation_id": "inv_456",
          "room_id": "room_789",
          "sender_user_id": "user_alice",
          "sender_display_name": "Alice"
        },
        "created_at": "2025-10-20T10:00:00.000000+00:00",
        "is_read": false,
        "read_at": null,
        "expires_at": "2025-10-20T10:15:00.000000+00:00"
      }
    ],
    "total": 45,
    "unread_count": 12,
    "limit": 20,
    "offset": 0,
    "has_more": true
  }
}
```

**Database Schema** (suggested):
```sql
CREATE TABLE notifications (
  id VARCHAR(255) PRIMARY KEY,
  user_id VARCHAR(255) NOT NULL,
  type VARCHAR(50) NOT NULL,
  title VARCHAR(255) NOT NULL,
  body TEXT NOT NULL,
  data JSONB,
  created_at TIMESTAMP DEFAULT NOW(),
  is_read BOOLEAN DEFAULT FALSE,
  read_at TIMESTAMP NULL,
  expires_at TIMESTAMP NULL,
  FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
  INDEX idx_user_notifications (user_id, created_at DESC),
  INDEX idx_user_unread (user_id, is_read, expires_at)
);
```

**Implementation Notes**:
- Order by `created_at DESC` (newest first)
- `total`: Count of all matching notifications (for pagination)
- `unread_count`: Total unread (ignoring filters, for badge count)
- `has_more`: `offset + limit < total`
- Exclude expired notifications from unread count: `WHERE is_read = false AND (expires_at IS NULL OR expires_at > NOW())`

---

### 2.2 Get Unread Count

**Endpoint**: `GET /api/notifications/unread-count`

**Purpose**: Lightweight endpoint for badge/counter display

**Success Response** (200 OK):
```json
{
  "message": "UNREAD_COUNT_RETRIEVED",
  "data": {
    "unread_count": 12
  }
}
```

**Implementation**:
```sql
SELECT COUNT(*) FROM notifications
WHERE user_id = ?
  AND is_read = FALSE
  AND (expires_at IS NULL OR expires_at > NOW())
```

---

### 2.3 Mark Notification as Read

**Endpoint**: `PUT /api/notifications/{notificationId}`

**Purpose**: Mark specific notification as read

**Path Parameters**:
- `notificationId`: Notification ID to mark as read

**Success Response** (200 OK):
```json
{
  "message": "NOTIFICATION_MARKED_READ_SUCCESS",
  "data": {
    "notification": {
      "id": "notif_123",
      "is_read": true,
      "read_at": "2025-10-20T10:05:00.000000+00:00"
      // ... other notification fields
    }
  }
}
```

**Error Responses**:
- `404 Not Found`:
  - `NOTIFICATION_NOT_FOUND`: Notification doesn't exist or doesn't belong to user

**Implementation**:
```sql
UPDATE notifications
SET is_read = TRUE, read_at = NOW()
WHERE id = ? AND user_id = ?
```

**Notes**:
- Must verify notification belongs to authenticated user
- If already read, update `read_at` to current time (idempotent)

---

### 2.4 Mark All as Read

**Endpoint**: `PUT /api/notifications/read-all`

**Purpose**: Mark all user's notifications as read

**Success Response** (200 OK):
```json
{
  "message": "NOTIFICATIONS_MARKED_READ_SUCCESS",
  "data": {
    "updated_count": 12
  }
}
```

**Implementation**:
```sql
UPDATE notifications
SET is_read = TRUE, read_at = NOW()
WHERE user_id = ? AND is_read = FALSE
RETURNING COUNT(*)
```

---

### 2.5 Delete Notification

**Endpoint**: `DELETE /api/notifications/{notificationId}`

**Purpose**: Delete specific notification from inbox

**Path Parameters**:
- `notificationId`: Notification ID to delete

**Success Response** (200 OK):
```json
{
  "message": "NOTIFICATION_DELETED_SUCCESS"
}
```

**Error Responses**:
- `404 Not Found`:
  - `NOTIFICATION_NOT_FOUND`: Notification doesn't exist or doesn't belong to user

**Implementation**:
```sql
DELETE FROM notifications
WHERE id = ? AND user_id = ?
```

---

### 2.6 Clear All Notifications

**Endpoint**: `DELETE /api/notifications`

**Purpose**: Delete all user's notifications (nuclear option)

**Success Response** (200 OK):
```json
{
  "message": "NOTIFICATIONS_CLEARED_SUCCESS"
}
```

**Implementation**:
```sql
DELETE FROM notifications WHERE user_id = ?
```

---

## 🔔 3. Creating Notifications (Server-Side)

Notifications are **created by the backend** when events occur, not via API POST from clients.

### When to Create Notifications

| Event | Notification Type | Trigger | Recipients |
|-------|------------------|---------|------------|
| User sends room invitation | `room_invitation` | POST /api/multiplayer/rooms/{id}/invitations | Recipient user(s) |
| User accepts invitation | `invitation_accepted` | POST /api/multiplayer/invitations/{id}/accept | Sender user |
| User declines invitation | `invitation_declined` | POST /api/multiplayer/invitations/{id}/decline | Sender user |
| Invitation expires | `invitation_expired` | Cron job (15 min after creation) | Recipient user |
| Friend comes online | `friend_online` | WebSocket connection | All friends |
| Room starts | `room_started` | POST /api/multiplayer/rooms/{id}/start | All room players |
| Friend joins room | `friend_joined_room` | User joins multiplayer room | All friends |

### Notification Creation Pattern

```python
def create_notification(user_id, notification_type, title, body, data, expires_at=None):
    """
    Create notification and send push notification

    Args:
        user_id: User to notify
        notification_type: One of the valid types
        title: Localized notification title
        body: Localized notification body
        data: Type-specific data payload (dict)
        expires_at: Optional expiration timestamp
    """
    # 1. Insert into database
    notification = db.notifications.insert({
        'id': generate_id('notif_'),
        'user_id': user_id,
        'type': notification_type,
        'title': title,
        'body': body,
        'data': json.dumps(data),
        'created_at': datetime.now(),
        'is_read': False,
        'expires_at': expires_at
    })

    # 2. Send push notification via FCM
    devices = db.devices.find({'user_id': user_id})
    for device in devices:
        send_fcm_notification(
            device['device_token'],
            title=title,
            body=body,
            data={**data, 'notification_id': notification['id']}
        )

    # 3. Emit WebSocket event (if user online)
    emit_websocket('/multiplayer', 'notification_received', {
        'notification': notification
    }, to=user_id)

    return notification
```

### Example: Room Invitation

```python
@app.route('/api/multiplayer/rooms/<room_id>/invitations', methods=['POST'])
def send_room_invitation(room_id):
    sender_id = get_current_user_id()
    recipient_id = request.json['recipient_user_id']

    # Create invitation
    invitation = create_invitation(room_id, sender_id, recipient_id)

    # Get room and sender info
    room = db.rooms.find_one({'id': room_id})
    sender = db.users.find_one({'id': sender_id})

    # Create notification
    create_notification(
        user_id=recipient_id,
        notification_type='room_invitation',
        title=f"New Game Invitation",
        body=f"{sender['display_name']} invited you to play {room['game_name']}",
        data={
            'invitation_id': invitation['id'],
            'room_id': room_id,
            'room_code': room['code'],
            'game_id': room['game_id'],
            'sender_user_id': sender_id,
            'sender_display_name': sender['display_name']
        },
        expires_at=invitation['expires_at']
    )

    return jsonify({'message': 'INVITATION_SENT_SUCCESS', 'data': {'invitation': invitation}})
```

---

## 📊 4. Notification Data Payloads by Type

Each notification type has a specific data structure. These are stored in the `data` JSONB column.

### 4.1 `room_invitation`
```json
{
  "invitation_id": "inv_123",
  "room_id": "room_456",
  "room_code": "ABC123",
  "game_id": "tic_tac_toe",
  "sender_user_id": "user_789",
  "sender_display_name": "Alice"
}
```

### 4.2 `friend_request`
```json
{
  "request_id": "req_123",
  "requester_user_id": "user_789",
  "requester_display_name": "Alice"
}
```

### 4.3 `friend_online`
```json
{
  "friend_user_id": "user_789",
  "friend_display_name": "Alice"
}
```

### 4.4 `room_started`
```json
{
  "room_id": "room_456",
  "game_id": "tic_tac_toe"
}
```

### 4.5 `friend_joined_room`
```json
{
  "friend_user_id": "user_789",
  "friend_display_name": "Alice",
  "room_id": "room_456",
  "room_code": "ABC123"
}
```

### 4.6 `invitation_accepted`
```json
{
  "invitation_id": "inv_123",
  "accepted_by_user_id": "user_789",
  "accepted_by_display_name": "Alice",
  "room_id": "room_456"
}
```

### 4.7 `invitation_declined`
```json
{
  "invitation_id": "inv_123",
  "declined_by_user_id": "user_789",
  "declined_by_display_name": "Alice"
}
```

### 4.8 `invitation_expired`
```json
{
  "invitation_id": "inv_123",
  "room_id": "room_456"
}
```

---

## 🔥 5. Firebase Cloud Messaging Integration

### Backend FCM Setup

1. **Install Firebase Admin SDK**:
```bash
pip install firebase-admin
```

2. **Initialize Firebase** (Python example):
```python
import firebase_admin
from firebase_admin import credentials, messaging

# Initialize with service account
cred = credentials.Certificate('path/to/serviceAccountKey.json')
firebase_admin.initialize_app(cred)
```

3. **Send FCM Notification**:
```python
def send_fcm_notification(device_token, title, body, data):
    """Send push notification via FCM"""
    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body
        ),
        data=data,  # Custom data payload
        token=device_token
    )

    try:
        response = messaging.send(message)
        logger.info(f'FCM sent successfully: {response}')
        return True
    except messaging.UnregisteredError:
        # Token invalid, remove from database
        db.devices.delete({'device_token': device_token})
        logger.warning(f'Removed invalid FCM token: {device_token}')
        return False
    except Exception as e:
        logger.error(f'FCM send failed: {e}')
        return False
```

### Platform-Specific Considerations

**Android**:
- Supports background notifications out of the box
- Data payload max size: 4KB

**iOS**:
- Requires explicit user permission
- APNS-specific fields can be added via `apns` config

---

## 🧪 6. Testing Checklist

### Manual Testing

- [ ] Register device (Android)
- [ ] Register device (iOS)
- [ ] Unregister device
- [ ] Send test push notification
- [ ] Receive notification when app is:
  - [ ] Foreground
  - [ ] Background
  - [ ] Terminated
- [ ] Tap notification → Navigate to correct screen
- [ ] Fetch notifications (inbox)
- [ ] Mark notification as read
- [ ] Mark all as read
- [ ] Delete notification
- [ ] Clear all notifications
- [ ] Verify pagination works
- [ ] Verify filters (read/unread, type)
- [ ] Verify expiration logic
- [ ] Verify offline support (app uses local cache)

### API Testing (Postman/cURL)

```bash
# Register device
curl -X POST https://api.goodplay.com/api/devices/register \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "device_token": "test_fcm_token_123",
    "platform": "android"
  }'

# Get notifications
curl -X GET "https://api.goodplay.com/api/notifications?limit=10&offset=0&read=false" \
  -H "Authorization: Bearer $TOKEN"

# Mark as read
curl -X PUT https://api.goodplay.com/api/notifications/notif_123 \
  -H "Authorization: Bearer $TOKEN"

# Delete notification
curl -X DELETE https://api.goodplay.com/api/notifications/notif_123 \
  -H "Authorization: Bearer $TOKEN"
```

---

## 📝 7. Response Constants

All response messages should use these constants for consistency.

### Device Management
```python
DEVICE_REGISTERED_SUCCESS = "Device registered successfully"
DEVICE_UNREGISTERED_SUCCESS = "Device unregistered successfully"
DEVICE_TOKEN_REQUIRED = "Device token is required"
DEVICE_TOKEN_OR_ID_REQUIRED = "Device token or device ID is required"
PLATFORM_INVALID = "Platform must be 'android' or 'ios'"
DEVICE_REGISTRATION_FAILED = "Failed to register device"
```

### Notifications
```python
NOTIFICATIONS_RETRIEVED_SUCCESS = "Notifications retrieved successfully"
UNREAD_COUNT_RETRIEVED = "Unread count retrieved successfully"
NOTIFICATION_MARKED_READ_SUCCESS = "Notification marked as read"
NOTIFICATIONS_MARKED_READ_SUCCESS = "All notifications marked as read"
NOTIFICATION_DELETED_SUCCESS = "Notification deleted successfully"
NOTIFICATIONS_CLEARED_SUCCESS = "All notifications cleared"
NOTIFICATION_NOT_FOUND = "Notification not found"
NOTIFICATION_UPDATE_FAILED = "Failed to update notification"
NOTIFICATION_DELETE_FAILED = "Failed to delete notification"
INVALID_NOTIFICATION_TYPE = "Invalid notification type"
```

---

## 🚀 8. Deployment Checklist

- [ ] Database tables created (`devices`, `notifications`)
- [ ] Database indexes created for performance
- [ ] Firebase Admin SDK initialized with service account
- [ ] Environment variables set (Firebase credentials)
- [ ] Rate limiting configured (10 req/min for device registration)
- [ ] Cron job for expiring notifications (every 5 minutes)
- [ ] Monitoring/logging for FCM failures
- [ ] Backup strategy for notifications table
- [ ] API endpoints documented in Swagger/Postman
- [ ] Integration tests passing
- [ ] Load testing completed (100+ concurrent users)

---

## 📞 9. Support & Questions

**Flutter Implementation**: ✅ **COMPLETE** and ready to integrate

**Backend Team Contact**: [Your contact info here]

**OpenAPI Spec**: `docs/openapi/notifications.yaml`

**Questions**:
- How to handle notification localization? (Backend or client?)
- Retention policy for old notifications? (Default: 30 days)
- FCM quota limits and error handling strategy
- Notification priority levels (low/default/high)?

---

**Last Updated**: 2025-10-20
**Version**: 1.0.0
**Status**: Ready for Backend Implementation
