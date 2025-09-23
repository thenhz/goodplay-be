# GoodPlay Backend - Development Guide for Claude

## Project Overview
This is a Flask-based REST API backend using MongoDB, JWT authentication, and following Repository Pattern + Service Layer architecture. All responses and logs are in English.

## Current Architecture

### Structure (Modular Architecture)
```
app/
├── core/            # Core platform functionality
│   ├── models/      # Core data models (User with preferences, Config)
│   ├── repositories/ # Core data access layer
│   ├── services/    # Core business logic
│   └── controllers/ # Core route handlers (auth, health)
├── preferences/     # User preferences API layer (works with User model)
├── social/          # Social features and gamification
│   ├── models/      # Achievement, Leaderboard models
│   ├── repositories/ # Social data access
│   ├── services/    # Social business logic
│   └── controllers/ # Social route handlers
├── games/           # Game engine and management
│   ├── models/      # Game, Session models
│   ├── repositories/ # Game data access
│   ├── services/    # Game business logic
│   ├── controllers/ # Game route handlers
│   ├── modes/       # Temporary game modes system
│   │   ├── models/  # GameMode, ModeSchedule models
│   │   ├── services/ # Mode management and scheduling
│   │   └── controllers/ # Mode admin APIs
│   ├── challenges/  # Direct player challenges
│   │   ├── models/  # Challenge, Participant models
│   │   ├── services/ # Challenge and matchmaking services
│   │   └── controllers/ # Challenge APIs
│   ├── teams/       # Global teams and tournaments
│   │   ├── models/  # GlobalTeam, TeamMember, Tournament models
│   │   ├── services/ # Team management and tournaments
│   │   └── controllers/ # Team APIs
│   └── scoring/     # Universal scoring system
│       └── services/ # Score normalization and ELO
├── donations/       # Donation and wallet system
│   ├── models/      # Wallet, Transaction models
│   ├── repositories/ # Financial data access
│   ├── services/    # Payment business logic
│   └── controllers/ # Donation route handlers
├── onlus/          # ONLUS management
│   ├── models/      # ONLUS, Campaign models
│   ├── repositories/ # ONLUS data access
│   ├── services/    # ONLUS business logic
│   └── controllers/ # ONLUS route handlers
└── admin/          # Administrative interface
    ├── models/      # Admin-specific models
    ├── repositories/ # Admin data access
    ├── services/    # Admin business logic
    └── controllers/ # Admin route handlers
```

### Key Design Patterns
- **Modular Architecture**: Feature-based modules (core, social, games, donations, onlus, admin)
- **Repository Pattern**: Data access abstraction in each module's `repositories/`
- **Service Layer**: Business logic in each module's `services/`
- **Dependency Injection**: Services use repositories, modules can depend on core
- **Decorator Pattern**: `@auth_required`, `@admin_required` for route protection
- **Blueprint Pattern**: Each module registers its own Flask blueprints

## Current Features
- ✅ User registration with validation
- ✅ JWT-based authentication (access + refresh tokens)
- ✅ User profile management
- ✅ User preferences management system
- ✅ CORS configuration
- ✅ Structured logging
- ✅ Environment-based configuration
- ✅ Gunicorn production setup

### Game Engine Features (GOO-8)
- ✅ Game plugin architecture with base GamePlugin class
- ✅ Plugin manager for dynamic game loading and lifecycle management
- ✅ Plugin registry system for game discovery and metadata
- ✅ Core game session management
- ✅ Game API endpoints for plugin management

### Enhanced Session Management Features (GOO-9)
- ✅ **Precise Time Tracking**: Millisecond-accuracy play duration with pause/resume support
- ✅ **Cross-Device Synchronization**: State sync across multiple devices with conflict resolution
- ✅ **Device Information Tracking**: Platform, device type, and app version tracking
- ✅ **Enhanced Session Model**: Extended with play_duration_ms, device_info, sync_version, paused_at, resumed_at
- ✅ **State Synchronizer Service**: Intelligent state merging and conflict resolution strategies
- ✅ **Enhanced API Endpoints**:
  - `POST /api/games/sessions/{session_id}/sync` - Session state synchronization
  - `GET /api/games/sessions/{session_id}/device` - Device-optimized session data
  - `POST /api/games/sessions/{session_id}/conflicts/resolve` - Manual conflict resolution
  - `GET /api/games/sessions/conflicts` - Check for sync conflicts
  - `GET /api/games/sessions/active` - Get all active/paused sessions
- ✅ **Precise Credit Calculation**: Credits based on actual play time excluding paused periods
- ✅ **Comprehensive Test Coverage**: 15+ new test cases covering all session management features

### Universal Scoring & Tournament System Features (GOO-10)
- ✅ **Game Modes System**: Temporary game modes with scheduling and automatic management
  - Normal Mode (always available), Challenge Mode, Team Tournament Mode
  - Admin control for mode activation/deactivation with time constraints
  - Automatic mode scheduling and cleanup
- ✅ **Direct Challenges System**: 1v1 and NvN player challenges with matchmaking
  - Direct challenge invitations with accept/decline workflow
  - Public NvN challenges that players can join
  - Automatic matchmaking system with skill-based opponent finding
  - Cross-game challenges with score normalization
  - Real-time challenge status and notifications
- ✅ **Global Teams System**: Automatic team assignment with tournaments
  - 4 default global teams with automatic user assignment
  - Team contribution tracking and leaderboards
  - Dynamic team balancing algorithms
  - Team member roles (member, veteran, captain) with progression
- ✅ **Team Tournaments**: Seasonal wars and monthly battles
  - Configurable tournament types (seasonal_war, monthly_battle, special_event)
  - Automatic team score aggregation from individual games and challenges
  - Real-time leaderboards with detailed statistics
  - Prize and achievement system for tournament winners
- ✅ **Universal Scoring System**: Cross-game score normalization
  - Game type and difficulty-based score normalization
  - ELO rating system for competitive play
  - Time-based scoring adjustments
  - Team contribution calculations with weighted scoring
  - Streak bonuses and challenge multipliers

## Technology Stack
- **Framework**: Flask 3.1.2
- **Database**: MongoDB 
- **Authentication**: Flask-JWT-Extended 4.7.1
- **Password Hashing**: bcrypt 4.3.0
- **CORS**: Flask-CORS 6.0.1
- **Production Server**: Gunicorn 23.0.0
- **Config Management**: python-dotenv 1.1.1

## Database Schema & API Documentation

### Database Models
Database entities and schemas are defined in each module's `models/` directory:
- **Core models**: `app/core/models/` (User, Config, etc.)
- **Social models**: `app/social/models/` (UserRelationship, Achievement, etc.)
- **Games models**: `app/games/models/` (Game, GameSession, etc.)
- **Donations models**: `app/donations/models/` (Wallet, Transaction, etc.)
- **ONLUS models**: `app/onlus/models/` (ONLUS, Campaign, etc.)

### API Endpoints Documentation
API endpoints and their descriptions are documented in:
- **OpenAPI Specification**: `openapi.yaml` - Complete API documentation with schemas
- **Controller modules**: Each feature's `controllers/` directory contains route implementations
- **Postman Collection**: `GoodPlay_API.postman_collection.json` - API testing collection

#### Game Engine APIs (50+ endpoints)
- **Game Management**: `/api/games/*` - Core game and session management
- **Game Modes**: `/api/modes/*` - Temporary mode management and scheduling
- **Challenges**: `/api/challenges/*` - Direct challenges and matchmaking
- **Teams**: `/api/teams/*` - Global teams and tournament management

## Development Guidelines

### Adding New Endpoints (Modular Approach)
1. **Choose Module** - Determine which module the feature belongs to (core, games, social, donations, onlus, admin)
2. **Create Model** (if needed) in `app/{module}/models/`
3. **Create Repository** in `app/{module}/repositories/` extending `BaseRepository`
4. **Create Service** in `app/{module}/services/` with business logic
5. **Create Controller** in `app/{module}/controllers/` with route handlers
6. **Register Blueprint** in module's `__init__.py` and main `app/__init__.py`
7. **Update OpenAPI spec** in `openapi.yaml`


### Code Standards
- All user-facing messages should be constants in English. in the UI it will be translated properly
- Use type hints where possible
- Follow existing naming conventions
- Implement proper error handling with try/catch
- Use structured logging via `current_app.logger`
- Validate input data in services layer

### API Response Standards (🚨 CRITICAL FOR UI LOCALIZATION)
- **ALL API responses MUST use constant message keys**: Never return dynamic text messages
- **Message constants**: Use specific constant strings as documented in OpenAPI spec
- **UI Localization**: Frontend will localize these constant keys to user's language
- **OpenAPI Documentation**: All possible response constants are documented for each endpoint
- **Examples**:
  ```python
  # ❌ WRONG - Dynamic message
  return success_response("User John created successfully")

  # ✅ CORRECT - Constant string matching OpenAPI documentation
  return success_response("Registration completed successfully", {"user_id": user_id})
  ```

### Response Message Constants
All API response message constants are documented in:
- **OpenAPI specification**: `openapi.yaml` - Each endpoint lists all possible response messages
- **Endpoint-specific**: Constants are documented per endpoint with examples
- **UI Development**: Frontend developers can see exactly what messages each API call can return

### Security Best Practices
- Never log sensitive data (passwords, tokens)
- Validate all input data
- Use `@auth_required` decorator for protected routes
- Hash passwords with bcrypt
- Set proper CORS origins for production

### Testing Strategy & Requirements
- **🚨 MANDATORY**: After ANY code change (new features, bug fixes, refactoring), you MUST:
  1. **Create/Update Unit Tests**: Add tests for new functionality or update existing tests
  2. **Run Test Suite**: Execute `make test` or `python run_tests.py` to ensure all tests pass
  3. **Verify Coverage**: Ensure coverage remains above 80% (`make test-coverage`)
  4. **Update Test Documentation**: Update tests if API contracts change

#### Test Structure (FOLLOW THIS PATTERN):
- **Service Layer Tests**: Mock repository dependencies, test business logic
- **Controller Layer Tests**: Mock services, test API endpoints and error handling
- **Repository Layer Tests**: Mock database, test CRUD operations
- **Model Layer Tests**: Test validation, serialization, business methods
- **Integration Tests**: Test full request/response cycles
- **API Tests**: Test endpoint contracts match Postman collections

#### Test Execution Commands:
```bash
# Run all tests before committing
make test

# Test specific modules after changes
make test-module MODULE=auth        # After auth changes
make test-module MODULE=preferences # After preferences changes
make test-module MODULE=social     # After social changes
make test-module MODULE=games      # After games changes

# Verify coverage
make test-coverage

# Fast checks during development
make test-unit  # Skip coverage for speed
```

#### Test File Organization:
- `tests/test_core_auth.py` - Core authentication (47 tests)
- `tests/test_preferences.py` - Preferences module (35 tests)
- `tests/test_social.py` - Social features (28 tests)
- `tests/test_games.py` - Game engine (32 tests)
- `tests/conftest.py` - Shared fixtures and configuration

#### When to Create New Tests:
- **New Service Method**: Create corresponding test method
- **New API Endpoint**: Add controller test + update Postman collection
- **New Model Field**: Add model validation tests
- **New Repository Method**: Add repository test with mocked DB
- **Bug Fix**: Add regression test to prevent future occurrence
- **Performance Change**: Add benchmark test if significant

#### Test Quality Requirements:
- **Coverage**: Each new module must have 90%+ coverage
- **Assertions**: Test both success and failure scenarios
- **Mocking**: Mock external dependencies (DB, APIs, file system)
- **Fixtures**: Use shared fixtures from `conftest.py`
- **Naming**: Follow `test_<method>_<scenario>` pattern
- **Documentation**: Include docstrings explaining test purpose

## Environment Configuration

### Development (.env file)
```env
FLASK_ENV=development
SECRET_KEY=dev-secret
JWT_SECRET_KEY=jwt-dev-secret
MONGO_URI=mongodb://localhost:27017/goodplay_db
CORS_ORIGINS=http://localhost:3000
LOG_LEVEL=DEBUG
```

## Common Patterns

### Service Method Structure
```python
def service_method(self, params) -> Tuple[bool, str, Optional[Dict]]:
    # Validation
    validation_error = self._validate_data(params)
    if validation_error:
        return False, validation_error, None
    
    try:
        # Business logic
        result = self._do_business_logic(params)
        current_app.logger.info(f"Operation successful: {info}")
        return True, "Operation successful", result
    except Exception as e:
        current_app.logger.error(f"Operation failed: {str(e)}")
        return False, "Operation failed", None
```

### Controller Pattern
```python
@blueprint.route('/endpoint', methods=['POST'])
@auth_required
def endpoint(current_user):
    try:
        data = request.get_json()
        if not data:
            return error_response("Data required")
        
        success, message, result = service.method(data)
        
        if success:
            return success_response(message, result)
        else:
            return error_response(message)
    except Exception as e:
        current_app.logger.error(f"Endpoint error: {str(e)}")
        return error_response("Internal server error", status_code=500)
```

## Deployment

### Local Development
```bash
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your values
python app.py
```

### Heroku Production
```bash

# Deploy
git push heroku main
```

## Logging
- Development: Console output with DEBUG level
- Production: File + Console with configurable level
- Use structured logging for auth events, DB operations
- Never log sensitive information



### Technical Improvements
- API rate limiting
- Email verification system
- Password reset functionality
- Enhanced user roles and permissions system
- API versioning
- Database migrations
- Automated testing pipeline
- Monitoring and metrics
- Caching layer (Redis)
- WebSocket support for real-time features

## Notes for AI Assistant
- **🚨 CRITICAL**: NEVER commit changes without explicit user instruction. Always wait for user to say "commit" or "committa"
- **🚨 CRITICAL**: When adding/modifying/moving endpoints, ALWAYS update BOTH:
  - OpenAPI spec in `openapi.yaml`
  - Postman collection in `GoodPlay_API.postman_collection.json`
- **🚨 MANDATORY TESTING WORKFLOW**: After ANY code modification, you MUST:
  1. Create/update unit tests for the changed functionality
  2. Run `make test` to verify all tests pass
  3. Check coverage with `make test-coverage` (must be 80%+)
  4. For new features: add tests BEFORE implementing the feature (TDD approach preferred)
  5. For bug fixes: add regression test to prevent future occurrences
  6. Update test documentation if API contracts change
- Always follow the modular Repository → Service → Controller pattern within each module
- Respect module boundaries - core functionality should not depend on other modules
- Cross-module dependencies should flow towards core (e.g., games can use core auth, but core shouldn't use games)
- Maintain English language consistency
- Test authentication flows when making auth changes
- Consider database indexing for new queries
- Follow the development order: Core → Games → Social → Donations → ONLUS → Admin
- Update this file when making architectural changes