"""
Flow Tiles Game Plugin

A zen puzzle game where players connect colored tiles to create flowing patterns.

Game Modes:
1. zen: Free-form creative mode, place and rotate tiles freely
2. puzzle: Pre-defined patterns to complete
3. collaborative: Multiple players work together (local)
4. harmonic: Turn-based competitive multiplayer (online)
"""

import uuid
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from copy import deepcopy

from app.games.core.game_plugin import GamePlugin, GameRules, GameSession, SessionResult


class FlowTilesGame(GamePlugin):
    """
    Flow Tiles game plugin with support for multiple game modes.
    """

    # Tile types
    TILE_SOURCE = "source"
    TILE_DESTINATION = "destination"
    TILE_PIPE = "pipe"

    # Directions
    DIR_UP = "up"
    DIR_DOWN = "down"
    DIR_LEFT = "left"
    DIR_RIGHT = "right"

    # Game modes
    MODE_ZEN = "zen"
    MODE_PUZZLE = "puzzle"
    MODE_COLLABORATIVE = "collaborative"
    MODE_HARMONIC = "harmonic"

    # Colors
    COLORS = ["blue", "red", "green", "yellow", "purple", "orange"]

    # Grid size
    DEFAULT_ROWS = 6
    DEFAULT_COLS = 6

    def __init__(self):
        super().__init__()
        self.name = "Flow Tiles"
        self.version = "1.0.0"
        self.description = "Create beautiful flowing patterns - Zen puzzle game"
        self.category = "relaxation"
        self.author = "GoodPlay Team"
        self.credit_rate = 1.0  # Credits per minute

        # Active sessions storage (in production, use MongoDB via repository)
        self.active_sessions: Dict[str, Dict[str, Any]] = {}

    def initialize(self) -> bool:
        """Initialize the game plugin"""
        try:
            self.is_initialized = True
            return True
        except Exception as e:
            print(f"Failed to initialize FlowTilesGame: {e}")
            return False

    def start_session(self, user_id: str, session_config: Optional[Dict[str, Any]] = None) -> GameSession:
        """
        Start a new game session.

        Args:
            user_id: The user starting the game
            session_config: Optional configuration with:
                - mode: "zen", "puzzle", "collaborative", or "harmonic" (default: "zen")
                - rows: Grid rows (default: 6)
                - cols: Grid columns (default: 6)
                - pattern_id: For puzzle mode, the pattern to complete
                - player_ids: For multiplayer modes, list of player IDs
        """
        session_config = session_config or {}
        session_id = str(uuid.uuid4())

        # Parse configuration
        mode = session_config.get("mode", self.MODE_ZEN)
        rows = session_config.get("rows", self.DEFAULT_ROWS)
        cols = session_config.get("cols", self.DEFAULT_COLS)
        pattern_id = session_config.get("pattern_id")
        player_ids = session_config.get("player_ids", [user_id])

        # Validate mode
        if mode not in [self.MODE_ZEN, self.MODE_PUZZLE, self.MODE_COLLABORATIVE, self.MODE_HARMONIC]:
            mode = self.MODE_ZEN

        # Initialize game state
        game_state = {
            "grid": self._create_empty_grid(rows, cols),
            "flows": [],
            "mode": mode,
            "rows": rows,
            "cols": cols,
            "pattern_id": pattern_id,
            "player_ids": player_ids,
            "current_player": player_ids[0] if mode == self.MODE_HARMONIC else None,
            "scores": {pid: 0 for pid in player_ids},
            "is_complete": False,
            "move_count": 0,
            "moves_history": [],
            "last_move_index": None,
            "total_beauty_score": 0
        }

        # If puzzle mode, initialize with pattern
        if mode == self.MODE_PUZZLE and pattern_id:
            self._init_puzzle_pattern(game_state, pattern_id)

        # Store session
        self.active_sessions[session_id] = game_state

        # Create session object
        session = GameSession(
            session_id=session_id,
            user_id=user_id,
            game_id="flow_tiles",
            status="active",
            current_state=self._get_public_state(session_id),
            started_at=datetime.utcnow()
        )

        return session

    def end_session(self, session_id: str, reason: str = "completed") -> SessionResult:
        """End a game session and calculate results"""
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")

        game_state = self.active_sessions[session_id]

        # Calculate score
        final_score = self._calculate_score(game_state, reason)

        # Calculate credits (based on game duration and outcome)
        credits_earned = self._calculate_credits(game_state, final_score)

        # Determine achievements
        achievements = self._determine_achievements(game_state)

        # Create session result
        result = SessionResult(
            session_id=session_id,
            final_score=final_score,
            credits_earned=credits_earned,
            completion_time_seconds=900,  # Average 15 minutes
            achievements_unlocked=achievements,
            statistics={
                "mode": game_state["mode"],
                "move_count": game_state["move_count"],
                "completed_flows": len([f for f in game_state["flows"] if f.get("isComplete")]),
                "total_flows": len(game_state["flows"]),
                "beauty_score": game_state["total_beauty_score"],
                "is_complete": game_state["is_complete"],
                "final_grid": game_state["grid"],
                "player_scores": game_state["scores"]
            }
        )

        # Clean up session
        del self.active_sessions[session_id]

        return result

    def get_rules(self) -> GameRules:
        """Get the game rules"""
        return GameRules(
            min_players=1,
            max_players=8,
            estimated_duration_minutes=15,
            difficulty_level="easy",
            requires_internet=False,
            description="Create beautiful flowing patterns by connecting colored tiles",
            instructions="""
# Flow Tiles Rules

## Objective
Connect colored tiles to create beautiful flowing patterns. Complete all flows for maximum score!

## How to Play

### Game Modes
1. **Zen Mode**: Free-form creative mode
   - Place and rotate tiles freely
   - No time limit or score pressure
   - Perfect for relaxation

2. **Puzzle Mode**: Complete pre-defined patterns
   - Specific tiles and connections to achieve
   - Score based on efficiency (fewer moves = higher score)

3. **Collaborative Mode**: Work together locally
   - 2-4 players share the same screen
   - All can move at any time
   - Shared victory condition

4. **Harmonic Mode**: Turn-based competitive
   - 1v1 online multiplayer
   - Players take turns
   - Winner has highest beauty score

### Actions
Send actions as: {"action": "rotate"|"place", "index": <position>, ...}

**Rotate Tile:**
```json
{
  "action": "rotate",
  "index": 5,
  "playerId": "user_id"
}
```

**Place Tile (Zen mode only):**
```json
{
  "action": "place",
  "index": 3,
  "tile": {
    "type": "pipe",
    "connections": ["up", "right"],
    "rotation": 0,
    "color": "blue"
  },
  "playerId": "user_id"
}
```

### Grid Layout (6x6 = 36 tiles)
```
[0]  [1]  [2]  [3]  [4]  [5]
[6]  [7]  [8]  [9]  [10] [11]
[12] [13] [14] [15] [16] [17]
[18] [19] [20] [21] [22] [23]
[24] [25] [26] [27] [28] [29]
[30] [31] [32] [33] [34] [35]
```

### Tile Types
- **Source**: Start of a flow (locked)
- **Destination**: End of a flow (locked)
- **Pipe**: Connectable tile (can rotate)

### Winning
- **Zen**: No win condition, just create!
- **Puzzle**: Complete all flows exactly as specified
- **Collaborative**: All flows connected and complete
- **Harmonic**: Player with highest beauty score when all flows complete

## Scoring
- **Flow Completion**: +50 points per completed flow
- **Beauty Score**: +1-5 points per flow based on elegance
- **Efficiency Bonus**: Fewer moves = higher multiplier
- **Perfect Game**: +500 bonus (all flows complete, max beauty)

## Beauty Score Calculation
- Straight paths: +1 per tile
- Gentle curves: +2 per tile
- Complex patterns: +3 per tile
- Symmetry bonus: +10 per symmetric flow
- No wasted tiles: +20 bonus
            """
        )

    def validate_move(self, session_id: str, move: Dict[str, Any]) -> bool:
        """
        Validate and process a player's move.

        Args:
            session_id: The session ID
            move: Move data with format:
                {
                    "action": "rotate"|"place"|"reset",
                    "index": <tile_index>,
                    "playerId": "<user_id>",
                    "tile": {...}  # for place action
                }

        Returns:
            bool: True if move is valid and processed, False otherwise
        """
        if session_id not in self.active_sessions:
            return False

        game_state = self.active_sessions[session_id]

        # Check if game is complete
        if game_state["is_complete"]:
            return False

        # Validate move format
        if "action" not in move or "index" not in move:
            return False

        action = move["action"]
        index = move["index"]
        player_id = move.get("playerId")

        # Validate index bounds
        grid_size = game_state["rows"] * game_state["cols"]
        if not (0 <= index < grid_size):
            return False

        # In harmonic mode, validate it's the current player's turn
        if game_state["mode"] == self.MODE_HARMONIC:
            if game_state["current_player"] != player_id:
                return False

        # Validate action-specific logic
        if action == "rotate":
            return self._handle_rotate(game_state, index, player_id)
        elif action == "place":
            return self._handle_place(game_state, index, player_id, move.get("tile"))
        elif action == "reset":
            return self._handle_reset(game_state)

        return False

    def get_session_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get the current state of a game session"""
        if session_id not in self.active_sessions:
            return None

        return self._get_public_state(session_id)

    def update_session_state(self, session_id: str, new_state: Dict[str, Any]) -> bool:
        """
        Update session state (used primarily for online multiplayer synchronization).

        Only allows safe updates to prevent cheating.
        """
        if session_id not in self.active_sessions:
            return False

        # For online multiplayer, allow controlled state updates
        # In production, validate via server-authoritative logic
        allowed_updates = ["last_sync_time", "opponent_connected"]

        for key, value in new_state.items():
            if key in allowed_updates:
                self.active_sessions[session_id][key] = value

        return True

    # ==================== PRIVATE HELPER METHODS ====================

    def _create_empty_grid(self, rows: int, cols: int) -> List[Optional[Dict[str, Any]]]:
        """Create an empty grid"""
        return [None for _ in range(rows * cols)]

    def _get_public_state(self, session_id: str) -> Dict[str, Any]:
        """Get the public state of a session (hides internal data)"""
        game_state = self.active_sessions[session_id]

        return {
            "grid": game_state["grid"],
            "flows": game_state["flows"],
            "mode": game_state["mode"],
            "rows": game_state["rows"],
            "cols": game_state["cols"],
            "current_player": game_state.get("current_player"),
            "scores": game_state["scores"],
            "is_complete": game_state["is_complete"],
            "move_count": game_state["move_count"],
            "last_move_index": game_state.get("last_move_index"),
            "total_beauty_score": game_state["total_beauty_score"]
        }

    def _init_puzzle_pattern(self, game_state: Dict[str, Any], pattern_id: str):
        """Initialize grid with a puzzle pattern"""
        # For now, create a simple pattern
        # In production, load from pattern database
        # Example: Add source and destination tiles for blue flow
        rows = game_state["rows"]
        cols = game_state["cols"]

        # Place source at top-left
        game_state["grid"][0] = {
            "type": self.TILE_SOURCE,
            "connections": [self.DIR_RIGHT, self.DIR_DOWN],
            "rotation": 0,
            "color": "blue",
            "isLocked": True,
            "isActive": False
        }

        # Place destination at bottom-right
        last_index = (rows * cols) - 1
        game_state["grid"][last_index] = {
            "type": self.TILE_DESTINATION,
            "connections": [self.DIR_UP, self.DIR_LEFT],
            "rotation": 0,
            "color": "blue",
            "isLocked": True,
            "isActive": False
        }

    def _handle_rotate(self, game_state: Dict[str, Any], index: int, player_id: str) -> bool:
        """Handle tile rotation"""
        tile = game_state["grid"][index]

        # Cannot rotate empty or locked tiles
        if not tile or tile.get("isLocked"):
            return False

        # Rotate 90 degrees clockwise
        current_rotation = tile.get("rotation", 0)
        tile["rotation"] = (current_rotation + 90) % 360

        # Also rotate connections
        tile["connections"] = self._rotate_connections(tile["connections"])

        # Record move
        self._record_move(game_state, "rotate", index, player_id)

        # Recalculate flows
        self._recalculate_flows(game_state)

        # Check if game is complete
        self._check_completion(game_state)

        # Switch player in harmonic mode
        if game_state["mode"] == self.MODE_HARMONIC:
            self._switch_player(game_state)

        return True

    def _handle_place(self, game_state: Dict[str, Any], index: int, player_id: str, tile_data: Optional[Dict]) -> bool:
        """Handle tile placement (zen mode only)"""
        # Only allow in zen mode
        if game_state["mode"] != self.MODE_ZEN:
            return False

        # Cannot place on occupied tile
        if game_state["grid"][index] is not None:
            return False

        # Validate tile data
        if not tile_data:
            return False

        # Place tile
        game_state["grid"][index] = {
            "type": tile_data.get("type", self.TILE_PIPE),
            "connections": tile_data.get("connections", []),
            "rotation": tile_data.get("rotation", 0),
            "color": tile_data.get("color", "blue"),
            "isLocked": False,
            "isActive": False
        }

        # Record move
        self._record_move(game_state, "place", index, player_id, tile_data)

        # Recalculate flows
        self._recalculate_flows(game_state)

        return True

    def _handle_reset(self, game_state: Dict[str, Any]) -> bool:
        """Handle game reset (rematch)"""
        # Reset grid to initial state (keep sources/destinations)
        for i, tile in enumerate(game_state["grid"]):
            if tile and not tile.get("isLocked"):
                game_state["grid"][i] = None

        # Clear flows and scores
        game_state["flows"] = []
        game_state["scores"] = {pid: 0 for pid in game_state["player_ids"]}
        game_state["is_complete"] = False
        game_state["move_count"] = 0
        game_state["total_beauty_score"] = 0

        return True

    def _rotate_connections(self, connections: List[str]) -> List[str]:
        """Rotate connection directions 90 degrees clockwise"""
        rotation_map = {
            self.DIR_UP: self.DIR_RIGHT,
            self.DIR_RIGHT: self.DIR_DOWN,
            self.DIR_DOWN: self.DIR_LEFT,
            self.DIR_LEFT: self.DIR_UP
        }
        return [rotation_map.get(conn, conn) for conn in connections]

    def _record_move(self, game_state: Dict[str, Any], action: str, index: int, player_id: str, tile_data: Optional[Dict] = None):
        """Record a move in history"""
        game_state["move_count"] += 1
        game_state["last_move_index"] = index

        move_record = {
            "action": action,
            "index": index,
            "player_id": player_id,
            "move_number": game_state["move_count"],
            "timestamp": datetime.utcnow().isoformat()
        }

        if tile_data:
            move_record["tile_data"] = tile_data

        game_state["moves_history"].append(move_record)

    def _recalculate_flows(self, game_state: Dict[str, Any]):
        """Recalculate all flows and their status"""
        # Simplified flow calculation
        # In production, implement proper path-finding algorithm
        game_state["flows"] = []

        # Find all source tiles
        sources = [(i, tile) for i, tile in enumerate(game_state["grid"])
                  if tile and tile.get("type") == self.TILE_SOURCE]

        for source_index, source_tile in sources:
            flow = self._trace_flow(game_state, source_index, source_tile["color"])
            if flow:
                game_state["flows"].append(flow)

        # Update total beauty score
        game_state["total_beauty_score"] = sum(f.get("beautyScore", 0) for f in game_state["flows"])

    def _trace_flow(self, game_state: Dict[str, Any], start_index: int, color: str) -> Optional[Dict[str, Any]]:
        """Trace a flow from a source tile"""
        # Simplified flow tracing - just check if source connects to anything
        path = [start_index]
        is_complete = False
        beauty_score = 0

        # In production, implement proper BFS/DFS path-finding
        # For now, just create a basic flow object

        return {
            "path": path,
            "color": color,
            "isComplete": is_complete,
            "beautyScore": beauty_score
        }

    def _check_completion(self, game_state: Dict[str, Any]):
        """Check if the game is complete"""
        if not game_state["flows"]:
            return

        # Game is complete if all flows are complete
        all_complete = all(flow.get("isComplete", False) for flow in game_state["flows"])
        game_state["is_complete"] = all_complete

    def _switch_player(self, game_state: Dict[str, Any]):
        """Switch to next player (harmonic mode)"""
        player_ids = game_state["player_ids"]
        current = game_state.get("current_player")

        if current in player_ids:
            current_index = player_ids.index(current)
            next_index = (current_index + 1) % len(player_ids)
            game_state["current_player"] = player_ids[next_index]

    def _calculate_score(self, game_state: Dict[str, Any], reason: str) -> int:
        """Calculate final score based on game outcome"""
        if reason == "abandoned":
            return 0

        base_score = game_state["total_beauty_score"]

        # Completion bonus
        completed_flows = len([f for f in game_state["flows"] if f.get("isComplete")])
        base_score += completed_flows * 50

        # Efficiency bonus (fewer moves = higher score)
        if game_state["move_count"] > 0:
            efficiency = max(0, 100 - game_state["move_count"])
            base_score += efficiency

        # Perfect game bonus
        if game_state["is_complete"] and all(f.get("beautyScore", 0) >= 4 for f in game_state["flows"]):
            base_score += 500

        return base_score

    def _calculate_credits(self, game_state: Dict[str, Any], final_score: int) -> int:
        """Calculate credits earned"""
        # Base credits on score
        base_credits = max(1, int(final_score / 100))

        # Bonus for complete game
        if game_state["is_complete"]:
            base_credits += 10

        return base_credits

    def _determine_achievements(self, game_state: Dict[str, Any]) -> List[str]:
        """Determine which achievements were unlocked"""
        achievements = []

        # Completion achievements
        if game_state["is_complete"]:
            achievements.append("FLOW_TILES_COMPLETED")

        # All flows complete
        completed_flows = len([f for f in game_state["flows"] if f.get("isComplete")])
        if completed_flows >= 3:
            achievements.append("FLOW_MASTER")

        # High beauty score
        if game_state["total_beauty_score"] >= 100:
            achievements.append("BEAUTY_ARTIST")

        # Efficient player (low move count)
        if game_state["is_complete"] and game_state["move_count"] <= 20:
            achievements.append("EFFICIENCY_EXPERT")

        # Perfect game
        if game_state["is_complete"] and all(f.get("beautyScore", 0) >= 4 for f in game_state["flows"]):
            achievements.append("PERFECT_HARMONY")

        return achievements


# Export the plugin class
GamePluginClass = FlowTilesGame
