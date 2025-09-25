"""
Test Utilities Module

Provides common utilities, helpers, and data generators for GoodPlay tests.
Includes mock creation, data validation, and assertion helpers.
"""
import random
import string
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Union
from unittest.mock import MagicMock, Mock
from .config import TestConfig


class TestUtils:
    """
    Utility class providing common testing helpers and data generators.
    """

    def __init__(self, config: TestConfig = None):
        self.config = config
        self._counter = 0

    def get_unique_id(self) -> str:
        """Generate a unique ID for testing"""
        self._counter += 1
        timestamp = int(time.time() * 1000)
        return f"test_{timestamp}_{self._counter}"

    def get_unique_email(self) -> str:
        """Generate a unique email for testing"""
        unique_id = self.get_unique_id()
        return f"test_{unique_id}@goodplay.test"

    def generate_random_string(self, length: int = 10) -> str:
        """Generate a random string of specified length"""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

    def generate_random_phone(self) -> str:
        """Generate a random phone number for testing"""
        return f"+1{''.join(random.choices(string.digits, k=10))}"

    # User Data Generators

    def create_mock_user(self, **overrides) -> Dict[str, Any]:
        """Create a mock user with default values"""
        defaults = {
            '_id': self.get_unique_id(),
            'email': self.get_unique_email(),
            'first_name': 'Test',
            'last_name': 'User',
            'created_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc),
            'is_active': True,
            'is_admin': False,
            'is_verified': True
        }
        defaults.update(overrides)
        return defaults

    def create_mock_user_preferences(self, **overrides) -> Dict[str, Any]:
        """Create mock user preferences"""
        defaults = {
            'user_id': self.get_unique_id(),
            'gaming': {
                'preferred_categories': ['puzzle', 'strategy'],
                'difficulty_level': 'medium',
                'tutorial_enabled': True,
                'auto_save': True,
                'sound_enabled': True,
                'music_enabled': False,
                'vibration_enabled': True
            },
            'notifications': {
                'push_enabled': True,
                'email_enabled': False,
                'frequency': 'weekly',
                'achievement_alerts': True,
                'donation_confirmations': True,
                'friend_activity': False,
                'tournament_reminders': True,
                'maintenance_alerts': True
            },
            'privacy': {
                'profile_visibility': 'friends',
                'stats_sharing': False,
                'friends_discovery': True,
                'leaderboard_participation': True,
                'activity_visibility': 'private',
                'contact_permissions': 'friends'
            },
            'donations': {
                'auto_donate_enabled': False,
                'auto_donate_percentage': 10.0,
                'preferred_causes': ['education', 'environment'],
                'notification_threshold': 50.0,
                'monthly_goal': 100.0,
                'impact_sharing': True
            }
        }
        defaults.update(overrides)
        return defaults

    # Game Data Generators

    def create_mock_game(self, **overrides) -> Dict[str, Any]:
        """Create a mock game"""
        defaults = {
            '_id': self.get_unique_id(),
            'name': f'Test Game {self.generate_random_string(5)}',
            'description': 'A test game for unit testing',
            'category': 'puzzle',
            'difficulty': 'medium',
            'min_players': 1,
            'max_players': 4,
            'estimated_duration': 300,  # 5 minutes
            'is_active': True,
            'created_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc)
        }
        defaults.update(overrides)
        return defaults

    def create_mock_game_session(self, **overrides) -> Dict[str, Any]:
        """Create a mock game session"""
        defaults = {
            '_id': self.get_unique_id(),
            'user_id': self.get_unique_id(),
            'game_id': self.get_unique_id(),
            'status': 'active',
            'score': random.randint(0, 1000),
            'play_duration_ms': random.randint(30000, 600000),  # 30s to 10min
            'started_at': datetime.now(timezone.utc) - timedelta(minutes=5),
            'updated_at': datetime.now(timezone.utc),
            'device_info': {
                'platform': 'web',
                'device_type': 'desktop',
                'user_agent': 'Test Browser 1.0',
                'app_version': '1.0.0'
            },
            'sync_version': 1,
            'completed_at': None,
            'paused_at': None,
            'resumed_at': None
        }
        defaults.update(overrides)
        return defaults

    # Social Data Generators

    def create_mock_achievement(self, **overrides) -> Dict[str, Any]:
        """Create a mock achievement"""
        defaults = {
            '_id': self.get_unique_id(),
            'name': f'Test Achievement {self.generate_random_string(5)}',
            'description': 'A test achievement',
            'category': 'gaming',
            'points': random.randint(10, 100),
            'icon': 'trophy',
            'rarity': 'common',
            'conditions': {
                'type': 'score',
                'threshold': 100
            },
            'is_active': True,
            'created_at': datetime.now(timezone.utc)
        }
        defaults.update(overrides)
        return defaults

    def create_mock_user_achievement(self, **overrides) -> Dict[str, Any]:
        """Create a mock user achievement"""
        defaults = {
            '_id': self.get_unique_id(),
            'user_id': self.get_unique_id(),
            'achievement_id': self.get_unique_id(),
            'earned_at': datetime.now(timezone.utc),
            'progress': 100,
            'metadata': {}
        }
        defaults.update(overrides)
        return defaults

    # Challenge Data Generators

    def create_mock_challenge(self, **overrides) -> Dict[str, Any]:
        """Create a mock challenge"""
        defaults = {
            '_id': self.get_unique_id(),
            'creator_id': self.get_unique_id(),
            'game_id': self.get_unique_id(),
            'title': f'Test Challenge {self.generate_random_string(5)}',
            'description': 'A test challenge',
            'challenge_type': '1v1',
            'status': 'pending',
            'max_participants': 2,
            'duration_minutes': 30,
            'skill_level': 'medium',
            'is_public': True,
            'created_at': datetime.now(timezone.utc),
            'starts_at': datetime.now(timezone.utc) + timedelta(hours=1),
            'expires_at': datetime.now(timezone.utc) + timedelta(days=1)
        }
        defaults.update(overrides)
        return defaults

    # Database Mock Helpers

    def create_mock_db_response(self, data: Any = None, count: int = 0) -> MagicMock:
        """Create a mock database response"""
        mock = MagicMock()

        if data is None:
            mock.find_one.return_value = None
            mock.find.return_value = []
        elif isinstance(data, list):
            mock.find.return_value = data
            mock.find_one.return_value = data[0] if data else None
        else:
            mock.find_one.return_value = data
            mock.find.return_value = [data]

        mock.count_documents.return_value = count if count > 0 else (len(data) if isinstance(data, list) else (1 if data else 0))

        # Mock modification operations
        mock.insert_one.return_value = MagicMock(inserted_id=self.get_unique_id())
        mock.update_one.return_value = MagicMock(modified_count=1)
        mock.delete_one.return_value = MagicMock(deleted_count=1)
        mock.create_index.return_value = None

        return mock

    def setup_auth_mock(self, user_id: str = None) -> MagicMock:
        """Setup authentication mock"""
        if user_id is None:
            user_id = self.get_unique_id()

        mock_user = self.create_mock_user(_id=user_id)
        return mock_user

    def create_mock_collection(self, data: List[Dict] = None) -> MagicMock:
        """Create a mock MongoDB collection"""
        mock_collection = MagicMock()

        if data is None:
            data = []

        # Setup find operations
        mock_collection.find.return_value = data
        mock_collection.find_one.return_value = data[0] if data else None
        mock_collection.count_documents.return_value = len(data)

        # Setup modification operations
        def mock_insert_one(doc):
            result = MagicMock()
            result.inserted_id = doc.get('_id', self.get_unique_id())
            data.append(doc)
            return result

        def mock_update_one(filter_doc, update_doc):
            result = MagicMock()
            result.modified_count = 1
            return result

        def mock_delete_one(filter_doc):
            result = MagicMock()
            result.deleted_count = 1
            return result

        mock_collection.insert_one.side_effect = mock_insert_one
        mock_collection.update_one.side_effect = mock_update_one
        mock_collection.delete_one.side_effect = mock_delete_one

        return mock_collection

    # Validation Helpers

    def assert_valid_user_data(self, user_data: Dict[str, Any]):
        """Assert that user data is valid"""
        required_fields = ['email', 'first_name', 'last_name']
        for field in required_fields:
            assert field in user_data, f"Missing required field: {field}"

        assert '@' in user_data['email'], "Invalid email format"
        assert len(user_data['first_name']) > 0, "First name cannot be empty"
        assert len(user_data['last_name']) > 0, "Last name cannot be empty"

    def assert_valid_preferences_data(self, preferences: Dict[str, Any]):
        """Assert that preferences data is valid"""
        required_sections = ['gaming', 'notifications', 'privacy', 'donations']
        for section in required_sections:
            assert section in preferences, f"Missing preferences section: {section}"

    def assert_valid_game_session_data(self, session_data: Dict[str, Any]):
        """Assert that game session data is valid"""
        required_fields = ['user_id', 'game_id', 'status']
        for field in required_fields:
            assert field in session_data, f"Missing required field: {field}"

        valid_statuses = ['active', 'paused', 'completed', 'abandoned']
        assert session_data['status'] in valid_statuses, f"Invalid session status: {session_data['status']}"

    # Time Helpers

    def get_past_datetime(self, days: int = 1, hours: int = 0, minutes: int = 0) -> datetime:
        """Get a datetime in the past"""
        return datetime.now(timezone.utc) - timedelta(days=days, hours=hours, minutes=minutes)

    def get_future_datetime(self, days: int = 1, hours: int = 0, minutes: int = 0) -> datetime:
        """Get a datetime in the future"""
        return datetime.now(timezone.utc) + timedelta(days=days, hours=hours, minutes=minutes)

    def is_recent_datetime(self, dt: datetime, threshold_seconds: int = 60) -> bool:
        """Check if datetime is recent (within threshold)"""
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        now = datetime.now(timezone.utc)
        diff = abs((now - dt).total_seconds())
        return diff <= threshold_seconds

    # Request/Response Helpers

    def create_test_headers(self, auth_token: str = 'test-token', content_type: str = 'application/json') -> Dict[str, str]:
        """Create test HTTP headers"""
        return {
            'Authorization': f'Bearer {auth_token}',
            'Content-Type': content_type,
            'User-Agent': 'GoodPlay Test Client 1.0'
        }

    def create_api_request_data(self, **data) -> Dict[str, Any]:
        """Create API request data with common test patterns"""
        return {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'test_id': self.get_unique_id(),
            **data
        }

    def extract_api_response_data(self, response) -> Dict[str, Any]:
        """Extract and validate API response data"""
        assert hasattr(response, 'get_json'), "Response must have get_json method"
        data = response.get_json()
        assert isinstance(data, dict), "Response data must be a dictionary"
        return data

    # Performance Helpers

    def benchmark_function(self, func, iterations: int = 100, *args, **kwargs) -> Dict[str, float]:
        """Benchmark a function execution"""
        times = []

        for _ in range(iterations):
            start_time = time.time()
            func(*args, **kwargs)
            end_time = time.time()
            times.append(end_time - start_time)

        return {
            'min': min(times),
            'max': max(times),
            'avg': sum(times) / len(times),
            'total': sum(times)
        }

    # Error Testing Helpers

    def create_invalid_data_variants(self, base_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create variants of data with invalid values for testing error handling"""
        variants = []

        for key in base_data.keys():
            if isinstance(base_data[key], str):
                # Empty string variant
                invalid_data = base_data.copy()
                invalid_data[key] = ""
                variants.append(invalid_data)

                # None variant
                invalid_data = base_data.copy()
                invalid_data[key] = None
                variants.append(invalid_data)

            elif isinstance(base_data[key], (int, float)):
                # Negative number variant
                invalid_data = base_data.copy()
                invalid_data[key] = -1
                variants.append(invalid_data)

        # Missing key variants
        for key in base_data.keys():
            invalid_data = base_data.copy()
            del invalid_data[key]
            variants.append(invalid_data)

        return variants