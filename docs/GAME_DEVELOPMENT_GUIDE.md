# Game Development Guide - GoodPlay Backend

## Table of Contents

1. [Introduction](#introduction)
2. [Plugin System Architecture](#plugin-system-architecture)
3. [Quick Start](#quick-start)
4. [Plugin Implementation](#plugin-implementation)
5. [Game Modes & Patterns](#game-modes--patterns)
6. [API Reference](#api-reference)
7. [Integration Points](#integration-points)
8. [Best Practices](#best-practices)
9. [Testing](#testing)
10. [Deployment](#deployment)

---

## Introduction

### What is the Game Plugin System?

GoodPlay uses a **plugin architecture** to add games to the platform without modifying core code. Each game is a self-contained module that implements the `GamePlugin` interface.

**Benefits**:
- ✅ **Isolation**: Game logic is separate from platform code
- ✅ **Security**: Plugins are validated before loading
- ✅ **Flexibility**: Easy to add/remove games
- ✅ **Standardization**: All games follow the same interface
- ✅ **Auto-discovery**: Plugins are automatically loaded on startup

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    GoodPlay Platform                         │
│                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐ │
│  │   Frontend   │    │   Backend    │    │   Database   │ │
│  │  (React/Vue) │◄──►│   (Flask)    │◄──►│  (MongoDB)   │ │
│  └──────────────┘    └───────┬──────┘    └──────────────┘ │
│                              │                              │
│                              ▼                              │
│                  ┌───────────────────────┐                 │
│                  │   Plugin System       │                 │
│                  ├───────────────────────┤                 │
│                  │ - Plugin Registry     │                 │
│                  │ - Plugin Manager      │                 │
│                  │ - Session Management  │                 │
│                  └──────────┬────────────┘                 │
│                             │                              │
│              ┌──────────────┼──────────────┐              │
│              ▼              ▼               ▼              │
│         ┌────────┐    ┌────────┐     ┌────────┐          │
│         │ Plugin │    │ Plugin │     │ Plugin │          │
│         │   1    │    │   2    │     │   3    │          │
│         │ (TicTac│    │(Number │     │ (Your  │          │
│         │  Toe)  │    │Guess)  │     │ Game)  │          │
│         └────────┘    └────────┘     └────────┘          │
└─────────────────────────────────────────────────────────────┘
```

### When to Create a Plugin

Create a game plugin when:
- ✅ Implementing a new game
- ✅ Game has custom logic and rules
- ✅ Game needs session management
- ✅ Game calculates credits based on play time
- ✅ Game can be played in multiple modes

**Don't use plugins for**:
- ❌ Simple configuration changes
- ❌ Games that are just UI variants
- ❌ External game integration (use API wrapper instead)

---

## Plugin System Architecture

### Core Components

```
app/games/
├── core/
│   ├── game_plugin.py         # Base plugin interface (ABSTRACT)
│   ├── plugin_manager.py      # Plugin discovery/loading/lifecycle
│   └── plugin_registry.py     # Plugin registration and retrieval
├── plugins/
│   └── {game_name}/
│       ├── __init__.py        # Python package marker
│       ├── plugin.json        # Manifest (metadata)
│       └── main.py            # Plugin implementation
├── models/
│   └── game_session.py        # Session model
├── services/
│   └── game_session_service.py # Session management
├── repositories/
│   └── game_session_repository.py # Database access
└── controllers/
    └── games_controller.py    # REST API endpoints
```

### Plugin Lifecycle

```
1. DISCOVERY
   Plugin Manager scans app/games/plugins/
   ↓
2. VALIDATION
   Checks plugin.json schema
   Validates required fields
   ↓
3. REGISTRATION
   Plugin Registry stores plugin metadata
   Instantiates plugin class
   ↓
4. INITIALIZATION
   Plugin.initialize() called
   Plugin sets is_initialized = True
   ↓
5. READY
   Plugin available for session creation
   ↓
6. RUNTIME
   Sessions created/managed
   Plugin methods called
   ↓
7. UNLOAD (optional)
   Plugin unregistered
   Resources cleaned up
```

### Data Flow

```
HTTP Request (Frontend)
    ↓
Games Controller
    ↓
Game Session Service  ───┐
    ↓                    │
Plugin Registry          │  (Validation, Business Logic)
    ↓                    │
Game Plugin             ←┘
    ↓
Plugin Response
    ↓
Session Repository
    ↓
MongoDB
    ↓
HTTP Response (Frontend)
```

---

## Quick Start

### Create Your First Game Plugin

Let's create a simple "Coin Flip" game.

#### Step 1: Create Directory Structure

```bash
cd app/games/plugins
mkdir coin_flip
cd coin_flip
touch __init__.py plugin.json main.py
```

#### Step 2: Create plugin.json

```json
{
  "id": "coin_flip",
  "name": "Coin Flip",
  "version": "1.0.0",
  "description": "Simple coin flip game - guess heads or tails",
  "author": "Your Name",
  "category": "luck",
  "main_module": "main",
  "dependencies": {
    "python_packages": [],
    "plugins": []
  },
  "metadata": {
    "min_players": 1,
    "max_players": 1,
    "estimated_duration_minutes": 1,
    "difficulty_level": "easy",
    "requires_internet": false,
    "credit_rate": 0.2
  }
}
```

#### Step 3: Implement Plugin (main.py)

```python
import random
import uuid
from typing import Dict, Any, Optional
from datetime import datetime

from app.games.core.game_plugin import GamePlugin, GameRules, GameSession, SessionResult


class CoinFlipGame(GamePlugin):
    """Simple coin flip game plugin"""

    def __init__(self):
        super().__init__()
        self.name = "Coin Flip"
        self.version = "1.0.0"
        self.description = "Guess heads or tails"
        self.category = "luck"
        self.author = "Your Name"
        self.credit_rate = 0.2

        # Active sessions storage
        self.active_sessions: Dict[str, Dict[str, Any]] = {}

    def initialize(self) -> bool:
        """Initialize the plugin"""
        try:
            self.is_initialized = True
            return True
        except Exception as e:
            print(f"Failed to initialize CoinFlipGame: {e}")
            return False

    def start_session(self, user_id: str, session_config: Optional[Dict[str, Any]] = None) -> GameSession:
        """Start a new game session"""
        session_id = str(uuid.uuid4())

        # Initialize game state
        game_state = {
            "guess": None,
            "result": None,
            "game_over": False,
            "won": False
        }

        self.active_sessions[session_id] = game_state

        # Create session object
        session = GameSession(
            session_id=session_id,
            user_id=user_id,
            game_id="coin_flip",
            status="active",
            current_state={
                "message": "Make your guess: heads or tails",
                "guess_made": False
            },
            started_at=datetime.utcnow()
        )

        return session

    def end_session(self, session_id: str, reason: str = "completed") -> SessionResult:
        """End a game session"""
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")

        game_state = self.active_sessions[session_id]

        # Calculate score
        final_score = 1000 if game_state["won"] else 0
        credits_earned = 1 if game_state["won"] else 0

        # Achievements
        achievements = []
        if game_state["won"]:
            achievements.append("LUCKY_GUESS")

        result = SessionResult(
            session_id=session_id,
            final_score=final_score,
            credits_earned=credits_earned,
            completion_time_seconds=60,
            achievements_unlocked=achievements,
            statistics={
                "guess": game_state["guess"],
                "result": game_state["result"],
                "won": game_state["won"]
            }
        )

        # Cleanup
        del self.active_sessions[session_id]

        return result

    def get_rules(self) -> GameRules:
        """Get game rules"""
        return GameRules(
            min_players=1,
            max_players=1,
            estimated_duration_minutes=1,
            difficulty_level="easy",
            requires_internet=False,
            description="Guess heads or tails!",
            instructions="Make your guess and flip the coin. Win if you guess correctly!"
        )

    def validate_move(self, session_id: str, move: Dict[str, Any]) -> bool:
        """Validate and process a move"""
        if session_id not in self.active_sessions:
            return False

        game_state = self.active_sessions[session_id]

        if game_state["game_over"]:
            return False

        # Validate move format
        if "guess" not in move:
            return False

        guess = move["guess"].lower()
        if guess not in ["heads", "tails"]:
            return False

        # Flip coin
        result = random.choice(["heads", "tails"])

        # Update state
        game_state["guess"] = guess
        game_state["result"] = result
        game_state["won"] = (guess == result)
        game_state["game_over"] = True

        return True

    def get_session_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get current session state"""
        if session_id not in self.active_sessions:
            return None

        game_state = self.active_sessions[session_id]

        return {
            "guess": game_state["guess"],
            "result": game_state["result"],
            "game_over": game_state["game_over"],
            "won": game_state["won"],
            "message": "You won!" if game_state["won"] else "You lost!" if game_state["game_over"] else "Make your guess"
        }

    def update_session_state(self, session_id: str, new_state: Dict[str, Any]) -> bool:
        """Update session state"""
        if session_id not in self.active_sessions:
            return False

        # No custom state updates needed for this game
        return True


# Export plugin class
GamePluginClass = CoinFlipGame
```

#### Step 4: Test Plugin

```python
# Test in Python console
from app.games.plugins.coin_flip.main import CoinFlipGame

game = CoinFlipGame()
game.initialize()

# Start session
session = game.start_session("user123")
print(f"Session ID: {session.session_id}")

# Make guess
game.validate_move(session.session_id, {"guess": "heads"})

# Get result
state = game.get_session_state(session.session_id)
print(f"Result: {state}")

# End session
result = game.end_session(session.session_id)
print(f"Won: {result.statistics['won']}, Score: {result.final_score}")
```

#### Step 5: Plugin Auto-Discovery

```python
# The plugin is automatically discovered on app startup
# Or manually trigger discovery:

from app.games.core.plugin_manager import plugin_manager

discovered = plugin_manager.discover_plugins()
print(f"Discovered plugins: {discovered}")
# Output: ['coin_flip', 'tic_tac_toe', 'example_game']

# Get plugin from registry
from app.games.core.plugin_registry import plugin_registry

coin_flip = plugin_registry.get_plugin('coin_flip')
print(f"Plugin loaded: {coin_flip.name}")
```

---

## Plugin Implementation

### GamePlugin Base Class

All game plugins must extend `GamePlugin` and implement **6 abstract methods**:

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime

class GamePlugin(ABC):
    """Base class for all game plugins"""

    def __init__(self):
        self.name: str = ""                    # Game name
        self.version: str = ""                 # Plugin version
        self.description: str = ""             # Short description
        self.category: str = ""                # Category (puzzle, action, etc.)
        self.author: str = ""                  # Plugin author
        self.credit_rate: float = 1.0          # Credits per minute
        self.is_initialized: bool = False      # Initialization status

    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the plugin. Called once on load."""
        pass

    @abstractmethod
    def start_session(self, user_id: str, session_config: Optional[Dict[str, Any]] = None) -> GameSession:
        """Start a new game session for a user."""
        pass

    @abstractmethod
    def end_session(self, session_id: str, reason: str = "completed") -> SessionResult:
        """End an active game session."""
        pass

    @abstractmethod
    def get_rules(self) -> GameRules:
        """Get the rules and metadata for this game."""
        pass

    @abstractmethod
    def validate_move(self, session_id: str, move: Dict[str, Any]) -> bool:
        """Validate and process a player's move."""
        pass

    @abstractmethod
    def get_session_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get the current state of a game session."""
        pass

    @abstractmethod
    def update_session_state(self, session_id: str, new_state: Dict[str, Any]) -> bool:
        """Update the state of a game session."""
        pass
```

### Method Implementation Guide

#### 1. `initialize()` - Plugin Setup

**Purpose**: One-time setup when plugin is loaded.

**When Called**: During plugin discovery/registration.

**Implementation**:
```python
def initialize(self) -> bool:
    """Initialize the plugin"""
    try:
        # Load resources
        self.game_data = self._load_game_data()

        # Setup connections if needed
        # self.external_api = ExternalAPI()

        # Validate configuration
        if not self._validate_config():
            return False

        self.is_initialized = True
        return True

    except Exception as e:
        current_app.logger.error(f"Plugin init failed: {str(e)}")
        return False
```

**Best Practices**:
- ✅ Keep initialization fast (< 1 second)
- ✅ Validate all required resources
- ✅ Log errors clearly
- ✅ Return `False` on failure
- ❌ Don't make network calls
- ❌ Don't load large files synchronously

---

#### 2. `start_session()` - Create Game Instance

**Purpose**: Create a new game instance for a user.

**When Called**: User starts a new game via `POST /api/games/sessions`.

**Parameters**:
- `user_id`: The user's ID (string)
- `session_config`: Optional configuration (dict)

**Returns**: `GameSession` object

**Implementation**:
```python
def start_session(self, user_id: str, session_config: Optional[Dict[str, Any]] = None) -> GameSession:
    """Start a new game session"""
    session_config = session_config or {}
    session_id = str(uuid.uuid4())

    # Parse configuration
    game_mode = session_config.get("game_mode", "single_player")
    difficulty = session_config.get("difficulty", "medium")

    # Initialize game state
    game_state = {
        "level": 1,
        "score": 0,
        "lives": 3,
        "game_mode": game_mode,
        "difficulty": difficulty,
        "game_over": False,
        "started_at": datetime.utcnow().isoformat()
    }

    # Store session (in-memory or database)
    self.active_sessions[session_id] = game_state

    # Create session object
    session = GameSession(
        session_id=session_id,
        user_id=user_id,
        game_id="your_game",
        status="active",
        current_state=self._get_public_state(game_state),
        started_at=datetime.utcnow()
    )

    return session
```

**session_config Common Keys**:
```python
{
    "game_mode": "vs_ai" | "local" | "online",
    "difficulty": "easy" | "medium" | "hard",
    "player_count": 1-8,
    "time_limit": 300,  # seconds
    "custom_settings": {...}
}
```

**Best Practices**:
- ✅ Validate `session_config` parameters
- ✅ Generate unique `session_id` (use `uuid.uuid4()`)
- ✅ Store session state (in-memory dict or database)
- ✅ Return minimal state in `current_state` (no sensitive data)
- ❌ Don't start game immediately (wait for first move)
- ❌ Don't include internal state in `current_state`

---

#### 3. `end_session()` - Calculate Results

**Purpose**: End a session and calculate final results.

**When Called**:
- Game completes naturally
- User abandons game
- Session times out

**Parameters**:
- `session_id`: Session to end
- `reason`: "completed", "abandoned", "timeout"

**Returns**: `SessionResult` object

**Implementation**:
```python
def end_session(self, session_id: str, reason: str = "completed") -> SessionResult:
    """End a game session"""
    if session_id not in self.active_sessions:
        raise ValueError(f"Session {session_id} not found")

    game_state = self.active_sessions[session_id]

    # Calculate final score
    final_score = self._calculate_score(game_state, reason)

    # Calculate credits based on time and performance
    play_duration = self._get_play_duration(game_state)
    credits_earned = self._calculate_credits(play_duration, final_score)

    # Determine achievements
    achievements = self._check_achievements(game_state)

    # Create result
    result = SessionResult(
        session_id=session_id,
        final_score=final_score,
        credits_earned=credits_earned,
        completion_time_seconds=int(play_duration.total_seconds()),
        achievements_unlocked=achievements,
        statistics={
            "reason": reason,
            "level_reached": game_state["level"],
            "high_score": game_state["score"],
            "accuracy": self._calculate_accuracy(game_state)
        }
    )

    # Cleanup
    del self.active_sessions[session_id]

    return result
```

**Score Calculation**:
```python
def _calculate_score(self, game_state: Dict, reason: str) -> int:
    """Calculate final score"""
    if reason == "abandoned":
        return 0

    base_score = game_state["score"]

    # Bonuses
    if game_state["lives"] > 0:
        base_score += game_state["lives"] * 100

    if game_state["level"] >= 10:
        base_score += 500  # Level bonus

    # Time bonus
    play_time = (datetime.utcnow() - datetime.fromisoformat(game_state["started_at"])).total_seconds()
    if play_time < 60:
        base_score += 200  # Speed bonus

    return int(base_score)
```

**Credit Calculation**:
```python
def _calculate_credits(self, play_duration: timedelta, final_score: int) -> int:
    """Calculate credits earned"""
    # Base credits from time played
    minutes_played = play_duration.total_seconds() / 60
    base_credits = int(minutes_played * self.credit_rate)

    # Performance multiplier (0.5x to 2.0x)
    if final_score > 10000:
        multiplier = 2.0
    elif final_score > 5000:
        multiplier = 1.5
    elif final_score > 1000:
        multiplier = 1.0
    else:
        multiplier = 0.5

    return int(base_credits * multiplier)
```

**Best Practices**:
- ✅ Clean up session data after ending
- ✅ Calculate credits fairly based on actual play time
- ✅ Provide detailed statistics
- ✅ Handle all `reason` cases
- ❌ Don't allow negative scores/credits
- ❌ Don't forget to delete session data

---

#### 4. `get_rules()` - Game Metadata

**Purpose**: Provide game rules and metadata.

**When Called**: Frontend requests game info.

**Returns**: `GameRules` object

**Implementation**:
```python
def get_rules(self) -> GameRules:
    """Get game rules"""
    return GameRules(
        min_players=1,
        max_players=4,
        estimated_duration_minutes=10,
        difficulty_level="medium",
        requires_internet=False,
        description="Solve puzzles to progress through levels",
        instructions="""
# Your Game Rules

## Objective
Reach the highest level by solving puzzles.

## How to Play
1. Start a new game
2. Solve the puzzle by making moves
3. Complete all puzzles to win

## Scoring
- Base score: 100 points per puzzle
- Time bonus: +50 points if under 30 seconds
- Combo bonus: +25 points per consecutive correct move

## Move Format
Send moves as: {"action": "move", "data": {"x": 0, "y": 0}}

Example: {"action": "select", "data": {"tile_id": 5}}
        """
    )
```

**Best Practices**:
- ✅ Write clear, concise instructions
- ✅ Include move format examples
- ✅ Explain scoring system
- ✅ Use Markdown for formatting
- ✅ Set accurate duration estimate

---

#### 5. `validate_move()` - Process Player Actions

**Purpose**: Validate and process a player's move/action.

**When Called**: User makes a move via `POST /api/games/sessions/{id}/move`.

**Parameters**:
- `session_id`: Active session
- `move`: Move data (dict)

**Returns**: `bool` (True if valid, False otherwise)

**Implementation**:
```python
def validate_move(self, session_id: str, move: Dict[str, Any]) -> bool:
    """Validate and process a move"""
    if session_id not in self.active_sessions:
        return False

    game_state = self.active_sessions[session_id]

    # Check if game is over
    if game_state["game_over"]:
        return False

    # Validate move format
    if not self._validate_move_format(move):
        return False

    # Game-specific validation
    if not self._is_valid_move(game_state, move):
        return False

    # Apply move
    self._apply_move(game_state, move)

    # Check win condition
    if self._check_win_condition(game_state):
        game_state["game_over"] = True
        game_state["winner"] = game_state["current_player"]

    # Check lose condition
    if self._check_lose_condition(game_state):
        game_state["game_over"] = True
        game_state["winner"] = None

    return True
```

**Move Format Examples**:
```python
# Tic Tac Toe
{
    "position": [row, col]  # [0-2, 0-2]
}

# Card Game
{
    "action": "play_card",
    "card_id": "ace_spades",
    "target": "player_2"
}

# Platformer
{
    "action": "jump",
    "position": {"x": 100, "y": 200},
    "velocity": {"x": 5, "y": 10}
}

# Chess
{
    "from": "e2",
    "to": "e4",
    "piece": "pawn"
}
```

**Best Practices**:
- ✅ Validate move format first
- ✅ Check game state (not over, valid turn, etc.)
- ✅ Apply move atomically (all or nothing)
- ✅ Update game state after successful move
- ✅ Return `False` for invalid moves (don't throw exceptions)
- ❌ Don't modify state if move is invalid
- ❌ Don't return error messages (use logs)

---

#### 6. `get_session_state()` - Read Game State

**Purpose**: Get current game state for a session.

**When Called**:
- After each move (automatic)
- Frontend requests state update
- Cross-device synchronization

**Returns**: `Dict[str, Any]` with public state

**Implementation**:
```python
def get_session_state(self, session_id: str) -> Optional[Dict[str, Any]]:
    """Get current session state"""
    if session_id not in self.active_sessions:
        return None

    game_state = self.active_sessions[session_id]

    # Return only public state (hide internal data)
    return {
        "level": game_state["level"],
        "score": game_state["score"],
        "lives": game_state["lives"],
        "current_player": game_state.get("current_player"),
        "game_over": game_state["game_over"],
        "winner": game_state.get("winner"),

        # Game-specific state
        "board": game_state.get("board"),
        "available_moves": self._get_available_moves(game_state),

        # Don't include sensitive data:
        # - AI internal state
        # - Hidden cards
        # - Cheat detection flags
    }
```

**State Privacy Levels**:
```python
# PUBLIC - Always include
{
    "game_over": bool,
    "current_player": str,
    "score": int
}

# PLAYER_SPECIFIC - Only for this player
{
    "hand": [...],           # Cards in player's hand
    "private_resource": int  # Player's hidden resources
}

# HIDDEN - Never expose to frontend
{
    "ai_strategy": {...},
    "cheat_detection": {...},
    "rng_seed": int
}
```

**Best Practices**:
- ✅ Return only what frontend needs
- ✅ Hide opponent's private data
- ✅ Hide AI internal state
- ✅ Use consistent key names
- ❌ Don't include debugging info
- ❌ Don't return entire game_state

---

### 🚨 CRITICAL: State Synchronization Pattern

**Your `get_session_state()` method is the SOURCE OF TRUTH for game state.**

The platform automatically calls this method after EVERY game operation to sync the database with your plugin's internal state. This ensures:
- ✅ Database always reflects current game state
- ✅ API responses contain complete, up-to-date state
- ✅ Clients never need separate GET requests after operations
- ✅ Cross-device sync works correctly

#### When `get_session_state()` Is Called

The platform calls your `get_session_state()` method automatically after:

1. **`validate_move()`** - After recording a player move
   ```
   Player makes move → validate_move() → get_session_state() → DB update → Return complete session
   ```

2. **`pause_session()`** - After pausing a session
   ```
   Player pauses → pause in DB → get_session_state() → DB state update → Return session with current_state
   ```

3. **`resume_session()`** - After resuming a session
   ```
   Player resumes → resume in DB → get_session_state() → DB state update → Return session with current_state
   ```

4. **`GET /sessions/{id}`** - When client requests session details
   ```
   Client requests session → get_session_state() → DB sync → Return fresh state
   ```

5. **`update_session_state()`** - After validating external state update
   ```
   State update → update_session_state() → get_session_state() → DB update with validated state
   ```

#### Implementation Requirements

**✅ ALWAYS return fresh state**:
```python
def get_session_state(self, session_id: str) -> Optional[Dict[str, Any]]:
    """Get current session state - MUST return fresh, complete state"""
    if session_id not in self.active_sessions:
        return None

    game_state = self.active_sessions[session_id]

    # ✅ CORRECT: Calculate fresh state every time
    return {
        "board": game_state["board"],                      # Current board
        "current_player": game_state["current_player"],    # Current turn
        "game_over": self._check_game_over(game_state),    # Re-check game status
        "winner": self._determine_winner(game_state),      # Re-calculate winner
        "available_moves": self._get_valid_moves(game_state),  # Fresh move list
        "move_count": len(game_state["moves"])
    }
```

**❌ WRONG: Stale or incomplete state**:
```python
def get_session_state(self, session_id: str) -> Optional[Dict[str, Any]]:
    # ❌ WRONG: Returning cached state
    return self.cached_states.get(session_id)

    # ❌ WRONG: Missing critical fields
    return {
        "board": game_state["board"]
        # Missing: current_player, game_over, winner, etc.
    }

    # ❌ WRONG: Returning None when session exists
    if some_condition:
        return None  # Will cause DB sync to fail!
```

#### Common Mistakes to Avoid

**❌ Mistake 1: Returning cached/stale state**
```python
# BAD - State might be outdated
return self.state_cache[session_id]
```
**✅ Solution**: Always compute state from current game_state

**❌ Mistake 2: Returning incomplete state**
```python
# BAD - Missing game-specific fields
return {"score": 100}
```
**✅ Solution**: Include ALL fields frontend needs (board, current_player, game_over, winner, etc.)

**❌ Mistake 3: Returning None for existing sessions**
```python
# BAD - Will break state sync
if not self._some_flag:
    return None
```
**✅ Solution**: Only return None if session truly doesn't exist

**❌ Mistake 4: Expensive computations on every call**
```python
# BAD - Expensive AI analysis on every state request
def get_session_state(self, session_id: str):
    state = self.active_sessions[session_id]
    # This runs after EVERY operation!
    ai_analysis = self._run_expensive_ai_analysis(state)  # 2 seconds!
    return {"board": state["board"], "ai_hint": ai_analysis}
```
**✅ Solution**: Cache expensive computations, only recompute when game state actually changes

#### Performance Considerations

Since `get_session_state()` is called after every operation:

1. **Keep it fast** (< 10ms recommended)
   - Use cached computations where possible
   - Avoid expensive AI analysis
   - Don't make external API calls

2. **Return minimal but complete data**
   - Include everything frontend needs
   - Exclude internal/debug data
   - Hide sensitive information

3. **Optimize for common case**
   ```python
   def get_session_state(self, session_id: str):
       state = self.active_sessions[session_id]

       # Reuse cached expensive computations
       if state.get("_analysis_cache_version") == state["move_count"]:
           ai_hint = state["_cached_ai_hint"]
       else:
           ai_hint = self._compute_ai_hint(state)
           state["_cached_ai_hint"] = ai_hint
           state["_analysis_cache_version"] = state["move_count"]

       return {
           "board": state["board"],
           "game_over": state["game_over"],
           "ai_hint": ai_hint  # Cached when possible
       }
   ```

#### Testing Your Implementation

Verify `get_session_state()` works correctly:

```python
# Test 1: Returns fresh state after move
session = plugin.start_session(user_id, config)
plugin.validate_move(session.session_id, {"position": [0, 0]})
state = plugin.get_session_state(session.session_id)
assert "board" in state
assert "current_player" in state
assert "game_over" in state

# Test 2: State reflects latest changes
plugin.validate_move(session.session_id, {"position": [1, 1]})
new_state = plugin.get_session_state(session.session_id)
assert new_state != state  # State should have changed

# Test 3: Returns None only for non-existent sessions
assert plugin.get_session_state("fake_session_id") is None
assert plugin.get_session_state(session.session_id) is not None
```

---

#### 7. `update_session_state()` - Write Game State

**Purpose**: Update session state (used for sync/resume).

**When Called**:
- Cross-device synchronization
- Resume paused game
- Admin corrections

**Parameters**:
- `session_id`: Session to update
- `new_state`: State updates (dict)

**Returns**: `bool` (success/failure)

**Implementation**:
```python
def update_session_state(self, session_id: str, new_state: Dict[str, Any]) -> bool:
    """Update session state"""
    if session_id not in self.active_sessions:
        return False

    game_state = self.active_sessions[session_id]

    # Whitelist of allowed updates (prevent cheating)
    allowed_updates = {
        "last_sync_time",
        "device_id",
        "pause_count"
    }

    # Apply only allowed updates
    for key, value in new_state.items():
        if key in allowed_updates:
            game_state[key] = value

    return True
```

**Security Considerations**:
```python
# ❌ NEVER allow these updates from client
FORBIDDEN_UPDATES = {
    "score",           # Would allow score manipulation
    "lives",           # Would allow infinite lives
    "game_over",       # Would allow continuing finished games
    "winner",          # Would allow changing winner
    "credits_earned"   # Would allow credit fraud
}

# ✅ Allow these updates
SAFE_UPDATES = {
    "last_sync_time",  # Sync metadata
    "device_info",     # Device tracking
    "ui_preferences"   # UI settings
}
```

**Best Practices**:
- ✅ Whitelist allowed updates
- ✅ Validate update values
- ✅ Log suspicious updates
- ✅ Implement anti-cheat checks
- ❌ Don't allow score/credit updates
- ❌ Don't trust client state blindly

---

### plugin.json Schema

**Required Fields**:
```json
{
  "id": "your_game",              // Unique identifier (alphanumeric + underscore)
  "name": "Your Game",            // Display name
  "version": "1.0.0",             // Semantic versioning
  "main_module": "main"           // Python module name (without .py)
}
```

**Optional but Recommended**:
```json
{
  "description": "Short description",
  "author": "Your Name",
  "category": "puzzle",           // puzzle, action, strategy, card, board, etc.

  "dependencies": {
    "python_packages": ["numpy", "requests"],  // pip packages
    "plugins": ["base_card_game"]              // Other plugins
  },

  "metadata": {
    "min_players": 1,
    "max_players": 4,
    "estimated_duration_minutes": 10,
    "difficulty_level": "medium",    // easy, medium, hard
    "requires_internet": false,
    "credit_rate": 1.0               // Credits per minute
  }
}
```

---

## Game Modes & Patterns

### Pattern 1: Single Player vs AI

**Use Case**: Player competes against computer AI.

**Example**: Tic Tac Toe, Chess, Card Games

**Implementation**:
```python
def start_session(self, user_id: str, session_config: Optional[Dict[str, Any]] = None) -> GameSession:
    """Start vs AI session"""
    session_config = session_config or {}

    # Parse AI configuration
    ai_difficulty = session_config.get("ai_difficulty", "medium")
    player_symbol = session_config.get("player_symbol", "X")
    ai_symbol = "O" if player_symbol == "X" else "X"

    game_state = {
        "game_mode": "vs_ai",
        "ai_difficulty": ai_difficulty,
        "player_symbol": player_symbol,
        "ai_symbol": ai_symbol,
        "current_player": "X",  # X always goes first
        # ... other state
    }

    # If AI goes first, make AI move immediately
    if player_symbol == "O":
        self._make_ai_move(game_state)

    # ... create session
```

**AI Move After Player Move**:
```python
def validate_move(self, session_id: str, move: Dict[str, Any]) -> bool:
    """Process player move and trigger AI response"""
    game_state = self.active_sessions[session_id]

    # Apply player move
    self._apply_move(game_state, move)

    # Check if game ended
    if game_state["game_over"]:
        return True

    # Make AI move automatically
    self._make_ai_move(game_state)

    return True

def _make_ai_move(self, game_state: Dict[str, Any]) -> None:
    """Make AI move based on difficulty"""
    difficulty = game_state["ai_difficulty"]

    if difficulty == "easy":
        move = self._get_random_move(game_state)
    elif difficulty == "medium":
        move = self._get_smart_move(game_state)
    else:  # hard
        move = self._get_optimal_move(game_state)

    self._apply_move(game_state, move)
```

**AI Algorithms**:
- **Easy**: Random valid move
- **Medium**: Basic heuristics (block wins, take wins)
- **Hard**: Minimax, Alpha-Beta pruning, Monte Carlo Tree Search

---

### Pattern 2: Local Multiplayer

**Use Case**: Multiple players on same device, taking turns.

**Example**: Tic Tac Toe local, board games

**Implementation**:
```python
def start_session(self, user_id: str, session_config: Optional[Dict[str, Any]] = None) -> GameSession:
    """Start local multiplayer session"""
    session_config = session_config or {}

    player_count = session_config.get("player_count", 2)

    game_state = {
        "game_mode": "local",
        "player_count": player_count,
        "current_player_index": 0,
        "players": [f"Player{i+1}" for i in range(player_count)],
        # ... other state
    }

    # ... create session
```

**Turn Management**:
```python
def validate_move(self, session_id: str, move: Dict[str, Any]) -> bool:
    """Process move and switch player"""
    game_state = self.active_sessions[session_id]

    # Apply move
    self._apply_move(game_state, move)

    # Check if game ended
    if not game_state["game_over"]:
        # Switch to next player
        game_state["current_player_index"] = (
            (game_state["current_player_index"] + 1) % game_state["player_count"]
        )

    return True
```

**UI Integration**:
```typescript
// Frontend shows current player
function TurnIndicator({ state }) {
  return (
    <div>
      Current Turn: {state.players[state.current_player_index]}
    </div>
  );
}
```

---

### Pattern 3: Online Multiplayer

**Use Case**: Players on different devices play together.

**Example**: Tic Tac Toe online, multiplayer games

**Implementation**:

**Note**: Online multiplayer uses the existing multiplayer system. Your plugin only needs to:
1. Support `game_mode: "online"` in `session_config`
2. Validate that moves come from correct player
3. Provide state suitable for broadcasting

```python
def start_session(self, user_id: str, session_config: Optional[Dict[str, Any]] = None) -> GameSession:
    """Start online multiplayer session"""
    session_config = session_config or {}

    game_state = {
        "game_mode": "online",
        "room_id": session_config.get("room_id"),
        "players": session_config.get("players", []),
        "current_player_index": 0,
        # ... other state
    }

    # ... create session
```

**Move Validation with Player Check**:
```python
def validate_move(self, session_id: str, move: Dict[str, Any]) -> bool:
    """Validate move in online mode"""
    game_state = self.active_sessions[session_id]

    # In online mode, moves include player_id
    player_id = move.get("player_id")

    # Validate it's this player's turn
    current_player = game_state["players"][game_state["current_player_index"]]
    if player_id != current_player:
        return False  # Not this player's turn

    # Process move
    # ...
```

**Integration with Multiplayer System**:
```
app/games/multiplayer/
├── services/
│   ├── room_manager.py          # Creates rooms
│   └── state_manager.py         # Broadcasts state
└── events/
    └── game_events.py           # WebSocket handlers

Your Plugin:
- Validates moves
- Updates state
- Returns state for broadcast
```

The multiplayer system handles:
- Room creation/joining
- WebSocket connections
- State broadcasting
- Player disconnection

---

### Pattern 4: Turn-Based with Timer

**Use Case**: Players have limited time per turn.

**Implementation**:
```python
def start_session(self, user_id: str, session_config: Optional[Dict[str, Any]] = None) -> GameSession:
    """Start turn-based session with timer"""
    game_state = {
        "turn_duration": session_config.get("turn_duration", 30),  # seconds
        "turn_started_at": datetime.utcnow().isoformat(),
        # ...
    }

def validate_move(self, session_id: str, move: Dict[str, Any]) -> bool:
    """Validate move with time check"""
    game_state = self.active_sessions[session_id]

    # Check if turn expired
    turn_started = datetime.fromisoformat(game_state["turn_started_at"])
    elapsed = (datetime.utcnow() - turn_started).total_seconds()

    if elapsed > game_state["turn_duration"]:
        # Auto-forfeit turn
        self._skip_turn(game_state)
        return False

    # Process move
    # ...

    # Reset timer for next turn
    game_state["turn_started_at"] = datetime.utcnow().isoformat()
```

---

### Pattern 5: Real-Time Action

**Use Case**: Fast-paced games requiring frequent updates.

**Example**: Platformers, racing games

**Considerations**:
- Use WebSocket for real-time communication
- Validate moves server-side (prevent cheating)
- Implement lag compensation
- Throttle state updates (max 60 updates/second)

```python
def validate_move(self, session_id: str, move: Dict[str, Any]) -> bool:
    """Validate real-time action"""
    game_state = self.active_sessions[session_id]

    # Throttle updates
    last_update = datetime.fromisoformat(game_state.get("last_update", datetime.utcnow().isoformat()))
    min_interval = 0.016  # 60 FPS

    if (datetime.utcnow() - last_update).total_seconds() < min_interval:
        return False  # Too fast, reject

    # Validate movement (server-authoritative)
    if not self._is_valid_position(move["position"]):
        return False

    # Apply physics
    self._apply_physics(game_state, move)

    game_state["last_update"] = datetime.utcnow().isoformat()
    return True
```

---

## API Reference

### GamePlugin Methods

#### `initialize() -> bool`
- **Purpose**: One-time setup when plugin loads
- **Returns**: `True` if successful, `False` otherwise
- **Called**: Once during plugin registration

#### `start_session(user_id, session_config) -> GameSession`
- **Purpose**: Create new game instance
- **Parameters**:
  - `user_id` (str): User's unique ID
  - `session_config` (dict, optional): Game configuration
- **Returns**: GameSession object
- **Called**: When user starts new game

#### `end_session(session_id, reason) -> SessionResult`
- **Purpose**: End game and calculate results
- **Parameters**:
  - `session_id` (str): Session to end
  - `reason` (str): "completed", "abandoned", "timeout"
- **Returns**: SessionResult object
- **Called**: When game finishes or is abandoned

#### `get_rules() -> GameRules`
- **Purpose**: Provide game rules and metadata
- **Returns**: GameRules object
- **Called**: When frontend requests game info

#### `validate_move(session_id, move) -> bool`
- **Purpose**: Validate and process player move
- **Parameters**:
  - `session_id` (str): Active session
  - `move` (dict): Move data
- **Returns**: `True` if valid, `False` otherwise
- **Called**: When player makes a move

#### `get_session_state(session_id) -> Optional[Dict]`
- **Purpose**: Get current game state
- **Parameters**:
  - `session_id` (str): Session ID
- **Returns**: State dict or `None`
- **Called**: After each move, on sync

#### `update_session_state(session_id, new_state) -> bool`
- **Purpose**: Update game state (sync/resume)
- **Parameters**:
  - `session_id` (str): Session ID
  - `new_state` (dict): State updates
- **Returns**: `True` if successful
- **Called**: During state synchronization

---

### Data Classes

#### GameRules
```python
@dataclass
class GameRules:
    min_players: int                    # Minimum players
    max_players: int                    # Maximum players
    estimated_duration_minutes: int     # Average game duration
    difficulty_level: str               # "easy", "medium", "hard"
    requires_internet: bool             # Needs internet connection
    description: str                    # Short description
    instructions: str                   # Full rules (Markdown)
```

#### GameSession
```python
@dataclass
class GameSession:
    session_id: str                     # Unique session ID
    user_id: str                        # User ID
    game_id: str                        # Game/plugin ID
    status: str                         # "active", "paused", "completed"
    current_state: Dict[str, Any]       # Current game state
    score: Optional[int] = None         # Current score
    credits_earned: Optional[int] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
```

#### SessionResult
```python
@dataclass
class SessionResult:
    session_id: str                     # Session ID
    final_score: int                    # Final score
    credits_earned: int                 # Credits earned
    completion_time_seconds: int        # Duration in seconds
    achievements_unlocked: list         # Achievement IDs
    statistics: Dict[str, Any]          # Detailed stats
```

---

## Integration Points

### Achievement System

Unlock achievements during gameplay:

```python
def end_session(self, session_id: str, reason: str = "completed") -> SessionResult:
    """End session and check achievements"""
    game_state = self.active_sessions[session_id]

    achievements = []

    # Check various achievements
    if game_state["score"] > 10000:
        achievements.append("HIGH_SCORER")

    if game_state["perfect_game"]:
        achievements.append("PERFECT_GAME")

    if game_state["level"] >= 10:
        achievements.append("LEVEL_MASTER")

    # Time-based achievements
    play_time = (datetime.utcnow() - datetime.fromisoformat(game_state["started_at"])).total_seconds()
    if play_time < 60:
        achievements.append("SPEED_RUN")

    return SessionResult(
        # ...
        achievements_unlocked=achievements,
        # ...
    )
```

**Achievement Integration**:
```python
# Backend automatically triggers achievement system
from app.social.services.achievement_service import AchievementService

achievement_service = AchievementService()
for achievement_id in result.achievements_unlocked:
    achievement_service.unlock_achievement(user_id, achievement_id)
```

---

### Credit System

Calculate credits fairly:

```python
def _calculate_credits(self, game_state: Dict[str, Any]) -> int:
    """Calculate credits earned"""
    # Get actual play time (exclude pauses)
    play_duration_ms = game_state.get("play_duration_ms", 0)
    play_minutes = play_duration_ms / (1000 * 60)

    # Base credits from time
    base_credits = play_minutes * self.credit_rate

    # Performance multiplier
    multiplier = 1.0

    if game_state["score"] > 10000:
        multiplier = 2.0  # Excellent performance
    elif game_state["score"] > 5000:
        multiplier = 1.5  # Good performance
    elif game_state["score"] < 1000:
        multiplier = 0.5  # Poor performance

    # Difficulty multiplier
    difficulty_multipliers = {
        "easy": 0.8,
        "medium": 1.0,
        "hard": 1.5
    }
    multiplier *= difficulty_multipliers.get(game_state["difficulty"], 1.0)

    # Calculate final credits
    credits = int(base_credits * multiplier)

    # Enforce limits (prevent abuse)
    max_credits_per_game = 100
    return min(credits, max_credits_per_game)
```

**Credit Integration**:
```python
# Backend automatically processes credits
from app.donations.services.wallet_service import WalletService

wallet_service = WalletService()
wallet_service.add_credits(
    user_id,
    credits_earned=result.credits_earned,
    source="game_session",
    session_id=result.session_id
)
```

---

### Leaderboard System

Submit scores to leaderboards:

```python
def end_session(self, session_id: str, reason: str = "completed") -> SessionResult:
    """End session and submit score"""
    game_state = self.active_sessions[session_id]

    result = SessionResult(
        # ...
        statistics={
            "final_score": game_state["score"],
            "level_reached": game_state["level"],
            "accuracy": self._calculate_accuracy(game_state),
            # ... other stats for leaderboard
        }
    )

    return result
```

**Leaderboard Integration**:
```python
# Backend automatically updates leaderboards
from app.social.leaderboards.services.leaderboard_service import LeaderboardService

leaderboard_service = LeaderboardService()
leaderboard_service.submit_score(
    user_id=user_id,
    game_id=game_id,
    score=result.final_score,
    metadata=result.statistics
)
```

---

## Best Practices

### Security

#### Input Validation
```python
def validate_move(self, session_id: str, move: Dict[str, Any]) -> bool:
    """Always validate input"""

    # Check session exists
    if session_id not in self.active_sessions:
        return False

    # Validate move structure
    if not isinstance(move, dict):
        return False

    if "action" not in move:
        return False

    # Validate move values
    action = move["action"]
    if action not in ["move", "attack", "defend", "pass"]:
        return False

    # Sanitize strings
    if "name" in move:
        move["name"] = self._sanitize_string(move["name"])

    return True
```

#### Anti-Cheat
```python
def _detect_cheating(self, game_state: Dict[str, Any]) -> bool:
    """Detect suspicious activity"""

    # Check for impossible scores
    if game_state["score"] > self.max_possible_score:
        return True

    # Check for impossible progression
    time_played = (datetime.utcnow() - datetime.fromisoformat(game_state["started_at"])).total_seconds()
    if game_state["level"] > time_played / 10:  # Too fast
        return True

    # Check for modified state
    if not self._validate_state_integrity(game_state):
        return True

    return False
```

---

### Performance

#### Efficient State Storage
```python
# ❌ Bad: Store entire history
game_state["move_history"] = []  # Gets huge over time

# ✅ Good: Store summary
game_state["move_count"] = 0
game_state["last_10_moves"] = []  # Circular buffer
```

#### Lazy Loading
```python
def get_session_state(self, session_id: str) -> Optional[Dict[str, Any]]:
    """Lazy load expensive data"""

    state = {
        "score": game_state["score"],
        "level": game_state["level"],
        # ... essential data
    }

    # Only load detailed stats if requested
    if include_details:
        state["detailed_stats"] = self._calculate_detailed_stats(game_state)

    return state
```

---

### Error Handling

```python
def validate_move(self, session_id: str, move: Dict[str, Any]) -> bool:
    """Proper error handling"""

    try:
        if session_id not in self.active_sessions:
            current_app.logger.warning(f"Session not found: {session_id}")
            return False

        game_state = self.active_sessions[session_id]

        # Validate and process
        # ...

        return True

    except KeyError as e:
        current_app.logger.error(f"Missing required field: {e}")
        return False

    except ValueError as e:
        current_app.logger.error(f"Invalid value: {e}")
        return False

    except Exception as e:
        current_app.logger.error(f"Unexpected error: {e}", exc_info=True)
        return False
```

---

## Testing

### Unit Testing

```python
# tests/test_your_game_plugin.py
import pytest
from app.games.plugins.your_game.main import YourGamePlugin


class TestYourGamePlugin:
    def setup_method(self):
        """Setup before each test"""
        self.plugin = YourGamePlugin()
        self.plugin.initialize()

    def test_plugin_initialization(self):
        """Test plugin initializes correctly"""
        assert self.plugin.is_initialized is True
        assert self.plugin.name == "Your Game"
        assert self.plugin.version == "1.0.0"

    def test_start_session(self):
        """Test session creation"""
        session = self.plugin.start_session("user123")

        assert session.session_id is not None
        assert session.user_id == "user123"
        assert session.status == "active"
        assert session.current_state is not None

    def test_valid_move(self):
        """Test valid move processing"""
        session = self.plugin.start_session("user123")

        move = {"action": "move", "position": [0, 0]}
        result = self.plugin.validate_move(session.session_id, move)

        assert result is True

    def test_invalid_move(self):
        """Test invalid move rejection"""
        session = self.plugin.start_session("user123")

        # Invalid move format
        move = {"invalid": "data"}
        result = self.plugin.validate_move(session.session_id, move)

        assert result is False

    def test_end_session(self):
        """Test session ending"""
        session = self.plugin.start_session("user123")

        result = self.plugin.end_session(session.session_id)

        assert result.session_id == session.session_id
        assert result.final_score >= 0
        assert result.credits_earned >= 0
        assert isinstance(result.achievements_unlocked, list)

    def test_get_rules(self):
        """Test rules retrieval"""
        rules = self.plugin.get_rules()

        assert rules.min_players > 0
        assert rules.max_players >= rules.min_players
        assert rules.description != ""
        assert rules.instructions != ""
```

---

### Integration Testing

```python
# tests/integration/test_game_api.py
from app import create_app


class TestGameAPI:
    def setup_method(self):
        """Setup test client"""
        self.app = create_app('testing')
        self.client = self.app.test_client()
        self.token = self._get_auth_token()

    def test_start_game_session(self):
        """Test starting game via API"""
        response = self.client.post('/api/games/sessions',
            headers={'Authorization': f'Bearer {self.token}'},
            json={
                'game_id': 'your_game',
                'session_config': {
                    'game_mode': 'single_player',
                    'difficulty': 'medium'
                }
            }
        )

        assert response.status_code == 200
        data = response.json
        assert data['success'] is True
        assert 'session' in data['data']

    def test_make_move(self):
        """Test making move via API"""
        # Start session
        session_response = self.client.post('/api/games/sessions',
            headers={'Authorization': f'Bearer {self.token}'},
            json={'game_id': 'your_game'}
        )
        session_id = session_response.json['data']['session']['session_id']

        # Make move
        move_response = self.client.post(f'/api/games/sessions/{session_id}/move',
            headers={'Authorization': f'Bearer {self.token}'},
            json={'move': {'action': 'test'}}
        )

        assert move_response.status_code == 200
        assert move_response.json['success'] is True
```

---

## Deployment

### Plugin Discovery

Plugins are automatically discovered on server startup:

```python
# app/__init__.py
from app.games.core.plugin_manager import plugin_manager

def create_app(config_name='development'):
    app = Flask(__name__)

    # ... app configuration

    # Discover and load plugins
    with app.app_context():
        discovered = plugin_manager.discover_plugins()
        app.logger.info(f"Loaded {len(discovered)} game plugins: {discovered}")

    return app
```

### Manual Plugin Registration

For development, manually register a plugin:

```python
from app.games.core.plugin_registry import plugin_registry
from app.games.plugins.your_game.main import YourGamePlugin

# Register plugin
plugin_registry.register_plugin(
    plugin_id="your_game",
    plugin_class=YourGamePlugin,
    metadata={"dev_mode": True}
)

# Verify
plugin = plugin_registry.get_plugin("your_game")
print(f"Plugin loaded: {plugin.name}")
```

### Production Checklist

```markdown
## Pre-Deployment Checklist

### Code Quality
- [ ] All unit tests pass
- [ ] Integration tests pass
- [ ] Code follows style guidelines
- [ ] No hardcoded credentials
- [ ] Error handling implemented
- [ ] Logging added for key operations

### Security
- [ ] Input validation complete
- [ ] Anti-cheat measures in place
- [ ] No sensitive data in state
- [ ] Rate limiting considered
- [ ] SQL injection prevention (if applicable)

### Performance
- [ ] Session state optimized
- [ ] No memory leaks
- [ ] Efficient algorithms used
- [ ] Database queries optimized
- [ ] Load tested (1000+ concurrent sessions)

### Documentation
- [ ] plugin.json complete
- [ ] README.md added
- [ ] API documented
- [ ] Examples provided

### Integration
- [ ] Achievement integration tested
- [ ] Credit calculation verified
- [ ] Leaderboard submission works
- [ ] Multiplayer tested (if applicable)
```

---

## Summary

### Key Takeaways

✅ **Plugin Structure**: Directory with plugin.json + main.py
✅ **Base Class**: Extend GamePlugin, implement 7 methods
✅ **Session Management**: Store state, validate moves, calculate results
✅ **Security**: Validate input, prevent cheating, hide sensitive data
✅ **Integration**: Works with achievements, credits, leaderboards
✅ **Testing**: Unit tests + integration tests required
✅ **Auto-Discovery**: Plugins loaded on startup automatically

### Next Steps

1. **Study Examples**: Review `/app/games/plugins/tic_tac_toe/`
2. **Start Simple**: Create coin flip or dice game
3. **Add Complexity**: Implement AI, multiplayer, etc.
4. **Test Thoroughly**: Unit + integration tests
5. **Deploy**: Add to plugins directory, restart server

### Resources

- **Frontend Guide**: `/docs/FRONTEND_GAME_INTEGRATION_GUIDE.md`
- **Tic Tac Toe Example**: `/app/games/plugins/tic_tac_toe/`
- **API Docs**: `/docs/openapi/games.yaml`
- **Contributing**: `/CONTRIBUTING.md`

---

*Last Updated: 2025-10-21*
*Version: 1.0*
