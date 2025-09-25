"""
Game Factory Module

Factory-Boy implementations for generating Game, GameSession,
and related objects with realistic data and relationships.
"""
import random
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
import factory
from factory import LazyFunction, LazyAttribute, Sequence, Trait, SubFactory
from faker import Faker

# Import our custom providers and base classes
from tests.factories.base import MongoFactory, TimestampMixin, fake, DeviceInfoProvider
from tests.factories.providers import GameDataProvider

# Register our custom providers
fake.add_provider(GameDataProvider)
fake.add_provider(DeviceInfoProvider)


class GameFactory(MongoFactory):
    """Factory-Boy factory for creating Game objects with realistic data

    Optimized for performance while maintaining essential game fields.
    Achieves 1000+ objects < 1s requirement.

    Usage:
        game = GameFactory()  # Basic game
        puzzle = GameFactory(puzzle=True)  # Puzzle game trait
        multiplayer = GameFactory(multiplayer=True)  # Multiplayer trait
        batch = GameFactory.build_batch(1000)  # Fast batch creation
    """

    class Meta:
        model = dict

    # Core game information (essential fields only)
    name = LazyFunction(lambda: random.choice([
        'Puzzle Quest', 'Strategy Master', 'Action Hero', 'Adventure Land', 'Party Games',
        'Brain Trainer', 'Word Challenge', 'Number Game', 'Memory Test', 'Logic Puzzle',
        'Card Game', 'Board Game', 'Quiz Master', 'Trivia Night', 'Math Challenge'
    ]))
    category = LazyFunction(lambda: random.choice(['puzzle', 'strategy', 'action', 'adventure', 'party']))
    version = LazyFunction(lambda: f'{random.randint(1,3)}.{random.randint(0,2)}.0')

    # Essential game properties
    difficulty_level = LazyFunction(lambda: random.choice(['easy', 'medium', 'hard']))
    is_active = True  # Static value for performance
    credit_rate = LazyFunction(lambda: round(random.uniform(1.0, 2.5), 1))

    # Basic author info
    author = 'GoodPlay Team'  # Static for performance
    plugin_id = Sequence(lambda n: f'plugin_{n}')

    # Player configuration
    min_players = 1
    max_players = LazyFunction(lambda: random.choice([1, 2, 4, 8]))

    # Duration
    estimated_duration_minutes = LazyFunction(lambda: random.choice([10, 15, 30, 45]))

    # Simple flags
    requires_internet = False  # Static for performance

    # Minimal content
    description = LazyFunction(lambda: f"A fun {random.choice(['puzzle', 'strategy', 'action'])} game")
    instructions = 'Game instructions included'
    tags = ['game', 'fun']  # Static list for performance
    screenshots = []  # Empty list for performance

    # Basic stats
    install_count = LazyFunction(lambda: random.randint(100, 50000))
    rating = LazyFunction(lambda: round(random.uniform(3.5, 4.8), 1))
    total_ratings = LazyFunction(lambda: random.randint(10, 1000))

    # Timestamps (inherited from MongoFactory)

    # Game type traits
    class Params:
        puzzle = factory.Trait(
            category='puzzle',
            min_players=1,
            max_players=1,
            difficulty_level='medium',
            estimated_duration_minutes=15,
            tags=['puzzle', 'single-player', 'brain-training', 'logic'],
            requires_internet=False
        )

        strategy = factory.Trait(
            category='strategy',
            min_players=1,
            max_players=4,
            difficulty_level='hard',
            estimated_duration_minutes=45,
            tags=['strategy', 'tactical', 'thinking', 'planning'],
            credit_rate=LazyFunction(lambda: round(random.uniform(1.5, 3.0), 1))
        )

        action = factory.Trait(
            category='action',
            min_players=1,
            max_players=4,
            difficulty_level='medium',
            estimated_duration_minutes=15,
            tags=['action', 'fast-paced', 'reflexes', 'combat'],
            requires_internet=False
        )

        adventure = factory.Trait(
            category='adventure',
            min_players=1,
            max_players=2,
            difficulty_level='medium',
            estimated_duration_minutes=60,
            tags=['adventure', 'story', 'exploration', 'immersive'],
            credit_rate=3.0
        )

        multiplayer = factory.Trait(
            min_players=2,
            max_players=8,
            category='strategy',
            estimated_duration_minutes=30,
            tags=['multiplayer', 'competitive', 'social', 'team-play'],
            requires_internet=True
        )

        quick_play = factory.Trait(
            estimated_duration_minutes=3,
            difficulty_level='easy',
            tags=['quick-play', 'casual', 'time-killer', 'mobile-friendly'],
            min_players=1,
            max_players=2
        )

        party = factory.Trait(
            category='party',
            min_players=3,
            max_players=8,
            difficulty_level='easy',
            estimated_duration_minutes=20,
            tags=['party', 'social', 'fun', 'family-friendly', 'cooperative'],
            requires_internet=True
        )

    @classmethod
    def create_by_category(cls, category: str, count: int = 1, **kwargs) -> List[Dict[str, Any]]:
        """Create games of a specific category"""
        trait_map = {
            'puzzle': 'puzzle',
            'strategy': 'strategy',
            'action': 'action',
            'adventure': 'adventure',
            'party': 'party'
        }

        trait = trait_map.get(category)
        if trait:
            kwargs[trait] = True
        else:
            kwargs['category'] = category

        return cls.build_batch(count, **kwargs)

    @classmethod
    def create_game_collection(cls, count: int = 20, **kwargs) -> List[Dict[str, Any]]:
        """Create a diverse collection of games with different categories"""
        games = []
        categories = ['puzzle', 'strategy', 'action', 'adventure', 'party']

        # Distribute games across categories
        games_per_category = count // len(categories)
        remainder = count % len(categories)

        for i, category in enumerate(categories):
            category_count = games_per_category + (1 if i < remainder else 0)
            if category_count > 0:
                games.extend(cls.create_by_category(category, category_count, **kwargs))

        return games


class GameSessionFactory(MongoFactory):
    """Factory-Boy factory for creating GameSession objects with GOO-9 enhanced features

    Supports precise time tracking, cross-device synchronization, and realistic
    session state management.

    Usage:
        session = GameSessionFactory()  # Basic session
        active = GameSessionFactory(active=True)  # Active session trait
        completed = GameSessionFactory(completed=True)  # Completed session trait
        cross_device = GameSessionFactory(cross_device=True)  # Cross-device session
    """

    class Meta:
        model = dict

    # Basic session information
    user_id = LazyFunction(lambda: fake.uuid4()[:24])  # Simplified for performance
    game_id = LazyFunction(lambda: fake.uuid4()[:24])  # Simplified for performance
    session_id = LazyFunction(lambda: fake.uuid4())

    # Session status
    status = LazyFunction(lambda: random.choices(
        ['active', 'paused', 'completed', 'abandoned'],
        weights=[20, 10, 60, 10]  # Most sessions are completed
    )[0])

    # Timing information (GOO-9 enhanced features)
    started_at = LazyFunction(lambda: datetime.now(timezone.utc) - timedelta(
        minutes=random.randint(1, 1440)  # 1 minute to 24 hours ago
    ))

    # Play duration in milliseconds (precise timing)
    play_duration = LazyFunction(lambda: random.randint(30000, 3600000))  # 30s to 1h

    # Enhanced timestamps for pause/resume functionality
    paused_at = None
    resumed_at = None
    ended_at = None

    # Cross-device synchronization fields
    device_info = LazyFunction(fake.device_info)
    sync_version = LazyFunction(lambda: random.randint(1, 10))
    last_sync_at = LazyFunction(lambda: datetime.now(timezone.utc) - timedelta(
        minutes=random.randint(1, 60)
    ))

    # Game state and statistics
    current_state = LazyFunction(lambda: {
        'level': random.randint(1, 20),
        'lives': random.randint(0, 5),
        'score': random.randint(0, 50000),
        'power_ups': random.sample(['shield', 'double_score', 'time_bonus', 'extra_life'],
                                  random.randint(0, 3)),
        'inventory': {
            'coins': random.randint(0, 1000),
            'gems': random.randint(0, 50),
            'keys': random.randint(0, 10)
        },
        'progress': {
            'completion_percentage': round(random.uniform(0, 100), 1),
            'checkpoints_reached': random.randint(0, 10),
            'secrets_found': random.randint(0, 5)
        }
    })

    # Session configuration
    session_config = LazyFunction(lambda: {
        'difficulty': random.choice(['easy', 'medium', 'hard']),
        'sound_volume': round(random.uniform(0, 1), 1),
        'music_volume': round(random.uniform(0, 1), 1),
        'auto_save': True,
        'tutorial_shown': random.choice([True, False])
    })

    # Game moves and interactions
    moves = LazyFunction(lambda: [
        {
            'type': random.choice(['click', 'swipe', 'key_press', 'drag']),
            'timestamp': fake.date_time_this_year(),
            'position': {'x': random.randint(0, 1920), 'y': random.randint(0, 1080)},
            'success': random.choice([True, False])
        } for _ in range(random.randint(10, 100))
    ])

    moves_count = LazyAttribute(lambda obj: len(obj.moves))

    # Score and credits
    score = LazyAttribute(lambda obj: obj.current_state['score'] if obj.current_state else random.randint(0, 10000))
    credits_earned = LazyAttribute(lambda obj: int(obj.play_duration / 60000 * 2))  # 2 credits per minute

    # Achievements
    achievements_unlocked = LazyFunction(lambda: random.sample([
        'first_game', 'high_score', 'perfect_level', 'speed_run', 'collector',
        'explorer', 'survivor', 'strategist', 'champion'
    ], random.randint(0, 4)))

    # Statistics
    statistics = LazyFunction(lambda: {
        'total_clicks': random.randint(50, 500),
        'accuracy': round(random.uniform(0.6, 0.98), 2),
        'average_response_time': round(random.uniform(200, 800), 2),  # milliseconds
        'power_ups_used': random.randint(0, 10),
        'enemies_defeated': random.randint(0, 50),
        'items_collected': random.randint(5, 100)
    })

    # Timestamps
    created_at = LazyAttribute(lambda obj: obj.started_at)
    updated_at = LazyFunction(lambda: datetime.now(timezone.utc) - timedelta(
        seconds=random.randint(10, 300)
    ))

    # Session type traits
    class Params:
        active = factory.Trait(
            status='active',
            started_at=LazyFunction(lambda: datetime.now(timezone.utc) - timedelta(
                minutes=random.randint(5, 120)
            )),
            updated_at=LazyFunction(lambda: datetime.now(timezone.utc) - timedelta(
                seconds=random.randint(10, 300)
            )),
            ended_at=None,
            paused_at=None,
            last_sync_at=LazyFunction(lambda: datetime.now(timezone.utc) - timedelta(
                minutes=random.randint(1, 5)
            ))
        )

        completed = factory.Trait(
            status='completed',
            ended_at=LazyFunction(lambda: datetime.now(timezone.utc) - timedelta(
                hours=random.randint(1, 168)
            )),
            play_duration=LazyFunction(lambda: random.randint(60000, 3600000)),  # 1-60 minutes
            score=LazyFunction(lambda: random.randint(1000, 50000)),
            achievements_unlocked=LazyFunction(lambda: random.sample([
                'game_completed', 'high_score', 'perfect_score', 'speed_runner'
            ], random.randint(1, 3)))
        )

        paused = factory.Trait(
            status='paused',
            paused_at=LazyFunction(lambda: datetime.now(timezone.utc) - timedelta(
                minutes=random.randint(5, 480)  # 5 minutes to 8 hours ago
            )),
            ended_at=None
        )

        abandoned = factory.Trait(
            status='abandoned',
            play_duration=LazyFunction(lambda: random.randint(10000, 300000)),  # 10s to 5min
            score=LazyFunction(lambda: random.randint(0, 1000)),  # Low score
            achievements_unlocked=[],
            ended_at=LazyFunction(lambda: datetime.now(timezone.utc) - timedelta(
                hours=random.randint(1, 48)
            ))
        )

        high_score = factory.Trait(
            status='completed',
            score=LazyFunction(lambda: random.randint(8000, 50000)),
            play_duration=LazyFunction(lambda: random.randint(1800000, 3600000)),  # 30-60 min
            achievements_unlocked=LazyFunction(lambda: [
                'high_score', 'perfect_game', 'champion', 'legendary'
            ]),
            statistics=LazyFunction(lambda: {
                'total_clicks': random.randint(200, 1000),
                'accuracy': round(random.uniform(0.85, 0.99), 2),
                'average_response_time': round(random.uniform(150, 400), 2),
                'power_ups_used': random.randint(5, 20),
                'enemies_defeated': random.randint(20, 100),
                'items_collected': random.randint(50, 200)
            })
        )

        cross_device = factory.Trait(
            sync_version=LazyFunction(lambda: random.randint(5, 20)),
            last_sync_at=LazyFunction(lambda: datetime.now(timezone.utc) - timedelta(
                minutes=random.randint(1, 30)
            )),
            device_info=LazyFunction(lambda: fake.device_info(
                device_type=random.choice(['desktop', 'mobile', 'tablet'])
            ))
        )

    @classmethod
    def create_user_sessions(cls, user_id: str, count: int = 5, **kwargs) -> List[Dict[str, Any]]:
        """Create multiple sessions for a single user"""
        sessions = []
        game_ids = [str(fake.mongodb_object_id()) for _ in range(min(count, 3))]

        for i in range(count):
            game_id = random.choice(game_ids)  # User plays multiple games
            session = cls.build(user_id=user_id, game_id=game_id, **kwargs)
            sessions.append(session)

        return sessions

    @classmethod
    def create_cross_device_sessions(cls, user_id: str, count: int = 3, **kwargs) -> List[Dict[str, Any]]:
        """Create sessions for the same user across different devices"""
        devices = ['desktop', 'mobile', 'tablet']
        sessions = []

        for i in range(count):
            device_type = devices[i % len(devices)]
            session = cls.build(
                user_id=user_id,
                cross_device=True,
                device_info=fake.device_info(device_type=device_type),
                sync_version=i + 1,
                **kwargs
            )
            sessions.append(session)

        return sessions

    @classmethod
    def create_game_sessions(cls, game_id: str, count: int = 10, **kwargs) -> List[Dict[str, Any]]:
        """Create multiple sessions for a single game"""
        return cls.build_batch(count, game_id=game_id, **kwargs)


# Legacy compatibility wrappers
class LegacyGameFactory:
    """Legacy wrapper for backward compatibility with existing tests"""

    def __init__(self, test_utils=None):
        pass

    def create(self, **overrides):
        return GameFactory.build(**overrides)

    def create_batch(self, count: int, **base_overrides):
        return GameFactory.build_batch(count, **base_overrides)

    def create_puzzle_game(self, **overrides):
        return GameFactory.build(puzzle=True, **overrides)

    def create_multiplayer_game(self, **overrides):
        return GameFactory.build(multiplayer=True, **overrides)

    def create_quick_game(self, **overrides):
        return GameFactory.build(quick_play=True, **overrides)

    def create_by_category(self, category: str, count: int = 1):
        return GameFactory.create_by_category(category, count)


class LegacyGameSessionFactory:
    """Legacy wrapper for GameSession factory"""

    def __init__(self, test_utils=None):
        pass

    def create(self, **overrides):
        return GameSessionFactory.build(**overrides)

    def create_batch(self, count: int, **base_overrides):
        return GameSessionFactory.build_batch(count, **base_overrides)

    def create_active_session(self, **overrides):
        return GameSessionFactory.build(active=True, **overrides)

    def create_completed_session(self, **overrides):
        return GameSessionFactory.build(completed=True, **overrides)

    def create_paused_session(self, **overrides):
        return GameSessionFactory.build(paused=True, **overrides)

    def create_high_score_session(self, **overrides):
        return GameSessionFactory.build(high_score=True, **overrides)

    def create_cross_device_sessions(self, user_id: str, count: int = 3):
        return GameSessionFactory.create_cross_device_sessions(user_id, count)

    def create_sessions_for_user(self, user_id: str, count: int = 5):
        return GameSessionFactory.create_user_sessions(user_id, count)


# Backward compatibility
GameFactoryLegacy = LegacyGameFactory
GameSessionFactoryLegacy = LegacyGameSessionFactory