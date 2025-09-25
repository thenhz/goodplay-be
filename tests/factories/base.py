"""
Base factory classes and shared functionality for GoodPlay test factories

Provides MongoDB ObjectId handling, custom providers, and shared configurations
for enterprise-grade test data generation with Factory-Boy.
"""
import random
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from bson import ObjectId
import factory
from faker import Faker
from faker.providers import BaseProvider

# Initialize faker instance for shared use
fake = Faker()


class ObjectIdField(factory.LazyFunction):
    """Factory field for generating MongoDB ObjectId instances"""

    def __init__(self):
        super().__init__(ObjectId)


class MongoFactory(factory.Factory):
    """Base factory class for MongoDB document factories"""

    class Meta:
        abstract = True

    # Common MongoDB fields
    _id = ObjectIdField()
    created_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))
    updated_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))


class TimestampMixin:
    """Mixin for realistic timestamp generation"""

    @classmethod
    def _generate_past_timestamp(cls, days_ago_min: int = 1, days_ago_max: int = 365) -> datetime:
        """Generate a realistic past timestamp"""
        days_ago = random.randint(days_ago_min, days_ago_max)
        return datetime.now(timezone.utc) - timedelta(days=days_ago)

    @classmethod
    def _generate_recent_timestamp(cls, hours_ago_min: int = 1, hours_ago_max: int = 72) -> datetime:
        """Generate a recent timestamp (within last few days)"""
        hours_ago = random.randint(hours_ago_min, hours_ago_max)
        return datetime.now(timezone.utc) - timedelta(hours=hours_ago)


# Custom Faker Providers

class GameCategoryProvider(BaseProvider):
    """Custom provider for game categories"""

    categories = [
        'puzzle', 'strategy', 'action', 'adventure', 'simulation',
        'party', 'trivia', 'word', 'math', 'memory'
    ]

    category_weights = {
        'puzzle': 30, 'strategy': 25, 'action': 20, 'adventure': 15,
        'simulation': 5, 'party': 5, 'trivia': 8, 'word': 7, 'math': 6, 'memory': 9
    }

    def game_category(self) -> str:
        """Generate a weighted random game category"""
        categories = list(self.category_weights.keys())
        weights = list(self.category_weights.values())
        return random.choices(categories, weights=weights)[0]

    def game_categories(self, count: int = None) -> List[str]:
        """Generate multiple game categories"""
        if count is None:
            count = random.randint(1, 3)
        return random.sample(self.categories, min(count, len(self.categories)))


class AchievementProvider(BaseProvider):
    """Custom provider for achievement data"""

    categories = ['gaming', 'social', 'impact']
    rarities = ['common', 'rare', 'epic', 'legendary']

    trigger_types = [
        'game_session', 'game_score', 'social_friend', 'social_like',
        'donation_amount', 'donation_count', 'consecutive_days',
        'game_diversity', 'tournament_victory', 'help_provided'
    ]

    def achievement_category(self) -> str:
        return random.choice(self.categories)

    def achievement_rarity(self) -> str:
        """Generate weighted rarity (more commons than legendaries)"""
        weights = [50, 30, 15, 5]  # common, rare, epic, legendary
        return random.choices(self.rarities, weights=weights)[0]

    def achievement_trigger_type(self) -> str:
        return random.choice(self.trigger_types)


class DeviceInfoProvider(BaseProvider):
    """Custom provider for realistic device information"""

    platforms = ['web', 'mobile', 'tablet']
    device_types = ['desktop', 'smartphone', 'tablet']

    browsers = ['Chrome', 'Firefox', 'Safari', 'Edge']
    mobile_os = ['iOS 15.0', 'iOS 16.0', 'Android 11', 'Android 12', 'Android 13']

    screen_resolutions = {
        'desktop': ['1920x1080', '2560x1440', '3840x2160', '1366x768', '1440x900'],
        'mobile': ['1080x2400', '1170x2532', '1440x3200', '828x1792'],
        'tablet': ['2048x2732', '2560x1600', '2000x1200', '1920x1200']
    }

    device_models = {
        'desktop': ['Windows PC', 'MacBook Pro', 'iMac', 'Linux Desktop'],
        'mobile': ['iPhone 13', 'iPhone 14', 'Samsung Galaxy S21', 'Google Pixel 6', 'OnePlus 9'],
        'tablet': ['iPad Pro', 'Samsung Galaxy Tab', 'Surface Pro', 'iPad Air']
    }

    def device_info(self, device_type: Optional[str] = None) -> Dict[str, Any]:
        """Generate realistic device information"""
        if device_type is None:
            device_type = random.choice(self.device_types)

        if device_type == 'desktop':
            return {
                'platform': 'web',
                'device_type': 'desktop',
                'browser': random.choice(self.browsers),
                'user_agent': f'Mozilla/5.0 ({random.choice(["Windows NT 10.0; Win64; x64", "Macintosh; Intel Mac OS X 10_15_7", "X11; Linux x86_64"])}) AppleWebKit/537.36',
                'app_version': '1.0.0',
                'screen_resolution': random.choice(self.screen_resolutions['desktop'])
            }
        elif device_type in ['smartphone', 'mobile']:
            return {
                'platform': 'mobile',
                'device_type': 'smartphone',
                'user_agent': 'GoodPlay Mobile App 1.2.0',
                'app_version': '1.2.0',
                'os': random.choice(self.mobile_os),
                'screen_resolution': random.choice(self.screen_resolutions['mobile']),
                'device_model': random.choice(self.device_models['mobile'])
            }
        else:  # tablet
            return {
                'platform': 'mobile',
                'device_type': 'tablet',
                'user_agent': 'GoodPlay Mobile App 1.2.0',
                'app_version': '1.2.0',
                'os': random.choice(['iPadOS 15.0', 'Android 11']),
                'screen_resolution': random.choice(self.screen_resolutions['tablet']),
                'device_model': random.choice(self.device_models['tablet'])
            }


class CauseProvider(BaseProvider):
    """Custom provider for donation causes and ONLUS data"""

    causes = [
        'education', 'environment', 'health', 'poverty', 'animals',
        'disaster_relief', 'human_rights', 'children', 'elderly', 'research'
    ]

    onlus_types = [
        'Educational Foundation', 'Environmental NGO', 'Health Organization',
        'Children\'s Charity', 'Animal Welfare', 'Research Institute',
        'Human Rights Organization', 'Community Foundation'
    ]

    def donation_cause(self) -> str:
        return random.choice(self.causes)

    def donation_causes(self, count: int = None) -> List[str]:
        if count is None:
            count = random.randint(1, 3)
        return random.sample(self.causes, min(count, len(self.causes)))

    def onlus_type(self) -> str:
        return random.choice(self.onlus_types)


class GamingStatsProvider(BaseProvider):
    """Custom provider for gaming statistics"""

    def gaming_stats(self, veteran: bool = False) -> Dict[str, Any]:
        """Generate realistic gaming statistics"""
        if veteran:
            return {
                'total_play_time': random.randint(100000, 500000),  # milliseconds
                'games_played': random.randint(500, 2000),
                'favorite_category': fake.game_category(),
                'last_activity': datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 48)),
                'average_session_length': random.randint(600, 3600),  # seconds
                'achievements_unlocked': random.randint(50, 200),
                'high_scores': random.randint(20, 100)
            }
        else:
            return {
                'total_play_time': random.randint(1000, 50000),
                'games_played': random.randint(1, 100),
                'favorite_category': fake.game_category() if random.random() > 0.3 else None,
                'last_activity': datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 168)),
                'average_session_length': random.randint(180, 1800),
                'achievements_unlocked': random.randint(0, 25),
                'high_scores': random.randint(0, 10)
            }


# Register custom providers with faker
fake.add_provider(GameCategoryProvider)
fake.add_provider(AchievementProvider)
fake.add_provider(DeviceInfoProvider)
fake.add_provider(CauseProvider)
fake.add_provider(GamingStatsProvider)


# Utility functions for factories

def generate_unique_email(sequence: int) -> str:
    """Generate unique email addresses for testing"""
    domains = ['goodplay.test', 'example.com', 'test.org', 'demo.net']
    domain = random.choice(domains)
    return f'user{sequence}@{domain}'


def generate_realistic_score(duration_ms: int, difficulty: str = 'medium') -> int:
    """Generate realistic game scores based on duration and difficulty"""
    base_score = int(duration_ms / 1000)  # 1 point per second as base

    difficulty_multipliers = {'easy': 0.5, 'medium': 1.0, 'hard': 1.5}
    multiplier = difficulty_multipliers.get(difficulty, 1.0)

    # Add some randomness
    variance = random.uniform(0.5, 2.0)

    return int(base_score * multiplier * variance)


def generate_wallet_balance(user_type: str = 'regular') -> Dict[str, float]:
    """Generate realistic wallet balances"""
    if user_type == 'admin':
        return {
            'current_balance': round(random.uniform(1000, 10000), 2),
            'total_earned': round(random.uniform(5000, 50000), 2),
            'total_donated': round(random.uniform(2000, 20000), 2)
        }
    elif user_type == 'veteran':
        return {
            'current_balance': round(random.uniform(100, 2000), 2),
            'total_earned': round(random.uniform(1000, 10000), 2),
            'total_donated': round(random.uniform(500, 5000), 2)
        }
    else:  # regular user
        return {
            'current_balance': round(random.uniform(0, 500), 2),
            'total_earned': round(random.uniform(0, 2000), 2),
            'total_donated': round(random.uniform(0, 1000), 2)
        }


# Performance optimization helpers

class BatchFactoryMixin:
    """Mixin for optimized batch creation of factory objects"""

    @classmethod
    def create_batch_optimized(cls, size: int, **kwargs) -> List[Any]:
        """Optimized batch creation that reuses common computed values"""
        # Pre-compute common values that don't need to be unique
        common_timestamp = datetime.now(timezone.utc)

        # Override timestamp generators for batch creation
        kwargs.setdefault('created_at', common_timestamp)

        return [cls.create(**kwargs) for _ in range(size)]


# Factory configuration constants

class FactoryConfig:
    """Configuration constants for factories"""

    # Default batch sizes for different object types
    SMALL_BATCH = 10
    MEDIUM_BATCH = 50
    LARGE_BATCH = 100

    # Performance thresholds
    MAX_OBJECTS_PER_SECOND = 1000
    MAX_MEMORY_USAGE_MB = 100

    # Realistic data ranges
    USER_CREATION_DAYS_RANGE = (1, 1000)  # Users created 1-1000 days ago
    SESSION_DURATION_RANGE = (30000, 3600000)  # 30 seconds to 1 hour in ms
    SCORE_RANGE = (0, 50000)  # Reasonable score range

    # Probability weights for realistic distributions
    ACTIVE_USER_PROBABILITY = 0.85  # 85% of users are active
    VETERAN_USER_PROBABILITY = 0.15  # 15% are veteran users
    COMPLETED_SESSION_PROBABILITY = 0.70  # 70% of sessions are completed