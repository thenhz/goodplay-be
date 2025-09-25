"""
Social Factory Module

Factory-Boy implementations for generating Social domain objects
including achievements, badges, relationships, and leaderboards with
realistic data and proper relationships.
"""
import random
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
import factory
from factory import LazyFunction, LazyAttribute, Sequence, Trait, SubFactory
from faker import Faker

# Import our custom providers and base classes
from tests.factories.base import MongoFactory, TimestampMixin, fake
from tests.factories.providers import SocialDataProvider
from tests.factories.base import AchievementProvider

# Register our custom providers
fake.add_provider(SocialDataProvider)
fake.add_provider(AchievementProvider)


class AchievementFactory(MongoFactory):
    """Factory-Boy factory for creating Achievement objects

    Supports all achievement categories and rarities with realistic
    trigger conditions and reward systems.

    Usage:
        achievement = AchievementFactory()  # Basic achievement
        gaming = AchievementFactory(gaming=True)  # Gaming achievement
        rare = AchievementFactory(rare=True)  # Rare achievement
        batch = AchievementFactory.build_batch(10)  # Batch creation
    """

    class Meta:
        model = dict

    # Basic achievement information
    achievement_id = Sequence(lambda n: f'achievement_{n}_{fake.uuid4()[:8]}')
    name = LazyAttribute(lambda obj: fake.achievement_name(obj.category))
    description = LazyAttribute(lambda obj: fake.achievement_description(obj.category))

    # Achievement classification
    category = LazyFunction(fake.achievement_category)
    badge_rarity = LazyFunction(fake.achievement_rarity)

    # Trigger conditions
    trigger_conditions = LazyAttribute(lambda obj: fake.achievement_trigger_conditions(
        obj.trigger_conditions.get('type', 'game_session') if hasattr(obj, 'trigger_conditions') and obj.trigger_conditions else 'game_session'
    ))

    # Rewards
    reward_credits = LazyAttribute(lambda obj: {
        'common': random.randint(5, 25),
        'rare': random.randint(25, 75),
        'epic': random.randint(75, 200),
        'legendary': random.randint(200, 500)
    }.get(obj.badge_rarity, 10))

    # Visual representation
    icon_url = LazyFunction(lambda: f"https://cdn.goodplay.test/achievements/{fake.uuid4()[:8]}.svg")

    # Status
    is_active = LazyFunction(lambda: random.choice([True, True, True, False]))  # 75% active

    # Achievement category traits
    class Params:
        gaming = factory.Trait(
            category='gaming',
            trigger_conditions=LazyFunction(lambda: fake.achievement_trigger_conditions(
                random.choice(['game_session', 'game_score', 'game_diversity'])
            )),
            name=LazyFunction(lambda: fake.achievement_name('gaming')),
            description=LazyFunction(lambda: fake.achievement_description('gaming'))
        )

        social = factory.Trait(
            category='social',
            trigger_conditions=LazyFunction(lambda: fake.achievement_trigger_conditions(
                random.choice(['social_friend', 'social_like', 'help_provided'])
            )),
            name=LazyFunction(lambda: fake.achievement_name('social')),
            description=LazyFunction(lambda: fake.achievement_description('social'))
        )

        impact = factory.Trait(
            category='impact',
            trigger_conditions=LazyFunction(lambda: fake.achievement_trigger_conditions(
                random.choice(['donation_amount', 'donation_count', 'monthly_donation_streak'])
            )),
            name=LazyFunction(lambda: fake.achievement_name('impact')),
            description=LazyFunction(lambda: fake.achievement_description('impact'))
        )

        # Rarity traits
        common = factory.Trait(
            badge_rarity='common',
            reward_credits=LazyFunction(lambda: random.randint(5, 25))
        )

        rare = factory.Trait(
            badge_rarity='rare',
            reward_credits=LazyFunction(lambda: random.randint(25, 75)),
            trigger_conditions=LazyFunction(lambda: {
                'type': random.choice(['game_score', 'consecutive_days', 'tournament_victory']),
                'target_value': random.choice([5000, 7, 1])  # Higher thresholds for rare
            })
        )

        epic = factory.Trait(
            badge_rarity='epic',
            reward_credits=LazyFunction(lambda: random.randint(75, 200)),
            trigger_conditions=LazyFunction(lambda: {
                'type': random.choice(['game_score', 'donation_amount', 'game_diversity']),
                'target_value': random.choice([25000, 500, 10])  # Even higher thresholds
            })
        )

        legendary = factory.Trait(
            badge_rarity='legendary',
            reward_credits=LazyFunction(lambda: random.randint(200, 500)),
            trigger_conditions=LazyFunction(lambda: {
                'type': random.choice(['game_score', 'donation_amount', 'consecutive_days']),
                'target_value': random.choice([100000, 2000, 365])  # Legendary thresholds
            })
        )

    @classmethod
    def create_achievement_set(cls, category: str, count: int = 5) -> List[Dict[str, Any]]:
        """Create a set of achievements for a specific category with varied rarities"""
        achievements = []

        # Distribution: 40% common, 30% rare, 20% epic, 10% legendary
        rarity_weights = [0.4, 0.3, 0.2, 0.1]
        rarities = ['common', 'rare', 'epic', 'legendary']

        for i in range(count):
            rarity = random.choices(rarities, weights=rarity_weights)[0]
            trait_kwargs = {category: True, rarity: True}
            achievement = cls.build(**trait_kwargs)
            achievements.append(achievement)

        return achievements

    @classmethod
    def create_complete_achievement_system(cls) -> Dict[str, List[Dict[str, Any]]]:
        """Create a complete achievement system with all categories"""
        return {
            'gaming': cls.create_achievement_set('gaming', 8),
            'social': cls.create_achievement_set('social', 6),
            'impact': cls.create_achievement_set('impact', 6)
        }


class BadgeFactory(MongoFactory):
    """Factory-Boy factory for creating Badge objects

    Creates badge definitions that are awarded when achievements are unlocked.
    """

    class Meta:
        model = dict

    badge_id = Sequence(lambda n: f'badge_{n}_{fake.uuid4()[:8]}')
    name = LazyFunction(lambda: f"{random.choice(['Gold', 'Silver', 'Bronze', 'Platinum', 'Diamond'])} {fake.word().title()}")
    description = LazyFunction(lambda: f"Awarded for {fake.sentence()[:-1].lower()}")

    # Visual properties
    icon_emoji = LazyFunction(fake.badge_icon)
    color = LazyFunction(lambda: random.choice(['#FFD700', '#C0C0C0', '#CD7F32', '#E5E4E2', '#B9F2FF']))

    # Badge rarity
    rarity = LazyFunction(fake.achievement_rarity)

    # Badge value
    points_value = LazyAttribute(lambda obj: {
        'common': random.randint(10, 50),
        'rare': random.randint(50, 150),
        'epic': random.randint(150, 400),
        'legendary': random.randint(400, 1000)
    }.get(obj.rarity, 25))


class UserAchievementFactory(MongoFactory):
    """Factory-Boy factory for creating UserAchievement objects

    Represents the relationship between users and their unlocked achievements.
    """

    class Meta:
        model = dict

    user_id = LazyFunction(lambda: str(fake.mongodb_object_id()))
    achievement_id = LazyFunction(lambda: str(fake.mongodb_object_id()))

    # Progress tracking
    progress = LazyFunction(lambda: random.randint(0, 100))
    is_completed = LazyAttribute(lambda obj: obj.progress >= 100)
    completion_date = LazyAttribute(lambda obj:
        fake.date_time_between(start_date='-30d', end_date='now') if obj.is_completed else None
    )

    # Achievement details at unlock time
    achievement_snapshot = LazyFunction(lambda: {
        'name': fake.achievement_name('gaming'),
        'category': fake.achievement_category(),
        'rarity': fake.achievement_rarity(),
        'reward_credits': random.randint(10, 100)
    })

    # Notification status
    notification_sent = LazyAttribute(lambda obj: obj.is_completed and random.choice([True, False]))

    class Params:
        completed = factory.Trait(
            progress=100,
            is_completed=True,
            completion_date=LazyFunction(lambda: fake.date_time_between(start_date='-30d', end_date='now')),
            notification_sent=True
        )

        in_progress = factory.Trait(
            progress=LazyFunction(lambda: random.randint(10, 90)),
            is_completed=False,
            completion_date=None,
            notification_sent=False
        )


class UserRelationshipFactory(MongoFactory):
    """Factory-Boy factory for creating UserRelationship objects

    Manages friend relationships and social connections between users.
    """

    class Meta:
        model = dict

    user_id = LazyFunction(lambda: str(fake.mongodb_object_id()))
    friend_id = LazyFunction(lambda: str(fake.mongodb_object_id()))

    # Relationship status
    status = LazyFunction(lambda: random.choices(
        ['pending', 'accepted', 'blocked', 'declined'],
        weights=[20, 70, 5, 5]  # Most relationships are accepted
    )[0])

    # Timestamps
    created_at = LazyFunction(lambda: fake.date_time_between(start_date='-1y', end_date='now'))
    updated_at = LazyAttribute(lambda obj: obj.created_at + timedelta(
        hours=random.randint(0, 72) if obj.status != 'pending' else 0
    ))

    # Interaction tracking
    interactions_count = LazyFunction(lambda: random.randint(0, 100))
    last_interaction = LazyFunction(lambda: fake.date_time_between(start_date='-30d', end_date='now'))

    # Relationship metadata
    relationship_strength = LazyFunction(lambda: round(random.uniform(0.1, 1.0), 2))
    mutual_games_played = LazyFunction(lambda: random.randint(0, 20))

    class Params:
        friends = factory.Trait(
            status='accepted',
            interactions_count=LazyFunction(lambda: random.randint(10, 100)),
            relationship_strength=LazyFunction(lambda: round(random.uniform(0.5, 1.0), 2)),
            mutual_games_played=LazyFunction(lambda: random.randint(1, 20))
        )

        pending = factory.Trait(
            status='pending',
            interactions_count=0,
            relationship_strength=0.0,
            mutual_games_played=0,
            last_interaction=None
        )

    @classmethod
    def create_friend_network(cls, user_id: str, friend_count: int = 5) -> List[Dict[str, Any]]:
        """Create a network of friends for a specific user"""
        return cls.build_batch(friend_count, user_id=user_id, friends=True)

    @classmethod
    def create_mutual_friendship(cls, user_id_1: str, user_id_2: str) -> List[Dict[str, Any]]:
        """Create mutual friendship between two users"""
        return [
            cls.build(user_id=user_id_1, friend_id=user_id_2, friends=True),
            cls.build(user_id=user_id_2, friend_id=user_id_1, friends=True)
        ]


class LeaderboardFactory(MongoFactory):
    """Factory-Boy factory for creating Leaderboard objects

    Creates different types of leaderboards for various competition aspects.
    """

    class Meta:
        model = dict

    leaderboard_id = Sequence(lambda n: f'leaderboard_{n}_{fake.uuid4()[:8]}')
    name = LazyFunction(lambda: random.choice([
        'Weekly High Scores', 'Monthly Donations', 'All-Time Champions',
        'Social Butterflies', 'Puzzle Masters', 'Strategy Legends',
        'Speed Demons', 'Charitable Hearts', 'Game Explorers'
    ]))

    description = LazyFunction(lambda: fake.sentence())

    # Leaderboard type and scope
    type = LazyFunction(lambda: random.choice([
        'global', 'friends', 'regional', 'game_specific', 'category_specific'
    ]))

    category = LazyFunction(lambda: random.choice([
        'total_score', 'donations', 'achievements', 'games_played',
        'social_interactions', 'puzzle_score', 'strategy_score'
    ]))

    # Time scope
    time_period = LazyFunction(lambda: random.choice([
        'daily', 'weekly', 'monthly', 'yearly', 'all_time'
    ]))

    # Configuration
    max_entries = LazyFunction(lambda: random.choice([10, 25, 50, 100]))
    is_active = True

    # Dates
    start_date = LazyFunction(lambda: fake.date_time_between(start_date='-3m', end_date='-1m'))
    end_date = LazyAttribute(lambda obj: obj.start_date + timedelta(
        days={'daily': 1, 'weekly': 7, 'monthly': 30, 'yearly': 365}.get(obj.time_period, 30)
    ))

    # Prizes
    prizes = LazyFunction(lambda: {
        'first': {'credits': random.randint(100, 500), 'badge': 'gold_medal'},
        'second': {'credits': random.randint(50, 250), 'badge': 'silver_medal'},
        'third': {'credits': random.randint(25, 125), 'badge': 'bronze_medal'},
        'participation': {'credits': random.randint(5, 25)}
    })

    class Params:
        global_leaderboard = factory.Trait(
            type='global',
            max_entries=100,
            prizes=LazyFunction(lambda: {
                'first': {'credits': 500, 'badge': 'world_champion'},
                'second': {'credits': 300, 'badge': 'global_runner_up'},
                'third': {'credits': 200, 'badge': 'global_third'},
                'top_10': {'credits': 50}
            })
        )

        friends_leaderboard = factory.Trait(
            type='friends',
            max_entries=25,
            prizes=LazyFunction(lambda: {
                'first': {'credits': 100, 'badge': 'friend_champion'},
                'second': {'credits': 50, 'badge': 'friend_runner_up'},
                'third': {'credits': 25, 'badge': 'friend_third'}
            })
        )


class LeaderboardEntryFactory(MongoFactory):
    """Factory-Boy factory for creating LeaderboardEntry objects

    Represents individual entries in leaderboards with scores and rankings.
    """

    class Meta:
        model = dict

    leaderboard_id = LazyFunction(lambda: str(fake.mongodb_object_id()))
    user_id = LazyFunction(lambda: str(fake.mongodb_object_id()))

    # Score and ranking
    score = LazyFunction(lambda: random.randint(100, 100000))
    rank = LazyFunction(lambda: random.randint(1, 100))
    previous_rank = LazyAttribute(lambda obj: obj.rank + random.randint(-5, 5) if obj.rank > 5 else obj.rank)

    # User snapshot at entry time
    user_snapshot = LazyFunction(lambda: {
        'username': fake.user_first_name(),
        'display_name': fake.user_first_name() + ' ' + fake.user_last_name(),
        'avatar_url': fake.user_avatar_url(),
        'country': fake.user_country()
    })

    # Entry metadata
    total_games_played = LazyFunction(lambda: random.randint(1, 1000))
    total_time_played = LazyFunction(lambda: random.randint(3600, 360000))  # 1 hour to 100 hours
    achievements_count = LazyFunction(lambda: random.randint(1, 50))

    # Timestamps
    first_entry_date = LazyFunction(lambda: fake.date_time_between(start_date='-1m', end_date='now'))
    last_updated = LazyFunction(lambda: fake.date_time_between(start_date='-7d', end_date='now'))

    class Params:
        top_player = factory.Trait(
            rank=LazyFunction(lambda: random.randint(1, 10)),
            score=LazyFunction(lambda: random.randint(50000, 100000)),
            total_games_played=LazyFunction(lambda: random.randint(500, 2000)),
            achievements_count=LazyFunction(lambda: random.randint(25, 100))
        )

        casual_player = factory.Trait(
            rank=LazyFunction(lambda: random.randint(50, 100)),
            score=LazyFunction(lambda: random.randint(100, 10000)),
            total_games_played=LazyFunction(lambda: random.randint(10, 100)),
            achievements_count=LazyFunction(lambda: random.randint(1, 20))
        )

    @classmethod
    def create_leaderboard_rankings(cls, leaderboard_id: str, entry_count: int = 10) -> List[Dict[str, Any]]:
        """Create a complete leaderboard with properly ranked entries"""
        entries = []

        for rank in range(1, entry_count + 1):
            # Score decreases with rank but with some randomness
            base_score = 100000 - (rank * 1000)
            score = base_score + random.randint(-500, 500)
            score = max(score, 100)  # Minimum score

            entry = cls.build(
                leaderboard_id=leaderboard_id,
                rank=rank,
                score=score,
                previous_rank=rank + random.randint(-3, 3) if rank > 3 else rank
            )
            entries.append(entry)

        return entries


class ImpactScoreFactory(MongoFactory):
    """Factory-Boy factory for creating ImpactScore objects

    Tracks user impact through donations and charitable activities.
    """

    class Meta:
        model = dict

    user_id = LazyFunction(lambda: str(fake.mongodb_object_id()))

    # Impact metrics
    total_donations = LazyFunction(lambda: round(random.uniform(0, 5000), 2))
    donation_count = LazyFunction(lambda: random.randint(0, 100))
    causes_supported = LazyFunction(lambda: random.randint(0, 10))

    # Impact score calculation
    impact_score = LazyAttribute(lambda obj: int(
        obj.total_donations * 2 + obj.donation_count * 5 + obj.causes_supported * 10
    ))

    # Streak tracking
    current_donation_streak = LazyFunction(lambda: random.randint(0, 365))
    longest_donation_streak = LazyAttribute(lambda obj: max(
        obj.current_donation_streak, random.randint(0, 500)
    ))

    # Monthly goals
    monthly_goal = LazyFunction(lambda: round(random.uniform(50, 500), 2))
    monthly_progress = LazyFunction(lambda: round(random.uniform(0, 600), 2))

    # Recognition level
    impact_level = LazyAttribute(lambda obj: {
        range(0, 100): 'Supporter',
        range(100, 500): 'Advocate',
        range(500, 1500): 'Champion',
        range(1500, 5000): 'Hero',
        range(5000, 999999): 'Legend'
    }[next(r for r in [range(0, 100), range(100, 500), range(500, 1500),
                       range(1500, 5000), range(5000, 999999)]
            if obj.impact_score in r)])

    # Timestamps
    first_donation_date = LazyFunction(lambda: fake.date_time_between(start_date='-2y', end_date='-1m'))
    last_donation_date = LazyFunction(lambda: fake.date_time_between(start_date='-1m', end_date='now'))

    class Params:
        high_impact = factory.Trait(
            total_donations=LazyFunction(lambda: round(random.uniform(1000, 10000), 2)),
            donation_count=LazyFunction(lambda: random.randint(50, 200)),
            causes_supported=LazyFunction(lambda: random.randint(5, 15)),
            current_donation_streak=LazyFunction(lambda: random.randint(30, 365)),
            monthly_goal=LazyFunction(lambda: round(random.uniform(200, 1000), 2))
        )

        new_donor = factory.Trait(
            total_donations=LazyFunction(lambda: round(random.uniform(5, 100), 2)),
            donation_count=LazyFunction(lambda: random.randint(1, 10)),
            causes_supported=LazyFunction(lambda: random.randint(1, 3)),
            current_donation_streak=LazyFunction(lambda: random.randint(1, 10)),
            first_donation_date=LazyFunction(lambda: fake.date_time_between(start_date='-30d', end_date='-1d'))
        )