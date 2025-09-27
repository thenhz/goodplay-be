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

### Virtual Wallet & Credit System Features (GOO-14)
- ✅ **Virtual Wallet Management**: Complete wallet system with balance tracking
  - Individual user wallets with current balance, total earned, and total donated
  - Optimistic locking for concurrent transaction safety
  - Auto-donation settings with configurable thresholds and percentages
  - Comprehensive wallet statistics and analytics
- ✅ **Credit Conversion Engine**: Time-based credit calculation with multipliers
  - Base rate: €0.01 per minute of gameplay
  - Dynamic multipliers: Tournament (2.0x), Challenge (1.5x), Daily Streak (1.2x), Weekend (1.1x), Special Events (3.0x)
  - Precise time tracking integration with GOO-9 session management (play_duration_ms)
  - Fraud detection with anomaly detection for suspicious patterns
- ✅ **Transaction Processing**: Complete audit trail with batch operations
  - Transaction types: earned, donated, bonus, refund, adjustment, fee
  - Transaction statuses: pending, completed, failed, cancelled, refunded
  - Batch transaction processing for performance optimization
  - Receipt generation for donations with tax deductibility information
- ✅ **Auto-Donation System**: Automated donation processing
  - Configurable auto-donation thresholds and percentages
  - Round-up donation options for micro-donations
  - Preferred ONLUS selection for automated donations
  - Smart donation triggers based on balance thresholds
- ✅ **Fraud Prevention & Security**: Multi-layer security system
  - Rate limiting on credit conversion (max €1000/day per user)
  - Anomaly detection for unusual earning patterns
  - Session validation for legitimate gameplay
  - Transaction integrity validation with cryptographic signatures
  - Suspicious activity flagging and automated alerts
- ✅ **Enhanced API Endpoints** (15+ new endpoints):
  - `GET /api/wallet` - Get user wallet information
  - `GET /api/wallet/transactions` - Transaction history with pagination
  - `GET /api/wallet/statistics` - Comprehensive wallet analytics
  - `POST /api/wallet/convert-session` - Convert game session to credits
  - `PUT /api/wallet/auto-donation` - Configure auto-donation settings
  - `POST /api/donations/create` - Process donation to ONLUS
  - `GET /api/donations/history` - User donation history
  - `GET /api/donations/{id}/receipt` - Get donation receipt
  - `GET /api/conversion-rates` - Current rates and multipliers
  - `GET /api/conversion-rates/calculator` - Estimate credits for duration

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

### API Documentation & Testing

#### OpenAPI Specification (`docs/openapi/`)
- **Main file**: `docs/openapi.yaml` - Complete API documentation with schemas and examples
- **Module files**:
  - `docs/openapi/core.yaml` - Authentication, user management, preferences
  - `docs/openapi/games.yaml` - Game engine, sessions, challenges, teams
  - `docs/openapi/social.yaml` - Social features, achievements, leaderboards
  - `docs/openapi/donations.yaml` - Virtual wallet, credits, donations, conversion rates
- **Usage**:
  - Import into Swagger UI for interactive documentation
  - Use for frontend API client generation
  - Reference for all endpoint contracts and response constants
  - All possible response message constants are documented per endpoint

#### Postman Collections (`docs/postman/`)
- **Core Collection**: `docs/postman/core_collection.json` - Auth, users, preferences
- **Games Collection**: `docs/postman/games_collection.json` - Game engine APIs
- **Social Collection**: `docs/postman/social_collection.json` - Social features
- **Environment Files**:
  - `docs/postman/GoodPlay_Local.postman_environment.json` - Local development
  - `docs/postman/GoodPlay_Production.postman_environment.json` - Production
- **Usage**:
  1. Import collections and environment into Postman
  2. Set environment variables (`baseUrl`, `access_token`, etc.)
  3. Use for manual API testing and development
  4. Run collection tests for API validation
  5. Export new requests when adding endpoints

#### Platform APIs (70+ endpoints)
- **Game Management**: `/api/games/*` - Core game and session management
- **Game Modes**: `/api/modes/*` - Temporary mode management and scheduling
- **Challenges**: `/api/challenges/*` - Direct challenges and matchmaking
- **Teams**: `/api/teams/*` - Global teams and tournament management
- **Wallet Management**: `/api/wallet/*` - Virtual wallet and credit operations
- **Donations**: `/api/donations/*` - Donation processing and receipts
- **Conversion Rates**: `/api/conversion-rates/*` - Credit rates and calculators

## Development Guidelines

### Adding New Endpoints (Modular Approach)
1. **Choose Module** - Determine which module the feature belongs to (core, games, social, donations, onlus, admin)
2. **Create Model** (if needed) in `app/{module}/models/`
3. **Create Repository** in `app/{module}/repositories/` extending `BaseRepository`
4. **Create Service** in `app/{module}/services/` with business logic
5. **Create Controller** in `app/{module}/controllers/` with route handlers
6. **Register Blueprint** in module's `__init__.py` and main `app/__init__.py`
7. **Update Documentation**:
   - Add endpoint to appropriate `docs/openapi/{module}.yaml` file
   - Add request to appropriate `docs/postman/{module}_collection.json`
   - Include all possible response constants in OpenAPI examples
8. **Test Implementation**:
   - Write unit tests for new service methods
   - Test endpoints using Postman collection
   - Verify OpenAPI documentation matches implementation


### Code Standards
- All user-facing messages should be constants in English. in the UI it will be translated properly
- Use type hints where possible
- Follow existing naming conventions
- Implement proper error handling with try/catch
- Use structured logging via `current_app.logger`
- Validate input data in services layer

### API Response Standards (🚨 CRITICAL FOR UI LOCALIZATION)

#### Mandatory Constant Message Usage
- **🚨 ALL API responses MUST use constant message keys**: Never return dynamic text messages
- **No Dynamic Content**: Messages must be static constants defined in OpenAPI specification
- **UI Localization**: Frontend will translate these constant keys to user's preferred language
- **Consistency**: Same constant must be used across all similar operations

#### Message Constant Examples
```python
# ❌ WRONG - Dynamic/custom messages
return success_response("User John created successfully")
return error_response("Password must be longer")
return success_response("Profile updated successfully")

# ✅ CORRECT - Constants from OpenAPI spec
return success_response("USER_REGISTRATION_SUCCESS", {"user_id": user_id})
return error_response("PASSWORD_TOO_WEAK")
return success_response("PROFILE_UPDATED_SUCCESS", user_data)
```

#### Available Constant Categories
- **Authentication**: `USER_LOGIN_SUCCESS`, `INVALID_CREDENTIALS`, `TOKEN_EXPIRED`, etc.
- **Profile Management**: `PROFILE_RETRIEVED_SUCCESS`, `PROFILE_UPDATED_SUCCESS`, etc.
- **Password Management**: `PASSWORD_CHANGED_SUCCESS`, `CURRENT_PASSWORD_INCORRECT`, etc.
- **System Errors**: `DATA_REQUIRED`, `INTERNAL_SERVER_ERROR`, `VALIDATION_ERROR`, etc.
- **Account Management**: `ACCOUNT_DELETED_SUCCESS`, `ACCOUNT_DISABLED`, etc.

### Response Message Constants
All API response message constants are documented in:
- **OpenAPI specification**: `docs/openapi/core.yaml` - Complete list in `core_constants` section
- **Endpoint-specific**: Each endpoint documents all possible response messages with examples
- **UI Development**: Frontend developers can see exactly what messages each API call can return

## API Documentation Usage Guide

### Using OpenAPI Specification
1. **For Frontend Development**:
   ```bash
   # Generate TypeScript client from OpenAPI spec
   npx @openapitools/openapi-generator-cli generate \
     -i docs/openapi.yaml \
     -g typescript-axios \
     -o frontend/src/api
   ```

2. **For Documentation**:
   - Import `docs/openapi.yaml` into Swagger UI
   - Use Redoc for API documentation websites
   - Reference for all endpoint contracts and response constants

3. **For Testing**:
   - Validate API responses match documented schemas
   - Ensure all response constants are documented
   - Check endpoint parameters and request bodies

### Using Postman Collections
1. **Setup Environment**:
   - Import environment file for your target (Local/Production)
   - Set required variables: `baseUrl`, `test_email`, `test_password`
   - After login, set `access_token` and `refresh_token`

2. **Testing Workflow**:
   ```
   1. Health Check → Verify API is running
   2. Register User → Create test account
   3. Login User → Get authentication tokens
   4. Test Protected Endpoints → Use with Bearer token
   5. Run Collection → Automated testing
   ```

3. **Adding New Endpoints**:
   - Create request in appropriate collection (core/games/social)
   - Use environment variables for dynamic values
   - Add tests for response validation
   - Export and commit updated collection

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

#### Test Configuration & Database Mocking (🚨 CRITICAL SETUP):
- **Environment Variables**: Always set `TESTING=true` in `conftest.py` BEFORE importing app modules
- **Database Index Creation**: All repository `create_indexes()` methods MUST check for testing mode:
  ```python
  def create_indexes(self):
      import os
      if self.collection is None or os.getenv('TESTING') == 'true':
          return
  ```
- **BaseRepository Abstract Methods**: ALL repositories extending `BaseRepository` MUST implement `create_indexes()` method
- **MongoDB Connection Mocking**: Mock `get_db()` and collection operations in `conftest.py` to prevent DB connection attempts during testing
- **Flask Application Context**: Use `with app.app_context():` for tests that access `current_app.logger` or other Flask globals

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
- **🚨 CRITICAL**: ALL API responses MUST use constant message keys (never dynamic text):
  - Use constants from `docs/openapi/core.yaml` core_constants section
  - Examples: `USER_LOGIN_SUCCESS`, `INVALID_CREDENTIALS`, `DATA_REQUIRED`
  - NEVER use dynamic messages like "User John created successfully"
- **🚨 CRITICAL**: When adding/modifying/moving endpoints, ALWAYS update ALL documentation:
  - OpenAPI spec in appropriate `docs/openapi/{module}.yaml` file
  - Postman collection in appropriate `docs/postman/{module}_collection.json`
  - Include all possible response constants in OpenAPI examples
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