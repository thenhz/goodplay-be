"""
Game Factory Module

Provides factory classes for generating Game, GameSession,
and related objects with realistic data and relationships.
"""
import random
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from tests.core import TestUtils


class GameFactory:
    """Factory for creating Game objects with realistic data"""

    def __init__(self, test_utils: TestUtils = None):
        self.test_utils = test_utils or TestUtils()
        self._counter = 0

    def create(self, **overrides) -> Dict[str, Any]:
        """Create a single game with optional overrides"""
        self._counter += 1

        defaults = {
            '_id': self.test_utils.get_unique_id(),
            'name': self._generate_game_name(),
            'description': self._generate_game_description(),
            'category': self._generate_category(),
            'difficulty': random.choice(['easy', 'medium', 'hard']),
            'min_players': random.choice([1, 1, 1, 2]),  # Weighted towards single player
            'max_players': random.randint(1, 8),
            'estimated_duration': random.choice([
                180, 300, 600, 900, 1200, 1800, 2400, 3600  # 3min to 1hour
            ]),
            'is_active': random.choice([True, True, True, False]),  # 75% active
            'created_at': datetime.now(timezone.utc) - timedelta(days=random.randint(1, 730)),
            'updated_at': datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 168)),
            'version': f"1.{random.randint(0, 9)}.{random.randint(0, 9)}",
            'rating': round(random.uniform(3.0, 5.0), 1),
            'play_count': random.randint(0, 100000),
            'tags': self._generate_tags(),
            'screenshots': self._generate_screenshots(),
            'instructions': self._generate_instructions()
        }

        # Ensure max_players >= min_players
        defaults['max_players'] = max(defaults['min_players'], defaults['max_players'])

        defaults.update(overrides)
        return defaults

    def create_batch(self, count: int, **base_overrides) -> List[Dict[str, Any]]:
        """Create multiple games with optional base overrides"""
        return [self.create(**base_overrides) for _ in range(count)]

    def create_puzzle_game(self, **overrides) -> Dict[str, Any]:
        """Create a puzzle game"""
        puzzle_defaults = {
            'category': 'puzzle',
            'min_players': 1,
            'max_players': 1,
            'difficulty': random.choice(['easy', 'medium', 'hard']),
            'estimated_duration': random.choice([300, 600, 900, 1200]),  # 5-20 minutes
            'tags': ['puzzle', 'single-player', 'brain-training']
        }
        puzzle_defaults.update(overrides)
        return self.create(**puzzle_defaults)

    def create_multiplayer_game(self, **overrides) -> Dict[str, Any]:
        """Create a multiplayer game"""
        multiplayer_defaults = {
            'min_players': random.randint(2, 4),
            'max_players': random.randint(4, 8),
            'category': random.choice(['strategy', 'action', 'party']),
            'estimated_duration': random.choice([900, 1800, 2400, 3600]),  # 15min-1hour
            'tags': ['multiplayer', 'competitive', 'social']
        }
        multiplayer_defaults.update(overrides)
        return self.create(**multiplayer_defaults)

    def create_quick_game(self, **overrides) -> Dict[str, Any]:
        """Create a quick game (under 5 minutes)"""
        quick_defaults = {
            'estimated_duration': random.choice([60, 120, 180, 240, 300]),  # 1-5 minutes
            'difficulty': random.choice(['easy', 'medium']),
            'tags': ['quick-play', 'casual', 'time-killer']
        }
        quick_defaults.update(overrides)
        return self.create(**quick_defaults)

    def create_by_category(self, category: str, count: int = 1) -> List[Dict[str, Any]]:
        """Create games of a specific category"""
        category_settings = {
            'puzzle': {
                'min_players': 1, 'max_players': 1,
                'estimated_duration': random.choice([300, 600, 900]),
                'tags': ['puzzle', 'brain-training', 'logic']
            },
            'strategy': {
                'min_players': random.randint(1, 2), 'max_players': random.randint(2, 6),
                'estimated_duration': random.choice([1200, 1800, 2400, 3600]),
                'tags': ['strategy', 'tactical', 'thinking']
            },
            'action': {
                'min_players': 1, 'max_players': random.randint(2, 8),
                'estimated_duration': random.choice([300, 600, 900, 1200]),
                'tags': ['action', 'fast-paced', 'reflexes']
            },
            'adventure': {
                'min_players': 1, 'max_players': random.randint(1, 4),
                'estimated_duration': random.choice([1800, 2400, 3600, 5400]),
                'tags': ['adventure', 'story', 'exploration']
            }
        }

        settings = category_settings.get(category, {})
        settings['category'] = category

        return self.create_batch(count, **settings)

    def _generate_game_name(self) -> str:
        """Generate a realistic game name"""
        adjectives = [
            'Amazing', 'Epic', 'Super', 'Mega', 'Ultimate', 'Fantastic',
            'Incredible', 'Awesome', 'Legendary', 'Mysterious', 'Magical',
            'Crystal', 'Golden', 'Silver', 'Diamond', 'Rainbow'
        ]

        nouns = [
            'Quest', 'Adventure', 'Challenge', 'Puzzle', 'Mystery',
            'Journey', 'Battle', 'War', 'Kingdom', 'Empire',
            'World', 'Land', 'Realm', 'Galaxy', 'Universe',
            'Tower', 'Castle', 'Fortress', 'Temple', 'Maze'
        ]

        suffixes = [
            '', ' Game', ' Challenge', ' Quest', ' Adventure',
            ' Pro', ' Deluxe', ' Premium', ' HD', ' 2D'
        ]

        adjective = random.choice(adjectives)
        noun = random.choice(nouns)
        suffix = random.choice(suffixes)

        return f"{adjective} {noun}{suffix}"

    def _generate_game_description(self) -> str:
        """Generate a game description"""
        descriptions = [
            "An engaging puzzle game that challenges your mind and reflexes.",
            "Strategic gameplay meets exciting adventure in this immersive experience.",
            "Test your skills against players worldwide in this competitive challenge.",
            "A relaxing yet stimulating game perfect for quick breaks or long sessions.",
            "Combine strategy and luck in this entertaining multiplayer experience.",
            "Solve increasingly complex puzzles in beautifully designed environments.",
            "Fast-paced action meets tactical decision-making in this unique game.",
            "Explore mysterious worlds while helping real charities with every play."
        ]
        return random.choice(descriptions)

    def _generate_category(self) -> str:
        """Generate a game category"""
        categories = ['puzzle', 'strategy', 'action', 'adventure', 'simulation', 'party']
        weights = [30, 25, 20, 15, 5, 5]  # Puzzle and strategy are more common
        return random.choices(categories, weights=weights)[0]

    def _generate_tags(self) -> List[str]:
        """Generate game tags"""
        all_tags = [
            'casual', 'hardcore', 'single-player', 'multiplayer', 'competitive',
            'cooperative', 'brain-training', 'relaxing', 'challenging', 'educational',
            'family-friendly', 'quick-play', 'time-killer', 'social', 'strategic',
            'tactical', 'puzzle', 'logic', 'math', 'word', 'trivia',
            'action', 'adventure', 'simulation', 'party', 'board-game'
        ]
        return random.sample(all_tags, random.randint(2, 5))

    def _generate_screenshots(self) -> List[str]:
        """Generate mock screenshot URLs"""
        count = random.randint(2, 6)
        screenshots = []
        for i in range(count):
            game_id = self.test_utils.generate_random_string(8)
            screenshots.append(f"https://cdn.goodplay.test/games/{game_id}/screenshot_{i+1}.png")
        return screenshots

    def _generate_instructions(self) -> str:
        """Generate game instructions"""
        instructions = [
            "Click or tap to interact with game elements. Follow the on-screen prompts to complete each level.",
            "Use arrow keys or swipe gestures to move. Collect items and avoid obstacles to progress.",
            "Match similar elements by clicking them. Create chains for bonus points and special effects.",
            "Plan your moves carefully. Each decision affects your score and available options.",
            "Work together with other players to achieve common goals and unlock achievements.",
            "Solve puzzles by dragging and dropping pieces into the correct positions.",
            "Time your actions perfectly to achieve the highest scores and beat other players.",
            "Explore the game world by clicking on interactive elements and discovering hidden secrets."
        ]
        return random.choice(instructions)


class GameSessionFactory:
    """Factory for creating GameSession objects with realistic data"""

    def __init__(self, test_utils: TestUtils = None):
        self.test_utils = test_utils or TestUtils()

    def create(self, **overrides) -> Dict[str, Any]:
        """Create a game session with optional overrides"""
        # Generate realistic session timing
        started_minutes_ago = random.randint(1, 1440)  # 1 minute to 24 hours ago
        started_at = datetime.now(timezone.utc) - timedelta(minutes=started_minutes_ago)

        # Determine session duration and status
        duration_ms = random.randint(30000, 3600000)  # 30 seconds to 1 hour
        status = random.choices(
            ['active', 'paused', 'completed', 'abandoned'],
            weights=[20, 10, 60, 10]  # Most sessions are completed
        )[0]

        defaults = {
            '_id': self.test_utils.get_unique_id(),
            'user_id': self.test_utils.get_unique_id(),
            'game_id': self.test_utils.get_unique_id(),
            'status': status,
            'score': self._generate_score_for_status(status, duration_ms),
            'play_duration_ms': duration_ms,
            'started_at': started_at,
            'updated_at': self._calculate_updated_at(started_at, status, duration_ms),
            'device_info': self._generate_device_info(),
            'sync_version': random.randint(1, 10),
            'game_state': self._generate_game_state(),
            'completed_at': None,
            'paused_at': None,
            'resumed_at': None,
            'final_score': None
        }

        # Set timestamps based on status
        if status == 'completed':
            defaults['completed_at'] = defaults['updated_at']
            defaults['final_score'] = defaults['score']
        elif status == 'paused':
            defaults['paused_at'] = defaults['updated_at']
        elif status == 'active':
            # Might have been paused and resumed
            if random.random() < 0.3:  # 30% chance of having been paused
                pause_time = started_at + timedelta(milliseconds=duration_ms * 0.6)
                resume_time = pause_time + timedelta(minutes=random.randint(1, 60))
                defaults['paused_at'] = pause_time
                defaults['resumed_at'] = resume_time

        defaults.update(overrides)
        return defaults

    def create_batch(self, count: int, **base_overrides) -> List[Dict[str, Any]]:
        """Create multiple sessions with optional base overrides"""
        return [self.create(**base_overrides) for _ in range(count)]

    def create_active_session(self, **overrides) -> Dict[str, Any]:
        """Create an active session"""
        active_defaults = {
            'status': 'active',
            'started_at': datetime.now(timezone.utc) - timedelta(minutes=random.randint(5, 120)),
            'updated_at': datetime.now(timezone.utc) - timedelta(seconds=random.randint(10, 300)),
            'completed_at': None,
            'final_score': None
        }
        active_defaults.update(overrides)
        return self.create(**active_defaults)

    def create_completed_session(self, **overrides) -> Dict[str, Any]:
        """Create a completed session"""
        duration_ms = random.randint(60000, 3600000)  # 1-60 minutes
        score = self._generate_score_for_status('completed', duration_ms)

        completed_defaults = {
            'status': 'completed',
            'play_duration_ms': duration_ms,
            'score': score,
            'final_score': score,
            'completed_at': datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 168))
        }
        completed_defaults.update(overrides)
        return self.create(**completed_defaults)

    def create_paused_session(self, **overrides) -> Dict[str, Any]:
        """Create a paused session"""
        paused_defaults = {
            'status': 'paused',
            'paused_at': datetime.now(timezone.utc) - timedelta(minutes=random.randint(5, 480)),
            'completed_at': None,
            'final_score': None
        }
        paused_defaults.update(overrides)
        return self.create(**paused_defaults)

    def create_cross_device_sessions(self, user_id: str, count: int = 3) -> List[Dict[str, Any]]:
        """Create sessions for the same user across different devices"""
        devices = [
            self._generate_device_info('desktop'),
            self._generate_device_info('mobile'),
            self._generate_device_info('tablet')
        ]

        sessions = []
        for i in range(count):
            device = devices[i % len(devices)]
            session = self.create(
                user_id=user_id,
                device_info=device,
                sync_version=i + 1
            )
            sessions.append(session)

        return sessions

    def create_sessions_for_user(self, user_id: str, count: int = 5) -> List[Dict[str, Any]]:
        """Create multiple sessions for a single user"""
        sessions = []
        game_ids = [self.test_utils.get_unique_id() for _ in range(min(count, 3))]

        for i in range(count):
            game_id = random.choice(game_ids)  # User plays multiple games
            session = self.create(
                user_id=user_id,
                game_id=game_id
            )
            sessions.append(session)

        return sessions

    def create_high_score_session(self, **overrides) -> Dict[str, Any]:
        """Create a high-score session"""
        high_score_defaults = {
            'status': 'completed',
            'score': random.randint(8000, 15000),
            'final_score': random.randint(8000, 15000),
            'play_duration_ms': random.randint(1800000, 3600000),  # 30-60 minutes
            'achievements_unlocked': random.sample(
                ['high_score', 'perfect_game', 'speed_demon', 'persistent', 'champion'],
                random.randint(1, 3)
            )
        }
        high_score_defaults.update(overrides)
        return self.create(**high_score_defaults)

    def _generate_score_for_status(self, status: str, duration_ms: int) -> int:
        """Generate a realistic score based on session status and duration"""
        base_score = int(duration_ms / 1000)  # 1 point per second as base

        if status == 'completed':
            return random.randint(base_score, base_score * 3)
        elif status == 'active':
            return random.randint(base_score // 2, base_score * 2)
        elif status == 'paused':
            return random.randint(base_score // 3, base_score)
        elif status == 'abandoned':
            return random.randint(0, base_score // 2)
        else:
            return base_score

    def _calculate_updated_at(self, started_at: datetime, status: str, duration_ms: int) -> datetime:
        """Calculate realistic updated_at timestamp"""
        if status == 'completed':
            return started_at + timedelta(milliseconds=duration_ms)
        elif status == 'abandoned':
            return started_at + timedelta(milliseconds=duration_ms // 2)
        else:
            return started_at + timedelta(
                milliseconds=duration_ms + random.randint(0, 300000)  # Up to 5 minutes
            )

    def _generate_device_info(self, device_type: str = None) -> Dict[str, Any]:
        """Generate realistic device information"""
        if device_type is None:
            device_type = random.choice(['desktop', 'mobile', 'tablet'])

        if device_type == 'desktop':
            return {
                'platform': 'web',
                'device_type': 'desktop',
                'user_agent': random.choice([
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
                ]),
                'app_version': '1.0.0',
                'screen_resolution': random.choice(['1920x1080', '2560x1440', '3840x2160']),
                'browser': random.choice(['Chrome', 'Firefox', 'Safari', 'Edge'])
            }
        elif device_type == 'mobile':
            return {
                'platform': 'mobile',
                'device_type': 'smartphone',
                'user_agent': 'GoodPlay Mobile App 1.2.0',
                'app_version': '1.2.0',
                'os': random.choice(['iOS 15.0', 'Android 11', 'Android 12']),
                'screen_resolution': random.choice(['1080x2400', '1170x2532', '1440x3200']),
                'device_model': random.choice(['iPhone 13', 'Samsung Galaxy S21', 'Google Pixel 6'])
            }
        else:  # tablet
            return {
                'platform': 'mobile',
                'device_type': 'tablet',
                'user_agent': 'GoodPlay Mobile App 1.2.0',
                'app_version': '1.2.0',
                'os': random.choice(['iPadOS 15.0', 'Android 11']),
                'screen_resolution': random.choice(['2048x2732', '2560x1600', '2000x1200']),
                'device_model': random.choice(['iPad Pro', 'Samsung Galaxy Tab', 'Surface Pro'])
            }

    def _generate_game_state(self) -> Dict[str, Any]:
        """Generate realistic game state data"""
        return {
            'level': random.randint(1, 20),
            'lives': random.randint(0, 5),
            'power_ups': random.sample(
                ['shield', 'double_score', 'time_bonus', 'extra_life', 'hint'],
                random.randint(0, 3)
            ),
            'inventory': {
                'coins': random.randint(0, 1000),
                'gems': random.randint(0, 50),
                'keys': random.randint(0, 10)
            },
            'progress': {
                'completion_percentage': round(random.uniform(0, 100), 1),
                'checkpoints_reached': random.randint(0, 10),
                'secrets_found': random.randint(0, 5)
            },
            'settings': {
                'difficulty': random.choice(['easy', 'medium', 'hard']),
                'sound_volume': round(random.uniform(0, 1), 1),
                'music_volume': round(random.uniform(0, 1), 1)
            }
        }