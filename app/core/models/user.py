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
            'gaming': {
                'preferred_categories': [],
                'difficulty_level': 'medium',
                'tutorial_enabled': True,
                'auto_save': True,
                'sound_enabled': True,
                'music_enabled': True,
                'vibration_enabled': True
            },
            'notifications': {
                'push_enabled': True,
                'email_enabled': True,
                'frequency': 'daily',
                'achievement_alerts': True,
                'donation_confirmations': True,
                'friend_activity': True,
                'tournament_reminders': True,
                'maintenance_alerts': True
            },
            'privacy': {
                'profile_visibility': 'public',
                'stats_sharing': True,
                'friends_discovery': True,
                'leaderboard_participation': True,
                'activity_visibility': 'friends',
                'contact_permissions': 'friends'
            },
            'donations': {
                'auto_donate_enabled': False,
                'auto_donate_percentage': 10,
                'preferred_causes': [],
                'notification_threshold': 50,
                'monthly_goal': None,
                'impact_sharing': True
            }
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
        """Update user preferences (legacy method for backwards compatibility)"""
        for key, value in kwargs.items():
            if key in self.preferences:
                self.preferences[key] = value
        self.updated_at = datetime.now(timezone.utc)

    def update_preferences_category(self, category: str, preferences: dict):
        """Update a specific category of preferences"""
        if category in self.preferences and isinstance(preferences, dict):
            for key, value in preferences.items():
                if key in self.preferences[category]:
                    self.preferences[category][key] = value
            self.updated_at = datetime.now(timezone.utc)
            return True
        return False

    def get_preferences_category(self, category: str):
        """Get preferences for a specific category"""
        return self.preferences.get(category, {})

    def reset_preferences_to_defaults(self):
        """Reset all preferences to default values"""
        self.preferences = {
            'gaming': {
                'preferred_categories': [],
                'difficulty_level': 'medium',
                'tutorial_enabled': True,
                'auto_save': True,
                'sound_enabled': True,
                'music_enabled': True,
                'vibration_enabled': True
            },
            'notifications': {
                'push_enabled': True,
                'email_enabled': True,
                'frequency': 'daily',
                'achievement_alerts': True,
                'donation_confirmations': True,
                'friend_activity': True,
                'tournament_reminders': True,
                'maintenance_alerts': True
            },
            'privacy': {
                'profile_visibility': 'public',
                'stats_sharing': True,
                'friends_discovery': True,
                'leaderboard_participation': True,
                'activity_visibility': 'friends',
                'contact_permissions': 'friends'
            },
            'donations': {
                'auto_donate_enabled': False,
                'auto_donate_percentage': 10,
                'preferred_causes': [],
                'notification_threshold': 50,
                'monthly_goal': None,
                'impact_sharing': True
            }
        }
        self.updated_at = datetime.now(timezone.utc)

    @staticmethod
    def validate_preferences_data(data: dict) -> str:
        """Validate preferences data structure and values"""
        if not isinstance(data, dict):
            return "PREFERENCES_INVALID_FORMAT"

        # Validate gaming preferences
        if 'gaming' in data:
            gaming = data['gaming']
            if not isinstance(gaming, dict):
                return "GAMING_PREFERENCES_INVALID"

            if 'difficulty_level' in gaming and gaming['difficulty_level'] not in ['easy', 'medium', 'hard']:
                return "GAMING_DIFFICULTY_INVALID"

            if 'preferred_categories' in gaming and not isinstance(gaming['preferred_categories'], list):
                return "GAMING_CATEGORIES_INVALID"

        # Validate notification preferences
        if 'notifications' in data:
            notifications = data['notifications']
            if not isinstance(notifications, dict):
                return "NOTIFICATION_PREFERENCES_INVALID"

            if 'frequency' in notifications and notifications['frequency'] not in ['none', 'daily', 'weekly', 'monthly']:
                return "NOTIFICATION_FREQUENCY_INVALID"

        # Validate privacy preferences
        if 'privacy' in data:
            privacy = data['privacy']
            if not isinstance(privacy, dict):
                return "PRIVACY_PREFERENCES_INVALID"

            if 'profile_visibility' in privacy and privacy['profile_visibility'] not in ['public', 'friends', 'private']:
                return "PRIVACY_VISIBILITY_INVALID"

            if 'activity_visibility' in privacy and privacy['activity_visibility'] not in ['public', 'friends', 'private']:
                return "PRIVACY_ACTIVITY_INVALID"

            if 'contact_permissions' in privacy and privacy['contact_permissions'] not in ['everyone', 'friends', 'none']:
                return "PRIVACY_CONTACT_INVALID"

        # Validate donation preferences
        if 'donations' in data:
            donations = data['donations']
            if not isinstance(donations, dict):
                return "DONATION_PREFERENCES_INVALID"

            if 'auto_donate_percentage' in donations:
                percentage = donations['auto_donate_percentage']
                if not isinstance(percentage, (int, float)) or percentage < 0 or percentage > 100:
                    return "DONATION_PERCENTAGE_INVALID"

            if 'preferred_causes' in donations and not isinstance(donations['preferred_causes'], list):
                return "DONATION_CAUSES_INVALID"

        return None  # No validation errors

    def update_social_profile(self, **kwargs):
        """Update social profile settings"""
        for key, value in kwargs.items():
            if key in self.social_profile:
                self.social_profile[key] = value
        self.updated_at = datetime.now(timezone.utc)

    def __repr__(self):
        return f'<User {self.email}>'