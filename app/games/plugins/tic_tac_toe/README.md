# Tic Tac Toe Plugin - Usage Guide

## Overview
Classic Tic Tac Toe game with three play modes:
- **vs AI**: Play against computer AI (easy/medium/hard)
- **Local**: Play against another player on same device
- **Online**: Play against another player on different devices

## Installation

The plugin is auto-discovered on server startup from `/app/games/plugins/tic_tac_toe/`.

To manually load the plugin:
```python
from app.games.core.plugin_manager import plugin_manager
plugin_manager.discover_plugins()
```

## Game Modes

### 1. Play vs AI (Single Player)

Start a game against the computer:

```bash
POST /api/games/sessions
Content-Type: application/json
Authorization: Bearer {token}

{
  "game_id": "tic_tac_toe",
  "session_config": {
    "game_mode": "vs_ai",
    "ai_difficulty": "hard",    // "easy", "medium", or "hard"
    "player_symbol": "X"         // "X" (goes first) or "O"
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "SESSION_CREATED_SUCCESS",
  "data": {
    "session_id": "abc-123",
    "game_id": "tic_tac_toe",
    "status": "active",
    "current_state": {
      "board": [[null, null, null], [null, null, null], [null, null, null]],
      "current_player": "X",
      "game_mode": "vs_ai",
      "player_symbol": "X",
      "moves_history": [],
      "game_over": false
    }
  }
}
```

**Make a Move:**
```bash
POST /api/games/sessions/{session_id}/move
Content-Type: application/json
Authorization: Bearer {token}

{
  "move": {
    "position": [1, 1]  // Row 1, Col 1 (center)
  }
}
```

**Board Positions:**
```
[0,0] | [0,1] | [0,2]
------|-------|------
[1,0] | [1,1] | [1,2]
------|-------|------
[2,0] | [2,1] | [2,2]
```

**AI Difficulty Levels:**
- **Easy**: Random moves
- **Medium**: Blocks obvious wins, takes winning moves
- **Hard**: Unbeatable Minimax algorithm

---

### 2. Local Multiplayer (Same Device)

Two players take turns on the same device:

```bash
POST /api/games/sessions
{
  "game_id": "tic_tac_toe",
  "session_config": {
    "game_mode": "local"
  }
}
```

**Gameplay:**
1. Player 1 (X) makes a move
2. Player 2 (O) makes a move on the same device
3. Players alternate until game ends

The `current_player` field in state indicates whose turn it is.

---

### 3. Online Multiplayer (Different Devices)

Play against another player over the internet using WebSocket.

#### Step 1: Create a Room

**Player 1 creates a room:**
```bash
POST /api/multiplayer/rooms
Content-Type: application/json
Authorization: Bearer {player1_token}

{
  "game_id": "tic_tac_toe",
  "max_players": 2,
  "game_config": {
    "game_mode": "online"
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "ROOM_CREATED_SUCCESS",
  "data": {
    "room": {
      "room_id": "room-123",
      "room_code": "ABC123",
      "game_id": "tic_tac_toe",
      "host_user_id": "user1",
      "player_ids": ["user1"],
      "max_players": 2,
      "status": "waiting"
    }
  }
}
```

#### Step 2: Player 2 Joins the Room

**Player 2 joins using room code:**
```bash
POST /api/multiplayer/rooms/{room_id}/join
Authorization: Bearer {player2_token}

{
  "password": null  // if room is private
}
```

Or by room code:
```bash
GET /api/multiplayer/rooms/code/ABC123
```

Then:
```bash
POST /api/multiplayer/rooms/code/ABC123/join
```

#### Step 3: Connect via WebSocket

Both players connect to WebSocket:

```javascript
// Client-side (JavaScript example)
const socket = io('/multiplayer', {
  auth: {
    token: userToken
  }
});

// Join the room
socket.emit('join_room', {
  token: userToken,
  room_id: 'room-123'
});

// Listen for game events
socket.on('game_state_updated', (data) => {
  console.log('New game state:', data.state);
  // Update UI with new board state
});

socket.on('player_moved', (data) => {
  console.log('Player moved:', data.move);
  // Animate the move on the board
});

socket.on('game_ended', (data) => {
  console.log('Game ended:', data.result);
  // Show winner/draw screen
});
```

#### Step 4: Start the Game

```bash
POST /api/multiplayer/rooms/{room_id}/start
Authorization: Bearer {token}
```

#### Step 5: Make Moves via WebSocket

```javascript
// Make a move
socket.emit('game_action', {
  token: userToken,
  room_id: 'room-123',
  action_type: 'move',
  action_data: {
    position: [0, 0]  // Top-left corner
  }
});
```

**Server broadcasts move to both players:**
```javascript
// All players receive:
{
  "player_id": "user1",
  "move": {
    "position": [0, 0]
  },
  "new_state": {
    "board": [["X", null, null], ...],
    "current_player": "O",
    "move_count": 1
  }
}
```

---

## API Endpoints

### Session Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/games/sessions` | POST | Create new session |
| `/api/games/sessions/{session_id}` | GET | Get session state |
| `/api/games/sessions/{session_id}/move` | POST | Make a move |
| `/api/games/sessions/{session_id}` | DELETE | End session |

### Multiplayer (Online Mode)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/multiplayer/rooms` | POST | Create room |
| `/api/multiplayer/rooms/{room_id}` | GET | Get room details |
| `/api/multiplayer/rooms/code/{code}` | GET | Get room by code |
| `/api/multiplayer/rooms/{room_id}/join` | POST | Join room |
| `/api/multiplayer/rooms/{room_id}/start` | POST | Start game |

### WebSocket Events

| Event | Direction | Description |
|-------|-----------|-------------|
| `join_room` | Client → Server | Join a game room |
| `leave_room` | Client → Server | Leave a room |
| `game_action` | Client → Server | Make a move |
| `game_state_updated` | Server → Client | Board state changed |
| `player_moved` | Server → Client | Player made a move |
| `game_ended` | Server → Client | Game finished |
| `player_joined` | Server → Client | New player joined |
| `player_left` | Server → Client | Player left |

---

## Game State Structure

```javascript
{
  "board": [
    ["X", "O", null],
    [null, "X", null],
    ["O", null, null]
  ],
  "current_player": "X",      // "X" or "O"
  "game_mode": "vs_ai",       // "vs_ai", "local", or "online"
  "player_symbol": "X",       // Your symbol (vs_ai mode)
  "moves_history": [
    {"player": "X", "position": [0, 0], "move_number": 1},
    {"player": "O", "position": [0, 1], "move_number": 2}
  ],
  "game_over": false,
  "winner": null,             // "X", "O", or null
  "is_draw": false,
  "winning_line": null,       // [[0,0], [1,1], [2,2]] for diagonal win
  "move_count": 5
}
```

---

## Scoring System

| Outcome | Base Score | Bonuses |
|---------|-----------|---------|
| **Win** | 1000 | +200 (Quick Win ≤5 moves)<br>+500 (Perfect Win) |
| **Draw** | 300 | - |
| **Loss** | 100 | - |

**AI Difficulty Bonus:**
- Beat Hard AI: +5 credits
- Beat Medium AI: +2 credits
- Beat Easy AI: +1 credit

---

## Achievements

| Achievement | Condition |
|------------|-----------|
| `GAME_COMPLETED` | Finish any game |
| `TIC_TAC_TOE_WINNER` | Win a game |
| `AI_MASTER` | Beat Hard AI |
| `AI_CHALLENGER` | Beat Medium AI |
| `SPEED_DEMON` | Win in 5 moves or less |
| `PERFECT_VICTORY` | Win without opponent getting 2 in a row |
| `STALEMATE` | Finish in a draw |

---

## Example: Complete vs AI Game Flow

```bash
# 1. Start session
POST /api/games/sessions
{
  "game_id": "tic_tac_toe",
  "session_config": {
    "game_mode": "vs_ai",
    "ai_difficulty": "hard",
    "player_symbol": "X"
  }
}

# 2. Player moves to center
POST /api/games/sessions/{session_id}/move
{
  "move": {"position": [1, 1]}
}

# AI automatically responds...

# 3. Player moves again
POST /api/games/sessions/{session_id}/move
{
  "move": {"position": [0, 0]}
}

# Continue until game ends...

# 4. Get final state
GET /api/games/sessions/{session_id}

# Response shows winner, score, achievements

# 5. Delete session (optional, auto-cleans after end)
DELETE /api/games/sessions/{session_id}
```

---

## Development Notes

- **Session Storage**: In production, use MongoDB to persist sessions
- **Multiplayer Integration**: Online mode integrates with existing multiplayer system
- **AI Algorithm**: Hard mode uses Minimax (unbeatable)
- **WebSocket Namespace**: Events use `/multiplayer` namespace
- **Credit Rate**: 0.3 credits per minute (configured in plugin.json)

---

## Testing

```bash
# Test plugin loading
python -c "from app.games.core.plugin_manager import plugin_manager; \
           plugin_manager.discover_plugins(); \
           print(plugin_manager.registry.get_plugin('tic_tac_toe'))"

# Test AI move
python -c "from app.games.plugins.tic_tac_toe.main import TicTacToeGame; \
           game = TicTacToeGame(); \
           game.initialize(); \
           session = game.start_session('user1', {'game_mode': 'vs_ai', 'ai_difficulty': 'hard'}); \
           print(session.current_state)"
```

---

## Support

For issues or questions:
- Check game logs in `/api/games/sessions/{session_id}`
- Review multiplayer room status: `/api/multiplayer/rooms/{room_id}`
- Contact: support@goodplay.com
