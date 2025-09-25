"""
Test suite for the new Test Architecture Foundation.

Demonstrates and validates the new testing infrastructure including
TestConfig, TestBase, TestUtils, factories, and fixtures.
"""
import pytest
from tests.core import TestBase, TestConfig, TestUtils
from tests.factories.user_factory import UserFactory, UserPreferencesFactory
from tests.factories.game_factory import GameFactory, GameSessionFactory


class TestNewArchitecture(TestBase):
    """Test the new test architecture components"""

    def test_test_config_functionality(self):
        """Test TestConfig features"""
        # Test configuration creation
        config = TestConfig()
        assert config.environment == 'testing'
        assert config.database.test_uri.endswith('goodplay_test')

        # Test configuration override
        new_config = config.override(
            database={'isolation_mode': 'transaction'},
            performance={'slow_test_threshold': 2.0}
        )
        assert new_config.database.isolation_mode == 'transaction'
        assert new_config.performance.slow_test_threshold == 2.0

        self.log_test_info("TestConfig working correctly")

    def test_test_utils_functionality(self, test_utils):
        """Test TestUtils with fixture injection"""
        # Test unique ID generation
        id1 = test_utils.get_unique_id()
        id2 = test_utils.get_unique_id()
        assert id1 != id2
        assert id1.startswith('test_')

        # Test unique email generation
        email1 = test_utils.get_unique_email()
        email2 = test_utils.get_unique_email()
        assert email1 != email2
        assert '@goodplay.test' in email1

        # Test mock user creation
        user = test_utils.create_mock_user()
        test_utils.assert_valid_user_data(user)

        self.log_test_info(f"Created test user: {user['email']}")

    def test_user_factory_functionality(self, user_factory):
        """Test UserFactory features"""
        # Test basic user creation
        user = user_factory.create()
        assert 'email' in user
        assert 'first_name' in user
        assert user['is_active'] is True

        # Test user creation with overrides
        admin_user = user_factory.create(
            first_name="Admin",
            is_admin=True
        )
        assert admin_user['first_name'] == "Admin"
        assert admin_user['is_admin'] is True

        # Test specialized user creation
        new_user = user_factory.create_new_user()
        assert new_user['games_played'] == 0
        assert new_user['total_score'] == 0

        veteran_user = user_factory.create_veteran_user()
        assert veteran_user['games_played'] >= 1000
        assert veteran_user['total_score'] >= 50000

        self.log_test_info("UserFactory creating users with correct attributes")

    def test_game_factory_functionality(self, game_factory):
        """Test GameFactory and GameSessionFactory"""
        # Test game creation
        game = game_factory['game'].create()
        assert 'name' in game
        assert 'category' in game
        assert game['max_players'] >= game['min_players']

        # Test session creation
        session = game_factory['session'].create()
        assert 'user_id' in session
        assert 'game_id' in session
        assert session['status'] in ['active', 'paused', 'completed', 'abandoned']

        # Test specialized session creation
        active_session = game_factory['session'].create_active_session()
        assert active_session['status'] == 'active'
        assert active_session['completed_at'] is None

        completed_session = game_factory['session'].create_completed_session()
        assert completed_session['status'] == 'completed'
        assert completed_session['final_score'] is not None

        self.log_test_info("GameFactory creating realistic game data")

    def test_performance_monitoring(self, test_config_instance):
        """Test automatic performance monitoring"""
        import time

        # This test should be detected as slow due to sleep
        time.sleep(1.2)  # Exceed the 1.0s threshold

        # The performance monitoring fixture should have recorded this
        self.log_test_info("Performance monitoring test completed")

    def test_enhanced_assertions(self):
        """Test enhanced assertion methods from TestBase"""
        # Test success response assertion
        success_response = {
            'success': True,
            'message': 'Operation successful',
            'data': {'id': 123}
        }
        self.assert_success_response(success_response, 'Operation successful')

        # Test error response assertion
        error_response = {
            'success': False,
            'message': 'Invalid data',
            'code': 400
        }
        self.assert_error_response(error_response, 'Invalid data', 400)

        self.log_test_info("Enhanced assertions working correctly")

    def test_mock_creation_utilities(self):
        """Test mock creation utilities"""
        # Test mock user creation
        user = self.create_mock_user(email='test@example.com')
        assert user['email'] == 'test@example.com'

        # Test mock database response
        mock_response = self.create_mock_db_response([{'id': 1}, {'id': 2}])
        assert len(mock_response.find.return_value) == 2

        self.log_test_info("Mock utilities working correctly")

    def test_configuration_override_in_test(self, override_test_config):
        """Test configuration override within a test"""
        # Create a custom config for this specific test
        custom_config = override_test_config(
            performance={'enable_timing': False},
            logging={'level': 'DEBUG'}
        )

        assert custom_config.performance.enable_timing is False
        assert custom_config.logging.level == 'DEBUG'

        # Use the custom config
        self.use_config(custom_config)
        assert self.test_config.performance.enable_timing is False

        self.log_test_info("Configuration override working in test context")