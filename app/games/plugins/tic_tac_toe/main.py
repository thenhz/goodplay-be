"""
Tic Tac Toe Game Plugin

Supports three game modes:
1. vs_ai: Play against computer AI (Minimax algorithm)
2. local: Play against another player on the same device
3. online: Play against another player on different devices (uses multiplayer system)
"""

import random
import uuid
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from copy import deepcopy

from app.games.core.game_plugin import GamePlugin, GameRules, GameSession, SessionResult


class TicTacToeGame(GamePlugin):
    """
    Tic Tac Toe game plugin with AI, local, and online multiplayer support.
    """

    # Game constants
    EMPTY = None
    PLAYER_X = "X"
    PLAYER_O = "O"

    # Game modes
    MODE_VS_AI = "vs_ai"
    MODE_LOCAL = "local"
    MODE_ONLINE = "online"

    def __init__(self):
        super().__init__()
        self.name = "Tic Tac Toe"
        self.version = "1.0.0"
        self.description = "Classic Tic Tac Toe game with support for AI opponent, local multiplayer, and online multiplayer"
        self.category = "strategy"
        self.author = "GoodPlay Team"
        self.credit_rate = 0.3  # Credits per minute

        # Active sessions storage (in production, use MongoDB via repository)
        self.active_sessions: Dict[str, Dict[str, Any]] = {}

    def initialize(self) -> bool:
        """Initialize the game plugin"""
        try:
            self.is_initialized = True
            return True
        except Exception as e:
            print(f"Failed to initialize TicTacToeGame: {e}")
            return False

    def start_session(self, user_id: str, session_config: Optional[Dict[str, Any]] = None) -> GameSession:
        """
        Start a new game session.

        Args:
            user_id: The user starting the game
            session_config: Optional configuration with:
                - game_mode: "vs_ai", "local", or "online" (default: "vs_ai")
                - ai_difficulty: "easy", "medium", "hard" (default: "hard")
                - player_symbol: "X" or "O" (default: "X")
                - opponent_id: For online mode, the opponent user ID
        """
        session_config = session_config or {}
        session_id = str(uuid.uuid4())

        # Parse configuration
        game_mode = session_config.get("game_mode", self.MODE_VS_AI)
        ai_difficulty = session_config.get("ai_difficulty", "hard")
        player_symbol = session_config.get("player_symbol", self.PLAYER_X)
        opponent_id = session_config.get("opponent_id")

        # Validate game mode
        if game_mode not in [self.MODE_VS_AI, self.MODE_LOCAL, self.MODE_ONLINE]:
            game_mode = self.MODE_VS_AI

        # Initialize game state
        game_state = {
            "board": self._create_empty_board(),
            "current_player": self.PLAYER_X,  # X always starts
            "game_mode": game_mode,
            "ai_difficulty": ai_difficulty,
            "player_symbol": player_symbol,
            "ai_symbol": self.PLAYER_O if player_symbol == self.PLAYER_X else self.PLAYER_X,
            "opponent_id": opponent_id,
            "moves_history": [],
            "game_over": False,
            "winner": None,
            "winning_line": None,
            "is_draw": False,
            "move_count": 0
        }

        # Store session
        self.active_sessions[session_id] = game_state

        # If AI goes first (player chose O), make AI move
        if game_mode == self.MODE_VS_AI and player_symbol == self.PLAYER_O:
            self._make_ai_move(session_id)

        # Create session object
        session = GameSession(
            session_id=session_id,
            user_id=user_id,
            game_id="tic_tac_toe",
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
            completion_time_seconds=180,  # Average 3 minutes
            achievements_unlocked=achievements,
            statistics={
                "game_mode": game_state["game_mode"],
                "winner": game_state["winner"],
                "is_draw": game_state["is_draw"],
                "move_count": game_state["move_count"],
                "moves_history": game_state["moves_history"],
                "final_board": game_state["board"],
                "winning_line": game_state["winning_line"]
            }
        )

        # Clean up session
        del self.active_sessions[session_id]

        return result

    def get_rules(self) -> GameRules:
        """Get the game rules"""
        return GameRules(
            min_players=1,
            max_players=2,
            estimated_duration_minutes=3,
            difficulty_level="easy",
            requires_internet=False,
            description="Classic 3x3 Tic Tac Toe - Get three in a row to win!",
            instructions="""
# Tic Tac Toe Rules

## Objective
Be the first player to get three of your symbols (X or O) in a row - horizontally, vertically, or diagonally.

## How to Play

### Game Modes
1. **vs AI**: Play against the computer
   - Choose your difficulty: easy, medium, or hard
   - Choose your symbol: X (goes first) or O (goes second)

2. **Local**: Play against another player on the same device
   - Players take turns on the same screen

3. **Online**: Play against another player on a different device
   - Requires internet connection
   - Real-time multiplayer via WebSocket

### Making Moves
Send moves as: {"position": [row, col]}
- row: 0-2 (top to bottom)
- col: 0-2 (left to right)

Example: {"position": [0, 0]} places your symbol in the top-left corner
Example: {"position": [1, 1]} places your symbol in the center

### Board Layout
```
[0,0] | [0,1] | [0,2]
------|-------|------
[1,0] | [1,1] | [1,2]
------|-------|------
[2,0] | [2,1] | [2,2]
```

### Winning
- Get three symbols in a row (horizontal, vertical, or diagonal)
- If all 9 squares are filled with no winner, it's a draw

## Scoring
- **Win**: 1000 points
- **Draw**: 300 points
- **Loss**: 100 points (participation)
- **Quick Win Bonus**: +200 points (win in 5 moves or less)
- **Perfect Win Bonus**: +500 points (win without opponent getting 2 in a row)

## AI Difficulty Levels
- **Easy**: Random valid moves
- **Medium**: Blocks obvious wins, takes winning moves
- **Hard**: Unbeatable Minimax algorithm
            """
        )

    def validate_move(self, session_id: str, move: Dict[str, Any]) -> bool:
        """
        Validate and process a player's move.

        Args:
            session_id: The session ID
            move: Move data with format {"position": [row, col]}

        Returns:
            bool: True if move is valid and processed, False otherwise
        """
        if session_id not in self.active_sessions:
            return False

        game_state = self.active_sessions[session_id]

        # Check if game is over
        if game_state["game_over"]:
            return False

        # Validate move format
        if "position" not in move:
            return False

        position = move["position"]
        if not isinstance(position, list) or len(position) != 2:
            return False

        row, col = position

        # Validate position bounds
        if not (0 <= row <= 2 and 0 <= col <= 2):
            return False

        # Check if position is empty
        if game_state["board"][row][col] is not None:
            return False

        # In online mode, validate it's the current player's turn
        # (This would be handled by the multiplayer system in production)

        # Make the move
        self._make_move(session_id, row, col, game_state["current_player"])

        # If playing vs AI and game is not over, make AI move
        if (game_state["game_mode"] == self.MODE_VS_AI and
            not game_state["game_over"]):
            self._make_ai_move(session_id)

        return True

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

        # For online multiplayer, allow board synchronization
        # In production, this would be validated by the multiplayer system
        allowed_updates = ["last_sync_time", "opponent_connected"]

        for key, value in new_state.items():
            if key in allowed_updates:
                self.active_sessions[session_id][key] = value

        return True

    # ==================== PRIVATE HELPER METHODS ====================

    def _create_empty_board(self) -> List[List[Optional[str]]]:
        """Create an empty 3x3 board"""
        return [[None, None, None] for _ in range(3)]

    def _get_public_state(self, session_id: str) -> Dict[str, Any]:
        """Get the public state of a session (hides internal data)"""
        game_state = self.active_sessions[session_id]

        return {
            "board": game_state["board"],
            "current_player": game_state["current_player"],
            "game_mode": game_state["game_mode"],
            "player_symbol": game_state["player_symbol"],
            "moves_history": game_state["moves_history"],
            "game_over": game_state["game_over"],
            "winner": game_state["winner"],
            "is_draw": game_state["is_draw"],
            "winning_line": game_state["winning_line"],
            "move_count": game_state["move_count"]
        }

    def _make_move(self, session_id: str, row: int, col: int, player: str) -> None:
        """Make a move on the board"""
        game_state = self.active_sessions[session_id]

        # Place the symbol
        game_state["board"][row][col] = player
        game_state["move_count"] += 1

        # Record move
        game_state["moves_history"].append({
            "player": player,
            "position": [row, col],
            "move_number": game_state["move_count"]
        })

        # Check for win or draw
        winner, winning_line = self._check_winner(game_state["board"])

        if winner:
            game_state["game_over"] = True
            game_state["winner"] = winner
            game_state["winning_line"] = winning_line
        elif self._is_board_full(game_state["board"]):
            game_state["game_over"] = True
            game_state["is_draw"] = True
        else:
            # Switch player
            game_state["current_player"] = (
                self.PLAYER_O if player == self.PLAYER_X else self.PLAYER_X
            )

    def _make_ai_move(self, session_id: str) -> None:
        """Make an AI move based on difficulty"""
        game_state = self.active_sessions[session_id]
        ai_symbol = game_state["ai_symbol"]
        difficulty = game_state["ai_difficulty"]

        if difficulty == "easy":
            row, col = self._get_random_move(game_state["board"])
        elif difficulty == "medium":
            row, col = self._get_medium_ai_move(game_state["board"], ai_symbol)
        else:  # hard
            row, col = self._get_best_move(game_state["board"], ai_symbol)

        if row is not None and col is not None:
            self._make_move(session_id, row, col, ai_symbol)

    def _get_random_move(self, board: List[List[Optional[str]]]) -> Tuple[Optional[int], Optional[int]]:
        """Get a random valid move (easy AI)"""
        empty_positions = []
        for row in range(3):
            for col in range(3):
                if board[row][col] is None:
                    empty_positions.append((row, col))

        if empty_positions:
            return random.choice(empty_positions)
        return None, None

    def _get_medium_ai_move(self, board: List[List[Optional[str]]], ai_symbol: str) -> Tuple[Optional[int], Optional[int]]:
        """Get a move for medium difficulty AI (blocks wins, takes wins, otherwise random)"""
        player_symbol = self.PLAYER_O if ai_symbol == self.PLAYER_X else self.PLAYER_X

        # 1. Check if AI can win in one move
        for row in range(3):
            for col in range(3):
                if board[row][col] is None:
                    # Try this move
                    board[row][col] = ai_symbol
                    winner, _ = self._check_winner(board)
                    board[row][col] = None  # Undo

                    if winner == ai_symbol:
                        return row, col

        # 2. Check if player can win in one move and block it
        for row in range(3):
            for col in range(3):
                if board[row][col] is None:
                    # Try player move
                    board[row][col] = player_symbol
                    winner, _ = self._check_winner(board)
                    board[row][col] = None  # Undo

                    if winner == player_symbol:
                        return row, col

        # 3. Take center if available
        if board[1][1] is None:
            return 1, 1

        # 4. Take a corner
        corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
        random.shuffle(corners)
        for row, col in corners:
            if board[row][col] is None:
                return row, col

        # 5. Random move
        return self._get_random_move(board)

    def _get_best_move(self, board: List[List[Optional[str]]], ai_symbol: str) -> Tuple[Optional[int], Optional[int]]:
        """Get the best move using Minimax algorithm (hard AI - unbeatable)"""
        best_score = float('-inf')
        best_move = None

        for row in range(3):
            for col in range(3):
                if board[row][col] is None:
                    # Try this move
                    board[row][col] = ai_symbol
                    score = self._minimax(board, 0, False, ai_symbol)
                    board[row][col] = None  # Undo

                    if score > best_score:
                        best_score = score
                        best_move = (row, col)

        return best_move if best_move else self._get_random_move(board)

    def _minimax(self, board: List[List[Optional[str]]], depth: int, is_maximizing: bool, ai_symbol: str) -> int:
        """
        Minimax algorithm for optimal Tic Tac Toe play.

        Args:
            board: Current board state
            depth: Current depth in the game tree
            is_maximizing: True if maximizing player (AI), False if minimizing (human)
            ai_symbol: AI's symbol (X or O)

        Returns:
            int: Score of the position
        """
        player_symbol = self.PLAYER_O if ai_symbol == self.PLAYER_X else self.PLAYER_X

        # Check terminal states
        winner, _ = self._check_winner(board)

        if winner == ai_symbol:
            return 10 - depth  # Prefer faster wins
        elif winner == player_symbol:
            return depth - 10  # Prefer slower losses
        elif self._is_board_full(board):
            return 0  # Draw

        if is_maximizing:
            # AI's turn - maximize score
            max_score = float('-inf')
            for row in range(3):
                for col in range(3):
                    if board[row][col] is None:
                        board[row][col] = ai_symbol
                        score = self._minimax(board, depth + 1, False, ai_symbol)
                        board[row][col] = None
                        max_score = max(score, max_score)
            return max_score
        else:
            # Player's turn - minimize score
            min_score = float('inf')
            for row in range(3):
                for col in range(3):
                    if board[row][col] is None:
                        board[row][col] = player_symbol
                        score = self._minimax(board, depth + 1, True, ai_symbol)
                        board[row][col] = None
                        min_score = min(score, min_score)
            return min_score

    def _check_winner(self, board: List[List[Optional[str]]]) -> Tuple[Optional[str], Optional[List[Tuple[int, int]]]]:
        """
        Check if there's a winner.

        Returns:
            Tuple of (winner_symbol, winning_line_positions) or (None, None)
        """
        # Check rows
        for row in range(3):
            if (board[row][0] == board[row][1] == board[row][2] and
                board[row][0] is not None):
                return board[row][0], [(row, 0), (row, 1), (row, 2)]

        # Check columns
        for col in range(3):
            if (board[0][col] == board[1][col] == board[2][col] and
                board[0][col] is not None):
                return board[0][col], [(0, col), (1, col), (2, col)]

        # Check diagonals
        if (board[0][0] == board[1][1] == board[2][2] and
            board[0][0] is not None):
            return board[0][0], [(0, 0), (1, 1), (2, 2)]

        if (board[0][2] == board[1][1] == board[2][0] and
            board[0][2] is not None):
            return board[0][2], [(0, 2), (1, 1), (2, 0)]

        return None, None

    def _is_board_full(self, board: List[List[Optional[str]]]) -> bool:
        """Check if the board is completely filled"""
        for row in board:
            for cell in row:
                if cell is None:
                    return False
        return True

    def _calculate_score(self, game_state: Dict[str, Any], reason: str) -> int:
        """Calculate final score based on game outcome"""
        if reason == "abandoned":
            return 0

        player_symbol = game_state["player_symbol"]
        winner = game_state["winner"]
        is_draw = game_state["is_draw"]
        move_count = game_state["move_count"]

        base_score = 0

        if is_draw:
            base_score = 300
        elif winner == player_symbol:
            base_score = 1000

            # Quick win bonus (5 moves or less)
            if move_count <= 5:
                base_score += 200

            # Check if it was a perfect win (opponent never got 2 in a row)
            if self._is_perfect_win(game_state):
                base_score += 500
        else:
            # Participation points
            base_score = 100

        return base_score

    def _is_perfect_win(self, game_state: Dict[str, Any]) -> bool:
        """Check if the player won without letting opponent get 2 in a row"""
        # This is a simplified check - in reality you'd analyze the move history
        return game_state["move_count"] <= 5

    def _calculate_credits(self, game_state: Dict[str, Any], final_score: int) -> int:
        """Calculate credits earned"""
        # Base credits on score
        base_credits = max(1, int(final_score / 200))

        # Bonus for hard difficulty AI wins
        if (game_state["game_mode"] == self.MODE_VS_AI and
            game_state["ai_difficulty"] == "hard" and
            game_state["winner"] == game_state["player_symbol"]):
            base_credits += 5

        return base_credits

    def _determine_achievements(self, game_state: Dict[str, Any]) -> List[str]:
        """Determine which achievements were unlocked"""
        achievements = []

        player_symbol = game_state["player_symbol"]
        winner = game_state["winner"]

        # Completion achievements
        if game_state["game_over"]:
            achievements.append("GAME_COMPLETED")

        # Win achievements
        if winner == player_symbol:
            achievements.append("TIC_TAC_TOE_WINNER")

            if game_state["game_mode"] == self.MODE_VS_AI:
                if game_state["ai_difficulty"] == "hard":
                    achievements.append("AI_MASTER")
                elif game_state["ai_difficulty"] == "medium":
                    achievements.append("AI_CHALLENGER")

            # Quick win
            if game_state["move_count"] <= 5:
                achievements.append("SPEED_DEMON")

            # Perfect win
            if self._is_perfect_win(game_state):
                achievements.append("PERFECT_VICTORY")

        # Draw achievement
        if game_state["is_draw"]:
            achievements.append("STALEMATE")

        return achievements


# Export the plugin class
GamePluginClass = TicTacToeGame
