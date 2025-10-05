# Multiplayer WebSocket API Documentation

## Overview
This document describes the WebSocket API for GoodPlay multiplayer functionality implemented in GOO-54.

**WebSocket Endpoint**: `ws://your-host/multiplayer`  
**Technology**: Flask-SocketIO 5.5.1 (threading mode)

## Authentication

All WebSocket events (except `ping`) require JWT authentication via the `token` field in the event data.

### Token Format
Include your JWT access token in every authenticated event:
```json
{
  "token": "your_jwt_access_token",
  ... other fields ...
}
```

## WebSocket Events

### Connection Events

#### `connect`
Emitted automatically when WebSocket connection is established.

**Server Response**: Connection accepted/rejected

---

#### `disconnect`
Emitted automatically when WebSocket connection is closed.

**Server Action**: Cleanup sessions and rooms

---

### Ping/Pong

#### `ping`
Client sends ping for latency measurement.

**Client Payload**:
```json
{
  "timestamp": 1696512345678
}
```

**Server Response** (`pong`):
```json
{
  "timestamp": 1696512345678,
  "server_time": 1696512345680
}
```

---

### Authentication

#### `authenticate`
Authenticate WebSocket connection with JWT token.

**Client Payload**:
```json
{
  "token": "your_jwt_token",
  "device_info": {
    "platform": "ios|android|web",
    "device_type": "mobile|tablet|desktop",
    "app_version": "1.0.0"
  }
}
```

**Server Response** (`authenticated`):
```json
{
  "user_id": "user_123",
  "session_id": "socket_session_id",
  "message": "WEBSOCKET_AUTH_SUCCESS",
  "timestamp": "2025-10-05T10:30:00.123456+00:00"
}
```

**Error Response** (`error`):
```json
{
  "message": "AUTHENTICATION_REQUIRED|INVALID_TOKEN|TOKEN_EXPIRED"
}
```

---

### Room Management

#### `join_room`
Join a multiplayer game room.

**Client Payload**:
```json
{
  "token": "your_jwt_token",
  "room_id": "room_123"
}
```

**Server Response** (`room_joined`):
```json
{
  "room_id": "room_123",
  "message": "ROOM_JOINED_SUCCESS",
  "timestamp": "2025-10-05T10:30:00.123456+00:00"
}
```

**Broadcast to Room** (`player_joined`):
```json
{
  "user_id": "user_456",
  "room_id": "room_123",
  "message": "PLAYER_JOINED",
  "timestamp": "2025-10-05T10:30:00.123456+00:00"
}
```

---

#### `leave_room`
Leave a multiplayer game room.

**Client Payload**:
```json
{
  "token": "your_jwt_token",
  "room_id": "room_123"
}
```

**Server Response** (`room_left`):
```json
{
  "room_id": "room_123",
  "message": "ROOM_LEFT_SUCCESS",
  "timestamp": "2025-10-05T10:30:00.123456+00:00"
}
```

**Broadcast to Room** (`player_left`):
```json
{
  "user_id": "user_456",
  "room_id": "room_123",
  "message": "PLAYER_LEFT",
  "timestamp": "2025-10-05T10:30:00.123456+00:00"
}
```

---

### Game Actions

#### `game_action`
Send a game action to other players in the room.

**Client Payload**:
```json
{
  "token": "your_jwt_token",
  "room_id": "room_123",
  "action": "move|jump|shoot|...",
  "payload": {
    "x": 10,
    "y": 20,
    ... custom action data ...
  }
}
```

**Broadcast to Room** (`game_action`):
```json
{
  "user_id": "user_456",
  "action": "move",
  "payload": {
    "x": 10,
    "y": 20
  },
  "timestamp": "2025-10-05T10:30:00.123456+00:00"
}
```

---

#### `update_state`
Update player state and broadcast to room.

**Client Payload**:
```json
{
  "token": "your_jwt_token",
  "room_id": "room_123",
  "state": {
    "score": 100,
    "level": 5,
    "position": {"x": 50, "y": 60},
    ... custom state data ...
  }
}
```

**Broadcast to Room** (`state_updated`):
```json
{
  "user_id": "user_456",
  "state": {
    "score": 100,
    "level": 5,
    "position": {"x": 50, "y": 60}
  },
  "timestamp": "2025-10-05T10:30:00.123456+00:00"
}
```

---

## REST API Endpoints

The multiplayer module also provides REST API endpoints for room management:

### Create Room
**POST** `/api/multiplayer/rooms`

### Get Room
**GET** `/api/multiplayer/rooms/{room_id}`

### Get Room by Code
**GET** `/api/multiplayer/rooms/code/{room_code}`

### Join Room (REST)
**POST** `/api/multiplayer/rooms/{room_id}/join`

### Leave Room (REST)
**POST** `/api/multiplayer/rooms/{room_id}/leave`

### Start Game
**POST** `/api/multiplayer/rooms/{room_id}/start`

### Get Available Rooms
**GET** `/api/multiplayer/rooms/available?game_id={game_id}&limit={limit}`

### Get My Rooms
**GET** `/api/multiplayer/rooms/my-rooms`

### Get Room State
**GET** `/api/multiplayer/rooms/{room_id}/state`

### Get Active Sessions
**GET** `/api/multiplayer/sessions/active`

### Get Statistics
**GET** `/api/multiplayer/statistics`

---

## Error Messages

Common error message constants:
- `AUTHENTICATION_REQUIRED` - Token not provided
- `INVALID_TOKEN` - Token is malformed or invalid
- `TOKEN_EXPIRED` - Token has expired
- `ROOM_ID_REQUIRED` - Room ID not provided
- `ROOM_NOT_FOUND` - Room does not exist
- `ROOM_FULL` - Room has reached max players
- `NOT_ROOM_HOST` - Action requires host privileges
- `INTERNAL_SERVER_ERROR` - Server error occurred

---

## Connection Flow Example

```javascript
// 1. Connect to WebSocket
const socket = io('http://your-host/multiplayer');

// 2. Listen for connection
socket.on('connect', () => {
  console.log('Connected:', socket.id);
  
  // 3. Authenticate
  socket.emit('authenticate', {
    token: 'your_jwt_token',
    device_info: {
      platform: 'web',
      device_type: 'desktop',
      app_version: '1.0.0'
    }
  });
});

// 4. Listen for authentication success
socket.on('authenticated', (data) => {
  console.log('Authenticated:', data.user_id);
  
  // 5. Join a room
  socket.emit('join_room', {
    token: 'your_jwt_token',
    room_id: 'room_123'
  });
});

// 6. Listen for room events
socket.on('room_joined', (data) => {
  console.log('Joined room:', data.room_id);
});

socket.on('player_joined', (data) => {
  console.log('Player joined:', data.user_id);
});

// 7. Send game actions
socket.emit('game_action', {
  token: 'your_jwt_token',
  room_id: 'room_123',
  action: 'move',
  payload: { x: 10, y: 20 }
});

// 8. Listen for game actions from others
socket.on('game_action', (data) => {
  console.log('Action from:', data.user_id, data.action, data.payload);
});

// 9. Ping/pong for latency
setInterval(() => {
  const timestamp = Date.now();
  socket.emit('ping', { timestamp });
}, 5000);

socket.on('pong', (data) => {
  const latency = Date.now() - data.timestamp;
  console.log('Latency:', latency, 'ms');
});

// 10. Handle errors
socket.on('error', (data) => {
  console.error('WebSocket error:', data.message);
});

// 11. Cleanup on disconnect
socket.on('disconnect', () => {
  console.log('Disconnected from server');
});
```

---

## Configuration

WebSocket configuration can be set via environment variables:

```env
SOCKETIO_PING_TIMEOUT=60          # Ping timeout in seconds
SOCKETIO_PING_INTERVAL=25         # Ping interval in seconds
SOCKETIO_MAX_MESSAGE_SIZE=1000000 # Max message size (1MB)
MAX_PLAYERS_PER_ROOM=8            # Max players per room
MAX_ROOMS_PER_USER=3              # Max concurrent rooms per user
ROOM_TIMEOUT_SECONDS=3600         # Room timeout (1 hour)
ROOM_CODE_LENGTH=6                # Room code length
```

---

## Technical Details

- **Library**: Flask-SocketIO 5.5.1
- **Socket.IO Protocol**: Latest version
- **Transport**: WebSocket (with polling fallback)
- **Async Mode**: Threading (recommended for production 2025)
- **Cross-Origin**: Configured via CORS_ORIGINS environment variable
- **Authentication**: JWT-based with Bearer token
- **State Management**: MongoDB-backed persistence

---

## Database Collections

The multiplayer module uses three MongoDB collections:

1. **multiplayer_sessions** - Active WebSocket sessions
2. **game_rooms** - Multiplayer game rooms
3. **player_states** - Real-time player states

All collections are automatically indexed for performance.

---

## Production Deployment

For production deployment with Gunicorn:

```bash
gunicorn -w 1 --threads 100 -b 0.0.0.0:5000 app:app
```

Note: Flask-SocketIO with threading mode works best with a single worker and multiple threads.

For horizontal scaling, implement a message queue (Redis) for inter-process communication:

```python
socketio.init_app(app, message_queue='redis://localhost:6379')
```

---

## Testing

WebSocket tests are located in `tests/test_websocket_multiplayer.py`.

Run tests with:
```bash
pytest tests/test_websocket_multiplayer.py -v
```

---

## Implementation Status

✅ All GOO-54 acceptance criteria completed:
- Flask-SocketIO successfully installed and configured
- WebSocket server starts without errors
- Basic connection/disconnection handling works
- JWT authentication works on WebSocket
- Ping/pong latency measurement functioning
- Room join/leave events working
- Multiplayer module structure created
- Integration with existing app structure complete
- Error handling and logging in place
