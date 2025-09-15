from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

class UserPreferences:
    def __init__(self, user_id, gaming=None, notifications=None, privacy=None,
                 donations=None, _id=None, created_at=None, updated_at=None):
        self._id = _id
        self.user_id = user_id
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or datetime.now(timezone.utc)

        # Gaming Preferences
        self.gaming = gaming or {
            'preferred_categories': [],  # e.g., ['puzzle', 'action', 'strategy']
            'difficulty_level': 'medium',  # easy, medium, hard
            'tutorial_enabled': True,
            'auto_save': True,
            'sound_enabled': True,
            'music_enabled': True,
            'vibration_enabled': True
        }

        # Notification Preferences
        self.notifications = notifications or {
            'push_enabled': True,
            'email_enabled': True,
            'frequency': 'daily',  # none, daily, weekly, monthly
            'achievement_alerts': True,
            'donation_confirmations': True,
            'friend_activity': True,
            'tournament_reminders': True,
            'maintenance_alerts': True
        }

        # Privacy Preferences
        self.privacy = privacy or {
            'profile_visibility': 'public',  # public, friends, private
            'stats_sharing': True,
            'friends_discovery': True,
            'leaderboard_participation': True,
            'activity_visibility': 'friends',  # public, friends, private
            'contact_permissions': 'friends'  # everyone, friends, none
        }

        # Donation Preferences
        self.donations = donations or {
            'auto_donate_enabled': False,
            'auto_donate_percentage': 10,  # percentage of earned credits
            'preferred_causes': [],  # e.g., ['education', 'health', 'environment']
            'notification_threshold': 50,  # notify when credits reach this amount
            'monthly_goal': None,  # optional monthly donation goal
            'impact_sharing': True  # share impact stats with friends
        }

    @staticmethod
    def get_default_preferences() -> Dict[str, Any]:
        """Get default preferences for new users"""
        return {
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

    @staticmethod
    def validate_preferences_data(data: Dict[str, Any]) -> Optional[str]:
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

    def update_category(self, category: str, preferences: Dict[str, Any]) -> bool:
        """Update a specific category of preferences"""
        if not hasattr(self, category):
            return False

        current_prefs = getattr(self, category)
        for key, value in preferences.items():
            if key in current_prefs:
                current_prefs[key] = value

        self.updated_at = datetime.now(timezone.utc)
        return True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            '_id': str(self._id) if self._id else None,
            'user_id': str(self.user_id) if self.user_id else None,
            'gaming': self.gaming,
            'notifications': self.notifications,
            'privacy': self.privacy,
            'donations': self.donations,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserPreferences':
        """Create UserPreferences from dictionary"""
        if not data:
            return None

        return cls(
            _id=data.get('_id'),
            user_id=data.get('user_id'),
            gaming=data.get('gaming'),
            notifications=data.get('notifications'),
            privacy=data.get('privacy'),
            donations=data.get('donations'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )

    def reset_to_defaults(self):
        """Reset all preferences to default values"""
        defaults = self.get_default_preferences()
        self.gaming = defaults['gaming']
        self.notifications = defaults['notifications']
        self.privacy = defaults['privacy']
        self.donations = defaults['donations']
        self.updated_at = datetime.now(timezone.utc)

    def get_category(self, category: str) -> Optional[Dict[str, Any]]:
        """Get preferences for a specific category"""
        if hasattr(self, category):
            return getattr(self, category)
        return None

    def __repr__(self):
        return f'<UserPreferences user_id={self.user_id}>'