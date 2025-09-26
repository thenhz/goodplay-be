# Postman Testing Guide for GoodPlay API

## Files Structure

All Postman files are organized in `docs/postman/`:

### Collections (Modular Architecture)
1. **docs/postman/core_collection.json** - Core API (health, auth, user management, preferences) - **18 requests**
2. **docs/postman/games_collection.json** - Game Engine APIs (sessions, modes, challenges, teams) - **45+ requests**
3. **docs/postman/social_collection.json** - Social Features (friends, relationships, search) - **15 requests**
4. **docs/postman/leaderboards_collection.json** - Leaderboards & Impact Scores - **15 requests**
5. **docs/postman/social_challenges_collection.json** - Social Challenges & Interactions - **30+ requests**

### Environments
1. **docs/postman/GoodPlay_Local.postman_environment.json** - Local development
2. **docs/postman/GoodPlay_Production.postman_environment.json** - Production

**Total: 125+ endpoints across 5 modular collections**

## How to Import

### Step 1: Import Environment (Required First)
1. Open Postman
2. Click the gear icon (⚙️) in top right
3. Click "Import"
4. Select `docs/postman/GoodPlay_Local.postman_environment.json` (or Production)
5. Click "Import"
6. Select "GoodPlay Local" environment from dropdown

### Step 2: Import Collections (Choose what you need)
1. Click "Import" button in main workspace
2. **For Core API testing**: Import `docs/postman/core_collection.json`
3. **For Game Engine testing**: Import `docs/postman/games_collection.json`
4. **For Social Features**: Import `docs/postman/social_collection.json`
5. **For Leaderboards**: Import `docs/postman/leaderboards_collection.json`
6. **For Social Challenges**: Import `docs/postman/social_challenges_collection.json`

## Collection Details

### 🔐 Core Collection (`core_collection.json`)
**Purpose**: Essential API functionality and user management

**Endpoints Include:**
- **Health Check**: `/api/health`
- **Authentication**: Register, login, logout, refresh token
- **User Management**: Profile CRUD, gaming stats, wallet operations
- **Preferences**: Get/update preferences by category, reset to defaults
- **Error Test Cases**: Invalid inputs, unauthorized access

**Testing Workflow:**
1. **Health Check** → **Register User** → **Login** → **Get Profile** → **Update Preferences**

---

### 🎮 Games Collection (`games_collection.json`)
**Purpose**: Complete game engine and session management

**Endpoints Include:**
- **Game Management**: CRUD, categories, search, install, rating
- **Session Management**: Create, pause, resume, end, state updates
- **Cross-Device Sync**: State synchronization, conflict resolution
- **Game Modes**: Current modes, admin activation/deactivation, scheduling
- **Direct Challenges**: 1v1/NvN challenges, join/accept/decline
- **Matchmaking**: Find opponents, quick match, recommendations
- **Team Management**: Join teams, leaderboards, contribution tracking

**Testing Workflow:**
1. **Get Games** → **Create Session** → **Update State** → **Sync Across Devices** → **End Session**

---

### 👥 Social Collection (`social_collection.json`)
**Purpose**: Friend relationships and social networking

**Endpoints Include:**
- **Friend Management**: Send requests, accept/decline, remove friends
- **User Blocking**: Block/unblock users, view blocked list
- **Social Discovery**: Search users, friend suggestions
- **Relationship Status**: Check friendship status
- **Social Statistics**: User social stats and activity

**Testing Workflow:**
1. **Search Users** → **Send Friend Request** → **Accept Request** → **Get Friends List**

---

### 🏆 Leaderboards Collection (`leaderboards_collection.json`)
**Purpose**: Impact scoring and competitive rankings

**Endpoints Include:**
- **Impact Score Management**: Personal scores, history, refresh
- **Leaderboards**: Global, friends, team rankings with statistics
- **Privacy Settings**: Control leaderboard participation visibility
- **Rankings System**: Health checks, manual updates
- **Admin Operations**: Recalculate scores, refresh leaderboards

**Testing Workflow:**
1. **Get My Impact Score** → **View Leaderboards** → **Check Friends Rankings** → **Update Privacy Settings**

---

### 💬 Social Challenges Collection (`social_challenges_collection.json`)
**Purpose**: Community challenges and social interactions

**Endpoints Include:**
- **Challenge Management**: Create gaming/social/impact challenges, view details
- **Challenge Discovery**: Public challenges, friend challenges, trending, search
- **Participation**: Join/leave challenges, update progress, view leaderboards
- **Social Interactions**: Cheers, comments, likes, replies, activity feeds
- **Templates**: Pre-built challenge templates with customization
- **Invitations**: Invite friends to participate
- **Admin Operations**: Cleanup expired challenges

**Testing Workflow:**
1. **Create Challenge** → **Invite Friends** → **Join Challenge** → **Update Progress** → **Add Comments/Cheers**

## Environment Variables

### Core Variables (Required)
- `{{baseUrl}}` - API base URL (http://localhost:5000 for local)
- `{{access_token}}` - JWT access token (auto-populated after login)
- `{{refresh_token}}` - JWT refresh token (auto-populated after login)
- `{{test_email}}` - Test user email
- `{{test_password}}` - Test user password
- `{{user_id}}` - Current user ID (auto-populated)

### Feature-Specific Variables (Auto-populated)
- `{{game_id}}` - Current game ID
- `{{session_id}}` - Current session ID
- `{{challenge_id}}` - Current challenge ID
- `{{team_id}}` - Current team ID
- `{{friend_user_id}}` - Friend user ID
- `{{relationship_id}}` - Relationship ID
- `{{interaction_id}}` - Interaction ID
- `{{leaderboard_type}}` - Leaderboard type
- `{{template_type}}` - Template type

## Automatic Token Management

The collections include scripts that automatically:
- **Save tokens**: Access and refresh tokens after successful registration/login
- **Auto-authenticate**: Use saved tokens for authenticated requests
- **Update tokens**: Refresh access token when needed
- **Populate IDs**: Auto-save entity IDs from responses (game_id, session_id, etc.)

## Testing Workflows

### 🚀 Quick Start (Recommended)
1. **Import Environment** → **Import Core Collection**
2. **Run**: Health Check → Register User → Login User
3. **Verify**: Get Profile → Update Preferences
4. **Import additional collections** as needed for specific features

### 🔄 Full API Testing
1. **Core**: Authentication flow → User management → Preferences
2. **Games**: Game discovery → Session management → Cross-device sync
3. **Social**: Friend management → User search → Social stats
4. **Leaderboards**: Impact scores → Rankings → Privacy settings
5. **Social Challenges**: Create challenges → Participate → Social interactions

### 🎯 Feature-Specific Testing

**Game Engine Testing:**
```
games_collection.json → Get Games → Create Session → Pause/Resume → End Session
```

**Social Features Testing:**
```
social_collection.json → Search Users → Friend Requests → Social Stats
```

**Challenge System Testing:**
```
social_challenges_collection.json → Create Challenge → Join → Progress → Interactions
```

## Advanced Features

### 🔄 Cross-Collection Workflows
Variables are shared across collections, enabling complex workflows:

1. **User Registration** (Core) → **Join Team** (Games) → **Create Challenge** (Social Challenges)
2. **Game Session** (Games) → **Record Contribution** (Games) → **Check Leaderboard** (Leaderboards)

### 📊 Testing Strategies

**Development Testing:**
- Use Core + one feature collection
- Focus on authentication and basic CRUD operations

**Integration Testing:**
- Import all collections
- Test cross-feature workflows
- Verify data consistency across modules

**Performance Testing:**
- Use batch operations where available
- Test pagination limits
- Monitor response times

## Error Handling

Each collection includes error test cases:
- **Invalid Authentication**: Missing/expired tokens
- **Bad Requests**: Invalid data, missing fields
- **Authorization Errors**: Insufficient permissions
- **Resource Not Found**: Non-existent IDs

## Expected Response Format

All API responses follow this structure:
```json
{
    "success": boolean,
    "message": "CONSTANT_KEY",
    "data": {} // optional
}
```

### Successful Responses
```json
{
    "success": true,
    "message": "USER_LOGIN_SUCCESS",
    "data": {
        "user": {...},
        "tokens": {...}
    }
}
```

### Error Responses
```json
{
    "success": false,
    "message": "INVALID_CREDENTIALS"
}
```

## Tips & Best Practices

### 🎯 Efficient Testing
1. **Start with Core**: Always test authentication first
2. **Use Environment Switching**: Switch between Local/Production as needed
3. **Leverage Auto-Population**: Let scripts save IDs automatically
4. **Batch Import**: Import multiple collections at once for comprehensive testing

### 🔧 Troubleshooting

**500 Errors:**
- Check server logs and MongoDB connection
- Verify API server is running

**401 Unauthorized:**
- Token expired → Run "Refresh Token" or "Login User"
- Missing token → Ensure environment is selected

**400 Bad Request:**
- Check request body format matches expected JSON structure
- Verify required fields are present

**Connection Refused:**
- Ensure Flask server is running on correct port (5000 for local)
- Check baseUrl in environment matches server

### 🔄 Maintenance

**Regular Updates:**
- Keep collections synchronized with OpenAPI specs
- Update environment variables for new features
- Test collections after API changes

**Version Control:**
- Collections are stored in git repository
- Environment files include version timestamps
- UUID-based collection IDs prevent conflicts

## API Coverage

| Module | Endpoints | Collection | Status |
|--------|-----------|------------|--------|
| Core | 18 | core_collection.json | ✅ Complete |
| Games | 45+ | games_collection.json | ✅ Complete |
| Social | 15 | social_collection.json | ✅ Complete |
| Leaderboards | 15 | leaderboards_collection.json | ✅ Complete |
| Social Challenges | 30+ | social_challenges_collection.json | ✅ Complete |

**Total API Coverage: 125+ endpoints across all major features**

---

*Generated with Claude Code - Last updated: September 26, 2024*