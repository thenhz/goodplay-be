# Frontend Game Integration Guide - GoodPlay Platform

## Table of Contents

1. [Overview](#overview)
2. [Game Architecture](#game-architecture)
3. [Game Modes](#game-modes)
4. [API Integration - vs AI Mode](#api-integration---vs-ai-mode)
5. [API Integration - Local Multiplayer](#api-integration---local-multiplayer)
6. [API Integration - Online Multiplayer](#api-integration---online-multiplayer)
7. [WebSocket Integration](#websocket-integration)
8. [State Management](#state-management)
9. [Error Handling](#error-handling)
10. [Code Examples](#code-examples)
11. [Testing & Debugging](#testing--debugging)

---

## Overview

### What is GoodPlay?

GoodPlay is a gaming platform where users play games to earn virtual credits that can be donated to charitable organizations. Games are implemented as **plugins** on the backend, with a standardized API for frontend integration.

### How Games Work

```
┌─────────────┐      HTTP/WS      ┌──────────────┐      Plugin API      ┌─────────────┐
│  Frontend   │ ←───────────────→ │   Backend    │ ←──────────────────→ │ Game Plugin │
│   (React)   │                   │   (Flask)    │                      │ (Tic Tac Toe)│
└─────────────┘                   └──────────────┘                      └─────────────┘
```

**Key Concepts:**
- **Game Plugin**: Backend module that implements game logic
- **Game Session**: An instance of a game being played
- **Game State**: Current state of the game (board, score, etc.)
- **Game Mode**: How the game is played (vs AI, local, online)

### Supported Game Modes

| Mode | Description | Players | Connection Type |
|------|-------------|---------|-----------------|
| **vs AI** | Play against computer | 1 | REST API only |
| **Local** | Play on same device | 2+ | REST API only |
| **Online** | Play across devices | 2+ | REST API + WebSocket |

---

## Game Architecture

### Backend Components

```
app/games/
├── core/
│   ├── game_plugin.py          # Base plugin interface
│   ├── plugin_manager.py        # Plugin discovery/loading
│   └── plugin_registry.py       # Plugin registration
├── plugins/
│   ├── tic_tac_toe/            # Example game plugin
│   │   ├── plugin.json         # Game metadata
│   │   ├── main.py             # Game implementation
│   │   └── README.md           # Documentation
│   └── example_game/           # Another example
├── controllers/
│   └── games_controller.py     # REST endpoints
├── services/
│   └── game_session_service.py # Session management
└── multiplayer/
    ├── controllers/            # Multiplayer endpoints
    ├── services/               # Room management
    └── events/                 # WebSocket handlers
```

### Frontend Integration Flow

```
1. User selects game → GET /api/games/{game_id}
2. User starts game → POST /api/games/sessions
3. User plays game → POST /api/games/sessions/{id}/move (or WebSocket)
4. Game ends → GET /api/games/sessions/{id} (final state)
5. Cleanup → DELETE /api/games/sessions/{id}
```

---

## Game Modes

### Mode 1: vs AI (Single Player)

**Use Case**: User plays against computer AI

**Flow**:
1. Start session with AI configuration
2. Player makes move → POST request
3. **AI responds automatically** (included in response)
4. Repeat until game ends
5. View results

**Pros**:
- Simple integration (REST only)
- No connection management
- Instant AI response

**Cons**:
- Can't pause/resume easily
- No real-time updates

---

### Mode 2: Local Multiplayer

**Use Case**: Multiple players on same device taking turns

**Flow**:
1. Start session with local mode
2. Player 1 makes move → POST request
3. UI shows "Player 2's turn"
4. Player 2 makes move → POST request
5. Repeat until game ends

**Pros**:
- Simple integration (REST only)
- No network requirements
- Good for pass-and-play games

**Cons**:
- All players must share device
- No remote play

---

### Mode 3: Online Multiplayer

**Use Case**: Players on different devices playing together

**Flow**:
1. Player 1 creates room → POST /api/multiplayer/rooms
2. Player 2 joins room → POST /api/multiplayer/rooms/{id}/join
3. Both connect via WebSocket
4. Players make moves → WebSocket events
5. Real-time state sync via WebSocket
6. Game ends → WebSocket event

**Pros**:
- Real-time multiplayer
- Cross-device play
- Spectator support

**Cons**:
- More complex integration
- Requires WebSocket management
- Connection stability important

---

## API Integration - vs AI Mode

### Complete Flow Diagram

```
┌─────────┐                          ┌─────────┐
│ Frontend│                          │ Backend │
└────┬────┘                          └────┬────┘
     │                                    │
     │  POST /api/games/sessions         │
     │  {game_id, config: {game_mode:    │
     │   "vs_ai", ai_difficulty: "hard"}}│
     ├──────────────────────────────────►│
     │                                    │
     │  ◄─────────────────────────────────┤
     │  {session_id, board, current_player}
     │                                    │
     │  POST /sessions/{id}/move         │
     │  {move: {position: [0,0]}}        │
     ├──────────────────────────────────►│
     │                                    │
     │  ◄─────────────────────────────────┤
     │  {board (with AI move), game_over}│
     │                                    │
     │  (Repeat until game_over)         │
     │                                    │
     │  GET /sessions/{id}               │
     ├──────────────────────────────────►│
     │                                    │
     │  ◄─────────────────────────────────┤
     │  {winner, score, achievements}    │
     │                                    │
     │  DELETE /sessions/{id}            │
     ├──────────────────────────────────►│
     │                                    │
```

### Step 1: Start Game Session

**Endpoint**: `POST /api/games/sessions`

**Headers**:
```http
Authorization: Bearer {access_token}
Content-Type: application/json
```

**Request Body**:
```json
{
  "game_id": "tic_tac_toe",
  "session_config": {
    "game_mode": "vs_ai",
    "ai_difficulty": "hard",
    "player_symbol": "X"
  }
}
```

**Configuration Options**:
```typescript
interface SessionConfig {
  game_mode: "vs_ai" | "local" | "online";

  // vs AI specific
  ai_difficulty?: "easy" | "medium" | "hard";
  player_symbol?: "X" | "O";

  // Game-specific options
  [key: string]: any;
}
```

**Response (200 OK)**:
```json
{
  "success": true,
  "message": "GAME_SESSION_STARTED_SUCCESS",
  "data": {
    "session": {
      "session_id": "abc123",
      "game_id": "tic_tac_toe",
      "status": "active",
      "current_state": {
        "board": [[null, null, null], [null, null, null], [null, null, null]],
        "current_player": "X",
        "game_mode": "vs_ai",
        "player_symbol": "X",
        "moves_history": [],
        "game_over": false,
        "winner": null,
        "is_draw": false
      },
      "created_at": "2025-10-21T10:30:00Z"
    },
    "game": {
      "id": "tic_tac_toe",
      "name": "Tic Tac Toe",
      "description": "Classic 3x3 Tic Tac Toe",
      "credit_rate": 0.3
    }
  }
}
```

**Important Notes**:
- ✅ If player chooses `"O"`, AI makes first move automatically
- ✅ Response includes initial board state
- ✅ Save `session_id` for subsequent requests

---

### Step 2: Make Move (Player Action)

**Endpoint**: `POST /api/games/sessions/{session_id}/move`

**Request Body**:
```json
{
  "move": {
    "position": [1, 1]
  }
}
```

**Position Format** (for Tic Tac Toe):
```
Board Coordinates:
[0,0] | [0,1] | [0,2]
------|-------|------
[1,0] | [1,1] | [1,2]
------|-------|------
[2,0] | [2,1] | [2,2]

Example: [1,1] = center square
```

**Response (200 OK)** - Game Still Active:
```json
{
  "success": true,
  "message": "MOVE_VALID_SUCCESS",
  "data": {
    "session_id": "abc123",
    "current_state": {
      "board": [
        ["O", null, null],
        [null, "X", null],
        [null, null, null]
      ],
      "current_player": "X",
      "game_over": false,
      "move_count": 2,
      "moves_history": [
        {"player": "X", "position": [1, 1], "move_number": 1},
        {"player": "O", "position": [0, 0], "move_number": 2}
      ]
    }
  }
}
```

**Key Point**:
- ⚠️ **AI move is already included** in the response!
- Board shows both your move AND the AI's response
- `move_count` increases by 2 (your move + AI move)

**Response (200 OK)** - Game Ended:
```json
{
  "success": true,
  "message": "GAME_ENDED",
  "data": {
    "session_id": "abc123",
    "current_state": {
      "board": [
        ["X", "X", "X"],
        ["O", "O", null],
        [null, null, null]
      ],
      "current_player": "X",
      "game_over": true,
      "winner": "X",
      "is_draw": false,
      "winning_line": [[0, 0], [0, 1], [0, 2]]
    },
    "final_score": 1700,
    "credits_earned": 10,
    "achievements_unlocked": [
      "GAME_COMPLETED",
      "TIC_TAC_TOE_WINNER",
      "SPEED_DEMON"
    ]
  }
}
```

**Error Response (400 Bad Request)** - Invalid Move:
```json
{
  "success": false,
  "message": "INVALID_MOVE",
  "error": "Position already occupied"
}
```

**Common Invalid Moves**:
- Position already occupied
- Position out of bounds (e.g., `[3, 3]`)
- Not player's turn
- Game already over

---

### Step 3: Get Final State (Optional)

**Endpoint**: `GET /api/games/sessions/{session_id}`

**When to use**:
- To retrieve game results after completion
- To check session status
- To recover from connection issues

**Response**:
```json
{
  "success": true,
  "message": "SESSION_RETRIEVED_SUCCESS",
  "data": {
    "session_id": "abc123",
    "game_id": "tic_tac_toe",
    "user_id": "user123",
    "status": "completed",
    "current_state": { ... },
    "final_score": 1700,
    "credits_earned": 10,
    "started_at": "2025-10-21T10:30:00Z",
    "ended_at": "2025-10-21T10:33:00Z",
    "play_duration_ms": 180000
  }
}
```

---

### Step 4: End Session (Cleanup)

**Endpoint**: `DELETE /api/games/sessions/{session_id}`

**When to use**:
- After viewing final results
- User abandons game
- Cleanup on unmount

**Response**:
```json
{
  "success": true,
  "message": "SESSION_DELETED_SUCCESS"
}
```

**Note**: Sessions are auto-deleted after 24 hours of inactivity.

---

### Complete vs AI Example (Tic Tac Toe)

```typescript
// TypeScript/React example

interface TicTacToeMove {
  position: [number, number];
}

interface GameState {
  board: (string | null)[][];
  current_player: string;
  game_over: boolean;
  winner: string | null;
  is_draw: boolean;
}

class TicTacToeVsAI {
  private sessionId: string | null = null;
  private apiUrl = 'https://api.goodplay.com';
  private token: string;

  constructor(token: string) {
    this.token = token;
  }

  // Step 1: Start game
  async startGame(difficulty: 'easy' | 'medium' | 'hard' = 'hard'): Promise<GameState> {
    const response = await fetch(`${this.apiUrl}/api/games/sessions`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        game_id: 'tic_tac_toe',
        session_config: {
          game_mode: 'vs_ai',
          ai_difficulty: difficulty,
          player_symbol: 'X'
        }
      })
    });

    const data = await response.json();

    if (!data.success) {
      throw new Error(data.message);
    }

    this.sessionId = data.data.session.session_id;
    return data.data.session.current_state;
  }

  // Step 2: Make move
  async makeMove(row: number, col: number): Promise<GameState> {
    if (!this.sessionId) {
      throw new Error('Game not started');
    }

    const response = await fetch(`${this.apiUrl}/api/games/sessions/${this.sessionId}/move`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        move: {
          position: [row, col]
        }
      })
    });

    const data = await response.json();

    if (!data.success) {
      throw new Error(data.message);
    }

    return data.data.current_state;
  }

  // Step 3: Get final results
  async getResults() {
    if (!this.sessionId) {
      throw new Error('Game not started');
    }

    const response = await fetch(`${this.apiUrl}/api/games/sessions/${this.sessionId}`, {
      headers: {
        'Authorization': `Bearer ${this.token}`
      }
    });

    const data = await response.json();
    return data.data;
  }

  // Step 4: Cleanup
  async endGame() {
    if (!this.sessionId) return;

    await fetch(`${this.apiUrl}/api/games/sessions/${this.sessionId}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${this.token}`
      }
    });

    this.sessionId = null;
  }
}

// Usage example
const game = new TicTacToeVsAI(userToken);

// Start game
const initialState = await game.startGame('hard');
console.log('Initial board:', initialState.board);

// Make moves until game ends
let state = await game.makeMove(1, 1); // Center
if (!state.game_over) {
  state = await game.makeMove(0, 0); // Top-left
}

// Check if game ended
if (state.game_over) {
  const results = await game.getResults();
  console.log('Winner:', results.current_state.winner);
  console.log('Score:', results.final_score);
  console.log('Credits:', results.credits_earned);

  // Cleanup
  await game.endGame();
}
```

---

## API Integration - Local Multiplayer

### Complete Flow Diagram

```
┌──────────┐                         ┌─────────┐
│ Frontend │                         │ Backend │
│ (1 Device│                         │         │
│ 2 Players)                         │         │
└────┬─────┘                         └────┬────┘
     │                                    │
     │  POST /api/games/sessions         │
     │  {game_id, config: {game_mode:    │
     │   "local"}}                        │
     ├──────────────────────────────────►│
     │                                    │
     │  ◄─────────────────────────────────┤
     │  {session_id, board,              │
     │   current_player: "X"}            │
     │                                    │
     │  [UI shows "Player X's turn"]     │
     │                                    │
     │  POST /sessions/{id}/move         │
     │  {move: {position: [0,0]}}        │
     ├──────────────────────────────────►│
     │                                    │
     │  ◄─────────────────────────────────┤
     │  {board, current_player: "O"}     │
     │                                    │
     │  [UI shows "Player O's turn"]     │
     │                                    │
     │  POST /sessions/{id}/move         │
     │  {move: {position: [1,1]}}        │
     ├──────────────────────────────────►│
     │                                    │
     │  ◄─────────────────────────────────┤
     │  {board, current_player: "X"}     │
     │                                    │
     │  (Repeat until game_over)         │
     │                                    │
```

### Key Differences from vs AI

| Aspect | vs AI | Local |
|--------|-------|-------|
| **AI Response** | Automatic (in same response) | N/A |
| **Turn Management** | Handled by backend | Frontend shows whose turn |
| **Move Count** | +2 per request | +1 per request |
| **Player Switching** | N/A | UI prompts next player |

### Step 1: Start Local Game

**Request**:
```json
{
  "game_id": "tic_tac_toe",
  "session_config": {
    "game_mode": "local"
  }
}
```

**Response**:
```json
{
  "success": true,
  "message": "GAME_SESSION_STARTED_SUCCESS",
  "data": {
    "session": {
      "session_id": "xyz789",
      "current_state": {
        "board": [[null, null, null], [null, null, null], [null, null, null]],
        "current_player": "X",
        "game_mode": "local",
        "game_over": false
      }
    }
  }
}
```

### Step 2: Player X Makes Move

**Request**:
```json
{
  "move": {
    "position": [0, 0]
  }
}
```

**Response**:
```json
{
  "success": true,
  "message": "MOVE_VALID_SUCCESS",
  "data": {
    "current_state": {
      "board": [
        ["X", null, null],
        [null, null, null],
        [null, null, null]
      ],
      "current_player": "O",  // ← Note: switched to O
      "game_over": false,
      "move_count": 1         // ← Only 1 move (not 2)
    }
  }
}
```

**UI Action**: Show "Player O's turn" message

### Step 3: Player O Makes Move

Same device, different player makes next move.

**Request**:
```json
{
  "move": {
    "position": [1, 1]
  }
}
```

**Response**:
```json
{
  "success": true,
  "message": "MOVE_VALID_SUCCESS",
  "data": {
    "current_state": {
      "board": [
        ["X", null, null],
        [null, "O", null],
        [null, null, null]
      ],
      "current_player": "X",  // ← Back to X
      "game_over": false,
      "move_count": 2
    }
  }
}
```

**UI Action**: Show "Player X's turn" message

### Complete Local Example

```typescript
class TicTacToeLocal {
  private sessionId: string | null = null;
  private apiUrl = 'https://api.goodplay.com';
  private token: string;

  constructor(token: string) {
    this.token = token;
  }

  async startGame(): Promise<GameState> {
    const response = await fetch(`${this.apiUrl}/api/games/sessions`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        game_id: 'tic_tac_toe',
        session_config: {
          game_mode: 'local'
        }
      })
    });

    const data = await response.json();
    this.sessionId = data.data.session.session_id;
    return data.data.session.current_state;
  }

  async makeMove(row: number, col: number): Promise<GameState> {
    if (!this.sessionId) throw new Error('Game not started');

    const response = await fetch(`${this.apiUrl}/api/games/sessions/${this.sessionId}/move`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        move: { position: [row, col] }
      })
    });

    const data = await response.json();

    if (!data.success) {
      throw new Error(data.message);
    }

    return data.data.current_state;
  }

  async endGame() {
    if (!this.sessionId) return;
    await fetch(`${this.apiUrl}/api/games/sessions/${this.sessionId}`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${this.token}` }
    });
  }
}

// Usage in React component
function LocalGameComponent() {
  const [game] = useState(new TicTacToeLocal(token));
  const [state, setState] = useState<GameState | null>(null);
  const [message, setMessage] = useState('');

  useEffect(() => {
    game.startGame().then(setState);
  }, []);

  const handleCellClick = async (row: number, col: number) => {
    if (!state || state.game_over) return;

    try {
      const newState = await game.makeMove(row, col);
      setState(newState);

      if (newState.game_over) {
        setMessage(`Game Over! Winner: ${newState.winner || 'Draw'}`);
      } else {
        setMessage(`Player ${newState.current_player}'s turn`);
      }
    } catch (error) {
      setMessage(`Error: ${error.message}`);
    }
  };

  return (
    <div>
      <h2>{message}</h2>
      <Board state={state} onCellClick={handleCellClick} />
    </div>
  );
}
```

---

## API Integration - Online Multiplayer

### Architecture Overview

Online multiplayer uses **REST API for setup** and **WebSocket for gameplay**.

```
┌────────────┐                      ┌─────────┐                      ┌────────────┐
│  Player 1  │                      │ Backend │                      │  Player 2  │
│  (Device 1)│                      │         │                      │  (Device 2)│
└─────┬──────┘                      └────┬────┘                      └──────┬─────┘
      │                                  │                                  │
      │  POST /api/multiplayer/rooms    │                                  │
      ├────────────────────────────────►│                                  │
      │  ◄──────────────────────────────┤                                  │
      │  {room_id, room_code: "ABC123"} │                                  │
      │                                  │                                  │
      │  WebSocket connect              │                                  │
      ├────────────────────────────────►│                                  │
      │                                  │                                  │
      │  emit: join_room                │                                  │
      ├────────────────────────────────►│                                  │
      │                                  │                                  │
      │                                  │  GET /rooms/code/ABC123         │
      │                                  │◄────────────────────────────────┤
      │                                  │────────────────────────────────►│
      │                                  │  {room details}                 │
      │                                  │                                  │
      │                                  │  POST /rooms/{id}/join          │
      │                                  │◄────────────────────────────────┤
      │                                  │────────────────────────────────►│
      │                                  │                                  │
      │                                  │  WebSocket connect              │
      │                                  │◄────────────────────────────────┤
      │                                  │                                  │
      │                                  │  emit: join_room                │
      │                                  │◄────────────────────────────────┤
      │                                  │                                  │
      │  on: player_joined              │  on: player_joined              │
      │◄────────────────────────────────┼────────────────────────────────►│
      │                                  │                                  │
      │  POST /rooms/{id}/start         │                                  │
      ├────────────────────────────────►│                                  │
      │                                  │                                  │
      │  on: game_started               │  on: game_started               │
      │◄────────────────────────────────┼────────────────────────────────►│
      │                                  │                                  │
      │  emit: game_action (move)       │                                  │
      ├────────────────────────────────►│                                  │
      │                                  │  on: game_state_updated         │
      │                                  ├────────────────────────────────►│
      │                                  │                                  │
      │                                  │  emit: game_action (move)       │
      │                                  │◄────────────────────────────────┤
      │  on: game_state_updated         │                                  │
      │◄────────────────────────────────┤                                  │
      │                                  │                                  │
      │  (Continue until game_over)     │                                  │
      │                                  │                                  │
      │  on: game_ended                 │  on: game_ended                 │
      │◄────────────────────────────────┼────────────────────────────────►│
```

### Player 1 (Host) Flow

#### Step 1: Create Room

**Endpoint**: `POST /api/multiplayer/rooms`

**Request**:
```json
{
  "game_id": "tic_tac_toe",
  "max_players": 2,
  "game_config": {
    "game_mode": "online"
  }
}
```

**Response**:
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
      "status": "waiting",
      "created_at": "2025-10-21T10:30:00Z"
    }
  }
}
```

**Important**: Display `room_code` ("ABC123") to user for sharing.

#### Step 2: Connect WebSocket

```javascript
import io from 'socket.io-client';

const socket = io('https://api.goodplay.com/multiplayer', {
  auth: {
    token: userToken
  }
});

socket.on('connect', () => {
  console.log('WebSocket connected:', socket.id);
});

socket.on('disconnect', () => {
  console.log('WebSocket disconnected');
});
```

#### Step 3: Join Room (WebSocket)

```javascript
socket.emit('join_room', {
  token: userToken,
  room_id: 'room-123'
});

// Listen for confirmation
socket.on('room_joined', (data) => {
  console.log('Joined room:', data.room_id);
  console.log('Players:', data.players);
});
```

#### Step 4: Wait for Player 2

```javascript
socket.on('player_joined', (data) => {
  console.log('Player joined:', data.user_id);
  console.log('Total players:', data.player_count);

  // UI: Show "Opponent connected" message
  if (data.player_count === 2) {
    // UI: Enable "Start Game" button
  }
});
```

#### Step 5: Start Game

**Endpoint**: `POST /api/multiplayer/rooms/{room_id}/start`

```javascript
const startGame = async () => {
  const response = await fetch(`${apiUrl}/api/multiplayer/rooms/room-123/start`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${userToken}`
    }
  });

  const data = await response.json();
  console.log('Game started:', data);
};

// WebSocket event sent to all players
socket.on('game_started', (data) => {
  console.log('Game has started!');
  console.log('Initial state:', data.game_state);

  // UI: Show game board
});
```

### Player 2 (Guest) Flow

#### Step 1: Find Room by Code

**Endpoint**: `GET /api/multiplayer/rooms/code/{room_code}`

```javascript
const findRoom = async (roomCode: string) => {
  const response = await fetch(`${apiUrl}/api/multiplayer/rooms/code/${roomCode}`, {
    headers: {
      'Authorization': `Bearer ${userToken}`
    }
  });

  const data = await response.json();
  return data.data.room;
};

const room = await findRoom('ABC123');
console.log('Found room:', room.room_id);
```

**Response**:
```json
{
  "success": true,
  "message": "ROOM_RETRIEVED_SUCCESS",
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

#### Step 2: Join Room

**Endpoint**: `POST /api/multiplayer/rooms/{room_id}/join`

```javascript
const joinRoom = async (roomId: string) => {
  const response = await fetch(`${apiUrl}/api/multiplayer/rooms/${roomId}/join`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${userToken}`
    }
  });

  const data = await response.json();
  return data;
};

await joinRoom('room-123');
```

#### Step 3: Connect WebSocket

Same as Player 1 - connect and join room via WebSocket events.

```javascript
const socket = io('https://api.goodplay.com/multiplayer', {
  auth: { token: userToken }
});

socket.on('connect', () => {
  socket.emit('join_room', {
    token: userToken,
    room_id: 'room-123'
  });
});
```

#### Step 4: Wait for Game Start

```javascript
socket.on('game_started', (data) => {
  console.log('Game started by host');
  console.log('Initial state:', data.game_state);
  // UI: Show game board
});
```

---

## WebSocket Integration

### WebSocket Events Reference

#### Client → Server Events

| Event | Data | Description |
|-------|------|-------------|
| `join_room` | `{token, room_id}` | Join a multiplayer room |
| `leave_room` | `{room_id}` | Leave a room |
| `game_action` | `{token, room_id, action_type, action_data}` | Make a game move |
| `player_ready` | `{room_id}` | Mark player as ready |

#### Server → Client Events

| Event | Data | Description |
|-------|------|-------------|
| `room_joined` | `{room_id, players}` | Confirmation of join |
| `player_joined` | `{user_id, player_count}` | Another player joined |
| `player_left` | `{user_id, player_count}` | Player disconnected |
| `game_started` | `{game_state}` | Game has begun |
| `game_state_updated` | `{state, timestamp}` | State changed |
| `player_moved` | `{player_id, move, new_state}` | Player made move |
| `game_ended` | `{result, winner, scores}` | Game finished |
| `error` | `{message, code}` | Error occurred |

### Making Moves via WebSocket

```javascript
// Make a move
socket.emit('game_action', {
  token: userToken,
  room_id: 'room-123',
  action_type: 'move',
  action_data: {
    position: [0, 0]
  }
});
```

### Receiving State Updates

```javascript
// Listen for state updates
socket.on('game_state_updated', (data) => {
  console.log('New state:', data.state);
  console.log('Updated at:', data.timestamp);

  // Update UI
  updateBoard(data.state.board);
  updateCurrentPlayer(data.state.current_player);

  if (data.state.game_over) {
    showGameOver(data.state.winner);
  }
});

// Listen for specific player moves
socket.on('player_moved', (data) => {
  console.log(`${data.player_id} moved to ${data.move.position}`);

  // Animate the move
  animateMove(data.move.position, data.player_id);
});
```

### Handling Game End

```javascript
socket.on('game_ended', (data) => {
  console.log('Game ended!');
  console.log('Winner:', data.result.winner);
  console.log('Scores:', data.result.scores);
  console.log('Achievements:', data.result.achievements);

  // UI: Show results screen
  showResults({
    winner: data.result.winner,
    yourScore: data.result.scores[userId],
    creditsEarned: data.result.credits_earned
  });

  // Cleanup
  socket.emit('leave_room', { room_id: roomId });
});
```

### Reconnection Handling

```javascript
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 5;

socket.on('disconnect', (reason) => {
  console.log('Disconnected:', reason);

  if (reason === 'io server disconnect') {
    // Server kicked us out, don't reconnect
    showError('You were disconnected from the game');
  } else {
    // Connection lost, try to reconnect
    showReconnecting();
  }
});

socket.on('reconnect', (attemptNumber) => {
  console.log('Reconnected after', attemptNumber, 'attempts');

  // Rejoin room
  socket.emit('join_room', {
    token: userToken,
    room_id: currentRoomId
  });

  hideReconnecting();
});

socket.on('reconnect_failed', () => {
  console.log('Reconnection failed');
  showError('Could not reconnect to game');
});
```

### Complete Online Example

```typescript
class TicTacToeOnline {
  private socket: Socket;
  private roomId: string | null = null;
  private roomCode: string | null = null;
  private apiUrl = 'https://api.goodplay.com';
  private token: string;

  constructor(token: string) {
    this.token = token;
    this.socket = io(`${this.apiUrl}/multiplayer`, {
      auth: { token }
    });
    this.setupSocketListeners();
  }

  // Create room (Player 1)
  async createRoom(): Promise<{roomId: string, roomCode: string}> {
    const response = await fetch(`${this.apiUrl}/api/multiplayer/rooms`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        game_id: 'tic_tac_toe',
        max_players: 2,
        game_config: { game_mode: 'online' }
      })
    });

    const data = await response.json();
    this.roomId = data.data.room.room_id;
    this.roomCode = data.data.room.room_code;

    // Join room via WebSocket
    this.socket.emit('join_room', {
      token: this.token,
      room_id: this.roomId
    });

    return {
      roomId: this.roomId,
      roomCode: this.roomCode
    };
  }

  // Join room by code (Player 2)
  async joinRoomByCode(roomCode: string): Promise<void> {
    // Find room
    const response = await fetch(`${this.apiUrl}/api/multiplayer/rooms/code/${roomCode}`, {
      headers: { 'Authorization': `Bearer ${this.token}` }
    });

    const data = await response.json();
    this.roomId = data.data.room.room_id;
    this.roomCode = roomCode;

    // Join via REST
    await fetch(`${this.apiUrl}/api/multiplayer/rooms/${this.roomId}/join`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${this.token}` }
    });

    // Join via WebSocket
    this.socket.emit('join_room', {
      token: this.token,
      room_id: this.roomId
    });
  }

  // Start game (Host only)
  async startGame(): Promise<void> {
    if (!this.roomId) throw new Error('Not in a room');

    await fetch(`${this.apiUrl}/api/multiplayer/rooms/${this.roomId}/start`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${this.token}` }
    });
  }

  // Make move
  makeMove(row: number, col: number): void {
    if (!this.roomId) throw new Error('Not in a room');

    this.socket.emit('game_action', {
      token: this.token,
      room_id: this.roomId,
      action_type: 'move',
      action_data: {
        position: [row, col]
      }
    });
  }

  // Setup event listeners
  private setupSocketListeners(): void {
    this.socket.on('connect', () => {
      console.log('WebSocket connected');
    });

    this.socket.on('room_joined', (data) => {
      console.log('Joined room:', data.room_id);
    });

    this.socket.on('player_joined', (data) => {
      console.log('Player joined:', data.user_id);
      this.onPlayerJoined?.(data);
    });

    this.socket.on('game_started', (data) => {
      console.log('Game started');
      this.onGameStarted?.(data.game_state);
    });

    this.socket.on('game_state_updated', (data) => {
      this.onStateUpdated?.(data.state);
    });

    this.socket.on('game_ended', (data) => {
      this.onGameEnded?.(data.result);
    });

    this.socket.on('error', (error) => {
      console.error('Socket error:', error);
      this.onError?.(error);
    });
  }

  // Event callbacks (set these from your UI)
  onPlayerJoined?: (data: any) => void;
  onGameStarted?: (state: GameState) => void;
  onStateUpdated?: (state: GameState) => void;
  onGameEnded?: (result: any) => void;
  onError?: (error: any) => void;

  // Cleanup
  disconnect(): void {
    if (this.roomId) {
      this.socket.emit('leave_room', { room_id: this.roomId });
    }
    this.socket.disconnect();
  }
}

// Usage in React
function OnlineGameComponent() {
  const [game] = useState(() => new TicTacToeOnline(token));
  const [state, setState] = useState<GameState | null>(null);
  const [roomCode, setRoomCode] = useState('');
  const [isHost, setIsHost] = useState(false);

  useEffect(() => {
    // Setup callbacks
    game.onGameStarted = setState;
    game.onStateUpdated = setState;
    game.onGameEnded = (result) => {
      console.log('Game ended:', result);
      // Show results
    };

    return () => game.disconnect();
  }, []);

  const handleCreateRoom = async () => {
    const { roomCode } = await game.createRoom();
    setRoomCode(roomCode);
    setIsHost(true);
  };

  const handleJoinRoom = async (code: string) => {
    await game.joinRoomByCode(code);
    setRoomCode(code);
    setIsHost(false);
  };

  const handleStartGame = () => {
    game.startGame();
  };

  const handleCellClick = (row: number, col: number) => {
    game.makeMove(row, col);
  };

  return (
    <div>
      {!roomCode ? (
        <div>
          <button onClick={handleCreateRoom}>Create Room</button>
          <input
            placeholder="Room Code"
            onChange={(e) => handleJoinRoom(e.target.value)}
          />
        </div>
      ) : (
        <div>
          <h2>Room Code: {roomCode}</h2>
          {isHost && <button onClick={handleStartGame}>Start Game</button>}
          {state && <Board state={state} onCellClick={handleCellClick} />}
        </div>
      )}
    </div>
  );
}
```

---

## State Management

### Game State Structure

Every game provides a `current_state` object. For Tic Tac Toe:

```typescript
interface TicTacToeState {
  // Core game state
  board: (string | null)[][];      // 3x3 grid
  current_player: "X" | "O";       // Whose turn
  game_mode: "vs_ai" | "local" | "online";

  // Game progress
  game_over: boolean;
  winner: "X" | "O" | null;
  is_draw: boolean;
  winning_line: [number, number][] | null;  // Winning positions

  // Move history
  move_count: number;
  moves_history: Array<{
    player: string;
    position: [number, number];
    move_number: number;
  }>;

  // vs AI specific
  player_symbol?: "X" | "O";
  ai_symbol?: "X" | "O";
}
```

### UI State Mapping

```typescript
// Component state
interface UIState {
  gameState: TicTacToeState | null;
  isLoading: boolean;
  error: string | null;
  message: string;  // Display to user

  // Computed from gameState
  canMakeMove: boolean;
  currentPlayerName: string;
  gameResult: GameResult | null;
}

function useGameState(initialState: TicTacToeState | null) {
  const [uiState, setUIState] = useState<UIState>({
    gameState: initialState,
    isLoading: false,
    error: null,
    message: '',
    canMakeMove: true,
    currentPlayerName: 'Player X',
    gameResult: null
  });

  // Update UI state when game state changes
  useEffect(() => {
    if (!uiState.gameState) return;

    const state = uiState.gameState;

    setUIState(prev => ({
      ...prev,
      canMakeMove: !state.game_over,
      currentPlayerName: `Player ${state.current_player}`,
      message: state.game_over
        ? (state.winner ? `${state.winner} wins!` : "It's a draw!")
        : `${state.current_player}'s turn`,
      gameResult: state.game_over ? {
        winner: state.winner,
        isDraw: state.is_draw,
        winningLine: state.winning_line
      } : null
    }));
  }, [uiState.gameState]);

  return [uiState, setUIState] as const;
}
```

### Optimistic Updates

For better UX, update UI immediately before server response:

```typescript
async function makeMove(row: number, col: number) {
  if (!state || state.game_over) return;

  // 1. Optimistic update - show move immediately
  const optimisticState = {
    ...state,
    board: state.board.map((r, i) =>
      i === row ? r.map((c, j) => j === col ? state.current_player : c) : r
    )
  };
  setState(optimisticState);
  setIsLoading(true);

  try {
    // 2. Send request
    const newState = await game.makeMove(row, col);

    // 3. Replace with server state
    setState(newState);
  } catch (error) {
    // 4. Rollback on error
    setState(state);
    setError(error.message);
  } finally {
    setIsLoading(false);
  }
}
```

---

## Error Handling

### Common Errors

| Error Code | Message | Cause | Solution |
|------------|---------|-------|----------|
| `GAME_NOT_FOUND` | Game not found | Invalid game_id | Check available games |
| `GAME_NOT_ACTIVE` | Game not active | Game disabled | Choose another game |
| `ACTIVE_SESSION_EXISTS` | Session already active | User has open session | End existing session first |
| `SESSION_NOT_FOUND` | Session not found | Invalid session_id | Create new session |
| `INVALID_MOVE` | Move not valid | Occupied/out of bounds | Validate move client-side |
| `NOT_PLAYER_TURN` | Not your turn | Wrong player | Wait for turn |
| `GAME_ALREADY_ENDED` | Game already ended | Session completed | Create new session |
| `ROOM_NOT_FOUND` | Room not found | Invalid room_id/code | Check room code |
| `ROOM_FULL` | Room is full | Max players reached | Create new room |
| `AUTHENTICATION_REQUIRED` | Not authenticated | Missing/invalid token | Re-login |

### Error Handling Pattern

```typescript
async function handleGameAction<T>(
  action: () => Promise<T>,
  errorHandler?: (error: Error) => void
): Promise<T | null> {
  try {
    setIsLoading(true);
    setError(null);

    const result = await action();
    return result;

  } catch (error) {
    console.error('Game action failed:', error);

    // Parse error
    const message = error.response?.data?.message || error.message;

    // Handle specific errors
    if (message === 'AUTHENTICATION_REQUIRED') {
      // Redirect to login
      router.push('/login');
    } else if (message === 'SESSION_NOT_FOUND') {
      // Reset game
      resetGame();
    } else {
      // Show error to user
      setError(getErrorMessage(message));
      errorHandler?.(error);
    }

    return null;

  } finally {
    setIsLoading(false);
  }
}

// Usage
const state = await handleGameAction(
  () => game.makeMove(0, 0),
  (error) => console.log('Move failed:', error)
);
```

### User-Friendly Error Messages

```typescript
const ERROR_MESSAGES: Record<string, string> = {
  'GAME_NOT_FOUND': 'This game is not available',
  'INVALID_MOVE': 'Invalid move. Try another position.',
  'NOT_PLAYER_TURN': 'Wait for your turn',
  'ROOM_NOT_FOUND': 'Room not found. Check the code.',
  'ROOM_FULL': 'This room is full',
  'CONNECTION_LOST': 'Connection lost. Reconnecting...',
  'AUTHENTICATION_REQUIRED': 'Please login again'
};

function getErrorMessage(code: string): string {
  return ERROR_MESSAGES[code] || 'An error occurred. Please try again.';
}
```

---

## Code Examples

### React + TypeScript Complete Example

```typescript
// hooks/useGameSession.ts
import { useState, useEffect, useCallback } from 'react';

interface UseGameSessionOptions {
  gameId: string;
  mode: 'vs_ai' | 'local' | 'online';
  config?: any;
}

export function useGameSession(options: UseGameSessionOptions) {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [state, setState] = useState<GameState | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const startSession = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/games/sessions', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${getToken()}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          game_id: options.gameId,
          session_config: {
            game_mode: options.mode,
            ...options.config
          }
        })
      });

      const data = await response.json();

      if (!data.success) {
        throw new Error(data.message);
      }

      setSessionId(data.data.session.session_id);
      setState(data.data.session.current_state);

    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }, [options]);

  const makeMove = useCallback(async (move: any) => {
    if (!sessionId) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`/api/games/sessions/${sessionId}/move`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${getToken()}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ move })
      });

      const data = await response.json();

      if (!data.success) {
        throw new Error(data.message);
      }

      setState(data.data.current_state);

    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }, [sessionId]);

  const endSession = useCallback(async () => {
    if (!sessionId) return;

    await fetch(`/api/games/sessions/${sessionId}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${getToken()}`
      }
    });

    setSessionId(null);
    setState(null);
  }, [sessionId]);

  return {
    sessionId,
    state,
    isLoading,
    error,
    startSession,
    makeMove,
    endSession
  };
}

// components/TicTacToe.tsx
function TicTacToeGame() {
  const {
    state,
    isLoading,
    error,
    startSession,
    makeMove,
    endSession
  } = useGameSession({
    gameId: 'tic_tac_toe',
    mode: 'vs_ai',
    config: {
      ai_difficulty: 'hard',
      player_symbol: 'X'
    }
  });

  useEffect(() => {
    startSession();
    return () => endSession();
  }, []);

  const handleCellClick = (row: number, col: number) => {
    if (!state || state.game_over || isLoading) return;
    makeMove({ position: [row, col] });
  };

  if (!state) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div className="game">
      <h2>
        {state.game_over
          ? state.winner ? `${state.winner} wins!` : "Draw!"
          : `${state.current_player}'s turn`
        }
      </h2>

      <div className="board">
        {state.board.map((row, i) => (
          <div key={i} className="row">
            {row.map((cell, j) => (
              <button
                key={j}
                className="cell"
                onClick={() => handleCellClick(i, j)}
                disabled={!!cell || state.game_over || isLoading}
              >
                {cell}
              </button>
            ))}
          </div>
        ))}
      </div>

      {state.game_over && (
        <button onClick={startSession}>Play Again</button>
      )}
    </div>
  );
}
```

### Vue 3 + Composition API Example

```vue
<!-- composables/useGameSession.ts -->
<script setup lang="ts">
import { ref, computed } from 'vue';

export function useGameSession(gameId: string, mode: string, config: any = {}) {
  const sessionId = ref<string | null>(null);
  const state = ref<GameState | null>(null);
  const isLoading = ref(false);
  const error = ref<string | null>(null);

  const gameOver = computed(() => state.value?.game_over ?? false);
  const winner = computed(() => state.value?.winner);

  async function startSession() {
    isLoading.value = true;
    error.value = null;

    try {
      const response = await fetch('/api/games/sessions', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${getToken()}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          game_id: gameId,
          session_config: { game_mode: mode, ...config }
        })
      });

      const data = await response.json();
      sessionId.value = data.data.session.session_id;
      state.value = data.data.session.current_state;

    } catch (err) {
      error.value = err.message;
    } finally {
      isLoading.value = false;
    }
  }

  async function makeMove(move: any) {
    if (!sessionId.value) return;

    isLoading.value = true;

    try {
      const response = await fetch(`/api/games/sessions/${sessionId.value}/move`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${getToken()}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ move })
      });

      const data = await response.json();
      state.value = data.data.current_state;

    } catch (err) {
      error.value = err.message;
    } finally {
      isLoading.value = false;
    }
  }

  return {
    sessionId,
    state,
    isLoading,
    error,
    gameOver,
    winner,
    startSession,
    makeMove
  };
}
</script>

<!-- TicTacToe.vue -->
<template>
  <div class="game">
    <h2>{{ message }}</h2>

    <div v-if="state" class="board">
      <div v-for="(row, i) in state.board" :key="i" class="row">
        <button
          v-for="(cell, j) in row"
          :key="j"
          class="cell"
          @click="handleCellClick(i, j)"
          :disabled="!!cell || gameOver || isLoading"
        >
          {{ cell }}
        </button>
      </div>
    </div>

    <button v-if="gameOver" @click="startSession">
      Play Again
    </button>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue';
import { useGameSession } from './composables/useGameSession';

const {
  state,
  isLoading,
  gameOver,
  winner,
  startSession,
  makeMove
} = useGameSession('tic_tac_toe', 'vs_ai', {
  ai_difficulty: 'hard',
  player_symbol: 'X'
});

const message = computed(() => {
  if (!state.value) return 'Loading...';
  if (gameOver.value) {
    return winner.value ? `${winner.value} wins!` : "Draw!";
  }
  return `${state.value.current_player}'s turn`;
});

function handleCellClick(row: number, col: number) {
  makeMove({ position: [row, col] });
}

onMounted(() => {
  startSession();
});
</script>
```

### Vanilla JavaScript Example

```javascript
// game-session.js
class GameSession {
  constructor(gameId, mode, config = {}) {
    this.gameId = gameId;
    this.mode = mode;
    this.config = config;
    this.sessionId = null;
    this.state = null;
    this.apiUrl = 'https://api.goodplay.com';
    this.token = localStorage.getItem('token');
  }

  async startSession() {
    const response = await fetch(`${this.apiUrl}/api/games/sessions`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        game_id: this.gameId,
        session_config: {
          game_mode: this.mode,
          ...this.config
        }
      })
    });

    const data = await response.json();

    if (!data.success) {
      throw new Error(data.message);
    }

    this.sessionId = data.data.session.session_id;
    this.state = data.data.session.current_state;

    return this.state;
  }

  async makeMove(move) {
    const response = await fetch(`${this.apiUrl}/api/games/sessions/${this.sessionId}/move`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ move })
    });

    const data = await response.json();

    if (!data.success) {
      throw new Error(data.message);
    }

    this.state = data.data.current_state;
    return this.state;
  }

  async endSession() {
    if (!this.sessionId) return;

    await fetch(`${this.apiUrl}/api/games/sessions/${this.sessionId}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${this.token}`
      }
    });

    this.sessionId = null;
    this.state = null;
  }
}

// tic-tac-toe.js
class TicTacToeUI {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    this.session = new GameSession('tic_tac_toe', 'vs_ai', {
      ai_difficulty: 'hard',
      player_symbol: 'X'
    });

    this.init();
  }

  async init() {
    await this.session.startSession();
    this.render();
  }

  render() {
    const state = this.session.state;

    if (!state) {
      this.container.innerHTML = '<p>Loading...</p>';
      return;
    }

    const message = state.game_over
      ? (state.winner ? `${state.winner} wins!` : "Draw!")
      : `${state.current_player}'s turn`;

    let html = `<h2>${message}</h2><div class="board">`;

    state.board.forEach((row, i) => {
      html += '<div class="row">';
      row.forEach((cell, j) => {
        const disabled = cell || state.game_over ? 'disabled' : '';
        html += `
          <button
            class="cell"
            data-row="${i}"
            data-col="${j}"
            ${disabled}
          >
            ${cell || ''}
          </button>
        `;
      });
      html += '</div>';
    });

    html += '</div>';

    if (state.game_over) {
      html += '<button id="play-again">Play Again</button>';
    }

    this.container.innerHTML = html;

    // Add event listeners
    this.container.querySelectorAll('.cell').forEach(button => {
      button.addEventListener('click', (e) => {
        const row = parseInt(e.target.dataset.row);
        const col = parseInt(e.target.dataset.col);
        this.handleCellClick(row, col);
      });
    });

    const playAgainBtn = document.getElementById('play-again');
    if (playAgainBtn) {
      playAgainBtn.addEventListener('click', () => this.init());
    }
  }

  async handleCellClick(row, col) {
    try {
      await this.session.makeMove({ position: [row, col] });
      this.render();
    } catch (error) {
      alert(`Error: ${error.message}`);
    }
  }
}

// Initialize
const game = new TicTacToeUI('game-container');
```

---

## Testing & Debugging

### Local Testing Setup

```bash
# 1. Start backend
cd goodplay-be
python app.py

# 2. Test authentication
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}'

# 3. Start game session
curl -X POST http://localhost:5000/api/games/sessions \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "game_id": "tic_tac_toe",
    "session_config": {"game_mode": "vs_ai"}
  }'

# 4. Make move
curl -X POST http://localhost:5000/api/games/sessions/SESSION_ID/move \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"move": {"position": [1,1]}}'
```

### Postman Collections

Import the Postman collections from `docs/postman/`:
- `games_collection.json` - All game endpoints
- `core_collection.json` - Auth and user endpoints

**Setup**:
1. Import collection
2. Set environment variables:
   - `baseUrl`: http://localhost:5000
   - `token`: (auto-filled after login)
3. Run "Login" request first
4. Test game flows

### Browser DevTools

```javascript
// Debug WebSocket in console
socket.onAny((event, ...args) => {
  console.log(`[WS] ${event}:`, args);
});

// Monitor all requests
window.addEventListener('beforeunload', () => {
  console.log('Current session:', sessionId);
  console.log('Last state:', state);
});

// Test game state
window.gameDebug = {
  getState: () => state,
  makeMove: (r, c) => makeMove(r, c),
  endGame: () => endSession()
};
```

### Common Issues & Solutions

| Issue | Symptom | Solution |
|-------|---------|----------|
| **CORS Error** | `Access-Control-Allow-Origin` | Check CORS_ORIGINS in backend `.env` |
| **401 Unauthorized** | Authentication failed | Re-login, check token expiry |
| **Session not found** | 404 on move | Session expired, create new one |
| **WebSocket not connecting** | `disconnect` immediately | Check token, firewall, URL |
| **State not updating** | Old state displayed | Check event listeners, React state |
| **Moves not working** | No response | Validate move format, check current_player |

### Debug Checklist

```markdown
## Pre-Launch Checklist

### Authentication
- [ ] Login works
- [ ] Token is stored correctly
- [ ] Token is sent in all requests
- [ ] Token refresh works (if implemented)

### Game Session
- [ ] Session creation works
- [ ] Session ID is saved
- [ ] State updates on moves
- [ ] Game over detection works
- [ ] Session cleanup on unmount

### UI/UX
- [ ] Loading states shown
- [ ] Error messages displayed
- [ ] Disabled state for invalid moves
- [ ] Winner announcement works
- [ ] "Play again" resets correctly

### Online Multiplayer (if applicable)
- [ ] WebSocket connects
- [ ] Room creation works
- [ ] Room joining works
- [ ] Room code is displayed
- [ ] Both players see updates
- [ ] Reconnection works
- [ ] Game end cleanup works
```

---

## Summary

### Quick Reference

#### vs AI Mode
```
1. POST /api/games/sessions (with vs_ai config)
2. Loop: POST /sessions/{id}/move
3. DELETE /sessions/{id}
```

#### Local Mode
```
1. POST /api/games/sessions (with local config)
2. Loop: POST /sessions/{id}/move (alternate players)
3. DELETE /sessions/{id}
```

#### Online Mode
```
1. POST /api/multiplayer/rooms
2. WebSocket connect + join_room
3. POST /api/multiplayer/rooms/{id}/start
4. WebSocket: game_action events
5. Cleanup on game_ended
```

### Key Takeaways

✅ **vs AI**: Simplest integration, REST only, AI responds automatically
✅ **Local**: Pass-and-play, REST only, manual turn management
✅ **Online**: Most complex, REST + WebSocket, real-time sync
✅ **State Management**: Always check `current_player` and `game_over`
✅ **Error Handling**: Validate moves client-side, handle errors gracefully
✅ **WebSocket**: Implement reconnection logic for stability

### Need Help?

- **API Docs**: `/docs/openapi/games.yaml`
- **Postman**: `/docs/postman/games_collection.json`
- **Backend Guide**: `/docs/GAME_DEVELOPMENT_GUIDE.md`
- **Support**: support@goodplay.com

---

*Last Updated: 2025-10-21*
*Version: 1.0*
