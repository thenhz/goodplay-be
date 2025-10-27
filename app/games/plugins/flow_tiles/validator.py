"""
Flow Tiles Move Validator

Server-side validation for Flow Tiles game actions.
Prevents cheating and ensures game rules are followed.
"""

from typing import Dict, Any, Tuple, Optional


class FlowTilesValidator:
    """
    Validates Flow Tiles game moves to ensure they follow game rules.

    Used by both the plugin and multiplayer services for consistent validation.
    """

    # Tile types
    TILE_SOURCE = "source"
    TILE_DESTINATION = "destination"
    TILE_PIPE = "pipe"

    # Game modes
    MODE_ZEN = "zen"
    MODE_PUZZLE = "puzzle"
    MODE_COLLABORATIVE = "collaborative"
    MODE_HARMONIC = "harmonic"

    @staticmethod
    def validate_move(state: Dict[str, Any], action: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate a game action.

        Args:
            state: Current game state
            action: Action to validate with format:
                {
                    "action": "rotate" | "place" | "reset",
                    "index": <tile_index>,
                    "playerId": "<user_id>",
                    "tile": {...}  # for place action
                }

        Returns:
            Tuple[bool, str]: (is_valid, reason/error_code)
        """
        # Validation 1: Required fields
        if "action" not in action:
            return False, "ACTION_REQUIRED"

        if action["action"] != "reset" and "index" not in action:
            return False, "INDEX_REQUIRED"

        action_type = action["action"]
        index = action.get("index")
        player_id = action.get("playerId")

        # Validation 2: Valid action type
        if action_type not in ["rotate", "place", "reset"]:
            return False, "INVALID_ACTION_TYPE"

        # Validation 3: Game not already complete
        if state.get("is_complete", False):
            return False, "GAME_ALREADY_COMPLETE"

        # Reset is always valid
        if action_type == "reset":
            return True, "MOVE_VALID"

        # Validation 4: Valid index
        grid_size = state.get("rows", 6) * state.get("cols", 6)
        if index is None or not (0 <= index < grid_size):
            return False, "INVALID_TILE_INDEX"

        # Validation 5: Tile exists and is not locked (for rotate)
        if action_type == "rotate":
            return FlowTilesValidator._validate_rotate(state, index, player_id)

        # Validation 6: Place action validation
        if action_type == "place":
            return FlowTilesValidator._validate_place(state, index, player_id, action.get("tile"))

        return False, "UNKNOWN_ACTION"

    @staticmethod
    def _validate_rotate(state: Dict[str, Any], index: int, player_id: str) -> Tuple[bool, str]:
        """Validate rotation action"""
        grid = state.get("grid", [])

        # Check tile exists
        if index >= len(grid):
            return False, "INDEX_OUT_OF_BOUNDS"

        tile = grid[index]

        if not tile:
            return False, "TILE_EMPTY"

        # Check tile is not locked
        if tile.get("isLocked", False):
            return False, "TILE_LOCKED"

        # Check turn-based logic (harmonic mode)
        if state.get("mode") == FlowTilesValidator.MODE_HARMONIC:
            current_player = state.get("current_player")
            if current_player != player_id:
                return False, "NOT_YOUR_TURN"

        return True, "MOVE_VALID"

    @staticmethod
    def _validate_place(state: Dict[str, Any], index: int, player_id: str, tile_data: Optional[Dict]) -> Tuple[bool, str]:
        """Validate place action"""
        # Can only place in zen mode
        if state.get("mode") != FlowTilesValidator.MODE_ZEN:
            return False, "CANNOT_PLACE_IN_THIS_MODE"

        grid = state.get("grid", [])

        # Check index valid
        if index >= len(grid):
            return False, "INDEX_OUT_OF_BOUNDS"

        # Check tile is empty
        if grid[index] is not None:
            return False, "TILE_ALREADY_EXISTS"

        # Check tile data provided
        if not tile_data:
            return False, "TILE_DATA_REQUIRED"

        # Validate tile structure
        required_fields = ["type", "connections", "color"]
        for field in required_fields:
            if field not in tile_data:
                return False, f"TILE_MISSING_{field.upper()}"

        return True, "MOVE_VALID"

    @staticmethod
    def validate_game_config(config: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate game configuration.

        Args:
            config: Game configuration

        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        mode = config.get("mode", "zen")
        rows = config.get("rows", 6)
        cols = config.get("cols", 6)

        # Validate mode
        valid_modes = [FlowTilesValidator.MODE_ZEN, FlowTilesValidator.MODE_PUZZLE,
                       FlowTilesValidator.MODE_COLLABORATIVE, FlowTilesValidator.MODE_HARMONIC]
        if mode not in valid_modes:
            return False, "INVALID_GAME_MODE"

        # Validate grid size
        if not (3 <= rows <= 10) or not (3 <= cols <= 10):
            return False, "INVALID_GRID_SIZE"

        # Validate player count for multiplayer modes
        player_ids = config.get("player_ids", [])
        if mode == FlowTilesValidator.MODE_HARMONIC and len(player_ids) != 2:
            return False, "HARMONIC_MODE_REQUIRES_2_PLAYERS"

        if mode == FlowTilesValidator.MODE_COLLABORATIVE and not (2 <= len(player_ids) <= 4):
            return False, "COLLABORATIVE_MODE_REQUIRES_2_TO_4_PLAYERS"

        return True, "CONFIG_VALID"

    @staticmethod
    def calculate_beauty_score(flow: Dict[str, Any], grid: list) -> int:
        """
        Calculate beauty score for a flow path.

        Args:
            flow: Flow data with path
            grid: Game grid

        Returns:
            int: Beauty score (0-5 per tile)
        """
        path = flow.get("path", [])
        if len(path) < 2:
            return 0

        beauty_score = 0

        # Score based on path characteristics
        for i in range(len(path) - 1):
            current_idx = path[i]
            next_idx = path[i + 1]

            # Straight paths: +1
            if FlowTilesValidator._is_straight(current_idx, next_idx):
                beauty_score += 1
            # Gentle curves: +2
            elif FlowTilesValidator._is_curve(current_idx, next_idx, path, i):
                beauty_score += 2
            # Complex patterns: +3
            else:
                beauty_score += 3

        # Symmetry bonus
        if FlowTilesValidator._is_symmetric(path):
            beauty_score += 10

        return beauty_score

    @staticmethod
    def _is_straight(idx1: int, idx2: int, cols: int = 6) -> bool:
        """Check if two indices form a straight line"""
        row1, col1 = divmod(idx1, cols)
        row2, col2 = divmod(idx2, cols)
        return row1 == row2 or col1 == col2

    @staticmethod
    def _is_curve(idx1: int, idx2: int, path: list, position: int, cols: int = 6) -> bool:
        """Check if indices form a gentle curve"""
        if position == 0 or position >= len(path) - 2:
            return False

        prev_idx = path[position - 1]
        next_idx = path[position + 1]

        # Simple curve detection (can be enhanced)
        row1, col1 = divmod(prev_idx, cols)
        row2, col2 = divmod(idx1, cols)
        row3, col3 = divmod(next_idx, cols)

        # Check for 90-degree turn
        horizontal_change = abs(col3 - col1)
        vertical_change = abs(row3 - row1)

        return horizontal_change > 0 and vertical_change > 0

    @staticmethod
    def _is_symmetric(path: list) -> bool:
        """Check if path is symmetric"""
        if len(path) < 4:
            return False

        # Simple symmetry check
        half = len(path) // 2
        first_half = path[:half]
        second_half = path[half:][::-1]

        return first_half == second_half
