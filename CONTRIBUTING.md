# Contributing to GoodPlay Backend

Welcome to the GoodPlay community! This document provides comprehensive guidelines for developers who want to contribute to this open-source gaming platform that combines entertainment with social impact through charitable donations.

## 🎯 Project Vision

GoodPlay is a platform where users play games to earn virtual credits that can be donated to verified charitable organizations (ONLUS). Our mission is to gamify charitable giving while creating an engaging gaming experience.

## 📋 Table of Contents

1. [Getting Started](#getting-started)
2. [Architecture Overview](#architecture-overview)
3. [Development Workflow](#development-workflow)
4. [Game Development Guide](#game-development-guide)
5. [API Development Standards](#api-development-standards)
6. [Code Style Guidelines](#code-style-guidelines)
7. [Testing Requirements](#testing-requirements)
8. [Deployment Guidelines](#deployment-guidelines)
9. [Community Guidelines](#community-guidelines)

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- MongoDB 5.0+
- Git
- Code editor (VS Code recommended)

### Local Setup

```bash
# Clone the repository
git clone https://github.com/yourorg/goodplay-be.git
cd goodplay-be

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your MongoDB connection and other settings

# Start development server
python app.py
```

### Project Structure

```
goodplay-be/
├── app/                    # Main application package
│   ├── core/              # Core platform functionality
│   │   ├── models/        # Core data models (User, Config)
│   │   ├── repositories/  # Data access layer
│   │   ├── services/      # Business logic layer
│   │   └── controllers/   # HTTP route handlers
│   ├── games/             # Game engine and management
│   ├── social/            # Social features and gamification
│   ├── donations/         # Donation and wallet system
│   ├── onlus/            # ONLUS management
│   ├── preferences/       # User preferences system
│   └── admin/            # Administrative interface
├── config/               # Configuration files
├── tests/               # Test suite
├── docs/                # Additional documentation
└── requirements.txt     # Python dependencies
```

## 🏗️ Architecture Overview

### Modular Architecture

GoodPlay follows a **modular monolithic architecture** where each feature is organized into self-contained modules:

- **Core Module**: Authentication, user management, health checks
- **Games Module**: Game engine, session management, game library
- **Social Module**: Achievements, leaderboards, friend systems
- **Donations Module**: Wallet system, donation processing
- **ONLUS Module**: Charitable organization management
- **Admin Module**: Administrative controls and monitoring

### Design Patterns

#### 1. Repository Pattern
Data access is abstracted through repositories:

```python
# app/games/repositories/game_repository.py
class GameRepository(BaseRepository):
    def __init__(self):
        super().__init__('games')

    def find_active_games(self):
        return self.find_many({'is_active': True})
```

#### 2. Service Layer Pattern
Business logic is centralized in services:

```python
# app/games/services/game_service.py
class GameService:
    def start_game_session(self, user_id: str, game_id: str) -> Tuple[bool, str, Optional[Dict]]:
        # Validation
        # Business logic
        # Return (success, message_constant, data)
```

#### 3. Controller Pattern
HTTP request handling with consistent response format:

```python
# app/games/controllers/game_controller.py
@games_bp.route('/sessions', methods=['POST'])
@auth_required
def start_session(current_user):
    success, message, result = game_service.start_game_session(
        current_user.get_id(), request.json['game_id']
    )
    return success_response(message, result) if success else error_response(message)
```

### Database Design

#### Embedded vs Referenced Documents

- **Embedded**: User preferences, gaming stats (frequently accessed together)
- **Referenced**: Games, ONLUS organizations (independent entities)

#### Indexing Strategy

```python
# Essential indexes for performance
db.users.create_index([('email', 1)], unique=True)
db.games.create_index([('category', 1), ('is_active', 1)])
db.game_sessions.create_index([('user_id', 1), ('created_at', -1)])
```

## 🎮 Game Development Guide

### Overview

GoodPlay uses a **plugin system** for game development. Each game is implemented as a self-contained plugin that follows a standardized interface.

For complete documentation on developing games, see:
- **📘 [Game Development Guide](docs/GAME_DEVELOPMENT_GUIDE.md)** - Complete backend development guide
- **📗 [Frontend Integration Guide](docs/FRONTEND_GAME_INTEGRATION_GUIDE.md)** - Frontend integration patterns
- **📕 [Tic Tac Toe Implementation](app/games/plugins/tic_tac_toe/IMPLEMENTATION_NOTES.md)** - Reference implementation

### Quick Start

#### 1. Create Plugin Structure

```bash
cd app/games/plugins
mkdir your_game
cd your_game
touch __init__.py plugin.json main.py
```

#### 2. Define Plugin Metadata (plugin.json)

```json
{
  "id": "your_game",
  "name": "Your Game",
  "version": "1.0.0",
  "description": "Game description",
  "author": "Your Name",
  "category": "puzzle",
  "main_module": "main",
  "dependencies": {
    "python_packages": [],
    "plugins": []
  },
  "metadata": {
    "min_players": 1,
    "max_players": 4,
    "estimated_duration_minutes": 10,
    "difficulty_level": "medium",
    "requires_internet": false,
    "credit_rate": 1.0
  }
}
```

#### 3. Implement Game Logic (main.py)

```python
from app.games.core.game_plugin import GamePlugin, GameRules, GameSession, SessionResult
import uuid
from typing import Dict, Any, Optional
from datetime import datetime


class YourGame(GamePlugin):
    """Your game plugin"""

    def __init__(self):
        super().__init__()
        self.name = "Your Game"
        self.version = "1.0.0"
        self.description = "Game description"
        self.category = "puzzle"
        self.author = "Your Name"
        self.credit_rate = 1.0
        self.active_sessions = {}

    def initialize(self) -> bool:
        """Initialize plugin"""
        self.is_initialized = True
        return True

    def start_session(self, user_id: str, session_config: Optional[Dict[str, Any]] = None) -> GameSession:
        """Start new game session"""
        session_id = str(uuid.uuid4())

        # Initialize game state
        game_state = {
            "score": 0,
            "level": 1,
            "game_over": False
        }
        self.active_sessions[session_id] = game_state

        return GameSession(
            session_id=session_id,
            user_id=user_id,
            game_id="your_game",
            status="active",
            current_state=game_state,
            started_at=datetime.utcnow()
        )

    def end_session(self, session_id: str, reason: str = "completed") -> SessionResult:
        """End game session"""
        game_state = self.active_sessions[session_id]

        return SessionResult(
            session_id=session_id,
            final_score=game_state["score"],
            credits_earned=self._calculate_credits(game_state),
            completion_time_seconds=180,
            achievements_unlocked=[],
            statistics=game_state
        )

    def get_rules(self) -> GameRules:
        """Get game rules"""
        return GameRules(
            min_players=1,
            max_players=1,
            estimated_duration_minutes=10,
            difficulty_level="medium",
            requires_internet=False,
            description="Your game description",
            instructions="How to play..."
        )

    def validate_move(self, session_id: str, move: Dict[str, Any]) -> bool:
        """Validate and process move"""
        if session_id not in self.active_sessions:
            return False

        game_state = self.active_sessions[session_id]

        # Your game logic here
        # ...

        return True

    def get_session_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get current state"""
        return self.active_sessions.get(session_id)

    def update_session_state(self, session_id: str, new_state: Dict[str, Any]) -> bool:
        """Update state"""
        if session_id in self.active_sessions:
            self.active_sessions[session_id].update(new_state)
            return True
        return False

    def _calculate_credits(self, game_state: Dict) -> int:
        """Calculate credits earned"""
        return int(game_state["score"] / 100)


# Export plugin class
GamePluginClass = YourGame
```

### Plugin Auto-Discovery

Plugins are automatically discovered and loaded on server startup. No manual registration required!

```python
# Plugins in app/games/plugins/ are auto-loaded
from app.games.core.plugin_manager import plugin_manager

# View loaded plugins
plugins = plugin_manager.list_available_plugins()
```

### Game Modes

Plugins can support multiple game modes:

1. **Single Player (vs AI)**: Player competes against computer
2. **Local Multiplayer**: Players on same device
3. **Online Multiplayer**: Players on different devices (uses WebSocket)

See the **[Game Development Guide](docs/GAME_DEVELOPMENT_GUIDE.md)** for detailed implementation patterns for each mode.

### Integration with Platform Features

#### Achievements
```python
# Return achievement IDs in SessionResult
achievements_unlocked = ["FIRST_WIN", "HIGH_SCORE", "PERFECT_GAME"]
```

#### Credits
```python
# Calculate based on play time and performance
credits = int(play_minutes * self.credit_rate * performance_multiplier)
```

#### Leaderboards
```python
# Statistics automatically submitted to leaderboards
statistics = {
    "final_score": score,
    "level_reached": level,
    "accuracy": accuracy
}
```

### Testing Your Plugin

```python
# Manual test
from app.games.plugins.your_game.main import YourGame

game = YourGame()
game.initialize()

session = game.start_session("user123")
print("Session started:", session.session_id)

game.validate_move(session.session_id, {"action": "test"})
state = game.get_session_state(session.session_id)
print("Current state:", state)

result = game.end_session(session.session_id)
print("Final score:", result.final_score)
```

### Resources

- **Complete Guide**: See [docs/GAME_DEVELOPMENT_GUIDE.md](docs/GAME_DEVELOPMENT_GUIDE.md) for:
  - Detailed API reference
  - Implementation patterns
  - Best practices
  - Security considerations
  - Performance optimization
  - Advanced examples

- **Frontend Integration**: See [docs/FRONTEND_GAME_INTEGRATION_GUIDE.md](docs/FRONTEND_GAME_INTEGRATION_GUIDE.md) for:
  - API endpoints usage
  - WebSocket integration
  - State management
  - Code examples (React, Vue, Vanilla JS)

- **Reference Implementation**: See [app/games/plugins/tic_tac_toe/](app/games/plugins/tic_tac_toe/) for:
  - Complete working example
  - AI implementation
  - Multiple game modes
  - Implementation notes

## 🔌 API Development Standards

### Response Format Consistency

All API endpoints must return consistent response formats with constant message keys for UI localization:

#### Success Response
```python
{
    "success": true,
    "message": "OPERATION_SUCCESS",  # Constant key for UI localization
    "data": {
        # Response data
    },
    "timestamp": "2024-01-15T10:30:00Z"
}
```

#### Error Response
```python
{
    "success": false,
    "message": "VALIDATION_ERROR",  # Constant key for UI localization
    "error_details": {
        # Specific error information
    },
    "timestamp": "2024-01-15T10:30:00Z"
}
```

### Message Constants

All response messages must use predefined constants defined in each module:

```python
# app/games/constants.py
GAME_CONSTANTS = {
    # Success messages
    'GAME_SESSION_STARTED': 'GAME_SESSION_STARTED',
    'GAME_MOVE_VALID': 'GAME_MOVE_VALID',
    'GAME_SESSION_COMPLETED': 'GAME_SESSION_COMPLETED',

    # Error messages
    'GAME_NOT_FOUND': 'GAME_NOT_FOUND',
    'GAME_SESSION_INVALID': 'GAME_SESSION_INVALID',
    'GAME_MOVE_INVALID': 'GAME_MOVE_INVALID'
}
```

### Service Method Pattern

```python
def service_method(self, params) -> Tuple[bool, str, Optional[Dict]]:
    """
    Standard service method pattern

    Returns:
        Tuple[bool, str, Optional[Dict]]: (success, message_constant, data)
    """
    # 1. Input validation
    if not self._validate_input(params):
        return False, "VALIDATION_ERROR", None

    try:
        # 2. Business logic
        result = self._perform_operation(params)

        # 3. Success logging
        current_app.logger.info(f"Operation completed successfully")
        return True, "OPERATION_SUCCESS", result

    except Exception as e:
        # 4. Error logging and handling
        current_app.logger.error(f"Operation failed: {str(e)}")
        return False, "OPERATION_FAILED", None
```

### API Documentation Requirements

#### Modular Documentation Structure

All API documentation is organized modularly under the `docs/` directory:

```
docs/
├── openapi.yaml              # Main OpenAPI specification
├── openapi/                  # Modular OpenAPI specifications
│   ├── core.yaml            # Authentication & user management
│   ├── social.yaml          # Social features & relationships
│   ├── games.yaml           # Game engine & sessions
│   └── leaderboards.yaml    # Impact scores & leaderboards
├── postman/                  # Modular Postman collections
│   ├── core_collection.json        # Core API collection
│   ├── social_collection.json      # Social API collection
│   ├── games_collection.json       # Games API collection
│   └── leaderboards_collection.json # Leaderboards API collection
└── API_ORGANIZATION.md       # Documentation guide
```

#### Documentation Maintenance Workflow

When adding new endpoints or modifying existing ones:

1. **Choose the Appropriate Module**: Determine which module your endpoint belongs to (core, social, games, leaderboards)

2. **Update Module OpenAPI Spec**: Add/modify endpoints in the appropriate `docs/openapi/{module}.yaml` file:

```yaml
# docs/openapi/games.yaml
/api/games/{gameId}/sessions:
  post:
    summary: Start a new game session
    parameters:
      - name: gameId
        in: path
        required: true
        schema:
          type: string
    responses:
      200:
        description: Session started successfully
        content:
          application/json:
            schema:
              type: object
              properties:
                success:
                  type: boolean
                  example: true
                message:
                  type: string
                  enum: ["GAME_SESSION_STARTED"]
                data:
                  $ref: '#/components/schemas/GameSession'
```

3. **Update Main OpenAPI Spec**: If adding new paths, reference them in `docs/openapi.yaml`:

```yaml
# docs/openapi.yaml
paths:
  /api/games/{gameId}/sessions:
    $ref: './openapi/games.yaml#/paths/~1api~1games~1{gameId}~1sessions'
```

4. **Update Postman Collection**: Add/modify requests in the appropriate `docs/postman/{module}_collection.json` file:

```json
{
  "name": "Start Game Session",
  "request": {
    "method": "POST",
    "header": [
      {
        "key": "Authorization",
        "value": "Bearer {{token}}"
      }
    ],
    "url": {
      "raw": "{{baseUrl}}/api/games/{{gameId}}/sessions",
      "host": ["{{baseUrl}}"],
      "path": ["api", "games", "{{gameId}}", "sessions"]
    }
  }
}
```

5. **Validate Documentation**: Ensure consistency between OpenAPI spec and Postman collections

#### Module-Specific Documentation Guidelines

- **Core Module**: Authentication, user management, preferences, health checks
- **Social Module**: Friend relationships, blocking, user discovery, social stats
- **Games Module**: Game management, sessions, modes, challenges, teams, tournaments
- **Leaderboards Module**: Impact scores, leaderboards, privacy controls, ranking engine

#### Documentation Quality Standards

- **Complete Coverage**: Every endpoint must be documented in both OpenAPI and Postman
- **Consistent Naming**: Use consistent parameter names and response structures across modules
- **Example Values**: Provide realistic example values for all parameters and responses
- **Error Documentation**: Document all possible error responses with specific message constants
- **Environment Variables**: Use consistent variable names across Postman collections ({{baseUrl}}, {{token}}, etc.)

## 🎨 Code Style Guidelines

### Python Code Style

- Follow PEP 8 standards
- Use type hints for all function parameters and return values
- Maximum line length: 100 characters
- Use descriptive variable names

```python
# Good
def calculate_user_credits(user_id: str, session_duration: int) -> int:
    """Calculate credits earned by user during game session."""
    pass

# Bad
def calc(uid, dur):
    pass
```

### Documentation Standards

- All classes and functions must have docstrings
- Use Google-style docstrings
- Include parameter types and return value descriptions

```python
def create_game_session(self, user_id: str, game_id: str) -> Tuple[bool, str, Optional[Dict]]:
    """
    Create a new game session for a user.

    Args:
        user_id (str): The user's unique identifier
        game_id (str): The game's unique identifier

    Returns:
        Tuple[bool, str, Optional[Dict]]: Success status, message constant, and session data

    Raises:
        ValidationError: If user_id or game_id is invalid
    """
```

### Import Organization

```python
# 1. Standard library imports
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# 2. Third-party imports
from flask import current_app, request
from bson import ObjectId

# 3. Local application imports
from app.core.models.user import User
from app.core.repositories.base_repository import BaseRepository
```

## 🧪 Testing Requirements

### Test Structure

```
tests/
├── unit/                  # Unit tests for individual components
│   ├── test_models/
│   ├── test_services/
│   └── test_repositories/
├── integration/          # Integration tests for API endpoints
│   ├── test_auth_api/
│   ├── test_games_api/
│   └── test_donations_api/
└── fixtures/            # Test data and mock objects
```

### Test Examples

#### Unit Test Example
```python
# tests/unit/test_services/test_game_service.py
import pytest
from unittest.mock import Mock, patch
from app.games.services.game_service import GameService

class TestGameService:
    def setup_method(self):
        self.game_service = GameService()

    @patch('app.games.repositories.game_repository.GameRepository.find_by_id')
    def test_start_game_session_success(self, mock_find_game):
        # Arrange
        mock_find_game.return_value = Mock(id='game123', is_active=True)

        # Act
        success, message, data = self.game_service.start_game_session('user123', 'game123')

        # Assert
        assert success is True
        assert message == 'GAME_SESSION_STARTED'
        assert data['session_id'] is not None
```

#### Integration Test Example
```python
# tests/integration/test_games_api/test_game_sessions.py
import pytest
from app import create_app

class TestGameSessionAPI:
    def setup_method(self):
        self.app = create_app('testing')
        self.client = self.app.test_client()

    def test_start_game_session(self):
        # Create test user and game
        # Get auth token

        response = self.client.post('/api/games/game123/sessions',
                                  headers={'Authorization': f'Bearer {token}'})

        assert response.status_code == 200
        assert response.json['success'] is True
        assert response.json['message'] == 'GAME_SESSION_STARTED'
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/unit/test_services/test_game_service.py

# Run with verbose output
pytest -v
```

## 🚀 Deployment Guidelines

### Environment Configuration

Create environment-specific configuration files:

```python
# config/settings.py
class DevelopmentConfig(Config):
    DEBUG = True
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/goodplay_dev')
    LOG_LEVEL = 'DEBUG'

class ProductionConfig(Config):
    DEBUG = False
    MONGO_URI = os.getenv('MONGO_URI')
    LOG_LEVEL = 'INFO'
```

### Docker Configuration

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "app:create_app()"]
```

### Health Checks

Ensure your features include health check endpoints:

```python
@module_bp.route('/health', methods=['GET'])
def module_health():
    """Health check for this module"""
    return {
        'status': 'healthy',
        'module': 'games',
        'timestamp': datetime.now(timezone.utc).isoformat()
    }
```

## 🤝 Community Guidelines

### Pull Request Process

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/game-xyz`
3. **Commit** changes with clear messages
4. **Test** thoroughly (unit + integration tests)
5. **Update** documentation and OpenAPI spec
6. **Submit** pull request with detailed description

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] New feature
- [ ] Bug fix
- [ ] Game integration
- [ ] Documentation update
- [ ] Performance improvement

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed
- [ ] OpenAPI spec updated

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex logic
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
```

### Code Review Guidelines

#### For Reviewers
- Focus on architecture, security, and maintainability
- Suggest improvements, don't just point out problems
- Ask questions if logic isn't clear
- Approve when code meets standards

#### For Contributors
- Respond to feedback constructively
- Make requested changes promptly
- Explain design decisions when asked
- Test thoroughly before requesting review

### Issue Templates

#### Bug Report
```markdown
**Bug Description**
Clear description of the bug

**Steps to Reproduce**
1. Step one
2. Step two
3. Expected vs actual result

**Environment**
- OS: [e.g., Ubuntu 20.04]
- Python version: [e.g., 3.9.2]
- Browser: [e.g., Chrome 96]

**Additional Context**
Screenshots, logs, or other helpful information
```

#### Feature Request
```markdown
**Feature Description**
Clear description of the proposed feature

**Use Case**
Why is this feature needed? What problem does it solve?

**Proposed Solution**
How should this feature work?

**Additional Context**
Mockups, examples, or related features
```

### Game Contribution Guidelines

#### Submitting a New Game

1. **Proposal**: Create an issue with game concept and design
2. **Discussion**: Community review and feedback
3. **Implementation**: Follow game development guide
4. **Testing**: Comprehensive testing including edge cases
5. **Documentation**: Update API docs and user guides
6. **Review**: Code review by maintainers
7. **Integration**: Merge and deployment

#### Game Quality Standards

- **Performance**: Must handle 1000+ concurrent sessions
- **Security**: Input validation and XSS prevention
- **Accessibility**: Support for screen readers and keyboard navigation
- **Internationalization**: All text must use constant keys
- **Mobile**: Responsive design for mobile devices

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and ideas
- **Discord**: Real-time community chat (link in README)
- **Email**: security@goodplay.org for security issues

### Recognition System

Contributors are recognized through:
- **Commit attribution**: All commits preserve author information
- **Contributor list**: Updated in README.md
- **Special mentions**: In release notes for significant contributions
- **Game creator credits**: In-game attribution for game developers

## 📚 Additional Resources

### Learning Resources

- **Flask Documentation**: https://flask.palletsprojects.com/
- **MongoDB Python Driver**: https://pymongo.readthedocs.io/
- **JWT Authentication**: https://flask-jwt-extended.readthedocs.io/
- **OpenAPI Specification**: https://swagger.io/specification/

### Development Tools

- **API Documentation**: Swagger UI available at `/api/docs`
- **OpenAPI Specifications**: Modular specs in `docs/openapi/` directory
- **Postman Collections**: Modular collections in `docs/postman/` directory
  - Core API: `docs/postman/core_collection.json`
  - Social API: `docs/postman/social_collection.json`
  - Games API: `docs/postman/games_collection.json`
  - Leaderboards API: `docs/postman/leaderboards_collection.json`
- **Database GUI**: MongoDB Compass for database exploration
- **Logging**: Check `logs/` directory for application logs

### Community Resources

- **Architecture Decisions**: See `docs/adr/` directory
- **API Examples**: Check `examples/` directory
- **Game Templates**: Available in `templates/games/`

---

## ⚡ Quick Start Checklist

For new contributors, here's your quick start checklist:

- [ ] Read this entire document
- [ ] Set up local development environment
- [ ] Run the test suite successfully
- [ ] Make a small test change and submit a PR
- [ ] Join the community Discord
- [ ] Choose your first issue from "good first issue" label

Welcome to the GoodPlay community! We're excited to see what amazing games and features you'll contribute to our platform for social good. 🎮❤️

---

*For questions about this documentation or the contribution process, please create an issue or reach out on Discord.*