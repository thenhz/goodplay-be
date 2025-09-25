"""
Fluent Test Data Builders for GoodPlay Testing (GOO-35)

Provides fluent, chainable builders for creating test data with sensible defaults
and easy customization to reduce boilerplate and improve test readability.
"""
import uuid
from typing import Dict, Any, List, Optional, Union
from bson import ObjectId
from datetime import datetime, timezone
from copy import deepcopy


class BaseBuilder:
    """Base class for all fluent builders"""

    def __init__(self):
        self._data = {}

    def build(self) -> Dict[str, Any]:
        """Build and return the final data structure"""
        return deepcopy(self._data)

    def with_id(self, obj_id: Union[str, ObjectId] = None) -> 'BaseBuilder':
        """Set the _id field"""
        self._data['_id'] = ObjectId(obj_id) if isinstance(obj_id, str) else (obj_id or ObjectId())
        return self

    def with_timestamps(self, created_at: datetime = None, updated_at: datetime = None) -> 'BaseBuilder':
        """Add created_at and updated_at timestamps"""
        now = datetime.now(timezone.utc)
        self._data['created_at'] = created_at or now
        self._data['updated_at'] = updated_at or now
        return self

    def with_field(self, field_name: str, value: Any) -> 'BaseBuilder':
        """Set any custom field"""
        self._data[field_name] = value
        return self

    def merge(self, data: Dict[str, Any]) -> 'BaseBuilder':
        """Merge additional data into the builder"""
        self._data.update(data)
        return self


class UserBuilder(BaseBuilder):
    """Fluent builder for user test data"""

    def __init__(self):
        super().__init__()
        # Set sensible defaults
        self._data.update({
            'email': f'user_{uuid.uuid4().hex[:8]}@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'active': True,
            'preferences': {
                'gaming': {'difficulty': 'medium'},
                'notifications': {'email_enabled': True},
                'privacy': {'profile_public': False},
                'donations': {'auto_donate': False}
            }
        })

    def with_email(self, email: str) -> 'UserBuilder':
        """Set user email"""
        self._data['email'] = email
        return self

    def with_name(self, first_name: str, last_name: str) -> 'UserBuilder':
        """Set user name"""
        self._data['first_name'] = first_name
        self._data['last_name'] = last_name
        return self

    def with_role(self, role: str) -> 'UserBuilder':
        """Set user role"""
        self._data['role'] = role
        return self

    def as_admin(self) -> 'UserBuilder':
        """Configure as admin user"""
        self._data.update({
            'role': 'admin',
            'permissions': ['read', 'write', 'admin'],
            'first_name': 'Admin',
            'last_name': 'User'
        })
        return self

    def as_guest(self) -> 'UserBuilder':
        """Configure as guest user"""
        self._data.update({
            'role': 'guest',
            'permissions': ['read'],
            'first_name': 'Guest',
            'last_name': 'User'
        })
        return self

    def as_premium(self) -> 'UserBuilder':
        """Configure as premium user"""
        self._data.update({
            'role': 'premium',
            'subscription': {
                'type': 'premium',
                'expires_at': datetime.now(timezone.utc).replace(year=2025)
            },
            'preferences': {
                **self._data.get('preferences', {}),
                'gaming': {'difficulty': 'hard', 'premium_features': True}
            }
        })
        return self

    def inactive(self) -> 'UserBuilder':
        """Set user as inactive"""
        self._data['active'] = False
        return self

    def with_preferences(self, preferences: Dict[str, Any]) -> 'UserBuilder':
        """Set user preferences"""
        self._data['preferences'] = preferences
        return self

    def with_gaming_preference(self, difficulty: str = 'medium', **kwargs) -> 'UserBuilder':
        """Set gaming preferences"""
        if 'preferences' not in self._data:
            self._data['preferences'] = {}
        self._data['preferences']['gaming'] = {'difficulty': difficulty, **kwargs}
        return self

    def with_notification_preference(self, email_enabled: bool = True, **kwargs) -> 'UserBuilder':
        """Set notification preferences"""
        if 'preferences' not in self._data:
            self._data['preferences'] = {}
        self._data['preferences']['notifications'] = {'email_enabled': email_enabled, **kwargs}
        return self


class GameBuilder(BaseBuilder):
    """Fluent builder for game test data"""

    def __init__(self):
        super().__init__()
        # Set sensible defaults
        self._data.update({
            'title': f'Test Game {uuid.uuid4().hex[:6]}',
            'description': 'A test game for unit testing',
            'category': 'puzzle',
            'difficulty': 'medium',
            'credits_required': 10,
            'active': True,
            'settings': {
                'max_players': 1,
                'time_limit': None,
                'scoring_type': 'points'
            }
        })

    def with_title(self, title: str) -> 'GameBuilder':
        """Set game title"""
        self._data['title'] = title
        return self

    def with_description(self, description: str) -> 'GameBuilder':
        """Set game description"""
        self._data['description'] = description
        return self

    def with_category(self, category: str) -> 'GameBuilder':
        """Set game category"""
        valid_categories = ['puzzle', 'action', 'strategy', 'casual', 'arcade']
        if category not in valid_categories:
            raise ValueError(f"Invalid category. Must be one of: {valid_categories}")
        self._data['category'] = category
        return self

    def with_difficulty(self, difficulty: str) -> 'GameBuilder':
        """Set game difficulty"""
        valid_difficulties = ['easy', 'medium', 'hard', 'expert']
        if difficulty not in valid_difficulties:
            raise ValueError(f"Invalid difficulty. Must be one of: {valid_difficulties}")
        self._data['difficulty'] = difficulty
        return self

    def with_credits(self, credits: int) -> 'GameBuilder':
        """Set required credits"""
        self._data['credits_required'] = credits
        return self

    def as_puzzle(self) -> 'GameBuilder':
        """Configure as puzzle game"""
        self._data.update({
            'category': 'puzzle',
            'difficulty': 'medium',
            'settings': {
                **self._data.get('settings', {}),
                'scoring_type': 'time_bonus',
                'hints_available': True
            }
        })
        return self

    def as_action(self) -> 'GameBuilder':
        """Configure as action game"""
        self._data.update({
            'category': 'action',
            'difficulty': 'hard',
            'settings': {
                **self._data.get('settings', {}),
                'max_players': 4,
                'real_time': True,
                'scoring_type': 'survival'
            }
        })
        return self

    def as_multiplayer(self, max_players: int = 4) -> 'GameBuilder':
        """Configure as multiplayer game"""
        self._data['settings']['max_players'] = max_players
        self._data['settings']['multiplayer'] = True
        return self

    def with_time_limit(self, seconds: int) -> 'GameBuilder':
        """Set time limit"""
        self._data['settings']['time_limit'] = seconds
        return self

    def inactive(self) -> 'GameBuilder':
        """Set game as inactive"""
        self._data['active'] = False
        return self

    def free(self) -> 'GameBuilder':
        """Set game as free (0 credits)"""
        self._data['credits_required'] = 0
        return self

    def premium(self, credits: int = 50) -> 'GameBuilder':
        """Configure as premium game"""
        self._data.update({
            'credits_required': credits,
            'premium': True,
            'settings': {
                **self._data.get('settings', {}),
                'premium_features': True
            }
        })
        return self


class SessionBuilder(BaseBuilder):
    """Fluent builder for game session test data"""

    def __init__(self):
        super().__init__()
        # Set sensible defaults
        self._data.update({
            'user_id': str(ObjectId()),
            'game_id': str(ObjectId()),
            'status': 'active',
            'play_duration_ms': 0,
            'score': 0,
            'level': 1,
            'device_info': {
                'platform': 'web',
                'device_type': 'desktop',
                'app_version': '1.0.0'
            },
            'sync_version': 1
        })

    def for_user(self, user_id: Union[str, ObjectId]) -> 'SessionBuilder':
        """Set user ID"""
        self._data['user_id'] = str(user_id)
        return self

    def for_game(self, game_id: Union[str, ObjectId]) -> 'SessionBuilder':
        """Set game ID"""
        self._data['game_id'] = str(game_id)
        return self

    def with_status(self, status: str) -> 'SessionBuilder':
        """Set session status"""
        valid_statuses = ['active', 'paused', 'completed', 'abandoned']
        if status not in valid_statuses:
            raise ValueError(f"Invalid status. Must be one of: {valid_statuses}")
        self._data['status'] = status
        return self

    def active(self) -> 'SessionBuilder':
        """Set as active session"""
        self._data['status'] = 'active'
        return self

    def paused(self) -> 'SessionBuilder':
        """Set as paused session"""
        self._data.update({
            'status': 'paused',
            'paused_at': datetime.now(timezone.utc)
        })
        return self

    def completed(self, final_score: int = None) -> 'SessionBuilder':
        """Set as completed session"""
        self._data.update({
            'status': 'completed',
            'completed_at': datetime.now(timezone.utc),
            'final_score': final_score or self._data.get('score', 100)
        })
        return self

    def with_score(self, score: int) -> 'SessionBuilder':
        """Set session score"""
        self._data['score'] = score
        return self

    def with_duration(self, duration_ms: int) -> 'SessionBuilder':
        """Set play duration in milliseconds"""
        self._data['play_duration_ms'] = duration_ms
        return self

    def on_mobile(self) -> 'SessionBuilder':
        """Configure for mobile device"""
        self._data['device_info'].update({
            'platform': 'mobile',
            'device_type': 'mobile'
        })
        return self

    def on_desktop(self) -> 'SessionBuilder':
        """Configure for desktop device"""
        self._data['device_info'].update({
            'platform': 'web',
            'device_type': 'desktop'
        })
        return self

    def with_level(self, level: int) -> 'SessionBuilder':
        """Set current level"""
        self._data['level'] = level
        return self


class APIRequestBuilder(BaseBuilder):
    """Fluent builder for API request test data"""

    def __init__(self):
        super().__init__()
        self._headers = {'Content-Type': 'application/json'}

    def with_auth(self, token: str = None) -> 'APIRequestBuilder':
        """Add authentication header"""
        token = token or f'test_token_{uuid.uuid4().hex[:8]}'
        self._headers['Authorization'] = f'Bearer {token}'
        return self

    def with_header(self, name: str, value: str) -> 'APIRequestBuilder':
        """Add custom header"""
        self._headers[name] = value
        return self

    def with_json_body(self, body: Dict[str, Any]) -> 'APIRequestBuilder':
        """Set JSON request body"""
        self._data = body
        return self

    def build_request(self) -> Dict[str, Any]:
        """Build complete request with headers and body"""
        return {
            'headers': self._headers,
            'json': self._data if self._data else None
        }

    def for_user_creation(self) -> 'APIRequestBuilder':
        """Configure for user creation request"""
        self._data = {
            'email': f'newuser_{uuid.uuid4().hex[:8]}@example.com',
            'password': 'password123',
            'first_name': 'New',
            'last_name': 'User'
        }
        return self

    def for_user_update(self) -> 'APIRequestBuilder':
        """Configure for user update request"""
        self._data = {
            'first_name': 'Updated',
            'last_name': 'Name'
        }
        return self

    def for_game_creation(self) -> 'APIRequestBuilder':
        """Configure for game creation request"""
        self._data = {
            'title': f'New Game {uuid.uuid4().hex[:6]}',
            'description': 'A newly created test game',
            'category': 'puzzle',
            'difficulty': 'medium',
            'credits_required': 10
        }
        return self

    def for_preferences_update(self) -> 'APIRequestBuilder':
        """Configure for preferences update request"""
        self._data = {
            'gaming': {'difficulty': 'hard'},
            'notifications': {'email_enabled': False},
            'privacy': {'profile_public': True}
        }
        return self


class AuthTokenBuilder(BaseBuilder):
    """Fluent builder for authentication token test data"""

    def __init__(self):
        super().__init__()
        self._data.update({
            'user_id': str(ObjectId()),
            'email': f'user_{uuid.uuid4().hex[:8]}@example.com',
            'role': 'user',
            'permissions': ['read'],
            'issued_at': datetime.now(timezone.utc),
            'expires_at': datetime.now(timezone.utc).replace(year=2025)
        })

    def for_user(self, user_id: Union[str, ObjectId], email: str = None) -> 'AuthTokenBuilder':
        """Set user information"""
        self._data['user_id'] = str(user_id)
        if email:
            self._data['email'] = email
        return self

    def with_role(self, role: str) -> 'AuthTokenBuilder':
        """Set user role"""
        self._data['role'] = role
        return self

    def with_permissions(self, permissions: List[str]) -> 'AuthTokenBuilder':
        """Set permissions"""
        self._data['permissions'] = permissions
        return self

    def as_admin_token(self) -> 'AuthTokenBuilder':
        """Configure as admin token"""
        self._data.update({
            'role': 'admin',
            'permissions': ['read', 'write', 'admin']
        })
        return self

    def expired(self) -> 'AuthTokenBuilder':
        """Set token as expired"""
        self._data['expires_at'] = datetime.now(timezone.utc).replace(year=2020)
        return self

    def long_lived(self) -> 'AuthTokenBuilder':
        """Set token as long-lived"""
        self._data['expires_at'] = datetime.now(timezone.utc).replace(year=2030)
        return self


class PreferencesBuilder(BaseBuilder):
    """Fluent builder for user preferences test data"""

    def __init__(self):
        super().__init__()
        self._data.update({
            'gaming': {
                'difficulty': 'medium',
                'auto_save': True,
                'sound_enabled': True
            },
            'notifications': {
                'email_enabled': True,
                'push_enabled': False,
                'achievements': True
            },
            'privacy': {
                'profile_public': False,
                'show_stats': True,
                'show_achievements': True
            },
            'donations': {
                'auto_donate': False,
                'default_amount': 5
            }
        })

    def gaming_hard(self) -> 'PreferencesBuilder':
        """Set gaming difficulty to hard"""
        self._data['gaming']['difficulty'] = 'hard'
        return self

    def gaming_easy(self) -> 'PreferencesBuilder':
        """Set gaming difficulty to easy"""
        self._data['gaming']['difficulty'] = 'easy'
        return self

    def notifications_disabled(self) -> 'PreferencesBuilder':
        """Disable all notifications"""
        self._data['notifications'].update({
            'email_enabled': False,
            'push_enabled': False,
            'achievements': False
        })
        return self

    def privacy_public(self) -> 'PreferencesBuilder':
        """Set public privacy settings"""
        self._data['privacy'].update({
            'profile_public': True,
            'show_stats': True,
            'show_achievements': True
        })
        return self

    def privacy_private(self) -> 'PreferencesBuilder':
        """Set private privacy settings"""
        self._data['privacy'].update({
            'profile_public': False,
            'show_stats': False,
            'show_achievements': False
        })
        return self

    def auto_donations(self, amount: int = 10) -> 'PreferencesBuilder':
        """Enable auto donations"""
        self._data['donations'].update({
            'auto_donate': True,
            'default_amount': amount
        })
        return self


class AchievementBuilder(BaseBuilder):
    """Fluent builder for achievement test data"""

    def __init__(self):
        super().__init__()
        self._data.update({
            'title': f'Test Achievement {uuid.uuid4().hex[:6]}',
            'description': 'A test achievement',
            'category': 'gameplay',
            'points': 100,
            'rarity': 'common',
            'conditions': {
                'type': 'score_threshold',
                'value': 1000
            },
            'active': True
        })

    def with_title(self, title: str) -> 'AchievementBuilder':
        """Set achievement title"""
        self._data['title'] = title
        return self

    def with_points(self, points: int) -> 'AchievementBuilder':
        """Set achievement points"""
        self._data['points'] = points
        return self

    def rare(self) -> 'AchievementBuilder':
        """Set as rare achievement"""
        self._data.update({
            'rarity': 'rare',
            'points': 500
        })
        return self

    def epic(self) -> 'AchievementBuilder':
        """Set as epic achievement"""
        self._data.update({
            'rarity': 'epic',
            'points': 1000
        })
        return self

    def score_based(self, threshold: int) -> 'AchievementBuilder':
        """Set as score-based achievement"""
        self._data['conditions'] = {
            'type': 'score_threshold',
            'value': threshold
        }
        return self

    def time_based(self, seconds: int) -> 'AchievementBuilder':
        """Set as time-based achievement"""
        self._data['conditions'] = {
            'type': 'time_limit',
            'value': seconds
        }
        return self


class TransactionBuilder(BaseBuilder):
    """Fluent builder for transaction test data"""

    def __init__(self):
        super().__init__()
        self._data.update({
            'user_id': str(ObjectId()),
            'amount': 10,
            'currency': 'credits',
            'type': 'purchase',
            'status': 'completed',
            'description': 'Test transaction'
        })

    def for_user(self, user_id: Union[str, ObjectId]) -> 'TransactionBuilder':
        """Set user ID"""
        self._data['user_id'] = str(user_id)
        return self

    def with_amount(self, amount: int) -> 'TransactionBuilder':
        """Set transaction amount"""
        self._data['amount'] = amount
        return self

    def credit_purchase(self, credits: int) -> 'TransactionBuilder':
        """Configure as credit purchase"""
        self._data.update({
            'amount': credits,
            'currency': 'credits',
            'type': 'purchase',
            'description': f'Purchase of {credits} credits'
        })
        return self

    def donation(self, amount: int) -> 'TransactionBuilder':
        """Configure as donation"""
        self._data.update({
            'amount': amount,
            'currency': 'usd',
            'type': 'donation',
            'description': f'Donation of ${amount}'
        })
        return self

    def pending(self) -> 'TransactionBuilder':
        """Set transaction as pending"""
        self._data['status'] = 'pending'
        return self

    def failed(self) -> 'TransactionBuilder':
        """Set transaction as failed"""
        self._data['status'] = 'failed'
        return self


# Convenience functions for quick access

def user() -> UserBuilder:
    """Create a new UserBuilder"""
    return UserBuilder()

def admin_user() -> UserBuilder:
    """Create a new admin UserBuilder"""
    return UserBuilder().as_admin()

def game() -> GameBuilder:
    """Create a new GameBuilder"""
    return GameBuilder()

def puzzle_game() -> GameBuilder:
    """Create a new puzzle GameBuilder"""
    return GameBuilder().as_puzzle()

def session() -> SessionBuilder:
    """Create a new SessionBuilder"""
    return SessionBuilder()

def api_request() -> APIRequestBuilder:
    """Create a new APIRequestBuilder"""
    return APIRequestBuilder()

def auth_token() -> AuthTokenBuilder:
    """Create a new AuthTokenBuilder"""
    return AuthTokenBuilder()

def preferences() -> PreferencesBuilder:
    """Create a new PreferencesBuilder"""
    return PreferencesBuilder()

def achievement() -> AchievementBuilder:
    """Create a new AchievementBuilder"""
    return AchievementBuilder()

def transaction() -> TransactionBuilder:
    """Create a new TransactionBuilder"""
    return TransactionBuilder()


# Usage Examples:
"""
# Simple usage
user_data = user().with_email('test@example.com').build()

# Chained configuration
admin_data = user().as_admin().with_name('Admin', 'User').with_timestamps().build()

# Game configuration
puzzle_data = game().as_puzzle().with_difficulty('hard').free().build()

# Session with user and game
session_data = session().for_user(user_id).for_game(game_id).completed(500).build()

# API request
request = api_request().with_auth().for_user_creation().build_request()

# Complex preferences
prefs = preferences().gaming_hard().notifications_disabled().privacy_public().build()
"""