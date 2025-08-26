# GoodPlay Backend - Development Guide for Claude

## Project Overview
This is a Flask-based REST API backend using MongoDB, JWT authentication, and following Repository Pattern + Service Layer architecture. All responses and logs are in English.

## Current Architecture

### Structure
```
app/
├── models/          # Data models (User)
├── repositories/    # Data access layer (MongoDB operations)  
├── services/        # Business logic layer
├── controllers/     # HTTP route handlers
└── utils/          # Decorators, responses, logging utilities
```

### Key Design Patterns
- **Repository Pattern**: Data access abstraction in `repositories/`
- **Service Layer**: Business logic in `services/` 
- **Dependency Injection**: Services use repositories
- **Decorator Pattern**: `@auth_required`, `@admin_required` for route protection

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

### Users Collection
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

## API Endpoints

### Authentication Routes (`/api/auth/`)
- `POST /register` - User registration
- `POST /login` - User login
- `POST /refresh` - Token refresh  
- `GET /profile` - Get user profile (auth required)
- `PUT /profile` - Update user profile (auth required)
- `POST /logout` - User logout (auth required)

### Health Check
- `GET /api/health` - API health status

## Development Guidelines

### Adding New Endpoints
1. **Create Model** (if needed) in `app/models/`
2. **Create Repository** in `app/repositories/` extending `BaseRepository`
3. **Create Service** in `app/services/` with business logic
4. **Create Controller** in `app/controllers/` with route handlers
5. **Register Blueprint** in `app/__init__.py`
6. **Update OpenAPI spec** in `openapi.yaml`

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
- API rate limiting
- Email verification system  
- Password reset functionality
- User roles and permissions system
- API versioning
- Database migrations
- Automated testing pipeline
- Monitoring and metrics

## Notes for AI Assistant
- Always follow the Repository → Service → Controller pattern
- Update OpenAPI spec when adding endpoints
- Maintain English language consistency
- Test authentication flows when making auth changes
- Consider database indexing for new queries
- Update this file when making architectural changes