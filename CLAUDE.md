# GoodPlay Backend - Development Guide for Claude

## Project Overview
This is a Flask-based REST API backend using MongoDB, JWT authentication, and following Repository Pattern + Service Layer architecture. All responses and logs are in English.

## Current Architecture

### Structure (Modular Architecture)
```
app/
├── core/            # Core platform functionality
│   ├── models/      # Core data models (User, Config)
│   ├── repositories/ # Core data access layer
│   ├── services/    # Core business logic
│   └── controllers/ # Core route handlers (auth, health)
├── preferences/     # User preferences and settings
├── social/          # Social features and gamification
│   ├── models/      # Achievement, Leaderboard models
│   ├── repositories/ # Social data access
│   ├── services/    # Social business logic
│   └── controllers/ # Social route handlers
├── games/           # Game engine and management
│   ├── models/      # Game, Session models
│   ├── repositories/ # Game data access
│   ├── services/    # Game business logic
│   └── controllers/ # Game route handlers
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

### Migration from Monolithic to Modular
The application has been restructured from a monolithic architecture to a modular one:
- **Previous**: Single `models/`, `repositories/`, `services/`, `controllers/` directories
- **Current**: Feature-based modules with their own MVC structure
- **Benefits**: Better separation of concerns, easier maintenance, scalable development

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
- ✅ CORS configuration
- ✅ Structured logging
- ✅ Environment-based configuration
- ✅ Gunicorn production setup

## Technology Stack
- **Framework**: Flask 3.1.2
- **Database**: MongoDB 
- **Authentication**: Flask-JWT-Extended 4.7.1
- **Password Hashing**: bcrypt 4.3.0
- **CORS**: Flask-CORS 6.0.1
- **Production Server**: Gunicorn 23.0.0
- **Config Management**: python-dotenv 1.1.1

## Database Schema

### Core Collections

#### Users Collection (app/core/models/)
```javascript
{
  _id: ObjectId,
  email: String (unique, lowercase),
  first_name: String (optional),
  last_name: String (optional),
  password_hash: String,
  is_active: Boolean (default: true),
  role: String (default: 'user'),
  created_at: DateTime,
  updated_at: DateTime
}
```

### Planned Collections (Future Implementation)

#### Games Collection (app/games/models/)
```javascript
{
  _id: ObjectId,
  name: String,
  description: String,
  category: String,
  version: String,
  is_active: Boolean,
  credit_rate: Number, // Credits per minute
  created_at: DateTime
}
```

#### Wallets Collection (app/donations/models/)
```javascript
{
  _id: ObjectId,
  user_id: ObjectId,
  balance: Number,
  total_earned: Number,
  total_donated: Number,
  updated_at: DateTime
}
```

#### ONLUS Collection (app/onlus/models/)
```javascript
{
  _id: ObjectId,
  name: String,
  description: String,
  verification_status: String, // pending, verified, rejected
  created_at: DateTime
}
```

## API Endpoints

### Current Endpoints

#### Core Routes (`/api/core/`)
- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `POST /auth/refresh` - Token refresh
- `GET /auth/profile` - Get user profile (auth required)
- `PUT /auth/profile` - Update user profile (auth required)
- `POST /auth/logout` - User logout (auth required)
- `GET /health` - API health status

### Planned Endpoints (Future Implementation)

#### Games Routes (`/api/games/`)
- `GET /` - List available games
- `GET /{game_id}` - Get game details
- `POST /{game_id}/sessions` - Start game session
- `PUT /sessions/{session_id}` - Update session progress

#### Social Routes (`/api/social/`)
- `GET /leaderboards` - Get leaderboards
- `GET /achievements` - Get user achievements
- `GET /friends` - Get user's friends list

#### Donations Routes (`/api/donations/`)
- `GET /wallet` - Get user wallet balance
- `POST /donate` - Make donation to ONLUS
- `GET /transactions` - Get donation history

#### ONLUS Routes (`/api/onlus/`)
- `GET /` - List verified ONLUS organizations
- `GET /{onlus_id}` - Get ONLUS details
- `POST /` - Register new ONLUS (admin)

## Development Guidelines

### Adding New Endpoints (Modular Approach)
1. **Choose Module** - Determine which module the feature belongs to (core, games, social, donations, onlus, admin)
2. **Create Model** (if needed) in `app/{module}/models/`
3. **Create Repository** in `app/{module}/repositories/` extending `BaseRepository`
4. **Create Service** in `app/{module}/services/` with business logic
5. **Create Controller** in `app/{module}/controllers/` with route handlers
6. **Register Blueprint** in module's `__init__.py` and main `app/__init__.py`
7. **Update OpenAPI spec** in `openapi.yaml`

### Module Development Order
1. **Core** - Foundation (auth, users, health) ✅ Completed
2. **Games** - Game engine and session management
3. **Social** - Achievements, leaderboards, social features
4. **Donations** - Wallet system and donation processing
5. **ONLUS** - Organization management and verification
6. **Admin** - Administrative interface and controls

### Code Standards
- All user-facing messages in English
- Use type hints where possible
- Follow existing naming conventions
- Implement proper error handling with try/catch
- Use structured logging via `current_app.logger`
- Validate input data in services layer

### Security Best Practices
- Never log sensitive data (passwords, tokens)
- Validate all input data
- Use `@auth_required` decorator for protected routes
- Hash passwords with bcrypt
- Set proper CORS origins for production

### Testing Strategy
- Unit tests for services layer
- Integration tests for API endpoints
- Mock MongoDB operations in tests
- Test authentication flows

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

## Future Enhancements

### Platform Features
- Plugin-based game installation system
- Real-time session synchronization across devices
- Advanced social features (chat, tournaments)
- Impact score calculation and community rankings
- Multi-language support (currently English-only)
- Push notifications for achievements and donations

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
- Always follow the modular Repository → Service → Controller pattern within each module
- Respect module boundaries - core functionality should not depend on other modules
- Cross-module dependencies should flow towards core (e.g., games can use core auth, but core shouldn't use games)
- Update OpenAPI spec when adding endpoints
- Maintain English language consistency
- Test authentication flows when making auth changes
- Consider database indexing for new queries
- Follow the development order: Core → Games → Social → Donations → ONLUS → Admin
- Update this file when making architectural changes