import random
import json
from typing import Dict, Any, Optional
from datetime import datetime

from app.games.core.game_plugin import GamePlugin, GameRules, GameSession, SessionResult

class NumberGuessingGame(GamePlugin):
    """
    Example game plugin: Number Guessing Game

    Players try to guess a randomly generated number between 1 and 100.
    They have 10 attempts and get hints (higher/lower) after each guess.
    """

    def __init__(self):
        super().__init__()
        self.name = "Number Guessing Game"
        self.version = "1.0.0"
        self.description = "A simple number guessing game where players try to guess a randomly generated number between 1 and 100"
        self.category = "puzzle"
        self.author = "GoodPlay Team"
        self.credit_rate = 0.5  # Credits per minute

        # Game-specific settings
        self.min_number = 1
        self.max_number = 100
        self.max_attempts = 10

        # Active sessions storage (in production, this would be in database)
        self.active_sessions: Dict[str, Dict[str, Any]] = {}

    def initialize(self) -> bool:
        """Initialize the game plugin"""
        try:
            self.is_initialized = True
            return True
        except Exception as e:
            print(f"Failed to initialize NumberGuessingGame: {e}")
            return False

    def start_session(self, user_id: str, session_config: Optional[Dict[str, Any]] = None) -> GameSession:
        """Start a new game session"""
        import uuid

        session_id = str(uuid.uuid4())
        target_number = random.randint(self.min_number, self.max_number)

        # Initialize game state
        game_state = {
            "target_number": target_number,
            "attempts_remaining": self.max_attempts,
            "guesses_made": [],
            "hints_given": [],
            "game_over": False,
            "won": False
        }

        # Store session
        self.active_sessions[session_id] = game_state

        # Create session object
        session = GameSession(
            session_id=session_id,
            user_id=user_id,
            game_id="number_guessing_game",
            status="active",
            current_state={
                "attempts_remaining": self.max_attempts,
                "guesses_made": [],
                "hints": [],
                "range": f"{self.min_number}-{self.max_number}"
            },
            started_at=datetime.utcnow()
        )

        return session

    def end_session(self, session_id: str, reason: str = "completed") -> SessionResult:
        """End a game session"""
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")

        game_state = self.active_sessions[session_id]

        # Calculate final score
        attempts_used = self.max_attempts - game_state["attempts_remaining"]
        base_score = 1000 if game_state["won"] else 0

        # Bonus for fewer attempts (only if won)
        if game_state["won"]:
            attempt_bonus = max(0, (self.max_attempts - attempts_used) * 50)
            final_score = base_score + attempt_bonus
        else:
            # Partial score for trying
            final_score = attempts_used * 10

        # Calculate credits (based on time spent)
        credits_earned = max(1, int(final_score / 100))

        # Determine achievements
        achievements = []
        if game_state["won"]:
            achievements.append("GAME_COMPLETED")
            if attempts_used == 1:
                achievements.append("LUCKY_GUESS")
            elif attempts_used <= 3:
                achievements.append("QUICK_SOLVER")
            elif attempts_used <= 5:
                achievements.append("GOOD_GUESSER")

        if attempts_used >= self.max_attempts and not game_state["won"]:
            achievements.append("PERSISTENT_PLAYER")

        # Create session result
        result = SessionResult(
            session_id=session_id,
            final_score=final_score,
            credits_earned=credits_earned,
            completion_time_seconds=300,  # Estimated average time
            achievements_unlocked=achievements,
            statistics={
                "attempts_used": attempts_used,
                "won": game_state["won"],
                "target_number": game_state["target_number"],
                "guesses": game_state["guesses_made"],
                "final_score": final_score
            }
        )

        # Clean up session
        del self.active_sessions[session_id]

        return result

    def get_rules(self) -> GameRules:
        """Get the game rules"""
        return GameRules(
            min_players=1,
            max_players=1,
            estimated_duration_minutes=5,
            difficulty_level="easy",
            requires_internet=False,
            description="Guess the secret number between 1 and 100!",
            instructions=f"""
# Number Guessing Game Rules

## Objective
Guess the secret number between {self.min_number} and {self.max_number} in {self.max_attempts} attempts or less.

## How to Play
1. Start a game session
2. Make a guess by sending a move with your number
3. Receive a hint: "higher", "lower", or "correct"
4. Use the hints to narrow down your next guess
5. Win by guessing correctly within {self.max_attempts} attempts

## Scoring
- Base score: 1000 points for winning
- Attempt bonus: 50 points for each unused attempt
- Participation points: 10 points per attempt (if you don't win)

## Move Format
Send moves as: {{"guess": your_number}}

Example: {{"guess": 50}}
            """
        )

    def validate_move(self, session_id: str, move: Dict[str, Any]) -> bool:
        """Validate a move (guess)"""
        if session_id not in self.active_sessions:
            return False

        game_state = self.active_sessions[session_id]

        # Check if game is over
        if game_state["game_over"]:
            return False

        # Check if move has required data
        if "guess" not in move:
            return False

        try:
            guess = int(move["guess"])
        except (ValueError, TypeError):
            return False

        # Check if guess is in valid range
        if not (self.min_number <= guess <= self.max_number):
            return False

        # Check if they have attempts remaining
        if game_state["attempts_remaining"] <= 0:
            return False

        # Process the guess
        self._process_guess(session_id, guess)

        return True

    def get_session_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get current session state"""
        if session_id not in self.active_sessions:
            return None

        game_state = self.active_sessions[session_id]

        return {
            "attempts_remaining": game_state["attempts_remaining"],
            "guesses_made": game_state["guesses_made"],
            "hints": game_state["hints_given"],
            "game_over": game_state["game_over"],
            "won": game_state["won"],
            "range": f"{self.min_number}-{self.max_number}"
        }

    def update_session_state(self, session_id: str, new_state: Dict[str, Any]) -> bool:
        """Update session state (limited updates allowed)"""
        if session_id not in self.active_sessions:
            return False

        # Only allow certain state updates to prevent cheating
        allowed_updates = ["last_hint_acknowledged"]

        for key, value in new_state.items():
            if key in allowed_updates:
                self.active_sessions[session_id][key] = value

        return True

    def _process_guess(self, session_id: str, guess: int) -> None:
        """Process a player's guess"""
        game_state = self.active_sessions[session_id]
        target = game_state["target_number"]

        # Record the guess
        game_state["guesses_made"].append(guess)
        game_state["attempts_remaining"] -= 1

        # Generate hint
        if guess == target:
            hint = "correct"
            game_state["won"] = True
            game_state["game_over"] = True
        elif guess < target:
            hint = "higher"
        else:
            hint = "lower"

        game_state["hints_given"].append({
            "guess": guess,
            "hint": hint,
            "attempts_remaining": game_state["attempts_remaining"]
        })

        # Check if game should end
        if game_state["attempts_remaining"] <= 0 and not game_state["won"]:
            game_state["game_over"] = True
            game_state["hints_given"].append({
                "message": f"Game over! The number was {target}",
                "game_over": True
            })

# This is what the plugin system will look for
GamePluginClass = NumberGuessingGame