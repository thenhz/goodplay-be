# GOO-60 Frontend Integration Guide
## Multiplayer Invitations & Real-time Notifications

**For:** Frontend Developers
**API Version:** 1.0.0
**Last Updated:** 2025-10-07

---

## 🚀 Quick Start

### **Step 1: Connect to WebSocket**
```typescript
import io from 'socket.io-client';

const socket = io('http://localhost:5000/multiplayer', {
  auth: {
    token: accessToken  // Your JWT token
  }
});

// Authenticate
socket.emit('authenticate', {
  token: accessToken,
  device_info: {
    platform: 'web',        // 'ios' | 'android' | 'web'
    device_type: 'desktop', // 'mobile' | 'tablet' | 'desktop'
    app_version: '1.0.0'
  }
});

socket.on('authenticated', (data) => {
  console.log('WebSocket authenticated:', data);
});
```

### **Step 2: Listen for Invitation Events**
```typescript
// New invitation received
socket.on('invitation_received', (data) => {
  console.log('New invitation:', data.invitation);

  // Show notification to user
  showNotification({
    title: 'New Game Invitation!',
    message: `Join ${data.invitation.game_name}`,
    roomCode: data.invitation.room_code,
    expiresIn: calculateTimeRemaining(data.invitation.expires_at)
  });
});

// Your invitation was accepted
socket.on('invitation_accepted', (data) => {
  console.log('Invitation accepted:', data.invitation);

  showNotification({
    title: 'Invitation Accepted!',
    message: `Player joined your room`,
    roomId: data.invitation.room_id
  });
});

// Your invitation was declined
socket.on('invitation_declined', (data) => {
  console.log('Invitation declined:', data.invitation);

  showNotification({
    title: 'Invitation Declined',
    message: 'Player declined your invitation'
  });
});

// Invitation expired
socket.on('invitation_expired', (data) => {
  console.log('Invitation expired:', data.invitation_id);

  // Remove from UI
  removeInvitationFromList(data.invitation_id);
});

// Friend joined a room
socket.on('friend_joined_room', (data) => {
  console.log('Friend joined room:', data.friend, data.room);

  showNotification({
    title: 'Friend Online!',
    message: `${data.friend.display_name} is playing ${data.room.game_id}`,
    action: 'Join Room',
    roomCode: data.room.room_code
  });
});
```

### **Step 3: Send Invitations**
```typescript
// Send single invitation
async function sendInvitation(roomId: string, recipientUserId: string) {
  const response = await fetch(`/api/multiplayer/rooms/${roomId}/invitations`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ recipient_user_id: recipientUserId })
  });

  const result = await response.json();

  if (response.ok) {
    console.log('Invitation sent:', result.data.invitation);
    return result.data.invitation;
  } else {
    handleInvitationError(result.message);
  }
}

// Send batch invitations
async function sendBatchInvitations(roomId: string, recipientIds: string[]) {
  const response = await fetch(`/api/multiplayer/rooms/${roomId}/invitations`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ recipient_ids: recipientIds })
  });

  const result = await response.json();

  if (response.ok) {
    console.log(`Sent ${result.data.sent_count} invitations`);
    console.log(`Failed ${result.data.failed_count} invitations`);

    // Show results to user
    showBatchInvitationResults(result.data);
    return result.data;
  } else {
    handleInvitationError(result.message);
  }
}
```

---

## 📡 WebSocket Events Reference

### **Events You Listen To:**

#### `invitation_received`
When a player receives a new invitation.

**Payload:**
```typescript
{
  invitation: {
    invitation_id: string;
    room_id: string;
    room_code: string;        // "ABC123"
    game_id: string;          // "memory_game"
    game_name: string;        // "Memory Game"
    sender_user_id: string;
    expires_at: string;       // ISO 8601 timestamp
  };
  message: "NEW_INVITATION_RECEIVED";
  timestamp: string;
}
```

**Action:** Show notification, add to invitations list

---

#### `invitation_accepted`
When someone accepts your invitation.

**Payload:**
```typescript
{
  invitation: {
    invitation_id: string;
    room_id: string;
    accepted_by: string;      // User ID
  };
  message: "INVITATION_WAS_ACCEPTED";
  timestamp: string;
}
```

**Action:** Show success notification, maybe navigate to room

---

#### `invitation_declined`
When someone declines your invitation.

**Payload:**
```typescript
{
  invitation: {
    invitation_id: string;
    declined_by: string;      // User ID
  };
  message: "INVITATION_WAS_DECLINED";
  timestamp: string;
}
```

**Action:** Remove from pending list, show notification

---

#### `invitation_expired`
When an invitation expires (15 minutes after sending).

**Payload:**
```typescript
{
  invitation_id: string;
  message: "INVITATION_EXPIRED";
  timestamp: string;
}
```

**Action:** Remove from invitations list

---

#### `friend_joined_room`
When a friend joins a multiplayer room.

**Payload:**
```typescript
{
  friend: {
    user_id: string;
    display_name: string;
  };
  room: {
    room_id: string;
    room_code: string;
    game_id: string;
  };
  message: "FRIEND_JOINED_ROOM";
  timestamp: string;
}
```

**Action:** Show "Join Friend" prompt

---

## 🔗 REST API Endpoints

### **1. Send Invitation(s)**

**Endpoint:** `POST /api/multiplayer/rooms/{roomId}/invitations`

**Single Invitation:**
```typescript
POST /api/multiplayer/rooms/room_123/invitations
Authorization: Bearer <token>
Content-Type: application/json

{
  "recipient_user_id": "user456"
}

// Response (200 OK)
{
  "message": "INVITATION_SENT_SUCCESS",
  "data": {
    "invitation": {
      "invitation_id": "inv_789",
      "room_id": "room_123",
      "room_code": "ABC123",
      "game_id": "memory_game",
      "game_name": "Memory Game",
      "sender_user_id": "user123",
      "recipient_user_id": "user456",
      "status": "pending",
      "created_at": "2025-10-07T10:00:00.000000+00:00",
      "expires_at": "2025-10-07T10:15:00.000000+00:00"
    }
  }
}
```

**Batch Invitation:**
```typescript
POST /api/multiplayer/rooms/room_123/invitations
Authorization: Bearer <token>
Content-Type: application/json

{
  "recipient_ids": ["user1", "user2", "user3"]
}

// Response (200 OK)
{
  "message": "BATCH_INVITATIONS_SENT",
  "data": {
    "sent": [
      { "recipient_id": "user1", "invitation_id": "inv_1" },
      { "recipient_id": "user3", "invitation_id": "inv_3" }
    ],
    "failed": [
      { "recipient_id": "user2", "reason": "USER_BLOCKED" }
    ],
    "sent_count": 2,
    "failed_count": 1,
    "total_requested": 3
  }
}
```

**Error Responses:**
- `400` - `USER_BLOCKED`, `ROOM_FULL`, `ALREADY_IN_ROOM`, `TOO_MANY_RECIPIENTS` (>10)
- `429` - `RATE_LIMIT_EXCEEDED` (max 10 invitations per minute)

---

### **2. Get My Invitations**

**Endpoint:** `GET /api/multiplayer/invitations?include_expired=false`

```typescript
GET /api/multiplayer/invitations?include_expired=false
Authorization: Bearer <token>

// Response (200 OK)
{
  "message": "INVITATIONS_RETRIEVED_SUCCESS",
  "data": {
    "invitations": [
      {
        "invitation_id": "inv_123",
        "room_id": "room_456",
        "room_code": "ABC123",
        "game_id": "memory_game",
        "game_name": "Memory Game",
        "sender_user_id": "user_sender",
        "recipient_user_id": "user_me",
        "status": "pending",
        "created_at": "2025-10-07T10:00:00.000000+00:00",
        "expires_at": "2025-10-07T10:15:00.000000+00:00"
      }
    ],
    "count": 1
  }
}
```

---

### **3. Accept Invitation**

**Endpoint:** `POST /api/multiplayer/invitations/{invitationId}/accept`

```typescript
POST /api/multiplayer/invitations/inv_123/accept
Authorization: Bearer <token>

// Response (200 OK)
{
  "message": "INVITATION_ACCEPTED_SUCCESS",
  "data": {
    "room_id": "room_456"  // Join this room
  }
}

// After accepting, join the room:
POST /api/multiplayer/rooms/room_456/join
```

**Error Responses:**
- `400` - `INVITATION_NOT_FOUND`, `INVITATION_EXPIRED`, `ROOM_FULL`, `ROOM_NOT_ACCEPTING_PLAYERS`

---

### **4. Decline Invitation**

**Endpoint:** `POST /api/multiplayer/invitations/{invitationId}/decline`

```typescript
POST /api/multiplayer/invitations/inv_123/decline
Authorization: Bearer <token>

// Response (200 OK)
{
  "message": "INVITATION_DECLINED_SUCCESS"
}
```

---

### **5. Cancel Invitation (Sender Only)**

**Endpoint:** `DELETE /api/multiplayer/invitations/{invitationId}`

```typescript
DELETE /api/multiplayer/invitations/inv_123
Authorization: Bearer <token>

// Response (200 OK)
{
  "message": "INVITATION_CANCELLED_SUCCESS"
}
```

**Error Responses:**
- `400` - `INVITATION_NOT_FOUND`, `NOT_INVITATION_SENDER`, `INVITATION_ALREADY_PROCESSED`

---

## 👥 Social Integration Endpoints

### **1. Get Online Friends**

**Endpoint:** `GET /api/social/friends/online`

```typescript
GET /api/social/friends/online
Authorization: Bearer <token>

// Response (200 OK)
{
  "message": "ONLINE_FRIENDS_RETRIEVED",
  "data": {
    "friends": [
      {
        "user_id": "user1",
        "display_name": "Alice",
        "first_name": "Alice",
        "last_name": "Smith",
        "is_in_room": true,
        "room_id": "room_123"
      },
      {
        "user_id": "user2",
        "display_name": "Bob",
        "first_name": "Bob",
        "last_name": "Jones",
        "is_in_room": false,
        "room_id": null
      }
    ],
    "count": 2
  }
}
```

**UI Integration:**
```typescript
// Show "Join Friend" button for friends in rooms
friends.forEach(friend => {
  if (friend.is_in_room) {
    showJoinFriendButton(friend, friend.room_id);
  }
});
```

---

### **2. Get Friend's Current Room**

**Endpoint:** `GET /api/social/friends/{friendId}/current-room`

```typescript
GET /api/social/friends/user1/current-room
Authorization: Bearer <token>

// Response (200 OK) - Friend in room
{
  "message": "FRIEND_ROOM_RETRIEVED",
  "data": {
    "in_room": true,
    "room": {
      "room_id": "room_123",
      "room_code": "ABC123",
      "game_id": "memory_game",
      "max_players": 8,
      "current_players": 3,
      "status": "waiting"
    },
    "is_joinable": true,
    "reason": null
  }
}

// Response (200 OK) - Friend not in room
{
  "message": "FRIEND_NOT_IN_ROOM",
  "data": {
    "in_room": false
  }
}

// Response (200 OK) - Friend in room but not joinable
{
  "message": "FRIEND_ROOM_RETRIEVED",
  "data": {
    "in_room": true,
    "room": { ... },
    "is_joinable": false,
    "reason": "ROOM_FULL"  // or "ROOM_NOT_ACCEPTING_PLAYERS" or "ALREADY_IN_ROOM"
  }
}
```

**UI Integration:**
```typescript
const friendRoomData = await getFriendCurrentRoom(friendId);

if (friendRoomData.in_room && friendRoomData.is_joinable) {
  showJoinButton(friendRoomData.room);
} else if (friendRoomData.in_room && !friendRoomData.is_joinable) {
  showDisabledJoinButton(friendRoomData.reason);
}
```

---

### **3. Invite Friend to Your Room**

**Endpoint:** `POST /api/social/friends/{friendId}/invite-to-room`

```typescript
// Option 1: Specify room ID
POST /api/social/friends/user1/invite-to-room
Authorization: Bearer <token>
Content-Type: application/json

{
  "room_id": "room_123"
}

// Option 2: Use your current room (no body needed)
POST /api/social/friends/user1/invite-to-room
Authorization: Bearer <token>

// Response (200 OK)
{
  "message": "INVITATION_SENT_SUCCESS",
  "data": {
    "invitation": {
      "invitation_id": "inv_456",
      "room_id": "room_123",
      "room_code": "ABC123",
      "game_id": "memory_game",
      "sender_user_id": "user_me",
      "recipient_user_id": "user1",
      "status": "pending",
      "expires_at": "2025-10-07T10:15:00.000000+00:00"
    }
  }
}
```

**Error Responses:**
- `400` - `NOT_IN_ANY_ROOM` (if no room_id provided and not in a room)

**UI Integration:**
```typescript
// Quick invite button in friends list
<button onClick={() => inviteFriendToCurrentRoom(friend.user_id)}>
  Invite to Game
</button>

async function inviteFriendToCurrentRoom(friendId: string) {
  try {
    const result = await fetch(`/api/social/friends/${friendId}/invite-to-room`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json'
      }
    });

    if (result.ok) {
      showToast('Invitation sent!');
    }
  } catch (error) {
    showError('Failed to send invitation');
  }
}
```

---

## ⏱️ Timing & Expiry

### **Invitation Expiry:**
- Invitations expire **15 minutes** after creation
- `expires_at` field shows exact expiry time (ISO 8601)
- Frontend should show countdown timer
- `invitation_expired` WebSocket event is emitted when expired

**UI Timer Example:**
```typescript
function showExpiryCountdown(expiresAt: string) {
  const expiryTime = new Date(expiresAt);
  const now = new Date();
  const remainingMs = expiryTime.getTime() - now.getTime();
  const remainingMinutes = Math.floor(remainingMs / 60000);
  const remainingSeconds = Math.floor((remainingMs % 60000) / 1000);

  return `${remainingMinutes}:${remainingSeconds.toString().padStart(2, '0')}`;
}
```

### **Rate Limiting:**
- Maximum **10 invitations per minute** per user
- Backend returns `429 RATE_LIMIT_EXCEEDED` when exceeded
- Frontend should show cooldown timer

**UI Rate Limit Handling:**
```typescript
let lastRateLimitTime: Date | null = null;
let invitationsSentThisMinute = 0;

async function sendInvitation(roomId: string, recipientId: string) {
  // Client-side rate limit check
  if (invitationsSentThisMinute >= 10) {
    const timeSinceLastReset = Date.now() - (lastRateLimitTime?.getTime() || 0);
    if (timeSinceLastReset < 60000) {
      showError(`Rate limit: wait ${Math.ceil((60000 - timeSinceLastReset) / 1000)}s`);
      return;
    } else {
      // Reset counter
      invitationsSentThisMinute = 0;
      lastRateLimitTime = null;
    }
  }

  const response = await fetch(`/api/multiplayer/rooms/${roomId}/invitations`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ recipient_user_id: recipientId })
  });

  if (response.status === 429) {
    showError('Too many invitations. Please wait 1 minute.');
    lastRateLimitTime = new Date();
    invitationsSentThisMinute = 10;
  } else if (response.ok) {
    invitationsSentThisMinute++;
    if (invitationsSentThisMinute === 1) {
      lastRateLimitTime = new Date();
    }
  }
}
```

---

## 🎨 UI/UX Recommendations

### **1. Invitations List Screen**
```
┌─────────────────────────────────────┐
│ 📩 Invitations (2)                  │
├─────────────────────────────────────┤
│                                     │
│ 🎮 Memory Game - ABC123             │
│ From: Alice                         │
│ Expires in: 12:34                   │
│ [Accept] [Decline]                  │
│                                     │
│ 🎯 Trivia Quest - XYZ789            │
│ From: Bob                           │
│ Expires in: 08:15                   │
│ [Accept] [Decline]                  │
│                                     │
└─────────────────────────────────────┘
```

### **2. Friends List with Multiplayer Status**
```
┌─────────────────────────────────────┐
│ 👥 Friends (5)                      │
├─────────────────────────────────────┤
│                                     │
│ 🟢 Alice ─ Playing Memory Game      │
│            [Join Room]              │
│                                     │
│ 🟢 Bob ─ Online                     │
│          [Invite to Game]           │
│                                     │
│ ⚫ Charlie ─ Offline                │
│                                     │
└─────────────────────────────────────┘
```

### **3. In-Game Invitation Flow**
```
Step 1: Player clicks "Invite Friends" button
Step 2: Show friends list with checkboxes (max 10)
Step 3: Click "Send Invitations"
Step 4: Show results:
        ✅ Sent to Alice
        ✅ Sent to Bob
        ❌ Charlie is blocked
        ❌ Dave is already in room
```

### **4. Toast Notifications**
```typescript
// Invitation received
showToast({
  type: 'info',
  title: 'New Invitation!',
  message: 'Alice invited you to Memory Game',
  actions: [
    { label: 'Join', onClick: () => acceptInvitation(invId) },
    { label: 'Decline', onClick: () => declineInvitation(invId) }
  ],
  duration: 15000  // Auto-dismiss after 15s
});

// Invitation accepted
showToast({
  type: 'success',
  message: 'Bob joined your room!',
  duration: 3000
});

// Invitation expired
showToast({
  type: 'warning',
  message: 'Invitation from Alice expired',
  duration: 3000
});
```

---

## 🚨 Error Handling

### **Common Error Messages:**
```typescript
const ERROR_MESSAGES = {
  // Invitation errors
  ROOM_NOT_FOUND: 'Room no longer exists',
  ROOM_FULL: 'Room is full',
  ROOM_NOT_ACCEPTING_PLAYERS: 'Game has already started',
  USER_BLOCKED: 'Cannot invite blocked users',
  ALREADY_IN_ROOM: 'User is already in the room',
  INVITATION_ALREADY_SENT: 'Invitation already sent to this user',
  INVITATION_EXPIRED: 'This invitation has expired',
  INVITATION_NOT_FOUND: 'Invitation not found',
  NOT_IN_ROOM: 'You must be in the room to send invitations',
  NOT_IN_ANY_ROOM: 'You are not currently in a game',

  // Rate limiting
  RATE_LIMIT_EXCEEDED: 'Too many invitations. Please wait 1 minute.',
  TOO_MANY_RECIPIENTS: 'Maximum 10 users per invitation batch',

  // Authorization
  NOT_INVITATION_SENDER: 'Only the sender can cancel this invitation',
  NOT_INVITATION_RECIPIENT: 'This invitation is not for you'
};

function handleInvitationError(errorCode: string) {
  const message = ERROR_MESSAGES[errorCode] || 'An error occurred';
  showError(message);
}
```

---

## 📱 Mobile Considerations

### **Push Notifications:**
When app is in background:
```typescript
// Register for push notifications
if ('Notification' in window && Notification.permission === 'granted') {
  // Backend can send push via FCM/APNs
  // Use invitation_id to link push to WebSocket event
}
```

### **Reconnection Handling:**
When app comes back from background:
```typescript
socket.on('reconnect', async () => {
  // Fetch missed invitations
  const invitations = await fetch('/api/multiplayer/invitations');

  // Update UI with any new invitations received while offline
  updateInvitationsList(invitations.data.invitations);
});
```

---

## 🔧 Debugging

### **Enable Debug Logging:**
```typescript
const socket = io('http://localhost:5000/multiplayer', {
  auth: { token: accessToken },
  reconnection: true,
  reconnectionDelay: 1000,
  reconnectionAttempts: 5,
  transports: ['websocket'],
  debug: true  // Enable debug mode
});

socket.on('connect', () => console.log('✅ WebSocket connected'));
socket.on('disconnect', () => console.log('❌ WebSocket disconnected'));
socket.on('connect_error', (error) => console.error('Connection error:', error));
```

### **Test WebSocket Events:**
```typescript
// Manually trigger events for testing
socket.emit('authenticate', {
  token: 'your_test_token',
  device_info: { platform: 'web', device_type: 'desktop', app_version: '1.0.0' }
});

// Listen to all events
socket.onAny((eventName, ...args) => {
  console.log(`Event: ${eventName}`, args);
});
```

---

## 📚 Complete Code Example

```typescript
// invitation-manager.ts
import io from 'socket.io-client';

class InvitationManager {
  private socket: Socket;
  private accessToken: string;

  constructor(accessToken: string, baseUrl: string = 'http://localhost:5000') {
    this.accessToken = accessToken;
    this.socket = io(`${baseUrl}/multiplayer`, {
      auth: { token: accessToken }
    });

    this.setupEventListeners();
  }

  private setupEventListeners() {
    this.socket.on('authenticated', (data) => {
      console.log('WebSocket authenticated:', data);
    });

    this.socket.on('invitation_received', (data) => {
      this.handleInvitationReceived(data);
    });

    this.socket.on('invitation_accepted', (data) => {
      this.handleInvitationAccepted(data);
    });

    this.socket.on('invitation_declined', (data) => {
      this.handleInvitationDeclined(data);
    });

    this.socket.on('invitation_expired', (data) => {
      this.handleInvitationExpired(data);
    });

    this.socket.on('friend_joined_room', (data) => {
      this.handleFriendJoinedRoom(data);
    });
  }

  private handleInvitationReceived(data: any) {
    // Show notification
    this.showNotification({
      title: 'New Invitation!',
      message: `Join ${data.invitation.game_name}`,
      actions: [
        { label: 'Accept', onClick: () => this.acceptInvitation(data.invitation.invitation_id) },
        { label: 'Decline', onClick: () => this.declineInvitation(data.invitation.invitation_id) }
      ]
    });

    // Update UI
    this.addInvitationToList(data.invitation);
  }

  async sendInvitation(roomId: string, recipientId: string) {
    const response = await fetch(`/api/multiplayer/rooms/${roomId}/invitations`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.accessToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ recipient_user_id: recipientId })
    });

    return await response.json();
  }

  async acceptInvitation(invitationId: string) {
    const response = await fetch(`/api/multiplayer/invitations/${invitationId}/accept`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.accessToken}`
      }
    });

    const result = await response.json();

    if (response.ok) {
      // Join the room
      await this.joinRoom(result.data.room_id);
    }

    return result;
  }

  async getOnlineFriends() {
    const response = await fetch('/api/social/friends/online', {
      headers: {
        'Authorization': `Bearer ${this.accessToken}`
      }
    });

    return await response.json();
  }

  // ... more methods
}

export default InvitationManager;
```

---

## 🎯 Summary

**Key Points:**
1. Connect to `/multiplayer` WebSocket namespace on app start
2. Listen to 5 real-time events (invitation_received, accepted, declined, expired, friend_joined_room)
3. Use REST endpoints for sending invitations and managing them
4. Handle 15-minute expiry with countdown timers
5. Respect rate limiting (10 invitations/minute)
6. Integrate with social endpoints for online friends
7. Show friendly error messages using constants

**Full API Documentation:** `docs/openapi/goo-60-multiplayer-invitations.yaml`

**Questions?** Check `docs/GOO-60_IMPLEMENTATION_SUMMARY.md` for technical details.

---

**Happy Coding! 🚀**
