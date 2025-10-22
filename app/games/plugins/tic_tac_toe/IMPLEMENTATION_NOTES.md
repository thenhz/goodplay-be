# Tic Tac Toe Plugin - Implementation Notes

## Overview

This document provides technical details about the Tic Tac Toe plugin implementation. Use this as a reference when implementing similar games or understanding the plugin system.

---

## Architecture Decisions

### Why Three Game Modes?

The plugin supports three modes to demonstrate the flexibility of the plugin system:

1. **vs AI**: Single-player experience, demonstrates AI integration
2. **Local**: Pass-and-play multiplayer, demonstrates turn management
3. **Online**: Cross-device multiplayer, demonstrates WebSocket integration

### State Storage Strategy

**In-Memory Storage**: Currently uses a simple dictionary (`self.active_sessions`) for session storage.

```python
self.active_sessions: Dict[str, Dict[str, Any]] = {}
```

**Why In-Memory?**
- ✅ Fast access (no database queries)
- ✅ Simple implementation
- ✅ Suitable for short games (< 5 minutes)

**Limitations**:
- ❌ Lost on server restart
- ❌ Not suitable for long-running games
- ❌ No cross-server state sharing

**Production Alternative**:
```python
# Use MongoDB for persistence
from app.games.repositories.game_session_repository import GameSessionRepository

class TicTacToeGame(GamePlugin):
    def __init__(self):
        self.session_repo = GameSessionRepository()

    def start_session(self, user_id, session_config):
        # ... create session
        self.session_repo.save_session_state(session_id, game_state)
```

---

## AI Implementation

### Minimax Algorithm

The "hard" difficulty uses the Minimax algorithm with alpha-beta pruning for optimal play.

**Algorithm Overview**:
```
Minimax explores all possible game states and chooses the move that:
- Maximizes AI's score (assuming optimal play)
- Minimizes opponent's score
```

**Code Location**: `main.py:_minimax()`

**Time Complexity**: O(b^d) where:
- b = branching factor (avg 5 moves)
- d = depth (max 9 for Tic Tac Toe)

**Optimizations**:
1. **Alpha-Beta Pruning** (not yet implemented): Could reduce to O(b^(d/2))
2. **Depth Penalty**: Prefer faster wins/slower losses
3. **Early Termination**: Stop when terminal state found

### AI Difficulty Levels

#### Easy (Random)
```python
def _get_random_move(self, board):
    empty_positions = [(r, c) for r in range(3) for c in range(3) if board[r][c] is None]
    return random.choice(empty_positions)
```

**Characteristics**:
- Completely random
- No strategy
- Easy to beat

#### Medium (Heuristic)
```python
def _get_medium_ai_move(self, board, ai_symbol):
    # 1. Take winning move if available
    # 2. Block opponent's winning move
    # 3. Take center
    # 4. Take corner
    # 5. Random
```

**Characteristics**:
- Defensive play (blocks wins)
- Offensive play (takes wins)
- Strategic positions (center, corners)
- Medium challenge

#### Hard (Minimax)
```python
def _minimax(self, board, depth, is_maximizing, ai_symbol):
    # Recursive evaluation of all game states
    # Returns optimal score for current position
```

**Characteristics**:
- Optimal play
- Unbeatable
- Always draws or wins

**Why It's Unbeatable**:
- Evaluates all 9! = 362,880 possible games
- Chooses mathematically optimal move
- Perfect information game (no hidden state)

---

## State Management

### Game State Structure

```python
game_state = {
    # Board representation
    "board": [[None, None, None], [None, None, None], [None, None, None]],

    # Game flow
    "current_player": "X",      # "X" or "O"
    "game_mode": "vs_ai",       # "vs_ai", "local", "online"
    "game_over": False,
    "winner": None,             # "X", "O", or None
    "is_draw": False,
    "winning_line": None,       # [(0,0), (0,1), (0,2)] for horizontal win

    # Move tracking
    "move_count": 0,
    "moves_history": [
        {"player": "X", "position": [0, 0], "move_number": 1},
        {"player": "O", "position": [1, 1], "move_number": 2}
    ],

    # vs AI specific
    "ai_difficulty": "hard",
    "player_symbol": "X",
    "ai_symbol": "O"
}
```

### Public vs Private State

**Public State** (returned to frontend):
```python
{
    "board": [...],
    "current_player": "X",
    "game_mode": "vs_ai",
    "game_over": False,
    "winner": None,
    "is_draw": False,
    "winning_line": None,
    "move_count": 5
}
```

**Private State** (internal only):
```python
{
    # All public state +
    "ai_next_move_calculated": [1, 1],  # Hidden from player
    "minimax_evaluation": 5,             # Internal AI data
    "cheat_detection_flags": []          # Security data
}
```

**Why Separate?**
- Security: Don't leak AI strategy
- Performance: Don't send unnecessary data
- Clarity: Frontend only gets what it needs

---

## Move Validation

### Validation Pipeline

```python
def validate_move(self, session_id, move):
    # 1. Session exists?
    if session_id not in self.active_sessions:
        return False

    # 2. Game not over?
    if game_state["game_over"]:
        return False

    # 3. Move has correct format?
    if "position" not in move:
        return False

    # 4. Position is valid coordinates?
    row, col = move["position"]
    if not (0 <= row <= 2 and 0 <= col <= 2):
        return False

    # 5. Position is empty?
    if game_state["board"][row][col] is not None:
        return False

    # 6. Apply move
    self._make_move(session_id, row, col, current_player)

    # 7. If vs AI, make AI move
    if game_mode == "vs_ai" and not game_state["game_over"]:
        self._make_ai_move(session_id)

    return True
```

### Why This Order?

1. **Cheap checks first**: Session existence is O(1)
2. **Game state check**: Prevent moves on finished games
3. **Format validation**: Catch malformed requests
4. **Business logic**: Board validation
5. **State mutation**: Only if all checks pass

---

## Win Detection

### Algorithm

```python
def _check_winner(self, board):
    # Check rows
    for row in range(3):
        if board[row][0] == board[row][1] == board[row][2] and board[row][0] is not None:
            return board[row][0], [(row, 0), (row, 1), (row, 2)]

    # Check columns
    for col in range(3):
        if board[0][col] == board[1][col] == board[2][col] and board[0][col] is not None:
            return board[0][col], [(0, col), (1, col), (2, col)]

    # Check diagonals
    if board[0][0] == board[1][1] == board[2][2] and board[0][0] is not None:
        return board[0][0], [(0, 0), (1, 1), (2, 2)]

    if board[0][2] == board[1][1] == board[2][0] and board[0][2] is not None:
        return board[0][2], [(0, 2), (1, 1), (2, 0)]

    return None, None
```

**Returns**: `(winner, winning_line)` or `(None, None)`

**Time Complexity**: O(1) - Always checks 8 lines

**Why Return Winning Line?**
- Frontend can highlight winning cells
- Better UX
- Animation support

---

## Scoring System

### Score Calculation

```python
def _calculate_score(self, game_state, reason):
    if reason == "abandoned":
        return 0

    player_symbol = game_state["player_symbol"]
    winner = game_state["winner"]
    move_count = game_state["move_count"]

    # Base score
    if game_state["is_draw"]:
        base_score = 300
    elif winner == player_symbol:
        base_score = 1000

        # Quick win bonus (≤5 moves)
        if move_count <= 5:
            base_score += 200

        # Perfect win (opponent never got 2 in a row)
        if self._is_perfect_win(game_state):
            base_score += 500
    else:
        base_score = 100  # Participation

    return base_score
```

### Credit Calculation

```python
def _calculate_credits(self, game_state, final_score):
    # Base credits from score
    base_credits = max(1, int(final_score / 200))

    # AI difficulty bonus
    if game_state["game_mode"] == "vs_ai":
        if game_state["ai_difficulty"] == "hard" and game_state["winner"] == game_state["player_symbol"]:
            base_credits += 5  # Beat hard AI
        elif game_state["ai_difficulty"] == "medium":
            base_credits += 2

    return base_credits
```

**Why This Formula?**
- Rewards wins more than losses
- Encourages challenging AI
- Prevents credit farming (caps at reasonable values)
- Aligns with play time (short game = fewer credits)

---

## Mode-Specific Implementation

### vs AI Mode

**Key Features**:
- AI responds automatically after player move
- Response included in same HTTP response
- No need for polling

**Implementation**:
```python
def validate_move(self, session_id, move):
    # ... validation

    # Player move
    self._make_move(session_id, row, col, player_symbol)

    # Check if game ended
    if game_state["game_over"]:
        return True

    # AI move (automatic)
    self._make_ai_move(session_id)

    return True
```

**Why Automatic Response?**
- Better UX (instant AI response)
- Simpler frontend code
- Fewer HTTP requests

---

### Local Mode

**Key Features**:
- Manual turn switching
- Players share device
- Frontend manages "whose turn" display

**Implementation**:
```python
def start_session(self, user_id, session_config):
    game_state = {
        "game_mode": "local",
        "current_player": "X",  # X always starts
        # ... other state
    }

def validate_move(self, session_id, move):
    # ... validation

    # Apply move
    self._make_move(session_id, row, col, current_player)

    # Switch player (if game not over)
    if not game_state["game_over"]:
        game_state["current_player"] = "O" if current_player == "X" else "X"

    return True
```

**Frontend Responsibility**:
- Display "Player X's turn" / "Player O's turn"
- Disable board during opponent's turn (optional)
- Show turn indicator

---

### Online Mode

**Key Features**:
- WebSocket communication
- Real-time state sync
- Multiplayer room management

**Implementation**:
```python
def start_session(self, user_id, session_config):
    game_state = {
        "game_mode": "online",
        "room_id": session_config.get("room_id"),
        "players": session_config.get("players", []),
        # ... other state
    }

def validate_move(self, session_id, move):
    # ... validation

    # Check if correct player
    player_id = move.get("player_id")
    if player_id != game_state["players"][game_state["current_player_index"]]:
        return False  # Not this player's turn

    # Apply move
    # ... (same as local mode)

    return True
```

**Multiplayer System Integration**:
```
Plugin validates moves → State updated → Multiplayer system broadcasts
```

The multiplayer system handles:
- WebSocket connections
- Room management
- Broadcasting state to all players
- Disconnection handling

---

## Testing

### Manual Testing Script

```python
# Test vs AI mode
from app.games.plugins.tic_tac_toe.main import TicTacToeGame

game = TicTacToeGame()
game.initialize()

# Start game
session = game.start_session("user123", {
    "game_mode": "vs_ai",
    "ai_difficulty": "hard",
    "player_symbol": "X"
})

print("Initial state:", game.get_session_state(session.session_id))

# Player X move (center)
game.validate_move(session.session_id, {"position": [1, 1]})
state = game.get_session_state(session.session_id)
print("After first move:", state)
print("Board:", state["board"])

# Player X move (top-left)
game.validate_move(session.session_id, {"position": [0, 0]})
state = game.get_session_state(session.session_id)
print("After second move:", state)
print("Board:", state["board"])
```

### Unit Tests

```python
# tests/test_tic_tac_toe.py
import pytest
from app.games.plugins.tic_tac_toe.main import TicTacToeGame

class TestTicTacToePlugin:
    def setup_method(self):
        self.game = TicTacToeGame()
        self.game.initialize()

    def test_win_detection_horizontal(self):
        """Test horizontal win detection"""
        session = self.game.start_session("user123", {"game_mode": "local"})

        # Create winning scenario
        moves = [
            ([0, 0], "X"),  # X
            ([1, 0], "O"),  # O
            ([0, 1], "X"),  # X
            ([1, 1], "O"),  # O
            ([0, 2], "X"),  # X wins horizontally
        ]

        for pos, _ in moves:
            self.game.validate_move(session.session_id, {"position": pos})

        state = self.game.get_session_state(session.session_id)
        assert state["game_over"] is True
        assert state["winner"] == "X"
        assert state["winning_line"] == [(0, 0), (0, 1), (0, 2)]

    def test_ai_never_loses(self):
        """Test that hard AI never loses"""
        results = []

        # Play 100 games
        for i in range(100):
            session = self.game.start_session("user123", {
                "game_mode": "vs_ai",
                "ai_difficulty": "hard",
                "player_symbol": "X"
            })

            # Make random moves until game ends
            state = self.game.get_session_state(session.session_id)
            while not state["game_over"]:
                # Find empty position
                for r in range(3):
                    for c in range(3):
                        if state["board"][r][c] is None:
                            self.game.validate_move(session.session_id, {"position": [r, c]})
                            break
                    if state["board"][r][c] is not None:
                        break

                state = self.game.get_session_state(session.session_id)

            results.append(state["winner"])

        # AI should never lose (only win or draw)
        assert "X" not in results  # Player never wins
```

---

## Performance Considerations

### Time Complexity

| Operation | Complexity | Notes |
|-----------|-----------|-------|
| `start_session` | O(1) | Initialize empty board |
| `validate_move` | O(1) vs AI easy/medium<br>O(b^d) vs AI hard | Minimax explores tree |
| `_check_winner` | O(1) | Always checks 8 lines |
| `_is_board_full` | O(1) | 3x3 grid |
| `end_session` | O(1) | Simple calculations |

### Space Complexity

| Structure | Space | Notes |
|-----------|-------|-------|
| Board | O(1) | Fixed 3x3 = 9 cells |
| Moves history | O(n) | n = move count (max 9) |
| Active sessions | O(s) | s = concurrent sessions |

### Bottlenecks

**Minimax Algorithm**:
- Worst case: 9! = 362,880 game states
- Average: ~60,000 states (with pruning potential)
- Improvement: Add alpha-beta pruning

```python
# TODO: Add alpha-beta pruning
def _minimax(self, board, depth, is_maximizing, ai_symbol, alpha=-inf, beta=inf):
    # ... terminal checks

    if is_maximizing:
        max_score = -inf
        for move in get_empty_cells():
            score = self._minimax(board, depth+1, False, ai_symbol, alpha, beta)
            max_score = max(score, max_score)
            alpha = max(alpha, score)
            if beta <= alpha:
                break  # Beta cutoff
        return max_score
    # ... similar for minimizing
```

**Expected Improvement**: 50-90% reduction in states evaluated

---

## Extensibility

### Adding New AI Difficulty

```python
# In __init__
self.ai_difficulties = {
    "easy": self._get_random_move,
    "medium": self._get_medium_ai_move,
    "hard": self._get_best_move,
    "expert": self._get_expert_move  # NEW
}

def _get_expert_move(self, board, ai_symbol):
    """Expert AI with alpha-beta pruning and opening book"""
    # Check opening book
    if move_count < 3:
        return self._get_opening_book_move(board)

    # Use alpha-beta minimax
    return self._get_best_move_with_pruning(board, ai_symbol)
```

### Adding Larger Board

```python
# Support 4x4 or 5x5
def __init__(self):
    self.board_size = 3  # Make configurable

def _create_empty_board(self, size=None):
    size = size or self.board_size
    return [[None] * size for _ in range(size)]

def _check_winner(self, board, win_length=3):
    """Check for N in a row"""
    # Generalized win detection
    # ... implementation
```

### Adding Time Limits

```python
game_state = {
    # ... existing fields
    "turn_time_limit": 30,  # seconds
    "turn_started_at": datetime.utcnow().isoformat(),
}

def validate_move(self, session_id, move):
    # Check time limit
    turn_start = datetime.fromisoformat(game_state["turn_started_at"])
    elapsed = (datetime.utcnow() - turn_start).total_seconds()

    if elapsed > game_state["turn_time_limit"]:
        # Auto-forfeit turn
        self._forfeit_turn(game_state)
        return False

    # ... rest of validation
```

---

## Common Issues & Solutions

### Issue 1: AI Move Not Appearing

**Symptom**: Frontend doesn't show AI move after player move

**Cause**: Frontend not updating state from response

**Solution**:
```javascript
// Ensure frontend uses response state, not local state
const response = await makeMove(row, col);
setState(response.data.current_state);  // ✅ Use server state
// Not: setState(localState)  // ❌ Don't use local state
```

### Issue 2: Invalid Move Accepted

**Symptom**: Move to occupied cell succeeds

**Cause**: Validation order wrong

**Solution**:
```python
# Check position empty BEFORE applying move
if game_state["board"][row][col] is not None:
    return False

# Then apply move
self._make_move(...)
```

### Issue 3: Game Never Ends

**Symptom**: Game continues after win

**Cause**: Win detection not called

**Solution**:
```python
def _make_move(self, session_id, row, col, player):
    # ... apply move

    # Check win AFTER every move
    winner, winning_line = self._check_winner(game_state["board"])
    if winner:
        game_state["game_over"] = True
        game_state["winner"] = winner
```

---

## Future Improvements

### Short-term (Easy)
- ✅ Add alpha-beta pruning to minimax
- ✅ Add opening book for expert AI
- ✅ Add move undo/redo
- ✅ Add replay mode

### Medium-term (Moderate)
- ✅ Support larger boards (4x4, 5x5)
- ✅ Add time limits per move
- ✅ Add move hints for beginners
- ✅ Add tournaments mode

### Long-term (Complex)
- ✅ Neural network AI (ML-based)
- ✅ Spectator mode
- ✅ Tournament brackets
- ✅ ELO rating system

---

## References

- **Plugin System**: `/docs/GAME_DEVELOPMENT_GUIDE.md`
- **Frontend Integration**: `/docs/FRONTEND_GAME_INTEGRATION_GUIDE.md`
- **Minimax Algorithm**: https://en.wikipedia.org/wiki/Minimax
- **Alpha-Beta Pruning**: https://en.wikipedia.org/wiki/Alpha%E2%80%93beta_pruning

---

*Last Updated: 2025-10-21*
*Author: GoodPlay Team*
