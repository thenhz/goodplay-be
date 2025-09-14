# Postman Testing Guide for GoodPlay API

## Files Created

1. **GoodPlay_API.postman_collection.json** - Complete API collection
2. **GoodPlay_Local.postman_environment.json** - Local development environment
3. **GoodPlay_Production.postman_environment.json** - Production environment

## How to Import

### Step 1: Import Collection
1. Open Postman
2. Click "Import" button
3. Select `GoodPlay_API.postman_collection.json`
4. Click "Import"

### Step 2: Import Environment
1. Click the gear icon (⚙️) in top right
2. Click "Import"
3. Select `GoodPlay_Local.postman_environment.json` (or Production)
4. Click "Import"
5. Select "GoodPlay Local" environment from dropdown

## Available Endpoints

### Health Check
- **GET** `/api/health` - Check API status

### Authentication Endpoints
- **POST** `/api/auth/register` - User registration
- **POST** `/api/auth/login` - User login
- **POST** `/api/auth/refresh` - Refresh access token
- **GET** `/api/auth/profile` - Get user profile (auth required)
- **PUT** `/api/auth/profile` - Update user profile (auth required)
- **POST** `/api/auth/logout` - User logout (auth required)

### Test Cases Included
- Register with missing data
- Register with invalid email
- Login with wrong credentials
- Access protected routes without token
- Access protected routes with invalid token

## Environment Variables

### Local Environment
- `base_url`: http://localhost:5000
- `test_email`: test@example.com
- `test_password`: password123
- `access_token`: (auto-populated after login)
- `refresh_token`: (auto-populated after login)

### Automatic Token Management
The collection includes scripts that automatically:
- Save access and refresh tokens after successful registration/login
- Use saved tokens for authenticated requests
- Update access token after refresh

## Testing Workflow

### 1. Start Your Server
```bash
python app.py
```

### 2. Test Sequence
1. **Health Check** - Verify API is running
2. **Register User** - Creates new user and saves tokens
3. **Login User** - Alternative login and saves tokens
4. **Get Profile** - Test authenticated endpoint
5. **Update Profile** - Test profile modification
6. **Refresh Token** - Test token refresh mechanism
7. **Logout** - Test logout endpoint

### 3. Error Testing
Test all the "Test Cases" folder requests to verify proper error handling.

## Expected Responses

### Successful Registration (201)
```json
{
    "success": true,
    "message": "User registered successfully",
    "data": {
        "user": {...},
        "tokens": {
            "access_token": "...",
            "refresh_token": "..."
        }
    }
}
```

### Successful Login (200)
```json
{
    "success": true,
    "message": "Login successful",
    "data": {
        "user": {...},
        "tokens": {
            "access_token": "...",
            "refresh_token": "..."
        }
    }
}
```

### Error Response (400/401/500)
```json
{
    "success": false,
    "message": "Error description"
}
```

## Tips

1. **First Time Setup**: Run "Register User" first to create a test account
2. **Token Expiry**: If you get 401 errors, run "Refresh Token" or "Login User"
3. **Environment Switching**: Change between Local/Production environments as needed
4. **Custom Test Data**: Modify environment variables to use different test emails/passwords

## Troubleshooting

- **500 Errors**: Check server logs and MongoDB connection
- **401 Unauthorized**: Token expired or invalid - try refreshing or logging in again
- **400 Bad Request**: Check request body format matches expected JSON structure
- **Connection Refused**: Ensure Flask server is running on correct port