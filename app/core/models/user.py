from datetime import datetime, timezone
from bson import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash

class User:
    def __init__(self, email, password_hash=None, first_name=None, last_name=None,
                 is_active=True, role='user', _id=None, created_at=None, updated_at=None,
                 gaming_stats=None, impact_score=0, preferences=None, social_profile=None, wallet_credits=None):
        self._id = _id
        self.email = email.lower()
        self.first_name = first_name
        self.last_name = last_name
        self.password_hash = password_hash
        self.is_active = is_active
        self.role = role
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or datetime.now(timezone.utc)

        # Gaming and social extensions
        self.gaming_stats = gaming_stats or {
            'total_play_time': 0,
            'games_played': 0,
            'favorite_category': None,
            'last_activity': None
        }

        self.impact_score = impact_score

        self.preferences = preferences or {
            'notification_enabled': True,
            'preferred_game_categories': [],
            'donation_frequency': 'weekly'
        }

        self.social_profile = social_profile or {
            'display_name': first_name or email.split('@')[0],
            'privacy_level': 'public',
            'friends_count': 0
        }

        self.wallet_credits = wallet_credits or {
            'current_balance': 0.0,
            'total_earned': 0.0,
            'total_donated': 0.0
        }
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        self.updated_at = datetime.now(timezone.utc)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self, include_sensitive=False):
        user_dict = {
            '_id': str(self._id) if self._id else None,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'is_active': self.is_active,
            'role': self.role,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'gaming_stats': self.gaming_stats,
            'impact_score': self.impact_score,
            'preferences': self.preferences,
            'social_profile': self.social_profile,
            'wallet_credits': self.wallet_credits
        }

        if include_sensitive:
            user_dict['password_hash'] = self.password_hash

        return {k: v for k, v in user_dict.items() if v is not None}
    
    @classmethod
    def from_dict(cls, data, include_sensitive=False):
        if not data:
            return None

        return cls(
            _id=data.get('_id'),
            email=data.get('email'),
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            is_active=data.get('is_active', True),
            role=data.get('role', 'user'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
            password_hash=data.get('password_hash') if include_sensitive else None,
            gaming_stats=data.get('gaming_stats'),
            impact_score=data.get('impact_score', 0),
            preferences=data.get('preferences'),
            social_profile=data.get('social_profile'),
            wallet_credits=data.get('wallet_credits')
        )
    
    def get_id(self):
        return str(self._id) if self._id else None

    def update_gaming_stats(self, play_time=0, game_category=None):
        """Update user gaming statistics"""
        self.gaming_stats['total_play_time'] += play_time
        if game_category and game_category not in [None, '']:
            self.gaming_stats['favorite_category'] = game_category
        self.gaming_stats['last_activity'] = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    def add_credits(self, amount, transaction_type='earned'):
        """Add credits to user wallet"""
        if amount > 0:
            self.wallet_credits['current_balance'] += amount
            if transaction_type == 'earned':
                self.wallet_credits['total_earned'] += amount
            self.updated_at = datetime.now(timezone.utc)

    def donate_credits(self, amount):
        """Deduct credits for donation"""
        if amount > 0 and self.wallet_credits['current_balance'] >= amount:
            self.wallet_credits['current_balance'] -= amount
            self.wallet_credits['total_donated'] += amount
            self.updated_at = datetime.now(timezone.utc)
            return True
        return False

    def update_preferences(self, **kwargs):
        """Update user preferences"""
        for key, value in kwargs.items():
            if key in self.preferences:
                self.preferences[key] = value
        self.updated_at = datetime.now(timezone.utc)

    def update_social_profile(self, **kwargs):
        """Update social profile settings"""
        for key, value in kwargs.items():
            if key in self.social_profile:
                self.social_profile[key] = value
        self.updated_at = datetime.now(timezone.utc)

    def __repr__(self):
        return f'<User {self.email}>'