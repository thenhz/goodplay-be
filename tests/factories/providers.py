"""
Custom Faker providers for GoodPlay-specific test data generation

These providers extend Faker with domain-specific data generation
for realistic and consistent test objects across the GoodPlay platform.
"""
import random
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple
from faker import Faker
from faker.providers import BaseProvider

# Initialize faker for internal use
fake = Faker()


class GoodPlayBaseProvider(BaseProvider):
    """Base provider for GoodPlay-specific data with shared functionality"""

    @classmethod
    def weighted_choice(cls, choices: Dict[str, int]) -> str:
        """Make weighted random choice from dictionary of choices and weights"""
        items = list(choices.keys())
        weights = list(choices.values())
        return random.choices(items, weights=weights)[0]


class UserDataProvider(GoodPlayBaseProvider):
    """Provider for user-related data generation"""

    # Real-world name distributions
    first_names_male = [
        'Alex', 'Jordan', 'Taylor', 'Morgan', 'Riley', 'Casey', 'Avery',
        'Cameron', 'Quinn', 'Sage', 'River', 'Phoenix', 'Rowan', 'Skylar'
    ]

    first_names_female = [
        'Luna', 'Aria', 'Nova', 'Zoe', 'Maya', 'Chloe', 'Emma', 'Olivia',
        'Sophia', 'Isabella', 'Ava', 'Mia', 'Charlotte', 'Amelia'
    ]

    last_names = [
        'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller',
        'Davis', 'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez',
        'Wilson', 'Anderson', 'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin',
        'Lee', 'Perez', 'Thompson', 'White', 'Harris', 'Sanchez', 'Clark'
    ]

    # Realistic country distribution (top gaming countries)
    countries = {
        'US': 25, 'CA': 8, 'GB': 10, 'AU': 5, 'DE': 12, 'FR': 8, 'IT': 6,
        'ES': 6, 'BR': 7, 'MX': 4, 'JP': 8, 'KR': 5, 'IN': 6, 'CN': 4,
        'RU': 3, 'NL': 4, 'SE': 2, 'NO': 2, 'FI': 2, 'DK': 2
    }

    timezones = [
        'America/New_York', 'America/Los_Angeles', 'America/Chicago', 'America/Denver',
        'Europe/London', 'Europe/Paris', 'Europe/Berlin', 'Europe/Rome',
        'Europe/Madrid', 'Europe/Amsterdam', 'Europe/Stockholm',
        'Asia/Tokyo', 'Asia/Seoul', 'Asia/Shanghai', 'Asia/Kolkata',
        'Australia/Sydney', 'Australia/Melbourne', 'America/Sao_Paulo'
    ]

    user_bios = [
        "Gaming enthusiast who loves puzzles and strategy games.",
        "Casual player looking to make friends and have fun!",
        "Competitive gamer always seeking the next challenge.",
        "Playing games to relax after work and help good causes.",
        "New to GoodPlay but excited to contribute to charity while gaming!",
        "Puzzle solver by day, team player by night.",
        "Here to enjoy games and make a positive impact.",
        "Strategy game lover with a passion for helping others.",
        "Love connecting with people through gaming for good.",
        "Dedicated to making gaming a force for positive change."
    ]

    def user_first_name(self, gender: Optional[str] = None) -> str:
        """Generate realistic first name with optional gender preference"""
        if gender == 'male':
            return random.choice(self.first_names_male)
        elif gender == 'female':
            return random.choice(self.first_names_female)
        else:
            all_names = self.first_names_male + self.first_names_female
            return random.choice(all_names)

    def user_last_name(self) -> str:
        """Generate realistic last name"""
        return random.choice(self.last_names)

    def user_country(self) -> str:
        """Generate weighted country code based on gaming demographics"""
        return self.weighted_choice(self.countries)

    def user_timezone(self) -> str:
        """Generate realistic timezone"""
        return random.choice(self.timezones)

    def user_bio(self) -> str:
        """Generate realistic user bio"""
        return random.choice(self.user_bios)

    def user_avatar_url(self, style: str = None) -> str:
        """Generate mock avatar URL using DiceBear API"""
        styles = ['adventurer', 'avataaars', 'bottts', 'croodles', 'personas', 'pixel-art']
        if style is None:
            style = random.choice(styles)

        seed = fake.uuid4()[:10]
        return f"https://api.dicebear.com/7.x/{style}/svg?seed={seed}"

    def phone_number_realistic(self) -> Optional[str]:
        """Generate realistic phone number or None (not all users have phones)"""
        if random.random() < 0.7:  # 70% of users have phone numbers
            return fake.phone_number()
        return None

    def gaming_stats(self, veteran: bool = False) -> Dict[str, Any]:
        """Generate realistic gaming statistics"""
        if veteran:
            return {
                'total_play_time': random.randint(100000, 500000),  # milliseconds
                'games_played': random.randint(500, 2000),
                'favorite_category': random.choice(['puzzle', 'strategy', 'action', 'adventure']),
                'last_activity': datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 48)),
                'average_session_length': random.randint(600, 3600),  # seconds
                'achievements_unlocked': random.randint(50, 200),
                'high_scores': random.randint(20, 100)
            }
        else:
            return {
                'total_play_time': random.randint(1000, 50000),
                'games_played': random.randint(1, 100),
                'favorite_category': random.choice(['puzzle', 'strategy', 'action', 'adventure']) if random.random() > 0.3 else None,
                'last_activity': datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 168)) if random.random() > 0.2 else None,
                'average_session_length': random.randint(180, 1800),
                'achievements_unlocked': random.randint(0, 25),
                'high_scores': random.randint(0, 10)
            }

    def user_age_range(self) -> Tuple[int, str]:
        """Generate age and corresponding birth date"""
        # Realistic age distribution for gamers
        age_weights = {
            (13, 17): 10,  # Teen
            (18, 24): 25,  # Young adult
            (25, 34): 35,  # Prime gaming age
            (35, 44): 20,  # Adult
            (45, 54): 8,   # Middle-aged
            (55, 80): 2    # Senior
        }

        # Weighted random selection of age range
        ranges = list(age_weights.keys())
        weights = list(age_weights.values())
        min_age, max_age = random.choices(ranges, weights=weights)[0]

        age = random.randint(min_age, max_age)
        birth_date = datetime.now(timezone.utc) - timedelta(days=age * 365)

        return age, birth_date.strftime('%Y-%m-%d')


class GameDataProvider(GoodPlayBaseProvider):
    """Provider for game-related data generation"""

    # Realistic game name components
    game_adjectives = [
        'Amazing', 'Epic', 'Super', 'Mega', 'Ultimate', 'Fantastic', 'Incredible',
        'Awesome', 'Legendary', 'Mysterious', 'Magical', 'Crystal', 'Golden',
        'Silver', 'Diamond', 'Rainbow', 'Cosmic', 'Digital', 'Neon', 'Retro'
    ]

    game_nouns = [
        'Quest', 'Adventure', 'Challenge', 'Puzzle', 'Mystery', 'Journey',
        'Battle', 'War', 'Kingdom', 'Empire', 'World', 'Land', 'Realm',
        'Galaxy', 'Universe', 'Tower', 'Castle', 'Fortress', 'Temple', 'Maze',
        'Arena', 'Lab', 'Factory', 'Station', 'Portal', 'Dimension'
    ]

    game_suffixes = [
        '', ' Game', ' Challenge', ' Quest', ' Adventure', ' Pro', ' Deluxe',
        ' Premium', ' HD', ' 2D', ' 3D', ' VR', ' Mobile', ' Online', ' Plus'
    ]

    # Game categories with realistic weights
    categories = {
        'puzzle': 30, 'strategy': 25, 'action': 20, 'adventure': 15,
        'simulation': 5, 'party': 5, 'trivia': 8, 'word': 7, 'math': 6, 'memory': 9
    }

    # Game descriptions by category
    descriptions = {
        'puzzle': [
            "Challenge your mind with increasingly complex puzzles.",
            "Solve intricate brain teasers in beautiful environments.",
            "Test your logic skills with unique puzzle mechanics.",
            "A relaxing puzzle experience with stunning visuals."
        ],
        'strategy': [
            "Plan your moves carefully in this tactical challenge.",
            "Build, manage, and conquer in this strategic adventure.",
            "Outsmart your opponents with clever strategy.",
            "Deep strategic gameplay meets beautiful design."
        ],
        'action': [
            "Fast-paced action meets precise controls.",
            "Adrenaline-pumping gameplay with stunning effects.",
            "Test your reflexes in this action-packed adventure.",
            "Non-stop action with challenging boss battles."
        ],
        'adventure': [
            "Explore vast worlds filled with secrets and treasures.",
            "Embark on an epic journey across mystical lands.",
            "Discover hidden stories in this immersive adventure.",
            "A captivating tale of heroism and discovery."
        ]
    }

    # Game tags by category
    tags = {
        'puzzle': ['brain-training', 'logic', 'relaxing', 'single-player', 'casual'],
        'strategy': ['tactical', 'thinking', 'planning', 'competitive', 'turn-based'],
        'action': ['fast-paced', 'reflexes', 'combat', 'arcade', 'challenging'],
        'adventure': ['story', 'exploration', 'immersive', 'quest', 'discovery'],
        'simulation': ['realistic', 'management', 'building', 'educational'],
        'party': ['multiplayer', 'social', 'fun', 'family-friendly', 'cooperative']
    }

    def game_name(self) -> str:
        """Generate realistic game name"""
        adjective = random.choice(self.game_adjectives)
        noun = random.choice(self.game_nouns)
        suffix = random.choice(self.game_suffixes)
        return f"{adjective} {noun}{suffix}"

    def game_category(self) -> str:
        """Generate weighted game category"""
        return self.weighted_choice(self.categories)

    def game_description(self, category: str) -> str:
        """Generate description appropriate for game category"""
        category_descriptions = self.descriptions.get(category, self.descriptions['puzzle'])
        return random.choice(category_descriptions)

    def game_tags(self, category: str, count: Optional[int] = None) -> List[str]:
        """Generate tags appropriate for game category"""
        if count is None:
            count = random.randint(2, 5)

        category_tags = self.tags.get(category, self.tags['puzzle'])
        common_tags = ['casual', 'single-player', 'multiplayer', 'educational', 'family-friendly']

        # Mix category-specific tags with common ones
        available_tags = category_tags + random.sample(common_tags, 2)
        return random.sample(available_tags, min(count, len(available_tags)))

    def game_difficulty(self) -> str:
        """Generate weighted game difficulty"""
        difficulties = {'easy': 30, 'medium': 50, 'hard': 20}
        return self.weighted_choice(difficulties)

    def game_version(self) -> str:
        """Generate realistic version number"""
        major = random.randint(1, 5)
        minor = random.randint(0, 9)
        patch = random.randint(0, 9)
        return f"{major}.{minor}.{patch}"

    def game_rating(self) -> float:
        """Generate realistic game rating (3.0-5.0 range, weighted toward higher)"""
        # Weight toward higher ratings (most games are decent)
        ratings = [3.0, 3.5, 4.0, 4.5, 5.0]
        weights = [5, 15, 35, 30, 15]
        base_rating = random.choices(ratings, weights=weights)[0]

        # Add small random variation
        variation = random.uniform(-0.2, 0.2)
        final_rating = max(1.0, min(5.0, base_rating + variation))

        return round(final_rating, 1)

    def game_duration_minutes(self, category: str) -> int:
        """Generate realistic game duration based on category"""
        duration_ranges = {
            'puzzle': (5, 30),
            'strategy': (20, 90),
            'action': (10, 45),
            'adventure': (30, 120),
            'simulation': (30, 180),
            'party': (10, 60)
        }

        min_duration, max_duration = duration_ranges.get(category, (10, 30))
        return random.randint(min_duration, max_duration)

    def game_player_count(self, category: str) -> Tuple[int, int]:
        """Generate realistic min/max player count based on category"""
        player_ranges = {
            'puzzle': (1, 1),
            'strategy': (1, random.choice([2, 4, 6])),
            'action': (1, random.choice([1, 2, 4, 8])),
            'adventure': (1, random.choice([1, 2, 4])),
            'simulation': (1, random.choice([1, 2, 4])),
            'party': (2, random.choice([4, 6, 8, 10]))
        }

        min_players, max_players = player_ranges.get(category, (1, 1))
        return min_players, max_players


class SocialDataProvider(GoodPlayBaseProvider):
    """Provider for social and achievement-related data"""

    achievement_names = {
        'gaming': [
            "First Steps", "Game Master", "Speed Runner", "Perfect Score",
            "Dedicated Player", "Game Explorer", "Challenge Accepted",
            "High Achiever", "Gaming Legend", "Ultimate Champion"
        ],
        'social': [
            "Friend Maker", "Community Builder", "Social Butterfly", "Team Player",
            "Helpful Friend", "Connector", "Social Star", "Network Builder",
            "People Person", "Community Champion"
        ],
        'impact': [
            "Good Deed", "Generous Heart", "Impact Maker", "Change Agent",
            "Charitable Soul", "World Changer", "Donation Hero", "Impact Champion",
            "Philanthropist", "Global Citizen"
        ]
    }

    achievement_descriptions = {
        'gaming': [
            "Complete your first game session",
            "Master multiple game categories",
            "Achieve a perfect score in any game",
            "Play for 100 hours total",
            "Complete 50 different games"
        ],
        'social': [
            "Make your first friend on GoodPlay",
            "Help 10 other players",
            "Join a community challenge",
            "Share your achievements",
            "Build a network of 25 friends"
        ],
        'impact': [
            "Make your first donation",
            "Donate to 5 different causes",
            "Raise $100 for charity through gaming",
            "Participate in a charity tournament",
            "Make donations for 30 consecutive days"
        ]
    }

    badge_icons = [
        "🏆", "🥇", "🏅", "⭐", "💎", "👑", "🎯", "🚀", "💡", "🌟",
        "🔥", "⚡", "🎪", "🎊", "🎉", "🌈", "🦄", "👑", "💫", "✨"
    ]

    def achievement_name(self, category: str) -> str:
        """Generate achievement name for category"""
        names = self.achievement_names.get(category, self.achievement_names['gaming'])
        return random.choice(names)

    def achievement_description(self, category: str) -> str:
        """Generate achievement description for category"""
        descriptions = self.achievement_descriptions.get(category, self.achievement_descriptions['gaming'])
        return random.choice(descriptions)

    def badge_icon(self) -> str:
        """Generate badge icon emoji"""
        return random.choice(self.badge_icons)

    def achievement_trigger_conditions(self, trigger_type: str) -> Dict[str, Any]:
        """Generate realistic trigger conditions for achievements"""
        conditions = {'type': trigger_type}

        if trigger_type == 'game_session':
            conditions['target_value'] = random.choice([1, 5, 10, 25, 50, 100])
        elif trigger_type == 'game_score':
            conditions.update({
                'target_value': random.choice([1000, 5000, 10000, 25000, 50000]),
                'comparison': random.choice(['gte', 'eq'])
            })
        elif trigger_type == 'social_friend':
            conditions['target_value'] = random.choice([1, 5, 10, 25, 50])
        elif trigger_type == 'donation_amount':
            conditions['target_value'] = random.choice([10, 50, 100, 500, 1000])
        elif trigger_type == 'consecutive_days':
            conditions['target_value'] = random.choice([3, 7, 14, 30, 90])

        return conditions


class FinancialDataProvider(GoodPlayBaseProvider):
    """Provider for financial and donation-related data"""

    transaction_types = ['earned', 'donated', 'bonus', 'refund', 'adjustment']

    onlus_names = [
        "Education First Foundation", "Green Earth Initiative", "Health for All",
        "Children's Future Fund", "Animal Rescue Network", "Clean Water Project",
        "Global Education Alliance", "Wildlife Conservation Trust", "Community Health Center",
        "Emergency Relief Fund", "Research Innovation Lab", "Youth Development Program"
    ]

    campaign_titles = [
        "Back to School Supply Drive", "Clean Water for Villages", "Emergency Disaster Relief",
        "Wildlife Habitat Protection", "Community Health Initiative", "Education Technology Fund",
        "Food Security Program", "Environmental Restoration", "Medical Research Support",
        "Youth Empowerment Project", "Senior Care Initiative", "Mental Health Awareness"
    ]

    def transaction_type(self) -> str:
        """Generate transaction type"""
        return random.choice(self.transaction_types)

    def onlus_name(self) -> str:
        """Generate realistic ONLUS organization name"""
        return random.choice(self.onlus_names)

    def campaign_title(self) -> str:
        """Generate realistic campaign title"""
        return random.choice(self.campaign_titles)

    def donation_amount(self, user_type: str = 'regular') -> float:
        """Generate realistic donation amount based on user type"""
        if user_type == 'veteran':
            return round(random.uniform(25, 500), 2)
        elif user_type == 'admin':
            return round(random.uniform(100, 1000), 2)
        else:
            return round(random.uniform(5, 100), 2)

    def transaction_amount(self, transaction_type: str) -> float:
        """Generate realistic transaction amount based on type"""
        if transaction_type == 'earned':
            return round(random.uniform(1, 50), 2)
        elif transaction_type == 'donated':
            return round(random.uniform(5, 200), 2)
        elif transaction_type == 'bonus':
            return round(random.uniform(10, 100), 2)
        else:
            return round(random.uniform(1, 25), 2)