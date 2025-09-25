"""
Smart Fixture Presets for GOO-34

Predefined fixture combinations for common test scenarios with automatic
dependency resolution and intelligent caching.
"""
from typing import Dict, Any, List, Optional
import random

from .smart_manager import smart_fixture_manager, FixtureScope
from .decorators import smart_fixture, factory_fixture, preset_fixture


class FixturePresetManager:
    """Manager for predefined fixture combinations"""

    def __init__(self):
        self._presets: Dict[str, Dict[str, Any]] = {}
        self._register_default_presets()

    def register_preset(
        self,
        name: str,
        fixtures: List[str],
        description: str = "",
        scope: FixtureScope = FixtureScope.FUNCTION,
        factory_kwargs: Dict[str, Any] = None
    ):
        """Register a fixture preset"""
        self._presets[name] = {
            'fixtures': fixtures,
            'description': description,
            'scope': scope,
            'factory_kwargs': factory_kwargs or {}
        }

    def create_preset(self, name: str, **kwargs) -> Dict[str, Any]:
        """Create a preset fixture combination"""
        if name not in self._presets:
            raise ValueError(f"Unknown preset '{name}'. Available: {list(self._presets.keys())}")

        preset_config = self._presets[name]
        fixtures_to_create = preset_config['fixtures']

        # Merge preset factory_kwargs with provided kwargs
        merged_kwargs = {**preset_config.get('factory_kwargs', {}), **kwargs}

        # Create all fixtures in the preset
        results = smart_fixture_manager.create_fixtures(fixtures_to_create, **merged_kwargs)

        return results

    def get_available_presets(self) -> Dict[str, str]:
        """Get list of available presets with descriptions"""
        return {
            name: config.get('description', 'No description')
            for name, config in self._presets.items()
        }

    def _register_default_presets(self):
        """Register the 5 default presets required by GOO-34"""

        # 1. Basic User Setup
        self.register_preset(
            'basic_user_setup',
            fixtures=['basic_user', 'user_preferences'],
            description="User with default preferences and basic setup",
            scope=FixtureScope.FUNCTION
        )

        # 2. Gaming Session Setup
        self.register_preset(
            'gaming_session_setup',
            fixtures=['basic_user', 'game', 'game_session'],
            description="User + Game + Active gaming session",
            scope=FixtureScope.FUNCTION
        )

        # 3. Social Network Setup
        self.register_preset(
            'social_network_setup',
            fixtures=['user_alice', 'user_bob', 'user_charlie', 'user_relationships'],
            description="Multiple users with established social relationships",
            scope=FixtureScope.CLASS
        )

        # 4. Financial Setup
        self.register_preset(
            'financial_setup',
            fixtures=['basic_user', 'wallet', 'transaction_history'],
            description="User + Wallet + Complete transaction history",
            scope=FixtureScope.FUNCTION
        )

        # 5. Admin Setup
        self.register_preset(
            'admin_setup',
            fixtures=['admin_user', 'admin_permissions', 'admin_session'],
            description="Admin user with full permissions and active session",
            scope=FixtureScope.SESSION
        )


# Global preset manager instance
preset_manager = FixturePresetManager()


# =============================================================================
# PRESET 1: Basic User Setup
# =============================================================================

@smart_fixture('basic_user', scope=FixtureScope.FUNCTION)
def basic_user():
    """Basic user for testing"""
    from tests.factories.user_factory import UserFactory
    return UserFactory.build()


@smart_fixture('user_preferences', dependencies=['basic_user'], scope=FixtureScope.FUNCTION)
def user_preferences(basic_user):
    """User preferences linked to basic user"""
    from tests.factories.user_factory import UserPreferencesFactory
    return UserPreferencesFactory.build(user_id=basic_user['_id'])


@preset_fixture('basic_user_setup')
def basic_user_setup():
    """User with default preferences - PRESET 1"""
    return preset_manager.create_preset('basic_user_setup')


# =============================================================================
# PRESET 2: Gaming Session Setup
# =============================================================================

@smart_fixture('game', scope=FixtureScope.CLASS)
def game():
    """Sample game for testing"""
    from tests.factories.game_factory import GameFactory
    return GameFactory.build()


@smart_fixture(
    'game_session',
    dependencies=['basic_user', 'game'],
    scope=FixtureScope.FUNCTION
)
def game_session(basic_user, game):
    """Active game session"""
    from tests.factories.game_factory import GameSessionFactory
    return GameSessionFactory.build(
        user_id=basic_user['_id'],
        game_id=game['_id'],
        status='active'
    )


@preset_fixture('gaming_session_setup')
def gaming_session_setup():
    """User + Game + Active gaming session - PRESET 2"""
    return preset_manager.create_preset('gaming_session_setup')


# =============================================================================
# PRESET 3: Social Network Setup
# =============================================================================

@smart_fixture('user_alice', scope=FixtureScope.CLASS)
def user_alice():
    """Social network user Alice"""
    from tests.factories.user_factory import UserFactory
    return UserFactory.build(
        email='alice@goodplay.test',
        first_name='Alice',
        last_name='Wonder'
    )


@smart_fixture('user_bob', scope=FixtureScope.CLASS)
def user_bob():
    """Social network user Bob"""
    from tests.factories.user_factory import UserFactory
    return UserFactory.build(
        email='bob@goodplay.test',
        first_name='Bob',
        last_name='Builder'
    )


@smart_fixture('user_charlie', scope=FixtureScope.CLASS)
def user_charlie():
    """Social network user Charlie"""
    from tests.factories.user_factory import UserFactory
    return UserFactory.build(
        email='charlie@goodplay.test',
        first_name='Charlie',
        last_name='Brown'
    )


@smart_fixture(
    'user_relationships',
    dependencies=['user_alice', 'user_bob', 'user_charlie'],
    scope=FixtureScope.CLASS
)
def user_relationships(user_alice, user_bob, user_charlie):
    """Established relationships between users"""
    from tests.factories.social_factory import UserRelationshipFactory

    relationships = []

    # Alice and Bob are friends
    relationships.append(UserRelationshipFactory.build(
        user_id=user_alice['_id'],
        related_user_id=user_bob['_id'],
        relationship_type='friend',
        status='accepted'
    ))

    # Bob and Charlie are friends
    relationships.append(UserRelationshipFactory.build(
        user_id=user_bob['_id'],
        related_user_id=user_charlie['_id'],
        relationship_type='friend',
        status='accepted'
    ))

    # Alice follows Charlie
    relationships.append(UserRelationshipFactory.build(
        user_id=user_alice['_id'],
        related_user_id=user_charlie['_id'],
        relationship_type='follower',
        status='active'
    ))

    return relationships


@preset_fixture('social_network_setup')
def social_network_setup():
    """Multiple users with established relationships - PRESET 3"""
    return preset_manager.create_preset('social_network_setup')


# =============================================================================
# PRESET 4: Financial Setup
# =============================================================================

@smart_fixture('wallet', dependencies=['basic_user'], scope=FixtureScope.FUNCTION)
def wallet(basic_user):
    """User wallet with initial balance"""
    from tests.factories.financial_factory import WalletFactory
    return WalletFactory.build(
        user_id=basic_user['_id'],
        current_balance=100.0,
        total_earned=500.0
    )


@smart_fixture(
    'transaction_history',
    dependencies=['basic_user', 'wallet'],
    scope=FixtureScope.FUNCTION
)
def transaction_history(basic_user, wallet):
    """Complete transaction history"""
    from tests.factories.financial_factory import TransactionFactory

    transactions = []

    # Create various types of transactions
    transaction_types = ['earning', 'donation', 'reward', 'purchase']

    for i in range(10):  # Create 10 sample transactions
        transaction_type = random.choice(transaction_types)
        amount = round(random.uniform(5.0, 50.0), 2)

        if transaction_type in ['donation', 'purchase']:
            amount = -amount  # Negative for outgoing transactions

        transactions.append(TransactionFactory.build(
            user_id=basic_user['_id'],
            wallet_id=wallet['_id'],
            transaction_type=transaction_type,
            amount=amount,
            description=f"Test {transaction_type} #{i+1}"
        ))

    return transactions


@preset_fixture('financial_setup')
def financial_setup():
    """User + Wallet + Complete transaction history - PRESET 4"""
    return preset_manager.create_preset('financial_setup')


# =============================================================================
# PRESET 5: Admin Setup
# =============================================================================

@smart_fixture('admin_user', scope=FixtureScope.SESSION)
def admin_user():
    """Admin user with elevated privileges"""
    from tests.factories.user_factory import UserFactory
    return UserFactory.build(
        admin=True,  # Uses admin trait
        email='admin@goodplay.test',
        first_name='Admin',
        last_name='User'
    )


@smart_fixture('admin_permissions', dependencies=['admin_user'], scope=FixtureScope.SESSION)
def admin_permissions(admin_user):
    """Admin permissions configuration"""
    return {
        'user_id': admin_user['_id'],
        'permissions': [
            'user_management',
            'game_management',
            'financial_access',
            'system_admin',
            'analytics_access',
            'content_moderation'
        ],
        'access_level': 'superadmin',
        'granted_at': '2024-01-01T00:00:00Z'
    }


@smart_fixture(
    'admin_session',
    dependencies=['admin_user'],
    scope=FixtureScope.SESSION
)
def admin_session(admin_user):
    """Active admin session"""
    return {
        'user_id': admin_user['_id'],
        'session_type': 'admin',
        'access_token': 'admin_test_token_12345',
        'permissions': ['*'],  # All permissions
        'expires_at': '2024-12-31T23:59:59Z'
    }


@preset_fixture('admin_setup')
def admin_setup():
    """Admin user with full permissions and active session - PRESET 5"""
    return preset_manager.create_preset('admin_setup')


# =============================================================================
# Additional Utility Presets
# =============================================================================

@preset_fixture('empty_setup')
def empty_setup():
    """Empty setup for tests that need clean state"""
    return {}


@smart_fixture('test_data_ecosystem', scope=FixtureScope.MODULE)
def test_data_ecosystem():
    """Complete test data ecosystem with all major entities"""
    # Create a comprehensive test environment
    ecosystem = {}

    # Create basic entities
    ecosystem.update(preset_manager.create_preset('basic_user_setup'))
    ecosystem.update(preset_manager.create_preset('gaming_session_setup'))
    ecosystem.update(preset_manager.create_preset('financial_setup'))

    # Add achievements
    from tests.factories.social_factory import AchievementFactory
    ecosystem['achievements'] = AchievementFactory.build_batch(5)

    # Add ONLUS organizations
    from tests.factories.onlus_factory import ONLUSFactory
    ecosystem['onlus_orgs'] = ONLUSFactory.build_batch(3)

    return ecosystem


# =============================================================================
# Preset Registration Helper
# =============================================================================

def register_all_presets():
    """Register all presets with the smart fixture manager"""
    presets = [
        'basic_user_setup',
        'gaming_session_setup',
        'social_network_setup',
        'financial_setup',
        'admin_setup'
    ]

    for preset_name in presets:
        smart_fixture_manager.register_fixture(
            name=preset_name,
            creator=lambda name=preset_name: preset_manager.create_preset(name),
            scope=FixtureScope.FUNCTION
        )


# Auto-register presets when module is imported
register_all_presets()