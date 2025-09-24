# GoodPlay Backend 🎮❤️

**Gaming for Good - A platform where fun meets philanthropy**

GoodPlay is an open-source gaming platform where users play games to earn virtual credits that can be donated to verified charitable organizations (ONLUS). Our mission is to gamify charitable giving while creating an engaging gaming experience.

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)](https://github.com/yourorg/goodplay-be)
[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Discord](https://img.shields.io/badge/discord-join%20chat-7289da)](https://discord.gg/goodplay)

## 🚀 Quick Start

```bash
# Clone and setup
git clone https://github.com/yourorg/goodplay-be.git
cd goodplay-be

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your MongoDB URI

# Start development server
python app.py
```

**API Documentation**: http://localhost:5000/api/docs
**Health Check**: http://localhost:5000/api/health

## 🎯 Core Features

- 🎮 **Game Engine**: Pluggable game system with session management
- 🏆 **Social Gaming**: Achievements, leaderboards, and friend systems
- 💰 **Credit System**: Earn credits through gameplay
- ❤️ **Charitable Donations**: Convert credits to real charitable donations
- 🔐 **JWT Authentication**: Secure user authentication and authorization
- 📱 **Mobile-First**: RESTful API designed for mobile applications
- 🌍 **Internationalization**: Constant-based message system for UI localization

## 🏗️ Architecture

### Modular Design

```
app/
├── core/            # Authentication, users, health
├── games/           # Game engine and management
├── social/          # Achievements, leaderboards
├── donations/       # Wallet system, donations
├── onlus/          # Charitable organization management
├── preferences/     # User preferences system
└── admin/          # Administrative interface
```

### Technology Stack

- **Backend**: Flask 3.1.2, Python 3.9+
- **Database**: MongoDB with embedded documents
- **Authentication**: JWT with Flask-JWT-Extended
- **API Documentation**: OpenAPI 3.0.3 / Swagger
- **Testing**: pytest with coverage
- **Production**: Gunicorn WSGI server

## 🎮 Game Development

### Adding a New Game

1. **Create Game Model**
```python
# app/games/models/your_game.py
class YourGame:
    def __init__(self, name, category, credit_rate):
        self.name = name
        self.category = category
        self.credit_rate = credit_rate  # Credits per minute
```

2. **Implement Game Service**
```python
# app/games/services/your_game_service.py
def validate_move(self, session_id: str, move_data: dict) -> Tuple[bool, str, Optional[Dict]]:
    # Game logic here
    return True, "GAME_MOVE_VALID", result_data
```

3. **Add API Routes**
```python
# app/games/controllers/your_game_controller.py
@auth_required
def make_move(current_user):
    success, message, result = your_game_service.validate_move(...)
    return success_response(message, result) if success else error_response(message)
```

4. **Update Documentation**
   - Add endpoints to `docs/openapi/games.yaml`
   - Update `docs/postman/games_collection.json`
   - Add game to this README

### Game Categories

- 🧩 **Puzzle Games**: Word puzzles, logic games, brain teasers
- ⚡ **Action Games**: Quick reflexes, timing challenges
- 🎯 **Strategy Games**: Resource management, tactical games
- 🎨 **Creative Games**: Drawing, building, design challenges
- 📚 **Educational Games**: Learning-focused games

## 📡 API Documentation

### Documentation Structure

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

### API Access Points

- **Swagger UI**: `http://localhost:5000/api/docs`
- **OpenAPI Spec**: `docs/openapi.yaml`
- **Postman Collections**: `docs/postman/`

### API Modules Overview

#### Core Module (`/api/auth`, `/api/users`, `/api/preferences`)
- User registration and authentication
- Profile management
- User preferences and settings
- System health checks

#### Social Module (`/api/social`)
- Friend request management
- User relationships and blocking
- User discovery and search
- Social statistics

#### Games Module (`/api/games`, `/api/modes`, `/api/challenges`, `/api/teams`)
- Game management and plugin system
- Session lifecycle and cross-device sync
- Game modes and scheduling
- Direct challenges and tournaments
- Global teams and scoring

#### Leaderboards Module (`/api/social/impact-score`, `/api/social/leaderboards`)
- Social impact score calculation
- Multi-category leaderboard system
- Privacy controls and settings
- Ranking engine monitoring

### Response Format

All endpoints return consistent JSON responses:

```json
{
  "success": true,
  "message": "OPERATION_SUCCESS",
  "data": { ... },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Message Constants**: All API responses use constant message keys for UI localization.

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=app --cov-report=html

# Run specific test category
pytest tests/unit/
pytest tests/integration/
```

### Test Structure

- **Unit Tests**: Individual component testing
- **Integration Tests**: API endpoint testing
- **Game Tests**: Game-specific logic validation
- **Performance Tests**: Load testing for game sessions

## 🚀 Deployment

### Development
```bash
python app.py  # Development server with hot reload
```

### Production
```bash
gunicorn --bind 0.0.0.0:5000 --workers 4 "app:create_app()"
```

### Docker
```bash
docker build -t goodplay-backend .
docker run -p 5000:5000 goodplay-backend
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FLASK_ENV` | Environment mode | `development` |
| `MONGO_URI` | MongoDB connection string | `mongodb://localhost:27017/goodplay_db` |
| `JWT_SECRET_KEY` | JWT signing secret | Required in production |
| `CORS_ORIGINS` | Allowed CORS origins | `http://localhost:3000` |

## 🤝 Contributing

We welcome contributions from developers of all skill levels! Here are some ways to get involved:

### For Game Developers
- Create new games using our game engine
- Improve existing game mechanics
- Design game UI components
- Add achievements and social features

### For Backend Developers
- Add new API endpoints
- Improve performance and scalability
- Enhance security features
- Write comprehensive tests

### For Community Members
- Report bugs and suggest features
- Improve documentation
- Translate UI messages
- Help with user support

**Read our [Contributing Guide](CONTRIBUTING.md)** for detailed guidelines.

### Quick Contribution Steps

1. **Fork** the repository
2. **Create** feature branch: `git checkout -b feature/amazing-game`
3. **Commit** changes: `git commit -m 'Add amazing new game'`
4. **Push** branch: `git push origin feature/amazing-game`
5. **Create** Pull Request

## 📊 Project Status

### Current Version: 1.0.0-beta

### Completed Features ✅
- User authentication and authorization
- User preferences management system
- Core API infrastructure
- OpenAPI documentation
- JWT token system
- MongoDB integration
- CORS configuration
- Structured logging

### In Development 🚧
- Game engine framework
- Social features (achievements, leaderboards)
- Wallet and donation system
- ONLUS management system
- Administrative interface

### Planned Features 🎯
- Multiple game integrations
- Real-time multiplayer support
- Push notifications
- Advanced analytics
- Mobile app SDK
- Charity impact tracking

## 🎮 Featured Games

*Games will be listed here as they are developed by the community*

### Coming Soon
- **Word Puzzle Challenge** - Earn credits by solving word puzzles
- **Math Master** - Quick arithmetic challenges
- **Memory Matrix** - Pattern matching and memory games
- **Strategy Builder** - Resource management simulation

## 📈 Stats

- **Games Available**: 0 (launching soon!)
- **Registered Users**: Ready for launch
- **Credits Donated**: Ready to make an impact
- **ONLUS Partners**: Actively recruiting

## 🏆 Contributors

Thanks to all our contributors! 🎉

<!-- Contributors will be automatically added here -->

### Game Developers
*Your name could be here! Create a game and join our community.*

### Core Contributors
*Contributors to the platform infrastructure and API.*

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Documentation
- **API Docs**: [Swagger UI](http://localhost:5000/api/docs)
- **OpenAPI Specification**: [docs/openapi.yaml](docs/openapi.yaml)
- **Postman Collections**: [docs/postman/](docs/postman/)
- **API Organization Guide**: [docs/API_ORGANIZATION.md](docs/API_ORGANIZATION.md)
- **Contributing Guide**: [CONTRIBUTING.md](CONTRIBUTING.md)
- **Architecture Guide**: [CLAUDE.md](CLAUDE.md)

### Community
- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and ideas
- **Discord**: Real-time community chat
- **Email**: hello@goodplay.org

### Getting Help

1. Check the [API documentation](http://localhost:5000/api/docs)
2. Search [existing issues](https://github.com/yourorg/goodplay-be/issues)
3. Ask in [GitHub Discussions](https://github.com/yourorg/goodplay-be/discussions)
4. Join our [Discord community](https://discord.gg/goodplay)

## 🌟 Star History

If you find GoodPlay useful, please consider starring the repository! ⭐

[![Star History Chart](https://api.star-history.com/svg?repos=yourorg/goodplay-be&type=Date)](https://star-history.com/#yourorg/goodplay-be&Date)

---

## 🎯 Mission Statement

*"At GoodPlay, we believe that gaming can be a force for good in the world. By combining the joy of gaming with the satisfaction of charitable giving, we're creating a platform where every minute spent playing contributes to meaningful social impact."*

**Join us in gaming for good!** 🎮❤️

---

*Ready to contribute? Check out our [Contributing Guide](CONTRIBUTING.md) and start building amazing games for social good!*