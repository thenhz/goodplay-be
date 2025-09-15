# 🎮 GoodPlay Game Engine Framework - Developer Guide

## 🎯 Overview

The GoodPlay Game Engine Framework (GOO-8) is a powerful, plugin-based system that allows developers to create and integrate games into the GoodPlay platform. Built with Flask and MongoDB, it provides a complete infrastructure for game management, session handling, and credit earning.

## 🏗️ Architecture

### Core Components

```
app/games/
├── core/                    # Plugin System Core
│   ├── game_plugin.py       # Base class for all games
│   ├── plugin_manager.py    # Plugin lifecycle management
│   └── plugin_registry.py   # Plugin storage and discovery
├── models/                  # Data Models
│   ├── game.py             # Game metadata model
│   └── game_session.py     # Game session model
├── repositories/           # Data Access Layer
│   ├── game_repository.py
│   └── game_session_repository.py
├── services/               # Business Logic
│   ├── game_service.py
│   └── game_session_service.py
├── controllers/            # API Endpoints
│   └── games_controller.py
└── plugins/               # Game Plugins Directory
    └── example_game/      # Example: Number Guessing Game
        ├── plugin.json    # Plugin manifest
        ├── main.py       # Plugin implementation
        └── __init__.py
```

### Plugin System Flow

1. **Discovery**: `PluginManager` scans `plugins/` directory on startup
2. **Registration**: Valid plugins are registered in `PluginRegistry`
3. **Instantiation**: Plugin classes are instantiated and initialized
4. **Session Management**: Games create and manage user sessions
5. **Credit Calculation**: Sessions track time and calculate earned credits

## 🔧 Creating a Game Plugin

### Step 1: Plugin Structure

Create a new directory in `app/games/plugins/your_game_name/`:

```
your_game_name/
├── plugin.json     # Plugin manifest
├── main.py        # Plugin implementation
└── __init__.py    # Python module init
```

### Step 2: Plugin Manifest (plugin.json)

```json
{
  "id": "your_game_id",
  "name": "Your Game Name",
  "version": "1.0.0",
  "description": "Description of your game",
  "author": "Your Name",
  "category": "puzzle",
  "main_module": "main",
  "dependencies": {
    "python_packages": [],
    "plugins": []
  },
  "metadata": {
    "min_players": 1,
    "max_players": 1,
    "estimated_duration_minutes": 10,
    "difficulty_level": "medium",
    "requires_internet": false,
    "credit_rate": 1.0
  }
}
```

### Step 3: Plugin Implementation (main.py)

```python
from app.games.core.game_plugin import GamePlugin, GameRules, GameSession, SessionResult
from typing import Dict, Any, Optional
from datetime import datetime
import uuid

class YourGamePlugin(GamePlugin):
    def __init__(self):
        super().__init__()
        self.name = "Your Game Name"
        self.version = "1.0.0"
        self.description = "Description of your game"
        self.category = "puzzle"
        self.author = "Your Name"
        self.credit_rate = 1.0

        # Game-specific storage
        self.active_sessions = {}

    def initialize(self) -> bool:
        """Initialize your game plugin"""
        try:
            # Perform any setup here
            self.is_initialized = True
            return True
        except Exception as e:
            print(f"Failed to initialize {self.name}: {e}")
            return False

    def start_session(self, user_id: str, session_config: Optional[Dict[str, Any]] = None) -> GameSession:
        """Start a new game session"""
        session_id = str(uuid.uuid4())

        # Initialize game state
        game_state = {
            "player_data": {},
            "game_status": "active",
            # Add your game-specific state here
        }

        # Store session
        self.active_sessions[session_id] = game_state

        # Create session object
        session = GameSession(
            session_id=session_id,
            user_id=user_id,
            game_id="your_game_id",
            status="active",
            current_state={
                # Public state visible to client
                "status": "waiting_for_input"
            },
            started_at=datetime.utcnow()
        )

        return session

    def end_session(self, session_id: str, reason: str = "completed") -> SessionResult:
        """End a game session and calculate results"""
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")

        game_state = self.active_sessions[session_id]

        # Calculate final score and credits
        final_score = self._calculate_score(game_state)
        credits_earned = max(1, int(final_score / 100))

        # Determine achievements
        achievements = self._calculate_achievements(game_state)

        # Create result
        result = SessionResult(
            session_id=session_id,
            final_score=final_score,
            credits_earned=credits_earned,
            completion_time_seconds=300,  # Calculate actual time
            achievements_unlocked=achievements,
            statistics=self._get_session_statistics(game_state)
        )

        # Cleanup
        del self.active_sessions[session_id]

        return result

    def get_rules(self) -> GameRules:
        """Return game rules and metadata"""
        return GameRules(
            min_players=1,
            max_players=1,
            estimated_duration_minutes=10,
            difficulty_level="medium",
            requires_internet=False,
            description="Your game description",
            instructions="""
# Your Game Instructions

## How to Play
1. Step one
2. Step two
3. Step three

## Scoring
- Points for X
- Bonus for Y

## Controls
Send moves as: {"action": "value"}
            """
        )

    def validate_move(self, session_id: str, move: Dict[str, Any]) -> bool:
        """Validate a player move"""
        if session_id not in self.active_sessions:
            return False

        game_state = self.active_sessions[session_id]

        # Implement your move validation logic
        if "action" not in move:
            return False

        # Process the move
        self._process_move(session_id, move)

        return True

    def get_session_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get current session state"""
        if session_id not in self.active_sessions:
            return None

        game_state = self.active_sessions[session_id]

        # Return public state visible to client
        return {
            "status": game_state.get("game_status", "active"),
            "player_data": game_state.get("player_data", {}),
            # Add other public state here
        }

    def update_session_state(self, session_id: str, new_state: Dict[str, Any]) -> bool:
        """Update session state (limited updates allowed)"""
        if session_id not in self.active_sessions:
            return False

        # Only allow certain state updates to prevent cheating
        allowed_updates = ["player_choice", "settings"]

        for key, value in new_state.items():
            if key in allowed_updates:
                self.active_sessions[session_id][key] = value

        return True

    # Helper methods (implement as needed)
    def _calculate_score(self, game_state: Dict[str, Any]) -> int:
        """Calculate final score"""
        return 100  # Implement your scoring logic

    def _calculate_achievements(self, game_state: Dict[str, Any]) -> list:
        """Calculate unlocked achievements"""
        achievements = []
        # Add achievement logic
        return achievements

    def _get_session_statistics(self, game_state: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed session statistics"""
        return {
            "moves_made": game_state.get("moves_count", 0),
            "final_status": game_state.get("game_status", "unknown")
        }

    def _process_move(self, session_id: str, move: Dict[str, Any]) -> None:
        """Process a validated move"""
        game_state = self.active_sessions[session_id]

        # Implement your move processing logic
        action = move.get("action")

        # Update game state based on action
        # ...

# This is what the plugin system will look for
GamePluginClass = YourGamePlugin
```

## 📊 Example: Number Guessing Game

The framework includes a complete example game that demonstrates all features:

**Location**: `app/games/plugins/example_game/`

**Game Flow**:
1. Player starts session
2. System generates random number (1-100)
3. Player makes guesses via moves: `{"guess": 42}`
4. System provides hints: "higher", "lower", "correct"
5. Game ends when number is guessed or attempts exhausted
6. Credits awarded based on performance

**Key Features Demonstrated**:
- Session state management
- Move validation and processing
- Score calculation with bonuses
- Achievement system
- Detailed game instructions

## 🚀 API Usage Examples

### 1. Get Available Games

```bash
curl -X GET "http://localhost:5000/api/games?category=puzzle&limit=10"
```

### 2. Start Game Session

```bash
curl -X POST "http://localhost:5000/api/games/{game_id}/sessions" \
  -H "Authorization: Bearer {access_token}" \
  -H "Content-Type: application/json" \
  -d '{"session_config": {"difficulty": "medium"}}'
```

**Response**:
```json
{
  "success": true,
  "message": "GAME_SESSION_STARTED_SUCCESS",
  "data": {
    "session": {
      "session_id": "uuid-session-12345",
      "user_id": "user123",
      "game_id": "number_guessing_game",
      "status": "active",
      "current_state": {
        "attempts_remaining": 10,
        "range": "1-100"
      }
    },
    "game": {
      "name": "Number Guessing Game",
      "description": "Guess the secret number!",
      "credit_rate": 0.5
    }
  }
}
```

### 3. Make a Move

```bash
curl -X POST "http://localhost:5000/api/games/sessions/{session_id}/moves" \
  -H "Authorization: Bearer {access_token}" \
  -H "Content-Type: application/json" \
  -d '{"move": {"guess": 42}}'
```

### 4. End Session

```bash
curl -X PUT "http://localhost:5000/api/games/sessions/{session_id}/end" \
  -H "Authorization: Bearer {access_token}" \
  -H "Content-Type: application/json" \
  -d '{"reason": "completed"}'
```

## 🔐 Security Considerations

### Plugin Validation

The system validates plugins on multiple levels:

1. **Manifest Validation**: Required fields, version format
2. **Code Validation**: Python syntax, class inheritance
3. **Dependency Checking**: Required packages and plugins
4. **Runtime Validation**: Method signatures, return types

### Session Security

- **User Ownership**: Users can only access their own sessions
- **State Isolation**: Plugin state is isolated per session
- **Move Validation**: All moves are validated before processing
- **Admin Protection**: Plugin installation requires admin privileges

### Data Protection

- **No Sensitive Data**: Never store passwords or tokens in game state
- **State Sanitization**: Public state excludes internal game secrets
- **Credit Verification**: Credits are calculated server-side only

## 🎖️ Achievement System

### Built-in Achievement Types

```python
# Common achievement patterns
ACHIEVEMENTS = {
    "FIRST_GAME": "Complete your first game",
    "QUICK_SOLVER": "Solve in under 3 attempts",
    "PERSISTENT_PLAYER": "Use all available attempts",
    "PERFECT_SCORE": "Achieve maximum score",
    "LUCKY_GUESS": "Guess correctly on first try",
    "COMEBACK_KING": "Win after being behind"
}
```

### Custom Achievements

```python
def _calculate_achievements(self, game_state: Dict[str, Any]) -> list:
    achievements = []

    if game_state.get("moves_count", 0) == 1:
        achievements.append("LUCKY_GUESS")

    if game_state.get("final_score", 0) >= 1000:
        achievements.append("HIGH_SCORER")

    return achievements
```

## 📈 Analytics and Statistics

### Session Statistics

Each completed session automatically tracks:

- **Performance Metrics**: Score, completion time, moves made
- **Engagement Data**: Session duration, pause/resume events
- **Achievement Progress**: Unlocked achievements, progress toward goals
- **Credit Earnings**: Credits earned, rate calculations

### Aggregated Analytics

The system provides platform-wide analytics:

```python
# Get game statistics
GET /api/games/stats

# Get user session statistics
GET /api/games/sessions/stats
```

## 🔧 Testing Your Plugin

### 1. Development Testing

```python
# Test plugin validation
python -c "
from app.games.core.plugin_manager import plugin_manager
result = plugin_manager.validate_plugin('your_game_id')
print(result)
"
```

### 2. Integration Testing

Use the Postman collection to test all endpoints:

1. Install your plugin (admin required)
2. Start a game session
3. Make several moves
4. End the session
5. Verify credits and achievements

### 3. Load Testing

Test with multiple concurrent sessions:

```python
# Simulate 10 concurrent players
import asyncio
import aiohttp

async def test_concurrent_sessions():
    # Implementation for load testing
    pass
```

## 🚀 Deployment

### Plugin Packaging

Create a zip file with your plugin:

```bash
cd app/games/plugins/your_game_name/
zip -r your_game_plugin.zip . -x "*.pyc" "__pycache__/*"
```

### Installation

Upload via API (admin required):

```bash
curl -X POST "http://localhost:5000/api/games/install" \
  -H "Authorization: Bearer {admin_token}" \
  -F "plugin_file=@your_game_plugin.zip" \
  -F "plugin_id=your_game_id"
```

### Plugin Discovery

The system automatically discovers and loads plugins on startup. For production:

1. Upload plugin files to server
2. Restart the application
3. Verify plugin is loaded: `GET /api/games/stats`

## 🤝 Best Practices

### Plugin Development

1. **Keep State Simple**: Minimize session state complexity
2. **Validate Everything**: Always validate user input
3. **Error Handling**: Gracefully handle all error conditions
4. **Documentation**: Provide clear game instructions
5. **Testing**: Test all game flows thoroughly

### Performance Optimization

1. **Memory Management**: Clean up session data promptly
2. **Database Queries**: Minimize database operations in game logic
3. **Caching**: Cache static game data when possible
4. **Async Operations**: Use async for I/O operations when needed

### User Experience

1. **Clear Instructions**: Provide detailed game rules
2. **Meaningful Feedback**: Give clear responses to user actions
3. **Progress Indicators**: Show game progress clearly
4. **Error Messages**: Provide helpful error messages

## 🛠️ Troubleshooting

### Common Issues

1. **Plugin Not Loading**
   - Check plugin.json syntax
   - Verify main module exists
   - Check class inheritance

2. **Session Creation Fails**
   - Verify game is active
   - Check user authentication
   - Review plugin initialization

3. **Moves Not Validating**
   - Check move format requirements
   - Verify session is active
   - Review validation logic

### Debug Mode

Enable debug logging for plugin development:

```python
import logging
logging.getLogger('app.games').setLevel(logging.DEBUG)
```

## 📚 Additional Resources

- **OpenAPI Documentation**: `/openapi.yaml` - Complete API specification
- **Postman Collection**: `GoodPlay_API.postman_collection.json` - API testing
- **Core Code**: `app/games/core/` - Plugin system implementation
- **Example Plugin**: `app/games/plugins/example_game/` - Complete working example

## 🎯 Next Steps

1. **Study the Example**: Review the Number Guessing Game implementation
2. **Create Your Plugin**: Follow the step-by-step guide above
3. **Test Thoroughly**: Use the provided tools for testing
4. **Deploy and Monitor**: Upload your plugin and monitor performance
5. **Iterate and Improve**: Gather user feedback and enhance your game

---

🎮 **Happy Game Development!** The GoodPlay Game Engine Framework provides everything you need to create engaging, credit-earning games for the platform.

For questions or support, refer to the Linear project GOO-8 or contact the development team.