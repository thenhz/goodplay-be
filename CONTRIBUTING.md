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

### Game Integration Architecture

Games in GoodPlay are integrated through a standardized API that handles:
- Session management
- Credit calculation
- Progress tracking
- Achievement integration

### Creating a New Game

#### 1. Game Model Definition

```python
# app/games/models/game.py
class Game:
    def __init__(self, name, description, category, version, credit_rate,
                 game_config=None, requirements=None, **kwargs):
        self.name = name
        self.description = description
        self.category = category  # 'puzzle', 'action', 'strategy', etc.
        self.version = version
        self.credit_rate = credit_rate  # Credits per minute
        self.game_config = game_config or {}
        self.requirements = requirements or {}
        self.is_active = kwargs.get('is_active', True)
        # ... other fields
```

#### 2. Game Service Implementation

```python
# app/games/services/your_game_service.py
class YourGameService:
    def validate_game_move(self, session_id: str, move_data: dict) -> Tuple[bool, str, Optional[Dict]]:
        """Validate a game move and update session state"""
        try:
            # Game-specific validation logic
            # Update session progress
            # Calculate earned credits
            return True, "GAME_MOVE_VALID", {
                'new_state': updated_state,
                'credits_earned': credits,
                'achievements_unlocked': achievements
            }
        except Exception as e:
            current_app.logger.error(f"Game move validation failed: {str(e)}")
            return False, "GAME_MOVE_INVALID", None
```

#### 3. Game Controller Routes

```python
# app/games/controllers/your_game_controller.py
@your_game_bp.route('/move', methods=['POST'])
@auth_required
def make_move(current_user):
    """Handle game move submission"""
    data = request.get_json()
    success, message, result = your_game_service.validate_game_move(
        data['session_id'], data['move_data']
    )

    if success:
        return success_response(message, result)
    else:
        return error_response(message)
```

### Game Configuration Schema

```python
# Example game configuration
GAME_CONFIG = {
    'name': 'Word Puzzle Challenge',
    'category': 'puzzle',
    'difficulty_levels': ['easy', 'medium', 'hard'],
    'max_session_duration': 1800,  # 30 minutes
    'credit_rate': 2,  # 2 credits per minute
    'achievements': [
        {'id': 'first_win', 'name': 'First Victory', 'credits_bonus': 50},
        {'id': 'streak_5', 'name': '5 Win Streak', 'credits_bonus': 100}
    ],
    'ui_config': {
        'theme': 'colorful',
        'animations': True,
        'sound_effects': True
    }
}
```

### Game Session Lifecycle

#### Basic Session Management
1. **Session Start**: `POST /api/games/{game_id}/sessions`
2. **Move Validation**: `POST /api/games/sessions/{session_id}/moves`
3. **Progress Update**: `PUT /api/games/sessions/{session_id}/progress`
4. **Session End**: `PUT /api/games/sessions/{session_id}/complete`

#### Enhanced Session Management (GOO-9)
1. **Session Pause**: `PUT /api/games/sessions/{session_id}/pause`
2. **Session Resume**: `PUT /api/games/sessions/{session_id}/resume`
3. **Cross-Device Sync**: `POST /api/games/sessions/{session_id}/sync`
4. **Device Optimization**: `GET /api/games/sessions/{session_id}/device`
5. **Conflict Resolution**: `POST /api/games/sessions/{session_id}/conflicts/resolve`
6. **Active Sessions**: `GET /api/games/sessions/active`
7. **Conflict Detection**: `GET /api/games/sessions/conflicts`

### Enhanced Session Management Features (GOO-9)

#### Precise Time Tracking
The enhanced session management provides millisecond-accuracy time tracking:

```python
# Session model with enhanced time tracking
session = GameSession(
    user_id=user_id,
    game_id=game_id,
    play_duration=0,  # Milliseconds of actual play time
    paused_at=None,
    resumed_at=None,
    device_info={
        "device_id": "mobile-123",
        "device_type": "mobile",
        "platform": "iOS",
        "app_version": "1.2.0"
    }
)

# Pause/resume with precise time tracking
session.pause_session()  # Calculates and stores play duration
session.resume_session()  # Resumes time tracking
```

#### Cross-Device Synchronization
Sessions can be synchronized across multiple devices:

```python
# Sync session state from device
sync_data = {
    "device_state": {
        "current_state": {"level": 2, "score": 200},
        "play_duration_ms": 45000,
        "sync_version": 1,
        "new_moves": [{"action": "click", "position": {"x": 100, "y": 200}}],
        "new_achievements": ["LEVEL_2_REACHED"]
    },
    "device_info": {
        "device_id": "mobile-device-123",
        "device_type": "mobile",
        "platform": "iOS"
    }
}

# POST /api/games/sessions/{session_id}/sync
success, message, result = state_synchronizer.sync_session_state(
    session_id, sync_data["device_state"], sync_data["device_info"]
)
```

#### Conflict Resolution Strategies
When sync conflicts occur, multiple resolution strategies are available:

- **server_wins**: Server state takes precedence (default)
- **device_wins**: Device state overwrites server state
- **merge**: Intelligent merging of states (highest score, longest duration, union of achievements)

```python
# Resolve conflicts with merge strategy
resolution_data = {
    "device_state": conflicting_state,
    "resolution_strategy": "merge"
}

# POST /api/games/sessions/{session_id}/conflicts/resolve
```

#### Device-Specific Optimizations
Sessions can be optimized for different device types:

```python
# Device-specific optimizations
device_optimizations = {
    "mobile": {
        "reduce_state_size": True,
        "compress_moves": True,
        "sync_interval": 30  # seconds
    },
    "web": {
        "include_debug_info": True,
        "sync_interval": 60
    }
}
```

### Credit Calculation System

#### Legacy Credit Calculation
```python
def calculate_session_credits(session_duration_seconds: int, game_credit_rate: int,
                            performance_multiplier: float = 1.0) -> int:
    """
    Calculate credits earned for a game session

    Args:
        session_duration_seconds: Length of gaming session
        game_credit_rate: Credits per minute for this game
        performance_multiplier: Bonus/penalty based on performance (0.5-2.0)

    Returns:
        int: Total credits earned
    """
    base_credits = (session_duration_seconds / 60) * game_credit_rate
    return int(base_credits * performance_multiplier)
```

#### Precise Credit Calculation (GOO-9)
```python
def calculate_credits_earned_precise(play_duration_ms: int, credit_rate: float) -> int:
    """
    Calculate credits based on precise play duration (excludes paused time)

    Args:
        play_duration_ms: Actual play time in milliseconds
        credit_rate: Credits per minute for this game

    Returns:
        int: Total credits earned based on actual play time
    """
    play_duration_minutes = play_duration_ms / (1000 * 60)
    return int(play_duration_minutes * credit_rate)
```

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

### OpenAPI Documentation Requirements

Every endpoint must be fully documented in `openapi.yaml`:

```yaml
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
      400:
        description: Invalid game or user
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ErrorResponse'
            examples:
              game_not_found:
                value:
                  success: false
                  message: "GAME_NOT_FOUND"
              user_not_authorized:
                value:
                  success: false
                  message: "USER_NOT_AUTHORIZED"
```

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

- **Postman Collection**: Import `GoodPlay_API.postman_collection.json`
- **Database GUI**: MongoDB Compass for database exploration
- **API Testing**: Swagger UI available at `/api/docs`
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