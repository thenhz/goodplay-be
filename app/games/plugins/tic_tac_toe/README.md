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

---

## For Developers

This section provides technical guidance for developers working on the Tic Tac Toe plugin or using it as a reference for new game development.

### 📚 Comprehensive Guides

For detailed development information, see:

- **[Game Development Guide](../../../docs/GAME_DEVELOPMENT_GUIDE.md)** - Complete guide for creating game plugins, implementing GamePlugin interface, and integrating with platform features
- **[Implementation Notes](IMPLEMENTATION_NOTES.md)** - Technical deep-dive into this plugin's architecture, AI algorithms, state management, and design decisions
- **[Frontend Integration Guide](../../../docs/FRONTEND_GAME_INTEGRATION_GUIDE.md)** - Step-by-step guide for frontend developers on integrating games with the backend API

### 🏗️ Code Structure

```
tic_tac_toe/
├── __init__.py           # Python package marker
├── plugin.json           # Plugin metadata and configuration
├── main.py              # Core game logic (TicTacToeGame class)
├── README.md            # User documentation (this file)
└── IMPLEMENTATION_NOTES.md  # Technical implementation details
```

**Key Components in `main.py`:**

| Component | Line Range | Description |
|-----------|-----------|-------------|
| `TicTacToeGame` class | 1-650 | Main plugin class extending GamePlugin |
| `start_session()` | ~80-150 | Session initialization for all 3 modes |
| `validate_move()` | ~180-280 | Move validation + AI response trigger |
| AI: `_make_ai_move()` | ~350-380 | AI move orchestrator |
| AI: `_get_random_move()` | ~385-390 | Easy difficulty (random) |
| AI: `_get_heuristic_move()` | ~395-450 | Medium difficulty (strategic) |
| AI: `_get_best_move()` | ~455-480 | Hard difficulty (minimax) |
| AI: `_minimax()` | ~485-550 | Recursive minimax algorithm |
| `_check_winner()` | ~560-620 | Win detection with winning line |
| `_calculate_score()` | ~630-650 | Score and credit calculation |

### 🎯 Key Implementation Highlights

#### 1. Game Mode Support

The plugin demonstrates three distinct game modes:

```python
# vs_ai: Single-player against computer
if game_mode == self.MODE_VS_AI:
    # Auto-trigger AI response in validate_move()

# local: Pass-and-play on same device
elif game_mode == self.MODE_LOCAL:
    # Simple turn switching

# online: Real-time multiplayer
elif game_mode == self.MODE_ONLINE:
    # Validate player_id matches turn
    # Relies on multiplayer system for sync
```

**Reference**: `IMPLEMENTATION_NOTES.md` Section 2 for detailed mode patterns

#### 2. AI Implementation

Three difficulty levels with different algorithms:

- **Easy** (`random`): O(1) - Random valid move
- **Medium** (`heuristic`): O(n) - Strategic rules (win/block/center)
- **Hard** (`minimax`): O(b^d) - Unbeatable minimax with alpha-beta pruning

**Reference**: `IMPLEMENTATION_NOTES.md` Section 3 for AI algorithm details

#### 3. State Management

The plugin uses a dual-state approach:

```python
# Public state (visible to frontend)
public_state = {
    "board": [[...], [...], [...]],
    "current_player": "X",
    "game_over": False
}

# Private state (server-only)
private_state = {
    "ai_difficulty": "hard",
    "player_symbol": "X"
}
```

**Reference**: `IMPLEMENTATION_NOTES.md` Section 4 for state structure

#### 4. Platform Integration

Demonstrates integration with GoodPlay platform features:

```python
# Achievements
achievements = []
if winner == player_symbol:
    achievements.append("TIC_TAC_TOE_WINNER")
if move_count <= 5:
    achievements.append("SPEED_DEMON")

# Credits calculation
base_credits = play_time_minutes * self.credit_rate
if beat_hard_ai:
    bonus_credits += 5.0
```

**Reference**: `GAME_DEVELOPMENT_GUIDE.md` Section 8 for platform integration patterns

### 🔧 Extending the Plugin

#### Adding New AI Difficulty

To add a "Expert" difficulty level:

1. Add constant: `AI_EXPERT = "expert"`
2. Implement method: `_get_expert_move(board, ai_symbol)`
3. Update `_make_ai_move()` dispatcher
4. Update `plugin.json` metadata

```python
def _make_ai_move(self, session):
    difficulty = session.current_state.get("ai_difficulty", "medium")
    if difficulty == "expert":
        return self._get_expert_move(board, ai_symbol)
    # ... existing code
```

#### Adding New Game Mode

To add a "Tournament" mode:

1. Add constant: `MODE_TOURNAMENT = "tournament"`
2. Update `start_session()` to initialize tournament state
3. Add validation logic in `validate_move()`
4. Update session state structure

**Reference**: `GAME_DEVELOPMENT_GUIDE.md` Section 6 for game mode patterns

#### Customizing Scoring

To modify score calculation:

1. Update `_calculate_score()` method in `main.py`
2. Adjust base score constants
3. Add/remove bonus conditions
4. Update credit multipliers

```python
def _calculate_score(self, session, result):
    base_score = 1500 if won else 1000  # Custom base
    if custom_condition:
        base_score += 300
    # ... existing bonus logic
```

### 🧪 Testing Your Changes

After modifying the plugin:

```bash
# 1. Test plugin loading
python -c "from app.games.core.plugin_manager import plugin_manager; \
           plugin_manager.discover_plugins(); \
           print(plugin_manager.registry.get_plugin('tic_tac_toe'))"

# 2. Test AI behavior
python -c "from app.games.plugins.tic_tac_toe.main import TicTacToeGame; \
           game = TicTacToeGame(); \
           game.initialize(); \
           session = game.start_session('test_user', {'game_mode': 'vs_ai'}); \
           print('Initial state:', session.current_state)"

# 3. Run integration tests
python -m pytest tests/test_games.py -k tic_tac_toe -v

# 4. Test multiplayer mode
# See FRONTEND_INTEGRATION_GUIDE.md for WebSocket testing
```

### 📖 Learning Resources

Use this plugin as a reference for:

- **Turn-based games**: Chess, Checkers, Connect Four
- **AI opponent implementation**: Any game with computer player
- **Multi-mode support**: Games with single/local/online play
- **State validation**: Input validation and game rule enforcement
- **Score calculation**: Complex scoring with bonuses and achievements

### 🐛 Common Development Issues

| Issue | Solution |
|-------|----------|
| AI not responding | Check `game_mode == "vs_ai"` in `validate_move()` |
| State not persisting | Sessions are in-memory; use MongoDB in production |
| Invalid move accepted | Verify `_is_valid_move()` logic |
| WebSocket not syncing | Ensure `game_mode == "online"` and room_id exists |
| Wrong player turn | Check `current_player` validation logic |

**Full troubleshooting guide**: `IMPLEMENTATION_NOTES.md` Section 10

### 🚀 Performance Considerations

- **Minimax**: Caches board evaluation (memoization possible)
- **Session Storage**: In-memory dict (replace with Redis/MongoDB for scale)
- **AI Response Time**: Hard AI takes ~10ms for Tic Tac Toe (acceptable for larger boards: use depth limiting)

**Full performance analysis**: `IMPLEMENTATION_NOTES.md` Section 9

### 📝 Contributing

When modifying this plugin:

1. Update `IMPLEMENTATION_NOTES.md` if changing algorithms or architecture
2. Update this README if changing user-facing features or APIs
3. Update `plugin.json` version using semantic versioning
4. Add tests for new features in `tests/test_games.py`
5. Follow patterns from `GAME_DEVELOPMENT_GUIDE.md`

---

**Quick Links:**
- [Backend Development Guide](../../../docs/GAME_DEVELOPMENT_GUIDE.md)
- [Frontend Integration Guide](../../../docs/FRONTEND_GAME_INTEGRATION_GUIDE.md)
- [Implementation Deep-Dive](IMPLEMENTATION_NOTES.md)
- [Contributing Guidelines](../../../CONTRIBUTING.md)
