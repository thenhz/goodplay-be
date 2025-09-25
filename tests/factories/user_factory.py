"""
User Factory Module

Factory-Boy implementations for generating User and related objects
with customizable attributes and realistic defaults using Factory-Boy patterns.
"""
import random
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
import factory
from factory import LazyFunction, LazyAttribute, Sequence, Trait, SubFactory
from faker import Faker

# Import our custom providers and base classes
from tests.factories.base import MongoFactory, TimestampMixin, fake
from tests.factories.providers import (
    UserDataProvider, FinancialDataProvider
)

# Register our custom providers
fake.add_provider(UserDataProvider)
fake.add_provider(FinancialDataProvider)

# Import the User model for type hints
from app.core.models.user import User


class UserFactory(MongoFactory):
    """Factory-Boy factory for creating User objects with realistic data

    Supports traits for different user types and uses custom providers
    for domain-specific realistic data generation.

    Usage:
        user = UserFactory()  # Basic user
        admin = UserFactory(admin=True)  # Admin trait
        veteran = UserFactory(veteran=True)  # Veteran trait
        batch = UserFactory.build_batch(10)  # Batch creation
    """

    class Meta:
        model = dict  # We're creating dictionaries, not actual model instances

    # Basic user information
    email = Sequence(lambda n: f'user{n}@goodplay.test')
    first_name = LazyFunction(fake.user_first_name)
    last_name = LazyFunction(fake.user_last_name)
    password_hash = factory.LazyFunction(lambda: 'hashed_password_placeholder')

    # Status and verification
    is_active = True
    is_verified = True
    role = 'user'

    # Timestamps with realistic past dates
    created_at = LazyFunction(lambda: datetime.now(timezone.utc) - timedelta(days=random.randint(1, 365)))
    updated_at = LazyFunction(lambda: datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 24)))
    last_login = LazyFunction(lambda: datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 72)))

    # Optional contact information
    phone = LazyFunction(fake.phone_number_realistic)
    date_of_birth = LazyFunction(lambda: fake.user_age_range()[1])  # Get just the date string
    country = LazyFunction(fake.user_country)
    timezone = LazyFunction(fake.user_timezone)

    # Optional profile information
    bio = factory.LazyFunction(lambda: fake.user_bio() if random.random() > 0.3 else None)
    avatar_url = factory.LazyFunction(lambda: fake.user_avatar_url() if random.random() > 0.4 else None)

    # Gaming statistics
    gaming_stats = LazyFunction(lambda: fake.gaming_stats(veteran=False))
    impact_score = LazyFunction(lambda: random.randint(0, 1000))

    # Social profile
    social_profile = LazyFunction(lambda: {
        'display_name': fake.user_first_name(),
        'privacy_level': random.choice(['public', 'friends', 'private']),
        'friends_count': random.randint(0, 100)
    })

    # Wallet and financial information
    wallet_credits = LazyFunction(lambda: {
        'current_balance': round(random.uniform(0, 500), 2),
        'total_earned': round(random.uniform(0, 2000), 2),
        'total_donated': round(random.uniform(0, 1000), 2)
    })

    # Default preferences structure
    preferences = LazyFunction(lambda: {
        'gaming': {
            'preferred_categories': fake.game_categories(count=random.randint(1, 3)),
            'difficulty_level': random.choice(['easy', 'medium', 'hard']),
            'tutorial_enabled': random.choice([True, False]),
            'auto_save': True,
            'sound_enabled': random.choice([True, False]),
            'music_enabled': random.choice([True, False]),
            'vibration_enabled': random.choice([True, False])
        },
        'notifications': {
            'push_enabled': random.choice([True, False]),
            'email_enabled': random.choice([True, False]),
            'frequency': random.choice(['daily', 'weekly', 'monthly']),
            'achievement_alerts': random.choice([True, False]),
            'donation_confirmations': random.choice([True, False]),
            'friend_activity': random.choice([True, False]),
            'tournament_reminders': random.choice([True, False]),
            'maintenance_alerts': True
        },
        'privacy': {
            'profile_visibility': random.choice(['public', 'friends', 'private']),
            'stats_sharing': random.choice([True, False]),
            'friends_discovery': random.choice([True, False]),
            'leaderboard_participation': random.choice([True, False]),
            'activity_visibility': random.choice(['public', 'friends', 'private']),
            'contact_permissions': random.choice(['everyone', 'friends', 'none'])
        },
        'donations': {
            'auto_donate_enabled': random.choice([True, False]),
            'auto_donate_percentage': round(random.uniform(5.0, 25.0), 1),
            'preferred_causes': fake.donation_causes(count=random.randint(1, 3)),
            'notification_threshold': round(random.uniform(10.0, 100.0), 2),
            'monthly_goal': round(random.uniform(50.0, 500.0), 2),
            'impact_sharing': random.choice([True, False])
        }
    })

    # User type traits
    class Params:
        admin = factory.Trait(
            role='admin',
            is_verified=True,
            created_at=LazyFunction(lambda: datetime.now(timezone.utc) - timedelta(days=random.randint(100, 1000))),
            gaming_stats=LazyFunction(lambda: fake.gaming_stats(veteran=True)),
            wallet_credits=LazyFunction(lambda: {
                'current_balance': round(random.uniform(1000, 10000), 2),
                'total_earned': round(random.uniform(5000, 50000), 2),
                'total_donated': round(random.uniform(2000, 20000), 2)
            })
        )

        veteran = factory.Trait(
            created_at=LazyFunction(lambda: datetime.now(timezone.utc) - timedelta(days=random.randint(500, 1500))),
            is_verified=True,
            gaming_stats=LazyFunction(lambda: fake.gaming_stats(veteran=True)),
            wallet_credits=LazyFunction(lambda: {
                'current_balance': round(random.uniform(100, 2000), 2),
                'total_earned': round(random.uniform(1000, 10000), 2),
                'total_donated': round(random.uniform(500, 5000), 2)
            }),
            social_profile=LazyFunction(lambda: {
                'display_name': fake.user_first_name(),
                'privacy_level': 'public',
                'friends_count': random.randint(50, 200)
            })
        )

        new_user = factory.Trait(
            created_at=LazyFunction(lambda: datetime.now(timezone.utc) - timedelta(minutes=random.randint(1, 60))),
            updated_at=LazyFunction(lambda: datetime.now(timezone.utc) - timedelta(minutes=random.randint(1, 30))),
            last_login=LazyFunction(lambda: datetime.now(timezone.utc) - timedelta(minutes=random.randint(1, 30))),
            is_verified=False,
            gaming_stats=LazyFunction(lambda: {
                'total_play_time': 0,
                'games_played': 0,
                'favorite_category': None,
                'last_activity': None,
                'average_session_length': 0,
                'achievements_unlocked': 0,
                'high_scores': 0
            }),
            wallet_credits=LazyFunction(lambda: {
                'current_balance': 0.0,
                'total_earned': 0.0,
                'total_donated': 0.0
            }),
            social_profile=LazyFunction(lambda: {
                'display_name': fake.user_first_name(),
                'privacy_level': 'public',
                'friends_count': 0
            })
        )

        inactive = factory.Trait(
            is_active=False,
            last_login=LazyFunction(lambda: datetime.now(timezone.utc) - timedelta(days=random.randint(30, 365)))
        )

        unverified = factory.Trait(
            is_verified=False,
            verification_token=LazyFunction(lambda: fake.sha256()[:32]),
            verification_sent_at=LazyFunction(lambda: datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 24)))
        )

        privacy_focused = factory.Trait(
            preferences=LazyFunction(lambda: {
                'gaming': {
                    'preferred_categories': [],
                    'difficulty_level': 'medium',
                    'tutorial_enabled': True,
                    'auto_save': True,
                    'sound_enabled': True,
                    'music_enabled': True,
                    'vibration_enabled': False
                },
                'notifications': {
                    'push_enabled': False,
                    'email_enabled': False,
                    'frequency': 'none',
                    'achievement_alerts': False,
                    'donation_confirmations': True,
                    'friend_activity': False,
                    'tournament_reminders': False,
                    'maintenance_alerts': True
                },
                'privacy': {
                    'profile_visibility': 'private',
                    'stats_sharing': False,
                    'friends_discovery': False,
                    'leaderboard_participation': False,
                    'activity_visibility': 'private',
                    'contact_permissions': 'none'
                },
                'donations': {
                    'auto_donate_enabled': False,
                    'auto_donate_percentage': 0,
                    'preferred_causes': [],
                    'notification_threshold': 100.0,
                    'monthly_goal': None,
                    'impact_sharing': False
                }
            }),
            social_profile=LazyFunction(lambda: {
                'display_name': 'Anonymous',
                'privacy_level': 'private',
                'friends_count': 0
            })
        )

    @classmethod
    def create_friends_group(cls, count: int = 3, **kwargs) -> List[Dict[str, Any]]:
        """Create a group of users who are friends with each other"""
        users = cls.build_batch(count, **kwargs)

        # Add friend relationships
        for i, user in enumerate(users):
            friend_ids = [u['_id'] for j, u in enumerate(users) if j != i]
            # Each user is friends with some random subset of the group
            user['friends'] = random.sample(friend_ids, random.randint(1, len(friend_ids)))
            user['social_profile']['friends_count'] = len(user['friends'])

        return users

    @classmethod
    def create_diverse_group(cls, count: int = 10, **kwargs) -> List[Dict[str, Any]]:
        """Create a diverse group of users with different characteristics"""
        users = []

        # Create one of each type if count allows
        if count >= 5:
            users.append(cls.build(admin=True, **kwargs))
            users.append(cls.build(veteran=True, **kwargs))
            users.append(cls.build(new_user=True, **kwargs))
            users.append(cls.build(inactive=True, **kwargs))
            users.append(cls.build(unverified=True, **kwargs))

            # Fill remaining with regular users
            remaining = count - 5
            if remaining > 0:
                users.extend(cls.build_batch(remaining, **kwargs))
        else:
            # Just create regular users if count is too small
            users.extend(cls.build_batch(count, **kwargs))

        return users


class UserPreferencesFactory(MongoFactory):
    """Factory-Boy factory for creating UserPreferences objects

    Creates detailed user preference structures with realistic defaults
    and support for different preference profiles via traits.

    Usage:
        prefs = UserPreferencesFactory()  # Default preferences
        gaming_prefs = UserPreferencesFactory(gaming_focused=True)
        privacy_prefs = UserPreferencesFactory(privacy_focused=True)
    """

    class Meta:
        model = dict

    user_id = factory.LazyFunction(lambda: str(fake.mongodb_object_id()))

    # Gaming preferences
    gaming = LazyFunction(lambda: {
        'preferred_categories': fake.game_categories(count=random.randint(1, 3)),
        'difficulty_level': random.choice(['easy', 'medium', 'hard']),
        'tutorial_enabled': random.choice([True, False]),
        'auto_save': random.choice([True, False]),
        'sound_enabled': random.choice([True, False]),
        'music_enabled': random.choice([True, False]),
        'vibration_enabled': random.choice([True, False])
    })

    # Notification preferences
    notifications = LazyFunction(lambda: {
        'push_enabled': random.choice([True, False]),
        'email_enabled': random.choice([True, False]),
        'frequency': random.choice(['daily', 'weekly', 'monthly']),
        'achievement_alerts': random.choice([True, False]),
        'donation_confirmations': random.choice([True, False]),
        'friend_activity': random.choice([True, False]),
        'tournament_reminders': random.choice([True, False]),
        'maintenance_alerts': True
    })

    # Privacy preferences
    privacy = LazyFunction(lambda: {
        'profile_visibility': random.choice(['public', 'friends', 'private']),
        'stats_sharing': random.choice([True, False]),
        'friends_discovery': random.choice([True, False]),
        'leaderboard_participation': random.choice([True, False]),
        'activity_visibility': random.choice(['public', 'friends', 'private']),
        'contact_permissions': random.choice(['everyone', 'friends', 'none'])
    })

    # Donation preferences
    donations = LazyFunction(lambda: {
        'auto_donate_enabled': random.choice([True, False]),
        'auto_donate_percentage': round(random.uniform(5.0, 25.0), 1),
        'preferred_causes': fake.donation_causes(count=random.randint(1, 3)),
        'notification_threshold': round(random.uniform(10.0, 100.0), 2),
        'monthly_goal': round(random.uniform(50.0, 500.0), 2),
        'impact_sharing': random.choice([True, False])
    })

    class Params:
        gaming_focused = factory.Trait(
            gaming=LazyFunction(lambda: {
                'preferred_categories': ['action', 'adventure', 'puzzle', 'strategy'],
                'difficulty_level': random.choice(['medium', 'hard']),
                'tutorial_enabled': False,
                'auto_save': True,
                'sound_enabled': True,
                'music_enabled': True,
                'vibration_enabled': True
            }),
            notifications=LazyFunction(lambda: {
                'push_enabled': True,
                'email_enabled': True,
                'frequency': 'daily',
                'achievement_alerts': True,
                'donation_confirmations': True,
                'friend_activity': True,
                'tournament_reminders': True,
                'maintenance_alerts': True
            })
        )

        privacy_focused = factory.Trait(
            privacy=LazyFunction(lambda: {
                'profile_visibility': 'private',
                'stats_sharing': False,
                'friends_discovery': False,
                'leaderboard_participation': False,
                'activity_visibility': 'private',
                'contact_permissions': 'none'
            }),
            notifications=LazyFunction(lambda: {
                'push_enabled': False,
                'email_enabled': False,
                'frequency': 'none',
                'achievement_alerts': False,
                'donation_confirmations': True,
                'friend_activity': False,
                'tournament_reminders': False,
                'maintenance_alerts': True
            })
        )

        minimal = factory.Trait(
            gaming=LazyFunction(lambda: {
                'preferred_categories': [],
                'difficulty_level': 'easy',
                'tutorial_enabled': True,
                'auto_save': True,
                'sound_enabled': False,
                'music_enabled': False,
                'vibration_enabled': False
            }),
            notifications=LazyFunction(lambda: {
                'push_enabled': False,
                'email_enabled': False,
                'frequency': 'none',
                'achievement_alerts': False,
                'donation_confirmations': False,
                'friend_activity': False,
                'tournament_reminders': False,
                'maintenance_alerts': True
            }),
            privacy=LazyFunction(lambda: {
                'profile_visibility': 'private',
                'stats_sharing': False,
                'friends_discovery': False,
                'leaderboard_participation': False,
                'activity_visibility': 'private',
                'contact_permissions': 'none'
            }),
            donations=LazyFunction(lambda: {
                'auto_donate_enabled': False,
                'auto_donate_percentage': 0,
                'preferred_causes': [],
                'notification_threshold': 0,
                'monthly_goal': None,
                'impact_sharing': False
            })
        )


# Legacy compatibility - maintain old interface for existing tests
class LegacyUserFactory:
    """Legacy wrapper for backward compatibility with existing tests"""

    def __init__(self, test_utils=None):
        # Ignore test_utils parameter for Factory-Boy compatibility
        pass

    def create(self, **overrides):
        """Create single user - delegates to Factory-Boy"""
        return UserFactory.build(**overrides)

    def create_batch(self, count: int, **base_overrides):
        """Create multiple users - delegates to Factory-Boy"""
        return UserFactory.build_batch(count, **base_overrides)

    def create_admin(self, **overrides):
        """Create admin user - delegates to Factory-Boy with admin trait"""
        return UserFactory.build(admin=True, **overrides)

    def create_new_user(self, **overrides):
        """Create new user - delegates to Factory-Boy with new_user trait"""
        return UserFactory.build(new_user=True, **overrides)

    def create_veteran_user(self, **overrides):
        """Create veteran user - delegates to Factory-Boy with veteran trait"""
        return UserFactory.build(veteran=True, **overrides)

    def create_inactive_user(self, **overrides):
        """Create inactive user - delegates to Factory-Boy with inactive trait"""
        return UserFactory.build(inactive=True, **overrides)

    def create_unverified_user(self, **overrides):
        """Create unverified user - delegates to Factory-Boy with unverified trait"""
        return UserFactory.build(unverified=True, **overrides)

    def create_friends(self, count: int = 2):
        """Create friends group - delegates to Factory-Boy class method"""
        return UserFactory.create_friends_group(count)

    def create_diverse_group(self, count: int = 10):
        """Create diverse group - delegates to Factory-Boy class method"""
        return UserFactory.create_diverse_group(count)


# For backward compatibility, expose the legacy interface as the main class
# This allows existing tests to work without modification
UserFactoryLegacy = LegacyUserFactory