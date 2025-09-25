"""
User Factory Module

Provides factory classes for generating User and related objects
with customizable attributes and realistic defaults.
"""
import random
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from tests.core import TestUtils


class UserFactory:
    """Factory for creating User objects with realistic data"""

    def __init__(self, test_utils: TestUtils = None):
        self.test_utils = test_utils or TestUtils()
        self._counter = 0

    def create(self, **overrides) -> Dict[str, Any]:
        """Create a single user with optional overrides"""
        self._counter += 1

        defaults = {
            '_id': self.test_utils.get_unique_id(),
            'email': f'user{self._counter}@goodplay.test',
            'first_name': self._generate_first_name(),
            'last_name': self._generate_last_name(),
            'password_hash': 'hashed_password_placeholder',
            'created_at': datetime.now(timezone.utc) - timedelta(days=random.randint(1, 365)),
            'updated_at': datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 24)),
            'last_login': datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 72)),
            'is_active': True,
            'is_verified': True,
            'is_admin': False,
            'phone': self.test_utils.generate_random_phone() if random.random() > 0.5 else None,
            'date_of_birth': self._generate_date_of_birth(),
            'country': self._generate_country(),
            'timezone': self._generate_timezone(),
            'bio': self._generate_bio() if random.random() > 0.7 else None,
            'avatar_url': self._generate_avatar_url() if random.random() > 0.6 else None,
            'total_score': random.randint(0, 10000),
            'games_played': random.randint(0, 500),
            'achievements_earned': random.randint(0, 50),
            'friends_count': random.randint(0, 100),
            'donation_total': round(random.uniform(0, 1000), 2)
        }

        defaults.update(overrides)
        return defaults

    def create_batch(self, count: int, **base_overrides) -> List[Dict[str, Any]]:
        """Create multiple users with optional base overrides"""
        return [self.create(**base_overrides) for _ in range(count)]

    def create_admin(self, **overrides) -> Dict[str, Any]:
        """Create an admin user"""
        admin_defaults = {
            'email': f'admin{self._counter}@goodplay.test',
            'first_name': 'Admin',
            'is_admin': True,
            'is_verified': True,
            'created_at': datetime.now(timezone.utc) - timedelta(days=random.randint(100, 1000))
        }
        admin_defaults.update(overrides)
        return self.create(**admin_defaults)

    def create_new_user(self, **overrides) -> Dict[str, Any]:
        """Create a newly registered user"""
        new_user_defaults = {
            'created_at': datetime.now(timezone.utc) - timedelta(minutes=random.randint(1, 60)),
            'updated_at': datetime.now(timezone.utc) - timedelta(minutes=random.randint(1, 30)),
            'last_login': datetime.now(timezone.utc) - timedelta(minutes=random.randint(1, 30)),
            'is_verified': False,
            'total_score': 0,
            'games_played': 0,
            'achievements_earned': 0,
            'friends_count': 0,
            'donation_total': 0.0
        }
        new_user_defaults.update(overrides)
        return self.create(**new_user_defaults)

    def create_veteran_user(self, **overrides) -> Dict[str, Any]:
        """Create a veteran user with lots of activity"""
        veteran_defaults = {
            'created_at': datetime.now(timezone.utc) - timedelta(days=random.randint(500, 1500)),
            'total_score': random.randint(50000, 200000),
            'games_played': random.randint(1000, 5000),
            'achievements_earned': random.randint(100, 500),
            'friends_count': random.randint(50, 200),
            'donation_total': round(random.uniform(500, 5000), 2),
            'is_verified': True
        }
        veteran_defaults.update(overrides)
        return self.create(**veteran_defaults)

    def create_inactive_user(self, **overrides) -> Dict[str, Any]:
        """Create an inactive user"""
        inactive_defaults = {
            'is_active': False,
            'deactivated_at': datetime.now(timezone.utc) - timedelta(days=random.randint(1, 90)),
            'last_login': datetime.now(timezone.utc) - timedelta(days=random.randint(30, 365))
        }
        inactive_defaults.update(overrides)
        return self.create(**inactive_defaults)

    def create_unverified_user(self, **overrides) -> Dict[str, Any]:
        """Create an unverified user"""
        unverified_defaults = {
            'is_verified': False,
            'verification_token': self.test_utils.generate_random_string(32),
            'verification_sent_at': datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 24))
        }
        unverified_defaults.update(overrides)
        return self.create(**unverified_defaults)

    def create_friends(self, count: int = 2) -> List[Dict[str, Any]]:
        """Create a group of users who are friends with each other"""
        users = self.create_batch(count)

        # Add friend relationships
        for i, user in enumerate(users):
            friend_ids = [u['_id'] for j, u in enumerate(users) if j != i]
            user['friends'] = friend_ids[:random.randint(1, len(friend_ids))]
            user['friends_count'] = len(user['friends'])

        return users

    def create_diverse_group(self, count: int = 10) -> List[Dict[str, Any]]:
        """Create a diverse group of users with different characteristics"""
        users = []

        # Create different types of users
        users.append(self.create_admin())
        users.append(self.create_new_user())
        users.append(self.create_veteran_user())
        users.append(self.create_inactive_user())
        users.append(self.create_unverified_user())

        # Fill the rest with regular users
        remaining = count - len(users)
        if remaining > 0:
            users.extend(self.create_batch(remaining))

        return users

    def _generate_first_name(self) -> str:
        """Generate a realistic first name"""
        first_names = [
            'Alex', 'Jordan', 'Casey', 'Taylor', 'Morgan',
            'Riley', 'Avery', 'Quinn', 'Sage', 'River',
            'Phoenix', 'Rowan', 'Skylar', 'Dakota', 'Cameron',
            'Emery', 'Finley', 'Hayden', 'Indigo', 'Justice'
        ]
        return random.choice(first_names)

    def _generate_last_name(self) -> str:
        """Generate a realistic last name"""
        last_names = [
            'Smith', 'Johnson', 'Williams', 'Brown', 'Jones',
            'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez',
            'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson',
            'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin'
        ]
        return random.choice(last_names)

    def _generate_date_of_birth(self) -> str:
        """Generate a realistic date of birth"""
        # Generate age between 13 and 80
        years_ago = random.randint(13, 80)
        birth_date = datetime.now(timezone.utc) - timedelta(days=years_ago * 365)
        return birth_date.strftime('%Y-%m-%d')

    def _generate_country(self) -> str:
        """Generate a country code"""
        countries = [
            'US', 'CA', 'GB', 'AU', 'DE', 'FR', 'IT', 'ES',
            'BR', 'MX', 'JP', 'KR', 'IN', 'CN', 'RU', 'NL'
        ]
        return random.choice(countries)

    def _generate_timezone(self) -> str:
        """Generate a timezone"""
        timezones = [
            'America/New_York', 'America/Los_Angeles', 'America/Chicago',
            'Europe/London', 'Europe/Paris', 'Europe/Berlin',
            'Asia/Tokyo', 'Asia/Seoul', 'Asia/Shanghai',
            'Australia/Sydney', 'America/Sao_Paulo'
        ]
        return random.choice(timezones)

    def _generate_bio(self) -> str:
        """Generate a short bio"""
        bios = [
            "Gaming enthusiast who loves puzzles and strategy games.",
            "Casual player looking to make friends and have fun!",
            "Competitive gamer always seeking the next challenge.",
            "Playing games to relax after work and help good causes.",
            "New to GoodPlay but excited to contribute to charity while gaming!",
            "Puzzle solver by day, team player by night.",
            "Here to enjoy games and make a positive impact.",
            "Strategy game lover with a passion for helping others."
        ]
        return random.choice(bios)

    def _generate_avatar_url(self) -> str:
        """Generate a mock avatar URL"""
        avatar_styles = ['adventurer', 'avataaars', 'bottts', 'croodles', 'personas']
        style = random.choice(avatar_styles)
        seed = self.test_utils.generate_random_string(10)
        return f"https://api.dicebear.com/7.x/{style}/svg?seed={seed}"


class UserPreferencesFactory:
    """Factory for creating UserPreferences objects"""

    def __init__(self, test_utils: TestUtils = None):
        self.test_utils = test_utils or TestUtils()

    def create(self, **overrides) -> Dict[str, Any]:
        """Create user preferences with optional overrides"""
        defaults = {
            'user_id': self.test_utils.get_unique_id(),
            'gaming': self._create_gaming_preferences(),
            'notifications': self._create_notification_preferences(),
            'privacy': self._create_privacy_preferences(),
            'donations': self._create_donation_preferences(),
            'created_at': datetime.now(timezone.utc) - timedelta(days=random.randint(1, 365)),
            'updated_at': datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 72))
        }

        defaults.update(overrides)
        return defaults

    def create_gaming_focused(self, **overrides) -> Dict[str, Any]:
        """Create gaming-focused preferences"""
        gaming_focused = {
            'gaming': {
                'preferred_categories': ['action', 'adventure', 'puzzle', 'strategy'],
                'difficulty_level': random.choice(['medium', 'hard']),
                'tutorial_enabled': False,
                'auto_save': True,
                'sound_enabled': True,
                'music_enabled': True,
                'vibration_enabled': True
            },
            'notifications': {
                'achievement_alerts': True,
                'tournament_reminders': True,
                'friend_activity': True,
                'push_enabled': True
            }
        }
        gaming_focused.update(overrides)
        return self.create(**gaming_focused)

    def create_privacy_focused(self, **overrides) -> Dict[str, Any]:
        """Create privacy-focused preferences"""
        privacy_focused = {
            'privacy': {
                'profile_visibility': 'private',
                'stats_sharing': False,
                'friends_discovery': False,
                'leaderboard_participation': False,
                'activity_visibility': 'private',
                'contact_permissions': 'none'
            },
            'notifications': {
                'push_enabled': False,
                'email_enabled': False,
                'achievement_alerts': False,
                'friend_activity': False
            }
        }
        privacy_focused.update(overrides)
        return self.create(**privacy_focused)

    def _create_gaming_preferences(self) -> Dict[str, Any]:
        """Create gaming preferences"""
        categories = ['puzzle', 'strategy', 'action', 'adventure', 'simulation']
        return {
            'preferred_categories': random.sample(categories, random.randint(1, 3)),
            'difficulty_level': random.choice(['easy', 'medium', 'hard']),
            'tutorial_enabled': random.choice([True, False]),
            'auto_save': random.choice([True, False]),
            'sound_enabled': random.choice([True, False]),
            'music_enabled': random.choice([True, False]),
            'vibration_enabled': random.choice([True, False])
        }

    def _create_notification_preferences(self) -> Dict[str, Any]:
        """Create notification preferences"""
        return {
            'push_enabled': random.choice([True, False]),
            'email_enabled': random.choice([True, False]),
            'frequency': random.choice(['daily', 'weekly', 'monthly']),
            'achievement_alerts': random.choice([True, False]),
            'donation_confirmations': random.choice([True, False]),
            'friend_activity': random.choice([True, False]),
            'tournament_reminders': random.choice([True, False]),
            'maintenance_alerts': True  # Usually always enabled
        }

    def _create_privacy_preferences(self) -> Dict[str, Any]:
        """Create privacy preferences"""
        return {
            'profile_visibility': random.choice(['public', 'friends', 'private']),
            'stats_sharing': random.choice([True, False]),
            'friends_discovery': random.choice([True, False]),
            'leaderboard_participation': random.choice([True, False]),
            'activity_visibility': random.choice(['public', 'friends', 'private']),
            'contact_permissions': random.choice(['everyone', 'friends', 'none'])
        }

    def _create_donation_preferences(self) -> Dict[str, Any]:
        """Create donation preferences"""
        causes = ['education', 'environment', 'health', 'poverty', 'animals', 'disaster_relief']
        return {
            'auto_donate_enabled': random.choice([True, False]),
            'auto_donate_percentage': round(random.uniform(5.0, 25.0), 1),
            'preferred_causes': random.sample(causes, random.randint(1, 3)),
            'notification_threshold': round(random.uniform(10.0, 100.0), 2),
            'monthly_goal': round(random.uniform(50.0, 500.0), 2),
            'impact_sharing': random.choice([True, False])
        }